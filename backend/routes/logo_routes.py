from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import Response
import os
import requests
from io import BytesIO
from PIL import Image, ImageOps
import base64
import uuid
from typing import Optional
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logo", tags=["logo"])

# Configuration
UPLOAD_DIR = "/app/backend/uploads/logos"
CURRENT_LOGO_PATH = "/app/backend/uploads/current_logo.png"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Remove.bg API configuration (you'll need to add REMOVE_BG_API_KEY to .env)
REMOVE_BG_API_URL = "https://api.remove.bg/v1.0/removebg"

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
    """Save processed logo as the current site logo"""
    try:
        # Validate file type
        if not logo.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")
        
        # Read and validate image
        image_data = await logo.read()
        
        # Create unique filename
        filename = f"logo_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(image_data)
        
        # Update current logo
        shutil.copy2(file_path, CURRENT_LOGO_PATH)
        
        logger.info(f"Logo saved successfully: {filename}")
        
        return {
            "success": True,
            "message": "Логотип успешно сохранен",
            "filename": filename,
            "logo_url": f"/api/logo/current"
        }
        
    except Exception as e:
        logger.error(f"Error saving logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения логотипа")

@router.get("/current")
async def get_current_logo():
    """Get the current site logo"""
    try:
        if os.path.exists(CURRENT_LOGO_PATH):
            with open(CURRENT_LOGO_PATH, "rb") as f:
                logo_data = f.read()
            
            return Response(
                content=logo_data,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=3600"
                }
            )
        else:
            # Return default logo or 404
            raise HTTPException(status_code=404, detail="Логотип не найден")
            
    except Exception as e:
        logger.error(f"Error retrieving current logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения логотипа")

@router.get("/list")
async def list_logos():
    """Get list of all uploaded logos"""
    try:
        logos = []
        
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    file_stats = os.stat(file_path)
                    
                    logos.append({
                        "filename": filename,
                        "size": file_stats.st_size,
                        "created": file_stats.st_ctime,
                        "url": f"/api/logo/file/{filename}"
                    })
        
        return {
            "success": True,
            "logos": sorted(logos, key=lambda x: x['created'], reverse=True)
        }
        
    except Exception as e:
        logger.error(f"Error listing logos: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка логотипов")

@router.get("/file/{filename}")
async def get_logo_file(filename: str):
    """Get specific logo file"""
    try:
        # Validate filename (security)
        if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise HTTPException(status_code=400, detail="Неверное имя файла")
        
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Determine media type
        if filename.lower().endswith('.png'):
            media_type = "image/png"
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            media_type = "image/jpeg"
        elif filename.lower().endswith('.gif'):
            media_type = "image/gif"
        else:
            media_type = "application/octet-stream"
        
        return Response(
            content=file_data,
            media_type=media_type,
            headers={
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving logo file: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения файла")

@router.delete("/file/{filename}")
async def delete_logo(filename: str):
    """Delete a specific logo file"""
    try:
        # Validate filename (security)
        if not filename.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise HTTPException(status_code=400, detail="Неверное имя файла")
        
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        os.remove(file_path)
        
        return {
            "success": True,
            "message": f"Логотип {filename} удален"
        }
        
    except Exception as e:
        logger.error(f"Error deleting logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка удаления логотипа")