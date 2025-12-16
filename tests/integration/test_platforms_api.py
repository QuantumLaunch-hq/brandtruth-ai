# tests/integration/test_platforms_api.py
"""Integration tests for Platform Recommender API (Slice 19)."""

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


class TestPlatformsAPI:
    """Integration tests for /platforms endpoints."""

    @pytest.mark.anyio
    async def test_recommend_platforms(self, client):
        """Test POST /platforms/recommend endpoint."""
        response = await client.post(
            "/platforms/recommend",
            json={
                "product_type": "b2b_saas",
                "audience_type": "founders",
                "monthly_budget": 1000,
                "product_price": 99,
                "is_visual": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "primary_platform" in data
        assert "strategy" in data
        assert "budget_allocation" in data
        assert "recommendations" in data

    @pytest.mark.anyio
    async def test_recommend_returns_rankings(self, client):
        """Test recommendations include rankings."""
        response = await client.post(
            "/platforms/recommend",
            json={
                "product_type": "b2c_saas",
                "audience_type": "consumers",
                "monthly_budget": 2000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) >= 5
        for rec in data["recommendations"]:
            assert "platform" in rec
            assert "score" in rec
            assert "rank" in rec

    @pytest.mark.anyio
    async def test_get_platforms_list(self, client):
        """Test GET /platforms/list endpoint."""
        response = await client.get("/platforms/list")
        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        assert len(data["platforms"]) >= 7

    @pytest.mark.anyio
    async def test_platforms_demo(self, client):
        """Test POST /platforms/demo endpoint."""
        response = await client.post("/platforms/demo")
        assert response.status_code == 200
        data = response.json()
        assert "primary_platform" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_recommend_low_budget(self, client):
        """Test recommendation with low budget."""
        response = await client.post(
            "/platforms/recommend",
            json={
                "product_type": "b2b_saas",
                "audience_type": "founders",
                "monthly_budget": 300,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Low budget should focus on single platform
        assert "focus" in data["strategy"].lower() or len(data["budget_allocation"]) <= 2

    @pytest.mark.anyio
    async def test_recommend_high_budget(self, client):
        """Test recommendation with high budget."""
        response = await client.post(
            "/platforms/recommend",
            json={
                "product_type": "ecommerce",
                "audience_type": "consumers",
                "monthly_budget": 10000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # High budget should diversify
        assert len(data["budget_allocation"]) >= 2
