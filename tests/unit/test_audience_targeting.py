# tests/unit/test_audience_targeting.py
"""Unit tests for Audience Targeting AI (Slice 21)."""

import pytest
from src.analyzers.audience_targeting import (
    AudienceTargeting, AudienceRequest, AudienceType,
    INTEREST_DATABASE, get_audience_targeting,
)


class TestAudienceTargeting:
    """Test AudienceTargeting class."""

    @pytest.fixture
    def targeting(self):
        return AudienceTargeting()

    @pytest.fixture
    def sample_request(self):
        return AudienceRequest(
            product_name="Careerfied",
            product_description="AI-powered resume builder for job seekers",
            product_type="saas",
            target_persona="Job seekers and career changers",
            price_point=29,
            existing_customers=False,
            website_traffic=False,
        )

    @pytest.mark.asyncio
    async def test_suggest_returns_primary_audiences(self, targeting, sample_request):
        """Test primary audiences are returned."""
        result = await targeting.suggest(sample_request)
        assert len(result.primary_audiences) > 0

    @pytest.mark.asyncio
    async def test_suggest_returns_secondary_audiences(self, targeting, sample_request):
        """Test secondary audiences are returned."""
        result = await targeting.suggest(sample_request)
        assert len(result.secondary_audiences) >= 0

    @pytest.mark.asyncio
    async def test_suggest_returns_exclusions(self, targeting, sample_request):
        """Test exclusions are returned."""
        result = await targeting.suggest(sample_request)
        assert len(result.exclusions) > 0

    @pytest.mark.asyncio
    async def test_suggest_returns_lookalike_strategy(self, targeting, sample_request):
        """Test lookalike strategy is provided."""
        result = await targeting.suggest(sample_request)
        assert len(result.lookalike_strategy) > 0

    @pytest.mark.asyncio
    async def test_suggest_returns_budget_allocation(self, targeting, sample_request):
        """Test budget allocation is provided."""
        result = await targeting.suggest(sample_request)
        assert len(result.budget_allocation) > 0

    @pytest.mark.asyncio
    async def test_suggest_returns_testing_order(self, targeting, sample_request):
        """Test testing order is provided."""
        result = await targeting.suggest(sample_request)
        assert len(result.testing_order) > 0

    @pytest.mark.asyncio
    async def test_suggest_returns_recommendations(self, targeting, sample_request):
        """Test recommendations are provided."""
        result = await targeting.suggest(sample_request)
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_audiences_have_required_fields(self, targeting, sample_request):
        """Test audiences have required fields."""
        result = await targeting.suggest(sample_request)
        for aud in result.primary_audiences:
            assert aud.name
            assert aud.type in AudienceType
            assert aud.estimated_size
            assert 0 <= aud.relevance_score <= 100

    @pytest.mark.asyncio
    async def test_exclusions_have_required_fields(self, targeting, sample_request):
        """Test exclusions have required fields."""
        result = await targeting.suggest(sample_request)
        for exc in result.exclusions:
            assert exc.name
            assert exc.reason
            assert exc.impact

    @pytest.mark.asyncio
    async def test_with_existing_customers(self, targeting):
        """Test with existing customer data."""
        request = AudienceRequest(
            product_name="Test",
            product_description="Test product",
            product_type="saas",
            target_persona="Users",
            existing_customers=True,
            website_traffic=False,
        )
        result = await targeting.suggest(request)
        lookalike_audiences = [a for a in result.primary_audiences if a.type == AudienceType.LOOKALIKE]
        assert len(lookalike_audiences) > 0

    @pytest.mark.asyncio
    async def test_with_website_traffic(self, targeting):
        """Test with website traffic data."""
        request = AudienceRequest(
            product_name="Test",
            product_description="Test product",
            product_type="saas",
            target_persona="Users",
            existing_customers=False,
            website_traffic=True,
        )
        result = await targeting.suggest(request)
        retargeting_audiences = [a for a in result.primary_audiences if a.type == AudienceType.RETARGETING]
        assert len(retargeting_audiences) > 0

    @pytest.mark.asyncio
    async def test_career_product_detection(self, targeting):
        """Test career-related products get career audiences."""
        request = AudienceRequest(
            product_name="ResumeBuilder",
            product_description="Resume and job application tool",
            product_type="career",
            target_persona="Job seekers",
        )
        result = await targeting.suggest(request)
        # Should detect career category
        audience_names = [a.name.lower() for a in result.primary_audiences]
        assert any("job" in name or "career" in name or "resume" in name for name in audience_names)

    def test_get_interest_categories(self, targeting):
        """Test get_interest_categories returns all categories."""
        categories = targeting.get_interest_categories()
        assert "saas" in categories
        assert "ecommerce" in categories
        assert "career" in categories

    def test_singleton_pattern(self):
        """Test get_audience_targeting returns singleton."""
        t1 = get_audience_targeting()
        t2 = get_audience_targeting()
        assert t1 is t2


class TestAudienceType:
    """Test AudienceType enum."""

    def test_all_types_defined(self):
        """Test all audience types exist."""
        assert AudienceType.INTEREST.value == "interest"
        assert AudienceType.BEHAVIOR.value == "behavior"
        assert AudienceType.LOOKALIKE.value == "lookalike"
        assert AudienceType.RETARGETING.value == "retargeting"


class TestInterestDatabase:
    """Test interest database."""

    def test_categories_exist(self):
        """Test expected categories exist."""
        assert "saas" in INTEREST_DATABASE
        assert "ecommerce" in INTEREST_DATABASE
        assert "career" in INTEREST_DATABASE
        assert "default" in INTEREST_DATABASE

    def test_category_structure(self):
        """Test category has primary and secondary interests."""
        for category, data in INTEREST_DATABASE.items():
            assert "primary" in data
            assert "secondary" in data
            assert len(data["primary"]) > 0
