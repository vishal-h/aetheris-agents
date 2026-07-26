import { useState, useEffect, useCallback } from 'react';
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
    invoke<TrajectoryFile>('trajectory_load', { runId })
      .then((t) => { setTrajectory(t); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, [runId]);

  /**
   * Re-attempt the file load without disturbing what is on screen (BL-030 r1).
   *
   * A run that completes while being watched writes its `trajectory.json` only
   * at the end, so by then the view is in BL-005 reconstructed mode and the
   * now-existing file would never be read. This lets the caller pick it up.
   *
   * **Silent by design:** `loading` is deliberately not set. `TrajectoryView`
   * renders `Loading…` whenever `loading` is true, so a reload that touched it
   * would blank the streamed view mid-watch and flash it back — the transition
   * has to be seamless or it is no better than the tab-out this exists to
   * remove. On success `error` is cleared, and that is what flips the view from
   * reconstructed to file-backed. On failure the previous error is kept, so a
   * run whose file genuinely never appeared (a failed write — `server.ex:680`
   * discards the write result — or a BL-003-swept orphan) stays reconstructed
   * with its terminal banner instead of losing the view it had.
   */
  const reload = useCallback(() => {
    if (!runId) return;
    invoke<TrajectoryFile>('trajectory_load', { runId })
      .then((t) => { setTrajectory(t); setError(null); })
      .catch(() => { /* keep the reconstructed view and its existing error */ });
  }, [runId]);

  return { trajectory, loading, error, reload };
}
