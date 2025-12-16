import { test, expect } from '@playwright/test';

test.describe('BrandTruth Studio - Premium', () => {
  
  test.describe('Onboarding', () => {
    test('shows welcome screen', async ({ page }) => {
      await page.goto('/studio');
      
      await expect(page.getByText('BrandTruth Studio')).toBeVisible();
      await expect(page.getByText(/Extract real claims/)).toBeVisible();
    });

    test('has enter URL and skip buttons', async ({ page }) => {
      await page.goto('/studio');
      
      await expect(page.getByRole('button', { name: 'Enter your website URL' })).toBeVisible();
      await expect(page.getByRole('button', { name: 'Skip for now' })).toBeVisible();
    });

    test('URL input step shows correctly', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      
      await expect(page.getByPlaceholder('yoursite.com')).toBeVisible();
      await expect(page.getByText('Back')).toBeVisible();
    });

    test('back button returns to welcome', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByText('Back').click();
      
      await expect(page.getByText('BrandTruth Studio')).toBeVisible();
    });

    test('example URLs populate input', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByText('careerfied.ai').click();
      
      const input = page.getByPlaceholder('yoursite.com');
      await expect(input).toHaveValue('careerfied.ai');
    });

    test('processes URL and shows review', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByPlaceholder('yoursite.com').fill('careerfied.ai');
      await page.getByRole('button', { name: 'Continue' }).click();
      
      // Wait for processing to complete
      await expect(page.getByText('Careerfied')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText(/claims extracted/)).toBeVisible();
    });

    test('review shows risk badges', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByText('careerfied.ai').click();
      await page.getByRole('button', { name: 'Continue' }).click();
      
      await expect(page.getByText('low').first()).toBeVisible({ timeout: 15000 });
    });

    test('skip goes directly to studio', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Skip for now' }).click();
      
      await expect(page.getByPlaceholder('Ask anything...')).toBeVisible();
    });
  });

  test.describe('Main Interface', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Skip for now' }).click();
    });

    test('shows chat input', async ({ page }) => {
      await expect(page.getByPlaceholder('Ask anything...')).toBeVisible();
    });

    test('shows Studio branding', async ({ page }) => {
      await expect(page.getByText('Studio')).toBeVisible();
    });

    test('shows command palette trigger', async ({ page }) => {
      await expect(page.getByText('Commands')).toBeVisible();
      await expect(page.getByText('⌘K')).toBeVisible();
    });

    test('shows preview panel', async ({ page }) => {
      await expect(page.getByText('Preview')).toBeVisible();
      await expect(page.getByText('Claims')).toBeVisible();
    });

    test('shows phone preview', async ({ page }) => {
      await expect(page.getByText('9:41')).toBeVisible(); // Phone time
      await expect(page.getByText('Sponsored')).toBeVisible();
      await expect(page.getByText('Learn More')).toBeVisible();
    });
  });

  test.describe('Command Palette', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Skip for now' }).click();
    });

    test('opens with button click', async ({ page }) => {
      await page.getByText('Commands').click();
      
      await expect(page.getByPlaceholder('Search commands...')).toBeVisible();
    });

    test('opens with keyboard shortcut', async ({ page }) => {
      await page.keyboard.press('Meta+k');
      
      await expect(page.getByPlaceholder('Search commands...')).toBeVisible();
    });

    test('shows all commands', async ({ page }) => {
      await page.getByText('Commands').click();
      
      await expect(page.getByText('Generate hooks')).toBeVisible();
      await expect(page.getByText('New campaign')).toBeVisible();
      await expect(page.getByText('Plan budget')).toBeVisible();
      await expect(page.getByText('Find audience')).toBeVisible();
    });

    test('shows command descriptions', async ({ page }) => {
      await page.getByText('Commands').click();
      
      await expect(page.getByText('Create scroll-stopping headlines')).toBeVisible();
      await expect(page.getByText('Start a full campaign')).toBeVisible();
    });

    test('filters commands on search', async ({ page }) => {
      await page.getByText('Commands').click();
      await page.getByPlaceholder('Search commands...').fill('hook');
      
      await expect(page.getByText('Generate hooks')).toBeVisible();
      await expect(page.getByText('Plan budget')).not.toBeVisible();
    });

    test('shows no results when no matches', async ({ page }) => {
      await page.getByText('Commands').click();
      await page.getByPlaceholder('Search commands...').fill('xyzabc');
      
      await expect(page.getByText('No commands found')).toBeVisible();
    });

    test('closes on Escape', async ({ page }) => {
      await page.getByText('Commands').click();
      await expect(page.getByPlaceholder('Search commands...')).toBeVisible();
      
      await page.keyboard.press('Escape');
      
      await expect(page.getByPlaceholder('Search commands...')).not.toBeVisible();
    });

    test('closes on backdrop click', async ({ page }) => {
      await page.getByText('Commands').click();
      await expect(page.getByPlaceholder('Search commands...')).toBeVisible();
      
      // Click backdrop (outside the palette)
      await page.locator('.bg-black\\/60').click();
      
      await expect(page.getByPlaceholder('Search commands...')).not.toBeVisible();
    });

    test('executes command on click', async ({ page }) => {
      await page.getByText('Commands').click();
      await page.getByText('Generate hooks').click();
      
      // Should close palette and show user message
      await expect(page.getByPlaceholder('Search commands...')).not.toBeVisible();
      await expect(page.getByText('Generate hooks')).toBeVisible();
    });

    test('keyboard navigation works', async ({ page }) => {
      await page.keyboard.press('Meta+k');
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      
      // Should execute a command
      await expect(page.getByPlaceholder('Search commands...')).not.toBeVisible();
    });
  });

  test.describe('Chat Functionality', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Skip for now' }).click();
    });

    test('can type in input', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Hello world');
      
      await expect(input).toHaveValue('Hello world');
    });

    test('sends message on Enter', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Generate hooks for my product');
      await input.press('Enter');
      
      // User message should appear
      await expect(page.getByText('Generate hooks for my product')).toBeVisible();
    });

    test('clears input after sending', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Test message');
      await input.press('Enter');
      
      await expect(input).toHaveValue('');
    });

    test('shows thinking indicator', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Test');
      await input.press('Enter');
      
      // Should briefly show thinking
      await expect(page.getByText('Thinking...')).toBeVisible({ timeout: 2000 });
    });

    test('shows AI response', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Generate hooks');
      await input.press('Enter');
      
      // Should show AI response with hooks
      await expect(page.getByText(/hooks/i)).toBeVisible({ timeout: 5000 });
    });

    test('hook response includes artifacts', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Generate hooks');
      await input.press('Enter');
      
      // Should show hook artifacts with scores
      await expect(page.locator('text=/\\d{2}/')).toBeVisible({ timeout: 5000 }); // Score like 94
    });

    test('budget response shows budget info', async ({ page }) => {
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Plan my budget');
      await input.press('Enter');
      
      // Should show budget artifact
      await expect(page.getByText(/budget/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Brand Context', () => {
    test('shows brand header after onboarding', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByText('careerfied.ai').click();
      await page.getByRole('button', { name: 'Continue' }).click();
      
      // Wait for review
      await expect(page.getByText('Careerfied')).toBeVisible({ timeout: 15000 });
      
      // Continue to studio
      await page.getByRole('button', { name: 'Continue' }).click();
      
      // Should show brand in header
      await expect(page.getByText('Careerfied')).toBeVisible();
      await expect(page.getByText(/claims extracted/)).toBeVisible();
    });

    test('change button triggers rescan', async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByText('careerfied.ai').click();
      await page.getByRole('button', { name: 'Continue' }).click();
      
      await expect(page.getByText('Careerfied')).toBeVisible({ timeout: 15000 });
      await page.getByRole('button', { name: 'Continue' }).click();
      
      // Click Change button
      await page.getByRole('button', { name: 'Change' }).click();
      
      // Should go back to onboarding
      await expect(page.getByText('BrandTruth Studio')).toBeVisible();
    });
  });

  test.describe('Full Workflow', () => {
    test('complete flow: URL → review → studio → generate', async ({ page }) => {
      await page.goto('/studio');
      
      // Step 1: Enter URL
      await page.getByRole('button', { name: 'Enter your website URL' }).click();
      await page.getByText('careerfied.ai').click();
      await page.getByRole('button', { name: 'Continue' }).click();
      
      // Step 2: Review
      await expect(page.getByText('Careerfied')).toBeVisible({ timeout: 15000 });
      await expect(page.getByText(/claims extracted/)).toBeVisible();
      await page.getByRole('button', { name: 'Continue' }).click();
      
      // Step 3: Main studio
      await expect(page.getByPlaceholder('Ask anything...')).toBeVisible();
      await expect(page.getByText('Careerfied')).toBeVisible();
      
      // Step 4: Generate hooks
      const input = page.getByPlaceholder('Ask anything...');
      await input.fill('Generate hooks');
      await input.press('Enter');
      
      // Step 5: Should see hooks
      await expect(page.getByText(/hooks/i)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Responsive Design', () => {
    test('renders on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/studio');
      
      await expect(page.getByText('BrandTruth Studio')).toBeVisible();
    });

    test('renders on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/studio');
      
      await expect(page.getByText('BrandTruth Studio')).toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/studio');
      await page.getByRole('button', { name: 'Skip for now' }).click();
    });

    test('input is focusable', async ({ page }) => {
      await page.getByPlaceholder('Ask anything...').focus();
      
      await expect(page.getByPlaceholder('Ask anything...')).toBeFocused();
    });

    test('can navigate with keyboard', async ({ page }) => {
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Should be able to tab through elements
      const focusedElement = page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });
  });
});
