# src/analyzers/attention_analyzer.py
"""Attention Heatmap Analyzer for BrandTruth AI - Slice 10

Predicts where users' eyes will focus on an ad using AI analysis.

Features:
- Eye-tracking prediction without hardware
- Attention heatmap generation
- First-focus point identification
- Reading flow analysis
- Attention distribution scoring
- Visual hierarchy assessment

Uses Claude Vision to analyze:
- Focal points and visual weight
- Color contrast and salience
- Face detection (eyes attract eyes)
- Text positioning and readability
- CTA visibility
- Visual flow patterns
"""

import asyncio
import base64
import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFilter
from pydantic import BaseModel, Field

from anthropic import Anthropic

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class AttentionLevel(str, Enum):
    """Attention intensity levels."""
    VERY_HIGH = "very_high"    # Red - immediate focus
    HIGH = "high"              # Orange - strong attention
    MEDIUM = "medium"          # Yellow - moderate attention
    LOW = "low"                # Green - peripheral
    VERY_LOW = "very_low"      # Blue - barely noticed


class ElementType(str, Enum):
    """Types of visual elements."""
    FACE = "face"
    TEXT_HEADLINE = "text_headline"
    TEXT_BODY = "text_body"
    CTA_BUTTON = "cta_button"
    LOGO = "logo"
    PRODUCT = "product"
    BACKGROUND = "background"
    IMAGE_FOCAL = "image_focal"
    OTHER = "other"


# =============================================================================
# DATA MODELS
# =============================================================================

class AttentionPoint(BaseModel):
    """A point of attention on the image."""
    x: float = Field(ge=0, le=1)  # 0-1 normalized
    y: float = Field(ge=0, le=1)  # 0-1 normalized
    radius: float = Field(ge=0, le=0.5)  # Radius of attention area
    intensity: float = Field(ge=0, le=1)  # 0-1 intensity
    element_type: ElementType
    description: str
    attention_level: AttentionLevel
    time_to_notice_ms: int  # Estimated milliseconds to notice


class VisualFlowStep(BaseModel):
    """A step in the visual flow sequence."""
    order: int
    x: float
    y: float
    element: str
    dwell_time_ms: int
    description: str


class AttentionAnalysis(BaseModel):
    """Complete attention analysis for an ad."""
    # Summary metrics
    overall_score: int = Field(ge=0, le=100)
    cta_visibility_score: int = Field(ge=0, le=100)
    headline_visibility_score: int = Field(ge=0, le=100)
    
    # First impressions
    first_focus_point: AttentionPoint
    first_focus_element: str
    time_to_cta_ms: int
    
    # Attention distribution
    attention_points: list[AttentionPoint]
    attention_distribution: dict[str, float]  # Element type -> % of attention
    
    # Visual flow
    visual_flow: list[VisualFlowStep]
    flow_efficiency: float  # How well flow leads to CTA
    
    # Issues and recommendations
    attention_issues: list[str]
    recommendations: list[str]
    
    # Heatmap data
    heatmap_data: list[list[float]] = Field(default_factory=list)  # Grid of intensities
    
    # Meta
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    image_dimensions: tuple[int, int] = (1080, 1080)
    
    def get_summary(self) -> str:
        """Get a human-readable summary."""
        return f"👁️ Attention Score: {self.overall_score}/100 | First focus: {self.first_focus_element} | CTA visibility: {self.cta_visibility_score}%"


class HeatmapConfig(BaseModel):
    """Configuration for heatmap generation."""
    width: int = 400
    height: int = 400
    opacity: float = 0.6
    blur_radius: int = 30
    color_scheme: str = "thermal"  # thermal, viridis, plasma


# =============================================================================
# ATTENTION ANALYZER
# =============================================================================

class AttentionAnalyzer:
    """Analyzes visual attention patterns in ads using AI."""
    
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-sonnet-4-20250514"
    
    async def analyze(
        self, 
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        ad_context: Optional[dict] = None,
    ) -> AttentionAnalysis:
        """
        Analyze attention patterns in an ad image.
        
        Args:
            image_path: Local path to image
            image_url: URL of image
            image_base64: Base64 encoded image
            ad_context: Optional context (headline, CTA, etc.)
        
        Returns:
            AttentionAnalysis with heatmap data and recommendations
        """
        logger.info("Analyzing attention patterns...")
        
        # Get image data
        image_data, media_type, dimensions = await self._prepare_image(
            image_path, image_url, image_base64
        )
        
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(ad_context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
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
                            },
                        ],
                    }
                ],
            )
            
            result_text = response.content[0].text
            
            # Parse JSON response
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result_json = json.loads(result_text[json_start:json_end])
                analysis = self._parse_analysis(result_json, dimensions)
                
                # Generate heatmap grid
                analysis.heatmap_data = self._generate_heatmap_grid(
                    analysis.attention_points,
                    dimensions
                )
                
                return analysis
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._default_analysis(str(e), dimensions)
    
    async def _prepare_image(
        self,
        image_path: Optional[str],
        image_url: Optional[str],
        image_base64: Optional[str],
    ) -> tuple[str, str, tuple[int, int]]:
        """Prepare image data for API call."""
        if image_base64:
            # Assume JPEG if base64 provided
            return image_base64, "image/jpeg", (1080, 1080)
        
        if image_path:
            path = Path(image_path)
            with open(path, "rb") as f:
                image_bytes = f.read()
            
            # Get dimensions
            with Image.open(path) as img:
                dimensions = img.size
            
            media_type = "image/jpeg" if path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            return base64.b64encode(image_bytes).decode(), media_type, dimensions
        
        if image_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_bytes = response.content
            
            # Get dimensions
            with Image.open(BytesIO(image_bytes)) as img:
                dimensions = img.size
            
            media_type = "image/jpeg"
            return base64.b64encode(image_bytes).decode(), media_type, dimensions
        
        raise ValueError("Must provide image_path, image_url, or image_base64")
    
    def _build_analysis_prompt(self, ad_context: Optional[dict]) -> str:
        """Build the analysis prompt."""
        context_str = ""
        if ad_context:
            context_str = f"""
## Ad Context
- Headline: {ad_context.get('headline', 'Unknown')}
- CTA: {ad_context.get('cta', 'Unknown')}
- Primary Text: {ad_context.get('primary_text', 'Unknown')[:100]}...
"""

        return f"""You are an expert in eye-tracking research and visual attention analysis with 15+ years experience in advertising effectiveness.

Analyze this ad image and predict where viewers' eyes will naturally focus, in what order, and for how long.

{context_str}

## Analysis Framework

1. **First Focus Point**: Where will the eye land first? (0-50ms)
   - High contrast areas
   - Faces (especially eyes)
   - Bright colors against dark
   - Movement suggestion
   - Centered elements

2. **Visual Flow**: The natural path the eye takes through the ad
   - F-pattern or Z-pattern reading
   - Size hierarchy
   - Color contrast guidance
   - Line direction and arrows
   - Whitespace channeling

3. **Attention Distribution**: What % of attention goes to each element?
   - Headline
   - Body text
   - CTA button
   - Product/hero image
   - Logo
   - Background elements

4. **Key Metrics**:
   - Time to notice CTA (ms)
   - CTA visibility score
   - Headline visibility score
   - Overall attention effectiveness

## Response Format

Return a JSON object:

{{
  "overall_score": <0-100>,
  "cta_visibility_score": <0-100>,
  "headline_visibility_score": <0-100>,
  "first_focus_point": {{
    "x": <0.0-1.0>,
    "y": <0.0-1.0>,
    "radius": <0.05-0.3>,
    "intensity": <0.8-1.0>,
    "element_type": "<face|text_headline|text_body|cta_button|logo|product|image_focal|other>",
    "description": "<what element>",
    "attention_level": "very_high",
    "time_to_notice_ms": <0-100>
  }},
  "first_focus_element": "<human readable description>",
  "time_to_cta_ms": <estimated ms to notice CTA>,
  "attention_points": [
    {{
      "x": <0.0-1.0>,
      "y": <0.0-1.0>,
      "radius": <0.05-0.3>,
      "intensity": <0.0-1.0>,
      "element_type": "<type>",
      "description": "<what>",
      "attention_level": "<very_high|high|medium|low|very_low>",
      "time_to_notice_ms": <ms>
    }}
  ],
  "attention_distribution": {{
    "headline": <0-100>,
    "body_text": <0-100>,
    "cta": <0-100>,
    "product_image": <0-100>,
    "face": <0-100>,
    "logo": <0-100>,
    "background": <0-100>
  }},
  "visual_flow": [
    {{
      "order": 1,
      "x": <0.0-1.0>,
      "y": <0.0-1.0>,
      "element": "<what the eye sees>",
      "dwell_time_ms": <ms spent looking>,
      "description": "<why eye goes here>"
    }}
  ],
  "flow_efficiency": <0.0-1.0>,
  "attention_issues": [
    "<issue 1>",
    "<issue 2>"
  ],
  "recommendations": [
    "<recommendation 1>",
    "<recommendation 2>"
  ]
}}

Provide 5-8 attention points covering all major elements. Provide 4-6 visual flow steps.
Coordinates are normalized 0-1 where (0,0) is top-left and (1,1) is bottom-right."""

    def _parse_analysis(self, data: dict, dimensions: tuple[int, int]) -> AttentionAnalysis:
        """Parse the JSON response into AttentionAnalysis."""
        first_focus = data.get("first_focus_point", {})
        
        return AttentionAnalysis(
            overall_score=data.get("overall_score", 50),
            cta_visibility_score=data.get("cta_visibility_score", 50),
            headline_visibility_score=data.get("headline_visibility_score", 50),
            first_focus_point=AttentionPoint(
                x=first_focus.get("x", 0.5),
                y=first_focus.get("y", 0.5),
                radius=first_focus.get("radius", 0.1),
                intensity=first_focus.get("intensity", 1.0),
                element_type=ElementType(first_focus.get("element_type", "other")),
                description=first_focus.get("description", "Center"),
                attention_level=AttentionLevel(first_focus.get("attention_level", "very_high")),
                time_to_notice_ms=first_focus.get("time_to_notice_ms", 50),
            ),
            first_focus_element=data.get("first_focus_element", "Unknown"),
            time_to_cta_ms=data.get("time_to_cta_ms", 2000),
            attention_points=[
                AttentionPoint(
                    x=p.get("x", 0.5),
                    y=p.get("y", 0.5),
                    radius=p.get("radius", 0.1),
                    intensity=p.get("intensity", 0.5),
                    element_type=ElementType(p.get("element_type", "other")),
                    description=p.get("description", "Element"),
                    attention_level=AttentionLevel(p.get("attention_level", "medium")),
                    time_to_notice_ms=p.get("time_to_notice_ms", 500),
                )
                for p in data.get("attention_points", [])
            ],
            attention_distribution=data.get("attention_distribution", {}),
            visual_flow=[
                VisualFlowStep(
                    order=f.get("order", i + 1),
                    x=f.get("x", 0.5),
                    y=f.get("y", 0.5),
                    element=f.get("element", "Unknown"),
                    dwell_time_ms=f.get("dwell_time_ms", 200),
                    description=f.get("description", ""),
                )
                for i, f in enumerate(data.get("visual_flow", []))
            ],
            flow_efficiency=data.get("flow_efficiency", 0.5),
            attention_issues=data.get("attention_issues", []),
            recommendations=data.get("recommendations", []),
            image_dimensions=dimensions,
        )
    
    def _generate_heatmap_grid(
        self,
        attention_points: list[AttentionPoint],
        dimensions: tuple[int, int],
        grid_size: int = 50,
    ) -> list[list[float]]:
        """Generate a heatmap grid from attention points."""
        grid = [[0.0 for _ in range(grid_size)] for _ in range(grid_size)]
        
        for point in attention_points:
            # Convert normalized coords to grid coords
            cx = int(point.x * grid_size)
            cy = int(point.y * grid_size)
            radius = int(point.radius * grid_size)
            
            # Add gaussian-like distribution around point
            for y in range(max(0, cy - radius * 2), min(grid_size, cy + radius * 2)):
                for x in range(max(0, cx - radius * 2), min(grid_size, cx + radius * 2)):
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if dist < radius * 2:
                        falloff = 1 - (dist / (radius * 2))
                        grid[y][x] = min(1.0, grid[y][x] + point.intensity * falloff)
        
        return grid
    
    def _default_analysis(self, error: str, dimensions: tuple[int, int]) -> AttentionAnalysis:
        """Return default analysis on error."""
        return AttentionAnalysis(
            overall_score=50,
            cta_visibility_score=50,
            headline_visibility_score=50,
            first_focus_point=AttentionPoint(
                x=0.5, y=0.3, radius=0.15, intensity=1.0,
                element_type=ElementType.IMAGE_FOCAL,
                description="Center area",
                attention_level=AttentionLevel.HIGH,
                time_to_notice_ms=50,
            ),
            first_focus_element="Center of image",
            time_to_cta_ms=1500,
            attention_points=[],
            attention_distribution={},
            visual_flow=[],
            flow_efficiency=0.5,
            attention_issues=[f"Analysis error: {error}"],
            recommendations=["Re-run analysis for detailed results"],
            image_dimensions=dimensions,
        )
    
    async def generate_heatmap_image(
        self,
        analysis: AttentionAnalysis,
        original_image_path: Optional[str] = None,
        original_image_url: Optional[str] = None,
        config: Optional[HeatmapConfig] = None,
    ) -> Image.Image:
        """Generate a visual heatmap overlay image."""
        config = config or HeatmapConfig()
        
        # Load original image or create blank
        if original_image_path:
            base_image = Image.open(original_image_path).convert("RGBA")
        elif original_image_url:
            async with httpx.AsyncClient() as client:
                response = await client.get(original_image_url)
                base_image = Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            base_image = Image.new("RGBA", (config.width, config.height), (40, 40, 40, 255))
        
        # Resize to config dimensions
        base_image = base_image.resize((config.width, config.height), Image.Resampling.LANCZOS)
        
        # Create heatmap layer
        heatmap = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(heatmap)
        
        # Color mapping for thermal
        def get_thermal_color(intensity: float) -> tuple[int, int, int, int]:
            """Map intensity to thermal color."""
            alpha = int(intensity * 180 * config.opacity)
            if intensity > 0.8:
                return (255, 0, 0, alpha)  # Red - very high
            elif intensity > 0.6:
                return (255, 128, 0, alpha)  # Orange - high
            elif intensity > 0.4:
                return (255, 255, 0, alpha)  # Yellow - medium
            elif intensity > 0.2:
                return (0, 255, 0, alpha)  # Green - low
            else:
                return (0, 128, 255, alpha)  # Blue - very low
        
        # Draw attention points
        for point in analysis.attention_points:
            x = int(point.x * config.width)
            y = int(point.y * config.height)
            r = int(point.radius * config.width)
            
            # Draw multiple circles for gradient effect
            for i in range(r, 0, -5):
                intensity = point.intensity * (i / r)
                color = get_thermal_color(intensity)
                draw.ellipse(
                    [x - i, y - i, x + i, y + i],
                    fill=color,
                )
        
        # Blur the heatmap
        heatmap = heatmap.filter(ImageFilter.GaussianBlur(config.blur_radius))
        
        # Composite
        result = Image.alpha_composite(base_image, heatmap)
        
        # Draw visual flow arrows
        flow_layer = Image.new("RGBA", (config.width, config.height), (0, 0, 0, 0))
        flow_draw = ImageDraw.Draw(flow_layer)
        
        if len(analysis.visual_flow) > 1:
            for i in range(len(analysis.visual_flow) - 1):
                start = analysis.visual_flow[i]
                end = analysis.visual_flow[i + 1]
                
                x1 = int(start.x * config.width)
                y1 = int(start.y * config.height)
                x2 = int(end.x * config.width)
                y2 = int(end.y * config.height)
                
                # Draw line
                flow_draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 150), width=2)
                
                # Draw number circle
                flow_draw.ellipse(
                    [x1 - 12, y1 - 12, x1 + 12, y1 + 12],
                    fill=(255, 255, 255, 200),
                )
                # Note: Would need font for text, simplified here
        
        result = Image.alpha_composite(result, flow_layer)
        
        return result


# =============================================================================
# MOCK ANALYZER FOR DEMO
# =============================================================================

class MockAttentionAnalyzer:
    """Mock analyzer for demo/testing."""
    
    async def analyze(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        ad_context: Optional[dict] = None,
    ) -> AttentionAnalysis:
        """Generate realistic mock analysis."""
        await asyncio.sleep(0.5)
        
        # Determine dimensions
        dimensions = (1080, 1080)
        if image_path:
            try:
                with Image.open(image_path) as img:
                    dimensions = img.size
            except:
                pass
        
        return AttentionAnalysis(
            overall_score=78,
            cta_visibility_score=72,
            headline_visibility_score=85,
            first_focus_point=AttentionPoint(
                x=0.5, y=0.25,
                radius=0.15,
                intensity=1.0,
                element_type=ElementType.TEXT_HEADLINE,
                description="Main headline text",
                attention_level=AttentionLevel.VERY_HIGH,
                time_to_notice_ms=50,
            ),
            first_focus_element="Headline: 'Stop Getting Rejected by ATS'",
            time_to_cta_ms=1200,
            attention_points=[
                AttentionPoint(
                    x=0.5, y=0.25, radius=0.15, intensity=1.0,
                    element_type=ElementType.TEXT_HEADLINE,
                    description="Headline",
                    attention_level=AttentionLevel.VERY_HIGH,
                    time_to_notice_ms=50,
                ),
                AttentionPoint(
                    x=0.5, y=0.5, radius=0.2, intensity=0.85,
                    element_type=ElementType.IMAGE_FOCAL,
                    description="Hero image - person at laptop",
                    attention_level=AttentionLevel.HIGH,
                    time_to_notice_ms=200,
                ),
                AttentionPoint(
                    x=0.5, y=0.75, radius=0.12, intensity=0.75,
                    element_type=ElementType.CTA_BUTTON,
                    description="CTA Button",
                    attention_level=AttentionLevel.HIGH,
                    time_to_notice_ms=800,
                ),
                AttentionPoint(
                    x=0.5, y=0.4, radius=0.1, intensity=0.6,
                    element_type=ElementType.TEXT_BODY,
                    description="Body text",
                    attention_level=AttentionLevel.MEDIUM,
                    time_to_notice_ms=500,
                ),
                AttentionPoint(
                    x=0.85, y=0.1, radius=0.08, intensity=0.4,
                    element_type=ElementType.LOGO,
                    description="Brand logo",
                    attention_level=AttentionLevel.LOW,
                    time_to_notice_ms=1500,
                ),
            ],
            attention_distribution={
                "headline": 30,
                "body_text": 15,
                "cta": 20,
                "product_image": 25,
                "face": 0,
                "logo": 5,
                "background": 5,
            },
            visual_flow=[
                VisualFlowStep(
                    order=1, x=0.5, y=0.25,
                    element="Headline",
                    dwell_time_ms=400,
                    description="Eye lands on high-contrast headline first",
                ),
                VisualFlowStep(
                    order=2, x=0.5, y=0.5,
                    element="Hero image",
                    dwell_time_ms=600,
                    description="Natural downward flow to main visual",
                ),
                VisualFlowStep(
                    order=3, x=0.5, y=0.4,
                    element="Body text",
                    dwell_time_ms=300,
                    description="Scans supporting copy",
                ),
                VisualFlowStep(
                    order=4, x=0.5, y=0.75,
                    element="CTA button",
                    dwell_time_ms=200,
                    description="Arrives at call to action",
                ),
                VisualFlowStep(
                    order=5, x=0.85, y=0.1,
                    element="Logo",
                    dwell_time_ms=100,
                    description="Quick brand recognition check",
                ),
            ],
            flow_efficiency=0.78,
            attention_issues=[
                "CTA button could be more prominent",
                "Body text competes with hero image for attention",
                "Logo placement may be overlooked initially",
            ],
            recommendations=[
                "Increase CTA button size by 20% for better visibility",
                "Add subtle arrow or visual cue pointing to CTA",
                "Consider adding a face/person in hero image - faces attract 30% more attention",
                "Use higher contrast for CTA button background",
            ],
            image_dimensions=dimensions,
        )
    
    async def generate_heatmap_image(
        self,
        analysis: AttentionAnalysis,
        original_image_path: Optional[str] = None,
        original_image_url: Optional[str] = None,
        config: Optional[HeatmapConfig] = None,
    ) -> Image.Image:
        """Generate heatmap using the real implementation."""
        real_analyzer = AttentionAnalyzer()
        return await real_analyzer.generate_heatmap_image(
            analysis, original_image_path, original_image_url, config
        )


def get_attention_analyzer() -> AttentionAnalyzer | MockAttentionAnalyzer:
    """Get appropriate analyzer based on configuration."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return AttentionAnalyzer()
    return MockAttentionAnalyzer()


# =============================================================================
# DEMO
# =============================================================================

async def demo_attention_analyzer():
    """Demo the attention analyzer."""
    print("\n" + "="*60)
    print("ATTENTION HEATMAP ANALYZER DEMO")
    print("="*60)
    
    analyzer = get_attention_analyzer()
    
    # Analyze a sample image
    print("\n👁️ Analyzing attention patterns...")
    
    analysis = await analyzer.analyze(
        image_url="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600",
        ad_context={
            "headline": "Stop Getting Rejected by ATS",
            "cta": "Get Started",
            "primary_text": "Build resumes that get interviews...",
        }
    )
    
    print(f"\n{analysis.get_summary()}")
    print(f"\n📍 First Focus: {analysis.first_focus_element}")
    print(f"⏱️  Time to CTA: {analysis.time_to_cta_ms}ms")
    print(f"🎯 Flow Efficiency: {analysis.flow_efficiency:.0%}")
    
    print("\n📊 Attention Distribution:")
    for element, pct in analysis.attention_distribution.items():
        if pct > 0:
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {element:15} {bar} {pct}%")
    
    print("\n👀 Visual Flow:")
    for step in analysis.visual_flow:
        print(f"  {step.order}. {step.element} ({step.dwell_time_ms}ms)")
    
    print("\n⚠️ Issues:")
    for issue in analysis.attention_issues:
        print(f"  • {issue}")
    
    print("\n💡 Recommendations:")
    for rec in analysis.recommendations:
        print(f"  • {rec}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_attention_analyzer())
