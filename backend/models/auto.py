"""
BuyAnywhere Auto - data models.

Pydantic models consistent with existing backend style.
All IDs are UUID strings. Timestamps are UTC ISO datetimes.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid

from pydantic import BaseModel, Field


# ---------- Enums ----------

class AutoCountry(str, Enum):
    NZ = "NZ"
    AU = "AU"


class AutoListingType(str, Enum):
    AUCTION = "auction"
    FIXED_PRICE = "fixed_price"
    INQUIRY_ONLY = "inquiry_only"


class AutoVehicleStatus(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    EXPIRED = "expired"
    WON = "won"
    HIDDEN = "hidden"
    IMPORT_ERROR = "import_error"


class AutoSyncStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


class AutoInventoryStatus(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class AutoBidStatus(str, Enum):
    ACTIVE = "active"
    OUTBID = "outbid"
    CANCELLED = "cancelled"
    WON = "won"
    LOST = "lost"


class AutoDepositStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class AutoDepositMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CRYPTO = "crypto"
    RUB_TRANSFER = "rub_transfer"
    STRIPE = "stripe"
    MANUAL = "manual"


class AutoInquiryStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    CLOSED = "closed"


class AutoInvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    CANCELLED = "cancelled"


class AutoLogisticsStatus(str, Enum):
    WON = "won"
    INVOICE_ISSUED = "invoice_issued"
    PAID = "paid"
    COLLECTED = "collected"
    STORED = "stored"
    CONTAINER_ASSIGNED = "container_assigned"
    LOADED = "loaded"
    SHIPPED = "shipped"
    ARRIVED = "arrived"
    DELIVERED = "delivered"


class AutoImageRights(str, Enum):
    SOURCE_PREVIEW = "source_preview"
    ADMIN_UPLOADED = "admin_uploaded"
    LICENSED = "licensed"
    UNKNOWN = "unknown"


# ---------- Documents ----------

def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.utcnow()


class AutoVehicle(BaseModel):
    id: str = Field(default_factory=_uuid)
    source: str = "manual"
    source_url: Optional[str] = None
    source_reference: Optional[str] = None
    country: AutoCountry = AutoCountry.NZ
    listing_type: AutoListingType = AutoListingType.AUCTION

    title_original: Optional[str] = None
    title_ru: str = ""
    description_original: Optional[str] = None
    description_ru: Optional[str] = None

    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    engine: Optional[str] = None
    fuel: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    damage_type: Optional[str] = None

    auction_end_time: Optional[datetime] = None
    current_price_nzd: Optional[float] = None
    buy_now_price_nzd: Optional[float] = None
    estimated_total_nzd: Optional[float] = None

    status: AutoVehicleStatus = AutoVehicleStatus.AVAILABLE
    images: List[str] = Field(default_factory=list)
    image_rights_status: AutoImageRights = AutoImageRights.SOURCE_PREVIEW
    source_images: List[str] = Field(default_factory=list)
    local_images: List[str] = Field(default_factory=list)

    vin: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    sync_status: AutoSyncStatus = AutoSyncStatus.SUCCESS
    inventory_status: AutoInventoryStatus = AutoInventoryStatus.AVAILABLE
    sync_error: Optional[str] = None

    ai_summary_ru: Optional[str] = None
    ai_risk_summary_ru: Optional[str] = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AutoVehicleCreate(BaseModel):
    source: str = "manual"
    source_url: Optional[str] = None
    source_reference: Optional[str] = None
    country: AutoCountry = AutoCountry.NZ
    listing_type: AutoListingType = AutoListingType.AUCTION
    title_original: Optional[str] = None
    title_ru: str
    description_original: Optional[str] = None
    description_ru: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    engine: Optional[str] = None
    fuel: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    damage_type: Optional[str] = None
    auction_end_time: Optional[datetime] = None
    current_price_nzd: Optional[float] = None
    buy_now_price_nzd: Optional[float] = None
    status: AutoVehicleStatus = AutoVehicleStatus.AVAILABLE
    images: List[str] = Field(default_factory=list)
    image_rights_status: AutoImageRights = AutoImageRights.SOURCE_PREVIEW


class AutoVehicleUpdate(BaseModel):
    source: Optional[str] = None
    source_url: Optional[str] = None
    source_reference: Optional[str] = None
    country: Optional[AutoCountry] = None
    listing_type: Optional[AutoListingType] = None
    title_original: Optional[str] = None
    title_ru: Optional[str] = None
    description_original: Optional[str] = None
    description_ru: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage_km: Optional[int] = None
    engine: Optional[str] = None
    fuel: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    damage_type: Optional[str] = None
    auction_end_time: Optional[datetime] = None
    current_price_nzd: Optional[float] = None
    buy_now_price_nzd: Optional[float] = None
    status: Optional[AutoVehicleStatus] = None
    images: Optional[List[str]] = None
    image_rights_status: Optional[AutoImageRights] = None
    ai_summary_ru: Optional[str] = None
    ai_risk_summary_ru: Optional[str] = None


class AutoBid(BaseModel):
    id: str = Field(default_factory=_uuid)
    vehicle_id: str
    user_id: str
    max_bid_nzd: float
    status: AutoBidStatus = AutoBidStatus.ACTIVE
    created_at: datetime = Field(default_factory=_utcnow)


class AutoBidCreate(BaseModel):
    max_bid_nzd: float


class AutoDeposit(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    amount: float
    currency: str = "NZD"
    method: AutoDepositMethod = AutoDepositMethod.BANK_TRANSFER
    payment_proof_file: Optional[str] = None
    payment_proof_note: Optional[str] = None
    stripe_session_id: Optional[str] = None
    status: AutoDepositStatus = AutoDepositStatus.PENDING
    admin_note: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AutoDepositCreate(BaseModel):
    amount: float = 1000.0
    currency: str = "NZD"
    method: AutoDepositMethod = AutoDepositMethod.BANK_TRANSFER
    payment_proof_file: Optional[str] = None
    payment_proof_note: Optional[str] = None


class AutoInquiry(BaseModel):
    id: str = Field(default_factory=_uuid)
    vehicle_id: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    message: str
    status: AutoInquiryStatus = AutoInquiryStatus.NEW
    created_at: datetime = Field(default_factory=_utcnow)


class AutoInquiryCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram: Optional[str] = None
    message: str


class AutoInvoice(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    vehicle_id: str
    vehicle_price_nzd: float
    commission_nzd: float = 0.0
    local_transport_nzd: float = 500.0
    forklift_nzd: float = 0.0
    storage_days: int = 0
    storage_nzd: float = 0.0
    documentation_nzd: float = 250.0
    container_share_nzd: float = 3333.0
    fx_rate_rub_nzd: Optional[float] = None
    total_nzd: float
    total_rub: Optional[float] = None
    status: AutoInvoiceStatus = AutoInvoiceStatus.DRAFT
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AutoInvoiceCreate(BaseModel):
    user_id: str
    vehicle_id: str
    vehicle_price_nzd: float
    storage_days: int = 0
    forklift_nzd: float = 0.0
    local_transport_nzd: float = 500.0
    documentation_nzd: float = 250.0
    container_share_nzd: float = 3333.0
    fx_rate_rub_nzd: Optional[float] = None
    status: AutoInvoiceStatus = AutoInvoiceStatus.DRAFT


class AutoLogisticsEvent(BaseModel):
    id: str = Field(default_factory=_uuid)
    vehicle_id: str
    user_id: str
    status: AutoLogisticsStatus
    note_ru: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)


class AutoLogisticsEventCreate(BaseModel):
    user_id: str
    status: AutoLogisticsStatus
    note_ru: Optional[str] = None


class AutoWatchlistItem(BaseModel):
    id: str = Field(default_factory=_uuid)
    vehicle_id: str
    user_id: str
    created_at: datetime = Field(default_factory=_utcnow)


# Highest-bid response

class HighestBidResponse(BaseModel):
    vehicle_id: str
    highest_bid_nzd: float = 0.0
    bid_count: int = 0


# Deposit-with-payment requests

class StripeDepositRequest(BaseModel):
    origin_url: str
