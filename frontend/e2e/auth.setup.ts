import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../.playwright/.auth/user.json');

/**
 * Authentication setup for E2E tests
 *
 * This creates an authenticated session that can be reused across tests.
 * For development, we use credentials login.
 */
setup('authenticate', async ({ page }) => {
  // Go to login page
  await page.goto('/login');

  // Wait for login form
  await expect(page.getByPlaceholder('you@company.com')).toBeVisible({ timeout: 10000 });

  // Fill in test credentials
  // Note: Create a test user in the database for E2E tests
  await page.getByPlaceholder('you@company.com').fill('test@brandtruth.ai');
  await page.getByPlaceholder('Enter your password').fill('testpassword123');

  // Click sign in
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for redirect to dashboard or studio
  await expect(page).toHaveURL(/\/(studio|campaigns|dashboard)/, { timeout: 15000 });

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
