import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from models.crm import (
    CRMOrder, OrderStatus, PaymentStatus, Priority, 
    NotificationType, CRMNotification, DashboardStats,
    OrderFilter, OrderTimeline, NotificationRule
)
from models.user import UserRole
from services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

class CRMService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
        # Default notification rules
        self.default_notification_rules = [
            {
                "type": NotificationType.ORDER_PAID,
                "recipients": ["+79135533369"],  # Admin phone
                "message": "🔔 Новый оплаченный заказ #{order_id} на сумму {amount} ₽. Требуется закупка товара."
            },
            {
                "type": NotificationType.NEED_TO_PURCHASE,
                "recipients": ["+79135533369"],
                "message": "⏰ Напоминание: Заказ #{order_id} оплачен клиентом. Необходимо произвести закупку у поставщика."
            },
            {
                "type": NotificationType.SHIPPING_REQUIRED,
                "recipients": ["+79135533369"],
                "message": "📦 Заказ #{order_id} куплен у поставщика. Необходимо организовать отправку клиенту."
            }
        ]
    
    async def create_crm_order(self, order_data: Dict) -> CRMOrder:
        """Create CRM order from regular order"""
        crm_order = CRMOrder(
            order_id=order_data['order_id'],
            customer_id=order_data.get('customer_id', ''),
            customer_name=order_data.get('customer_name', ''),
            customer_email=order_data.get('customer_email', ''),
            customer_phone=order_data.get('customer_phone', ''),
            product_name=order_data.get('product_name', ''),
            product_url=order_data.get('product_url'),
            supplier_store=order_data.get('store_name', ''),
            customer_paid_amount=order_data.get('total_price', 0),
            commission=order_data.get('commission', 0),
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING
        )
        
        return crm_order
    
    async def update_order_status(self, order_id: str, new_status: OrderStatus, 
                                updated_by: str, notes: Optional[str] = None) -> bool:
        """Update order status and create timeline entry"""
        try:
            # Update order status
            update_data = {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
            
            # Set status-specific timestamps
            if new_status == OrderStatus.PAID:
                update_data["paid_at"] = datetime.utcnow()
                update_data["payment_status"] = PaymentStatus.COMPLETED
            elif new_status == OrderStatus.PROCESSING:
                update_data["processing_started_at"] = datetime.utcnow()
            elif new_status == OrderStatus.PURCHASED:
                update_data["purchased_at"] = datetime.utcnow()
            elif new_status == OrderStatus.SHIPPING:
                update_data["shipped_at"] = datetime.utcnow()
            elif new_status == OrderStatus.DELIVERED:
                update_data["delivered_at"] = datetime.utcnow()
            
            # Create timeline entry
            timeline_entry = OrderTimeline(
                order_id=order_id,
                status=new_status,
                description=self.get_status_description(new_status),
                created_by=updated_by,
                is_visible_to_customer=True
            )
            
            # Trigger notifications based on status
            await self.trigger_status_notifications(order_id, new_status)
            
            logger.info(f"Order {order_id} status updated to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return False
    
    def get_status_description(self, status: OrderStatus) -> str:
        descriptions = {
            OrderStatus.PENDING: "Заказ создан, ожидается оплата",
            OrderStatus.PAID: "Оплата получена, заказ принят в работу",
            OrderStatus.PROCESSING: "Заказ обрабатывается",
            OrderStatus.PURCHASING: "Покупаем товар у поставщика",
            OrderStatus.PURCHASED: "Товар куплен, готовится к отправке",
            OrderStatus.SHIPPING: "Товар отправлен клиенту",
            OrderStatus.IN_TRANSIT: "Товар в пути",
            OrderStatus.DELIVERED: "Товар доставлен клиенту",
            OrderStatus.CANCELLED: "Заказ отменён",
            OrderStatus.REFUNDED: "Произведён возврат средств"
        }
        return descriptions.get(status, f"Статус изменён на {status}")
    
    async def trigger_status_notifications(self, order_id: str, status: OrderStatus):
        """Trigger appropriate notifications based on order status"""
        try:
            if status == OrderStatus.PAID:
                await self.send_notification(
                    NotificationType.ORDER_PAID,
                    order_id,
                    "Заказ оплачен - требуется закупка",
                    f"Заказ #{order_id} оплачен клиентом. Необходимо произвести закупку товара."
                )
            
            elif status == OrderStatus.PURCHASED:
                await self.send_notification(
                    NotificationType.SHIPPING_REQUIRED,
                    order_id,
                    "Товар куплен - требуется отправка",
                    f"Заказ #{order_id} куплен у поставщика. Организуйте отправку клиенту."
                )
                
        except Exception as e:
            logger.error(f"Error triggering notifications: {str(e)}")
    
    async def send_notification(self, notification_type: NotificationType, 
                              order_id: str, title: str, message: str,
                              priority: Priority = Priority.MEDIUM):
        """Send CRM notification"""
        try:
            # Create notification record
            notification = CRMNotification(
                notification_type=notification_type,
                order_id=order_id,
                title=title,
                message=message,
                priority=priority,
                recipients=["+79135533369"]  # Admin phone
            )
            
            # Send SMS notification
            notification_data = {
                'order_id': order_id,
                'message': message
            }
            
            sms_sent = await self.notification_service.send_sms_notification(notification_data)
            
            if sms_sent:
                notification.is_sent = True
                notification.sent_at = datetime.utcnow()
            
            logger.info(f"CRM notification sent for order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending CRM notification: {str(e)}")
            return False
    
    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics"""
        try:
            # These would be real database queries in production
            stats = DashboardStats(
                total_orders=156,
                orders_pending_payment=12,
                orders_paid_need_purchase=8,
                orders_in_shipping=15,
                orders_delivered_today=3,
                
                revenue_today=45000.0,
                revenue_this_month=890000.0,
                profit_this_month=178000.0,
                
                active_customers=89,
                new_customers_this_month=23,
                
                avg_order_value=5700.0,
                avg_processing_time=36.5,
                customer_satisfaction=92.0
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return DashboardStats(
                total_orders=0, orders_pending_payment=0, orders_paid_need_purchase=0,
                orders_in_shipping=0, orders_delivered_today=0, revenue_today=0.0,
                revenue_this_month=0.0, profit_this_month=0.0, active_customers=0,
                new_customers_this_month=0, avg_order_value=0.0, avg_processing_time=0.0,
                customer_satisfaction=0.0
            )
    
    async def get_orders_need_attention(self) -> List[Dict]:
        """Get orders that need immediate attention"""
        try:
            # Mock data - in production this would be database queries
            urgent_orders = [
                {
                    "order_id": "ORD-20241010-ABC123",
                    "customer_name": "Иван Петров",
                    "product_name": "iPhone 15 Pro",
                    "status": "paid",
                    "amount": 95000,
                    "days_since_paid": 2,
                    "urgency": "high",
                    "action_required": "Произвести закупку у поставщика"
                },
                {
                    "order_id": "ORD-20241009-DEF456", 
                    "customer_name": "Мария Сидорова",
                    "product_name": "MacBook Pro M3",
                    "status": "purchased",
                    "amount": 180000,
                    "days_since_purchased": 1,
                    "urgency": "medium",
                    "action_required": "Организовать отправку клиенту"
                }
            ]
            
            return urgent_orders
            
        except Exception as e:
            logger.error(f"Error getting urgent orders: {str(e)}")
            return []
    
    async def set_reminder(self, order_id: str, reminder_time: datetime, 
                          reminder_type: NotificationType, message: str):
        """Set automated reminder for order"""
        try:
            # In production, this would use a task queue like Celery
            # For now, we'll just log the reminder
            logger.info(f"Reminder set for order {order_id} at {reminder_time}: {message}")
            
            # Calculate delay
            delay = (reminder_time - datetime.utcnow()).total_seconds()
            
            if delay > 0:
                # Schedule the reminder (simplified implementation)
                asyncio.create_task(self._send_delayed_reminder(delay, order_id, message))
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting reminder: {str(e)}")
            return False
    
    async def _send_delayed_reminder(self, delay: float, order_id: str, message: str):
        """Send delayed reminder"""
        try:
            await asyncio.sleep(delay)
            
            notification_data = {
                'order_id': order_id,
                'message': f"⏰ Напоминание: {message}"
            }
            
            await self.notification_service.send_sms_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error sending delayed reminder: {str(e)}")