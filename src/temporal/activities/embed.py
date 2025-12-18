# src/temporal/activities/embed.py
"""Embedding generation activities for Temporal workflow.

This activity handles generating embeddings for brands and ad variants:
- Brand profile embeddings for similarity search
- Copy variant embeddings for performance prediction
- Batch embedding for efficiency

Enterprise Patterns:
- Heartbeats for long-running batch operations
- Idempotency: checks if already embedded
- Graceful degradation when embedding service unavailable
"""

from dataclasses import dataclass
from typing import Optional
import json

from temporalio import activity
from temporalio.exceptions import ApplicationError

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    point_ids: list[str]
    collection_name: str
    count: int
    skipped: int  # Already existed


@activity.defn
async def embed_brand_activity(
    brand_profile_json: str,
    campaign_id: str,
) -> EmbeddingResult:
    """Generate and store brand profile embedding.

    This activity:
    1. Generates embedding for brand profile using OpenAI
    2. Upserts to Qdrant brands collection
    3. Returns point ID for reference

    Args:
        brand_profile_json: Serialized BrandProfile
        campaign_id: Campaign ID for reference

    Returns:
        EmbeddingResult with point IDs

    Raises:
        ApplicationError: On validation errors
    """
    from src.vector.qdrant_client import get_qdrant_client
    from src.vector.embeddings import get_embedding_service

    activity.heartbeat({"stage": "parsing", "campaign_id": campaign_id})

    # Deserialize brand profile
    try:
        brand_data = json.loads(brand_profile_json)
    except json.JSONDecodeError as e:
        raise ApplicationError(
            message=f"Invalid brand profile JSON: {e}",
            type="ValidationError",
            non_retryable=True,
        )

    activity.logger.info(f"Embedding brand: {brand_data.get('brand_name', 'Unknown')}")

    # Generate embedding
    activity.heartbeat({"stage": "embedding", "brand_name": brand_data.get("brand_name")})

    embedding_service = await get_embedding_service()
    vector = await embedding_service.embed_brand_profile(brand_data)

    # Check if all zeros (service unavailable)
    if all(v == 0.0 for v in vector[:10]):
        activity.logger.warning("Embedding service unavailable, skipping brand embedding")
        return EmbeddingResult(
            point_ids=[],
            collection_name="brands",
            count=0,
            skipped=1,
        )

    # Upsert to Qdrant
    activity.heartbeat({"stage": "upserting", "collection": "brands"})

    point_id = f"brand_{campaign_id}"
    qdrant = await get_qdrant_client()

    # Build payload
    payload = {
        "brand_name": brand_data.get("brand_name", "Unknown"),
        "website_url": brand_data.get("website_url", ""),
        "industry": brand_data.get("industry", "general"),
        "tagline": brand_data.get("tagline", ""),
        "value_propositions": brand_data.get("value_propositions", []),
        "tone_summary": brand_data.get("tone_summary", ""),
        "key_terms": brand_data.get("key_terms", []),
        "confidence_score": brand_data.get("confidence_score", 0.0),
        "campaign_id": campaign_id,
    }

    await qdrant.upsert_brand(point_id, vector, payload)

    activity.logger.info(f"Embedded brand: {brand_data.get('brand_name')} -> {point_id}")

    return EmbeddingResult(
        point_ids=[point_id],
        collection_name="brands",
        count=1,
        skipped=0,
    )


@activity.defn
async def embed_variants_activity(
    variants_json: str,
    campaign_id: str,
) -> EmbeddingResult:
    """Generate and store embeddings for all copy variants.

    This activity:
    1. Generates embeddings for all variants (batch)
    2. Upserts to Qdrant ad_creatives collection
    3. Returns point IDs

    Args:
        variants_json: Serialized list of CopyVariant dicts
        campaign_id: Campaign ID for reference

    Returns:
        EmbeddingResult with point IDs
    """
    from src.vector.qdrant_client import get_qdrant_client, QdrantConfig
    from src.vector.embeddings import get_embedding_service
    from qdrant_client.models import PointStruct

    activity.heartbeat({"stage": "parsing", "campaign_id": campaign_id})

    # Deserialize variants
    try:
        variants = json.loads(variants_json)
    except json.JSONDecodeError as e:
        raise ApplicationError(
            message=f"Invalid variants JSON: {e}",
            type="ValidationError",
            non_retryable=True,
        )

    activity.logger.info(f"Embedding {len(variants)} variants for campaign {campaign_id}")

    if not variants:
        return EmbeddingResult(
            point_ids=[],
            collection_name="ad_creatives",
            count=0,
            skipped=0,
        )

    # Generate embeddings in batch
    activity.heartbeat({"stage": "embedding", "count": len(variants)})

    embedding_service = await get_embedding_service()

    # Build embedding texts
    embedding_texts = []
    for v in variants:
        text = f"{v.get('headline', '')}. {v.get('primary_text', '')}"
        angle = v.get("angle", "")
        emotion = v.get("emotion", "")
        if angle or emotion:
            text += f" [Angle: {angle}, Emotion: {emotion}]"
        embedding_texts.append(text)

    vectors = await embedding_service.embed_batch(embedding_texts)

    # Check if embeddings are valid
    if not vectors or all(v == 0.0 for v in vectors[0][:10]):
        activity.logger.warning("Embedding service unavailable, skipping variant embeddings")
        return EmbeddingResult(
            point_ids=[],
            collection_name="ad_creatives",
            count=0,
            skipped=len(variants),
        )

    # Build points for batch upsert
    activity.heartbeat({"stage": "upserting", "count": len(variants)})

    points = []
    point_ids = []

    for variant, vector in zip(variants, vectors):
        variant_id = variant.get("id", f"unknown-{len(point_ids)}")
        point_id = f"variant_{variant_id}"
        point_ids.append(point_id)

        payload = {
            "copy_variant_id": variant_id,
            "campaign_id": campaign_id,
            "headline": variant.get("headline", ""),
            "primary_text": variant.get("primary_text", ""),
            "cta": variant.get("cta", ""),
            "angle": variant.get("angle", ""),
            "emotion": variant.get("emotion", ""),
            "platform": variant.get("platform", "meta"),
            "persona": variant.get("persona", ""),
            "performance_score": variant.get("quality_score", 0.0),
            "is_approved": False,
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )

    # Batch upsert to Qdrant
    qdrant = await get_qdrant_client()
    await qdrant.batch_upsert(QdrantConfig.COLLECTION_AD_CREATIVES, points)

    activity.logger.info(f"Embedded {len(variants)} variants")

    return EmbeddingResult(
        point_ids=point_ids,
        collection_name="ad_creatives",
        count=len(points),
        skipped=0,
    )


@activity.defn
async def find_similar_brands_activity(
    brand_profile_json: str,
    limit: int = 5,
) -> list[dict]:
    """Find brands similar to the given brand profile.

    Use case: Learn from similar brands' successful ad strategies.

    Args:
        brand_profile_json: Serialized BrandProfile
        limit: Number of results to return

    Returns:
        List of similar brands with similarity scores
    """
    from src.vector.qdrant_client import get_qdrant_client
    from src.vector.embeddings import get_embedding_service

    activity.heartbeat({"stage": "parsing"})

    brand_data = json.loads(brand_profile_json)

    activity.heartbeat({"stage": "embedding"})

    # Generate query embedding
    embedding_service = await get_embedding_service()
    query_vector = await embedding_service.embed_brand_profile(brand_data)

    # Check if valid embedding
    if all(v == 0.0 for v in query_vector[:10]):
        activity.logger.warning("Embedding service unavailable")
        return []

    activity.heartbeat({"stage": "searching"})

    # Search Qdrant
    qdrant = await get_qdrant_client()
    results = await qdrant.search_similar_brands(
        query_vector=query_vector,
        limit=limit,
        min_confidence=0.7,
        exclude_brand_name=brand_data.get("brand_name"),
    )

    activity.logger.info(f"Found {len(results)} similar brands")

    return results


@activity.defn
async def find_similar_ads_activity(
    copy_variant_json: str,
    limit: int = 10,
    min_performance: float = 70.0,
) -> list[dict]:
    """Find historically similar ads that performed well.

    Use case: Predict performance based on similar past ads.

    Args:
        copy_variant_json: Serialized CopyVariant
        limit: Number of results
        min_performance: Minimum performance score

    Returns:
        List of similar high-performing ads
    """
    from src.vector.qdrant_client import get_qdrant_client
    from src.vector.embeddings import get_embedding_service

    activity.heartbeat({"stage": "parsing"})

    variant_data = json.loads(copy_variant_json)

    activity.heartbeat({"stage": "embedding"})

    # Generate query embedding
    embedding_service = await get_embedding_service()
    query_vector = await embedding_service.embed_copy_variant(variant_data)

    # Check if valid embedding
    if all(v == 0.0 for v in query_vector[:10]):
        activity.logger.warning("Embedding service unavailable")
        return []

    activity.heartbeat({"stage": "searching"})

    # Search Qdrant
    qdrant = await get_qdrant_client()
    results = await qdrant.search_similar_ads(
        query_vector=query_vector,
        limit=limit,
        angle=variant_data.get("angle"),
        min_performance=min_performance,
        only_approved=True,
    )

    activity.logger.info(f"Found {len(results)} similar high-performing ads")

    return results
