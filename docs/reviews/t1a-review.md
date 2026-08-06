# t1a review — correct the false `2>&1` causal claim in every standing carrier

**Reviewer:** claude-ui · **Author:** claude-code · **Closed:** 2026-08-06, round 4, zero blocking.
**Final tree:** `aetheris-agents@157e986+` / `aetheris@e6687f1`.

Four review rounds. Full packet with done-check output, both diffs, the census and every
disposition is the session artifact `t1a-review-packet.md`; this file is the review record.

## Arc

| Round | Raised | Outcome |
|---|---|---|
| 1 | 3 blocking, 6 non-blocking, 1 question | F1 (packet §2b duplicated §2a) fixed by regeneration; rest carried |
| 2 | 2 blocking (N1 gate provenance, N2 BL-105 overclaim), 3 non-blocking | all closed; F2 found to span 4 documents, not 1 |
| 3 | F10 re-opened on its reasoning; 2 texts owed | F10 reconciled — documented term set ≠ executed term set |
| 4 | 0 blocking; 2 precision edits at merge | applied; ticket closed |

## What the ticket established

- The harness's **Logger output shares stdout** with the `--json` payload, so `2>&1` is not
  why the sprint's reads fail. Demonstrated by stream split, not inferred.
- The reads are **unpredictable rather than uniformly broken** — news captures parse 4/4,
  payslip 0/8, cloudcost 0/10, same helper and redirect.
- The causes are **at least three and not interchangeable**: resume-failure lines are
  store-state dependent; the orphan-sweep line is config-gated and did not exist before
  2026-07-15 (`0188a90`); `[sandbox]` routing is unestablished.
- Worker output (`aetheris_worker fatal`) is on **stderr** (`eprintln!`), which makes the
  harness fix and stream splitting **complementary, not alternative**, and links BL-105 to
  BL-099's D2 grep.

## Rows filed

BL-105 (`--json` payload shares stdout) · BL-106 (no JSON document on a non-success run) ·
BL-107 (chaos gate has never evaluated its subject) · BL-108 (eduloka sink gate) ·
BL-109 (two `milestone-reference.md` files). BL-100 rescoped, **not closed** — the fix has
not landed.

## Carried into t1b

1. Assert-versus-retract census classification — this ticket seeded the corpus with
   retractions that a term-match census will mis-flag as carriers.
2. The multiple-payload question — the backward scan takes the *last* parsing JSON object;
   0 of 50 captures carry more than one, and nothing in the contract excludes it.
3. Cwd-independent commands in every gate and census (`git -C` or absolute paths).
4. G1 states both forms: level-with-origin pre-implementation, ahead-by-N-unpushed after.

## Promotion candidates (§7)

- *Search the claim's substance, not a token* — with its own hazard attached (item 1 above).
- *A disposition commit travels as a claim about its content, not as content.* Mechanical
  closures stay grep-settleable; anything that authored a mechanism gets quoted.
- *A check caught because its output was implausible is not a check.* The corrupted G4
  survived only until someone noticed a phrase cannot be in two files at once; a cwd defect
  yielding a plausible result would have passed.

## The reviewer's closing observation, recorded because it is the point

> Four instances of this ticket's own class, inside the ticket. A packet section that did not
> travel; a mechanism claim past its evidence, twice; a method record describing a search that
> did not run. None was carelessness — each was found and each was disclosed. That is the
> argument for the promotion wording being about *shape* rather than about any one artifact:
> claims that outrun what the claimant could check are this project's dominant defect mode,
> and they recur most in the documents written to correct them.
