# Review — BL-022 — round 1

## Ownership, stated plainly

Eight items. **Six true, two false-premised. Both false ones were authored by the
reviewer**, from exported and planning documents rather than from source. Both were
caught by the ticket's own instruction — *"re-verify each against source; treat the
list as leads, not facts"* — before anything was written.

That instruction paid for the ticket twice over. Without it, item 6 would have added
a false footnote to a correct table.

## Item-by-item verification

| # | Claim | Verdict |
|---|---|---|
| 1 | Doc lists 12 event types; union has 22 | **TRUE** — regenerated from the union |
| 2 | Doc says two places; "rule 14 is three" | **premise FALSE, conclusion right** |
| 3 | `receive_timeout` "Fixed" claim over-broad | **rewrite correct** — accurate but under-specified |
| 4 | Adapter tree omits `openrouter.ex` | **TRUE** — and worse than stated |
| 5 | No sweep anywhere | **TRUE** — `grep -ci sweep` = 0 |
| 6 | Fork listed as shipped; `fork_run` unbuilt | **FALSE** — acting would have corrupted the doc |
| 7 | Shows `meta.json` as a separate file | **TRUE** — verified on disk |
| 8 | Add header + manifest row | valid |

## The two reviewer errors

**Item 6 — `Cited-means-read` violation, reviewer side.** "`Aetheris.fork_run` is
BL-007, unbuilt" was written from the backlog's BL-007 scope sketch and the roadmap —
*planning* documents — and asserted as code state. `lib/aetheris.ex` was never opened.
`fork_run/3` has existed since 2026-05-17 with `Fork.from_step/3`, a CLI command,
tests in two files, and `:fork` first-class in `run_config.ex:115`. The failure mode is
inverted from the ticket's premise: not a stale doc, a stale reviewer. Planning
documents are the most seductive source precisely because they describe intent, and
intent reads like fact.

**Item 2 — the same class, smaller.** "Rule 14 is three" came from BL-003's review
discussion ("the three places span two repos"), not from rule 14's text, which said
*two*. The conclusion — "following the doc produces a drift FAIL" — was accidentally
right, because the *enforced* reality (`drift_check` `_fail`s on a type missing from
specs §6) is three even though the *written* rule was two. Architecture.md faithfully
mirrored rule 14's understatement. Both are now corrected.

## What the verification found beyond the eight

- **The repo tree is stale well past item 4.** The one-omission-suggests-others
  instruction was right: 7 of 9 tools and 6 execution modules were missing, including
  `fork.ex` — whose absence from the tree is quietly consistent with item 6's error.
- **BL-007's scope sketch is itself stale.** Its harness half is built, *including* the
  provenance back-link (`fork_from`/`fork_step`, persisted into trajectory `meta` by
  `maybe_add_fork_meta`). Only the Rig side is verified absent. Annotated, not
  re-scoped — that is the planning session's job. The milestone is now provenance +
  determinism contract + Rig UX on top of an existing core.
- **One more of my own.** In first reporting BL-007's state I wrote "no
  parent/forked_from in fork.ex" from a grep using the wrong field name (`forked_from`,
  not `fork_from`) truncated at `head -5`. The back-link was there at `fork.ex:119`.
  A `Cited-means-read` slip committed *while documenting that rule* — corrected before
  it reached the annotation, but worth recording: the rule binds its author in the act
  of writing it.

## Cross-ticket note

Third consecutive ticket where verify-before-implement caught a false premise
(BL-021's `:retry` claim, BL-022's items 2 and 6). The pattern across all three is
identical: **a claim derived from a document about code, rather than from the code.**
The documents differed — a sibling adapter, a review discussion, a scope sketch — the
mechanism did not. `Cited-means-read` now carries all four instances and names both
sides it binds.
