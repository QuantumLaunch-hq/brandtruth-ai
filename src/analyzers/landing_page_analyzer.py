# src/analyzers/landing_page_analyzer.py
"""Landing Page Analyzer - Analyzes LP quality and ad-to-page match.

Checks:
- Message match (does LP deliver on ad promise?)
- Above-fold effectiveness
- CTA clarity and placement
- Mobile experience
- Load speed impact
"""

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MessageMatchLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    MISMATCH = "mismatch"


class LandingPageIssue(BaseModel):
    category: str
    severity: str  # critical, warning, info
    message: str
    recommendation: str


class LandingPageAnalysis(BaseModel):
    url: str
    overall_score: int = Field(ge=0, le=100)
    message_match_score: int = Field(ge=0, le=100)
    message_match_level: MessageMatchLevel
    above_fold_score: int = Field(ge=0, le=100)
    cta_score: int = Field(ge=0, le=100)
    mobile_score: int = Field(ge=0, le=100)
    load_speed_score: int = Field(ge=0, le=100)
    issues: list[LandingPageIssue] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    ad_promise: str = ""
    lp_headline: str = ""
    
    def get_summary(self) -> str:
        return f"LP Score: {self.overall_score}/100 | Message Match: {self.message_match_level.value}"


class LandingPageRequest(BaseModel):
    landing_page_url: str
    ad_headline: str
    ad_primary_text: str
    ad_cta: str = "Learn More"


class LandingPageAnalyzer:
    def __init__(self):
        pass
    
    async def analyze(self, request: LandingPageRequest) -> LandingPageAnalysis:
        logger.info(f"Analyzing landing page: {request.landing_page_url}")
        
        # Simulate LP analysis (would scrape real page in production)
        lp_data = await self._fetch_landing_page(request.landing_page_url)
        
        # Calculate scores
        message_match = self._calculate_message_match(request, lp_data)
        above_fold = self._analyze_above_fold(lp_data)
        cta_score = self._analyze_cta(lp_data)
        mobile_score = self._analyze_mobile(lp_data)
        speed_score = self._analyze_speed(lp_data)
        
        # Calculate overall score (weighted)
        overall = int(
            message_match * 0.35 +
            above_fold * 0.25 +
            cta_score * 0.20 +
            mobile_score * 0.10 +
            speed_score * 0.10
        )
        
        # Determine match level
        if message_match >= 85:
            match_level = MessageMatchLevel.EXCELLENT
        elif message_match >= 70:
            match_level = MessageMatchLevel.GOOD
        elif message_match >= 50:
            match_level = MessageMatchLevel.FAIR
        elif message_match >= 30:
            match_level = MessageMatchLevel.POOR
        else:
            match_level = MessageMatchLevel.MISMATCH
        
        # Identify issues
        issues = self._identify_issues(message_match, above_fold, cta_score, mobile_score, speed_score, request)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues, match_level)
        
        return LandingPageAnalysis(
            url=request.landing_page_url,
            overall_score=overall,
            message_match_score=message_match,
            message_match_level=match_level,
            above_fold_score=above_fold,
            cta_score=cta_score,
            mobile_score=mobile_score,
            load_speed_score=speed_score,
            issues=issues,
            recommendations=recommendations,
            ad_promise=request.ad_headline,
            lp_headline=lp_data.get("headline", ""),
        )
    
    async def _fetch_landing_page(self, url: str) -> dict:
        """Fetch and parse landing page (simulated)."""
        # In production, would use httpx + BeautifulSoup
        return {
            "headline": "Transform Your Career Today",
            "subheadline": "AI-powered resume builder",
            "cta_text": "Get Started Free",
            "cta_visible": True,
            "has_hero_image": True,
            "mobile_friendly": True,
            "load_time_ms": 1200,
            "word_count_above_fold": 45,
            "testimonials_count": 3,
            "trust_badges": True,
        }
    
    def _calculate_message_match(self, request: LandingPageRequest, lp_data: dict) -> int:
        """Calculate how well LP matches ad promise."""
        score = 70  # Base score
        
        # Check keyword overlap
        ad_words = set(request.ad_headline.lower().split())
        lp_words = set(lp_data.get("headline", "").lower().split())
        overlap = len(ad_words & lp_words) / max(len(ad_words), 1)
        score += int(overlap * 20)
        
        # Check CTA consistency
        if request.ad_cta.lower() in lp_data.get("cta_text", "").lower():
            score += 10
        
        return min(score, 100)
    
    def _analyze_above_fold(self, lp_data: dict) -> int:
        score = 60
        if lp_data.get("has_hero_image"):
            score += 15
        if lp_data.get("cta_visible"):
            score += 15
        if 30 <= lp_data.get("word_count_above_fold", 0) <= 60:
            score += 10
        return min(score, 100)
    
    def _analyze_cta(self, lp_data: dict) -> int:
        score = 50
        if lp_data.get("cta_visible"):
            score += 30
        if lp_data.get("cta_text"):
            score += 20
        return min(score, 100)
    
    def _analyze_mobile(self, lp_data: dict) -> int:
        return 85 if lp_data.get("mobile_friendly") else 40
    
    def _analyze_speed(self, lp_data: dict) -> int:
        load_time = lp_data.get("load_time_ms", 3000)
        if load_time < 1000:
            return 95
        elif load_time < 2000:
            return 80
        elif load_time < 3000:
            return 60
        else:
            return 40
    
    def _identify_issues(self, message: int, fold: int, cta: int, mobile: int, speed: int, req: LandingPageRequest) -> list[LandingPageIssue]:
        issues = []
        
        if message < 50:
            issues.append(LandingPageIssue(
                category="Message Match",
                severity="critical",
                message=f"Ad promises '{req.ad_headline}' but LP doesn't clearly deliver",
                recommendation="Align LP headline with ad promise or create dedicated landing page"
            ))
        
        if cta < 70:
            issues.append(LandingPageIssue(
                category="CTA",
                severity="warning",
                message="CTA not immediately visible above the fold",
                recommendation="Move primary CTA above the fold with contrasting color"
            ))
        
        if speed < 60:
            issues.append(LandingPageIssue(
                category="Speed",
                severity="warning",
                message="Page load time over 2 seconds may hurt conversions",
                recommendation="Optimize images, enable caching, consider CDN"
            ))
        
        if mobile < 70:
            issues.append(LandingPageIssue(
                category="Mobile",
                severity="critical",
                message="Page not optimized for mobile devices",
                recommendation="Implement responsive design - 60%+ of ad clicks are mobile"
            ))
        
        return issues
    
    def _generate_recommendations(self, issues: list[LandingPageIssue], match_level: MessageMatchLevel) -> list[str]:
        recs = []
        
        if match_level in [MessageMatchLevel.POOR, MessageMatchLevel.MISMATCH]:
            recs.append("Create a dedicated landing page that matches your ad messaging")
        
        critical_count = sum(1 for i in issues if i.severity == "critical")
        if critical_count > 0:
            recs.append(f"Address {critical_count} critical issue(s) before scaling ad spend")
        
        recs.append("A/B test your landing page headline to improve message match")
        recs.append("Add social proof (testimonials, logos) above the fold")
        
        return recs


_instance: Optional[LandingPageAnalyzer] = None

def get_landing_page_analyzer() -> LandingPageAnalyzer:
    global _instance
    if _instance is None:
        _instance = LandingPageAnalyzer()
    return _instance
