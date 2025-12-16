# tests/unit/test_budget_simulator.py
"""Unit tests for Budget Simulator (Slice 18)."""

import pytest
from src.analyzers.budget_simulator import (
    BudgetSimulator, BudgetRequest, Industry, CampaignGoal, BudgetTier,
    INDUSTRY_BENCHMARKS, get_budget_simulator,
)


class TestBudgetSimulator:
    """Test BudgetSimulator class."""

    @pytest.fixture
    def simulator(self):
        return BudgetSimulator()

    @pytest.fixture
    def sample_request(self):
        return BudgetRequest(
            industry=Industry.SAAS,
            goal=CampaignGoal.LEADS,
            product_price=99.0,
            target_monthly_conversions=50,
            target_cpa=None,
        )

    @pytest.mark.asyncio
    async def test_simulate_returns_daily_budget(self, simulator, sample_request):
        """Test daily budget is calculated."""
        result = await simulator.simulate(sample_request)
        assert result.daily_budget > 0

    @pytest.mark.asyncio
    async def test_simulate_returns_monthly_budget(self, simulator, sample_request):
        """Test monthly budget is calculated."""
        result = await simulator.simulate(sample_request)
        assert result.monthly_budget == pytest.approx(result.daily_budget * 30, rel=0.01)

    @pytest.mark.asyncio
    async def test_simulate_returns_budget_tier(self, simulator, sample_request):
        """Test budget tier is assigned."""
        result = await simulator.simulate(sample_request)
        assert result.tier in BudgetTier

    @pytest.mark.asyncio
    async def test_simulate_returns_expected_metrics(self, simulator, sample_request):
        """Test all expected metrics are returned."""
        result = await simulator.simulate(sample_request)
        assert result.expected_impressions > 0
        assert result.expected_clicks > 0
        assert result.expected_conversions >= 0
        assert result.expected_cpa > 0
        assert result.expected_roas >= 0

    @pytest.mark.asyncio
    async def test_simulate_returns_break_even_days(self, simulator, sample_request):
        """Test break-even days is calculated."""
        result = await simulator.simulate(sample_request)
        assert 1 <= result.break_even_days <= 90

    @pytest.mark.asyncio
    async def test_simulate_returns_recommendations(self, simulator, sample_request):
        """Test recommendations are provided."""
        result = await simulator.simulate(sample_request)
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_simulate_with_target_cpa(self, simulator):
        """Test simulation with custom target CPA."""
        request = BudgetRequest(
            industry=Industry.SAAS,
            goal=CampaignGoal.LEADS,
            product_price=99.0,
            target_monthly_conversions=50,
            target_cpa=50.0,
        )
        result = await simulator.simulate(request)
        assert result.daily_budget > 0

    @pytest.mark.asyncio
    async def test_different_industries(self, simulator):
        """Test simulation works for all industries."""
        for industry in Industry:
            request = BudgetRequest(
                industry=industry,
                goal=CampaignGoal.LEADS,
                product_price=99.0,
                target_monthly_conversions=50,
            )
            result = await simulator.simulate(request)
            assert result.daily_budget > 0

    @pytest.mark.asyncio
    async def test_different_goals(self, simulator):
        """Test simulation works for all goals."""
        for goal in CampaignGoal:
            request = BudgetRequest(
                industry=Industry.SAAS,
                goal=goal,
                product_price=99.0,
                target_monthly_conversions=50,
            )
            result = await simulator.simulate(request)
            assert result.daily_budget > 0

    def test_get_benchmarks_all(self, simulator):
        """Test get_benchmarks returns all industries."""
        benchmarks = simulator.get_benchmarks()
        assert len(benchmarks) == len(Industry)

    def test_get_benchmarks_single(self, simulator):
        """Test get_benchmarks returns single industry."""
        benchmarks = simulator.get_benchmarks(Industry.SAAS)
        assert "saas" in benchmarks
        assert len(benchmarks) == 1

    def test_singleton_pattern(self):
        """Test get_budget_simulator returns singleton."""
        s1 = get_budget_simulator()
        s2 = get_budget_simulator()
        assert s1 is s2


class TestIndustryBenchmarks:
    """Test industry benchmark data."""

    def test_all_industries_have_benchmarks(self):
        """Test all industries have benchmark data."""
        for industry in Industry:
            assert industry in INDUSTRY_BENCHMARKS

    def test_benchmark_structure(self):
        """Test benchmark data structure."""
        for industry, data in INDUSTRY_BENCHMARKS.items():
            assert "cpm" in data
            assert "ctr" in data
            assert "cvr" in data
            assert "avg_cpa" in data


class TestBudgetTier:
    """Test BudgetTier enum."""

    def test_all_tiers_defined(self):
        """Test all tiers exist."""
        assert BudgetTier.STARTER.value == "starter"
        assert BudgetTier.GROWTH.value == "growth"
        assert BudgetTier.SCALE.value == "scale"
        assert BudgetTier.ENTERPRISE.value == "enterprise"
