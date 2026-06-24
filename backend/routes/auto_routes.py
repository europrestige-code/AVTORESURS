"""
BuyAnywhere Auto - API router.

Mounted at /api/auto in server.py.

Auth model:
- Public endpoints: no token required.
- Client endpoints: require Bearer JWT from /api/auth/login.
- Admin endpoints: require user.role == "admin".
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import stripe
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models.auto import (
    AutoBidCreate,
    AutoCountry,
    AutoDeposit,
    AutoDepositCreate,
    AutoDepositMethod,
    AutoDepositStatus,
    AutoImageRights,
    AutoInquiry,
    AutoInquiryCreate,
    AutoInvoiceCreate,
    AutoListingType,
    AutoLogisticsEventCreate,
    AutoLogisticsStatus,
    AutoVehicle,
    AutoVehicleCreate,
    AutoVehicleStatus,
    AutoVehicleUpdate,
    StripeDepositRequest,
)
from services.auto_ai_service import AutoAIService
from services.auto_import_service import AutoImportService
from services.auto_service import (
    DEPOSIT_AMOUNT_NZD,
    AutoService,
    calculate_price_breakdown,
)
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto", tags=["Auto"])
security = HTTPBearer(auto_error=False)
auth_service = AuthService()


# ----- DB / services dependency injection -----

async def get_db():
    from server import db
    return db


async def get_auto_service(db=Depends(get_db)) -> AutoService:
    return AutoService(db)


_ai_service = AutoAIService()


def get_ai_service() -> AutoAIService:
    return _ai_service


def get_import_service() -> AutoImportService:
    return AutoImportService(_ai_service)


# ----- Auth helpers -----

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    try:
        payload = auth_service.verify_token(credentials.credentials)
    except HTTPException:
        return None
    user = await db.users.find_one({"id": payload.get("user_id")})
    if not user:
        return None
    user.pop("_id", None)
    return user


async def require_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db=Depends(get_db),
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(401, "Требуется авторизация.")
    payload = auth_service.verify_token(credentials.credentials)
    user = await db.users.find_one({"id": payload.get("user_id")})
    if not user:
        raise HTTPException(401, "Пользователь не найден.")
    user.pop("_id", None)
    return user


async def require_admin(user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(403, "Требуются права администратора.")
    return user


# ----- Public endpoints -----

@router.get("/vehicles")
async def list_vehicles(
    country: Optional[AutoCountry] = None,
    source: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    mileage_from: Optional[int] = None,
    mileage_to: Optional[int] = None,
    condition: Optional[str] = None,
    damage_type: Optional[str] = None,
    body_type: Optional[str] = None,
    listing_type: Optional[AutoListingType] = None,
    status_: Optional[AutoVehicleStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    svc: AutoService = Depends(get_auto_service),
):
    filters = {
        "country": country.value if country else None,
        "source": source,
        "make": make,
        "model": model,
        "year_from": year_from,
        "year_to": year_to,
        "price_from": price_from,
        "price_to": price_to,
        "mileage_from": mileage_from,
        "mileage_to": mileage_to,
        "condition": condition,
        "damage_type": damage_type,
        "body_type": body_type,
        "listing_type": listing_type.value if listing_type else None,
        "status": status_.value if status_ else None,
        "search": search,
    }
    return await svc.list_vehicles(filters, limit=limit, offset=offset)


@router.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str, svc: AutoService = Depends(get_auto_service)):
    return await svc.get_vehicle(vehicle_id)


@router.get("/vehicles/{vehicle_id}/highest-bid")
async def highest_bid(vehicle_id: str, svc: AutoService = Depends(get_auto_service)):
    res = await svc.get_highest_bid(vehicle_id)
    return res.model_dump()


@router.post("/price-breakdown")
async def price_breakdown(payload: Dict[str, Any] = Body(...)):
    return calculate_price_breakdown(
        vehicle_price_nzd=float(payload.get("vehicle_price_nzd", 0)),
        storage_days=int(payload.get("storage_days", 0)),
        forklift_nzd=float(payload.get("forklift_nzd", 0)),
        local_transport_nzd=(float(payload["local_transport_nzd"])
                              if payload.get("local_transport_nzd") not in (None, "") else None),
        documentation_nzd=float(payload.get("documentation_nzd", 250)),
        container_share_nzd=float(payload.get("container_share_nzd", 3333)),
        fx_rate_rub_nzd=payload.get("fx_rate_rub_nzd"),
        branch_or_city=payload.get("branch_or_city") or payload.get("location"),
        is_non_runner=bool(payload.get("is_non_runner", False)),
    )


@router.get("/transport/cost")
async def transport_cost_endpoint(
    branch: Optional[str] = None,
    non_runner: bool = False,
):
    from services.auto_transport_service import transport_cost
    return transport_cost(branch, is_non_runner=non_runner)


@router.get("/transport/pricing")
async def transport_pricing_endpoint():
    from services.auto_transport_service import list_branches
    return {"runner_nzd_by_branch": list_branches()}


@router.get("/ru-customs/calc")
async def ru_customs_calc(
    fob_nzd: float,
    age_years: int = 5,
    engine_cc: int = 2000,
    engine_hp: int = 150,
    importer_type: str = "personal",   # personal | commercial
    scheme: str = "whole",              # whole | parts
    include_nz_buyers_premium: bool = True,
    include_avtoresurs_commission: bool = True,
    # NZ-side extras
    nz_branch: Optional[str] = None,
    is_non_runner: bool = False,
    inspection: bool = False,
    forklift: bool = False,
    dismantling: bool = False,
    docs_fee: bool = True,
    storage_days: int = 0,
):
    """Approximate Vladivostok-landed cost for a NZ vehicle (RUB + USD + NZD).

    ⚠️ Quoted FOB prices on this site are auction-only. This endpoint adds
    NZ buyer's premium, AvtoResurs commission, branch-aware local transport
    (×2 if non-runner), optional inspection / forklift / dismantling / docs /
    storage, ocean freight (shared 40-ft container, $5k per car), insurance,
    Russian customs duty, VAT, excise (commercial) and утильсбор.
    Result is INDICATIVE and can vary ±10–15%.
    """
    from services.auto_ru_customs_service import calculate_ru_landed_cost
    if importer_type not in ("personal", "commercial"):
        raise HTTPException(400, "importer_type must be 'personal' or 'commercial'")
    if scheme not in ("whole", "parts"):
        raise HTTPException(400, "scheme must be 'whole' or 'parts'")
    if fob_nzd <= 0:
        raise HTTPException(400, "fob_nzd must be positive")
    res = calculate_ru_landed_cost(
        fob_nzd=fob_nzd,
        age_years=max(0, age_years),
        engine_cc=max(0, engine_cc),
        engine_hp=max(0, engine_hp),
        importer_type=importer_type,   # type: ignore[arg-type]
        scheme=scheme,                  # type: ignore[arg-type]
        include_nz_buyers_premium=include_nz_buyers_premium,
        include_avtoresurs_commission=include_avtoresurs_commission,
        nz_branch=nz_branch,
        is_non_runner=is_non_runner,
        inspection=inspection,
        forklift=forklift,
        dismantling=dismantling,
        docs_fee=docs_fee,
        storage_days=max(0, storage_days),
    )
    return res.to_dict()


@router.get("/vehicles/{vehicle_id}/landed-defaults")
async def vehicle_landed_defaults(
    vehicle_id: str,
    svc: AutoService = Depends(get_auto_service),
):
    """Return suggested defaults for the landed-price modal for this vehicle.

    DAMAGED → non-runner + forklift + inspection ON, scheme = whole
    END_OF_LIFE → non-runner + forklift + dismantling ON, scheme = parts
    AUCTION (clean) → all extras OFF, scheme = whole
    """
    from services.auto_ru_customs_service import suggest_defaults_for_listing
    v = await svc.db.auto_vehicles.find_one({"id": vehicle_id}, {"_id": 0})
    if not v:
        raise HTTPException(404, "Автомобиль не найден.")
    # try to extract engine size from `engine` text like "2.0L" or "1998cc"
    engine_cc = None
    eng_txt = (v.get("engine") or "").lower()
    import re as _re
    m_cc = _re.search(r"(\d{3,4})\s*cc", eng_txt)
    m_l = _re.search(r"(\d(?:\.\d+)?)\s*l", eng_txt)
    if m_cc:
        engine_cc = int(m_cc.group(1))
    elif m_l:
        engine_cc = int(round(float(m_l.group(1)) * 1000))
    # age
    year = v.get("year") or 0
    from datetime import datetime as _dt
    age = max(0, _dt.utcnow().year - year) if year else 5
    defaults = suggest_defaults_for_listing(
        listing_type=v.get("listing_type"),
        damage_type=v.get("damage_type"),
        condition=v.get("condition"),
    )
    return {
        "vehicle_id": vehicle_id,
        "fob_nzd": v.get("current_price_nzd") or v.get("buy_now_price_nzd"),
        "age_years": age,
        "engine_cc": engine_cc or 2000,
        "engine_hp": 0,
        "nz_branch": v.get("location") or "",
        "listing_type": v.get("listing_type"),
        **defaults,
    }


@router.get("/hot-daily")
async def hot_daily(
    svc: AutoService = Depends(get_auto_service),
):
    """Daily handpicks for Russian buyers — MAX 2 items.

    One «super new» (newest year) + one «super cheap» (lowest current price).
    Both must be:
      - listing_type = "auction"   (no fixed-price)
      - status = "available"
      - make ∈ popular-for-RU list (Toyota/Lexus/Honda/Mazda/Subaru/Nissan/…)
      - year ≥ current_year − 5   (under-5-years-old)
      - mileage ≤ 150 000 km (or unknown)
    """
    from datetime import datetime as _dt
    POPULAR_MAKES = [
        "toyota", "lexus", "honda", "mazda", "subaru", "nissan", "mitsubishi",
        "bmw", "mercedes-benz", "mercedes", "volkswagen", "vw", "audi",
        "hyundai", "kia", "infiniti", "porsche", "land rover",
    ]
    min_year = _dt.utcnow().year - 5
    makes_re = "(" + "|".join(POPULAR_MAKES) + ")"
    base_q = {
        "listing_type": "auction",
        "status": "available",
        "year": {"$gte": min_year},
        # Match popular makes either in the `make` column OR the parsed title.
        "$or": [
            {"make":     {"$regex": makes_re, "$options": "i"}},
            {"title_ru": {"$regex": makes_re, "$options": "i"}},
        ],
    }
    # Super new: newest year, lowest km
    super_new = await svc.db.auto_vehicles.find_one(
        base_q, {"_id": 0}, sort=[("year", -1), ("mileage_km", 1)]
    )
    # Super cheap: lowest current OR buy-now price (must be >0)
    cheap_q = dict(base_q)
    cheap_q["$and"] = [{
        "$or": [
            {"current_price_nzd": {"$gt": 0}},
            {"buy_now_price_nzd": {"$gt": 0}},
        ],
    }]
    super_cheap = await svc.db.auto_vehicles.find_one(
        cheap_q, {"_id": 0}, sort=[("current_price_nzd", 1)]
    )
    items = []
    if super_new:
        super_new["pick_label"] = "Самый свежий"
        items.append(super_new)
    if super_cheap and (not super_new or super_cheap.get("id") != super_new.get("id")):
        super_cheap["pick_label"] = "Самый выгодный"
        items.append(super_cheap)
    return {
        "count": len(items),
        "criteria": {
            "popular_makes": POPULAR_MAKES,
            "min_year": min_year,
            "max_km": 150_000,
        },
        "items": items,
    }


@router.get("/fx-rate")
async def fx_rate(force_refresh: bool = False):
    """Live NZD → RUB rate (Google/open.er-api spot) + 3% convenience markup."""
    from services.auto_fx_service import get_fx_rate
    return await get_fx_rate(force_refresh=force_refresh)


@router.get("/auctions/calendar")
async def auctions_calendar(
    city: Optional[str] = None,
    category: Optional[str] = None,
    days_ahead: int = 21,
    db=Depends(get_db),
):
    from services.auto_auctions_service import AuctionCalendarService
    svc = AuctionCalendarService(db)
    events = await svc.list_events(city=city, category=category, days_ahead=days_ahead)
    days = await svc.summary_by_day(days_ahead=days_ahead)
    return {"events": events, "by_day": days, "count": len(events)}


@router.post("/admin/auctions/refresh")
async def admin_refresh_auctions(
    payload: Optional[Dict[str, Any]] = Body(None),
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    from services.auto_auctions_service import AuctionCalendarService
    svc = AuctionCalendarService(db)
    cats = (payload or {}).get("categories") or ["cars", "damaged", "trucks"]
    return await svc.refresh(categories=cats)


# ----- Source importers (Turners / Manheim / Pickles) -----

@router.get("/admin/sources")
async def admin_list_sources(_: Dict[str, Any] = Depends(require_admin)):
    from services.auto_source_importers import IMPORTERS
    return {"sources": list(IMPORTERS.keys())}


@router.post("/admin/sources/scan")
async def admin_sources_scan(
    payload: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
    ai: AutoAIService = Depends(get_ai_service),
):
    """Run a single source importer in preview mode (no DB writes).
    Body: {source: 'turners'|'manheim'|'pickles', limit: int=20}"""
    from services.auto_source_importers import IMPORTERS, find_duplicate
    src = (payload.get("source") or "").lower()
    if src not in IMPORTERS:
        raise HTTPException(400, f"Неизвестный источник: {src}")
    limit = int(payload.get("limit", 20))
    cls = IMPORTERS[src]
    try:
        importer = cls(ai=ai, db=db)
    except TypeError:
        importer = cls(ai=ai)
    try:
        raw_items = await importer.fetch_vehicles(limit=limit)
    except Exception as e:
        return {"ok": False, "error": str(e), "items": []}
    items = []
    for raw in raw_items:
        try:
            vehicle = importer.normalise(raw)
            existing = await find_duplicate(db, vehicle)
            items.append({
                "vehicle": vehicle.model_dump(mode="json"),
                "duplicate_of": existing.get("id") if existing else None,
                "is_new": existing is None,
            })
        except Exception as e:
            items.append({"error": str(e), "raw": raw})
    return {
        "ok": True,
        "source": src,
        "fetched": len(raw_items),
        "new": sum(1 for i in items if i.get("is_new")),
        "duplicates": sum(1 for i in items if i.get("duplicate_of")),
        "items": items,
    }


@router.post("/admin/sources/import")
async def admin_sources_import(
    payload: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
    ai: AutoAIService = Depends(get_ai_service),
):
    """Import vehicles from one source.
    Body: {source, limit, skip_duplicates: bool=true, ids?: [source_reference,...]}.
    If `ids` is provided, only items whose source_reference is in that list are saved."""
    from services.auto_source_importers import IMPORTERS, ImportOrchestrator
    src = (payload.get("source") or "").lower()
    if src not in IMPORTERS:
        raise HTTPException(400, f"Неизвестный источник: {src}")
    limit = int(payload.get("limit", 20))
    ids_filter = set(payload.get("ids") or [])
    orchestrator = ImportOrchestrator(db, ai=ai)
    # Patch the orchestrator's run_one to respect the optional ids filter
    cls = IMPORTERS[src]
    try:
        importer = cls(ai=ai, db=db)
    except TypeError:
        importer = cls(ai=ai)
    try:
        raw_items = await importer.fetch_vehicles(limit=limit)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    from services.auto_source_importers import find_duplicate, ImportResult
    from models.auto import AutoSyncStatus
    res = ImportResult(importer=src)
    res.fetched = len(raw_items)
    skip_dups = payload.get("skip_duplicates", True)
    from datetime import datetime as _dt
    for raw in raw_items:
        try:
            vehicle = importer.normalise(raw)
            if ids_filter and (vehicle.source_reference or "") not in ids_filter:
                res.skipped += 1
                continue
            existing = await find_duplicate(db, vehicle)
            payload_doc = vehicle.model_dump()
            if existing:
                if skip_dups:
                    res.skipped += 1
                    continue
                payload_doc.pop("id", None)
                payload_doc.pop("created_at", None)
                payload_doc["updated_at"] = _dt.utcnow()
                payload_doc["last_sync_time"] = _dt.utcnow()
                await db.auto_vehicles.update_one(
                    {"id": existing["id"]}, {"$set": payload_doc}
                )
                res.updated += 1
            else:
                await db.auto_vehicles.insert_one(payload_doc)
                res.created += 1
        except Exception as e:
            res.failed += 1
            res.errors.append(str(e))
    from datetime import datetime as _dt2
    res.finished_at = _dt2.utcnow()
    if res.failed and res.created + res.updated == 0:
        res.sync_status = AutoSyncStatus.FAILED
    elif res.failed:
        res.sync_status = AutoSyncStatus.PARTIAL
    await db.auto_import_runs.insert_one(res.to_dict())
    return res.to_dict()


@router.get("/admin/sources/runs")
async def admin_sources_runs(
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
    limit: int = 25,
):
    items = []
    async for r in db.auto_import_runs.find().sort("started_at", -1).limit(limit):
        r.pop("_id", None)
        items.append(r)
    return items


@router.get("/admin/scheduler/status")
async def admin_scheduler_status(_: Dict[str, Any] = Depends(require_admin)):
    from services import auto_scheduler
    return auto_scheduler.status()


# ----- Public contacts -----

@router.get("/contacts")
async def contacts():
    """Public contact details for the floating contact bar and chat widget."""
    return {
        "whatsapp": "+64 21 425 233",
        "whatsapp_raw": "+6421425233",
        "phone_nz": "+64 21 080 94550",
        "phone_nz_raw": "+642108094550",
        "phone_ru": "+7 913 512 1934",
        "phone_ru_raw": "+79135121934",
        "email": "auto@buyanywhere.ru",
        "telegram": "@avtoresurs",
    }


# ----- AI chat (Тина) -----

@router.post("/chat")
async def chat(
    payload: Dict[str, Any] = Body(...),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    db=Depends(get_db),
):
    """Russian AI assistant trained on the АвтоРесурс business model.

    Body: {message: str, history?: [{role,content}], session_id?: str}.
    Anonymous use is allowed; logged-in users have their conversation
    history persisted to auto_chat_messages for follow-up by support.
    """
    from services.auto_chat_service import get_chat_service
    msg = (payload.get("message") or "").strip()
    if not msg:
        raise HTTPException(400, "Пустое сообщение.")
    history = payload.get("history") or []
    session_id = payload.get("session_id")
    svc = get_chat_service()
    result = await svc.reply(history, msg, session_id=session_id)
    # Persist for logged-in users
    if user:
        from datetime import datetime as _dt
        sid = result.get("session_id") or session_id
        await db.auto_chat_messages.insert_many([
            {"session_id": sid, "user_id": user["id"], "role": "user",
             "content": msg, "created_at": _dt.utcnow()},
            {"session_id": sid, "user_id": user["id"], "role": "assistant",
             "content": result.get("content", ""), "created_at": _dt.utcnow()},
        ])
    return result


# ----- Image branding backfill -----

@router.post("/admin/images/backfill-branding")
async def admin_backfill_branding(
    payload: Optional[Dict[str, Any]] = Body(None),
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    """Run the АвтоРесурс branded-frame overlay on existing vehicles.

    Body: {limit?: int=20, force?: bool=false, vehicle_ids?: [id,...]}.
    By default only processes vehicles that have source_images but no
    local_images (idempotent). Pass force=true to re-brand.
    """
    from services.auto_image_service import brand_vehicle_images
    payload = payload or {}
    limit = int(payload.get("limit", 20))
    force = bool(payload.get("force", False))
    vehicle_ids = payload.get("vehicle_ids") or []
    query: Dict[str, Any] = {}
    if vehicle_ids:
        query["id"] = {"$in": vehicle_ids}
    else:
        # Either explicit source_images list, OR `images` list, but no local_images yet
        query["$and"] = [
            {"$or": [
                {"source_images": {"$exists": True, "$ne": []}},
                {"images": {"$exists": True, "$ne": []}},
            ]},
        ]
        if not force:
            query["$and"].append(
                {"$or": [
                    {"local_images": {"$exists": False}},
                    {"local_images": {"$eq": []}},
                ]}
            )
    cursor = db.auto_vehicles.find(query).limit(limit)
    processed = 0
    branded_total = 0
    errors: List[Dict[str, Any]] = []
    async for v in cursor:
        v_id = v.get("id")
        source_imgs = v.get("source_images") or v.get("images") or []
        if not source_imgs:
            continue
        try:
            local_paths = await brand_vehicle_images(
                source_imgs[:6],
                vehicle_id=v_id,
                source_label=v.get("source") or "",
                vehicle_title=v.get("title_ru"),
            )
        except Exception as e:
            errors.append({"vehicle_id": v_id, "error": str(e)})
            continue
        if local_paths:
            await db.auto_vehicles.update_one(
                {"id": v_id},
                {"$set": {
                    "local_images": local_paths,
                    "image_rights_status": "admin_uploaded",
                    "updated_at": datetime.utcnow(),
                }},
            )
            branded_total += len(local_paths)
        processed += 1
    return {
        "processed": processed,
        "branded_images": branded_total,
        "errors": errors,
        "at": datetime.utcnow().isoformat(),
    }


@router.get("/catalog-summary")
async def catalog_summary(svc: AutoService = Depends(get_auto_service)):
    """Counts for the catalog hero (Turners-style): total + by body_type + by listing_type + makes."""
    base = {"status": {"$ne": AutoVehicleStatus.HIDDEN.value}}
    total = await svc.db.auto_vehicles.count_documents(base)

    async def _bucket(field: str, limit: int = 50):
        pipeline = [
            {"$match": base},
            {"$group": {"_id": f"${field}", "n": {"$sum": 1}}},
            {"$match": {"_id": {"$ne": None}}},
            {"$sort": {"n": -1}},
            {"$limit": limit},
        ]
        out = []
        async for row in svc.db.auto_vehicles.aggregate(pipeline):
            out.append({"value": row["_id"], "count": row["n"]})
        return out

    body_types = await _bucket("body_type")
    listing_types = await _bucket("listing_type")
    makes = await _bucket("make", limit=200)
    countries = await _bucket("country")
    # Category-style counters
    damaged_count = await svc.db.auto_vehicles.count_documents({
        **base,
        "$or": [
            {"condition": "Повреждённое"},
            {"damage_type": {"$nin": [None, "", "Без повреждений"]}},
        ],
    })
    eol_count = await svc.db.auto_vehicles.count_documents({
        **base,
        "$or": [
            {"condition": "На запчасти"},
            {"damage_type": {"$in": ["Двигатель", "Передний удар", "Тотал"]}},
        ],
    })
    # distinct models grouped by make for the cascading dropdown
    pipeline = [
        {"$match": {"$and": [base, {"make": {"$ne": None}}, {"model": {"$ne": None}}]}},
        {"$group": {"_id": {"make": "$make", "model": "$model"}, "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]
    models_by_make: Dict[str, List[Dict[str, Any]]] = {}
    async for row in svc.db.auto_vehicles.aggregate(pipeline):
        mk = row["_id"]["make"]; md = row["_id"]["model"]
        models_by_make.setdefault(mk, []).append({"value": md, "count": row["n"]})
    return {
        "total": total,
        "body_types": body_types,
        "listing_types": listing_types,
        "makes": makes,
        "countries": countries,
        "models_by_make": models_by_make,
        "damaged_count": damaged_count,
        "eol_count": eol_count,
    }


# ----- Client endpoints -----

@router.post("/vehicles/{vehicle_id}/bid")
async def place_bid(
    vehicle_id: str,
    payload: AutoBidCreate,
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.place_bid(vehicle_id, user["id"], payload.max_bid_nzd)


@router.get("/my/bids")
async def my_bids(
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.my_bids(user["id"])


@router.get("/my/dashboard")
async def my_dashboard(
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    data = await svc.my_dashboard(user["id"])
    data["user"] = {"id": user["id"], "email": user["email"], "role": user.get("role")}
    return data


@router.get("/my/deposit")
async def my_deposit(
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    d = await svc.latest_deposit(user["id"])
    return {
        "deposit": d,
        "verified": d is not None and d.get("status") == AutoDepositStatus.VERIFIED.value,
        "amount_required_nzd": DEPOSIT_AMOUNT_NZD,
    }


@router.post("/deposit/upload")
async def deposit_upload(
    amount: float = Form(DEPOSIT_AMOUNT_NZD),
    currency: str = Form("NZD"),
    method: str = Form("bank_transfer"),
    payment_proof_note: Optional[str] = Form(None),
    payment_proof_file: Optional[UploadFile] = File(None),
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    try:
        method_enum = AutoDepositMethod(method)
    except ValueError:
        raise HTTPException(400, "Неверный метод оплаты.")
    proof_name: Optional[str] = None
    if payment_proof_file is not None and payment_proof_file.filename:
        # Save to disk under /app/backend/uploads/deposits/
        ALLOWED = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif"}
        MAX_BYTES = 10 * 1024 * 1024  # 10 MB
        ext = os.path.splitext(payment_proof_file.filename)[1].lower()
        if ext not in ALLOWED:
            raise HTTPException(400, "Допустимы файлы: PDF, PNG, JPG, WEBP, HEIC.")
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "deposits")
        os.makedirs(uploads_dir, exist_ok=True)
        import uuid as _uuid
        stored_name = f"{_uuid.uuid4().hex}{ext}"
        stored_path = os.path.join(uploads_dir, stored_name)
        bytes_read = 0
        with open(stored_path, "wb") as f:
            while True:
                chunk = await payment_proof_file.read(1024 * 1024)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if bytes_read > MAX_BYTES:
                    f.close()
                    try:
                        os.remove(stored_path)
                    except OSError:
                        pass
                    raise HTTPException(400, "Файл слишком большой (макс. 10 МБ).")
                f.write(chunk)
        proof_name = stored_name
    deposit = AutoDeposit(
        user_id=user["id"],
        amount=float(amount),
        currency=currency,
        method=method_enum,
        payment_proof_file=proof_name,
        payment_proof_note=payment_proof_note,
        status=AutoDepositStatus.PENDING,
    )
    return await svc.create_deposit(deposit)


@router.get("/deposit/{deposit_id}/proof")
async def get_deposit_proof(
    deposit_id: str,
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    """Download deposit proof file. Owner or admin only."""
    deposit = await svc.db.auto_deposits.find_one({"id": deposit_id})
    if not deposit:
        raise HTTPException(404, "Депозит не найден.")
    if user["id"] != deposit["user_id"] and user.get("role") != "admin":
        raise HTTPException(403, "Доступ запрещён.")
    fname = deposit.get("payment_proof_file")
    if not fname:
        raise HTTPException(404, "Файл подтверждения не загружен.")
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "deposits")
    fpath = os.path.join(uploads_dir, fname)
    if not os.path.exists(fpath):
        raise HTTPException(404, "Файл не найден на диске.")
    from fastapi.responses import FileResponse
    return FileResponse(fpath, filename=fname)


@router.post("/deposit/stripe/session")
async def deposit_stripe_session(
    payload: StripeDepositRequest,
    request: Request,
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    """Create a Stripe Checkout Session for the deposit (server-defined amount)."""
    try:
        from emergentintegrations.payments.stripe.checkout import (
            CheckoutSessionRequest,
            StripeCheckout,
        )
    except Exception as e:
        raise HTTPException(500, f"Stripe модуль недоступен: {e}")

    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(500, "STRIPE_API_KEY не настроен.")

    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

    success_url = f"{payload.origin_url.rstrip('/')}/auto/dashboard?stripe_session={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{payload.origin_url.rstrip('/')}/auto/dashboard?stripe_cancelled=1"

    # Server-side amount; never trust frontend
    amount = float(DEPOSIT_AMOUNT_NZD)
    req = CheckoutSessionRequest(
        amount=amount,
        currency="nzd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user["id"], "purpose": "auto_deposit"},
    )
    session = await checkout.create_checkout_session(req)

    # Record an attempted deposit + payment_transactions entry
    deposit = AutoDeposit(
        user_id=user["id"],
        amount=amount,
        currency="NZD",
        method=AutoDepositMethod.STRIPE,
        stripe_session_id=session.session_id,
        payment_proof_note="Stripe Checkout",
        status=AutoDepositStatus.PENDING,
    )
    await svc.create_deposit(deposit)
    await svc.db.payment_transactions.insert_one(
        {
            "session_id": session.session_id,
            "user_id": user["id"],
            "amount": amount,
            "currency": "NZD",
            "purpose": "auto_deposit",
            "payment_status": "initiated",
            "deposit_id": deposit.id,
            "metadata": {"purpose": "auto_deposit"},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
    )
    return {"url": session.url, "session_id": session.session_id}


@router.get("/deposit/stripe/status/{session_id}")
async def deposit_stripe_status(
    session_id: str,
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
    except Exception as e:
        raise HTTPException(500, f"Stripe модуль недоступен: {e}")
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(500, "STRIPE_API_KEY не настроен.")
    checkout = StripeCheckout(api_key=api_key, webhook_url="")
    res = await checkout.get_checkout_status(session_id)

    tx = await svc.db.payment_transactions.find_one({"session_id": session_id})
    if not tx:
        raise HTTPException(404, "Платёж не найден.")
    if tx.get("user_id") != user["id"] and user.get("role") != "admin":
        raise HTTPException(403, "Доступ запрещён.")

    if tx.get("payment_status") != "paid":
        await svc.db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": res.payment_status,
                "status": res.status,
                "updated_at": datetime.utcnow(),
            }},
        )
        if res.payment_status == "paid":
            # Auto-verify the deposit upon successful Stripe payment
            await svc.db.auto_deposits.update_one(
                {"id": tx["deposit_id"]},
                {"$set": {
                    "status": AutoDepositStatus.VERIFIED.value,
                    "admin_note": "Auto-verified via Stripe",
                    "updated_at": datetime.utcnow(),
                }},
            )
    return {
        "payment_status": res.payment_status,
        "status": res.status,
        "amount_total": res.amount_total,
        "currency": res.currency,
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, svc: AutoService = Depends(get_auto_service)):
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
    except Exception as e:
        raise HTTPException(500, f"Stripe модуль недоступен: {e}")
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(500, "STRIPE_API_KEY не настроен.")
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    checkout = StripeCheckout(api_key=api_key, webhook_url="")
    try:
        ev = await checkout.handle_webhook(body, sig)
    except Exception as e:
        logger.warning(f"Stripe webhook error: {e}")
        raise HTTPException(400, "Невалидный webhook.")
    if ev.session_id:
        tx = await svc.db.payment_transactions.find_one({"session_id": ev.session_id})
        if tx and tx.get("payment_status") != "paid" and ev.payment_status == "paid":
            await svc.db.payment_transactions.update_one(
                {"session_id": ev.session_id},
                {"$set": {"payment_status": "paid", "updated_at": datetime.utcnow()}},
            )
            await svc.db.auto_deposits.update_one(
                {"id": tx["deposit_id"]},
                {"$set": {
                    "status": AutoDepositStatus.VERIFIED.value,
                    "admin_note": "Auto-verified via Stripe webhook",
                    "updated_at": datetime.utcnow(),
                }},
            )
    return {"received": True}


@router.post("/vehicles/{vehicle_id}/watchlist")
async def toggle_watchlist(
    vehicle_id: str,
    user: Dict[str, Any] = Depends(require_user),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.toggle_watchlist(user["id"], vehicle_id)


@router.post("/vehicles/{vehicle_id}/inquiry")
async def create_inquiry(
    vehicle_id: str,
    payload: AutoInquiryCreate,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    svc: AutoService = Depends(get_auto_service),
):
    inquiry = AutoInquiry(
        vehicle_id=vehicle_id,
        user_id=(user or {}).get("id"),
        name=payload.name or ((user or {}).get("customer_info") or {}).get("first_name"),
        email=payload.email or (user or {}).get("email"),
        phone=payload.phone or (user or {}).get("phone"),
        telegram=payload.telegram,
        message=payload.message[:4000],
    )
    return await svc.create_inquiry(inquiry)


# ----- Admin endpoints -----

@router.post("/admin/vehicles")
async def admin_create_vehicle(
    payload: AutoVehicleCreate,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    vehicle = AutoVehicle(**payload.model_dump())
    return await svc.create_vehicle(vehicle)


@router.put("/admin/vehicles/{vehicle_id}")
async def admin_update_vehicle(
    vehicle_id: str,
    payload: AutoVehicleUpdate,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    return await svc.update_vehicle(vehicle_id, update)


@router.delete("/admin/vehicles/{vehicle_id}")
async def admin_delete_vehicle(
    vehicle_id: str,
    hard: bool = Query(False),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    await svc.delete_vehicle(vehicle_id, hard=hard)
    return {"deleted": True, "hard": hard}


@router.post("/admin/import/from-text")
async def admin_import_text(
    payload: Dict[str, Any] = Body(...),
    save: bool = Query(False),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
    importer: AutoImportService = Depends(get_import_service),
):
    raw = (payload.get("text") or "").strip()
    result = await importer.import_from_text(raw, default_source=payload.get("source") or "manual_text")
    if save and result.get("ok"):
        vehicle = AutoVehicle(**result["vehicle"])
        result["saved"] = await svc.create_vehicle(vehicle)
    return result


@router.post("/admin/import/from-url")
async def admin_import_url(
    payload: Dict[str, Any] = Body(...),
    save: bool = Query(False),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
    importer: AutoImportService = Depends(get_import_service),
):
    url = (payload.get("url") or "").strip()
    result = await importer.import_from_url(url)
    if save and result.get("ok"):
        vehicle = AutoVehicle(**result["vehicle"])
        result["saved"] = await svc.create_vehicle(vehicle)
    return result


@router.post("/admin/import/csv")
async def admin_import_csv(
    csv_file: UploadFile = File(...),
    save: bool = Query(False),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
    importer: AutoImportService = Depends(get_import_service),
):
    content = (await csv_file.read()).decode("utf-8", errors="ignore")
    result = await importer.import_from_csv(content)
    if save and result.get("ok"):
        saved: List[Dict[str, Any]] = []
        for v in result["vehicles"]:
            vehicle = AutoVehicle(**v)
            saved.append(await svc.create_vehicle(vehicle))
        result["saved"] = saved
    return result


@router.post("/admin/vehicles/{vehicle_id}/ai-translate")
async def admin_ai_translate(
    vehicle_id: str,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
    ai: AutoAIService = Depends(get_ai_service),
):
    vehicle = await svc.get_vehicle(vehicle_id)
    out = await ai.translate_vehicle_to_russian(vehicle)
    updates: Dict[str, Any] = {}
    if out.get("title_ru"):
        updates["title_ru"] = out["title_ru"]
    if out.get("description_ru"):
        updates["description_ru"] = out["description_ru"]
    if updates:
        await svc.update_vehicle(vehicle_id, updates)
    return {"result": out, "updates": updates}


@router.post("/admin/vehicles/{vehicle_id}/ai-summary")
async def admin_ai_summary(
    vehicle_id: str,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
    ai: AutoAIService = Depends(get_ai_service),
):
    vehicle = await svc.get_vehicle(vehicle_id)
    out = await ai.generate_vehicle_risk_summary(vehicle)
    updates: Dict[str, Any] = {}
    if out.get("ai_summary_ru"):
        updates["ai_summary_ru"] = out["ai_summary_ru"]
    if out.get("ai_risk_summary_ru"):
        updates["ai_risk_summary_ru"] = out["ai_risk_summary_ru"]
    if updates:
        await svc.update_vehicle(vehicle_id, updates)
    return {"result": out, "updates": updates}


@router.get("/admin/bids")
async def admin_list_bids(
    vehicle_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status_: Optional[str] = Query(None, alias="status"),
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    query: Dict[str, Any] = {}
    if vehicle_id:
        query["vehicle_id"] = vehicle_id
    if user_id:
        query["user_id"] = user_id
    if status_:
        query["status"] = status_
    items: List[Dict[str, Any]] = []
    async for b in db.auto_bids.find(query).sort("created_at", -1):
        b.pop("_id", None)
        u = await db.users.find_one({"id": b["user_id"]})
        if u:
            b["user_email"] = u.get("email")
        v = await db.auto_vehicles.find_one({"id": b["vehicle_id"]})
        if v:
            b["vehicle_title_ru"] = v.get("title_ru")
        items.append(b)
    return items


@router.get("/admin/deposits")
async def admin_list_deposits(
    status_: Optional[str] = Query(None, alias="status"),
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    query: Dict[str, Any] = {}
    if status_:
        query["status"] = status_
    items: List[Dict[str, Any]] = []
    async for d in db.auto_deposits.find(query).sort("created_at", -1):
        d.pop("_id", None)
        u = await db.users.find_one({"id": d["user_id"]})
        if u:
            d["user_email"] = u.get("email")
        items.append(d)
    return items


@router.put("/admin/deposits/{deposit_id}/verify")
async def admin_verify_deposit(
    deposit_id: str,
    payload: Optional[Dict[str, Any]] = Body(None),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    note = (payload or {}).get("note")
    return await svc.admin_set_deposit_status(deposit_id, AutoDepositStatus.VERIFIED, admin_note=note)


@router.put("/admin/deposits/{deposit_id}/reject")
async def admin_reject_deposit(
    deposit_id: str,
    payload: Optional[Dict[str, Any]] = Body(None),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    note = (payload or {}).get("note") or "Отклонено администратором."
    return await svc.admin_set_deposit_status(deposit_id, AutoDepositStatus.REJECTED, admin_note=note)


@router.get("/admin/invoices")
async def admin_list_invoices(
    user_id: Optional[str] = None,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.list_invoices(user_id=user_id)


@router.post("/admin/invoices")
async def admin_create_invoice(
    payload: AutoInvoiceCreate,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.create_invoice(payload)


@router.get("/admin/logistics")
async def admin_list_logistics(
    vehicle_id: Optional[str] = None,
    user_id: Optional[str] = None,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.list_logistics(user_id=user_id, vehicle_id=vehicle_id)


@router.put("/admin/logistics/{vehicle_id}")
async def admin_add_logistics_event(
    vehicle_id: str,
    payload: AutoLogisticsEventCreate,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    return await svc.add_logistics_event(vehicle_id, payload)


@router.get("/admin/clients")
async def admin_list_clients(
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    items: List[Dict[str, Any]] = []
    async for u in db.users.find({"role": "customer"}).sort("created_at", -1):
        u.pop("_id", None)
        u.pop("password_hash", None)
        # latest deposit status
        d = await db.auto_deposits.find_one({"user_id": u["id"]}, sort=[("created_at", -1)])
        u["latest_deposit_status"] = (d or {}).get("status")
        items.append(u)
    return items


@router.post("/admin/vehicles/{vehicle_id}/mark-won")
async def admin_mark_vehicle_won(
    vehicle_id: str,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """Convenience action: flip vehicle to status='won' which triggers CRM linkage."""
    updated = await svc.update_vehicle(vehicle_id, {"status": AutoVehicleStatus.WON.value})
    crm = await svc.db.crm_orders.find_one({"auto_vehicle_id": vehicle_id})
    if crm:
        crm.pop("_id", None)
    return {"vehicle": updated, "crm_order": crm}


@router.get("/admin/crm-orders")
async def admin_list_crm_orders(
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    """List CRM orders that originated from BuyAnywhere Auto."""
    items: List[Dict[str, Any]] = []
    async for o in db.crm_orders.find({"source": "buyanywhere_auto"}).sort("created_at", -1):
        o.pop("_id", None)
        items.append(o)
    return items


# =============================================================================
# Email campaigns
# =============================================================================

@router.get("/admin/campaigns")
async def admin_list_campaigns(
    limit: int = 20,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """List the most recent email campaigns (drafts + sent)."""
    cursor = svc.db.auto_email_campaigns.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return {"items": [c async for c in cursor]}


@router.post("/admin/campaigns/generate")
async def admin_generate_campaign(
    slot: str = "morning",
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """Manually generate a new DRAFT campaign for the given slot."""
    from services.auto_email_service import generate_campaign_draft
    if slot not in ("morning", "evening"):
        raise HTTPException(400, "slot must be 'morning' or 'evening'")
    camp = await generate_campaign_draft(svc.db, slot=slot)
    if not camp:
        return {"created": False, "reason": "no eligible vehicles"}
    return {"created": True, "campaign": camp.model_dump()}


@router.get("/admin/campaigns/{campaign_id}")
async def admin_get_campaign(
    campaign_id: str,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    doc = await svc.db.auto_email_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Campaign not found")
    return doc


@router.get("/admin/campaigns/{campaign_id}/preview")
async def admin_preview_campaign(
    campaign_id: str,
    email: Optional[str] = None,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """Render the HTML email for one recipient (default: a sample address)."""
    from services.auto_email_service import render_email_html
    from models.auto import AutoEmailCampaign
    doc = await svc.db.auto_email_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Campaign not found")
    camp = AutoEmailCampaign(**doc)
    html = render_email_html(camp, email or "preview@avtoresurs.nz")
    return Response(content=html, media_type="text/html")


@router.post("/admin/campaigns/{campaign_id}/approve-send")
async def admin_approve_and_send(
    campaign_id: str,
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """Mark approved + ship via provider (stub by default)."""
    from services.auto_email_service import send_campaign
    try:
        camp = await send_campaign(svc.db, campaign_id)
        return {"sent": True, "campaign": camp.model_dump()}
    except ValueError as e:
        raise HTTPException(404, str(e))


# ----- Public unsubscribe endpoint -----

@router.get("/unsubscribe")
async def public_unsubscribe(
    email: str,
    token: str,
    svc: AutoService = Depends(get_auto_service),
):
    """Disable marketing emails for an address using a signed token.

    No login required — the HMAC token authenticates the request.
    """
    from services.auto_email_service import verify_unsub_token
    from datetime import datetime as _dt
    if not verify_unsub_token(email, token):
        raise HTTPException(400, "Invalid unsubscribe token")
    await svc.db.users.update_one(
        {"email": email.lower()},
        {"$set": {"customer_info.marketing_consent": False,
                  "updated_at": _dt.utcnow()}},
    )
    await svc.db.auto_email_unsubscribes.insert_one({
        "email": email.lower(),
        "token": token,
        "created_at": _dt.utcnow(),
    })
    return {
        "ok": True,
        "message": "Вы отписаны от рассылки. Возобновить можно в личном кабинете.",
    }


@router.get("/makes")
async def list_makes_and_models(
    svc: AutoService = Depends(get_auto_service),
):
    """Return every distinct make + its models (with counts) from the catalog.

    Powers cascading Make → Model dropdowns in filters and the homepage
    SearchPanel. Excludes nulls. Sorted by count DESC then alphabetically.
    """
    pipeline = [
        {"$match": {"make": {"$ne": None, "$exists": True}}},
        {"$group": {
            "_id": {"make": "$make", "model": "$model"},
            "count": {"$sum": 1},
        }},
        {"$group": {
            "_id": "$_id.make",
            "count": {"$sum": "$count"},
            "models": {"$push": {"model": "$_id.model", "count": "$count"}},
        }},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    items = []
    async for d in svc.db.auto_vehicles.aggregate(pipeline):
        models = sorted(
            [m for m in d["models"] if m.get("model")],
            key=lambda x: (-x["count"], x["model"]),
        )
        items.append({"make": d["_id"], "count": d["count"], "models": models})
    return {"items": items}


# =============================================================================
# Admin: app settings — editable API keys / integrations
# =============================================================================

@router.get("/admin/settings")
async def admin_get_settings(
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """Return the schema + current values (secrets masked)."""
    from services.auto_settings_service import list_for_admin
    return await list_for_admin(svc.db)


@router.put("/admin/settings")
async def admin_update_settings(
    payload: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(require_admin),
    svc: AutoService = Depends(get_auto_service),
):
    """Partial-update settings. Empty/masked secret fields are preserved."""
    from services.auto_settings_service import update_settings
    return await update_settings(svc.db, payload or {})
