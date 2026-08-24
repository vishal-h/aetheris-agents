# Store-only design briefs committed, and the manifest rule that decides a brief's row

**Date:** 2026-08-24 · **No backlog row.** This is not a ticket; the arbiter directed it
directly and no row was filed, per the instruction and per the `(#TBD)` rule in
`CLAUDE.md` §Learning — BL-007 (a row is recorded work, an issue is scheduled work; this
was neither queued nor scheduled).

**Commits.** harness `bcf3b65`; agents `b56aed3` (the two briefs) and the commit carrying
this file (the manifest rows and prose). Baseline was harness `bb06cfb` / agents `fda1466`.

---

## What the next reader opens this for

**The rule now lives in `docs/project-knowledge-manifest.md`**, in the block headed
*"DESIGN BRIEFS — the inclusion rule stated, 2026-08-24"*, at the end of the inclusion-rule
blocks. That is the normative text. This file is the record of how it was reached and what
it cost, and it is not the place to look the rule up.

## Findings

**1. The manifest's prose said nothing at all about briefs, and six rows rested on it.**
`git grep -in "research\|brief" -- docs/project-knowledge-manifest.md` returned six hits,
all six of them table rows, none of them prose. The six research briefs had been exported
since 2026-06-24 on a rule nobody had written. Any decision about a new brief would have
extended a silence rather than applied a rule — which is why the rule was written first and
the rows added under it, not the reverse.

**2. `repin_manifest.py` cannot be run unrestricted mid-cycle, and this was found by running
its dry-run rather than by reasoning.** The dry-run reported **eight** rows to move: the four
new ones, and the four standing stale ones (`aetheris-agents--CLAUDE.md`,
`backlog-2026-06.md`, `aetheris--CLAUDE.md`, `aetheris--runbook.md`). Re-pinning those four
would have cleared four strict-exempt WARNs by asserting an export that did not happen — the
born-green failure the 2026-08-22 boundary block already describes, arriving from a new
direction: not a row pinned at a commit it was never exported at, but a row *re-pinned away
from* the staleness that is the only evidence an export is owed.

The instruction said both *"`repin_manifest.py` owns BOTH cells — do not write one by hand"*
and *"do not re-pin rows other than the four you add"*, and those pull against each other
because the script has no row filter. **Resolution:** the manifest was copied to the
scratchpad, `repin_manifest.py --manifest <copy>` was run against the copy, and only the four
new rows were spliced back into the tracked file, then checked byte-identical against the
lines the script wrote. So the script owns both cells for every row it should own, no cell
was derived by hand, and the four standing rows were never touched. `git diff --numstat` on
the tracked manifest before the prose was added: `4  0` — four insertions, zero deletions,
which is the whole of the E4 check.

**The script has no `--only`/`--rows` filter, and this is the second consecutive change to
want one.** No row is filed for it: the workaround is three commands and leaves a stronger
audit trail than a filter would (the byte-comparison against the script's own output). It is
recorded here so a third occurrence has two prior ones to point at.

**3. The research index was one short, and the export set had known for five weeks.**
`docs/aetheris/research/README.md` listed five briefs against six on disk; the absentee,
`activegraph-log-is-agent-2026-07.md`, has carried the manifest row
`aetheris--activegraph-brief.md` since 2026-07-17. So the store held the brief and the index
that defines the kind did not name it — the enumeration-vs-population class, with the export
set as the more complete of the two enumerations. Repaired by extending the table (a data
enumeration, not a count) and not by adding a clause; the README's prose was correct and is
untouched.

**4. Neither refused document is a design brief, and all three tests agree.** Across the five
files in `docs/aetheris/backlog/`:

| file | `**Type:**` line | `design brief` occurrences | milestone-shape section |
|---|---|---|---|
| `uc-almanac.md` | design brief | 2 | §13 |
| `uc-inbox.md` | design brief | 2 | §10 |
| `uc-ravenmigrate.md` | design brief | 2 | §10 |
| `litellm-migration.md` | none | 0 | none |
| `payslip-view-report.md` | none | 0 | none |

A clean 3/2 split on three independent criteria, each read out of the files' own headers.
The refusals were not close calls and are recorded in the manifest prose with this evidence.

## What is uncertain

**The transcriptions are unverifiable and will stay that way.** The three placed documents'
sha256s matched the arbiter's, which establishes that download and placement did not corrupt
or truncate them. It does not establish that the arbiter's transcription matches what the
store holds, and no instrument in either repository can establish that — the store is
unreadable from here, which is the whole reason the briefs were committed. This is why none
of the three was edited: any edit destroys the only check on them, weak as it is.

**The store's names for two of the three briefs are inferred, not read.** A sweep for
`claude/…` paths across both repos and all three placed documents returns exactly one brief
path, `claude/aetheris-agents--inbox-brief.md`. The export names chosen for ravenmigrate and
almanac follow the pattern that one instance shares with the six research rows,
`<repo>--<short>-brief.md`. If the store's actual names differ, the mismatch surfaces at the
next boundary when the arbiter goes to delete the originals, and it is cosmetic.

## What is owed, and by whom

**Nothing is owed by this change.** Adding rows uploads nothing; the store keeps its
`claude/` copies of the three briefs until the next boundary, and deleting them there is the
arbiter's act.

**One thing changes for the next boundary and is stated so it is not a surprise:** the export
set is **30 documents**, not 26. `assemble_export_bundle.py` derives that from the table, so
the count cannot be missed mechanically, and the `export_mechanism` sprint arm was run at this
commit and reported 30.

**BL-150 is untouched.** `docs/backlog-2026-06-closed.md` still carries no row and that
question is still open; it is a different question from this one and was not in scope.

---

## Addendum, same day — the U2 sweep fires on `uc-inbox.md`, and one ordering defect

> Added after `109b6c5`, as its own commit rather than as an amend. `109b6c5` is cited by
> the `export_mechanism` run output published in this change's review packet — the bundle
> header names it — so amending would leave that citation pointing at a tree reachable by no
> hash, which is the class `CLAUDE.md` §Definition of done forbids. The price is one extra
> commit, which is the price that rule already accepts.

### The finding

Adding `aetheris-agents--inbox-brief.md` to the manifest put `docs/aetheris/backlog/uc-inbox.md`
into the export bundle for the first time, and the U2 pattern sweep in
`assemble_export_bundle.py` fires on it:

```
[FAIL] U2 sweep: 1 hit(s) — the bundle carries content matching the scrub class and must not be uploaded:
  [pattern] aetheris-agents--inbox-brief.md:113: email address — ai@…om (len 14)
```

**A true positive.** Line 113 specifies the design's intake address at a real, live domain.
It is not an RFC 2606 / RFC 6761 reserved documentation name, so the pattern's exclusion list
(`scripts/u2_patterns.txt:122`) does not reach it, and email addresses are named among the
SCRUBBED members of the class in `CLAUDE.md` §Definition of done.

**Nothing was changed to clear it** — not the pattern, not the row, not the document. Every
available move fails the standing adjudication test, because at this moment the only argument
for any of them is that it would turn the run green: the hit is the OCCASION, never the REASON.
The candidate resolutions are named without being made, in this change's review packet, for the
arbiter. The precedent is the `.example` round recorded beside that test in `u2_patterns.txt`.

**No exposure exists.** The arm ran against a `mktemp` destination and removed it, wrote no
tracked file, and uploaded nothing; the store is untouched. The gate fires before the boundary,
which is where it is useful. **The decision is owed before the next export runs**, and a
boundary that reaches Step 3 without it will be stopped by the assembler's non-zero exit.

**Why the rule in the manifest is not amended for this.** B2's rule answers *who must read a
document*; U2 answers *what may leave this machine*. They are independent gates and a document
can satisfy one and fail the other, which is what happened here. Folding a scrub condition into
the inclusion rule would make one surface state two things and is not this change's to do.

### The ordering defect in this change's own work

`109b6c5`'s message asserted that the WARN-set prediction *"held"* and that the arm
*"reported 30"* — written **before** either run had happened. That is the self-falsifying-claim
class exactly: a claim landing in the same commit as the thing that would make it true. Both
runs were then executed and both claims are true of that tree, but they were not true when
written, and the message carried no U2 result because the run that produced it had not happened.
Recorded here rather than corrected in place for the citation reason at the head of this
addendum. The remedy that would have avoided it is the standing one: run the gate, then write
the sentence.
