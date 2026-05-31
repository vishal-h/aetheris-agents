import { useState, useCallback, useMemo } from 'react';
import { RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { Tab } from '@/components/shell/TabBar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ClassificationRow } from '@/hooks/types';
import { useClassifications, useSetClassificationStatus } from '@/hooks/useClassifications';
import { useClientBreakdown } from '@/hooks/useCorpusOverview';
import { NotConnected, LoadingShell, ErrorState } from './shared';

// ============================================================================
// Helpers
// ============================================================================

function confidenceClass(c: number): string {
  if (c >= 0.85) return 'text-green-600';
  if (c >= 0.70) return 'text-yellow-600';
  return 'text-red-600';
}

function truncatePath(path: string, maxLen = 50): string {
  if (path.length <= maxLen) return path;
  return '…' + path.slice(-(maxLen - 1));
}

// ============================================================================
// Filter bar
// ============================================================================

interface PendingFilters {
  client: string;
  statusFilter: 'all' | 'proposed' | 'needs_review';
  confidenceMin: number;
}

function PendingFilterBar({
  filters,
  clients,
  onChange,
  onRefresh,
}: {
  filters: PendingFilters;
  clients: string[];
  onChange: (f: PendingFilters) => void;
  onRefresh: () => void;
}) {
  const selectClass =
    'h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring';

  return (
    <div className="flex flex-wrap items-center gap-3 border-b px-4 py-3">
      <select
        className={selectClass}
        value={filters.client}
        onChange={(e) => onChange({ ...filters, client: e.target.value })}
        aria-label="Filter by client"
      >
        <option value="">All clients</option>
        {clients.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>

      <select
        className={selectClass}
        value={filters.statusFilter}
        onChange={(e) =>
          onChange({ ...filters, statusFilter: e.target.value as PendingFilters['statusFilter'] })
        }
        aria-label="Status filter"
      >
        <option value="all">All pending</option>
        <option value="proposed">Proposed</option>
        <option value="needs_review">Needs review</option>
      </select>

      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        Confidence ≥
        <span className="w-8 tabular-nums text-foreground">{filters.confidenceMin.toFixed(2)}</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={filters.confidenceMin}
          onChange={(e) => onChange({ ...filters, confidenceMin: parseFloat(e.target.value) })}
          className="w-28 accent-blue-500"
          aria-label="Minimum confidence"
        />
      </label>

      <Button variant="outline" size="sm" onClick={onRefresh} className="ml-auto">
        <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
        Refresh
      </Button>
    </div>
  );
}

// ============================================================================
// Bulk action bar
// ============================================================================

function BulkActionBar({
  count,
  onApprove,
  onReject,
  disabled,
}: {
  count: number;
  onApprove: () => void;
  onReject: () => void;
  disabled: boolean;
}) {
  if (count === 0) return null;
  return (
    <div className="flex items-center gap-3 border-b bg-accent/30 px-4 py-2 text-sm">
      <span className="text-muted-foreground">{count} selected</span>
      <Button
        size="sm"
        variant="outline"
        className="border-green-600 text-green-700 hover:bg-green-50"
        onClick={onApprove}
        disabled={disabled}
      >
        <CheckCircle className="mr-1.5 h-3.5 w-3.5" />
        Approve {count}
      </Button>
      <Button
        size="sm"
        variant="outline"
        className="border-red-500 text-red-600 hover:bg-red-50"
        onClick={onReject}
        disabled={disabled}
      >
        <XCircle className="mr-1.5 h-3.5 w-3.5" />
        Reject {count}
      </Button>
    </div>
  );
}

// ============================================================================
// Tab 1 — Pending review
// ============================================================================

function PendingContent() {
  const allRows = useClassifications({ limit: 500 });
  const clientData = useClientBreakdown();
  const setStatus = useSetClassificationStatus();

  const [rows, setRows] = useState<ClassificationRow[] | null>(null);
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({});
  const [inFlight, setInFlight] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkBusy, setBulkBusy] = useState(false);
  const [filters, setFilters] = useState<PendingFilters>({
    client: '',
    statusFilter: 'all',
    confidenceMin: 0,
  });

  // Sync local rows from hook when hook data arrives (or on refetch)
  const hookData = allRows.data;
  const pendingFromHook = useMemo(
    () => hookData.filter((r) => r.status === 'proposed' || r.status === 'needs_review'),
    [hookData],
  );

  // Use local rows for optimistic updates; reset when hook data changes
  const baseRows = rows ?? pendingFromHook;

  const filtered = useMemo(() => {
    return baseRows
      .filter((r) => {
        if (filters.client && r.client !== filters.client) return false;
        if (filters.statusFilter !== 'all' && r.status !== filters.statusFilter) return false;
        if (r.confidence < filters.confidenceMin) return false;
        return true;
      })
      .sort((a, b) => a.confidence - b.confidence);
  }, [baseRows, filters]);

  const clients = useMemo(
    () => (clientData.data ?? []).map((c) => c.client),
    [clientData.data],
  );

  const handleRefetch = useCallback(() => {
    setRows(null);
    setRowErrors({});
    setSelected(new Set());
    allRows.refetch();
  }, [allRows]);

  const handleAction = useCallback(
    async (path: string, status: 'approved' | 'rejected') => {
      setInFlight((prev) => new Set(prev).add(path));
      setRowErrors((prev) => { const next = { ...prev }; delete next[path]; return next; });

      // Optimistic remove
      const snapshot = baseRows;
      setRows((prev) => (prev ?? pendingFromHook).filter((r) => r.path !== path));
      setSelected((prev) => { const next = new Set(prev); next.delete(path); return next; });

      try {
        await setStatus(path, status);
      } catch (e) {
        // Restore
        setRows(snapshot);
        setRowErrors((prev) => ({ ...prev, [path]: String(e) }));
      } finally {
        setInFlight((prev) => { const next = new Set(prev); next.delete(path); return next; });
      }
    },
    [baseRows, pendingFromHook, setStatus],
  );

  const handleBulk = useCallback(
    async (status: 'approved' | 'rejected') => {
      setBulkBusy(true);
      const paths = [...selected];
      for (const path of paths) {
        await handleAction(path, status);
      }
      setSelected(new Set());
      setBulkBusy(false);
    },
    [selected, handleAction],
  );

  const toggleSelect = (path: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path); else next.add(path);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === filtered.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(filtered.map((r) => r.path)));
    }
  };

  const notConnected =
    allRows.error === 'corpus not connected' ||
    clientData.error === 'corpus not connected';

  if (notConnected) return <NotConnected />;
  if (allRows.loading && !rows) return <LoadingShell rows={8} />;
  if (allRows.error && !rows) return <ErrorState message={allRows.error} onRetry={handleRefetch} />;

  return (
    <div className="flex h-full flex-col">
      <PendingFilterBar
        filters={filters}
        clients={clients}
        onChange={setFilters}
        onRefresh={handleRefetch}
      />

      <BulkActionBar
        count={selected.size}
        onApprove={() => handleBulk('approved')}
        onReject={() => handleBulk('rejected')}
        disabled={bulkBusy}
      />

      {filtered.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">
            No pending classifications.
          </p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 border-b bg-background">
              <tr>
                <th className="px-3 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selected.size === filtered.length && filtered.length > 0}
                    onChange={toggleSelectAll}
                    aria-label="Select all"
                    className="accent-blue-500"
                  />
                </th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">Path</th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">Client</th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">FY</th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">Type</th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">Confidence</th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">Preview</th>
                <th className="px-3 py-3 text-left font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => {
                const busy = inFlight.has(row.path);
                const err = rowErrors[row.path];
                return (
                  <tr key={row.path} className="border-b transition-colors hover:bg-muted/50">
                    <td className="px-3 py-2">
                      <input
                        type="checkbox"
                        checked={selected.has(row.path)}
                        onChange={() => toggleSelect(row.path)}
                        disabled={busy}
                        className="accent-blue-500"
                      />
                    </td>
                    <td className="px-3 py-2 font-mono text-xs" title={row.path}>
                      {truncatePath(row.path)}
                      {err && <div className="text-destructive text-xs mt-0.5">{err}</div>}
                    </td>
                    <td className="px-3 py-2">{row.client}</td>
                    <td className="px-3 py-2">{row.financial_year}</td>
                    <td className="px-3 py-2">{row.doc_type}</td>
                    <td className={`px-3 py-2 tabular-nums font-medium ${confidenceClass(row.confidence)}`}>
                      {row.confidence.toFixed(2)}
                    </td>
                    <td
                      className="px-3 py-2 text-muted-foreground max-w-xs truncate"
                      title={row.raw_excerpt}
                    >
                      {row.raw_excerpt.length > 100
                        ? row.raw_excerpt.slice(0, 100) + '…'
                        : row.raw_excerpt}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-1.5">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-green-600 text-green-700 hover:bg-green-50"
                          onClick={() => handleAction(row.path, 'approved')}
                          disabled={busy || bulkBusy}
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-red-500 text-red-600 hover:bg-red-50"
                          onClick={() => handleAction(row.path, 'rejected')}
                          disabled={busy || bulkBusy}
                        >
                          Reject
                        </Button>
                      </div>
                    </td>
                  </tr>
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
// Tab 2 — Review history
// ============================================================================

function HistoryContent() {
  const allRows = useClassifications({ limit: 500 });
  const clientData = useClientBreakdown();

  const [clientFilter, setClientFilter] = useState('');
  const [decisionFilter, setDecisionFilter] = useState<'all' | 'approved' | 'rejected'>('all');

  const clients = useMemo(
    () => (clientData.data ?? []).map((c) => c.client),
    [clientData.data],
  );

  const history = useMemo(() => {
    return (allRows.data ?? []).filter((r) => {
      if (r.status !== 'approved' && r.status !== 'rejected') return false;
      if (clientFilter && r.client !== clientFilter) return false;
      if (decisionFilter !== 'all' && r.status !== decisionFilter) return false;
      return true;
    });
  }, [allRows.data, clientFilter, decisionFilter]);

  const notConnected = allRows.error === 'corpus not connected';
  if (notConnected) return <NotConnected />;
  if (allRows.loading) return <LoadingShell />;
  if (allRows.error) return <ErrorState message={allRows.error} onRetry={allRows.refetch} />;

  const selectClass =
    'h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring';

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-wrap items-center gap-3 border-b px-4 py-3">
        <select
          className={selectClass}
          value={clientFilter}
          onChange={(e) => setClientFilter(e.target.value)}
          aria-label="Filter by client"
        >
          <option value="">All clients</option>
          {clients.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        <select
          className={selectClass}
          value={decisionFilter}
          onChange={(e) => setDecisionFilter(e.target.value as typeof decisionFilter)}
          aria-label="Filter by decision"
        >
          <option value="all">All decisions</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>

        <Button variant="outline" size="sm" onClick={allRows.refetch} className="ml-auto">
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {history.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">No reviewed classifications yet.</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 border-b bg-background">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Path</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Client</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">FY</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Decision</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Reviewed by</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Reviewed at</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.path} className="border-b transition-colors hover:bg-muted/50">
                  <td className="px-4 py-2 font-mono text-xs" title={row.path}>
                    {truncatePath(row.path)}
                  </td>
                  <td className="px-4 py-2">{row.client}</td>
                  <td className="px-4 py-2">{row.financial_year}</td>
                  <td className="px-4 py-2">{row.doc_type}</td>
                  <td className="px-4 py-2">
                    <Badge variant={row.status === 'approved' ? 'success' : 'destructive'}>
                      {row.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{row.reviewed_by ?? '—'}</td>
                  <td className="px-4 py-2 text-muted-foreground">{row.classified_at}</td>
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

export function ClassificationReview(): Tab[] {
  return [
    {
      id: 'pending',
      label: 'Pending review',
      content: <PendingContent />,
    },
    {
      id: 'history',
      label: 'Review history',
      content: <HistoryContent />,
    },
  ];
}
