# BrandTruth AI - API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication required (MVP). Production will use API keys.

## Response Format

All responses are JSON with the following structure:

**Success:**
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Error:**
```json
{
  "detail": "Error message"
}
```

---

## Endpoints

### Root

#### GET /
Get API information.

**Response:**
```json
{
  "message": "BrandTruth AI API",
  "version": "1.0.0",
  "status": "100% Complete - All 15 Slices!",
  "endpoints": {...}
}
```

#### GET /health
Health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Performance Prediction (Slice 9)

#### POST /predict
Predict ad performance before launch.

**Request:**
```json
{
  "headline": "Stop Getting Rejected by ATS",
  "primary_text": "Build resumes that get interviews",
  "cta": "Get Started"
}
```

**Response:**
```json
{
  "score": 78,
  "tier": "good",
  "summary": "Score: 78/100 (Good) | CTR: above_average"
}
```

#### POST /predict/demo
Run demo prediction.

---

### Attention Analysis (Slice 10)

#### POST /attention/analyze
Analyze visual attention patterns.

**Request:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "headline": "Test Headline",
  "cta": "Learn More"
}
```

**Response:**
```json
{
  "score": 72,
  "summary": "Attention Score: 72/100 | First Focus: headline",
  "first_focus": "headline",
  "recommendations": ["Consider moving CTA higher"]
}
```

#### POST /attention/demo
Run demo analysis.

---

### Multi-Format Export (Slice 11)

#### GET /export/formats
Get available export formats.

**Response:**
```json
{
  "formats": [
    {"id": "meta_feed", "name": "Meta Feed", "width": 1200, "height": 628},
    {"id": "meta_story", "name": "Meta Story", "width": 1080, "height": 1920},
    ...
  ],
  "total": 9
}
```

#### POST /export/all
Export ad in multiple formats.

**Request:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "headline": "Test Headline",
  "cta": "Learn More",
  "formats": ["meta_feed", "instagram_square"],
  "create_zip": true
}
```

**Response:**
```json
{
  "success": true,
  "exported": 2,
  "zip": "/output/export_20240115_100000.zip"
}
```

#### POST /export/demo
Run demo export.

---

### Competitor Intelligence (Slice 12)

#### POST /intel/analyze
Analyze competitor advertising strategies.

**Request:**
```json
{
  "brand_name": "Careerfied",
  "industry": "career",
  "competitor_names": ["Resume.io", "Zety", "Indeed"]
}
```

**Response:**
```json
{
  "summary": "Analyzed 3 competitors with 15 ads | $15,000/mo estimated market spend",
  "competitors": [
    {"name": "Resume.io", "ads": 5, "spend": 5000, "threat": "medium"}
  ],
  "copy_patterns": [
    {"type": "social_proof", "frequency": 8}
  ],
  "insights": [
    {"title": "Video Format Gap", "action": "Test video ads"}
  ],
  "recommendations": ["A/B test headlines against competitors"]
}
```

#### POST /intel/demo/{industry}
Run demo for industry (career, saas, ecommerce).

---

### AI Video Generation (Slice 13)

#### POST /video/generate
Generate AI UGC-style video ad.

**Request:**
```json
{
  "brand_name": "Careerfied",
  "product_description": "AI resume builder",
  "target_audience": "Job seekers",
  "key_benefits": ["ATS-optimized", "Templates", "Feedback"],
  "cta": "Get Started",
  "style": "ugc",
  "aspect_ratio": "9:16",
  "avatar_style": "casual",
  "include_captions": true,
  "include_music": true
}
```

**Response:**
```json
{
  "video_id": "vid_abc123",
  "title": "Careerfied - UGC Ad",
  "status": "complete",
  "duration_seconds": 25,
  "resolution": "1080x1920",
  "script": {
    "hook": "POV: You just discovered Careerfied...",
    "body": ["Point 1", "Point 2"],
    "cta": "Link in bio!",
    "scenes": [...]
  },
  "avatar": {"id": "avatar_maya", "name": "Maya", "style": "casual"},
  "music": {"name": "TikTok Trending", "mood": "fun", "bpm": 140},
  "predictions": {
    "engagement_score": 75,
    "hook_strength": 80
  }
}
```

#### POST /video/demo/{style}
Run demo for style (ugc, testimonial, demo, explainer, storytelling, listicle).

#### GET /video/styles
Get available video styles.

#### GET /video/avatars
Get available AI avatars.

#### GET /video/music
Get available music tracks.

---

### Creative Fatigue (Slice 14)

#### POST /fatigue/predict
Predict when ad needs refreshing.

**Request:**
```json
{
  "ad_id": "my_ad_001",
  "days_running": 18,
  "frequency": 3.2,
  "reach": 50000,
  "audience_size": 150000,
  "industry": "saas"
}
```

**Response:**
```json
{
  "fatigue_score": 55,
  "level": "moderate",
  "summary": "⚠️ Fatigue: 55/100 (moderate) | Refresh in 7 days",
  "days_until": 7,
  "recommendations": ["Refresh headline", "Expand targeting"]
}
```

#### POST /fatigue/demo/{scenario}
Run demo for scenario (fresh, healthy, moderate, high, critical).

---

### Proof Pack (Slice 15)

#### POST /proof/generate
Generate compliance documentation.

**Request:**
```json
{
  "ad_id": "my_ad_001",
  "campaign_name": "Launch Campaign",
  "brand_name": "Careerfied",
  "headline": "Stop Getting Rejected",
  "primary_text": "Build resumes that work",
  "cta": "Get Started",
  "claims": [
    {"claim": "Join 10,000+ users", "source_text": "User surveys", "risk_level": "low"}
  ]
}
```

**Response:**
```json
{
  "pack_id": "proof_abc123",
  "summary": "✅ Compliance: PASS | Claims: 1/1 verified | Brand Safety: 95/100",
  "compliance": "pass",
  "safety_score": 95,
  "action_items": []
}
```

#### POST /proof/demo
Run demo proof pack.

---

### Sentiment Monitoring (Slice 6)

#### POST /sentiment/check
Check brand sentiment.

**Request:**
```json
{
  "brand_name": "Careerfied",
  "scenario": "normal"
}
```

**Response:**
```json
{
  "health": "🟢 Healthy",
  "auto_pause": false
}
```

#### POST /sentiment/demo/{scenario}
Run demo for scenario (normal, crisis, positive).

---

### Meta Publishing (Slice 8)

#### POST /meta/publish
Publish ad to Meta.

**Request:**
```json
{
  "headline": "Stop Getting Rejected",
  "primary_text": "Build resumes that work",
  "cta": "Get Started",
  "link_url": "https://careerfied.ai",
  "page_id": "my_page",
  "campaign_name": "Launch",
  "daily_budget": 1000
}
```

**Response:**
```json
{
  "success": true,
  "ad_id": "meta_ad_123"
}
```

#### POST /meta/demo
Run demo publish.

---

### Pipeline (Slice 7)

#### POST /pipeline/run
Run full ad generation pipeline.

**Request:**
```json
{
  "url": "https://careerfied.ai",
  "num_variants": 5,
  "platform": "meta",
  "formats": ["square"]
}
```

**Response:**
```json
{
  "job_id": "job_abc123",
  "stage": "complete",
  "variants": [...]
}
```

#### GET /jobs
List pipeline jobs.

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Rate Limits

Currently no rate limits (MVP). Production will implement:
- 100 requests/minute for standard endpoints
- 10 requests/minute for generation endpoints
