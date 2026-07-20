import { Fragment, useState, useCallback, useEffect, useRef } from 'react';
import { useSessionRecord } from '@/hooks/useSessionRecord';
import { ChevronDown, ChevronRight, RefreshCw } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';
import { MainArea } from '@/components/shell/MainArea';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RunSummary } from '@/hooks/types';
import { useHarnessStatus, useRunList, useRunEvents } from '@/hooks';
import { NotConnected, LoadingShell } from './shared';
import { TrajectoryView } from './TrajectoryView';

// ============================================================================
// Helpers
// ============================================================================

function formatDuration(startedAt: string, finishedAt: string | null): string {
  if (!finishedAt) return '—';
  const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime();
  const secs = Math.round(ms / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

function statusBadgeVariant(status: string): 'success' | 'warning' | 'destructive' | 'default' {
  switch (status) {
    case 'done':    return 'success';
    case 'running': return 'warning';
    case 'failed':  return 'destructive';
    default:        return 'default';
  }
}

function eventTypeClass(type: string): string {
  switch (type) {
    case 'prompt_built':  return 'text-slate-500';
    case 'llm_called':    return 'text-purple-600';
    case 'llm_responded': return 'text-purple-800';
    case 'tool_called':   return 'text-blue-600';
    case 'tool_result':   return 'text-blue-800';
    case 'error':         return 'text-red-600';
    case 'run_complete':  return 'text-green-600';
    case 'step_complete': return 'text-slate-400';
    default:              return 'text-slate-600';
  }
}

function formatTokens(n: number | null): string {
  if (n === null) return '—';
  return n.toLocaleString();
}

/**
 * Token totals for the Cost cell's tooltip (BL-004). The runs table is at 8
 * columns, so tokens ride the existing Cost cell rather than adding a 9th.
 *
 * Returns undefined — not an empty string — when neither total is present, so
 * React omits the `title` attribute entirely and no blank tooltip appears on
 * stub/pre-instrumentation runs. null-not-zero: a run with genuine zero tokens
 * still renders "0".
 */
function tokenTooltip(run: RunSummary): string | undefined {
  if (run.total_input_tokens === null && run.total_output_tokens === null) {
    return undefined;
  }
  return `Tokens — in ${formatTokens(run.total_input_tokens)} · out ${formatTokens(run.total_output_tokens)}`;
}

function payloadPreview(payload: string): string {
  return payload.replace(/\s+/g, ' ').trim().slice(0, 120);
}

const SELECT_CLASS =
  'h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring';

// A running run with no activity for this long is shown as "stalled?"
const STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

// Both event.timestamp and runs.started_at are written by the harness via
// DateTime.to_iso8601 (store.ex:1019, 1512) — always Z-suffixed UTC ISO 8601.
// new Date() parses them correctly without timezone ambiguity.
function staleMinsAgo(referenceAt: string, now: number): number {
  return Math.floor((now - new Date(referenceAt).getTime()) / 60_000);
}

// ============================================================================
// Run grouping
// ============================================================================

const DEFAULT_SHOW = 10;

// Order matters — more specific prefixes must appear before less specific ones.
const USE_CASE_PREFIXES: Array<{ prefix: string; label: string }> = [
  { prefix: 'payslip',     label: 'Payslip' },
  { prefix: 'drive',       label: 'Drive' },
  { prefix: 'email',       label: 'Email' },
  { prefix: 'api-tenant',  label: 'API / Tenant' },
  { prefix: 'api-gateway', label: 'API / Gateway' },
  { prefix: 'provenance',  label: 'Provenance' },
  { prefix: 'cap-matrix',  label: 'Capability Matrix' },
];

interface RunGroup {
  label: string;
  runs:  RunSummary[];
}

function classifyRun(label: string): string {
  const lower = label.toLowerCase();
  for (const { prefix, label: groupLabel } of USE_CASE_PREFIXES) {
    if (lower.startsWith(prefix)) return groupLabel;
  }
  return 'Unclassified';
}

function groupRuns(runs: RunSummary[]): RunGroup[] {
  const map = new Map<string, RunSummary[]>();
  for (const run of runs) {
    const g = classifyRun(run.label);
    const arr = map.get(g) ?? [];
    arr.push(run);
    map.set(g, arr);
  }
  const ordered: RunGroup[] = [];
  for (const { label } of USE_CASE_PREFIXES) {
    const arr = map.get(label);
    if (arr?.length) ordered.push({ label, runs: arr });
  }
  const unclassified = map.get('Unclassified');
  if (unclassified?.length) ordered.push({ label: 'Unclassified', runs: unclassified });
  return ordered;
}

function visibleRuns(group: RunGroup, showAll: boolean): RunSummary[] {
  return showAll ? group.runs : group.runs.slice(0, DEFAULT_SHOW);
}

// ============================================================================
// RunRow
// ============================================================================

interface RunRowProps {
  run:      RunSummary;
  onSelect: (run: RunSummary) => void;
  now:      number;
}

function RunRow({ run, onSelect, now }: RunRowProps) {
  // Fall back to started_at when no events have been persisted yet (run crashed
  // before writing its first event — last_event_at is NULL in that case).
  const referenceAt = run.last_event_at ?? run.started_at;
  const stalled =
    run.status === 'running' &&
    now - new Date(referenceAt).getTime() > STALE_THRESHOLD_MS;
  const mins = stalled ? staleMinsAgo(referenceAt, now) : 0;

  return (
    <tr
      onClick={() => onSelect(run)}
      className="cursor-pointer border-b transition-colors hover:bg-muted/50"
    >
      <td className="px-4 py-2 max-w-[280px] truncate" title={run.label}>
        {run.label.length > 45 ? run.label.slice(0, 45) + '…' : run.label}
      </td>
      <td className="px-4 py-2">
        {stalled ? (
          <span
            className="inline-flex items-center gap-1.5"
            title={`No events for ${mins}m — process may have died`}
          >
            <Badge variant="warning">running</Badge>
            <span className="text-xs font-medium text-amber-600">stalled?</span>
          </span>
        ) : (
          <Badge variant={statusBadgeVariant(run.status)}>{run.status}</Badge>
        )}
      </td>
      <td className="px-4 py-2 text-muted-foreground">
        {run.model.split('/').pop() ?? run.model}
      </td>
      <td className="px-4 py-2 text-muted-foreground">
        {new Date(run.started_at).toLocaleString()}
      </td>
      <td className="px-4 py-2 text-muted-foreground">
        {formatDuration(run.started_at, run.finished_at)}
      </td>
      <td className="px-4 py-2 text-right tabular-nums">{run.step_count}</td>
      <td className="px-4 py-2 text-right tabular-nums">{run.event_count}</td>
      <td
        className="px-4 py-2 text-right tabular-nums text-muted-foreground"
        title={tokenTooltip(run)}
      >
        {run.total_cost_usd != null ? `$${run.total_cost_usd.toFixed(4)}` : '—'}
      </td>
    </tr>
  );
}

// ============================================================================
// Tab 1 — Runs
// ============================================================================

interface RunsContentProps {
  onSelectRun: (run: RunSummary) => void;
}

function RunsContent({ onSelectRun }: RunsContentProps) {
  const status  = useHarnessStatus();
  const runList = useRunList();
  const [statusFilter, setStatusFilter] = useState('all');
  const expanded = useSessionRecord('rig:runs:expanded', false);
  const showAll  = useSessionRecord('rig:runs:showAll', false);

  // Re-evaluate staleness every 60s without refetching data
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(id);
  }, []);

  if (status.data && !status.data.connected) return <NotConnected />;
  if (runList.loading) return <LoadingShell rows={6} />;
  if (runList.error?.includes('harness not connected')) return <NotConnected />;

  // Filter first, then group — empty groups are hidden after filter.
  const filtered = (runList.data ?? []).filter(
    (r) => statusFilter === 'all' || r.status === statusFilter,
  );
  const groups = groupRuns(filtered);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-2 border-b shrink-0">
        <select
          className={SELECT_CLASS}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Status filter"
        >
          <option value="all">All</option>
          <option value="running">Running</option>
          <option value="done">Done</option>
          <option value="failed">Failed</option>
          <option value="paused">Paused</option>
        </select>
        <div className="ml-2 flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              expanded.setAll(groups.map((g) => g.label), false);
              showAll.setAll(groups.map((g) => g.label), false);
            }}
          >
            Collapse all
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => expanded.setAll(groups.map((g) => g.label), true)}
          >
            Expand all
          </Button>
        </div>
        <div className="ml-auto">
          <Button variant="outline" size="sm" onClick={runList.refetch}>
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {groups.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">
            No runs found. Run an agent via{' '}
            <code className="rounded bg-muted px-1">mix aetheris run</code>.
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 border-b bg-background">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Label</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Model</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Started</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Duration</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Steps</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Events</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Cost</th>
              </tr>
            </thead>
            <tbody>
              {groups.map((group) => {
                const exp = expanded.get(group.label);
                const sa  = showAll.get(group.label);
                return (
                  <Fragment key={group.label}>
                    {/* Group header row */}
                    <tr
                      onClick={() => expanded.set(group.label, !exp)}
                      className="cursor-pointer select-none border-b bg-muted/50 transition-colors hover:bg-muted/80"
                    >
                      <td colSpan={8} className="px-4 py-2">
                        <div className="flex items-center gap-2">
                          {exp
                            ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                            : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                          <span className="text-sm font-medium">{group.label}</span>
                          <span className="ml-1 text-xs text-muted-foreground">
                            ({group.runs.length})
                          </span>
                        </div>
                      </td>
                    </tr>

                    {/* Run rows */}
                    {exp && visibleRuns(group, sa).map((run) => (
                      <RunRow key={run.run_id} run={run} onSelect={onSelectRun} now={now} />
                    ))}

                    {/* Show more / show less */}
                    {exp && group.runs.length > DEFAULT_SHOW && (
                      <tr className="border-b">
                        <td colSpan={8} className="px-4 py-2">
                          <button
                            className="text-xs text-muted-foreground transition-colors hover:text-foreground"
                            onClick={(e) => { e.stopPropagation(); showAll.set(group.label, !sa); }}
                          >
                            {sa
                              ? 'Show less'
                              : `Show ${group.runs.length - DEFAULT_SHOW} more…`}
                          </button>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Tab 2 — Events
// ============================================================================

interface EventsContentProps {
  selectedRun: RunSummary | null;
}

function EventsContent({ selectedRun }: EventsContentProps) {
  const status = useHarnessStatus();
  const events = useRunEvents(
    selectedRun?.run_id ?? null,
    { polling: selectedRun?.status === 'running' },
  );
  const { isPolling } = events;

  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new events if already near the bottom
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    if (nearBottom) el.scrollTop = el.scrollHeight;
  }, [events.data]);

  const isComplete = (events.data ?? []).some((ev) => ev.event_type === 'run_complete');
  const displayStatus = isComplete ? 'done' : (selectedRun?.status ?? '');

  if (status.data && !status.data.connected) return <NotConnected />;

  if (!selectedRun) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">
          Select a run from the Runs tab to view its events.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-3 border-b px-4 py-3 text-sm">
        <span className="font-medium truncate max-w-xs" title={selectedRun.label}>
          {selectedRun.label}
        </span>
        <Badge variant={statusBadgeVariant(displayStatus)}>{displayStatus}</Badge>
        <span className="text-muted-foreground">
          {selectedRun.model.split('/').pop() ?? selectedRun.model}
        </span>
        <span className="text-muted-foreground">
          Started: {new Date(selectedRun.started_at).toLocaleString()}
        </span>
        {isPolling && (
          <span className="flex items-center gap-1.5 text-xs text-green-600">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            Live
          </span>
        )}
      </div>

      {events.loading && !events.data ? (
        <LoadingShell rows={6} />
      ) : (events.data ?? []).length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">No events found for this run.</p>
        </div>
      ) : (
        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 border-b bg-background">
              <tr>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Seq</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Step</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Timestamp</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Payload preview</th>
              </tr>
            </thead>
            <tbody>
              {(events.data ?? []).map((ev) => (
                <tr key={ev.id} className="border-b hover:bg-muted/50">
                  <td className="px-4 py-2 text-right font-mono tabular-nums text-muted-foreground">
                    {ev.seq}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">
                    {ev.step}
                  </td>
                  <td className={`px-4 py-2 font-medium ${eventTypeClass(ev.event_type)}`}>
                    {ev.event_type}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                    {new Date(ev.timestamp).toISOString().slice(11, 23)}
                  </td>
                  <td
                    className="px-4 py-2 font-mono text-xs text-muted-foreground max-w-lg truncate"
                    title={payloadPreview(ev.payload)}
                  >
                    {payloadPreview(ev.payload)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// HarnessRoute — manages shared state; use this in App.tsx
// ============================================================================

export function HarnessRoute() {
  const [selectedRun, setSelectedRun] = useState<RunSummary | null>(null);
  const [activeTab, setActiveTab] = useState('runs');

  const handleSelectRun = useCallback((run: RunSummary) => {
    setSelectedRun(run);
    setActiveTab('events');
  }, []);

  // Surface a resolved fork (BL-007 t4): jump to the child run's trajectory so its
  // provenance banner is immediately visible. `fork_run` resolves only on a `done`
  // fork, and TrajectoryView reads all display data from the trajectory file's meta
  // (not this summary) — the synthesized summary's `status: 'done'` only gates polling
  // off. The Runs-list row appears on the next manual Refresh.
  const handleForked = useCallback((runId: string) => {
    setSelectedRun({
      run_id:         runId,
      label:          '',
      status:         'done',
      provider:       '',
      model:          '',
      started_at:     '',
      finished_at:    null,
      step_count:     0,
      event_count:    0,
      last_event_at:  null,
      total_cost_usd: null,
      // Placeholder, like the rest of this literal — the real totals arrive with
      // the row on the next manual Refresh. null (not 0) keeps the Cost cell and
      // its token tooltip honest in the meantime.
      total_input_tokens:  null,
      total_output_tokens: null,
    });
    setActiveTab('trajectory');
  }, []);

  const hasSelection = selectedRun !== null;

  return (
    <MainArea
      activeTab={activeTab}
      onTabChange={setActiveTab}
      tabs={[
        { id: 'runs',       label: 'Runs',       content: <RunsContent onSelectRun={handleSelectRun} /> },
        { id: 'events',     label: 'Events',     content: <EventsContent selectedRun={selectedRun} />, disabled: !hasSelection },
        { id: 'trajectory', label: 'Trajectory', content: <TrajectoryView run={selectedRun} onForked={handleForked} />, disabled: !hasSelection },
      ]}
    />
  );
}

// Tab factory — kept for spec compatibility
export function RunList(): Tab[] {
  return [
    { id: 'runs',   label: 'Runs',   content: <RunsContent onSelectRun={() => {}} /> },
    { id: 'events', label: 'Events', content: <EventsContent selectedRun={null} /> },
  ];
}
