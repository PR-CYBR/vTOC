import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'pnpm dev -- --port 4173 --host 127.0.0.1 --strictPort',
    url: 'http://127.0.0.1:4173',
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 120_000,
    env: {
      VITE_API_BASE_URL: 'http://127.0.0.1:4173',
      VITE_CHATKIT_API_KEY: 'test-public-key',
      VITE_CHATKIT_TELEMETRY_CHANNEL: 'test-channel',
      VITE_AGENTKIT_ORG_ID: 'playwright-org',
      VITE_AGENTKIT_DEFAULT_STATION_CONTEXT: 'TEST-SECTOR',
      VITE_AGENTKIT_API_BASE_PATH: '/api/v1/agent-actions',
      PORT: '4173',
      VITE_PORT: '4173',
    },
  },
});
