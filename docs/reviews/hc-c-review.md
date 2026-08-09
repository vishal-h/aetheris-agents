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
