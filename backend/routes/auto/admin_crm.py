"""Admin CRM endpoints — deep client list, merged timelines, CRM orders,
plus the lightweight admin endpoints for leads (interests + offers)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ._deps import get_db, get_engagement_service, require_admin
from services.auto_service import AutoService
from models.auto import AutoVehicleStatus

from ._deps import get_auto_service

router = APIRouter()


# ---------- Lead queues (interests + offers) ----------

@router.get("/admin/interests")
async def admin_list_interests(
    status: Optional[str] = None,
    limit: int = 100,
    _: Dict[str, Any] = Depends(require_admin),
    eng=Depends(get_engagement_service),
):
    return {"items": await eng.list_interests(status=status, limit=limit)}


@router.patch("/admin/interests/{interest_id}/status")
async def admin_update_interest(
    interest_id: str,
    payload: Dict[str, Any],
    _: Dict[str, Any] = Depends(require_admin),
    eng=Depends(get_engagement_service),
):
    res = await eng.update_interest_status(interest_id, payload.get("status", ""))
    if not res:
        raise HTTPException(404, "Лид не найден или статус неверный.")
    return res


@router.get("/admin/offers")
async def admin_list_offers(
    status: Optional[str] = None,
    limit: int = 100,
    _: Dict[str, Any] = Depends(require_admin),
    eng=Depends(get_engagement_service),
):
    return {"items": await eng.list_offers(status=status, limit=limit)}


@router.patch("/admin/offers/{offer_id}/status")
async def admin_update_offer(
    offer_id: str,
    payload: Dict[str, Any],
    _: Dict[str, Any] = Depends(require_admin),
    eng=Depends(get_engagement_service),
):
    res = await eng.update_offer_status(
        offer_id,
        payload.get("status", ""),
        admin_response=payload.get("admin_response"),
    )
    if not res:
        raise HTTPException(404, "Предложение не найдено или статус неверный.")
    return res


# ---------- Deep CRM (clients + timeline) ----------

@router.get("/admin/clients")
async def admin_list_clients(
    limit: int = 200,
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    """Deep CRM client list with merged activity counts (interests, offers,
    bids, chat sessions, quiz leads) and a `last_activity` timestamp so the
    panel can be sorted by recency."""
    from services.auto_crm_timeline import AutoCrmTimelineService
    return await AutoCrmTimelineService(db).list_clients(limit=limit)


@router.get("/admin/clients/{user_id}/timeline")
async def admin_client_timeline(
    user_id: str,
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    """Return a single merged chronological timeline (all stages, all
    interactions) for one registered client."""
    from services.auto_crm_timeline import AutoCrmTimelineService
    res = await AutoCrmTimelineService(db).timeline_for_user(user_id)
    if not res.get("client"):
        raise HTTPException(404, "Клиент не найден.")
    return res


@router.get("/admin/clients/lead/{phone}/timeline")
async def admin_lead_timeline(
    phone: str,
    _: Dict[str, Any] = Depends(require_admin),
    db=Depends(get_db),
):
    """Timeline for an anonymous lead (no registered account) — keyed by
    phone number. Sales uses this to follow up before the lead converts."""
    from services.auto_crm_timeline import AutoCrmTimelineService
    return await AutoCrmTimelineService(db).timeline_by_phone(phone)


# ---------- CRM-order linkage helpers ----------

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
