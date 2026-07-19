# BL-007 / t2 — implementation notes: fork core alignment (seed-carry + CLI convergence)

**Ticket:** [README.md](./README.md) §t2 · **Milestone:** [BL-007](./README.md) (#48; per-ticket issues waived)
**Date:** 2026-07-19 · **Repos:** harness `../aetheris/` (branch `bl-007-t2`; the four source/test files) + `aetheris-agents/` (branch `bl-007-t2`; README rider + these notes)
**Watermark verified against:** harness `7ccdccf`, agents `ae0b0b2` (both `main`, clean; all t0/t1 handoff branches merged). Anything cited beyond these HEADs was fresh-read this session.

## What was built (harness, the ticket's four files)

1. **`lib/aetheris/execution/fork.ex`**
   - **Seed-carry (D1).** `assemble_config/5` base map now reads `seed: Map.get(meta, "seed")` (string key, no default). Absent → `nil`, matching both the `RunConfig` struct default (`run_config.ex:80`) and the canonical meta→config convention `from_map/2` (`run_config.ex:173`), so no clobber. The existing `struct(RunConfig, Map.merge(base, overrides))` means an atom-keyed `%{seed: n}` override still wins.
   - **Rename (ratified rider).** `find_last_step_complete/2` → `find_step_complete_at/2` (`defp` + its one call site in `build_fork_config/5`). The match is exact (`e.type == :step_complete and e.step == step`, no fallback) so "last" was false. No `@spec`/docstring referenced the private name. Behavior-neutral.
2. **`lib/aetheris/cli/commands/fork.ex`** — **CLI convergence (D2).** `start_fork/4` (struct-cloned the stored config, kept the original `user_prompt`, re-ran from the original prompt — the F1 bug) replaced by `start_fork/3` routing through `Fork.from_step/3`, exactly like `Aetheris.fork_run/3`. Alias `RunConfig` (now unused) dropped; alias `Fork` added. The `lookup_run` in `run_with_step/3` is kept as an existence precondition but its value discarded (`{:ok, _config} <-`). A new `fork_overrides/1` passes `%{label: name}` only when `--name` is given (atom key, required by `struct/2`). Both `from_step` error branches normalized to `String.t()` for the `@spec`.
3. **`test/aetheris/execution/fork_test.exs`** — `write_stub_trajectory/2` refactored to optionally emit a `:tool_result` event (`tool_result_step:`) and a `"seed"` meta value (`seed:`); seqs are now positional (`Enum.with_index`) so an injected event can't collide, and default output (no opts) stays byte-identical. Three new tests: seed inherited-unless-overridden, seed-nil-when-absent, tool_result→tool-message rebuild.
4. **`test/aetheris/cli/commands/fork_test.exs`** — `base_config/1` gains `seed: 4242`, a distinguishing `user_prompt: "original question"`, and a **tool-call step 0** (`max_steps: 2`; step 0 `echo`, step 1 finishing text) so the source records a real `:step_complete` fork point. The "fork with step" test now reads the fork's persisted config via `Aetheris.CLI.Commands.RunHelpers.lookup_run/1` and asserts seed carried (`4242`), provenance (`fork_from`/`fork_step`), `user_prompt == ""`, and the source prompt reconstructed into `fork_context` — closing the recon §4 gap (was status/run_id only).

## Design decisions (adjudicated, with source evidence)

- **`mode: :fork` dropped — mandated by contract §4 D2, not a choice.** `mode` is behaviorally significant only for `:replay`/`:verify` (`pre_tools.ex:59`, `loop.ex:410,648`); `:fork` is inert in the loop. Fork provenance meta is gated on `fork_from` presence, **not** mode (`server.ex:717-721`), and `assemble_config` always sets `fork_from`. `fork_run/3` never forces `mode: :fork` or `Aetheris.ID.generate()` — so forcing them in the CLI would *break* the mandated equivalence. Verified no in-repo code or test keys off `meta["mode"] == "fork"` or the `fork-` id format. Consequence: CLI forks now carry `meta["mode"] == "record"` and a `fork-`-prefixed id; they remain identifiable via `meta["fork_from"]`.
- **Rename target `find_step_complete_at`** — verb-prefixed to match the file's `build_/extract_/assemble_/generate_` style; exact-match-honest.
- **CLI-path observability via `lookup_run/1`.** `await_run/2` returns only `%{run_id, status}` — seed/context aren't observable there. But `encode_config/1` (`server.ex:752-761`) keeps `seed`/`fork_context`/`fork_from`/`fork_step`/`user_prompt` in the persisted `config_json` (it strips only pids/`stub_responses`/`label`/`max_duration`), and `lookup_run/1` round-trips them (string-keyed message maps preserved). So asserting on the stored fork config is the reliable CLI-path check.

### Discovery that shaped the CLI fixture (real fork-point semantics)

A **text** LLM response *finishes* the run: `handle_llm_response(_, _, _, %{type: :text})` emits `llm_responded` + `run_complete` "agent_finished" and **no `:step_complete`** (`loop.ex:237-265`). Only a **tool_call** step emits `:step_complete` and advances (`loop.ex:289-294`). So the original CLI source run (single text step, `max_steps: 1`) had **no forkable step** — once the CLI routes through `from_step`, forking it correctly returns `:step_not_found`. The fixture therefore makes step 0 a tool call. Worker-free by construction: `dispatch_tool(nil, …)` falls back to local `Echo.execute` writing the `"output"` key (`loop.ex:547+`), and even a tool *error* returns `{:ok, …}` from `execute_response` so `:step_complete` is still emitted — a tool-call step 0 robustly yields a fork point regardless of worker availability. This matches the F2 contract line "Consumers MUST offer fork only on completed steps."

## Deviations recorded (per the ratified Option-1 conditions — blocking if absent)

1. **Touches addition (5th file).** README §t2 (`docs/rig/milestones/bl-007/README.md`, agents repo) is edited beyond the ticket's four harness files, under the ratified Option-1 reconciliation of the rename rider. The edit is one minimal line in §t2 scope (new name; nothing restated from the contract).
2. **Sequencing slip.** The rename rider was ratified in the t2 ticket message *before* README §t2 carried it; the handoff's §1.1 doc-first sequencing (rider → README first, then draw the prompt from the updated doc) did not execute. Reconciled **concurrently within this review round** instead: §1.1's real invariant is "doc and impl in sync at every merge point," and — because the README edit is cross-repo and cannot literally share the harness commit — the README rider lands as **its own human-approved commit in the agents repo, no later than the harness t2 merge** (doc commit first or simultaneous within this round).
3. **Done-check expanded** to the full Elixir gate set (README §t2 lists the shorter set; the ticket message adds `mix format --check-formatted`, `mix credo --strict`, `mix dialyzer` per CLAUDE.md "every gate at every boundary" / t1 finding-3). Additive; divergence noted, not silently followed.
4. **`mode: :fork` dropped** for D2 convergence (evidence above) — a behavioral consequence of converging on `from_step`, recorded so it is a decision, not drift.

## Gate results (full set at the boundary)

```
cd ../aetheris
  mix test test/…/fork_test.exs test/…/cli/commands/fork_test.exs → 9 tests, 0 failures
  mix test                     → 868 tests, 0 failures, 114 excluded   (t1: 865; +3 new execution tests)
  mix hex.audit                → No retired or security advisory packages found
  mix format --check-formatted → clean (exit 0)
  mix credo --strict           → 1906 mods/funs, no issues
  mix dialyzer                 → Total errors: 0 (passed successfully)
cd ../aetheris-agents
  python3 scripts/drift_check.py → 8 PASS  0 FAIL  0 WARN  7 INFO   (7 INFO pre-existing, unrelated)
```

## Cross-ticket note (for the t2 review file)

This is the second doc-first sequencing slip class this milestone has flirted with (methodology §8 flags recovery/pressure moments as where doc-first slips; §1.1 was written then not executed). One occurrence isn't promotable; if anything similar surfaces at t3–t5, the promotion candidate is: *a ratified rider isn't executable until the milestone doc carries it — the ratification message and the doc edit are one act, not two.*

## Review round-1 facts (added on disposition)

- **Seed survives the real writer, not just a field copy (D1).** Provenance chain, end
  to end: source run executes with `seed: 4242` → `server.ex:668` (`"seed" => config.seed`)
  persists it into the trajectory meta via the real writer → the CLI's `from_step` does
  `File.read(run_id)` and reads that persisted `meta["seed"]` → `assemble_config` sets
  `seed: Map.get(meta, "seed")` → `encode_config` keeps it in the fork's `config_json` →
  `lookup_run(fork_id)` decodes it → the CLI test asserts `4242`. The test therefore
  proves seed survives the writer *and* the fork round-trip.
- **`mode` sweep — agents repo (Rig) result.** The t2 "nothing keys off `meta["mode"]`"
  claim, extended to the agents repo this round: **zero** `fork` occurrences in
  `rig/src` / `rig/src-tauri/src`; `TrajectoryMeta.mode` is `string` (not a fork enum);
  Rig only *displays* `meta.mode` (`TrajectoryView.tsx:341` MetaRow, `useRunDiff.ts:66`
  diff row), no branch. CLI forks render `Mode: "record"` — cosmetic. (Separately noted:
  `TrajectoryMeta.seed` is typed `string | null` but the harness writes an integer — a
  latent representation question, out of scope here.)

## Open items forwarded

- **Latent, out-of-scope (flag only):** `event_to_messages(%{type: :tool_result})` reads only `payload["output"]`, but real success payloads are mixed — worker/`run_command`-style tools write `"output"` while many in-process tools write `"result"` (`loop.ex:354,424,435,459,469,482,492,508`). Tool results whose payload uses `"result"` reconstruct with empty content on fork. Fixing it touches `fork.ex` only but is a behavior change beyond t2's four goals — candidate for a follow-up ticket, not this one.
- **t5 (export boundary, D6):** manifest regen incl. the contract; the backlog rows surfaced at t1 (`verifier.ex` effect-class/record-and-serve, first-diverging-event report gap, verify `KeyError` crash) still land there.
