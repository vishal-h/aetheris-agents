# Review — hc-c — the `--json` contract (BL-105 + BL-106)

**Shape** follows `hc-b-review.md` and `hc-b2-review.md`: one `## Round <R>` section, appended,
never rewritten; reviewer findings verbatim; claude-code's disposition table beneath them.

Committed per **R2** — every `hc-*` ticket commits its review file, which is §1.4 and §8 compliance
rather than anything this round scoped.

---

## Round 0 — submitted for review

**Raised at:** nothing yet. This file opens with the ticket's own record so round 1 has a place to
land verbatim.

**What hc-c did, in the reviewer's own units:**

- The three amendments, with A3 re-placed by the reviewer after its named target was found absent
  from this document (it is `m4-consolidation.md`'s section).
- The step-1 gate, run as authored. **Verdict: routes to stderr**, on a non-nil `containment` and a
  2/0 split. §Not established item 1 resolved after being open since m4 t1a.
- BL-105 and BL-106 closed as one contract; both mutation postures recorded; Rig verified still
  correct on both paths; the runbook entry landed in this ticket.
- Decision 13 recorded as **not overturned**, with its reasoning and its now-established clause.

**Two things the ticket says about itself that a reviewer should press on first:**

1. **The gate's run failed** (Ollama out of memory) and the verdict was taken anyway. The argument
   is that the positive control is independent of the LLM call and `containment` proves the worker
   ran. If that argument is wrong, the verdict is wrong and everything downstream of it moves.
2. **A fork that starts and then fails was never observed by me** — it is covered by source
   ordering plus an existing harness test, not by a capture I produced. Stated in the notes §5.

---

## Round 1

_Awaiting review. Findings land here verbatim; dispositions beneath them, in a later commit._
