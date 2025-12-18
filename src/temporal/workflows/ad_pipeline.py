# src/temporal/workflows/ad_pipeline.py
"""Ad Pipeline Workflow for BrandTruth AI.

This is the main durable workflow that orchestrates ad generation.
The workflow is "fire-and-forget" - it completes after scoring and
does NOT wait for human approval. Approval/rejection is handled
via REST API (database state), not workflow signals.

Key properties:
1. Survives crashes - resumes from last successful step
2. Has automatic retries - each activity retries independently
3. Completes quickly - no waiting for human input
4. Provides real-time progress - queryable state at any time
5. Is observable - full history in Temporal UI

Workflow Stages:
1. extract_brand - Extract brand profile from URL
2. generate_copy - Generate copy variants
3. match_images - Match images to variants
4. compose_ads - Compose final ad creatives
5. score_variants - Predict performance scores
6. complete - Workflow done, results saved to DB

Post-workflow (handled separately):
- User reviews variants in UI
- User approves/rejects via REST API (DB update)
- Publishing to ad platforms is a separate workflow
"""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activity stubs (not actual implementations)
with workflow.unsafe.imports_passed_through():
    from src.temporal.activities.extract import extract_brand_activity, BrandProfileResult
    from src.temporal.activities.generate import generate_copy_activity, CopyGenerationResult
    from src.temporal.activities.match import match_images_activity, ImageMatchingResult
    from src.temporal.activities.compose import compose_ads_activity, AdCompositionResult
    from src.temporal.activities.score import predict_performance_activity, PerformanceScoringResult
    from src.temporal.activities.persist import (
        create_campaign_activity,
        update_campaign_status_activity,
        save_brand_profile_activity,
        save_variants_activity,
        complete_campaign_activity,
        fail_campaign_activity,
        CampaignRef,
    )
    # MinIO upload activities
    from src.temporal.activities.upload import (
        upload_composed_ad_activity,
        UploadResult,
    )
    # Qdrant embedding activities
    from src.temporal.activities.embed import (
        embed_brand_activity,
        embed_variants_activity,
        EmbeddingResult,
    )
    import json


class PipelineStage(str, Enum):
    """Pipeline execution stages for progress tracking.

    Note: Workflow completes after scoring. Approval/rejection is handled
    via REST API (database state), not workflow signals. Publishing to
    ad platforms is a separate workflow triggered after approval.
    """
    PENDING = "pending"
    EXTRACTING = "extracting"
    EMBEDDING_BRAND = "embedding_brand"
    GENERATING = "generating"
    EMBEDDING_VARIANTS = "embedding_variants"
    MATCHING = "matching"
    COMPOSING = "composing"
    UPLOADING = "uploading"
    SCORING = "scoring"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """Configuration for a pipeline run."""
    url: str
    num_variants: int = 5
    platform: str = "meta"
    objective: str = "conversions"
    formats: list[str] | None = None
    output_dir: str = "./output"
    # Database persistence (optional - if not provided, workflow runs without DB)
    user_id: str | None = None
    campaign_name: str | None = None


@dataclass
class PipelineProgress:
    """Current progress of the pipeline."""
    stage: str
    progress_percent: int
    message: str
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Complete result of the pipeline workflow.

    Note: This workflow produces variants with scores. Approval status
    is managed separately in the database, not in this result.
    """
    workflow_id: str
    config: PipelineConfig
    stage: str
    brand_profile: Optional[BrandProfileResult] = None
    copy_variants: Optional[CopyGenerationResult] = None
    image_matches: Optional[ImageMatchingResult] = None
    composed_ads: Optional[AdCompositionResult] = None
    performance_scores: Optional[PerformanceScoringResult] = None
    error: Optional[str] = None
    duration_ms: int = 0
    # Database reference (if persistence was enabled)
    campaign_id: Optional[str] = None


# Retry policy for activities - optimized for LLM workloads (Dec 2025)
DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=3,
    backoff_coefficient=2.0,
    # Don't retry on these non-transient errors
    non_retryable_error_types=["ValueError", "ValidationError"],
)

# LLM-specific retry policy - more patient with rate limits
LLM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=5,
    backoff_coefficient=2.5,
    non_retryable_error_types=["ValueError", "ValidationError"],
)


@workflow.defn
class AdPipelineWorkflow:
    """Durable ad generation pipeline workflow.

    This workflow orchestrates all pipeline stages with:
    - Automatic retries and error handling
    - Progress tracking via queries
    - Human approval via signals
    - Full observability in Temporal UI

    Example usage:
        # Start workflow
        handle = await client.start_workflow(
            AdPipelineWorkflow.run,
            PipelineConfig(url="https://example.com"),
            id="pipeline-123",
            task_queue="brandtruth-pipeline",
        )

        # Query progress
        progress = await handle.query(AdPipelineWorkflow.get_progress)

        # Approve variants
        await handle.signal(AdPipelineWorkflow.approve_variants, ["v1", "v2"])

        # Wait for completion
        result = await handle.result()
    """

    def __init__(self):
        self._stage = PipelineStage.PENDING
        self._progress_percent = 0
        self._message = "Initializing..."
        self._error: Optional[str] = None

        # Results from each stage
        self._brand_profile: Optional[BrandProfileResult] = None
        self._copy_variants: Optional[CopyGenerationResult] = None
        self._image_matches: Optional[ImageMatchingResult] = None
        self._composed_ads: Optional[AdCompositionResult] = None
        self._performance_scores: Optional[PerformanceScoringResult] = None

        # Database persistence
        self._campaign_id: Optional[str] = None

    @workflow.run
    async def run(self, config: PipelineConfig) -> PipelineResult:
        """Execute the complete ad generation pipeline.

        Args:
            config: Pipeline configuration

        Returns:
            PipelineResult with all generated data
        """
        # Use workflow.now() instead of time.time() for determinism
        start_time = workflow.now()
        workflow_id = workflow.info().workflow_id

        try:
            # Stage 0: Create campaign in database (if user_id provided)
            if config.user_id:
                self._update_progress(PipelineStage.PENDING, 5, "Creating campaign record")

                campaign_ref: CampaignRef = await workflow.execute_activity(
                    create_campaign_activity,
                    args=[
                        config.campaign_name or f"Campaign for {config.url[:50]}",
                        config.url,
                        config.user_id,
                        workflow_id,
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )
                self._campaign_id = campaign_ref.campaign_id
                workflow.logger.info(f"Created campaign: {self._campaign_id}")

            # Stage 1: Extract brand (uses Playwright + LLM)
            self._update_progress(PipelineStage.EXTRACTING, 10, f"Extracting brand from {config.url}")

            self._brand_profile = await workflow.execute_activity(
                extract_brand_activity,
                config.url,
                start_to_close_timeout=timedelta(minutes=5),  # Allow time for page scraping + LLM
                retry_policy=LLM_RETRY_POLICY,
            )

            self._update_progress(
                PipelineStage.EXTRACTING, 25,
                f"Extracted: {self._brand_profile.brand_name}"
            )

            # Save brand profile to database
            if self._campaign_id:
                await workflow.execute_activity(
                    save_brand_profile_activity,
                    args=[
                        self._campaign_id,
                        {
                            "brand_name": self._brand_profile.brand_name,
                            "website_url": self._brand_profile.website_url,
                            "tagline": self._brand_profile.tagline,
                            "industry": self._brand_profile.industry,
                            "value_propositions": self._brand_profile.value_propositions,
                            "claims": self._brand_profile.claims,
                            "tone_markers": self._brand_profile.tone_markers,
                            "confidence_score": self._brand_profile.confidence_score,
                        },
                    ],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )

            # Stage 1.5: Embed brand profile to Qdrant (for similarity search)
            self._update_progress(PipelineStage.EMBEDDING_BRAND, 28, "Embedding brand profile")

            brand_json = json.dumps({
                "brand_name": self._brand_profile.brand_name,
                "website_url": self._brand_profile.website_url,
                "tagline": self._brand_profile.tagline,
                "industry": self._brand_profile.industry,
                "value_propositions": self._brand_profile.value_propositions,
                "tone_markers": self._brand_profile.tone_markers,
                "confidence_score": self._brand_profile.confidence_score,
            })

            try:
                await workflow.execute_activity(
                    embed_brand_activity,
                    args=[brand_json, workflow_id],  # brand_profile_json, campaign_id
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )
                workflow.logger.info("Brand profile embedded to Qdrant")
            except Exception as e:
                # Non-critical - log and continue
                workflow.logger.warning(f"Failed to embed brand (continuing): {e}")

            # Stage 2: Generate copy (LLM-intensive - multiple variants)
            self._update_progress(
                PipelineStage.GENERATING, 30,
                f"Generating {config.num_variants} ad variants"
            )

            self._copy_variants = await workflow.execute_activity(
                generate_copy_activity,
                args=[self._brand_profile, config.num_variants, config.platform, config.objective],
                start_to_close_timeout=timedelta(minutes=10),  # LLM can take time for multiple variants
                retry_policy=LLM_RETRY_POLICY,
            )

            self._update_progress(
                PipelineStage.GENERATING, 45,
                f"Generated {len(self._copy_variants.variants)} variants"
            )

            # Stage 2.5: Embed copy variants to Qdrant (for similarity search)
            self._update_progress(PipelineStage.EMBEDDING_VARIANTS, 48, "Embedding copy variants")

            variants_json = json.dumps([
                {
                    "id": v.id,
                    "headline": v.headline,
                    "primary_text": v.primary_text,
                    "cta": v.cta,
                    "angle": v.angle,
                    "emotion": v.emotion,
                }
                for v in self._copy_variants.variants
            ])

            try:
                await workflow.execute_activity(
                    embed_variants_activity,
                    args=[variants_json, workflow_id],  # variants_json, campaign_id
                    start_to_close_timeout=timedelta(seconds=120),  # Batch embedding takes longer
                    retry_policy=DEFAULT_RETRY_POLICY,
                )
                workflow.logger.info(f"Embedded {len(self._copy_variants.variants)} variants to Qdrant")
            except Exception as e:
                # Non-critical - log and continue
                workflow.logger.warning(f"Failed to embed variants (continuing): {e}")

            # Stage 3: Match images (Unsplash API + optional vision AI)
            self._update_progress(PipelineStage.MATCHING, 50, "Matching images with vision AI")

            self._image_matches = await workflow.execute_activity(
                match_images_activity,
                args=[self._copy_variants.variants, 1],
                start_to_close_timeout=timedelta(minutes=5),  # API calls for each variant
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            self._update_progress(
                PipelineStage.MATCHING, 60,
                f"Matched {len(self._image_matches.matches)} images"
            )

            # Stage 4: Compose ads (image download + rendering)
            self._update_progress(PipelineStage.COMPOSING, 65, "Composing ad creatives")

            self._composed_ads = await workflow.execute_activity(
                compose_ads_activity,
                args=[
                    self._copy_variants.variants,
                    self._image_matches.matches,
                    config.url,  # destination_url - where ad clicks should go
                    config.output_dir,
                    config.formats,
                ],
                start_to_close_timeout=timedelta(minutes=10),  # Image processing can be slow
                retry_policy=DEFAULT_RETRY_POLICY,
            )

            self._update_progress(
                PipelineStage.COMPOSING, 80,
                f"Composed {len(self._composed_ads.ads)} ads"
            )

            # Stage 4.5: Upload composed ads to MinIO
            self._update_progress(PipelineStage.UPLOADING, 82, "Uploading ads to storage")

            upload_count = 0
            for ad in self._composed_ads.ads:
                for asset in ad.assets:
                    if asset.file_path:
                        try:
                            # Format name: convert "1:1" to "1x1"
                            format_name = asset.format.replace(":", "x") if asset.format else "default"

                            upload_result: UploadResult = await workflow.execute_activity(
                                upload_composed_ad_activity,
                                args=[
                                    workflow_id,  # campaign_id
                                    ad.copy_variant_id,  # variant_id
                                    asset.file_path,  # local_file_path
                                    format_name,  # format_name
                                ],
                                start_to_close_timeout=timedelta(minutes=2),
                                heartbeat_timeout=timedelta(seconds=30),
                                retry_policy=DEFAULT_RETRY_POLICY,
                            )

                            # Update asset with public MinIO URL (no expiration since bucket is public)
                            asset.file_url = upload_result.object_url
                            upload_count += 1

                        except Exception as e:
                            workflow.logger.warning(f"Failed to upload {asset.file_path}: {e}")
                            # Keep original local URL as fallback

            workflow.logger.info(f"Uploaded {upload_count} assets to MinIO")
            self._update_progress(PipelineStage.UPLOADING, 84, f"Uploaded {upload_count} assets")

            # Stage 5: Score variants (LLM-based scoring per variant)
            self._update_progress(PipelineStage.SCORING, 85, "Predicting performance")

            self._performance_scores = await workflow.execute_activity(
                predict_performance_activity,
                self._copy_variants.variants,
                start_to_close_timeout=timedelta(minutes=10),  # LLM call per variant
                retry_policy=LLM_RETRY_POLICY,
            )

            avg_score = sum(s.score for s in self._performance_scores.scores) / len(self._performance_scores.scores)
            self._update_progress(
                PipelineStage.SCORING, 95,
                f"Scored variants (avg: {avg_score:.0f}/100)"
            )

            # Save variants to database (with images and scores)
            if self._campaign_id:
                await workflow.execute_activity(
                    save_variants_activity,
                    args=[
                        self._campaign_id,
                        self._copy_variants.variants,
                        self._image_matches.matches,
                        self._performance_scores.scores,
                    ],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )

            # Complete - workflow is done, approval is handled via REST API
            self._stage = PipelineStage.COMPLETED
            self._progress_percent = 100
            self._message = "Pipeline complete"

            # Mark campaign as ready in database
            if self._campaign_id:
                await workflow.execute_activity(
                    complete_campaign_activity,
                    self._campaign_id,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=DEFAULT_RETRY_POLICY,
                )

            # Calculate duration using workflow.now() for determinism
            duration_ms = int((workflow.now() - start_time).total_seconds() * 1000)

            return PipelineResult(
                workflow_id=workflow_id,
                config=config,
                stage=self._stage.value,
                brand_profile=self._brand_profile,
                copy_variants=self._copy_variants,
                image_matches=self._image_matches,
                composed_ads=self._composed_ads,
                performance_scores=self._performance_scores,
                duration_ms=duration_ms,
                campaign_id=self._campaign_id,
            )

        except Exception as e:
            self._stage = PipelineStage.FAILED
            self._error = str(e)
            self._message = f"Pipeline failed: {e}"
            workflow.logger.error(f"Pipeline failed: {e}")

            # Mark campaign as failed in database
            if self._campaign_id:
                try:
                    await workflow.execute_activity(
                        fail_campaign_activity,
                        args=[self._campaign_id, str(e)],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=DEFAULT_RETRY_POLICY,
                    )
                except Exception as db_err:
                    workflow.logger.warning(f"Failed to update campaign status: {db_err}")

            return PipelineResult(
                workflow_id=workflow_id,
                config=config,
                stage=self._stage.value,
                brand_profile=self._brand_profile,
                copy_variants=self._copy_variants,
                image_matches=self._image_matches,
                composed_ads=self._composed_ads,
                performance_scores=self._performance_scores,
                error=str(e),
                duration_ms=int((workflow.now() - start_time).total_seconds() * 1000),
                campaign_id=self._campaign_id,
            )

    def _update_progress(self, stage: PipelineStage, percent: int, message: str):
        """Update progress state for queries."""
        self._stage = stage
        self._progress_percent = percent
        self._message = message
        workflow.logger.info(f"[{stage.value}] {percent}% - {message}")

    # Note: Approval signals removed. Approval is now handled via REST API
    # and database state. See POST /api/variants/{id}/approve

    @workflow.query
    def get_progress(self) -> PipelineProgress:
        """Query current progress."""
        return PipelineProgress(
            stage=self._stage.value,
            progress_percent=self._progress_percent,
            message=self._message,
            error=self._error,
        )

    @workflow.query
    def get_stage(self) -> str:
        """Query current stage."""
        return self._stage.value

    @workflow.query
    def get_brand_profile(self) -> Optional[BrandProfileResult]:
        """Query extracted brand profile."""
        return self._brand_profile

    @workflow.query
    def get_variants(self) -> Optional[CopyGenerationResult]:
        """Query generated variants."""
        return self._copy_variants

    @workflow.query
    def get_scores(self) -> Optional[PerformanceScoringResult]:
        """Query performance scores."""
        return self._performance_scores

    @workflow.query
    def get_image_matches(self) -> Optional[ImageMatchingResult]:
        """Query matched images."""
        return self._image_matches

    @workflow.query
    def get_composed_ads(self) -> Optional[AdCompositionResult]:
        """Query composed ad creatives."""
        return self._composed_ads

    @workflow.query
    def get_campaign_id(self) -> Optional[str]:
        """Query database campaign ID."""
        return self._campaign_id
