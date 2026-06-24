from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Contact(BaseModel):
    """Individual contact within a company"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    personal_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    phone_number: Optional[str] = None
    is_primary: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Company(BaseModel):
    """Company record with multiple contacts"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    industry_category: Optional[str] = None  # AI-enhanced: MILK/DAIRY, etc.
    market_segment: Optional[str] = None  # B2B segmentation
    description: Optional[str] = None
    
    # Address information
    address_raw: Optional[str] = None
    address_formatted: Optional[str] = None  # Russian format
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "Russia"
    
    # Contact information
    contacts: List[Contact] = []
    main_phone: Optional[str] = None
    main_email: Optional[str] = None
    
    # Business information (AI-enhanced)
    annual_revenue: Optional[str] = None
    employee_count: Optional[str] = None
    business_type: Optional[str] = None  # B2B, B2C, etc.
    target_market: Optional[str] = None
    
    # CRM metadata
    source: str = "bulk_upload"
    status: str = "active"  # active, inactive, unsubscribed
    lead_score: Optional[int] = None
    tags: List[str] = []
    notes: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_contacted: Optional[datetime] = None

    @validator('contacts')
    def validate_contacts(cls, v):
        if v:
            # Ensure at least one primary contact
            primary_contacts = [c for c in v if c.is_primary]
            if not primary_contacts and v:
                v[0].is_primary = True
        return v

class BulkUploadRequest(BaseModel):
    """Request for bulk upload processing"""
    file_type: str  # csv, xlsx
    enhance_with_ai: bool = True
    market_research: bool = True
    classify_industries: bool = True
    deduplicate: bool = True
    source_name: Optional[str] = "bulk_upload"

class BulkUploadResult(BaseModel):
    """Result of bulk upload operation"""
    success: bool
    total_rows: int
    processed_companies: int
    new_companies: int
    updated_companies: int
    skipped_duplicates: int
    errors: List[str] = []
    warnings: List[str] = []
    ai_enhancements: int = 0
    processing_time: float
    
class CompanyMatch(BaseModel):
    """Company matching result for duplicate detection"""
    company_id: str
    match_confidence: float
    match_reasons: List[str]
    existing_company: Company

class AIEnhancementResult(BaseModel):
    """Result of AI enhancement for a company"""
    company_id: str
    enhancements: Dict[str, Any]
    confidence_score: float
    processing_time: float

# Industry categories for market segmentation
INDUSTRY_CATEGORIES = {
    "FOOD_BEVERAGE": [
        "milk", "dairy", "cheese", "yogurt", "food", "beverage", "restaurant", 
        "cafe", "bakery", "meat", "fish", "grocery", "supermarket"
    ],
    "TECHNOLOGY": [
        "software", "hardware", "it", "tech", "computer", "digital", "app", 
        "development", "programming", "ai", "automation"
    ],
    "MANUFACTURING": [
        "manufacturing", "factory", "production", "industrial", "machinery", 
        "equipment", "automotive", "construction", "engineering"
    ],
    "HEALTHCARE": [
        "medical", "healthcare", "hospital", "clinic", "pharmaceutical", 
        "therapy", "dental", "veterinary"
    ],
    "RETAIL": [
        "retail", "shop", "store", "commerce", "trading", "wholesale", 
        "distribution", "sales"
    ],
    "SERVICES": [
        "consulting", "finance", "banking", "insurance", "legal", "accounting", 
        "marketing", "advertising", "logistics", "transportation"
    ],
    "EDUCATION": [
        "education", "school", "university", "training", "learning", "academic"
    ],
    "REAL_ESTATE": [
        "real estate", "property", "housing", "development", "architecture"
    ],
    "ENERGY": [
        "energy", "oil", "gas", "renewable", "solar", "electricity", "power"
    ],
    "OTHER": []
}

MARKET_SEGMENTS = {
    "ENTERPRISE": "Large corporations (1000+ employees)",
    "SME": "Small and medium enterprises (50-999 employees)", 
    "SMALL_BUSINESS": "Small businesses (1-49 employees)",
    "STARTUP": "Startup companies",
    "GOVERNMENT": "Government and public sector",
    "NON_PROFIT": "Non-profit organizations"
}