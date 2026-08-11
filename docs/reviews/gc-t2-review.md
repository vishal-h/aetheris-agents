# gc t2 — review

`Findings on gc t2, the two pointer defects. Reviewed 2026-08-11 by claude-ui; authored per
methodology §10 and hc R2, saved verbatim. Round document: docs/milestones/gc-stale-claims.md §t2.
The ticket's own record is docs/milestones/gc-t2-implementation-notes.md.`

## Verdict

**Ratified, after two amendments made before the work committed.** Both pointers resolve to what
they claim; the pair landed harness-first and the mirror was verified byte-identical after the sync.

## Findings and dispositions

**F1 — The reverse pointer restated the rule it points at.** As first landed it carried a précis of
the entry it names, inside a file that is a mirrored pair — so an amendment to that entry would
leave a stale restatement in two places, and nothing would catch it: the mirror check compares the
copies to each other, never to their source. This is the round's own subject reproduced by the
round's own edit.
*Disposition: amended before commit, trimmed to the relation alone, with the rule left single-copy
where it lives. Carried to §Promotion candidates, not promoted.*

**F2 — The ticket corrected a document without applying the live/archival test.** t3's body requires
that discrimination per destination; t2's did not, and t2 had a destination of exactly the kind the
test exists for. The gap is in the reviewer's authoring — the test was written into one ticket and
not its sibling.
*Disposition: the test was run at the amendment and the document established archival on its own
evidence, which decided the correction's shape. Carried to §Promotion candidates, not promoted.*

**F3 — Five items raised for arbitration, all ruled.** Both edits made beyond the literal
instruction are ratified — flagging them where they landed rather than absorbing them is the
behaviour the loop wants. The three-commit split is ratified. The close criterion that presumed an
unreachable resolution shape is amended. The docbuilder parenthetical is trimmed. Decision 10's
"current equivalent" is ruled to mean operational content, at D6.

## What the reviewer got wrong

A decision authored at this review cited a finding this round did not carry — a claim about another
document's contents that did not hold, inside the round convened to correct claims about other
documents' contents that do not hold. Caught by the ticket, not by the reviewer. Repointed at Phase
C, and the missing inbound channel it exposed became §Carried in.
