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
    vi.stubEnv('VITE_CHATKIT_WIDGET_URL', 'https://example.com/widget.js');

    const { container } = render(<ChatKitWidget telemetry={telemetry} />);
    await waitFor(() => {
      expect(container.querySelector('chatkit-assistant')).not.toBeNull();
    });
  });

  it('passes Supabase session data through data attributes', async () => {
    vi.stubEnv('VITE_CHATKIT_API_KEY', 'test');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', 'org');
    vi.stubEnv('VITE_CHATKIT_WIDGET_URL', 'https://example.com/widget.js');

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

  it('updates the custom element context when telemetry changes', async () => {
    vi.stubEnv('VITE_CHATKIT_API_KEY', 'test');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', 'org');
    vi.stubEnv('VITE_CHATKIT_WIDGET_URL', 'https://example.com/widget.js');

    const { container, rerender } = render(<ChatKitWidget telemetry={telemetry} />);

    await waitFor(() => {
      expect(container.querySelector('chatkit-assistant')).not.toBeNull();
    });

    const widget = container.querySelector('chatkit-assistant') as HTMLElement & {
      context?: typeof telemetry;
    };

    expect(widget?.context).toEqual(expect.objectContaining(telemetry));

    const updatedTelemetry = {
      ...telemetry,
      events: [
        {
          id: 1,
          source_id: 1,
          status: 'received',
          received_at: '2024-03-12T10:00:00Z',
          source: {
            id: 1,
            name: 'sensor-1',
            slug: 'sensor-1',
            source_type: 'radar',
          },
        },
      ],
      lastEventTimestamp: '2024-03-12T10:00:00Z',
    };

    rerender(<ChatKitWidget telemetry={updatedTelemetry} />);

    await waitFor(() => {
      expect(widget?.context).toEqual(expect.objectContaining(updatedTelemetry));
    });
  });

  it('toggles visibility based on the open prop', async () => {
    vi.stubEnv('VITE_CHATKIT_API_KEY', 'test');
    vi.stubEnv('VITE_AGENTKIT_ORG_ID', 'org');
    vi.stubEnv('VITE_CHATKIT_WIDGET_URL', 'https://example.com/widget.js');

    const { container, rerender } = render(<ChatKitWidget telemetry={telemetry} open={false} />);

    await waitFor(() => {
      expect(container.querySelector('chatkit-assistant')).not.toBeNull();
    });

    let widget = container.querySelector('chatkit-assistant') as HTMLElement;
    expect(widget.style.display).toBe('none');

    rerender(<ChatKitWidget telemetry={telemetry} open />);

    await waitFor(() => {
      widget = container.querySelector('chatkit-assistant') as HTMLElement;
      expect(widget.style.display).toBe('block');
    });
  });
});
