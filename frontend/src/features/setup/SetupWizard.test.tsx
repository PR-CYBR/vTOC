import { describe, expect, vi, beforeAll, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SetupWizard from './SetupWizard';
import '@testing-library/jest-dom/vitest';

import type { ChatKitClient } from '../../lib/chatkit/client';

const ensureCrypto = () => {
  if (!globalThis.crypto) {
    Object.defineProperty(globalThis, 'crypto', {
      value: {
        randomUUID: () => 'test-uuid',
      },
    });
  } else if (!('randomUUID' in globalThis.crypto)) {
    Object.defineProperty(globalThis.crypto, 'randomUUID', {
      value: () => 'test-uuid',
    });
  }
};

describe('SetupWizard', () => {
  beforeAll(() => {
    ensureCrypto();
  });

  it('guides the user through configuration and connector testing', async () => {
    const user = userEvent.setup();
    const triggerConnectorTest = vi.fn<ChatKitClient['triggerConnectorTest']>().mockResolvedValue({
      status: 'succeeded',
      message: 'Test complete',
      connector_id: 'adsb-receiver',
    });

    const factory = vi.fn(() => ({
      triggerConnectorTest,
    } as unknown as ChatKitClient));

    render(<SetupWizard chatKitFactory={factory} />);

    const stationName = screen.getByLabelText(/station name/i);
    await user.clear(stationName);
    await user.type(stationName, 'Forward Ops Station');
    const stationSlug = screen.getByLabelText(/station slug/i);
    await user.clear(stationSlug);
    await user.type(stationSlug, 'forward-ops');

    await user.click(screen.getByRole('button', { name: /next/i }));

    const adsbOption = screen.getByLabelText(/ads-b receiver/i);
    await user.click(adsbOption);

    await user.click(screen.getByRole('button', { name: /next/i }));

    const runTests = screen.getByRole('button', { name: /run tests/i });
    await user.click(runTests);

    await screen.findByText(/succeeded/i);
    expect(triggerConnectorTest).toHaveBeenCalledWith('adsb-receiver');

    await user.click(screen.getByRole('button', { name: /finish setup/i }));
    expect(screen.getByTestId('setup-summary')).toHaveTextContent('Forward Ops Station');
  });

  it('requires hardware selection before moving forward', async () => {
    const user = userEvent.setup();
    render(<SetupWizard chatKitFactory={() => ({
      triggerConnectorTest: vi.fn().mockResolvedValue({ status: 'succeeded' }),
    }) as unknown as ChatKitClient} />);

    await user.type(screen.getByLabelText(/station name/i), 'Sensor Base');
    await user.type(screen.getByLabelText(/station slug/i), 'sensor-base');

    await user.click(screen.getByRole('button', { name: /next/i }));

    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();

    await user.click(screen.getByLabelText(/ads-b receiver/i));
    expect(nextButton).toBeEnabled();
  });
});
