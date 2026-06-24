import os
import logging
from typing import Dict, List, Any, Optional
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class AISearchService:
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        logger.info("Initialized AI Search Service with Emergent LLM")

    async def search_chinese_platforms(self, query: str, platform: str = None) -> Dict[str, Any]:
        """AI-powered search for Chinese platforms with product analysis."""
        try:
            platform_context = ""
            if platform:
                platform_contexts = {
                    "aliexpress": "AliExpress - глобальная торговая площадка с защитой покупателя",
                    "taobao": "Taobao - крупнейшая китайская платформа с эксклюзивными товарами",
                    "shein": "SHEIN - быстрая мода и доступная одежда",
                    "jd": "JD.com - премиальная площадка с официальными брендами",
                    "tmall": "Tmall - официальные магазины люксовых брендов",
                    "1688": "1688.com - оптовая торговая B2B площадка"
                }
                platform_context = platform_contexts.get(platform.lower(), "")

            prompt = f"""
            Ты эксперт по китайским торговым площадкам. Пользователь ищет: "{query}"
            {f"Платформа: {platform_context}" if platform_context else "Поиск по всем платформам"}
            
            Проанализируй запрос и предоставь:
            1. Рекомендуемые товары с описанием
            2. Примерные цены в юанях и рублях
            3. Лучшие платформы для этого товара
            4. Советы по выбору и покупке
            5. Возможные подводные камни
            
            Отвечай на русском языке в формате JSON:
            {{
                "products": [
                    {{
                        "name": "название товара",
                        "description": "подробное описание", 
                        "price_yuan": "цена в юанях",
                        "price_rub": "цена в рублях",
                        "platform": "рекомендуемая платформа",
                        "rating": "рейтинг 1-5",
                        "pros": ["плюсы"],
                        "cons": ["минусы"]
                    }}
                ],
                "recommendations": "общие рекомендации",
                "warnings": "предупреждения и советы"
            }}
            """

            # Create LlmChat instance for this request
            llm_chat = LlmChat(
                api_key=self.api_key,
                session_id=f"chinese_search_{hash(query)}",
                system_message="Ты эксперт по китайским торговым площадкам и помогаешь пользователям найти лучшие товары."
            )
            
            user_message = UserMessage(text=prompt)
            response = await llm_chat.send_message(user_message)
            
            return {
                "success": True,
                "query": query,
                "platform": platform,
                "ai_analysis": response,
                "search_type": "chinese_platforms"
            }

        except Exception as e:
            logger.error(f"Chinese platforms search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    async def search_car_parts(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered car parts search with OEM manufacturer identification."""
        try:
            search_type = search_data.get("type", "description")
            
            if search_type == "vin":
                prompt = f"""
                Ты эксперт по автозапчастям и VIN-кодам. VIN номер: {search_data.get('vin', '')}
                
                Проанализируй VIN и определи:
                1. Марку, модель, год выпуска автомобиля
                2. Тип двигателя и трансмиссии
                3. Основные расходные запчасти для этого авто
                4. OEM производителей для каждой категории деталей
                5. Примерные цены на популярные запчасти
                
                Ответь в формате JSON на русском языке:
                {{
                    "vehicle_info": {{
                        "make": "марка",
                        "model": "модель", 
                        "year": "год",
                        "engine": "двигатель",
                        "transmission": "трансмиссия"
                    }},
                    "common_parts": [
                        {{
                            "part_name": "название детали",
                            "oem_manufacturer": "OEM производитель",
                            "part_number": "номер детали",
                            "price_range": "диапазон цен",
                            "replacement_interval": "интервал замены"
                        }}
                    ],
                    "recommendations": "рекомендации по обслуживанию"
                }}
                """
            
            elif search_type == "part_number":
                prompt = f"""
                Ты эксперт по автозапчастям. Номер детали: {search_data.get('part_number', '')}
                
                Определи:
                1. Что это за деталь
                2. Для каких автомобилей подходит
                3. Оригинального OEM производителя
                4. Аналоги от других производителей
                5. Примерную стоимость
                
                Ответь в формате JSON:
                {{
                    "part_info": {{
                        "name": "название детали",
                        "description": "описание функции",
                        "original_manufacturer": "оригинальный производитель",
                        "oem_manufacturer": "OEM производитель"
                    }},
                    "compatibility": ["список совместимых авто"],
                    "alternatives": [
                        {{
                            "manufacturer": "производитель",
                            "part_number": "номер",
                            "price": "цена",
                            "quality": "качество"
                        }}
                    ],
                    "buying_tips": "советы по покупке"
                }}
                """
            
            else:  # car details
                prompt = f"""
                Автомобиль: {search_data.get('year', '')} {search_data.get('make', '')} {search_data.get('model', '')} {search_data.get('variant', '')}
                
                Предоставь информацию о:
                1. Основных расходных материалах
                2. OEM производителях для каждой категории
                3. Рекомендуемых интервалах замены
                4. Примерных ценах на запчасти
                5. Проблемных узлах данной модели
                
                Формат ответа JSON:
                {{
                    "maintenance_schedule": [
                        {{
                            "part_category": "категория",
                            "parts": ["список деталей"],
                            "oem_manufacturers": ["OEM производители"],
                            "interval": "интервал замены",
                            "price_range": "диапазон цен"
                        }}
                    ],
                    "common_issues": ["типичные проблемы"],
                    "recommendations": "рекомендации по эксплуатации"
                }}
                """

            # Create LlmChat instance for this request
            llm_chat = LlmChat(
                api_key=self.api_key,
                session_id=f"car_parts_{hash(str(search_data))}",
                system_message="Ты эксперт по автозапчастям и OEM производителям. Помогаешь найти правильные детали для автомобилей."
            )
            
            user_message = UserMessage(text=prompt)
            response = await llm_chat.send_message(user_message)
            
            return {
                "success": True,
                "search_data": search_data,
                "ai_analysis": response,
                "search_type": "car_parts"
            }

        except Exception as e:
            logger.error(f"Car parts search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "search_data": search_data
            }

    async def search_business_equipment(self, query: str, category: str = None, image_description: str = None) -> Dict[str, Any]:
        """AI-powered business equipment search with brand identification."""
        try:
            category_context = ""
            if category:
                category_contexts = {
                    "automation": "Автоматизация и робототехника: ПЛК, роботы, датчики, приводы",
                    "electrical": "Электротехника: автоматика, УЗО, контакторы, щиты",
                    "pneumatics": "Пневматика: цилиндры, клапаны, компрессоры, фитинги", 
                    "machinery": "Станки и оборудование: ЧПУ, инструмент, тяжелая техника"
                }
                category_context = category_contexts.get(category, "")

            image_context = f"Описание загруженного изображения: {image_description}" if image_description else ""

            prompt = f"""
            Ты эксперт по промышленному оборудованию. 
            Запрос: "{query}"
            Категория: {category_context}
            {image_context}
            
            Проанализируй и предоставь:
            1. Подходящее оборудование с техническими характеристиками
            2. Ведущих производителей для каждого типа оборудования
            3. Примерные цены и сроки поставки
            4. Технические требования и совместимость
            5. Рекомендации по выбору поставщика
            
            Ответь в формате JSON:
            {{
                "equipment": [
                    {{
                        "name": "название оборудования",
                        "manufacturer": "производитель",
                        "model": "модель/серия",
                        "specifications": {{
                            "key_specs": "основные характеристики"
                        }},
                        "price_range": "диапазон цен",
                        "availability": "доступность",
                        "lead_time": "срок поставки"
                    }}
                ],
                "manufacturers": [
                    {{
                        "name": "название бренда",
                        "country": "страна",
                        "specialization": "специализация",
                        "reputation": "репутация"
                    }}
                ],
                "technical_recommendations": "технические рекомендации",
                "procurement_advice": "советы по закупке"
            }}
            """

            # Create LlmChat instance for this request
            llm_chat = LlmChat(
                api_key=self.api_key,
                session_id=f"business_equipment_{hash(query)}",
                system_message="Ты эксперт по промышленному оборудованию и помогаешь найти лучшие решения для бизнеса."
            )
            
            user_message = UserMessage(text=prompt)
            response = await llm_chat.send_message(user_message)
            
            return {
                "success": True,
                "query": query,
                "category": category,
                "ai_analysis": response,
                "search_type": "business_equipment"
            }

        except Exception as e:
            logger.error(f"Business equipment search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    async def analyze_product_image(self, image_data: bytes, context: str = "") -> Dict[str, Any]:
        """Analyze product image and provide detailed information."""
        try:
            # Note: This would use vision capabilities in a full implementation
            # For now, we'll provide a structured response based on context
            
            prompt = f"""
            Пользователь загрузил изображение продукта. Контекст: "{context}"
            
            Предоставь анализ изображения в формате JSON:
            {{
                "product_identification": {{
                    "category": "категория товара",
                    "brand_detection": "определенный бренд (если виден)",
                    "model_estimation": "предполагаемая модель",
                    "condition": "состояние товара"
                }},
                "key_features": ["ключевые особенности"],
                "market_analysis": {{
                    "estimated_price": "примерная цена",
                    "popular_sources": ["где лучше покупать"],
                    "alternatives": ["аналоги и альтернативы"]
                }},
                "recommendations": "рекомендации по покупке"
            }}
            """

            # Create LlmChat instance for this request
            llm_chat = LlmChat(
                api_key=self.api_key,
                session_id=f"image_analysis_{hash(context)}",
                system_message="Ты эксперт по анализу товаров и помогаешь определить продукты по изображениям."
            )
            
            user_message = UserMessage(text=prompt)
            response = await llm_chat.send_message(user_message)
            
            return {
                "success": True,
                "context": context,
                "ai_analysis": response,
                "search_type": "image_analysis"
            }

        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "context": context
            }

    async def generate_predictive_suggestions(self, partial_query: str, search_context: str = "") -> Dict[str, Any]:
        """Generate predictive search suggestions based on partial input."""
        try:
            context_prompts = {
                "chinese": "китайские товары и платформы",
                "car_parts": "автозапчасти и OEM производители", 
                "business": "промышленное оборудование и B2B решения",
                "general": "товары и услуги BuyAnywhere"
            }
            
            context = context_prompts.get(search_context, context_prompts["general"])

            prompt = f"""
            Пользователь начал вводить поисковый запрос: "{partial_query}"
            Контекст поиска: {context}
            
            Предложи 5-10 наиболее вероятных завершений запроса в формате JSON:
            {{
                "suggestions": [
                    {{
                        "completion": "полный вариант запроса",
                        "category": "категория товара",
                        "popularity": "популярность 1-5",
                        "description": "краткое описание"
                    }}
                ],
                "trending": ["популярные сейчас запросы в этой категории"]
            }}
            """

            # Create LlmChat instance for this request
            llm_chat = LlmChat(
                api_key=self.api_key,
                session_id=f"predictive_{hash(partial_query)}",
                system_message="Ты эксперт по поисковым запросам и помогаешь пользователям найти то, что они ищут."
            )
            
            user_message = UserMessage(text=prompt)
            response = await llm_chat.send_message(user_message)
            
            return {
                "success": True,
                "partial_query": partial_query,
                "context": search_context,
                "ai_suggestions": response,
                "search_type": "predictive_suggestions"
            }

        except Exception as e:
            logger.error(f"Predictive suggestions failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "partial_query": partial_query
            }

    async def enhance_search_results(self, results: List[Dict], query: str, search_type: str) -> Dict[str, Any]:
        """Enhance search results with AI analysis and recommendations."""
        try:
            results_summary = "\n".join([
                f"- {r.get('name', 'Unknown')}: {r.get('description', 'No description')}" 
                for r in results[:5]
            ])

            prompt = f"""
            Пользователь искал: "{query}"
            Тип поиска: {search_type}
            
            Найденные результаты:
            {results_summary}
            
            Проанализируй результаты и предоставь:
            1. Краткий анализ найденных товаров
            2. Рекомендации по выбору
            3. Дополнительные критерии для рассмотрения
            4. Предупреждения о возможных проблемах
            
            Ответь в формате JSON:
            {{
                "analysis": "анализ результатов поиска",
                "top_recommendation": "главная рекомендация",
                "selection_criteria": ["критерии выбора"],
                "warnings": ["предупреждения"],
                "next_steps": ["следующие шаги"]
            }}
            """

            # Create LlmChat instance for this request
            llm_chat = LlmChat(
                api_key=self.api_key,
                session_id=f"enhance_{hash(query)}",
                system_message="Ты эксперт по анализу результатов поиска и помогаешь пользователям сделать лучший выбор."
            )
            
            user_message = UserMessage(text=prompt)
            response = await llm_chat.send_message(user_message)
            
            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results_count": len(results),
                "ai_enhancement": response
            }

        except Exception as e:
            logger.error(f"Results enhancement failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

# Global service instance
ai_search_service = AISearchService()