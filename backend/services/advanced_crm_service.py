"""
Advanced CRM Service
Complete customer relationship management with automation and support tickets
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
import hashlib

from models.crm import (
    CustomerProfile, CustomerStatus, CustomerSegment, CommunicationHistory,
    SupportTicket, TicketStatus, TicketCategory, CommunicationType,
    AutomationRule, CreateTicketRequest, UpdateTicketRequest,
    SendCommunicationRequest, CustomerFilterRequest, CRMResponse,
    CustomerListResponse, CRMDashboardData, Priority
)
from services.notification_service import NotificationService

try:
    from emergentintegrations import LlmChat
except ImportError:
    # Mock LlmChat if not available
    class LlmChat:
        def __init__(self, api_key: str):
            self.api_key = api_key
        
        async def chat(self, prompt: str) -> object:
            class MockResponse:
                message = f"Mock CRM response: {prompt[:50]}..."
            return MockResponse()

class AdvancedCRMService:
    """Advanced CRM service with automation, analytics, and support tickets"""
    
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        notification_service: NotificationService,
        emergent_key: str
    ):
        self.db = database
        self.notification_service = notification_service
        self.emergent_key = emergent_key
        self.logger = logging.getLogger(__name__)
        self.ai_client = LlmChat(api_key=emergent_key)
        
        # Collections
        self.customers_collection = database.crm_customers
        self.communications_collection = database.crm_communications
        self.tickets_collection = database.support_tickets
        self.automations_collection = database.crm_automations
        self.users_collection = database.users
        self.orders_collection = database.orders
        
        # Ticket counter for human-readable numbers
        self.ticket_counter = 1000
    
    async def initialize(self) -> bool:
        """Initialize CRM service"""
        try:
            await self._create_indexes()
            await self._sync_customers_from_users()
            self.logger.info("Advanced CRM service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize CRM service: {e}")
            return False
    
    async def _create_indexes(self):
        """Create database indexes for performance"""
        # Customer indexes
        await self.customers_collection.create_index("user_id", unique=True)
        await self.customers_collection.create_index("email", unique=True)
        await self.customers_collection.create_index("status")
        await self.customers_collection.create_index("segment")
        await self.customers_collection.create_index([("created_at", -1)])
        await self.customers_collection.create_index([("last_order_date", -1)])
        
        # Communication indexes
        await self.communications_collection.create_index("customer_id")
        await self.communications_collection.create_index("type")
        await self.communications_collection.create_index([("created_at", -1)])
        
        # Support ticket indexes
        await self.tickets_collection.create_index("ticket_number", unique=True)
        await self.tickets_collection.create_index("customer_id")
        await self.tickets_collection.create_index("status")
        await self.tickets_collection.create_index("priority")
        await self.tickets_collection.create_index([("created_at", -1)])
    
    async def _sync_customers_from_users(self):
        """Sync customer profiles from existing users"""
        try:
            # Get all users who don't have CRM profiles
            async for user in self.users_collection.find():
                existing_customer = await self.customers_collection.find_one({"user_id": user["id"]})
                
                if not existing_customer:
                    # Create customer profile from user
                    customer_profile = CustomerProfile(
                        user_id=user["id"],
                        email=user["email"],
                        full_name=user.get("full_name", user.get("name", "Unknown")),
                        phone=user.get("phone"),
                        status=CustomerStatus.ACTIVE if user.get("is_active", True) else CustomerStatus.INACTIVE,
                        created_at=user.get("created_at", datetime.now(timezone.utc)),
                        country=user.get("country", "RU"),
                        preferred_language=user.get("language", "ru")
                    )
                    
                    await self.customers_collection.insert_one(customer_profile.model_dump())
                    self.logger.info(f"Created CRM profile for user {user['email']}")
        
        except Exception as e:
            self.logger.error(f"Error syncing customers from users: {e}")
    
    # Customer Management
    async def get_customer_profile(self, user_id: str) -> Optional[CustomerProfile]:
        """Get customer profile by user_id"""
        try:
            customer_doc = await self.customers_collection.find_one({"user_id": user_id})
            if customer_doc:
                return CustomerProfile(**customer_doc)
            return None
        except Exception as e:
            self.logger.error(f"Error getting customer profile {user_id}: {e}")
            return None
    
    async def update_customer_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[CustomerProfile]:
        """Update customer profile"""
        try:
            # Add updated timestamp
            updates["updated_at"] = datetime.now(timezone.utc)
            
            result = await self.customers_collection.update_one(
                {"user_id": user_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return await self.get_customer_profile(user_id)
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating customer profile {user_id}: {e}")
            return None
    
    async def calculate_customer_metrics(self, customer_id: str) -> Dict[str, Any]:
        """Calculate customer business metrics"""
        try:
            # Get all orders for customer
            orders_cursor = self.orders_collection.find({"customer_id": customer_id})
            orders = await orders_cursor.to_list(length=None)
            
            if not orders:
                return {
                    "total_orders": 0,
                    "total_spent": 0.0,
                    "average_order_value": 0.0,
                    "lifetime_value": 0.0,
                    "last_order_date": None,
                    "first_order_date": None
                }
            
            # Calculate metrics
            total_orders = len(orders)
            total_spent = sum(order.get("total_amount", 0) for order in orders)
            average_order_value = total_spent / total_orders if total_orders > 0 else 0
            
            # Sort orders by date
            dated_orders = [o for o in orders if o.get("created_at")]
            dated_orders.sort(key=lambda x: x["created_at"])
            
            first_order_date = dated_orders[0]["created_at"] if dated_orders else None
            last_order_date = dated_orders[-1]["created_at"] if dated_orders else None
            
            # Simple LTV calculation (can be enhanced)
            lifetime_value = total_spent * 1.2  # Estimate future value
            
            return {
                "total_orders": total_orders,
                "total_spent": total_spent,
                "average_order_value": average_order_value,
                "lifetime_value": lifetime_value,
                "last_order_date": last_order_date,
                "first_order_date": first_order_date
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating customer metrics for {customer_id}: {e}")
            return {}
    
    async def segment_customer(self, customer_id: str) -> List[CustomerSegment]:
        """Automatically segment customer based on behavior"""
        try:
            customer = await self.get_customer_profile(customer_id)
            if not customer:
                return []
            
            segments = []
            
            # High value customer
            if customer.total_spent > 50000:  # 50k rubles
                segments.append(CustomerSegment.HIGH_VALUE)
            
            # Frequent buyer
            if customer.total_orders >= 10:
                segments.append(CustomerSegment.FREQUENT_BUYER)
            
            # New customer (less than 30 days)
            if customer.created_at and (datetime.now(timezone.utc) - customer.created_at).days <= 30:
                segments.append(CustomerSegment.NEW_CUSTOMER)
            
            # Returning customer
            elif customer.total_orders > 1:
                segments.append(CustomerSegment.RETURNING_CUSTOMER)
            
            # Premium buyer (high AOV)
            if customer.average_order_value > 10000:  # 10k rubles AOV
                segments.append(CustomerSegment.PREMIUM_BUYER)
            
            return segments
            
        except Exception as e:
            self.logger.error(f"Error segmenting customer {customer_id}: {e}")
            return []
    
    async def filter_customers(self, filter_request: CustomerFilterRequest) -> CustomerListResponse:
        """Filter customers based on criteria"""
        try:
            query = {}
            
            # Status filter
            if filter_request.status:
                query["status"] = {"$in": [s.value for s in filter_request.status]}
            
            # Segment filter
            if filter_request.segments:
                query["segment"] = {"$in": [s.value for s in filter_request.segments]}
            
            # Tags filter
            if filter_request.tags:
                query["tags"] = {"$in": filter_request.tags}
            
            # Spending filters
            if filter_request.min_total_spent is not None:
                query["total_spent"] = {"$gte": filter_request.min_total_spent}
            if filter_request.max_total_spent is not None:
                if "total_spent" not in query:
                    query["total_spent"] = {}
                query["total_spent"]["$lte"] = filter_request.max_total_spent
            
            # Order count filter
            if filter_request.min_orders is not None:
                query["total_orders"] = {"$gte": filter_request.min_orders}
            
            # Last order date filter
            if filter_request.last_order_days_ago is not None:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=filter_request.last_order_days_ago)
                query["last_order_date"] = {"$gte": cutoff_date}
            
            # Created date filter
            if filter_request.created_after:
                query["created_at"] = {"$gte": filter_request.created_after}
            
            # Get total count
            total_count = await self.customers_collection.count_documents(query)
            
            # Get customers with pagination
            cursor = self.customers_collection.find(query).skip(filter_request.offset).limit(filter_request.limit)
            customers = []
            
            async for customer_doc in cursor:
                customers.append(CustomerProfile(**customer_doc))
            
            return CustomerListResponse(
                success=True,
                data=customers,
                total=total_count,
                page=filter_request.offset // filter_request.limit + 1,
                per_page=filter_request.limit,
                message=f"Найдено {len(customers)} клиентов"
            )
            
        except Exception as e:
            self.logger.error(f"Error filtering customers: {e}")
            return CustomerListResponse(
                success=False,
                data=[],
                total=0,
                page=1,
                per_page=filter_request.limit,
                message=f"Ошибка при фильтрации клиентов: {str(e)}"
            )
    
    # Support Ticket System
    async def create_support_ticket(self, request: CreateTicketRequest) -> CRMResponse:
        """Create new support ticket"""
        try:
            # Find customer by email
            customer = await self.customers_collection.find_one({"email": request.customer_email})
            
            if not customer:
                # Create customer profile if doesn't exist
                customer_profile = CustomerProfile(
                    user_id=str(uuid.uuid4()),
                    email=request.customer_email,
                    full_name="Unknown Customer",
                    status=CustomerStatus.LEAD
                )
                await self.customers_collection.insert_one(customer_profile.model_dump())
                customer = customer_profile.model_dump()
            
            # Generate ticket number
            self.ticket_counter += 1
            ticket_number = f"TK-{self.ticket_counter:06d}"
            
            # Create ticket
            ticket = SupportTicket(
                ticket_number=ticket_number,
                customer_id=customer["id"],
                customer_email=request.customer_email,
                customer_name=customer.get("full_name", "Unknown Customer"),
                customer_phone=customer.get("phone"),
                subject=request.subject,
                description=request.description,
                category=request.category,
                priority=request.priority,
                order_id=request.order_id,
                sla_deadline=datetime.now(timezone.utc) + timedelta(hours=24)  # 24h SLA
            )
            
            # Save ticket
            await self.tickets_collection.insert_one(ticket.model_dump())
            
            # Log communication
            await self.log_communication(
                customer_id=customer["id"],
                comm_type=CommunicationType.SUPPORT_TICKET,
                direction="inbound",
                subject=request.subject,
                content=request.description,
                ticket_id=ticket.id
            )
            
            # Send notification to customer
            await self.notification_service.send_sms(
                customer.get("phone", ""),
                f"Заявка {ticket_number} создана. Мы ответим в течение 24 часов."
            )
            
            self.logger.info(f"Created support ticket {ticket_number} for {request.customer_email}")
            
            return CRMResponse(
                success=True,
                message=f"Заявка {ticket_number} успешно создана",
                data=ticket.model_dump()
            )
            
        except Exception as e:
            self.logger.error(f"Error creating support ticket: {e}")
            return CRMResponse(
                success=False,
                message="Ошибка при создании заявки",
                error=str(e)
            )
    
    async def update_support_ticket(self, ticket_id: str, request: UpdateTicketRequest) -> CRMResponse:
        """Update support ticket"""
        try:
            updates = {}
            
            if request.status:
                updates["status"] = request.status.value
                if request.status == TicketStatus.RESOLVED:
                    updates["resolved_at"] = datetime.now(timezone.utc)
                elif request.status == TicketStatus.CLOSED:
                    updates["closed_at"] = datetime.now(timezone.utc)
            
            if request.priority:
                updates["priority"] = request.priority.value
            
            if request.assigned_to:
                updates["assigned_to"] = request.assigned_to
            
            if request.resolution:
                updates["resolution"] = request.resolution
            
            if request.internal_notes:
                updates["internal_notes"] = request.internal_notes
            
            if request.tags:
                updates["tags"] = request.tags
            
            updates["updated_at"] = datetime.now(timezone.utc)
            
            result = await self.tickets_collection.update_one(
                {"id": ticket_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                # Get updated ticket
                ticket_doc = await self.tickets_collection.find_one({"id": ticket_id})
                if ticket_doc:
                    ticket = SupportTicket(**ticket_doc)
                    
                    # Send status update to customer if status changed
                    if request.status and request.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                        customer = await self.customers_collection.find_one({"id": ticket.customer_id})
                        if customer and customer.get("phone"):
                            status_text = "решена" if request.status == TicketStatus.RESOLVED else "закрыта"
                            await self.notification_service.send_sms(
                                customer["phone"],
                                f"Ваша заявка {ticket.ticket_number} {status_text}."
                            )
                    
                    return CRMResponse(
                        success=True,
                        message="Заявка успешно обновлена",
                        data=ticket.model_dump()
                    )
            
            return CRMResponse(
                success=False,
                message="Заявка не найдена"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating support ticket {ticket_id}: {e}")
            return CRMResponse(
                success=False,
                message="Ошибка при обновлении заявки",
                error=str(e)
            )
    
    async def get_support_tickets(
        self, 
        customer_id: Optional[str] = None,
        status: Optional[TicketStatus] = None,
        limit: int = 50
    ) -> List[SupportTicket]:
        """Get support tickets with optional filters"""
        try:
            query = {}
            
            if customer_id:
                query["customer_id"] = customer_id
            
            if status:
                query["status"] = status.value
            
            cursor = self.tickets_collection.find(query).sort("created_at", -1).limit(limit)
            tickets = []
            
            async for ticket_doc in cursor:
                tickets.append(SupportTicket(**ticket_doc))
            
            return tickets
            
        except Exception as e:
            self.logger.error(f"Error getting support tickets: {e}")
            return []
    
    # Communication System
    async def log_communication(
        self,
        customer_id: str,
        comm_type: CommunicationType,
        direction: str,
        subject: Optional[str] = None,
        content: str = "",
        **kwargs
    ) -> str:
        """Log customer communication"""
        try:
            communication = CommunicationHistory(
                customer_id=customer_id,
                type=comm_type,
                direction=direction,
                subject=subject,
                content=content,
                **kwargs
            )
            
            await self.communications_collection.insert_one(communication.model_dump())
            return communication.id
            
        except Exception as e:
            self.logger.error(f"Error logging communication: {e}")
            return ""
    
    async def send_communication(self, request: SendCommunicationRequest) -> CRMResponse:
        """Send communication to customer"""
        try:
            customer = await self.get_customer_profile(request.customer_id)
            if not customer:
                return CRMResponse(
                    success=False,
                    message="Клиент не найден"
                )
            
            # Send based on communication type
            if request.type == CommunicationType.EMAIL:
                # Would integrate with email service
                success = True  # Mock success
                
            elif request.type == CommunicationType.SMS:
                success = await self.notification_service.send_sms(
                    customer.phone or "",
                    request.content
                )
            else:
                success = True
            
            if success:
                # Log communication
                await self.log_communication(
                    customer_id=request.customer_id,
                    comm_type=request.type,
                    direction="outbound",
                    subject=request.subject,
                    content=request.content,
                    scheduled_at=request.scheduled_at
                )
                
                return CRMResponse(
                    success=True,
                    message="Сообщение отправлено"
                )
            else:
                return CRMResponse(
                    success=False,
                    message="Ошибка при отправке сообщения"
                )
                
        except Exception as e:
            self.logger.error(f"Error sending communication: {e}")
            return CRMResponse(
                success=False,
                message="Ошибка при отправке сообщения",
                error=str(e)
            )
    
    async def get_customer_communications(self, customer_id: str, limit: int = 50) -> List[CommunicationHistory]:
        """Get customer communication history"""
        try:
            cursor = self.communications_collection.find({"customer_id": customer_id}).sort("created_at", -1).limit(limit)
            communications = []
            
            async for comm_doc in cursor:
                communications.append(CommunicationHistory(**comm_doc))
            
            return communications
            
        except Exception as e:
            self.logger.error(f"Error getting customer communications: {e}")
            return []
    
    # Automation System
    async def create_automation_rule(self, rule: AutomationRule) -> CRMResponse:
        """Create automation rule"""
        try:
            await self.automations_collection.insert_one(rule.model_dump())
            
            return CRMResponse(
                success=True,
                message="Правило автоматизации создано",
                data=rule.model_dump()
            )
            
        except Exception as e:
            self.logger.error(f"Error creating automation rule: {e}")
            return CRMResponse(
                success=False,
                message="Ошибка при создании правила автоматизации",
                error=str(e)
            )
    
    async def execute_automation_rules(self, trigger_event: str, customer_id: str, **context):
        """Execute automation rules for specific trigger"""
        try:
            # Find matching automation rules
            rules_cursor = self.automations_collection.find({
                "trigger_event": trigger_event,
                "active": True
            })
            
            async for rule_doc in rules_cursor:
                rule = AutomationRule(**rule_doc)
                
                # Check conditions (simplified)
                if await self._check_automation_conditions(rule, customer_id, context):
                    await self._execute_automation_actions(rule, customer_id, context)
                    
                    # Update execution stats
                    await self.automations_collection.update_one(
                        {"id": rule.id},
                        {
                            "$inc": {"total_executions": 1, "successful_executions": 1},
                            "$set": {"last_executed": datetime.now(timezone.utc)}
                        }
                    )
                    
        except Exception as e:
            self.logger.error(f"Error executing automation rules: {e}")
    
    async def _check_automation_conditions(
        self, 
        rule: AutomationRule, 
        customer_id: str, 
        context: Dict[str, Any]
    ) -> bool:
        """Check if automation rule conditions are met"""
        # Simplified condition checking
        # In production, this would be more sophisticated
        return True
    
    async def _execute_automation_actions(
        self, 
        rule: AutomationRule, 
        customer_id: str, 
        context: Dict[str, Any]
    ):
        """Execute automation rule actions"""
        try:
            for action in rule.actions:
                action_type = action.get("type")
                
                if action_type == "send_email":
                    await self.send_communication(SendCommunicationRequest(
                        customer_id=customer_id,
                        type=CommunicationType.EMAIL,
                        subject=action.get("subject", ""),
                        content=action.get("content", "")
                    ))
                
                elif action_type == "send_sms":
                    await self.send_communication(SendCommunicationRequest(
                        customer_id=customer_id,
                        type=CommunicationType.SMS,
                        content=action.get("content", "")
                    ))
                
                elif action_type == "update_segment":
                    segment = action.get("segment")
                    if segment:
                        await self.update_customer_profile(
                            customer_id,
                            {"$addToSet": {"segment": segment}}
                        )
                        
        except Exception as e:
            self.logger.error(f"Error executing automation actions: {e}")
    
    # Analytics and Dashboard
    async def get_crm_dashboard(self) -> CRMDashboardData:
        """Get CRM dashboard data"""
        try:
            dashboard = CRMDashboardData()
            
            # Customer counts
            dashboard.total_customers = await self.customers_collection.count_documents({})
            
            # New customers this month
            month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            dashboard.new_customers_this_month = await self.customers_collection.count_documents({
                "created_at": {"$gte": month_start}
            })
            
            # Active customers
            dashboard.active_customers = await self.customers_collection.count_documents({
                "status": CustomerStatus.ACTIVE.value
            })
            
            # VIP customers
            dashboard.vip_customers = await self.customers_collection.count_documents({
                "status": CustomerStatus.VIP.value
            })
            
            # Customer status distribution
            status_pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            async for doc in self.customers_collection.aggregate(status_pipeline):
                dashboard.customers_by_status[doc["_id"]] = doc["count"]
            
            # Support ticket metrics
            dashboard.open_tickets = await self.tickets_collection.count_documents({
                "status": {"$in": [TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value]}
            })
            
            week_start = datetime.now(timezone.utc) - timedelta(days=7)
            dashboard.tickets_this_week = await self.tickets_collection.count_documents({
                "created_at": {"$gte": week_start}
            })
            
            # Communication metrics
            dashboard.emails_sent_this_week = await self.communications_collection.count_documents({
                "type": CommunicationType.EMAIL.value,
                "direction": "outbound",
                "created_at": {"$gte": week_start}
            })
            
            dashboard.sms_sent_this_week = await self.communications_collection.count_documents({
                "type": CommunicationType.SMS.value,
                "direction": "outbound",
                "created_at": {"$gte": week_start}
            })
            
            # Revenue metrics (simplified)
            total_spent_pipeline = [
                {"$group": {"_id": None, "total": {"$sum": "$total_spent"}}}
            ]
            async for doc in self.customers_collection.aggregate(total_spent_pipeline):
                dashboard.total_revenue = doc.get("total", 0)
            
            # Average customer value
            if dashboard.total_customers > 0:
                dashboard.avg_customer_value = dashboard.total_revenue / dashboard.total_customers
            
            # Recent customers (last 10)
            recent_customers_cursor = self.customers_collection.find().sort("created_at", -1).limit(10)
            async for customer_doc in recent_customers_cursor:
                dashboard.recent_customers.append(CustomerProfile(**customer_doc))
            
            # Recent tickets (last 10)
            recent_tickets_cursor = self.tickets_collection.find().sort("created_at", -1).limit(10)
            async for ticket_doc in recent_tickets_cursor:
                dashboard.recent_tickets.append(SupportTicket(**ticket_doc))
            
            # Automation metrics
            dashboard.active_automation_rules = await self.automations_collection.count_documents({"active": True})
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error getting CRM dashboard: {e}")
            return CRMDashboardData()