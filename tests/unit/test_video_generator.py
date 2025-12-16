# tests/unit/test_video_generator.py
"""Unit tests for Video Generator (Slice 13)."""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generators.video_generator import (
    VideoGenerator,
    VideoGenerationRequest,
    VideoConfig,
    GeneratedVideo,
    VideoScript,
    VideoScene,
    Avatar,
    MusicTrack,
    VideoStyle,
    AspectRatio,
    AvatarStyle,
    VoiceTone,
    VideoStatus,
    get_video_generator,
)


class TestVideoStyle:
    """Tests for VideoStyle enum."""
    
    def test_all_styles_exist(self):
        """Test all video styles exist."""
        assert VideoStyle.UGC.value == "ugc"
        assert VideoStyle.TESTIMONIAL.value == "testimonial"
        assert VideoStyle.DEMO.value == "demo"
        assert VideoStyle.EXPLAINER.value == "explainer"
        assert VideoStyle.STORYTELLING.value == "storytelling"
        assert VideoStyle.LISTICLE.value == "listicle"


class TestAspectRatio:
    """Tests for AspectRatio enum."""
    
    def test_all_ratios_exist(self):
        """Test all aspect ratios exist."""
        assert AspectRatio.VERTICAL.value == "9:16"
        assert AspectRatio.SQUARE.value == "1:1"
        assert AspectRatio.HORIZONTAL.value == "16:9"


class TestVideoConfig:
    """Tests for VideoConfig model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = VideoConfig()
        
        assert config.style == VideoStyle.UGC
        assert config.aspect_ratio == AspectRatio.VERTICAL
        assert config.avatar_style == AvatarStyle.CASUAL
        assert config.include_captions is True
        assert config.include_music is True
        assert config.max_duration_seconds == 60
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = VideoConfig(
            style=VideoStyle.TESTIMONIAL,
            aspect_ratio=AspectRatio.SQUARE,
            avatar_style=AvatarStyle.PROFESSIONAL,
            include_captions=False,
            max_duration_seconds=30,
        )
        
        assert config.style == VideoStyle.TESTIMONIAL
        assert config.aspect_ratio == AspectRatio.SQUARE
        assert config.include_captions is False


class TestVideoGenerationRequest:
    """Tests for VideoGenerationRequest model."""
    
    def test_create_request(self):
        """Test creating generation request."""
        request = VideoGenerationRequest(
            brand_name="Careerfied",
            product_description="AI resume builder",
            target_audience="Job seekers",
            key_benefits=["ATS-optimized", "Templates", "Feedback"],
            cta="Get Started",
        )
        
        assert request.brand_name == "Careerfied"
        assert len(request.key_benefits) == 3
        assert request.config.style == VideoStyle.UGC  # default
    
    def test_request_with_custom_config(self):
        """Test request with custom config."""
        config = VideoConfig(style=VideoStyle.DEMO)
        request = VideoGenerationRequest(
            brand_name="Test",
            product_description="Test product",
            target_audience="Test audience",
            key_benefits=["Benefit 1"],
            config=config,
        )
        
        assert request.config.style == VideoStyle.DEMO


class TestVideoScript:
    """Tests for VideoScript model."""
    
    def test_create_script(self):
        """Test creating video script."""
        script = VideoScript(
            script_id="script_001",
            title="Test Script",
            hook="POV: You just discovered something amazing",
            body=["Point 1", "Point 2", "Point 3"],
            cta="Link in bio!",
            total_duration_seconds=30,
        )
        
        assert script.hook.startswith("POV")
        assert len(script.body) == 3
    
    def test_get_full_script(self):
        """Test full script generation."""
        script = VideoScript(
            script_id="script_001",
            title="Test Script",
            hook="Hook text",
            body=["Body 1", "Body 2"],
            cta="CTA text",
            total_duration_seconds=30,
        )
        
        full = script.get_full_script()
        
        assert "Hook text" in full
        assert "Body 1" in full
        assert "CTA text" in full


class TestAvatar:
    """Tests for Avatar model."""
    
    def test_create_avatar(self):
        """Test creating avatar."""
        avatar = Avatar(
            avatar_id="avatar_test",
            name="Test Avatar",
            gender="female",
            age_range="25-35",
            ethnicity="caucasian",
            style=AvatarStyle.FRIENDLY,
            preview_url="/avatars/test.jpg",
        )
        
        assert avatar.name == "Test Avatar"
        assert avatar.style == AvatarStyle.FRIENDLY


class TestMusicTrack:
    """Tests for MusicTrack model."""
    
    def test_create_track(self):
        """Test creating music track."""
        track = MusicTrack(
            track_id="track_test",
            name="Test Track",
            genre="electronic",
            mood="energetic",
            duration_seconds=120,
            bpm=128,
        )
        
        assert track.mood == "energetic"
        assert track.bpm == 128


class TestVideoGenerator:
    """Tests for VideoGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return VideoGenerator()
    
    @pytest.mark.asyncio
    async def test_generate_ugc_video(self, generator):
        """Test generating UGC style video."""
        request = VideoGenerationRequest(
            brand_name="Careerfied",
            product_description="AI resume builder",
            target_audience="Job seekers",
            key_benefits=["ATS-optimized", "Templates", "Feedback"],
            cta="Get Started",
            config=VideoConfig(style=VideoStyle.UGC),
        )
        
        video = await generator.generate_video(request)
        
        assert isinstance(video, GeneratedVideo)
        assert video.status == VideoStatus.COMPLETE
        assert video.style == VideoStyle.UGC
        assert "POV" in video.script.hook or "discovered" in video.script.hook.lower()
    
    @pytest.mark.asyncio
    async def test_generate_testimonial_video(self, generator):
        """Test generating testimonial style video."""
        request = VideoGenerationRequest(
            brand_name="Test Brand",
            product_description="Test product",
            target_audience="Test audience",
            key_benefits=["Benefit 1", "Benefit 2"],
            cta="Try Now",
            config=VideoConfig(style=VideoStyle.TESTIMONIAL),
        )
        
        video = await generator.generate_video(request)
        
        assert video.style == VideoStyle.TESTIMONIAL
        assert "thought" in video.script.hook.lower() or "impressed" in video.script.body[0].lower() if video.script.body else True
    
    @pytest.mark.asyncio
    async def test_generate_listicle_video(self, generator):
        """Test generating listicle style video."""
        request = VideoGenerationRequest(
            brand_name="Test Brand",
            product_description="Test product",
            target_audience="Test audience",
            key_benefits=["Benefit 1", "Benefit 2", "Benefit 3"],
            cta="Check it out",
            config=VideoConfig(style=VideoStyle.LISTICLE),
        )
        
        video = await generator.generate_video(request)
        
        assert video.style == VideoStyle.LISTICLE
        # Listicle should have numbered points
        assert any("number" in point.lower() or "1" in point or "2" in point for point in video.script.body)
    
    @pytest.mark.asyncio
    async def test_video_has_scenes(self, generator):
        """Test that video has scene breakdown."""
        request = VideoGenerationRequest(
            brand_name="Test",
            product_description="Test",
            target_audience="Test",
            key_benefits=["A", "B", "C"],
            cta="CTA",
        )
        
        video = await generator.generate_video(request)
        
        assert len(video.script.scenes) > 0
        
        # First scene should be hook
        assert video.script.scenes[0].scene_number == 1
        
        # Last scene should be CTA
        last_scene = video.script.scenes[-1]
        assert "cta" in last_scene.script_text.lower() or last_scene.visual_type == "text-overlay"
    
    @pytest.mark.asyncio
    async def test_video_has_avatar(self, generator):
        """Test that video has avatar assigned."""
        request = VideoGenerationRequest(
            brand_name="Test",
            product_description="Test",
            target_audience="Test",
            key_benefits=["A"],
            cta="CTA",
            config=VideoConfig(avatar_style=AvatarStyle.PROFESSIONAL),
        )
        
        video = await generator.generate_video(request)
        
        assert video.avatar is not None
        assert video.avatar.name
    
    @pytest.mark.asyncio
    async def test_video_has_music(self, generator):
        """Test that video has music when enabled."""
        request = VideoGenerationRequest(
            brand_name="Test",
            product_description="Test",
            target_audience="Test",
            key_benefits=["A"],
            cta="CTA",
            config=VideoConfig(include_music=True),
        )
        
        video = await generator.generate_video(request)
        
        assert video.music_track is not None
        assert video.music_track.mood
    
    @pytest.mark.asyncio
    async def test_video_no_music_when_disabled(self, generator):
        """Test that video has no music when disabled."""
        request = VideoGenerationRequest(
            brand_name="Test",
            product_description="Test",
            target_audience="Test",
            key_benefits=["A"],
            cta="CTA",
            config=VideoConfig(include_music=False),
        )
        
        video = await generator.generate_video(request)
        
        assert video.music_track is None
    
    @pytest.mark.asyncio
    async def test_video_has_engagement_prediction(self, generator):
        """Test that video has engagement prediction."""
        request = VideoGenerationRequest(
            brand_name="Test",
            product_description="Test",
            target_audience="Test",
            key_benefits=["A", "B", "C"],
            cta="CTA",
        )
        
        video = await generator.generate_video(request)
        
        assert 0 <= video.predicted_engagement_score <= 100
        assert 0 <= video.hook_strength <= 100
    
    @pytest.mark.asyncio
    async def test_custom_script(self, generator):
        """Test video with custom script."""
        custom_script = """POV: You just found the secret
It's called Careerfied
And it changed everything
Link in bio!"""
        
        request = VideoGenerationRequest(
            brand_name="Careerfied",
            product_description="Test",
            target_audience="Test",
            key_benefits=["A"],
            cta="CTA",
            custom_script=custom_script,
        )
        
        video = await generator.generate_video(request)
        
        assert "POV" in video.script.hook
    
    def test_get_avatars(self, generator):
        """Test getting available avatars."""
        avatars = generator.get_avatars()
        
        assert len(avatars) >= 5
        assert all(isinstance(a, Avatar) for a in avatars)
    
    def test_get_music_tracks(self, generator):
        """Test getting available music tracks."""
        tracks = generator.get_music_tracks()
        
        assert len(tracks) >= 5
        assert all(isinstance(t, MusicTrack) for t in tracks)
    
    def test_get_video_styles(self, generator):
        """Test getting available video styles."""
        styles = generator.get_video_styles()
        
        assert len(styles) == 6
        assert all("id" in s and "name" in s and "description" in s for s in styles)


class TestGeneratedVideo:
    """Tests for GeneratedVideo model."""
    
    def test_get_summary(self):
        """Test summary generation."""
        video = GeneratedVideo(
            video_id="vid_test",
            title="Test Video",
            status=VideoStatus.COMPLETE,
            style=VideoStyle.UGC,
            aspect_ratio=AspectRatio.VERTICAL,
            duration_seconds=30,
            script=VideoScript(
                script_id="script_test",
                title="Test",
                hook="Hook",
                body=["Body"],
                cta="CTA",
                total_duration_seconds=30,
            ),
            predicted_engagement_score=75,
            hook_strength=80,
        )
        
        summary = video.get_summary()
        
        assert "Test Video" in summary
        assert "ugc" in summary.lower()
        assert "75" in summary


class TestGetVideoGenerator:
    """Tests for factory function."""
    
    def test_returns_generator(self):
        """Test factory returns generator."""
        generator = get_video_generator()
        assert generator is not None
        assert hasattr(generator, "generate_video")
