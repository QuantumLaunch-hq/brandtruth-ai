# src/connectors/__init__.py
"""
Multi-Platform Ad Connectors

Unified interface for publishing ads to:
- Meta (Facebook/Instagram)
- LinkedIn
- TikTok
- Google Ads

Usage:
    from src.connectors import get_connector, Platform

    # Get a specific connector
    connector = get_connector(Platform.META)

    # Publish an ad
    result = await connector.publish(creative, campaign, ad_group)
"""

# Base classes and enums
from .base import (
    Platform,
    ConnectionStatus,
    CampaignObjectiveType,
    AdStatusType,
    CreativeType,
    AdFormat,
    PlatformCredentials,
    AccountInfo,
    TargetingConfig,
    CampaignConfig as UnifiedCampaignConfig,
    AdGroupConfig,
    CreativeConfig,
    AdConfig as UnifiedAdConfig,
    PublishResult as UnifiedPublishResult,
    PreflightCheck,
    PreflightResult,
    AdPlatformConnector,
    ConnectorError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    PolicyViolationError,
    InsufficientFundsError,
)

# Format specifications
from .formats import (
    META_FORMATS,
    LINKEDIN_FORMATS,
    TIKTOK_FORMATS,
    GOOGLE_FORMATS,
    TEXT_LIMITS,
    get_formats_for_platform,
    get_format_by_aspect_ratio,
    get_common_aspect_ratios,
    get_image_formats_for_platform,
    get_video_formats_for_platform,
    get_text_limits,
    validate_text_length,
)

# Factory functions
from .factory import (
    get_connector,
    get_all_connectors,
    get_available_platforms,
    get_unavailable_platforms,
    get_platform_status,
    get_all_platform_statuses,
    is_platform_configured,
    get_missing_env_vars,
    get_platforms_for_format,
    get_common_platforms_for_creative,
)

# Legacy imports for backwards compatibility with existing code
from .meta_connector import (
    MetaConnector,
    MockMetaConnector,
    MetaCredentials,
    CampaignConfig,  # Legacy Meta-specific
    AdSetConfig,
    AdCreativeConfig,
    AdConfig,  # Legacy Meta-specific
    TargetingSpec,
    PublishResult,  # Legacy Meta-specific
    CampaignObjective,
    AdSetOptimizationGoal,
    AdStatus,
    get_meta_connector,
)

# Platform-specific connectors (optional imports)
try:
    from .linkedin_connector import LinkedInConnector, MockLinkedInConnector
except ImportError:
    LinkedInConnector = None
    MockLinkedInConnector = None

try:
    from .tiktok_connector import TikTokConnector, MockTikTokConnector
except ImportError:
    TikTokConnector = None
    MockTikTokConnector = None

try:
    from .google_connector import GoogleAdsConnector, MockGoogleAdsConnector
except ImportError:
    GoogleAdsConnector = None
    MockGoogleAdsConnector = None


__all__ = [
    # Base
    "Platform",
    "ConnectionStatus",
    "CampaignObjectiveType",
    "AdStatusType",
    "CreativeType",
    "AdFormat",
    "PlatformCredentials",
    "AccountInfo",
    "TargetingConfig",
    "UnifiedCampaignConfig",
    "AdGroupConfig",
    "CreativeConfig",
    "UnifiedAdConfig",
    "UnifiedPublishResult",
    "PreflightCheck",
    "PreflightResult",
    "AdPlatformConnector",
    # Exceptions
    "ConnectorError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "PolicyViolationError",
    "InsufficientFundsError",
    # Formats
    "META_FORMATS",
    "LINKEDIN_FORMATS",
    "TIKTOK_FORMATS",
    "GOOGLE_FORMATS",
    "TEXT_LIMITS",
    "get_formats_for_platform",
    "get_format_by_aspect_ratio",
    "get_common_aspect_ratios",
    "get_image_formats_for_platform",
    "get_video_formats_for_platform",
    "get_text_limits",
    "validate_text_length",
    # Factory
    "get_connector",
    "get_all_connectors",
    "get_available_platforms",
    "get_unavailable_platforms",
    "get_platform_status",
    "get_all_platform_statuses",
    "is_platform_configured",
    "get_missing_env_vars",
    "get_platforms_for_format",
    "get_common_platforms_for_creative",
    # Connectors
    "MetaConnector",
    "MockMetaConnector",
    "LinkedInConnector",
    "MockLinkedInConnector",
    "TikTokConnector",
    "MockTikTokConnector",
    "GoogleAdsConnector",
    "MockGoogleAdsConnector",
    # Legacy (backwards compatibility)
    "MetaCredentials",
    "CampaignConfig",
    "AdSetConfig",
    "AdCreativeConfig",
    "AdConfig",
    "TargetingSpec",
    "PublishResult",
    "CampaignObjective",
    "AdSetOptimizationGoal",
    "AdStatus",
    "get_meta_connector",
]
