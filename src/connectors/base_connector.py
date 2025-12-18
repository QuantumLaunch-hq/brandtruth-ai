"""Base connector interface for ad platforms.

All platform connectors should inherit from this base class to ensure
consistent API across different ad platforms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    """Supported ad platforms."""
    META = "meta"           # Facebook + Instagram
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    GOOGLE = "google"       # Google Ads (Display, YouTube)
    TWITTER = "twitter"     # X/Twitter


class AdObjective(str, Enum):
    """Common ad objectives across platforms."""
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEADS = "leads"
    CONVERSIONS = "conversions"
    APP_INSTALLS = "app_installs"
    VIDEO_VIEWS = "video_views"


@dataclass
class AdCreative:
    """Universal ad creative that can be adapted per platform."""
    headline: str
    primary_text: str
    cta: str
    image_url: str
    destination_url: str

    # Optional fields
    description: Optional[str] = None
    video_url: Optional[str] = None
    display_url: Optional[str] = None  # Shortened URL for display


@dataclass
class TargetingSpec:
    """Universal targeting specification."""
    age_min: int = 18
    age_max: int = 65
    countries: list[str] = field(default_factory=lambda: ["US"])

    # Optional targeting
    interests: list[str] = field(default_factory=list)
    job_titles: list[str] = field(default_factory=list)      # LinkedIn
    industries: list[str] = field(default_factory=list)      # LinkedIn
    company_sizes: list[str] = field(default_factory=list)   # LinkedIn
    keywords: list[str] = field(default_factory=list)        # Google
    placements: list[str] = field(default_factory=list)      # Google/Meta
    custom_audiences: list[str] = field(default_factory=list)


@dataclass
class CampaignConfig:
    """Universal campaign configuration."""
    name: str
    objective: AdObjective
    daily_budget: int  # in cents
    destination_url: str

    # Creatives to publish
    creatives: list[AdCreative] = field(default_factory=list)

    # Targeting
    targeting: TargetingSpec = field(default_factory=TargetingSpec)

    # Settings
    start_paused: bool = True
    schedule_start: Optional[str] = None  # ISO datetime
    schedule_end: Optional[str] = None


@dataclass
class PublishResult:
    """Result of publishing to a platform."""
    success: bool
    platform: Platform

    # IDs from the platform
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    ad_ids: list[str] = field(default_factory=list)

    # Status
    demo_mode: bool = False
    error: Optional[str] = None
    details: dict = field(default_factory=dict)


class BaseAdConnector(ABC):
    """Abstract base class for ad platform connectors.

    Each platform connector must implement these methods to provide
    a consistent interface for the publishing workflow.
    """

    platform: Platform

    @abstractmethod
    async def check_credentials(self) -> tuple[bool, str]:
        """Check if API credentials are configured and valid.

        Returns:
            (is_configured, message)
        """
        pass

    @abstractmethod
    async def create_campaign(self, config: CampaignConfig) -> PublishResult:
        """Create a complete campaign with ad set and ads.

        Args:
            config: Campaign configuration

        Returns:
            PublishResult with platform IDs
        """
        pass

    @abstractmethod
    async def upload_image(self, image_url: str) -> str:
        """Upload an image to the platform's media library.

        Args:
            image_url: URL of the image to upload

        Returns:
            Platform-specific image hash/ID
        """
        pass

    @abstractmethod
    async def get_campaign_status(self, campaign_id: str) -> dict:
        """Get status of an existing campaign.

        Args:
            campaign_id: Platform campaign ID

        Returns:
            Campaign status and metrics
        """
        pass

    @abstractmethod
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause a running campaign."""
        pass

    @abstractmethod
    async def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign."""
        pass

    @abstractmethod
    def get_supported_objectives(self) -> list[AdObjective]:
        """Get list of objectives supported by this platform."""
        pass

    @abstractmethod
    def get_ad_specs(self) -> dict:
        """Get platform-specific ad specifications.

        Returns:
            Dict with image sizes, text limits, etc.
        """
        pass

    # Helper methods (not abstract)

    def adapt_creative(self, creative: AdCreative) -> dict:
        """Adapt a universal creative to platform-specific format.

        Override in subclass for platform-specific transformations.
        """
        return {
            "headline": creative.headline,
            "primary_text": creative.primary_text,
            "cta": creative.cta,
            "image_url": creative.image_url,
            "destination_url": creative.destination_url,
        }

    def adapt_targeting(self, targeting: TargetingSpec) -> dict:
        """Adapt universal targeting to platform-specific format.

        Override in subclass for platform-specific transformations.
        """
        return {
            "age_min": targeting.age_min,
            "age_max": targeting.age_max,
            "countries": targeting.countries,
        }


# Platform-specific ad specs for reference
AD_SPECS = {
    Platform.META: {
        "image_sizes": {
            "feed": {"width": 1080, "height": 1080, "ratio": "1:1"},
            "story": {"width": 1080, "height": 1920, "ratio": "9:16"},
            "carousel": {"width": 1080, "height": 1080, "ratio": "1:1"},
        },
        "text_limits": {
            "headline": 40,
            "primary_text": 125,
            "description": 30,
        },
        "cta_options": [
            "SHOP_NOW", "LEARN_MORE", "SIGN_UP", "BOOK_NOW",
            "CONTACT_US", "DOWNLOAD", "GET_OFFER", "GET_QUOTE",
        ],
    },
    Platform.LINKEDIN: {
        "image_sizes": {
            "single_image": {"width": 1200, "height": 627, "ratio": "1.91:1"},
            "carousel": {"width": 1080, "height": 1080, "ratio": "1:1"},
        },
        "text_limits": {
            "headline": 70,
            "introductory_text": 600,
            "description": 100,
        },
        "cta_options": [
            "APPLY", "DOWNLOAD", "GET_QUOTE", "LEARN_MORE",
            "SIGN_UP", "SUBSCRIBE", "REGISTER", "JOIN", "ATTEND",
        ],
    },
    Platform.TIKTOK: {
        "image_sizes": {
            "feed": {"width": 1080, "height": 1920, "ratio": "9:16"},
        },
        "video_specs": {
            "min_duration": 5,
            "max_duration": 60,
            "min_resolution": "720p",
        },
        "text_limits": {
            "ad_text": 100,
            "cta_text": 16,
        },
        "cta_options": [
            "SHOP_NOW", "LEARN_MORE", "SIGN_UP", "CONTACT_US",
            "DOWNLOAD", "ORDER_NOW", "BOOK_NOW", "WATCH_MORE",
        ],
    },
    Platform.GOOGLE: {
        "image_sizes": {
            "responsive": [
                {"width": 1200, "height": 628, "ratio": "1.91:1"},
                {"width": 1200, "height": 1200, "ratio": "1:1"},
                {"width": 300, "height": 250, "ratio": "1.2:1"},
            ],
        },
        "text_limits": {
            "headline": 30,  # Up to 5 headlines
            "description": 90,  # Up to 5 descriptions
        },
        "cta_options": [
            "LEARN_MORE", "GET_QUOTE", "APPLY_NOW", "CONTACT_US",
            "SIGN_UP", "DOWNLOAD", "BOOK_NOW", "SHOP_NOW",
        ],
    },
}
