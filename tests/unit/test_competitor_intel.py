# tests/unit/test_competitor_intel.py
"""Unit tests for Competitor Intelligence (Slice 12)."""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analyzers.competitor_intel import (
    CompetitorIntelAnalyzer,
    CompetitorAnalysis,
    CompetitorProfile,
    CompetitorAd,
    CompetitorInsight,
    CopyPattern,
    VisualStrategy,
    CompetitorThreat,
    AdCategory,
    AdFormat,
    CompetitorIntelConfig,
    get_competitor_intel_analyzer,
)


class TestCompetitorThreat:
    """Tests for CompetitorThreat enum."""
    
    def test_all_levels_exist(self):
        """Test all threat levels exist."""
        assert CompetitorThreat.LOW.value == "low"
        assert CompetitorThreat.MEDIUM.value == "medium"
        assert CompetitorThreat.HIGH.value == "high"
        assert CompetitorThreat.CRITICAL.value == "critical"


class TestAdFormat:
    """Tests for AdFormat enum."""
    
    def test_all_formats_exist(self):
        """Test all formats exist."""
        assert AdFormat.IMAGE.value == "image"
        assert AdFormat.VIDEO.value == "video"
        assert AdFormat.CAROUSEL.value == "carousel"


class TestCompetitorAd:
    """Tests for CompetitorAd model."""
    
    def test_create_ad(self):
        """Test creating competitor ad."""
        ad = CompetitorAd(
            ad_id="ad_001",
            page_id="page_test",
            page_name="Test Company",
            ad_text="Test ad text",
            cta="Learn More",
            ad_format=AdFormat.IMAGE,
        )
        
        assert ad.page_name == "Test Company"
        assert ad.ad_format == AdFormat.IMAGE
        assert ad.is_active is True  # default


class TestCopyPattern:
    """Tests for CopyPattern model."""
    
    def test_create_pattern(self):
        """Test creating copy pattern."""
        pattern = CopyPattern(
            pattern_type="hook",
            examples=["Example 1", "Example 2"],
            frequency=10,
            effectiveness_score=0.8,
        )
        
        assert pattern.pattern_type == "hook"
        assert pattern.frequency == 10
        assert pattern.effectiveness_score == 0.8


class TestCompetitorProfile:
    """Tests for CompetitorProfile model."""
    
    def test_create_profile(self):
        """Test creating competitor profile."""
        profile = CompetitorProfile(
            page_id="page_test",
            page_name="Test Competitor",
            industry="saas",
            total_ads=25,
            active_ads=20,
            estimated_monthly_spend=5000,
            primary_platforms=["facebook", "instagram"],
            ad_formats_used={"image": 15, "video": 10},
            top_performing_themes=["Free trial", "Ease of use"],
            copy_patterns=[],
            visual_strategies=[],
            common_ctas=["Get Started", "Try Free"],
            threat_level=CompetitorThreat.MEDIUM,
        )
        
        assert profile.page_name == "Test Competitor"
        assert profile.total_ads == 25
        assert profile.threat_level == CompetitorThreat.MEDIUM


class TestCompetitorInsight:
    """Tests for CompetitorInsight model."""
    
    def test_create_insight(self):
        """Test creating insight."""
        insight = CompetitorInsight(
            insight_type="opportunity",
            title="Video Format Gap",
            description="Competitors not using video",
            action="Test video ads",
            priority=1,
            competitors_involved=["Comp A", "Comp B"],
        )
        
        assert insight.insight_type == "opportunity"
        assert insight.priority == 1
        assert len(insight.competitors_involved) == 2


class TestCompetitorIntelConfig:
    """Tests for CompetitorIntelConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CompetitorIntelConfig()
        
        assert config.max_ads_per_competitor == 50
        assert config.lookback_days == 90
        assert "US" in config.countries
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CompetitorIntelConfig(
            max_ads_per_competitor=100,
            lookback_days=180,
            countries=["US", "UK", "CA"],
        )
        
        assert config.max_ads_per_competitor == 100
        assert len(config.countries) == 3


class TestCompetitorIntelAnalyzer:
    """Tests for CompetitorIntelAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return CompetitorIntelAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_career_industry(self, analyzer):
        """Test analyzing career industry."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Careerfied",
            industry="career",
            competitor_names=["Resume.io", "Zety"],
        )
        
        assert isinstance(analysis, CompetitorAnalysis)
        assert analysis.brand_name == "Careerfied"
        assert analysis.industry == "career"
        assert len(analysis.competitors) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_saas_industry(self, analyzer):
        """Test analyzing SaaS industry."""
        analysis = await analyzer.analyze_competitors(
            brand_name="TestApp",
            industry="saas",
        )
        
        assert analysis.industry == "saas"
        assert analysis.total_competitor_ads > 0
    
    @pytest.mark.asyncio
    async def test_analysis_has_competitors(self, analyzer):
        """Test that analysis includes competitor profiles."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Test",
            industry="career",
        )
        
        for comp in analysis.competitors:
            assert comp.page_name
            assert comp.total_ads >= 0
            assert comp.threat_level in CompetitorThreat
    
    @pytest.mark.asyncio
    async def test_analysis_has_copy_patterns(self, analyzer):
        """Test that analysis includes copy patterns."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Test",
            industry="career",
        )
        
        assert len(analysis.industry_copy_patterns) > 0
        for pattern in analysis.industry_copy_patterns:
            assert pattern.pattern_type
            assert pattern.frequency >= 0
    
    @pytest.mark.asyncio
    async def test_analysis_has_insights(self, analyzer):
        """Test that analysis includes insights."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Test",
            industry="career",
            competitor_names=["Resume.io", "Zety", "Indeed"],
        )
        
        # Should generate at least one insight
        assert len(analysis.insights) > 0
        for insight in analysis.insights:
            assert insight.title
            assert insight.action
            assert 1 <= insight.priority <= 5
    
    @pytest.mark.asyncio
    async def test_analysis_has_recommendations(self, analyzer):
        """Test that analysis includes recommendations."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Test",
            industry="career",
        )
        
        assert len(analysis.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_analysis_has_market_metrics(self, analyzer):
        """Test that analysis includes market metrics."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Test",
            industry="career",
        )
        
        assert analysis.market_ad_spend_estimate >= 0
        assert len(analysis.dominant_platforms) > 0
        assert len(analysis.trending_formats) > 0
    
    @pytest.mark.asyncio
    async def test_analysis_opportunities_and_threats(self, analyzer):
        """Test that analysis includes opportunities and threats."""
        analysis = await analyzer.analyze_competitors(
            brand_name="Test",
            industry="career",
        )
        
        assert len(analysis.opportunities) > 0
        # Threats might be empty if no high-threat competitors


class TestCompetitorAnalysis:
    """Tests for CompetitorAnalysis model."""
    
    def test_get_summary(self):
        """Test summary generation."""
        analysis = CompetitorAnalysis(
            analysis_id="test_001",
            brand_name="Test",
            industry="career",
            competitors=[
                CompetitorProfile(
                    page_id="p1",
                    page_name="Comp1",
                    industry="career",
                    total_ads=10,
                    active_ads=8,
                    estimated_monthly_spend=5000,
                    primary_platforms=["facebook"],
                    ad_formats_used={},
                    top_performing_themes=[],
                    copy_patterns=[],
                    visual_strategies=[],
                    common_ctas=[],
                    threat_level=CompetitorThreat.MEDIUM,
                ),
            ],
            total_competitor_ads=10,
            market_ad_spend_estimate=5000,
            dominant_platforms=["facebook"],
            trending_formats=["image"],
            industry_copy_patterns=[],
            overused_phrases=[],
            underutilized_angles=[],
            visual_trends=[],
            insights=[],
            opportunities=[],
            threats=[],
            recommendations=[],
        )
        
        summary = analysis.get_summary()
        
        assert "1 competitor" in summary.lower() or "1" in summary
        assert "5,000" in summary or "5000" in summary


class TestGetCompetitorIntelAnalyzer:
    """Tests for factory function."""
    
    def test_returns_analyzer(self):
        """Test factory returns analyzer."""
        analyzer = get_competitor_intel_analyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "analyze_competitors")
