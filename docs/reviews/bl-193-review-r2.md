# Review — BL-193 — round 3

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bl193r2packet.md` · Commit: `f35ac30` on `c171034`

**Verdict:** finding 12 closed; the settlement holds and is well made. Two new findings — 13 is an operational consequence the data establishes and nobody has stated, 14 is a narrowing of one corroboration claim. Neither disturbs the conclusion.

---

## Findings

### 13. [blocking — operational, not editorial] Three employees have no August payslip in Drive, and nothing currently says so

The widened read establishes this and the round did not draw it out. It is the most consequential fact in the packet.

`collect_upload_files` sorts by `(employee_id, path.name)`, so **within** each employee folder the write order is by filename: `2026-05-Payslip.csv`, `2026-05-…pdf`, `2026-07-…csv`, `2026-07-…pdf`, `2026-08-…csv`, `2026-08-…pdf`. **The requested month sorts last.** Every employee's August payslip is the last thing written for that employee.

Cross that with where the run stopped:

- `BTL_036` — **1 of 6** objects. By sort order that one object is `2026-05-Payslip.csv`. Its August payslip was never written.
- `BTL_06` — folder absent from `2026-08/` entirely.
- `BTL_Consult_01` — folder absent from `2026-08/` entirely.

So **three of eighteen employees have no August payslip in the Drive archive**, today. The other fifteen do, because they completed all six objects — `BTL_035`'s max `createdTime` of `02:47:48.179` is its `2026-08-Payslip.pdf`.

This is a different defect consequence from the one BL-191 tracks. BL-191's cleanup is about files that are *present and misplaced*. This is about files that are *absent*. A cleanup pass that removes stray months from `2026-08/` will not notice three employees whose August payslip was never uploaded, and will leave the archive quietly incomplete for exactly the people the fix was for.

It is also the sharpest possible statement of the defect's cost, and it belongs in BUG-001: **the unfiltered glob did not merely add wrong files, it starved the wanted ones.** Because the requested month sorts last within each employee, any truncation of this run loses the requested month first. That is a structural property of the bug, not an accident of where it stopped.

The employees were not harmed — `email_send.py` reads local `payslip/output/`, and all 18 August emails went out. The gap is the archive.

**Suggested fix:** one dated block in BUG-001 recording the three affected folders, the sort-order reason the requested month is lost first, and that the archive gap is distinct from BL-191's misplacement cleanup. Then either a row for the remediation or an explicit note that re-running the fixed upload for `2026-08` closes it — which it would, and cheaply, since the fixed code uploads 36 objects rather than 108 and completes well inside the cap.

### 14. [non-blocking] The overshoot corroborates the conclusion but does not discriminate as claimed

§5 argues: *"A large overshoot would have been evidence against the story; 0.270 s is evidence for it,"* on the mechanism that `Task.yield` brutal-kills only the awaiting task and the `python3` child dies when the BEAM node exits.

There is a second account that produces the same observation. Drive's `createdTime` records when Drive completed the object, not when the client began the request. At a ~3 s cadence per object, an upload initiated up to ~3 s before the cap can land after it with no child outliving anything. Under that reading a 0.270 s overshoot and a 2.5 s overshoot are equally consistent, so the interval's size is not the discriminator the paragraph claims.

Both accounts support **(ii)** — under either, the process was working when the cap fired — so the settlement is untouched. What narrows is the corroboration: the overshoot is *not inconsistent* with the mechanism rather than *evidence for* it, and the falsifiability claim attached to a large overshoot does not hold.

**Suggested fix:** restate the paragraph as consistency rather than confirmation, and name the in-flight account as the alternative. It costs nothing and removes the one place in a carefully-hedged row where a claim reaches past its evidence.

---

## Finding 12 — closed, and the method is the point

The prediction was written to a file and hashed **before any query ran**, with the invalidator stated as part of the prediction rather than appended after. The observation then matched on every axis:

| | predicted | observed |
|---|---|---|
| objects present | ≈92 | 91 |
| last `createdTime` | ≈`02:47:5x` | `02:47:52.739Z` |
| absent | ≈16 | 17 |
| where | last folders alphabetically | `BTL_036`, `BTL_06`, `BTL_Consult_01` — exactly the tail |

The absence accounting closes independently (5 + 6 + 6 = 17 against 108 − 91), the sort order was verified rather than assumed, and the invalidator was run and did not fire — per-folder mean gaps 2.786–3.185 s, spread 0.399 s, so the rate that produced the ≈92 holds across employees rather than being one folder's accident.

**The deciding observation is the sign of a subtraction, and it is the right one to have chosen.** The last object at `02:47:52.739Z` against a cap at `02:47:52.469Z` means the process was writing when the cap fired. History (i) cannot accommodate a process that dies of its own accord and stops within a second of `run_start + 300 s`.

---

## Commended

**Two controls were load-bearing in one round, and both caught something.**

The Drive query's first form returned zero folders named `2026-08` — the same shape that missed in round 1 — and the script **aborted** rather than reporting an empty listing. §8 deviation 2 states the stakes exactly right: here a zero does not read as "query wrong", it reads as "no objects were written", which is the early-death shape. An uncontrolled run would have produced a well-formed, plausible, and exactly backwards settlement of (i) versus (ii). Recording that this is the second consecutive round in which the control was the thing standing between a broken query and a false finding — and inferring it is a property of the corpus rather than luck — is the right conclusion to draw from two data points.

**And the vacuous-guard catch is the better of the two.** A grep written to prove BUG-001's Status and Done-when were untouched returned a clean "nothing changed" — the answer the author wanted — and its positive control over the r1 commit, which *did* edit a Done-when, also returned 0. A control that returns the same answer as the test is impossible if the test works. Replacing it with a byte comparison carrying a mutation control, plus the blunter and stronger removed-lines count, is right; leaving the failed first version in the packet because *"the check I first wrote was blind is information about how much the surviving check is worth"* is righter.

**The row's amendments are honest about what they overturn.** The heading changed from *"What is NOT established"* to *"What the trajectory does not establish"*, the closing sentence from *"this row does not choose"* to a settlement, and both carry dated blocks quoting what they replaced — including the reason both histories are kept stated: the argument for (ii) is that (i) cannot accommodate one observation, and a reader cannot check that against a history the row has deleted. That last clause is the one most rounds would have skipped.

**The `timeout_ms` paragraph promoted correctly.** It was filed as a principle with *"whether that is what happened here is not settled"*; it is now demonstrated, with the 1.716 s margin identified as the same number the trajectory ends after because `tool_called` and the cap share an offset from `run_start` — one number in two roles, named as such rather than presented as a coincidence.

---

## Dispositions requested

| # | Expected |
|---|---|
| 13 | fixed — dated block in BUG-001; remediation either rowed or explicitly closed by a re-run |
| 14 | fixed — one paragraph restated as consistency |

## Owed

Unchanged, plus one: BUG-001's September verification is still open and correctly untouched; "a different writer" remains the only live way to overturn the settlement and is unfalsified rather than refuted; the six-item packet head still belongs to the housekeeping pass. **New:** if finding 13's remediation is a re-run rather than a row, it is also the first live exercise of the fixed code — which is BUG-001's September Done-when arriving three weeks early. Worth noticing before someone runs it casually.
