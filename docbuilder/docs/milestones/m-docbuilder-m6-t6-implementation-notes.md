# Implementation notes — m-docbuilder-m6 t6 (docs sync + milestone close)

Ticket: bring all reference docs in sync with t1–t5 (+ t4b), scan for recurring findings, write
the milestone summary, run drift. Docs-only.

---

## What shipped

- **`docs/capability-matrix.md`** — added `generate_html.py` and `generate_docx_from_html.py`
  rows; `render_template.py` row marked deprecated (m6); `generate_pdf.py` row notes the Jinja
  path. Counts: **docbuilder 2 agents / 24 scripts; total 25 / 62** (was 2/22, 25/60 — +2 the
  new scripts; cross-checked against `ls scripts/*.py` = 24 excl. conftest/__init__).
- **`docs/rig/runbook.md`** — added the m6 authoring/Jinja pointer after the m4 fresh-path
  entry (→ `docbuilder/runbook.md` §"Editing an existing template" / §"Adding a new doc type" /
  §"Jinja2 templates (m6)", + the two m6 sprint gates). This **clears the pre-m6 deferred
  BL-002 item** (the authoring-guide pointer that was held back to avoid a standalone re-upload).
- **`docbuilder/runbook.md`** — §"Jinja2 templates (m6)" gained the **t5 F3** `no_sheets?` note:
  the docx-jinja chain is for table-less narrative letters; a sheeted bundle (invoice) uses the
  structured `generate_docx.py` path.
- **`CLAUDE.md`** — `## Learning — m6-docbuilder` (two findings, each recurring on ≥2 tickets):
  (1) run an end-to-end/eval check beyond the unit done-check for pipeline-integration tickets
  (t3 compute_doc passthrough, t5 docx-jinja over-match — both passed the unit check, both
  broken end-to-end); (2) a generic renderer stays generic — pipeline enrichment (sheet tables)
  lives in the caller, so every render path must enrich or be excluded (t3/t5).
- **`docbuilder/docs/m6-milestone.md`** — milestone summary appended.

## Carries actioned at t6

- **t4b F1** (positional `compute_doc`): the t4b ticket lived outside this doc, so there is no
  `§t4b` done-check command in the milestone doc to fix — confirmed nothing stale to change.
  The corrected positional form is recorded in the t4b notes and the milestone summary.
- **t5 F3** (no_sheets? note): added to `docbuilder/runbook.md` (above).
- Review-scan covered t1, t2, t3, t4, **t4b**, t5.

## Done-check

- `drift_check.py`: **0 FAIL**. Pre-commit it reads 0 WARN (the three tracked files' last commit
  still matches the manifest until this commit lands); **post-commit it shows 3
  `project_knowledge` WARNs** — `CLAUDE.md`, `docs/capability-matrix.md`, `docs/rig/runbook.md`
  ahead of the manifest. These are **BL-002, human-owned**: re-upload the three, then advance
  `docs/project-knowledge-manifest.md` → 0 FAIL / 0 WARN. (13 INFO are pre-existing.)
- `grep` checks: `generate_html`/`generate_docx_from_html` in capability-matrix (3);
  `Jinja2 templates (m6)`/`docbuilder/runbook` pointer in rig runbook (3); anchored
  `^## Milestone summary` in m6-milestone.md (1); `no_sheets` note in docbuilder runbook (1);
  `## Learning — m6-docbuilder` (1).

## m6 close

t1–t6 (+ t4b) complete. The Jinja2 renderer backs the invoice PDF and a new offer-letter DOCX
doc type, both proven by live sprints (`docbuilder-orch-vb69ng`, `docbuilder-orch-MXl0Ew`).
**BL-002 (human-owned):** re-upload `docs/capability-matrix.md`, `docs/rig/runbook.md`,
`CLAUDE.md`; then advance the manifest to this commit.
