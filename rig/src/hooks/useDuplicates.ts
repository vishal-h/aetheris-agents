import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { DuplicateGroup } from './types';

export interface UseDuplicatesResult {
  groups: DuplicateGroup[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDuplicates(): UseDuplicatesResult {
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const duplicateGroups = await invoke<DuplicateGroup[]>('f2_get_duplicates');
      setGroups(duplicateGroups);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Failed to fetch duplicates:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const unlisten = listen('scan-complete', () => {
      fetchData();
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, [fetchData]);

  return {
    groups,
    loading,
    error,
    refetch: fetchData,
  };
}
