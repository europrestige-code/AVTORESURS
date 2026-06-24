"""
BuyAnywhere Auto - AI service (extraction, translation, risk summary).

Uses emergentintegrations LlmChat with GPT-5.2 via Emergent Universal Key.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from typing import Any, Dict, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

DEFAULT_MODEL = ("openai", "gpt-5.2")
FALLBACK_MODEL = ("openai", "gpt-4o-mini")


def _strip_json(text: str) -> str:
    """Strip code fences or surrounding text and return the JSON body."""
    text = text.strip()
    # Remove ```json ... ``` fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    # Try to find first JSON object/array
    obj = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if obj:
        return obj.group(1)
    return text


def _safe_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(_strip_json(text))
    except Exception as e:
        logger.warning(f"AI returned non-JSON content: {e}; raw={text[:200]!r}")
        return None


class AutoAIService:
    def __init__(self) -> None:
        self.api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY missing; AI features will return graceful errors.")

    def _new_chat(self, system_message: str) -> LlmChat:
        chat = LlmChat(
            api_key=self.api_key or "missing",
            session_id=f"auto-{uuid.uuid4()}",
            system_message=system_message,
        ).with_model(*DEFAULT_MODEL)
        return chat

    async def _ask(self, system: str, prompt: str) -> str:
        """Send a message; fall back to gpt-4o-mini on model errors."""
        try:
            chat = self._new_chat(system)
            return await chat.send_message(UserMessage(text=prompt))
        except Exception as e:
            logger.warning(f"Primary model failed ({e}); trying fallback model.")
            chat = LlmChat(
                api_key=self.api_key or "missing",
                session_id=f"auto-fb-{uuid.uuid4()}",
                system_message=system,
            ).with_model(*FALLBACK_MODEL)
            return await chat.send_message(UserMessage(text=prompt))

    async def chat(self, prompt: str, system: str = "You are a helpful assistant.",
                    max_tokens: int = 800) -> str:
        """Public helper used by other services (e.g. email campaigns)."""
        return await self._ask(system, prompt)

    # ---- 1. Structured extraction from raw text ----
    EXTRACTION_SYSTEM = (
        "Вы — эксперт по аукционным и розничным объявлениям об автомобилях из Новой Зеландии и Австралии. "
        "Извлеките структурированные данные ИЗ ПРЕДОСТАВЛЕННОГО ТЕКСТА и верните строго JSON без пояснений. "
        "Не выдумывайте отсутствующие данные. Если поле неизвестно, используйте null. "
        "Используйте следующую схему:\n"
        "{\n"
        '  "source": null,\n'
        '  "source_url": null,\n'
        '  "source_reference": null,\n'
        '  "country": "NZ"|"AU"|null,\n'
        '  "listing_type": "auction"|"fixed_price"|"inquiry_only"|null,\n'
        '  "title_original": null,\n'
        '  "make": null,\n'
        '  "model": null,\n'
        '  "year": null,\n'
        '  "mileage_km": null,\n'
        '  "engine": null,\n'
        '  "fuel": null,\n'
        '  "transmission": null,\n'
        '  "body_type": null,\n'
        '  "location": null,\n'
        '  "condition": null,\n'
        '  "damage_type": null,\n'
        '  "auction_end_time": null,\n'
        '  "current_price_nzd": null,\n'
        '  "buy_now_price_nzd": null,\n'
        '  "description_original": null,\n'
        '  "images": []\n'
        "}\n"
        "Год — целое число. Пробег — целое число в км. Цены — числа в NZD без знаков валюты."
    )

    async def extract_vehicle_from_text(self, raw_text: str) -> Dict[str, Any]:
        if not raw_text or not raw_text.strip():
            return {"error": "Пустой текст объявления."}
        prompt = f"Объявление:\n{raw_text.strip()[:6000]}\n\nВерните JSON."
        response = await self._ask(self.EXTRACTION_SYSTEM, prompt)
        data = _safe_json(response)
        if data is None:
            return {
                "error": "Не удалось разобрать ответ AI.",
                "raw": response[:500],
            }
        return data

    # ---- 2. Translation to Russian ----
    TRANSLATION_SYSTEM = (
        "Вы — переводчик автомобильных объявлений с английского на русский. "
        "Переведите заголовок и описание чётко и без маркетинговых преувеличений. "
        "Сохраните технические термины (двигатель, коробка передач, кузов, состояние, тип повреждения). "
        "Верните строго JSON: {\"title_ru\": str, \"description_ru\": str|null}."
    )

    async def translate_vehicle_to_russian(self, vehicle: Dict[str, Any]) -> Dict[str, Any]:
        title = vehicle.get("title_original") or vehicle.get("title_ru") or ""
        description = vehicle.get("description_original") or vehicle.get("description_ru") or ""
        if not title and not description:
            return {"title_ru": vehicle.get("title_ru") or "Автомобиль", "description_ru": None,
                    "note": "Недостаточно данных для перевода."}
        prompt = (
            f"Заголовок (исходный): {title}\n"
            f"Описание (исходное): {description}\n\n"
            "Переведите на русский. Верните JSON."
        )
        response = await self._ask(self.TRANSLATION_SYSTEM, prompt)
        data = _safe_json(response)
        if not data:
            return {
                "title_ru": title or "Автомобиль",
                "description_ru": description or None,
                "note": "AI вернул некорректный ответ; использован исходный текст.",
            }
        return data

    # ---- 3. Risk summary ----
    RISK_SYSTEM = (
        "Вы — независимый автомобильный эксперт. На основе предоставленных данных составьте на русском языке: "
        "1) короткое информативное резюме (ai_summary_ru, 2-3 предложения); "
        "2) оценку рисков (ai_risk_summary_ru), упоминая: риск двигателя, риск коробки, риск затопления/воды (если применимо), "
        "риск подушек безопасности/каркаса (если применимо), пригодность как донор/на запчасти, рекомендованный тип покупателя, "
        "уровень осторожности (низкий/средний/высокий). НЕ выдумывайте факты. Если данных недостаточно для конкретного пункта, "
        "напишите 'Недостаточно данных для оценки.' Верните строго JSON: "
        "{\"ai_summary_ru\": str, \"ai_risk_summary_ru\": str}."
    )

    async def generate_vehicle_risk_summary(self, vehicle: Dict[str, Any]) -> Dict[str, Any]:
        # Build a brief vehicle description from known fields
        fields = {
            "Производитель": vehicle.get("make"),
            "Модель": vehicle.get("model"),
            "Год": vehicle.get("year"),
            "Пробег, км": vehicle.get("mileage_km"),
            "Двигатель": vehicle.get("engine"),
            "Топливо": vehicle.get("fuel"),
            "КПП": vehicle.get("transmission"),
            "Кузов": vehicle.get("body_type"),
            "Состояние": vehicle.get("condition"),
            "Повреждения": vehicle.get("damage_type"),
            "Локация": vehicle.get("location"),
            "Описание": (vehicle.get("description_original") or vehicle.get("description_ru") or "")[:1500],
        }
        if not any(v for v in fields.values() if v not in (None, "", 0)):
            return {
                "ai_summary_ru": "Недостаточно данных для оценки.",
                "ai_risk_summary_ru": "Недостаточно данных для оценки.",
            }
        lines = [f"{k}: {v}" for k, v in fields.items() if v not in (None, "")]
        prompt = "Данные об автомобиле:\n" + "\n".join(lines) + "\n\nВерните JSON."
        response = await self._ask(self.RISK_SYSTEM, prompt)
        data = _safe_json(response)
        if not data:
            return {
                "ai_summary_ru": "Недостаточно данных для оценки.",
                "ai_risk_summary_ru": "Недостаточно данных для оценки.",
            }
        return data
