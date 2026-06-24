from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User, UserRole
from models.order import Order
from typing import List, Optional
from datetime import datetime
import logging

router = APIRouter(tags=["Customer Dashboard"])
logger = logging.getLogger(__name__)

# Database dependency - will be injected from main app
async def get_db():
    from server import db
    return db

# Import get_current_user from auth routes
from routes.auth_routes import get_current_user

@router.get("/dashboard")
async def get_customer_dashboard(current_user: User = Depends(get_current_user), 
                               db = Depends(get_db)):
    """Get customer dashboard data"""
    try:
        if current_user.role != UserRole.CUSTOMER:
            raise HTTPException(status_code=403, detail="Доступно только для клиентов")
        
        # Get user orders
        orders_cursor = db.orders.find({"customer_info.email": current_user.email})
        orders = await orders_cursor.to_list(length=100)
        
        # Calculate statistics
        total_orders = len(orders)
        total_spent = sum(order.get('price_calculation', {}).get('total_rub', 0) for order in orders)
        
        # Group orders by status
        orders_by_status = {}
        for order in orders:
            status = order.get('status', 'unknown')
            if status not in orders_by_status:
                orders_by_status[status] = 0
            orders_by_status[status] += 1
        
        # Recent orders (last 10)
        recent_orders = sorted(orders, key=lambda x: x.get('created_at', datetime.min), reverse=True)[:10]
        
        # Format orders for frontend
        formatted_orders = []
        for order in recent_orders:
            formatted_order = {
                "order_id": order.get('order_id', ''),
                "product_name": order.get('product_details', {}).get('name', 'Unknown'),
                "amount": order.get('price_calculation', {}).get('total_rub', 0),
                "status": order.get('status', 'unknown'),
                "created_at": order.get('created_at', datetime.utcnow()).isoformat(),
                "payment_status": "completed" if order.get('status') in ['paid', 'processing', 'shipped', 'delivered'] else "pending"
            }
            formatted_orders.append(formatted_order)
        
        return {
            "user_info": {
                "name": f"{current_user.customer_info.first_name} {current_user.customer_info.last_name}",
                "email": current_user.email,
                "phone": current_user.phone,
                "member_since": current_user.created_at.isoformat()
            },
            "statistics": {
                "total_orders": total_orders,
                "total_spent": total_spent,
                "orders_by_status": orders_by_status,
                "avg_order_value": total_spent / total_orders if total_orders > 0 else 0
            },
            "recent_orders": formatted_orders
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")

@router.get("/orders")
async def get_customer_orders(page: int = 1, limit: int = 20, 
                            status: Optional[str] = None,
                            current_user: User = Depends(get_current_user),
                            db = Depends(get_db)):
    """Get customer orders with pagination"""
    try:
        if current_user.role != UserRole.CUSTOMER:
            raise HTTPException(status_code=403, detail="Доступно только для клиентов")
        
        # Build query
        query = {"customer_info.email": current_user.email}
        if status:
            query["status"] = status
        
        # Get total count
        total_orders = await db.orders.count_documents(query)
        
        # Get paginated orders
        skip = (page - 1) * limit
        orders_cursor = db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit)
        orders = await orders_cursor.to_list(length=limit)
        
        # Format orders
        formatted_orders = []
        for order in orders:
            formatted_order = {
                "order_id": order.get('order_id', ''),
                "product_name": order.get('product_details', {}).get('name', 'Unknown'),
                "product_url": order.get('product_details', {}).get('url', ''),
                "store_name": order.get('price_calculation', {}).get('store_name', ''),
                "amount": order.get('price_calculation', {}).get('total_rub', 0),
                "status": order.get('status', 'unknown'),
                "payment_status": "completed" if order.get('status') in ['paid', 'processing', 'shipped', 'delivered'] else "pending",
                "created_at": order.get('created_at', datetime.utcnow()).isoformat(),
                "estimated_delivery": None,  # Would be calculated based on shipping
                "tracking_number": order.get('tracking_number'),
                "price_breakdown": {
                    "original_price": order.get('price_calculation', {}).get('original_price_rub', 0),
                    "commission": order.get('price_calculation', {}).get('commission_rub', 0),
                    "shipping": order.get('price_calculation', {}).get('shipping_rub', 0),
                    "customs": order.get('price_calculation', {}).get('customs_rub', 0),
                    "insurance": order.get('price_calculation', {}).get('insurance_rub', 0)
                }
            }
            formatted_orders.append(formatted_order)
        
        return {
            "orders": formatted_orders,
            "pagination": {
                "current_page": page,
                "total_pages": (total_orders + limit - 1) // limit,
                "total_orders": total_orders,
                "has_next": (page * limit) < total_orders,
                "has_prev": page > 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения заказов")

@router.get("/orders/{order_id}")
async def get_order_details(order_id: str, 
                          current_user: User = Depends(get_current_user),
                          db = Depends(get_db)):
    """Get detailed order information"""
    try:
        if current_user.role != UserRole.CUSTOMER:
            raise HTTPException(status_code=403, detail="Доступно только для клиентов")
        
        # Find order
        order = await db.orders.find_one({
            "order_id": order_id,
            "customer_info.email": current_user.email
        })
        
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Get order timeline
        timeline_cursor = db.order_timeline.find({"order_id": order_id, "is_visible_to_customer": True})
        timeline = await timeline_cursor.to_list(length=100)
        
        formatted_timeline = [
            {
                "status": entry.get('status', ''),
                "description": entry.get('description', ''),
                "created_at": entry.get('created_at', datetime.utcnow()).isoformat()
            }
            for entry in sorted(timeline, key=lambda x: x.get('created_at', datetime.min))
        ]
        
        # Format detailed order
        detailed_order = {
            "order_id": order.get('order_id', ''),
            "product_details": {
                "name": order.get('product_details', {}).get('name', 'Unknown'),
                "description": order.get('product_details', {}).get('description', ''),
                "url": order.get('product_details', {}).get('url', ''),
                "image_url": order.get('product_details', {}).get('image_url', '')
            },
            "store_info": {
                "name": order.get('price_calculation', {}).get('store_name', ''),
                "url": order.get('product_details', {}).get('url', '')
            },
            "price_breakdown": {
                "original_price": order.get('price_calculation', {}).get('original_price_rub', 0),
                "commission": order.get('price_calculation', {}).get('commission_rub', 0),
                "shipping": order.get('price_calculation', {}).get('shipping_rub', 0),
                "customs": order.get('price_calculation', {}).get('customs_rub', 0),
                "insurance": order.get('price_calculation', {}).get('insurance_rub', 0),
                "total": order.get('price_calculation', {}).get('total_rub', 0),
                "currency_rate": order.get('price_calculation', {}).get('exchange_rate', 0)
            },
            "status_info": {
                "current_status": order.get('status', 'unknown'),
                "payment_status": "completed" if order.get('status') in ['paid', 'processing', 'shipped', 'delivered'] else "pending",
                "tracking_number": order.get('tracking_number'),
                "estimated_delivery": None
            },
            "dates": {
                "created_at": order.get('created_at', datetime.utcnow()).isoformat(),
                "paid_at": order.get('paid_at'),
                "shipped_at": order.get('shipped_at'),
                "delivered_at": order.get('delivered_at')
            },
            "timeline": formatted_timeline
        }
        
        return detailed_order
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order details: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка получения деталей заказа")

@router.put("/profile")
async def update_customer_profile(profile_data: dict,
                                current_user: User = Depends(get_current_user),
                                db = Depends(get_db)):
    """Update customer profile"""
    try:
        if current_user.role != UserRole.CUSTOMER:
            raise HTTPException(status_code=403, detail="Доступно только для клиентов")
        
        # Update allowed fields
        update_data = {}
        if 'first_name' in profile_data:
            update_data['customer_info.first_name'] = profile_data['first_name']
        if 'last_name' in profile_data:
            update_data['customer_info.last_name'] = profile_data['last_name']
        if 'phone' in profile_data:
            update_data['phone'] = profile_data['phone']
            update_data['customer_info.phone'] = profile_data['phone']
        if 'address' in profile_data:
            update_data['customer_info.address'] = profile_data['address']
        if 'city' in profile_data:
            update_data['customer_info.city'] = profile_data['city']
        
        update_data['updated_at'] = datetime.utcnow()
        
        # Update user
        await db.users.update_one(
            {"id": current_user.id},
            {"$set": update_data}
        )
        
        logger.info(f"Profile updated for user: {current_user.email}")
        
        return {"message": "Профиль успешно обновлён"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка обновления профиля")