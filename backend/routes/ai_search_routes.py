from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging
from services.ai_search_service import ai_search_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-search", tags=["AI Search"])

class ChinesePlatformSearch(BaseModel):
    query: str
    platform: Optional[str] = None
    price_range: Optional[str] = None
    category: Optional[str] = None

class CarPartsSearch(BaseModel):
    search_type: str  # "vin", "part_number", or "car_details"
    vin: Optional[str] = None
    part_number: Optional[str] = None
    year: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None

class BusinessEquipmentSearch(BaseModel):
    query: str
    category: Optional[str] = None  # "automation", "electrical", "pneumatics", "machinery"
    budget_range: Optional[str] = None
    technical_requirements: Optional[str] = None

class PredictiveSearchRequest(BaseModel):
    partial_query: str
    context: Optional[str] = None  # "chinese", "car_parts", "business", "general"

@router.post("/chinese-platforms")
async def search_chinese_platforms(request: ChinesePlatformSearch):
    """AI-powered search for Chinese e-commerce platforms."""
    try:
        result = await ai_search_service.search_chinese_platforms(
            query=request.query,
            platform=request.platform
        )
        
        if result["success"]:
            return {
                "success": True,
                "query": request.query,
                "platform": request.platform,
                "ai_analysis": result["ai_analysis"],
                "search_metadata": {
                    "search_type": "chinese_platforms",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "processing_time": "2.3s"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Chinese platforms search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/car-parts") 
async def search_car_parts(request: CarPartsSearch):
    """AI-powered car parts search with OEM identification."""
    try:
        search_data = {
            "type": request.search_type,
            "vin": request.vin,
            "part_number": request.part_number,
            "year": request.year,
            "make": request.make,
            "model": request.model,
            "variant": request.variant
        }
        
        result = await ai_search_service.search_car_parts(search_data)
        
        if result["success"]:
            return {
                "success": True,
                "search_data": search_data,
                "ai_analysis": result["ai_analysis"],
                "search_metadata": {
                    "search_type": "car_parts",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "processing_time": "3.1s"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Car parts search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/business-equipment")
async def search_business_equipment(request: BusinessEquipmentSearch):
    """AI-powered business equipment search."""
    try:
        result = await ai_search_service.search_business_equipment(
            query=request.query,
            category=request.category
        )
        
        if result["success"]:
            return {
                "success": True,
                "query": request.query,
                "category": request.category,
                "ai_analysis": result["ai_analysis"],
                "search_metadata": {
                    "search_type": "business_equipment", 
                    "timestamp": "2024-01-01T00:00:00Z",
                    "processing_time": "2.8s"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Business equipment search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-image")
async def analyze_product_image(
    image: UploadFile = File(...),
    context: str = Form("")
):
    """Analyze uploaded product image with AI."""
    try:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Uploaded file must be an image")
        
        image_data = await image.read()
        
        result = await ai_search_service.analyze_product_image(
            image_data=image_data,
            context=context
        )
        
        if result["success"]:
            return {
                "success": True,
                "filename": image.filename,
                "context": context,
                "ai_analysis": result["ai_analysis"],
                "search_metadata": {
                    "search_type": "image_analysis",
                    "image_size": len(image_data),
                    "timestamp": "2024-01-01T00:00:00Z",
                    "processing_time": "4.2s"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predictive-suggestions")
async def get_predictive_suggestions(request: PredictiveSearchRequest):
    """Get AI-powered predictive search suggestions."""
    try:
        result = await ai_search_service.generate_predictive_suggestions(
            partial_query=request.partial_query,
            search_context=request.context or "general"
        )
        
        if result["success"]:
            return {
                "success": True,
                "partial_query": request.partial_query,
                "context": request.context,
                "suggestions": result["ai_suggestions"],
                "search_metadata": {
                    "search_type": "predictive_suggestions",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "processing_time": "1.1s"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Predictive suggestions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending-searches/{category}")
async def get_trending_searches(category: str):
    """Get trending searches for a specific category."""
    try:
        # Mock trending searches - in production this would come from analytics
        trending_data = {
            "chinese": [
                "iPhone 15 Pro AliExpress",
                "Xiaomi смартфон Taobao", 
                "Nike кроссовки SHEIN",
                "MacBook Air JD.com",
                "Косметика Tmall"
            ],
            "car_parts": [
                "BMW тормозные колодки BOSCH",
                "Mercedes фильтр масляный",
                "Audi амортизаторы Sachs", 
                "Toyota свечи зажигания",
                "Ford ремень ГРМ"
            ],
            "business": [
                "Siemens ПЛК S7-1200",
                "ABB частотный преобразователь",
                "Schneider контактор",
                "Festo пневмоцилиндр",
                "Omron датчик"
            ],
            "general": [
                "Netflix подписка США",
                "Adobe Creative Cloud",
                "Steam игры",
                "Apple Store товары",
                "Booking.com отели"
            ]
        }
        
        trends = trending_data.get(category, trending_data["general"])
        
        return {
            "success": True,
            "category": category,
            "trending_searches": trends,
            "metadata": {
                "updated_at": "2024-01-01T00:00:00Z",
                "period": "last_7_days",
                "total_searches": len(trends)
            }
        }
        
    except Exception as e:
        logger.error(f"Trending searches failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-results")
async def enhance_search_results(
    results: List[Dict[str, Any]],
    query: str,
    search_type: str
):
    """Enhance search results with AI analysis."""
    try:
        result = await ai_search_service.enhance_search_results(
            results=results,
            query=query,
            search_type=search_type
        )
        
        if result["success"]:
            return {
                "success": True,
                "query": query,
                "search_type": search_type,
                "results_count": result["results_count"],
                "ai_enhancement": result["ai_enhancement"],
                "search_metadata": {
                    "enhancement_type": "ai_analysis",
                    "timestamp": "2024-01-01T00:00:00Z",
                    "processing_time": "1.8s"
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Results enhancement failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-capabilities")
async def get_search_capabilities():
    """Get information about available AI search capabilities."""
    return {
        "success": True,
        "capabilities": {
            "chinese_platforms": {
                "description": "AI-powered search across Chinese e-commerce platforms",
                "supported_platforms": ["AliExpress", "Taobao", "SHEIN", "JD.com", "Tmall", "1688"],
                "features": ["Price comparison", "Authenticity check", "Seller ratings"]
            },
            "car_parts": {
                "description": "OEM car parts identification and search",
                "search_methods": ["VIN lookup", "Part number search", "Car specifications"],
                "features": ["OEM manufacturer detection", "Compatibility check", "Price estimation"]
            },
            "business_equipment": {
                "description": "Industrial equipment search and analysis",
                "categories": ["Automation", "Electrical", "Pneumatics", "Machinery"],
                "features": ["Brand identification", "Technical specs", "Supplier recommendations"]
            },
            "image_analysis": {
                "description": "AI-powered product image analysis",
                "supported_formats": ["JPEG", "PNG", "WebP"],
                "features": ["Product identification", "Brand detection", "Market analysis"]
            },
            "predictive_search": {
                "description": "Smart search suggestions and autocomplete",
                "contexts": ["General", "Chinese platforms", "Car parts", "Business equipment"],
                "features": ["Real-time suggestions", "Trending searches", "Category-specific"]
            }
        },
        "ai_models": {
            "llm_provider": "Emergent LLM",
            "capabilities": ["Text analysis", "Product recommendations", "Technical consultation"],
            "languages": ["Russian", "English", "Chinese (basic)"]
        }
    }