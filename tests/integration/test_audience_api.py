# tests/integration/test_audience_api.py
"""Integration tests for Audience Targeting API (Slice 21)."""

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


class TestAudienceAPI:
    """Integration tests for /audience endpoints."""

    @pytest.mark.anyio
    async def test_suggest_audiences(self, client):
        """Test POST /audience/suggest endpoint."""
        response = await client.post(
            "/audience/suggest",
            json={
                "product_name": "Careerfied",
                "product_description": "AI-powered resume builder",
                "product_type": "saas",
                "target_persona": "Job seekers",
                "price_point": 29,
                "existing_customers": False,
                "website_traffic": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "primary_audiences" in data
        assert "secondary_audiences" in data
        assert "exclusions" in data
        assert "lookalike_strategy" in data

    @pytest.mark.anyio
    async def test_suggest_returns_budget_allocation(self, client):
        """Test suggestion includes budget allocation."""
        response = await client.post(
            "/audience/suggest",
            json={
                "product_name": "Test",
                "product_description": "Test product",
                "target_persona": "Users",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "budget_allocation" in data
        assert "testing_order" in data

    @pytest.mark.anyio
    async def test_suggest_with_existing_customers(self, client):
        """Test suggestion with customer data enables lookalikes."""
        response = await client.post(
            "/audience/suggest",
            json={
                "product_name": "Test",
                "product_description": "Test product",
                "target_persona": "Users",
                "existing_customers": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should recommend lookalike audiences
        lookalike_audiences = [a for a in data["primary_audiences"] if a.get("type") == "lookalike"]
        assert len(lookalike_audiences) > 0

    @pytest.mark.anyio
    async def test_suggest_with_website_traffic(self, client):
        """Test suggestion with traffic data enables retargeting."""
        response = await client.post(
            "/audience/suggest",
            json={
                "product_name": "Test",
                "product_description": "Test product",
                "target_persona": "Users",
                "website_traffic": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should recommend retargeting
        retargeting = [a for a in data["primary_audiences"] if a.get("type") == "retargeting"]
        assert len(retargeting) > 0

    @pytest.mark.anyio
    async def test_audience_demo(self, client):
        """Test POST /audience/demo endpoint."""
        response = await client.post("/audience/demo")
        assert response.status_code == 200
        data = response.json()
        assert "primary_audiences" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_audiences_have_scores(self, client):
        """Test audiences have relevance scores."""
        response = await client.post(
            "/audience/suggest",
            json={
                "product_name": "Test",
                "product_description": "Test product",
                "target_persona": "Users",
            },
        )
        assert response.status_code == 200
        data = response.json()
        for aud in data["primary_audiences"]:
            assert "relevance_score" in aud
            assert 0 <= aud["relevance_score"] <= 100

    @pytest.mark.anyio
    async def test_exclusions_returned(self, client):
        """Test exclusions are returned with reasons."""
        response = await client.post(
            "/audience/suggest",
            json={
                "product_name": "Test",
                "product_description": "Test product",
                "target_persona": "Users",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["exclusions"]) > 0
        for exc in data["exclusions"]:
            assert "name" in exc
            assert "reason" in exc
