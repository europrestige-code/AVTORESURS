from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our services and models
from services.ai_service import AIService
from services.currency_service import CurrencyService
from services.notification_service import NotificationService
from services.auth_service import AuthService
from services.crm_service import CRMService
from models.order import (
    Order, OrderInput, OrderResponse, CustomerInfo, ProductDetails, PriceCalculation,
    PriceCalculationRequest, PriceCalculationResponse
)
from models.user import User, UserLogin, UserRegister, UserResponse
from models.crm import CRMOrder, OrderStatus, DashboardStats

# Import route modules
from routes.auth_routes import router as auth_router
from routes.customer_routes import router as customer_router
from routes.customer_payment_routes import router as customer_payment_router
from routes.ai_search_routes import router as ai_search_router
from routes.admin_auth_routes import router as admin_auth_router
from routes.admin_payment_routes import router as admin_payment_router
from routes.telephony_routes import router as telephony_router
from routes.news_routes import router as news_router
from routes.crm_routes import router as crm_router
from routes.logo_routes import router as logo_router
from routes.crm_bulk_routes import router as crm_bulk_router
from routes.auto_routes import router as auto_router
from services.auto_service import AutoService


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize services
ai_service = AIService()
currency_service = CurrencyService()
notification_service = NotificationService()
auth_service = AuthService()
crm_service = CRMService(notification_service)

# Initialize telephony service (will be initialized in startup event)
telephony_service = None

# Initialize news service (will be initialized in startup event)
news_service = None

# Initialize CRM service (will be initialized in startup event)
advanced_crm_service = None

# Define dependency injection
def get_database():
    return db

def get_auth_service():
    return auth_service

def get_crm_service():
    return crm_service

# Database dependency function 
async def get_db():
    return db


# Define Models (keeping the existing ones for compatibility)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "BuyAnywhere API - Russian Personal Shopping Service"}

@api_router.post("/calculate-price", response_model=PriceCalculationResponse)
async def calculate_price(request: PriceCalculationRequest):
    """Calculate price for a product using AI analysis and real currency rates"""
    try:
        logger.info(f"Price calculation request: {request.input_type}")
        
        # Step 1: Analyze product based on input type
        if request.input_type == "url" and request.url:
            product_info = await ai_service.analyze_product_from_url(request.url)
        elif request.input_type == "photo" and request.photo_base64:
            product_info = await ai_service.analyze_product_from_photo(request.photo_base64)
        elif request.input_type == "manual":
            product_info = await ai_service.analyze_manual_input(
                request.product_name or "",
                request.model or "",
                request.serial_number or "",
                request.description or ""
            )
        else:
            raise HTTPException(status_code=400, detail="Неверный тип ввода или отсутствуют обязательные поля")
        
        # Step 2: Find best price using AI
        price_info = await ai_service.find_best_price(product_info)
        
        # Step 3: Calculate price breakdown with real currency rates
        best_price_usd = price_info['cheapest_option']['price_usd']
        estimated_shipping_usd = 25.0  # Default shipping estimate
        
        price_breakdown = await currency_service.calculate_price_breakdown(
            best_price_usd, estimated_shipping_usd
        )
        
        # Step 4: Format response
        response = PriceCalculationResponse(
            success=True,
            product_name=product_info.get('product_name', 'Unknown Product'),
            best_store=price_info['cheapest_option']['store_name'],
            original_price_usd=best_price_usd,
            exchange_rate=price_breakdown['exchange_rate'],
            original_price_rub=price_breakdown['original_price_rub'],
            commission=price_breakdown['commission_rub'],
            shipping=price_breakdown['shipping_rub'],
            customs=price_breakdown['customs_rub'],
            insurance=price_breakdown['insurance_rub'],
            total_price=price_breakdown['total_rub'],
            breakdown={
                "original_price": currency_service.format_price_rub(price_breakdown['original_price_rub']),
                "commission": currency_service.format_price_rub(price_breakdown['commission_rub']),
                "shipping": currency_service.format_price_rub(price_breakdown['shipping_rub']),
                "customs": currency_service.format_price_rub(price_breakdown['customs_rub']),
                "insurance": currency_service.format_price_rub(price_breakdown['insurance_rub']),
                "total_price": currency_service.format_price_rub(price_breakdown['total_rub'])
            },
            ai_confidence=product_info.get('confidence', 0.8)
        )
        
        logger.info(f"Price calculation completed: {response.product_name} - {response.total_price} RUB")
        return response
        
    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Error in price calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка расчёта стоимости: {str(e)}")

@api_router.post("/create-order", response_model=OrderResponse)
async def create_order(order_data: dict):
    """Create a new order and send notifications"""
    try:
        # Extract customer info
        customer_info = CustomerInfo(
            name=order_data.get('customer_name', ''),
            phone=order_data.get('customer_phone', ''),
            email=order_data.get('customer_email')
        )
        
        # Extract product details
        product_details = ProductDetails(
            name=order_data.get('product_name', ''),
            url=order_data.get('product_url'),
            description=order_data.get('product_description')
        )
        
        # Extract price calculation
        price_calc = PriceCalculation(
            original_price_usd=order_data.get('original_price_usd', 0),
            original_price_rub=order_data.get('original_price_rub', 0),
            commission_rub=order_data.get('commission', 0),
            shipping_rub=order_data.get('shipping', 0),
            customs_rub=order_data.get('customs', 0),
            insurance_rub=order_data.get('insurance', 0),
            total_rub=order_data.get('total_price', 0),
            exchange_rate=order_data.get('exchange_rate', 95.0)
        )
        
        # Create order input
        order_input = OrderInput(
            input_type=order_data.get('input_type', 'manual'),
            url=order_data.get('original_url'),
            product_name=order_data.get('product_name')
        )
        
        # Create order
        order = Order(
            customer_info=customer_info,
            product_details=product_details,
            price_calculation=price_calc,
            order_input=order_input
        )
        
        # Save to database
        order_dict = order.dict()
        await db.orders.insert_one(order_dict)
        
        # Prepare notification data
        notification_data = {
            'order_id': order.order_id,
            'product_name': product_details.name,
            'total_price': int(price_calc.total_rub),
            'customer_name': customer_info.name,
            'customer_phone': customer_info.phone,
            'customer_email': customer_info.email,
            'product_url': product_details.url or '',
            'store_name': order_data.get('store_name', ''),
            'original_price': int(price_calc.original_price_rub),
            'commission': int(price_calc.commission_rub),
            'shipping': int(price_calc.shipping_rub),
            'customs': int(price_calc.customs_rub),
            'insurance': int(price_calc.insurance_rub)
        }
        
        # Send notifications
        notification_results = await notification_service.send_order_confirmation(notification_data)
        
        # Update order with notification status
        await db.orders.update_one(
            {"order_id": order.order_id},
            {"$set": {"notifications_sent": list(notification_results.keys())}}
        )
        
        # Generate payment instructions
        total_formatted = currency_service.format_price_rub(price_calc.total_rub)
        payment_instructions = f"""
Переведите {total_formatted} ₽ одним из способов:
• Сбербанк: карта/счёт (реквизиты вышлем отдельно)
• Т-Банк: перевод по номеру телефона
• СБП: быстрые платежи по номеру +79135533369
        """.strip()
        
        response = OrderResponse(
            success=True,
            order_id=order.order_id,
            total_price=price_calc.total_rub,
            payment_instructions=payment_instructions,
            sms_sent=notification_results.get('sms_sent', False),
            email_sent=notification_results.get('email_sent', False),
            message=f"Заказ {order.order_id} создан успешно"
        )
        
        logger.info(f"Order created: {order.order_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания заказа: {str(e)}")

@api_router.get("/popular-services/{category}")
async def get_popular_services(category: str):
    """Get popular services for a category"""
    try:
        # For now, return the same mock data structure but from backend
        # This can be replaced with a real database or API later
        
        services_data = {
            "subscriptions": [
                {"name": "Netflix", "description": "Фильмы и сериалы", "url": "netflix.com", "estimated_price": "от 1500 ₽/мес"},
                {"name": "Spotify Premium", "description": "Музыка без рекламы", "url": "spotify.com", "estimated_price": "от 1200 ₽/мес"},
                {"name": "Adobe Creative Cloud", "description": "Photoshop, Illustrator, Premiere", "url": "adobe.com", "estimated_price": "от 5200 ₽/мес"}
            ],
            "courses": [
                {"name": "Coursera Plus", "description": "Курсы от топ университетов", "url": "coursera.org", "estimated_price": "от 4500 ₽/мес"},
                {"name": "MasterClass", "description": "Уроки от мировых экспертов", "url": "masterclass.com", "estimated_price": "от 15000 ₽/год"}
            ],
            "brands": [
                {"name": "Louis Vuitton", "description": "Сумки, аксессуары, одежда", "url": "louisvuitton.com", "estimated_price": "от 50000 ₽"},
                {"name": "Gucci", "description": "Luxury fashion и аксессуары", "url": "gucci.com", "estimated_price": "от 30000 ₽"}
            ],
            "travel": [
                {"name": "Booking.com", "description": "Бронирование отелей", "url": "booking.com", "estimated_price": "по тарифам отеля"},
                {"name": "Airbnb", "description": "Аренда жилья", "url": "airbnb.com", "estimated_price": "по тарифам хозяина"}
            ],
            "electronics": [
                {"name": "Apple Store", "description": "iPhone, MacBook, iPad", "url": "apple.com", "estimated_price": "от 50000 ₽"},
                {"name": "Best Buy", "description": "Электроника и гаджеты", "url": "bestbuy.com", "estimated_price": "от 5000 ₽"}
            ],
            "digital": [
                {"name": "Steam", "description": "PC игры", "url": "store.steampowered.com", "estimated_price": "от 500 ₽"},
                {"name": "Epic Games Store", "description": "Бесплатные игры каждую неделю", "url": "epicgames.com", "estimated_price": "от 1000 ₽"}
            ]
        }
        
        category_services = services_data.get(category, [])
        
        return {
            "category": category,
            "services": category_services
        }
        
    except Exception as e:
        logger.error(f"Error getting popular services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения сервисов: {str(e)}")

@api_router.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    try:
        order = await db.orders.find_one({"order_id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Remove MongoDB _id field for JSON serialization
        order.pop('_id', None)
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения заказа: {str(e)}")

@api_router.get("/currency-info")
async def get_currency_info():
    """Get current currency rate information"""
    try:
        rate_info = await currency_service.get_rate_info()
        return rate_info
    except Exception as e:
        logger.error(f"Error getting currency info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения курса валют: {str(e)}")

# Include the routers in the main app
app.include_router(api_router)
app.include_router(auth_router, prefix="/api/auth")
app.include_router(customer_router, prefix="/api/customer")
app.include_router(customer_payment_router)
app.include_router(ai_search_router)

# Include admin routes
app.include_router(admin_auth_router, prefix="/api/admin/auth")
app.include_router(admin_payment_router, prefix="/api/admin")

# Include telephony routes
app.include_router(telephony_router)

# Include news routes
app.include_router(news_router)

# Include CRM routes
app.include_router(crm_router)

# Include logo routes
app.include_router(logo_router)

# Include CRM bulk routes
app.include_router(crm_bulk_router)

# Include BuyAnywhere Auto routes (mounted at /api/auto)
app.include_router(auto_router)

# Include admin CRM routes
@api_router.get("/admin/dashboard")
async def get_admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        stats = await crm_service.get_dashboard_stats()
        urgent_orders = await crm_service.get_orders_need_attention()
        
        return {
            "stats": stats,
            "urgent_orders": urgent_orders,
            "system_status": "healthy"
        }
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")

@api_router.post("/admin/orders/{order_id}/status")
async def update_order_status_admin(order_id: str, status_data: dict):
    """Update order status (admin only)"""
    try:
        new_status = OrderStatus(status_data.get('status'))
        updated_by = status_data.get('updated_by', 'admin')
        notes = status_data.get('notes')
        
        success = await crm_service.update_order_status(order_id, new_status, updated_by, notes)
        
        if success:
            return {"message": f"Статус заказа {order_id} обновлён на {new_status}"}
        else:
            raise HTTPException(status_code=400, detail="Не удалось обновить статус")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Неверный статус: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса")

# AI Telephony endpoints
@api_router.get("/telephony/number")
async def get_support_number():
    """Get AI telephony support number"""
    # This would return the actual Twilio number when configured
    return {
        "support_number": "+7 (495) 123-45-67",  # Placeholder Russian number
        "description": "ИИ поддержка на русском языке",
        "available_24_7": True,
        "languages": ["русский"],
        "services": [
            "Информация о заказах",
            "Расчёт стоимости",
            "Статус доставки",
            "Общие вопросы"
        ]
    }

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_services():
    """Initialize services on startup"""
    global telephony_service, news_service, advanced_crm_service
    try:
        # Mock Redis client since we don't need it for basic telephony functionality
        class MockRedisClient:
            async def get(self, key): 
                return None
            async def set(self, key, value, ex=None): 
                return True
            async def setex(self, key, time, value):
                return True
            async def delete(self, key): 
                return True
            async def exists(self, key):
                return False
            async def incr(self, key):
                return 1
            async def expire(self, key, time):
                return True
            async def lpush(self, key, value):
                return 1
            async def close(self): 
                pass
        
        redis_client = MockRedisClient()
        
        # Get Emergent LLM key
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        if not emergent_key:
            logger.warning("EMERGENT_LLM_KEY not found, telephony AI features will be limited")
            
        # Initialize telephony service
        from services.telephony_service import TelephonyService
        telephony_service = TelephonyService(
            database=db,
            redis_client=redis_client,
            emergent_key=emergent_key or "demo_key"
        )
        
        # Initialize telephony service
        await telephony_service.initialize()
        logger.info("Telephony service initialized successfully")
        
        # Initialize news service
        from services.news_service import NewsService
        newsdata_api_key = os.environ.get('NEWSDATA_API_KEY')
        newsapi_api_key = os.environ.get('NEWSAPI_API_KEY')
        
        news_service = NewsService(
            database=db,
            emergent_key=emergent_key or "demo_key",
            newsdata_api_key=newsdata_api_key,
            newsapi_api_key=newsapi_api_key
        )
        
        # Initialize news service
        await news_service.initialize()
        logger.info("News service initialized successfully")
        
        # Initialize CRM service
        from services.advanced_crm_service import AdvancedCRMService
        advanced_crm_service = AdvancedCRMService(
            database=db,
            notification_service=notification_service,
            emergent_key=emergent_key or "demo_key"
        )
        
        # Initialize CRM service
        await advanced_crm_service.initialize()
        logger.info("Advanced CRM service initialized successfully")

        # Initialize Auto module indexes
        try:
            auto_svc = AutoService(db)
            await auto_svc.ensure_indexes()
        except Exception as ie:
            logger.warning(f"Auto module index init failed: {ie}")
        
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        # Don't fail startup if services fail
        telephony_service = None
        news_service = None
        advanced_crm_service = None

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    if telephony_service and hasattr(telephony_service, 'redis'):
        try:
            await telephony_service.redis.close()
        except:
            pass
