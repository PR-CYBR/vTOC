export interface StationDetailsForm {
  name: string;
  slug: string;
  timezone: string;
  latitude: string;
  longitude: string;
  description: string;
}

export interface HardwareOption {
  id: string;
  name: string;
  description: string;
  recommended?: boolean;
}

export interface ConnectorTestResult {
  connectorId: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed';
  message?: string;
}

export interface SetupWizardState {
  station: StationDetailsForm;
  hardware: string[];
  connectorResults: Record<string, ConnectorTestResult>;
}
