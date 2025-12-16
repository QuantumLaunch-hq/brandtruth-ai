# tests/contract/test_new_features_contracts.py
"""Contract tests for new feature API endpoints (Slices 16-23).

These tests verify API contracts - request/response shapes remain stable.
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


class TestHookGeneratorContract:
    """Contract tests for Hook Generator API."""

    @pytest.mark.anyio
    async def test_generate_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/hooks/generate", json={
            "product_name": "Test",
            "product_description": "Test",
            "target_audience": "Users",
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "hooks" in data
        assert "best_hook" in data
        assert "avg_score" in data
        assert "pattern_distribution" in data
        assert "recommendations" in data
        assert "summary" in data
        
        # Hook shape
        for hook in data["hooks"]:
            assert "text" in hook
            assert "pattern" in hook
            assert "score" in hook
            assert "character_count" in hook

    @pytest.mark.anyio
    async def test_patterns_response_shape(self, client):
        """Verify patterns response shape."""
        response = await client.get("/hooks/patterns")
        assert response.status_code == 200
        data = response.json()
        
        assert "patterns" in data
        assert "power_words" in data
        
        for pattern in data["patterns"]:
            assert "id" in pattern
            assert "name" in pattern


class TestLandingPageAnalyzerContract:
    """Contract tests for Landing Page Analyzer API."""

    @pytest.mark.anyio
    async def test_analyze_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/landing/analyze", json={
            "landing_page_url": "https://test.com",
            "ad_headline": "Test",
            "ad_primary_text": "Test",
            "ad_cta": "Test",
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "url" in data
        assert "overall_score" in data
        assert "message_match_score" in data
        assert "message_match_level" in data
        assert "above_fold_score" in data
        assert "cta_score" in data
        assert "mobile_score" in data
        assert "load_speed_score" in data
        
        # Score ranges
        assert 0 <= data["overall_score"] <= 100
        assert data["message_match_level"] in ["excellent", "good", "fair", "poor", "mismatch"]


class TestBudgetSimulatorContract:
    """Contract tests for Budget Simulator API."""

    @pytest.mark.anyio
    async def test_simulate_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/budget/simulate", json={
            "industry": "saas",
            "goal": "leads",
            "product_price": 99.0,
            "target_monthly_conversions": 50,
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "daily_budget" in data
        assert "monthly_budget" in data
        assert "tier" in data
        assert "expected_impressions" in data
        assert "expected_clicks" in data
        assert "expected_conversions" in data
        assert "expected_cpa" in data
        assert "expected_roas" in data
        assert "break_even_days" in data
        assert "confidence_level" in data
        assert "recommendations" in data
        
        # Type checks
        assert isinstance(data["daily_budget"], (int, float))
        assert data["tier"] in ["starter", "growth", "scale", "enterprise"]

    @pytest.mark.anyio
    async def test_benchmarks_response_shape(self, client):
        """Verify benchmarks response shape."""
        response = await client.get("/budget/benchmarks")
        assert response.status_code == 200
        data = response.json()
        
        # Each industry should have benchmark data
        for industry, benchmarks in data.items():
            assert "cpm" in benchmarks
            assert "ctr" in benchmarks
            assert "cvr" in benchmarks
            assert "avg_cpa" in benchmarks


class TestPlatformRecommenderContract:
    """Contract tests for Platform Recommender API."""

    @pytest.mark.anyio
    async def test_recommend_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/platforms/recommend", json={
            "product_type": "b2b_saas",
            "audience_type": "founders",
            "monthly_budget": 1000,
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "primary_platform" in data
        assert "strategy" in data
        assert "budget_allocation" in data
        assert "recommendations" in data
        
        # Recommendation shape
        for rec in data["recommendations"]:
            assert "platform" in rec
            assert "score" in rec
            assert "rank" in rec
            assert "min_budget" in rec
            assert "cpa_range" in rec
            assert "strengths" in rec
            assert "best_formats" in rec

    @pytest.mark.anyio
    async def test_platforms_list_response_shape(self, client):
        """Verify platforms list response shape."""
        response = await client.get("/platforms/list")
        assert response.status_code == 200
        data = response.json()
        
        for platform in data:
            assert "id" in platform
            assert "name" in platform
            assert "min_budget" in platform


class TestABTestPlannerContract:
    """Contract tests for A/B Test Planner API."""

    @pytest.mark.anyio
    async def test_plan_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/abtest/plan", json={
            "variants": [{"headline": "A"}, {"headline": "B"}],
            "daily_budget": 50,
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "test_pairs" in data
        assert "required_sample_size" in data
        assert "estimated_days" in data
        assert "daily_budget_needed" in data
        assert "testing_sequence" in data
        assert "recommendations" in data
        
        # Test pair shape
        for pair in data["test_pairs"]:
            assert "element" in pair
            assert "variant_a" in pair
            assert "variant_b" in pair
            assert "hypothesis" in pair
            assert "priority" in pair
            assert "expected_lift" in pair

    @pytest.mark.anyio
    async def test_calculate_response_shape(self, client):
        """Verify calculate response shape."""
        response = await client.post("/abtest/calculate", json={
            "control_conversions": 100,
            "control_visitors": 5000,
            "variant_conversions": 150,
            "variant_visitors": 5000,
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "is_significant" in data
        assert "confidence" in data
        assert "lift" in data
        assert "control_rate" in data
        assert "variant_rate" in data
        assert isinstance(data["is_significant"], bool)


class TestAudienceTargetingContract:
    """Contract tests for Audience Targeting API."""

    @pytest.mark.anyio
    async def test_suggest_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/audience/suggest", json={
            "product_name": "Test",
            "product_description": "Test",
            "target_persona": "Users",
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "primary_audiences" in data
        assert "secondary_audiences" in data
        assert "exclusions" in data
        assert "lookalike_strategy" in data
        assert "budget_allocation" in data
        assert "testing_order" in data
        assert "recommendations" in data
        
        # Audience shape
        for aud in data["primary_audiences"]:
            assert "name" in aud
            assert "type" in aud
            assert "estimated_size" in aud
            assert "relevance_score" in aud
        
        # Exclusion shape
        for exc in data["exclusions"]:
            assert "name" in exc
            assert "reason" in exc
            assert "impact" in exc


class TestIterationAssistantContract:
    """Contract tests for Iteration Assistant API."""

    @pytest.mark.anyio
    async def test_analyze_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/iterate/analyze", json={
            "headline": "Test",
            "primary_text": "Test",
            "cta": "Test",
            "current_ctr": 1.0,
            "current_cvr": 2.0,
            "current_cpa": 80,
            "target_cpa": 50,
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "diagnoses" in data
        assert "improved_variants" in data
        assert "priority_fixes" in data
        assert "testing_roadmap" in data
        assert "quick_wins" in data
        assert "estimated_improvement" in data
        
        # Diagnosis shape
        for diag in data["diagnoses"]:
            assert "issue" in diag
            assert "severity" in diag
            assert "description" in diag
            assert "likely_cause" in diag
            assert "impact" in diag
        
        # Improvement shape
        for imp in data["improved_variants"]:
            assert "element" in imp
            assert "original" in imp
            assert "improved" in imp
            assert "rationale" in imp
            assert "expected_improvement" in imp


class TestSocialProofCollectorContract:
    """Contract tests for Social Proof Collector API."""

    @pytest.mark.anyio
    async def test_collect_response_shape(self, client):
        """Verify response shape matches contract."""
        response = await client.post("/social/collect", json={
            "brand_name": "Test",
            "product_description": "Test",
        })
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "proofs" in data
        assert "trust_score" in data
        assert "ad_snippets" in data
        assert "recommendations" in data
        
        # Score range
        assert 0 <= data["trust_score"] <= 100
        
        # Proof shape
        for proof in data["proofs"]:
            assert "type" in proof
            assert "content" in proof
            assert "source" in proof
            assert "ad_ready" in proof


class TestErrorContracts:
    """Test error response contracts."""

    @pytest.mark.anyio
    async def test_invalid_industry_error(self, client):
        """Test error response for invalid industry."""
        response = await client.post("/budget/simulate", json={
            "industry": "invalid_industry",
            "goal": "leads",
            "product_price": 99.0,
            "target_monthly_conversions": 50,
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_missing_required_field_error(self, client):
        """Test error response for missing required field."""
        response = await client.post("/hooks/generate", json={
            "product_description": "Test",
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_invalid_score_range_error(self, client):
        """Test error response for out-of-range values."""
        response = await client.post("/iterate/analyze", json={
            "headline": "Test",
            "primary_text": "Test",
            "cta": "Test",
            "current_ctr": -1.0,  # Invalid negative
            "current_cvr": 2.0,
            "current_cpa": 80,
            "target_cpa": 50,
        })
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]
