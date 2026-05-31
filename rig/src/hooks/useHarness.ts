import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { HarnessStatus, RunSummary, EventRow, RunDetail } from './types';

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

export function useRunList(limit?: number): AsyncState<RunSummary[]> {
  return useInvoke<RunSummary[]>('harness_list_runs', limit !== undefined ? { limit } : undefined);
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

export function useRunDetail(runId: string | null): AsyncState<RunDetail> {
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

  useEffect(() => {
    if (!runId) {
      setData(null);
      setError(null);
      return;
    }
    fetch();
  }, [fetch, runId]);

  return { data, loading, error, refetch: fetch };
}
