# Implementation notes — m-docbuilder-m4 t4 (milestone close)

Ticket: docs sync — milestone summary, m4 runbook sections, capability matrix, drift.
Docs-only.

---

## What shipped

- **`m-docbuilder-m4.md`** — appended `## Milestone summary` (shipped t1–t4; the two
  accepted divergences — `amount_due` display-string, single-shot self-correction; deferred
  items; m5 open items incl. the single-shot promotion candidate; BL-002).
- **`docbuilder/runbook.md`** — new `## m4 — freeform NL field extraction` section
  (extract → validate → self-correct once → gate/clarify; `docbuilder_fresh` sprint;
  `raw_extraction.json` / `validated_extraction.json`; the validate-exit-1 failure mode).
  Uses the **single-shot self-correction** wording (t2 adjudication), not "wait for reply".
  Includes the F1 default-request known-limitation note.
- **`docs/rig/runbook.md`** — promoted the t3 inline "Freeform fresh path" paragraph into a
  proper `### m4 — freeform NL field extraction (fresh path)` subsection (mirrors the m3
  entry; single-shot wording; F1 note).
- **`docs/capability-matrix.md`** — added `validate_fields.py`; docbuilder **2 agents /
  22 scripts**; repo total **25 / 60** (cross-checked against the filesystem).

## Carried findings — disposition

- **t3 F1** (client-match uses default request) → documented as a "known limitation" in
  both runbooks' `docbuilder_fresh` entries.
- **t1 F2** (hardcoded `CURRENCIES` allowlist) → recorded in the milestone summary as an
  m5 open item.
- **t3 F3** (test docstring "Integration tests") → m5 cosmetic open item. NOT fixed here:
  t4 is docs-only ("do not modify any `.py`/`.exs`"), and it's a non-functional label.
- **t2 confirm** — both runbook m4 sections use the single-shot self-correction model, not
  "wait for reply". Verified.

## Done-check

- `drift_check.py`: **0 FAIL** (pre-commit 1 WARN = t3's committed `docs/rig/runbook.md`;
  after this commit `docs/capability-matrix.md` + `docs/rig/runbook.md` are ahead of the
  manifest → `project_knowledge` WARNs, expected — BL-002). `tauri_commands`/`routes`/
  schema all PASS.
- `## Milestone summary` section present (`grep -c "^## Milestone summary"` = 1; the doc's
  own unanchored `grep -c` from the t4 prompt counts the in-doc references too, so the
  anchored count is the meaningful one).
- Capability-matrix counts verified against `ls docbuilder/scripts` (22 scripts excl.
  conftest/__init__).

## m4 close

t1–t4 complete; the freeform fresh path ships end-to-end (operator-verified at t2/t3).
**BL-002 (human-owned):** re-upload `docs/capability-matrix.md` + `docs/rig/runbook.md`,
then advance `docs/project-knowledge-manifest.md` → 0 FAIL / 0 WARN. (CLAUDE.md unchanged
in m4 — the single-shot learning promotion is a separate, human-approved step if it recurs.)
