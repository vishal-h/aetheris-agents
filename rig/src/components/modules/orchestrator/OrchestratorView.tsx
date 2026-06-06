import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useOrchestrator } from '@/hooks/useOrchestrator';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import type { PlanStep, StepStatus } from '@/hooks/types';

// ── Config hints — which env vars are relevant for each agent ─────────────────

const STEP_CONFIG_HINTS: Record<string, string[]> = {
  'drive/agents/drive_orchestrator.exs':               ['GOOGLE_SERVICE_ACCOUNT', 'DRIVE_ROOT_FOLDER_ID'],
  'email/agents/email_orchestrator.exs':               ['SMTP_TO', 'SMTP_FROM'],
  'provenance/agents/scan_orchestrator.exs':           ['PROVENANCE_NAS_PATH'],
  'provenance/agents/classification_orchestrator.exs': [],
};

// ── Sub-components ─────────────────────────────────────────────────────────────

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'running') return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
  if (status === 'done')    return <CheckCircle2 className="h-4 w-4 text-green-600" />;
  if (status === 'failed')  return <XCircle className="h-4 w-4 text-red-600" />;
  return <span className="h-4 w-4 flex items-center justify-center text-muted-foreground">·</span>;
}

function ParamsStrip({ params }: { params: Record<string, string> }) {
  const entries = Object.entries(params);
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs font-mono text-muted-foreground">
      {entries.map(([k, v]) => (
        <span key={k}>{k} = {v}</span>
      ))}
    </div>
  );
}

interface StepCardProps {
  step:         PlanStep;
  index:        number;
  configValues: Record<string, string>;
  status?:      StepStatus;
}

function StepCard({ step, index, configValues, status }: StepCardProps) {
  const hints = STEP_CONFIG_HINTS[step.agent] ?? [];
  const configLines = hints
    .filter((k) => configValues[k] !== undefined && configValues[k] !== '')
    .map((k) => `${k}: ${configValues[k]}`);

  return (
    <div className="rounded-md border p-3 flex items-start gap-3">
      {status !== undefined && (
        <div className="mt-0.5 shrink-0">
          <StepIcon status={status} />
        </div>
      )}
      {status === undefined && (
        <div className="mt-0.5 shrink-0 w-4" />
      )}
      <div className="min-w-0 flex-1">
        <span className="text-xs text-muted-foreground">Step {index + 1}</span>
        <p className="font-medium">{step.description}</p>
        <p className="text-xs text-muted-foreground font-mono">{step.agent}</p>
        {step.context && step.context !== '' && (
          <p className="text-xs text-muted-foreground italic mt-1">{step.context}</p>
        )}
        {configLines.length > 0 && (
          <div className="mt-1.5 flex flex-col gap-0.5">
            {configLines.map((line) => (
              <p key={line} className="text-xs font-mono text-muted-foreground">{line}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function OrchestratorView() {
  const location = useLocation();
  const prefill  = (location.state as { prefill?: string } | null)?.prefill ?? '';
  const [request, setRequest] = useState(prefill);
  const { phase, plan, params, stepStatuses, error, start, approve, cancel, reset } = useOrchestrator();
  const { values: configValues } = useAgentConfig();

  return (
    <div className="flex flex-col items-center">
      <div className="w-full max-w-[600px] flex flex-col gap-6">

        {phase === 'idle' && (
          <div className="flex flex-col gap-4">
            <h2 className="text-lg font-semibold">Orchestrator</h2>
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm
                         placeholder:text-muted-foreground focus-visible:outline-none
                         focus-visible:ring-2 focus-visible:ring-ring resize-none"
              rows={3}
              placeholder="Describe what you want to do…"
              value={request}
              onChange={(e) => setRequest(e.target.value)}
            />
            <Button onClick={() => start(request)} disabled={!request.trim()}>
              Run
            </Button>
          </div>
        )}

        {phase === 'planning' && (
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Planning…</span>
          </div>
        )}

        {phase === 'plan_ready' && plan && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
            <ParamsStrip params={params} />
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => (
                <StepCard
                  key={step.id}
                  step={step}
                  index={i}
                  configValues={configValues}
                />
              ))}
            </div>
            <div className="flex gap-3">
              <Button onClick={() => approve(true)}>Approve</Button>
              <Button variant="outline" onClick={() => approve(false)}>Cancel</Button>
            </div>
          </div>
        )}

        {phase === 'executing' && plan && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
            <ParamsStrip params={params} />
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => (
                <StepCard
                  key={step.id}
                  step={step}
                  index={i}
                  configValues={configValues}
                  status={stepStatuses[step.id] ?? 'pending'}
                />
              ))}
            </div>
            <Button variant="outline" onClick={cancel}>Cancel</Button>
          </div>
        )}

        {phase === 'done' && plan && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
            <ParamsStrip params={params} />
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => (
                <StepCard
                  key={step.id}
                  step={step}
                  index={i}
                  configValues={configValues}
                  status={stepStatuses[step.id] ?? 'done'}
                />
              ))}
            </div>
            <div className="flex flex-col items-center gap-3 pt-2">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
              <p className="font-medium">Done</p>
              <Button variant="outline" onClick={reset}>Run another</Button>
            </div>
          </div>
        )}

        {phase === 'cancelled' && plan && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
            <ParamsStrip params={params} />
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => (
                <StepCard
                  key={step.id}
                  step={step}
                  index={i}
                  configValues={configValues}
                  status={stepStatuses[step.id] ?? 'pending'}
                />
              ))}
            </div>
            <div className="flex flex-col items-center gap-3 pt-2">
              <p className="text-muted-foreground">Cancelled.</p>
              <Button variant="outline" onClick={reset}>Run another</Button>
            </div>
          </div>
        )}

        {phase === 'cancelled' && !plan && (
          <div className="flex flex-col items-center gap-4">
            <p className="text-muted-foreground">Cancelled.</p>
            <Button variant="outline" onClick={reset}>Run another</Button>
          </div>
        )}

        {phase === 'error' && (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-red-600">{error}</p>
            <Button variant="outline" onClick={reset}>Run another</Button>
          </div>
        )}

      </div>
    </div>
  );
}
