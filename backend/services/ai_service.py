import os
import asyncio
import json
import base64
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY', 'sk-emergent-f5a879eA455CdD819C')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
    
    async def analyze_product_from_url(self, url: str) -> Dict[str, Any]:
        """Analyze product from URL and extract details"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"url_analysis_{hash(url)}",
                system_message="""Вы - эксперт по анализу товаров в интернет-магазинах. 
                Проанализируйте URL и извлеките информацию о товаре.
                Верните ответ ТОЛЬКО в формате JSON без дополнительного текста:
                {
                    "product_name": "Точное название товара",
                    "brand": "Бренд",
                    "category": "Категория товара",
                    "estimated_price_usd": 999.99,
                    "store_name": "Название магазина",
                    "description": "Краткое описание товара",
                    "availability": "В наличии/Нет в наличии",
                    "confidence": 0.85
                }"""
            ).with_model("openai", "gpt-4o-mini")
            
            user_message = UserMessage(
                text=f"Проанализируйте этот URL товара и извлеките информацию: {url}"
            )
            
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback if response is not pure JSON
                return {
                    "product_name": "Товар из URL",
                    "brand": "Unknown",
                    "category": "General",
                    "estimated_price_usd": 50.0,
                    "store_name": "Интернет-магазин",
                    "description": "Товар определён по URL",
                    "availability": "Уточняется",
                    "confidence": 0.6
                }
                
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {str(e)}")
            raise Exception(f"Ошибка анализа URL: {str(e)}")
    
    async def analyze_product_from_photo(self, image_base64: str) -> Dict[str, Any]:
        """Analyze product from photo and identify it"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"photo_analysis_{hash(image_base64[:100])}",
                system_message="""Вы - эксперт по определению товаров по фотографиям.
                Проанализируйте изображение и определите товар.
                Верните ответ ТОЛЬКО в формате JSON без дополнительного текста:
                {
                    "product_name": "Точное название товара",
                    "brand": "Бренд (если видно)",
                    "category": "Категория товара", 
                    "estimated_price_usd": 999.99,
                    "description": "Подробное описание товара с характеристиками",
                    "confidence": 0.85,
                    "search_keywords": ["ключевое", "слово", "для", "поиска"]
                }"""
            ).with_model("openai", "gpt-4o-mini")
            
            # Create image content
            image_content = ImageContent(image_base64=image_base64)
            
            user_message = UserMessage(
                text="Определите товар на изображении и предоставьте детальную информацию для поиска в интернет-магазинах.",
                file_contents=[image_content]
            )
            
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return {
                    "product_name": "Товар с фото",
                    "brand": "Unknown",
                    "category": "General",
                    "estimated_price_usd": 30.0,
                    "description": "Товар определён по фотографии",
                    "confidence": 0.6,
                    "search_keywords": ["товар", "фото"]
                }
                
        except Exception as e:
            logger.error(f"Error analyzing photo: {str(e)}")
            raise Exception(f"Ошибка анализа фото: {str(e)}")
    
    async def find_best_price(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Find best price and store for the product"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"price_search_{hash(str(product_info))}",
                system_message="""Вы - эксперт по поиску лучших цен на товары в зарубежных интернет-магазинах.
                Найдите лучшие варианты покупки товара.
                Верните ответ ТОЛЬКО в формате JSON без дополнительного текста:
                {
                    "best_stores": [
                        {
                            "store_name": "Amazon",
                            "price_usd": 999.99,
                            "url": "https://amazon.com/product",
                            "shipping_to_russia": true,
                            "rating": 4.5
                        }
                    ],
                    "cheapest_option": {
                        "store_name": "Best Store",
                        "price_usd": 899.99,
                        "url": "https://beststore.com/product"
                    },
                    "average_price_usd": 950.00,
                    "confidence": 0.90
                }"""
            ).with_model("openai", "gpt-4o-mini")
            
            product_query = f"""
            Товар: {product_info.get('product_name', 'Unknown')}
            Бренд: {product_info.get('brand', 'Unknown')}
            Категория: {product_info.get('category', 'Unknown')}
            Описание: {product_info.get('description', '')}
            
            Найдите лучшие варианты покупки этого товара в зарубежных магазинах (Amazon, eBay, официальные сайты брендов и т.д.)
            """
            
            user_message = UserMessage(text=product_query)
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback response
                return {
                    "best_stores": [
                        {
                            "store_name": "Amazon",
                            "price_usd": product_info.get('estimated_price_usd', 50.0),
                            "url": "https://amazon.com",
                            "shipping_to_russia": True,
                            "rating": 4.3
                        }
                    ],
                    "cheapest_option": {
                        "store_name": "Amazon",
                        "price_usd": product_info.get('estimated_price_usd', 50.0),
                        "url": "https://amazon.com"
                    },
                    "average_price_usd": product_info.get('estimated_price_usd', 50.0),
                    "confidence": 0.7
                }
                
        except Exception as e:
            logger.error(f"Error finding best price: {str(e)}")
            raise Exception(f"Ошибка поиска цен: {str(e)}")
    
    async def analyze_manual_input(self, product_name: str, model: str = "", 
                                 serial_number: str = "", description: str = "") -> Dict[str, Any]:
        """Analyze manually entered product information"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"manual_analysis_{hash(product_name)}",
                system_message="""Вы - эксперт по товарам. Проанализируйте введённую информацию о товаре.
                Верните ответ ТОЛЬКО в формате JSON без дополнительного текста:
                {
                    "product_name": "Полное название товара",
                    "brand": "Бренд",
                    "category": "Категория",
                    "estimated_price_usd": 999.99,
                    "description": "Подробное описание товара",
                    "specifications": "Технические характеристики",
                    "confidence": 0.85
                }"""
            ).with_model("openai", "gpt-4o-mini")
            
            product_query = f"""
            Название товара: {product_name}
            Модель: {model}
            Серийный номер/Артикул: {serial_number}
            Дополнительное описание: {description}
            
            Проанализируйте эту информацию и дополните детали о товаре.
            """
            
            user_message = UserMessage(text=product_query)
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                return {
                    "product_name": product_name,
                    "brand": "Unknown",
                    "category": "General",
                    "estimated_price_usd": 100.0,
                    "description": f"{product_name} {model} {description}".strip(),
                    "specifications": f"Модель: {model}, Артикул: {serial_number}",
                    "confidence": 0.7
                }
                
        except Exception as e:
            logger.error(f"Error analyzing manual input: {str(e)}")
            raise Exception(f"Ошибка анализа данных: {str(e)}")