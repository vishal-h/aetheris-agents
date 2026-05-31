import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { TrajectoryFile } from './types';

export function useTrajectory(runId: string | null) {
  const [trajectory, setTrajectory] = useState<TrajectoryFile | null>(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setTrajectory(null);
      return;
    }
    setLoading(true);
    setError(null);
    invoke<TrajectoryFile>('trajectory_load', { run_id: runId })
      .then((t) => { setTrajectory(t); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, [runId]);

  return { trajectory, loading, error };
}
