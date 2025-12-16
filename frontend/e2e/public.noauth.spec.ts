import { test, expect } from '@playwright/test';

/**
 * Public Pages Tests (No Auth Required)
 *
 * Tests for pages that don't require authentication.
 */

test.describe('Login Page', () => {

  test('login page loads', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByText('Welcome back')).toBeVisible();
    await expect(page.getByRole('link', { name: 'BrandTruth AI' })).toBeVisible();
  });

  test('shows email and password fields', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByPlaceholder('you@company.com')).toBeVisible();
    await expect(page.getByPlaceholder('Enter your password')).toBeVisible();
  });

  test('shows sign in button', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });

  test('shows OAuth providers', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByText('Google')).toBeVisible();
    await expect(page.getByText('GitHub')).toBeVisible();
  });

  test('can type in email field', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.getByPlaceholder('you@company.com');
    await emailInput.fill('test@example.com');

    await expect(emailInput).toHaveValue('test@example.com');
  });

  test('can type in password field', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.getByPlaceholder('Enter your password');
    await passwordInput.fill('testpassword');

    await expect(passwordInput).toHaveValue('testpassword');
  });
});

test.describe('Landing Page', () => {

  test('landing page loads', async ({ page }) => {
    await page.goto('/landing');

    // Should show some landing content
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Root Redirect', () => {

  test('root page loads', async ({ page }) => {
    await page.goto('/');

    // Root may show landing page or redirect
    // Just verify page loads without error
    await expect(page.locator('body')).toBeVisible();
  });
});
