# src/connectors/formats.py
"""Ad Format Specifications for All Platforms

Defines the supported ad formats, sizes, and requirements for each platform.
This data is used for:
- Validation before publishing
- Format selection in ad composer
- Pre-flight checks
"""

from .base import AdFormat, Platform, CreativeType


# =============================================================================
# META (Facebook/Instagram) FORMATS
# =============================================================================

META_FORMATS = [
    # Feed formats
    AdFormat(
        name="Feed Square",
        aspect_ratio="1:1",
        width=1080,
        height=1080,
        min_width=600,
        min_height=600,
        max_file_size_mb=30,
        supported_types=[CreativeType.IMAGE, CreativeType.VIDEO, CreativeType.CAROUSEL],
        platform=Platform.META,
        placement="feed",
    ),
    AdFormat(
        name="Feed Portrait",
        aspect_ratio="4:5",
        width=1080,
        height=1350,
        min_width=600,
        min_height=750,
        max_file_size_mb=30,
        supported_types=[CreativeType.IMAGE, CreativeType.VIDEO, CreativeType.CAROUSEL],
        platform=Platform.META,
        placement="feed",
    ),
    AdFormat(
        name="Feed Landscape",
        aspect_ratio="1.91:1",
        width=1200,
        height=628,
        min_width=600,
        min_height=314,
        max_file_size_mb=30,
        supported_types=[CreativeType.IMAGE, CreativeType.VIDEO],
        platform=Platform.META,
        placement="feed",
    ),
    # Stories/Reels formats
    AdFormat(
        name="Stories/Reels",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        min_width=500,
        min_height=889,
        max_file_size_mb=30,
        supported_types=[CreativeType.IMAGE, CreativeType.VIDEO],
        platform=Platform.META,
        placement="stories",
    ),
    # Right column (desktop only)
    AdFormat(
        name="Right Column",
        aspect_ratio="1.91:1",
        width=1200,
        height=628,
        min_width=254,
        min_height=133,
        max_file_size_mb=30,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.META,
        placement="right_column",
    ),
]


# =============================================================================
# LINKEDIN FORMATS
# =============================================================================

LINKEDIN_FORMATS = [
    # Sponsored Content
    AdFormat(
        name="Single Image (Square)",
        aspect_ratio="1:1",
        width=1200,
        height=1200,
        min_width=400,
        min_height=400,
        max_file_size_mb=8,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.LINKEDIN,
        placement="sponsored_content",
    ),
    AdFormat(
        name="Single Image (Landscape)",
        aspect_ratio="1.91:1",
        width=1200,
        height=628,
        min_width=400,
        min_height=209,
        max_file_size_mb=8,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.LINKEDIN,
        placement="sponsored_content",
    ),
    AdFormat(
        name="Single Image (Portrait)",
        aspect_ratio="4:5",
        width=1080,
        height=1350,
        min_width=400,
        min_height=500,
        max_file_size_mb=8,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.LINKEDIN,
        placement="sponsored_content",
    ),
    # Video ads
    AdFormat(
        name="Video (Landscape)",
        aspect_ratio="16:9",
        width=1920,
        height=1080,
        min_width=640,
        min_height=360,
        max_file_size_mb=200,
        supported_types=[CreativeType.VIDEO],
        platform=Platform.LINKEDIN,
        placement="sponsored_content",
    ),
    AdFormat(
        name="Video (Square)",
        aspect_ratio="1:1",
        width=1080,
        height=1080,
        min_width=360,
        min_height=360,
        max_file_size_mb=200,
        supported_types=[CreativeType.VIDEO],
        platform=Platform.LINKEDIN,
        placement="sponsored_content",
    ),
    # Message Ads
    AdFormat(
        name="Message Ad Banner",
        aspect_ratio="1.91:1",
        width=300,
        height=250,
        max_file_size_mb=2,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.LINKEDIN,
        placement="message_ad",
    ),
]


# =============================================================================
# TIKTOK FORMATS
# =============================================================================

TIKTOK_FORMATS = [
    # In-Feed Ads (primary format)
    AdFormat(
        name="In-Feed Video (Vertical)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        min_width=540,
        min_height=960,
        max_file_size_mb=500,
        supported_types=[CreativeType.VIDEO],
        platform=Platform.TIKTOK,
        placement="in_feed",
    ),
    AdFormat(
        name="In-Feed Video (Square)",
        aspect_ratio="1:1",
        width=1080,
        height=1080,
        min_width=540,
        min_height=540,
        max_file_size_mb=500,
        supported_types=[CreativeType.VIDEO],
        platform=Platform.TIKTOK,
        placement="in_feed",
    ),
    # Image ads (Spark Ads)
    AdFormat(
        name="Spark Ad Image (Vertical)",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        min_width=540,
        min_height=960,
        max_file_size_mb=20,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.TIKTOK,
        placement="spark_ad",
    ),
    # TopView (premium placement)
    AdFormat(
        name="TopView",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        min_width=720,
        min_height=1280,
        max_file_size_mb=500,
        supported_types=[CreativeType.VIDEO],
        platform=Platform.TIKTOK,
        placement="topview",
    ),
    # Brand Takeover
    AdFormat(
        name="Brand Takeover",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        max_file_size_mb=500,
        supported_types=[CreativeType.IMAGE, CreativeType.VIDEO],
        platform=Platform.TIKTOK,
        placement="brand_takeover",
    ),
]


# =============================================================================
# GOOGLE ADS FORMATS
# =============================================================================

GOOGLE_FORMATS = [
    # Display Network - Responsive Display Ads
    AdFormat(
        name="Marketing Image (Landscape)",
        aspect_ratio="1.91:1",
        width=1200,
        height=628,
        min_width=600,
        min_height=314,
        max_file_size_mb=5,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.GOOGLE,
        placement="display_responsive",
    ),
    AdFormat(
        name="Marketing Image (Square)",
        aspect_ratio="1:1",
        width=1200,
        height=1200,
        min_width=300,
        min_height=300,
        max_file_size_mb=5,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.GOOGLE,
        placement="display_responsive",
    ),
    AdFormat(
        name="Logo (Landscape)",
        aspect_ratio="4:1",
        width=1200,
        height=300,
        min_width=512,
        min_height=128,
        max_file_size_mb=5,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.GOOGLE,
        placement="display_responsive",
    ),
    AdFormat(
        name="Logo (Square)",
        aspect_ratio="1:1",
        width=1200,
        height=1200,
        min_width=128,
        min_height=128,
        max_file_size_mb=5,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.GOOGLE,
        placement="display_responsive",
    ),
    # YouTube
    AdFormat(
        name="YouTube In-Stream",
        aspect_ratio="16:9",
        width=1920,
        height=1080,
        min_width=426,
        min_height=240,
        max_file_size_mb=256000,  # 256GB max
        supported_types=[CreativeType.VIDEO],
        platform=Platform.GOOGLE,
        placement="youtube_instream",
    ),
    AdFormat(
        name="YouTube Shorts",
        aspect_ratio="9:16",
        width=1080,
        height=1920,
        min_width=540,
        min_height=960,
        max_file_size_mb=256000,
        supported_types=[CreativeType.VIDEO],
        platform=Platform.GOOGLE,
        placement="youtube_shorts",
    ),
    # Discovery/Demand Gen
    AdFormat(
        name="Discovery (Square)",
        aspect_ratio="1:1",
        width=1200,
        height=1200,
        min_width=300,
        min_height=300,
        max_file_size_mb=5,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.GOOGLE,
        placement="discovery",
    ),
    AdFormat(
        name="Discovery (Portrait)",
        aspect_ratio="4:5",
        width=960,
        height=1200,
        min_width=480,
        min_height=600,
        max_file_size_mb=5,
        supported_types=[CreativeType.IMAGE],
        platform=Platform.GOOGLE,
        placement="discovery",
    ),
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_formats_for_platform(platform: Platform) -> list[AdFormat]:
    """Get all supported formats for a platform."""
    format_map = {
        Platform.META: META_FORMATS,
        Platform.LINKEDIN: LINKEDIN_FORMATS,
        Platform.TIKTOK: TIKTOK_FORMATS,
        Platform.GOOGLE: GOOGLE_FORMATS,
    }
    return format_map.get(platform, [])


def get_format_by_aspect_ratio(platform: Platform, aspect_ratio: str) -> AdFormat | None:
    """Get the primary format for a given aspect ratio on a platform."""
    formats = get_formats_for_platform(platform)
    for fmt in formats:
        if fmt.aspect_ratio == aspect_ratio:
            return fmt
    return None


def get_common_aspect_ratios() -> list[str]:
    """Get aspect ratios that work across all platforms."""
    # Find intersection of aspect ratios across all platforms
    all_ratios = []
    for platform in Platform:
        formats = get_formats_for_platform(platform)
        ratios = set(f.aspect_ratio for f in formats)
        if not all_ratios:
            all_ratios = list(ratios)
        else:
            all_ratios = [r for r in all_ratios if r in ratios]
    return all_ratios  # Typically ["1:1"] is universal


def get_image_formats_for_platform(platform: Platform) -> list[AdFormat]:
    """Get only image-compatible formats for a platform."""
    formats = get_formats_for_platform(platform)
    return [f for f in formats if CreativeType.IMAGE in f.supported_types]


def get_video_formats_for_platform(platform: Platform) -> list[AdFormat]:
    """Get only video-compatible formats for a platform."""
    formats = get_formats_for_platform(platform)
    return [f for f in formats if CreativeType.VIDEO in f.supported_types]


# =============================================================================
# TEXT LIMITS BY PLATFORM
# =============================================================================

TEXT_LIMITS = {
    Platform.META: {
        "headline": 40,  # Recommended (255 max)
        "headline_max": 255,
        "primary_text": 125,  # Recommended (no hard limit)
        "description": 30,  # Recommended
        "cta_options": [
            "Learn More", "Shop Now", "Sign Up", "Apply Now", "Book Now",
            "Contact Us", "Download", "Get Offer", "Get Quote", "Subscribe",
            "Watch More", "Get Started", "Order Now", "See Menu", "Send Message"
        ],
    },
    Platform.LINKEDIN: {
        "headline": 70,  # Recommended
        "headline_max": 200,
        "primary_text": 150,  # Recommended (600 max)
        "primary_text_max": 600,
        "description": 100,
        "cta_options": [
            "Apply", "Download", "View Quote", "Learn More", "Sign Up",
            "Subscribe", "Register", "Join", "Attend", "Request Demo"
        ],
    },
    Platform.TIKTOK: {
        "display_name": 40,
        "headline": 100,
        "primary_text": 100,
        "cta_options": [
            "Shop Now", "Learn More", "Sign Up", "Download", "Book Now",
            "Contact Us", "Apply Now", "Subscribe", "Get Quote", "View More"
        ],
    },
    Platform.GOOGLE: {
        "headline": 30,  # Per headline (up to 15 headlines)
        "headline_count": 15,
        "description": 90,  # Per description (up to 4 descriptions)
        "description_count": 4,
        "long_headline": 90,
        "business_name": 25,
        "cta_options": [
            "Apply Now", "Book Now", "Contact Us", "Download", "Learn More",
            "Get Quote", "Shop Now", "Sign Up", "Subscribe", "Visit Site"
        ],
    },
}


def get_text_limits(platform: Platform) -> dict:
    """Get text character limits for a platform."""
    return TEXT_LIMITS.get(platform, {})


def validate_text_length(platform: Platform, field: str, text: str) -> tuple[bool, str]:
    """
    Validate text length against platform limits.

    Returns:
        (is_valid, message)
    """
    limits = get_text_limits(platform)
    max_key = f"{field}_max"
    recommended_key = field

    max_limit = limits.get(max_key)
    recommended_limit = limits.get(recommended_key)

    if max_limit and len(text) > max_limit:
        return False, f"{field} exceeds maximum of {max_limit} characters"

    if recommended_limit and len(text) > recommended_limit:
        return True, f"{field} exceeds recommended {recommended_limit} characters (may be truncated)"

    return True, "OK"
