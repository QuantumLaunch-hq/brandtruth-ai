# tests/unit/test_landing_page_analyzer.py
"""Unit tests for Landing Page Analyzer (Slice 17)."""

import pytest
from src.analyzers.landing_page_analyzer import (
    LandingPageAnalyzer, LandingPageRequest, MessageMatchLevel,
    get_landing_page_analyzer,
)


class TestLandingPageAnalyzer:
    """Test LandingPageAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        return LandingPageAnalyzer()

    @pytest.fixture
    def sample_request(self):
        return LandingPageRequest(
            landing_page_url="https://careerfied.ai",
            ad_headline="Stop Getting Rejected",
            ad_primary_text="Build ATS-optimized resumes in minutes",
            ad_cta="Get Started Free",
        )

    @pytest.mark.asyncio
    async def test_analyze_returns_overall_score(self, analyzer, sample_request):
        """Test overall score is returned."""
        result = await analyzer.analyze(sample_request)
        assert 0 <= result.overall_score <= 100

    @pytest.mark.asyncio
    async def test_analyze_returns_message_match_score(self, analyzer, sample_request):
        """Test message match score is calculated."""
        result = await analyzer.analyze(sample_request)
        assert 0 <= result.message_match_score <= 100

    @pytest.mark.asyncio
    async def test_analyze_returns_message_match_level(self, analyzer, sample_request):
        """Test message match level is set."""
        result = await analyzer.analyze(sample_request)
        assert result.message_match_level in MessageMatchLevel

    @pytest.mark.asyncio
    async def test_analyze_returns_component_scores(self, analyzer, sample_request):
        """Test all component scores are returned."""
        result = await analyzer.analyze(sample_request)
        assert 0 <= result.above_fold_score <= 100
        assert 0 <= result.cta_score <= 100
        assert 0 <= result.mobile_score <= 100
        assert 0 <= result.load_speed_score <= 100

    @pytest.mark.asyncio
    async def test_analyze_returns_url(self, analyzer, sample_request):
        """Test URL is preserved in result."""
        result = await analyzer.analyze(sample_request)
        assert result.url == sample_request.landing_page_url

    @pytest.mark.asyncio
    async def test_analyze_returns_recommendations(self, analyzer, sample_request):
        """Test recommendations are provided."""
        result = await analyzer.analyze(sample_request)
        assert isinstance(result.recommendations, list)

    @pytest.mark.asyncio
    async def test_analyze_returns_summary(self, analyzer, sample_request):
        """Test summary is generated."""
        result = await analyzer.analyze(sample_request)
        summary = result.get_summary()
        assert "Score" in summary or "score" in summary.lower()

    @pytest.mark.asyncio
    async def test_message_match_levels(self, analyzer):
        """Test different match levels based on score."""
        # High match
        req = LandingPageRequest(
            landing_page_url="https://test.com",
            ad_headline="Transform Career Today",
            ad_primary_text="AI resume builder",
            ad_cta="Get Started",
        )
        result = await analyzer.analyze(req)
        assert result.message_match_level in MessageMatchLevel

    def test_singleton_pattern(self):
        """Test get_landing_page_analyzer returns singleton."""
        a1 = get_landing_page_analyzer()
        a2 = get_landing_page_analyzer()
        assert a1 is a2


class TestMessageMatchLevel:
    """Test MessageMatchLevel enum."""

    def test_all_levels_defined(self):
        """Test all levels exist."""
        assert MessageMatchLevel.EXCELLENT.value == "excellent"
        assert MessageMatchLevel.GOOD.value == "good"
        assert MessageMatchLevel.FAIR.value == "fair"
        assert MessageMatchLevel.POOR.value == "poor"
        assert MessageMatchLevel.MISMATCH.value == "mismatch"
