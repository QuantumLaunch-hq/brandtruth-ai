# src/composers/image_matcher_v2.py
"""Vision-enhanced image matching using Claude multimodal.

This is an upgraded Image Matcher that uses Claude's vision capability
to analyze images before selection, filtering out:
- Competitor branding
- Irrelevant images
- Poor composition for text overlay
"""

import base64
import os
import time
import uuid
from io import BytesIO
from typing import Optional

import anthropic
import httpx

from ..models.copy_variant import CopyVariant, CopyAngle, EmotionalTarget
from ..models.image_match import (
    ImageMatch,
    ImageMatchResult,
    BatchImageMatchResult,
    ImageMood,
    ImageComposition,
    TextSafeArea,
    ImageSource,
)


# Vision analysis prompt
VISION_ANALYSIS_PROMPT = """Analyze this image for use in a digital ad for a CAREER/RESUME BUILDING product.

Ad Copy:
HEADLINE: {headline}
BODY: {primary_text}
TARGET EMOTION: {emotion}

Evaluate the image and respond with ONLY a JSON object:

{{
  "suitable": true/false,
  "score": 0.0-1.0,
  "reasons": {{
    "relevance": 0.0-1.0,
    "mood_match": 0.0-1.0, 
    "text_space": 0.0-1.0,
    "brand_safe": 0.0-1.0
  }},
  "brand_risks": ["List any visible brand names, logos, or trademarks"],
  "text_safe_areas": ["top", "bottom", "left", "right", "center"],
  "rejection_reason": "If suitable=false, explain why",
  "composition": "minimal|centered|rule_of_thirds|busy|portrait|abstract",
  "dominant_mood": "positive|professional|aspirational|empathetic|energetic|calm|tense|neutral",
  "background_brightness": "dark|medium|light"
}}

SCORING RULES:
- relevance: How well does this image CONCEPTUALLY relate to careers, job searching, resumes, or professional growth?
  * 0.9-1.0: Directly career-related (person at desk, professional setting, documents)
  * 0.7-0.8: Strong metaphor (stairs=growth, lightbulb=ideas, path=journey)
  * 0.4-0.6: Weak metaphor (generic objects, abstract patterns)
  * 0.0-0.3: Unrelated (food, nature without clear metaphor, random objects)
  
- brand_safe: 1.0 if NO brands visible, 0.0 if ANY competitor visible
  * Competitors: LinkedIn, Indeed, Glassdoor, Monster, ZipRecruiter, etc.
  * Also reject: Any app screenshots, UI mockups with readable text

- text_space: 1.0 if large clear area for text, 0.0 if busy throughout

- mood_match: Does the emotional tone support the ad message?

FINAL SCORE CALCULATION:
score = (relevance * 0.4) + (mood_match * 0.2) + (text_space * 0.2) + (brand_safe * 0.2)

SUITABILITY RULES:
- suitable=false if brand_safe < 0.5
- suitable=false if relevance < 0.5
- suitable=false if text_space < 0.4
- suitable=false if score < 0.6

Be STRICT. We'd rather reject 10 mediocre images than use 1 bad one."""


class VisionImageMatcher:
    """
    Vision-enhanced image matcher using Claude multimodal.
    
    This analyzes each candidate image to ensure:
    - No competitor branding
    - Relevant to ad concept
    - Good composition for text
    - Appropriate mood
    """
    
    UNSPLASH_API_URL = "https://api.unsplash.com"
    
    def __init__(
        self,
        unsplash_access_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        self.unsplash_key = unsplash_access_key or os.getenv("UNSPLASH_ACCESS_KEY")
        self.anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.unsplash_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not set")
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.http_client = httpx.Client(
            headers={"Authorization": f"Client-ID {self.unsplash_key}"},
            timeout=30.0,
        )
        self.claude = anthropic.Anthropic(api_key=self.anthropic_key)
    
    def match_single(
        self,
        copy_variant: CopyVariant,
        count: int = 3,
        candidates_to_analyze: int = 8,
    ) -> ImageMatchResult:
        """
        Find matching images with vision analysis.
        
        Args:
            copy_variant: The copy variant to match
            count: Number of final images to return
            candidates_to_analyze: How many candidates to analyze with vision
        """
        start_time = time.time()
        warnings = []
        
        # Generate search terms
        search_terms = self._generate_search_terms(copy_variant)
        
        # Search Unsplash
        all_images = []
        for term in search_terms[:3]:
            try:
                images = self._search_unsplash(term, per_page=10)
                all_images.extend(images)
            except Exception as e:
                warnings.append(f"Search failed for '{term}': {e}")

        # Fallback to generic search if no specific images found
        if not all_images:
            fallback_terms = ["business professional", "career success", "modern office"]
            warnings.append("Using fallback search terms")
            print("  No specific images found, trying fallback search...")
            for term in fallback_terms:
                try:
                    images = self._search_unsplash(term, per_page=10)
                    all_images.extend(images)
                    if all_images:
                        break
                except Exception as e:
                    warnings.append(f"Fallback search failed for '{term}': {e}")

        if not all_images:
            return ImageMatchResult(
                copy_variant_id=copy_variant.id,
                matches=[],
                search_terms_used=search_terms,
                total_candidates=0,
                match_time_seconds=time.time() - start_time,
                warnings=["No images found even with fallback"],
            )
        
        # Deduplicate
        seen_ids = set()
        unique_images = []
        for img in all_images:
            if img["id"] not in seen_ids:
                seen_ids.add(img["id"])
                unique_images.append(img)
        
        # Take top candidates by basic score for vision analysis
        candidates = sorted(
            unique_images,
            key=lambda x: x.get("likes", 0),
            reverse=True
        )[:candidates_to_analyze]
        
        # Analyze with vision
        print(f"  Analyzing {len(candidates)} candidates with vision...")
        analyzed = []
        
        for img in candidates:
            try:
                analysis = self._analyze_image_with_vision(
                    image_url=img["urls"]["small"],  # Use small for faster analysis
                    copy_variant=copy_variant,
                )
                
                if analysis and analysis.get("suitable", False):
                    img["vision_analysis"] = analysis
                    img["vision_score"] = analysis.get("score", 0.5)
                    analyzed.append(img)
                    print(f"    ✓ Image {img['id'][:8]}: score {analysis.get('score', 0):.2f}")
                else:
                    reason = analysis.get("rejection_reason", "Unknown") if analysis else "Analysis failed"
                    print(f"    ✗ Image {img['id'][:8]}: {reason[:50]}")
                    
            except Exception as e:
                warnings.append(f"Vision analysis failed for {img['id']}: {e}")
        
        if not analyzed:
            warnings.append("No images passed vision analysis")
            # Fallback to basic matching
            print("  Falling back to basic matching...")
            analyzed = unique_images[:count]
            for img in analyzed:
                img["vision_score"] = 0.5
        
        # Sort by vision score and take top
        analyzed.sort(key=lambda x: x.get("vision_score", 0), reverse=True)
        top_images = analyzed[:count]
        
        # Convert to ImageMatch objects
        matches = []
        for img in top_images:
            analysis = img.get("vision_analysis", {})
            
            # Determine mood from analysis
            mood_str = analysis.get("dominant_mood", "professional")
            try:
                mood = ImageMood(mood_str)
            except ValueError:
                mood = ImageMood.PROFESSIONAL
            
            # Determine composition
            comp_str = analysis.get("composition", "rule_of_thirds")
            try:
                composition = ImageComposition(comp_str)
            except ValueError:
                composition = ImageComposition.RULE_OF_THIRDS
            
            # Parse text safe areas
            safe_areas_str = analysis.get("text_safe_areas", ["bottom"])
            safe_areas = []
            for area in safe_areas_str:
                try:
                    safe_areas.append(TextSafeArea(area.lower()))
                except ValueError:
                    pass
            if not safe_areas:
                safe_areas = [TextSafeArea.BOTTOM]
            
            match = ImageMatch(
                id=f"img-{uuid.uuid4().hex[:8]}",
                copy_variant_id=copy_variant.id,
                image_id=img["id"],
                image_url=img["urls"]["regular"],
                thumb_url=img["urls"]["thumb"],
                download_url=img["urls"]["full"],
                source=ImageSource.UNSPLASH,
                photographer=img["user"]["name"],
                photographer_url=img["user"]["links"]["html"],
                search_terms=search_terms,
                mood=mood,
                composition=composition,
                text_safe_areas=safe_areas,
                dominant_colors=[img.get("color", "#000000")],
                match_score=img.get("vision_score", 0.5),
                width=img["width"],
                height=img["height"],
                license="Unsplash License",
                attribution_required=False,
            )
            match.calculate_aspect_ratio()
            matches.append(match)
        
        return ImageMatchResult(
            copy_variant_id=copy_variant.id,
            matches=matches,
            search_terms_used=search_terms,
            total_candidates=len(unique_images),
            match_time_seconds=time.time() - start_time,
            warnings=warnings,
        )
    
    def match_batch(
        self,
        copy_variants: list[CopyVariant],
        images_per_variant: int = 3,
    ) -> BatchImageMatchResult:
        """Match images for multiple variants."""
        start_time = time.time()
        results = []
        
        for i, variant in enumerate(copy_variants):
            print(f"Matching images for variant {i+1}/{len(copy_variants)}...")
            result = self.match_single(variant, count=images_per_variant)
            results.append(result)
        
        total_matches = sum(len(r.matches) for r in results)
        
        return BatchImageMatchResult(
            results=results,
            total_variants=len(copy_variants),
            total_matches=total_matches,
            total_time_seconds=time.time() - start_time,
        )
    
    def _generate_search_terms(self, copy_variant: CopyVariant) -> list[str]:
        """Generate search terms using Claude with retry logic."""
        
        prompt = f"""Generate 5 stock photo search terms for this ad:

Headline: {copy_variant.headline}
Body: {copy_variant.primary_text}
Angle: {copy_variant.angle.value}
Emotion: {copy_variant.emotion.value}

Requirements:
- Find PROFESSIONAL stock photos suitable for business ads
- NO photos with visible brand logos or app screenshots
- Photos should have clear space for text overlay
- Prefer abstract, metaphorical images over literal ones
- Avoid: screenshots, UI mockups, branded products

Return ONLY a JSON array of 5 search terms.
Example: ["professional workspace minimal", "career growth abstract", "success concept clean"]"""
        
        max_attempts = 5
        base_delay = 2.0
        
        for attempt in range(max_attempts):
            try:
                message = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response = message.content[0].text.strip()
                if response.startswith("["):
                    import json
                    terms = json.loads(response)
                    if isinstance(terms, list):
                        return terms
                        
            except anthropic.APIStatusError as e:
                if e.status_code in (429, 529, 500, 502, 503, 504):
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"    ⚠️  API error {e.status_code} (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                print(f"Search term generation failed: {e}")
            except Exception as e:
                if "overloaded" in str(e).lower() or "529" in str(e):
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"    ⚠️  API overloaded (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                print(f"Search term generation failed: {e}")
        
        # Fallback
        return [
            "professional workspace minimal",
            "career success abstract",
            "business growth concept",
            "professional person thinking",
            "modern office clean"
        ]
    
    def _search_unsplash(self, query: str, per_page: int = 10) -> list[dict]:
        """Search Unsplash API."""
        try:
            response = self.http_client.get(
                f"{self.UNSPLASH_API_URL}/search/photos",
                params={
                    "query": query,
                    "per_page": per_page,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            return results
        except Exception as e:
            print(f"    Unsplash search error for '{query}': {e}")
            return []
    
    def _analyze_image_with_vision(
        self,
        image_url: str,
        copy_variant: CopyVariant,
    ) -> Optional[dict]:
        """Analyze an image using Claude vision with retry logic."""
        
        max_attempts = 5
        base_delay = 2.0
        
        try:
            # Download image (no retry needed - just HTTP)
            response = self.http_client.get(image_url)
            response.raise_for_status()
            
            # Convert to base64
            image_data = base64.b64encode(response.content).decode("utf-8")
            
            # Determine media type
            content_type = response.headers.get("content-type", "image/jpeg")
            if "png" in content_type:
                media_type = "image/png"
            elif "webp" in content_type:
                media_type = "image/webp"
            else:
                media_type = "image/jpeg"
            
            # Build prompt
            prompt = VISION_ANALYSIS_PROMPT.format(
                headline=copy_variant.headline,
                primary_text=copy_variant.primary_text,
                emotion=copy_variant.emotion.value,
            )
            
            # Call Claude with vision - with retry
            for attempt in range(max_attempts):
                try:
                    message = self.claude.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": media_type,
                                            "data": image_data,
                                        },
                                    },
                                    {
                                        "type": "text",
                                        "text": prompt,
                                    }
                                ],
                            }
                        ]
                    )
                    
                    response_text = message.content[0].text.strip()
                    
                    # Parse JSON
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0]
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0]
                    
                    import json
                    return json.loads(response_text.strip())
                    
                except anthropic.APIStatusError as e:
                    if e.status_code in (429, 529, 500, 502, 503, 504):
                        if attempt < max_attempts - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"    ⚠️  Vision API error {e.status_code} (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                            time.sleep(delay)
                            continue
                    raise
                except Exception as e:
                    if "overloaded" in str(e).lower() or "529" in str(e):
                        if attempt < max_attempts - 1:
                            delay = base_delay * (2 ** attempt)
                            print(f"    ⚠️  Vision API overloaded (attempt {attempt + 1}/{max_attempts}). Retrying in {delay:.1f}s...")
                            time.sleep(delay)
                            continue
                    raise
            
            return None
            
        except Exception as e:
            print(f"    Vision analysis error: {e}")
            return None
    
    def close(self):
        """Close HTTP client."""
        self.http_client.close()


# Convenience function
def match_images_v2(
    copy_variants: list[CopyVariant],
    images_per_variant: int = 3,
    unsplash_key: Optional[str] = None,
) -> BatchImageMatchResult:
    """
    Match images to copy variants using vision analysis.
    """
    matcher = VisionImageMatcher(unsplash_access_key=unsplash_key)
    try:
        return matcher.match_batch(copy_variants, images_per_variant)
    finally:
        matcher.close()
