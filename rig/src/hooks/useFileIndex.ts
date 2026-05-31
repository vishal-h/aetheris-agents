import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { FileEntry } from './types';

export interface UseFileIndexResult {
  entries: FileEntry[];
  total: number;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFileIndex(limit = 500, offset = 0): UseFileIndexResult {
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [fileEntries, fileCount] = await Promise.all([
        invoke<FileEntry[]>('f2_get_file_index', { limit, offset }),
        invoke<number>('f2_get_file_count'),
      ]);

      setEntries(fileEntries);
      setTotal(fileCount);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      console.error('Failed to fetch file index:', err);
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

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
    entries,
    total,
    loading,
    error,
    refetch: fetchData,
  };
}
