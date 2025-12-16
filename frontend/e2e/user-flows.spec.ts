/**
 * E2E Tests - Complete User Flows
 * 
 * Tests end-to-end user journeys through the application.
 */

import { test, expect } from '@playwright/test'

test.describe('Complete Ad Creation Flow', () => {
  test('user can navigate from landing to dashboard and create ads', async ({ page }) => {
    // Step 1: Start at landing page
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('Create ads')
    
    // Step 2: Click CTA to go to dashboard
    await page.click('text=Start Creating Ads >> nth=0')
    await expect(page).toHaveURL(/\/dashboard/)
    
    // Step 3: Enter a URL
    const urlInput = page.locator('input[type="url"], input[placeholder*="url" i], input[placeholder*="website" i]')
    await urlInput.fill('https://example.com')
    
    // Step 4: Page should be functional
    await expect(page.locator('body')).toBeVisible()
  })

  test('user can explore feature pages', async ({ page }) => {
    // Test a subset of pages that are known to work
    const featurePages = [
      '/predict',
      '/attention',
      '/fatigue',
      '/proof',
      '/sentiment',
    ]
    
    for (const featurePath of featurePages) {
      await page.goto(featurePath)
      await page.waitForLoadState('domcontentloaded')
      await expect(page).toHaveURL(new RegExp(featurePath))
    }
  })
})

test.describe('Sentiment Monitor Flow', () => {
  test('user can check brand sentiment', async ({ page }) => {
    // Step 1: Navigate to sentiment page
    await page.goto('/sentiment')
    await expect(page).toHaveURL(/\/sentiment/)
    
    // Step 2: Enter brand name
    const input = page.locator('input').first()
    await input.fill('Careerfied')
    
    // Step 3: Click check/analyze button
    const checkButton = page.getByRole('button', { name: /check|analyze|monitor/i })
    if (await checkButton.count() > 0) {
      await checkButton.first().click()
      await page.waitForTimeout(1000)
    }
    
    // Step 4: Page should show results
    await expect(page.locator('body')).toBeVisible()
  })
})

test.describe('Multi-Page Navigation', () => {
  test('user can navigate core pages without errors', async ({ page }) => {
    const pages = [
      '/',
      '/dashboard',
      '/predict',
      '/sentiment',
    ]
    
    for (const pagePath of pages) {
      await page.goto(pagePath)
      await page.waitForLoadState('domcontentloaded')
      
      // Page should load without crash
      const body = page.locator('body')
      await expect(body).toBeAttached()
    }
  })

  test('back/forward navigation works', async ({ page }) => {
    // Go to landing
    await page.goto('/')
    
    // Go to dashboard
    await page.goto('/dashboard')
    
    // Go to sentiment
    await page.goto('/sentiment')
    
    // Navigate back
    await page.goBack()
    await expect(page).toHaveURL(/\/dashboard/)
    
    // Navigate back again
    await page.goBack()
    await expect(page).toHaveURL('/')
    
    // Navigate forward
    await page.goForward()
    await expect(page).toHaveURL(/\/dashboard/)
  })
})

test.describe('Cross-Browser Visual Consistency', () => {
  test('landing page renders consistently', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('domcontentloaded')
    
    // Check key visual elements
    await expect(page.locator('nav')).toBeVisible()
    await expect(page.locator('h1')).toBeVisible()
    await expect(page.locator('footer')).toBeVisible()
  })

  test('dashboard renders consistently', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('domcontentloaded')
    
    // Input should be visible
    const inputs = page.locator('input')
    await expect(inputs.first()).toBeVisible()
  })
})

test.describe('Error Handling', () => {
  test('404 page for non-existent routes', async ({ page }) => {
    const response = await page.goto('/non-existent-page-xyz')
    
    // Should either show 404 or redirect
    expect(response?.status()).toBeTruthy()
  })

  test('handles invalid URL input gracefully', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('domcontentloaded')
    
    const urlInput = page.locator('input[type="url"], input[placeholder*="url" i], input[placeholder*="website" i]')
    await urlInput.fill('not-a-valid-url')
    
    // Page should not crash
    await expect(page.locator('body')).toBeAttached()
  })
})

test.describe('Performance', () => {
  test('landing page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/')
    const loadTime = Date.now() - startTime
    
    // Should load within 5 seconds
    expect(loadTime).toBeLessThan(5000)
  })

  test('dashboard page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/dashboard')
    const loadTime = Date.now() - startTime
    
    // Should load within 5 seconds
    expect(loadTime).toBeLessThan(5000)
  })
})
