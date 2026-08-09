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

**Raised at:** agents `1f82118` / harness `e8889c3`. **Verdict on the round as a whole, verbatim:**
*"the gate is sound, both rows are closed on real evidence, and BL-106's consumer enumeration is
the standard the rest of the ticket should have been held to. Five findings, three of which
require an edit."*

### Findings, verbatim

> **F1 — MUST FIX. The BL-105 change is global; its consumer enumeration is not.**
>
> `route_logging_to_stderr/0` runs on the boot path unconditionally. It moves Logger for **every**
> invocation and every mode — `--json`, `--quiet`, human, `server`, escript, release — not only for
> `--json`. BL-105's Done-when is about the `--json` payload stream; the implementation is broader
> than the row.
>
> The implementation is probably right (diagnostics on stderr is the convention, and the gate makes
> it coherent with the worker's lines). That is not what is wrong. What is wrong is the asymmetry:
> for BL-106 you enumerated **every** consumer of the error values before touching the first, and
> named `fork.ex` as the only interpolating site. For BL-105 you moved an entire stream for every
> entry point and the packet shows verification of two consumers (Rig, and `sprint.sh` via R11's
> guard) — both of which happen to be `--json` readers.
>
> Nothing in the packet establishes that no consumer read *harness log output* on stdout. That is
> absent-is-unknown: the absence of a known reader is not the established absence of readers.
>
> Required:
> (a) Enumerate the consumers of harness stdout that are NOT `--json` payload readers. At minimum
>     sweep `scripts/sprint.sh` and any other in-repo script or Rust/TS call site that captures
>     harness stdout — including stdout-only captures, and including greps over log text rather
>     than over JSON. Name the population you swept and print the enumeration beside the count.
> (b) If the sweep is clean, say so with its population named. If you cannot make it exhaustive,
>     say *that*, and record the residue in §Not established rather than letting a clean-looking
>     sweep stand for a complete one.
> (c) The runbook section is titled "The `--json` output contract" and its first property describes
>     a change that is not `--json`-scoped. Retitle or restate so a human-mode reader who greps
>     stdout for a log line is not surprised by a section they had no reason to read.

> **F2 — MUST FIX. §Not established item 1's resolution overstates its observation.**
>
> The resolution reads "They route to stderr" on an observation of **two** lines. Those two are the
> success-path pair. The question was about `[sandbox]` routing as a class, and the class has many
> more emission sites than the two that fired — hc-b2 §G3(3)/§G3(4) recorded a count for
> `../aetheris/native/aetheris_worker/src/{sandbox.rs,main.rs}`; derive that count from source
> rather than carrying hc-b2's number or mine.
>
> The generalization is almost certainly sound, and its truth-maker is a derivation, not this
> observation: every site is `eprintln!`, and `../aetheris/lib/aetheris/worker/client.ex`
> `port_options/1` sets no `:stderr_to_stdout`, so worker fd 2 is inherited rather than folded into
> the port. State it that way. Amend the resolution block in §Not established item 1 to separate
> the two:
>
> - **Observed:** N lines on this run, all in stderr.txt, 0 in stdout.txt — the success-path pair.
> - **Derived, not observed:** the remaining sites route identically, because each is `eprintln!`
>   and the port sets no `:stderr_to_stdout`. Cite both anchors with line numbers as parentheticals.
>
> A resolution that reads as fully observed when part of it is derived is the
> resolved-versus-advertised shape you named in your own §3.

> **F3 — MUST FIX. The stale status surfaces are hc-c's to fix, not hc-d's.**
>
> You were right that a status edit was not inside your three authorised amendments, and right to
> name it rather than fold it in silently. That was the correct call at the time you made it. It is
> now authorised: hc-c is what made those surfaces false, and a canonical document that says hc-c
> is *Not started* while hc-c is closed is a live false claim carried across a ticket boundary —
> exactly the shape this round exists to stop.
>
> Update, section-scoped, in this round: the document header's status line and §Ticket set's hc-c
> row. Do not touch hc-d's or hc-e's rows. Diff both.

> **F4 — RECORD. The merged-capture ordering guarantee changed, and the runbook does not say so.**
>
> Before hc-c, the payload and the Logger lines were written to one stream, so their relative order
> in any capture was fixed by a single write sequence. After hc-c they are two
> independently-buffered devices, and a `2>&1` capture interleaves them in an order that is no
> longer guaranteed.
>
> Neither in-repo consumer is harmed — `json_read`'s backward scan looks for the last *parsing*
> object and a Logger line does not parse; Rig reads stdout alone, which is now payload-only.
> Verify both of those claims rather than taking them from me. But the runbook currently says only
> that a `2>&1` capture "merges them back into one file by your choice, and a reader of that file
> still has to scan." Add that the merged order between the two streams is not guaranteed, and that
> this is why a reader must scan for a parsing object rather than rely on position. One sentence.

> **F5 — RECORD. The BL-075 green is reported without the fact that hc-c edited the flake's own
> module.**
>
> Notes §7 says `mix test` is green and "nothing was watching when it changed." hc-c's own diff
> touches `../aetheris/lib/aetheris/cli/commands/run_helpers.ex` and
> `test/aetheris/cli/commands/run_helpers_test.exs`, and BL-075's flake was named at m4 close-b as
> `Aetheris.CLI.Commands.RunHelpersTimeoutTest` — the same module family. The packet shows no
> pre-edit `mix test` on this tree, so "green because of this ticket" and "green despite it" are
> not distinguished by the evidence here.
>
> The changes are return-shape only and almost certainly timing-neutral. Say that, and say that it
> is a reasoning-from-source claim rather than a measurement. Amend the §7 bullet and BL-075's row
> note accordingly. Do not re-run to chase a red — a single green does not refute a flake and a
> single red would not confirm one.

**Accepted without action, verbatim:** the gate's verdict on a failed run (*"Not re-running was
correct and the reason you gave for not re-running is the right reason"*); the
fork-that-starts-then-fails gap (*"Named honestly … That is the correct disposition; no further
work"*); BL-106's consumer enumeration and the `error_message`/`error_payload` pair with no
catch-all (*"Both exemplary. F1 asks BL-105 to be held to this"*); A3's re-placement and the
two-hunks-three-amendments note (*"the note pre-empts exactly the misread it names"*).

### Dispositions

| Finding | Disposition |
|---|---|
| **F1(a)** — enumerate non-`--json` consumers | **done.** Population named (39 files, both repos, executable extensions, four search terms recorded); 5 are real consumers; **0 read log text from stdout**. Enumeration printed with the counts beside it in `hc-c-implementation-notes.md` §7. sprint.sh derived separately: 92 invocation lines, **0** stdout-only text reads |
| **F1(b)** — clean vs exhaustive, into the document | **done.** Result in BL-105's closure record; residue as **§Not established item 6** — the sweep cannot reach an operator's own pipeline, anything outside these two repos, or an invocation none of the four terms matched. Stated as *clean, not exhaustive* |
| **F1(c)** — runbook title and scope | **done.** Retitled *"Output streams, and the `--json` contract"*, with an explicit note that property 1 applies to every invocation and mode, property 2 only to `--json`, and that human-mode command output stays on stdout |
| **F2** — separate observed from derived | **done.** Observed (2 lines, 2/0) and derived (16 emission sites, **16 of 16 `eprintln!`, 0 `println!`**) split, with anchors as parentheticals and a dated amendment note. **The count was re-derived from source**, not carried from hc-b2 or the finding |
| **F3** — status surfaces | **done.** Header line and hc-c's row only; hc-d's and hc-e's untouched. Written **after** the gates ran, so *Closed* is not a claim landing in the commit that makes it true |
| **F4** — ordering guarantee | **done.** One paragraph added. Both claims verified from source first, not taken: `json_read`'s implementation is `for line in reversed(lines)` with `continue` on `ValueError`; `orchestrate.rs` keeps only JSON-parsing stdout lines with `stderr(Stdio::null())`, `fork.rs` reads stdout alone |
| **F5** — BL-075 qualification | **done**, and sharper than the finding asked. The flake's own file is **not** in hc-c's diff; the assertion it flakes on is the `:done` success path, which hc-c did not touch; the branch it failed into is unchanged; no timing/poll/window touched. Stated as reasoning from the diff, not a measurement. Amended in the notes and on BL-075's row. Not re-run |

**One correction to the finding text, offered rather than pressed.** F5 says hc-c touches
`test/aetheris/cli/commands/run_helpers_test.exs` and calls that "the same module family" as the
flake. Both true — but the flake lives in a **different file**,
`run_helpers_timeout_test.exs`, which hc-c does not touch at all (last modified at `a935038`,
BL-031 r2). The finding's substance is unaffected: `run_helpers.ex`, which hc-c *does* edit, is the
module that file exercises, so the qualification was owed either way.

**Closure.** Conditions 1–4 of the pre-authorisation are met: the sweep ran with its population
named and enumeration printed (1), F1(c)/F2/F3/F4/F5 applied and diffed (2), the harness gates
re-ran clean after the edits (3), and **no code changed** — r1 touches only the runbook and
documents (4). The sweep found no broken consumer, so the stop-and-report branch of condition 4
did not fire.

> **`[amended 2026-08-09 (hc-c r2)]` — the closure claim above did not hold, and two of its
> supports were defective. Recorded here rather than rewritten, per decision 7.**
>
> - **hc-c did not close at r1.** Round 2 was raised. The disposition table above stands as the
>   record of what r1 *did*; the closure paragraph's conclusion is superseded by §Round 2.
> - **Condition 3's evidence was partly broken as published.** The r1 packet's `drift_check`
>   block printed a command that had failed to run (wrong repo, persisting `cd`) beside an
>   `exit=0` that belonged to no invocation — **F6**. The harness gates in that packet were real;
>   the `drift_check` block was not. Re-run bound explicitly at r2: 0 FAIL, 3 WARN, exit 0, same
>   WARN set. See §Round 2, F6.
> - **F3's edit left the document self-contradictory** — the header said hc-b was closed while
>   §Ticket set still said *In review*. **F7**, fixed at r2.
> - **F1(a)'s term list was incomplete**, demonstrated by r1's own sprint.sh analysis. **F8**,
>   re-swept at r2: population 39 → 48.

---

## Round 2

**Raised at:** agents `3d5a8da` / harness `1b09b23`. **Opening verdict, verbatim:** *"F1 through
F5 are all discharged, and F1(a)'s sweep and F2's derivation are the best work in this round —
population named, terms recorded, enumeration printed beside every count, residue stated as
residue. The four findings below are what r1 introduced or left, not a re-litigation of r0."*

### Findings, verbatim

> **F6 — MUST FIX, AND IT BLOCKS CLOSURE. The r1 done-check asserts a `drift_check` result it does
> not have.**
>
> §1e of the r1 packet reads, in full:
>
>     python3: can't open file '/home/it/sandbox/elixirws/aetheris/scripts/drift_check.py':
>     [Errno 2] No such file or directory
>
>     exit=0
>
> and is followed by: *"Zero FAIL. The same three `project_knowledge` staleness WARNs, all exempt
> and all named."*
>
> **The command did not run.** The result reported beneath it is carried from r0, not observed at
> r1. Three separate defects, and each is a carrier this round has already promoted or ratified:
>
> 1. **Command binding.** `drift_check.py` was invoked against a harness path. Its output at r0
>    identifies it as the Rig doc-drift checker, and the F1(a) sweep you just ran lists
>    `aetheris-agents/tests/test_drift_check.py` — it is an agents-repo tool. This is the
>    command-binding carrier of silent-wrong-answer verbatim: *bind every command to its target
>    explicitly*.
> 2. **`exit=0` is not this command's exit code.** A `python3` file-not-found exits non-zero.
>    Whatever produced that `0` was bound to something other than the invocation whose stderr is
>    printed above it. A packet that prints a failure and an exit code that contradicts it is
>    reporting two things that cannot both be true and asserting neither.
> 3. **A count carried across a state change.** "The same three WARNs" is a claim about the
>    manifest-versus-git comparison *after* r1's four document commits. r1 changed the very files
>    those WARNs are about. The number may well still be three — it is not established, and it is
>    the third carrier of the promoted count rule: a count taken over a capture that was never made.
>
> Required:
> (a) Locate `drift_check` by finding it, not by assuming its path. Run it `--strict` from its own
>     repo, bound explicitly, post-commit.
> (b) Print its full output and its real exit code, captured from the invocation itself.
> (c) State the WARN set as observed at r2 — with the manifest and current hashes as printed —
>     rather than as "the same three".
> (d) If the WARN count or membership differs from r1's assertion, say so plainly and correct the
>     r1 record in `docs/reviews/hc-c-review.md` §Round 1 with a dated amendment note. Do not
>     rewrite the r1 disposition table in place.
>
> This is the finding that keeps hc-c open. Everything else below is small.

> **F7 — MUST FIX. F3's edit made the document contradict itself.**
>
> The header now reads *"hc-a, hc-b and hc-c closed; hc-d next."* §Ticket set's `hc-b` row still
> reads **In review** — visible as an unchanged context line in r1's own hunk 2. Two status
> surfaces in one document now disagree.
>
> That is my finding to own: F3 scoped the edit to "the header's status line and §Ticket set's
> hc-c row" and you applied it exactly as written, including the instruction not to touch
> neighbouring rows. Following a scope faithfully and surfacing what it broke is the right
> behaviour; the scope was wrong.
>
> Required:
> (a) Bring §Ticket set's `hc-b` row into agreement with the header. Its disposition is **closed**
>     — hc-b's review rounds concluded and hc-b2 was opened and closed as a separate repair ticket
>     against hc-c's specification, not as an open hc-b round. Record the closing commit if the
>     document's other closed rows carry one; match the shape those rows already use rather than
>     inventing a new one.
> (b) Check whether §Ticket set has a row for **hc-b2** at all. R12 says a ticket's anatomy is
>     written into the canonical document before that ticket opens; if hc-b2 has no row, that is a
>     live R12 gap and it should be filed — either as a row now, or as a §Not established entry
>     naming what is missing and why. Do not guess which; establish whether the row exists first.
> (c) Sweep every remaining status surface in `hc-consolidation.md` — not only the two F3 named and
>     the one this finding names. Name the population you swept (the set of places the document
>     states a ticket's state) and print it, so the next reader does not have to rediscover which
>     surfaces exist. This is the census discipline applied to the document's own claims about
>     itself.

> **F8 — MUST FIX, bounded. The sweep's term list demonstrably misses a spelling that exists in the
> repo.**
>
> F1(a)'s population is defined by four terms: `mix aetheris`, `./aetheris`, `["mix", "aetheris"]`,
> `"aetheris".to_string`.
>
> Your own sprint.sh analysis then uses a *different* population — including `mix run --eval`, with
> the reason given explicitly: *"it boots the app, so `route_logging_to_stderr/0` runs there too."*
> That reason is correct and it is general. It is also not one of the four terms, so for the other
> 38 files `mix run --eval` was never searched for.
>
> The residue you recorded at §Not established item 6 says the sweep may miss "an invocation whose
> spelling none of the four terms matched." F8 upgrades that from a hypothetical to a demonstrated
> gap: you found such a spelling, in the repo, and handled it in one file only.
>
> Required:
> (a) Re-run the sweep with the term list extended to cover boot-path invocations that are not
>     spelled `mix aetheris` — at minimum `mix run`, and any `System.cmd` / `subprocess` /
>     `Command::new` construction of an Elixir or harness invocation. Derive the extended term list
>     from what actually boots the app rather than from my list.
> (b) Print the new population count and its enumeration beside the old, so the two can disagree in
>     public. If the new files are all prose or all merged captures, say so per file.
> (c) Amend §Not established item 6 to state the extended terms, and to record that the first term
>     list was found incomplete by its own sprint.sh analysis. A residue statement that was written
>     before the gap was known should not be left reading as though it anticipated it.

> **F9 — RECORD. The hc-d/hc-e untouched check is a negative with no positive control.**
>
>     git show 3d5a8da -- docs/milestones/hc-consolidation.md \
>       | grep -c "^[+-]| \*\*hc-[de]\*\*"  ->  0
>
> A `grep -c` returning 0 is evidence only if the pattern is known to match when the thing it looks
> for is present. A malformed pattern, a wrong escape, or a `|` that is literal rather than
> alternating all return 0 identically. This is the same shape your own step-1 gate was built to
> avoid — the gate ran a positive control first precisely so a zero could be read as absence rather
> than as breakage.
>
> Required: either re-run it with a positive control (the same pattern against `hc-c`, which you
> know changed, returning non-zero), or replace the check with one whose negative is unambiguous.
> Then record the result. No document change beyond the notes.

**Accepted without action, verbatim:** F1(a)'s sweep as method (*"F8 exists because you documented
your method well enough to be checked"*); F2's derivation (*"the promoted count rule discharged
properly"*); the status line written after the gates ran; **F5's correction accepted** (*"Your
version is the accurate one and it is already in the record. No further action."*); F1(c)'s runbook
restructure and F4's ordering paragraph; and the quieter-sprint observation.

### Dispositions

| Finding | Disposition |
|---|---|
| **F6(a)** | **done.** Located by `find`, not assumed: `aetheris-agents/scripts/drift_check.py` is the **only** copy; the harness path never existed. Re-run post-commit, bound by absolute path, from the agents repo |
| **F6(b)** | **done.** Full output printed; **exit captured from that invocation** via `$?` immediately after it — **0**. The r1 defect is also evidenced rather than conceded: the broken invocation reproduces at **exit 2**, against the `exit=0` r1 printed |
| **F6(c)** | **done.** WARN set stated as observed at r2 with both hashes per row, not as "the same three" |
| **F6(d)** | **does not fire, recorded explicitly.** Count, membership and hashes are identical to r1's assertion. §Round 1 carries a dated amendment note anyway — its closure paragraph rested on a block that had not run — and its disposition table is **not** rewritten |
| **F7(a)** | **done.** `hc-b` → **Closed** 2026-08-08 at r1, in the shape the other closed rows use, with commits (`e8cd5cd`→`a581a8c`, harness `b4d782a`) and hc-b2 named as its repair |
| **F7(b)** | **established, then filed as a §Not established entry (item 7), not as a row.** There is **no** `hc-b2` row and no `### hc-b2` subsection — six source-citations only. **Why not a row:** authoring anatomy now would place it after the ticket closed, which is what R12 exists to prevent, and anatomy is the reviewer's to author (decision 11, R12). The gap is named and the remedy left to whoever takes it. A note under §Ticket set records that *"Five tickets"* is the planned set, not a census of what ran |
| **F7(c)** | **done.** Population named (every place the document states an `hc-*` ticket's state), 26 vocabulary hits classified, **7 surfaces** printed as a table in the notes §8b. **It found two stale surfaces, not one** — hc-b's row, and **hc-c's own row claiming closure at r1**, which r2 denies; both corrected. One adjacent surface (§Rows filed's *"Empty at hc-b"*) named as checked-and-still-true |
| **F8(a)** | **done.** Terms derived from what boots the app (`route_logging_to_stderr/0` runs in `Application.start/2`), not from the finding's list: `mix aetheris`, `mix run`, `mix test`, `mix eval`, `iex -S mix`, `./aetheris`, `["mix", …]`, `System.cmd("mix")`, `Command::new("mix")`, `subprocess … "mix"` |
| **F8(b)** | **done.** **39 → 48, nine added, zero lost** (superset checked, not assumed). Per file: **four are prose** (harness `.exs` comments about `mix test`), **five are real consumers** — the provenance pytest suites spawning `["mix","run","--eval",…]` with `capture_output=True`. **None broken; all helped** — their four stdout reads are whole-stdout `json.loads`, which boot output on stdout would have broken. 41 tests pass on the changed harness; the boot path confirmed by running one test's exact command (stdout **0 bytes**, three `[Aetheris.Application]` lines on stderr) |
| **F8(c)** | **done.** Item 6 amended with the extended terms and with the record that the first list was found incomplete **by its own sibling analysis, before any reviewer read it** — the residue sentence no longer reads as though it anticipated the gap |
| **F9** | **done.** Positive control run: the same pattern against `hc-c` returns **2** (both diff lines printed), the `hc-[de]` pattern returns **0**. The zero now reads as absence. Recorded in the notes §8d |

**A count error of my own, found and corrected inside this round.** Discharging F8 I first counted
the provenance tests' stdout/stderr reads with `grep -c … test_*.py`, which globs every test in
that directory rather than the five under discussion — 21 and 18 against an enumeration showing 4
and 11. That is *a count printed beside an enumeration that contradicts it*, produced while
discharging a finding about population discipline. Corrected by binding the count to the five files
by name; recorded in the notes §8c rather than silently fixed.

> **`[amended 2026-08-09 (hc-d, R-i) — F8(b)'s disposition above is wrong in its rationale, and
> the correction is recorded here rather than by rewriting the row, per decision 7.]`**
>
> *"None broken; all helped — their four stdout reads are whole-stdout `json.loads`"* attributes to
> the harness four reads that belong to **Python-CLI** subprocesses in the same files. Per
> *invocation* rather than per *file*: 17 `subprocess.run` calls across the five — **7 harness, 10
> Python CLI** — and **no harness invocation reads stdout**. hc-d ran the five suites against the
> pre-hc-c harness (`b4d782a`, positive-controlled): **41 passed**, the same as after. So they are
> **unaffected**, not helped, and were never at risk. **"None broken" stands**; the rationale does
> not. This also resolves what was §Not established item 8 (D3), which asked exactly this question.

**One correction to F6's text, offered rather than pressed.** F6 says the r1 result was *"carried
from r0"*. It was not: a correctly-bound `drift_check --strict` **was** run post-commit at r1 and
reported `current=3d5a8da` / `current=1b09b23` — hashes that appear nowhere in r0's output
(`1f82118` / `e8889c3`), so the text cannot have been copied forward. But that invocation lived
only in the session, and **the packet is the artifact that travels**; as published the claim had no
truth-maker. The finding's substance is unaffected and its three defects are accepted as stated.
