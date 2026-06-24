"""
Telephony API Routes
Provides REST API endpoints for AI IP Telephony system management
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, status
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import List, Optional, Dict, Any
import logging
import os
from datetime import datetime

from models.telephony import (
    ProviderType, RussianCity, CreateProviderConfigRequest, ProviderConfigResponse,
    PurchaseNumberRequest, NumberSearchRequest, MakeCallRequest, CallResponse,
    ProviderConfig, VirtualNumber, CallInfo, TelephonyDashboard
)
from services.telephony_service import TelephonyService
from utils.auth import get_current_admin_user as get_current_admin

router = APIRouter(prefix="/api/telephony", tags=["telephony"])
logger = logging.getLogger(__name__)

# Dependency to get telephony service
async def get_telephony_service() -> TelephonyService:
    """Get telephony service instance"""
    # This will be injected by the main application
    # For now, we'll assume it's available in the app state
    from server import telephony_service
    return telephony_service

# Provider Management Endpoints
@router.get("/providers/templates")
async def get_provider_templates(admin = Depends(get_current_admin)):
    """Get provider configuration templates"""
    try:
        templates = {
            "zadarma": {
                "name": "Zadarma",
                "description": "Российский VoIP провайдер с поддержкой виртуальных номеров",
                "fields": [
                    {
                        "key": "api_key",
                        "label": "API Key",
                        "type": "text",
                        "required": True,
                        "description": "API ключ из личного кабинета Zadarma"
                    },
                    {
                        "key": "api_secret", 
                        "label": "API Secret",
                        "type": "password",
                        "required": True,
                        "description": "Секретный ключ API"
                    },
                    {
                        "key": "webhook_secret",
                        "label": "Webhook Secret",
                        "type": "password",
                        "required": False,
                        "description": "Секретный ключ для веб-хуков (опционально)"
                    }
                ],
                "features": [
                    "voice_calls",
                    "sms",
                    "virtual_numbers",
                    "call_recording",
                    "russian_numbers"
                ],
                "supported_cities": ["moscow", "krasnoyarsk", "vladivostok"]
            },
            "twilio": {
                "name": "Twilio",
                "description": "Международный провайдер облачной телефонии",
                "fields": [
                    {
                        "key": "account_sid",
                        "label": "Account SID", 
                        "type": "text",
                        "required": True,
                        "description": "Идентификатор аккаунта Twilio"
                    },
                    {
                        "key": "auth_token",
                        "label": "Auth Token",
                        "type": "password", 
                        "required": True,
                        "description": "Токен авторизации"
                    }
                ],
                "features": [
                    "voice_calls",
                    "sms",
                    "virtual_numbers", 
                    "call_recording"
                ],
                "note": "Ограниченная поддержка российских номеров"
            }
        }
        
        return {
            "success": True,
            "data": templates,
            "message": "Шаблоны провайдеров получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting provider templates: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении шаблонов провайдеров"
        )

@router.post("/providers", response_model=ProviderConfigResponse)
async def create_provider(
    request: CreateProviderConfigRequest,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Create new telephony provider configuration"""
    try:
        response = await telephony_service.create_provider_config(request)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating provider: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при создании провайдера"
        )

@router.get("/providers")
async def get_providers(
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Get all configured providers"""
    try:
        configs = telephony_service.provider_manager.get_provider_configs()
        
        return {
            "success": True,
            "data": [config.model_dump() for config in configs],
            "message": "Провайдеры получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении провайдеров"
        )

@router.post("/providers/{provider_id}/test")
async def test_provider(
    provider_id: str,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Test provider configuration"""
    try:
        result = await telephony_service.test_provider_config(provider_id)
        
        return {
            "success": result['success'],
            "data": result,
            "message": result['message']
        }
        
    except Exception as e:
        logger.error(f"Error testing provider {provider_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при тестировании провайдера"
        )

@router.post("/providers/{provider_id}/activate")
async def activate_provider(
    provider_id: str,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Switch to a different provider"""
    try:
        success = await telephony_service.provider_manager.switch_provider(provider_id)
        
        if success:
            return {
                "success": True,
                "message": "Провайдер активирован"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Провайдер не найден"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating provider {provider_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при активации провайдера"
        )

# Virtual Number Management
@router.get("/numbers/search")
async def search_numbers(
    city: RussianCity,
    limit: int = 10,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Search available virtual numbers for Russian cities"""
    try:
        numbers = await telephony_service.search_available_numbers(city, limit)
        
        return {
            "success": True,
            "data": [number.model_dump() for number in numbers],
            "message": f"Найдено {len(numbers)} доступных номеров для {city.value}"
        }
        
    except Exception as e:
        logger.error(f"Error searching numbers for {city}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при поиске доступных номеров"
        )

@router.post("/numbers/purchase", response_model=CallResponse)
async def purchase_number(
    request: PurchaseNumberRequest,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Purchase virtual number"""
    try:
        response = await telephony_service.purchase_virtual_number(request)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing number {request.number}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при приобретении номера"
        )

@router.get("/numbers")
async def get_virtual_numbers(
    city: Optional[RussianCity] = None,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Get virtual numbers, optionally filtered by city"""
    try:
        numbers = await telephony_service.get_virtual_numbers(city)
        
        return {
            "success": True,
            "data": [number.model_dump() for number in numbers],
            "message": f"Получено {len(numbers)} виртуальных номеров"
        }
        
    except Exception as e:
        logger.error(f"Error getting virtual numbers: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении виртуальных номеров"
        )

# Call Management
@router.post("/calls/outbound", response_model=CallResponse)
async def make_call(
    request: MakeCallRequest,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Make outbound call"""
    try:
        response = await telephony_service.make_outbound_call(request)
        
        if not response.success:
            raise HTTPException(
                status_code=400,
                detail=response.message
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making outbound call: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при совершении звонка"
        )

@router.get("/calls")
async def get_calls(
    limit: int = 50,
    offset: int = 0,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Get call history"""
    try:
        # Query calls from database
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$skip": offset},
            {"$limit": limit}
        ]
        
        calls = []
        async for call_doc in telephony_service.calls_collection.aggregate(pipeline):
            calls.append(CallInfo(**call_doc).model_dump())
        
        # Get total count
        total_calls = await telephony_service.calls_collection.count_documents({})
        
        return {
            "success": True,
            "data": {
                "calls": calls,
                "total": total_calls,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_calls
            },
            "message": f"Получено {len(calls)} звонков"
        }
        
    except Exception as e:
        logger.error(f"Error getting calls: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении истории звонков"
        )

# Dashboard and Statistics
@router.get("/dashboard")
async def get_telephony_dashboard(
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Get telephony dashboard data"""
    try:
        dashboard = await telephony_service.get_telephony_dashboard()
        
        return {
            "success": True,
            "data": dashboard.model_dump(),
            "message": "Данные панели управления получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting telephony dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении данных панели управления"
        )

# Webhook Endpoints
@router.get("/webhooks/zadarma")
async def zadarma_webhook_validation(zd_echo: Optional[str] = None):
    """Handle Zadarma webhook endpoint validation"""
    if zd_echo:
        logger.info(f"Zadarma webhook validation: {zd_echo}")
        return PlainTextResponse(zd_echo)
    return {"status": "ok"}

@router.post("/webhooks/zadarma")
async def zadarma_webhook_handler(
    request: Request,
    background_tasks: BackgroundTasks,
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Handle Zadarma webhook events"""
    try:
        # Get request body and headers
        body = await request.body()
        headers = request.headers
        
        # Parse webhook data
        if request.headers.get('content-type', '').startswith('application/json'):
            webhook_data = await request.json()
        else:
            # Handle form-encoded data
            form_data = await request.form()
            webhook_data = dict(form_data)
        
        logger.info(f"Received Zadarma webhook: {webhook_data}")
        
        # Process webhook in background
        background_tasks.add_task(
            telephony_service.process_webhook,
            ProviderType.ZADARMA,
            webhook_data
        )
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error processing Zadarma webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обработке webhook"
        )

# Configuration and Settings
@router.get("/settings")
async def get_telephony_settings(admin = Depends(get_current_admin)):
    """Get telephony system settings"""
    try:
        settings = {
            "routing_number": "+79135533369",
            "supported_cities": [
                {
                    "code": "moscow",
                    "name": "Москва",
                    "area_codes": ["495", "499"],
                    "timezone": "Europe/Moscow"
                },
                {
                    "code": "krasnoyarsk", 
                    "name": "Красноярск",
                    "area_codes": ["391"],
                    "timezone": "Asia/Krasnoyarsk"
                },
                {
                    "code": "vladivostok",
                    "name": "Владивосток", 
                    "area_codes": ["423"],
                    "timezone": "Asia/Vladivostok"
                }
            ],
            "ai_features": {
                "russian_language_processing": True,
                "intent_recognition": True,
                "automatic_routing": True,
                "call_transcription": True
            },
            "business_hours": {
                "start": 9,
                "end": 18,
                "timezone": "Europe/Moscow"
            }
        }
        
        return {
            "success": True,
            "data": settings,
            "message": "Настройки телефонии получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting telephony settings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении настроек"
        )

@router.post("/test/ai-analysis")
async def test_ai_analysis(
    text: str,
    city: RussianCity = RussianCity.MOSCOW,
    admin = Depends(get_current_admin),
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Test AI analysis of Russian text"""
    try:
        # Process text with AI engine
        result = await telephony_service.ai_engine.russian_service.process_customer_input(text, city)
        
        return {
            "success": True,
            "data": result,
            "message": "Анализ текста выполнен"
        }
        
    except Exception as e:
        logger.error(f"Error testing AI analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при анализе текста"
        )

# Public endpoints for call handling (no auth required)
@router.post("/public/handle-call")
async def handle_public_call(
    from_number: str,
    to_number: str,
    provider_call_id: Optional[str] = None,
    telephony_service: TelephonyService = Depends(get_telephony_service)
):
    """Handle incoming call (public endpoint for provider callbacks)"""
    try:
        call_info = await telephony_service.handle_inbound_call(
            from_number=from_number,
            to_number=to_number,
            provider_call_id=provider_call_id
        )
        
        return {
            "success": True,
            "data": call_info.model_dump(),
            "message": "Звонок обработан"
        }
        
    except Exception as e:
        logger.error(f"Error handling public call: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при обработке звонка"
        )

@router.get("/health")
async def telephony_health_check():
    """Health check endpoint for telephony system"""
    try:
        return {
            "status": "healthy",
            "service": "telephony",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "russian_language_processing",
                "zadarma_integration", 
                "ai_call_routing",
                "virtual_numbers"
            ]
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )