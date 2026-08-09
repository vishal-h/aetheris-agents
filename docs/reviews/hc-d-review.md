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
