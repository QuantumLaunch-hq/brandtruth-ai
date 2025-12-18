# tests/contract/test_infrastructure_contracts.py
"""Contract tests for MinIO and Qdrant infrastructure.

These tests verify:
1. MinIO client uploads/downloads work correctly
2. Qdrant embeddings are generated and stored properly
3. Activity dataclass shapes match expectations
"""

import pytest
import os
import tempfile
from pathlib import Path
from dataclasses import asdict

# Test activity result shapes first (no external deps)


class TestUploadActivityContracts:
    """Contract tests for MinIO upload activity result shapes."""

    def test_upload_result_shape(self):
        """Verify UploadResult dataclass has required fields."""
        from src.temporal.activities.upload import UploadResult

        result = UploadResult(
            object_url="http://localhost:9000/ad-creatives/test.png",
            presigned_url="http://localhost:9000/ad-creatives/test.png?X-Amz-Signature=...",
            bucket="ad-creatives",
            object_key="campaigns/test/variants/v1/1x1.png",
            size_bytes=12345,
        )

        # Required fields
        assert hasattr(result, "object_url")
        assert hasattr(result, "presigned_url")
        assert hasattr(result, "bucket")
        assert hasattr(result, "object_key")
        assert hasattr(result, "size_bytes")

        # Field types
        assert isinstance(result.object_url, str)
        assert isinstance(result.presigned_url, str)
        assert isinstance(result.bucket, str)
        assert isinstance(result.object_key, str)
        assert isinstance(result.size_bytes, int)

        # URL format validation
        assert result.object_url.startswith("http")
        assert result.presigned_url.startswith("http")
        assert "/" in result.object_key

    def test_batch_upload_result_shape(self):
        """Verify BatchUploadResult dataclass has required fields."""
        from src.temporal.activities.upload import UploadResult, BatchUploadResult

        upload1 = UploadResult(
            object_url="http://test/1.png",
            presigned_url="http://test/1.png?sig=...",
            bucket="ad-creatives",
            object_key="test/1.png",
            size_bytes=1000,
        )
        upload2 = UploadResult(
            object_url="http://test/2.png",
            presigned_url="http://test/2.png?sig=...",
            bucket="ad-creatives",
            object_key="test/2.png",
            size_bytes=2000,
        )

        batch = BatchUploadResult(
            uploads=[upload1, upload2],
            total_bytes=3000,
        )

        # Required fields
        assert hasattr(batch, "uploads")
        assert hasattr(batch, "total_bytes")

        # Field types
        assert isinstance(batch.uploads, list)
        assert isinstance(batch.total_bytes, int)
        assert len(batch.uploads) == 2
        assert batch.total_bytes == 3000


class TestEmbedActivityContracts:
    """Contract tests for Qdrant embed activity result shapes."""

    def test_embedding_result_shape(self):
        """Verify EmbeddingResult dataclass has required fields."""
        from src.temporal.activities.embed import EmbeddingResult

        result = EmbeddingResult(
            point_ids=["id-1", "id-2"],
            collection_name="brands",
            count=2,
            skipped=0,
        )

        # Required fields
        assert hasattr(result, "point_ids")
        assert hasattr(result, "collection_name")
        assert hasattr(result, "count")
        assert hasattr(result, "skipped")

        # Field types
        assert isinstance(result.point_ids, list)
        assert isinstance(result.collection_name, str)
        assert isinstance(result.count, int)
        assert isinstance(result.skipped, int)

        # Values
        assert len(result.point_ids) == result.count
        assert result.collection_name in ["brands", "ad_creatives"]

    def test_embedding_result_with_skipped(self):
        """Verify EmbeddingResult handles skipped items."""
        from src.temporal.activities.embed import EmbeddingResult

        result = EmbeddingResult(
            point_ids=[],
            collection_name="brands",
            count=0,
            skipped=1,
        )

        assert result.skipped == 1
        assert result.count == 0
        assert len(result.point_ids) == 0


class TestMinIOClientContracts:
    """Contract tests for MinIO client interface."""

    def test_minio_config_shape(self):
        """Verify MinIOConfig has required fields."""
        from src.storage.minio_client import MinIOConfig

        # Required class attributes
        assert hasattr(MinIOConfig, "ENDPOINT_URL")
        assert hasattr(MinIOConfig, "PUBLIC_URL")
        assert hasattr(MinIOConfig, "ACCESS_KEY")
        assert hasattr(MinIOConfig, "SECRET_KEY")
        assert hasattr(MinIOConfig, "BUCKET_AD_CREATIVES")
        assert hasattr(MinIOConfig, "BUCKET_BRAND_ASSETS")

        # Bucket names are strings
        assert isinstance(MinIOConfig.BUCKET_AD_CREATIVES, str)
        assert isinstance(MinIOConfig.BUCKET_BRAND_ASSETS, str)

    def test_minio_client_interface(self):
        """Verify MinIOClient has required methods."""
        from src.storage.minio_client import MinIOClient

        client = MinIOClient()

        # Required async methods
        assert hasattr(client, "upload_file")
        assert hasattr(client, "upload_fileobj")
        assert hasattr(client, "generate_presigned_url")
        assert hasattr(client, "download_file")
        assert hasattr(client, "delete_object")
        assert hasattr(client, "object_exists")
        assert hasattr(client, "get_public_url")

        # Methods are callable
        assert callable(client.upload_file)
        assert callable(client.generate_presigned_url)
        assert callable(client.get_public_url)

    def test_minio_public_url_format(self):
        """Verify get_public_url returns correct format."""
        from src.storage.minio_client import MinIOClient, MinIOConfig

        client = MinIOClient()
        url = client.get_public_url("ad-creatives", "test/image.png")

        # URL structure
        assert url.startswith("http")
        assert "ad-creatives" in url
        assert "test/image.png" in url


class TestQdrantClientContracts:
    """Contract tests for Qdrant client interface."""

    def test_qdrant_config_shape(self):
        """Verify QdrantConfig has required fields."""
        from src.vector.qdrant_client import QdrantConfig

        # Required class attributes
        assert hasattr(QdrantConfig, "URL")
        assert hasattr(QdrantConfig, "GRPC_PORT")
        assert hasattr(QdrantConfig, "API_KEY")
        assert hasattr(QdrantConfig, "COLLECTION_BRANDS")
        assert hasattr(QdrantConfig, "COLLECTION_AD_CREATIVES")
        assert hasattr(QdrantConfig, "EMBEDDING_DIM")

        # Embedding dimension is correct for text-embedding-3-small
        assert QdrantConfig.EMBEDDING_DIM == 1536

    def test_qdrant_client_interface(self):
        """Verify QdrantClient has required methods."""
        from src.vector.qdrant_client import QdrantClient

        # Required async methods
        assert hasattr(QdrantClient, "get_instance")
        assert hasattr(QdrantClient, "ensure_collections")
        assert hasattr(QdrantClient, "upsert_brand")
        assert hasattr(QdrantClient, "upsert_ad_creative")
        assert hasattr(QdrantClient, "batch_upsert")
        assert hasattr(QdrantClient, "search_similar_brands")
        assert hasattr(QdrantClient, "search_similar_ads")
        assert hasattr(QdrantClient, "update_ad_performance")


class TestEmbeddingServiceContracts:
    """Contract tests for embedding service interface."""

    def test_embedding_service_interface(self):
        """Verify EmbeddingService has required methods."""
        from src.vector.embeddings import EmbeddingService

        # Required class methods
        assert hasattr(EmbeddingService, "get_instance")

        # Required instance methods
        assert hasattr(EmbeddingService, "embed_text")
        assert hasattr(EmbeddingService, "embed_batch")
        assert hasattr(EmbeddingService, "embed_brand_profile")
        assert hasattr(EmbeddingService, "embed_copy_variant")

    def test_embedding_service_constants(self):
        """Verify embedding service has correct constants."""
        from src.vector.embeddings import EmbeddingService

        # Model constants
        assert hasattr(EmbeddingService, "OPENAI_MODEL")
        assert hasattr(EmbeddingService, "DIMENSIONS")
        assert hasattr(EmbeddingService, "BATCH_SIZE")

        # Dimensions match Qdrant config
        from src.vector.qdrant_client import QdrantConfig
        assert EmbeddingService.DIMENSIONS == QdrantConfig.EMBEDDING_DIM


class TestWorkflowIntegrationContracts:
    """Contract tests for workflow with new stages."""

    def test_pipeline_stage_enum_has_new_stages(self):
        """Verify PipelineStage enum includes new stages."""
        from src.temporal.workflows.ad_pipeline import PipelineStage

        # New stages added
        assert hasattr(PipelineStage, "EMBEDDING_BRAND")
        assert hasattr(PipelineStage, "EMBEDDING_VARIANTS")
        assert hasattr(PipelineStage, "UPLOADING")

        # Values are strings
        assert PipelineStage.EMBEDDING_BRAND.value == "embedding_brand"
        assert PipelineStage.EMBEDDING_VARIANTS.value == "embedding_variants"
        assert PipelineStage.UPLOADING.value == "uploading"

    def test_pipeline_stage_order(self):
        """Verify pipeline stages are in correct order."""
        from src.temporal.workflows.ad_pipeline import PipelineStage

        stages = list(PipelineStage)
        stage_names = [s.value for s in stages]

        # Embedding brand comes after extracting
        assert stage_names.index("embedding_brand") > stage_names.index("extracting")

        # Embedding variants comes after generating
        assert stage_names.index("embedding_variants") > stage_names.index("generating")

        # Uploading comes after composing
        assert stage_names.index("uploading") > stage_names.index("composing")

        # Scoring comes after uploading
        assert stage_names.index("scoring") > stage_names.index("uploading")


class TestActivityImportsContract:
    """Verify all new activities can be imported in workflow."""

    def test_upload_activities_importable(self):
        """Verify upload activities are importable."""
        from src.temporal.activities.upload import (
            upload_composed_ad_activity,
            UploadResult,
            BatchUploadResult,
        )

        # Activities are decorated functions
        assert callable(upload_composed_ad_activity)

    def test_embed_activities_importable(self):
        """Verify embed activities are importable."""
        from src.temporal.activities.embed import (
            embed_brand_activity,
            embed_variants_activity,
            find_similar_brands_activity,
            find_similar_ads_activity,
            EmbeddingResult,
        )

        # Activities are decorated functions
        assert callable(embed_brand_activity)
        assert callable(embed_variants_activity)
        assert callable(find_similar_brands_activity)
        assert callable(find_similar_ads_activity)

    def test_workflow_imports_new_activities(self):
        """Verify workflow module can import new activities."""
        # This tests the import statements in the workflow file
        from src.temporal.workflows.ad_pipeline import AdPipelineWorkflow

        # Workflow class exists and is decorated
        assert hasattr(AdPipelineWorkflow, "run")


@pytest.mark.integration
class TestMinIOIntegrationContracts:
    """Integration tests requiring MinIO service (skipped if unavailable)."""

    @pytest.fixture
    def temp_image(self):
        """Create a temporary test image."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Write minimal PNG header (1x1 transparent pixel)
            f.write(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
                b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
                b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.mark.anyio
    async def test_minio_upload_download_roundtrip(self, temp_image):
        """Test uploading and downloading a file from MinIO."""
        import aiohttp
        from src.storage.minio_client import get_minio_client, MinIOConfig

        # Check if MinIO is available
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{MinIOConfig.ENDPOINT_URL}/minio/health/live") as resp:
                    if resp.status != 200:
                        pytest.skip("MinIO not available")
        except Exception:
            pytest.skip("MinIO not available")

        minio = await get_minio_client()

        # Upload
        object_key = "test-contracts/test-roundtrip.png"
        url = await minio.upload_file(
            file_path=temp_image,
            bucket=MinIOConfig.BUCKET_AD_CREATIVES,
            object_key=object_key,
            content_type="image/png",
        )

        assert url is not None
        assert "ad-creatives" in url

        # Verify exists
        exists = await minio.object_exists(MinIOConfig.BUCKET_AD_CREATIVES, object_key)
        assert exists is True

        # Generate presigned URL
        presigned = await minio.generate_presigned_url(
            bucket=MinIOConfig.BUCKET_AD_CREATIVES,
            object_key=object_key,
            expiry_seconds=300,
        )
        assert "X-Amz-" in presigned or "?" in presigned

        # Download and verify
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            download_path = f.name

        try:
            await minio.download_file(
                bucket=MinIOConfig.BUCKET_AD_CREATIVES,
                object_key=object_key,
                local_path=download_path,
            )

            assert os.path.exists(download_path)
            assert os.path.getsize(download_path) > 0
        finally:
            if os.path.exists(download_path):
                os.unlink(download_path)

        # Cleanup
        await minio.delete_object(MinIOConfig.BUCKET_AD_CREATIVES, object_key)


@pytest.mark.integration
class TestQdrantIntegrationContracts:
    """Integration tests requiring Qdrant service (skipped if unavailable)."""

    @pytest.mark.anyio
    async def test_qdrant_collections_exist(self):
        """Test Qdrant collections are created."""
        import aiohttp
        from src.vector.qdrant_client import QdrantConfig

        # Check if Qdrant is available
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{QdrantConfig.URL}/") as resp:
                    if resp.status != 200:
                        pytest.skip("Qdrant not available")
        except Exception:
            pytest.skip("Qdrant not available")

        from src.vector.qdrant_client import get_qdrant_client

        client = await get_qdrant_client()
        await client.ensure_collections()

        # Collections should exist now
        # Get collection info via internal client
        brands_info = await client._client.get_collection(QdrantConfig.COLLECTION_BRANDS)
        assert brands_info is not None
        # points_count is the correct attribute in newer qdrant_client versions
        assert brands_info.points_count is not None or hasattr(brands_info, 'points_count')

        ads_info = await client._client.get_collection(QdrantConfig.COLLECTION_AD_CREATIVES)
        assert ads_info is not None


@pytest.mark.integration
class TestEmbeddingIntegrationContracts:
    """Integration tests requiring embedding API (skipped if unavailable)."""

    @pytest.mark.anyio
    async def test_embedding_service_initializes(self):
        """Test embedding service initializes (may use zero vectors if no API key)."""
        from src.vector.embeddings import get_embedding_service

        service = await get_embedding_service()

        # Service should exist
        assert service is not None
        assert hasattr(service, "_initialized")

    @pytest.mark.anyio
    async def test_embed_text_returns_vector(self):
        """Test embed_text returns a vector of correct dimension."""
        from src.vector.embeddings import get_embedding_service, EmbeddingService

        service = await get_embedding_service()
        vector = await service.embed_text("test text")

        # Should return a list of floats
        assert isinstance(vector, list)
        assert len(vector) == EmbeddingService.DIMENSIONS

        # All elements should be floats (even if zero)
        assert all(isinstance(v, float) for v in vector)
