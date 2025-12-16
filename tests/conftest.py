# tests/conftest.py
"""Pytest configuration and shared fixtures for BrandTruth AI tests."""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_server import app


# =============================================================================
# ASYNC FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for API testing using ASGITransport (httpx 0.28+)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_brand_profile():
    """Sample brand profile for testing."""
    return {
        "brand_name": "Careerfied",
        "tagline": "Build resumes that get interviews",
        "value_propositions": [
            "AI-powered resume optimization",
            "ATS-friendly templates",
            "Real-time feedback",
        ],
        "target_audience": "Job seekers frustrated with resume rejections",
        "tone_of_voice": "Confident, supportive, professional",
        "claims": [
            {
                "claim": "Join 10,000+ job seekers",
                "source_text": "Based on user surveys",
                "risk_level": "low",
            },
            {
                "claim": "AI-powered optimization",
                "source_text": "Uses GPT-4",
                "risk_level": "low",
            },
        ],
        "primary_color": "#4F46E5",
        "secondary_color": "#F59E0B",
    }


@pytest.fixture
def sample_copy_variant():
    """Sample copy variant for testing."""
    return {
        "id": "variant_001",
        "headline": "Stop Getting Rejected by ATS",
        "primary_text": "Build resumes that get interviews with AI-powered optimization.",
        "cta": "Get Started",
        "hook_type": "pain_point",
        "emotion_target": "frustration_relief",
    }


@pytest.fixture
def sample_ad_performance_data():
    """Sample ad performance data for fatigue testing."""
    return {
        "ad_id": "test_ad_001",
        "days_running": 14,
        "impressions": 50000,
        "clicks": 1000,
        "frequency": 2.5,
        "reach": 20000,
        "audience_size": 100000,
        "ctr_history": [2.0, 1.95, 1.9, 1.85, 1.8, 1.75, 1.7, 1.65, 1.6, 1.55, 1.5, 1.48, 1.45, 1.42],
        "cpm_history": [10.0, 10.2, 10.4, 10.6, 10.8, 11.0, 11.2, 11.4, 11.6, 11.8, 12.0, 12.2, 12.4, 12.6],
        "industry": "saas",
    }


@pytest.fixture
def sample_video_request():
    """Sample video generation request."""
    return {
        "brand_name": "Careerfied",
        "product_description": "AI-powered resume builder",
        "target_audience": "Job seekers",
        "key_benefits": ["ATS-optimized", "Industry templates", "Real-time feedback"],
        "cta": "Get Started Free",
        "style": "ugc",
        "aspect_ratio": "9:16",
        "avatar_style": "casual",
        "include_captions": True,
        "include_music": True,
    }


@pytest.fixture
def sample_competitor_request():
    """Sample competitor intel request."""
    return {
        "brand_name": "Careerfied",
        "industry": "career",
        "competitor_names": ["Resume.io", "Zety", "Indeed"],
    }


@pytest.fixture
def sample_proof_pack_request():
    """Sample proof pack request."""
    return {
        "ad_id": "test_ad_001",
        "campaign_name": "Launch Campaign",
        "brand_name": "Careerfied",
        "headline": "Stop Getting Rejected by ATS",
        "primary_text": "Build resumes that get interviews with AI-powered optimization.",
        "cta": "Get Started",
        "claims": [
            {"claim": "Join 10,000+ users", "source_text": "User surveys", "risk_level": "low"},
        ],
    }


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    with patch("anthropic.Anthropic") as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Mock message creation
        message_response = MagicMock()
        message_response.content = [MagicMock(text='{"brand_name": "Test", "tagline": "Test tagline"}')]
        client.messages.create.return_value = message_response
        
        yield client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx async client."""
    with patch("httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value.__aenter__.return_value = client
        
        # Mock successful response
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"results": []}
        client.get.return_value = response
        client.post.return_value = response
        
        yield client


# =============================================================================
# TEMP FILE FIXTURES
# =============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_jobs_dir(tmp_path):
    """Temporary jobs directory."""
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    return jobs_dir


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_output_files():
    """Clean up generated files after tests."""
    yield
    # Cleanup code runs after test
    output_dir = Path("./output")
    if output_dir.exists():
        for file in output_dir.glob("test_*"):
            try:
                file.unlink()
            except Exception:
                pass


# =============================================================================
# NEW FEATURE FIXTURES (Slices 16-23)
# =============================================================================

@pytest.fixture
def sample_hook_request():
    """Sample hook generation request."""
    return {
        "product_name": "Careerfied",
        "product_description": "AI-powered resume builder",
        "target_audience": "Job seekers",
        "pain_points": ["getting rejected", "ATS systems"],
        "benefits": ["land more interviews", "stand out"],
        "tone": "professional",
        "include_emojis": False,
        "num_hooks": 10,
    }


@pytest.fixture
def sample_landing_request():
    """Sample landing page analysis request."""
    return {
        "landing_page_url": "https://careerfied.ai",
        "ad_headline": "Stop Getting Rejected",
        "ad_primary_text": "Build ATS-optimized resumes",
        "ad_cta": "Get Started Free",
    }


@pytest.fixture
def sample_budget_request():
    """Sample budget simulation request."""
    return {
        "industry": "saas",
        "goal": "leads",
        "product_price": 99.0,
        "target_monthly_conversions": 50,
        "target_cpa": None,
    }


@pytest.fixture
def sample_platform_request():
    """Sample platform recommendation request."""
    return {
        "product_type": "b2b_saas",
        "audience_type": "founders",
        "monthly_budget": 1000,
        "product_price": 99,
        "is_visual": True,
    }


@pytest.fixture
def sample_abtest_request():
    """Sample A/B test planning request."""
    return {
        "variants": [
            {"headline": "Stop Getting Rejected", "primary_text": "Build resumes", "cta": "Get Started"},
            {"headline": "Land More Interviews", "primary_text": "AI-powered", "cta": "Try Free"},
        ],
        "baseline_ctr": 1.0,
        "baseline_cvr": 2.0,
        "daily_budget": 50,
        "confidence_level": 0.95,
        "minimum_lift": 0.20,
    }


@pytest.fixture
def sample_audience_request():
    """Sample audience targeting request."""
    return {
        "product_name": "Careerfied",
        "product_description": "AI-powered resume builder",
        "product_type": "saas",
        "target_persona": "Job seekers",
        "price_point": 29,
        "existing_customers": False,
        "website_traffic": False,
    }


@pytest.fixture
def sample_iteration_request():
    """Sample ad iteration request."""
    return {
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
    }


@pytest.fixture
def sample_social_proof_request():
    """Sample social proof collection request."""
    return {
        "brand_name": "Careerfied",
        "brand_url": "https://careerfied.ai",
        "product_description": "AI-powered resume builder",
        "existing_testimonials": [
            "This helped me land my dream job!",
            "Got 3 interviews in the first week",
        ],
        "user_count": 1500,
        "rating": 4.8,
        "notable_customers": ["Google", "Meta", "Microsoft"],
    }


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "contract: Contract tests")
    config.addinivalue_line("markers", "component: Component tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "api: API tests")
