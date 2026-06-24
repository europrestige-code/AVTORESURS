"""
Main News Service
Handles news storage, translation, scheduling, and Russian localization
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid

from models.news import (
    NewsArticle, NewsCategory, NewsSource, NewsLanguage, NewsStatus,
    NewsFilter, NewsResponse, NewsFeedResponse, NewsStatistics,
    NewsUpdateSchedule, NewsUpdateJob, TranslationRequest, TranslationResult
)
from services.news_api_service import NewsAggregatorService

try:
    from emergentintegrations import LlmChat
except ImportError:
    # Mock LlmChat if not available
    class LlmChat:
        def __init__(self, api_key: str):
            self.api_key = api_key
        
        async def chat(self, prompt: str) -> object:
            class MockResponse:
                message = f"Mock translation: {prompt[:100]}..."
            return MockResponse()

class NewsTranslationService:
    """Handles Russian translation of news articles using AI"""
    
    def __init__(self, emergent_key: str, logger: Optional[logging.Logger] = None):
        self.emergent_key = emergent_key
        self.logger = logger or logging.getLogger(__name__)
        self.ai_client = LlmChat(api_key=emergent_key)
        
        # Translation prompts in Russian
        self.translation_prompts = {
            "title": """Переведи заголовок новости на русский язык. Сохрани смысл и сделай его привлекательным для русскоязычной аудитории:
            
Заголовок: {text}

Перевод:""",
            
            "description": """Переведи описание новости на русский язык. Сохрани все важные детали и сделай текст понятным:

Описание: {text}

Перевод:""",
            
            "content": """Переведи статью на русский язык. Сохрани структуру, все факты и технические термины. Сделай текст естественным для русского читателя:

Статья: {text}

Перевод:"""
        }
    
    async def translate_article(self, article: NewsArticle) -> NewsArticle:
        """Translate article fields to Russian"""
        try:
            # Translate title
            if article.title and not article.title_ru:
                article.title_ru = await self._translate_text(
                    article.title, "title"
                )
            
            # Translate description
            if article.description and not article.description_ru:
                article.description_ru = await self._translate_text(
                    article.description, "description"
                )
            
            # Translate content (if available and not too long)
            if article.content and not article.content_ru and len(article.content) < 5000:
                article.content_ru = await self._translate_text(
                    article.content, "content"
                )
            
            # Update status
            if article.title_ru or article.description_ru:
                article.status = NewsStatus.TRANSLATED
            
            self.logger.info(f"Successfully translated article: {article.title[:50]}...")
            return article
            
        except Exception as e:
            self.logger.error(f"Error translating article {article.article_id}: {e}")
            article.processing_notes.append(f"Translation failed: {str(e)}")
            return article
    
    async def _translate_text(self, text: str, field_type: str) -> str:
        """Translate text using AI"""
        try:
            prompt = self.translation_prompts[field_type].format(text=text)
            response = await self.ai_client.chat(prompt)
            
            # Clean up the response
            translated = response.message.strip()
            
            # Remove any "Перевод:" prefix if AI added it
            if translated.startswith("Перевод:"):
                translated = translated[8:].strip()
            
            return translated
            
        except Exception as e:
            self.logger.error(f"AI translation failed for {field_type}: {e}")
            return f"[Перевод недоступен] {text[:100]}..."

class NewsService:
    """Main news service handling all news operations"""
    
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        emergent_key: str,
        newsdata_api_key: Optional[str] = None,
        newsapi_api_key: Optional[str] = None
    ):
        self.db = database
        self.emergent_key = emergent_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.aggregator = NewsAggregatorService(
            newsdata_api_key=newsdata_api_key,
            newsapi_api_key=newsapi_api_key,
            logger=self.logger
        )
        self.translator = NewsTranslationService(emergent_key, self.logger)
        
        # Collections
        self.articles_collection = database.news_articles
        self.jobs_collection = database.news_jobs
        self.config_collection = database.news_config
        
        # Default update schedule
        self.default_schedule = NewsUpdateSchedule(
            enabled=True,
            update_frequency_hours=24,
            update_time_utc="03:00",  # 6 AM Moscow time
            categories_to_update=[
                NewsCategory.TECHNOLOGY,
                NewsCategory.ELECTRONICS,
                NewsCategory.PRODUCT_LAUNCHES,
                NewsCategory.SHOPPING,
                NewsCategory.SALES
            ],
            max_articles_per_category=10,
            auto_translate=True,
            auto_publish=True
        )
    
    async def initialize(self) -> bool:
        """Initialize news service"""
        try:
            # Create indexes for better performance
            await self._create_indexes()
            self.logger.info("News service initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize news service: {e}")
            return False
    
    async def _create_indexes(self):
        """Create database indexes"""
        # Article indexes
        await self.articles_collection.create_index("article_id", unique=True)
        await self.articles_collection.create_index("category")
        await self.articles_collection.create_index("published_at")
        await self.articles_collection.create_index("status")
        await self.articles_collection.create_index("featured")
        await self.articles_collection.create_index([("category", 1), ("published_at", -1)])
        
        # Text search index for Russian content
        await self.articles_collection.create_index([
            ("title", "text"),
            ("title_ru", "text"),
            ("description", "text"),
            ("description_ru", "text")
        ])
    
    # News Fetching and Processing
    async def fetch_and_store_news(
        self, 
        categories: Optional[List[NewsCategory]] = None,
        max_articles_per_category: int = 10,
        auto_translate: bool = True
    ) -> NewsUpdateJob:
        """Fetch news from APIs and store in database"""
        
        job = NewsUpdateJob()
        
        try:
            # Use default categories if none provided
            if not categories:
                categories = self.default_schedule.categories_to_update
            
            self.logger.info(f"Starting news fetch job {job.job_id}")
            
            # Fetch news for each category
            for category in categories:
                try:
                    articles = await self.aggregator.fetch_category_news(
                        category=category,
                        max_articles=max_articles_per_category
                    )
                    
                    job.articles_fetched += len(articles)
                    
                    # Process and store articles
                    for article in articles:
                        try:
                            # Check if article already exists
                            existing = await self.articles_collection.find_one({
                                "article_id": article.article_id
                            })
                            
                            if not existing:
                                # Translate if requested
                                if auto_translate:
                                    article = await self.translator.translate_article(article)
                                    job.articles_translated += 1
                                
                                article.status = NewsStatus.PROCESSED
                                
                                # Store in database
                                await self.articles_collection.insert_one(article.model_dump())
                                job.articles_processed += 1
                                
                                self.logger.info(f"Stored new article: {article.title[:50]}...")
                            else:
                                self.logger.debug(f"Article already exists: {article.article_id}")
                        
                        except Exception as e:
                            error_msg = f"Error processing article {article.article_id}: {e}"
                            self.logger.error(error_msg)
                            job.errors.append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error fetching {category.value} news: {e}"
                    self.logger.error(error_msg)
                    job.errors.append(error_msg)
                
                # Small delay between categories
                await asyncio.sleep(2)
            
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            
            # Store job record
            await self.jobs_collection.insert_one(job.model_dump())
            
            self.logger.info(
                f"News fetch job completed: {job.articles_processed} processed, "
                f"{job.articles_translated} translated, {len(job.errors)} errors"
            )
            
            return job
            
        except Exception as e:
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            job.errors.append(f"Job failed: {str(e)}")
            
            await self.jobs_collection.insert_one(job.model_dump())
            
            self.logger.error(f"News fetch job failed: {e}")
            return job
    
    # News Retrieval
    async def get_news_feed(
        self, 
        language: NewsLanguage = NewsLanguage.RUSSIAN,
        categories: Optional[List[NewsCategory]] = None,
        limit_per_category: int = 5
    ) -> NewsFeedResponse:
        """Get organized news feed by categories"""
        try:
            feed_data = {}
            total_articles = 0
            
            # Default categories if none provided
            if not categories:
                categories = [
                    NewsCategory.TECHNOLOGY,
                    NewsCategory.ELECTRONICS,
                    NewsCategory.PRODUCT_LAUNCHES,
                    NewsCategory.SHOPPING,
                    NewsCategory.SALES
                ]
            
            for category in categories:
                articles = await self.get_articles_by_category(
                    category=category,
                    language=language,
                    limit=limit_per_category,
                    status=NewsStatus.PROCESSED
                )
                feed_data[category.value] = articles
                total_articles += len(articles)
            
            # Get last update time
            last_job = await self.jobs_collection.find_one(
                {"status": "completed"},
                sort=[("completed_at", -1)]
            )
            
            last_updated = datetime.now(timezone.utc)
            if last_job:
                last_updated = last_job.get("completed_at", last_updated)
            
            # Calculate next update time
            next_update = last_updated + timedelta(hours=24)
            
            return NewsFeedResponse(
                success=True,
                data=feed_data,
                last_updated=last_updated,
                next_update=next_update,
                total_articles=total_articles
            )
            
        except Exception as e:
            self.logger.error(f"Error getting news feed: {e}")
            return NewsFeedResponse(
                success=False,
                data={},
                last_updated=datetime.now(timezone.utc),
                next_update=datetime.now(timezone.utc) + timedelta(hours=1),
                total_articles=0
            )
    
    async def get_articles_by_category(
        self,
        category: NewsCategory,
        language: NewsLanguage = NewsLanguage.RUSSIAN,
        limit: int = 10,
        status: Optional[NewsStatus] = None
    ) -> List[NewsArticle]:
        """Get articles for specific category"""
        try:
            query = {"category": category.value}
            
            if status:
                query["status"] = status.value
            
            cursor = self.articles_collection.find(query).sort("published_at", -1).limit(limit)
            articles = []
            
            async for doc in cursor:
                article = NewsArticle(**doc)
                
                # Use Russian content if available and requested
                if language == NewsLanguage.RUSSIAN:
                    if not article.title_ru and article.title:
                        # Auto-translate on demand if not already translated
                        article = await self.translator.translate_article(article)
                        # Update in database
                        await self.articles_collection.update_one(
                            {"article_id": article.article_id},
                            {"$set": article.model_dump()}
                        )
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error getting articles for {category.value}: {e}")
            return []
    
    async def search_articles(
        self,
        query: str,
        language: NewsLanguage = NewsLanguage.RUSSIAN,
        categories: Optional[List[NewsCategory]] = None,
        limit: int = 20
    ) -> List[NewsArticle]:
        """Search articles by text query"""
        try:
            # Build search query
            search_filter = {"$text": {"$search": query}}
            
            if categories:
                search_filter["category"] = {"$in": [cat.value for cat in categories]}
            
            cursor = self.articles_collection.find(
                search_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            articles = []
            async for doc in cursor:
                articles.append(NewsArticle(**doc))
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error searching articles: {e}")
            return []
    
    # Statistics and Management
    async def get_news_statistics(self) -> NewsStatistics:
        """Get news system statistics"""
        try:
            # Total articles
            total_articles = await self.articles_collection.count_documents({})
            
            # Articles today
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            articles_today = await self.articles_collection.count_documents({
                "fetched_at": {"$gte": today_start}
            })
            
            # Articles this week
            week_start = today_start - timedelta(days=7)
            articles_this_week = await self.articles_collection.count_documents({
                "fetched_at": {"$gte": week_start}
            })
            
            # Articles by category
            category_pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            category_counts = {}
            async for doc in self.articles_collection.aggregate(category_pipeline):
                category_counts[doc["_id"]] = doc["count"]
            
            # Articles by source
            source_pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            source_counts = {}
            async for doc in self.articles_collection.aggregate(source_pipeline):
                source_counts[doc["_id"]] = doc["count"]
            
            # Get last job info
            last_job = await self.jobs_collection.find_one(
                {"status": "completed"},
                sort=[("completed_at", -1)]
            )
            
            last_fetch_time = None
            next_scheduled = None
            
            if last_job:
                last_fetch_time = last_job.get("completed_at")
                next_scheduled = last_fetch_time + timedelta(hours=24)
            
            # API quota info
            service_status = await self.aggregator.get_service_status()
            
            return NewsStatistics(
                total_articles=total_articles,
                articles_today=articles_today,
                articles_this_week=articles_this_week,
                articles_by_category=category_counts,
                articles_by_source=source_counts,
                articles_by_language={"en": total_articles, "ru": total_articles},  # Simplified
                last_fetch_time=last_fetch_time,
                next_scheduled_fetch=next_scheduled,
                api_quota_used={
                    "newsdata_io": service_status.get("newsdata_io", {}).get("requests_today", 0),
                    "newsapi_org": service_status.get("newsapi_org", {}).get("requests_today", 0)
                },
                api_quota_remaining={
                    "newsdata_io": service_status.get("newsdata_io", {}).get("daily_limit", 100) - 
                                  service_status.get("newsdata_io", {}).get("requests_today", 0),
                    "newsapi_org": service_status.get("newsapi_org", {}).get("daily_limit", 100) - 
                                 service_status.get("newsapi_org", {}).get("requests_today", 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting news statistics: {e}")
            return NewsStatistics()
    
    async def cleanup_old_articles(self, days_old: int = 30) -> int:
        """Remove articles older than specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            result = await self.articles_collection.delete_many({
                "fetched_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            self.logger.info(f"Cleaned up {deleted_count} old articles (older than {days_old} days)")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old articles: {e}")
            return 0