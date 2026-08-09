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

**Status surfaces left untouched, deliberately.** The document header still reads *"hc-a closed,
hc-b in review"* and §Ticket set still gives hc-c *Not started*. Three amendments were authorised;
a fourth edit to a status claim is not mine to fold into their commit. **It is a real divergence
and it is named here rather than silently followed** — whoever opens hc-d should settle it.

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

## 7. For hc-d and hc-e

- **`mix test` is green** — 972 tests, 0 failures. BL-075 is not red in this environment today.
  Recorded in both directions per the gate rule: a gate that silently heals trains the same reflex
  as one that silently rots, and nothing was watching when it changed.
- **The status surfaces in `hc-consolidation.md` are stale** (§1 above). hc-d's opening
  section-scoped edit is the natural place to settle it.
- **`## Suggested order` has no row for BL-105 or BL-106** — its table ends at BL-095. Checked, so
  hc-e's clause-2 sweep does not have to rediscover it; the absence is a status, not a defect.
- **Three `project_knowledge` staleness WARNs are expected** at the post-commit done-check:
  `backlog-2026-06.md` and `aetheris--runbook.md` from this ticket, `aetheris--CLAUDE.md` still
  standing from hc-b's I0. All clear at hc-e's export boundary.
