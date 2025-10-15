import { useEffect, useMemo, useRef } from 'react';
import type { DetailedHTMLProps, HTMLAttributes } from 'react';
import type { TelemetryEvent } from '../../services/api';

const scriptState: { promise: Promise<void> | null; src?: string } = { promise: null };

async function ensureWidgetScript(src: string | undefined): Promise<void> {
  if (typeof window === 'undefined' || !src) {
    return;
  }

  const existing = document.querySelector<HTMLScriptElement>('script[data-chatkit-widget="true"]');
  if (existing) {
    if (existing.dataset.src === src) {
      return;
    }
    existing.remove();
    scriptState.promise = null;
  }

  if (!scriptState.promise) {
    scriptState.promise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.dataset.chatkitWidget = 'true';
      script.dataset.src = src;
      script.onload = () => resolve();
      script.onerror = () => {
        console.error('Failed to load ChatKit widget script', src);
        scriptState.promise = null;
        reject(new Error(`Failed to load widget script: ${src}`));
      };
      document.head.appendChild(script);
    });
  }

  await scriptState.promise;
}

export interface ChatKitTelemetryContext {
  events: TelemetryEvent[];
  lastEventTimestamp?: string;
  defaultStation: string;
}

export interface ChatKitWidgetProps {
  open?: boolean;
  telemetry: ChatKitTelemetryContext;
  onReady?: () => void;
  className?: string;
}

interface ChatKitElement extends HTMLElement {
  context?: ChatKitTelemetryContext;
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'chatkit-assistant': DetailedHTMLProps<HTMLAttributes<ChatKitElement>, ChatKitElement> & {
        'data-api-key'?: string;
        'data-org-id'?: string;
        'data-telemetry-channel'?: string;
        'data-actions-endpoint'?: string;
        'data-default-station'?: string;
      };
    }
  }
}

const ChatKitWidget = ({ open = true, telemetry, onReady, className }: ChatKitWidgetProps) => {
  const chatkitApiKey = import.meta.env.VITE_CHATKIT_API_KEY;
  const agentkitOrgId = import.meta.env.VITE_AGENTKIT_ORG_ID ?? '';
  const widgetSrc = import.meta.env.VITE_CHATKIT_WIDGET_URL;
  const telemetryChannel = import.meta.env.VITE_CHATKIT_TELEMETRY_CHANNEL ?? 'vtoc-intel';
  const defaultStationFromEnv = import.meta.env.VITE_AGENTKIT_DEFAULT_STATION_CONTEXT ?? '';
  const basePath = (import.meta.env.VITE_AGENTKIT_API_BASE_PATH ?? '/api/v1/agent-actions').replace(/\/$/, '');
  const actionsEndpoint = useMemo(() => `${basePath}/execute`, [basePath]);
  const elementRef = useRef<ChatKitElement | null>(null);

  useEffect(() => {
    if (!chatkitApiKey || !agentkitOrgId) {
      return;
    }

    ensureWidgetScript(widgetSrc)
      .then(() => {
        if (elementRef.current) {
          elementRef.current.context = telemetry;
        }
        onReady?.();
      })
      .catch((error) => {
        console.error(error);
      });
  }, [onReady, widgetSrc, agentkitOrgId, chatkitApiKey]);

  useEffect(() => {
    if (elementRef.current) {
      elementRef.current.style.display = open ? 'block' : 'none';
      elementRef.current.context = telemetry;
    }
  }, [open, telemetry]);

  if (!chatkitApiKey || !agentkitOrgId) {
    if (import.meta.env.DEV) {
      console.warn('ChatKit widget is disabled. Missing API key or AgentKit org identifier.');
    }
    return null;
  }

  return (
    <chatkit-assistant
      ref={elementRef}
      className={className}
      data-api-key={chatkitApiKey}
      data-org-id={agentkitOrgId}
      data-telemetry-channel={telemetryChannel}
      data-actions-endpoint={actionsEndpoint}
      data-default-station={telemetry.defaultStation || defaultStationFromEnv}
    />
  );
};

export default ChatKitWidget;
