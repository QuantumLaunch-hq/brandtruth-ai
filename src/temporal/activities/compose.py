# src/temporal/activities/compose.py
"""Ad composition activity for Temporal workflow.

This activity wraps the ad_composer module, providing:
- Image download and processing
- Multi-format ad generation
- Asset storage and tracking
"""

from dataclasses import dataclass
from pathlib import Path

from temporalio import activity

from src.composers.ad_composer import compose_ads
from src.models.image_match import ImageMatch, ImageMood, ImageComposition, ImageSource
from src.models.copy_variant import CopyVariant, CopyAngle, EmotionalTarget, Platform
from src.models.composed_ad import AdFormat
from src.temporal.activities.generate import CopyVariantResult
from src.temporal.activities.match import ImageMatchResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AdAsset:
    """Serializable ad asset for Temporal."""
    format: str
    file_path: str
    file_url: str  # Relative URL path like /output/ad-xyz_1x1.png
    width: int
    height: int


@dataclass
class ComposedAdResult:
    """Serializable composed ad for Temporal."""
    id: str
    copy_variant_id: str
    headline: str
    primary_text: str
    cta: str
    assets: list[AdAsset]
    destination_url: str = ""  # URL where ad clicks should go (the original site)


@dataclass
class AdCompositionResult:
    """Result of ad composition activity."""
    ads: list[ComposedAdResult]
    composition_time_ms: int


@activity.defn
async def compose_ads_activity(
    variants: list[CopyVariantResult],
    image_matches: list[ImageMatchResult],
    destination_url: str,
    output_dir: str = "./output",
    formats: list[str] | None = None,
) -> AdCompositionResult:
    """Compose final ad creatives from copy and images.

    This activity wraps the ad composer with:
    - Image download and caching
    - Multi-format rendering
    - Progress heartbeating

    Args:
        variants: Copy variants
        image_matches: Matched images for each variant
        destination_url: The original site URL (where ad clicks should go)
        output_dir: Directory for generated assets
        formats: Ad formats to generate (default: SQUARE)

    Returns:
        AdCompositionResult with composed ads

    Raises:
        Exception: On composition failure (will be retried)
    """
    import time
    start_time = time.time()

    activity.logger.info(f"Composing ads for {len(variants)} variants")
    activity.heartbeat(f"Starting ad composition for {len(variants)} variants")

    try:
        # Convert variants to CopyVariant objects
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

        # Build image matches dict using all fields from match activity
        image_matches_dict = {}
        for match in image_matches:
            # Map string values back to enums
            source_map = {
                "unsplash": ImageSource.UNSPLASH,
                "pexels": ImageSource.PEXELS,
                "azure_dalle": ImageSource.AZURE_DALLE,
                "openai_dalle": ImageSource.OPENAI_DALLE,
            }
            mood_map = {
                "positive": ImageMood.POSITIVE,
                "professional": ImageMood.PROFESSIONAL,
                "aspirational": ImageMood.ASPIRATIONAL,
                "empathetic": ImageMood.EMPATHETIC,
                "energetic": ImageMood.ENERGETIC,
                "calm": ImageMood.CALM,
                "tense": ImageMood.TENSE,
                "neutral": ImageMood.NEUTRAL,
            }
            comp_map = {
                "centered": ImageComposition.CENTERED,
                "rule_of_thirds": ImageComposition.RULE_OF_THIRDS,
                "minimal": ImageComposition.MINIMAL,
                "busy": ImageComposition.BUSY,
                "portrait": ImageComposition.PORTRAIT,
                "abstract": ImageComposition.ABSTRACT,
            }

            image_matches_dict[match.copy_variant_id] = ImageMatch(
                id=match.id or f"match-{match.copy_variant_id[:8]}",
                copy_variant_id=match.copy_variant_id,
                image_id=match.image_id or match.id or "unknown",
                image_url=match.image_url,
                thumb_url=match.thumb_url or match.image_url,
                download_url=match.download_url or match.image_url,
                source=source_map.get(match.source, ImageSource.PEXELS),
                photographer=match.photographer or "Unknown",
                photographer_url=match.photographer_url,
                mood=mood_map.get(match.mood, ImageMood.PROFESSIONAL),
                composition=comp_map.get(match.composition, ImageComposition.RULE_OF_THIRDS),
                match_score=match.match_score or match.relevance_score or 0.8,
                width=match.width or 1200,
                height=match.height or 800,
            )

        # Parse formats - map common names to enum values
        format_mapping = {
            "square": AdFormat.SQUARE,
            "portrait": AdFormat.PORTRAIT,
            "story": AdFormat.STORY,
            "landscape": AdFormat.LANDSCAPE,
            "1:1": AdFormat.SQUARE,
            "4:5": AdFormat.PORTRAIT,
            "9:16": AdFormat.STORY,
            "16:9": AdFormat.LANDSCAPE,
        }
        default_formats = [AdFormat.SQUARE]
        if formats:
            ad_formats = [format_mapping.get(f.lower(), AdFormat.SQUARE) for f in formats]
        else:
            ad_formats = default_formats

        activity.heartbeat("Composing ad creatives")

        # Call the existing composer
        composition_result = compose_ads(
            copy_variants=copy_variants,
            image_matches=image_matches_dict,
            output_dir=output_dir,
            formats=ad_formats,
        )

        # Convert to serializable format
        ads = []
        for ad in composition_result.ads:
            assets = []
            for fmt, asset in ad.assets.items():
                # Extract filename from path to create URL
                filename = Path(asset.file_path).name
                file_url = f"/output/{filename}"

                assets.append(AdAsset(
                    format=fmt,
                    file_path=asset.file_path,
                    file_url=file_url,
                    width=asset.width,
                    height=asset.height,
                ))

            ads.append(
                ComposedAdResult(
                    id=ad.id,
                    copy_variant_id=ad.copy_variant_id,
                    headline=ad.headline,
                    primary_text=ad.primary_text,
                    cta=ad.cta,
                    destination_url=destination_url,
                    assets=assets,
                )
            )

        result = AdCompositionResult(
            ads=ads,
            composition_time_ms=int((time.time() - start_time) * 1000),
        )

        activity.logger.info(
            f"Composed {len(ads)} ads in {result.composition_time_ms}ms"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Ad composition failed: {e}")
        raise
