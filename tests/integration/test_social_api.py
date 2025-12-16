# tests/integration/test_social_api.py
"""Integration tests for Social Proof Collector API (Slice 23)."""

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


class TestSocialAPI:
    """Integration tests for /social endpoints."""

    @pytest.mark.anyio
    async def test_collect_social_proof(self, client):
        """Test POST /social/collect endpoint."""
        response = await client.post(
            "/social/collect",
            json={
                "brand_name": "Careerfied",
                "brand_url": "https://careerfied.ai",
                "product_description": "AI-powered resume builder",
                "existing_testimonials": [
                    "This helped me land my dream job!",
                    "Got 3 interviews in the first week",
                ],
                "user_count": 1500,
                "rating": 4.8,
                "notable_customers": ["Google", "Meta"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "proofs" in data
        assert "trust_score" in data
        assert "ad_snippets" in data

    @pytest.mark.anyio
    async def test_collect_returns_proofs(self, client):
        """Test collection returns properly structured proofs."""
        response = await client.post(
            "/social/collect",
            json={
                "brand_name": "Test",
                "brand_url": "https://test.com",
                "product_description": "Test product",
                "existing_testimonials": ["Great product!"],
                "user_count": 500,
            },
        )
        assert response.status_code == 200
        data = response.json()
        for proof in data["proofs"]:
            assert "type" in proof
            assert "content" in proof
            assert "ad_ready" in proof

    @pytest.mark.anyio
    async def test_collect_calculates_trust_score(self, client):
        """Test trust score is calculated correctly."""
        # Minimal proof
        minimal = await client.post(
            "/social/collect",
            json={
                "brand_name": "Test",
                "brand_url": "https://test.com",
                "product_description": "Test",
            },
        )
        # Full proof
        full = await client.post(
            "/social/collect",
            json={
                "brand_name": "Test",
                "brand_url": "https://test.com",
                "product_description": "Test",
                "existing_testimonials": ["Great!", "Amazing!"],
                "user_count": 10000,
                "rating": 4.9,
                "notable_customers": ["Google", "Microsoft", "Apple"],
            },
        )
        assert minimal.status_code == 200
        assert full.status_code == 200
        assert full.json()["trust_score"] > minimal.json()["trust_score"]

    @pytest.mark.anyio
    async def test_collect_returns_ad_snippets(self, client):
        """Test ad-ready snippets are generated."""
        response = await client.post(
            "/social/collect",
            json={
                "brand_name": "Test",
                "brand_url": "https://test.com",
                "product_description": "Test",
                "user_count": 1000,
                "rating": 4.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["ad_snippets"]) > 0

    @pytest.mark.anyio
    async def test_collect_returns_best_proof(self, client):
        """Test best testimonial and stat are selected."""
        response = await client.post(
            "/social/collect",
            json={
                "brand_name": "Test",
                "brand_url": "https://test.com",
                "product_description": "Test",
                "existing_testimonials": ["This is amazing!"],
                "user_count": 5000,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "best_testimonial" in data
        assert "best_stat" in data

    @pytest.mark.anyio
    async def test_social_demo(self, client):
        """Test POST /social/demo endpoint."""
        response = await client.post("/social/demo")
        assert response.status_code == 200
        data = response.json()
        assert "trust_score" in data
        assert "summary" in data

    @pytest.mark.anyio
    async def test_collect_minimal_request(self, client):
        """Test collection with minimal data."""
        response = await client.post(
            "/social/collect",
            json={
                "brand_name": "NewBrand",
                "brand_url": "https://newbrand.com",
                "product_description": "A new product",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["trust_score"] >= 0
        assert "recommendations" in data

    @pytest.mark.anyio
    async def test_collect_formats_large_numbers(self, client):
        """Test large user counts are formatted."""
        response = await client.post(
            "/social/collect",
            json={
                "brand_name": "Test",
                "brand_url": "https://test.com",
                "product_description": "Test",
                "user_count": 1500000,  # 1.5M
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Should format as M or K
        stat_proofs = [p for p in data["proofs"] if p["type"] == "stat"]
        assert len(stat_proofs) > 0
