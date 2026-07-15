import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Link } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle, AlertCircle, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDocbuilder } from '@/hooks/useDocbuilder';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import type { PlanStep, StepStatus } from '@/hooks/types';

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'running') return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
  if (status === 'done')    return <CheckCircle2 className="h-4 w-4 text-green-600" />;
  if (status === 'failed')  return <XCircle className="h-4 w-4 text-red-600" />;
  return <span className="h-4 w-4 flex items-center justify-center text-muted-foreground">·</span>;
}

function StepRow({ step, index, status, error }: {
  step: PlanStep; index: number; status: StepStatus; error?: string;
}) {
  return (
    <div className="rounded-md border p-3 flex items-start gap-3">
      <div className="mt-0.5 shrink-0"><StepIcon status={status} /></div>
      <div className="min-w-0 flex-1">
        <span className="text-xs text-muted-foreground">Step {index + 1}</span>
        <p className="font-medium">{step.description}</p>
        <p className="text-xs text-muted-foreground font-mono">{step.agent}</p>
        {status === 'failed' && error && (
          <p className="text-xs text-red-600 mt-1 font-mono">{error}</p>
        )}
      </div>
    </div>
  );
}

export function DocbuilderView() {
  const [request, setRequest] = useState('');
  const [outputs, setOutputs] = useState<string[] | null>(null);
  const { phase, plan, stepStatuses, stepErrors, error, run, reset } = useDocbuilder();
  const { values: config } = useAgentConfig();
  const tenant = config['DOCBUILDER_TENANT'];

  // On completion, read the orchestrator's rename record for the rendered file list.
  // Best-effort — a missing/unparseable file just shows a generic completion message.
  useEffect(() => {
    if (phase !== 'done') return;
    invoke<string>('tools_read_script', { useCase: 'docbuilder', file: 'output/renamed.json' })
      .then((raw) => {
        try {
          const arr = JSON.parse(raw) as { original: string; renamed: string }[];
          setOutputs(arr.map((e) => e.renamed.split('/').pop() ?? e.renamed));
        } catch {
          setOutputs([]);
        }
      })
      .catch(() => setOutputs([]));
  }, [phase]);

  const handleReset = () => { setOutputs(null); reset(); };

  return (
    <div className="flex flex-col items-center">
      <div className="w-full max-w-[600px] flex flex-col gap-6">

        {phase === 'idle' && (
          <div className="flex flex-col gap-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="h-5 w-5" /> Docbuilder
            </h2>

            {tenant
              ? <p className="text-sm text-muted-foreground">Tenant: <span className="font-mono">{tenant}</span></p>
              : (
                <p className="text-sm text-amber-600">
                  No tenant configured.{' '}
                  <Link to="/settings" className="underline">Set DOCBUILDER_TENANT in Settings</Link>.
                </p>
              )}

            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm
                         placeholder:text-muted-foreground focus-visible:outline-none
                         focus-visible:ring-2 focus-visible:ring-ring resize-none"
              rows={3}
              placeholder="Invoice for XYZ for June 2026, same as last month"
              value={request}
              onChange={(e) => setRequest(e.target.value)}
            />
            <Button onClick={() => run(request)} disabled={!request.trim() || !tenant}>
              Run
            </Button>
          </div>
        )}

        {phase === 'planning' && (
          <div className="flex items-center gap-3 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Starting…</span>
          </div>
        )}

        {plan && phase !== 'idle' && phase !== 'planning' && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
            <div className="flex flex-col gap-2">
              {plan.steps.map((step, i) => (
                <StepRow
                  key={step.id}
                  step={step}
                  index={i}
                  status={stepStatuses[step.id] ?? 'pending'}
                  error={stepErrors[step.id]}
                />
              ))}
            </div>

            {phase === 'done' && (() => {
              const anyFailed = Object.values(stepStatuses).some((s) => s === 'failed');
              return (
                <div className="flex flex-col items-center gap-3 pt-2">
                  {anyFailed
                    ? <AlertCircle className="h-8 w-8 text-amber-500" />
                    : <CheckCircle2 className="h-8 w-8 text-green-600" />}
                  <p className="font-medium">{anyFailed ? 'Completed with errors' : 'Done'}</p>
                  {!anyFailed && outputs && outputs.length > 0 && (
                    <div className="w-full flex flex-col gap-1">
                      <p className="text-xs text-muted-foreground">Rendered files</p>
                      {outputs.map((f) => (
                        <p key={f} className="text-sm font-mono">{f}</p>
                      ))}
                    </div>
                  )}
                  {!anyFailed && outputs && outputs.length === 0 && (
                    <p className="text-sm text-muted-foreground">Run complete.</p>
                  )}
                  <Button variant="outline" onClick={handleReset}>Run another</Button>
                </div>
              );
            })()}
          </div>
        )}

        {phase === 'error' && (
          <div className="flex flex-col gap-3">
            <p className="text-sm text-red-600">{error}</p>
            <Button variant="outline" onClick={handleReset}>Run another</Button>
          </div>
        )}

      </div>
    </div>
  );
}
