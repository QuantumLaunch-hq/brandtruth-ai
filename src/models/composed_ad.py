# src/models/composed_ad.py
"""Composed Ad data models for final ad creatives.

ComposedAd represents a fully rendered ad with all assets
ready for platform upload.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AdFormat(str, Enum):
    """Standard ad format sizes."""
    SQUARE = "1:1"           # 1080x1080 - Feed
    PORTRAIT = "4:5"         # 1080x1350 - Feed optimal
    STORY = "9:16"           # 1080x1920 - Stories/Reels
    LANDSCAPE = "16:9"       # 1920x1080 - Video covers


class AdFormatSpec(BaseModel):
    """Specifications for an ad format."""
    format: AdFormat
    width: int
    height: int
    name: str
    platform_use: str


# Standard format specifications
FORMAT_SPECS = {
    AdFormat.SQUARE: AdFormatSpec(
        format=AdFormat.SQUARE,
        width=1080,
        height=1080,
        name="Square",
        platform_use="Feed posts, carousel"
    ),
    AdFormat.PORTRAIT: AdFormatSpec(
        format=AdFormat.PORTRAIT,
        width=1080,
        height=1350,
        name="Portrait",
        platform_use="Feed optimal, mobile"
    ),
    AdFormat.STORY: AdFormatSpec(
        format=AdFormat.STORY,
        width=1080,
        height=1920,
        name="Story",
        platform_use="Stories, Reels, TikTok"
    ),
    AdFormat.LANDSCAPE: AdFormatSpec(
        format=AdFormat.LANDSCAPE,
        width=1920,
        height=1080,
        name="Landscape",
        platform_use="Video covers, YouTube"
    ),
}


class TextPosition(str, Enum):
    """Position for text overlay."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"


class CompositionStyle(str, Enum):
    """Visual composition style for the ad."""
    DARK_OVERLAY = "dark_overlay"      # Dark gradient over image
    LIGHT_OVERLAY = "light_overlay"    # Light gradient over image
    SPLIT = "split"                    # Image on one side, text on other
    MINIMAL = "minimal"                # Small text badge
    BOLD = "bold"                      # Large text, high contrast


class RenderedAsset(BaseModel):
    """A single rendered ad asset."""
    format: AdFormat
    width: int
    height: int
    file_path: str
    file_size_bytes: Optional[int] = None
    url: Optional[str] = None  # If uploaded to storage


class ComposedAd(BaseModel):
    """
    A fully composed ad creative.
    
    This is the output of the Ad Composer (Slice 4) and serves as
    input to the HITL Dashboard (Slice 5) and Platform Connectors (Slice 8).
    """
    # Identification
    id: str = Field(description="Unique identifier")
    copy_variant_id: str = Field(description="Source copy variant ID")
    image_match_id: str = Field(description="Source image match ID")
    
    # Copy elements (denormalized for convenience)
    headline: str
    primary_text: str
    cta: str
    
    # Image info
    source_image_url: str
    photographer: str
    photographer_attribution: str
    
    # Composition settings
    style: CompositionStyle = Field(default=CompositionStyle.DARK_OVERLAY)
    text_position: TextPosition = Field(default=TextPosition.BOTTOM)
    overlay_opacity: float = Field(default=0.5, ge=0, le=1)
    
    # Brand elements
    logo_path: Optional[str] = None
    brand_color: str = Field(default="#FFFFFF")
    accent_color: str = Field(default="#007AFF")
    
    # Rendered assets
    assets: dict[str, RenderedAsset] = Field(
        default_factory=dict,
        description="Rendered assets by format key"
    )
    
    # Metadata
    composed_at: datetime = Field(default_factory=datetime.utcnow)
    composition_time_seconds: Optional[float] = None
    
    # Quality
    estimated_text_readability: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Estimated text readability score"
    )
    
    def get_asset(self, format: AdFormat) -> Optional[RenderedAsset]:
        """Get asset by format."""
        return self.assets.get(format.value)
    
    def get_all_file_paths(self) -> list[str]:
        """Get all rendered file paths."""
        return [asset.file_path for asset in self.assets.values()]
    
    def get_primary_asset(self) -> Optional[RenderedAsset]:
        """Get the primary asset (usually square or portrait)."""
        for format in [AdFormat.PORTRAIT, AdFormat.SQUARE, AdFormat.STORY]:
            if format.value in self.assets:
                return self.assets[format.value]
        return None


class CompositionRequest(BaseModel):
    """Request for ad composition."""
    copy_variant_id: str
    image_match_id: str
    headline: str
    primary_text: str
    cta: str
    image_url: str
    photographer: str
    
    # Options
    formats: list[AdFormat] = Field(
        default=[AdFormat.SQUARE, AdFormat.PORTRAIT, AdFormat.STORY]
    )
    style: CompositionStyle = Field(default=CompositionStyle.DARK_OVERLAY)
    text_position: TextPosition = Field(default=TextPosition.BOTTOM)
    
    # Brand
    logo_path: Optional[str] = None
    brand_color: str = "#FFFFFF"
    accent_color: str = "#007AFF"
    
    # Output
    output_dir: str = "./output"


class CompositionResult(BaseModel):
    """Result of ad composition."""
    ad: ComposedAd
    success: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class BatchCompositionResult(BaseModel):
    """Result of batch ad composition."""
    ads: list[ComposedAd]
    total_requested: int
    total_composed: int
    total_assets: int
    total_time_seconds: float
    errors: list[str] = Field(default_factory=list)
    
    def get_all_file_paths(self) -> list[str]:
        """Get all rendered file paths across all ads."""
        paths = []
        for ad in self.ads:
            paths.extend(ad.get_all_file_paths())
        return paths
