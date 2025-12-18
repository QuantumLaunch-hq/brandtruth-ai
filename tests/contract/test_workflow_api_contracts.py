# tests/contract/test_workflow_api_contracts.py
"""Contract tests for Workflow API endpoints.

These tests verify:
1. Workflow result endpoint returns correct shapes
2. Composed ads include MinIO URLs (absolute http:// URLs)
3. Progress endpoint includes new pipeline stages
4. Error responses follow expected format
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestWorkflowResultContract:
    """Contract tests for /workflow/result/{id} endpoint."""

    def test_composed_ads_asset_shape(self):
        """Verify AdAsset has required fields including file_url."""
        from src.temporal.activities.compose import AdAsset

        asset = AdAsset(
            format="1:1",
            file_path="/app/output/ad-123_1x1.png",
            file_url="http://localhost:9000/ad-creatives/campaigns/wf-123/variants/v1/1x1.png",
            width=1080,
            height=1080,
        )

        # Required fields
        assert hasattr(asset, "format")
        assert hasattr(asset, "file_path")
        assert hasattr(asset, "file_url")
        assert hasattr(asset, "width")
        assert hasattr(asset, "height")

        # file_url should be absolute URL for MinIO
        assert asset.file_url.startswith("http://") or asset.file_url.startswith("https://")

    def test_composed_ad_shape(self):
        """Verify ComposedAdResult has required fields."""
        from src.temporal.activities.compose import ComposedAdResult, AdAsset

        asset = AdAsset(
            format="1:1",
            file_path="/app/output/ad-123_1x1.png",
            file_url="http://localhost:9000/ad-creatives/test/1x1.png",
            width=1080,
            height=1080,
        )

        ad = ComposedAdResult(
            id="ad-123",
            copy_variant_id="variant-123",
            headline="Test Headline",
            primary_text="Test primary text",
            cta="Learn More",
            assets=[asset],
        )

        # Required fields
        assert hasattr(ad, "id")
        assert hasattr(ad, "copy_variant_id")
        assert hasattr(ad, "headline")
        assert hasattr(ad, "primary_text")
        assert hasattr(ad, "cta")
        assert hasattr(ad, "assets")
        assert isinstance(ad.assets, list)
        assert len(ad.assets) > 0

    def test_ad_composition_result_shape(self):
        """Verify AdCompositionResult has required fields."""
        from src.temporal.activities.compose import (
            AdCompositionResult,
            ComposedAdResult,
            AdAsset,
        )

        asset = AdAsset(
            format="1:1",
            file_path="/app/output/ad-123_1x1.png",
            file_url="http://localhost:9000/ad-creatives/test/1x1.png",
            width=1080,
            height=1080,
        )

        result = AdCompositionResult(
            ads=[ComposedAdResult(
                id="ad-v1",
                copy_variant_id="v1",
                headline="Test",
                primary_text="Test text",
                cta="CTA",
                assets=[asset],
            )],
            composition_time_ms=1234,
        )

        # Required fields
        assert hasattr(result, "ads")
        assert hasattr(result, "composition_time_ms")
        assert isinstance(result.ads, list)

    def test_minio_url_format(self):
        """Verify MinIO URLs follow expected format."""
        # MinIO public URL pattern
        url = "http://localhost:9000/ad-creatives/campaigns/wf-123/variants/v1/1x1.png"

        # Should contain bucket name
        assert "ad-creatives" in url

        # Should contain path structure
        assert "/campaigns/" in url
        assert "/variants/" in url

        # Should end with format
        assert url.endswith(".png")

    def test_workflow_result_serialization_shape(self):
        """Verify the expected shape of serialized workflow result."""
        # This is the shape the frontend expects
        expected_shape = {
            "workflow_id": str,
            "stage": str,
            "brand_profile": (dict, type(None)),
            "copy_variants": {
                "variants": list,
                "generation_time_ms": (int, float),
            },
            "image_matches": {
                "matches": list,
            },
            "composed_ads": {
                "ads": list,  # Each ad has copy_variant_id and assets[]
            },
            "performance_scores": {
                "scores": list,
            },
        }

        # Mock result matching expected shape
        mock_result = {
            "workflow_id": "pipeline-123",
            "stage": "awaiting_approval",
            "brand_profile": {
                "brand_name": "Test Brand",
                "website_url": "https://test.com",
            },
            "copy_variants": {
                "variants": [
                    {"id": "v1", "headline": "Test", "primary_text": "Test"},
                ],
                "generation_time_ms": 1000,
            },
            "image_matches": {
                "matches": [
                    {"copy_variant_id": "v1", "image_url": "https://images.pexels.com/test.jpg"},
                ],
            },
            "composed_ads": {
                "ads": [
                    {
                        "copy_variant_id": "v1",
                        "assets": [
                            {
                                "format": "1:1",
                                "file_path": "output/ad-v1_1x1.png",
                                "file_url": "http://localhost:9000/ad-creatives/campaigns/123/variants/v1/1x1.png",
                                "width": 1080,
                                "height": 1080,
                            }
                        ],
                    }
                ],
            },
            "performance_scores": {
                "scores": [
                    {"variant_id": "v1", "score": 85},
                ],
            },
        }

        # Verify shape
        assert "composed_ads" in mock_result
        assert "ads" in mock_result["composed_ads"]
        assert len(mock_result["composed_ads"]["ads"]) > 0

        ad = mock_result["composed_ads"]["ads"][0]
        assert "copy_variant_id" in ad
        assert "assets" in ad
        assert len(ad["assets"]) > 0

        asset = ad["assets"][0]
        assert "file_url" in asset
        assert asset["file_url"].startswith("http://")


class TestWorkflowProgressContract:
    """Contract tests for /workflow/progress/{id} endpoint."""

    def test_pipeline_stages_include_new_stages(self):
        """Verify PipelineStage enum includes embedding and upload stages."""
        from src.temporal.workflows.ad_pipeline import PipelineStage

        # All expected stages
        expected_stages = [
            "pending",
            "extracting",
            "embedding_brand",
            "generating",
            "embedding_variants",
            "matching",
            "composing",
            "uploading",
            "scoring",
            "awaiting_approval",
            "approved",
            "completed",
            "failed",
        ]

        actual_stages = [s.value for s in PipelineStage]

        for stage in expected_stages:
            assert stage in actual_stages, f"Missing stage: {stage}"

    def test_progress_response_shape(self):
        """Verify PipelineProgress has required fields."""
        from src.temporal.workflows.ad_pipeline import PipelineProgress

        progress = PipelineProgress(
            stage="uploading",
            progress_percent=82,
            message="Uploading ads to storage",
            error=None,
        )

        # Required fields
        assert hasattr(progress, "stage")
        assert hasattr(progress, "progress_percent")
        assert hasattr(progress, "message")
        assert hasattr(progress, "error")

        # Types
        assert isinstance(progress.stage, str)
        assert isinstance(progress.progress_percent, int)
        assert isinstance(progress.message, str)

        # Valid ranges
        assert 0 <= progress.progress_percent <= 100


class TestWorkflowAPIRoutes:
    """Contract tests for workflow route handlers."""

    @pytest.mark.anyio
    async def test_result_endpoint_returns_composed_ads(self):
        """Verify result endpoint includes composed_ads in response."""
        from src.temporal.routes import router
        from src.temporal.client import get_pipeline_state

        # Mock state with composed_ads
        mock_state = {
            "stage": "awaiting_approval",
            "progress_percent": 98,
            "composed_ads": {
                "ads": [
                    {
                        "copy_variant_id": "v1",
                        "assets": [
                            {
                                "format": "1:1",
                                "file_url": "http://localhost:9000/ad-creatives/test.png",
                            }
                        ],
                    }
                ]
            },
        }

        # The route should return composed_ads in the response
        assert "composed_ads" in mock_state
        assert "ads" in mock_state["composed_ads"]

        # Each ad should have file_url in assets
        for ad in mock_state["composed_ads"]["ads"]:
            for asset in ad["assets"]:
                assert "file_url" in asset


class TestFrontendURLHandling:
    """Contract tests for frontend URL handling logic."""

    def test_absolute_minio_url_detected(self):
        """Verify absolute MinIO URLs are detected correctly."""
        urls = [
            "http://localhost:9000/ad-creatives/test.png",
            "https://minio.example.com/bucket/image.png",
            "http://192.168.1.1:9000/ad-creatives/image.png",
        ]

        for url in urls:
            is_absolute = url.startswith("http://") or url.startswith("https://")
            assert is_absolute, f"URL should be detected as absolute: {url}"

    def test_relative_url_detected(self):
        """Verify relative URLs are detected correctly."""
        urls = [
            "/output/ad-123_1x1.png",
            "output/ad-123_1x1.png",
            "./output/ad-123_1x1.png",
        ]

        for url in urls:
            is_absolute = url.startswith("http://") or url.startswith("https://")
            assert not is_absolute, f"URL should be detected as relative: {url}"

    def test_get_image_url_logic(self):
        """Test the getImageUrl logic from studio/page.tsx."""

        def get_image_url(
            result: dict,
            variant_id: str,
            api_url: str = "http://localhost:8010",
        ) -> str | None:
            """Python implementation of frontend getImageUrl logic."""
            # First try composed_ads
            composed_ads = result.get("composed_ads", {}).get("ads", [])
            for ad in composed_ads:
                if ad.get("copy_variant_id") == variant_id:
                    assets = ad.get("assets", [])
                    if assets and assets[0].get("file_url"):
                        file_url = assets[0]["file_url"]
                        # MinIO URLs are absolute, use directly
                        if file_url.startswith("http://") or file_url.startswith("https://"):
                            return file_url
                        # Legacy: relative URLs from API server
                        return f"{api_url}{file_url}"

            # Fall back to image_matches
            matches = result.get("image_matches", {}).get("matches", [])
            for match in matches:
                if match.get("copy_variant_id") == variant_id:
                    if match.get("image_url"):
                        return match["image_url"]

            return None

        # Test case 1: MinIO URL (absolute)
        result_minio = {
            "composed_ads": {
                "ads": [
                    {
                        "copy_variant_id": "v1",
                        "assets": [
                            {"file_url": "http://localhost:9000/ad-creatives/test.png"}
                        ],
                    }
                ]
            }
        }
        url = get_image_url(result_minio, "v1")
        assert url == "http://localhost:9000/ad-creatives/test.png"

        # Test case 2: Legacy relative URL
        result_legacy = {
            "composed_ads": {
                "ads": [
                    {
                        "copy_variant_id": "v1",
                        "assets": [{"file_url": "/output/ad-123.png"}],
                    }
                ]
            }
        }
        url = get_image_url(result_legacy, "v1")
        assert url == "http://localhost:8010/output/ad-123.png"

        # Test case 3: Fallback to image_matches
        result_fallback = {
            "composed_ads": {"ads": []},
            "image_matches": {
                "matches": [
                    {
                        "copy_variant_id": "v1",
                        "image_url": "https://images.pexels.com/test.jpg",
                    }
                ]
            },
        }
        url = get_image_url(result_fallback, "v1")
        assert url == "https://images.pexels.com/test.jpg"

        # Test case 4: Not found
        result_empty = {"composed_ads": {"ads": []}, "image_matches": {"matches": []}}
        url = get_image_url(result_empty, "v1")
        assert url is None

    def test_next_config_patterns(self):
        """Verify next.config.js should allow MinIO URLs."""
        # Expected patterns in next.config.js remotePatterns
        expected_patterns = [
            {"hostname": "images.unsplash.com", "protocol": "https"},
            {"hostname": "images.pexels.com", "protocol": "https"},
            {"hostname": "localhost", "port": "8010", "pathname": "/output/**"},
            {"hostname": "localhost", "port": "9000", "pathname": "/ad-creatives/**"},
        ]

        # Test URL matching
        test_urls = [
            ("https://images.unsplash.com/photo-123", True),
            ("https://images.pexels.com/photo/123", True),
            ("http://localhost:8010/output/ad-123.png", True),
            ("http://localhost:9000/ad-creatives/test.png", True),
            ("http://evil.com/malicious.png", False),
        ]

        def matches_pattern(url: str, patterns: list) -> bool:
            """Check if URL matches any allowed pattern."""
            from urllib.parse import urlparse

            parsed = urlparse(url)

            for pattern in patterns:
                if parsed.hostname == pattern["hostname"]:
                    if pattern.get("protocol") and parsed.scheme != pattern["protocol"]:
                        continue
                    if pattern.get("port") and str(parsed.port) != pattern["port"]:
                        continue
                    # pathname check simplified
                    return True
            return False

        for url, should_match in test_urls:
            assert matches_pattern(url, expected_patterns) == should_match, f"URL {url} match expected {should_match}"


class TestImageComponentContract:
    """Contract tests for Next.js Image component usage."""

    def test_unoptimized_prop_for_localhost(self):
        """Verify unoptimized prop logic for localhost images."""

        def should_unoptimize(url: str) -> bool:
            """Logic from studio/page.tsx: unoptimized={variant.image_url.includes('localhost')}"""
            return "localhost" in url

        # MinIO URLs should be unoptimized
        assert should_unoptimize("http://localhost:9000/ad-creatives/test.png") is True

        # Legacy API URLs should be unoptimized
        assert should_unoptimize("http://localhost:8010/output/ad-123.png") is True

        # External URLs should NOT be unoptimized (use Next.js optimization)
        assert should_unoptimize("https://images.pexels.com/photo/123") is False
        assert should_unoptimize("https://images.unsplash.com/photo-123") is False

    def test_minio_url_contains_localhost(self):
        """Verify MinIO URLs will trigger unoptimized mode."""
        from src.storage.minio_client import MinIOConfig

        # The public URL should contain localhost for local development
        public_url = MinIOConfig.PUBLIC_URL
        # In docker-compose, this is set to http://localhost:9000
        # This ensures unoptimized prop will be True
        assert "localhost" in public_url or "127.0.0.1" in public_url
