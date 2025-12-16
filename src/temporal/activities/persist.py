# src/temporal/activities/persist.py
"""Database persistence activities for Temporal workflow.

These activities handle saving workflow results to the database,
allowing the frontend to display real campaign data.
"""

from dataclasses import dataclass
from temporalio import activity

from src.db import (
    get_database,
    CampaignCreate,
    CampaignUpdate,
    CampaignStatus,
    VariantCreate,
    VariantStatus,
)
from src.temporal.activities.generate import CopyVariantResult
from src.temporal.activities.match import ImageMatchResult
from src.temporal.activities.score import PerformanceScore
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CampaignRef:
    """Reference to a campaign for workflow use."""
    campaign_id: str
    user_id: str


@activity.defn
async def create_campaign_activity(
    name: str,
    url: str,
    user_id: str,
    workflow_id: str,
) -> CampaignRef:
    """Create a new campaign in the database.

    Called at the start of the workflow to create the campaign record.

    Args:
        name: Campaign name (derived from URL if not provided)
        url: Target URL
        user_id: Owner user ID
        workflow_id: Temporal workflow ID for linking

    Returns:
        CampaignRef with campaign_id and user_id
    """
    activity.logger.info(f"Creating campaign for {url}")
    activity.heartbeat("Creating campaign")

    db = get_database()
    await db.connect()

    try:
        campaign = await db.create_campaign(
            CampaignCreate(
                name=name,
                url=url,
                user_id=user_id,
                status=CampaignStatus.PROCESSING,
                workflow_id=workflow_id,
            )
        )

        activity.logger.info(f"Created campaign: {campaign.id}")
        return CampaignRef(campaign_id=campaign.id, user_id=user_id)

    finally:
        await db.disconnect()


@activity.defn
async def update_campaign_status_activity(
    campaign_id: str,
    status: str,
) -> bool:
    """Update campaign status.

    Args:
        campaign_id: Campaign ID
        status: New status (DRAFT, PROCESSING, READY, APPROVED, PUBLISHED, FAILED, CANCELLED)

    Returns:
        True if updated successfully
    """
    activity.logger.info(f"Updating campaign {campaign_id} status to {status}")

    db = get_database()
    await db.connect()

    try:
        campaign = await db.update_campaign_status(
            campaign_id,
            CampaignStatus(status)
        )
        return campaign is not None

    finally:
        await db.disconnect()


@activity.defn
async def save_brand_profile_activity(
    campaign_id: str,
    brand_profile: dict,
) -> bool:
    """Save brand profile to campaign.

    Args:
        campaign_id: Campaign ID
        brand_profile: Extracted brand profile as dict

    Returns:
        True if saved successfully
    """
    activity.logger.info(f"Saving brand profile to campaign {campaign_id}")
    activity.heartbeat("Saving brand profile")

    db = get_database()
    await db.connect()

    try:
        campaign = await db.update_campaign(
            campaign_id,
            CampaignUpdate(brand_profile=brand_profile)
        )
        return campaign is not None

    finally:
        await db.disconnect()


@activity.defn
async def save_variants_activity(
    campaign_id: str,
    variants: list[CopyVariantResult],
    image_matches: list[ImageMatchResult],
    scores: list[PerformanceScore],
) -> int:
    """Save copy variants with images and scores to database.

    Combines copy variants, image matches, and scores into database records.

    Args:
        campaign_id: Campaign ID
        variants: Generated copy variants
        image_matches: Matched images for each variant
        scores: Performance scores for each variant

    Returns:
        Number of variants saved
    """
    activity.logger.info(f"Saving {len(variants)} variants to campaign {campaign_id}")
    activity.heartbeat(f"Saving {len(variants)} variants")

    db = get_database()
    await db.connect()

    try:
        # Build lookup dicts for images and scores
        images_by_variant = {m.copy_variant_id: m for m in image_matches}
        scores_by_variant = {s.variant_id: s for s in scores}

        # Create variant records
        variant_creates = []
        for v in variants:
            image = images_by_variant.get(v.id)
            score = scores_by_variant.get(v.id)

            variant_creates.append(
                VariantCreate(
                    campaign_id=campaign_id,
                    headline=v.headline,
                    primary_text=v.primary_text,
                    cta=v.cta,
                    angle=v.angle,
                    emotion=v.emotion,
                    image_url=image.image_url if image else None,
                    composed_url=None,  # Will be set after composition
                    score=score.score if score else None,
                    score_details={
                        "confidence": score.confidence,
                        "strengths": score.strengths,
                        "weaknesses": score.weaknesses,
                        "recommendations": score.recommendations,
                    } if score else None,
                    status=VariantStatus.PENDING,
                )
            )

        # Batch create
        created = await db.create_variants_batch(variant_creates)
        activity.logger.info(f"Saved {len(created)} variants")
        return len(created)

    finally:
        await db.disconnect()


@activity.defn
async def complete_campaign_activity(
    campaign_id: str,
) -> bool:
    """Mark campaign as ready for review.

    Called when all pipeline stages complete successfully.

    Args:
        campaign_id: Campaign ID

    Returns:
        True if updated successfully
    """
    from datetime import datetime

    activity.logger.info(f"Completing campaign {campaign_id}")

    db = get_database()
    await db.connect()

    try:
        campaign = await db.update_campaign(
            campaign_id,
            CampaignUpdate(
                status=CampaignStatus.READY,
                completed_at=datetime.now(),
            )
        )
        return campaign is not None

    finally:
        await db.disconnect()


@activity.defn
async def fail_campaign_activity(
    campaign_id: str,
    error: str,
) -> bool:
    """Mark campaign as failed.

    Called when the pipeline fails.

    Args:
        campaign_id: Campaign ID
        error: Error message

    Returns:
        True if updated successfully
    """
    activity.logger.info(f"Failing campaign {campaign_id}: {error}")

    db = get_database()
    await db.connect()

    try:
        campaign = await db.update_campaign_status(
            campaign_id,
            CampaignStatus.FAILED
        )
        return campaign is not None

    finally:
        await db.disconnect()
