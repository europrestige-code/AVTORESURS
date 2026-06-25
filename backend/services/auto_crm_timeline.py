"""Deep CRM timeline — consolidate chat, leads, offers, bids and deposits
into a single chronological view per client.

A client can be identified either by:
- user_id (registered customer)
- phone / email (anonymous leads collected through the lead modal or quiz)

The service returns activity buckets + a flat sorted timeline so the admin UI
can render either as a list or grouped sections.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _iso(v: Any) -> Optional[str]:
    if isinstance(v, datetime):
        return v.isoformat()
    return v if v else None


def _ts(v: Any) -> float:
    """Sort key – returns POSIX timestamp, falling back to 0 for nulls."""
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.timestamp()
    if isinstance(v, str):
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except Exception:
            return 0.0
    return 0.0


class AutoCrmTimelineService:
    def __init__(self, db):
        self.db = db

    async def list_clients(self, limit: int = 200) -> List[Dict[str, Any]]:
        """All clients with activity, sorted by last_activity desc.

        Combines registered users + anonymous lead phones/emails. The shape
        intentionally matches the legacy `/admin/clients` payload so the
        existing UI still renders; we only add `last_activity` and counts.
        """
        out: Dict[str, Dict[str, Any]] = {}

        # 1) Registered users (role=customer)
        async for u in self.db.users.find({"role": "customer"}).sort("created_at", -1):
            u.pop("_id", None)
            u.pop("password_hash", None)
            key = f"u:{u['id']}"
            out[key] = {
                "id": u["id"],
                "kind": "user",
                "name": (u.get("full_name") or u.get("email") or "").strip(),
                "email": u.get("email"),
                "phone": u.get("phone"),
                "created_at": _iso(u.get("created_at")),
                "deposit_status": u.get("deposit_status"),
                "bidding_enabled": bool(u.get("bidding_enabled")),
                "interests": 0,
                "offers": 0,
                "bids": 0,
                "chat_messages": 0,
                "quiz_leads": 0,
                "last_activity": u.get("created_at"),
            }

        # 2) Per-user activity counts (single aggregate per collection)
        await self._fold_counts(out, "auto_interests", "interests")
        await self._fold_counts(out, "auto_offers", "offers")
        await self._fold_counts(out, "auto_bids", "bids")
        await self._fold_counts(out, "auto_chat_messages", "chat_messages")
        await self._fold_counts(out, "auto_quiz_leads", "quiz_leads")

        # 3) Anonymous interests (lead-modal + quiz) — group by phone
        async for lead in self.db.auto_interests.find({"user_id": None}):
            phone = (lead.get("phone") or "").strip()
            if not phone:
                continue
            key = f"p:{phone}"
            agg = out.get(key)
            if not agg:
                agg = out[key] = {
                    "id": phone,
                    "kind": "lead",
                    "name": lead.get("name") or "",
                    "email": lead.get("email"),
                    "phone": phone,
                    "created_at": _iso(lead.get("created_at")),
                    "deposit_status": None,
                    "bidding_enabled": False,
                    "interests": 0, "offers": 0, "bids": 0,
                    "chat_messages": 0, "quiz_leads": 0,
                    "last_activity": lead.get("created_at"),
                }
            agg["interests"] += 1
            if _ts(lead.get("created_at")) > _ts(agg.get("last_activity")):
                agg["last_activity"] = lead.get("created_at")
                if not agg.get("name"):
                    agg["name"] = lead.get("name") or agg["name"]

        # 4) Normalize last_activity -> iso, sort
        items: List[Dict[str, Any]] = []
        for v in out.values():
            v["last_activity"] = _iso(v.get("last_activity"))
            v["total_events"] = (
                v["interests"] + v["offers"] + v["bids"]
                + v["chat_messages"] + v["quiz_leads"]
            )
            items.append(v)
        items.sort(key=lambda x: _ts(x.get("last_activity")), reverse=True)
        return items[: int(limit)]

    async def _fold_counts(
        self, agg: Dict[str, Dict[str, Any]], coll_name: str, field: str
    ) -> None:
        coll = self.db[coll_name]
        async for doc in coll.aggregate([
            {"$match": {"user_id": {"$ne": None}}},
            {"$group": {
                "_id": "$user_id",
                "n": {"$sum": 1},
                "last": {"$max": "$created_at"},
            }},
        ]):
            user_id = doc["_id"]
            row = agg.get(f"u:{user_id}")
            if not row:
                continue
            row[field] = int(doc["n"])
            if _ts(doc.get("last")) > _ts(row.get("last_activity")):
                row["last_activity"] = doc.get("last")

    # ---------- Per-client timeline ----------
    async def timeline_for_user(self, user_id: str) -> Dict[str, Any]:
        user = await self.db.users.find_one({"id": user_id})
        if user:
            user.pop("_id", None)
            user.pop("password_hash", None)
            for k in ("created_at", "updated_at"):
                user[k] = _iso(user.get(k))

        events: List[Dict[str, Any]] = []
        events += await self._interests_events({"user_id": user_id})
        events += await self._offers_events({"user_id": user_id})
        events += await self._bids_events({"user_id": user_id})
        events += await self._chat_events({"user_id": user_id})
        events += await self._deposit_events({"user_id": user_id})
        events += await self._quiz_events({"user_id": user_id})
        events.sort(key=lambda e: _ts(e.get("at")), reverse=True)
        return {"client": user, "events": events}

    async def timeline_by_phone(self, phone: str) -> Dict[str, Any]:
        events: List[Dict[str, Any]] = []
        events += await self._interests_events({"phone": phone})
        events += await self._quiz_events({"contact": phone})
        events.sort(key=lambda e: _ts(e.get("at")), reverse=True)
        return {"client": {"phone": phone, "kind": "lead"}, "events": events}

    # ---------- Event builders ----------
    async def _interests_events(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        async for d in self.db.auto_interests.find(q).sort("created_at", -1):
            out.append({
                "type": "interest",
                "at": _iso(d.get("created_at")),
                "vehicle_id": d.get("vehicle_id"),
                "title": d.get("name") or "Заявка интереса",
                "body": d.get("message"),
                "meta": {
                    "phone": d.get("phone"),
                    "email": d.get("email"),
                    "city": d.get("city"),
                    "source": d.get("source"),
                    "budget_nzd": d.get("budget_nzd"),
                    "status": d.get("status"),
                },
            })
        return out

    async def _offers_events(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        async for d in self.db.auto_offers.find(q).sort("created_at", -1):
            out.append({
                "type": "offer",
                "at": _iso(d.get("created_at")),
                "vehicle_id": d.get("vehicle_id"),
                "title": f"Предложил цену NZ${int(d.get('offer_price_nzd') or 0):,}",
                "body": d.get("message"),
                "meta": {
                    "offer_price_nzd": d.get("offer_price_nzd"),
                    "status": d.get("status"),
                    "admin_response": d.get("admin_response"),
                },
            })
        return out

    async def _bids_events(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        async for d in self.db.auto_bids.find(q).sort("created_at", -1):
            max_bid = d.get("max_bid_nzd") or d.get("amount_nzd") or 0
            out.append({
                "type": "bid",
                "at": _iso(d.get("created_at")),
                "vehicle_id": d.get("vehicle_id"),
                "title": f"Поставил ставку до NZ${int(max_bid):,}",
                "body": d.get("notes"),
                "meta": {
                    "max_bid_nzd": d.get("max_bid_nzd"),
                    "status": d.get("status"),
                    "requires_deposit": d.get("requires_deposit"),
                },
            })
        return out

    async def _chat_events(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Collapse chat messages by session and return one event per session.
        sessions: Dict[str, Dict[str, Any]] = {}
        async for m in self.db.auto_chat_messages.find(q).sort("created_at", 1):
            sid = m.get("session_id") or "?"
            s = sessions.setdefault(sid, {
                "session_id": sid,
                "msgs": 0,
                "first_at": m.get("created_at"),
                "last_at": m.get("created_at"),
                "first_user_msg": None,
            })
            s["msgs"] += 1
            s["last_at"] = m.get("created_at")
            if m.get("role") == "user" and not s["first_user_msg"]:
                s["first_user_msg"] = m.get("content")
        out = []
        for s in sessions.values():
            out.append({
                "type": "chat",
                "at": _iso(s["last_at"]),
                "title": f"Диалог в чате · {s['msgs']} сообщ.",
                "body": s.get("first_user_msg"),
                "meta": {
                    "session_id": s["session_id"],
                    "first_at": _iso(s["first_at"]),
                },
            })
        return out

    async def _deposit_events(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        async for d in self.db.auto_deposits.find(q).sort("created_at", -1):
            out.append({
                "type": "deposit",
                "at": _iso(d.get("created_at")),
                "title": f"Депозит · {d.get('status', 'created')}",
                "body": d.get("notes"),
                "meta": {
                    "amount_nzd": d.get("amount_nzd"),
                    "status": d.get("status"),
                    "method": d.get("method"),
                    "refund_reason": d.get("refund_reason"),
                },
            })
        return out

    async def _quiz_events(self, q: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        async for d in self.db.auto_quiz_leads.find(q).sort("created_at", -1):
            out.append({
                "type": "quiz",
                "at": _iso(d.get("created_at")),
                "title": "Заполнил АИ-подборщик",
                "body": ", ".join(filter(None, [
                    d.get("purpose_label"),
                    d.get("urgency_label"),
                    ("Кузов: " + ", ".join(d.get("body_types") or [])) if d.get("body_types") else None,
                ])),
                "meta": {
                    "budget_rub_max": d.get("budget_rub_max"),
                    "country": d.get("country"),
                    "city": d.get("city"),
                    "contact": d.get("contact"),
                },
            })
        return out
