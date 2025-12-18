# src/api/variants.py
"""REST API endpoints for variant management.

These endpoints handle:
- Variant approval/rejection (for ad review workflow)
- Variant retrieval and updates
- Batch operations

Note: Generation workflow now completes after scoring. Approval is handled
separately via these REST endpoints, not workflow signals.
"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.db.client import get_database
from src.db.models import VariantStatus, VariantUpdate
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models
class VariantResponse(BaseModel):
    """Response model for a single variant."""
    id: str
    campaign_id: str
    headline: str
    primary_text: str
    cta: str
    angle: Optional[str] = None
    emotion: Optional[str] = None
    image_url: Optional[str] = None
    composed_url: Optional[str] = None
    score: Optional[int] = None
    score_details: Optional[dict] = None
    status: str
    created_at: str
    updated_at: str


class ApprovalResponse(BaseModel):
    """Response for approval/rejection operations."""
    success: bool
    variant_id: str
    status: str
    message: str


class BatchApprovalRequest(BaseModel):
    """Request for batch approval/rejection."""
    variant_ids: list[str] = Field(..., min_length=1, description="List of variant IDs")


class BatchApprovalResponse(BaseModel):
    """Response for batch operations."""
    success: bool
    approved_count: int
    failed_count: int
    results: list[ApprovalResponse]


def _variant_to_response(variant) -> VariantResponse:
    """Convert Variant dataclass to response model."""
    # Handle score_details which may be a JSON string or dict or None
    score_details = variant.score_details
    if isinstance(score_details, str):
        if score_details == "null" or not score_details:
            score_details = None
        else:
            try:
                score_details = json.loads(score_details)
            except (json.JSONDecodeError, TypeError):
                score_details = None

    return VariantResponse(
        id=variant.id,
        campaign_id=variant.campaign_id,
        headline=variant.headline,
        primary_text=variant.primary_text,
        cta=variant.cta,
        angle=variant.angle,
        emotion=variant.emotion,
        image_url=variant.image_url,
        composed_url=variant.composed_url,
        score=variant.score,
        score_details=score_details,
        status=variant.status.value,
        created_at=variant.created_at.isoformat(),
        updated_at=variant.updated_at.isoformat(),
    )


# =========================================================================
# STATIC ROUTES (must come before parameterized routes)
# =========================================================================

@router.post("/batch/approve", response_model=BatchApprovalResponse)
async def batch_approve_variants(request: BatchApprovalRequest):
    """Approve multiple variants at once.

    Args:
        request: List of variant IDs to approve

    Returns:
        Batch operation results
    """
    logger.info(f"Batch approving {len(request.variant_ids)} variants")
    db = get_database()

    results = []
    approved_count = 0
    failed_count = 0

    for variant_id in request.variant_ids:
        try:
            updated = await db.approve_variant(variant_id)
            if updated:
                results.append(ApprovalResponse(
                    success=True,
                    variant_id=variant_id,
                    status=updated.status.value,
                    message="Approved",
                ))
                approved_count += 1
            else:
                results.append(ApprovalResponse(
                    success=False,
                    variant_id=variant_id,
                    status="UNKNOWN",
                    message="Variant not found",
                ))
                failed_count += 1
        except Exception as e:
            results.append(ApprovalResponse(
                success=False,
                variant_id=variant_id,
                status="ERROR",
                message=str(e),
            ))
            failed_count += 1

    logger.info(f"Batch approve complete: {approved_count} approved, {failed_count} failed")
    return BatchApprovalResponse(
        success=failed_count == 0,
        approved_count=approved_count,
        failed_count=failed_count,
        results=results,
    )


@router.post("/batch/reject", response_model=BatchApprovalResponse)
async def batch_reject_variants(request: BatchApprovalRequest):
    """Reject multiple variants at once.

    Args:
        request: List of variant IDs to reject

    Returns:
        Batch operation results
    """
    logger.info(f"Batch rejecting {len(request.variant_ids)} variants")
    db = get_database()

    results = []
    rejected_count = 0
    failed_count = 0

    for variant_id in request.variant_ids:
        try:
            updated = await db.reject_variant(variant_id)
            if updated:
                results.append(ApprovalResponse(
                    success=True,
                    variant_id=variant_id,
                    status=updated.status.value,
                    message="Rejected",
                ))
                rejected_count += 1
            else:
                results.append(ApprovalResponse(
                    success=False,
                    variant_id=variant_id,
                    status="UNKNOWN",
                    message="Variant not found",
                ))
                failed_count += 1
        except Exception as e:
            results.append(ApprovalResponse(
                success=False,
                variant_id=variant_id,
                status="ERROR",
                message=str(e),
            ))
            failed_count += 1

    logger.info(f"Batch reject complete: {rejected_count} rejected, {failed_count} failed")
    return BatchApprovalResponse(
        success=failed_count == 0,
        approved_count=rejected_count,  # reuse field for count
        failed_count=failed_count,
        results=results,
    )


@router.get("/campaign/{campaign_id}", response_model=list[VariantResponse])
async def get_campaign_variants(
    campaign_id: str,
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED"),
):
    """Get all variants for a campaign.

    Args:
        campaign_id: The campaign UUID
        status: Optional status filter

    Returns:
        List of variants for the campaign
    """
    db = get_database()
    variants = await db.get_campaign_variants(campaign_id)

    if status:
        try:
            status_filter = VariantStatus(status.upper())
            variants = [v for v in variants if v.status == status_filter]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be PENDING, APPROVED, or REJECTED",
            )

    return [_variant_to_response(v) for v in variants]


@router.get("/campaign/{campaign_id}/approved", response_model=list[VariantResponse])
async def get_approved_variants(campaign_id: str):
    """Get only approved variants for a campaign.

    Convenience endpoint for the publishing workflow.

    Args:
        campaign_id: The campaign UUID

    Returns:
        List of approved variants only
    """
    db = get_database()
    variants = await db.get_campaign_variants(campaign_id)
    approved = [v for v in variants if v.status == VariantStatus.APPROVED]
    return [_variant_to_response(v) for v in approved]


# =========================================================================
# PARAMETERIZED ROUTES (must come after static routes)
# =========================================================================

@router.get("/{variant_id}", response_model=VariantResponse)
async def get_variant(variant_id: str):
    """Get a single variant by ID.

    Args:
        variant_id: The variant UUID

    Returns:
        Variant details
    """
    db = get_database()
    variant = await db.get_variant(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail=f"Variant {variant_id} not found")

    return _variant_to_response(variant)


@router.post("/{variant_id}/approve", response_model=ApprovalResponse)
async def approve_variant(variant_id: str):
    """Approve a variant for publishing.

    This marks the variant as approved and eligible for inclusion in
    ad campaigns. Approved variants can be published to ad platforms.

    Args:
        variant_id: The variant UUID to approve

    Returns:
        Approval confirmation with updated status
    """
    logger.info(f"Approving variant: {variant_id}")
    db = get_database()

    # Check variant exists
    existing = await db.get_variant(variant_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Variant {variant_id} not found")

    # Approve
    updated = await db.approve_variant(variant_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to approve variant")

    logger.info(f"Approved variant {variant_id}")
    return ApprovalResponse(
        success=True,
        variant_id=variant_id,
        status=updated.status.value,
        message="Variant approved successfully",
    )


@router.post("/{variant_id}/reject", response_model=ApprovalResponse)
async def reject_variant(variant_id: str):
    """Reject a variant.

    This marks the variant as rejected. Rejected variants will not be
    included in publishing workflows.

    Args:
        variant_id: The variant UUID to reject

    Returns:
        Rejection confirmation with updated status
    """
    logger.info(f"Rejecting variant: {variant_id}")
    db = get_database()

    # Check variant exists
    existing = await db.get_variant(variant_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Variant {variant_id} not found")

    # Reject
    updated = await db.reject_variant(variant_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to reject variant")

    logger.info(f"Rejected variant {variant_id}")
    return ApprovalResponse(
        success=True,
        variant_id=variant_id,
        status=updated.status.value,
        message="Variant rejected",
    )


@router.post("/{variant_id}/reset", response_model=ApprovalResponse)
async def reset_variant_status(variant_id: str):
    """Reset a variant back to pending status.

    Useful for undoing an accidental approval or rejection.

    Args:
        variant_id: The variant UUID to reset

    Returns:
        Reset confirmation with updated status
    """
    logger.info(f"Resetting variant status: {variant_id}")
    db = get_database()

    existing = await db.get_variant(variant_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Variant {variant_id} not found")

    updated = await db.update_variant_status(variant_id, VariantStatus.PENDING)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to reset variant status")

    logger.info(f"Reset variant {variant_id} to PENDING")
    return ApprovalResponse(
        success=True,
        variant_id=variant_id,
        status=updated.status.value,
        message="Variant status reset to pending",
    )
