# src/temporal/activities/generate.py
"""Copy generation activity for Temporal workflow.

This activity wraps the copy_generator module, providing:
- Automatic retries on LLM API failures
- Token cost tracking
- Parallel variant generation
"""

from dataclasses import dataclass
from temporalio import activity

from src.generators.copy_generator import generate_copy
from src.models.brand_profile import BrandProfile, BrandClaim, ToneMarker, ClaimRiskLevel, ToneCategory
from src.models.copy_variant import Platform
from src.temporal.activities.extract import BrandProfileResult
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CopyVariantResult:
    """Serializable copy variant for Temporal."""
    id: str
    headline: str
    primary_text: str
    cta: str
    angle: str
    emotion: str
    persona: str
    quality_score: float
    claims_used: list[str]


@dataclass
class CopyGenerationResult:
    """Result of copy generation activity."""
    variants: list[CopyVariantResult]
    generation_time_ms: int
    total_tokens_used: int


@activity.defn
async def generate_copy_activity(
    brand_profile: BrandProfileResult,
    num_variants: int = 5,
    platform: str = "meta",
    objective: str = "conversions",
) -> CopyGenerationResult:
    """Generate ad copy variants from brand profile.

    This activity wraps the copy generator with:
    - Automatic retries on LLM API failures
    - Heartbeating for multi-variant generation
    - Token usage tracking

    Args:
        brand_profile: Extracted brand profile
        num_variants: Number of variants to generate
        platform: Target platform (meta, google, tiktok)
        objective: Campaign objective

    Returns:
        CopyGenerationResult with generated variants

    Raises:
        Exception: On generation failure (will be retried)
    """
    import time
    start_time = time.time()

    activity.logger.info(
        f"Generating {num_variants} copy variants for {brand_profile.brand_name}"
    )
    activity.heartbeat(f"Starting copy generation for {brand_profile.brand_name}")

    try:
        # Reconstruct BrandProfile from serialized data
        # This is necessary because Temporal passes serialized data
        brand = BrandProfile(
            brand_name=brand_profile.brand_name,
            website_url=brand_profile.website_url,
            tagline=brand_profile.tagline,
            industry=brand_profile.industry,
            value_propositions=brand_profile.value_propositions,
            claims=[
                BrandClaim(
                    claim=c["claim"],
                    claim_type="extracted",
                    source_text=c["source"],
                    source_url=brand_profile.website_url,
                    risk_level=ClaimRiskLevel(c["risk_level"].lower()),
                )
                for c in brand_profile.claims
            ],
            tone_markers=[
                ToneMarker(
                    category=ToneCategory(t["tone"].lower()),
                    confidence=t["confidence"],
                    evidence="Extracted from website",
                    source_url=brand_profile.website_url,
                )
                for t in brand_profile.tone_markers
            ],
            confidence_score=brand_profile.confidence_score,
        )

        # Call the existing copy generator
        copy_result = generate_copy(
            brand_profile=brand,
            objective=objective,
            platform=Platform(platform),
            num_variants=num_variants,
        )

        activity.heartbeat(f"Generated {len(copy_result.variants)} variants")

        # Convert to serializable format
        variants = [
            CopyVariantResult(
                id=v.id,
                headline=v.headline,
                primary_text=v.primary_text,
                cta=v.cta,
                angle=v.angle.value,
                emotion=v.emotion.value,
                persona=v.persona,
                quality_score=v.quality_score,
                claims_used=v.brand_claims_used,
            )
            for v in copy_result.variants
        ]

        result = CopyGenerationResult(
            variants=variants,
            generation_time_ms=int((time.time() - start_time) * 1000),
            total_tokens_used=0,  # TODO: Track actual token usage
        )

        activity.logger.info(
            f"Generated {len(variants)} variants in {result.generation_time_ms}ms"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Copy generation failed: {e}")
        raise
