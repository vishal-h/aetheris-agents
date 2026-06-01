# rig/p6: Usage view

## Context

A new "Usage" section under the Harness sidebar entry. Shows aggregate token
and cost statistics across all instrumented runs: four summary cards at the
top, then cost broken down by model and by use case. All data comes from
`aetheris.db` via two new SQLite queries using `json_extract`.

All work is in `aetheris-agents/rig/`.

---

## What to build

### New Tauri command: `usage_stats_load`

Add `src-tauri/src/commands/usage.rs`. Uses the existing `HarnessState`
connection.

```rust
use crate::HarnessState;
use tauri::State;

#[derive(serde::Serialize)]
pub struct ModelUsageRow {
    pub model:          String,
    pub run_count:      i64,
    pub input_tokens:   i64,
    pub output_tokens:  i64,
    pub total_cost_usd: f64,
    pub avg_cost_usd:   f64,
}

#[derive(serde::Serialize)]
pub struct UseCaseUsageRow {
    pub use_case:       String,
    pub run_count:      i64,
    pub total_cost_usd: f64,
}

#[derive(serde::Serialize)]
pub struct UsageStats {
    pub total_cost_usd:     f64,
    pub total_runs:         i64,
    pub instrumented_runs:  i64,
    pub total_input_tokens: i64,
    pub total_output_tokens:i64,
    pub by_model:           Vec<ModelUsageRow>,
    pub by_use_case:        Vec<UseCaseUsageRow>,
}

#[tauri::command]
pub fn usage_stats_load(
    state: State<'_, HarnessState>,
) -> Result<UsageStats, String> {
    let conn = get_harness_conn(&state)?;

    // ── Summary row ──────────────────────────────────────────────────────────
    let summary_sql = "
        SELECT
            COALESCE(SUM(json_extract(payload_json, '$.cost_usd')), 0.0)     AS total_cost,
            COALESCE(SUM(json_extract(payload_json, '$.input_tokens')), 0)   AS total_in,
            COALESCE(SUM(json_extract(payload_json, '$.output_tokens')), 0)  AS total_out,
            COUNT(DISTINCT run_id)                                            AS instrumented_runs
        FROM events
        WHERE type = 'llm_responded'
          AND json_extract(payload_json, '$.cost_usd') IS NOT NULL
    ";

    let (total_cost, total_in, total_out, instrumented_runs) = conn
        .query_row(summary_sql, [], |r| {
            Ok((r.get::<_, f64>(0)?, r.get::<_, i64>(1)?,
                r.get::<_, i64>(2)?, r.get::<_, i64>(3)?))
        })
        .map_err(|e| format!("summary query failed: {}", e))?;

    let total_runs: i64 = conn
        .query_row("SELECT COUNT(*) FROM runs", [], |r| r.get(0))
        .map_err(|e| format!("run count failed: {}", e))?;

    // ── By model ─────────────────────────────────────────────────────────────
    let model_sql = "
        SELECT
            json_extract(payload_json, '$.resolved_model')              AS model,
            COUNT(DISTINCT run_id)                                       AS run_count,
            COALESCE(SUM(json_extract(payload_json, '$.input_tokens')), 0)  AS input_tokens,
            COALESCE(SUM(json_extract(payload_json, '$.output_tokens')), 0) AS output_tokens,
            COALESCE(SUM(json_extract(payload_json, '$.cost_usd')), 0.0)    AS total_cost,
            COALESCE(AVG(json_extract(payload_json, '$.cost_usd')), 0.0)    AS avg_cost
        FROM events
        WHERE type = 'llm_responded'
          AND json_extract(payload_json, '$.cost_usd') IS NOT NULL
        GROUP BY model
        ORDER BY total_cost DESC
    ";

    let mut stmt = conn.prepare(model_sql)
        .map_err(|e| format!("model query failed: {}", e))?;

    let by_model: Vec<ModelUsageRow> = stmt
        .query_map([], |r| Ok(ModelUsageRow {
            model:          r.get::<_, String>(0).unwrap_or_default(),
            run_count:      r.get(1)?,
            input_tokens:   r.get(2)?,
            output_tokens:  r.get(3)?,
            total_cost_usd: r.get(4)?,
            avg_cost_usd:   r.get(5)?,
        }))
        .map_err(|e| format!("model rows failed: {}", e))?
        .filter_map(|r| r.ok())
        .collect();

    // ── By use case ──────────────────────────────────────────────────────────
    // Use case derived from run label prefix in Rust — same logic as RunList
    let use_case_sql = "
        SELECT
            r.label,
            COUNT(DISTINCT e.run_id)                                        AS run_count,
            COALESCE(SUM(json_extract(e.payload_json, '$.cost_usd')), 0.0) AS total_cost
        FROM events e
        JOIN runs r ON e.run_id = r.run_id
        WHERE e.type = 'llm_responded'
          AND json_extract(e.payload_json, '$.cost_usd') IS NOT NULL
        GROUP BY r.label
        ORDER BY total_cost DESC
    ";

    let mut stmt = conn.prepare(use_case_sql)
        .map_err(|e| format!("use case query failed: {}", e))?;

    let raw_use_case: Vec<(String, i64, f64)> = stmt
        .query_map([], |r| Ok((
            r.get::<_, String>(0)?,
            r.get::<_, i64>(1)?,
            r.get::<_, f64>(2)?,
        )))
        .map_err(|e| format!("use case rows failed: {}", e))?
        .filter_map(|r| r.ok())
        .collect();

    // Aggregate by use case prefix
    let by_use_case = aggregate_by_use_case(raw_use_case);

    Ok(UsageStats {
        total_cost_usd: total_cost,
        total_runs,
        instrumented_runs,
        total_input_tokens: total_in,
        total_output_tokens: total_out,
        by_model,
        by_use_case,
    })
}

// ── Use case prefix aggregation ───────────────────────────────────────────────

const USE_CASE_PREFIXES: &[(&str, &str)] = &[
    ("payslip",     "Payslip"),
    ("drive",       "Drive"),
    ("email",       "Email"),
    ("api-tenant",  "API / Tenant"),
    ("api-gateway", "API / Gateway"),
    ("provenance",  "Provenance"),
    ("cap-matrix",  "Capability Matrix"),
];

fn classify_label(label: &str) -> &'static str {
    let lower = label.to_lowercase();
    for (prefix, name) in USE_CASE_PREFIXES {
        if lower.starts_with(prefix) {
            return name;
        }
    }
    "Unclassified"
}

fn aggregate_by_use_case(rows: Vec<(String, i64, f64)>) -> Vec<UseCaseUsageRow> {
    use std::collections::HashMap;

    let mut map: HashMap<&'static str, (i64, f64)> = HashMap::new();
    for (label, run_count, cost) in &rows {
        let uc = classify_label(label);
        let entry = map.entry(uc).or_insert((0, 0.0));
        entry.0 += run_count;
        entry.1 += cost;
    }

    // Order by USE_CASE_PREFIXES order, Unclassified last
    let mut result: Vec<UseCaseUsageRow> = USE_CASE_PREFIXES
        .iter()
        .filter_map(|(_, name)| {
            map.get(name).map(|(rc, cost)| UseCaseUsageRow {
                use_case:       name.to_string(),
                run_count:      *rc,
                total_cost_usd: *cost,
            })
        })
        .collect();

    if let Some((rc, cost)) = map.get("Unclassified") {
        result.push(UseCaseUsageRow {
            use_case:       "Unclassified".to_string(),
            run_count:      *rc,
            total_cost_usd: *cost,
        });
    }

    result
}
```

### Registration

In `commands/mod.rs`:
```rust
pub mod usage;
```

In `lib.rs` `generate_handler![]`:
```rust
commands::usage::usage_stats_load,
```

`usage_stats_load` uses `get_harness_conn` — follow the same pattern as
`harness.rs`. Import it via `use crate::commands::harness::get_harness_conn;`
or make it `pub` in `harness.rs` if it isn't already.

---

### TypeScript types (add to `src/hooks/types.ts`)

```typescript
export interface ModelUsageRow {
  model:          string;
  run_count:      number;
  input_tokens:   number;
  output_tokens:  number;
  total_cost_usd: number;
  avg_cost_usd:   number;
}

export interface UseCaseUsageRow {
  use_case:       string;
  run_count:      number;
  total_cost_usd: number;
}

export interface UsageStats {
  total_cost_usd:      number;
  total_runs:          number;
  instrumented_runs:   number;
  total_input_tokens:  number;
  total_output_tokens: number;
  by_model:            ModelUsageRow[];
  by_use_case:         UseCaseUsageRow[];
}
```

Export all three from `src/hooks/index.ts`.

---

### `src/hooks/useUsageStats.ts`

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { UsageStats } from './types';

export function useUsageStats() {
  const [stats,   setStats]   = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    invoke<UsageStats>('usage_stats_load')
      .then((s) => { setStats(s);  setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }

  useEffect(() => { load(); }, []);

  return { stats, loading, error, refresh: load };
}
```

Export from `src/hooks/index.ts`.

---

### `src/components/modules/harness/UsageView.tsx`

```tsx
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
      <div className="flex items-center justify-center h-full
                      text-muted-foreground text-sm">
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
          <StatCard
            label="Total spend"
            value={formatCost(stats.total_cost_usd)}
          />
          <StatCard
            label="Total runs"
            value={stats.total_runs.toLocaleString()}
          />
          <StatCard
            label="Total tokens"
            value={formatTokens(
              stats.total_input_tokens + stats.total_output_tokens
            )}
          />
          <StatCard
            label="Avg cost / run"
            value={formatCost(avgCost)}
          />
        </div>

        {/* Pre-instrumentation note */}
        {stats.instrumented_runs < stats.total_runs && (
          <p className="text-xs text-muted-foreground">
            Cost data available for {stats.instrumented_runs.toLocaleString()} of{' '}
            {stats.total_runs.toLocaleString()} runs.
            Earlier runs were not instrumented.
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
                    <tr key={row.model}
                        className="border-b last:border-b-0 hover:bg-muted/30">
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
                      <td className="px-3 py-2 text-right tabular-nums
                                     text-muted-foreground text-xs">
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
                    <tr key={row.use_case}
                        className="border-b last:border-b-0 hover:bg-muted/30">
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

        {/* Empty state — no instrumented runs yet */}
        {stats.instrumented_runs === 0 && (
          <div className="flex items-center justify-center py-12
                          text-muted-foreground text-sm">
            No instrumented runs yet. Run an agent to start tracking usage.
          </div>
        )}

      </div>
    </div>
  );
}
```

---

### Route + registry

In `src/App.tsx`:
```tsx
import { UsageView } from '@/components/modules/harness/UsageView';

<Route path="/usage" element={
  <div className="flex flex-1 flex-col h-full bg-background overflow-hidden">
    <UsageView />
  </div>
} />
```

In `src/modules/registry.ts` — add fourth section to `harnessModule`:
```typescript
{ id: 'usage', label: 'Usage', icon: 'TrendingUp', path: '/usage' },
```

Add `TrendingUp` to `iconMap` in `Sidebar.tsx`.

---

## Acceptance criteria

- [ ] `usage_stats_load` command compiles, returns correct shapes
- [ ] Summary query uses `json_extract` with `IS NOT NULL` filter
- [ ] Use-case aggregation correct — same prefix order as run list
- [ ] `total_runs` counts all runs; `instrumented_runs` counts only runs
      with cost data
- [ ] Four summary cards: Total spend, Total runs, Total tokens, Avg cost/run
- [ ] Pre-instrumentation note shown when `instrumented_runs < total_runs`
- [ ] By model table: model, runs, input tokens, output tokens, total cost,
      avg/run — sorted by total cost descending
- [ ] By use case table: use case, runs, total cost — sorted by cost descending
- [ ] Empty state shown when `instrumented_runs === 0`
- [ ] Refresh button reloads stats
- [ ] Usage section in Harness sidebar (TrendingUp icon, `/usage`)
- [ ] `cargo build` exits 0, zero warnings
- [ ] `bun run build` exits 0, zero TypeScript errors
- [ ] No TypeScript `any`

---

## Files to create/modify

**Create:**
- `src-tauri/src/commands/usage.rs`
- `src/hooks/useUsageStats.ts`
- `src/components/modules/harness/UsageView.tsx`

**Modify:**
- `src-tauri/src/commands/mod.rs` — `pub mod usage;`
- `src-tauri/src/lib.rs` — register `usage_stats_load`
- `src/hooks/types.ts` — add `ModelUsageRow`, `UseCaseUsageRow`, `UsageStats`
- `src/hooks/index.ts` — export `useUsageStats` and new types
- `src/modules/registry.ts` — add Usage section to `harnessModule`
- `src/App.tsx` — add `/usage` route
- `src/components/shell/Sidebar.tsx` — add `TrendingUp` to `iconMap`

---

## Notes

**`get_harness_conn` visibility.** `usage.rs` calls `get_harness_conn` from
`harness.rs`. If it's currently private, add `pub` to the function signature
in `harness.rs`. Follow the same borrow pattern used in other commands.

**`avg_cost_usd` in SQL vs Rust.** The SQL `AVG()` averages per-event cost,
not per-run cost. For a more accurate per-run average, compute it in Rust:
`total_cost / run_count`. The SQL `AVG` is a reasonable approximation for
now — the difference is small when runs have similar step counts.

**`TrendingUp` from lucide-react.** Already used in `UsageView.tsx` header.
Add to `iconMap` in `Sidebar.tsx` alongside the existing imports.

**Empty tables.** If `by_model` or `by_use_case` is empty (no instrumented
runs), the sections are hidden via `{stats.by_model.length > 0 && ...}`.
The empty state message covers this case.
