# gc t1 — review

`Findings on gc t1, the gate-claim census. Reviewed 2026-08-11 by claude-ui; authored per
methodology §10 and hc R2, saved verbatim. Round document: docs/milestones/gc-stale-claims.md. The
ticket's own record is docs/milestones/gc-t1-implementation-notes.md; this file carries the findings
and their dispositions, not a second copy of either.`

## Verdict

**Ratified.** The census is an enumeration and not an observation. Its class list and description
tokens are inlined and re-runnable — established at Phase D by re-running them as printed, every
per-class and per-token count reproducing with no repair. Three method defects were found by the
ticket's own controls and recorded rather than patched over. The description-form pass earned its
cost: it reached the one claim naming both its gate components with no id on the line, which the
id-form sweep is structurally blind to.

## Findings and dispositions

**F1 — The subset check caught a defect the census would otherwise have shipped.** The first pattern
forbade the gate relation from crossing a sentence boundary and suppressed a fifth of the class;
four of the five known instances passed under it and one did not. Diagnosed to its cause, fixed, and
the delta published.
*Disposition: accepted, and not a send-back.* The reviewer had named a miss on any of the five as
the one result that would return t1. The miss occurred and the ticket caught it in-session,
diagnosed rather than patched. That is the check working, not failing.

**F2 — The control set that caught F1 was sized to what a prior packet happened to name.** Five
instances is not a size derived from the method's error rate, and it caught a defect suppressing a
fifth of the class.
*Disposition: carried to §Promotion candidates. Not promoted — one instance, and this round has no
second census to test the claim against.*

**F3 — Six items were raised for arbitration and all six are ruled.** The round id and subject; the
R12 authorship deviation; the live/archival status of the preceding round's consolidation document;
what the round corrects versus defers to a row; the unstamped contracts' silence; and the deferred
dialyzer trigger.
*Disposition: §Decisions D1–D5 and the naming ruling, authored at this review; D6 follows at Phase D
on a question t2 surfaced.*

## What the reviewer got wrong, recorded here rather than only in the round

The round prompt that opened this arc asserted the gate was live. It had closed four days earlier.
The error was carried from the reviewer's own scoping into the first cc:prompt and was caught only
because the ticket was instructed to resolve every pointer before acting on it. The instruction that
saved it was standing practice, not the reviewer's scoping.

## Dated addendum

`[Appended 2026-08-11 at Phase D. Two things later phases established about t1, recorded here
because a review file that does not carry them leaves the verdict resting on unconfirmed ground.
(1) §Close criteria clause 1 — re-runnable as printed — is established rather than assumed: every
pattern and token ran unaltered and every count reproduced. (2) t1's three negative controls now
return non-zero, the hit in each being the document that published them. That is the carried-in
entry on control decay firing on its own instruments one round after it was written, and it is a
confirmed prediction rather than a defect in t1.]`
