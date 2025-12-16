# src/pipeline/orchestrator.py
"""Pipeline Orchestrator for BrandTruth AI - Slice 7

Connects all slices into a unified end-to-end workflow:
URL → Brand Extraction → Copy Generation → Image Matching → Ad Composition → HITL → Export

Features:
- Async pipeline execution
- Progress callbacks for UI updates
- Error handling with partial results
- Job persistence for long-running tasks
- Batch processing support
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

# Import all slice modules
from src.extractors.brand_extractor import extract_brand
from src.generators.copy_generator import generate_copy, CopyGenerationResult
from src.composers.image_matcher_v2 import match_images_v2
from src.composers.ad_composer import compose_ads
from src.extractors.sentiment_monitor import SentimentMonitor, SentimentMonitorConfig, create_mock_mentions
from src.models.brand_profile import BrandProfile
from src.models.copy_variant import CopyVariant, Platform
from src.models.composed_ad import ComposedAd, AdFormat
from src.models.sentiment import SentimentSnapshot, SentimentAlert
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PipelineStage(str, Enum):
    """Pipeline execution stages."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    GENERATING = "generating"
    MATCHING = "matching"
    COMPOSING = "composing"
    CHECKING_SENTIMENT = "checking_sentiment"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class PipelineConfig(BaseModel):
    """Configuration for a pipeline run."""
    url: str
    num_variants: int = 5
    platform: Platform = Platform.META
    objective: str = "conversions"
    formats: list[AdFormat] = Field(default_factory=lambda: [AdFormat.SQUARE])
    use_vision_matching: bool = True
    check_sentiment: bool = True
    auto_pause_on_crisis: bool = True
    output_dir: str = "./output"


class PipelineProgress(BaseModel):
    """Progress update for pipeline execution."""
    job_id: str
    stage: PipelineStage
    progress_percent: int = 0
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None


class PipelineResult(BaseModel):
    """Complete result of a pipeline run."""
    job_id: str
    config: PipelineConfig
    stage: PipelineStage
    
    # Results from each stage
    brand_profile: Optional[dict] = None
    copy_variants: list[dict] = Field(default_factory=list)
    image_matches: dict[str, dict] = Field(default_factory=dict)
    composed_ads: list[dict] = Field(default_factory=list)
    sentiment_snapshot: Optional[dict] = None
    sentiment_alerts: list[dict] = Field(default_factory=list)
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    
    # HITL status
    approved_variant_ids: list[str] = Field(default_factory=list)
    rejected_variant_ids: list[str] = Field(default_factory=list)
    
    def get_approved_ads(self) -> list[dict]:
        """Get only approved composed ads."""
        return [
            ad for ad in self.composed_ads 
            if ad.get("copy_variant_id") in self.approved_variant_ids
        ]


class PipelineOrchestrator:
    """Orchestrates the complete ad generation pipeline."""
    
    def __init__(
        self,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
        jobs_dir: str = "./jobs"
    ):
        self.progress_callback = progress_callback
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(exist_ok=True)
        
        # Active jobs in memory
        self._active_jobs: dict[str, PipelineResult] = {}
    
    def _emit_progress(self, job_id: str, stage: PipelineStage, percent: int, message: str, error: str = None):
        """Emit a progress update."""
        progress = PipelineProgress(
            job_id=job_id,
            stage=stage,
            progress_percent=percent,
            message=message,
            error=error,
        )
        logger.info(f"[{job_id}] {stage.value}: {message} ({percent}%)")
        
        if self.progress_callback:
            self.progress_callback(progress)
        
        return progress
    
    def _save_job(self, result: PipelineResult):
        """Save job result to disk."""
        job_path = self.jobs_dir / f"{result.job_id}.json"
        with open(job_path, "w") as f:
            f.write(result.model_dump_json(indent=2))
    
    def load_job(self, job_id: str) -> Optional[PipelineResult]:
        """Load a job result from disk or memory."""
        if job_id in self._active_jobs:
            return self._active_jobs[job_id]
        
        job_path = self.jobs_dir / f"{job_id}.json"
        if job_path.exists():
            with open(job_path) as f:
                return PipelineResult.model_validate_json(f.read())
        
        return None
    
    async def run_pipeline(self, config: PipelineConfig) -> PipelineResult:
        """
        Run the complete ad generation pipeline.
        
        Stages:
        1. Extract brand profile from URL
        2. Generate copy variants
        3. Match images for each variant
        4. Compose final ads
        5. Check sentiment (optional)
        6. Ready for HITL review
        """
        job_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        result = PipelineResult(
            job_id=job_id,
            config=config,
            stage=PipelineStage.PENDING,
        )
        self._active_jobs[job_id] = result
        
        try:
            # Stage 1: Brand Extraction
            self._emit_progress(job_id, PipelineStage.EXTRACTING, 10, f"Extracting brand from {config.url}")
            result.stage = PipelineStage.EXTRACTING
            
            brand_profile = await extract_brand(config.url)
            result.brand_profile = {
                "brand_name": brand_profile.brand_name,
                "tagline": brand_profile.tagline,
                "industry": brand_profile.industry,
                "value_propositions": brand_profile.value_propositions,
                "claims": [
                    {
                        "claim": c.claim,
                        "source": c.source_text,
                        "risk_level": c.risk_level.value,
                    }
                    for c in brand_profile.claims
                ],
                "tone_markers": [
                    {"tone": t.category.value, "confidence": t.confidence}
                    for t in brand_profile.tone_markers
                ],
                "confidence_score": brand_profile.confidence_score,
            }
            
            self._emit_progress(job_id, PipelineStage.EXTRACTING, 25, f"Extracted: {brand_profile.brand_name}")
            
            # Stage 2: Copy Generation
            self._emit_progress(job_id, PipelineStage.GENERATING, 30, f"Generating {config.num_variants} ad variants")
            result.stage = PipelineStage.GENERATING
            
            copy_result = generate_copy(
                brand_profile=brand_profile,
                objective=config.objective,
                platform=config.platform,
                num_variants=config.num_variants,
            )
            
            result.copy_variants = [
                {
                    "id": v.id,
                    "headline": v.headline,
                    "primary_text": v.primary_text,
                    "cta": v.cta,
                    "angle": v.angle.value,
                    "emotion": v.emotion.value,
                    "persona": v.persona,
                    "quality_score": v.quality_score,
                    "claims_used": v.brand_claims_used,
                }
                for v in copy_result.variants
            ]
            
            self._emit_progress(job_id, PipelineStage.GENERATING, 45, f"Generated {len(copy_result.variants)} variants")
            
            # Stage 3: Image Matching
            self._emit_progress(job_id, PipelineStage.MATCHING, 50, "Matching images with vision AI")
            result.stage = PipelineStage.MATCHING
            
            if config.use_vision_matching and os.getenv("UNSPLASH_ACCESS_KEY"):
                image_result = match_images_v2(
                    copy_variants=copy_result.variants,
                    images_per_variant=1,
                )
            else:
                from src.composers.image_matcher import match_images
                image_result = match_images(
                    copy_variants=copy_result.variants,
                    images_per_variant=1,
                )
            
            # Build image matches dict - keep actual ImageMatch objects for composer
            image_matches_for_composer = {}
            for match_result in image_result.results:
                best = match_result.get_best_match()
                if best:
                    # Store serialized data for result (API response)
                    result.image_matches[match_result.copy_variant_id] = {
                        "image_url": best.image_url,
                        "relevance_score": best.relevance_score or best.match_score,
                        "photographer": best.photographer,
                        "photographer_url": best.photographer_url,
                    }
                    # Keep actual ImageMatch object for composer
                    image_matches_for_composer[match_result.copy_variant_id] = best

            self._emit_progress(job_id, PipelineStage.MATCHING, 65, f"Matched {len(result.image_matches)} images")

            # Stage 4: Ad Composition
            self._emit_progress(job_id, PipelineStage.COMPOSING, 70, "Composing final ad creatives")
            result.stage = PipelineStage.COMPOSING

            composition_result = compose_ads(
                copy_variants=copy_result.variants,
                image_matches=image_matches_for_composer,
                output_dir=config.output_dir,
                formats=config.formats,
            )
            
            result.composed_ads = [
                {
                    "id": ad.id,
                    "copy_variant_id": ad.copy_variant_id,
                    "assets": {
                        fmt: {
                            "file_path": asset.file_path,
                            "width": asset.width,
                            "height": asset.height,
                        }
                        for fmt, asset in ad.assets.items()
                    },
                    "headline": ad.headline,
                    "primary_text": ad.primary_text,
                    "cta": ad.cta,
                }
                for ad in composition_result.ads
            ]
            
            self._emit_progress(job_id, PipelineStage.COMPOSING, 85, f"Composed {len(composition_result.ads)} ads")
            
            # Stage 5: Sentiment Check (optional)
            if config.check_sentiment:
                self._emit_progress(job_id, PipelineStage.CHECKING_SENTIMENT, 90, "Checking brand sentiment")
                result.stage = PipelineStage.CHECKING_SENTIMENT
                
                sentiment_config = SentimentMonitorConfig(
                    brand_name=brand_profile.brand_name,
                    monitor_twitter=False,  # Use mock for now
                    monitor_news=False,
                    auto_pause_rules=[],
                )
                
                monitor = SentimentMonitor(sentiment_config)
                
                # Use mock data for demo (real APIs would be used in production)
                mentions = create_mock_mentions(brand_profile.brand_name, "normal")
                snapshot = await monitor.create_snapshot(mentions)
                alerts = monitor.check_alerts(snapshot)
                
                result.sentiment_snapshot = {
                    "health_status": snapshot.get_health_status(),
                    "overall_score": snapshot.overall_score,
                    "total_mentions": snapshot.total_mentions,
                    "positive": snapshot.positive_mentions,
                    "negative": snapshot.negative_mentions,
                    "neutral": snapshot.neutral_mentions,
                    "is_crisis": snapshot.is_crisis(),
                }
                
                result.sentiment_alerts = [
                    {
                        "severity": a.severity.value,
                        "reason": a.trigger_reason,
                        "action": a.recommended_action,
                    }
                    for a in alerts
                ]
                
                # Auto-pause check
                if config.auto_pause_on_crisis and snapshot.is_crisis():
                    self._emit_progress(
                        job_id, PipelineStage.CHECKING_SENTIMENT, 95,
                        "⚠️ Crisis detected - ads should be paused"
                    )
            
            # Ready for review
            result.stage = PipelineStage.READY_FOR_REVIEW
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - start_time).total_seconds()
            
            self._emit_progress(job_id, PipelineStage.READY_FOR_REVIEW, 100, "Pipeline complete - ready for review")
            self._save_job(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            result.stage = PipelineStage.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - start_time).total_seconds()
            
            self._emit_progress(job_id, PipelineStage.FAILED, 0, f"Pipeline failed: {e}", error=str(e))
            self._save_job(result)
            
            return result
    
    def approve_variant(self, job_id: str, variant_id: str) -> bool:
        """Approve a variant for export/publishing."""
        result = self.load_job(job_id)
        if not result:
            return False
        
        if variant_id not in result.approved_variant_ids:
            result.approved_variant_ids.append(variant_id)
        
        if variant_id in result.rejected_variant_ids:
            result.rejected_variant_ids.remove(variant_id)
        
        self._save_job(result)
        return True
    
    def reject_variant(self, job_id: str, variant_id: str) -> bool:
        """Reject a variant."""
        result = self.load_job(job_id)
        if not result:
            return False
        
        if variant_id not in result.rejected_variant_ids:
            result.rejected_variant_ids.append(variant_id)
        
        if variant_id in result.approved_variant_ids:
            result.approved_variant_ids.remove(variant_id)
        
        self._save_job(result)
        return True
    
    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get current status of a job."""
        result = self.load_job(job_id)
        if not result:
            return None
        
        return {
            "job_id": result.job_id,
            "stage": result.stage.value,
            "brand_name": result.brand_profile.get("brand_name") if result.brand_profile else None,
            "variants_count": len(result.copy_variants),
            "approved_count": len(result.approved_variant_ids),
            "rejected_count": len(result.rejected_variant_ids),
            "has_sentiment_alert": len(result.sentiment_alerts) > 0,
            "duration_seconds": result.duration_seconds,
            "error": result.error,
        }
    
    def list_jobs(self, limit: int = 20) -> list[dict]:
        """List recent jobs."""
        jobs = []
        
        # Get from disk
        job_files = sorted(self.jobs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        for job_file in job_files[:limit]:
            try:
                with open(job_file) as f:
                    result = PipelineResult.model_validate_json(f.read())
                    jobs.append(self.get_job_status(result.job_id))
            except Exception as e:
                logger.warning(f"Failed to load job {job_file}: {e}")
        
        return jobs


# Convenience function for simple usage
async def run_ad_pipeline(
    url: str,
    num_variants: int = 5,
    platform: str = "meta",
    check_sentiment: bool = True,
) -> PipelineResult:
    """
    Simple function to run the complete pipeline.
    
    Example:
        result = await run_ad_pipeline("https://careerfied.ai", num_variants=5)
        print(f"Generated {len(result.composed_ads)} ads")
    """
    config = PipelineConfig(
        url=url,
        num_variants=num_variants,
        platform=Platform(platform),
        check_sentiment=check_sentiment,
    )
    
    orchestrator = PipelineOrchestrator()
    return await orchestrator.run_pipeline(config)


if __name__ == "__main__":
    import sys
    
    async def main():
        url = sys.argv[1] if len(sys.argv) > 1 else "https://careerfied.ai"
        
        print(f"\n{'='*60}")
        print("BRANDTRUTH AI - PIPELINE ORCHESTRATOR")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        def progress_handler(progress: PipelineProgress):
            print(f"[{progress.stage.value.upper():20}] {progress.progress_percent:3}% | {progress.message}")
        
        orchestrator = PipelineOrchestrator(progress_callback=progress_handler)
        
        config = PipelineConfig(
            url=url,
            num_variants=3,
            check_sentiment=True,
        )
        
        result = await orchestrator.run_pipeline(config)
        
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Job ID:          {result.job_id}")
        print(f"Status:          {result.stage.value}")
        print(f"Duration:        {result.duration_seconds:.1f}s")
        print(f"Brand:           {result.brand_profile.get('brand_name') if result.brand_profile else 'N/A'}")
        print(f"Variants:        {len(result.copy_variants)}")
        print(f"Composed Ads:    {len(result.composed_ads)}")
        
        if result.sentiment_snapshot:
            print(f"\nSentiment:       {result.sentiment_snapshot.get('health_status')}")
            print(f"Score:           {result.sentiment_snapshot.get('overall_score'):.2f}")
        
        if result.error:
            print(f"\nError:           {result.error}")
        
        print(f"\n{'='*60}\n")
        
        return result
    
    asyncio.run(main())
