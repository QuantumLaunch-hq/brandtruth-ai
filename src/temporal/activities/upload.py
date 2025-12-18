# src/temporal/activities/upload.py
"""MinIO upload activities for Temporal workflow.

This activity handles uploading composed ad images to MinIO with:
- Progress tracking via heartbeats
- Idempotent uploads (checks if already exists)
- Presigned URL generation for frontend access

Enterprise Patterns:
- Heartbeats every operation for cancellation support
- Idempotency: checks existence before upload
- Retryable transient errors vs non-retryable validation errors
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import os

from temporalio import activity
from temporalio.exceptions import ApplicationError

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UploadResult:
    """Result of uploading an asset to MinIO."""

    object_url: str  # Public URL (via MinIO)
    presigned_url: str  # Time-limited URL for browser
    bucket: str
    object_key: str
    size_bytes: int


@dataclass
class BatchUploadResult:
    """Result of batch upload operation."""

    uploads: list[UploadResult]
    total_bytes: int


@activity.defn
async def upload_composed_ad_activity(
    campaign_id: str,
    variant_id: str,
    local_file_path: str,
    format_name: str,
) -> UploadResult:
    """Upload a composed ad image to MinIO.

    Uses heartbeats to report progress. Automatically retried by Temporal
    on transient failures (network issues). Non-retryable on validation
    errors (file not found).

    Args:
        campaign_id: Campaign UUID
        variant_id: Variant UUID
        local_file_path: Path to rendered image
        format_name: Format identifier (e.g., "1x1", "4x5", "9x16")

    Returns:
        UploadResult with URLs and metadata

    Raises:
        ApplicationError: On validation errors (non-retryable)
        Exception: On transient errors (retryable)
    """
    from src.storage.minio_client import get_minio_client, MinIOConfig

    activity.logger.info(f"Uploading {format_name} for variant {variant_id}")

    # Check for resumption
    heartbeat_details = activity.info().heartbeat_details
    if heartbeat_details:
        checkpoint = heartbeat_details[0]
        activity.logger.info(f"Resuming from checkpoint: {checkpoint}")
    else:
        checkpoint = {"stage": "init"}

    activity.heartbeat({"stage": "validating", "format": format_name})

    # Validate file exists
    if not os.path.exists(local_file_path):
        raise ApplicationError(
            message=f"File not found: {local_file_path}",
            type="ValidationError",
            non_retryable=True,
        )

    # Get file size
    file_size = os.path.getsize(local_file_path)

    # Build object key following naming convention
    object_key = f"{campaign_id}/variants/{variant_id}/{format_name}.png"

    try:
        minio = await get_minio_client()

        # Idempotency check: skip if already uploaded
        activity.heartbeat({"stage": "checking_exists", "object_key": object_key})
        if await minio.object_exists(MinIOConfig.BUCKET_AD_CREATIVES, object_key):
            activity.logger.info(f"Object already exists: {object_key}")

            # Generate presigned URL for existing object
            presigned_url = await minio.generate_presigned_url(
                bucket=MinIOConfig.BUCKET_AD_CREATIVES,
                object_key=object_key,
                expiry_seconds=86400,
            )

            return UploadResult(
                object_url=minio.get_public_url(MinIOConfig.BUCKET_AD_CREATIVES, object_key),
                presigned_url=presigned_url,
                bucket=MinIOConfig.BUCKET_AD_CREATIVES,
                object_key=object_key,
                size_bytes=file_size,
            )

        # Upload file
        activity.heartbeat({"stage": "uploading", "object_key": object_key, "size": file_size})

        object_url = await minio.upload_file(
            file_path=local_file_path,
            bucket=MinIOConfig.BUCKET_AD_CREATIVES,
            object_key=object_key,
            content_type="image/png",
            metadata={
                "campaign-id": campaign_id,
                "variant-id": variant_id,
                "format": format_name,
            },
        )

        # Generate presigned URL for frontend
        activity.heartbeat({"stage": "generating_url", "object_key": object_key})

        presigned_url = await minio.generate_presigned_url(
            bucket=MinIOConfig.BUCKET_AD_CREATIVES,
            object_key=object_key,
            expiry_seconds=86400,  # 24 hours
        )

        activity.logger.info(f"Uploaded {format_name} ({file_size} bytes) to {object_key}")

        return UploadResult(
            object_url=object_url,
            presigned_url=presigned_url,
            bucket=MinIOConfig.BUCKET_AD_CREATIVES,
            object_key=object_key,
            size_bytes=file_size,
        )

    except ApplicationError:
        raise  # Don't wrap application errors

    except Exception as e:
        activity.logger.error(f"Upload failed: {e}")
        # Transient error - let Temporal retry
        raise


@activity.defn
async def upload_batch_activity(
    campaign_id: str,
    variant_id: str,
    files: dict[str, str],
) -> BatchUploadResult:
    """Upload multiple ad formats in parallel.

    Args:
        campaign_id: Campaign UUID
        variant_id: Variant UUID
        files: Dict mapping format names to local file paths

    Returns:
        BatchUploadResult with all upload results
    """
    import asyncio

    activity.logger.info(f"Uploading {len(files)} formats for variant {variant_id}")
    activity.heartbeat({"stage": "batch_start", "count": len(files)})

    results = []
    total_bytes = 0

    # Upload sequentially to avoid overwhelming MinIO
    for i, (format_name, local_path) in enumerate(files.items()):
        activity.heartbeat({
            "stage": "batch_upload",
            "current": i + 1,
            "total": len(files),
            "format": format_name,
        })

        result = await upload_composed_ad_activity(
            campaign_id=campaign_id,
            variant_id=variant_id,
            local_file_path=local_path,
            format_name=format_name,
        )
        results.append(result)
        total_bytes += result.size_bytes

    activity.logger.info(f"Uploaded {len(results)} files ({total_bytes} bytes total)")

    return BatchUploadResult(
        uploads=results,
        total_bytes=total_bytes,
    )
