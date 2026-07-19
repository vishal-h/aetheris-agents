import { useState, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

// ============================================================================
// useFork — imperative fork action (BL-007 t4)
//
// Wraps the `fork_run` Tauri command (BL-007 t3). The command is `async` and
// **blocks to completion**: `mix aetheris fork` prints the child run id only when
// the fork reaches a terminal status (`await_run`), so the invoke promise resolves
// only when the fork finishes — minutes for a real provider. Callers therefore
// need the `forking` flag to show an in-flight state. A non-`done` outcome rejects
// with the CLI's stderr; the mirror of `usePlaygroundSubmit`'s error handling
// surfaces it via `error` and rethrows so the caller can skip its success path.
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
      const msg = String(e);
      setError(msg);
      throw new Error(msg);
    } finally {
      setForking(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { fork, forking, error, clearError };
}
