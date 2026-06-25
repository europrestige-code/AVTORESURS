"""Auction observation + AI estimate models.

Three orthogonal data sources feed the AI estimator:
  • `auction_observations`    — live/observed prices captured by the buyer-
    session Playwright harness OR scraped from public post-auction archives.
  • Existing `auto_vehicles.buy_now_price_nzd`, `current_price_nzd` —
    catalog-driven values from the same hourly importer.
  • Manual entries by admin (kept for emergencies — `source_type=manual`).

Output of the AI estimator lives directly on the Vehicle document
(`ai_estimate_*` fields below) so the customer-facing PriceGuidance can read
without an extra hop.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field
import uuid


ObservationSource = Literal[
    "buyer_session",      # captured via Playwright on a logged-in buyer view
    "public_archive",     # post-auction public scrape
    "manual",             # admin entered
    "official_listing",   # the source itself published a price (e.g. Buy Now)
    "ai_estimate",        # our own model
]


class AuctionObservation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: Optional[str] = None      # if matched to an auto_vehicles row
    source: str                            # "turners" | "manheim_nz" | "pickles" …
    source_type: ObservationSource
    lot_ref: Optional[str] = None          # auction lot/listing id from the source
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    body_type: Optional[str] = None
    damage_type: Optional[str] = None
    branch: Optional[str] = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auction_at: Optional[datetime] = None
    observed_price_nzd: Optional[float] = None
    buy_now_price_nzd: Optional[float] = None
    reserve_met: Optional[bool] = None
    sold: Optional[bool] = None
    notes: Optional[str] = None
    raw_payload: Optional[dict] = None     # raw HTML extract / JSON for debugging


# ============ AI estimate fields living on Vehicle (see migration note) ============

class VehicleAiEstimate(BaseModel):
    """Sub-document attached to auto_vehicles.ai_estimate"""
    estimate_low_nzd: Optional[float] = None
    estimate_high_nzd: Optional[float] = None
    recommended_max_bid_nzd: Optional[float] = None
    buy_now_reference_nzd: Optional[float] = None
    landed_rub_estimate: Optional[float] = None
    market_score: Optional[int] = None     # 0..100
    confidence: Optional[Literal[
        "excellent_buy", "good_buy", "average", "high_risk", "avoid"
    ]] = None
    confidence_pct: Optional[int] = None   # 0..100 quantitative confidence
    reasoning: Optional[list] = None       # short bullets (3-5)
    based_on_observations: Optional[int] = 0
    model: Optional[str] = None            # which LLM produced this
    generated_at: Optional[datetime] = None
