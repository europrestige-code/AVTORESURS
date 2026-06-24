# API Contracts - BuyAnywhere Russian Personal Shopping Service

## Frontend Mock Data Analysis
Current mock data in `/app/frontend/src/utils/mockData.js`:

### 1. Price Calculation Mock (`getPriceCalculation`)
**Mock Response:**
```javascript
{
  productName: 'iPhone 15 Pro 256GB',
  bestStore: 'Apple Store USA', 
  originalPrice: '116,403',
  commission: '11,640',
  shipping: '2,500',
  customs: '15,000', 
  insurance: '6,407',
  totalPrice: '152,050'
}
```

### 2. Popular Links Mock (`getPopularLinks`)
**Mock Data:** Pre-defined lists for each category (subscriptions, courses, brands, travel, electronics, digital)

### 3. Payment Methods Mock
**Mock Data:** Russian bank payment options (Sberbank, T-Bank, VTB, SBP)

## Backend Implementation Requirements

### API Endpoints to Implement

#### 1. `/api/calculate-price` (POST)
**Purpose:** AI-powered price calculation with real currency conversion

**Request Body:**
```json
{
  "input_type": "url|manual|photo",
  "url": "https://example.com/product", // if input_type = "url"
  "product_name": "iPhone 15 Pro", // if input_type = "manual"  
  "model": "A2848",
  "serial_number": "MTQN3LL/A",
  "description": "256GB, Natural Titanium",
  "photo_base64": "data:image/jpeg;base64,..." // if input_type = "photo"
}
```

**Response:**
```json
{
  "success": true,
  "product_name": "iPhone 15 Pro 256GB",
  "best_store": "Apple Store USA",
  "original_price_usd": 1199,
  "exchange_rate": 97,
  "original_price_rub": 116403,
  "commission": 11640,
  "shipping": 2500,
  "customs": 15000,
  "insurance": 6407,
  "total_price": 152050,
  "breakdown": {
    "original_price": "116,403 ₽",
    "commission": "11,640 ₽", 
    "shipping": "2,500 ₽",
    "customs": "15,000 ₽",
    "insurance": "6,407 ₽",
    "total_price": "152,050 ₽"
  }
}
```

#### 2. `/api/create-order` (POST)
**Purpose:** Create order and send SMS/email notifications

**Request Body:**
```json
{
  "calculation_id": "uuid",
  "customer_info": {
    "name": "Иван Иванов",
    "phone": "+79001234567",
    "email": "ivan@example.com"
  },
  "product_details": {
    "name": "iPhone 15 Pro 256GB",
    "url": "https://apple.com/iphone-15-pro",
    "total_price": 152050
  }
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "ORD-2024-001",
  "payment_instructions": "Переведите 152,050 ₽ на карту...",
  "sms_sent": true,
  "email_sent": true
}
```

#### 3. `/api/popular-services/:category` (GET)
**Purpose:** Get real popular links for each category

**Response:**
```json
{
  "category": "subscriptions",
  "services": [
    {
      "name": "Netflix",
      "description": "Фильмы и сериалы",
      "url": "netflix.com",
      "estimated_price": "от 1500 ₽/мес",
      "logo_url": "https://..."
    }
  ]
}
```

## Backend Integration Strategy

### 1. ChatGPT Integration
**File:** `/app/backend/services/ai_service.py`
- Price comparison and best store finder
- Product identification from photos
- URL analysis and product extraction

### 2. Currency Service
**File:** `/app/backend/services/currency_service.py`
- Google Exchange Rates API integration
- Apply -3 points risk coverage
- Cache rates for performance

### 3. Notification Service  
**File:** `/app/backend/services/notification_service.py`
- SMS to +79135533369
- Email notifications (when email provided)
- Order status updates

### 4. Database Models
**File:** `/app/backend/models/order.py`
```python
class Order:
    order_id: str
    customer_info: dict
    product_details: dict
    price_calculation: dict
    status: str  # "pending", "paid", "processing", "delivered"
    created_at: datetime
    notifications_sent: list
```

### 5. Frontend Integration Points

#### OrderForm Component Updates:
- Replace `mockData.getPriceCalculation()` with API call to `/api/calculate-price`
- Add loading states during calculation
- Handle API errors gracefully

#### Services Component Updates:
- Replace `mockData.getPopularLinks()` with API call to `/api/popular-services/:category`
- Cache popular services data

#### New Components:
- Order confirmation modal after price calculation
- Payment instructions display
- Order tracking (future enhancement)

## Environment Variables Needed
```
OPENAI_API_KEY=sk-...
GOOGLE_EXCHANGE_API_KEY=...
SMS_SERVICE_API_KEY=...
EMAIL_SERVICE_API_KEY=...
NOTIFICATION_PHONE=+79135533369
```

## Implementation Priority
1. **High Priority:** Price calculation with ChatGPT + currency conversion
2. **High Priority:** Order creation with SMS notifications  
3. **Medium Priority:** Popular services API endpoints
4. **Low Priority:** Advanced features (order tracking, payment integration)

This contract ensures seamless transition from mock data to real backend functionality while maintaining the existing frontend user experience.