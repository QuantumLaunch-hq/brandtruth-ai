# BrandTruth AI - Implementation Plan

**Version:** 1.0
**Created:** December 16, 2025
**Goal:** Production-ready MVP in 6 weeks

---

## OVERVIEW

We're fixing this the **right way** - production-grade, tested, no shortcuts.

### Core Principle
> **5 features that work completely > 23 features that work partially**

### The 5 Essential Features
1. ✅ Brand Extraction (DONE)
2. ✅ Copy Generation (DONE)
3. ❌ Image Composition (IMPLEMENT)
4. ❌ HITL with Persistence (CONNECT)
5. ❌ Meta Publishing (IMPLEMENT)

---

## PHASE 1: FOUNDATION (Days 1-10)

### Day 1-2: Security Hardening

**Objective:** Close all critical security vulnerabilities

#### Tasks

**1.1 Rotate API Keys**
```bash
# Generate new keys from:
# - https://console.anthropic.com (Anthropic)
# - https://www.pexels.com/api (Pexels)
# - https://unsplash.com/developers (Unsplash)
# - https://portal.azure.com (Azure)
```

**1.2 Add API Authentication**
- File: `api_server.py`
- Add: `X-API-Key` header validation
- Store keys in database (hashed)
- Create admin endpoint to generate keys

```python
# Implementation approach
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def validate_api_key(api_key: str = Security(api_key_header)):
    # Validate against database
    if not await verify_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

**1.3 Fix Password Validation**
- File: `frontend/lib/auth.ts`
- Implement bcrypt password hashing
- Store hashed passwords in database
- Add password strength requirements

```typescript
// Implementation approach
import bcrypt from 'bcrypt';

// On registration
const hashedPassword = await bcrypt.hash(password, 12);

// On login
const isValid = await bcrypt.compare(password, user.hashedPassword);
```

**1.4 Generate Proper Secrets**
```bash
# Generate NEXTAUTH_SECRET
openssl rand -base64 32

# Update docker-compose.yml to use env var
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
```

**1.5 Restrict CORS**
- File: `api_server.py`
- Remove localhost:* wildcards
- Add production domain
- Environment-based configuration

**1.6 Add Rate Limiting**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/pipeline/run")
@limiter.limit("10/minute")
async def run_pipeline(...):
    ...
```

**Tests:**
```bash
pytest tests/security/ -v
```

---

### Day 3-5: Database Integration

**Objective:** Replace JSON files with proper database persistence

#### Tasks

**2.1 Run Prisma Migrations**
```bash
cd frontend
npx prisma migrate dev --name init
npx prisma generate
```

**2.2 Create Python Database Client**
- File: `src/db/client.py`
- Use `asyncpg` for PostgreSQL
- Connection pooling
- Transaction support

```python
# Implementation approach
import asyncpg

class Database:
    pool: asyncpg.Pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=os.getenv("DATABASE_URL"),
            min_size=5,
            max_size=20
        )

    async def create_campaign(self, user_id: str, data: dict) -> str:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                """INSERT INTO campaigns (user_id, name, url, status)
                   VALUES ($1, $2, $3, $4) RETURNING id""",
                user_id, data['name'], data['url'], 'DRAFT'
            )
```

**2.3 Update Pipeline to Use Database**
- File: `src/pipeline/orchestrator.py`
- Replace: `save_to_json()` → `db.save_campaign()`
- Add: User ID association
- Add: Transaction wrapping

**2.4 Add Campaign CRUD API**
```python
@app.post("/api/campaigns")
async def create_campaign(request: CampaignRequest, user_id: str = Depends(get_user)):
    campaign_id = await db.create_campaign(user_id, request.dict())
    return {"id": campaign_id}

@app.get("/api/campaigns")
async def list_campaigns(user_id: str = Depends(get_user)):
    return await db.get_user_campaigns(user_id)
```

**2.5 User Isolation**
- All queries filtered by `user_id`
- Ownership validation on mutations
- Row-level security in PostgreSQL

**Tests:**
```bash
pytest tests/integration/test_database.py -v
```

---

### Day 6-7: Fix Broken Tests

**Objective:** Green test suite as regression baseline

#### Tasks

**3.1 Fix Import Error**
- File: `tests/unit/test_social_proof_collector.py`
- Update imports to match current module structure

**3.2 Fix Failing Tests**
- `test_with_existing_customers` - Check expected behavior
- `test_with_website_traffic` - Check expected behavior
- `test_career_product_detection` - Check expected behavior

**3.3 Rename Conflicting Enums**
- File: `src/analyzers/ab_test_planner.py`
- Rename: `TestElement` → `ABTestElement`
- Rename: `TestPriority` → `ABTestPriority`

**3.4 Add Missing Tests**
```python
# tests/integration/test_temporal_workflow.py
@pytest.mark.asyncio
async def test_workflow_starts_and_completes():
    """Verify Temporal workflow runs end-to-end."""
    ...

# tests/integration/test_campaign_persistence.py
@pytest.mark.asyncio
async def test_campaign_saved_to_database():
    """Verify campaign data persists to PostgreSQL."""
    ...
```

**Target:** 195+ tests passing, 0 failing

---

## PHASE 2: CORE PIPELINE (Days 11-20)

### Day 8-10: Image Composition

**Objective:** Render actual ad images with text overlays

#### Tasks

**4.1 Add PIL Integration**
- File: `src/composers/image_renderer.py`
- Download stock image
- Apply text overlay
- Handle brand colors

```python
from PIL import Image, ImageDraw, ImageFont
import httpx

class ImageRenderer:
    def __init__(self, brand_colors: dict):
        self.primary_color = brand_colors.get('primary', '#000000')
        self.font_path = "assets/fonts/Inter-Bold.ttf"

    async def render(
        self,
        image_url: str,
        headline: str,
        primary_text: str,
        cta: str,
        format: str = "1:1"
    ) -> bytes:
        # Download image
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            img = Image.open(BytesIO(resp.content))

        # Resize for format
        dimensions = {"1:1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}
        img = self._crop_and_resize(img, dimensions[format])

        # Apply gradient overlay
        img = self._apply_gradient(img)

        # Add text
        draw = ImageDraw.Draw(img)
        self._add_headline(draw, headline)
        self._add_body(draw, primary_text)
        self._add_cta(draw, cta)

        # Return bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
```

**4.2 Multi-Format Export**
- 1:1 (1080×1080) - Feed
- 4:5 (1080×1350) - Optimal feed
- 9:16 (1080×1920) - Stories

**4.3 Brand Color Extraction**
```python
from colorthief import ColorThief

def extract_brand_colors(logo_url: str) -> dict:
    # Download logo, extract dominant colors
    ...
```

**4.4 Storage Integration**
- Upload rendered images to S3/R2
- Return public URLs
- Cache for reuse

**Tests:**
```python
# tests/unit/test_image_renderer.py
def test_renders_correct_dimensions():
    renderer = ImageRenderer({})
    result = renderer.render_sync(image_url, "Test", "Body", "CTA", "1:1")
    img = Image.open(BytesIO(result))
    assert img.size == (1080, 1080)
```

---

### Day 11-13: Pipeline Integration

**Objective:** End-to-end flow with database persistence

#### Tasks

**5.1 Update Temporal Workflow**
```python
# src/temporal/workflows/ad_pipeline.py

@workflow.defn
class AdPipelineWorkflow:
    @workflow.run
    async def run(self, config: PipelineConfig) -> PipelineResult:
        # Extract brand
        brand = await workflow.execute_activity(
            extract_brand_activity,
            config.url,
            start_to_close_timeout=timedelta(minutes=5)
        )

        # Save to database (new)
        await workflow.execute_activity(
            save_brand_to_db_activity,
            config.campaign_id,
            brand
        )

        # Generate copy
        variants = await workflow.execute_activity(
            generate_copy_activity,
            brand,
            config.num_variants
        )

        # Save variants to database (new)
        await workflow.execute_activity(
            save_variants_to_db_activity,
            config.campaign_id,
            variants
        )

        # Match images
        matches = await workflow.execute_activity(
            match_images_activity,
            variants
        )

        # Compose ads (new - actually render images)
        composed = await workflow.execute_activity(
            compose_ads_activity,
            variants,
            matches,
            brand.assets
        )

        # Save composed ads to database (new)
        await workflow.execute_activity(
            save_composed_ads_activity,
            config.campaign_id,
            composed
        )

        # Update campaign status
        await workflow.execute_activity(
            update_campaign_status_activity,
            config.campaign_id,
            "READY"
        )

        return PipelineResult(
            campaign_id=config.campaign_id,
            variant_count=len(variants),
            status="READY"
        )
```

**5.2 Connect Frontend to Database**
```typescript
// frontend/app/campaigns/page.tsx

async function getCampaigns() {
  const session = await getServerSession(authOptions);
  const campaigns = await prisma.campaign.findMany({
    where: { userId: session.user.id },
    include: { variants: true },
    orderBy: { createdAt: 'desc' }
  });
  return campaigns;
}
```

**5.3 Real-time Updates**
- SSE for workflow progress (already implemented)
- Database polling for campaign status
- Optimistic UI updates

---

### Day 14-15: HITL Dashboard

**Objective:** Approve/reject with persistence

#### Tasks

**6.1 Connect to Real Data**
```typescript
// frontend/app/campaigns/[id]/page.tsx

export default async function CampaignPage({ params }) {
  const campaign = await prisma.campaign.findUnique({
    where: { id: params.id },
    include: {
      variants: true,
      brandProfile: true
    }
  });

  return <CampaignEditor campaign={campaign} />;
}
```

**6.2 Approval Persistence**
```typescript
// API route
export async function POST(req: Request) {
  const { variantId, status } = await req.json();

  await prisma.variant.update({
    where: { id: variantId },
    data: { status } // 'APPROVED' | 'REJECTED'
  });

  return Response.json({ success: true });
}
```

**6.3 Download Approved Ads**
```typescript
async function downloadApproved(campaignId: string) {
  const approved = await prisma.variant.findMany({
    where: {
      campaignId,
      status: 'APPROVED'
    }
  });

  // Create ZIP with ad images
  const zip = new JSZip();
  for (const variant of approved) {
    const img = await fetch(variant.composedUrl);
    zip.file(`${variant.id}.png`, await img.blob());
  }

  return zip.generateAsync({ type: 'blob' });
}
```

---

## PHASE 3: PLATFORM INTEGRATION (Days 21-35)

### Day 16-20: Meta OAuth & Publishing

**Objective:** Publish real ads to Meta

#### Tasks

**7.1 OAuth Implementation**
```python
# src/connectors/meta_oauth.py

class MetaOAuth:
    def __init__(self):
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")
        self.redirect_uri = os.getenv("META_REDIRECT_URI")

    def get_auth_url(self, state: str) -> str:
        return (
            f"https://www.facebook.com/v18.0/dialog/oauth"
            f"?client_id={self.app_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&state={state}"
            f"&scope=ads_management,ads_read"
        )

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code
                }
            )
            return resp.json()
```

**7.2 Ad Publishing**
```python
# src/connectors/meta_publisher.py

class MetaPublisher:
    async def create_campaign(self, account_id: str, name: str) -> str:
        resp = await self.client.post(
            f"https://graph.facebook.com/v18.0/act_{account_id}/campaigns",
            data={
                "name": name,
                "objective": "OUTCOME_TRAFFIC",
                "status": "PAUSED",
                "special_ad_categories": []
            }
        )
        return resp.json()["id"]

    async def create_ad(self, adset_id: str, creative_id: str) -> str:
        resp = await self.client.post(
            f"https://graph.facebook.com/v18.0/act_{self.account_id}/ads",
            data={
                "name": f"BrandTruth Ad {datetime.now().isoformat()}",
                "adset_id": adset_id,
                "creative": {"creative_id": creative_id},
                "status": "PAUSED"
            }
        )
        return resp.json()["id"]
```

### Day 21-25: Performance Ingestion

**Objective:** Track real ad performance

#### Tasks

**8.1 Metrics Pull**
```python
# src/connectors/meta_insights.py

class MetaInsights:
    async def get_ad_insights(self, ad_id: str, date_range: tuple) -> dict:
        resp = await self.client.get(
            f"https://graph.facebook.com/v18.0/{ad_id}/insights",
            params={
                "fields": "impressions,clicks,spend,ctr,cpm,actions",
                "time_range": json.dumps({
                    "since": date_range[0],
                    "until": date_range[1]
                })
            }
        )
        return resp.json()
```

**8.2 Store in Database**
```python
async def save_performance_snapshot(campaign_id: str, metrics: dict):
    await db.execute(
        """INSERT INTO performance_snapshots
           (campaign_id, impressions, clicks, spend, ctr, cpm, recorded_at)
           VALUES ($1, $2, $3, $4, $5, $6, NOW())""",
        campaign_id,
        metrics['impressions'],
        metrics['clicks'],
        metrics['spend'],
        metrics['ctr'],
        metrics['cpm']
    )
```

---

## PHASE 4: POLISH (Days 36-45)

### Day 26-30: Proof Pack & Error Handling

**Objective:** Audit trail and graceful failures

### Day 31-35: Monitoring & Documentation

**Objective:** Production observability

---

## TEST STRATEGY

### Unit Tests
- All new modules have tests
- Target: 80% coverage on new code

### Integration Tests
- API endpoint tests
- Database CRUD tests
- External API mocks

### E2E Tests
- Full pipeline flow
- Frontend user journeys

### Contract Tests
- API schema validation
- Temporal activity contracts

### Regression Tests
- Run full suite before each commit
- CI/CD pipeline enforcement

```bash
# Run before committing
make test

# Run with coverage
make test-cov

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

---

## DEFINITION OF DONE

For each task:
- [ ] Code complete
- [ ] Tests written and passing
- [ ] No new security issues
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Merged to main

---

## RISK MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Meta API changes | Low | High | Abstract behind interface |
| Rate limits hit | Medium | Medium | Implement backoff, caching |
| Image rendering slow | Medium | Medium | Queue + CDN caching |
| Database bottleneck | Low | High | Connection pooling, indexes |

---

**Plan Owner:** Development Team
**Review:** Weekly on Fridays
