# src/storage/minio_client.py
"""MinIO client for S3-compatible object storage operations.

This module provides:
- Async MinIO client with connection pooling
- Presigned URLs for frontend access
- Upload/download operations with progress tracking
- Bucket management utilities

Usage:
    client = await get_minio_client()
    url = await client.upload_file("local/path.png", "ad-creatives", "campaign/variant.png")
    presigned = await client.generate_presigned_url("ad-creatives", "campaign/variant.png")
"""

import os
from functools import lru_cache
from typing import BinaryIO, Optional
from pathlib import Path
from dataclasses import dataclass

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MinIOConfig:
    """MinIO connection configuration from environment variables."""

    # Connection settings
    ENDPOINT_URL: str = os.getenv("MINIO_ENDPOINT_URL", "http://localhost:9000")
    PUBLIC_URL: str = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
    ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    REGION: str = os.getenv("MINIO_REGION", "us-east-1")

    # Bucket names
    BUCKET_AD_CREATIVES: str = "ad-creatives"
    BUCKET_BRAND_ASSETS: str = "brand-assets"

    # Connection pooling settings
    MAX_POOL_CONNECTIONS: int = int(os.getenv("MINIO_MAX_POOL_CONNECTIONS", "14"))

    # Transfer configuration for multipart uploads
    MULTIPART_THRESHOLD: int = 64 * 1024 * 1024  # 64MB
    MULTIPART_CHUNKSIZE: int = 64 * 1024 * 1024  # 64MB
    MAX_CONCURRENCY: int = 8

    # Presigned URL expiry (seconds)
    PRESIGNED_URL_EXPIRY: int = int(os.getenv("MINIO_PRESIGNED_EXPIRY_SECONDS", "86400"))  # 24h


@lru_cache(maxsize=1)
def _get_minio_session() -> aioboto3.Session:
    """Get or create cached MinIO session with connection pooling.

    Uses aioboto3 for async operations. Connection pool is shared
    across all clients created from this session.

    Returns:
        Configured aioboto3 session
    """
    config = MinIOConfig()
    return aioboto3.Session(
        aws_access_key_id=config.ACCESS_KEY,
        aws_secret_access_key=config.SECRET_KEY,
        region_name=config.REGION,
    )


def _get_boto_config() -> Config:
    """Get boto3 configuration with optimized connection pooling.

    Returns:
        Config object for S3 client
    """
    config = MinIOConfig()
    return Config(
        region_name=config.REGION,
        signature_version="s3v4",
        max_pool_connections=config.MAX_POOL_CONNECTIONS,
        retries={
            "max_attempts": 3,
            "mode": "adaptive",
        },
        s3={
            "addressing_style": "path",  # Required for MinIO
        },
    )


class MinIOClient:
    """Async MinIO client for object storage operations.

    Provides high-level operations for uploading, downloading,
    and generating presigned URLs for ad assets.

    Usage:
        client = await get_minio_client()

        # Upload a file
        url = await client.upload_file(
            file_path="./output/ad.png",
            bucket="ad-creatives",
            object_key="campaign-123/variant-456/1x1.png",
            content_type="image/png",
        )

        # Get presigned URL for frontend
        presigned_url = await client.generate_presigned_url(
            bucket="ad-creatives",
            object_key="campaign-123/variant-456/1x1.png",
            expiry_seconds=3600,
        )
    """

    _instance: Optional['MinIOClient'] = None

    def __init__(self):
        self.session = _get_minio_session()
        self.boto_config = _get_boto_config()
        self.config = MinIOConfig()
        self._initialized = False

    @classmethod
    async def get_instance(cls) -> 'MinIOClient':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._initialize()
        return cls._instance

    async def _initialize(self):
        """Initialize the client and verify connection."""
        if self._initialized:
            return

        try:
            async with self.session.client(
                "s3",
                endpoint_url=self.config.ENDPOINT_URL,
                config=self.boto_config,
            ) as s3:
                # Verify connection by listing buckets
                response = await s3.list_buckets()
                bucket_names = [b["Name"] for b in response.get("Buckets", [])]
                logger.info(f"Connected to MinIO - buckets: {bucket_names}")
                self._initialized = True

        except Exception as e:
            logger.warning(f"MinIO not available: {e}")
            # Don't fail - MinIO is optional for local dev

    async def upload_file(
        self,
        file_path: str,
        bucket: str,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload a file to MinIO.

        Automatically uses multipart upload for files > 64MB.

        Args:
            file_path: Local file path
            bucket: Bucket name
            object_key: Object key (path within bucket)
            content_type: MIME type (auto-detected if None)
            metadata: Custom metadata dict

        Returns:
            Public URL for the object

        Raises:
            ClientError: On upload failure
        """
        extra_args = {
            "CacheControl": "public, max-age=31536000, immutable",
        }
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata

        async with self.session.client(
            "s3",
            endpoint_url=self.config.ENDPOINT_URL,
            config=self.boto_config,
        ) as s3:
            try:
                await s3.upload_file(
                    file_path,
                    bucket,
                    object_key,
                    ExtraArgs=extra_args,
                )

                # Return public URL
                public_url = f"{self.config.PUBLIC_URL}/{bucket}/{object_key}"
                logger.info(f"Uploaded {file_path} to {bucket}/{object_key}")
                return public_url

            except ClientError as e:
                logger.error(f"Upload failed: {e}")
                raise

    async def upload_fileobj(
        self,
        file_obj: BinaryIO,
        bucket: str,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload a file-like object to MinIO.

        Useful for uploading in-memory files (e.g., PIL Images).

        Args:
            file_obj: File-like object (must be binary mode)
            bucket: Bucket name
            object_key: Object key
            content_type: MIME type

        Returns:
            Public URL
        """
        extra_args = {
            "CacheControl": "public, max-age=31536000, immutable",
        }
        if content_type:
            extra_args["ContentType"] = content_type

        async with self.session.client(
            "s3",
            endpoint_url=self.config.ENDPOINT_URL,
            config=self.boto_config,
        ) as s3:
            await s3.upload_fileobj(file_obj, bucket, object_key, ExtraArgs=extra_args)
            public_url = f"{self.config.PUBLIC_URL}/{bucket}/{object_key}"
            logger.info(f"Uploaded file object to {bucket}/{object_key}")
            return public_url

    async def generate_presigned_url(
        self,
        bucket: str,
        object_key: str,
        expiry_seconds: Optional[int] = None,
        method: str = "GET",
    ) -> str:
        """Generate a presigned URL for browser access.

        Presigned URLs allow frontend to access objects without credentials.

        Args:
            bucket: Bucket name
            object_key: Object key
            expiry_seconds: URL expiry in seconds (default: 24 hours)
            method: HTTP method (GET for download, PUT for upload)

        Returns:
            Presigned URL string
        """
        if expiry_seconds is None:
            expiry_seconds = self.config.PRESIGNED_URL_EXPIRY

        async with self.session.client(
            "s3",
            endpoint_url=self.config.ENDPOINT_URL,
            config=self.boto_config,
        ) as s3:
            operation_map = {
                "GET": "get_object",
                "PUT": "put_object",
            }

            url = await s3.generate_presigned_url(
                operation_map[method],
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=expiry_seconds,
            )
            return url

    async def download_file(
        self,
        bucket: str,
        object_key: str,
        local_path: str,
    ) -> str:
        """Download a file from MinIO.

        Args:
            bucket: Bucket name
            object_key: Object key
            local_path: Local destination path

        Returns:
            Local file path
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.config.ENDPOINT_URL,
            config=self.boto_config,
        ) as s3:
            await s3.download_file(bucket, object_key, local_path)
            logger.info(f"Downloaded {bucket}/{object_key} to {local_path}")
            return local_path

    async def delete_object(
        self,
        bucket: str,
        object_key: str,
    ) -> bool:
        """Delete an object from MinIO.

        Args:
            bucket: Bucket name
            object_key: Object key

        Returns:
            True if deleted
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.config.ENDPOINT_URL,
            config=self.boto_config,
        ) as s3:
            await s3.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Deleted {bucket}/{object_key}")
            return True

    async def object_exists(
        self,
        bucket: str,
        object_key: str,
    ) -> bool:
        """Check if an object exists in MinIO.

        Args:
            bucket: Bucket name
            object_key: Object key

        Returns:
            True if exists
        """
        async with self.session.client(
            "s3",
            endpoint_url=self.config.ENDPOINT_URL,
            config=self.boto_config,
        ) as s3:
            try:
                await s3.head_object(Bucket=bucket, Key=object_key)
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return False
                raise

    def get_public_url(self, bucket: str, object_key: str) -> str:
        """Get the public URL for an object (no presigning).

        Use this when the bucket has public read access.

        Args:
            bucket: Bucket name
            object_key: Object key

        Returns:
            Public URL
        """
        return f"{self.config.PUBLIC_URL}/{bucket}/{object_key}"


# Singleton accessor
async def get_minio_client() -> MinIOClient:
    """Get the singleton MinIO client instance.

    Returns:
        MinIOClient instance
    """
    return await MinIOClient.get_instance()
