# Review — m-docbuilder-m6 t6 — sign-off (milestone close)

Reviewer: claude-ui
Subject: m6 close — docs sync, learning promotions, milestone summary (commit `eeb37a1`)

---

## Checklist verification

| Item | Verified |
|------|----------|
| t1–t5 + t4b all closed; review files committed | ✅ |
| `docs/capability-matrix.md` — `generate_html.py` + `generate_docx_from_html.py` added; `render_template.py` deprecated; `generate_pdf.py` Jinja note; counts 2/24, 25/62 | ✅ grep 3 hits |
| `docs/rig/runbook.md` — m6 authoring/Jinja pointer + sprint gates (clears pre-m6 deferred BL-002 item) | ✅ grep 3 hits |
| `docbuilder/runbook.md` — `no_sheets?` note in §"Jinja2 templates (m6)" (t5 F3) | ✅ grep 1 hit |
| `## Learning — m6-docbuilder` in `CLAUDE.md` — 2 promotions, each sourced to ≥2 tickets | ✅ |
| Milestone summary appended to `m6-milestone.md` | ✅ anchored grep = 1 |
| Drift: 0 FAIL (3 `project_knowledge` WARNs = BL-002 re-upload, expected) | ✅ |
| All carries actioned: t4b-F1 (positional compute_doc confirmed), t5-F3 (no_sheets? note), review scan included t4b | ✅ |

## Learning promotions — quality check

- **L1 (end-to-end check for pipeline-integration tickets)** — sourced to t3 (`has_jinja`
  passthrough) + t5 (docx-jinja over-match). Both: unit done-check green, integration broken.
  Specific + actionable ("inspect the final artifact"). Will change claude-code's done-check
  behaviour on future pipeline tickets.
- **L2 (generic renderer stays generic; enrichment lives in the caller)** — same two tickets,
  the architectural lesson distinct from L1's process lesson. `no_sheets?` is the canonical
  correct resolution (restrict the path that can't enrich; don't duplicate injection).

## BL-002 (human-owned — required to clear drift WARNs)

Re-upload to the Claude.ai project: `aetheris-agents--CLAUDE.md`, `docs/capability-matrix.md`,
`docs/rig/runbook.md`. Then advance `docs/project-knowledge-manifest.md` to `eeb37a1` and
re-run drift_check → 0 FAIL / 0 WARN.

## Outcome

**m6 is complete. t1–t6 (+ t4b) merged.** The Jinja2 renderer backs the invoice PDF and the
offer-letter DOCX, both proven by live sprints (`docbuilder-orch-vb69ng`,
`docbuilder-orch-MXl0Ew`). BL-002 re-upload is the only remaining step.
