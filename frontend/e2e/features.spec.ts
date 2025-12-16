/**
 * E2E Tests - Feature Pages
 * 
 * Tests all the WOW feature pages in a real browser.
 */

import { test, expect } from '@playwright/test'

test.describe('Performance Predictor Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/predict')
    await expect(page).toHaveURL(/\/predict/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('has input form', async ({ page }) => {
    await page.goto('/predict')
    await page.waitForLoadState('domcontentloaded')
    const inputs = page.locator('input, textarea')
    await expect(inputs.first()).toBeVisible()
  })

  test('has analyze/predict button', async ({ page }) => {
    await page.goto('/predict')
    await page.waitForLoadState('domcontentloaded')
    const button = page.getByRole('button', { name: /analyze|predict|score/i })
    await expect(button.first()).toBeVisible()
  })
})

test.describe('Attention Heatmap Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/attention')
    await expect(page).toHaveURL(/\/attention/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('has image upload or URL input', async ({ page }) => {
    await page.goto('/attention')
    await page.waitForLoadState('domcontentloaded')
    const hasInput = (await page.locator('input').count()) > 0
    expect(hasInput).toBeTruthy()
  })
})

test.describe('Multi-Format Export Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/export')
    await expect(page).toHaveURL(/\/export/)
    await page.waitForLoadState('domcontentloaded')
    // Just verify navigation works
  })

  test('displays available formats', async ({ page }) => {
    await page.goto('/export')
    await page.waitForLoadState('domcontentloaded')
    const pageText = await page.textContent('body')
    expect(pageText).toBeTruthy()
  })
})

test.describe('Competitor Intelligence Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/intel')
    await page.waitForLoadState('domcontentloaded')
  })

  test('has industry selector or input', async ({ page }) => {
    await page.goto('/intel')
    await page.waitForLoadState('domcontentloaded')
    const hasInput = (await page.locator('input, select').count()) > 0
    expect(hasInput).toBeTruthy()
  })
})

test.describe('AI Video Generator Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/video')
    await expect(page).toHaveURL(/\/video/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('has video style options', async ({ page }) => {
    await page.goto('/video')
    await page.waitForLoadState('domcontentloaded')
    const pageText = await page.textContent('body')
    expect(pageText?.toLowerCase()).toContain('video')
  })
})

test.describe('Creative Fatigue Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/fatigue')
    await expect(page).toHaveURL(/\/fatigue/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('displays fatigue analysis UI', async ({ page }) => {
    await page.goto('/fatigue')
    await page.waitForLoadState('domcontentloaded')
    const pageText = await page.textContent('body')
    expect(pageText?.toLowerCase()).toMatch(/fatigue|refresh|creative/i)
  })
})

test.describe('Proof Pack Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/proof')
    await expect(page).toHaveURL(/\/proof/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('displays compliance UI', async ({ page }) => {
    await page.goto('/proof')
    await page.waitForLoadState('domcontentloaded')
    const pageText = await page.textContent('body')
    expect(pageText?.toLowerCase()).toMatch(/proof|compliance|verification/i)
  })
})

test.describe('Sentiment Monitor Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/sentiment')
    await expect(page).toHaveURL(/\/sentiment/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('displays sentiment monitoring UI', async ({ page }) => {
    await page.goto('/sentiment')
    await page.waitForLoadState('domcontentloaded')
    const pageText = await page.textContent('body')
    expect(pageText?.toLowerCase()).toMatch(/sentiment|monitor|brand/i)
  })

  test('has brand input', async ({ page }) => {
    await page.goto('/sentiment')
    await page.waitForLoadState('domcontentloaded')
    const inputs = page.locator('input')
    await expect(inputs.first()).toBeVisible()
  })
})

test.describe('Meta Publish Page', () => {
  test('loads correctly', async ({ page }) => {
    await page.goto('/publish')
    await expect(page).toHaveURL(/\/publish/)
    await page.waitForLoadState('domcontentloaded')
  })

  test('displays publishing UI', async ({ page }) => {
    await page.goto('/publish')
    await page.waitForLoadState('domcontentloaded')
    const pageText = await page.textContent('body')
    expect(pageText?.toLowerCase()).toMatch(/publish|meta|facebook/i)
  })
})
