import { RefreshCw } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatBytes } from '@/lib/utils';
import {
  useCorpusSummary,
  useClientBreakdown,
  useScanRuns,
  useDuplicateGroups,
} from '@/hooks/useCorpusOverview';
import { CorpusSummary, ClientRow, ScanRun, CorpusDuplicateGroup } from '@/hooks/types';
import { NotConnected, LoadingShell, ErrorState } from './shared';

function formatDuration(secs: number | null): string {
  if (secs === null) return '—';
  if (secs < 60) return `${secs}s`;
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}m ${s}s`;
}

function scanStatusVariant(status: string): 'success' | 'warning' | 'destructive' | 'default' {
  if (status === 'complete') return 'success';
  if (status === 'running') return 'warning';
  if (status === 'failed') return 'destructive';
  return 'default';
}

// ============================================================================
// Tab 1 — Summary
// ============================================================================

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function SummaryCards({ s }: { s: CorpusSummary }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      <StatCard label="Total files" value={s.total_files.toLocaleString()} />
      <StatCard label="Unique files" value={s.unique_files.toLocaleString()} />
      <StatCard label="Duplicates" value={s.duplicate_files.toLocaleString()} />
      <StatCard label="Wasted space" value={formatBytes(s.wasted_bytes)} />
      <StatCard label="Classified" value={s.classified_files.toLocaleString()} />
      <StatCard label="Migrated" value={s.migrated_files.toLocaleString()} />
    </div>
  );
}

function ClientTable({ rows }: { rows: ClientRow[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground py-4">No clients found.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="border-b">
        <tr>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Client</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Files</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Size</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Migrated</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Doc types</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.client} className="border-b transition-colors hover:bg-muted/50">
            <td className="py-2 px-3 font-medium">{row.client}</td>
            <td className="py-2 px-3 tabular-nums">{row.file_count.toLocaleString()}</td>
            <td className="py-2 px-3 tabular-nums">{formatBytes(row.total_size_bytes)}</td>
            <td className="py-2 px-3 tabular-nums">{row.migrated_count.toLocaleString()}</td>
            <td className="py-2 px-3 text-muted-foreground">{row.doc_types.join(', ') || '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SummaryContent() {
  const summary = useCorpusSummary();
  const breakdown = useClientBreakdown();

  const loading = summary.loading || breakdown.loading;
  const notConnected =
    summary.error === 'corpus not connected' ||
    breakdown.error === 'corpus not connected';

  if (notConnected) return <NotConnected />;
  if (loading) return <LoadingShell rows={8} />;
  if (summary.error) return <ErrorState message={summary.error} onRetry={summary.refetch} />;
  if (breakdown.error) return <ErrorState message={breakdown.error} onRetry={breakdown.refetch} />;
  if (!summary.data) return null;

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-muted-foreground">
          {summary.data.last_scan_at ? `Last scan: ${summary.data.last_scan_at}` : 'No scans recorded'}
        </h2>
        <Button variant="outline" size="sm" onClick={() => { summary.refetch(); breakdown.refetch(); }}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      <SummaryCards s={summary.data} />

      <div>
        <h3 className="mb-3 text-sm font-medium">Per-client breakdown</h3>
        <div className="rounded-lg border overflow-hidden">
          <ClientTable rows={breakdown.data ?? []} />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Tab 2 — Scan History
// ============================================================================

function ScanHistoryContent() {
  const { data, loading, error, refetch } = useScanRuns();

  if (error === 'corpus not connected') return <NotConnected />;
  if (loading) return <LoadingShell />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;

  const runs: ScanRun[] = data ?? [];

  if (runs.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">No scans yet. Run the scan orchestrator.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto">
      <div className="flex justify-end p-4 pb-2">
        <Button variant="outline" size="sm" onClick={refetch}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 border-b bg-background">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Run ID</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Root path</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Files</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Duplicates</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Started</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Duration</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id} className="border-b transition-colors hover:bg-muted/50">
                <td className="px-4 py-3 font-mono text-xs" title={run.id}>
                  {run.id.substring(0, 8)}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground" title={run.root_path}>
                  {run.root_path.length > 40 ? '…' + run.root_path.slice(-38) : run.root_path}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={scanStatusVariant(run.status)}>{run.status}</Badge>
                </td>
                <td className="px-4 py-3 tabular-nums">{run.files_scanned.toLocaleString()}</td>
                <td className="px-4 py-3 tabular-nums">{run.duplicates_found.toLocaleString()}</td>
                <td className="px-4 py-3 text-muted-foreground">{run.started_at}</td>
                <td className="px-4 py-3 tabular-nums">{formatDuration(run.duration_secs)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// Tab 3 — Storage Breakdown
// ============================================================================

function StorageBar({ summary }: { summary: CorpusSummary }) {
  const total = summary.total_size_bytes;
  if (total === 0) {
    return <div className="h-8 rounded bg-muted text-xs flex items-center justify-center text-muted-foreground">No data</div>;
  }

  const uniquePct = Math.round((summary.unique_size_bytes / total) * 100);
  const wastedPct = Math.round((summary.wasted_bytes / total) * 100);
  // remainder: files with null sha256 or size drift; absorb into unique segment
  const uniqueActual = 100 - wastedPct;

  return (
    <div className="space-y-2">
      <div className="flex h-8 w-full overflow-hidden rounded-md text-xs font-medium">
        <div
          className="flex items-center justify-center bg-blue-500 text-white transition-all"
          style={{ width: `${uniqueActual}%` }}
          title={`Unique content: ${formatBytes(summary.unique_size_bytes)}`}
        >
          {uniqueActual > 10 ? 'Unique' : ''}
        </div>
        {wastedPct > 0 && (
          <div
            className="flex items-center justify-center bg-amber-400 text-amber-900 transition-all"
            style={{ width: `${wastedPct}%` }}
            title={`Wasted (duplicates): ${formatBytes(summary.wasted_bytes)}`}
          >
            {wastedPct > 8 ? 'Wasted' : ''}
          </div>
        )}
      </div>
      <div className="flex gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />
          Unique {formatBytes(summary.unique_size_bytes)} ({uniquePct}%)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
          Wasted {formatBytes(summary.wasted_bytes)} ({wastedPct}%)
        </span>
      </div>
    </div>
  );
}

function DuplicateGroupsTable({ groups }: { groups: CorpusDuplicateGroup[] }) {
  if (groups.length === 0) {
    return <p className="text-sm text-muted-foreground py-4">No duplicate groups found.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="border-b">
        <tr>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">SHA-256</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Copies</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Size each</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Wasted</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((g) => (
          <tr key={g.sha256} className="border-b transition-colors hover:bg-muted/50">
            <td className="py-2 px-3 font-mono text-xs text-muted-foreground" title={g.sha256}>
              {g.sha256.substring(0, 12)}
            </td>
            <td className="py-2 px-3 tabular-nums">{g.copy_count}</td>
            <td className="py-2 px-3 tabular-nums">{formatBytes(g.size_each)}</td>
            <td className="py-2 px-3 tabular-nums text-amber-600">{formatBytes(g.wasted_bytes)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function StorageContent() {
  const summary = useCorpusSummary();
  const dupes = useDuplicateGroups();

  const loading = summary.loading || dupes.loading;
  const notConnected =
    summary.error === 'corpus not connected' ||
    dupes.error === 'corpus not connected';

  if (notConnected) return <NotConnected />;
  if (loading) return <LoadingShell rows={6} />;
  if (summary.error) return <ErrorState message={summary.error} onRetry={summary.refetch} />;
  if (dupes.error) return <ErrorState message={dupes.error} onRetry={dupes.refetch} />;
  if (!summary.data) return null;

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Storage distribution</h3>
        <Button variant="outline" size="sm" onClick={() => { summary.refetch(); dupes.refetch(); }}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      <StorageBar summary={summary.data} />

      <div>
        <h3 className="mb-3 text-sm font-medium">Top duplicate groups</h3>
        <div className="rounded-lg border overflow-hidden">
          <DuplicateGroupsTable groups={dupes.data ?? []} />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Tab factory
// ============================================================================

export function CorpusOverview(): Tab[] {
  return [
    {
      id: 'summary',
      label: 'Summary',
      content: <SummaryContent />,
    },
    {
      id: 'scan-history',
      label: 'Scan history',
      content: <ScanHistoryContent />,
    },
    {
      id: 'storage',
      label: 'Storage',
      content: <StorageContent />,
    },
  ];
}
