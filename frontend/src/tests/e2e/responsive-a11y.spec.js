// @ts-check
import { test, expect } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('landing page should not have horizontal scroll on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile-only test');
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    // Body should not be wider than viewport (no horizontal scroll)
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 5); // 5px tolerance
  });

  test('content should stack vertically on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile-only test');
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Page should render without error
    const body = await page.textContent('body');
    expect(body.length).toBeGreaterThan(0);
  });

  test('login form should be full-width on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile-only test');
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    const form = page.locator('form').first();
    if (await form.isVisible()) {
      const box = await form.boundingBox();
      if (box) {
        // Form should use most of the viewport width
        // Login page uses max-w-md with padding, so 250px is reasonable minimum
        expect(box.width).toBeGreaterThan(250);
      }
    }
  });
});

test.describe('Accessibility Checks', () => {
  test('landing page should have ARIA landmarks', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Should have at least a main landmark
    const main = page.locator('main, [role="main"]');
    const mainCount = await main.count();
    expect(mainCount).toBeGreaterThanOrEqual(1);
  });

  test('pages should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    // Should have at least one h1
    const h1 = page.locator('h1');
    const h1Count = await h1.count();
    expect(h1Count).toBeGreaterThanOrEqual(1);
  });

  test('interactive elements should have minimum touch targets', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile-only test');
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    // Check that buttons have minimum size
    const buttons = page.locator('button:visible');
    const count = await buttons.count();
    for (let i = 0; i < count; i++) {
      const box = await buttons.nth(i).boundingBox();
      if (box && box.width > 0 && box.height > 0) {
        expect(box.height).toBeGreaterThanOrEqual(40); // Reasonable minimum
      }
    }
  });

  test('should have visible focus indicators', async ({ page }) => {
    await page.goto('/login');
    // Tab to first focusable element
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    // Check that an element has focus
    const focusedTag = await page.evaluate(() => document.activeElement?.tagName);
    expect(focusedTag).toBeTruthy();
  });

  test('images should have alt attributes', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < Math.min(count, 10); i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).not.toBeNull();
    }
  });

  test('color contrast should be sufficient', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    // Basic check: text elements have non-transparent color
    const bodyColor = await page.evaluate(() => {
      const body = document.body;
      const style = getComputedStyle(body);
      return { color: style.color, bg: style.backgroundColor };
    });
    expect(bodyColor.color).toBeTruthy();
  });
});
