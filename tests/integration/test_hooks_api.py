# tests/integration/test_hooks_api.py
"""Integration tests for Hook Generator API (Slice 16)."""

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


class TestHooksAPI:
    """Integration tests for /hooks endpoints."""

    @pytest.mark.anyio
    async def test_generate_hooks(self, client):
        """Test POST /hooks/generate endpoint."""
        response = await client.post(
            "/hooks/generate",
            json={
                "product_name": "Careerfied",
                "product_description": "AI-powered resume builder",
                "target_audience": "job seekers",
                "pain_points": ["getting rejected", "ATS systems"],
                "benefits": ["land more interviews"],
                "include_emojis": False,
                "num_hooks": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "hooks" in data
        assert len(data["hooks"]) == 5
        assert "best_hook" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_generate_hooks_with_emojis(self, client):
        """Test hook generation with emojis."""
        response = await client.post(
            "/hooks/generate",
            json={
                "product_name": "Test",
                "product_description": "Test product",
                "target_audience": "users",
                "include_emojis": True,
                "num_hooks": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["hooks"]) == 3

    @pytest.mark.anyio
    async def test_get_patterns(self, client):
        """Test GET /hooks/patterns endpoint."""
        response = await client.get("/hooks/patterns")
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert "power_words" in data
        assert len(data["patterns"]) == 10

    @pytest.mark.anyio
    async def test_hooks_demo(self, client):
        """Test POST /hooks/demo endpoint."""
        response = await client.post("/hooks/demo")
        assert response.status_code == 200
        data = response.json()
        assert "hooks" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_generate_hooks_validation(self, client):
        """Test validation errors."""
        response = await client.post(
            "/hooks/generate",
            json={
                "product_description": "Missing product_name",
            },
        )
        assert response.status_code == 422
