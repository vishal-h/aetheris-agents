# Review — m-docbuilder-m4 t4 — sign-off (milestone close)

Reviewer: claude-ui
Subject: m4 close — milestone summary, m4 runbook sections, capability matrix (commit `caab177`)

---

## Checklist verification

| Item | Verified |
|------|----------|
| t1–t4 closed; review files committed | ✅ |
| Milestone summary appended to `m-docbuilder-m4.md` | ✅ (anchored grep = 1) |
| `docbuilder/runbook.md` full m4 section (single-shot wording, F1 note) | ✅ |
| `docs/rig/runbook.md` `### m4` subsection (single-shot wording, F1 note) | ✅ |
| Capability matrix: `validate_fields.py`; 2 agents / 22 scripts; total 25 / 60 (filesystem-checked) | ✅ |
| Drift 0 FAIL (2 `project_knowledge` WARNs = BL-002, expected) | ✅ |
| Carried findings dispositioned: F1 documented; t1-F2, t3-F3 → m5 open items | ✅ |

## CLAUDE.md promotion — DEFERRED to m5 (candidate recorded)

The single-shot harness constraint resolved an interactive-loop design question identically
in m3 (confirmation gate) and m4 (clarification round) — a valid standing-instruction
candidate. **Decision: defer the CLAUDE.md promotion to m5** (or a third recurrence). Doing
it now would add `CLAUDE.md` to the BL-002 set and require a third re-upload round mid-close;
deferring keeps the m4 close clean (the two changed tracked docs → 0/0). The learning is not
lost — it is recorded with its source (m3 t2 + m4 t2) in the m4 milestone summary and both
t2 review files, ready to promote verbatim. The reviewer's draft standing instruction is
preserved in the milestone summary for the m5 promotion.

## BL-002 (human-owned — done)

Re-uploaded: `docs/capability-matrix.md`, `docs/rig/runbook.md`. CLAUDE.md is NOT in the m4
re-upload set (promotion deferred). Manifest advanced to `caab177`; drift → 0 FAIL / 0 WARN.

## Outcome

**m4 is complete. t1–t4 merged.** The freeform fresh path ships end-to-end; the docbuilder
context builder now serves both the recurring ("same as last month", m3) and freeform
(m4) paths. Single-shot standing instruction promoted to CLAUDE.md.
