import { useState, useEffect, useRef, type ReactNode } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ChevronDown, ChevronRight, Download, GitBranch, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTrajectory, useRunEvents, useRunDetail, useFork } from '@/hooks';
import type { RunSummary, TrajectoryEvent, TrajectoryFile, TokenSummary } from '@/hooks/types';
import { reconstructTrajectory, reconstructedBanner } from '@/lib/reconstructTrajectory';

const EVENT_COLOURS: Record<string, string> = {
  prompt_built:           'bg-blue-100 text-blue-800',
  llm_called:             'bg-purple-100 text-purple-800',
  llm_responded:          'bg-violet-100 text-violet-800',
  tool_called:            'bg-amber-100 text-amber-800',
  tool_result:            'bg-orange-100 text-orange-800',
  step_complete:          'bg-green-100 text-green-800',
  run_complete:           'bg-green-200 text-green-900',
  error:                  'bg-red-100 text-red-800',
  agent_message_sent:     'bg-sky-100 text-sky-800',
  agent_message_received: 'bg-sky-100 text-sky-800',
};

function eventColour(type: string): string {
  return EVENT_COLOURS[type] ?? 'bg-muted text-muted-foreground';
}

// ── Token / cost helpers ──────────────────────────────────────────────────────

function computeTokenSummary(events: TrajectoryEvent[]): TokenSummary {
  const llmEvents = events.filter((e) => e.event_type === 'llm_responded');

  if (llmEvents.length === 0) {
    return { input_tokens: null, output_tokens: null, cost_usd: null, llm_calls: 0 };
  }

  const hasData = llmEvents.some((e) => e.payload['cost_usd'] != null);

  if (!hasData) {
    return { input_tokens: null, output_tokens: null, cost_usd: null, llm_calls: llmEvents.length };
  }

  const input_tokens = llmEvents.reduce(
    (sum, e) => sum + ((e.payload['input_tokens'] as number | null) ?? 0), 0
  );
  const output_tokens = llmEvents.reduce(
    (sum, e) => sum + ((e.payload['output_tokens'] as number | null) ?? 0), 0
  );
  const cost_usd = llmEvents.reduce(
    (sum, e) => sum + ((e.payload['cost_usd'] as number | null) ?? 0), 0
  );

  return { input_tokens, output_tokens, cost_usd, llm_calls: llmEvents.length };
}

function formatCost(usd: number | null): string {
  if (usd === null) return '—';
  if (usd >= 1) return `$${usd.toFixed(2)}`;
  return `$${usd.toFixed(4)}`;
}

function formatTokens(n: number | null): string {
  if (n === null) return '—';
  return n.toLocaleString();
}

function TokenSummaryRows({ events }: { events: TrajectoryEvent[] }) {
  const summary = computeTokenSummary(events);
  if (summary.llm_calls === 0) return null;
  return (
    <>
      <MetaRow label="LLM calls"     value={String(summary.llm_calls)} />
      <MetaRow label="Input tokens"  value={formatTokens(summary.input_tokens)} />
      <MetaRow label="Output tokens" value={formatTokens(summary.output_tokens)} />
      <MetaRow label="Cost"          value={formatCost(summary.cost_usd)} />
    </>
  );
}

function EventRow({ event }: { event: TrajectoryEvent }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b last:border-b-0">
      <button
        className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted/50 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-xs font-mono text-muted-foreground w-8 shrink-0">
          {event.seq}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${eventColour(event.event_type)}`}>
          {event.event_type}
        </span>
        <span className="text-xs text-muted-foreground ml-auto shrink-0">
          {new Date(event.timestamp).toISOString().replace('T', ' ').slice(0, 23)}
        </span>
        {open
          ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
          : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />}
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs font-mono bg-muted/30 overflow-x-auto whitespace-pre-wrap break-all">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

interface StepGroupProps {
  step:        number;
  events:      TrajectoryEvent[];
  /** True while any fork on this trajectory is in flight — disables all fork buttons. */
  isForking:   boolean;
  /** The step whose fork is currently in flight (shows the spinner), or null. */
  forkingStep: number | null;
  /** Fires when the fork button for this step is pressed. Absent → no fork affordance. */
  onFork?:     (step: number) => void;
}

function StepGroup({ step, events, isForking, forkingStep, onFork }: StepGroupProps) {
  const [open, setOpen] = useState(true);

  // Fork points are steps with a recorded `:step_complete` event (determinism
  // contract §4 F2 — matched exactly, no fallback). A terminal text step emits
  // `run_complete`, not `step_complete`, so the final step is never forkable.
  const forkable = onFork !== undefined && events.some((e) => e.event_type === 'step_complete');
  const thisForking = forkingStep === step;

  return (
    <div className="border rounded-md mb-2">
      {/* Header row: the toggle and the fork control are siblings — a <button>
          nested in a <button> is invalid HTML (rig/CLAUDE.md nested-clickable rule). */}
      <div className="flex items-center gap-2 pr-2 hover:bg-muted/50 transition-colors">
        <button
          className="flex-1 flex items-center gap-2 px-3 py-2 text-left font-medium text-sm"
          onClick={() => setOpen((o) => !o)}
        >
          {open
            ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
            : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          Step {step}
          <span className="ml-2 text-xs text-muted-foreground font-normal">
            {events.length} event{events.length !== 1 ? 's' : ''}
          </span>
        </button>
        {forkable && (
          <Button
            variant="outline"
            size="xs"
            disabled={isForking}
            title="Fork a new run that replays this run's transcript up to and including this step, then continues live. Transcript prefix and seed are carried; the environment (filesystem, clock) is fresh."
            onClick={(e) => {
              e.stopPropagation();
              onFork?.(step);
            }}
          >
            {thisForking
              ? <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />Forking…</>
              : <><GitBranch className="h-3.5 w-3.5 mr-1.5" />Fork from here</>}
          </Button>
        )}
      </div>
      {open && (
        <div className="border-t">
          {events.map((e) => <EventRow key={e.id} event={e} />)}
        </div>
      )}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-muted-foreground shrink-0 w-24">{label}</span>
      <span className="font-mono truncate">{value}</span>
    </div>
  );
}

function ExpandableText({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);
  const preview = text?.slice(0, 120);

  return (
    <div className="mb-1">
      <button
        className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        onClick={() => setOpen((o) => !o)}
      >
        {open
          ? <ChevronDown className="h-3 w-3" />
          : <ChevronRight className="h-3 w-3" />}
        {label}
      </button>
      {open
        ? <pre className="mt-1 text-xs font-mono bg-muted/30 rounded p-2 whitespace-pre-wrap break-all">{text}</pre>
        : <p className="mt-0.5 text-xs text-muted-foreground truncate">{preview}{text?.length > 120 ? '…' : ''}</p>
      }
    </div>
  );
}

function CentredMessage({ children }: { children: ReactNode }) {
  return (
    <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
      {children}
    </div>
  );
}

interface Props {
  run: RunSummary | null;
  /** Called with the child run id when a fork resolves — lets the host surface it. */
  onForked?: (runId: string) => void;
}

/**
 * Trajectory viewer with a live-run fallback (BL-005).
 *
 * The primary source is the atomically-written `trajectory.json`, loaded via
 * `useTrajectory`. That file exists only after a clean run end, so for running
 * runs — and for runs swept from orphaned state (BL-003), which never get a
 * file — the load fails. On failure we rebuild the identical view from the live
 * SQLite event stream (`harness_get_events`) plus `runs.config_json`
 * (`harness_get_run`), showing a banner that names the source. The fallback DB
 * queries are gated to fire only after the file load has failed, so completed
 * runs are unaffected.
 */
export function TrajectoryView({ run, onForked }: Props) {
  const runId = run?.run_id ?? null;
  const { trajectory: fileTrajectory, loading: fileLoading, error: fileError } =
    useTrajectory(runId);

  // Only reach for the event stream once the file load has failed. Gating the
  // run_id to null until then means a completed run (file present) never issues
  // the extra queries. Poll while the run is live so the view appends events.
  const fileMissing = fileError !== null;
  const fallbackRunId = fileMissing ? runId : null;
  const events = useRunEvents(fallbackRunId, { polling: run?.status === 'running' });
  const detail = useRunDetail(fallbackRunId);

  // Preserve the interrupted-write / corrupt-file signal the runbook documents:
  // the banner reports the file as "unavailable" generically, so log the actual
  // read error once when the fallback engages (e.g. a truncated `.tmp`).
  useEffect(() => {
    if (fileError !== null) {
      console.warn(`[TrajectoryView] trajectory_load failed for ${runId}; reconstructing from events: ${fileError}`);
    }
  }, [fileError, runId]);

  if (!runId) {
    return <CentredMessage>Select a run to view its trajectory.</CentredMessage>;
  }

  // Active file load — show Loading. Checked before the file-present branch so
  // a reload never flashes the previously-selected run's trajectory (useTrajectory
  // holds the prior value until the new load settles).
  if (fileLoading) {
    return <CentredMessage>Loading…</CentredMessage>;
  }

  // File load failed — reconstruct the view from the live event stream. Handled
  // before the file-present branch because on a failed load `fileTrajectory`
  // still holds the previous run's (stale) value.
  if (fileMissing) {
    // Events are required; config (from harness_get_run) is best-effort and only
    // enriches meta, so a detail error does not block reconstruction.
    const eventsPending = events.data === null && events.error === null;
    const detailPending = detail.data === null && detail.error === null;
    if (eventsPending || detailPending) {
      return <CentredMessage>Loading…</CentredMessage>;
    }

    if (events.error !== null) {
      // Neither the file nor the event stream is available — surface the original
      // trajectory-load error the user was trying to resolve.
      return <div className="p-4 text-sm text-red-600">{fileError}</div>;
    }

    const reconstructed = reconstructTrajectory(
      runId,
      run,
      detail.data?.config ?? null,
      events.data ?? [],
    );

    return (
      <TrajectoryBody
        trajectory={reconstructed}
        banner={reconstructedBanner(run?.status)}
        isPolling={events.isPolling}
        showExport={false}
        canFork={false}
        onForked={onForked}
      />
    );
  }

  // File loaded successfully — render it exactly as before.
  if (fileTrajectory) {
    // A fork inherits its parent's label verbatim (BL-029 rider). Two ways `label`
    // is not a real label, both of which must degrade to an unlabelled fork rather
    // than to a synthesized one:
    //   - server-side it is COALESCE(runs.label, run_id), so an unlabelled parent
    //     yields the run_id — inheriting that writes a run_id into the child's label;
    //   - the synthesized post-fork summary (RunList.tsx `handleForked`) carries
    //     label: '', so forking a fork before a Refresh would inherit Some("").
    const parentLabel =
      run && run.label && run.label !== run.run_id ? run.label : undefined;
    return <TrajectoryBody trajectory={fileTrajectory} banner={null} isPolling={false} showExport canFork parentLabel={parentLabel} onForked={onForked} />;
  }

  // First render, before the useTrajectory effect has started the load.
  return <CentredMessage>Loading…</CentredMessage>;
}

interface TrajectoryBodyProps {
  trajectory: TrajectoryFile;
  /** Reconstructed-source banner text, or null for the file-backed view. */
  banner: string | null;
  isPolling: boolean;
  showExport: boolean;
  /** Whether forking is offered. Only the file-backed view can fork — a running /
   *  orphan-swept run has no trajectory.json, so the fork CLI's source load would
   *  always fail (offered-but-always-fails). Reconstructed path passes false. */
  canFork: boolean;
  /** The parent run's label, inherited verbatim by a fork — or undefined, which
   *  leaves the fork unlabelled (Rust `Option::None`). Never a synthesized or
   *  suffixed value: an unlabelled fork is legible, an invented label is not.
   *  The caller is responsible for the run_id-fallback guard (see :302). */
  parentLabel?: string;
  /** Called with the child run id when a fork resolves. */
  onForked?: (runId: string) => void;
}

function TrajectoryBody({ trajectory, banner, isPolling, showExport, canFork, parentLabel, onForked }: TrajectoryBodyProps) {
  const [metaOpen, setMetaOpen] = useState(true);
  const { fork, forking, error, clearError } = useFork();
  const [forkingStep, setForkingStep] = useState<number | null>(null);

  // A fork blocks to completion (minutes). If the user selects another run or leaves
  // the Trajectory tab meanwhile, this body unmounts (run change → the fileLoading
  // branch swaps in CentredMessage; tab switch → Radix TabsContent unmounts inactive
  // content). The pending promise still resolves, but `onForked` lives on the
  // still-mounted HarnessRoute, so an unguarded resolve would yank the user to the
  // child from wherever they navigated. Skip *navigation* once unmounted; the child
  // then lands silently and appears in Runs on the next refresh.
  //
  // Set `alive.current = true` in the effect BODY, not only in cleanup: React
  // StrictMode double-invokes effects in dev (mount → cleanup → remount), so a
  // cleanup-only latch leaves the ref stuck `false` from the first render — which
  // silently killed both the navigate and the spinner-clear on every press (dev is
  // the operator's environment). Re-arming in the body makes it StrictMode-safe.
  // (BL-007 t4 review r5.)
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);

  const { meta, events } = trajectory;

  // A run is a fork iff the harness wrote `meta.fork_from` (server.ex:720) — never
  // inferred from `meta.mode`, since CLI forks run in `:record` (determinism
  // contract §4). null-not-zero: the banner shows only when the field is present.
  const isFork = meta.fork_from != null;

  async function handleFork(step: number) {
    setForkingStep(step);
    try {
      const forkedRunId = await fork(trajectory.run_id, step, parentLabel);
      if (alive.current) onForked?.(forkedRunId);
    } catch {
      // Error is already surfaced via `error` (useFork sets it and rethrows).
    } finally {
      // Always clear the pressed-step spinner — only navigation is mount-guarded.
      // (A state set on an unmounted component is a no-op in React 18/19.)
      setForkingStep(null);
    }
  }

  const steps = events.reduce<Map<number, TrajectoryEvent[]>>((acc, e) => {
    const group = acc.get(e.step) ?? [];
    group.push(e);
    acc.set(e.step, group);
    return acc;
  }, new Map());

  const duration = meta.started_at && meta.finished_at
    ? Math.round(
        (new Date(meta.finished_at).getTime() - new Date(meta.started_at).getTime()) / 1000
      )
    : null;

  async function handleExport() {
    try {
      await invoke('trajectory_export', { runId: trajectory.run_id });
    } catch (e) {
      console.error('export failed', e);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Provenance banner — only on forked runs (meta.fork_from present). Copy is
          bounded by the determinism contract §4: transcript prefix + seed carried,
          environment fresh; no post-fork reproducibility claim. */}
      {isFork && (
        <div
          className="flex items-center gap-2 border-b bg-indigo-50 px-4 py-1.5 text-xs text-indigo-800 shrink-0"
          title="Transcript prefix and seed carried; environment (filesystem, clock) is fresh. Post-fork execution is live."
        >
          <GitBranch className="h-3.5 w-3.5 shrink-0" />
          <span>
            Forked from <span className="font-mono">{meta.fork_from}</span>
            {meta.fork_step != null && <> @ step {meta.fork_step}</>}
          </span>
        </div>
      )}

      {/* Fork error — surfaced from the rejected invoke promise, dismissible */}
      {error !== null && (
        <div className="flex items-start gap-2 border-b border-destructive/40 bg-destructive/5 px-4 py-2 text-xs text-destructive shrink-0">
          <span className="flex-1 whitespace-pre-wrap break-all font-mono">Fork failed: {error}</span>
          <button
            className="shrink-0 hover:opacity-70"
            title="Dismiss"
            onClick={clearError}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Reconstructed-source banner — absent for the file-backed view */}
      {banner !== null && (
        <div className="flex items-center gap-2 border-b bg-amber-50 px-4 py-1.5 text-xs text-amber-800 shrink-0">
          {isPolling && (
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-500" />
            </span>
          )}
          {banner}
        </div>
      )}

      {/* Meta panel */}
      <div className="border-b shrink-0">
        <div className="flex items-center justify-between px-4 py-2">
          <button
            className="flex items-center gap-2 text-sm font-medium hover:text-foreground text-muted-foreground transition-colors"
            onClick={() => setMetaOpen((o) => !o)}
          >
            {metaOpen
              ? <ChevronDown className="h-4 w-4" />
              : <ChevronRight className="h-4 w-4" />}
            Run metadata
          </button>
          {showExport && (
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-3.5 w-3.5 mr-1.5" />
              Export JSON
            </Button>
          )}
        </div>

        {metaOpen && (
          <div className="px-4 pb-3 grid grid-cols-2 gap-x-8 gap-y-1 text-xs">
            <MetaRow label="Model"    value={meta.model} />
            <MetaRow label="Provider" value={meta.provider} />
            <MetaRow label="Mode"     value={meta.mode} />
            <MetaRow label="Steps"    value={`${meta.step_count} / ${meta.max_steps}`} />
            {duration !== null &&
              <MetaRow label="Duration" value={`${duration}s`} />}
            <MetaRow label="Tools" value={meta.tools.join(', ') || '—'} />
            <TokenSummaryRows events={events} />
            <div className="col-span-2 mt-1">
              <ExpandableText label="System prompt" text={meta.system_prompt} />
            </div>
            <div className="col-span-2">
              <ExpandableText label="User prompt" text={meta.user_prompt} />
            </div>
          </div>
        )}
      </div>

      {/* Event stream */}
      <div className="flex-1 overflow-y-auto p-4">
        {Array.from(steps.entries())
          .sort(([a], [b]) => a - b)
          .map(([step, evts]) => (
            <StepGroup
              key={step}
              step={step}
              events={evts}
              isForking={forking}
              forkingStep={forkingStep}
              onFork={canFork ? handleFork : undefined}
            />
          ))}
      </div>
    </div>
  );
}
