import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import {
  PlaygroundStatus,
  PlaygroundPolicy,
  PlaygroundSandboxes,
  PlaygroundSubmitRequest,
  PlaygroundSubmitResult,
  PlaygroundRunStatus,
} from './types';

// ============================================================================
// Shared async-state shape (mirrors useHarness.ts)
// ============================================================================

interface AsyncState<T> {
  data:    T | null;
  loading: boolean;
  error:   string | null;
  refetch: () => void;
}

function useInvoke<T>(command: string, args?: Record<string, unknown>): AsyncState<T> {
  const [data, setData]       = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

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

// ============================================================================
// Playground connection status
// ============================================================================

export function usePlaygroundStatus(): AsyncState<PlaygroundStatus> {
  return useInvoke<PlaygroundStatus>('playground_connection_status');
}

// ============================================================================
// Policy — provider list, model map, tools, caps, defaults
// ============================================================================

export function usePlaygroundPolicy(): AsyncState<PlaygroundPolicy> {
  return useInvoke<PlaygroundPolicy>('playground_get_policy');
}

// ============================================================================
// Sandboxes
// ============================================================================

export function usePlaygroundSandboxes(): AsyncState<PlaygroundSandboxes> {
  return useInvoke<PlaygroundSandboxes>('playground_get_sandboxes');
}

// ============================================================================
// Run status — on-demand; no polling
// ============================================================================

export function usePlaygroundRunStatus(runId: string | null): AsyncState<PlaygroundRunStatus> {
  const [data, setData]       = useState<PlaygroundRunStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<PlaygroundRunStatus>('playground_run_status', { runId });
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

// ============================================================================
// Submit — returns run_id on success, throws on error
// ============================================================================

export function usePlaygroundSubmit(): {
  submit:    (request: PlaygroundSubmitRequest) => Promise<PlaygroundSubmitResult>;
  loading:   boolean;
  error:     string | null;
  clearError: () => void;
} {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const submit = useCallback(async (request: PlaygroundSubmitRequest): Promise<PlaygroundSubmitResult> => {
    setLoading(true);
    setError(null);
    try {
      const result = await invoke<PlaygroundSubmitResult>('playground_submit_run', { request });
      return result;
    } catch (e) {
      const msg = String(e);
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { submit, loading, error, clearError };
}

// ============================================================================
// MRU — recent submissions stored in localStorage
// ============================================================================

const STORAGE_KEY = 'rig:playground:history';
const MAX_STORED  = 20;

export interface PlaygroundMruEntry {
  run_id:       string;
  label:        string;
  provider:     string;
  model:        string;
  submitted_at: string;
}

export function usePlaygroundHistory(): {
  history: PlaygroundMruEntry[];
  add:     (entry: PlaygroundMruEntry) => void;
} {
  const [history, setHistory] = useState<PlaygroundMruEntry[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as PlaygroundMruEntry[]) : [];
    } catch {
      return [];
    }
  });

  const add = useCallback((entry: PlaygroundMruEntry) => {
    setHistory((prev) => {
      const deduped = [
        entry,
        ...prev.filter((e) => e.run_id !== entry.run_id),
      ].slice(0, MAX_STORED);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(deduped));
      return deduped;
    });
  }, []);

  return { history, add };
}
