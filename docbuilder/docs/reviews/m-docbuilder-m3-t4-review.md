# Review — m-docbuilder-m3 t4 — round 1

Reviewer: claude-ui
Subject: orchestrator reads confirmed_context.json + docbuilder_context sprint
(aetheris-agents `79c930a`, aetheris `56435a3`)

---

## Findings

1. **[blocking → adjudicated (a), actioned] `DOCBUILDER_CONTEXT_FILE` env var missing.**
   The file path was hardcoded to `output/confirmed_context.json`; the design table
   specifies a configurable env var. **Actioned:**
   - Orchestrator: `confirmed_path = System.get_env("DOCBUILDER_CONTEXT_FILE") ||
     Path.join(agent_root, "output/confirmed_context.json")`.
   - Sprint case: sets `DOCBUILDER_CONTEXT_FILE` to the absolute path before the
     orchestrator run; unsets it afterward (no leak under `TARGET=all`).
   - Milestone doc: added the `DOCBUILDER_CONTEXT_FILE` design-table row.
   - Re-verified eval in three modes (DOCBUILDER_CONTEXT set; DOCBUILDER_CONTEXT_FILE set;
     neither set with the default file present).

2. **[non-blocking → actioned] Hardcoded verification target `…30-Jun-2026…`.** Would
   break in another month. **Actioned:** the sprint now verifies the files listed in the
   orchestrator's own `output/renamed.json` (PHASE D's authoritative record) — fully
   date-independent and tied to *this* run (renamed.json is removed at case start).

3. **[non-blocking → actioned (discretionary)] `Context source:` path clarity.** The
   label now shows the actual path used and its origin:
   `file:<path> (DOCBUILDER_CONTEXT_FILE)` vs `file:<path> (default)` vs
   `env:DOCBUILDER_CONTEXT`.

4. **[non-blocking → confirmed, actioned] `DOCBUILDER_AUTOCONFIRM`.** Not implemented.
   **Actioned (doc-only):** added a milestone-doc note — "DOCBUILDER_AUTOCONFIRM: not
   implemented (t4 decision); the context builder always writes confirmed_context.json and
   the operator reviews the trajectory before invoking the orchestrator (single-shot gate,
   t2/F2)."

---

## Cross-ticket notes

- t5 Touches: `DOCBUILDER_CONTEXT_FILE` in the rig runbook env-var table; the
  `DOCBUILDER_AUTOCONFIRM` note; sprint verification documented as renamed.json-derived
  (date-independent).
- The "scripts do, agents decide" invariant held across t3 (byte-identical) and t4
  (end-to-end render from script-produced context) → **CLAUDE.md standing-instruction
  promotion at t5**.

---

## Outcome

F1 (env var) + F4 (doc) actioned; F2 (date-independent verification) + F3 (label) actioned.
Round-2 re-verify: eval in three modes, full suite, end-to-end docbuilder_context sprint.
**t4 clear after round-2 re-verify.**
