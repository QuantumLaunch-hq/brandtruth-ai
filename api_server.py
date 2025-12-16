#!/usr/bin/env python3
"""FastAPI backend for BrandTruth AI.

Endpoints:
- /pipeline/* - Pipeline orchestration
- /predict/* - Performance prediction (Slice 9)
- /attention/* - Attention heatmap (Slice 10)
- /export/* - Multi-format export (Slice 11)
- /intel/* - Competitor intelligence (Slice 12)
- /video/* - AI UGC Video (Slice 13)
- /fatigue/* - Creative fatigue (Slice 14)
- /proof/* - Proof pack (Slice 15)
- /meta/* - Meta publishing (Slice 8)
- /sentiment/* - Sentiment monitoring (Slice 6)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.extractors.brand_extractor import extract_brand
from src.generators.copy_generator import generate_copy
from src.composers.image_matcher_v2 import match_images_v2
from src.composers.ad_composer import compose_ads
from src.models.copy_variant import Platform
from src.models.composed_ad import AdFormat
from src.extractors.sentiment_monitor import (
    SentimentMonitor, SentimentMonitorConfig, create_mock_mentions,
)
from src.models.sentiment import AutoPauseRule
from src.pipeline.orchestrator import (
    PipelineOrchestrator, PipelineConfig, PipelineStage,
)
from src.connectors.meta_connector import (
    get_meta_connector, TargetingSpec,
)
from src.analyzers.performance_predictor import (
    get_predictor, AdToAnalyze,
)
from src.analyzers.attention_analyzer import (
    get_attention_analyzer,
)
from src.composers.format_exporter import (
    FormatExporter, ExportConfig, ExportFormat, get_format_catalog,
)
from src.analyzers.fatigue_predictor import (
    get_fatigue_predictor, AdPerformanceData,
)
from src.generators.proof_pack import (
    get_proof_pack_generator,
)
from src.analyzers.competitor_intel import (
    get_competitor_intel_analyzer,
)
from src.generators.video_generator import (
    get_video_generator, VideoGenerationRequest, VideoConfig,
    VideoStyle, AspectRatio, AvatarStyle, VoiceTone,
)
from src.generators.hook_generator import (
    get_hook_generator, HookGeneratorRequest,
)
from src.analyzers.landing_page_analyzer import (
    get_landing_page_analyzer, LandingPageRequest,
)
from src.analyzers.budget_simulator import (
    get_budget_simulator, BudgetRequest, Industry, CampaignGoal,
)
from src.analyzers.platform_recommender import (
    get_platform_recommender, PlatformRequest, ProductType, AudienceType,
)
from src.analyzers.ab_test_planner import (
    get_ab_test_planner, ABTestRequest,
)
from src.analyzers.audience_targeting import (
    get_audience_targeting, AudienceRequest,
)
from src.analyzers.iteration_assistant import (
    get_iteration_assistant, IterationRequest,
)
from src.extractors.social_proof_collector import (
    get_social_proof_collector, ProofRequest,
)

# Optional Temporal workflow routes (graceful fallback if Temporal not available)
try:
    from src.temporal.routes import router as temporal_router
    TEMPORAL_AVAILABLE = True
except ImportError:
    TEMPORAL_AVAILABLE = False
    temporal_router = None

app = FastAPI(
    title="BrandTruth AI API",
    description="AI-powered ad generation with video creation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3010",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3010",
        "http://192.168.8.145:3000",
        "http://192.168.8.145:3001",
        "http://192.168.8.145:3010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

# Include Temporal workflow routes if available
if TEMPORAL_AVAILABLE and temporal_router:
    app.include_router(temporal_router, prefix="/workflow", tags=["Temporal Workflows"])

orchestrator = PipelineOrchestrator(jobs_dir="./jobs")
sentiment_monitors: dict[str, SentimentMonitor] = {}
_instances: dict = {}

def get_instance(name: str, factory):
    if name not in _instances:
        _instances[name] = factory()
    return _instances[name]


# =============================================================================
# REQUEST MODELS
# =============================================================================

class PipelineRequest(BaseModel):
    url: str
    num_variants: int = 5
    platform: str = "meta"
    formats: list[str] = ["square"]

class PredictRequest(BaseModel):
    headline: str
    primary_text: str
    cta: str

class AttentionRequest(BaseModel):
    image_url: Optional[str] = None
    headline: Optional[str] = None
    cta: Optional[str] = None

class ExportRequest(BaseModel):
    image_url: str
    headline: str
    cta: str = "Learn More"
    formats: Optional[list[str]] = None
    create_zip: bool = True

class FatigueRequest(BaseModel):
    ad_id: str
    days_running: int = 14
    frequency: float = 2.5
    reach: int = 20000
    audience_size: int = 100000
    industry: str = "general"

class ProofPackRequest(BaseModel):
    ad_id: str
    campaign_name: str
    brand_name: str
    headline: str
    primary_text: str
    cta: str = "Learn More"
    claims: Optional[list[dict]] = None

class CompetitorIntelRequest(BaseModel):
    brand_name: str
    industry: str
    competitor_names: Optional[list[str]] = None

class VideoRequest(BaseModel):
    """Request for AI video generation."""
    brand_name: str
    product_description: str
    target_audience: str
    key_benefits: list[str]
    cta: str = "Learn More"
    style: str = "ugc"
    aspect_ratio: str = "9:16"
    avatar_style: str = "casual"
    include_captions: bool = True
    include_music: bool = True
    custom_script: Optional[str] = None

class MetaPublishRequest(BaseModel):
    headline: str
    primary_text: str
    cta: str = "Learn More"
    link_url: str
    page_id: str = "demo_page"
    campaign_name: str = "BrandTruth Campaign"
    daily_budget: int = 1000

class SentimentCheckRequest(BaseModel):
    brand_name: str
    scenario: str = "normal"


# =============================================================================
# ROOT & HEALTH
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "BrandTruth AI API",
        "version": "1.0.0",
        "status": "100% Complete - All 15 Slices!",
        "endpoints": {
            "pipeline": "/pipeline/run",
            "predict": "/predict",
            "attention": "/attention/analyze",
            "export": "/export/all",
            "intel": "/intel/analyze",
            "video": "/video/generate",
            "fatigue": "/fatigue/predict",
            "proof": "/proof/generate",
            "meta": "/meta/publish",
            "sentiment": "/sentiment/check",
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "temporal_available": TEMPORAL_AVAILABLE,
    }


# =============================================================================
# AI VIDEO GENERATION ENDPOINTS (Slice 13)
# =============================================================================

@app.post("/video/generate")
async def generate_video(request: VideoRequest):
    """
    Generate AI UGC-style video ad.
    
    Returns:
    - Video metadata and URLs
    - Generated script with scenes
    - Engagement predictions
    - Avatar and music info
    """
    generator = get_instance("video", get_video_generator)
    
    # Map string values to enums
    style_map = {s.value: s for s in VideoStyle}
    aspect_map = {a.value: a for a in AspectRatio}
    avatar_map = {a.value: a for a in AvatarStyle}
    
    config = VideoConfig(
        style=style_map.get(request.style, VideoStyle.UGC),
        aspect_ratio=aspect_map.get(request.aspect_ratio, AspectRatio.VERTICAL),
        avatar_style=avatar_map.get(request.avatar_style, AvatarStyle.CASUAL),
        include_captions=request.include_captions,
        include_music=request.include_music,
    )
    
    gen_request = VideoGenerationRequest(
        brand_name=request.brand_name,
        product_description=request.product_description,
        target_audience=request.target_audience,
        key_benefits=request.key_benefits,
        cta=request.cta,
        config=config,
        custom_script=request.custom_script,
    )
    
    video = await generator.generate_video(gen_request)
    
    return {
        "video_id": video.video_id,
        "title": video.title,
        "status": video.status.value,
        "summary": video.get_summary(),
        "video_url": video.video_url,
        "thumbnail_url": video.thumbnail_url,
        "duration_seconds": video.duration_seconds,
        "resolution": video.resolution,
        "file_size_mb": video.file_size_mb,
        "script": {
            "hook": video.script.hook,
            "body": video.script.body,
            "cta": video.script.cta,
            "full_script": video.script.get_full_script(),
            "scenes": [
                {
                    "number": s.scene_number,
                    "duration": s.duration_seconds,
                    "text": s.script_text,
                    "visual": s.visual_type,
                }
                for s in video.script.scenes
            ],
        },
        "avatar": {
            "id": video.avatar.avatar_id,
            "name": video.avatar.name,
            "style": video.avatar.style.value,
        } if video.avatar else None,
        "music": {
            "name": video.music_track.name,
            "mood": video.music_track.mood,
            "bpm": video.music_track.bpm,
        } if video.music_track else None,
        "predictions": {
            "engagement_score": video.predicted_engagement_score,
            "hook_strength": video.hook_strength,
        },
    }


@app.post("/video/demo/{style}")
async def video_demo(style: str):
    """Generate demo video for a style."""
    valid_styles = ["ugc", "testimonial", "demo", "explainer", "storytelling", "listicle"]
    if style not in valid_styles:
        raise HTTPException(status_code=400, detail=f"Style must be: {', '.join(valid_styles)}")
    
    generator = get_instance("video", get_video_generator)
    
    style_enum = VideoStyle(style)
    config = VideoConfig(style=style_enum, aspect_ratio=AspectRatio.VERTICAL)
    
    request = VideoGenerationRequest(
        brand_name="Careerfied",
        product_description="AI-powered resume builder",
        target_audience="Job seekers",
        key_benefits=["ATS-optimized", "Industry templates", "Real-time feedback"],
        cta="Get Started Free",
        config=config,
    )
    
    video = await generator.generate_video(request)
    
    return {
        "demo": True,
        "style": style,
        "video_id": video.video_id,
        "summary": video.get_summary(),
        "hook": video.script.hook,
        "engagement_score": video.predicted_engagement_score,
        "hook_strength": video.hook_strength,
        "duration_seconds": video.duration_seconds,
    }


@app.get("/video/styles")
async def get_video_styles():
    """Get available video styles."""
    generator = get_instance("video", get_video_generator)
    return {"styles": generator.get_video_styles()}


@app.get("/video/avatars")
async def get_avatars():
    """Get available AI avatars."""
    generator = get_instance("video", get_video_generator)
    avatars = generator.get_avatars()
    return {
        "avatars": [
            {
                "id": a.avatar_id,
                "name": a.name,
                "gender": a.gender,
                "age_range": a.age_range,
                "style": a.style.value,
                "preview_url": a.preview_url,
            }
            for a in avatars
        ]
    }


@app.get("/video/music")
async def get_music_tracks():
    """Get available music tracks."""
    generator = get_instance("video", get_video_generator)
    tracks = generator.get_music_tracks()
    return {
        "tracks": [
            {
                "id": t.track_id,
                "name": t.name,
                "genre": t.genre,
                "mood": t.mood,
                "bpm": t.bpm,
            }
            for t in tracks
        ]
    }


# =============================================================================
# COMPETITOR INTELLIGENCE (Slice 12)
# =============================================================================

@app.post("/intel/analyze")
async def analyze_competitors(request: CompetitorIntelRequest):
    analyzer = get_instance("intel", get_competitor_intel_analyzer)
    analysis = await analyzer.analyze_competitors(
        brand_name=request.brand_name, industry=request.industry,
        competitor_names=request.competitor_names,
    )
    return {
        "summary": analysis.get_summary(),
        "competitors": [{"name": c.page_name, "ads": c.total_ads, "spend": c.estimated_monthly_spend, "threat": c.threat_level.value} for c in analysis.competitors],
        "copy_patterns": [{"type": p.pattern_type, "frequency": p.frequency} for p in analysis.industry_copy_patterns],
        "insights": [{"title": i.title, "action": i.action} for i in analysis.insights],
        "recommendations": analysis.recommendations,
    }


@app.post("/intel/demo/{industry}")
async def intel_demo(industry: str):
    if industry not in ["career", "saas", "ecommerce"]:
        raise HTTPException(status_code=400, detail="Industry must be: career, saas, ecommerce")
    analyzer = get_instance("intel", get_competitor_intel_analyzer)
    analysis = await analyzer.analyze_competitors(brand_name="Demo", industry=industry)
    return {"demo": True, "industry": industry, "summary": analysis.get_summary(), "competitors": len(analysis.competitors)}


# =============================================================================
# PROOF PACK (Slice 15)
# =============================================================================

@app.post("/proof/generate")
async def generate_proof_pack(request: ProofPackRequest):
    generator = get_instance("proof", get_proof_pack_generator)
    pack = await generator.generate(
        ad_id=request.ad_id, campaign_name=request.campaign_name, brand_name=request.brand_name,
        headline=request.headline, primary_text=request.primary_text, cta=request.cta, claims=request.claims,
    )
    return {"pack_id": pack.pack_id, "summary": pack.get_summary(), "compliance": pack.overall_compliance.value, "safety_score": pack.brand_safety_score, "action_items": pack.action_items}


@app.post("/proof/demo")
async def proof_demo():
    generator = get_instance("proof", get_proof_pack_generator)
    pack = await generator.generate(ad_id="demo", campaign_name="Demo", brand_name="Careerfied", headline="Stop Getting Rejected", primary_text="Build resumes.", cta="Get Started")
    return {"demo": True, "summary": pack.get_summary(), "safety_score": pack.brand_safety_score}


# =============================================================================
# FATIGUE (Slice 14)
# =============================================================================

@app.post("/fatigue/predict")
async def predict_fatigue(request: FatigueRequest):
    predictor = get_instance("fatigue", get_fatigue_predictor)
    data = AdPerformanceData(
        ad_id=request.ad_id, start_date=datetime.utcnow() - timedelta(days=request.days_running),
        days_running=request.days_running, frequency=request.frequency, reach=request.reach,
        audience_size=request.audience_size, industry=request.industry,
        ctr_history=[max(0.5, 2.0 * (0.97 ** i)) for i in range(request.days_running)],
        cpm_history=[10.0 * (1.02 ** i) for i in range(request.days_running)],
    )
    prediction = await predictor.predict(data)
    return {"fatigue_score": prediction.fatigue_score, "level": prediction.fatigue_level.value, "summary": prediction.get_summary(), "days_until": prediction.days_until_fatigue, "recommendations": prediction.recommendations}


@app.post("/fatigue/demo/{scenario}")
async def fatigue_demo(scenario: str):
    scenarios = {"fresh": (3, 1.2), "healthy": (10, 2.0), "moderate": (18, 3.0), "high": (25, 4.0), "critical": (35, 5.5)}
    if scenario not in scenarios:
        raise HTTPException(status_code=400, detail=f"Scenario: {', '.join(scenarios.keys())}")
    days, freq = scenarios[scenario]
    predictor = get_instance("fatigue", get_fatigue_predictor)
    data = AdPerformanceData(ad_id=f"demo_{scenario}", start_date=datetime.utcnow() - timedelta(days=days), days_running=days, frequency=freq, reach=days*3000, audience_size=150000, ctr_history=[max(0.5,2.0*(0.97**i)) for i in range(days)], cpm_history=[10.0*(1.02**i) for i in range(days)], industry="saas")
    prediction = await predictor.predict(data)
    return {"demo": True, "scenario": scenario, "fatigue_score": prediction.fatigue_score, "summary": prediction.get_summary()}


# =============================================================================
# EXPORT (Slice 11)
# =============================================================================

@app.get("/export/formats")
async def get_formats():
    return {"formats": get_format_catalog(), "total": len(get_format_catalog())}


@app.post("/export/all")
async def export_all(request: ExportRequest):
    config = ExportConfig(output_dir="./output", create_zip=request.create_zip)
    if request.formats:
        config.formats = [ExportFormat(f) for f in request.formats]
    exporter = FormatExporter(config)
    result = await exporter.export_all(source_image_url=request.image_url, headline=request.headline, cta=request.cta)
    return {"success": result.success, "exported": len(result.formats_exported), "zip": f"/output/{Path(result.zip_path).name}" if result.zip_path else None}


@app.post("/export/demo")
async def export_demo():
    exporter = FormatExporter(ExportConfig(output_dir="./output", create_zip=True))
    result = await exporter.export_all(source_image_url="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=1200", headline="Demo Ad", cta="Get Started")
    return {"demo": True, "exported": len(result.formats_exported)}


# =============================================================================
# ATTENTION (Slice 10)
# =============================================================================

@app.post("/attention/analyze")
async def analyze_attention(request: AttentionRequest):
    analyzer = get_instance("attention", get_attention_analyzer)
    ad_context = {"headline": request.headline, "cta": request.cta} if request.headline else None
    analysis = await analyzer.analyze(image_url=request.image_url, ad_context=ad_context)
    return {"score": analysis.overall_score, "summary": analysis.get_summary(), "first_focus": analysis.first_focus_element, "recommendations": analysis.recommendations}


@app.post("/attention/demo")
async def attention_demo():
    analyzer = get_instance("attention", get_attention_analyzer)
    analysis = await analyzer.analyze(image_url="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=600", ad_context={"headline": "Demo", "cta": "Get Started"})
    return {"demo": True, "score": analysis.overall_score, "summary": analysis.get_summary()}


# =============================================================================
# PREDICT (Slice 9)
# =============================================================================

@app.post("/predict")
async def predict(request: PredictRequest):
    predictor = get_instance("predictor", get_predictor)
    ad = AdToAnalyze(headline=request.headline, primary_text=request.primary_text, cta=request.cta)
    prediction = await predictor.predict(ad)
    return {"score": prediction.overall_score, "tier": prediction.performance_tier.value, "summary": prediction.get_summary()}


@app.post("/predict/demo")
async def predict_demo():
    predictor = get_instance("predictor", get_predictor)
    ad = AdToAnalyze(headline="Stop Getting Rejected", primary_text="Build resumes.", cta="Get Started")
    prediction = await predictor.predict(ad)
    return {"demo": True, "score": prediction.overall_score, "summary": prediction.get_summary()}


# =============================================================================
# PIPELINE (Slice 7)
# =============================================================================

@app.post("/pipeline/run")
async def run_pipeline(request: PipelineRequest):
    """Run the full ad generation pipeline.
    
    Returns complete result including brand_profile, copy_variants, 
    image_matches, composed_ads, and sentiment data.
    """
    format_map = {"square": AdFormat.SQUARE, "portrait": AdFormat.PORTRAIT, "landscape": AdFormat.LANDSCAPE}
    config = PipelineConfig(url=request.url, num_variants=request.num_variants, platform=Platform(request.platform), formats=[format_map.get(f, AdFormat.SQUARE) for f in request.formats])
    result = await orchestrator.run_pipeline(config)
    
    # Return full result for frontend
    return {
        "job_id": result.job_id,
        "stage": result.stage.value,
        "brand_profile": result.brand_profile,
        "copy_variants": result.copy_variants,
        "image_matches": result.image_matches,
        "composed_ads": result.composed_ads,
        "sentiment_snapshot": result.sentiment_snapshot,
        "sentiment_alerts": result.sentiment_alerts,
        "duration_seconds": result.duration_seconds,
        "error": result.error,
    }


@app.get("/jobs")
async def list_jobs(limit: int = 20):
    return {"jobs": orchestrator.list_jobs(limit=limit)}


# =============================================================================
# META (Slice 8)
# =============================================================================

@app.post("/meta/publish")
async def publish_meta(request: MetaPublishRequest):
    connector = get_instance("meta", get_meta_connector)
    result = await connector.publish_ad(headline=request.headline, primary_text=request.primary_text, cta=request.cta, link_url=request.link_url, page_id=request.page_id, campaign_name=request.campaign_name, daily_budget=request.daily_budget, start_paused=True)
    return {"success": result.success, "ad_id": result.ad_id}


@app.post("/meta/demo")
async def meta_demo():
    connector = get_instance("meta", get_meta_connector)
    result = await connector.publish_ad(headline="Demo", primary_text="Test", cta="Learn More", link_url="https://example.com", page_id="demo", campaign_name="Demo", daily_budget=1000, start_paused=True)
    return {"demo": True, "success": result.success}


# =============================================================================
# SENTIMENT (Slice 6)
# =============================================================================

@app.post("/sentiment/check")
async def check_sentiment(request: SentimentCheckRequest):
    if request.brand_name not in sentiment_monitors:
        config = SentimentMonitorConfig(brand_name=request.brand_name, auto_pause_rules=[AutoPauseRule(id=f"default_{request.brand_name}", brand_name=request.brand_name, min_sentiment_score=-0.4)])
        sentiment_monitors[request.brand_name] = SentimentMonitor(config)
    monitor = sentiment_monitors[request.brand_name]
    mentions = create_mock_mentions(request.brand_name, request.scenario)
    snapshot = await monitor.create_snapshot(mentions)
    should_pause, _ = monitor.evaluate_auto_pause(snapshot)
    return {"health": snapshot.get_health_status(), "auto_pause": should_pause}


@app.post("/sentiment/demo/{scenario}")
async def sentiment_demo(scenario: str):
    if scenario not in ["normal", "crisis", "positive"]:
        raise HTTPException(status_code=400, detail="Scenario: normal, crisis, positive")
    config = SentimentMonitorConfig(brand_name="Demo", auto_pause_rules=[AutoPauseRule(id="demo", brand_name="Demo", min_sentiment_score=-0.4)])
    monitor = SentimentMonitor(config)
    mentions = create_mock_mentions("Demo", scenario)
    snapshot = await monitor.create_snapshot(mentions)
    should_pause, _ = monitor.evaluate_auto_pause(snapshot)
    return {"demo": True, "scenario": scenario, "health": snapshot.get_health_status(), "auto_pause": should_pause}


# =============================================================================
# HOOK GENERATOR (Slice 16)
# =============================================================================

class HookRequest(BaseModel):
    product_name: str
    product_description: str
    target_audience: str
    pain_points: list[str] = []
    benefits: list[str] = []
    tone: str = "professional"
    include_emojis: bool = False
    num_hooks: int = 10


@app.post("/hooks/generate")
async def generate_hooks(request: HookRequest):
    generator = get_instance("hooks", get_hook_generator)
    req = HookGeneratorRequest(**request.model_dump())
    result = await generator.generate(req)
    return {
        "hooks": [{"text": h.text, "pattern": h.pattern.value, "score": h.score, "explanation": h.explanation} for h in result.hooks],
        "best_hook": result.best_hook.text if result.best_hook else None,
        "summary": result.get_summary(),
        "recommendations": result.recommendations,
    }


@app.get("/hooks/patterns")
async def get_hook_patterns():
    generator = get_instance("hooks", get_hook_generator)
    return {"patterns": generator.get_patterns(), "power_words": generator.get_power_words()}


@app.post("/hooks/demo")
async def hooks_demo():
    generator = get_instance("hooks", get_hook_generator)
    req = HookGeneratorRequest(
        product_name="Careerfied",
        product_description="AI-powered resume builder",
        target_audience="job seekers",
        pain_points=["getting rejected", "ATS systems"],
        benefits=["land more interviews", "stand out"],
    )
    result = await generator.generate(req)
    return {"demo": True, "summary": result.get_summary(), "hooks": [h.text for h in result.hooks[:5]]}


# =============================================================================
# LANDING PAGE ANALYZER (Slice 17)
# =============================================================================

class LandingRequest(BaseModel):
    landing_page_url: str
    ad_headline: str
    ad_primary_text: str
    ad_cta: str = "Learn More"


@app.post("/landing/analyze")
async def analyze_landing_page(request: LandingRequest):
    analyzer = get_instance("landing", get_landing_page_analyzer)
    req = LandingPageRequest(**request.model_dump())
    result = await analyzer.analyze(req)
    return {
        "url": result.url,
        "overall_score": result.overall_score,
        "message_match_score": result.message_match_score,
        "message_match_level": result.message_match_level.value,
        "above_fold_score": result.above_fold_score,
        "cta_score": result.cta_score,
        "mobile_score": result.mobile_score,
        "load_speed_score": result.load_speed_score,
        "issues": [{"category": i.category, "severity": i.severity, "message": i.message, "recommendation": i.recommendation} for i in result.issues],
        "recommendations": result.recommendations,
        "summary": result.get_summary(),
    }


@app.post("/landing/demo")
async def landing_demo():
    analyzer = get_instance("landing", get_landing_page_analyzer)
    req = LandingPageRequest(
        landing_page_url="https://careerfied.ai",
        ad_headline="Stop Getting Rejected",
        ad_primary_text="Build ATS-optimized resumes in minutes",
        ad_cta="Get Started Free",
    )
    result = await analyzer.analyze(req)
    return {"demo": True, "summary": result.get_summary(), "score": result.overall_score, "match_level": result.message_match_level.value}


# =============================================================================
# BUDGET SIMULATOR (Slice 18)
# =============================================================================

class BudgetSimRequest(BaseModel):
    industry: str = "saas"
    goal: str = "leads"
    product_price: float = 99.0
    target_monthly_conversions: int = 50
    target_cpa: Optional[float] = None


@app.post("/budget/simulate")
async def simulate_budget(request: BudgetSimRequest):
    simulator = get_instance("budget", get_budget_simulator)
    req = BudgetRequest(
        industry=Industry(request.industry),
        goal=CampaignGoal(request.goal),
        product_price=request.product_price,
        target_monthly_conversions=request.target_monthly_conversions,
        target_cpa=request.target_cpa,
    )
    result = await simulator.simulate(req)
    return {
        "daily_budget": result.daily_budget,
        "monthly_budget": result.monthly_budget,
        "tier": result.tier.value,
        "expected_impressions": result.expected_impressions,
        "expected_clicks": result.expected_clicks,
        "expected_conversions": result.expected_conversions,
        "expected_cpa": result.expected_cpa,
        "expected_roas": result.expected_roas,
        "break_even_days": result.break_even_days,
        "confidence_level": result.confidence_level,
        "recommendations": result.recommendations,
        "summary": result.get_summary(),
    }


@app.get("/budget/benchmarks")
async def get_benchmarks(industry: Optional[str] = None):
    simulator = get_instance("budget", get_budget_simulator)
    ind = Industry(industry) if industry else None
    return {"benchmarks": simulator.get_benchmarks(ind)}


@app.post("/budget/demo")
async def budget_demo():
    simulator = get_instance("budget", get_budget_simulator)
    req = BudgetRequest(industry=Industry.SAAS, goal=CampaignGoal.LEADS, product_price=99, target_monthly_conversions=50)
    result = await simulator.simulate(req)
    return {"demo": True, "summary": result.get_summary(), "daily_budget": result.daily_budget, "expected_cpa": result.expected_cpa}


# =============================================================================
# PLATFORM RECOMMENDER (Slice 19)
# =============================================================================

class PlatformRecRequest(BaseModel):
    product_type: str = "b2b_saas"
    audience_type: str = "founders"
    monthly_budget: float = 1000
    product_price: float = 99
    is_visual: bool = True


@app.post("/platforms/recommend")
async def recommend_platforms(request: PlatformRecRequest):
    recommender = get_instance("platforms", get_platform_recommender)
    req = PlatformRequest(
        product_type=ProductType(request.product_type),
        audience_type=AudienceType(request.audience_type),
        monthly_budget=request.monthly_budget,
        product_price=request.product_price,
        is_visual=request.is_visual,
    )
    result = await recommender.recommend(req)
    return {
        "primary_platform": result.primary_platform.value,
        "strategy": result.strategy,
        "budget_allocation": result.budget_allocation,
        "recommendations": [
            {
                "platform": r.platform.value,
                "score": r.score,
                "rank": r.rank,
                "min_budget": r.min_budget,
                "cpa_range": r.expected_cpa_range,
                "strengths": r.strengths,
                "best_formats": r.best_formats,
            }
            for r in result.recommendations[:5]
        ],
        "summary": result.get_summary(),
    }


@app.get("/platforms/list")
async def list_platforms():
    recommender = get_instance("platforms", get_platform_recommender)
    return {"platforms": recommender.get_platforms()}


@app.post("/platforms/demo")
async def platforms_demo():
    recommender = get_instance("platforms", get_platform_recommender)
    req = PlatformRequest(product_type=ProductType.B2B_SAAS, audience_type=AudienceType.FOUNDERS, monthly_budget=1000)
    result = await recommender.recommend(req)
    return {"demo": True, "summary": result.get_summary(), "primary": result.primary_platform.value, "strategy": result.strategy}


# =============================================================================
# A/B TEST PLANNER (Slice 20)
# =============================================================================

class ABTestPlanRequest(BaseModel):
    variants: list[dict]
    baseline_ctr: float = 1.0
    baseline_cvr: float = 2.0
    daily_budget: float = 50
    confidence_level: float = 0.95
    minimum_lift: float = 0.20


@app.post("/abtest/plan")
async def plan_ab_test(request: ABTestPlanRequest):
    planner = get_instance("abtest", get_ab_test_planner)
    req = ABTestRequest(**request.model_dump())
    result = await planner.plan(req)
    return {
        "test_pairs": [{"element": t.element.value, "variant_a": t.variant_a, "variant_b": t.variant_b, "hypothesis": t.hypothesis, "priority": t.priority.value, "expected_lift": t.expected_lift} for t in result.test_pairs],
        "required_sample_size": result.required_sample_size,
        "estimated_days": result.estimated_days,
        "daily_budget_needed": result.daily_budget_needed,
        "testing_sequence": result.testing_sequence,
        "recommendations": result.recommendations,
        "summary": result.get_summary(),
    }


@app.post("/abtest/calculate")
async def calculate_significance(control_conversions: int, control_visitors: int, variant_conversions: int, variant_visitors: int):
    planner = get_instance("abtest", get_ab_test_planner)
    return planner.calculate_significance(control_conversions, control_visitors, variant_conversions, variant_visitors)


@app.post("/abtest/demo")
async def abtest_demo():
    planner = get_instance("abtest", get_ab_test_planner)
    req = ABTestRequest(
        variants=[
            {"headline": "Stop Getting Rejected", "primary_text": "Build resumes fast", "cta": "Get Started"},
            {"headline": "Land More Interviews", "primary_text": "AI-powered resumes", "cta": "Try Free"},
        ],
        daily_budget=50,
    )
    result = await planner.plan(req)
    return {"demo": True, "summary": result.get_summary(), "estimated_days": result.estimated_days, "test_pairs": len(result.test_pairs)}


# =============================================================================
# AUDIENCE TARGETING (Slice 21)
# =============================================================================

class AudienceTargetRequest(BaseModel):
    product_name: str
    product_description: str
    product_type: str = "saas"
    target_persona: str
    price_point: float = 99
    existing_customers: bool = False
    website_traffic: bool = False


@app.post("/audience/suggest")
async def suggest_audiences(request: AudienceTargetRequest):
    targeting = get_instance("audience", get_audience_targeting)
    req = AudienceRequest(**request.model_dump())
    result = await targeting.suggest(req)
    return {
        "primary_audiences": [{"name": a.name, "type": a.type.value, "estimated_size": a.estimated_size, "relevance_score": a.relevance_score, "targeting_tips": a.targeting_tips} for a in result.primary_audiences],
        "secondary_audiences": [{"name": a.name, "type": a.type.value, "estimated_size": a.estimated_size, "relevance_score": a.relevance_score} for a in result.secondary_audiences],
        "exclusions": [{"name": e.name, "reason": e.reason, "impact": e.impact} for e in result.exclusions],
        "lookalike_strategy": result.lookalike_strategy,
        "budget_allocation": result.budget_allocation,
        "testing_order": result.testing_order,
        "recommendations": result.recommendations,
        "summary": result.get_summary(),
    }


@app.post("/audience/demo")
async def audience_demo():
    targeting = get_instance("audience", get_audience_targeting)
    req = AudienceRequest(
        product_name="Careerfied",
        product_description="AI-powered resume builder for job seekers",
        target_persona="Job seekers and career changers",
        price_point=29,
    )
    result = await targeting.suggest(req)
    return {"demo": True, "summary": result.get_summary(), "primary_count": len(result.primary_audiences), "exclusions": len(result.exclusions)}


# =============================================================================
# ITERATION ASSISTANT (Slice 22)
# =============================================================================

class IterateRequest(BaseModel):
    headline: str
    primary_text: str
    cta: str
    current_ctr: float = 0.8
    current_cvr: float = 1.5
    current_cpa: float = 80
    target_cpa: float = 50
    impressions: int = 10000
    frequency: float = 2.0
    days_running: int = 7


@app.post("/iterate/analyze")
async def analyze_for_iteration(request: IterateRequest):
    assistant = get_instance("iterate", get_iteration_assistant)
    req = IterationRequest(**request.model_dump())
    result = await assistant.analyze(req)
    return {
        "diagnoses": [{"issue": d.issue.value, "severity": d.severity.value, "description": d.description, "likely_cause": d.likely_cause, "impact": d.impact} for d in result.diagnoses],
        "improved_variants": [{"element": v.element, "original": v.original, "improved": v.improved, "rationale": v.rationale, "expected_improvement": v.expected_improvement} for v in result.improved_variants],
        "priority_fixes": result.priority_fixes,
        "testing_roadmap": result.testing_roadmap,
        "quick_wins": result.quick_wins,
        "estimated_improvement": result.estimated_improvement,
        "summary": result.get_summary(),
    }


@app.post("/iterate/demo")
async def iterate_demo():
    assistant = get_instance("iterate", get_iteration_assistant)
    req = IterationRequest(
        headline="Check out our product",
        primary_text="We have a great product that you should try.",
        cta="Learn More",
        current_ctr=0.5,
        current_cvr=1.0,
        current_cpa=120,
        target_cpa=50,
    )
    result = await assistant.analyze(req)
    return {"demo": True, "summary": result.get_summary(), "diagnoses": len(result.diagnoses), "improvements": len(result.improved_variants)}


# =============================================================================
# SOCIAL PROOF COLLECTOR (Slice 23)
# =============================================================================

class SocialProofRequest(BaseModel):
    brand_name: str
    brand_url: str
    product_description: str
    existing_testimonials: list[str] = []
    user_count: Optional[int] = None
    rating: Optional[float] = None
    notable_customers: list[str] = []


@app.post("/social/collect")
async def collect_social_proof(request: SocialProofRequest):
    collector = get_instance("social", get_social_proof_collector)
    req = ProofRequest(**request.model_dump())
    result = await collector.collect(req)
    return {
        "proofs": [{"type": p.type.value, "content": p.content, "source": p.source, "ad_ready": p.ad_ready, "verified": p.verified} for p in result.proofs],
        "best_testimonial": result.best_testimonial.ad_ready if result.best_testimonial else None,
        "best_stat": result.best_stat.ad_ready if result.best_stat else None,
        "ad_snippets": result.ad_snippets,
        "trust_score": result.trust_score,
        "recommendations": result.recommendations,
        "summary": result.get_summary(),
    }


@app.post("/social/demo")
async def social_demo():
    collector = get_instance("social", get_social_proof_collector)
    req = ProofRequest(
        brand_name="Careerfied",
        brand_url="https://careerfied.ai",
        product_description="AI-powered resume builder",
        existing_testimonials=["This helped me land my dream job!", "Got 3 interviews in the first week"],
        user_count=1500,
        rating=4.8,
        notable_customers=["Google", "Meta", "Microsoft"],
    )
    result = await collector.collect(req)
    return {"demo": True, "summary": result.get_summary(), "trust_score": result.trust_score, "snippets": result.ad_snippets[:3]}


# =============================================================================
# STATIC FILES
# =============================================================================

@app.get("/output/{filename}")
async def get_file(filename: str):
    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    BRANDTRUTH AI API                        ║
║                      Version 1.0.0                          ║
║               🎉 100% COMPLETE - ALL 15 SLICES! 🎉          ║
╠══════════════════════════════════════════════════════════════╣
║  Server: http://localhost:{args.port}                            ║
║  Docs:   http://localhost:{args.port}/docs                       ║
╠══════════════════════════════════════════════════════════════╣
║  AI VIDEO (Slice 13) - NEW!                                 ║
║    POST /video/generate     - Generate AI video ad          ║
║    POST /video/demo/:style  - Demo (ugc/testimonial/etc)    ║
║    GET  /video/styles       - Available styles              ║
║    GET  /video/avatars      - Available avatars             ║
║    GET  /video/music        - Available music               ║
╠══════════════════════════════════════════════════════════════╣
║  INTEL (12) | PROOF (15) | FATIGUE (14) | EXPORT (11):      ║
║    /intel/analyze | /proof/generate | /fatigue/predict      ║
╠══════════════════════════════════════════════════════════════╣
║  ATTENTION (10) | PREDICT (9) | PIPELINE (7) | META (8):    ║
║    /attention/analyze | /predict | /pipeline/run | /meta    ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run(app, host=args.host, port=args.port)
