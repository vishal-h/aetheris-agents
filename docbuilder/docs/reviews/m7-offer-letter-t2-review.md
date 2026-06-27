# Review — m7 t2 — round 1

Reviewer: claude-ui
Subject: offer_letter bundle spec + logo, PDF primary (commit `abb96bb`)

> Filed at `docbuilder/docs/reviews/` (m7 convention, settled in t1 round-2).

---

## Findings

**1. [non-blocking] Record the done-check correction in the milestone doc's §t2 block now, not
"carry to t4".** The doc is the canonical done-check (§1.1); if someone re-runs §t2 before t4
lands they hit the `for e in cat` iteration error. Fix the `python3 -c "..."` block to use
`cat["doc_types"]`. Disposition: fix in the t4 commit at the latest (one-line doc correction,
no re-review for that change alone).

**2. [non-blocking] The JPEG-content / `.png`-name note belongs in the milestone doc (Design
decisions / bundle-assets), not only the implementation notes** — so a future reader who adds a
logo or wonders why a `.png` is JPEG finds it. One sentence; deferrable to t4.

## Cross-ticket notes

The end-to-end PDF render as a t2 de-risk is the right application of the m6 learning — t3's
failure surface is now narrowed to sprint wiring, not logo resolution. The catalogue-structure
correction (`cat["doc_types"]`) is the same class as the m6 t4b `compute_doc --template`
positional fix — flag as a t4 learning-promotion candidate if it recurs in t3 (done-check
written against an assumed structure, not a verified one).

t2 is clean. Both non-blocking items are doc-polish. Ready to merge.

---

## Resolution (actioned now, not deferred)

Both items fixed in this round (trivial doc edits; fixing now > deferring, per the reviewer's
own §1.1 argument — and "no re-review needed for that change alone"):

- **F1 — done.** Corrected the §t2 Done-check block in `m7-offer-letter.md`:
  `for e in cat` → `for e in cat['doc_types']`. The doc's canonical check now runs clean.
- **F2 — done.** Added **D8** to the Design-decisions table: `btl_logo-withtext.png` is JPEG
  content with a `.png` name (bundle convention; WeasyPrint sniffs content; don't "fix" the
  extension). The t2 implementation notes point to D8.

**Carried to t4 (learning-promotion candidate, per the cross-ticket note):** if t3 also ships a
done-check command written against an assumed (unverified) structure, promote a CLAUDE.md
learning — "done-check commands must be run against the real data shape, not an assumed one"
(t2 `cat["doc_types"]`, m6 t4b `compute_doc` positional, m5 t1 smoke `--spec`/filenames are the
prior instances).

**Disposition: t2 fully closed.** No bundle/spec/catalogue code change in this round (doc + notes
only); the t2 deliverables stand at `abb96bb`.
