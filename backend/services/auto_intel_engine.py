"""AI estimate engine.

Pulls all available signals for a vehicle:
  • the vehicle's own buy_now / current_price (catalog)
  • similar vehicles' historical auction observations
  • published Buy Now premium pattern (Buy Now ≈ auction + 20–25%)
  • damage / mileage adjustments

…and asks the LLM (Emergent Universal Key — Claude Sonnet 4.5) to return a
structured estimate: low/high bid range, recommended max, market score 0–100,
confidence label, and 3–5 reasoning bullets.

We deliberately ask the LLM for STRUCTURED JSON output and validate before
writing. If parsing fails we fall back to a heuristic estimate so the UI is
never blank.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import os
import logging

log = logging.getLogger(__name__)

CONFIDENCE_LABELS = ["excellent_buy", "good_buy", "average", "high_risk", "avoid"]


async def _gather_signals(db, vehicle: dict) -> Dict[str, Any]:
    """Pull comparable observations + buy-now stats from Mongo."""
    make = vehicle.get("make")
    model = vehicle.get("model")
    year = vehicle.get("year")

    query: Dict[str, Any] = {}
    if make: query["make"] = make
    if model: query["model"] = model
    if year:
        query["year"] = {"$gte": year - 2, "$lte": year + 2}

    cursor = db.auction_observations.find(query).sort("observed_at", -1).limit(50)
    sims: List[dict] = [d async for d in cursor]
    sold = [s for s in sims if s.get("sold") and s.get("observed_price_nzd")]
    prices = [s["observed_price_nzd"] for s in sold]
    buy_nows = [
        s["buy_now_price_nzd"] for s in sims
        if s.get("buy_now_price_nzd")
    ]
    return {
        "sample_size": len(sims),
        "sold_count": len(sold),
        "avg_observed_nzd": round(sum(prices) / len(prices), 2) if prices else None,
        "min_observed_nzd": min(prices) if prices else None,
        "max_observed_nzd": max(prices) if prices else None,
        "avg_buy_now_nzd": round(sum(buy_nows) / len(buy_nows), 2) if buy_nows else None,
    }


def _heuristic_estimate(vehicle: dict, signals: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback estimate when the LLM is unavailable or returns junk."""
    buy_now = vehicle.get("buy_now_price_nzd") or signals.get("avg_buy_now_nzd")
    cur = vehicle.get("current_price_nzd")
    base = cur or (buy_now * 0.8 if buy_now else 5000)
    return {
        "estimate_low_nzd": round(base * 0.85, 0),
        "estimate_high_nzd": round(base * 1.15, 0),
        "recommended_max_bid_nzd": round(base * 1.10, 0),
        "buy_now_reference_nzd": buy_now,
        "market_score": 55,
        "confidence": "average",
        "confidence_pct": 35,
        "reasoning": [
            "Эвристическая оценка: недостаточно исторических наблюдений.",
            f"База {round(base,0)} NZ$ — текущая аукционная цена или 80% от Buy Now.",
            "Точная оценка появится после накопления данных по похожим лотам.",
        ],
        "based_on_observations": signals.get("sample_size", 0),
        "model": "heuristic_v1",
    }


async def estimate_for_vehicle(db, vehicle: dict, *, force: bool = False) -> Dict[str, Any]:
    """Generate an AI estimate for a single vehicle and persist it on the doc."""
    if vehicle.get("ai_estimate") and not force:
        return vehicle["ai_estimate"]

    signals = await _gather_signals(db, vehicle)

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore
        key = os.environ.get("EMERGENT_LLM_KEY")
        if not key:
            raise RuntimeError("EMERGENT_LLM_KEY missing")

        prompt = _build_prompt(vehicle, signals)
        chat = LlmChat(api_key=key, session_id=f"estimate-{vehicle.get('id')}", system_message=_SYSTEM)
        chat.with_model("anthropic", "claude-sonnet-4-5")
        resp = await chat.send_message(UserMessage(text=prompt))
        ai_json = _safe_json(resp)
        if ai_json:
            est = {
                "estimate_low_nzd": ai_json.get("estimate_low_nzd"),
                "estimate_high_nzd": ai_json.get("estimate_high_nzd"),
                "recommended_max_bid_nzd": ai_json.get("recommended_max_bid_nzd"),
                "buy_now_reference_nzd": vehicle.get("buy_now_price_nzd") or signals.get("avg_buy_now_nzd"),
                "market_score": int(ai_json.get("market_score") or 0),
                "confidence": ai_json.get("confidence") if ai_json.get("confidence") in CONFIDENCE_LABELS else "average",
                "confidence_pct": int(ai_json.get("confidence_pct") or 0),
                "reasoning": ai_json.get("reasoning") or [],
                "based_on_observations": signals["sample_size"],
                "model": "claude-sonnet-4.5",
            }
        else:
            est = _heuristic_estimate(vehicle, signals)
    except Exception as e:
        log.warning("AI estimate fallback for %s: %s", vehicle.get("id"), e)
        est = _heuristic_estimate(vehicle, signals)

    est["generated_at"] = datetime.now(timezone.utc).isoformat()
    await db.auto_vehicles.update_one({"id": vehicle["id"]}, {"$set": {"ai_estimate": est}})
    return est


_SYSTEM = """Ты — оценщик б/у автомобилей с аукционов Новой Зеландии.
Отвечай СТРОГО валидным JSON по схеме:
{
  "estimate_low_nzd": number,
  "estimate_high_nzd": number,
  "recommended_max_bid_nzd": number,
  "market_score": integer 0..100,
  "confidence": one of ["excellent_buy","good_buy","average","high_risk","avoid"],
  "confidence_pct": integer 0..100,
  "reasoning": [3..5 коротких пунктов на русском]
}
Никакого markdown, никаких комментариев — только JSON."""


def _build_prompt(v: dict, s: Dict[str, Any]) -> str:
    return f"""Оцени лот:
- {v.get('year', '—')} {v.get('make','—')} {v.get('model','—')}
- Кузов: {v.get('body_type','—')} | Топливо: {v.get('fuel_type','—')} | Коробка: {v.get('transmission','—')}
- Пробег: {v.get('mileage_km','—')} км
- Повреждения: {v.get('damage_type') or 'нет'} | Состояние: {v.get('condition','—')}
- Текущая цена аукциона: {v.get('current_price_nzd','—')} NZ$
- Buy Now: {v.get('buy_now_price_nzd','—')} NZ$
- Источник: {v.get('source','—')}, филиал: {v.get('branch','—')}

Исторические сигналы по похожим (последние 50):
- Наблюдений: {s['sample_size']}, проданных с ценой: {s['sold_count']}
- Средняя цена продажи: {s['avg_observed_nzd']} NZ$, диапазон: {s['min_observed_nzd']}–{s['max_observed_nzd']}
- Средняя Buy Now: {s['avg_buy_now_nzd']}

Учитывай российский экспорт и спрос. Верни JSON."""


def _safe_json(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    s = text.strip()
    # Strip ```json fences if the model adds them.
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.lower().startswith("json"):
            s = s[4:]
        s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        return None
