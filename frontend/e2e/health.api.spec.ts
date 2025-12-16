import { test, expect } from '@playwright/test';

/**
 * API Health & Integration Tests
 *
 * These tests verify the backend API is running and healthy.
 * No authentication required.
 */

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

  test('API version is returned', async ({ request }) => {
    const response = await request.get('http://localhost:8010/health');
    const body = await response.json();

    expect(body.version).toBeDefined();
  });
});

test.describe('API Endpoints', () => {

  test('predict endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8010/predict/demo');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.score).toBeDefined();
    expect(body.score).toBeGreaterThanOrEqual(0);
    expect(body.score).toBeLessThanOrEqual(100);
  });

  test('hooks endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8010/hooks/demo');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.hooks).toBeDefined();
    expect(Array.isArray(body.hooks)).toBeTruthy();
  });

  test('attention score endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8010/attention/demo');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.score).toBeDefined();
    expect(body.summary).toBeDefined();
  });

  test('budget simulation endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8010/budget/demo');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.daily_budget).toBeDefined();
    expect(body.expected_cpa).toBeDefined();
  });
});

test.describe('Workflow API', () => {

  test('workflow health check', async ({ request }) => {
    const response = await request.get('http://localhost:8010/workflow/health');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.temporal_available).toBe(true);
    expect(body.status).toBe('healthy');
  });
});

test.describe('Output Files', () => {

  test('output directory is accessible', async ({ request }) => {
    // This may return 404 if empty, or 200 with files
    const response = await request.get('http://localhost:8010/output/');

    // 404 is acceptable if no files exist yet
    expect([200, 404]).toContain(response.status());
  });
});
