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
