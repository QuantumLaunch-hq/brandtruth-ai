# tests/contract/test_openapi_schema.py
"""OpenAPI Schema Validation Tests.

Validates that API responses conform to the OpenAPI specification.
Ensures contract between frontend and backend is maintained.
"""

import pytest
from httpx import AsyncClient, ASGITransport

# Import the FastAPI app
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from api_server import app


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def openapi_schema():
    """Get the OpenAPI schema from the app."""
    return app.openapi()


@pytest.fixture
async def async_client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# SCHEMA VALIDATION TESTS
# =============================================================================

class TestOpenAPISchemaValidity:
    """Test that the OpenAPI schema itself is valid."""
    
    @pytest.mark.contract
    def test_schema_has_info(self, openapi_schema):
        """Verify schema has required info section."""
        assert "info" in openapi_schema
        assert "title" in openapi_schema["info"]
        assert "version" in openapi_schema["info"]
    
    @pytest.mark.contract
    def test_schema_has_paths(self, openapi_schema):
        """Verify schema has paths defined."""
        assert "paths" in openapi_schema
        assert len(openapi_schema["paths"]) > 0
    
    @pytest.mark.contract
    def test_all_endpoints_have_responses(self, openapi_schema):
        """Verify all endpoints define responses."""
        for path, methods in openapi_schema["paths"].items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    assert "responses" in details, f"No responses for {method.upper()} {path}"
    
    @pytest.mark.contract
    def test_api_version_matches(self, openapi_schema):
        """Test API version is 1.0.0."""
        assert openapi_schema["info"]["version"] == "1.0.0"
    
    @pytest.mark.contract
    def test_api_title_correct(self, openapi_schema):
        """Test API title contains BrandTruth."""
        assert "BrandTruth" in openapi_schema["info"]["title"]


class TestEndpointSchemaCompliance:
    """Test that actual API responses match their schemas."""
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_root_endpoint_schema(self, async_client):
        """Test / endpoint matches schema."""
        response = await async_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert "endpoints" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_health_endpoint_schema(self, async_client):
        """Test /health endpoint matches schema."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_predict_endpoint_schema(self, async_client):
        """Test /predict endpoint request/response schema."""
        request_data = {
            "headline": "Test Headline",
            "primary_text": "Test primary text for the ad",
            "cta": "Learn More"
        }
        
        response = await async_client.post("/predict", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Validate actual response fields
        assert "score" in data
        assert "tier" in data
        assert "summary" in data
        
        # Validate types
        assert isinstance(data["score"], int)
        assert 0 <= data["score"] <= 100
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_predict_demo_endpoint_schema(self, async_client):
        """Test /predict/demo endpoint schema (POST)."""
        response = await async_client.post("/predict/demo")
        assert response.status_code == 200
        
        data = response.json()
        assert "demo" in data
        assert "score" in data
        assert "summary" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_attention_demo_endpoint_schema(self, async_client):
        """Test /attention/demo endpoint schema (POST)."""
        response = await async_client.post("/attention/demo")
        assert response.status_code == 200
        
        data = response.json()
        assert "demo" in data
        assert "score" in data
        assert "summary" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_export_formats_endpoint_schema(self, async_client):
        """Test /export/formats endpoint schema."""
        response = await async_client.get("/export/formats")
        assert response.status_code == 200
        
        data = response.json()
        assert "formats" in data
        assert "total" in data
        assert isinstance(data["formats"], list)
        
        # Each format should have required fields
        for fmt in data["formats"]:
            assert "id" in fmt
            assert "name" in fmt
            assert "width" in fmt
            assert "height" in fmt
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_video_styles_endpoint_schema(self, async_client):
        """Test /video/styles endpoint schema."""
        response = await async_client.get("/video/styles")
        assert response.status_code == 200
        
        data = response.json()
        assert "styles" in data
        assert isinstance(data["styles"], list)
        
        for style in data["styles"]:
            assert "id" in style
            assert "name" in style
            assert "description" in style
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_video_avatars_endpoint_schema(self, async_client):
        """Test /video/avatars endpoint schema."""
        response = await async_client.get("/video/avatars")
        assert response.status_code == 200
        
        data = response.json()
        assert "avatars" in data
        assert isinstance(data["avatars"], list)
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_video_music_endpoint_schema(self, async_client):
        """Test /video/music endpoint schema."""
        response = await async_client.get("/video/music")
        assert response.status_code == 200
        
        data = response.json()
        assert "tracks" in data
        assert isinstance(data["tracks"], list)
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_fatigue_demo_endpoint_schema(self, async_client):
        """Test /fatigue/demo/:scenario endpoint schema (POST)."""
        scenarios = ["fresh", "healthy", "moderate", "high", "critical"]
        
        for scenario in scenarios:
            response = await async_client.post(f"/fatigue/demo/{scenario}")
            assert response.status_code == 200
            
            data = response.json()
            assert "demo" in data
            assert "scenario" in data
            assert "fatigue_score" in data
            assert "summary" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_sentiment_demo_endpoint_schema(self, async_client):
        """Test /sentiment/demo/:scenario endpoint schema (POST)."""
        scenarios = ["normal", "crisis", "positive"]
        
        for scenario in scenarios:
            response = await async_client.post(f"/sentiment/demo/{scenario}")
            assert response.status_code == 200
            
            data = response.json()
            assert "demo" in data
            assert "scenario" in data
            assert "health" in data
            assert "auto_pause" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_proof_demo_endpoint_schema(self, async_client):
        """Test /proof/demo endpoint schema (POST)."""
        response = await async_client.post("/proof/demo")
        assert response.status_code == 200
        
        data = response.json()
        assert "demo" in data
        assert "summary" in data
        assert "safety_score" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_intel_demo_endpoint_schema(self, async_client):
        """Test /intel/demo/:industry endpoint schema (POST)."""
        industries = ["career", "saas", "ecommerce"]
        
        for industry in industries:
            response = await async_client.post(f"/intel/demo/{industry}")
            assert response.status_code == 200
            
            data = response.json()
            assert "demo" in data
            assert "industry" in data
            assert "summary" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_jobs_endpoint_schema(self, async_client):
        """Test /jobs endpoint schema."""
        response = await async_client.get("/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)


class TestRequestValidation:
    """Test that invalid requests are properly rejected."""
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_predict_missing_required_field(self, async_client):
        """Test /predict rejects missing required fields."""
        # Missing headline
        request_data = {
            "primary_text": "Test text",
            "cta": "Learn More"
        }
        
        response = await async_client.post("/predict", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_intel_invalid_industry(self, async_client):
        """Test /intel/demo rejects invalid industry (POST)."""
        response = await async_client.post("/intel/demo/invalid_industry_xyz")
        assert response.status_code == 400
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_video_invalid_style(self, async_client):
        """Test /video/demo rejects invalid style (POST)."""
        response = await async_client.post("/video/demo/invalid_style_xyz")
        assert response.status_code == 400
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_fatigue_invalid_scenario(self, async_client):
        """Test /fatigue/demo rejects invalid scenario (POST)."""
        response = await async_client.post("/fatigue/demo/invalid_scenario_xyz")
        assert response.status_code == 400
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_sentiment_invalid_scenario(self, async_client):
        """Test /sentiment/demo rejects invalid scenario (POST)."""
        response = await async_client.post("/sentiment/demo/invalid_scenario_xyz")
        assert response.status_code == 400


class TestResponseTypes:
    """Test that responses have correct content types."""
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_json_content_type(self, async_client):
        """Test JSON endpoints return correct content type."""
        response = await async_client.get("/")
        assert "application/json" in response.headers.get("content-type", "")
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_health_json_content_type(self, async_client):
        """Test health endpoint returns JSON."""
        response = await async_client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


class TestCriticalEndpoints:
    """Test the most critical API endpoints for ad generation."""
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_video_generate_endpoint_schema(self, async_client):
        """Test /video/generate endpoint schema."""
        request_data = {
            "brand_name": "TestBrand",
            "product_description": "Test product description",
            "target_audience": "Test audience",
            "key_benefits": ["Benefit 1", "Benefit 2"],
            "cta": "Get Started"
        }
        
        response = await async_client.post("/video/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "video_id" in data
        assert "title" in data
        assert "status" in data
        assert "script" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_attention_analyze_endpoint_schema(self, async_client):
        """Test /attention/analyze endpoint schema."""
        request_data = {
            "image_url": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600",
            "headline": "Test Headline",
            "cta": "Learn More"
        }
        
        response = await async_client.post("/attention/analyze", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "score" in data
        assert "summary" in data
    
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_sentiment_check_endpoint_schema(self, async_client):
        """Test /sentiment/check endpoint schema."""
        request_data = {
            "brand_name": "TestBrand",
            "scenario": "normal"
        }
        
        response = await async_client.post("/sentiment/check", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "health" in data
        assert "auto_pause" in data
