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
    get_pipeline_state,
    # approve_variants,  # Removed - approval now via REST API
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


# ApproveVariantsRequest removed - approval now via REST API on variants table
# See: POST /api/variants/{variant_id}/approve


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


# Get Result (current state or completed result)
@router.get("/result/{workflow_id}")
async def get_workflow_result(workflow_id: str):
    """Get the result or current state of a pipeline workflow.

    Returns current state for in-progress workflows.
    Returns full result for completed workflows.
    Note: Workflow completes after scoring - no approval wait.
    """
    # First, try to get current state (doesn't block)
    state = await get_pipeline_state(workflow_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found",
        )

    # For in-progress workflows, return current state without blocking
    in_progress_stages = ["extracting", "generating", "matching", "composing", "scoring",
                          "embedding_brand", "embedding_variants", "uploading"]
    if state.get("stage") in in_progress_stages:
        # Convert dataclass results to dicts if needed
        result = {
            "workflow_id": workflow_id,
            "stage": state.get("stage"),
            "progress_percent": state.get("progress_percent"),
            "message": state.get("message"),
            "error": state.get("error"),
            "campaign_id": state.get("campaign_id"),
        }

        # Add brand_profile
        bp = state.get("brand_profile")
        if bp:
            result["brand_profile"] = bp.__dict__ if hasattr(bp, "__dict__") else bp

        # Add copy_variants
        cv = state.get("copy_variants")
        if cv:
            if hasattr(cv, "variants"):
                result["copy_variants"] = {
                    "variants": [v.__dict__ if hasattr(v, "__dict__") else v for v in cv.variants],
                    "generation_time_ms": getattr(cv, "generation_time_ms", 0),
                }
            else:
                result["copy_variants"] = cv

        # Add performance_scores
        ps = state.get("performance_scores")
        if ps:
            if hasattr(ps, "scores"):
                result["performance_scores"] = {
                    "scores": [s.__dict__ if hasattr(s, "__dict__") else s for s in ps.scores],
                }
            else:
                result["performance_scores"] = ps

        # Add image_matches
        im = state.get("image_matches")
        if im:
            if hasattr(im, "matches"):
                result["image_matches"] = {
                    "matches": [m.__dict__ if hasattr(m, "__dict__") else m for m in im.matches],
                }
            else:
                result["image_matches"] = im

        # Add composed_ads (the actual rendered images)
        ca = state.get("composed_ads")
        if ca:
            if hasattr(ca, "ads"):
                result["composed_ads"] = {
                    "ads": [
                        {
                            **(a.__dict__ if hasattr(a, "__dict__") else a),
                            "assets": [
                                asset.__dict__ if hasattr(asset, "__dict__") else asset
                                for asset in (a.assets if hasattr(a, "assets") else [])
                            ]
                        }
                        for a in ca.ads
                    ],
                }
            else:
                result["composed_ads"] = ca

        return result

    # For completed/failed workflows, try to get full result
    result = await get_pipeline_result(workflow_id)

    if result is None:
        # Fall back to state
        return state

    # Handle both dict (from Temporal serialization) and dataclass results
    if isinstance(result, dict):
        return result

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
        # Note: approved_variant_ids removed - approval is now in database
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

                # Check if workflow is done (completed or failed)
                # Note: Workflow no longer waits for approval - it completes after scoring
                if progress.stage in ["completed", "failed"]:
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
# DEPRECATED: Workflow no longer waits for approval signals
# Approval is now handled via REST API on the variants table
# See: POST /api/variants/{variant_id}/approve
# @router.post("/approve/{workflow_id}")
# async def approve_workflow_variants(...):
#     """This endpoint is deprecated. Use /api/variants/{id}/approve instead."""
#     pass


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


# =============================================================================
# PUBLISH WORKFLOW ROUTES
# =============================================================================

class StartPublishRequest(BaseModel):
    """Request to start a publish workflow."""
    campaign_id: str = Field(..., description="Internal campaign ID")
    campaign_name: str = Field(..., description="Campaign name for Meta")
    destination_url: str = Field(..., description="Click-through URL")
    daily_budget: int = Field(3000, ge=100, description="Daily budget in cents")
    page_id: str = Field("demo_page", description="Facebook page ID")
    variants: list[dict] = Field(..., description="Variants to publish")

    # Targeting
    age_min: int = Field(18, ge=13, le=65)
    age_max: int = Field(65, ge=18, le=65)
    countries: list[str] = Field(default=["US"])

    # Settings
    auto_activate: bool = Field(False, description="Start campaign immediately")


class StartPublishResponse(BaseModel):
    """Response from starting a publish workflow."""
    workflow_id: str
    status: str
    message: str


@router.post("/publish/start", response_model=StartPublishResponse)
async def start_publish_workflow(request: StartPublishRequest):
    """Start a publish workflow to send ads to Meta.

    This workflow:
    1. Validates Meta credentials
    2. Uploads images to Meta
    3. Creates campaign and ad set
    4. Creates ads for each variant
    5. Optionally activates the campaign
    """
    from src.temporal.client import get_client
    from src.temporal.workflows.publish_workflow import PublishToMetaWorkflow, PublishConfig

    try:
        client = await get_client()

        # Generate workflow ID
        import uuid
        workflow_id = f"publish-{uuid.uuid4().hex[:8]}"

        # Create config
        config = PublishConfig(
            campaign_id=request.campaign_id,
            campaign_name=request.campaign_name,
            destination_url=request.destination_url,
            daily_budget=request.daily_budget,
            page_id=request.page_id,
            variants=request.variants,
            age_min=request.age_min,
            age_max=request.age_max,
            countries=request.countries,
            auto_activate=request.auto_activate,
        )

        # Start workflow
        handle = await client.start_workflow(
            PublishToMetaWorkflow.run,
            config,
            id=workflow_id,
            task_queue="brandtruth-pipeline",
        )

        logger.info(f"Started publish workflow: {workflow_id}")

        return StartPublishResponse(
            workflow_id=workflow_id,
            status="started",
            message=f"Publish workflow started for {len(request.variants)} variants",
        )

    except Exception as e:
        logger.error(f"Failed to start publish workflow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start publish workflow: {str(e)}",
        )


@router.get("/publish/progress/{workflow_id}")
async def get_publish_progress(workflow_id: str):
    """Get progress of a publish workflow."""
    from src.temporal.client import get_client

    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)

        progress = await handle.query("get_progress")
        return progress

    except Exception as e:
        logger.error(f"Failed to get publish progress: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Publish workflow {workflow_id} not found",
        )


@router.get("/publish/result/{workflow_id}")
async def get_publish_result(workflow_id: str):
    """Get result of a completed publish workflow."""
    from src.temporal.client import get_client

    try:
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)

        result = await handle.query("get_result")
        meta_ids = await handle.query("get_meta_ids")

        return {
            "workflow_id": workflow_id,
            "result": result,
            "meta_ids": meta_ids,
        }

    except Exception as e:
        logger.error(f"Failed to get publish result: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Publish workflow {workflow_id} not found",
        )
