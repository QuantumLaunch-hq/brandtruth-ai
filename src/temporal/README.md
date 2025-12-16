# Temporal Workflow Integration

This module provides durable workflow execution for the BrandTruth AI pipeline using [Temporal](https://temporal.io/).

## Benefits over Synchronous Orchestrator

| Feature | Old (synchronous) | New (Temporal) |
|---------|------------------|----------------|
| Crash recovery | Restart from scratch | Resume from last step |
| Retries | Manual, full pipeline | Automatic, per activity |
| Long-running | HTTP timeout risk | Days/weeks supported |
| Progress | Fake progress bar | Real-time SSE streaming |
| Observability | Basic logging | Full Temporal UI |
| Human approval | Synchronous | Async signals with wait |

## Quick Start

### 1. Start Temporal

```bash
# From project root
docker-compose -f docker-compose.temporal.yml up -d

# Check Temporal UI at http://localhost:8080
```

### 2. Start the Worker

```bash
# Activate virtualenv
source venv/bin/activate

# Start worker (in separate terminal)
python -m src.temporal.worker
```

### 3. Start the API Server

```bash
# Start API with Temporal routes
python api_server.py

# Check health
curl http://localhost:8000/workflow/health
```

### 4. Start a Pipeline

```bash
# Start a workflow
curl -X POST http://localhost:8000/workflow/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://careerfied.ai", "num_variants": 3}'

# Response: {"workflow_id": "pipeline-abc123", "status": "started"}
```

### 5. Stream Progress

```bash
# Stream progress via SSE
curl -N http://localhost:8000/workflow/stream/pipeline-abc123

# Or use JavaScript:
# const es = new EventSource('/workflow/stream/pipeline-abc123');
# es.onmessage = (e) => console.log(JSON.parse(e.data));
```

### 6. Approve Variants

```bash
# Approve specific variants
curl -X POST http://localhost:8000/workflow/approve/pipeline-abc123 \
  -H "Content-Type: application/json" \
  -d '{"variant_ids": ["v1", "v2"]}'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ API Server (FastAPI)                                         │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ /workflow/start   - Start new pipeline                  │ │
│ │ /workflow/progress - Query progress                     │ │
│ │ /workflow/stream  - SSE progress streaming              │ │
│ │ /workflow/approve - Approve variants (signal)           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ gRPC
┌─────────────────────────────────────────────────────────────┐
│ Temporal Server (docker-compose)                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Workflow History    - Durable execution state           │ │
│ │ Task Queues         - Activity scheduling               │ │
│ │ Signals/Queries     - Communication with workflows      │ │
│ │ Temporal UI         - Observability (port 8080)         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ Activities
┌─────────────────────────────────────────────────────────────┐
│ Worker Process (python -m src.temporal.worker)               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ extract_brand_activity   - Brand extraction             │ │
│ │ generate_copy_activity   - Copy generation              │ │
│ │ match_images_activity    - Image matching               │ │
│ │ compose_ads_activity     - Ad composition               │ │
│ │ predict_performance_activity - Performance scoring      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Files

```
src/temporal/
├── __init__.py           # Module exports
├── README.md             # This file
├── client.py             # Temporal client utilities
├── routes.py             # FastAPI routes for workflow management
├── worker.py             # Temporal worker process
├── activities/
│   ├── __init__.py
│   ├── extract.py        # Brand extraction activity
│   ├── generate.py       # Copy generation activity
│   ├── match.py          # Image matching activity
│   ├── compose.py        # Ad composition activity
│   └── score.py          # Performance scoring activity
└── workflows/
    ├── __init__.py
    └── ad_pipeline.py    # Main pipeline workflow
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflow/health` | GET | Check Temporal availability |
| `/workflow/start` | POST | Start new pipeline |
| `/workflow/progress/{id}` | GET | Get current progress |
| `/workflow/stream/{id}` | GET | Stream progress (SSE) |
| `/workflow/result/{id}` | GET | Get complete result |
| `/workflow/approve/{id}` | POST | Approve variants |
| `/workflow/cancel/{id}` | POST | Cancel workflow |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEMPORAL_HOST` | `localhost:7234` | Temporal server address |
| `TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `TEMPORAL_TASK_QUEUE` | `brandtruth-pipeline` | Task queue name |

## Fallback Behavior

If Temporal is unavailable, the API server falls back to the synchronous orchestrator. Check `/workflow/health` to see if Temporal is enabled:

```json
{"temporal_available": true, "status": "healthy"}
// or
{"temporal_available": false, "status": "degraded", "message": "Using fallback"}
```

## Monitoring

Access the Temporal Web UI at http://localhost:8080 to:
- View running and completed workflows
- Inspect workflow history step-by-step
- See activity inputs/outputs
- Debug failures with full stack traces
- Query workflow state
