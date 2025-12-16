# src/analyzers/competitor_intel.py
"""Competitor Intelligence Analyzer for BrandTruth AI - Slice 12

Analyzes competitor advertising strategies from Meta Ads Library.

Features:
- Fetch competitor ads from Meta Ads Library
- Analyze copy patterns and messaging themes
- Identify visual strategies
- Track ad frequency and spend estimates
- Generate competitive insights
- Benchmark against industry

Meta Ads Library API:
- Free public access
- No authentication for basic queries
- Rate limited
- Returns active ads for any page
"""

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AdCategory(str, Enum):
    """Ad categories in Meta Ads Library."""
    ALL = "all"
    EMPLOYMENT = "employment"
    HOUSING = "housing"
    CREDIT = "credit"
    ISSUES_ELECTIONS_POLITICS = "issues_elections_politics"


class CompetitorThreat(str, Enum):
    """Threat level from competitor."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AdFormat(str, Enum):
    """Detected ad format."""
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    COLLECTION = "collection"
    UNKNOWN = "unknown"


# =============================================================================
# DATA MODELS
# =============================================================================

class CompetitorAd(BaseModel):
    """Single competitor ad from Meta Ads Library."""
    ad_id: str
    page_id: str
    page_name: str
    ad_text: str
    ad_creative_link_title: Optional[str] = None
    ad_creative_link_description: Optional[str] = None
    ad_creative_link_caption: Optional[str] = None
    cta: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    ad_format: AdFormat = AdFormat.IMAGE
    start_date: Optional[datetime] = None
    is_active: bool = True
    platforms: list[str] = Field(default_factory=lambda: ["facebook", "instagram"])
    impressions_lower: int = 0
    impressions_upper: int = 0
    spend_lower: float = 0
    spend_upper: float = 0
    demographic_distribution: Optional[dict] = None


class CopyPattern(BaseModel):
    """Detected pattern in competitor copy."""
    pattern_type: str  # hook, benefit, social_proof, urgency, question
    examples: list[str]
    frequency: int
    effectiveness_score: float = 0.0


class VisualStrategy(BaseModel):
    """Detected visual strategy."""
    strategy_type: str  # product_focus, lifestyle, testimonial, comparison, stats
    examples: list[str]
    frequency: int


class CompetitorProfile(BaseModel):
    """Profile of a single competitor."""
    page_id: str
    page_name: str
    industry: str
    total_ads: int
    active_ads: int
    estimated_monthly_spend: float
    primary_platforms: list[str]
    ad_formats_used: dict[str, int]
    top_performing_themes: list[str]
    copy_patterns: list[CopyPattern]
    visual_strategies: list[VisualStrategy]
    common_ctas: list[str]
    target_demographics: Optional[dict] = None
    threat_level: CompetitorThreat = CompetitorThreat.MEDIUM
    first_seen: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class CompetitorInsight(BaseModel):
    """Actionable insight from competitor analysis."""
    insight_type: str  # opportunity, threat, trend, gap
    title: str
    description: str
    action: str
    priority: int = 1  # 1-5, 1 is highest
    competitors_involved: list[str]


class CompetitorAnalysis(BaseModel):
    """Complete competitor analysis result."""
    analysis_id: str
    brand_name: str
    industry: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Competitors
    competitors: list[CompetitorProfile]
    total_competitor_ads: int
    
    # Market Overview
    market_ad_spend_estimate: float
    dominant_platforms: list[str]
    trending_formats: list[str]
    
    # Copy Intelligence
    industry_copy_patterns: list[CopyPattern]
    overused_phrases: list[str]
    underutilized_angles: list[str]
    
    # Visual Intelligence
    visual_trends: list[VisualStrategy]
    
    # Insights
    insights: list[CompetitorInsight]
    opportunities: list[str]
    threats: list[str]
    
    # Recommendations
    recommendations: list[str]
    
    def get_summary(self) -> str:
        """Get summary."""
        return f"Analyzed {len(self.competitors)} competitors with {self.total_competitor_ads} ads | ${self.market_ad_spend_estimate:,.0f}/mo estimated market spend | {len(self.insights)} insights"


class CompetitorIntelConfig(BaseModel):
    """Configuration for competitor intelligence."""
    max_ads_per_competitor: int = 50
    lookback_days: int = 90
    min_ads_for_analysis: int = 5
    countries: list[str] = Field(default_factory=lambda: ["US"])
    platforms: list[str] = Field(default_factory=lambda: ["facebook", "instagram"])


# =============================================================================
# COMPETITOR INTEL ANALYZER
# =============================================================================

class CompetitorIntelAnalyzer:
    """Analyzes competitor advertising strategies."""
    
    def __init__(self, config: Optional[CompetitorIntelConfig] = None):
        self.config = config or CompetitorIntelConfig()
        self.base_url = "https://www.facebook.com/ads/library/api"
    
    async def analyze_competitors(
        self,
        brand_name: str,
        industry: str,
        competitor_names: Optional[list[str]] = None,
        competitor_page_ids: Optional[list[str]] = None,
    ) -> CompetitorAnalysis:
        """
        Analyze competitors in an industry.
        
        Args:
            brand_name: Your brand name
            industry: Industry category
            competitor_names: List of competitor names to search
            competitor_page_ids: List of competitor page IDs (more accurate)
        
        Returns:
            CompetitorAnalysis with insights
        """
        logger.info(f"Analyzing competitors for {brand_name} in {industry}...")
        
        analysis_id = f"intel_{brand_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Fetch competitor ads
        all_ads: list[CompetitorAd] = []
        competitor_profiles: list[CompetitorProfile] = []
        
        # If specific competitors provided, fetch their ads
        if competitor_page_ids:
            for page_id in competitor_page_ids:
                ads = await self._fetch_ads_by_page_id(page_id)
                all_ads.extend(ads)
        elif competitor_names:
            for name in competitor_names:
                ads = await self._search_ads_by_name(name)
                all_ads.extend(ads)
        else:
            # Search by industry keywords
            ads = await self._search_ads_by_industry(industry)
            all_ads.extend(ads)
        
        # Group ads by competitor and build profiles
        ads_by_page = self._group_ads_by_page(all_ads)
        for page_id, ads in ads_by_page.items():
            if len(ads) >= self.config.min_ads_for_analysis:
                profile = self._build_competitor_profile(page_id, ads, industry)
                competitor_profiles.append(profile)
        
        # Analyze industry patterns
        industry_copy_patterns = self._analyze_copy_patterns(all_ads)
        visual_trends = self._analyze_visual_strategies(all_ads)
        overused = self._find_overused_phrases(all_ads)
        underutilized = self._find_underutilized_angles(all_ads, industry)
        
        # Calculate market metrics
        total_ads = len(all_ads)
        market_spend = sum(p.estimated_monthly_spend for p in competitor_profiles)
        dominant_platforms = self._get_dominant_platforms(all_ads)
        trending_formats = self._get_trending_formats(all_ads)
        
        # Generate insights
        insights = self._generate_insights(competitor_profiles, industry_copy_patterns)
        opportunities = self._find_opportunities(competitor_profiles, industry)
        threats = self._identify_threats(competitor_profiles)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            competitor_profiles, industry_copy_patterns, visual_trends
        )
        
        return CompetitorAnalysis(
            analysis_id=analysis_id,
            brand_name=brand_name,
            industry=industry,
            competitors=competitor_profiles,
            total_competitor_ads=total_ads,
            market_ad_spend_estimate=market_spend,
            dominant_platforms=dominant_platforms,
            trending_formats=trending_formats,
            industry_copy_patterns=industry_copy_patterns,
            overused_phrases=overused,
            underutilized_angles=underutilized,
            visual_trends=visual_trends,
            insights=insights,
            opportunities=opportunities,
            threats=threats,
            recommendations=recommendations,
        )
    
    async def _fetch_ads_by_page_id(self, page_id: str) -> list[CompetitorAd]:
        """Fetch ads for a specific page ID."""
        # In production, this would call Meta Ads Library API
        # For now, return mock data
        return await self._get_mock_ads(page_id)
    
    async def _search_ads_by_name(self, name: str) -> list[CompetitorAd]:
        """Search ads by advertiser name."""
        return await self._get_mock_ads(name)
    
    async def _search_ads_by_industry(self, industry: str) -> list[CompetitorAd]:
        """Search ads by industry keywords."""
        return await self._get_mock_ads(industry)
    
    async def _get_mock_ads(self, identifier: str) -> list[CompetitorAd]:
        """Generate realistic mock competitor ads."""
        await asyncio.sleep(0.2)  # Simulate API call
        
        # Industry-specific mock data
        industry_ads = {
            "career": [
                ("Resume.io", "Your dream job is one resume away. Join 25M+ users who got hired.", "Get Started Free", "resume"),
                ("Zety", "Build a resume that gets noticed. AI-powered suggestions.", "Create My Resume", "zety"),
                ("Indeed Resume", "Upload your resume. Let employers find you.", "Upload Now", "indeed"),
                ("TopResume", "Is your resume getting ignored? Get a free expert review.", "Get Free Review", "topresume"),
                ("LinkedIn Jobs", "Find your next opportunity. 15M+ jobs posted.", "Search Jobs", "linkedin"),
            ],
            "saas": [
                ("Notion", "All-in-one workspace. Replace your scattered tools.", "Get Notion Free", "notion"),
                ("Slack", "Where work happens. Connect your team.", "Try Free", "slack"),
                ("Airtable", "Build apps without code. Organize anything.", "Start Free", "airtable"),
                ("Monday.com", "Work OS that lets you shape workflows.", "Get Started", "monday"),
                ("Asana", "Manage projects without chaos. Try free.", "Start Free Trial", "asana"),
            ],
            "ecommerce": [
                ("Shopify", "Start selling online today. Free trial, no credit card.", "Start Free Trial", "shopify"),
                ("WooCommerce", "The most customizable ecommerce platform.", "Get Started", "woo"),
                ("BigCommerce", "Enterprise ecommerce made simple.", "Start Trial", "bigcommerce"),
                ("Squarespace", "Build your online store. Beautiful templates.", "Get Started", "squarespace"),
            ],
        }
        
        # Determine which ads to use based on identifier
        ads_data = industry_ads.get("career", industry_ads["career"])
        if "resume" in identifier.lower() or "career" in identifier.lower():
            ads_data = industry_ads["career"]
        elif "saas" in identifier.lower() or "software" in identifier.lower():
            ads_data = industry_ads["saas"]
        elif "ecommerce" in identifier.lower() or "shop" in identifier.lower():
            ads_data = industry_ads["ecommerce"]
        
        ads = []
        for name, text, cta, page_id in ads_data:
            # Create multiple ad variants per competitor
            for i in range(3):
                ad = CompetitorAd(
                    ad_id=f"ad_{hashlib.md5(f'{page_id}_{i}'.encode()).hexdigest()[:12]}",
                    page_id=page_id,
                    page_name=name,
                    ad_text=text if i == 0 else self._vary_ad_text(text, i),
                    cta=cta,
                    ad_format=AdFormat.IMAGE if i < 2 else AdFormat.VIDEO,
                    start_date=datetime.utcnow() - timedelta(days=30 + i * 10),
                    impressions_lower=10000 * (i + 1),
                    impressions_upper=50000 * (i + 1),
                    spend_lower=500 * (i + 1),
                    spend_upper=2000 * (i + 1),
                )
                ads.append(ad)
        
        return ads
    
    def _vary_ad_text(self, base_text: str, variant: int) -> str:
        """Create variations of ad text."""
        variations = [
            f"🚀 {base_text}",
            f"NEW: {base_text.replace('.', '!')}",
            f"Limited time: {base_text}",
        ]
        return variations[variant % len(variations)]
    
    def _group_ads_by_page(self, ads: list[CompetitorAd]) -> dict[str, list[CompetitorAd]]:
        """Group ads by page/competitor."""
        groups: dict[str, list[CompetitorAd]] = {}
        for ad in ads:
            if ad.page_id not in groups:
                groups[ad.page_id] = []
            groups[ad.page_id].append(ad)
        return groups
    
    def _build_competitor_profile(
        self,
        page_id: str,
        ads: list[CompetitorAd],
        industry: str,
    ) -> CompetitorProfile:
        """Build profile for a competitor."""
        page_name = ads[0].page_name if ads else page_id
        
        # Count ad formats
        format_counts: dict[str, int] = {}
        for ad in ads:
            fmt = ad.ad_format.value
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        # Estimate monthly spend
        total_spend = sum((ad.spend_lower + ad.spend_upper) / 2 for ad in ads)
        
        # Analyze copy patterns
        copy_patterns = self._analyze_copy_patterns(ads)
        
        # Analyze visuals
        visual_strategies = self._analyze_visual_strategies(ads)
        
        # Extract CTAs
        ctas = list(set(ad.cta for ad in ads if ad.cta))
        
        # Determine threat level
        threat_level = CompetitorThreat.MEDIUM
        if len(ads) > 20 or total_spend > 10000:
            threat_level = CompetitorThreat.HIGH
        elif len(ads) > 50 or total_spend > 50000:
            threat_level = CompetitorThreat.CRITICAL
        elif len(ads) < 10:
            threat_level = CompetitorThreat.LOW
        
        return CompetitorProfile(
            page_id=page_id,
            page_name=page_name,
            industry=industry,
            total_ads=len(ads),
            active_ads=sum(1 for ad in ads if ad.is_active),
            estimated_monthly_spend=total_spend,
            primary_platforms=["facebook", "instagram"],
            ad_formats_used=format_counts,
            top_performing_themes=self._extract_themes(ads),
            copy_patterns=copy_patterns,
            visual_strategies=visual_strategies,
            common_ctas=ctas[:5],
            threat_level=threat_level,
            first_seen=min((ad.start_date for ad in ads if ad.start_date), default=None),
        )
    
    def _analyze_copy_patterns(self, ads: list[CompetitorAd]) -> list[CopyPattern]:
        """Analyze copy patterns across ads."""
        patterns = []
        
        # Check for hooks
        hook_patterns = ["🚀", "NEW:", "Limited", "FREE", "Join", "Stop"]
        hook_count = sum(1 for ad in ads if any(h in ad.ad_text for h in hook_patterns))
        if hook_count > 0:
            patterns.append(CopyPattern(
                pattern_type="hook",
                examples=[ad.ad_text[:50] for ad in ads if any(h in ad.ad_text for h in hook_patterns)][:3],
                frequency=hook_count,
                effectiveness_score=0.7,
            ))
        
        # Check for social proof
        social_patterns = ["M+", "K+", "users", "customers", "people", "trusted"]
        social_count = sum(1 for ad in ads if any(p in ad.ad_text.lower() for p in social_patterns))
        if social_count > 0:
            patterns.append(CopyPattern(
                pattern_type="social_proof",
                examples=[ad.ad_text[:50] for ad in ads if any(p in ad.ad_text.lower() for p in social_patterns)][:3],
                frequency=social_count,
                effectiveness_score=0.8,
            ))
        
        # Check for urgency
        urgency_patterns = ["today", "now", "limited", "last chance", "hurry"]
        urgency_count = sum(1 for ad in ads if any(p in ad.ad_text.lower() for p in urgency_patterns))
        if urgency_count > 0:
            patterns.append(CopyPattern(
                pattern_type="urgency",
                examples=[ad.ad_text[:50] for ad in ads if any(p in ad.ad_text.lower() for p in urgency_patterns)][:3],
                frequency=urgency_count,
                effectiveness_score=0.6,
            ))
        
        # Check for questions
        question_count = sum(1 for ad in ads if "?" in ad.ad_text)
        if question_count > 0:
            patterns.append(CopyPattern(
                pattern_type="question",
                examples=[ad.ad_text[:50] for ad in ads if "?" in ad.ad_text][:3],
                frequency=question_count,
                effectiveness_score=0.65,
            ))
        
        return sorted(patterns, key=lambda p: p.frequency, reverse=True)
    
    def _analyze_visual_strategies(self, ads: list[CompetitorAd]) -> list[VisualStrategy]:
        """Analyze visual strategies."""
        strategies = []
        
        video_count = sum(1 for ad in ads if ad.ad_format == AdFormat.VIDEO)
        image_count = sum(1 for ad in ads if ad.ad_format == AdFormat.IMAGE)
        
        if image_count > 0:
            strategies.append(VisualStrategy(
                strategy_type="static_image",
                examples=["Product screenshots", "Lifestyle imagery"],
                frequency=image_count,
            ))
        
        if video_count > 0:
            strategies.append(VisualStrategy(
                strategy_type="video",
                examples=["Demo videos", "Testimonial clips"],
                frequency=video_count,
            ))
        
        return strategies
    
    def _extract_themes(self, ads: list[CompetitorAd]) -> list[str]:
        """Extract common themes from ads."""
        themes = []
        all_text = " ".join(ad.ad_text.lower() for ad in ads)
        
        if "free" in all_text:
            themes.append("Free trial/offer")
        if "easy" in all_text or "simple" in all_text:
            themes.append("Ease of use")
        if "fast" in all_text or "quick" in all_text:
            themes.append("Speed/efficiency")
        if "ai" in all_text or "smart" in all_text:
            themes.append("AI/Technology")
        if "save" in all_text:
            themes.append("Cost savings")
        
        return themes[:5]
    
    def _find_overused_phrases(self, ads: list[CompetitorAd]) -> list[str]:
        """Find overused phrases in the market."""
        overused = [
            "Get started today",
            "Limited time offer",
            "Join thousands",
            "Don't miss out",
            "Sign up now",
        ]
        return overused
    
    def _find_underutilized_angles(self, ads: list[CompetitorAd], industry: str) -> list[str]:
        """Find underutilized angles."""
        angles = {
            "career": [
                "Specific salary increase claims",
                "Industry-specific resume templates",
                "Recruiter perspective messaging",
                "Job search time reduction",
            ],
            "saas": [
                "Environmental impact",
                "Work-life balance benefits",
                "Security/privacy focus",
                "Integration ecosystem",
            ],
        }
        return angles.get(industry.lower(), [
            "Customer success stories",
            "Behind-the-scenes content",
            "Educational value-add",
            "Community building",
        ])
    
    def _get_dominant_platforms(self, ads: list[CompetitorAd]) -> list[str]:
        """Get dominant advertising platforms."""
        platform_counts: dict[str, int] = {}
        for ad in ads:
            for platform in ad.platforms:
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        sorted_platforms = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)
        return [p[0] for p in sorted_platforms[:3]]
    
    def _get_trending_formats(self, ads: list[CompetitorAd]) -> list[str]:
        """Get trending ad formats."""
        format_counts: dict[str, int] = {}
        for ad in ads:
            fmt = ad.ad_format.value
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        sorted_formats = sorted(format_counts.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in sorted_formats[:3]]
    
    def _generate_insights(
        self,
        competitors: list[CompetitorProfile],
        patterns: list[CopyPattern],
    ) -> list[CompetitorInsight]:
        """Generate actionable insights."""
        insights = []
        
        # High-spend competitors
        high_spenders = [c for c in competitors if c.threat_level in [CompetitorThreat.HIGH, CompetitorThreat.CRITICAL]]
        if high_spenders:
            insights.append(CompetitorInsight(
                insight_type="threat",
                title="High-Spend Competitors Detected",
                description=f"{len(high_spenders)} competitors are spending heavily on ads",
                action="Analyze their top-performing ad creatives for inspiration",
                priority=1,
                competitors_involved=[c.page_name for c in high_spenders],
            ))
        
        # Social proof is underused
        social_proof_pattern = next((p for p in patterns if p.pattern_type == "social_proof"), None)
        if not social_proof_pattern or social_proof_pattern.frequency < 5:
            insights.append(CompetitorInsight(
                insight_type="opportunity",
                title="Social Proof Underutilized",
                description="Competitors are not heavily using social proof in their ads",
                action="Add user counts, testimonials, or trust signals to stand out",
                priority=2,
                competitors_involved=[],
            ))
        
        # Video format opportunity
        video_users = sum(1 for c in competitors if c.ad_formats_used.get("video", 0) > 0)
        if video_users < len(competitors) / 2:
            insights.append(CompetitorInsight(
                insight_type="opportunity",
                title="Video Format Gap",
                description=f"Only {video_users}/{len(competitors)} competitors using video ads",
                action="Test video ads to differentiate and capture attention",
                priority=2,
                competitors_involved=[],
            ))
        
        return insights
    
    def _find_opportunities(
        self,
        competitors: list[CompetitorProfile],
        industry: str,
    ) -> list[str]:
        """Find market opportunities."""
        return [
            "Test messaging angles not used by competitors",
            "Target underserved audience segments",
            "Use video format if competitors focus on static",
            "Highlight unique features competitors lack",
            "Offer better/clearer pricing transparency",
        ]
    
    def _identify_threats(self, competitors: list[CompetitorProfile]) -> list[str]:
        """Identify market threats."""
        threats = []
        
        high_spenders = [c for c in competitors if c.threat_level == CompetitorThreat.CRITICAL]
        if high_spenders:
            threats.append(f"{len(high_spenders)} competitors with very high ad spend")
        
        prolific = [c for c in competitors if c.total_ads > 30]
        if prolific:
            threats.append(f"{len(prolific)} competitors running 30+ ad variants")
        
        return threats
    
    def _generate_recommendations(
        self,
        competitors: list[CompetitorProfile],
        patterns: list[CopyPattern],
        visuals: list[VisualStrategy],
    ) -> list[str]:
        """Generate strategic recommendations."""
        recommendations = []
        
        # Based on patterns
        high_freq_patterns = [p for p in patterns if p.frequency > 5]
        if high_freq_patterns:
            recommendations.append(
                f"Consider using {high_freq_patterns[0].pattern_type} pattern - competitors use it {high_freq_patterns[0].frequency}x"
            )
        
        # Based on visuals
        if any(v.strategy_type == "video" for v in visuals):
            recommendations.append("Test video ads - competitors are finding success with this format")
        
        # General recommendations
        recommendations.extend([
            "A/B test headlines against competitor messaging",
            "Monitor competitor ad changes weekly",
            "Focus on differentiation rather than imitation",
        ])
        
        return recommendations[:5]


def get_competitor_intel_analyzer() -> CompetitorIntelAnalyzer:
    """Get competitor intel analyzer."""
    return CompetitorIntelAnalyzer()


# =============================================================================
# DEMO
# =============================================================================

async def demo_competitor_intel():
    """Demo the competitor intel analyzer."""
    print("\n" + "="*60)
    print("COMPETITOR INTELLIGENCE DEMO")
    print("="*60)
    
    analyzer = CompetitorIntelAnalyzer()
    
    analysis = await analyzer.analyze_competitors(
        brand_name="Careerfied",
        industry="career",
        competitor_names=["Resume.io", "Zety", "Indeed"],
    )
    
    print(f"\n📊 {analysis.get_summary()}")
    
    print(f"\n🏢 Competitors Analyzed ({len(analysis.competitors)}):")
    for comp in analysis.competitors:
        threat_emoji = "🔴" if comp.threat_level == CompetitorThreat.CRITICAL else "🟠" if comp.threat_level == CompetitorThreat.HIGH else "🟡" if comp.threat_level == CompetitorThreat.MEDIUM else "🟢"
        print(f"   {threat_emoji} {comp.page_name}: {comp.total_ads} ads, ${comp.estimated_monthly_spend:,.0f}/mo")
    
    print(f"\n📝 Copy Patterns:")
    for pattern in analysis.industry_copy_patterns[:3]:
        print(f"   • {pattern.pattern_type}: {pattern.frequency}x used")
    
    print(f"\n💡 Key Insights ({len(analysis.insights)}):")
    for insight in analysis.insights[:3]:
        emoji = "⚠️" if insight.insight_type == "threat" else "✨" if insight.insight_type == "opportunity" else "📈"
        print(f"   {emoji} [{insight.priority}] {insight.title}")
        print(f"      → {insight.action}")
    
    print(f"\n🎯 Recommendations:")
    for rec in analysis.recommendations[:3]:
        print(f"   • {rec}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_competitor_intel())
