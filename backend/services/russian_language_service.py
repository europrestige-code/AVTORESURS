"""
Russian Language Processing Service for AI Telephony
Handles Russian language understanding, text processing, and localization
"""

import re
import pytz
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Tuple
import logging
from babel import Locale, dates, numbers
from babel.dates import format_date, format_time, format_datetime

from models.telephony import RussianCity
# Create mock AICallAnalysis if not available in models
try:
    from models.telephony import AICallAnalysis
except ImportError:
    from pydantic import BaseModel
    from datetime import datetime
    from typing import Dict, Any, List, Optional
    
    class AICallAnalysis(BaseModel):
        call_id: str
        intent: Optional[str] = None
        entities: Dict[str, Any] = {}
        sentiment: Optional[str] = None
        confidence: Optional[float] = None
        language: str = "ru"
        transcript: Optional[str] = None
        summary: Optional[str] = None
        action_items: List[str] = []
        resolution_status: Optional[str] = None
        created_at: datetime = datetime.now()

class RussianLanguageProcessor:
    """Handles Russian text processing and formatting"""
    
    def __init__(self):
        self.locale = Locale.parse("ru_RU")
        self.timezone = pytz.timezone("Europe/Moscow")
        self.logger = logging.getLogger(__name__)
        
        # Russian case endings for numbers
        self.number_cases = {
            'звонок': {1: 'звонок', 2: 'звонка', 5: 'звонков'},
            'минута': {1: 'минута', 2: 'минуты', 5: 'минут'},
            'час': {1: 'час', 2: 'часа', 5: 'часов'},
            'день': {1: 'день', 2: 'дня', 5: 'дней'},
            'месяц': {1: 'месяц', 2: 'месяца', 5: 'месяцев'},
            'год': {1: 'год', 2: 'года', 5: 'лет'},
            'номер': {1: 'номер', 2: 'номера', 5: 'номеров'},
            'агент': {1: 'агент', 2: 'агента', 5: 'агентов'},
            'заказ': {1: 'заказ', 2: 'заказа', 5: 'заказов'},
            'товар': {1: 'товар', 2: 'товара', 5: 'товаров'},
            'рубль': {1: 'рубль', 2: 'рубля', 5: 'рублей'}
        }
        
        # Russian city names with proper declensions
        self.city_names = {
            RussianCity.MOSCOW: {
                'nominative': 'Москва',
                'genitive': 'Москвы', 
                'dative': 'Москве',
                'accusative': 'Москву',
                'instrumental': 'Москвой',
                'prepositional': 'Москве'
            },
            RussianCity.KRASNOYARSK: {
                'nominative': 'Красноярск',
                'genitive': 'Красноярска',
                'dative': 'Красноярску', 
                'accusative': 'Красноярск',
                'instrumental': 'Красноярским',
                'prepositional': 'Красноярске'
            },
            RussianCity.VLADIVOSTOK: {
                'nominative': 'Владивосток',
                'genitive': 'Владивостока',
                'dative': 'Владивостоку',
                'accusative': 'Владивосток', 
                'instrumental': 'Владивостоком',
                'prepositional': 'Владивостоке'
            }
        }
        
        # Business greetings
        self.business_greetings = {
            'morning': 'Доброе утро',
            'day': 'Добрый день',
            'evening': 'Добрый вечер',
            'night': 'Добро пожаловать'
        }
    
    def pluralize_russian(self, number: int, word: str) -> str:
        """Apply Russian pluralization rules"""
        if word not in self.number_cases:
            return f"{number} {word}"
        
        cases = self.number_cases[word]
        
        # Russian pluralization rules
        if number % 10 == 1 and number % 100 != 11:
            return f"{number} {cases[1]}"
        elif 2 <= number % 10 <= 4 and not (12 <= number % 100 <= 14):
            return f"{number} {cases[2]}"
        else:
            return f"{number} {cases[5]}"
    
    def format_russian_phone(self, phone_number: str) -> str:
        """Format phone number according to Russian standards"""
        # Remove all non-digit characters
        clean_number = re.sub(r'\D', '', phone_number)
        
        # Handle different Russian phone formats
        if clean_number.startswith('7') and len(clean_number) == 11:
            # +7 (XXX) XXX-XX-XX format
            return f"+7 ({clean_number[1:4]}) {clean_number[4:7]}-{clean_number[7:9]}-{clean_number[9:11]}"
        elif clean_number.startswith('8') and len(clean_number) == 11:
            # Convert 8 to +7 format
            return f"+7 ({clean_number[1:4]}) {clean_number[4:7]}-{clean_number[7:9]}-{clean_number[9:11]}"
        elif len(clean_number) == 10:
            # Add country code
            return f"+7 ({clean_number[:3]}) {clean_number[3:6]}-{clean_number[6:8]}-{clean_number[8:10]}"
        else:
            return phone_number  # Return original if format is unclear
    
    def format_russian_currency(self, amount: float) -> str:
        """Format currency in Russian rubles"""
        try:
            formatted_number = numbers.format_currency(
                amount, 'RUB', locale=self.locale, currency_digits=True
            )
            return formatted_number
        except Exception:
            # Fallback formatting
            return f"{amount:,.2f} ₽"
    
    def format_russian_date(self, dt: datetime, include_year: bool = True) -> str:
        """Format date in Russian style"""
        try:
            if include_year:
                return format_date(dt, format='d MMMM y г.', locale=self.locale)
            else:
                return format_date(dt, format='d MMMM', locale=self.locale)
        except Exception:
            # Fallback formatting
            if include_year:
                return dt.strftime("%d.%m.%Y г.")
            else:
                return dt.strftime("%d.%m")
    
    def format_russian_time(self, dt: datetime) -> str:
        """Format time in Russian 24-hour format"""
        try:
            return format_time(dt, format='H:mm', locale=self.locale)
        except Exception:
            # Fallback formatting
            return dt.strftime("%H:%M")
    
    def format_russian_datetime(self, dt: datetime) -> str:
        """Format datetime in Russian style"""
        try:
            return format_datetime(dt, format='d MMMM y г. в H:mm', locale=self.locale)
        except Exception:
            # Fallback formatting
            return dt.strftime("%d.%m.%Y г. в %H:%M")
    
    def get_city_name(self, city: RussianCity, case: str = 'nominative') -> str:
        """Get Russian city name in specific grammatical case"""
        if city not in self.city_names:
            return city.value.title()
        
        city_cases = self.city_names[city]
        return city_cases.get(case, city_cases['nominative'])
    
    def format_business_greeting(self, hour: int) -> str:
        """Generate appropriate Russian business greeting based on time"""
        if 6 <= hour < 12:
            return self.business_greetings['morning']
        elif 12 <= hour < 17:
            return self.business_greetings['day']
        elif 17 <= hour < 22:
            return self.business_greetings['evening']
        else:
            return self.business_greetings['night']
    
    def format_call_duration(self, seconds: int) -> str:
        """Format call duration in Russian"""
        if seconds < 60:
            return self.pluralize_russian(seconds, 'секунда') if seconds > 0 else "менее секунды"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            if remaining_seconds > 0:
                return f"{self.pluralize_russian(minutes, 'минута')} {self.pluralize_russian(remaining_seconds, 'секунда')}"
            else:
                return self.pluralize_russian(minutes, 'минута')
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        result = self.pluralize_russian(hours, 'час')
        if remaining_minutes > 0:
            result += f" {self.pluralize_russian(remaining_minutes, 'минута')}"
        
        return result

class RussianCallIntentAnalyzer:
    """Analyzes Russian language call intents and extracts entities"""
    
    def __init__(self, emergent_key: str):
        self.emergent_key = emergent_key
        self.logger = logging.getLogger(__name__)
        
        # Common Russian customer service intents
        self.intent_patterns = {
            'order_status': [
                r'статус\s+заказа?',
                r'где\s+мой\s+заказ',
                r'проверить\s+заказ',
                r'отследить\s+заказ',
                r'когда\s+доставка',
                r'где\s+посылка'
            ],
            'speak_to_operator': [
                r'поговорить\s+с\s+оператором',
                r'живой\s+человек',
                r'менеджер',
                r'специалист',
                r'сотрудник'
            ],
            'complaint': [
                r'жалоба',
                r'претензия',
                r'недовольн',
                r'плохо',
                r'ужасно',
                r'возмущен'
            ],
            'compliment': [
                r'спасибо',
                r'благодар',
                r'отлично',
                r'хорошо',
                r'довольн'
            ],
            'callback_request': [
                r'перезвонить',
                r'обратный\s+звонок',
                r'перезвоните',
                r'свяжитесь'
            ],
            'payment_issue': [
                r'оплата',
                r'платеж',
                r'деньги',
                r'не\s+прошел\s+платеж',
                r'возврат\s+средств'
            ],
            'delivery_question': [
                r'доставка',
                r'курьер',
                r'получить',
                r'адрес',
                r'время\s+доставки'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'order_number': [
                r'заказ\s+(?:номер\s+)?([A-Z0-9\-]+)',
                r'ORD\-\d{8}\-[A-Z0-9]+',
                r'№\s*([A-Z0-9\-]+)'
            ],
            'phone_number': [
                r'\+?7\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}',
                r'8\s*\(?\d{3}\)?\s*\d{3}\s*\d{2}\s*\d{2}'
            ],
            'amount': [
                r'(\d+(?:\s*\d{3})*)\s*(?:рубл|₽)',
                r'(\d+(?:\.\d{2})?)\s*руб'
            ]
        }
    
    async def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Analyze customer intent from Russian text"""
        text_lower = text.lower()
        
        # Extract intents
        detected_intents = []
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected_intents.append(intent)
                    break
        
        # Extract entities
        entities = {}
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    entities[entity_type] = matches
        
        # Determine primary intent
        primary_intent = detected_intents[0] if detected_intents else 'general_inquiry'
        
        # Analyze sentiment (basic)
        sentiment = self._analyze_sentiment(text_lower)
        
        return {
            'primary_intent': primary_intent,
            'all_intents': detected_intents,
            'entities': entities,
            'sentiment': sentiment,
            'confidence': 0.8 if detected_intents else 0.5,
            'language': 'ru'
        }
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis for Russian text"""
        positive_words = [
            'спасибо', 'отлично', 'хорошо', 'супер', 'прекрасно', 
            'замечательно', 'благодарю', 'довольн'
        ]
        
        negative_words = [
            'плохо', 'ужасно', 'кошмар', 'отвратительно', 'недовольн',
            'жалоба', 'претензия', 'возмущен', 'безобразие'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

class RussianBusinessContext:
    """Handles Russian business context and cultural aspects"""
    
    def __init__(self, language_processor: RussianLanguageProcessor):
        self.language_processor = language_processor
        self.logger = logging.getLogger(__name__)
        
        # Russian federal holidays (fixed dates)
        self.federal_holidays = {
            (1, 1): "Новый год",
            (1, 7): "Рождество Христово", 
            (2, 23): "День защитника Отечества",
            (3, 8): "Международный женский день",
            (5, 1): "Праздник Весны и Труда",
            (5, 9): "День Победы",
            (6, 12): "День России",
            (11, 4): "День народного единства"
        }
        
        # Business hours by city
        self.business_hours = {
            RussianCity.MOSCOW: {'start': 9, 'end': 18, 'timezone': 'Europe/Moscow'},
            RussianCity.KRASNOYARSK: {'start': 9, 'end': 18, 'timezone': 'Asia/Krasnoyarsk'},
            RussianCity.VLADIVOSTOK: {'start': 9, 'end': 18, 'timezone': 'Asia/Vladivostok'}
        }
    
    def is_business_day(self, date_obj: datetime.date) -> bool:
        """Check if date is a Russian business day"""
        # Check if it's a weekend (Saturday = 5, Sunday = 6)
        if date_obj.weekday() >= 5:
            return False
        
        # Check if it's a federal holiday
        month_day = (date_obj.month, date_obj.day)
        if month_day in self.federal_holidays:
            return False
        
        return True
    
    def is_business_hours(self, dt: datetime, city: RussianCity = RussianCity.MOSCOW) -> bool:
        """Check if datetime falls within business hours for specific city"""
        city_info = self.business_hours.get(city, self.business_hours[RussianCity.MOSCOW])
        
        # Convert to city timezone
        city_tz = pytz.timezone(city_info['timezone'])
        local_dt = dt.astimezone(city_tz)
        
        # Check if it's a business day
        if not self.is_business_day(local_dt.date()):
            return False
        
        # Check business hours
        hour = local_dt.hour
        return city_info['start'] <= hour < city_info['end']
    
    def get_business_greeting_for_city(self, city: RussianCity = RussianCity.MOSCOW) -> str:
        """Get appropriate business greeting for specific Russian city"""
        city_info = self.business_hours.get(city, self.business_hours[RussianCity.MOSCOW])
        city_tz = pytz.timezone(city_info['timezone'])
        local_time = datetime.now(city_tz)
        
        greeting = self.language_processor.format_business_greeting(local_time.hour)
        city_name = self.language_processor.get_city_name(city, 'genitive')
        
        return f"{greeting} из {city_name}!"
    
    def format_business_message(
        self, 
        template: str,
        city: RussianCity = RussianCity.MOSCOW,
        **kwargs
    ) -> str:
        """Format business message with Russian localization"""
        
        # Add city-specific context
        kwargs['city'] = self.language_processor.get_city_name(city)
        kwargs['city_genitive'] = self.language_processor.get_city_name(city, 'genitive')
        
        # Add time context
        city_info = self.business_hours.get(city, self.business_hours[RussianCity.MOSCOW])
        city_tz = pytz.timezone(city_info['timezone'])
        local_time = datetime.now(city_tz)
        
        kwargs['current_time'] = self.language_processor.format_russian_time(local_time)
        kwargs['greeting'] = self.language_processor.format_business_greeting(local_time.hour)
        
        # Format template
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.logger.warning(f"Missing template variable: {e}")
            return template

class RussianTelephonyTemplates:
    """Pre-defined Russian templates for telephony responses"""
    
    ORDER_STATUS_RESPONSE = """
    {greeting}! Ваш заказ {order_number} {order_status}.
    {delivery_info}
    Если у вас есть вопросы, я могу соединить вас с оператором.
    """
    
    GENERAL_GREETING = """
    {greeting}! Вас приветствует служба поддержки BuyAnywhere из {city_genitive}.
    Чем могу помочь?
    """
    
    OPERATOR_TRANSFER = """
    Соединяю вас с оператором. Пожалуйста, подождите.
    """
    
    AFTER_HOURS_MESSAGE = """
    Сейчас нерабочее время. Наши операторы работают с {business_start} до {business_end} 
    по {timezone}. Оставьте сообщение или позвоните в рабочее время.
    """
    
    CALLBACK_CONFIRMATION = """
    Заявка на обратный звонок принята. Мы перезвоним вам в течение часа.
    """
    
    ERROR_MESSAGE = """
    Извините, произошла техническая ошибка. Соединяю с оператором.
    """

# Service class that combines all Russian language functionality
class RussianLanguageService:
    """Complete Russian language service for AI telephony"""
    
    def __init__(self, emergent_key: str):
        self.processor = RussianLanguageProcessor()
        self.intent_analyzer = RussianCallIntentAnalyzer(emergent_key)
        self.business_context = RussianBusinessContext(self.processor)
        self.templates = RussianTelephonyTemplates()
        self.logger = logging.getLogger(__name__)
    
    async def process_customer_input(
        self, 
        text: str, 
        city: RussianCity = RussianCity.MOSCOW
    ) -> Dict[str, Any]:
        """Process customer input and generate appropriate response"""
        
        # Analyze intent
        intent_analysis = await self.intent_analyzer.analyze_intent(text)
        
        # Generate response based on intent
        response = await self._generate_response(intent_analysis, city)
        
        return {
            'analysis': intent_analysis,
            'response': response,
            'city': city,
            'timestamp': datetime.now(pytz.timezone('Europe/Moscow')).isoformat()
        }
    
    async def _generate_response(
        self, 
        intent_analysis: Dict[str, Any], 
        city: RussianCity
    ) -> Dict[str, Any]:
        """Generate appropriate response based on intent analysis"""
        
        primary_intent = intent_analysis['primary_intent']
        entities = intent_analysis['entities']
        
        if primary_intent == 'order_status':
            order_number = entities.get('order_number', [''])[0] if entities.get('order_number') else None
            if order_number:
                # Would query actual order status here
                response_text = self.business_context.format_business_message(
                    self.templates.ORDER_STATUS_RESPONSE,
                    city=city,
                    order_number=order_number,
                    order_status="отправлен",
                    delivery_info="Ожидаемая дата доставки: завтра до 18:00"
                )
            else:
                response_text = "Назовите пожалуйста номер вашего заказа"
        
        elif primary_intent == 'speak_to_operator':
            response_text = self.templates.OPERATOR_TRANSFER
        
        elif primary_intent == 'callback_request':
            response_text = self.templates.CALLBACK_CONFIRMATION
        
        else:
            # General greeting
            response_text = self.business_context.format_business_message(
                self.templates.GENERAL_GREETING,
                city=city
            )
        
        return {
            'text': response_text,
            'action': self._determine_action(primary_intent),
            'transfer_to_operator': primary_intent in ['speak_to_operator', 'complaint'],
            'requires_followup': primary_intent in ['order_status', 'callback_request']
        }
    
    def _determine_action(self, intent: str) -> str:
        """Determine next action based on intent"""
        action_mapping = {
            'order_status': 'check_order',
            'speak_to_operator': 'transfer_call',
            'complaint': 'transfer_call',
            'callback_request': 'schedule_callback',
            'payment_issue': 'transfer_call',
            'delivery_question': 'provide_info'
        }
        
        return action_mapping.get(intent, 'continue_conversation')