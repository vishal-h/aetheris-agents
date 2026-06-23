# Implementation notes — m-docbuilder-m3 t5 (milestone close)

Ticket: docs sync + capability matrix + CLAUDE.md learning scan + milestone summary +
drift check.

---

## What shipped

- **Capability matrix** (`docs/capability-matrix.md`) — targeted edit (the agent drops
  underscore helpers; a hand edit is deterministic and the delta is known): added
  `context_builder.exs` (→ docbuilder **2 agents**) and `run_log_writer.py` +
  `resolve_last_run.py` (→ **20 scripts**); repo total **25 agents / 58 scripts**.
- **CLAUDE.md** — new `## Learning — m3-docbuilder` with three ≥2-ticket promotions:
  1. Deterministic script owns derived values; the LLM only orchestrates — assert with a
     byte-identical / end-to-end check (t3 byte-identical, t4 end-to-end).
  2. A divergence from the milestone doc is closed by adjudicating + updating the doc
     (single source of truth) — t2 (gate), t3 (degrade), t4 (env var, autoconfirm).
  3. Pre-list next-step tools; verify stateful pipelines against their own output record;
     reset accumulating fixtures (t2 run_command, t4 renamed.json + run_log seed reset).
- **rig runbook** (`docs/rig/runbook.md`) — new "m3 — context builder" subsection:
  `DOCBUILDER_REQUEST` / `DOCBUILDER_CONTEXT_FILE`, context-source precedence,
  `DOCBUILDER_AUTOCONFIRM` not-implemented note, the recurring-resolution flow, PHASE D2,
  and the `docbuilder_context` sprint invocation.
- **README** (`docbuilder/README.md`) — rewrote the m3 roadmap section: m3 is now the
  delivered **context builder** (✦ done); the original Option C + conversational template
  editing scope is marked **deferred**.
- **Milestone summary** — appended to `docs/m3-milestone.md` (shipped / capability matrix /
  promoted learnings / deferred / surprises / BL-002).

---

## Done-check

- Full docbuilder suite: **292 passed, 3 skipped**.
- drift_check **before committing these docs**: 8 PASS / 0 FAIL / 0 WARN (HEAD still
  matched the manifest while the doc edits were unstaged).
- After committing t5, `CLAUDE.md`, `docs/capability-matrix.md`, and `docs/rig/runbook.md`
  advance past the manifest → 3 `project_knowledge` WARNs (expected; the BL-002 re-export
  is human-owned). Cleared by re-upload + advancing `docs/project-knowledge-manifest.md`.
- Capability-matrix counts cross-checked against `ls docbuilder/{agents,scripts}`:
  2 agents, 20 scripts (excluding conftest/__init__).

---

## m3 close

m3 (t1–t5) is complete. The context builder produces a rendered "same as last month"
invoice end-to-end. Deferred to a future milestone: Option C (freeform NL extraction),
conversational template editing, an interactive confirm/amend loop.

**BL-002 (human-owned):** re-upload `CLAUDE.md`, `docs/capability-matrix.md`,
`docs/rig/runbook.md` to the Claude.ai project; then advance the manifest to clear the
3 WARNs (→ 0 FAIL / 0 WARN).
