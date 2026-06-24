import os
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from emergentintegrations.llm.chat import LlmChat, UserMessage
from models.crm_bulk import Company, Contact, AIEnhancementResult, INDUSTRY_CATEGORIES, MARKET_SEGMENTS

logger = logging.getLogger(__name__)

class CRMAIService:
    """AI service for enhancing CRM data with market research and analysis"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
        
        # Initialize LLM chat for different purposes
        self.market_researcher = LlmChat(
            api_key=self.api_key,
            session_id="crm_market_research",
            system_message="""You are an expert market research analyst specializing in B2B company analysis. 
            Your job is to analyze companies and provide detailed business intelligence including:
            - Industry classification and market segments
            - Company size and revenue estimates  
            - Business type identification
            - Target market analysis
            - Contact role identification
            
            Always respond in JSON format with specific, actionable data. Be concise but thorough."""
        ).with_model("openai", "gpt-5")
        
        self.contact_enhancer = LlmChat(
            api_key=self.api_key,
            session_id="crm_contact_enhancement",
            system_message="""You are a business contact research specialist. Given company information,
            you research and enhance contact details including:
            - Full names and proper positions/titles
            - Department assignments
            - Role hierarchy within organizations
            - Contact information validation
            
            Focus on Russian and international business structures. Respond in JSON format."""
        ).with_model("openai", "gpt-5")

    async def enhance_company_data(self, company: Company) -> AIEnhancementResult:
        """Enhance company data with AI market research and analysis"""
        start_time = datetime.now()
        enhancements = {}
        
        try:
            # Prepare company data for AI analysis
            company_info = {
                "company_name": company.company_name,
                "website": company.website,
                "existing_industry": company.industry,
                "existing_description": company.description,
                "contacts": [
                    {
                        "name": c.personal_name,
                        "position": c.position, 
                        "department": c.department,
                        "email": c.email
                    } for c in company.contacts if c.personal_name
                ]
            }
            
            # Market research and company analysis
            market_analysis = await self._analyze_market_data(company_info)
            enhancements.update(market_analysis)
            
            # Enhanced contact information
            if company.contacts:
                contact_enhancements = await self._enhance_contacts(company_info)
                enhancements["enhanced_contacts"] = contact_enhancements
            
            # Industry classification
            industry_classification = self._classify_industry(
                company.company_name, 
                company.description or "", 
                enhancements.get("industry_analysis", "")
            )
            enhancements.update(industry_classification)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIEnhancementResult(
                company_id=company.id,
                enhancements=enhancements,
                confidence_score=self._calculate_confidence_score(enhancements),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error enhancing company data for {company.company_name}: {str(e)}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIEnhancementResult(
                company_id=company.id,
                enhancements={"error": str(e)},
                confidence_score=0.0,
                processing_time=processing_time
            )

    async def _analyze_market_data(self, company_info: Dict) -> Dict[str, Any]:
        """Analyze company market data using AI"""
        try:
            prompt = f"""
            Analyze this company and provide market research data:
            
            Company: {company_info['company_name']}
            Website: {company_info.get('website', 'N/A')}
            Current Industry: {company_info.get('existing_industry', 'Unknown')}
            Description: {company_info.get('existing_description', 'None')}
            
            Provide analysis in this exact JSON format:
            {{
                "industry_analysis": "Detailed industry description",
                "market_segment": "ENTERPRISE|SME|SMALL_BUSINESS|STARTUP|GOVERNMENT|NON_PROFIT",
                "business_type": "B2B|B2C|B2B2C",
                "target_market": "Description of target market",
                "estimated_revenue_range": "Revenue estimate range",
                "estimated_employees": "Employee count estimate",
                "key_services": ["service1", "service2", "service3"],
                "competitive_advantages": ["advantage1", "advantage2"],
                "market_position": "market position analysis",
                "growth_stage": "startup|growth|mature|declining",
                "geographic_reach": "local|regional|national|international",
                "technology_adoption": "low|medium|high"
            }}
            
            Base your analysis on the company name, website domain, and any available information.
            """
            
            message = UserMessage(text=prompt)
            response = await self.market_researcher.send_message(message)
            
            # Parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback to basic analysis if JSON parsing fails
                return self._basic_market_analysis(company_info)
                
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return self._basic_market_analysis(company_info)

    async def _enhance_contacts(self, company_info: Dict) -> List[Dict]:
        """Enhance contact information using AI"""
        try:
            if not company_info.get("contacts"):
                return []
                
            prompt = f"""
            Enhance contact information for this company:
            
            Company: {company_info['company_name']}
            Website: {company_info.get('website', 'N/A')}
            
            Current contacts: {json.dumps(company_info['contacts'], indent=2)}
            
            For each contact, enhance and standardize the information in this JSON format:
            [
                {{
                    "original_name": "original name from input",
                    "enhanced_name": "properly formatted full name",
                    "standardized_position": "standardized job title",
                    "department": "department name",
                    "seniority_level": "entry|mid|senior|executive|c-level",
                    "decision_maker": true/false,
                    "contact_priority": "high|medium|low",
                    "typical_responsibilities": ["responsibility1", "responsibility2"],
                    "likely_interests": ["interest1", "interest2"]
                }}
            ]
            
            Focus on Russian and international business hierarchies and common positions.
            """
            
            message = UserMessage(text=prompt)
            response = await self.contact_enhancer.send_message(message)
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return self._basic_contact_enhancement(company_info['contacts'])
                
        except Exception as e:
            logger.error(f"Error enhancing contacts: {str(e)}")
            return self._basic_contact_enhancement(company_info.get('contacts', []))

    def _classify_industry(self, company_name: str, description: str, ai_analysis: str) -> Dict[str, str]:
        """Classify company industry based on keywords and AI analysis"""
        text_to_analyze = f"{company_name} {description} {ai_analysis}".lower()
        
        # Find matching industry categories
        matched_categories = []
        for category, keywords in INDUSTRY_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    matched_categories.append(category)
                    break
        
        # Determine primary category
        if matched_categories:
            primary_category = matched_categories[0]
        else:
            primary_category = "OTHER"
        
        return {
            "industry_category": primary_category,
            "industry_subcategories": matched_categories[:3],  # Top 3 matches
            "industry_keywords_found": self._extract_industry_keywords(text_to_analyze)
        }

    def _extract_industry_keywords(self, text: str) -> List[str]:
        """Extract industry-relevant keywords from text"""
        found_keywords = []
        for category, keywords in INDUSTRY_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in text and keyword not in found_keywords:
                    found_keywords.append(keyword)
        return found_keywords[:10]  # Limit to top 10

    def _basic_market_analysis(self, company_info: Dict) -> Dict[str, Any]:
        """Provide basic market analysis when AI analysis fails"""
        company_name = company_info.get('company_name', '').lower()
        
        # Basic industry detection
        if any(word in company_name for word in ['llc', 'ltd', 'inc', 'corp']):
            business_type = "B2B"
        elif any(word in company_name for word in ['shop', 'store', 'market']):
            business_type = "B2C"
        else:
            business_type = "B2B"
        
        return {
            "industry_analysis": f"Basic analysis for {company_info['company_name']}",
            "market_segment": "SME",
            "business_type": business_type,
            "target_market": "General market",
            "estimated_revenue_range": "Unknown",
            "estimated_employees": "Unknown",
            "key_services": [],
            "competitive_advantages": [],
            "market_position": "Unknown",
            "growth_stage": "unknown",
            "geographic_reach": "regional",
            "technology_adoption": "medium"
        }

    def _basic_contact_enhancement(self, contacts: List[Dict]) -> List[Dict]:
        """Provide basic contact enhancement when AI enhancement fails"""
        enhanced = []
        for contact in contacts:
            enhanced.append({
                "original_name": contact.get('name', ''),
                "enhanced_name": contact.get('name', ''),
                "standardized_position": contact.get('position', ''),
                "department": contact.get('department', ''),
                "seniority_level": "mid",
                "decision_maker": False,
                "contact_priority": "medium",
                "typical_responsibilities": [],
                "likely_interests": []
            })
        return enhanced

    def _calculate_confidence_score(self, enhancements: Dict) -> float:
        """Calculate confidence score for AI enhancements"""
        score = 0.0
        total_checks = 0
        
        # Check if key fields were enhanced
        key_fields = [
            'industry_analysis', 'market_segment', 'business_type',
            'target_market', 'estimated_revenue_range'
        ]
        
        for field in key_fields:
            total_checks += 1
            if enhancements.get(field) and enhancements[field] != "Unknown":
                score += 1
        
        # Bonus for contact enhancements
        if enhancements.get('enhanced_contacts'):
            total_checks += 1
            score += 1
        
        return score / total_checks if total_checks > 0 else 0.0

    async def batch_enhance_companies(self, companies: List[Company]) -> List[AIEnhancementResult]:
        """Enhance multiple companies in batch with rate limiting"""
        results = []
        
        # Process in batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.enhance_company_data(company) for company in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {str(result)}")
                    continue
                results.append(result)
            
            # Rate limiting pause between batches
            if i + batch_size < len(companies):
                await asyncio.sleep(1)  # 1 second pause between batches
        
        return results