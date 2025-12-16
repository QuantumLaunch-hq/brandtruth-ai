# src/composers/format_exporter.py
"""Multi-Format Exporter for BrandTruth AI - Slice 11

One-click generation of all ad formats from a single creative.

Supported Formats:
- Square (1:1) - 1080x1080 - Meta Feed, Instagram Feed
- Portrait (4:5) - 1080x1350 - Meta/Instagram Feed
- Landscape (1.91:1) - 1200x628 - Meta Feed, Link Ads
- Story (9:16) - 1080x1920 - Instagram/Facebook Stories
- Pin (2:3) - 1000x1500 - Pinterest
- Twitter (16:9) - 1200x675 - Twitter/X
- LinkedIn (1.91:1) - 1200x627 - LinkedIn Feed
- YouTube Thumb (16:9) - 1280x720 - YouTube Thumbnails
- Banner (3:1) - 1200x400 - Email, Web banners

Features:
- Batch export all formats at once
- Smart text repositioning per format
- Maintains visual hierarchy
- ZIP download option
- Platform-specific optimization
"""

import asyncio
import os
import zipfile
from datetime import datetime
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# FORMAT DEFINITIONS
# =============================================================================

class ExportFormat(str, Enum):
    """Available export formats."""
    SQUARE = "square"           # 1:1 - 1080x1080
    PORTRAIT = "portrait"       # 4:5 - 1080x1350
    LANDSCAPE = "landscape"     # 1.91:1 - 1200x628
    STORY = "story"             # 9:16 - 1080x1920
    PIN = "pin"                 # 2:3 - 1000x1500
    TWITTER = "twitter"         # 16:9 - 1200x675
    LINKEDIN = "linkedin"       # 1.91:1 - 1200x627
    YOUTUBE_THUMB = "youtube"   # 16:9 - 1280x720
    BANNER = "banner"           # 3:1 - 1200x400


class FormatSpec(BaseModel):
    """Specification for an export format."""
    name: str
    width: int
    height: int
    aspect_ratio: str
    platforms: list[str]
    text_safe_area: tuple[float, float, float, float]  # top, right, bottom, left as %
    headline_position: str  # top, center, bottom
    cta_position: str  # top, center, bottom
    max_headline_width: float  # % of width
    font_scale: float = 1.0


FORMAT_SPECS: dict[ExportFormat, FormatSpec] = {
    ExportFormat.SQUARE: FormatSpec(
        name="Square",
        width=1080,
        height=1080,
        aspect_ratio="1:1",
        platforms=["Meta Feed", "Instagram Feed"],
        text_safe_area=(0.1, 0.1, 0.15, 0.1),
        headline_position="top",
        cta_position="bottom",
        max_headline_width=0.9,
    ),
    ExportFormat.PORTRAIT: FormatSpec(
        name="Portrait",
        width=1080,
        height=1350,
        aspect_ratio="4:5",
        platforms=["Meta Feed", "Instagram Feed"],
        text_safe_area=(0.08, 0.1, 0.12, 0.1),
        headline_position="top",
        cta_position="bottom",
        max_headline_width=0.9,
    ),
    ExportFormat.LANDSCAPE: FormatSpec(
        name="Landscape",
        width=1200,
        height=628,
        aspect_ratio="1.91:1",
        platforms=["Meta Feed", "Link Ads"],
        text_safe_area=(0.1, 0.1, 0.15, 0.1),
        headline_position="center",
        cta_position="bottom",
        max_headline_width=0.7,
        font_scale=0.9,
    ),
    ExportFormat.STORY: FormatSpec(
        name="Story",
        width=1080,
        height=1920,
        aspect_ratio="9:16",
        platforms=["Instagram Stories", "Facebook Stories", "TikTok"],
        text_safe_area=(0.15, 0.1, 0.2, 0.1),
        headline_position="center",
        cta_position="bottom",
        max_headline_width=0.85,
        font_scale=1.1,
    ),
    ExportFormat.PIN: FormatSpec(
        name="Pinterest Pin",
        width=1000,
        height=1500,
        aspect_ratio="2:3",
        platforms=["Pinterest"],
        text_safe_area=(0.1, 0.1, 0.15, 0.1),
        headline_position="top",
        cta_position="bottom",
        max_headline_width=0.85,
    ),
    ExportFormat.TWITTER: FormatSpec(
        name="Twitter/X",
        width=1200,
        height=675,
        aspect_ratio="16:9",
        platforms=["Twitter/X"],
        text_safe_area=(0.1, 0.1, 0.15, 0.1),
        headline_position="center",
        cta_position="bottom",
        max_headline_width=0.75,
        font_scale=0.9,
    ),
    ExportFormat.LINKEDIN: FormatSpec(
        name="LinkedIn",
        width=1200,
        height=627,
        aspect_ratio="1.91:1",
        platforms=["LinkedIn Feed"],
        text_safe_area=(0.1, 0.1, 0.15, 0.1),
        headline_position="center",
        cta_position="bottom",
        max_headline_width=0.7,
        font_scale=0.85,
    ),
    ExportFormat.YOUTUBE_THUMB: FormatSpec(
        name="YouTube Thumbnail",
        width=1280,
        height=720,
        aspect_ratio="16:9",
        platforms=["YouTube"],
        text_safe_area=(0.1, 0.15, 0.1, 0.15),
        headline_position="center",
        cta_position="bottom",
        max_headline_width=0.7,
        font_scale=1.0,
    ),
    ExportFormat.BANNER: FormatSpec(
        name="Banner",
        width=1200,
        height=400,
        aspect_ratio="3:1",
        platforms=["Email", "Web Banners"],
        text_safe_area=(0.1, 0.2, 0.1, 0.2),
        headline_position="center",
        cta_position="center",
        max_headline_width=0.6,
        font_scale=0.8,
    ),
}


# =============================================================================
# DATA MODELS
# =============================================================================

class ExportedFormat(BaseModel):
    """A single exported format."""
    format: ExportFormat
    spec: FormatSpec
    file_path: str
    file_size_kb: int
    dimensions: tuple[int, int]


class ExportResult(BaseModel):
    """Result of a multi-format export."""
    success: bool
    source_image: Optional[str] = None
    headline: str
    cta: str
    formats_exported: list[ExportedFormat]
    zip_path: Optional[str] = None
    total_size_kb: int = 0
    export_time_ms: int = 0
    errors: list[str] = Field(default_factory=list)


class ExportConfig(BaseModel):
    """Configuration for export."""
    formats: list[ExportFormat] = Field(default_factory=lambda: list(ExportFormat))
    output_dir: str = "./output"
    create_zip: bool = True
    add_watermark: bool = False
    watermark_text: str = "BrandTruth"
    overlay_opacity: float = 0.4
    headline_color: str = "#FFFFFF"
    cta_color: str = "#FFFFFF"
    cta_bg_color: str = "#3B82F6"


# =============================================================================
# FORMAT EXPORTER
# =============================================================================

class FormatExporter:
    """Exports ads to multiple formats."""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get or create a font of the specified size."""
        if size not in self._font_cache:
            try:
                # Try to load a nice font
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/SFNSDisplay.ttf",
                    "C:\\Windows\\Fonts\\arial.ttf",
                ]
                for path in font_paths:
                    if os.path.exists(path):
                        self._font_cache[size] = ImageFont.truetype(path, size)
                        break
                else:
                    self._font_cache[size] = ImageFont.load_default()
            except Exception:
                self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]
    
    async def export_all(
        self,
        source_image_path: Optional[str] = None,
        source_image_url: Optional[str] = None,
        headline: str = "",
        primary_text: str = "",
        cta: str = "Learn More",
        brand_name: Optional[str] = None,
    ) -> ExportResult:
        """
        Export to all configured formats.
        
        Args:
            source_image_path: Local path to source image
            source_image_url: URL of source image
            headline: Ad headline
            primary_text: Ad body text
            cta: Call to action text
            brand_name: Brand name for watermark
        
        Returns:
            ExportResult with all exported formats
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting multi-format export for: {headline[:30]}...")
        
        # Load source image
        source_image = await self._load_image(source_image_path, source_image_url)
        if not source_image:
            return ExportResult(
                success=False,
                headline=headline,
                cta=cta,
                formats_exported=[],
                errors=["Failed to load source image"],
            )
        
        # Create output directory
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_formats: list[ExportedFormat] = []
        errors: list[str] = []
        
        # Export each format
        for fmt in self.config.formats:
            try:
                spec = FORMAT_SPECS[fmt]
                
                # Create the formatted image
                formatted_image = self._create_format(
                    source_image=source_image,
                    spec=spec,
                    headline=headline,
                    primary_text=primary_text,
                    cta=cta,
                    brand_name=brand_name,
                )
                
                # Save the image
                filename = f"ad_{timestamp}_{fmt.value}.png"
                file_path = output_dir / filename
                formatted_image.save(file_path, "PNG", optimize=True)
                
                file_size = file_path.stat().st_size // 1024
                
                exported_formats.append(ExportedFormat(
                    format=fmt,
                    spec=spec,
                    file_path=str(file_path),
                    file_size_kb=file_size,
                    dimensions=(spec.width, spec.height),
                ))
                
                logger.info(f"  ✓ {spec.name} ({spec.width}x{spec.height})")
                
            except Exception as e:
                error_msg = f"Failed to export {fmt.value}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Create ZIP if requested
        zip_path = None
        if self.config.create_zip and exported_formats:
            zip_filename = f"ad_export_{timestamp}.zip"
            zip_path = str(output_dir / zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for exp in exported_formats:
                    zf.write(exp.file_path, os.path.basename(exp.file_path))
            
            logger.info(f"  📦 Created ZIP: {zip_filename}")
        
        # Calculate total size
        total_size = sum(e.file_size_kb for e in exported_formats)
        export_time = int((time.time() - start_time) * 1000)
        
        return ExportResult(
            success=len(exported_formats) > 0,
            source_image=source_image_path or source_image_url,
            headline=headline,
            cta=cta,
            formats_exported=exported_formats,
            zip_path=zip_path,
            total_size_kb=total_size,
            export_time_ms=export_time,
            errors=errors,
        )
    
    async def _load_image(
        self,
        image_path: Optional[str],
        image_url: Optional[str],
    ) -> Optional[Image.Image]:
        """Load image from path or URL."""
        try:
            if image_path:
                return Image.open(image_path).convert("RGBA")
            
            if image_url:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    return Image.open(BytesIO(response.content)).convert("RGBA")
            
            return None
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None
    
    def _create_format(
        self,
        source_image: Image.Image,
        spec: FormatSpec,
        headline: str,
        primary_text: str,
        cta: str,
        brand_name: Optional[str],
    ) -> Image.Image:
        """Create a single format from the source image."""
        # Create canvas
        canvas = Image.new("RGBA", (spec.width, spec.height), (0, 0, 0, 255))
        
        # Resize and crop source image to fill canvas
        bg_image = self._smart_crop(source_image, spec.width, spec.height)
        
        # Apply slight darkening for text readability
        overlay = Image.new("RGBA", (spec.width, spec.height), (0, 0, 0, int(255 * self.config.overlay_opacity)))
        canvas.paste(bg_image, (0, 0))
        canvas = Image.alpha_composite(canvas, overlay)
        
        # Draw text elements
        draw = ImageDraw.Draw(canvas)
        
        # Calculate safe area
        safe_top = int(spec.height * spec.text_safe_area[0])
        safe_right = int(spec.width * (1 - spec.text_safe_area[1]))
        safe_bottom = int(spec.height * (1 - spec.text_safe_area[2]))
        safe_left = int(spec.width * spec.text_safe_area[3])
        
        # Draw headline
        if headline:
            headline_font_size = int(48 * spec.font_scale)
            headline_font = self._get_font(headline_font_size)
            
            max_width = int(spec.width * spec.max_headline_width)
            wrapped_headline = self._wrap_text(headline, headline_font, max_width, draw)
            
            # Calculate position
            bbox = draw.textbbox((0, 0), wrapped_headline, font=headline_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if spec.headline_position == "top":
                y = safe_top
            elif spec.headline_position == "center":
                y = (spec.height - text_height) // 2 - 50
            else:  # bottom
                y = safe_bottom - text_height - 100
            
            x = (spec.width - text_width) // 2
            
            # Draw shadow
            draw.text((x + 2, y + 2), wrapped_headline, font=headline_font, fill=(0, 0, 0, 180))
            # Draw text
            draw.text((x, y), wrapped_headline, font=headline_font, fill=self.config.headline_color)
        
        # Draw CTA button
        if cta:
            cta_font_size = int(28 * spec.font_scale)
            cta_font = self._get_font(cta_font_size)
            
            bbox = draw.textbbox((0, 0), cta, font=cta_font)
            cta_width = bbox[2] - bbox[0] + 40
            cta_height = bbox[3] - bbox[1] + 20
            
            if spec.cta_position == "bottom":
                cta_y = safe_bottom - cta_height - 20
            elif spec.cta_position == "center":
                cta_y = spec.height // 2 + 60
            else:  # top
                cta_y = safe_top + 100
            
            cta_x = (spec.width - cta_width) // 2
            
            # Draw button background
            draw.rounded_rectangle(
                [cta_x, cta_y, cta_x + cta_width, cta_y + cta_height],
                radius=8,
                fill=self.config.cta_bg_color,
            )
            
            # Draw button text
            text_x = cta_x + (cta_width - (bbox[2] - bbox[0])) // 2
            text_y = cta_y + (cta_height - (bbox[3] - bbox[1])) // 2
            draw.text((text_x, text_y), cta, font=cta_font, fill=self.config.cta_color)
        
        # Add watermark if configured
        if self.config.add_watermark and brand_name:
            watermark_font = self._get_font(int(16 * spec.font_scale))
            draw.text(
                (safe_left, safe_bottom + 10),
                brand_name,
                font=watermark_font,
                fill=(255, 255, 255, 128),
            )
        
        return canvas.convert("RGB")
    
    def _smart_crop(self, image: Image.Image, target_width: int, target_height: int) -> Image.Image:
        """Smart crop and resize image to target dimensions."""
        # Calculate aspect ratios
        source_ratio = image.width / image.height
        target_ratio = target_width / target_height
        
        if source_ratio > target_ratio:
            # Source is wider - crop sides
            new_width = int(image.height * target_ratio)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        else:
            # Source is taller - crop top/bottom (favor top for faces)
            new_height = int(image.width / target_ratio)
            top = (image.height - new_height) // 3  # Favor top third
            image = image.crop((0, top, image.width, top + new_height))
        
        # Resize to exact dimensions
        return image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return "\n".join(lines)
    
    def get_available_formats(self) -> list[dict]:
        """Get list of available formats with their specs."""
        return [
            {
                "id": fmt.value,
                "name": spec.name,
                "dimensions": f"{spec.width}x{spec.height}",
                "aspect_ratio": spec.aspect_ratio,
                "platforms": spec.platforms,
            }
            for fmt, spec in FORMAT_SPECS.items()
        ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def export_all_formats(
    source_image_url: str,
    headline: str,
    cta: str,
    output_dir: str = "./output",
    formats: Optional[list[str]] = None,
) -> ExportResult:
    """
    Quick export to all or selected formats.
    
    Args:
        source_image_url: URL of source image
        headline: Ad headline
        cta: Call to action
        output_dir: Output directory
        formats: List of format names (None = all)
    
    Returns:
        ExportResult
    """
    config = ExportConfig(
        output_dir=output_dir,
        create_zip=True,
    )
    
    if formats:
        config.formats = [ExportFormat(f) for f in formats]
    
    exporter = FormatExporter(config)
    return await exporter.export_all(
        source_image_url=source_image_url,
        headline=headline,
        cta=cta,
    )


def get_format_catalog() -> list[dict]:
    """Get catalog of all available formats."""
    return [
        {
            "id": fmt.value,
            "name": spec.name,
            "width": spec.width,
            "height": spec.height,
            "aspect_ratio": spec.aspect_ratio,
            "platforms": spec.platforms,
        }
        for fmt, spec in FORMAT_SPECS.items()
    ]


# =============================================================================
# DEMO
# =============================================================================

async def demo_exporter():
    """Demo the format exporter."""
    print("\n" + "="*60)
    print("MULTI-FORMAT EXPORTER DEMO")
    print("="*60)
    
    exporter = FormatExporter(ExportConfig(
        output_dir="./output/export_demo",
        create_zip=True,
    ))
    
    print("\n📋 Available Formats:")
    for fmt in exporter.get_available_formats():
        print(f"  • {fmt['name']:20} {fmt['dimensions']:12} {', '.join(fmt['platforms'][:2])}")
    
    print("\n🖼️ Exporting ad to all formats...")
    
    result = await exporter.export_all(
        source_image_url="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=1200",
        headline="Stop Getting Rejected by ATS",
        primary_text="Build resumes that get interviews with AI-powered optimization.",
        cta="Get Started",
        brand_name="Careerfied",
    )
    
    print(f"\n✅ Exported {len(result.formats_exported)} formats in {result.export_time_ms}ms")
    print(f"📦 Total size: {result.total_size_kb} KB")
    
    for exp in result.formats_exported:
        print(f"  ✓ {exp.spec.name:20} {exp.dimensions[0]}x{exp.dimensions[1]} ({exp.file_size_kb} KB)")
    
    if result.zip_path:
        print(f"\n📁 ZIP: {result.zip_path}")
    
    if result.errors:
        print(f"\n⚠️ Errors: {result.errors}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_exporter())
