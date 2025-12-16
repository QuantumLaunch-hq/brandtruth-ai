# src/connectors/meta_connector.py
"""Meta Marketing API Connector for BrandTruth AI - Slice 8

Enables direct publishing of ads to Facebook and Instagram.

Features:
- OAuth flow for ad account connection
- Campaign creation
- Ad Set creation with targeting
- Image upload
- Ad creation
- Status monitoring

Meta Marketing API Documentation:
https://developers.facebook.com/docs/marketing-apis/
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Any
from pathlib import Path
import httpx
from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class CampaignObjective(str, Enum):
    """Meta campaign objectives."""
    AWARENESS = "OUTCOME_AWARENESS"
    TRAFFIC = "OUTCOME_TRAFFIC"
    ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    LEADS = "OUTCOME_LEADS"
    APP_PROMOTION = "OUTCOME_APP_PROMOTION"
    SALES = "OUTCOME_SALES"


class AdSetOptimizationGoal(str, Enum):
    """Ad set optimization goals."""
    LINK_CLICKS = "LINK_CLICKS"
    LANDING_PAGE_VIEWS = "LANDING_PAGE_VIEWS"
    IMPRESSIONS = "IMPRESSIONS"
    REACH = "REACH"
    CONVERSIONS = "OFFSITE_CONVERSIONS"
    LEADS = "LEAD_GENERATION"


class BillingEvent(str, Enum):
    """Billing events."""
    IMPRESSIONS = "IMPRESSIONS"
    LINK_CLICKS = "LINK_CLICKS"


class AdStatus(str, Enum):
    """Ad status."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"


class PlacementType(str, Enum):
    """Ad placement types."""
    FACEBOOK_FEED = "facebook_feed"
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_STORIES = "instagram_stories"
    FACEBOOK_STORIES = "facebook_stories"
    AUDIENCE_NETWORK = "audience_network"
    MESSENGER = "messenger"


META_API_VERSION = "v18.0"
META_GRAPH_URL = f"https://graph.facebook.com/{META_API_VERSION}"


# =============================================================================
# DATA MODELS
# =============================================================================

class MetaCredentials(BaseModel):
    """Meta API credentials."""
    access_token: str
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    ad_account_id: str  # Format: act_XXXXX
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class TargetingSpec(BaseModel):
    """Targeting specification for ad sets."""
    age_min: int = 18
    age_max: int = 65
    genders: list[int] = Field(default_factory=lambda: [1, 2])  # 1=male, 2=female
    geo_locations: dict = Field(default_factory=lambda: {"countries": ["US"]})
    interests: list[dict] = Field(default_factory=list)
    behaviors: list[dict] = Field(default_factory=list)
    custom_audiences: list[dict] = Field(default_factory=list)
    excluded_custom_audiences: list[dict] = Field(default_factory=list)
    
    def to_api_format(self) -> dict:
        """Convert to Meta API format."""
        spec = {
            "age_min": self.age_min,
            "age_max": self.age_max,
            "genders": self.genders,
            "geo_locations": self.geo_locations,
        }
        if self.interests:
            spec["interests"] = self.interests
        if self.behaviors:
            spec["behaviors"] = self.behaviors
        if self.custom_audiences:
            spec["custom_audiences"] = self.custom_audiences
        if self.excluded_custom_audiences:
            spec["excluded_custom_audiences"] = self.excluded_custom_audiences
        return spec


class CampaignConfig(BaseModel):
    """Configuration for creating a campaign."""
    name: str
    objective: CampaignObjective = CampaignObjective.TRAFFIC
    status: AdStatus = AdStatus.PAUSED
    special_ad_categories: list[str] = Field(default_factory=list)
    daily_budget: Optional[int] = None  # In cents
    lifetime_budget: Optional[int] = None  # In cents


class AdSetConfig(BaseModel):
    """Configuration for creating an ad set."""
    name: str
    campaign_id: str
    optimization_goal: AdSetOptimizationGoal = AdSetOptimizationGoal.LINK_CLICKS
    billing_event: BillingEvent = BillingEvent.IMPRESSIONS
    bid_amount: Optional[int] = None  # In cents
    daily_budget: int = 1000  # $10/day in cents
    targeting: TargetingSpec = Field(default_factory=TargetingSpec)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: AdStatus = AdStatus.PAUSED


class AdCreativeConfig(BaseModel):
    """Configuration for ad creative."""
    name: str
    page_id: str  # Facebook Page ID
    instagram_actor_id: Optional[str] = None
    image_hash: Optional[str] = None
    image_url: Optional[str] = None
    headline: str
    primary_text: str
    description: Optional[str] = None
    link_url: str
    call_to_action: str = "LEARN_MORE"
    
    def get_cta_type(self) -> str:
        """Convert CTA text to Meta CTA type."""
        cta_map = {
            "Learn More": "LEARN_MORE",
            "Sign Up": "SIGN_UP",
            "Shop Now": "SHOP_NOW",
            "Get Started": "GET_STARTED",
            "Start Free": "SIGN_UP",
            "Try Now": "LEARN_MORE",
            "Apply Now": "APPLY_NOW",
            "Book Now": "BOOK_NOW",
            "Contact Us": "CONTACT_US",
            "Download": "DOWNLOAD",
            "Get Offer": "GET_OFFER",
            "Get Quote": "GET_QUOTE",
            "Subscribe": "SUBSCRIBE",
            "Watch More": "WATCH_MORE",
        }
        return cta_map.get(self.call_to_action, "LEARN_MORE")


class AdConfig(BaseModel):
    """Configuration for creating an ad."""
    name: str
    adset_id: str
    creative_id: str
    status: AdStatus = AdStatus.PAUSED


class MetaEntity(BaseModel):
    """Base model for Meta entities."""
    id: str
    name: str
    status: Optional[str] = None
    created_time: Optional[datetime] = None


class Campaign(MetaEntity):
    """Campaign entity."""
    objective: Optional[str] = None
    daily_budget: Optional[int] = None
    lifetime_budget: Optional[int] = None


class AdSet(MetaEntity):
    """Ad Set entity."""
    campaign_id: str
    optimization_goal: Optional[str] = None
    daily_budget: Optional[int] = None
    targeting: Optional[dict] = None


class Ad(MetaEntity):
    """Ad entity."""
    adset_id: str
    creative_id: Optional[str] = None
    effective_status: Optional[str] = None


class PublishResult(BaseModel):
    """Result of publishing to Meta."""
    success: bool
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    creative_id: Optional[str] = None
    ad_id: Optional[str] = None
    image_hash: Optional[str] = None
    error: Optional[str] = None
    details: dict = Field(default_factory=dict)


# =============================================================================
# META CONNECTOR
# =============================================================================

class MetaConnector:
    """Connector for Meta Marketing API."""
    
    def __init__(self, credentials: Optional[MetaCredentials] = None):
        """Initialize with credentials or load from environment."""
        if credentials:
            self.credentials = credentials
        else:
            # Load from environment
            access_token = os.getenv("META_ACCESS_TOKEN")
            ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
            
            if not access_token or not ad_account_id:
                logger.warning("Meta credentials not configured")
                self.credentials = None
            else:
                self.credentials = MetaCredentials(
                    access_token=access_token,
                    ad_account_id=ad_account_id,
                    app_id=os.getenv("META_APP_ID"),
                    app_secret=os.getenv("META_APP_SECRET"),
                )
        
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        """Check if connector is properly configured."""
        return self.credentials is not None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60)
        return self._client
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> dict:
        """Make a request to Meta Graph API."""
        if not self.credentials:
            raise ValueError("Meta credentials not configured")
        
        client = await self._get_client()
        url = f"{META_GRAPH_URL}/{endpoint}"
        
        # Add access token
        if params is None:
            params = {}
        params["access_token"] = self.credentials.access_token
        
        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                if files:
                    response = await client.post(url, params=params, files=files)
                else:
                    response = await client.post(url, params=params, data=data)
            elif method == "DELETE":
                response = await client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                logger.error(f"Meta API error: {error}")
                raise MetaAPIError(
                    message=error.get("message", "Unknown error"),
                    code=error.get("code"),
                    error_subcode=error.get("error_subcode"),
                )
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise
    
    # =========================================================================
    # ACCOUNT MANAGEMENT
    # =========================================================================
    
    async def get_ad_accounts(self) -> list[dict]:
        """Get list of ad accounts for the user."""
        result = await self._request("GET", "me/adaccounts", params={
            "fields": "id,name,account_status,currency,timezone_name"
        })
        return result.get("data", [])
    
    async def get_pages(self) -> list[dict]:
        """Get list of Facebook Pages the user manages."""
        result = await self._request("GET", "me/accounts", params={
            "fields": "id,name,access_token,instagram_business_account"
        })
        return result.get("data", [])
    
    async def validate_credentials(self) -> dict:
        """Validate current credentials."""
        try:
            result = await self._request("GET", "me", params={
                "fields": "id,name"
            })
            return {"valid": True, "user": result}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    # =========================================================================
    # CAMPAIGN MANAGEMENT
    # =========================================================================
    
    async def create_campaign(self, config: CampaignConfig) -> Campaign:
        """Create a new campaign."""
        data = {
            "name": config.name,
            "objective": config.objective.value,
            "status": config.status.value,
            "special_ad_categories": json.dumps(config.special_ad_categories),
        }
        
        if config.daily_budget:
            data["daily_budget"] = config.daily_budget
        if config.lifetime_budget:
            data["lifetime_budget"] = config.lifetime_budget
        
        result = await self._request(
            "POST",
            f"{self.credentials.ad_account_id}/campaigns",
            data=data
        )
        
        return Campaign(
            id=result["id"],
            name=config.name,
            status=config.status.value,
            objective=config.objective.value,
        )
    
    async def get_campaigns(self, status: Optional[AdStatus] = None) -> list[Campaign]:
        """Get list of campaigns."""
        params = {
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,created_time"
        }
        if status:
            params["filtering"] = json.dumps([{"field": "status", "operator": "EQUAL", "value": status.value}])
        
        result = await self._request(
            "GET",
            f"{self.credentials.ad_account_id}/campaigns",
            params=params
        )
        
        return [Campaign(**c) for c in result.get("data", [])]
    
    async def update_campaign_status(self, campaign_id: str, status: AdStatus) -> bool:
        """Update campaign status."""
        await self._request(
            "POST",
            campaign_id,
            data={"status": status.value}
        )
        return True
    
    # =========================================================================
    # AD SET MANAGEMENT
    # =========================================================================
    
    async def create_adset(self, config: AdSetConfig) -> AdSet:
        """Create a new ad set."""
        data = {
            "name": config.name,
            "campaign_id": config.campaign_id,
            "optimization_goal": config.optimization_goal.value,
            "billing_event": config.billing_event.value,
            "daily_budget": config.daily_budget,
            "targeting": json.dumps(config.targeting.to_api_format()),
            "status": config.status.value,
        }
        
        if config.bid_amount:
            data["bid_amount"] = config.bid_amount
        if config.start_time:
            data["start_time"] = config.start_time.isoformat()
        if config.end_time:
            data["end_time"] = config.end_time.isoformat()
        
        result = await self._request(
            "POST",
            f"{self.credentials.ad_account_id}/adsets",
            data=data
        )
        
        return AdSet(
            id=result["id"],
            name=config.name,
            campaign_id=config.campaign_id,
            status=config.status.value,
        )
    
    async def get_adsets(self, campaign_id: Optional[str] = None) -> list[AdSet]:
        """Get list of ad sets."""
        endpoint = f"{campaign_id}/adsets" if campaign_id else f"{self.credentials.ad_account_id}/adsets"
        
        result = await self._request(
            "GET",
            endpoint,
            params={"fields": "id,name,status,campaign_id,optimization_goal,daily_budget,targeting"}
        )
        
        return [AdSet(**a) for a in result.get("data", [])]
    
    # =========================================================================
    # IMAGE MANAGEMENT
    # =========================================================================
    
    async def upload_image(self, image_path: str) -> str:
        """Upload an image and return its hash."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        result = await self._request(
            "POST",
            f"{self.credentials.ad_account_id}/adimages",
            files={"filename": (path.name, image_bytes)}
        )
        
        # Response contains image hash
        images = result.get("images", {})
        if images:
            first_image = list(images.values())[0]
            return first_image.get("hash")
        
        raise ValueError("Failed to get image hash from upload response")
    
    async def upload_image_from_url(self, image_url: str) -> str:
        """Upload an image from URL and return its hash."""
        # Download image first
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
        
        # Generate a filename from URL hash
        filename = f"image_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
        
        result = await self._request(
            "POST",
            f"{self.credentials.ad_account_id}/adimages",
            files={"filename": (filename, image_bytes)}
        )
        
        images = result.get("images", {})
        if images:
            first_image = list(images.values())[0]
            return first_image.get("hash")
        
        raise ValueError("Failed to get image hash from upload response")
    
    # =========================================================================
    # AD CREATIVE MANAGEMENT
    # =========================================================================
    
    async def create_creative(self, config: AdCreativeConfig) -> str:
        """Create an ad creative and return its ID."""
        # Build object story spec
        object_story_spec = {
            "page_id": config.page_id,
            "link_data": {
                "link": config.link_url,
                "message": config.primary_text,
                "name": config.headline,
                "call_to_action": {
                    "type": config.get_cta_type(),
                    "value": {"link": config.link_url}
                }
            }
        }
        
        if config.description:
            object_story_spec["link_data"]["description"] = config.description
        
        if config.image_hash:
            object_story_spec["link_data"]["image_hash"] = config.image_hash
        elif config.image_url:
            object_story_spec["link_data"]["picture"] = config.image_url
        
        if config.instagram_actor_id:
            object_story_spec["instagram_actor_id"] = config.instagram_actor_id
        
        data = {
            "name": config.name,
            "object_story_spec": json.dumps(object_story_spec),
        }
        
        result = await self._request(
            "POST",
            f"{self.credentials.ad_account_id}/adcreatives",
            data=data
        )
        
        return result["id"]
    
    # =========================================================================
    # AD MANAGEMENT
    # =========================================================================
    
    async def create_ad(self, config: AdConfig) -> Ad:
        """Create an ad."""
        data = {
            "name": config.name,
            "adset_id": config.adset_id,
            "creative": json.dumps({"creative_id": config.creative_id}),
            "status": config.status.value,
        }
        
        result = await self._request(
            "POST",
            f"{self.credentials.ad_account_id}/ads",
            data=data
        )
        
        return Ad(
            id=result["id"],
            name=config.name,
            adset_id=config.adset_id,
            creative_id=config.creative_id,
            status=config.status.value,
        )
    
    async def get_ads(self, adset_id: Optional[str] = None) -> list[Ad]:
        """Get list of ads."""
        endpoint = f"{adset_id}/ads" if adset_id else f"{self.credentials.ad_account_id}/ads"
        
        result = await self._request(
            "GET",
            endpoint,
            params={"fields": "id,name,status,adset_id,creative{id},effective_status"}
        )
        
        return [Ad(**a) for a in result.get("data", [])]
    
    async def update_ad_status(self, ad_id: str, status: AdStatus) -> bool:
        """Update ad status."""
        await self._request(
            "POST",
            ad_id,
            data={"status": status.value}
        )
        return True
    
    # =========================================================================
    # HIGH-LEVEL PUBLISHING
    # =========================================================================
    
    async def publish_ad(
        self,
        headline: str,
        primary_text: str,
        cta: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        link_url: str = "",
        page_id: str = "",
        campaign_name: str = "BrandTruth Campaign",
        adset_name: str = "BrandTruth Ad Set",
        ad_name: str = "BrandTruth Ad",
        daily_budget: int = 1000,  # $10 in cents
        targeting: Optional[TargetingSpec] = None,
        start_paused: bool = True,
    ) -> PublishResult:
        """
        Publish a complete ad to Meta.
        
        This is a high-level method that:
        1. Creates a campaign
        2. Creates an ad set with targeting
        3. Uploads the image
        4. Creates the creative
        5. Creates the ad
        
        Returns a PublishResult with all created entity IDs.
        """
        if not self.is_configured:
            return PublishResult(
                success=False,
                error="Meta credentials not configured"
            )
        
        if not page_id:
            return PublishResult(
                success=False,
                error="Facebook Page ID is required"
            )
        
        try:
            result = PublishResult(success=True)
            status = AdStatus.PAUSED if start_paused else AdStatus.ACTIVE
            
            # Step 1: Create Campaign
            logger.info("Creating campaign...")
            campaign = await self.create_campaign(CampaignConfig(
                name=campaign_name,
                objective=CampaignObjective.TRAFFIC,
                status=status,
                daily_budget=daily_budget,
            ))
            result.campaign_id = campaign.id
            result.details["campaign"] = {"id": campaign.id, "name": campaign.name}
            
            # Step 2: Create Ad Set
            logger.info("Creating ad set...")
            adset = await self.create_adset(AdSetConfig(
                name=adset_name,
                campaign_id=campaign.id,
                daily_budget=daily_budget,
                targeting=targeting or TargetingSpec(),
                status=status,
            ))
            result.adset_id = adset.id
            result.details["adset"] = {"id": adset.id, "name": adset.name}
            
            # Step 3: Upload Image
            logger.info("Uploading image...")
            if image_path:
                image_hash = await self.upload_image(image_path)
            elif image_url:
                image_hash = await self.upload_image_from_url(image_url)
            else:
                image_hash = None
            
            result.image_hash = image_hash
            result.details["image"] = {"hash": image_hash}
            
            # Step 4: Create Creative
            logger.info("Creating creative...")
            creative_id = await self.create_creative(AdCreativeConfig(
                name=f"{ad_name} Creative",
                page_id=page_id,
                image_hash=image_hash,
                headline=headline,
                primary_text=primary_text,
                link_url=link_url,
                call_to_action=cta,
            ))
            result.creative_id = creative_id
            result.details["creative"] = {"id": creative_id}
            
            # Step 5: Create Ad
            logger.info("Creating ad...")
            ad = await self.create_ad(AdConfig(
                name=ad_name,
                adset_id=adset.id,
                creative_id=creative_id,
                status=status,
            ))
            result.ad_id = ad.id
            result.details["ad"] = {"id": ad.id, "name": ad.name}
            
            logger.info(f"Successfully published ad: {ad.id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to publish ad: {e}")
            return PublishResult(
                success=False,
                error=str(e),
                campaign_id=result.campaign_id,
                adset_id=result.adset_id,
                creative_id=result.creative_id,
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


class MetaAPIError(Exception):
    """Meta API error."""
    
    def __init__(self, message: str, code: Optional[int] = None, error_subcode: Optional[int] = None):
        self.message = message
        self.code = code
        self.error_subcode = error_subcode
        super().__init__(message)


# =============================================================================
# MOCK CONNECTOR FOR DEMO
# =============================================================================

class MockMetaConnector:
    """Mock connector for demo/testing without real Meta credentials."""
    
    def __init__(self):
        self.is_configured = True
        self._counter = 0
    
    def _next_id(self) -> str:
        self._counter += 1
        return f"mock_{self._counter}"
    
    async def validate_credentials(self) -> dict:
        return {"valid": True, "user": {"id": "mock_user", "name": "Demo User"}}
    
    async def get_ad_accounts(self) -> list[dict]:
        return [
            {"id": "act_123456789", "name": "Demo Ad Account", "account_status": 1, "currency": "USD"}
        ]
    
    async def get_pages(self) -> list[dict]:
        return [
            {"id": "page_123456789", "name": "Demo Facebook Page", "access_token": "mock_token"}
        ]
    
    async def create_campaign(self, config: CampaignConfig) -> Campaign:
        return Campaign(
            id=self._next_id(),
            name=config.name,
            status=config.status.value,
            objective=config.objective.value,
        )
    
    async def create_adset(self, config: AdSetConfig) -> AdSet:
        return AdSet(
            id=self._next_id(),
            name=config.name,
            campaign_id=config.campaign_id,
            status=config.status.value,
        )
    
    async def upload_image(self, image_path: str) -> str:
        return f"mock_hash_{hashlib.md5(image_path.encode()).hexdigest()[:8]}"
    
    async def upload_image_from_url(self, image_url: str) -> str:
        return f"mock_hash_{hashlib.md5(image_url.encode()).hexdigest()[:8]}"
    
    async def create_creative(self, config: AdCreativeConfig) -> str:
        return self._next_id()
    
    async def create_ad(self, config: AdConfig) -> Ad:
        return Ad(
            id=self._next_id(),
            name=config.name,
            adset_id=config.adset_id,
            creative_id=config.creative_id,
            status=config.status.value,
        )
    
    async def publish_ad(
        self,
        headline: str,
        primary_text: str,
        cta: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        link_url: str = "",
        page_id: str = "",
        campaign_name: str = "BrandTruth Campaign",
        adset_name: str = "BrandTruth Ad Set",
        ad_name: str = "BrandTruth Ad",
        daily_budget: int = 1000,
        targeting: Optional[TargetingSpec] = None,
        start_paused: bool = True,
    ) -> PublishResult:
        """Mock publishing."""
        await asyncio.sleep(1)  # Simulate API delay
        
        return PublishResult(
            success=True,
            campaign_id=self._next_id(),
            adset_id=self._next_id(),
            creative_id=self._next_id(),
            ad_id=self._next_id(),
            image_hash=f"mock_hash_{self._counter}",
            details={
                "campaign": {"id": f"mock_campaign_{self._counter}", "name": campaign_name},
                "adset": {"id": f"mock_adset_{self._counter}", "name": adset_name},
                "creative": {"id": f"mock_creative_{self._counter}"},
                "ad": {"id": f"mock_ad_{self._counter}", "name": ad_name},
                "demo_mode": True,
            }
        )
    
    async def close(self):
        pass


def get_meta_connector() -> MetaConnector | MockMetaConnector:
    """Get the appropriate Meta connector based on configuration."""
    access_token = os.getenv("META_ACCESS_TOKEN")
    ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
    
    if access_token and ad_account_id:
        return MetaConnector()
    else:
        logger.info("Using mock Meta connector (no credentials configured)")
        return MockMetaConnector()


# =============================================================================
# DEMO
# =============================================================================

async def demo_meta_connector():
    """Demo the Meta connector."""
    print("\n" + "="*60)
    print("META CONNECTOR DEMO")
    print("="*60)
    
    connector = get_meta_connector()
    
    # Validate credentials
    print("\n📋 Validating credentials...")
    validation = await connector.validate_credentials()
    print(f"   Valid: {validation.get('valid')}")
    if validation.get('user'):
        print(f"   User: {validation['user'].get('name')}")
    
    # Simulate publishing
    print("\n🚀 Publishing demo ad...")
    result = await connector.publish_ad(
        headline="Stop Getting Rejected by ATS",
        primary_text="Build resumes that get interviews with AI-powered optimization.",
        cta="Learn More",
        image_url="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600",
        link_url="https://careerfied.ai",
        page_id="demo_page_123",
        campaign_name="Careerfied - December Campaign",
        adset_name="Job Seekers - US",
        ad_name="ATS Resume Builder",
        daily_budget=2000,  # $20/day
        start_paused=True,
    )
    
    print(f"\n📊 Result:")
    print(f"   Success: {result.success}")
    print(f"   Campaign ID: {result.campaign_id}")
    print(f"   Ad Set ID: {result.adset_id}")
    print(f"   Creative ID: {result.creative_id}")
    print(f"   Ad ID: {result.ad_id}")
    
    if result.error:
        print(f"   Error: {result.error}")
    
    await connector.close()
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_meta_connector())
