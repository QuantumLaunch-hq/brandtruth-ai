# src/composers/image_provider.py
"""Multi-source Image Provider with fallback chain.

Provides images from multiple sources with automatic fallback:
1. Azure DALL-E 3 (AI-generated, uses Azure credits)
2. Pexels API (free, high-quality curated stock)
3. Unsplash API (free, community stock - original source)

This replaces direct Unsplash dependency with a resilient multi-source approach.
"""

import os
import uuid
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx

from ..models.copy_variant import CopyVariant
from ..models.image_match import (
    ImageMatch,
    ImageMatchResult,
    ImageMood,
    ImageComposition,
    TextSafeArea,
    ImageSource,
)
from .pexels_client import get_pexels_client, PexelsClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ImageProviderPriority(str, Enum):
    """Priority order for image sources."""
    DALLE_FIRST = "dalle_first"      # AI generation first, then stock
    STOCK_FIRST = "stock_first"      # Stock photos first, DALL-E as fallback
    STOCK_ONLY = "stock_only"        # Only use stock photos
    DALLE_ONLY = "dalle_only"        # Only use AI generation


@dataclass
class ImageProviderConfig:
    """Configuration for multi-source image provider."""
    priority: ImageProviderPriority = ImageProviderPriority.STOCK_FIRST
    enable_dalle: bool = True
    enable_pexels: bool = True
    enable_unsplash: bool = True
    dalle_quality: str = "standard"  # standard or hd
    dalle_size: str = "1792x1024"    # landscape for ads
    min_image_width: int = 1080
    images_per_variant: int = 1


class MultiSourceImageProvider:
    """
    Resilient image provider with multiple sources and fallback.

    Supports:
    - Azure OpenAI DALL-E 3 (AI-generated custom images)
    - Pexels (free curated stock)
    - Unsplash (free community stock)

    Falls back automatically if a source fails or is unavailable.
    """

    UNSPLASH_API_URL = "https://api.unsplash.com"

    def __init__(self, config: Optional[ImageProviderConfig] = None):
        """
        Initialize multi-source provider.

        Args:
            config: Provider configuration
        """
        self.config = config or ImageProviderConfig()

        # Initialize clients based on config
        self.dalle_generator = None
        self.pexels_client: Optional[PexelsClient] = None
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")

        # Lazy-load DALL-E to avoid import errors if openai not installed
        if self.config.enable_dalle:
            try:
                from ..generators.azure_dalle_generator import get_dalle_generator
                self.dalle_generator = get_dalle_generator()
                if self.dalle_generator.is_available:
                    logger.info("DALL-E generator available (Azure/OpenAI)")
            except Exception as e:
                logger.warning(f"DALL-E unavailable: {e}")

        if self.config.enable_pexels:
            self.pexels_client = get_pexels_client()
            if self.pexels_client.is_available:
                logger.info("Pexels API available")

        if self.config.enable_unsplash and self.unsplash_key:
            logger.info("Unsplash API available")

        self.http_client = httpx.Client(timeout=30.0)

    @property
    def available_sources(self) -> list[str]:
        """List available image sources."""
        sources = []
        if self.dalle_generator and self.dalle_generator.is_available:
            sources.append("dalle")
        if self.pexels_client and self.pexels_client.is_available:
            sources.append("pexels")
        if self.unsplash_key:
            sources.append("unsplash")
        return sources

    def get_images_for_variant(
        self,
        copy_variant: CopyVariant,
        count: int = 1,
    ) -> ImageMatchResult:
        """
        Get images for a copy variant using configured fallback chain.

        Args:
            copy_variant: The ad copy variant
            count: Number of images to return

        Returns:
            ImageMatchResult with matched images
        """
        start_time = time.time()
        warnings = []
        matches = []

        # Determine source order based on priority
        if self.config.priority == ImageProviderPriority.DALLE_FIRST:
            source_order = ["dalle", "pexels", "unsplash"]
        elif self.config.priority == ImageProviderPriority.DALLE_ONLY:
            source_order = ["dalle"]
        elif self.config.priority == ImageProviderPriority.STOCK_ONLY:
            source_order = ["pexels", "unsplash"]
        else:  # STOCK_FIRST (default)
            source_order = ["pexels", "unsplash", "dalle"]

        # Try each source until we have enough images
        for source in source_order:
            if len(matches) >= count:
                break

            remaining = count - len(matches)

            try:
                if source == "dalle" and self.dalle_generator and self.dalle_generator.is_available:
                    logger.info(f"Trying DALL-E for variant {copy_variant.id}")
                    dalle_matches = self._get_dalle_images(copy_variant, remaining)
                    matches.extend(dalle_matches)

                elif source == "pexels" and self.pexels_client and self.pexels_client.is_available:
                    logger.info(f"Trying Pexels for variant {copy_variant.id}")
                    pexels_matches = self._get_pexels_images(copy_variant, remaining)
                    matches.extend(pexels_matches)

                elif source == "unsplash" and self.unsplash_key:
                    logger.info(f"Trying Unsplash for variant {copy_variant.id}")
                    unsplash_matches = self._get_unsplash_images(copy_variant, remaining)
                    matches.extend(unsplash_matches)

            except Exception as e:
                warning = f"{source} failed: {e}"
                logger.warning(warning)
                warnings.append(warning)

        if not matches:
            warnings.append("No images found from any source")

        return ImageMatchResult(
            copy_variant_id=copy_variant.id,
            matches=matches[:count],
            search_terms_used=self._generate_search_terms(copy_variant),
            total_candidates=len(matches),
            match_time_seconds=time.time() - start_time,
            warnings=warnings,
        )

    def _get_dalle_images(
        self,
        copy_variant: CopyVariant,
        count: int,
    ) -> list[ImageMatch]:
        """Generate images using DALL-E."""
        if not self.dalle_generator:
            return []

        matches = []

        for _ in range(count):
            try:
                result = self.dalle_generator.generate_for_ad(
                    headline=copy_variant.headline,
                    primary_text=copy_variant.primary_text,
                    persona=copy_variant.persona,
                    emotion=copy_variant.emotion.value,
                )

                # Determine dimensions from size string
                size_parts = result.size.split("x")
                width = int(size_parts[0]) if len(size_parts) == 2 else 1024
                height = int(size_parts[1]) if len(size_parts) == 2 else 1024

                match = ImageMatch(
                    id=result.id,
                    copy_variant_id=copy_variant.id,
                    image_id=result.id,
                    image_url=result.local_path or result.url,
                    thumb_url=result.local_path or result.url,
                    download_url=result.local_path or result.url,
                    source=ImageSource.AZURE_DALLE if self.dalle_generator.using_azure else ImageSource.OPENAI_DALLE,
                    photographer="AI Generated (DALL-E 3)",
                    photographer_url="https://openai.com/dall-e-3",
                    search_terms=[result.revised_prompt[:100]],
                    mood=ImageMood.PROFESSIONAL,
                    composition=ImageComposition.RULE_OF_THIRDS,
                    text_safe_areas=[TextSafeArea.BOTTOM, TextSafeArea.TOP],
                    dominant_colors=["#2563eb"],
                    match_score=0.95,  # AI-generated is highly relevant
                    width=width,
                    height=height,
                    license="AI Generated - Full commercial rights",
                    attribution_required=False,
                )
                match.calculate_aspect_ratio()
                matches.append(match)

            except Exception as e:
                logger.error(f"DALL-E generation failed: {e}")
                break

        return matches

    def _get_pexels_images(
        self,
        copy_variant: CopyVariant,
        count: int,
    ) -> list[ImageMatch]:
        """Get images from Pexels."""
        if not self.pexels_client:
            return []

        search_terms = self._generate_search_terms(copy_variant)
        all_photos = []

        for term in search_terms[:2]:
            photos = self.pexels_client.search(
                query=term,
                per_page=10,
                orientation="landscape",
            )
            all_photos.extend(photos)

        # Deduplicate and filter
        seen_ids = set()
        unique_photos = []
        for photo in all_photos:
            if photo["id"] not in seen_ids:
                seen_ids.add(photo["id"])
                if photo["width"] >= self.config.min_image_width:
                    unique_photos.append(photo)

        # Convert to ImageMatch
        matches = []
        for photo in unique_photos[:count]:
            formatted = self.pexels_client.format_for_matcher(photo)

            match = ImageMatch(
                id=f"pexels-{formatted['id']}",
                copy_variant_id=copy_variant.id,
                image_id=formatted["id"],
                image_url=formatted["urls"]["regular"],
                thumb_url=formatted["urls"]["thumb"],
                download_url=formatted["urls"]["full"],
                source=ImageSource.PEXELS,
                photographer=formatted["user"]["name"],
                photographer_url=formatted["user"]["links"]["html"],
                search_terms=search_terms,
                mood=ImageMood.PROFESSIONAL,
                composition=ImageComposition.RULE_OF_THIRDS,
                text_safe_areas=[TextSafeArea.BOTTOM, TextSafeArea.TOP],
                dominant_colors=[formatted["color"]],
                match_score=0.8,
                width=formatted["width"],
                height=formatted["height"],
                license="Pexels License (Free for commercial use)",
                attribution_required=False,
            )
            match.calculate_aspect_ratio()
            matches.append(match)

        return matches

    def _get_unsplash_images(
        self,
        copy_variant: CopyVariant,
        count: int,
    ) -> list[ImageMatch]:
        """Get images from Unsplash."""
        if not self.unsplash_key:
            return []

        search_terms = self._generate_search_terms(copy_variant)
        all_photos = []

        for term in search_terms[:2]:
            try:
                response = self.http_client.get(
                    f"{self.UNSPLASH_API_URL}/search/photos",
                    params={
                        "query": term,
                        "per_page": 10,
                        "orientation": "landscape",
                    },
                    headers={"Authorization": f"Client-ID {self.unsplash_key}"},
                )
                response.raise_for_status()
                data = response.json()
                all_photos.extend(data.get("results", []))
            except Exception as e:
                logger.warning(f"Unsplash search failed for '{term}': {e}")

        # Deduplicate and filter
        seen_ids = set()
        unique_photos = []
        for photo in all_photos:
            if photo["id"] not in seen_ids:
                seen_ids.add(photo["id"])
                if photo.get("width", 0) >= self.config.min_image_width:
                    unique_photos.append(photo)

        # Convert to ImageMatch
        matches = []
        for photo in unique_photos[:count]:
            match = ImageMatch(
                id=f"unsplash-{photo['id']}",
                copy_variant_id=copy_variant.id,
                image_id=photo["id"],
                image_url=photo["urls"]["regular"],
                thumb_url=photo["urls"]["thumb"],
                download_url=photo["urls"]["full"],
                source=ImageSource.UNSPLASH,
                photographer=photo["user"]["name"],
                photographer_url=photo["user"]["links"]["html"],
                search_terms=search_terms,
                mood=ImageMood.PROFESSIONAL,
                composition=ImageComposition.RULE_OF_THIRDS,
                text_safe_areas=[TextSafeArea.BOTTOM, TextSafeArea.TOP],
                dominant_colors=[photo.get("color", "#808080")],
                match_score=0.75,
                width=photo["width"],
                height=photo["height"],
                license="Unsplash License",
                attribution_required=False,
            )
            match.calculate_aspect_ratio()
            matches.append(match)

        return matches

    def _generate_search_terms(self, copy_variant: CopyVariant) -> list[str]:
        """Generate search terms for stock photo APIs."""
        terms = []

        # Extract key concepts from headline
        headline_words = copy_variant.headline.lower().split()
        key_words = [w for w in headline_words if len(w) > 4][:3]
        if key_words:
            terms.append(" ".join(key_words))

        # Add persona-based term
        persona_lower = copy_variant.persona.lower()
        if "job" in persona_lower or "career" in persona_lower:
            terms.append("professional job interview")
        elif "business" in persona_lower:
            terms.append("business professional meeting")
        else:
            terms.append("professional person working laptop")

        # Add emotion-based term
        emotion_map = {
            "frustration": "person thinking problem solving",
            "hope": "person success achievement",
            "curiosity": "person learning discovery",
            "confidence": "confident professional business",
            "excitement": "excited person celebrating",
            "relief": "person relaxed content",
        }
        emotion_term = emotion_map.get(copy_variant.emotion.value.lower())
        if emotion_term:
            terms.append(emotion_term)

        # Generic fallback
        terms.append("professional business modern office")

        return terms[:4]

    def close(self):
        """Close HTTP clients."""
        self.http_client.close()
        if self.pexels_client:
            self.pexels_client.close()


# Singleton instance
_provider: Optional[MultiSourceImageProvider] = None


def get_image_provider(config: Optional[ImageProviderConfig] = None) -> MultiSourceImageProvider:
    """Get or create the image provider singleton."""
    global _provider
    if _provider is None or config is not None:
        _provider = MultiSourceImageProvider(config)
    return _provider


def match_images_multi_source(
    copy_variants: list[CopyVariant],
    images_per_variant: int = 1,
    priority: ImageProviderPriority = ImageProviderPriority.STOCK_FIRST,
) -> list[ImageMatchResult]:
    """
    Match images to copy variants using multi-source provider.

    Args:
        copy_variants: List of copy variants
        images_per_variant: Images to find per variant
        priority: Source priority order

    Returns:
        List of ImageMatchResult for each variant
    """
    config = ImageProviderConfig(
        priority=priority,
        images_per_variant=images_per_variant,
    )
    provider = get_image_provider(config)

    results = []
    for variant in copy_variants:
        result = provider.get_images_for_variant(variant, images_per_variant)
        results.append(result)

    return results
