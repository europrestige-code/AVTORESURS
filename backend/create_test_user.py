#!/usr/bin/env python3
"""
Script to create a test user for BuyAnywhere application
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from services.auth_service import AuthService
from models.user import User, UserRole, CustomerInfo
import uuid
from datetime import datetime

async def create_test_user():
    """Create a test user for authentication testing"""
    
    # Database connection
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Auth service
    auth_service = AuthService()
    
    # Test user data
    test_users = [
        {
            "email": "test@buyanywhere.com",
            "password": "password123",
            "first_name": "Тест",
            "last_name": "Пользователь",
            "phone": "+7 999 123 45 67"
        },
        {
            "email": "admin@buyanywhere.com", 
            "password": "admin123",
            "first_name": "Админ",
            "last_name": "Администратор",
            "phone": "+7 999 987 65 43"
        }
    ]
    
    for user_data in test_users:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data["email"]})
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping...")
            continue
        
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=user_data["email"],
            phone=user_data["phone"],
            password_hash=auth_service.hash_password(user_data["password"]),
            role=UserRole.CUSTOMER,
            customer_info=CustomerInfo(
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data["phone"],
                address="",
                city="Москва",
                country="Россия",
                postal_code=""
            ),
            created_at=datetime.utcnow(),
            last_login=None,
            total_orders=0,
            total_spent=0.0
        )
        
        # Insert into database
        await db.users.insert_one(user.dict())
        print(f"✅ Created test user: {user_data['email']} / {user_data['password']}")
    
    # Close connection
    client.close()
    print("\n🎉 Test users created successfully!")
    print("You can now login with:")
    print("📧 Email: test@buyanywhere.com")
    print("🔐 Password: password123")
    print("OR")
    print("📧 Email: admin@buyanywhere.com") 
    print("🔐 Password: admin123")

if __name__ == "__main__":
    asyncio.run(create_test_user())