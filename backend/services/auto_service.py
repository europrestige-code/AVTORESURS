"""
BuyAnywhere Auto - business logic service.

Encapsulates DB access + pricing/bid rules so route handlers stay thin.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.auto import (
    AutoBid,
    AutoBidStatus,
    AutoCountry,
    AutoDeposit,
    AutoDepositStatus,
    AutoInvoice,
    AutoInvoiceCreate,
    AutoInquiry,
    AutoListingType,
    AutoLogisticsEvent,
    AutoLogisticsEventCreate,
    AutoVehicle,
    AutoVehicleStatus,
    AutoWatchlistItem,
    HighestBidResponse,
)

logger = logging.getLogger(__name__)

# Pricing defaults (NZD)
COMMISSION_RATE = 0.20
STORAGE_RATE_PER_DAY = 50.0
DOCUMENTATION_FEE = 250.0
CONTAINER_SHARE = 3333.0
LOCAL_TRANSPORT_DEFAULT = 500.0
DEPOSIT_AMOUNT_NZD = 1000.0


def _strip_id(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


def calculate_price_breakdown(
    vehicle_price_nzd: float,
    storage_days: int = 0,
    forklift_nzd: float = 0.0,
    local_transport_nzd: float = LOCAL_TRANSPORT_DEFAULT,
    documentation_nzd: float = DOCUMENTATION_FEE,
    container_share_nzd: float = CONTAINER_SHARE,
    fx_rate_rub_nzd: Optional[float] = None,
) -> Dict[str, float]:
    """Return pricing breakdown for a vehicle.

    estimated_total_nzd = price + commission + transport + forklift + storage
                       + documentation + container share
    """
    if vehicle_price_nzd is None or vehicle_price_nzd < 0:
        raise HTTPException(400, "Цена автомобиля должна быть неотрицательной.")
    commission = round(vehicle_price_nzd * COMMISSION_RATE, 2)
    storage = round(max(storage_days, 0) * STORAGE_RATE_PER_DAY, 2)
    total_nzd = round(
        vehicle_price_nzd
        + commission
        + local_transport_nzd
        + forklift_nzd
        + storage
        + documentation_nzd
        + container_share_nzd,
        2,
    )
    total_rub = round(total_nzd * fx_rate_rub_nzd, 2) if fx_rate_rub_nzd else None
    return {
        "vehicle_price_nzd": round(vehicle_price_nzd, 2),
        "commission_nzd": commission,
        "local_transport_nzd": round(local_transport_nzd, 2),
        "forklift_nzd": round(forklift_nzd, 2),
        "storage_days": storage_days,
        "storage_nzd": storage,
        "documentation_nzd": round(documentation_nzd, 2),
        "container_share_nzd": round(container_share_nzd, 2),
        "fx_rate_rub_nzd": fx_rate_rub_nzd,
        "total_nzd": total_nzd,
        "total_rub": total_rub,
    }


class AutoService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    # ---- indexes ----
    async def ensure_indexes(self) -> None:
        try:
            await self.db.auto_vehicles.create_index("source_reference")
            await self.db.auto_vehicles.create_index("source")
            await self.db.auto_vehicles.create_index("country")
            await self.db.auto_vehicles.create_index("make")
            await self.db.auto_vehicles.create_index("model")
            await self.db.auto_vehicles.create_index("year")
            await self.db.auto_vehicles.create_index("status")
            await self.db.auto_vehicles.create_index("auction_end_time")
            await self.db.auto_vehicles.create_index("listing_type")
            await self.db.auto_bids.create_index("vehicle_id")
            await self.db.auto_bids.create_index("user_id")
            await self.db.auto_bids.create_index("status")
            await self.db.auto_bids.create_index("created_at")
            await self.db.auto_deposits.create_index("user_id")
            await self.db.auto_deposits.create_index("status")
            await self.db.auto_watchlist.create_index([("user_id", 1), ("vehicle_id", 1)], unique=True)
            logger.info("Auto module indexes ensured.")
        except Exception as e:
            logger.warning(f"Could not ensure auto indexes: {e}")

    # ---- vehicles ----
    async def list_vehicles(self, filters: Dict[str, Any], limit: int, offset: int) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        # hide hidden vehicles from public unless caller asks
        explicit_status = filters.get("status")
        if explicit_status:
            query["status"] = explicit_status
        else:
            query["status"] = {"$ne": AutoVehicleStatus.HIDDEN.value}

        for key in ("country", "source", "make", "model", "listing_type", "condition", "damage_type"):
            val = filters.get(key)
            if val:
                query[key] = val

        if filters.get("year_from") or filters.get("year_to"):
            year_q: Dict[str, Any] = {}
            if filters.get("year_from"):
                year_q["$gte"] = int(filters["year_from"])
            if filters.get("year_to"):
                year_q["$lte"] = int(filters["year_to"])
            query["year"] = year_q

        if filters.get("price_from") or filters.get("price_to"):
            p_q: Dict[str, Any] = {}
            if filters.get("price_from"):
                p_q["$gte"] = float(filters["price_from"])
            if filters.get("price_to"):
                p_q["$lte"] = float(filters["price_to"])
            query["current_price_nzd"] = p_q

        if filters.get("mileage_from") or filters.get("mileage_to"):
            m_q: Dict[str, Any] = {}
            if filters.get("mileage_from"):
                m_q["$gte"] = int(filters["mileage_from"])
            if filters.get("mileage_to"):
                m_q["$lte"] = int(filters["mileage_to"])
            query["mileage_km"] = m_q

        if filters.get("search"):
            term = filters["search"].strip()
            if term:
                query["$or"] = [
                    {"title_ru": {"$regex": term, "$options": "i"}},
                    {"title_original": {"$regex": term, "$options": "i"}},
                    {"make": {"$regex": term, "$options": "i"}},
                    {"model": {"$regex": term, "$options": "i"}},
                    {"source_reference": {"$regex": term, "$options": "i"}},
                ]

        total = await self.db.auto_vehicles.count_documents(query)
        cursor = (
            self.db.auto_vehicles.find(query)
            .sort("created_at", -1)
            .skip(max(offset, 0))
            .limit(min(max(limit, 1), 100))
        )
        items = [_strip_id(v) async for v in cursor]
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def get_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        doc = await self.db.auto_vehicles.find_one({"id": vehicle_id})
        if not doc:
            raise HTTPException(404, "Автомобиль не найден.")
        _strip_id(doc)
        highest = await self.get_highest_bid(vehicle_id)
        doc["highest_bid_nzd"] = highest.highest_bid_nzd
        doc["bid_count"] = highest.bid_count
        # Pricing breakdown preview if price known
        if doc.get("current_price_nzd"):
            doc["price_breakdown"] = calculate_price_breakdown(doc["current_price_nzd"])
        return doc

    async def create_vehicle(self, vehicle: AutoVehicle) -> Dict[str, Any]:
        if vehicle.current_price_nzd is not None and vehicle.current_price_nzd < 0:
            raise HTTPException(400, "Цена не может быть отрицательной.")
        if vehicle.current_price_nzd:
            vehicle.estimated_total_nzd = calculate_price_breakdown(vehicle.current_price_nzd)["total_nzd"]
        if not vehicle.title_ru:
            vehicle.title_ru = vehicle.title_original or "Автомобиль"
        data = vehicle.model_dump()
        await self.db.auto_vehicles.insert_one(data)
        return _strip_id(data)

    async def update_vehicle(self, vehicle_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if "current_price_nzd" in updates and updates["current_price_nzd"] is not None:
            if updates["current_price_nzd"] < 0:
                raise HTTPException(400, "Цена не может быть отрицательной.")
            updates["estimated_total_nzd"] = calculate_price_breakdown(updates["current_price_nzd"])["total_nzd"]
        updates["updated_at"] = datetime.utcnow()
        result = await self.db.auto_vehicles.update_one({"id": vehicle_id}, {"$set": updates})
        if result.matched_count == 0:
            raise HTTPException(404, "Автомобиль не найден.")
        return await self.get_vehicle(vehicle_id)

    async def delete_vehicle(self, vehicle_id: str, hard: bool = False) -> None:
        if hard:
            await self.db.auto_vehicles.delete_one({"id": vehicle_id})
            return
        result = await self.db.auto_vehicles.update_one(
            {"id": vehicle_id},
            {"$set": {"status": AutoVehicleStatus.HIDDEN.value, "updated_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            raise HTTPException(404, "Автомобиль не найден.")

    # ---- bids ----
    async def get_highest_bid(self, vehicle_id: str) -> HighestBidResponse:
        pipeline = [
            {"$match": {"vehicle_id": vehicle_id, "status": AutoBidStatus.ACTIVE.value}},
            {
                "$group": {
                    "_id": "$vehicle_id",
                    "highest": {"$max": "$max_bid_nzd"},
                    "count": {"$sum": 1},
                }
            },
        ]
        async for row in self.db.auto_bids.aggregate(pipeline):
            return HighestBidResponse(
                vehicle_id=vehicle_id,
                highest_bid_nzd=float(row.get("highest") or 0.0),
                bid_count=int(row.get("count") or 0),
            )
        # No active bids; count all bids for reference
        total = await self.db.auto_bids.count_documents({"vehicle_id": vehicle_id})
        return HighestBidResponse(vehicle_id=vehicle_id, highest_bid_nzd=0.0, bid_count=total)

    async def place_bid(self, vehicle_id: str, user_id: str, max_bid_nzd: float) -> Dict[str, Any]:
        if max_bid_nzd is None or max_bid_nzd <= 0:
            raise HTTPException(400, "Ставка должна быть положительным числом.")
        vehicle = await self.db.auto_vehicles.find_one({"id": vehicle_id})
        if not vehicle:
            raise HTTPException(404, "Автомобиль не найден.")
        if vehicle.get("country") != AutoCountry.NZ.value:
            raise HTTPException(400, "Ставки доступны только для автомобилей из Новой Зеландии.")
        if vehicle.get("listing_type") != AutoListingType.AUCTION.value:
            raise HTTPException(400, "Этот автомобиль не участвует в аукционе.")
        if vehicle.get("status") != AutoVehicleStatus.AVAILABLE.value:
            raise HTTPException(400, "Автомобиль недоступен для ставок.")

        if not await self.user_has_verified_auto_deposit(user_id):
            raise HTTPException(
                403,
                "Для участия в торгах требуется подтверждённый депозит NZ$1,000.",
            )

        highest = await self.get_highest_bid(vehicle_id)
        if max_bid_nzd == highest.highest_bid_nzd:
            raise HTTPException(
                400,
                "Такая ставка уже существует. Укажите сумму выше текущей максимальной ставки.",
            )
        if max_bid_nzd < highest.highest_bid_nzd:
            raise HTTPException(
                400,
                f"Ставка должна превышать текущую максимальную ставку (NZ${highest.highest_bid_nzd:.0f}).",
            )

        # Mark all previous active bids on this vehicle as outbid
        await self.db.auto_bids.update_many(
            {"vehicle_id": vehicle_id, "status": AutoBidStatus.ACTIVE.value},
            {"$set": {"status": AutoBidStatus.OUTBID.value}},
        )

        bid = AutoBid(vehicle_id=vehicle_id, user_id=user_id, max_bid_nzd=float(max_bid_nzd))
        await self.db.auto_bids.insert_one(bid.model_dump())

        # Update current_price_nzd to the new highest visible price (informational)
        await self.db.auto_vehicles.update_one(
            {"id": vehicle_id},
            {"$set": {"current_price_nzd": float(max_bid_nzd), "updated_at": datetime.utcnow()}},
        )

        return {
            "bid": _strip_id(bid.model_dump()),
            "highest_bid_nzd": float(max_bid_nzd),
        }

    async def my_bids(self, user_id: str) -> List[Dict[str, Any]]:
        bids: List[Dict[str, Any]] = []
        cursor = self.db.auto_bids.find({"user_id": user_id}).sort("created_at", -1)
        async for b in cursor:
            _strip_id(b)
            v = await self.db.auto_vehicles.find_one({"id": b["vehicle_id"]})
            if v:
                _strip_id(v)
                b["vehicle"] = {
                    "id": v.get("id"),
                    "title_ru": v.get("title_ru"),
                    "images": v.get("images", []),
                    "current_price_nzd": v.get("current_price_nzd"),
                    "auction_end_time": v.get("auction_end_time"),
                    "status": v.get("status"),
                }
            bids.append(b)
        return bids

    # ---- deposits ----
    async def user_has_verified_auto_deposit(self, user_id: str) -> bool:
        doc = await self.db.auto_deposits.find_one(
            {"user_id": user_id, "status": AutoDepositStatus.VERIFIED.value}
        )
        return doc is not None

    async def latest_deposit(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.db.auto_deposits.find_one(
            {"user_id": user_id}, sort=[("created_at", -1)]
        )
        return _strip_id(doc) if doc else None

    async def create_deposit(self, deposit: AutoDeposit) -> Dict[str, Any]:
        if deposit.amount <= 0:
            raise HTTPException(400, "Сумма депозита должна быть положительной.")
        data = deposit.model_dump()
        await self.db.auto_deposits.insert_one(data)
        return _strip_id(data)

    async def admin_set_deposit_status(
        self, deposit_id: str, new_status: AutoDepositStatus, admin_note: Optional[str] = None
    ) -> Dict[str, Any]:
        update: Dict[str, Any] = {"status": new_status.value, "updated_at": datetime.utcnow()}
        if admin_note is not None:
            update["admin_note"] = admin_note
        result = await self.db.auto_deposits.update_one({"id": deposit_id}, {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(404, "Депозит не найден.")
        doc = await self.db.auto_deposits.find_one({"id": deposit_id})
        return _strip_id(doc)

    # ---- watchlist ----
    async def toggle_watchlist(self, user_id: str, vehicle_id: str) -> Dict[str, Any]:
        existing = await self.db.auto_watchlist.find_one({"user_id": user_id, "vehicle_id": vehicle_id})
        if existing:
            await self.db.auto_watchlist.delete_one({"_id": existing["_id"]})
            return {"watching": False}
        item = AutoWatchlistItem(user_id=user_id, vehicle_id=vehicle_id)
        await self.db.auto_watchlist.insert_one(item.model_dump())
        return {"watching": True}

    async def my_watchlist(self, user_id: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        async for w in self.db.auto_watchlist.find({"user_id": user_id}).sort("created_at", -1):
            _strip_id(w)
            v = await self.db.auto_vehicles.find_one({"id": w["vehicle_id"]})
            if v:
                _strip_id(v)
                items.append(v)
        return items

    # ---- inquiries ----
    async def create_inquiry(self, inquiry: AutoInquiry) -> Dict[str, Any]:
        data = inquiry.model_dump()
        await self.db.auto_inquiries.insert_one(data)
        return _strip_id(data)

    async def my_inquiries(self, user_id: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        async for q in self.db.auto_inquiries.find({"user_id": user_id}).sort("created_at", -1):
            items.append(_strip_id(q))
        return items

    # ---- invoices ----
    async def create_invoice(self, payload: AutoInvoiceCreate) -> Dict[str, Any]:
        bd = calculate_price_breakdown(
            payload.vehicle_price_nzd,
            storage_days=payload.storage_days,
            forklift_nzd=payload.forklift_nzd,
            local_transport_nzd=payload.local_transport_nzd,
            documentation_nzd=payload.documentation_nzd,
            container_share_nzd=payload.container_share_nzd,
            fx_rate_rub_nzd=payload.fx_rate_rub_nzd,
        )
        invoice = AutoInvoice(
            user_id=payload.user_id,
            vehicle_id=payload.vehicle_id,
            vehicle_price_nzd=bd["vehicle_price_nzd"],
            commission_nzd=bd["commission_nzd"],
            local_transport_nzd=bd["local_transport_nzd"],
            forklift_nzd=bd["forklift_nzd"],
            storage_days=bd["storage_days"],
            storage_nzd=bd["storage_nzd"],
            documentation_nzd=bd["documentation_nzd"],
            container_share_nzd=bd["container_share_nzd"],
            fx_rate_rub_nzd=bd["fx_rate_rub_nzd"],
            total_nzd=bd["total_nzd"],
            total_rub=bd["total_rub"],
            status=payload.status,
        )
        await self.db.auto_invoices.insert_one(invoice.model_dump())
        return _strip_id(invoice.model_dump())

    async def list_invoices(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"user_id": user_id} if user_id else {}
        items: List[Dict[str, Any]] = []
        async for i in self.db.auto_invoices.find(query).sort("created_at", -1):
            items.append(_strip_id(i))
        return items

    # ---- logistics ----
    async def add_logistics_event(self, vehicle_id: str, payload: AutoLogisticsEventCreate) -> Dict[str, Any]:
        event = AutoLogisticsEvent(
            vehicle_id=vehicle_id,
            user_id=payload.user_id,
            status=payload.status,
            note_ru=payload.note_ru,
        )
        await self.db.auto_logistics_events.insert_one(event.model_dump())
        return _strip_id(event.model_dump())

    async def list_logistics(self, user_id: Optional[str] = None, vehicle_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if vehicle_id:
            query["vehicle_id"] = vehicle_id
        items: List[Dict[str, Any]] = []
        async for e in self.db.auto_logistics_events.find(query).sort("created_at", 1):
            items.append(_strip_id(e))
        return items

    # ---- dashboards ----
    async def my_dashboard(self, user_id: str) -> Dict[str, Any]:
        deposit = await self.latest_deposit(user_id)
        bids = await self.my_bids(user_id)
        watchlist = await self.my_watchlist(user_id)
        invoices = await self.list_invoices(user_id)
        logistics = await self.list_logistics(user_id)
        inquiries = await self.my_inquiries(user_id)
        return {
            "deposit": deposit,
            "deposit_verified": deposit is not None and deposit.get("status") == AutoDepositStatus.VERIFIED.value,
            "deposit_amount_required_nzd": DEPOSIT_AMOUNT_NZD,
            "bids": bids,
            "watchlist": watchlist,
            "invoices": invoices,
            "logistics": logistics,
            "inquiries": inquiries,
        }
