import { test, expect } from '@playwright/test';

test.describe('Setup wizard flow', () => {
  test('completes station onboarding with connector tests', async ({ page }) => {
    await page.goto('/setup');

    await page.getByLabelText(/station name/i).fill('Forward Ops Station');
    await page.getByLabelText(/station slug/i).fill('forward-ops');

    await page.getByRole('button', { name: 'Next' }).click();

    await page.getByLabelText(/ADS-B Receiver/i).check();

    await page.getByRole('button', { name: 'Next' }).click();

    await page.getByRole('button', { name: /run tests/i }).click();

    await expect(page.getByTestId('connector-test-adsb-receiver')).toContainText('succeeded');

    await page.getByRole('button', { name: /finish setup/i }).click();
    await expect(page.getByTestId('setup-summary')).toContainText('Forward Ops Station');
  });
});

test.describe('Operational map', () => {
  test('reflects ADS-B overlay toggles', async ({ page }) => {
    await page.goto('/map');

    const overlayToggle = page.getByLabelText(/ADS-B overlay/i);
    const trackCount = page.getByTestId('adsb-track-count');

    await expect(trackCount).toContainText('ADS-B tracks');
    await overlayToggle.click();
    await expect(trackCount).toHaveText(/ADS-B tracks: 0/);
  });
});
