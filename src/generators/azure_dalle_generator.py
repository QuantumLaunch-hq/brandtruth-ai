# src/generators/azure_dalle_generator.py
"""Azure OpenAI DALL-E 3 Image Generator.

Generates custom ad images using Azure OpenAI DALL-E 3.
Supports both Azure OpenAI Service and direct OpenAI API.
"""

import os
import uuid
import time
import httpx
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from openai import AzureOpenAI, OpenAI

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ImageQuality(str, Enum):
    """DALL-E image quality settings."""
    STANDARD = "standard"
    HD = "hd"


class ImageSize(str, Enum):
    """DALL-E supported image sizes."""
    SQUARE = "1024x1024"
    LANDSCAPE = "1792x1024"
    PORTRAIT = "1024x1792"


class ImageStyle(str, Enum):
    """DALL-E image style."""
    VIVID = "vivid"      # Hyper-real, cinematic
    NATURAL = "natural"  # More realistic, subdued


@dataclass
class GeneratedImage:
    """Result of DALL-E image generation."""
    id: str
    url: str
    revised_prompt: str
    size: str
    quality: str
    style: str
    local_path: Optional[str] = None
    generation_time_ms: int = 0


@dataclass
class ImageGenerationResult:
    """Result of batch image generation."""
    images: list[GeneratedImage]
    total_time_ms: int
    prompt_used: str
    errors: list[str]


class AzureDalleGenerator:
    """
    Generate images using Azure OpenAI DALL-E 3.

    Supports:
    - Azure OpenAI Service (uses Azure credits)
    - Direct OpenAI API (fallback)

    Usage:
        generator = AzureDalleGenerator()
        result = await generator.generate(
            prompt="Professional business meeting in modern office",
            size=ImageSize.LANDSCAPE,
            quality=ImageQuality.HD
        )
    """

    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        azure_api_key: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        azure_api_version: str = "2024-02-01",
        openai_api_key: Optional[str] = None,
        prefer_azure: bool = True,
        output_dir: str = "./output/generated_images",
    ):
        """
        Initialize DALL-E generator.

        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            azure_api_key: Azure OpenAI API key
            azure_deployment: DALL-E deployment name in Azure
            azure_api_version: Azure API version
            openai_api_key: Direct OpenAI API key (fallback)
            prefer_azure: Use Azure if available, else fall back to OpenAI
            output_dir: Directory to save generated images
        """
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = azure_api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_deployment = azure_deployment or os.getenv("AZURE_DALLE_DEPLOYMENT", "dall-e-3")
        self.azure_api_version = azure_api_version
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.prefer_azure = prefer_azure
        self.output_dir = output_dir

        # Initialize clients
        self.azure_client: Optional[AzureOpenAI] = None
        self.openai_client: Optional[OpenAI] = None

        if self.azure_endpoint and self.azure_api_key:
            self.azure_client = AzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_api_key,
                api_version=self.azure_api_version,
            )
            logger.info(f"Azure OpenAI DALL-E initialized: {self.azure_endpoint}")

        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("Direct OpenAI DALL-E initialized")

        if not self.azure_client and not self.openai_client:
            logger.warning("No DALL-E API configured - image generation unavailable")

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    @property
    def is_available(self) -> bool:
        """Check if any DALL-E API is available."""
        return self.azure_client is not None or self.openai_client is not None

    @property
    def using_azure(self) -> bool:
        """Check if using Azure (for billing info)."""
        return self.azure_client is not None and self.prefer_azure

    def generate(
        self,
        prompt: str,
        size: ImageSize = ImageSize.SQUARE,
        quality: ImageQuality = ImageQuality.STANDARD,
        style: ImageStyle = ImageStyle.NATURAL,
        save_locally: bool = True,
    ) -> GeneratedImage:
        """
        Generate a single image with DALL-E 3.

        Args:
            prompt: Image generation prompt
            size: Image dimensions
            quality: Standard or HD quality
            style: Vivid or natural style
            save_locally: Download and save image locally

        Returns:
            GeneratedImage with URL and metadata

        Raises:
            RuntimeError: If no DALL-E API is configured
            Exception: On API errors
        """
        if not self.is_available:
            raise RuntimeError("No DALL-E API configured")

        start_time = time.time()

        # Choose client (Azure preferred if available)
        if self.azure_client and self.prefer_azure:
            client = self.azure_client
            model = self.azure_deployment
            source = "azure"
        elif self.openai_client:
            client = self.openai_client
            model = "dall-e-3"
            source = "openai"
        else:
            raise RuntimeError("No DALL-E client available")

        logger.info(f"Generating image with {source} DALL-E 3: {prompt[:50]}...")

        # Generate image
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size.value,
            quality=quality.value,
            style=style.value,
            n=1,  # DALL-E 3 only supports n=1
        )

        image_data = response.data[0]
        image_id = f"dalle-{uuid.uuid4().hex[:8]}"

        result = GeneratedImage(
            id=image_id,
            url=image_data.url,
            revised_prompt=image_data.revised_prompt or prompt,
            size=size.value,
            quality=quality.value,
            style=style.value,
            generation_time_ms=int((time.time() - start_time) * 1000),
        )

        # Download and save locally if requested
        if save_locally and image_data.url:
            local_path = self._download_image(image_data.url, image_id)
            result.local_path = local_path

        logger.info(
            f"Generated image {image_id} in {result.generation_time_ms}ms "
            f"({quality.value}, {size.value})"
        )

        return result

    def generate_for_ad(
        self,
        headline: str,
        primary_text: str,
        persona: str,
        emotion: str,
        brand_name: Optional[str] = None,
        size: ImageSize = ImageSize.LANDSCAPE,
        quality: ImageQuality = ImageQuality.STANDARD,
    ) -> GeneratedImage:
        """
        Generate an image optimized for ad creative.

        Args:
            headline: Ad headline text
            primary_text: Ad body text
            persona: Target audience persona
            emotion: Target emotional response
            brand_name: Brand name for context
            size: Image dimensions
            quality: Image quality

        Returns:
            GeneratedImage optimized for ad use
        """
        # Build optimized prompt for ad imagery
        prompt = self._build_ad_prompt(
            headline=headline,
            primary_text=primary_text,
            persona=persona,
            emotion=emotion,
            brand_name=brand_name,
        )

        return self.generate(
            prompt=prompt,
            size=size,
            quality=quality,
            style=ImageStyle.NATURAL,  # Natural works better for ads
            save_locally=True,
        )

    def generate_batch(
        self,
        prompts: list[str],
        size: ImageSize = ImageSize.SQUARE,
        quality: ImageQuality = ImageQuality.STANDARD,
    ) -> ImageGenerationResult:
        """
        Generate multiple images (sequentially - DALL-E 3 doesn't support batch).

        Args:
            prompts: List of prompts
            size: Image dimensions for all
            quality: Quality for all

        Returns:
            ImageGenerationResult with all images
        """
        start_time = time.time()
        images = []
        errors = []

        for i, prompt in enumerate(prompts):
            try:
                logger.info(f"Generating image {i+1}/{len(prompts)}")
                image = self.generate(
                    prompt=prompt,
                    size=size,
                    quality=quality,
                )
                images.append(image)
            except Exception as e:
                error_msg = f"Failed to generate image {i+1}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        return ImageGenerationResult(
            images=images,
            total_time_ms=int((time.time() - start_time) * 1000),
            prompt_used=prompts[0] if prompts else "",
            errors=errors,
        )

    def _build_ad_prompt(
        self,
        headline: str,
        primary_text: str,
        persona: str,
        emotion: str,
        brand_name: Optional[str] = None,
    ) -> str:
        """Build an optimized prompt for ad imagery."""

        # Map emotions to visual descriptions
        emotion_visuals = {
            "frustration": "person looking thoughtful or concerned, soft lighting",
            "hope": "person looking optimistic and forward, bright natural lighting",
            "curiosity": "person engaged and interested, warm lighting",
            "confidence": "person standing tall and assured, professional lighting",
            "excitement": "person energized and motivated, dynamic lighting",
            "relief": "person relaxed and content, soft warm lighting",
        }

        visual_mood = emotion_visuals.get(emotion.lower(), "professional person in modern setting")

        prompt = f"""Professional advertising photograph for a digital ad campaign.

Scene: {visual_mood}
Target audience: {persona}
Theme inspired by: {headline}

Requirements:
- High-quality commercial photography style
- Clean composition with space for text overlay (bottom or side)
- Professional, authentic look (not stock photo clichés)
- No text, logos, or watermarks in the image
- Suitable for business/professional context
- Photorealistic, not illustrated or cartoon
- Well-lit with natural or studio lighting
- Modern, contemporary setting"""

        if brand_name:
            prompt += f"\n- Visual style appropriate for {brand_name} brand"

        return prompt

    def _download_image(self, url: str, image_id: str) -> str:
        """Download image from URL and save locally."""

        local_path = os.path.join(self.output_dir, f"{image_id}.png")

        with httpx.Client(timeout=60.0) as client:
            response = client.get(url)
            response.raise_for_status()

            with open(local_path, "wb") as f:
                f.write(response.content)

        logger.info(f"Saved image to {local_path}")
        return local_path

    def estimate_cost(
        self,
        count: int,
        size: ImageSize = ImageSize.SQUARE,
        quality: ImageQuality = ImageQuality.STANDARD,
    ) -> dict:
        """
        Estimate cost for generating images.

        Returns:
            Dict with cost estimates for Azure and OpenAI
        """
        # Azure/OpenAI DALL-E 3 pricing (Dec 2025)
        pricing = {
            (ImageSize.SQUARE, ImageQuality.STANDARD): 0.04,
            (ImageSize.SQUARE, ImageQuality.HD): 0.08,
            (ImageSize.LANDSCAPE, ImageQuality.STANDARD): 0.08,
            (ImageSize.LANDSCAPE, ImageQuality.HD): 0.12,
            (ImageSize.PORTRAIT, ImageQuality.STANDARD): 0.08,
            (ImageSize.PORTRAIT, ImageQuality.HD): 0.12,
        }

        price_per_image = pricing.get((size, quality), 0.04)
        total_cost = count * price_per_image

        return {
            "count": count,
            "size": size.value,
            "quality": quality.value,
            "price_per_image": price_per_image,
            "total_estimated_cost": total_cost,
            "currency": "USD",
            "note": "Uses Azure credits if Azure OpenAI is configured",
        }


# Singleton instance
_generator: Optional[AzureDalleGenerator] = None


def get_dalle_generator() -> AzureDalleGenerator:
    """Get or create the DALL-E generator singleton."""
    global _generator
    if _generator is None:
        _generator = AzureDalleGenerator()
    return _generator


# Convenience functions
def generate_ad_image(
    headline: str,
    primary_text: str,
    persona: str,
    emotion: str,
    brand_name: Optional[str] = None,
) -> GeneratedImage:
    """Generate an ad image using DALL-E."""
    generator = get_dalle_generator()
    return generator.generate_for_ad(
        headline=headline,
        primary_text=primary_text,
        persona=persona,
        emotion=emotion,
        brand_name=brand_name,
    )


def is_dalle_available() -> bool:
    """Check if DALL-E generation is available."""
    generator = get_dalle_generator()
    return generator.is_available
