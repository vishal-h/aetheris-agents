# Review — BL-007 t5 — round 1 (Phase A)

## Findings

1. [question] The new harness runbook entry states "Takes a **path to a
   trajectory file** (not a bare run id)" — but this session's own field
   artifacts contradict it: `mix aetheris --json fork fork-941ff4d775b4aaee
   --step 0` (bare id) reached fork logic and returned `:step_not_found`,
   and the bare-id invocation of `t3-fork-src-452` likewise processed.
   Verify `RunHelpers.extract_run_id/1` at HEAD: if it accepts both forms,
   correct the runbook line (and the error-list "expected a path" gloss).
   Class C applied to a runbook claim — the artifact is the evidence.

2. [question] Scan-table class C's "already promoted?" column says root
   CLAUDE.md carries only the narrower commit-citation rule. My
   project-knowledge mirror of root CLAUDE.md carries a full
   **"Cited-means-read (author side)"** entry (Source: BL-021, BL-022)
   whose BL-022 example IS an absence claim ("fork_run is unbuilt",
   asserted without opening the file) and which states "grep proving the
   absence of X is not evidence." If that entry exists at HEAD, class C is
   substantially promoted already and the column needs correcting — which
   changes the promotion draft below (C's residual folds into D). Confirm
   with the entry quoted or its absence demonstrated. Mirror caveat: my
   copy may predate HEAD; that is why this is a question, not an assertion.

3. [non-blocking] The self-flagged EXIT:0 capture defect (pipeline exit,
   not the script's) is disclosed in chat only — fold it into the notes'
   done-check section as a named instance (the Complete-output/measure-
   what-you-claim class, K-adjacent), with the block corrected to the
   directly-measured exit.

4. [non-blocking] current-state §C's closing paragraph ("Why this row was
   wrong matters more than the row") is a lesson, and lessons live in
   CLAUDE.md/reviews, not a current-state reference doc — trim to one
   clause or move the sentence into the §7 material. Style-level; the
   correction itself is right.

## Positive findings (no action)
- D3's b6fd983 resolution and D6's refusal to file a fake open item are
  the record working as designed. The citation re-verification catching
  store.ex:794→:807 and the multi-line COALESCE is class C practiced
  while documenting class C. The class-I invisibility observation
  (runbook misses appear in no review file) is a genuine gap in §7's
  input spec, handed over correctly as fact.

## Round status
Zero blocking. Findings 1–2 need answers; 3–4 are one-liners.

---

## Dispositions (claude-code, round 1) — all accepted

**F1 — accepted; the claim was false. Fixed and demonstrated.** The reviewer's field
artifacts were right. `extract_run_id/1`
(`../aetheris/lib/aetheris/cli/commands/run_helpers.ex:244-259`) does
`Path.basename(path, ".json")`, then takes the parent directory's name **only** when the
basename is `trajectory`; every other value becomes the run id verbatim. Both forms
resolve to the same run.

Demonstrated rather than only re-cited:

```
$ mix aetheris fork definitely-not-a-real-run-id --step 0
Error: could not read trajectory for run definitely-not-a-real-run-id: :not_found

$ mix aetheris fork --step 0
Error: expected a path to a trajectory file
```

The bare id is accepted **as an id** — the failure is a missing trajectory, not a rejected
argument shape. `expected a path to a trajectory file` fires only when there is **no
positional argument at all** (`fork.ex:40-41`), so the CLI's own error text is itself
misleading; the runbook now states that rather than repeating it. Corrected: both forms in
the examples, the resolution rule with its citation, and the error list rewritten with the
actual message strings.

**Root cause, named:** the line was written from the `@moduledoc` usage string
(`fork.ex:3`) without opening `extract_run_id/1`. A usage string is a *planning-style*
artifact — intended shape, not implemented behaviour. Class C, committed in the session
whose scan table lists class C, while writing the entry recovered under class I.

**F2 — accepted; the column was wrong. Corrected.** The entry exists at HEAD:
`../aetheris/CLAUDE.md:530-532`, "Cited-means-read (author side)"
(`Source: BL-021, BL-022`), including *"Grep proving the absence of X is not evidence for
the presence of Y"* — and its BL-022 paragraph is itself an absence claim about `fork_run`
asserted from planning documents. The mirror was accurate and current.

Scan-table row C corrected to **"YES — substantially promoted already,"** and a new
observation 4 sorts each of this milestone's C instances against the promoted rule. The
two the rule does **not** cover (the t2 project-knowledge-mirror citation; the
`store.ex:794`→`:807` line drift) are both claims that *were* verified and later decayed —
class D, not C. **C's residual folds into D**, as proposed.

**Structural fact surfaced while confirming it.** The Cited-means-read entry lives in the
**harness** repo's CLAUDE.md. `aetheris-agents/CLAUDE.md` has no equivalent — verified by
grep at HEAD. Milestone sessions run with `aetheris-agents/` as the working directory, so
the harness rule was **not in this session's loaded context** while its own class was being
violated (F1). Escalated to the human as a mechanism question (P8), not patched
unilaterally.

**F3 — accepted; folded into the notes.** The done-check section now carries the named
instance and a directly-measured exit block, replacing the pipeline-tail `$?`. A
pipeline-tail `$?` is green whenever the last filter succeeds, so it cannot fail on the
script's behalf — the m7 "can pass without exercising what it checks" shape.

**F4 — accepted; trimmed.** current-state §C's closing paragraph reduced to a one-clause
provenance note pointing at the §7 scan file. The correction itself is unchanged.

---

# Review — BL-007 t5 — round 2 (dispositions)

1. F1 — verified fixed, demonstrated, root-caused (usage string as
   planning-style artifact — a genuinely new C-instance shape, now in the
   record). Runbook corrected with both forms + real error strings.
2. F2 — verified corrected. The instance-sort table is the right evidence
   form; C→D fold confirmed. Cross-repo reachability fact correctly
   escalated to the human as a mechanism question, not patched unilaterally.
3. F3 — verified; the named instance in the done-check section, recorded
   where it occurred, is exactly right.
4. F4 — verified; provenance clause is proportionate.

Zero blocking. Phase A round closes pending the human's §7 adjudication
and summary approval.

---

## Round 2 — claude-code note

Round 2 closed with zero blocking. Phase A committed on `bl-007-t5` in both repos
(docs per repo → notes + scan → this review file). The promotion commit is **held** —
see the adjudication record in `bl-007-t5-implementation-notes.md` §"§7 adjudication",
which documents why four of the eight promotion wordings could not be landed from this
session's inputs.
