import { useState } from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useOrchestrator } from '@/hooks/useOrchestrator';
import type { StepStatus } from '@/hooks/types';

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'running') return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
  if (status === 'done')    return <CheckCircle2 className="h-4 w-4 text-green-600" />;
  if (status === 'failed')  return <XCircle className="h-4 w-4 text-red-600" />;
  return <span className="h-4 w-4 flex items-center justify-center text-muted-foreground">·</span>;
}

export function OrchestratorView() {
  const [request, setRequest] = useState('');
  const { phase, plan, stepStatuses, error, start, approve, cancel, reset } = useOrchestrator();

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
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => (
                <div key={step.id} className="rounded-md border p-3">
                  <span className="text-xs text-muted-foreground">Step {i + 1}</span>
                  <p className="font-medium">{step.description}</p>
                  <p className="text-xs text-muted-foreground">{step.agent}</p>
                </div>
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
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => {
                const status: StepStatus = stepStatuses[step.id] ?? 'pending';
                return (
                  <div key={step.id} className="rounded-md border p-3 flex items-start gap-3">
                    <div className="mt-0.5">
                      <StepIcon status={status} />
                    </div>
                    <div>
                      <span className="text-xs text-muted-foreground">Step {i + 1}</span>
                      <p className="font-medium">{step.description}</p>
                      <p className="text-xs text-muted-foreground">{step.agent}</p>
                    </div>
                  </div>
                );
              })}
            </div>
            <Button variant="outline" onClick={cancel}>Cancel</Button>
          </div>
        )}

        {phase === 'done' && (
          <div className="flex flex-col items-center gap-4">
            <CheckCircle2 className="h-10 w-10 text-green-600" />
            <p className="font-medium">Done</p>
            <Button variant="outline" onClick={reset}>Run another</Button>
          </div>
        )}

        {phase === 'cancelled' && (
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
