# tests/e2e/test_complete_flows.py
"""End-to-end tests for complete user flows."""

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


class TestAdCreationFlow:
    """Tests for complete ad creation flow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_ad_analysis_flow(self, client):
        """
        Test complete flow:
        1. Predict performance
        2. Analyze attention
        3. Generate proof pack
        4. Check fatigue readiness
        """
        ad_data = {
            "headline": "Stop Getting Rejected by ATS",
            "primary_text": "Build resumes that get interviews with AI-powered optimization. Join 10,000+ job seekers who landed their dream jobs.",
            "cta": "Get Started Free",
        }
        
        # Step 1: Predict performance
        predict_response = await client.post("/predict", json=ad_data)
        assert predict_response.status_code == 200
        predict_data = predict_response.json()
        assert predict_data["score"] > 0
        print(f"✓ Performance Score: {predict_data['score']}/100")
        
        # Step 2: Analyze attention
        attention_response = await client.post(
            "/attention/analyze",
            json={
                "image_url": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600",
                "headline": ad_data["headline"],
                "cta": ad_data["cta"],
            },
        )
        assert attention_response.status_code == 200
        attention_data = attention_response.json()
        assert attention_data["score"] > 0
        print(f"✓ Attention Score: {attention_data['score']}/100")
        
        # Step 3: Generate proof pack
        proof_response = await client.post(
            "/proof/generate",
            json={
                "ad_id": "flow_test_001",
                "campaign_name": "E2E Test Campaign",
                "brand_name": "Careerfied",
                "headline": ad_data["headline"],
                "primary_text": ad_data["primary_text"],
                "cta": ad_data["cta"],
                "claims": [
                    {"claim": "Join 10,000+ job seekers", "source_text": "User surveys", "risk_level": "low"},
                ],
            },
        )
        assert proof_response.status_code == 200
        proof_data = proof_response.json()
        assert "pack_id" in proof_data
        print(f"✓ Proof Pack: {proof_data['compliance'].upper()}, Safety: {proof_data['safety_score']}/100")
        
        # Step 4: Check fatigue readiness (new ad = fresh)
        fatigue_response = await client.post(
            "/fatigue/predict",
            json={
                "ad_id": "flow_test_001",
                "days_running": 1,
                "frequency": 1.0,
                "reach": 1000,
                "audience_size": 100000,
                "industry": "career",
            },
        )
        assert fatigue_response.status_code == 200
        fatigue_data = fatigue_response.json()
        assert fatigue_data["level"] in ["fresh", "healthy"]
        print(f"✓ Fatigue: {fatigue_data['level'].upper()}, Score: {fatigue_data['fatigue_score']}/100")
        
        print("\n✅ Complete ad analysis flow passed!")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_video_generation_flow(self, client):
        """
        Test complete video generation flow:
        1. Get available styles
        2. Get available avatars
        3. Generate video
        4. Verify output
        """
        # Step 1: Get styles
        styles_response = await client.get("/video/styles")
        assert styles_response.status_code == 200
        styles = styles_response.json()["styles"]
        print(f"✓ Available styles: {[s['id'] for s in styles]}")
        
        # Step 2: Get avatars
        avatars_response = await client.get("/video/avatars")
        assert avatars_response.status_code == 200
        avatars = avatars_response.json()["avatars"]
        print(f"✓ Available avatars: {[a['name'] for a in avatars]}")
        
        # Step 3: Generate video
        video_response = await client.post(
            "/video/generate",
            json={
                "brand_name": "Careerfied",
                "product_description": "AI-powered resume builder that helps job seekers pass ATS screening",
                "target_audience": "Job seekers frustrated with rejections",
                "key_benefits": [
                    "ATS-optimized resumes",
                    "Industry-specific templates",
                    "Real-time feedback",
                ],
                "cta": "Get Started Free",
                "style": "ugc",
                "aspect_ratio": "9:16",
                "avatar_style": "casual",
                "include_captions": True,
                "include_music": True,
            },
        )
        assert video_response.status_code == 200
        video_data = video_response.json()
        
        # Step 4: Verify output
        assert "video_id" in video_data
        assert video_data["status"] == "complete"
        assert video_data["script"]["hook"]
        assert len(video_data["script"]["scenes"]) > 0
        assert video_data["predictions"]["engagement_score"] > 0
        
        print(f"✓ Video ID: {video_data['video_id']}")
        print(f"✓ Duration: {video_data['duration_seconds']}s")
        print(f"✓ Hook: \"{video_data['script']['hook'][:50]}...\"")
        print(f"✓ Engagement Score: {video_data['predictions']['engagement_score']}/100")
        print(f"✓ Hook Strength: {video_data['predictions']['hook_strength']}/100")
        
        print("\n✅ Video generation flow passed!")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_competitor_analysis_flow(self, client):
        """
        Test complete competitor analysis flow:
        1. Analyze competitors
        2. Extract insights
        3. Get recommendations
        """
        # Step 1: Analyze competitors
        intel_response = await client.post(
            "/intel/analyze",
            json={
                "brand_name": "Careerfied",
                "industry": "career",
                "competitor_names": ["Resume.io", "Zety", "Indeed"],
            },
        )
        assert intel_response.status_code == 200
        intel_data = intel_response.json()
        
        # Step 2: Verify competitor data
        assert len(intel_data["competitors"]) > 0
        for comp in intel_data["competitors"]:
            assert comp["name"]
            assert comp["ads"] >= 0
            assert comp["threat"] in ["low", "medium", "high", "critical"]
        
        print(f"✓ Competitors analyzed: {len(intel_data['competitors'])}")
        for comp in intel_data["competitors"]:
            print(f"  - {comp['name']}: {comp['ads']} ads, {comp['threat'].upper()} threat")
        
        # Step 3: Verify insights
        assert len(intel_data["insights"]) > 0
        print(f"✓ Insights generated: {len(intel_data['insights'])}")
        for insight in intel_data["insights"]:
            print(f"  - {insight['title']}")
        
        # Step 4: Verify recommendations
        assert len(intel_data["recommendations"]) > 0
        print(f"✓ Recommendations: {len(intel_data['recommendations'])}")
        
        print("\n✅ Competitor analysis flow passed!")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_export_all_formats_flow(self, client):
        """
        Test complete export flow:
        1. Get available formats
        2. Export all formats
        3. Verify outputs
        """
        # Step 1: Get formats
        formats_response = await client.get("/export/formats")
        assert formats_response.status_code == 200
        formats = formats_response.json()["formats"]
        print(f"✓ Available formats: {len(formats)}")
        for f in formats:
            print(f"  - {f['id']}: {f['name']} ({f['width']}x{f['height']})")
        
        # Step 2: Export demo
        export_response = await client.post("/export/demo")
        assert export_response.status_code == 200
        export_data = export_response.json()
        
        # Step 3: Verify outputs
        assert export_data["exported"] > 0
        print(f"✓ Formats exported: {export_data['exported']}")
        
        print("\n✅ Export flow passed!")


class TestSentimentMonitoringFlow:
    """Tests for sentiment monitoring flow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_sentiment_scenarios(self, client):
        """
        Test sentiment monitoring across scenarios:
        1. Normal sentiment
        2. Crisis sentiment (should trigger pause)
        3. Positive sentiment
        """
        scenarios = ["normal", "crisis", "positive"]
        
        for scenario in scenarios:
            response = await client.post(f"/sentiment/demo/{scenario}")
            assert response.status_code == 200
            data = response.json()
            
            print(f"✓ Scenario: {scenario.upper()}")
            print(f"  - Health: {data['health']}")
            print(f"  - Auto-pause: {data['auto_pause']}")
            
            # Crisis should trigger auto-pause
            if scenario == "crisis":
                assert data["auto_pause"] is True
            elif scenario == "positive":
                assert data["auto_pause"] is False
        
        print("\n✅ Sentiment monitoring flow passed!")


class TestFatigueLifecycleFlow:
    """Tests for ad fatigue lifecycle."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_fatigue_progression(self, client):
        """
        Test fatigue progression over ad lifecycle:
        1. Fresh ad
        2. Healthy ad
        3. Moderate fatigue
        4. High fatigue
        5. Critical fatigue
        """
        scenarios = ["fresh", "healthy", "moderate", "high", "critical"]
        
        print("Ad Fatigue Lifecycle:")
        print("-" * 50)
        
        for scenario in scenarios:
            response = await client.post(f"/fatigue/demo/{scenario}")
            assert response.status_code == 200
            data = response.json()
            
            print(f"Stage: {scenario.upper()}")
            print(f"  - Fatigue Score: {data['fatigue_score']}/100")
            print(f"  - Level: {data['summary'][:60]}...")
            print()
        
        print("✅ Fatigue lifecycle flow passed!")


class TestAPIConsistency:
    """Tests for API consistency and contracts."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_all_demo_endpoints(self, client):
        """Test that all demo endpoints work."""
        demo_endpoints = [
            ("/predict/demo", "POST"),
            ("/attention/demo", "POST"),
            ("/export/demo", "POST"),
            ("/intel/demo/career", "POST"),
            ("/video/demo/ugc", "POST"),
            ("/fatigue/demo/moderate", "POST"),
            ("/proof/demo", "POST"),
            ("/sentiment/demo/normal", "POST"),
            ("/meta/demo", "POST"),
        ]
        
        print("Testing all demo endpoints:")
        print("-" * 50)
        
        for endpoint, method in demo_endpoints:
            if method == "POST":
                response = await client.post(endpoint)
            else:
                response = await client.get(endpoint)
            
            assert response.status_code == 200, f"Failed: {endpoint}"
            data = response.json()
            assert data.get("demo") is True, f"Missing demo flag: {endpoint}"
            
            print(f"✓ {endpoint}")
        
        print("\n✅ All demo endpoints passed!")
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_all_list_endpoints(self, client):
        """Test that all list/catalog endpoints work."""
        list_endpoints = [
            "/export/formats",
            "/video/styles",
            "/video/avatars",
            "/video/music",
            "/jobs",
        ]
        
        print("Testing all list endpoints:")
        print("-" * 50)
        
        for endpoint in list_endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 200, f"Failed: {endpoint}"
            print(f"✓ {endpoint}")
        
        print("\n✅ All list endpoints passed!")
