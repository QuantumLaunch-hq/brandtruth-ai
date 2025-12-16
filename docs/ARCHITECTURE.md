# BrandTruth AI - System Architecture

**Version:** 1.0  
**Last Updated:** December 2025

---

## 1. Architecture Overview

### Design Principles

1. **Serverless-first** - Modal for compute, Vercel for frontend
2. **Event-driven** - Async processing, webhook callbacks
3. **Stateless workers** - All state in database/storage
4. **Cost-transparent** - Track every API call cost
5. **Horizontally scalable** - No single points of failure

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                        (Vercel - React Dashboard)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
│                         (Modal Web Endpoints)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
            │  Extraction │   │  Generation │   │   Control   │
            │   Workers   │   │   Workers   │   │   Workers   │
            │   (Modal)   │   │   (Modal)   │   │   (Modal)   │
            └─────────────┘   └─────────────┘   └─────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Supabase   │  │    Modal     │  │   Pinecone   │  │  Cloudflare  │    │
│  │  (Postgres)  │  │   Volumes    │  │  (Vectors)   │  │     R2       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Claude     │  │   Unsplash   │  │   Meta API   │  │  LinkedIn    │    │
│  │     API      │  │     API      │  │              │  │     API      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Extraction Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTRACTION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  Web Scraper    │    │  Review Scraper │                    │
│  │  (Playwright)   │    │  (G2, Reddit)   │                    │
│  └────────┬────────┘    └────────┬────────┘                    │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ Brand Extractor │    │    Sentiment    │                    │
│  │    (Claude)     │    │    Extractor    │                    │
│  └────────┬────────┘    └────────┬────────┘                    │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌─────────────────────────────────────────┐                   │
│  │           BrandProfile + SentimentProfile                   │
│  │              (Pydantic Models)           │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Scraper | Playwright | Extract website content |
| Review Scraper | Playwright + BeautifulSoup | Extract market sentiment |
| Brand Extractor | Claude API | Analyze and structure brand data |
| Sentiment Extractor | Claude API | Analyze market mood |

**Data Models:**

```python
# BrandProfile (simplified)
{
  "brand_name": str,
  "website_url": str,
  "tagline": str,
  "value_propositions": list[str],
  "claims": list[BrandClaim],
  "social_proof": list[SocialProof],
  "tone_markers": list[ToneMarker],
  "key_terms": list[str],
  "assets": BrandAssets,
  "confidence_score": float
}

# SentimentProfile (simplified)
{
  "dominant_emotions": list[str],
  "winning_angles": list[str],
  "blocked_angles": list[str],
  "language_markers": list[str],
  "risk_posture": str
}
```

---

### 2.2 Generation Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                     GENERATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │         Constraint Builder              │                   │
│  │  (BrandProfile + SentimentProfile)      │                   │
│  └────────────────────┬────────────────────┘                   │
│                       │                                         │
│                       ▼                                         │
│  ┌─────────────────────────────────────────┐                   │
│  │           Copy Generator                │                   │
│  │     (Claude with constraints)           │                   │
│  └────────────────────┬────────────────────┘                   │
│                       │                                         │
│                       ▼                                         │
│  ┌─────────────────────────────────────────┐                   │
│  │          Image Matcher                  │                   │
│  │    (Unsplash API + Claude reasoning)    │                   │
│  └────────────────────┬────────────────────┘                   │
│                       │                                         │
│                       ▼                                         │
│  ┌─────────────────────────────────────────┐                   │
│  │           Ad Composer                   │                   │
│  │     (Sharp/Pillow image processing)     │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Copy Generation Flow:**

```
1. Load BrandProfile constraints
2. Load SentimentProfile constraints
3. Build constrained prompt:
   - Allowed claims (low/medium risk only)
   - Required tone markers
   - Key terms to include
   - Terms to avoid
   - Winning angles from sentiment
4. Generate 10 variants with Claude
5. Tag each variant:
   - angle (pain/benefit/curiosity/etc)
   - persona target
   - proof sources
6. Return structured CopyVariant[]
```

**Ad Composition Flow:**

```
1. For each CopyVariant:
   a. Extract keywords for image search
   b. Query Unsplash API
   c. Score images with Claude (mood, composition)
   d. Select best match
2. Render ad:
   a. Download and resize image
   b. Apply dark overlay
   c. Add text (headline, body, CTA)
   d. Add logo
   e. Export 3 sizes (1:1, 4:5, 9:16)
3. Return Ad with all assets
```

---

### 2.3 Control Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                      CONTROL LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  HITL Dashboard │  │   Proof Pack    │  │   Auto Actions  │ │
│  │     (React)     │  │   Generator     │  │    Engine       │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │          │
│           ▼                    ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Campaign State Machine                   ││
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         ││
│  │  │Draft │→ │Review│→ │Approved│→│Live │→ │Paused│         ││
│  │  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**State Machine:**

| State | Description | Transitions |
|-------|-------------|-------------|
| `draft` | Ads generated, not reviewed | → `review` |
| `review` | Pending human approval | → `approved` or → `draft` (regenerate) |
| `approved` | Ready to launch | → `live` |
| `live` | Active on platform | → `paused` |
| `paused` | Stopped (manual or auto) | → `live` or → `archived` |
| `archived` | Historical record | Terminal |

**Auto-Action Rules:**

```python
AUTO_PAUSE_RULES = [
    # Hard stops (immediate)
    {"condition": "spend > budget_limit", "action": "pause", "priority": "critical"},
    {"condition": "cpm > 3x baseline", "action": "pause", "priority": "critical"},
    {"condition": "impressions > 1000 AND clicks == 0", "action": "pause", "priority": "high"},
    
    # Soft actions (recommendations)
    {"condition": "ctr < 0.5%", "action": "recommend_creative_refresh", "priority": "medium"},
    {"condition": "frequency > 3", "action": "recommend_audience_expansion", "priority": "medium"},
]
```

---

### 2.4 Platform Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                     PLATFORM LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │          Platform Abstraction           │                   │
│  │  (Common interface for all platforms)   │                   │
│  └────────────────────┬────────────────────┘                   │
│                       │                                         │
│       ┌───────────────┼───────────────┐                        │
│       ▼               ▼               ▼                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                    │
│  │  Meta   │    │LinkedIn │    │ Google  │                    │
│  │Connector│    │Connector│    │Connector│                    │
│  └─────────┘    └─────────┘    └─────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Platform Interface:**

```python
class PlatformConnector(ABC):
    @abstractmethod
    async def create_campaign(self, campaign: Campaign) -> str:
        """Create campaign, return platform ID."""
        pass
    
    @abstractmethod
    async def upload_creative(self, ad: Ad) -> str:
        """Upload ad creative, return platform ID."""
        pass
    
    @abstractmethod
    async def publish(self, ad_id: str) -> bool:
        """Set ad to active status."""
        pass
    
    @abstractmethod
    async def pause(self, ad_id: str) -> bool:
        """Pause ad delivery."""
        pass
    
    @abstractmethod
    async def get_insights(self, ad_id: str, date_range: DateRange) -> Insights:
        """Fetch performance metrics."""
        pass
```

---

## 3. Data Architecture

### 3.1 Database Schema (Supabase/Postgres)

```sql
-- Campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    website_url TEXT NOT NULL,
    objective TEXT NOT NULL,
    platform TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    brand_profile JSONB,
    sentiment_profile JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ads
CREATE TABLE ads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id),
    copy_variant JSONB NOT NULL,
    image_match JSONB NOT NULL,
    rendered_assets JSONB NOT NULL,  -- URLs to 1:1, 4:5, 9:16
    platform_ids JSONB,              -- {meta_ad_id: "...", etc}
    status TEXT DEFAULT 'draft',
    approval_status TEXT DEFAULT 'pending',
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    proof_pack JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Snapshots
CREATE TABLE performance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_id UUID REFERENCES ads(id),
    platform TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    impressions INTEGER,
    clicks INTEGER,
    spend DECIMAL(10,2),
    ctr DECIMAL(5,4),
    cpm DECIMAL(10,2),
    conversions INTEGER,
    health_score INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto Actions Log
CREATE TABLE auto_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_id UUID REFERENCES ads(id),
    action_type TEXT NOT NULL,
    reason TEXT NOT NULL,
    rule_triggered TEXT,
    executed_at TIMESTAMPTZ DEFAULT NOW(),
    reverted_at TIMESTAMPTZ,
    reverted_by UUID
);
```

### 3.2 File Storage (Cloudflare R2)

```
/campaigns/{campaign_id}/
  brand_profile.json
  sentiment_profile.json
  
/ads/{ad_id}/
  copy_variant.json
  image_original.jpg
  ad_1x1.png
  ad_4x5.png
  ad_9x16.png
  proof_pack.pdf
  
/assets/{brand_id}/
  logo.png
  brand_colors.json
```

### 3.3 Vector Storage (Pinecone)

```
Namespaces:
- brand_snippets    # For brand similarity search
- sentiment_clusters # For market mood patterns
- creative_variants  # For "don't repeat losers"
- performance_embeddings # For pattern recognition

Index Schema:
{
  "id": "snippet_uuid",
  "values": [float array from embedding],
  "metadata": {
    "campaign_id": "uuid",
    "source_url": "https://...",
    "text": "Original snippet",
    "type": "claim|proof|tone",
    "performance_score": 0.75
  }
}
```

---

## 4. API Design

### 4.1 REST Endpoints

```
POST   /api/campaigns              # Create campaign
GET    /api/campaigns              # List campaigns
GET    /api/campaigns/{id}         # Get campaign details
DELETE /api/campaigns/{id}         # Delete campaign

POST   /api/campaigns/{id}/extract       # Trigger brand extraction
POST   /api/campaigns/{id}/generate      # Generate ads
POST   /api/campaigns/{id}/approve       # Bulk approve
POST   /api/campaigns/{id}/publish       # Push to platform

GET    /api/ads                    # List ads
GET    /api/ads/{id}               # Get ad details
PATCH  /api/ads/{id}               # Update ad (edit copy)
POST   /api/ads/{id}/approve       # Approve single ad
POST   /api/ads/{id}/reject        # Reject ad
POST   /api/ads/{id}/regenerate    # Regenerate ad

GET    /api/ads/{id}/insights      # Get performance data
GET    /api/ads/{id}/proof-pack    # Download proof pack

POST   /api/webhooks/meta          # Meta callback
POST   /api/webhooks/linkedin      # LinkedIn callback
```

### 4.2 WebSocket Events

```
campaign:extraction:started
campaign:extraction:progress
campaign:extraction:completed
campaign:extraction:failed

campaign:generation:started
campaign:generation:progress
campaign:generation:completed

ad:status:changed
ad:performance:updated
ad:auto_action:triggered
```

---

## 5. Deployment Architecture

### 5.1 Infrastructure

```
┌─────────────────────────────────────────────────────────────────┐
│                          MODAL                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Web Workers │  │ GPU Workers │  │ Cron Jobs   │             │
│  │ (Extraction)│  │ (Composing) │  │ (Insights)  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │          Modal Volumes (temp storage)   │                   │
│  └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         VERCEL                                  │
│  ┌─────────────────────────────────────────┐                   │
│  │      Next.js Dashboard (React)          │                   │
│  └─────────────────────────────────────────┘                   │
│  ┌─────────────────────────────────────────┐                   │
│  │           API Routes (Edge)             │                   │
│  └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        SUPABASE                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Postgres   │  │    Auth     │  │  Realtime   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE R2                                │
│  ┌─────────────────────────────────────────┐                   │
│  │         Object Storage (ads, assets)    │                   │
│  └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Cost Estimates (Monthly)

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Modal | Pay-per-use | $50-150 |
| Claude API | Usage-based | $50-200 |
| Vercel | Pro | $20 |
| Supabase | Pro | $25 |
| Cloudflare R2 | Free tier | $0-10 |
| Pinecone | Starter | $0-70 |
| Unsplash API | Free | $0 |
| **Total** | | **$145-475/month** |

### 5.3 Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| Extraction workers | Modal auto-scales |
| Generation workers | Modal auto-scales + GPU for image processing |
| Database | Supabase handles (upgrade tier if needed) |
| Storage | R2 unlimited |
| Vector DB | Pinecone pods (add as needed) |

---

## 6. Security Architecture

### 6.1 Authentication

- Supabase Auth (JWT-based)
- Row-level security (RLS) for multi-tenant
- API key rotation for external services

### 6.2 Secrets Management

```
Modal Secrets:
- anthropic-api-key
- unsplash-api-key
- meta-app-credentials
- supabase-credentials

Vercel Environment Variables:
- NEXT_PUBLIC_SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- MODAL_TOKEN_ID
```

### 6.3 Data Privacy

- No PII stored in vector databases
- Ad account credentials encrypted at rest
- Audit logs for all access

---

## 7. Monitoring & Observability

### 7.1 Logging

```python
# Structured logging for all operations
logger.info("extraction_started", extra={
    "campaign_id": campaign.id,
    "url": campaign.website_url,
    "trace_id": trace_id
})

logger.info("claude_api_call", extra={
    "model": "claude-sonnet-4-20250514",
    "input_tokens": response.usage.input_tokens,
    "output_tokens": response.usage.output_tokens,
    "cost_usd": calculate_cost(response.usage),
    "trace_id": trace_id
})
```

### 7.2 Metrics

| Metric | Purpose |
|--------|---------|
| extraction_duration_seconds | Performance monitoring |
| generation_duration_seconds | Performance monitoring |
| claude_api_cost_usd | Cost tracking |
| ads_generated_total | Volume tracking |
| approval_rate | Quality tracking |
| auto_pause_count | Safety tracking |

### 7.3 Alerting

| Alert | Condition | Action |
|-------|-----------|--------|
| High API cost | > $50/day | Notify + review |
| Extraction failure rate | > 20% | Investigate |
| Auto-pause spike | > 10/hour | Review rules |
| Platform API errors | > 5% | Check credentials |

---

## 8. Development Workflow

### 8.1 Local Development

```bash
# Start local environment
cd /Users/satish/qlp-projects/adplatform
source venv/bin/activate

# Run extraction locally
python run_local.py https://example.com

# Run with Modal (remote)
modal run modal_app.py --url https://example.com
```

### 8.2 Deployment

```bash
# Deploy Modal functions
modal deploy modal_app.py

# Deploy dashboard (Vercel)
cd dashboard && vercel --prod
```

### 8.3 Testing Strategy

| Layer | Testing Approach |
|-------|------------------|
| Models | Unit tests (pytest) |
| Extractors | Integration tests with mock websites |
| Generators | Golden file tests (known inputs → expected outputs) |
| Composers | Visual regression tests |
| Platform connectors | Sandbox API tests |

---

**Document Owner:** Subrahmanya  
**Architecture Review:** Pending  
**Last Updated:** December 2025
