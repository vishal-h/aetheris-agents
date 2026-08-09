# hc-d — implementation notes

**Ticket.** `docs/milestones/hc-consolidation.md` §Ticket set → hc-d. **Repos.** agents `eee5fed`,
harness `1b09b23`. **Date.** 2026-08-09.

**Outcome: the opening edit landed; the ticket stopped at the step-1 gate, which is unauthored.**
No contract work was done. That is the correct outcome, not a setback.

---

## 1. D1 — the R12 narrowing was offered conditionally, and its premise fails

D1 gave reviewer-authored narrowing text to be written **only if** hc-b2's scope was recorded
verbatim in a committed repo artifact **before hc-b2 opened**. It was not, so the narrowing is not
written and item 7 stays open.

**Method and result.** hc-b2 opened and closed at agents `6c61393`; the tree immediately before it
is `a581a8c`. (1) The only `hc-*` review file at `a581a8c` is `docs/reviews/hc-b-review.md`.
(2) `docs/reviews/hc-b2-review.md` was **first added by `6c61393` itself**. (3) Six wordings of
hc-b2's findings over the **entire committed tree** at `a581a8c`: *"exactly two slots"*,
*"inconclusive"*, *"two invocations"*, *"the gate's home"*, *"Finding B"* → **0 files**;
*"stub-provider run with a worker"* → **1**, which is hc-b's own gate text, the premise hc-b2
refuted rather than hc-b2's finding. (*"placeholder"* matches 115 unrelated files — not a
discriminator, and recorded so the term list is not read as five clean hits plus one.) (4)
`hc-b-review.md` §Round 1 at `a581a8c` is about the decision-count split and clause 2.

**The structural reason matters more than the instance.** The narrowing's premise was that R2
supplies a pre-dating artifact. **R2 requires a review file to be *committed*, not to *pre-date* the
ticket** — and a ticket's own review file is committed **by** that ticket. So this process does not
currently produce the condition the narrowing needs, for hc-b2 or for any repair ticket. Writing the
narrowing would have installed a rule over a condition that is never met.

---

## 2. D3 — answered by running it (R-i), and it falsifies an hc-c claim

**The suites were green before hc-c.** Harness checked out at `b4d782a` (the commit before hc-c's
`e8889c3`), detached, with a positive control confirming the fix was absent
(`route_logging_to_stderr` 0 occurrences, the `:json` error clause 0). Five suites: **41 passed** —
the same 41 that pass after. Restored to `main`, control run in reverse (3 and 1).

**So D3's second horn is the true one, and the mechanism it demanded is this.** hc-c r2 enumerated
stdout reads **per file**. Per **invocation** — the unit the question is actually about — the five
files make **17** `subprocess.run` calls: **7 spawn the harness** (`["mix","run","--eval",…]`) and
**10 spawn a Python CLI** (`[sys.executable, SCRIPT]`). **All four `json.loads(result.stdout.strip())`
parses belong to the Python CLIs.** No harness invocation in those files reads stdout at all; the
seven read `returncode` and `stderr`.

**hc-c's *"the change helps them"* is therefore wrong.** They are **unaffected**. F8's conclusion —
no broken consumer — stands; only its rationale falls. Corrected in all three documents that
adopted it (`hc-consolidation.md` item 6, `hc-c-implementation-notes.md` §8c,
`hc-c-review.md` §Round 2), each as a dated note beside the original rather than a rewrite, per
decision 7.

**The error's class:** a census keyed on the wrong unit. Two subprocess families share a file, and
counting by file merged them — the adjacent-case shape, one level above the code it was written
about.

---

## 3. R-ii — BL-044 against R3's own wording, not hc-c's characterisation

**R3 asks:** *"establish whether `expected_fail()`'s design needs a real exit code from `run_agent`
to key on."* **hc-c's notes characterise it** as *"BL-044 … is R3's question for hc-d"*.

**Related, but not the same question, and the difference matters.** BL-044 is the *defect*
(`Mix.Tasks.Aetheris.run/1` discards `Aetheris.CLI.run/1`'s code, so a failed run exits 0). R3 asks
whether hc-d's design **needs that fixed**. One input, established here rather than left for the
audit to re-derive: `run_agent` already keys on the exit status —
`if run_aetheris --json run "${args[@]}" > "$output_file" 2>&1; then … else fail "$label → non-zero
exit"; fi` — so BL-044 makes that `else` branch **unreachable today**. That is an input to R3, not
an answer to it.

**Not settled, and why.** `expected_fail()` does not exist: `grep -c 'expected_fail\|KNOWN_RED'` over
`../aetheris/scripts/sprint.sh` returns **0**. R3's question is about *that design's* needs, and the
design is hc-d's own — which the step-1 gate is written against, and the gate is unauthored (§4).
Settling R3 now would mean inventing the design in order to answer a question about it.

---

## 4. The stop: hc-d's step-1 gate is unauthored, and its resolver points at this edit

**The resolver, quoted.** hc-d's `Step-1 gate` slot reads: *"`[R13: not authorable. hc-d's design is
not done, and a gate is written against a design. Resolver: hc-d's own opening section-scoped edit,
per R12 — the gate is authored there, before the ticket opens, and it answers R3 above.]`"*

**`per R12` is load-bearing.** R12's closing line: *"Authoring is the reviewer's (decision 11) via a
section-scoped edit; the edit is dated and lands before the ticket does."* So the resolver names
**reviewer-authored gate text carried in hc-d's opening edit**. This opening edit is D1, D2 and D3 —
a conditional R12 narrowing, a promotion candidate, and a §Not established entry. **None of them
authors the gate.**

**And it is not only the gate.** Against §6's seven fields, named by this document's own
§What the methodology owes (*"seven sections and no more"*):

```
AUTHORED      Scope
AUTHORED      Contract refs
NOT AUTHORED  Touches
NOT AUTHORED  Do not generate
NOT AUTHORED  Runbook update rule
NOT AUTHORED  Done-check
NOT AUTHORED  Claude-code prompt

authored = 2 of 7      not authored = 5 of 7
```

hc-d's section still carries its catch-all: *"Everything else is `[R13: deferred to the
section-scoped edit that opens this ticket, per R12.]`"* — and that edit has now happened without
authoring them.

**So this is the stop the rider names, not a substitution.** Authoring the gate myself would be
exactly what hc-b2 found and what R13 was sharpened to forbid: hc-b completed hc-c's gate
confidently, and **every defect was in the one slot completed confidently** — a placeholder agent, a
transcript that could not distinguish its outcomes, and a premise the harness does not permit
(`supervisor.ex:62`). Every R13-marked slot was sound. Writing five §6 fields and a gate on my own
authority would reproduce that failure with five times the surface, and would also break decision
11's split — content is the reviewer's, formatting is the destination file's.

**What would unblock it:** a reviewer-authored section-scoped edit carrying hc-d's `Touches`,
`Do not generate`, `Runbook update rule`, `Done-check`, `Claude-code prompt`, and the step-1 gate —
the gate written against the design those fields describe, and answering R3.

**Two constraints the document already records for that edit**, restated so the author does not
rediscover them: **the population is 29, not 31** (BL-077's Done-when says *"Audit all 31 cases"*;
derive it again and correct the row), and **BL-077's §Suggested order entry is stale** — BL-069
closed by retirement, so only the `expected_fail()` disjunct is live, and R9 forbids reading the
first as licence.

---

## 5. R-iii and R-iv — not reached, and why that is not a silent omission

**R-iii** (fail-safe defaults must state what happens when input is missing, malformed or empty) and
**R-iv** (whether the `tee`/`pipefail` coupling really makes BL-077 and BL-133 face 2 one ticket)
are both riders on design work that did not start. **Neither is discharged and neither is dropped**
— they belong to the round that authors the gate. R-iv in particular is a finding *about R1* and
can only be made after the design exists; asserting it now would be the guess R13 forbids.

---

## 6. For whoever opens hc-d next

- **§Not established item 7 is still open** and now carries a second question: whether repair
  tickets should commit their findings *before* opening, which would make D1's premise true rather
  than assumed.
- **Item 8 is resolved** (§2 above) and hc-c's *"helps them"* rationale is corrected in three
  documents.
- **`Five tickets.`** in §Ticket set still needs revisiting with item 7.
- **BL-044's status is unchanged**, with one new input on the record: `run_agent`'s `else fail`
  branch is unreachable while BL-044 stands.
- **No code changed in this ticket**, in either repo. The harness tree is byte-identical to the one
  hc-c's gates passed on — it was checked out to `b4d782a` for §2's experiment and restored, with a
  positive control both ways.
