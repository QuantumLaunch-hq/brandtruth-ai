import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E Test Configuration for BrandTruth AI
 *
 * Run tests against Docker containers:
 *   docker-compose up -d
 *   cd frontend && npm run test:e2e
 *
 * Or run specific test:
 *   npm run test:e2e -- --grep "API Health"
 */

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.spec.ts',
  timeout: 60000,
  retries: 1,

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3010',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    // Setup project for authentication
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },

    // Tests that don't need auth (API health, public pages)
    {
      name: 'no-auth',
      testMatch: /\.(noauth|api)\.spec\.ts/,
      use: { ...devices['Desktop Chrome'] },
    },

    // Tests that need authentication
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.playwright/.auth/user.json',
      },
      dependencies: ['setup'],
      testIgnore: /\.(noauth|api)\.spec\.ts/,
    },
  ],
})
