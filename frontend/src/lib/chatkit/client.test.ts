import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const modulePath = './client';

describe('ChatKitClient', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  it('reports failure when ChatKit is not configured', async () => {
    vi.stubEnv('VITE_CHATKIT_API_KEY', '');
    vi.stubEnv('VITE_CHATKIT_TELEMETRY_CHANNEL', '');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', '');

    const { ChatKitClient } = await import(modulePath);
    const client = new ChatKitClient({ stationSlug: 'test-station' });
    const result = await client.triggerConnectorTest('connector-1');

    expect(result.status).toBe('failed');
    expect(result.message).toMatch(/not configured/i);
  });

  it('sends connector test commands when configured', async () => {
    const post = vi.fn().mockResolvedValue({ data: { status: 'succeeded', message: 'ok' } });
    vi.stubEnv('VITE_CHATKIT_API_KEY', 'demo');
    vi.stubEnv('VITE_CHATKIT_TELEMETRY_CHANNEL', 'channel');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', 'org');

    vi.doMock('../../services/api', () => ({
      default: { post },
    }));

    const { ChatKitClient } = await import(modulePath);
    const client = new ChatKitClient({ stationSlug: 'forward-ops', channel: 'custom-channel' });
    const result = await client.triggerConnectorTest('connector-42');

    expect(post).toHaveBeenCalledWith('/api/v1/chatkit/commands', {
      channel: 'custom-channel',
      station_slug: 'forward-ops',
      command: 'connector:test',
      payload: { connector_id: 'connector-42' },
    });
    expect(result.status).toBe('succeeded');
  });
});
