# hc-c — implementation notes

**Ticket.** `docs/milestones/hc-consolidation.md` §Ticket set → hc-c, as authored at hc-b and
repaired at hc-b2. **Repos.** agents at `6c61393` (amendments at `599747e`), harness at `b4d782a`.
**Date.** 2026-08-09.

---

## 1. The three amendments (hc-c's opening edit)

A1 (R14) and A2 (§Not established item 5) landed as authored. **A3 did not**, and the reason is
worth keeping: it named `§Rules promoted / §Promotion candidates` as its target and
`hc-consolidation.md` has **neither** — those are `cloudcost/m4-consolidation.md`'s sections
(`## Promotion candidates`, :802). The reviewer corrected the placement: a new `## Promotion
candidates` between §Not established and §Not carried, with an opening line saying that recording
a candidate is not promoting it, because ratification belongs to hc-e.

Two notes on the mechanics:

- **The three amendments produce two diff hunks, not three.** A2 and A3 are adjacent insertions at
  the same point, so `git diff` merges them at `-U3`. The packet shows both hunks; nobody should
  read "two hunks" as "one amendment missing".
- **A2's citations were verified, not carried.** `supervisor.ex:62` and `:63` are the two negative
  clauses as anchored; hc-b2 §G3(4) does carry *"no such agent file exists"* and *"all twenty use
  `anthropic`, `ollama` or `gemini`"*, and `ls ../aetheris/agents/` returns 20.

**Status surfaces: left untouched at r0, fixed at r1 (F3).** At r0 the header still read *"hc-a
closed, hc-b in review"* and §Ticket set still gave hc-c *Not started*. I left them because three
amendments were authorised and a fourth edit to a status claim was not mine to fold into their
commit — and named the divergence rather than following it silently. The reviewer's F3 ruled that
correct at the time and **now authorises the fix, because hc-c is what made those surfaces false**:
a canonical document saying hc-c is *Not started* while hc-c is closed is a live false claim
carried across a ticket boundary. The header line and hc-c's row are updated; hc-d's and hc-e's
rows are untouched.

**The status line was written after the gates ran, not before.** *Closed* is a claim about the
pre-authorisation's conditions, one of which is the gates re-running clean — so writing it first
would have been a claim landing in the same commit as the thing that makes it true.

**And r1's fix left the document contradicting itself (r2, F7).** The header said hc-b was closed
while §Ticket set's `hc-b` row still said *In review* — F3 scoped the edit to the header and hc-c's
row, and I applied that scope exactly, including its instruction not to touch neighbouring rows.
The scope was wrong and the reviewer owns that; what this ticket owns is that **applying a scope
faithfully is not the same as checking what it left behind**, and no census of the document's
status surfaces was run until r2 asked for one. It found **two** stale surfaces, not one — hc-b's
row, and **hc-c's own row asserting closure at r1**, which r2's opening denies. See §8b.

---

## 2. The gate

Precondition re-checked at gate time, not inherited from planning: `:11434` answered `200` with
`llama3.2:latest` served.

**Verdict: routes to stderr** (verdict-table row 3). `containment` non-nil first, then the count —
2 lines, both in `stderr.txt`, 0 in `stdout.txt`.

**The run failed, and the gate still holds.** Ollama could not load the model (2.3 GiB needed,
2.1 GiB available), so the run errored at step 0. That does not touch the verdict, and the gate was
built so it would not: the positive control asks whether a *worker* ran, and `containment` —
`seccomp: true`, `exec_server: true` — says it did. The `[sandbox]` lines are emitted by the worker
at startup, upstream of the LLM call that failed. **I did not re-run to get a prettier result.**
A second run would have added nothing to the routing question and would have looked like fishing.

**The source derivation was confirmed, not refuted** — the two lines are exactly the success-path
pair hc-b2 §G3(3) predicted. That is the less interesting outcome of the two the gate allowed for,
and it is the one that happened.

---

## 3. The arm, and why not the other two

**Taken: BL-105's first Done-when arm — the payload on a stream the Logger does not share.**
Implemented by moving **Logger** to stderr rather than moving the payload, because Rig reads
stdout; moving the payload there would have broken the one shipped consumer. stdout is the payload
stream, stderr the diagnostic stream — and the gate is what makes that coherent rather than
arbitrary, since the worker's `[sandbox]` lines were already on stderr.

**Not taken: hc-a's third arm (suppress boot logging).** It only removes the *boot* lines. Any log
line emitted during a run still lands on the payload stream, so it does not deliver Done-when's
*"separable by a consumer that does not have to know what the noise looks like"*, and it pays for
that with observability.

**Not taken as the primary arm: the second (contract-state a last-parsing-object scan).** Its
wording is in tension with a shipped consumer: Rig scans for the **first** JSON line with a
`run_id`, deliberately, because BL-030's whole point is returning in seconds rather than after the
run. Rewriting it to last-wins would regress that. Both in-repo consumers already scan (Rig
first-wins; `sprint.sh` via `json_read`'s backward scan), so what that arm actually asked for is
already true — it is now *stated*, in the runbook, rather than made a requirement that would move
Rig the wrong way.

### The part that was not a config line

`config/runtime.exs` did not work, and the way it failed is the useful part.

Setting `config :logger, :default_handler, config: %{type: :standard_error}` made
`:logger.get_handler_config(:default)` **report** `standard_error` while `mix aetheris` output
**still went to stdout**. The two disagreed. The cause: `mix aetheris` never runs `app.start`,
which is what re-installs the default handler from application env, so the config was set beside a
running handler that had already been installed pointing at stdout. `mix run` does run it, which is
why the same setting looked correct when probed that way. An escript never evaluates `runtime.exs`
at all, so config could not have covered that entry point either.

**This is the resolved-versus-advertised rule in a new carrier.** The handler's config map is what
the library says it will do; the capture is what it did. I only found it because the check was a
redirect capture rather than a config read — a config read would have reported success.

`:logger.update_handler_config/3` cannot fix it either: Erlang rejects a `type` change on a live
`logger_std_h` with `:illegal_config_change`. The handler is removed and re-installed, carrying its
own formatter, level and filters. **Guarded to the defect**: only when the handler is still the
stock `logger_std_h` on `:standard_io`. A file handler, or an operator who already moved it, is
left alone — the stdout case is the bug; nothing else is ours to overwrite.

---

## 4. BL-106, and the adjacent case it created

`Formatter.print({:error, …}, :json)` now writes a document to stdout beside the unchanged prose on
stderr. Terminal run outcomes carry a structured detail (`%{run_id | orb_id, status, error}`) so the
document can name the run; everything else stays a bare string and renders
`{"status":"error","error":"…"}` with **no `run_id`**.

**That absence is load-bearing, not incidental.** Rig's `read_first_run_id` treats any stdout line
that parses as a JSON object with a string `run_id` as the fork-start line. If a *start* failure
emitted a `run_id`, Rig would report a fork that never began as started. It cannot: a fork that
fails before starting fails in `extract_run_id` / `load_trajectory` / `lookup_run` / `start_fork`,
all of which return bare strings.

**The adjacent case.** Widening the error to a map broke `fork.ex`'s `"#{message}: #{reason}"`
(BL-039 Part C's cause-appending) — a map has no `String.Chars`. I enumerated every consumer of
these error values before touching the first: `fork.ex` is the **only** site that interpolates one.
`replay.ex` and `run.ex` pass theirs through; every other `{:error, reason}` in `cli/` builds its
string from a different source. The fix appends the cause to the detail's `:error` field, so the
prose keeps BL-039's behaviour and `run_id`/status survive for `--json`.

**Three existing tests failed, and all three were asserting the shape rather than their invariant** —
`{:error, "cancelled"}`, `message =~ …`. Updated, not reverted, per the harness rule. They came out
stronger: they now pin `run_id` and the real status. One of them —
`fork_test.exs`, *"a fork that starts and then fails still emits its run id"* — is precisely the
risk case I could not construct by hand, and it already existed. It is the thing that proves the
fork-start line precedes any `run_id`-bearing error document, which is what keeps Rig's first-wins
reader correct.

---

## 5. What was checked and what it rests on

- **BL-105's mutation posture, both store conditions.** Noisy store: stdout 1 line, parses; stderr
  3 lines. Quiet store (`MIX_ENV=test`, the toggle BL-105's constructibility note anticipated):
  stdout 1 line, parses; stderr 0 lines. **The broken state is observed, not simulated** — the
  pre-fix capture from this same tree shows 4 non-blank stdout lines, 3 unparseable.
- **BL-106's mutation posture.** A genuinely failing run emitted
  `{"error":"run ollama-9EuU5w failed","status":"failed","run_id":"ollama-9EuU5w"}`. The same
  failing run, pre-fix, emitted no JSON at all.
- **The three new unit tests were mutation-checked.** Clause removed → the two payload-asserting
  tests fail; the human-path test correctly stays green, which is the right result and worth saying
  rather than counting as a miss.
- **Rig: verified still correct, not migrated.** Success path run live (start line then completion
  line, nothing between); start-failure path run live (`:step_not_found` → error document with no
  `run_id` on stdout, prose on stderr); its own 7 tests pass unchanged.
- **R11's guard was evaluated, not assumed away.** Its predicate was run verbatim against a real
  merged `2>&1` capture from the changed harness and passes. No capture-side split happened, so the
  finding does not fire and `sprint.sh` is not in Touches.

**What I did not establish.** I could not construct a fork that starts and then fails by hand — the
stub responses restart in the fork, so it completed. The property rests on the source ordering
(`fork.ex`, `run_with_step/4`: `emit_fork_started` then `await_fork`) **and** on the harness test
named above, not on an observation of my own making. Said plainly because the gap is real even
though it is covered.

---

## 6. Decision 13, and what hc-c did not do

R6 asked for one of two outcomes. This is the second: **the round did not overturn decision 13.**
Its subject is *the sprint's `--json` reads*, and hc-c changed nothing there — `sprint.sh` still
captures with `2>&1` and reads through `json_read`'s backward scan. What moved is where the harness
*emits*. The full reasoning, and decision 13's now-established `[sandbox]` clause, are recorded in
the cycle document beneath the m4 decisions table.

**Deliberately not touched:** BL-044 (`mix aetheris` discards the exit code, so a failed run still
exits 0) — that is R3's question for hc-d, and it is *why* a real status word in the payload earns
its place. BL-112 (latin1 corruption of `--json` payloads), whose row says it belongs with these
two; it is a different defect and outside hc-c's stated scope. BL-108, eduloka's status read (R10).
No planted cloud resource (R9).

---

## 7. The consumer sweep (r1, F1) — population, enumeration, disposition

**Why it was owed.** BL-106's fix enumerated every consumer before touching the first. BL-105's
did not: `route_logging_to_stderr/0` runs on the boot path and moves the stream for **every**
invocation and every mode, while r0's packet verified two consumers — both `--json` readers. The
absence of a known log-on-stdout reader is not the established absence of one.

**Population.** Every file in both repos with an executable extension (`.sh .py .rs .ts .tsx .exs
.ex`), excluding `node_modules`, `target`, `_build`, `deps`, `priv`, `.git`, containing a harness
invocation. **Search terms run** (recorded because a method record that misdescribes what executed
is itself a false claim): `mix aetheris`; `./aetheris`; the Rust/Python argv vectors
`["mix", "aetheris"]` and `"aetheris".to_string`. **39 files matched.**

**Of the 39, five actually spawn the harness and read a stream.** The other 34 are prose:
comments, docstrings, runbook lines inside agent `.exs` files, UI display strings
(`rig/src/components/modules/harness/RunList.tsx` renders `mix aetheris run` as `<code>`), a
mocked test (`docbuilder/tests/test_chain_docbuilder.py` patches `subprocess.run`), and the
harness's own modules under `../aetheris/lib/`, which are the harness rather than consumers of it.

| # | Consumer | Streams | What it reads | Affected? |
|---|---|---|---|---|
| 1 | `../aetheris/scripts/sprint.sh` | see below | `json_read` (JSON) + text over **merged** captures | **no** |
| 2 | `docbuilder/scripts/chain_docbuilder.py` | `capture_output=True` | `returncode` and `stderr` only — never stdout text | **no** |
| 3 | `provenance/scripts/validate_search.py` | `capture_output=True` | `result.stdout + result.stderr` **concatenated** for its text search (`:61`); `_extract_run_id` (`:70`) scans stdout for `"Run ID:"` — **formatter** output, not Logger | **no** |
| 4 | `rig/src-tauri/src/commands/orchestrate.rs` | stdout piped, `stderr(Stdio::null())` | stdout line-by-line, **keeps only lines that parse as JSON** (`:84`), drops the rest | **no** |
| 5 | `rig/src-tauri/src/commands/fork.rs` | stdout piped, stderr collected | first stdout line parsing as JSON with a `run_id`; stderr prose on the failure path | **no** |

**sprint.sh, in detail** — 92 non-comment lines invoke the harness (`run_aetheris`, `mix aetheris`,
`mix run --eval`, `run_agent`, `run_orb`). `mix run --eval` is in the population because it boots
the app, so `route_logging_to_stderr/0` runs there too. Derived split:

```
captured via run_agent/run_orb (the helper redirects `> "$file" 2>&1`)   36
no capture — streams to the console                                      28
captured directly with stderr MERGED (2>&1)                              14
`if … 2>/dev/null; then` — stderr discarded, gate is the EXIT CODE       11
helper definitions themselves                                             3
                                                                       ----
                                                                         92
stdout captured WITHOUT stderr merged, and read as text                    0
```

The eleven exit-code gates are the seven `mix run --eval` eval-checks (`:1794`, `:1907`, `:1996`,
`:2080`, `:2216`, `:2315`, `:2697`), two `mix aetheris server … &>/dev/null &` backgrounds
(`:1160`, `:1251`) which discard both streams, and two `mix aetheris trajectory … --export`
calls (`:1198`, `:1282`) whose consumer is the exported **file**.

**The four text searches over harness artifacts** (`grep`/`=~` over an output file or captured
var) were checked individually: `:918` greps `"Sent:"` in `email/run.json` — written by
`run_agent`, which merges; `:2759`/`:2760` grep `$CC_GUARD_OUT`, captured `2>&1`, for an Elixir
raise message that was always on stderr; `:1640` greps a `curl` response, not harness output; and
`:890` is a `find` over PDFs. **None reads harness stdout in isolation.**

**One behavioural change worth naming, not a breakage:** the seven `2>/dev/null` eval-gates used
to let the boot log lines through to the sprint console on stdout, and now discard them with
stderr. The sprint gets **quieter**; the gate is the exit status either way.

**Disposition — clean, not exhaustive.** Zero broken consumers in the named population. The sweep
cannot reach an operator's own shell pipeline, anything outside these two repos, or an invocation
spelled in a way none of the four terms matched. **Recorded as §Not established item 6** rather
than allowed to read as completeness, and the change is announced in the operator-facing runbook
(F1(c)) rather than only in the backlog.

---

## 8. Round 2 — what r1 introduced or left

### 8a. The r1 done-check published a command that did not run (F6)

The r1 packet's §1e printed
`python3: can't open file '…/aetheris/scripts/drift_check.py': [Errno 2] No such file or directory`
and, beneath it, `exit=0` and *"the same three WARNs"*. Three defects in one block:

1. **Command binding.** The packet's build script had done `cd …/aetheris` for an earlier section,
   and the `cd` persisted. `drift_check.py` lives **only** at
   `aetheris-agents/scripts/drift_check.py` — located by `find`, not assumed. This is the
   persisting-`cd` carrier of **Silent-wrong-answer** named in the harness `CLAUDE.md`, in the
   packet-assembly step of the very ticket that quoted it.
2. **The exit code belonged to nothing.** `exit=0` was a literal I echoed, not a captured status.
   The real code is **2** — reproduced: `python3 <missing file>` exits 2. A packet that prints a
   failure and a contradicting exit code asserts neither.
3. **A count over a capture that was never made.** *"The same three"* quantified a comparison the
   published command had not performed.

**One correction to the finding, offered rather than pressed.** F6 says the result was *"carried
from r0"*. It was not: a correctly-bound `drift_check --strict` **was** run post-commit at r1 and
reported `current=3d5a8da` / `current=1b09b23`, hashes that do not appear in r0's output (`1f82118`
/ `e8889c3`). But that invocation lived only in the session, and **the packet is the artifact that
travels** — so as published the claim had no truth-maker, which is F6's substance and it stands.

**F6(d): does not fire.** Re-run at r2, bound explicitly, exit code captured from the invocation
itself: **0 FAIL, 3 WARN, exit 0**, and the WARN set is identical in count, membership and hashes
to what r1 asserted. Recorded as *not firing* rather than left silent.

### 8b. The status-surface census (F7(c))

**Population: every place `hc-consolidation.md` states an `hc-*` ticket's state.** Derived by
matching state vocabulary — `Status:`, `closed`/`Closed`, `In review`, `Not started`,
`In progress` — over the whole file, then classifying each of the 26 hits by hand. **Seven are
ticket-state surfaces; the other 19 are about m4, backlog rows, decisions, or generic prose.**

| # | Surface | State at r2 |
|---|---|---|
| 1 | The header `**Status:**` line | updated at r1 (F3) |
| 2 | §Ticket set, `hc-a` row | `**Closed.**` — unchanged, correct |
| 3 | §Ticket set, `hc-b` row | **was `In review`** — the contradiction F7 found; now closed |
| 4 | §Ticket set, `hc-c` row | **was `Closed … at r1`** — premature; now `at r2` |
| 5 | §Ticket set, `hc-d` row | `Not started` — correct, untouched |
| 6 | §Ticket set, `hc-e` row | `Not started` — correct, untouched |
| 7 | §hc-a's opening prose, *"Closed. Read-only, no commit, by design."* | correct, untouched. **A second surface for hc-a** — the only ticket whose state is stated twice |

**Two surfaces were stale, not one.** F7 named the `hc-b` row; the census also caught **hc-c's own
row asserting closure at r1**, which the reviewer's round-2 opening explicitly denies. A census
that had only checked the finding's own target would have left the document asserting a closure
that did not happen.

**One adjacent surface, in scope to name and not to change.** §Rows filed opens *"Empty at hc-b"*.
That is a claim about the section, not a ticket's state, and it stays true: hc-c filed no backlog
row (BL-105 and BL-106 were **closed**, and closure is recorded on the rows themselves, per §Close
criteria clause 2). Named here so the next reader does not have to re-derive that it was checked.

### 8c. The extended sweep (F8)

**The first term list was incomplete, and its own sibling analysis proved it before any reviewer
did.** r1's four terms were all spellings of `aetheris`, while r1's sprint.sh analysis argued —
correctly, and generally — that `mix run --eval` boots the app and is therefore in scope. That
term was never searched for in the other 38 files.

**The extended list is derived from what boots the app**, not from the finding's suggestion:
`route_logging_to_stderr/0` runs in `Aetheris.Application.start/2`, so anything that starts the
`:aetheris` OTP application counts — `mix aetheris`, `mix run`, `mix test`, `mix eval`,
`iex -S mix`, `./aetheris`, and the argv constructions `["mix", …]`, `System.cmd("mix", …)`,
`Command::new("mix")`, `subprocess … "mix"`.

```
OLD population (r1, four terms) = 39
NEW population (r2, extended)   = 48
ADDED by the extension          =  9
LOST by the extension           =  0   (the new list is a superset — checked, not assumed)
```

**The nine, per file:**

| File | Kind |
|---|---|
| `../aetheris/test/aetheris/execution/fork_test.exs` | **prose** — a comment about `mix test --include requires_real_provider` |
| `../aetheris/test/aetheris/integration/codebase_qa_test.exs` | **prose** — a docstring `mix test --include integration` |
| `../aetheris/test/aetheris/integration/skill_extraction_test.exs` | **prose** — a docstring *"Plain `mix test` coverage…"* |
| `../aetheris/test/aetheris/worker/client_internet_test.exs` | **prose** — a comment about `mix test --include requires_worker` |
| `provenance/tests/test_search_agent.py` | **consumer** — `["mix", "run", "--eval", …]`, `capture_output=True` |
| `provenance/tests/test_zip_archaeologist.py` | **consumer** — same |
| `provenance/tests/test_zip_orchestrator.py` | **consumer** — same |
| `provenance/tests/test_migration_agent.py` | **consumer** — same |
| `provenance/tests/test_classification_orchestrator.py` | **consumer** — same |

**None is broken, and the change helps them.** Bound to those five files by name, not by a glob:
**4** stdout reads, every one `json.loads(result.stdout.strip())` — a **whole-stdout** parse that
any boot line on stdout would have broken; and **3** stderr text assertions
(`"1 files pending migration"`, `"22 files to classify"`, `"1 zips pending"`), substring tests that
extra stderr content cannot falsify. **All 41 tests pass on the changed harness** (4 + 37 across
the five files). The boot path was confirmed to be real rather than inferred from a fast runtime:
running one test's exact command directly gives **stdout 0 bytes** and three
`[Aetheris.Application]` lines on stderr, in 815 ms.

> **`[corrected 2026-08-09 (hc-d, R-i) — the paragraph above is wrong in its rationale.]`** The
> four `json.loads(result.stdout.strip())` reads it attributes to the harness belong to
> **Python-CLI** subprocesses (`[sys.executable, SCRIPT]`) in the same files. Enumerated per
> *invocation* rather than per *file*: the five files make **17** `subprocess.run` calls — **7**
> spawn the harness, **10** spawn a Python CLI — and **all four whole-stdout parses are the Python
> CLIs'**. No harness invocation in these files reads stdout; the 7 read `returncode` and `stderr`.
> So the suites are **unaffected by hc-c, not helped by it**, and they were already green on the
> pre-hc-c tree (**41 passed at `b4d782a`**, positive-controlled both ways). **"None is broken"
> stands.** The error is a census keyed on the wrong unit — reads-per-file where the question was
> reads-per-invocation, merging two subprocess families that share a file. Established under
> hc-d's R-i; see `hc-consolidation.md` §Not established item 8. Original text left standing per
> decision 7.

> **A count error of my own, in this section, corrected rather than quietly fixed.** My first pass
> counted stdout/stderr reads with `grep -c … test_*.py`, which globs **every** test file in
> `provenance/tests/`, not the five under discussion — 21 and 18 against an enumeration showing 4
> and 11. That is *a count printed beside an enumeration that contradicts it*, the promoted
> carrier, produced while discharging a finding about population discipline. The counts above are
> bound to the five files named explicitly.

### 8d. The negative check now has a positive control (F9)

r1 asserted hc-d's and hc-e's rows were untouched with a `grep -c … -> 0`. A zero from a malformed
pattern is indistinguishable from a zero meaning absence — the shape the step-1 gate's own positive
control exists to prevent, applied to a `grep` this time.

```
POSITIVE CONTROL — same pattern against hc-c (a row the diff is known to change):  2
NEGATIVE          — the pattern against hc-d / hc-e:                               0
```

The control returns 2 (the `-` and `+` of hc-c's row, both printed), so the pattern matches when
its target is present and the 0 reads as absence. **hc-d's and hc-e's rows are untouched**, now on
evidence rather than on a bare zero.

---

## 9. For hc-d and hc-e

- **`mix test` is green** — 972 tests, 0 failures. BL-075 is not red in this environment today.
  Recorded in both directions per the gate rule: a gate that silently heals trains the same reflex
  as one that silently rots, and nothing was watching when it changed.

  **With a qualification this ticket owes, because hc-c edited the flake's own module family.**
  BL-075's flake was named at m4 close-b as `Aetheris.CLI.Commands.RunHelpersTimeoutTest`, and
  hc-c's diff touches `../aetheris/lib/aetheris/cli/commands/run_helpers.ex` — the module that
  test exercises — and `test/aetheris/cli/commands/run_helpers_test.exs`. **No `mix test` was run
  on this tree before the edits**, so "green because of this ticket" and "green despite it" are
  not distinguished by any measurement here.

  What the diff does say, read against the test rather than asserted in general:

  - The flake's own file, `test/aetheris/cli/commands/run_helpers_timeout_test.exs`, is **not in
    hc-c's diff** (last touched at `a935038`, BL-031 r2).
  - The assertion it flakes on is on the **`:done` success path** —
    `{:ok, %{run_id: ^run_id, status: :done}}` (`run_helpers_timeout_test.exs`, *"a status change
    alone counts as activity"*, `:98`). hc-c changed only `handle_run_status/5`'s `"failed"` and
    `"cancelled"` branches.
  - The branch it *failed* into is `continue_or_timeout/5`'s inactivity arm, which hc-c left
    exactly as it was — still a bare-string error.
  - No timing, polling interval, sleep or inactivity bound is touched anywhere in the diff.

  **So hc-c changed neither the path that test asserts nor the path it failed on — but that is
  reasoning from source, not a measurement.** Not re-run to chase a red: one green does not refute
  a flake and one red would not confirm it.
- **The status surfaces in `hc-consolidation.md` are stale** (§1 above). hc-d's opening
  section-scoped edit is the natural place to settle it.
- **`## Suggested order` has no row for BL-105 or BL-106** — its table ends at BL-095. Checked, so
  hc-e's clause-2 sweep does not have to rediscover it; the absence is a status, not a defect.
- **Three `project_knowledge` staleness WARNs are expected** at the post-commit done-check:
  `backlog-2026-06.md` and `aetheris--runbook.md` from this ticket, `aetheris--CLAUDE.md` still
  standing from hc-b's I0. All clear at hc-e's export boundary.
