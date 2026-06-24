"""
Customer Payment Routes

API endpoints for customer payment management including:
- Payment method management (add, remove, set default)
- Payment history
- Payment processing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from models.user import PaymentMethod, PaymentMethodType, PaymentHistory
from services.customer_payment_service import CustomerPaymentService
# Database dependency - will be injected from main app
async def get_db():
    from server import db
    return db
from utils.auth import get_current_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customer/payment", tags=["customer-payment"])
security = HTTPBearer()

# Pydantic models for requests
class AddPaymentMethodRequest(BaseModel):
    type: PaymentMethodType
    display_name: str
    is_default: bool = False
    card_mask: str = None
    card_holder_name: str = None
    phone_number: str = None
    bank_name: str = None

class ProcessPaymentRequest(BaseModel):
    payment_method_id: str
    amount: float
    order_id: str = None
    description: str = None

class SetDefaultMethodRequest(BaseModel):
    method_id: str

@router.get("/methods", response_model=List[PaymentMethod])
async def get_payment_methods(
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get all payment methods for the current user"""
    try:
        service = CustomerPaymentService(db)
        methods = await service.get_user_payment_methods(current_user["id"])
        
        # If user has no payment methods, create default T-Bank QR
        if not methods:
            default_method = await service.add_payment_method(current_user["id"], {
                "type": PaymentMethodType.TBANK_QR,
                "display_name": "T-Bank QR (по умолчанию)",
                "is_default": True,
                "bank_name": "Т-Банк"
            })
            if default_method:
                methods = [default_method]
        
        return methods
        
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения способов оплаты"
        )

@router.post("/methods", response_model=PaymentMethod)
async def add_payment_method(
    request: AddPaymentMethodRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Add a new payment method"""
    try:
        service = CustomerPaymentService(db)
        
        method = await service.add_payment_method(
            current_user["id"],
            request.dict()
        )
        
        if not method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не удалось добавить способ оплаты"
            )
        
        return method
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка добавления способа оплаты"
        )

@router.delete("/methods/{method_id}")
async def remove_payment_method(
    method_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Remove a payment method"""
    try:
        service = CustomerPaymentService(db)
        
        success = await service.remove_payment_method(current_user["id"], method_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Способ оплаты не найден"
            )
        
        return {"success": True, "message": "Способ оплаты удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления способа оплаты"
        )

@router.put("/methods/default")
async def set_default_payment_method(
    request: SetDefaultMethodRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Set a payment method as default"""
    try:
        service = CustomerPaymentService(db)
        
        success = await service.set_default_payment_method(
            current_user["id"], 
            request.method_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Способ оплаты не найден"
            )
        
        return {"success": True, "message": "Способ оплаты по умолчанию установлен"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка установки способа оплаты по умолчанию"
        )

@router.get("/history", response_model=List[PaymentHistory])
async def get_payment_history(
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get payment history for the current user"""
    try:
        service = CustomerPaymentService(db)
        history = await service.get_payment_history(
            current_user["id"], 
            limit=limit, 
            skip=skip
        )
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting payment history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории платежей"
        )

@router.post("/process")
async def process_payment(
    request: ProcessPaymentRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Process a payment"""
    try:
        service = CustomerPaymentService(db)
        
        payment_data = request.dict()
        payment_data["user_id"] = current_user["id"]
        
        result = await service.process_payment(current_user["id"], payment_data)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Ошибка обработки платежа")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обработки платежа"
        )

@router.get("/methods/default", response_model=PaymentMethod)
async def get_default_payment_method(
    current_user: dict = Depends(get_current_user_from_token),
    db = Depends(get_db)
):
    """Get the user's default payment method"""
    try:
        service = CustomerPaymentService(db)
        method = await service.get_default_payment_method(current_user["id"])
        
        if not method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Способ оплаты по умолчанию не найден"
            )
        
        return method
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting default payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения способа оплаты по умолчанию"
        )

@router.get("/methods/available")
async def get_available_payment_methods():
    """Get list of available payment method types with descriptions"""
    try:
        return {
            "success": True,
            "methods": [
                {
                    "type": PaymentMethodType.TBANK_QR,
                    "name": "T-Bank QR",
                    "description": "Оплата через QR-код в приложении Т-Банк",
                    "icon": "qr_code",
                    "is_default": True,
                    "supported": True
                },
                {
                    "type": PaymentMethodType.SBER_QR,
                    "name": "Сбер QR",
                    "description": "Оплата через QR-код в приложении СберБанк",
                    "icon": "qr_code",
                    "is_default": False,
                    "supported": True
                },
                {
                    "type": PaymentMethodType.MIR_CARD,
                    "name": "Карта МИР",
                    "description": "Оплата картой платежной системы МИР",
                    "icon": "credit_card",
                    "is_default": False,
                    "supported": True
                },
                {
                    "type": PaymentMethodType.SBP,
                    "name": "СБП",
                    "description": "Система быстрых платежей по номеру телефона",
                    "icon": "smartphone",
                    "is_default": False,
                    "supported": True
                },
                {
                    "type": PaymentMethodType.PHONE_PAYMENT,
                    "name": "Оплата с телефона",
                    "description": "Списание с баланса мобильного телефона",
                    "icon": "phone",
                    "is_default": False,
                    "supported": True
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting available payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения доступных способов оплаты"
        )