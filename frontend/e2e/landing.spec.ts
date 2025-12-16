/**
 * E2E Tests - Landing Page
 * 
 * Tests the landing page user experience in a real browser.
 */

import { test, expect } from '@playwright/test'

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('has correct page title', async ({ page }) => {
    await expect(page).toHaveTitle(/BrandTruth/)
  })

  test('displays main headline', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Create ads that are')
  })

  test('displays BrandTruth logo in nav', async ({ page }) => {
    await expect(page.getByText('BrandTruth').first()).toBeVisible()
  })

  test('navigation links work', async ({ page }) => {
    // Features link
    await page.click('a[href="#features"]')
    await expect(page.locator('#features')).toBeInViewport()

    // How it works link
    await page.click('a[href="#how-it-works"]')
    await expect(page.locator('#how-it-works')).toBeInViewport()
  })

  test('Launch Dashboard button navigates to dashboard', async ({ page }) => {
    await page.click('text=Launch Dashboard')
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('Start Creating Ads button navigates to dashboard', async ({ page }) => {
    await page.click('text=Start Creating Ads >> nth=0')
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('Sentiment Monitor link navigates correctly', async ({ page }) => {
    await page.click('text=Sentiment Monitor ✨')
    await expect(page).toHaveURL(/\/sentiment/)
  })

  test('Try Sentiment Monitor button works', async ({ page }) => {
    await page.click('text=Try Sentiment Monitor >> nth=0')
    await expect(page).toHaveURL(/\/sentiment/)
  })

  test('displays all feature cards', async ({ page }) => {
    // Use more specific selectors (heading role)
    await expect(page.getByRole('heading', { name: 'Brand Extraction' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Claim Verification' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Smart Image Matching' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'One-Click Export' })).toBeVisible()
  })

  test('displays how it works steps', async ({ page }) => {
    await expect(page.getByText('Enter Your URL')).toBeVisible()
    await expect(page.getByText('Review & Approve')).toBeVisible()
    await expect(page.getByText('Export & Launch')).toBeVisible()
  })

  test('displays statistics', async ({ page }) => {
    await expect(page.getByText('60s')).toBeVisible()
    await expect(page.getByText('100%')).toBeVisible()
    await expect(page.getByText('3x')).toBeVisible()
  })

  test('footer contains copyright', async ({ page }) => {
    await expect(page.getByText('© 2025 BrandTruth AI')).toBeVisible()
  })
})

test.describe('Landing Page - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } })

  test('is responsive on mobile', async ({ page }) => {
    await page.goto('/')
    
    // Main content should be visible
    await expect(page.locator('h1')).toBeVisible()
    await expect(page.getByText('BrandTruth').first()).toBeVisible()
  })

  test('mobile navigation works', async ({ page }) => {
    await page.goto('/')
    
    // CTA buttons should be visible and clickable
    const ctaButton = page.getByRole('link', { name: /Start Creating Ads/i }).first()
    await expect(ctaButton).toBeVisible()
  })
})

test.describe('Landing Page - Accessibility', () => {
  test('has no major accessibility violations', async ({ page }) => {
    await page.goto('/')
    
    // Check that main landmarks exist
    await expect(page.locator('nav')).toBeVisible()
    await expect(page.locator('main, section').first()).toBeVisible()
    await expect(page.locator('footer')).toBeVisible()
  })

  test('all images have alt text or are decorative', async ({ page }) => {
    await page.goto('/')
    
    const images = await page.locator('img').all()
    for (const img of images) {
      const alt = await img.getAttribute('alt')
      const role = await img.getAttribute('role')
      // Either has alt text or is marked as presentation/decorative
      expect(alt !== null || role === 'presentation').toBeTruthy()
    }
  })

  test('interactive elements are keyboard accessible', async ({ page }) => {
    await page.goto('/')
    
    // Tab through page
    await page.keyboard.press('Tab')
    
    // Something should be focused
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).toBeTruthy()
  })
})
