# src/extractors/brand_extractor.py
"""Brand extraction using Claude AI.

This is the core of Slice 1. It takes scraped website content and uses
Claude to extract a structured BrandProfile that constrains all downstream
ad generation.
"""

import json
import os
import time
from typing import Optional

import anthropic
from pydantic import HttpUrl

from ..models.brand_profile import (
    BrandProfile,
    BrandAssets,
    BrandClaim,
    ClaimRiskLevel,
    ToneMarker,
    ToneCategory,
    SocialProof,
    PageContent,
)
from .scraper import ScrapedPage, scrape_website

# Import logging utilities
try:
    from ..utils.logging import get_logger, log_step, log_success, log_warning, log_error
    from ..utils.retry import retry_sync, RetryConfig
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    import logging
    def get_logger():
        return logging.getLogger("brandtruth")
    def log_step(step, msg): print(f"[{step}] {msg}")
    def log_success(msg): print(f"✅ {msg}")
    def log_warning(msg): print(f"⚠️  {msg}")
    def log_error(msg): print(f"❌ {msg}")

logger = get_logger()


# The extraction prompt - carefully engineered for structured output
EXTRACTION_PROMPT = """You are a brand analyst AI. Your task is to extract a comprehensive brand profile from website content.

Analyze the following scraped website content and extract structured information about the brand.

<website_content>
{content}
</website_content>

Extract and return a JSON object with the following structure. Be thorough but accurate - only include information that is clearly present in the content.

{{
  "brand_name": "The company/product name",
  "tagline": "Main tagline or slogan if present",
  "industry": "The industry/category (e.g., 'HR Tech', 'E-commerce', 'SaaS')",
  
  "value_propositions": [
    "Main benefit or value prop 1",
    "Main benefit or value prop 2"
  ],
  
  "target_audience": "Description of who this product/service is for",
  
  "claims": [
    {{
      "claim": "The specific claim made",
      "claim_type": "statistic|testimonial|feature|benefit",
      "risk_level": "low|medium|high",
      "source_text": "Original context where claim appears"
    }}
  ],
  
  "social_proof": [
    {{
      "proof_type": "testimonial|statistic|logo|award|review",
      "content": "The actual social proof content",
      "attribution": "Who said it or source"
    }}
  ],
  
  "tone_analysis": {{
    "primary_tone": "professional|casual|friendly|authoritative|playful|urgent|empowering|technical|simple|luxurious",
    "secondary_tones": ["tone1", "tone2"],
    "tone_summary": "A 1-2 sentence description of the brand's voice and personality"
  }},
  
  "key_terms": ["important", "keywords", "the", "brand", "uses"],
  "avoided_terms": ["terms", "they", "seem", "to", "avoid"],
  
  "assets": {{
    "primary_colors": ["#hex1", "#hex2"],
    "has_logo": true,
    "has_product_images": true
  }},
  
  "warnings": [
    "Any issues or gaps in the content that might affect ad creation"
  ],
  
  "confidence_score": 0.85
}}

Rules for extraction:
1. Only include claims that are explicitly stated - do not infer
2. Mark claims as "high" risk if they make guarantees, use superlatives, or could be challenged
3. Mark claims as "medium" risk if they are subjective but reasonable
4. Mark claims as "low" risk if they are factual and verifiable
5. Be conservative - it's better to miss a claim than to misrepresent one
6. Extract actual colors from CSS/style information if available
7. Confidence score should reflect how much usable content was found (0.0-1.0)

Return ONLY valid JSON, no other text."""


class BrandExtractor:
    """
    Extract brand profile from website using Claude AI.
    
    This is the primary component of Slice 1. It orchestrates web scraping
    and AI analysis to produce a structured BrandProfile.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_pages: int = 5,
    ):
        """
        Initialize the brand extractor.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_pages: Maximum pages to scrape from website
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.model = model
        self.max_pages = max_pages
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    async def extract(self, url: str) -> BrandProfile:
        """
        Extract brand profile from a website URL.

        Args:
            url: The website URL (e.g., https://careerfied.ai or careerfied.ai)

        Returns:
            Complete BrandProfile object
        """
        # Normalize URL - ensure it has a scheme
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        # Step 1: Scrape the website
        print(f"Scraping {url}...")
        pages = await scrape_website(url, max_pages=self.max_pages)
        
        successful_pages = [p for p in pages if p.error is None]
        print(f"Successfully scraped {len(successful_pages)}/{len(pages)} pages")
        
        if not successful_pages:
            raise ValueError(f"Failed to scrape any pages from {url}")
        
        # Step 2: Prepare content for Claude
        content = self._prepare_content(successful_pages)
        
        # Step 3: Extract with Claude
        print("Analyzing with Claude...")
        extracted = self._extract_with_claude(content)
        
        # Step 4: Build BrandProfile
        profile = self._build_profile(url, extracted, successful_pages)
        
        print(f"Extraction complete. Confidence: {profile.confidence_score:.2f}")
        return profile
    
    def _prepare_content(self, pages: list[ScrapedPage]) -> str:
        """Prepare scraped content for Claude analysis."""
        sections = []
        
        for page in pages:
            section = f"""
=== PAGE: {page.url} ===
TITLE: {page.title}
META DESCRIPTION: {page.meta_description or 'N/A'}

HEADINGS:
{chr(10).join(f'- {h}' for h in page.headings[:15])}

KEY CONTENT:
{chr(10).join(page.paragraphs[:10])}

CALL-TO-ACTIONS:
{chr(10).join(f'- {cta}' for cta in page.ctas)}
"""
            sections.append(section)
        
        # Combine and truncate if needed
        combined = "\n\n".join(sections)
        if len(combined) > 50000:  # Truncate for context window
            combined = combined[:50000] + "\n\n[Content truncated...]"
        
        return combined
    
    def _extract_with_claude(self, content: str) -> dict:
        """Call Claude to extract brand information with retry logic."""
        prompt = EXTRACTION_PROMPT.format(content=content)
        
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
                
                # Parse JSON response
                response_text = message.content[0].text
                
                # Handle potential markdown code blocks
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                try:
                    return json.loads(response_text.strip())
                except json.JSONDecodeError as e:
                    log_error(f"JSON parse error: {e}")
                    raise ValueError(f"Failed to parse Claude response as JSON: {e}")
                    
            except anthropic.APIStatusError as e:
                # Check if retryable (overloaded, rate limit, etc.)
                if e.status_code in (429, 529, 500, 502, 503, 504):
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        log_warning(f"API error {e.status_code} (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                    else:
                        log_error(f"Max retries exceeded. Last error: {e}")
                raise
            except Exception as e:
                # Check for overloaded in error message
                if "overloaded" in str(e).lower() or "529" in str(e):
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        log_warning(f"API overloaded (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                raise
        
        raise RuntimeError("Failed to extract brand profile after all retries")
    
    def _build_profile(
        self,
        url: str,
        extracted: dict,
        pages: list[ScrapedPage]
    ) -> BrandProfile:
        """Build a BrandProfile from extracted data."""
        
        # Convert claims
        claims = []
        for c in extracted.get("claims", []):
            try:
                risk = ClaimRiskLevel(c.get("risk_level", "medium"))
            except ValueError:
                risk = ClaimRiskLevel.MEDIUM
            
            claims.append(BrandClaim(
                claim=c.get("claim", ""),
                claim_type=c.get("claim_type", "feature"),
                risk_level=risk,
                source_url=url,
                source_text=c.get("source_text", ""),
            ))
        
        # Convert social proof
        social_proof = []
        for sp in extracted.get("social_proof", []):
            social_proof.append(SocialProof(
                proof_type=sp.get("proof_type", "testimonial"),
                content=sp.get("content", ""),
                attribution=sp.get("attribution"),
                source_url=url,
            ))
        
        # Convert tone markers
        tone_markers = []
        tone_analysis = extracted.get("tone_analysis", {})
        
        primary_tone = tone_analysis.get("primary_tone")
        if primary_tone:
            try:
                tone_markers.append(ToneMarker(
                    category=ToneCategory(primary_tone),
                    confidence=0.9,
                    evidence="Primary tone from analysis",
                    source_url=url,
                ))
            except ValueError:
                pass
        
        for secondary in tone_analysis.get("secondary_tones", []):
            try:
                tone_markers.append(ToneMarker(
                    category=ToneCategory(secondary),
                    confidence=0.6,
                    evidence="Secondary tone from analysis",
                    source_url=url,
                ))
            except ValueError:
                pass
        
        # Convert page content
        page_contents = []
        for page in pages:
            page_contents.append(PageContent(
                url=page.url,
                title=page.title,
                meta_description=page.meta_description,
                headings=page.headings,
                key_paragraphs=page.paragraphs[:5],
                ctas=page.ctas,
            ))
        
        # Extract image URLs from pages
        all_images = []
        for page in pages:
            for img in page.images:
                if img.get("src"):
                    all_images.append(img["src"])
        
        # Build assets
        assets_data = extracted.get("assets", {})
        assets = BrandAssets(
            primary_colors=assets_data.get("primary_colors", []),
            product_images=all_images[:10] if all_images else [],
        )
        
        # Build final profile
        return BrandProfile(
            brand_name=extracted.get("brand_name", "Unknown"),
            website_url=url,
            tagline=extracted.get("tagline"),
            industry=extracted.get("industry"),
            value_propositions=extracted.get("value_propositions", []),
            target_audience=extracted.get("target_audience"),
            claims=claims,
            social_proof=social_proof,
            tone_markers=tone_markers,
            tone_summary=tone_analysis.get("tone_summary"),
            key_terms=extracted.get("key_terms", []),
            avoided_terms=extracted.get("avoided_terms", []),
            assets=assets,
            pages_analyzed=page_contents,
            confidence_score=extracted.get("confidence_score", 0.5),
            extraction_warnings=extracted.get("warnings", []),
        )


# Convenience function
async def extract_brand(url: str, api_key: Optional[str] = None) -> BrandProfile:
    """
    Extract brand profile from a website URL.
    
    Args:
        url: Website URL
        api_key: Optional Anthropic API key
        
    Returns:
        BrandProfile object
    """
    extractor = BrandExtractor(api_key=api_key)
    return await extractor.extract(url)
