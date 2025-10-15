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
});
