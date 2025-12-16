# tests/integration/test_budget_api.py
"""Integration tests for Budget Simulator API (Slice 18)."""

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


class TestBudgetAPI:
    """Integration tests for /budget endpoints."""

    @pytest.mark.anyio
    async def test_simulate_budget(self, client):
        """Test POST /budget/simulate endpoint."""
        response = await client.post(
            "/budget/simulate",
            json={
                "industry": "saas",
                "goal": "leads",
                "product_price": 99.0,
                "target_monthly_conversions": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "daily_budget" in data
        assert "monthly_budget" in data
        assert "tier" in data
        assert data["daily_budget"] > 0

    @pytest.mark.anyio
    async def test_simulate_returns_metrics(self, client):
        """Test simulation returns expected metrics."""
        response = await client.post(
            "/budget/simulate",
            json={
                "industry": "ecommerce",
                "goal": "sales",
                "product_price": 50.0,
                "target_monthly_conversions": 100,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "expected_impressions" in data
        assert "expected_clicks" in data
        assert "expected_conversions" in data
        assert "expected_cpa" in data
        assert "expected_roas" in data

    @pytest.mark.anyio
    async def test_simulate_with_target_cpa(self, client):
        """Test simulation with custom target CPA."""
        response = await client.post(
            "/budget/simulate",
            json={
                "industry": "saas",
                "goal": "leads",
                "product_price": 99.0,
                "target_monthly_conversions": 50,
                "target_cpa": 30.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["daily_budget"] > 0

    @pytest.mark.anyio
    async def test_get_benchmarks(self, client):
        """Test GET /budget/benchmarks endpoint."""
        response = await client.get("/budget/benchmarks")
        assert response.status_code == 200
        data = response.json()
        assert "benchmarks" in data
        assert "saas" in data["benchmarks"]
        assert "ecommerce" in data["benchmarks"]

    @pytest.mark.anyio
    async def test_get_benchmarks_single_industry(self, client):
        """Test GET /budget/benchmarks with industry filter."""
        response = await client.get("/budget/benchmarks?industry=saas")
        assert response.status_code == 200
        data = response.json()
        assert "benchmarks" in data
        assert "saas" in data["benchmarks"]

    @pytest.mark.anyio
    async def test_budget_demo(self, client):
        """Test POST /budget/demo endpoint."""
        response = await client.post("/budget/demo")
        assert response.status_code == 200
        data = response.json()
        assert "daily_budget" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_simulate_all_industries(self, client):
        """Test simulation works for all industries."""
        industries = ["saas", "ecommerce", "fintech", "healthcare", "education", "consumer_app"]
        for industry in industries:
            response = await client.post(
                "/budget/simulate",
                json={
                    "industry": industry,
                    "goal": "leads",
                    "product_price": 99.0,
                    "target_monthly_conversions": 50,
                },
            )
            assert response.status_code == 200, f"Failed for {industry}"
