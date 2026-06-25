"""AI-подборщик — chat-style quiz that captures buyer preferences and
returns a ranked list of matching auctions.

The lead is mirrored into `auto_interests` (source="quiz") so it shows up in
the existing admin lead queue with zero additional plumbing.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.auto_engagement import AutoInterestCreate
from services.auto_body_types import mongo_filter_for_key


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Rough RUB budget buckets shown in the chat. The numbers are inclusive
# ceilings except for the open-ended "более 6 млн" row which has no cap.
BUDGET_BUCKETS_RUB: List[Dict[str, Any]] = [
    {"key": "u1m",   "label": "до 1 млн ₽",            "max_rub": 1_000_000},
    {"key": "1_2m",  "label": "1 – 2 млн ₽",           "max_rub": 2_000_000},
    {"key": "2_3m",  "label": "2 – 3 млн ₽",           "max_rub": 3_000_000},
    {"key": "3_5m",  "label": "3 – 5 млн ₽",           "max_rub": 5_000_000},
    {"key": "5_8m",  "label": "5 – 8 млн ₽",           "max_rub": 8_000_000},
    {"key": "open",  "label": "более 8 млн / открыт",  "max_rub": None},
]


PURPOSE_LABELS = {
    "family":   "Для семьи / города",
    "work":     "Для работы / коммерции",
    "offroad":  "Внедорожник / путешествия",
    "passion":  "Спорт / для души",
    "resale":   "На перепродажу",
    "parts":    "На запчасти / распил",
}

URGENCY_LABELS = {
    "now":    "Готов покупать сейчас",
    "1_3m":   "Куплю в течение 1–3 месяцев",
    "watch":  "Просто присматриваюсь",
}


REPAIR_LABELS = {
    "no":     "Только целое авто",
    "light":  "Готов на лёгкий ремонт",
    "any":    "Беру под полное восстановление",
}


BUYER_TYPE_LABELS = {
    "private":  "Для себя",
    "dealer":   "Я дилер / для перепродажи",
    "company":  "От компании / парк",
}


def _purpose_to_body_types(purpose: Optional[str]) -> List[str]:
    """Heuristic mapping from declared purpose to canonical body-type keys.

    Used only when the user did not explicitly pick body types in the quiz.
    """
    if not purpose:
        return []
    return {
        "family":  ["wagon", "suv", "minivan", "hatchback", "sedan"],
        "work":    ["utility", "van"],
        "offroad": ["suv", "utility"],
        "passion": ["coupe", "convertible", "sedan"],
        "resale":  ["sedan", "suv", "hatchback"],
        "parts":   [],
    }.get(purpose, [])


class AutoQuizService:
    def __init__(self, db):
        self.db = db
        self.leads = db.auto_quiz_leads
        self.vehicles = db.auto_vehicles

    async def submit(
        self,
        payload: Dict[str, Any],
        fx_rate: float,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        name = (payload.get("name") or "").strip()
        contact = (payload.get("contact") or "").strip()
        if not name or not contact:
            raise ValueError("Укажите имя и контакт (телефон/Telegram).")

        budget_key = payload.get("budget_key")
        bucket = next((b for b in BUDGET_BUCKETS_RUB if b["key"] == budget_key), None)
        budget_rub = bucket["max_rub"] if bucket else None
        budget_nzd = (budget_rub / fx_rate) if (budget_rub and fx_rate) else None

        body_types: List[str] = list(payload.get("body_types") or [])
        purpose = payload.get("purpose")
        if not body_types:
            body_types = _purpose_to_body_types(purpose)
        country = payload.get("country")  # "NZ" | "AU" | None
        urgency = payload.get("urgency")
        repair = payload.get("repair")            # "no" | "light" | "any"
        buyer_type = payload.get("buyer_type")    # "private" | "dealer" | "company"
        city = (payload.get("city") or "").strip() or None
        notes = (payload.get("notes") or "").strip() or None

        # 1) Persist the quiz lead row (full snapshot)
        lead_doc = {
            "name": name,
            "contact": contact,
            "city": city,
            "budget_key": budget_key,
            "budget_rub_max": budget_rub,
            "budget_nzd_max": budget_nzd,
            "body_types": body_types,
            "purpose": purpose,
            "purpose_label": PURPOSE_LABELS.get(purpose),
            "urgency": urgency,
            "urgency_label": URGENCY_LABELS.get(urgency),
            "repair": repair,
            "repair_label": REPAIR_LABELS.get(repair),
            "buyer_type": buyer_type,
            "buyer_type_label": BUYER_TYPE_LABELS.get(buyer_type),
            "country": country,
            "notes": notes,
            "user_id": user_id,
            "fx_rate": fx_rate,
            "created_at": _now(),
        }
        await self.leads.insert_one(dict(lead_doc))
        lead_doc.pop("_id", None)
        lead_doc["created_at"] = lead_doc["created_at"].isoformat()

        # 2) Mirror as a standard АвтоИнтерес so the sales team sees it
        msg_parts: List[str] = []
        if bucket:
            msg_parts.append(f"Бюджет: {bucket['label']}")
        if purpose:
            msg_parts.append(f"Цель: {PURPOSE_LABELS.get(purpose, purpose)}")
        if body_types:
            msg_parts.append("Кузов: " + ", ".join(body_types))
        if country:
            msg_parts.append(f"Страна: {country}")
        if urgency:
            msg_parts.append(f"Срочность: {URGENCY_LABELS.get(urgency, urgency)}")
        if repair:
            msg_parts.append(f"Ремонт: {REPAIR_LABELS.get(repair, repair)}")
        if buyer_type:
            msg_parts.append(f"Покупатель: {BUYER_TYPE_LABELS.get(buyer_type, buyer_type)}")
        if notes:
            msg_parts.append(f"Заметки: {notes}")
        interest = AutoInterestCreate(
            name=name,
            phone=contact,                    # phone field stores the contact line
            email=None,
            city=city,
            budget_nzd=budget_nzd,
            message=" · ".join(msg_parts) or "Анкета АИ-подборщика",
            source="quiz",
        )
        try:
            from services.auto_engagement_service import AutoEngagementService
            await AutoEngagementService(self.db).create_interest(interest, user_id=user_id)
        except Exception:
            # Best-effort: never fail the quiz on the CRM mirror.
            pass

        # 3) Pull matching vehicles
        matches = await self._match(
            budget_nzd=budget_nzd,
            body_types=body_types,
            country=country,
            repair=repair,
            limit=int(payload.get("limit", 6)),
        )

        return {
            "lead": lead_doc,
            "matches": matches,
            "match_count": len(matches),
        }

    async def _match(
        self,
        budget_nzd: Optional[float],
        body_types: List[str],
        country: Optional[str],
        repair: Optional[str] = None,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        q: Dict[str, Any] = {"status": "available"}
        if country in ("NZ", "AU"):
            q["country"] = country
        # Damage preference
        if repair == "no":
            q["damage_type"] = {"$in": [None, ""]}
        elif repair == "any":
            q["damage_type"] = {"$nin": [None, ""], "$exists": True}
        if budget_nzd:
            # Compare against the AI estimate range, falling back to current price.
            # We use $or so vehicles without ai_estimate still match if their
            # current_price fits the budget.
            q["$or"] = [
                {"ai_estimate.recommended_max_bid_nzd": {"$lte": float(budget_nzd)}},
                {"current_price_nzd": {"$lte": float(budget_nzd), "$gt": 0}},
            ]
        if body_types:
            regex_clauses: List[Dict[str, Any]] = []
            for key in body_types:
                mf = mongo_filter_for_key(key)
                if mf:
                    regex_clauses.append({"body_type": mf})
            if regex_clauses:
                # Merge into any existing $or via $and so we don't lose budget.
                if "$or" in q:
                    existing_or = q.pop("$or")
                    q["$and"] = [{"$or": existing_or}, {"$or": regex_clauses}]
                else:
                    q["$or"] = regex_clauses

        cur = self.vehicles.find(q).sort("auction_ends_at", 1).limit(int(limit))
        out: List[Dict[str, Any]] = []
        async for v in cur:
            v.pop("_id", None)
            for k in ("auction_ends_at", "created_at", "updated_at"):
                t = v.get(k)
                if isinstance(t, datetime):
                    v[k] = t.isoformat()
            out.append({
                "id": v.get("id"),
                "title_ru": v.get("title_ru") or v.get("title"),
                "year": v.get("year"),
                "make": v.get("make"),
                "model": v.get("model"),
                "country": v.get("country"),
                "body_type": v.get("body_type"),
                "mileage_km": v.get("mileage_km"),
                "current_price_nzd": v.get("current_price_nzd"),
                "ai_estimate": v.get("ai_estimate"),
                "image": (v.get("local_images") or v.get("images") or [None])[0],
                "auction_ends_at": v.get("auction_ends_at"),
            })
        return out


def get_quiz_meta() -> Dict[str, Any]:
    """Static metadata used by the frontend wizard to render the steps."""
    return {
        "budgets": BUDGET_BUCKETS_RUB,
        "purposes": [
            {"key": k, "label": v} for k, v in PURPOSE_LABELS.items()
        ],
        "urgencies": [
            {"key": k, "label": v} for k, v in URGENCY_LABELS.items()
        ],
        "countries": [
            {"key": "NZ", "label": "Новая Зеландия"},
            {"key": "AU", "label": "Австралия"},
            {"key": None, "label": "Не важно"},
        ],
        "repairs": [
            {"key": k, "label": v} for k, v in REPAIR_LABELS.items()
        ],
        "buyer_types": [
            {"key": k, "label": v} for k, v in BUYER_TYPE_LABELS.items()
        ],
    }
