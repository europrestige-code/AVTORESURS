import os
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from models.user import User, UserLogin, UserRegister, UserSession, UserRole
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'buyanywhere-secret-key-2024')
        self.algorithm = 'HS256'
        self.access_token_expire_minutes = 1440  # 24 hours
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен истёк"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен"
            )
    
    def validate_registration(self, user_data: UserRegister) -> None:
        """Validate user registration data"""
        if user_data.password != user_data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароли не совпадают"
            )
        
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль должен содержать минимум 6 символов"
            )
        
        # Phone validation (Russian format)
        if not user_data.phone.startswith('+7') and not user_data.phone.startswith('8'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Введите корректный российский номер телефона"
            )
    
    def create_user_session(self, user: User) -> UserSession:
        """Create user session"""
        expire_time = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        session = UserSession(
            user_id=user.id,
            user_email=user.email,
            user_role=user.role,
            expires_at=expire_time
        )
        
        return session
    
    def get_admin_permissions(self, role: UserRole) -> list:
        """Get permissions based on user role"""
        permissions = {
            UserRole.ADMIN: [
                'view_all_orders',
                'edit_orders',
                'manage_users',
                'view_reports',
                'manage_settings',
                'send_notifications'
            ],
            UserRole.MANAGER: [
                'view_all_orders',
                'edit_orders',
                'view_reports',
                'send_notifications'
            ],
            UserRole.LOGISTICS: [
                'view_assigned_orders',
                'update_shipping_status',
                'view_logistics_reports'
            ],
            UserRole.CUSTOMER: [
                'view_own_orders',
                'create_orders'
            ]
        }
        
        return permissions.get(role, [])
    
    def check_permission(self, user_role: UserRole, required_permission: str) -> bool:
        """Check if user has required permission"""
        user_permissions = self.get_admin_permissions(user_role)
        return required_permission in user_permissions