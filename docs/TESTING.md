# BrandTruth AI - Testing Guide

## Overview

BrandTruth AI has comprehensive test coverage across both backend and frontend:

| Layer | Tool | Tests | Coverage |
|-------|------|-------|----------|
| Backend Unit | pytest | 88 | Models, analyzers, generators |
| Backend Integration | pytest | 27 | All API endpoints |
| Backend E2E | pytest | 8 | Complete workflows |
| Backend Contract | pytest | 29 | OpenAPI schema validation |
| Frontend Component | Jest + RTL | 47 | React components |
| Frontend E2E | Playwright | 56 | Browser automation |
| **Total** | | **255** | **Full stack** |

---

## Quick Start

### Run All Tests

```bash
# Backend tests
cd /path/to/adplatform
make test

# Frontend tests (component)
cd frontend
npm test

# Frontend tests (E2E) - requires dev server
npm run dev &          # Terminal 1
npm run test:e2e       # Terminal 2
```

---

## Backend Tests

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (88)
│   ├── test_competitor_intel.py
│   ├── test_fatigue_predictor.py
│   ├── test_performance_predictor.py
│   ├── test_proof_pack.py
│   └── test_video_generator.py
├── integration/             # Integration tests (27)
│   └── test_api_endpoints.py
├── contract/                # Contract tests (25)
│   ├── test_openapi_schema.py
│   ├── test_pact_consumer.py
│   └── test_pact_provider.py
└── e2e/                     # E2E tests (8)
    └── test_complete_flows.py
```

### Commands

```bash
# All tests
make test

# By category
make test-unit      # Unit tests only
make test-int       # Integration tests only
make test-e2e       # E2E tests only
make test-contract  # Contract/schema tests
make test-pact      # Pact consumer tests

# With coverage
make test-cov

# Specific file
pytest tests/unit/test_video_generator.py -v

# Specific test
pytest tests/unit/test_video_generator.py::TestVideoGenerator::test_generate_ugc_video -v
```

### Test Markers

```python
@pytest.mark.unit        # Unit tests
@pytest.mark.integration # Integration tests
@pytest.mark.e2e         # End-to-end tests
@pytest.mark.contract    # Contract/schema tests
@pytest.mark.pact        # Pact consumer tests
@pytest.mark.slow        # Slow tests (>5s)
@pytest.mark.api         # Tests requiring API keys
```

---

## Contract Tests

Contract tests ensure the API contract between frontend and backend remains stable.

### OpenAPI Schema Tests

Validates that API responses match the OpenAPI specification.

```bash
# Run OpenAPI schema tests
make test-contract

# Or directly
pytest tests/contract/test_openapi_schema.py -v -m contract
```

**What's tested:**
- Schema validity (has info, paths, responses)
- Endpoint response structure
- Request validation (required fields, types)
- Content types (JSON responses)
- Error responses (422, 400)

**Test Classes:**

| Class | Tests | Description |
|-------|-------|-------------|
| `TestOpenAPISchemaValidity` | 5 | Schema structure |
| `TestEndpointSchemaCompliance` | 14 | Response validation |
| `TestRequestValidation` | 5 | Input validation |
| `TestResponseTypes` | 2 | Content types |
| `TestCriticalEndpoints` | 3 | Core API testing |

### Pact Consumer Tests (Optional)

Consumer-driven contracts using Pact. Install first:

```bash
pip install pact-python
```

Run Pact tests:

```bash
# Generate contracts
make test-pact

# Verify against running server
python tests/contract/test_pact_provider.py --provider-url http://localhost:8000
```

**When to use Pact:**
- Multiple teams working on frontend/backend
- API consumed by external clients
- Need guaranteed backwards compatibility

**Files:**
- `test_pact_consumer.py` - Defines frontend expectations
- `test_pact_provider.py` - Verifies backend satisfies contracts
- `pacts/` - Generated contract JSON files

---

## Frontend Tests

### Directory Structure

```
frontend/
├── __tests__/               # Component tests (47)
│   ├── landing-page.test.tsx
│   └── dashboard.test.tsx
├── e2e/                     # E2E tests (56)
│   ├── landing.spec.ts
│   ├── dashboard.spec.ts
│   ├── features.spec.ts
│   └── user-flows.spec.ts
├── jest.config.js           # Jest configuration
├── jest.setup.ts            # Jest setup & mocks
└── playwright.config.ts     # Playwright configuration
```

### Component Tests (Jest)

```bash
# Run all component tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage
```

**What's tested:**
- Landing page: Navigation, Hero, Features, Stats, Footer
- Dashboard: URL input, Settings, Filters, Variants grid, Export
- Accessibility: Heading hierarchy, Links, Keyboard navigation

### E2E Tests (Playwright)

```bash
# Start dev server first (Terminal 1)
npm run dev

# Run E2E tests (Terminal 2)
npm run test:e2e

# With UI mode
npm run test:e2e:ui

# Headed mode (see browser)
npm run test:e2e:headed

# Specific file
npx playwright test e2e/landing.spec.ts

# Specific test
npx playwright test -g "displays main headline"
```

**What's tested:**
- All 11 pages load correctly
- Navigation flows work
- User interactions (click, type, submit)
- Mobile responsiveness
- Accessibility basics
- Performance (load times)
- Error handling

### Browser Coverage

Current configuration tests Chromium only (for speed). To enable cross-browser:

```typescript
// playwright.config.ts
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 12'] } },
]
```

---

## Test Fixtures

### Backend Fixtures (conftest.py)

```python
@pytest.fixture
async def async_client():
    """Async HTTP client for API testing."""
    
@pytest.fixture
def sample_ad_content():
    """Sample ad content for testing."""
    
@pytest.fixture
def sample_brand_profile():
    """Sample brand profile for testing."""
    
@pytest.fixture
def temp_output_dir():
    """Temporary directory for file outputs."""
```

### Frontend Fixtures (jest.setup.ts)

```typescript
// Mocked automatically:
- next/navigation (useRouter, usePathname, useSearchParams)
- next/link
- next/image
- window.matchMedia
- IntersectionObserver
- ResizeObserver
```

---

## Writing New Tests

### Backend Unit Test

```python
# tests/unit/test_my_feature.py
import pytest
from src.my_module import MyClass

class TestMyClass:
    @pytest.mark.unit
    async def test_my_method(self):
        obj = MyClass()
        result = await obj.my_method()
        assert result.status == "success"
```

### Backend Contract Test

```python
# tests/contract/test_my_endpoint.py
import pytest

class TestMyEndpointSchema:
    @pytest.mark.contract
    @pytest.mark.asyncio
    async def test_response_schema(self, async_client):
        response = await async_client.get("/my-endpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert "required_field" in data
        assert isinstance(data["required_field"], str)
```

### Frontend Component Test

```typescript
// __tests__/my-component.test.tsx
import { render, screen } from '@testing-library/react'
import MyComponent from '../app/my-component/page'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

### Frontend E2E Test

```typescript
// e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test'

test.describe('My Feature', () => {
  test('works correctly', async ({ page }) => {
    await page.goto('/my-feature')
    await expect(page.locator('h1')).toContainText('My Feature')
  })
})
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: make test

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && npm ci
      - run: cd frontend && npm test
      - run: cd frontend && npx playwright install --with-deps
      - run: cd frontend && npm run build && npm run start &
      - run: cd frontend && npm run test:e2e
```

---

## Troubleshooting

### Backend Tests Fail

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Check API keys
echo $ANTHROPIC_API_KEY
```

### Frontend Component Tests Fail

```bash
# Clear Jest cache
npm test -- --clearCache

# Check Node version
node --version  # Should be 18+

# Reinstall dependencies
rm -rf node_modules && npm install
```

### Frontend E2E Tests Fail

```bash
# Ensure dev server is running
npm run dev  # Must show "Ready on http://localhost:3001"

# Check port in playwright.config.ts matches
# baseURL: 'http://localhost:3001'

# Reinstall Playwright browsers
npx playwright install
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Port 3000 in use" | Dev server on 3001, update playwright.config.ts |
| "Cannot find module" | Run `npm install` |
| "Timeout" errors | Increase timeout in playwright.config.ts |
| "Element not found" | Add `waitForLoadState('domcontentloaded')` |

---

## Test Metrics

### Current Coverage (v1.0)

| Category | Files | Tests | Pass Rate |
|----------|-------|-------|-----------|
| Backend Unit | 5 | 88 | 100% |
| Backend Integration | 1 | 27 | 100% |
| Backend E2E | 1 | 8 | 100% |
| Backend Contract | 1 | 29 | 100% |
| Frontend Component | 2 | 47 | 100% |
| Frontend E2E | 4 | 56 | 100% |
| **Total** | **14** | **255** | **100%** |

### Execution Time

| Suite | Duration |
|-------|----------|
| Backend (all) | ~3.5 min |
| Backend Contract | ~5 sec |
| Frontend Component | ~1.2 sec |
| Frontend E2E | ~17 sec |
| **Total** | ~4 min |

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/)
- [Pact Documentation](https://docs.pact.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
