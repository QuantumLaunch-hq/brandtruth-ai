# src/connectors/linkedin_connector.py
"""LinkedIn Marketing API Connector

LinkedIn Marketing API Documentation:
https://learn.microsoft.com/en-us/linkedin/marketing/

Authentication: OAuth 2.0 with access tokens
Scopes required: r_ads, r_ads_reporting, w_organization_social, rw_ads
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
from .formats import LINKEDIN_FORMATS, get_text_limits
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

LINKEDIN_API_VERSION = "202312"  # Use versioned API
LINKEDIN_API_BASE = "https://api.linkedin.com/rest"
LINKEDIN_MARKETING_BASE = "https://api.linkedin.com/v2"


# Objective mapping
OBJECTIVE_MAP = {
    CampaignObjectiveType.AWARENESS: "BRAND_AWARENESS",
    CampaignObjectiveType.TRAFFIC: "WEBSITE_VISITS",
    CampaignObjectiveType.ENGAGEMENT: "ENGAGEMENT",
    CampaignObjectiveType.LEADS: "LEAD_GENERATION",
    CampaignObjectiveType.CONVERSIONS: "WEBSITE_CONVERSIONS",
    CampaignObjectiveType.VIDEO_VIEWS: "VIDEO_VIEWS",
}

# CTA mapping
CTA_MAP = {
    "Learn More": "LEARN_MORE",
    "Sign Up": "SIGN_UP",
    "Subscribe": "SUBSCRIBE",
    "Register": "REGISTER",
    "Download": "DOWNLOAD",
    "Apply": "APPLY",
    "Get Quote": "REQUEST_DEMO",
    "Request Demo": "REQUEST_DEMO",
    "Join": "JOIN",
    "Attend": "ATTEND",
}

# Status mapping
STATUS_MAP = {
    AdStatusType.DRAFT: "DRAFT",
    AdStatusType.ACTIVE: "ACTIVE",
    AdStatusType.PAUSED: "PAUSED",
    AdStatusType.ARCHIVED: "ARCHIVED",
}


# =============================================================================
# LINKEDIN CONNECTOR
# =============================================================================

class LinkedInConnector(AdPlatformConnector):
    """Connector for LinkedIn Marketing API."""

    platform = Platform.LINKEDIN

    def __init__(self):
        """Initialize with credentials from environment."""
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("LINKEDIN_AD_ACCOUNT_ID")
        self.organization_id = os.getenv("LINKEDIN_ORGANIZATION_ID")
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.ad_account_id)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=60,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "LinkedIn-Version": LINKEDIN_API_VERSION,
                    "X-Restli-Protocol-Version": "2.0.0",
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
        """Make a request to LinkedIn API."""
        if not self.is_configured:
            raise AuthenticationError("LinkedIn credentials not configured", Platform.LINKEDIN)

        client = await self._get_client()
        url = f"{LINKEDIN_API_BASE}/{endpoint}"

        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, json=data)
            elif method == "PATCH":
                response = await client.patch(url, json=data)
            elif method == "DELETE":
                response = await client.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Handle rate limits
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    "LinkedIn rate limit exceeded",
                    Platform.LINKEDIN,
                    retry_after=retry_after,
                )

            # Handle auth errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid or expired access token", Platform.LINKEDIN)

            if response.status_code == 403:
                raise AuthenticationError("Insufficient permissions", Platform.LINKEDIN)

            # Parse response
            if response.status_code == 204:
                return {}

            result = response.json()

            if response.status_code >= 400:
                error_msg = result.get("message", str(result))
                raise ValidationError(error_msg, Platform.LINKEDIN)

            return result

        except httpx.HTTPError as e:
            logger.error(f"LinkedIn HTTP error: {e}")
            raise

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    async def validate_credentials(self) -> AccountInfo:
        """Validate credentials and return account info."""
        try:
            # Get user info
            client = await self._get_client()
            response = await client.get(f"{LINKEDIN_MARKETING_BASE}/me")
            user_data = response.json()

            # Get ad account info
            account_data = await self._request(
                "GET",
                f"adAccounts/{self.ad_account_id}",
                params={"fields": "id,name,status,currency,type"},
            )

            return AccountInfo(
                platform=Platform.LINKEDIN,
                account_id=self.ad_account_id,
                account_name=account_data.get("name", "LinkedIn Ads Account"),
                status=ConnectionStatus.CONNECTED,
                currency=account_data.get("currency", "USD"),
                extra={
                    "user_id": user_data.get("id"),
                    "account_type": account_data.get("type"),
                    "account_status": account_data.get("status"),
                },
            )

        except Exception as e:
            logger.error(f"LinkedIn credential validation failed: {e}")
            return AccountInfo(
                platform=Platform.LINKEDIN,
                account_id=self.ad_account_id or "",
                account_name="Validation Failed",
                status=ConnectionStatus.ERROR,
                extra={"error": str(e)},
            )

    async def refresh_token(self) -> bool:
        """LinkedIn tokens need manual refresh via OAuth flow."""
        logger.warning("LinkedIn token refresh requires OAuth re-authentication")
        return False

    async def get_ad_accounts(self) -> list[AccountInfo]:
        """Get list of ad accounts."""
        try:
            result = await self._request(
                "GET",
                "adAccounts",
                params={"q": "search", "fields": "id,name,status,currency,type"},
            )

            accounts = []
            for account in result.get("elements", []):
                status = (
                    ConnectionStatus.CONNECTED
                    if account.get("status") == "ACTIVE"
                    else ConnectionStatus.DISCONNECTED
                )
                accounts.append(
                    AccountInfo(
                        platform=Platform.LINKEDIN,
                        account_id=str(account.get("id")),
                        account_name=account.get("name", ""),
                        status=status,
                        currency=account.get("currency", "USD"),
                    )
                )
            return accounts

        except Exception as e:
            logger.error(f"Failed to get LinkedIn ad accounts: {e}")
            return []

    # =========================================================================
    # FORMATS & SPECS
    # =========================================================================

    def get_supported_formats(self) -> list[AdFormat]:
        return LINKEDIN_FORMATS

    def get_supported_objectives(self) -> list[CampaignObjectiveType]:
        return list(OBJECTIVE_MAP.keys())

    def map_objective(self, objective: CampaignObjectiveType) -> str:
        return OBJECTIVE_MAP.get(objective, "WEBSITE_VISITS")

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
        """Run pre-flight checks for LinkedIn."""
        checks = []

        # 1. Account status check
        try:
            account_info = await self.validate_credentials()
            checks.append(
                PreflightCheck(
                    check_name="account_status",
                    passed=account_info.status == ConnectionStatus.CONNECTED,
                    message="Ad account is active" if account_info.status == ConnectionStatus.CONNECTED
                    else "Ad account is not active",
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

        # 2. Organization check (required for sponsored content)
        if not self.organization_id:
            checks.append(
                PreflightCheck(
                    check_name="organization",
                    passed=False,
                    message="LinkedIn Organization ID not configured (required for ads)",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="organization",
                    passed=True,
                    message="Organization configured",
                )
            )

        # 3. Text length checks
        limits = get_text_limits(Platform.LINKEDIN)

        if len(creative.headline) > limits.get("headline_max", 200):
            checks.append(
                PreflightCheck(
                    check_name="headline_length",
                    passed=False,
                    message=f"Headline exceeds {limits['headline_max']} characters",
                    severity="error",
                )
            )
        elif len(creative.headline) > limits.get("headline", 70):
            checks.append(
                PreflightCheck(
                    check_name="headline_length",
                    passed=True,
                    message=f"Headline exceeds recommended {limits['headline']} characters (may be truncated)",
                    severity="warning",
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

        if len(creative.primary_text) > limits.get("primary_text_max", 600):
            checks.append(
                PreflightCheck(
                    check_name="primary_text_length",
                    passed=False,
                    message=f"Primary text exceeds {limits['primary_text_max']} characters",
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

        # 4. CTA check
        valid_ctas = limits.get("cta_options", [])
        if creative.cta not in valid_ctas and self.map_cta(creative.cta) == "LEARN_MORE":
            checks.append(
                PreflightCheck(
                    check_name="cta_valid",
                    passed=True,
                    message=f"CTA '{creative.cta}' will be mapped to 'Learn More'",
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

        # 5. Image check
        if not creative.image_url and not creative.image_path:
            checks.append(
                PreflightCheck(
                    check_name="image_provided",
                    passed=False,
                    message="No image provided",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="image_provided",
                    passed=True,
                    message="Image provided",
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
        elif not creative.destination_url.startswith(("http://", "https://")):
            checks.append(
                PreflightCheck(
                    check_name="destination_url",
                    passed=False,
                    message="Destination URL must start with http:// or https://",
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
            platform=Platform.LINKEDIN,
            can_publish=can_publish,
            checks=checks,
        )

    # =========================================================================
    # ASSET MANAGEMENT
    # =========================================================================

    async def upload_image(self, image_path: str) -> str:
        """Upload image to LinkedIn."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Step 1: Register upload
        register_data = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:organization:{self.organization_id}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        client = await self._get_client()
        response = await client.post(
            f"{LINKEDIN_MARKETING_BASE}/assets?action=registerUpload",
            json=register_data,
        )
        register_result = response.json()

        upload_url = register_result["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn = register_result["value"]["asset"]

        # Step 2: Upload the image
        with open(path, "rb") as f:
            image_bytes = f.read()

        upload_response = await client.put(
            upload_url,
            content=image_bytes,
            headers={"Content-Type": "image/png"},
        )

        if upload_response.status_code not in [200, 201]:
            raise ValidationError(f"Image upload failed: {upload_response.text}", Platform.LINKEDIN)

        logger.info(f"Uploaded image to LinkedIn: {asset_urn}")
        return asset_urn

    async def upload_image_from_url(self, image_url: str) -> str:
        """Download image and upload to LinkedIn."""
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

        # Save to temp file
        temp_path = f"/tmp/linkedin_upload_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.png"
        with open(temp_path, "wb") as f:
            f.write(image_bytes)

        try:
            return await self.upload_image(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    # =========================================================================
    # CAMPAIGN MANAGEMENT
    # =========================================================================

    async def create_campaign(self, config: CampaignConfig) -> str:
        """Create a LinkedIn campaign."""
        data = {
            "account": f"urn:li:sponsoredAccount:{self.ad_account_id}",
            "name": config.name,
            "objectiveType": self.map_objective(config.objective),
            "status": STATUS_MAP.get(config.status, "PAUSED"),
            "type": "SPONSORED_UPDATES",
        }

        if config.daily_budget_cents:
            data["dailyBudget"] = {
                "currencyCode": "USD",
                "amount": str(config.daily_budget_cents / 100),
            }

        if config.lifetime_budget_cents:
            data["totalBudget"] = {
                "currencyCode": "USD",
                "amount": str(config.lifetime_budget_cents / 100),
            }

        result = await self._request("POST", "campaigns", data=data)
        campaign_id = result.get("id")
        logger.info(f"Created LinkedIn campaign: {campaign_id}")
        return str(campaign_id)

    async def create_ad_group(self, config: AdGroupConfig) -> str:
        """Create a LinkedIn campaign group (ad set equivalent)."""
        # LinkedIn uses Campaign Groups differently - for simplicity,
        # we'll use the campaign directly as the ad group equivalent
        # In a full implementation, you'd create separate targeting here

        data = {
            "account": f"urn:li:sponsoredAccount:{self.ad_account_id}",
            "campaign": f"urn:li:sponsoredCampaign:{config.campaign_id}",
            "name": config.name,
            "status": STATUS_MAP.get(config.status, "PAUSED"),
        }

        if config.daily_budget_cents:
            data["dailyBudget"] = {
                "currencyCode": "USD",
                "amount": str(config.daily_budget_cents / 100),
            }

        # Add targeting
        targeting = self._build_targeting(config.targeting)
        if targeting:
            data["targetingCriteria"] = targeting

        result = await self._request("POST", "campaignGroups", data=data)
        group_id = result.get("id")
        logger.info(f"Created LinkedIn campaign group: {group_id}")
        return str(group_id)

    def _build_targeting(self, targeting: TargetingConfig) -> dict:
        """Convert universal targeting to LinkedIn format."""
        criteria = {"include": {"and": []}}

        # Location targeting
        if targeting.countries:
            criteria["include"]["and"].append({
                "or": {
                    "urn:li:adTargetingFacet:locations": [
                        f"urn:li:geo:{c}" for c in targeting.countries
                    ]
                }
            })

        # Age targeting (LinkedIn uses age ranges)
        age_range = self._get_linkedin_age_range(targeting.age_min, targeting.age_max)
        if age_range:
            criteria["include"]["and"].append({
                "or": {"urn:li:adTargetingFacet:ageRanges": age_range}
            })

        return criteria if criteria["include"]["and"] else {}

    def _get_linkedin_age_range(self, age_min: int, age_max: int) -> list[str]:
        """Convert age range to LinkedIn age range URNs."""
        ranges = []
        linkedin_ranges = [
            (18, 24, "urn:li:ageRange:(18,24)"),
            (25, 34, "urn:li:ageRange:(25,34)"),
            (35, 54, "urn:li:ageRange:(35,54)"),
            (55, 200, "urn:li:ageRange:(55,)"),
        ]
        for range_min, range_max, urn in linkedin_ranges:
            if range_min <= age_max and range_max >= age_min:
                ranges.append(urn)
        return ranges

    async def create_creative(self, config: CreativeConfig, asset_id: str) -> str:
        """Create a LinkedIn ad creative."""
        data = {
            "account": f"urn:li:sponsoredAccount:{self.ad_account_id}",
            "type": "SPONSORED_UPDATE",
            "status": "ACTIVE",
            "variables": {
                "data": {
                    "com.linkedin.ads.SponsoredUpdateCreativeVariables": {
                        "activity": f"urn:li:activity:{await self._create_share(config, asset_id)}",
                    }
                }
            },
        }

        result = await self._request("POST", "creatives", data=data)
        creative_id = result.get("id")
        logger.info(f"Created LinkedIn creative: {creative_id}")
        return str(creative_id)

    async def _create_share(self, config: CreativeConfig, asset_id: str) -> str:
        """Create a LinkedIn share (post) for the creative."""
        data = {
            "author": f"urn:li:organization:{self.organization_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": config.primary_text,
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": asset_id,
                            "title": {"text": config.headline},
                            "description": {"text": config.description or ""},
                        }
                    ],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }

        client = await self._get_client()
        response = await client.post(f"{LINKEDIN_MARKETING_BASE}/ugcPosts", json=data)
        result = response.json()
        share_id = result.get("id", "").replace("urn:li:share:", "")
        return share_id

    async def create_ad(self, config: AdConfig) -> str:
        """Create a LinkedIn ad."""
        data = {
            "account": f"urn:li:sponsoredAccount:{self.ad_account_id}",
            "campaign": f"urn:li:sponsoredCampaign:{config.ad_group_id}",
            "creative": f"urn:li:sponsoredCreative:{config.creative_id}",
            "status": STATUS_MAP.get(config.status, "PAUSED"),
        }

        result = await self._request("POST", "ads", data=data)
        ad_id = result.get("id")
        logger.info(f"Created LinkedIn ad: {ad_id}")
        return str(ad_id)

    # =========================================================================
    # STATUS MANAGEMENT
    # =========================================================================

    async def get_ad_status(self, ad_id: str) -> AdStatusType:
        """Get ad status."""
        result = await self._request("GET", f"ads/{ad_id}", params={"fields": "status"})
        status = result.get("status", "PAUSED")

        status_reverse_map = {v: k for k, v in STATUS_MAP.items()}
        return status_reverse_map.get(status, AdStatusType.PAUSED)

    async def pause_ad(self, ad_id: str) -> bool:
        """Pause an ad."""
        await self._request("PATCH", f"ads/{ad_id}", data={"status": "PAUSED"})
        return True

    async def resume_ad(self, ad_id: str) -> bool:
        """Resume an ad."""
        await self._request("PATCH", f"ads/{ad_id}", data={"status": "ACTIVE"})
        return True

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# MOCK CONNECTOR
# =============================================================================

class MockLinkedInConnector(LinkedInConnector):
    """Mock LinkedIn connector for testing."""

    def __init__(self):
        self.access_token = "mock_token"
        self.ad_account_id = "123456789"
        self.organization_id = "987654321"
        self._client = None
        self._counter = 0

    @property
    def is_configured(self) -> bool:
        return True

    def _next_id(self) -> str:
        self._counter += 1
        return f"mock_li_{self._counter}"

    async def validate_credentials(self) -> AccountInfo:
        return AccountInfo(
            platform=Platform.LINKEDIN,
            account_id=self.ad_account_id,
            account_name="Mock LinkedIn Account",
            status=ConnectionStatus.CONNECTED,
            extra={"demo_mode": True},
        )

    async def upload_image(self, image_path: str) -> str:
        return f"urn:li:digitalmediaAsset:{self._next_id()}"

    async def upload_image_from_url(self, image_url: str) -> str:
        return f"urn:li:digitalmediaAsset:{self._next_id()}"

    async def create_campaign(self, config: CampaignConfig) -> str:
        return self._next_id()

    async def create_ad_group(self, config: AdGroupConfig) -> str:
        return self._next_id()

    async def create_creative(self, config: CreativeConfig, asset_id: str) -> str:
        return self._next_id()

    async def create_ad(self, config: AdConfig) -> str:
        return self._next_id()

    async def close(self):
        pass
