# tests/unit/test_ab_test_planner.py
"""Unit tests for A/B Test Planner (Slice 20)."""

import pytest
from src.analyzers.ab_test_planner import (
    ABTestPlanner, ABTestRequest, TestElement, TestPriority,
    get_ab_test_planner,
)


class TestABTestPlanner:
    """Test ABTestPlanner class."""

    @pytest.fixture
    def planner(self):
        return ABTestPlanner()

    @pytest.fixture
    def sample_request(self):
        return ABTestRequest(
            variants=[
                {"headline": "Stop Getting Rejected", "primary_text": "Build resumes fast", "cta": "Get Started"},
                {"headline": "Land More Interviews", "primary_text": "AI-powered resumes", "cta": "Try Free"},
            ],
            baseline_ctr=1.0,
            baseline_cvr=2.0,
            daily_budget=50,
            confidence_level=0.95,
            minimum_lift=0.20,
        )

    @pytest.mark.asyncio
    async def test_plan_returns_test_pairs(self, planner, sample_request):
        """Test plan returns test pairs."""
        result = await planner.plan(sample_request)
        assert len(result.test_pairs) > 0

    @pytest.mark.asyncio
    async def test_plan_returns_sample_size(self, planner, sample_request):
        """Test required sample size is calculated."""
        result = await planner.plan(sample_request)
        assert result.required_sample_size > 0

    @pytest.mark.asyncio
    async def test_plan_returns_estimated_days(self, planner, sample_request):
        """Test estimated days is calculated."""
        result = await planner.plan(sample_request)
        assert result.estimated_days >= 7

    @pytest.mark.asyncio
    async def test_plan_returns_testing_sequence(self, planner, sample_request):
        """Test testing sequence is provided."""
        result = await planner.plan(sample_request)
        assert len(result.testing_sequence) > 0

    @pytest.mark.asyncio
    async def test_plan_returns_recommendations(self, planner, sample_request):
        """Test recommendations are provided."""
        result = await planner.plan(sample_request)
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_test_pairs_have_required_fields(self, planner, sample_request):
        """Test test pairs have all required fields."""
        result = await planner.plan(sample_request)
        for pair in result.test_pairs:
            assert pair.element in TestElement
            assert pair.variant_a
            assert pair.variant_b
            assert pair.hypothesis
            assert pair.priority in TestPriority
            assert pair.expected_lift

    @pytest.mark.asyncio
    async def test_headline_test_is_high_priority(self, planner, sample_request):
        """Test headline tests are marked high priority."""
        result = await planner.plan(sample_request)
        headline_tests = [p for p in result.test_pairs if p.element == TestElement.HEADLINE]
        if headline_tests:
            assert headline_tests[0].priority == TestPriority.HIGH

    @pytest.mark.asyncio
    async def test_higher_budget_fewer_days(self, planner):
        """Test higher budget reduces estimated days."""
        low_budget = ABTestRequest(
            variants=[{"headline": "A"}, {"headline": "B"}],
            daily_budget=20,
        )
        high_budget = ABTestRequest(
            variants=[{"headline": "A"}, {"headline": "B"}],
            daily_budget=200,
        )
        low_result = await planner.plan(low_budget)
        high_result = await planner.plan(high_budget)
        assert high_result.estimated_days <= low_result.estimated_days

    def test_calculate_significance_significant(self, planner):
        """Test significance calculation with significant results."""
        result = planner.calculate_significance(
            control_conversions=100,
            control_visitors=5000,
            variant_conversions=150,
            variant_visitors=5000,
        )
        assert result["is_significant"] == True
        assert result["lift"] > 0

    def test_calculate_significance_not_significant(self, planner):
        """Test significance calculation with non-significant results."""
        result = planner.calculate_significance(
            control_conversions=100,
            control_visitors=5000,
            variant_conversions=102,
            variant_visitors=5000,
        )
        assert result["is_significant"] == False

    def test_calculate_significance_returns_rates(self, planner):
        """Test significance returns conversion rates."""
        result = planner.calculate_significance(
            control_conversions=100,
            control_visitors=5000,
            variant_conversions=150,
            variant_visitors=5000,
        )
        assert "control_rate" in result
        assert "variant_rate" in result
        assert result["control_rate"] == 2.0
        assert result["variant_rate"] == 3.0

    def test_singleton_pattern(self):
        """Test get_ab_test_planner returns singleton."""
        p1 = get_ab_test_planner()
        p2 = get_ab_test_planner()
        assert p1 is p2


class TestTestElement:
    """Test TestElement enum."""

    def test_all_elements_defined(self):
        """Test all test elements exist."""
        assert TestElement.HEADLINE.value == "headline"
        assert TestElement.PRIMARY_TEXT.value == "primary_text"
        assert TestElement.CTA.value == "cta"
        assert TestElement.IMAGE.value == "image"
        assert TestElement.AUDIENCE.value == "audience"


class TestTestPriority:
    """Test TestPriority enum."""

    def test_all_priorities_defined(self):
        """Test all priorities exist."""
        assert TestPriority.HIGH.value == "high"
        assert TestPriority.MEDIUM.value == "medium"
        assert TestPriority.LOW.value == "low"
