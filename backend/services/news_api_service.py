"""
News API Integration Service
Handles integration with NewsData.io and NewsAPI.org for technology and shopping news
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
from urllib.parse import urlencode

from models.news import (
    NewsArticle, NewsCategory, NewsSource, NewsLanguage, NewsStatus,
    NewsAPIConfig, NewsDataIOConfig, NewsAPIOrg, NewsAPIError,
    RussianNewsKeywords
)

class NewsAPIClient:
    """Base news API client with common functionality"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_count = 0
        self.daily_limit = 100
        self.last_reset = datetime.now(timezone.utc).date()
        
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
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
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_date = datetime.now(timezone.utc).date()
        
        # Reset counter if new day
        if current_date > self.last_reset:
            self.request_count = 0
            self.last_reset = current_date
        
        return self.request_count < self.daily_limit
    
    def _increment_request_count(self):
        """Increment request counter"""
        self.request_count += 1
    
    async def _make_request(
        self, 
        url: str, 
        params: Dict[str, Any], 
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        if not self._check_rate_limit():
            raise Exception(f"Daily rate limit exceeded ({self.daily_limit})")
        
        if not self.session:
            await self.connect()
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                self._increment_request_count()
                
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    raise Exception("Rate limit exceeded by API")
                elif response.status == 401:
                    raise Exception("Invalid API key")
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise Exception(f"Network error: {str(e)}")

class NewsDataIOClient(NewsAPIClient):
    """NewsData.io API client for technology and shopping news"""
    
    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.api_key = api_key
        self.base_url = "https://newsdata.io/api/1/news"
        self.daily_limit = 100  # Free tier limit
        
        # Category mapping to NewsData.io categories
        self.category_mapping = {
            NewsCategory.TECHNOLOGY: "technology",
            NewsCategory.ELECTRONICS: "technology",
            NewsCategory.GADGETS: "technology",
            NewsCategory.SHOPPING: "business",
            NewsCategory.E_COMMERCE: "business",
            NewsCategory.PRODUCT_LAUNCHES: "technology",
            NewsCategory.SALES: "business"
        }
        
        # Keywords for better filtering
        self.tech_keywords = [
            "iPhone", "Android", "smartphone", "laptop", "gadget", "AI", 
            "artificial intelligence", "product launch", "tech", "innovation",
            "electronics", "device", "app", "software", "hardware"
        ]
        
        self.shopping_keywords = [
            "e-commerce", "online shopping", "retail", "marketplace", "sale",
            "discount", "shopping", "consumer", "product", "brand", "store"
        ]
    
    async def fetch_tech_news(
        self, 
        category: NewsCategory = NewsCategory.TECHNOLOGY,
        limit: int = 10,
        language: str = "en"
    ) -> List[NewsArticle]:
        """Fetch technology news from NewsData.io"""
        try:
            # Map category to NewsData.io category
            api_category = self.category_mapping.get(category, "technology")
            
            # Determine keywords based on category
            if category in [NewsCategory.SHOPPING, NewsCategory.E_COMMERCE, NewsCategory.SALES]:
                keywords = ",".join(self.shopping_keywords[:5])  # Limit keywords
            else:
                keywords = ",".join(self.tech_keywords[:5])
            
            params = {
                "apikey": self.api_key,
                "category": api_category,
                "language": language,
                "size": min(limit, 10),  # NewsData.io free tier allows max 10
                "q": keywords,
                "country": "us,gb,de,fr,jp",  # Major tech markets
                "timeframe": "24h"  # Last 24 hours
            }
            
            self.logger.info(f"Fetching {category.value} news with keywords: {keywords}")
            data = await self._make_request(self.base_url, params)
            
            articles = []
            if data.get("status") == "success" and "results" in data:
                for item in data["results"]:
                    try:
                        article = self._parse_newsdata_article(item, category, NewsSource.NEWSDATA_IO)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        self.logger.error(f"Error parsing NewsData.io article: {e}")
                        continue
            
            self.logger.info(f"Successfully fetched {len(articles)} articles from NewsData.io")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching tech news from NewsData.io: {e}")
            return []
    
    def _parse_newsdata_article(
        self, 
        item: Dict[str, Any], 
        category: NewsCategory,
        source: NewsSource
    ) -> Optional[NewsArticle]:
        """Parse NewsData.io article response"""
        try:
            # Generate article ID from URL or title
            article_id = hashlib.md5(
                (item.get("link", "") + item.get("title", "")).encode()
            ).hexdigest()
            
            # Parse publication date
            pub_date_str = item.get("pubDate")
            if pub_date_str:
                try:
                    # NewsData.io returns ISO format
                    published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except Exception:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Extract and clean content
            description = item.get("description", "")
            content = item.get("content") or description
            
            # Generate tags from keywords and category
            tags = []
            if category in [NewsCategory.SHOPPING, NewsCategory.E_COMMERCE]:
                tags.extend(["shopping", "e-commerce", "retail"])
            else:
                tags.extend(["technology", "tech", "innovation"])
            
            # Add source-specific tags
            if item.get("source_id"):
                tags.append(item["source_id"])
            
            article = NewsArticle(
                article_id=article_id,
                title=item.get("title", ""),
                description=description,
                content=content,
                url=item.get("link", ""),
                image_url=item.get("image_url"),
                source=source,
                source_name=item.get("source_id", "Unknown"),
                category=category,
                tags=tags,
                language=NewsLanguage.ENGLISH,
                published_at=published_at,
                status=NewsStatus.PENDING,
                raw_data=item
            )
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing NewsData.io article: {e}")
            return None

class NewsAPIClient_Org(NewsAPIClient):
    """NewsAPI.org client for backup news source"""
    
    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        super().__init__(logger)
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        self.daily_limit = 100  # Free tier limit
        
        # Preferred tech sources
        self.tech_sources = [
            "techcrunch", "the-verge", "engadget", "wired", "ars-technica",
            "techradar", "the-next-web", "mashable", "recode"
        ]
        
        # Keywords for different categories
        self.category_keywords = {
            NewsCategory.TECHNOLOGY: "technology OR tech OR AI OR artificial intelligence OR smartphone OR gadget",
            NewsCategory.ELECTRONICS: "electronics OR device OR smartphone OR laptop OR tablet OR headphones",
            NewsCategory.PRODUCT_LAUNCHES: "product launch OR new product OR announcement OR release OR debut",
            NewsCategory.SHOPPING: "e-commerce OR shopping OR retail OR online store OR marketplace",
            NewsCategory.SALES: "sale OR discount OR deal OR offer OR promotion OR black friday"
        }
    
    async def fetch_tech_news(
        self, 
        category: NewsCategory = NewsCategory.TECHNOLOGY,
        limit: int = 10,
        language: str = "en"
    ) -> List[NewsArticle]:
        """Fetch technology news from NewsAPI.org"""
        try:
            # Get keywords for category
            query = self.category_keywords.get(category, "technology")
            
            # Use yesterday to avoid 24-hour delay on free tier
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            from_date = yesterday.strftime("%Y-%m-%d")
            
            params = {
                "apiKey": self.api_key,
                "q": query,
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": min(limit, 20),
                "from": from_date,
                "domains": "techcrunch.com,theverge.com,engadget.com,wired.com"
            }
            
            self.logger.info(f"Fetching {category.value} news from NewsAPI.org with query: {query}")
            data = await self._make_request(self.base_url, params)
            
            articles = []
            if data.get("status") == "ok" and "articles" in data:
                for item in data["articles"]:
                    try:
                        article = self._parse_newsapi_article(item, category, NewsSource.NEWSAPI_ORG)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        self.logger.error(f"Error parsing NewsAPI.org article: {e}")
                        continue
            
            self.logger.info(f"Successfully fetched {len(articles)} articles from NewsAPI.org")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching tech news from NewsAPI.org: {e}")
            return []
    
    def _parse_newsapi_article(
        self, 
        item: Dict[str, Any], 
        category: NewsCategory,
        source: NewsSource
    ) -> Optional[NewsArticle]:
        """Parse NewsAPI.org article response"""
        try:
            # Generate article ID from URL
            article_id = hashlib.md5(item.get("url", "").encode()).hexdigest()
            
            # Parse publication date
            pub_date_str = item.get("publishedAt")
            if pub_date_str:
                try:
                    published_at = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except Exception:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)
            
            # Generate tags
            tags = [category.value]
            if item.get("source", {}).get("name"):
                tags.append(item["source"]["name"].lower().replace(" ", "-"))
            
            article = NewsArticle(
                article_id=article_id,
                title=item.get("title", ""),
                description=item.get("description", ""),
                content=item.get("content", ""),
                url=item.get("url", ""),
                image_url=item.get("urlToImage"),
                source=source,
                source_name=item.get("source", {}).get("name", "Unknown"),
                source_url=item.get("source", {}).get("url"),
                category=category,
                tags=tags,
                language=NewsLanguage.ENGLISH,
                published_at=published_at,
                status=NewsStatus.PENDING,
                raw_data=item
            )
            
            return article
            
        except Exception as e:
            self.logger.error(f"Error parsing NewsAPI.org article: {e}")
            return None

class NewsAggregatorService:
    """Main service for aggregating news from multiple sources"""
    
    def __init__(
        self,
        newsdata_api_key: Optional[str] = None,
        newsapi_api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.newsdata_client = NewsDataIOClient(newsdata_api_key, logger) if newsdata_api_key else None
        self.newsapi_client = NewsAPIClient_Org(newsapi_api_key, logger) if newsapi_api_key else None
        self.russian_keywords = RussianNewsKeywords()
    
    async def fetch_category_news(
        self, 
        category: NewsCategory,
        max_articles: int = 20,
        prefer_recent: bool = True
    ) -> List[NewsArticle]:
        """Fetch news for a specific category from all available sources"""
        all_articles = []
        
        # Try NewsData.io first (primary source)
        if self.newsdata_client:
            try:
                async with self.newsdata_client:
                    articles = await self.newsdata_client.fetch_tech_news(
                        category=category,
                        limit=min(max_articles, 10)
                    )
                    all_articles.extend(articles)
                    self.logger.info(f"NewsData.io: fetched {len(articles)} articles for {category.value}")
            except Exception as e:
                self.logger.error(f"NewsData.io failed for {category.value}: {e}")
        
        # Try NewsAPI.org as backup if we need more articles
        remaining_articles = max_articles - len(all_articles)
        if remaining_articles > 0 and self.newsapi_client:
            try:
                async with self.newsapi_client:
                    articles = await self.newsapi_client.fetch_tech_news(
                        category=category,
                        limit=remaining_articles
                    )
                    all_articles.extend(articles)
                    self.logger.info(f"NewsAPI.org: fetched {len(articles)} articles for {category.value}")
            except Exception as e:
                self.logger.error(f"NewsAPI.org failed for {category.value}: {e}")
        
        # Remove duplicates based on URL or title similarity
        unique_articles = self._deduplicate_articles(all_articles)
        
        # Sort by publication date if prefer_recent
        if prefer_recent:
            unique_articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return unique_articles[:max_articles]
    
    async def fetch_all_categories(
        self, 
        articles_per_category: int = 10
    ) -> Dict[NewsCategory, List[NewsArticle]]:
        """Fetch news for all categories"""
        categories = [
            NewsCategory.TECHNOLOGY,
            NewsCategory.ELECTRONICS,
            NewsCategory.PRODUCT_LAUNCHES,
            NewsCategory.SHOPPING,
            NewsCategory.SALES
        ]
        
        results = {}
        
        for category in categories:
            try:
                articles = await self.fetch_category_news(
                    category=category,
                    max_articles=articles_per_category
                )
                results[category] = articles
                self.logger.info(f"Fetched {len(articles)} articles for {category.value}")
                
                # Small delay to respect rate limits
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Failed to fetch {category.value} news: {e}")
                results[category] = []
        
        return results
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on URL and title similarity"""
        seen_urls = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Check URL duplicates
            if article.url in seen_urls:
                continue
            
            # Check title similarity (simple approach)
            title_words = set(article.title.lower().split())
            is_similar = False
            
            for seen_title in seen_titles:
                seen_words = set(seen_title.lower().split())
                similarity = len(title_words & seen_words) / max(len(title_words), len(seen_words))
                if similarity > 0.7:  # 70% similarity threshold
                    is_similar = True
                    break
            
            if not is_similar:
                seen_urls.add(article.url)
                seen_titles.add(article.title)
                unique_articles.append(article)
        
        return unique_articles
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all news services"""
        status = {
            "newsdata_io": {
                "available": self.newsdata_client is not None,
                "requests_today": self.newsdata_client.request_count if self.newsdata_client else 0,
                "daily_limit": self.newsdata_client.daily_limit if self.newsdata_client else 0
            },
            "newsapi_org": {
                "available": self.newsapi_client is not None,
                "requests_today": self.newsapi_client.request_count if self.newsapi_client else 0,
                "daily_limit": self.newsapi_client.daily_limit if self.newsapi_client else 0
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
        return status