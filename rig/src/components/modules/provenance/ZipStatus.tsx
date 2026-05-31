import { RefreshCw, Lock } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatBytes } from '@/lib/utils';
import { ZipInventory, ZipRow, EncryptedZipRow } from '@/hooks/types';
import { useZipInventory, useEncryptedZips } from '@/hooks/useZipInventory';
import { NotConnected, LoadingShell, ErrorState } from './shared';

// ============================================================================
// Helpers
// ============================================================================

function zipStatusVariant(status: string): 'success' | 'warning' | 'destructive' | 'default' {
  if (status === 'processed') return 'success';
  if (status === 'encrypted') return 'warning';
  if (status === 'failed') return 'destructive';
  return 'default'; // pending, extracted
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-xl font-semibold tabular-nums">{value.toLocaleString()}</p>
    </div>
  );
}

// ============================================================================
// Tab 1 — Zip inventory
// ============================================================================

function LargestZipsTable({ rows }: { rows: ZipRow[] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground py-4">No zips found in corpus.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="border-b">
        <tr>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Path</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Size</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Status</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">Contents</th>
          <th className="py-2 px-3 text-left font-medium text-muted-foreground">New finds</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.path} className="border-b transition-colors hover:bg-muted/50">
            <td className="py-2 px-3 font-mono text-xs" title={row.path}>
              {row.path.length > 50 ? '…' + row.path.slice(-48) : row.path}
            </td>
            <td className="py-2 px-3 tabular-nums">{formatBytes(row.size_bytes)}</td>
            <td className="py-2 px-3">
              <Badge variant={zipStatusVariant(row.status)}>{row.status}</Badge>
            </td>
            <td className="py-2 px-3 tabular-nums text-muted-foreground">
              {row.contents_count?.toLocaleString() ?? '—'}
            </td>
            <td className="py-2 px-3 tabular-nums text-muted-foreground">
              {row.new_to_corpus?.toLocaleString() ?? '—'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ZipInventoryContent() {
  const { data, loading, error, refetch } = useZipInventory();

  if (error === 'corpus not connected') return <NotConnected />;
  if (loading) return <LoadingShell rows={6} />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;

  const inv: ZipInventory = data ?? {
    total: 0, processed: 0, encrypted: 0, pending: 0, failed: 0,
    new_to_corpus: 0, largest_zips: [],
  };

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">Zip archive inventory</h3>
        <Button variant="outline" size="sm" onClick={refetch}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-5 gap-3">
        <StatCard label="Total zips" value={inv.total} />
        <StatCard label="Processed" value={inv.processed} />
        <StatCard label="Encrypted" value={inv.encrypted} />
        <StatCard label="Pending" value={inv.pending} />
        <StatCard label="Failed" value={inv.failed} />
      </div>

      <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm">
        New-to-corpus files found:{' '}
        <span className="font-semibold">{inv.new_to_corpus.toLocaleString()}</span>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-medium">Largest zips (top 10)</h3>
        <div className="rounded-lg border overflow-hidden">
          <LargestZipsTable rows={inv.largest_zips} />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Tab 2 — Encrypted backlog
// ============================================================================

function EncryptedBacklogContent() {
  const { data, loading, error, refetch } = useEncryptedZips();

  if (error === 'corpus not connected') return <NotConnected />;
  if (loading) return <LoadingShell />;
  if (error) return <ErrorState message={error} onRetry={refetch} />;

  const rows: EncryptedZipRow[] = data ?? [];

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between p-4 pb-2">
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
          <Lock className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            These zips require a password to extract. Provide passwords to your
            Aetheris operator and re-run the zip orchestrator.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={refetch} className="ml-4 shrink-0">
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {rows.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">No encrypted zips pending.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 border-b bg-background">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Path</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Size</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Parent zip</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Depth</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.path} className="border-b transition-colors hover:bg-muted/50">
                  <td className="px-4 py-2 font-mono text-xs" title={row.path}>
                    {row.path.length > 55 ? '…' + row.path.slice(-53) : row.path}
                  </td>
                  <td className="px-4 py-2 tabular-nums">{formatBytes(row.size_bytes)}</td>
                  <td className="px-4 py-2 font-mono text-xs text-muted-foreground" title={row.parent_zip ?? ''}>
                    {row.parent_zip
                      ? row.parent_zip.length > 40 ? '…' + row.parent_zip.slice(-38) : row.parent_zip
                      : '—'}
                  </td>
                  <td className="px-4 py-2 tabular-nums">{row.depth}</td>
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

export function ZipStatus(): Tab[] {
  return [
    {
      id: 'zip-inventory',
      label: 'Zip inventory',
      content: <ZipInventoryContent />,
    },
    {
      id: 'zip-encrypted',
      label: 'Encrypted',
      content: <EncryptedBacklogContent />,
    },
  ];
}
