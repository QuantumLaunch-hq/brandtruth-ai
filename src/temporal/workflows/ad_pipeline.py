# src/temporal/workflows/ad_pipeline.py
"""Ad Pipeline Workflow for BrandTruth AI.

This is the main durable workflow that orchestrates the entire ad generation pipeline.
Unlike the current synchronous orchestrator, this workflow:

1. Survives crashes - resumes from last successful step
2. Has automatic retries - each activity retries independently
3. Supports long waits - can pause for human approval for days
4. Provides real-time progress - queryable state at any time
5. Is observable - full history in Temporal UI

Workflow Stages:
1. extract_brand - Extract brand profile from URL
2. generate_copy - Generate copy variants
3. match_images - Match images to variants (parallel)
4. compose_ads - Compose final ad creatives
5. score_variants - Predict performance scores
6. wait_for_approval - Wait for human approval (signal)
7. complete - Workflow complete
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


class PipelineStage(str, Enum):
    """Pipeline execution stages for progress tracking."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    GENERATING = "generating"
    MATCHING = "matching"
    COMPOSING = "composing"
    SCORING = "scoring"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
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
    """Complete result of the pipeline workflow."""
    workflow_id: str
    config: PipelineConfig
    stage: str
    brand_profile: Optional[BrandProfileResult] = None
    copy_variants: Optional[CopyGenerationResult] = None
    image_matches: Optional[ImageMatchingResult] = None
    composed_ads: Optional[AdCompositionResult] = None
    performance_scores: Optional[PerformanceScoringResult] = None
    approved_variant_ids: list[str] | None = None
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

        # Approval state
        self._approved_variant_ids: list[str] = []
        self._approval_received = False

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

            # Stage 6: Await approval (optional - can be skipped)
            self._update_progress(
                PipelineStage.AWAITING_APPROVAL, 98,
                "Ready for review - awaiting approval"
            )

            # Wait up to 7 days for approval signal
            # In production, you might skip this and let frontend handle approval
            try:
                await workflow.wait_condition(
                    lambda: self._approval_received,
                    timeout=timedelta(days=7),
                )
                self._update_progress(
                    PipelineStage.APPROVED, 100,
                    f"Approved {len(self._approved_variant_ids)} variants"
                )
            except TimeoutError:
                # Timeout is fine - auto-complete without explicit approval
                workflow.logger.info("Approval timeout - completing without explicit approval")

            # Complete
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
                approved_variant_ids=self._approved_variant_ids or None,
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

    @workflow.signal
    def approve_variants(self, variant_ids: list[str]):
        """Signal to approve specific variants."""
        self._approved_variant_ids = variant_ids
        self._approval_received = True
        workflow.logger.info(f"Approved variants: {variant_ids}")

    @workflow.signal
    def reject_all(self):
        """Signal to reject all variants and cancel workflow."""
        self._approved_variant_ids = []
        self._approval_received = True
        workflow.logger.info("All variants rejected")

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
    def get_campaign_id(self) -> Optional[str]:
        """Query database campaign ID."""
        return self._campaign_id
