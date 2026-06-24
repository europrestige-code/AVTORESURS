from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging

from models.payment_config import (
    PaymentProvider, PaymentConfigRequest, PaymentConfigResponse,
    PaymentTestRequest, PaymentTestResponse, PaymentProviderStatus
)
from services.payment_config_service import PaymentConfigService
from services.auth_service import AuthService
from utils.auth import get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_payment_config_service() -> PaymentConfigService:
    """Dependency injection for payment config service"""
    from server import db  # Import here to avoid circular imports
    return PaymentConfigService(db)

@router.get("/payment-methods", response_model=List[PaymentConfigResponse])
async def get_payment_methods(
    config_service: PaymentConfigService = Depends(get_payment_config_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get all configured payment methods"""
    
    try:
        configs = await config_service.get_all_configs()
        
        responses = []
        for config in configs:
            response = PaymentConfigResponse(
                id=config.id,
                provider=config.provider,
                name=config.name,
                status=config.status,
                test_mode=config.configuration.get('test_mode', True),
                created_at=config.created_at,
                updated_at=config.updated_at,
                created_by=config.created_by
            )
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения платежных методов"
        )

@router.post("/payment-methods", response_model=PaymentConfigResponse)
async def create_payment_method(
    request: PaymentConfigRequest,
    config_service: PaymentConfigService = Depends(get_payment_config_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Create new payment method configuration"""
    
    try:
        config_data = {
            "provider": request.provider,
            "name": request.name,
            "status": request.status,
            "configuration": request.configuration
        }
        
        config = await config_service.create_config(config_data, current_user["email"])
        
        response = PaymentConfigResponse(
            id=config.id,
            provider=config.provider,
            name=config.name,
            status=config.status,
            test_mode=config.configuration.get('test_mode', True),
            created_at=config.created_at,
            updated_at=config.updated_at,
            created_by=config.created_by
        )
        
        logger.info(f"Created payment method: {config.provider} by {current_user['email']}")
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания платежного метода"
        )

@router.put("/payment-methods/{config_id}", response_model=PaymentConfigResponse)
async def update_payment_method(
    config_id: str,
    request: PaymentConfigRequest,
    config_service: PaymentConfigService = Depends(get_payment_config_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Update payment method configuration"""
    
    try:
        updates = {
            "name": request.name,
            "status": request.status,
            "configuration": request.configuration
        }
        
        config = await config_service.update_config(config_id, updates)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Платежный метод не найден"
            )
        
        response = PaymentConfigResponse(
            id=config.id,
            provider=config.provider,
            name=config.name,
            status=config.status,
            test_mode=config.configuration.get('test_mode', True),
            created_at=config.created_at,
            updated_at=config.updated_at,
            created_by=config.created_by
        )
        
        logger.info(f"Updated payment method: {config_id} by {current_user['email']}")
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления платежного метода"
        )

@router.delete("/payment-methods/{config_id}")
async def delete_payment_method(
    config_id: str,
    config_service: PaymentConfigService = Depends(get_payment_config_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Delete payment method configuration"""
    
    try:
        success = await config_service.delete_config(config_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Платежный метод не найден"
            )
        
        logger.info(f"Deleted payment method: {config_id} by {current_user['email']}")
        return {"message": "Платежный метод удален успешно"}
        
    except Exception as e:
        logger.error(f"Error deleting payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления платежного метода"
        )

@router.post("/payment-methods/{config_id}/test", response_model=PaymentTestResponse)
async def test_payment_method(
    config_id: str,
    test_request: PaymentTestRequest,
    config_service: PaymentConfigService = Depends(get_payment_config_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Test payment method configuration"""
    
    try:
        test_result = await config_service.test_configuration(config_id, test_request)
        
        logger.info(f"Tested payment method: {config_id} by {current_user['email']} - Success: {test_result.success}")
        return test_result
        
    except Exception as e:
        logger.error(f"Error testing payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка тестирования платежного метода"
        )

@router.get("/payment-providers")
async def get_payment_providers():
    """Get available payment providers and their configuration templates"""
    
    providers = {
        PaymentProvider.UNITPAY: {
            "name": "UnitPay (MIR карты)",
            "description": "Российская платежная система для приема платежей с карт МИР",
            "fields": [
                {"name": "secret_key", "label": "Секретный ключ", "type": "password", "required": True},
                {"name": "public_key", "label": "Публичный ключ", "type": "text", "required": True},
                {"name": "project_id", "label": "ID проекта", "type": "number", "required": True},
                {"name": "domain", "label": "Домен", "type": "text", "default": "unitpay.ru"},
                {"name": "test_mode", "label": "Тестовый режим", "type": "boolean", "default": True}
            ]
        },
        PaymentProvider.TBANK_QR: {
            "name": "T-Bank QR",
            "description": "QR-коды T-Bank для быстрых платежей",
            "fields": [
                {"name": "terminal_id", "label": "ID терминала", "type": "text", "required": True},
                {"name": "terminal_password", "label": "Пароль терминала", "type": "password", "required": True},
                {"name": "api_url", "label": "URL API", "type": "text", "default": "https://securepay.tinkoff.ru/v2/"},
                {"name": "test_mode", "label": "Тестовый режим", "type": "boolean", "default": True}
            ]
        },
        PaymentProvider.SBER_QR: {
            "name": "Sberbank QR",
            "description": "QR-коды Сбербанка для платежей",
            "fields": [
                {"name": "merchant_id", "label": "ID мерчанта", "type": "text", "required": True},
                {"name": "api_key", "label": "API ключ", "type": "password", "required": True},
                {"name": "secret_key", "label": "Секретный ключ", "type": "password", "required": True},
                {"name": "api_url", "label": "URL API", "type": "text", "default": "https://api.sberbank.ru/ru/prod/"},
                {"name": "test_mode", "label": "Тестовый режим", "type": "boolean", "default": True}
            ]
        },
        PaymentProvider.PHONE_PAYMENT: {
            "name": "Оплата номером телефона",
            "description": "Платежи через мобильные операторы",
            "fields": [
                {"name": "provider_name", "label": "Оператор", "type": "text", "default": "MegaFon"},
                {"name": "api_key", "label": "API ключ", "type": "password", "required": True},
                {"name": "secret_key", "label": "Секретный ключ", "type": "password", "required": True},
                {"name": "api_url", "label": "URL API", "type": "text", "default": "https://api.megafon.ru/payment/"},
                {"name": "commission_rate", "label": "Комиссия (%)", "type": "number", "default": 0.03, "min": 0, "max": 0.5},
                {"name": "test_mode", "label": "Тестовый режим", "type": "boolean", "default": True}
            ]
        }
    }
    
    return providers

@router.get("/payment-methods/{config_id}")
async def get_payment_method(
    config_id: str,
    config_service: PaymentConfigService = Depends(get_payment_config_service),
    current_user: dict = Depends(get_current_admin_user)
):
    """Get specific payment method configuration"""
    
    try:
        config = await config_service.get_config(config_id)
        
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Платежный метод не найден"
            )
        
        # Return configuration with sensitive data masked
        masked_config = config.configuration.copy()
        for key, value in masked_config.items():
            if 'key' in key.lower() or 'password' in key.lower():
                masked_config[key] = '*' * len(str(value))
        
        return {
            "id": config.id,
            "provider": config.provider,
            "name": config.name,
            "status": config.status,
            "configuration": masked_config,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "created_by": config.created_by
        }
        
    except Exception as e:
        logger.error(f"Error getting payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения платежного метода"
        )