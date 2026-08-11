# gc t2 — the two pointer defects (implementation notes)

`Record of gc t2, run 2026-08-11, reviewed and amended 2026-08-11 (Phase C). Written at Phase D,
after the round's records were found absent. Round document: docs/milestones/gc-stale-claims.md §t2.
The diffs are in the commits; this file carries the decisions, the deviations with their reasons, the
surprises, and what is owed.`

---

## What landed

Two pointers now resolve to what they claim. A cross-repo pair, harness-first per hc decision 6.

```
harness  b400b12       docs/methodology/triad-loop.md        reverse pointer -> methodology §11
agents   this commit   docs/triad-loop.md                    mirror sync, byte-identical
                       docbuilder/docs/m4-milestone.md       §9 citation corrected to §8
```

> `[The agents half names "this commit" rather than a SHA. It cannot cite its own, and an
> earlier draft cited the pre-amendment SHA, which the Phase D re-cut invalidated within the
> hour — a stale pointer inside the record of a round whose subject is stale pointers. The
> harness SHA is stable and is given; it was not re-cut.]`

---

## Decisions, with reasons

**The reverse pointer cites §11 by section and entry headline, never by ordinal.** The round prompt
and t1's packet both called it *"§11 entry 2"*. §11's entries are unnumbered bullets, and
`aetheris/CLAUDE.md:930–932` forbids an ordinal into an ordered list — *"'§7 step 4' is invalidated
by an insert above it exactly as a line number is… Name the step, not its position."* So the pointer
names *entry* **A surgical edit is scoped by unit and quoted before it is replaced**. An insert above
it in §11 leaves the pointer valid.

**The pointer does not restate the rule it points at.** As first landed it carried a précis of §11's
entry. That was wrong and was corrected at Phase C: `triad-loop.md` is a **mirrored pair**, so a
restatement goes stale in two files at once, and the mirror check compares the copies to each other
and never to their source — nothing in the toolchain would catch the drift. The block now carries
the relation and nothing else, and says so: *"The rule itself is stated there and is deliberately not
restated here."* Carried to §Promotion candidates as an entry.

**`docbuilder/docs/m4-milestone.md` is ARCHIVAL, so the correction carries a dated note (hc decision
7) rather than being silent (decision 8).** Established at Phase C, on three legs, none of them the
filename:

```
1  A current equivalent exists — docbuilder/runbook.md:530-582, `## m4 — freeform NL field
   extraction`, bounded by `## Common failure modes` at :583. It carries the fresh-path
   description, the sprint case (:553), the output files (:567) and the validate_fields.py
   failure mode (:574). That is where an operator goes.
2  Successors are in tree — docbuilder/docs/m5-milestone.md, m6-milestone.md,
   docbuilder/docs/milestones/m7-offer-letter.md.
3  Commit history agrees — m4-milestone.md last at 144726b (2026-06-25); the runbook last at
   3ab125c (2026-07-02). The equivalent has moved since the milestone doc stopped.
```

Leg 1 is what decision 10 actually asks for; legs 2 and 3 corroborate. **This test was not in t2's
ticket body** and was run only because Phase C required it — carried to §Promotion candidates.

---

## Deviations, with reasons

**t2's ticket body did not require the live/archival test, and t3's does.** The omission is in the
authoring, not the execution: t2 had a destination of exactly the kind t3's body discriminates over,
and nothing asked for the discrimination. Recorded as a §Promotion candidates entry rather than a
finding against the session.

**`docs/project-knowledge-manifest.md` is in t2's `Touches` conditionally and was not touched.** The
condition was *"only if the mirror-pair check's result is recorded there"*; the result is recorded
here and in the packet instead. The manifest's row commit column is an export-boundary concern and
was out of scope by the ticket's own text.

---

## Surprises

**The mirror-pair check is the only instrument that can see this class, and the manifest says so.**
`docs/project-knowledge-manifest.md:76–79` — *"`drift_check` cannot see that class; the `diff -q` is
the only thing that catches it."* Confirmed in practice: `drift_check --strict` passed on every run
of this ticket, before and after both edits, and never had an opinion about whether the copies agreed.

**`drift_check` reported its own vacuity, correctly, and then resolved it.** Pre-commit the
`project_knowledge` check said of `docs/methodology/triad-loop.md`: *"has uncommitted working-tree
changes — this check compares committed history, so its staleness reading for this path is vacuous;
re-run --strict after committing"*. Post-commit it read *"stale — manifest=265d336
current=b400b12"*. The WARN count did not move — a vacuous reading was replaced by a real one, not
joined by one.

---

## Verification

```
diff -q docs/triad-loop.md ../aetheris/docs/methodology/triad-loop.md   -> exit 0
sha256  1b9cbf57c6864cdaecc3a07c431d51d34ee69f1ebc6afc1a664d8e167ea46f8a  (both)
md5     e8ca65598cc6b3a5d86523e31406ba2b                                  (both)
wc -lc  199  9532  (both)
```

Trajectory across the round: **188 / 8802** at HEAD → **201 / 9876** after the first landing →
**199 / 9532** after the Phase C trim. The pair moved together at every step; at no point did the
copies differ.

Citation resolves: `../aetheris/docs/methodology/milestone-methodology.md:267` is inside §8 (`:255`)
and before §9 (`:275`).

Offline spine, unchanged by this ticket, three runs across the round: **386 passed, exit 0** each
time — the figure m5 pinned.

---

## What is owed

```
OWED  A review file for this ticket — docs/reviews/gc-t2-review.md or the round's equivalent.
      NOT claude-code's to author: methodology §10 assigns review files to claude-ui, saved
      verbatim by the human. hc's R2 requires every ticket in the round to commit one.
OWED  The post-export manifest re-pin for docs/methodology/triad-loop.md. The row now reads
      stale at manifest=265d336 / current=b400b12; that clears at the export boundary, which
      is the enforcement point, not here.
```

## Anchors

```
round document     docs/milestones/gc-stale-claims.md  §t2
canonical/mirror   docs/project-knowledge-manifest.md:53-55  (harness copy canonical)
mirror check       docs/project-knowledge-manifest.md:76-79  (drift_check is blind to this class)
landing order      docs/milestones/hc-consolidation.md:583  decision 6
correction shape   docs/milestones/hc-consolidation.md:584 decision 7, :585 decision 8, :587 decision 10
ordinal rule       aetheris/CLAUDE.md:930-932
```
