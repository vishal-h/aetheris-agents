import { useState, useCallback, useEffect, useRef } from 'react';
import { RefreshCw } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';
import { MainArea } from '@/components/shell/MainArea';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RunSummary } from '@/hooks/types';
import { useHarnessStatus, useRunList, useRunEvents } from '@/hooks';
import { NotConnected, LoadingShell } from './shared';

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

function payloadPreview(payload: string): string {
  return payload.replace(/\s+/g, ' ').trim().slice(0, 120);
}

const SELECT_CLASS =
  'h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring';

// ============================================================================
// Tab 1 — Runs
// ============================================================================

interface RunsContentProps {
  onSelectRun: (run: RunSummary) => void;
}

function RunsContent({ onSelectRun }: RunsContentProps) {
  const status = useHarnessStatus();
  const runList = useRunList();
  const [statusFilter, setStatusFilter] = useState('all');

  if (status.data && !status.data.connected) return <NotConnected />;
  if (runList.loading) return <LoadingShell rows={6} />;
  if (runList.error?.includes('harness not connected')) return <NotConnected />;

  const rows = (runList.data ?? []).filter(
    (r) => statusFilter === 'all' || r.status === statusFilter,
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b px-4 py-3">
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
        <Button variant="outline" size="sm" onClick={runList.refetch} className="ml-auto">
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {rows.length === 0 ? (
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
              </tr>
            </thead>
            <tbody>
              {rows.map((run) => (
                <tr
                  key={run.run_id}
                  onClick={() => onSelectRun(run)}
                  className="cursor-pointer border-b transition-colors hover:bg-muted/50"
                >
                  <td className="px-4 py-2 max-w-[280px] truncate" title={run.label}>
                    {run.label.length > 45 ? run.label.slice(0, 45) + '…' : run.label}
                  </td>
                  <td className="px-4 py-2">
                    <Badge variant={statusBadgeVariant(run.status)}>{run.status}</Badge>
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

  return (
    <MainArea
      activeTab={activeTab}
      onTabChange={setActiveTab}
      tabs={[
        { id: 'runs',   label: 'Runs',   content: <RunsContent onSelectRun={handleSelectRun} /> },
        { id: 'events', label: 'Events', content: <EventsContent selectedRun={selectedRun} /> },
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
