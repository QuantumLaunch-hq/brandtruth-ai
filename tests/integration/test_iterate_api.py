# tests/integration/test_iterate_api.py
"""Integration tests for Iteration Assistant API (Slice 22)."""

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


class TestIterateAPI:
    """Integration tests for /iterate endpoints."""

    @pytest.mark.anyio
    async def test_analyze_ad(self, client):
        """Test POST /iterate/analyze endpoint."""
        response = await client.post(
            "/iterate/analyze",
            json={
                "headline": "Check out our product",
                "primary_text": "We have a great product",
                "cta": "Learn More",
                "current_ctr": 0.5,
                "current_cvr": 1.0,
                "current_cpa": 120,
                "target_cpa": 50,
                "impressions": 10000,
                "frequency": 2.0,
                "days_running": 7,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "diagnoses" in data
        assert "improved_variants" in data
        assert "priority_fixes" in data
        assert "estimated_improvement" in data

    @pytest.mark.anyio
    async def test_analyze_returns_diagnoses(self, client):
        """Test analysis returns properly structured diagnoses."""
        response = await client.post(
            "/iterate/analyze",
            json={
                "headline": "Test",
                "primary_text": "Test",
                "cta": "Test",
                "current_ctr": 0.3,
                "current_cvr": 0.5,
                "current_cpa": 200,
                "target_cpa": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        for diag in data["diagnoses"]:
            assert "issue" in diag
            assert "severity" in diag
            assert "description" in diag

    @pytest.mark.anyio
    async def test_analyze_returns_improvements(self, client):
        """Test analysis returns improved variants."""
        response = await client.post(
            "/iterate/analyze",
            json={
                "headline": "Bad headline",
                "primary_text": "Bad text",
                "cta": "Learn More",
                "current_ctr": 0.4,
                "current_cvr": 1.0,
                "current_cpa": 100,
                "target_cpa": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        for imp in data["improved_variants"]:
            assert "element" in imp
            assert "original" in imp
            assert "improved" in imp
            assert "rationale" in imp

    @pytest.mark.anyio
    async def test_analyze_detects_low_ctr(self, client):
        """Test low CTR is diagnosed."""
        response = await client.post(
            "/iterate/analyze",
            json={
                "headline": "Test",
                "primary_text": "Test",
                "cta": "Test",
                "current_ctr": 0.2,  # Very low
                "current_cvr": 2.0,
                "current_cpa": 80,
                "target_cpa": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        issues = [d["issue"] for d in data["diagnoses"]]
        assert "low_ctr" in issues

    @pytest.mark.anyio
    async def test_analyze_detects_high_frequency(self, client):
        """Test high frequency is diagnosed."""
        response = await client.post(
            "/iterate/analyze",
            json={
                "headline": "Test",
                "primary_text": "Test",
                "cta": "Test",
                "current_ctr": 1.0,
                "current_cvr": 2.0,
                "current_cpa": 80,
                "target_cpa": 50,
                "frequency": 5.0,  # High
            },
        )
        assert response.status_code == 200
        data = response.json()
        issues = [d["issue"] for d in data["diagnoses"]]
        assert "high_frequency" in issues

    @pytest.mark.anyio
    async def test_iterate_demo(self, client):
        """Test POST /iterate/demo endpoint."""
        response = await client.post("/iterate/demo")
        assert response.status_code == 200
        data = response.json()
        assert "diagnoses" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_analyze_good_performance(self, client):
        """Test analysis of good performing ad."""
        response = await client.post(
            "/iterate/analyze",
            json={
                "headline": "Stop Getting Rejected",
                "primary_text": "Build ATS-optimized resumes",
                "cta": "Get Started Free",
                "current_ctr": 2.5,
                "current_cvr": 4.0,
                "current_cpa": 40,
                "target_cpa": 50,
                "frequency": 1.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should have few or no critical issues
        critical = [d for d in data["diagnoses"] if d["severity"] == "critical"]
        assert len(critical) == 0
