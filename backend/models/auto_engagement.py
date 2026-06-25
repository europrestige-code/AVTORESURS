"""Three-stage engagement models — interest, offer, bid.

Bid already exists (`auto.AutoBid`); this file adds the two earlier stages so
we collect contact info long before the user is asked for a deposit.

Flow:
    1. Interest  → visitor / authed user expresses interest (lead-style).
                   No price commitment.
    2. Offer     → authed user proposes a *non-binding* price ("Предложение
                   цены"). Requires registration but NOT a deposit.
    3. Bid       → authed user with verified deposit submits an official
                   "Ставка". Existing `AutoBid` model — we only gate it.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, Field


class InterestStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    closed = "closed"


class OfferStatus(str, Enum):
    soft_offer = "soft_offer"
    countered = "countered"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class AutoInterest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: Optional[str] = None  # may be null when sourced from the AI quiz
    user_id: Optional[str] = None     # null when posted by an anonymous visitor
    name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    budget_nzd: Optional[float] = None
    message: Optional[str] = None
    source: str = "vehicle_page"  # vehicle_page | quiz | catalog | lead_modal
    status: InterestStatus = InterestStatus.new
    crm_contact_id: Optional[str] = None  # filled by the CRM-bridge if created
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutoInterestCreate(BaseModel):
    vehicle_id: Optional[str] = None
    name: str
    phone: str
    email: Optional[str] = None
    city: Optional[str] = None
    budget_nzd: Optional[float] = None
    message: Optional[str] = None
    source: str = "vehicle_page"


class AutoOffer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str
    user_id: str
    offer_price_nzd: float
    message: Optional[str] = None
    status: OfferStatus = OfferStatus.soft_offer
    admin_response: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AutoOfferCreate(BaseModel):
    vehicle_id: str
    offer_price_nzd: float
    message: Optional[str] = None


class EngagementCounts(BaseModel):
    """Returned for one vehicle — used by the urgency widget."""
    watchers: int = 0
    interested: int = 0
    offers: int = 0
    bids: int = 0
