# src/composers/image_matcher.py
"""Image matching using Unsplash API.

This is Slice 3. It takes copy variants and finds matching stock
images from Unsplash based on content, mood, and composition needs.
"""

import os
import time
import uuid
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


# Mapping from copy emotions to image moods
EMOTION_TO_MOOD = {
    EmotionalTarget.FRUSTRATION: ImageMood.EMPATHETIC,
    EmotionalTarget.HOPE: ImageMood.ASPIRATIONAL,
    EmotionalTarget.CURIOSITY: ImageMood.PROFESSIONAL,
    EmotionalTarget.CONFIDENCE: ImageMood.PROFESSIONAL,
    EmotionalTarget.FEAR: ImageMood.TENSE,
    EmotionalTarget.EXCITEMENT: ImageMood.ENERGETIC,
    EmotionalTarget.RELIEF: ImageMood.CALM,
}

# Mapping from copy angles to search modifiers
ANGLE_TO_SEARCH_MODIFIER = {
    CopyAngle.PAIN: ["frustrated", "stressed", "problem"],
    CopyAngle.BENEFIT: ["success", "happy", "achievement"],
    CopyAngle.CURIOSITY: ["thinking", "question", "discover"],
    CopyAngle.SOCIAL_PROOF: ["team", "group", "community"],
    CopyAngle.DIRECT_OFFER: ["professional", "business", "clean"],
    CopyAngle.FEAR_OF_MISSING: ["crowd", "trending", "popular"],
    CopyAngle.EDUCATIONAL: ["learning", "study", "knowledge"],
}


class ImageMatcher:
    """
    Match stock images to ad copy variants.
    
    Uses Unsplash API for image search and Claude for intelligent
    search term generation and image scoring.
    """
    
    UNSPLASH_API_URL = "https://api.unsplash.com"
    
    def __init__(
        self,
        unsplash_access_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        use_ai_search_terms: bool = True,
    ):
        """
        Initialize the image matcher.
        
        Args:
            unsplash_access_key: Unsplash API access key
            anthropic_api_key: Anthropic API key for smart search
            use_ai_search_terms: Whether to use Claude for search terms
        """
        self.unsplash_key = unsplash_access_key or os.getenv("UNSPLASH_ACCESS_KEY")
        self.anthropic_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.use_ai_search_terms = use_ai_search_terms
        
        if not self.unsplash_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not set")
        
        self.http_client = httpx.Client(
            headers={"Authorization": f"Client-ID {self.unsplash_key}"},
            timeout=30.0,
        )
        
        if self.use_ai_search_terms and self.anthropic_key:
            self.claude = anthropic.Anthropic(api_key=self.anthropic_key)
        else:
            self.claude = None
    
    def match_single(
        self,
        copy_variant: CopyVariant,
        count: int = 3,
        min_width: int = 1080,
    ) -> ImageMatchResult:
        """
        Find matching images for a single copy variant.
        
        Args:
            copy_variant: The copy variant to match
            count: Number of images to return
            min_width: Minimum image width
            
        Returns:
            ImageMatchResult with matched images
        """
        start_time = time.time()
        warnings = []
        
        # Generate search terms
        if self.use_ai_search_terms and self.claude:
            search_terms = self._generate_ai_search_terms(copy_variant)
        else:
            search_terms = self._generate_basic_search_terms(copy_variant)
        
        # Search Unsplash
        all_images = []
        for term in search_terms[:3]:  # Use top 3 search terms
            try:
                images = self._search_unsplash(term, per_page=10)
                all_images.extend(images)
            except Exception as e:
                warnings.append(f"Search failed for '{term}': {e}")
        
        if not all_images:
            warnings.append("No images found for any search term")
            return ImageMatchResult(
                copy_variant_id=copy_variant.id,
                matches=[],
                search_terms_used=search_terms,
                total_candidates=0,
                match_time_seconds=time.time() - start_time,
                warnings=warnings,
            )
        
        # Deduplicate
        seen_ids = set()
        unique_images = []
        for img in all_images:
            if img["id"] not in seen_ids:
                seen_ids.add(img["id"])
                unique_images.append(img)
        
        # Filter by size
        sized_images = [
            img for img in unique_images
            if img.get("width", 0) >= min_width
        ]
        
        if not sized_images:
            sized_images = unique_images[:10]  # Fallback to any images
            warnings.append(f"No images met minimum width {min_width}, using smaller images")
        
        # Score and rank images
        scored_images = self._score_images(sized_images, copy_variant)
        
        # Take top matches
        top_images = sorted(scored_images, key=lambda x: x["score"], reverse=True)[:count]
        
        # Convert to ImageMatch objects
        matches = []
        target_mood = EMOTION_TO_MOOD.get(copy_variant.emotion, ImageMood.PROFESSIONAL)
        
        for img in top_images:
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
                mood=target_mood,
                composition=self._guess_composition(img),
                text_safe_areas=self._guess_text_areas(img),
                dominant_colors=img.get("color", ["#000000"]) if isinstance(img.get("color"), list) else [img.get("color", "#000000")],
                match_score=img["score"],
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
        """
        Find matching images for multiple copy variants.
        
        Args:
            copy_variants: List of copy variants
            images_per_variant: Number of images per variant
            
        Returns:
            BatchImageMatchResult with all matches
        """
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
    
    def _generate_ai_search_terms(self, copy_variant: CopyVariant) -> list[str]:
        """Use Claude to generate smart search terms."""
        
        prompt = f"""Generate 5 stock photo search terms for this ad:

Headline: {copy_variant.headline}
Body: {copy_variant.primary_text}
Angle: {copy_variant.angle.value}
Emotion: {copy_variant.emotion.value}
Persona: {copy_variant.persona}

Requirements:
- Terms should find PROFESSIONAL stock photos
- Good for business/career context
- Should have space for text overlay
- Avoid cliché stock photos (no handshakes, pointing at screens)

Return ONLY a JSON array of 5 search terms, nothing else.
Example: ["focused professional working", "career growth", "confident job seeker"]"""
        
        try:
            message = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response = message.content[0].text.strip()
            
            # Parse JSON
            if response.startswith("["):
                import json
                terms = json.loads(response)
                if isinstance(terms, list) and len(terms) > 0:
                    return terms
        except Exception as e:
            print(f"AI search term generation failed: {e}")
        
        # Fallback to basic
        return self._generate_basic_search_terms(copy_variant)
    
    def _generate_basic_search_terms(self, copy_variant: CopyVariant) -> list[str]:
        """Generate search terms without AI."""
        
        terms = []
        
        # Base term from key terms
        if copy_variant.key_terms_used:
            terms.append(" ".join(copy_variant.key_terms_used[:2]))
        
        # Add angle modifier
        angle_mods = ANGLE_TO_SEARCH_MODIFIER.get(copy_variant.angle, [])
        if angle_mods:
            terms.append(f"professional {angle_mods[0]}")
        
        # Add persona-based term
        persona_lower = copy_variant.persona.lower()
        if "job" in persona_lower or "career" in persona_lower:
            terms.append("job interview professional")
        elif "business" in persona_lower:
            terms.append("business professional office")
        else:
            terms.append("professional person working")
        
        # Add emotion-based term
        emotion_terms = {
            EmotionalTarget.FRUSTRATION: "person thinking problem",
            EmotionalTarget.HOPE: "person success happy",
            EmotionalTarget.CURIOSITY: "person wondering thinking",
            EmotionalTarget.CONFIDENCE: "confident professional",
            EmotionalTarget.EXCITEMENT: "excited person celebration",
            EmotionalTarget.RELIEF: "relaxed person peaceful",
        }
        if copy_variant.emotion in emotion_terms:
            terms.append(emotion_terms[copy_variant.emotion])
        
        # Generic fallback
        terms.append("professional person laptop")
        
        return terms[:5]
    
    def _search_unsplash(self, query: str, per_page: int = 10) -> list[dict]:
        """Search Unsplash API."""
        
        response = self.http_client.get(
            f"{self.UNSPLASH_API_URL}/search/photos",
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape",  # Better for ads
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    
    def _score_images(
        self,
        images: list[dict],
        copy_variant: CopyVariant,
    ) -> list[dict]:
        """Score images for relevance to copy variant."""
        
        scored = []
        
        for img in images:
            score = 0.5  # Base score
            
            # Prefer landscape for ads
            if img["width"] > img["height"]:
                score += 0.1
            
            # Prefer larger images
            if img["width"] >= 2000:
                score += 0.1
            elif img["width"] >= 1500:
                score += 0.05
            
            # Prefer images with good contrast (darker = easier text overlay)
            color = img.get("color", "#808080")
            if color:
                # Simple brightness check
                try:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    brightness = (r + g + b) / 3
                    if brightness < 128:  # Darker images
                        score += 0.1
                    elif brightness < 180:  # Medium
                        score += 0.05
                except:
                    pass
            
            # Boost based on likes (social proof of quality)
            likes = img.get("likes", 0)
            if likes > 1000:
                score += 0.1
            elif likes > 100:
                score += 0.05
            
            # Add some randomness to avoid same images every time
            import random
            score += random.uniform(0, 0.1)
            
            img["score"] = min(score, 1.0)
            scored.append(img)
        
        return scored
    
    def _guess_composition(self, img: dict) -> ImageComposition:
        """Guess composition style from image metadata."""
        
        # Simple heuristic based on aspect ratio
        ratio = img["width"] / img["height"] if img["height"] > 0 else 1
        
        if ratio > 1.5:
            return ImageComposition.MINIMAL  # Wide = usually minimal
        elif ratio < 0.8:
            return ImageComposition.PORTRAIT
        else:
            return ImageComposition.RULE_OF_THIRDS  # Default assumption
    
    def _guess_text_areas(self, img: dict) -> list[TextSafeArea]:
        """Guess safe text areas from image metadata."""
        
        # Without actual image analysis, assume standard safe areas
        # In production, we'd use computer vision
        return [
            TextSafeArea.BOTTOM,
            TextSafeArea.TOP,
            TextSafeArea.BOTTOM_LEFT,
            TextSafeArea.BOTTOM_RIGHT,
        ]
    
    def close(self):
        """Close HTTP client."""
        self.http_client.close()


# Convenience function
def match_images(
    copy_variants: list[CopyVariant],
    images_per_variant: int = 3,
    unsplash_key: Optional[str] = None,
) -> BatchImageMatchResult:
    """
    Match images to copy variants.
    
    Args:
        copy_variants: List of copy variants
        images_per_variant: Number of images per variant
        unsplash_key: Optional Unsplash API key
        
    Returns:
        BatchImageMatchResult with all matches
    """
    matcher = ImageMatcher(unsplash_access_key=unsplash_key)
    try:
        return matcher.match_batch(copy_variants, images_per_variant)
    finally:
        matcher.close()
