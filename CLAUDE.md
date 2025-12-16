# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BrandTruth AI is an AI-native advertising platform that generates complete ad campaigns from a URL. The platform extracts brand information, generates copy variants, matches images, composes ads, and publishes to platforms like Meta.

**Tech Stack:** Python 3.11, FastAPI, Next.js 14, Pydantic, Claude API

## Development Commands

### Setup & Run
```bash
# Install dependencies
make install                    # Backend (requires venv activated)
cd frontend && npm install      # Frontend

# Start servers
make run                        # API server on :8000
make frontend                   # Frontend on :3000 (run in separate terminal)
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

The platform follows a pipeline architecture with four layers:

```
URL Input → Extraction → Generation → Control → Platform
```

### Layer Components (`src/`)

**Extractors** - Extract data from external sources
- `brand_extractor.py` - Extracts brand profile from website using Claude
- `sentiment_monitor.py` - Monitors brand sentiment, triggers auto-pause rules
- `social_proof_collector.py` - Collects testimonials, stats, trust signals

**Generators** - Create content using AI
- `copy_generator.py` - Generates ad copy variants with Claude
- `video_generator.py` - Creates AI UGC-style video scripts and metadata
- `hook_generator.py` - Generates attention-grabbing hooks
- `proof_pack.py` - Generates compliance documentation

**Composers** - Combine elements into final outputs
- `ad_composer.py` - Composites text + image into ad creatives
- `image_matcher_v2.py` - Matches copy to stock images via Unsplash
- `format_exporter.py` - Exports ads to 9 platform-specific formats

**Analyzers** - Analyze and predict performance
- `performance_predictor.py` - Predicts ad performance score 0-100
- `attention_analyzer.py` - Simulates eye-tracking heatmaps
- `fatigue_predictor.py` - Predicts creative fatigue timing
- `competitor_intel.py` - Analyzes competitor ad strategies
- `landing_page_analyzer.py` - Scores ad-to-landing page match
- `budget_simulator.py` - Simulates budget scenarios and ROAS
- `platform_recommender.py` - Recommends ad platforms
- `ab_test_planner.py` - Plans A/B test sequences
- `audience_targeting.py` - Suggests audience segments
- `iteration_assistant.py` - Diagnoses underperforming ads

**Pipeline** - Orchestrates the full flow
- `orchestrator.py` - Runs extraction → generation → composition pipeline

**Connectors** - Interface with ad platforms
- `meta_connector.py` - Publishes to Meta Ads (simulated)

### Data Flow

1. **Pipeline Orchestrator** receives URL and config
2. **Brand Extractor** scrapes website, calls Claude to extract BrandProfile
3. **Copy Generator** uses BrandProfile to generate CopyVariant[]
4. **Image Matcher** finds matching stock images for each variant
5. **Ad Composer** renders final ad images in multiple formats
6. **Sentiment Monitor** checks brand health before publishing
7. **Meta Connector** publishes approved ads

### Models (`src/models/`)

Core Pydantic models that flow through the pipeline:
- `BrandProfile` - Extracted brand data (tagline, claims, tone, assets)
- `CopyVariant` - Generated ad copy (headline, primary_text, cta)
- `ImageMatch` - Selected image with relevance score
- `ComposedAd` - Final ad with rendered assets in multiple formats

## API Structure

The FastAPI server (`api_server.py`) exposes endpoints grouped by feature:
- `/pipeline/*` - Full pipeline orchestration
- `/predict/*`, `/attention/*`, `/fatigue/*` - Analysis tools
- `/export/*`, `/video/*`, `/hooks/*` - Generation tools
- `/intel/*`, `/landing/*`, `/budget/*` - Research tools
- `/meta/*`, `/sentiment/*` - Publishing and monitoring

All endpoints have `/demo` variants for testing without real data.

Interactive API docs: `http://localhost:8000/docs`

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

- **Lazy singletons**: Use `get_instance(name, factory)` pattern for expensive objects
- **Async throughout**: All extractors/generators/analyzers are async
- **Pydantic models**: Strict typing for all data transfer objects
- **Demo endpoints**: Every feature has a `/demo` endpoint for testing
- **Factory functions**: `get_predictor()`, `get_video_generator()`, etc. for DI
