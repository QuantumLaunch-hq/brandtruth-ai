# tests/integration/test_new_features_integration.py
"""Integration tests for new features (Slices 16-23)."""

import pytest
from httpx import AsyncClient, ASGITransport
from api_server import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHookGeneratorIntegration:
    """Integration tests for Hook Generator API."""

    @pytest.mark.anyio
    async def test_generate_hooks_full_request(self, client):
        """Test full hook generation request."""
        response = await client.post("/hooks/generate", json={
            "product_name": "Careerfied",
            "product_description": "AI-powered resume builder for job seekers",
            "target_audience": "Job seekers and career changers",
            "pain_points": ["getting rejected", "ATS systems", "writer's block"],
            "benefits": ["land interviews", "save time", "professional results"],
            "tone": "professional",
            "include_emojis": True,
            "num_hooks": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["hooks"]) == 10
        assert data["best_hook"] is not None
        assert data["avg_score"] > 0

    @pytest.mark.anyio
    async def test_generate_hooks_minimal_request(self, client):
        """Test minimal hook generation request."""
        response = await client.post("/hooks/generate", json={
            "product_name": "Test Product",
            "product_description": "A test product",
            "target_audience": "Users",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["hooks"]) >= 5

    @pytest.mark.anyio
    async def test_get_patterns(self, client):
        """Test getting hook patterns."""
        response = await client.get("/hooks/patterns")
        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) == 10
        assert len(data["power_words"]) >= 7

    @pytest.mark.anyio
    async def test_hooks_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/hooks/demo")
        assert response.status_code == 200
        data = response.json()
        assert "hooks" in data
        assert "summary" in data


class TestLandingPageAnalyzerIntegration:
    """Integration tests for Landing Page Analyzer API."""

    @pytest.mark.anyio
    async def test_analyze_landing_page(self, client):
        """Test landing page analysis."""
        response = await client.post("/landing/analyze", json={
            "landing_page_url": "https://careerfied.ai",
            "ad_headline": "Stop Getting Rejected by ATS",
            "ad_primary_text": "Build ATS-optimized resumes in minutes",
            "ad_cta": "Get Started Free",
        })
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["overall_score"] <= 100
        assert data["message_match_level"] in ["excellent", "good", "fair", "poor", "mismatch"]
        assert "recommendations" in data

    @pytest.mark.anyio
    async def test_landing_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/landing/demo")
        assert response.status_code == 200
        data = response.json()
        assert "score" in data or "overall_score" in data


class TestBudgetSimulatorIntegration:
    """Integration tests for Budget Simulator API."""

    @pytest.mark.anyio
    async def test_simulate_budget(self, client):
        """Test budget simulation."""
        response = await client.post("/budget/simulate", json={
            "industry": "saas",
            "goal": "leads",
            "product_price": 99.0,
            "target_monthly_conversions": 50,
            "target_cpa": None,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["daily_budget"] > 0
        assert data["expected_conversions"] >= 0
        assert data["tier"] in ["starter", "growth", "scale", "enterprise"]

    @pytest.mark.anyio
    async def test_simulate_with_target_cpa(self, client):
        """Test budget simulation with target CPA."""
        response = await client.post("/budget/simulate", json={
            "industry": "ecommerce",
            "goal": "sales",
            "product_price": 50.0,
            "target_monthly_conversions": 100,
            "target_cpa": 25.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["daily_budget"] > 0

    @pytest.mark.anyio
    async def test_get_benchmarks(self, client):
        """Test getting industry benchmarks."""
        response = await client.get("/budget/benchmarks")
        assert response.status_code == 200
        data = response.json()
        assert "saas" in data
        assert "ecommerce" in data

    @pytest.mark.anyio
    async def test_budget_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/budget/demo")
        assert response.status_code == 200
        data = response.json()
        assert "daily_budget" in data


class TestPlatformRecommenderIntegration:
    """Integration tests for Platform Recommender API."""

    @pytest.mark.anyio
    async def test_recommend_platforms(self, client):
        """Test platform recommendation."""
        response = await client.post("/platforms/recommend", json={
            "product_type": "b2b_saas",
            "audience_type": "founders",
            "monthly_budget": 1000,
            "product_price": 99,
            "is_visual": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["primary_platform"] is not None
        assert len(data["recommendations"]) >= 5
        assert len(data["budget_allocation"]) > 0

    @pytest.mark.anyio
    async def test_get_platforms_list(self, client):
        """Test getting platforms list."""
        response = await client.get("/platforms/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 7

    @pytest.mark.anyio
    async def test_platforms_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/platforms/demo")
        assert response.status_code == 200
        data = response.json()
        assert "primary_platform" in data


class TestABTestPlannerIntegration:
    """Integration tests for A/B Test Planner API."""

    @pytest.mark.anyio
    async def test_plan_ab_test(self, client):
        """Test A/B test planning."""
        response = await client.post("/abtest/plan", json={
            "variants": [
                {"headline": "Stop Getting Rejected", "primary_text": "Build resumes", "cta": "Get Started"},
                {"headline": "Land More Interviews", "primary_text": "AI resumes", "cta": "Try Free"},
            ],
            "baseline_ctr": 1.0,
            "baseline_cvr": 2.0,
            "daily_budget": 50,
            "confidence_level": 0.95,
            "minimum_lift": 0.20,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["required_sample_size"] > 0
        assert data["estimated_days"] >= 7
        assert len(data["test_pairs"]) > 0
        assert len(data["testing_sequence"]) > 0

    @pytest.mark.anyio
    async def test_calculate_significance(self, client):
        """Test significance calculation."""
        response = await client.post("/abtest/calculate", json={
            "control_conversions": 100,
            "control_visitors": 5000,
            "variant_conversions": 150,
            "variant_visitors": 5000,
        })
        assert response.status_code == 200
        data = response.json()
        assert "is_significant" in data
        assert "lift" in data
        assert "control_rate" in data
        assert "variant_rate" in data

    @pytest.mark.anyio
    async def test_abtest_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/abtest/demo")
        assert response.status_code == 200
        data = response.json()
        assert "estimated_days" in data


class TestAudienceTargetingIntegration:
    """Integration tests for Audience Targeting API."""

    @pytest.mark.anyio
    async def test_suggest_audiences(self, client):
        """Test audience suggestion."""
        response = await client.post("/audience/suggest", json={
            "product_name": "Careerfied",
            "product_description": "AI-powered resume builder",
            "product_type": "saas",
            "target_persona": "Job seekers",
            "price_point": 29,
            "existing_customers": False,
            "website_traffic": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["primary_audiences"]) > 0
        assert len(data["exclusions"]) > 0
        assert len(data["testing_order"]) > 0

    @pytest.mark.anyio
    async def test_suggest_with_customer_data(self, client):
        """Test audience suggestion with customer data."""
        response = await client.post("/audience/suggest", json={
            "product_name": "Test",
            "product_description": "Test product",
            "target_persona": "Users",
            "existing_customers": True,
            "website_traffic": True,
        })
        assert response.status_code == 200
        data = response.json()
        # Should have lookalike/retargeting audiences
        audience_types = [a["type"] for a in data["primary_audiences"]]
        assert "lookalike" in audience_types or "retargeting" in audience_types

    @pytest.mark.anyio
    async def test_audience_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/audience/demo")
        assert response.status_code == 200
        data = response.json()
        assert "primary_audiences" in data


class TestIterationAssistantIntegration:
    """Integration tests for Iteration Assistant API."""

    @pytest.mark.anyio
    async def test_analyze_underperforming_ad(self, client):
        """Test analyzing underperforming ad."""
        response = await client.post("/iterate/analyze", json={
            "headline": "Check out our product",
            "primary_text": "We have a great product.",
            "cta": "Learn More",
            "current_ctr": 0.5,
            "current_cvr": 1.0,
            "current_cpa": 120,
            "target_cpa": 50,
            "impressions": 10000,
            "frequency": 2.0,
            "days_running": 7,
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["diagnoses"]) > 0
        assert len(data["improved_variants"]) > 0
        assert len(data["priority_fixes"]) > 0
        assert data["estimated_improvement"] is not None

    @pytest.mark.anyio
    async def test_analyze_good_performing_ad(self, client):
        """Test analyzing well-performing ad."""
        response = await client.post("/iterate/analyze", json={
            "headline": "Stop Getting Rejected",
            "primary_text": "Build ATS-optimized resumes",
            "cta": "Get Started Free",
            "current_ctr": 2.5,
            "current_cvr": 4.0,
            "current_cpa": 30,
            "target_cpa": 50,
            "impressions": 10000,
            "frequency": 1.5,
            "days_running": 7,
        })
        assert response.status_code == 200
        data = response.json()
        # Should have fewer critical issues
        critical_issues = [d for d in data["diagnoses"] if d["severity"] == "critical"]
        assert len(critical_issues) == 0

    @pytest.mark.anyio
    async def test_iterate_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/iterate/demo")
        assert response.status_code == 200
        data = response.json()
        assert "diagnoses" in data


class TestSocialProofCollectorIntegration:
    """Integration tests for Social Proof Collector API."""

    @pytest.mark.anyio
    async def test_collect_social_proof(self, client):
        """Test social proof collection."""
        response = await client.post("/social/collect", json={
            "brand_name": "Careerfied",
            "brand_url": "https://careerfied.ai",
            "product_description": "AI-powered resume builder",
            "existing_testimonials": [
                "This helped me land my dream job!",
                "Got 3 interviews in the first week",
            ],
            "user_count": 1500,
            "rating": 4.8,
            "notable_customers": ["Google", "Meta", "Microsoft"],
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["proofs"]) > 0
        assert 0 <= data["trust_score"] <= 100
        assert len(data["ad_snippets"]) > 0

    @pytest.mark.anyio
    async def test_collect_minimal(self, client):
        """Test collection with minimal data."""
        response = await client.post("/social/collect", json={
            "brand_name": "Test",
            "product_description": "Test product",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["trust_score"] < 50  # Low score with minimal data

    @pytest.mark.anyio
    async def test_social_demo(self, client):
        """Test demo endpoint."""
        response = await client.post("/social/demo")
        assert response.status_code == 200
        data = response.json()
        assert "trust_score" in data or "snippets" in data


class TestCrossFeatureIntegration:
    """Test integration between multiple features."""

    @pytest.mark.anyio
    async def test_hooks_to_iteration_flow(self, client):
        """Test flow from hook generation to iteration analysis."""
        # Generate hooks
        hook_response = await client.post("/hooks/generate", json={
            "product_name": "TestProduct",
            "product_description": "Test description",
            "target_audience": "Users",
            "num_hooks": 3,
        })
        assert hook_response.status_code == 200
        hooks = hook_response.json()["hooks"]
        
        # Use hook in iteration analysis
        iterate_response = await client.post("/iterate/analyze", json={
            "headline": hooks[0]["text"],
            "primary_text": "Test primary text",
            "cta": "Try Now",
            "current_ctr": 1.0,
            "current_cvr": 2.0,
            "current_cpa": 80,
            "target_cpa": 50,
        })
        assert iterate_response.status_code == 200

    @pytest.mark.anyio
    async def test_budget_to_platform_flow(self, client):
        """Test flow from budget simulation to platform recommendation."""
        # Get budget simulation
        budget_response = await client.post("/budget/simulate", json={
            "industry": "saas",
            "goal": "leads",
            "product_price": 99.0,
            "target_monthly_conversions": 50,
        })
        assert budget_response.status_code == 200
        budget = budget_response.json()
        
        # Use budget in platform recommendation
        platform_response = await client.post("/platforms/recommend", json={
            "product_type": "b2b_saas",
            "audience_type": "founders",
            "monthly_budget": budget["daily_budget"] * 30,
            "product_price": 99,
        })
        assert platform_response.status_code == 200

    @pytest.mark.anyio
    async def test_audience_to_abtest_flow(self, client):
        """Test flow from audience targeting to A/B test planning."""
        # Get audience suggestions
        audience_response = await client.post("/audience/suggest", json={
            "product_name": "Test",
            "product_description": "Test product",
            "target_persona": "Users",
        })
        assert audience_response.status_code == 200
        
        # Plan A/B test with audience variants
        abtest_response = await client.post("/abtest/plan", json={
            "variants": [
                {"headline": "Version A", "audience": "Interest targeting"},
                {"headline": "Version A", "audience": "Lookalike"},
            ],
            "daily_budget": 50,
        })
        assert abtest_response.status_code == 200
