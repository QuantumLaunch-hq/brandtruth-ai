# src/composers/ad_composer.py
"""Ad composition - combining images and copy into final creatives.

This is Slice 4. It takes copy variants + matched images and renders
final ad creatives in multiple formats.
"""

import os
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ..models.copy_variant import CopyVariant
from ..models.image_match import ImageMatch
from ..models.composed_ad import (
    ComposedAd,
    CompositionRequest,
    CompositionResult,
    BatchCompositionResult,
    AdFormat,
    FORMAT_SPECS,
    CompositionStyle,
    TextPosition,
    RenderedAsset,
)


class AdComposer:
    """
    Compose final ad creatives from copy and images.
    
    This handles image downloading, resizing, overlay application,
    and text rendering to produce platform-ready ad assets.
    """
    
    # Font settings
    DEFAULT_FONT_SIZE_HEADLINE = 48
    DEFAULT_FONT_SIZE_BODY = 28
    DEFAULT_FONT_SIZE_CTA = 24
    
    # Padding
    PADDING = 40
    
    def __init__(
        self,
        output_dir: str = "./output",
        font_path: Optional[str] = None,
    ):
        """
        Initialize the ad composer.
        
        Args:
            output_dir: Directory to save rendered ads
            font_path: Path to custom font (optional)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.font_path = font_path
        self.http_client = httpx.Client(timeout=60.0)
        
        # Try to load fonts
        self._load_fonts()
    
    def _load_fonts(self):
        """Load fonts for text rendering."""
        # Try to find a good system font
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/System/Library/Fonts/SFNSDisplay.ttf",  # macOS SF
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        
        self.font_bold = None
        self.font_regular = None
        
        if self.font_path and Path(self.font_path).exists():
            try:
                self.font_bold = ImageFont.truetype(self.font_path, self.DEFAULT_FONT_SIZE_HEADLINE)
                self.font_regular = ImageFont.truetype(self.font_path, self.DEFAULT_FONT_SIZE_BODY)
                return
            except Exception:
                pass
        
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    self.font_bold = ImageFont.truetype(font_path, self.DEFAULT_FONT_SIZE_HEADLINE)
                    self.font_regular = ImageFont.truetype(font_path, self.DEFAULT_FONT_SIZE_BODY)
                    return
                except Exception:
                    continue
        
        # Fallback to default
        self.font_bold = ImageFont.load_default()
        self.font_regular = ImageFont.load_default()
    
    def compose_single(
        self,
        copy_variant: CopyVariant,
        image_match: ImageMatch,
        formats: list[AdFormat] = None,
        style: CompositionStyle = CompositionStyle.DARK_OVERLAY,
        text_position: TextPosition = TextPosition.BOTTOM,
        logo_path: Optional[str] = None,
        brand_color: str = "#FFFFFF",
        accent_color: str = "#007AFF",
    ) -> CompositionResult:
        """
        Compose a single ad from copy variant and image match.
        
        Args:
            copy_variant: The copy to use
            image_match: The matched image
            formats: Which formats to render
            style: Composition style
            text_position: Where to place text
            logo_path: Optional logo file path
            brand_color: Primary text color
            accent_color: CTA button color
            
        Returns:
            CompositionResult with rendered ad
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        if formats is None:
            formats = [AdFormat.SQUARE, AdFormat.PORTRAIT, AdFormat.STORY]
        
        ad_id = f"ad-{uuid.uuid4().hex[:8]}"
        
        # Download source image
        try:
            source_image = self._download_image(image_match.image_url)
        except Exception as e:
            errors.append(f"Failed to download image: {e}")
            return CompositionResult(
                ad=None,
                success=False,
                errors=errors,
            )
        
        # Render each format
        assets = {}
        for format in formats:
            try:
                spec = FORMAT_SPECS[format]
                
                # Create the composed image
                composed = self._compose_format(
                    source_image=source_image,
                    width=spec.width,
                    height=spec.height,
                    headline=copy_variant.headline,
                    primary_text=copy_variant.primary_text,
                    cta=copy_variant.cta,
                    style=style,
                    text_position=text_position,
                    brand_color=brand_color,
                    accent_color=accent_color,
                    logo_path=logo_path,
                )
                
                # Save to file
                file_name = f"{ad_id}_{format.value.replace(':', 'x')}.png"
                file_path = self.output_dir / file_name
                composed.save(file_path, "PNG", quality=95)
                
                file_size = file_path.stat().st_size
                
                assets[format.value] = RenderedAsset(
                    format=format,
                    width=spec.width,
                    height=spec.height,
                    file_path=str(file_path),
                    file_size_bytes=file_size,
                )
                
            except Exception as e:
                errors.append(f"Failed to render {format.value}: {e}")
        
        if not assets:
            return CompositionResult(
                ad=None,
                success=False,
                errors=errors,
            )
        
        # Create the composed ad object
        composed_ad = ComposedAd(
            id=ad_id,
            copy_variant_id=copy_variant.id,
            image_match_id=image_match.id,
            headline=copy_variant.headline,
            primary_text=copy_variant.primary_text,
            cta=copy_variant.cta,
            source_image_url=image_match.image_url,
            photographer=image_match.photographer,
            photographer_attribution=image_match.get_attribution(),
            style=style,
            text_position=text_position,
            brand_color=brand_color,
            accent_color=accent_color,
            logo_path=logo_path,
            assets=assets,
            composition_time_seconds=time.time() - start_time,
        )
        
        return CompositionResult(
            ad=composed_ad,
            success=True,
            errors=errors,
            warnings=warnings,
        )
    
    def compose_batch(
        self,
        copy_variants: list[CopyVariant],
        image_matches: dict[str, ImageMatch],  # keyed by copy_variant_id
        formats: list[AdFormat] = None,
        **kwargs,
    ) -> BatchCompositionResult:
        """
        Compose multiple ads.
        
        Args:
            copy_variants: List of copy variants
            image_matches: Dict mapping copy_variant_id to best ImageMatch
            formats: Which formats to render
            **kwargs: Additional composition options
            
        Returns:
            BatchCompositionResult with all composed ads
        """
        start_time = time.time()
        ads = []
        all_errors = []
        
        for i, variant in enumerate(copy_variants):
            print(f"Composing ad {i+1}/{len(copy_variants)}...")
            
            # Get the matching image
            image_match = image_matches.get(variant.id)
            if not image_match:
                all_errors.append(f"No image match for variant {variant.id}")
                continue
            
            result = self.compose_single(
                copy_variant=variant,
                image_match=image_match,
                formats=formats,
                **kwargs,
            )
            
            if result.success and result.ad:
                ads.append(result.ad)
            else:
                all_errors.extend(result.errors)
        
        total_assets = sum(len(ad.assets) for ad in ads)
        
        return BatchCompositionResult(
            ads=ads,
            total_requested=len(copy_variants),
            total_composed=len(ads),
            total_assets=total_assets,
            total_time_seconds=time.time() - start_time,
            errors=all_errors,
        )
    
    def _download_image(self, url: str) -> Image.Image:
        """Download an image from URL."""
        response = self.http_client.get(url)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    
    def _compose_format(
        self,
        source_image: Image.Image,
        width: int,
        height: int,
        headline: str,
        primary_text: str,
        cta: str,
        style: CompositionStyle,
        text_position: TextPosition,
        brand_color: str,
        accent_color: str,
        logo_path: Optional[str] = None,
    ) -> Image.Image:
        """Compose a single format."""
        
        # Resize and crop to fit
        img = self._resize_and_crop(source_image, width, height)
        
        # Convert to RGBA for transparency
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        
        # Detect image brightness in text area to determine text color
        is_light_background = self._detect_brightness(img, text_position)
        
        # Choose text color based on background
        if is_light_background:
            # Dark text on light background
            effective_text_color = "#1a1a1a"
            overlay_style = CompositionStyle.LIGHT_OVERLAY
        else:
            # White text on dark background
            effective_text_color = brand_color if brand_color != "#FFFFFF" else "#FFFFFF"
            overlay_style = style
        
        # Apply overlay based on style
        if overlay_style == CompositionStyle.DARK_OVERLAY:
            img = self._apply_dark_overlay(img, text_position)
        elif overlay_style == CompositionStyle.LIGHT_OVERLAY:
            img = self._apply_light_overlay(img, text_position)
        
        # Add text
        img = self._add_text(
            img=img,
            headline=headline,
            primary_text=primary_text,
            cta=cta,
            text_position=text_position,
            brand_color=effective_text_color,
            accent_color=accent_color,
        )
        
        # Add logo if provided
        if logo_path and Path(logo_path).exists():
            img = self._add_logo(img, logo_path)
        
        # Convert back to RGB for PNG
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (0, 0, 0))
            background.paste(img, mask=img.split()[3])
            img = background
        
        return img
    
    def _detect_brightness(self, img: Image.Image, text_position: TextPosition) -> bool:
        """
        Detect if the text area of the image is light or dark.
        
        Returns True if the background is light (needs dark text).
        """
        width, height = img.size
        
        # Define the region where text will be placed
        if text_position == TextPosition.BOTTOM:
            # Bottom third of image
            crop_box = (0, int(height * 0.6), width, height)
        elif text_position == TextPosition.TOP:
            # Top third of image
            crop_box = (0, 0, width, int(height * 0.4))
        else:  # CENTER
            # Middle third
            crop_box = (0, int(height * 0.33), width, int(height * 0.67))
        
        # Crop to text region
        region = img.crop(crop_box)
        
        # Convert to grayscale and calculate average brightness
        grayscale = region.convert("L")
        
        # Get histogram and calculate weighted average
        histogram = grayscale.histogram()
        pixels = sum(histogram)
        brightness = sum(i * histogram[i] for i in range(256)) / pixels if pixels > 0 else 128
        
        # Threshold: values above 160 are considered "light"
        # (0-255 scale, 128 is middle gray)
        return brightness > 160
    
    def _resize_and_crop(
        self,
        img: Image.Image,
        target_width: int,
        target_height: int,
    ) -> Image.Image:
        """Resize and crop image to target dimensions."""
        
        # Calculate aspect ratios
        target_ratio = target_width / target_height
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            # Image is wider - crop width
            new_height = target_height
            new_width = int(target_height * img_ratio)
        else:
            # Image is taller - crop height
            new_width = target_width
            new_height = int(target_width / img_ratio)
        
        # Resize
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return img.crop((left, top, right, bottom))
    
    def _apply_dark_overlay(
        self,
        img: Image.Image,
        text_position: TextPosition,
    ) -> Image.Image:
        """Apply a dark gradient overlay for text readability."""
        
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        width, height = img.size
        
        if text_position == TextPosition.BOTTOM:
            # Gradient from bottom
            for y in range(height // 2, height):
                alpha = int(180 * (y - height // 2) / (height // 2))
                draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        elif text_position == TextPosition.TOP:
            # Gradient from top
            for y in range(height // 2):
                alpha = int(180 * (1 - y / (height // 2)))
                draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
        else:  # CENTER
            # Full overlay
            draw.rectangle([0, 0, width, height], fill=(0, 0, 0, 120))
        
        return Image.alpha_composite(img, overlay)
    
    def _apply_light_overlay(
        self,
        img: Image.Image,
        text_position: TextPosition,
    ) -> Image.Image:
        """Apply a light gradient overlay."""
        
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        width, height = img.size
        
        # Full light overlay
        draw.rectangle([0, 0, width, height], fill=(255, 255, 255, 180))
        
        return Image.alpha_composite(img, overlay)
    
    def _add_text(
        self,
        img: Image.Image,
        headline: str,
        primary_text: str,
        cta: str,
        text_position: TextPosition,
        brand_color: str,
        accent_color: str,
    ) -> Image.Image:
        """Add text elements to the image."""
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Calculate font sizes based on image size
        scale = min(width, height) / 1080
        headline_size = int(self.DEFAULT_FONT_SIZE_HEADLINE * scale)
        body_size = int(self.DEFAULT_FONT_SIZE_BODY * scale)
        cta_size = int(self.DEFAULT_FONT_SIZE_CTA * scale)
        padding = int(self.PADDING * scale)
        
        # Load fonts at appropriate sizes
        try:
            font_headline = ImageFont.truetype(
                self.font_path or "/System/Library/Fonts/Helvetica.ttc",
                headline_size
            )
            font_body = ImageFont.truetype(
                self.font_path or "/System/Library/Fonts/Helvetica.ttc",
                body_size
            )
            font_cta = ImageFont.truetype(
                self.font_path or "/System/Library/Fonts/Helvetica.ttc",
                cta_size
            )
        except Exception:
            font_headline = self.font_bold
            font_body = self.font_regular
            font_cta = self.font_regular
        
        # Parse colors
        text_color = brand_color if brand_color.startswith("#") else f"#{brand_color}"
        button_color = accent_color if accent_color.startswith("#") else f"#{accent_color}"
        
        # Word wrap headline
        headline_wrapped = self._wrap_text(headline, font_headline, width - padding * 2)
        primary_wrapped = self._wrap_text(primary_text, font_body, width - padding * 2)
        
        # Calculate text heights
        headline_bbox = draw.multiline_textbbox((0, 0), headline_wrapped, font=font_headline)
        headline_height = headline_bbox[3] - headline_bbox[1]
        
        primary_bbox = draw.multiline_textbbox((0, 0), primary_wrapped, font=font_body)
        primary_height = primary_bbox[3] - primary_bbox[1]
        
        cta_bbox = draw.textbbox((0, 0), cta, font=font_cta)
        cta_height = cta_bbox[3] - cta_bbox[1]
        cta_width = cta_bbox[2] - cta_bbox[0]
        
        # Calculate Y positions based on text_position
        spacing = int(15 * scale)
        total_text_height = headline_height + spacing + primary_height + spacing + cta_height + padding
        
        if text_position == TextPosition.BOTTOM:
            start_y = height - total_text_height - padding
        elif text_position == TextPosition.TOP:
            start_y = padding
        else:  # CENTER
            start_y = (height - total_text_height) // 2
        
        current_y = start_y
        
        # Draw headline
        draw.multiline_text(
            (padding, current_y),
            headline_wrapped,
            font=font_headline,
            fill=text_color,
        )
        current_y += headline_height + spacing
        
        # Draw primary text
        draw.multiline_text(
            (padding, current_y),
            primary_wrapped,
            font=font_body,
            fill=text_color,
        )
        current_y += primary_height + spacing
        
        # Draw CTA button
        button_padding_x = int(20 * scale)
        button_padding_y = int(10 * scale)
        button_x = padding
        button_y = current_y
        
        # Button background
        draw.rounded_rectangle(
            [
                button_x,
                button_y,
                button_x + cta_width + button_padding_x * 2,
                button_y + cta_height + button_padding_y * 2,
            ],
            radius=int(8 * scale),
            fill=button_color,
        )
        
        # Button text
        draw.text(
            (button_x + button_padding_x, button_y + button_padding_y),
            cta,
            font=font_cta,
            fill="#FFFFFF",
        )
        
        return img
    
    def _wrap_text(self, text: str, font, max_width: int) -> str:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        # Create a temporary image for measuring
        temp_img = Image.new("RGB", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    def _add_logo(self, img: Image.Image, logo_path: str) -> Image.Image:
        """Add logo to the image."""
        try:
            logo = Image.open(logo_path)
            
            # Resize logo to reasonable size
            max_logo_size = img.width // 6
            logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)
            
            # Position in top-right corner
            x = img.width - logo.width - self.PADDING
            y = self.PADDING
            
            # Handle transparency
            if logo.mode == "RGBA":
                img.paste(logo, (x, y), logo)
            else:
                img.paste(logo, (x, y))
            
        except Exception as e:
            print(f"Warning: Failed to add logo: {e}")
        
        return img
    
    def close(self):
        """Close HTTP client."""
        self.http_client.close()


# Convenience function
def compose_ads(
    copy_variants: list[CopyVariant],
    image_matches: dict[str, ImageMatch],
    output_dir: str = "./output",
    formats: list[AdFormat] = None,
    **kwargs,
) -> BatchCompositionResult:
    """
    Compose ads from copy variants and image matches.
    
    Args:
        copy_variants: List of copy variants
        image_matches: Dict mapping copy_variant_id to ImageMatch
        output_dir: Where to save rendered ads
        formats: Which formats to render
        **kwargs: Additional composition options
        
    Returns:
        BatchCompositionResult with all composed ads
    """
    composer = AdComposer(output_dir=output_dir)
    try:
        return composer.compose_batch(
            copy_variants=copy_variants,
            image_matches=image_matches,
            formats=formats,
            **kwargs,
        )
    finally:
        composer.close()
