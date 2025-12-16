# tests/integration/test_api_endpoints.py
"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api_server import app


@pytest.fixture
async def client():
    """Async HTTP client using ASGITransport for httpx 0.28+."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestRootEndpoints:
    """Tests for root endpoints."""
    
    @pytest.mark.asyncio
    async def test_root(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    @pytest.mark.asyncio
    async def test_health(self, client):
        """Test health endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPredictEndpoints:
    """Tests for prediction endpoints (Slice 9)."""
    
    @pytest.mark.asyncio
    async def test_predict(self, client):
        """Test predict endpoint."""
        response = await client.post(
            "/predict",
            json={
                "headline": "Stop Getting Rejected by ATS",
                "primary_text": "Build resumes that get interviews",
                "cta": "Get Started",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert 0 <= data["score"] <= 100
        assert "summary" in data
    
    @pytest.mark.asyncio
    async def test_predict_demo(self, client):
        """Test predict demo endpoint."""
        response = await client.post("/predict/demo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert "score" in data


class TestAttentionEndpoints:
    """Tests for attention endpoints (Slice 10)."""
    
    @pytest.mark.asyncio
    async def test_attention_analyze(self, client):
        """Test attention analyze endpoint."""
        response = await client.post(
            "/attention/analyze",
            json={
                "image_url": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600",
                "headline": "Test Headline",
                "cta": "Learn More",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "summary" in data
    
    @pytest.mark.asyncio
    async def test_attention_demo(self, client):
        """Test attention demo endpoint."""
        response = await client.post("/attention/demo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True


class TestExportEndpoints:
    """Tests for export endpoints (Slice 11)."""
    
    @pytest.mark.asyncio
    async def test_get_formats(self, client):
        """Test get formats endpoint."""
        response = await client.get("/export/formats")
        
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) == 9  # 9 formats
    
    @pytest.mark.asyncio
    async def test_export_demo(self, client):
        """Test export demo endpoint."""
        response = await client.post("/export/demo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["exported"] > 0


class TestIntelEndpoints:
    """Tests for competitor intel endpoints (Slice 12)."""
    
    @pytest.mark.asyncio
    async def test_intel_analyze(self, client):
        """Test intel analyze endpoint."""
        response = await client.post(
            "/intel/analyze",
            json={
                "brand_name": "Careerfied",
                "industry": "career",
                "competitor_names": ["Resume.io", "Zety"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "competitors" in data
        assert "recommendations" in data
    
    @pytest.mark.asyncio
    async def test_intel_demo(self, client):
        """Test intel demo endpoint."""
        response = await client.post("/intel/demo/career")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["industry"] == "career"
    
    @pytest.mark.asyncio
    async def test_intel_demo_invalid_industry(self, client):
        """Test intel demo with invalid industry."""
        response = await client.post("/intel/demo/invalid")
        
        assert response.status_code == 400


class TestVideoEndpoints:
    """Tests for video endpoints (Slice 13)."""
    
    @pytest.mark.asyncio
    async def test_video_generate(self, client):
        """Test video generate endpoint."""
        response = await client.post(
            "/video/generate",
            json={
                "brand_name": "Careerfied",
                "product_description": "AI resume builder",
                "target_audience": "Job seekers",
                "key_benefits": ["ATS-optimized", "Templates", "Feedback"],
                "cta": "Get Started",
                "style": "ugc",
                "aspect_ratio": "9:16",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "video_id" in data
        assert "script" in data
        assert "predictions" in data
    
    @pytest.mark.asyncio
    async def test_video_demo(self, client):
        """Test video demo endpoint."""
        response = await client.post("/video/demo/ugc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["style"] == "ugc"
    
    @pytest.mark.asyncio
    async def test_video_demo_invalid_style(self, client):
        """Test video demo with invalid style."""
        response = await client.post("/video/demo/invalid")
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_video_styles(self, client):
        """Test video styles endpoint."""
        response = await client.get("/video/styles")
        
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        assert len(data["styles"]) == 6
    
    @pytest.mark.asyncio
    async def test_video_avatars(self, client):
        """Test video avatars endpoint."""
        response = await client.get("/video/avatars")
        
        assert response.status_code == 200
        data = response.json()
        assert "avatars" in data
        assert len(data["avatars"]) >= 5
    
    @pytest.mark.asyncio
    async def test_video_music(self, client):
        """Test video music endpoint."""
        response = await client.get("/video/music")
        
        assert response.status_code == 200
        data = response.json()
        assert "tracks" in data
        assert len(data["tracks"]) >= 5


class TestFatigueEndpoints:
    """Tests for fatigue endpoints (Slice 14)."""
    
    @pytest.mark.asyncio
    async def test_fatigue_predict(self, client):
        """Test fatigue predict endpoint."""
        response = await client.post(
            "/fatigue/predict",
            json={
                "ad_id": "test_ad",
                "days_running": 14,
                "frequency": 2.5,
                "reach": 35000,
                "audience_size": 100000,
                "industry": "saas",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "fatigue_score" in data
        assert "level" in data
        assert "recommendations" in data
    
    @pytest.mark.asyncio
    async def test_fatigue_demo(self, client):
        """Test fatigue demo endpoint."""
        response = await client.post("/fatigue/demo/moderate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["scenario"] == "moderate"
    
    @pytest.mark.asyncio
    async def test_fatigue_demo_invalid_scenario(self, client):
        """Test fatigue demo with invalid scenario."""
        response = await client.post("/fatigue/demo/invalid")
        
        assert response.status_code == 400


class TestProofEndpoints:
    """Tests for proof pack endpoints (Slice 15)."""
    
    @pytest.mark.asyncio
    async def test_proof_generate(self, client):
        """Test proof generate endpoint."""
        response = await client.post(
            "/proof/generate",
            json={
                "ad_id": "test_ad",
                "campaign_name": "Test Campaign",
                "brand_name": "Test Brand",
                "headline": "Test Headline",
                "primary_text": "Test body text",
                "cta": "Learn More",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "pack_id" in data
        assert "compliance" in data
        assert "safety_score" in data
    
    @pytest.mark.asyncio
    async def test_proof_demo(self, client):
        """Test proof demo endpoint."""
        response = await client.post("/proof/demo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert "safety_score" in data


class TestSentimentEndpoints:
    """Tests for sentiment endpoints (Slice 6)."""
    
    @pytest.mark.asyncio
    async def test_sentiment_check(self, client):
        """Test sentiment check endpoint."""
        response = await client.post(
            "/sentiment/check",
            json={
                "brand_name": "Careerfied",
                "scenario": "normal",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "health" in data
        assert "auto_pause" in data
    
    @pytest.mark.asyncio
    async def test_sentiment_demo_crisis(self, client):
        """Test sentiment crisis demo."""
        response = await client.post("/sentiment/demo/crisis")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["scenario"] == "crisis"
        assert data["auto_pause"] is True  # Crisis should trigger pause
    
    @pytest.mark.asyncio
    async def test_sentiment_demo_positive(self, client):
        """Test sentiment positive demo."""
        response = await client.post("/sentiment/demo/positive")
        
        assert response.status_code == 200
        data = response.json()
        assert data["auto_pause"] is False  # Positive should not pause


class TestMetaEndpoints:
    """Tests for Meta publishing endpoints (Slice 8)."""
    
    @pytest.mark.asyncio
    async def test_meta_demo(self, client):
        """Test meta demo endpoint."""
        response = await client.post("/meta/demo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["demo"] is True
        assert data["success"] is True


class TestPipelineEndpoints:
    """Tests for pipeline endpoints (Slice 7)."""
    
    @pytest.mark.asyncio
    async def test_jobs_list(self, client):
        """Test jobs list endpoint."""
        response = await client.get("/jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
