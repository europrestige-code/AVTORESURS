import asyncio
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.payment_config import (
    PaymentProvider, PaymentProviderConfig, PaymentProviderStatus,
    UnitPayConfig, TBankQRConfig, SberQRConfig, PhonePaymentConfig,
    PaymentTestRequest, PaymentTestResponse
)

logger = logging.getLogger(__name__)

class PaymentConfigService:
    """Service for managing payment provider configurations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.payment_configs
        
    async def create_config(self, config_data: Dict[str, Any], created_by: str) -> PaymentProviderConfig:
        """Create new payment provider configuration"""
        
        # Validate configuration based on provider
        validated_config = await self._validate_provider_config(
            config_data['provider'], 
            config_data['configuration']
        )
        
        # Create configuration object
        config = PaymentProviderConfig(
            provider=config_data['provider'],
            name=config_data['name'],
            status=config_data.get('status', PaymentProviderStatus.INACTIVE),
            configuration=validated_config.dict(),
            created_by=created_by
        )
        
        # Save to database
        config_dict = config.dict()
        config_dict['created_at'] = config_dict['created_at'].isoformat()
        config_dict['updated_at'] = config_dict['updated_at'].isoformat()
        
        await self.collection.insert_one(config_dict)
        
        logger.info(f"Created payment configuration: {config.provider} - {config.name}")
        return config
    
    async def get_config(self, config_id: str) -> Optional[PaymentProviderConfig]:
        """Get payment configuration by ID"""
        
        config_data = await self.collection.find_one({"id": config_id})
        if not config_data:
            return None
        
        # Convert datetime strings back to datetime objects
        config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
        config_data['updated_at'] = datetime.fromisoformat(config_data['updated_at'])
        
        return PaymentProviderConfig(**config_data)
    
    async def get_configs_by_provider(self, provider: PaymentProvider) -> List[PaymentProviderConfig]:
        """Get all configurations for a specific provider"""
        
        configs = []
        async for config_data in self.collection.find({"provider": provider.value}):
            config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
            config_data['updated_at'] = datetime.fromisoformat(config_data['updated_at'])
            configs.append(PaymentProviderConfig(**config_data))
        
        return configs
    
    async def get_active_configs(self) -> List[PaymentProviderConfig]:
        """Get all active payment configurations"""
        
        configs = []
        async for config_data in self.collection.find({"status": PaymentProviderStatus.ACTIVE.value}):
            config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
            config_data['updated_at'] = datetime.fromisoformat(config_data['updated_at'])
            configs.append(PaymentProviderConfig(**config_data))
        
        return configs
    
    async def get_all_configs(self) -> List[PaymentProviderConfig]:
        """Get all payment configurations regardless of status"""
        
        configs = []
        async for config_data in self.collection.find({}):
            config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
            config_data['updated_at'] = datetime.fromisoformat(config_data['updated_at'])
            configs.append(PaymentProviderConfig(**config_data))
        
        return configs
    
    async def update_config(self, config_id: str, updates: Dict[str, Any]) -> Optional[PaymentProviderConfig]:
        """Update payment configuration"""
        
        # Validate configuration if it's being updated
        if 'configuration' in updates and 'provider' in updates:
            validated_config = await self._validate_provider_config(
                updates['provider'], 
                updates['configuration']
            )
            updates['configuration'] = validated_config.dict()
        
        updates['updated_at'] = datetime.utcnow().isoformat()
        
        result = await self.collection.update_one(
            {"id": config_id},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_config(config_id)
    
    async def delete_config(self, config_id: str) -> bool:
        """Delete payment configuration"""
        
        result = await self.collection.delete_one({"id": config_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted payment configuration: {config_id}")
            return True
        
        return False
    
    async def test_configuration(self, config_id: str, test_request: PaymentTestRequest) -> PaymentTestResponse:
        """Test payment configuration with mock transaction"""
        
        config = await self.get_config(config_id)
        if not config:
            return PaymentTestResponse(
                success=False,
                provider=test_request.provider,
                test_amount=test_request.amount,
                response_time_ms=0,
                message="Configuration not found"
            )
        
        start_time = time.time()
        
        try:
            # Test based on provider type
            if config.provider == PaymentProvider.UNITPAY:
                test_result = await self._test_unitpay_config(config, test_request.amount)
            elif config.provider == PaymentProvider.TBANK_QR:
                test_result = await self._test_tbank_config(config, test_request.amount)
            elif config.provider == PaymentProvider.SBER_QR:
                test_result = await self._test_sber_config(config, test_request.amount)
            elif config.provider == PaymentProvider.PHONE_PAYMENT:
                test_result = await self._test_phone_config(config, test_request.amount)
            else:
                test_result = {
                    "success": False,
                    "message": f"Testing not implemented for {config.provider}",
                    "test_data": None
                }
            
            response_time = (time.time() - start_time) * 1000
            
            return PaymentTestResponse(
                success=test_result["success"],
                provider=config.provider,
                test_amount=test_request.amount,
                response_time_ms=response_time,
                message=test_result["message"],
                test_data=test_result.get("test_data")
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Configuration test failed: {e}")
            
            return PaymentTestResponse(
                success=False,
                provider=config.provider,
                test_amount=test_request.amount,
                response_time_ms=response_time,
                message="Configuration test failed",
                error_details=str(e)
            )
    
    async def _validate_provider_config(self, provider: PaymentProvider, config_data: Dict[str, Any]):
        """Validate provider-specific configuration"""
        
        if provider == PaymentProvider.UNITPAY:
            return UnitPayConfig(**config_data)
        elif provider == PaymentProvider.TBANK_QR:
            return TBankQRConfig(**config_data)
        elif provider == PaymentProvider.SBER_QR:
            return SberQRConfig(**config_data)
        elif provider == PaymentProvider.PHONE_PAYMENT:
            return PhonePaymentConfig(**config_data)
        else:
            raise ValueError(f"Unknown payment provider: {provider}")
    
    async def _test_unitpay_config(self, config: PaymentProviderConfig, amount: float) -> Dict[str, Any]:
        """Test UnitPay configuration with mock API call"""
        
        unitpay_config = UnitPayConfig(**config.configuration)
        
        # Mock UnitPay API test - simulate API call patterns
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # In real implementation, this would make actual API calls to UnitPay test endpoints
        mock_response = {
            "success": True,
            "message": "UnitPay configuration test successful",
            "test_data": {
                "project_id": unitpay_config.project_id,
                "domain": unitpay_config.domain,
                "test_mode": unitpay_config.test_mode,
                "test_amount": amount,
                "mock_payment_url": f"https://{unitpay_config.domain}/pay/test_{int(time.time())}"
            }
        }
        
        return mock_response
    
    async def _test_tbank_config(self, config: PaymentProviderConfig, amount: float) -> Dict[str, Any]:
        """Test T-Bank configuration with mock API call"""
        
        tbank_config = TBankQRConfig(**config.configuration)
        
        # Mock T-Bank API test
        await asyncio.sleep(0.15)  # Simulate network delay
        
        mock_response = {
            "success": True,
            "message": "T-Bank QR configuration test successful",
            "test_data": {
                "terminal_id": tbank_config.terminal_id,
                "api_url": tbank_config.api_url,
                "test_mode": tbank_config.test_mode,
                "test_amount": amount,
                "mock_qr_data": f"https://www.tinkoff.ru/tpay/{int(time.time())}"
            }
        }
        
        return mock_response
    
    async def _test_sber_config(self, config: PaymentProviderConfig, amount: float) -> Dict[str, Any]:
        """Test Sberbank configuration with mock API call"""
        
        sber_config = SberQRConfig(**config.configuration)
        
        # Mock Sberbank API test
        await asyncio.sleep(0.12)  # Simulate network delay
        
        mock_response = {
            "success": True,
            "message": "Sberbank QR configuration test successful",
            "test_data": {
                "merchant_id": sber_config.merchant_id,
                "api_url": sber_config.api_url,
                "test_mode": sber_config.test_mode,
                "test_amount": amount,
                "mock_qr_url": f"https://api.sberbank.ru/qr/{int(time.time())}"
            }
        }
        
        return mock_response
    
    async def _test_phone_config(self, config: PaymentProviderConfig, amount: float) -> Dict[str, Any]:
        """Test phone payment configuration with mock API call"""
        
        phone_config = PhonePaymentConfig(**config.configuration)
        
        # Mock phone payment API test
        await asyncio.sleep(0.08)  # Simulate network delay
        
        commission = amount * phone_config.commission_rate
        total_amount = amount + commission
        
        mock_response = {
            "success": True,
            "message": "Phone payment configuration test successful",
            "test_data": {
                "provider_name": phone_config.provider_name,
                "api_url": phone_config.api_url,
                "test_mode": phone_config.test_mode,
                "test_amount": amount,
                "commission": commission,
                "total_amount": total_amount,
                "mock_payment_id": f"phone_{int(time.time())}"
            }
        }
        
        return mock_response