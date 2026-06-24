from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid

class CustomerInfo(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None

class ProductDetails(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class PriceCalculation(BaseModel):
    original_price_usd: float
    original_price_rub: float
    commission_rub: float
    shipping_rub: float
    customs_rub: float
    insurance_rub: float
    total_rub: float
    exchange_rate: float
    store_name: Optional[str] = None

class OrderInput(BaseModel):
    input_type: str  # "url", "manual", "photo"
    url: Optional[str] = None
    product_name: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    photo_base64: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = Field(default_factory=lambda: f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}")
    
    customer_info: CustomerInfo
    product_details: ProductDetails
    price_calculation: PriceCalculation
    order_input: OrderInput
    
    status: str = "pending"  # pending, paid, processing, shipped, delivered, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    notifications_sent: List[str] = []  # Track which notifications were sent
    ai_analysis: Optional[Dict] = None  # Store AI analysis results
    notes: Optional[str] = None  # Internal notes
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OrderResponse(BaseModel):
    success: bool
    order_id: str
    total_price: float
    payment_instructions: str
    sms_sent: bool
    email_sent: bool
    message: str

class PriceCalculationRequest(BaseModel):
    input_type: str  # "url", "manual", "photo"
    url: Optional[str] = None
    product_name: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    description: Optional[str] = None
    photo_base64: Optional[str] = None

class PriceCalculationResponse(BaseModel):
    success: bool
    product_name: str
    best_store: str
    original_price_usd: float
    exchange_rate: float
    original_price_rub: float
    commission: float
    shipping: float
    customs: float
    insurance: float
    total_price: float
    breakdown: Dict[str, str]  # Formatted prices for display
    calculation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: Optional[str] = None
    ai_confidence: Optional[float] = None