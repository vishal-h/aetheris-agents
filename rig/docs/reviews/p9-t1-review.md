# Review — rig-p9 t1 — round 1

Reviewer: claude-ui
Subject: `orchestrate_start` per-run env vars (`extra_env`) — commit `096cd30`

---

## Findings

1. **[blocking → actioned, doc-only] `orchestrate_start` hardcodes the script path.**
   `orchestrate_start` runs a hardcoded `{agents_path}/agents/orchestrator.exs`, and
   `useOrchestrator.start` takes no script path — but t4 must run
   `docbuilder_context_orchestrator.exs`. The t1 notes flagged this; it widens t4's Rust
   surface beyond what the milestone doc described. **Actioned (doc-only, no t1 code
   change):** updated `rig/docs/milestones/p9/README.md` §t4 —
   - Added a "Prerequisite" block (run before the panel): add
     `script_path: Option<String>` to `orchestrate_start` (default
     `agents/orchestrator.exs` when `None` → existing callers unaffected); thread
     `scriptPath?: string` through `useOrchestrator.start`.
   - Added `orchestrate.rs` and `useOrchestrator.ts` to §t4 Touches.
   - Reconciled "Do not generate" — extending `orchestrate_start` with `script_path`
     is in scope; no *new* commands.
   - Added the prerequisite to the §t4 Claude-code prompt.

2. **[non-blocking → actioned] `cargo build` path.** The t1 done-check said
   `cd rig && cargo build`, but `Cargo.toml` is in `rig/src-tauri/`. **Actioned:** t1
   done-check now builds via `( cd src-tauri && cargo build … )` (subshell keeps cwd at
   `rig/` for the rest of the block). t2/t4 use `cargo tauri dev` (works from `rig/`) and
   have no raw `cargo build`, so no change needed there.

3. **[non-blocking → merge gate] `cargo tauri dev` smoke not run** (no display in this
   environment) — expected for the automated done-check. **Manual smoke pass is the t1
   merge gate (operator-owned):** Orchestrator → "Additional env vars" visible (collapsed
   by default), expands via chevron, add/remove rows work, key/value inputs accept text,
   Run still works with zero rows.

---

## Cross-ticket notes

- F1 (t4 scope update) landed in this commit so t4 is prompted with the correct surface.
- F2 path correction applied to t1; t2/t4 unaffected (no raw `cargo build`).
- F3 manual smoke is the merge gate for t1.

---

## Outcome

No t1 code changes. Two doc fixes to the milestone doc (§t4 prerequisite/Touches/prompt,
t1 `cargo build` path) committed alongside this review. **t1 clear once the manual smoke
pass is confirmed.**
