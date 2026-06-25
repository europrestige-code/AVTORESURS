"""Customer-facing engagement endpoints — interests, offers, market signals."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from models.auto_engagement import AutoInterestCreate, AutoOfferCreate

from ._deps import get_engagement_service, get_optional_user, require_user

router = APIRouter()


@router.post("/interests")
async def create_interest(
    payload: AutoInterestCreate,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    eng=Depends(get_engagement_service),
):
    """Anyone (visitor or authed) can express interest. Used by the lead
    modal and the «Выразить интерес» CTA on the vehicle page."""
    if not payload.name or not payload.phone:
        raise HTTPException(400, "Укажите имя и телефон.")
    return await eng.create_interest(payload, user_id=user.get("id") if user else None)


@router.post("/offers")
async def create_offer(
    payload: AutoOfferCreate,
    user: Dict[str, Any] = Depends(require_user),
    eng=Depends(get_engagement_service),
):
    """Authed user posts a non-binding *Предложение цены*. Does NOT require
    a deposit. Stored separately from `auto_bids` to keep the legal/UX
    distinction (offer = soft, bid = binding instruction)."""
    if not payload.offer_price_nzd or payload.offer_price_nzd <= 0:
        raise HTTPException(400, "Сумма предложения должна быть положительной.")
    return await eng.create_offer(payload, user_id=user["id"])


@router.get("/my/offers")
async def list_my_offers(
    user: Dict[str, Any] = Depends(require_user),
    eng=Depends(get_engagement_service),
):
    return {"items": await eng.my_offers(user["id"])}


@router.get("/vehicles/{vehicle_id}/engagement")
async def vehicle_engagement(vehicle_id: str, eng=Depends(get_engagement_service)):
    counts = await eng.engagement_counts(vehicle_id)
    return counts.dict()


@router.get("/market-summary")
async def market_summary(eng=Depends(get_engagement_service)):
    """Live numbers for the homepage strip — total available, ending soon,
    damaged, buy-now, leads in the last 24h."""
    return await eng.market_summary()


@router.get("/ending-soon")
async def vehicles_ending_soon(
    limit: int = 8,
    eng=Depends(get_engagement_service),
):
    from services.auto_fx_service import get_fx_rate
    items = await eng.ending_soon(limit=limit)
    fx = await get_fx_rate()
    return {"items": items, "fx_rate": fx}
