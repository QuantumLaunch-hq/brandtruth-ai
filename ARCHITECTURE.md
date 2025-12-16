# BrandTruth AI - Architecture Documentation

## System Overview

BrandTruth AI is a modular, AI-native advertising platform built with Python (FastAPI) backend and Next.js frontend. The architecture follows a pipeline-based design pattern with clear separation of concerns.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │                     Next.js 14 Frontend                             │    │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │    │
│   │  │ Dashboard│ │  Predict │ │ Attention│ │   Video  │ │   Intel  │ │    │
│   │  │ (HITL)   │ │  (Score) │ │ (Heatmap)│ │   (UGC)  │ │  (Spy)   │ │    │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │    │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │    │
│   │  │  Export  │ │  Fatigue │ │   Proof  │ │Sentiment │ │  Publish │ │    │
│   │  │ (Formats)│ │ (Refresh)│ │(Complian)│ │ (Crisis) │ │  (Meta)  │ │    │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ HTTP/REST                               │
│                                    ▼                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                              API LAYER                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │                    FastAPI Application (v1.0.0)                     │    │
│   │                                                                     │    │
│   │  ┌─────────────────────────────────────────────────────────────┐   │    │
│   │  │                      Middleware                              │   │    │
│   │  │  • CORS (localhost:3000, 3001)                              │   │    │
│   │  │  • Error Handling                                           │   │    │
│   │  │  • Request Logging                                          │   │    │
│   │  └─────────────────────────────────────────────────────────────┘   │    │
│   │                                                                     │    │
│   │  ┌─────────────────────────────────────────────────────────────┐   │    │
│   │  │                    Route Groups                              │   │    │
│   │  │  /pipeline/* │ /predict/* │ /attention/* │ /video/*         │   │    │
│   │  │  /intel/*    │ /export/*  │ /fatigue/*   │ /proof/*         │   │    │
│   │  │  /meta/*     │ /sentiment/*│ /jobs       │ /health          │   │    │
│   │  └─────────────────────────────────────────────────────────────┘   │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                            SERVICE LAYER                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │   EXTRACTORS    │  │   GENERATORS    │  │    COMPOSERS    │             │
│   │─────────────────│  │─────────────────│  │─────────────────│             │
│   │ • BrandExtractor│  │ • CopyGenerator │  │ • ImageMatcher  │             │
│   │ • SentimentMon  │  │ • VideoGenerator│  │ • AdComposer    │             │
│   │                 │  │ • ProofPackGen  │  │ • FormatExporter│             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │    ANALYZERS    │  │    PIPELINE     │  │   CONNECTORS    │             │
│   │─────────────────│  │─────────────────│  │─────────────────│             │
│   │ • Performance   │  │ • Orchestrator  │  │ • MetaConnector │             │
│   │ • Attention     │  │ • JobManager    │  │ • UnsplashAPI   │             │
│   │ • Fatigue       │  │                 │  │ • AnthropicAPI  │             │
│   │ • CompetitorInt │  │                 │  │                 │             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                            DATA LAYER                                         │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│   │   MODELS        │  │   PERSISTENCE   │  │    OUTPUTS      │             │
│   │─────────────────│  │─────────────────│  │─────────────────│             │
│   │ • Pydantic DTOs │  │ • JSON Files    │  │ • Generated Ads │             │
│   │ • Enums         │  │ • Job Storage   │  │ • Export ZIPs   │             │
│   │ • Configs       │  │ • (Future: DB)  │  │ • Video Files   │             │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Module Details

### 1. Extractors

```python
# Brand Extractor (Slice 1)
class BrandExtractor:
    """
    Extracts brand DNA from website URL using Claude AI.
    
    Input: URL string
    Output: BrandProfile with:
        - brand_name
        - tagline
        - value_propositions
        - target_audience
        - tone_of_voice
        - claims (with risk levels)
        - colors, fonts
    """
    
# Sentiment Monitor (Slice 6)
class SentimentMonitor:
    """
    Monitors brand mentions for sentiment analysis.
    
    Features:
        - Real-time sentiment scoring (-1 to +1)
        - Crisis detection
        - Auto-pause rules for campaigns
        - Alert thresholds
    """
```

### 2. Generators

```python
# Copy Generator (Slice 2)
class CopyGenerator:
    """
    Generates ad copy variants using Claude AI.
    
    Input: BrandProfile
    Output: List[CopyVariant] with:
        - headline (max 40 chars)
        - primary_text (max 125 chars)
        - cta
        - hook_type
        - emotion_target
    """

# Video Generator (Slice 13)
class VideoGenerator:
    """
    Generates TikTok-style video ads.
    
    Features:
        - Script generation (hook, body, CTA)
        - Avatar selection (5 personalities)
        - Music track selection (5 moods)
        - Scene breakdown
        - Engagement prediction
    
    Styles: UGC, Testimonial, Demo, Explainer, Storytelling, Listicle
    """

# Proof Pack Generator (Slice 15)
class ProofPackGenerator:
    """
    Generates compliance documentation.
    
    Checks:
        - Claim verification
        - FTC compliance
        - Meta Policy compliance
        - Brand safety
    
    Output: ProofPack with action items
    """
```

### 3. Composers

```python
# Image Matcher (Slice 3)
class ImageMatcher:
    """
    Finds matching images using Claude Vision.
    
    Process:
        1. Analyze brand profile for visual requirements
        2. Search Unsplash with semantic queries
        3. Score images with Vision API
        4. Return top matches with scores
    """

# Ad Composer (Slice 4)
class AdComposer:
    """
    Assembles final ad creatives.
    
    Features:
        - Text overlay with brand fonts
        - Multiple formats (square, portrait, landscape)
        - Brand color integration
        - CTA button placement
    """

# Format Exporter (Slice 11)
class FormatExporter:
    """
    Exports ads in multiple platform formats.
    
    Formats (9):
        - meta_feed (1200x628)
        - meta_story (1080x1920)
        - instagram_square (1080x1080)
        - instagram_portrait (1080x1350)
        - linkedin_feed (1200x627)
        - twitter_feed (1200x675)
        - google_display (300x250)
        - google_leaderboard (728x90)
        - tiktok_video (1080x1920)
    """
```

### 4. Analyzers

```python
# Performance Predictor (Slice 9)
class PerformancePredictor:
    """
    Predicts ad performance before launch.
    
    Scoring Components:
        - Headline impact (25%)
        - Emotional resonance (20%)
        - CTA effectiveness (20%)
        - Clarity (15%)
        - Social proof (10%)
        - Urgency (10%)
    
    Output: Score 0-100 with tier (Poor/Below/Average/Good/Excellent)
    """

# Attention Analyzer (Slice 10)
class AttentionAnalyzer:
    """
    Predicts eye-tracking patterns without hardware.
    
    Analysis:
        - Heatmap overlay
        - Visual flow sequence
        - First focus element
        - Time to CTA
        - Attention distribution
    """

# Fatigue Predictor (Slice 14)
class FatiguePredictor:
    """
    Predicts when ads need refreshing.
    
    Metrics:
        - CTR decline tracking
        - CPM increase tracking
        - Frequency oversaturation
        - Audience saturation
    
    Output: Fatigue score, days until refresh, recommendations
    """

# Competitor Intel Analyzer (Slice 12)
class CompetitorIntelAnalyzer:
    """
    Analyzes competitor advertising strategies.
    
    Features:
        - Ad library analysis
        - Copy pattern detection
        - Visual strategy identification
        - Spend estimation
        - Threat level assessment
    """
```

### 5. Pipeline

```python
# Orchestrator (Slice 7)
class PipelineOrchestrator:
    """
    Coordinates end-to-end ad generation.
    
    Stages:
        1. INIT - Initialize job
        2. BRAND_EXTRACTION - Extract from URL
        3. COPY_GENERATION - Generate variants
        4. IMAGE_MATCHING - Find images
        5. AD_COMPOSITION - Create ads
        6. SENTIMENT_CHECK - Verify safety
        7. COMPLETE - Ready for review
    
    Features:
        - Job persistence (JSON)
        - Status tracking
        - Error recovery
        - Parallel processing
    """
```

### 6. Connectors

```python
# Meta Connector (Slice 8)
class MetaConnector:
    """
    Publishes ads to Meta (Facebook/Instagram).
    
    Features:
        - Campaign creation
        - Ad set management
        - Targeting configuration
        - Budget management
        - Status tracking
    """
```

## Data Flow

### Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE DATA FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

User Input (URL)
      │
      ▼
┌─────────────────┐
│ Brand Extractor │──────► BrandProfile
└─────────────────┘              │
                                 │
      ┌──────────────────────────┼──────────────────────────┐
      │                          │                          │
      ▼                          ▼                          ▼
┌──────────┐            ┌──────────────┐           ┌────────────┐
│ Competitor│            │ Copy Generator│           │Performance │
│ Intel    │            └──────────────┘           │ Predictor  │
└──────────┘                    │                  └────────────┘
      │                         │                         │
      │                  List[CopyVariant]                │
      │                         │                         │
      │                         ▼                         │
      │               ┌──────────────┐                    │
      │               │Image Matcher │◄───────────────────┘
      │               └──────────────┘
      │                         │
      │                   MatchedImages
      │                         │
      │                         ▼
      │               ┌──────────────┐
      │               │ Ad Composer  │
      │               └──────────────┘
      │                         │
      │                   ComposedAds
      │                         │
      │    ┌────────────────────┼────────────────────┐
      │    │                    │                    │
      │    ▼                    ▼                    ▼
      │ ┌────────┐      ┌────────────┐       ┌──────────┐
      │ │Attention│      │Format Export│       │  Video   │
      │ │Analyzer │      │  (9 sizes) │       │Generator │
      │ └────────┘      └────────────┘       └──────────┘
      │    │                    │                    │
      │    │                    │                    │
      │    └────────────────────┼────────────────────┘
      │                         │
      │                         ▼
      │               ┌──────────────┐
      │               │ HITL Review  │
      │               └──────────────┘
      │                         │
      │                   Approved Ads
      │                         │
      ▼                         ▼
┌──────────┐            ┌──────────────┐
│ Proof    │            │ Meta Publish │
│ Pack     │            └──────────────┘
└──────────┘                    │
                                │
                          Published Ads
                                │
                                ▼
                       ┌──────────────┐
                       │  Sentiment   │◄──────┐
                       │  Monitor     │       │
                       └──────────────┘       │
                                │             │
                                ▼             │
                       ┌──────────────┐       │
                       │   Fatigue    │───────┘
                       │  Predictor   │  (Refresh cycle)
                       └──────────────┘
```

## API Endpoint Structure

```
/
├── /health                    GET     Health check
├── /pipeline
│   ├── /run                   POST    Run full pipeline
│   └── /status/{job_id}       GET     Job status
├── /jobs                      GET     List jobs
├── /predict
│   ├── /                      POST    Predict performance
│   └── /demo                  POST    Demo
├── /attention
│   ├── /analyze               POST    Analyze attention
│   └── /demo                  POST    Demo
├── /export
│   ├── /formats               GET     List formats
│   ├── /all                   POST    Export all
│   └── /demo                  POST    Demo
├── /intel
│   ├── /analyze               POST    Competitor analysis
│   ├── /demo/{industry}       POST    Demo
│   └── /industries            GET     List industries
├── /video
│   ├── /generate              POST    Generate video
│   ├── /demo/{style}          POST    Demo
│   ├── /styles                GET     List styles
│   ├── /avatars               GET     List avatars
│   └── /music                 GET     List music
├── /fatigue
│   ├── /predict               POST    Predict fatigue
│   └── /demo/{scenario}       POST    Demo
├── /proof
│   ├── /generate              POST    Generate proof pack
│   └── /demo                  POST    Demo
├── /meta
│   ├── /publish               POST    Publish to Meta
│   └── /demo                  POST    Demo
├── /sentiment
│   ├── /check                 POST    Check sentiment
│   └── /demo/{scenario}       POST    Demo
└── /output/{filename}         GET     Static file serving
```

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | Async API framework |
| Validation | Pydantic | Data validation & serialization |
| AI | Anthropic Claude | LLM for extraction/generation |
| Images | Pillow | Image processing |
| HTTP | httpx | Async HTTP client |
| Server | Uvicorn | ASGI server |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 14 | React framework |
| Styling | Tailwind CSS | Utility-first CSS |
| Icons | Lucide React | Icon library |
| State | React Hooks | Local state management |
| HTTP | Fetch API | API calls |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Storage | JSON Files | Job persistence (MVP) |
| Static | FastAPI Static | File serving |
| Config | python-dotenv | Environment management |

## Security Considerations

### API Security
- CORS configured for specific origins
- Input validation via Pydantic
- Rate limiting (to be added)
- API key authentication (to be added)

### Data Security
- No PII stored in job files
- API keys in environment variables
- Sensitive data not logged

## Scalability Path

### Current (MVP)
- Single server
- JSON file storage
- In-memory job queue

### Phase 2
- PostgreSQL for persistence
- Redis for caching
- Background job workers (Celery)

### Phase 3
- Kubernetes deployment
- Horizontal scaling
- CDN for static assets
- Real-time WebSocket updates

## Error Handling

```python
# Standard error response format
{
    "detail": "Error message",
    "error_code": "ERROR_TYPE",
    "timestamp": "2024-01-15T10:00:00Z"
}

# HTTP Status Codes Used
200 - Success
201 - Created
400 - Bad Request (validation errors)
404 - Not Found
500 - Internal Server Error
```

## Monitoring & Observability

### Logging
- Structured JSON logging
- Request/response logging
- Error tracking with stack traces

### Metrics (Planned)
- Request latency
- Pipeline completion rates
- AI token usage
- Error rates by endpoint

## Development Workflow

```bash
# Development
python api_server.py --port 8000  # Hot reload enabled
cd frontend && npm run dev       # Next.js dev server

# Testing
pytest tests/                    # Run all tests
pytest --cov=src                # With coverage

# Linting
ruff check src/                  # Python linting
npm run lint                     # Next.js linting

# Build
npm run build                    # Frontend build
docker build .                   # Docker image
```
