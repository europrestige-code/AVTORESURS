"""
Zadarma VoIP API Service
Handles integration with Zadarma telephony provider for Russian numbers
"""

import asyncio
import hashlib
import hmac
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode, quote
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timezone

from models.telephony import (
    ProviderType, CallStatus, CallDirection, NumberType, RussianCity,
    VirtualNumber, CallInfo, WebhookEvent, TelephonyError
)

@dataclass
class ZadarmaResponse:
    """Standardized response from Zadarma API"""
    status: str
    data: Dict[str, Any]
    headers: Dict[str, str]
    status_code: int
    success: bool

class ZadarmaAPIClient:
    """Asynchronous Zadarma API client with authentication and rate limiting"""
    
    # Russian cities configuration
    RUSSIAN_CITIES = {
        RussianCity.MOSCOW: {"area_codes": ["495", "499"], "country": "RU"},
        RussianCity.KRASNOYARSK: {"area_codes": ["391"], "country": "RU"},
        RussianCity.VLADIVOSTOK: {"area_codes": ["423"], "country": "RU"}
    }
    
    def __init__(
        self, 
        api_key: str, 
        api_secret: str, 
        base_url: str = "https://api.zadarma.com",
        logger: Optional[logging.Logger] = None
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logger or logging.getLogger(__name__)
        self.rate_limit_remaining = 100
        self.rate_limit_reset = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _generate_signature(self, method: str, path: str, params: Dict[str, Any]) -> str:
        """Generate API request signature for authentication"""
        # Sort parameters for consistent signature generation
        sorted_params = sorted(params.items()) if params else []
        query_string = urlencode(sorted_params, quote_via=quote)
        
        # Create signature string
        signature_string = f"{method.upper()}{path}{query_string}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        return signature
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> ZadarmaResponse:
        """Make authenticated API request to Zadarma"""
        if not self.session:
            await self.connect()
        
        # Rate limiting check
        if self.rate_limit_remaining <= 1 and time.time() < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time()
            self.logger.warning(f"Rate limit reached, waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
        
        # Prepare request parameters
        params = params or {}
        full_url = f"{self.base_url}{endpoint}"
        
        # Generate signature
        signature = self._generate_signature(method, endpoint, params)
        
        # Prepare headers
        headers = {
            'Authorization': f"{self.api_key}:{signature}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            # Make request
            async with self.session.request(
                method=method,
                url=full_url,
                params=params if method.upper() == 'GET' else None,
                data=data if method.upper() in ['POST', 'PUT'] else None,
                headers=headers
            ) as response:
                
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 100))
                self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                
                # Parse response
                response_data = await response.json()
                
                return ZadarmaResponse(
                    status=response_data.get('status', 'error'),
                    data=response_data,
                    headers=dict(response.headers),
                    status_code=response.status,
                    success=response_data.get('status') == 'success'
                )
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Zadarma API request failed: {e}")
            return ZadarmaResponse(
                status="error",
                data={"message": f"Connection error: {str(e)}"},
                headers={},
                status_code=0,
                success=False
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during Zadarma API request: {e}")
            return ZadarmaResponse(
                status="error",
                data={"message": f"Unexpected error: {str(e)}"},
                headers={},
                status_code=0,
                success=False
            )
    
    # API method implementations
    async def get_balance(self) -> ZadarmaResponse:
        """Get account balance"""
        return await self._make_request('GET', '/v1/info/balance/')
    
    async def get_countries(self) -> ZadarmaResponse:
        """Get available countries for virtual numbers"""
        return await self._make_request('GET', '/v1/direct_numbers/countries/')
    
    async def get_available_numbers(
        self, 
        city: RussianCity, 
        limit: int = 10
    ) -> List[VirtualNumber]:
        """Get available virtual numbers for specific Russian city"""
        city_config = self.RUSSIAN_CITIES.get(city)
        if not city_config:
            raise ValueError(f"Unsupported city: {city}")
        
        available_numbers = []
        
        for area_code in city_config["area_codes"]:
            try:
                params = {
                    'country': city_config["country"],
                    'city': area_code
                }
                response = await self._make_request('GET', '/v1/direct_numbers/available/', params=params)
                
                if response.success and "numbers" in response.data:
                    numbers_data = response.data["numbers"]
                    
                    for number_item in numbers_data:
                        if isinstance(number_item, dict):
                            number = number_item.get("number", "")
                            cost = number_item.get("cost", 0.0)
                        else:
                            number = str(number_item)
                            cost = 0.0
                        
                        if self._validate_russian_number(number):
                            formatted_number = self._format_russian_number(number)
                            
                            virtual_number = VirtualNumber(
                                number=formatted_number,
                                provider_type=ProviderType.ZADARMA,
                                country_code="7",
                                area_code=area_code,
                                city=city,
                                number_type=NumberType.LOCAL,
                                monthly_cost=float(cost),
                                currency="USD",
                                capabilities=["voice", "sms"],
                                status="available"
                            )
                            
                            available_numbers.append(virtual_number)
                
            except Exception as e:
                self.logger.error(f"Error fetching numbers for {city} area code {area_code}: {e}")
                continue
        
        return available_numbers[:limit]
    
    async def purchase_number(self, number: str) -> ZadarmaResponse:
        """Purchase a virtual phone number"""
        if not self._validate_russian_number(number):
            return ZadarmaResponse(
                status="error",
                data={"message": f"Invalid Russian phone number format: {number}"},
                headers={},
                status_code=400,
                success=False
            )
        
        formatted_number = self._format_russian_number(number)
        data = {'number': formatted_number}
        
        return await self._make_request('POST', '/v1/direct_numbers/order/', data=data)
    
    async def set_caller_name(self, number: str, name: str) -> ZadarmaResponse:
        """Set caller name for a virtual number"""
        data = {
            'number': number,
            'name': name
        }
        return await self._make_request('PUT', '/v1/direct_numbers/set_caller_name/', data=data)
    
    async def make_call(
        self, 
        from_number: str, 
        to_number: str, 
        callback_url: Optional[str] = None
    ) -> ZadarmaResponse:
        """Initiate outbound call"""
        data = {
            'from': from_number,
            'to': to_number
        }
        
        if callback_url:
            data['callback_url'] = callback_url
        
        return await self._make_request('POST', '/v1/request/callback/', data=data)
    
    async def hangup_call(self, call_id: str) -> ZadarmaResponse:
        """Hangup an active call"""
        data = {'pbx_call_id': call_id}
        return await self._make_request('POST', '/v1/pbx/hangup/', data=data)
    
    async def get_call_details(self, call_id: str) -> ZadarmaResponse:
        """Get call details"""
        params = {'pbx_call_id': call_id}
        return await self._make_request('GET', '/v1/statistics/pbx/', params=params)
    
    async def configure_webhook(self, webhook_url: str) -> ZadarmaResponse:
        """Configure webhook URL for receiving call events"""
        data = {'url': webhook_url}
        return await self._make_request('POST', '/v1/webhooks/call/', data=data)
    
    def _format_russian_number(self, number: str) -> str:
        """Format number according to Russian E.164 standard"""
        import re
        # Remove all non-digit characters
        clean_number = re.sub(r'\D', '', number)
        
        # Handle different input formats
        if clean_number.startswith('7'):
            return f"+{clean_number}"
        elif clean_number.startswith('8') and len(clean_number) == 11:
            return f"+7{clean_number[1:]}"
        elif len(clean_number) == 10:
            return f"+7{clean_number}"
        else:
            raise ValueError(f"Invalid Russian phone number format: {number}")
    
    def _validate_russian_number(self, number: str) -> bool:
        """Validate Russian phone number format"""
        try:
            formatted = self._format_russian_number(number)
            import re
            return bool(re.match(r'^\+7\d{10}$', formatted))
        except ValueError:
            return False
    
    def _extract_area_code(self, number: str) -> str:
        """Extract area code from Russian phone number"""
        formatted = self._format_russian_number(number)
        return formatted[2:5]  # Area code is typically 3 digits after +7
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Process incoming webhook data from Zadarma"""
        try:
            event_type = webhook_data.get('event', '')
            
            # Generate event ID for deduplication
            event_id = self._generate_event_id(webhook_data)
            
            # Create webhook event
            webhook_event = WebhookEvent(
                event_type=event_type,
                event_id=event_id,
                provider_type=ProviderType.ZADARMA,
                timestamp=datetime.now(timezone.utc),
                call_id=webhook_data.get('call_id'),
                pbx_call_id=webhook_data.get('pbx_call_id'),
                caller_id=webhook_data.get('caller_id'),
                destination=webhook_data.get('destination') or webhook_data.get('called_did'),
                duration=webhook_data.get('duration'),
                status=webhook_data.get('disposition'),
                recording_url=webhook_data.get('recording'),
                raw_data=webhook_data
            )
            
            return webhook_event
            
        except Exception as e:
            self.logger.error(f"Error processing Zadarma webhook data: {e}")
            return None
    
    def _generate_event_id(self, webhook_data: Dict[str, Any]) -> str:
        """Generate unique event ID for deduplication"""
        import json
        key_data = {
            "event": webhook_data.get("event"),
            "pbx_call_id": webhook_data.get("pbx_call_id"),
            "call_id": webhook_data.get("call_id"),
            "timestamp": webhook_data.get("call_start") or webhook_data.get("end_time")
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

class ZadarmaService:
    """High-level Zadarma service for Russian telephony operations"""
    
    def __init__(
        self, 
        api_key: str, 
        api_secret: str,
        webhook_secret: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.api_client = ZadarmaAPIClient(api_key, api_secret, logger=logger)
        self.webhook_secret = webhook_secret
        self.logger = logger or logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize service and test connection"""
        try:
            async with self.api_client as client:
                response = await client.get_balance()
                if response.success:
                    balance_info = response.data
                    self.logger.info(f"Zadarma service initialized. Balance: {balance_info}")
                    return True
                else:
                    self.logger.error(f"Failed to initialize Zadarma service: {response.data}")
                    return False
        except Exception as e:
            self.logger.error(f"Error initializing Zadarma service: {e}")
            return False
    
    async def search_available_numbers(
        self, 
        city: RussianCity, 
        limit: int = 10
    ) -> List[VirtualNumber]:
        """Search for available virtual numbers in Russian city"""
        try:
            async with self.api_client as client:
                return await client.get_available_numbers(city, limit)
        except Exception as e:
            self.logger.error(f"Error searching numbers for {city}: {e}")
            return []
    
    async def purchase_virtual_number(
        self, 
        number: str, 
        city: RussianCity,
        caller_name: Optional[str] = None
    ) -> Tuple[bool, Optional[VirtualNumber], Optional[str]]:
        """Purchase virtual number and configure it"""
        try:
            async with self.api_client as client:
                # Purchase number
                purchase_response = await client.purchase_number(number)
                
                if not purchase_response.success:
                    error_msg = purchase_response.data.get('message', 'Unknown error')
                    return False, None, f"Не удалось заказать номер: {error_msg}"
                
                # Extract area code
                area_code = client._extract_area_code(number)
                
                # Create VirtualNumber object
                virtual_number = VirtualNumber(
                    number=number,
                    provider_type=ProviderType.ZADARMA,
                    provider_number_id=purchase_response.data.get('number_id'),
                    country_code="7",
                    area_code=area_code,
                    city=city,
                    number_type=NumberType.LOCAL,
                    monthly_cost=purchase_response.data.get('cost', 0.0),
                    currency="USD",
                    capabilities=["voice", "sms"],
                    status="active",
                    activated_at=datetime.now(timezone.utc),
                    caller_name=caller_name
                )
                
                # Set caller name if provided
                if caller_name:
                    name_response = await client.set_caller_name(number, caller_name)
                    if not name_response.success:
                        self.logger.warning(f"Failed to set caller name for {number}: {name_response.data}")
                
                self.logger.info(f"Successfully purchased number {number} for {city.value}")
                return True, virtual_number, "Номер успешно заказан"
                
        except Exception as e:
            self.logger.error(f"Error purchasing number {number}: {e}")
            return False, None, f"Ошибка при заказе номера: {str(e)}"
    
    async def initiate_call(
        self,
        from_number: str,
        to_number: str,
        callback_url: Optional[str] = None
    ) -> Tuple[bool, Optional[CallInfo], Optional[str]]:
        """Initiate outbound call"""
        try:
            async with self.api_client as client:
                response = await client.make_call(from_number, to_number, callback_url)
                
                if response.success:
                    call_info = CallInfo(
                        call_id=f"zadarma_{int(time.time())}",
                        provider_call_id=response.data.get('call_id'),
                        provider_type=ProviderType.ZADARMA,
                        direction=CallDirection.OUTBOUND,
                        from_number=from_number,
                        to_number=to_number,
                        status=CallStatus.INITIATED,
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    return True, call_info, "Звонок инициирован"
                else:
                    error_msg = response.data.get('message', 'Unknown error')
                    return False, None, f"Не удалось инициировать звонок: {error_msg}"
                    
        except Exception as e:
            self.logger.error(f"Error initiating call from {from_number} to {to_number}: {e}")
            return False, None, f"Ошибка при инициации звонка: {str(e)}"
    
    async def end_call(self, call_id: str) -> Tuple[bool, Optional[str]]:
        """End active call"""
        try:
            async with self.api_client as client:
                response = await client.hangup_call(call_id)
                
                if response.success:
                    return True, "Звонок завершён"
                else:
                    error_msg = response.data.get('message', 'Unknown error')
                    return False, f"Не удалось завершить звонок: {error_msg}"
                    
        except Exception as e:
            self.logger.error(f"Error ending call {call_id}: {e}")
            return False, f"Ошибка при завершении звонка: {str(e)}"
    
    def verify_webhook_signature(self, request_body: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        if not self.webhook_secret:
            self.logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                request_body,
                hashlib.sha1
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def handle_webhook_event(self, webhook_data: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Handle incoming webhook event from Zadarma"""
        try:
            return self.api_client.process_webhook_data(webhook_data)
        except Exception as e:
            self.logger.error(f"Error handling webhook event: {e}")
            return None