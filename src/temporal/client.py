# src/temporal/client.py
"""Temporal Client utilities for BrandTruth AI API.

This module provides helper functions for interacting with Temporal workflows
from the FastAPI server.
"""

import os
from typing import Optional
from contextlib import asynccontextmanager

from temporalio.client import Client, WorkflowHandle

from src.temporal.workflows.ad_pipeline import (
    AdPipelineWorkflow,
    PipelineConfig,
    PipelineProgress,
    PipelineResult,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "brandtruth-pipeline")

# Global client instance
_client: Optional[Client] = None


async def get_client() -> Client:
    """Get or create a Temporal client."""
    global _client

    if _client is None:
        logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}")
        _client = await Client.connect(
            TEMPORAL_HOST,
            namespace=TEMPORAL_NAMESPACE,
        )
        logger.info("Temporal client connected")

    return _client


async def close_client():
    """Close the Temporal client."""
    global _client

    if _client is not None:
        await _client.close()
        _client = None
        logger.info("Temporal client closed")


@asynccontextmanager
async def temporal_client():
    """Context manager for Temporal client."""
    client = await get_client()
    try:
        yield client
    finally:
        pass  # Don't close - reuse connection


async def start_pipeline(
    url: str,
    num_variants: int = 5,
    platform: str = "meta",
    workflow_id: Optional[str] = None,
    user_id: Optional[str] = None,
    campaign_name: Optional[str] = None,
) -> str:
    """Start a new ad pipeline workflow.

    Args:
        url: Website URL to process
        num_variants: Number of ad variants to generate
        platform: Target platform (meta, google, tiktok)
        workflow_id: Optional custom workflow ID
        user_id: Optional user ID for database persistence
        campaign_name: Optional campaign name for database

    Returns:
        Workflow ID for tracking

    Raises:
        Exception: If Temporal is unavailable
    """
    client = await get_client()

    config = PipelineConfig(
        url=url,
        num_variants=num_variants,
        platform=platform,
        user_id=user_id,
        campaign_name=campaign_name,
    )

    # Generate workflow ID if not provided
    if workflow_id is None:
        import uuid
        workflow_id = f"pipeline-{uuid.uuid4().hex[:8]}"

    logger.info(f"Starting pipeline workflow: {workflow_id} (user: {user_id or 'anonymous'})")

    # Start workflow
    handle = await client.start_workflow(
        AdPipelineWorkflow.run,
        config,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    logger.info(f"Pipeline started: {workflow_id}")
    return workflow_id


async def get_pipeline_progress(workflow_id: str) -> Optional[PipelineProgress]:
    """Get current progress of a pipeline workflow.

    Args:
        workflow_id: Workflow ID to query

    Returns:
        PipelineProgress or None if not found
    """
    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        progress = await handle.query(AdPipelineWorkflow.get_progress)
        return progress
    except Exception as e:
        logger.warning(f"Failed to get progress for {workflow_id}: {e}")
        return None


async def get_pipeline_state(workflow_id: str) -> Optional[dict]:
    """Get current state of a pipeline workflow by querying (doesn't wait for completion).

    Use this when workflow is in 'awaiting_approval' stage to get variants/ads without blocking.

    Args:
        workflow_id: Workflow ID to query

    Returns:
        Dict with current workflow state or None if not found
    """
    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)

        # Query all available state
        progress = await handle.query(AdPipelineWorkflow.get_progress)
        brand_profile = await handle.query(AdPipelineWorkflow.get_brand_profile)
        variants = await handle.query(AdPipelineWorkflow.get_variants)
        scores = await handle.query(AdPipelineWorkflow.get_scores)
        image_matches = await handle.query(AdPipelineWorkflow.get_image_matches)
        composed_ads = await handle.query(AdPipelineWorkflow.get_composed_ads)
        campaign_id = await handle.query(AdPipelineWorkflow.get_campaign_id)

        return {
            "workflow_id": workflow_id,
            "stage": progress.stage if progress else "unknown",
            "progress_percent": progress.progress_percent if progress else 0,
            "message": progress.message if progress else "",
            "error": progress.error if progress else None,
            "brand_profile": brand_profile,
            "copy_variants": variants,
            "image_matches": image_matches,
            "composed_ads": composed_ads,
            "performance_scores": scores,
            "campaign_id": campaign_id,
        }
    except Exception as e:
        logger.warning(f"Failed to get state for {workflow_id}: {e}")
        return None


async def get_pipeline_result(workflow_id: str) -> Optional[PipelineResult]:
    """Get the result of a completed pipeline workflow (blocks until complete).

    WARNING: This blocks until workflow finishes. Use get_pipeline_state() for
    'awaiting_approval' workflows.

    Args:
        workflow_id: Workflow ID to get result for

    Returns:
        PipelineResult or None if not complete/found
    """
    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.result()
        return result
    except Exception as e:
        logger.warning(f"Failed to get result for {workflow_id}: {e}")
        return None


async def approve_variants(workflow_id: str, variant_ids: list[str]) -> bool:
    """Send approval signal to a pipeline workflow.

    Args:
        workflow_id: Workflow ID to signal
        variant_ids: List of variant IDs to approve

    Returns:
        True if signal sent successfully
    """
    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(AdPipelineWorkflow.approve_variants, variant_ids)
        logger.info(f"Approved variants for {workflow_id}: {variant_ids}")
        return True
    except Exception as e:
        logger.error(f"Failed to approve variants for {workflow_id}: {e}")
        return False


async def cancel_pipeline(workflow_id: str) -> bool:
    """Cancel a running pipeline workflow.

    Args:
        workflow_id: Workflow ID to cancel

    Returns:
        True if cancelled successfully
    """
    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.cancel()
        logger.info(f"Cancelled pipeline: {workflow_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel {workflow_id}: {e}")
        return False


async def is_temporal_available() -> bool:
    """Check if Temporal server is available.

    Returns:
        True if Temporal is reachable
    """
    try:
        client = await get_client()
        # Try a simple operation - list namespaces to verify connection
        from temporalio.api.workflowservice.v1 import GetSystemInfoRequest
        await client.workflow_service.get_system_info(GetSystemInfoRequest())
        return True
    except Exception as e:
        logger.warning(f"Temporal not available: {e}")
        return False
