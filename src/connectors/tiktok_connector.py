# src/connectors/tiktok_connector.py
"""TikTok Marketing API Connector

TikTok Marketing API Documentation:
https://business-api.tiktok.com/portal/docs

Authentication: OAuth 2.0 with access tokens
Requires: App ID, App Secret, Advertiser ID, Access Token
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import httpx

from .base import (
    AdPlatformConnector,
    Platform,
    AdFormat,
    CampaignObjectiveType,
    AdStatusType,
    AccountInfo,
    ConnectionStatus,
    CampaignConfig,
    AdGroupConfig,
    CreativeConfig,
    AdConfig,
    TargetingConfig,
    PreflightCheck,
    PreflightResult,
    PublishResult,
    AuthenticationError,
    ValidationError,
    RateLimitError,
)
from .formats import TIKTOK_FORMATS, get_text_limits
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3"


# Objective mapping - TikTok uses different naming
OBJECTIVE_MAP = {
    CampaignObjectiveType.AWARENESS: "REACH",
    CampaignObjectiveType.TRAFFIC: "TRAFFIC",
    CampaignObjectiveType.ENGAGEMENT: "VIDEO_VIEWS",
    CampaignObjectiveType.LEADS: "LEAD_GENERATION",
    CampaignObjectiveType.CONVERSIONS: "CONVERSIONS",
    CampaignObjectiveType.APP_INSTALLS: "APP_PROMOTION",
    CampaignObjectiveType.VIDEO_VIEWS: "VIDEO_VIEWS",
}

# CTA mapping
CTA_MAP = {
    "Learn More": "LEARN_MORE",
    "Shop Now": "SHOP_NOW",
    "Sign Up": "SIGN_UP",
    "Download": "DOWNLOAD",
    "Book Now": "BOOK_NOW",
    "Contact Us": "CONTACT_US",
    "Apply Now": "APPLY_NOW",
    "Subscribe": "SUBSCRIBE",
    "Get Quote": "GET_QUOTE",
    "Watch Now": "WATCH_NOW",
    "View More": "VIEW_NOW",
}

# Status mapping
STATUS_MAP = {
    AdStatusType.DRAFT: "DISABLE",
    AdStatusType.ACTIVE: "ENABLE",
    AdStatusType.PAUSED: "DISABLE",
    AdStatusType.ARCHIVED: "DELETE",
}


# =============================================================================
# TIKTOK CONNECTOR
# =============================================================================

class TikTokConnector(AdPlatformConnector):
    """Connector for TikTok Marketing API."""

    platform = Platform.TIKTOK

    def __init__(self):
        """Initialize with credentials from environment."""
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        self.advertiser_id = os.getenv("TIKTOK_ADVERTISER_ID")
        self.app_id = os.getenv("TIKTOK_APP_ID")
        self.app_secret = os.getenv("TIKTOK_APP_SECRET")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.advertiser_id)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=60,
                headers={
                    "Access-Token": self.access_token,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make a request to TikTok API."""
        if not self.is_configured:
            raise AuthenticationError("TikTok credentials not configured", Platform.TIKTOK)

        client = await self._get_client()
        url = f"{TIKTOK_API_BASE}/{endpoint}"

        # Always include advertiser_id
        if params is None:
            params = {}
        if data is None:
            data = {}

        try:
            if method == "GET":
                params["advertiser_id"] = self.advertiser_id
                response = await client.get(url, params=params)
            elif method == "POST":
                data["advertiser_id"] = self.advertiser_id
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            result = response.json()

            # TikTok uses code/message format
            code = result.get("code", 0)
            message = result.get("message", "")

            if code != 0:
                # Rate limit
                if code == 40100:
                    raise RateLimitError(message, Platform.TIKTOK, retry_after=60)
                # Auth errors
                if code in [40001, 40002, 40003]:
                    raise AuthenticationError(message, Platform.TIKTOK)
                # Validation errors
                raise ValidationError(f"TikTok API Error {code}: {message}", Platform.TIKTOK)

            return result.get("data", {})

        except httpx.HTTPError as e:
            logger.error(f"TikTok HTTP error: {e}")
            raise

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    async def validate_credentials(self) -> AccountInfo:
        """Validate credentials and return account info."""
        try:
            result = await self._request(
                "GET",
                "advertiser/info/",
                params={"advertiser_ids": json.dumps([self.advertiser_id])},
            )

            advertiser = result.get("list", [{}])[0] if result.get("list") else {}

            status = ConnectionStatus.CONNECTED
            if advertiser.get("status") != "STATUS_ENABLE":
                status = ConnectionStatus.DISCONNECTED

            return AccountInfo(
                platform=Platform.TIKTOK,
                account_id=self.advertiser_id,
                account_name=advertiser.get("name", "TikTok Ads Account"),
                status=status,
                currency=advertiser.get("currency", "USD"),
                timezone=advertiser.get("timezone", "UTC"),
                extra={
                    "advertiser_status": advertiser.get("status"),
                    "role": advertiser.get("role"),
                    "balance": advertiser.get("balance"),
                },
            )

        except Exception as e:
            logger.error(f"TikTok credential validation failed: {e}")
            return AccountInfo(
                platform=Platform.TIKTOK,
                account_id=self.advertiser_id or "",
                account_name="Validation Failed",
                status=ConnectionStatus.ERROR,
                extra={"error": str(e)},
            )

    async def refresh_token(self) -> bool:
        """Refresh TikTok access token."""
        if not self.app_id or not self.app_secret:
            logger.warning("TikTok app credentials not configured for token refresh")
            return False

        # TikTok token refresh requires refresh_token
        # Implementation would call /oauth2/refresh_token/
        logger.warning("TikTok token refresh not implemented")
        return False

    async def get_ad_accounts(self) -> list[AccountInfo]:
        """Get list of advertiser accounts."""
        try:
            result = await self._request(
                "GET",
                "advertiser/info/",
                params={"advertiser_ids": json.dumps([self.advertiser_id])},
            )

            accounts = []
            for advertiser in result.get("list", []):
                status = (
                    ConnectionStatus.CONNECTED
                    if advertiser.get("status") == "STATUS_ENABLE"
                    else ConnectionStatus.DISCONNECTED
                )
                accounts.append(
                    AccountInfo(
                        platform=Platform.TIKTOK,
                        account_id=str(advertiser.get("advertiser_id")),
                        account_name=advertiser.get("name", ""),
                        status=status,
                        currency=advertiser.get("currency", "USD"),
                    )
                )
            return accounts

        except Exception as e:
            logger.error(f"Failed to get TikTok ad accounts: {e}")
            return []

    # =========================================================================
    # FORMATS & SPECS
    # =========================================================================

    def get_supported_formats(self) -> list[AdFormat]:
        return TIKTOK_FORMATS

    def get_supported_objectives(self) -> list[CampaignObjectiveType]:
        return list(OBJECTIVE_MAP.keys())

    def map_objective(self, objective: CampaignObjectiveType) -> str:
        return OBJECTIVE_MAP.get(objective, "TRAFFIC")

    def map_cta(self, cta: str) -> str:
        return CTA_MAP.get(cta, "LEARN_MORE")

    # =========================================================================
    # PRE-FLIGHT CHECKS
    # =========================================================================

    async def run_preflight_checks(
        self,
        creative: CreativeConfig,
        targeting: Optional[TargetingConfig] = None,
    ) -> PreflightResult:
        """Run pre-flight checks for TikTok."""
        checks = []

        # 1. Account status check
        try:
            account_info = await self.validate_credentials()
            checks.append(
                PreflightCheck(
                    check_name="account_status",
                    passed=account_info.status == ConnectionStatus.CONNECTED,
                    message="Advertiser account is active" if account_info.status == ConnectionStatus.CONNECTED
                    else "Advertiser account is not active",
                    severity="error",
                )
            )
        except Exception as e:
            checks.append(
                PreflightCheck(
                    check_name="account_status",
                    passed=False,
                    message=f"Failed to verify account: {e}",
                    severity="error",
                )
            )

        # 2. Text length checks
        limits = get_text_limits(Platform.TIKTOK)

        if len(creative.headline) > limits.get("headline", 100):
            checks.append(
                PreflightCheck(
                    check_name="headline_length",
                    passed=False,
                    message=f"Headline exceeds {limits['headline']} characters",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="headline_length",
                    passed=True,
                    message="Headline length OK",
                )
            )

        if len(creative.primary_text) > limits.get("primary_text", 100):
            checks.append(
                PreflightCheck(
                    check_name="primary_text_length",
                    passed=False,
                    message=f"Primary text exceeds {limits['primary_text']} characters",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="primary_text_length",
                    passed=True,
                    message="Primary text length OK",
                )
            )

        # 3. TikTok strongly prefers video content
        if creative.creative_type.value == "image":
            checks.append(
                PreflightCheck(
                    check_name="content_type",
                    passed=True,
                    message="TikTok performs better with video content. Consider video ads.",
                    severity="warning",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="content_type",
                    passed=True,
                    message="Video content is optimal for TikTok",
                )
            )

        # 4. CTA check
        valid_ctas = limits.get("cta_options", [])
        if creative.cta not in valid_ctas:
            checks.append(
                PreflightCheck(
                    check_name="cta_valid",
                    passed=True,
                    message=f"CTA '{creative.cta}' will be mapped to '{self.map_cta(creative.cta)}'",
                    severity="info",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="cta_valid",
                    passed=True,
                    message="CTA is valid",
                )
            )

        # 5. Media check
        has_media = creative.image_url or creative.image_path or creative.video_url or creative.video_path
        if not has_media:
            checks.append(
                PreflightCheck(
                    check_name="media_provided",
                    passed=False,
                    message="No media provided (image or video required)",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="media_provided",
                    passed=True,
                    message="Media provided",
                )
            )

        # 6. Destination URL check
        if not creative.destination_url:
            checks.append(
                PreflightCheck(
                    check_name="destination_url",
                    passed=False,
                    message="Destination URL is required",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="destination_url",
                    passed=True,
                    message="Destination URL is valid",
                )
            )

        can_publish = all(c.passed or c.severity != "error" for c in checks)

        return PreflightResult(
            platform=Platform.TIKTOK,
            can_publish=can_publish,
            checks=checks,
        )

    # =========================================================================
    # ASSET MANAGEMENT
    # =========================================================================

    async def upload_image(self, image_path: str) -> str:
        """Upload image to TikTok."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        client = await self._get_client()

        with open(path, "rb") as f:
            files = {"image_file": (path.name, f, "image/png")}
            # Remove JSON content-type for multipart
            headers = {"Access-Token": self.access_token}

            response = await client.post(
                f"{TIKTOK_API_BASE}/file/image/ad/upload/",
                files=files,
                data={"advertiser_id": self.advertiser_id},
                headers=headers,
            )

        result = response.json()
        if result.get("code") != 0:
            raise ValidationError(f"Image upload failed: {result.get('message')}", Platform.TIKTOK)

        image_id = result.get("data", {}).get("image_id")
        logger.info(f"Uploaded image to TikTok: {image_id}")
        return image_id

    async def upload_image_from_url(self, image_url: str) -> str:
        """Upload image from URL to TikTok."""
        result = await self._request(
            "POST",
            "file/image/ad/upload/",
            data={"image_url": image_url},
        )
        image_id = result.get("image_id")
        logger.info(f"Uploaded image from URL to TikTok: {image_id}")
        return image_id

    async def upload_video(self, video_path: str) -> str:
        """Upload video to TikTok."""
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        file_size = path.stat().st_size

        # TikTok requires chunked upload for videos > 5MB
        if file_size > 5 * 1024 * 1024:
            return await self._chunked_video_upload(path)

        client = await self._get_client()

        with open(path, "rb") as f:
            files = {"video_file": (path.name, f, "video/mp4")}
            headers = {"Access-Token": self.access_token}

            response = await client.post(
                f"{TIKTOK_API_BASE}/file/video/ad/upload/",
                files=files,
                data={"advertiser_id": self.advertiser_id},
                headers=headers,
            )

        result = response.json()
        if result.get("code") != 0:
            raise ValidationError(f"Video upload failed: {result.get('message')}", Platform.TIKTOK)

        video_id = result.get("data", {}).get("video_id")
        logger.info(f"Uploaded video to TikTok: {video_id}")
        return video_id

    async def _chunked_video_upload(self, path: Path) -> str:
        """Upload large video in chunks."""
        # Simplified - in production would implement full chunked upload
        raise NotImplementedError("Chunked video upload not yet implemented")

    # =========================================================================
    # CAMPAIGN MANAGEMENT
    # =========================================================================

    async def create_campaign(self, config: CampaignConfig) -> str:
        """Create a TikTok campaign."""
        data = {
            "campaign_name": config.name,
            "objective_type": self.map_objective(config.objective),
            "budget_mode": "BUDGET_MODE_DAY" if config.daily_budget_cents else "BUDGET_MODE_TOTAL",
        }

        if config.daily_budget_cents:
            data["budget"] = config.daily_budget_cents / 100  # TikTok uses dollars
        elif config.lifetime_budget_cents:
            data["budget"] = config.lifetime_budget_cents / 100

        # TikTok operation status
        if config.status in [AdStatusType.ACTIVE]:
            data["operation_status"] = "ENABLE"
        else:
            data["operation_status"] = "DISABLE"

        result = await self._request("POST", "campaign/create/", data=data)
        campaign_id = result.get("campaign_id")
        logger.info(f"Created TikTok campaign: {campaign_id}")
        return str(campaign_id)

    async def create_ad_group(self, config: AdGroupConfig) -> str:
        """Create a TikTok ad group."""
        data = {
            "campaign_id": config.campaign_id,
            "adgroup_name": config.name,
            "placement_type": "PLACEMENT_TYPE_AUTOMATIC",  # Let TikTok optimize
            "budget_mode": "BUDGET_MODE_DAY",
            "budget": config.daily_budget_cents / 100,
            "schedule_type": "SCHEDULE_START_END",
            "schedule_start_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "billing_event": "CPC",
            "bid_type": "BID_TYPE_NO_BID",  # Lowest cost
            "optimization_goal": "CLICK",
        }

        # Add targeting
        targeting = self._build_targeting(config.targeting)
        data.update(targeting)

        # Operation status
        if config.status in [AdStatusType.ACTIVE]:
            data["operation_status"] = "ENABLE"
        else:
            data["operation_status"] = "DISABLE"

        result = await self._request("POST", "adgroup/create/", data=data)
        adgroup_id = result.get("adgroup_id")
        logger.info(f"Created TikTok ad group: {adgroup_id}")
        return str(adgroup_id)

    def _build_targeting(self, targeting: TargetingConfig) -> dict:
        """Convert universal targeting to TikTok format."""
        data = {}

        # Location targeting
        if targeting.countries:
            data["location_ids"] = targeting.countries  # TikTok uses location IDs

        # Age targeting
        age_list = []
        age_ranges = ["AGE_13_17", "AGE_18_24", "AGE_25_34", "AGE_35_44", "AGE_45_54", "AGE_55_100"]
        for age_range in age_ranges:
            # Parse age range
            parts = age_range.replace("AGE_", "").split("_")
            if len(parts) == 2:
                range_min, range_max = int(parts[0]), int(parts[1])
                if range_min <= targeting.age_max and range_max >= targeting.age_min:
                    age_list.append(age_range)
        if age_list:
            data["age_groups"] = age_list

        # Gender targeting
        if targeting.genders and "all" not in targeting.genders:
            gender_map = {"male": "MALE", "female": "FEMALE"}
            data["gender"] = [gender_map.get(g, "MALE") for g in targeting.genders if g in gender_map][0] if targeting.genders else "UNLIMITED"
        else:
            data["gender"] = "UNLIMITED"

        return data

    async def create_creative(self, config: CreativeConfig, asset_id: str) -> str:
        """Create a TikTok ad creative - TikTok handles this in ad creation."""
        # TikTok doesn't have a separate creative endpoint
        # Creative is created as part of the ad
        # Return the asset_id as a reference
        return asset_id

    async def create_ad(self, config: AdConfig) -> str:
        """Create a TikTok ad."""
        # For TikTok, we need to pass more info since creative is embedded
        # This is a simplified version

        data = {
            "adgroup_id": config.ad_group_id,
            "ad_name": config.name,
            "ad_format": "SINGLE_IMAGE",  # or SINGLE_VIDEO
            "image_ids": [config.creative_id],  # Asset ID from upload
            "ad_text": "",  # Would come from CreativeConfig
            "call_to_action": "LEARN_MORE",
            "landing_page_url": "",  # Would come from CreativeConfig
        }

        if config.status in [AdStatusType.ACTIVE]:
            data["operation_status"] = "ENABLE"
        else:
            data["operation_status"] = "DISABLE"

        result = await self._request("POST", "ad/create/", data=data)
        ad_id = result.get("ad_id")
        logger.info(f"Created TikTok ad: {ad_id}")
        return str(ad_id)

    # Override publish to handle TikTok's creative-in-ad pattern
    async def publish(
        self,
        creative: CreativeConfig,
        campaign: CampaignConfig,
        ad_group: AdGroupConfig,
        run_preflight: bool = True,
    ) -> PublishResult:
        """Publish to TikTok with creative embedded in ad."""
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
            elif creative.video_path:
                asset_id = await self.upload_video(creative.video_path)
            else:
                result.error = "No media provided"
                return result
            result.asset_id = asset_id

            # Create campaign
            campaign_id = await self.create_campaign(campaign)
            result.campaign_id = campaign_id

            # Create ad group
            ad_group.campaign_id = campaign_id
            ad_group_id = await self.create_ad_group(ad_group)
            result.ad_group_id = ad_group_id

            # Create ad (with embedded creative info)
            ad_data = {
                "adgroup_id": ad_group_id,
                "ad_name": f"{creative.name} Ad",
                "ad_format": "SINGLE_IMAGE" if not creative.video_path else "SINGLE_VIDEO",
                "image_ids": [asset_id] if not creative.video_path else None,
                "video_id": asset_id if creative.video_path else None,
                "ad_text": creative.primary_text[:100],  # TikTok limit
                "call_to_action": self.map_cta(creative.cta),
                "landing_page_url": creative.destination_url,
                "display_name": creative.headline[:40],  # TikTok limit
                "operation_status": "ENABLE" if campaign.status == AdStatusType.ACTIVE else "DISABLE",
            }

            # Remove None values
            ad_data = {k: v for k, v in ad_data.items() if v is not None}

            ad_result = await self._request("POST", "ad/create/", data=ad_data)
            ad_id = ad_result.get("ad_id")
            result.ad_id = str(ad_id)
            result.creative_id = asset_id  # Use asset as creative reference

            result.success = True
            return result

        except Exception as e:
            result.error = str(e)
            return result

    # =========================================================================
    # STATUS MANAGEMENT
    # =========================================================================

    async def get_ad_status(self, ad_id: str) -> AdStatusType:
        """Get ad status."""
        result = await self._request(
            "GET",
            "ad/get/",
            params={"ad_ids": json.dumps([ad_id]), "fields": json.dumps(["operation_status"])},
        )

        ad = result.get("list", [{}])[0] if result.get("list") else {}
        status = ad.get("operation_status", "DISABLE")

        if status == "ENABLE":
            return AdStatusType.ACTIVE
        elif status == "DELETE":
            return AdStatusType.ARCHIVED
        else:
            return AdStatusType.PAUSED

    async def pause_ad(self, ad_id: str) -> bool:
        """Pause an ad."""
        await self._request(
            "POST",
            "ad/status/update/",
            data={"ad_ids": [ad_id], "operation_status": "DISABLE"},
        )
        return True

    async def resume_ad(self, ad_id: str) -> bool:
        """Resume an ad."""
        await self._request(
            "POST",
            "ad/status/update/",
            data={"ad_ids": [ad_id], "operation_status": "ENABLE"},
        )
        return True

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# MOCK CONNECTOR
# =============================================================================

class MockTikTokConnector(TikTokConnector):
    """Mock TikTok connector for testing."""

    def __init__(self):
        self.access_token = "mock_token"
        self.advertiser_id = "mock_advertiser_123"
        self.app_id = None
        self.app_secret = None
        self._client = None
        self._counter = 0

    @property
    def is_configured(self) -> bool:
        return True

    def _next_id(self) -> str:
        self._counter += 1
        return f"mock_tt_{self._counter}"

    async def validate_credentials(self) -> AccountInfo:
        return AccountInfo(
            platform=Platform.TIKTOK,
            account_id=self.advertiser_id,
            account_name="Mock TikTok Account",
            status=ConnectionStatus.CONNECTED,
            extra={"demo_mode": True},
        )

    async def upload_image(self, image_path: str) -> str:
        return self._next_id()

    async def upload_image_from_url(self, image_url: str) -> str:
        return self._next_id()

    async def upload_video(self, video_path: str) -> str:
        return self._next_id()

    async def create_campaign(self, config: CampaignConfig) -> str:
        return self._next_id()

    async def create_ad_group(self, config: AdGroupConfig) -> str:
        return self._next_id()

    async def create_ad(self, config: AdConfig) -> str:
        return self._next_id()

    async def close(self):
        pass
