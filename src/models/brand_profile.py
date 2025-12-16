# src/models/brand_profile.py
"""Brand Profile data models for BrandTruth AI.

The BrandProfile is the core data structure that captures everything we know
about a brand from their website. It serves as the constraint layer for all
downstream ad generation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ToneCategory(str, Enum):
    """Categories of brand tone/voice."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    PLAYFUL = "playful"
    URGENT = "urgent"
    EMPOWERING = "empowering"
    TECHNICAL = "technical"
    SIMPLE = "simple"
    LUXURIOUS = "luxurious"


class ClaimRiskLevel(str, Enum):
    """Risk level for brand claims."""
    LOW = "low"           # Factual, verifiable
    MEDIUM = "medium"     # Subjective but reasonable
    HIGH = "high"         # Could be challenged, needs proof
    BLOCKED = "blocked"   # Should not be used in ads


class ToneMarker(BaseModel):
    """A detected tone/voice characteristic."""
    category: ToneCategory
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    evidence: str = Field(description="Text snippet that demonstrates this tone")
    source_url: HttpUrl


class BrandClaim(BaseModel):
    """A specific claim made by the brand."""
    claim: str = Field(description="The actual claim text")
    claim_type: str = Field(description="Type: statistic, testimonial, feature, benefit")
    risk_level: ClaimRiskLevel
    source_url: HttpUrl
    source_text: str = Field(description="Original text context where claim was found")
    verification_notes: Optional[str] = None


class SocialProof(BaseModel):
    """Social proof elements found on the website."""
    proof_type: str = Field(description="Type: testimonial, statistic, logo, award, review")
    content: str
    attribution: Optional[str] = Field(default=None, description="Who said it / source")
    source_url: HttpUrl
    is_verifiable: bool = Field(default=False)


class BrandAssets(BaseModel):
    """Visual and identity assets extracted from the website."""
    logo_url: Optional[HttpUrl] = None
    favicon_url: Optional[HttpUrl] = None
    primary_colors: list[str] = Field(default_factory=list, description="Hex color codes")
    secondary_colors: list[str] = Field(default_factory=list)
    product_images: list[HttpUrl] = Field(default_factory=list)
    hero_images: list[HttpUrl] = Field(default_factory=list)
    screenshots: list[HttpUrl] = Field(default_factory=list)


class PageContent(BaseModel):
    """Content extracted from a single page."""
    url: HttpUrl
    title: str
    meta_description: Optional[str] = None
    headings: list[str] = Field(default_factory=list)
    key_paragraphs: list[str] = Field(default_factory=list)
    ctas: list[str] = Field(default_factory=list, description="Call-to-action buttons/links")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class BrandProfile(BaseModel):
    """
    Complete brand profile extracted from a website.
    
    This is the primary output of Slice 1 (Brand Extractor) and serves as
    the constraint layer for all downstream ad generation.
    """
    # Identity
    brand_name: str
    website_url: HttpUrl
    tagline: Optional[str] = None
    industry: Optional[str] = None
    
    # Core messaging
    value_propositions: list[str] = Field(
        default_factory=list,
        description="Main value props / benefits"
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Inferred target audience from website content"
    )
    
    # Claims & proof
    claims: list[BrandClaim] = Field(default_factory=list)
    social_proof: list[SocialProof] = Field(default_factory=list)
    
    # Tone & voice
    tone_markers: list[ToneMarker] = Field(default_factory=list)
    tone_summary: Optional[str] = Field(
        default=None,
        description="AI-generated summary of brand voice"
    )
    
    # Keywords & language
    key_terms: list[str] = Field(
        default_factory=list,
        description="Important terms/jargon used by the brand"
    )
    avoided_terms: list[str] = Field(
        default_factory=list,
        description="Terms the brand seems to avoid"
    )
    
    # Visual identity
    assets: BrandAssets = Field(default_factory=BrandAssets)
    
    # Source pages
    pages_analyzed: list[PageContent] = Field(default_factory=list)
    
    # Metadata
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_version: str = Field(default="1.0.0")
    confidence_score: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Overall confidence in extraction quality"
    )
    
    # Warnings
    extraction_warnings: list[str] = Field(
        default_factory=list,
        description="Any issues encountered during extraction"
    )

    def get_safe_claims(self) -> list[BrandClaim]:
        """Return only low and medium risk claims safe for ad use."""
        return [c for c in self.claims if c.risk_level in (ClaimRiskLevel.LOW, ClaimRiskLevel.MEDIUM)]
    
    def get_dominant_tone(self) -> Optional[ToneCategory]:
        """Return the most confident tone marker."""
        if not self.tone_markers:
            return None
        return max(self.tone_markers, key=lambda t: t.confidence).category
    
    def to_prompt_context(self) -> str:
        """Generate a text summary suitable for LLM prompts."""
        safe_claims = self.get_safe_claims()
        dominant_tone = self.get_dominant_tone()
        
        return f"""
BRAND: {self.brand_name}
WEBSITE: {self.website_url}
TAGLINE: {self.tagline or 'Not specified'}
INDUSTRY: {self.industry or 'Not specified'}

VALUE PROPOSITIONS:
{chr(10).join(f'- {vp}' for vp in self.value_propositions) or '- None extracted'}

TARGET AUDIENCE: {self.target_audience or 'Not specified'}

SAFE CLAIMS FOR ADS:
{chr(10).join(f'- {c.claim} (source: {c.source_url})' for c in safe_claims[:5]) or '- None available'}

SOCIAL PROOF:
{chr(10).join(f'- {sp.content[:100]}...' for sp in self.social_proof[:3]) or '- None available'}

BRAND TONE: {dominant_tone.value if dominant_tone else 'Not determined'}
TONE SUMMARY: {self.tone_summary or 'Not available'}

KEY TERMS TO USE: {', '.join(self.key_terms[:10]) or 'None specified'}
TERMS TO AVOID: {', '.join(self.avoided_terms[:5]) or 'None specified'}
""".strip()
