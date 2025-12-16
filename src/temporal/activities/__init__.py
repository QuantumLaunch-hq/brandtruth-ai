# src/temporal/activities/__init__.py
"""Temporal Activities for BrandTruth AI pipeline stages.

Each activity wraps an existing pipeline module, making it:
- Retriable with configurable backoff
- Independently checkpointed
- Observable via Temporal UI
- Measurable for latency and cost tracking
"""

from .extract import extract_brand_activity
from .generate import generate_copy_activity
from .match import match_images_activity
from .compose import compose_ads_activity
from .score import predict_performance_activity

__all__ = [
    "extract_brand_activity",
    "generate_copy_activity",
    "match_images_activity",
    "compose_ads_activity",
    "predict_performance_activity",
]
