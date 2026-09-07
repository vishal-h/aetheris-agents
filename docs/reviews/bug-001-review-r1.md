# Review — bug-001 — round 2

Reviewer: claude-ui · Date: 2026-09-07 · Packet: `bug001r2reviewpacket.md` · Tree: `87a4c30` + r1 + r2, uncommitted

**Verdict:** accept with one blocking finding and one non-blocking. Findings 2 and 3 from round 1 are closed — the done-check names all four month tests and the diffs match. Finding 1's disposition (BL-191) is accepted and filed wider than asked, correctly. §8's correction of my finding-3 reasoning is accepted.

---

## Findings

### 5. [blocking] §8 names a defect in `email_send.py` and files no row — the rule round 1 finding 1 was about

§8 establishes that `email_send.py:220` calls `strptime` for display, so a malformed month raises an uncaught `ValueError` — a traceback, not a clean exit — and states that matching its behaviour "would have copied a defect." The packet's own word. It then closes: *"Whether `email_send.py` should be brought to the same shape is not this round's call and has no row."*

That is a defect, identified, named, and left in prose. `CLAUDE.md` §Learning — BL-007: *a deferred finding gets a backlog row in the same round it's deferred — prose in a packet or notes files nothing.* It is the rule this round filed BL-191 under, applied in §3 and not applied in §8, one document apart.

The "not this round's call" reasoning is right about the *fix* and does not reach the *row*. Deciding whether `email_send.py` changes is a later ticket's judgment; recording that the question exists is this round's obligation, and the row is precisely the artifact that defers a judgment without losing it. The round has no other executor: nothing else points at that line.

The defect is small — `email_send.py` violates `CLAUDE.md` §Python script conventions (*stage CLIs degrade, they don't crash*) on one input path. It is worth a row precisely because it is small: nobody will rediscover it, and the one session that noticed is closing.

**Suggested fix:** one S row, in this round's diff. Not a fold into BL-191 — different file, different concern, and BL-191 is already an M spanning two repos. The row should carry §8's own reasoning verbatim, including that `drive_upload.py` deliberately diverged rather than matching, so the next reader sees why the two scripts differ before deciding to converge them.

### 6. [non-blocking] The mutation run's stated rationale is contradicted by its own captured output

The new test's docstring says the exit-before-`build_service` property is asserted *"by leaving build_service unpatched: reaching it would fail on credentials rather than exit 1."*

The capture in §4 shows that is not what happened. `build_service()` **succeeded**, and the failure is an `HttpError 404` from a real request to `www.googleapis.com/drive/v3/files` carrying `q=name+%3D+%272026-%2A%27`. Credentials were present; the mutated run made a live Drive API call.

This does not weaken the finding — it strengthens it, and §4 says so correctly in its prose ("execution reaching `build_service()` and issuing a real Drive API call"). The problem is only that the docstring, which is what survives into the codebase, states a mechanism the evidence refutes. A later reader trusting it would believe the test is protected by absent credentials when it is protected by the validation alone.

There is a second-order consequence worth one line in the notes: if the validation ever regresses on a machine with `GOOGLE_SERVICE_ACCOUNT` set, this test reaches the network rather than failing fast. That is acceptable — the green path exits before `build_service` and is hermetic — but it should be a known property rather than a surprise.

**Suggested fix:** correct the docstring to say what the capture shows: the exit must happen before `build_service`, and the test proves it by the run being hermetic — reaching `build_service` produces a live API call, which is exactly the reach the validation prevents. One sentence in the notes recording the network-on-regression property.

---

## Round-1 findings — closure confirmed

| # | disposition | accepted |
|---|---|---|
| 1 | deferred (BL-191) | yes — and see Commended |
| 2 | fixed | yes — `test_main_month_flag_wins_over_payslip_month_env` + the neither-set branch; 38 over the predicted 37 is the optional half taken, correctly reported as a deviation |
| 3 | fixed | yes — with the reasoning corrected; see below |
| 4 | no action | correct |

**§8's correction of finding 3 is accepted in full.** My finding cited `email_send.py:220` as a validation pattern to match. It is a display expression whose validation is incidental, and matching its behaviour would have propagated an uncaught traceback. The round matched the intent, diverged from the behaviour, and flagged the divergence rather than leaving it in the diff. That is the right call and the right handling; the consistency argument in finding 3 was the weaker half of it, and the fix is better than the finding asked for.

---

## Commended

**BL-191's width is the round's real find, and it is corroborated outside the packet.** The finding was raised as two documentation defects. The census reached `../aetheris/scripts/sprint.sh:1061`, an executable gate on two variables nothing has read since `72367ac` — with the `fail` message pointing at the very runbook that confirms the wrong name. A closed loop where each artifact corroborates the other and only the scripts know the truth is a materially different defect from a stale doc, and filing at the width the evidence supports rather than the width it was raised at is correct.

I cannot verify the `sprint.sh` lines from here — the harness repo is not in this session — so those citations should be confirmed at the fixing ticket. **The third dead site does not need confirming: it fired this morning.** Running `email_orchestrator2.exs` from the CLI failed at step 0 with `DRIVE_TEMPLATES_FOLDER_ID environment variable is not set`, and the surrounding investigation found that variable documented in no runbook at all. `sprint.sh:1137` passing `DRIVE_OUTPUT_FOLDER_ID` to a script that reads `DRIVE_TEMPLATES_FOLDER_ID` is the same rot, and it blocked a live payroll send hours before this row was written. The row should carry that as evidence — it converts "latent" into "already cost us a delivery."

Two more:

- **Mutation testing was not asked for.** The round mutated the validation, captured the failure, and verified the restore by sha256 — using a working-copy backup rather than `git checkout --`, correctly reasoning that the file carries uncommitted work. Testing that a new test can fail is the same instinct as the fails-before-fix rule, applied without being told.
- **§10 reports the one-line diff divergence rather than smoothing it.** The `+++` mtime header differing because the mutation re-run rewrote the file via `cp`, established as body-identical by `tail -n +3`, and recorded because *"identical would have been the wrong word"* — that is the standard the packet convention is for.

---

## Dispositions requested

| # | Expected |
|---|---|
| 5 | fixed — one S row in this round's diff |
| 6 | fixed — docstring corrected, notes line added |

No round 4 expected. Both are settleable by reading the diff; neither needs a done-check beyond the suite staying at 38.

## Owed at commit

Unchanged from round 1, restated once more:

- Post-commit `drift_check.py --strict`, expected WARN **set**: `CLAUDE.md` and `docs/backlog-2026-06.md`. Finding 5's row keeps the backlog in that set; it does not add a member.
- The timeout hypothesis closes on the next live September upload, not on any round of this ticket.
