# BrandTruth AI

> AI-Native Advertising Platform with Complete Ad Lifecycle Management

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/brandtruth/adplatform)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/next.js-14+-black.svg)](https://nextjs.org)
[![Tests](https://img.shields.io/badge/tests-585%20passing-brightgreen.svg)](docs/TESTING.md)
[![Features](https://img.shields.io/badge/features-23%20slices-orange.svg)](docs/INDEX.md)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

## Overview

BrandTruth AI transforms any website URL into high-performing, brand-safe advertisements with AI-powered optimization at every step. **23 integrated features** covering the complete ad lifecycle.

### Key Differentiators

| Feature | Traditional Tools | BrandTruth AI |
|---------|------------------|---------------|
| Brand Extraction | Manual copywriting | Auto from URL |
| Performance Prediction | Post-launch analytics | Pre-launch AI scoring |
| Attention Analysis | $10K+ eye-tracking hardware | Built-in AI heatmaps |
| Sentiment Monitoring | Separate tool | Integrated auto-pause |
| Competitor Intel | Manual research | Automated analysis |
| Video Ads | Separate production | AI UGC generation |
| Compliance | Legal review | Automated proof packs |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Installation

```bash
# Clone repository
git clone https://github.com/brandtruth/adplatform.git
cd adplatform

# Backend setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install
cd ..

# Environment configuration
cp .env.example .env
# Edit .env with your API keys
```

### Running

```bash
# Terminal 1: API Server
source venv/bin/activate
python api_server.py --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Access the application:
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BRANDTRUTH AI                               │
├─────────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14)                                              │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │Dashboard│ │ Predict │ │Attention│ │  Video  │ │  Intel  │ ...   │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │
├───────┼──────────┼──────────┼──────────┼──────────┼────────────────┤
│       │          │          │          │          │                 │
│  ┌────▼──────────▼──────────▼──────────▼──────────▼────┐           │
│  │              FastAPI Backend (v1.0.0)                │           │
│  └──────────────────────┬───────────────────────────────┘           │
│                         │                                           │
├─────────────────────────┼───────────────────────────────────────────┤
│  Core Modules           │                                           │
│  ┌──────────────────────▼───────────────────────────────┐          │
│  │ Extractors │ Generators │ Composers │ Analyzers      │          │
│  │ ─────────  │ ──────────│ ─────────│ ─────────       │          │
│  │ • Brand    │ • Copy     │ • Image   │ • Performance  │          │
│  │ • Sentiment│ • Video    │ • Ad      │ • Attention    │          │
│  │            │ • Proof    │ • Export  │ • Fatigue      │          │
│  │            │            │           │ • Competitor   │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  External Services                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Anthropic│ │ Unsplash │ │ Meta Ads │ │ HeyGen*  │               │
│  │  Claude  │ │  Images  │ │   API    │ │  Video   │               │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
└─────────────────────────────────────────────────────────────────────┘
* Video API integration ready, mock mode for demo
```

## Features

### 1. Core Pipeline (Slices 1-8)

| Slice | Feature | Description |
|-------|---------|-------------|
| 1 | Brand Extraction | Extract brand DNA from any URL |
| 2 | Copy Generation | AI-generated ad copy variants |
| 3 | Image Matching | Vision-based image selection |
| 4 | Ad Composition | Automated ad assembly |
| 5 | HITL Dashboard | Human-in-the-loop approval |
| 6 | Sentiment Monitor | Brand safety with auto-pause |
| 7 | Pipeline Orchestrator | Job management system |
| 8 | Meta Connector | Facebook/Instagram publishing |

### 2. WOW Features (Slices 9-15)

| Slice | Feature | Description |
|-------|---------|-------------|
| 9 | Performance Predictor | AI scoring 0-100 before launch |
| 10 | Attention Heatmap | Eye-tracking without hardware |
| 11 | Multi-Format Export | 9 ad sizes, one click |
| 12 | Competitor Intel | Market analysis from Ads Library |
| 13 | AI UGC Video | TikTok-style video generation |
| 14 | Creative Fatigue | Predict when to refresh ads |
| 15 | Proof Pack | Compliance documentation |

## API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Pipeline
```http
POST /pipeline/run
Content-Type: application/json

{
  "url": "https://careerfied.ai",
  "num_variants": 5,
  "platform": "meta"
}
```

#### Performance Prediction
```http
POST /predict
Content-Type: application/json

{
  "headline": "Stop Getting Rejected by ATS",
  "primary_text": "Build resumes that get interviews",
  "cta": "Get Started"
}
```

#### AI Video Generation
```http
POST /video/generate
Content-Type: application/json

{
  "brand_name": "Careerfied",
  "product_description": "AI resume builder",
  "target_audience": "Job seekers",
  "key_benefits": ["ATS-optimized", "Templates", "Feedback"],
  "style": "ugc",
  "aspect_ratio": "9:16"
}
```

#### Competitor Analysis
```http
POST /intel/analyze
Content-Type: application/json

{
  "brand_name": "Careerfied",
  "industry": "career",
  "competitor_names": ["Resume.io", "Zety"]
}
```

See full API documentation at `/docs` when server is running.

## Frontend Pages

| Page | URL | Description |
|------|-----|-------------|
| Landing | `/` | Hero page with feature overview |
| Dashboard | `/dashboard` | Generate and approve ads |
| Predict | `/predict` | Performance scoring |
| Attention | `/attention` | Heatmap analysis |
| Export | `/export` | Multi-format export |
| Intel | `/intel` | Competitor intelligence |
| Video | `/video` | AI video generation |
| Fatigue | `/fatigue` | Creative fatigue prediction |
| Proof | `/proof` | Compliance documentation |
| Sentiment | `/sentiment` | Brand monitoring |
| Publish | `/publish` | Meta publishing |

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional
UNSPLASH_ACCESS_KEY=...
META_ACCESS_TOKEN=...
VIDEO_API_KEY=...  # HeyGen/Synthesia

# Server
API_HOST=0.0.0.0
API_PORT=8000
```

### Video Configuration

```python
VideoConfig(
    style="ugc",              # ugc, testimonial, demo, explainer, storytelling, listicle
    aspect_ratio="9:16",      # 9:16, 1:1, 16:9
    avatar_style="casual",    # casual, professional, energetic, friendly, authoritative
    include_captions=True,
    include_music=True,
    max_duration_seconds=60
)
```

## Testing

BrandTruth AI has **255 tests** across backend and frontend:

| Category | Tool | Tests |
|----------|------|-------|
| Backend Unit | pytest | 88 |
| Backend Integration | pytest | 27 |
| Backend E2E | pytest | 8 |
| Backend Contract | pytest | 29 |
| Frontend Component | Jest | 47 |
| Frontend E2E | Playwright | 56 |

```bash
# Backend tests
make test              # All backend tests
make test-unit         # Unit tests only
make test-cov          # With coverage

# Frontend tests
cd frontend
npm test               # Component tests
npm run test:e2e       # E2E tests (requires npm run dev)
```

See [docs/TESTING.md](docs/TESTING.md) for complete testing guide.

## Deployment

### Docker

```bash
docker-compose up -d
```

### Production

```bash
# Backend
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
npm run build
npm start
```

## Project Structure

```
adplatform/
├── src/
│   ├── extractors/          # Brand & sentiment extraction
│   ├── generators/          # Copy, video, proof generation
│   ├── composers/           # Image matching, ad composition
│   ├── analyzers/           # Performance, attention, fatigue
│   ├── pipeline/            # Orchestration
│   ├── connectors/          # External APIs
│   ├── models/              # Pydantic models
│   └── utils/               # Logging, retry logic
├── frontend/
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   └── lib/                 # Utilities
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   ├── e2e/                # End-to-end tests
│   └── fixtures/           # Test data
├── api_server.py           # FastAPI application
├── requirements.txt        # Python dependencies
└── CLAUDE.md              # AI assistant guide
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Documentation:** [docs.brandtruth.ai](https://docs.brandtruth.ai)
- **Issues:** [GitHub Issues](https://github.com/brandtruth/adplatform/issues)
- **Email:** support@brandtruth.ai

---

Built with ❤️ by the BrandTruth Team
