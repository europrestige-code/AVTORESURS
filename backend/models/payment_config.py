from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class PaymentProvider(str, Enum):
    UNITPAY = "unitpay"
    TBANK_QR = "tbank_qr"
    SBER_QR = "sber_qr"
    PHONE_PAYMENT = "phone_payment"

class PaymentProviderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"

class UnitPayConfig(BaseModel):
    """UnitPay payment configuration"""
    secret_key: str = Field(..., description="UnitPay Secret Key")
    public_key: str = Field(..., description="UnitPay Public Key")
    project_id: int = Field(..., description="UnitPay Project ID")
    domain: str = Field(default="unitpay.ru", description="UnitPay Domain")
    test_mode: bool = Field(default=True, description="Enable test mode")
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Secret key must be at least 10 characters')
        return v
    
    @validator('project_id')
    def validate_project_id(cls, v):
        if v <= 0:
            raise ValueError('Project ID must be positive')
        return v

class TBankQRConfig(BaseModel):
    """T-Bank QR payment configuration"""
    terminal_id: str = Field(..., description="T-Bank Terminal ID")
    terminal_password: str = Field(..., description="T-Bank Terminal Password")
    api_url: str = Field(default="https://securepay.tinkoff.ru/v2/", description="T-Bank API URL")
    test_mode: bool = Field(default=True, description="Enable test mode")
    
    @validator('terminal_id')
    def validate_terminal_id(cls, v):
        if not v or len(v) < 5:
            raise ValueError('Terminal ID must be at least 5 characters')
        return v
    
    @validator('terminal_password')
    def validate_terminal_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Terminal password must be at least 8 characters')
        return v

class SberQRConfig(BaseModel):
    """Sberbank QR payment configuration"""
    merchant_id: str = Field(..., description="Sberbank Merchant ID")
    api_key: str = Field(..., description="Sberbank API Key")
    secret_key: str = Field(..., description="Sberbank Secret Key")
    api_url: str = Field(default="https://api.sberbank.ru/ru/prod/", description="Sberbank API URL")
    test_mode: bool = Field(default=True, description="Enable test mode")
    
    @validator('merchant_id')
    def validate_merchant_id(cls, v):
        if not v or len(v) < 5:
            raise ValueError('Merchant ID must be at least 5 characters')
        return v

class PhonePaymentConfig(BaseModel):
    """Phone payment configuration"""
    provider_name: str = Field(default="MegaFon", description="Phone payment provider")
    api_key: str = Field(..., description="Phone payment API key")
    secret_key: str = Field(..., description="Phone payment secret key")
    api_url: str = Field(default="https://api.megafon.ru/payment/", description="Phone payment API URL")
    test_mode: bool = Field(default=True, description="Enable test mode")
    commission_rate: float = Field(default=0.03, description="Commission rate (3%)")
    
    @validator('commission_rate')
    def validate_commission_rate(cls, v):
        if v < 0 or v > 0.5:
            raise ValueError('Commission rate must be between 0 and 50%')
        return v

class PaymentProviderConfig(BaseModel):
    """Payment provider configuration model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: PaymentProvider
    name: str = Field(..., description="Display name for the payment method")
    status: PaymentProviderStatus = PaymentProviderStatus.INACTIVE
    configuration: Dict[str, Any] = Field(..., description="Provider-specific configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="Admin user who created this configuration")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Name must be at least 3 characters')
        return v

class PaymentConfigRequest(BaseModel):
    """Request model for creating/updating payment configuration"""
    provider: PaymentProvider
    name: str
    status: PaymentProviderStatus = PaymentProviderStatus.INACTIVE
    configuration: Dict[str, Any]

class PaymentConfigResponse(BaseModel):
    """Response model for payment configuration"""
    id: str
    provider: PaymentProvider
    name: str
    status: PaymentProviderStatus
    test_mode: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    # Don't include sensitive configuration data in response

class PaymentTestRequest(BaseModel):
    """Request model for testing payment configuration"""
    provider: PaymentProvider
    amount: float = Field(default=100.0, description="Test amount in rubles")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0 or v > 10000:
            raise ValueError('Test amount must be between 0 and 10000 rubles')
        return v

class PaymentTestResponse(BaseModel):
    """Response model for payment configuration test"""
    success: bool
    provider: PaymentProvider
    test_amount: float
    response_time_ms: float
    message: str
    error_details: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None