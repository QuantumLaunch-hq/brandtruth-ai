# src/temporal/workflows/publish_workflow.py
"""Publish to Meta Workflow.

This workflow handles publishing approved ads to Meta Ads platform.
It's separate from the ad generation workflow for clean separation of concerns.

Workflow stages:
1. VALIDATING - Check Meta credentials
2. UPLOADING_IMAGES - Upload ad images to Meta
3. CREATING_CAMPAIGN - Create Meta campaign
4. CREATING_ADSET - Create ad set with targeting
5. CREATING_ADS - Create individual ads
6. ACTIVATING - Activate campaign (optional)
7. COMPLETED - All done
8. FAILED - Error occurred
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.temporal.activities.publish import (
        upload_image_to_meta_activity,
        create_meta_campaign_activity,
        create_meta_adset_activity,
        create_meta_ad_activity,
        activate_campaign_activity,
        validate_meta_credentials_activity,
        PublishResult,
        CampaignPublishResult,
    )


class PublishStage(str, Enum):
    """Stages of the publish workflow."""
    PENDING = "pending"
    VALIDATING = "validating"
    UPLOADING_IMAGES = "uploading_images"
    CREATING_CAMPAIGN = "creating_campaign"
    CREATING_ADSET = "creating_adset"
    CREATING_ADS = "creating_ads"
    ACTIVATING = "activating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PublishConfig:
    """Configuration for the publish workflow."""
    campaign_id: str  # Internal campaign ID
    campaign_name: str
    destination_url: str
    daily_budget: int  # in cents
    page_id: str

    # Variants to publish
    variants: list[dict] = field(default_factory=list)

    # Targeting
    age_min: int = 18
    age_max: int = 65
    countries: list[str] = field(default_factory=lambda: ["US"])
    interests: list[str] = field(default_factory=list)

    # Settings
    auto_activate: bool = False  # Start campaign immediately
    objective: str = "OUTCOME_TRAFFIC"
    optimization_goal: str = "LINK_CLICKS"


@dataclass
class PublishProgress:
    """Progress information for the publish workflow."""
    stage: str
    progress_percent: int
    message: str
    error: Optional[str] = None


# Retry policies
META_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=3,
    backoff_coefficient=2.0,
    non_retryable_error_types=["ValueError", "AuthenticationError"],
)


@workflow.defn
class PublishToMetaWorkflow:
    """Workflow for publishing ads to Meta.

    This workflow:
    1. Validates Meta credentials
    2. Uploads images for each variant
    3. Creates a Meta campaign
    4. Creates an ad set with targeting
    5. Creates ads for each variant
    6. Optionally activates the campaign
    """

    def __init__(self):
        self._stage = PublishStage.PENDING
        self._progress_percent = 0
        self._message = "Initializing..."
        self._error: Optional[str] = None

        # Results
        self._meta_campaign_id: Optional[str] = None
        self._meta_adset_id: Optional[str] = None
        self._image_hashes: dict[str, str] = {}  # variant_id -> image_hash
        self._ad_results: list[dict] = []
        self._result: Optional[CampaignPublishResult] = None

    def _update_progress(self, stage: PublishStage, percent: int, message: str):
        """Update workflow progress."""
        self._stage = stage
        self._progress_percent = percent
        self._message = message
        workflow.logger.info(f"[{stage.value}] {percent}% - {message}")

    # =========================================================================
    # Queries
    # =========================================================================

    @workflow.query
    def get_progress(self) -> dict:
        """Get current progress."""
        return {
            "stage": self._stage.value,
            "progress_percent": self._progress_percent,
            "message": self._message,
            "error": self._error,
        }

    @workflow.query
    def get_result(self) -> Optional[dict]:
        """Get publish result."""
        if not self._result:
            return None
        return {
            "success": self._result.success,
            "campaign_id": self._result.campaign_id,
            "adset_id": self._result.adset_id,
            "ads_published": self._result.ads_published,
            "ads_failed": self._result.ads_failed,
            "demo_mode": self._result.demo_mode,
            "error": self._result.error,
        }

    @workflow.query
    def get_meta_ids(self) -> dict:
        """Get Meta entity IDs."""
        return {
            "campaign_id": self._meta_campaign_id,
            "adset_id": self._meta_adset_id,
            "image_hashes": self._image_hashes,
            "ad_results": self._ad_results,
        }

    # =========================================================================
    # Main Workflow
    # =========================================================================

    @workflow.run
    async def run(self, config: PublishConfig) -> CampaignPublishResult:
        """Run the publish workflow.

        Args:
            config: Publishing configuration

        Returns:
            CampaignPublishResult with details
        """
        workflow.logger.info(f"Starting publish workflow for campaign: {config.campaign_name}")

        try:
            # Stage 1: Validate credentials
            self._update_progress(
                PublishStage.VALIDATING, 5,
                "Validating Meta API credentials"
            )

            validation = await workflow.execute_activity(
                validate_meta_credentials_activity,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=META_RETRY_POLICY,
            )

            is_demo = validation.get("demo_mode", False)
            if is_demo:
                workflow.logger.info("Running in demo mode - no real publishing")

            # Stage 2: Upload images
            self._update_progress(
                PublishStage.UPLOADING_IMAGES, 15,
                f"Uploading {len(config.variants)} images to Meta"
            )

            for i, variant in enumerate(config.variants):
                if variant.get("image_url"):
                    progress = 15 + int((i + 1) / len(config.variants) * 20)
                    self._update_progress(
                        PublishStage.UPLOADING_IMAGES, progress,
                        f"Uploading image {i + 1}/{len(config.variants)}"
                    )

                    image_hash = await workflow.execute_activity(
                        upload_image_to_meta_activity,
                        args=[variant["image_url"]],
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=META_RETRY_POLICY,
                    )
                    self._image_hashes[variant["id"]] = image_hash

            # Stage 3: Create campaign
            self._update_progress(
                PublishStage.CREATING_CAMPAIGN, 40,
                "Creating Meta campaign"
            )

            campaign_config = {
                "name": config.campaign_name,
                "objective": config.objective,
                "daily_budget": config.daily_budget,
                "start_paused": not config.auto_activate,
            }

            campaign_result = await workflow.execute_activity(
                create_meta_campaign_activity,
                args=[campaign_config],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=META_RETRY_POLICY,
            )
            self._meta_campaign_id = campaign_result["id"]

            # Stage 4: Create ad set
            self._update_progress(
                PublishStage.CREATING_ADSET, 55,
                "Creating ad set with targeting"
            )

            adset_config = {
                "name": f"{config.campaign_name} - Ad Set",
                "daily_budget": config.daily_budget,
                "age_min": config.age_min,
                "age_max": config.age_max,
                "countries": config.countries,
                "optimization_goal": config.optimization_goal,
                "start_paused": not config.auto_activate,
            }

            adset_result = await workflow.execute_activity(
                create_meta_adset_activity,
                args=[self._meta_campaign_id, adset_config],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=META_RETRY_POLICY,
            )
            self._meta_adset_id = adset_result["id"]

            # Stage 5: Create ads
            self._update_progress(
                PublishStage.CREATING_ADS, 65,
                f"Creating {len(config.variants)} ads"
            )

            ads_published = 0
            ads_failed = 0

            for i, variant in enumerate(config.variants):
                progress = 65 + int((i + 1) / len(config.variants) * 25)
                self._update_progress(
                    PublishStage.CREATING_ADS, progress,
                    f"Creating ad {i + 1}/{len(config.variants)}"
                )

                image_hash = self._image_hashes.get(variant["id"], "")

                try:
                    ad_result = await workflow.execute_activity(
                        create_meta_ad_activity,
                        args=[
                            self._meta_adset_id,
                            variant,
                            image_hash,
                            config.page_id,
                        ],
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=META_RETRY_POLICY,
                    )
                    self._ad_results.append(ad_result)
                    ads_published += 1
                except Exception as e:
                    workflow.logger.error(f"Failed to create ad for variant {variant['id']}: {e}")
                    self._ad_results.append({
                        "variant_id": variant["id"],
                        "error": str(e),
                    })
                    ads_failed += 1

            # Stage 6: Activate (if requested)
            if config.auto_activate and ads_published > 0:
                self._update_progress(
                    PublishStage.ACTIVATING, 95,
                    "Activating campaign"
                )

                await workflow.execute_activity(
                    activate_campaign_activity,
                    args=[self._meta_campaign_id],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=META_RETRY_POLICY,
                )

            # Complete
            self._update_progress(
                PublishStage.COMPLETED, 100,
                f"Published {ads_published} ads successfully"
            )

            self._result = CampaignPublishResult(
                success=ads_published > 0,
                campaign_id=self._meta_campaign_id,
                adset_id=self._meta_adset_id,
                ads_published=ads_published,
                ads_failed=ads_failed,
                demo_mode=is_demo,
            )

            return self._result

        except Exception as e:
            self._error = str(e)
            self._update_progress(
                PublishStage.FAILED, self._progress_percent,
                f"Failed: {str(e)}"
            )

            self._result = CampaignPublishResult(
                success=False,
                error=str(e),
            )

            raise
