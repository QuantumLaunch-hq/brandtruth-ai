# src/models/__init__.py
"""Data models for BrandTruth AI."""

from .brand_profile import (
    BrandProfile,
    BrandAssets,
    BrandClaim,
    ClaimRiskLevel,
    ToneMarker,
    ToneCategory,
    SocialProof,
    PageContent,
)

from .copy_variant import (
    CopyVariant,
    CopyAngle,
    EmotionalTarget,
    Platform,
    PlatformCompliance,
    CopyGenerationRequest,
    CopyGenerationResult,
)

from .image_match import (
    ImageMatch,
    ImageMatchResult,
    BatchImageMatchResult,
    ImageMood,
    ImageComposition,
    TextSafeArea,
    ImageSource,
    ImageSearchRequest,
)

from .composed_ad import (
    ComposedAd,
    CompositionRequest,
    CompositionResult,
    BatchCompositionResult,
    AdFormat,
    FORMAT_SPECS,
    CompositionStyle,
    TextPosition,
    RenderedAsset,
)

__all__ = [
    # Brand Profile
    "BrandProfile",
    "BrandAssets",
    "BrandClaim",
    "ClaimRiskLevel",
    "ToneMarker",
    "ToneCategory",
    "SocialProof",
    "PageContent",
    # Copy Variant
    "CopyVariant",
    "CopyAngle",
    "EmotionalTarget",
    "Platform",
    "PlatformCompliance",
    "CopyGenerationRequest",
    "CopyGenerationResult",
    # Image Match
    "ImageMatch",
    "ImageMatchResult",
    "BatchImageMatchResult",
    "ImageMood",
    "ImageComposition",
    "TextSafeArea",
    "ImageSource",
    "ImageSearchRequest",
    # Composed Ad
    "ComposedAd",
    "CompositionRequest",
    "CompositionResult",
    "BatchCompositionResult",
    "AdFormat",
    "FORMAT_SPECS",
    "CompositionStyle",
    "TextPosition",
    "RenderedAsset",
]
