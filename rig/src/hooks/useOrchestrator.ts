import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import {
  OrchestratorPhase, OrchestratorPlan, PollResult, StepStatus
} from './types';

export function useOrchestrator() {
  const [phase,        setPhase]        = useState<OrchestratorPhase>('idle');
  const [jobId,        setJobId]        = useState<string | null>(null);
  const [plan,         setPlan]         = useState<OrchestratorPlan | null>(null);
  const [stepStatuses, setStepStatuses] = useState<Record<string, StepStatus>>({});
  const [error,        setError]        = useState<string | null>(null);

  const processMessage = useCallback((msg: Record<string, unknown>) => {
    switch (msg.type) {
      case 'plan':
        setPlan(msg as unknown as OrchestratorPlan);
        setStepStatuses(
          Object.fromEntries(
            (msg.steps as { id: string }[]).map((s) => [s.id, 'pending' as StepStatus])
          )
        );
        setPhase('plan_ready');
        break;
      case 'step_started':
        setStepStatuses((prev) => ({ ...prev, [msg.step_id as string]: 'running' as StepStatus }));
        break;
      case 'step_complete':
        setStepStatuses((prev) => ({
          ...prev,
          [msg.step_id as string]: (msg.status === 'done' ? 'done' : 'failed') as StepStatus,
        }));
        break;
      case 'orchestration_complete':
        setPhase('done');
        break;
      case 'orchestration_cancelled':
        setPhase('cancelled');
        break;
    }
  }, []);

  useEffect(() => {
    const terminal: OrchestratorPhase[] = ['idle', 'done', 'cancelled', 'error'];
    if (!jobId || terminal.includes(phase)) return;

    const id = setInterval(async () => {
      try {
        const result = await invoke<PollResult>('orchestrate_poll', { job_id: jobId });
        result.messages.forEach(processMessage);
      } catch (e) {
        setError(String(e));
        setPhase('error');
      }
    }, 1000);

    return () => clearInterval(id);
  }, [jobId, phase, processMessage]);

  const start = useCallback(async (request: string) => {
    setPhase('planning');
    setPlan(null);
    setStepStatuses({});
    setError(null);
    try {
      const id = await invoke<string>('orchestrate_start', { request });
      setJobId(id);
    } catch (e) {
      setError(String(e));
      setPhase('error');
    }
  }, []);

  const approve = useCallback(async (approved: boolean) => {
    if (!jobId) return;
    if (approved) setPhase('executing');
    try {
      await invoke('orchestrate_approve', { job_id: jobId, approved });
      if (!approved) setPhase('cancelled');
    } catch (e) {
      setError(String(e));
      setPhase('error');
    }
  }, [jobId]);

  const cancel = useCallback(async () => {
    if (!jobId) return;
    await invoke('orchestrate_cancel', { job_id: jobId }).catch(() => {});
    setPhase('cancelled');
  }, [jobId]);

  const reset = useCallback(() => {
    setPhase('idle');
    setJobId(null);
    setPlan(null);
    setStepStatuses({});
    setError(null);
  }, []);

  return { phase, plan, stepStatuses, error, start, approve, cancel, reset };
}
