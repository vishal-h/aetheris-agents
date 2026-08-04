/**
 * Derive a pipeline stage name from a step's `run_command` tool call (BL-086).
 *
 * Exported separately from TrajectoryView so it can be exercised against real on-disk
 * trajectories without rendering anything — the derivation is offline-provable even
 * though the badge itself is not (Tauri `invoke` does not resolve headless).
 *
 * Payload shapes were enumerated over 68 cloudcost + docbuilder trajectories (468 steps)
 * rather than assumed. What that found, and what this therefore has to tolerate:
 *
 *   - The script lives at `tool_input.args[0]`. There is NO top-level `args`; a naive
 *     `payload.args[0]` reads undefined on every real payload.
 *   - `tool_name` is the only reliable discriminator. Native tools (`read_file`,
 *     `write_file`) carry just `{tool_name, tool_input}` with no `server_id`/`source`,
 *     so keying on those would silently skip nothing and match nothing.
 *   - `command` is not always `python3`: `cat` (14), `bash` (4), `sh` (3), `ls` (2)
 *     also appear, and one payload puts an entire shell line in `command` with **no
 *     `args` key at all**. That last one is the real null-args case this must survive.
 *   - 331 of 359 `run_command` calls carry exactly one `.py` arg; 28 carry none.
 *   - No step in 468 contained more than one `run_command`, so "first match wins" is a
 *     safety rule for a case that does not currently occur, not a guess about ordering.
 *
 * Accepted latent case: keying on `tool_name` + a `.py` arg rather than on
 * `command === 'python3'` means a non-python command that merely *mentions* a script —
 * `cat scripts/fetch_aws.py` — would be labelled as that stage. Deliberate: gating on
 * `command` under-matches real runs (see the command spread above), and the mislabel
 * occurs 0× in 468 steps. Revisit only if inspection-style `cat`/`ls` calls on `.py`
 * files start appearing in pipelines; the fix would be to require `command` to be a
 * python interpreter *and* the arg to be `.py`, which trades this edge for the
 * under-matching one.
 */

/** The subset of TrajectoryEvent this needs (types.ts:238-247). */
export interface StageEventLike {
  event_type: string;
  payload:    Record<string, unknown> | null | undefined;
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v);
}

/**
 * Stage name from a single `tool_called` payload, or null when it is not a script call.
 *
 * Returns null — never throws — for every unrecognised shape: wrong tool, absent or
 * non-object `tool_input`, absent/null/non-array `args`, and args with no `.py` entry.
 */
export function stageFromToolCallPayload(payload: unknown): string | null {
  if (!isRecord(payload)) return null;
  if (payload.tool_name !== 'run_command') return null;

  const toolInput = payload.tool_input;
  if (!isRecord(toolInput)) return null;

  const args = toolInput.args;
  if (!Array.isArray(args)) return null;

  // First `.py` rather than args[0]: tolerates a flag or `-m` ahead of the script. No
  // such invocation exists in the enumerated data, so this is headroom, not a fix.
  const script = args.find((a): a is string => typeof a === 'string' && a.endsWith('.py'));
  if (!script) return null;

  const base = script.slice(script.lastIndexOf('/') + 1).slice(0, -'.py'.length);
  return base.length > 0 ? base : null;
}

/**
 * Stage for a step, from its events. Null when the step ran no script — the
 * orchestrator's final summary turn, and any step whose only tools were read/write.
 */
export function stageForStep(events: readonly StageEventLike[] | null | undefined): string | null {
  if (!Array.isArray(events)) return null;
  for (const e of events) {
    if (!isRecord(e) || e.event_type !== 'tool_called') continue;
    const stage = stageFromToolCallPayload(e.payload);
    if (stage) return stage;
  }
  return null;
}

/** Badge text for a step header: "Step 3 · fetch_aws", or "Step 3" when no script ran. */
export function stepBadge(step: number, events: readonly StageEventLike[] | null | undefined): string {
  const stage = stageForStep(events);
  return stage ? `Step ${step} · ${stage}` : `Step ${step}`;
}
