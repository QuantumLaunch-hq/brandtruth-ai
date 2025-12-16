# tests/integration/test_landing_api.py
"""Integration tests for Landing Page Analyzer API (Slice 17)."""

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


class TestLandingAPI:
    """Integration tests for /landing endpoints."""

    @pytest.mark.anyio
    async def test_analyze_landing_page(self, client):
        """Test POST /landing/analyze endpoint."""
        response = await client.post(
            "/landing/analyze",
            json={
                "landing_page_url": "https://careerfied.ai",
                "ad_headline": "Stop Getting Rejected",
                "ad_primary_text": "Build ATS-optimized resumes",
                "ad_cta": "Get Started Free",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "message_match_score" in data
        assert "message_match_level" in data
        assert 0 <= data["overall_score"] <= 100

    @pytest.mark.anyio
    async def test_analyze_returns_component_scores(self, client):
        """Test component scores are returned."""
        response = await client.post(
            "/landing/analyze",
            json={
                "landing_page_url": "https://test.com",
                "ad_headline": "Test",
                "ad_primary_text": "Test text",
                "ad_cta": "Learn More",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "above_fold_score" in data
        assert "cta_score" in data
        assert "mobile_score" in data
        assert "load_speed_score" in data

    @pytest.mark.anyio
    async def test_landing_demo(self, client):
        """Test POST /landing/demo endpoint."""
        response = await client.post("/landing/demo")
        assert response.status_code == 200
        data = response.json()
        assert "score" in data or "overall_score" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_analyze_validation(self, client):
        """Test validation errors."""
        response = await client.post(
            "/landing/analyze",
            json={
                "ad_headline": "Missing URL",
            },
        )
        assert response.status_code == 422
