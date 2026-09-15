"""
Customer Payment Service

This service handles customer payment methods, payment history, and payment processing
for the BuyAnywhere platform. It's structured to easily accommodate new payment methods
in the future without major code changes.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import uuid
import logging

from models.user import PaymentMethod, PaymentMethodType, PaymentHistory
# from services.payment_service import PaymentService  # Not needed for current implementation

logger = logging.getLogger(__name__)

class CustomerPaymentService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.payment_methods_collection = db.customer_payment_methods
        self.payment_history_collection = db.customer_payment_history
        # self.payment_service = PaymentService(db)  # Not needed for current implementation
    
    async def get_user_payment_methods(self, user_id: str) -> List[PaymentMethod]:
        """Get all active payment methods for a user"""
        try:
            cursor = self.payment_methods_collection.find({
                "user_id": user_id,
                "is_active": True
            }).sort("is_default", -1)  # Default methods first
            
            methods = []
            async for doc in cursor:
                # Remove MongoDB _id field, keep the UUID string id
                doc.pop("_id", None)
                # Ensure we have an id field (fallback to UUID if missing)
                if "id" not in doc:
                    doc["id"] = str(uuid.uuid4())
                methods.append(PaymentMethod(**doc))
            
            return methods
        except Exception as e:
            logger.error(f"Error getting payment methods for user {user_id}: {e}")
            return []
    
    async def add_payment_method(self, user_id: str, payment_data: Dict[str, Any]) -> Optional[PaymentMethod]:
        """Add a new payment method for a user"""
        try:
            # Create payment method
            payment_method = PaymentMethod(
                user_id=user_id,
                type=PaymentMethodType(payment_data["type"]),
                display_name=payment_data["display_name"],
                is_default=payment_data.get("is_default", False),
                card_mask=payment_data.get("card_mask"),
                card_holder_name=payment_data.get("card_holder_name"),
                phone_number=payment_data.get("phone_number"),
                bank_name=payment_data.get("bank_name")
            )
            
            # If this is set as default, remove default from other methods
            if payment_method.is_default:
                await self.payment_methods_collection.update_many(
                    {"user_id": user_id},
                    {"$set": {"is_default": False}}
                )
            
            # Insert into database
            method_dict = payment_method.dict()
            # Keep the UUID string as 'id' field, let MongoDB generate its own _id
            
            result = await self.payment_methods_collection.insert_one(method_dict)
            
            if result.inserted_id:
                # Keep the original UUID as the id
                logger.info(f"Added payment method {payment_method.id} for user {user_id}")
                return payment_method
            
            return None
            
        except Exception as e:
            logger.error(f"Error adding payment method for user {user_id}: {e}")
            return None
    
    async def remove_payment_method(self, user_id: str, method_id: str) -> bool:
        """Remove a payment method"""
        try:
            # Try to remove by UUID string id first, then by ObjectId
            result = await self.payment_methods_collection.delete_one({
                "id": method_id,
                "user_id": user_id
            })
            
            # If not found by UUID, try ObjectId (backward compatibility)
            if result.deleted_count == 0:
                try:
                    result = await self.payment_methods_collection.delete_one({
                        "_id": ObjectId(method_id),
                        "user_id": user_id
                    })
                except Exception:
                    pass
            
            if result and result.deleted_count > 0:
                logger.info(f"Removed payment method {method_id} for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing payment method {method_id} for user {user_id}: {e}")
            return False
    
    async def set_default_payment_method(self, user_id: str, method_id: str) -> bool:
        """Set a payment method as default"""
        try:
            # Remove default from all methods
            await self.payment_methods_collection.update_many(
                {"user_id": user_id},
                {"$set": {"is_default": False}}
            )
            
            # Set the specified method as default (try UUID first)
            result = await self.payment_methods_collection.update_one(
                {"id": method_id, "user_id": user_id},
                {"$set": {"is_default": True, "updated_at": datetime.now(timezone.utc)}}
            )
            
            # If not found by UUID, try ObjectId (backward compatibility)
            if result.modified_count == 0:
                try:
                    result = await self.payment_methods_collection.update_one(
                        {"_id": ObjectId(method_id), "user_id": user_id},
                        {"$set": {"is_default": True, "updated_at": datetime.now(timezone.utc)}}
                    )
                except Exception:
                    pass
            
            if result.modified_count > 0:
                logger.info(f"Set payment method {method_id} as default for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting default payment method {method_id} for user {user_id}: {e}")
            return False
    
    async def get_payment_history(self, user_id: str, limit: int = 20, skip: int = 0) -> List[PaymentHistory]:
        """Get payment history for a user"""
        try:
            cursor = self.payment_history_collection.find({
                "user_id": user_id
            }).sort("created_at", -1).skip(skip).limit(limit)
            
            history = []
            async for doc in cursor:
                # Remove MongoDB _id field, keep the UUID string id
                doc.pop("_id", None)
                # Ensure we have an id field (fallback to UUID if missing)
                if "id" not in doc:
                    doc["id"] = str(uuid.uuid4())
                history.append(PaymentHistory(**doc))
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting payment history for user {user_id}: {e}")
            return []
    
    async def process_payment(self, user_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a payment using the user's selected payment method.
        This is the main entry point for payment processing.
        """
        try:
            payment_method_id = payment_data.get("payment_method_id")
            amount = payment_data.get("amount")
            order_id = payment_data.get("order_id")
            
            if not all([payment_method_id, amount]):
                return {
                    "success": False,
                    "error": "Отсутствуют обязательные данные для оплаты"
                }
            
            # Get payment method - use UUID string lookup first
            payment_method = None
            try:
                # Try to find by UUID string id first (this is our primary method)
                method_doc = await self.payment_methods_collection.find_one({
                    "id": payment_method_id,
                    "user_id": user_id,
                    "is_active": True
                })
                
                if method_doc:
                    # Remove MongoDB _id field for JSON serialization
                    method_doc.pop("_id", None)
                    payment_method = PaymentMethod(**method_doc)
                else:
                    # Fallback: try to find by ObjectId (for backward compatibility)
                    try:
                        method_doc = await self.payment_methods_collection.find_one({
                            "_id": ObjectId(payment_method_id),
                            "user_id": user_id,
                            "is_active": True
                        })
                        if method_doc:
                            method_doc["id"] = str(method_doc.pop("_id"))
                            payment_method = PaymentMethod(**method_doc)
                    except Exception:
                        # ObjectId conversion failed, payment method not found
                        pass
                
            except Exception as e:
                logger.error(f"Error getting payment method {payment_method_id}: {e}")
            
            if not payment_method:
                logger.error(f"Payment method {payment_method_id} not found for user {user_id}")
                return {
                    "success": False,
                    "error": "Способ оплаты не найден"
                }
            
            # Create payment history record
            payment_history = PaymentHistory(
                user_id=user_id,
                order_id=order_id,
                payment_method_id=payment_method_id,
                amount=amount,
                currency="RUB",
                status="pending",
                payment_type=payment_method.type,
                description=payment_data.get("description", "Оплата заказа")
            )
            
            # Save payment history (keep UUID as id field)
            history_dict = payment_history.dict()
            
            history_result = await self.payment_history_collection.insert_one(history_dict)
            # Keep the original UUID as the id
            
            # Process payment based on method type
            payment_result = await self._process_payment_by_type(
                payment_method, amount, payment_history.id, payment_data
            )
            
            # Update payment history with result (use UUID string id)
            try:
                await self.payment_history_collection.update_one(
                    {"id": payment_history.id},
                    {
                        "$set": {
                            "status": payment_result.get("status", "failed"),
                            "transaction_id": payment_result.get("transaction_id"),
                            "payment_provider": payment_result.get("provider"),
                            "provider_response": payment_result.get("provider_response"),
                            "completed_at": datetime.now(timezone.utc) if payment_result.get("success") else None
                        }
                    }
                )
            except Exception as e:
                logger.error(f"Error updating payment history {payment_history.id}: {e}")
            
            return {
                "success": payment_result.get("success", False),
                "payment_id": payment_history.id,
                "transaction_id": payment_result.get("transaction_id"),
                "status": payment_result.get("status"),
                "payment_instructions": payment_result.get("payment_instructions"),
                "qr_code": payment_result.get("qr_code"),
                "error": payment_result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error processing payment for user {user_id}: {e}")
            return {
                "success": False,
                "error": "Ошибка обработки платежа"
            }
    
    async def _process_payment_by_type(self, payment_method: PaymentMethod, amount: float, 
                                     payment_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment based on the payment method type"""
        
        if payment_method.type == PaymentMethodType.TBANK_QR:
            return await self._process_tbank_qr_payment(amount, payment_id, payment_data)
        
        elif payment_method.type == PaymentMethodType.SBER_QR:
            return await self._process_sber_qr_payment(amount, payment_id, payment_data)
        
        elif payment_method.type == PaymentMethodType.MIR_CARD:
            return await self._process_mir_card_payment(amount, payment_id, payment_data)
        
        elif payment_method.type == PaymentMethodType.PHONE_PAYMENT:
            return await self._process_phone_payment(amount, payment_id, payment_method.phone_number, payment_data)
        
        elif payment_method.type == PaymentMethodType.SBP:
            return await self._process_sbp_payment(amount, payment_id, payment_method.phone_number, payment_data)
        
        else:
            return {
                "success": False,
                "error": "Неподдерживаемый способ оплаты"
            }
    
    async def _process_tbank_qr_payment(self, amount: float, payment_id: str, payment_data: Dict) -> Dict[str, Any]:
        """Process T-Bank QR payment (default payment method)"""
        try:
            # This would integrate with actual T-Bank API
            # For now, return mock successful response
            return {
                "success": True,
                "status": "pending",
                "transaction_id": f"TBANK_{payment_id}_{uuid.uuid4().hex[:8].upper()}",
                "provider": "T-Bank",
                "payment_instructions": {
                    "type": "qr_code",
                    "message": "Отсканируйте QR-код в приложении Т-Банк для оплаты",
                    "amount": amount,
                    "currency": "RUB"
                },
                "qr_code": f"data:image/png;base64,mock_qr_code_for_amount_{amount}_rub",
                "provider_response": {
                    "mock": True,
                    "amount": amount,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error processing T-Bank QR payment: {e}")
            return {
                "success": False,
                "error": "Ошибка создания QR-кода T-Bank"
            }
    
    async def _process_sber_qr_payment(self, amount: float, payment_id: str, payment_data: Dict) -> Dict[str, Any]:
        """Process Sber QR payment"""
        try:
            return {
                "success": True,
                "status": "pending",
                "transaction_id": f"SBER_{payment_id}_{uuid.uuid4().hex[:8].upper()}",
                "provider": "Sberbank",
                "payment_instructions": {
                    "type": "qr_code",
                    "message": "Отсканируйте QR-код в приложении СберБанк для оплаты",
                    "amount": amount,
                    "currency": "RUB"
                },
                "qr_code": f"data:image/png;base64,mock_sber_qr_code_for_amount_{amount}_rub",
                "provider_response": {
                    "mock": True,
                    "amount": amount,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error processing Sber QR payment: {e}")
            return {
                "success": False,
                "error": "Ошибка создания QR-кода СберБанк"
            }
    
    async def _process_mir_card_payment(self, amount: float, payment_id: str, payment_data: Dict) -> Dict[str, Any]:
        """Process MIR card payment"""
        try:
            return {
                "success": True,
                "status": "pending",
                "transaction_id": f"MIR_{payment_id}_{uuid.uuid4().hex[:8].upper()}",
                "provider": "MIR/UnitPay",
                "payment_instructions": {
                    "type": "card_form",
                    "message": "Введите данные карты МИР для оплаты",
                    "amount": amount,
                    "currency": "RUB",
                    "form_url": f"/payment/mir/{payment_id}"
                },
                "provider_response": {
                    "mock": True,
                    "amount": amount,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error processing MIR card payment: {e}")
            return {
                "success": False,
                "error": "Ошибка обработки платежа картой МИР"
            }
    
    async def _process_phone_payment(self, amount: float, payment_id: str, phone: str, payment_data: Dict) -> Dict[str, Any]:
        """Process phone payment"""
        try:
            return {
                "success": True,
                "status": "pending",
                "transaction_id": f"PHONE_{payment_id}_{uuid.uuid4().hex[:8].upper()}",
                "provider": "Phone Payment",
                "payment_instructions": {
                    "type": "phone_payment",
                    "message": f"Платеж будет списан с номера {phone}",
                    "amount": amount,
                    "currency": "RUB",
                    "confirmation_required": True
                },
                "provider_response": {
                    "mock": True,
                    "phone": phone,
                    "amount": amount,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error processing phone payment: {e}")
            return {
                "success": False,
                "error": "Ошибка обработки платежа с телефона"
            }
    
    async def _process_sbp_payment(self, amount: float, payment_id: str, phone: str, payment_data: Dict) -> Dict[str, Any]:
        """Process SBP (Faster Payment System) payment"""
        try:
            return {
                "success": True,
                "status": "pending",
                "transaction_id": f"SBP_{payment_id}_{uuid.uuid4().hex[:8].upper()}",
                "provider": "СБП",
                "payment_instructions": {
                    "type": "sbp",
                    "message": f"Оплата через СБП с номера {phone}",
                    "amount": amount,
                    "currency": "RUB",
                    "phone": phone
                },
                "provider_response": {
                    "mock": True,
                    "phone": phone,
                    "amount": amount,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error processing SBP payment: {e}")
            return {
                "success": False,
                "error": "Ошибка обработки платежа через СБП"
            }
    
    async def get_default_payment_method(self, user_id: str) -> Optional[PaymentMethod]:
        """Get user's default payment method, or T-Bank QR if none set"""
        try:
            # Try to get user's default method
            method_doc = await self.payment_methods_collection.find_one({
                "user_id": user_id,
                "is_default": True,
                "is_active": True
            })
            
            if method_doc:
                method_doc.pop("_id", None)
                return PaymentMethod(**method_doc)
            
            # If no default method, try to get T-Bank QR method
            method_doc = await self.payment_methods_collection.find_one({
                "user_id": user_id,
                "type": PaymentMethodType.TBANK_QR,
                "is_active": True
            })
            
            if method_doc:
                method_doc.pop("_id", None)
                return PaymentMethod(**method_doc)
            
            # If no T-Bank QR, create a default one
            default_method = await self.add_payment_method(user_id, {
                "type": PaymentMethodType.TBANK_QR,
                "display_name": "T-Bank QR (по умолчанию)",
                "is_default": True,
                "bank_name": "Т-Банк"
            })
            
            return default_method
            
        except Exception as e:
            logger.error(f"Error getting default payment method for user {user_id}: {e}")
            return None