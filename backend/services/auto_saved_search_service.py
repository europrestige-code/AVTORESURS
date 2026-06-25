"""Saved-search engine — CRUD, matching, and run-on-demand entrypoint."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models.auto_saved_search import (
    SavedSearch,
    SavedSearchCreate,
    SavedSearchFilters,
)
from services.auto_body_types import mongo_filter_for_key

logger = logging.getLogger(__name__)
_FX_FALLBACK = 57.68
_PUBLIC_URL = (
    os.environ.get("PUBLIC_FRONTEND_URL")
    or "https://auto-nz-bidding.preview.emergentagent.com"
).rstrip("/")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _strip(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return doc
    doc.pop("_id", None)
    for k in ("created_at", "updated_at", "last_run_at"):
        v = doc.get(k)
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


def _filters_to_mongo(f: SavedSearchFilters, fx_rate: float) -> Dict[str, Any]:
    """Translate a SavedSearchFilters payload into a Mongo query against
    `auto_vehicles`. Always restricts to `status=available`."""
    q: Dict[str, Any] = {"status": "available"}
    if f.country:
        q["country"] = f.country
    if f.make:
        q["make"] = {"$regex": f"^{f.make}$", "$options": "i"}
    if f.model:
        q["model"] = {"$regex": f.model, "$options": "i"}
    if f.body_type:
        mf = mongo_filter_for_key(f.body_type)
        if mf:
            q["body_type"] = mf
    if f.year_from or f.year_to:
        rng: Dict[str, Any] = {}
        if f.year_from:
            rng["$gte"] = f.year_from
        if f.year_to:
            rng["$lte"] = f.year_to
        q["year"] = rng
    # Price: prefer NZD if explicit, else convert RUB → NZD via fx rate
    price_from = f.price_from_nzd
    price_to = f.price_to_nzd
    if price_from is None and f.price_from_rub:
        price_from = round(f.price_from_rub / fx_rate, 2) if fx_rate else None
    if price_to is None and f.price_to_rub:
        price_to = round(f.price_to_rub / fx_rate, 2) if fx_rate else None
    if price_from or price_to:
        rng = {}
        if price_from:
            rng["$gte"] = float(price_from)
        if price_to:
            rng["$lte"] = float(price_to)
        # Use $or so vehicles without current_price still match via AI estimate.
        q["$or"] = [
            {"current_price_nzd": rng},
            {"ai_estimate.recommended_max_bid_nzd": rng},
        ]
    if f.mileage_to_km:
        q["mileage_km"] = {"$lte": int(f.mileage_to_km)}
    if f.fuel:
        q["fuel"] = {"$regex": f.fuel, "$options": "i"}
    if f.damage_only:
        q["damage_type"] = {"$nin": [None, ""], "$exists": True}
    if f.keywords:
        q["$text"] = {"$search": f.keywords}  # best effort if index present
    return q


def _vehicle_card(v: Dict[str, Any]) -> Dict[str, Any]:
    """Pick a small, JSON-friendly subset of a vehicle for notifier payloads."""
    return {
        "id": v.get("id"),
        "title_ru": v.get("title_ru") or v.get("title"),
        "year": v.get("year"),
        "make": v.get("make"),
        "country": v.get("country"),
        "mileage_km": v.get("mileage_km"),
        "current_price_nzd": v.get("current_price_nzd"),
        "image": (v.get("local_images") or v.get("images") or [None])[0],
    }


class AutoSavedSearchService:
    def __init__(self, db):
        self.db = db
        self.coll = db.auto_saved_searches

    # ---------- CRUD ----------
    async def create(
        self,
        payload: SavedSearchCreate,
        user_id: str,
        email: Optional[str],
        telegram_chat_id: Optional[int],
    ) -> Dict[str, Any]:
        record = SavedSearch(
            user_id=user_id,
            name=payload.name.strip() or "Без названия",
            filters=payload.filters,
            channels=payload.channels,
            email=email,
            telegram_chat_id=telegram_chat_id,
        )
        await self.coll.insert_one(record.model_dump())
        return _strip(record.model_dump())

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        cur = self.coll.find({"user_id": user_id}).sort("created_at", -1)
        return [_strip(d) async for d in cur]

    async def delete(self, search_id: str, user_id: str) -> bool:
        r = await self.coll.delete_one({"id": search_id, "user_id": user_id})
        return bool(r.deleted_count)

    async def toggle(self, search_id: str, user_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        await self.coll.update_one(
            {"id": search_id, "user_id": user_id},
            {"$set": {"enabled": enabled, "updated_at": _now()}},
        )
        return _strip(await self.coll.find_one({"id": search_id, "user_id": user_id}))

    # ---------- Matching ----------
    async def preview_matches(
        self,
        filters: SavedSearchFilters,
        fx_rate: float,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        q = _filters_to_mongo(filters, fx_rate)
        cur = (
            self.db.auto_vehicles.find(q, {"_id": 0})
            .sort("created_at", -1)
            .limit(int(limit))
        )
        return [_vehicle_card(v) async for v in cur]

    async def run_all(self) -> Dict[str, Any]:
        """Iterate every enabled saved search; find vehicles created after
        `last_run_at` that match its filters; deliver via notifier; bump
        the watermark. Best-effort: failures are logged but don't raise."""
        from services.auto_fx_service import get_fx_rate
        from services.auto_notify_service import deliver_match_batch
        fx_payload = await get_fx_rate()
        fx_rate = float(fx_payload.get("nzd_to_rub_display") or _FX_FALLBACK)

        out = {"searches": 0, "notified": 0, "matches": 0, "errors": 0}
        async for s in self.coll.find({"enabled": True}):
            out["searches"] += 1
            try:
                filters = SavedSearchFilters(**(s.get("filters") or {}))
                q = _filters_to_mongo(filters, fx_rate)
                last_run = s.get("last_run_at")
                if last_run:
                    q["created_at"] = {"$gt": last_run}
                # Exclude already-notified vehicle ids (rolling 100-id window)
                seen = list(s.get("last_match_ids") or [])
                if seen:
                    q["id"] = {"$nin": seen[-100:]}
                cur = self.db.auto_vehicles.find(q, {"_id": 0}).sort("created_at", -1).limit(20)
                matches = [_vehicle_card(v) async for v in cur]
                if matches:
                    out["matches"] += len(matches)
                    # Lookup the user's preferred name
                    user = await self.db.users.find_one(
                        {"id": s.get("user_id")}, {"_id": 0, "full_name": 1, "email": 1}
                    )
                    user_name = (
                        (user or {}).get("full_name")
                        or (s.get("email") or "").split("@")[0]
                        or "клиент"
                    )
                    await deliver_match_batch(
                        user_name=user_name,
                        search_name=s.get("name") or "Подписка",
                        matches=matches,
                        fx_rate=fx_rate,
                        email=s.get("email") if (s.get("channels") or {}).get("email", True) else None,
                        telegram_chat_id=s.get("telegram_chat_id")
                            if (s.get("channels") or {}).get("telegram", False) else None,
                        public_url=_PUBLIC_URL,
                    )
                    out["notified"] += 1
                    new_seen = (seen + [m["id"] for m in matches])[-100:]
                    await self.coll.update_one(
                        {"id": s["id"]},
                        {
                            "$set": {
                                "last_run_at": _now(),
                                "last_match_ids": new_seen,
                                "updated_at": _now(),
                            },
                            "$inc": {"notify_count": len(matches)},
                        },
                    )
                else:
                    await self.coll.update_one(
                        {"id": s["id"]},
                        {"$set": {"last_run_at": _now(), "updated_at": _now()}},
                    )
            except Exception as e:
                out["errors"] += 1
                logger.warning(f"saved-search {s.get('id')} run error: {e}")
        return out
