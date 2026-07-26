import type { RunDetail, RunSummary } from '@/hooks/types';

/**
 * Build a `RunSummary` from the real `runs` row (BL-030 r2).
 *
 * Exists to kill a synthesized placeholder at its source. After a fork, the run
 * list had no row for the child yet, so `RunList.handleForked` invented a
 * summary with `started_at: ''`, `label: ''`, `model: ''`. Every consumer of the
 * selected run then inherited those blanks — `new Date('')` renders
 * "Invalid Date" — and r1 fixed only the consumers it enumerated
 * (`TrajectoryView` via `reconstructTrajectory`), leaving the Events tab header
 * reading the placeholder directly. Fixing the source means there is nothing to
 * enumerate: the invention is gone.
 *
 * The data was always available. `Aetheris.start_run/1` calls `Server.run/1`,
 * which is a **synchronous** `GenServer.call` (`server.ex:70-72`) whose
 * `handle_call(:run, …)` upserts the row — `status`, a real `started_at`,
 * `config_json`, `label` — before returning (`server.ex:229-235`). The CLI's
 * fork-start emit happens after that call returns, so by the time Rig has the
 * forked id from stdout the row is already in SQLite. One `harness_get_run` and
 * the placeholder is unnecessary.
 *
 * Fields with no live source are left honestly empty rather than zeroed with
 * intent: counts are genuinely 0 at fork-start, and cost/token totals are
 * `null` (not `0`) so the Cost cell and its tooltip render "—" instead of
 * claiming $0.0000 — the same contract `handleForked`'s placeholder already
 * observed and `types.ts` documents.
 */
export function runSummaryFromDetail(detail: RunDetail): RunSummary {
  const config = parseConfig(detail.config);

  return {
    run_id:      detail.run_id,
    // `harness_get_run` returns COALESCE(label, run_id) (harness.rs:300), so an
    // unlabelled fork yields its run_id here. That is what the Events header
    // wants: it prints the run_id separately only when it differs from the
    // label, so the id shows exactly once either way.
    label:       detail.label,
    status:      detail.status,
    provider:    stringField(config, 'provider'),
    model:       stringField(config, 'model'),
    started_at:  detail.started_at,
    finished_at: detail.finished_at,
    // True at fork-start, and superseded by the real row on the next Refresh.
    step_count:  0,
    event_count: 0,
    last_event_at: null,
    total_cost_usd: null,
    total_input_tokens: null,
    total_output_tokens: null,
  };
}

function stringField(config: Record<string, unknown>, key: string): string {
  const value = config[key];
  return typeof value === 'string' ? value : '';
}

function parseConfig(configJson: string | null): Record<string, unknown> {
  if (!configJson) return {};
  try {
    const parsed = JSON.parse(configJson) as unknown;
    if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return {};
  } catch {
    return {};
  }
}
