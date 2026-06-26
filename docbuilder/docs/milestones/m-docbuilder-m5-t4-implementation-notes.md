# Implementation notes — m-docbuilder-m5 t4 (docs sync + milestone close)

Ticket: bring all reference docs in sync with t1–t3, action the carried t1/F1 smoke-command
fix, scan for recurring findings, write the milestone summary, run drift. Docs-only.

---

## What shipped

- **`docs/capability-matrix.md`** — appended to the `render_template.py` row description:
  `Optional fields render as empty string when absent (m5).` Counts unchanged (no new
  scripts/agents — m5 modified existing files only).
- **`docs/rig/runbook.md`** — added the `docbuilder_fresh_render` full-chain paragraph to the
  m4 fresh-path section; **also corrected the now-stale "Known limitation"** (it still claimed
  the sprint's client-match checks the hardcoded "Northwind" substring, which t2 replaced with
  a client-agnostic non-empty check).
- **`docbuilder/runbook.md`** — corrected the same stale "Known limitation" in the m4-detail
  section (lines ~209). The `docbuilder_fresh_render` sprint-case list entry was already added
  in t3.
- **`docbuilder/docs/m5-milestone.md`** — (1) corrected the §t1 Done-check smoke command
  (t1 F1): real asset filenames `invoice_v1.*` and a valid empty spec piped on stdin
  (`echo '{"sheets":[]}' | … --spec -`). The Touches note that said `--spec '{"sheets":[]}'`
  was itself wrong — `--spec` is a path/`-`, not inline JSON — so I used the script's stdin
  contract and updated the note to match. (2) Appended the `## Milestone summary`.
- **`CLAUDE.md`** — added `## Learning — m5-docbuilder`: **no recurring findings** across
  t1–t3 (each review carried ≤1 finding, none recurring on ≥2 tickets). The single-shot
  promotion lives under `## Learning — m4-docbuilder` (pre-milestone commit).

## Done-check

- `drift_check.py`: **7 PASS / 0 FAIL / 1 WARN / 13 INFO** at notes-write time. The lone WARN
  is `project_knowledge: CLAUDE.md stale` (the pre-milestone commit `6da271d` is ahead of the
  manifest `6127ebc`) — BL-002, human-owned. After this t4 commit, `docs/capability-matrix.md`
  and `docs/rig/runbook.md` will also go ahead of the manifest → **3 expected
  `project_knowledge` WARNs**; all clear once re-uploaded and the manifest is advanced. INFO
  lines (env_vars agent-side, payload_fields, etc.) are pre-existing and unrelated.
- `grep render_template docs/capability-matrix.md` → the m5 note present.
- `grep docbuilder_fresh_render docs/rig/runbook.md` → present.
- `grep -c "^## Milestone summary" docbuilder/docs/m5-milestone.md` → **1** (anchored).
- **Corrected §t1 smoke command verified runnable**: `echo '{"sheets":[]}' | render_template.py
  --template …invoice_v1.md.template --css …invoice_v1.css --context '{...}' --spec -` →
  `grep -c '{{'` = **0**, and the renderer actually runs (no longer a trivial 0).

## Notes / decisions

- **Doc-accuracy sweep beyond strict Touches.** t2's client-agnostic change made a "Known
  limitation" claim false in *both* runbooks; the close ticket is the right place to correct
  doc drift, so I fixed `docbuilder/runbook.md` too even though only `docs/rig/runbook.md` was
  named in the t4 Touches. Flagged in the review packet.
- **Touches-text vs reality on the smoke fix.** The t4 Touches text inherited `--spec
  '{"sheets":[]}'` from the t1 review wording, but that is not a valid invocation (`--spec`
  takes a path or `-`). Used the stdin form and corrected the Touches note in the same commit.
- No `sprint.sh` change in t4 → no aetheris-repo commit this ticket.

## m5 close

t1–t4 complete; the freeform fresh→render chain ships with zero `{{` artifacts, proven
end-to-end (run `docbuilder-orch-h2yeTQ`). **BL-002 (human-owned):** re-upload
`docs/capability-matrix.md`, `docs/rig/runbook.md`, and `CLAUDE.md`, then advance
`docs/project-knowledge-manifest.md` → 0 FAIL / 0 WARN.
