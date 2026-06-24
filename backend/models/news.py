"""
News models for international technology and shopping news integration
Supporting Russian localization and multiple API sources
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
import uuid

class NewsCategory(str, Enum):
    """News categories for BuyAnywhere content"""
    TECHNOLOGY = "technology"
    SHOPPING = "shopping"
    ELECTRONICS = "electronics"
    GADGETS = "gadgets"
    PRODUCT_LAUNCHES = "product_launches"
    SALES = "sales"
    E_COMMERCE = "e_commerce"
    INTERNATIONAL = "international"
    GENERAL = "general"

class NewsSource(str, Enum):
    """Supported news API sources"""
    NEWSDATA_IO = "newsdata_io"
    NEWSAPI_ORG = "newsapi_org"
    RSS_FEED = "rss_feed"
    MANUAL = "manual"

class NewsLanguage(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    RUSSIAN = "ru"
    AUTO_DETECT = "auto"

class NewsStatus(str, Enum):
    """Article processing status"""
    PENDING = "pending"
    PROCESSED = "processed"
    TRANSLATED = "translated"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"

# Core News Models
class NewsArticle(BaseModel):
    """Main news article model"""
    model_config = ConfigDict(extra="allow")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    article_id: str = Field(..., description="Unique article identifier from source")
    title: str = Field(..., description="Article title")
    title_ru: Optional[str] = Field(None, description="Russian translated title")
    
    description: Optional[str] = Field(None, description="Article summary/description")
    description_ru: Optional[str] = Field(None, description="Russian translated description")
    
    content: Optional[str] = Field(None, description="Full article content")
    content_ru: Optional[str] = Field(None, description="Russian translated content")
    
    url: str = Field(..., description="Original article URL")
    image_url: Optional[str] = Field(None, description="Article image URL")
    
    # Source information
    source: NewsSource = Field(..., description="API source of the article")
    source_name: Optional[str] = Field(None, description="Name of the news outlet")
    source_url: Optional[str] = Field(None, description="Source website URL")
    
    # Categorization
    category: NewsCategory = Field(default=NewsCategory.GENERAL)
    tags: List[str] = Field(default_factory=list, description="Article tags/keywords")
    
    # Language and localization
    language: NewsLanguage = Field(default=NewsLanguage.ENGLISH)
    
    # Publishing information
    published_at: datetime = Field(..., description="Original publication date")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # Status and metadata
    status: NewsStatus = Field(default=NewsStatus.PENDING)
    featured: bool = Field(default=False, description="Featured article flag")
    priority: int = Field(default=0, description="Display priority (higher = more important)")
    
    # Engagement metrics
    views: int = Field(default=0)
    clicks: int = Field(default=0)
    
    # Technical metadata
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Original API response")
    processing_notes: List[str] = Field(default_factory=list)
    
    # SEO and social
    seo_keywords: List[str] = Field(default_factory=list)
    social_shares: int = Field(default=0)

class NewsFilter(BaseModel):
    """News filtering and search parameters"""
    categories: List[NewsCategory] = Field(default_factory=list)
    sources: List[NewsSource] = Field(default_factory=list)
    languages: List[NewsLanguage] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    featured_only: bool = False
    status: Optional[NewsStatus] = None
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0)

class NewsSearchRequest(BaseModel):
    """Request model for news search API"""
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[NewsCategory] = None
    language: NewsLanguage = Field(default=NewsLanguage.RUSSIAN)
    limit: int = Field(default=10, le=50)
    include_content: bool = Field(default=False)

# API Integration Models
class NewsAPIConfig(BaseModel):
    """Configuration for news API sources"""
    model_config = ConfigDict(extra="allow")
    
    source: NewsSource
    api_key: Optional[str] = None
    base_url: str
    rate_limit_per_day: int
    rate_limit_per_hour: int = 0
    enabled: bool = True
    priority: int = 1  # Lower = higher priority
    
    # Source-specific settings
    supported_categories: List[str] = Field(default_factory=list)
    supported_languages: List[str] = Field(default=["en"])
    max_articles_per_request: int = 100
    
    # Request configuration
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 5

class NewsDataIOConfig(BaseModel):
    """NewsData.io specific configuration"""
    api_key: str
    categories: List[str] = Field(default=["technology", "business", "entertainment"])
    countries: List[str] = Field(default=["us", "gb", "de", "fr", "jp"])
    languages: List[str] = Field(default=["en"])
    exclude_domains: List[str] = Field(default_factory=list)
    priority_domains: List[str] = Field(default_factory=list)

class NewsAPIOrg(BaseModel):
    """NewsAPI.org specific configuration"""
    api_key: str
    sources: List[str] = Field(default_factory=list)  # Specific sources like "techcrunch"
    domains: List[str] = Field(default_factory=list)  # Domain filtering
    exclude_domains: List[str] = Field(default_factory=list)
    sort_by: str = Field(default="publishedAt")  # publishedAt, relevancy, popularity

# Response Models
class NewsResponse(BaseModel):
    """Standard response for news API endpoints"""
    success: bool
    message: str
    data: Optional[List[NewsArticle]] = None
    total: int = 0
    page: int = 1
    per_page: int = 20
    error: Optional[str] = None

class NewsFeedResponse(BaseModel):
    """Response for news feed with categories"""
    success: bool
    data: Dict[str, List[NewsArticle]] = Field(default_factory=dict)
    last_updated: datetime
    next_update: datetime
    total_articles: int = 0

# Statistics and Analytics
class NewsStatistics(BaseModel):
    """News system statistics"""
    total_articles: int = 0
    articles_today: int = 0
    articles_this_week: int = 0
    articles_by_category: Dict[str, int] = Field(default_factory=dict)
    articles_by_source: Dict[str, int] = Field(default_factory=dict)
    articles_by_language: Dict[str, int] = Field(default_factory=dict)
    top_keywords: List[Dict[str, Any]] = Field(default_factory=list)
    last_fetch_time: Optional[datetime] = None
    next_scheduled_fetch: Optional[datetime] = None
    api_quota_used: Dict[str, int] = Field(default_factory=dict)
    api_quota_remaining: Dict[str, int] = Field(default_factory=dict)

# Translation Models
class TranslationRequest(BaseModel):
    """Request for text translation"""
    text: str
    from_language: str = "en"
    to_language: str = "ru"
    field_type: str = "title"  # title, description, content

class TranslationResult(BaseModel):
    """Translation result"""
    original_text: str
    translated_text: str
    from_language: str
    to_language: str
    confidence: Optional[float] = None
    provider: str = "emergent_ai"

# Scheduling and Automation
class NewsUpdateSchedule(BaseModel):
    """News update scheduling configuration"""
    enabled: bool = True
    update_frequency_hours: int = 24  # Every 24 hours
    update_time_utc: str = "03:00"  # 6 AM Moscow time
    categories_to_update: List[NewsCategory] = Field(default_factory=list)
    max_articles_per_category: int = 50
    auto_translate: bool = True
    auto_publish: bool = True
    cleanup_old_articles_days: int = 30

class NewsUpdateJob(BaseModel):
    """News update job tracking"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    articles_fetched: int = 0
    articles_processed: int = 0
    articles_translated: int = 0
    errors: List[str] = Field(default_factory=list)
    sources_used: List[str] = Field(default_factory=list)

# Russian-specific Models
class RussianNewsKeywords(BaseModel):
    """Russian keywords for tech and shopping news"""
    technology_keywords: List[str] = Field(default=[
        "технологии", "гаджеты", "смартфон", "iPhone", "Android", 
        "ноутбук", "компьютер", "AI", "ИИ", "нейросети"
    ])
    
    shopping_keywords: List[str] = Field(default=[
        "покупки", "интернет-магазин", "скидки", "распродажа", 
        "доставка", "онлайн-шоппинг", "e-commerce", "маркетплейс"
    ])
    
    product_launch_keywords: List[str] = Field(default=[
        "анонс", "презентация", "новый продукт", "запуск", 
        "релиз", "выход", "дебют"
    ])
    
    electronics_keywords: List[str] = Field(default=[
        "электроника", "планшет", "наушники", "телевизор", 
        "игровая консоль", "умный дом", "носимые устройства"
    ])

# Error Handling
class NewsAPIError(BaseModel):
    """News API error information"""
    error_code: str
    error_message: str
    error_message_ru: str
    source: NewsSource
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request_details: Dict[str, Any] = Field(default_factory=dict)
    retry_after_seconds: Optional[int] = None