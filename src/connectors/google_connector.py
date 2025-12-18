# src/connectors/google_connector.py
"""Google Ads API Connector

Google Ads API Documentation:
https://developers.google.com/google-ads/api/docs/start

Authentication: OAuth 2.0 with refresh tokens
Requires: Developer Token, Client ID, Client Secret, Refresh Token, Customer ID
"""

import os
import json
import hashlib
from datetime import datetime
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
from .formats import GOOGLE_FORMATS, get_text_limits
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

GOOGLE_ADS_API_VERSION = "v15"
GOOGLE_ADS_BASE = f"https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}"


# Objective mapping - Google uses campaign types
OBJECTIVE_MAP = {
    CampaignObjectiveType.AWARENESS: "DISPLAY",
    CampaignObjectiveType.TRAFFIC: "SEARCH",
    CampaignObjectiveType.ENGAGEMENT: "VIDEO",
    CampaignObjectiveType.LEADS: "DEMAND_GEN",
    CampaignObjectiveType.CONVERSIONS: "PERFORMANCE_MAX",
    CampaignObjectiveType.APP_INSTALLS: "APP",
    CampaignObjectiveType.VIDEO_VIEWS: "VIDEO",
}

# CTA mapping (Google uses ad extensions/assets for CTAs)
CTA_MAP = {
    "Learn More": "LEARN_MORE",
    "Shop Now": "SHOP_NOW",
    "Sign Up": "SIGN_UP",
    "Download": "DOWNLOAD",
    "Book Now": "BOOK_NOW",
    "Contact Us": "CONTACT_US",
    "Apply Now": "APPLY_NOW",
    "Get Quote": "GET_QUOTE",
    "Subscribe": "SUBSCRIBE",
    "Visit Site": "VISIT_SITE",
}

# Status mapping
STATUS_MAP = {
    AdStatusType.DRAFT: "PAUSED",
    AdStatusType.ACTIVE: "ENABLED",
    AdStatusType.PAUSED: "PAUSED",
    AdStatusType.ARCHIVED: "REMOVED",
}


# =============================================================================
# GOOGLE ADS CONNECTOR
# =============================================================================

class GoogleAdsConnector(AdPlatformConnector):
    """Connector for Google Ads API."""

    platform = Platform.GOOGLE

    def __init__(self):
        """Initialize with credentials from environment."""
        self.developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
        self.client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
        self.refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
        self._access_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.developer_token and self.customer_id)

    async def _get_access_token(self) -> str:
        """Get or refresh OAuth access token."""
        if self._access_token:
            return self._access_token

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise AuthenticationError(
                "Google OAuth credentials not configured",
                Platform.GOOGLE,
            )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )

            if response.status_code != 200:
                raise AuthenticationError(
                    f"Failed to refresh token: {response.text}",
                    Platform.GOOGLE,
                )

            result = response.json()
            self._access_token = result["access_token"]
            return self._access_token

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            access_token = await self._get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "developer-token": self.developer_token,
                "Content-Type": "application/json",
            }
            if self.login_customer_id:
                headers["login-customer-id"] = self.login_customer_id

            self._client = httpx.AsyncClient(timeout=60, headers=headers)
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> dict:
        """Make a request to Google Ads API."""
        if not self.is_configured:
            raise AuthenticationError("Google Ads credentials not configured", Platform.GOOGLE)

        client = await self._get_client()
        url = f"{GOOGLE_ADS_BASE}/customers/{self.customer_id}/{endpoint}"

        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Handle rate limits
            if response.status_code == 429:
                raise RateLimitError("Google Ads rate limit exceeded", Platform.GOOGLE, retry_after=60)

            # Handle auth errors
            if response.status_code == 401:
                self._access_token = None  # Clear token for refresh
                raise AuthenticationError("Invalid or expired access token", Platform.GOOGLE)

            if response.status_code == 403:
                raise AuthenticationError("Insufficient permissions", Platform.GOOGLE)

            result = response.json()

            # Google Ads returns errors in a specific format
            if response.status_code >= 400:
                error = result.get("error", {})
                message = error.get("message", str(result))
                raise ValidationError(message, Platform.GOOGLE)

            return result

        except httpx.HTTPError as e:
            logger.error(f"Google Ads HTTP error: {e}")
            raise

    async def _search(self, query: str) -> list[dict]:
        """Execute a Google Ads Query Language (GAQL) search."""
        result = await self._request(
            "POST",
            "googleAds:searchStream",
            data={"query": query},
        )
        return result.get("results", [])

    async def _mutate(self, operations: list[dict], resource_type: str) -> dict:
        """Execute mutate operations."""
        return await self._request(
            "POST",
            f"{resource_type}:mutate",
            data={"operations": operations},
        )

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    async def validate_credentials(self) -> AccountInfo:
        """Validate credentials and return account info."""
        try:
            query = """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone,
                    customer.status
                FROM customer
                LIMIT 1
            """
            results = await self._search(query)

            if not results:
                raise ValidationError("No customer data returned", Platform.GOOGLE)

            customer = results[0].get("customer", {})

            status = ConnectionStatus.CONNECTED
            if customer.get("status") != "ENABLED":
                status = ConnectionStatus.DISCONNECTED

            return AccountInfo(
                platform=Platform.GOOGLE,
                account_id=str(customer.get("id", self.customer_id)),
                account_name=customer.get("descriptiveName", "Google Ads Account"),
                status=status,
                currency=customer.get("currencyCode", "USD"),
                timezone=customer.get("timeZone", "UTC"),
                extra={
                    "customer_status": customer.get("status"),
                },
            )

        except Exception as e:
            logger.error(f"Google Ads credential validation failed: {e}")
            return AccountInfo(
                platform=Platform.GOOGLE,
                account_id=self.customer_id or "",
                account_name="Validation Failed",
                status=ConnectionStatus.ERROR,
                extra={"error": str(e)},
            )

    async def refresh_token(self) -> bool:
        """Refresh Google OAuth access token."""
        try:
            self._access_token = None
            await self._get_access_token()
            return True
        except Exception as e:
            logger.error(f"Failed to refresh Google Ads token: {e}")
            return False

    async def get_ad_accounts(self) -> list[AccountInfo]:
        """Get list of accessible customer accounts."""
        try:
            # For MCC accounts, query accessible customers
            query = """
                SELECT
                    customer_client.client_customer,
                    customer_client.descriptive_name,
                    customer_client.currency_code,
                    customer_client.status
                FROM customer_client
                WHERE customer_client.status = 'ENABLED'
            """
            results = await self._search(query)

            accounts = []
            for result in results:
                client = result.get("customerClient", {})
                status = (
                    ConnectionStatus.CONNECTED
                    if client.get("status") == "ENABLED"
                    else ConnectionStatus.DISCONNECTED
                )
                accounts.append(
                    AccountInfo(
                        platform=Platform.GOOGLE,
                        account_id=str(client.get("clientCustomer", "")).split("/")[-1],
                        account_name=client.get("descriptiveName", ""),
                        status=status,
                        currency=client.get("currencyCode", "USD"),
                    )
                )
            return accounts

        except Exception as e:
            logger.error(f"Failed to get Google Ads accounts: {e}")
            # Return current account as fallback
            account_info = await self.validate_credentials()
            return [account_info] if account_info.status == ConnectionStatus.CONNECTED else []

    # =========================================================================
    # FORMATS & SPECS
    # =========================================================================

    def get_supported_formats(self) -> list[AdFormat]:
        return GOOGLE_FORMATS

    def get_supported_objectives(self) -> list[CampaignObjectiveType]:
        return list(OBJECTIVE_MAP.keys())

    def map_objective(self, objective: CampaignObjectiveType) -> str:
        return OBJECTIVE_MAP.get(objective, "SEARCH")

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
        """Run pre-flight checks for Google Ads."""
        checks = []

        # 1. Account status check
        try:
            account_info = await self.validate_credentials()
            checks.append(
                PreflightCheck(
                    check_name="account_status",
                    passed=account_info.status == ConnectionStatus.CONNECTED,
                    message="Google Ads account is active" if account_info.status == ConnectionStatus.CONNECTED
                    else "Google Ads account is not active",
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

        # 2. Text length checks - Google has strict limits
        limits = get_text_limits(Platform.GOOGLE)

        # Google allows multiple headlines (30 chars each)
        headline_limit = limits.get("headline", 30)
        if len(creative.headline) > headline_limit:
            checks.append(
                PreflightCheck(
                    check_name="headline_length",
                    passed=False,
                    message=f"Headline exceeds {headline_limit} characters (Google limit). Will be truncated.",
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

        # Description limit
        description_limit = limits.get("description", 90)
        if len(creative.primary_text) > description_limit:
            checks.append(
                PreflightCheck(
                    check_name="description_length",
                    passed=False,
                    message=f"Description exceeds {description_limit} characters. Will be truncated.",
                    severity="warning",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="description_length",
                    passed=True,
                    message="Description length OK",
                )
            )

        # 3. Image check
        if not creative.image_url and not creative.image_path:
            checks.append(
                PreflightCheck(
                    check_name="image_provided",
                    passed=True,  # Not required for all Google ad types
                    message="No image provided (using responsive ads)",
                    severity="info",
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

        # 4. Final URL check
        if not creative.destination_url:
            checks.append(
                PreflightCheck(
                    check_name="final_url",
                    passed=False,
                    message="Final URL is required",
                    severity="error",
                )
            )
        elif not creative.destination_url.startswith(("http://", "https://")):
            checks.append(
                PreflightCheck(
                    check_name="final_url",
                    passed=False,
                    message="Final URL must start with http:// or https://",
                    severity="error",
                )
            )
        else:
            checks.append(
                PreflightCheck(
                    check_name="final_url",
                    passed=True,
                    message="Final URL is valid",
                )
            )

        # 5. Policy hint - Google has strict ad policies
        checks.append(
            PreflightCheck(
                check_name="policy_reminder",
                passed=True,
                message="Ensure ad complies with Google Ads policies (no misleading claims, proper trademarks)",
                severity="info",
            )
        )

        can_publish = all(c.passed or c.severity != "error" for c in checks)

        return PreflightResult(
            platform=Platform.GOOGLE,
            can_publish=can_publish,
            checks=checks,
        )

    # =========================================================================
    # ASSET MANAGEMENT
    # =========================================================================

    async def upload_image(self, image_path: str) -> str:
        """Upload image as a media file asset."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(path, "rb") as f:
            image_data = f.read()

        import base64
        image_base64 = base64.b64encode(image_data).decode()

        operations = [
            {
                "create": {
                    "type": "IMAGE",
                    "image": {
                        "data": image_base64,
                    },
                    "name": path.name,
                }
            }
        ]

        result = await self._mutate(operations, "assets")
        asset_resource = result.get("results", [{}])[0].get("resourceName", "")
        logger.info(f"Uploaded image to Google Ads: {asset_resource}")
        return asset_resource

    async def upload_image_from_url(self, image_url: str) -> str:
        """Google Ads requires image data, so download and upload."""
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content

        # Save to temp file
        temp_path = f"/tmp/google_upload_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.png"
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
        """Create a Google Ads campaign."""
        campaign_type = self.map_objective(config.objective)

        campaign_data = {
            "name": config.name,
            "advertisingChannelType": campaign_type,
            "status": STATUS_MAP.get(config.status, "PAUSED"),
            "campaignBudget": f"customers/{self.customer_id}/campaignBudgets/TEMP",  # Created separately
        }

        # Set bidding strategy
        campaign_data["manualCpc"] = {}  # Simple CPC bidding

        # Create budget first
        budget_amount = (config.daily_budget_cents or 1000) / 100  # Convert to dollars

        budget_operations = [
            {
                "create": {
                    "name": f"{config.name} Budget",
                    "amountMicros": int(budget_amount * 1_000_000),  # Google uses micros
                    "deliveryMethod": "STANDARD",
                }
            }
        ]

        budget_result = await self._mutate(budget_operations, "campaignBudgets")
        budget_resource = budget_result.get("results", [{}])[0].get("resourceName", "")

        # Now create campaign with budget
        campaign_data["campaignBudget"] = budget_resource

        operations = [{"create": campaign_data}]
        result = await self._mutate(operations, "campaigns")

        campaign_resource = result.get("results", [{}])[0].get("resourceName", "")
        campaign_id = campaign_resource.split("/")[-1] if campaign_resource else ""
        logger.info(f"Created Google Ads campaign: {campaign_id}")
        return campaign_id

    async def create_ad_group(self, config: AdGroupConfig) -> str:
        """Create a Google Ads ad group."""
        ad_group_data = {
            "name": config.name,
            "campaign": f"customers/{self.customer_id}/campaigns/{config.campaign_id}",
            "status": STATUS_MAP.get(config.status, "PAUSED"),
            "type": "DISPLAY_STANDARD",  # For display campaigns
        }

        # Add CPC bid
        if config.bid_amount_cents:
            ad_group_data["cpcBidMicros"] = config.bid_amount_cents * 10_000  # cents to micros

        operations = [{"create": ad_group_data}]
        result = await self._mutate(operations, "adGroups")

        ad_group_resource = result.get("results", [{}])[0].get("resourceName", "")
        ad_group_id = ad_group_resource.split("/")[-1] if ad_group_resource else ""
        logger.info(f"Created Google Ads ad group: {ad_group_id}")

        # Add targeting criteria
        if config.targeting:
            await self._add_targeting(ad_group_id, config.targeting)

        return ad_group_id

    async def _add_targeting(self, ad_group_id: str, targeting: TargetingConfig):
        """Add targeting criteria to ad group."""
        operations = []

        # Location targeting (campaign level in Google Ads)
        for country in targeting.countries:
            operations.append({
                "create": {
                    "adGroup": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                    "location": {
                        "geoTargetConstant": f"geoTargetConstants/{self._get_geo_id(country)}",
                    },
                }
            })

        # Age targeting
        age_ranges = self._get_google_age_ranges(targeting.age_min, targeting.age_max)
        for age_range in age_ranges:
            operations.append({
                "create": {
                    "adGroup": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                    "ageRange": {"type": age_range},
                }
            })

        if operations:
            try:
                await self._mutate(operations, "adGroupCriteria")
            except Exception as e:
                logger.warning(f"Failed to add targeting: {e}")

    def _get_geo_id(self, country_code: str) -> str:
        """Get Google geo target constant ID for country."""
        # Common country codes to geo IDs
        geo_map = {
            "US": "2840",
            "GB": "2826",
            "CA": "2124",
            "AU": "2036",
            "DE": "2276",
            "FR": "2250",
        }
        return geo_map.get(country_code.upper(), "2840")  # Default to US

    def _get_google_age_ranges(self, age_min: int, age_max: int) -> list[str]:
        """Get Google age range targeting values."""
        ranges = []
        google_ranges = [
            (18, 24, "AGE_RANGE_18_24"),
            (25, 34, "AGE_RANGE_25_34"),
            (35, 44, "AGE_RANGE_35_44"),
            (45, 54, "AGE_RANGE_45_54"),
            (55, 64, "AGE_RANGE_55_64"),
            (65, 200, "AGE_RANGE_65_UP"),
        ]
        for range_min, range_max, value in google_ranges:
            if range_min <= age_max and range_max >= age_min:
                ranges.append(value)
        return ranges

    async def create_creative(self, config: CreativeConfig, asset_id: str) -> str:
        """Create responsive display ad (Google's recommended format)."""
        # For Google, we create assets and then reference them in the ad
        # Return asset_id as the creative reference
        return asset_id

    async def create_ad(self, config: AdConfig) -> str:
        """Create a Google Ads responsive display ad."""
        # Note: This is simplified - Google Ads requires specific ad types per campaign type
        # For full implementation, would need ResponsiveDisplayAd, ResponsiveSearchAd, etc.

        ad_data = {
            "adGroup": f"customers/{self.customer_id}/adGroups/{config.ad_group_id}",
            "status": STATUS_MAP.get(config.status, "PAUSED"),
            "responsiveDisplayAd": {
                "headlines": [{"text": config.name[:30]}],  # Would come from CreativeConfig
                "longHeadline": {"text": config.name},
                "descriptions": [{"text": "Click to learn more"}],  # Would come from CreativeConfig
                "businessName": "Business",  # Would come from brand profile
                "marketingImages": [{"asset": config.creative_id}] if config.creative_id else [],
            },
            "finalUrls": ["https://example.com"],  # Would come from CreativeConfig
        }

        operations = [{"create": ad_data}]
        result = await self._mutate(operations, "adGroupAds")

        ad_resource = result.get("results", [{}])[0].get("resourceName", "")
        ad_id = ad_resource.split("/")[-1] if ad_resource else ""
        logger.info(f"Created Google Ads ad: {ad_id}")
        return ad_id

    # Override publish for Google-specific flow
    async def publish(
        self,
        creative: CreativeConfig,
        campaign: CampaignConfig,
        ad_group: AdGroupConfig,
        run_preflight: bool = True,
    ) -> PublishResult:
        """Publish to Google Ads with responsive display ad."""
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

            # Upload assets if provided
            asset_resources = []
            if creative.image_path:
                asset_id = await self.upload_image(creative.image_path)
                asset_resources.append(asset_id)
            elif creative.image_url:
                asset_id = await self.upload_image_from_url(creative.image_url)
                asset_resources.append(asset_id)
            result.asset_id = asset_resources[0] if asset_resources else None

            # Create campaign
            campaign_id = await self.create_campaign(campaign)
            result.campaign_id = campaign_id

            # Create ad group
            ad_group.campaign_id = campaign_id
            ad_group_id = await self.create_ad_group(ad_group)
            result.ad_group_id = ad_group_id

            # Create responsive display ad
            ad_data = {
                "adGroup": f"customers/{self.customer_id}/adGroups/{ad_group_id}",
                "status": STATUS_MAP.get(campaign.status, "PAUSED"),
                "responsiveDisplayAd": {
                    "headlines": [{"text": creative.headline[:30]}],
                    "longHeadline": {"text": creative.headline[:90]},
                    "descriptions": [{"text": creative.primary_text[:90]}],
                    "businessName": creative.extra.get("business_name", "Brand")[:25],
                },
                "finalUrls": [creative.destination_url],
            }

            # Add images if uploaded
            if asset_resources:
                ad_data["responsiveDisplayAd"]["marketingImages"] = [
                    {"asset": asset_resources[0]}
                ]

            operations = [{"create": ad_data}]
            ad_result = await self._mutate(operations, "adGroupAds")

            ad_resource = ad_result.get("results", [{}])[0].get("resourceName", "")
            result.ad_id = ad_resource.split("/")[-1] if ad_resource else ""
            result.creative_id = result.ad_id  # In Google, creative is part of ad

            result.success = True
            result.details["external_url"] = (
                f"https://ads.google.com/aw/ads?campaignId={campaign_id}&adGroupId={ad_group_id}"
            )
            return result

        except Exception as e:
            result.error = str(e)
            return result

    # =========================================================================
    # STATUS MANAGEMENT
    # =========================================================================

    async def get_ad_status(self, ad_id: str) -> AdStatusType:
        """Get ad status."""
        query = f"""
            SELECT ad_group_ad.status
            FROM ad_group_ad
            WHERE ad_group_ad.ad.id = {ad_id}
        """
        results = await self._search(query)

        if not results:
            return AdStatusType.PAUSED

        status = results[0].get("adGroupAd", {}).get("status", "PAUSED")

        status_reverse_map = {v: k for k, v in STATUS_MAP.items()}
        return status_reverse_map.get(status, AdStatusType.PAUSED)

    async def pause_ad(self, ad_id: str) -> bool:
        """Pause an ad."""
        operations = [
            {
                "update": {
                    "resourceName": f"customers/{self.customer_id}/adGroupAds/{ad_id}",
                    "status": "PAUSED",
                },
                "updateMask": "status",
            }
        ]
        await self._mutate(operations, "adGroupAds")
        return True

    async def resume_ad(self, ad_id: str) -> bool:
        """Resume an ad."""
        operations = [
            {
                "update": {
                    "resourceName": f"customers/{self.customer_id}/adGroupAds/{ad_id}",
                    "status": "ENABLED",
                },
                "updateMask": "status",
            }
        ]
        await self._mutate(operations, "adGroupAds")
        return True

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# MOCK CONNECTOR
# =============================================================================

class MockGoogleAdsConnector(GoogleAdsConnector):
    """Mock Google Ads connector for testing."""

    def __init__(self):
        self.developer_token = "mock_dev_token"
        self.customer_id = "1234567890"
        self.login_customer_id = None
        self.client_id = None
        self.client_secret = None
        self.refresh_token = None
        self._access_token = "mock_access_token"
        self._client = None
        self._counter = 0

    @property
    def is_configured(self) -> bool:
        return True

    def _next_id(self) -> str:
        self._counter += 1
        return f"mock_gads_{self._counter}"

    async def validate_credentials(self) -> AccountInfo:
        return AccountInfo(
            platform=Platform.GOOGLE,
            account_id=self.customer_id,
            account_name="Mock Google Ads Account",
            status=ConnectionStatus.CONNECTED,
            currency="USD",
            extra={"demo_mode": True},
        )

    async def upload_image(self, image_path: str) -> str:
        return f"customers/{self.customer_id}/assets/{self._next_id()}"

    async def upload_image_from_url(self, image_url: str) -> str:
        return f"customers/{self.customer_id}/assets/{self._next_id()}"

    async def create_campaign(self, config: CampaignConfig) -> str:
        return self._next_id()

    async def create_ad_group(self, config: AdGroupConfig) -> str:
        return self._next_id()

    async def create_ad(self, config: AdConfig) -> str:
        return self._next_id()

    async def _search(self, query: str) -> list[dict]:
        return []

    async def _mutate(self, operations: list[dict], resource_type: str) -> dict:
        return {"results": [{"resourceName": f"mock/{self._next_id()}"}]}

    async def close(self):
        pass
