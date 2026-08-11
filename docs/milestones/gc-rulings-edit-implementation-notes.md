# gc — the rulings edit (implementation notes)

`Committed record of the reviewer-authored section-scoped edits to
docs/milestones/gc-stale-claims.md, per R20 (hc-consolidation.md:528-538): a reviewer-authored
section-scoped edit is not a ticket round and gets no review file; this file is its committed record.
Landed across the t1 review (Phase A), the t2 review (Phase C) and Phase D.`

**This file points at the round document; it does not restate it.** What was ruled is in
`docs/milestones/gc-stale-claims.md` §Decisions, §Close criteria, §Carried in, §Promotion candidates
and §t3. Copying any of it here would be the defect C.5a existed to fix, one level over — a second
copy that goes stale when the first is amended, with nothing comparing them. What this record carries
is what the document cannot: **who ruled, when, on what evidence, and what the rulings changed
about the round.**

---

## What landed, and where to read it

```
D1   dialyzer runs at this round's close        gc-stale-claims.md §Decisions
D2   m4-consolidation is archival               gc-stale-claims.md §Decisions
D3   the R12 deviation, narrowed, one-off       gc-stale-claims.md §Decisions
D4   what t3 corrects, what it defers to rows   gc-stale-claims.md §Decisions
D5   a stamp's absence is not a verdict         gc-stale-claims.md §Decisions
D6   decision 10's "current equivalent"         gc-stale-claims.md §Decisions
—    seven close criteria                       gc-stale-claims.md §Close criteria
—    four inherited items                       gc-stale-claims.md §Carried in
—    five promotion candidates                  gc-stale-claims.md §Promotion candidates
—    t3's body, Touches unblocked               gc-stale-claims.md §t3
—    rename gc-census.md -> gc-stale-claims.md  gc-stale-claims.md §Naming derivation
```

---

## Provenance, phase by phase

```
Phase A  t1 review     §Decisions D1-D5 created; §Close criteria authored; t3's body authored,
                       Touches unblocked; §Promotion candidates created (3 entries); rename,
                       id `gc` ratified as minted, subject re-ruled census -> stale-claims.
Phase C  t2 review     §Carried in created (4 items); D5 repointed; §Close criteria clause 3
                       replaced; §Promotion candidates +2 entries (5).
Phase D  t2 review     D6 appended; §Close criteria clause 7 replaced.
```

Authoring is the reviewer's per R12 and decision 11; claude-code formatted into §6 anatomy and
supplied every checkable specific, per the reviewer's standing rule that authored specs assert none.

---

## The three amendments that were corrections, not additions

Recorded because each was a reviewer error caught by the verification pass, and because the pattern —
a ruling whose internal pointer or presumed shape does not hold — is the round's own subject.

**D5's pointer named a section that did not carry the finding.** It read *"This round's own
§Promotion candidates carries the measurement finding…"*; §Promotion candidates held three entries,
none of them the measurement. The finding is m5's, at `cloudcost/m5-n1-compose.md:1188–1199`.
Repointed at §Carried in item 2 — which is also why §Carried in was created: the round had no
inbound channel for what m5 hands forward, so D5's referent had nowhere to live. **Corrected in
place** rather than superseded: the document is live and the edit pre-dated any reader of D5.

**§Close criteria clause 3 presumed a shape a closed round does not admit.** It required m5 §Not
established item 1 be *"resolved"*. m5 closed 2026-08-10; hc decision 7 governs a closed record — a
dated superseding note, original text not rewritten — so that item's `[OPEN]` prefix cannot be
flipped the way this round's own was. Replaced with a clause requiring a dated record that the gate
is discharged, leaving the shape to t3.

**§Close criteria clause 7 did not carry the obligation §Carried in item 4 imports.** Item 4 binds
the close — a promoted entry is compared against the candidate it came from — and no clause or ticket
carried it, so it would have been discovered at the close or not at all. Clause 7 now states it.

---

## Two edits made beyond the literal instruction, named rather than folded in

Both are consequences of rulings rather than new content; neither was instructed.

**§Not established item 1 flipped `[OPEN]` → `[RESOLVED]`.** D1 answers it, and leaving it open
beside a decision that settles it would be a contradiction inside one document. Original text left
unrewritten per decision 7, with a dated resolution block naming D1. Shape taken from
`cloudcost/m5-n1-compose.md:869–889`, the in-repo precedent for resolving an item of this kind in
place.

**A dated bracket under the R12 deviation note, pointing at D3**, plus two rows added to §Round rules
in force (decisions 7 and 10, which the round came to rely on and had not listed). The original note
is byte-unchanged.

---

## What is owed

```
OWED  Nothing from this edit. R20 states this file is its committed record and gets no review
      file; the reviewer's findings on it land here, appended as a dated `## Review` section.
OPEN  Whether D6's interpretation should be written back into hc-consolidation.md as an
      amendment to decision 10. D6 reserves it for the round's close and this record does not
      settle it.
OPEN  Whether `operational content` is the right general name for decision 10's test or merely
      its usual carrier. Same reservation.
```

## Anchors

```
the document        docs/milestones/gc-stale-claims.md
R20 (this record)   docs/milestones/hc-consolidation.md:528-538
R12 / decision 11   docs/milestones/hc-consolidation.md:335-347, :588
decision 7 / 8 / 10 docs/milestones/hc-consolidation.md:584, :585, :587
carried-in source   cloudcost/m5-n1-compose.md:1035-1227
resolve-in-place    cloudcost/m5-n1-compose.md:869-889
```
