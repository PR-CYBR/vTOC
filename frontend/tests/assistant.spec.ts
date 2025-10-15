import { test, expect } from '@playwright/test';

test.describe('ChatKit Co-Pilot integration', () => {
  test('mounts the assistant widget and toggles visibility', async ({ page }) => {
    await page.goto('/');

    const coPilotToggle = page.getByRole('button', { name: /co-pilot/i });
    await expect(coPilotToggle).toBeVisible();

    const assistant = page.locator('chatkit-assistant');
    await expect(assistant).toBeVisible();

    await coPilotToggle.click();
    await expect(assistant).toBeHidden();

    await coPilotToggle.click();
    await expect(assistant).toBeVisible();
  });
});
