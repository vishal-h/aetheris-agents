# Review — bug-001 — round 1

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bug001reviewpacket.md` · Tree: `87a4c30` + round edits (uncommitted)

**Verdict:** accept with findings. One blocking (cheap), two non-blocking, one correction to the ticket that the round already caught and reported correctly.

---

## Findings

### 1. [blocking] §10's deferred finding has no backlog row — the same rule BL-190 was filed under

`CLAUDE.md` §Learning — BL-007: *"A deferred finding gets a backlog row in the same round it's deferred — prose in a packet or notes files nothing."* The packet applies this rule correctly to the red gate (BL-190, §5c) and then does not apply it to §10, while explicitly recognising it: *"it needs a backlog row if it is to have an executor."* Recognising the rule and not applying it is the failure the rule describes.

The §10 content is two distinct defects, both in a section this round edited:

- `drive/runbook.md` names `DRIVE_OUTPUT_FOLDER_ID` while the script reads `DRIVE_ROOT_FOLDER_ID` (divergent since `72367ac`), including in the `Verify in Drive` line inside this round's own diff hunk.
- The §"Validate upload standalone" *Expected output* block shows per-file `Uploaded … → <file_id>` lines the script has never printed; it emits only the `N uploaded, M failed.` summary.

The second is the more dangerous of the two: an operator following the runbook sees output that does not match and cannot tell whether the step failed. That is a false negative in the one document written to be followed under pressure.

**Suggested fix:** file one row covering both, in this round's diff, alongside BL-190. No code change. The row should note that the env-var half spans ten sites across the file, so it is a sweep rather than a one-line edit, and that the round deliberately edited the section without fixing them.

### 2. [non-blocking] `--month` is a new public flag with zero test coverage

The regression test uses `PAYSLIP_MONTH` — correctly, since that is the only vehicle that runs pre-fix (§2.5 of the ticket). But no test passes `--month` at all, so the flag's existence, its precedence over the env var, and the new "neither set" error message are all unverified. The round added an argparse argument and a precedence rule and tested neither.

The precedence is the part that matters: `args.month` winning over `PAYSLIP_MONTH` is the behaviour an operator relies on when overriding a Rig-injected value from the CLI, and nothing currently pins it.

**Suggested fix:** one test — set `PAYSLIP_MONTH=2026-03`, pass `--month 2026-04`, assert the uploaded set is April's. It is a copy of the new regression test with one line changed, and it pins precedence and flag-plumbing together. Optionally a second asserting exit 1 with the new message when neither is set.

### 3. [non-blocking] No `YYYY-MM` validation — `--month` accepts a glob and re-opens the defect class

`entry.glob(f"{month}-Payslip.pdf")` treats `month` as a pattern, not a literal. `--month '2026-*'` collects every month again and uploads them into a Drive folder named `2026-*`, because `period_folder_name` passes the string through unchanged. That is the original defect, reachable through operator input, in the code that fixes it.

A plain typo fails clean — `2026-8` matches nothing, and the `if not files: exit 1` guard at `:142` fires *before* `build_service`, so no stray folder is created. Only metacharacters reach the bad path. Low likelihood, but the failure is silent and client-visible.

The consistency argument the whole fix rests on also points here: `email_send.py:220` already does `datetime.strptime(args.month, "%Y-%m")`, and the packet's thesis is that `drive_upload.py` should match `email_send.py`. It now matches on selection and precedence but not on validation.

**Suggested fix:** `datetime.strptime(payslip_month, "%Y-%m")` after resolution, exiting 1 with a clear message on `ValueError`. Three lines, and it closes the input path into the defect class permanently.

### 4. [correction — mine, not the round's] The ticket's "two existing tests" was wrong; there is one

§6 is right and the census establishes it. The error is in the ticket I wrote: I read `test_collect_returns_sorted_by_employee_and_filename` at `:73-81` and reported it as two tests. There is one cross-month fixture in the file.

Recorded here rather than left in the packet's deviation section alone, because the ticket was the artifact that was wrong and the correction belongs against it. The round handled this correctly — it did not manufacture a second test to make the count come out right, and it published the census rather than asserting the conclusion.

---

## Commended

**The `keys == sorted(keys)` vacuity catch (§6) is the strongest thing in the packet, and the ticket did not ask for it.** The old assertion is true of any ordered output including an empty list, so under the month filter it would have kept passing while testing nothing — a test that stops testing without going red. Replacing it with an explicit expected list in the same edit is exactly right, and calling it out as an unrequested change rather than leaving it to be noticed in the diff is the behaviour the review loop is for.

Three more, briefly:

- **The red run is real.** Stashing only the source file, verifying with `git diff --stat` that the source sat at HEAD, and quoting `8 uploaded, 0 failed.` from captured stdout is the evidence the rule exists to produce. The restore was verified by diffstat rather than assumed.
- **BL-190 is diagnosed, not just reported.** Identifying a *moving* red — one seat at 31.93 days, five crossing around 2026-09-12, so the answer becomes 6 — and stating that a fix re-pinning to today's number is wrong within a week, is what separates a filed row from a deferred one.
- **§7 states the claim at the width the evidence supports.** 108 → 36 is measured; that the count caused the 300s timeout is labelled hypothesis. The temptation to let a verified 3× stand in for a timing result was available and declined.

---

## Dispositions requested

| # | Expected |
|---|---|
| 1 | fixed — one row filed in this round's diff |
| 2 | fixed — one precedence test |
| 3 | fixed, or `deferred (backlog ref)` with a row |
| 4 | no action — correction recorded against the ticket |

No re-review needed for 2 and 3 if the done-check output shows the new tests passing. Finding 1 is settleable by grep.

## Owed at commit, carried forward

Both already named by the round, restated so they are not lost between rounds:

- Post-commit `drift_check.py --strict` re-run, with the expected WARN set named as a **set**: `CLAUDE.md` and `docs/backlog-2026-06.md` staleness. Filing the finding-1 row keeps `docs/backlog-2026-06.md` in that set.
- The timeout hypothesis closes only on the next live September upload. The packet is correct that no live run is owed by this ticket; the obligation is on the run, not the round.
