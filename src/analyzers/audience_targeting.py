# src/analyzers/audience_targeting.py
"""Audience Targeting AI - Suggests optimal audience targeting.

Provides:
- Meta audience recommendations
- Interest targeting suggestions
- Lookalike strategies
- Exclusion recommendations
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AudienceType(str, Enum):
    INTEREST = "interest"
    BEHAVIOR = "behavior"
    DEMOGRAPHIC = "demographic"
    LOOKALIKE = "lookalike"
    CUSTOM = "custom"
    RETARGETING = "retargeting"


class AudienceSegment(BaseModel):
    name: str
    type: AudienceType
    description: str
    estimated_size: str
    relevance_score: int = Field(ge=0, le=100)
    recommended: bool = True
    targeting_tips: list[str] = Field(default_factory=list)


class AudienceExclusion(BaseModel):
    name: str
    reason: str
    impact: str


class AudienceStrategy(BaseModel):
    primary_audiences: list[AudienceSegment]
    secondary_audiences: list[AudienceSegment]
    exclusions: list[AudienceExclusion]
    lookalike_strategy: str
    budget_allocation: dict[str, int]
    testing_order: list[str]
    recommendations: list[str] = Field(default_factory=list)
    
    def get_summary(self) -> str:
        return f"{len(self.primary_audiences)} primary audiences | {len(self.exclusions)} exclusions"


class AudienceRequest(BaseModel):
    product_name: str
    product_description: str
    product_type: str  # saas, ecommerce, app, etc.
    target_persona: str
    price_point: float = 99
    existing_customers: bool = False
    website_traffic: bool = False


# Interest categories for different product types
INTEREST_DATABASE = {
    "saas": {
        "primary": [
            {"name": "Small business owners", "size": "50-100M", "score": 90},
            {"name": "Entrepreneurship", "size": "100-200M", "score": 85},
            {"name": "Startups", "size": "20-50M", "score": 88},
            {"name": "Business software", "size": "30-60M", "score": 85},
            {"name": "Productivity", "size": "80-150M", "score": 75},
        ],
        "secondary": [
            {"name": "Marketing automation", "size": "10-20M", "score": 70},
            {"name": "Project management", "size": "15-30M", "score": 68},
            {"name": "Remote work", "size": "40-80M", "score": 65},
        ],
    },
    "ecommerce": {
        "primary": [
            {"name": "Online shopping", "size": "500M+", "score": 85},
            {"name": "Engaged shoppers", "size": "200-400M", "score": 90},
            {"name": "Fashion enthusiasts", "size": "100-200M", "score": 80},
        ],
        "secondary": [
            {"name": "Deal seekers", "size": "150-300M", "score": 75},
            {"name": "Brand loyalists", "size": "50-100M", "score": 70},
        ],
    },
    "career": {
        "primary": [
            {"name": "Job seekers", "size": "100-200M", "score": 95},
            {"name": "Career development", "size": "50-100M", "score": 90},
            {"name": "Professional networking", "size": "80-150M", "score": 85},
            {"name": "Resume writing", "size": "10-30M", "score": 92},
        ],
        "secondary": [
            {"name": "LinkedIn users", "size": "200M+", "score": 75},
            {"name": "Recent graduates", "size": "30-60M", "score": 80},
            {"name": "Career changers", "size": "20-40M", "score": 85},
        ],
    },
    "default": {
        "primary": [
            {"name": "Engaged buyers", "size": "100-200M", "score": 80},
            {"name": "Technology early adopters", "size": "50-100M", "score": 75},
        ],
        "secondary": [
            {"name": "Online shoppers", "size": "300M+", "score": 65},
        ],
    },
}


class AudienceTargeting:
    def __init__(self):
        self.interest_db = INTEREST_DATABASE
    
    async def suggest(self, request: AudienceRequest) -> AudienceStrategy:
        logger.info(f"Generating audience strategy for {request.product_name}")
        
        # Determine product category
        category = self._categorize_product(request)
        interests = self.interest_db.get(category, self.interest_db["default"])
        
        # Build primary audiences
        primary = []
        for interest in interests["primary"]:
            primary.append(AudienceSegment(
                name=interest["name"],
                type=AudienceType.INTEREST,
                description=f"Users interested in {interest['name'].lower()}",
                estimated_size=interest["size"],
                relevance_score=interest["score"],
                targeting_tips=self._get_tips(interest["name"], request),
            ))
        
        # Build secondary audiences
        secondary = []
        for interest in interests["secondary"]:
            secondary.append(AudienceSegment(
                name=interest["name"],
                type=AudienceType.INTEREST,
                description=f"Broader audience interested in {interest['name'].lower()}",
                estimated_size=interest["size"],
                relevance_score=interest["score"],
                recommended=interest["score"] >= 70,
            ))
        
        # Add custom audiences if available
        if request.existing_customers:
            primary.insert(0, AudienceSegment(
                name="Customer Lookalike (1%)",
                type=AudienceType.LOOKALIKE,
                description="Users similar to your existing customers",
                estimated_size="2-5M",
                relevance_score=95,
                targeting_tips=["Best performing audience", "Start with 1% lookalike, expand to 3-5%"],
            ))
        
        if request.website_traffic:
            primary.insert(0, AudienceSegment(
                name="Website Visitors (Retargeting)",
                type=AudienceType.RETARGETING,
                description="Users who visited your website in last 30-180 days",
                estimated_size="Depends on traffic",
                relevance_score=98,
                targeting_tips=["Highest intent audience", "Segment by pages viewed"],
            ))
        
        # Build exclusions
        exclusions = self._build_exclusions(request)
        
        # Lookalike strategy
        lookalike = self._get_lookalike_strategy(request)
        
        # Budget allocation
        allocation = self._calculate_allocation(request, primary, secondary)
        
        # Testing order
        testing_order = [
            "1. Retargeting (if available) - highest ROI",
            "2. Customer lookalike (1%) - proven interest",
            "3. Top interest audience - broadest reach",
            "4. Stacked interests - more qualified",
            "5. Expand lookalike to 3-5% for scale",
        ]
        
        recommendations = self._generate_recommendations(request, primary)
        
        return AudienceStrategy(
            primary_audiences=primary,
            secondary_audiences=secondary,
            exclusions=exclusions,
            lookalike_strategy=lookalike,
            budget_allocation=allocation,
            testing_order=testing_order,
            recommendations=recommendations,
        )
    
    def _categorize_product(self, request: AudienceRequest) -> str:
        desc = (request.product_description + " " + request.product_type).lower()
        if any(w in desc for w in ["resume", "job", "career", "interview", "hire"]):
            return "career"
        elif any(w in desc for w in ["shop", "store", "product", "buy", "ecommerce"]):
            return "ecommerce"
        elif any(w in desc for w in ["saas", "software", "app", "tool", "platform"]):
            return "saas"
        return "default"
    
    def _get_tips(self, interest: str, request: AudienceRequest) -> list[str]:
        tips = [f"Combine with behavior: Recent app installers or engaged shoppers"]
        if request.price_point > 100:
            tips.append("Layer with income targeting: Top 25% household income")
        tips.append("Test narrow (2-5M) vs broad (10M+) audience sizes")
        return tips
    
    def _build_exclusions(self, request: AudienceRequest) -> list[AudienceExclusion]:
        exclusions = [
            AudienceExclusion(
                name="Existing customers",
                reason="Don't pay to reach people who already converted",
                impact="Saves 5-15% of budget",
            ),
            AudienceExclusion(
                name="Competitors' employees",
                reason="Unlikely to convert, may be researching",
                impact="Cleaner data, less noise",
            ),
        ]
        
        if request.price_point > 200:
            exclusions.append(AudienceExclusion(
                name="Low-income demographics",
                reason="Price point may be out of reach",
                impact="Higher conversion rate",
            ))
        
        return exclusions
    
    def _get_lookalike_strategy(self, request: AudienceRequest) -> str:
        if request.existing_customers:
            return "Create 1%, 3%, and 5% lookalikes from customer list. Start with 1% (highest quality), expand for scale."
        elif request.website_traffic:
            return "Create lookalikes from website visitors. Segment by: All visitors, Add-to-cart, Checkout initiated."
        else:
            return "No seed audience available yet. Focus on interest targeting, then create lookalikes from converters."
    
    def _calculate_allocation(self, request: AudienceRequest, primary: list, secondary: list) -> dict:
        allocation = {}
        
        has_custom = any(a.type in [AudienceType.LOOKALIKE, AudienceType.RETARGETING] for a in primary)
        
        if has_custom:
            allocation["Retargeting/Lookalike"] = 40
            allocation["Primary Interests"] = 40
            allocation["Testing (Secondary)"] = 20
        else:
            allocation["Primary Interests"] = 70
            allocation["Testing (Secondary)"] = 30
        
        return allocation
    
    def _generate_recommendations(self, request: AudienceRequest, primary: list) -> list[str]:
        recs = []
        
        if not request.existing_customers:
            recs.append("Upload customer list ASAP to create high-performing lookalike audiences")
        
        if not request.website_traffic:
            recs.append("Install Meta Pixel immediately to enable retargeting")
        
        recs.append("Start with 3-5 interest audiences, let Meta optimize with Advantage+")
        recs.append("Avoid audience overlap - use exclusions between ad sets")
        
        if request.price_point > 100:
            recs.append("Consider layering with income/education demographics for B2B")
        
        return recs
    
    def get_interest_categories(self) -> list[str]:
        return list(self.interest_db.keys())


_instance: Optional[AudienceTargeting] = None

def get_audience_targeting() -> AudienceTargeting:
    global _instance
    if _instance is None:
        _instance = AudienceTargeting()
    return _instance
