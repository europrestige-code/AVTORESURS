import os
import asyncio
import aiohttp
import json
from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.sms_phone = "+79135533369"  # Target phone from requirements
        self.admin_email = None  # Will be provided later
        
    async def send_sms_notification(self, order_data: Dict) -> bool:
        """Send SMS notification about new order"""
        try:
            # For now, we'll simulate SMS sending since no SMS service is configured
            # In production, this would integrate with SMS.ru, SMSC.ru, or similar
            
            message = f"""
🛒 НОВЫЙ ЗАКАЗ BuyAnywhere

📱 Заказ: {order_data.get('order_id', 'N/A')}
🛍️ Товар: {order_data.get('product_name', 'Unknown')}
💰 Сумма: {order_data.get('total_price', 0)} ₽
👤 Клиент: {order_data.get('customer_name', 'Unknown')}
📞 Телефон: {order_data.get('customer_phone', 'Unknown')}

🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}
            """.strip()
            
            # Simulate SMS sending - in production, replace with actual SMS API
            logger.info(f"SMS to {self.sms_phone}: {message}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # For demo purposes, always return success
            # In production, this would return the actual API response
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            return False
    
    async def send_email_notification(self, order_data: Dict, customer_email: Optional[str] = None) -> bool:
        """Send email notification about order"""
        try:
            if not self.admin_email:
                logger.warning("Admin email not configured, skipping email notification")
                return False
            
            # Email content
            subject = f"Новый заказ BuyAnywhere #{order_data.get('order_id', 'N/A')}"
            
            email_body = f"""
            <h2>Новый заказ в системе BuyAnywhere</h2>
            
            <h3>Детали заказа:</h3>
            <ul>
                <li><strong>ID заказа:</strong> {order_data.get('order_id', 'N/A')}</li>
                <li><strong>Товар:</strong> {order_data.get('product_name', 'Unknown')}</li>
                <li><strong>Магазин:</strong> {order_data.get('store_name', 'Unknown')}</li>
                <li><strong>Общая стоимость:</strong> {order_data.get('total_price', 0)} ₽</li>
                <li><strong>Дата создания:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</li>
            </ul>
            
            <h3>Информация о клиенте:</h3>
            <ul>
                <li><strong>Имя:</strong> {order_data.get('customer_name', 'Unknown')}</li>
                <li><strong>Телефон:</strong> {order_data.get('customer_phone', 'Unknown')}</li>
                <li><strong>Email:</strong> {customer_email or 'Не указан'}</li>
            </ul>
            
            <h3>Расчёт стоимости:</h3>
            <ul>
                <li>Цена товара: {order_data.get('original_price', 0)} ₽</li>
                <li>Комиссия: {order_data.get('commission', 0)} ₽</li>
                <li>Доставка: {order_data.get('shipping', 0)} ₽</li>
                <li>Таможня: {order_data.get('customs', 0)} ₽</li>
                <li>Страховка: {order_data.get('insurance', 0)} ₽</li>
            </ul>
            
            <p><strong>Ссылка на товар:</strong> {order_data.get('product_url', 'Не указана')}</p>
            """
            
            # Simulate email sending - in production, replace with actual email service
            logger.info(f"Email notification prepared for {self.admin_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {email_body}")
            
            # Simulate API call delay
            await asyncio.sleep(0.1)
            
            # For demo purposes, always return success
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    async def send_order_confirmation(self, order_data: Dict) -> Dict[str, bool]:
        """Send both SMS and email notifications"""
        results = {}
        
        # Send SMS notification
        results['sms_sent'] = await self.send_sms_notification(order_data)
        
        # Send email notification if customer email is provided
        customer_email = order_data.get('customer_email')
        if customer_email:
            results['email_sent'] = await self.send_email_notification(order_data, customer_email)
        else:
            results['email_sent'] = False
            
        return results
    
    def set_admin_email(self, email: str):
        """Set admin email for notifications"""
        self.admin_email = email
        logger.info(f"Admin email set to: {email}")
    
    async def send_status_update(self, order_id: str, status: str, customer_phone: str) -> bool:
        """Send status update to customer"""
        try:
            status_messages = {
                'paid': '✅ Оплата получена, начинаем обработку заказа',
                'processing': '🛒 Заказ в обработке, покупаем товар',
                'shipped': '📦 Товар отправлен, ожидайте доставку',
                'delivered': '🎉 Заказ доставлен! Спасибо за покупку!'
            }
            
            message = f"""
BuyAnywhere - Заказ #{order_id}

{status_messages.get(status, f'Статус обновлён: {status}')}

🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}
            """.strip()
            
            # Simulate SMS sending
            logger.info(f"Status update SMS to {customer_phone}: {message}")
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending status update: {str(e)}")
            return False