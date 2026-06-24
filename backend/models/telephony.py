"""
Telephony models for AI IP Telephony system
Supporting Russian language VoIP integration with provider abstraction
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import uuid

class ProviderType(str, Enum):
    """Supported VoIP provider types"""
    ZADARMA = "zadarma"
    TWILIO = "twilio"
    PLIVO = "plivo"
    VONAGE = "vonage"
    BANDWIDTH = "bandwidth"

class CallStatus(str, Enum):
    """Standardized call status across providers"""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"
    QUEUED = "queued"
    ROUTING = "routing"

class CallDirection(str, Enum):
    """Call direction enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"

class NumberType(str, Enum):
    """Standardized number types"""
    LOCAL = "local"
    MOBILE = "mobile"
    TOLL_FREE = "toll_free"
    INTERNATIONAL = "international"

class RussianCity(str, Enum):
    """Russian cities supported for telephony"""
    MOSCOW = "moscow"
    KRASNOYARSK = "krasnoyarsk"
    VLADIVOSTOK = "vladivostok"

# Provider Configuration Models
class ProviderConfig(BaseModel):
    """Base provider configuration"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_type: ProviderType
    name: str
    api_credentials: Dict[str, str]
    webhook_url: Optional[str] = None
    enabled: bool = True
    priority: int = Field(default=1, description="Lower number = higher priority")
    rate_limits: Dict[str, int] = Field(default_factory=dict)
    supported_countries: List[str] = Field(default_factory=lambda: ["RU"])
    features: Dict[str, bool] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ZadarmaConfig(BaseModel):
    """Zadarma-specific configuration"""
    model_config = ConfigDict(extra="allow")
    
    api_key: str
    api_secret: str
    sip_login: Optional[str] = None
    webhook_secret: Optional[str] = None
    test_mode: bool = True

# Virtual Number Models
class VirtualNumber(BaseModel):
    """Virtual phone number representation"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    number: str = Field(..., description="Phone number in international format")
    provider_type: ProviderType
    provider_number_id: Optional[str] = None
    country_code: str = "7"  # Russia
    area_code: str
    city: RussianCity
    number_type: NumberType = NumberType.LOCAL
    monthly_cost: float = 0.0
    currency: str = "USD"
    capabilities: List[str] = Field(default_factory=list)
    status: str = "active"
    sip_login: Optional[str] = None
    caller_name: Optional[str] = None
    forwarding_rules: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Call Models
class CallInfo(BaseModel):
    """Call information representation"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    call_id: str = Field(..., description="Internal call ID")
    provider_call_id: Optional[str] = None
    provider_type: ProviderType
    direction: CallDirection
    from_number: str
    to_number: str
    status: CallStatus = CallStatus.INITIATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    cost: Optional[float] = None
    currency: Optional[str] = "USD"
    recording_url: Optional[str] = None
    error_message: Optional[str] = None
    caller_id: Optional[str] = None
    assigned_agent: Optional[str] = None
    queue_time_seconds: Optional[int] = None
    customer_data: Dict[str, Any] = Field(default_factory=dict)
    ai_analysis: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Agent Models
class Agent(BaseModel):
    """Call center agent representation"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str
    email: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=lambda: ["ru"])
    capacity: int = 1
    current_calls: int = 0
    status: str = "available"  # available, busy, away, offline
    last_call_ended: Optional[datetime] = None
    total_calls_today: int = 0
    total_calls_month: int = 0
    average_call_duration_seconds: int = 300  # 5 minutes default
    city_preferences: List[RussianCity] = Field(default_factory=list)
    business_hours: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Call Routing Models
class RoutingRule(BaseModel):
    """Call routing rule configuration"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = Field(..., description="Unique rule identifier")
    name: str
    description: Optional[str] = None
    priority: int = Field(..., description="Lower number = higher priority")
    conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    valid_from_hour: Optional[int] = None
    valid_to_hour: Optional[int] = None
    valid_days: List[int] = Field(default_factory=lambda: list(range(7)))  # 0=Monday
    timezone: str = "Europe/Moscow"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# AI Models
class AICallAnalysis(BaseModel):
    """AI analysis of call content"""
    model_config = ConfigDict(extra="allow")
    
    call_id: str
    intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    language: str = "ru"
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: List[str] = Field(default_factory=list)
    resolution_status: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Webhook Models
class WebhookEvent(BaseModel):
    """Webhook event from telephony provider"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_id: str
    provider_type: ProviderType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    call_id: Optional[str] = None
    pbx_call_id: Optional[str] = None
    caller_id: Optional[str] = None
    destination: Optional[str] = None
    duration: Optional[int] = None
    status: Optional[str] = None
    recording_url: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    processed: bool = False
    processed_at: Optional[datetime] = None

# Request/Response Models
class CreateProviderConfigRequest(BaseModel):
    """Request to create provider configuration"""
    provider_type: ProviderType
    name: str
    api_credentials: Dict[str, str]
    webhook_url: Optional[str] = None
    enabled: bool = True
    priority: int = 1
    features: Dict[str, bool] = Field(default_factory=dict)

class ProviderConfigResponse(BaseModel):
    """Response for provider configuration"""
    success: bool
    data: Optional[ProviderConfig] = None
    message: str
    error: Optional[str] = None

class PurchaseNumberRequest(BaseModel):
    """Request to purchase virtual number"""
    number: str
    city: RussianCity
    caller_name: Optional[str] = None
    provider_type: Optional[ProviderType] = None

class NumberSearchRequest(BaseModel):
    """Request to search available numbers"""
    city: RussianCity
    number_type: NumberType = NumberType.LOCAL
    limit: int = Field(default=10, le=50)

class MakeCallRequest(BaseModel):
    """Request to make outbound call"""
    from_number: str
    to_number: str
    caller_id: Optional[str] = None
    provider_type: Optional[ProviderType] = None
    ai_enabled: bool = True
    callback_url: Optional[str] = None

class CallResponse(BaseModel):
    """Response for call operations"""
    success: bool
    data: Optional[CallInfo] = None
    message: str
    error: Optional[str] = None

# Statistics Models
class CallStatistics(BaseModel):
    """Call statistics summary"""
    total_calls: int = 0
    answered_calls: int = 0
    missed_calls: int = 0
    average_duration_seconds: float = 0.0
    total_duration_seconds: int = 0
    answer_rate: float = 0.0
    cost_total: float = 0.0
    currency: str = "USD"
    period_start: datetime
    period_end: datetime

class TelephonyDashboard(BaseModel):
    """Telephony dashboard data"""
    active_calls: int = 0
    queue_size: int = 0
    available_agents: int = 0
    busy_agents: int = 0
    virtual_numbers: int = 0
    active_providers: int = 0
    today_stats: CallStatistics
    week_stats: CallStatistics
    month_stats: CallStatistics
    recent_calls: List[CallInfo] = Field(default_factory=list)

# Russian Language Models
class RussianGreeting(BaseModel):
    """Russian greeting configuration"""
    city: RussianCity
    time_based: bool = True
    business_greeting: str
    after_hours_greeting: str
    weekend_greeting: str
    holiday_greeting: str

class RussianPrompts(BaseModel):
    """Russian language prompts for AI"""
    order_status_check: str = "Проверить статус заказа"
    speak_to_operator: str = "Поговорить с оператором"
    general_inquiry: str = "Общий вопрос"
    complaint: str = "Жалоба"
    compliment: str = "Благодарность"
    callback_request: str = "Заказать обратный звонок"

# Error Models
class TelephonyError(BaseModel):
    """Telephony system error"""
    error_code: str
    error_message: str
    error_message_ru: str
    provider_error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    call_id: Optional[str] = None
    provider_type: Optional[ProviderType] = None