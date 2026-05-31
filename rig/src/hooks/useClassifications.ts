import { useEffect, useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ClassificationRow } from './types';

interface UseClassificationsOptions {
  client?: string;
  limit?: number;
}

export interface UseClassificationsResult {
  data: ClassificationRow[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useClassifications(opts: UseClassificationsOptions = {}): UseClassificationsResult {
  const { client, limit = 500 } = opts;
  const [data, setData] = useState<ClassificationRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await invoke<ClassificationRow[]>('provenance_classification_list', {
        client: client ?? null,
        status: null,
        limit,
      });
      setData(rows);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [client, limit]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useSetClassificationStatus() {
  const [reviewer, setReviewer] = useState('unknown');

  useEffect(() => {
    invoke<string>('get_system_username').then(setReviewer).catch(() => {});
  }, []);

  return useCallback(
    async (path: string, status: 'approved' | 'rejected'): Promise<void> => {
      await invoke('provenance_set_classification_status', { path, status, reviewer });
    },
    [reviewer],
  );
}
