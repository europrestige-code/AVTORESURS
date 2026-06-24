import os
import asyncio
import aiohttp
import json
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CurrencyService:
    def __init__(self):
        # We'll use a free currency API for now, can be upgraded later
        self.base_url = "https://api.exchangerate-api.com/v4/latest/USD"
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 minutes
        
    async def get_usd_to_rub_rate(self) -> float:
        """Get USD to RUB exchange rate with -3 points risk coverage"""
        try:
            # Check cache first
            if self._is_cache_valid():
                return self.cache['rate']
            
            # Fetch fresh rate
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        base_rate = data['rates'].get('RUB', 95.0)  # Default fallback
                        
                        # Apply -3 points risk coverage as requested
                        adjusted_rate = base_rate - 3.0
                        
                        # Update cache
                        self.cache = {
                            'rate': adjusted_rate,
                            'timestamp': datetime.now(),
                            'original_rate': base_rate
                        }
                        
                        logger.info(f"Currency rate updated: {base_rate} -> {adjusted_rate} (with -3 risk coverage)")
                        return adjusted_rate
                    else:
                        raise Exception(f"Currency API returned {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching currency rate: {str(e)}")
            # Return cached rate if available, otherwise fallback
            if self.cache and 'rate' in self.cache:
                logger.warning("Using cached currency rate due to API error")
                return self.cache['rate']
            else:
                logger.warning("Using fallback currency rate: 94.0")
                return 94.0  # Fallback rate (97 - 3 risk coverage)
    
    def _is_cache_valid(self) -> bool:
        """Check if cached rate is still valid"""
        if not self.cache or 'timestamp' not in self.cache:
            return False
        
        age = datetime.now() - self.cache['timestamp']
        return age < self.cache_duration
    
    async def calculate_price_breakdown(self, price_usd: float, 
                                      shipping_usd: float = 0.0,
                                      customs_percent: float = 0.15) -> Dict[str, float]:
        """Calculate complete price breakdown in RUB"""
        try:
            rate = await self.get_usd_to_rub_rate()
            
            # Convert base prices
            original_price_rub = price_usd * rate
            shipping_rub = shipping_usd * rate
            
            # Calculate commission (18% or minimum 1500 RUB)
            commission_rub = max(original_price_rub * 0.18, 1500.0)
            
            # Calculate customs (15% of product value, not on shipping)
            customs_rub = original_price_rub * customs_percent
            
            # Calculate insurance (5% of total product + commission)
            insurance_base = original_price_rub + commission_rub
            insurance_rub = insurance_base * 0.05
            
            # Total calculation
            total_rub = original_price_rub + commission_rub + shipping_rub + customs_rub + insurance_rub
            
            return {
                'original_price_rub': round(original_price_rub, 2),
                'commission_rub': round(commission_rub, 2),
                'shipping_rub': round(shipping_rub, 2),
                'customs_rub': round(customs_rub, 2),
                'insurance_rub': round(insurance_rub, 2),
                'total_rub': round(total_rub, 2),
                'exchange_rate': rate,
                'original_price_usd': price_usd,
                'shipping_usd': shipping_usd
            }
            
        except Exception as e:
            logger.error(f"Error calculating price breakdown: {str(e)}")
            raise Exception(f"Ошибка расчёта стоимости: {str(e)}")
    
    def format_price_rub(self, amount: float) -> str:
        """Format price in Russian locale"""
        return f"{int(amount):,}".replace(',', ' ')
    
    async def get_rate_info(self) -> Dict[str, any]:
        """Get current rate information for debugging"""
        rate = await self.get_usd_to_rub_rate()
        return {
            'current_rate': rate,
            'original_rate': self.cache.get('original_rate', 'Unknown'),
            'last_updated': self.cache.get('timestamp', 'Never').isoformat() if self.cache.get('timestamp') else 'Never',
            'cache_valid': self._is_cache_valid()
        }