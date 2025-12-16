# src/temporal/__init__.py
"""Temporal workflow infrastructure for BrandTruth AI.

This module provides durable workflow execution for the ad generation pipeline.
Each pipeline stage is wrapped as a Temporal Activity, and the AdPipelineWorkflow
orchestrates them with automatic retry, checkpointing, and progress tracking.

Benefits over the current synchronous orchestrator:
- Workflows survive crashes and server restarts
- Automatic retries with exponential backoff
- Step-by-step execution with checkpoints
- Real-time progress streaming to frontend
- Support for long-running workflows (days/weeks)
- Human-in-the-loop approval with signal/wait patterns
"""

from .workflows.ad_pipeline import AdPipelineWorkflow
from .activities.extract import extract_brand_activity
from .activities.generate import generate_copy_activity
from .activities.match import match_images_activity
from .activities.compose import compose_ads_activity
from .activities.score import predict_performance_activity

__all__ = [
    "AdPipelineWorkflow",
    "extract_brand_activity",
    "generate_copy_activity",
    "match_images_activity",
    "compose_ads_activity",
    "predict_performance_activity",
]
