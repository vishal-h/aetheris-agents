import { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { CorpusSummary } from './types';

export interface UseProvenanceStatusResult {
  connected: boolean;
  error: string | null;
}

export function useProvenanceStatus(): UseProvenanceStatusResult {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    invoke<CorpusSummary>('provenance_corpus_summary')
      .then(() => {
        setConnected(true);
        setError(null);
      })
      .catch((e: unknown) => {
        setConnected(false);
        setError(String(e));
      });
  }, []);

  return { connected, error };
}
