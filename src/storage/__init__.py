# src/storage/__init__.py
"""Storage module for object storage operations."""

from src.storage.minio_client import MinIOClient, get_minio_client, MinIOConfig

__all__ = ["MinIOClient", "get_minio_client", "MinIOConfig"]
