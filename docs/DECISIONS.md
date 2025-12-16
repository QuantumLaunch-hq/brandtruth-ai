# BrandTruth AI - Key Decisions Log

**Last Updated:** December 2025

---

## Decision Framework

For each decision, we document:
- **Context:** Why this decision was needed
- **Options:** What alternatives were considered
- **Decision:** What was chosen
- **Rationale:** Why this option was selected
- **Consequences:** Expected impacts
- **Status:** Active / Superseded / Revisit

---

## Strategic Decisions

### D001: Product Positioning

**Date:** December 2025  
**Status:** Active

**Context:**  
Needed to define what BrandTruth AI is and isn't in a crowded ad-tech space.

**Options:**
1. Generic AI ad generator (compete on speed)
2. Brand-safe ad system (compete on trust)
3. Full-service ad platform (compete on features)

**Decision:** Option 2 - Brand-safe ad system

**Rationale:**
- Speed-focused tools are commoditized
- Trust is underserved in market
- Explainability is a moat
- Smaller scope, faster to build

**Consequences:**
- Must invest in proof/provenance features
- Slower generation is acceptable
- HITL is non-negotiable
- Marketing message is differentiated

---

### D002: Initial Platform Focus

**Date:** December 2025  
**Status:** Active

**Context:**  
Which ad platform to target first.

**Options:**
1. Meta (Facebook + Instagram)
2. Google Ads
3. LinkedIn
4. TikTok

**Decision:** Option 1 - Meta first

**Rationale:**
- Largest ad platform
- Well-documented API
- Visual ads (good for showcasing)
- Broad SMB adoption
- Lower CPMs than LinkedIn

**Consequences:**
- Need Meta Business Account setup
- Need to learn Meta Marketing API
- LinkedIn and Google deferred to Phase 2

---

### D003: No Video Ads (MVP)

**Date:** December 2025  
**Status:** Active

**Context:**  
Should we support video ad generation?

**Options:**
1. Static images only
2. Static images + simple video
3. Full video support

**Decision:** Option 1 - Static images only

**Rationale:**
- Video is 10x more complex
- Stock video licensing is harder
- Video composition requires more compute
- 80% of SMB ads are still static
- Can add later when validated

**Consequences:**
- Simpler tech stack
- Faster time to market
- Miss video-only placements
- Revisit after MVP validation

---

### D004: Mandatory Human-in-the-Loop

**Date:** December 2025  
**Status:** Active

**Context:**  
Should we allow fully autonomous ad launch?

**Options:**
1. Full automation (AI launches ads)
2. HITL required for all launches
3. HITL optional (user setting)

**Decision:** Option 2 - HITL always required

**Rationale:**
- Trust is our core value prop
- Brand risk too high for automation
- Legal liability concerns
- Builds user confidence
- Can relax later if proven safe

**Consequences:**
- Slower than competitors
- More friction for users
- Higher trust/satisfaction
- Non-negotiable in MVP

---

## Technical Decisions

### D005: Python as Primary Language

**Date:** December 2025  
**Status:** Active

**Context:**  
Which language for backend development.

**Options:**
1. Python
2. Node.js/TypeScript
3. Go

**Decision:** Option 1 - Python

**Rationale:**
- Best AI/ML library ecosystem
- Anthropic SDK is Python-first
- Playwright works well
- Pydantic for data modeling
- Faster prototyping

**Consequences:**
- Slightly slower runtime (acceptable)
- Rich ecosystem
- Good Modal support

---

### D006: Modal for Serverless Compute

**Date:** December 2025  
**Status:** Active

**Context:**  
Where to run backend compute (scraping, AI calls, image processing).

**Options:**
1. Modal
2. AWS Lambda
3. Google Cloud Run
4. Self-hosted (Railway, Render)

**Decision:** Option 1 - Modal

**Rationale:**
- Pay-per-use (great for MVP)
- Native Python support
- Easy GPU access for image processing
- Simple deployment model
- Good developer experience

**Consequences:**
- Vendor lock-in (acceptable for MVP)
- Learning curve (minimal)
- Cost-efficient at low scale

---

### D007: Supabase for Database

**Date:** December 2025  
**Status:** Active

**Context:**  
Database for campaigns, ads, performance data.

**Options:**
1. Supabase (Postgres)
2. PlanetScale (MySQL)
3. MongoDB Atlas
4. Firebase

**Decision:** Option 1 - Supabase

**Rationale:**
- Postgres (industry standard)
- Built-in auth
- Row-level security
- Realtime subscriptions
- Generous free tier
- Good Vercel integration

**Consequences:**
- SQL-based (structured data)
- Auth handled for free
- Easy to scale

---

### D008: Unsplash for Stock Images

**Date:** December 2025  
**Status:** Active

**Context:**  
Source for stock images in ads.

**Options:**
1. Unsplash API (free)
2. Pexels API (free)
3. Shutterstock API (paid)
4. AI-generated images (DALL-E, etc.)

**Decision:** Option 1 - Unsplash primary, Pexels backup

**Rationale:**
- Free API with generous limits
- High quality images
- No attribution required for ads
- Commercial use allowed
- Well-documented API

**Consequences:**
- Limited to existing photos
- No custom generation
- May need paid source later for variety

---

### D009: No AI-Generated Images (MVP)

**Date:** December 2025  
**Status:** Active

**Context:**  
Should we use DALL-E/Midjourney for ad images?

**Options:**
1. Stock photos only
2. AI-generated images only
3. Hybrid (both)

**Decision:** Option 1 - Stock photos only

**Rationale:**
- AI images often look "off" for ads
- Licensing is unclear
- Brand authenticity concerns
- Stock is proven effective
- Simpler to implement

**Consequences:**
- Dependent on stock availability
- More realistic look
- Revisit when AI quality improves

---

### D010: HTML-to-Screenshot for Ad Composition

**Date:** December 2025  
**Status:** Active

**Context:**  
How to render final ad images.

**Options:**
1. HTML templates + Playwright screenshot
2. Pure image manipulation (Pillow/Sharp)
3. Design tool API (Canva, Figma)

**Decision:** Option 1 - HTML templates + screenshot

**Rationale:**
- Easier layout control
- CSS for typography
- Responsive templates
- Playwright already in stack
- More flexible than pixel manipulation

**Consequences:**
- Slight performance overhead
- Pixel-perfect control
- Easy to iterate on designs

---

## Business Decisions

### D011: SaaS Pricing Model

**Date:** December 2025  
**Status:** Tentative (validate with customers)

**Context:**  
How to charge for the service.

**Options:**
1. Subscription (flat monthly)
2. Usage-based (per ad)
3. % of ad spend
4. Freemium

**Decision:** Option 1 - Subscription with usage tiers

**Rationale:**
- Predictable revenue
- Simple to understand
- No perverse incentives
- Aligned with value (more ads = more value)

**Proposed Tiers:**
- Free: 5 ads one-time
- Starter: $99/mo, 50 ads
- Growth: $299/mo, 200 ads
- Scale: $799/mo, unlimited

**Consequences:**
- Need to track usage
- Price anchoring important
- Will revisit based on customer feedback

---

### D012: Careerfied as First Customer

**Date:** December 2025  
**Status:** Active

**Context:**  
Who to build for first.

**Options:**
1. Build for hypothetical customer
2. Build for Careerfied (own product)
3. Build for external beta users

**Decision:** Option 2 - Careerfied first

**Rationale:**
- Zero sales cycle
- Full access to brand
- Immediate feedback
- Real ads running
- Proof of concept for others

**Consequences:**
- May over-fit to career niche
- Fast iteration
- Built-in case study

---

## Deferred Decisions

### D013: Vector Database Choice

**Status:** Deferred until Slice 7+

**Options:**
1. Pinecone
2. Weaviate
3. Qdrant
4. Supabase pgvector

**Notes:** Will decide when implementing AI aging/memory features.

---

### D014: Multi-tenant Architecture

**Status:** Deferred until first paying customer

**Options:**
1. Single database, RLS
2. Database per tenant
3. Schema per tenant

**Notes:** Start with single-tenant, add multi-tenant when needed.

---

## Decision Review Schedule

| Decision | Review Date | Trigger |
|----------|-------------|---------|
| D003 (No Video) | Post-MVP | Customer demand |
| D009 (No AI Images) | Q2 2026 | AI quality improvement |
| D011 (Pricing) | First 10 customers | Revenue data |

---

**Document Owner:** Subrahmanya  
**Review Frequency:** Monthly or after major milestones
