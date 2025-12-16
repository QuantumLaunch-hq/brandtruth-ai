# BrandTruth AI - Documentation Index

**Project:** BrandTruth AI  
**Location:** `/Users/satish/qlp-projects/adplatform`  
**Last Updated:** December 15, 2025

---

## Quick Links

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [PRD.md](./PRD.md) | Complete product requirements | Understanding what we're building |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design & tech stack | Before making technical decisions |
| [SLICES.md](./SLICES.md) | Execution plan & slice details | Daily development guidance |
| [TRACKER.md](./TRACKER.md) | Progress & metrics | Daily/weekly check-ins |
| [TESTING.md](./TESTING.md) | Test suite & coverage | Running or writing tests |
| [DECISIONS.md](./DECISIONS.md) | Key decisions made | Before changing direction |
| [MARKET_ANALYSIS.md](./MARKET_ANALYSIS.md) | Market & competitive intel | Business context |

---

## Document Summaries

### PRD.md
The complete Product Requirements Document. Contains:
- Executive summary
- Problem statement
- Product vision
- Target customer
- Functional requirements (9.1-9.10)
- Non-functional requirements
- MVP success criteria
- Validation budget
- Monetization model

### ARCHITECTURE.md
Technical system architecture. Contains:
- High-level architecture diagram
- Component details (Extraction, Generation, Control, Platform layers)
- Data architecture (schemas, storage)
- API design
- Deployment architecture
- Security considerations
- Cost estimates

### SLICES.md
Detailed execution slices. Contains:
- 10 slices with:
  - Goal
  - Input/Output specs
  - Tech stack
  - Implementation plan
  - Success criteria
  - Files to create
- Timeline (20 days)
- Definition of done

### TRACKER.md
Progress tracking. Contains:
- Overall progress percentage
- Slice-by-slice status
- Weekly scorecards
- Cost tracking
- MVP success criteria status
- Blockers & risks
- Daily log

### TESTING.md
Complete testing guide. Contains:
- Test suite overview (255 tests total)
- Backend testing (pytest - 152 tests)
- Frontend component testing (Jest + RTL - 47 tests)
- Frontend E2E testing (Playwright - 56 tests)
- Contract testing (OpenAPI schema validation)
- Configuration files
- Writing new tests
- CI/CD integration
- Troubleshooting

### DECISIONS.md
Decision log. Contains:
- Strategic decisions (positioning, platform focus, etc.)
- Technical decisions (language, infra, databases)
- Business decisions (pricing, target customer)
- Deferred decisions
- Review schedule

### MARKET_ANALYSIS.md
Market intelligence. Contains:
- Market size & opportunity
- Target segment analysis
- Competitive landscape
- Positioning matrix
- Pricing analysis
- Go-to-market strategy
- Unit economics
- Risk assessment

---

## Related Project Files

| File | Purpose |
|------|---------|
| `../README.md` | Project overview & quick start |
| `../CLAUDE.md` | AI assistant guide |
| `../pyproject.toml` | Python project config |
| `../run_local.py` | Local testing CLI |
| `../modal_app.py` | Serverless deployment |

---

## Documentation Standards

### Updating Documents

1. **TRACKER.md** - Update daily during active development
2. **SLICES.md** - Update when slice status changes
3. **DECISIONS.md** - Update when significant decisions are made
4. **Other docs** - Update when content becomes stale

### Naming Conventions

- Use UPPERCASE for markdown files
- Use descriptive names (not `doc1.md`)
- Keep in `/docs` folder

### Formatting

- Use tables for structured data
- Use code blocks for technical content
- Include "Last Updated" dates
- Add document owner

---

## Version History

| Date | Change | Author |
|------|--------|--------|
| Dec 15, 2025 | Added TESTING.md, contract tests (255 total) | Claude + Subrahmanya |
| Dec 14, 2025 | Initial documentation created | Claude + Subrahmanya |

---

**Document Owner:** Subrahmanya
