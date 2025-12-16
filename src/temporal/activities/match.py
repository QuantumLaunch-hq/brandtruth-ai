# src/temporal/activities/match.py
"""Image matching activity for Temporal workflow.

This activity uses a multi-source image provider with fallback:
1. Pexels API (free, curated stock - primary)
2. Unsplash API (free, community stock - fallback)
3. Azure DALL-E 3 (AI-generated - final fallback, uses Azure credits)

The provider automatically falls back if a source is unavailable or fails.
"""

import os
from dataclasses import dataclass
from temporalio import activity

from src.composers.image_provider import (
    get_image_provider,
    ImageProviderConfig,
    ImageProviderPriority,
)
from src.models.copy_variant import CopyVariant, CopyAngle, EmotionalTarget, Platform
from src.temporal.activities.generate import CopyVariantResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ImageMatchResult:
    """Serializable image match for Temporal.

    Contains all fields needed by compose activity to build full ImageMatch.
    """
    copy_variant_id: str
    image_url: str
    relevance_score: float
    photographer: str
    photographer_url: str
    # Additional fields for compose activity
    id: str = ""
    image_id: str = ""
    thumb_url: str = ""
    download_url: str = ""
    source: str = "pexels"
    mood: str = "professional"
    composition: str = "rule_of_thirds"
    width: int = 1200
    height: int = 800
    match_score: float = 0.8


@dataclass
class ImageMatchingResult:
    """Result of image matching activity."""
    matches: list[ImageMatchResult]
    matching_time_ms: int


@activity.defn
async def match_images_activity(
    variants: list[CopyVariantResult],
    images_per_variant: int = 1,
) -> ImageMatchingResult:
    """Match images to copy variants.

    This activity wraps the image matcher with:
    - Automatic retries on API failures
    - Rate limit handling for Unsplash
    - Heartbeating for batch operations

    Args:
        variants: Copy variants to match images for
        images_per_variant: Number of images per variant

    Returns:
        ImageMatchingResult with matched images

    Raises:
        Exception: On matching failure (will be retried)
    """
    import time
    start_time = time.time()

    activity.logger.info(f"Matching images for {len(variants)} variants")
    activity.heartbeat(f"Starting image matching for {len(variants)} variants")

    try:
        # Convert to CopyVariant objects for the matcher
        copy_variants = [
            CopyVariant(
                id=v.id,
                headline=v.headline,
                primary_text=v.primary_text,
                cta=v.cta,
                angle=CopyAngle(v.angle),
                emotion=EmotionalTarget(v.emotion),
                platform=Platform.META,
                persona=v.persona,
                quality_score=v.quality_score,
                brand_claims_used=v.claims_used,
            )
            for v in variants
        ]

        # Configure multi-source image provider with fallback chain
        # Priority: Pexels -> Unsplash -> Azure DALL-E (uses Azure credits)
        config = ImageProviderConfig(
            priority=ImageProviderPriority.STOCK_FIRST,
            enable_dalle=bool(os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("OPENAI_API_KEY")),
            enable_pexels=bool(os.getenv("PEXELS_API_KEY")),
            enable_unsplash=bool(os.getenv("UNSPLASH_ACCESS_KEY")),
            images_per_variant=images_per_variant,
        )

        provider = get_image_provider(config)
        activity.logger.info(f"Image sources available: {provider.available_sources}")

        # Match images for each variant
        matches = []
        for i, variant in enumerate(copy_variants):
            activity.heartbeat(f"Matching image {i+1}/{len(copy_variants)}")

            match_result = provider.get_images_for_variant(variant, images_per_variant)

            # Log any warnings
            for warning in match_result.warnings:
                activity.logger.warning(warning)

            # Get best match
            best = match_result.get_best_match()
            if best:
                matches.append(
                    ImageMatchResult(
                        copy_variant_id=match_result.copy_variant_id,
                        image_url=best.image_url,
                        relevance_score=best.relevance_score if best.relevance_score is not None else best.match_score,
                        photographer=best.photographer or "",
                        photographer_url=best.photographer_url or "",
                        # Pass through all fields for compose activity
                        id=best.id,
                        image_id=best.image_id,
                        thumb_url=best.thumb_url,
                        download_url=best.download_url,
                        source=best.source.value,
                        mood=best.mood.value,
                        composition=best.composition.value,
                        width=best.width,
                        height=best.height,
                        match_score=best.match_score,
                    )
                )
                activity.logger.info(
                    f"Variant {variant.id}: matched from {best.source.value} "
                    f"(score: {best.match_score:.2f})"
                )
            else:
                activity.logger.warning(f"No image found for variant {variant.id}")

        result = ImageMatchingResult(
            matches=matches,
            matching_time_ms=int((time.time() - start_time) * 1000),
        )

        activity.logger.info(
            f"Matched {len(matches)} images in {result.matching_time_ms}ms "
            f"(sources: {provider.available_sources})"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Image matching failed: {e}")
        raise
