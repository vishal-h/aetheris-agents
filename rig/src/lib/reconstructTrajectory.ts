import type {
  EventRow,
  RunSummary,
  TrajectoryEvent,
  TrajectoryFile,
  TrajectoryMeta,
} from '@/hooks/types';

/**
 * Reconstruct a TrajectoryFile from the live SQLite event stream + config JSON.
 *
 * The harness writes `trajectory.json` atomically only at clean run end
 * (server.ex → file.ex), so the file is absent for `running` runs and for
 * runs swept from orphaned state (BL-003). This rebuilds the same view the
 * trajectory viewer renders directly from `harness_get_events` +
 * `runs.config_json`, so the Trajectory tab works before (and without) a file.
 *
 * Fidelity note: `EventRow.payload` is a raw JSON *string* (SQLite
 * `payload_json` column); the file inlines the same payload as an object.
 * Both stores are complete and untruncated, so parsing each row yields an
 * identical payload — the only difference is string vs object.
 *
 * `meta` is only partially recoverable pre-completion: model / provider /
 * mode / max_steps / tools / prompts / sandbox_path / seed come from
 * `config_json`; started_at / finished_at from the run row. `step_count` is
 * derived from the events seen so far. Fields the file records at completion
 * that have no live source (`overlay_changes`) are left empty.
 */

/** The data source backing a rendered trajectory. */
export type TrajectorySource = 'file' | 'events';

/** Parse a single `EventRow` (payload is a raw JSON string) into a `TrajectoryEvent`. */
export function parseEventRow(row: EventRow): TrajectoryEvent {
  return {
    id:         row.id,
    run_id:     row.run_id,
    seq:        row.seq,
    step:       row.step,
    event_type: row.event_type,
    payload:    parsePayload(row.payload),
    timestamp:  row.timestamp,
  };
}

/**
 * Parse `EventRow.payload` (a JSON string) into an object. Payloads are always
 * valid JSON in the DB, but if a row is ever malformed the raw string is
 * preserved under `_raw` rather than dropped, so nothing is silently lost.
 */
function parsePayload(raw: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return { _raw: parsed };
  } catch {
    return { _raw: raw };
  }
}

function stringField(config: Record<string, unknown>, key: string): string {
  const value = config[key as keyof typeof config];
  return typeof value === 'string' ? value : '';
}

function toolsField(config: Record<string, unknown>): string[] {
  const value = config['tools' as keyof typeof config];
  return Array.isArray(value) ? value.filter((t): t is string => typeof t === 'string') : [];
}

function maxStepsField(config: Record<string, unknown>): number {
  const value = config['max_steps' as keyof typeof config];
  return typeof value === 'number' ? value : 0;
}

function seedField(config: Record<string, unknown>): number | null {
  const value = config['seed' as keyof typeof config];
  if (value === null || value === undefined) return null;
  const n = Number(value);
  return Number.isNaN(n) ? null : n;
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

/**
 * Build a `TrajectoryFile` from live events + the run's `config_json`.
 *
 * @param runId      the run being viewed
 * @param run        the run summary (status / provider / model / timestamps), or null
 * @param configJson `runs.config_json` (from `harness_get_run`), or null
 * @param rows       events from `harness_get_events`
 */
export function reconstructTrajectory(
  runId: string,
  run: RunSummary | null,
  configJson: string | null,
  rows: EventRow[],
): TrajectoryFile {
  const config = parseConfig(configJson);
  const events = rows.map(parseEventRow);

  // step_count: number of distinct step indices observed so far. Live runs
  // have no recorded final count; this reflects progress at read time.
  const stepCount = new Set(rows.map((r) => r.step)).size;

  const meta: TrajectoryMeta = {
    model:           stringField(config, 'model')    || (run?.model ?? ''),
    provider:        stringField(config, 'provider') || (run?.provider ?? ''),
    mode:            stringField(config, 'mode'),
    step_count:      stepCount,
    max_steps:       maxStepsField(config),
    started_at:      run?.started_at ?? stringField(config, 'started_at'),
    // TrajectoryMeta.finished_at is '' when the run has not finished — mirrors
    // the Rust unwrap_or default on the file path (see types.ts).
    finished_at:     run?.finished_at ?? '',
    tools:           toolsField(config),
    system_prompt:   stringField(config, 'system_prompt'),
    user_prompt:     stringField(config, 'user_prompt'),
    sandbox_path:    stringField(config, 'sandbox_path'),
    seed:            seedField(config),
    overlay_changes: [],
  };

  return {
    run_id:         runId,
    schema_version: '1',
    meta,
    events,
  };
}

/**
 * Banner text for a reconstructed (non-file) trajectory. A live run reads
 * "live — reconstructed from events"; a terminal run reads "trajectory file
 * unavailable — reconstructed from events".
 *
 * "unavailable" (not "no trajectory file") is deliberate: the fallback fires on
 * any `trajectory_load` failure, which includes a completed run whose file is
 * corrupt or a truncated `.tmp` — the file exists but is unreadable. "no
 * trajectory file" would be false for that case; "unavailable" is accurate for
 * both an absent file (a BL-003-swept orphan) and an unreadable one. The
 * original read error is surfaced to the console by the caller so the
 * interrupted-write signal is not lost.
 */
export function reconstructedBanner(status: string | undefined): string {
  return status === 'running'
    ? 'live — reconstructed from events'
    : 'trajectory file unavailable — reconstructed from events';
}
