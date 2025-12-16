# tests/unit/test_platform_recommender.py
"""Unit tests for Platform Recommender (Slice 19)."""

import pytest
from src.analyzers.platform_recommender import (
    PlatformRecommender, PlatformRequest, Platform, ProductType, AudienceType,
    PLATFORM_DATA, get_platform_recommender,
)


class TestPlatformRecommender:
    """Test PlatformRecommender class."""

    @pytest.fixture
    def recommender(self):
        return PlatformRecommender()

    @pytest.fixture
    def sample_request(self):
        return PlatformRequest(
            product_type=ProductType.B2B_SAAS,
            audience_type=AudienceType.FOUNDERS,
            monthly_budget=1000,
            product_price=99,
            is_visual=True,
        )

    @pytest.mark.asyncio
    async def test_recommend_returns_primary_platform(self, recommender, sample_request):
        """Test primary platform is selected."""
        result = await recommender.recommend(sample_request)
        assert result.primary_platform in Platform

    @pytest.mark.asyncio
    async def test_recommend_returns_strategy(self, recommender, sample_request):
        """Test strategy is provided."""
        result = await recommender.recommend(sample_request)
        assert len(result.strategy) > 0

    @pytest.mark.asyncio
    async def test_recommend_returns_budget_allocation(self, recommender, sample_request):
        """Test budget allocation is provided."""
        result = await recommender.recommend(sample_request)
        assert len(result.budget_allocation) > 0
        assert sum(result.budget_allocation.values()) <= 100

    @pytest.mark.asyncio
    async def test_recommend_returns_all_platforms_ranked(self, recommender, sample_request):
        """Test all platforms are ranked."""
        result = await recommender.recommend(sample_request)
        assert len(result.recommendations) >= 5

    @pytest.mark.asyncio
    async def test_recommendations_sorted_by_score(self, recommender, sample_request):
        """Test recommendations are sorted by score descending."""
        result = await recommender.recommend(sample_request)
        scores = [r.score for r in result.recommendations]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_recommendations_have_required_fields(self, recommender, sample_request):
        """Test each recommendation has required fields."""
        result = await recommender.recommend(sample_request)
        for rec in result.recommendations:
            assert rec.platform in Platform
            assert 0 <= rec.score <= 100
            assert rec.rank > 0
            assert rec.min_budget > 0
            assert len(rec.strengths) > 0
            assert len(rec.best_formats) > 0

    @pytest.mark.asyncio
    async def test_different_product_types(self, recommender):
        """Test all product types work."""
        for pt in ProductType:
            request = PlatformRequest(
                product_type=pt,
                audience_type=AudienceType.CONSUMERS,
                monthly_budget=1000,
            )
            result = await recommender.recommend(request)
            assert result.primary_platform is not None

    @pytest.mark.asyncio
    async def test_different_audience_types(self, recommender):
        """Test all audience types work."""
        for at in AudienceType:
            request = PlatformRequest(
                product_type=ProductType.B2C_SAAS,
                audience_type=at,
                monthly_budget=1000,
            )
            result = await recommender.recommend(request)
            assert result.primary_platform is not None

    @pytest.mark.asyncio
    async def test_low_budget_strategy(self, recommender):
        """Test low budget gets focused strategy."""
        request = PlatformRequest(
            product_type=ProductType.B2B_SAAS,
            audience_type=AudienceType.FOUNDERS,
            monthly_budget=300,
        )
        result = await recommender.recommend(request)
        assert "focus" in result.strategy.lower() or "100%" in result.strategy

    @pytest.mark.asyncio
    async def test_high_budget_strategy(self, recommender):
        """Test high budget gets diversified strategy."""
        request = PlatformRequest(
            product_type=ProductType.B2B_SAAS,
            audience_type=AudienceType.FOUNDERS,
            monthly_budget=5000,
        )
        result = await recommender.recommend(request)
        assert "diversify" in result.strategy.lower() or len(result.budget_allocation) > 1

    def test_get_platforms(self, recommender):
        """Test get_platforms returns all platforms."""
        platforms = recommender.get_platforms()
        assert len(platforms) == len(Platform)

    def test_singleton_pattern(self):
        """Test get_platform_recommender returns singleton."""
        r1 = get_platform_recommender()
        r2 = get_platform_recommender()
        assert r1 is r2


class TestPlatformData:
    """Test platform data structure."""

    def test_all_platforms_have_data(self):
        """Test all platforms have configuration."""
        for platform in Platform:
            assert platform in PLATFORM_DATA

    def test_platform_data_structure(self):
        """Test platform data has required fields."""
        for platform, data in PLATFORM_DATA.items():
            assert "min_budget" in data
            assert "best_for" in data
            assert "audiences" in data
            assert "strengths" in data
            assert "weaknesses" in data
            assert "formats" in data
            assert "cpa_range" in data
