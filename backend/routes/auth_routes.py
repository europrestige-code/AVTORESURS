from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User, UserLogin, UserRegister, UserResponse, UserRole, CustomerInfo
from services.auth_service import AuthService
from datetime import datetime
import logging

router = APIRouter(tags=["Authentication"])
security = HTTPBearer()
auth_service = AuthService()
logger = logging.getLogger(__name__)

# Database dependency - will be injected from main app
async def get_db():
    from server import db
    return db

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                          db = Depends(get_db)) -> User:
    """Get current authenticated user"""
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user_data = await db.users.find_one({"id": payload["user_id"]})
        
        if not user_data:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return User(**user_data)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Недействительный токен")

@router.post("/register")
async def register_user(user_data: UserRegister, db = Depends(get_db)):
    """Register new user"""
    try:
        # Validate registration data
        auth_service.validate_registration(user_data)
        
        # Check if user already exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": user_data.email},
                {"phone": user_data.phone}
            ]
        })
        
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="Пользователь с такой почтой или телефоном уже существует"
            )
        
        # Create new user
        customer_info = CustomerInfo(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            email=user_data.email
        )
        
        new_user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=auth_service.hash_password(user_data.password),
            role=UserRole.CUSTOMER,
            customer_info=customer_info
        )
        
        # Save to database
        await db.users.insert_one(new_user.dict())
        
        # Create session and token
        access_token = auth_service.create_access_token(new_user)
        session = auth_service.create_user_session(new_user)
        await db.user_sessions.insert_one(session.dict())
        
        logger.info(f"New user registered: {user_data.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=new_user.id,
                email=new_user.email,
                phone=new_user.phone,
                role=new_user.role,
                status=new_user.status,
                customer_info=new_user.customer_info,
                total_orders=new_user.total_orders,
                total_spent=new_user.total_spent,
                created_at=new_user.created_at,
                last_login=new_user.last_login
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")

@router.post("/login")
async def login_user(login_data: UserLogin, db = Depends(get_db)):
    """Login user"""
    try:
        # Find user
        user_data = await db.users.find_one({"email": login_data.email})
        
        if not user_data:
            raise HTTPException(status_code=400, detail="Неверная почта или пароль")
        
        user = User(**user_data)
        
        # Verify password
        if not auth_service.verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Неверная почта или пароль")
        
        # Update last login
        await db.users.update_one(
            {"id": user.id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create session and token
        access_token = auth_service.create_access_token(user)
        session = auth_service.create_user_session(user)
        await db.user_sessions.insert_one(session.dict())
        
        logger.info(f"User logged in: {login_data.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                email=user.email,
                phone=user.phone,
                role=user.role,
                status=user.status,
                customer_info=user.customer_info,
                total_orders=user.total_orders,
                total_spent=user.total_spent,
                created_at=user.created_at,
                last_login=datetime.utcnow()
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка входа")

@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user), db = Depends(get_db)):
    """Logout user"""
    try:
        # Deactivate user sessions
        await db.user_sessions.update_many(
            {"user_id": current_user.id, "is_active": True},
            {"$set": {"is_active": False}}
        )
        
        logger.info(f"User logged out: {current_user.email}")
        
        return {"message": "Успешный выход из системы"}
        
    except Exception as e:
        logger.error(f"Error logging out user: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка выхода")

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        status=current_user.status,
        customer_info=current_user.customer_info,
        total_orders=current_user.total_orders,
        total_spent=current_user.total_spent,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )