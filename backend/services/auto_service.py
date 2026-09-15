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
    AutoLogisticsStatus,
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


# Heuristic: detect a vehicle that won't drive (and therefore needs to be
# towed → 2× transport per spec).
_NON_RUNNER_KEYWORDS = (
    "не заводится", "не запускается", "non-runner", "non runner",
    "non_runner", "won't start", "wont start", "не на ходу", "не на ход",
    "донор", "на запчасти", "parts only", "разбор", "engine damage",
    "engine seized", "no start", "for parts", "wreck", "wrecked", "salvage",
)


def _is_non_runner(vehicle: Dict[str, Any]) -> bool:
    if vehicle.get("is_non_runner") is True:
        return True
    haystack = " ".join(str(vehicle.get(k) or "") for k in (
        "condition", "damage_type", "description_ru", "description_original",
        "title_ru", "title_original",
    )).lower()
    return any(k in haystack for k in _NON_RUNNER_KEYWORDS)


def _estimate_ru_landed_for_vehicle(vehicle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Approximate "Ориентир под ключ" — Vladivostok-landed price with RU
    customs + utilsbor + freight, computed with vehicle-derived defaults.

    A simpler `calculate_price_breakdown()` is **not enough** for the inline
    «Ориентир под ключ» tile: it only sums the NZ-side fees + freight, never
    adding the Russian customs duty / утильсбор (which can be 100k–4M ₽).
    Without those, the displayed RUB total is grossly understated.

    This helper invokes the canonical `calculate_ru_landed_cost()` with the
    same sensible defaults the `/landed-defaults` endpoint exposes, so the
    inline tile, the LandedPriceModal and the customs calculator stay in
    sync.
    """
    fob = vehicle.get("current_price_nzd") or vehicle.get("buy_now_price_nzd")
    if not fob or float(fob) <= 0:
        return None

    import re as _re
    eng_txt = (vehicle.get("engine") or "").lower()
    engine_cc = 2000  # fallback (avg 2.0L) — declared engine missing from many scrapes
    m_cc = _re.search(r"(\d{3,4})\s*cc", eng_txt)
    m_l = _re.search(r"(\d(?:\.\d+)?)\s*l", eng_txt)
    if m_cc:
        engine_cc = int(m_cc.group(1))
    elif m_l:
        engine_cc = int(round(float(m_l.group(1)) * 1000))

    year = vehicle.get("year") or 0
    age_years = max(0, datetime.utcnow().year - int(year)) if year else 5

    from services.auto_ru_customs_service import (
        calculate_ru_landed_cost,
        suggest_defaults_for_listing,
    )
    defaults = suggest_defaults_for_listing(
        listing_type=vehicle.get("listing_type"),
        damage_type=vehicle.get("damage_type"),
        condition=vehicle.get("condition"),
    )
    try:
        res = calculate_ru_landed_cost(
            fob_nzd=float(fob),
            age_years=age_years,
            engine_cc=engine_cc,
            engine_hp=0,
            importer_type="personal",
            scheme=defaults.get("scheme", "whole"),
            nz_branch=vehicle.get("location"),
            is_non_runner=bool(defaults.get("is_non_runner") or _is_non_runner(vehicle)),
            inspection=bool(defaults.get("inspection")),
            forklift=bool(defaults.get("forklift")),
            dismantling=bool(defaults.get("dismantling")),
        )
    except Exception as e:
        logger.warning(f"landed estimate failed for vehicle {vehicle.get('id')}: {e}")
        return None
    return {
        "landed_total_rub": round(res.landed_total_rub, 2),
        "landed_total_nzd": round(res.landed_total_nzd, 2),
        "landed_total_usd": round(res.landed_total_usd, 2),
        "fob_nzd": round(res.fob_nzd, 2),
        "scheme": res.scheme,
        "assumed_engine_cc": engine_cc,
        "assumed_age_years": age_years,
    }


def calculate_price_breakdown(
    vehicle_price_nzd: float,
    storage_days: int = 0,
    forklift_nzd: float = 0.0,
    local_transport_nzd: Optional[float] = None,
    documentation_nzd: float = DOCUMENTATION_FEE,
    container_share_nzd: float = CONTAINER_SHARE,
    fx_rate_rub_nzd: Optional[float] = None,
    branch_or_city: Optional[str] = None,
    is_non_runner: bool = False,
) -> Dict[str, Any]:
    """Return pricing breakdown for a vehicle.

    estimated_total_nzd = price + commission + transport + forklift + storage
                       + documentation + container share

    Transport rules (per spec):
      • Auckland-area branches → $0 extra (default base $0).
      • Other NZ branches → city-specific surcharge from auto_transport_service.
      • Non-runners → 2 × transport.
      • If neither branch nor explicit override is provided, fall back to
        the legacy NZ$500 default so back-compat is preserved.
    """
    if vehicle_price_nzd is None or vehicle_price_nzd < 0:
        raise HTTPException(400, "Цена автомобиля должна быть неотрицательной.")
    commission = round(vehicle_price_nzd * COMMISSION_RATE, 2)
    storage = round(max(storage_days, 0) * STORAGE_RATE_PER_DAY, 2)

    transport_detail: Dict[str, Any]
    if local_transport_nzd is not None:
        # Caller forced a value; still apply the non-runner doubling rule.
        runner = float(local_transport_nzd)
        multiplier = 2.0 if is_non_runner else 1.0
        transport_amount = round(runner * multiplier, 2)
        transport_detail = {
            "branch": branch_or_city,
            "matched": False,
            "runner_nzd": runner,
            "is_non_runner": is_non_runner,
            "multiplier": multiplier,
            "transport_nzd": transport_amount,
        }
    elif branch_or_city:
        from services.auto_transport_service import transport_cost  # local to avoid cycle
        transport_detail = transport_cost(branch_or_city, is_non_runner=is_non_runner)
        transport_amount = float(transport_detail["transport_nzd"])
    else:
        runner = LOCAL_TRANSPORT_DEFAULT
        multiplier = 2.0 if is_non_runner else 1.0
        transport_amount = round(runner * multiplier, 2)
        transport_detail = {
            "branch": None,
            "matched": False,
            "runner_nzd": runner,
            "is_non_runner": is_non_runner,
            "multiplier": multiplier,
            "transport_nzd": transport_amount,
        }

    total_nzd = round(
        vehicle_price_nzd
        + commission
        + transport_amount
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
        "local_transport_nzd": transport_amount,
        "transport_detail": transport_detail,
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

        # body_type supports canonical English keys (sedan, suv, wagon, ...) that
        # match across EN/RU aliases stored in the DB. Anything else is treated
        # as an exact value (legacy behaviour).
        bt = filters.get("body_type")
        if bt:
            from services.auto_body_types import mongo_filter_for_key
            mf = mongo_filter_for_key(bt)
            query["body_type"] = mf if mf else bt

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
        # Two-tier sort: vehicles with a current auction price surface first
        # so the catalog's default page is never populated by price-less
        # scrapes; within each tier we keep recency order (newest first).
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "_has_price": {
                    "$cond": [
                        {"$gt": [{"$ifNull": ["$current_price_nzd", 0]}, 0]},
                        1, 0,
                    ]
                }
            }},
            {"$sort": {"_has_price": -1, "created_at": -1}},
            {"$skip": max(offset, 0)},
            {"$limit": min(max(limit, 1), 100)},
            {"$project": {"_has_price": 0, "_id": 0}},
        ]
        items = [v async for v in self.db.auto_vehicles.aggregate(pipeline)]
        # Apply UX-clamping on the AI estimate so catalog tiles never show
        # absurd low/high ranges that confuse customers.
        from services.auto_intel_engine import sanitize_ai_estimate
        for it in items:
            if it.get("ai_estimate"):
                it["ai_estimate"] = sanitize_ai_estimate(it, it["ai_estimate"])
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def get_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        doc = await self.db.auto_vehicles.find_one({"id": vehicle_id})
        if not doc:
            raise HTTPException(404, "Автомобиль не найден.")
        _strip_id(doc)
        highest = await self.get_highest_bid(vehicle_id)
        doc["highest_bid_nzd"] = highest.highest_bid_nzd
        doc["bid_count"] = highest.bid_count
        # Sanity-clamp AI estimate before the customer sees it — see
        # auto_intel_engine.sanitize_ai_estimate for the rules.
        if doc.get("ai_estimate"):
            from services.auto_intel_engine import sanitize_ai_estimate
            doc["ai_estimate"] = sanitize_ai_estimate(doc, doc["ai_estimate"])
        # Pricing breakdown preview if price known. Auto-infer transport from
        # `location` and detect non-runners by condition/damage.
        if doc.get("current_price_nzd"):
            non_runner = _is_non_runner(doc)
            doc["is_non_runner"] = non_runner
            doc["price_breakdown"] = calculate_price_breakdown(
                doc["current_price_nzd"],
                branch_or_city=doc.get("location"),
                is_non_runner=non_runner,
            )
            # Full "Ориентир под ключ" — includes RU customs + utilsbor +
            # freight, so the inline tile no longer shows just the FOB price.
            doc["landed_estimate"] = _estimate_ru_landed_for_vehicle(doc)
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
        # Detect transition to "won" to trigger CRM linkage
        new_status = updates.get("status")
        transitioning_to_won = False
        if new_status == AutoVehicleStatus.WON.value or new_status == AutoVehicleStatus.WON:
            current = await self.db.auto_vehicles.find_one({"id": vehicle_id})
            if current and current.get("status") != AutoVehicleStatus.WON.value:
                transitioning_to_won = True
        updates["updated_at"] = datetime.utcnow()
        result = await self.db.auto_vehicles.update_one({"id": vehicle_id}, {"$set": updates})
        if result.matched_count == 0:
            raise HTTPException(404, "Автомобиль не найден.")
        if transitioning_to_won:
            try:
                await self._on_vehicle_won(vehicle_id)
            except Exception as e:
                logger.warning(f"CRM linkage failed for vehicle {vehicle_id}: {e}")
        return await self.get_vehicle(vehicle_id)

    async def _on_vehicle_won(self, vehicle_id: str) -> None:
        """When a vehicle status flips to 'won': identify the winning bid,
        mark it as 'won' and the rest as 'lost', and create a CRMOrder record
        linked to the customer so they appear in the existing CRM."""
        vehicle = await self.db.auto_vehicles.find_one({"id": vehicle_id})
        if not vehicle:
            return
        # Pick the highest bid (active wins; otherwise highest by amount)
        winning = await self.db.auto_bids.find_one(
            {"vehicle_id": vehicle_id, "status": AutoBidStatus.ACTIVE.value},
            sort=[("max_bid_nzd", -1), ("created_at", 1)],
        )
        if not winning:
            winning = await self.db.auto_bids.find_one(
                {"vehicle_id": vehicle_id},
                sort=[("max_bid_nzd", -1), ("created_at", 1)],
            )
        if not winning:
            logger.info(f"Vehicle {vehicle_id} won but no bids found; skipping CRM link.")
            return
        await self.db.auto_bids.update_one(
            {"id": winning["id"]}, {"$set": {"status": AutoBidStatus.WON.value}}
        )
        await self.db.auto_bids.update_many(
            {"vehicle_id": vehicle_id, "id": {"$ne": winning["id"]},
             "status": {"$in": [AutoBidStatus.ACTIVE.value, AutoBidStatus.OUTBID.value]}},
            {"$set": {"status": AutoBidStatus.LOST.value}},
        )
        user = await self.db.users.find_one({"id": winning["user_id"]})
        if not user:
            return
        info = user.get("customer_info") or {}
        name = (
            f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
            or user.get("email")
            or "Клиент"
        )
        price = float(winning["max_bid_nzd"])
        bd = calculate_price_breakdown(price)
        crm_order_doc = {
            "id": __import__("uuid").uuid4().__str__(),
            "order_id": f"AUTO-{vehicle_id[:8].upper()}",
            "customer_id": user["id"],
            "customer_name": name,
            "customer_email": user.get("email", ""),
            "customer_phone": user.get("phone", "") or info.get("phone", ""),
            "product_name": vehicle.get("title_ru") or "Автомобиль",
            "product_url": vehicle.get("source_url"),
            "supplier_store": vehicle.get("source") or "BuyAnywhere Auto",
            "customer_paid_amount": price,
            "supplier_cost": price,
            "commission": bd["commission_nzd"],
            "profit": None,
            "status": "paid",
            "payment_status": "pending",
            "priority": "high",
            "created_at": datetime.utcnow(),
            "internal_notes": [f"Авто-сделка из BuyAnywhere Auto. Vehicle {vehicle_id}."],
            "customer_notes": None,
            "assigned_to": None,
            "source": "buyanywhere_auto",
            "auto_vehicle_id": vehicle_id,
            "auto_bid_id": winning["id"],
        }
        # idempotency: skip if already linked
        existing = await self.db.crm_orders.find_one({"auto_vehicle_id": vehicle_id})
        if existing:
            logger.info(f"CRM order already exists for vehicle {vehicle_id}")
            return
        await self.db.crm_orders.insert_one(crm_order_doc)
        # Auto-create a 'won' logistics event for the winning user
        await self.add_logistics_event(
            vehicle_id,
            AutoLogisticsEventCreate(
                user_id=winning["user_id"],
                status=AutoLogisticsStatus.WON,
                note_ru=f"Аукцион выигран. Сумма: NZ${price:,.0f}",
            ),
        )
        logger.info(f"Linked vehicle {vehicle_id} to CRM order {crm_order_doc['order_id']}")

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

        # Expensive-lot deposit rule (≥ NZ$10K → 30% deposit).
        from services.auto_payment_terms import required_deposit_nzd
        req = required_deposit_nzd(vehicle)
        if req["amount_nzd"] > 0:
            verified_amount = await self._verified_deposit_amount(user_id)
            if verified_amount + 0.01 < req["amount_nzd"]:
                raise HTTPException(
                    403,
                    (
                        f"Для ставки на этот лот требуется депозит "
                        f"NZ${req['amount_nzd']:,.0f} ({req['explanation']}). "
                        f"Сейчас подтверждено: NZ${verified_amount:,.0f}."
                    ),
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

    async def _verified_deposit_amount(self, user_id: str) -> float:
        """Sum of all VERIFIED deposit amounts for the user (used by the
        expensive-lot deposit rule)."""
        total = 0.0
        async for d in self.db.auto_deposits.find(
            {"user_id": user_id, "status": AutoDepositStatus.VERIFIED.value}
        ):
            total += float(d.get("amount_nzd") or 0)
        return total

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
