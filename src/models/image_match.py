# src/models/image_match.py
"""Image Match data models for stock image selection.

ImageMatch represents a matched stock image for an ad variant,
including metadata about mood, composition, and licensing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ImageMood(str, Enum):
    """The emotional mood of an image."""
    POSITIVE = "positive"          # Happy, uplifting, bright
    PROFESSIONAL = "professional"  # Clean, corporate, serious
    ASPIRATIONAL = "aspirational"  # Success, achievement, goals
    EMPATHETIC = "empathetic"      # Understanding, supportive
    ENERGETIC = "energetic"        # Dynamic, active, movement
    CALM = "calm"                  # Peaceful, relaxed, serene
    TENSE = "tense"                # Urgency, pressure, stress
    NEUTRAL = "neutral"            # Generic, flexible


class ImageComposition(str, Enum):
    """Visual composition style."""
    CENTERED = "centered"              # Subject in center
    RULE_OF_THIRDS = "rule_of_thirds"  # Subject off-center
    MINIMAL = "minimal"                # Clean, lots of whitespace
    BUSY = "busy"                      # Lots of elements
    PORTRAIT = "portrait"              # Person-focused
    ABSTRACT = "abstract"              # Patterns, shapes


class TextSafeArea(str, Enum):
    """Areas safe for text overlay."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class ImageSource(str, Enum):
    """Stock image source."""
    UNSPLASH = "unsplash"
    PEXELS = "pexels"
    AZURE_DALLE = "azure_dalle"  # Azure OpenAI DALL-E 3
    OPENAI_DALLE = "openai_dalle"  # Direct OpenAI DALL-E 3


class ImageMatch(BaseModel):
    """
    A matched stock image for ad copy.
    
    This is the output of the Image Matcher (Slice 3) and serves as
    input to the Ad Composer (Slice 4).
    """
    # Identification
    id: str = Field(description="Unique identifier")
    copy_variant_id: str = Field(description="ID of the copy variant this matches")
    
    # Image data
    image_id: str = Field(description="Source platform image ID")
    image_url: str = Field(description="Full resolution image URL")
    thumb_url: str = Field(description="Thumbnail URL for preview")
    download_url: str = Field(description="URL to download image")
    
    # Source info
    source: ImageSource = Field(default=ImageSource.UNSPLASH)
    photographer: str = Field(description="Photographer name")
    photographer_url: Optional[str] = Field(default=None)
    
    # Search metadata
    search_terms: list[str] = Field(
        default_factory=list,
        description="Search terms used to find this image"
    )
    
    # Visual analysis
    mood: ImageMood = Field(description="Emotional mood of image")
    composition: ImageComposition = Field(description="Visual composition style")
    text_safe_areas: list[TextSafeArea] = Field(
        default_factory=list,
        description="Areas safe for text overlay"
    )
    dominant_colors: list[str] = Field(
        default_factory=list,
        description="Dominant colors in hex"
    )
    
    # Scoring
    match_score: float = Field(
        ge=0,
        le=1,
        description="How well image matches the copy variant"
    )
    relevance_score: Optional[float] = Field(
        default=None,
        description="Search relevance score"
    )
    
    # Licensing
    license: str = Field(default="Unsplash License")
    attribution_required: bool = Field(default=False)
    attribution_text: Optional[str] = Field(default=None)
    
    # Dimensions
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    aspect_ratio: Optional[float] = Field(default=None)
    
    # Metadata
    matched_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_aspect_ratio(self) -> float:
        """Calculate and store aspect ratio."""
        self.aspect_ratio = self.width / self.height if self.height > 0 else 1.0
        return self.aspect_ratio
    
    def is_landscape(self) -> bool:
        """Check if image is landscape orientation."""
        return self.width > self.height
    
    def is_portrait(self) -> bool:
        """Check if image is portrait orientation."""
        return self.height > self.width
    
    def get_attribution(self) -> str:
        """Generate attribution string."""
        if self.source == ImageSource.UNSPLASH:
            return f"Photo by {self.photographer} on Unsplash"
        elif self.source == ImageSource.PEXELS:
            return f"Photo by {self.photographer} on Pexels"
        return f"Photo by {self.photographer}"


class ImageSearchRequest(BaseModel):
    """Request for image search."""
    copy_variant_id: str
    search_terms: list[str]
    mood_preference: Optional[ImageMood] = None
    min_width: int = Field(default=1080)
    min_height: int = Field(default=1080)
    count: int = Field(default=3, ge=1, le=10)


class ImageMatchResult(BaseModel):
    """Result of image matching for a copy variant."""
    copy_variant_id: str
    matches: list[ImageMatch]
    search_terms_used: list[str]
    total_candidates: int
    match_time_seconds: float
    warnings: list[str] = Field(default_factory=list)
    
    def get_best_match(self) -> Optional[ImageMatch]:
        """Get the highest scoring match."""
        if not self.matches:
            return None
        return max(self.matches, key=lambda m: m.match_score)


class BatchImageMatchResult(BaseModel):
    """Result of image matching for multiple copy variants."""
    results: list[ImageMatchResult]
    total_variants: int
    total_matches: int
    total_time_seconds: float
    
    def get_all_matches(self) -> list[ImageMatch]:
        """Get all matches across all variants."""
        all_matches = []
        for result in self.results:
            all_matches.extend(result.matches)
        return all_matches
