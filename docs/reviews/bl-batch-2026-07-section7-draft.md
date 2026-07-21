# §7 promotion draft — small-ticket batch b1–b3 (BL-029+BL-004, BL-028, BL-031)

**Status:** DRAFT for human adjudication. Authored by claude-ui, 2026-07-21, per the
transport rule (promotion wording travels as a review-file artifact, not chat).
Target path on commit: `docs/reviews/bl-batch-2026-07-section7-draft.md`
(aetheris-agents). Nothing below lands in any CLAUDE.md until adjudicated; the
promotion commit is claude-code's, reviewed like any other, per methodology §7
step 3.

**Scan basis.** No milestone doc — the batch ran on backlog rows. Inputs, per §7's
"review files are not the only input": `docs/reviews/bl-029-review.md`,
`bl-028-review.md`, `bl-031-review.md` (all rounds + addenda), the three
implementation-notes files, the BL-038/BL-039/BL-040 rows, and the post-push
correction record. Bar: findings recurring on ≥2 tickets.

---

## Class 1 — the silent wrong answer

**Proposed rule (one instruction):**

> **A mechanism that returns a well-formed value where a gap exists is asserting,
> not reporting — before trusting any green result or displayed value, ask what it
> would look like if the thing were broken; if the answer is "identical," it
> verifies nothing, and the gap case must be exercised explicitly.** Fallbacks,
> windows, non-validating providers, all-modules-loaded test environments, and
> summary headlines are the recurring carriers: each degrades to a confident wrong
> answer instead of a visible gap, and well-formedness is exactly what lets it
> survive review.
> `Source: BL-029 (COALESCE label fallback, 596 runs); BL-038 (LIMIT window read
> as the whole store); BL-039 (stub-green fork e2e; fourteen empty-queue "successes");
> BL-029 batch r2→gate (a "CLOSED" headline over an unevidenced arm); BL-031 r2 §1c
> (suite green while boot crashes — test env structurally unlike the operator's);
> BL-040 (a deserialiser accepting a type the spec denies, silently); post-push
> 2026-07-21 (cross-repo claim verified against one repo).`

**Adjudication questions.**
1. This is arguably a *rewrite* of the harness CLAUDE.md's Vacuous-exercise rule
   under §7's too-vague test (that rule covers exercises; five of the eight faces
   were not exercises — they were displays, headlines, and pushes). Rewrite-and-
   replace, or new rule beside it with a cross-reference? Draft assumes rewrite.
2. Home repo: faces span both repos. Proposal: harness CLAUDE.md (where
   Vacuous-exercise lives), reachable from agents via P8(c).

**Mechanism sharpening riding with it (one clause appended to the existing
gate-before-action rule, not a new rule):**

> A cross-repo change needs a cross-repo done-check — any gate that runs in one
> repo silently passes omissions in the sibling (repo-scoped `git add -A` +
> single-repo drift check let a one-repo edit push under a two-repo claim).
> `Source: b1 post-push correction, 2026-07-21 (d831220)`

---

## Class 2 — the adjacent case and the load-bearing coincidence

**Proposed rule:**

> **A fix's blast radius is one case wider than the case it was written against —
> before shipping a fix or refactor, enumerate the adjacent cases that share its
> syntax but not its semantics, and name any coincidence the current behavior
> depends on: removing a coincidence that was doing real work is a regression that
> diff review structurally cannot see, because the break is in code the diff never
> touched.**
> `Source: BL-029 F9 (label≡run_id coincidence was the UI's only run_id display);
> BL-028 r2 F1 (map-valued results truthy past a nil guard); BL-031 r2 F18 (paused
> runs quiet-by-design inside an inactivity frame); BL-031 r2 §1c (a literal atom
> in sweep.ex was the sole reason event deserialisation worked at boot).`

**Adjudication questions.**
3. §1c's fix *rejected* the coincidence-restoring one-liner by citing this
   class-in-draft — evidence the wording steers correctly. But one rule carrying
   two imperatives (enumerate adjacents; name coincidences) risks the vagueness
   §7 punishes. Split into two rules, or keep unified on the shared mechanism
   ("the truth isn't where the diff is")? Draft keeps unified; flag if split
   preferred.
4. Home: harness CLAUDE.md proposed (three of four faces are harness-side), P8(c)
   reachable.

---

## Class 3 — the reviewer's sketch is not the finding

**Proposed rule:**

> **A finding binds by its invariant, not its sketch. The implementer verifies any
> suggested mechanism against the full writer/consumer family before adopting it —
> a reviewer's proposed fix is inference until the family is read, and this batch's
> four sketch failures (all the reviewer's) shared one mechanism: a word matched
> the vocabulary of the right family without belonging to it.** The invariant held
> all four times; the sketch failed all four times; implementing the invariant
> instead of the sketch produced the correct fix each time.
> `Source: BL-029 r1 F1 suggested-fix clause (--label inferred, --name true);
> BL-028 r2 F1 (third-||-arm under-covered the map shape); BL-031 r2 F18
> ("paused" status does not exist); BL-031 F23 correction (mode union ≠ event
> union).`

**Adjudication questions.**
5. This extends Cited-means-read (which binds authors and reviewers on *claims*)
   to *suggested fixes*. Append as a clause there, or stand alone? Standing alone
   proposed: the failure mode (implementer defers to reviewer authority) is
   distinct from the citation failure mode, and the audience clause differs — this
   one primarily licenses the implementer to push back.
6. All four instances are one author (claude-ui). §7's bar counts tickets, not
   authors, and the bar is cleared — but the single-author fact is itself worth a
   sentence in the committed wording, as calibration for future reviews. Included
   above; strike if judged self-referential noise.

---

## Recorded, not promoted (for the file, so nothing evaporates)

- **Complete-output, gate-side instance** (BL-031 §1f: `tail -3` destroyed a
  failure's identity): the promoted rule applied, no rewrite needed. First
  gate-capture casualty noted against it.
- **Batching heuristic** (b1: one half's compiler caught the other half's edge;
  same-artifact-boundary batching validated): one instance, below bar, watching.
- **The §1f flake**: one unattributed failure in twelve+ observed runs; escalation
  trigger on record (second unattributed full-suite failure → row + seed-preserving
  chase, timing-shaped tests first).
- **Copyability boundary** (b1 F12/tooltip): commands spelled fully where operators
  copy; shorthand acceptable in pointers. Convention recorded in bl-029-review.md;
  not rule-sized.

## Process notes for the ritual itself

- The batch ran §7 without a milestone doc; the scan inputs above are the
  precedent for what "the milestone's review files" means in backlog-batch mode —
  worth one line in methodology §7 if this mode recurs, not proposed as an edit
  now.
- Classes 1 and 2 each contain an instance where the *promoted-in-draft* wording
  steered a live decision before promotion (§1c's fix direction; F13's
  headline-vs-body diagnosis using class-1 language). The loop paid out early;
  recorded as evidence the wordings are actionable, which is §7's real test.
