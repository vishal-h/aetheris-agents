import { TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUsageStats } from '@/hooks/useUsageStats';
import type { ModelUsageRow, UseCaseUsageRow } from '@/hooks/types';

// ── Formatting helpers ────────────────────────────────────────────────────────

function formatCost(usd: number): string {
  if (usd >= 1) return `$${usd.toFixed(2)}`;
  return `$${usd.toFixed(4)}`;
}

function formatTokens(n: number): string {
  return n.toLocaleString();
}

// ── Summary card ──────────────────────────────────────────────────────────────

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-4 flex flex-col gap-1">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-xl font-semibold tabular-nums">{value}</p>
    </div>
  );
}

// ── Main view ─────────────────────────────────────────────────────────────────

export function UsageView() {
  const { stats, loading, error, refresh } = useUsageStats();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Loading usage stats…
      </div>
    );
  }

  if (error) {
    return <div className="p-6 text-sm text-red-600">{error}</div>;
  }

  if (!stats) return null;

  const avgCost = stats.instrumented_runs > 0
    ? stats.total_cost_usd / stats.instrumented_runs
    : 0;

  return (
    <div className="flex flex-col h-full overflow-hidden">

      {/* Header */}
      <div className="px-6 py-4 border-b shrink-0 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-base font-semibold">Usage</h2>
        </div>
        <Button variant="outline" size="sm" onClick={refresh}>
          Refresh
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">

        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard label="Total spend"   value={formatCost(stats.total_cost_usd)} />
          <StatCard label="Total runs"    value={stats.total_runs.toLocaleString()} />
          <StatCard
            label="Total tokens"
            value={formatTokens(stats.total_input_tokens + stats.total_output_tokens)}
          />
          <StatCard label="Avg cost / run" value={formatCost(avgCost)} />
        </div>

        {/* Pre-instrumentation note */}
        {stats.instrumented_runs < stats.total_runs && (
          <p className="text-xs text-muted-foreground">
            Cost data available for {stats.instrumented_runs.toLocaleString()} of{' '}
            {stats.total_runs.toLocaleString()} runs. Earlier runs were not instrumented.
          </p>
        )}

        {/* By model */}
        {stats.by_model.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-2">By model</h3>
            <div className="rounded-md border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left px-3 py-2 font-medium">Model</th>
                    <th className="text-right px-3 py-2 font-medium">Runs</th>
                    <th className="text-right px-3 py-2 font-medium">Input</th>
                    <th className="text-right px-3 py-2 font-medium">Output</th>
                    <th className="text-right px-3 py-2 font-medium">Total cost</th>
                    <th className="text-right px-3 py-2 font-medium">Avg / run</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.by_model.map((row: ModelUsageRow) => (
                    <tr key={row.model} className="border-b last:border-b-0 hover:bg-muted/30">
                      <td className="px-3 py-2 font-mono text-xs">{row.model}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {row.run_count.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-xs">
                        {formatTokens(row.input_tokens)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-xs">
                        {formatTokens(row.output_tokens)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums font-medium">
                        {formatCost(row.total_cost_usd)}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums text-muted-foreground text-xs">
                        {formatCost(row.avg_cost_usd)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* By use case */}
        {stats.by_use_case.length > 0 && (
          <section>
            <h3 className="text-sm font-semibold mb-2">By use case</h3>
            <div className="rounded-md border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left px-3 py-2 font-medium">Use case</th>
                    <th className="text-right px-3 py-2 font-medium">Runs</th>
                    <th className="text-right px-3 py-2 font-medium">Total cost</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.by_use_case.map((row: UseCaseUsageRow) => (
                    <tr key={row.use_case} className="border-b last:border-b-0 hover:bg-muted/30">
                      <td className="px-3 py-2">{row.use_case}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {row.run_count.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums font-medium">
                        {formatCost(row.total_cost_usd)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Empty state */}
        {stats.instrumented_runs === 0 && (
          <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
            No instrumented runs yet. Run an agent to start tracking usage.
          </div>
        )}

      </div>
    </div>
  );
}
