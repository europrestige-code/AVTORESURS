import os
import asyncio
import pandas as pd
import io
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase
from models.crm_bulk import (
    Company, Contact, BulkUploadResult, CompanyMatch,
    BulkUploadRequest, MARKET_SEGMENTS
)
from services.crm_ai_service import CRMAIService

logger = logging.getLogger(__name__)

class CRMBulkService:
    """Service for handling bulk CRM data uploads and processing"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.companies_collection = db.companies
        self.contacts_collection = db.contacts
        self.ai_service = CRMAIService()
        
        # Field mapping for various CSV/Excel formats
        self.field_mappings = {
            'company': [
                'company_name', 'company', 'business_name', 'organization', 
                'firm', 'enterprise', 'название компании', 'компания'
            ],
            'website': [
                'website', 'site', 'url', 'web', 'homepage', 'веб-сайт', 'сайт'
            ],
            'email': [
                'email', 'e-mail', 'mail', 'contact_email', 'email_address',
                'электронная почта', 'имейл'
            ],
            'phone': [
                'phone', 'telephone', 'tel', 'phone_number', 'contact_number',
                'телефон', 'номер телефона'
            ],
            'mobile': [
                'mobile', 'cell', 'cellular', 'mobile_phone', 'мобильный'
            ],
            'contact_name': [
                'contact_name', 'name', 'person', 'contact_person', 'full_name',
                'имя', 'контактное лицо', 'фио'
            ],
            'position': [
                'position', 'title', 'job_title', 'role', 'designation',
                'должность', 'позиция'
            ],
            'department': [
                'department', 'dept', 'division', 'отдел', 'департамент'
            ],
            'address': [
                'address', 'location', 'адрес', 'местоположение'
            ],
            'city': [
                'city', 'town', 'город'
            ],
            'region': [
                'region', 'state', 'область', 'регион'
            ]
        }

    async def process_bulk_upload(
        self, 
        file_content: bytes, 
        filename: str, 
        upload_request: BulkUploadRequest
    ) -> BulkUploadResult:
        """Process bulk upload file and return results"""
        start_time = datetime.now()
        
        try:
            # Parse file based on type
            if filename.endswith('.csv'):
                df = await self._parse_csv(file_content)
            elif filename.endswith(('.xlsx', '.xls')):
                df = await self._parse_excel(file_content)
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            
            logger.info(f"Parsed file with {len(df)} rows")
            
            # Normalize column names
            df = self._normalize_columns(df)
            
            # Convert DataFrame to companies
            companies = await self._dataframe_to_companies(df)
            logger.info(f"Converted to {len(companies)} companies")
            
            # Process companies (duplicates, AI enhancement, etc.)
            result = await self._process_companies(
                companies, 
                upload_request,
                len(df)
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing bulk upload: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return BulkUploadResult(
                success=False,
                total_rows=0,
                processed_companies=0,
                new_companies=0,
                updated_companies=0,
                skipped_duplicates=0,
                errors=[f"Processing error: {str(e)}"],
                processing_time=processing_time
            )

    async def _parse_csv(self, file_content: bytes) -> pd.DataFrame:
        """Parse CSV file with encoding detection"""
        import chardet
        
        # Detect encoding
        detected = chardet.detect(file_content)
        encoding = detected.get('encoding', 'utf-8')
        
        try:
            # Try detected encoding first
            content = file_content.decode(encoding)
            return pd.read_csv(io.StringIO(content))
        except (UnicodeDecodeError, pd.errors.EmptyDataError):
            # Fallback to common encodings
            for enc in ['utf-8', 'cp1251', 'iso-8859-1', 'cp866']:
                try:
                    content = file_content.decode(enc)
                    return pd.read_csv(io.StringIO(content))
                except (UnicodeDecodeError, pd.errors.EmptyDataError):
                    continue
            
            raise ValueError("Unable to decode CSV file with any supported encoding")

    async def _parse_excel(self, file_content: bytes) -> pd.DataFrame:
        """Parse Excel file"""
        try:
            # Try xlsx first
            return pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        except:
            try:
                # Try xls format
                return pd.read_excel(io.BytesIO(file_content), engine='xlrd')
            except Exception as e:
                raise ValueError(f"Unable to read Excel file: {str(e)}")

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format"""
        column_mapping = {}
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Find best match for each field type
            for field_type, variations in self.field_mappings.items():
                for variation in variations:
                    if variation in col_lower or col_lower in variation:
                        column_mapping[col] = field_type
                        break
                if col in column_mapping:
                    break
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Fill NaN values
        df = df.fillna('')
        
        return df

    async def _dataframe_to_companies(self, df: pd.DataFrame) -> List[Company]:
        """Convert DataFrame rows to Company objects"""
        companies = []
        
        for index, row in df.iterrows():
            try:
                # Extract company information
                company_name = str(row.get('company', '')).strip()
                if not company_name:
                    continue
                
                # Create main contact
                contacts = []
                contact_name = str(row.get('contact_name', '')).strip()
                if contact_name:
                    contact = Contact(
                        personal_name=contact_name,
                        position=str(row.get('position', '')).strip(),
                        department=str(row.get('department', '')).strip(),
                        email=str(row.get('email', '')).strip(),
                        mobile_number=str(row.get('mobile', '')).strip(),
                        phone_number=str(row.get('phone', '')).strip(),
                        is_primary=True
                    )
                    contacts.append(contact)
                
                # Create company
                company = Company(
                    company_name=company_name,
                    website=str(row.get('website', '')).strip(),
                    contacts=contacts,
                    main_phone=str(row.get('phone', '')).strip(),
                    main_email=str(row.get('email', '')).strip(),
                    address_raw=str(row.get('address', '')).strip(),
                    city=str(row.get('city', '')).strip(),
                    region=str(row.get('region', '')).strip(),
                    source="bulk_upload"
                )
                
                companies.append(company)
                
            except Exception as e:
                logger.error(f"Error processing row {index}: {str(e)}")
                continue
        
        return companies

    async def _process_companies(
        self, 
        companies: List[Company], 
        upload_request: BulkUploadRequest,
        total_rows: int
    ) -> BulkUploadResult:
        """Process companies: deduplicate, enhance with AI, save to database"""
        
        result = BulkUploadResult(
            success=True,
            total_rows=total_rows,
            processed_companies=0,
            new_companies=0,
            updated_companies=0,
            skipped_duplicates=0
        )
        
        for company in companies:
            try:
                # Check for duplicates
                if upload_request.deduplicate:
                    existing_match = await self._find_duplicate_company(company)
                    if existing_match:
                        # Handle duplicate
                        await self._handle_duplicate_company(company, existing_match, result)
                        continue
                
                # AI Enhancement
                if upload_request.enhance_with_ai:
                    enhancement_result = await self.ai_service.enhance_company_data(company)
                    await self._apply_ai_enhancements(company, enhancement_result)
                    result.ai_enhancements += 1
                
                # Format Russian address
                if company.address_raw:
                    company.address_formatted = self._format_russian_address(company.address_raw)
                
                # Save to database
                await self._save_company(company)
                result.new_companies += 1
                result.processed_companies += 1
                
            except Exception as e:
                logger.error(f"Error processing company {company.company_name}: {str(e)}")
                result.errors.append(f"Error processing {company.company_name}: {str(e)}")
        
        return result

    async def _find_duplicate_company(self, company: Company) -> Optional[CompanyMatch]:
        """Find duplicate company in database"""
        # Search by company name (fuzzy match)
        name_query = {
            "company_name": {
                "$regex": re.escape(company.company_name), 
                "$options": "i"
            }
        }
        
        existing = await self.companies_collection.find_one(name_query)
        if existing:
            return CompanyMatch(
                company_id=existing["id"],
                match_confidence=0.9,
                match_reasons=["company_name_exact"],
                existing_company=Company(**existing)
            )
        
        # Search by website
        if company.website:
            website_query = {"website": company.website}
            existing = await self.companies_collection.find_one(website_query)
            if existing:
                return CompanyMatch(
                    company_id=existing["id"],
                    match_confidence=0.8,
                    match_reasons=["website_match"],
                    existing_company=Company(**existing)
                )
        
        # Search by email domain
        if company.main_email and "@" in company.main_email:
            domain = company.main_email.split("@")[1]
            domain_query = {"main_email": {"$regex": f"@{re.escape(domain)}", "$options": "i"}}
            existing = await self.companies_collection.find_one(domain_query)
            if existing:
                return CompanyMatch(
                    company_id=existing["id"],
                    match_confidence=0.7,
                    match_reasons=["email_domain_match"],
                    existing_company=Company(**existing)
                )
        
        return None

    async def _handle_duplicate_company(
        self, 
        new_company: Company, 
        existing_match: CompanyMatch, 
        result: BulkUploadResult
    ):
        """Handle duplicate company by merging contacts and information"""
        existing_company = existing_match.existing_company
        
        # Check if we should skip (same contact person)
        if new_company.contacts:
            new_contact = new_company.contacts[0]
            for existing_contact in existing_company.contacts:
                if (existing_contact.personal_name == new_contact.personal_name and 
                    existing_contact.email == new_contact.email):
                    result.skipped_duplicates += 1
                    return
        
        # Merge new contacts into existing company
        if new_company.contacts:
            new_contact = new_company.contacts[0]
            existing_company.contacts.append(new_contact)
            existing_company.updated_at = datetime.now()
            
            # Save updated company
            await self.companies_collection.replace_one(
                {"id": existing_company.id},
                existing_company.dict()
            )
            
            result.updated_companies += 1
            result.processed_companies += 1

    async def _apply_ai_enhancements(self, company: Company, enhancement_result):
        """Apply AI enhancements to company data"""
        enhancements = enhancement_result.enhancements
        
        # Update company fields with AI enhancements
        if enhancements.get("industry_analysis"):
            company.description = enhancements["industry_analysis"]
        
        if enhancements.get("market_segment"):
            company.market_segment = enhancements["market_segment"]
        
        if enhancements.get("business_type"):
            company.business_type = enhancements["business_type"]
        
        if enhancements.get("industry_category"):
            company.industry_category = enhancements["industry_category"]
        
        if enhancements.get("target_market"):
            company.target_market = enhancements["target_market"]
        
        if enhancements.get("estimated_revenue_range"):
            company.annual_revenue = enhancements["estimated_revenue_range"]
        
        if enhancements.get("estimated_employees"):
            company.employee_count = enhancements["estimated_employees"]
        
        # Update tags
        if enhancements.get("industry_keywords_found"):
            company.tags.extend(enhancements["industry_keywords_found"])
        
        # Enhance contacts
        if enhancements.get("enhanced_contacts"):
            enhanced_contacts = enhancements["enhanced_contacts"]
            for i, enhanced in enumerate(enhanced_contacts):
                if i < len(company.contacts):
                    contact = company.contacts[i]
                    if enhanced.get("enhanced_name"):
                        contact.personal_name = enhanced["enhanced_name"]
                    if enhanced.get("standardized_position"):
                        contact.position = enhanced["standardized_position"]
                    if enhanced.get("department"):
                        contact.department = enhanced["department"]

    def _format_russian_address(self, address_raw: str) -> str:
        """Format address according to Russian standards"""
        if not address_raw:
            return ""
        
        # Basic Russian address formatting
        # Expected format: "City, Street, Building, Apartment, Postal Code, Region"
        
        # Clean up the address
        cleaned = address_raw.strip()
        
        # If already well-formatted, return as is
        if "," in cleaned and len(cleaned.split(",")) >= 3:
            return cleaned
        
        # Basic cleanup and formatting
        # This is a simplified version - in production, you'd use more sophisticated parsing
        return cleaned

    async def _save_company(self, company: Company):
        """Save company to database"""
        company_dict = company.dict()
        
        # Save company
        await self.companies_collection.insert_one(company_dict)
        
        # Save individual contacts for easier querying
        for contact in company.contacts:
            contact_dict = contact.dict()
            contact_dict["company_id"] = company.id
            contact_dict["company_name"] = company.company_name
            await self.contacts_collection.insert_one(contact_dict)

    async def get_upload_template(self) -> Dict[str, Any]:
        """Get template for bulk upload with example data"""
        return {
            "csv_template": {
                "headers": [
                    "company_name", "website", "contact_name", "position", 
                    "department", "email", "phone", "mobile", "address", 
                    "city", "region"
                ],
                "example_row": [
                    "ООО Молочные продукты", 
                    "https://milk-products.ru",
                    "Иван Петров",
                    "Генеральный директор",
                    "Управление",
                    "ivan@milk-products.ru",
                    "+7 495 123-45-67",
                    "+7 903 123-45-67",
                    "ул. Ленина, дом 1",
                    "Москва",
                    "Московская область"
                ]
            },
            "supported_columns": self.field_mappings
        }

    async def get_companies_by_segment(self, segment: str) -> List[Dict]:
        """Get companies by market segment for B2B targeting"""
        companies = await self.companies_collection.find(
            {"market_segment": segment}
        ).to_list(length=None)
        
        return companies

    async def get_companies_by_industry(self, industry_category: str) -> List[Dict]:
        """Get companies by industry category"""
        companies = await self.companies_collection.find(
            {"industry_category": industry_category}
        ).to_list(length=None)
        
        return companies