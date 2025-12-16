# BrandTruth AI - Frontend

Next.js 14 frontend for the BrandTruth AI advertising platform.

## 🚀 NEW: AI Studio (`/studio`)

The Studio is a completely redesigned, conversational AI interface that replaces the old form-based approach.

### Features

- **🎤 Conversational AI**: Talk naturally, get results
- **⌘K Command Palette**: Power user quick access
- **🎙️ Voice Input**: Speak your requests
- **📱 Live Platform Previews**: Real iPhone/Instagram/Facebook/TikTok frames
- **🔗 URL Intake Flow**: Extract real claims from your website
- **✅ Claim Verification**: Risk-scored claims (LOW/MEDIUM/HIGH)
- **📊 Smart Artifacts**: Interactive cards for hooks, audiences, budgets
- **💡 AI Suggestions**: Contextual next-action recommendations

### Try It

```bash
# Start backend
cd .. && python api_server.py

# Start frontend
npm run dev

# Open Studio
open http://localhost:3000/studio
```

### Sample Prompts

- "Generate hooks that convert"
- "Plan my ad budget"
- "Find my target audience"
- "Show me this as an Instagram ad"
- "Build a complete campaign"
- "Show me my extracted claims"

---

## Getting Started

```bash
# Install dependencies
npm install

# Install framer-motion (for animations)
npm install framer-motion

# Run development server
npm run dev

# Open http://localhost:3000
```

## Testing

### Test Summary

| Type | Tool | Tests | Description |
|------|------|-------|-------------|
| Component | Jest + RTL | 100+ | React component tests |
| E2E | Playwright | 70+ | Browser automation tests |
| **Total** | | **170+** | Full frontend coverage |

### Component Tests (Jest + React Testing Library)

```bash
# Run all component tests
npm test

# Run Studio tests only
npm test -- --testPathPattern=studio

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

**Tested Components:**
- Landing page
- Dashboard
- **Studio (NEW)**
  - Onboarding flow
  - Command palette
  - Platform previews
  - Chat interface

### E2E Tests (Playwright)

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Start dev server (Terminal 1)
npm run dev

# Run E2E tests (Terminal 2)
npm run test:e2e

# Run Studio E2E tests only
npm run test:e2e -- studio.spec.ts

# Run E2E tests with UI
npm run test:e2e:ui
```

**E2E Coverage:**
- Onboarding flow (URL → Extract → Review → Studio)
- Command palette (⌘K)
- Message sending
- Platform preview switching
- Full campaign workflow

### Run All Tests

```bash
npm run test:all
```

## Test Structure

```
frontend/
├── __tests__/                    # Component tests
│   ├── landing-page.test.tsx
│   ├── dashboard.test.tsx
│   └── studio/                   # NEW: Studio tests
│       ├── Onboarding.test.tsx
│       ├── CommandPalette.test.tsx
│       └── PlatformPreview.test.tsx
├── e2e/                          # E2E browser tests
│   ├── landing.spec.ts
│   ├── dashboard.spec.ts
│   ├── features.spec.ts
│   ├── user-flows.spec.ts
│   └── studio.spec.ts            # NEW: Studio E2E
├── jest.config.js
├── jest.setup.ts
└── playwright.config.ts
```

## Pages

| Page | Path | Description |
|------|------|-------------|
| Landing | `/` | Marketing landing page |
| **Studio** | `/studio` | **NEW: AI conversational interface** |
| Dashboard | `/dashboard` | Legacy ad creation workflow |
| Tools | `/tools` | All 23 tools grid |
| Hooks | `/hooks` | Hook generator |
| Landing Analyzer | `/landing` | Landing page analyzer |
| Budget | `/budget` | Budget simulator |
| Platforms | `/platforms` | Platform recommender |
| A/B Test | `/abtest` | A/B test planner |
| Audience | `/audience` | Audience targeting |
| Iterate | `/iterate` | Iteration assistant |
| Social | `/social` | Social proof collector |
| Predict | `/predict` | Performance prediction |
| Attention | `/attention` | Attention heatmap |
| Export | `/export` | Multi-format export |
| Intel | `/intel` | Competitor intelligence |
| Video | `/video` | AI video generator |
| Fatigue | `/fatigue` | Creative fatigue predictor |
| Proof | `/proof` | Compliance proof pack |
| Sentiment | `/sentiment` | Sentiment monitoring |
| Publish | `/publish` | Meta Ads publishing |

## Studio Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        /studio                                  │
├──────────────────────────────┬──────────────────────────────────┤
│      CONVERSATION            │         RIGHT PANEL              │
│                              │                                  │
│  [Brand Context Bar]         │   [Preview | Claims | Canvas]    │
│  ↓                           │                                  │
│  [AI Chat Messages]          │   📱 Live Phone Preview          │
│  ↓                           │   - Instagram                    │
│  [Smart Artifacts]           │   - Facebook                     │
│  ↓                           │   - TikTok                       │
│  [Quick Suggestions]         │                                  │
│                              │   OR                             │
│                              │                                  │
│                              │   ✓ Extracted Claims List        │
│                              │                                  │
│                              │   OR                             │
│                              │                                  │
│                              │   🎨 Created Items Canvas        │
│                              │                                  │
├──────────────────────────────┴──────────────────────────────────┤
│  [⌘K Commands]    [🎤 Voice]    [Type message...]   [Send]      │
└─────────────────────────────────────────────────────────────────┘
```

## Key Files

### Studio Components

| File | Description |
|------|-------------|
| `app/studio/page.tsx` | Main Studio interface |
| `app/studio/Onboarding.tsx` | URL intake & brand extraction flow |
| `app/studio/CommandPalette.tsx` | ⌘K quick command menu |
| `app/studio/PlatformPreview.tsx` | iPhone frame + Instagram/Facebook/TikTok previews |

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm test` | Run component tests |
| `npm run test:e2e` | Run Playwright E2E tests |
| `npm run test:all` | Run all tests |

## Tech Stack

- **Framework:** Next.js 14
- **Styling:** Tailwind CSS
- **Animations:** Framer Motion
- **Icons:** Lucide React
- **Component Tests:** Jest + React Testing Library
- **E2E Tests:** Playwright
- **Language:** TypeScript
