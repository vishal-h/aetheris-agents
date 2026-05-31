import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import {
  CorpusSummary,
  ClientRow,
  ScanRun,
  CorpusDuplicateGroup,
} from './types';

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

export function useCorpusSummary(): AsyncState<CorpusSummary> {
  return useInvoke<CorpusSummary>('provenance_corpus_summary');
}

export function useClientBreakdown(): AsyncState<ClientRow[]> {
  return useInvoke<ClientRow[]>('provenance_client_breakdown');
}

export function useScanRuns(): AsyncState<ScanRun[]> {
  return useInvoke<ScanRun[]>('provenance_scan_runs');
}

export function useDuplicateGroups(): AsyncState<CorpusDuplicateGroup[]> {
  return useInvoke<CorpusDuplicateGroup[]>('provenance_duplicate_groups');
}
