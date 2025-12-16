# BrandTruth AI - Product Requirements Document (PRD)

**Version:** 1.0  
**Last Updated:** December 2025  
**Status:** In Development (Slice 1 Complete)

---

## 1. Executive Summary

BrandTruth AI is an AI-native advertising system that engineers brand-safe, market-aligned, performance-ready ads using:

- **Brand truth** extracted directly from source websites
- **Market sentiment** intelligence from reviews, forums, competitors
- **Licensed stock imagery** with visual reasoning
- **Human-in-the-loop** approval (mandatory)
- **Real-time performance** diagnosis
- **Auto-actions** (pause, rotate, throttle) with guardrails
- **Persistent vector-based memory** that ages the system

### Core Positioning

> **We do not generate ads. We engineer trustable advertising systems that get better every week.**

### One-Line Positioning

> **Brand-safe advertising, engineered from market truth.**

---

## 2. Problem Statement

Modern advertising suffers from:

| Problem | Impact |
|---------|--------|
| **Creative fatigue** | Endless refresh cycles, diminishing returns |
| **Brand risk** | Generic AI outputs erode trust |
| **Opaque automation** | Marketers don't trust black boxes |
| **Slow iteration** | Agencies and teams can't experiment fast enough |

### Existing Tool Gaps

Current tools:
- Optimize for speed, not trust
- Generate content, not systems
- Forget everything after each prompt

**There is no system that combines brand fidelity, market intelligence, explainability, and compounding learning.**

---

## 3. Product Vision

Build an AI system that behaves like a **senior creative + media strategist**:

1. It **understands the brand** (extracted truth, not assumptions)
2. It **understands the market mood** (sentiment, not guesses)
3. It **explains its decisions** (proof, not magic)
4. It **improves with experience** (memory, not reset)
5. It **earns permission** to touch budget (trust, not control)

---

## 4. Target Customer

### Primary (MVP)

| Attribute | Value |
|-----------|-------|
| Segment | SMB & mid-market advertisers |
| Ad Spend | $3k–$50k/month on Meta ads |
| Pain Point | Slightly dissatisfied with creatives |
| Priority | Care about brand safety |

### Secondary (Phase 2+)

- B2B SaaS marketers (LinkedIn)
- Technical founders running their own ads
- Small agencies seeking efficiency

### Anti-Personas (Not For)

- Large enterprises with in-house creative teams
- Agencies (as first customers)
- Brand-new businesses with no website presence

---

## 5. Core User Outcome

> **"I can launch brand-safe ads faster, with confidence, and trust the system to protect my budget."**

### Success Metrics (User Perspective)

- Time from idea to live ad: < 30 minutes
- Approval rate on generated ads: > 50%
- Performance vs baseline: within ±20%
- Trust in system decisions: Would recommend

---

## 6. Core Principles (Non-Negotiable)

| # | Principle | What It Means |
|---|-----------|---------------|
| 1 | **Brand Truth First** | Every ad grounded in actual brand claims |
| 2 | **Constrained AI > Generative AI** | AI operates within brand/market constraints |
| 3 | **Human Approval is Mandatory** | No autonomous launches ever |
| 4 | **Every Output Has Proof** | Full provenance for every ad |
| 5 | **The System Must Learn** | Performance feeds back into generation |
| 6 | **No Magic Without Explanation** | Every decision is explainable |

---

## 7. Platform Scope & Phasing

| Phase | Platforms | Ad Types | Timeline |
|-------|-----------|----------|----------|
| **Phase 1 (MVP)** | Meta (Facebook + Instagram) | Static image ads only | Weeks 1-4 |
| **Phase 2** | LinkedIn Sponsored Content | Static image ads | Weeks 5-8 |
| **Phase 3** | Google Search + Display | Text + static | Weeks 9-12 |

### Explicitly Out of Scope

❌ TikTok  
❌ Video ads  
❌ Influencer content  
❌ Programmatic display  
❌ Autonomous launch without approval

---

## 8. System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                   │
│                    (URL + Campaign Params)                          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Website    │  │   Reviews    │  │  Competitor  │              │
│  │   Scraper    │  │   Scraper    │  │   Monitor    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    Brand     │  │  Sentiment   │  │    Vector    │              │
│  │   Extractor  │  │   Analyzer   │  │    Memory    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CREATION LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    Copy      │  │    Image     │  │     Ad       │              │
│  │  Generator   │  │   Matcher    │  │   Composer   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONTROL LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    HITL      │  │   Proof      │  │    Auto      │              │
│  │  Dashboard   │  │    Pack      │  │   Actions    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PLATFORM LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Meta API    │  │ LinkedIn API │  │ Google API   │              │
│  │  Connector   │  │  Connector   │  │  Connector   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Functional Requirements

### 9.1 Campaign Ingestion

**Inputs:**
- Website URL (required)
- Campaign objective (awareness/traffic/conversions)
- Target audience persona
- Platform (Meta only in MVP)
- Tone constraints (optional)
- Offer / CTA (optional)

**Outputs:**
- Campaign object with metadata
- Execution plan

---

### 9.2 Brand Truth Extraction

**System Must:**
- Scrape key pages (home, product, pricing, FAQ, testimonials)
- Extract:
  - Value propositions
  - Claims (with risk classification)
  - Tone markers
  - Social proof
- Flag risky claims automatically

**Outputs:**
- `BrandProfile` object
- Source-cited facts
- Asset library (logos, product images)

---

### 9.3 Market Sentiment Intelligence

**Sources:**
- Reviews (G2, Trustpilot, App Store)
- Reddit / forums
- SERP snippets
- Competitor ads (Meta Ad Library)

**Outputs:**
- Dominant emotions
- Winning angles
- Blocked angles
- Language markers
- Market risk posture

> **Key:** Sentiment constrains generation, it does not decorate it.

---

### 9.4 Creative Generation (Claude)

**Generates:**
- Platform-specific copy variants
- Tagged with:
  - Persona
  - Pain
  - Promise
  - Proof
  - Emotional intent

**Rules:**
- Must obey BrandProfile constraints
- Must obey Sentiment constraints
- Must be reproducible (prompt + hash)

---

### 9.5 Visual Intelligence (Stock Images)

**System Must:**
- Use licensed stock images only (Unsplash, Pexels)
- Classify images by:
  - Mood
  - Composition
  - Professionalism
  - Text-safe areas
- Select images aligned to persona + sentiment

> **Rule:** No random images. Ever.

---

### 9.6 Creative Composition

**Renders:**
- 1:1 (1080×1080) - Feed
- 4:5 (1080×1350) - Feed optimal
- 9:16 (1080×1920) - Stories/Reels

**Requirements:**
- Safe typography
- Logo placement rules
- Platform-safe margins
- Text overlay limits (<20% for Meta)

---

### 9.7 HITL Approval Dashboard

**Must Support:**
- Grid view of generated ads
- Approve / Reject per ad
- Inline copy edits
- Regenerate with constraints
- Full audit trail

> **Critical:** Launch is blocked without explicit approval.

---

### 9.8 Proof Pack (Critical Differentiator)

Every ad must produce a Proof Pack containing:

| # | Element | Purpose |
|---|---------|---------|
| 1 | Brand provenance | Source URLs for all claims |
| 2 | Claim compliance checks | Risk assessment |
| 3 | Rendered creative | Final ad image |
| 4 | Platform IDs | Meta ad/adset/campaign IDs |
| 5 | Delivery confirmation | Upload status |
| 6 | Performance snapshot | Metrics once live |

> **Proof is first-class, not an afterthought.**

---

### 9.9 Real-Time Performance Analysis

**Ingest:**
- Impressions, clicks, spend
- CTR, CPM
- Delivery status
- Frequency

**Compute:**
- Health score (0–100)
- Failure classification:
  - Creative failure
  - Targeting failure
  - Platform failure
  - Tracking failure

---

### 9.10 Auto-Actions (Guardrailed)

**Hard-stop Auto-pause:**
- Rejected ads
- Spend > threshold with zero results
- Severe CPM spikes (>3x baseline)

**Soft Actions (Recommendations):**
- Throttle budget
- Rotate creative
- Recommend edits

**All Actions Must Be:**
- Explainable
- Logged
- Reversible
- HITL-controlled

---

## 10. Vector Intelligence & AI Aging

### Vector Memory Stores:
- Brand snippets
- Sentiment clusters
- Creative variants
- Approval edits
- Performance outcomes
- Policy events

### Enables:
- "Don't regenerate losers"
- "Reuse winning angles"
- Visual similarity reasoning
- Root-cause diagnostics
- System aging (gets smarter over time)

---

## 11. Multimodal Intelligence (Selective)

| Capability | Required? | Purpose |
|------------|-----------|---------|
| Text embeddings | ✅ Yes | Memory, search, similarity |
| Image embeddings (CLIP) | ✅ Yes | Visual matching |
| Video processing | ❌ No | Out of scope |
| Audio processing | ❌ No | Out of scope |
| Generative imagery | ❌ No | Use stock only |

> **Purpose:** Memory + reasoning, not creativity theatre.

---

## 12. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Deterministic outputs | Same input → reproducible output |
| Full observability | Logs for every decision |
| Idempotent jobs | Safe to retry |
| Cost visibility | Track AI/API costs per campaign |
| API key isolation | Per-customer secrets |

---

## 13. MVP Success Criteria (Falsifiable)

**Must hit 2 of 3:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| Approval rate | ≥50% | Ads approved / ads generated |
| Performance parity | ±20% of baseline | CPA, CTR vs manual ads |
| Paying customer | At least 1 at $299+ | Actual revenue |

> **Failure to hit → stop or pivot.**

---

## 14. Validation Budget

| Category | Budget |
|----------|--------|
| Infrastructure + AI | $150–300 |
| Stock images | $50–100 |
| Ad spend (testing) | $3k–5k |
| Pilot buffer | $500–1.5k |
| **Total** | **$4k–7k** |
| **Timeline** | **~60 days** |
| **Dev cost** | **$0** (Claude Code Max) |

---

## 15. Monetization Model

### Pricing Structure (Planned)

| Tier | Price | Includes |
|------|-------|----------|
| **Free** | $0 | 5 ads one-time |
| **Starter** | $99/month | 50 ads/month, 1 platform |
| **Growth** | $299/month | 200 ads/month, 2 platforms, auto-refresh |
| **Scale** | $799/month | Unlimited ads, all platforms, priority support |

### Revenue Model
- Subscription-based (SaaS)
- No % of ad spend (avoid perverse incentives)
- Usage-based overage for enterprise

---

## 16. Competitive Positioning

### vs. Jasper/Copy.ai
- They generate generic copy
- We constrain to brand truth

### vs. AdCreative.ai
- They optimize for CTR
- We optimize for brand safety + CTR

### vs. Agencies
- They cost $5k-50k/month
- We cost $99-799/month

### vs. Manual
- Manual: 4-8 hours per ad batch
- Us: 30 minutes per ad batch

---

## 17. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI generates off-brand content | Medium | High | Constraint layer + HITL |
| Performance worse than manual | Medium | High | A/B testing, gradual rollout |
| Platform API changes | Low | Medium | Abstraction layer |
| Stock image licensing issues | Low | High | Use only verified sources |
| Customer doesn't trust AI | Medium | Medium | Proof pack, transparency |

---

## 18. Future Roadmap (Post-MVP)

| Phase | Features | Timeline |
|-------|----------|----------|
| 2.1 | LinkedIn integration | Month 3 |
| 2.2 | Google Ads integration | Month 4 |
| 3.0 | Video ad support | Month 6 |
| 3.1 | Multi-language | Month 7 |
| 4.0 | White-label for agencies | Month 9 |
| 5.0 | Autonomous mode (with guardrails) | Month 12 |

---

## 19. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| BrandProfile | Structured extraction of brand truth from website |
| SentimentProfile | Market mood analysis from reviews/forums |
| Proof Pack | Documentation bundle for each ad |
| HITL | Human-in-the-loop approval |
| Health Score | 0-100 metric for ad performance |

### B. References

- Meta Marketing API: https://developers.facebook.com/docs/marketing-apis
- Unsplash API: https://unsplash.com/developers
- Anthropic Claude: https://docs.anthropic.com

---

**Document Owner:** Subrahmanya  
**Last Review:** December 2025  
**Next Review:** After MVP completion
