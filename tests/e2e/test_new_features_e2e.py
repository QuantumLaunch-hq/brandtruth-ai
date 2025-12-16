# tests/e2e/test_new_features_e2e.py
"""End-to-end tests for new features (Slices 16-23).

These tests verify complete user workflows across multiple features.
"""

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


class TestAdCreationWorkflow:
    """E2E test for complete ad creation workflow."""

    @pytest.mark.anyio
    async def test_complete_ad_creation_flow(self, client):
        """Test complete flow from hooks to iteration."""
        # Step 1: Generate hooks
        hooks_response = await client.post("/hooks/generate", json={
            "product_name": "Careerfied",
            "product_description": "AI-powered resume builder for job seekers",
            "target_audience": "Job seekers and career changers",
            "pain_points": ["getting rejected", "ATS systems"],
            "benefits": ["land interviews", "save time"],
            "include_emojis": True,
            "num_hooks": 5,
        })
        assert hooks_response.status_code == 200
        hooks = hooks_response.json()
        best_hook = hooks["best_hook"]["text"]
        
        # Step 2: Get social proof
        social_response = await client.post("/social/collect", json={
            "brand_name": "Careerfied",
            "product_description": "AI-powered resume builder",
            "existing_testimonials": ["Got 3 interviews in first week!"],
            "user_count": 1500,
            "rating": 4.8,
        })
        assert social_response.status_code == 200
        social = social_response.json()
        social_snippet = social["ad_snippets"][0] if social["ad_snippets"] else ""
        
        # Step 3: Analyze with iteration assistant
        iterate_response = await client.post("/iterate/analyze", json={
            "headline": best_hook,
            "primary_text": f"{social_snippet} Build ATS-optimized resumes.",
            "cta": "Get Started Free",
            "current_ctr": 1.0,
            "current_cvr": 2.0,
            "current_cpa": 80,
            "target_cpa": 50,
        })
        assert iterate_response.status_code == 200
        iteration = iterate_response.json()
        
        # Verify we have actionable output
        assert len(iteration["improved_variants"]) > 0 or len(iteration["quick_wins"]) > 0


class TestCampaignPlanningWorkflow:
    """E2E test for campaign planning workflow."""

    @pytest.mark.anyio
    async def test_complete_campaign_planning_flow(self, client):
        """Test complete flow from budget to A/B test planning."""
        # Step 1: Simulate budget
        budget_response = await client.post("/budget/simulate", json={
            "industry": "saas",
            "goal": "leads",
            "product_price": 99.0,
            "target_monthly_conversions": 100,
        })
        assert budget_response.status_code == 200
        budget = budget_response.json()
        monthly_budget = budget["daily_budget"] * 30
        
        # Step 2: Get platform recommendations
        platform_response = await client.post("/platforms/recommend", json={
            "product_type": "b2b_saas",
            "audience_type": "founders",
            "monthly_budget": monthly_budget,
            "product_price": 99,
            "is_visual": True,
        })
        assert platform_response.status_code == 200
        platforms = platform_response.json()
        primary_platform = platforms["primary_platform"]
        
        # Step 3: Get audience targeting
        audience_response = await client.post("/audience/suggest", json={
            "product_name": "TestProduct",
            "product_description": "B2B SaaS product",
            "product_type": "saas",
            "target_persona": "Founders and entrepreneurs",
            "price_point": 99,
        })
        assert audience_response.status_code == 200
        audience = audience_response.json()
        
        # Step 4: Plan A/B tests
        abtest_response = await client.post("/abtest/plan", json={
            "variants": [
                {"headline": "Version A", "cta": "Get Started"},
                {"headline": "Version B", "cta": "Try Free"},
            ],
            "baseline_ctr": 1.0,
            "baseline_cvr": 2.0,
            "daily_budget": budget["daily_budget"],
        })
        assert abtest_response.status_code == 200
        abtest = abtest_response.json()
        
        # Verify coherent plan
        assert primary_platform is not None
        assert len(audience["primary_audiences"]) > 0
        assert abtest["estimated_days"] >= 7
        assert budget["daily_budget"] > 0


class TestLandingPageOptimizationWorkflow:
    """E2E test for landing page optimization workflow."""

    @pytest.mark.anyio
    async def test_landing_page_optimization_flow(self, client):
        """Test flow from landing analysis to iteration."""
        # Step 1: Analyze landing page
        landing_response = await client.post("/landing/analyze", json={
            "landing_page_url": "https://careerfied.ai",
            "ad_headline": "Stop Getting Rejected by ATS",
            "ad_primary_text": "Build ATS-optimized resumes in minutes",
            "ad_cta": "Get Started Free",
        })
        assert landing_response.status_code == 200
        landing = landing_response.json()
        
        # Step 2: If low score, analyze ad for improvements
        if landing["overall_score"] < 80:
            iterate_response = await client.post("/iterate/analyze", json={
                "headline": "Stop Getting Rejected by ATS",
                "primary_text": "Build ATS-optimized resumes in minutes",
                "cta": "Get Started Free",
                "current_ctr": 0.8,
                "current_cvr": 1.5,
                "current_cpa": 100,
                "target_cpa": 50,
            })
            assert iterate_response.status_code == 200
            iteration = iterate_response.json()
            
            # Should have recommendations
            assert len(iteration["improved_variants"]) > 0


class TestDemoWorkflow:
    """E2E test for demo endpoints."""

    @pytest.mark.anyio
    async def test_all_demos_work(self, client):
        """Test all demo endpoints return valid data."""
        demos = [
            "/hooks/demo",
            "/landing/demo",
            "/budget/demo",
            "/platforms/demo",
            "/abtest/demo",
            "/audience/demo",
            "/iterate/demo",
            "/social/demo",
        ]
        
        for demo in demos:
            response = await client.post(demo)
            assert response.status_code == 200, f"Demo {demo} failed"
            data = response.json()
            assert len(data) > 0, f"Demo {demo} returned empty data"


class TestCareeriedScenario:
    """E2E test simulating Careerfied ad campaign setup."""

    @pytest.mark.anyio
    async def test_careerfied_campaign_setup(self, client):
        """Simulate setting up a complete Careerfied campaign."""
        
        # 1. Generate ad hooks
        hooks = await client.post("/hooks/generate", json={
            "product_name": "Careerfied",
            "product_description": "AI-powered career intelligence platform that helps job seekers build ATS-optimized resumes and land more interviews",
            "target_audience": "Job seekers, career changers, recent graduates",
            "pain_points": [
                "Getting rejected by ATS systems",
                "Not hearing back from applications",
                "Don't know what recruiters want",
            ],
            "benefits": [
                "Land more interviews",
                "Beat ATS systems",
                "Get real-time feedback",
            ],
            "tone": "professional",
            "include_emojis": True,
            "num_hooks": 10,
        })
        assert hooks.status_code == 200
        hook_data = hooks.json()
        assert len(hook_data["hooks"]) == 10
        
        # 2. Collect social proof
        social = await client.post("/social/collect", json={
            "brand_name": "Careerfied",
            "brand_url": "https://careerfied.ai",
            "product_description": "AI-powered career intelligence platform",
            "existing_testimonials": [
                "Careerfied helped me land my dream job at Google!",
                "Got 5 interviews in my first week using Careerfied.",
                "Finally understood why my resume was getting rejected.",
            ],
            "user_count": 1500,
            "rating": 4.8,
            "notable_customers": ["Google", "Meta", "Microsoft", "Amazon"],
        })
        assert social.status_code == 200
        social_data = social.json()
        assert social_data["trust_score"] >= 70
        
        # 3. Set budget
        budget = await client.post("/budget/simulate", json={
            "industry": "saas",
            "goal": "leads",
            "product_price": 29.0,
            "target_monthly_conversions": 200,
        })
        assert budget.status_code == 200
        budget_data = budget.json()
        
        # 4. Choose platforms
        platforms = await client.post("/platforms/recommend", json={
            "product_type": "b2c_saas",
            "audience_type": "job_seekers",
            "monthly_budget": budget_data["daily_budget"] * 30,
            "product_price": 29,
            "is_visual": True,
        })
        assert platforms.status_code == 200
        
        # 5. Set up audience targeting
        audience = await client.post("/audience/suggest", json={
            "product_name": "Careerfied",
            "product_description": "AI resume builder and career platform",
            "product_type": "saas",
            "target_persona": "Job seekers looking for new opportunities",
            "price_point": 29,
            "existing_customers": True,
            "website_traffic": True,
        })
        assert audience.status_code == 200
        audience_data = audience.json()
        assert len(audience_data["primary_audiences"]) > 0
        
        # 6. Plan A/B tests
        best_hooks = sorted(hook_data["hooks"], key=lambda x: x["score"], reverse=True)[:2]
        abtest = await client.post("/abtest/plan", json={
            "variants": [
                {"headline": best_hooks[0]["text"], "cta": "Get Started Free"},
                {"headline": best_hooks[1]["text"], "cta": "Try Careerfied Free"},
            ],
            "baseline_ctr": 1.0,
            "baseline_cvr": 2.5,
            "daily_budget": budget_data["daily_budget"],
            "confidence_level": 0.95,
            "minimum_lift": 0.15,
        })
        assert abtest.status_code == 200
        abtest_data = abtest.json()
        
        # 7. Analyze landing page
        landing = await client.post("/landing/analyze", json={
            "landing_page_url": "https://careerfied.ai",
            "ad_headline": best_hooks[0]["text"],
            "ad_primary_text": f"{social_data['ad_snippets'][0]} Build ATS-optimized resumes.",
            "ad_cta": "Get Started Free",
        })
        assert landing.status_code == 200
        
        # Final verification - we have a complete campaign plan
        assert budget_data["daily_budget"] > 0
        assert len(audience_data["primary_audiences"]) >= 3
        assert abtest_data["estimated_days"] >= 7
        assert len(social_data["ad_snippets"]) > 0


class TestIterativeOptimization:
    """E2E test for iterative ad optimization."""

    @pytest.mark.anyio
    async def test_optimization_cycle(self, client):
        """Test a complete optimization cycle."""
        
        # Initial ad (poor performance)
        initial_analysis = await client.post("/iterate/analyze", json={
            "headline": "Check out our product",
            "primary_text": "We have a great product you should try.",
            "cta": "Learn More",
            "current_ctr": 0.4,
            "current_cvr": 0.8,
            "current_cpa": 150,
            "target_cpa": 50,
            "impressions": 10000,
            "frequency": 3.0,
            "days_running": 14,
        })
        assert initial_analysis.status_code == 200
        initial = initial_analysis.json()
        
        # Should have multiple issues
        assert len(initial["diagnoses"]) >= 2
        
        # Get improved variant
        improved_headline = initial["improved_variants"][0]["improved"] if initial["improved_variants"] else "Stop Wasting Time"
        
        # Re-analyze with improved copy
        improved_analysis = await client.post("/iterate/analyze", json={
            "headline": improved_headline,
            "primary_text": "Join 1,500+ users who achieved results.",
            "cta": "Get Started Free",
            "current_ctr": 1.2,  # Better
            "current_cvr": 2.0,  # Better
            "current_cpa": 80,   # Better
            "target_cpa": 50,
            "impressions": 10000,
            "frequency": 1.8,
            "days_running": 7,
        })
        assert improved_analysis.status_code == 200
        improved = improved_analysis.json()
        
        # Should have fewer critical issues
        initial_critical = len([d for d in initial["diagnoses"] if d["severity"] == "critical"])
        improved_critical = len([d for d in improved["diagnoses"] if d["severity"] == "critical"])
        assert improved_critical <= initial_critical
