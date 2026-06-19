# Review — m-docbuilder-m1 t8 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6, §7; aetheris-agents--CLAUDE.md §"Learning"; docbuilder/docs/milestones/m-docbuilder-m1-t7-implementation-notes.md §"t8 notes"

---

## Packet assessment

Ticket ID + scope: ✅ provided  
Diff — aetheris-agents (18b9b01): provided via done-check evidence (no explicit diff block in packet)  
Diff — aetheris (00248a7): sprint.sh — cap-matrix-docbuilder case + run_id fix  
Implementation notes: ✗ absent (docs-only ticket; accepted on done-check evidence — see F1)  
Done-check output: ✅ capability matrix sprint output, grep confirming docbuilder section, ls milestones/, pytest 123/123

---

## Findings

**F1 (non-blocking)** — no diff block in packet, no implementation notes file.
Accepted on done-check evidence for a docs ticket, but the human should verify
the 8 expected files are all in 18b9b01:
- capability-matrix.md ✅
- README.md ✅
- milestone.md ✅
- doc-spec-schema.md ✅
- rig--runbook.md ✗ (not in 18b9b01; docbuilder section missing — gap fixed post-review)
- agent-creation-guide.md ✅
- CLAUDE.md ✅
- t8-implementation-notes.md ✗ (not created — gap fixed post-review)

**F2 (question — confirmed no action)** — `no-json (228 bytes)` pattern in sprint
output. This is the log noise that caused the original `jq` run_id extraction to
fail. The `grep -o` fix correctly skips it. Confirmed expected behaviour.

**F3 (question — resolved)** — CLAUDE.md showed only 2 of 3 expected promotions.
Missing: "implementation notes are a required deliverable." Added post-review.
All three promotions now present:
1. `run_command` has no stdin parameter — `--input FILE` required
2. Review packets must open with done-check output block
3. Implementation notes are a required deliverable

---

## Gaps fixed post-review

The following items were missing from 18b9b01 and fixed in the post-review commit:

- `docs/rig/runbook.md` — docbuilder section added (env vars, sprint invocation,
  expected output, 3 common failure modes)
- `docbuilder/docs/milestones/m-docbuilder-m1-t8-implementation-notes.md` — created
- `CLAUDE.md` — third learning promotion added (impl notes required)

**F4 (t1 gap — fixed post-review)** — `docbuilder/output/` was missing a
`.gitignore` rule. The `agent-creation-guide.md` §"Repository structure"
specifies `output/*` with `!output/.gitkeep` as a required ignore rule for
every use case. Only `data/.gitignore` was committed at t1; `output/` had
`.gitkeep` committed but no ignore rule for its contents. Result: pipeline
output files (`proposal.xlsx`, `proposal.pdf`, `pipeline_raw.json`, etc.)
appeared as untracked in `git status`. Fixed by adding
`docbuilder/output/.gitignore` with `* / !.gitignore / !.gitkeep`.

---

## Milestone retrospective

Two items most relevant for m2 planning:

**`run_command` stdin constraint** — document the `--input FILE` convention in
the m2 milestone from day one. Every future agent that calls generation scripts
will hit this. The pattern is now in `agent-creation-guide.md` and CLAUDE.md,
but the m2 milestone prompt should call it out explicitly so it is not
re-discovered.

**`summary_rows` design emerged during t1, not planning** — the two-pass
processing requirement (data-bearing sheets → summary sheets) was implicit in
the template schema decided at t1. The m2 planning phase should explicitly
design the multi-source merge schema before any tickets start, so that
`compute_doc.py` extension points are specified, not discovered during
implementation.

---

**Milestone status: DONE** — all gaps resolved post-review. m1 is clear to close.
