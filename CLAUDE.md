# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BrandTruth AI is an AI-native advertising platform that generates complete ad campaigns from a URL. The platform extracts brand information, generates copy variants, matches images, composes ads, and publishes to platforms like Meta.

**Tech Stack:** Python 3.11, FastAPI, Next.js 14, Temporal, PostgreSQL, MinIO, Qdrant, Prisma, Claude API

## Development Commands

### Docker Development (Recommended)
```bash
docker-compose up -d              # Start all services (API :8010, Frontend :3010)
docker-compose up -d --build      # Rebuild and start
docker-compose logs -f api        # View API logs
docker-compose logs -f worker     # View Temporal worker logs
docker-compose down               # Stop all services
```

Services accessible at:
- Frontend: http://localhost:3010
- API: http://localhost:8010/docs
- Temporal UI: http://localhost:8091
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Qdrant: http://localhost:6333/dashboard

### Local Development (without Docker)
```bash
# Install dependencies
make install                    # Backend (requires venv activated)
cd frontend && npm install      # Frontend

# Start servers
make run                        # API server on :8000
make frontend                   # Frontend on :3000 (separate terminal)
```

### Database Commands
```bash
cd frontend
npx prisma generate             # Generate Prisma client after schema changes
npx prisma db push              # Push schema changes to database
npx prisma studio               # Open Prisma Studio GUI
```

### Testing
```bash
make test                       # All backend tests
make test-unit                  # Unit tests only
make test-int                   # Integration tests only
make test-e2e                   # E2E tests only
make test-contract              # Contract/schema tests
make test-cov                   # With coverage report

# Run single test file
pytest tests/unit/test_performance_predictor.py -v

# Run specific test
pytest tests/unit/test_performance_predictor.py::test_predict_high_score -v

# Frontend tests
cd frontend
npm test                        # Jest component tests
npm run test:e2e                # Playwright E2E (requires dev server running)
```

### Code Quality
```bash
make lint                       # Run ruff linter
make format                     # Format with ruff
make clean                      # Clean generated files
```

## Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)         │  Studio (main workflow)               │
│  ─────────────────────         │  Campaigns, Dashboard, Tools          │
├─────────────────────────────────────────────────────────────────────────┤
│  API Server (FastAPI)          │  Temporal Routes (/workflow/*)        │
│  ─────────────────────         │  Campaign APIs, Variant APIs          │
├─────────────────────────────────────────────────────────────────────────┤
│  Temporal Workflows            │  AdPipelineWorkflow, PublishWorkflow  │
│  ─────────────────────         │  Durable, retryable, queryable        │
├─────────────────────────────────────────────────────────────────────────┤
│  Activities (src/temporal/)    │  extract, generate, match, compose,   │
│                                │  score, upload, embed, publish        │
├─────────────────────────────────────────────────────────────────────────┤
│  Storage                                                                │
│  PostgreSQL (campaigns, variants, users)                                │
│  MinIO (ad creatives, images)                                           │
│  Qdrant (brand/variant embeddings)                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Temporal Workflow Pipeline (`src/temporal/`)

The core ad generation is a Temporal workflow that survives crashes and provides real-time progress:

**AdPipelineWorkflow stages** (`workflows/ad_pipeline.py`):
1. `extract_brand` - Scrape website + Claude extraction → BrandProfile
2. `embed_brand` - Store brand embedding in Qdrant
3. `generate_copy` - Claude generates N copy variants
4. `embed_variants` - Store variant embeddings in Qdrant
5. `match_images` - Pexels/Unsplash/DALL-E image matching
6. `compose_ads` - Render ad creatives in multiple formats
7. `upload` - Upload to MinIO storage
8. `score_variants` - Claude predicts performance (0-100)
9. `complete` - Save to PostgreSQL, ready for approval

**Key workflow APIs**:
- `POST /workflow/start` - Start pipeline, returns workflow_id
- `GET /workflow/progress/{id}` - Query current stage/percent
- `GET /workflow/stream/{id}` - SSE stream for real-time updates
- `GET /workflow/result/{id}` - Get full result when complete

### Database Schema (`frontend/prisma/schema.prisma`)

- **User** - NextAuth.js user with campaigns
- **Campaign** - URL, status, brandProfile JSON, workflowId reference
- **Variant** - headline, primaryText, cta, imageUrl, composedUrl, score, status

Campaign statuses: DRAFT → PROCESSING → READY → APPROVED → PUBLISHED

### Layer Components (`src/`)

**Extractors** (`extractors/`)
- `brand_extractor.py` - Extracts brand profile from website using Claude
- `sentiment_monitor.py` - Monitors brand sentiment, triggers auto-pause rules

**Generators** (`generators/`)
- `copy_generator.py` - Generates ad copy variants with Claude
- `video_generator.py` - Creates AI UGC-style video scripts

**Composers** (`composers/`)
- `ad_composer.py` - Composites text + image into ad creatives
- `image_matcher_v2.py` - Matches copy to stock images (Pexels → Unsplash → DALL-E)
- `format_exporter.py` - Exports ads to 9 platform-specific formats

**Analyzers** (`analyzers/`)
- `performance_predictor.py` - Predicts ad performance score 0-100
- `attention_analyzer.py` - Simulates eye-tracking heatmaps
- `fatigue_predictor.py` - Predicts creative fatigue timing

**Connectors** (`connectors/`)
- `meta_connector.py` - Publishes to Meta Ads
- `google_connector.py`, `linkedin_connector.py`, `tiktok_connector.py` - Multi-platform support
- `factory.py` - Connector factory pattern for platform selection

**Storage** (`storage/`)
- `minio_client.py` - S3-compatible storage for ad creatives

**Vector** (`vector/`)
- Qdrant integration for semantic search over brands/variants

### Models (`src/models/`)

Core Pydantic models that flow through the pipeline:
- `BrandProfile` - Extracted brand data (tagline, claims, tone, assets)
- `CopyVariant` - Generated ad copy (headline, primary_text, cta)
- `ImageMatch` - Selected image with relevance score
- `ComposedAd` - Final ad with rendered assets in multiple formats

## API Structure

The FastAPI server (`api_server.py`) exposes endpoints grouped by feature:
- `/workflow/*` - Temporal workflow management (start, progress, stream, result)
- `/api/campaigns/*` - Campaign CRUD operations
- `/api/variants/*` - Variant approval/rejection
- `/predict/*`, `/attention/*`, `/fatigue/*` - Analysis tools
- `/export/*`, `/video/*`, `/hooks/*` - Generation tools

All feature endpoints have `/demo` variants for testing without real data.

Interactive API docs: `http://localhost:8010/docs` (Docker) or `http://localhost:8000/docs` (local)

## Frontend Structure

**Main Pages** (`frontend/app/`):
- `/studio` - Main workflow: enter URL → watch pipeline → approve variants
- `/campaigns` - Campaign list and management
- `/campaigns/[id]` - Campaign detail with variant approval
- `/dashboard` - Overview and quick actions
- `/tools` - Access to all analysis tools
- `/publish` - Publish approved campaigns to Meta

**Key Hooks** (`frontend/lib/hooks/`):
- `useWorkflow.ts` - Start pipeline, manage workflow state
- `useWorkflowProgress.ts` - SSE subscription for real-time progress

## Testing Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Test individual modules
├── integration/             # Test API endpoints
├── e2e/                     # Test complete user flows
├── contract/                # Schema validation tests
└── component/               # Component integration tests
```

Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`

## Key Patterns

- **Temporal workflows**: Durable, retryable pipelines with queryable progress
- **Lazy singletons**: Use `get_instance(name, factory)` pattern for expensive objects
- **Async throughout**: All extractors/generators/analyzers are async
- **Pydantic models**: Strict typing for all data transfer objects
- **Demo endpoints**: Every feature has a `/demo` endpoint for testing
- **Factory functions**: `get_predictor()`, `get_video_generator()`, etc. for DI
- **SSE streaming**: Real-time progress updates via EventSource

## Environment Variables

Required in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...

# Image sources (fallback chain)
PEXELS_API_KEY=...
UNSPLASH_ACCESS_KEY=...

# Azure OpenAI (optional, for DALL-E)
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
```
