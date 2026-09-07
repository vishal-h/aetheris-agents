# Review — BL-193 + BL-189 cross-reference — round 1

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bl193bl189packet.md` · Commits: `d282c1d`, `2b2f0f4` on `ab64cf2`

**Verdict:** accept. Item 2 closes. Item 1's row is correct and the control did exactly what it was for. Three findings: one is my error, one settles a claim the row leaves open, one closes the packet's own labelled prediction. None blocks the commit.

---

## Findings

### 9. [reviewer error, recorded against the ticket] "It originates in the harness" was asserted from a `rig/`-only grep

The cc:prompt said: *"the string is NOT in the Rig repo at 87a4c30 … So it originates in `../aetheris` or in something the harness passes through."* Both halves of that sentence were wrong to state as a conclusion. The grep behind it covered `rig/` alone; `agents/orchestrator.exs` sits in `aetheris-agents`, in a clone I had open, and one unscoped grep would have found it. Verified now:

```
$ grep -rn "step timed out after 5 minutes" . --exclude-dir=.git
./agents/orchestrator.exs:302:        {:error, "step timed out after 5 minutes"}
```

Eliminating one candidate and naming the next without testing it is the same shape as this morning's timeout diagnosis, which read a UI string while the trajectory sat unread. Twice in one day, and both times the missing evidence was already within reach. The round was right to record this as *located, not absent*, and right to note that the preceding search had eliminated two plausible homes and concluded wrongly about the third.

### 10. [substantive] The wall-clock record the row says would settle `s2inHA` exists, and it points away from history (i)

BL-193 declines to choose between two histories and says settling them *"needs a wall-clock record from outside the trajectory."* One exists, and it was in the incident report from the start.

The Drive listing for `2026-08/BTL_01/` shows six files with `Date modified` of **8:12–8:13 AM**. The operator is UTC+5:30, so that is **02:42–02:43 UTC**. The run's last recorded event, `tool_called`, is at **02:42:54.185Z**. Files were therefore being written to Drive *after* the trajectory stops — the process was alive and doing work past its last event.

That does not settle (i) versus (ii), but it refutes **(i) as worded**. The row states it as *"the run died at `02:42:54` for a reason of its own"* — anchoring the death to the last-event timestamp, which is the exact inference the row elsewhere warns against (`finished_at` *"dates the last event, not the death of the process"*). The caution is right and the hypothesis was written without it.

**Two caveats, both checkable, and the row should carry them rather than the conclusion:**

- The Drive UI displays minute granularity. The Files API `modifiedTime`/`createdTime` gives seconds and is the citable form.
- Nothing here rules out a different `drive-upload-*` run having populated that folder. `select run_id, status, started_at from runs where run_id like 'drive-upload-%' and started_at like '2026-09-07%'` settles it in one query.

**Suggested fix:** replace history (i)'s wording so it is not anchored to `02:42:54`, and add a short paragraph naming Drive object timestamps as the outside record, with both checks above. The row currently tells a fixing ticket that it needs something it does not have; it has it.

### 11. [closes §8 item 2] The `inspect/1` prediction is confirmed — I have the card

§8 flags one derived claim: hop 2 passes the message through `inspect/1`, so the card should render it quote-wrapped, and *"I did not see the card."*

I did. The screenshot of the 2026-09-07 payslip run shows step 3's error rendered as:

```
"step timed out after 5 minutes"
```

Literal double quotes, exactly as `inspect/1` on a binary produces. The derivation from `:312` holds and can be relabelled observed.

Worth keeping the reasoning beside the observation rather than replacing it — the prediction was made from the code alone and was right, which is what makes the emission path trustworthy end to end.

**Suggested fix:** in BL-193, mark the hop-2 consequence as confirmed against the reported card, and note the quoting is itself a small operator-facing wart: an error already rendered as prose arrives on the card wrapped in quotes because it passed through `inspect/1` on its way. Not worth its own row; worth one clause in the Done-when so a fix does not reintroduce it.

---

## Item 2 — accepted

The BL-189 cross-reference is placed correctly: a dated pointer in §Surface 2 naming `email-orch-dWIgxw`, with the evidence left where it was recorded in BL-191 and explicitly not moved or duplicated. That is the right resolution of a findability problem — one pointer, one copy of the evidence.

---

## Commended

**The control did the job it was chosen for, and the result is stronger than "no timeout recorded."** Both 2026-06-10 runs carry a `tool_result` one timeout-length after `tool_called`, both state the bound as `"timed out after 60000ms"`, and — the part neither of us predicted — both runs are `status: done`, because a step timeout is a result the agent reads and continues past, not a run failure. So a genuine step timeout does not merely look different from `s2inHA`; it cannot produce a `failed` run at all. `s2inHA` is not a timeout with its evidence missing, it is structurally not a timeout.

**The minutes sweep is what closes it.** Establishing that the harness renders no timeout in minutes anywhere — three `minute` hits across `lib`, `native` and `test`, none an error message — turns "the string isn't in the harness" into "the string *cannot* come from the harness," which is a different and much stronger claim. That is the difference between a grep and a proof.

**The two-clocks derivation is the row's real content, and it outlives the message.** `Task.yield`'s deadline is fixed at spawn; `await_run`'s equal-sized inactivity bound resets on every activity change, and resets on the first poll unconditionally because `watch.key` starts `nil`. So the harness's accurate, seq-naming diagnosis loses the race for *every* run, by construction. The corollary is worse than the wart that prompted the row: the step's own `timeout_ms` is also `300000`, so a script that genuinely runs its full budget has its `tool_result` land after the orchestrator has already abandoned it. The Done-when correctly refuses a wording-only fix on exactly that ground.

**Deviation 2 is the packet's best moment.** A count published in a row, true when measured and false from the commit that carries it, because the row's own prose contains the searched string three times. Caught by regenerating rather than trusting, de-numeralised to a site, and landed as a second commit rather than an amend — because `d282c1d` was already cited in the round's own `drift_check` capture and amending would have pointed that citation at a tree that never existed. The reasoning about *why not amend* is the part worth keeping.

**And the substitution/positive-control discipline.** Reporting `select count(*) … like '%stalled%'` → 0 as *a check that cannot observe its subject* rather than as evidence, with `orphaned_no_live_process` → 80 over the same column and form as the control that proves the query shape works, is the correct handling of a negative over an unobservable population. Most packets would have published the zero.

---

## Dispositions requested

| # | Expected |
|---|---|
| 9 | no action — recorded against the ticket, not the round |
| 10 | fixed — reword history (i), add the Drive-timestamp record and its two checks |
| 11 | fixed — hop-2 consequence marked confirmed; one clause in Done-when about the `inspect/1` quoting |

## On §8 item 3

The six-item packet head living only in cc:prompt preambles, with `CLAUDE.md` §Learning — ds naming three of six, is the BL-162 shape and does deserve a row. It is **not** this round's, and it is not a defect in the code — it is a methodology-doc gap. It belongs with the backlog housekeeping pass that is already pending (archive-on-close, the `superseded`/`wontfix` sweep, the section split), where the methodology file is being touched anyway. Flagging it here rather than acting on it was the right call.
