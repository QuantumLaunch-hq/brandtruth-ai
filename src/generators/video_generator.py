# src/generators/video_generator.py
"""AI UGC Video Generator for BrandTruth AI - Slice 13

Generates TikTok-style video ads with AI avatars.

Features:
- Script-to-video conversion
- AI avatar selection
- Multiple video styles (UGC, testimonial, demo, explainer)
- Auto-captioning
- Background music selection
- Aspect ratio options (9:16, 1:1, 16:9)
- Hook optimization

Video Generation Pipeline:
1. Script input/generation
2. Avatar selection
3. Voice synthesis
4. Scene composition
5. Caption generation
6. Music overlay
7. Final render

Integration Options:
- HeyGen API
- Synthesia API
- D-ID API
- Runway ML
- (Mock mode for demo)
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class VideoStyle(str, Enum):
    """Video content styles."""
    UGC = "ugc"                    # User-generated content style
    TESTIMONIAL = "testimonial"    # Customer testimonial
    DEMO = "demo"                  # Product demonstration
    EXPLAINER = "explainer"        # Educational explainer
    STORYTELLING = "storytelling"  # Narrative format
    LISTICLE = "listicle"          # List-based content


class AspectRatio(str, Enum):
    """Video aspect ratios."""
    VERTICAL = "9:16"      # TikTok, Reels, Stories
    SQUARE = "1:1"         # Feed posts
    HORIZONTAL = "16:9"    # YouTube, landscape


class AvatarStyle(str, Enum):
    """AI avatar presentation styles."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    ENERGETIC = "energetic"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"


class VoiceTone(str, Enum):
    """Voice synthesis tones."""
    CONVERSATIONAL = "conversational"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"


class VideoStatus(str, Enum):
    """Video generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    RENDERING = "rendering"
    COMPLETE = "complete"
    FAILED = "failed"


# =============================================================================
# DATA MODELS
# =============================================================================

class Avatar(BaseModel):
    """AI avatar definition."""
    avatar_id: str
    name: str
    gender: str
    age_range: str
    ethnicity: str
    style: AvatarStyle
    preview_url: str
    supported_languages: list[str] = Field(default_factory=lambda: ["en"])


class VideoScene(BaseModel):
    """Single scene in a video."""
    scene_id: str
    scene_number: int
    duration_seconds: float
    script_text: str
    visual_type: str  # avatar, b-roll, text-overlay, product-shot
    visual_description: Optional[str] = None
    transition: str = "cut"  # cut, fade, slide
    caption_style: str = "dynamic"  # dynamic, static, none


class VideoScript(BaseModel):
    """Complete video script."""
    script_id: str
    title: str
    hook: str  # First 3 seconds
    body: list[str]  # Main content points
    cta: str  # Call to action
    total_duration_seconds: float
    scenes: list[VideoScene] = Field(default_factory=list)
    
    def get_full_script(self) -> str:
        """Get full script text."""
        return f"{self.hook}\n\n" + "\n".join(self.body) + f"\n\n{self.cta}"


class MusicTrack(BaseModel):
    """Background music track."""
    track_id: str
    name: str
    genre: str
    mood: str
    duration_seconds: float
    bpm: int
    preview_url: Optional[str] = None


class VideoConfig(BaseModel):
    """Configuration for video generation."""
    style: VideoStyle = VideoStyle.UGC
    aspect_ratio: AspectRatio = AspectRatio.VERTICAL
    avatar_id: Optional[str] = None
    avatar_style: AvatarStyle = AvatarStyle.CASUAL
    voice_tone: VoiceTone = VoiceTone.CONVERSATIONAL
    include_captions: bool = True
    caption_style: str = "dynamic"
    include_music: bool = True
    music_volume: float = 0.3
    brand_colors: Optional[list[str]] = None
    logo_url: Optional[str] = None
    max_duration_seconds: int = 60


class GeneratedVideo(BaseModel):
    """Generated video result."""
    video_id: str
    title: str
    status: VideoStatus
    style: VideoStyle
    aspect_ratio: AspectRatio
    duration_seconds: float
    
    # URLs
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    
    # Content
    script: VideoScript
    avatar: Optional[Avatar] = None
    music_track: Optional[MusicTrack] = None
    
    # Metadata
    file_size_mb: Optional[float] = None
    resolution: str = "1080x1920"
    fps: int = 30
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Analytics predictions
    predicted_engagement_score: int = 0
    hook_strength: int = 0
    
    def get_summary(self) -> str:
        """Get video summary."""
        return f"🎬 {self.title} | {self.style.value} | {self.aspect_ratio.value} | {self.duration_seconds:.0f}s | Score: {self.predicted_engagement_score}/100"


class VideoGenerationRequest(BaseModel):
    """Request to generate a video."""
    brand_name: str
    product_description: str
    target_audience: str
    key_benefits: list[str]
    cta: str = "Learn More"
    config: VideoConfig = Field(default_factory=VideoConfig)
    custom_script: Optional[str] = None


# =============================================================================
# VIDEO GENERATOR
# =============================================================================

class VideoGenerator:
    """Generates AI-powered video ads."""
    
    # Pre-defined avatars
    AVATARS = [
        Avatar(
            avatar_id="avatar_sarah",
            name="Sarah",
            gender="female",
            age_range="25-35",
            ethnicity="caucasian",
            style=AvatarStyle.FRIENDLY,
            preview_url="/avatars/sarah.jpg",
        ),
        Avatar(
            avatar_id="avatar_marcus",
            name="Marcus",
            gender="male",
            age_range="30-40",
            ethnicity="african-american",
            style=AvatarStyle.PROFESSIONAL,
            preview_url="/avatars/marcus.jpg",
        ),
        Avatar(
            avatar_id="avatar_emily",
            name="Emily",
            gender="female",
            age_range="20-30",
            ethnicity="asian",
            style=AvatarStyle.ENERGETIC,
            preview_url="/avatars/emily.jpg",
        ),
        Avatar(
            avatar_id="avatar_james",
            name="James",
            gender="male",
            age_range="35-45",
            ethnicity="caucasian",
            style=AvatarStyle.AUTHORITATIVE,
            preview_url="/avatars/james.jpg",
        ),
        Avatar(
            avatar_id="avatar_maya",
            name="Maya",
            gender="female",
            age_range="25-35",
            ethnicity="hispanic",
            style=AvatarStyle.CASUAL,
            preview_url="/avatars/maya.jpg",
        ),
    ]
    
    # Pre-defined music tracks
    MUSIC_TRACKS = [
        MusicTrack(track_id="track_upbeat", name="Upbeat Energy", genre="electronic", mood="energetic", duration_seconds=120, bpm=128),
        MusicTrack(track_id="track_inspiring", name="Inspiring Journey", genre="cinematic", mood="inspiring", duration_seconds=180, bpm=90),
        MusicTrack(track_id="track_chill", name="Chill Vibes", genre="lo-fi", mood="relaxed", duration_seconds=150, bpm=85),
        MusicTrack(track_id="track_corporate", name="Professional Growth", genre="corporate", mood="professional", duration_seconds=120, bpm=100),
        MusicTrack(track_id="track_trendy", name="TikTok Trending", genre="pop", mood="fun", duration_seconds=60, bpm=140),
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VIDEO_API_KEY")
        self.output_dir = Path("./output/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_video(self, request: VideoGenerationRequest) -> GeneratedVideo:
        """
        Generate a video ad from the request.
        
        Args:
            request: Video generation request with brand info and config
        
        Returns:
            GeneratedVideo with URLs and metadata
        """
        logger.info(f"Generating {request.config.style.value} video for {request.brand_name}...")
        
        video_id = f"vid_{hashlib.md5(f'{request.brand_name}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}"
        
        # Step 1: Generate or parse script
        if request.custom_script:
            script = self._parse_custom_script(request.custom_script, video_id)
        else:
            script = await self._generate_script(request, video_id)
        
        # Step 2: Select avatar
        avatar = self._select_avatar(request.config)
        
        # Step 3: Select music
        music = self._select_music(request.config.style)
        
        # Step 4: Generate scenes
        scenes = self._generate_scenes(script, request.config)
        script.scenes = scenes
        
        # Step 5: Calculate engagement prediction
        engagement_score = self._predict_engagement(script, request.config)
        hook_strength = self._analyze_hook(script.hook)
        
        # Step 6: Mock render (in production, call video API)
        video_url, thumbnail_url = await self._render_video(
            video_id, script, avatar, music, request.config
        )
        
        # Calculate duration
        duration = sum(scene.duration_seconds for scene in scenes)
        
        return GeneratedVideo(
            video_id=video_id,
            title=f"{request.brand_name} - {request.config.style.value.title()} Ad",
            status=VideoStatus.COMPLETE,
            style=request.config.style,
            aspect_ratio=request.config.aspect_ratio,
            duration_seconds=duration,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            preview_url=video_url,
            script=script,
            avatar=avatar,
            music_track=music if request.config.include_music else None,
            file_size_mb=round(duration * 0.5, 1),  # ~0.5 MB per second estimate
            resolution=self._get_resolution(request.config.aspect_ratio),
            predicted_engagement_score=engagement_score,
            hook_strength=hook_strength,
            completed_at=datetime.utcnow(),
        )
    
    async def _generate_script(self, request: VideoGenerationRequest, video_id: str) -> VideoScript:
        """Generate video script from request."""
        # In production, use Claude to generate script
        # For now, use template-based generation
        
        style = request.config.style
        
        # Generate hook based on style
        hooks = {
            VideoStyle.UGC: f"POV: You just discovered {request.brand_name} and it changed everything",
            VideoStyle.TESTIMONIAL: f"I never thought {request.brand_name} would work this well...",
            VideoStyle.DEMO: f"Let me show you exactly how {request.brand_name} works",
            VideoStyle.EXPLAINER: f"Here's why everyone's talking about {request.brand_name}",
            VideoStyle.STORYTELLING: f"6 months ago, I was struggling with {request.target_audience.split()[0].lower()} problems...",
            VideoStyle.LISTICLE: f"3 reasons why {request.brand_name} is a game changer",
        }
        hook = hooks.get(style, f"Check out {request.brand_name}")
        
        # Generate body points
        body = []
        for i, benefit in enumerate(request.key_benefits[:3], 1):
            if style == VideoStyle.LISTICLE:
                body.append(f"Number {i}: {benefit}")
            elif style == VideoStyle.UGC:
                body.append(f"The {benefit.lower()} is absolutely insane")
            elif style == VideoStyle.TESTIMONIAL:
                body.append(f"What really impressed me was the {benefit.lower()}")
            else:
                body.append(benefit)
        
        # Generate CTA
        ctas = {
            VideoStyle.UGC: f"Link in bio to try {request.brand_name}!",
            VideoStyle.TESTIMONIAL: f"Try {request.brand_name} yourself - link below",
            VideoStyle.DEMO: f"Get started with {request.brand_name} today",
            VideoStyle.EXPLAINER: f"Click the link to learn more about {request.brand_name}",
            VideoStyle.STORYTELLING: f"Start your journey with {request.brand_name}",
            VideoStyle.LISTICLE: f"Don't miss out - check out {request.brand_name}",
        }
        cta = ctas.get(style, request.cta)
        
        # Calculate duration (rough estimate: 3 words per second)
        full_text = f"{hook} " + " ".join(body) + f" {cta}"
        word_count = len(full_text.split())
        duration = min(request.config.max_duration_seconds, max(15, word_count / 3))
        
        return VideoScript(
            script_id=f"script_{video_id}",
            title=f"{request.brand_name} {style.value.title()} Script",
            hook=hook,
            body=body,
            cta=cta,
            total_duration_seconds=duration,
        )
    
    def _parse_custom_script(self, custom_script: str, video_id: str) -> VideoScript:
        """Parse custom script into VideoScript."""
        lines = [line.strip() for line in custom_script.strip().split('\n') if line.strip()]
        
        hook = lines[0] if lines else "Check this out"
        body = lines[1:-1] if len(lines) > 2 else []
        cta = lines[-1] if len(lines) > 1 else "Learn more"
        
        word_count = len(custom_script.split())
        duration = max(15, word_count / 3)
        
        return VideoScript(
            script_id=f"script_{video_id}",
            title="Custom Script",
            hook=hook,
            body=body,
            cta=cta,
            total_duration_seconds=duration,
        )
    
    def _select_avatar(self, config: VideoConfig) -> Avatar:
        """Select appropriate avatar."""
        if config.avatar_id:
            avatar = next((a for a in self.AVATARS if a.avatar_id == config.avatar_id), None)
            if avatar:
                return avatar
        
        # Match by style
        style_match = next((a for a in self.AVATARS if a.style == config.avatar_style), None)
        if style_match:
            return style_match
        
        return self.AVATARS[0]
    
    def _select_music(self, style: VideoStyle) -> MusicTrack:
        """Select appropriate music track."""
        mood_map = {
            VideoStyle.UGC: "fun",
            VideoStyle.TESTIMONIAL: "inspiring",
            VideoStyle.DEMO: "professional",
            VideoStyle.EXPLAINER: "professional",
            VideoStyle.STORYTELLING: "inspiring",
            VideoStyle.LISTICLE: "energetic",
        }
        target_mood = mood_map.get(style, "energetic")
        
        track = next((t for t in self.MUSIC_TRACKS if t.mood == target_mood), None)
        return track or self.MUSIC_TRACKS[0]
    
    def _generate_scenes(self, script: VideoScript, config: VideoConfig) -> list[VideoScene]:
        """Generate scene breakdown."""
        scenes = []
        
        # Hook scene (first 3 seconds)
        scenes.append(VideoScene(
            scene_id="scene_hook",
            scene_number=1,
            duration_seconds=3.0,
            script_text=script.hook,
            visual_type="avatar",
            visual_description="Close-up, engaging expression",
            transition="cut",
            caption_style="dynamic",
        ))
        
        # Body scenes
        body_duration = (script.total_duration_seconds - 6) / max(1, len(script.body))
        for i, point in enumerate(script.body, 2):
            scenes.append(VideoScene(
                scene_id=f"scene_body_{i-1}",
                scene_number=i,
                duration_seconds=body_duration,
                script_text=point,
                visual_type="avatar" if i % 2 == 0 else "b-roll",
                visual_description=f"Point {i-1} visualization",
                transition="fade" if i == 2 else "slide",
                caption_style="dynamic",
            ))
        
        # CTA scene (last 3 seconds)
        scenes.append(VideoScene(
            scene_id="scene_cta",
            scene_number=len(scenes) + 1,
            duration_seconds=3.0,
            script_text=script.cta,
            visual_type="text-overlay",
            visual_description="CTA with brand logo",
            transition="fade",
            caption_style="static",
        ))
        
        return scenes
    
    def _predict_engagement(self, script: VideoScript, config: VideoConfig) -> int:
        """Predict engagement score 0-100."""
        score = 50  # Base score
        
        # Hook bonus
        hook_lower = script.hook.lower()
        if any(w in hook_lower for w in ["pov", "you", "this", "here's"]):
            score += 15
        
        # Length optimization (15-30 seconds is ideal for TikTok)
        if 15 <= script.total_duration_seconds <= 30:
            score += 10
        elif script.total_duration_seconds > 60:
            score -= 10
        
        # Benefits count
        if len(script.body) >= 3:
            score += 10
        
        # Style bonus
        if config.style in [VideoStyle.UGC, VideoStyle.STORYTELLING]:
            score += 10
        
        # Captions
        if config.include_captions:
            score += 5
        
        return min(100, max(0, score))
    
    def _analyze_hook(self, hook: str) -> int:
        """Analyze hook strength 0-100."""
        score = 50
        
        hook_lower = hook.lower()
        
        # Strong hook patterns
        if hook_lower.startswith("pov"):
            score += 20
        if "?" in hook:
            score += 10
        if any(w in hook_lower for w in ["secret", "hack", "mistake", "changed"]):
            score += 15
        if len(hook.split()) <= 10:
            score += 10
        
        # Weak patterns
        if hook_lower.startswith("hi") or hook_lower.startswith("hello"):
            score -= 15
        
        return min(100, max(0, score))
    
    async def _render_video(
        self,
        video_id: str,
        script: VideoScript,
        avatar: Avatar,
        music: MusicTrack,
        config: VideoConfig,
    ) -> tuple[str, str]:
        """
        Render the video.
        
        In production, this would call HeyGen/Synthesia/D-ID API.
        For demo, returns mock URLs.
        """
        await asyncio.sleep(0.5)  # Simulate processing
        
        # Mock URLs (in production, these would be real video URLs)
        video_url = f"/output/videos/{video_id}.mp4"
        thumbnail_url = f"/output/videos/{video_id}_thumb.jpg"
        
        # Create a placeholder file
        placeholder_path = self.output_dir / f"{video_id}.json"
        placeholder_path.write_text(json.dumps({
            "video_id": video_id,
            "script": script.get_full_script(),
            "avatar": avatar.name,
            "music": music.name,
            "config": config.model_dump(),
            "status": "mock_render",
            "note": "In production, this would be a real video file",
        }, indent=2))
        
        return video_url, thumbnail_url
    
    def _get_resolution(self, aspect_ratio: AspectRatio) -> str:
        """Get resolution for aspect ratio."""
        resolutions = {
            AspectRatio.VERTICAL: "1080x1920",
            AspectRatio.SQUARE: "1080x1080",
            AspectRatio.HORIZONTAL: "1920x1080",
        }
        return resolutions.get(aspect_ratio, "1080x1920")
    
    def get_avatars(self) -> list[Avatar]:
        """Get available avatars."""
        return self.AVATARS
    
    def get_music_tracks(self) -> list[MusicTrack]:
        """Get available music tracks."""
        return self.MUSIC_TRACKS
    
    def get_video_styles(self) -> list[dict]:
        """Get available video styles with descriptions."""
        return [
            {"id": VideoStyle.UGC.value, "name": "UGC Style", "description": "User-generated content feel, authentic and relatable"},
            {"id": VideoStyle.TESTIMONIAL.value, "name": "Testimonial", "description": "Customer success story format"},
            {"id": VideoStyle.DEMO.value, "name": "Product Demo", "description": "Show how your product works"},
            {"id": VideoStyle.EXPLAINER.value, "name": "Explainer", "description": "Educational content about your solution"},
            {"id": VideoStyle.STORYTELLING.value, "name": "Storytelling", "description": "Narrative journey format"},
            {"id": VideoStyle.LISTICLE.value, "name": "Listicle", "description": "List-based content (3 reasons, 5 tips)"},
        ]


def get_video_generator() -> VideoGenerator:
    """Get video generator instance."""
    return VideoGenerator()


# =============================================================================
# DEMO
# =============================================================================

async def demo_video_generator():
    """Demo the video generator."""
    print("\n" + "="*60)
    print("AI UGC VIDEO GENERATOR DEMO")
    print("="*60)
    
    generator = VideoGenerator()
    
    # Test different styles
    styles = [VideoStyle.UGC, VideoStyle.TESTIMONIAL, VideoStyle.LISTICLE]
    
    for style in styles:
        print(f"\n🎬 Generating {style.value.upper()} video...")
        
        request = VideoGenerationRequest(
            brand_name="Careerfied",
            product_description="AI-powered resume builder that helps job seekers pass ATS screening",
            target_audience="Job seekers frustrated with resume rejections",
            key_benefits=[
                "AI-optimized for ATS systems",
                "Industry-specific templates",
                "Real-time feedback and scoring",
            ],
            cta="Get Started Free",
            config=VideoConfig(
                style=style,
                aspect_ratio=AspectRatio.VERTICAL,
                avatar_style=AvatarStyle.CASUAL,
                include_captions=True,
                include_music=True,
            ),
        )
        
        video = await generator.generate_video(request)
        
        print(f"   {video.get_summary()}")
        print(f"   Hook: \"{video.script.hook[:50]}...\"")
        print(f"   Hook Strength: {video.hook_strength}/100")
        print(f"   Avatar: {video.avatar.name}")
        print(f"   Music: {video.music_track.name if video.music_track else 'None'}")
        print(f"   Scenes: {len(video.script.scenes)}")
    
    print("\n📋 Available Avatars:")
    for avatar in generator.get_avatars():
        print(f"   • {avatar.name} ({avatar.style.value}) - {avatar.age_range}, {avatar.gender}")
    
    print("\n🎵 Available Music:")
    for track in generator.get_music_tracks():
        print(f"   • {track.name} ({track.mood}) - {track.bpm} BPM")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_video_generator())
