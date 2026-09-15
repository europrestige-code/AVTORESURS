from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import Response
import os
import requests
from io import BytesIO
from PIL import Image, ImageOps
import base64
import uuid
from datetime import datetime
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logo", tags=["logo"])

# Remove.bg API configuration (you'll need to add REMOVE_BG_API_KEY to .env)
REMOVE_BG_API_URL = "https://api.remove.bg/v1.0/removebg"


async def _get_db():
    """Late-imported MongoDB handle so this module has no import cycle."""
    from server import db
    return db

async def remove_background_with_api(image_data: bytes) -> Optional[bytes]:
    """Remove background using remove.bg API"""
    try:
        api_key = os.getenv('REMOVE_BG_API_KEY')
        if not api_key:
            logger.warning("REMOVE_BG_API_KEY not found in environment")
            return None
            
        response = requests.post(
            REMOVE_BG_API_URL,
            files={'image_file': image_data},
            data={'size': 'auto'},
            headers={'X-Api-Key': api_key},
            timeout=30
        )
        
        if response.status_code == requests.codes.ok:
            logger.info("Background removed successfully with remove.bg API")
            return response.content
        else:
            logger.error(f"remove.bg API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error with remove.bg API: {str(e)}")
        return None

async def remove_background_local(image_data: bytes) -> bytes:
    """Fallback local background removal using PIL"""
    try:
        # Open image
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGBA if not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get image data
        data = image.getdata()
        
        # Simple background removal - convert white/light colors to transparent
        # This is a basic approach, real AI removal would be much better
        new_data = []
        for item in data:
            # If pixel is close to white, make it transparent
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))  # Transparent
            else:
                new_data.append(item)
        
        # Update image
        image.putdata(new_data)
        
        # Save to bytes
        output = BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error with local background removal: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка обработки изображения")

@router.post("/remove-background")
async def remove_background(image: UploadFile = File(...)):
    """Remove background from uploaded image"""
    try:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")
        
        # Read image data
        image_data = await image.read()
        
        # Validate file size (10MB max)
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Файл слишком большой (максимум 10МБ)")
        
        # Try remove.bg API first, then fallback to local processing
        processed_data = await remove_background_with_api(image_data)
        
        if processed_data is None:
            logger.info("Using local background removal as fallback")
            processed_data = await remove_background_local(image_data)
        
        # Return processed image
        return Response(
            content=processed_data,
            media_type="image/png",
            headers={
                "Content-Disposition": "attachment; filename=logo-transparent.png"
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing background removal: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка обработки изображения")

@router.post("/save")
async def save_logo(logo: UploadFile = File(...)):
    """Save processed logo as the current site logo (stored in Mongo)."""
    try:
        if not logo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")
        image_data = await logo.read()
        filename = f"logo_{uuid.uuid4().hex[:8]}.png"
        db = await _get_db()
        # Mark all existing logos as non-current, then insert new one as current.
        await db.logo_uploads.update_many({"is_current": True}, {"$set": {"is_current": False}})
        await db.logo_uploads.insert_one({
            "filename": filename,
            "data": image_data,
            "content_type": "image/png",
            "size": len(image_data),
            "created_at": datetime.utcnow(),
            "is_current": True,
        })
        logger.info(f"Logo saved successfully: {filename}")
        return {
            "success": True,
            "message": "Логотип успешно сохранен",
            "filename": filename,
            "logo_url": "/api/logo/current",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения логотипа")

@router.get("/current")
async def get_current_logo():
    """Get the current site logo from Mongo."""
    try:
        db = await _get_db()
        doc = await db.logo_uploads.find_one({"is_current": True}, sort=[("created_at", -1)])
        if not doc:
            raise HTTPException(status_code=404, detail="Логотип не найден")
        return Response(
            content=doc["data"],
            media_type=doc.get("content_type", "image/png"),
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving current logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения логотипа")

@router.get("/list")
async def list_logos():
    """Get list of all uploaded logos from Mongo."""
    try:
        db = await _get_db()
        logos = []
        async for doc in db.logo_uploads.find({}, {"data": 0}).sort("created_at", -1):
            logos.append({
                "filename": doc.get("filename"),
                "size": doc.get("size", 0),
                "created": doc.get("created_at").timestamp() if doc.get("created_at") else 0,
                "url": f"/api/logo/file/{doc.get('filename')}",
            })
        return {"success": True, "logos": logos}
    except Exception as e:
        logger.error(f"Error listing logos: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка логотипов")

@router.get("/file/{filename}")
async def get_logo_file(filename: str):
    """Get specific logo file from Mongo."""
    try:
        if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise HTTPException(status_code=400, detail="Неверное имя файла")
        db = await _get_db()
        doc = await db.logo_uploads.find_one({"filename": filename})
        if not doc:
            raise HTTPException(status_code=404, detail="Файл не найден")
        return Response(
            content=doc["data"],
            media_type=doc.get("content_type", "image/png"),
            headers={"Cache-Control": "public, max-age=3600"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving logo file: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения файла")

@router.delete("/file/{filename}")
async def delete_logo(filename: str):
    """Delete a specific logo file from Mongo."""
    try:
        if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise HTTPException(status_code=400, detail="Неверное имя файла")
        db = await _get_db()
        r = await db.logo_uploads.delete_one({"filename": filename})
        if r.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Файл не найден")
        return {"success": True, "message": f"Логотип {filename} удален"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка удаления логотипа")