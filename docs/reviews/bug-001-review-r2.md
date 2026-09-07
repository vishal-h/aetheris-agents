# Review — bug-001 — round 3

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bug001r3reviewpacket.md` · Tree: `87a4c30` + r1–r3, uncommitted

**Verdict:** findings 5 and 6 closed. Two new, both small; finding 7 is the ticket's own closing obligation and is what stands between this round and a commit. The ROUND TYPE question is answered below.

---

## Findings

### 7. [blocking] bug-001 has no backlog row, so its one outstanding obligation has no executor

Three rows now stand in the working tree — BL-190, BL-191, BL-192 — every one of them for a finding discovered *beside* this ticket. The defect the ticket exists for has none. `grep "^### BUG-" docs/` returns nothing; `grep "^### BL-19"` returns only the three incidentals.

That is survivable while the ticket is open, because the review files and implementation notes carry it. It stops being survivable at commit, because one obligation outlives the ticket and currently lives only in prose:

> *The timeout hypothesis closes only on the next live September upload.*

Restated in every round's §Owed, correctly excluded from each round's scope, and pointing at nothing that will still be read in three weeks. When the September upload runs, the person watching it needs to know that a specific prediction — 108 → 36 uploads, and a step that no longer exceeds 300s — is being tested. `drive/docs/bug-001-implementation-notes.md` is not where anyone looks before a payroll run.

This is the rule the round applied twice, turned on the ticket itself: *prose in a packet or notes files nothing.* The rounds filed rows for other people's defects and left their own open item unfiled.

It is also the row that makes the `BUG-` convention real. The convention was proposed, the ticket was named `bug-001`, the review files are `bug-001-review*.md` — and no `BUG-` row exists to anchor any of it.

**Suggested fix:** file `BUG-001` in this round's diff, status **fixed** (not `verified`), with:
- the root cause and the fix, briefly — the RCA detail is in the notes and reviews, and the row should reference rather than restate;
- **Done-when: the next live upload for a month with prior months in `payslip/output/` completes inside the step timeout, and the destination period folder contains only that month's files.** That is the `verified` transition;
- the measured 108 → 36 as the prediction under test, with the caveat both rounds stated — the count is measured, the causal claim is not;
- the partial-Drive-state note: the 2026-08 upload died mid-run, so the folder holds an unknown subset, and BL-191's cleanup is not this row's.

### 8. [non-blocking] The BL-191 evidence block's `Source:` span has nested backticks

§7's block closes with:

```
`Source: reported by the reviewer at `docs/reviews/bug-001-review-r1.md` §Commended; …`
```

The inner pair terminates the outer code span, so the line renders broken. The file's own convention writes paths bare inside a `Source:` span — e.g. `` `Source: m2-cloudcost t3, 2026-08-02 (aetheris-agents cbf3fbf). Verified by reading compose_report_data.py:711/:334/:342 …` `` — precisely because nesting is not available there.

**Suggested fix:** drop the inner backticks. Cosmetic, but it is in a committed artifact and the row is one someone will read under pressure.

---

## Round-2 findings — closure confirmed

| # | disposition | accepted |
|---|---|---|
| 5 | deferred (BL-192) | yes — and see below |
| 6 | fixed | yes |

**BL-192's two precisions correct my finding, not just execute it.** Finding 5 leaned on round 2's framing of the defect. The row establishes two things neither of us had run:

- **The exit code is 1 either way.** An uncaught `ValueError` and a clean rejection are indistinguishable to a caller checking `$?`. So the defect is the *shape* of stderr — an interpreter frame from `_strptime.py` where an operator needs a statement about their input — and a reader told "it crashes instead of exiting 1" would go looking for a wrong exit code and find none. That is a materially different row from the one my finding implied.
- **The blast radius is a bad message, not data movement.** `find_pdf` builds a literal path and tests `.exists()`, so `email_send.py` never treats the month as a glob — the property that made the same input serious in `drive_upload.py` does not exist here. And `:220` precedes the send loop at `:225`, so a malformed month sends nothing.

Sizing the row S/low on that basis is right, and the Not-done-when clause — *converging the two scripts means bringing `email_send.py` up, never bringing `drive_upload.py` down* — closes the failure mode where a later reader "harmonises" them by deleting the validation this ticket added. That clause is the row's most valuable sentence.

**The BL-191 evidence block is correctly scoped.** It settles the *class* and explicitly does not settle the row's open question, on the accurate ground that the observed failure was the email orchestrator and not `sprint.sh`. Carrying it as reported evidence with a named holder — rather than as something the session verified — is the right handling for a fact that cannot be reproduced without re-blocking a send.

---

## The ROUND TYPE question — answered

Declare it **code**. The determinant is *did a tracked source file change*, not *did an executable statement change*.

Three reasons, in order of weight:

1. **The boundary you proposed requires judgment; mine requires a grep.** "No executable statement changed" is a claim a reviewer has to re-verify. "A `.py` file is in the diff" is checkable without reading the diff, and a round type that can be confirmed mechanically is worth more than one that is more precise in principle.
2. **Finding 6 is the counterexample to its own premise.** A docstring made a false claim about a mechanism, and a reader acting on it would have been wrong about what protects the test. If a docstring can carry a defect worth a review finding, a docstring edit is not prose.
3. **The failure modes are asymmetric.** Over-declaring costs one done-check run that was going to pass. Under-declaring creates a category where source files change under documentation-round expectations — and the first thing to slip through it will not be a docstring.

The round was right to raise it rather than decide it silently, and right that a declaration exists so the reviewer can decline a shape they did not expect. Use `code` from here.

---

## Dispositions requested

| # | Expected |
|---|---|
| 7 | fixed — `BUG-001` filed in this round's diff |
| 8 | fixed — inner backticks dropped |

Both settleable by reading the diff. **This should be the last round.** After it: commit, then the owed post-commit `drift_check --strict` with the two-member WARN set.

## Owed after commit

- Post-commit `drift_check.py --strict`; expected WARN set `CLAUDE.md` and `docs/backlog-2026-06.md`. Finding 7's row adds no member.
- The September live upload, which finding 7 gives an address.
