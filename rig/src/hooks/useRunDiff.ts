import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { TrajectoryFile, RunDiff, MetaDiffRow, StepDiffEntry } from './types';

function formatTools(tools: string[]): string {
  return tools.length ? tools.join(', ') : '—';
}

function formatCost(usd: number | null): string {
  if (usd === null) return '—';
  if (usd >= 1) return `$${usd.toFixed(2)}`;
  return `$${usd.toFixed(4)}`;
}

function computeTotalLatency(traj: TrajectoryFile): number {
  return traj.events
    .filter((e) => e.event_type === 'llm_responded')
    .reduce((sum, e) => sum + ((e.payload['latency_ms'] as number | undefined) ?? 0), 0);
}

function toolsForStep(traj: TrajectoryFile, step: number): string[] {
  return traj.events
    .filter((e) => e.step === step && e.event_type === 'tool_called')
    .map((e) => (e.payload['tool_name'] as string | undefined) ?? '?');
}

function computeTotalInputTokens(traj: TrajectoryFile): number | null {
  const events = traj.events.filter((e) => e.event_type === 'llm_responded');
  const hasData = events.some((e) => e.payload['input_tokens'] != null);
  if (!hasData) return null;
  return events.reduce(
    (sum, e) => sum + ((e.payload['input_tokens'] as number | null) ?? 0), 0
  );
}

function computeTotalOutputTokens(traj: TrajectoryFile): number | null {
  const events = traj.events.filter((e) => e.event_type === 'llm_responded');
  const hasData = events.some((e) => e.payload['output_tokens'] != null);
  if (!hasData) return null;
  return events.reduce(
    (sum, e) => sum + ((e.payload['output_tokens'] as number | null) ?? 0), 0
  );
}

function computeTotalCost(traj: TrajectoryFile): number | null {
  const events = traj.events.filter((e) => e.event_type === 'llm_responded');
  const hasData = events.some((e) => e.payload['cost_usd'] != null);
  if (!hasData) return null;
  return events.reduce(
    (sum, e) => sum + ((e.payload['cost_usd'] as number | null) ?? 0), 0
  );
}

function terminalReason(traj: TrajectoryFile): string {
  const e = traj.events.find((e) => e.event_type === 'run_complete');
  return (e?.payload['reason'] as string | undefined) ?? '—';
}

function computeDiff(a: TrajectoryFile, b: TrajectoryFile): RunDiff {
  const latA = computeTotalLatency(a);
  const latB = computeTotalLatency(b);

  const fields: Array<[string, string, string]> = [
    ['Model',           a.meta.model,                b.meta.model],
    ['Provider',        a.meta.provider,             b.meta.provider],
    ['Mode',            a.meta.mode,                 b.meta.mode],
    ['Step count',      String(a.meta.step_count),   String(b.meta.step_count)],
    ['Max steps',       String(a.meta.max_steps),    String(b.meta.max_steps)],
    ['Total latency',   latA ? `${latA.toLocaleString()} ms` : '—',
                        latB ? `${latB.toLocaleString()} ms` : '—'],
    ['Terminal reason', terminalReason(a),           terminalReason(b)],
    ['Tools',           formatTools(a.meta.tools),   formatTools(b.meta.tools)],
    ['Input tokens',
      computeTotalInputTokens(a) !== null ? computeTotalInputTokens(a)!.toLocaleString() : '—',
      computeTotalInputTokens(b) !== null ? computeTotalInputTokens(b)!.toLocaleString() : '—'],
    ['Output tokens',
      computeTotalOutputTokens(a) !== null ? computeTotalOutputTokens(a)!.toLocaleString() : '—',
      computeTotalOutputTokens(b) !== null ? computeTotalOutputTokens(b)!.toLocaleString() : '—'],
    ['Total cost',     formatCost(computeTotalCost(a)), formatCost(computeTotalCost(b))],
  ];

  const meta_rows: MetaDiffRow[] = fields.map(([field, va, vb]) => ({
    field,
    a: va,
    b: vb,
    differs: va !== vb,
  }));

  const stepsA = new Set(a.events.map((e) => e.step));
  const stepsB = new Set(b.events.map((e) => e.step));
  const allSteps = Array.from(new Set([...stepsA, ...stepsB])).sort((x, y) => x - y);

  const step_rows: StepDiffEntry[] = allSteps.map((step) => {
    const inA = stepsA.has(step);
    const inB = stepsB.has(step);
    const tools_a = inA ? toolsForStep(a, step) : [];
    const tools_b = inB ? toolsForStep(b, step) : [];
    const differs = !inA || !inB || JSON.stringify(tools_a) !== JSON.stringify(tools_b);
    return { step, tools_a, tools_b, differs, only_in_a: inA && !inB, only_in_b: inB && !inA };
  });

  return {
    meta_rows,
    step_rows,
    any_differs: meta_rows.some((r) => r.differs) || step_rows.some((r) => r.differs),
  };
}

export function useRunDiff(runIdA: string | null, runIdB: string | null) {
  const [trajectoryA, setTrajectoryA] = useState<TrajectoryFile | null>(null);
  const [trajectoryB, setTrajectoryB] = useState<TrajectoryFile | null>(null);
  const [diff,        setDiff]        = useState<RunDiff | null>(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState<string | null>(null);

  useEffect(() => {
    if (!runIdA || !runIdB) {
      setTrajectoryA(null);
      setTrajectoryB(null);
      setDiff(null);
      return;
    }

    setLoading(true);
    setError(null);

    Promise.all([
      invoke<TrajectoryFile>('trajectory_load', { runId: runIdA }),
      invoke<TrajectoryFile>('trajectory_load', { runId: runIdB }),
    ])
      .then(([a, b]) => {
        setTrajectoryA(a);
        setTrajectoryB(b);
        setDiff(computeDiff(a, b));
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, [runIdA, runIdB]);

  return { trajectoryA, trajectoryB, diff, loading, error };
}
