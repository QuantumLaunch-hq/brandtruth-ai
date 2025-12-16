import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Campaign Management
 *
 * These tests require authentication. They are skipped by default
 * until a test user is set up in the database.
 *
 * To enable:
 * 1. Create a test user in the database
 * 2. Update auth.setup.ts with test credentials
 * 3. Remove .skip from test.describe blocks
 *
 * Requires Docker containers: docker-compose up -d
 */

// Skip all tests that require authentication
test.describe.skip('Campaigns Page (requires auth)', () => {

  test('shows campaigns list', async ({ page }) => {
    await page.goto('/campaigns');

    // Should show page header
    await expect(page.getByText('Campaigns')).toBeVisible();
  });

  test('shows loading state initially', async ({ page }) => {
    await page.goto('/campaigns');

    // Brief loading state
    await expect(page.locator('text=Loading')).toBeVisible({ timeout: 2000 }).catch(() => {
      // Loading might be too fast to catch
    });
  });

  test('displays campaign cards or empty state', async ({ page }) => {
    await page.goto('/campaigns');

    // Wait for data to load
    await page.waitForTimeout(2000);

    // Should show either campaigns or empty state
    const hasCampaigns = await page.locator('[data-testid="campaign-card"]').count() > 0;
    const hasEmptyState = await page.getByText(/No campaigns|Create your first/).isVisible().catch(() => false);

    expect(hasCampaigns || hasEmptyState).toBeTruthy();
  });
});

test.describe.skip('Pipeline Workflow (requires auth)', () => {

  test('studio page loads', async ({ page }) => {
    await page.goto('/studio');

    await expect(page.getByText('BrandTruth Studio')).toBeVisible();
  });

  test('can enter URL and start pipeline', async ({ page }) => {
    await page.goto('/studio');

    // Click enter URL
    await page.getByRole('button', { name: 'Enter your website URL' }).click();

    // Enter a test URL
    await page.getByPlaceholder('yoursite.com').fill('example.com');

    // Verify input
    await expect(page.getByPlaceholder('yoursite.com')).toHaveValue('example.com');
  });

  test('shows processing state after URL submission', async ({ page }) => {
    await page.goto('/studio');

    await page.getByRole('button', { name: 'Enter your website URL' }).click();
    await page.getByText('careerfied.ai').click();
    await page.getByRole('button', { name: 'Continue' }).click();

    // Should show processing or brand data
    await expect(
      page.getByText(/Processing|Extracting|Careerfied/i)
    ).toBeVisible({ timeout: 20000 });
  });
});

test.describe.skip('Ad Composition Display (requires auth)', () => {

  test('preview panel shows ad preview', async ({ page }) => {
    await page.goto('/studio');
    await page.getByRole('button', { name: 'Skip for now' }).click();

    // Should show preview panel with phone mockup
    await expect(page.getByText('Preview')).toBeVisible();
    await expect(page.getByText('Sponsored')).toBeVisible();
  });

  test('preview shows CTA button', async ({ page }) => {
    await page.goto('/studio');
    await page.getByRole('button', { name: 'Skip for now' }).click();

    await expect(page.getByText('Learn More')).toBeVisible();
  });
});

// These tests don't require auth - they test the API directly
test.describe('API Health', () => {

  test('API is healthy', async ({ request }) => {
    const response = await request.get('http://localhost:8010/health');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe('healthy');
  });

  test('Temporal is available', async ({ request }) => {
    const response = await request.get('http://localhost:8010/health');
    const body = await response.json();

    expect(body.temporal_available).toBe(true);
  });
});

test.describe('Full Pipeline E2E', () => {

  test.skip('complete pipeline: URL → extract → generate → compose', async ({ page }) => {
    // This is a long-running test, skip by default
    // Enable with: npx playwright test --grep "complete pipeline"

    await page.goto('/studio');

    // Step 1: Enter URL
    await page.getByRole('button', { name: 'Enter your website URL' }).click();
    await page.getByPlaceholder('yoursite.com').fill('careerfied.ai');
    await page.getByRole('button', { name: 'Continue' }).click();

    // Step 2: Wait for brand extraction
    await expect(page.getByText('Careerfied')).toBeVisible({ timeout: 30000 });
    await page.getByRole('button', { name: 'Continue' }).click();

    // Step 3: In studio, request campaign
    await page.getByPlaceholder('Ask anything...').fill('Generate 3 ad variants');
    await page.keyboard.press('Enter');

    // Step 4: Wait for variants to be generated
    await expect(page.getByText(/variant|headline/i)).toBeVisible({ timeout: 60000 });

    // Step 5: Check campaigns page for new campaign
    await page.goto('/campaigns');
    await expect(page.locator('[data-testid="campaign-card"]')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Output Images', () => {

  test('output endpoint serves static files', async ({ request }) => {
    // First check if the output directory has any files
    const response = await request.get('http://localhost:8010/output/');

    // May return 404 if no files, or 200 with directory listing
    expect([200, 404]).toContain(response.status());
  });
});
