# src/temporal/activities/extract.py
"""Brand extraction activity for Temporal workflow.

This activity wraps the brand_extractor module, providing:
- Automatic retries on transient failures
- Heartbeating for long-running extractions
- Serializable result for workflow checkpointing
"""

from dataclasses import dataclass
from typing import Optional
from temporalio import activity

from src.extractors.brand_extractor import extract_brand
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BrandProfileResult:
    """Serializable brand profile result for Temporal."""
    brand_name: str
    tagline: str
    industry: str
    value_propositions: list[str]
    claims: list[dict]  # {claim, source, risk_level}
    tone_markers: list[dict]  # {tone, confidence}
    confidence_score: float
    extraction_time_ms: int
    website_url: str  # Source URL for constructing BrandProfile


@activity.defn
async def extract_brand_activity(url: str) -> BrandProfileResult:
    """Extract brand profile from URL.

    This is a Temporal activity that wraps the existing brand extractor.
    It automatically handles:
    - Retries on transient failures (network, rate limits)
    - Heartbeating for long extractions
    - Result serialization for checkpointing

    Args:
        url: Website URL to extract brand from (with or without scheme)

    Returns:
        BrandProfileResult with extracted brand information

    Raises:
        Exception: On extraction failure (will be retried by Temporal)
    """
    import time
    start_time = time.time()

    # Normalize URL - ensure it has a scheme
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"

    activity.logger.info(f"Extracting brand from {url}")

    # Heartbeat to let Temporal know we're still working
    activity.heartbeat(f"Starting extraction from {url}")

    try:
        # Call the existing brand extractor
        brand_profile = await extract_brand(url)

        activity.heartbeat("Brand extracted, serializing result")

        # Convert to serializable format
        result = BrandProfileResult(
            brand_name=brand_profile.brand_name,
            tagline=brand_profile.tagline or "",
            industry=brand_profile.industry or "general",
            value_propositions=brand_profile.value_propositions,
            claims=[
                {
                    "claim": c.claim,
                    "source": c.source_text,
                    "risk_level": c.risk_level.value,
                }
                for c in brand_profile.claims
            ],
            tone_markers=[
                {"tone": t.category.value, "confidence": t.confidence}
                for t in brand_profile.tone_markers
            ],
            confidence_score=brand_profile.confidence_score,
            extraction_time_ms=int((time.time() - start_time) * 1000),
            website_url=str(brand_profile.website_url),
        )

        activity.logger.info(
            f"Extracted brand: {result.brand_name} "
            f"({result.confidence_score:.0%} confidence, {result.extraction_time_ms}ms)"
        )

        return result

    except Exception as e:
        activity.logger.error(f"Brand extraction failed: {e}")
        raise  # Let Temporal handle retry
