import { useMemo, useState } from 'react';

import { ChatKitClient, createChatKitClient, isChatKitConfigured } from '../../lib/chatkit/client';
import type { ConnectorTestResult, HardwareOption, SetupWizardState, StationDetailsForm } from './types';

const DEFAULT_TIMEZONE = 'UTC';
const HARDWARE_OPTIONS: HardwareOption[] = [
  {
    id: 'adsb-receiver',
    name: 'ADS-B Receiver',
    description: 'Captures aircraft telemetry using SDR hardware tuned for ADS-B frequencies.',
    recommended: true,
  },
  {
    id: 'ais-module',
    name: 'AIS Module',
    description: 'Marine AIS receiver for tracking coastal vessel movements.',
  },
  {
    id: 'weather-station',
    name: 'Weather Station',
    description: 'EnviroPro WX-400 sensor suite monitoring pressure, humidity, and wind data.',
  },
  {
    id: 'ptz-camera',
    name: 'PTZ Camera',
    description: 'Pan-tilt-zoom camera for visual confirmation of high priority tracks.',
  },
];

const INITIAL_STATE: SetupWizardState = {
  station: {
    name: '',
    slug: '',
    timezone: DEFAULT_TIMEZONE,
    latitude: '18.4663',
    longitude: '-66.1057',
    description: '',
  },
  hardware: [],
  connectorResults: {},
};

const sanitizeSlug = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9-\s]/g, '')
    .trim()
    .replace(/\s+/g, '-');

interface StationDetailsStepProps {
  value: StationDetailsForm;
  onChange: (value: StationDetailsForm) => void;
}

const StationDetailsStep = ({ value, onChange }: StationDetailsStepProps) => {
  const updateField = (field: keyof StationDetailsForm, newValue: string) => {
    const next = { ...value, [field]: newValue };

    if (field === 'name' && !value.slug) {
      next.slug = sanitizeSlug(newValue);
    }

    if (field === 'slug') {
      next.slug = sanitizeSlug(newValue);
    }

    onChange(next);
  };

  return (
    <div className="setup-card" aria-labelledby="station-details-heading">
      <header>
        <h2 id="station-details-heading">Station details</h2>
        <p>Describe the station deployment and provide coordinates for mapping.</p>
      </header>
      <form>
        <div className="setup-grid">
          <div className="setup-field">
            <label htmlFor="station-name">Station name</label>
            <input
              id="station-name"
              value={value.name}
              onChange={(event) => updateField('name', event.target.value)}
              placeholder="TOC-S1 Forward Ops"
              required
            />
          </div>
          <div className="setup-field">
            <label htmlFor="station-slug">Station slug</label>
            <input
              id="station-slug"
              value={value.slug}
              onChange={(event) => updateField('slug', event.target.value)}
              placeholder="toc-s1"
              required
            />
          </div>
        </div>
        <div className="setup-grid">
          <div className="setup-field">
            <label htmlFor="station-latitude">Latitude</label>
            <input
              id="station-latitude"
              value={value.latitude}
              onChange={(event) => updateField('latitude', event.target.value)}
              placeholder="18.4663"
            />
          </div>
          <div className="setup-field">
            <label htmlFor="station-longitude">Longitude</label>
            <input
              id="station-longitude"
              value={value.longitude}
              onChange={(event) => updateField('longitude', event.target.value)}
              placeholder="-66.1057"
            />
          </div>
          <div className="setup-field">
            <label htmlFor="station-timezone">Timezone</label>
            <select
              id="station-timezone"
              value={value.timezone}
              onChange={(event) => updateField('timezone', event.target.value)}
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">America/New_York</option>
              <option value="America/Los_Angeles">America/Los_Angeles</option>
              <option value="Europe/London">Europe/London</option>
            </select>
          </div>
        </div>
        <div className="setup-field">
          <label htmlFor="station-description">Mission brief</label>
          <textarea
            id="station-description"
            value={value.description}
            onChange={(event) => updateField('description', event.target.value)}
            rows={3}
            placeholder="Outline mission objectives, response playbooks, and key partner units."
          />
        </div>
      </form>
    </div>
  );
};

interface HardwareSelectionStepProps {
  options: HardwareOption[];
  selected: string[];
  onToggle: (id: string) => void;
}

const HardwareSelectionStep = ({ options, selected, onToggle }: HardwareSelectionStepProps) => {
  return (
    <div className="setup-card" aria-labelledby="hardware-selection-heading">
      <header>
        <h2 id="hardware-selection-heading">Hardware selection</h2>
        <p>Choose the telemetry connectors to provision for this station.</p>
      </header>
      <div className="connector-results">
        {options.map((option) => {
          const checkboxId = `hardware-${option.id}`;
          return (
            <label key={option.id} htmlFor={checkboxId} className="hardware-option" data-testid={`hardware-${option.id}`}>
              <input
                id={checkboxId}
                type="checkbox"
                checked={selected.includes(option.id)}
                onChange={() => onToggle(option.id)}
              />
              <div>
                <strong>
                  {option.name}
                  {option.recommended ? ' · Recommended' : ''}
                </strong>
                <span>{option.description}</span>
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
};

interface ConnectorTestingStepProps {
  connectors: HardwareOption[];
  results: Record<string, ConnectorTestResult>;
  onRunTests: () => Promise<void>;
  isTesting: boolean;
  chatKitReady: boolean;
}

const ConnectorTestingStep = ({ connectors, results, onRunTests, isTesting, chatKitReady }: ConnectorTestingStepProps) => {
  const hasResults = connectors.every((connector) => results[connector.id]);

  return (
    <div className="setup-card" aria-labelledby="connector-testing-heading">
      <header>
        <h2 id="connector-testing-heading">Connector testing</h2>
        <p>
          Validate that each connector responds to a ChatKit test command. The setup completes when all
          connectors succeed.
        </p>
      </header>
      <div className="connector-results">
        {connectors.length === 0 && <p>Select at least one connector to run automated tests.</p>}
        {connectors.map((connector) => {
          const result = results[connector.id];
          const statusLabel = result?.status ?? 'pending';
          return (
            <div className="connector-result" key={connector.id} data-testid={`connector-test-${connector.id}`}>
              <div>
                <strong>{connector.name}</strong>
                <div>{connector.description}</div>
              </div>
              <span className={`connector-result__status connector-result__status--${statusLabel}`}>
                {statusLabel}
              </span>
            </div>
          );
        })}
      </div>
      <div className="setup-actions">
        <div className="setup-summary">
          {!chatKitReady && 'ChatKit is not fully configured. Tests will simulate failures.'}
          {chatKitReady && connectors.length > 0 && !hasResults && 'Ready to run integration tests for selected connectors.'}
          {chatKitReady && hasResults && 'Review results and finalize setup.'}
        </div>
        <button type="button" onClick={onRunTests} disabled={isTesting || connectors.length === 0}>
          {isTesting ? 'Running tests…' : hasResults ? 'Re-run tests' : 'Run tests'}
        </button>
      </div>
    </div>
  );
};

const mapResponseToResult = (connectorId: string, response: Awaited<ReturnType<ChatKitClient['triggerConnectorTest']>>): ConnectorTestResult => {
  const status = response.status === 'succeeded' ? 'succeeded' : response.status === 'failed' ? 'failed' : 'running';

  return {
    connectorId,
    status,
    message: response.message,
  };
};

interface SetupWizardProps {
  chatKitFactory?: (stationSlug: string) => ChatKitClient;
}

const SetupWizard = ({ chatKitFactory }: SetupWizardProps) => {
  const [state, setState] = useState<SetupWizardState>(INITIAL_STATE);
  const [activeStep, setActiveStep] = useState(0);
  const [isTesting, setIsTesting] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const selectedHardware = useMemo(
    () => HARDWARE_OPTIONS.filter((option) => state.hardware.includes(option.id)),
    [state.hardware],
  );

  const chatKitReady = isChatKitConfigured();

  const steps = [
    {
      id: 'station-details',
      label: 'Station details',
      content: (
        <StationDetailsStep
          value={state.station}
          onChange={(value) => setState((current) => ({ ...current, station: value }))}
        />
      ),
    },
    {
      id: 'hardware-selection',
      label: 'Hardware selection',
      content: (
        <HardwareSelectionStep
          options={HARDWARE_OPTIONS}
          selected={state.hardware}
          onToggle={(id) =>
            setState((current) => {
              const next = current.hardware.includes(id)
                ? current.hardware.filter((hardwareId) => hardwareId !== id)
                : [...current.hardware, id];

              return {
                ...current,
                hardware: next,
                connectorResults: Object.fromEntries(
                  Object.entries(current.connectorResults).filter(([key]) => next.includes(key)),
                ),
              };
            })
          }
        />
      ),
    },
    {
      id: 'connector-testing',
      label: 'Connector testing',
      content: (
        <ConnectorTestingStep
          connectors={selectedHardware}
          results={state.connectorResults}
          isTesting={isTesting}
          onRunTests={async () => {
            setIsTesting(true);
            setIsComplete(false);

            setState((current) => ({
              ...current,
              connectorResults: selectedHardware.reduce<Record<string, ConnectorTestResult>>((acc, connector) => {
                acc[connector.id] = {
                  connectorId: connector.id,
                  status: 'running',
                  message: 'Executing ChatKit test…',
                };
                return acc;
              }, {}),
            }));

            const factory = chatKitFactory ?? ((slug: string) => createChatKitClient({ stationSlug: slug }));
            const fallbackSlug = typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : 'station';
            const client = factory(state.station.slug || `station-${fallbackSlug}`);

            for (const connector of selectedHardware) {
              // eslint-disable-next-line no-await-in-loop
              const response = await client.triggerConnectorTest(connector.id);
              setState((current) => ({
                ...current,
                connectorResults: {
                  ...current.connectorResults,
                  [connector.id]: mapResponseToResult(connector.id, response),
                },
              }));
            }

            setIsTesting(false);
          }}
          chatKitReady={chatKitReady}
        />
      ),
    },
  ];

  const currentStep = steps[activeStep];

  const canMoveNext = () => {
    if (activeStep === 0) {
      return Boolean(state.station.name && state.station.slug);
    }

    if (activeStep === 1) {
      return state.hardware.length > 0;
    }

    if (activeStep === 2) {
      return selectedHardware.length > 0 && Object.keys(state.connectorResults).length === selectedHardware.length;
    }

    return true;
  };

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      setIsComplete(true);
      return;
    }

    setActiveStep((value) => Math.min(value + 1, steps.length - 1));
  };

  const handlePrevious = () => {
    setActiveStep((value) => Math.max(value - 1, 0));
  };

  return (
    <section className="setup-wizard">
      <header>
        <h1>Base Station Setup</h1>
        <p>Guide new deployments through station configuration, hardware selection, and connector validation.</p>
      </header>
      <nav className="setup-wizard__steps" aria-label="Setup progress">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`setup-wizard__step${index === activeStep ? ' setup-wizard__step--active' : ''}`}
            aria-current={index === activeStep ? 'step' : undefined}
          >
            {step.label}
          </div>
        ))}
      </nav>
      {currentStep.content}
      <div className="setup-actions">
        <button type="button" onClick={handlePrevious} disabled={activeStep === 0}>
          Previous
        </button>
        <button type="button" onClick={handleNext} disabled={!canMoveNext()}>
          {activeStep === steps.length - 1 ? 'Finish setup' : 'Next'}
        </button>
      </div>
      {isComplete && (
        <div className="setup-summary" data-testid="setup-summary">
          <h3>Setup complete</h3>
          <p>
            {state.station.name} ({state.station.slug}) is ready for tasking. Provisioned connectors:{' '}
            {selectedHardware.map((connector) => connector.name).join(', ')}.
          </p>
        </div>
      )}
    </section>
  );
};

export default SetupWizard;
