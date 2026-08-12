# gc t4 — the close (implementation notes)

`Record of gc t4, run 2026-08-12. Round document: docs/milestones/gc-stale-claims.md §t4, which is
the authority. The per-clause assessment, the nine dispositions and the milestone summary are in
that document; this file carries what it cannot — the findings this close surfaced, the deviations,
and what is owed. §7's scan reads this file.`

---

## What the close found, and did not expect to

**§7's own instrument produced a false negative, and the finding that predicts it was sitting in
this round's inbox.** Step 4's prior-claims census over m5 was run first as an exact-string search
on the candidates' opening words. It reported **2 of 7 claims ABSENT**:

```
ABSENT?  "A check that structurally cannot observe the failure…"
ABSENT?  "An unpushed artifact may be corrected in place…"
```

Both were **present**. The first is at `../aetheris/CLAUDE.md:723` with the word *structurally*
dropped from its headline. The second is at `:956`, rewritten around *"An artifact's kind decides
how a correction is made; its push state decides only whether the correction may be silent"* — a
different sentence carrying the same rule, with the original phrasing surviving only in the entry's
body at `:981`. A substance search found both. **Census result: 7 of 7 present, nothing absent, no
census promotion owed**, with a fresh negative control (`flembic-not-a-promoted-rule`) at 0 in both
files.

**This is §Carried in item 4 — *§7's distillation can lose what the candidate got right* —
demonstrated on the close's own instrument, at the close that had to dispose it.** It is why item 4
was promoted rather than dropped, and the promoted entry carries the episode as its `Source:`.

**Two of the three carried-in items were promoted on demonstrations from inside this round rather
than on their inherited evidence.** Item 3 (controls spend on publication) fired twice on gc's own
instruments; item 4 fired once, above. Item 2 was promoted on its inherited measurement, which is
the only one of the three whose evidence is external to gc.

---

## Deviations, with reasons

**Four entries were promoted into harness `CLAUDE.md`, not one.** `Touches` names that file with the
parenthetical *"the one promotion"*, anticipating the arbiter's step-4 entry alone. Step 3 then
required §Carried in items 2–4 to be **promoted or dropped** under **R24**, and all three had
evidence — two of them demonstrated inside this round. Dropping a well-evidenced finding to keep a
count would have inverted the rule's purpose. **The file is in `Touches`; the count is not.** Named
here rather than absorbed.

**The home for items 2–4 is arguable and was decided by `Touches`.** The three concern round
records, negative controls and §7's distillation — the packet-and-record family, which this round
itself established (at t1 §0.1) lives **agents-side**. `Touches` names only the harness file, so
they landed there. Recorded as a question for the arbiter rather than resolved by me.

**The arbiter's promoted entry has no candidate to compare against.** §Close criteria clause 7, as
amended at Phase D, requires an entry promoted out of §Promotion candidates to be compared against
the candidate it came from. The arbiter's entry was ruled in directly from t1's and t3's committed
records — deliberately, because the finding is a population census rather than a ≥2-ticket
recurrence, which is the channel gap m5 recorded as open. So the comparison ran for the three step-3
promotions and **has no subject** for the fourth. Stated as a qualification on clause 7 rather than
counted as met.

**The document's §Close criteria assessment was written before the criteria in the first pass** and
reordered. Cosmetic; recorded because the packet shows the section list.

---

## What is owed

```
OWED  A review file for this ticket — docs/reviews/gc-t4-review.md. NOT claude-code's to author:
      methodology §10 assigns review files to claude-ui, saved verbatim by the human.
OWED  The push. Seven commits before this ticket, two more from it, across both repos, all held
      for the arbiter. Nothing else stands between the round and being pushed.
OPEN  BL-145 - BL-149 (t3's five) and BL-150 (the standing row). All open by construction.
OPEN  D6's write-back question. Answerable under R22 as of today; deliberately not answered —
      writing an interpretation back into another round's registry on the day it became
      permissible is the speed this round exists to slow down.
OPEN  Five §Promotion candidates, first carry. Under R24 they are promoted or dropped at the
      next close and cannot be carried a third time.
NOT OWED  Anything sequenced after this round. There is no t5 and no successor.
```

## Anchors

```
the ticket           docs/milestones/gc-stale-claims.md §t4
the assessment       docs/milestones/gc-stale-claims.md §Close criteria — the per-clause assessment
the dispositions     docs/milestones/gc-stale-claims.md §Dispositions
the summary          docs/milestones/gc-stale-claims.md §Milestone summary
§7's ritual          ../aetheris/docs/methodology/milestone-methodology.md:216-251
R22 / R23 / R24      docs/milestones/hc-consolidation.md
the four promotions  ../aetheris/CLAUDE.md:1095, :1111, :1126, :1139
```
