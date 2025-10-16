import { render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ChatKitWidget from './ChatKitWidget';

describe('ChatKitWidget', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  const telemetry = {
    events: [],
    lastEventTimestamp: undefined,
    defaultStation: 'TEST',
  };

  it('renders nothing when credentials are missing', () => {
    const { container } = render(<ChatKitWidget telemetry={telemetry} />);
    expect(container.querySelector('chatkit-assistant')).toBeNull();
  });

  it('renders the chatkit custom element when configured', async () => {
    vi.stubEnv('VITE_CHATKIT_API_KEY', 'test');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', 'org');

    const { container } = render(<ChatKitWidget telemetry={telemetry} />);
    await waitFor(() => {
      expect(container.querySelector('chatkit-assistant')).not.toBeNull();
    });
  });

  it('passes Supabase session data through data attributes', async () => {
    vi.stubEnv('VITE_CHATKIT_API_KEY', 'test');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', 'org');

    const richTelemetry = {
      ...telemetry,
      channel: 'custom-channel',
      credentials: {
        accessToken: 'token-123',
        refreshToken: 'refresh-123',
        userId: 'user-123',
      },
    };

    const { container } = render(<ChatKitWidget telemetry={richTelemetry} />);

    await waitFor(() => {
      const widget = container.querySelector('chatkit-assistant');
      expect(widget).not.toBeNull();
      expect(widget?.getAttribute('data-supabase-access-token')).toBe('token-123');
      expect(widget?.getAttribute('data-supabase-refresh-token')).toBe('refresh-123');
      expect(widget?.getAttribute('data-supabase-user-id')).toBe('user-123');
      expect(widget?.getAttribute('data-telemetry-channel')).toBe('custom-channel');
    });
  });
});
