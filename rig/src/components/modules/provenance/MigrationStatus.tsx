import { RefreshCw } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';
import { Button } from '@/components/ui/button';
import { MigrationSummary, MigrationClientRow, FailedMigration } from '@/hooks/types';
import { useMigrationSummary, useFailedMigrations } from '@/hooks/useMigration';
import { NotConnected, LoadingShell, ErrorState } from './shared';

// ============================================================================
// Helpers
// ============================================================================

function ProgressBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span>
          Migrated:{' '}
          <span className="font-medium">
            {value.toLocaleString()} / {max.toLocaleString()} files
          </span>
        </span>
        <span className="font-medium text-green-600">{pct}%</span>
      </div>
      <div className="w-full bg-muted rounded-full h-3">
        <div
          className="bg-green-500 h-3 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function InlineBar({ value, total }: { value: number; total: number }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-muted rounded-full h-1.5 shrink-0">
        <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-muted-foreground tabular-nums">{pct}%</span>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: number; accent?: string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={`text-xl font-semibold tabular-nums ${accent ?? ''}`}>
        {value.toLocaleString()}
      </p>
    </div>
  );
}

function ClientTable({ rows }: { rows: MigrationClientRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No migrations yet — run the migration agent to begin.
      </p>
    );
  }
  return (
    <table className="w-full text-sm">
      <thead className="border-b">
        <tr>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Client</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Migrated</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Pending</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Failed</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Progress</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => {
          const total = row.migrated + row.pending + row.failed;
          return (
            <tr key={row.client} className="border-b transition-colors hover:bg-muted/50">
              <td className="py-2 px-3 font-medium">{row.client}</td>
              <td className="py-2 px-3 tabular-nums text-green-600">{row.migrated.toLocaleString()}</td>
              <td className="py-2 px-3 tabular-nums text-yellow-600">{row.pending.toLocaleString()}</td>
              <td className="py-2 px-3 tabular-nums text-red-600">{row.failed.toLocaleString()}</td>
              <td className="py-2 px-3">
                <InlineBar value={row.migrated} total={total} />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

// ============================================================================
// Tab 1 — Migration overview
// ============================================================================

function MigrationOverviewContent() {
  const { data, loading, error, refetch } = useMigrationSummary();

  if (error === 'corpus not connected') return <NotConnected />;
  if (loading) return <LoadingShell rows={6} />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;

  const s: MigrationSummary = data ?? { total: 0, migrated: 0, failed: 0, pending: 0, by_client: [] };

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">Migration progress</h3>
        <Button variant="outline" size="sm" onClick={refetch}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      <ProgressBar value={s.migrated} max={s.total} />

      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Migrated" value={s.migrated} accent="text-green-600" />
        <StatCard label="Pending" value={s.pending} accent="text-yellow-600" />
        <StatCard label="Failed" value={s.failed} accent="text-red-600" />
        <StatCard label="Total" value={s.total} />
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium">Per-client breakdown</h3>
        <div className="rounded-lg border overflow-hidden">
          <ClientTable rows={s.by_client} />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Tab 2 — Failed migrations
// ============================================================================

function FailedMigrationsContent() {
  const { data, loading, error, refetch } = useFailedMigrations();

  if (error === 'corpus not connected') return <NotConnected />;
  if (loading) return <LoadingShell />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;

  const rows: FailedMigration[] = data ?? [];

  return (
    <div className="flex h-full flex-col">
      <div className="flex justify-end p-4 pb-2">
        <Button variant="outline" size="sm" onClick={refetch}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">No failed migrations.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 border-b bg-background">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Source path</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Destination</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Error</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Attempted at</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.path} className="border-b transition-colors hover:bg-muted/50">
                  <td className="px-4 py-2 font-mono text-xs" title={row.path}>
                    {row.path.length > 45 ? '…' + row.path.slice(-43) : row.path}
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground" title={row.dest_path}>
                    {row.dest_path.length > 45 ? '…' + row.dest_path.slice(-43) : row.dest_path}
                  </td>
                  <td className="px-4 py-2 text-destructive text-xs max-w-xs" title={row.error ?? ''}>
                    {row.error ?? '—'}
                  </td>
                  <td className="px-4 py-2 text-muted-foreground tabular-nums">
                    {row.proposed_at}
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
// Tab factory
// ============================================================================

export function MigrationStatus(): Tab[] {
  return [
    {
      id: 'migration-overview',
      label: 'Migration',
      content: <MigrationOverviewContent />,
    },
    {
      id: 'migration-failed',
      label: 'Failed',
      content: <FailedMigrationsContent />,
    },
  ];
}
