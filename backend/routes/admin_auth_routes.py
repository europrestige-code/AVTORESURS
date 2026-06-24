from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import logging

from utils.auth import authenticate_admin, create_admin_token, get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    
    try:
        # Authenticate admin
        user = authenticate_admin(request.email, request.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные данные для входа"
            )
        
        # Create access token
        access_token = create_admin_token(user)
        
        # Remove sensitive data from response
        user_response = {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "permissions": user["permissions"]
        }
        
        logger.info(f"Admin login successful: {user['email']}")
        
        return AdminLoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка входа в систему"
        )

@router.get("/me")
async def get_admin_profile(current_user: dict = Depends(get_current_admin_user)):
    """Get current admin user profile"""
    
    return {
        "email": current_user["email"],
        "role": current_user["role"],
        "permissions": current_user["permissions"]
    }

@router.post("/logout")
async def admin_logout(current_user: dict = Depends(get_current_admin_user)):
    """Admin logout endpoint"""
    
    # In a real implementation, you would invalidate the token
    # For now, just return success
    logger.info(f"Admin logout: {current_user['email']}")
    
    return {"message": "Выход выполнен успешно"}