"""
Advanced CRM API Routes
Complete customer relationship management system with automation and support
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
import logging
from datetime import datetime

from models.crm import (
    CustomerProfile, CustomerStatus, CustomerSegment, SupportTicket,
    TicketStatus, TicketCategory, CreateTicketRequest, UpdateTicketRequest,
    SendCommunicationRequest, CustomerFilterRequest, CRMResponse,
    CustomerListResponse, CRMDashboardData, AutomationRule, Priority,
    CommunicationType
)
from services.advanced_crm_service import AdvancedCRMService
from utils.auth import get_current_admin_user, get_current_user

router = APIRouter(prefix="/api/crm", tags=["crm"])
logger = logging.getLogger(__name__)

# Dependency to get CRM service
async def get_crm_service() -> AdvancedCRMService:
    """Get CRM service instance"""
    from server import advanced_crm_service
    return advanced_crm_service

# Customer Management Endpoints
@router.get("/customers")
async def get_customers(
    status: Optional[str] = Query(None, description="Filter by customer status"),
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Get customers with filtering (admin only)"""
    try:
        # Build filter request
        filter_request = CustomerFilterRequest(
            status=[CustomerStatus(status)] if status else None,
            segments=[CustomerSegment(segment)] if segment else None,
            limit=limit,
            offset=offset
        )
        
        result = await crm_service.filter_customers(filter_request)
        return result.model_dump()
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Неверные параметры фильтра: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении списка клиентов"
        )

@router.get("/customers/{customer_id}")
async def get_customer_profile(
    customer_id: str,
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Get customer profile by ID (admin only)"""
    try:
        customer = await crm_service.get_customer_profile(customer_id)
        
        if not customer:
            raise HTTPException(
                status_code=404,
                detail="Клиент не найден"
            )
        
        # Get additional data
        metrics = await crm_service.calculate_customer_metrics(customer_id)
        communications = await crm_service.get_customer_communications(customer_id, limit=20)
        tickets = await crm_service.get_support_tickets(customer_id=customer_id, limit=10)
        
        return {
            "success": True,
            "data": {
                "profile": customer.model_dump(),
                "metrics": metrics,
                "recent_communications": [comm.model_dump() for comm in communications],
                "recent_tickets": [ticket.model_dump() for ticket in tickets]
            },
            "message": "Профиль клиента получен"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer profile {customer_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении профиля клиента"
        )

@router.put("/customers/{customer_id}")
async def update_customer_profile(
    customer_id: str,
    updates: dict,
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Update customer profile (admin only)"""
    try:
        updated_customer = await crm_service.update_customer_profile(customer_id, updates)
        
        if not updated_customer:
            raise HTTPException(
                status_code=404,
                detail="Клиент не найден"
            )
        
        return {
            "success": True,
            "data": updated_customer.model_dump(),
            "message": "Профиль клиента обновлён"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer profile {customer_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении профиля клиента"
        )

@router.post("/customers/{customer_id}/segment")
async def update_customer_segment(
    customer_id: str,
    background_tasks: BackgroundTasks,
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Auto-segment customer based on behavior (admin only)"""
    try:
        # Run segmentation in background
        background_tasks.add_task(
            crm_service.segment_customer,
            customer_id
        )
        
        return {
            "success": True,
            "message": "Сегментация клиента запущена"
        }
        
    except Exception as e:
        logger.error(f"Error triggering customer segmentation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при запуске сегментации"
        )

# Support Ticket System
@router.post("/tickets")
async def create_support_ticket(
    request: CreateTicketRequest,
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Create support ticket (public endpoint)"""
    try:
        result = await crm_service.create_support_ticket(request)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message
            )
        
        return result.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при создании заявки в поддержку"
        )

@router.get("/tickets")
async def get_support_tickets(
    status: Optional[str] = Query(None, description="Filter by ticket status"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(50, le=200),
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Get support tickets with filtering (admin only)"""
    try:
        ticket_status = TicketStatus(status) if status else None
        tickets = await crm_service.get_support_tickets(
            customer_id=customer_id,
            status=ticket_status,
            limit=limit
        )
        
        return {
            "success": True,
            "data": [ticket.model_dump() for ticket in tickets],
            "total": len(tickets),
            "message": f"Получено {len(tickets)} заявок"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный статус заявки: {status}"
        )
    except Exception as e:
        logger.error(f"Error getting support tickets: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении заявок поддержки"
        )

@router.put("/tickets/{ticket_id}")
async def update_support_ticket(
    ticket_id: str,
    request: UpdateTicketRequest,
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Update support ticket (admin only)"""
    try:
        result = await crm_service.update_support_ticket(ticket_id, request)
        
        if not result.success:
            raise HTTPException(
                status_code=404 if "не найдена" in result.message else 400,
                detail=result.message
            )
        
        return result.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating support ticket {ticket_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обновлении заявки"
        )

@router.get("/tickets/categories")
async def get_ticket_categories():
    """Get available ticket categories"""
    try:
        categories = {
            TicketCategory.ORDER_ISSUE.value: {
                "name": "Проблема с заказом",
                "description": "Вопросы по статусу, изменению или отмене заказа",
                "priority": Priority.MEDIUM.value
            },
            TicketCategory.PAYMENT_PROBLEM.value: {
                "name": "Проблема с оплатой",
                "description": "Ошибки оплаты, возвраты, счета",
                "priority": Priority.HIGH.value
            },
            TicketCategory.DELIVERY_INQUIRY.value: {
                "name": "Вопрос по доставке",
                "description": "Сроки, адрес, способ доставки",
                "priority": Priority.MEDIUM.value
            },
            TicketCategory.PRODUCT_QUESTION.value: {
                "name": "Вопрос о товаре",
                "description": "Характеристики, совместимость, наличие",
                "priority": Priority.LOW.value
            },
            TicketCategory.TECHNICAL_ISSUE.value: {
                "name": "Техническая проблема",
                "description": "Проблемы с сайтом, приложением",
                "priority": Priority.HIGH.value
            },
            TicketCategory.ACCOUNT_ISSUE.value: {
                "name": "Проблема с аккаунтом",
                "description": "Вход, пароль, профиль",
                "priority": Priority.MEDIUM.value
            },
            TicketCategory.REFUND_REQUEST.value: {
                "name": "Запрос возврата",
                "description": "Возврат товара или денежных средств",
                "priority": Priority.HIGH.value
            },
            TicketCategory.GENERAL_INQUIRY.value: {
                "name": "Общий вопрос",
                "description": "Прочие вопросы",
                "priority": Priority.LOW.value
            },
            TicketCategory.COMPLAINT.value: {
                "name": "Жалоба",
                "description": "Недовольство сервисом или товаром",
                "priority": Priority.HIGH.value
            },
            TicketCategory.COMPLIMENT.value: {
                "name": "Благодарность",
                "description": "Положительный отзыв",
                "priority": Priority.LOW.value
            }
        }
        
        return {
            "success": True,
            "data": categories,
            "message": "Категории заявок получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting ticket categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении категорий"
        )

# Communication System
@router.post("/communications/send")
async def send_communication(
    request: SendCommunicationRequest,
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Send communication to customer (admin only)"""
    try:
        result = await crm_service.send_communication(request)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message
            )
        
        return result.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending communication: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при отправке сообщения"
        )

@router.get("/communications/types")
async def get_communication_types():
    """Get available communication types"""
    try:
        types = {
            CommunicationType.EMAIL.value: {
                "name": "Email",
                "description": "Электронная почта",
                "icon": "mail"
            },
            CommunicationType.SMS.value: {
                "name": "SMS",
                "description": "SMS сообщение",
                "icon": "message-circle"
            },
            CommunicationType.PHONE_CALL.value: {
                "name": "Звонок",
                "description": "Телефонный звонок",
                "icon": "phone"
            },
            CommunicationType.SYSTEM_NOTIFICATION.value: {
                "name": "Уведомление",
                "description": "Системное уведомление",
                "icon": "bell"
            },
            CommunicationType.MARKETING_EMAIL.value: {
                "name": "Маркетинг",
                "description": "Маркетинговое письмо",
                "icon": "target"
            },
            CommunicationType.ORDER_UPDATE.value: {
                "name": "Статус заказа",
                "description": "Обновление заказа",
                "icon": "package"
            }
        }
        
        return {
            "success": True,
            "data": types,
            "message": "Типы коммуникаций получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting communication types: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении типов коммуникаций"
        )

@router.get("/communications/{customer_id}")
async def get_customer_communications(
    customer_id: str,
    limit: int = Query(50, le=200),
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Get customer communication history (admin only)"""
    try:
        communications = await crm_service.get_customer_communications(customer_id, limit)
        
        return {
            "success": True,
            "data": [comm.model_dump() for comm in communications],
            "total": len(communications),
            "message": f"Получено {len(communications)} сообщений"
        }
        
    except Exception as e:
        logger.error(f"Error getting customer communications: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении истории сообщений"
        )

# Automation System
@router.post("/automation/rules")
async def create_automation_rule(
    rule: AutomationRule,
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Create automation rule (admin only)"""
    try:
        result = await crm_service.create_automation_rule(rule)
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message
            )
        
        return result.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating automation rule: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при создании правила автоматизации"
        )

@router.get("/automation/templates")
async def get_automation_templates(admin = Depends(get_current_admin_user)):
    """Get automation rule templates (admin only)"""
    try:
        templates = {
            "welcome_new_customer": {
                "name": "Приветствие нового клиента",
                "description": "Отправить приветственное сообщение новому клиенту",
                "trigger_event": "customer_registered",
                "actions": [
                    {
                        "type": "send_email",
                        "subject": "Добро пожаловать в BuyAnywhere!",
                        "content": "Спасибо за регистрацию! Мы поможем вам покупать товары со всего мира."
                    }
                ]
            },
            "order_confirmation": {
                "name": "Подтверждение заказа",
                "description": "Отправить SMS с подтверждением заказа",
                "trigger_event": "order_placed",
                "actions": [
                    {
                        "type": "send_sms",
                        "content": "Ваш заказ {{order_number}} принят в обработку. Спасибо за покупку!"
                    }
                ]
            },
            "inactive_customer_reactivation": {
                "name": "Реактивация неактивных клиентов",
                "description": "Отправить предложение клиентам без заказов 30+ дней",
                "trigger_event": "customer_inactive_30_days",
                "actions": [
                    {
                        "type": "send_email",
                        "subject": "Скидка 10% на ваш следующий заказ",
                        "content": "Мы скучаем по вам! Получите скидку 10% на следующую покупку."
                    }
                ]
            },
            "vip_customer_upgrade": {
                "name": "Перевод в VIP статус",
                "description": "Автоматически назначить VIP статус при превышении суммы покупок",
                "trigger_event": "customer_spent_threshold",
                "conditions": {
                    "total_spent": {"$gte": 100000}
                },
                "actions": [
                    {
                        "type": "update_segment",
                        "segment": "vip"
                    },
                    {
                        "type": "send_sms",
                        "content": "Поздравляем! Вы получили VIP статус и персональные условия."
                    }
                ]
            }
        }
        
        return {
            "success": True,
            "data": templates,
            "message": "Шаблоны автоматизации получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting automation templates: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении шаблонов автоматизации"
        )

# Dashboard and Analytics
@router.get("/dashboard")
async def get_crm_dashboard(
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Get CRM dashboard data (admin only)"""
    try:
        dashboard = await crm_service.get_crm_dashboard()
        
        return {
            "success": True,
            "data": dashboard.model_dump(),
            "message": "Данные CRM панели получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting CRM dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении данных CRM панели"
        )

@router.get("/analytics/customer-segments")
async def get_customer_segments_analytics(
    admin = Depends(get_current_admin_user),
    crm_service: AdvancedCRMService = Depends(get_crm_service)
):
    """Get customer segments analytics (admin only)"""
    try:
        segments_info = {
            CustomerSegment.HIGH_VALUE.value: {
                "name": "Дорогие клиенты",
                "description": "Клиенты с высокой суммой покупок (50,000+ ₽)",
                "color": "purple",
                "criteria": "total_spent >= 50000"
            },
            CustomerSegment.FREQUENT_BUYER.value: {
                "name": "Частые покупатели",
                "description": "Клиенты с 10+ заказами",
                "color": "blue",
                "criteria": "total_orders >= 10"
            },
            CustomerSegment.NEW_CUSTOMER.value: {
                "name": "Новые клиенты",
                "description": "Зарегистрированы менее 30 дней назад",
                "color": "green",
                "criteria": "created_at <= 30 days ago"
            },
            CustomerSegment.RETURNING_CUSTOMER.value: {
                "name": "Возвращающиеся клиенты",
                "description": "Клиенты с повторными заказами",
                "color": "orange",
                "criteria": "total_orders > 1"
            },
            CustomerSegment.PREMIUM_BUYER.value: {
                "name": "Премиум покупатели",
                "description": "Высокая средняя стоимость заказа (10,000+ ₽)",
                "color": "gold",
                "criteria": "average_order_value >= 10000"
            }
        }
        
        return {
            "success": True,
            "data": segments_info,
            "message": "Информация о сегментах получена"
        }
        
    except Exception as e:
        logger.error(f"Error getting customer segments analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении аналитики сегментов"
        )

@router.get("/health")
async def crm_health_check():
    """Health check endpoint for CRM system"""
    try:
        return {
            "status": "healthy",
            "service": "advanced_crm",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "customer_management",
                "support_tickets",
                "communication_history",
                "automation_rules",
                "customer_segmentation",
                "analytics_dashboard",
                "russian_localization"
            ]
        }
        
    except Exception as e:
        logger.error(f"CRM health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }