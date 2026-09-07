# bug-001 — Drive upload ignored the requested month

**Fixed at:** working tree over `87a4c30`. All repo-state claims below were
verified at that commit unless stated otherwise.

---

## The defect

`drive/scripts/drive_upload.py:21` — `collect_upload_files(source_dir)` globbed
`*-Payslip.pdf` and `*-Payslip.csv` with no month predicate. `main()` read
`PAYSLIP_MONTH` at `:132` but used it only to name the destination period
folder (`:148-149`). Every month present in `payslip/output/` was therefore
uploaded into the requested month's folder.

`payslip/output/` is a deliberate per-employee archive — `generate_employee_payslips.py`
generates every month in the CSV by design and `merge_employee_payslips.py`
depends on that — so the archive is correct and the *selector* was the defect.

## The fix

`collect_upload_files(source_dir, month)` globs `f"{month}-Payslip.pdf"` and
`f"{month}-Payslip.csv"`. The sort key `(employee_id, path.name)` and the two
skip rules (HTML files, non-directory entries at the source root) are unchanged.
`main()` gains `--month`, falling back to `PAYSLIP_MONTH`, erroring when neither
is set — the precedence in `email/scripts/email_send.py:204-207`, whose exact
month path construction (`:131`) is the pattern this now matches.

**No agent file changed, and none needed to.** The three `.exs` call sites —
`drive/agents/drive_upload_orchestrator.exs:22`,
`drive/agents/drive_orchestrator.exs:27`, `payslip/agents/payslip_pipeline.exs:40`
— all invoke the script with no arguments, so they take the `PAYSLIP_MONTH`
fallback, which is the path they already used.

---

## The two corrected test assertions, and why

The ticket named two existing tests asserting cross-month collection. **There is
one.** `git grep -n "2026-0[0-9]-Payslip" drive/tests/` at `87a4c30` returns every
month-bearing fixture in the directory; exactly one test creates files in two
different months. This is recorded as a divergence between ticket text and repo
state rather than resolved by finding a second candidate. The *call-site* count
in the ticket is right: eight, one in `main()` and seven in the tests.

**1. `test_collect_returns_sorted_by_employee_and_filename`** (`:73-81` pre-fix).
Its fixture gave each of two employees a `2026-04` PDF and a `2026-03` CSV, and
asserted all four came back sorted. That assertion **encoded the defect**: it is
a direct statement that a cross-month collection is the correct result. Corrected
by moving both files into the requested month, so the test still exercises two
files per employee — which is what makes the `path.name` half of the sort key
observable — while no longer asserting anything about months.

The assertion also changed shape, from `keys == sorted(keys)` to an explicit
expected list. `keys == sorted(keys)` is satisfied by any output the function
happens to produce in order, including an empty list, so under the fix it would
have passed while collecting nothing. The corrected fixture would have made it
vacuous rather than red — a test that stops testing without going red is the
failure this repo's gate rules exist to prevent, so the assertion was made
falsifiable at the same time.

**2. The month argument itself** at the six remaining `collect_upload_files`
call sites. These are signature updates, not corrected assertions: each fixture
was already single-month, and passing `"2026-04"` preserves what each test
asserted.

## The entrypoint-vehicle constraint

The new regression test is `test_main_uploads_only_the_requested_month`.

A test calling `collect_upload_files(dir, month)` **cannot run against pre-fix
code at all** — pre-fix the function takes one argument, so the test errors on
its own call rather than on the defect, and a test that cannot run red for the
right reason proves nothing. The test therefore drives `main()`.

Within `main()`, the vehicle must be `PAYSLIP_MONTH` and not `--month`: pre-fix
`main()` already reads the env var at `:132`, whereas `argparse` exits 2 on an
unrecognised `--month`, which is again an error about the test rather than about
the defect.

The assertion is on `upload_file.call_args_list` — the exact multiset of uploaded
filenames — and deliberately **not** on the printed count. A count assertion
passes for the wrong reason the moment the fixture changes size, and the count is
exactly the quantity the defect inflates, so asserting on it would couple the
test to the fixture instead of to the behaviour.

**Red run against pre-fix source.** `git stash push drive/scripts/drive_upload.py`
(source at `87a4c30`, tests at the working copy), then the single test:

```
drive/tests/test_drive_upload.py::test_main_uploads_only_the_requested_month FAILED [100%]

E       AssertionError: assert ['2026-03-Pay...lip.csv', ...] == ['2026-04-Pay...-Payslip.pdf']
E         At index 0 diff: '2026-03-Payslip.csv' != '2026-04-Payslip.csv'
E         Left contains 4 more items, first extra item: '2026-04-Payslip.csv'
----------------------------- Captured stdout call -----------------------------
8 uploaded, 0 failed.
=========================== short test summary info ============================
FAILED drive/tests/test_drive_upload.py::test_main_uploads_only_the_requested_month
============================== 1 failed in 0.12s ===============================
```

Eight uploads pre-fix against four post-fix on the same fixture (two employees ×
two months × two file types, `PAYSLIP_MONTH=2026-04`) — the defect exactly. The
source was restored with `git stash pop`.

---

## Did the timeout hypothesis hold?

**Yes, and the ratio is larger than the ticket's estimate.** Counted in
`payslip/output/` at `87a4c30`:

```
$ ls -d payslip/output/*/ | wc -l
18
$ find payslip/output/ \( -name '*-Payslip.pdf' -o -name '*-Payslip.csv' \) | wc -l
108
$ find payslip/output/ \( -name '*-Payslip.pdf' -o -name '*-Payslip.csv' \) \
    | sed 's#.*/##; s/-Payslip\..*//' | sort | uniq -c
     36 2026-05
     36 2026-07
     36 2026-08
```

18 employees, three months present, 36 files per month.

| | uploads | folder lookups |
|---|---|---|
| before | 108 | 1 period + 18 employee |
| after | 36 | 1 period + 18 employee |

**Uploads drop 108 → 36, a factor of 3.** The ticket estimated "~18 employees ×
3+ months × 2 files"; the archive holds exactly three months, so the estimate was
right in shape and the factor is 3 rather than more. Each upload is a
`files.list` followed by a `files.create` or `files.update` — two API round trips
— so the step goes from ~216 round trips to ~72 against the same 19 folder
lookups. That is consistent with the 300s orchestrator timeout being hit before
step 3 completed, and with the email step never running.

**This is an arithmetic argument, not a measurement.** No live upload was run —
the timing was not reproduced against Drive, and this repo carries no recorded
before/after wall-clock for the step. What is established is the count; that the
count was what exceeded 300s remains the hypothesis, now supported by a verified
3× rather than by an estimate. A live run is the only thing that would close it,
and it is not owed by this ticket.

The three months in the archive are `2026-05`, `2026-07` and `2026-08` — note
the gap at `2026-06`. The fix makes the selected month exact, so the gap does not
matter to it; it is recorded because the count above is a function of what the
archive happens to hold on this machine and will move.

---

## Boundary gates

`python3 scripts/drift_check.py --strict` — 0 FAIL. The `project_knowledge` WARNs
are the exempt staleness class; none of the three `drive/` files this fix touches
carries a manifest row, so check 8's verdict is unmoved by them.

`python3 -m pytest -q -m "not integration and not dormant"` from the repo root —
**RED, off-territory**: `1 failed, 1558 passed, 3 skipped, 324 deselected,
7 xfailed in 190.37s`. The failure is
`cloudcost/tests/test_fetch_github.py::test_the_normalized_inventory_is_readable_by_the_shared_rule_engine`,
reproduced at a clean tree at `87a4c30` and therefore not this fix's doing. It
was untracked; per `CLAUDE.md` §Definition of done it got a ticket the day it was
found — **BL-190**, which carries the diagnosis (a frozen seat fixture compared
against a reference date that resolves to the wall clock) and the two candidate
fixes. Not fixed here: this ticket is drive-only.

## Out of scope, not done

Per the ticket's DO NOT GENERATE list, untouched: `payslip/scripts/generate_employee_payslips.py`,
everything under `email/`, every orchestrator `.exs`, any manifest-based upload
design, and the already-misplaced files in Drive (live client data — a separate
task, and this fix does not clean up what earlier runs uploaded).

**One observation, not acted on.** `drive/runbook.md` §"Validate upload standalone"
names `DRIVE_OUTPUT_FOLDER_ID` while the script reads `DRIVE_ROOT_FOLDER_ID`, and
its "Expected output" block shows per-file `Uploaded …` lines the script does not
print — it prints only the `N uploaded, M failed.` summary. Both predate this
ticket and neither is the month defect, so neither was changed here.

---

# Round 2 — review dispositions

Appended 2026-09-07 against `docs/reviews/bug-001-review.md` (claude-ui, round 1).
Nothing above this line is rewritten; the round-1 record stands as written.

| # | disposition |
|---|---|
| 1 | **deferred (BL-191)** — a row is what the finding asked for; both defects left unfixed by design |
| 2 | **fixed** — two tests: `--month` precedence, and the neither-set branch |
| 3 | **fixed** — `YYYY-MM` validation + one rejection test |
| 4 | no action — the reviewer's correction to their own ticket |

**Done-check: `python3 -m pytest drive/tests/ -v` → 38 passed.** The review
predicted 37 (35 + one per finding). The extra test is finding 2's *optional*
second half — the "neither `--month` nor `PAYSLIP_MONTH`" branch — which the
review offered and I took, so the count is 35 + 2 + 1.

## Finding 1 — BL-191, and why it is filed wider than it was raised

The finding asked for one row covering two `drive/runbook.md` defects. The census
run to write that row found the population reaches **executable code in the
harness repo**, so the row is filed at that width.

`../aetheris/scripts/sprint.sh:1061` gates the drive sprint arm on
`DRIVE_PAYROLL_FOLDER_ID` and `DRIVE_OUTPUT_FOLDER_ID` and `exit 1`s when either
is unset. Nothing has read either since `72367ac` (2026-06-06), the commit that
replaced them with `DRIVE_ROOT_FOLDER_ID`. So an operator who sets what the
scripts read kills the sprint at its prerequisite loop; one who sets what the
sprint demands passes that gate and then fails inside `drive_upload.py`. The
`fail` message points at `drive/runbook.md` — the document that confirms the wrong
name. Each artifact corroborates the other and neither matches the code.

This is the *wiring list's enumeration is short* class (`CLAUDE.md` §Learning —
m6-cloudcost) with the generated-artefact clause instead reading as an executable
one: a shell script that gates on an env var is a wiring place, and it is the kind
of place a rename reliably forgets.

Not fixed here, per the round's instruction and the finding's own framing: the row
is the deliverable.

## Finding 3 — what the mutation test established

The validation was mutation-tested before the round closed, restoring from a
working-copy backup rather than `git checkout --` (the file carries uncommitted
work; `CLAUDE.md` §Learning — the 2026-08-16 export boundary). Restore verified by
sha256 — identical before and after.

With `datetime.strptime(...)` replaced by `pass`,
`test_main_exits_1_on_a_month_that_is_not_yyyy_mm` fails **with an `HttpError`
from `googleapiclient`**, not with an assertion mismatch. That is stronger than
the finding claimed: it shows execution reaching `build_service()` and issuing a
real Drive API call on a globbed month. The `if not files: exit 1` guard does not
save the metacharacter case — `2026-*` matches files, so the guard passes and the
run proceeds to Drive with a folder name of `2026-*`. The finding's "low
likelihood, silent failure" reading is right about likelihood and understates the
reach.

**One deliberate divergence from `email_send.py`.** The finding cites
`email_send.py:220` as the pattern. That line calls `strptime` for *display*
(`.strftime("%B %Y")`), so its validation is a side effect and a bad month raises
an uncaught `ValueError` — a traceback, not a clean exit. `drive_upload.py` exits
1 with a message instead, which is what `CLAUDE.md` §Python script conventions
requires of a stage CLI (*they degrade, they don't crash*). Matching
`email_send.py`'s *behaviour* here would have meant copying a defect; the
divergence is toward the convention, not away from it. Whether `email_send.py`
should be brought to the same shape is not this round's call and has no row.

## Gates

Not re-run, per the round's instruction: the whole-suite gate and
`drift_check --strict` were captured in round 1 and **BL-190** stands as filed.
Round 2 adds BL-191 to `docs/backlog-2026-06.md`, which was already in the
expected post-commit WARN set for that file's staleness, so the set is unchanged:
`CLAUDE.md` and `docs/backlog-2026-06.md`. The post-commit `--strict` re-run
remains owed at the commit.

---

# Round 3 — review dispositions

Appended 2026-09-07 against `docs/reviews/bug-001-review-r1.md` (claude-ui, round
2). Rounds 1 and 2 above are not rewritten.

| # | disposition |
|---|---|
| 5 | **deferred (BL-192)** — one S row; `email_send.py` deliberately not fixed |
| 6 | **fixed** — docstring corrected to what the capture shows, plus the note below |

**Done-check: `python3 -m pytest drive/tests/ -v` → 38 passed**, unchanged as the
review expected. Neither finding adds or removes a test; finding 6 edits only a
docstring.

**BL-191 gained evidence, not a row.** The `DRIVE_TEMPLATES_FOLDER_ID` failure the
reviewer reported — `email_orchestrator2.exs` dying at step 0, run
`email-orch-dWIgxw`, blocking the August payslip send until `email_send.py` was
invoked directly — is recorded inside BL-191 as a dated evidence block, beside the
`sprint.sh:1137` mismatch it corroborates. It does **not** settle that row's open
"has the drive arm run since `72367ac`" question: that was the *email*
orchestrator, not `sprint.sh`. What it settles is the class — these mismatches are
load-bearing, and this one has now cost a payroll run.

## Finding 6 — the known network-on-regression property

`test_main_exits_1_on_a_month_that_is_not_yyyy_mm` leaves `build_service`
unpatched, which is what makes it prove the exit precedes the Drive client. The
old docstring explained that as "reaching it would fail on credentials rather than
exit 1". **The mutation capture refutes that**: `build_service()` *succeeded* and
the run issued a real request to `www.googleapis.com/drive/v3/files` carrying
`q=name = '2026-*'`, failing with `HttpError 404`. Credentials were present, as
they generally are on a machine running this suite.

The consequence, recorded as a known property rather than left to be discovered:
**if the `YYYY-MM` validation ever regresses on a machine with
`GOOGLE_SERVICE_ACCOUNT` set, this test reaches the network instead of failing
fast.** The green path is hermetic — `main()` exits at validation before
`build_service()` is called, so a passing run touches nothing and the test
correctly carries neither deferral marker. Only a regression reaches out, and a
test that makes a live call when the thing it guards breaks is an acceptable
trade for one that proves the guard is load-bearing. It is documented here and in
the docstring so a later reader meets it as a design decision.

## Finding 5 — why BL-192 is separate, and which script is correct

Filed as its own S row rather than folded into BL-191: different file, different
concern, and BL-191 is already an M spanning two repos.

The row carries the reasoning from round 2's §8 so the divergence is legible
before anyone converges the two scripts. In short: `email_send.py:220` calls
`strptime` inside a *display* expression (`.strftime("%B %Y")`), so its validation
is incidental and a malformed month raises an uncaught `ValueError` — a traceback
on stderr, not a message. The exit code is coincidentally 1; the defect is the
shape, against `CLAUDE.md` §Python script conventions.

Two precisions the row establishes that round 2's prose did not:

- **The blast radius is a bad error message, not data movement.** `find_pdf`
  builds a literal path and tests `.exists()`, so `email_send.py` never treats the
  month as a glob — a metacharacter month cannot re-collect other months there.
  Line 220 also runs before the send loop, so nothing is sent. This is why it is
  S/low where the same input was serious in `drive_upload.py`.
- **`drive_upload.py` is the correct side of the divergence.** Converging the two
  means bringing `email_send.py` up to a clean exit, never bringing
  `drive_upload.py` down to a traceback. The row says so in its Not-done-when, so
  a later reader cannot close it by deleting the validation.

`email_send.py` is untouched by this round, per the instruction.

## Gates

Not re-run, per the instruction. BL-190 stands as filed. Round 3 writes only to
`docs/backlog-2026-06.md` (BL-192, plus the BL-191 evidence block),
`drive/tests/test_drive_upload.py` (one docstring) and this file — so the expected
post-commit WARN set is unchanged: `CLAUDE.md` and `docs/backlog-2026-06.md`
staleness. Finding 5's row keeps the backlog in that set; it adds no member. The
post-commit `drift_check --strict` re-run remains owed at the commit.

---

# Round 4 — review dispositions (final round)

Appended 2026-09-07 against `docs/reviews/bug-001-review-r2.md` (claude-ui, round
3). Rounds 1–3 above are not rewritten.

| # | disposition |
|---|---|
| 7 | **fixed** — `BUG-001` filed, in a new `## Bugs` section with the id-space convention declared |
| 8 | **fixed** — inner backticks dropped from BL-191's `Source:` span |

**Done-check: `python3 -m pytest drive/tests/ -v` → 38 passed**, unchanged.
Neither finding touches a test; neither touches any source file.

**ROUND TYPE convention adopted:** a round is `code` whenever a tracked source
file appears in the diff, regardless of whether an executable statement changed.
The reviewer's grep-checkable boundary beats the judgment-based one, and finding
6 was the counterexample to my own premise — a docstring carried a false claim
about a mechanism, so a docstring edit is not prose. **This round is
`documentation` under that rule**: the diff contains no `.py` file at all.

## What the dev DB added to BUG-001, and why the row is longer than the finding asked

The finding asked for the run ids to be recorded. Reading them changed what the
row says.

- **`drive-upload-s2inHA` did not record a timeout.** Its events end at
  `tool_called` (`run_command`, `timeout_ms: 300000`, and **no `--month`** —
  confirming the `PAYSLIP_MONTH` fallback path round 1 described), with **no
  `tool_result`**, followed by `run_orphaned`
  `{"reason":"orphaned_no_live_process"}`. `runs.status` is `failed` by that
  sweep. The DB shows the harness losing the process, not a 300 s timeout firing.
- **The hypothesis has precedent at a different limit.** `drive-upload--gjVYA`
  and `drive-upload-bMsa_Q`, both 2026-06-10, both recorded
  `tool_result{"duration_ms":60001,"exit_code":-1,"stderr":"timed out after 60000ms"}`
  — a **60 s** limit, and both runs marked `done` because the agent reported the
  timeout and finished.

So the step has demonstrably timed out before, at 60 s; the failure this ticket
was filed from was an orphan sweep at 300 s; and **no 300 s timeout is recorded
anywhere**. The causal claim rests on the upload count alone. That belongs in the
row rather than here, because the person watching the September run would
otherwise look for a timeout event to stop happening and find that there never
was one. It does not weaken the fix — the month defect is proven independently —
and it sharpens what `verified` will actually mean.

`payslip-orch-WRFoqQ` confirms the denominator: *"Done: 18 employee(s), 18
payslip(s) generated."*

## A second instance for BL-189, found the same way

`email-orch-dWIgxw` — the run behind BL-191's evidence block — has
`runs.status` = `done` while its **step 0 failed**
(`tool_result{"exit_code":1,"stderr":"DRIVE_TEMPLATES_FOLDER_ID environment
variable is not set."}`, then `step_complete{"step":0}` and
`run_complete{"reason":"agent_finished"}`). An operator reading run status alone
sees a successful run of an orchestrator whose first step failed. That is
**BL-189**'s class observed rather than reasoned about, so it is recorded as a
dated precision inside BL-191's evidence block. It changes neither row's scope.

## Placement of the `## Bugs` section — a decision worth being able to reverse

The section is placed **at the top of the file**, after the intro block and before
`## Harness (aetheris/)`, rather than beside BL-190–192 at the end. Reasoning: the
finding's fallback clause (*"else immediately before the BL rows"*) indicates the
intended direction; a heading at the entry point establishes an **id space**
rather than a row; and `BUG-` rows carry diagnosed defects, which are higher-signal
than the enhancement backlog. Noted here because it is a filing convention that
will be imitated, and imitating an unexamined choice is the failure the `(#TBD)`
rule was declared against. Moving it is one cut-and-paste if the reviewer prefers
the end.

## Ticket state

Committable. Four rows stand in the working tree: **BUG-001** (this ticket's own,
`fixed` not `verified`), **BL-190**, **BL-191**, **BL-192**. The post-commit
`drift_check --strict` is run at the commit and reported against the predicted
WARN set — `CLAUDE.md` and `docs/backlog-2026-06.md`, both `project_knowledge`
staleness. BUG-001 adds no member to that set.
