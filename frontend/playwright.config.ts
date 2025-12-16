import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E Test Configuration for BrandTruth AI
 * 
 * IMPORTANT: Start dev server first in separate terminal: npm run dev
 * Then run tests: npm run test:e2e
 */

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  timeout: 30000,
  retries: 0,
  
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  
  use: {
    baseURL: 'http://localhost:3001',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  // Run only Chromium for faster local testing
  // Add more browsers for CI
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Uncomment to auto-start dev server (slower)
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: true,
  //   timeout: 120000,
  // },
})
