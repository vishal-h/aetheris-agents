# Review — hc-d — the sprint exit contract

**Shape** follows `hc-b-review.md`, `hc-b2-review.md` and `hc-c-review.md`: one `## Round <R>`
section, appended, never rewritten; reviewer findings verbatim; claude-code's disposition table
beneath them. Committed per **R2**.

---

## Round 0 — the opening edit, and the stop

**Raised at:** nothing yet. This file opens with the ticket's own record.

**hc-d did not reach its contract work.** The opening edit (D1, D2, D3) landed; the step-1 gate is
**unauthored**, and its resolver names reviewer-authored text that this opening edit does not
carry. The ticket stopped there without an edit to `sprint.sh` or anything else in scope.

**What the opening edit did:**

| | Amendment | Outcome |
|---|---|---|
| **D1** | An R12 narrowing, offered **conditionally** on hc-b2's scope existing in a committed artifact before hc-b2 opened | **Premise fails — narrowing not written.** `hc-b2-review.md` was first added by hc-b2's own commit; six wordings of its findings return 0 files over the whole tree at `a581a8c`. §Not established item 7 **stays open**, with the finding added |
| **D2** | §Promotion candidates — the packet-assembly entry | **Added verbatim** |
| **D3** | §Not established — whether the provenance suites passed pre-hc-c | **Added, then resolved the same round** under R-i: they were green before (41 passed at `b4d782a`), and hc-c's *"the change helps them"* rationale is **wrong** — corrected in the three documents that carried it |

**The stop, stated so a reviewer can disagree with it precisely:**

- hc-d's `Step-1 gate` slot is `[R13: not authorable … Resolver: hc-d's own opening section-scoped
  edit, **per R12** — the gate is authored there, before the ticket opens]`.
- R12's closing line assigns authoring to **the reviewer** (decision 11).
- This opening edit is D1/D2/D3 and authors **neither the gate nor five of the seven §6 fields**:
  `Touches`, `Do not generate`, `Runbook update rule`, `Done-check`, `Claude-code prompt` are all
  still under the section's `[R13: deferred to the section-scoped edit that opens this ticket]`
  catch-all. **2 of 7 authored.**
- The rider is explicit: *"if the resolver names something that no longer exists or was never
  written, that is a stop, not a substitution (hc-b2 §G3(4) is the precedent)."*

**Why substitution would be the wrong call, not merely the unauthorised one.** hc-b2 established
that every defect in hc-c's specification sat in **the one slot hc-b completed confidently**, while
every R13-marked slot was sound. Authoring five fields and a gate here would reproduce that failure
across five times the surface.

**Three things the next author inherits, already on the record:** the population for BL-077 is
**29, not 31**; BL-077's §Suggested order entry is **stale** (only the `expected_fail()` disjunct is
live, and R9 forbids reading the other as licence); and `expected_fail()` **does not exist yet** —
`grep -c` over `sprint.sh` returns 0 — which is why R3 cannot be settled before the design exists.

**R-ii, recorded rather than settled.** R3's question is whether `expected_fail()`'s design needs a
real exit code from `run_agent`; hc-c characterised it as BL-044 itself. Related, not identical. One
new input: `run_agent` already branches on the exit status, so BL-044 makes its `else fail` arm
unreachable today. That is an input to R3, not an answer.

**R-iii and R-iv are not reached and not dropped** — both are riders on design work that did not
start.

---

## Round 1

_Awaiting review. Findings land here verbatim; dispositions beneath them, in a later commit._
