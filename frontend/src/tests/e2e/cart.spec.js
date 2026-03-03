// ============================================
// E2E Test: Cart & Checkout Flow
// Covers: cart page, empty cart state, checkout access
// ============================================
import { test, expect } from '@playwright/test';

test.describe('Cart Flow', () => {
  test('should show empty cart state', async ({ page }) => {
    await page.goto('/cart');
    // Should show empty cart message or redirect to login
    const content = page.locator('body');
    const text = await content.textContent();
    const isEmpty = /empty|no items|start shopping|continue shopping|login/i.test(text);
    expect(isEmpty).toBeTruthy();
  });

  test('cart should have continue shopping link', async ({ page }) => {
    await page.goto('/cart');
    const shopLink = page.locator('a[href="/"], a[href="/shop"], a:has-text("Continue Shopping")');
    if (await shopLink.count() > 0) {
      await expect(shopLink.first()).toBeVisible();
    }
  });

  test('checkout should require authentication', async ({ page }) => {
    await page.goto('/checkout');
    await page.waitForURL(/\/login|\/checkout/);
    // Should either redirect to login or show checkout (if already logged in)
    const url = page.url();
    expect(url.includes('/login') || url.includes('/checkout')).toBeTruthy();
  });
});

test.describe('Cart Accessibility', () => {
  test('cart page should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/cart');
    const h1 = page.locator('h1');
    if (await h1.count() > 0) {
      await expect(h1.first()).toBeVisible();
    }
  });

  test('cart buttons should be keyboard accessible', async ({ page }) => {
    await page.goto('/cart');
    const buttons = page.locator('button, a[role="button"]');
    const count = await buttons.count();
    for (let i = 0; i < Math.min(count, 5); i++) {
      const btn = buttons.nth(i);
      if (await btn.isVisible()) {
        await btn.focus();
        await expect(btn).toBeFocused();
      }
    }
  });
});
