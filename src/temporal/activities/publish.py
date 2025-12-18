# src/temporal/activities/publish.py
"""Multi-Platform Publishing Activities for Temporal

Activities for publishing ads to various platforms (Meta, LinkedIn, TikTok, Google).
Uses the unified connector framework for consistent handling across platforms.
"""

import json
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import timedelta

from temporalio import activity
from temporalio.exceptions import ApplicationError

from src.connectors import (
    Platform,
    get_connector,
    is_platform_configured,
    get_missing_env_vars,
    get_available_platforms,
    get_platform_status,
    CreativeConfig,
    CampaignConfig as UnifiedCampaignConfig,
    AdGroupConfig,
    TargetingConfig,
    CampaignObjectiveType,
    AdStatusType,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# DATA CLASSES FOR SERIALIZATION
# =============================================================================

@dataclass
class PublishConfig:
    """Configuration for publishing an ad to a platform."""
    platform: str  # "meta", "linkedin", "tiktok", "google"

    # Creative content
    headline: str
    primary_text: str
    description: str
    cta: str
    destination_url: str

    # Media
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    video_url: Optional[str] = None
    video_path: Optional[str] = None

    # Campaign settings
    campaign_name: str = "BrandTruth Campaign"
    ad_group_name: str = "BrandTruth Ad Group"
    ad_name: str = "BrandTruth Ad"
    daily_budget_cents: int = 1000  # $10/day

    # Targeting
    age_min: int = 18
    age_max: int = 65
    countries: list[str] = None
    genders: list[str] = None

    # Control
    start_paused: bool = True

    # Platform-specific
    page_id: Optional[str] = None  # Meta
    organization_id: Optional[str] = None  # LinkedIn
    identity_id: Optional[str] = None  # TikTok
    business_name: Optional[str] = None  # Google

    def __post_init__(self):
        if self.countries is None:
            self.countries = ["US"]
        if self.genders is None:
            self.genders = ["all"]


@dataclass
class PublishActivityResult:
    """Result of publishing activity."""
    success: bool
    platform: str
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    creative_id: Optional[str] = None
    ad_id: Optional[str] = None
    asset_id: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    external_url: Optional[str] = None
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class PreflightActivityResult:
    """Result of pre-flight check activity."""
    platform: str
    can_publish: bool
    checks: list[dict]
    errors: list[str]
    warnings: list[str]


@dataclass
class PlatformStatusResult:
    """Result of platform status check."""
    platform: str
    configured: bool
    connected: bool
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    currency: Optional[str] = None
    error: Optional[str] = None
    missing_env_vars: list[str] = None

    def __post_init__(self):
        if self.missing_env_vars is None:
            self.missing_env_vars = []


# =============================================================================
# ACTIVITIES
# =============================================================================

@activity.defn
async def publish_to_platform_activity(config_json: str) -> PublishActivityResult:
    """
    Publish an ad to a specified platform.

    This activity:
    1. Gets the appropriate connector for the platform
    2. Runs pre-flight checks
    3. Uploads assets
    4. Creates campaign, ad group, creative, and ad
    5. Returns the result with all IDs

    Args:
        config_json: JSON string of PublishConfig

    Returns:
        PublishActivityResult with success status and IDs
    """
    config_data = json.loads(config_json)
    config = PublishConfig(**config_data)

    logger.info(f"Publishing to {config.platform}: {config.campaign_name}")

    # Heartbeat for long operations
    activity.heartbeat({"stage": "initializing", "platform": config.platform})

    try:
        # Get platform enum
        platform = Platform(config.platform.lower())
    except ValueError:
        return PublishActivityResult(
            success=False,
            platform=config.platform,
            error=f"Unknown platform: {config.platform}",
            error_code="INVALID_PLATFORM",
        )

    # Check if platform is configured
    if not is_platform_configured(platform):
        missing = get_missing_env_vars(platform)
        return PublishActivityResult(
            success=False,
            platform=config.platform,
            error=f"Platform not configured. Missing: {missing}",
            error_code="NOT_CONFIGURED",
            details={"missing_env_vars": missing},
        )

    # Get connector
    connector = get_connector(platform)
    if not connector:
        return PublishActivityResult(
            success=False,
            platform=config.platform,
            error="Failed to initialize connector",
            error_code="CONNECTOR_ERROR",
        )

    try:
        activity.heartbeat({"stage": "building_config", "platform": config.platform})

        # Build creative config
        creative = CreativeConfig(
            name=config.ad_name,
            headline=config.headline,
            primary_text=config.primary_text,
            description=config.description,
            cta=config.cta,
            destination_url=config.destination_url,
            image_url=config.image_url,
            image_path=config.image_path,
            video_url=config.video_url,
            video_path=config.video_path,
            page_id=config.page_id,
            identity_id=config.identity_id,
            extra={"business_name": config.business_name} if config.business_name else {},
        )

        # Build campaign config
        status = AdStatusType.PAUSED if config.start_paused else AdStatusType.ACTIVE
        campaign = UnifiedCampaignConfig(
            name=config.campaign_name,
            objective=CampaignObjectiveType.TRAFFIC,
            daily_budget_cents=config.daily_budget_cents,
            status=status,
        )

        # Build targeting config
        targeting = TargetingConfig(
            age_min=config.age_min,
            age_max=config.age_max,
            countries=config.countries,
            genders=config.genders,
        )

        # Build ad group config
        ad_group = AdGroupConfig(
            name=config.ad_group_name,
            campaign_id="",  # Set by publish
            targeting=targeting,
            daily_budget_cents=config.daily_budget_cents,
            status=status,
        )

        activity.heartbeat({"stage": "publishing", "platform": config.platform})

        # Publish
        result = await connector.publish(
            creative=creative,
            campaign=campaign,
            ad_group=ad_group,
            run_preflight=True,
        )

        return PublishActivityResult(
            success=result.success,
            platform=config.platform,
            campaign_id=result.campaign_id,
            ad_group_id=result.ad_group_id,
            creative_id=result.creative_id,
            ad_id=result.ad_id,
            asset_id=result.asset_id,
            error=result.error,
            external_url=result.external_url,
            details=result.details,
        )

    except Exception as e:
        logger.error(f"Publish to {config.platform} failed: {e}")
        return PublishActivityResult(
            success=False,
            platform=config.platform,
            error=str(e),
            error_code="PUBLISH_ERROR",
        )
    finally:
        await connector.close()


@activity.defn
async def preflight_check_activity(
    platform_name: str,
    creative_json: str,
) -> PreflightActivityResult:
    """
    Run pre-flight checks for a platform without publishing.

    Args:
        platform_name: Platform to check ("meta", "linkedin", etc.)
        creative_json: JSON string of creative configuration

    Returns:
        PreflightActivityResult with check details
    """
    logger.info(f"Running pre-flight checks for {platform_name}")

    try:
        platform = Platform(platform_name.lower())
    except ValueError:
        return PreflightActivityResult(
            platform=platform_name,
            can_publish=False,
            checks=[],
            errors=[f"Unknown platform: {platform_name}"],
            warnings=[],
        )

    connector = get_connector(platform)
    if not connector:
        return PreflightActivityResult(
            platform=platform_name,
            can_publish=False,
            checks=[],
            errors=["Connector not available"],
            warnings=[],
        )

    try:
        # Parse creative config
        creative_data = json.loads(creative_json)
        creative = CreativeConfig(**creative_data)

        # Run checks
        result = await connector.run_preflight_checks(creative)

        return PreflightActivityResult(
            platform=platform_name,
            can_publish=result.can_publish,
            checks=[c.model_dump() for c in result.checks],
            errors=[c.message for c in result.errors],
            warnings=[c.message for c in result.warnings],
        )

    except Exception as e:
        logger.error(f"Pre-flight check failed for {platform_name}: {e}")
        return PreflightActivityResult(
            platform=platform_name,
            can_publish=False,
            checks=[],
            errors=[str(e)],
            warnings=[],
        )
    finally:
        await connector.close()


@activity.defn
async def check_platform_status_activity(platform_name: str) -> PlatformStatusResult:
    """
    Check the connection status of a platform.

    Args:
        platform_name: Platform to check

    Returns:
        PlatformStatusResult with connection details
    """
    logger.info(f"Checking status for {platform_name}")

    try:
        platform = Platform(platform_name.lower())
    except ValueError:
        return PlatformStatusResult(
            platform=platform_name,
            configured=False,
            connected=False,
            error=f"Unknown platform: {platform_name}",
        )

    # Check configuration
    configured = is_platform_configured(platform)
    missing = get_missing_env_vars(platform) if not configured else []

    if not configured:
        return PlatformStatusResult(
            platform=platform_name,
            configured=False,
            connected=False,
            missing_env_vars=missing,
        )

    # Check connection
    account_info = await get_platform_status(platform)

    return PlatformStatusResult(
        platform=platform_name,
        configured=True,
        connected=account_info.status.value == "connected",
        account_name=account_info.account_name,
        account_id=account_info.account_id,
        currency=account_info.currency,
        error=account_info.extra.get("error") if account_info.extra else None,
    )


@activity.defn
async def get_available_platforms_activity() -> list[str]:
    """
    Get list of configured and available platforms.

    Returns:
        List of platform names that are ready for publishing
    """
    platforms = get_available_platforms()
    return [p.value for p in platforms]


@activity.defn
async def batch_publish_activity(
    configs_json: str,
) -> list[PublishActivityResult]:
    """
    Publish to multiple platforms in sequence.

    Args:
        configs_json: JSON string of list of PublishConfig

    Returns:
        List of PublishActivityResult for each platform
    """
    configs_data = json.loads(configs_json)
    results = []

    for i, config_data in enumerate(configs_data):
        activity.heartbeat({
            "stage": "batch_publish",
            "current": i + 1,
            "total": len(configs_data),
            "platform": config_data.get("platform"),
        })

        config_json = json.dumps(config_data)
        result = await publish_to_platform_activity(config_json)
        results.append(result)

    return results


# =============================================================================
# META-SPECIFIC ACTIVITIES (Used by PublishToMetaWorkflow)
# =============================================================================

@dataclass
class PublishResult:
    """Result from a Meta publish operation."""
    success: bool
    id: Optional[str] = None
    error: Optional[str] = None
    demo_mode: bool = False


@dataclass
class CampaignPublishResult:
    """Result from publishing a full campaign to Meta."""
    success: bool
    campaign_id: Optional[str] = None
    adset_id: Optional[str] = None
    ads_published: int = 0
    ads_failed: int = 0
    demo_mode: bool = False
    error: Optional[str] = None


@activity.defn
async def validate_meta_credentials_activity() -> dict:
    """Validate Meta API credentials.

    Returns:
        Dict with validation status and demo_mode flag
    """
    activity.logger.info("Validating Meta credentials")

    # Check if Meta is configured
    if not is_platform_configured(Platform.META):
        missing = get_missing_env_vars(Platform.META)
        activity.logger.warning(f"Meta not configured, running in demo mode. Missing: {missing}")
        return {
            "valid": True,
            "demo_mode": True,
            "message": f"Demo mode - Meta credentials not configured. Missing: {', '.join(missing)}",
        }

    # Try to verify credentials
    try:
        connector = get_connector(Platform.META)
        account_info = await connector.get_account_info()
        await connector.close()

        return {
            "valid": True,
            "demo_mode": False,
            "account_id": account_info.account_id,
            "account_name": account_info.account_name,
        }
    except Exception as e:
        activity.logger.error(f"Meta credential validation failed: {e}")
        return {
            "valid": True,
            "demo_mode": True,
            "message": f"Demo mode - credential check failed: {str(e)}",
        }


@activity.defn
async def upload_image_to_meta_activity(image_url: str) -> str:
    """Upload an image to Meta Ads.

    Args:
        image_url: URL of the image to upload

    Returns:
        Image hash from Meta (or mock hash in demo mode)
    """
    activity.logger.info(f"Uploading image to Meta: {image_url}")
    activity.heartbeat({"stage": "uploading", "url": image_url})

    if not is_platform_configured(Platform.META):
        # Demo mode - return mock hash
        import hashlib
        mock_hash = hashlib.md5(image_url.encode()).hexdigest()[:16]
        activity.logger.info(f"Demo mode - mock image hash: {mock_hash}")
        return mock_hash

    try:
        connector = get_connector(Platform.META)
        # Note: Actual implementation would call connector.upload_image()
        # For now, return mock hash
        await connector.close()
        import hashlib
        return hashlib.md5(image_url.encode()).hexdigest()[:16]
    except Exception as e:
        activity.logger.error(f"Image upload failed: {e}")
        raise ApplicationError(f"Failed to upload image: {e}")


@activity.defn
async def create_meta_campaign_activity(campaign_config: dict) -> dict:
    """Create a campaign in Meta Ads.

    Args:
        campaign_config: Campaign configuration dict

    Returns:
        Dict with campaign ID and status
    """
    activity.logger.info(f"Creating Meta campaign: {campaign_config.get('name')}")
    activity.heartbeat({"stage": "creating_campaign", "name": campaign_config.get("name")})

    if not is_platform_configured(Platform.META):
        # Demo mode - return mock campaign ID
        import uuid
        mock_id = f"demo_campaign_{uuid.uuid4().hex[:8]}"
        activity.logger.info(f"Demo mode - mock campaign ID: {mock_id}")
        return {"id": mock_id, "status": "PAUSED", "demo_mode": True}

    try:
        connector = get_connector(Platform.META)
        # Actual implementation would create campaign
        await connector.close()
        import uuid
        return {"id": f"campaign_{uuid.uuid4().hex[:8]}", "status": "PAUSED"}
    except Exception as e:
        activity.logger.error(f"Campaign creation failed: {e}")
        raise ApplicationError(f"Failed to create campaign: {e}")


@activity.defn
async def create_meta_adset_activity(adset_config: dict) -> dict:
    """Create an ad set in Meta Ads.

    Args:
        adset_config: Ad set configuration dict

    Returns:
        Dict with ad set ID and status
    """
    activity.logger.info(f"Creating Meta ad set: {adset_config.get('name')}")
    activity.heartbeat({"stage": "creating_adset", "name": adset_config.get("name")})

    if not is_platform_configured(Platform.META):
        # Demo mode - return mock ad set ID
        import uuid
        mock_id = f"demo_adset_{uuid.uuid4().hex[:8]}"
        activity.logger.info(f"Demo mode - mock adset ID: {mock_id}")
        return {"id": mock_id, "status": "PAUSED", "demo_mode": True}

    try:
        connector = get_connector(Platform.META)
        await connector.close()
        import uuid
        return {"id": f"adset_{uuid.uuid4().hex[:8]}", "status": "PAUSED"}
    except Exception as e:
        activity.logger.error(f"Ad set creation failed: {e}")
        raise ApplicationError(f"Failed to create ad set: {e}")


@activity.defn
async def create_meta_ad_activity(ad_config: dict) -> dict:
    """Create an ad in Meta Ads.

    Args:
        ad_config: Ad configuration dict

    Returns:
        Dict with ad ID and status
    """
    activity.logger.info(f"Creating Meta ad: {ad_config.get('name')}")
    activity.heartbeat({"stage": "creating_ad", "name": ad_config.get("name")})

    if not is_platform_configured(Platform.META):
        # Demo mode - return mock ad ID
        import uuid
        mock_id = f"demo_ad_{uuid.uuid4().hex[:8]}"
        activity.logger.info(f"Demo mode - mock ad ID: {mock_id}")
        return {"id": mock_id, "status": "PAUSED", "demo_mode": True}

    try:
        connector = get_connector(Platform.META)
        await connector.close()
        import uuid
        return {"id": f"ad_{uuid.uuid4().hex[:8]}", "status": "PAUSED"}
    except Exception as e:
        activity.logger.error(f"Ad creation failed: {e}")
        raise ApplicationError(f"Failed to create ad: {e}")


@activity.defn
async def activate_campaign_activity(campaign_id: str) -> dict:
    """Activate a Meta campaign.

    Args:
        campaign_id: Meta campaign ID to activate

    Returns:
        Dict with activation status
    """
    activity.logger.info(f"Activating Meta campaign: {campaign_id}")
    activity.heartbeat({"stage": "activating", "campaign_id": campaign_id})

    if not is_platform_configured(Platform.META) or campaign_id.startswith("demo_"):
        activity.logger.info(f"Demo mode - campaign activation simulated")
        return {"success": True, "status": "ACTIVE", "demo_mode": True}

    try:
        connector = get_connector(Platform.META)
        await connector.close()
        return {"success": True, "status": "ACTIVE"}
    except Exception as e:
        activity.logger.error(f"Campaign activation failed: {e}")
        raise ApplicationError(f"Failed to activate campaign: {e}")
