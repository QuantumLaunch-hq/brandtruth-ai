# src/connectors/base.py
"""Abstract Base Connector for Ad Platforms

Defines the common interface that all ad platform connectors must implement.
This enables a unified publishing workflow across Meta, LinkedIn, TikTok, and Google.

Architecture:
    AdPlatformConnector (ABC)
        ├── MetaConnector
        ├── LinkedInConnector
        ├── TikTokConnector
        └── GoogleAdsConnector
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS - Common across platforms
# =============================================================================

class Platform(str, Enum):
    """Supported ad platforms."""
    META = "meta"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    GOOGLE = "google"


class ConnectionStatus(str, Enum):
    """Account connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"


class CampaignObjectiveType(str, Enum):
    """Unified campaign objectives (mapped to platform-specific)."""
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEADS = "leads"
    CONVERSIONS = "conversions"
    APP_INSTALLS = "app_installs"
    VIDEO_VIEWS = "video_views"


class AdStatusType(str, Enum):
    """Unified ad status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    PAUSED = "paused"
    REJECTED = "rejected"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CreativeType(str, Enum):
    """Types of ad creatives."""
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    COLLECTION = "collection"


# =============================================================================
# DATA MODELS - Platform-agnostic
# =============================================================================

class AdFormat(BaseModel):
    """Ad format specification."""
    name: str  # e.g., "Feed", "Stories", "Reels"
    aspect_ratio: str  # e.g., "1:1", "9:16", "1.91:1"
    width: int
    height: int
    min_width: Optional[int] = None
    min_height: Optional[int] = None
    max_file_size_mb: float = 30.0
    supported_types: list[CreativeType] = Field(default_factory=lambda: [CreativeType.IMAGE])
    platform: Platform
    placement: str  # Platform-specific placement ID


class PlatformCredentials(BaseModel):
    """Base credentials model."""
    platform: Platform
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    account_id: str  # Platform-specific account ID
    extra: dict = Field(default_factory=dict)  # Platform-specific fields

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class AccountInfo(BaseModel):
    """Connected account information."""
    platform: Platform
    account_id: str
    account_name: str
    status: ConnectionStatus
    currency: str = "USD"
    timezone: str = "UTC"
    permissions: list[str] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class TargetingConfig(BaseModel):
    """Universal targeting configuration."""
    # Demographics
    age_min: int = 18
    age_max: int = 65
    genders: list[str] = Field(default_factory=lambda: ["all"])  # "male", "female", "all"

    # Geography
    countries: list[str] = Field(default_factory=lambda: ["US"])
    regions: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)

    # Interests & behaviors (platform-specific IDs)
    interests: list[dict] = Field(default_factory=list)
    behaviors: list[dict] = Field(default_factory=list)

    # Audiences
    custom_audiences: list[str] = Field(default_factory=list)
    lookalike_audiences: list[str] = Field(default_factory=list)
    excluded_audiences: list[str] = Field(default_factory=list)

    # Platform-specific extras
    platform_specific: dict = Field(default_factory=dict)


class CampaignConfig(BaseModel):
    """Universal campaign configuration."""
    name: str
    objective: CampaignObjectiveType = CampaignObjectiveType.TRAFFIC
    daily_budget_cents: Optional[int] = None
    lifetime_budget_cents: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: AdStatusType = AdStatusType.PAUSED


class AdGroupConfig(BaseModel):
    """Universal ad group/ad set configuration."""
    name: str
    campaign_id: str
    targeting: TargetingConfig = Field(default_factory=TargetingConfig)
    daily_budget_cents: int = 1000  # $10/day default
    bid_strategy: str = "lowest_cost"
    bid_amount_cents: Optional[int] = None
    placements: list[str] = Field(default_factory=list)  # Empty = automatic
    status: AdStatusType = AdStatusType.PAUSED


class CreativeConfig(BaseModel):
    """Universal creative configuration."""
    name: str
    creative_type: CreativeType = CreativeType.IMAGE

    # Content
    headline: str
    primary_text: str
    description: Optional[str] = None
    cta: str = "Learn More"
    destination_url: str

    # Media
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    video_url: Optional[str] = None
    video_path: Optional[str] = None

    # Platform-specific
    page_id: Optional[str] = None  # Meta/LinkedIn
    identity_id: Optional[str] = None  # TikTok identity
    extra: dict = Field(default_factory=dict)


class AdConfig(BaseModel):
    """Universal ad configuration."""
    name: str
    ad_group_id: str
    creative_id: str
    status: AdStatusType = AdStatusType.PAUSED


class PublishResult(BaseModel):
    """Result of publishing to any platform."""
    success: bool
    platform: Platform
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    creative_id: Optional[str] = None
    ad_id: Optional[str] = None
    asset_id: Optional[str] = None  # Uploaded image/video ID
    error: Optional[str] = None
    error_code: Optional[str] = None
    details: dict = Field(default_factory=dict)

    @property
    def external_url(self) -> Optional[str]:
        """URL to view the ad in platform's ads manager."""
        return self.details.get("external_url")


class PreflightCheck(BaseModel):
    """Result of a pre-flight check."""
    check_name: str
    passed: bool
    message: str
    severity: str = "error"  # "error", "warning", "info"
    details: dict = Field(default_factory=dict)


class PreflightResult(BaseModel):
    """Combined pre-flight check results."""
    platform: Platform
    can_publish: bool
    checks: list[PreflightCheck]

    @property
    def errors(self) -> list[PreflightCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "error"]

    @property
    def warnings(self) -> list[PreflightCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]


# =============================================================================
# ABSTRACT BASE CONNECTOR
# =============================================================================

class AdPlatformConnector(ABC):
    """
    Abstract base class for ad platform connectors.

    All platform-specific connectors must implement these methods to ensure
    a consistent interface for the publishing workflow.
    """

    platform: Platform  # Must be set by subclass

    # =========================================================================
    # CONNECTION & AUTHENTICATION
    # =========================================================================

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if connector has valid credentials configured."""
        pass

    @abstractmethod
    async def validate_credentials(self) -> AccountInfo:
        """
        Validate current credentials and return account info.

        Raises:
            AuthenticationError: If credentials are invalid or expired.
        """
        pass

    @abstractmethod
    async def refresh_token(self) -> bool:
        """
        Refresh the access token if expired.

        Returns:
            True if refresh successful, False otherwise.
        """
        pass

    @abstractmethod
    async def get_ad_accounts(self) -> list[AccountInfo]:
        """Get list of ad accounts the user has access to."""
        pass

    # =========================================================================
    # FORMAT & SPEC INFORMATION
    # =========================================================================

    @abstractmethod
    def get_supported_formats(self) -> list[AdFormat]:
        """Get list of ad formats supported by this platform."""
        pass

    @abstractmethod
    def get_supported_objectives(self) -> list[CampaignObjectiveType]:
        """Get list of campaign objectives supported by this platform."""
        pass

    @abstractmethod
    def map_objective(self, objective: CampaignObjectiveType) -> str:
        """Map universal objective to platform-specific value."""
        pass

    @abstractmethod
    def map_cta(self, cta: str) -> str:
        """Map CTA text to platform-specific CTA type."""
        pass

    # =========================================================================
    # PRE-FLIGHT CHECKS
    # =========================================================================

    @abstractmethod
    async def run_preflight_checks(
        self,
        creative: CreativeConfig,
        targeting: Optional[TargetingConfig] = None,
    ) -> PreflightResult:
        """
        Run pre-flight checks before publishing.

        Checks typically include:
        - Account status (active, has payment method)
        - Creative compliance (image size, text limits)
        - Targeting validity
        - Budget minimums
        - Policy compliance hints
        """
        pass

    # =========================================================================
    # ASSET MANAGEMENT
    # =========================================================================

    @abstractmethod
    async def upload_image(self, image_path: str) -> str:
        """
        Upload an image and return platform-specific asset ID.

        Args:
            image_path: Local path to image file.

        Returns:
            Platform-specific asset ID (hash, URL, or ID).
        """
        pass

    @abstractmethod
    async def upload_image_from_url(self, image_url: str) -> str:
        """Upload an image from URL and return asset ID."""
        pass

    async def upload_video(self, video_path: str) -> str:
        """
        Upload a video and return platform-specific asset ID.

        Default implementation raises NotImplementedError.
        Override in platforms that support video.
        """
        raise NotImplementedError(f"{self.platform} does not support video upload")

    # =========================================================================
    # CAMPAIGN MANAGEMENT
    # =========================================================================

    @abstractmethod
    async def create_campaign(self, config: CampaignConfig) -> str:
        """Create a campaign and return its ID."""
        pass

    @abstractmethod
    async def create_ad_group(self, config: AdGroupConfig) -> str:
        """Create an ad group/ad set and return its ID."""
        pass

    @abstractmethod
    async def create_creative(self, config: CreativeConfig, asset_id: str) -> str:
        """Create an ad creative and return its ID."""
        pass

    @abstractmethod
    async def create_ad(self, config: AdConfig) -> str:
        """Create an ad and return its ID."""
        pass

    # =========================================================================
    # STATUS & MONITORING
    # =========================================================================

    @abstractmethod
    async def get_ad_status(self, ad_id: str) -> AdStatusType:
        """Get the current status of an ad."""
        pass

    @abstractmethod
    async def pause_ad(self, ad_id: str) -> bool:
        """Pause an ad."""
        pass

    @abstractmethod
    async def resume_ad(self, ad_id: str) -> bool:
        """Resume a paused ad."""
        pass

    # =========================================================================
    # HIGH-LEVEL PUBLISHING
    # =========================================================================

    async def publish(
        self,
        creative: CreativeConfig,
        campaign: CampaignConfig,
        ad_group: AdGroupConfig,
        run_preflight: bool = True,
    ) -> PublishResult:
        """
        High-level method to publish a complete ad.

        This method:
        1. Runs pre-flight checks (if enabled)
        2. Uploads creative assets
        3. Creates campaign
        4. Creates ad group with targeting
        5. Creates creative
        6. Creates ad

        Override for platform-specific optimizations.
        """
        result = PublishResult(success=False, platform=self.platform)

        try:
            # Pre-flight checks
            if run_preflight:
                preflight = await self.run_preflight_checks(creative, ad_group.targeting)
                if not preflight.can_publish:
                    errors = "; ".join([e.message for e in preflight.errors])
                    result.error = f"Pre-flight failed: {errors}"
                    result.details["preflight"] = preflight.model_dump()
                    return result

            # Upload asset
            if creative.image_path:
                asset_id = await self.upload_image(creative.image_path)
            elif creative.image_url:
                asset_id = await self.upload_image_from_url(creative.image_url)
            else:
                result.error = "No image provided"
                return result
            result.asset_id = asset_id

            # Create campaign
            campaign_id = await self.create_campaign(campaign)
            result.campaign_id = campaign_id

            # Create ad group
            ad_group.campaign_id = campaign_id
            ad_group_id = await self.create_ad_group(ad_group)
            result.ad_group_id = ad_group_id

            # Create creative
            creative_id = await self.create_creative(creative, asset_id)
            result.creative_id = creative_id

            # Create ad
            ad_config = AdConfig(
                name=f"{creative.name} Ad",
                ad_group_id=ad_group_id,
                creative_id=creative_id,
                status=campaign.status,
            )
            ad_id = await self.create_ad(ad_config)
            result.ad_id = ad_id

            result.success = True
            return result

        except Exception as e:
            result.error = str(e)
            return result

    # =========================================================================
    # CLEANUP
    # =========================================================================

    @abstractmethod
    async def close(self):
        """Close any open connections."""
        pass


# =============================================================================
# EXCEPTIONS
# =============================================================================

class ConnectorError(Exception):
    """Base exception for connector errors."""
    def __init__(self, message: str, platform: Platform, code: Optional[str] = None):
        self.message = message
        self.platform = platform
        self.code = code
        super().__init__(f"[{platform.value}] {message}")


class AuthenticationError(ConnectorError):
    """Authentication or authorization error."""
    pass


class RateLimitError(ConnectorError):
    """Rate limit exceeded."""
    def __init__(self, message: str, platform: Platform, retry_after: Optional[int] = None):
        super().__init__(message, platform, "RATE_LIMIT")
        self.retry_after = retry_after


class ValidationError(ConnectorError):
    """Creative or targeting validation error."""
    pass


class PolicyViolationError(ConnectorError):
    """Ad policy violation."""
    def __init__(self, message: str, platform: Platform, policy_id: Optional[str] = None):
        super().__init__(message, platform, "POLICY_VIOLATION")
        self.policy_id = policy_id


class InsufficientFundsError(ConnectorError):
    """Insufficient budget or payment method error."""
    pass
