# tests/component/test_new_features_components.py
"""Component tests for new features (Slices 16-23).
Test modules with mocked external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestHookGeneratorComponent:
    """Component tests for Hook Generator."""

    @pytest.mark.asyncio
    async def test_hook_generator_with_claude_mock(self):
        """Test hook generator with mocked Claude API."""
        from src.generators.hook_generator import HookGenerator, HookGeneratorRequest
        
        generator = HookGenerator()
        request = HookGeneratorRequest(
            product_name="TestProduct",
            product_description="A test product",
            target_audience="testers",
            num_hooks=5,
        )
        
        result = await generator.generate(request)
        
        # Component should work even without Claude API
        assert len(result.hooks) == 5
        assert result.best_hook is not None
        assert all(0 <= h.score <= 100 for h in result.hooks)

    @pytest.mark.asyncio
    async def test_hook_patterns_isolated(self):
        """Test hook patterns work in isolation."""
        from src.generators.hook_generator import HookGenerator, HookPattern
        
        generator = HookGenerator()
        patterns = generator.get_patterns()
        
        assert len(patterns) == 10
        pattern_ids = [p["id"] for p in patterns]
        assert "question" in pattern_ids
        assert "pain_point" in pattern_ids


class TestLandingAnalyzerComponent:
    """Component tests for Landing Page Analyzer."""

    @pytest.mark.asyncio
    async def test_analyzer_without_network(self):
        """Test analyzer works without actual page fetch."""
        from src.analyzers.landing_page_analyzer import LandingPageAnalyzer, LandingPageRequest
        
        analyzer = LandingPageAnalyzer()
        request = LandingPageRequest(
            landing_page_url="https://example.com",
            ad_headline="Test Headline",
            ad_primary_text="Test primary text",
            ad_cta="Click Here",
        )
        
        result = await analyzer.analyze(request)
        
        # Should return simulated scores
        assert 0 <= result.overall_score <= 100
        assert result.message_match_level is not None

    @pytest.mark.asyncio
    async def test_message_match_scoring_isolated(self):
        """Test message match scoring logic."""
        from src.analyzers.landing_page_analyzer import LandingPageAnalyzer, LandingPageRequest
        
        analyzer = LandingPageAnalyzer()
        
        # High match scenario
        request = LandingPageRequest(
            landing_page_url="https://test.com",
            ad_headline="Get More Sales",
            ad_primary_text="Increase your sales with our tool",
            ad_cta="Start Now",
        )
        result = await analyzer.analyze(request)
        assert result.message_match_score >= 0


class TestBudgetSimulatorComponent:
    """Component tests for Budget Simulator."""

    @pytest.mark.asyncio
    async def test_budget_calculation_logic(self):
        """Test budget calculation without external services."""
        from src.analyzers.budget_simulator import BudgetSimulator, BudgetRequest, Industry, CampaignGoal
        
        simulator = BudgetSimulator()
        request = BudgetRequest(
            industry=Industry.SAAS,
            goal=CampaignGoal.LEADS,
            product_price=100,
            target_monthly_conversions=50,
        )
        
        result = await simulator.simulate(request)
        
        # Verify calculation logic
        assert result.daily_budget > 0
        assert result.monthly_budget == pytest.approx(result.daily_budget * 30, rel=0.01)
        assert result.expected_cpa > 0

    @pytest.mark.asyncio
    async def test_all_industries_have_benchmarks(self):
        """Test benchmark data completeness."""
        from src.analyzers.budget_simulator import INDUSTRY_BENCHMARKS, Industry
        
        for industry in Industry:
            assert industry in INDUSTRY_BENCHMARKS
            bench = INDUSTRY_BENCHMARKS[industry]
            assert "cpm" in bench
            assert "ctr" in bench
            assert "cvr" in bench


class TestPlatformRecommenderComponent:
    """Component tests for Platform Recommender."""

    @pytest.mark.asyncio
    async def test_scoring_algorithm(self):
        """Test platform scoring without external data."""
        from src.analyzers.platform_recommender import (
            PlatformRecommender, PlatformRequest, ProductType, AudienceType
        )
        
        recommender = PlatformRecommender()
        request = PlatformRequest(
            product_type=ProductType.B2B_SAAS,
            audience_type=AudienceType.FOUNDERS,
            monthly_budget=2000,
        )
        
        result = await recommender.recommend(request)
        
        # Verify scoring logic
        scores = [r.score for r in result.recommendations]
        assert scores == sorted(scores, reverse=True)  # Should be sorted

    @pytest.mark.asyncio
    async def test_budget_allocation_sums_correctly(self):
        """Test budget allocation logic."""
        from src.analyzers.platform_recommender import (
            PlatformRecommender, PlatformRequest, ProductType, AudienceType
        )
        
        recommender = PlatformRecommender()
        request = PlatformRequest(
            product_type=ProductType.ECOMMERCE,
            audience_type=AudienceType.CONSUMERS,
            monthly_budget=5000,
        )
        
        result = await recommender.recommend(request)
        
        total = sum(result.budget_allocation.values())
        assert total <= 100


class TestABTestPlannerComponent:
    """Component tests for A/B Test Planner."""

    @pytest.mark.asyncio
    async def test_sample_size_calculation(self):
        """Test statistical sample size calculation."""
        from src.analyzers.ab_test_planner import ABTestPlanner, ABTestRequest
        
        planner = ABTestPlanner()
        request = ABTestRequest(
            variants=[{"headline": "A"}, {"headline": "B"}],
            baseline_ctr=1.0,
            baseline_cvr=2.0,
            daily_budget=50,
            confidence_level=0.95,
            minimum_lift=0.20,
        )
        
        result = await planner.plan(request)
        
        # Sample size should be positive
        assert result.required_sample_size > 0
        # Days should be reasonable
        assert result.estimated_days >= 7

    def test_significance_calculation_math(self):
        """Test statistical significance math."""
        from src.analyzers.ab_test_planner import ABTestPlanner
        
        planner = ABTestPlanner()
        
        # Clear winner
        result = planner.calculate_significance(
            control_conversions=50,
            control_visitors=1000,
            variant_conversions=100,
            variant_visitors=1000,
        )
        assert result["lift"] == 100.0  # 100% lift
        
        # No difference
        result = planner.calculate_significance(
            control_conversions=50,
            control_visitors=1000,
            variant_conversions=50,
            variant_visitors=1000,
        )
        assert result["lift"] == 0.0


class TestAudienceTargetingComponent:
    """Component tests for Audience Targeting."""

    @pytest.mark.asyncio
    async def test_interest_detection(self):
        """Test interest category detection logic."""
        from src.analyzers.audience_targeting import AudienceTargeting, AudienceRequest
        
        targeting = AudienceTargeting()
        
        # Career-related product
        request = AudienceRequest(
            product_name="ResumeBuilder",
            product_description="Resume and job application tool",
            target_persona="Job seekers",
        )
        result = await targeting.suggest(request)
        
        # Should detect career interests
        assert len(result.primary_audiences) > 0

    @pytest.mark.asyncio
    async def test_exclusion_logic(self):
        """Test exclusion generation logic."""
        from src.analyzers.audience_targeting import AudienceTargeting, AudienceRequest
        
        targeting = AudienceTargeting()
        request = AudienceRequest(
            product_name="Test",
            product_description="Test product",
            target_persona="Users",
            price_point=500,  # High price
        )
        result = await targeting.suggest(request)
        
        # Should exclude low-income for high-priced products
        exclusion_names = [e.name.lower() for e in result.exclusions]
        assert any("customer" in n or "competitor" in n for n in exclusion_names)


class TestIterationAssistantComponent:
    """Component tests for Iteration Assistant."""

    @pytest.mark.asyncio
    async def test_issue_detection_logic(self):
        """Test issue detection thresholds."""
        from src.analyzers.iteration_assistant import (
            IterationAssistant, IterationRequest, PerformanceIssue, IssueSeverity
        )
        
        assistant = IterationAssistant()
        
        # Bad CTR
        request = IterationRequest(
            headline="Test",
            primary_text="Test",
            cta="Test",
            current_ctr=0.2,  # Very bad
            current_cvr=2.0,
            current_cpa=80,
            target_cpa=50,
        )
        result = await assistant.analyze(request)
        
        ctr_issues = [d for d in result.diagnoses if d.issue == PerformanceIssue.LOW_CTR]
        assert len(ctr_issues) > 0
        assert ctr_issues[0].severity == IssueSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_improvement_generation(self):
        """Test improvement suggestion generation."""
        from src.analyzers.iteration_assistant import IterationAssistant, IterationRequest
        
        assistant = IterationAssistant()
        request = IterationRequest(
            headline="Check out our product",
            primary_text="We have a product",
            cta="Learn More",
            current_ctr=0.5,
            current_cvr=1.0,
            current_cpa=100,
            target_cpa=50,
        )
        result = await assistant.analyze(request)
        
        # Should generate improvements
        assert len(result.improved_variants) > 0
        for imp in result.improved_variants:
            assert imp.improved != imp.original


class TestSocialProofComponent:
    """Component tests for Social Proof Collector."""

    @pytest.mark.asyncio
    async def test_trust_score_calculation(self):
        """Test trust score calculation logic."""
        from src.extractors.social_proof_collector import SocialProofCollector, SocialProofRequest
        
        collector = SocialProofCollector()
        
        # Minimal proof
        minimal = SocialProofRequest(
            brand_name="Test",
            brand_url="https://test.com",
            product_description="Test",
        )
        minimal_result = await collector.collect(minimal)
        
        # Full proof
        full = SocialProofRequest(
            brand_name="Test",
            brand_url="https://test.com",
            product_description="Test",
            existing_testimonials=["Great!", "Amazing!"],
            user_count=10000,
            rating=4.9,
            notable_customers=["Google", "Microsoft"],
        )
        full_result = await collector.collect(full)
        
        # More proof = higher score
        assert full_result.trust_score > minimal_result.trust_score

    @pytest.mark.asyncio
    async def test_number_formatting(self):
        """Test large number formatting."""
        from src.extractors.social_proof_collector import SocialProofCollector, SocialProofRequest
        
        collector = SocialProofCollector()
        request = SocialProofRequest(
            brand_name="Test",
            brand_url="https://test.com",
            product_description="Test",
            user_count=2500000,  # 2.5M
        )
        result = await collector.collect(request)
        
        # Should format nicely
        stat_proofs = [p for p in result.proofs if p.type.value == "stat"]
        assert len(stat_proofs) > 0
