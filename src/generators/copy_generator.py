# src/generators/copy_generator.py
"""Ad copy generation using Claude AI.

This is Slice 2. It takes a BrandProfile and generates constrained
ad copy variants that respect brand truth.
"""

import hashlib
import json
import os
import time
import uuid
from typing import Optional

import anthropic

from ..models.brand_profile import BrandProfile
from ..models.copy_variant import (
    CopyAngle,
    CopyGenerationRequest,
    CopyGenerationResult,
    CopyVariant,
    EmotionalTarget,
    Platform,
)


# The generation prompt - carefully engineered for structured output
GENERATION_PROMPT = """You are an expert performance marketer and copywriter. Generate ad copy variants for {platform} ads.

<brand_context>
{brand_context}
</brand_context>

<campaign>
Objective: {objective}
Target Audience: {audience}
{offer_line}
</campaign>

<constraints>
MANDATORY RULES:
1. Only use claims from the SAFE CLAIMS list - never make up statistics or guarantees
2. Match the brand tone described above
3. Use KEY TERMS naturally where appropriate  
4. Never use TERMS TO AVOID
5. Keep headlines under {headline_limit} characters
6. Keep primary text under {primary_text_limit} characters
7. CTAs should be action-oriented and 2-4 words
</constraints>

<format>
Generate exactly {num_variants} ad copy variants as a JSON array.

Each variant must have this structure:
{{
  "headline": "Your headline here (under {headline_limit} chars)",
  "primary_text": "Your body copy here. 2-3 sentences that hook and persuade.",
  "cta": "Action Button",
  "angle": "pain|benefit|curiosity|social_proof|direct_offer|fomo|educational",
  "persona": "Brief description of target persona",
  "emotion": "frustration|hope|curiosity|confidence|fear|excitement|relief",
  "brand_claims_used": ["claim 1 used", "claim 2 used"],
  "key_terms_used": ["term1", "term2"],
  "quality_score": 0.85
}}

ANGLE DISTRIBUTION:
{angle_distribution}

Return ONLY valid JSON array, no other text.
</format>"""


class CopyGenerator:
    """
    Generate constrained ad copy from BrandProfile.
    
    This is the core of Slice 2. It ensures all generated copy
    respects brand truth and platform requirements.
    """
    
    # Default angle distribution
    DEFAULT_ANGLES = {
        CopyAngle.PAIN: 2,
        CopyAngle.BENEFIT: 3,
        CopyAngle.CURIOSITY: 2,
        CopyAngle.SOCIAL_PROOF: 1,
        CopyAngle.DIRECT_OFFER: 2,
    }
    
    # Platform limits
    PLATFORM_LIMITS = {
        Platform.META: {"headline": 40, "primary_text": 125},
        Platform.LINKEDIN: {"headline": 70, "primary_text": 150},
        Platform.GOOGLE: {"headline": 30, "primary_text": 90},
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """
        Initialize the copy generator.
        
        Args:
            api_key: Anthropic API key (defaults to env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate(
        self,
        brand_profile: BrandProfile,
        objective: str = "conversions",
        audience: str = "",
        platform: Platform = Platform.META,
        num_variants: int = 10,
        offer: Optional[str] = None,
        angle_distribution: Optional[dict[CopyAngle, int]] = None,
    ) -> CopyGenerationResult:
        """
        Generate ad copy variants from a brand profile.
        
        Args:
            brand_profile: Extracted brand profile
            objective: Campaign objective
            audience: Target audience (overrides brand profile if provided)
            platform: Target platform
            num_variants: Number of variants to generate
            offer: Optional specific offer
            angle_distribution: How many of each angle
            
        Returns:
            CopyGenerationResult with all variants
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]
        
        # Use brand profile audience if not specified
        if not audience and brand_profile.target_audience:
            audience = brand_profile.target_audience
        
        # Build the prompt
        prompt = self._build_prompt(
            brand_profile=brand_profile,
            objective=objective,
            audience=audience,
            platform=platform,
            num_variants=num_variants,
            offer=offer,
            angle_distribution=angle_distribution or self.DEFAULT_ANGLES,
        )
        
        # Generate with Claude
        print(f"Generating {num_variants} copy variants...")
        raw_variants = self._generate_with_claude(prompt)
        
        # Parse and validate
        variants = self._parse_variants(
            raw_variants=raw_variants,
            brand_profile=brand_profile,
            platform=platform,
            request_id=request_id,
            prompt=prompt,
        )
        
        # Check compliance
        compliant_count = 0
        for variant in variants:
            compliance = variant.check_compliance(platform)
            if compliance.overall_compliant:
                compliant_count += 1
        
        generation_time = time.time() - start_time
        
        # Build result
        result = CopyGenerationResult(
            request_id=request_id,
            variants=variants,
            brand_name=brand_profile.brand_name,
            generation_time_seconds=generation_time,
            total_generated=len(variants),
            compliant_count=compliant_count,
            warnings=self._collect_warnings(variants, brand_profile),
        )
        
        print(f"Generated {len(variants)} variants in {generation_time:.1f}s")
        print(f"Compliant: {compliant_count}/{len(variants)}")
        
        return result
    
    def _build_prompt(
        self,
        brand_profile: BrandProfile,
        objective: str,
        audience: str,
        platform: Platform,
        num_variants: int,
        offer: Optional[str],
        angle_distribution: dict,
    ) -> str:
        """Build the generation prompt."""
        
        limits = self.PLATFORM_LIMITS[platform]
        
        # Format angle distribution
        angle_lines = []
        for angle, count in angle_distribution.items():
            if isinstance(angle, CopyAngle):
                angle_lines.append(f"- {count} variants with '{angle.value}' angle")
            else:
                angle_lines.append(f"- {count} variants with '{angle}' angle")
        
        offer_line = f"Offer: {offer}" if offer else "Offer: General promotion"
        
        return GENERATION_PROMPT.format(
            platform=platform.value.upper(),
            brand_context=brand_profile.to_prompt_context(),
            objective=objective,
            audience=audience or "Not specified",
            offer_line=offer_line,
            headline_limit=limits["headline"],
            primary_text_limit=limits["primary_text"],
            num_variants=num_variants,
            angle_distribution="\n".join(angle_lines),
        )
    
    def _generate_with_claude(self, prompt: str) -> list[dict]:
        """Call Claude to generate copy variants with retry logic."""
        
        max_attempts = 5
        base_delay = 2.0
        
        for attempt in range(max_attempts):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                response_text = message.content[0].text
                
                # Handle markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                try:
                    variants = json.loads(response_text.strip())
                    if not isinstance(variants, list):
                        variants = [variants]
                    return variants
                except json.JSONDecodeError as e:
                    print(f"JSON parse error: {e}")
                    raise ValueError(f"Failed to parse Claude response: {e}")
                    
            except anthropic.APIStatusError as e:
                if e.status_code in (429, 529, 500, 502, 503, 504):
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠️  API error {e.status_code} (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"❌ Max retries exceeded. Last error: {e}")
                raise
            except Exception as e:
                if "overloaded" in str(e).lower() or "529" in str(e):
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"⚠️  API overloaded (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                raise
        
        raise RuntimeError("Failed to generate copy after all retries")
    
    def _parse_variants(
        self,
        raw_variants: list[dict],
        brand_profile: BrandProfile,
        platform: Platform,
        request_id: str,
        prompt: str,
    ) -> list[CopyVariant]:
        """Parse raw JSON into CopyVariant objects."""
        
        variants = []
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        
        for i, raw in enumerate(raw_variants):
            try:
                # Map angle string to enum
                angle_str = raw.get("angle", "benefit").lower()
                try:
                    angle = CopyAngle(angle_str)
                except ValueError:
                    angle = CopyAngle.BENEFIT
                
                # Map emotion string to enum
                emotion_str = raw.get("emotion", "hope").lower()
                try:
                    emotion = EmotionalTarget(emotion_str)
                except ValueError:
                    emotion = EmotionalTarget.HOPE
                
                variant = CopyVariant(
                    id=f"{request_id}-{i+1:02d}",
                    headline=raw.get("headline", "")[:100],
                    primary_text=raw.get("primary_text", "")[:500],
                    cta=raw.get("cta", "Learn More")[:30],
                    angle=angle,
                    persona=raw.get("persona", "General audience"),
                    emotion=emotion,
                    proof_sources=[str(brand_profile.website_url)],
                    brand_claims_used=raw.get("brand_claims_used", []),
                    key_terms_used=raw.get("key_terms_used", []),
                    platform=platform,
                    generation_prompt_hash=prompt_hash,
                    quality_score=raw.get("quality_score"),
                )
                
                variants.append(variant)
                
            except Exception as e:
                print(f"Warning: Failed to parse variant {i}: {e}")
                continue
        
        return variants
    
    def _collect_warnings(
        self,
        variants: list[CopyVariant],
        brand_profile: BrandProfile,
    ) -> list[str]:
        """Collect warnings about the generation."""
        
        warnings = []
        
        # Check for non-compliant variants
        non_compliant = [v for v in variants 
                        if v.compliance and not v.compliance.overall_compliant]
        if non_compliant:
            warnings.append(
                f"{len(non_compliant)} variants exceed platform character limits"
            )
        
        # Check for missing social proof
        if not brand_profile.social_proof:
            warnings.append(
                "No social proof available - social_proof angle variants may be weak"
            )
        
        # Check for high-risk claims being used
        high_risk_claims = [c.claim for c in brand_profile.claims 
                          if c.risk_level.value == "high"]
        for variant in variants:
            for claim in variant.brand_claims_used:
                if any(hr in claim for hr in high_risk_claims):
                    warnings.append(
                        f"Variant {variant.id} may use high-risk claim"
                    )
                    break
        
        return warnings


# Convenience function
def generate_copy(
    brand_profile: BrandProfile,
    objective: str = "conversions",
    audience: str = "",
    platform: Platform = Platform.META,
    num_variants: int = 10,
    offer: Optional[str] = None,
    api_key: Optional[str] = None,
) -> CopyGenerationResult:
    """
    Generate ad copy variants from a brand profile.
    
    Args:
        brand_profile: Extracted brand profile
        objective: Campaign objective
        audience: Target audience description
        platform: Target platform
        num_variants: Number of variants to generate
        offer: Optional specific offer
        api_key: Optional Anthropic API key
        
    Returns:
        CopyGenerationResult with all variants
    """
    generator = CopyGenerator(api_key=api_key)
    return generator.generate(
        brand_profile=brand_profile,
        objective=objective,
        audience=audience,
        platform=platform,
        num_variants=num_variants,
        offer=offer,
    )
