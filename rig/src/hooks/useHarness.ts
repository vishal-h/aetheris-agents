import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { HarnessStatus, RunListResult, EventRow, RunDetail } from './types';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

function useInvoke<T>(command: string, args?: Record<string, unknown>): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<T>(command, args);
      setData(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [command]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useHarnessStatus(): AsyncState<HarnessStatus> {
  return useInvoke<HarnessStatus>('harness_connection_status');
}

/**
 * Run list with optional server-side search (BL-038).
 *
 * Not `useInvoke`: that hook keys its effect on the command name alone, so a
 * changing argument would never refetch. Search is the whole point here, so this
 * one keys on `limit` + `search` and re-queries the store on every change.
 * Filtering is server-side only — a second, client-side filter over the window
 * could disagree with the store, which is the gap this replaced.
 */
export function useRunList(options?: { limit?: number; search?: string }): AsyncState<RunListResult> {
  const limit  = options?.limit;
  const search = options?.search ?? '';

  const [data, setData]       = useState<RunListResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const args: Record<string, unknown> = {};
      if (limit !== undefined) args.limit = limit;
      if (search !== '') args.search = search;
      const result = await invoke<RunListResult>('harness_list_runs', args);
      setData(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [limit, search]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useRunEvents(
  runId: string | null,
  options?: { polling?: boolean },
): AsyncState<EventRow[]> & { isPolling: boolean } {
  const [data, setData] = useState<EventRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activelyPolling, setActivelyPolling] = useState(false);

  const fetch = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<EventRow[]>('harness_get_events', { runId });
      setData(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  // Initial fetch on runId change
  useEffect(() => {
    if (!runId) {
      setData(null);
      setError(null);
      return;
    }
    fetch();
  }, [fetch, runId]);

  // Sync activelyPolling with caller's intent
  useEffect(() => {
    setActivelyPolling(options?.polling ?? false);
  }, [options?.polling]);

  // Stop polling when run_complete appears in the event stream
  useEffect(() => {
    if (!data || !activelyPolling) return;
    const done = data.some((ev) => ev.event_type === 'run_complete');
    if (done) setActivelyPolling(false);
  }, [data, activelyPolling]);

  // Interval-based polling
  useEffect(() => {
    if (!activelyPolling || !runId) return;
    const id = setInterval(fetch, 2000);
    return () => clearInterval(id);
  }, [activelyPolling, runId, fetch]);

  return { data, loading, error, refetch: fetch, isPolling: activelyPolling };
}

/**
 * Run statuses at which the harness has finished writing everything it will
 * write for a run. Mirrors `Aetheris.Store` (`done` / `failed` / `cancelled`).
 */
const TERMINAL_STATUSES = ['done', 'failed', 'cancelled'];

/**
 * The run row, optionally polled while the run is live (BL-030 r1).
 *
 * Polling this rather than only the event stream is what makes the completion
 * transition race-free. The harness's ordering at run end is:
 *
 *   1. the `run_complete` **event** is appended to SQLite  (`loop.ex:267`)
 *   2. the loop returns
 *   3. `trajectory.json` is written — tmp file, then atomic rename
 *      (`server.ex:680` → `file.ex:37-38`)
 *   4. `runs.status` is set to a terminal value       (`server.ex:456-465`)
 *
 * So the `run_complete` event arrives *before* the file exists — a reload fired
 * on seeing it in the event stream races the write — whereas the status flip
 * strictly follows the completed rename. Waiting for a terminal **status** is
 * therefore correct by construction and needs no retry.
 *
 * Self-terminating: polling stops as soon as a terminal status is observed.
 */
export function useRunDetail(
  runId: string | null,
  options?: { polling?: boolean },
): AsyncState<RunDetail> & { isPolling: boolean } {
  const [data, setData] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<RunDetail>('harness_get_run', { runId });
      setData(result);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  const [activelyPolling, setActivelyPolling] = useState(false);

  useEffect(() => {
    if (!runId) {
      setData(null);
      setError(null);
      return;
    }
    fetch();
  }, [fetch, runId]);

  // Sync activelyPolling with caller's intent
  useEffect(() => {
    setActivelyPolling(options?.polling ?? false);
  }, [options?.polling]);

  // Stop polling once the run row reaches a terminal status — by then the
  // harness has written everything, including the trajectory file.
  useEffect(() => {
    if (!data || !activelyPolling) return;
    if (TERMINAL_STATUSES.includes(data.status)) setActivelyPolling(false);
  }, [data, activelyPolling]);

  // Interval-based polling. Same 2s cadence as useRunEvents, against the same
  // local SQLite file.
  useEffect(() => {
    if (!activelyPolling || !runId) return;
    const id = setInterval(fetch, 2000);
    return () => clearInterval(id);
  }, [activelyPolling, runId, fetch]);

  return { data, loading, error, refetch: fetch, isPolling: activelyPolling };
}
