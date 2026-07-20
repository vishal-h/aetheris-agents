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

---

# §7 promotion draft (claude-ui, authored)

**Filed retroactively 2026-07-20**, in the same commit that lands P6 and P8. This section
exists because of the rule it contains: through the whole §7 ritual this wording lived only
in chat — the P3–P6 relay gap held the promotion commit at round 2, and P6 again required a
third relay attempt after the session restart. The review file is where the draft should
have been from the start, so it is filed here now and the milestone's own record becomes
what the new rule requires of every milestone after it.

Wordings below are claude-ui's, as authored. P1–P5 landed at `3394386`; P6 and the
transport rule land with this commit. All six are in `CLAUDE.md` §"Learning — BL-007".

**P1 (class E — packet integrity).**
A packet section referenced is a packet section absent — inline every required section
verbatim; existence-in-repo does not satisfy the packet. `Source: m-docbuilder-m1 t4, t8;
BL-007 t3`

**P2 (class F — acting ahead of an unexecuted gate).**
No action past a gate until that gate has run and its result is on the record — covering
doc-order gates, test gates, and publish/merge gates alike. `Source: BL-007 t2, t4 (×2)`

**P3 (class A — deferred findings).**
A deferred finding gets a backlog row in the same round it's deferred — prose in a packet
or notes files nothing. `Source: BL-007 t1, t2, t3`

**P4 (class B — forward carry).**
Decisions that constrain ticket N+1 land in N+1's README section before its session
starts — implementation notes don't travel forward on the prompt path.
`Source: BL-007 t2, t3, t4`

**P5 (class D — decay of verified claims).**
A correction chases the corrected claim into every doc that adopted it, in the same
round — and a verified citation decays the moment the file moves; re-verify at HEAD before
reuse. Absorbs class C's residual (C itself withdrawn — "Cited-means-read" exists at
`../aetheris/CLAUDE.md:530-532`). `Source: BL-007 t2, t4, t5`

**P6 (classes G+H — symptom vs. mechanism). Ratified 2026-07-20 with an explicit bar
exception.**
One symptom can have several mechanisms: verify a fix against the real counterpart in the
operator's environment, not a simulation — and a fix proven for one face doesn't close the
symptom until the observed face is captured directly. Promoted **below** §7's ≥2-ticket
threshold by explicit human ratification: the class recurred across six *rounds* of one
ticket rather than across two tickets, and that cost was judged sufficient evidence. The
exception is recorded in the CLAUDE.md entry itself so the override is auditable rather
than erosive. `Source: BL-007 t4 r3–r6`

**Transport rule (class E, applied to the §7 pipeline itself).**
Promotion wording travels as a review-file artifact, not chat: claude-ui's §7 promotion
draft lands in `docs/reviews/` before the promotion commit is cut.
`Source: BL-007 t5 (§7 ritual, ×2)`

**P7 — methodology amendment, not a CLAUDE.md rule.** Landed in the harness at `0a0439f`:
§6's runbook trigger list gains "changes the observable semantics of an existing command,
flag, or UI affordance" (t2's `--step N` change matched none of the four existing nouns),
and §7 step 1 gains the second-input clause from scan observation 3 (a review-file-only
scan cannot see class I).

**P8 — reachability mechanism, option (c). Ratified 2026-07-20.** One standing line in
*each* repo's CLAUDE.md directing cross-repo milestone sessions to read both repos'
learning sections at session start. Rejected: (a) duplicating rules into both files, which
invites the copy-divergence this project's drift apparatus exists to prevent; (b) a
cross-reference alone, which depends on a session prioritising a pointer it has no reason
to follow. (c) puts the cost once at session start, changes no rule's home, and creates no
second copy to drift.
