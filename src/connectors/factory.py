# src/connectors/factory.py
"""Connector Factory - Unified access to all ad platform connectors.

Usage:
    from src.connectors.factory import get_connector, get_all_connectors

    # Get a specific connector
    meta = get_connector(Platform.META)
    linkedin = get_connector("linkedin")

    # Get all configured connectors
    connectors = get_all_connectors()

    # Check platform availability
    available = get_available_platforms()
"""

import os
from typing import Optional, Union
from functools import lru_cache

from .base import (
    Platform,
    AdPlatformConnector,
    AccountInfo,
    ConnectionStatus,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# CONNECTOR REGISTRY
# =============================================================================

# Lazy imports to avoid circular dependencies
_connector_classes: dict[Platform, type] = {}


def _register_connectors():
    """Register all connector classes. Called once on first use."""
    global _connector_classes

    if _connector_classes:
        return  # Already registered

    # Import connectors here to avoid circular imports
    try:
        from .meta_connector_v2 import MetaConnectorV2
        _connector_classes[Platform.META] = MetaConnectorV2
    except ImportError:
        # Fall back to original if v2 not available
        from .meta_connector import MetaConnector
        _connector_classes[Platform.META] = MetaConnector

    try:
        from .linkedin_connector import LinkedInConnector
        _connector_classes[Platform.LINKEDIN] = LinkedInConnector
    except ImportError:
        logger.debug("LinkedIn connector not available")

    try:
        from .tiktok_connector import TikTokConnector
        _connector_classes[Platform.TIKTOK] = TikTokConnector
    except ImportError:
        logger.debug("TikTok connector not available")

    try:
        from .google_connector import GoogleAdsConnector
        _connector_classes[Platform.GOOGLE] = GoogleAdsConnector
    except ImportError:
        logger.debug("Google Ads connector not available")


# =============================================================================
# ENVIRONMENT VARIABLE MAPPING
# =============================================================================

PLATFORM_ENV_VARS = {
    Platform.META: {
        "required": ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
        "optional": ["META_APP_ID", "META_APP_SECRET", "META_PAGE_ID"],
    },
    Platform.LINKEDIN: {
        "required": ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AD_ACCOUNT_ID"],
        "optional": ["LINKEDIN_ORGANIZATION_ID"],
    },
    Platform.TIKTOK: {
        "required": ["TIKTOK_ACCESS_TOKEN", "TIKTOK_ADVERTISER_ID"],
        "optional": ["TIKTOK_APP_ID", "TIKTOK_APP_SECRET"],
    },
    Platform.GOOGLE: {
        "required": ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID"],
        "optional": [
            "GOOGLE_ADS_CLIENT_ID",
            "GOOGLE_ADS_CLIENT_SECRET",
            "GOOGLE_ADS_REFRESH_TOKEN",
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        ],
    },
}


def is_platform_configured(platform: Platform) -> bool:
    """Check if a platform has all required environment variables set."""
    env_config = PLATFORM_ENV_VARS.get(platform, {})
    required = env_config.get("required", [])
    return all(os.getenv(var) for var in required)


def get_missing_env_vars(platform: Platform) -> list[str]:
    """Get list of missing required environment variables for a platform."""
    env_config = PLATFORM_ENV_VARS.get(platform, {})
    required = env_config.get("required", [])
    return [var for var in required if not os.getenv(var)]


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def get_connector(
    platform: Union[Platform, str],
    use_mock: bool = False,
) -> Optional[AdPlatformConnector]:
    """
    Get a connector instance for the specified platform.

    Args:
        platform: Platform enum or string name (e.g., "meta", "linkedin")
        use_mock: If True, return mock connector for testing

    Returns:
        Connector instance or None if platform not available

    Example:
        connector = get_connector(Platform.META)
        connector = get_connector("linkedin")
    """
    _register_connectors()

    # Convert string to enum
    if isinstance(platform, str):
        try:
            platform = Platform(platform.lower())
        except ValueError:
            logger.error(f"Unknown platform: {platform}")
            return None

    # Check if connector class is registered
    connector_class = _connector_classes.get(platform)
    if not connector_class:
        logger.warning(f"No connector registered for {platform.value}")
        return None

    # Return mock if requested
    if use_mock:
        return _get_mock_connector(platform)

    # Check if configured
    if not is_platform_configured(platform):
        missing = get_missing_env_vars(platform)
        logger.warning(f"{platform.value} not configured. Missing: {missing}")
        return _get_mock_connector(platform)

    # Create and return connector
    try:
        return connector_class()
    except Exception as e:
        logger.error(f"Failed to create {platform.value} connector: {e}")
        return None


def _get_mock_connector(platform: Platform) -> Optional[AdPlatformConnector]:
    """Get mock connector for a platform."""
    if platform == Platform.META:
        from .meta_connector import MockMetaConnector
        return MockMetaConnector()
    # Add mock connectors for other platforms as implemented
    return None


def get_all_connectors(
    include_unconfigured: bool = False,
    use_mock_for_unconfigured: bool = False,
) -> dict[Platform, AdPlatformConnector]:
    """
    Get all available connectors.

    Args:
        include_unconfigured: Include platforms without credentials
        use_mock_for_unconfigured: Use mock connectors for unconfigured platforms

    Returns:
        Dict mapping Platform to connector instance
    """
    _register_connectors()

    connectors = {}
    for platform in Platform:
        if is_platform_configured(platform):
            connector = get_connector(platform)
            if connector:
                connectors[platform] = connector
        elif include_unconfigured:
            if use_mock_for_unconfigured:
                mock = _get_mock_connector(platform)
                if mock:
                    connectors[platform] = mock

    return connectors


def get_available_platforms() -> list[Platform]:
    """Get list of platforms that are properly configured."""
    return [p for p in Platform if is_platform_configured(p)]


def get_unavailable_platforms() -> list[tuple[Platform, list[str]]]:
    """Get list of unconfigured platforms with their missing env vars."""
    result = []
    for platform in Platform:
        if not is_platform_configured(platform):
            missing = get_missing_env_vars(platform)
            result.append((platform, missing))
    return result


# =============================================================================
# CONNECTION STATUS
# =============================================================================

async def get_platform_status(platform: Platform) -> AccountInfo:
    """
    Get the connection status for a platform.

    Returns AccountInfo with status indicating connection health.
    """
    if not is_platform_configured(platform):
        return AccountInfo(
            platform=platform,
            account_id="",
            account_name="Not Configured",
            status=ConnectionStatus.DISCONNECTED,
            extra={"missing_vars": get_missing_env_vars(platform)},
        )

    connector = get_connector(platform)
    if not connector:
        return AccountInfo(
            platform=platform,
            account_id="",
            account_name="Connector Error",
            status=ConnectionStatus.ERROR,
        )

    try:
        account_info = await connector.validate_credentials()
        await connector.close()
        return account_info
    except Exception as e:
        return AccountInfo(
            platform=platform,
            account_id="",
            account_name="Connection Error",
            status=ConnectionStatus.ERROR,
            extra={"error": str(e)},
        )


async def get_all_platform_statuses() -> dict[Platform, AccountInfo]:
    """Get connection status for all platforms."""
    statuses = {}
    for platform in Platform:
        statuses[platform] = await get_platform_status(platform)
    return statuses


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_platforms_for_format(aspect_ratio: str) -> list[Platform]:
    """Get platforms that support a given aspect ratio."""
    from .formats import get_formats_for_platform

    supported = []
    for platform in Platform:
        formats = get_formats_for_platform(platform)
        if any(f.aspect_ratio == aspect_ratio for f in formats):
            supported.append(platform)
    return supported


def get_common_platforms_for_creative(
    creative_type: str,
    aspect_ratio: str,
) -> list[Platform]:
    """Get platforms that support both the creative type and aspect ratio."""
    from .formats import get_formats_for_platform
    from .base import CreativeType

    try:
        ctype = CreativeType(creative_type.lower())
    except ValueError:
        ctype = CreativeType.IMAGE

    supported = []
    for platform in Platform:
        formats = get_formats_for_platform(platform)
        for fmt in formats:
            if fmt.aspect_ratio == aspect_ratio and ctype in fmt.supported_types:
                supported.append(platform)
                break
    return supported
