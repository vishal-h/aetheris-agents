# Review — rig-p9 t5 — sign-off (milestone close)

Reviewer: claude-ui
Subject: rig-p9 close — specs/runbook sync, capability matrix, CLAUDE.md learnings (commit `6127ebc`)

---

## Checklist verification

| Item | Verified |
|------|----------|
| t1–t4 all closed, 4 review files committed | ✅ |
| `docs/rig/specs.md` — `extra_env` + `script_path` + `.py` heuristic; `DOCBUILDER_TENANT` §1; Docbuilder module §8 | ✅ |
| `docs/rig/runbook.md` — Docbuilder module section + env row | ✅ |
| Capability matrix — `chain_docbuilder.py`; 2 agents / 21 scripts; total 25 / 59 | ✅ (filesystem cross-check) |
| `## Learning — rig-p9` — 2 promotions, each sourced to ≥2 tickets | ✅ |
| Milestone summary appended | ✅ |
| Drift: 0 FAIL (4 `project_knowledge` WARNs = BL-002, expected) | ✅ |
| Path correction `rig/docs/` → `docs/rig/` fixed in milestone doc | ✅ |

## Observation → recorded

The `docs/rig/` vs `rig/docs/` confusion surfaced twice (t1 `cargo build` directory; t5 doc
paths), each caught + fixed in-ticket. Recorded in the t5 implementation notes. **Pre-flight
item for the next milestone template:** "confirm `docs/rig/` is the drift-checked + manifest-
tracked path; `rig/docs/` is legacy." (Process note — no code change.)

## BL-002 (human-owned — required to clear drift WARNs)

Re-upload to the Claude.ai project: `CLAUDE.md`, `docs/capability-matrix.md`,
`docs/rig/specs.md`, `docs/rig/runbook.md`. Then advance
`docs/project-knowledge-manifest.md` to `6127ebc` and re-run drift_check → 0 FAIL / 0 WARN.

## Outcome

**rig-p9 is complete. t1–t5 merged.** The Docbuilder panel ships end-to-end: a
natural-language request in Rig → rendered, branded document, via a top-level chain script
that emits the orchestrator protocol. Headline learnings (no `run_command` env / `sh`
blocked; no nested `mix aetheris run`) promoted to CLAUDE.md.
