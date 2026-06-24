"""
News API Routes
Provides REST API endpoints for international technology and shopping news
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from typing import List, Optional
import logging
import os
from datetime import datetime

from models.news import (
    NewsArticle, NewsCategory, NewsLanguage, NewsStatus,
    NewsSearchRequest, NewsResponse, NewsFeedResponse, NewsStatistics,
    NewsUpdateJob
)
from services.news_service import NewsService
from utils.auth import get_current_admin_user

router = APIRouter(prefix="/api/news", tags=["news"])
logger = logging.getLogger(__name__)

# Dependency to get news service
async def get_news_service() -> NewsService:
    """Get news service instance"""
    from server import news_service
    return news_service

# Public News Endpoints (no auth required)
@router.get("/feed")
async def get_news_feed(
    language: NewsLanguage = NewsLanguage.RUSSIAN,
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    limit_per_category: int = Query(5, le=20),
    news_service: NewsService = Depends(get_news_service)
):
    """Get organized news feed by categories"""
    try:
        # Parse categories if provided
        category_list = None
        if categories:
            category_names = [cat.strip() for cat in categories.split(",")]
            category_list = []
            for cat_name in category_names:
                try:
                    category_list.append(NewsCategory(cat_name))
                except ValueError:
                    logger.warning(f"Invalid category: {cat_name}")
        
        feed = await news_service.get_news_feed(
            language=language,
            categories=category_list,
            limit_per_category=limit_per_category
        )
        
        return feed
        
    except Exception as e:
        logger.error(f"Error getting news feed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении новостной ленты"
        )

@router.get("/category/{category}")
async def get_news_by_category(
    category: NewsCategory,
    language: NewsLanguage = NewsLanguage.RUSSIAN,
    limit: int = Query(10, le=50),
    news_service: NewsService = Depends(get_news_service)
):
    """Get news articles for specific category"""
    try:
        articles = await news_service.get_articles_by_category(
            category=category,
            language=language,
            limit=limit,
            status=NewsStatus.PROCESSED
        )
        
        return NewsResponse(
            success=True,
            message=f"Получено {len(articles)} новостей в категории {category.value}",
            data=articles,
            total=len(articles)
        )
        
    except Exception as e:
        logger.error(f"Error getting news for category {category}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении новостей категории {category.value}"
        )

@router.post("/search")
async def search_news(
    request: NewsSearchRequest,
    news_service: NewsService = Depends(get_news_service)
):
    """Search news articles by query"""
    try:
        if not request.query:
            raise HTTPException(
                status_code=400,
                detail="Поисковый запрос не может быть пустым"
            )
        
        articles = await news_service.search_articles(
            query=request.query,
            language=request.language,
            categories=[request.category] if request.category else None,
            limit=request.limit
        )
        
        return NewsResponse(
            success=True,
            message=f"Найдено {len(articles)} новостей по запросу '{request.query}'",
            data=articles,
            total=len(articles)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при поиске новостей"
        )

@router.get("/trending")
async def get_trending_news(
    language: NewsLanguage = NewsLanguage.RUSSIAN,
    limit: int = Query(20, le=50),
    news_service: NewsService = Depends(get_news_service)
):
    """Get trending/featured news articles"""
    try:
        # Get featured articles across all categories
        categories = [
            NewsCategory.TECHNOLOGY,
            NewsCategory.ELECTRONICS,
            NewsCategory.PRODUCT_LAUNCHES,
            NewsCategory.SHOPPING
        ]
        
        all_articles = []
        for category in categories:
            articles = await news_service.get_articles_by_category(
                category=category,
                language=language,
                limit=5,  # 5 per category
                status=NewsStatus.PROCESSED
            )
            all_articles.extend(articles)
        
        # Sort by published date and limit
        all_articles.sort(key=lambda x: x.published_at, reverse=True)
        trending_articles = all_articles[:limit]
        
        return NewsResponse(
            success=True,
            message=f"Получено {len(trending_articles)} популярных новостей",
            data=trending_articles,
            total=len(trending_articles)
        )
        
    except Exception as e:
        logger.error(f"Error getting trending news: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении популярных новостей"
        )

@router.get("/categories")
async def get_news_categories():
    """Get available news categories with Russian translations"""
    try:
        categories = {
            NewsCategory.TECHNOLOGY.value: {
                "name": "Технологии",
                "description": "Новости технологий, ИИ и инноваций",
                "icon": "laptop"
            },
            NewsCategory.ELECTRONICS.value: {
                "name": "Электроника",
                "description": "Смартфоны, гаджеты и электроника",
                "icon": "smartphone"
            },
            NewsCategory.PRODUCT_LAUNCHES.value: {
                "name": "Новые продукты",
                "description": "Анонсы и запуски новых продуктов",
                "icon": "rocket"
            },
            NewsCategory.SHOPPING.value: {
                "name": "Шоппинг",
                "description": "E-commerce и интернет-покупки",
                "icon": "shopping-bag"
            },
            NewsCategory.SALES.value: {
                "name": "Скидки и акции",
                "description": "Распродажи и специальные предложения",
                "icon": "tag"
            }
        }
        
        return {
            "success": True,
            "data": categories,
            "message": "Категории новостей получены"
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении категорий"
        )

# Admin News Management Endpoints
@router.post("/admin/fetch", response_model=NewsResponse)
async def fetch_news_manual(
    categories: Optional[str] = Query(None, description="Comma-separated categories"),
    max_articles: int = Query(10, le=50),
    auto_translate: bool = Query(True),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    admin = Depends(get_current_admin_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Manually trigger news fetch (admin only)"""
    try:
        # Parse categories
        category_list = None
        if categories:
            category_names = [cat.strip() for cat in categories.split(",")]
            category_list = []
            for cat_name in category_names:
                try:
                    category_list.append(NewsCategory(cat_name))
                except ValueError:
                    logger.warning(f"Invalid category: {cat_name}")
        
        # Run news fetch in background
        background_tasks.add_task(
            news_service.fetch_and_store_news,
            categories=category_list,
            max_articles_per_category=max_articles,
            auto_translate=auto_translate
        )
        
        return NewsResponse(
            success=True,
            message="Обновление новостей запущено в фоновом режиме",
            data=[],
            total=0
        )
        
    except Exception as e:
        logger.error(f"Error triggering manual news fetch: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при запуске обновления новостей"
        )

@router.get("/admin/statistics")
async def get_news_statistics(
    admin = Depends(get_current_admin_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Get news system statistics (admin only)"""
    try:
        stats = await news_service.get_news_statistics()
        
        return {
            "success": True,
            "data": stats.model_dump(),
            "message": "Статистика новостной системы получена"
        }
        
    except Exception as e:
        logger.error(f"Error getting news statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении статистики"
        )

@router.post("/admin/cleanup")
async def cleanup_old_news(
    days_old: int = Query(30, ge=7, le=365),
    admin = Depends(get_current_admin_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Clean up old news articles (admin only)"""
    try:
        deleted_count = await news_service.cleanup_old_articles(days_old)
        
        return {
            "success": True,
            "data": {"deleted_count": deleted_count},
            "message": f"Удалено {deleted_count} старых новостей (старше {days_old} дней)"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old news: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при очистке старых новостей"
        )

@router.get("/admin/jobs")
async def get_news_jobs(
    limit: int = Query(10, le=50),
    admin = Depends(get_current_admin_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Get news update job history (admin only)"""
    try:
        jobs = []
        cursor = news_service.jobs_collection.find().sort("started_at", -1).limit(limit)
        
        async for job_doc in cursor:
            jobs.append(NewsUpdateJob(**job_doc))
        
        return {
            "success": True,
            "data": [job.model_dump() for job in jobs],
            "message": f"Получено {len(jobs)} записей о задачах обновления новостей"
        }
        
    except Exception as e:
        logger.error(f"Error getting news jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении истории задач"
        )

@router.get("/admin/sources")
async def get_news_sources(
    admin = Depends(get_current_admin_user),
    news_service: NewsService = Depends(get_news_service)
):
    """Get news source configuration and status (admin only)"""
    try:
        service_status = await news_service.aggregator.get_service_status()
        
        sources_info = {
            "newsdata_io": {
                "name": "NewsData.io",
                "description": "Основной источник технологических новостей",
                "status": "active" if service_status["newsdata_io"]["available"] else "inactive",
                "requests_today": service_status["newsdata_io"]["requests_today"],
                "daily_limit": service_status["newsdata_io"]["daily_limit"],
                "categories": ["Technology", "Business", "Electronics"],
                "languages": ["English", "Русский (перевод)"]
            },
            "newsapi_org": {
                "name": "NewsAPI.org",
                "description": "Резервный источник новостей",
                "status": "active" if service_status["newsapi_org"]["available"] else "inactive",
                "requests_today": service_status["newsapi_org"]["requests_today"],
                "daily_limit": service_status["newsapi_org"]["daily_limit"],
                "categories": ["Technology", "Electronics", "Product Launches"],
                "languages": ["English", "Русский (перевод)"]
            }
        }
        
        return {
            "success": True,
            "data": sources_info,
            "message": "Информация об источниках новостей получена",
            "last_updated": service_status["last_updated"]
        }
        
    except Exception as e:
        logger.error(f"Error getting news sources: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении информации об источниках"
        )

@router.get("/health")
async def news_health_check():
    """Health check endpoint for news system"""
    try:
        return {
            "status": "healthy",
            "service": "news",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "news_aggregation",
                "russian_translation",
                "category_filtering",
                "search_functionality",
                "daily_updates"
            ]
        }
        
    except Exception as e:
        logger.error(f"News health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }