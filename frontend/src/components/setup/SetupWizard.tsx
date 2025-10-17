import { useMemo, useState } from 'react';

interface SetupWizardProps {
  open: boolean;
  onClose: () => void;
}

interface WizardStep {
  title: string;
  description: string;
  action: string;
}

const wizardSteps: WizardStep[] = [
  {
    title: 'Connect services',
    description: 'Provide ChatKit and AgentKit credentials so the station can orchestrate missions.',
    action: 'Open configuration docs',
  },
  {
    title: 'Seed telemetry',
    description: 'Load offline captures or enable live connectors for ADS-B, AIS, and GPS feeds.',
    action: 'Review connector catalog',
  },
  {
    title: 'Invite operators',
    description: 'Share the station callsign and invite Ops, Intel, and Logistics roles to ChatKit.',
    action: 'Send invitation email',
  },
];

const SetupWizard = ({ open, onClose }: SetupWizardProps) => {
  const [stepIndex, setStepIndex] = useState(0);
  const step = useMemo(() => wizardSteps[stepIndex], [stepIndex]);

  if (!open) {
    return null;
  }

  const goNext = () => {
    setStepIndex((index) => Math.min(index + 1, wizardSteps.length - 1));
  };

  const goPrevious = () => {
    setStepIndex((index) => Math.max(index - 1, 0));
  };

  return (
    <div className="setup-wizard__backdrop" role="presentation">
      <div className="setup-wizard" role="dialog" aria-modal="true" aria-labelledby="setup-wizard-heading">
        <header className="setup-wizard__header">
          <h2 id="setup-wizard-heading">Station setup wizard</h2>
          <button type="button" onClick={onClose} aria-label="Close setup wizard">
            Close
          </button>
        </header>
        <div className="setup-wizard__body">
          <div className="setup-wizard__progress" aria-hidden="true">
            Step {stepIndex + 1} of {wizardSteps.length}
          </div>
          <h3>{step.title}</h3>
          <p>{step.description}</p>
          <button type="button" className="setup-wizard__primary">
            {step.action}
          </button>
        </div>
        <footer className="setup-wizard__footer">
          <button type="button" onClick={goPrevious} disabled={stepIndex === 0}>
            Previous
          </button>
          {stepIndex < wizardSteps.length - 1 ? (
            <button type="button" onClick={goNext} data-testid="wizard-next">
              Next
            </button>
          ) : (
            <button type="button" onClick={onClose} data-testid="wizard-finish">
              Finish
            </button>
          )}
        </footer>
      </div>
    </div>
  );
};

export default SetupWizard;
