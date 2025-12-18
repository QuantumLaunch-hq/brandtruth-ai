# src/api/platforms.py
"""API Routes for Multi-Platform Ad Publishing

Endpoints for:
- Checking platform connection status
- Running pre-flight checks
- Publishing to platforms
- Getting available formats
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.connectors import (
    Platform,
    get_connector,
    get_available_platforms,
    get_unavailable_platforms,
    is_platform_configured,
    get_missing_env_vars,
    get_platform_status,
    get_all_platform_statuses,
    get_formats_for_platform,
    get_text_limits,
    CreativeConfig,
    CampaignObjectiveType,
    AdStatusType,
)
from src.connectors.base import (
    CampaignConfig,
    AdGroupConfig,
    TargetingConfig,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/platforms", tags=["platforms"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class PlatformStatus(BaseModel):
    """Status of a single platform."""
    platform: str
    configured: bool
    connected: bool
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    currency: Optional[str] = None
    error: Optional[str] = None
    missing_env_vars: list[str] = Field(default_factory=list)


class AllPlatformsStatus(BaseModel):
    """Status of all platforms."""
    platforms: list[PlatformStatus]
    available_count: int
    total_count: int


class AdFormatInfo(BaseModel):
    """Information about an ad format."""
    name: str
    aspect_ratio: str
    width: int
    height: int
    max_file_size_mb: float
    supported_types: list[str]
    placement: str


class PlatformFormats(BaseModel):
    """Formats available for a platform."""
    platform: str
    formats: list[AdFormatInfo]
    text_limits: dict


class PreflightCheckResult(BaseModel):
    """Result of a single pre-flight check."""
    check_name: str
    passed: bool
    message: str
    severity: str


class PreflightResponse(BaseModel):
    """Response from pre-flight check."""
    platform: str
    can_publish: bool
    checks: list[PreflightCheckResult]
    errors: list[str]
    warnings: list[str]


class CreativeInput(BaseModel):
    """Creative configuration for pre-flight or publish."""
    headline: str
    primary_text: str
    description: str = ""
    cta: str = "Learn More"
    destination_url: str
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    video_url: Optional[str] = None


class TargetingInput(BaseModel):
    """Targeting configuration."""
    age_min: int = 18
    age_max: int = 65
    countries: list[str] = Field(default_factory=lambda: ["US"])
    genders: list[str] = Field(default_factory=lambda: ["all"])


class PublishRequest(BaseModel):
    """Request to publish an ad."""
    platform: str
    creative: CreativeInput
    campaign_name: str = "BrandTruth Campaign"
    ad_group_name: str = "BrandTruth Ad Group"
    daily_budget_cents: int = 1000
    targeting: Optional[TargetingInput] = None
    start_paused: bool = True
    # Platform-specific
    page_id: Optional[str] = None  # Meta
    organization_id: Optional[str] = None  # LinkedIn
    business_name: Optional[str] = None  # Google


class PublishResponse(BaseModel):
    """Response from publishing."""
    success: bool
    platform: str
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    creative_id: Optional[str] = None
    ad_id: Optional[str] = None
    error: Optional[str] = None
    external_url: Optional[str] = None


class MultiPublishRequest(BaseModel):
    """Request to publish to multiple platforms."""
    platforms: list[str]
    creative: CreativeInput
    campaign_name: str = "BrandTruth Campaign"
    daily_budget_cents: int = 1000
    targeting: Optional[TargetingInput] = None
    start_paused: bool = True


class MultiPublishResponse(BaseModel):
    """Response from multi-platform publish."""
    results: list[PublishResponse]
    success_count: int
    failure_count: int


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status", response_model=AllPlatformsStatus)
async def get_all_platforms_status():
    """
    Get connection status for all platforms.

    Returns which platforms are configured, connected, and ready for use.
    """
    statuses = await get_all_platform_statuses()

    platform_statuses = []
    for platform, account_info in statuses.items():
        missing = get_missing_env_vars(platform) if not is_platform_configured(platform) else []
        platform_statuses.append(
            PlatformStatus(
                platform=platform.value,
                configured=is_platform_configured(platform),
                connected=account_info.status.value == "connected",
                account_name=account_info.account_name,
                account_id=account_info.account_id,
                currency=account_info.currency,
                error=account_info.extra.get("error") if account_info.extra else None,
                missing_env_vars=missing,
            )
        )

    available = len([p for p in platform_statuses if p.connected])

    return AllPlatformsStatus(
        platforms=platform_statuses,
        available_count=available,
        total_count=len(platform_statuses),
    )


@router.get("/status/{platform_name}", response_model=PlatformStatus)
async def get_platform_status_endpoint(platform_name: str):
    """
    Get connection status for a specific platform.
    """
    try:
        platform = Platform(platform_name.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform_name}")

    account_info = await get_platform_status(platform)
    missing = get_missing_env_vars(platform) if not is_platform_configured(platform) else []

    return PlatformStatus(
        platform=platform.value,
        configured=is_platform_configured(platform),
        connected=account_info.status.value == "connected",
        account_name=account_info.account_name,
        account_id=account_info.account_id,
        currency=account_info.currency,
        error=account_info.extra.get("error") if account_info.extra else None,
        missing_env_vars=missing,
    )


@router.get("/available")
async def get_available():
    """
    Get list of platforms that are configured and ready.
    """
    available = get_available_platforms()
    unavailable = get_unavailable_platforms()

    return {
        "available": [p.value for p in available],
        "unavailable": [
            {"platform": p.value, "missing": missing}
            for p, missing in unavailable
        ],
    }


@router.get("/formats/{platform_name}", response_model=PlatformFormats)
async def get_platform_formats(platform_name: str):
    """
    Get supported ad formats for a platform.
    """
    try:
        platform = Platform(platform_name.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform_name}")

    formats = get_formats_for_platform(platform)
    text_limits = get_text_limits(platform)

    format_infos = [
        AdFormatInfo(
            name=f.name,
            aspect_ratio=f.aspect_ratio,
            width=f.width,
            height=f.height,
            max_file_size_mb=f.max_file_size_mb,
            supported_types=[t.value for t in f.supported_types],
            placement=f.placement,
        )
        for f in formats
    ]

    return PlatformFormats(
        platform=platform.value,
        formats=format_infos,
        text_limits=text_limits,
    )


@router.post("/preflight/{platform_name}", response_model=PreflightResponse)
async def run_preflight_check(platform_name: str, creative: CreativeInput):
    """
    Run pre-flight checks for a platform without publishing.

    Validates creative content, account status, and policy compliance.
    """
    try:
        platform = Platform(platform_name.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform_name}")

    if not is_platform_configured(platform):
        missing = get_missing_env_vars(platform)
        return PreflightResponse(
            platform=platform_name,
            can_publish=False,
            checks=[],
            errors=[f"Platform not configured. Missing: {missing}"],
            warnings=[],
        )

    connector = get_connector(platform)
    if not connector:
        raise HTTPException(status_code=500, detail="Failed to initialize connector")

    try:
        creative_config = CreativeConfig(
            name="Preflight Check",
            headline=creative.headline,
            primary_text=creative.primary_text,
            description=creative.description,
            cta=creative.cta,
            destination_url=creative.destination_url,
            image_url=creative.image_url,
            image_path=creative.image_path,
            video_url=creative.video_url,
        )

        result = await connector.run_preflight_checks(creative_config)

        return PreflightResponse(
            platform=platform_name,
            can_publish=result.can_publish,
            checks=[
                PreflightCheckResult(
                    check_name=c.check_name,
                    passed=c.passed,
                    message=c.message,
                    severity=c.severity,
                )
                for c in result.checks
            ],
            errors=[c.message for c in result.errors],
            warnings=[c.message for c in result.warnings],
        )

    finally:
        await connector.close()


@router.post("/publish", response_model=PublishResponse)
async def publish_to_platform(request: PublishRequest):
    """
    Publish an ad to a platform.

    This endpoint:
    1. Runs pre-flight checks
    2. Uploads creative assets
    3. Creates campaign, ad group, and ad
    4. Returns IDs for all created entities
    """
    try:
        platform = Platform(request.platform.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {request.platform}")

    if not is_platform_configured(platform):
        missing = get_missing_env_vars(platform)
        return PublishResponse(
            success=False,
            platform=request.platform,
            error=f"Platform not configured. Missing: {missing}",
        )

    connector = get_connector(platform)
    if not connector:
        raise HTTPException(status_code=500, detail="Failed to initialize connector")

    try:
        # Build creative config
        creative = CreativeConfig(
            name=f"{request.campaign_name} Creative",
            headline=request.creative.headline,
            primary_text=request.creative.primary_text,
            description=request.creative.description,
            cta=request.creative.cta,
            destination_url=request.creative.destination_url,
            image_url=request.creative.image_url,
            image_path=request.creative.image_path,
            video_url=request.creative.video_url,
            page_id=request.page_id,
            extra={"business_name": request.business_name} if request.business_name else {},
        )

        # Build campaign config
        status = AdStatusType.PAUSED if request.start_paused else AdStatusType.ACTIVE
        campaign = CampaignConfig(
            name=request.campaign_name,
            objective=CampaignObjectiveType.TRAFFIC,
            daily_budget_cents=request.daily_budget_cents,
            status=status,
        )

        # Build targeting
        targeting_input = request.targeting or TargetingInput()
        targeting = TargetingConfig(
            age_min=targeting_input.age_min,
            age_max=targeting_input.age_max,
            countries=targeting_input.countries,
            genders=targeting_input.genders,
        )

        # Build ad group
        ad_group = AdGroupConfig(
            name=request.ad_group_name,
            campaign_id="",
            targeting=targeting,
            daily_budget_cents=request.daily_budget_cents,
            status=status,
        )

        # Publish
        result = await connector.publish(
            creative=creative,
            campaign=campaign,
            ad_group=ad_group,
            run_preflight=True,
        )

        return PublishResponse(
            success=result.success,
            platform=request.platform,
            campaign_id=result.campaign_id,
            ad_group_id=result.ad_group_id,
            creative_id=result.creative_id,
            ad_id=result.ad_id,
            error=result.error,
            external_url=result.external_url,
        )

    finally:
        await connector.close()


@router.post("/publish/multi", response_model=MultiPublishResponse)
async def publish_to_multiple_platforms(request: MultiPublishRequest):
    """
    Publish an ad to multiple platforms.

    Publishes sequentially to each platform and returns results for all.
    """
    results = []

    for platform_name in request.platforms:
        try:
            platform = Platform(platform_name.lower())
        except ValueError:
            results.append(
                PublishResponse(
                    success=False,
                    platform=platform_name,
                    error=f"Unknown platform: {platform_name}",
                )
            )
            continue

        if not is_platform_configured(platform):
            missing = get_missing_env_vars(platform)
            results.append(
                PublishResponse(
                    success=False,
                    platform=platform_name,
                    error=f"Platform not configured. Missing: {missing}",
                )
            )
            continue

        connector = get_connector(platform)
        if not connector:
            results.append(
                PublishResponse(
                    success=False,
                    platform=platform_name,
                    error="Failed to initialize connector",
                )
            )
            continue

        try:
            # Build configs (same as single publish)
            creative = CreativeConfig(
                name=f"{request.campaign_name} Creative",
                headline=request.creative.headline,
                primary_text=request.creative.primary_text,
                description=request.creative.description,
                cta=request.creative.cta,
                destination_url=request.creative.destination_url,
                image_url=request.creative.image_url,
                image_path=request.creative.image_path,
                video_url=request.creative.video_url,
            )

            status = AdStatusType.PAUSED if request.start_paused else AdStatusType.ACTIVE
            campaign = CampaignConfig(
                name=request.campaign_name,
                objective=CampaignObjectiveType.TRAFFIC,
                daily_budget_cents=request.daily_budget_cents,
                status=status,
            )

            targeting_input = request.targeting or TargetingInput()
            targeting = TargetingConfig(
                age_min=targeting_input.age_min,
                age_max=targeting_input.age_max,
                countries=targeting_input.countries,
                genders=targeting_input.genders,
            )

            ad_group = AdGroupConfig(
                name=f"{request.campaign_name} Ad Group",
                campaign_id="",
                targeting=targeting,
                daily_budget_cents=request.daily_budget_cents,
                status=status,
            )

            result = await connector.publish(
                creative=creative,
                campaign=campaign,
                ad_group=ad_group,
                run_preflight=True,
            )

            results.append(
                PublishResponse(
                    success=result.success,
                    platform=platform_name,
                    campaign_id=result.campaign_id,
                    ad_group_id=result.ad_group_id,
                    creative_id=result.creative_id,
                    ad_id=result.ad_id,
                    error=result.error,
                    external_url=result.external_url,
                )
            )

        except Exception as e:
            results.append(
                PublishResponse(
                    success=False,
                    platform=platform_name,
                    error=str(e),
                )
            )
        finally:
            await connector.close()

    success_count = len([r for r in results if r.success])
    failure_count = len(results) - success_count

    return MultiPublishResponse(
        results=results,
        success_count=success_count,
        failure_count=failure_count,
    )


# =============================================================================
# CAMPAIGN-LEVEL PREFLIGHT
# =============================================================================

class CampaignPreflightRequest(BaseModel):
    """Request for campaign-level preflight checks."""
    campaign_id: str
    platforms: list[str] = Field(default_factory=lambda: ["meta"])


class CampaignPreflightCheck(BaseModel):
    """Single campaign preflight check result."""
    check_name: str
    passed: bool
    message: str
    severity: str  # error, warning, info


class CampaignPreflightResponse(BaseModel):
    """Response from campaign preflight checks."""
    campaign_id: str
    can_publish: bool
    approved_variant_count: int
    platform_checks: dict[str, bool]  # platform -> ready
    checks: list[CampaignPreflightCheck]
    blockers: list[str]
    warnings: list[str]


@router.post("/campaign/preflight", response_model=CampaignPreflightResponse)
async def run_campaign_preflight(request: CampaignPreflightRequest):
    """
    Run comprehensive pre-flight checks before publishing a campaign.

    Validates:
    1. Campaign has approved variants
    2. Target platforms are connected
    3. Ad accounts are ready
    4. Creative content is valid for target platforms

    This should be called before starting a publish workflow to ensure
    all prerequisites are met.
    """
    from src.db.client import get_database
    from src.db.models import VariantStatus

    checks = []
    blockers = []
    warnings = []
    platform_checks = {}

    db = get_database()

    # Check 1: Campaign exists
    campaign = await db.get_campaign(request.campaign_id)
    if not campaign:
        checks.append(CampaignPreflightCheck(
            check_name="campaign_exists",
            passed=False,
            message=f"Campaign {request.campaign_id} not found",
            severity="error",
        ))
        blockers.append("Campaign not found")
        return CampaignPreflightResponse(
            campaign_id=request.campaign_id,
            can_publish=False,
            approved_variant_count=0,
            platform_checks={},
            checks=checks,
            blockers=blockers,
            warnings=warnings,
        )

    checks.append(CampaignPreflightCheck(
        check_name="campaign_exists",
        passed=True,
        message=f"Campaign '{campaign.name}' found",
        severity="info",
    ))

    # Check 2: Has approved variants
    variants = await db.get_campaign_variants(request.campaign_id)
    approved_variants = [v for v in variants if v.status == VariantStatus.APPROVED]

    if len(approved_variants) == 0:
        checks.append(CampaignPreflightCheck(
            check_name="approved_variants",
            passed=False,
            message="No approved variants found. Approve at least one variant to publish.",
            severity="error",
        ))
        blockers.append("No approved variants")
    else:
        checks.append(CampaignPreflightCheck(
            check_name="approved_variants",
            passed=True,
            message=f"{len(approved_variants)} approved variant(s) ready for publishing",
            severity="info",
        ))

    # Check 3: Variants have images
    variants_with_images = [v for v in approved_variants if v.image_url or v.composed_url]
    if approved_variants and len(variants_with_images) < len(approved_variants):
        missing_count = len(approved_variants) - len(variants_with_images)
        checks.append(CampaignPreflightCheck(
            check_name="variant_images",
            passed=False,
            message=f"{missing_count} approved variant(s) missing images",
            severity="error",
        ))
        blockers.append(f"{missing_count} variant(s) missing images")
    elif approved_variants:
        checks.append(CampaignPreflightCheck(
            check_name="variant_images",
            passed=True,
            message="All approved variants have images",
            severity="info",
        ))

    # Check 4: Platform connectivity for each requested platform
    for platform_name in request.platforms:
        try:
            platform = Platform(platform_name.lower())
            configured = is_platform_configured(platform)

            if not configured:
                missing = get_missing_env_vars(platform)
                checks.append(CampaignPreflightCheck(
                    check_name=f"platform_{platform_name}_configured",
                    passed=False,
                    message=f"{platform_name} not configured. Missing: {', '.join(missing)}",
                    severity="error",
                ))
                blockers.append(f"{platform_name} not configured")
                platform_checks[platform_name] = False
                continue

            # Check if connected
            account_info = await get_platform_status(platform)
            is_connected = account_info.status.value == "connected"

            if not is_connected:
                error_msg = account_info.extra.get("error", "Not connected") if account_info.extra else "Not connected"
                checks.append(CampaignPreflightCheck(
                    check_name=f"platform_{platform_name}_connected",
                    passed=False,
                    message=f"{platform_name} not connected: {error_msg}",
                    severity="error",
                ))
                blockers.append(f"{platform_name} not connected")
                platform_checks[platform_name] = False
            else:
                checks.append(CampaignPreflightCheck(
                    check_name=f"platform_{platform_name}_connected",
                    passed=True,
                    message=f"{platform_name} connected (Account: {account_info.account_name or account_info.account_id})",
                    severity="info",
                ))
                platform_checks[platform_name] = True

        except ValueError:
            checks.append(CampaignPreflightCheck(
                check_name=f"platform_{platform_name}_valid",
                passed=False,
                message=f"Unknown platform: {platform_name}",
                severity="error",
            ))
            blockers.append(f"Unknown platform: {platform_name}")
            platform_checks[platform_name] = False

    # Check 5: Destination URL exists (from campaign)
    if not campaign.url:
        checks.append(CampaignPreflightCheck(
            check_name="destination_url",
            passed=False,
            message="Campaign missing destination URL",
            severity="error",
        ))
        blockers.append("Missing destination URL")
    else:
        checks.append(CampaignPreflightCheck(
            check_name="destination_url",
            passed=True,
            message=f"Destination URL: {campaign.url}",
            severity="info",
        ))

    # Check 6: Campaign status (warn if already published)
    if campaign.status.value == "PUBLISHED":
        checks.append(CampaignPreflightCheck(
            check_name="campaign_status",
            passed=True,
            message="Campaign already published - publishing again will create duplicate ads",
            severity="warning",
        ))
        warnings.append("Campaign already published")
    else:
        checks.append(CampaignPreflightCheck(
            check_name="campaign_status",
            passed=True,
            message=f"Campaign status: {campaign.status.value}",
            severity="info",
        ))

    # Determine overall result
    can_publish = len(blockers) == 0

    return CampaignPreflightResponse(
        campaign_id=request.campaign_id,
        can_publish=can_publish,
        approved_variant_count=len(approved_variants),
        platform_checks=platform_checks,
        checks=checks,
        blockers=blockers,
        warnings=warnings,
    )


# Demo endpoint
@router.get("/demo/status")
async def demo_platforms_status():
    """
    Demo endpoint showing platform status without real credentials.
    """
    return {
        "platforms": [
            {
                "platform": "meta",
                "configured": False,
                "connected": False,
                "missing_env_vars": ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
            },
            {
                "platform": "linkedin",
                "configured": False,
                "connected": False,
                "missing_env_vars": ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AD_ACCOUNT_ID"],
            },
            {
                "platform": "tiktok",
                "configured": False,
                "connected": False,
                "missing_env_vars": ["TIKTOK_ACCESS_TOKEN", "TIKTOK_ADVERTISER_ID"],
            },
            {
                "platform": "google",
                "configured": False,
                "connected": False,
                "missing_env_vars": ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CUSTOMER_ID"],
            },
        ],
        "available_count": 0,
        "total_count": 4,
        "note": "This is demo data. Configure platform credentials to enable real connections.",
    }
