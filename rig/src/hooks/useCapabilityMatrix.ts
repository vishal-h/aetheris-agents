import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { CapabilityMatrix } from './types';

export function useCapabilityMatrix() {
  const [matrix,  setMatrix]  = useState<CapabilityMatrix | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    invoke<CapabilityMatrix>('capability_matrix_load')
      .then((m) => { setMatrix(m);  setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, []);

  return { matrix, loading, error };
}
