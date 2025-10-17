import { test, expect } from '@playwright/test';

const dashboardResponse = {
  station: {
    id: 1,
    slug: 'toc-s1',
    name: 'TOC-S1 Coastal Watch',
    timezone: 'America/Puerto_Rico',
  },
  metrics: {
    total_events: 4,
    active_sources: 2,
    last_event: {
      id: 99,
      source_id: 101,
      latitude: 18.2,
      longitude: -66.5,
      event_time: new Date().toISOString(),
      received_at: new Date().toISOString(),
      payload: { callsign: 'N7823C' },
      status: 'mocked',
      station_id: 1,
      source: {
        id: 101,
        name: 'Mock ADS-B feed',
        slug: 'mock-adsb',
        source_type: 'adsb',
      },
    },
  },
};

const telemetryResponse = [
  {
    id: 1,
    source_id: 101,
    latitude: 18.456,
    longitude: -66.105,
    event_time: new Date().toISOString(),
    received_at: new Date().toISOString(),
    payload: { callsign: 'N7823C', altitude_ft: 1250 },
    status: 'mocked',
    station_id: 1,
    source: {
      id: 101,
      name: 'Mock ADS-B feed',
      slug: 'mock-adsb',
      source_type: 'adsb',
    },
  },
];

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/stations/toc-s1/dashboard', async (route) => {
    await route.fulfill({ json: dashboardResponse });
  });

  await page.route('**/api/v1/telemetry/events', async (route) => {
    await route.fulfill({ json: telemetryResponse });
  });

  await page.route('**/api/v1/stations/', async (route) => {
    await route.fulfill({ json: [dashboardResponse.station] });
  });
});

test.describe('Setup wizard and mock telemetry overlay', () => {
  test('guides operators through setup and toggles overlay', async ({ page }) => {
    await page.goto('/');

    const wizardToggle = page.getByRole('button', { name: /launch setup wizard/i });
    await expect(wizardToggle).toBeVisible();
    await wizardToggle.click();

    const wizardDialog = page.getByRole('dialog', { name: /station setup wizard/i });
    await expect(wizardDialog).toBeVisible();
    await expect(wizardDialog.getByText('Connect services')).toBeVisible();

    await wizardDialog.getByTestId('wizard-next').click();
    await expect(wizardDialog.getByText('Seed telemetry')).toBeVisible();

    await wizardDialog.getByTestId('wizard-next').click();
    await expect(wizardDialog.getByText('Invite operators')).toBeVisible();

    await wizardDialog.getByTestId('wizard-finish').click();
    await expect(wizardDialog).toBeHidden();

    await page.getByRole('button', { name: /show mock telemetry/i }).click();
    const overlay = page.getByRole('complementary', { name: /mock telemetry overlay/i });
    await expect(overlay).toBeVisible();
    await expect(overlay.getByText(/mock ads-b feed/i)).toBeVisible();
    await expect(overlay.getByText(/n7823c/i)).toBeVisible();
  });
});
