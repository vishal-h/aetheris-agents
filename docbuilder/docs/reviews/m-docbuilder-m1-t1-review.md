# Review — m-docbuilder-m1 t1 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"

---

## Packet assessment

Diff: ✅ provided  
Done-check output: ✅ provided (`template valid`, `11 docbuilder/data/sample_data.csv`)  
Implementation notes: ❌ missing — no `docs/milestones/m-docbuilder-m1-t1-implementation-notes.md` in diff. Per aetheris-agents--CLAUDE.md §"Implementation notes", this file is required before marking a ticket done. **This finding is blocking because it is a process requirement, not cosmetic — the audit trail depends on it.**

---

## Findings

1. **[blocking]** Implementation notes file not committed. Per aetheris-agents--CLAUDE.md §"Implementation notes": "On completing any milestone ticket, create a file at `docs/aetheris/milestones/{milestone}-{ticket}-implementation-notes.md` before marking the ticket done." The equivalent docbuilder path is `docbuilder/docs/milestones/m-docbuilder-m1-t1-implementation-notes.md`. The design note about `summary_rows` (see finding 3) is exactly the content this file exists to capture — it is currently in chat only, which the methodology explicitly rules out: "If a decision isn't in a file, it didn't happen." Contract: aetheris-agents--CLAUDE.md §"Implementation notes"; milestone-methodology.md §1.6. **Fix: write the file in the t2 session as the first touch (backdated to t1 scope), then add it as an explicit Touches item in every subsequent ticket prompt.**

2. **[non-blocking]** The `data/.gitignore` pattern `templates/*/` excludes all tenant subdirectories correctly, but `templates/demo/*/` with `!templates/demo/proposal_v1.json` would also exclude any future files added under `templates/demo/` (e.g. a second template version `proposal_v2.json`). This is probably too restrictive — new demo templates should be commitable without gitignore edits. Suggested fix: replace the last two lines with `!templates/demo/` (allow all files in the demo tenant). Non-blocking because there is only one template for now; address before adding a second demo template.

3. **[question — design impact]** The `summary_rows` key was introduced on the Summary sheet (distinct from `aggregate_rows` on data-bearing sheets). This distinction was not in the t1 milestone prompt or the README design decisions — it was a claude-code design choice made during implementation. The choice is sound (the two cases are semantically different), but it needs to be: (a) captured in the t1 implementation notes, (b) explicitly handled in the t2 `compute_doc.py` scope as a named requirement — specifically the two-pass ordering constraint: data-bearing sheets must be fully computed before summary sheets that reference them via `summary_rows[].aggregate.source_sheet`. If t2 does not handle both paths, the pipeline will be incomplete. **This is a question because the design choice itself is correct, but the downstream impact on t2 is material — the t2 prompt must be updated before the t2 session starts.**

---

## Cross-ticket notes

- The `summary_rows` / `aggregate_rows` split introduced in t1 has direct scope implications for t2 (`compute_doc.py` two-pass processing), t3 (`generate_xlsx.py` must render both), and t4 (`generate_docx.py` same). The milestone doc's t2–t4 prompts should be reviewed and updated before those tickets run. The current t2 prompt references "aggregate values are pre-computed here" but does not name the two-pass constraint or the `summary_rows` path explicitly.
- The missing implementation notes file is a process gap that, if left until t8 (docs sync), creates an incomplete audit trail for the full milestone. Establish the pattern in t2 to avoid compounding.
