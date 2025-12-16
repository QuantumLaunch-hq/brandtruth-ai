# tests/integration/test_abtest_api.py
"""Integration tests for A/B Test Planner API (Slice 20)."""

import pytest
from httpx import AsyncClient
from api_server import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestABTestAPI:
    """Integration tests for /abtest endpoints."""

    @pytest.mark.anyio
    async def test_plan_ab_test(self, client):
        """Test POST /abtest/plan endpoint."""
        response = await client.post(
            "/abtest/plan",
            json={
                "variants": [
                    {"headline": "Stop Getting Rejected", "primary_text": "Build resumes", "cta": "Get Started"},
                    {"headline": "Land More Interviews", "primary_text": "AI-powered", "cta": "Try Free"},
                ],
                "baseline_ctr": 1.0,
                "baseline_cvr": 2.0,
                "daily_budget": 50,
                "confidence_level": 0.95,
                "minimum_lift": 0.20,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "test_pairs" in data
        assert "required_sample_size" in data
        assert "estimated_days" in data
        assert "testing_sequence" in data

    @pytest.mark.anyio
    async def test_plan_returns_test_pairs(self, client):
        """Test plan returns properly structured test pairs."""
        response = await client.post(
            "/abtest/plan",
            json={
                "variants": [
                    {"headline": "A", "cta": "Click"},
                    {"headline": "B", "cta": "Go"},
                ],
                "daily_budget": 100,
            },
        )
        assert response.status_code == 200
        data = response.json()
        for pair in data["test_pairs"]:
            assert "element" in pair
            assert "variant_a" in pair
            assert "variant_b" in pair
            assert "priority" in pair

    @pytest.mark.anyio
    async def test_calculate_significance(self, client):
        """Test POST /abtest/calculate endpoint."""
        response = await client.post(
            "/abtest/calculate",
            json={
                "control_conversions": 100,
                "control_visitors": 5000,
                "variant_conversions": 150,
                "variant_visitors": 5000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_significant" in data
        assert "control_rate" in data
        assert "variant_rate" in data
        assert "lift" in data

    @pytest.mark.anyio
    async def test_calculate_not_significant(self, client):
        """Test calculation returns not significant for small differences."""
        response = await client.post(
            "/abtest/calculate",
            json={
                "control_conversions": 100,
                "control_visitors": 5000,
                "variant_conversions": 102,
                "variant_visitors": 5000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_significant"] == False

    @pytest.mark.anyio
    async def test_abtest_demo(self, client):
        """Test POST /abtest/demo endpoint."""
        response = await client.post("/abtest/demo")
        assert response.status_code == 200
        data = response.json()
        assert "estimated_days" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_higher_budget_fewer_days(self, client):
        """Test higher budget reduces estimated days."""
        low_budget = await client.post(
            "/abtest/plan",
            json={
                "variants": [{"headline": "A"}, {"headline": "B"}],
                "daily_budget": 20,
            },
        )
        high_budget = await client.post(
            "/abtest/plan",
            json={
                "variants": [{"headline": "A"}, {"headline": "B"}],
                "daily_budget": 200,
            },
        )
        assert low_budget.status_code == 200
        assert high_budget.status_code == 200
        assert high_budget.json()["estimated_days"] <= low_budget.json()["estimated_days"]
