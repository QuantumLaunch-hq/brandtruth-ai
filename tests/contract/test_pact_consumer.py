# tests/contract/test_pact_consumer.py
"""Pact Consumer Contract Tests.

Consumer-driven contracts define what the frontend expects from the backend API.
These contracts are then verified against the actual backend implementation.

Install: pip install pact-python
"""

import pytest
import atexit
from pathlib import Path

# Try to import pact, skip tests if not installed
try:
    from pact import Consumer, Provider, Like, EachLike, Term
    PACT_AVAILABLE = True
except ImportError:
    PACT_AVAILABLE = False
    pytest.skip("pact-python not installed", allow_module_level=True)


# =============================================================================
# PACT SETUP
# =============================================================================

PACT_DIR = Path(__file__).parent / "pacts"
PACT_DIR.mkdir(exist_ok=True)

# Create the pact between consumer (frontend) and provider (backend)
pact = Consumer("BrandTruthFrontend").has_pact_with(
    Provider("BrandTruthAPI"),
    pact_dir=str(PACT_DIR),
    log_dir=str(PACT_DIR / "logs"),
)

# Start the mock service
pact.start_service()

# Ensure we stop the service when tests complete
atexit.register(pact.stop_service)


# =============================================================================
# CONSUMER CONTRACT TESTS
# =============================================================================

class TestHealthContract:
    """Contract for /health endpoint."""
    
    @pytest.mark.pact
    def test_health_endpoint_contract(self):
        """Frontend expects health endpoint to return status."""
        expected = {
            "status": "healthy"
        }
        
        (pact
         .given("the API is running")
         .upon_receiving("a health check request")
         .with_request("GET", "/health")
         .will_respond_with(200, body=expected))
        
        with pact:
            # Simulate frontend calling the API
            import requests
            result = requests.get(f"{pact.uri}/health")
            assert result.status_code == 200
            assert result.json()["status"] == "healthy"


class TestPredictContract:
    """Contract for /predict endpoint."""
    
    @pytest.mark.pact
    def test_predict_endpoint_contract(self):
        """Frontend expects prediction response structure."""
        request_body = {
            "headline": "Test Headline",
            "primary_text": "Test primary text",
            "cta": "Learn More"
        }
        
        expected_response = {
            "overall_score": Like(75),  # Any integer
            "performance_tier": Term(r"exceptional|strong|good|average|weak|poor", "good"),
            "confidence": Like(0.85),  # Any float
            "ctr_prediction": Term(r"very_high|high|above_average|average|below_average|low", "average"),
            "estimated_ctr_range": EachLike(1.0, minimum=2),  # Array of floats
            "conversion_potential": Term(r"High|Medium|Low", "Medium"),
            "component_scores": EachLike({
                "name": Like("Headline"),
                "score": Like(80),
                "weight": Like(0.25),
                "analysis": Like("Analysis text"),
                "strengths": EachLike("Strength", minimum=0),
                "weaknesses": EachLike("Weakness", minimum=0),
            }),
            "improvements": EachLike({
                "component": Like("Headline"),
                "priority": Term(r"critical|high|medium|low", "high"),
                "suggestion": Like("Suggestion text"),
                "expected_impact": Like("Impact text"),
            }),
            "ab_test_suggestions": EachLike({
                "variant_name": Like("Variant A"),
                "change_description": Like("Change description"),
                "hypothesis": Like("Hypothesis"),
                "expected_lift": Like("10%"),
            }, minimum=0),
        }
        
        (pact
         .given("prediction service is available")
         .upon_receiving("a performance prediction request")
         .with_request("POST", "/predict", body=request_body, headers={"Content-Type": "application/json"})
         .will_respond_with(200, body=expected_response))
        
        with pact:
            import requests
            result = requests.post(
                f"{pact.uri}/predict",
                json=request_body,
                headers={"Content-Type": "application/json"}
            )
            assert result.status_code == 200
            data = result.json()
            assert "overall_score" in data
            assert "performance_tier" in data


class TestExportFormatsContract:
    """Contract for /export/formats endpoint."""
    
    @pytest.mark.pact
    def test_export_formats_contract(self):
        """Frontend expects format list structure."""
        expected = {
            "formats": EachLike({
                "id": Like("meta_feed"),
                "name": Like("Meta Feed"),
                "width": Like(1200),
                "height": Like(628),
                "platform": Like("meta"),
                "aspect_ratio": Like("1.91:1"),
            })
        }
        
        (pact
         .given("export formats are available")
         .upon_receiving("a request for available formats")
         .with_request("GET", "/export/formats")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/export/formats")
            assert result.status_code == 200
            data = result.json()
            assert "formats" in data
            assert isinstance(data["formats"], list)


class TestVideoStylesContract:
    """Contract for /video/styles endpoint."""
    
    @pytest.mark.pact
    def test_video_styles_contract(self):
        """Frontend expects video styles structure."""
        expected = {
            "styles": EachLike({
                "id": Like("ugc"),
                "name": Like("UGC Style"),
                "description": Like("User-generated content style"),
                "best_for": EachLike("Social media", minimum=1),
                "duration_range": Like("15-60s"),
            })
        }
        
        (pact
         .given("video styles are available")
         .upon_receiving("a request for video styles")
         .with_request("GET", "/video/styles")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/video/styles")
            assert result.status_code == 200
            data = result.json()
            assert "styles" in data


class TestIntelIndustriesContract:
    """Contract for /intel/industries endpoint."""
    
    @pytest.mark.pact
    def test_intel_industries_contract(self):
        """Frontend expects industries list."""
        expected = {
            "industries": EachLike("career", minimum=1)
        }
        
        (pact
         .given("industries list is available")
         .upon_receiving("a request for supported industries")
         .with_request("GET", "/intel/industries")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/intel/industries")
            assert result.status_code == 200
            data = result.json()
            assert "industries" in data


class TestFatigueDemoContract:
    """Contract for /fatigue/demo/:scenario endpoint."""
    
    @pytest.mark.pact
    def test_fatigue_demo_fresh_contract(self):
        """Frontend expects fatigue response for fresh scenario."""
        expected = {
            "fatigue_score": Like(15),
            "fatigue_level": Term(r"fresh|healthy|moderate|high|critical", "fresh"),
            "days_until_refresh": Like(45),
            "decay_rate": Like(0.02),
            "decay_pattern": Like("linear"),
            "recommendations": EachLike({
                "action": Like("Action"),
                "priority": Term(r"high|medium|low", "low"),
                "reason": Like("Reason"),
            }),
        }
        
        (pact
         .given("fatigue demo is available")
         .upon_receiving("a request for fresh fatigue demo")
         .with_request("GET", "/fatigue/demo/fresh")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/fatigue/demo/fresh")
            assert result.status_code == 200
            data = result.json()
            assert "fatigue_score" in data


class TestSentimentDemoContract:
    """Contract for /sentiment/demo/:scenario endpoint."""
    
    @pytest.mark.pact
    def test_sentiment_demo_normal_contract(self):
        """Frontend expects sentiment response for normal scenario."""
        expected = {
            "brand_name": Like("TestBrand"),
            "overall_sentiment": Like(0.65),
            "mention_count": Like(150),
            "should_pause": Like(False),
            "top_concerns": EachLike("Concern", minimum=0),
        }
        
        (pact
         .given("sentiment demo is available")
         .upon_receiving("a request for normal sentiment demo")
         .with_request("GET", "/sentiment/demo/normal")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/sentiment/demo/normal")
            assert result.status_code == 200
            data = result.json()
            assert "brand_name" in data
            assert "should_pause" in data


class TestProofDemoContract:
    """Contract for /proof/demo endpoint."""
    
    @pytest.mark.pact
    def test_proof_demo_contract(self):
        """Frontend expects proof pack response structure."""
        expected = {
            "ad_id": Like("ad_001"),
            "compliance_status": Term(r"compliant|needs_review|non_compliant", "compliant"),
            "safety_score": Like(95),
            "claim_verifications": EachLike({
                "claim": Like("Claim text"),
                "verified": Like(True),
                "risk_level": Term(r"low|medium|high", "low"),
            }),
            "action_items": EachLike({
                "item": Like("Action item"),
                "priority": Like("low"),
            }, minimum=0),
        }
        
        (pact
         .given("proof demo is available")
         .upon_receiving("a request for proof pack demo")
         .with_request("GET", "/proof/demo")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/proof/demo")
            assert result.status_code == 200
            data = result.json()
            assert "compliance_status" in data


class TestJobsContract:
    """Contract for /jobs endpoint."""
    
    @pytest.mark.pact
    def test_jobs_list_contract(self):
        """Frontend expects jobs list structure."""
        expected = {
            "jobs": EachLike({
                "job_id": Like("job_123"),
                "status": Term(r"pending|running|completed|failed", "completed"),
                "created_at": Like("2025-12-15T00:00:00"),
            }, minimum=0)
        }
        
        (pact
         .given("jobs endpoint is available")
         .upon_receiving("a request for jobs list")
         .with_request("GET", "/jobs")
         .will_respond_with(200, body=expected))
        
        with pact:
            import requests
            result = requests.get(f"{pact.uri}/jobs")
            assert result.status_code == 200
            data = result.json()
            assert "jobs" in data
