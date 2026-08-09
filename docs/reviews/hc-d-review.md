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

**Raised at:** harness `2d76a65`, agents `05a4cdb` + `88183b8`. **hc-d does NOT close at r0.**
Six findings; three require an edit, two of those are code. Findings verbatim, dispositions beneath.

### F1 — MUST FIX. §1a used `tail` for three gates. Done-check item 1 forbids it.

> Item 1, as authored and as this ticket transcribed it, reads *"full output, no `tail`, elisions
> stated"*. §1a states: *"`mix credo`, `mix test` and `mix dialyzer` are shown via `tail` of their
> own runs."*
>
> Stating the elision is the mitigation for an elision, not a licence for the one thing the item
> names. And the justification given — *"the elision is the progress dots and the log noise, not any
> result line"* — is a claim about what was cut, made by someone who published only what survived.
> It happens to be true here (0 failures, so there is no failure block to lose), but a `tail` on a
> red `mix test` cuts the failure details and keeps the summary, which is the exact shape where it
> would matter.
>
> The round immediately before this one published `mix test` in full — 135 lines, explicitly *"not
> elided"*. This is a regression against both the item and that precedent, inside the ticket whose
> subject is gates that pass without looking.
>
> Required: re-run the harness gate set at r1 and publish all six in full, no `tail`. If any output
> is genuinely unbounded, say which and why, and cut something other than what a failure would
> occupy.

**Disposition: ACCEPTED, fixed.** The finding is right and the justification it quotes was the
worse half of the error — I published only what survived and then characterised what I had cut.
All six gates are re-run at r1 and published in full at packet §1a. Nothing is elided, so there is
no elision to state. The regression against the immediately preceding round is the sharper point:
the precedent existed, in this same round, and I did not hold it.

### F2 — MUST FIX, code. `sleep 0.2` is the console capture's only drain guarantee, and the tail it can lose is the exit-contract summary.

> `sprint.sh` ends:
>
>     sleep 0.2
>     if [[ "$FAILURES" -gt 0 ]]; then exit 1; fi
>     exit 0
>
> with the comment *"give `tee` a moment to drain … without it the tail of the run can be missing
> from the very file kept for reading it back."*
>
> The comment diagnoses the problem correctly and then fixes it with a race. There is no bound on
> how long a process substitution's `tee` needs to flush; 0.2 s is an empirical guess made on an
> idle machine. This one thrashed itself to a standstill in swap earlier today — the conditions
> under which the drain is slow are exactly the conditions under which someone reads the log
> afterwards.
>
> And the tail at risk is not incidental. The last thing the sprint prints is the
> `Exit contract (BL-077)` block — the four counters this ticket exists to add. A truncated capture
> loses the verdict and keeps the run.
>
> Required:
> (a) Replace the sleep with a deterministic drain: capture the `tee`'s PID at the `exec`, close the
>     redirected descriptors before exiting, and `wait` on it. Derive the working form against this
>     bash rather than taking mine — if `$!` does not carry the process substitution's PID here, use
>     a named FIFO or a `coproc` and say which and why.
> (b) Prove it rather than asserting it: after a run, assert that `console.log`'s last non-blank line
>     is the last line the sprint printed. Make that assertion part of item 3's exercise so a future
>     regression trips it.
> (c) If no deterministic form is available in this shell, that is a permitted outcome — but then the
>     bound is *unknown*, not 0.2 s, and it is recorded in §Not established with what a truncated
>     capture would cost.

**Disposition: ACCEPTED, F2(a)+(b) applied; (c) not needed.** `$!` **does** carry the process
substitution's PID on this bash (5.1.16), derived by running it rather than assumed, so no FIFO or
`coproc` is required. The form: save the originals on fds 3/4 at the `exec`, capture `$!`, then at
exit restore fds — which closes the pipe and gives `tee` EOF — and `wait` on the PID. (b) is a
standing assertion in the script, not a one-off: the sprint prints a known last line, then checks
that the capture's last non-blank line matches it, and **increments `FAILURES` if it does not**, so
a future regression trips the gate rather than a reader's attention.

**One honest qualification, volunteered.** I could not make the `sleep` form truncate on this
machine — 20 000 lines through `tee`, and 3 000 through a deliberately slow line-at-a-time consumer,
five runs each, all arrived complete and the caller saw the sentinel every time. So the change
removes an unbounded wait **by construction**, and is **not** backed by an observed failure. That is
said in the code comment too, rather than letting a future reader infer the fix was
regression-driven.

### F3 — MUST FIX, code. R17(b) checks the row's SHAPE, not its EXISTENCE. `expected_fail BL-999 …` passes.

> The guard is `[[ ! "$ref" =~ ^BL-[0-9]{3}$ ]]`. Your own arm-(b) exercises used `<empty>` and
> `not-a-row` — both malformed. A well-formed reference to a row that does not exist takes the
> KNOWN-RED branch and silences the red.
>
> R17(b)'s wording is *"a `KNOWN_RED` entry whose evidence is missing, empty, or unparseable →
> failure, not 'known red'"*, and *"an entry naming no row is arm (b)"*. `BL-999` names no row. The
> justification the ticket gives for arm (b) — *"a declaration naming no backlog row declares
> nothing, and absent input is unknown rather than benign"* — applies to a dangling reference more
> sharply than to a malformed one, because a dangling reference looks correct.
>
> Required, either branch, not both:
> (a) Check existence against `docs/backlog-2026-06.md`. `sprint.sh` already reaches into the agents
>     repo for `drift_check.py`, so the coupling exists. If the row is absent, take arm (b).
>     Exercise it with a well-formed nonexistent row alongside the two shape cases already covered.
> (b) Or state the limit explicitly — the guard checks shape only — in the code comment, in the
>     runbook's `KNOWN_RED` paragraph, and in §Not established with a resolver. Then the gap is a
>     known bound rather than an unnoticed one.
>
> Choose on cost and say why. Do not do both.

**Disposition: ACCEPTED, branch (a).** **Why (a):** the cost is one `grep` against a path the script
can already reach, versus (b)'s cost of three documents carrying a permanent caveat about a gap that
one line closes. (b) is the right choice only when the check is expensive or unreliable; this one is
neither. A dangling reference is also the failure mode most worth catching, precisely because it
*looks* correct — (b) would have left the more dangerous half open and written it down.

Implemented as an **anchored heading match** (`^### BL-nnn `), not a substring search, so it is a
field match rather than a hit anywhere in a 7 500-line file. **Backlog unreadable is itself arm
(b)** — the gate does not assume a row it could not look for. Exercised with `BL-999` alongside the
two shape cases; all three fire.

### F4 — RECORD. The retention sweep counts before it deletes, and both the find and the `rm -rf` are bound to the working directory.

> Two things in the same block:
>
>     _pruned=$(find sprint … -mtime "+N" -print | wc -l)
>     find sprint … -exec rm -rf {} +
>     info "Retention sweep: pruned ${_pruned} run directories older than Nd"
>
> 1. `_pruned` is measured before the delete and reported as what the delete did. It is a prediction
>    printed in the past tense. If the `rm` partially fails — permissions, a race, a mount — the line
>    overstates and the failure is swallowed by `|| true`. Count what was removed, or word the line
>    as what will be attempted.
> 2. `find sprint` is relative to the working directory, not to the repo. Every other path in the
>    script resolves through `$(dirname "$0")/..`. As written, the retention sweep — including its
>    `rm -rf` — targets whatever `sprint/` directory happens to sit in the caller's cwd. `OUT_DIR`
>    has the same relative assumption and predates this ticket, but a cwd-relative `rm -rf` is new
>    and is this ticket's.
>
> Bind both to the repo root the way the rest of the script does. This is the command-binding carrier
> applied to a destructive command.

**Disposition: ACCEPTED, both fixed.** The `find` and the `rm -rf` are now bound to
`SPRINT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"`, and the printed root is part of the line so the
target is visible in the capture rather than inferred. The count is taken **after** the delete as
`candidates - remaining`, so it reports what happened; a non-zero remainder now raises a `warn`
instead of being swallowed. Point 2 is the one that mattered — the same class bit this very round,
in this ticket's own review work: a `git checkout` ran under a persisting `cd` and silently restored
nothing, which is recorded in the packet rather than quietly re-run.

### F5 — RECORD. The summary's two columns can legitimately disagree, and the runbook does not say so.

> `expected_fail`'s failure branch increments `FAILURES` without incrementing `BLOCKING_ARMS`. So a
> run whose only defect is a malformed `KNOWN_RED` prints `arms declared blocking … 0` beside
> `blocking failures … 1`, which reads as a contradiction to anyone who has not read the source.
> Your own §1c shows the shape: `FAILURES=4` against `BLOCKING_ARMS=1`.
>
> The behaviour is right — a malformed declaration is not a declared arm, and it is still blocking.
> Say so in the runbook's exit-contract section, in one sentence, so an operator meeting it does not
> read the summary as broken.

**Disposition: ACCEPTED, recorded.** One paragraph added to the runbook's exit-contract section,
covering the dangling case F3 adds as well as the malformed one, with the reading spelled out:
*"nothing was promoted, and something failed anyway"*, not a contradiction.

### F6 — RECORD. Item 8's artifact was produced on a dirty tree.

> The provenance stamp reads `harness_dirty: yes`, correctly — `sprint.sh` was modified when the run
> happened, and there is no way around that inside the ticket that modifies it. The stamp catching
> and printing it is the mechanism working.
>
> But item 5's `drift_check` was deliberately re-run post-commit for exactly this reason, and the
> sprint artifact was not, so the round's two pieces of evidence were held to different standards. At
> r1, after the F2/F3 commits land, re-run `./scripts/sprint.sh drift_check` once post-commit and
> publish that stamp alongside the r0 one. `harness_dirty: no` is what makes the artifact
> reconstructible from a commit, which is what G0 exists to protect.

**Disposition: ACCEPTED, done.** Re-run post-commit at r1; both stamps published side by side in the
packet, the r0 one reading `harness_dirty: yes` and the r1 one `harness_dirty: no`. The asymmetry
was real — one gate was held to the committed-tree standard and the other was not, in the same
round.

---

## Round 2

**Raised at:** harness `5782cbb`, agents `28741ae`. Two findings, both in F2's new code. Narrowly
scoped and pre-authorised to close — **but see the stop declared beneath F7.**

### F7 — MUST FIX, code. The drain assertion treats a MISSING capture as benign.

>     if [[ -f "$SPRINT_CONSOLE" ]]; then
>       _cap_last=$(grep . "$SPRINT_CONSOLE" | tail -1 || true)
>       if [[ "$_cap_last" == *"$_sprint_last_line"* ]]; then
>         ok "console capture drained complete (last line matches)"
>       else
>         echo -e "…TRUNCATED…"; FAILURES=$((FAILURES + 1))
>       fi
>     fi
>
> The outer `if` has no `else`. If `$SPRINT_CONSOLE` does not exist — `tee` failed to start, the
> directory was not writable, the process substitution never ran — the assertion is skipped
> entirely, nothing is printed, `FAILURES` is untouched, and the sprint exits 0 reporting a clean
> run with no capture at all.
>
> That is a strictly worse outcome than the truncation the assertion was written to catch, and it is
> the only one the assertion cannot see. It is also R17(b) inverted, in the same commit that
> ratified R17(b): *"absent input is unknown, not benign"*, and *"the gate does not assume a row it
> could not look for"* — the same reasoning you applied to an unreadable backlog, not applied to an
> unreadable capture.
>
> Required:
> (a) A missing or empty `$SPRINT_CONSOLE` is a failure on the same footing as a truncated one.
>     Increment `FAILURES`, with a message that distinguishes *absent* from *truncated* — they have
>     different causes and a reader needs to know which.
> (b) Exercise it: construct a run where the capture cannot be written, and show the sprint
>     reporting the absence and exiting non-zero. If the absence cannot be constructed here, say so
>     and say what you did instead.
> (c) The runbook's exit-contract section names three ways the gate fails. It is now four — a
>     capture that is missing or truncated. Add it, with the same "this will surprise you" framing
>     the healed-entry arm gets, because an operator meeting it will assume the sprint itself broke.

**Disposition: ACCEPTED, (a)+(b)+(c) applied.** Four states now, three of which fail, with **absent**,
**empty** and **truncated** reported distinctly. (b) was constructed in a *real run*, not simulated:
unlinking `console.log` mid-run leaves `tee` writing to the unlinked inode, so the run completes
normally while the file is gone from the directory — exactly the state the assertion must catch. The
sprint reported `console capture ABSENT` and exited **1**. (c) added as a fourth failure mode with
the three causes distinguished.

**The diagnosis is exactly right and worth restating**: it is R17(b) inverted in the same script that
ratifies R17(b). I applied absent-is-unknown to the backlog I read and not to the file I wrote.

> **STOP DECLARED — a defect found in this round's own shipped code, not in the review procedure.**
>
> F7(b)'s first exercise exposed it. With the capture absent, the sprint exited **1** while its
> summary block had already printed `blocking failures … 0 → sprint will exit 0`. **The tally and
> the exit code contradicted each other**, in the block this ticket exists to add.
>
> **Cause, and it is structural rather than a typo.** The capture assertion cannot run until the
> capture has drained; the drain cannot run until all captured output — including the summary — has
> been written. So any `FAILURES` increment from the capture check necessarily lands *after* the
> tally is printed. This predates F7: it arrived with F2(b) at r1, where a *truncated* capture would
> have produced the same contradiction. F7 did not create it; F7's exercise is what made it visible.
>
> **Fixed, and the fix is reported rather than folded in silently.** The in-capture block is now
> labelled **provisional** and says why, and a **FINAL** tally prints after the capture check on the
> restored stdout — the one that can be compared against `$?`. Verified: the absent-capture run now
> prints `blocking failures … 1 → exit 1` and exits 1.
>
> **I am not claiming closure on my own authority.** The pre-authorisation says a new defect in F7's
> fix is a stop. This one is adjacent rather than inside — it is in the interaction between F2(b)'s
> assertion and r0's summary — and that distinction is the reviewer's to make, not mine, since the
> last round's ambiguity of exactly this kind was resolved in my favour and I should not assume it
> twice. Everything else in the pre-authorisation is met.

### F8 — RECORD. R17(c) is available but not automatic.

> `expected_fail` fires in an arm's failure branch; `known_red_healed` has to be called in its pass
> branch. Nothing enforces the pairing. An arm written with `expected_fail BL-0xx` on failure and a
> plain `ok` on success accepts a healed red silently — which is precisely the defect R17(c) exists
> to remove, surviving in every arm whose author forgets the other half.
>
> `[V: establish whether `known_red_healed` has any call site in `sprint.sh` at all, or exists only
> as a helper exercised by sourcing. Report the count with its command; do not take mine.]`
>
> This is not live — there are zero `KNOWN_RED` arms today — which is exactly why it is worth
> writing down before the first one is added.
>
> Required, record only, no mechanism this round:
> (a) State the convention explicitly where the helpers are defined: an arm declared `KNOWN_RED`
>     wires BOTH branches, or arm (c) does not exist for it.
> (b) File it in §Not established with a resolver — whether the pairing should be enforced
>     structurally (one helper taking the arm's own condition, rather than two the author must
>     remember) is a design question this ticket does not have to settle, and the first `KNOWN_RED`
>     arm is when it must be.

**Disposition: ACCEPTED, `[V]` confirmed, (a)+(b) applied.**

**The `[V]`, derived rather than taken.** `grep -nE 'known_red_healed' scripts/sprint.sh` → **one
line**, `:142`, the definition. **Zero call sites.** `expected_fail` the same: `:106`, definition
only. **Positive control**, identical form over a helper that is called: `blocking_ok` → 2
occurrences, definition plus a real call site at `:1584`. So the pattern finds call sites where they
exist, and both `KNOWN_RED` helpers exist only as helpers exercised by sourcing — as the finding
says.

(a) The convention is stated at the helper definitions with the two-branch shape written out.
(b) §Not established **item 12 `[OPEN]`**, with the structural-enforcement question named as the
open design decision and **the first `KNOWN_RED` arm's author** as its resolver.

### Promotion candidate — transcribed

**A restore is verified, not assumed.** Added to §Promotion candidates verbatim as authored.

---

## Round 3

**Raised at:** harness `2ebc59c`, agents `2b62192`. **r2's stop did NOT fire** — the reviewer
adjudicated the defect as originating at F2(b) and merely *exposed* by F7(b), one floor below F7's
fix. Two new findings.

### F9 — MUST FIX, code. The authoritative tally is not in the durable record, and the record's own last line calls the provisional one the verdict.

> The FINAL block prints on restored stdout, after the drain. So it is not in `console.log`. What
> `console.log` contains is:
>
>     blocking failures ............... 0
>     → sprint will exit 0 unless the capture check below changes it
>     (provisional — the console-capture check runs after the drain; final tally follows it)
>     …
>     Sprint finished — exit contract above is the verdict.
>
> The final tally that follows is nowhere in the file, and the last line in the file asserts that
> the block above it — the one labelled provisional — is the verdict. Both sentences are
> individually true when read live at the terminal. Read back from the file in six weeks, which is
> the entire purpose of BL-133 face 2, they are a durable record that misstates its own verdict.
>
> The provisional/final split was the right fix for the contradiction. It moved the authoritative
> number out of the artifact kept for reading the run back.
>
> Required:
> (a) After the drain and after the capture assertion has run, append the FINAL block to
>     `$SPRINT_CONSOLE` directly. `tee` has exited by then, so a plain append is ordered and safe —
>     do not route it back through the capture.
> (b) Append ONLY when the capture exists and is non-empty. If it is absent or empty, the record is
>     already declared broken; recreating the file with a verdict and nothing else would make a
>     broken record look like a short one. Say in the code why the append is conditional.
> (c) Fix the sentinel. `Sprint finished — exit contract above is the verdict.` must stop pointing at
>     the provisional block. Reword it, and keep the sentinel string and the assertion's compare
>     string as **one variable** so they cannot drift apart.
> (d) State the ordering explicitly in the code: drain → assert → append. The assertion compares the
>     last line against the sentinel *before* the append, so after the append the file's last line is
>     the final tally and the assertion would no longer hold if re-run. That is correct and it is the
>     kind of thing that reads as a bug to the next person unless it is written down.
> (e) Show `console.log`'s tail in the packet for both a passing run and the absent-capture run, so
>     the record's own ending is visible rather than described.

**Disposition: ACCEPTED, (a)–(e) applied.** The finding is exactly right and the diagnosis is the
part worth keeping: **r2's fix cured the contradiction by moving the true number out of the artifact
that exists to carry it.** Live at a terminal both sentences were true; as a durable record the file
asserted a verdict that was not the run's.

(a) FINAL block appended directly after drain and assertion; `tee` has exited, so the append is
ordered and is not routed back through the capture. (b) Guarded on exists-and-non-empty, with the
reason in the code — a broken record must stay visibly broken rather than become a confident tally
over no run; **verified both ways**, the absent run leaves no `console.log` at all and the guard
refuses to pad a zero-byte file. (c) Sentinel reworded to point *forward*; it was already one
variable for print and compare and remains so — that shared variable is the only thing preventing
this assertion from going quietly vacuous. (d) Ordering stated, including the consequence: after the
append the file's last line is the FINAL block, **so re-running the assertion over the finished file
would fail**, which is correct because the assertion is about the drain, not about the file's
permanent ending. (e) Both tails published in the packet.

### F10 — MUST FIX. §1g published a command with no output and no statement.

> §1g ends:
>
>     $ grep "Retention sweep" console.log
>
> with nothing beneath it and no comment. r1's §1g ran the same command and published
> `[INFO]  Retention sweep: pruned 0 of 0 run directories older than 30d (root: …)`.
>
> Exactly one of two things is true and neither is stated:
> - The retention line is missing from `console.log` at r2 — a real regression, since the sweep runs
>   after the `exec >` redirect and should be captured.
> - The output was dropped when the packet was assembled — packet-integrity, the carrier you named
>   yourself at hc-c r2 §8a.
>
> Required: establish which, with the command bound and its output published. If the line is
> genuinely absent, that is a new defect and a stop — report it, do not fix it inside a closing
> round. If the packet dropped it, say so and name it as the carrier's next instance.
>
> An empty result is a result. A command published with nothing beneath it reads as "ran, nothing to
> say", which is the same silence the exit-contract block was built to remove.

**Disposition: ACCEPTED — and it resolves to a THIRD thing, so the stop does not fire.**

**Neither disjunct is true.** The retention line is **not** missing from the sprint's output, and
the packet did **not** drop it. The grep really did return empty, and it returned empty because it
was pointed at the wrong artifact: **§1g selected the run directory with `ls -1dt | head -1`, and
the newest run at that moment was the EMPTY-state test run** — the one whose `console.log` I had
been repeatedly truncating with a watcher seconds earlier. My own test had erased the line from that
specific file.

Established, bound, and published in the packet: the retention line is present in every
uncorrupted run (`132413` → 1, `131128` → 1, and the r3 passing run → 1 at `:3`), and absent only
from `132417`, which `r2empty.txt` names as the EMPTY-state run. Positive control on the same file:
`grep -c 'Exit contract'` → 1, so the file is readable and the pattern works.

**So it is the carrier's next instance after all, in a form neither of us named: an artifact
selected by RECENCY rather than bound to its purpose.** `ls -1dt | head -1` is the command-binding
failure with a timestamp in place of a path — and it hit twice in the same packet, because **r2's
item 8 provenance stamp came from that same corrupted run**. Its contents were accurate, but it was
published as clean-post-commit evidence while being drawn from a run I had deliberately broken.

**Fixed in method, not in code:** every run directory in this packet is taken from **the run's own
output** (`grep -o 'sprint/20260809_[0-9]*'` over the run's stdout), never from `ls -t`.

**And the finding's standing rule is upheld against my own packet:** an empty result is a result. I
published a command with nothing beneath it, which read as "ran, nothing to say" — the same silence
the exit-contract block exists to remove.
