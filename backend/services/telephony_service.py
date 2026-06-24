"""
Main Telephony Service
Coordinates AI IP Telephony with Russian language support and provider abstraction
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
import uuid
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.telephony import (
    ProviderType, ProviderConfig, VirtualNumber, CallInfo, Agent, 
    RussianCity, CallStatus, CallDirection, WebhookEvent,
    CreateProviderConfigRequest, ProviderConfigResponse,
    PurchaseNumberRequest, MakeCallRequest, CallResponse,
    TelephonyDashboard, CallStatistics
)
from services.zadarma_service import ZadarmaService
from services.russian_language_service import RussianLanguageService
try:
    from emergentintegrations import LlmChat
except ImportError:
    # Mock LlmChat if not available
    class LlmChat:
        def __init__(self, api_key: str):
            self.api_key = api_key
        
        async def chat(self, prompt: str) -> object:
            class MockResponse:
                message = "Mock AI response for testing"
            return MockResponse()

class TelephonyProviderManager:
    """Manages multiple telephony providers with abstraction"""
    
    def __init__(self, redis_client, logger: logging.Logger):
        self.providers: Dict[str, Any] = {}
        self.active_provider: Optional[str] = None
        self.redis_client = redis_client
        self.logger = logger
    
    async def add_provider(self, config: ProviderConfig) -> bool:
        """Add a new telephony provider"""
        try:
            if config.provider_type == ProviderType.ZADARMA:
                creds = config.api_credentials
                service = ZadarmaService(
                    api_key=creds.get('api_key'),
                    api_secret=creds.get('api_secret'),
                    webhook_secret=creds.get('webhook_secret'),
                    logger=self.logger
                )
                
                # Test connection
                if await service.initialize():
                    self.providers[config.id] = {
                        'config': config,
                        'service': service,
                        'type': config.provider_type
                    }
                    
                    # Set as active if it's the first or highest priority
                    if not self.active_provider or config.priority < self.providers[self.active_provider]['config'].priority:
                        self.active_provider = config.id
                    
                    self.logger.info(f"Added provider {config.name} ({config.provider_type.value})")
                    return True
                else:
                    self.logger.error(f"Failed to initialize provider {config.name}")
                    return False
            
            else:
                self.logger.error(f"Unsupported provider type: {config.provider_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding provider {config.name}: {e}")
            return False
    
    async def get_active_provider(self) -> Optional[Any]:
        """Get the currently active provider service"""
        if self.active_provider and self.active_provider in self.providers:
            return self.providers[self.active_provider]['service']
        return None
    
    async def switch_provider(self, provider_id: str) -> bool:
        """Switch to a different provider"""
        if provider_id in self.providers:
            self.active_provider = provider_id
            self.logger.info(f"Switched to provider {provider_id}")
            return True
        return False
    
    def get_provider_configs(self) -> List[ProviderConfig]:
        """Get all provider configurations"""
        return [p['config'] for p in self.providers.values()]

class AITelephonyEngine:
    """AI engine for processing calls with Russian language support"""
    
    def __init__(self, emergent_key: str, logger: logging.Logger):
        self.emergent_key = emergent_key
        self.logger = logger
        self.russian_service = RussianLanguageService(emergent_key)
        self.ai_client = LlmChat(api_key=emergent_key)
        
        # Call routing configuration
        self.routing_number = "+79135533369"  # Default routing number
        
    async def process_inbound_call(
        self, 
        call_info: CallInfo, 
        transcript: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process inbound call with AI analysis"""
        
        try:
            # Identify caller city based on phone number
            caller_city = self._identify_caller_city(call_info.from_number)
            
            # Generate greeting
            greeting = self.russian_service.business_context.get_business_greeting_for_city(caller_city)
            
            if transcript:
                # Process customer speech
                analysis = await self.russian_service.process_customer_input(transcript, caller_city)
                
                # Determine if call should be transferred
                should_transfer = analysis['response']['transfer_to_operator']
                
                if should_transfer:
                    return {
                        'action': 'transfer_call',
                        'transfer_to': self.routing_number,
                        'message': analysis['response']['text'],
                        'analysis': analysis['analysis']
                    }
                else:
                    return {
                        'action': 'respond',
                        'message': analysis['response']['text'],
                        'continue_conversation': True,
                        'analysis': analysis['analysis']
                    }
            else:
                # Initial greeting
                return {
                    'action': 'respond',
                    'message': f"{greeting} Вас приветствует служба поддержки BuyAnywhere. Чем могу помочь?",
                    'continue_conversation': True
                }
                
        except Exception as e:
            self.logger.error(f"Error processing inbound call {call_info.call_id}: {e}")
            return {
                'action': 'transfer_call',
                'transfer_to': self.routing_number,
                'message': "Извините, произошла техническая ошибка. Соединяю с оператором.",
                'error': str(e)
            }
    
    async def generate_order_status_response(self, order_id: str) -> str:
        """Generate order status response using AI"""
        try:
            # This would typically query the order database
            # For now, we'll use the AI to generate a realistic response
            
            prompt = f"""
            Как русскоязычный оператор службы поддержки BuyAnywhere, предоставь информацию о статусе заказа {order_id}.
            Ответь как будто заказ уже отправлен и находится в пути.
            Включи трек-номер и ожидаемую дату доставки.
            Ответ должен быть вежливым и информативным, на русском языке.
            """
            
            response = await self.ai_client.chat(prompt)
            return response.message
            
        except Exception as e:
            self.logger.error(f"Error generating order status response: {e}")
            return f"Ваш заказ {order_id} обрабатывается. Подробную информацию можете уточнить у оператора."
    
    def _identify_caller_city(self, phone_number: str) -> RussianCity:
        """Identify caller's city based on phone number area code"""
        if phone_number.startswith("+7"):
            area_code = phone_number[2:5]
            
            city_mapping = {
                "495": RussianCity.MOSCOW,
                "499": RussianCity.MOSCOW, 
                "391": RussianCity.KRASNOYARSK,
                "423": RussianCity.VLADIVOSTOK
            }
            
            return city_mapping.get(area_code, RussianCity.MOSCOW)
        
        return RussianCity.MOSCOW  # Default

class TelephonyService:
    """Main telephony service coordinating all components"""
    
    def __init__(
        self, 
        database: AsyncIOMotorDatabase,
        redis_client=None,
        emergent_key: str = None
    ):
        self.db = database
        self.redis = redis_client
        self.emergent_key = emergent_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.provider_manager = TelephonyProviderManager(redis_client, self.logger)
        self.ai_engine = AITelephonyEngine(emergent_key, self.logger)
        
        # Collections
        self.providers_collection = database.telephony_providers
        self.numbers_collection = database.virtual_numbers
        self.calls_collection = database.calls
        self.agents_collection = database.agents
        self.webhooks_collection = database.webhook_events
    
    async def initialize(self) -> bool:
        """Initialize telephony service"""
        try:
            # Load existing provider configurations
            await self._load_providers()
            
            self.logger.info("Telephony service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize telephony service: {e}")
            return False
    
    async def _load_providers(self):
        """Load provider configurations from database"""
        try:
            async for provider_doc in self.providers_collection.find({"enabled": True}):
                config = ProviderConfig(**provider_doc)
                await self.provider_manager.add_provider(config)
                
        except Exception as e:
            self.logger.error(f"Error loading providers: {e}")
    
    # Provider Management
    async def create_provider_config(self, request: CreateProviderConfigRequest) -> ProviderConfigResponse:
        """Create new provider configuration"""
        try:
            config = ProviderConfig(
                provider_type=request.provider_type,
                name=request.name,
                api_credentials=request.api_credentials,
                webhook_url=request.webhook_url,
                enabled=request.enabled,
                priority=request.priority,
                features=request.features
            )
            
            # Add to provider manager
            if await self.provider_manager.add_provider(config):
                # Save to database
                await self.providers_collection.insert_one(config.model_dump())
                
                return ProviderConfigResponse(
                    success=True,
                    data=config,
                    message="Провайдер успешно настроен"
                )
            else:
                return ProviderConfigResponse(
                    success=False,
                    message="Не удалось настроить провайдера",
                    error="Provider initialization failed"
                )
                
        except Exception as e:
            self.logger.error(f"Error creating provider config: {e}")
            return ProviderConfigResponse(
                success=False,
                message="Ошибка при создании конфигурации провайдера",
                error=str(e)
            )
    
    async def test_provider_config(self, provider_id: str) -> Dict[str, Any]:
        """Test provider configuration"""
        try:
            if provider_id in self.provider_manager.providers:
                provider_service = self.provider_manager.providers[provider_id]['service']
                
                # Test connection
                is_initialized = await provider_service.initialize()
                
                return {
                    'success': is_initialized,
                    'message': 'Провайдер работает корректно' if is_initialized else 'Ошибка подключения к провайдеру',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    'success': False,
                    'message': 'Провайдер не найден',
                    'error': 'Provider not found'
                }
                
        except Exception as e:
            self.logger.error(f"Error testing provider {provider_id}: {e}")
            return {
                'success': False,
                'message': 'Ошибка при тестировании провайдера',
                'error': str(e)
            }
    
    # Virtual Number Management
    async def search_available_numbers(
        self, 
        city: RussianCity, 
        limit: int = 10
    ) -> List[VirtualNumber]:
        """Search for available virtual numbers"""
        try:
            provider_service = await self.provider_manager.get_active_provider()
            if not provider_service:
                self.logger.error("No active telephony provider")
                return []
            
            numbers = await provider_service.search_available_numbers(city, limit)
            return numbers
            
        except Exception as e:
            self.logger.error(f"Error searching numbers for {city}: {e}")
            return []
    
    async def purchase_virtual_number(self, request: PurchaseNumberRequest) -> CallResponse:
        """Purchase virtual number"""
        try:
            provider_service = await self.provider_manager.get_active_provider()
            if not provider_service:
                return CallResponse(
                    success=False,
                    message="Нет активного провайдера телефонии",
                    error="No active provider"
                )
            
            success, virtual_number, message = await provider_service.purchase_virtual_number(
                request.number, 
                request.city, 
                request.caller_name
            )
            
            if success and virtual_number:
                # Save to database
                await self.numbers_collection.insert_one(virtual_number.model_dump())
                
                return CallResponse(
                    success=True,
                    data=virtual_number,
                    message=message
                )
            else:
                return CallResponse(
                    success=False,
                    message=message or "Не удалось приобрести номер",
                    error="Purchase failed"
                )
                
        except Exception as e:
            self.logger.error(f"Error purchasing number {request.number}: {e}")
            return CallResponse(
                success=False,
                message="Ошибка при приобретении номера",
                error=str(e)
            )
    
    async def get_virtual_numbers(self, city: Optional[RussianCity] = None) -> List[VirtualNumber]:
        """Get virtual numbers, optionally filtered by city"""
        try:
            query = {"status": "active"}
            if city:
                query["city"] = city.value
            
            numbers = []
            async for number_doc in self.numbers_collection.find(query):
                numbers.append(VirtualNumber(**number_doc))
            
            return numbers
            
        except Exception as e:
            self.logger.error(f"Error getting virtual numbers: {e}")
            return []
    
    # Call Management
    async def handle_inbound_call(
        self, 
        from_number: str, 
        to_number: str,
        provider_call_id: Optional[str] = None
    ) -> CallInfo:
        """Handle incoming call"""
        try:
            # Create call record
            call_info = CallInfo(
                call_id=f"call_{uuid.uuid4().hex[:8]}",
                provider_call_id=provider_call_id,
                provider_type=ProviderType.ZADARMA,  # Would be dynamic based on active provider
                direction=CallDirection.INBOUND,
                from_number=from_number,
                to_number=to_number,
                status=CallStatus.RINGING,
                created_at=datetime.now(timezone.utc)
            )
            
            # Save to database
            await self.calls_collection.insert_one(call_info.model_dump())
            
            # Process with AI
            ai_response = await self.ai_engine.process_inbound_call(call_info)
            
            # Update call with AI analysis
            call_info.ai_analysis = ai_response
            call_info.status = CallStatus.ANSWERED
            call_info.answered_at = datetime.now(timezone.utc)
            
            await self.calls_collection.update_one(
                {"call_id": call_info.call_id},
                {"$set": call_info.model_dump()}
            )
            
            self.logger.info(f"Handled inbound call {call_info.call_id}")
            return call_info
            
        except Exception as e:
            self.logger.error(f"Error handling inbound call from {from_number}: {e}")
            raise
    
    async def make_outbound_call(self, request: MakeCallRequest) -> CallResponse:
        """Make outbound call"""
        try:
            provider_service = await self.provider_manager.get_active_provider()
            if not provider_service:
                return CallResponse(
                    success=False,
                    message="Нет активного провайдера телефонии"
                )
            
            success, call_info, message = await provider_service.initiate_call(
                request.from_number,
                request.to_number,
                request.callback_url
            )
            
            if success and call_info:
                # Save to database
                await self.calls_collection.insert_one(call_info.model_dump())
                
                return CallResponse(
                    success=True,
                    data=call_info,
                    message=message
                )
            else:
                return CallResponse(
                    success=False,
                    message=message or "Не удалось инициировать звонок"
                )
                
        except Exception as e:
            self.logger.error(f"Error making outbound call: {e}")
            return CallResponse(
                success=False,
                message="Ошибка при инициации звонка",
                error=str(e)
            )
    
    # Webhook Processing
    async def process_webhook(self, provider_type: ProviderType, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming webhook from telephony provider"""
        try:
            if provider_type == ProviderType.ZADARMA:
                provider_service = await self.provider_manager.get_active_provider()
                if provider_service:
                    webhook_event = await provider_service.handle_webhook_event(webhook_data)
                    
                    if webhook_event:
                        # Save webhook event
                        await self.webhooks_collection.insert_one(webhook_event.model_dump())
                        
                        # Update call status if applicable
                        if webhook_event.call_id or webhook_event.pbx_call_id:
                            await self._update_call_from_webhook(webhook_event)
                        
                        self.logger.info(f"Processed webhook event {webhook_event.event_type}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error processing webhook: {e}")
            return False
    
    async def _update_call_from_webhook(self, webhook_event: WebhookEvent):
        """Update call information from webhook event"""
        try:
            query = {}
            if webhook_event.call_id:
                query["call_id"] = webhook_event.call_id
            elif webhook_event.pbx_call_id:
                query["provider_call_id"] = webhook_event.pbx_call_id
            
            if query:
                update_data = {}
                
                if webhook_event.event_type == "NOTIFY_END":
                    update_data["status"] = CallStatus.COMPLETED.value
                    update_data["ended_at"] = webhook_event.timestamp
                    if webhook_event.duration:
                        update_data["duration_seconds"] = webhook_event.duration
                
                if webhook_event.recording_url:
                    update_data["recording_url"] = webhook_event.recording_url
                
                if update_data:
                    await self.calls_collection.update_one(query, {"$set": update_data})
                    
        except Exception as e:
            self.logger.error(f"Error updating call from webhook: {e}")
    
    # Statistics and Dashboard
    async def get_telephony_dashboard(self) -> TelephonyDashboard:
        """Get telephony dashboard data"""
        try:
            # Get active calls count
            active_calls = await self.calls_collection.count_documents({
                "status": {"$in": [CallStatus.RINGING.value, CallStatus.ANSWERED.value]}
            })
            
            # Get virtual numbers count
            virtual_numbers = await self.numbers_collection.count_documents({"status": "active"})
            
            # Get active providers count
            active_providers = len([p for p in self.provider_manager.providers.values() if p['config'].enabled])
            
            # Get today's statistics
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_stats = await self._get_call_statistics(today_start, datetime.now(timezone.utc))
            
            # Get week statistics
            week_start = today_start - timedelta(days=7)
            week_stats = await self._get_call_statistics(week_start, datetime.now(timezone.utc))
            
            # Get month statistics
            month_start = today_start - timedelta(days=30)
            month_stats = await self._get_call_statistics(month_start, datetime.now(timezone.utc))
            
            # Get recent calls
            recent_calls = []
            async for call_doc in self.calls_collection.find().sort("created_at", -1).limit(10):
                recent_calls.append(CallInfo(**call_doc))
            
            return TelephonyDashboard(
                active_calls=active_calls,
                virtual_numbers=virtual_numbers,
                active_providers=active_providers,
                today_stats=today_stats,
                week_stats=week_stats,
                month_stats=month_stats,
                recent_calls=recent_calls
            )
            
        except Exception as e:
            self.logger.error(f"Error getting telephony dashboard: {e}")
            return TelephonyDashboard()
    
    async def _get_call_statistics(self, start_date: datetime, end_date: datetime) -> CallStatistics:
        """Get call statistics for date range"""
        try:
            # Build aggregation pipeline
            pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_calls": {"$sum": 1},
                        "answered_calls": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", CallStatus.ANSWERED.value]}, 1, 0]
                            }
                        },
                        "total_duration": {"$sum": "$duration_seconds"},
                        "total_cost": {"$sum": "$cost"}
                    }
                }
            ]
            
            result = await self.calls_collection.aggregate(pipeline).to_list(1)
            
            if result:
                data = result[0]
                total_calls = data.get("total_calls", 0)
                answered_calls = data.get("answered_calls", 0)
                
                return CallStatistics(
                    total_calls=total_calls,
                    answered_calls=answered_calls,
                    missed_calls=total_calls - answered_calls,
                    average_duration_seconds=data.get("total_duration", 0) / max(1, answered_calls),
                    total_duration_seconds=data.get("total_duration", 0),
                    answer_rate=answered_calls / max(1, total_calls) * 100,
                    cost_total=data.get("total_cost", 0.0),
                    period_start=start_date,
                    period_end=end_date
                )
            else:
                return CallStatistics(
                    period_start=start_date,
                    period_end=end_date
                )
                
        except Exception as e:
            self.logger.error(f"Error getting call statistics: {e}")
            return CallStatistics(
                period_start=start_date,
                period_end=end_date
            )