from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

security = HTTPBearer()

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "buyanywhere-super-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Admin users - in production, this would be in database
ADMIN_USERS = {
    "admin@buyanywhere.com": {
        "email": "admin@buyanywhere.com",
        "name": "BuyAnywhere Admin",
        "role": "admin",
        "permissions": ["payment_config", "user_management", "orders", "analytics"]
    },
    "demo@buyanywhere.com": {
        "email": "demo@buyanywhere.com", 
        "name": "Demo Admin",
        "role": "admin",
        "permissions": ["payment_config", "orders"]
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
        # In production, fetch user from database
        # For now, return basic user info
        return {
            "email": email,
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", [])
        }
        
    except JWTError:
        raise credentials_exception

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """Get current admin user with admin permissions"""
    
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    return current_user

async def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from token for customer routes"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Use the same secret key as auth service
        auth_secret_key = os.environ.get('JWT_SECRET_KEY', 'buyanywhere-secret-key-2024')
        
        # Decode token using the same method as auth service
        import jwt as pyjwt  # Use the same jwt library as auth service
        payload = pyjwt.decode(credentials.credentials, auth_secret_key, algorithms=["HS256"])
        
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role", "customer")
        
        if not user_id or not email:
            raise credentials_exception
            
        # Return user info for customer payment routes
        return {
            "id": user_id,
            "email": email,
            "role": role,
            "permissions": payload.get("permissions", [])
        }
        
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк"
        )
    except pyjwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен"
        )

def authenticate_admin(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate admin user"""
    
    # For demo purposes, accept any password for admin users
    # In production, implement proper password verification
    if email in ADMIN_USERS:
        return ADMIN_USERS[email]
    
    return None

def create_admin_token(user_data: Dict[str, Any]) -> str:
    """Create admin access token"""
    
    token_data = {
        "sub": user_data["email"],
        "role": user_data["role"],
        "permissions": user_data["permissions"],
        "name": user_data["name"]
    }
    
    return create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )