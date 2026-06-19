# Review — m-docbuilder-m1 t7 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Agent file conventions", §"Orchestrator patterns", §"Pre-flight checklist"; aetheris-agents--CLAUDE.md; docbuilder/docs/milestones/m-docbuilder-m1-t6-implementation-notes.md §"t7 notes"

---

## Packet assessment

Ticket ID + scope: ✅ provided  
Diff — aetheris-agents (a16f898): ✅ 10 files (orchestrator, runbook, impl notes, 7 generate script --input additions)  
Diff — aetheris (5486c4e): ✅ sprint.sh  
Implementation notes: ✅ `m-docbuilder-m1-t7-implementation-notes.md` — present, substantive, honest about first-attempt failure  
Done-check output: ✅ syntax check exit 0, sprint run with xlsx+pdf confirmed, 123/123 tests, ls -lh output/  

---

## Findings

1. **[non-blocking]** The `--input` flag opens the file but does not close it
   explicitly. In all seven scripts the pattern is:
   ```python
   src = open(args.input, encoding="utf-8") if args.input else sys.stdin
   doc_spec = json.load(src)
   ```
   `src` is never closed (no `with` block, no `src.close()`). For a
   short-lived CLI script this is benign — the OS reclaims the file handle on
   exit. But it means the file is held open for the lifetime of any generation
   work that follows `json.load`. For m1 with small files and immediate exit,
   no impact. Non-blocking — worth a note for m2 if scripts become longer-lived
   or are called in loops.

2. **[non-blocking]** `run_id: n/a` in sprint output. The implementation notes
   document this clearly: `jq -r '.run_id // empty'` fails because the
   run.json file contains log noise before the JSON line. The t8 notes flag the
   fix: extract from the last JSON line. This is a known, documented limitation
   — non-blocking for t7. Should be fixed in t8 docs sync or promoted to a
   standing sprint.sh issue.

3. **[non-blocking]** The sprint.sh docbuilder case uses `warn` (not `fail`) if
   the xlsx or pdf output files are missing:
   ```bash
   warn "${fmt}: output not found (check run log)"
   ```
   A missing output file after a sprint run is a pipeline failure, not a
   warning. `fail` with `exit 1` would be more appropriate and consistent with
   how other sprint cases handle missing output. Non-blocking — the run
   produced output correctly in the done-check, so this only matters on
   failure paths. Worth a one-line fix before t8 commits sprint.sh changes.

4. **[question]** The `output/proposal.docx`, `output/proposal.pdf`, and
   `output/proposal.xlsx` files visible in the `ls -lh output/` listing
   (dated `Jun 19 08:22`, `Jun 19 10:51`, and `Jun 19 08:10` respectively)
   are from earlier manual pipeline runs (t4, t5, t3 done-checks). The t7
   sprint produced `proposal_v1.xlsx` and `proposal_v1.pdf` (versioned
   filename from `DOCBUILDER_DOC_TYPE=proposal` + `DOCBUILDER_VERSION=v1`).
   The unversioned files remain from earlier tickets. This is not a bug —
   the output dir convention is documented — but the `data/.gitignore`
   should confirm `output/*` is excluded. Confirmed: `output/.gitkeep`
   was committed and `output/*` is in the gitignore. No action needed,
   noted for completeness.

---

## Cross-ticket notes

- **`--input` as a fundamental `run_command` constraint** — the implementation
  notes document this clearly and honestly, including the first-attempt failure.
  This is exactly the kind of harness constraint that belongs in
  `agent-creation-guide.md` §"Common failure modes" as a standing note:
  *"run_command has no stdin parameter. Scripts that read from stdin must also
  accept `--input FILE` for orchestrator use."* Strong candidate for CLAUDE.md
  promotion at the t8 milestone-end ritual — this will affect every future
  agent that calls generation scripts.

- **`write_file` exception to the guide rule** — the justification ("this
  orchestrator is the exception: it must write intermediates") is clean and
  documented. The guide says "almost never need write_file" — the notes give
  the concrete condition under which it is needed. This is the right pattern
  for documenting justified deviations.

- **max_steps: 20 rationale documented** — the step count breakdown (4 setup +
  N render + 1 LLM per step ≈ 12 minimum) is exactly the kind of reasoning
  that should survive in the notes. Future orchestrator authors can reference
  this to size their own `max_steps`.

- **t8 readiness** — the implementation notes §"t8 notes" section is the
  cleanest forward-signalling in the milestone. Four concrete items: `--input`
  addition to doc-spec-schema.md, run_id fix in sprint.sh, README open
  questions closure, format characteristics table. t8 has a clear starting
  list.

- **Zero blocking findings. t7 is clear to merge. t8 is clear to start.**
