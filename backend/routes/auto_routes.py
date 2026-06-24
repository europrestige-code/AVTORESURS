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
