# src/models/copy_variant.py
"""Copy Variant data models for ad copy generation.

CopyVariant represents a single ad copy option, complete with
headline, primary text, CTA, and metadata about the angle and
target persona.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CopyAngle(str, Enum):
    """The psychological angle of the ad copy."""
    PAIN = "pain"                    # Focus on problem/frustration
    BENEFIT = "benefit"              # Focus on positive outcome
    CURIOSITY = "curiosity"          # Question or intrigue
    SOCIAL_PROOF = "social_proof"    # Testimonials, numbers
    DIRECT_OFFER = "direct_offer"    # Clear CTA, promotional
    FEAR_OF_MISSING = "fomo"         # Urgency, scarcity
    EDUCATIONAL = "educational"      # How-to, tips


class EmotionalTarget(str, Enum):
    """Primary emotion the copy targets."""
    FRUSTRATION = "frustration"
    HOPE = "hope"
    CURIOSITY = "curiosity"
    CONFIDENCE = "confidence"
    FEAR = "fear"
    EXCITEMENT = "excitement"
    RELIEF = "relief"


class Platform(str, Enum):
    """Target ad platform."""
    META = "meta"          # Facebook + Instagram
    LINKEDIN = "linkedin"
    GOOGLE = "google"


class PlatformCompliance(BaseModel):
    """Platform-specific compliance checks."""
    platform: Platform
    headline_length: int
    headline_limit: int
    headline_ok: bool
    primary_text_length: int
    primary_text_limit: int
    primary_text_ok: bool
    cta_ok: bool
    overall_compliant: bool


class CopyVariant(BaseModel):
    """
    A single ad copy variant.
    
    This is the output of the Copy Generator (Slice 2) and serves as
    input to the Image Matcher (Slice 3) and Ad Composer (Slice 4).
    """
    # Identification
    id: str = Field(description="Unique identifier for this variant")
    campaign_id: Optional[str] = None
    
    # Core copy elements
    headline: str = Field(
        description="Main headline (5-10 words typically)",
        max_length=100
    )
    primary_text: str = Field(
        description="Body copy (2-4 sentences)",
        max_length=500
    )
    cta: str = Field(
        description="Call-to-action button text",
        max_length=30
    )
    
    # Optional elements
    description: Optional[str] = Field(
        default=None,
        description="Secondary text (for some placements)",
        max_length=200
    )
    
    # Metadata
    angle: CopyAngle = Field(description="Psychological angle used")
    persona: str = Field(description="Target persona description")
    emotion: EmotionalTarget = Field(description="Primary emotion targeted")
    
    # Provenance
    proof_sources: list[str] = Field(
        default_factory=list,
        description="URLs/sources for claims used"
    )
    brand_claims_used: list[str] = Field(
        default_factory=list,
        description="Specific brand claims incorporated"
    )
    key_terms_used: list[str] = Field(
        default_factory=list,
        description="Brand key terms incorporated"
    )
    
    # Platform compliance
    platform: Platform = Field(default=Platform.META)
    compliance: Optional[PlatformCompliance] = None
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_prompt_hash: Optional[str] = Field(
        default=None,
        description="Hash of prompt used for reproducibility"
    )
    
    # Quality signals
    quality_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="AI-assessed quality score"
    )
    
    def check_compliance(self, platform: Platform = Platform.META) -> PlatformCompliance:
        """Check if copy meets platform requirements."""
        
        # Platform limits
        limits = {
            Platform.META: {
                "headline": 40,
                "primary_text": 125,  # Recommended, not hard limit
                "cta_options": ["Learn More", "Sign Up", "Get Started", "Shop Now", 
                               "Book Now", "Contact Us", "Download", "Get Offer",
                               "Get Quote", "Subscribe", "Apply Now", "Try Free"]
            },
            Platform.LINKEDIN: {
                "headline": 70,
                "primary_text": 150,
                "cta_options": ["Learn More", "Sign Up", "Register", "Download",
                               "Get Quote", "Apply", "Subscribe", "Contact Us"]
            },
            Platform.GOOGLE: {
                "headline": 30,
                "primary_text": 90,
                "cta_options": []  # More flexible
            }
        }
        
        platform_limits = limits.get(platform, limits[Platform.META])
        
        headline_len = len(self.headline)
        primary_len = len(self.primary_text)
        
        # CTA check (flexible - just check it's reasonable)
        cta_ok = len(self.cta) <= 25 and len(self.cta) >= 2
        
        compliance = PlatformCompliance(
            platform=platform,
            headline_length=headline_len,
            headline_limit=platform_limits["headline"],
            headline_ok=headline_len <= platform_limits["headline"],
            primary_text_length=primary_len,
            primary_text_limit=platform_limits["primary_text"],
            primary_text_ok=primary_len <= platform_limits["primary_text"] * 2,  # Allow some flexibility
            cta_ok=cta_ok,
            overall_compliant=True  # Will be updated
        )
        
        compliance.overall_compliant = (
            compliance.headline_ok and 
            compliance.primary_text_ok and 
            compliance.cta_ok
        )
        
        self.compliance = compliance
        return compliance

    def to_ad_preview(self) -> str:
        """Generate a text preview of how the ad would look."""
        return f"""
┌────────────────────────────────────────┐
│ {self.headline[:38]:<38} │
├────────────────────────────────────────┤
│ {self.primary_text[:76]:<76} │
│ {self.primary_text[76:152] if len(self.primary_text) > 76 else '':<76} │
├────────────────────────────────────────┤
│ [{self.cta}]                           │
└────────────────────────────────────────┘
Angle: {self.angle.value} | Emotion: {self.emotion.value}
""".strip()


class CopyGenerationRequest(BaseModel):
    """Request parameters for copy generation."""
    
    # Required
    brand_profile_json: str = Field(description="Serialized BrandProfile")
    
    # Campaign context
    objective: str = Field(
        default="conversions",
        description="Campaign objective: awareness, traffic, conversions"
    )
    audience_description: str = Field(
        default="",
        description="Target audience description"
    )
    platform: Platform = Field(default=Platform.META)
    
    # Generation parameters
    num_variants: int = Field(default=10, ge=1, le=20)
    
    # Constraints
    tone_override: Optional[str] = Field(
        default=None,
        description="Override extracted tone"
    )
    offer: Optional[str] = Field(
        default=None,
        description="Specific offer to promote"
    )
    must_include_terms: list[str] = Field(
        default_factory=list,
        description="Terms that must appear"
    )
    must_avoid_terms: list[str] = Field(
        default_factory=list,
        description="Terms to avoid"
    )
    
    # Angle distribution
    angle_distribution: Optional[dict[str, int]] = Field(
        default=None,
        description="How many of each angle, e.g., {'pain': 2, 'benefit': 3}"
    )


class CopyGenerationResult(BaseModel):
    """Result of copy generation."""
    
    request_id: str
    variants: list[CopyVariant]
    
    # Metadata
    brand_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generation_time_seconds: float
    
    # Stats
    total_generated: int
    compliant_count: int
    
    # Warnings
    warnings: list[str] = Field(default_factory=list)
    
    def get_by_angle(self, angle: CopyAngle) -> list[CopyVariant]:
        """Get variants by angle."""
        return [v for v in self.variants if v.angle == angle]
    
    def get_compliant_only(self) -> list[CopyVariant]:
        """Get only platform-compliant variants."""
        return [v for v in self.variants 
                if v.compliance and v.compliance.overall_compliant]
