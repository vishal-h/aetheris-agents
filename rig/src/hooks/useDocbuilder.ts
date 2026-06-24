import { useCallback } from 'react';
import { useOrchestrator } from './useOrchestrator';

const CHAIN_SCRIPT = 'docbuilder/scripts/chain_docbuilder.py';

/**
 * Docbuilder panel hook — a thin wrapper over `useOrchestrator` that runs the
 * docbuilder chain script (`chain_docbuilder.py`) top-level via the `.py` heuristic
 * in `orchestrate_start`. The script emits the orchestrator protocol, so the full
 * phase lifecycle (plan → steps → done) is driven by `useOrchestrator` for free.
 *
 * `DOCBUILDER_REQUEST` is passed as a per-run env var; `DOCBUILDER_TENANT` comes from
 * stored agent config and is injected automatically at spawn.
 */
export function useDocbuilder() {
  const orch = useOrchestrator();

  const run = useCallback((request: string) => {
    return orch.start(request, { DOCBUILDER_REQUEST: request }, CHAIN_SCRIPT);
  }, [orch]);

  return {
    phase:        orch.phase,
    plan:         orch.plan,
    params:       orch.params,
    stepStatuses: orch.stepStatuses,
    stepErrors:   orch.stepErrors,
    error:        orch.error,
    run,
    reset:        orch.reset,
  };
}
