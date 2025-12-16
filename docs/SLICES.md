# BrandTruth AI - Execution Slices

**Version:** 1.0  
**Last Updated:** December 2025

---

## Overview

Each slice is designed to be:
- **Completable in 1-2 days**
- **Produce visible, testable output**
- **Deployable independently**
- **Buildable in dependency order**

---

## Slice Summary

| Slice | Name | Status | Days | Dependencies |
|-------|------|--------|------|--------------|
| 1 | Brand Extractor | ✅ Complete | 2 | None |
| 2 | Copy Generator | 🔲 Next | 2 | Slice 1 |
| 3 | Image Matcher | 🔲 Pending | 2 | Slice 2 |
| 4 | Ad Composer | 🔲 Pending | 2 | Slice 3 |
| 5 | HITL Dashboard | 🔲 Pending | 2 | Slice 4 |
| 6 | Sentiment Extractor | 🔲 Pending | 2 | Slice 1 |
| 7 | Pipeline Integration | 🔲 Pending | 2 | Slices 1-6 |
| 8 | Meta API Connector | 🔲 Pending | 2 | Slice 7 |
| 9 | Performance Ingestion | 🔲 Pending | 2 | Slice 8 |
| 10 | Proof Pack Generator | 🔲 Pending | 2 | Slice 9 |

**Total Estimated Days:** 20

---

## Slice 1: Brand Extractor ✅ COMPLETE

### Goal
Extract brand truth from any website URL into a structured BrandProfile.

### Input
```python
url: str  # e.g., "https://careerfied.ai"
```

### Output
```python
BrandProfile:
  brand_name: str
  tagline: str
  website_url: str
  industry: str
  value_propositions: list[str]
  target_audience: str
  claims: list[BrandClaim]  # with risk levels
  social_proof: list[SocialProof]
  tone_markers: list[ToneMarker]  # with confidence
  key_terms: list[str]
  avoided_terms: list[str]
  assets: BrandAssets
  confidence_score: float
```

### Tech Stack
- Playwright (web scraping)
- BeautifulSoup (HTML parsing)
- Claude API (extraction)
- Pydantic (data models)
- Modal (deployment)

### Key Files
```
src/extractors/scraper.py         # Playwright scraping
src/extractors/brand_extractor.py # Claude extraction
src/models/brand_profile.py       # Data models
modal_app.py                      # Serverless deployment
run_local.py                      # Local testing
```

### Success Criteria
- [x] Run on 5 different websites
- [x] Get usable BrandProfile for 4/5
- [x] JSON output with all required fields
- [x] Confidence score reflects quality

### Commands
```bash
# Local
python run_local.py https://careerfied.ai

# Modal
modal run modal_app.py --url https://careerfied.ai
```

---

## Slice 2: Copy Generator 🔲 NEXT

### Goal
Generate constrained ad copy variants from a BrandProfile.

### Input
```python
brand_profile: BrandProfile
campaign_params: CampaignParams
  objective: str      # "signups" | "traffic" | "awareness"
  audience: str       # "job seekers in India"
  platform: str       # "meta" | "linkedin"
  tone_override: str  # optional
  offer: str          # optional, e.g., "Free ATS review"
```

### Output
```python
list[CopyVariant]:
  id: str
  headline: str           # 5-10 words
  primary_text: str       # 2-4 sentences
  cta: str                # "Get Started" etc.
  angle: str              # "pain" | "benefit" | "curiosity" | "social_proof" | "direct"
  persona: str            # Target persona name
  emotion: str            # Primary emotion targeted
  proof_sources: list[str]  # URLs of claims used
  platform_compliance: dict  # Character counts, etc.
```

### Tech Stack
- Claude API (generation)
- Pydantic (models)

### Implementation Plan
```
1. Create CopyVariant model
2. Build constraint prompt from BrandProfile:
   - Include only safe claims (low/medium risk)
   - Include tone markers
   - Include key terms
   - Include avoided terms
3. Generate 10 variants with Claude
4. Parse and validate output
5. Tag with angle, persona, emotion
6. Check platform compliance (char limits)
```

### Prompt Structure
```
You are an expert ad copywriter. Generate ad copy for {platform}.

BRAND CONSTRAINTS:
{brand_profile.to_prompt_context()}

CAMPAIGN:
- Objective: {objective}
- Audience: {audience}
- Offer: {offer}

RULES:
- Only use claims from the provided list
- Match the brand tone
- Use key terms where natural
- Never use avoided terms
- Stay within character limits:
  - Headline: max 40 chars
  - Primary text: max 125 chars (Meta)

Generate 10 variants covering these angles:
- 2 pain-focused
- 2 benefit-focused
- 2 curiosity/question
- 2 social proof
- 2 direct offer

Return JSON array...
```

### Success Criteria
- [ ] Generate 10 variants from Careerfied BrandProfile
- [ ] 7/10 variants usable without edits
- [ ] All variants pass platform compliance
- [ ] Each variant tagged with angle/persona

### Files to Create
```
src/models/copy_variant.py
src/generators/copy_generator.py
tests/test_copy_generator.py
```

---

## Slice 3: Image Matcher 🔲 PENDING

### Goal
Find brand-aligned stock images for each copy variant.

### Input
```python
copy_variant: CopyVariant
brand_profile: BrandProfile
count: int = 3  # Images per variant
```

### Output
```python
list[ImageMatch]:
  id: str
  copy_variant_id: str
  image_url: str
  source: str           # "unsplash" | "pexels"
  search_terms: list[str]
  mood: str             # "positive" | "tense" | "neutral"
  composition: str      # "centered" | "rule_of_thirds" | "minimal"
  text_safe_areas: list[str]  # "top" | "bottom" | "left" | "right"
  match_score: float    # 0-1, how well it matches
  license: str
  attribution: str
```

### Tech Stack
- Unsplash API
- Pexels API (backup)
- Claude API (search term generation + scoring)

### Implementation Plan
```
1. Create ImageMatch model
2. Generate search terms from copy variant:
   - Extract key concepts
   - Map emotions to visual terms
   - Consider audience demographics
3. Query Unsplash API
4. Score each image with Claude:
   - Mood alignment
   - Composition analysis
   - Text overlay feasibility
5. Return top 3 matches
```

### Success Criteria
- [ ] For 10 copy variants → 8/10 have at least 1 good match
- [ ] No random/unrelated images
- [ ] All images have clear text-safe areas

### Files to Create
```
src/models/image_match.py
src/composers/image_matcher.py
tests/test_image_matcher.py
```

---

## Slice 4: Ad Composer 🔲 PENDING

### Goal
Render final ad images by combining copy + stock images.

### Input
```python
copy_variant: CopyVariant
image_match: ImageMatch
brand_assets: BrandAssets
formats: list[str] = ["1:1", "4:5", "9:16"]
```

### Output
```python
ComposedAd:
  id: str
  copy_variant_id: str
  image_match_id: str
  assets: dict[str, str]  # {"1:1": "url", "4:5": "url", "9:16": "url"}
  composition_metadata: dict
    layout: str
    text_position: str
    logo_position: str
    overlay_opacity: float
```

### Tech Stack
- Sharp (Node.js) or Pillow (Python)
- Or: HTML templates + Playwright screenshot

### Implementation Plan
```
1. Download stock image
2. Resize/crop for each format:
   - 1:1: 1080x1080
   - 4:5: 1080x1350
   - 9:16: 1080x1920
3. Apply overlay (darken for text readability)
4. Add text layers:
   - Headline (largest)
   - Primary text (if space)
   - CTA button
5. Add logo (corner)
6. Export as PNG
7. Upload to storage (R2)
```

### Layout Templates
```
TEMPLATE 1: Full bleed with bottom text
┌────────────────────┐
│                    │
│   [Image fills]    │
│                    │
├────────────────────┤
│ Headline           │
│ Primary text       │
│ [CTA]   [Logo]     │
└────────────────────┘

TEMPLATE 2: Split layout
┌──────────┬─────────┐
│          │Headline │
│  Image   │Text     │
│          │[CTA]    │
└──────────┴─────────┘
```

### Success Criteria
- [ ] Render 30 ads (10 variants × 3 sizes)
- [ ] 25+ look professional
- [ ] Text is readable on all
- [ ] Logo visible and correct

### Files to Create
```
src/models/composed_ad.py
src/composers/ad_composer.py
src/composers/templates/
tests/test_ad_composer.py
```

---

## Slice 5: HITL Dashboard 🔲 PENDING

### Goal
Web interface for reviewing and approving generated ads.

### Input
- Generated ads from pipeline

### Output
- Approved/rejected status per ad
- Edited copy (if user changes)
- Downloadable ZIP of approved ads

### Tech Stack
- Next.js (React)
- Tailwind CSS
- Vercel deployment

### Features (MVP)
```
1. Grid view of all ads
2. Click to expand/preview
3. Approve / Reject buttons
4. Inline copy editing
5. Regenerate button (with constraints)
6. Download approved (ZIP)
7. Basic campaign info header
```

### UI Mockup
```
┌─────────────────────────────────────────────────────────────┐
│ Campaign: Careerfied Launch           [Download Approved]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Ad 1   │  │  Ad 2   │  │  Ad 3   │  │  Ad 4   │       │
│  │ [image] │  │ [image] │  │ [image] │  │ [image] │       │
│  │         │  │         │  │         │  │         │       │
│  │ [✓] [✗] │  │ [✓] [✗] │  │ [✓] [✗] │  │ [✓] [✗] │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  Ad 5   │  │  Ad 6   │  │  Ad 7   │  │  Ad 8   │       │
│  │         │  │         │  │         │  │         │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Success Criteria
- [ ] Review 30 ads in < 5 minutes
- [ ] Approve 10, download ZIP
- [ ] Edit copy inline
- [ ] Regenerate works

### Files to Create
```
dashboard/
  app/
    page.tsx
    campaigns/[id]/page.tsx
  components/
    AdCard.tsx
    AdGrid.tsx
    ApprovalControls.tsx
  package.json
```

---

## Slice 6: Sentiment Extractor 🔲 PENDING

### Goal
Extract market sentiment to constrain copy generation.

### Input
```python
keywords: list[str]      # ["resume builder", "ATS", "job search"]
competitors: list[str]   # ["zety", "novoresume"] optional
```

### Output
```python
SentimentProfile:
  dominant_emotions: list[str]    # ["frustration", "hope", "skepticism"]
  winning_angles: list[str]       # ["time savings", "confidence"]
  blocked_angles: list[str]       # ["guaranteed results"]
  language_markers: list[str]     # ["ATS", "ghosted", "callback"]
  competitor_claims: list[str]    # What competitors say
  risk_posture: str               # "conservative" | "moderate" | "aggressive"
  sources: list[SentimentSource]
```

### Sources to Scrape
```
1. G2 / Capterra reviews (search by keyword)
2. Reddit threads (r/jobs, r/resumes, etc.)
3. Google SERP snippets
4. Meta Ad Library (competitor ads)
```

### Success Criteria
- [ ] Run on "resume builder" category
- [ ] Get actionable constraints
- [ ] Identify at least 3 winning angles
- [ ] Identify at least 2 blocked angles

### Files to Create
```
src/models/sentiment_profile.py
src/extractors/sentiment_extractor.py
src/extractors/review_scraper.py
src/extractors/reddit_scraper.py
```

---

## Slice 7: Pipeline Integration 🔲 PENDING

### Goal
Connect all slices into a single end-to-end workflow.

### Workflow
```
URL + CampaignParams
        │
        ▼
┌───────────────────┐
│  1. Brand Extract │ (Slice 1)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  2. Sentiment     │ (Slice 6)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  3. Generate Copy │ (Slice 2, constrained by 1+6)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  4. Match Images  │ (Slice 3)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  5. Compose Ads   │ (Slice 4)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  6. Dashboard     │ (Slice 5)
└───────────────────┘
        │
        ▼
    User Approves
        │
        ▼
    Download / Publish
```

### Success Criteria
- [ ] URL → Approved Ads in < 10 minutes
- [ ] Run full pipeline for Careerfied
- [ ] All intermediate artifacts saved
- [ ] Error handling at each step

### Files to Create
```
src/pipeline/orchestrator.py
src/pipeline/campaign_runner.py
modal_app.py (add run_pipeline function)
```

---

## Slice 8: Meta API Connector 🔲 PENDING

### Goal
Push approved ads to Meta Ads Manager.

### Input
```python
approved_ads: list[ComposedAd]
ad_account_id: str
campaign_settings: MetaCampaignSettings
  budget: float
  objective: str
  targeting: dict
```

### Output
```python
MetaDeployment:
  campaign_id: str
  adset_id: str
  ad_ids: list[str]
  status: str
  preview_urls: list[str]
```

### API Flow
```
1. Create Campaign (if not exists)
2. Create Ad Set (targeting, budget)
3. Upload creative images
4. Create Ads (copy + creative)
5. Set status to PAUSED (HITL will activate)
```

### Success Criteria
- [ ] Push 5 ads to test ad account
- [ ] All appear in Ads Manager
- [ ] Preview URLs work
- [ ] Status is PAUSED

### Files to Create
```
src/connectors/meta_connector.py
src/models/meta_deployment.py
```

---

## Slice 9: Performance Ingestion 🔲 PENDING

### Goal
Pull performance data from Meta for analysis.

### Input
```python
meta_ad_ids: list[str]
date_range: DateRange
```

### Output
```python
PerformanceSnapshot:
  ad_id: str
  meta_ad_id: str
  timestamp: datetime
  impressions: int
  clicks: int
  spend: float
  ctr: float
  cpm: float
  conversions: int
  health_score: int  # 0-100
  status: str        # "healthy" | "warning" | "critical"
```

### Health Score Logic
```python
def calculate_health(snapshot):
    score = 100
    
    # CTR check
    if snapshot.ctr < 0.5:
        score -= 30
    elif snapshot.ctr < 1.0:
        score -= 15
    
    # CPM check
    if snapshot.cpm > 20:
        score -= 25
    elif snapshot.cpm > 15:
        score -= 10
    
    # Delivery check
    if snapshot.impressions == 0 and snapshot.spend > 0:
        score -= 40
    
    return max(0, score)
```

### Success Criteria
- [ ] After 24 hours of running → See data in system
- [ ] Health scores calculated
- [ ] Trends visible

### Files to Create
```
src/connectors/performance_tracker.py
src/models/performance_snapshot.py
```

---

## Slice 10: Proof Pack Generator 🔲 PENDING

### Goal
Generate compliance documentation for each ad.

### Input
```python
ad: ComposedAd
brand_profile: BrandProfile
sentiment_profile: SentimentProfile
performance: PerformanceSnapshot  # optional
```

### Output
```python
ProofPack:
  ad_id: str
  generated_at: datetime
  
  brand_provenance: list[dict]
    claim: str
    source_url: str
    risk_level: str
    
  sentiment_sources: list[dict]
    insight: str
    source: str
    url: str
    
  image_license: dict
    source: str
    photographer: str
    license: str
    url: str
    
  approval: dict
    approved_by: str
    approved_at: datetime
    
  platform_ids: dict
    meta_ad_id: str
    meta_campaign_id: str
    
  performance: dict  # if available
    impressions: int
    ctr: float
    health: str
```

### Output Formats
- JSON (machine-readable)
- PDF (human-readable, downloadable)

### Success Criteria
- [ ] Every approved ad has proof pack
- [ ] PDF downloadable from dashboard
- [ ] All claims have source citations

### Files to Create
```
src/proof/proof_generator.py
src/proof/pdf_renderer.py
src/models/proof_pack.py
```

---

## Timeline

### Week 1 (Days 1-7)
- [x] Day 1-2: Slice 1 - Brand Extractor ✅
- [ ] Day 3-4: Slice 2 - Copy Generator
- [ ] Day 5-6: Slice 3 - Image Matcher
- [ ] Day 7: Buffer / testing

### Week 2 (Days 8-14)
- [ ] Day 8-9: Slice 4 - Ad Composer
- [ ] Day 10-11: Slice 5 - HITL Dashboard
- [ ] Day 12-13: Slice 6 - Sentiment Extractor
- [ ] Day 14: Buffer / testing

### Week 3 (Days 15-21)
- [ ] Day 15-16: Slice 7 - Pipeline Integration
- [ ] Day 17-18: Slice 8 - Meta API Connector
- [ ] Day 19-20: Slice 9 - Performance Ingestion
- [ ] Day 21: Slice 10 - Proof Pack

### Week 4 (Days 22-28)
- [ ] Run real ads for Careerfied
- [ ] Fix bugs
- [ ] Iterate based on results
- [ ] First customer conversation

---

## Definition of Done (Per Slice)

- [ ] Code complete
- [ ] Local test passes
- [ ] Modal deployment works
- [ ] Success criteria met
- [ ] Documentation updated
- [ ] Committed to git

---

**Document Owner:** Subrahmanya  
**Last Updated:** December 2025
