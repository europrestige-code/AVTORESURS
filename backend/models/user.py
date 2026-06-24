from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr
import uuid
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    LOGISTICS = "logistics"
    MANAGER = "manager"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"

class PaymentMethodType(str, Enum):
    TBANK_QR = "tbank_qr"
    SBER_QR = "sber_qr"
    MIR_CARD = "mir_card"
    PHONE_PAYMENT = "phone_payment"
    SBP = "sbp"

class PaymentMethod(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: PaymentMethodType
    display_name: str
    is_default: bool = False
    
    # Card-specific fields
    card_mask: Optional[str] = None  # e.g., "**** **** **** 1234"
    card_holder_name: Optional[str] = None
    
    # Phone-specific fields
    phone_number: Optional[str] = None
    
    # Bank-specific fields
    bank_name: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class PaymentHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    order_id: Optional[str] = None
    payment_method_id: str
    amount: float
    currency: str = "RUB"
    status: str  # pending, completed, failed, cancelled
    payment_type: PaymentMethodType
    
    # Payment details
    transaction_id: Optional[str] = None
    payment_provider: Optional[str] = None
    provider_response: Optional[Dict] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Additional info
    description: Optional[str] = None
    metadata: Optional[Dict] = None

class CustomerInfo(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: str = "Russia"
    preferred_payment_method: Optional[str] = None
    # AvtoResurs marketing rules: opt-IN by default; opt-OUT via the
    # unsubscribe link in every email (also exposed in the customer dashboard).
    marketing_consent: bool = True

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Optional[str] = None  # For admin users
    email: EmailStr
    phone: str
    password_hash: str
    role: UserRole = UserRole.CUSTOMER
    status: UserStatus = UserStatus.ACTIVE
    
    customer_info: Optional[CustomerInfo] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Customer specific fields
    total_orders: int = 0
    total_spent: float = 0.0
    
    # Admin specific fields
    permissions: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    user_role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    is_active: bool = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    phone: str
    password: str
    first_name: str
    last_name: str
    confirm_password: str

class UserResponse(BaseModel):
    id: str
    email: str
    phone: str
    role: UserRole
    status: UserStatus
    customer_info: Optional[CustomerInfo]
    total_orders: int
    total_spent: float
    created_at: datetime
    last_login: Optional[datetime]