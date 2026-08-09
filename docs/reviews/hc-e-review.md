# Review — hc-e — the close

**Shape** follows `hc-b-review.md`, `hc-b2-review.md`, `hc-c-review.md` and `hc-d-review.md`: one
`## Round <R>` section, appended, never rewritten; reviewer findings verbatim; claude-code's
disposition beneath them. Committed per **R2**.

---

## Round 0 — the opening edit, and the stop

**Raised at:** nothing yet. This file opens with the ticket's own record.

**hc-e did not reach its close work.** The opening edit E1–E4 landed; the anatomy census then
stopped the ticket. hc-e has **2 of 7** §6 fields authored and **no step-1 gate slot at all**.

**What the opening edit did:**

| | Amendment | Outcome |
|---|---|---|
| **E1** | hc-d's §Ticket set row, under R19 as reviewer-authorised | **Closed at r3**, in hc-c's shape. Range **derived from the repos** per the `[V]`: agents `240eb59`→`f8ed90f`, harness `2d76a65`→`48f59e7`. Prior "Opened and stopped" text kept verbatim in the cell, per decision 7 |
| **E2** | §Promotion candidates — *an artifact selected by recency is not bound to its purpose* | **Added verbatim** |
| **E3** | BL-135 against BL-075 | **Same defect.** Module, file, line, stacktrace, assertion and error shape all identical; only the `System.unique_integer` run id differs. BL-135 was a duplicate I filed without searching the backlog. **Folded onto BL-075** as a third observation with its nine non-reproductions; BL-135 kept as the record of the duplication |
| **E4** | BL-075's arm-2 blocker | **Partly lifted.** Half 1 of the blocking clause (*"no such place exists"*) is now false; half 2 (*"`mix test` output is archived nowhere at all"*) still holds and is the half arm 2 needs. The place exists; the routing does not |

**The census, and the stop it forces:**

```
AUTHORED      Scope
AUTHORED      Contract refs
NOT AUTHORED  Touches
NOT AUTHORED  Do not generate
NOT AUTHORED  Runbook update rule
NOT AUTHORED  Done-check
NOT AUTHORED  Claude-code prompt

population = 7    authored = 2    not authored = 5
Step-1 gate slot: ABSENT — not even R13-marked
```

Positive control over hc-d's section, which has all seven: `1` for every field, `2` for the gate
slot. So the zeros read as absence.

**hc-e is hc-d's shape and worse in one respect** — hc-d's gate slot existed and was R13-marked
with a resolver; hc-e has no gate slot, and its catch-all (`**Everything else is
`[R13: deferred, per R12.]`**`) defers the gate along with the five fields.

**Why a stop rather than a substitution.** R12 assigns authoring to the reviewer (decision 11), and
hc-d's precedent is that every defect in hc-b's version of hc-c's specification sat in **the one slot
completed confidently**, while every R13-marked slot was sound. Doing it here would reproduce that
failure in the ticket that closes the round, where nothing later catches it.

**What would unblock it:** a reviewer-authored section-scoped edit carrying hc-e's five remaining
§6 fields and a step-1 gate written against the design they describe.

**Two things for that edit, beyond the three already on the record.** hc-e's *"named question that
gates the rest"* is marked `[partly falsified]`, and the half that still stood — *"hc-d has not
run"* — is **now false too**; both halves are knowable when the anatomy is authored, which changes
what the slot should say rather than merely dating it. And **hc-e's own row in §Ticket set was left
untouched deliberately**, because the census may change what it should say.

---

## Round 1

_Awaiting review. Findings land here verbatim; dispositions beneath them, in a later commit._
