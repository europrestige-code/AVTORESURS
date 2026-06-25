"""Engagement service — interests, offers, market summary.

Designed as a thin layer over Mongo so it can be wired into the existing
`auto_routes.py` without touching the heavier `auto_service.AutoService`.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from models.auto_engagement import (
    AutoInterest,
    AutoInterestCreate,
    AutoOffer,
    AutoOfferCreate,
    EngagementCounts,
    InterestStatus,
    OfferStatus,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _strip(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    doc.pop("_id", None)
    for k in ("created_at", "updated_at"):
        v = doc.get(k)
        if isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc


class AutoEngagementService:
    def __init__(self, db):
        self.db = db
        self.interests = db.auto_interests
        self.offers = db.auto_offers
        self.bids = db.auto_bids
        self.watchlist = db.auto_watchlist

    # ---------- Interest ----------
    async def create_interest(
        self,
        payload: AutoInterestCreate,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = AutoInterest(
            **payload.dict(),
            user_id=user_id,
        )
        await self.interests.insert_one(record.dict())
        # Silently mirror as a CRM contact so the sales team has it the moment
        # the lead is captured (best-effort — never fail the request on this).
        try:
            await self._mirror_to_crm(record)
        except Exception:
            pass
        return _strip(record.dict())

    async def list_interests(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        q: Dict[str, Any] = {}
        if status:
            q["status"] = status
        cur = self.interests.find(q).sort("created_at", -1).limit(int(limit))
        return [_strip(d) async for d in cur]

    async def update_interest_status(
        self, interest_id: str, status: str
    ) -> Optional[Dict[str, Any]]:
        if status not in InterestStatus.__members__:
            return None
        await self.interests.update_one(
            {"id": interest_id},
            {"$set": {"status": status, "updated_at": _now()}},
        )
        return _strip(await self.interests.find_one({"id": interest_id}))

    # ---------- Offer ----------
    async def create_offer(
        self, payload: AutoOfferCreate, user_id: str
    ) -> Dict[str, Any]:
        record = AutoOffer(**payload.dict(), user_id=user_id)
        await self.offers.insert_one(record.dict())
        return _strip(record.dict())

    async def list_offers(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        q: Dict[str, Any] = {}
        if status:
            q["status"] = status
        cur = self.offers.find(q).sort("created_at", -1).limit(int(limit))
        return [_strip(d) async for d in cur]

    async def my_offers(self, user_id: str) -> List[Dict[str, Any]]:
        cur = self.offers.find({"user_id": user_id}).sort("created_at", -1)
        return [_strip(d) async for d in cur]

    async def update_offer_status(
        self, offer_id: str, status: str, admin_response: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if status not in OfferStatus.__members__:
            return None
        upd: Dict[str, Any] = {"status": status, "updated_at": _now()}
        if admin_response is not None:
            upd["admin_response"] = admin_response
        await self.offers.update_one({"id": offer_id}, {"$set": upd})
        return _strip(await self.offers.find_one({"id": offer_id}))

    # ---------- Engagement counts (per vehicle) ----------
    async def engagement_counts(self, vehicle_id: str) -> EngagementCounts:
        return EngagementCounts(
            watchers=await self.watchlist.count_documents({"vehicle_id": vehicle_id}),
            interested=await self.interests.count_documents({"vehicle_id": vehicle_id}),
            offers=await self.offers.count_documents({"vehicle_id": vehicle_id}),
            bids=await self.bids.count_documents({"vehicle_id": vehicle_id}),
        )

    # ---------- Market summary (live strip on homepage) ----------
    async def market_summary(self) -> Dict[str, int]:
        v = self.db.auto_vehicles
        base = {"status": {"$ne": "hidden"}}
        now = _now()
        ending_soon_cut = now + timedelta(hours=48)

        return {
            "available": await v.count_documents(
                {**base, "listing_type": {"$in": ["auction", "buy_now"]}}
            ),
            "auctions_total": await v.count_documents(
                {**base, "listing_type": "auction"}
            ),
            "ending_soon": await v.count_documents(
                {
                    **base,
                    "listing_type": "auction",
                    "auction_ends_at": {"$gte": now, "$lte": ending_soon_cut},
                }
            ),
            "damaged": await v.count_documents(
                {**base, "damage_type": {"$nin": [None, ""], "$exists": True}}
            ),
            "buynow": await v.count_documents({**base, "listing_type": "buy_now"}),
            "interests_today": await self.interests.count_documents(
                {"created_at": {"$gte": now - timedelta(hours=24)}}
            ),
        }

    # ---------- Ending-soon carousel ----------
    async def ending_soon(self, limit: int = 8) -> List[Dict[str, Any]]:
        now = _now()
        cur = (
            self.db.auto_vehicles.find(
                {
                    "status": {"$ne": "hidden"},
                    "listing_type": "auction",
                    "auction_ends_at": {"$gte": now, "$lte": now + timedelta(hours=72)},
                }
            )
            .sort("auction_ends_at", 1)
            .limit(int(limit))
        )
        out: List[Dict[str, Any]] = []
        async for d in cur:
            d.pop("_id", None)
            for k in ("auction_ends_at", "created_at", "updated_at"):
                v = d.get(k)
                if isinstance(v, datetime):
                    d[k] = v.isoformat()
            out.append(d)
        return out

    # ---------- CRM bridge (best-effort) ----------
    async def _mirror_to_crm(self, lead: AutoInterest) -> None:
        """Best-effort: drop a Contact row so sales sees the lead instantly.

        We don't fail the inbound request if the parent CRM service isn't
        available — the engagement DB row is always the canonical store.
        """
        contacts = self.db.contacts
        if not contacts:
            return
        existing = await contacts.find_one({"phone": lead.phone})
        if existing:
            await contacts.update_one(
                {"id": existing["id"]},
                {
                    "$set": {
                        "last_engagement_at": _now(),
                        "last_engagement_source": lead.source,
                    },
                    "$inc": {"engagement_count": 1},
                },
            )
            # back-fill the interest with the CRM id
            await self.interests.update_one(
                {"id": lead.id},
                {"$set": {"crm_contact_id": existing.get("id")}},
            )
            return

        import uuid
        contact_doc = {
            "id": str(uuid.uuid4()),
            "first_name": lead.name.split(" ")[0] if lead.name else "",
            "last_name": " ".join(lead.name.split(" ")[1:]) if lead.name else "",
            "email": lead.email,
            "phone": lead.phone,
            "city": lead.city,
            "source": f"auto:{lead.source}",
            "tags": ["auto-lead"],
            "created_at": _now(),
            "updated_at": _now(),
            "last_engagement_at": _now(),
            "last_engagement_source": lead.source,
            "engagement_count": 1,
        }
        try:
            await contacts.insert_one(contact_doc)
            await self.interests.update_one(
                {"id": lead.id},
                {"$set": {"crm_contact_id": contact_doc["id"]}},
            )
        except Exception:
            pass
