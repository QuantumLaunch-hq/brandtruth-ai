# src/analyzers/platform_recommender.py
"""Platform Recommender - Recommends best ad platforms for your product.

Analyzes:
- Product type and audience
- Budget constraints
- Platform strengths/weaknesses
- Expected performance by platform
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    META = "meta"
    GOOGLE = "google"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    REDDIT = "reddit"
    YOUTUBE = "youtube"


class ProductType(str, Enum):
    B2B_SAAS = "b2b_saas"
    B2C_SAAS = "b2c_saas"
    ECOMMERCE = "ecommerce"
    MOBILE_APP = "mobile_app"
    AGENCY = "agency"
    COURSE = "course"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class AudienceType(str, Enum):
    DEVELOPERS = "developers"
    MARKETERS = "marketers"
    FOUNDERS = "founders"
    ENTERPRISE = "enterprise"
    CONSUMERS = "consumers"
    CREATORS = "creators"
    PROFESSIONALS = "professionals"


class PlatformRecommendation(BaseModel):
    platform: Platform
    score: int = Field(ge=0, le=100)
    rank: int
    min_budget: float
    expected_cpa_range: str
    strengths: list[str]
    weaknesses: list[str]
    best_formats: list[str]
    recommended_budget_split: float  # percentage


class PlatformRecommenderResult(BaseModel):
    recommendations: list[PlatformRecommendation]
    primary_platform: Platform
    budget_allocation: dict[str, float]
    strategy: str
    
    def get_summary(self) -> str:
        return f"Primary: {self.primary_platform.value.upper()} | Strategy: {self.strategy}"


class PlatformRequest(BaseModel):
    product_type: ProductType
    audience_type: AudienceType
    monthly_budget: float = 1000
    product_price: float = 99
    is_visual: bool = True


PLATFORM_DATA = {
    Platform.META: {
        "min_budget": 300,
        "best_for": [ProductType.ECOMMERCE, ProductType.B2C_SAAS, ProductType.COURSE, ProductType.MOBILE_APP],
        "audiences": [AudienceType.CONSUMERS, AudienceType.CREATORS, AudienceType.MARKETERS],
        "strengths": ["Massive reach", "Advanced targeting", "Visual formats", "Retargeting"],
        "weaknesses": ["Rising CPMs", "Privacy changes impact", "B2B harder"],
        "formats": ["Feed ads", "Stories", "Reels", "Carousel"],
        "cpa_range": "$20-100",
    },
    Platform.GOOGLE: {
        "min_budget": 500,
        "best_for": [ProductType.B2B_SAAS, ProductType.AGENCY, ProductType.ECOMMERCE],
        "audiences": [AudienceType.ENTERPRISE, AudienceType.PROFESSIONALS, AudienceType.FOUNDERS],
        "strengths": ["High intent", "Search capture", "Broad reach", "Performance max"],
        "weaknesses": ["Expensive keywords", "Steep learning curve", "Complex setup"],
        "formats": ["Search ads", "Display", "YouTube", "Performance Max"],
        "cpa_range": "$50-200",
    },
    Platform.LINKEDIN: {
        "min_budget": 1000,
        "best_for": [ProductType.B2B_SAAS, ProductType.AGENCY, ProductType.COURSE],
        "audiences": [AudienceType.ENTERPRISE, AudienceType.FOUNDERS, AudienceType.PROFESSIONALS, AudienceType.MARKETERS],
        "strengths": ["B2B targeting", "Job title targeting", "Professional context", "Lead gen forms"],
        "weaknesses": ["High CPCs ($5-15)", "Limited scale", "Expensive"],
        "formats": ["Sponsored content", "Message ads", "Lead gen forms"],
        "cpa_range": "$100-300",
    },
    Platform.TIKTOK: {
        "min_budget": 200,
        "best_for": [ProductType.B2C_SAAS, ProductType.ECOMMERCE, ProductType.MOBILE_APP, ProductType.COURSE],
        "audiences": [AudienceType.CONSUMERS, AudienceType.CREATORS],
        "strengths": ["Low CPMs", "Viral potential", "Young audience", "Native feel"],
        "weaknesses": ["Needs video content", "Younger skew", "B2B difficult"],
        "formats": ["In-feed video", "Spark ads", "TopView"],
        "cpa_range": "$10-50",
    },
    Platform.TWITTER: {
        "min_budget": 300,
        "best_for": [ProductType.B2B_SAAS, ProductType.NEWSLETTER],
        "audiences": [AudienceType.DEVELOPERS, AudienceType.FOUNDERS, AudienceType.MARKETERS],
        "strengths": ["Tech audience", "Thought leadership", "Conversation targeting"],
        "weaknesses": ["Limited scale", "Brand safety", "Lower intent"],
        "formats": ["Promoted tweets", "Follower ads"],
        "cpa_range": "$30-100",
    },
    Platform.REDDIT: {
        "min_budget": 200,
        "best_for": [ProductType.B2B_SAAS, ProductType.B2C_SAAS, ProductType.MOBILE_APP],
        "audiences": [AudienceType.DEVELOPERS, AudienceType.CONSUMERS],
        "strengths": ["Niche communities", "Low CPCs", "Authentic engagement"],
        "weaknesses": ["Anti-ad culture", "Needs native approach", "Limited targeting"],
        "formats": ["Promoted posts", "Conversation ads"],
        "cpa_range": "$20-80",
    },
    Platform.YOUTUBE: {
        "min_budget": 500,
        "best_for": [ProductType.COURSE, ProductType.B2C_SAAS, ProductType.ECOMMERCE],
        "audiences": [AudienceType.CONSUMERS, AudienceType.CREATORS, AudienceType.PROFESSIONALS],
        "strengths": ["Video storytelling", "Long-form content", "Search + discovery"],
        "weaknesses": ["Needs video production", "Skippable ads", "Higher production cost"],
        "formats": ["Skippable in-stream", "Discovery ads", "Shorts"],
        "cpa_range": "$30-100",
    },
}


class PlatformRecommender:
    def __init__(self):
        self.platform_data = PLATFORM_DATA
    
    async def recommend(self, request: PlatformRequest) -> PlatformRecommenderResult:
        logger.info(f"Recommending platforms for {request.product_type.value}")
        
        scores = []
        for platform, data in self.platform_data.items():
            score = self._score_platform(platform, data, request)
            scores.append((platform, score, data))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for rank, (platform, score, data) in enumerate(scores, 1):
            recommendations.append(PlatformRecommendation(
                platform=platform,
                score=score,
                rank=rank,
                min_budget=data["min_budget"],
                expected_cpa_range=data["cpa_range"],
                strengths=data["strengths"],
                weaknesses=data["weaknesses"],
                best_formats=data["formats"],
                recommended_budget_split=self._calculate_split(rank, score, request.monthly_budget),
            ))
        
        # Calculate budget allocation for top 3
        budget_allocation = {}
        remaining = 100
        for rec in recommendations[:3]:
            if remaining > 0:
                split = min(rec.recommended_budget_split, remaining)
                budget_allocation[rec.platform.value] = split
                remaining -= split
        
        # Determine strategy
        primary = recommendations[0].platform
        if request.monthly_budget < 500:
            strategy = f"Focus 100% on {primary.value.upper()} to maximize learning"
        elif request.monthly_budget < 2000:
            strategy = f"80% {primary.value.upper()}, 20% testing secondary platform"
        else:
            strategy = f"Diversify across top 3 platforms with {primary.value.upper()} as primary"
        
        return PlatformRecommenderResult(
            recommendations=recommendations,
            primary_platform=primary,
            budget_allocation=budget_allocation,
            strategy=strategy,
        )
    
    def _score_platform(self, platform: Platform, data: dict, request: PlatformRequest) -> int:
        score = 50
        
        # Product fit
        if request.product_type in data["best_for"]:
            score += 25
        
        # Audience fit
        if request.audience_type in data["audiences"]:
            score += 20
        
        # Budget fit
        if request.monthly_budget >= data["min_budget"]:
            score += 10
        else:
            score -= 20
        
        # Visual product bonus for visual platforms
        if request.is_visual and platform in [Platform.META, Platform.TIKTOK, Platform.YOUTUBE]:
            score += 10
        
        # B2B adjustments
        if request.audience_type in [AudienceType.ENTERPRISE, AudienceType.FOUNDERS]:
            if platform == Platform.LINKEDIN:
                score += 15
            elif platform == Platform.TIKTOK:
                score -= 15
        
        return min(max(score, 0), 100)
    
    def _calculate_split(self, rank: int, score: int, budget: float) -> float:
        if rank == 1:
            return 60 if budget > 1000 else 80
        elif rank == 2:
            return 25 if budget > 1000 else 15
        elif rank == 3:
            return 15 if budget > 2000 else 5
        return 0
    
    def get_platforms(self) -> list[dict]:
        return [{"id": p.value, "name": p.value.upper()} for p in Platform]


_instance: Optional[PlatformRecommender] = None

def get_platform_recommender() -> PlatformRecommender:
    global _instance
    if _instance is None:
        _instance = PlatformRecommender()
    return _instance
