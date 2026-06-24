from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
import os
import logging
from typing import List, Optional

from models.crm_bulk import BulkUploadRequest, BulkUploadResult, MARKET_SEGMENTS, INDUSTRY_CATEGORIES
from services.crm_bulk_service import CRMBulkService
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm/bulk", tags=["crm-bulk"])

# Dependency to get database
async def get_database() -> AsyncIOMotorDatabase:
    from server import db  # Import from main server module
    return db

@router.post("/upload")
async def upload_bulk_data(
    file: UploadFile = File(...),
    enhance_with_ai: bool = Form(True),
    market_research: bool = Form(True),
    classify_industries: bool = Form(True),
    deduplicate: bool = Form(True),
    source_name: Optional[str] = Form("bulk_upload"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Upload and process bulk CRM data from CSV or Excel file"""
    
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый формат файла. Поддерживаются: CSV, XLSX, XLS"
            )
        
        # Validate file size (50MB max)
        file_content = await file.read()
        if len(file_content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Файл слишком большой (максимум 50МБ)"
            )
        
        # Determine file type
        file_type = "xlsx" if file.filename.lower().endswith(('.xlsx', '.xls')) else "csv"
        
        # Create upload request
        upload_request = BulkUploadRequest(
            file_type=file_type,
            enhance_with_ai=enhance_with_ai,
            market_research=market_research,
            classify_industries=classify_industries,
            deduplicate=deduplicate,
            source_name=source_name
        )
        
        # Process upload
        bulk_service = CRMBulkService(db)
        result = await bulk_service.process_bulk_upload(
            file_content, 
            file.filename, 
            upload_request
        )
        
        logger.info(f"Bulk upload processed: {result.processed_companies} companies")
        
        return {
            "success": result.success,
            "message": f"Обработано компаний: {result.processed_companies}",
            "details": {
                "total_rows": result.total_rows,
                "processed_companies": result.processed_companies,
                "new_companies": result.new_companies,
                "updated_companies": result.updated_companies,
                "skipped_duplicates": result.skipped_duplicates,
                "ai_enhancements": result.ai_enhancements,
                "processing_time": f"{result.processing_time:.2f}s",
                "errors": result.errors,
                "warnings": result.warnings
            }
        }
        
    except Exception as e:
        logger.error(f"Error in bulk upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки файла: {str(e)}"
        )

@router.get("/template")
async def get_upload_template(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get template and example data for bulk upload"""
    
    try:
        bulk_service = CRMBulkService(db)
        template = await bulk_service.get_upload_template()
        
        return {
            "success": True,
            "template": template,
            "instructions": {
                "ru": {
                    "title": "Инструкция по загрузке данных CRM",
                    "steps": [
                        "Скачайте шаблон CSV или создайте Excel файл с указанными колонками",
                        "Заполните обязательные поля: Название компании, Телефон, Email, Веб-сайт",
                        "Добавьте контактные данные: Имя, Должность, Отдел, Мобильный",
                        "Можно загружать несколько контактов для одной компании",
                        "Система автоматически найдет дубликаты и улучшит данные с помощью ИИ",
                        "Поддерживаются форматы: CSV, XLSX, XLS (максимум 50МБ)"
                    ]
                }
            },
            "sample_csv": "company_name,website,contact_name,position,department,email,phone,mobile,address,city,region\nООО Молочные продукты,https://milk-products.ru,Иван Петров,Генеральный директор,Управление,ivan@milk-products.ru,+7 495 123-45-67,+7 903 123-45-67,ул. Ленина дом 1,Москва,Московская область"
        }
        
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения шаблона: {str(e)}"
        )

@router.get("/segments")
async def get_market_segments():
    """Get available market segments for filtering"""
    
    return {
        "success": True,
        "market_segments": MARKET_SEGMENTS,
        "industry_categories": {
            category: {
                "name": category,
                "keywords": keywords[:5]  # Show first 5 keywords as examples
            }
            for category, keywords in INDUSTRY_CATEGORIES.items()
        }
    }

@router.get("/companies/by-segment/{segment}")
async def get_companies_by_segment(
    segment: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get companies filtered by market segment"""
    
    try:
        if segment not in MARKET_SEGMENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Неизвестный сегмент: {segment}"
            )
        
        bulk_service = CRMBulkService(db)
        companies = await bulk_service.get_companies_by_segment(segment)
        
        return {
            "success": True,
            "segment": segment,
            "segment_description": MARKET_SEGMENTS[segment],
            "count": len(companies),
            "companies": companies
        }
        
    except Exception as e:
        logger.error(f"Error getting companies by segment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения компаний по сегменту: {str(e)}"
        )

@router.get("/companies/by-industry/{industry}")
async def get_companies_by_industry(
    industry: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get companies filtered by industry category"""
    
    try:
        if industry not in INDUSTRY_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Неизвестная отрасль: {industry}"
            )
        
        bulk_service = CRMBulkService(db)
        companies = await bulk_service.get_companies_by_industry(industry)
        
        return {
            "success": True,
            "industry": industry,
            "count": len(companies),
            "companies": companies
        }
        
    except Exception as e:
        logger.error(f"Error getting companies by industry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения компаний по отрасли: {str(e)}"
        )

@router.get("/statistics")
async def get_bulk_upload_statistics(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get statistics about uploaded companies and segments"""
    
    try:
        companies_collection = db.companies
        
        # Total companies
        total_companies = await companies_collection.count_documents({})
        
        # Companies by source
        bulk_companies = await companies_collection.count_documents({"source": "bulk_upload"})
        
        # Companies by market segment
        segment_stats = {}
        for segment in MARKET_SEGMENTS.keys():
            count = await companies_collection.count_documents({"market_segment": segment})
            segment_stats[segment] = count
        
        # Companies by industry
        industry_stats = {}
        for industry in INDUSTRY_CATEGORIES.keys():
            count = await companies_collection.count_documents({"industry_category": industry})
            industry_stats[industry] = count
        
        # Companies with AI enhancements
        enhanced_companies = await companies_collection.count_documents({
            "description": {"$exists": True, "$ne": ""}
        })
        
        return {
            "success": True,
            "statistics": {
                "total_companies": total_companies,
                "bulk_uploaded": bulk_companies,
                "ai_enhanced": enhanced_companies,
                "by_market_segment": segment_stats,
                "by_industry": industry_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения статистики: {str(e)}"
        )

@router.delete("/companies/{company_id}")
async def delete_company(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a company and its contacts"""
    
    try:
        companies_collection = db.companies
        contacts_collection = db.contacts
        
        # Check if company exists
        company = await companies_collection.find_one({"id": company_id})
        if not company:
            raise HTTPException(
                status_code=404,
                detail="Компания не найдена"
            )
        
        # Delete company and its contacts
        await companies_collection.delete_one({"id": company_id})
        await contacts_collection.delete_many({"company_id": company_id})
        
        return {
            "success": True,
            "message": f"Компания '{company['company_name']}' удалена"
        }
        
    except Exception as e:
        logger.error(f"Error deleting company: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка удаления компании: {str(e)}"
        )

@router.post("/companies/{company_id}/unsubscribe")
async def unsubscribe_company(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Mark company as unsubscribed"""
    
    try:
        companies_collection = db.companies
        
        result = await companies_collection.update_one(
            {"id": company_id},
            {
                "$set": {
                    "status": "unsubscribed",
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Компания не найдена"
            )
        
        return {
            "success": True,
            "message": "Компания отписана от рассылки"
        }
        
    except Exception as e:
        logger.error(f"Error unsubscribing company: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка отписки компании: {str(e)}"
        )