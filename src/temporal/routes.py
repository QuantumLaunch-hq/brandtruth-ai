# src/temporal/routes.py
"""FastAPI routes for Temporal workflow management.

These routes provide HTTP endpoints for:
- Starting new pipeline workflows
- Querying workflow progress
- Streaming real-time progress via SSE
- Approving/rejecting variants
- Cancelling workflows

Usage:
    from src.temporal.routes import router as temporal_router
    app.include_router(temporal_router, prefix="/workflow", tags=["Temporal Workflows"])
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.temporal.client import (
    start_pipeline,
    get_pipeline_progress,
    get_pipeline_result,
    approve_variants,
    cancel_pipeline,
    is_temporal_available,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models
class StartPipelineRequest(BaseModel):
    """Request to start a new pipeline workflow."""
    url: str = Field(..., description="Website URL to process")
    num_variants: int = Field(5, ge=1, le=10, description="Number of variants to generate")
    platform: str = Field("meta", description="Target platform")
    user_id: Optional[str] = Field(None, description="User ID for database persistence")
    campaign_name: Optional[str] = Field(None, description="Campaign name")


class StartPipelineResponse(BaseModel):
    """Response from starting a pipeline."""
    workflow_id: str
    status: str = "started"
    message: str
    campaign_id: Optional[str] = None


class PipelineProgressResponse(BaseModel):
    """Response with pipeline progress."""
    workflow_id: str
    stage: str
    progress_percent: int
    message: str
    error: Optional[str] = None


class ApproveVariantsRequest(BaseModel):
    """Request to approve variants."""
    variant_ids: list[str]


# Health Check
@router.get("/health")
async def workflow_health():
    """Check if Temporal is available."""
    available = await is_temporal_available()
    return {
        "temporal_available": available,
        "status": "healthy" if available else "degraded",
        "message": "Temporal workflows enabled" if available else "Temporal unavailable - using fallback",
    }


# Start Pipeline
@router.post("/start", response_model=StartPipelineResponse)
async def start_workflow_pipeline(request: StartPipelineRequest):
    """Start a new ad generation pipeline workflow.

    This creates a durable workflow that:
    - Survives server restarts
    - Automatically retries on failures
    - Can be queried for progress
    - Supports approval signals
    - Persists to database if user_id is provided

    Returns workflow_id for tracking.
    """
    try:
        workflow_id = await start_pipeline(
            url=request.url,
            num_variants=request.num_variants,
            platform=request.platform,
            user_id=request.user_id,
            campaign_name=request.campaign_name,
        )

        return StartPipelineResponse(
            workflow_id=workflow_id,
            status="started",
            message=f"Pipeline started for {request.url}",
            campaign_id=None,  # Campaign ID is created async by workflow, query later
        )

    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to start workflow: {str(e)}. Is Temporal running?",
        )


# Get Progress
@router.get("/progress/{workflow_id}", response_model=PipelineProgressResponse)
async def get_workflow_progress(workflow_id: str):
    """Get current progress of a pipeline workflow."""
    progress = await get_pipeline_progress(workflow_id)

    if progress is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )

    return PipelineProgressResponse(
        workflow_id=workflow_id,
        stage=progress.stage,
        progress_percent=progress.progress_percent,
        message=progress.message,
        error=progress.error,
    )


# Get Result
@router.get("/result/{workflow_id}")
async def get_workflow_result(workflow_id: str):
    """Get the complete result of a finished pipeline workflow."""
    result = await get_pipeline_result(workflow_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found or not complete",
        )

    # Convert dataclasses to dicts for JSON response
    return {
        "workflow_id": result.workflow_id,
        "stage": result.stage,
        "config": {
            "url": result.config.url,
            "num_variants": result.config.num_variants,
            "platform": result.config.platform,
        },
        "brand_profile": result.brand_profile.__dict__ if result.brand_profile else None,
        "copy_variants": {
            "variants": [v.__dict__ for v in result.copy_variants.variants],
            "generation_time_ms": result.copy_variants.generation_time_ms,
        } if result.copy_variants else None,
        "image_matches": {
            "matches": [m.__dict__ for m in result.image_matches.matches],
        } if result.image_matches else None,
        "composed_ads": {
            "ads": [
                {**a.__dict__, "assets": [asset.__dict__ for asset in a.assets]}
                for a in result.composed_ads.ads
            ],
        } if result.composed_ads else None,
        "performance_scores": {
            "scores": [s.__dict__ for s in result.performance_scores.scores],
        } if result.performance_scores else None,
        "approved_variant_ids": result.approved_variant_ids,
        "error": result.error,
        "duration_ms": result.duration_ms,
        "campaign_id": result.campaign_id,
    }


# Stream Progress (SSE)
@router.get("/stream/{workflow_id}")
async def stream_workflow_progress(workflow_id: str):
    """Stream real-time progress updates via Server-Sent Events.

    Connect to this endpoint to receive progress updates as they happen.
    The stream closes when the workflow completes or fails.

    Example client:
        const eventSource = new EventSource('/workflow/stream/pipeline-123');
        eventSource.onmessage = (e) => console.log(JSON.parse(e.data));
    """

    async def event_generator():
        last_stage = None
        last_percent = None
        retries = 0
        max_retries = 300  # 5 minutes with 1-second polls
        initial_retries = 0
        max_initial_retries = 10  # Wait up to 10 seconds for workflow to register

        while retries < max_retries:
            try:
                progress = await get_pipeline_progress(workflow_id)

                if progress is None:
                    # Workflow might still be starting - retry a few times
                    initial_retries += 1
                    if initial_retries <= max_initial_retries:
                        await asyncio.sleep(1)
                        continue
                    # After retries, workflow really doesn't exist
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Workflow not found"}),
                    }
                    break

                # Only send if changed
                if progress.stage != last_stage or progress.progress_percent != last_percent:
                    last_stage = progress.stage
                    last_percent = progress.progress_percent

                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "workflow_id": workflow_id,
                            "stage": progress.stage,
                            "progress_percent": progress.progress_percent,
                            "message": progress.message,
                            "error": progress.error,
                        }),
                    }

                # Check if complete
                if progress.stage in ["completed", "failed", "approved"]:
                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "workflow_id": workflow_id,
                            "stage": progress.stage,
                            "message": progress.message,
                        }),
                    }
                    break

                await asyncio.sleep(1)  # Poll every second
                retries += 1

            except Exception as e:
                logger.error(f"SSE error for {workflow_id}: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)}),
                }
                break

        # Stream timeout
        if retries >= max_retries:
            yield {
                "event": "timeout",
                "data": json.dumps({"message": "Stream timeout"}),
            }

    return EventSourceResponse(event_generator())


# Approve Variants
@router.post("/approve/{workflow_id}")
async def approve_workflow_variants(workflow_id: str, request: ApproveVariantsRequest):
    """Approve specific variants in a workflow.

    This sends a signal to the workflow to approve the specified variants.
    The workflow will then proceed to completion.
    """
    success = await approve_variants(workflow_id, request.variant_ids)

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve variants for {workflow_id}",
        )

    return {
        "workflow_id": workflow_id,
        "approved_variants": request.variant_ids,
        "status": "approved",
    }


# Cancel Workflow
@router.post("/cancel/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel a running workflow."""
    success = await cancel_pipeline(workflow_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel workflow {workflow_id}",
        )

    return {
        "workflow_id": workflow_id,
        "status": "cancelled",
    }
