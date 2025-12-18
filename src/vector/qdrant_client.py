# src/vector/qdrant_client.py
"""Qdrant vector database client for semantic search.

This module provides:
- Async Qdrant client with connection management
- Collection creation and management
- Semantic search queries with filtering
- Batch upsert operations

Collections:
- brands: Brand profile embeddings for similarity search
- ad_creatives: Ad copy embeddings for performance prediction

Usage:
    client = await get_qdrant_client()
    await client.ensure_collections()

    # Upsert brand embedding
    await client.upsert_brand(brand_profile, embedding_vector)

    # Search similar brands
    results = await client.search_similar_brands(query_vector, limit=10)
"""

import os
from typing import Optional, Any
from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    PayloadSchemaType,
)

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QdrantConfig:
    """Qdrant connection configuration from environment variables."""

    URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    GRPC_PORT: int = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
    API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    TIMEOUT: int = 30

    # Collection names
    COLLECTION_BRANDS: str = "brands"
    COLLECTION_AD_CREATIVES: str = "ad_creatives"

    # Embedding dimensions (OpenAI text-embedding-3-small)
    EMBEDDING_DIM: int = 1536


class QdrantClient:
    """Async Qdrant client for vector operations.

    Provides high-level operations for managing brand and ad embeddings
    with semantic search capabilities.
    """

    _instance: Optional['QdrantClient'] = None

    def __init__(self):
        self.config = QdrantConfig()
        self._client: Optional[AsyncQdrantClient] = None
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> 'QdrantClient':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """Initialize the async Qdrant client."""
        if self._initialized:
            return

        try:
            self._client = AsyncQdrantClient(
                url=self.config.URL,
                api_key=self.config.API_KEY,
                port=6333,
                grpc_port=self.config.GRPC_PORT,
                prefer_grpc=True,
                timeout=self.config.TIMEOUT,
            )

            # Verify connection
            collections = await self._client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.info(f"Connected to Qdrant - collections: {collection_names}")
            self._initialized = True

        except Exception as e:
            logger.warning(f"Qdrant not available: {e}")
            # Don't fail - Qdrant is optional for local dev

    @property
    def client(self) -> AsyncQdrantClient:
        """Get the underlying async client."""
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized - call get_instance() first")
        return self._client

    async def ensure_collections(self):
        """Create collections if they don't exist.

        Creates:
        - brands: Brand profile embeddings with metadata filtering
        - ad_creatives: Ad copy embeddings with performance data
        """
        if self._client is None:
            logger.warning("Qdrant client not initialized, skipping collection creation")
            return

        # Get existing collections
        collections = await self._client.get_collections()
        existing = {c.name for c in collections.collections}

        # Create brands collection
        if self.config.COLLECTION_BRANDS not in existing:
            await self._client.create_collection(
                collection_name=self.config.COLLECTION_BRANDS,
                vectors_config=VectorParams(
                    size=self.config.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

            # Create payload indexes for filtering
            for field_name, field_type in [
                ("brand_name", PayloadSchemaType.KEYWORD),
                ("industry", PayloadSchemaType.KEYWORD),
                ("confidence_score", PayloadSchemaType.FLOAT),
            ]:
                await self._client.create_payload_index(
                    collection_name=self.config.COLLECTION_BRANDS,
                    field_name=field_name,
                    field_schema=field_type,
                )

            logger.info(f"Created collection: {self.config.COLLECTION_BRANDS}")

        # Create ad_creatives collection
        if self.config.COLLECTION_AD_CREATIVES not in existing:
            await self._client.create_collection(
                collection_name=self.config.COLLECTION_AD_CREATIVES,
                vectors_config=VectorParams(
                    size=self.config.EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

            # Create payload indexes for filtering
            for field_name, field_type in [
                ("campaign_id", PayloadSchemaType.KEYWORD),
                ("copy_variant_id", PayloadSchemaType.KEYWORD),
                ("angle", PayloadSchemaType.KEYWORD),
                ("emotion", PayloadSchemaType.KEYWORD),
                ("platform", PayloadSchemaType.KEYWORD),
                ("performance_score", PayloadSchemaType.FLOAT),
                ("is_approved", PayloadSchemaType.BOOL),
            ]:
                await self._client.create_payload_index(
                    collection_name=self.config.COLLECTION_AD_CREATIVES,
                    field_name=field_name,
                    field_schema=field_type,
                )

            logger.info(f"Created collection: {self.config.COLLECTION_AD_CREATIVES}")

    async def upsert_brand(
        self,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> bool:
        """Upsert a brand embedding.

        Args:
            point_id: Unique identifier (e.g., "brand_{campaign_id}")
            vector: Embedding vector (1536 dimensions)
            payload: Brand metadata (brand_name, industry, etc.)

        Returns:
            True if successful
        """
        if self._client is None:
            logger.warning("Qdrant not available, skipping brand upsert")
            return False

        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload,
        )

        result = await self._client.upsert(
            collection_name=self.config.COLLECTION_BRANDS,
            points=[point],
            wait=False,
        )

        logger.info(f"Upserted brand: {point_id}")
        return True

    async def upsert_ad_creative(
        self,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> bool:
        """Upsert an ad creative embedding.

        Args:
            point_id: Unique identifier (e.g., "variant_{variant_id}")
            vector: Embedding vector (1536 dimensions)
            payload: Ad metadata (headline, angle, emotion, score, etc.)

        Returns:
            True if successful
        """
        if self._client is None:
            logger.warning("Qdrant not available, skipping ad creative upsert")
            return False

        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload,
        )

        result = await self._client.upsert(
            collection_name=self.config.COLLECTION_AD_CREATIVES,
            points=[point],
            wait=False,
        )

        logger.info(f"Upserted ad creative: {point_id}")
        return True

    async def batch_upsert(
        self,
        collection_name: str,
        points: list[PointStruct],
        batch_size: int = 100,
    ) -> bool:
        """Batch upsert points for efficiency.

        Args:
            collection_name: Target collection
            points: List of PointStruct to upsert
            batch_size: Number of points per batch

        Returns:
            True if successful
        """
        if self._client is None:
            logger.warning("Qdrant not available, skipping batch upsert")
            return False

        total = len(points)
        for i in range(0, total, batch_size):
            batch = points[i : i + batch_size]
            await self._client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=False,
            )
            logger.debug(f"Upserted batch {i // batch_size + 1}/{(total - 1) // batch_size + 1}")

        logger.info(f"Batch upserted {total} points to {collection_name}")
        return True

    async def search_similar_brands(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_confidence: float = 0.7,
        exclude_brand_name: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Find brands similar to the query vector.

        Args:
            query_vector: Query embedding
            limit: Number of results
            min_confidence: Minimum extraction confidence score
            exclude_brand_name: Brand to exclude from results

        Returns:
            List of similar brands with scores
        """
        if self._client is None:
            logger.warning("Qdrant not available, returning empty results")
            return []

        # Build filter
        must_conditions = [
            FieldCondition(
                key="confidence_score",
                range=Range(gte=min_confidence),
            ),
        ]

        must_not = []
        if exclude_brand_name:
            must_not.append(
                FieldCondition(
                    key="brand_name",
                    match=MatchValue(value=exclude_brand_name),
                )
            )

        filters = Filter(must=must_conditions, must_not=must_not if must_not else None)

        results = await self._client.search(
            collection_name=self.config.COLLECTION_BRANDS,
            query_vector=query_vector,
            query_filter=filters,
            limit=limit,
            score_threshold=0.6,
            with_payload=True,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    async def search_similar_ads(
        self,
        query_vector: list[float],
        limit: int = 10,
        angle: Optional[str] = None,
        min_performance: float = 0.0,
        only_approved: bool = False,
    ) -> list[dict[str, Any]]:
        """Find ad creatives similar to the query vector.

        Args:
            query_vector: Query embedding
            limit: Number of results
            angle: Filter by ad angle (pain, benefit, etc.)
            min_performance: Minimum performance score
            only_approved: Only return approved ads

        Returns:
            List of similar ads with scores
        """
        if self._client is None:
            logger.warning("Qdrant not available, returning empty results")
            return []

        # Build filter
        must_conditions = []

        if min_performance > 0:
            must_conditions.append(
                FieldCondition(
                    key="performance_score",
                    range=Range(gte=min_performance),
                )
            )

        if angle:
            must_conditions.append(
                FieldCondition(
                    key="angle",
                    match=MatchValue(value=angle),
                )
            )

        if only_approved:
            must_conditions.append(
                FieldCondition(
                    key="is_approved",
                    match=MatchValue(value=True),
                )
            )

        filters = Filter(must=must_conditions) if must_conditions else None

        results = await self._client.search(
            collection_name=self.config.COLLECTION_AD_CREATIVES,
            query_vector=query_vector,
            query_filter=filters,
            limit=limit,
            score_threshold=0.5,
            with_payload=True,
        )

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
            }
            for hit in results
        ]

    async def update_ad_performance(
        self,
        point_id: str,
        performance_score: float,
        is_approved: bool = False,
    ) -> bool:
        """Update performance data for an ad creative.

        Args:
            point_id: Point ID to update
            performance_score: New performance score
            is_approved: Approval status

        Returns:
            True if successful
        """
        if self._client is None:
            logger.warning("Qdrant not available, skipping performance update")
            return False

        await self._client.set_payload(
            collection_name=self.config.COLLECTION_AD_CREATIVES,
            payload={
                "performance_score": performance_score,
                "is_approved": is_approved,
            },
            points=[point_id],
        )

        logger.info(f"Updated performance for {point_id}: score={performance_score}")
        return True

    async def close(self):
        """Close the client connection."""
        if self._client:
            await self._client.close()
            logger.info("Closed Qdrant client")


# Singleton accessor
async def get_qdrant_client() -> QdrantClient:
    """Get the singleton Qdrant client instance.

    Returns:
        QdrantClient instance
    """
    return await QdrantClient.get_instance()
