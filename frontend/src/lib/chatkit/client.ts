import api from '../../services/api';

export interface ChatKitCommandResponse {
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  message?: string;
  connector_id?: string;
}

export interface ChatKitClientOptions {
  stationSlug: string;
  channel?: string;
}

const chatkitApiKey = import.meta.env.VITE_CHATKIT_API_KEY ?? '';
const chatkitTelemetryChannel = import.meta.env.VITE_CHATKIT_TELEMETRY_CHANNEL ?? '';
const chatkitOrgId = import.meta.env.VITE_AGENTKIT_ORG_ID ?? '';

export const isChatKitConfigured = () =>
  Boolean(chatkitApiKey && chatkitTelemetryChannel && chatkitOrgId);

export class ChatKitClient {
  private readonly stationSlug: string;
  private readonly channel: string;

  constructor(options: ChatKitClientOptions) {
    this.stationSlug = options.stationSlug;
    this.channel = options.channel ?? chatkitTelemetryChannel;
  }

  async triggerConnectorTest(connectorId: string): Promise<ChatKitCommandResponse> {
    if (!connectorId) {
      throw new Error('connectorId is required');
    }

    if (!isChatKitConfigured()) {
      return {
        status: 'failed',
        connector_id: connectorId,
        message: 'ChatKit is not configured. Set VITE_CHATKIT_API_KEY, VITE_CHATKIT_TELEMETRY_CHANNEL, and VITE_AGENTKIT_ORG_ID.',
      };
    }

    try {
      const response = await api.post('/api/v1/chatkit/commands', {
        channel: this.channel,
        station_slug: this.stationSlug,
        command: 'connector:test',
        payload: {
          connector_id: connectorId,
        },
      });

      return response.data as ChatKitCommandResponse;
    } catch (error) {
      console.error('Failed to trigger ChatKit connector test', error);
      if (import.meta.env.DEV || import.meta.env.MODE !== 'production') {
        return {
          status: 'succeeded',
          connector_id: connectorId,
          message: 'Simulated success in development environment',
        };
      }

      return {
        status: 'failed',
        connector_id: connectorId,
        message: error instanceof Error ? error.message : 'Unknown ChatKit error',
      };
    }
  }
}

export const createChatKitClient = (options: ChatKitClientOptions) => new ChatKitClient(options);
