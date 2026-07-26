import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

// ============================================================================
// useFork — imperative fork action (BL-007 t4, early-return since BL-030)
//
// Wraps the `fork_run` Tauri command (BL-007 t3). The command is `async` and
// **resolves when the fork starts**, not when it finishes: the CLI emits the
// child run id as soon as the run is started, and Rig returns it and hands the
// still-running subprocess to a background thread. The promise settles in
// seconds (mix boot + fork start) rather than minutes, so `forking` now covers
// the start, not the whole run — the caller navigates to the child and watches
// it stream.
//
// The signature is unchanged. A rejection now means the fork never *started*
// (`step_not_found`, an unreadable trajectory), carrying the CLI's stderr; a
// fork that starts and then fails surfaces on the child run's own trajectory,
// where its diagnosis was always recorded. The error handling mirrors
// `usePlaygroundSubmit`: surface via `error` and rethrow so the caller can skip
// its success path.
// ============================================================================

export function useFork(): {
  fork:       (runId: string, step: number, label?: string) => Promise<string>;
  forking:    boolean;
  error:      string | null;
  clearError: () => void;
} {
  const [forking, setForking] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const fork = useCallback(async (runId: string, step: number, label?: string): Promise<string> => {
    setForking(true);
    setError(null);
    try {
      // camelCase key `runId` → Rust `run_id`; `step`/`label` are single-word safe.
      // Omitting `label` maps to Rust `Option::None`.
      const forkedRunId = await invoke<string>('fork_run', { runId, step, label });
      return forkedRunId;
    } catch (e) {
      // fork_run's start-failure error already reads "fork failed: <stderr>"
      // (fork.rs `start_failure_error`); the error strip adds its own "Fork failed:"
      // label, so strip the redundant prefix here — the UI label is the single
      // authoritative frame (BL-007 t4 r6 cosmetic).
      const msg = String(e).replace(/^fork failed:\s*/i, '');
      setError(msg);
      throw new Error(msg);
    } finally {
      setForking(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { fork, forking, error, clearError };
}
