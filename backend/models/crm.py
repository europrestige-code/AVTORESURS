from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr
import uuid
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"              # Заказ создан, ожидает оплаты
    PAID = "paid"                    # Оплачен клиентом
    PROCESSING = "processing"        # В обработке
    PURCHASING = "purchasing"        # Покупаем у поставщика
    PURCHASED = "purchased"          # Куплено у поставщика
    SHIPPING = "shipping"           # Отправлено
    IN_TRANSIT = "in_transit"       # В пути
    DELIVERED = "delivered"         # Доставлено
    CANCELLED = "cancelled"         # Отменён
    REFUNDED = "refunded"           # Возврат средств

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotificationType(str, Enum):
    ORDER_PAID = "order_paid"
    NEED_TO_PURCHASE = "need_to_purchase"
    SHIPPING_REQUIRED = "shipping_required"
    ORDER_DELAYED = "order_delayed"
    CUSTOMER_INQUIRY = "customer_inquiry"

# New CRM-specific enums
class CustomerStatus(str, Enum):
    """Customer lifecycle status"""
    LEAD = "lead"
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    VIP = "vip"
    BLOCKED = "blocked"
    CHURNED = "churned"

class CustomerSegment(str, Enum):
    """Customer segmentation"""
    HIGH_VALUE = "high_value"
    FREQUENT_BUYER = "frequent_buyer"
    NEW_CUSTOMER = "new_customer"
    RETURNING_CUSTOMER = "returning_customer"
    PRICE_SENSITIVE = "price_sensitive"
    PREMIUM_BUYER = "premium_buyer"
    BULK_BUYER = "bulk_buyer"

class CommunicationType(str, Enum):
    """Types of customer communication"""
    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    SUPPORT_TICKET = "support_ticket"
    SYSTEM_NOTIFICATION = "system_notification"
    MARKETING_EMAIL = "marketing_email"
    ORDER_UPDATE = "order_update"

class TicketStatus(str, Enum):
    """Support ticket statuses"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

class TicketCategory(str, Enum):
    """Support ticket categories"""
    ORDER_ISSUE = "order_issue"
    PAYMENT_PROBLEM = "payment_problem"
    DELIVERY_INQUIRY = "delivery_inquiry"
    PRODUCT_QUESTION = "product_question"
    TECHNICAL_ISSUE = "technical_issue"
    ACCOUNT_ISSUE = "account_issue"
    REFUND_REQUEST = "refund_request"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"

class CRMOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str  # Reference to main order
    
    # Customer info
    customer_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    
    # Product info
    product_name: str
    product_url: Optional[str] = None
    supplier_store: str
    
    # Financial info
    customer_paid_amount: float
    supplier_cost: Optional[float] = None
    commission: float
    profit: Optional[float] = None
    
    # Status tracking
    status: OrderStatus = OrderStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    priority: Priority = Priority.MEDIUM
    
    # Dates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    processing_started_at: Optional[datetime] = None
    purchased_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Logistics
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    
    # Internal notes
    internal_notes: List[str] = []
    customer_notes: Optional[str] = None
    
    # Assigned staff
    assigned_to: Optional[str] = None  # User ID
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OrderTimeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    status: OrderStatus
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # User ID
    is_visible_to_customer: bool = True

class NotificationRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_type: NotificationType
    trigger_condition: Dict[str, Any]  # JSON conditions
    recipients: List[str]  # User IDs or phone numbers
    message_template: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CRMNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_type: NotificationType
    order_id: str
    title: str
    message: str
    priority: Priority = Priority.MEDIUM
    recipients: List[str]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_sent: bool = False
    is_read: bool = False

class DashboardStats(BaseModel):
    total_orders: int
    orders_pending_payment: int
    orders_paid_need_purchase: int
    orders_in_shipping: int
    orders_delivered_today: int
    
    revenue_today: float
    revenue_this_month: float
    profit_this_month: float
    
    active_customers: int
    new_customers_this_month: int
    
    avg_order_value: float
    avg_processing_time: float  # hours
    customer_satisfaction: float  # percentage

class OrderFilter(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    priority: Optional[Priority] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    customer_email: Optional[str] = None
    assigned_to: Optional[str] = None
    search_query: Optional[str] = None

class BulkOrderUpdate(BaseModel):
    order_ids: List[str]
    status: Optional[OrderStatus] = None
    assigned_to: Optional[str] = None
    priority: Optional[Priority] = None
    internal_note: Optional[str] = None

# Advanced CRM Models
class CustomerProfile(BaseModel):
    """Extended customer profile with CRM data"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="Reference to user account")
    
    # Basic Information
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    
    # CRM Status
    status: CustomerStatus = CustomerStatus.LEAD
    segment: List[CustomerSegment] = Field(default_factory=list)
    
    # Contact Preferences
    email_notifications: bool = True
    sms_notifications: bool = True
    marketing_emails: bool = True
    preferred_language: str = "ru"
    
    # Business Metrics
    total_orders: int = 0
    total_spent: float = 0.0
    average_order_value: float = 0.0
    lifetime_value: float = 0.0
    last_order_date: Optional[datetime] = None
    first_order_date: Optional[datetime] = None
    
    # Engagement Metrics
    last_login: Optional[datetime] = None
    last_contact: Optional[datetime] = None
    last_email_opened: Optional[datetime] = None
    last_sms_received: Optional[datetime] = None
    
    # Geographic Data
    country: str = "RU"
    city: Optional[str] = None
    region: Optional[str] = None
    timezone: str = "Europe/Moscow"
    
    # Custom Fields
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Automation Data
    automation_scores: Dict[str, float] = Field(default_factory=dict)
    next_followup_date: Optional[datetime] = None
    assigned_manager: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Privacy and Compliance
    gdpr_consent: bool = False
    gdpr_consent_date: Optional[datetime] = None
    data_processing_consent: bool = True

class CommunicationHistory(BaseModel):
    """Record of all customer communications"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = Field(..., description="Reference to customer")
    
    # Communication Details
    type: CommunicationType
    direction: str = Field(..., description="inbound or outbound")
    subject: Optional[str] = None
    content: str
    
    # Channel Information
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    channel_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Status and Tracking
    status: str = "sent"  # sent, delivered, read, failed
    delivery_status: Optional[str] = None
    read_at: Optional[datetime] = None
    
    # Related Records
    order_id: Optional[str] = None
    ticket_id: Optional[str] = None
    campaign_id: Optional[str] = None
    
    # Staff Information
    staff_user_id: Optional[str] = None
    staff_name: Optional[str] = None
    
    # Automation
    automated: bool = False
    automation_rule_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    # Response Tracking
    response_expected: bool = False
    response_received: bool = False
    response_time_hours: Optional[float] = None

class SupportTicket(BaseModel):
    """Customer support ticket system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = Field(..., description="Human-readable ticket number")
    
    # Customer Information
    customer_id: str
    customer_email: EmailStr
    customer_name: str
    customer_phone: Optional[str] = None
    
    # Ticket Details
    subject: str
    description: str
    category: TicketCategory
    priority: Priority = Priority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    
    # Assignment
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    
    # Related Records
    order_id: Optional[str] = None
    related_tickets: List[str] = Field(default_factory=list)
    
    # Resolution
    resolution: Optional[str] = None
    resolution_time_hours: Optional[float] = None
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    
    # SLA Tracking
    sla_deadline: Optional[datetime] = None
    first_response_time: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Communication Thread
    messages: List[str] = Field(default_factory=list)  # References to CommunicationHistory
    
    # Tags and Classification
    tags: List[str] = Field(default_factory=list)
    internal_notes: str = ""
    
    # Escalation
    escalated: bool = False
    escalated_at: Optional[datetime] = None
    escalated_to: Optional[str] = None
    escalation_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Customer Feedback
    feedback_requested: bool = False
    feedback_received_at: Optional[datetime] = None
    feedback_comments: Optional[str] = None

class AutomationRule(BaseModel):
    """CRM automation rules"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    
    # Rule Configuration
    trigger_event: str  # order_placed, customer_inactive, birthday, etc.
    conditions: Dict[str, Any] = Field(default_factory=dict)
    
    # Actions
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Timing
    delay_minutes: int = 0
    active: bool = True
    
    # Limits
    max_executions_per_customer: Optional[int] = None
    execution_window_days: Optional[int] = None
    
    # Statistics
    total_executions: int = 0
    successful_executions: int = 0
    last_executed: Optional[datetime] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request/Response Models
class CreateTicketRequest(BaseModel):
    """Request to create support ticket"""
    customer_email: EmailStr
    subject: str
    description: str
    category: TicketCategory
    priority: Priority = Priority.MEDIUM
    order_id: Optional[str] = None

class UpdateTicketRequest(BaseModel):
    """Request to update support ticket"""
    status: Optional[TicketStatus] = None
    priority: Optional[Priority] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: Optional[List[str]] = None

class SendCommunicationRequest(BaseModel):
    """Request to send communication to customer"""
    customer_id: str
    type: CommunicationType
    subject: Optional[str] = None
    content: str
    scheduled_at: Optional[datetime] = None

class CustomerFilterRequest(BaseModel):
    """Request to filter customers"""
    status: Optional[List[CustomerStatus]] = None
    segments: Optional[List[CustomerSegment]] = None
    tags: Optional[List[str]] = None
    min_total_spent: Optional[float] = None
    max_total_spent: Optional[float] = None
    min_orders: Optional[int] = None
    last_order_days_ago: Optional[int] = None
    created_after: Optional[datetime] = None
    limit: int = Field(default=50, le=1000)
    offset: int = Field(default=0, ge=0)

class CRMResponse(BaseModel):
    """Standard CRM response"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class CustomerListResponse(BaseModel):
    """Response for customer list"""
    success: bool
    data: List[CustomerProfile]
    total: int
    page: int
    per_page: int
    message: str

class CRMDashboardData(BaseModel):
    """Enhanced CRM dashboard with advanced metrics"""
    # Customer Counts
    total_customers: int = 0
    new_customers_this_month: int = 0
    active_customers: int = 0
    inactive_customers: int = 0
    vip_customers: int = 0
    
    # Customer Status Distribution
    customers_by_status: Dict[str, int] = Field(default_factory=dict)
    customers_by_segment: Dict[str, int] = Field(default_factory=dict)
    
    # Support Metrics
    open_tickets: int = 0
    tickets_this_week: int = 0
    avg_resolution_time_hours: float = 0.0
    customer_satisfaction_avg: float = 0.0
    
    # Communication Metrics
    emails_sent_this_week: int = 0
    sms_sent_this_week: int = 0
    avg_response_time_hours: float = 0.0
    
    # Revenue Metrics
    total_revenue: float = 0.0
    revenue_this_month: float = 0.0
    avg_customer_value: float = 0.0
    
    # Automation Metrics
    active_automation_rules: int = 0
    automations_executed_today: int = 0
    
    # Recent Activity
    recent_customers: List[CustomerProfile] = Field(default_factory=list)
    recent_tickets: List[SupportTicket] = Field(default_factory=list)
    
    # Trends
    customer_growth_rate: float = 0.0
    churn_rate: float = 0.0
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))