/// <reference types="vite/client" />

declare global {
  interface ImportMetaEnv {
    readonly VITE_PORT?: string;
    readonly VITE_API_BASE_URL?: string;
    readonly VITE_MAP_TILES_URL?: string;
    readonly VITE_MAP_ATTRIBUTION?: string;
    readonly VITE_DEFAULT_DIV?: string;
    readonly VITE_RSS_ENABLED?: string;
    readonly VITE_CHAT_ENABLED?: string;
    readonly VITE_CHATKIT_WIDGET_URL?: string;
    readonly VITE_CHATKIT_API_KEY?: string;
    readonly VITE_CHATKIT_TELEMETRY_CHANNEL?: string;
    readonly VITE_AGENTKIT_ORG_ID?: string;
    readonly VITE_AGENTKIT_DEFAULT_STATION_CONTEXT?: string;
    readonly VITE_AGENTKIT_API_BASE_PATH?: string;
  }
}

export {};
