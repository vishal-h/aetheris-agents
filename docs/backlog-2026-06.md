# Backlog — 2026-06

Distilled from the reality-check / drift-apparatus work of 2026-06-11.
All file references verified against code as of `docs/rig/current-state-2026-06.md`
(plus subsequent commits: stale-run/cost `88705f1`/`0eddf20`, drift checker
`66566b6` + `bd2c3d8` and follow-ups).

Sizes: **S** < half a day · **M** a day or two · **L** milestone-sized (gets its
own `docs/rig/milestones/` directory and issue docs before implementation).

GitHub issues: #42–#55 on vishal-h/aetheris-agents.

---

### BL-135 — `run_helpers_timeout_test.exs:84` is timing-flaky: a 200 ms feeder against a 300 ms bound (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/test/aetheris/cli/commands/run_helpers_timeout_test.exs`)

Filed 2026-08-09 from **hc-d r3's** ticket-boundary gate run — off-territory, the way the gate rule
intends, and filed the day it was found rather than carried.

**The observation.** `mix test` returned **exit 2**, `972 tests, 1 failure`:

```
1) test a status change alone counts as activity, with no events at all
   (Aetheris.CLI.Commands.RunHelpersTimeoutTest)
   test/aetheris/cli/commands/run_helpers_timeout_test.exs:84
   right: {:error, "run await-status-activity-8610 stalled: no status or event
           activity for 300ms (last status: running, last event seq: -1)"}
   stacktrace: test/…/run_helpers_timeout_test.exs:98
```

**Not caused by the ticket that found it.** hc-d r3's diff (`48f59e7`) touches
`scripts/sprint.sh` and nothing else — no `lib/`, no `test/`, no `config/`. The three preceding gate
runs in the same cycle all reported `972 tests, 0 failures`.

**The mechanism is structural, and visible in the test's own source.** A feeder task writes four
status changes with `Process.sleep(200)` between them, while the assertion runs
`await_bounded(run_id, await_inactivity_timeout_ms: 300)`. **A 100 ms margin.** Any scheduling delay
that pushes one 200 ms sleep past 300 ms fires the inactivity bound and the test fails. The gate run
that caught it was executing concurrently with sprint runs and filesystem watchers.

**Not reproduced, and that is stated rather than glossed.** **9 attempts, 0 reproductions**: 8
consecutive runs of `…:84` on an idle machine (8 PASS), plus 1 run under deliberate CPU load (6 spin
loops) which also passed. So the failure is real and observed, and the conditions that produce it
are **not** established — only the 100 ms margin that makes it possible.

**Do not "fix" it by widening the bound alone.** `await_inactivity_timeout_ms` is the behaviour under
test; inflating it to buy margin weakens the assertion it exists to make. The likely correct shape is
to make the feeder's activity observable rather than timed — drive it off a signal the assertion can
wait on — or to give this test an explicitly generous bound *with the reason recorded*, so a later
reader does not read the number as the contract.

**Done when:** the test is either deterministic under load, or its timing margin is stated as
deliberate with a recorded rationale, and 20 consecutive runs under CPU load pass. Until then the
gate runs **expected-flaky, named with this row's ref** per the tracked-carry clause — named in
packets, not re-triaged, and **not relaxed**.

`Source: hc-d r3 ticket-boundary gate run, 2026-08-09 (harness 48f59e7, agents 4222804). One
observation; the non-reproduction is recorded above as part of the evidence, not omitted from it.`

> **`[FOLDED into BL-075, 2026-08-09 (hc-e's opening edit, E3). Same defect — this row should not
> have been filed. Kept, not deleted, because the fold and its reason are the record.]`**
>
> **They are the same defect, established from the rows and the source, not from resemblance.**
> BL-075's m4 close-b annotation already names the identity in full — same module
> (`Aetheris.CLI.Commands.RunHelpersTimeoutTest`), same file and line
> (`test/aetheris/cli/commands/run_helpers_timeout_test.exs:84`), same stacktrace line (`:98`),
> same assertion (`await_bounded(run_id, await_inactivity_timeout_ms: 300)`), and the same error
> shape (`stalled: no status or event activity for 300ms … last event seq: -1`). The only
> difference between the two observations is the generated run id — `await-status-activity-7139`
> at close-b, `-8610` here — which is `System.unique_integer` and distinguishes nothing.
>
> **Not two tests in one module, and not two failures of one test.** One test, one assertion, two
> observations seven days apart. `grep -c 'run_helpers_timeout_test'` over `../aetheris/scripts/`
> is not the question; the question is the module's test count, and the row above named a single
> `test …:84`.
>
> **So this row is a duplicate, and the error is mine.** The gate rule says a red gate gets a
> tracked ticket *the day it is found* — it does not say file without looking. I filed BL-135 at
> hc-d r3 without searching the backlog for an existing row on the same test, and BL-075 not only
> existed but already carried the identical stack trace. **The count error is over a population of
> size two:** filing a second row for one defect, exactly as filing one row for two would have
> been.
>
> **What BL-135 contributes, folded onto BL-075 above as a third observation:** the 2026-08-09
> failure with its own date and evidence, and — new — **nine non-reproductions** (8 idle runs of
> `:84`, one under six CPU spin loops, plus a full green suite), which is the first time the
> reproduction conditions have been probed rather than only the failures counted. **The warning
> against the tempting fix stands and is not duplicated:** widening
> `await_inactivity_timeout_ms` weakens the assertion, because the bound *is* the behaviour under
> test — which is BL-075's own *"fixed-ms window rather than a poll"* mechanism class, and
> BL-054's §Suggested order entry already names the cure.
>
> **Status:** folded. Track the defect on **BL-075**. This row stays as the record of the
> duplication and of the non-reproduction evidence.

---

## Housekeeping (do first, near-zero effort)

### BL-001 — Capture clean drift baseline (#42)
**Size:** S · **Priority:** now

Every drift_check output recorded so far predates at least one parser fix
(paren-depth, payload `?` marker, `_evaluate_payload_fields` extraction).
There is no recorded genuinely-clean run.

- Run `python3 scripts/drift_check.py` with `AETHERIS_DB_PATH` set.
- Expected (as observed 2026-07-15): 8 PASS, 0 FAIL, 0 WARN. The 8th PASS
  is the `project_knowledge` check. INFOs fall in two benign categories:
  `env_vars` (agent-side vars in specs §1 not read by Rig) and
  `payload_fields` (event payload fields observed in the DB but not yet
  promoted to specs §6). The phantom `runs.finished_at` and
  `llm_responded.stop_reason` INFOs must be gone.
- Append the summary line to `docs/rig/current-state-2026-06.md` as
  "Drift baseline 2026-07-XX: …".

**Done when:** baseline recorded; any unexpected finding triaged.

**Status:** Done 2026-07-15 — baseline in `current-state-2026-06.md`,
commit `d24e482`. Expectation lines above corrected to observed reality
per review finding 1 (`docs/reviews/bl-001-review.md`).

---

### BL-015 — Promote nine observed payload_fields to specs §6 (#66)
**Size:** S · **Priority:** now (before BL-002)

> Numbered BL-015, not BL-010 as the review draft suggested — BL-010
> through BL-014 are existing boxy-pipeline tickets. GitHub issue #66.

The 2026-07-15 baseline (`d24e482`) reports nine payload fields observed
in DB events but absent from specs §6: `prompt_built.key`,
`prompt_built.tool_schema`, `llm_responded.content`,
`llm_responded.tool_input`, `llm_responded.tool_name`,
`llm_responded.type`, `tool_result.is_error`, `tool_result.result`,
`error.detail`. Per the BL-006 logic, observed fields get promoted — but
the §8 errata's `llm_called`/`llm_responded` divergence means each field
needs a canonical-name confirm before promotion, not a mechanical copy.

Split from BL-001 review finding 3. Ordered before BL-002 so BL-002's
single export catches the promoted fields, the corrected backlog, and the
new baseline in one manifest refresh. `stop_reason` stays with BL-006 —
still zero rows, its trigger hasn't fired; BL-015 does not subsume it.

**Done when:** each field has a disposition (promoted to §6 / errata note
/ anomaly triaged); drift_check shows zero `payload_fields` INFOs, 0 FAIL,
0 WARN.

**Status:** Done 2026-07-15. 6 canonical fields promoted to specs §6
(`prompt_built.tool_schema`; `llm_responded.tool_name`/`tool_input`;
`tool_result.result`/`is_error`; `error.detail`) — each confirmed against
current harness emission (`loop.ex:170/244/245/352/355`,
`agent/server.ex:529`). 3 fields errata-noted in specs §6, **not**
promoted: `prompt_built.key` (test-fixture `{"key":"value"}`) and
`llm_responded.content`/`type` (pre-2026-05-15 legacy emission, superseded
by `raw_response`/`response_type`) — all confined to 2026-05-12 rows.
Residual after this ticket: 3 `payload_fields` INFOs (legacy DB rows;
clear on dev-DB reset, DB read-only here) and 2 `project_knowledge` WARN
(manifest staleness from the BL-001 + BL-015 doc commits — BL-002 owns the
refresh and the clean re-verify, per BL-001 review finding 2).

**Tracked follow-up (event-triggered, not scheduled — BL-006 pattern):** a
dev-DB reset clears the three BL-015 documented-legacy payload INFOs
(`prompt_built.key`, `llm_responded.content`/`type`). **Gated on BL-003
completion** — the pre-2026-05-15 legacy rows share the May window with
BL-003's orphaned-`running` fixtures, so a reset before BL-003 consumes
them would destroy fixtures. (Note surfaced during BL-015: the DB now holds
76 `running` rows, not five — BL-003's "five orphaned rows" count is itself
stale and wants re-checking when BL-003 is scoped.)

---

### BL-002 — Refresh Claude project knowledge files (all three scopes) (#43)
**Size:** S · **Priority:** now

The Claude.ai project still carries the 2026-05-31 snapshot (superseded
handoff, pre-fix specs/architecture/runbook). This staleness is what
triggered the entire reality-check exercise. The refresh must cover all
three scopes, not just Rig:

**Rig** (replaces current stale set):
- `docs/rig/specs.md`, `docs/rig/architecture.md`, `docs/rig/runbook.md`,
  `docs/rig/milestones/p3/protocol.md`, `docs/rig/current-state-2026-06.md`
- `rig/CLAUDE.md` if conversations will touch Rig implementation
  (it is the authoritative Claude Code context for that subtree)

**aetheris-agents repo** (mostly new additions):
- Repo-root `CLAUDE.md` (refresh — now carries the doc-sync DoD)
- `docs/agent-creation-guide.md` (CLAUDE.md names it the authoritative
  agent-building reference; currently absent from project knowledge)
- `docs/capability-matrix.md` (what agents exist; orchestrator plans
  from it; needed for any "which agent does X" conversation)
- `docs/backlog-2026-06.md` (this file)

**aetheris (harness)** (currently zero representation):
- `aetheris/CLAUDE.md` if it exists (verify) — the harness-side Claude
  Code contract. Harness *source* facts (schema, event types, trajectory
  format) are deliberately NOT exported raw; they live verified in
  `current-state-2026-06.md` §7/§8/3.1 and the corrected specs.md.

**Drops:** the superseded handoff (banner already redirects) and
`docs/rig/README.md` (redundant with architecture + current-state).

**Manifest:** add `docs/project-knowledge-manifest.md` — one table:
file → commit hash at export. Refresh the manifest with every export.
This makes project-knowledge staleness mechanically detectable: the
next reality-check (or a future drift_check check) compares manifest
hashes against `git log -1 --format=%h -- <file>`.

- Convention going forward: refresh at the same boundaries the
  reality-check prompt runs at (milestone end / before handoff), and
  the manifest is part of the export, not optional.

**Done when:** project knowledge matches HEAD for all three scopes and
the manifest exists in-repo.

**Status:** Done 2026-07-15. Repos rule added to root `CLAUDE.md`; BL-001
/ BL-002 / BL-015 marked complete here and on the roadmap Active line;
`../aetheris/CLAUDE.md` confirmed present (27 KB) and in the export set.
Manifest regenerated as the final commit (hashes at HEAD after the doc
edits): `rig--specs.md`, `rig--current-state-2026-06.md`,
`backlog-2026-06.md`, `aetheris-agents--CLAUDE.md`. drift_check re-verify
at HEAD: 8 PASS / 0 FAIL / 0 WARN / 7 INFO. The Claude.ai upload itself is
the human step; export file list + hashes delivered in the packet.

---

## Harness (aetheris/)

### BL-003 — Startup sweep for orphaned `running` runs (watchdog, cure side) (#44)
**Size:** M · **Priority:** high

Rig's "stalled?" marker (commit `0eddf20`) is the *detector*; the DB still
lies forever. As of the 2026-07-15 baseline (verified `d24e482`),
`priv/aetheris.db` holds **76** `status='running'` rows — not the five May
rows the earlier draft assumed (corrected per BL-002 review finding 2).
Census (reference fixture — re-run at execution time, see done-when):

| Last event | Count | True state | Sweep action |
|---|---|---|---|
| (no events) | 11 | orphaned | `run_orphaned`, `finished_at`=`started_at` |
| `llm_called` | 30 | orphaned | `run_orphaned`, `finished_at`=last-event ts |
| `tool_called` | 22 | orphaned | `run_orphaned`, `finished_at`=last-event ts |
| `prompt_built` | 3 | orphaned | `run_orphaned`, `finished_at`=last-event ts |
| `run_complete` | 6 | finished (status lagged) | reconcile → `done`, `finished_at`=event ts |
| `error` | 4 | errored (status lagged) | reconcile → terminal, `finished_at`=event ts |
| `agent_waiting` | 0 | none paused currently | synthetic fixture required |

- **Pre-flight — this is the project's first ticket that WRITES to the DB
  (76 status mutations, a new event type, `finished_at` stamps).** Before
  the first sweep run, copy `priv/aetheris.db` aside (plain file copy; the
  harness must not be running during the sweep). The census is the
  acceptance fixture; the backup is the undo button if the sweep mishandles
  real rows on first contact. Record the backup path in the implementation
  notes; delete it after the done-check passes.
- On harness application start (and/or a `mix aetheris sweep` task), find
  runs where `status='running'` and the owning process is provably gone
  (no live GenServer for the run_id; last event older than a **named config
  threshold** — see below).
- **Orphaned (66, no terminal event):** mark `failed`; emit a new
  **`run_orphaned`** event type — per harness rule 14 this is a three-place
  change in one commit: `event.ex` union **and** `Trajectory.File`
  `@event_type_map` **and** specs §6, then drift_check. `finished_at` =
  last-event timestamp; for the 11 no-event rows, `started_at`. **Never
  sweep time** — that fabricates the dormancy gap into the run duration.
- **Reconcilable (10, last event `run_complete`/`error`):** adopt the
  terminal outcome the events already record — set `runs.status` to
  `done`/error and `finished_at` to the terminal event's timestamp; emit
  **no** new event (the trajectory already tells the truth); log one
  reconciliation line. Do **not** overwrite a real outcome with `failed`.
- Must not touch legitimately paused runs: a run whose latest event is
  `agent_waiting` with an unexpired `wait_condition` in `run_checkpoints`
  is paused, not dead. **Zero such runs exist in the current DB** — the
  exclusion path has no live fixture, so build a **synthetic
  `wait_for_event` run** during the ticket to exercise it; do not assume
  it is present.
- The liveness **threshold is a named config key**, not a buried constant:
  name it, pick a default with one sentence of rationale, and document it
  in `runbook.md` (runbook update rule — operational knob, same commit).
- Specs §6's `run_orphaned` row **notes the status mapping** (event
  `run_orphaned`, status `failed`) so the event/status asymmetry reads as
  designed, not accidental.
- Write `finished_at` when sweeping (note: Rig's `TrajectoryMeta` treats
  missing `finished_at` as `""`).

**Do not:** change Rig's stalled? detector (ships as-is; this is the cure
side); clean up the BL-015 legacy event rows (separately gated on this
ticket's completion).

**Done when:** re-run the census pre-sweep (fresh numbers, not the
`d24e482` reference) → sweep → post-sweep counts match that fresh census:
orphaned rows marked `failed` with `run_orphaned`, reconcilable rows
adopted to their recorded terminal outcome, **0** rows remain `running`;
both censuses in the implementation notes; a kill-9'd run is swept on next
harness start; a synthetic `wait_for_event` run survives; drift_check
passes (`--strict` if BL-009 landed).

**Status:** Done 2026-07-15. `Aetheris.Sweep` ships the cure: startup hook
(after checkpoint resume, gated by `config :aetheris, :sweep_on_start`,
default on) plus `mix aetheris sweep`. New `run_orphaned` event type added
via the rule-14 three-place change (`event.ex` union + `Trajectory.File`
`@event_type_map` + specs §6, one commit); drift `event_types` parity holds
at 22 types. Fresh pre-sweep census matched the `d24e482` reference exactly
(66 orphaned / 10 reconcilable / 0 paused); post-sweep **0** rows remain
`running`. Liveness threshold is the named config key
`:sweep_liveness_threshold_ms` (default 300 000 ms, mirroring Rig's "stalled?"
display detector; documented in `runbook.md`). Paused-run exclusion exercised
with a synthetic unexpired `wait_for_event` fixture (survives, not merely
created). Methodology §6 repo-qualified-Touches rule batched into this commit
per the approved promotion. Implementation notes + both censuses in
`../aetheris/docs/aetheris/milestones/bl-003-startup-sweep-implementation-notes.md`.

---

### BL-004 — Per-run token totals in RunSummary (#45)
**Size:** S · **Priority:** low

Gap A residual ("Rig-side addressed" note in current-state doc): cost
landed in the run list; token totals did not.

- Same pattern as `total_cost_usd` in `harness.rs` `harness_list_runs`:
  correlated subquery `SUM(json_extract(payload_json,'$.input_tokens'))` /
  `'$.output_tokens'` over `type='llm_responded'` (tokens live ONLY in
  `llm_responded` — see specs §6 / report errata).
- `RunSummary` + `types.ts` + optional column or tooltip in `RunList.tsx`
  (the table is at 8 columns; consider folding tokens into the Cost
  cell's tooltip instead of a 9th column).
- Update specs §3; run drift_check.

**Done when:** token totals visible per run; NULL stays NULL for stub runs.

**Status:** Done 2026-07-20 — `total_input_tokens` / `total_output_tokens` added to
`RunSummary` as correlated subqueries mirroring `total_cost_usd`, surfaced in the
Cost cell's `title` tooltip (table stays at 8 columns), commit `c39bf7e`. No
`COALESCE`: NULL stays NULL, verified against stub fork runs. Cross-checked against
`usage.rs`'s differently-shaped aggregation — 57591 input tokens both ways on
`docbuilder-orch-iDGIIQ`. Columns appended after `total_cost_usd` so `row.get`
indices 0–10 are unshifted.

**Correction:** "Update specs §3" above is a **stale structural pointer**. §3 is
*Trajectory File Schema*; the Tauri command structs live in **§4**, which is also the
section `drift_check.py` parses. §4 is what was edited. A backlog row quoting doc
structure decays exactly like a `file:line` citation does — same class, different
surface (review finding 3, `docs/reviews/bl-029-review.md`).

---

### BL-016 — Fix standing `payslip_orchestrator` test failure (#67)
**Size:** S · **Priority:** medium

`test/aetheris/agents_test.exs:22` ("payslip_orchestrator.exs evaluates to a
valid RunConfig") is **red on `main`** and has been since before BL-003.
Surfaced during BL-003's suite run and triaged per the standing pristine-HEAD
rule: with BL-003's work stashed, `mix test test/aetheris/agents_test.exs`
still fails identically (`git stash push --include-untracked` → run → pop), so
it is not a BL-003 regression. Evidence in `docs/reviews/bl-003-review.md`
finding 2 and `bl-003-startup-sweep-implementation-notes.md`.

- The test asserts `agents/payslip_orchestrator.exs` resolves to tools
  `["run_command", "spawn_agent", "wait_for_all"]` (test lines 43–45), but the
  agent file currently yields only `["run_command"]` — `assert "spawn_agent" in
  result.tools` fails (`left: "spawn_agent", right: ["run_command"]`).
- Decide the source of truth: either the agent file lost `spawn_agent` /
  `wait_for_all` (restore them) or the test is ahead of the file (correct the
  assertion). Do not silently delete the assertion.

**Why it matters:** a standing red test normalises "1 failure is expected" and
lets the *next* real failure hide behind it (alarm fatigue). Close it so the
suite is 0-failure and a new red is unambiguous.

**Done when:** `mix test` is green with no excluded/expected failures; whichever
side was wrong (agent file or test) is corrected with a one-line rationale.

**Status:** Done 2026-07-15. Evidence resolved the fork: `git log -p` on
`payslip/agents/payslip_orchestrator.exs` shows commit **5abd4b9**
("refactor(payslip): move employee loop into generate script, remove LLM
iteration") deliberately dropped `spawn_agent`/`wait_for_all` — the LLM was
mangling employee IDs when iterating, so the same commit rewrote
`generate_employee_payslips.py` to loop over all employees internally. This is
the deliberate-sequential branch, aligned with the ROADMAP "Sequential over
parallel for independent agents" principle — so the **test was stale**, not the
agent file. Fixed in the harness (`test/aetheris/agents_test.exs:22`):
`tools == ["run_command"]`, `context_strategy == :full`; the stale spawn-based
assertions and `max_spawn_depth == 2` corrected, not deleted. The ROADMAP
uc-payslip description (the current-state mirror that still claimed "Parallel
sub-agents via spawn_agent + wait_for_all") was corrected in the same change.
`payslip/milestone.md` left as-is: it is a point-in-time milestone record of the
as-built parallel design, not a current-state claim.

---

### BL-024 — Fork lineage queries (`fork_event_id` / "list forks of run X") (#TBD)
**Size:** M · **Priority:** low

BL-007 D4, deferred at that milestone with this entry as the record (README
"Open decisions" — *"Deferral gets a backlog entry, not silence"*).

BL-007 ships parent-link **display** only: Rig reads `fork_from`/`fork_step` from
the forked run's trajectory meta. The reverse query — *list the forks of run X* —
needs an index or a `config_json`-deserializing scan, neither of which exists.

- **Compose with `caused_by`, don't grow a parallel mechanism.** t0 landed the
  `caused_by` event-lineage field; a fork-only lineage index would be a second,
  overlapping causal structure. Any lineage query should build on general causal
  lineage.
- **The store is not single-shaped — design for two fork-provenance shapes.**
  Verified against 1,201 `fork_from`-bearing metas in the dev store: BL-007's
  `Fork.from_step` writes an **integer** `fork_step` (661 metas), while the older
  `replay-source-*` / `verify-*` producers write `fork_from` with `fork_step:
  **null**` (540 metas). The key is always co-present; only the value varies. A
  lineage view that assumes an integer step will mis-render or drop 45% of the
  existing rows. (Surfaced at t4 r2 F6; Rig already tolerates both via
  `fork_step?: number | null` plus a banner guard.)
- **Deferred verification, with its trigger.** The null-`fork_step` banner render
  is currently unverified end-to-end because those runs are file-only and do not
  appear in the runs list. **Trigger: when file-only runs become listable, that
  ticket's e2e picks up the null-`fork_step` banner render.** Not a standalone
  e2e — it rides the ticket that makes it reachable.

**Done when:** a lineage query exists that composes with `caused_by`, handles both
provenance shapes, and has an e2e covering the null-`fork_step` case.

---

### BL-025 — Verify: effect classes / record-and-serve for effectful tools (#TBD)
**Size:** M · **Priority:** medium — **DONE 2026-07-23**

**Landed.** `Aetheris.Execution.EffectClass` declares `:pure` / `:contained` /
`:uncontained` as the single source of truth; `Verifier` record-and-serves `:uncontained`
tools by default and reports them **served, not verified** (excluded from the verified
tally); `aetheris verify <traj> --allow-effects` opts back in. Proven by a hermetic
localhost listener: **0 inbound connections** under default verify, **1** under
`--allow-effects`. A completeness test asserts the classifier is total over
`Registry.names/0` and every in-process tool module, mutation-checked.

**Scope grew, by human decision in-cycle (rev 2, 2026-07-22).** `aetheris verify` never
reached `Verifier` at all — `Commands.Verify` started a fresh **live** run
(`mode: :verify`) and returned `verified: true` unconditionally. The CLI was rewired to
`Aetheris.verify_run/2` and now returns the real verdict with a failure-reflecting exit
code; the vacuous `verified == true` test was replaced with a mutation-checked pass/fail
pair.

**Contract edits (§8, human-approved in-cycle):** determinism-contract **§3** (verify row;
plus a new paragraph separating `verify` the command from `RunConfig mode: :verify`) and
**§5** (full rewrite: taxonomy, record-and-serve, served-not-verified, mechanized
tripwire). Draft: `docs/reviews/bl-025-contract-draft.md`.

**MCP scope note:** the MCP *family* is classified `:uncontained`, not `http_call` alone.
Because MCP tool names are discovered at runtime, classification falls back to the recorded
`"source"`/`"server_id"` — with `server_id == "aetheris_exec"` held `:contained`, since the
internal exec server routes `run_command` and all eleven `git_*` as MCP calls.

**BL-027 folded in (human call, 2026-07-23).** `verify_step/2` now reads the recorded result
through the same `"output"`-else-`"result"` fallback as the served path. Without it, BL-025
would have shipped the crash as the behaviour of the command it had just made real: any
trajectory with a failed contained tool call took verify down. See BL-027 for the red-first
evidence; the payload-key *convention* residue is BL-046.

**Deliberately not closed here:** capability-level egress safety. `run_command` stays
`:contained` (rev 3) and its allowlisted interpreters can still egress — named as a §5
limitation, tracked by **BL-042**. Follow-ups filed: BL-042, BL-043 (`http_call` is
SIGSYS-killed in every mode), BL-044 (`mix aetheris` discards exit codes), BL-045
(`mode: :verify` misnomer), BL-046 (payload-key convention).

---

**Original row:**

`verify` **re-executes** every recorded tool call against a live worker
(`verifier.ex:136`, `Client.execute/2`). For a pure tool that is the point; for an
effectful one it is a hazard. The motivating case: verifying a run that called
`http_call` performs the network egress **again** — real requests to a third party,
from what an operator reasonably reads as a read-only check. A verify over a run
with a destructive tool call would re-perform the destruction.

Determinism contract §5 names this; `verifier.ex:130-136` is the mechanism.

Shape to consider: classify tools as pure / effectful, and for effectful ones
*record-and-serve* the recorded output rather than re-executing — verifying the
transcript's consistency without re-entering the world.

**Done when:** verify cannot re-perform an external effect without an explicit
opt-in; `http_call` is covered by a test that asserts no egress during verify.

---

### BL-026 — Verify: divergence report names no first diverging event (#TBD)
**Size:** S · **Priority:** low — **PARKED ON TRIGGER**

**This row activates on its trigger, and not before. Trigger: the first `verify`
run against a multi-agent / orb trajectory.** Human-ratified 2026-07-19 (BL-007 t5
boundary). Until that trigger fires, this is recorded, not scheduled — do not pick
it up as ready work.

`VerifyReport` (`verifier.ex:176-186`) carries only `run_id`, `verified`, `failed`,
and a flat `steps` list; the renderer (`:188-242`) prints per-step rows. Nothing
identifies **the first step at which the run diverged** — the single most useful
fact when a verify fails, since later divergences are usually consequences of the
first. An operator gets a wall of per-step results and reconstructs the ordering by
eye.

**Done when:** a failing verify names the first diverging event/step explicitly,
and the trigger condition above has actually occurred.

---

### BL-027 — Verify: `KeyError` crash on paired in-process tools (#TBD)
**Size:** S · **Priority:** medium — **DONE 2026-07-23 (folded into BL-025)**

**Closed.** `Verifier.verify_step/2` now reads the recorded result through the same
`recorded_result/1` fallback (`"output"`, else `"result"`) that the record-and-serve path
uses — one reader, both paths. Red-first evidence, on a trajectory whose recorded
`read_file` **failed**:

```
** (KeyError) key "output" not found in:
   %{"is_error" => true, "result" => "Error: :enoent", "tool_name" => "read_file"}
   verifier.ex:201  Aetheris.Execution.Verifier.verify_step/2
→ after the fix: 6 tests, 0 failures; the step reports :output_mismatch with
  recorded_output "Error: :enoent" — a genuine divergence, legibly, instead of a crash.
```

**Why it was unparked rather than left on its trigger.** The stated trigger — a
multi-agent/orb trajectory — was **too narrow**, and the row's in-process framing was the
reason. `Loop.record_tool_error/7` writes *every* recorded tool failure under `"result"`
with `"is_error"` and no `"output"` key, including for **contained, worker-dispatched**
tools. So a single failed `read_file` or `run_command` — a routine shape, needing no orb —
crashed verify. BL-025 made `aetheris verify` actually route through `Verifier`, which would
have shipped that crash as the operator-visible behaviour of the command it had just made
real. Human call, 2026-07-23: fold the fix in rather than release that state.

BL-025's record-and-serve independently removed the *in-process* face (those tools are
`:uncontained` and no longer dispatched), so the residual this fix closes is precisely the
contained-tool face the original row did not describe.

**Not closed here — tracked as BL-046:** the payload-key *convention* itself, shared with
BL-028. This row fixed the reader; it did not unify the writers.

---

**Original row:**

**Same trigger and ratification as BL-026: activates on the first `verify` run
against a multi-agent / orb trajectory.** Human-ratified 2026-07-19. Recorded, not
scheduled.

`verify_step/2` reads the recorded tool output with
`result_event.payload |> Map.fetch!("output")` (`verifier.ex:133`) — a hard fetch,
not a lookup with a default. But **in-process** tool writers emit the payload under
`"result"`, not `"output"` (`loop.ex:421-497`). So verifying a trajectory whose
tools ran in-process raises `KeyError` and takes the verify down.

The tools that hit this are exactly the orb/coordination ones —
`wait_for_event`, `read_blackboard`, `write_blackboard` — which is why the trigger
is a multi-agent/orb trajectory: that is the first trajectory shape that can
contain them, and the crash is unreachable until one exists.

**Trigger correction (BL-025, 2026-07-23) — the stated trigger is too narrow, and the
in-process framing is now stale in both directions.** Two changes:

1. **The crash never needed an orb trajectory.** `Loop.record_tool_error/7` writes *every*
   recorded tool failure — including worker-dispatched, contained tools — under `"result"`
   with `"is_error" => true` and **no `"output"` key at all**. So a trajectory containing a
   single failed `read_file` or `run_command` reaches the same `Map.fetch!` and crashes
   verify. Demonstrated at BL-025 against a recorded `http_call` failure before that tool
   was reclassified:
   `** (KeyError) key "output" not found in: %{"is_error" => true, "result" => "Error: :timeout", …}`
   at `verifier.ex:133`. The parked-on-trigger status understates reachability accordingly.

2. **BL-025 sidesteps the in-process case without fixing this row.** The in-process tools are
   now classified `:uncontained` and record-and-served, so verify no longer dispatches them
   and the `"result"`-key crash is unreachable *for them*. The residual — and the real scope
   of this row now — is a **`:contained`** tool whose recorded result is an error. Do not
   read BL-025 as having closed this; the hard fetch on the re-execution path is untouched.

Fix shape unchanged: read the recorded result with a fallback (`"output"`, else `"result"`),
as `Verifier.serve_step/1` already does on the served path — the two paths should share one
reader.

Note the shared root cause with BL-028: two independent consumers of recorded tool
results each assume `"output"` while a family of writers uses `"result"`. Worth
fixing as one payload-key convention rather than two point patches.

**Done when:** verify tolerates both payload keys (or the writers converge on one),
with a test over an orb trajectory — and the trigger has occurred.

**Evidence base (added 2026-07-21, BL-028 round 2 — annotation only; trigger,
ratification and parked status all stand unchanged).** Root-cause map and fix-space
analysis in BL-028's implementation notes
(`../aetheris/docs/aetheris/milestones/bl-028-implementation-notes.md`). Note in
particular: `record_tool_error/6` writes `"result"` (`loop.ex:354`) for **every**
recorded tool error regardless of which tool raised it — so the `KeyError` is
reachable on any trajectory containing a tool error, not only orb trajectories. The
trigger's wording stands as ratified; its reachability is wider than the row's
"multi-agent / orb" framing implies.

---

### BL-028 — Fork reconstruction drops `"result"`-keyed tool output (#TBD)
**Size:** S · **Priority:** medium

`event_to_messages(:tool_result)` reads `Map.get(payload, "output", "")`
(`fork.ex:101-105`). Many in-process tool writers store the payload under
`"result"` instead (`loop.ex:354,424,435,450,459,469,482,492,508`). Because the read
**defaults to an empty string**, those tool results reconstruct as tool messages
with **empty content** — silently. The fork starts from a transcript in which the
tools appear to have returned nothing, and nothing in the output says so.

Silent-empty is the dangerous part: a fork that should have failed loudly instead
proceeds from a subtly wrong context.

`fork.ex`-local fix, but a behaviour change beyond t2's four goals, which is why t2
surfaced rather than fixed it. Shares its root cause with BL-027 — see that entry.

**Done when:** fork reconstruction carries `"result"`-keyed tool output, with a
test asserting non-empty reconstructed content for an in-process tool.

**Status:** Done 2026-07-21 — read-side fix in `event_to_messages(:tool_result)`
plus `normalize_content/1` (nil → `""`, non-binary → JSON-encoded; contract §2's
string invariant), commit `9b2b102`. Three test arms, each verified red-first.
Citations above describe the pre-fix file and are left as written; post-fix
locations in the contract's repaired citations and
`../aetheris/docs/aetheris/milestones/bl-028-implementation-notes.md`. BL-027
annotated same round (`16de968`), not reopened. Review:
`docs/reviews/bl-028-review.md`.

---

### BL-030 — Early-return `fork_run` (spawn without blocking to completion) (#TBD)
**Size:** M · **Priority:** medium

`mix aetheris fork` blocks until the forked run finishes: the CLI reveals the new
run id only via `RunHelpers.await_run/1` at the end (`fork.ex:37`,
`run_helpers.ex`). Every consumer inherits the block — Rig's "Fork from here"
button sits disabled for the full run, which for a real fork is minutes.

Wanted: a spawn-and-return-early shape like `orchestrate_start`, which needs the
**harness CLI to emit the run id at fork-start** rather than at completion. Once it
does, Rig can navigate to the child immediately and let it stream.

Harness-touching enhancement, ratified-tracked at BL-007 t3 and explicitly not t3
or t4 scope — the t4 affordance ships against the blocking contract on purpose.
Pairs naturally with BL-031: an early-return fork makes the unbounded `await_run`
loop far less load-bearing.

**Done when:** the fork CLI can emit the run id at start; Rig's affordance returns
without waiting for completion.

**Status:** Done 2026-07-26. Harness: `cli/commands/fork.ex` emits the run id
between `start_fork/3` and `await_fork/1`, per resolved mode
(`{"status":"forked","run_id":…}` under `--json`); `output_mode/1` moved from
`Aetheris.CLI` to `Formatter.resolve_mode/1` so the command can resolve the same
mode the closing `print/2` uses. The CLI still blocks to completion — deliberately:
the fork run is a Task in the CLI process's own supervision tree, so an early
return would kill it. Rig: `fork.rs` spawns piped and owns the child, returns at
the first `run_id` line, and hands the running subprocess to a detached thread that
drains both pipes and reaps; `handleForked` sets `status: 'running'` so
`TrajectoryView`'s existing BL-005 events-fallback polling streams the child.
`--detach`/`--follow` untouched (daemon path). Notes:
`docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md` +
`../aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md`. Scout:
`docs/reviews/bl-030-fork-early-return-scout.md`. Review: `docs/reviews/bl-030-review.md`
(r1, approve; F1 non-blocking, fixed at harness `f79365a`).

**Closed 2026-07-26 after three rounds and a confirmed GUI pass.**

- **r0** — the early-return fork itself (harness `ae0c510`, agents `b5e8eee`).
- **r1** — completion transition, folding BL-063 (agents `4bf0fd6`). A fork
  watched to completion stayed in BL-005 reconstructed mode: the trajectory file
  that now existed was never re-read, so provenance / `started_at` / duration
  appeared only after a manual tab-out/in. Scouted first, and the scout changed
  the mechanism: the `run_complete` **event** precedes the file write
  (`loop.ex:267` → `server.ex:680` → `server.ex:456`), so a reload triggered by
  the event races it, while one gated on the row's **terminal status** cannot.
  Status-gated, no retry. Packet `docs/reviews/bl-030-r1-review-packet.md`.
- **r2** — source-seeded selection (agents `c2af6cf`). r1's per-consumer fix left
  the Events header reading the synthesized summary directly: `new Date('')` →
  "Invalid Date", with `label` and `model` blank from the same cause. The
  **Adjacent-case** class — the blast radius was one consumer wider than the view
  the fix was written against. Closed at the source: `handleForked` now seeds the
  selection from the real `runs` row (`runSummaryFromDetail/1`), so the invented
  summary is gone and there is no consumer list to keep in step. Incidentally
  retires a documented compromise — a labelled fork now hands its label to a
  grandchild without a Refresh. Packet `docs/reviews/bl-030-r2-review-packet.md`.
- **GUI pass confirmed end-to-end** on the real app: Trajectory (r1) — provenance
  banner, the amber "live — reconstructed" banner clearing in place at completion,
  incremental steps; Events (r2) — real label, run_id, model and `Started:` date
  on first landing, no re-select.

Carried out of this ticket as their own rows: **BL-062**, **BL-064**, **BL-065**.

> **Dangling ref, deliberate.** Determinism contract §4 says "the CLI and Rig entry
> points pass a label only (BL-030)". That sentence is still **true** after this
> ticket — BL-030 did not add overrides — but its `(BL-030)` ref now points at a
> closed ticket that never carried them. The override work split out as **BL-062**,
> whose §8 edit repoints it. Flagged rather than left to rot: §4 already carries one
> decayed parenthetical (D2's `cli/commands/fork.ex:47-55`, per the scout), so this
> section has form.

---

### BL-031 — `await_run` has no timeout or cap (#TBD)
**Size:** S · **Priority:** medium

`await_run` (`cli/commands/run_helpers.ex`) is a poll-forever loop —
`Process.sleep(200)` + `Store.get_run`, with **no bound**. If a terminal status
never lands, the CLI spins forever, and so does any Rig `invoke` wrapping it.

This was the **amplifier**, not the cause, of BL-007 t4's field hang: a store
`:busy` crash stopped statuses landing, and the unbounded loop turned that into an
indefinite hang. t4 fixed the store side (`059c92e`), so statuses land and the loop
terminates today — which is exactly why this stayed out of that emergency fix
(scope held to three store changes).

It remains a latent resilience defect: **any** future cause of a stuck
non-terminal status reproduces the hang, with no timeout to convert it into a
legible error. Surfaced at t4 r3 F7.

**Done when:** `await_run` bounds its wait and returns a timeout error naming the
run and its last-seen status.

**Status:** Done 2026-07-21 — inactivity bound on `{status, max_event_seq}` with
paused-run exemption via `Aetheris.RunPause` (shared with Sweep by construction),
config key `:await_inactivity_timeout_ms` default 300 000; harness `4392194`+`a935038`,
notes/agents `6defe0e`+`d0690a6`; r2 also fixed a boot-crash regression in `Store`
event deserialization (compile-time type map) and filed BL-040. Review:
`docs/reviews/bl-031-review.md`.

---

### BL-032 — WAL connection-lifecycle follow-ups (#TBD)
**Size:** M · **Priority:** low

BL-007 t4 added `PRAGMA busy_timeout=5000` (load-bearing), `:busy` handling in
`run_stmt/3`, and `PRAGMA journal_mode=WAL` to `Store.init/1` (`059c92e`). WAL is
kept **opportunistic with a comment**: SQLite can only convert the journal mode
when no reads are in flight, so with Rig holding a read connection the store may
stay in `delete` mode indefinitely and convert later at idle. Verified: an idle
real store converts to `wal`; under continuous read-hammering it stays `delete` and
forks still exit 0. The fix does not depend on the conversion — but it does mean
**WAL adoption is not something the harness can currently guarantee**, and that is
a connection-lifecycle question, not a pragma question.

If WAL is genuinely wanted rather than opportunistic, the three follow-ups:

- **(a) Checkpointing / `-wal` growth.** Rig holding a long read snapshot prevents
  checkpointing; the `-wal` file can grow unbounded.
- **(b) Dirty-`-wal` recovery under a read-only connection.** A read-only
  connection cannot recover a dirty `-wal` left by a harness crash with no live
  writer. It resolves on the next harness write, but Rig reads can fail in that
  window.
- **(c) Observability.** WAL's success or failure is currently silent — log the
  post-pragma `journal_mode` so the mode in effect is a fact, not an assumption.

Surfaced at t4 r4.

**Done when:** a decision is recorded — either WAL is made deterministic via
connection lifecycle (with the three items addressed), or opportunistic WAL is
ratified as the permanent design and documented as such.

---

### BL-033 — Remove `:fork` from the `RunConfig` mode union (#TBD)
**Size:** S · **Priority:** low

`@type mode :: :record | :replay | :verify | :explore | :fork`
(`run_config.ex:115`) still lists `:fork`, but **no code path in the harness sets
or matches it.** `mode` is behaviourally significant only for `:replay` and
`:verify`; BL-007 t2 dropped `mode: :fork` from the CLI fork path deliberately, so
that forks are behaviourally identical to `fork_run/3`. Fork lineage is carried by
`fork_from`/`fork_step`, not by mode.

The member is therefore vestigial, and actively misleading: it invites consumers to
key off `meta["mode"] == "fork"`, which is **never** true for a fork.

Ratified at the BL-007 t5 boundary as *no code change now* — deleting it is a
harness code change outside the milestone that surfaced it. The
`../aetheris/docs/aetheris/architecture.md` Execution Modes table is annotated to
document the discrepancy in the meantime.

Check before deleting: nothing in-repo (or in Rig) pattern-matches `:fork`, and no
persisted `config_json` decodes to it.

**Done when:** `:fork` is removed from the union, or a reason to keep it is
recorded on this entry.

---

### BL-034 — `prompts/bl-002-refresh-project-knowledge.md` has a self-staling step order (#TBD)
**Size:** S · **Priority:** medium

The BL-002 prompt is **internally contradictory**, and has been since it was written.
Step 2 writes `docs/project-knowledge-manifest.md` with each file's current hash. Its
closing constraint then says to *append* a drift-baseline line to
`docs/rig/current-state-2026-06.md` — a file the manifest tracks. That append moves
`current-state`'s hash past the value just recorded, so the manifest is stale for that
row the instant the step completes. The same constraint also says to "run drift_check.py
once at the end to confirm exit 0 and **zero WARN**" — which the preceding instruction
has guaranteed cannot happen.

~~Evidence it fired in production, not just on paper: at the 2026-07-17 export
(`628f15f`) the manifest recorded `current-state` at `d24e482`, two commits behind
`628f15f`. The row was born stale.~~ — **WITHDRAWN as false, 2026-07-22. This claim was
never verified and does not hold; see the Evidence correction in the Status block below.
The hazard is real but latent — it never fired.**

The general rule the fix must encode: **any file the manifest tracks is edited *before*
the manifest is written, never after.** BL-007 Phase B hit this and sequenced around it
by hand — the manifest regen was made the last commit of the export, after the rider,
this row, and the notes had all landed.

Not fixed inline at BL-007 t5 Phase B because the Phase B scope was the export itself,
and editing the prompt mid-export is the same class of ordering mistake the row
describes.

**Done when:** the prompt's step order puts every manifest-tracked edit (including the
drift-baseline append) before the manifest write, and the "zero WARN" assertion is
reachable — or the baseline append is dropped from the prompt if it is not worth the
ordering constraint.

**Status:** Done 2026-07-22. Resolved by **dropping the baseline append** (decision:
drop, human call 2026-07-22). The append was the sole reason BL-002 wrote a
manifest-tracked file other than the manifest, so removing it makes the manifest the
only tracked write and trivially the last. **Three defects closed in
`prompts/bl-002-refresh-project-knowledge.md`:** (1) the ordering hazard this row
describes; (2) the `exit 0 and zero WARN` done-check the committed append made
unreachable; (3) an adjacent self-contradiction the row did not name — the constraint
declared current-state read-only (`read-only outside …manifest… and /tmp`) then ordered
a write to it four lines later. Defects (2) and (3) are demonstrable from the prompt
text alone.

**Evidence correction (supersedes this row's "it fired in production" claim).** The line
above — "at the 2026-07-17 export (`628f15f`) the manifest recorded current-state at
`d24e482`, two commits behind … born stale" — is **WITHDRAWN as false** (struck in place
above). A check-8 sweep of all 38 committed manifests is clean (38/38); no manifest was
ever born-stale. The two hashes are real (`d24e482` = the BL-001 baseline commit;
`628f15f` = a real export commit — the export HEAD named in manifest commit `d11464f`'s
Exported line, not a manifest commit itself) but the "two commits behind" relationship
between them was never checked — a **Cited-means-read** instance. At `d11464f` the
manifest pinned `current-state` at `d24e482` and the file genuinely last changed at
`d24e482`; the row was correct. The comparison made was per-file pin vs export HEAD, and
a per-file pin always lags HEAD — that is what it records. The hazard is real but
**latent, never fired**; the drop stands on the prompt's textual self-contradiction plus
latent-staleness, not on a production instance. The same false claim also appears in the
b1–b3 export manifest narrative (`docs/project-knowledge-manifest.md`, "reproducing the
2026-07-17 instance at `628f15f`") — it must **not** be repeated in the next manifest
regen; flagged here so the correction chases forward rather than silently recurring. The
manifest is deliberately not edited by this ticket (an out-of-scope tracked write).

The general rule is now encoded as a standing invariant in the prompt itself (the
manifest is the last tracked write; no manifest-tracked edit after Step 2), so a future
re-addition reads as the regression it is. The per-export drift-baseline capture is
intentionally **not** relocated — BL-001 (#42) captured the one-time clean baseline and
is Done; nothing consumes a per-export refresh. The overdue 2026-07-22 baseline is closed
by the same removal (no baseline is owed in current-state). The prompt file is not
manifest-tracked, so the fix stales nothing; this row's own edit stales
`backlog-2026-06.md` until the next export (expected, strict-exempt).

---

## Rig (aetheris-agents/rig/)

### BL-005 — TrajectoryView fallback for live runs (#46)
**Size:** S–M · **Priority:** medium

`trajectory.json` is written atomically at run end (`server.ex:673,944`
via `file.ex:37-38`) — the file does not exist while a run is live, so
TrajectoryView errors for `status='running'`.

- On `trajectory_load` failure for a running run, build the same view from
  `harness_get_events`: `EventRow.payload` is a JSON *string* (SQLite) vs
  the file's inlined object — parse per row; payloads are complete/
  untruncated in both stores, so fidelity is identical.
- Reuse the existing step-grouping; show a "live — reconstructed from
  events" banner; optionally reuse the p2 polling hook for live append.
- `meta` is unavailable pre-completion except via `runs.config_json` —
  render what's derivable, leave the rest blank.
- Update the runbook troubleshooting entry ("use the Events tab for live
  runs") to reflect the new behavior.

**Done when:** opening Trajectory on a running run shows events instead of
an error; completed runs unchanged.

**Status:** Done 2026-07-15. `TrajectoryView` falls back to
`harness_get_events` + `harness_get_run` on `trajectory_load` failure and
rebuilds the step-grouped view via `src/lib/reconstructTrajectory.ts`; the
`run` prop replaces `runId` so the banner can vary by status. **Scope
widened** past "for a running run" per the ticket's own recommendation:
BL-003 swept 66 orphaned runs to `failed` with no trajectory file either, so
the fallback triggers on any `trajectory_load` failure, with the banner
reading `live — reconstructed from events` (running) vs `trajectory file
unavailable — reconstructed from events` (terminal — covers absent *and*
corrupt/`.tmp` files, with the read error logged to console). p2 polling reused
for live append (decision: **in** — free via the existing `useRunEvents` hook).
Fidelity verified byte-identical against a real 58-event `trajectory.json`,
guarded durably by `rig/scripts/verify-reconstruct-trajectory.ts`. Export JSON
hidden in reconstructed mode. No new Tauri command (specs §4 unchanged).

---

### BL-006 — Document `stop_reason` when first observed (#47)
**Size:** S · **Priority:** tracked (event-triggered, not scheduled)

Confirmed absent from all current DB events (count = 0). The trigger is
mechanical: when drift_check emits
`INFO payload_fields: llm_responded.stop_reason in DB events but not
listed in specs.md §6`, add `stop_reason` to the §6 `llm_responded` row —
no `?` suffix needed, since by then it is observed. The `?` convention
exists for the general case; this ticket just records the trigger.

**Done when:** the INFO fires once and the field is promoted.

---

### BL-017 — Resolve `react-hooks/set-state-in-effect` lint failures (#68)
**Size:** S–M · **Priority:** after BL-016 (standing-red gate)

`bun run lint` (`eslint .`) is red on `main`: **31** `react-hooks/set-state-in-effect`
errors across ~15 files. Origin is a bump of `eslint-plugin-react-hooks` that
promoted the rule to error — undated, because the gate had not been run
whole-project until BL-005 ran it off-territory (per the gate-boundary rule now
in `CLAUDE.md`). The flagged pattern is the idiomatic `if (!id) { setData(null) }`
reset at the top of the data hooks (`useHarness`, `useTrajectory`, `useRunDiff`,
the `use*` corpus/provenance hooks) plus a few views (`OrchestratorView:140`,
`PlaygroundView:295/325/333/341`). No BL-005 file is among them.

**Decide first, before touching any site:** does this codebase *adopt* the rule
(refactor all ~15 sites so effects don't call `setState` synchronously — the
lint-clean-per-file path) or *reject* it (disable the rule in `eslint.config.js`
with a comment stating why the guard pattern is acceptable here)? Pin the
decision in this ticket; do **not** let it be settled implicitly by silencing
errors file-by-file.

**Done when:** ~~`bun run lint` exits 0~~, and the adopt-vs-reject decision is
recorded (in the rule-config comment if rejected, or in the notes if adopted).

**Divergence noted (per the standing rule):** the "31 = one rule" premise was a
miscount — the true split is **28 `react-hooks/set-state-in-effect` + 3
`react-refresh/only-export-components`** (BL-016's gate line read only the
eslint tail). So BL-017's done-when is corrected to: *the 28
`set-state-in-effect` errors cleared, the reject decision recorded, and the
residual 3 tracked as BL-018 (#69)*. `bun run lint → exit 0` is delivered
jointly with BL-018 at one shared export boundary, not by BL-017 alone.

**Status:** Done 2026-07-16 (decision: **reject**, 2026-07-15 human call on
claude-ui recommendation). `react-hooks/set-state-in-effect` disabled rule-level
in `rig/eslint.config.js` (not 28 per-site comments) with the decision recorded
in the config comment: functionally-correct data-hook resets, rule targets
render hygiene not bugs, ~22 sites with no frontend test runner → refactor risk
without a net; revisit when a test runner exists. Lint went 31 → 3. The residual
3 are a different rule class (react-refresh) — surfaced as a finding, not swept
— and are BL-018's scope. See `docs/reviews/bl-017-review.md`.

---

### BL-018 — Resolve `react-refresh/only-export-components` lint failures (#69)
**Size:** S · **Priority:** immediately after BL-017 (joint lint-green endpoint)

The residual behind BL-017's rule disable: **3** `react-refresh/only-export-components`
errors, pre-existing since 2026-05-31 (`ed63058`), hidden behind the 28
`set-state-in-effect` errors until BL-017's verify step surfaced them (origin:
BL-017 packet). Fast-refresh requires that a file exporting a component export
nothing else:

- `rig/src/components/ui/badge.tsx:37` — exports `badgeVariants` (cva helper)
- `rig/src/components/ui/button.tsx:67` — exports `buttonVariants` (cva helper)
- `rig/src/context/AppContext.tsx:103` — exports the `useApp` hook

Unlike BL-017's rule, this one has a standard zero-risk fix (extract the
non-component exports to their own modules), verifiable by `tsc -b` + `bun run
build` without a frontend test runner — so it is fixed, not disabled.

**Touches:** the 3 source files + new sibling modules (`badge-variants.ts`,
`button-variants.ts`, `app-context.ts`, `useApp.ts`) + `useApp` import sites
(Sidebar, RightPanel, TopBar); backlog status; the shared manifest regen.

**Done when:** `bun run lint` exits 0 (the joint endpoint BL-017 and BL-018
deliver together), `tsc -b` + `bun run build` green, decision-comment convention
followed (each new module cites BL-018 / #69).

**Status:** Done 2026-07-16. `badgeVariants`/`buttonVariants` extracted to
`*-variants.ts`; `AppContext` object + types to `app-context.ts` and the `useApp`
hook to `useApp.ts`, leaving `AppContext.tsx` exporting only `<AppProvider>`; the
3 `useApp` importers repointed. Verified `bun run lint → exit 0` (31 → 0),
`tsc -b` 0, `bun run build` 0 (1908 modules); no behavior change. This is the
shared export boundary that also clears BL-016's carried staleness WARN — its
named endpoint moved one ticket later than promised (BL-016 → BL-018), dated
here so the carry stays honest.

---

### BL-019 — Harness runbook: sweep section + mirror convention (#70)
**Size:** S · **Priority:** now (before BL-007 planning)

BL-003's operational docs single-homed on the Rig side (`docs/rig/runbook.md`,
agents repo — per that ticket's Touches). The harness's own
`docs/aetheris/runbook.md` has no sweep entry, so a harness-side operator finds
nothing on `mix aetheris sweep`, the config knobs, or the startup hook. The gap
was invisible by construction: harness-side docs (methodology excepted) sit
outside every detection mechanism built this cycle — no manifest row, no drift
check, no export. Surfaced by human spot-check 2026-07-16.

Three parts: (1) sweep section in the harness `runbook.md`, describing
**observed** behavior — one real harness start performed during the ticket
confirms the startup hook's log line; (2) a header codifying the mirror
convention (the BL-016 mirror-vs-record distinction, applied); (3) decision —
manifest-track the harness runbook: **yes** (claude-ui recommendation; BL-007 has
operational surface and will touch this file — untracked mirrors are how this
cycle started).

**Done when:** sweep section present and matching observed behavior; convention
header in place; manifest row added; `drift_check --strict` exit 0 at the
closeout export.

**Approved deviations (on record, per the standing rule):**
- **Touches widened to `docs/rig/runbook.md`.** The Rig entry already carried the
  knob defaults/rationale and behavioral detail, so writing the harness section
  without trimming Rig would leave the same facts in two docs — and `drift_check`
  compares each doc against its *own* repo's git history, never cross-doc
  agreement, so divergence would be silent. That is the one rot class the tooling
  cannot see. BL-017/018's scope split separated *different fix classes*; this is
  one docs-only restructure of a single feature across its two mirrors, where
  splitting would manufacture the inconsistency rather than prevent one.
- **Convention wording supersedes the ticket's draft.** The drafted rule
  ("`runbook-m*.md` files are point-in-time milestone records") was written from
  inference; `ls` proves that glob also matches `runbook-model-comparison.md`, a
  *living* topic guide, which the rule would have frozen by name-accident. The
  taxonomy is three-way and **enumerated**: status is a property of the file, not
  its name — a category rule defined by filename pattern is exactly what failed.
- **Rider taken:** one-line status headers added to the three living topic guides
  so category is visible from inside each file, not only from `runbook.md`.

**Status:** Done 2026-07-17. Harness `runbook.md` gains: the three-category
convention header (canonical-for-current-state / milestone records / living topic
guides, plus a self-maintaining "add it to the correct list" line); `mix aetheris
sweep` in the CLI commands block; and a `## Orphan sweep` section placed after
*Checkpoint and resume* to mirror real boot order (resume → sweep). The section
documents the five-way verdict table, the `finished_at`-never-sweep-time rule,
both config knobs, idempotency, BL-003's worked census, and the highest-value
operational gotcha — a *just-killed* run reports `skipped_recent`, not a cure, and
only sweeps once staleness exceeds the threshold. Observed-behavior check ran
against the real DB; log line matched BL-003's documented behavior exactly, so the
"finding, not write-around" clause did not fire. Rig entry trimmed to badge +
cure command + cross-ref. `aetheris--runbook.md` joins the manifest — the harness
runbook enters project knowledge for the first time.

---

### BL-020 — Update HTTP-stack dependencies carrying security advisories (#71)
**Size:** S–M · **Priority:** medium

Surfaced by the clean-clone smoke test 2026-07-17. `mix deps.get` on a fresh clone
prints "Found packages with security advisories"; `mix hex.audit` itemises them —
all in the HTTP stack (the Bandit / Req dependency chain):

| Package | Advisories |
|---|---|
| `req 0.5.17` | EEF-CVE-2026-49755 (**HIGH**), EEF-CVE-2026-49756 (LOW) |
| `plug 1.19.1` | EEF-CVE-2026-54892 (**HIGH**), EEF-CVE-2026-8468 (**HIGH**), EEF-CVE-2026-56814 (MEDIUM), EEF-CVE-2026-56813 (LOW) |
| `mint 1.8.0` | **8 advisories** — 49754 (HIGH), 48862 (HIGH), 56810 (HIGH), 58229 (HIGH), 49753 (MED), 59246 (MED), 59249 (MED), 48861 (LOW) |
| `hpax 1.0.3` | EEF-CVE-2026-58226 (**HIGH**) |

> **Table corrected 2026-07-17 by BL-020's pre-audit capture (a finding).** As
> first written, the `mint` row listed only 56810, putting the total at 8. The
> true count is **15**: `mint 1.8.0` alone carries **8** advisories. This was not
> upstream drift — the clean-clone smoke test was the same day — it was a
> reporting error: the table was composed from two *truncated* views of
> `mix hex.audit` (`head -20` and `tail -8`), capturing the first seven entries
> and the last one. Same failure mode as the BL-016 gate-line miscount:
> characterising a tool's output from a fragment. Note that BL-017's hardening
> ("gate lines quote the tool's actual summary line") would **not** have caught
> it — `hex.audit`'s summary line, `Found packages with security advisories`,
> carries no count. The generalised lesson: never compose a factual table from a
> truncated view; capture the whole output or count it programmatically.

No CI gate fails on these — deps resolve, `compile --warnings-as-errors` is clean,
suite green 857/0 from a clean clone. That is *why* they went unnoticed:
`hex.audit` is not in the gate set, so the advisories are invisible to every check
that runs at a ticket boundary. Reachable surface, not dormant: `req` backs the
LLM adapters, `plug`/`bandit` back the playground HTTP API.

- `mix deps.update` across the HTTP chain; re-run the full gate line.
- Sensitive area on update: the adapters' retry/timeout handling (see the
  `receive_timeout` note in CLAUDE.md — socket timeouts must stay terminal, not
  `:retry`).
- Open question for the ticket: should `mix hex.audit` join the CI contract, so
  this class surfaces at a boundary rather than by clean-clone spot-check?

**Done when:** `mix hex.audit` clean, or each residual advisory explicitly
accepted with a recorded rationale; full gate line green.

**Status:** Done 2026-07-17. `mix hex.audit` → **`No retired or security advisory
packages found`** (exit 0). All 15 advisories cleared; **no residuals**, so the
accept-with-rationale path was not needed and no human decision is pending.

Version delta (`mix deps.update req plug mint hpax`; `mix.lock` only — **`mix.exs`
unchanged**, since `~> 0.5` already permitted 0.6.x and `~> 1.0` permitted 1.20.x;
no constraint conflicts, no forced overrides):

| Package | Before | After | |
|---|---|---|---|
| `req` | 0.5.17 | **0.6.3** | target (0.x minor — see below) |
| `plug` | 1.19.1 | **1.20.3** | target |
| `mint` | 1.8.0 | **1.9.3** | target |
| `hpax` | 1.0.3 | **1.0.4** | target |
| `finch` | 0.21.0 | 0.23.0 | resolver-dragged (via req) |
| `telemetry` | 1.4.1 | 1.4.2 | resolver-dragged |

Six packages, nothing else — no opportunistic updates, so the diff stays
auditable *as* a security patch.

**`req 0.5.17 → 0.6.3` crossed a 0.x minor boundary** (breaking-change territory
for a 0.x library) and `req` backs every LLM adapter — the sensitive area. Verified
rather than assumed: `test/aetheris/execution/llm_adapter/gemini_test.exs:351`
("Req.TransportError timeout is terminal and not retried") stubs
`Req.Test.transport_error(conn, :timeout)` and asserts both that the error
surfaces (`{:error, "receive timeout"}`) **and** that it prevented the retry
(`call_count == 1`). It passes under 0.6.3, so `Req.TransportError`'s shape and
semantics survived the bump. No adapter code changed.

**Finding — asymmetric coverage (surfaced, not filled).** The identical terminality
branch exists in **two** adapters — `gemini.ex:79` and `anthropic.ex:91` — but only
Gemini has a test. Anthropic, the *primary production adapter* and the one CLAUDE.md's
`receive_timeout` note is explicitly written about, has none; its correctness here is
verified only by symmetry with Gemini (identical clause shape, and compilation proves
the struct still exists). Low risk, genuinely unverified. ~~Related: `ollama.ex` and
`openrouter.ex` set `receive_timeout` but never match `TransportError` at all, so a
socket timeout there falls to `{:error, _} -> {:error, :retry}` — the exact behavior
CLAUDE.md forbids.~~ Worth a ticket.

> **Correction 2026-07-17 (BL-021 verify step) — the struck sentence was false.**
> The anthropic coverage gap above is real and stands. The ollama/openrouter claim
> was not: **neither adapter has a `:retry` fallthrough, because neither retries
> anything.** `:retry` is an adapter-*internal* protocol consumed only by each
> adapter's own `with_retry/2`; `ollama.ex` and `openrouter.ex` have no
> `with_retry/2` and never emit `:retry`. Their catch-alls, quoted verbatim:
>
> ```elixir
> # ollama.ex:63 (call_native) and :83 (call_xml)
> {:error, reason} ->
>   {:error, "Ollama request failed: #{inspect(reason)}"}
>
> # openrouter.ex:49
> {:error, reason} ->
>   {:error, "OpenRouter request failed: #{inspect(reason)}"}
> ```
>
> Terminal binaries. A socket timeout in those adapters was **already terminal**;
> CLAUDE.md's rule governs adapters that retry, and is vacuously satisfied there.
> There was no live bug.
>
> **How the error was made:** `anthropic.ex`'s catch-all *is*
> `{:error, _reason} -> {:error, :retry}`. That file was read; ollama/openrouter
> were only *grepped* for `TransportError` (0 hits), and their catch-all shape was
> **inferred from the sibling** and asserted with `file:line` citations that made
> it look verified. Grep proved absence of X; it was treated as proving presence of
> Y. The citations are why it passed two reviews and propagated into BL-021 (#72)
> and BL-022's item 3. Promoted to CLAUDE.md as **Cited-means-read** (author side)
> and **Demonstration-not-citation** (reviewer side), extending **Complete-output**
> — which would *not* have caught this, since no output was truncated; the lines
> were simply never read.

**Gate recommendation on the pinned open question** — *should `mix hex.audit` join
the gate set?* **Adopted 2026-07-17** (human call on claude-ui recommendation).
`mix hex.audit` now sits in the harness CI contract after `deps.get`, with the
accept path written into CLAUDE.md rather than left implicit: advisories cannot be
suppressed (no ignore mechanism), so when no patched version exists the accepted
advisory gets a backlog rationale and the gate runs **expected-red, named with its
ticket ref** per the tracked-carry clause. Upstream-triggered red — a new advisory
arriving through nobody's commit — is the gate working, not a defect, and gets a
ticket the day it is found. Adopted knowingly with that tradeoff on record.

---

### BL-021 — Adapter socket-timeout terminality: test all four adapters (#72)
**Size:** S · **Priority:** next (runnable standalone, harness-side)

> **Re-scoped 2026-07-17 by its own verify step, before any code was changed.** As
> filed, this ticket had two parts: (a) a coverage gap, (b) a "live violation" in
> ollama/openrouter. **(b)'s premise was false and (b) is withdrawn** — see the
> correction note in §BL-020 for the verbatim catch-alls and the how-it-happened.
> In short: `:retry` is an adapter-*internal* protocol consumed only by each
> adapter's own `with_retry/2`; ollama and openrouter have **no `with_retry/2` and
> never emit `:retry`**, so their socket timeouts were already terminal. There was
> no bug. The claim came from inferring their catch-all's shape from
> `anthropic.ex` and asserting it with citations to lines never read.

Origin: BL-020's packet. Verifying that `req 0.5 → 0.6` had not changed
`Req.TransportError` semantics surfaced that terminality is *tested* unevenly
across the four LLM adapters. CLAUDE.md's `receive_timeout` note requires
`%Req.TransportError{reason: :timeout}` be matched as **terminal**, never
`:retry` — a rule that binds adapters which retry, and is vacuously satisfied by
adapters which do not.

Actual state, verified by reading every catch-all:

| Adapter | `with_retry/2` | Timeout path | Was |
|---|---|---|---|
| `anthropic` | yes | `TransportError` clause (`:91`) precedes the `:retry` catch-all (`:94`) → terminal | correct, **untested** |
| `gemini` | yes | same shape (`:79` before `:82`) | correct, tested |
| `ollama` | **none** | catch-all → terminal binary | correct by construction, untested |
| `openrouter` | **none** | catch-all → terminal binary | correct by construction, untested |

**(a) Test the Anthropic terminality branch.** The load-bearing part.
`anthropic.ex:91` sits *before* the `{:error, _reason} -> {:error, :retry}`
catch-all, so without it a timeout reaches `with_retry/2` and is retried 6× with
exponential backoff — the exact CLAUDE.md scenario. Untested until now. Template:
`gemini_test.exs:351`, non-vacuous (error surfaces **and** `call_count == 1`).

**(b′) Regression guards for ollama + openrouter — tests only, no code change.**
Not vacuous: they lock in current-correct behaviour and fail the day someone adds
`with_retry/2` without excluding `TransportError`. The exact message is incidental
and deliberately unpinned; the load-bearing pair is *terminal (never `:retry`)*
and *exactly one call*.

**Done when:** all four adapters have a test asserting both that a socket timeout
surfaces as terminal and that no retry occurred; full gate line green (now
including `mix hex.audit`).

**Status:** Done 2026-07-17. Four tests, gemini's as the template for all.
`openrouter_test.exs` created (none existed; also gained an API-key-absent test).
**No adapter code changed** — none needed changing. The anthropic test was
**mutation-checked** rather than assumed load-bearing: removing the
`TransportError` clause makes it fail inside `with_retry/2` at
`Process.sleep/1` (anthropic.ex:113), blowing the 60 s ExUnit timeout — CLAUDE.md's
documented scenario reproduced. Findings promoted to CLAUDE.md as
**Cited-means-read** and **Demonstration-not-citation**. The 429-parity observation
became BL-023.

---

### BL-022 — Refresh harness architecture.md + manifest-track it (#73)
**Size:** S–M · **Priority:** before BL-007 milestone docs (input to fork planning)

`docs/aetheris/architecture.md` was last refreshed around m13 and predates the
entire hygiene cycle (confirmed: last touched **2026-05-22**, `56fd1f8`).
Surfaced by human spot-check 2026-07-17 (claude-ui review of the project-knowledge
copy) — the same way the runbook gap was found, and for the same reason: **the
file is in project knowledge but has no manifest row**, so no mechanism watches
it. Second instance of the harness-doc blind-spot class (first: BL-019).

Verified-stale items (all found against the project-knowledge copy — **re-verify
each against source**):

1. **Event-type list (§Trajectory.Log)** enumerates 12 types; the `event_type()`
   union has 22 (drift-verified at parity all cycle, incl. `run_orphaned` from
   BL-003). Regenerate the list *from the union*, not by patching the delta.
2. **"Adding a new event type" says two places; rule 14 is three** (`event.ex` +
   `file.ex` + specs §6, one commit, drift-enforced). Following the doc as written
   produces a drift FAIL. Cite rule 14.
3. **§Known Limitations `receive_timeout` claim — verify, then add per-adapter
   nuance + a coverage pointer.** *(Rewritten 2026-07-17: as first drafted this
   item said the "Fixed" claim was over-broad because ollama/openrouter "carry the
   forbidden `:retry` fallthrough". That premise was false — see §BL-020's
   correction note and §BL-021. It is corrected here rather than carried, since a
   ticket built on a false premise produces a wrong edit.)* Expected outcome is now
   that the claim is **accurate but under-specified**, not over-broad. Verify
   against source, then say what "fixed" means per adapter: `anthropic`/`gemini`
   retry transient errors via `with_retry/2` and exclude
   `%Req.TransportError{reason: :timeout}` explicitly, so the clause is
   load-bearing; `ollama`/`openrouter` have no retry mechanism at all, so their
   timeouts are terminal by construction and the rule is vacuously satisfied. All
   four now carry a terminality test (BL-021, #72) — point at them. Do **not**
   restate this as "all four fixed the same way"; the two mechanisms differ, and
   flattening them is how the original error started.
4. **Adapter list (repo structure) omits `openrouter.ex`.** While correcting it,
   spot-check the whole repo-structure tree against `ls` — one omission found by
   eyeball suggests others; verify, don't assume the rest is current.
5. **No sweep anywhere**: add `Aetheris.Sweep` to the component narrative and the
   application-start/boot-order description (reseed → resume → sweep → optional
   API). Cross-ref runbook §Orphan sweep rather than duplicating the verdict
   table — BL-019's dedup rule applies.
6. ~~**Execution Modes table lists "Fork" as a shipped mode.** What exists is
   `Eval.AB.run_forked/5` (m11); `Aetheris.fork_run` is BL-007, unbuilt. Footnote
   the row to say exactly that.~~ **FALSE — struck 2026-07-17 by this ticket's own
   verify step. The table is correct; no change made.** `Aetheris.fork_run/3`
   **exists** (`lib/aetheris.ex:73`), backed by `Fork.from_step/3`
   (`lib/aetheris/execution/fork.ex`, since 2026-05-17), a CLI command
   (`cli/commands/fork.ex`), tests in both `execution/fork_test.exs` and
   `cli/commands/fork_test.exs`, and `:fork` is first-class in the mode union
   (`run_config.ex:115`). Acting on this item would have added a **false footnote
   to accurate content** — the failure mode inverted: not a stale doc, a stale
   reviewer.
   **How it happened (reviewer-side `Cited-means-read` violation):** the claim was
   written from the backlog's BL-007 scope sketch and the roadmap — *planning*
   documents — and asserted as code state; `lib/aetheris.ex` was never opened.
   Planning docs describe intent, and intent reads like fact. Caught only by this
   ticket's own instruction to treat its items as leads and re-verify against
   source. See `docs/reviews/bl-022-review.md`.
7. **Trajectory-file layout shows `meta.json` as a separate file**; BL-005 treated
   `meta` as inline in `trajectory.json`. Verify on disk against a real run
   directory; correct whichever is wrong (specs §3 is the tiebreaker).
8. **Add the current-state-mirror header** per BL-019's convention (this file is
   canonical current-state; milestone docs are the frozen records), and **add the
   `aetheris--architecture.md` manifest row** — confirmed absent today; the only
   `architecture` row is `rig--architecture.md`.

While in the file, sweep for *other* post-m13 staleness beyond the eight — the list
above is what a review of the exported copy caught, not a guarantee of
completeness. Anything found is corrected and named in the packet.

**Done when:** all eight items resolved with source-verified corrections; header +
manifest row in place; `drift_check --strict` exit 0 at the closeout export; the
refreshed doc uploaded to project knowledge (the copy claude-ui reads during BL-007
planning is the point of the ticket).

**Sequencing:** run **after BL-021 (#72)** — item 3 writes cleanest as a statement
of fixed reality rather than an annotation of a known bug, and BL-021 is the
smaller, sharper ticket. Fresh session each: BL-021 touches adapter code with
tests, BL-022 is a doc-verification sweep — different modes, don't chain them to
save a `/clear`. The two boundaries may share one export if run back-to-back, or
close separately. *(BL-021 landed 2026-07-17; item 3 rewritten in light of it.)*

**Approved deviation (on record):** **Touches widened to `../aetheris/CLAUDE.md`**
to correct **rule 14** in the same boundary. Item 2 required architecture.md to say
"three places"; rule 14 said "two". Fixing only the doc would manufacture a
cross-mirror contradiction that no tooling detects — the BL-019 logic exactly. Rule
14's text now matches what `drift_check.py` has always enforced, with the
enforcement behaviour cited as the evidence. This is a correction to enforced
reality, not a new rule.

**Status:** Done 2026-07-17. Eight items verified against source before any write —
**six true, two false-premised**, both false ones authored by the reviewer from
exported/planning docs and both caught by this ticket's own instruction to treat its
items as leads rather than facts. Landed: three-category convention header;
event-type list regenerated **from the union** (12 → all 22, table-formatted); the
three-place rule with rule 14 corrected alongside; `openrouter.ex` added to the
adapter tree — plus the spot-check the item asked for, which found the tree stale
well beyond it (7 of 9 tools and 6 execution modules were missing, incl. `fork.ex`);
`Aetheris.Sweep` added to the component narrative and the boot-order section
(reseed → resume → sweep → API, with *why* the order is load-bearing), cross-ref'd
to the runbook rather than duplicating its verdict table; the `receive_timeout`
claim given per-adapter nuance and a coverage pointer, with an explicit note that
flattening the two mechanisms is how BL-021's false report began; and the trajectory
layout corrected — `meta` is inline, no `meta.json` has ever been written (verified
on disk and against specs §3). Item 6 **not acted on** — the table was already
correct. `aetheris--architecture.md` joins the manifest. Findings: BL-007's scope
sketch annotated (its harness half already shipped); rule 14 corrected; the
reviewer-side `Cited-means-read` instance appended to CLAUDE.md. See
`docs/reviews/bl-022-review.md`.

---

### BL-023 — Retry parity for hosted-provider adapters: 429 handling (#74)
**Size:** S · **Priority:** answered-and-parked (event-triggered, not scheduled)

Surfaced by BL-021's verify step, which read every adapter's error path and found
an asymmetry pointing the *opposite* way to the one BL-021 was filed about.
Recorded rather than acted on: this is a design question for the human, and the
answer may legitimately be "leave it".

Current retry behaviour, verified by reading each catch-all:

| Adapter | Retries | Hosted? | Rate-limits? |
|---|---|---|---|
| `anthropic` | 429, 529, + transient network errors (`with_retry/2`, 6× exponential backoff) | yes | yes |
| `gemini` | 429 + transient network errors (`with_retry/2`) | yes | yes |
| `openrouter` | **nothing** | **yes** | **yes** |
| `ollama` | **nothing** | no — local | no |

Ollama not retrying is defensible: it is a local process with no rate limiting.
**OpenRouter is the odd one** — a hosted, rate-limiting service with no 429
handling, so a rate-limit response surfaces as a terminal
`{:error, "OpenRouter HTTP 429: ..."}` and fails the step where anthropic/gemini
would back off and succeed.

**The question (human's to answer, do not decide in-ticket):** should hosted-provider
adapters have retry parity for 429? Reasonable answers include:
- **Yes** — add `with_retry/2` + 429 to openrouter, matching gemini. Note this makes
  the `TransportError` terminality clause **newly load-bearing there**, so it must be
  added in the same commit, and BL-021's regression guard is exactly the test that
  catches its absence — that guard was written for this.
- **No** — openrouter is used for cheap small-model experiments where failing fast
  is preferable to a 63 s backoff; the eval runner's window is short.
- **Not yet** — no observed 429 from openrouter in practice; wait for the trigger
  (the BL-006 pattern).

**Done when:** the question is answered and recorded here. If the answer is yes, the
implementation follows as its own scoped work.

**Answered 2026-07-17: not yet** (human call on claude-ui recommendation). Parked
with a trigger, per the BL-006 convention — waiting on a named event, not on
anyone's attention.

- **Trigger:** an observed 429 from OpenRouter in a real run's trajectory.
- **On trigger:** add `with_retry/2` + 429 matching gemini's shape, with the
  `%Req.TransportError{reason: :timeout}` terminality clause **in the same
  commit** — retry logic and the timeout exclusion are one change, never two.
  BL-021's (#72) `openrouter_test.exs` regression guard is the test that enforces
  it: it asserts terminal-never-`:retry` and exactly-one-call, so it fails the
  moment retry arrives without the exclusion. That guard was written for this
  branch.
- **Until then:** fail-fast stands. OpenRouter surfaces a 429 as a terminal
  `{:error, "OpenRouter HTTP 429: ..."}`, which is the intended behaviour for
  cheap small-model experiments where a 63 s backoff would exhaust the eval
  runner's window.

---

### BL-029 — Rig reads the run label from the wrong place, for every run (#TBD)
**Size:** S · **Priority:** medium

Both Rig harness queries read the run label out of `config_json`:

- `harness_list_runs` — `COALESCE(json_extract(r.config_json, '$.label'), r.run_id)`
  (`rig/src-tauri/src/commands/harness.rs:82-84`)
- `harness_get_run` — same shape (`harness.rs:196`)

But the harness **strips `label` from `config_json` before persisting it**:
`encode_config/1` does `Map.delete(:label)`
(`../aetheris/lib/aetheris/agent/server.ex:758`). The label lives in the dedicated
`runs.label` column (`../aetheris/lib/aetheris/store.ex:807`, backfilled by
`ensure_runs_label_column/1` at `:989`).

So the `json_extract` always returns NULL and the `COALESCE` always takes the
fallback: **Rig displays `run_id` as the label for every run.** The feature reads as
"labels aren't set" rather than as a bug, which is why it survived this long.

Not fork-specific — it affects every run in the list. Surfaced at BL-007 t3 while
chasing why forked runs showed no label; the t4 fork invoke omits `label`
accordingly, and can pass it once this lands.

One-line-per-site fix: read `r.label` / `label` from the column, keeping the
`COALESCE(..., run_id)` fallback for genuinely unlabelled runs.

**Done when:** both queries read `runs.label`; a labelled run shows its label in the
Rig run list and detail view.

**Status:** Done 2026-07-20 — both queries read `runs.label` with the
`COALESCE(..., run_id)` fallback retained, commit `c39bf7e`. Measured at the fix:
878 runs, 596 labelled, **0** with a label in `config_json` — so the old read
returned the fallback for every row, including the 596 properly named ones.
Batched with BL-004 per the sequencing table. The BL-007 t4 fork rider landed in
the same commit: a fork inherits its parent's label verbatim, guarded on both ways
`label` is not real (the COALESCE fallback, and the `label: ''` placeholder in
`handleForked`). Reviewed round 1 in `docs/reviews/bl-029-review.md`; merge gated
on the manual GUI pass (review finding 2). Backend real-vs-fallback distinction
deferred to BL-037 (review finding 5).
**F9 addendum:** the run detail header now shows the run_id when it differs from the
label, commit `5ad4bf2`. Making labels real had removed the operator's only view of
the run_id — the handle `mix aetheris inspect` / `fork` / `tree show` all take — so
restoring it is part of what BL-029 ships, not a separate fix (review finding 9).

---

### BL-035 — Extract `formatCost` / `formatTokens` to `src/lib/format.ts` (#TBD)
**Size:** XS · **Priority:** low

`rig/CLAUDE.md` ("React / Frontend patterns") sets the rule: these helpers are
duplicated in `TrajectoryView.tsx:54,60`, `UsageView.tsx:8,13`, and
`useRunDiff.ts:9`, "acceptable for three locations. Extract to `src/lib/format.ts`
if they spread to a fourth."

BL-004 added a third `formatTokens` copy in `RunList.tsx` (for the Cost cell's token
tooltip) — at the threshold, not past it, so extraction was deliberately *not* done
in that ticket: it would have touched three files outside the ticket's Touches list.
The next site tips it over.

Note the copies have **diverged in signature**: `TrajectoryView`/`RunList` take
`number | null` and return `'—'` for null; `UsageView` takes a bare `number`. The
extracted helper should be the nullable form, with `UsageView`'s call sites passing
non-null values unchanged.

**Done when:** one `src/lib/format.ts` exports both helpers; all four sites import
them; no local copies remain; `bunx tsc -b && bun run lint` green.

---

### BL-036 — drift_check: field-level checking for specs §4 command structs (#TBD)
**Size:** M · **Priority:** low

`check_tauri_commands` (`scripts/drift_check.py:194-238`) compares command **names**
only, three ways (`lib.rs` `generate_handler!` / `#[tauri::command]` fns / specs §4).
The *struct fields* documented under each command in §4 are entirely unguarded.

Found by: specs §4 documented `RunDetail` with an `events: Vec<EventRow>` field that
the real struct (`harness.rs`) has never had. Nothing caught it; it was noticed only
because BL-029 happened to edit that exact block. Corrected in the BL-029 + BL-004
commit. The same blind spot let `RunSummary.label`'s `// from config_json.label`
provenance comment stay wrong for as long as the bug itself lasted.

§6 payload fields already have a live-DB sampling checker (`check_payload_fields`) —
this is the §4 analogue. Likely approach: parse the ```rust fenced blocks in §4 for
`pub <field>: <type>` and compare against the corresponding struct in
`commands/*.rs`. The `?`-suffix optionality convention from §6 may be worth reusing.

**Done when:** a field present in a §4 struct block but absent from the Rust struct
(or vice versa) is reported; the checker is in the sprint's `--strict` run;
`tests/test_drift_check.py` covers both directions.

---

### BL-036 — DONE 2026-07-25

Landed as a **new check 9**, `command_fields` (`11675cc`), batched with BL-041(b) — both
are `drift_check` blind spots on one file surface. `check_tauri_commands` stays names-only
and three-way: the ratified shape was a separate check, not field logic folded into check 2.

**What it does.** Parses the ` ```rust ` fenced blocks under specs §4 for
`pub struct NAME { pub field: Type }` and compares against the same-named struct in
`rig/src-tauri/src/commands/*.rs`. The join key is the **struct name** — it appears verbatim
on both sides, and one fenced block may declare two structs (`TrajectoryEvent` +
`TrajectoryFile`). One shared field parser serves both sides (the doc blocks and the Rust
source are the same syntax); it drops `///` doc comments, trailing `// …` notes and `#[…]`
attributes, and is line-based rather than comma-split because a type may contain a comma
(`HashMap<String, String>`).

**Signals.** WARN on documented-but-absent (the phantom-field case this row was filed for),
struct-field-undocumented, type mismatch, and ghost struct. FAIL is reserved for the
structural "zero structs parsed from §4", matching every other check's shape. The §6
`?`-suffix optionality convention is reused: a documented `field?: T` is satisfied by
`Option<T>`, and `?` relaxes the **type**, not existence — a `field?` absent from the struct
still warns. §4 documents `Option<T>` directly today and uses no `?`; the convention is
forward-compatible and carries its own tests.

**Result at HEAD: clean** — 9 documented §4 structs, 52 fields, all matching
(`RunSummary`, `EventRow`, `RunDetail`, `HarnessStatus`, `TrajectoryEvent`, `TrajectoryFile`,
`PollResult`, `CapabilityMatrix`, `UsageStats`, against `commands/harness.rs`,
`trajectory.rs`, `orchestrate.rs`, `capability_matrix.rs`, `usage.rs`). The phantom
`RunDetail.events` was already corrected in the BL-029 commit, and nothing else had drifted,
so **no specs §4 edit was needed** — the row closes with nothing to reconcile rather than
with a silent fix. The green is mutation-checked, not asserted: neutering the absent-field
branch turns its tests red.

Sprint coverage is automatic — `sprint.sh`'s `drift_check` case invokes `--strict` with no
hardcoded check count, and the header/`Summary` lines were already computed from
`len(selected)`/`FINDINGS`.

`Source: 11675cc, 2026-07-25. Notes:
docs/rig/milestones/bl-041b-bl-036-drift-check-guards-implementation-notes.md.`

**r1 (review F1/F2/F3), `0d5127b`.** The closing PASS in check 8 is now gated on
structural failures too (see the BL-041 DONE section); `_field_types_match` carries a
docstring line naming its textual-matching limitation (F2 — no row, conditional on §4 first
documenting a qualified or aliased type); the ghost-struct scope became **BL-052** (F3).
Check 9's result at HEAD is unchanged: 9 structs, 52 fields.
Review: `docs/reviews/bl-041b-bl-036-review.md`.

---

### BL-053 — DONE 2026-07-25 — verify makes no filesystem-hash claim (#TBD)
**Size:** S · **Section:** Harness (aetheris/) · Closes the **fs_hash strand of BL-048**

Landed at harness `915d582`, with the §3 contract edit ratified at `b4857eb` (r1). Diagnosis:
`docs/reviews/bl-048-fs-hash-diagnosis.md` (harness, committed in the same change). Contract
edit: `docs/reviews/bl-053-contract-draft.md` — **RATIFIED, option B** (§8, human, 2026-07-25).

**§3 changed in both cells, not one.** r0 struck "— and recorded vs. actual filesystem `fs_hash`"
from the `verify` row's Guarantees cell; review chose **option B** over a bare strike, so r1 added
an explicit non-guarantee to the same row's Does-NOT cell: *"any filesystem-state claim — the
comparison ranges over tool output only, so an unrelated file changing between record and verify
is not detected."* The reasoning: the row previously *told* operators verify compared filesystem
state, so a pure strike would make that change invisible to anyone who trusted the old claim, and
the loss below is exactly a non-guarantee worth stating where operators read guarantees. §5 is
untouched in both rounds.

**What was wrong.** `verify`'s comparison had a second arm —
`recorded_fs_hash != actual_fs_hash -> :hash_mismatch` — that could not fire for any tool.
`read_file`/`list_dir` stopped hashing at **`d4728af`** (2026-06-06), which removed a recursive
whole-sandbox-tree SHA-256 that reliably blew the 30 s GenServer timeout on a 31 GB / 52k-file
sandbox, and deleted `fs_hash.rs`. The exec-server family records and re-executes `nil`. Served
steps never reach a comparison. `write_file`'s hash is a digest of the *recorded input content*,
which re-execution reproduces by construction. So the arm compared `nil` to `nil`, fell through
to `:verified` — while §3's mode table told operators a filesystem hash had been compared. Two
Elixir tests still asserted the pre-`d4728af` `"sha256:"` shape and were three of BL-048's 15
failures.

**Ratified direction: delete and correct, do not restore.** `d4728af` is a correct fix for a real
defect and is not reverted. Verify's comparison is output value-equality over the deterministic
portion, full stop.

**What landed.** Verify-side deletes: the `:hash_mismatch` arm, `compare_status/4` → `/2`, the
`recorded_fs_hash`/`actual_fs_hash` extraction and step-map fields, the hardcoded exec-server
`fs_hash: nil`, `:hash_mismatch` from the `verify_report.ex` status union, and the per-step
rendering of both hashes. §3's clause struck; five mirrors corrected (`runbook.md`, `specs.md`
×2, `architecture.md` ×2). **Record side untouched** — the trajectory `fs_hash` payload field
stays (`null` for read tools, real for `write_file`); removing it is a schema migration touching
fork and the `payload_fields` drift check.

**Tests made honest, and one made non-vacuous.** `client_test.exs` now asserts
`Map.fetch!(result, :fs_hash) == nil` — `fetch!`, so the key must be *present and null* rather
than absent. `fs_hash_stability_test.exs` is **re-pointed at `write_file`**: it asserted
`hash1 == hash2` over two nils, so the stability property it existed to guard had not been
exercised since `d4728af` — the failing `"sha256:"` line was the only thing keeping it honest.
It now writes identical content twice, asserts a 64-char hex digest *before* comparing, and adds
a sensitivity case (different content → different hash) so the guarantee cannot be met by a
constant. Two verify tests asserting `Map.get(step, :actual_fs_hash) == nil` were changed to
`refute Map.has_key?` — `Map.get` on a deleted key also returns `nil`, so they would have kept
passing while asserting nothing.

**The real loss, stated plainly.** Whole-sandbox drift detection — an unrelated file changing
between record and verify — was removed at `d4728af` and is **not** restored here. Nothing
detects it today. If it is ever wanted it is a new, performance-aware feature (bounded to the
files a step touched, not the whole tree), not a revert.

**Evidence:** `requires_worker` 15 → 12 failures, the three fs_hash failures green and
non-vacuous; default `mix test` 934/0; `grep` confirms no remaining `:hash_mismatch` producer or
consumer outside explanatory comments; mutation-checked — reintroducing the arm turns the new
output-only verify test red (`verified: 0`, expected 1).

`Source: BL-048 fs_hash strand; diagnosis 2026-07-25. Review:
docs/reviews/bl-053-review.md (pending).`

---

### BL-054 — The twelfth `requires_worker` failure is a load-sensitive flake with no stable identity (#TBD)
**Size:** XS–S · **Priority:** low · **Section:** Harness (aetheris/)

Filed 2026-07-25 during BL-053's done-check, per the standing rule that a red gate gets a tracked
ticket the day it is found — and per **BL-051**, whose whole lesson is that a flake without a name
is met as a first sighting every time.

After BL-053 closed the fs_hash strand, `mix test --include requires_worker` reports 12 failures:
pwd ×3 (BL-048), SIGSYS ×8 (BL-043) — and **one slot that changes identity between runs**:

| Run | pwd | SIGSYS | Twelfth failure |
|---|---|---|---|
| diagnosis, 2026-07-25 (`af56a57`) | 3 | 8 | `RunOverlayTest` "overlay dirs are created and upper is empty…" — **BL-050**'s handshake race |
| BL-053 done-check, run 1 | 3 | 8 | `RunHelpersTimeoutTest` "a status change alone counts as activity, with no events at all" (`run_helpers_timeout_test.exs:84`) |
| BL-053 done-check, run 2 | 3 | 8 | `RunOverlayTest` again — `RunHelpersTimeoutTest` green |

Three consecutive runs, same arithmetic (3 + 8 + 1 = 12), **two different occupants** of the
twelfth slot and each green in the run where the other failed. That is the evidence the slot is a
race rather than a defect: the two stable strands never move, and the twelfth never sits still.

The `RunHelpersTimeoutTest` case asserts `await_bounded(run_id, await_inactivity_timeout_ms: 300)`
reaches `:done`; under the full suite's load it instead returns
`stalled: no status or event activity for 300ms (last status: running, last event seq: -1)`.
**10/10 green in isolation** (five isolated runs × two tests). BL-053's diff touches only
`verifier.ex`, `verify_report.ex` and verify/worker tests — nothing in the `await_bounded` path —
so it is not attributable to that change. Both candidates are timing races whose window is a
few hundred ms; the full suite is where the load exists to lose them.

Not merged into BL-050: that row is one specific race with a mechanism, while this is the
*pattern* — a fixed-ms inactivity window asserted inside a suite whose scheduling is not bounded.
The candidates share the shape, not the site.

**Done when:** the fixed-ms windows in `run_helpers_timeout_test.exs` are made load-insensitive
(poll for the state transition rather than assert against a wall-clock budget — the pattern the
harness `CLAUDE.md` already promotes, *"poll for trajectory events, not time"*), or the tests are
tagged so a loaded full-suite run cannot flake them; and BL-050's race is settled. Until then the
twelfth slot is **named here** rather than re-triaged each run.

`Source: BL-053 done-check, 2026-07-25. Captures: full_requires_worker.txt (both runs),
rht_1..5.txt (isolation).`

---

### BL-052 — drift_check check 9: ghost-struct arm is scoped to `commands/*.rs` (#TBD)
**Size:** XS · **Priority:** low · **Trigger-fired**

`check_command_fields` (check 9, BL-036, `11675cc`) resolves each §4-documented struct against
`_parse_command_structs_from_source(COMMANDS_DIR)`, which globs
`rig/src-tauri/src/commands/*.rs` only. A documented struct that the checker cannot find there
draws a **ghost** WARN:

```
struct 'X' documented in specs.md §4 but not found in commands/*.rs (ghost)
```

All nine structs documented in §4 live in `commands/` today, so the arm is accurate at HEAD and
the scope matches BL-036's ticket text. It is the arm most likely to produce the checker's first
**false positive**: a §4 block documenting a struct defined elsewhere under `src-tauri/src`, or
re-exported into `commands/` from another module, would be reported as a ghost that isn't one.
A false WARN in a `--strict` sprint is a red gate, and a red gate that is wrong is what trains
the "the check is probably stale" reflex the standing gates rule exists to prevent.

**Fix (trivial):** widen the source scan to `rig/src-tauri/src/**/*.rs` (`rglob`), keeping the
join on struct name. Nothing else changes — `_parse_structs_from_rust_text` is already
file-agnostic. Adjust the ghost message to name the widened scope, and add a test that a struct
defined outside `commands/` is found rather than ghosted.

**Deliberately deferred, not overlooked.** Widening now would broaden the surface with no live
case and no test that could distinguish the two behaviours at HEAD. This row makes the
recurrence countable if it lands.

**Done when:** the source scan covers `src-tauri/src/**/*.rs`, or the row is closed with a
recorded reason for keeping the narrow scope; `tests/test_drift_check.py` covers a
non-`commands/` struct either way.

`Source: BL-041(b)+BL-036 review F3 (claude-ui, 2026-07-25), raised as the packet's §8 flagged
observation and promoted from prose to a row. Review: docs/reviews/bl-041b-bl-036-review.md.`

---

### BL-037 — Nullable `label` in RunSummary/RunDetail: backend distinguishes real from fallback (#TBD)
**Size:** XS–S · **Priority:** low

BL-029 made both harness queries return `COALESCE(runs.label, run_id)`, so the wire
type cannot express "this run has no label" — the fallback is indistinguishable from
a run genuinely labelled with its own id.

Every consumer that needs the distinction must re-derive it by string comparison. The
fork rider already does:

```ts
// TrajectoryView.tsx
run && run.label && run.label !== run.run_id ? run.label : undefined
```

That is the frontend reconstructing a fact the backend erased, and it will be wanted
again — **BL-024's lineage view** needs real-vs-fallback to render sensibly, and any
further consumer either repeats this guard or gets it wrong silently (the failure
mode is a run_id displayed as if it were a chosen name, which is precisely the BL-029
symptom returning by a different route).

Shape: `label: Option<String>` / `string | null` on the wire; the `COALESCE` comes out
of both queries; the run_id fallback moves to the display layer where it belongs; the
`TrajectoryView` guard simplifies to a null check. Note this also removes the
`label: ''` placeholder hazard in `RunList.tsx` `handleForked` (BL-029 review
finding 6) — `null` is expressible where `''` was a stand-in.

Sequence **with or before BL-024** so the lineage view is built against the corrected
contract rather than inheriting the string-comparison guard.

**Done when:** `label` is nullable end-to-end; no consumer compares `label` to
`run_id`; the run_id fallback is applied once, at display; `cargo test` + `tsc -b` +
`bun run lint` green.

---

### BL-038 — Run list: search/filter, and the LIMIT window hides old runs (#TBD)
**Size:** S · **Priority:** medium

Two faces of one gap, surfaced together during BL-029's merge-gate check (2026-07-20).

**No search.** At 250+ visible runs (878+ in store), locating a run by id or label
means scrolling. A text filter over label + run_id on the loaded rows is the minimum;
it makes labels (real as of BL-029) actually navigational.

**The window is silent.** `harness_list_runs` is `ORDER BY started_at DESC LIMIT ?`
(`rig/src-tauri/src/commands/harness.rs`), so runs older than the window are
unreachable from the UI with no indication they exist — an operator concludes "not
there" for a row that is. Concrete instance: `demo-01` (verified present, unlabelled,
forkable — 53 events, steps 0–9) invisible at the default limit. A client-side filter
alone does **not** fix this face: it filters the window, not the store. Minimum honest
fix is to show "N of M runs" so the cutoff is visible; the full fix is server-side
search (`WHERE label LIKE ? OR run_id LIKE ?`) or pagination.

The two faces share a failure shape with BL-029 itself: the UI stated something false
without appearing to state anything at all. There, every run's label silently read as
its run_id; here, the store silently reads as 250 runs deep. Both degrade to a
confident wrong answer rather than a visible gap, which is why both survived — an
operator has no prompt to doubt what they see.

**Relation:** BL-024's lineage view will need find-run-by-id anyway; whichever lands
first should carry the shared piece.

**Does not block BL-029.** An earlier draft of this row claimed it did, via the
`demo-01` / `run_zS6XSQ` candidates being windowed out. That claim was stale when
written and is struck: both candidates were deliberately retired, and the gate's
closure path moved to a stub fixture agent. The real obstacle to fork-based checks is
**BL-039** — real-provider fork continuation fails at the first LLM call — which no
amount of window-raising fixes, since a real-provider fork of any run fails
identically. Search/window and fork continuation are independent gaps.

**Done when:** an operator can locate any run in the store by id or label from the UI,
or the UI states plainly that it is showing a truncated window.

**Decided scope (2026-07-25, ahead of implementation): server-side, one filtering
path.** The row above offers "a text filter over label + run_id on the loaded rows"
as the minimum and server-side search *or* pagination as the full fix. Adjudicated:
**server-side search, no client-side filter layer, no pagination UI.** Two filtering
paths — client over the window, server over the store — can disagree, which is the
same silent-wrong-answer class the ticket exists to kill; a second path is a second
thing that can lie. The round-trip against local SQLite is sub-millisecond, so a
debounce is sufficient and the instant-filter layer buys nothing. Pagination is
dropped rather than built alongside search: search subsumes the navigational need and
building both is gold-plating an S.

Wire shape: `harness_list_runs` returns `RunListResult { runs, total_count }` rather
than `Vec<RunSummary>`; `total_count` is `COUNT(*)` under the same `WHERE` from the
same call. A separate `harness_runs_count` command was rejected — two calls can
straddle a concurrent write and desync the badge from the list.

**Status:** Done 2026-07-25 — `c0977c2` (agents). Both faces closed. Search filters
`WHERE runs.label LIKE ?term OR runs.run_id LIKE ?term` (`%term%`, metacharacters
escaped) on the **raw** columns, so an unlabelled run is reachable by run_id — `LIKE`
never matches the NULL label, and `demo-01` (NULL label, 879th of 896 by `started_at
DESC`) is the verified instance: absent from the unsearched 250-run window, returned
by search, proven against the real store by an opt-in live test arm. Window
disclosure renders "Showing N of M runs", with a second form while the client-side
*status* filter is active so the badge cannot misdescribe the rows on screen. Both
reads run inside one deferred read transaction — one command is not sufficient for
the stated invariant on its own, since two statements can still straddle a harness
insert. Notes: `docs/rig/milestones/bl-038-run-list-search-implementation-notes.md`.
**Merge gate closed** — manual GUI pass executed 2026-07-25 against the real 896-run
store: A/B/C/rider green, `Showing 500 of 896 runs` confirmed (BL-029 precedent; Rig
has no frontend test runner, BL-017). The expected badge is the **default** 500 window,
not the 250 the live test first used (review F1, fixed in `e4baddf`; arms and numbers
in the implementation notes). Review: `docs/reviews/bl-038-review.md` — no blocking
code findings; both in-cycle additions (LIKE-metacharacter escaping, single read
transaction) endorsed. Spawned **BL-058** (specs §5 TypeScript interfaces are
unchecked and already stale). Nothing pulled in from BL-037, BL-035, or BL-024.

---

### BL-058 — specs §5 (TypeScript Interfaces) is unchecked, and already stale (#TBD)
**Size:** S · **Priority:** low-medium · **Section:** Rig (`aetheris-agents/rig/` + `scripts/drift_check.py`)

Found during BL-038 while adding `RunListResult` to both halves of the doc contract.

`drift_check` check 9 (`command_fields`, BL-036) compares specs §4's ` ```rust ` structs
against `rig/src-tauri/src/commands/*.rs`. **Nothing checks §5**, the TypeScript half of
the same contract, against `rig/src/hooks/types.ts` — so the frontend-facing types drift
silently while the Rust-facing ones are guarded.

It has already drifted. §5's `interface RunSummary` carries nine fields; `types.ts` has
thirteen — `last_event_at`, `total_cost_usd`, `total_input_tokens`, `total_output_tokens`
are all absent from §5, the last three since BL-004 (2026-07-20). §5 also narrows
`status` to a five-member union where `types.ts` widens it with `| string`. A reader
trusting §5 gets a well-formed, confidently wrong picture of the type — the same shape
BL-036 closed one section up.

**Not** a §4-style port: the two sections describe different surfaces (§4 is the Rust
wire shape, §5 is what the hooks hand components), so the fix is a check keyed on the
interfaces §5 actually declares, plus the one-time correction of `RunSummary`. Decide
whether §5 is authoritative for *all* of `types.ts` or only the harness block before
writing the check — the section is currently a partial mirror, and a check that demands
totality would fail on types nobody intended to document there.

`RunListResult` was added to §5 by BL-038, so that ticket contributed no new drift.

**Done when:** a `drift_check` check compares specs §5 interfaces against
`src/hooks/types.ts` with a documented scope rule, §5's `RunSummary` matches source, and
`--strict` is green.

---

### BL-039 — Fork continuation fails against real providers: reconstructed transcript carries a `"tool"` role (#TBD)
**Size:** M (docs-first — the fix is a design choice with contract implications)
· **Priority:** medium-high

Forking a run and continuing it against a real provider fails at the **first LLM
call**. Two layers, and the second is why this is M rather than a one-line fix.

**Layer 1 — the immediate rejector.** `../aetheris/lib/aetheris/execution/fork.ex:104`
emits a message with `"role" => "tool"`:

```elixir
defp event_to_messages(%{type: :tool_result, payload: payload}) do
  tool_name = Map.get(payload, "tool_name", "")
  output = Map.get(payload, "output", "")
  [%{"role" => "tool", "tool_name" => tool_name, "content" => output}]
end
```

Anthropic accepts `user` and `assistant` only → HTTP 400 on the first call. This is
the only `"role" => "tool"` site in the tree.

**Layer 2 — why relabeling is insufficient.** Rewriting that message to the API's real
shape (a `user`-role turn carrying a `tool_result` block) would *still* be rejected: a
`tool_result` must pair with a preceding assistant `tool_use` block, and those are
never reconstructed. `event_to_messages(:llm_responded)` spans `fork.ex:87-98` and
drops every non-text response at `:95-96`:

```elixir
      _ ->
        []
```

So the contract's §4 known limitation — assistant tool-call turns are not
reconstructed — is not cosmetic. It is operationally fatal against any validating
provider.

**Minimal reproducer:** fork from any step whose `llm_responded` was a tool call. Step
0 of any tool-using agent hits it.

**Evidence.** `fork-aa6a6a65804f6645` — **human-executed via the Rig UI**, `fork_step:
0`, parent `payslip-orch-a7Vi3A`, `provider: anthropic`, 2026-07-20. `message_count: 2`
at seq 0 (user_prompt + the tool-role message; the parent's step 0 was a `run_command`
with no text response, so `event_to_messages(:llm_responded)` contributed nothing),
HTTP 400 at seq 2. This was the **first real-provider fork continuation ever
attempted**; all fourteen prior `fork-*` rows were stub-provider, and the stub
validates nothing. Full trail in `docs/reviews/bl-029-review.md`.

**Reproduced — three attempts, two distinct parents, all identical.** All human-executed
via the Rig UI, all `fork_step: 0`, `provider: anthropic`, `message_count: 2` at seq 0,
`HTTP 400: Unexpected role "tool"` at seq 2:

| fork run | parent | date |
|---|---|---|
| `fork-aa6a6a65804f6645` | `payslip-orch-a7Vi3A` | 2026-07-20 |
| `fork-333da479c4902361` | `payslip-orch-a7Vi3A` | 2026-07-20 |
| `fork-955dd155d2a8d4c4` | `payslip-orch-TVgr-Q` | 2026-07-21 |

100% failure rate on real-provider fork continuation; zero successes ever recorded. The
minimal reproducer is demonstrated, not inferred.

**And the stub "successes" are vacuous — the failure is universal, not real-provider-
only.** `encode_config` strips `stub_responses` (`../aetheris/lib/aetheris.ex:372`), so
a stub fork begins with an **empty queue**, receives `[stub exhausted]` on its first
call, and terminates at step 0. Confirmed on `fork-94c31612127f2009`: `llm_called`
(`stub-model`) → `llm_responded` (`[stub exhausted]`) → `run_complete`
(`agent_finished`). The fourteen green `fork-*` rows from 2026-07-19 are green for this
reason. **No fork on any provider has ever had a meaningful continuation** — real ones
are rejected at the first call, stub ones exhaust at it. Any future fix must be
verified against a fork that actually continues, since a `done` stub fork proves
nothing.

**Operator-facing symptom (noted, not separately filed):** the Rig UI surfaces this as
`Fork failed: [sandbox] entered user+mount namespaces … Error: run <id> failed` — the
sandbox preamble is carried into the error string and the actual cause (the HTTP 400)
does not appear at all. An operator cannot diagnose from the UI message; the reason is
only reachable by querying the events table. Whoever takes BL-039 or BL-030 should
decide which owns surfacing the underlying error.

**Fix space — sketched, not decided.** Either reconstruct assistant `tool_use` blocks
from recorded `llm_responded` payloads (if the payload retains enough to rebuild the
block), or fold tool results into user-role text and abandon structured tool
continuation. The choice changes what a fork *is* — whether it resumes a tool
conversation or replays a flattened one — so it is a contract decision, docs-first.

**Third consideration: the stub queue is stripped on fork** (`aetheris.ex:372`), which
is why no stub fork can exercise a continuation. Whatever the fix, it needs a test path
where a fork *actually continues* — either by carrying `stub_responses` across the fork
(cheap, test-only) or by an integration test against a recorded real transcript.
Without that, the fix's own verification would be as vacuous as the fourteen green rows
this row documents.

**Sequencing.** Ahead of BL-030: an early-return fork UX matters little while real
forks cannot run at all. **Builds atop BL-028's landed state** — BL-028's
`"output"`/`"result"` key fix is in this exact clause (`fork.ex:101-105`,
`Map.get(payload, "output", "")` at `:103`). Land BL-028 (b2) first; BL-039 must not
race it.

**§4 wording ratified 2026-07-26** — `../aetheris/docs/reviews/bl-039-contract-draft.md`,
with three edits (positional pairing named as an adapter dependency rather than a world
property; the id claim scoped to the harness; cross-provider fork carrying its
reachability caveat). Implementation is unblocked. The adjudication spawned **BL-059** —
the adapter silently discards parallel `tool_use` blocks, which is the *only* reason
one-call-per-step holds; BL-039 must not fix it, and its §4 clause records the coupling.
This row's own citations were corrected at HEAD by the scout memo
(`../aetheris/docs/reviews/bl-039-fork-continuation-scout.md`) — line numbers moved
post-BL-028, the "only `role => tool` site" claim is false, and the `aetheris.ex:372`
stub-strip attribution is wrong (the fork path never *sets* `stub_responses`; the cited
function is the scheduled-run template encoder). Conclusions unaffected.

**Done when:** a fork of a tool-using run continues successfully against a real
provider, or the contract states plainly that fork continuation is stub-only and the
UI refuses real-provider forks rather than failing at the first call.

**Status:** Done 2026-07-26 — harness `ebc3878` (docs-first §4 + §2 and runbook echo
sweep), `e44d35c` (implementation), `3f561d9` (notes); agents `7d6013a` (rig runbook +
fork fixture mirrors). Design A as ratified. A recorded tool step rebuilds as the
canonical pair — an assistant `tool_use` block and a `user` `tool_result` block sharing
a step-derived synthetic id — built through
`Aetheris.Execution.CanonicalMessage`, extracted from `loop.ex` so the live loop and
fork reconstruction have one definition. The record path is untouched: no `tool_use_id`
is added to any event. Part C ships in the same change —
`RunHelpers.terminal_error_reason/1` puts the fork's terminal `error` reason into the
CLI message, which previously read only "run \<id\> failed". No provider/model fork
overrides were built (BL-030).

**Done-when is met, demonstrated not asserted.** The `:requires_real_provider` arm was
run manually against Anthropic: **PASS**, and mutated back to the pre-fix shape the same
arm returns `HTTP 400: messages: Unexpected role "tool"…` — byte-identical to the reason
recorded in `fork-aa6a6a65804f6645`. That retires the hedge the §4 wording deliberately
carried (`bl-039-contract-draft.md` obligation 2). All three done-check arms are
mutation-checked; the stub-continuation arm asserts the reconstructed context as well as
the continuation, because the stub validates nothing and continuation alone would be a
fifteenth vacuous green. Notes:
`../aetheris/docs/aetheris/milestones/bl-039-implementation-notes.md`.

**Two corrections to the scout memo, recorded because they outlive this ticket.** The
memo's §4 "one constraint the design must respect" attributes key-dropping to
`Agent.Server.normalize_context_entry/1` and quotes both clauses fetching `"content"`;
at HEAD the atom-key clause fetches `:content`, and the function is **not on the wire
path** — it feeds `Agent.Server`'s `context:` state, while the adapter's messages come
from `Loop.run/5`, which uses `config.fork_context` unnormalized. The design instruction
(everything inside `content`) is unaffected; its stated reason was wrong. Also: the memo
is at `docs/reviews/bl-039-fork-continuation-scout.md` in **this** repo, not
`../aetheris/` as this row and the ticket text both say.

**Spawned BL-060** (`mix hex.audit` red on an upstream `bandit` advisory), found by an
off-territory gate run, and **BL-061** (review F1 — Gemini thought signatures are not
recorded, so a forked Gemini run does not round-trip them).

**Review:** `docs/reviews/bl-039-review.md` — approved, no blocking findings; two
non-blocking items dispositioned in r1 (`ebc3878`..`0e14500` plus the r1 commit).

---

### BL-062 — Fork provider/model overrides (#TBD)
**Size:** S–M · **Priority:** medium · **Section:** harness CLI + Rig fork dialog · **§8 edit required**

Split out of BL-030 during its scoping so that ticket stayed §8-free (adjudicated
2026-07-26). `Aetheris.fork_run/3` already accepts arbitrary `RunConfig` overrides
and the harness threads them into the fork's config; cross-provider forking works
by design (determinism contract §4, ratified at BL-039). The CLI and Rig simply
never expose it — `fork_overrides/1` (`../aetheris/lib/aetheris/cli/commands/fork.ex`)
maps `--name` to `label` and nothing else.

**Wanted.** CLI: widen `fork_overrides/1` and the fork `@switches` to accept
`--provider` / `--model` into the overrides map. Rig: a provider/model picker in
the fork dialog so the flag is operator-reachable rather than wired to nothing —
or an explicit record of "CLI-only for now" with the picker deferred to its own
row.

**§8.** Determinism contract §4 currently says *"Selecting a different provider is
a capability of `Aetheris.fork_run/3`'s `overrides`; the CLI and Rig entry points
pass a label only (BL-030)."* That sentence stays **true** until this lands, but
its `(BL-030)` ref already points at a closed ticket that never carried the
overrides — this row's §8 edit corrects the sentence *and* repoints the ref. §4
has form for decayed parentheticals (D2's `cli/commands/fork.ex:47-55`), so do not
leave it.

**Done when:** the CLI accepts the flags and they reach the fork run; the §4
sentence is corrected and its ref repointed under §8 ratification; operator access
(picker vs CLI-only) is decided and recorded.

---

### BL-064 — Fork with additional instructions (#TBD)
**Size:** TBD · **Priority:** TBD · **Section:** TBD

Parked at BL-030 closure, 2026-07-26. **Scope not yet written** — this row exists
so the idea has an owner and a number rather than living in a review thread, per
the deferred-finding rule. It is a stub, not a spec.

**What is known:** the intent is to fork a run *and* supply new or amended
instructions at the fork point, rather than replaying the recorded prefix and
continuing unchanged. Nothing beyond that has been adjudicated here — not the
surface (CLI flag, Rig dialog, or both), not where the instruction lands (appended
user turn, `system_prompt` override, something else), and not what it means for
the determinism contract's fork guarantee, which today describes a fork as the
recorded prefix continued live.

**Adjacent:** BL-062 is the same seam (fork-time overrides reaching CLI and Rig)
and would likely share its plumbing; a `system_prompt` override is already an
`overrides` key, so part of this may be reachable the same way.

**Do not start from this row.** Get the scope from whoever parked it, write it
here, then implement. Anyone who fills this in should treat the paragraph above as
leads, not facts.

---

### BL-065 — A failed trajectory write still reports the run as `done` (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/lib/aetheris/agent/server.ex`)

Raised by BL-030 r1 and carried through r2. Not introduced there — latent since
the write was added.

**The defect.** `execute_run/…` calls the trajectory write and then branches on a
*different* value (`server.ex:680-684`):

```elixir
    Aetheris.Trajectory.File.write(config.run_id, events, meta)

    case result do
      :ok -> GenServer.cast(server_pid, {:run_complete, :done})
      {:error, reason} -> GenServer.cast(server_pid, {:run_failed, reason})
    end
```

`result` is the **loop's** result. `File.write/3`'s `{:ok, path} | {:error, …}` is
never examined, so a disk-full, permission or rename failure produces a run whose
status reads `done`, with no trajectory file and no error recorded anywhere. The
same pattern is at the resume path (`server.ex:952`).

**Class:** Silent-wrong-answer (harness `CLAUDE.md`) — the failure renders as a
normal completion, which is exactly what lets it survive. Ask what a broken write
looks like from outside: identical to a successful one.

**Consequence already relied upon.** BL-030 r1's completion transition treats
terminal status as "the harness has finished writing", *not* "the file exists",
and its reload is best-effort for this reason — on this path Rig stays in the
reconstructed view with its terminal banner. That degradation is correct and
should stay correct after this is fixed; fixing it here means the operator also
learns the write failed.

**Done when:** a failed trajectory write is surfaced — the run does not report
`done` on a write failure, or the failure is recorded as an event/log with the
reason — and both call sites (`:680`, `:952`) are covered. Exercise the gap
explicitly (a write forced to fail must not produce a `done` run), not just the
happy path.

---

### BL-067 — `capability_matrix_assemble.exs` computes its whole derived block in the LLM, so the Summary counts, the unique-tools line and the Overlap Report are unverified every regen (#TBD)
**Size:** S · **Priority:** next · **Section:** aetheris-agents (`agents/capability_matrix_assemble.exs`)

Steps 2 and 3 of the assembler's prompt ask the model to *detect overlaps*, *count agents and
scripts per section*, and *list all unique tools* — three computations over content it has just
read, handed to an LLM. **Everything the assembler derives rather than pastes is in scope
here**; the counts are only the loudest instance.

**The counts.** Two consecutive runs at m1-cloudcost t5, same restored section files, both
wrong and wrong differently:

```
run cap-matrix-assemble-QWY6QQ : docbuilder 27 · Total 27 / 70
run cap-matrix-assemble-9bx1Pw : docbuilder 25 · Total 27 / 68
actual (counted from the emitted table rows) : docbuilder 24 · Total 26 / 67
```

**The unique-tools line** (t5 review, finding 2 — the same defect one line lower). It is
LLM-derived too, and it silently changed across this regen:

```
eeb37a1 : run_command, write_blackboard, send_message, read_blackboard, wait_for_event,
          spawn_agent, wait_for_all, read_file,            MCP servers (corpus_search, lattice)
6abc3e8 : run_command, read_file, write_file, spawn_agent, wait_for_all, write_blackboard,
          send_message, read_blackboard, wait_for_event,   MCP servers (corpus_search, lattice)
```

`write_file` appeared. It was not new — `context_builder.exs` has carried
`read_file, write_file, run_command` since m3, and that row is *in the same document*
(`docs/capability-matrix.md:164`). So the line was **wrong at `eeb37a1` and is right now by
luck, not by mechanism** — which is the proof that it is non-deterministic rather than
authoritative. A derived line that silently heals trains the same "probably fine" reflex as one
that silently rots. The **Overlap Report** (Step 2) is derived by the same means and has never
been checked at all; its agent-name column also churned this regen.

This is a direct violation of the repo's core principle (`CLAUDE.md` → "Scripts do; agents
decide… Never ask the LLM to construct file content or compute values programmatically"), and
it is a **Silent-wrong-answer**: every one of these outputs is well-formed and plausible inside
a generated artifact nobody recounts.

Not fixed at t5: the fix needs a deterministic generator, which means giving the assembler
`run_command` + a script, beyond that ticket's scope. t5 hand-corrected the three Summary
numbers to the verified values and said so in its packet; the tools line and overlap block were
left as the regen produced them.

**Fix:** `scripts/assemble_matrix.py` does the **whole assemble** — reads `docs/.sections/*.md`
in an explicit `SECTIONS` order, concatenates them verbatim, computes the entire derived block
(Summary table, unique-tools line, Overlap Report) from the sections' own table rows, and writes
`docs/capability-matrix.md`. `agents/capability_matrix_assemble.exs` is retired; sprint.sh's
`capability_matrix` case calls the script where it called the agent.

> Widened from "the generator emits the derived block to a file, the assembler pastes it
> verbatim" (this row's original Fix) because that leaves an LLM transcribing a counted block —
> the same fallible actor the fix exists to remove, and the m2a blob round-trip says it will
> improvise. Concatenation is not a task worth an LLM either.

**Done when:** the Summary counts, the unique-tools line and the Overlap Report are all
script-produced with no LLM in the assemble step; a regen is byte-stable for unchanged sections;
and a test **per derived value** asserts claimed == counted against the emitted tables (per-section
and total agent/script counts, claimed tools == union of the tool cells, claimed tool-set and
script-name overlaps == recomputed overlaps).

**Status:** Done 2026-07-30 — `scripts/assemble_matrix.py` + `tests/test_assemble_matrix.py`
(24 tests, each derived-value check mutation-verified), `agents/capability_matrix_assemble.exs`
deleted, `aetheris/scripts/sprint.sh` `capability_matrix` case calls the script. Commits
`de685fe` (agents) + `27bcd94` (harness). The regen corrected three Overlap Report defects the LLM had left standing (the
5-tool group listed 4 of 7 agents, the `write_blackboard, send_message, run_command` group was
missing entirely, and `docbuilder_orchestrator` was absent from the `run_command` group) — none
of which had ever been checked. Notes: `docs/milestones/bl-067-implementation-notes.md`.

> The matrix committed with this ticket was assembled over sections **restored from
> `HEAD:docs/capability-matrix.md`**, because a full section-agent regen still destroys curated
> prose (BL-068). That restore is a stopgap ritual; BL-068 retires it.

---

### BL-068 — A full capability-matrix regen destroys hand-curated section content, because `docs/.sections/` is gitignored (#TBD)
**Size:** S · **Priority:** next · **Section:** aetheris-agents (`agents/capability_matrix_{uc}.exs`, `docs/.sections/`)

The section files are the only home for the matrix's curated prose, and they are gitignored.
Re-running all eight section agents therefore rewrites every section — reordering rows,
rewording purposes, and dropping the hand-added m3/m5/m6 provenance annotations in the
docbuilder Scripts table. m1-cloudcost t5 measured it: a 121-line diff for a one-section
addition, against 1–6 line diffs for the three prior matrix commits, i.e. previous sessions had
been regenerating only the changed section. That practice is correct, undocumented, and
unenforced — the artifact's durability rests on each session remembering it.

The current workaround is a manual ritual: reconstruct the sections from
`HEAD:docs/capability-matrix.md`, then re-run the assembler alone. BL-067 used it (its packet
says so), and it is the reason a full sprint regen is discarded rather than committed.

**Related:** `agents/capability_matrix_eduloka.exs` exists but is wired into neither sprint.sh's
`capability_matrix` case nor `SECTIONS` in `scripts/assemble_matrix.py`, and there is no
`docs/.sections/eduloka.md`; eduloka has never appeared in the matrix. Decide whether it joins
the matrix or the agent is deleted — either way it stops being an unwired ninth file.

**Fix direction:** give the curation a home the section agents cannot clobber — a committed
overrides file (`docs/capability-matrix-overrides.md` or JSON, keyed by use case + script name)
that `assemble_matrix.py` merges over the generated purpose cells, or a preserve step that
re-applies curated cells after a regen. The overrides route is preferred: it is deterministic,
diffable, and the assembler is already the single place every section passes through.

Raised at m1-cloudcost t5 (implementation notes, "`docs/.sections/` is gitignored, so a full
regen is destructive"); filed as a row at BL-067 per *a deferred finding gets a backlog row in
the same round it's deferred* — t5 left it as prose, which files nothing.

**Done when:** a full eight-agent regen preserves curated purpose text (or the curation lives
somewhere a regen cannot reach), so the restore-from-HEAD ritual is no longer needed; the
runbook's "Full regen loses curation" limitation is removed rather than documented; and the
eduloka question is resolved either way.

**Status:** Done 2026-07-30 — commits `e60bcfd` (agents) + `fd9ac48` (harness). `docs/capability-matrix-overrides.json` is the
durable home: committed, keyed by use case → `agents`/`scripts` → row key → field, merged by
`scripts/assemble_matrix.py` **before** anything is counted, so claimed == counted still holds
and an overridden Tools cell flows into the unique-tools line and the overlap tables like any
other. Seeded with the twelve known-fragile cells (eleven docbuilder m3/m4/m5/m6/rig-p9 purpose
annotations + provenance `search_agent.exs`'s prose Tools cell — the BL-067 §1e leak).

*Demonstrated, not asserted:* a full nine-agent regen ran and the section agents reworded **all
twelve** curated cells (every milestone marker gone), yet the emitted matrix is byte-identical to
`HEAD` in each of them — the overrides were load-bearing on every one, and the matrix committed
here is the regen's own output, with no restore-from-HEAD anywhere. An override matching no row
**fails the run** (exit 1), so a renamed script can no longer drop its curation quietly. The
runbook's "Full regen loses curation" limitation is deleted and replaced by a **Curated cells**
section.

**Eduloka: wired, not deleted** — `eduloka/` has a real surface (`eduloka_orchestrator.exs` +
14 scripts), so it joined `SECTIONS`, sprint.sh and the matrix (`eduloka 1 / 14`; totals 26/67 →
27/81). Wiring it exposed why it had never appeared: `max_steps: 15` against ~18 needed tool
calls, so its first live run ended `max_steps_reached` before writing its section. Raised to 30,
matching the scaling the other agents already use (provenance 16 scripts → 30, docbuilder 24 →
50). It had never been run since the day it was written.

---

### BL-066 — Bump `bandit` to `~> 1.12` (hex.audit HIGH, EEF-CVE-2026-65623) (#TBD)
**Size:** XS · **Priority:** now (security gate red) · **Section:** harness (`../aetheris/mix.exs` + `mix.lock`)

Quadratic CPU blow-up reassembling fragmented WebSocket frames. Fix is a **version
bump, not an accepted advisory**: `aetheris/mix.lock` pins 1.11.1;
`aetheris/mix.exs:30` declares `{:bandit, "~> 1.0"}`; `mix hex.info bandit`
recommends `~> 1.12`.

**Touches:** harness repo (`aetheris/mix.exs` + `mix.lock`), tracked here per the
**BL-020** supply-chain precedent — same class, same ledger, so the advisory
history stays in one series instead of forking across two.

Surfaced off-territory by the m1-cloudcost t1 boundary gate, 2026-07-27. Until the
bump lands, `mix hex.audit` runs **expected-red, named with this ref**
(tracked-carry, not silent-carry).

```
Advisories:
  bandit 1.11.1 - EEF-CVE-2026-65623 (HIGH)
    aka: CVE-2026-65623, GHSA-vg8x-66vg-5pxh
    Quadratic CPU blow-up reassembling fragmented WebSocket messages in Bandit
    https://osv.dev/vulnerability/EEF-CVE-2026-65623

Found packages with security advisories
```

**Done when:** `mix hex.audit` is clean (exit 0), or any residual advisory carries
an explicit rationale on this row per the BL-020 accept path; the harness CI
contract passes with the bumped dependency.

**Status:** Done 2026-07-30 — commit `892b0f7`. `mix.exs:30` now declares
`{:bandit, "~> 1.12"}`; `mix deps.update bandit` resolved **bandit 1.12.4**, and moved two
co-resolved deps: `thousand_island` 1.4.3 → 1.5.0, `plug_crypto` 2.1.1 → 2.2.0 (`websock`
0.5.3, `plug` 1.20.3, `hpax` 1.0.4 unchanged). `mix hex.audit` → **`No retired or security
advisory packages found`**, exit 0 — verified after the bump, not assumed from the `~> 1.12`
constraint. Full CI contract green on the bumped tree: `compile --warnings-as-errors`,
`format --check-formatted`, `credo --strict` (2047 mods/funs, no issues), `dialyzer` (0
errors), `test` (969 tests, 0 failures, 133 excluded), plus `./scripts/sprint.sh
playground_api` — the Bandit-served path — green end to end.

> **Duplicate of BL-060**, which filed the same advisory one day earlier from BL-039's gate
> run; this row's "same class, same ledger" note missed it. Both closed by this commit. The
> harness has exactly one Bandit call site (`lib/aetheris/api/server.ex:25`,
> `Bandit.start_link(plug:, scheme:, port:, ip:)`) and no `WebSock` usage at all, so the
> advisory's fragmented-frame path was never reachable here — a bound on the exposure, not a
> reason the gate could have been left red.

---

### BL-069 — DO ≥1-orphan assertion is armed: its planted reserved IP is deleted (#TBD)
**Size:** S · **Priority:** now (live failure mode) · **Section:** aetheris-agents (cloudcost)

> **Done-when superseded 2026-08-06 (m4 t2, step 0).** The row offers two ways to close and the
> cycle has ruled out both as written. **Decision 12** (`cloudcost/m4-consolidation.md`
> §Ratified decisions → Technical) retires planted cloud resources on every provider, and reframes
> re-pointing as a **rule-legibility assertion** rather than a recorded orphan fixture. So this row
> closes by **retirement** — a third branch its own Done-when does not contemplate. The Done-when
> is marked `[corrected 2026-08-06]` below with the superseded text kept beneath it. Everything
> else in this row is record — what was planted, when it was deleted, the one run the Linode leg
> went green — and is left intact.

The DO cloudcost pipeline's `≥1 orphan` end-to-end assertion is a **known-positive
pipeline self-test**, not a business alert — it proves detection *fires* against the real
bill, using a planted orphan as the fixture. Reserved IP **168.144.13.150** (NYC1),
that fixture, was confirmed deleted 2026-07-30 (m1 loose end closed). So the next
DO-inclusive run finds **0** DO orphans and the assertion either fails, or — worse —
greens **vacuously** off a prior run's gitignored output (Silent-wrong-answer, harness
`CLAUDE.md`). Independent of the AWS work; m2 is per-provider (decision H), so AWS carries
its own planted Elastic IP and does not depend on this.

**`[corrected 2026-08-06]` Done when:** the practice is retired rather than re-fixtured. The
cloudcost sprint case no longer asserts a planted orphan; in its place it asserts the property
that tripwire stood in for — that the adapter's inventory **reached the rule catalog in a shape
the catalog could read**: every emitted `type` drawn from `_normalized.CANONICAL_TYPES`, imported
rather than restated, and an empty illegible-skip set. A zero-resource inventory reaches a stated
not-applicable arm and never a pass. Mutation posture is owed on **every** arm, not only the
failing one. And every live instruction anywhere in either repo directing an operator to create a
billable cloud resource is removed; records of what was planted stay intact.

> *Superseded 2026-08-01 text, kept:* "**Done when:** before the next DO run, either a fresh DO
> orphan is planted, or the assertion is re-pointed to a recorded fixture rather than the live
> account — and a DO run confirms the assertion passes for the right reason (mutation posture: it
> must fail when no orphan is present)."

**The Linode leg went green once, 2026-08-05 — and reverted.** m3 t3 planted a zero-backend
`common` NodeBalancer (`aetheris-m3-bl069-plant`, `2405879`, us-southeast) and the assertion
passed for the right reason: run `cloudcost-orch-linode-h5lltQ`, 1 candidate, rule
`idle_load_balancer`, confidence 0.85, **$10.00/month**, priced from `/nodebalancers/types` and
independently corroborated by July's `NodeBalancer` invoice line at $20.00 for the two
pre-existing balancers. The plant is deleted after the run (`cloudcost/runbook.md:307-310`), so
the Linode leg **reverts to red** and this row stays armed. Recorded so the row does not read as
never-green: the mutation posture the Done-when asks for is already demonstrated on one provider —
t3's first live read found zero zero-backend balancers and the sprint was not run, then the same
read found one and the assertion passed. What remains is a *durable* fixture, on any leg.
**DO and AWS are untouched by this** — the DO reserved IP is still deleted and the AWS Elastic IP
is still `m2-milestone.md` §Prereqs 3, pending.

**DONE 2026-08-06 (m4 t2) — by retirement. The DONE section itself is written 2026-08-08 at the
m4 close, and that gap is this row's second finding.** The work closed at t2; the row was never
marked, so §Ticket set and §What t2 established both read *closed by retirement* while the row
read open. **§Close criteria clause 1 caught it** — *"a row closed in the repo and open here, or
the reverse"* — which is the one thing that clause exists to do, on the one row where it had
something to find. Assessed per clause of the amended Done-when, verified at harness `288c8ef`:

| Clause | Satisfied by |
|---|---|
| *the practice is retired rather than re-fixtured* | the `≥1 orphan` assertion is gone from `../aetheris/scripts/sprint.sh`; `grep` for `orphan candidates` / `expected ≥1` returns nothing |
| *in its place it asserts … every emitted `type` drawn from `_normalized.CANONICAL_TYPES`, imported rather than restated* | `sprint.sh:3025` — `from _normalized import CANONICAL_TYPES`; membership tested at `:3048`, not restated in shell |
| *an empty illegible-skip set* | `:3048` computes `outside`, and `:3055` names both the offenders and the canonical set on failure |
| *a zero-resource inventory reaches a stated not-applicable arm and never a pass* | three arms at `:3071–3075` — `ok` / `warn` (not-applicable, explicitly *"an unknown, not a clean empty account"*, citing BL-098) / `fail` |
| *mutation posture is owed on **every** arm, not only the failing one* | all three arms mutation-checked at t2, the two failing ones against real artifacts rather than invented fixtures (§What t2 established) |
| *every live instruction anywhere in either repo directing an operator to create a billable cloud resource is removed; records of what was planted stay intact* | t2's substance census over both repos; re-verified at this close — no live plant instruction in `cloudcost/runbook.md` or `sprint.sh`. The records above are **kept deliberately**: they are history, not instruction |

**Two sentences above are superseded by this closure and are left standing as record**, per
decision 7: *"the Linode leg **reverts to red** and this row stays armed"* and *"What remains is a
*durable* fixture, on any leg."* Both were true when written and were made false by decision 12 —
there is no durable fixture because there is no fixture; the assertion the row was armed on no
longer exists. **No cloud resource was ever planted for this cycle**, and none is owed.

`Source: m2-cloudcost ratification, 2026-08-01; m1 loose end (reserved IP) closed 2026-07-30;
m3-cloudcost t3 live run 2026-08-05 (Linode leg green once, reverted on plant deletion). Retired
at m4 t2, 2026-08-06 (harness f8bbac8). DONE section written at m4 close-c, 2026-08-08, after
§Close criteria clause 1 found the row unmarked.`

---

### BL-069 — DONE 2026-08-06 (m4 t2) — closed by **retirement**, neither branch its Done-when offered

The row offered two closures: plant a fresh orphan, or re-point the assertion at a recorded
fixture. Decision 12 ruled out the first and reframed the second, so the row closes a third way —
**the assertion and the practice behind it are retired outright**. The Done-when was corrected at
t2's opening, before any implementation, with the superseded text kept beneath it.

**What was removed.** `../aetheris/scripts/sprint.sh` no longer asserts `orphan candidates ≥ 1`;
the assertion and its KNOWN-RED comment block are gone, replaced in place by a comment recording
why and warning the next reader off reinstating a count-based orphan check. An assertion whose
only satisfying state is *money being wasted on a live account* is not a check on the pipeline.

**What replaced it — rule legibility, three arms.** Outside the `CLOUDCOST_PERIOD` guard (it reads
the provider output directory, not the report, so it stays meaningful on exactly the runs where
the report is missing — the D2 credential grep's precedent). It reads the run's own two artifacts,
both found by pattern rather than by period, and imports the canonical vocabulary from
`cloudcost/scripts/_normalized.py` (`CANONICAL_TYPES`) rather than restating it in shell:

| Arm | Condition | Output |
|---|---|---|
| legible | resources evaluated, every emitted `type` canonical, nothing skipped, catalog count agrees with the inventory | `[OK]` |
| illegible | a `type` outside the closed set, a non-empty skip set, or a count disagreement | `[FAIL]` |
| not applicable | zero resources | `[WARN]`, stated as an unknown — never a pass |
| vacuity guard | either artifact missing, or not exactly one | `[FAIL]` |

No new sprint output state; `fail()`'s effect on exit status untouched; nothing under
`cloudcost/scripts/` edited (all eight blob hashes unchanged).

**Why the third arm reports an unknown rather than a clean not-applicable.** Whether the adapter's
*coverage* was complete is recorded in no artifact the sprint can read — the inventory envelope is
five keys and carries no `not_inventoried` (**BL-098**), and the adapter's summary, which does
carry it, dies at its own stdout (verified: 0 occurrences across 13 archived
`sprint/*/cloudcost/run.json` captures). The orchestrator-exit assertion cannot discharge it
either, because `mix aetheris` discards every command's exit code (**BL-044**, verified at harness
`871a720`). **BL-098 is what would discharge it**, and it is out of scope for this cycle. So a zero
is reported as *nothing was evaluated, and why is not established here*.

**Mutation posture, all arms** — each state constructed, the arm observed, then restored. The two
`[FAIL]` fixtures are real artifacts rather than invented ones: `cloudcost/output/do_inventory_2026-07.json`,
a surviving pre-m2 inventory carrying `droplet` / `reserved_ip`, drove the out-of-vocabulary arm;
an entry with `type` removed drove the skip arm; a real zero-resource AWS inventory drove the
not-applicable arm; the live DO run drove the pass.

**Live outcome, before and after**, same leg, same day:

```
[FAIL]  orphan candidates: 0 (expected ≥1 — BL-069 armed: …)                    (18:25, pre-edit)
[OK]    rule legibility: 18 resources evaluated, 0 skipped; types
        [compute_instance, load_balancer, volume] all drawn from the canonical set  (18:29, post-edit)
```

**The retirement sweep.** Censused by substance across both repos, not by the token "plant". Live
instructions were treated under the cycle's document rules: `cloudcost/runbook.md` corrected in
place (decision 8); `CLAUDE.md`'s gate-rule exemplar corrected in place, since it read as an
endorsement of planting; `cloudcost/milestone.md`, `m2-milestone.md` (including the
`Status: PENDING` prerequisite, which was an instruction awaiting execution rather than a record)
and `m3-milestone.md`, plus three handoffs, each given one dated superseded note with its original
text intact (decision 7). Records were left alone. The full census — terms run, every hit, its
classification and its treatment — is in `cloudcost/docs/m4-t2-implementation-notes.md`.

**Not verified against a live account:** the m3 Linode plant `aetheris-m3-bl069-plant`
(`2405879`) is recorded as deleted in two places — this row above, and
`docs/project-knowledge-manifest.md` — and this session holds no Linode credential, so that
remains a record rather than an observation.

`Source: m4-consolidation decision 12; m4 t2, 2026-08-06. Live runs sprint/20260806_182514
(pre-edit, run cloudcost-orch-digitalocean-XApoxQ) and sprint/20260806_182911 (post-edit, run
cloudcost-orch-digitalocean-OK48Sw).`

---

### BL-070 — Retire the dormant cross-provider merge code in `compose_report_data.py` (#TBD)
**Size:** S · **Priority:** low · **Section:** aetheris-agents (cloudcost)

m2 adopted per-provider reporting (decision H, no cross-provider roll-up), which makes the
N-merge, the `providers_without_prior_snapshot` caveat, the multi-currency "No combined
total" path, and the cross-currency 4-site aggregation all **unreachable**. m2 left them
**dormant** rather than deleting them, so `compose_report_data.py` stayed literally
unchanged and the "contract is mechanical" negative proof stayed pristine. Dead code that
is never exercised rots — delete it in a dedicated cleanup, not inside a ticket whose
result depends on `compose` not moving.

**Also converge the two slug functions — the risk class is silent-wrong-answer, not tidiness
(t2 review N1).** t2 added `_normalized.provider_slug()`, used by `detect_orphans` to write
`{provider}_orphan_candidates_{period}.json`; `compose_report_data.py` keeps an identical
private `slug()` for its history filenames. They were deliberately *not* converged at t2 —
that edit would have touched `compose` and spoilt the negative proof. Today both transforms
agree on every live provider token (`aws`, `digitalocean`), so there is no divergence to fix,
only one to prevent: a future provider whose name the two functions transform differently
would have `compose` silently find no orphans file and under-report — a well-formed report
with a section missing, not an error. Converge on the shared helper here, where `compose` is
already being edited.

**Done when:** the unreachable cross-provider merge / caveat / currency paths are removed
`[deferred 2026-08-07 — see the amendment note]`;
`compose` uses `_normalized.provider_slug()` and its private `slug()` is gone
`[DONE 2026-08-07, m4 t5b]`; the retained
single-provider compose has a test asserting its behaviour is unchanged; and the four m1 open
items those paths carried are marked resolved-by-deletion.

**Done-when amended 2026-08-07 (m4 t5b), before any deletion was made** — the same move t2 made
on BL-069 and t4b made on BL-074 clause 2: a row implemented against a premise the work has
already undermined is implemented against nothing.

*What changed.* **The cross-provider deletions are deferred, not cancelled**, pending **BL-131**.
The **slug convergence is discharged here**, independently of them, on §Contracts C9's explicit
assignment (*"BL-070 owns the convergence, to be taken when that file is next legitimately
edited"*) and on its own argument, which is divergence-prevention rather than reachability.

*What the deferral covers.* **Every target whose premise is decision-H-unreachability** — the
N-merge, the `providers_without_prior_snapshot` caveat, all four cross-currency aggregation sites,
and the multi-currency "No combined total" path — **not only the two that turned out to be
contract-covered.** m4 t5b's gate found C4 and C11 describing cross-provider behaviour as current,
but the premise is shared by targets no contract mentions, and a premise under question does not
become sound where nobody happened to write it down.

*Why the premise is under question — three states, not two.* This row calls the paths
**unreachable**; `cloudcost/milestone.md` §Open items calls them **"latent while m1 is DO-only
single-currency; live at the first fan-out"**; and m4 t5b's gate established a third reading: the
`--input-dir` route that reaches them is **declared in `cloudcost/tools.json` with a worked
example**, so it is an advertised interface that the orchestrator simply never invokes. Dead,
source-only, and live are three different things and this row assumed the first. BL-131 decides
which it is.

*One consequence recorded here rather than left to be rediscovered.* The multi-currency path is
reachable **only** through the N-merge, so retaining one while deleting the other would retain code
no input can reach — which is what this row exists to remove. The two cannot be taken separately in
either direction.

`Source: m2-cloudcost decision H, ratified 2026-08-01; slug convergence added from the t2
review's N1 (docs/reviews/m2-cloudcost-t2-review.md), 2026-08-02.`

---

### BL-070 — DONE 2026-08-10 (m5 t2) — the cross-provider deletions are **not taken**, by ruling

**m5-D2** (`cloudcost/m5-n1-compose.md` §Ratified decisions — *"the N>1 compose surface is
retained and bounded. It is a library-and-CLI capability the pipeline does not invoke, and it is
declared as such"*) disposes this row's deferred deletions **not taken**. The N-merge, the
`providers_without_prior_snapshot` caveat, all four cross-currency aggregation sites and the
multi-currency *"No combined total"* path all stay.

**The row's premise did not hold, and that is why.** This row called those paths **unreachable**;
m5 t1's **E1** established **three** routes that reach N>1 — the repeatable flags, `--input-dir`,
and the directory route — and that the route-bearing code is byte-unchanged since the commit
BL-131 read. So the paths are **reachable and uninvoked**, not dead: no orchestrator invocation
takes any of the three. Deleting reachable, advertised, tested code because nothing in one caller
happens to call it is the deletion m4 t5b withdrew and this ruling declines.

**Its four Done-when clauses, each disposed rather than left to be read against a ruling that
moved them:**

1. **The deletions** — **not taken**, per the above.
2. **The slug convergence** — already **DONE 2026-08-07 (m4 t5b)**, independently of this ruling
   and on C9's assignment. Unaffected.
3. **A test asserting the retained single-provider compose is unchanged** — **moot as written.**
   It existed to prove a deletion changed nothing; with no deletion there is nothing for it to
   bracket. The offline spine's 386 tests already constrain compose at N=1 and are unchanged by
   this ticket.
4. **The four m1 open items marked resolved-by-deletion** — **corrected in place, as this row's
   Done-when was once before at m4 t5b.** Nothing is deleted, so nothing is resolved by deletion,
   and the clause is unsatisfiable as written. Those items **stay open** in `cloudcost/milestone.md`
   §Open items with a determinate status they did not have before: the paths they name are
   reachable, uninvoked and now declared. **The one that changes character is the human-eyeball
   item** — *"Two of t4's rendered paths have never been looked at by a human"*, the new-provider
   caveat and the multi-currency *"No combined total"* rendering — which that section calls
   *"unreachable while DO is the only provider"*. Under this ruling they are **not** unreachable;
   they are uninvoked, and the eyeball is still owed by the first ticket that makes either
   reachable from the pipeline. §Open items is not in this ticket's `Touches` and is not edited
   here; the correction is recorded in this row, which owns the clause.

`Source: m5-D2, ratified 2026-08-10 at the m5 gate stop; applied at m5 t2, 2026-08-10. Route
count and byte-unchanged finding from m5 t1's E1 (cloudcost/docs/m5-t1-implementation-notes.md).`

---

### BL-071 — Resource-level AWS cost + the resource-rate spot-check (#TBD)
**Size:** M · **Priority:** low (deferred) · **Section:** aetheris-agents (cloudcost)

m2 settled AWS cost at **service-level** (decision B) because current AWS usage is low, so
resource-level (`GetCostAndUsageWithResources` — a paid hourly/resource opt-in, ~14-day
window, EC2-centric; or a CUR→S3 pipeline) would prove little and risk a vacuous proof.
The resource-level cost path is still unproven, and with it the m1 **resource-rate
spot-check** (checking the inventory size/type estimates against a real per-resource bill),
which has now been deferred past DO and AWS.

**Trigger:** the first provider actually billed per resource, or AWS usage growing enough
that enabling CE resource-level granularity is worthwhile. On trigger, the cost snapshot
carries `source_granularity:"resource"` with per-line `resource_id` where the provider
attributes it, and the rate spot-check lands as a test.

**Done when:** a resource-level cost path emits per-resource cost lines for at least one
provider, and the rate spot-check compares them against the inventory estimates.

`Source: m2-cloudcost decision B, ratified 2026-08-01; m1 open item (rate spot-check), re-forwarded.`

---

### BL-072 — Cost Optimization Hub / Compute Optimizer optimization milestone (#TBD)
**Size:** L · **Priority:** low · **Section:** Milestones

m2's t4 is a **hand-rolled read-only spike** for S3/ECR/Secrets waste signals
(no-lifecycle, incomplete-multipart, unused-secret), deliberately *not* the engine-backed
integration. AWS's own **Cost Optimization Hub** and **Compute Optimizer** already compute
rightsizing and waste recommendations across services; the full optimization milestone
sources from them rather than reinventing per-service heuristics. This is also where the
decision-F MCP evaluation's one genuine forward item lands (Hub/Compute Optimizer as an
alternative signal source to cross-check `detect_orphans.py`).

**Done when:** milestone docs exist (docs-first, per repo convention); t4's real-bill read
seeds the scope (which signals are worth surfacing, what noise looks like); read-only,
gated behind its own IAM.

`Source: m2-cloudcost decisions F + G (t4 spike), ratified 2026-08-01.`

---

### BL-073 — Surface a run's report artifact in Rig ("View report"), minimal (#TBD)
**Size:** S · **Priority:** medium · **Section:** aetheris-agents (`rig/`)

**Rescoped 2026-08-03** from the m2-filed generic row ("deferred; the delivery-side decision is
the weight of the ticket") to an actionable minimal build. The original's open question — how does
Rig learn the path — is **answered below against a real run**, which is what makes it buildable.
Generic over any report-producing use case (docbuilder too), **not** cloudcost-specific: no
cloudcost strings in Rig.

**The gap.** The report is a self-contained HTML at
`output/{provider}/cloudcost_report_{period}.html`; Rig shows the run but not the report, so "test
from Rig" ends at the file system. Pairs with per-provider **solo runs** (decision H): one run,
one report, so the run→artifact relation is 1:1 with nothing to disambiguate.

**Decision 1 — discovery: SCRAPE. Verified against run `cloudcost-orch-aws-oFbapA`,** not
inferred — the path is present in the completed run's trajectory twice, so no harness change and
no new event type is needed:

| Where | Event | Content |
|---|---|---|
| step 4, seq 28 | `tool_result` | the render step's stdout JSON, `file` = `output/aws/cloudcost_report_2026-08.html` |
| step 5, seq 32 | `llm_responded` | the same path restated in the LLM's closing prose |

**Read the `tool_result`, never the `llm_responded`.** The orchestrator prompt forbids the LLM
editing a path, but a UI affordance must not depend on a model honouring an instruction when the
tool's own structured output is right there. Parse `payload.output` → `stdout` → `file`.

**Selecting WHICH `file` — do not key on the render step, and do not key on `.html`.** A pipeline
emits a file from most of its stages, so "the render step's tool_result" is exact for cloudcost and
wrong as a general rule. Measured on the two real pipelines:

| Run | file-emitting `tool_result`s | Final artifact |
|---|---|---|
| `cloudcost-orch-aws-oFbapA` | 4 (costs+inventory, orphans, report_data, report) | `…/cloudcost_report_2026-08.html` |
| `docbuilder-orch-iDGIIQ` | 1, carrying **4 paths** | `…offer_letter….docx` **and** `.pdf` |

So the discriminator is the **document extension set** (`.html`, `.pdf`, `.docx`, …) — never
`.html` alone, which would find *nothing* in the docbuilder run and leave the control permanently
absent on the case this row exists to prove generic. Take the **last** qualifying artifact across
tool_results (later steps are more final; the intermediates are all `.json`). Note docbuilder emits
several documents in one result — two formats of two documents — so "last wins" is not
self-evidently right there: either offer the qualifying set, or take the last and say so, but do
not silently pick one of four and label it "the report".

*Two more things this row would otherwise discover mid-ticket:*
- **The path is relative** (`output/aws/…`). Resolve it against the run's `sandbox_path`, which is
  already in `runs.config_json` (`/home/it/…/aetheris-agents/cloudcost` for the verified run).
  Both halves are already stored — that is what makes "no harness change" true rather than hopeful.
- **Guard on `overlay_base_dir`.** It is `nil` for cloudcost by requirement, so the file really is
  at that path. A use case running under an overlay would resolve the same relative path into the
  overlay instead — show no control rather than a broken link, which the done-when already demands.

The alternative — a run that *formally records* an artifact path — is cleaner and
cross-provider-stable but touches the harness/orchestrator and likely the event union (the
three-change rule + `drift_check`), so it is **deferred**. Settle that convention before provider
three *if* you want it recorded rather than scraped; for this row, scrape.

**Decision 2 — surface + security: open-external or sandboxed.** A "View report" control in the
run detail. The HTML is our template and `render_report` escapes provider-supplied strings
(`test_provider_supplied_strings_are_escaped_not_injected`), but it still embeds provider data — so
**never `innerHTML` it into Rig's React tree**. Open in the OS browser (Tauri shell), or a
sandboxed `<iframe>` with a restrictive CSP, or a separate webview window. Open-external is the
smallest honest version.

**Scope guard — discover + open, nothing more.** Explicitly OUT: inline render with section
navigation, orphan/optimization panels, live refresh. That is the rich version, a separate small
milestone, and it is the scope-creep magnet of this batch; do not let it grow this row.

**Do-not-generate.** `innerHTML` of use-case HTML into the app DOM; any cloudcost-specific path or
logic in Rig (derive from the trajectory, keep it generic); a new event type unless the
recorded-path option is deliberately chosen (it is not, for minimal); trusting the LLM's prose path
over the tool's JSON.

**Doc-sync DoD carried from the original row:** any new Tauri command or `RunSummary`/`RunDetail`
field lands with its `specs.md` §4/§5 entry in the same commit (check 9 `command_fields` guards §4
structs). Follow the runbook's "Adding a new module" pattern (`harness.rs` query + `types.ts` +
detail view, the BL-004/BL-029 precedent).

**Done when:** from a completed cloudcost run's detail, "View report" opens the produced HTML
(external or sandboxed); the same control works for a docbuilder run with no cloudcost-specific
code; a run that produced no artifact shows no control or a disabled one, never a broken link;
`tsc -b` + `bun run build` + `drift_check --strict` green.

`Source: m2-cloudcost §Referenced Rig ticket, ratified 2026-08-01 (decision H); rescoped from the
m2-filed generic row at the m2 Rig thread, 2026-08-03, with discovery verified against run
cloudcost-orch-aws-oFbapA.`

### BL-073 — DONE 2026-08-04

Landed `2bfa984` → `11e53ef`, merged `d4f44e4`. Discovery scrapes document-extension paths from
`tool_result` (four guarded hops: `output` → JSON → `stdout` → JSON → recursive value-scan);
resolution + **existence gate** are server-side, which subsumes the overlay case *and* drops
docbuilder's `rename_output` `original` paths (renamed away by the step that reported them —
value-scanning yields six candidates for a three-document run, the gate keeps three). Offer-the-set:
one artifact → button, N → list. 8 unit tests + a live arm, with an explicit anti-vacuity control.

**Reopened once (r2).** The first cut opened via the frontend shell plugin, whose `open` is
URL-scoped and rejects filesystem paths — so it could never have worked. Fixed by opening
server-side (`harness_open_artifact`), which re-vets the path against a freshly computed artifact
set before `open::that_detached`; the shell scope is untouched, since widening it would have let
the frontend open any local file and discarded the existence-gated invariant. **The residual
concealed the defect** — "the open is owed" read as an unverified step when the primitive behind
it was unusable; promoted as a review learning.

**Live acceptance:** cloudcost's HTML opens; `docbuilder-orch-wFwf_g` (3 artifacts) renders the
offer-the-set list. Doc-sync in the same commits: `specs.md` §4 carries both commands.

`Source: BL-073, closed 2026-08-04.`

---

### BL-074 — Seam sweep: enumerate every provider-vocabulary / provider-assumption seam in shared machinery (#TBD)
**Size:** S–M · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/`)

m1 closed calling `STOPPED_STATES` *"the one seam where a provider's own vocabulary reaches
shared machinery."* m2 t1 found it is at least **three**:

1. **`state`** — `detect_orphans.py:71` `STOPPED_STATES = {"off"}` (DO vocabulary). Known at
   m1, resolved at **t2 (a)**.
2. **`type`** — every rule keys on the inventory `type` field, but m1's §Normalized schemas
   never enumerated its *values*, so DO's `droplet` / `reserved_ip` were provider vocabulary
   inside shared machinery. Surfaced at **t1**, resolved at **t2 (a′)**.
3. **The flat-billed-regardless-of-state cost assumption** — `rule_stopped_droplet_with_attached_storage`
   takes its saving from the instance's own `monthly_cost_estimate` (`detect_orphans.py:243`
   states the m1 forward: *"saving estimate is the instance's own monthly_cost_estimate;
   attached storage is named but not summed (m1)"*). True for DO, which bills a droplet on or
   off; false for AWS, which bills no compute for a stopped instance. Adapter half resolved at
   **t1** (a stopped instance reports `monthly_cost_estimate: 0.0`, keeping the provider's cost
   model in its adapter per D5); saving half at **t2 (c)**.

**Why a row rather than three fixes.** All three are being fixed. What is not fixed is the
thing that produced them: the "one seam" claim came from **observation, not enumeration** —
exactly the **Adjacent-case** rule (*"enumerate every site of that exact class before filing or
fixing the first one"*). Fixing the three found by accident leaves the same blind spot for the
fourth. So this ticket is the enumeration itself.

**Scope.** Sweep `detect_orphans.py`, `_normalized.py`, `compose_report_data.py` and
`render_report.py` for *any other* value, threshold, spelling or billing assumption a provider
could legitimately differ on, and decide for each whether it is schema-level (enumerate it in
§Normalized schemas) or adapter-owned (push it into the adapter). Named next candidates:

- the rule-catalog **age thresholds** (`UNATTACHED_VOLUME_MIN_AGE_DAYS`,
  `STOPPED_DROPLET_MIN_AGE_DAYS`, `DEFAULT_SNAPSHOT_AGE_DAYS`) — a provider whose billing
  granularity differs may want different ones, and today they are global constants;
- the **`keep=true` tag spelling** (`KEEP_TAG`) — DO tags are flat strings, AWS tags are
  key/value pairs flattened to `k=v` by the adapter, so the spelling is already an adapter
  convention masquerading as a shared constant;
- `EPHEMERAL_NAME_PATTERN`, and `TAGGED_ACCOUNT_COVERAGE_THRESHOLD`.

Also **correct m1's "the one seam" text where it appears** (`cloudcost/milestone.md` §Open
items) so the next reader does not re-derive the wrong count.

**Done when:** every provider-differing value in shared machinery is enumerated with a
schema-level-or-adapter-owned ruling; the ones ruled schema-level are in
`[amended 2026-08-07]` **§Contracts** ~~§Normalized schemas~~;
m1's "one seam" text is corrected; the sweep's *method* (how completeness was established) is
recorded, so this is an enumeration and not another observation;
`[added 2026-08-07]` **and the rows the rulings created are filed** — see the second amendment
note below.

**Done-when clause 2 amended 2026-08-06/07 (m4 t4b, reviewer's ruling), before the row was
assessed against it** — the same move t2 made on BL-069, and for the same reason: a row assessed
against a clause the work has already superseded is assessed against nothing.

*What changed.* The schema-level rulings live in **`cloudcost/milestone.md` §Contracts (C1–C15)**,
a new sibling section immediately after §Normalized schemas, not inside it. As written the clause
was **unsatisfiable**, so the row could not have closed cleanly against it.

*Why.* The two sections make different kinds of statement. **§Normalized schemas states shapes**;
**§Contracts states value semantics and adapter obligations.** Interleaving 48 of the second into
the first would make the shapes harder to read for every future reader — an argument that holds
regardless of anything else.

Secondarily, and stated as a floor with its method named: **at least 12 citations across 9 files**
call §Normalized schemas *frozen*, by a search of both repos for the literal word `frozen` within 40
characters of the section name. `cloudcost/m2-milestone.md` (×3), `cloudcost/m3-milestone.md`,
`cloudcost/runbook.md`, `cloudcost/docs/t1-implementation-notes.md` (×2),
`cloudcost/docs/t3-implementation-notes.md`, `cloudcost/docs/m3-linode-scout.md`,
`docs/reviews/m2-cloudcost-closeout.md` and two handoffs. So rewriting the section would have
falsified a standing claim in nine other documents in the same commit, and `cloudcost/runbook.md` —
live operational guidance — is the one that would have cost most.

*Two things about that figure, both corrected at t4b r2.* The search returns **13**, not 12: the
thirteenth is **this paragraph**, which the search matches because it contains the claim. Counting
the assertion as evidence for itself is the error, and it is excluded here explicitly rather than
silently. (It is **not** a harness hit — the search spans both repos and every genuine citation is
agents-side, so *"in this repo"* was doing no work and has been dropped.) And the figure is a
**floor**, not a census: the pattern requires the literal word *frozen*, so a document that says the
section is fixed as of m1 and must not be edited, without using that word, is invisible to it. The
argument needs a floor and never needed a count.

**Done-when clause 5 added 2026-08-07 (m4 t4b r2, reviewer's ruling — branch (a)).** t4b assessed
all four original clauses **satisfied** and still did not close this row. That reason lived only in
the ticket's packet and in `cloudcost/m4-consolidation.md`, so a reader of *this file* saw a row
whose stated Done-when was fully met, no DONE section, and no explanation in the row — the shape a
done-check exists to prevent, arriving from the other side.

*Why (a) rather than a hold note.* The assessment was **already applying a fifth clause**; it was
simply unwritten. An unwritten clause is worse than an amended one, because it cannot be reviewed
and it cannot be checked at the close. Writing it makes the row **honestly unmet** rather than
mysteriously open.

*What the fifth clause requires.* The rulings produced eleven items that stay broken whichever arm
they land in — a scoring modifier that has never fired, a billing case neither stopped rule covers,
a validation the sprint's own gate presumes absent — plus three exclusions to be recorded with their
reasons. **m4 t4c files them; this row closes there.** A Done-when satisfied by documents whose
consequences have nowhere to live is the complete-but-unmarked shape BL-102 exists for.

**§7 promotion candidate at m2 close** — Adjacent-case / enumerate-the-class, in its
"a uniqueness claim produced by observation" form.

**Coupling added 2026-08-06 (m4 t2): the sprint case is now a consumer of the vocabulary
surface this row sweeps.** The cloudcost sprint case's rule-legibility assertion imports
`CANONICAL_TYPES` from `cloudcost/scripts/_normalized.py` — deliberately, so the vocabulary is
never restated in shell. If this sweep relocates or renames it, `../aetheris/scripts/sprint.sh`
breaks, and it breaks *loudly* (the probe fails and the arm reads `[FAIL]`), which is the intended
posture. Two observations for the sweep, both found while wiring it:

- **`CANONICAL_TYPES` has no public accessor.** Adapters import the seven `TYPE_*` constants
  individually and never the set; nothing outside tests referenced the set before t2. If the sweep
  wants a stable surface, this is the moment to decide whether one exists.
- **`usable_resources()` checks that `type` is *present*, never that it is *canonical*.** An
  out-of-vocabulary `type` passes through as usable and simply matches no rule — silently. That
  gap is precisely why the sprint assertion had to check membership itself, and it is a candidate
  for this sweep's ruling: schema-level validation in `_normalized`, or left to the callers.

**DONE 2026-08-07 (m4 t4a / t4b / t4c).** All five Done-when clauses satisfied; assessed per
clause below.

| # | Clause | Satisfied by |
|---|---|---|
| 1 | *every provider-differing value … enumerated with a schema-level-or-adapter-owned ruling* | `cloudcost/docs/m4-t4a-implementation-notes.md` — **54 items** from a structural AST extraction over **518 nodes**, with a recorded completeness argument. Ruled at t4b: **48 schema-level, 4 adapter-owned, 2 neither**. **Qualification, stated not glossed**: the clause offers two arms and **two items fit neither** (D5, operator configuration; R4, an environment dependency), recorded with their reason under C15 rather than forced. |
| 2 | *the ones ruled schema-level are in §Contracts* `[amended]` | `cloudcost/milestone.md` **§Contracts (C1–C15)**. Every one of the 54 is cited by item id in **exactly one** contract — an exact bijection, derived not asserted. Clause amended 2026-08-07 before assessment (note above). |
| 3 | *m1's "one seam" text is corrected* | `cloudcost/milestone.md` §Open items, corrected in place. m2 had corrected *"the one seam"* → *"at least three"*; **that was itself an observation**, produced by the failure mode the sentence describes. The entry now states the censused count, asserts **no seam count** (t4a establishes a censused count, not a seam count), and carries its correction history by strikethrough. |
| 4 | *the sweep's method is recorded, so this is an enumeration and not another observation* | `cloudcost/docs/m4-t4a-implementation-notes.md` §2 — the extraction inlined verbatim and re-runnable, per-class node counts a reader can diff, the classification criterion, the exclusion record with reasons, and §2.7 *"what would not have counted"*, which names *"I searched for the known candidates and found them"* as the failure mode. §2.6 bounds the claim: an AST-class census is complete **relative to its class list**, and the method cannot answer from inside itself whether a further population remains. |
| 5 | *and the rows the rulings created are filed* `[added]` | **17 rows: BL-114–BL-130.** Ten defect rows (X4, F2, F3, N8, X5, P8, D16, P2, P11, D12) and seven contract-consequence rows (N3, D20, N5, N7, D6, P6, P7). Three exclusions confirmed already recorded in §Contracts with their reasons and deliberately not filed — D15 (C7), D17 (C3), P4 (C10). One candidate row **not** filed: D5's precondition was run at t4c and failed, and the residual is a note under C15. |

**What this row established, beyond its own fix.** m1 called `STOPPED_STATES` *"the one seam"*; m2
found three; the census found **54**, of which the seven candidates BL-074 and its later couplings
named account for eight items. **The substantive finding is that this was never a handful of seams
to close but a large, mostly undocumented contract** — which is why the deliverable was a contract
section rather than a migration, and why 48 of 54 ruled schema-level: these four scripts *are* the
shared machinery, so almost nothing in them should move to an adapter.

**The §7 promotion candidate this row carried** — *Adjacent-case / enumerate-the-class, in its "a
uniqueness claim produced by observation" form* — is now evidenced three times over in one lineage:
*"the one seam"*, then *"at least three"*, then a t4b correction that asserted a seam predicate over
all 54 which the census denies. Each was a count replaced without re-checking the claim it hung on.
Carried to the m4 close.

`Source: m4 t4a (census, agents 904a568), m4 t4b (§Contracts, agents 611feba), m4 t4c (rows,
this commit). Closed 2026-08-07.`

`Source: m2-cloudcost t1 review r0/r1 (docs/reviews/m2-cloudcost-t1-review.md), ratified
2026-08-01. Line citations verified at aetheris-agents 3bc970b. Coupling appended m4 t2,
2026-08-06.`

---

### BL-075 — `mix test` failed once then passed three times, identity uncaptured (#TBD)
**Size:** XS–S · **Priority:** low · **Section:** harness (`../aetheris/test/`)

Filed 2026-08-02 at the m2-cloudcost **t2** boundary, per the gate rule (*a red gate gets a
tracked ticket the day it's found, never carried silently*). t2 is single-repo Python work, so
`mix test` was an **off-territory** run — exactly the kind the rule exists to force.

**What was observed.** First run: `969 tests, 1 failure, 133 excluded`. Three consecutive
re-runs immediately after, same tree, same command: `969 tests, 0 failures, 133 excluded`.
Nothing in this ticket touches the harness (`../aetheris` is untouched at t2), so the failure
cannot be attributed to the change under test.

**What is not known — and why.** *The failing test's name.* The first run's output was piped
through `tail -12`, which showed the summary line and none of the failure block; by the time
the gap was noticed the run was gone. That is the **Complete-output** rule failing in its
mildest form — a count characterised from a fragment — and it is recorded here rather than
quietly dropped, because "1 failure" with no name is not a finding anyone can act on.

**Likely home, unconfirmed.** `BL-054` already exists for the `requires_worker` twelfth-slot
flake, and a 1-in-4 timing failure in the 88s sync block fits that shape. It is **not** claimed
as the same defect — no evidence connects them beyond plausibility.

**Done when:** either the flake is reproduced with its name captured (run the suite in a loop
with full output retained, e.g. `mix test --seed 0` plus repeated seeded runs) and folded into
BL-054 or filed on its own, or three further full-output runs come back clean and this row is
closed as unreproducible with that stated. Whichever way it goes, capture the **whole** output.

**Annotated 2026-08-08 (m4 close-b) — the flake reproduced, and this time it has a name.**
`mix test` was run off-territory at this ticket's boundary (close-b edits four markdown files and
no code, so the failure cannot be attributed to the change under test — the same reasoning this row
recorded in 2026-08). It reproduced **the 2026-08-02 shape exactly**: one failure, then three
consecutive clean runs on the same tree with the same command.

```
run 1:  969 tests, 1 failure,  133 excluded
run 2:  969 tests, 0 failures, 133 excluded
run 3:  969 tests, 0 failures, 133 excluded
run 4:  969 tests, 0 failures, 133 excluded
```

**The identity, which is what this row was filed to obtain:**

```
1) test a status change alone counts as activity, with no events at all
   (Aetheris.CLI.Commands.RunHelpersTimeoutTest)
   test/aetheris/cli/commands/run_helpers_timeout_test.exs:84
   code:  assert {:ok, %{run_id: ^run_id, status: :done}} =
            await_bounded(run_id, await_inactivity_timeout_ms: 300)
   right: {:error, "run await-status-activity-7139 stalled: no status or event
           activity for 300ms (last status: running, last event seq: -1)"}
   stacktrace: test/aetheris/cli/commands/run_helpers_timeout_test.exs:98
```

A **fixed 300 ms inactivity window** the machine missed under load.

**The "likely home" hypothesis is refuted, not confirmed.** This row was careful to call the BL-054
connection *plausible, not established*, and it was right to be: **BL-054 is the `requires_worker`
twelfth-slot flake**, and this is a different test in a different file, not `requires_worker`-tagged
(it ran — the 133 excluded are elsewhere). What the two do share is the **mechanism class** — a
fixed-ms window rather than a poll — which is exactly the cure BL-054's §Suggested order entry
already names: *"Fold into a polling-based rewrite of the fixed-ms windows when someone is in that
file."* So the two rows converge on one fix while remaining two defects.

**Deliberately not closed and not folded here.** The first Done-when arm asks for the flake
reproduced with its name captured **and then** folded into BL-054 or filed on its own; the fold-or-file
is the closing action, and close-b closes no row. The evidence is now on the row, in the repo, where
the next ticket can act on it — **note that the runs themselves are not retained anywhere, only this
transcription of them, which is BL-133's subject exactly.**

**And the second arm still has nowhere to be satisfied.** *"Three further full-output runs come
back clean"* requires that those runs' full output be **retained somewhere durable**, and **BL-133**
establishes that no such place exists: `../aetheris/sprint/` archives `run.json` alone, and
`mix test` output is archived nowhere at all. Three clean runs were observed here and their output
lives in a session scratchpad — which is to say the arm was *performed* and cannot be *evidenced*,
and a later tally assembled from packets would be a count over a capture nobody can check. That is
the very defect this row's own *"What is not known — and why"* paragraph records, arriving a second
time.

**The Done-when is deliberately left as written.** Amending it now — narrowing it to "three runs
observed in a session", say — would be writing a clause around the gap instead of naming it, and
would quietly relax a row rather than fix what makes it unsatisfiable.

**Where this row now stands:** arm 1's evidence is captured and durable (above); arm 1's *action*
— fold into BL-054 or file on its own — is the next ticket's, and BL-054 is now known to be the
wrong home. Arm 2 stays blocked on **BL-133**.

**Annotated 2026-08-09 (hc-c) — one green run, on a tree that edited this flake's own module.**
`mix test` at hc-c's boundary: **972 tests, 0 failures, 133 excluded**. It does **not** count
toward arm 2 (a single run, and its output is retained nowhere durable — the same BL-133 block),
and it is **not** evidence of a fix.

**It also cannot be read as an untouched-tree observation, which is why it is qualified rather
than just recorded.** hc-c edits `../aetheris/lib/aetheris/cli/commands/run_helpers.ex`, the module
`RunHelpersTimeoutTest` exercises, and **no `mix test` was run on this tree before those edits** —
so "green because of hc-c" and "green despite hc-c" are not separated by any measurement. What is
established from source: the flake's own file
(`../aetheris/test/aetheris/cli/commands/run_helpers_timeout_test.exs`) is untouched by hc-c; the
assertion it flakes on is the `:done` success path, while hc-c changed only `handle_run_status/5`'s
`failed` and `cancelled` branches; the branch it failed into — `continue_or_timeout/5`'s inactivity
arm — is unchanged; and no timing, poll interval or window is touched. **That is reasoning from the
diff, not a measurement.** Not re-run to chase a red: one green does not refute a flake and one red
would not confirm it.

**Annotated 2026-08-09 (hc-e's opening edit, E3) — a third observation, folded in from BL-135,
which was a duplicate row.** hc-d r3's boundary gate hit **the same defect**: same module, same
`…run_helpers_timeout_test.exs:84`, same `:98` stacktrace, same
`await_bounded(…, await_inactivity_timeout_ms: 300)`, same `stalled: … for 300ms … last event
seq: -1`. Only the generated run id differs (`-7139` at close-b, `-8610` here), and that is
`System.unique_integer`. **BL-135 should not have been filed** — the gate rule requires a tracked
row the day a red is found, not a row filed without checking whether one exists. BL-135 is kept as
the record of the duplication, not deleted.

```
run 1 (2026-08-02, m2 t2)        969 tests, 1 failure    identity uncaptured (tail -12)
run 2 (2026-08-08, m4 close-b)   969 tests, 1 failure    identity captured
run 3 (2026-08-09, hc-d r3)      972 tests, 1 failure    identity captured, same assertion
```

**What is new, and it is the first probe of the reproduction conditions rather than another
failure count: nine non-reproductions.** Eight consecutive runs of `…:84` alone on an idle machine
(all PASS), one under six deliberate CPU spin loops (PASS), and one full suite immediately after
(`972 tests, 0 failures`). So across three observations the failure is real and its trigger is still
**not established** — only the **100 ms margin** that makes it possible (a feeder sleeping 200 ms
against a 300 ms bound) is established, from the test's own source.

**Do not widen the bound to buy margin.** `await_inactivity_timeout_ms` is the behaviour under
test; inflating it weakens the assertion it exists to make. That is this row's own *"fixed-ms window
rather than a poll"* mechanism class, and BL-054's §Suggested order entry already names the cure —
*"fold into a polling-based rewrite of the fixed-ms windows when someone is in that file."*

**Annotated 2026-08-09 (hc-e's opening edit, E4) — arm 2's blocker is PARTLY lifted, and the
remaining gap is a different shape.** The blocking clause read: *"Three further full-output runs
come back clean"* requires that those runs' full output be **retained somewhere durable**, and
**BL-133** establishes that no such place exists: `../aetheris/sprint/` archives `run.json` alone,
and `mix test` output is archived nowhere at all.*

**The first half of that premise is now false.** hc-d discharged BL-133 face 2: every sprint run
retains `console.log` — every arm, in order, untruncated, streams merged — beside a
`provenance.txt` naming both repos' commits, the target and the command, under a stated, bounded and
enforced 30-day retention. A durable place with provenance **exists**.

**The second half still holds, and it is the half arm 2 needs.** Established rather than assumed:

- `sprint.sh` invokes `mix test` **once**, at `:1517`, on **two named files**
  (`server_checkpoint_test.exs`, `server_inject_test.exs`) inside one case — not the suite.
- It never references this flake's file: `grep -c 'run_helpers_timeout_test'` over
  `../aetheris/scripts/sprint.sh` → **0**. *Positive control:* `grep -c 'server_checkpoint_test'`
  → **3**, so the pattern finds referenced test files where they exist.
- The boundary-gate `mix test` is a **direct invocation**, outside any sprint process, and
  `SPRINT_CONSOLE` exists only inside one — so its output is not captured.
- Measured against the retained corpus: `grep -rlE '[0-9]+ tests, [0-9]+ failures' sprint/*/console.log`
  → **0 files**. *Positive control:* the same pattern over a direct `mix test` capture → **1**.

**So: the place exists; the routing does not.** Arm 2 remains unsatisfiable as written, but the
blocker has changed shape — from *"no durable place exists"* to *"the full suite is never run where
the durable place would capture it."* That is smaller, and it is a routing decision rather than a
ruling. **Face 1 (reviews as session artifacts) is untouched and is not what arm 2 needed** — arm 2
is about run output.

**One thing recorded against hc-d's own reasoning:** hc-d chose the 30-day retention bound *citing
this row's "three further full-output runs come back clean"* as its justification. That citation was
optimistic — the bound was set for a consumer the mechanism does not yet serve. The bound is not
wrong; its stated rationale reached one step further than the mechanism does.

**Arm 2 is not started here.** E4's whole scope was establishing the blocker's status.

`Source: m2-cloudcost t2 done-check, 2026-08-02 (aetheris-agents 7a7b7ec; aetheris fd9ac48,
untouched). Annotated at m4-cloudcost close-b, 2026-08-08 — close-a Part 5 for the retention
finding; the reproduction and the failing test's identity are this close's own four runs, at agents
2806305 / aetheris 288c8ef, neither of which touches harness code. Annotated again 2026-08-09 at
hc-e's opening edit (E3 fold, E4 blocker status), at agents f8ed90f / aetheris 48f59e7.`

---

### BL-076 — `compose_report_data` sums *every* provider's prior snapshot into one `prior_total` (#TBD)
**Size:** S · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`)

Filed 2026-08-02 at the m2-cloudcost **t3** boundary. A **Silent-wrong-answer**: the month-on-month
headline is well-formed, plausible, and wrong.

**The defect.** `load_prior_snapshots` (`:711`) globs the prior month's directory
indiscriminately —

```python
for path in sorted(directory.glob("*.json")):   # history/{prior}/ — every provider
```

— and `month_on_month` sums whatever it returns into one figure (`:334`, `:342`):

```python
prior_total = round(sum(prior_providers.values()), 2)
"delta_amount": round(current_total - prior_total, 2),
```

That is m1's N-provider merge assumption (*everything in the month belongs to this report*)
meeting m2 decision H (*each provider is its own solo run*). Under H it is false: a solo run's
report is about the providers **in that run**, so its delta must read those providers' prior
snapshots and no others.

**Demonstrated, not inferred.** t3 ran the real AWS pipeline's output through `compose` twice,
changing only `--history-dir`:

| history tree | `mom_delta.status` | headline |
|---|---|---|
| shared `history/2026-07/` | `ok` | `prior_total 185.50` (DigitalOcean, July) vs `current_total 0.29` (AWS, August) → **`delta_amount −185.21`** |
| per-provider `history/aws/` | `no_prior_month` | — |

The `ok` row is the wrong answer: it reports a −$185.21 month-on-month movement for an account
whose first-ever snapshot this is. It also contradicts §t3's own done-check ("first run → the
m1-tested 'no prior month' path"). `providers_only_in_prior: ["digitalocean"]` is emitted as a
caveat, so the report is not *silent* — but the headline figure is the thing a human reads.

**Why it is not fixed here.** §t3 permits exactly one enumerated `compose`/`render` change (A4);
anything further is a contract-leak finding to report, not to write. t3 therefore mitigated it
**at the orchestrator** — each provider gets `--history-dir history/{provider}`, decision H's own
`history/{provider}/{period}/` layout, needing no script change. The mitigation is real and
verified live, but it is a *convention* the caller must honour: a direct `compose` invocation
with the m1-shaped shared tree still produces the wrong figure.

**Done when:** `load_prior_snapshots`/`month_on_month` scope priors to the providers present in
the run's own bundles, with a test asserting the `no_prior_month` path survives another
provider's history sitting in the same tree, and a second asserting an N>1 run is unchanged (so
the fix does not over-filter). Natural batch with **BL-070**, which retires the surrounding
cross-provider merge code — this row is the one piece of that code that is not merely dead but
actively wrong, so if BL-070 slips, do this alone. Fold in the duplicated `slug()`/`provider_slug()`
convergence at the same time (t2 deferred it precisely to keep `compose` unedited).

`[Annotated 2026-08-16 at BL-153 s0 — **this row's convention-only mitigation has now been
observed failing in the tree, unprompted**, and the observation is recorded here rather than
as a new row because this row already owns the mechanism and stays open. s0's read of
`cloudcost/history/` found two directory shapes on disk. They are **not two composer
layouts**: `persist_history` writes exactly one shape,
`{history_dir}/{period}/{provider}_costs_{period}.json`
(`cloudcost/scripts/compose_report_data.py:989`), and the two shapes are two values of
`--history-dir`. The orchestrator passes `history/{provider_slug}`
(`cloudcost/agents/cloudcost_orchestrator.exs:141`) — this row's mitigation — giving
`history/{provider}/{period}/`, which is what four providers have. The odd one,
`cloudcost/history/2026-08/github_costs_2026-08.json`, is the **default** path:
`--history-dir` defaults to `DEFAULT_HISTORY_DIR`, the shared `cloudcost/history`
(`:111`, `:1037`). **Not residue of a layout change** — the per-provider layout predates it
and its mtime is `2026-08-14 08:18`, six hours *before* that same day's provider-scoped
GitHub run at `14:29`. It is a direct `compose` invocation that omitted the flag, i.e. the
very *"a direct `compose` invocation with the m1-shaped shared tree still produces the wrong
figure"* this row's **Why it is not fixed here** paragraph names, firing in the tree twelve
days after the row predicted it and noticed by nobody at the time.

**The stray artifact itself is inert and needs no cleanup.** `cloudcost/history/` is
gitignored (`cloudcost/.gitignore:10`, `history/*`; only `.gitkeep` is tracked), and
`load_prior_snapshots` reads `history_dir / previous` (`:1002`), which under the
orchestrator is `history/github/2026-07` — never the flat tree. Nothing an orchestrated run
does can read it. What is *not* inert is the default that produced it, and that is this
row's subject, not a new one. `cloudcost/tools.json:514` already documents the consequence
in the operator-facing description, and `cloudcost/runbook.md:415` documents a migration
command for the old shape — so the hazard is captioned in two places and guarded in none,
which is what **Done when** above is for.

**Also: two of this row's own citations have drifted.** `load_prior_snapshots` is at `:994`
(the glob at `:1006`), not `:711`; the two `month_on_month` lines are `:352` and `:360`, not
`:334`/`:342`. The code at those lines is unchanged in substance — the row's quoted
`for path in sorted(directory.glob("*.json"))` and
`prior_total = round(sum(prior_providers.values()), 2)` are both present verbatim. Verified
at agents `900662f`. **No fix proposed and no scope widened**; the Done-when stands as
written.]`

`Source: m2-cloudcost t3, 2026-08-02 (aetheris-agents cbf3fbf). Verified by reading
compose_report_data.py:711/:334/:342 and by the two-run demonstration above.`

---

### BL-077 — `sprint.sh` assertion failures do not affect the sprint's exit code (#TBD)
**Size:** S–M · **Priority:** medium · **Section:** harness (`../aetheris/scripts/sprint.sh`)

Filed 2026-08-02 from the m2-cloudcost **t3** review (claude-ui N1). Pre-existing and
**sprint-wide** — all 31 cases, not t3's to fix, which is why it is a row rather than a patch.

**The gap.** `fail()` is a printer:

```bash
fail()    { echo -e "\033[0;31m[FAIL]\033[0m  $*"; }
```
(`sprint.sh:37`, verbatim.)

It sets no exit status and no failure flag, and `run_agent`/`run_orb` wrap their invocation in
an `if` so a non-zero child exit is swallowed too. Only the explicit `exit 1` preflights
(missing tool, missing credential) can make the script exit non-zero. So a sprint whose
**assertions** all fail still exits **0**.

Observed concretely at t3: both cloudcost legs printed
`[FAIL] orphan candidates: 0 …` and the sprint exited 0 either way. The red was real and
correctly reported — but nothing downstream of `$?` could have known.

**Why it matters.** It makes the sprint's exit code a check that passes identically whether or
not the thing under test worked — the **Silent-wrong-answer** shape, one level up, in the
apparatus rather than in a script. Any CI job, cron wrapper, or `&&` chain keying on `$?` reads
a fully-red sprint as success. The gate rule (*every existing gate runs at ticket boundaries; a
red gate gets a tracked ticket the day it's found*) leans on someone **reading** the output,
which holds for a human at a terminal and fails for anything automated.

**Not a trivial flip.** Making `fail` set a flag turns every currently-tolerated red into a
sprint failure at once — including tracked known-reds like **BL-069**, which are *supposed* to
stay visible without blocking. So the row has a design question, not just an edit:

- a `FAILURES=$((FAILURES+1))` counter plus a final `exit $(( FAILURES > 0 ))`, and
- a companion `expected_fail()` (or a `KNOWN_RED` allowlist keyed by ticket ref) so a tracked
  carry prints its `[FAIL]` line and its ticket without flipping the exit code.

Without the second half this fix cannot land while BL-069 is armed.

**Done when:** the sprint exits non-zero when an untracked assertion fails, tracked known-reds
are declared with their ticket ref and do not flip the exit, the summary block prints the
pass/fail tally (it is static text today), and the change is mutation-checked — deliberately
break one assertion in one case, confirm a non-zero exit; restore, confirm zero. Audit all 31
cases for reds that would newly become blocking before flipping the default.

> **`[corrected 2026-08-09 (hc-d, G5). The population is 29, not 31 — derived, not inherited.]`**
> One pattern, stated: `^if \[\[ "\$TARGET" ==`, the line that opens a case block.
> **30 blocks, 29 distinct case names** (`uc4` opens twice, at `:202` and `:303`); `all` is the
> selector, not a case. Both non-case-head `$TARGET` lines are accounted for rather than dropped —
> `:192` is the credential preflight's `!=` guard and `:1467` is an inner exit inside the
> `playground_api` case. The independent population agrees: `$TARGET ==` takes 30 distinct values,
> one of which is `all`.
>
> **Identical at `fa158a4`, the commit this row cites, and at `1b09b23`** — so the row was wrong
> when filed, not overtaken. **Whether 31 has a provenance is NOT established and is therefore not
> offered:** `grep -c 'section "'` returns exactly 31 at both commits (29 indented + 2 unindented),
> which makes it the only quantity in the file equal to 31 and a live candidate — but a plausible
> explanation for a wrong number is not a truth-maker, and nothing in either repo settles what the
> row's author counted.
>
> The audit clause is answered by **R7's fail-safe posture** rather than by sweeping 29 cases: no
> arm becomes blocking without individual verification, so nothing newly blocks by default and the
> undeclared count is printed on every run.

**Status:** Done 2026-08-09 — hc-d. `fail()` now counts; `blocking_fail`/`blocking_ok` are the
per-arm promotion; `expected_fail <BL-row>` is the tracked carry and rejects an entry naming no
row; `known_red_healed` makes a healed entry a failure. The summary prints all four counters
including zeros, and the script exits 1 iff a blocking failure occurred. **Mutation-checked both
ways on a real red**, not a simulated one: a phantom event type added to `docs/rig/specs.md` §6
made the promoted `drift_check` arm fail — `sprint.sh drift_check` exited **1**; restored, it
exited **0**. R17's arms (b) and (c) were constructed and observed. **One arm promoted** — the
`drift_check` case, the only one individually verifiable here without credentials or network;
every other arm stays undeclared by design, which is R7, not an omission.

`Source: m2-cloudcost t3 review, claude-ui N1, 2026-08-02 (aetheris fa158a4; observed on both
cloudcost legs). Reported by claude-code in the t3 packet before the review raised it.`

---

### BL-061 — Gemini thought signatures are not recorded, so a forked Gemini run loses them (#TBD)
**Size:** S · **Priority:** low-medium · **Section:** harness (`../aetheris/lib/aetheris/execution/`)

Raised 2026-07-26 by BL-039's review (F1). **Not a demonstrated defect** — a reachable gap
whose provider-side effect is unestablished, filed so the question has an owner and a
trigger rather than living as a contract sentence with neither.

**The gap.** Gemini returns a thought signature on a tool call. `gemini.ex` parses it off
`extra_content.google.thought_signature`, carries it on the response as
`:thought_signature_blob`, and `CanonicalMessage.assistant_tool_use_message/2` puts it on
the canonical `tool_use` block; `build_tool_calls/1` re-attaches it on the way out. So a
**live** Gemini run round-trips the signature. It is not among the ten keys `loop.ex`
writes to `:llm_responded`, so a **forked** one cannot: reconstruction calls the same
builder with a payload-derived map that lacks the key, `Map.get/2` returns nil, and the
block is emitted signature-free. That degradation is deliberate and is what lets one
builder serve both paths (BL-039 §4) — the open question is only what Gemini does with it.

**What is *not* the gap.** The review sketched this as Anthropic interleaved thinking
requiring a signed thinking block on a replayed assistant turn. That case cannot arise
here: the harness sends no `thinking` parameter from any call site, so Anthropic returns
no thinking blocks to lose. `:thought_signature_blob` has exactly one producer
(`gemini.ex`) and one consumer (the same file). The invariant the review named holds —
§4's "does not preserve" list was incomplete — but against the Gemini family, not the
Anthropic one.

**Trigger:** the first fork of a Gemini tool run. Nobody has run one; if the answer is
"degrades silently and correctly", this closes as a one-line §4 confirmation with the
run recorded.

**Two dispositions, and the cheap one may be enough.** (a) Record the signature — add
`"thought_signature"` to the `:llm_responded` payload and read it back in
`tool_call_messages/2`. This is a **record-path change**, which BL-039 was explicitly
forbidden; it also touches `payload_fields` in `drift_check` and specs.md §6 (a `?`-suffixed
optional field, per the optional-payload-fields rule). (b) Confirm Gemini tolerates a
missing signature on a replayed call and leave §4's limitation standing as documentation.
Do **not** ship (a) before establishing (b) is insufficient — the harness records what it
needs, not everything it sees, and one un-round-tripped provider hint is not obviously
worth widening the event schema for.

**Done when:** a Gemini fork of a tool step has been run and its outcome recorded, **and §4
is updated from that work either way** — the limitation is confirmed harmless and the clause
says so, *or* the signature is recorded, the fork round-trips it, and the clause's Gemini
scoping is corrected in the same change, with a test that fails if the block loses its
signature. §4 currently states the omission as unestablished-in-effect; the moment the effect
is established, that sentence is stale in whichever direction the answer goes, so neither
branch closes without touching it. (Review r2: the soft end of the same both-ends discipline
BL-059 carries in its hard form — there the coupling is code-to-code and a diff can break the
other side invisibly; here it is code-to-contract and the contract can go quietly wrong
instead.)

---

### BL-060 — `mix hex.audit` is red: bandit 1.11.1 carries EEF-CVE-2026-65623 (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/mix.exs`, `mix.lock`)

Found 2026-07-26 by BL-039's ticket-boundary gate run — off-territory, exactly the way
the gate rule intends. Filed the day it was found, not carried.

```
bandit 1.11.1 - EEF-CVE-2026-65623 (HIGH)
  aka: CVE-2026-65623, GHSA-vg8x-66vg-5pxh
  Quadratic CPU blow-up reassembling fragmented WebSocket messages in Bandit
  https://osv.dev/vulnerability/EEF-CVE-2026-65623
```

**Upstream-triggered, not commit-triggered** — the advisory was published under a lock
file nobody touched, which is the case `CLAUDE.md`'s `hex.audit` section names as the
gate working rather than failing. BL-020 cleared all 15 advisories on 2026-07-17 with no
residuals, so this is a fresh one, not a regression.

`mix.exs` requires `{:bandit, "~> 1.0"}` and the lock pins **1.11.1**; hex advertises
`Config: {:bandit, "~> 1.12"}` with 1.12.3 released 2026-07-25. So a patched line exists
and the constraint already admits it — this looks like a lock bump plus a `mix.exs`
floor, not a migration. **Confirm the advisory is actually fixed in the 1.12 line before
bumping** (this row read the version list, not the changelog) and check the
`thousand_island`/`websock`/`plug` co-resolution.

Reachability is worth a sentence in the fix, not a reason to defer: bandit backs the
playground API, which is **disabled by default** and started on demand
(`api/server.ex`), and the WebSocket path is not something the harness exposes today.
That bounds the exposure; it does not clear the advisory, and `hex.audit` has no
suppression mechanism.

Until it lands, the gate runs **expected-red, named with this row's ref** per the
tracked-carry clause — named in packets, not re-triaged.

**Done when:** `mix hex.audit` is clean, or the residual advisory has a recorded
rationale here and the gate's expected-red state is stated with this ref.

**Status:** Done 2026-07-30 — commit `892b0f7`, the same bump that closes **BL-066**, which
filed this identical advisory a day later (2026-07-27, off m1-cloudcost t1's gate run) without
noticing this row. BL-060 is the original; keep the fix detail on BL-066's row.

Both of this row's pre-conditions were checked rather than assumed: the advisory **is** fixed in
the 1.12 line — `mix hex.audit` is clean at the resolved **bandit 1.12.4** — and the
co-resolution moved `thousand_island` 1.4.3 → 1.5.0 and `plug_crypto` 2.1.1 → 2.2.0, leaving
`websock`/`plug`/`hpax` where they were. The reachability sentence this row asked for: the
playground API stays disabled by default and on-demand, and `grep` over `lib/` finds one Bandit
call site and no `WebSock` usage, so the fragmented-frame path was never exposed.

**The gate is green as of this commit** — the expected-red carry above no longer applies, and
any packet naming `hex.audit` red against BL-060 or BL-066 is out of date.

---

### BL-059 — Parallel tool calls are silently discarded: the adapter keeps the first `tool_use` block (#TBD)
**Size:** M · **Priority:** medium · **Section:** harness (`../aetheris/lib/aetheris/execution/`)

Raised 2026-07-26 by BL-039's §8 contract adjudication, which was about to make this
defect load-bearing. Not part of BL-039 — that ticket must not change the record path.

**The defect.** `anthropic.ex`'s response parse selects the tool block with
`Enum.find/2`:

```elixir
tool_block = Enum.find(content_blocks, fn b -> Map.get(b, "type") == "tool_use" end)
```

`find`, not `filter`. When a response carries several `tool_use` blocks, the first is
executed and **every other one is dropped before any event is written** — no
`tool_called`, no `tool_result`, no warning, no trace in the trajectory that a call was
ever requested. The model's turn is answered with one result where it asked for several.

**Why this is live, not theoretical.** Anthropic's API permits parallel tool use and it
is **on by default**; the documented client contract is to execute every `tool_use` block
and return all `tool_result` blocks in one user turn. The harness never opts out:
`RunConfig` defaults `tool_choice: nil` (`run_config.ex:96`) and `build_request_body/2`'s
`maybe_put` drops a nil, so `disable_parallel_tool_use` is never sent. Every real
Anthropic run is therefore eligible for parallel calls, and would silently lose them.

Whether any recorded run has actually hit it is **unknown and not established by the scout
sweep**: 537 recorded tool steps across 91 trajectories all carry exactly one
`tool_result`, but that is the *post-discard* record — it is what a step looks like both
when the model asked for one tool and when it asked for four. The record cannot
distinguish the two cases, which is the defect's own signature. Do not read that sweep as
evidence the case has never fired.

**Blast radius beyond the dropped call.** `loop.ex` builds one `assistant_tool_use_message`
per step from the single surviving response, so the transcript sent back on the next step
also claims the model made one call. The conversation the provider sees is not the
conversation it produced.

**Why BL-039 raised it.** Fork reconstruction pairs a recorded tool result with the tool
call at the same step, positionally. That is sound *only* while a step carries at most one
call — which is true today solely because of this discard. The ratified §4 clause
(`../aetheris/docs/reviews/bl-039-contract-draft.md`) names the dependency and its
enforcement point rather than asserting one-call-per-step as a property of the world, so
fixing this row does not silently break fork pairing; it obliges a matching change there.

**Two dispositions, and the choice is a product decision.** (a) Honour parallel calls —
execute each block, record a `tool_called`/`tool_result` pair per call, and emit one
assistant turn carrying all `tool_use` blocks followed by one user turn carrying all
`tool_result` blocks. Touches the response shape (`tool_use_id` is already parsed but only
one survives), the loop's per-step event model, and every reader that assumes one result
per step — including `Fork.event_to_messages/1` and the verifier. (b) Decline them
explicitly — send `disable_parallel_tool_use: true` so the provider returns one call and
the record is honest. (b) is small and stops the silent loss immediately; (a) is the real
fix. They are not exclusive: (b) is a defensible interim if (a) is not scheduled, but
shipping (b) alone must be recorded as a deliberate capability limit, not a fix.

**Sequencing.** Independent of BL-039 and must not be batched with it — BL-039 is
docs-first with an explicit do-not-generate on record-path changes. If (a) lands first,
BL-039's positional pairing needs revisiting before it is written.

**(b) is not closure, and must not be recorded as it.** Disabling parallel tool use stops
*future* silent loss. It tells you nothing about whether past runs dropped calls, and
nothing ever will: the recorded step is byte-identical whether the model asked for one
tool or four, so the corpus cannot be audited after the fact. That indistinguishability is
why (a) is the real fix. If (b) ships alone, record it as a deliberate capability limit
with the un-auditable history named — not as "parallel tool calls: handled".

**Done when:** a run whose provider response carries multiple `tool_use` blocks either
executes and records all of them (a), or cannot occur because the request disables
parallel tool use (b) — with the choice recorded in the determinism contract, and a test
that fails if the extra blocks are silently dropped. A stub response carrying two
`tool_use` blocks is the cheap regression exercise; assert on the recorded events, not on
the run's status.

**Additionally, for disposition (a) — the reciprocal of BL-039's §4 note, and the reason
this line exists:** the same commit must update fork reconstruction to pair *N* `tool_use`
blocks against *N* `tool_result` blocks per step. BL-039's positional pairing is sound only
under one-call-per-step; the day (a) lands, that premise is gone. **A (a) diff confined to
`anthropic.ex`/`run_config.ex` breaks `fork.ex` without touching it** — the same
diff-invisible break the §4 clause guards against, running the other direction. §4 names
the dependency from the fork side; this line names it from the adapter side, so neither
ticket can land its half and leave the other silently wrong. Fork's done-check must be
re-run as part of (a), not deferred to whoever next opens `fork.ex`.

**BL-039 has landed (2026-07-26), so the fork side is now concrete.** The pairing lives
in `Fork.event_to_messages/1` and the id in `Fork.synthetic_tool_use_id/1`, which derives
`"fork-toolu-#{step}"` — one id per *step*, which is precisely the assumption (a)
removes. Both the function's comment and §4 point here. Under (a) the id must become one
per *call*, and the `:tool_result` clause must consume N results rather than one; the
canonical blocks themselves need no change, since `CanonicalMessage` already builds one
block at a time and both turns take a list.

---

### BL-040 — Event-type list exists in three places; drift between them is silent (#TBD)
**Size:** S · **Priority:** low-medium

The set of trajectory event types is written out three times:

| Site | Shape | Purpose |
|---|---|---|
| `../aetheris/lib/aetheris/trajectory/event.ex` `@type event_type` | type union | documentation / dialyzer |
| `../aetheris/lib/aetheris/trajectory/event.ex` `@event_types` | literal atom list | atom-table guarantee; `known_types/0` |
| `../aetheris/lib/aetheris/trajectory/file.ex` `@event_type_map` | `~w[…]a` → map | JSON trajectory deserialisation |

`Store` was made to derive from the canonical list at BL-031 r2 (`a935038`), so it is
no longer a fourth copy. `Trajectory.File` still holds its own, and the `@type` union
cannot be derived from a list at all — so nothing makes the three agree.

**The drift is not hypothetical — it is already present.** `:run_started` appears in
`File.@event_type_map` and in `@event_types`, is **absent** from the `@type
event_type` union, and is emitted by **no code path in `lib/`** (verified at
`a935038`). So one deserialiser accepts a type the type spec denies and the harness
never writes. Nobody noticed because no mechanism could.

**Done when:** `Trajectory.File` derives its map from `Event.known_types/0`, and a
test asserts the `@type` union and `@event_types` agree — the union is not derivable,
so the test is the only possible guard. The test must also adjudicate `:run_started`:
delete it as a phantom, or add it to the union and name what emits it.

**Surfaced by** BL-031 r2's boot-crash regression, where `Store`'s
`String.to_existing_atom` deserialisation depended on some *other* module having
mentioned the atom first (`docs/reviews/bl-031-review.md`).

> **Sequencing note, correcting the round-2 finding.** F23 suggested sequencing near
> BL-033 and checking BL-033's `:fork` removal against `@event_types`. These are two
> different unions: BL-033 concerns `RunConfig.@type mode` (`run_config.ex:115`),
> whose vestigial member is `:fork`. `:fork` is a **mode, not an event type** — its
> absence from `@event_types` is not a deliberate removal, and there is no
> interaction between the two rows. Sequence BL-040 on its own merits.

### BL-078 — Converge the AWS client plumbing into a shared `scripts/_aws.py` (#TBD)
**Size:** S · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/`)

Filed 2026-08-02 at the m2-cloudcost **t4** boundary, deferred deliberately rather than
discovered.

**The state.** `detect_optimization_signals.py` needs the same AWS plumbing `fetch_aws.py`
already carries — `load_credentials`, `warn_shadowing_env`, `AWSClients` (explicit-session
construction, the `AWS_PROFILE` neutralization, `redact`), `enumerate_regions`, `paginate`,
`error_code`, `write_json` — so it **imports them from `fetch_aws`**. That is a CLI-to-CLI
import, which the repo's own rule (`CLAUDE.md`, m2b learning) says should be a shared
`scripts/_helper.py` instead.

**Why it was not done at t4.** Lifting them means editing `fetch_aws.py`, and t4's
Do-not-generate list forbids touching it. The alternative — duplicating `AWSClients` — would
put a second copy of the D2 credential guarantee in the tree, which is strictly worse than one
import: two copies of that guarantee are two things that can drift apart, and the one that
drifts silently is a credential falling back to the default chain.

**Done when:** `AWSClients` / `load_credentials` / `warn_shadowing_env` / `enumerate_regions`
live in `scripts/_aws.py`; both CLIs import from there; `fetch_aws.py`'s existing 62 AWS tests
and t4's suite stay green with no fixture change (the check that it *was* a relocation and not
a change — the same evidence t2 used when the type constants moved to `_normalized.py`).

**Trigger, not a calendar:** do it the next time `fetch_aws.py` is legitimately edited. This is
the BL-070 precedent exactly — compose's duplicated `slug()` was left alone for the same reason
and for the same duration.

`Source: m2-cloudcost t4.`

### BL-079 — cloudcost holds no S3 storage rate for `ap-south-1`, where this account's buckets live (#TBD)
**Size:** XS · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/detect_optimization_signals.py`)

Filed 2026-08-02 from the m2-cloudcost **t4 live read**. Not a defect — the designed
omit-and-warn path firing in production — but it means the S3 half of the spike produces no
dollar figure on the one account it is pointed at.

**Observed.** All three buckets are in `ap-south-1`, which `S3_STANDARD_USD_PER_GB_MONTH` does
not carry, so all three `s3_no_lifecycle_policy` signals omitted `monthly_cost_estimate` and
warned by name:

```
s3 s3-b1-campustrack-net: no published Standard rate is held for ap-south-1, so its cost
estimate is omitted rather than taken from another region
```

That is the rule working: never a fallback to another region's rate. The nine `secret_unused`
signals were priced (flat charge), so the run still produced figures — $3.60/month against a
Secrets Manager line that t1 measured at $4.14 of a $4.99 bill.

**Done when:** an `ap-south-1` Standard rate is added **from a verified source with its
`as_of`**, or the table is dropped in favour of whatever BL-072's engine-backed integration
returns. Do **not** close this by copying another region's number — that is the exact failure
the omit path exists to prevent, and the table is deliberately partial rather than
optimistically complete.

**Batch with BL-072** if that milestone lands first: Cost Optimization Hub returns real,
account-specific figures and would retire the static table rather than extend it.

`Source: m2-cloudcost t4 live read.`

### BL-080 — `detect_optimization_signals` reports `partial` for intentional honesty, not only for a read gap (#TBD)
**Size:** S · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/detect_optimization_signals.py`)

Filed 2026-08-02 from the m2-cloudcost **t4** review (claude-ui N1, non-blocking).

**The observation.** The stdout `status` is `"partial" if (denied or warnings) else "ok"`. A
fully-granted run that merely declined to price something — an unrated region, bytes in an
unrated storage class — therefore reads as `partial`. On the live account **every** run will,
because every bucket is in `ap-south-1` (BL-079). A status field that is permanently `partial`
is a field readers learn to skip, which is the alarm-fatigue shape the strict-mode WARN
exemption in `CLAUDE.md` exists to name. `status` is informational here — not gating, not the
exit code — so this is cosmetic, not a defect.

**Why the review's two-way fix is not quite it.** N1 suggests reserving `partial` for `denied[]`
and letting figure-omission ride under `ok`. That would be right if `warnings[]` held only
intentional omissions — but it currently holds two different kinds:

- *intentional omission* — "no published Standard rate is held for ap-south-1", "GlacierStorage
  is excluded from the cost estimate". Nothing is unknown; a figure was declined on purpose.
- *a genuinely unknown fact* — "no NumberOfObjects datapoint published, so whether it is empty
  is unknown", "size and object count are unknown". Something the run wanted to know and does
  not.

Collapsing both under `ok` would hide the second kind, which is the same
absent-read-as-fine failure the `denied[]`/`warnings[]` split was introduced to prevent. So the
fix is a **three-way** split, not a two-way one: `denied[]` (refused), `warnings[]` (unknown
fact), and a new third bucket for priced-declined-on-purpose — with `status` keying on the first
two only.

**Done when:** the third category exists in the envelope, `status` reads `partial` for
`denied[] or warnings[]` and `ok` for omissions alone, the render section distinguishes the
third (it currently renders warnings under "Left unknown", which is the wrong heading for an
intentional omission), and a test asserts a run whose ONLY finding is an unrated region reports
`ok`.

**Batch with BL-081** — same file, same envelope, and both are t4 review tidy-ups.

`Source: m2-cloudcost t4 review N1.`

### BL-081 — `s3_no_lifecycle_policy` fires on an observably empty bucket (#TBD)
**Size:** XS · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/detect_optimization_signals.py`)

Filed 2026-08-02 from the m2-cloudcost **t4** review (claude-ui N2, non-blocking).

**The observation.** A bucket with no lifecycle policy and zero objects raises both
`s3_empty_bucket` and `s3_no_lifecycle_policy` (fixture `cc-empty` does exactly this). The
second is low-value noise: an empty bucket has nothing to expire or transition, so the missing
policy costs nothing today.

**The care needed when fixing it.** Suppress only on an **observed** zero — `objects == 0` read
from a real datapoint. An *absent* `NumberOfObjects` datapoint must NOT suppress, because absent
means unknown, and a bucket whose metric has not published looks identical to an empty one. That
is the same unknown-is-not-zero rule the empty-bucket signal itself already turns on
(`aws_cloudwatch_metrics_cc_unknown` is the existing control), so the fix must not quietly
invert it in the neighbouring branch — a suppression driven by `not metrics.get("objects")`
would do precisely that.

**Done when:** `s3_no_lifecycle_policy` is suppressed when and only when the object count was
observed to be 0; a test asserts an unknown-count bucket with no policy still raises it.

**Batch with BL-080.**

`Source: m2-cloudcost t4 review N2.`

### BL-082 — no end-to-end orchestrated run of the `CLOUDCOST_OPTIMIZATION=1` path (#TBD)
**Size:** S · **Priority:** low · **Section:** cloudcost (`cloudcost/agents/cloudcost_orchestrator.exs`, `../aetheris/scripts/sprint.sh`)

Filed 2026-08-02 from the m2-cloudcost **t4** review (claude-ui N3, non-blocking). The row the
note asked for: t4 flagged this as "no trigger yet", and a gap with no trigger is what a row is
for.

**What IS proven.** The prompt the orchestrator builds, both ways — byte-identical to t3's with
the gate unset (same md5, for both providers), exactly one extra step with it set; the raise when
the gate is set for a non-AWS provider; `detect_optimization_signals.py` end-to-end offline
through the stub; and `render_report.py --optimization-file` against the live signals file.

**What is NOT.** The LLM actually executing STEP 2b and threading the printed path into STEP 4's
`--optimization-file`. Every link is verified; the chain is not. That is the shape m6-docbuilder
promoted a learning about — cross-stage wiring defects pass the per-stage check and surface only
when the real pipeline runs.

**Why it was skipped:** the run needs live AWS credentials and an LLM call, and t4 is
non-gating. The risk is genuinely low (the threading is one placeholder substitution, identical
in form to the four the prompt already does) but it is not zero.

**Done when:** either a `cloudcost` sprint leg runs the orchestrator with
`CLOUDCOST_OPTIMIZATION=1` and asserts the rendered report contains the optimization section, or
an operator runs it once and the trajectory is recorded in the implementation notes. Sequence
after **BL-069** if the sprint route is chosen — that case is already known-red on its orphan
assertion, and adding a second assertion to a red case buries it.

`Source: m2-cloudcost t4 review N3.`

### BL-083 — Run list: classify the four unclassified use cases; provider in the cloudcost label (#TBD)
**Size:** S · **Priority:** medium · **Section:** aetheris-agents (`rig/`, `cloudcost/agents/`)

Filed 2026-08-03. **Scoped wider than the cloudcost symptom that surfaced it** — the open question
("why does payslip group but cloudcost not?") resolved on first read, and the answer showed the
class.

**Mechanism.** `RunList.tsx:133` `classifyRun(run.label)` matches the **label**, not the run_id,
against the hardcoded `USE_CASE_PREFIXES` list (`:118`). There is no `cloudcost` entry, so it falls
through to `Unclassified` (`:138`). Nothing about run_id prefixes is involved.

**The class, counted from the live store (`mix aetheris list --limit 200`), not inferred:**

| Label | Runs | Today |
|---|---|---|
| `Docbuilder Orchestrator` / `Context Builder` / `Context Orchestrator` | **54** | Unclassified |
| `Cloudcost Orchestrator` | 9 | Unclassified |
| `Capability Matrix -- Provenance` (legacy label; `cap-matrix:` siblings match) | 5 | Unclassified |
| `cap-matrix: *`, `Payslip *`, `Email *` | 49 | correct |

So cloudcost is **not** the main occupant of Unclassified — docbuilder is, by 6×. Fixing only
cloudcost leaves 59 runs misfiled and the next reader re-derives all of this. Also **two dead
entries**: `api-tenant` and `api-gateway` match nothing, because the api agents are labelled
`at1cmd` / `at1qry` / `cot1` / `cot1_stub`; and `eduloka` has an orchestrator but no prefix.

**Scope.** Add `cloudcost`, `docbuilder`, `eduloka`; fix or drop the two dead api entries (decide
against the real labels, not against the use-case directory names); handle the legacy
`Capability Matrix -- Provenance` label. Separately, `cloudcost_orchestrator.exs` sets a
provider-distinct `label` — `Cloudcost · AWS` / `Cloudcost · DigitalOcean`. Note the two halves
compose: `classifyRun` lowercases and does `startsWith`, so `"cloudcost · aws"` still matches a
`cloudcost` prefix — changing the label cannot break the grouping, but only in that direction.

**Done when:** no use case with a live orchestrator lands in Unclassified; the cloudcost rows name
their provider without the search filter; every remaining `USE_CASE_PREFIXES` entry matches at
least one real label (a prefix matching nothing is the dead-entry defect, re-armed).

### BL-083 — DONE 2026-08-04

Landed as a **label patch, not run_id re-keying** — reversing handoff §Corrections 3, which had
recorded the opposite as answered. The run_ids it rests on were verified at HEAD and the api ones
break it: `uc-api-t2-AeGOtw-at1cmd` / `uc-api-t2-tuquiQ-cot1`, where the first segment is `uc` (not
the use case, and zero run_ids start with `api`), the tenant/gateway discriminator is a **suffix**,
and the shared prefix embeds a milestone number that `t3` would invalidate. Full adjudication in
`docs/rig/milestones/bl-083-run-classifier-implementation-notes.md`.

Three of the row's own claims did not survive re-derivation and are corrected there: the docbuilder
"bare `Context Builder`" variants **do not exist** (all three labels start with `Docbuilder`, so one
prefix covers all 57); the legacy capability-matrix label has **14** runs, not 5, plus a missed
`Capability matrix generator`; and **eduloka has never produced a run** — it is covered because a
real agent *declares* the label, which is why "real label" was defined as declared ∪ observed.

**Result over 957 runs — Unclassified 693 → 565, 128 rescued:**
API/Gateway 0→15, API/Tenant 0→29, Cloudcost 0→12, Docbuilder 0→57, Capability Matrix 85→100;
Drive/Email/Payslip/Provenance unchanged.

`cloudcost_orchestrator.exs` now emits `Cloudcost · AWS` / `Cloudcost · DigitalOcean`, which still
groups as Cloudcost (`startsWith` on the lowercased label).

**Standing guard added** — `scripts/check_run_classifier.py` + `tests/test_run_classifier.py`
(15 tests, hermetic). It parses `USE_CASE_PREFIXES` out of `RunList.tsx` rather than duplicating it,
and fails on either rot direction: a prefix matching no known label, or a declared agent label
falling through. Mutation-checked both ways.

**Residual, conceded:** label-keying is safe for suffix appends (proven by the `· AWS` change) but
a change to a label's *leading* word unfiles its runs. That is what the guard watches.

**Not verified visually:** the run list renders via Tauri `invoke`, so grouping was confirmed by
computation over the same store, not by looking at Rig. The group headings are the one thing that
does not cover.

`Source: m2-cloudcost close-out, 2026-08-03; closed 2026-08-04.`

### BL-084 — Tools manifests for the four use cases that have none (#TBD)
**Size:** S · **Priority:** low-medium · **Section:** aetheris-agents (`cloudcost/`, `docbuilder/`, …)

Filed 2026-08-03. Cloudcost's six pipeline scripts show undeclared/amber in the Tools tree —
runnable but raw-args, no descriptions. Add `cloudcost/tools.json` declaring `fetch_aws`,
`fetch_do`, `detect_orphans`, `detect_optimization_signals`, `compose_report_data`,
`render_report` with descriptions (reuse the capability-matrix wording) and arg forms.
`_normalized.py` is an import-only shared module, not a CLI — describe-only or omit, never Run.

**Same adjacent-case as BL-083:** `tools.json` exists for payslip, drive, email, api and eduloka;
it is **absent for cloudcost, docbuilder, provenance and boxy-pipeline**. Cloudcost is one of four.
Do cloudcost first (its scripts are freshly documented), but file the others in the same sweep
rather than rediscovering the gap per use case.

**Sequence before BL-085, because it partly delivers it.** `env_deps` is *derived from the
manifests* — `tools.rs:594` walks every script's `env` array and the Settings tab renders any key
not in the static `AGENT_CONFIG_DEFS` as a dynamic config row (`AgentConfigTab.tsx:185`).
`api/tools.json` already declares 16 such keys, so the path is exercised, not theoretical.
Declaring `CLOUDCOST_AWS_*` in the manifest therefore produces the config rows **without** editing
`agentConfigDefs.ts` at all.

**Done when:** the six cloudcost scripts show without the amber badge and with structured arg
forms; descriptions match `capability-matrix.md`; the other three use cases are filed or done.

`Source: m2-cloudcost close-out, 2026-08-03.`

### BL-085 — Cloudcost credentials + per-launch provider selection in Rig (#TBD)
**Size:** M · **Priority:** medium · **Section:** aetheris-agents (`rig/`, `cloudcost/runbook.md`)

Filed 2026-08-03. Surface the read-only AWS key in Rig's Agent Config and let an operator launch
the cloudcost orchestrator from Rig. **This is the one row of the four with unresolved design** —
the other three are drop-in.

**Config surface — mostly free once BL-084 lands.** Declaring `CLOUDCOST_AWS_ACCESS_KEY_ID`,
`CLOUDCOST_AWS_SECRET_ACCESS_KEY` (masked), and optional `_REGION` / `_REGIONS` / `_SESSION_TOKEN`
in `cloudcost/tools.json` renders them as dynamic config rows already. A static `agentConfigDefs.ts`
group is then only worth adding for grouping/labels/masking polish — decide which, don't do both.

**Open question 1 — launch affordance.** How does an operator launch
`cloudcost_orchestrator.exs` from Rig: the meta-orchestrator prefill (`/orchestrator`, which adds
an LLM planning turn) or a direct control? Prefer the direct path if one exists; do not route a
four-stage deterministic pipeline through an LLM planner just because that is the existing door.

**Open question 2 — per-launch provider, and it has no home today.** `CLOUDCOST_PROVIDER` must be
selectable **per launch**, and agent config is single-valued and global. The nearest precedent
(`PAYSLIP_MONTH`, `PAYSLIP_START_STEP` — static defs an operator edits *between* runs) is exactly
the shape this row rejects. So either the launch control grows a parameter concept, or the
selection lives in the request the meta-orchestrator reads. **If the answer is "Rig needs a
launch-parameter concept", that is the trigger to peel this row into its own small milestone** —
it stops being a ticket at that point.

**D2 posture — decide and document, do not code.** A Rig-launched run injects the config env but
**not** the `env -u AWS_* AWS_SHARED_CREDENTIALS_FILE=/dev/null` hermetic prefix (Rig cannot set it
per-agent). That is **suspenders-only**, and the suspenders genuinely hold: the adapter's explicit
session refuses boto3's default chain by construction, proven live and offline by t1's poison
guard. One sharpening the belt-and-suspenders framing misses, found while scoping: `api/tools.json`
**already declares `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as env deps**, so Rig's own
config surface actively *invites* the operator to set the two variables the D2 belt exists to
strip. A Rig-launched cloudcost run is therefore not merely missing the belt — it may run with the
poison present. The guard still holds, but say so in `cloudcost/runbook.md` rather than leaving the
next reader to infer that "no belt" means "clean environment". Also: `agent-config.json` is
plaintext on disk — a read-only key there is the same trust level as the GitHub PAT already stored
there; a write key must never go in it.

**Done when:** with the credentials set, a Rig-launched AWS run authenticates with the read-only
key and produces its report; `CLOUDCOST_AWS_*` appears nowhere in the trajectory or `config_json`;
the operator can pick aws vs do per launch; the runbook records the posture above.

**Annotated 2026-08-14 (m6 t4) — the planner has never been told the key exists, so Open question
2 is open in a way the row does not yet say.** This row's answer to per-launch provider selection
is Rig's "Additional env vars" box, and the mechanism ships and works
(`orchestrate.rs:57-66`; `cloudcost/runbook.md` §Rig step 2). What was never wired is the *other*
end of the same door. `agents/orchestrator.exs`'s **Known params** block (`:65-70`) — the only
place the planner LLM is told which env keys it may emit — lists `PAYSLIP_MONTH` and
`PAYSLIP_EMPLOYEE_ID` and **has never mentioned any cloudcost key**, at any commit. Verified at
agents `97c61a0`. So the LLM standing between the operator and the agent cannot surface, confirm,
or default the provider, and `cloudcost_orchestrator.exs:58` defaults to `digitalocean` when the
key is absent. **Provider selection therefore depends entirely on an operator having read the
runbook before each launch** — a run requested as GitHub and launched without that knowledge
executes as DigitalOcean, produces a well-formed DigitalOcean report, and nothing in the plan
card, the run, or the artifact says the request was not honoured. That is a **Silent-wrong-answer**
(harness `CLAUDE.md`) sitting on this row's Open question 2, not on BL-094: BL-094 is the *direct,
non-LLM* door — the path that removes the planner — and closing it would leave this defect intact
for every launch that still goes through the planner. Recorded here, on the row that owns
per-launch provider selection.

**Also stale in this row's own Done-when, noted rather than edited:** *"the operator can pick aws
vs do per launch"* is itself a two-provider enumeration, written 2026-08-03 before Linode (m3) and
GitHub (m6). The criterion is right and its enumeration is short by two — the same defect m6 t4
repaired in `cloudcost/runbook.md` §Adding a provider. Left as written because rewriting a
Done-when is a disposition and this ticket files rather than disposes.

`Source: m2-cloudcost close-out, 2026-08-03.`

### BL-086 — Trajectory: label steps by their `run_command` stage (#TBD)
**Size:** S · **Priority:** medium · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-03. `TrajectoryView` shows a generic "Step N". For each step carrying a
`run_command` tool call whose first arg is a `.py`, derive `stage = basename(arg, ".py")` and
render it as the step badge — "Step 0 · fetch_aws", "Step 1 · detect_orphans". Pure frontend, no
harness or event change, retroactive on existing runs, and **generic**: every scripted pipeline
gets it, not just cloudcost. Steps with no script call — the orchestrator's final summary turn —
stay "Step N".

**Done when:** a cloudcost run labels its stages (`fetch_aws` → `detect_orphans` →
`compose_report_data` → `render_report`, plus `detect_optimization_signals` when
`CLOUDCOST_OPTIMIZATION=1`); a docbuilder run shows its stages; non-script steps render unchanged.

`Source: m2-cloudcost close-out, 2026-08-03.`

### BL-087 — `payslip/tools.json` omits a runnable CLI (#TBD)
**Size:** XS · **Priority:** low · **Section:** aetheris-agents (`payslip/`)

Filed 2026-08-03 by BL-084. `payslip/scripts/merge_employee_payslips.py` is a real CLI
(`argparse` at :48, `if __name__ == "__main__":` at :76) and is absent from
`payslip/tools.json`, which declares only `scripts/payslip_compute.py` and
`scripts/generate_employee_payslips.py`. So it renders in Rig with the amber badge, the
"not declared in tools.json" banner, and a raw-args box instead of a structured form.

**Found by an off-territory sweep, not by working payslip.** BL-084's new
`tests/test_tools_manifests.py` audits every manifest, not just the one it was written for;
this was the only pre-existing red across api/drive/eduloka/email/payslip. It is carried as
`xfail(strict=True)` on `test_no_undeclared_scripts[payslip]` **only** — payslip's parse,
declared-files and env-dep params are unmarked and green. `strict=True` means the marker must
be deleted in the same commit that fixes this, or the suite fails on the unexpected pass.

Not auto-fixed at BL-084 because payslip is outside that ticket's cloudcost scope, and a
manifest entry needs its arg forms read off `--help` rather than guessed.

**Done when:** the entry is declared with arg forms derived from
`python3 scripts/merge_employee_payslips.py --help`; the `xfail` marker in
`tests/test_tools_manifests.py` is removed in the same commit.

`Source: BL-084, 2026-08-03.`

### BL-088 — `ManifestScript.runnable`: mark a manifest entry describe-only (#TBD)
**Size:** S · **Priority:** low · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-03 by BL-084. A `tools.json` entry cannot say "this is not a CLI". The Run
button at `ToolDetail.tsx:175-186` renders for every script, declared or not, gated only on
empty required args, and `ManifestScript` (`tools.rs:29-46`) has no field to suppress it.

The live case is `cloudcost/scripts/_normalized.py`, an import-only shared module. BL-084's
row asked for it to be "describe-only, never Run"; only the describe half was deliverable, so
BL-084 declares it with `args: []` and a description saying it is import-only. Running it is
genuinely harmless there — no `__main__`, so `python3 scripts/_normalized.py` exits 0 with no
output — which is why this is low priority rather than a correctness bug. Omitting the entry
instead is strictly worse: the walker synthesises it as `undeclared` anyway
(`tools.rs:560-575`), so it stays amber *and* stays runnable.

Not unique to cloudcost: `docbuilder/scripts/_drive.py`, `_format.py`, `_table_html.py`,
eduloka's eight import-only modules and `drive/scripts/drive_utils.py` are the same class —
enumerate them when this lands rather than fixing the one that was noticed.

**Done when:** `runnable: Option<bool>` (serde default true) exists on `ManifestScript`,
mirrors into `src/hooks/types.ts`, gates the Run button, and is rejected server-side in
`tools_run_script` so the gate is not frontend-only; `p4-001-manifest-spec.md` documents it.

`Source: BL-084, 2026-08-03.`

### BL-089 — tools.json for the three use cases that still have none (#TBD)
**Size:** S · **Priority:** low-medium · **Section:** aetheris-agents (`docbuilder/`, `provenance/`, `boxy-pipeline/`)

Filed 2026-08-03 by BL-084 (Decision A). `tools.json` is absent for docbuilder, provenance and
boxy-pipeline; every runnable CLI in each renders amber with a raw-args box in Rig. BL-084 did
cloudcost only and carried these three as `xfail(strict=True)` in `tests/test_tools_manifests.py`
(`test_manifest_parses` + `test_no_undeclared_scripts`), so they cannot rot silently.

Declare each use case's runnable CLIs (arg forms off each script's `--help`, descriptions from
`capability-matrix.md`), import-only modules describe-only per BL-088. May land per-use-case or
together; each landing must delete that use case from `NO_MANIFEST_YET` in the suite in the same
commit, or the strict xfail fails on the unexpected pass.

`Source: BL-084, 2026-08-03.`

### BL-090 — capability-matrix stale: cloudcost omits detect_optimization_signals (#TBD)
**Size:** XS · **Priority:** low · **Section:** aetheris-agents (`docs/`, matrix generator)

Filed 2026-08-03 by BL-084. `docs/capability-matrix.md` §Cloudcost lists six scripts and its summary
reads `| cloudcost | 1 | 6 |`, but seven `.py` are on disk — `detect_optimization_signals.py` is
absent. Cross-checked against BL-084's serde script counts: every other use case's matrix count
matches disk (drive/payslip differ from their manifests only by import-only/undeclared scripts, as
expected); cloudcost is uniquely short, i.e. the script was added after the last matrix regen.

The matrix is GENERATED — fix by re-running the capability_matrix sprint case, not by hand-editing.
One reconciliation at regen: the generator will source detect_optimization_signals' cell from its
docstring, which differs from BL-084's code-derived manifest description (written from the signal
constants, deliberately more precise than the docstring). Either improve the script docstring to
match, or accept the manifest wording as canonical and let the cells differ. "descriptions match
capability-matrix.md" is not re-opened by this — BL-084 satisfied it 5-of-6 with the 6th documented.

**Second staleness in the same section, added 2026-08-04 by BL-083.** `docs/capability-matrix.md`
§Cloudcost still shows the agent Label as `Cloudcost Orchestrator`; BL-083 changed it to
`Cloudcost · #{provider_name}`, so the live values are `Cloudcost · AWS` / `Cloudcost ·
DigitalOcean`. Filed rather than hand-fixed for the reason this row already gives — the matrix is
generated — and noted here so the regen reconciles both cells in one pass instead of discovering
the second one afterwards.

`Source: BL-084, 2026-08-03; label drift appended by BL-083, 2026-08-04.`

### BL-090 — DONE 2026-08-05

Regenerated in `4d98ec2` (m3-cloudcost t3), merged `8dca843`. **Both** stale cells this row
accumulated reconcile in the one pass it asked for:

| cell | before | after | filed by |
|---|---|---|---|
| Agent Label | `Cloudcost Orchestrator` | `Cloudcost · {provider}` | BL-083, 2026-08-04 |
| Scripts | 6 listed, `detect_optimization_signals.py` absent | 8 listed | BL-084, 2026-08-03 |

Summary row `| cloudcost | 1 | 6 |` → `| 1 | 8 |`; totals `27 | 82` → `27 | 84`.

**Eight, not the seven §t3 predicted.** The "seven" figure is the scout's §A9 count, written
against `dc8c077` — six on the matrix plus `detect_optimization_signals.py` — and it predates
t1 adding `fetch_linode.py`. So the doc was the stale side of its own staleness ticket: t3
reported the count the regen produced and flagged the prediction rather than reconciling
down to it (`m3-milestone.md` rev 7 corrected §t3). This is the m3 learning about documents
that quote repo state, fired on the row whose subject *is* a document quoting repo state.

Regenerated by the §A9 ritual — the cloudcost section agent alone
(`cap-matrix-cloudcost-BEWzHw`), then `assemble_matrix.py` over all nine sections. Never a
full nine-agent regen (BL-068: `docs/.sections/` is gitignored, so a full re-run destroys the
eight sections it does not regenerate), never a hand-edit — the artifact is generated, which
is the reason this row exists rather than a one-line fix. The regen also rewrote the six
carried script descriptions from current docstrings; that is regen output, not a curation.

`Source: BL-084 (filed 2026-08-03), label drift appended by BL-083 (2026-08-04), closed by
m3-cloudcost t3 done-when 5, 2026-08-05.`

### BL-091 — exportConfig() drops every manifest-derived env key (#TBD)
**Size:** S · **Priority:** low-medium · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-03 by BL-084. `exportConfig()` (`rig/src/hooks/useAgentConfig.ts:33-41`) iterates
`AGENT_CONFIG_DEFS` only, so every dynamic env_deps key — api's 16, cloudcost's 6 — is editable and
persisted in agent-config but silently omitted from Export. Pre-existing (api already affected);
BL-084 surfaced it. Decide the masked-key policy deliberately when fixing: omitting secret keys from
export may be intended hygiene, but omitting the non-masked keys (region, access-key-id) is silent
data loss on config transfer.

`Source: BL-084, 2026-08-03.`

### BL-092 — tools.rs manifest-deserialization test coverage (#TBD)
**Size:** S · **Priority:** low · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-03 by BL-084. `tools.rs` has zero `#[cfg(test)]`. BL-084 proved cloudcost/tools.json
deserializes into `ToolsManifest` via a temporary test module, then discarded it (tools.rs is
byte-identical to HEAD). Make it permanent: a `#[cfg(test)]` module round-tripping every committed
manifest into `ToolsManifest` and asserting Ok plus the env_deps dedup walk. This is the only
standing offline guard against the pytest suite's transcription gap — a manifest that passes pytest
but fails serde is dropped to None with every script going amber and nothing saying why. Seed is in
`cloudcost/docs/bl-084-implementation-notes.md` §"What is proven offline."

`Source: BL-084, 2026-08-03.`

### BL-092 — DONE 2026-08-05

Landed `f28b817` (m3-cloudcost t2), merged `f552094`. A `#[cfg(test)] mod tests` at the end of
`rig/src-tauri/src/commands/tools.rs` — 157 insertions, 0 deletions, one hunk; the file is
byte-identical outside `cfg(test)`.

**Coverage is by walk, not by list.** `committed_manifests()` reads the agents root and takes
every `<use_case>/tools.json`, mirroring `tools_list_inventory`'s own exclusions, so a manifest
added later is guarded without editing the test. Four tests over that set:

- `every_committed_manifest_round_trips_into_tools_manifest` — the property the row exists for.
  `tools_list_inventory` does `serde_json::from_str(&raw).ok()`, so a schema violation is not an
  error but a `None`: the use case silently falls back to all-undeclared, every script amber and
  nothing saying why. Also re-serializes and re-parses, catching a field that deserializes only
  because serde defaulted it away.
- `a_manifest_missing_an_env_dep_field_is_rejected` — **the negative control.** Without it the
  round-trip has only ever been seen passing, so it is not yet a check. Drops `"masked"` from
  cloudcost's first `EnvDep` (a bool, so removal is a schema violation rather than a coercion),
  asserts the mutation applied, and asserts the mutant fails to deserialize.
- `discovery_finds_every_committed_manifest` — anti-vacuity for all of the above: a walk that
  silently returned nothing would pass a round-trip over zero manifests. Asserts the *set*
  (`api, cloudcost, drive, eduloka, email, payslip`), not a count, so adding a use case fails
  where the expectation lives instead of silently widening coverage.
- `env_deps_dedup_walk_keeps_the_first_occurrence_only` — the first-occurrence-wins dedup,
  anchored on `CLOUDCOST_AWS_ACCESS_KEY_ID`, which genuinely repeats across `fetch_aws` and
  `detect_optimization_signals`; the anchor's repetition is itself asserted, so the dedup is
  doing work rather than passing over an already-unique list. Also asserts
  `CLOUDCOST_LINODE_TOKEN` is masked in the Rig config surface.

This is the standing offline guard `tests/test_tools_manifests.py` structurally cannot be: the
pytest suite transcribes these structs, only this test runs serde. Seed was
`cloudcost/docs/bl-084-implementation-notes.md` §"What is proven offline", as the row directed.

`Source: BL-084 (filed 2026-08-03), closed by m3-cloudcost t2 done-when 5, 2026-08-05.`

### BL-093 — runbook drift: PAYSLIP_MONTH described as non-persistent (#TBD)
**Size:** XS · **Priority:** low · **Section:** aetheris-agents (`rig/docs/`)

Filed 2026-08-04 by BL-085. `rig/docs/runbook.md:316-317` states "`PAYSLIP_MONTH` is injected
per-invocation by the orchestrator — it is not a persistent Agent Config setting." That is true of
the meta-orchestrator's `params` mechanism (`agents/orchestrator.exs:272-273`, restored `:295-298`)
and **false** of `rig/src/components/modules/settings/agentConfigDefs.ts:38`, which renders it as a
persistent, savable, exported row alongside `PAYSLIP_START_STEP` and `PAYSLIP_EMPLOYEE_ID`. Both
realities ship; the runbook denies one of them.

Fix by describing both mechanisms, or by moving the three payslip rows out of the static defs —
decide deliberately. Note the second option is the same question BL-085 answered for cloudcost
(per-launch values belong in `extra_env`, not in global config), so this row is the payslip half of
that adjudication and should not be closed by editing the sentence alone without deciding which
mechanism is intended.

`Source: BL-085, 2026-08-04.`

### BL-095 — plan-card renders secret config values in clear (#TBD)
**Size:** S · **Priority:** medium · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-04 by BL-085. `StepCard` builds `` `${k}: ${configValues[k]}` `` for every
`STEP_CONFIG_HINTS` key that is set and renders the result as visible text
(`rig/src/components/modules/orchestrator/OrchestratorView.tsx:83-86`, rendered `:105-111`;
`configValues` is the persisted agent config, `:130`). The `payslip/agents/payslip_pipeline.exs`
hint list includes `SMTP_PASSWORD` and `GOOGLE_SERVICE_ACCOUNT` (`:20-30`), so an approved payslip
plan card displays those secrets in clear today.

Fix by consulting the same `masked` flag the config tab already uses (`AgentConfigTab.tsx:41-61`),
or by showing set/unset status only — the `ToolDetail.tsx:83-101` "Required config" dots are the
existing pattern for exactly this and render no values.

Found while adjudicating BL-085's STEP_CONFIG_HINTS question; it is the reason no cloudcost entry
was added there (a cloudcost entry would have printed `CLOUDCOST_AWS_SECRET_ACCESS_KEY` and
`CLOUDCOST_DO_TOKEN` in clear). Pre-existing — BL-085 surfaced it, payslip owns the live exposure.

`Source: BL-085, 2026-08-04.`

### BL-095 — DONE 2026-08-04

Landed `63ea4b5`, merged `5fe1903`. **Deny by default, not mask-if-flagged**: `StepCard` renders a
hint value only on an explicit `masked === false`, so masked keys, the two hint keys carrying no
metadata at all (`DOCBUILDER_CONTEXT_FILE`, `DOCBUILDER_REQUEST`), and any future undeclared key
show `set` rather than their value.

**Enumeration falsified both candidate rules.** Of the 15 hint keys exactly one is `masked: true`
(`SMTP_PASSWORD`) — and `GOOGLE_SERVICE_ACCOUNT`, the other key this row names as leaked, was
explicitly `masked: false`. Mask-if-flagged would have left it in clear; so would a
"show if `masked === false`" rule. Resolved by fixing the metadata rather than special-casing the
rule: it is now `masked: true`, being a credential-*file* locator. A plan-card-only secrecy list
was rejected — duplicated secrecy metadata is a drift class this repo already pays for.

11 of 15 keys still render their values, so `PAYSLIP_MONTH: 2026-04` survives as plan-review
signal. Predicate proven against the real `AGENT_CONFIG_DEFS` with **two** anti-vacuity arms,
because the obvious cheat is hiding everything. Live: the card reads `set` for both secrets and
Settings dots the service-account path.

`Source: BL-085 (filed), closed 2026-08-04.`

### BL-096 — `fetch_aws.py` exceeds the 60 s `run_command` default on every AWS run (#TBD)
**Size:** XS · **Priority:** medium · **Section:** aetheris-agents (`cloudcost/`)

Filed 2026-08-04 by BL-085, found while diagnosing a Rig-launched run reported as "timed out".
`cloudcost/agents/cloudcost_orchestrator.exs` mentions `timeout` **nowhere**, so STEP 1's
`run_command` uses the exec server's 60 000 ms default
(`../aetheris/native/aetheris_exec_server/src/main.rs:472`, documented `:127`).
`fetch_aws.py` takes **63–67 s** against the real bill, so the first call always times out.

**Chronic, not a regression — 5 of 5 AWS runs in the DB:**

| run | fetch_aws calls | timeouts | tool durations (ms) |
|---|---|---|---|
| `cloudcost-orch-aws--ez4vQ` (Rig, 2026-08-04) | 2 | 1 | 60000, 66991, 49, 47, 134 |
| `cloudcost-orch-aws-oFbapA` (m2 milestone run, `m2-milestone.md:4`) | 2 | 1 | 60000, 66136, 43, 42, 129 |
| `cloudcost-orch-aws-SdBOkw` | 2 | 1 | 60000, 66454, 44, 42, 172 |
| `cloudcost-orch-aws-XWjM8A` | 2 | 1 | 60000, 63818, 42, 45, 121 |
| `cloudcost-orch-aws-cwB8KA` | 2 | 1 | 60000, 63352, 38, 45, 119 |

Every run recovers: the LLM retries the identical command with `timeout_ms: 300000` and succeeds.
That recovery is why this went unnoticed through all of m2 — including the milestone's own cited
evidence run.

**This is a determinism-contract item, not a cosmetic one.** The contract's §1 opens *"The harness
is deterministic; the model is not"* (`../aetheris/docs/aetheris/determinism-contract.md:31`,
manifest-tracked as `aetheris--determinism-contract.md`). Whether a four-stage deterministic
pipeline **completes** is a harness-side property, and today it is not one: STEP 1 always fails, and
the run only finishes because the model elects to retry with a larger `timeout_ms`. Nothing
instructs that retry — not the agent file, not the exec server, not the tool description. It has
held 5/5, but only under `claude-haiku-4-5-20251001`; a model swap, a temperature change, or a
differently-worded plan converts a working pipeline into a failed run with no code change anywhere.
The LLM is on the success path for a question it should never have been asked.

It also inverts *scripts do, agents decide* in its purest form: the run duration of `fetch_aws.py`
is a fixed, measurable property of the script, rediscovered by an LLM at runtime, once per run,
forever. And it burns a guaranteed-wasted 60 s — ~45 % of a 2 m 18 s run — to rediscover it.

**Fix — instruct the timeout so the model is off the success path.** Declare an explicit
`timeout_ms` on the `fetch_aws` step in `cloudcost/agents/cloudcost_orchestrator.exs`
(300 000 matches what the model already converges on), or raise the exec-server default for that
call. Either way completion becomes deterministic and the retry stops being a lucky behaviour. The
other three stages run in 38–172 ms and need nothing. Check whether the DO path carries the same
latent gap at a different threshold — `fetch_do.py` currently completes inside the default, so the
gap there is unproven, not absent (**Absent is unknown, not zero**).

**Done when:** an AWS run shows one `fetch_aws` `tool_called` and zero timeouts in its trajectory;
the timeout value is declared in the agent file rather than chosen at runtime; and the
determinism-contract cross-reference is recorded when the fix lands.

### BL-096 — DONE 2026-08-04

Fixed in `32933d8`: `fetch_timeout_ms = 300_000` declared on STEP 1 of
`cloudcost/agents/cloudcost_orchestrator.exs`. Exec-server default untouched.

Live acceptance — run `cloudcost-orch-aws-3KU2NQ`, status `done`, report produced:

| check | before (`--ez4vQ`) | after (`3KU2NQ`) |
|---|---|---|
| `fetch_aws` `tool_called` | 2 | **1** |
| timeout events | 1 | **0** |
| `timeout_ms` on the **first** call | absent (defaulted to 60 000) | **300000** |
| tool durations (ms) | 60000, 66991, 49, 47, 134 | **63882, 45, 47, 115** |
| wall clock | 2 m 18 s | **1 m 18 s** |

The first call now carries the declared value and completes in 63.9 s — inside the measured
63–67 s band, and no longer a retry. The third row is the load-bearing one: without it a run that
merely finished fast would read as a passing fix.

Non-leak re-checked under the settled BL-085 criterion: all 20 stored agent-config values with
length ≥ 8 grepped against this run's trajectory and `config_json` — zero secret hits.
The only value matches are non-secrets (`AETHERIS_MODEL`, `AETHERIS_PROVIDER`,
`CLOUDCOST_AWS_REGION`), `RunConfig.env` is `{}`, and both D2 guard warnings fired, so the run was
in the poisoned-but-guarded posture the criterion expects.

**Still open, deliberately:** a prompt declaration *instructs* the timeout, it does not
structurally remove the model from the success path. `pre_tools`
(`../aetheris/lib/aetheris/run_config.ex:44-47`) is the only mechanism that would; not taken, for
the three reasons in `cloudcost/docs/bl-096-implementation-notes.md`. File a follow-up if
prompt-adherence ever proves insufficient.

`Source: BL-085, 2026-08-04 (diagnosing cloudcost-orch-aws--ez4vQ); closed same day by
cloudcost-orch-aws-3KU2NQ.`

### BL-097 — Orchestrator: selecting a Recent prompt covers Run and the env disclosure (#TBD)
**Size:** XS · **Priority:** medium · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-04. On the Orchestrator idle view, clicking a **Recent** entry renders a card over the
Run button and the "Additional env vars" disclosure. The screen is unusable — env cannot be set, no
other prompt can be picked, the run cannot be started — until you navigate away and back.

**Mechanism (one line).** The overlaying element is the *filter-suggestions* dropdown, not the
Recent list: it is absolutely positioned (`absolute left-0 right-0 top-full mt-1 z-10`,
`OrchestratorView.tsx:170-171`) inside the `relative` wrapper that holds only the textarea (`:159`),
so it paints over everything below — the env disclosure (`:186-239`) and Run (`:241-246`). Its
visibility is derived **purely** from `suggestions.length > 0` (`:169`), and `suggestions` is
`history.filter(h => h.toLowerCase().includes(request.toLowerCase()))` (`:133-135`). Selecting a
Recent entry calls `setRequest(h)` (`:257`), after which `h` trivially contains itself — so the
dropdown opens and **can never close**, because the condition that opens it is now permanently true.
Navigating away "fixes" it only by unmounting the component and resetting `request`.

The Recent list itself is innocent and correctly hides once the box is populated (`:247`, gated on
an empty request).

**Wider than the reported repro.** The same permanent overlay appears whenever *typed* text
substring-matches any stored history entry — Recent selection is just the reliable way to reach it,
since it guarantees an exact self-match. There is no blur, Escape, or selection dismissal anywhere.

**Minimal fix (this row).** Give the dropdown an explicit open flag instead of deriving visibility
from the filter result: opened by typing, closed by selection, Escape, and blur. No relayout, no
relocation, no change to the `extra_env` panel or `ParamsStrip`.

**Done when:** selecting a Recent entry populates the request box and dismisses cleanly; Run and the
env disclosure stay clickable; a second selection works inline with no click-away; `bun run lint`
and `bun run build` green.

**Follow-up, deliberately NOT in scope here:** move Recent into a scrollable right-side panel. That
is a UX enhancement — it would also make Recent reachable while the box is populated, which the
current design intentionally does not do — and it should be decided on its own merits, not folded
into an unbreak.

`Source: BL-097, 2026-08-04 (reported from the Rig UI during the cloudcost batch).`

---

## Milestones (L — issue docs first, per repo convention)

### BL-007 — Replay / fork from step (Rig p9 candidate) (#48)
**Size:** L · **Priority:** medium

Feasibility confirmed (report Gap C + §3.1): trajectory files store full
untruncated prompts (`meta.system_prompt`/`user_prompt`) and complete
tool-call/tool-result payloads, so the conversation at step N is
mechanically reconstructable for completed runs — `run_checkpoints` is
only needed for live ones. No recording changes required.

Scope sketch for the milestone docs:
- ~~Harness: `Aetheris.fork_run(run_id, step)` — rebuild messages up to
  step N from the trajectory, start a new run with provenance back-link
  (consider reusing `agent_trees` for the parent/child relation).~~
  **Already built — struck 2026-07-17, see the annotation below.**
- ~~Rig: one Tauri command + a "Fork from here" affordance on a step group
  in TrajectoryView. *(Verified absent — this is the real work.)*~~
  **Built — struck 2026-07-20.** Shipped exactly as sketched: the `fork_run`
  Tauri command (t3) and a per-step "Fork from here" affordance with a
  provenance banner in `TrajectoryView` (t4, `6dd2d55`).
- Decide divergence semantics up front: forked run gets a fresh run_id
  and records normally; original is never mutated.
- New event types or config fields → event.ex/specs §6 in the same
  commit (drift_check enforces).

> **Verified state 2026-07-17 (BL-022's source check — this sketch was stale).**
> The harness half of the sketch describes work that already shipped:
>
> | Claimed as work | Verified state |
> |---|---|
> | `Aetheris.fork_run(run_id, step)` | **exists** — `lib/aetheris.ex:73` |
> | "rebuild messages up to step N" | **exists** — `Fork.from_step/3`, `lib/aetheris/execution/fork.ex`, since 2026-05-17 |
> | "provenance back-link" | **exists** — `fork_from` / `fork_step` are first-class `RunConfig` fields (`run_config.ex:82,196`), set at `fork.ex:119`, and **persisted into the trajectory's `meta`** by `maybe_add_fork_meta` (`agent/server.ex:717-720`). Shipped as a direct field link, not via `agent_trees` — the sketch's parenthetical was a suggestion, and a simpler design won. |
> | — | `:fork` is first-class in the mode union (`run_config.ex:115`); CLI `cli/commands/fork.ex`; tests in `execution/fork_test.exs` and `cli/commands/fork_test.exs` |
>
> ~~**Verified absent:** the Rig side — no fork command in `rig/src-tauri/src/*.rs`, no
> frontend references, nothing in `specs.md` §4.~~ **Closed 2026-07-20:** all three
> now exist — `fork_run` in `rig/src-tauri/src/commands/fork.rs:34`, the
> `useFork`/`TrajectoryView` frontend path, and the `specs.md` §4 command row.
>
> Not re-scoped here; that is the planning session's job. Noting only that the shape
> has changed: provenance, determinism contract, and Rig UX **on top of an existing
> core**, rather than a from-scratch build.
>
> **Milestone scoping starts from source, not this sketch.**

**Done when:** milestone README + issue docs exist; implementation gated
on them, per the p3 pattern (docs → mock/real split if useful → UI).

---

### BL-008 — Skills auto-extraction + Rig skills view (compounding) (#49)
**Size:** L · **Priority:** medium-low

The "compounding/dreaming" idea from the Burr HN thread, grounded in what
exists: `skills` table schema-complete (`store.ex:817`), write path live
(`insert_skill`, `store.ex:132/619`), public API `Aetheris.extract_skill`
(`lib/aetheris.ex:111`) — but nothing calls it automatically and nothing
reads the table. Operationally empty.

Scope sketch:
- Harness: post-run hook (opt-in via RunConfig flag) that calls
  `extract_skill` for successful runs matching criteria (e.g. ≥N steps,
  `reason: agent_finished`); populate `source_run_ids_json`.
- Dedup/quality gate before insert (don't accumulate near-identical
  skills from repeated sprint runs).
- Rig: read-only Skills section under Harness (one command, one view —
  follow the harness.rs / RunList.tsx pattern per runbook's "Adding a
  new module" steps).
- Relation to `api/tenant/scripts/extract_skill_hints.py` (separate,
  domain-specific): document the distinction or unify deliberately.
- Schema/command/doc changes → drift_check in the same commit.

**Done when:** milestone docs exist; a normal sprint run leaves at least
one skill row behind and Rig can show it.

### BL-094 — A direct, non-LLM launch door for config-style orchestrators (#TBD)
**Size:** M/L · **Priority:** medium · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-04, peeled off BL-085 by its own pre-agreed trigger. BL-085 asked whether per-launch
provider selection needed a new Rig launch-parameter concept; it does not — `extra_env` already
exists, ships, and is operator-editable. What is missing is a **direct (non-LLM) door**, and BL-085
shipped its launch recipe on the LLM planner as an explicit interim. This row is that door.

**The blocking correctness defect — fix this first, it is not cosmetic.**
`cloudcost/agents/cloudcost_orchestrator.exs` is a pure `%Aetheris.RunConfig{}` config file
(`:238-256`; no `Aetheris.start_run`, no protocol emission), while `orchestrate_start`'s
non-Python branch spawns plain `mix run` (`rig/src-tauri/src/commands/orchestrate.rs:46-49`).
`mix run` on a config file **evaluates the struct and discards it** — exit 0, nothing on stdout, so
`orchestrate_poll` reports `done: true` with zero messages and no run is ever created. That is a
well-formed success over a gap (**Silent-wrong-answer**, harness `CLAUDE.md`). Only
`mix aetheris run` → `RunHelpers.load_agent_file/1`
(`../aetheris/lib/aetheris/cli/commands/run_helpers.ex:356-368`, which pattern-matches
`%RunConfig{}`/`%OrbConfig{}` and errors on anything else) turns that value into a run.

**Code-vs-intended, not mere doc drift.** `docs/rig/specs.md:307-309` and
`rig/docs/milestones/p9/t4-implementation-notes.md:11-15` both already describe the branch as
`mix aetheris run` — i.e. the docs describe the behaviour the code lacks.
`docs/rig/architecture.md:123` correctly documents `mix run` for the planner path. So the docs are
not uniformly wrong; they disagree with each other because two different paths are being described.

**Flipping the branch globally is unsafe — enumerate before fixing.** `agents/orchestrator.exs` is
a *driver* `.exs`: it calls `Aetheris.start_run` itself (`:287-289`) and emits the newline-delimited
JSON protocol (`:301-311`), which is exactly what `mix run` must do for it. Driver and config `.exs`
files therefore need **distinct paths**; the fix is a discriminator, not a one-line swap. Enumerate
every `.exs` reachable through this branch before choosing the discriminator (return-value shape vs.
a manifest flag vs. a directory convention).

**Also in scope:**
- A UI that supplies `script_path`. The parameter exists (`orchestrate.rs:14`, default `:25`) but no
  operator-facing control sets it; the only non-LLM caller hardcodes a module constant
  (`rig/src/hooks/useDocbuilder.ts:4,19`).
- The Capability-Matrix Run button discards the one thing it knows — `handleLaunch` forwards only
  `agent.label` as textarea prefill and drops `agent.file`
  (`rig/src/components/modules/harness/CapabilityMatrixView.tsx:123-125`), forcing the planner LLM
  to re-derive a path the UI already had.
- The latent unused `RunConfig.env` hook: declared at `../aetheris/lib/aetheris/run_config.ex:81`
  (typespec `:195`) with **no consumer in `lib/`**. Confirmed empirically at BL-085 — a live run's
  `config_json` carries `"env": {}`. Decide whether the direct door populates it or it is removed;
  leaving an unimplemented per-run env field beside a working one invites the wrong call site.

**Done when:** an operator can launch a named config-style orchestrator from Rig without an LLM
planning turn; the driver-vs-config discriminator is explicit and tested (including the negative —
a config file through the wrong path must fail loudly, not exit 0); `specs.md`, `architecture.md`
and the p9 t4 notes agree with the code; cloudcost is the first consumer and its runbook §Rig loses
the "interim" caveat.

`Source: BL-085 scout, 2026-08-04 (peel-off trigger fired on the direct-door half only).`

---

## Drift apparatus (optional hardening)

### BL-009 — Promote sprint drift_check to `--strict` (#50)
**Size:** S · **Priority:** after BL-001

Zero standing WARNs was achieved (f2/provenance command tables added).
Flip the sprint.sh case to `drift_check.py --strict` so new WARNs fail the
sprint instead of accumulating into the next alarm-fatigue cycle.

**`project_knowledge` staleness exemption (decision 2026-07-15).** Under
`--strict`, manifest-*staleness* WARNs are reported but do **not** fail —
every doc commit re-stales the manifest until the next export, so mid-cycle
staleness is expected truth between export boundaries, not regression. The
invariant becomes **"zero *unexplained* WARNs"**, not "zero WARNs".
Structural manifest problems (missing manifest, unknown repo, git failure)
are **not** exempt and still fail. Land the promoted standing rule in
CLAUDE.md alongside: *ticket text quoting repo state cites the commit it was
verified against; divergence is a deviation to note, never silently follow*
(source: BL-001, BL-015, BL-002).

**Done when:** sprint runs `--strict` and passes; CLAUDE.md doc-sync
section documents strict mode, the exemption + rationale, and the standing
rule.

**Depends on:** BL-001 (#42)

**Status:** Done 2026-07-15. `drift_check.py` `--strict` exempts
`project_knowledge` staleness via a `strict_exempt` flag on `record`
(only the staleness WARN at the manifest-comparison site; structural pk
WARNs still promote to FAIL). `sprint.sh` drift case flipped to `--strict`.
CLAUDE.md doc-sync section updated. Exemption isolation verified: staleness
WARN → exit 0; a milestone_status WARN → `--strict` exit 1.

---

### BL-041 — Manifest-staleness done-checks are vacuous pre-commit; `drift_check` reads committed state only (#TBD)
**Size:** S · **Priority:** medium

Surfaced by BL-034's own verification (fe8298c, 2026-07-22), and caught by the executing
session as a Silent-wrong-answer in its own gate order — recorded here because a deferred
finding gets a row, not packet prose.

`check_project_knowledge` (check 8) computes each row's "actual" hash via
`_git_head_hash` → `git log -1 --format=%h -- <path>` (`scripts/drift_check.py:623-628`),
which reads **committed** history. A working-tree (uncommitted) edit to a manifest-tracked
doc creates no commit, so it is **invisible to check 8**: a `drift_check --strict` run
*before* the edit is committed reports the manifest clean whether or not the edit was
made. At BL-034 the pre-commit `--strict` run showed 0 WARN; the predicted
`backlog-2026-06.md` staleness WARN only materialized after fe8298c.

**Class: Silent-wrong-answer, in the verification order rather than the checker.** A
pre-commit gate on a manifest-staleness question passes identically in the broken and
fixed worlds — it looks like confirmation but exercises nothing about the edit. Ask what
the gate would show if the staleness were real: identical → it verifies nothing.

**Two dispositions (decide before implementing):**

- **(a) Convention, doc-only (cheap, do now).** Encode in the CLAUDE.md doc-sync section
  (and the export/handoff conventions): *any done-check that turns on manifest staleness
  runs post-commit; a pre-commit drift_check on a tracked-file edit is a vacuous PASS.*
  One rule, no tooling change.
- **(b) Tooling guard (optional hardening).** `drift_check` emits a WARN (or INFO) when a
  manifest-tracked path has uncommitted working-tree modifications (`git status
  --porcelain -- <path>`), so the gap is visible in the tool instead of relying on gate
  discipline. This closes the manifest-blind direction from the *other* side — the header
  already warns the check cannot see an upload without a regen; this is the same blindness
  to an uncommitted edit. Reuses the `?`/INFO-vs-WARN split the checker already has.

**§7 learning candidate.** The Silent-wrong-answer entry gains a verification-ordering
instance. Below the ≥2-ticket threshold on its own — promote when a second instance lands,
or by explicit human ratification, per §7. Recorded here as the first instance so the
recurrence is countable.

---

### Worked instance — BL-025, 2026-07-23 (second instance; disposition (b) now warranted)

BL-025 edited **three** manifest-tracked docs (`docs/backlog-2026-06.md`,
`../aetheris/docs/aetheris/runbook.md`,
`../aetheris/docs/aetheris/determinism-contract.md`). The same gate, run either side of the
commit boundary:

```
pre-commit   (working tree):   7 PASS  0 FAIL  1 WARN   backlog stale
post-commit  (8021a59/00ddd34): 7 PASS  0 FAIL  3 WARN   + runbook, + determinism-contract
```

All three are the exempt staleness class and both runs exit 0, so nothing was *wrong* — but
the pre-commit number was **understated by two**, and it was the number that went into the
review packet's done-check section as the cross-repo gate result.

**Why this instance is decisive for the disposition choice.** The executing session had
already read this row, and *flagged the vacuity in the packet from this row's own text* —
naming BL-041, stating that the pre-commit reading was vacuous in both directions and that
the hash would move after commit. It then reported "1 WARN" anyway. So disposition **(a)**,
the doc-only "run it post-commit" convention, was tested under the most favourable possible
conditions — the rule was known, cited, and consciously applied by the person holding it —
and still did not produce the right number. Discipline did not surface the gap; only the
commit did.

That moves **(b)** from "optional hardening" to warranted. A rule that fails while its own
author is quoting it is not a rule problem to be solved with better wording; the checker has
to say it. Recommended: implement (b), and keep (a) as the human-facing companion rather
than the primary defence.

**Class, in its own right.** "1 WARN" was well-formed, authoritative, and wrong by two —
Silent-wrong-answer in the summary-headline carrier, not merely in the verification order.
It would have looked identical had the run concealed ten stale docs instead of two.

**§7 status: second instance, now countable at 2** (BL-034 fe8298c, BL-025 8021a59/00ddd34),
same class and same verification-ordering form. That clears the ≥2 bar on its face; promotion
wording is still a milestone-boundary act with human ratification, per §7 — recorded here, not
self-promoted.

**Done when:** the post-commit ordering rule is recorded (disposition a), and the tooling
guard (disposition b) is either implemented in the `--strict` run with a
`tests/test_drift_check.py` case both directions, or explicitly declined on this row with
a reason.

`Source: BL-034 review packet flagged observation, fe8298c, 2026-07-22; worked instance
BL-025, 8021a59 + 00ddd34, 2026-07-23.`

---

### BL-041 — DONE 2026-07-25 (both dispositions)

**(a) Convention — `1013a95`.** The post-commit ordering rule is in `CLAUDE.md`'s doc-sync
section: a `drift_check --strict` before committing a manifest-tracked edit is vacuous;
run it after the commit and *name* the exempt `project_knowledge` staleness WARNs rather
than chasing them. Kept as the human-facing companion, not the primary defence.

**(b) Tooling guard — `11675cc`.** `_git_is_dirty` runs `git status --porcelain -- <path>`
per manifest row **in that row's owning repo** — the harness rows live in the sibling
`../aetheris` checkout, and porcelain against `REPO_ROOT` would report every one of them
clean, which is the same blindness one layer down. A dirty tracked path gets a per-path
**strict-exempt WARN** naming that check 8 compares committed history, so its staleness
reading for that path is vacuous, and to re-run after committing. Structural arms (missing
manifest, unknown repo, git failure — now including a `git status` failure) stay
**non-exempt** and still FAIL under `--strict`.

The closing PASS is suppressed while any tracked path is dirty. "N manifest entries all
match git HEAD" is a well-formed, authoritative answer to a question the run cannot yet
answer — the Silent-wrong-answer carrier this row was filed against, and it would have
survived the guard otherwise.

**The two signals are complementary across the commit boundary**, which is what closes the
gap discipline could not. For a path whose manifest entry is *fresh at the export*: pre-commit
only the uncommitted WARN can fire and the staleness WARN cannot, because the committed hash
still matches; post-commit the uncommitted signal clears and the real staleness WARN takes its
place. They are not mutually exclusive in general — a path already stale from an earlier
commit in the same cycle fires **both** while it is dirty (observed on this ticket's own r1
edit to this file, stale from `de46ac0` and uncommitted at once). That compound state is
correct and is the point: the uncommitted WARN says the staleness reading is not final, not
that there is no staleness. Both are strict-exempt, both exit 0.

**Self-exercised by its own landing.** This row's DONE edit is to `docs/backlog-2026-06.md`,
itself manifest-tracked, so the ticket ran the boundary it describes: while the edit was
uncommitted the new guard fired for that path and the staleness WARN could not; after the
commit the guard cleared and the exempt staleness WARN took its place. Both `--strict` runs
exit 0, and both are recorded verbatim in the review packet and in the implementation notes.

**§7 status.** The Silent-wrong-answer verification-ordering instance stands at 2 (BL-034
`fe8298c`, BL-025 `8021a59`/`00ddd34`) and was promoted as disposition (a) at `1013a95`.
No new promotion is claimed here; (b) is the mechanical enforcement of the rule already
promoted.

**r1 — review F1 folded, `0d5127b`.** The closing PASS was suppressed for `stale` and
`uncommitted` rows but **not** for rows that failed *structurally* (unknown repo, `git log`
failure, and the new `git status` failure), so a skipped row could sit beside
"`N` manifest entries all match git HEAD" — a count including rows never checked. Pre-existing
and `--strict`-safe (structural WARNs promote to FAIL), but it is this ticket's own
Silent-wrong-answer class one arm over, in the function already being edited, so it was folded
rather than filed. `check_project_knowledge` now tracks `structural` alongside the other two and
gates the PASS on all three; with the gate in place `len(rows)` is accurate wherever the PASS
prints, so the count needed no narrowing. Two tests, one per arm — `git log` failure, and the
unknown-repo arm which `continue`s before either guard. Mutation-checked: without the fold both
go red, and the run prints the contradictory pair the finding describes.
Review: `docs/reviews/bl-041b-bl-036-review.md`.

`Source: 1013a95 (a), 11675cc (b), 2026-07-25. Notes:
docs/rig/milestones/bl-041a-promotion-implementation-notes.md,
docs/rig/milestones/bl-041b-bl-036-drift-check-guards-implementation-notes.md.`

---

### BL-046 — Tool-result payload key is a convention, not a contract: `"output"` vs `"result"` (#TBD)
**Size:** S · **Priority:** low · **Section:** Harness (aetheris/)

Three tickets have now fixed the *same root cause* on the read side, one reader at a time:

| Ticket | Reader fixed | Failure shape it produced |
|---|---|---|
| BL-028 (`9b2b102`) | `Fork.event_to_messages/1` — `Map.get(payload, "output", "")` | **Silent empty** tool messages; fork proceeds from a wrong transcript |
| BL-025 | `Verifier.serve_step/1` (new path) | — (written correctly from the start) |
| BL-027 (folded into BL-025) | `Verifier.verify_step/2` — `Map.fetch!(payload, "output")` | **Crash**; verify dies on any failed-tool trajectory |

The writers remain unreconciled. `Loop` emits `:tool_result` payloads under **`"output"`**
for worker and MCP dispatch, **`"result"`** for in-process tools, and **`"result"` +
`"is_error"`** for every tool error regardless of dispatch route (`record_tool_error/7`).
Nothing declares this; each new reader must rediscover it, and the two failure shapes above
are what rediscovery costs. A fourth reader will be written eventually.

Note the two fixes differ in a way worth preserving: BL-028's read-side fallback also
normalizes (nil → `""`, non-binary → JSON) per contract §2's string invariant; BL-025's does
not, because verify must reflect the record verbatim rather than improve on it. So "one
shared helper" is not automatically the right answer — the *convention* needs declaring even
if the readers stay separate.

**Done when:** the `:tool_result` payload contract is stated in one place (a `@type` plus
docstring on the writer side, or a documented accessor), the existing readers are pointed at
it, and adding a writer that invents a third key is caught — by a test or by there being
only one way to write the payload. Decide explicitly whether the readers share code or only
share the convention.

`Source: BL-028 (2026-07-21), BL-027/BL-025 (2026-07-23) — same root cause, third reader.`

---

### BL-042 — Capability-shaped containment for the verify worker (`CLONE_NEWNET`) (#TBD)
**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)

BL-025 classifies `run_command` `:contained` and record-and-serves only the purpose-network
tools (`http_call`, MCP). But the verify sandbox confines filesystem only — no network
namespace (`CLONE_NEWNET` absent, `sandbox.rs:144`), seccomp permits `connect`
(`sandbox.rs:265-278`) — and the exec allowlist (`aetheris_exec_server/src/runner.rs:7-24`)
permits `python3`/`node`/`npm`/`mix`/`cargo`/`git`, every one socket-capable
(`npm install` / `mix deps.get` egress by design). So verify re-executing a `run_command`
that ran a networked script **egresses**, regardless of BL-025's record-and-serve. The
containment is command-shaped, not capability-shaped (found at BL-025, HEAD `d567d75`).

Fix: add `CLONE_NEWNET` to the verify worker's namespace set so re-execution cannot egress
regardless of allowlist — capability-shaped containment. This makes BL-025's record-and-serve
**defence-in-depth** for the purpose-network tools rather than the sole (and partial) defence.

**Builds on BL-025, does not race it.** Under a network namespace, `http_call`/MCP would
*fail* (no network) rather than egress — so record-and-serve (BL-025) must be landed first,
or those tools break under verify. Sequence BL-042 after BL-025.

**Adjacent — decide, don't assume:** a networked `run_command` re-executed under a netns will
*diverge* (the script fails/times out) rather than reproduce. That is verify honestly
reporting a non-reproducible (network-dependent) step, but the divergence message must read
as "network unavailable under verify," not a spurious content mismatch — specify the surfaced
error. Do not silently skip it.

**Interacts with BL-043.** BL-043 (missing `setsockopt`) currently truncates worker egress at
`connect(2)` by accident. Fixing BL-043 restores full egress and makes this row's exposure
larger, not smaller; fixing this row makes BL-043's repair safe. Neither is a substitute for
the other — do not let BL-043's accidental truncation be read as containment.

---

### Pre-implementation handoff (verified at `8021a59`, 2026-07-23)

Recorded here, not in BL-025's implementation notes, because the next session reads *this
row* and not the previous ticket's notes. Each item below was checked against source; treat
them as verified ground, not leads.

**H1 — the premise holds: the exec server inherits the netns.** This was the way the row's
fix could have been quietly false — `run_command`/`git_*` are dispatched to a *separate
process*, so the netns closes their egress only if that process is inside it. Startup order
in `native/aetheris_worker/src/main.rs` settles it: `enter_namespaces()` at `:53` → exec
server spawned at `:80` (comment: "before seccomp filter — execve is blocked after") →
`apply_seccomp_filter()` at `:92`. The exec server is spawned **after** `unshare`, so it
inherits the namespaces. Adding `CLONE_NEWNET` at `sandbox.rs:144` therefore does cover
`run_command` and the eleven `git_*` tools. (Note the exec server is *not* under the seccomp
filter — a separate process, filtered independently — which is why BL-043's `setsockopt`
kill affects `http_call` but not `run_command`.)

**H2 — `lo` comes up DOWN in a fresh netns. Decide, don't default.** A new network namespace
has only a loopback interface and it starts down, so 127.0.0.1 is unreachable until something
brings it up. Nothing in the worker needs it: the worker↔BEAM channel is pipes (`Port`), and
MCP stdio is pipes. **Recommendation: leave `lo` down** — it is the stricter choice and
matches the row's goal; bringing it up would re-admit localhost-only egress for no benefit
verify needs. Flagged for ratification, and whichever way it goes it must be a stated
decision in the implementation notes, not an unexamined default.

**H3 — `enter_namespaces()` fails open, and verify must not inherit that.** `unshare`
failure is logged and execution continues (`sandbox.rs:146-153`: "Fails open: if `unshare` is
rejected by the kernel (e.g. in restricted container environments), the error is logged and
the worker continues without isolation"). So in a restricted container there is **no netns**,
and verify would report a clean result while having had none of the containment it claims —
a well-formed verdict over a gap, which is the Silent-wrong-answer class BL-025 exists to
remove. **Verify cannot stay silent about this.**

  - **RATIFIED 2026-07-23 (human): fail closed.** Verify refuses to re-execute and errors
    (`cannot establish network containment`) rather than proceeding under a banner. This is
    settled — implement it, do not re-litigate.

    Two reasons, recorded so a future reader sees the argument and not just the verdict.
    (i) Verify's entire value *is* the guarantee, so a verify that cannot guarantee has
    nothing to report; a banner is the mitigation you choose when refusing is not an option,
    and here it is — `--allow-effects` already names the deliberate-uncontained path (H4),
    so a *silently* uncontained default has no constituency.
    (ii) **Fail-closed is the reversible direction.** The niche it does not serve is the
    operator who wants default behaviour (serve uncontained, re-execute contained) but cannot
    get a netns; only degrade-and-report serves that. Checked at `8021a59`: nothing in this
    repo runs verify inside a restricted container — CI excludes `:requires_worker`
    (`ci.yml:64`) so the worker never starts there, Rig invokes verify nowhere, `sprint.sh`
    runs on the host. The niche is empty today. If it later appears, degrade-and-report is
    *additive* (a new flag or downgraded verdict, strict default intact); shipping it first
    and tightening later would be a behaviour change on the default path needing its own
    contract edit and migration. Cheap-to-reverse wins.
  - **`record` mode keeps its fail-open.** Normal runs in restricted containers must keep
    working; do not tighten `enter_namespaces` globally.

**H4 — the netns MUST be gated on `not allow_effects`. Required, not optional.** An
unconditional netns breaks `--allow-effects`: the flag exists precisely to re-issue real
network effects, and inside a netns it cannot. It would also flip BL-025's opt-in test
(`test/aetheris/execution/verify_effects_test.exs` — `--allow-effects` → **≥1** connection to
a listener living outside the netns) to 0, i.e. the regression guard for the opt-in path
would silently invert into asserting the opposite of what it was written for.

  - default verify → **netns on**: contained tools re-execute but cannot egress (this row's goal)
  - `--allow-effects` → **netns off**: re-execute everything with real egress (the explicit opt-in)

  It is a clean per-verify decision because BL-025's `Verifier.execute_planned_steps/3` starts
  exactly one worker per verify, and `allow_effects` is already resolved at that point.

**H5 — scope: this is not a one-line flag add.** Three pieces, in order:

  1. **Conditional `CLONE_NEWNET`** — the flag must be *requestable*, so it rides the init
     payload: `Worker.Client.worker_init_payload/5` (`lib/aetheris/worker/client.ex:58-70`)
     builds the map (`sandbox_path`, `memory_limit_bytes`, `cpu_quota_percent`, optional
     `overlay`); add a `network_namespace` field plus a matching `Client.start_link` opt
     (`init/1`, `:157-171`), and have `enter_namespaces` take it.
  2. **Establishment-status plumbing** — and note the ordering problem: the worker writes
     `{"status": "ready"}` at `main.rs:51`, **before** `enter_namespaces()` at `:53`. The
     existing handshake therefore *cannot* carry the netns result without reordering it (move
     the ready write after namespace setup, or add a second message). Whichever is chosen,
     `enter_namespaces` must report whether `CLONE_NEWNET` was actually established rather
     than only logging.
  3. **Verify's non-silent handling** of that status, per H3.

**H6 — reuse the existing hermetic harness.** `test/aetheris/execution/verify_effects_test.exs`
(BL-025) already provides a localhost listener that counts inbound connections, and the
`recorded-trajectory` fixture shape. BL-042's egress test is the same harness pointed at a
`run_command` that shells out to `python3` (allowlisted) opening a socket — expect **0** under
default verify. Its `--allow-effects` arm must keep recording **≥1** (H4).

**Decision status.** H3 (fail closed) — **ratified, human, 2026-07-23**. H2 (`lo` down) —
**agreed in review 2026-07-23**; still must be *stated* as a decision in the implementation
notes rather than left as an unexamined default. H4 (netns gated on `not allow_effects`) is a
requirement, not a choice. Nothing here is open; the implementer starts from settled ground.

**Done when:** the verify worker runs under `CLONE_NEWNET` **when re-executing without
`--allow-effects`**; a `run_command` recorded doing network egress cannot egress during
verify (hermetic listener: 0 hits) and its divergence is reported legibly; the
`--allow-effects` path still egresses and BL-025's opt-in arm still asserts ≥1 (H4); netns
establishment is reported by the worker and acted on by verify, never silently assumed (H3),
with `record` mode's fail-open untouched; `http_call`/MCP remain served (BL-025) and do not
fail under the netns; §5's egress-safety statement upgrades from partial to
capability-complete, human-approved in-cycle (§8) — **and that §5 edit is two statements, not
one**: (a) the upgrade itself, and (b) the guarantee is *conditional on the netns being
establishable*, with the fail-closed refusal (H3) named as contract-visible behaviour, since
an operator whose kernel denies `unshare` gets an error instead of a verdict. Drafting (a)
without (b) would restate the exact overclaim BL-025's §5 rewrite was written to remove —
a capability-complete guarantee asserted unconditionally over an environment that cannot
provide it. Draft both in one review-file artifact for a single approval, as BL-025 did with
§3+§5.

`Source: BL-025 execution, run_command allowlist finding, HEAD d567d75, 2026-07-22.
Pre-implementation handoff verified at 8021a59, 2026-07-23.`

---

### BL-042 — DONE 2026-07-23

**Landed:** conditional `CLONE_NEWNET` (`sandbox.rs:161-224`, gated on the init payload's
`network_namespace`), establishment status reported through a reordered handshake (namespaces
entered *before* `ready`, which now carries `network_namespace` — `main.rs:56-74`),
fail-closed enforcement in `Worker.Client.init/1` via `containment_verdict/2`, the netns
requested as `not allow_effects` by `Verifier` (`verifier.ex:89-96`), a legible CLI refusal,
and `network_isolated` on `VerifyReport` so a networked divergence is interpretable.

**Grew in-cycle by one tool, and the growth was load-bearing.** H6's red-first arm could not
be written as specified: `Verifier` sent every tool to the worker's own dispatch table, but
`run_command` is an exec-server MCP tool, so it re-executed as `unknown_tool:run_command` and
opened **0 connections before the netns existed**. The row's "0 hits" done-when was already
true, for a reason that had nothing to do with containment — a check that could not fail.
Routing `run_command` (scoped decision, human, 2026-07-23) made the red arm real; the
`git_*` family was left alone and filed as **BL-047** with the taxonomy question it deserves.

**Evidence** (`test/aetheris/execution/verify_effects_test.exs`, `--include requires_worker`;
the tag is excluded by default, so a plain `mix test` exercises neither arm):

| arm | connections | step status |
|---|---|---|
| pre-fix, unrouted | 0 | `:error` — `unknown_tool:run_command`, never ran |
| pre-netns, routed | **1** | re-executed and egressed — the red arm |
| default verify (netns) | **0** | `:output_mismatch` + isolation note |
| `--allow-effects` | **≥1** | re-executed and egressed — opt-in preserved (H4); status not asserted, see BL-049 |

**Decisions recorded** (implementation notes: `../aetheris/docs/aetheris/milestones/bl-042-implementation-notes.md`):
H2 `lo` left down — no code brings it up. On a `/proc` mapping-write failure the worker keeps
its log-and-continue and reports `network_namespace: false`, so record's fail-open survives
that path too while verify still refuses. Non-Linux hosts report `net: false`, so a default
verify there refuses — fail-closed working as ratified, named in §5 rather than discovered.

**Off-territory gate finding:** `mix test --include requires_worker` is red with 15 failures,
identical on a clean tree — filed as **BL-048**, not carried silently.

**§5 contract edit:** drafted in `docs/reviews/bl-042-contract-draft.md` as three statements
— (a) partial → capability-complete, (b) conditional on establishability with the fail-closed
refusal named as contract-visible, and (c) the correction of BL-025's false "`:contained` …
re-executed and compared" claim. Lands only on human approval per §8.

---

### BL-043 — `http_call` is killed by seccomp (SIGSYS) in every mode: `setsockopt` missing from the allowlist (#TBD)
**Size:** S · **Priority:** medium · **Section:** Harness (aetheris/)

`http_call` does not work at all — not in verify, not in a normal **record** run. The worker's
seccomp allowlist (`native/aetheris_worker/src/sandbox.rs`) carries a section explicitly
headed *"Network (http_call + MCP stdio)"* listing `socket`, `connect`, `sendto`, `recvfrom`,
`sendmsg`, `recvmsg`, `bind`, `listen`, `accept4`, `poll`, `epoll_*` — but **omits
`setsockopt`** (x86_64 syscall 54), which `ureq` calls to set timeouts immediately after
`connect(2)`. The filter's default action is `KillProcess`, so the worker dies of SIGSYS.

**Demonstrated at BL-025** (hermetic localhost listener + kernel audit, 2026-07-23):

```
audit: type=1326 … comm="aetheris_worker" … sig=31 arch=c000003e syscall=54 code=0x80000000
worker exit status 159   (128 + 31 = SIGSYS)
Worker.Client.execute → {:error, "worker_crashed"}
INBOUND TCP CONNECTIONS TO LISTENER: 1
```

So the TCP connection **does** land; only the HTTP request is never written.

**Do not read this as containment.** It is an unintended truncation of a real egress path,
and the "Network" heading shows egress was the intent. Two consequences:

- **`http_call` is unusable.** Any agent using it gets a crashed worker, not a response. That
  the defect went unnoticed suggests the tool has no live users — worth confirming before
  choosing a fix direction.
- **It is load-bearing by accident.** Adding `setsockopt` restores full egress instantly,
  which widens BL-042's exposure. Sequence: BL-025 (landed) → BL-042 (netns) → this row, or
  accept the widened window knowingly.

**Second defect, same path:** `Verifier` starts the worker with `Client.start_link`, so a
worker that dies takes the **caller** with it (`{:worker_crashed, 159}` propagates as an exit
signal). A library function should not kill its caller because a sandboxed tool crashed; the
BL-025 test traps exits to assert around it. Decide whether the verify worker should be
started unlinked or supervised.

**Operator-visible consequence, observed at BL-025:** the two defects compose, so
`aetheris verify <traj> --allow-effects` on any trajectory containing `http_call` **crashes
the CLI** rather than reporting a verdict:

```
** (stop) {:worker_crashed, 159}
** (EXIT from #PID<0.95.0>) {:worker_crashed, 159}
```

BL-025's opt-in flag is proven to route correctly (the step is served without it, re-executed
with it — 0 vs 1 inbound connections at a hermetic listener), but the opt-in is not
practically usable for `http_call` until this row lands. Not a BL-025 regression: the same
crash occurs on the pre-BL-025 code path and in record runs.

**Done when:** `setsockopt` (and any other syscall a real `ureq` request needs — enumerate by
running one, do not guess the list) is either added to the allowlist with an `http_call`
round-trip test against a hermetic local listener, or `http_call` is explicitly retired; the
worker-crash-kills-caller behaviour is resolved or consciously accepted with a reason.

`Source: BL-025 execution, demonstrated 2026-07-23 (kernel audit + hermetic listener).`

---

### BL-043 — DONE 2026-07-25 — `http_call` repaired (5 syscalls), caller-kill fixed

Landed at harness `515a4ab`, with the §5 contract edit ratified at `1e00a52` (r1). Direction:
**repair, not retire**. Contract edit: `docs/reviews/bl-043-contract-draft.md` (harness) —
**RATIFIED (generalized)**, §8, 2026-07-25.

**§5 names no syscalls, by review disposition.** The r0 draft listed three of the five and
misattributed one (`getsockopt` is a resolver call, not a `ureq` call) — the contract had drifted
from the code inside a single ticket. The ratified clause points at `sandbox.rs`'s commented
"Network" list instead, which is the only copy that cannot fall out of step with the code.

**No-live-users checkpoint, run first as the row required.** The scan found only declarations,
tests and contract examples — no working dependent, as expected of a tool that has SIGSYS-crashed
since forever. Two agent files list it (`agents/news_research.exs`, `agents/pr_learner.exs`), and
the m07→m08 handoff records `pr_learner.exs` as *"run after `http_call` stable"* — it was deferred
pending exactly this fix. Two milestone docs list `tools: ["http_call"]` as a worker-start
*workaround*, already resolved elsewhere. Repair therefore unblocks `pr_learner.exs` rather than
disturbing anything.

**Five syscalls, not one — and they took three rounds to find.** The row named `setsockopt`; the
enumeration turned up four more. Method: patch the filter's default action to non-killing, drive
the real worker binary over its stdio protocol against a hermetic localhost listener under
`strace -ff`, diff the request-path syscalls against the allowlist, then restore `KillProcess` and
re-probe. Each round's probe found the *next* wall:

| Round | Probe | Syscall(s) found |
|---|---|---|
| 1 | `http://127.0.0.1:PORT/` (IP literal) | `setsockopt` (TCP_NODELAY, then SO_RCVTIMEO/SO_SNDTIMEO), `getsockname` |
| 2 | `http://localhost:PORT/` (resolver via `/etc/hosts`) | `getsockopt` |
| 3 | `http://…invalid/` (real nameserver query) | `sendmmsg`, `recvmmsg` — glibc sends A+AAAA in one call |

Round 2 is why "enumerate, don't guess" earned its place: `localhost` resolves from `/etc/hosts`
and never issues a DNS query, so a hostname probe that *looks* like it covers resolution does not.
Only a name that must reach a nameserver surfaced the last two.

**Verified against three paths under the live `KillProcess` filter**, all worker-exit-0: plaintext
localhost round-trip returns `{"status":200,"body":"live"}`; a real DNS lookup returns a clean
`Dns Failed … Name or service not known`; and HTTPS to a self-signed local listener returns a
clean certificate-validation error — i.e. the TLS handshake path is covered too. The suite's
`https://httpbin.org/get` test now reaches the real host and fails on *its* `503`, which is the
clearest possible evidence the request completes end-to-end.

**A near-miss worth recording.** The first "successful" round-trip was a false green: adding
`setsockopt` to the allowlist without adding it to `syscall_number/1` made filter *construction*
fail, and `apply_seccomp_filter` **fails open** — so the worker ran with **no filter at all** and
`http_call` worked because the sandbox was gone. A typo in that list silently disables the entire
sandbox while every tool test stays green. Three Rust tests now guard it: every allowlist name
resolves, the filter builds, and the five socket calls are present by name.

**Caller-kill (part 2): unlinking was necessary but not sufficient.** `Verifier` now starts the
worker via a new `Client.start/1` (unlinked) plus a monitor, `demonitor(:flush)` on every exit
path — unlinked+monitor rather than supervised because the worker has a one-call lifecycle and a
re-executed step must not be restarted. But `GenServer.call` *independently* exits the caller with
the server's reason when the server dies mid-call, so the unlink alone left the crash path intact;
`execute/2` and `call_mcp_tool/4` now convert any such exit into `{:error, "worker_crashed"}`,
matching what the port handler already replies to dispatched requests. Both halves are
mutation-checked, and a verify-level test kills the worker *from inside a re-executed step* (via
`/proc` to reach the grandparent pid) — without it, reverting to `start_link` reddened nothing.

**Result: `requires_worker` 12 → 11 failures; SIGSYS 8 → 4.** Not the ~4 total the ticket
predicted, because the 8 SIGSYS were **two different gaps**, not one — see BL-055. The four this
row fixed are gone; the four that remain are MCP-stdio spawn hitting a *deliberate* exclusion, and
they must not be "fixed" by widening the filter.

`Source: BL-043, 2026-07-25. Captures: full_requires_worker{,2}.txt, strace rounds 1–3.`

---

### BL-050 + BL-055 + BL-056 — DONE 2026-07-25 (one reorder, three rows)

Landed together at harness `9871059` — they were the same surgery — with the §5 contract edit
ratified at `dd12dbb` (r1). Contract edit: `docs/reviews/bl-050-055-056-contract-draft.md`
(harness), **RATIFIED (hedged)**, §8, 2026-07-25. Review: `docs/reviews/bl-050-055-056-review.md`.

**§5 was hedged at review, and the operator message deliberately was not.** The r0 wording asserted
that container runtimes refusing `unshare` do not refuse `seccomp` — the exact claim the scout memo
had listed as *unverified*. §5 now says the filter is *rarely* refused and admits no survey was
done; the one-line error in `verify.ex` still says "harness defect, not an environment limitation",
because its job is to stop an operator reaching for `--allow-effects`. That split is recorded in §5
itself and in the draft so a later reader does not reconcile one to the other.
Scout memo that settled the directions: `docs/reviews/bl-055-bl-056-containment-decisions.md`.

**The one change.** `ready` was written straight after the namespaces while cgroup, overlay,
exec-server spawn and the seccomp filter all happened *after* it. `ready` is now the
**fully-established barrier**:

```
namespaces → cgroup → overlay → exec server → stdio MCP servers → seccomp → ready(attests all)
```

and the handshake carries `overlay`, `exec_server`, `seccomp` (+ error) and a per-server
`mcp_servers` attestation alongside `network_namespace`. Order is forced: the filter must be last
because the exec server and the stdio servers both need `execve`, which it excludes.

**BL-050** — the overlay is mounted before the handshake, so `RunOverlayTest`'s `File.dir?(upper)`
immediately after start no longer races. Green, no sleep, no polling.

**BL-055 (option 1)** — `config.mcp_servers` travels in the init payload (stdio entries only;
`:http` still connects at request time through the exec server, which the filter permits). The
worker spawns them pre-filter and attests each. `loop.ex` no longer spawns — it only lists tools.
The request-time `mcp_spawn` is **removed** on both sides rather than left as a call that always
killed the worker; `spawn_mcp_server/2` became `connect_http_mcp_server/2`, which refuses a stdio
config. Verify passes no `mcp_servers`, so a verify worker spawns none.

**BL-056** — the worker still fails open and now *attests*; policy moved to the BEAM, which is the
only side that knows the mode. Verify **refuses** with a message that shares no wording with the
netns refusal and does **not** offer `--allow-effects` (the flag would not install a filter and
would drop the network guard too). Record **continues**, but no longer silently: `Logger.error` at
worker start plus `meta.containment` in the trajectory, so a later reader can tell a sandboxed run
from an unsandboxed one. That silence was the defect, not the fail-open.

**Risks checked rather than assumed.** Time-to-ready after the reorder: **2–3 ms** bare, **17–20 ms**
with a stdio MCP server declared, against the **5 000 ms** init timeout — three orders of magnitude
of headroom, no adjustment needed. `requires_worker` run **twice**: 6 failures both times with
**identical membership**, so the reorder introduced and shifted no flake; the BL-054 slot did not
appear in either run.

`Source: BL-050/055/056, harness 9871059, 2026-07-25.`

---
### BL-056 — `apply_seccomp_filter` fails open: any filter-build failure runs the worker fully unsandboxed (#TBD)
**Size:** S–M · **Priority:** medium · **Section:** Harness (aetheris/)

Filed from BL-043's flagged observation at review r1, per the standing rule that a deferred
finding gets a row rather than packet prose.

**The defect.** `Sandbox.apply_seccomp_filter/0` returns `Err` on any build failure, and the caller
logs a single stderr line and **continues** (`main.rs`):

```
[sandbox] seccomp filter failed: unknown syscall: setsockopt
```

The worker then runs with **no filter at all**. Nothing else reports it: the handshake still says
`ready`, tools still work — better than before, in fact — and every test stays green. The failure
mode of a disabled sandbox is *more* capability, so nothing downstream notices.

**BL-043 tripped this live, which is why it is filed rather than theorised.** Adding `"setsockopt"`
to the allowlist without adding it to `syscall_number/1` made construction fail; the resulting
`http_call` round-trip **passed**, and it passed *because the sandbox was gone*. A green test was
the evidence of the protection's absence.

**Why the BL-043 guards do not close it.** The three Rust tests added there (every allowlist name
resolves; the filter builds; the five socket calls are present) close the **typo vector at test
time**. The runtime fail-open remains for every other build-failure path: a seccompiler shape
rejection (it rejects identical match/mismatch actions — also hit during BL-043), an architecture
`TargetArch::try_from` failure, or a kernel that refuses `SECCOMP_SET_MODE_FILTER`.

**The parallel that frames the decision.** Verify already **fail-closes** on its *other* containment
primitive: a worker that cannot establish the network namespace never finishes starting, and
`aetheris verify` reports `cannot establish network containment for verify; re-run with
--allow-effects …` rather than a verdict (§5, "When containment cannot be established"). The
seccomp filter — the primitive that confines everything the namespace does not — fail-opens
instead. Those two should not disagree.

Fail-open is **correct** for `enter_namespaces` in *record* mode, and that must not change: a
normal run in a restricted container has to keep working, and §5 says so explicitly. The question
is narrower — should **verify** proceed with an unfiltered worker?

**Done when:** the question is decided and recorded — verify refuses to run unfiltered (the netns
parallel), or accepts it with a reason written down — and the chosen behaviour is implemented with
a test that exercises the *failure* path, not just the happy one. If refuse is chosen, the refusal
must be distinguishable in the report from the netns refusal, since an operator needs to know
which primitive was unavailable. The refuse-vs-accept call is **§8/human**; this row carries it.

`Source: BL-043 done-check flagged observation, review r1 disposition, 2026-07-25.`

---

### BL-055 — MCP stdio servers cannot be spawned after the seccomp filter: `execve` is excluded by design (#TBD)
**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)

Surfaced by BL-043's done-check, which expected to clear all 8 of BL-048's SIGSYS failures and
cleared 4. The other 4 are a different defect wearing the same symptom.

`Client.spawn_mcp_server/2` sends `mcp_spawn` to the worker **at request time**, i.e. *after*
`apply_seccomp_filter`. Spawning a subprocess there needs `prilimit64` then `execve`, and neither
is in the allowlist. Traced, not inferred — the worker dies at `prlimit64` immediately after two
`pipe2` calls:

```
read(0, "…{\"id\": \"1\", \"command\": \"mcp_…"…) = 109
pipe2([3, 4], O_CLOEXEC)                = 0
pipe2([5, 6], O_CLOEXEC)                = 0
prlimit64(0, RLIMIT_NOFILE, …)          = 302
+++ killed by SIGSYS (core dumped) +++
```

**This exclusion is deliberate, and BL-043 deliberately did not touch it.** `main.rs:95` says so
in as many words — *"Spawn internal exec server before seccomp filter — execve is blocked after
filter is applied"* — and the harness spawns its own exec server pre-filter for exactly this
reason. Adding `execve` to the allowlist would let a sandboxed worker execute arbitrary binaries
after the filter is installed, which is a containment decision far larger than a test fix, and
BL-043's ticket explicitly forbade weakening containment to make tests pass.

So the four affected tests (`spawn_mcp_server/2`, `list_mcp_tools/2`, `call_mcp_tool/4` in
`client_test.exs`, and `McpGithubTest`, which spawns `github-mcp-server` over stdio) assert a
capability the sandbox removes. One of three things is true and someone has to choose:

1. **Stdio MCP servers must be spawned pre-filter**, like the internal exec server — i.e. from the
   init payload, with the server list known at worker start. This preserves containment and makes
   the capability real, at the cost of no longer being able to add servers mid-run.
2. **Stdio MCP spawn is unsupported** and the tests are stale — HTTP-transport MCP and the
   pre-spawned exec server remain the supported paths.
3. **The filter is relaxed** for this case. Named for completeness; it is the option that trades
   the sandbox for a convenience and should not be chosen quietly.

**Done when:** one of the three is chosen and recorded; the four tests either pass under the
chosen design or are removed/retagged with the reason; and if (1), the mid-run spawn API is
removed rather than left as a call that always crashes the worker.

`Source: BL-043 done-check, 2026-07-25 (strace of the mcp_spawn path).`

---

### BL-044 — `mix aetheris` discards every command's exit code (#TBD)
**Size:** S · **Priority:** low · **Section:** Harness (aetheris/)

`Mix.Tasks.Aetheris.run/1` is `_ = Aetheris.CLI.run(argv); :ok`
(`lib/mix/tasks/aetheris.ex:10-11`). `Aetheris.CLI.run/1` returns `Formatter.print/2`'s
`0 | 1` — which the escript entry point does halt on (`main.ex:33-34`) — but the Mix task
throws it away. So **`mix aetheris <anything>` exits 0 regardless of outcome**, for every
command, not just verify.

Surfaced at BL-025, where `aetheris verify` was given a failure-reflecting exit code: the
escript honours it, `mix aetheris verify` does not. The BL-025 test therefore asserts the code
at `Formatter.print/2` rather than by shelling out through `mix`.

**Not fixed at BL-025 deliberately** — making the Mix task halt non-zero would change
behaviour for every command at once, and `scripts/sprint.sh` runs `mix aetheris` under
`set -euo pipefail`, so any command that starts reporting failure honestly could abort the
sprint. That is a wanted outcome eventually, but it needs the sprint audited in the same
change rather than as a side effect.

**Done when:** `mix aetheris` propagates the exit code (or documents why it cannot), and
`sprint.sh` is audited for commands that would newly abort it.

**A concrete audit input, found 2026-08-06 (m4 t2) — one site where the discarded code makes an
existing assertion vacuous.** The cloudcost case wraps its real run in an exit-status test
(`../aetheris/scripts/sprint.sh`, the `if "${CC_HERMETIC[@]}" mix aetheris --json run …` block) and
`fail`s on "non-zero exit". Because the Mix task discards the code, that branch is reachable only
when the task *raises*; a run that ends `:failed` exits 0 and the case prints `[OK]`. So the
assertion passes identically whether or not the run succeeded — the **Silent-wrong-answer** shape,
in the apparatus. Verified at harness `871a720`: `lib/mix/tasks/aetheris.ex` is still
`_ = Aetheris.CLI.run(argv); :ok`, and `CLI.run/1`'s `System.halt(exit_code)` is still commented
out. Named here rather than fixed at t2, which does not open that file; it is the kind of site
this row's audit exists to enumerate, and there is no reason to think it is the only one.

**A second audit input, found 2026-08-06 (m4 t3) — three sites that are NOT affected, recorded as
a negative so the audit does not re-derive them.** The cloudcost case's three no-silent-fallback
guards (`CLOUDCOST_PROVIDER=aws` with no key, `linode` with no token, unknown provider) run
`mix run --eval`, not `mix aetheris`, and `mix run` does **not** swallow the code. Verified both
directions at harness `f8bbac8`: each guard exits 1 with its own `RuntimeError` message, and the
same command with nothing to raise about exits 0. So these three need no change when this row is
fixed. **The guards do have a defect, but it is not this one**: each asserts only *that* an eval
raised, never *which* raise fired, so any raise passes — including one caused by an environment
change. m4 t3 fixed that for the one guard whose environment it moved (the Linode guard now matches
the raise message) and left the other two, whose failure direction is safe.

`Source: BL-025 execution, 2026-07-23; audit input appended m4 t2, 2026-08-06; second audit input
appended m4 t3, 2026-08-06.`

---

### BL-047 — DONE (impl) 2026-07-24 · §5/§3 edits pending §8 ratification

**Classification ratified (human, 2026-07-24): Option 3** — `git_*` is served-not-verified,
always, **not** lifted by `--allow-effects`. It is `:contained` for *safety* (local-only; no
`push`/`fetch`/`pull`/`clone`/`remote`, confirmed from source) but not verify-reproducible:
verify mounts no overlay, so the recorded repo is absent and `git_commit` embeds a
nondeterministic SHA. Re-executing would manufacture a spurious `:output_mismatch` — BL-049 at
family scale. The read/mutate line does **not** split the family; none reproduce.

**Landed (harness `f41eb12` code+tests, `68d2614` notes):** `EffectClass` gains `@git_tools`
(single source of the **ten** names — read `git_status`/`git_diff`/`git_diff_staged`/`git_log`/
`git_show`, mutate `git_add`/`git_commit`/`git_checkout`/`git_cherry_pick`/
`git_cherry_pick_control`), referenced by both `@contained_tools` and the new
`@non_reproducible_tools`, plus `non_reproducible?/1`. `Verifier.plan_step/2` serves
non-reproducible tools **ahead of** the `--allow-effects` gate, so the git serve is
unconditional. Union / `@classes` / `known_tools/0` / completeness test / `@exec_server_tools`
(`[run_command]`) all untouched — git is served, never re-executed (3a; 3b rejected).

**The family is TEN, not eleven.** All three authorities agree on ten; the landed §5 said
"eleven" (×2), inherited from BL-042 — corrected in the held §5 edits, flagged not followed.

**Tripwire (BL-049 F1 forward):** every `git_*` the *registry* exposes must be in
`@non_reproducible_tools`, expected set derived from `Registry.names()` (a real source), not a
literal — mutation-checked (drop `git_commit` → guard fails naming it; completeness stays
green). A future `git_worktree` forgotten in the set fails loudly instead of shipping
re-executable.

**Done-check:** before-fix `git_commit` → `:error unknown_tool:git_commit`; after → `:served`
under default AND `--allow-effects`; git-only starts no worker; non-vacuity — git served while
a co-recorded `http_call` re-executes and egresses under `--allow-effects`. `mix test` 930/0,
format/credo/dialyzer/hex.audit green. `requires_worker` red set unchanged (BL-048 + BL-050).

**§5/§3 edits (five): LANDED, harness `af56a57` (§8, human-approved 2026-07-24).** §3 verify
row (re-execution qualified to reproducible output; served set gains `git_*`; non-guarantee
reframed), §5 three-classes split (`eleven`→`ten` ×2), the two-reasons-to-serve paragraph, the
opt-in rider (`--allow-effects` does not lift the git serve), residual bullet → resolved.
claude-ui r1 raised one non-blocking finding (F1: `non_reproducible?` scope) — answered by
keeping it name-only (`classify/2` is name-first, so a colliding external `git_status` is
`:contained` not `:uncontained`) plus the `@non_reproducible_tools ⊆ @contained_tools` guard;
closed at r2. Draft: `docs/reviews/bl-047-contract-draft.md`. Reviews r0/r1/r2 +
`bl-047-review-r1.md` in `docs/reviews/`.

`Source: BL-042 execution (routing gap demonstrated 2026-07-23 at 8021a59); classification
ratified + implemented 2026-07-24 at f41eb12.`

<details><summary>Original ticket (pre-implementation)</summary>

### BL-047 — Verify never re-executes the `git_*` family: exec-server routing gap + a taxonomy decision (#TBD)
**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)

`Verifier` re-executes a recorded tool by sending it to the worker's own dispatch table
(`Client.execute` → `main.rs` `dispatch/3`), which knows only `read_file`, `list_dir`,
`write_file`, `http_call`. But `run_command` and the eleven `git_*` tools are **exec-server
MCP tools** in a live run (`loop.ex` `@exec_server_tools`, `dispatch_mcp_tool/4`). So every
member of that family re-executed as `unknown_tool:<name>` — a per-step `:error`, never a
comparison — while determinism-contract §5 claimed `:contained` tools are "re-executed and
compared".

Demonstrated at BL-042 against unmodified `8021a59`, before any fix:

```
%{error: "unknown_tool:run_command", status: :error, actual_output: nil,
  recorded_output: "{\"duration_ms\":20,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"connected\\n\"}"}
```

**BL-042 routed `run_command` only** — the tool its own containment proof requires, whose
re-execution BL-025 already ratified, and whose new hazard (egress) is exactly what BL-042's
network namespace contains. The `git_*` family was deliberately left unrouted rather than
fixed by the same three lines, because routing it is not merely a bug fix:

**The real question is whether mutating git operations should re-execute under verify at
all.** `git_add`, `git_commit`, `git_checkout`, `git_cherry_pick` and
`git_cherry_pick_control` mutate a repository. Re-executing `git_commit` against a sandbox
whose HEAD has moved does not reproduce a recorded step, it writes a new one; `git_checkout`
can destroy working-tree state that the recorded run did not have. The read-only members
(`git_status`, `git_diff`, `git_diff_staged`, `git_log`, `git_show`) are a different case
entirely. This is a taxonomy decision of the same weight as BL-025's three classes and it
should be **decided**, not inherited from an accident of routing — which is the whole reason
BL-042 did not quietly extend its own fix over the family.

**Options to adjudicate (not a menu to pick from silently):** route them all as `:contained`;
split the family, re-executing the read-only members and reclassifying the mutating ones as
`:uncontained` (record-and-served); or declare the family unsupported under verify with an
explicit status distinct from `:error`.

**Done when:** the classification of each `git_*` tool is decided and recorded in §5 with a
human-approved edit (§8), the implementation matches the decision, and a recorded `git_*`
trajectory verifies to whatever verdict that decision implies — never to
`unknown_tool:<name>`. §5's routing-gap paragraph and §3's verify row (both landed by BL-042)
are updated to remove the named gap.

**Pre-wired by BL-049, so read this before routing (BL-049 r1 F5).** The volatile-metadata
strip is already in place for `git_*` on the **record** side: it keys off the exec-server id at
dispatch (`loop.ex`, `dispatch_mcp_tool/4` → `exec_server_payload/2`), so all twelve routed
tools are recorded with `duration_ms` in the step envelope, `git_*` included, and
`VolatileMetadataTest` unit-covers the `git_*` response shape. The **verify** side is not:
`Verifier`'s `@exec_server_tools` is `run_command` alone, and both `reexecute/3` and
`normalize_recorded/2` key off it. So routing the family is one edit to that list — but the
invariant between the two lists is **subset containment**, not equality: a name in `Verifier`'s
list that `Loop` does not route would be normalized on read yet recorded unstripped, which is
BL-049's failure mode reintroduced for exactly that tool. Confirm both sides agree when you
route them.

`Source: BL-042 execution, demonstrated 2026-07-23 at 8021a59. §5 correction landed with
BL-042's contract edit; this row closes the gap that correction names. Pre-wiring note added
from BL-049 review r1, 2026-07-24.`

</details>

---

### BL-049 — A `run_command` step can essentially never verify: `duration_ms` is inside the compared payload (#TBD)
**Size:** S · **Priority:** medium-high · **Section:** Harness (aetheris/)

`Verifier.compare_status/4` compares recorded vs re-executed tool output by **value equality**
over the whole payload string. The exec server's `run_command` payload is
`{"duration_ms":N,"exit_code":N,"stderr":"…","stdout":"…"}` — it carries a wall-clock
measurement. So two runs of an identical, perfectly reproducible command differ whenever the
timing differs, which is almost always.

Measured, six consecutive runs of the same `python3` one-liner, recorded and then re-executed
under `--allow-effects` (no namespace, network reachable, identical stdout and exit code):

```
status: :output_mismatch  recorded: {"duration_ms":19,…}  actual: {"duration_ms":21,…}
status: :verified         recorded: {"duration_ms":22,…}  actual: {"duration_ms":22,…}
status: :output_mismatch  recorded: {"duration_ms":23,…}  actual: {"duration_ms":19,…}
status: :output_mismatch  recorded: {"duration_ms":19,…}  actual: {"duration_ms":20,…}
status: :output_mismatch  recorded: {"duration_ms":19,…}  actual: {"duration_ms":21,…}
status: :output_mismatch  recorded: {"duration_ms":21,…}  actual: {"duration_ms":20,…}
```

Five of six report a divergence that is purely timing; the sixth "verifies" by coincidence.

**Exposed by BL-042, not caused by it.** Before BL-042 routed `run_command`, the step returned
`unknown_tool:run_command` and never reached the comparison at all, so the defect was
unreachable. It is now live for any operator running `aetheris verify` on a trajectory
containing `run_command` steps: they get `Failed: N` on commands that reproduced exactly.

**Not a patch — a §5 semantics decision.** Three directions, and they differ in what "verified"
comes to mean:
- **Exclude volatile fields from comparison** (`duration_ms` today; enumerate rather than
  guess). Verify then compares what the tool *did*, not how long it took.
- **Compare structurally** rather than by string equality, with a per-tool field policy. More
  general, more machinery, and the policy is exactly the thing that needs deciding.
- **Stop returning timing inside the compared payload** — move `duration_ms` out of the tool
  output and into the step envelope, where it is recorded but not compared. Cleanest, and it
  touches the exec server's response shape plus every recorded trajectory's expectations.

Whichever is chosen, §5 must say what a `:verified` `run_command` step asserts, since today it
asserts something no honest command can satisfy.

**Adjacent, check before fixing:** `read_file`/`list_dir`/`write_file` go through the worker's
own dispatch and their `duration_ms` sits *outside* the compared `output` (`parse_execute_response/1`
splits `output`/`fs_hash`/`duration_ms`) — which is why this never surfaced for them, and why
the third direction above is the one that matches the existing worker-native shape.

**Done when:** the comparison semantics for timing-bearing payloads is decided and recorded in
§5 with a human-approved edit (§8); a recorded `run_command` that reproduces exactly reports
`:verified` deterministically; and a regression test asserts that across repeated runs, not
once.

`Source: BL-042 review, 2026-07-23 — reviewer challenged the packet's `:verified` claim for the
--allow-effects arm; measurement showed the arm is nondeterministic and the claim was wrong.`

---

### BL-049 — DONE 2026-07-24

**Direction chosen:** the third of the row's three, *"stop returning timing inside the compared
payload"* — the one the row itself flagged as matching the existing worker-native shape. The
verifier grew **one** change and it is reuse, not policy: it calls the same strip on the
recorded side. It holds no field list of its own, which is what separates this from the
rejected "exclude volatile fields in the compare".

**Landed:** `Aetheris.Execution.VolatileMetadata` as the single definition of "volatile"
(`fields/0`, `split/1`, `strip/1`); `Loop.exec_server_payload/2` splitting `duration_ms` into
the step envelope for every `aetheris_exec`-routed tool; `Verifier` stripping both the
re-executed output and — via `normalize_recorded/2` — the recorded one before comparing; the
two LLM-facing `registry.ex` descriptions corrected; a tripwire test binding the worker-native
envelope (`parse_execute_response/1`) to the same definition.

**Why the read side is not optional.** Trajectory events are immutable (critical rule #1), so
every trajectory recorded before this commit carries `duration_ms` inside the recorded blob
forever. A parse-layer-only fix would have satisfied the invariant for new records while
turning the old corpus's 1-in-6 flap into a deterministic `:output_mismatch` — a confident
wrong verdict, which is worse than a flaky one. Normalizing both sides through one definition
is what lets §5 say "resolved" without hedging to "resolved for records at or after `13ff59c`".

**Evidence** — the same hermetic `python3 -c 'print("bl049")'` trajectory, six verifies:

| | verdicts | note |
|---|---|---|
| before fix | 5 × `:output_mismatch`, 1 × `:verified` | `stdout`/`stderr`/`exit_code` byte-identical in all six; only `duration_ms` moved (recorded 10, actual 13/12/9/11/10/11) |
| after fix, pre-fix recording | 6 × `:verified` | exercises the read-side normalization; fixture asserted to still contain `duration_ms` |
| after fix, post-fix recording | 6 × `:verified` | exercises the parse-layer fix; fixture asserted to *not* contain it |

Each run additionally asserts `verified: 1`, `served: 0` and a non-empty actual output — a
served step cannot fail, so it must not be allowed to pass as a fix
(`test/aetheris/execution/verify_verdict_test.exs`, `--include requires_worker`). The
deterministic half of the proof needs no worker at all
(`test/aetheris/execution/volatile_metadata_test.exs`): two responses differing only in
`duration_ms` compare byte-identical.

**BL-042's `--allow-effects` arm tightened.** It asserted only `!= :served` because the verdict
was a coin flip; it now asserts `== :verified`, confirmed across six seeds. Two BL-042
assertions comparing `recorded_output` to the raw exec-server blob were updated: they were
asserting the pre-fix shape. They now assert the *compared* form **and** that the on-disk
recording still carries `duration_ms` — immutability of the record and exclusion of the field
from the compare are separate claims, and both are now asserted.

**Deviation from the ticket's sketch, adjudicated.** The ticket said to extract the strip *out
of* `parse_execute_response/1`. Nothing there is extractable: that function splits sibling keys
of a decoded map, while the exec-server case removes keys from a JSON object embedded in the
`output` string. The invariant ("one definition of volatile") binds; the sketch does not. It is
met by `VolatileMetadata.fields/0` plus a tripwire test on the worker-native envelope.

**Consequence stated rather than buried:** the agent no longer sees `duration_ms` in an
exec-server tool result. `payload["output"]` *is* the transcript content (`fork.ex:107`), so
the recorded and model-visible values cannot diverge without breaking fork replay. This is the
worker-native behaviour, where the field was always envelope-only.

**Decisions recorded** (implementation notes:
`../aetheris/docs/aetheris/milestones/bl-049-implementation-notes.md`): `normalize_recorded/2`
is restricted to `@exec_server_tools` rather than applied to every recorded output, because a
worker-native `read_file` result that merely *happens* to be JSON with a `duration_ms` key is
file content, not execution metadata. `Verifier`'s `@exec_server_tools` stays `run_command`
alone — verify only compares what it re-executes, and `git_*` is BL-047's decision.

**§5/§3 contract edits: LANDED, harness `a926631` (§8, human-approved 2026-07-24).** Three,
after review grew (a)'s two to three: (a) §5 gains "What the comparison ranges over" — the
compare is value equality over the deterministic portion, volatile metadata excluded, resolved
across both record eras (landed **restructured** per r2, out of Residual-limitations into the §5
body with a one-line resolved pointer left behind); (b) "The opt-in" — `--allow-effects` also
waives the netns; (c) §3 verify row qualified to "the deterministic portion … excluded on both
sides" (added at r1 F3, an overstatement the r0 draft had claimed needed no change). Draft +
before/after: `docs/reviews/bl-049-contract-draft.md`. Reviews: r0/r1/r2 in `docs/reviews/`.

---

### BL-048 — DONE (pending first CI dispatch) 2026-07-25

Landed at harness `6e2fad8`. **The set is green and wired.** `mix test --include
requires_worker` on a capable machine: **951 tests, 0 failures, 67 excluded, 1 skipped**,
identical across two consecutive runs.

**One thing pends, and it is the human's move.** The wiring is a CI job gated on the worker's
containment attestation, and the attestation only reports on `ubuntu-latest` once a job runs
there (a PR or `workflow_dispatch`). If it reports capable, BL-048 closes as a CI job. If it
reports *not* capable — GitHub's 24.04 image may restrict unprivileged user namespaces via
AppArmor, which this repo has deliberately not surveyed — the harness sprint is the standing
home and **BL-048 still closes**, just wired there: `scripts/sprint.sh` already prints the same
probe. Either way the set has a gate; which gate is what the first dispatch decides.

**The six, each triaged (the row's own done-when):**

| Test | Disposition | Why |
|---|---|---|
| `RunCommandTest` ×3 | **fixed** | Three *different* non-permitted commands — `sleep`, `pwd`, `false` — not just `pwd`. Each asserted against a command the exec server is right to refuse, so none exercised what its name claimed. Rewritten on `python3` |
| `McpHttpTest` | **fixed** | Test-hygiene, not environment: `on_exit` called `Port.close` on an already-closed port and raised, so the test's only failure mode was its own teardown. It is hermetic (local python mock) and stays in the set |
| `McpGithubTest` | **retagged, kept** | `:requires_real_provider`. Needs a real model to *choose* to call the tool, plus a token and the binary. The stdio GitHub MCP path is live and surfaced, so the test is kept — it just cannot live in a sandbox-only set |
| httpbin `http_call` | **retagged (extracted)** | `:requires_internet`, in a module of its own. See the correction below |
| `OverlayAutonomousTest` | **skipped, filed as BL-057** | Cannot pass as written; no test-side config fixes it. See BL-057 |

**A correction worth recording, because it nearly shipped.** The first attempt retagged the
httpbin test in place with `@tag requires_worker: false`. That does **not** hold against a
module-level `@moduletag :requires_worker` under an `--include` — the test still ran, and the
set reported **green** because httpbin happened to return 200 on that run. The second run got a
503 and exposed it. The fix is a module of its own; the lesson is that "the set is green" needed
two runs to be worth saying, which is why the done-check asked for two.

**Residual accounting, corrected one last time.** This row's characterisations were wrong twice
before: "network/credential-dependent integration tests" (they were mostly SIGSYS → BL-043),
then "mostly BL-043" (half were the MCP-stdio/`execve` exclusion → BL-055). Final state: **zero
residual in the deterministic set.** What was environment-dependent is retagged out and still
runs under its own include — verified, not assumed: both retagged tests were executed under
`--include requires_internet` / `--include requires_real_provider` and fail for their
environmental reasons (a live 503; the model not calling the tool). Retagged, not dropped.

**Part B — the set cannot rot invisibly again.** `scripts/containment_probe.exs` asks the worker
what it established (BL-050/055/056 made that a runtime fact) and reports
netns/seccomp/exec-server/overlay. The CI `sandbox` job runs the probe, then runs the set if
capable or **skips with the missing primitive named** — deliberately not red, because a job that
reddens on a runner's limits gets disabled, which is how this set rotted in the first place.

`Source: BL-048, closed at harness 6e2fad8, 2026-07-25.`

---

### BL-057 — A stub run that declares tools silently gets no worker, so its tool calls never execute (#TBD)
**Size:** S–M · **Priority:** medium · **Section:** Harness (aetheris/)

Found during the BL-048 closeout while diagnosing `OverlayAutonomousTest`, which is skipped
pending this.

`Agent.Supervisor.worker_child_spec/1`'s **first** clause is

```elixir
defp worker_child_spec(%{provider: "stub", mcp_servers: []}), do: []
defp worker_child_spec(%{tools: [], mcp_servers: []}), do: []
```

The first matches on `provider` and `mcp_servers` **without looking at `tools`**, and it is
matched before the clause that does. So a run with `provider: "stub"` and
`tools: ["write_file"]` starts **no worker at all**. Its stub responses can still drive tool
calls; those calls silently do not execute; and the run reports `:done`.

`OverlayAutonomousTest` is exactly that shape, which is why it fails identically before and
after BL-050's reorder — no worker means nothing mounts an overlay, so the probe file lands
nowhere and the test's `assert File.exists?(probe_in_upper)` cannot pass. It is **not** the
BL-050 race, and BL-050 correctly did not claim it.

**Why this was not fixed in the BL-048 closeout.** The honest fix is the clause — a stub run
that declares tools does need a worker — but that clause governs **six test files, three of them
in the default suite** (`loop_test.exs`, `pre_tools_test.exs`, `injector_test.exs`, plus
`spawn_agent_test.exs`, `skill_extraction_test.exs`, and the overlay test). Changing it turns
default-suite tests into worker-dependent runs, which is a product decision about what a stub run
*is*, not a test fix — and BL-048 was explicitly forbidden from weakening or reshaping product
behaviour to make tests green.

**The question to settle:** should a `provider: "stub"` run that declares tools start a worker
and execute them (making the stub a *model* stub only), or is a stub run defined as
tool-inert — in which case declaring tools on one should be rejected at config validation rather
than silently ignored? Either answer is defensible; the current behaviour — accept the config,
start no worker, execute nothing, report success — is not.

**Done when:** the question is answered and recorded; the behaviour matches the answer (worker
started, or config rejected); `OverlayAutonomousTest`'s `@moduletag :skip` is removed and it
passes, or the test is rewritten against whatever the answer makes correct; and the blast radius
on the six files is walked, not assumed.

`Source: BL-048 closeout, 2026-07-25 (harness 6e2fad8).`

---

### BL-048 — The `requires_worker` test set is red: 15 failures, invisible to CI and to every default `mix test` (#TBD)
**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)

`mix test --include requires_worker` reports **15 failures** on `main` at `8021a59`, with no
BL-042 changes applied (verified by stashing them and re-running: the failing set is
byte-identical, 900 tests / 15 failures). CI never sees them — `ci.yml:64` runs
`--exclude requires_worker --exclude integration` — and neither does a local `mix test`,
because `test_helper.exs:4` excludes the same tags by default. Found off-territory by
BL-042's own done-check, which is the only reason it is on the record at all.

Three distinct causes, not one:

- **Test written against a stale allowlist** — `run_command_test.exs` uses `pwd`, which is not
  in `PERMITTED_COMMANDS` (`aetheris_exec_server/src/runner.rs:7-24`); the exec server
  correctly answers `command not permitted: pwd`. 3 failures.
- **`fs_hash` is nil where the test expects `sha256:…`** — `client_test.exs:53`,
  `fs_hash_stability_test.exs` (×2). ~~This one is **not** obviously a stale test and may be a
  live defect in worker fs-hashing; it needs diagnosis, not a test edit.~~ **CORRECTED — it is
  nil by design, not a live defect. Diagnosed and closed as BL-053** (`d4728af` removed the
  whole-sandbox hash for a real 30s-timeout reason; the tests were never updated). 3 failures,
  now green.
- **Network/credential-dependent integration tests pulled in by the include** — `httpbin.org`,
  the GitHub MCP server, the HTTP MCP transport. `--include requires_worker` overrides the
  `:integration` exclusion for tests carrying both tags, so these run whether or not the
  environment can support them. 6+ failures. **CORRECTED — the characterization is mostly
  wrong.** Eight of the nine carry `** (stop) {:worker_crashed, 159}` — 159 = 128+31 = SIGSYS —
  which is **BL-043**'s `setsockopt` seccomp gap killing the worker, not a missing credential or
  an unreachable host. Landing BL-043 should clear ~8 of these on its own. The ninth
  (`RunOverlayTest`) is **BL-050**'s handshake race. So the strand is two tracked defects wearing
  an environment-dependency costume; the `:integration` tagging question is real but secondary.
  Do not re-triage per packet — this correction is the triage.

**This is the gate-rot pattern the CLAUDE.md gate rule exists to catch**, running in the
direction that is hardest to see: a set that no gate executes cannot go red visibly, so it
went red silently and stayed. When it broke is unknown, because nothing was watching.

**Done when:** each failure is triaged to stale-test / live-defect / environment-dependent;
stale tests are corrected, live defects get their own rows, environment-dependent tests are
tagged so an include cannot drag them into a run that cannot satisfy them; and the set is
wired into something that runs it — a sprint case or a CI job with the worker available —
so it cannot rot invisibly again. Until then it is a **known-red gate named with this ticket
ref** in packets, not re-triaged each time.

`Source: BL-042 done-check, off-territory, 2026-07-23. Baseline captured on a clean tree.`

**Status 2026-07-25, after BL-050/055/056 (`9871059`):** `requires_worker` is **6 failures**
(951 tests / 65 excluded), down from 11 — and **stable across two consecutive runs with identical
membership**. The four MCP failures and `RunOverlayTest` are gone. Residual, each named:

| Cause | Count | Ticket |
|---|---|---|
| stale `pwd` allowlist | 3 | BL-048 (this row) — the last strand actually owned here |
| `McpHttpTest` — `port_close` in an `on_exit` cleanup | 1 | environment |
| `McpGithubTest` — the server now spawns fine; the agent did not choose to call an MCP tool | 1 | LLM-behaviour integration test, not containment |
| `OverlayAutonomousTest` | 1 | **not BL-050** — see below |

**`OverlayAutonomousTest` is a different defect wearing BL-050's clothes.** It fails with a
byte-identical message before and after the reorder. Root cause: `supervisor.ex:62` starts **no
worker at all** for `provider: "stub"` with empty `mcp_servers`, so that run never mounts an
overlay and the probe cannot land in `upper/`. Diagnosed rather than assumed fixed, and left with
BL-048 rather than silently claimed by BL-050. It needs its own decision — the test asserts overlay
behaviour for a configuration that by design has no worker.

**Zero real SIGSYS remain.** The only `worker_crashed, 159` lines in the capture are
`verify_worker_lifecycle_test.exs` stopping workers with that reason deliberately.

**Status 2026-07-25, after BL-043:** `requires_worker` reports **11 failures** (940 tests / 65
excluded) at harness `515a4ab`, and **SIGSYS is down 8 → 4**. BL-043 corrects this row's
third bullet twice over: the nine residuals were never "network/credential-dependent integration
tests", and they were never *one* cause either. They are now:

| Cause | Count | Ticket |
|---|---|---|
| stale `pwd` allowlist | 3 | BL-048 (this row) |
| MCP-stdio spawn vs. the deliberate `execve` exclusion (SIGSYS) | 4 | **BL-055** |
| overlay (`RunOverlayTest`, `OverlayAutonomousTest`) | 2 | BL-050 / BL-054 slot |
| external service — `httpbin.org` returning 503, and `McpHttpTest`'s `port_close` cleanup | 2 | genuinely environment-dependent |

The `httpbin` one is worth reading closely: it now fails on a real **503 from the live host**,
where before it died of SIGSYS. That is the repair working — the request reaches the internet.

**Status 2026-07-25, after BL-053:** `mix test --include requires_worker` at harness
`915d582` reports **12 failures** (was 15; 934 tests / 65 excluded). The fs_hash strand
is closed. Remaining: pwd ×3, SIGSYS/BL-043 ×8, and **one load-sensitive flake** — the twelfth
slot is not stable. In the BL-053 run it was `RunHelpersTimeoutTest` "a status change alone
counts as activity" (a 300 ms inactivity window, 10/10 green in isolation); in the diagnosis run
it was `RunOverlayTest` (BL-050). Both are races that surface only under the full suite's load.
Filed as **BL-054** so the twelfth slot has a name rather than being met as a first sighting each
time (the BL-051 lesson).

---

### BL-050 — `RunOverlayTest` races the worker handshake: overlay dirs are created *after* `ready` (#TBD)
**Size:** S · **Priority:** medium-low · **Section:** Harness (aetheris/)

`run_overlay_test.exs:38` asserts `File.dir?(upper)` immediately after `Client.start_link`
returns. `start_link` returns as soon as the worker's `ready` handshake arrives
(`client.ex`, `init/1`), but the worker writes `ready` at `main.rs:71-74` and only *then*
runs `sandbox::mount_overlay` (`main.rs:79-94`), which is what creates `upper`/`work`/`merged`
(`sandbox.rs:242-244`). The test therefore synchronises on a handshake that does not cover
the side effect it asserts.

The test's own comment — "always created by the Rust worker before attempting the mount" — is
true and is not the issue: both the creation and the mount happen after `ready`.

**Latent since BL-042**, which moved namespace entry (and with it the `ready` write) ahead of
the rest of init so the handshake could carry `network_namespace`. The reorder was correct and
is not in question; this test was left synchronising on the old ordering.

**Load-dependent, which is why it reads as flaky.** It passes in isolation (3/3), passes
under `--trace` (`max_cases: 1`), and fails 5 times in 8 seeds when run after a module that
starts several workers in quick succession:

```
seed 1: 4 tests, 0 failures      seed 5: 4 tests, 0 failures
seed 2: 4 tests, 1 failure       seed 6: 4 tests, 1 failure
seed 3: 4 tests, 1 failure       seed 7: 4 tests, 1 failure
seed 4: 4 tests, 0 failures      seed 8: 4 tests, 1 failure
```

**Not caused by BL-049, demonstrated rather than asserted.** With BL-049's `lib/` changes
applied and its two new test files removed from the run, `mix test --include requires_worker`
produces a **byte-identical failing set** to the clean tree (907 tests, 14 failures, same
names). With the new test files present the set gains only this one entry (921 tests, 15
failures) — they add worker churn ahead of it, they do not change what it exercises.

**Done when:** the test waits for the condition it asserts rather than for `ready` — poll for
the directory with a deadline, or have the worker report overlay establishment in the
handshake the way BL-042 made it report `network_namespace`. The second is the better shape
and is the same argument BL-042 made: a worker that announces itself ready before its setup
exists leaves the BEAM no way to tell setup from its absence. Prefer it if the handshake is
being touched anyway; the poll is acceptable otherwise. Do **not** add a `Process.sleep`.

`Source: BL-049 done-check, off-territory, 2026-07-24. Mechanism read from main.rs/sandbox.rs
at 9d994fd; non-causation demonstrated by a three-way run (clean / lib-only / full).`

---

### BL-051 — One unidentified `mix test` failure, and the capture discipline that lost its name (#TBD)
**Size:** XS · **Priority:** low (capture fix) / unknown (the flake itself) · **Section:** Harness (aetheris/)

A single `mix test` run at `c80a8e4` (BL-049 r1) reported `921 tests, 1 failure, 122 excluded`.
**Nine consecutive runs before and after were `0 failures`**, and the default suite has not
otherwise been red on this branch. The failing test cannot be named: the gate command piped
through `tail -2`, keeping the summary line and discarding the failure block.

**The nameable defect is the capture, not the flake.** This is the Complete-output rule
failing in its most ordinary form — a summary line preserved, the detail that made it
actionable thrown away — and it cost the one occurrence that would have identified the test.
BL-016 and BL-020 are the same class on counts; this is the class on failure identity.

**Not attributed to BL-049.** The r1 diff is a test, a `@doc false` seam, and comments — no
runtime behaviour change — and the r0 diff had nine clean default-suite runs across the
cycle. But attribution is *unknown*, not *cleared*, and this row says so rather than assuming
the comfortable answer.

**Rerun burst (r2 suggestion, run at `c80a8e4`+r2 notes): 20 of 20 clean** (`921 tests, 0
failures` each). BL-049's default-suite additions are pure and deterministic
(`VolatileMetadataTest`, `async: true`, no worker; the verdict/effects tests are
`:requires_worker`, excluded from default `mix test`), so a flake in them would be a real
ordering/async defect rather than env noise — and none surfaced in 20 runs. That is evidence
toward "pre-existing / env, not BL-049's", **not** proof: the original occurrence still has no
name, and one clean burst cannot clear a one-in-thirty-odd intermittent. Attribution stays
*unknown*. The capture-discipline fix below is what actually closes this; the burst just lowers
the prior that BL-049 introduced it.

**Done when:** gate runs capture full test output to a file (summary *and* failure blocks) so
a single occurrence is identifiable — this is a habit fix, not a code fix, and belongs in
whatever runs the gates; and if the flake recurs with a name, it gets its own row with a
mechanism. Until then this row exists so a second sighting has something to attach to rather
than being met as a first sighting again.

`Source: BL-049 review r1 done-check, 2026-07-24. Observed once at c80a8e4; unreproduced in 9
subsequent runs, then 0/20 in a dedicated r2 burst (29 clean total); name lost to a truncated
capture.`

---

### BL-045 — `RunConfig mode: :verify` is a misnomer: no verification semantics (#TBD)
**Size:** S · **Priority:** low · **Section:** Harness (aetheris/)

After BL-025 routed `aetheris verify` through `Aetheris.Execution.Verifier`, nothing in the
harness treats `mode: :verify` as verification. The mode does exactly two things — skip
context trimming (`loop.ex:409-411`) and skip pre-tools (`pre_tools.ex:59`) — and is
otherwise a normal **live** run: live model calls, live tool execution, no comparison against
any record.

**This is not a BL-033-shaped deletion.** BL-033 removes `:fork` from the same union because
it is unused; `:verify` is *still reachable* — from agent-file config
(`run_helpers.ex`, `normalize_config_value(:mode, …)`) and from eval task templates
(`eval/runner.ex:298`). The defect is naming, not deadness: a config author writing
`mode: "verify"` reasonably expects verification and gets a live run. That mis-expectation is
precisely what let the CLI diverge from determinism-contract §3 unnoticed for the life of the
doc (BL-025 §3 edit separates the two by name).

**Scope note:** this is the `RunConfig` **mode** union (`run_config.ex:115`), *not* the
event-type union (BL-040). Conflating those two is a recorded sketch-failure; keep them apart.

**Done when:** the mode is renamed to what it does (e.g. `:replay_context`) with its two
call-site parsers updated, or kept with a docstring stating it performs no verification —
decided, not left ambiguous.

`Source: BL-025 execution, rev-2 adjacent finding, 2026-07-23.`

---

## boxy-pipeline

### BL-010 — Clean order_formatter output: strip extra sheets and clear stale template formulas (#51)
**Size:** S · **Priority:** now

Two output defects observed on first real run:

1. **Extra sheets in output xlsx.** `--template` and `--catalog` point to the
   same file (`Updated_Boxy_MSRP_Sales_Order_Form.xlsx`), which contains all
   five `{N}000 Price List` and `{N}000 Order Form` sheets. openpyxl loads and
   saves the whole workbook, so the output carries all those sheets. Only
   `2000 Order Form` should be in the output file.

2. **`#NAME?` errors in unused template rows.** The template has VLOOKUP
   formulas pre-filled in rows 12–67. The formatter writes items into rows
   12–N, but rows N+1 through 67 retain the original VLOOKUP formulas. When
   openpyxl saves the workbook, named-range references in those formulas break,
   producing `#NAME?` errors visible in Excel.

**Fix (both in `scripts/order_formatter.py`):**
- After loading the template workbook, delete all sheets except `2000 Order Form`.
- After writing all line items and fee placeholder rows, clear all cells in
  columns B–K (cols 2–11) for rows `(last_written_row + 1)` through `67`. Set to `None`.

**Touches.**
- `scripts/order_formatter.py`
- `tests/test_order_formatter.py` — add tests: output has exactly one sheet;
  no `#NAME?` errors beyond last written row (`@pytest.mark.integration`)
- `docs/runbook.md` — update §"Understanding the output": rows beyond fee
  placeholders are now blank, not VLOOKUP

**Do not generate.**
- Changes to any other script
- Changes to `schema.py`

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_order_formatter.py -v
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2 \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('output/Joey_Kitchen_V2_order_form.xlsx')
print('Sheets:', wb.sheetnames)
assert wb.sheetnames == ['2000 Order Form'], 'Expected exactly one sheet'
ws = wb.active
errors = [(r, c, ws.cell(r,c).value) for r in range(31,68) for c in range(1,12)
          if ws.cell(r,c).value and '#NAME?' in str(ws.cell(r,c).value)]
assert not errors, f'#NAME? errors found: {errors}'
print('OK — one sheet, no #NAME? errors')
"
```

**Claude-code prompt.**
> Fix two output defects in `scripts/order_formatter.py` per
> `docs/backlog-2026-06.md §BL-010`.
>
> 1. After loading the template workbook with openpyxl, delete all sheets
>    except `"2000 Order Form"` before writing any data.
> 2. After writing all line items and fee placeholder rows, clear all cells
>    in columns B–K (cols 2–11) for rows `(last_written_row + 1)` through
>    `67` by setting each cell's value to `None`.
>
> Update `tests/test_order_formatter.py`:
> - Unit test: output workbook has exactly one sheet named `"2000 Order Form"`.
> - Integration test (`@pytest.mark.integration`): no cell in rows 31–67
>   contains a string with `"#NAME?"` after a full pipe run.
>
> Update `docs/runbook.md` §"Understanding the output": replace the note
> about rows 42–67 retaining VLOOKUP formulas with a note that all rows
> beyond the fee placeholders are blank.
>
> Run the done-check from §BL-010 and include actual output (including the
> Python verification snippet result) in your review packet.

### BL-011 — Extract shared parsing helpers into `scripts/parsing_utils.py` (#52)
**Size:** S · **Priority:** before next catalog/resolver change

`_parse_dimensions`, `_extract_cabinet_type`, `_parse_color_columns`, and
`_color_name_from_header` are duplicated verbatim between
`catalog_resolver.py` and `catalog_extractor.py` (noted in t1 review,
m-boxy-pipeline-1a). A bug fix in one won't propagate to the other.

**Fix:** extract all four helpers into `scripts/parsing_utils.py`; import
from both scripts. No logic changes — pure refactor.

**Touches.**
- `scripts/parsing_utils.py` (new)
- `scripts/catalog_resolver.py` (import from parsing_utils; remove local copies)
- `scripts/catalog_extractor.py` (import from parsing_utils; remove local copies)
- `tests/test_parsing_utils.py` (new — move or copy the relevant unit tests
  from `test_catalog_resolver.py` and `test_catalog_extractor.py`)

**Do not generate.**
- Any logic change to the helpers
- Changes to `schema.py`, `main.py`, `order_formatter.py`, `plan_extractor.py`

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/ -v
# All existing tests must pass unchanged
# parsing_utils.py must be the only location of the four helpers
grep -rn "_parse_dimensions\|_extract_cabinet_type\|_parse_color_columns\|_color_name_from_header" \
  scripts/catalog_resolver.py scripts/catalog_extractor.py
# Expected: only import lines, no function definitions
```

**Depends on:** BL-010 merged (clean baseline before refactor)

---

### BL-012 — Catalog enrichment merge strategy (#53)
**Size:** S–M · **Priority:** before anyone enriches `catalog.jsonl`

`catalog_extractor.py` currently overwrites `catalog.jsonl` on every run.
Once `mapped_20_20_codes` or `notes` fields are manually populated, a
re-extraction would silently discard all enrichment. No merge logic exists.

**Design options (decide before implementing):**

**Option A — Merge on re-extraction.** If `catalog.jsonl` already exists,
read it first, build a `{sku → enrichment}` index, then re-extract from
Excel and carry forward non-empty `mapped_20_20_codes` and non-None `notes`
from the existing file. Write the merged result.

**Option B — Separate enrichment file.** Keep `catalog.jsonl` as a
pure extraction artifact (always overwritable). Store enrichment in a
separate `data/catalog-enrichment.jsonl` keyed by SKU. The resolver merges
at load time. Enrichment file is committed (it's hand-maintained, not
generated).

**Option C — Versioned files, no overwrite.** `catalog_extractor.py` always
writes `catalog-{YYYY-MM-DD}.jsonl`; never overwrites. `catalog.jsonl` is a
symlink or a manually updated pointer. Enrichment lives in the dated file and
is carried forward manually when updating.

**Recommendation:** Option B. Cleanest separation of concerns — extraction
is always safe to re-run; enrichment is a human-maintained artifact that
belongs in git. The resolver's `load_catalog_jsonl` merges the two at load
time (after t3 lands).

**This ticket requires a design decision before implementation.** Capture the
chosen option and rationale in `docs/m-boxy-pipeline-1a.md §Enrichment
strategy` before handing to claude-code.

**Depends on:** m-boxy-pipeline-1a t3 merged (resolver reads JSONL)

---

### BL-013 — Parameterise column x-boundaries in `so_extractor.py` (#54)
**Size:** S–M · **Priority:** before processing a second SO PDF

`so_extractor.py` has four hardcoded x-boundary constants (`_QTY_X_MAX`,
`_SPECIAL_X`, `_RATE_X`, `_AMOUNT_X`) calibrated from SO86708_Aria_Joey.pdf.
A different Boxy SO template (different page margins, font, or column widths)
could shift columns enough to mis-assign words to the wrong column bucket.

**Fix:** detect column boundaries dynamically from the table header row
(`Quantity`, `Item`, `Special`, `Rate`, `Amount`) on the first page, rather
than using hardcoded constants. Use the header word x0 positions plus a
configurable margin to compute the bucket ranges at runtime.

**Touches.**
- `scripts/so_extractor.py` — replace four constants with a
  `_detect_col_bounds(page)` function
- `tests/test_so_extractor.py` — add unit test for `_detect_col_bounds` using
  a minimal mock page

**Do not generate.**
- Changes to `schema.py` or any other script

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
python3 -m pytest tests/test_so_extractor.py -v
# SO86708 extraction must still produce 34 items, $8,099.54
python3 scripts/so_extractor.py \
  --so data/samples/SO86708_Aria_Joey.pdf \
  --project joey --output-dir data/projects/
```

---

### BL-014 — Parse Bill To and Ship To addresses separately in `_parse_header` (#55)
**Size:** S · **Priority:** low (before multi-customer use)

`so_extractor._parse_header` currently sets both `bill_to` and `ship_to` to
the customer company name (extracted from the first line of the address block).
The `SOHeader` schema has distinct fields for a reason: real SOs may bill to
one address and ship to another. SO86708 happens to use the same company name
for both, so the approximation is invisible in the done-check.

**Fix:** use word x-coordinate extraction on the address block (the three
columns below "Bill To | Ship To | Customer") to separately capture the Bill
To address (x < ~200) and Ship To address (~200 < x < ~370), including
multi-line street/city/state/zip.

**Touches.**
- `scripts/so_extractor.py` — extend `_parse_header` with coordinate-based
  address block parsing
- `tests/test_so_extractor.py` — add integration tests: `bill_to` contains
  "Brokaw" (the SO86708 bill-to street), `ship_to` contains "Laurel"

**Do not generate.**
- Changes to `schema.py` or any other script

---

## Suggested order

| Order | Ticket | Why first |
|-------|--------|-----------|
| ✔ | BL-001, BL-015, BL-002 | **Done 2026-07-15.** Baseline captured (`d24e482`); six canonical payload fields promoted to specs §6; repos rule added to root `CLAUDE.md` and the manifest regenerated. The BL-015-before-BL-002 ordering held — one export caught the §6 promotions |
| 2 | BL-010 | First real run revealed output defects; fix before next client demo |
| ✔ | BL-003 | **Done 2026-07-15.** `Aetheris.Sweep` ships the cure: startup hook (gated by `:sweep_on_start`, default on) plus `mix aetheris sweep`, and a new `run_orphaned` event type. 76 orphaned `running` rows cured (66 orphaned / 10 reconcilable) |
| ✔ | BL-005 | **Done 2026-07-15.** `TrajectoryView` falls back to `harness_get_events` + `harness_get_run` on `trajectory_load` failure and rebuilds the step-grouped view via `src/lib/reconstructTrajectory.ts`. That fallback is the path BL-030 r1/r2 later built the live completion transition on |
| ✔ | BL-009 | **Done 2026-07-15.** `drift_check.py --strict` exempts `project_knowledge` staleness via a `strict_exempt` flag on `record` — only the staleness WARN at the manifest-comparison site; structural pk WARNs still fail |
| 6 | BL-011 | Refactor before more scripts share the helpers |
| ✔ | BL-004 | **Done 2026-07-20.** `total_input_tokens` / `total_output_tokens` added to `RunSummary` as correlated subqueries mirroring `total_cost_usd`, surfaced in the Cost cell tooltip (table stays at 8 columns) |
| 8 | BL-012 | Design decision first; implement after 1a t3 merges |
| 9 | BL-013 | Needed before testing a second SO template |
| 10 | BL-014 | Low-effort address fix; do with BL-013 pass |
| ✔ | BL-007 | **Closed 2026-07-20.** All three sketched pieces exist: `fork_run` (`rig/src-tauri/src/commands/fork.rs`), the `useFork`/`TrajectoryView` frontend path, and the `specs.md` §4 entry. Its §7 promotions are in the root `CLAUDE.md`; BL-030 continued this surface |
| 11 | BL-008 | Milestone-sized; docs-first per repo convention. **Row split 2026-07-26** — BL-007, previously ranked here with it, closed 2026-07-20; this half is still open |
| ✔ | BL-029 | **Done 2026-07-20** (`c39bf7e`). Both queries read `runs.label` with the `COALESCE(…, run_id)` fallback retained. Measured at the fix: 878 runs, 596 labelled, **0** with a label in `config_json` |
| ✔ | BL-028 | **Done 2026-07-21** (`9b2b102`). Read-side fix in `event_to_messages(:tool_result)` plus `normalize_content/1` (nil → `""`, non-binary → JSON-encoded, per contract §2's string invariant) |
| ✔ | BL-031 | **Done 2026-07-21.** Inactivity bound on `{status, max_event_seq}` with a paused-run exemption via `Aetheris.RunPause` (shared with Sweep by construction); config key `:await_inactivity_timeout_ms`, default 300 000. BL-030's fork-start emit later measured against its 200 ms poll floor |
| ✔ | BL-025 | **Done 2026-07-23.** Grew in-cycle to include the CLI rewire (it never reached `Verifier`). Spawned BL-042/043/044/045 |
| ✔ | BL-042 | **Done 2026-07-23.** Grew in-cycle by one tool: `run_command` was never re-executed under verify at all (`unknown_tool`), so the netns had nothing to contain until the routing was fixed. Spawned BL-047 (the `git_*` half of that gap, plus its taxonomy question) and BL-048 (the red `requires_worker` set found off-territory) |
| ✔ | BL-047 | **DONE (impl) 2026-07-24** — implementation landed; **§5/§3 edits pending §8 ratification**, per the section's own heading. Ticked for the implementation, not for the doc half, which is the open remainder |
| ✔ | BL-049 | **DONE 2026-07-24.** Direction chosen: the third of the row's three options — stop returning timing inside the compared payload, the one matching the existing worker-native shape |
| ✔ | BL-038 | **Done 2026-07-25** (`c0977c2` + F1 `e4baddf`; GUI merge gate green, 500 of 896). Scope narrowed in-cycle to server-side search only — no client-side filter, no pagination — because two filtering paths can disagree. BL-024 (19b) inherits the find-run-by-id primitive as intended: a server-side `label`/`run_id` LIKE reaching the whole store, which a window-scoped client filter could not have been. Spawned BL-058 |
| 22b | BL-058 | Same surface as BL-036 (check 9) one section down. Do with or after BL-035/BL-036 cleanup; decide §5's scope rule before writing the check |
| ✔ | BL-039 | **Done 2026-07-26.** Harness `ebc3878` (docs-first §4 + §2 and runbook echo sweep), `e44d35c` (implementation), `3f561d9` (notes); agents `7d6013a`. Design A as ratified. Spawned BL-061 |
| 15d | BL-059 | Independent of BL-039 and **not** batchable with it (BL-039 forbids record-path changes). If disposition (a) lands first, BL-039's positional pairing must be revisited before it is written; if BL-039 lands first, its §4 clause already names this as the dependency to update |
| 15e | BL-065 | Same family as 15d and the same class: a record-path Silent-wrong-answer, where a failed trajectory write still reports the run `done`. Independent of the fork chain and cheap (S). Do it while the record path is already open — and note BL-030's completion transition currently *relies* on terminal-status-≠-file-exists, so the fix must keep that degradation correct rather than assume the file is now guaranteed |
| ✔ | BL-030 | **Done 2026-07-26** (harness `ae0c510`+`f79365a`, agents `b5e8eee`..`06b333e`; GUI merge gate green on both tabs). Three rounds: r0 early-return, r1 completion transition (folded BL-063), r2 source-seeded selection after r1's fix missed an Adjacent-case consumer. Both scouts changed the mechanism — the CLI must keep blocking (the run is a Task in its own tree), and the reload must gate on terminal *status*, not the `run_complete` event, which precedes the file write. Spawned BL-062, BL-064, BL-065 |
| 16a | BL-062 | Unblocked now BL-030 has landed — the split that kept BL-030 §8-free. Carries the §4 sentence correction *and* repoints its dangling `(BL-030)` ref, so the longer it waits the longer §4 cites a closed ticket for a capability it never shipped. Decide operator surface (Rig picker vs CLI-only) as part of the row, not after |
| 16b | BL-064 | **Not startable as filed** — the row is an explicit stub with no adjudicated scope. Sequenced here because it shares BL-062's seam (fork-time overrides reaching CLI and Rig) and would likely reuse its plumbing, so scoping it *after* BL-062 lands costs least. Write the scope onto the row before picking it up |
| 17 | BL-032 | Decide WAL-or-not once the fork call pattern (BL-030) settles, since that changes the contention profile |
| 18 | BL-033 | Trivial deletion, but do it after BL-024 confirms no lineage work wants the union member |
| 19 | BL-037 | Before BL-024 — the lineage view needs real-vs-fallback labels; building it first bakes in the string-comparison guard |
| 19b | BL-024 | Design-led; compose with `caused_by` rather than a fork-only index. Handle both provenance shapes |
| ✔ | BL-034 | **Done 2026-07-22.** Resolved by dropping the baseline append (human call). That append was the sole reason BL-002 wrote a manifest-tracked file other than the manifest |
| 21 | BL-035 | Do with the next frontend ticket that touches a fourth formatter site — the trigger, not the calendar |
| ✔ | BL-036 | **DONE 2026-07-25** (`11675cc`). Landed as a new check 9, `command_fields`, batched with BL-041(b) — both were `drift_check` blind spots on one file surface. `check_tauri_commands` stays names-only |
| ✔ | BL-041 | **DONE 2026-07-25** (both dispositions). (a) Convention `1013a95` — the post-commit ordering rule now in `CLAUDE.md`'s doc-sync section; (b) batched with BL-036 |
| 23b | BL-044, BL-045 | Small harness cleanups from BL-025; neither blocks anything. BL-045 is a naming decision, not a deletion — do not batch it with BL-033 |
| 23c | BL-046 | The payload-key convention, after three read-side fixes. Low priority but rising: each new reader has cost a bug. Do with the next `:tool_result` reader, not on a calendar |
| ✔ | BL-053 | **Done 2026-07-25.** Closed the fs_hash strand of BL-048: verify makes no filesystem-hash claim; §3 corrected in both cells (strike + explicit non-guarantee, **§8-ratified option B**) plus five mirrors; dead arm deleted; stability tests re-pointed at `write_file` |
| ✔ | BL-043 | **Done 2026-07-25.** Repaired (not retired): five syscalls enumerated over three probe rounds, caller-kill fixed in both its mechanisms. Cleared 4 of the 8 SIGSYS; the other 4 turned out to be a different defect → BL-055 |
| ✔ | BL-050, BL-055, BL-056 | **Done 2026-07-25 (`9871059`).** One reorder — `ready` became the fully-established barrier and now attests overlay/exec-server/seccomp/MCP. Verify refuses on a filter failure; record attests and continues. requires_worker 11 → 6, stable across two runs |
| ✔ | BL-048 | **Done 2026-07-25 (`6e2fad8`), pending the first CI dispatch.** The set is green (951/0, two runs) and wired behind a containment-attestation gate: CI runs it if the runner is capable, skips with the missing primitive named if not. If `ubuntu-latest` cannot sandbox, the sprint is the standing home and it still closes |
| 27 | BL-057 | Raised by BL-048's closeout: a stub run declaring tools starts no worker and its tool calls silently never execute. Blocks un-skipping `OverlayAutonomousTest`. A product question (what is a stub run?), not a test fix — walk the six affected files |
| — | BL-054 | Fires whenever the `requires_worker` twelfth slot flakes; the row exists so it has a name. Fold into a polling-based rewrite of the fixed-ms windows when someone is in that file |
| — | BL-052 | Fires on its trigger: the first §4 block documenting a struct defined outside `commands/`. Trivial (`rglob`) when it does; no live case today |
| — | BL-026 | Fires on its trigger: first `verify` run against a multi-agent/orb trajectory (ratified 2026-07-19) |
| ✔ | BL-027 | **Done 2026-07-23, folded into BL-025.** Its trigger was too narrow — any failed contained tool call reached the crash — and BL-025 made `aetheris verify` real, which would have shipped it. Convention residue → BL-046 |
| — | BL-006 | Fires on its own trigger |
| — | BL-075 | Fires on the next `mix test` red: capture the full output that time. Fold into BL-054 only if the name matches the twelfth-slot flake — the connection is plausible, not established |
| — | BL-077 | Blocked in practice until BL-069 is re-armed or the `expected_fail()` half is designed — flipping `fail` to a real failure today would turn every tracked known-red into a blocking one. Do the counter and the known-red declaration together, never the counter alone |
| — | BL-076 | Batch with BL-070 — same file, and BL-070's cleanup has to touch this code anyway. Do it alone if BL-070 slips: this is the one piece of the cross-provider merge that is not merely dead but actively produces a wrong month-on-month headline. t3's per-provider `--history-dir` mitigates it by convention only, so a direct `compose` call still hits it |
| — | BL-078 | Fires on its trigger: the next legitimate edit to `cloudcost/scripts/fetch_aws.py`. Exactly BL-070's shape — a duplication left alone because closing it means editing a file the current ticket froze |
| — | BL-079 | Fires when someone has a verified `ap-south-1` S3 Standard rate, or is retired wholesale by BL-072. Never close it by copying another region's number — that is the failure the omit path exists to prevent |
| — | BL-080, BL-081 | Batch: same file, same envelope, both t4 review tidy-ups. BL-080's fix is a three-way split (refused / unknown / declined-on-purpose), NOT the two-way collapse the note sketched — that would hide the genuine unknowns under `ok` |
| — | BL-082 | Sequence after BL-069 if the sprint route is chosen: that case is already known-red on its orphan assertion, and a second assertion added to a red case is a buried one |
| — | BL-083, BL-084 | Batch: both are "the list/manifest was written once and four use cases arrived since". BL-084 sequences before BL-085 — declaring env in the manifest renders the config rows for free, so doing 085 first duplicates work in agentConfigDefs.ts |
| — | BL-085 | ~~The only one of the four with unresolved design. Peel into its own small milestone IF open question 2 resolves to "Rig needs a launch-parameter concept"~~ **Resolved 2026-08-04: the trigger did NOT fire.** `extra_env` (`orchestrate.rs:13,57-66`) + the shipped "Additional env vars" panel already carry a per-launch value that wins over global config and persists nowhere — the premise "a per-launch value has no home" was false. Landed docs-only on the existing door; the *direct/non-LLM* door peeled to BL-094 |
| — | BL-094 | The half of BL-085 that did peel. Blocked on a correctness defect, not a design gap: `mix run` on a config-style `.exs` exits 0 having created no run. Do the discriminator before the UI |
| — | BL-086 | Independent, pure frontend, retroactive. Do whenever someone is in TrajectoryView |
| — | BL-073 | Rescoped 2026-08-03 to minimal ("View report": scrape the path from the render step's tool_result, open external/sandboxed). Independent drop-in; pairs thematically with BL-085 (launch-from-Rig + view-report-in-Rig) but does not depend on it — a CLI-launched run's report views the same way. The rich inline render is a separate milestone and is this batch's scope-creep magnet |
| — | BL-087 | Do whenever someone is in payslip. Carried `xfail(strict=True)` by `tests/test_tools_manifests.py`, so it cannot rot silently — but the marker must be deleted in the fixing commit or the suite fails on the unexpected pass |
| — | BL-088 | Fires when an import-only module's Run button actually costs something. It does not today: `_normalized.py` has no `__main__`, so running it is a no-op. Enumerate the whole import-only class (docbuilder ×3, eduloka ×8, drive ×1) when it lands — BL-084 noticed one, which is an observation, not a census |
| — | BL-089 | The Decision-A sweep. Carried xfail(strict) by tests/test_tools_manifests.py per use case; each landing deletes its NO_MANIFEST_YET entry in the same commit |
| — | BL-090 | Regenerate the matrix, don't hand-edit — it's generated. Pure staleness; reconcile the detect_optimization_signals cell to the BL-084 manifest wording at regen |
| — | BL-091 | Wider than cloudcost (api's 16 keys already affected). Decide masked-key export policy when fixing |
| — | BL-092 | Makes the discarded BL-084 round-trip permanent. The offline guard the pytest suite structurally cannot be |
| — | BL-093 | XS doc fix, but decide the mechanism (describe both, or move the payslip rows out of static defs) — it is the payslip half of the question BL-085 answered for cloudcost |
| — | BL-095 | Live secret exposure in the payslip plan card today. Fix with the `masked` flag or the `ToolDetail` set/unset dots; pairs with BL-091 as the "masked-key policy" pair |

### BL-098 — The inventory envelope has no extras key, so adapter run-metadata dies at stdout (#TBD)
**Size:** M · **Priority:** medium · **Section:** aetheris-agents (`cloudcost/`)

Filed 2026-08-05, from m3-cloudcost t1 review r0 F3 / r1 F5. An adapter's run metadata —
`not_inventoried`, `surveyed`, `undetermined`, `warnings`, `exclusions`, `duration_ms` — is emitted
only on the CLI summary and is lost when the process exits. It never reaches
`compose_report_data.py` and so never reaches the rendered report.

**Not a Linode regression.** `fetch_aws.py` behaves identically: `"warnings"`, `"errors"` and
`"regions_swept"` each occur exactly once in that file, in its own stdout summary
(`fetch_aws.py:1113-1128`). This is the established behaviour of the use case, surfaced by m3
rather than introduced by it.

**Why it was not fixed in m3.** The **cost** schema sanctions `provider_extra`, but the m1
**inventory** schema has no extras key at all (`provider`, `account`, `period`, `resources`,
`generated_at`), so there is no contract-sanctioned home on the inventory side. Adding one is a
§Normalized change, and it is **not free**: §Normalized's emit-with-a-real-value-or-`null`
rule (never by omission) would oblige `fetch_do.py` and `fetch_aws.py` to emit the new key too,
so the extension touches all three adapters at once. Doing that inside the milestone whose entire
purpose is proving §Normalized does not change would confound the proof — which is exactly why it
is filed rather than done.

**Mitigated, not open-ended.** m3 t1 made `not_inventoried` non-empty fail the run (`status:
partial`, exit 1), so a class going UNKNOWN now stops the pipeline rather than producing a report
with a quiet hole. That is louder than a JSON field no consumer currently reads, and it is why this
row is medium rather than high.

**The sharpest concrete instance — the artifact least able to justify itself is the one that most
needs to.** `provider_extra.period_basis` records what backs a Linode snapshot's `period` label,
but it lives on the *cost* document, where its value is necessarily `invoice-covered`. The two
values that mean "this label is NOT invoice-confirmed" — `requested` and `fallback-current-month`
— arise only on runs that emit **inventory alone**, and the inventory envelope has no
`provider_extra` to carry them. So the artifact whose `period` is least trustworthy is precisely
the one that cannot record why.

Not reachable by any consumer today: such a run is `partial` with exit 1, and the pipeline stops
before a report exists. That behavioural guard is what holds this at medium — and it is the first
thing to revisit if a future change ever lets a partial run continue, because the gap becomes live
the moment it does.

**Done when:** the §Normalized inventory envelope carries a sanctioned extras key, ratified
doc-first per m3 §D-C (section-scoped edit applied against HEAD and diffed by the arbiter, before
any adapter emits it); all three adapters emit it; `compose_report_data.py` carries it through; and
the report surfaces "this class could not be assessed" distinctly from "this class is empty".

**Sequence after** BL-070 / BL-076 / BL-078 if any of those is opening `compose_report_data.py` or
`fetch_aws.py` anyway — this touches both.

`Source: m3-cloudcost t1 review r0 F3, r1 F5 (2026-08-05).`

---

### BL-099 — The sprint's D2 credential grep is AWS-only, so two providers' D2 posture is asserted rather than checked (#TBD)
**Size:** S · **Priority:** medium · **Section:** aetheris-agents (`../aetheris/scripts/sprint.sh`)

Filed 2026-08-05, from m3-cloudcost t3 review r0 F1. The cloudcost sprint case greps the run
output for the live credential — the D2 trajectory half — inside
`if [[ "$CC_PROVIDER" == "aws" ]]` (`../aetheris/scripts/sprint.sh:2670`). So on the **Linode**
and **DigitalOcean** legs no assertion covers m3 §Done-when 7 (`CLOUDCOST_LINODE_TOKEN` appears in
neither stdout, stderr nor the trajectory), and the DO equivalent has never had one at all.

**A provider whose credential is never grepped has a D2 posture that is asserted rather than
checked.** A green Linode or DO sprint says nothing about credential leakage; it says the run
finished. That is the gap, and it is invisible because the leg is green either way.

**The fix is the same shape as the strip t2 already landed.** t2 extended `CC_HERMETIC` to Linode
by taking the strip list from `fetch_linode.SHADOWING_ENV` rather than hand-typing it, so the
prefix and the adapter cannot drift. The D2 grep wants the same treatment: select the credential
variable from `$CC_PROVIDER` and grep for *that*, keeping the existing gate on the searched file
demonstrably having content and a `run_id` — a grep over an empty file is the classic vacuous
pass, which is why the AWS arm already carries that guard.

**Add the control the AWS arm lacks.** t3 ran the Linode arm by hand with an explicit anti-vacuity
check — the same `grep -qF` against a file constructed to contain the token **does** find it — so
a clean result is the grep working rather than the grep being incapable of matching. Without it,
a credential whose shell-quoting or encoding differs from what `grep -qF` sees would report clean
forever. Land that control with the generalisation, not after it.

**Why it was not fixed in m3 t3.** `sprint.sh` is in §t2's Touches, not §t3's; t3 found it while
satisfying done-when 7 and could not edit the file. This is the second Linode-shaped defect in
that file found by a ticket that could not fix it — t1 found the wall-clock report filename and
t2 fixed it.

**Done when:** the credential grep runs on every provider leg against that provider's own
credential variable; the file-has-content-and-a-run_id gate is preserved; an anti-vacuity control
proves the grep can match; and the mutation posture is recorded (a run output seeded with the
credential must fail the assertion).

`Source: m3-cloudcost t3 §3.3, t3 review r0 F1 (2026-08-05).`

**DONE 2026-08-06 (m4 t3).** Every Done-when clause discharged.

- **The grep runs on every provider leg against that provider's own credential variable.** It sits
  outside any provider gate now. The names are **selected from the adapter that reads them** —
  `TOKEN_ENV` / `ACCESS_KEY_ENV` / `SECRET_KEY_ENV` / `SESSION_TOKEN_ENV`, the same treatment t2
  gave `CANONICAL_TYPES` — so a hand-typed copy cannot drift, and the grep, the survival arm and
  the poison control need no per-provider edit. (The bridge's provider→module map and the
  credential preflight `case` do still take an entry per provider; both fail loudly if missed.)
  Region constants are deliberately not selected: they are not secrets and their values
  legitimately appear in the report, so grepping for them would fire falsely.
- **The file-has-content-and-a-run_id gate is preserved**, per file.
- **An anti-vacuity control proves the grep can match.** The same matcher runs first against a
  file constructed to contain the credential and must find it, else `fail`. The file is
  `mktemp`-derived, mode `600`, and removed unconditionally by trap.
- **The mutation posture is recorded**: a run output seeded with the live credential produced
  `[FAIL] CLOUDCOST_DO_TOKEN appears in run.json — D2 violated`; a bait file built without the
  credential produced `[FAIL] D2 anti-vacuity FAILED …`. The seeded capture was located by content
  and deleted, and every other capture swept clean.
- **Decision 15 honoured:** the searched-file set is the array `CC_D2_FILES`, not an inline path,
  so covering `run.err` if the harness round splits the streams is one entry rather than a rewrite.

**Observed on the leg this row was filed about:** the DigitalOcean leg now prints
`[OK] no CLOUDCOST_DO_TOKEN in run.json (searched a file with content and a run_id)`. Before this
ticket that leg had no D2 assertion at all and was green either way — which is exactly the
asserted-rather-than-checked posture the row names.

`Source: m4 t3, 2026-08-06 — landed with BL-104 in one pass; the two interact.`

---

### BL-100 — the sprint's `--json` reads fail unpredictably; the status line prints a fallback token when they do (#TBD)
**Size:** S–M · **Priority:** low-medium · **Section:** aetheris-agents (`../aetheris/scripts/sprint.sh`)

> **Rescoped and corrected 2026-08-06 (t1a).** Three changes, each recorded rather than silently
> applied. **(1) The causal claim below is false.** `2>&1` is not why the reads fail: the
> harness's **Logger output shares stdout with the payload**
> (`mix aetheris --json list --limit 1 2>/dev/null` emits both; `… 2>&1 >/dev/null` emits
> nothing), so the merge is irrelevant to parseability. Whether `[sandbox]` lines go to stdout or
> stderr is **not established** — that command spawns no worker. **(2) Stream splitting is not
> sufficient**: it cannot restore parseability in any environment where the harness emits Logger
> output on stdout, which is every capture in this repo from 2026-07 onward. Whether it sufficed
> earlier depends on `[sandbox]` routing, which is unestablished — *not* a claim that it could
> never have worked. **(3) The subject is not "broken reads" but reads whose success depends on
> ambient run-store state.** Identical expressions succeed or fail by environment — by store
> state, by harness version, and by whether a worker ran; see `claude-notes.md` for which line
> does which. News captures
> parse in 4 of 4, payslip fails in 8 of 8, cloudcost fails in 10 of 10 — same helper, same
> redirect. Non-determinism is the defect, and it is why fixing this makes the reads
> *deterministic* rather than "makes every read work". Size raised XS → S–M to match. The
> original text below is left intact **except where marked `[corrected 2026-08-06]`** — this is an
> open row, so the paragraphs someone would act on are corrected rather than merely annotated.

Filed 2026-08-05, from m3-cloudcost t3 review r0 F1. The cloudcost case's inline run redirects
`2>&1` into `run.json` (`../aetheris/scripts/sprint.sh:2571-2572`), so the harness's boot warnings
and the two `[sandbox]` lines are prepended to the `--json` document. `jq -r '.status // "unknown"'`
cannot parse the result and falls through its `||` to the literal `no-json`, which is what the
`[OK]` line prints:

```
[OK]    uc-cloudcost orchestrator → no-json (695 bytes)
```

The JSON payload is intact on the last line
(`{"label":"Cloudcost · Linode","status":"done","run_id":"cloudcost-orch-linode-h5lltQ"}`), and the
**assertion** is the surrounding `if` on exit status rather than the `jq`, so nothing is
mis-asserted and no check is vacuous. This is a display defect only.

**Its cost is a signal nobody will read when it finally matters.** A status field that reads
`no-json` on every run trains every reader to skip it, so the one run where the status is genuinely
interesting — `partial`, `error`, a status the exit code does not distinguish — reports it into a
line already classified as noise. That is the same reflex the standing gate rule names for a
known-red note that never changes.

**`[corrected 2026-08-06]` That justification is not achievable by this row alone.** The payload's
`status` can only ever read `done`: `handle_run_status/5`
(`../aetheris/lib/aetheris/cli/commands/run_helpers.ex`) returns `{:ok, %{… status: :done}}` for
`"done"` and `{:error, …}` for `"failed"`/`"cancelled"`, and the formatter's error branch
(`../aetheris/lib/aetheris/cli/output/formatter.ex`, `def print({:error, reason}, _mode)`) ignores
the output mode and emits no JSON at all. So `partial`/`error` never reach the line. Fixing this
row stops the display asserting something false and makes the read deterministic; recovering the
*signal* requires the sibling harness row on the `--json` failure contract.

**Provider-independent and pre-existing.** The redirect is not in any provider branch, so DO, AWS
and Linode are all affected, and have been since the case was written (m1 t5). m3 t3 surfaced it
rather than introducing it.

**`[corrected 2026-08-06]` Scope — the class, not the one line.** This row was filed against the
cloudcost case's status line. The same expression appears at four sites in `sprint.sh` — the `ok`-line reads inside
`run_agent()` (`:53`) and `run_orb()` (`:70`), the chaos case's gate extraction (`:297`), and the
cloudcost case's inline orchestrator line (`:2573`) — and the same root cause reaches eight further reads (`.run_id` ×6, `.orb_id`,
`extract_step_count`). **The chaos site is a gate, not a display line**: its operand feeds
`[[ "$status" == "done" ]]`, so when the read fails the assertion cannot match. Two sites already
carry ad-hoc `grep` workarounds (docbuilder, cloudcost) while their siblings do not. Enumerate the
class before fixing the first instance.

**`[corrected 2026-08-06]` The fix: payload extraction, and splitting is not an alternative.** The
original two-candidate framing below is superseded. Splitting the streams cannot restore
parseability while Logger output is on stdout, so it is not a viable branch — see the correction
block above. What works is a **backward scan for the last line that parses as a JSON object**,
which holds whatever is on either stream, whatever the store contains, and whether noise lands
before *or after* the payload. `tail -1` is **not** sufficient: three captured files carry worker
output after the payload (`sprint/2026052{1_202137,2_090058,2_095912}/payslip/run.json`). When no
line parses, print an explicit unknown — never a fabricated status; four captures have no payload
at all. A working implementation is in `../aetheris/docs/aetheris/claude-notes.md` §Claude Code —
sprint output parsing, verified against all four capture shapes.

*Original two-candidate text, superseded, kept as the record:* **Two candidate fixes, and the
choice is the whole ticket.** Either split the streams (`2>` to a sibling `run.err`, leaving
`run.json` parseable) — which changes what the D2 credential grep searches, so BL-099's
generalisation must then cover both files; or keep the merge and extract the payload (`tail -1`,
or the last line that parses), which is a one-line change that leaves every existing consumer's
file untouched. Do **not** do the first without re-reading BL-099: a credential-leak grep that
stops covering stderr is a strictly worse trade than a wrong status word.

**`[corrected 2026-08-06]` Done when:** the sprint's `--json` reads are **deterministic** — they
parse the payload regardless of ambient run-store state — at every site of the class, not only the
cloudcost status line; the chaos gate's operand is a real status rather than the fallback token;
a file with no payload prints an explicit unknown rather than a fabricated status; the streams stay
merged so the D2 credential grep continues to search everything the run wrote to both; and the
mutation posture is recorded against states that can actually occur (noise after the payload; no
payload at all) rather than against a non-success status, which the harness never writes into the
payload — see the sibling harness rows.

*Original done-when, superseded, kept as the record:* the sprint's orchestrator line prints the
run's real status, and whichever fix is chosen, the D2 credential grep demonstrably still searches
everything the run wrote to both streams.

**DONE 2026-08-06 (t1b).** Every Done-when clause discharged, each against evidence rather than
assertion:

- **One mechanism, every site.** `json_read <file> <jq-filter> [absent]` in
  `../aetheris/scripts/sprint.sh` scans the file's lines in reverse and takes the first that
  parses as a JSON object. **29 reads converted** across four previously-distinct mechanisms:
  **13** × `jq` over the file (incl. `run_agent`, `run_orb`, the chaos gate, the cloudcost inline
  line), **5** × `tail -1 | jq`, **7** × `grep -o '"run_id":"[^"]*"' | tail -1 | cut`, **4** × `jq`
  over a `--json` pipe (via the `json_read_cmd` wrapper, which captures the pipe to a temp file so
  the same scan applies). The workarounds that *worked* were folded in too — two mechanisms for one
  job is how the class regenerates. **13 sites excluded with reasons** (trajectory `--export`
  files, curl HTTP bodies, use-case script stdout, the eduloka sink gate → BL-108, the D2
  credential grep, `head -1` over `ls`).
  *(Count corrected at t1b review round 1 from a stated 19: three Group A sites — payslip, drive,
  email `.run_id` — were converted and verified but omitted from the census table, and the "19"
  itself rested on a bogus pairing step. 29 censused = 29 helper call sites, derived independently
  and matching; see the implementation notes.)*
- **Deterministic, on clean and noisy alike.** Per converted site, verified against the four
  capture shapes in `../aetheris/sprint/`: clean single line, noise *before* the payload, worker
  output *after* it, and no payload at all. **23 checks, 23 pass.** Expected values are pinned
  literals obtained independently of `json_read`, so the check cannot satisfy itself.
- **The chaos gate's operand is a real status.** Before: `[WARN] Chaos 1: status=no-json
  (investigate)`. After: `[OK] Chaos 1: agent exhausted max_steps → :done (expected)`. Both
  quoted from live runs — and the "before" is **the first chaos output ever captured in this
  repo**, so BL-107's "it has always warned" is now observation for at least one environment
  rather than inference. See BL-107.
- **A file with no payload prints an explicit unknown.** The token is `no-payload`, naming *the
  read* rather than the run. It cannot collide with a run status now (`handle_run_status/5` admits
  only `done`) nor with the statuses BL-106 would add. Sites feeding a `[[ -n … ]]` guard yield
  **empty** instead — a token there would push a garbage id into `mix aetheris inspect`.
- **The streams stay merged.** No change to any redirect, and none to the D2 credential grep,
  `CC_HERMETIC`, the poison-control arms or the orphan-count assertion. Live cloudcost leg
  confirms both D2 arms still run.
- **Mutation postures against states that occur in the record** — construct, observe, restore:
  non-JSON output *after* the payload (gate holds `OK`; the old `tail -1 | jq` yields `no-json` on
  the same file); no parseable payload at all (gate → `WARN status=no-payload`); and an
  anti-vacuity posture flipping the payload's `status` to `failed` (gate → `WARN status=failed`),
  which proves the repaired gate can still report red.

**The multiple-payload question, which this row's fix rested on, is settled — see BL-105's
sibling note and `../aetheris/docs/aetheris/claude-notes.md`.** One invocation *can* emit two
parsing JSON objects, for exactly one command (`fork`, per its own source comment at
`../aetheris/lib/aetheris/cli/commands/fork.ex:71`); it writes the early document first and the
result last, so recency still selects correctly, and `sprint.sh` never invokes `fork`. Of 319
captured files, zero carry more than one.

**Live evidence:** `./scripts/sprint.sh cloudcost` → `uc-cloudcost orchestrator → done (707 bytes)`
— the line that read `no-json` on every cloudcost run ever recorded. `./scripts/sprint.sh payslip`
→ `uc-payslip orchestrator → done (687 bytes)` (payslip parsed in 0 of 8 prior captures).

`Source: m3-cloudcost t3 §4, t3 review r0 F1 (2026-08-05).`
`Source (2026-08-06 corrections + rescope): t1a — census and evidence in
cloudcost/docs/t1a-implementation-notes.md; causal claim refuted by the stdout/stderr split
recorded there. Citations verified at aetheris@aaf0f9a / aetheris-agents@90c7c67.`
`Source (2026-08-06 close): t1b — census, per-site checks and postures in
cloudcost/docs/t1b-implementation-notes.md.`

---

### BL-101 — The report states tag coverage as a percentage and nothing else; surface the tags themselves (#TBD)
**Size:** S–M · **Priority:** medium · **Section:** aetheris-agents (`cloudcost/scripts/compose_report_data.py`, `cloudcost/templates/report.html.j2`)

Filed 2026-08-05 from the m3-cloudcost close. The report's Tag coverage section renders one
ratio (`40.00 % (0.4) tagged — 6 of 15 usable resources carry at least one tag; 9 carry none`)
plus per-provider counts and top untagged spenders. It never names a single tag. An operator
who wants to tag critical infrastructure so it is protected, and throwaway infrastructure so it
is visible, cannot tell from the report which tags exist, what carries them, or what they cost.

**A third of this is already built and dropped on the floor.** `detect_orphans.py` emits a
`reported` block — the untagged-in-tagged-account governance rule, reported-only by §t2 design,
each entry carrying its own `evidence[]` — and `compose_report_data.orphan_section` carries
`candidates` only, so `report_data` has no key for it and the template cannot render it. The
rule fires in the pipeline and is invisible in its output. m1 closed with exactly this as an
open question ("decide whether the report carries the `reported` list — a scope question, not a
done-when gap"); this row is the answer.

**Scope — descriptive only.** No detection logic changes, no §Normalized extension: `tags` is
already first-class on every inventory resource, and `reported` already exists in the orphan
artifact. Three additions:
- carry `reported` through compose into `report_data`, and render it as its own section;
- a **tags-in-use** table: each distinct tag, the resources carrying it, and their summed
  `monthly_cost_estimate`, ordered by cost. Apply the existing `top_k` convention and report
  the cap applied — a long tail of one-off tags is the expected shape and a silent truncation
  reads as "these are all the tags";
- show each resource's `tags` on the rows the report already renders (top untagged spenders,
  orphan candidates — candidates already carry `tags` in their identity fields, so this is a
  template change alone).

**Keep the orphan section and the tag section apart, deliberately.** m1 ruled that `keep=true`
resources stay invisible because "those are resources the operator asked to keep, and
suppressing them is the intent." That ruling is about the orphan *queue* and is preserved: an
excluded resource is still not a candidate. Showing it in the **tag** section — as a resource
carrying a keep tag, with its cost — is a different statement and does not reverse the ruling.
Do not merge the two sections into one "governance" block; that reversal, if ever wanted, is
its own decision.

**Not in scope, and gated.** Grouping by tag *key* is not a cross-provider concept: AWS tags are
key/value flattened to `k=v` by its adapter, DO and Linode tags are flat strings where `k=v` is
a human convention nothing enforces. A key-grouped view would be honest on AWS and inferred
elsewhere — the provider-vocabulary seam class **BL-074** exists for, and which already names
`KEEP_TAG`'s spelling as an adapter convention masquerading as a shared constant. Tags *driving*
detection (a `lifecycle=temp` tag raising confidence or creating candidates) is a change to the
shared engine and a milestone of its own, gated on BL-074 landing first. This row is the
descriptive layer that makes either worth building.

**Sequence with BL-070.** Both edit `compose_report_data.py`, which has been byte-unchanged
since m1 and whose stillness was the negative proof for two milestones. Doing them together is
one review of that file instead of two — the BL-078 trigger shape (do it the next time someone
is legitimately in the file).

**Note on content.** Tags can carry owner emails, project codenames and ticket ids. The report
is a local self-contained HTML file, so this is not a new exposure, but a tag table makes the
strings prominent where the percentage did not. Worth a line in the runbook when this lands
rather than a guard in the code.

**Done when:** the report names the tags in use with their resource counts and summed
estimates, applying and reporting a `top_k`; the `reported` governance list reaches
`report_data` and renders with its evidence; each rendered resource row shows its tags; a
`keep=true` resource appears in the tag section and still appears nowhere in the orphan section;
and the tag figures reconcile with the existing coverage ratio, asserted in a test.

`Source: m3-cloudcost close, 2026-08-05 (human request, from reading the live Linode report);
resolves m1-cloudcost §Open items' `reported`-list question.`


**DONE 2026-08-07 (m4 t5b).** Every Done-when clause satisfied; assessed per clause.

| Clause | Satisfied by |
|---|---|
| *the report names the tags in use with their resource counts and summed estimates, applying and reporting a `top_k`* | `coverage_section` emits `tags_in_use` / `tags_in_use_total` / `tags_not_shown`; the template renders a **Tags in use** table and states its cap in **both** states. `test_the_tag_table_reports_its_own_cap_in_both_states`, `test_the_tags_in_use_table_renders_with_its_tags` |
| *the `reported` governance list reaches `report_data` and renders with its evidence* | `orphan_section` carries `reported` through with `evidence[]` intact; the template renders it as its own sub-section. `test_the_governance_reported_block_reaches_report_data_with_its_evidence` |
| *each rendered resource row shows its tags* | spender rows carry `tags` (key always present, `[]` when none) and render chips or an explicit em dash. `test_untagged_spender_rows_carry_their_tags_and_the_key_is_always_present`, `test_untagged_spender_rows_render_their_tags_or_an_explicit_dash` |
| *a `keep=true` resource appears in the tag section and still appears nowhere in the orphan section* | `test_a_reported_resource_never_appears_in_the_orphan_section`; the m1 ruling is preserved, not reversed, and `test_a_reported_entry_is_never_banded_as_a_candidate` pins that a reported entry carries no `confidence` and no `monthly_saving_estimate` |
| *the tag figures reconcile with the existing coverage ratio, asserted in a test* | `test_tags_in_use_reconciles_with_the_coverage_ratio`, with `test_the_reconciliation_check_fails_against_a_deliberately_broken_fixture` as its anti-vacuity control |

**One finding worth carrying.** The governance rule **has never fired on any committed fixture** —
`inventory_rules_positive` is at 16.67 % coverage and `inventory_soc_2026-07` at 25 %, both below
the 50 % threshold, so `account_uses_tags` is False on every fixture in the repo. Asserting the
fired state required constructing an inventory over the threshold. The unfired state is what the
live DO report renders, and it now says **"Not evaluated … the rule did not run. This is not a
finding of 'no untagged resources'."** — which is the rider's shape, arrived at because this row
could not be implemented honestly without it.

`Source: m3-cloudcost close, 2026-08-05; implemented m4 t5b, 2026-08-07.`

---

### BL-102 — The complete-but-unmarked sweep runs at milestone closes only, so batch closes leave rows silently open (#TBD)
**Size:** XS–S · **Priority:** low-medium · **Section:** aetheris-agents (`docs/`, export procedure)

Filed 2026-08-05 from the m3-cloudcost export boundary. `CLAUDE.md` §Definition of done — doc
sync now carries *"`drift_check` verifies a pin is current, never that it is complete — read the
pinned content against what it should say."* At the m3 boundary that rule was discharged by
sweeping the **milestone doc's** §Done-when and §Milestone summary against the backlog, which
found BL-090 and BL-092 marked ✓ in done-when 5 and carrying no DONE section — pinned as-is, the
export would have shipped two closed rows reading as open. Same correction the 2026-08-04
boundary made mid-flight for BL-073/BL-095.

**The gap: a batch has no milestone doc, so it has nothing to sweep.** The cloudcost-in-Rig
batch closed against BL-0xx rows plus a handoff, not a `§Done-when` table. Its standing
instance is visible now: **BL-084 and BL-085** carry implementation notes on disk
(`cloudcost/docs/bl-08{4,5}-implementation-notes.md`) and no DONE section, and were outside the
m3 census by construction — no m3 document claims them. Whether they are actually complete is
the first thing this row has to establish; the notes-on-disk signal is evidence, not a verdict,
and closing a row that is not done is the worse error of the two.

**Two findings in two consecutive boundaries is the argument.** The class does not depend on
which artifact a cycle happens to produce, but the sweep as written does — it is keyed to a
document type only milestones have. A batch's closed rows are exactly as exportable and exactly
as invisible.

**Scope — procedure, not tooling.** Do not build a checker. The signal a script would key on
(notes file exists, row lacks DONE) is unreliable in both directions: notes are written for
tickets that later get deferred, and some closed rows never had notes. A green check over that
heuristic would be a **silent-wrong-answer** generator, which is the class the pin-currency rule
exists to prevent — the point is to *read*, and automating the read reintroduces the trust the
rule withdrew. What lands is a sentence in the export procedure naming what to sweep when there
is no milestone doc: the batch's closed BL-0xx rows and the handoff's own claims.

**Sequence.** Do it at the next batch close, when there is a live instance to sweep rather than
a retrospective one — the BL-078 trigger shape. Filing it now only because prose in a packet
files nothing.

**Done when:** the export procedure states what the complete-but-unmarked sweep reads at a batch
close; BL-084 and BL-085 are each adjudicated done-or-open, with a DONE section written for any
that is done; and the rule's wording in `CLAUDE.md` §Definition of done — doc sync no longer
reads as milestone-only if it currently does.

`Source: m3-cloudcost export boundary, 2026-08-05 (packet §3.6, deferred past the boundary
deliberately — filing it inside would have re-staled the backlog row the boundary had just
pinned and reopened a WARN the boundary existed to close).`

---

### BL-103 — The store may hold documents the manifest does not describe, and "remove all" is undefined against them (#TBD)
**Size:** S · **Priority:** medium · **Section:** aetheris-agents (`docs/`, export procedure)

Filed 2026-08-05 from the m3-cloudcost export boundary's post-upload check: the manifest
describes **25** documents; the store held **26**. The 26th predates the upload window, so it
survived the remove — the first time anything has produced evidence about the upload half at
all. Every prior boundary's upload was covered by discipline alone, and this is the first
boundary that could have caught the discrepancy, not the first at which it could have existed.

**Both branches of that finding are open, and they need opposite fixes.** If a non-manifest
document may legitimately live in the store, then the manifest is silent about a class of
document it shares a store with, and BL-002 Step 5's "REMOVE the old knowledge files" is
**destructive against a document this repo does not own** — the procedure says remove-all and
scopes it to nothing. If it may not, the store under-describes itself and the export record is
wrong. Note the asymmetry: under the benign branch the standing procedure is the hazard, and it
has been running unscoped at every boundary to date.

**Identified, not established.** The document is `claude/aetheris-agents--inbox-brief.md`,
created 2026-08-05 11:01 UTC, roughly an hour before the 11:57 upload window. The `claude/`
prefix is where agent-written project docs land by default, so the likely owner is another
Claude surface writing to this project. **Likely is not established, and that gap is the row's
point** — a document whose owner is assumed is a document whose removal is assumed safe. What
remains is confirming the writer and whether it is expected to persist across boundaries, which
is a fact to be found, not a preference to be settled.

**Scope — the manifest header and the prompt, not tooling.** Check 8 cannot see the store in
either direction; nothing here becomes automatable, and a checker over a store this repo cannot
read would be a green light with no referent. What lands is a sentence in the manifest saying
whether non-manifest documents may coexist and are out of scope, and a Step 5 that names what
"all" means so the next uploader is not choosing.

**Done when:** `claude/aetheris-agents--inbox-brief.md`'s writer is established rather than
inferred, and whether it is expected to persist; the manifest states whether non-manifest
documents may coexist and are out of scope; BL-002 Step 5's remove-all names its scope; and the
post-upload verification's check 3 says what an older timestamp means *given* that policy,
rather than leaving the reader the fork it leaves today.

`Source: m3-cloudcost export boundary, 2026-08-05 — post-upload verification, 26 documents
against a 25-row manifest; document identified by the human at filing.`

---

### BL-104 — sprint.sh's hermetic prefix is a denylist; invert it to an allowlist (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`scripts/sprint.sh`)

Filed from the m3-cloudcost close. The `CC_HERMETIC=(env -u …)` array in the cloudcost case
(`../aetheris/scripts/sprint.sh`, verified at `aetheris@082b37c:2383-2386`)
neutralises **named** variables: `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY
-u AWS_PROFILE`, plus `AWS_SHARED_CREDENTIALS_FILE=/dev/null`, plus (m3 t2) `-u LINODE_CLI_TOKEN
-u LINODE_TOKEN`. Every one of those is a name someone thought of. **A denylist cannot cover the
name nobody thought of**, and the list grows by one entry per provider forever.

**The live instance.** During m3 t1's preflight a 64-character credential-shaped variable named
`LINODE_BILLING` was found in the session environment — read by no Linode library, present in no
denylist, and surviving three separate cleanup passes (`~/.profile`, the systemd user-manager's
imported block, and a `gnome-terminal-server` process that snapshotted it at launch). Had it been
an active credential for the account under test, the hermetic proof would have reported green
while the run inherited it. The three-carrier finding is recorded in `aetheris/CLAUDE.md`
(Adjacent-case, *the class is not only code*).

**Fix direction — default-deny.** `env -i` with an explicit passthrough list rather than `-u` per
hazard. Establishing that list empirically is the whole risk of the ticket: `PATH`, `HOME`, the
`CLOUDCOST_*` keys the selected provider actually needs, and whatever the mix/BEAM invocation
genuinely requires (`MIX_ENV`, `ERL_*`, locale, possibly `ANTHROPIC_API_KEY`). Build it by
starting from nothing and adding only what the run demonstrably fails without, recording why each
entry is on it — a passthrough list assembled by guessing is the denylist problem wearing the
other hat.

**What the inversion buys beyond coverage.** The poison-control block — the `CC_POISON` /
`CC_PROBE` arms (i)–(iii), and their Linode siblings `CC_LINODE_POISON` / `CC_LINODE_PROBE`
(verified at `082b37c:2480-2560`) — then proves a *structural* property rather than an
enumerated one, and its per-provider arms collapse: with `env -i` there is nothing
provider-specific to unset, so the AWS arm's `[[ "$CC_PROVIDER" == "aws" ]]` gate **inside the
poison-control block** (verified at `082b37c:2512`) — the same test also guards the region
assertions (`:2651`) and the D2 credential grep (`:2671`), and this row means only the first —
disappears rather than being duplicated per provider. Adding provider four stops touching this
file at all.

**Sequence with BL-099 and BL-100 — all three edit the same block, and two of them interact.**
BL-099 generalises the D2 credential grep past AWS; this row changes what reaches the child at
all, so arm (iii) — *the credential the adapter reads survives the strip* — must hold for every
provider under the new passthrough list, or the run cannot authenticate. BL-100's stream-splitting
option changes what the grep searches. One pass over the cloudcost sprint case beats three, and
the interaction is only visible when they are read together.

**The standing-rule form of this is deliberately held.** *Environment isolation wants an
allowlist, not a denylist* is true and generalises past `sprint.sh` to any hermetic prefix or
container invocation, but it is one instance and its full argument is already here, where someone
acting on it will be standing. Filing it as a `CLAUDE.md` rule now puts one argument in two files.
Trigger for promoting it: a second denylist-shaped isolation found anywhere else — at which point
it promotes on the normal ≥2 bar with two citations.

**Done when:** `CC_HERMETIC` passes an explicit allowlist rather than unsetting names; the
poison-control block proves a non-allowlisted variable does not reach the child **without naming
it**; the AWS, DO and Linode legs all pass unchanged in behaviour; each passthrough entry is
recorded with the reason it is there; and the mutation posture is shown — a variable added to the
ambient environment and not to the list must not appear in the child.

`Source: m3-cloudcost t1 preflight, 2026-08-05 — LINODE_BILLING found in the session environment
under a name no denylist carried.`

`Citations verified at aetheris@082b37c. Anchors name the construct; the line numbers are
parentheticals against that commit, so a later insert makes them checkable rather than
silently wrong — the fix the m3 promotion prescribes, applied to a row that had already
drifted three times before it was filed.`

**DONE 2026-08-06 (m4 t3).** Every Done-when clause discharged.

- **`CC_HERMETIC` passes an explicit allowlist rather than unsetting names.** It is no longer an
  `env` array at all: `env -i NAME=value` would have put the credential in **argv**, readable from
  `/proc`, which breaks D2 in the ticket that hardens D2. It is now a `cc_hermetic` function that
  unsets every exported name not on the list inside a subshell and `exec`s — no value is re-typed,
  copied, or placed in an argv.
- **The poison control proves a non-allowlisted variable does not reach the child without naming
  it.** Arm (i) asserts the child's *entire* key set is a subset of the list — it names no hazard,
  so it covers `LINODE_BILLING`, `AWS_REGION` and DO's shadow names (none of which the denylist
  carried) by construction. The permitted shell-injected extras (`LC_CTYPE`/`PWD`/`SHLVL`/`_`) are
  derived from `env -i`, **not** from the mechanism under test — deriving them from `cc_hermetic`
  would let a leaking prefix excuse its own leak.
- **Each passthrough entry is recorded with the reason it is there**, and every reason is an
  observed failure: `PATH` (exit 127), `HOME` (`could not find the user home`), `LANG` (silent
  latin1 corruption of the payload — `c2 b7` becomes a bare `b7`), `ANTHROPIC_API_KEY` (run
  `failed` at step 0), `CLOUDCOST_OPTIMIZATION` (another component's fail-fast guard silently
  stops firing), plus the adapter-selected credential and knob names. Full transcripts in
  `cloudcost/docs/m4-t3-implementation-notes.md` §2.
- **The mutation posture is shown** — probe allowlisted → arm (ii) fails as a declared tautology;
  credential not allowlisted → survival arm fails. Both constructed, observed, reverted.
- **The per-provider arms collapsed as this row predicted.** Six arms across two blocks became
  three; adding provider four touches none of it.
- **Legs:** digitalocean run in full (16 `[OK]`, 0 `[FAIL]`). AWS and Linode **not runnable — the
  credentials are not present in this environment, and none was minted or probed to make them so.**
  Their adapter env surface, guard raises and knob behaviour were verified without a run; this row
  is closed on that basis and the limit is stated rather than papered over.

**Two things this row did not anticipate, both found by doing it:**

1. **`env -i` removes `AWS_SHARED_CREDENTIALS_FILE`, and absent is not `/dev/null`.** Absent
   restores boto3's default `~/.aws/credentials` lookup, and `HOME` is on the allowlist, so the
   file is reachable. A naive inversion would have re-opened the exact arm the denylist closed.
   It is kept as an explicit assignment.
2. **Default-deny strips the Linode endpoint-redirect names, which the denylist deliberately let
   through** so the adapter could *warn* about them. The hazard is now neutralised instead of
   reported. The signal is restored as a parent-side `warn` before the strip, using the adapter's
   own `ENDPOINT_REDIRECT_ENV`/`SHADOWING_ENV` constants — names only, no values read.

`Source: m4 t3, 2026-08-06 — landed with BL-099 in one pass, per this row's own sequencing note.`

---

### BL-105 — `--json` mode's payload shares stdout with the harness's Logger output (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/lib/aetheris/cli/`)

Filed 2026-08-06 from t1a. `mix aetheris --json <cmd>` writes its payload to stdout via
`IO.puts(Jason.encode!(data))` (`../aetheris/lib/aetheris/cli/output/formatter.ex:47`), and the
application's Logger writes to the **same stream** — the console backend is unconfigured for a
device (`../aetheris/config/runtime.exs:3` sets only `level: :info`). Demonstrated rather than
inferred:

```
$ mix aetheris --json list --limit 1 2>/dev/null        # stdout only
07:51:25.434 [warning] [Aetheris.Application] failed to resume run bl031-paused-demo-2658: …
07:51:25.436 [info]    [Aetheris.Scheduler] started run run_5S_eBQ for schedule 'news-sprint-…'
07:51:25.460 [info]    [Aetheris.Application] orphan sweep: %{errors: 0, …}
{"entries":[{"id":"run_5S_eBQ","label":"","status":"running","type":"run","started_at":"…"}]}

$ mix aetheris --json list --limit 1 2>&1 >/dev/null    # stderr only
(nothing)
```

**Claim scope, deliberately narrow:** the *Logger* output shares stdout. Whether `[sandbox]` lines
go to stdout or stderr is **not established** — the command above spawns no worker, and this row
does not need it.

**The consequence is non-determinism, not universal breakage.** Identical expressions succeed or
fail by environment. **The mechanism is not single, and only part of it is established:** the
resume-failure lines *are* store-state dependent, but the orphan-sweep line is not — it logs with
every counter at zero and is gated on `config :aetheris, :sweep_on_start`
(`../aetheris/config/config.exs`), and it did not exist before 2026-07-15 (`0188a90`, BL-003), so
its absence from the May captures is a version boundary. Do not attribute a file's failure to one
cause without checking which lines it carries. Across the captures in `../aetheris/sprint/`: news parses in 4 of 4, payslip fails in
8 of 8, cloudcost fails in 10 of 10 — same helper, same redirect. A clean single-line capture
exists from 2026-05-21, written *after* the resume-failure Logger line already existed in the code
(`application.ex`, added 2026-05-20), which is what establishes the dependence on store state
rather than on code age. So fixing this makes the sprint's reads **deterministic**; it does not
"make every read work", because some already do — that is the defect.

**A shipped product surface parses this output.** Rig's fork command builds `--json` argv and scans
stdout line by line for a parsing JSON object
(`rig/src-tauri/src/commands/fork.rs`, `fork_argv/3` at `:117`, `run_id_from_line/1` at `:140`,
`read_first_run_id/1` at `:155`). Its own comment already records the correct diagnosis — *"`mix`
compile and log noise shares stdout and does not parse as JSON"* — written 2026-07-26, ten days
before BL-100 was filed with the wrong one. Any fix must keep that consumer working.

**Reach, stated precisely — this does NOT on its own fix every sprint read.** Fixing the Logger
contaminant addresses the reads that fail *because of it*, which is the 2026-07-onward captures.
It does **not** cover a second contaminant: three captures carry
`aetheris_worker fatal: Broken pipe (os error 32)` lines *after* the payload, emitted by
`eprintln!` in the worker's entry point (`../aetheris/native/aetheris_worker/src/main.rs`, the
fatal-exit arm) — i.e. on **stderr**, which the sprint's `2>&1` merge carries into the file
regardless of what this row changes. So a `tail -1`-style read stays wrong after this lands, and
the sprint still needs its own backward-scan fix. That is why BL-100 and this row are separate,
and why neither obviates the other. See BL-100.

**With both streams now established, the solution space is fully determined — and the two fixes
are complementary, not alternative.** Logger is on stdout; worker output is on stderr:

| | `run.json` contains | parseable? |
|---|---|---|
| Split streams only | stdout, still carrying Logger output | no |
| This row only (Logger off stdout), streams merged | worker stderr via `2>&1` | **not reliably** — unparseable whenever the worker emits, not unconditionally |
| **Both** | the payload alone | **yes, no scan needed** |

Row 2 is what refutes "at a stroke"; row 1 is why the arbiter's payload-extraction choice was
right. **The combination has a cost this repo already knows: splitting is exactly what BL-099's D2
credential grep must then cover across two files** — BL-099's row records that a credential-leak
grep which stops covering stderr is a strictly worse trade than a wrong status word. So anything
that pairs this row with a split must land BL-099's generalisation with it, not after. The
backward scan remains correct under all three worlds, so t1b's design is unaffected either way.

**Constructibility note on the mutation posture below.** It asks for a run whose store emits boot
output and one whose store does not. `config :aetheris, :sweep_on_start` defaults to **true**
(`../aetheris/config/config.exs`), so the orphan-sweep line is emitted regardless of store
contents — the second run cannot be produced by arranging the store alone and requires toggling
that config (or the equivalent of `config/test.exs`, which sets it false). Whoever picks this up
should plan for that rather than discover it mid-ticket.

**Done when:** the `--json` payload is separable from log output by a consumer that does not have
to know what the noise looks like — either the payload moves to a stream the Logger does not share,
or the contract states that consumers must scan for the last parsing JSON object and every in-repo
consumer does so; Rig's fork path is verified unbroken either way; and the mutation posture is
recorded against a run whose store emits boot output and one whose store does not.

**DONE 2026-08-09 (hc-c).** Closed with BL-106 as one contract. The arm taken is the first of
the Done-when's two — *the payload moves to a stream the Logger does not share* — implemented by
moving **Logger**, not the payload: stdout is the payload stream, stderr the diagnostic stream.
Moving the payload instead would have broken Rig, which reads stdout.

Applied on the boot path (`Aetheris.Application.route_logging_to_stderr/0`), not in
`config/runtime.exs`, because config does not reach the entry points that matter: `mix aetheris`
never runs `app.start`, so the *running* handler keeps writing to stdout however the file is set,
and an escript never evaluates `runtime.exs`. Found by capture — the handler's config and its
actual destination disagreed under `mix aetheris`, which is why the fix is not a config line.
`:logger.update_handler_config/3` cannot do it either (`:illegal_config_change` on a live
`logger_std_h`); the handler is removed and re-installed, and only when it is still the stock
stdout one, so a file handler or an operator's own destination is never overwritten.

**Mutation posture, both store conditions the row names.** Noisy store (default env,
`sweep_on_start: true`, two resumable checkpoints): stdout = **1** line, parses; stderr = 3 lines.
Quiet store (`MIX_ENV=test` — `sweep_on_start: false`, `:memory:` db, the toggle this row's
constructibility note anticipated): stdout = **1** line, parses; stderr = **0** lines. The broken
state was observed on this same tree before the fix: the row's own demonstration command emitted
**4** non-blank stdout lines, 3 of which did not parse.

**The third arm hc-a proposed — suppress boot logging on the boot path — was considered and not
taken.** It removes only the boot lines; any log line emitted during a run still lands on the
payload stream, so it does not deliver *"separable by a consumer that does not have to know what
the noise looks like"*, and it costs observability to boot.

**Reach, unchanged and restated honestly:** `mix` compile noise is a different emitter and still
goes to stdout on a run that recompiles. The Done-when is about Logger, and Logger is what moved.

**The change is wider than this row, so its consumers were swept (hc-c r1, F1).** Moving Logger
affects **every** invocation and every mode, not only `--json`, so "no `--json` reader broke" is
not the question. **Population:** every file in both repos with an executable extension
(`.sh .py .rs .ts .tsx .exs .ex`, excluding `node_modules`, `target`, `_build`, `deps`, `priv`,
`.git`) containing a harness invocation — **39 files**, of which **5** actually spawn the harness
and read a stream. **0 of the 5 read log text from stdout**; the enumeration and each site's
reading behaviour are in `docs/milestones/hc-c-implementation-notes.md` §7. **The sweep is clean,
not exhaustive** — it cannot reach an operator's own pipeline or anything outside these two repos,
and that residue is recorded in `docs/milestones/hc-consolidation.md` §Not established item 6
rather than left to read as completeness.

`Source: t1a, 2026-08-06 — established by the stdout/stderr split above; BL-100's `2>&1` diagnosis
corrected in the same round. Citations verified at aetheris@aaf0f9a / aetheris-agents@90c7c67.`

---

### BL-106 — `--json` emits no JSON document on a non-success run (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/lib/aetheris/cli/`)

Filed 2026-08-06 from t1a. **Sibling of BL-105 — one contract, two mechanisms.** BL-105 is why the
sprint's reads are unreliable; this row is why a programmatic consumer gets nothing on exactly the
runs it most needs to read.

The formatter's error branch ignores the output mode entirely
(`../aetheris/lib/aetheris/cli/output/formatter.ex:56`):

```elixir
  def print({:error, reason}, _mode) do
    IO.puts(:stderr, "Error: #{reason}")
    1
  end
```

`_mode` is unused, so `--json` and `--human` behave identically on the error path. And every
non-success terminal state routes there: `handle_run_status/5`
(`../aetheris/lib/aetheris/cli/commands/run_helpers.ex:112`) returns `{:ok, %{… status: :done}}`
for `"done"` but `{:error, …}` for `"failed"` and `"cancelled"`; `await_run/2`'s declared success
shape is `status: :done` and nothing else; `await_orb/1`
(`../aetheris/lib/aetheris/cli/commands/run.ex:121`) turns `%{status: :failed}` into `{:error, …}`
at `:126`. Confirmed in the record: all ten captured cloudcost payloads read `status: "done"`, and
a failed payslip run emitted `Error: run payslip-orch-cAdfJQ failed` with no JSON line at all
(`../aetheris/sprint/20260521_191506/payslip/run.json`).

**Product-facing, but not an outage — the known consumer compensates.** Rig does not look for JSON
on the failure path; it collects stderr on a separate thread and renders that prose
(`rig/src-tauri/src/commands/fork.rs`, `stderr_collector` at `:88`/`:108`, `start_failure_error/1`).
That works, and it means a UI error string is derived from human-readable wording rather than from
a machine contract — brittle to rewording, not broken today.

**This is the row BL-100's justification was actually describing.** BL-100 argued the fix would
restore a signal for *"`partial`, `error`, a status the exit code does not distinguish"*. Those
statuses never reach the payload, so BL-100 cannot deliver them; this row is where that becomes
achievable.

**Done when:** `--json` emits a JSON document on every terminal outcome, success or not, carrying
the run id and a real status; the human path is unchanged; Rig's fork error path is migrated or
verified still correct; and the mutation posture is recorded — a genuinely failing run must produce
parseable output naming the failure.

**DONE 2026-08-09 (hc-c).** Closed with BL-105 as one contract. `Formatter.print({:error, …}, :json)`
now emits a document on stdout beside the unchanged prose on stderr, and the terminal run outcomes
carry a structured detail so the document can name the run: `handle_run_status/5`'s `failed` and
`cancelled` branches and `Run.await_orb/1`'s failed branch return
`%{run_id | orb_id, status, error}` instead of a bare string. A failure that is *not* a run outcome
stays a string and renders `{"status":"error","error":"…"}` with **no `run_id`** — there is no run
to name, and that absence is load-bearing (see the Rig note below). The human path, the stderr
prose and the exit code are unchanged.

**Mutation posture: a genuinely failing run, observed.** `mix aetheris --json run
agents/ollama_smoke.exs` against an Ollama that cannot load the model emitted
`{"error":"run ollama-9EuU5w failed","status":"failed","run_id":"ollama-9EuU5w"}` on stdout. The
broken state was observed on the same tree minutes earlier: the same failing run emitted **no JSON
at all**. Three unit tests were added and mutation-checked — with the `:json` error clause removed,
the two payload-asserting tests fail and the human-path test correctly stays green.

**Rig's fork error path is verified still correct, not migrated** — the option this row's Done-when
allows. `read_first_run_id` returns the *first* stdout line with a string `run_id`, and the
fork-start line is written before `await_fork/1` is called (`fork.ex`, `run_with_step/4`), so an
error document carrying the same `run_id` can only follow it. A fork that never starts yields a
bare-string error, hence no `run_id` key, hence `None` and the stderr path — exercised live
(`--step` with no matching `step_complete` → `{"error":"failed to build fork config:
:step_not_found","status":"error"}` on stdout, prose on stderr). Rig's own 7 tests pass unchanged,
including `read_first_run_id_none_on_eof_without_a_run_id`, which already pinned `{"status":"error"}`
as a no-`run_id` line. The starts-then-fails case is covered by the harness's own
`fork_test.exs` test of that name.

**Not taken here: BL-112.** Its row says the UTF-8 choice "belongs with BL-105/BL-106". It is a
different defect (latin1 fallback corrupting payload bytes) and outside hc-c's scope, which is
these two rows' Done-whens and no `--json` schema beyond them. Left filed.

**The exit code is still 0 on a failed `mix aetheris` run** — `Mix.Tasks.Aetheris.run/1` discards
`Aetheris.CLI.run/1`'s code. That is **BL-044**, R3's question for hc-d, and is deliberately not
touched here. It is also why a real status word in the payload is worth having.

`Source: t1a, 2026-08-06. Citations verified at aetheris@aaf0f9a / aetheris-agents@90c7c67.`

---

### BL-107 — the chaos-case gate has never evaluated its subject (#TBD)
**Size:** XS–S · **Priority:** medium · **Section:** harness (`../aetheris/scripts/sprint.sh`)

Filed 2026-08-06 from t1a, per the gate rule — *a red gate gets a tracked ticket the day it's
found*. This is that ticket. **Repair is scheduled, not started:** it is expected to fall out of
BL-100's sprint work (t1b), which has not run. **If that sequence changes, this gate is carried
red with this row named**, per the tracked-carry clause — never relaxed, re-pointed or downgraded
to get a clean run.

`../aetheris/scripts/sprint.sh:296-299`:

```bash
  run_aetheris --json run /tmp/aetheris_chaos_maxsteps.exs > "$OUT_DIR/chaos/maxsteps.json" 2>&1 || true
  status=$(jq -r '.status // "unknown"' "$OUT_DIR/chaos/maxsteps.json" 2>/dev/null || echo "no-json")
  [[ "$status" == "done" ]] && ok "Chaos 1: agent exhausted max_steps → :done (expected)" \
                             || warn "Chaos 1: status=$status (investigate)"
```

Unlike the other three `.status` sites — `run_agent()` (`:53`), `run_orb()` (`:70`) and the
cloudcost case's inline `ok` line (`:2573`) — which interpolate into an `ok` line, **this one is a
gate** — the extracted value is the operand of an equality test. When the
read fails, `status` is the literal `no-json`, the test cannot match, and the case emits
`warn "Chaos 1: status=no-json (investigate)"`.

**Both claims below are qualified, because neither is a bare observation.** The operand is the
fallback token **in every environment emitting harness boot output** — not unconditionally, since
BL-105 establishes that some environments produce a clean, parseable file. And the frequency claim
is **inference, not observation**: no chaos output has ever been captured in this repo
(`find ../aetheris/sprint -path '*chaos*'` returns nothing), so "it has always warned" is derived
from the extraction's behaviour rather than seen. The premise — that every chaos run to date ran in
a noisy-store environment — is unexamined.

**Chaos runs only under specific sprint targets** — the chaos case's opening
`if [[ "$TARGET" == "chaos" || "$TARGET" == "all" ]]` guard (`:277`) — not on every sprint
invocation.

Nothing other than the warn line consumes the result: `grep -n '\$status'` over the file returns
exactly four reads — the `ok` lines inside `run_agent()` (`:54`) and `run_orb()` (`:71`), both
where `status` is `local`, and the chaos gate's own test and warn (`:298`, `:299`) — and
`maxsteps.json` is read only by the chaos gate's own extraction (`:297`). The chaos `status` is a
global but is never read after its warn line. `warn` sets no exit status (BL-077), so no exit path changes.

**Done when:** the gate's operand is a real status rather than a fallback token; the assertion's
outcome is recorded before and after, so the change from `warn` to whatever it becomes is visible
and adjudicated rather than silent; and if it then reports a genuine failure, that gets its own row
rather than being absorbed. **No claim is made here about what it will report after repair** — it
has never evaluated, so that is unknown.

**DONE 2026-08-06 (t1b). The gate now evaluates, and it passes.** Repair landed with BL-100's
single extraction mechanism, as this row anticipated, so the carried-red branch was not exercised.

| | Assertion outcome, quoted from the run |
|---|---|
| **Before** (`sprint/20260806_172144`, pre-edit tree at agents `c5b63ae` / harness `f6fbd82`) | `[WARN]  Chaos 1: status=no-json (investigate)` |
| **After** (`sprint/20260806_172825`, post-edit) | `[OK]    Chaos 1: agent exhausted max_steps → :done (expected)` |

The gate line itself is byte-unchanged apart from the extraction: the comparison
`[[ "$status" == "done" ]]`, the `ok` text and the `warn` text are all as they were. **Nothing was
relaxed, re-pointed or downgraded** — the operand changed from a fallback token to the payload's
real `status`, and that is the whole edit.

**Two claims this row qualified are now resolved by observation rather than inference.** The row
noted that "it has always warned" was derived from the extraction's behaviour, because
`find ../aetheris/sprint -path '*chaos*'` returned nothing. The before-run above **is** the first
chaos capture in this repo, and it warned — so the claim is now observed for at least this
environment. Its file (`sprint/20260806_172144/chaos/maxsteps.json`, 9 lines) carries two
`failed to resume run` warnings, an orphan-sweep line and two `[sandbox]` lines ahead of an intact
payload: the noisy-store shape the row's premise assumed, confirmed rather than presumed. Whether a
chaos run in a *clean*-store environment would have parsed remains open — that premise is still
unexamined, and is left in `cloudcost/m4-consolidation.md` §Not established.

**No new row is owed by this gate.** It reported no genuine failure. (A separate, unrelated red
*was* found off-territory during t1b's live runs and is filed as **BL-110**.)

`Source: t1a, 2026-08-06. Citations verified at aetheris@aaf0f9a.`
`Source (2026-08-06 close): t1b — before/after runs and the mutation postures in
cloudcost/docs/t1b-implementation-notes.md.`

---

### BL-108 — the eduloka sink gate parses a merged stream: same shape, different root cause (#TBD)
**Size:** XS · **Priority:** low · **Section:** harness (`../aetheris/scripts/sprint.sh`), eduloka

Filed 2026-08-06 from t1a's census. `../aetheris/scripts/sprint.sh:1657-1663` captures a script's
stdout **and stderr** together and parses the result whole as JSON, then gates on it:

```bash
  DIRECT_STDOUT=$(python3 "$EDULOKA_DIR/scripts/upsert_institute.py" \
    --in "$GOLD_TMP" 2>&1 || true)
  DIRECT_STATUS=$(echo "$DIRECT_STDOUT" | \
    python3 -c "import json,sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
  [[ "$DIRECT_STATUS" == "error" ]] \
    && ok "direct sink without EDUX_DATABASE_URL → error (no silent fallback)" \
    || warn "direct sink error path unexpected — got status: $DIRECT_STATUS"
```

Structurally this is the same defect class as BL-100 — a merged stream parsed whole, with a
fallback token on failure, feeding a gate rather than a display. **The root cause is different**:
the contaminant would be the script's own stderr, not harness Logger output, so BL-105 does not
reach it.

**The evidence indicates this gate passes today.** The exercised path is
`eduloka/scripts/upsert_institute.py:111`, which prints clean JSON to stdout and exits before any
database work; the module's imports are stdlib plus one local module, and `import edux_record`
writes nothing to stderr (checked). The documented contract is stdout-only (`:20`). So
`DIRECT_STDOUT` should be one clean JSON line and the assertion should match.

**The single remaining check** — which decides it either way, and does not require running the
sprint: whether `EDUX_DATABASE_URL` is set in the ambient environment at that point. The script is
invoked without `env -u`, so if the variable *is* set the run takes the `_run()` path instead,
where `psycopg` is imported and a connection attempted, and both can write to stderr and break the
parse. **Not established** — the operator's environment was not inspected.

**Done when:** the gate's parse is robust to anything on stderr (or the capture stops merging it);
the ambient-variable question is settled and recorded; and the anti-vacuity posture is shown — a
constructed stderr-contaminated run must still yield the right verdict or fail loudly.

`Source: t1a census, 2026-08-06. Citations verified at aetheris@aaf0f9a / aetheris-agents@90c7c67.`

---

### BL-109 — two `milestone-reference.md` files, canonical by different measures (#TBD)
**Size:** XS · **Priority:** low · **Section:** harness (`../aetheris/docs/aetheris/`)

Exposed by t1a's census, 2026-08-06, and **not in that ticket's scope to resolve** — recorded so
the duplication is not rediscovered. Two documents carry this name:

| Path | Size | Carries the sprint `no-json` claim? |
|---|---|---|
| `../aetheris/docs/aetheris/milestone-reference.md` | 12 lines | no |
| `../aetheris/docs/aetheris/milestones/milestone-reference.md` | the substantive index | yes (annotated by t1a) |

**Canonical by reference graph and canonical by content are different files.** Every cross-reference
in the repo points at the *short* one — `docs/aetheris/claude-notes.md`, and the "Add to
`docs/aetheris/milestone-reference.md`" instructions in `milestones/m11-eval-framework.md`,
`m12-hierarchical-delegation.md` (twice), `m13-persistent-agents.md`, `ollama-xml-milestone.md`,
`handoff-m12-m13.md` and `remove-nif.md`. The substantive milestone table, with the Status column,
is in the *other* one.

Neither covers anything past m13, and both were last touched 2026-05-27 — so neither is maintained,
while the project is several milestone-eras beyond them. That is what made t1a's liveness
classification undecidable; it applied the non-destructive default (a note, not an in-place
rewrite) and annotated only the file that carries the claim.

**The question is which survives, not which gets edited.** Resolving it means deciding whether the
index is still wanted at all — an unmaintained index that documents point to is a
`document-that-quotes-repo-state` hazard with a reference graph attached.

**Done when:** one file is canonical or both are retired; every cross-reference points at whatever
survives; and if an index is kept, it either covers current work or says plainly what era it stops
at.

`Source: t1a census, 2026-08-06. Citations verified at aetheris@aaf0f9a.`

---

### BL-110 — the payslip case asserts a reference employee the run cannot produce (#TBD)
**Size:** XS · **Priority:** medium · **Section:** harness (`../aetheris/scripts/sprint.sh`), payslip

Filed 2026-08-06 from t1b, per the gate rule — *every existing gate runs at ticket boundaries, even
off-territory; a red gate gets a tracked ticket the day it's found.* Found by running
`./scripts/sprint.sh payslip` as t1b's shared-helper live leg. **Pre-existing and unrelated to
t1b's change** — the assertion block is byte-identical at `c5b63ae`/`f6fbd82` and is not gated on
`RUN_ID`, so the extraction repair cannot have lit it:

```
[FAIL]  BTL_999 output directory not found: ../aetheris-agents/payslip/output/BTL_999
```

`../aetheris/scripts/sprint.sh:769-778` asserts `payslip/output/BTL_999` exists after the
orchestrator run. **Nothing in the run can create it.** The orchestrator invokes
`generate_employee_payslips.py --csv data/payroll.csv`
(`payslip/agents/payslip_orchestrator.exs:23`). The `BTL_999` directory's only possible source is
the `BTL/999` employee id, which appears **twice in `data/sample_payroll.csv` and zero times in
`data/payroll.csv`** — the sprint's own preflight names both files (`:742`, `:750`).

**It is another ambient-state assertion, which is why t1b noticed it.** `payslip/data/payroll.csv`
is gitignored (`payslip/.gitignore:2`) and the sprint copies the sample into place *only if it is
absent* (`:749-753`). So on a fresh clone the copy happens, `BTL/999` is present, and the assertion
passes; on any machine that has ever put real payroll data there — which is the intended
production shape — the copy is skipped and the assertion fails forever. Same defect class as
BL-100: an assertion whose verdict is decided by ambient state rather than by the run. That the
sprint has been reporting `[FAIL]` here indefinitely without anyone acting is the alarm-fatigue
outcome the gate rule exists to prevent.

**`fail()` only prints (BL-077)**, so the sprint still exits 0 and no CI signal changed. That is
why it has been invisible.

**Left red and carried, not relaxed.** t1b did not re-point it at an employee that happens to
exist, nor downgrade it to a `warn` — either would destroy the one thing the assertion still
preserves, that the payslip pipeline produced output for a *known* employee.

**Done when:** the reference employee the assertion names is one the run can actually produce —
either by keying the check to an id read out of the CSV the orchestrator was given, or by running
the assertion leg against `sample_payroll.csv` explicitly rather than depending on whether
`payroll.csv` exists. Decide which; do not simply delete the check. Whichever is chosen, the
verdict must not depend on whether a gitignored file is present.

`Source: t1b, 2026-08-06 — off-territory gate run. Citations verified at
aetheris@f6fbd82 / aetheris-agents@c5b63ae.`

---

### BL-111 — session memory is a durable instruction surface outside git, and no census, review or gate can reach it (#TBD)
**Size:** S to characterise · **Priority:** medium · **Section:** process (no repo owns it)

Filed 2026-08-06 from m4 t2. **Characterisation first — the fix is deliberately not designed
here**, because what this surface *is* decides whether the row is housekeeping or an untracked
normative document.

**What happened.** t2 retired the planted-orphan practice and censused both repos by substance for
every live instruction to create a billable cloud resource. The census was correct and complete for
its scope. It could not reach the stalest carrier: this project's **session memory** said
*"BL-069 re-ARMED"* and pointed at the runbook for *"how to plant an orphan to exercise the ≥1
path"*, across **five sites in two files**. `git grep` over both repos is *structurally* incapable
of finding it — the files are not in either repo, and not in any repo. Corrected at t2's close, so
the instance is discharged; the gap is not.

**What the surface is, established at t2 rather than assumed:**

- **Location and scope.** `~/.claude/projects/<cwd-slug>/memory/*.md`, where the slug is the
  session's working directory with separators replaced by `-`. So it is **per-project-directory**,
  not per-repo and not per-user.
- **Not under version control at all.** `git rev-parse` inside it returns *"not a git repository"*.
  No history, no diff, no blame, no review.
- **Seven scopes exist on this machine; four hold files** — `aetheris-agents` **22**, `aetheris`
  (the harness) **10**, `ctelixir` 2, `rig` 2.
- **Part of it is loaded into every session unconditionally.** `MEMORY.md` (~4.5 KB here) is an
  index read at session start by instruction; the individual files (~79 KB here) are recalled
  selectively.
- **Its content is explicitly normative, by its own schema.** Files carry a frontmatter `type:`,
  and in this scope **13 of 22 are `type: feedback`** — defined as *guidance the assistant has been
  given on how to work*. That is instruction, not notes.
- **It decays exactly like a document quoting repo state, with no invalidation channel.** **20 of
  22** files cite a repo artifact — a path, a script name, a `BL-` row. Nothing re-checks any of
  them, and `drift_check` does not know the directory exists.
- **A cross-repo cycle has two of them.** A session rooted in `../aetheris/` reads the harness
  scope's 10 files, which this cycle never opened. Checked at t2: nothing there was invalidated by
  the retirement, and the retired claim appears in **no scope but this one**. That is a fact about
  this instance, not coverage.

**Why it is worse than the channels this cycle has been closing.** BL-007's packet rule and the
handoff-is-not-a-promotion finding both concern content that exists *somewhere in a repo* and fails
to travel. This is content that instructs future sessions and is **outside version control, outside
every census, outside review, and outside every done-check** — the only channel found so far with
none of the four. Nothing would have caught it, and nothing will catch the next one.

**Done when:** the surface is characterised to a ruling — is it a private scratchpad whose staleness
is nobody's problem, or an untracked normative document that a retirement, a promotion or a
correction owes an update? — and, if the latter, what a census owes it is written down somewhere a
session will read. **Do not skip to a mechanism.** "Export it into the repo", "grep it in the
census", "stop putting normative content in it" are three different answers to three different
rulings, and picking one before the ruling is how this becomes a second surface to keep in sync.

**Related, not duplicated.** BL-007's *the packet is the artifact that travels* (agents `CLAUDE.md`
§Learning — BL-007) and *a learning exists only where a session will read it* (harness `CLAUDE.md`)
are the two rules this abuts. Both assume the destination is a tracked file. This row is the case
where a session *does* read it and no repo owns it.

`Source: m4 t2 close, 2026-08-06 — t2 review r1 §5 (observation) → r2 item 2 (filed). Surface
characterised at t2's close against the live directory; scope counts and the no-other-scope result
are reads of this machine on that date, not claims about the tool in general.`

---

### BL-112 — the BEAM's latin1 fallback silently corrupts non-ASCII in `--json` payloads (#TBD)
**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/lib/aetheris/cli/`)

Filed 2026-08-06 from m4 t3. When the BEAM starts with no UTF-8 locale in its environment, it runs
with `:file.native_name_encoding() == :latin1` and Elixir emits a startup warning saying so. In
that state the `--json` payload's non-ASCII characters are written as **bare high bytes rather
than UTF-8 sequences**. Measured on the cloudcost run label, which contains `·` (U+00B7):

```
LANG present (and every archived capture):
  6f 73 74 20 c2 b7 20 44  69 67 69 74 61 6c 4f 63   |ost .. DigitalOc|   valid UTF-8
LANG absent:
  6f 73 74 20 b7 20 44 69  67 69 74 61 6c 4f 63 65   |ost . DigitalOce|   invalid UTF-8
```

**The failure is silent, which is the whole reason this is a row.** The line still parses as JSON,
so nothing downstream errors: `sprint.sh`'s `json_read` opens the file with
`errors='replace'`, and a consumer reading the label gets a replacement character where a `·`
should be. The warning that *would* have told you appears on stderr at VM start, thousands of
lines from the payload, and every reader has been trained to skip it. This is the
**Silent-wrong-answer** shape in the harness's own output contract.

**Not caused by m4 t3, and not fixed by it.** t3's hermetic inversion *would* have introduced it
(a default-deny prefix drops `LANG` unless it is passed), which is how it was found; `LANG` is on
that prefix's allowlist precisely so the sprint reproduces the ambient behaviour. But the
underlying fallback is provider-independent, harness-wide, and predates the ticket: **any**
consumer on **any** workstation with no `LANG`/`LC_ALL` gets malformed UTF-8, and nothing anywhere
reports it. Rig's fork path (`rig/src-tauri/src/commands/fork.rs`) scans this same stdout.

**Two candidate fixes, and they are not equivalent.** Either the CLI sets its own output encoding
explicitly so the payload is UTF-8 regardless of locale, or the harness refuses to emit `--json`
under a latin1 name encoding and says why. The first is silent-correct; the second is loud. The
choice belongs with BL-105/BL-106, which are already reopening the `--json` output contract — this
row is scoped with them rather than alone.

**Done when:** a `--json` payload containing non-ASCII is byte-identical with and without a UTF-8
locale in the environment, or the harness refuses to emit one and names the reason; the mutation
posture is recorded against a run with no `LANG` and one with it; and Rig's fork consumer is
verified unbroken either way.

`Source: m4 t3, 2026-08-06 — found while deriving the hermetic allowlist, by comparing the
inverted prefix's payload bytes against the archived captures. Verified at harness f8bbac8.`

---

### BL-113 — a missed *knob* or *optional* credential constant disappears from the sprint's adapter env bridge silently (#TBD)
**Size:** XS · **Priority:** low · **Section:** aetheris-agents (`../aetheris/scripts/sprint.sh`)

Filed 2026-08-06 from m4 t3. **Re-characterised at t3 review r1, before the row was ever acted on
— the first filing was aimed at the half of the surface that fails loudly.** The original heading
read *"selects by constant name, so a new credential constant is missed silently"*; the trace below
establishes that a missed **mandatory credential** is the one case that does *not* go quiet.
Corrected rather than left standing, because this is an open row and the corrected text is what
someone will act on.

The cloudcost case builds its hermetic allowlist, its credential-survival arm and its D2 credential
grep from names read out of the selected provider's adapter module, in three categories — `cred`
from `TOKEN_ENV`/`ACCESS_KEY_ENV`/`SECRET_KEY_ENV`/`SESSION_TOKEN_ENV`, `knob` from
`REGION_ENV`/`REGIONS_ENV`, `hazard` from `SHADOWING_ENV`/`ENDPOINT_REDIRECT_ENV`. That is one
level better than hand-typing the environment variables — an adapter renaming
`CLOUDCOST_LINODE_TOKEN` is followed automatically — but **the list of constant *names* is still
hand-typed in the sprint**, so an adapter that adds a constant the sprint has never heard of is
picked up by nothing.

**What happens then depends on the category, and only some of it is loud.** Established at t3
review r1 by mutating the bridge's constant tuples and reading which array the grep iterates,
rather than by reasoning:

| Missed constant | Behaviour | Loud? |
|---|---|---|
| `cred`, on a provider whose *whole* cred list it was | the bridge yields nothing and the case `fail`s at preflight — `could not read digitalocean's credential env names from its adapter`, exit 1, before any run | **loud** |
| `cred`, on a provider carrying others (AWS) | the empty-list guard does **not** fire. The name is stripped; if the credential is mandatory the adapter fails at fetch — loud, but later and with a worse message | loud-ish |
| `cred` that is **optional** (an AWS session token is not always in use) | stripped; nothing fails and nothing reports it, until the day a temporary credential is the one in use | **silent** |
| `knob` | the documented override is stripped and the child reads `None` — the leg sweeps the default region set while the operator believes it swept theirs. Demonstrated: dropped from the final list, `CLOUDCOST_AWS_REGIONS -> None`, no error anywhere | **silent** |
| `hazard` | stripped anyway under default-deny, so the *run* is safe — but the operator-facing warning that their shell carries a redirect never fires | **silent, low severity** |
| a credential **mis-categorised as a `knob`** | the severe one. Knob names are appended to `CC_ALLOW` but never to `CC_CRED_NAMES`, and the D2 grep iterates `CC_CRED_NAMES` — so the credential **reaches the child and is never grepped for** | **silent** |

**So the row's subject is the quiet half**, and the loud half is evidence the design works rather
than a gap. The last line is the one that would actually cost something: a D2 hole that every leg
reports green.

**This is the same seam BL-074 sweeps**, one level up: not a provider's vocabulary reaching shared
machinery, but a provider's *env surface* reaching the apparatus that polices it.

**Fix direction, and the choice is the row.** A naming convention the sprint can enumerate (`*_ENV`
with a category prefix), a declared mapping the adapters export (`D2_ENV = {...}`), or a
completeness test in `cloudcost/tests/` asserting every `*_ENV` constant is classified. The third
is probably right — it fails at test time in the repo that owns the adapters rather than at sprint
time in the one that does not, and it is the only one that catches a **mis-categorisation**, which
no amount of enumeration in the sprint will.

**Done when:** an adapter constant naming a credential cannot be added, renamed, or mis-categorised
without either the sprint selecting it correctly or a test failing; and the mutation posture is
recorded for the **silent** cases specifically — a missed knob, a missed optional credential, and a
credential mis-categorised as a knob — not only for the mandatory-credential case that already
fails loudly.

*Original done-when, superseded, kept as the record:* an adapter constant naming a credential
cannot be added without either the sprint selecting it or a test failing; and the mutation posture
is recorded — add a new credential constant to one adapter, watch the guard fire, remove it.
*(Superseded because "watch the guard fire" names the mandatory-credential case, which is the one
that already fails loudly; the posture it asked for would have been recorded against the half of
the surface that needs no fix.)*

`Source: m4 t3, 2026-08-06 — recorded as a residual of that ticket's own bridge. Re-characterised
at t3 review r1 the same day, after the reviewer's trace was checked against the code rather than
taken; the mutations behind the table were run at agents aabf546 / harness 7c248c0.`

---

### BL-114 — the recent-activity modifier has never fired against any real inventory, on any provider (#TBD)
**Kind:** defect · **Census item:** X4 · **Contract:** C8
**Size:** XS–S · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/detect_orphans.py`)

Filed 2026-08-07 from m4 t4c, from the t4a census. **Established from the code**, not observed on a
run: `last_activity_at` is emitted as `None` at **every** emission site on **all three** adapters —
`fetch_do.py:347, 368, 387, 408, 442`; `fetch_aws.py:502, 530, 559, 602, 623, 651, 681`;
`fetch_linode.py:660, 692, 819, 861, 979`. `modifier_recent_activity` keys on that field and
nothing else, so it and `RECENT_ACTIVITY_WINDOW_DAYS` have never fired against a real inventory
from any provider. The only exercise they get is a synthetic fixture
(`tests/test_detect_orphans.py:419`).

The module comment records this **for DigitalOcean** (`detect_orphans.py:75–77`, *"A no-op for
DigitalOcean, which exposes no such field"*). The census established it is true fleet-wide, which
the comment does not say.

**Not a wrong output.** A modifier that never fires produces no incorrect candidate; it produces a
scoring path that is carried, documented, echoed into the `parameters` block and never exercised.
The risk is that its presence reads as tuned behaviour — C8 now records the universal-null status
beside the constant for exactly that reason.

**Owes:** a decision on whether a permanently-dead scoring path stays. Three defensible outcomes:
keep it with the status documented (done at C8, so this row could close on that basis alone);
gate it behind an adapter capability declaration; or remove it and the constant.
**Costs:** XS to decide, S to remove (the modifier, the constant, the `parameters` key, one test).
**Collides with:** nothing. Removing it would change the emitted `parameters` block — which no
consumer reads: not compose, not the renderer, not the sprint. That write-only status is census
item **D21**, recorded in **§Contracts C8**, and it correctly has no row of its own, being neither
a defect nor a marked consequence.

**Annotated 2026-08-07 (m4 t5c): the rider statement is surfaced; the row is NOT closed.**
`orphans.evaluation_coverage.recent_activity_modifier` now travels and the report states, in both
states, whether the modifier *could fire at all* — *"No resource carries `last_activity_at`, so the
recent-activity modifier could not fire on this inventory … its absence from every candidate below
means it was inapplicable, not that it was applied and found nothing. The window in the parameters
block is therefore not a tuned setting here."*

**The discharge question, assessed rather than assumed.** This row records three defensible
outcomes and notes it *"could close on that basis alone"* if the status were documented. It is now
documented in two places — §Contracts C8 and the rendered report. **It still does not close**, and
the reason is that the row's Done-when is *"a decision on whether a permanently-dead scoring path
stays"*. Documenting a thing is not deciding it. t5c made the situation legible; the choice between
*keep it documented*, *gate it behind an adapter capability declaration*, and *remove it* is
untaken, and closing the row would record a decision nobody made. **Closing it now would also be
closing it because it became convenient**, which the ticket that surfaced it was told not to do.

**Annotated 2026-08-13 (m6 t2c): the headline still holds; its stated cause is now incomplete,
and two of the body's factual claims have gone stale. The row does NOT close.**

*The headline holds.* The modifier still has never fired against a real inventory on any provider.

*The stated cause no longer covers every provider.* This row's mechanism is that
`last_activity_at` is universally null, so the modifier's own predicate can never match. **That
is now false for provider four.** `fetch_github.py:634` emits
`iso_utc(raw.get("last_activity_at"))` — a real value — and the live 2026-08 GitHub inventory
carries **6 of 6** resources with the field populated. The modifier still does not fire there,
but for a **second and different reason**: no rule keys on `seat`, so no candidate is produced,
and `MODIFIERS` run only inside `score()`, which the engine reaches only for a resource a rule
already fired on. So the row now has two causes — *field universally null* on DO/AWS/Linode, and
*no candidate to adjust* on GitHub — where it records one.

*Two stale claims in the body.* "all **three** adapters" is now four. And the AWS emission-site
list gives seven sites (`:502, 530, 559, 602, 623, 651, 681`); there are now **eight** — `:706`
was added after this row was written. Both read at agents `0b32f36`.

*The m6 t5c annotation above quotes a report sentence that now renders in a narrower state.* The
quoted *"No resource carries `last_activity_at`, so the recent-activity modifier could not fire
… its absence from every candidate below means it was inapplicable"* was, when written, the
sentence rendered whenever no resource carried the field — **including on a zero-candidate
inventory, where it quantified over an empty set.** m6 t2c split that: with zero candidates the
report now says the modifier *never ran* because the stage was not reached, and the quoted
sentence renders only when a rule fired and no resource carries the field. The quotation is
still in the template; it is no longer the sentence a reader sees in the case the annotation was
describing.

**What this does not change.** The Done-when is still *"a decision on whether a permanently-dead
scoring path stays"*, and t2c took no such decision — it made the non-firing legible in a third
state, which is the same kind of thing t5c did and was correctly held not to discharge the row.
**But the decision is now harder in a useful way:** "remove it and the constant" was cheap while
no adapter emitted the field, and provider four emits it, so the path is dead-in-practice rather
than dead-by-construction. That belongs to whoever takes this row, not to t2c.

`Source: m4 t4a census item X4; ruled schema-level at m4 t4b under C8. Emission sites read at
agents 611feba; re-read and corrected at agents 0b32f36 (m6 t2c).`

---

### BL-115 — a stopped instance with no attached storage and a non-zero own estimate yields no candidate (#TBD)
**Kind:** defect · **Census item:** F2 · **Contract:** C8
**Size:** S–M · **Priority:** **high** · **Section:** cloudcost (`cloudcost/scripts/detect_orphans.py`)

Filed 2026-08-07 from m4 t4c. Found by the t4a census's **per-rule predicate diff** — an asymmetry
between two same-shaped rules, which no grep and no constants sweep reaches.

**The gap.** `rule_stopped_compute_with_attached_storage` requires attached storage
(`detect_orphans.py:271`, `if not attached: return None`). `rule_stopped_database_with_storage`
instead requires a non-zero own estimate (`:326`, `if own <= 0: return None`). So a **stopped
compute instance with no separately-inventoried volume and a non-zero `monthly_cost_estimate`
matches neither rule** and produces nothing.

**Observed shape on DigitalOcean**, which is what makes this the costly one: DO bills a stopped
droplet **in full**, so its own estimate is the whole droplet price — and a stopped droplet with no
attached volume is exactly the case the catalog misses. On AWS the same shape is harmless, because
a stopped instance's own estimate is `0.0` and the EBS volume carries the charge, so the
attached-storage requirement is the right gate there. **The rule was written against one provider's
billing model and the gap only opens on the other's.**

**Owes:** one of — a third rule (stopped compute, no storage, non-zero own estimate); a widened
predicate on the existing rule (`not attached and own <= 0`); or a recorded blind spot with the
DO consequence stated. Not decided here.
**Costs:** S–M. A firing-set change, so it moves candidate counts, the sprint's rule-legibility
arm's evaluated count, and `tests/test_detect_orphans.py:173`.
**Collides with:** nothing structural. Any fix changes live candidate output on DO.

`Source: m4 t4a census item F2 (class F, structural absence); ruled schema-level at m4 t4b under
C8. Predicates read at agents 611feba.`

---

### BL-116 — the aged-snapshot rule's docstring requires a gate its code does not apply (#TBD)
**Kind:** defect · **Census item:** F3 · **Contract:** C8
**Size:** S · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/detect_orphans.py`)

Filed 2026-08-07 from m4 t4c. **Established from the code.**

`rule_aged_snapshot`'s docstring describes the heuristic as *"age plus a source that is gone"*
(`detect_orphans.py:205–207`). The code requires **only age** (`:213`). The source-is-gone half is
appended as an evidence sentence when `attached_to is None` (`:220–223`) and **silently omitted when
it is not** — so a snapshot of a live volume and a snapshot whose source was deleted fire at the
same `0.7`, and are distinguishable in the report only by whether one evidence line is present.

**Every other rule in the catalog treats `attached_to` as a gate** (`:167`, `:190`, `:235`, `:323`).
This one alone treats it as decoration. That is the asymmetry, and it is why the census flagged it.

**Provider-differing consequence:** on a provider where snapshots of live volumes are routine backup
hygiene, this is a systematic false-positive source at a MEDIUM-band confidence; on one where they
are not, it is harmless. No adapter distinguishes the two today.

**Owes:** either the gate (making the code match the docstring), or a corrected docstring **and** a
reconsidered confidence — because `0.7` was chosen for the two-fact heuristic the docstring
describes, not for the one-fact heuristic the code implements. **Do not fix only the docstring**:
that leaves a confidence calibrated for evidence the rule does not require.
**Costs:** S. Adding the gate shrinks the firing set and moves
`tests/test_detect_orphans.py:114, 268, 380`.
**Collides with:** nothing.

`Source: m4 t4a census item F3 (class F); ruled schema-level at m4 t4b under C8. Read at agents
611feba.`

---

### BL-117 — an out-of-vocabulary `type` is counted everywhere and evaluated by nothing (#TBD)
**Kind:** defect · **Census item:** N8 · **Contract:** C1
**Size:** S · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/_normalized.py`) — **cross-repo**
**Cross-repo:** `../aetheris/scripts/sprint.sh`

Filed 2026-08-07 from m4 t4c. **Established from the code.** First observed at m4 t2 and appended to
BL-074 as a sweep input; this is its own row now that the sweep has ruled.

`usable_resources()` validates that a resource entry has a `type` (`_normalized.py:129`,
`elif not resource.get("type")`) and **never that the type is canonical**. So a resource whose
`type` is outside `CANONICAL_TYPES` is classified **usable**: it is counted in `totals.resources`,
counted in the tag-coverage denominator, carried into the report — and matched by no rule, because
every rule keys on a canonical type. It contributes to every figure and to no finding, silently.

C1 now states the guarantee (*an out-of-vocabulary `type` is a contract violation, not a
pass-through*). This row is the enforcement.

**Owes:** the membership validation in `usable_resources`, skipping with a reason the way a
malformed entry is skipped.
**Costs:** S in `_normalized.py`. **The cost is not there.**

**Collides with — and this is why the row cannot be taken alone.** `../aetheris/scripts/sprint.sh`'s
cloudcost **rule-legibility assertion** has three arms, and its `illegible` arm exists *precisely
because this validation is absent* (`sprint.sh:3048`, `outside = sorted(t for t in emitted if t not
in CANONICAL_TYPES)`). Adding the validation upstream means an out-of-vocabulary type is skipped
before the catalog ever sees it, so:

- the `illegible` arm can no longer fire on that condition — it becomes unreachable, which is the
  chaos-gate shape (BL-107) arriving by a different route;
- the `evaluated + skipped == resources` arm (`sprint.sh:3060`) changes meaning, because the skip
  set now includes a category it never held.

**The row must be sequenced with a sprint change, in one landing.** Taking it alone changes what the
sprint's third arm means without touching the sprint — and leaves an assertion that reads green
because its subject can no longer occur.

**Annotated 2026-08-07 (m4 t5b): the reconciliation target moved.** m4 t5b restructured
`coverage_section` — it now takes a tag-skip sink, builds the tags-in-use table and reports its
cap — so this row's skip-semantics change lands against a **changed** consumer, not the one the
census read. The cross-repo sprint coupling is unchanged and still dominates the sequencing.

**Annotated 2026-08-07 (m4 t5c): the rider statement is surfaced; the validation is not.** The
report now names, in both states, how many usable resources carry a type the rule catalog does not
evaluate — with the resources listed, the candidate total re-stated over the set actually evaluated,
and the tag-coverage denominator's share of it cross-referenced. **Nothing is validated and nothing
is skipped**: `usable_resources` is untouched, the uncatalogued resource is still usable and still
counted, and a test pins that. **The sprint's rule-legibility arm is therefore untouched**, which is
what let the statement land without this row's cross-repo landing.

**One constraint m4 t5b established that this row inherits:** the sprint's rule-legibility arm
reads `orphans["skipped"]` and fires `illegible` on **any** entry, and separately asserts
`evaluated + len(skipped) == len(resources)`. Any new skip category routed into that list fails the
sprint from another repo. m4 t5b's tag-skip sink was deliberately routed into compose's own
`skipped` for that reason; this row's canonicality skip **cannot** be, being a whole-resource skip —
which is precisely why it must land with the sprint change.

`Source: m4 t4a census item N8; ruled schema-level at m4 t4b under C1. Observed at m4 t2 while
wiring the rule-legibility assertion; sprint arms read at harness e75f838.`

---

### BL-118 — five I/O sites decode adapter JSON under the platform default encoding (#TBD)
**Kind:** defect · **Census item:** X5 · **Contract:** C12
**Size:** S · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/`)
**Sibling:** BL-112 — same root cause, different layer; **neither guards the other**

Filed 2026-08-07 from m4 t4c. **Established from the code.** Found by the t4a census's class-H
extraction (literals in any call argument), which is the only class that reaches a missing `encoding=`
kwarg.

`render_report.py` passes `encoding="utf-8"` at **all four** of its I/O sites (`:334`, `:352`,
`:381`, `:404`). `detect_orphans.py` (`:583`, `:613`) and `compose_report_data.py` (`:667`, `:678`,
`:708`) pass **none** at five, so those reads and writes take `locale.getpreferredencoding()`.

**No current artifact differs**, because every value the three adapters emit is ASCII — which is
exactly why this has gone unnoticed. Under a non-UTF-8 locale a non-ASCII resource `name`, `tags`
entry or `region` either raises `UnicodeDecodeError` — breaking the stdout contract the stage-CLI
rule exists to protect — or mis-decodes silently into the candidate identity, the evidence text and
the rendered report.

**The asymmetry is worse than the absence.** The one stage that would *display* the corruption is
the one that already specifies the encoding, so corruption enters **upstream of the only correct
site**.

**Relationship to BL-112, ruled at m4 t4c G3 — two rows, not one.** They share a root cause (an
absent UTF-8 locale) and nothing else: BL-112 is the **harness**, Elixir, the BEAM's
`native_name_encoding` fallback corrupting the `--json` payload's run label;
this is **aetheris-agents**, Python, `locale.getpreferredencoding()` on file I/O in the cloudcost
stages. Different repos, languages, mechanisms and artifacts. **Neither fix addresses the other's
failure**, and a single environment change (exporting `LANG`) would mask both without repairing
either — which is the argument for two rows rather than one, and for each citing the other.

**Owes:** five `encoding="utf-8"` kwargs — byte-neutral on every current artifact — **and a
non-ASCII fixture**, without which the change is unverifiable and the row's own premise untested.
**Annotated 2026-08-07 (m4 t5c): the rider aspect is BLOCKED on this row, not deferred.** t5c's
gate ruled X5 *needs its row*: **the report cannot mark a mis-decode it never detects.** A
mis-decoded name decodes to *something* and nothing downstream knows it is wrong, so there is no
payload fact for a rider statement to read; and `compose` is contractually pure of the environment
(*"no clock, no filesystem, no environment"*), so it cannot report the locale either. The fix
here **prevents** rather than detects, which is why it has no report-side surface. Ruled out with a
reason rather than given a statement that gestures at a risk the report cannot observe.

**Costs: the fixture is the row's real cost.** The kwargs are minutes. A fixture carrying a
non-ASCII resource name, threaded through detect → compose → render with an assertion on the
rendered bytes, is the work.
**Collides with:** nothing. BL-112 may be taken independently in either order.

`Source: m4 t4a census item X5, added at t4a review r1 by the class-G/H extraction extension; ruled
schema-level at m4 t4b under C12. BL-112 relationship ruled at m4 t4c G3. Read at agents 611feba.`

---

### BL-119 — a cost snapshot with a declared total and no line items is silently dropped from discovery (#TBD)
**Kind:** defect · **Census item:** P8 · **Contract:** C10
**Size:** S (the warning) / M (the document-type change) · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`)

Filed 2026-08-07 from m4 t4c. **Established from the code — and the sharp form is that two functions
in one module disagree about what a valid cost document is.**

`service_totals` explicitly supports a snapshot that declares a total without line items
(`compose_report_data.py:193`, `amount = money(declared.get("amount")) if "amount" in declared else
line_items_sum`). `classify` recognises a cost document **only** by the presence of a list-valued
`line_items` key (`:690–700`). So such a snapshot is **legitimate to one and unclassifiable to the
other**.

**The consequence is a silent omission, not an error.** In `--input-dir` mode `discover_bundles`
drops any document `classify` returns `None` for (`:715–716`) with **no warning and no `skipped`
entry**, so the run composes a report missing that provider's costs entirely and exits `ok`. The
same discriminator gates history: `load_prior_snapshots` accepts a document only if
`classify(document) == "cost"` (`:768`), so the month-on-month baseline silently loses it too.

**Owes, in two steps, and the first is worth taking alone:**
1. **A warning and a `skipped` entry** for any document `classify` cannot type. Cheap, and it
   converts a silent omission into a reported one — the property that matters.
2. The C10 change proper: documents carry an explicit `document_type`.

**Costs:** step 1 is S. Step 2 is **expensive and the row should say so**: it touches all three
adapters, `detect_orphans`'s output, every fixture, and the history tree **already on disk**, whose
snapshots carry no such key and would need a compatibility read.
**Collides with:** BL-070 (retires dormant merge code in the same module) and BL-076 (`load_prior_snapshots`
globbing) — all three edit `compose_report_data.py`, and BL-070 asks to be a dedicated cleanup.
Sequence them.

**Annotated 2026-08-07 (m4 t5b).** **Both steps stay filed**, including step 1, which m4 t5b's
first scoping had put in tier 1. Its subject is `discover_bundles` — the `--input-dir` route —
which is **the surface BL-131 decides the support of**. Deferring a decision about a surface and
then investing in it is incoherent, so step 1 waits on BL-131 with step 2.

**Annotated 2026-08-10 (m5 t2). This row stays open and is now unambiguously in scope.** The wait
is over and it ended in retention: **m5-D2** (`cloudcost/m5-n1-compose.md` §Ratified decisions)
retains the N>1 compose surface as a library-and-CLI capability the pipeline does not invoke. Its
own text names this row — *"**BL-119** stays open and is now unambiguously in scope, because the
route it concerns is retained."* The incoherence the m4 t5b annotation named is gone in the
direction that keeps the work: `discover_bundles` is retained code, so investing in it is coherent,
and **both steps are now takeable on their own merits** rather than blocked on a decision.

**Step 1 is the one to take, and the ruling sharpens why.** A silent drop is worse on a retained
surface than on one awaiting deletion: the surface is advertised in `cloudcost/tools.json` with a
worked example, so an operator can reach `--input-dir` mode by following documentation and get a
report missing a provider's costs with an `ok` exit. Step 1 converts that into a reported omission
and does not depend on step 2's schema change.

**Cross-reference — BL-136.** The read-only cross-provider summary filed 2026-08-10 reads the
persisted per-provider snapshots, and its third requirement is *"say when a declared total has no
line items"*, which cites this row. **The two are not duplicates and neither closes the other**:
this row fixes the silent drop in `discover_bundles` at compose time; BL-136 must handle the same
snapshot correctly in a reader that never invokes compose. Whichever lands first, the other still
owes its own handling — and if this row's step 2 ever gives documents an explicit `document_type`,
BL-136's reader is a second consumer that would need the compatibility read step 2 already costs.

`Source: m4 t4a census item P8; ruled schema-level at m4 t4b under C10. Read at agents 611feba.`

---

### BL-120 — the idle-load-balancer rule rests on a `tag:` convention nothing enforces (#TBD)
**Kind:** defect · **Census item:** D16 · **Contract:** C7
**Size:** XS to check · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/detect_orphans.py`)

Filed 2026-08-07 from m4 t4c. **Established from the code.**

`rule_idle_load_balancer` fires on `type == load_balancer` and `attached_to is None`, at `0.85` —
HIGH band. Its correctness rests entirely on a premise stated in its own docstring
(`detect_orphans.py:230–232`): a **tag-targeted** load balancer carries
`attached_to == "tag:<name>"` and therefore never reaches the rule.

That convention **originates in one adapter's normalizer, is emitted by no other adapter, is
enforced by nothing, and is asserted by no test.** C7 now makes it part of `attached_to`'s
definition, which is the contract half. This row is the check.

**This row owes a check, not a fix.** The question is prior to any change:

> On DigitalOcean and Linode, can a load balancer **in active use** present with `attached_to is
> None`?

If yes, that adapter is already producing HIGH-band false positives and the row becomes a defect
with a known blast radius. If no, the convention holds by accident on those adapters and the row
becomes a test plus the C7 obligation. **Verify and record the answer before proposing anything** —
the fix differs completely between the two outcomes, and proposing one now would be the guess this
row exists to prevent.

**Costs:** XS to answer (read the two adapters' load-balancer normalizers and their fixtures). The
fix is unscoped until the check runs.
**Collides with:** nothing until the answer is known.

`Source: m4 t4a census item D16; ruled schema-level at m4 t4b under C7. Read at agents 611feba.`

---

### BL-121 — the untagged-spenders cap truncates across all providers and reports nothing (#TBD)
**Kind:** defect · **Census item:** P2 · **Contract:** C11
**Size:** XS · **Priority:** low–medium · **Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`)

Filed 2026-08-07 from m4 t4c. **Established from the code.**

`coverage_section` sorts untagged resources by estimate **across all providers combined** and then
truncates to `top_untagged` (`compose_report_data.py:388–408`). At N>1 a provider whose resources
are individually cheap can be **absent from the table entirely** while another fills every row —
and nothing in the payload records that anything was dropped.

**The same file argues against exactly this, one section away.** `region_coverage_section`'s
rationale (`:521–534`) invokes decision D's no-silent-caps clause: *"a sweep narrowed by an override
or by a failed region enumeration is visible rather than quietly shrinking the inventory behind an
unchanged-looking report."* The spenders cap is that shape, unguarded.

**Owes:** the dropped count in the payload — how many untagged resources exist beyond `top_k`, and
ideally the per-provider breakdown, so an absent provider is visible as absent rather than as
having nothing to report.
**Costs:** XS. Additive to the payload; the template may render it or not.
**Collides with:** BL-101, which redesigns the tag section (adds a tags-in-use table and carries the
`reported` block through). Same section, same file — take together or sequence.

**Annotated 2026-08-07 (m4 t5b).** **The cap-truncation gap is fixed** — `untagged_not_shown` and
`tags_not_shown` now travel in the payload and render in both states, and the fix does **not**
depend on BL-131. **The row's stated consequence does.** *"A provider can be absent from the table
entirely"* requires the N>1 compose path, whose support BL-131 decides; at N=1 the same cap drops
rows without dropping a provider. **Not re-characterised here** — doing so now would pre-empt
BL-131's ruling.

`Source: m4 t4a census item P2; ruled schema-level at m4 t4b under C11. Read at agents 611feba.`


**DONE 2026-08-07 (m4 t5b).** `untagged_not_shown` travels in the payload and the template states
the truncation in both states — *"N further untagged resource(s) are not shown"* and *"Every
untagged resource is shown; the cap of N dropped none."* Zero is emitted explicitly rather than
omitted, so *nothing dropped* and *nobody counted* are different renderings (absent-is-unknown).
The same treatment was given to the new tag table, which BL-101's own text required.
`test_the_cap_reports_what_it_dropped_in_both_states`,
`test_the_spenders_cap_states_what_it_dropped_in_both_states`.

**The row's stated consequence is not closed by this** — see the annotation above: *"a provider can
be absent from the table entirely"* needs the N>1 path, which BL-131 decides. The cap-truncation
gap itself was real at any N and is fixed.

**Framing resolved 2026-08-10 (m5 t2) — and with it the row closes.** **m5-D2**
(`cloudcost/m5-n1-compose.md` §Ratified decisions) rules the N>1 compose surface **retained as a
library-and-CLI capability the pipeline does not invoke**. So this row's stated consequence —
*"a provider can be absent from the table entirely while another fills every row"* — is
**true of the surface and unreachable from the pipeline**: every orchestrator run composes one
bundle, and at one bundle the cap drops rows without dropping a provider. It is not withdrawn and
not re-characterised as a defect; it is **correctly stated and source-only**, which is the third
reading this row could not choose between while BL-131 was open.

Nothing further is owed. The **fix** landed at m4 t5b and never depended on the ruling; the
**framing** was the whole of what waited, and it is settled here. C11 carries the same declaration
in `cloudcost/milestone.md` §Contracts, where a reader meets it.

`Source: m5-D2, ratified 2026-08-10; framing applied at m5 t2, 2026-08-10.`

---

### BL-122 — `source_granularity` is carried into the report and validated nowhere (#TBD)
**Kind:** defect · **Census item:** P11 · **Contract:** C10
**Size:** XS–S · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`)

Filed 2026-08-07 from m4 t4c. **Established from the code.**

`source_granularity` exists to make decision D4's honesty claim checkable — that cost totals are
service-level and per-resource dollars are estimates. `service_totals` copies it into the payload
(`compose_report_data.py:210`) and **compares it against nothing**. All three adapters declare
`"service"` (`fetch_aws.py:747`, `fetch_do.py:304`, `fetch_linode.py:554`), so the field has never
been anything else and the absence of a check has never cost anything.

**This row is an absent guard, not a wrong output — and it should be triaged as one.** Nothing is
incorrect today. What is missing is the mechanism that would notice if it became incorrect: a
provider emitting account-level costs would have them grouped by service exactly as if they were
service-level, and the only trace would be a string in the report that nothing reads.

**Owes:** the enumeration (what values are valid) and the comparison — `service_totals` warns on a
granularity coarser than service.
**Costs:** XS–S. A warning in the existing warnings list; no payload shape change.
**Collides with:** BL-071, which proposes resource-level AWS cost carrying
`source_granularity: "resource"`. That is a **finer** granularity, which this guard must not reject —
whoever takes either row should read the other first, because a guard written as *"must equal
service"* would block BL-071 outright.

**Annotated 2026-08-07 (m4 t5c): the rider statement is surfaced; the guard is not.** The report
now says the granularity column states what each provider *declared* and that nothing verifies it —
*"a snapshot declaring a coarser granularity than service would be grouped by service exactly as if
it were service-level, and this report would not say so. Declared, not checked."* **Template-only**:
`service_totals` is byte-unchanged, so the N>1 deferral is untouched and this row's enumeration and
comparison are entirely still owed. The BL-071 caution stands — a guard spelled *"must equal
service"* would block resource-level cost.

`Source: m4 t4a census item P11; ruled schema-level at m4 t4b under C10. Read at agents 611feba.`

---

### BL-123 — `age_phrase` truncates, so the evidence sentence contradicts its own threshold (#TBD)
**Kind:** defect · **Census item:** D12 (display half) · **Contract:** C3
**Size:** XS · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/detect_orphans.py`)

Filed 2026-08-07 from m4 t4c. **Established from the code.**

Age is a **float** of days (`detect_orphans.py:135`, `/ 86400.0`) and a rule fires on age *strictly
greater* than its threshold (`:170`, `:213`, `:268`, `:329`). `age_phrase` renders it with
`int(age)` (`:141`), which **truncates**.

So a resource of age 14.9 days fires against a 14-day threshold and renders as:

```
unattached for 14d (created …, ref …); threshold >14d
```

**The number is right and the sentence contradicts itself** — it reports an age that, as printed,
would not have fired. The candidate is correct; its evidence is not readable as a justification,
which is what evidence is for.

**Owes:** either rounding, or a stated display convention (e.g. one decimal place, or *"14d+"*).
A decision, not a design.
**Costs:** XS, confined to `age_phrase`. It changes evidence strings, so any test asserting evidence
text moves.
**Collides with:** nothing.

`Source: m4 t4a census item D12, display half; the comparison half is stated as contract at m4 t4b
under C3. Read at agents 611feba.`

---

### BL-124 — C3: reject a naive timestamp rather than assuming UTC (#TBD)
**Kind:** contract consequence · **Census item:** N3 · **Contract:** C3
**Size:** S · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/_normalized.py`)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today** — this is a stated contract the code has
not yet met.

**C3 requires:** ISO-8601 **with offset** for `created_at`, `last_activity_at` and `generated_at`; a
naive timestamp is **rejected**, not assumed UTC.

**The code today:** `parse_timestamp` accepts a naive timestamp and stamps it UTC
(`_normalized.py:76–77`, `if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=timezone.utc)`).

**Why the contract says reject.** On a provider emitting local time the assumption produces age
errors of up to a day, in the direction that **suppresses** rule firings — a silent wrong answer
rather than a parse failure. Rejecting surfaces it through `timestamp_warnings`, which already
exists for exactly this.

**Costs:** S — but the sequencing matters and the contract does not state it: a naive stamp
currently parses, so flipping to rejection could turn existing fixtures' timestamps into warnings.
**Sweep all three adapters' fixtures for naive timestamps before flipping**, or the change lands as
a fixture regression rather than a contract fix.
**Collides with:** BL-125 (same module, same contract).

`Source: §Contracts C3 at m4 t4b, marked [code consequence]; census item N3. Code claim **read**
(not inherited) at agents 1779368: `_normalized.py:76-77`, `if parsed.tzinfo is None: parsed =
parsed.replace(tzinfo=timezone.utc)`.`

---

### BL-125 — C3: name the timestamp field set once instead of hardcoding the pair (#TBD)
**Kind:** contract consequence · **Census item:** D20 · **Contract:** C3
**Size:** XS · **Priority:** low · **Section:** cloudcost (`cloudcost/scripts/detect_orphans.py`, `cloudcost/scripts/_normalized.py`)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today.**

**C3 requires:** the schema's timestamp field set is **named once**, and read by both the function
and the contract.

**The code today:** `timestamp_warnings` hardcodes the pair `("created_at", "last_activity_at")`
(`detect_orphans.py:431`) — a hand-maintained restatement of what the schema's timestamp fields are.
A third timestamp added to the schema is unchecked unless someone remembers that line. It is the
hand-typed-vocabulary class, one level below the one BL-074 swept.

**Costs:** XS. Additive extraction into `_normalized.py`; no behaviour change while the set stays
two.
**Collides with:** BL-124 (same contract). Cheap enough to ride along with it.

`Source: §Contracts C3 at m4 t4b, marked [code consequence]; census item D20. Code claim **read**
(not inherited) at agents 1779368: `detect_orphans.py:431`, `for field in ("created_at",
"last_activity_at"):`.`

---

### BL-126 — C4: carry the currency's minor-unit exponent and round to it (#TBD)
**Kind:** contract consequence · **Census item:** N5 · **Contract:** C4
**Size:** M · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/_normalized.py`, all three adapters)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today** — all three adapters declare `USD`
(`fetch_aws.py:71`, `fetch_do.py:56`, `fetch_linode.py:89`), and the 2dp rounding is correct *only
because they agree*.

**C4 requires:** the minor-unit exponent belongs in the cost snapshot beside `currency`, and
`money()` takes it.

**The code today:** `money()` rounds to a hardcoded two decimal places (`_normalized.py:92`). Two
decimals is wrong for a zero-decimal currency (JPY, KRW) and wrong for sub-cent unit pricing — of
which Linode's own price surface already carries an instance (`fetch_linode.py:728`, a recorded
`unit_price 0.0015`).

**Costs: M, and this is the expensive one in this group.** It changes `money()`'s **signature** and
therefore **every call site** — 14 across the four shared scripts, plus the adapters. It also
interacts with the deliberate arithmetic order in `service_totals` (`:191` sums the *rounded* rows
*"so the column adds up on paper"*), which would need restating rather than merely re-rounding.
**Collides with:** nothing filed. **The reconcile tolerance (census item P3) rides along with this
row and has no row of its own**, by C4's own wording — *"the reconcile tolerance is currently
absolute … or stated per currency **alongside that exponent**"* — so P3 carries no
`[code consequence]` marker and none was filed. Whoever takes this row takes the tolerance with it;
a reader looking for a separate P3 row will not find one, and should not.

`Source: §Contracts C4 at m4 t4b, marked [code consequence]; census item N5. Code claims **read**
(not inherited) at agents 1779368: `_normalized.py:92` (`return round(float(value), 2)`); the
sub-cent instance is `VOLUME_PRICE_BASIS_EVIDENCE`, `fetch_linode.py:728-730`, whose string
literal carries `unit_price 0.0015` on `:729` — cited as the assignment rather than the line,
because the line is the fragile half.`

---

### BL-127 — C6: a non-`str` tag element is a counted skip, not a silent drop (#TBD)
**Kind:** contract consequence · **Census item:** N7 · **Contract:** C6
**Size:** S · **Priority:** low–medium · **Section:** cloudcost (`cloudcost/scripts/_normalized.py`)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today** — all three adapters emit `list[str]` by
construction.

**C6 requires:** a non-`str` tag element is a **counted skip**, surfaced the way `usable_resources`
surfaces a malformed resource.

**The code today:** `tags_of` filters non-`str` elements out silently (`_normalized.py:112`,
`[t for t in tags if isinstance(t, str)]`) — no warning, no `skipped` entry. An adapter emitting the
wrong element type would have every tag vanish, taking `tag_coverage` to `0.0` and switching off the
untagged-in-tagged-account governance rule. **A clean-looking zero**, which is the failure shape this
contract set exists to name.

**Costs:** S. `tags_of` currently returns a list and has no skip sink, so it needs one — which means
touching both callers (`has_keep_tag`, `tag_coverage`) and `coverage_section` in compose.
**Collides with:** BL-121 and BL-101 both edit the tag-coverage path.

`Source: §Contracts C6 at m4 t4b, marked [code consequence]; census item N7. Code claim **read**
(not inherited) at agents 1779368: `_normalized.py:112`, `return [t for t in tags if isinstance(t,
str)] if isinstance(tags, list) else []`.`


**DONE 2026-08-07 (m4 t5b).** `tags_of` takes an optional skip sink; a non-`str` element is
recorded with its `resource_id`, index and type rather than silently filtered.
`test_a_non_string_tag_element_is_counted_not_silently_dropped` asserts both states — a clean
inventory records no tag skip, a broken one records exactly two with their reasons.

**The sink is opt-in per caller, and that is the row's real content.** The sprint's rule-legibility
arm reads `orphans["skipped"]`, fires `illegible` on **any** entry, and separately asserts
`evaluated + len(skipped) == len(resources)`. A tag-element skip is neither a whole resource nor an
unreadable one, so routing it there would have failed the sprint **from another repo**.
`detect_orphans` therefore passes no sink and is byte-identical to its pre-BL-127 behaviour;
`compose_report_data` passes its own report-data sink, which nothing in the sprint reads.
`test_the_tag_skip_sink_never_reaches_the_orphan_artifacts_skipped_list` pins the constraint so it
cannot regress silently.

---

### BL-128 — C6: the keep marker becomes a first-class field, not a tag spelling (#TBD)
**Kind:** contract consequence · **Census item:** D6 · **Contract:** C6
**Size:** M · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/`, all three adapters)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today**, but the current spelling is reachable
unevenly across providers, which is the substance of BL-074's own phrase for it:
*an adapter convention masquerading as a shared constant.*

**C6 requires:** the exclusion marker is a **first-class normalized field**; each adapter decides how
its own tag surface expresses it; shared machinery reads a boolean.

**The code today:** `KEEP_TAG = "keep=true"` (`detect_orphans.py:84`), matched case-folded against
the flat tag list (`:112`). The `k=v` spelling is **native only on AWS**, whose adapter constructs it
(`fetch_aws.py:438`); on DigitalOcean and Linode a tag is a flat string, so `keep=true` must be typed
literally as a tag name — established for Linode at `cloudcost/docs/m3-linode-scout.md:925–928`
(*"writable by hand but is not a native key/value construct"*).

**Costs:** M. §Normalized extension (a new resource field), all three adapters, every fixture
carrying a keep tag, `has_keep_tag`, and the `excluded[].reason` string that prints the constant.
**Collides with:** BL-098 — both are §Normalized extensions, and BL-098 records that the
emit-with-a-real-value-or-`null` rule obliges *every* adapter to emit any new key. Sequence them so
the schema moves once.

`Source: §Contracts C6 at m4 t4b, marked [code consequence]; census item D6. Code claims **read**
(not inherited) at agents 1779368: `detect_orphans.py:84` (`KEEP_TAG = "keep=true"`), `:112`
(`tag.strip().lower() == KEEP_TAG`), `fetch_aws.py:438` (`out.append(f"{name}={value}" if value
else str(name))`).`

**Annotated 2026-08-07 (m4 t5b): sequence this AFTER m4 t5b, not merely apart from it.** BL-101's
Done-when required an acceptance test on a `keep=true` resource, and that test now exists
(`tests/test_render_report.py::test_a_reported_resource_never_appears_in_the_orphan_section`).
This row **replaces the spelling that test is written against**, so taking it will rewrite a test
written days earlier — expected, and cheaper to know now than to meet as a surprise regression.

---

### BL-129 — C10: service identity needs a stable identifier beside the display name (#TBD)
**Kind:** contract consequence · **Census item:** P6 · **Contract:** C10
**Size:** M–L · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`, all three adapters)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today**, and the failure it prevents is invisible
until it happens.

**C10 requires:** a stable service identifier beside the display name.

**The code today:** service names are raw provider strings, grouped by exact string match
(`compose_report_data.py:176–177`) and keyed by the month-on-month delta as `(provider, service)`
(`:279–280`). So **any** change in a provider's service naming between two months reports the old
name as `removed` and the new one as `new` — a full swing in both directions, with nothing
indicating they are the same service. Linode additionally emits a literal `Tax` service line
(`fetch_linode.py:116`), so the vocabulary is not even uniform in kind.

**Costs: M–L, and the contract already names why.** *"Expensive — prior snapshots on disk carry the
old names."* The history tree is the persisted month-on-month baseline; introducing an id means
either backfilling it or reading both shapes for a transition period. That, not the adapter change,
is the work.
**Collides with:** BL-076 (`load_prior_snapshots`, same MoM path) and BL-070 (same module, dedicated
cleanup). Sequence.

`Source: §Contracts C10 at m4 t4b, marked [code consequence]; census item P6. Code claims **read**
(not inherited) at agents 1779368: `compose_report_data.py:176-177` (grouping by exact service
string), `:279-280` (the `(provider, service)` delta key), `fetch_linode.py:116` (`TAX_SERVICE =
"Tax"`).`

---

### BL-130 — C11: promote `swept_regions` to a first-class optional envelope field (#TBD)
**Kind:** contract consequence · **Census item:** P7 · **Contract:** C11
**Size:** S–M · **Priority:** medium · **Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`, `cloudcost/scripts/fetch_aws.py`)

Filed 2026-08-07 from m4 t4c. **Nothing is broken today.** The current read is deliberate, sanctioned
and works.

**C11 requires:** the sanctioned provider-extra read is promoted out of the opaque provider payload
block into a **first-class optional envelope field**, at which point the m2 A4 exception disappears
entirely.

**The code today:** `SWEPT_REGIONS_KEY = "swept_regions"` is lifted from `cost["provider_extra"]`
(`compose_report_data.py:516, 539–540`) as **one named constant**, precisely so the block is never
iterated generically. The census's ruling test puts it in the schema because
`region_coverage_section` **keys on its presence** — the section appears or does not appear because
of it — which is keying, not carrying.

**Why promote it rather than leave a working exception.** Today only a **comment** prevents a second
such read (`:511–515`). A first-class field removes the precedent instead of documenting it.

**Costs:** S–M. `fetch_aws.py:765` moves the key up a level; `region_coverage_section` reads the
envelope; `render_report.OPTIONAL_FIELDS` is unchanged (it already reads the report payload, not the
provider block); `tests/test_render_report.py:404, 791` guard the tuple choice and should stay green.
DigitalOcean and Linode emit no such key, and their reports must stay byte-identical.
**Collides with:** BL-098 — the **inventory** envelope has no extras key at all, and this is the
**cost** envelope's equivalent question. Ruled at m4 t4c G3 as **adjacent, not duplicate**; they are
two halves of one §Normalized decision and should be sequenced together.

`Source: §Contracts C11 at m4 t4b, marked [code consequence]; census item P7. BL-098 relationship
ruled at m4 t4c G3. Code claims **read** (not inherited) at agents 1779368:
`compose_report_data.py:516` (`SWEPT_REGIONS_KEY`), `:539-540` (the guarded lift),
`fetch_aws.py:765` (the only emitter), and `render_report.py:219` — `value = data.get(key)` inside
the `OPTIONAL_FIELDS` loop, confirming it reads the **report payload**, not the provider block.`

---

### BL-131 — decide whether the N>1 compose path is a supported surface (#TBD)
**Kind:** decision · **Census items:** n/a (surfaced by the m4 t5b gate) · **Contract:** C4, C11
**Size:** S to decide, M–L to implement either way · **Priority:** medium
**Section:** cloudcost (`cloudcost/scripts/compose_report_data.py`, `cloudcost/milestone.md`)

Filed 2026-08-07 from m4 t5b's G2 gate-stop. **This row exists because three documents describe
the same code three different ways and no decision record settles it.**

**The three states, and each is asserted somewhere.**

| State | Asserted by | Reading |
|---|---|---|
| **dead** | **BL-070** — *"decision H … makes the N-merge … unreachable"* | delete it |
| **live at the first fan-out** | `cloudcost/milestone.md` §Open items — *"latent while m1 is DO-only single-currency; **live at the first fan-out**"* | fix it before provider four |
| **advertised but uninvoked** | established at m4 t5b (below) | decide whether to support it |

**The reachability derivation** (m4 t5b G7, at agents `6832159`): the N>1 path is reachable only
through `--input-dir` → `discover_bundles`. The orchestrator
(`cloudcost/agents/cloudcost_orchestrator.exs:258, 263`) passes **exactly one**
`--cost`/`--inventory`/`--orphans` triple, and `--input-dir` appears in neither the orchestrator,
`../aetheris/scripts/sprint.sh`, nor `cloudcost/runbook.md`. **But it is declared in
`cloudcost/tools.json` (`args[3]`) with a worked example** — *"`--input-dir output/aws
--output-dir output/aws --history-dir history/aws`"* — so it is a documented tool interface, not a
stray flag. Note the example points at **one** provider's directory: even the advertised use is
N=1. **So N>1 is an emergent capability of a supported interface that nothing advertises, tests or
invokes** — and those are two separable questions this row must not conflate.

**Resolving this requires amending §Contracts either way.** C4's currency paragraph ratifies the
one-currency-scalar policy as *"correct, and m1's stated position"* and states its blast radius as
*"blanks the report's headline number for **every provider**"*; C11's P2 paragraph describes the
spenders cap as applied *"after a global sort **across all providers**"*. **Both describe
cross-provider behaviour that only exists because the N-merge exists.** Whichever way this goes,
those two paragraphs change — kept and justified, or rewritten as superseded by decision H.

**The knock-ons resolve with it, not before it:**

- **BL-121**'s stated consequence (*"a provider can be absent from the table entirely"*) is
  reachable only on this surface. The cap-truncation gap itself is real at any N and was fixed at
  m4 t5b; only the framing waits.
- **BL-119**'s subject is `discover_bundles`, which is this surface.
- **BL-070**'s remaining deletion targets are all premised on this being dead.

**Owes:** a ruling — supported, or removed — and the §Contracts amendment that follows it.
**Costs:** the decision is cheap; either implementation is M–L, because "supported" means tests and
a sprint leg for N>1 and "removed" means deleting a declared tool interface and its manifest entry.
**Collides with:** BL-070, BL-119, BL-121's framing, C4, C11.

**It blocks nothing in m4 and it blocks provider four.** Sequence: **after the harness
consolidation round, before provider four** — the first fan-out is exactly when the wrong answer
starts costing.

**Scoped 2026-08-09 into `cloudcost/m5-n1-compose.md`** — a two-ticket round
with a gate stop: t1 establishes read-only and stops, the reviewer rules, t2
applies the ruling and amends §Contracts. Both tickets' §6 anatomy is authored
there before either opens, per hc-consolidation R12. **This row is not amended
by that scoping** — it states the same question it stated when filed, and the
round is where the answer will be.

`Source: m4 t5b G2 gate-stop and G7, 2026-08-07. Reachability derived at agents 6832159; the
orchestrator, sprint, runbook and tools.json all read at that commit.`

---

### BL-131 — DONE 2026-08-10 (m5 t2) — closed on the ruling: **retained and bounded**

The row asked for *"a ruling — supported, or removed — and the §Contracts amendment that follows
it."* Both have landed. **m5-D2** (`cloudcost/m5-n1-compose.md` §Ratified decisions), ratified
2026-08-10 at the m5 gate stop, rules the surface **neither supported nor removed but retained and
declared**: *"It is a library-and-CLI capability the pipeline does not invoke, and it is declared
as such."*

**The three states this row could not choose between are all answered, and none was the answer.**
Not **dead** — m5 t1's **E1** found three routes reaching N>1, not the one this row derived, and
the route-bearing code byte-unchanged since `6832159`, so the derivation was incomplete rather
than overtaken. Not **live at the first fan-out** — decision H makes provider four a fourth solo
run, so nothing about a fourth provider brings the path into the pipeline, and the urgency this
row borrowed from the first fan-out was borrowed from an event H forecloses. **Advertised but
uninvoked** is what holds, and it is a state that needed declaring rather than resolving.

**Its own framing, corrected where t1 falsified it.** This row's reachability derivation states
*"the N>1 path is reachable only through `--input-dir` → `discover_bundles`"*. **E1** established
that `bundles_from_args` reaches N>1 with no `--input-dir` at all, the three flags being
`action="append"`. The row's **conclusion** — that no orchestrator invocation reaches N>1 — is
unaffected and was confirmed at HEAD by this ticket's step-1 gate; only its route count was wrong.
Recorded here rather than silently inherited, because a later reader citing this row would
otherwise carry the one-route claim forward.

**What landed, and where a reader meets it** — m5-D2's four declaration requirements, all
discharged at m5 t2: §Contracts **C4** and **C11** in `cloudcost/milestone.md` each carry a
*Source-only by ruling* paragraph and each one's m4 t5b pointer block is discharged in place;
`cloudcost/scripts/compose_report_data.py`'s module docstring states the pipeline invokes it at one
bundle, with no executable line changed; `cloudcost/runbook.md`'s now-unreachable sentence is
corrected to reachable-and-uninvoked; and the rows that resolve with this one carry their
dispositions — **BL-070** not taken, **BL-121** framing resolved, **BL-132** keeping its census
with two instances answered, **BL-119** open and now unambiguously in scope.

`Source: BL-131 filed 2026-08-07 from m4 t5b's G2 gate-stop; scoped 2026-08-09 into
cloudcost/m5-n1-compose.md; established read-only at m5 t1 (E1–E8); ruled as m5-D2 2026-08-10 at
the gate stop per R12; applied at m5 t2, 2026-08-10.`

---

### BL-132 — establish, per contract, whether the behaviour it states is reachable from the live pipeline (#TBD)
**Kind:** method · **Census items:** n/a (surfaced by the m4 t5b gate) · **Contract:** all of C1–C15
**Size:** S · **Priority:** medium · **Section:** cloudcost (`cloudcost/milestone.md` §Contracts)

Filed 2026-08-07 from m4 t5b's G2 gate-stop. **The method finding, which is the row:**

> **The m4 t4a census swept *code*. §Contracts at t4b stated that code as *contract*. Neither step
> established *reachability*.**

So §Contracts can state — accurately, as a description of the source — behaviour that no live
invocation can produce. **C4 and C11 are the two known instances**: both describe cross-provider
behaviour, and the cross-provider path is reachable only through a CLI flag the orchestrator never
passes (BL-131). Neither contract is *false*; each describes the source correctly. The gap is that
a reader — including the reviewer who wrote the ruling that m4 t5b's gate stopped — can cite a
contract as authority without knowing whether it describes a path anything takes.

**Two is not a census.** That is this row's whole point, and it is the same lesson BL-074 was filed
for: *"the one seam"* was an observation. Two contract instances found by accident, through a
collision map, are an observation too.

**The method, which is cheap and bounded — and the row states it so the work is not mis-scoped:**

- **The entry point is `cloudcost/agents/cloudcost_orchestrator.exs`.** Everything the pipeline
  runs, it runs from there. Anything reachable only through a CLI flag the orchestrator never
  passes is **source-only**.
- For each contract C1–C15, ask one question: *is the behaviour this states produced by any
  invocation the orchestrator makes?* Answer **reachable**, **source-only**, or **untested** —
  and where source-only, say whether the contract should be kept, qualified, or superseded.

**This is a reachability check, not decision-record archaeology.** It does not ask what any
milestone decided or when; it asks what the current entry point can produce. Scoped as archaeology
it becomes a multi-day read of five milestone documents, which is not what it is for and not what
it costs.

**Owes:** the per-contract table, and a qualifying sentence in each contract found source-only.
**Costs:** S. Fifteen contracts, one question each, one entry point.
**Collides with:** BL-131, which decides the two known instances. **Take BL-131 first** — otherwise
this row re-derives its answer and then has to change it.

**Annotated 2026-08-09.** BL-131 is scoped in `cloudcost/m5-n1-compose.md`. This
row's *"Take BL-131 first"* clause is unchanged; the round to take first now has
a document.

**Annotated 2026-08-10 (m5 t2). This row stays open, and its census is not run here.** BL-131 has
been taken first, as this row required: **m5-D2** rules the N>1 surface retained and declared, and
m5 t2 amended **C4** and **C11** accordingly. **The two known instances are answered, so the census
need not re-derive them** — each now carries a *Source-only by ruling* paragraph naming m5-D2, and
each one's m4 t5b pointer block is discharged in place. Start from **C1**; C4 and C11 are done and
their answer is **source-only**, with the qualifying sentence this row asks for already written.

**What is unchanged is the row's whole point.** Two contract instances found by accident are still
not a census, and the remaining thirteen are still unexamined. m5 t2 deliberately did **no**
reachability work over C1–C15 — its ticket forbids it (*"no reachability work over C1–C15 (BL-132's
row)"*) — precisely so that this row's method runs once, over the full set, rather than being
half-done as a side effect of another ticket.

**Annotated 2026-08-10 (m5 t2), marked as such 2026-08-11.** The paragraph below landed at
`305b3a1`, in the same commit as the annotation block above it, and until now carried no opening
marker — so it read as text filed 2026-08-07. Its wording is unchanged.

**One thing m5 t1 supplies that this row's method should use.** BL-132 names the entry point as
`cloudcost/agents/cloudcost_orchestrator.exs` and asks one question per contract. m5 t1's **E1**
showed that *"reachable only through a CLI flag the orchestrator never passes"* undercounted the
routes to the same surface by two. The method survives — the question is still *is this produced by
any invocation the orchestrator makes?* — but the answer for a source-only contract should
**enumerate the routes it is reachable by**, not just assert the orchestrator misses one.

**Taken 2026-08-11. Anatomy and method refinements, authored by the reviewer before the row
is worked, per R12.**

**Shape — light, and one part of it is new.** Taken directly as a backlog row: one
implementation-notes file, no round document, no review file — the shape **BL-084**,
**BL-085** and **BL-096** were taken in. **Those three carried no anatomy at all**, so the
`Touches` and `Done-check` below are an addition to that shape rather than a relocation of
§6's fields into it. They are added because both earned their place in m5: a scoping a
ticket may not exceed, and a completion condition a ticket cannot declare for itself.

**Touches.**

- `cloudcost/milestone.md` — **§Contracts only**: a reachability sentence in each contract
  found source-only, and nothing else. **C4 and C11 are neither re-derived nor re-edited** —
  m5 t2 answered both, and each already carries its qualifying paragraph.
- `docs/backlog-2026-06.md` — **this row only**.
- `cloudcost/docs/bl-132-implementation-notes.md` *(new)*.

Nothing else. Any other path that changes is a deviation and is named in the notes.

**Do not generate.** No change to any executable line. **No amendment to any contract's
guarantee** — only to what it claims about reachability. No new contract, no renumbering, no
edit to a contract's `Closed arm` rulings. **No decision-record archaeology**: this row
forbids it in its own text, and the population is the source at HEAD, not five milestone
documents.

**Done-check.**

```bash
# 1. The offline spine, unchanged — this row changes no executable line. Re-resolve both
#    anchors at HEAD before running: cloudcost/runbook.md §Offline tests for the command,
#    CLAUDE.md §Commands for the root. A differing count is a finding, not a pass.
python3 -m pytest cloudcost/tests/ -v

# 2. The census covers its population. Print §Contracts' identifier enumeration beside the
#    table's rows and show they match. A table with a row missing is not a census, and a
#    count without its enumeration is not an answer.

# 3. Every contract found source-only carries its sentence in the file, read back from the
#    file rather than from the packet.
grep -n 'BL-132' cloudcost/milestone.md

# 4. Nothing outside Touches changed.
git status --short
```

**Method — three refinements on what this row already states.**

1. **Execution before reading.** The two STEP 3 arg forms are the entry point and they can
   be *run* — over recorded fixtures, with those exact forms, capturing the payload and the
   rendered report. A contract is then checked against **what came out**, not against source
   read for what it implies. Where a contract's subject sits upstream of compose, say so and
   check it differently; do not stretch one instrument across the whole set. m5 t1 settled in
   one run what three documents had disagreed about.
2. **Three contracts state reachability about themselves — those are claims to check, not
   answers to inherit.** C3 names a wall-clock fallback unreachable on all three adapters;
   C8 says a modifier never fired against any real inventory; C12 says its own guarantee does
   not hold. BL-131's entire cost was a reachability claim taken on a document's word.
3. **C13 has no reachability question.** It states field ownership and a prohibition, not
   behaviour an invocation produces. Record it **not applicable**, with that reason, rather
   than forcing a verdict onto it.

**Population, refined.** Fifteen contracts; **C4 and C11** answered at m5 t2; **C13** not
applicable. **Twelve to answer** — verify that split against §Contracts at HEAD before
relying on it.

**Findings threshold, in force for this row.** A finding earns its own action only if it has
already cost something pointable — a session that derived it, a ruling that rested on it, a
check that passed for the wrong reason. **A gap argued from structure alone is recorded in
the notes and swept once at the end, not acted on.** A gap argued from structure is a
prediction; a gap with a session that paid for it is a finding.

`Anatomy authored 2026-08-11 by the reviewer, before the row is worked, per R12. Shape ruled
light by the human on the BL-084 / BL-085 / BL-096 precedent — row taken directly, one
implementation-notes file, no round document, no review file. Those three carried no anatomy at
all, so Touches and Done-check are new fields here rather than §6 fields relocated into the
light shape. This block attributes to this date and not to the row's Source line below.`

`Source: m4 t5b G2 gate-stop, 2026-08-07 — the finding that C4 ratified an m1 position decision H
had already superseded, and that no step between the census and the contract checked reachability.`

---

### BL-132 — DONE 2026-08-11 — the census ran over all fifteen; **both `Owes:` items discharged**

**The row's own `Owes:` is the checklist, and both are discharged.** *"The per-contract table"* —
in `cloudcost/docs/bl-132-implementation-notes.md` §2, fifteen rows, each with its verdict and what
the verdict rests on. *"A qualifying sentence in each contract found source-only"* — **nine**
landed in `cloudcost/milestone.md` §Contracts, one closing each of **C1, C2, C3, C6, C8, C9, C10,
C12** and **C14**, each tagged `Reachability (BL-132, 2026-08-11)` so the set is greppable from the
file rather than from a packet.

**The distribution.** Fifteen contracts. **Two** answered before this row ran and not re-derived —
**C4** and **C11**, source-only by **m5-D2**. **One** not applicable: **C13** states field
ownership and a keying prohibition, not behaviour an invocation produces, so it was recorded with
that reason rather than given a verdict forced onto it. **Twelve** answered here, and none of the
twelve was source-only *whole*: every one holds a guarantee the pipeline exercises beside a clause
describing something no invocation reaches. **Three** — **C5**, **C7**, **C15** — are reachable
entire and took no sentence.

**The population was derived, not inherited.** `grep -c '^### C[0-9]' cloudcost/milestone.md` → 15,
contiguous C1–C15, no gap and no duplicate, measured at `8845d85`. The anatomy's *twelve to answer*
is confirmed; it was checked rather than relied on, which the anatomy required.

**Method — the entry point was run, not read.** Both STEP 3 arg forms in
`cloudcost/agents/cloudcost_orchestrator.exs` were executed over recorded artifacts, with STEP 2
before and STEP 4 after, and contracts were checked against the payload and the rendered report.
**The result that could not have come from reading**: **C2**'s X1 clause says the ~fifteen raw
provider state strings *"reach the rendered report verbatim"* via evidence text — at HEAD both
interpolation sites are gated on `STOPPED_STATES`, so only the canonical value can, and the
composed payload carries no `state` field at all. Measured over three chains of the orchestrator's
own STEP 3 forms across recorded DO and Linode artifacts — DO at both arg forms and Linode at the
first: **zero** `"state"` across **all three composed payloads and all three rendered reports**,
against a control of **18** in the DO inventory those chains consumed.

> **`[corrected 2026-08-11 (the row-correction round). The measurement is stated over six artifacts
> and one named inventory, not two artifacts and an unnamed one — taken from the corrected sibling,
> not re-derived.]`**
>
> **It read:** *"Zero in either payload and either rendered report, against **18** in the inventory
> those runs consumed."*
>
> **Both clauses failed, and in opposite directions — which is why this is a replacement and not a
> narrowing.** *"Either"* is two; the exercise sweep at `8f36e45` re-measured all **six** artifacts
> of the three chains and every one is zero, so the row **understated** the population its result
> rests on. *"The inventory those runs consumed"* is the clause that is **over-broad**: those chains
> consumed **two** inventories with different counts — **18** DO and **15** Linode
> (`cloudcost/milestone.md` §C6's basis figures) — so one control attributed to *the* inventory
> conflates them, which is the same defect `8f36e45` corrected in C3 one file over. The replacement
> is the text `cloudcost/milestone.md:391–394` carries at HEAD, quoted rather than re-derived.
>
> **The verdict is unchanged**, and so is every other claim in this paragraph — the `STOPPED_STATES`
> gating, the absent `state` field, and the finding that this result could not have come from
> reading. Corrected here because `8f36e45` touched `cloudcost/milestone.md` **only**, leaving this
> row as the sibling that still carried the superseded wording — the gap **BL-140**'s `Source:`
> block names, below in this file. The second such site,
> `cloudcost/docs/bl-132-implementation-notes.md` §2's C2 basis cell, is corrected in the same
> commit as this and was **not** named in that note. The round's record is
> `cloudcost/docs/bl-132-row-correction-implementation-notes.md`.

**The three self-reporting contracts were treated as subject, not input**, per the anatomy's
method refinement 2 — **C3**'s unreachable wall-clock fallback, **C8**'s never-fired activity
modifier, **C12**'s own report that its guarantee does not hold. **All three hold under check**,
each established by a different instrument. Had one been false the ticket was to stop and relay;
none was.

**One finding, and it is filed rather than carried here: `BL-138`.** C8's D21 clause enumerates the
declared parameter block wrongly — it emits five keys, one of which the clause excludes. It was
**declined on scope**: this row's subject is reachability and D21's defect is accuracy, and D21's
operative claim — the block is write-only — is confirmed and unaffected. Filed as its own row
rather than left as prose, because prose owns nothing.

`Source: BL-132 filed 2026-08-07 from m4 t5b's G2 gate-stop; annotated 2026-08-09 and 2026-08-10
(m5 t2); anatomy authored into this row 2026-08-11 by the reviewer per R12; census run and closed
2026-08-11. Record: cloudcost/docs/bl-132-implementation-notes.md.`

---

### BL-133 — the loop's evidence is not retained, so no past run's greenness is checkable after the fact (#TBD)
**Kind:** method · **Census items:** n/a (surfaced by the m4 close) · **Contract:** n/a
**Size:** S to rule, S–M to implement · **Priority:** medium
**Section:** process / harness (`../aetheris/sprint/`, `docs/reviews/`)

Filed 2026-08-08 from the m4-cloudcost close. **One row with two faces, and the consequence is the
row.** Both faces were found independently at close-a — one by the ticket-closure gate, one by the
attempt to tally BL-075 — and they are the same defect about two artifacts.

**Face 1 — reviews are session artifacts.** A round's findings, and their dispositions, exist in
the review packet and nowhere else. `docs/reviews/` holds a handful of committed review files, but
no m4 ticket's rounds are among them. So *"the ticket closed with zero blocking findings"* is
derivable only as *"the row says Closed and a closure note exists"* — closure is showable, the
**absence of an open finding** is not.

**Face 2 — `sprint/` archives the run payload and not the verdicts.** Verified at the close over
this cycle's window:

```
$ ls -d sprint/2026080*/                          -> 26 run directories
$ ls -d sprint/2026080*/cloudcost                 -> 23 have a cloudcost dir
$ for d in sprint/2026080*/cloudcost; do ls $d; done | sort | uniq -c
     18 run.json                                  # and nothing else, ever
$ for d in sprint/2026080*/cloudcost; do [ -z "$(ls -A $d)" ] && echo $d; done | wc -l
      5                                           # empty cloudcost dirs
```

So **8 of 26** runs archived no cloudcost payload at all, and the 18 that did archived `run.json`
alone — **no arm count, no `[FAIL]`/`[WARN]` lines, no record of whether the capture was complete.**
The console output, which is where every assertion's verdict lives, is retained nowhere.
**`mix test` output is archived nowhere at all** — a `grep -rl "tests, .* failure" sprint/` returns
nothing.

**The consequence, which is what this row is for.** No past run's greenness is checkable after the
fact. Any clause asking for *zero blocking findings*, *three clean runs*, or *the sprint was green
at commit X* is **not assessable from the record** — only from a packet, and a packet is the thing
that does not outlive the session. §Close criteria's own head-1 clause hit this at close-a and
could be answered only partly, for exactly this reason.

**Distinguish this from the packet rule promoted at the same close.** *A packet's sprint section
shows the run's full output* (agents `CLAUDE.md` §Learning — BL-007) fixes **what the packet
carries**. It does not fix **what outlives the packet**, and the archive is the only thing that
does. Closing that rule does not close this row.

**Do not skip to a mechanism.** "Archive the console output beside `run.json`", "commit review
files per round", "have the sprint emit a machine-readable verdict summary" answer three different
rulings about what the record is *for* — an audit trail, a debugging aid, or a gate input — and
picking one before the ruling builds the wrong thing cheaply.

**Owes:** a ruling on what a run's durable record must contain, and then the mechanism.
**Costs:** S to rule. Implementation depends on the ruling; capturing the sprint's stdout into the
existing run directory is the cheap end.

> **`[FACE 2 DISCHARGED 2026-08-09 (hc-d). Face 1 is not this row's to close and stays open.]`**
> The ruling is **hc-consolidation R1**: the record is a **debugging aid with provenance** — (b)
> plus one element of (a) — explicitly *not* an audit trail (`sprint/` is gitignored, so one here
> is one machine's) and *not* a gate input (no consumer keys on a verdict document; the trigger for
> re-opening (c) is recorded on R1). The mechanism, landed with BL-077 as R1's coupling requires:
> `sprint/<ts>/console.log` carries every arm in order, untruncated, **streams merged** (R18(b));
> `sprint/<ts>/provenance.txt` carries both repos' commits with dirty flags, the target, the
> command, and the start time. **Retention is stated, bounded and enforced** — 30 days, swept at
> the start of every run, printed on each run, `SPRINT_RETENTION_DAYS` to override.
>
> **R18(a) was demonstrated, not argued.** The capture uses `exec > >(tee -a …) 2>&1`, which
> creates no pipeline, so the status the counter drives is untouched. hc-d's G3 measured the
> alternative directly on the same failing case: status `0` with and without a `tee`, with a
> positive control showing `tee` under `pipefail` does preserve a real non-zero (`1` both ways) —
> so the sameness is an observation about this command, not a `tee` swallowing everything.
>
> **Face 1 — reviews as session artifacts — is untouched and still open.**
**Collides with:** **BL-075**, which cannot be closed without it (annotated to say so);
**BL-077**, whose `expected_fail()`/`KNOWN_RED` counter would produce exactly the verdict summary
face 2 is missing, so the two should be looked at together.

`Source: m4-cloudcost close-a, 2026-08-08 — G2's method limit (face 1) and Part 5 (face 2).
Archive counts re-derived at the close against ../aetheris at e75f838, not inherited: close-a
reported "three hold no cloudcost artifact at all", and the re-run found 3 with no cloudcost dir
plus 5 more holding an empty one — 8 of 26.`

**Face 2 discharged 2026-08-09 (hc-d).** Every sprint run now retains its own console output
beside the run payload, under a stated and enforced retention bound, with a provenance stamp
naming both repos' commits, the target and the command — harness `2d76a65`→`48f59e7`. **The row
stays open**: face 1 (reviews as session artifacts) is untouched, and **R2** of the hc round ruled
it out of scope as a methodology obligation the round simply meets rather than a mechanism to
build. What face 2 does **not** cover is recorded at hc-e's opening edit E4 and on **BL-075**: the
durable place exists, but `mix test` output is still routed nowhere into it.

`Recorded 2026-08-09 by hc-e's §Close criteria clause 1 sweep, which found the discharge claimed
in docs/milestones/hc-consolidation.md §Ticket set and recorded on no row here. The work is hc-d's;
only the record was missing.`

---

### BL-134 — verify the seven comment-anchored census claims, and hand-classify the eight the sweep could not reach (#TBD)
**Kind:** verification · **Census items:** X3, D5, D9, D12, P3, P8, P10 (the seven); D13, D16, D21, F2, F3, R1, R2, R3 (the eight) · **Contract:** n/a
**Size:** S · **Priority:** low–medium
**Section:** cloudcost (`cloudcost/docs/m4-t4a-implementation-notes.md`)

Filed 2026-08-08 from the m4-cloudcost close. **A bounded verification task, not a rule** — which
is why it is a row: verifying seven claims and hand-classifying eight entries is work, and no
standing instruction falls out of it.

**Where it comes from.** The t4b defect was narrow and specific: *a comment that asserted its own
test coverage, taken as evidence that the test existed.* A comment is not a truth-maker for its own
claim. close-a sized how much of the t4a census could be exposed to that defect by resolving every
anchor in all **54** entries against the source at agents `2806305` and classifying each single-line
anchor by what that line actually is.

| | |
|---|---|
| census entries | **54** |
| classifiable (≥1 single-line anchor) | **46** |
| **citing a comment or docstring line** | **7** — X3, D5, D9, D12, P3, P8, P10 |
| citing only code lines | 39 |
| **unclassifiable** | **8** — D13, D16, D21, F2, F3, R1, R2, R3 (range-only or no line anchor) |

**What is and is not established.** A comment anchor is **not per se the defect** — the census's
convention is to quote a rule's rationale from its comment and its behaviour from its code, and
most of the seven cite both. **Whether any of the seven asserts its own test coverage is not
established**, because the method finds anchor *kind* and never whether a comment's claim was
independently checked. That check is this row.

**The work, stated so it is not mis-scoped.**

- For each of the **seven**, read the cited comment or docstring and ask one question: *does the
  census rest on this line for a claim the line only asserts about itself?* Where it does, verify
  the claim against the code or the test and correct the entry.
- For each of the **eight**, resolve the anchors by hand and classify them, so the population that
  the automated pass could not reach is closed rather than left at 15 %.

**A method artefact that is not a finding, recorded so nobody re-files it.** close-a's sweep also
reported eleven items whose anchor resolves outside its inherited file. That is almost certainly
the group-inheritance heuristic mis-attributing cross-file citations in `Consumers` fields — **not
eleven decayed citations.** Do not open this row expecting eleven; if the hand pass finds real
decay, that is a new finding and gets its own record.

**Owes:** a verdict per entry for the seven, a classification for the eight, and any corrections
those produce in the census.
**Costs:** S. Fifteen entries, one question each, all in one file.
**Collides with:** nothing. The census is closed (BL-074) and this does not reopen it — it checks a
property of the citations, not of the rulings.

`Source: m4-cloudcost close-a Part 3, 2026-08-08 — anchors resolved against agents 2806305. The
counts are the corrected pass's: close-a's first two passes reported 39 and then 37 unclassifiable,
both of which were its parser's limits rather than the census's, and both were discarded. close-a
itself read this as a row rather than a promotion candidate, and that read is adopted here.`

---

### BL-136 — decision H's consequent: a read-only cross-provider cost summary over the persisted per-provider snapshots (#TBD)
**Kind:** feature · **Census items:** n/a (surfaced by m5 t1's E7) · **Contract:** verify and record which of C1–C15 apply
**Size:** S–M · **Priority:** medium · **Section:** cloudcost

**What it is.** A read-only reader over the per-provider cost snapshots the pipeline
already persists, emitting one table — markdown or HTML — with a row per provider
per period. **It runs on artifacts, never on the pipeline:** it invokes no adapter,
no orchestrator and no compose, and it writes nothing into the history or output
trees.

**This is decision H's own consequent, and its precondition is already met.**
H (`cloudcost/m2-milestone.md` §H — *Per-provider reporting; no cross-provider
roll-up*) drops the merge-across-clouds while stating that consolidation is not
foreclosed, because each provider persists a normalized cost snapshot from which a
cross-provider total stays re-derivable by *"a thin read-only aggregator — a
separate optional read-layer, never coupled to the pipeline."* m5 t1's **E7**
(`cloudcost/docs/m5-t1-implementation-notes.md`) established **by execution** that
the layout H names is written on every orchestrator run, and that snapshots for
three providers exist on disk. **The aggregator is the only part of H that was
never built.**

**And it is independent of the N>1 compose surface.** **m5-D2** retains that surface
as a library-and-CLI capability the pipeline does not invoke. This row does not use
it: H's route is reading persisted artifacts after the fact, not merging bundles at
compose time. Either ruling on BL-131 would have left this row exactly where it is.
Stated because the two were assumed coupled until t1 separated them.

**The table.** One row per provider per period. Columns: provider, period,
currency, amount, and the run stamp each snapshot carries, plus whatever else the
snapshot supports. **Verify the field names against a snapshot and record them; do
not take them from this row.**

**Four requirements that are not obvious, each for a reason:**

- **Group or sort by period, and never sum across periods.** Two providers whose
  latest snapshots are different periods sit adjacent in any table sorted by
  provider, and a reader adds them. Whatever shape the output takes, a period
  mismatch is visible without arithmetic.
- **No currency conversion, and no grand total across currencies.** Conversion needs
  rates, rate dates and a source of truth for both, and it inherits C4's unresolved
  minor-unit exponent and currency-relative tolerance. Per-currency figures only.
  Where a period holds one currency across every provider in it, a subtotal is safe
  and is the one aggregation this row endorses.
- **Say when a declared total has no line items.** **BL-119** records that such a
  snapshot is silently dropped from discovery. A reader over the history tree does
  not drop it — so it must say so, or it reports an unbacked figure as though it
  were backed.
- **Every row names the artifact it came from.** The table is an input to a
  reconciliation nobody has scoped; a figure whose artifact cannot be found is not
  reconcilable.

**One thing it cannot do today, and this is the row's known limit.** m5 t1's **E7**
could not establish which run wrote a given snapshot: the history tree is
gitignored, the files carry a generation timestamp but no run identifier, and a
listing cannot bind a file to a command. **So the run column is a timestamp, not a
run reference.** Verify and record what the snapshots actually carry. If a later
consumer needs run provenance — and a bank reconciliation would — that is a change
to what the pipeline *writes*, which is a different row and not this one. This row
stays read-only.

**The destination, named and deliberately not scoped in.** The eventual use is
reconciling cloud spend against a bank statement, factoring conversion rate and bank
commission. That is not this row and nothing here is built for it. It is named
because it is why the two requirements above — artifact traceability, and no silent
conversion — are requirements rather than preferences.

**Owes:** the reader, its offline tests against fixture history trees, and a runbook
entry — it is operator-run, so the runbook rule applies to it.
**Costs:** S–M. One script, one output template, no pipeline coupling, no adapter
work, no change to anything the pipeline writes.
**Collides with:** **BL-119**'s subject, which this row surfaces rather than fixes.
Nothing else — it is additive and reads artifacts the pipeline already writes.

`Source: m5 t1 r0 §E7, 2026-08-10 — `cloudcost/docs/m5-t1-implementation-notes.md`,
which established H's precondition by execution and its consequent absent. Decision H
itself: `cloudcost/m2-milestone.md` §H — *Per-provider reporting; no cross-provider
roll-up (ratified 2026-07-30, rev 3)*. Filed at the human's direction at the **m5-D2**
ruling, where H's consequent was named as neither decided nor owned —
`cloudcost/m5-n1-compose.md` §Ratified decisions, m5-D2's *What this does not decide*.`

---

### BL-137 — a freshness census over `cloudcost/milestone.md` §Open items: items whose trigger has already fired, or whose framing predates adapters that have since shipped (#TBD)
**Kind:** method · **Census items:** n/a (surfaced by m5 t2 r1's second-claim sweep) · **Contract:** none — §Open items states no contract
**Size:** S–M · **Priority:** medium · **Section:** cloudcost (`cloudcost/milestone.md` §Open items carried forward)

**What it is.** §Open items is a carry-forward list, and a carry-forward list decays in a
way nothing currently watches: an item written while one adapter shipped can name a
condition that three adapters have since changed, or schedule itself against an event that
has already happened. The item still reads as true — its own sentence is unchanged — so
neither `drift_check` nor a review of the file's diff can see it. Only reading each item
against the repo as it now stands can.

**This is not the m5-D2 correction, and the distinction is the row's point.** m5 t2 and its
r1 corrected two §Open items claims that rested on the reachability premise **m5-D2**
overturned — the *"unreachable while DO is the only provider"* clause on the
new-provider-caveat and multi-currency paths, and the cross-currency aggregation item's
*"live at the first fan-out"*. **Neither of the two items this row names rests on that
premise.** They are stale for an unrelated reason, which is why correcting them was outside
t2's amended `Touches` and why they get a row instead of a third scoping amendment.

**Two reported instances — a starting population, not the census.** Both were found by the
sweep t2 r1 ran for a *different* premise and reported deliberately unfixed
(`cloudcost/docs/m5-t2-implementation-notes.md` §*W3(d) — Reported, not fixed — two, and the
reviewer's call*):

- **The recency-modifier item**, `cloudcost/milestone.md` §Open items carried forward —
  *"Bound the recency modifier's window at both ends"*. Its stale clause is *"Unreachable
  while DO is the only provider (the field is null), so it lands with the first adapter that
  populates it"*. AWS and Linode ship. **Whether either populates `last_activity_at` is not
  established** — that is an adapter read, and it is this row's work, not a wording fix.
- **The orphan-filename item**, same section — *"Give t2's output file a provider prefix
  before the first multi-provider run"*. Its stale clause is the schedule, *"Lands with the
  second adapter."*; the second adapter landed at m2 and the third at m3. **Lead, offered
  for the census to verify rather than as a finding:** `cloudcost/m2-milestone.md` §*m1 open
  items — final triage after A–H (LIVE / latent / RETIRED)* records a row *t2 output filename
  collision* as **CLOSED — t2 b**, *"Each provider writes
  `{provider}_orphan_candidates_{period}.json`"*, which if it holds at HEAD means the item's
  trigger fired **and** was discharged, and the item is a residue rather than an open
  question. Read `detect_orphans.py`, not the record — the record is the lead.

**Why the two are a starting population and not the census.** They were surfaced by a sweep
looking for something else, over the subset of the section that sweep happened to reach. The
section carries **eleven** top-level items — seven bold carried items and four plain
forward-looking bullets — and the census reads all eleven, including the four the sweep had
no reason to touch. `(Count derived at agents d36b8e9 by enumeration of "^- " within the
section; the enumeration, not just the count, belongs in the census's own record.)`

**Done-when.** Every one of the eleven items in §Open items is read against HEAD and marked one of: still
accurate; **trigger fired** (the condition it waits on has occurred — say what discharged it
and whether the item survives); **framing stale** (the sentence is true but its stated reason
is not — corrected in place with the superseded wording quoted, per decision 7); or
**discharged elsewhere** (another milestone closed it — cite where). The two above are
included, not assumed.

**Owes:** adapter reads for the recency-modifier item (`cloudcost/scripts/fetch_aws.py` and
`fetch_linode.py` — whether either populates `last_activity_at`, and `_normalized.py` for
whether the field survives normalisation) and a source read of `detect_orphans.py` for the
orphan-filename item; neither is a documentation-only change, which is exactly why this is a
row rather than a wording fix inside a ticket already scoped elsewhere.
**Costs:** S–M. No behaviour change and no contract amendment — establishment work over
eleven items, most of which will settle by reading.
**Collides with:** nothing. **BL-132** is the contract-reachability census over C1–C15 and
this is the open-items freshness census; they share a shape and no subject matter.

`Source: m5-cloudcost t2 r1, 2026-08-10 — the two instances and their shape are
`cloudcost/docs/m5-t2-implementation-notes.md` §W3(d), and the reviewer's disposition that
they get a row rather than a third `Touches` amendment is
`cloudcost/docs/m5-close-anatomy-implementation-notes.md` §Review → *The two staleness items
get a row, not a third `Touches` amendment*. Filed at the m5 close (t3), 2026-08-10, as the
one row `cloudcost/m5-n1-compose.md` §t3 → `Touches` provides for. Read at agents `d36b8e9`.`

---

### BL-138 — C8's D21 clause enumerates the declared parameter block wrongly (#TBD)
**Kind:** accuracy · **Census items:** D21 · **Contract:** C8 (`cloudcost/milestone.md` §Contracts)
**Size:** XS · **Priority:** low · **Section:** cloudcost (`cloudcost/milestone.md`)

Filed 2026-08-11 by **BL-132**, which found it and declined it on scope.

**The claim, quoted.** C8's D21 paragraph opens: *"**The declared parameter block covers the age
thresholds and the coverage threshold, and nothing else** (D21). The six confidences, the two
modifier deltas, the keep-tag spelling, the ephemeral pattern and the band cutoffs are **not**
echoed, so a report cannot state the full parameterization it was produced under."*

**What the block actually emits — five keys**, read from a `detect_orphans.py` run over a recorded
inventory:

```
snapshot_age_days
unattached_volume_min_age_days
stopped_compute_min_age_days
tagged_account_coverage_threshold
recent_activity_window_days
```

**The omission is the fifth.** Three age thresholds and the coverage threshold are the four the
clause names; **`recent_activity_window_days` is neither** — it is `modifier_recent_activity`'s
fourteen-day window, and C8's own next sentence lists *"the two modifier deltas"* among what is
**not** echoed. The deltas indeed are not; this modifier's *window* is. So *"and nothing else"* is
false, and it is false in the direction that matters: the block is **less** incomplete than the
contract says, and a reader deciding what a report can state about its own parameterization is
told the modifier surface is absent from it when one member is present.

**This is an enumeration defect, not a behaviour defect.** **D21's operative claim is confirmed and
unaffected**: the block is **write-only** — no consumer reads it, not the compose stage, not the
renderer, not the template, not the sprint, verified at BL-132's census. Nothing about what the
pipeline *does* is in question, and no code is wrong. What is wrong is a canonical document's
statement of what one of its own artifacts contains.

**Why it is filed rather than fixed at BL-132.** That row's subject is **reachability** — whether a
contract states behaviour an invocation produces — and this is **accuracy**: the clause is about
content, and correcting it needs no reachability finding. BL-132's findings threshold routes a gap
argued from structure to its notes; this is neither a gap nor a prediction but an error of fact, so
it gets an executor rather than a sweep. Prose in a notes file owns nothing.

**Done when:** C8's D21 clause names the five emitted keys, or names the four and says the fifth
explicitly; and the *"and nothing else"* claim is either true as written or replaced.

**Costs: XS, and sized from the work rather than by analogy to a neighbouring row.** Two reads —
the emitting site in `detect_orphans.py` and the D21 paragraph — and one sentence rewritten. **No
adapter work**, since no adapter supplies any of these values. **No execution required**: the key
set is a literal at the emitting site and can be read there; the run BL-132 used is a convenience,
not a dependency. The one judgement it carries is whether the clause should enumerate at all or
state the rule that generates the set, and that is a wording call inside one paragraph.

**Collides with:** nothing. It touches one paragraph of C8 and no other contract. BL-132 is closed
and does not need reopening — its census verdict for C8 stands unchanged, and C8's landed
reachability sentence already points at the record this row supersedes.

`Source: BL-132's census, 2026-08-11 — found while confirming D21's write-only status, which holds;
recorded at cloudcost/docs/bl-132-implementation-notes.md §5 and declined there on scope.`

---

### BL-139 — record the conditions under which a triad exchange may be looped without a human turn (#TBD)
**Kind:** method · **Census items:** n/a · **Contract:** n/a
**Size:** S to rule · **Priority:** low
**Section:** process / methodology (`docs/triad-loop.md` and its canonical harness copy
`../aetheris/docs/methodology/triad-loop.md`)

Filed 2026-08-11 at the m5 session close. **The item as agreed and parked, verbatim:**

Record the conditions under which a triad exchange may be looped without a human turn, and the
conditions under which it may not. The formulation reached in discussion and not yet tested
against a document: verification loops, authority relays. Status: the loop itself is on hold by
user decision; this row holds the criterion, not a build.

**Done when:** the two conditions are written into whichever of the triad documents the ruling
names, or the row is closed with a recorded decision that no criterion is to be stated.

**Costs:** S to rule. No build is authorised by this row and none is implied by it — the hold is
part of the item, not a blocker on it.

**Collides with:** nothing. It states a criterion; **BL-140**, **BL-141** and **BL-142** are the
three other methodology items parked at the same close, and no two of the four touch the same
sentence.

`Source: agreed in reviewer/user discussion after m5-cloudcost's close (2026-08-10) and existing
in no file until this row. Filed at the m5 session close, 2026-08-11, at agents 8f36e45. Checked
before filing: no "verification loop" or "authority relay" instance exists in either repo, and
docs/triad-loop.md describes the loop with a human turn at every phase boundary and states no
criterion for omitting one — so this row is opening the question, not restating a document.`

---

### BL-140 — whether a correction owes a same-commit sweep for recurrences as a standing obligation (#TBD)
**Kind:** method · **Census items:** n/a · **Contract:** n/a
**Size:** S to rule · **Priority:** medium
**Section:** process / methodology (`../aetheris/docs/methodology/milestone-methodology.md`;
the standing rule it would generalise is in this repo's `CLAUDE.md` §Learning — BL-007)

Filed 2026-08-11 at the m5 session close. **The item as agreed and parked, verbatim:**

A correction to a claim landed by a prior session currently sweeps for recurrences only when the
ticket says so. Determine whether the sweep should be a standing obligation on every correction,
and if so where it is stated. Anchor: the m5 BL-132 close, where a literal-string sweep and a
class sweep gave different answers — verify that episode against its committed record before
relying on it.

**Done when:** the obligation is either stated in one named document with its scope (every
correction, or a named subset) or declined with the reason recorded, and the existing
`CLAUDE.md` correction-chasing entry is reconciled with whichever answer lands.

**Costs:** S to rule. A ruling plus one edit in one document; the evidence is already committed
and is named in the `Source:` below.

**Collides with:** nothing directly. It **generalises** an existing standing rule — agents
`CLAUDE.md` §Learning — BL-007, *"A correction chases the corrected claim into every doc that
adopted it, in the same round"* — so whoever takes it reconciles with that entry rather than
adding a second copy of it.

`Source: agreed in reviewer/user discussion after m5-cloudcost's close (2026-08-10) and existing
in no file until this row. Filed at the m5 session close, 2026-08-11, at agents 8f36e45. The
anchor was verified before filing and holds, in a sharper form than the parked text states: the
episode's committed record is the commit message of 8f36e45, which reads "The earlier sweep
covered a literal string, not a class: grep for 'every detect pass' over cloudcost/ and docs/. It
found C8 only because C8 shared the wording, not because the class was searched." The class sweep
that followed found four of the nine landed sentences overstated and five accurate. Note for
whoever takes this row: that commit touched cloudcost/milestone.md only, so the sweep has no
implementation-notes record, and BL-132's own row above still carries the C2 wording that sweep
corrected one file over.`

---

### BL-141 — a Done-check that cannot fail, and whether a positional claim must carry path:line (#TBD)
**Kind:** method · **Census items:** n/a · **Contract:** n/a
**Size:** S–M to rule (two questions, one document) · **Priority:** medium
**Section:** process / methodology (`../aetheris/docs/methodology/milestone-methodology.md` §6)

Filed 2026-08-11 at the m5 session close. **The item as agreed and parked, verbatim:**

Two candidate methodology changes discussed together. (a) A Done-check that structurally cannot
fail costs a session and proves nothing; decide whether §6 should bar them and how such a check
is recognised. (b) Whether a positional claim must carry path:line as a standing requirement
rather than per-ticket. Anchor: m5-D1 in cloudcost/m5-n1-compose.md §Ratified decisions — read it
and report whether it already settles (b), before treating (b) as open.

**Done when:** (a) §6 either carries a bar with a stated recognition test or records the decision
not to add one; and (b) is either settled by reference to **m5-D1** with the reference written
down, or ruled on separately.

**Costs:** S–M to rule. (a) is the larger half: barring a check is easy to write and hard to make
recognisable, and the recognition test is the deliverable.

**Collides with:** nothing structurally, but (a) sits directly on two already-promoted standing
rules and must not become a third copy — `CLAUDE.md` §Learning — m7-docbuilder (*"A done-check
that can pass without exercising the thing it checks is worse than no check"*) and
`../aetheris/CLAUDE.md` (*"A check that cannot observe the failure it stands in for returns green
for the wrong reason"*). What is unsettled is whether **§6** should bar such a check, which
neither rule does.

`Source: agreed in reviewer/user discussion after m5-cloudcost's close (2026-08-10) and existing
in no file until this row. Filed at the m5 session close, 2026-08-11, at agents 8f36e45. The
anchor was read before filing, and m5-D1 does not settle (b) as posed: it rules the converse —
"a line number is only for a claim about a line" — and for a positional claim it requires a
commit stamp, not a path:line; and its scope is stated as "Binds t1 and t2", not the methodology
at large. So (b) survives, narrowed to whether the stamped-positional form m5-D1 already defines
should become standing.`

---

### BL-142 — whether §6 should require `Touches` to be derived from a search for the premise (#TBD)
**Kind:** method · **Census items:** n/a · **Contract:** n/a
**Size:** S to rule · **Priority:** medium
**Section:** process / methodology (`../aetheris/docs/methodology/milestone-methodology.md` §6,
the `Touches` field)

Filed 2026-08-11 at the m5 session close. **The item as agreed and parked, verbatim:**

A ticket's Touches field has more than once named a subset of the sections carrying the premise
being changed, so the gap was found mid-ticket rather than at authoring. Determine whether §6
should require Touches to be derived from a search for the premise rather than enumerated by the
author. Anchor: verify the m5 t2 episode against docs/reviews/m5-cloudcost-t2-review.md and the
t2 implementation-notes file before relying on it.

**Done when:** §6's `Touches` field either states the derivation requirement with the search it
implies, or records the decision that enumeration stays the author's and why.

**Costs:** S to rule. One field's wording; the cost that matters is on the authoring side
afterwards, which is what the ruling is weighing.

**Collides with:** nothing. It changes how a field is authored, not what any ticket may edit, and
it leaves untouched the rule the same round upheld — that a ticket's scoping is authoritative
over a ticket's judgement.

`Source: agreed in reviewer/user discussion after m5-cloudcost's close (2026-08-10) and existing
in no file until this row. Filed at the m5 session close, 2026-08-11, at agents 8f36e45. The
anchor was verified before filing and holds: cloudcost/docs/m5-t2-implementation-notes.md §W1
quotes the amended field's own stamp — "The field as authored named §Contracts only and missed a
third site in the same file carrying the same premise — the reviewer's scoping gap, not the
ticket's" — and docs/reviews/m5-cloudcost-t2-review.md carries the same at its F1. One
qualification for whoever takes this row: the parked text's "more than once" is true of rounds,
not of tickets. Both amendments are m5 t2's (the BL-136 addition at the reviewer edit, §Open
items at r1), and a third was declined into BL-137.`

---

### BL-143 — the `project_knowledge` export boundary has no owner and no schedule (#TBD)
**Kind:** decision · **Census items:** n/a · **Contract:** n/a
**Size:** S to decide · **Priority:** medium
**Section:** process / project knowledge (`docs/project-knowledge-manifest.md`,
`prompts/bl-002-refresh-project-knowledge.md`)

Filed 2026-08-11 at the obligation-landing edit. **This row is the reviewer taking the decision
m5 t3's G2 reserved** — posing it, not settling it.

**The exemption is not in question.** `project_knowledge` manifest-staleness WARNs are exempt
under `--strict`, and the reasoning is stated consistently in four places
(`scripts/drift_check.py:24–30` and `:78–80`, `CLAUDE.md` §Definition of done, and BL-009
itself): mid-cycle manifest staleness is expected truth between export boundaries, and the export
boundary is the enforcement point. Nothing here reopens that.

**What is in question is the enforcement point.** It has no owner and no schedule. Its trigger is
an event rather than a schedule — `docs/project-knowledge-manifest.md:13`, *"Refresh trigger:
milestone end, or before any handoff session"* — and **the event has fired**: m5-cloudcost closed
2026-08-10. Nothing in either repo will notice that it fired. So the exempt class, which the
exemption itself describes as *mid-cycle* staleness, has become the steady state: four WARNs
carried by every run, with nothing that will clear them and nothing that would tell the difference
between a boundary not yet reached and a boundary indefinitely missed. That is the same
alarm-fatigue shape BL-009 was filed to prevent, arriving through the exemption instead of
through the count.

**Determine who owns the refresh and by what trigger it is guaranteed to run** — or record the
decision that a permanently-occupied exemption is accepted, with the reason.

**Done when:** either the refresh has a named owner and a trigger with a mechanism behind it
(something that fires without a human remembering), or the permanent occupancy is accepted in
writing with its reason recorded **where `drift_check`'s output sends a reader**.

**Costs:** S to decide. The acceptance branch is one paragraph in the place the WARN already
points at. The owner branch is larger only if it implies building something: the upload half is
human-owned by design (`prompts/bl-002-refresh-project-knowledge.md:11–13`) and no generator
script exists in either repo, so a mechanism can guarantee the *reminder* and never the act —
which is itself part of what the ruling has to say.

**Collides with:** nothing. It does not reopen BL-002 or BL-009 and does not question the
exemption's rationale, which four documents state consistently.

`[Ruled 2026-08-16 by the arbiter, at the export boundary of the same date, on the
condition the 2026-08-12 deviation block set and the 2026-08-14 boundary replaced:
rule which of check 1 and check 3 governs, and give this manifest vocabulary for a
document that is in the store and out of the export set.

CHECK 1 AND CHECK 3 BOTH GOVERN. THEY WERE NEVER IN CONFLICT. They were written
without a namespace boundary, and read without one they appear to contradict on
the documents that actually exist. Check 1 — set equality between the store and
the export-name column, in both directions — governs the MANIFEST NAMESPACE, which
is every store path not under `claude/`. Check 3 governs `claude/`. A
`claude/`-namespaced document is neither a check-1 finding nor a check-3
exception: it is out of the export set BY CONSTRUCTION.

THE VOCABULARY THIS MANIFEST SAYS IT LACKS IS THE NAMESPACE. A document that is in
the store and out of the export set is a `claude/`-namespaced document. That is
the word, and it already existed; what was missing was any statement that it
carried this meaning.

CONSEQUENTLY, REMOVE-ALL-UPLOAD-ALL IS REHABILITATED, SCOPED. `CLAUDE.md`'s
standing rule is correct once *remove-all* is read as *all of the manifest set*
rather than *everything in the store*. Scoped that way the procedure destroys
nothing the record cannot name, and it buys precisely the guarantee check 1 was
for: no hash-driven shortcut, every tracked document replaced wholesale.

THE TWO DEVIATION BLOCKS WERE RIGHT FOR THE REASON THEY GAVE. The remove half, as
they read it, would have deleted documents this manifest could not describe. Their
reason simply had a narrower scope than either could establish — and neither could
have established it, because the census that settles it can only be taken from the
store, and no session that writes this manifest can see the store. Their condition
is DISCHARGED, not defeated. They are point-in-time records and are not amended.

PERFORMED, NOT ASSERTED. At this boundary all twenty-five manifest documents were
rewritten wholesale rather than as a diff of the two movers; the five
`claude/`-namespaced documents were not touched. Check 1 was run as set equality
in both directions, parsed from the table bound to its header, with a control
proving it detects a dropped row. Check 2 was run on both movers as a BYTE
comparison — stronger than the procedure specifies, which asks for a read rather
than a diff. Check 3 was run as an enumeration of the five.

WHAT THIS RULING DOES NOT CLAIM. It says nothing about what the U2 sweep
establishes; that claim stays as narrow as BL-160 records it. Check 2 was
performed on the two movers, which is its own definition — the other twenty-three
documents were written from the same bundle in the same pass and were not
individually verified. And it does not reach who owns the boundary or on what
trigger.

WHAT FOLLOWS AND IS NOT DONE HERE. `prompts/bl-002-refresh-project-knowledge.md`
§Post-upload verification still states check 1 and check 3 without the namespace
boundary. Rewriting them is now unblocked and is deliberately not done in this
commit: the ruling and the procedure it governs are separate landings, and a
procedure edited in the same commit as the ruling that authorises it cannot be
reviewed against it.]`

`[Scope note, 2026-08-16 — this records scope and adds none. Two questions were routed to this row
by documents outside it: the check-1/check-3 contradiction and the vocabulary gap, ruled in the
annotation above, and a deferred sprint arm, filed as **BL-161**. Neither appears anywhere in this
row's own text. This row's Done-when — ownership and trigger — is **unchanged and open**, and
nothing above or below narrows it. The finding about the routing itself is **BL-162**; the
prompt-file rewrite the ruling above defers is **BL-163**, which is that deferral's executor and
deliberately does not widen this row.]`

`Source: filed by the reviewer at the obligation-landing edit, 2026-08-11, at agents 0587bf3,
with each of the four claims below verified before it was written. **The trigger has fired, and
what fired it:** docs/project-knowledge-manifest.md:13 states the trigger as "milestone end, or
before any handoff session"; m5-cloudcost's close is written into cloudcost/m5-n1-compose.md
§Milestone summary, authored at t3 on 2026-08-10 per §Close criteria clause 6 — so the
milestone-end arm fired there. **m5 t3's G2 reported this read-only and reserved the decision:**
cloudcost/docs/m5-t3-implementation-notes.md §G2 (:727–731 at 0587bf3) — "No manifest was
refreshed, no row was filed, and no file was edited for this question — the instruction reserves
that decision to the reviewer." **The reserved decision appears in no review file:**
docs/reviews/m5-cloudcost-t2-review.md and docs/reviews/m5-cloudcost-t3-review.md each return 0
for a case-insensitive sweep of manifest|G2|project_knowledge|export boundary; the control is
that the same term over docs/reviews/ returns 35 files, so the two zeros are absence and not a
broken search. **Nothing schedules a refresh:** the agents repo has no .github directory at all;
the harness's only workflow, ../aetheris/.github/workflows/ci.yml, triggers on workflow_dispatch
and pull_request with no schedule: key and no manifest or drift_check step; no cron/scheduled hit
in either repo concerns export (they concern the harness's scheduled_runs table); and sprint.sh
runs drift_check but no refresh. BL-002 and BL-009 are both "Done 2026-07-15"
(docs/backlog-2026-06.md:218 and :4197), so no open row owns it. The prior read of the same
ground, reported without filing, is cloudcost/docs/bl-132-row-correction-implementation-notes.md
§2d.`

---

### BL-144 — a round whose output is a derivation may leave it only in a scratch directory (#TBD)
**Kind:** decision · **Census items:** n/a · **Contract:** n/a
**Size:** S to decide · **Priority:** medium
**Section:** process / round records (`docs/milestones/hc-consolidation.md`,
`docs/measurements/2026-08-11-notes-readership/`)

Filed 2026-08-11 at the rescue edit. **This row poses the obligation; it does not settle it.**

**What happened.** The notes-readership measurement round produced a report and eleven derivation
scripts, and wrote them only to its session scratch directory under `/tmp/claude-1000/`. It
committed nothing, by instruction. One round later a promotion candidate was landed that rests on
that report's figures — `cloudcost/m5-n1-compose.md:1188` — and at the moment it landed, **the
evidence it rests on was in neither repo**. The artifact was found and preserved a round after
that, at `docs/measurements/2026-08-11-notes-readership/`, **by chance rather than by rule**: the
rescue happened because a reviewer thought to look, and nothing in either repo would have noticed
its absence or its loss.

**Why the existing rules do not cover it.** A round's obligations are written for rounds whose
output is a *document*: R20 says a reviewer-directed edit gets no review file and its
implementation-notes file is its record, and the readership candidate itself says a record should
carry the findings and **point at the commit for the derivation**
(`cloudcost/m5-n1-compose.md:1202`). **That rule assumes a commit exists to point at**, and this
case is the counter-example — the derivation had no commit, so the pointer had nowhere to land and
the candidate's own precondition was unmet at the moment it was written. A round instructed to
produce no record is currently also, silently, a round that preserves no evidence.

**Determine what a round owes when its output is a derivation rather than a document** — whether
the artifact must be committed, whether the script must be, and where. The scripts are the larger
half of the question: a measurement whose script survives is re-runnable, and re-runnability is
most of a measurement's future value, but the eleven preserved here hardcode absolute scratch and
repo paths and so are re-runnable only after repointing — which suggests any obligation on scripts
has to say something about their portability, not only their existence.

**Done when:** the obligation is stated in one named document with its scope — which artifacts,
whose responsibility, and where they land — or declined with the reason recorded.

**Costs:** S to decide. `docs/measurements/` was created by this round's rescue as a proposal, not
a convention; no precedent for a preserved measurement existed in either repo, the nearest
analogue being the capability matrix (derived doc at `docs/capability-matrix.md`, generator at
`scripts/assemble_matrix.py`, intermediates gitignored at `.gitignore:10`). Ratifying or replacing
that location is part of the decision.

**Collides with:** nothing. It does not reopen the readership candidate; it supplies the
precondition that candidate assumes.

`Source: filed by the reviewer at the rescue edit, 2026-08-11, at agents a5381ee, with each claim
below verified before it was written. **The producing round was instructed to produce no record
and no row:** its report's own opening line states it — "**Read-only round.** No edits, no commit,
no row, no notes file for this round." (docs/measurements/2026-08-11-notes-readership/report.md,
first line of the preserved body). The instruction is the reviewer's: that round and the two
after it were reviewer-directed prompts, and the round after it was told "Do not amend the
measurement round's report — it was read-only by design and stays that way." What is verified is
that the round was so instructed and that the instruction came through the reviewer-directed
prompt channel; no separate authorship record was sought. **The report was found**, not lost, at
/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/
scratchpad/notes-readership-measurement.md — 17,895 bytes, mtime 2026-08-11 13:45:25 +0530, md5
f90de0d50d0300d55470773c5f3fb26d — together with all eleven derivation scripts; the preserved
copies are byte-identical, checked and published at the rescue edit. **The candidate that rests on
it is landed** at cloudcost/m5-n1-compose.md §Milestone summary → §Open for the next cycle, the
entry at :1188, appended at agents a5381ee. Note that /tmp on this machine is ext4 on the root
device, not a tmpfs, so the loss risk was reboot- and cleaner-driven rather than memory-driven —
the urgency was real but its stated mechanism was not.`

---

### BL-145 — the backlog has two status surfaces and says so nowhere (#TBD)
**Kind:** defect · **Census items:** n/a (surfaced by gc t1's row census) · **Contract:** none — the file states no status convention
**Size:** S to decide, M to fix · **Priority:** medium
**Section:** process / backlog hygiene (`docs/backlog-2026-06.md`)

Filed 2026-08-12 at gc t3. **This row poses the question; it does not settle it.**

**What happened.** gc t1 needed every row's status to cross-join against gate claims, and derived it
programmatically. It found **two** surfaces that carry status and **they disagree in both
directions**. Row bodies carry `DONE`/`CLOSED`/`Closed <date>` markers for **33** rows. The
`## Suggested order` table at `:5662` carries ✔ marks for **28**. The union is **48**, and neither
surface alone is right: **20** rows are closed in their body and not ticked in the table
(BL-069, BL-070, BL-073, BL-074, BL-083, BL-090, BL-092, BL-095, BL-096, BL-099, BL-100, BL-101,
BL-104, BL-105, BL-106, BL-107, BL-121, BL-127, BL-131, BL-132), and **15** are ticked with no
closure marker in the body (BL-001, BL-002, BL-003, BL-004, BL-005, BL-009, BL-015, BL-028, BL-029,
BL-031, BL-038, BL-039, BL-050, BL-055, BL-056). Every one of the 20 the table misses closed on or
after 2026-08-04; the table has not been maintained since 2026-07-26.

**Why the existing rules do not cover it.** Nothing in the file says there are two surfaces, so a
reader consulting either alone gets a confident wrong answer about a different 20 or 15 rows — and
the wrongness is invisible from inside whichever surface was consulted. `drift_check` has no check
over this file. The nearest analogous rule, *A document that quotes repo state is a snapshot with no
invalidation* (`aetheris/CLAUDE.md`), binds a reader who suspects staleness; here there is nothing to
prompt the suspicion, because both surfaces read as authoritative.

**Determine what the backlog's status convention is** — one surface or two, which is authoritative,
and whether the second is a view that must be regenerated or a duplicate that should be retired.
The `## Suggested order` table carries a second thing the row bodies do not: a sequencing opinion.
Whether that survives a de-duplication is part of the question and not assumed here.

**RULED 2026-08-12 by the arbiter, at the gc t3 review. The question this row posed is answered;
the execution is not done, and this row owns it.**

**The row bodies are authoritative. The `## Suggested order` ✔ table is retired.** The ruling is on
the ground the row states: the table has not been maintained since 2026-07-26 and misses every one
of the 20 rows that closed on or after 2026-08-04, while the bodies are written by the session that
changes a row's state and are therefore current by construction. Two surfaces where one is
maintained is not a redundancy, it is a trap.

**What the ruling does not decide**, and what this row must therefore still establish: the table
carries a **sequencing opinion** the bodies do not — an ordering of what to do next — and retiring
the table drops it unless it is reconstructed somewhere. Whether that opinion is worth preserving,
and where, is execution and belongs here.

**Done when:** the `## Suggested order` table is either **retired** or **reconstructed from the row
bodies** as a derived view that cannot drift; the file **states in its own text which surface
answers the question**, so a reader is not left to infer it; and, if the table is retired, its
sequencing opinion is either carried somewhere named or dropped with the reason recorded.

**Costs:** M. The ruling removes the decision cost; what remains is 28 ✔ rows to reconcile against
48 closures, and one judgement about the sequencing opinion.

`Source: gc t1's row census, 2026-08-11 — 143 rows, extraction and both controls published at
docs/milestones/gc-t1-implementation-notes.md §A and §H. The two figures and the two disagreement
sets above are derived, not counted by eye. Filed gc t3, 2026-08-12, per D4. Ruled by the arbiter
2026-08-12 at the gc t3 review; the ruling is recorded here rather than in the round document
because it is a fact about this file, and the round that surfaced it does not own it.`

---

### BL-146 — a row's status marker can be a quotation of a different row's disposition (#TBD)
**Kind:** defect · **Census items:** n/a (surfaced by gc t1's row census) · **Contract:** none
**Size:** S · **Priority:** low–medium
**Section:** process / backlog hygiene (`docs/backlog-2026-06.md`)

Filed 2026-08-12 at gc t3. **This row poses the question; it does not settle it.**

**What happened.** gc t1's status extraction classified **BL-137** as closed. It is not. The marker
it matched is at `:8155`, and it is a **quotation of a row in `cloudcost/m2-milestone.md`** — BL-137's
body quotes that row's disposition, in the same bold-marker form a row uses for its own status, as a
lead for BL-137's own census. BL-137 was filed 2026-08-10 and is open. The extraction was corrected
by hand and the exclusion recorded; the point of this row is that **the correction was a human
judgement, not something the file's structure made available**.

*(The offending marker is described above rather than reproduced. Quoting it literally — as the
first draft of this row did — made **this** row trip the same extraction, which the done-check
caught. That is the hazard demonstrating itself, and it is recorded here rather than left armed: a
row that reads as closed to any marker-keyed reader is not a row that stays open.)*

**Why the existing rules do not cover it.** Any status extraction keyed on bold markers inside a row
body will read a quoted marker as the row's own. There is no syntactic difference between a row
saying it is closed and a row quoting something else that is closed. The same trap caught a second
row from the other direction — **BL-014**, whose body carries no status at all and which a
span-bounding defect briefly credited with a marker from a table about other rows.

**Determine whether row status should be structurally distinguishable from quoted text** — a
dedicated field, a fixed position, or a rule that quoted dispositions are fenced. Any answer must
survive the file's actual practice, in which rows quote other rows' dispositions routinely and
usefully; the goal is not to stop that.

**Done when:** either a structural convention is stated and the existing rows conform to it, or the
hazard is recorded as accepted with the reason, so a later extraction author is warned rather than
surprised.

**Costs:** S. The population is small — one confirmed false positive across 143 rows — but the cost
of the failure is a wrong closed/open answer that reads as confident.

`Source: gc t1's row census, 2026-08-11; the BL-137 false positive and the BL-014 span defect are
recorded at docs/milestones/gc-t1-implementation-notes.md §I. Filed gc t3, 2026-08-12, per D4.`

---

### BL-147 — the absence of a reachability stamp encodes three different dispositions (#TBD)
**Kind:** defect · **Census items:** BL-132's census over C1–C15 · **Contract:** `cloudcost/milestone.md` §Contracts
**Size:** S · **Priority:** medium
**Section:** cloudcost (`cloudcost/milestone.md` §Contracts)

Filed 2026-08-12 at gc t3, per **D5**. **This row poses the question; it does not settle it.**

**What happened.** BL-132's census ran over all fifteen contracts and landed **nine** reachability
stamps — C1, C2, C3, C6, C8, C9, C10, C12, C14. Six carry none: **C4, C5, C7, C11, C13, C15**. The
silence is not one thing. It encodes **three** dispositions, each recorded in the census's notes
file and none of them in the contract: *answered elsewhere and deliberately not re-derived* (C4,
C11 — m5 t2's ruling); *not applicable* (C13 — *"states field ownership and a keying prohibition,
not behaviour an invocation produces"*); and *reachable, whole, nothing to qualify* (C5, C7, C15).

**Why the existing rules do not cover it.** A reader of `cloudcost/milestone.md` alone sees the same
absence in all six cases and cannot tell which. Two of the three verdicts exist **only** in
`cloudcost/docs/bl-132-implementation-notes.md` — and §Carried in item 2 of the `gc` round carries
m5's measurement that an implementation-notes file is read by the next round in its arc or by
nobody, so a verdict parked there is a verdict with no reader. The census recorded its stamp-placement
rule deliberately (*"None landed in C4, C11 … C13 … or C5, C7, C15"*), so this is a documented
choice and not an oversight; the question is whether the choice survives contact with a reader who
has only the contract.

**Determine whether a contract should carry its reachability verdict even when the verdict is
"nothing to qualify"** — and if so, in what form, given that the census deliberately declined to
edit C4 and C11 and ruled C13 out of scope entirely.

**Done when:** either every contract carries a legible disposition, or the three-way silence is
stated once in §Contracts' preamble so a reader can decode it without the notes file.

**Costs:** S. Six short additions or one preamble sentence. It is a contract-file edit and the `gc`
round has no contracts ticket, which is why it is deferred rather than taken.

`Source: gc t1 addendum A, 2026-08-11 — the nine stamps enumerated by grep and the six absences
verified at HEAD, against cloudcost/docs/bl-132-implementation-notes.md §2 for the per-contract
dispositions. Ruled deferred at gc D5. Filed gc t3, 2026-08-12.`

---

### BL-148 — C7 and C13 state adapter obligations with no exemplar and no verdict in the contract (#TBD)
**Kind:** defect · **Census items:** D15, D16 (C7); X2, D19 (C13) · **Contract:** `cloudcost/milestone.md` §Contracts C7, C13
**Size:** S–M · **Priority:** medium — before provider four
**Section:** cloudcost (`cloudcost/milestone.md` §Contracts)

Filed 2026-08-12 at gc t3. **This row poses the question; it does not settle it.**

**What happened.** Both contracts bind a new adapter and neither shows it what compliance looks
like. **C7** requires an adapter to *"guarantee one attachment only, and **must declare its reduction
rule** — first, or most significant — where the provider permits several"*, and states in the same
breath that *"the adapters differ today in how they reduce; the reduction is currently an accident
of each implementation rather than a stated obligation"* — so the obligation exists and **no adapter
demonstrates it**. C7 also carries the `attached_to == "tag:<name>"` grammar, which *"originates in
one adapter's normalizer, is emitted by no other adapter, is enforced by nothing and asserted by no
test"*. **C13** requires an adapter to *"reduce its own richer structure into the single value the
schema carries"* and to flatten a region hierarchy, with no worked case. Neither contract carries a
reachability stamp (see **BL-147**), so a reader gets the obligation with neither an exemplar nor a
verdict.

**Why the existing rules do not cover it.** C1 has an exemplar and says so — Linode's image →
`TYPE_SNAPSHOT` mapping is recorded there as *"the shape to copy"*. C14 makes its obligation testable
by requiring each adapter to *"assert it in its own tests"*. C7 and C13 do neither, and the gap is
invisible from inside them: an obligation stated clearly still reads as complete. A fourth adapter's
author meets C7 first, at the point of deciding what `attached_to` carries.

**Determine what a contract owes an adapter author beyond the obligation itself** — an exemplar, a
test hook in the C14 shape, or an explicit statement that none exists yet — and whether C7's
tag-targeting grammar should be asserted by a test before a fourth adapter can break it silently.

**Done when:** C7 and C13 either carry an exemplar or state that they do not and why; and C7's
tag-grammar obligation has a stated enforcement position, even if that position is "none, by
decision".

**Costs:** S–M. Wording is small; deciding whether the tag grammar earns a test is the substance.
Sequenced **before provider four** — this is the obligation a fourth adapter meets earliest.

`Source: gc t1 addendum B, 2026-08-11 — C7 and C13 confirmed at HEAD to carry adapter obligations,
no reachability stamp and no m5-D2 paragraph, with the two Source-only-by-ruling paragraphs verified
to exist only at cloudcost/milestone.md:488 (C4) and :816 (C11). Filed gc t3, 2026-08-12, per D4.`

---

### BL-149 — two live documents use "live" in incompatible senses (#TBD)
**Kind:** decision · **Census items:** n/a (surfaced by gc t1's census, ruled at gc D2) · **Contract:** `docs/milestones/hc-consolidation.md` decision 10
**Size:** S to decide · **Priority:** medium
**Section:** process / round vocabulary (`docs/milestones/hc-consolidation.md`, `cloudcost/m5-n1-compose.md`)

Filed 2026-08-12 at gc t3, per **D2**. **This row poses the question; it does not settle it.**

**What happened.** gc t1 reported a contradiction: `cloudcost/m5-n1-compose.md` §Not established
item 1 calls two statements in `cloudcost/m4-consolidation.md` *"live"*, while the `gc` round ruled
that document **archival** under hc decision 10. Both are correct, because *live* means two
different things. m5 uses it for **unretracted-at-HEAD** — the statements have not been withdrawn.
hc decision 10 uses it for **read-for-current-guidance** — whether a reader seeking the current
answer goes there. A document can be the first and not the second, and m4-consolidation is exactly
that.

**Why the existing rules do not cover it.** Neither document defines the word, and both use it in
load-bearing positions: decision 10 turns on it, and §Not established item 1's disposition turns on
it. The instrument that surfaced the collision — a census cross-joining claims against current
state — **cannot tell the two senses apart**, because both render as the same English. gc D2 ruled
the specific case and explicitly declined to rule the vocabulary: *"the equivocation is itself a
finding this round records rather than resolves."*

**Determine whether the two senses should be separated in vocabulary** — one word retired, or both
kept with a stated discriminator — and where that lands, given that decision 10 lives in a closed
round's document and is cited by rounds after it.

**Done when:** either a discriminator is stated in one named document and the citing rounds are
consistent with it, or the collision is recorded as accepted with the reason, so the next census
author is warned before building an instrument that cannot see it.

**Costs:** S to decide. The scope question is larger than the wording: decision 10 is a standing hc
decision, and **gc D6 already interprets it** without amending it, reserving the write-back question
for that round's close. This row and that reservation are the same seam approached from two sides.

`Source: gc t1 §X.1, 2026-08-11 (filed there as a contradiction between two live documents); ruled
an equivocation at gc D2 and carried to gc §Promotion candidates. Filed gc t3, 2026-08-12.`

---

### BL-150 — standing: documentation-system findings, append-only (#TBD)
**Kind:** standing · **Census items:** n/a · **Contract:** `docs/milestones/hc-consolidation.md` R23
**Size:** n/a — does not close on any single item · **Priority:** medium
**Section:** process / documentation system (both repos)

Created 2026-08-12 at the gc t3 review, per **R23**. **This row collects; it does not settle.**

**What it is.** The single home for findings about **how the documentation system works** rather
than about what any document says. A status surface that disagrees with itself; a marker that cannot
be told apart from a quotation of one; a stamp whose absence encodes three different dispositions; a
pointer that resolves to a real section that does not contain the cited text. Each is an observation
about a system with one shape, not a unit of work — so each **appends here** rather than opening its
own row.

**Why a standing row and not five rows.** R23's ground: filing each separately produces a backlog
growing faster than anything discharges it, and each row states a question so small that closing it
changes nothing. The prompting instance is gc t1's census, which surfaced five such findings in one
pass.

**It is append-only and does not close on any single item.** Clearing the list is not the discharge.
What discharges it is a decision about the system — where these defects are collected, who rules on
them, and what standard retires one — which is the question below.

**Determine where documentation-system defects are collected and what discharges them.** Whether
this row is the permanent home or an interim one; whether an appended item can be individually
retired or only the row as a whole; and what evidence closes the question rather than the list.

**Applies forward. BL-145–BL-149 are not collapsed into this row.** They were filed by gc t3 on
2026-08-12, hours before R23 was ruled, under the rule then in force — the agents-side requirement
that a deferred finding gets a backlog row in the round that defers it. Re-filing rows a round has
just filed is the churn R23 exists to stop. They stand as filed; this row begins with what comes
next.

**Done when:** the collection question is answered in one named document with its scope — or
declined, with the reason recorded and this row's fate stated either way. **Not** when the appended
list is empty.

**Costs:** n/a to hold. The decision is S; the appended items carry their own costs.

**Appended.**

- `2026-08-12` — The three §Learning entries promoted from m5's carried candidates at the gc close
  (round records; negative controls; §7's distillation) landed in harness `CLAUDE.md` because t4's
  `Touches` named that file, while gc t1 established the packet-and-record family sits agents-side.
  Recorded so it is findable; not triaged here.

- `2026-08-14` — **The U2 leak check's scope excludes the review packet, which is the artifact
  most likely to leave the repo.** m6 t2's packet ran a leak check over all tracked files and the
  untracked implementation notes, and it **passed**. The packet itself was outside that scope. At
  t3 six live Copilot seat logins and the organisation login went into the packet unredacted —
  paired, in one table, with each person's Copilot last-activity timestamp to the second — and
  into the committed implementation notes with them. **It was found by the leak reaching a review,
  not by the check.** The check is repo-scoped and the packet is pasted into a review conversation
  by design, so the one channel that carries content off the machine is the one nothing was
  watching; and the check's passing at t2 was **not evidence about that round's packet**, though
  it reads as though it were. Recorded here rather than as its own row because it is a fact about
  how the record-keeping system verifies itself rather than a code defect. **No fix proposed** —
  that is this row's to decide. `[One tension worth stating rather than resolving: BL-150 collects
  by SUBJECT (the documentation system), and by that test this belongs here. By MECHANISM it is
  BL-152/BL-153's class — a verification that can silently yield a wrong answer — and if the
  collection question this row exists to answer is ever settled by routing on mechanism, this
  entry moves. Source: m6 t3, `cloudcost/docs/m6-t3-implementation-notes.md` §8a–8b, which carries
  the blast radius and the remediation.]`

- `2026-08-13` — The five cloudcost milestone documents carry **two forms** of post-H1 provenance
  block: `milestone.md`, `m2-milestone.md`, `m3-milestone.md` and `m4-consolidation.md` open with a
  bolded `**Status:**` paragraph, while `m5-n1-compose.md` opens with a backtick-quoted stamp. m5's
  departure from the preceding four is **unexplained by its own text** (which contains no occurrence
  of the string "Status"), **by its opening commit** `eebd47c`, and **by its own provenance stamp**,
  which cites R12 — a rule about when a ticket's anatomy is authored, not about header form.
  **Intent was not established, in either direction**: nothing found says the change was deliberate,
  and nothing says it was not. m6 t1 followed m5's form on recency grounds and left
  `m5-n1-compose.md` unchanged. Recorded so it is findable; not triaged here.

- `2026-08-14` — **§7's closing test cannot be performed by a milestone that commits no review
  file, and the absence is invisible from inside the close.** Methodology §7 ends with a success
  test: *"the same finding class should not appear as `blocking` in two consecutive milestones."*
  It is keyed on a **label that only a review file carries**. m6 committed none — `git log
  --name-only e4fabb7..e0c1ee2` lists no review artefact, the cycle's packets being scratch — so
  no finding in the milestone carries a label the close can read, and the test cannot be run on
  its own terms. **What makes this a documentation-system finding rather than one milestone's
  omission**: nothing in the close's own procedure surfaces the gap. Every other §7 step produced
  an artefact whose absence would have been noticed; this one produces a judgement, and a
  judgement over an empty population reads exactly like a judgement that found nothing. The m6
  close reported it only because it went looking for the test's input and found the input did not
  exist. **Not triaged and no fix proposed** — whether the remedy is committing review files,
  re-keying the test on something the tree keeps, or accepting that the test binds only cycles
  that commit them, is the collection question this row exists to hold rather than answer.
  `[Recorded at the m6 close, 2026-08-14, by arbiter ruling. Source: the close's own §5, and
  cloudcost/docs/m6-close-implementation-notes.md §4d, which carries what the surviving records
  do show — no m6 notes file records a blocking finding at all, and the two defects that did stop
  work were found by the tickets themselves rather than by a reviewer.]`

`Source: R23, ruled by the arbiter 2026-08-12 at the gc t3 review and recorded at
docs/milestones/hc-consolidation.md. Row created in the same commit, per R23's own stamp. The five
findings that prompted it are BL-145–BL-149, which stand as separately filed.`

---

### BL-151 — standing: code findings, append-only (#TBD)
**Kind:** standing · **Census items:** n/a · **Contract:** `docs/milestones/hc-consolidation.md` R26
**Size:** n/a — does not close on any single item · **Priority:** medium
**Section:** code / cloudcost and any use case (both repos)

Created 2026-08-13 at m6 t2b, per **R26**. **This row collects; it does not settle.**

**What it is.** The single home for **small code defects that break nothing today**. A private
helper duplicating a shared one that the module already imports from; an unreachable statement
after a return; two surfaces that must agree with nothing checking that they do. Each is a real
defect with a real fix and no urgency, so each **appends here** rather than opening its own row.

**Why a separate row from BL-150 and not a widening of it.** The two discharge differently. A
documentation-system finding closes on a **decision about the system** — where such defects are
collected, who rules on them, what retires one. A code finding closes by **being fixed**. One row
cannot state both discharge conditions, so widening BL-150 would have given half its contents a
`Done when:` that does not apply to them.

**It is append-only and does not close on any single item.** Clearing the list is not the
discharge. Fixing every entry here would leave the question this row asks unanswered.

**Determine how these are swept and what retires one.** Whether an appended item is retired
individually when fixed or only struck when the row as a whole is disposed; whether a sweep runs at
a milestone close, at a cadence, or on demand; and who decides an item is too small to keep.

**A finding with a natural home does not come here.** The row is for defects with nowhere else to
go. A defect in a file the current ticket is already editing is fixed in that ticket — filing it
here instead is the deferral R26 exists to discourage, not the collection it exists to enable.
`CLOUDCOST_GITHUB_ORG`'s missing `KNOB_CONSTANTS` entry was found at t2b and fixed at t2b on
exactly that ground; only the *unchecked-agreement* residue below is filed.

**Done when:** the sweep-and-retirement question is answered in one named document with its scope —
or declined, with the reason recorded and this row's fate stated either way. **Not** when the
appended list is empty.

**Costs:** n/a to hold. The decision is S; the appended items carry their own costs, all small.

**Appended.**

- `2026-08-13` — `cloudcost/scripts/fetch_aws.py:391` defines a private `money(value) -> float`
  that duplicates `_normalized.money` (`:92–97`) — same `round(float(value), 2)`, same
  `(TypeError, ValueError) → 0.0` — while the module **does** import from `_normalized`
  (`:41–50`, eight `TYPE_*`/`STATE_*` names) without taking `money`. So C4's "every amount is
  coerced through one function" guarantee has **two** implementations. Byte-equivalent in
  behaviour today; **nothing enforces that**, and the two would diverge silently. Verified at
  agents `0303597`. Recorded so it is findable; not triaged here.

- `2026-08-13` — `cloudcost/tests/conftest.py:724` carries an unreachable `return aws_stub`,
  after `full_linode_stub`'s own `return linode_stub` at `:723`. Dead on arrival and harmless;
  the name it returns is a different fixture's, which is what makes it worth recording rather
  than merely tidying. Verified at agents `0303597`. Recorded so it is findable; not triaged here.

- `2026-08-13` — An adapter's operator **knob** must be declared in two unlinked places: a
  `tools.json` `env` row (what an operator may configure, read by Rig) and `KNOB_CONSTANTS` in
  `../aetheris/scripts/sprint.sh`'s adapter env bridge (what survives the default-deny prefix).
  **Nothing checks that the two agree**, and m6 t2b found them disagreeing — `CLOUDCOST_GITHUB_ORG`
  was declared on the adapter as `ORG_ENV` and absent from `KNOB_CONSTANTS`, so the prefix stripped
  it. That instance was **fixed at t2b**; what is filed is the absence of a check, which lets the
  next provider — or a later edit to either surface — diverge again. The absence was verified at
  HEAD: `tests/test_tools_manifests.py` is the only reader of `cloudcost/tools.json` in either repo
  and never mentions `sprint.sh` or `KNOB_CONSTANTS`; `sprint.sh` reads the adapter modules
  directly and never opens `tools.json`; `drift_check.py`'s check 4 (`env_vars`) compares Rust
  `env::var()` calls against `docs/rig/specs.md` §1 and `runbook.md`, touching neither surface. No
  check is proposed here. Recorded so it is findable; not triaged here.

- `2026-08-14` — `EnvDep` has **no optionality axis**, so Rig renders every declared env row under
  the heading **"Required config"** — including ones whose own text says they are not.
  `EnvDep` (`rig/src-tauri/src/commands/tools.rs:6-13`, TS mirror `rig/src/hooks/types.ts:427-433`)
  carries `key`/`label`/`group`/`masked`/`placeholder` and nothing else, while its sibling
  `ManifestArg` (`tools.rs:15-24`) *does* carry `required: bool` — so the axis exists on the args
  half of the same manifest and not on the env half. `ToolDetail.tsx:85` prints the heading over
  `script.env` unconditionally. The live instance is `CLOUDCOST_GITHUB_ORG`, whose `label` reads
  *"GitHub organisation login (optional; unset, the token's sole membership is used)"*
  (`cloudcost/tools.json:295`): the row states optional underneath a heading that states required,
  and an operator reading the screen cannot tell which is authoritative. Two surfaces that must
  agree with nothing checking that they do — the same shape as the `KNOB_CONSTANTS` entry above,
  except that here both surfaces are Rig's own and the disagreement is visible on screen rather
  than latent. Verified at agents `97c61a0`. `cloudcost/runbook.md` §Rig's credential table gained
  a pointer at m6 t4 so the operator has somewhere correct to read; that is a caption over the
  defect, not a fix. No fix is proposed here. Recorded so it is findable; not triaged here.

- `2026-08-16` — `ROADMAP.md:246` states *"pytest passes before sprint.sh runs"*. It names **no
  command and no scope**, and BL-152 has since made the whole-suite gate a specific invocation
  that **deselects 320 of 1714 tests** — so the sentence now reads as a claim about a suite no
  command runs. The gate rule BL-152 landed in `CLAUDE.md` §Definition of done says the opposite:
  *the gate is the command, not the outcome*. Breaks nothing; a reader following `ROADMAP.md`
  simply learns nothing executable. Left uncorrected at BL-152 deliberately, because fixing it
  means adjudicating a payslip-era document's intent, which was outside that ticket. Verified at
  agents `2868a3e`. Recorded so it is findable; not triaged here.

- `2026-08-16` — A `python3 -m pytest -q -m integration` run **outlived its own
  `timeout 2700` SIGTERM**. Sampled at 52m21s elapsed: `timeout` still present as the parent,
  the pytest process in state `Rl` at **4.1% CPU with no child process**, still emitting progress
  characters. It was killed with `SIGKILL` rather than waited out. No explanation was established
  and none is proposed — a plausible one is a long-running C-extension call deferring Python's
  signal handler, but that was **not verified** and is recorded as a guess, not a finding. It
  matters because a cap that does not actually cap is a cap a future session will trust wrongly.
  Verified at agents `2868a3e` (the observation predates that commit; the code involved is
  unchanged by it). Recorded so it is findable; not triaged here.

- `2026-08-16` — `agents/orchestrator.exs` **validates the agent path the planner emits against
  nothing.** The model's `step["agent"]` is joined to the agents root
  (`agents/orchestrator.exs:267-268`) and handed straight to
  `RunHelpers.load_agent_file/1` (`:287`) — no allowlist, no membership test against the
  capability matrix the planner was given, no containment check on the joined path. The matrix is
  read whole into the system prompt (`:17-18`) and the prompt *instructs* the model that paths
  *"must match exactly the file paths listed in the capability matrix"*, so the constraint exists
  only as prose addressed to the model. Breaks nothing today: the planner is a first-party prompt
  over a first-party matrix, and a path that does not resolve simply fails the `with`. No fix is
  proposed here. Distinct from **BL-156**, which owns the approval card's *step text*
  (`description`/`context`), and from **BL-094**, which owns the absence of a direct non-LLM door
  — this is the *path* field rather than the prose fields, and it is about validation rather than
  about an alternative launch route. Verified at agents `900662f`. Recorded so it is findable; not
  triaged here.

- `2026-08-16` — **a column a script owns half of is a column nobody owns.** The manifest table's
  `last changed` cell was maintained by neither the mechanism nor an operator.
  `scripts/repin_manifest.py` re-derived the `commit` cell and, by its own docstring, claimed *"no
  authority over … the `last changed` column"*; `drift_check.py`'s check 8 parses the commit cell
  and never reads the date. So after the 2026-08-16 re-pin both movers carried commits dated
  2026-08-16 beside a `last changed` reading 2026-08-14, and **nothing in either repo could have
  said so** — the same blindness the mirror pair has, where a `diff -q` at the boundary is the only
  instrument. The class, which is the reason this is seeded and not merely fixed: a script that
  authoritatively owns *some* cells of a record makes the rest look owned too, and a half-owned
  record decays faster than an unowned one because its green is partly earned. **The defect is
  fixed in the next commit of this same pass** — `repin_manifest.py` derives `last changed` from
  the commit it already resolved, so the two cells cannot disagree — which is why this entry
  records the *class* rather than an open defect. The defect is verified at agents `a2df7b5`; the
  fix is **not** verifiable at this commit, deliberately, and is stated as forward rather than
  asserted here. Recorded so it is findable; not triaged here.

- `2026-08-16` — **nothing verifies arithmetic stated in prose.** The 2026-08-16 export boundary's
  section asserted *"the same 23 rows current"* over a 25-row table carrying two movers and one
  self row; 2 + 22 + 1 = 25, so the figure was 22. It was committed wrong and caught by
  **re-reading the committed section**, not by any check — `drift_check`'s check 8 parses the
  table's cells and never reads the prose around it, and no other instrument in either repo looks
  at a number in a sentence. The class is wider than one manifest: every boundary record, review
  packet and milestone summary in this repo states counts in prose, and each is a claim nothing
  can test. **The cheap mitigation, already applied at the correcting commit** (`7cf1789`): print
  the sum beside the figure — *"2 + 22 + 1 = 25"* — so the arithmetic is in public and a reader
  checks it in a glance rather than reconstructing the population first. **Kinship, stated because
  it is the same family and not the same rule:** `CLAUDE.md` §Learning — BL-152 holds that *a count
  recorded in prose carries the command that reproduces it*. That covers a figure over a population
  the repo will keep changing, and it does not reach this one — a row count is derivable, the
  boundary section is a snapshot that will not be re-derived, and what was wrong here was not the
  population but the addition. Showing the sum is to arithmetic what naming the command is to a
  census. **No proposal beyond that**, and specifically no checker: a linter for prose arithmetic
  would have to parse intent, and the failure is cheap to catch by the habit. Verified at agents
  `7cf1789`. Recorded so it is findable; not triaged here.

- `2026-08-16` — **push state does not belong in a point-in-time record.** Four `Repo push state`
  paragraphs in `docs/project-knowledge-manifest.md` assert that a boundary's commits are held and
  unpushed: the 2026-08-05 m3-cloudcost close (`:347–352`, *"held for review, not pushed"*), and
  each of the three passes of the 2026-08-16 boundary (`:632–637`, `:732–737`, `:802–805`). **All
  four are false, and none was ever discharged** — `git rev-list --left-right --count
  HEAD...origin/main` returns `0 0`, and `git branch -r --contains <hash>` returns `origin/main`
  for every commit those four paragraphs name (`de71e2b`, `29a51fa`, `a2df7b5`, `8653546`,
  `ef651f9`, `fd03bf3`). So the manifest raises a condition nothing in it closes, and a reader
  cannot tell from the document whether the hashes it pins are public — which is the one question
  those paragraphs exist to answer. **Two of the four were written the same day they went false**,
  at this boundary's own later passes: true when written, false when the commits were pushed, with
  no edit to the file and nothing anywhere noting the change. That is the mechanism rather than a
  detail — the claim decays without anyone touching the record, so a discipline of *"amend it when
  you push"* would have to fire in a session that has no reason to open the file. **The shape of
  the fix, not decided:** state what was pinned and leave push state to
  `git branch -r --contains <hash>`, which answers it at any later moment, instead of asserting a
  status the record cannot maintain. Kinship: `CLAUDE.md` §Learning — BL-152, *a count recorded in
  prose carries the command that reproduces it*, applied to a **status** rather than a figure. The
  two paragraphs at `:208` and `:263` are **not** instances — they claim synced, not held, and are
  still true. Recorded as a recurrence, four instances, not one. Verified at agents `9741c4e`.
  Recorded so it is findable; not triaged here.

**Deliberately not seeded: the top-level `email/` directory versus stdlib `email`.** Raised at
BL-152's amendment and **established inert by reading and by running it**, so nothing is filed.
`python3 -m` puts the repo root on `sys.path` (as `''`), and `email/` is the only top-level
directory in this repo sharing a name with a stdlib module. It does **not** shadow: with the repo
root at `sys.path[0]`, `import email` resolves to
`…/python3.12/lib/python3.12/email/__init__.py`. A directory without `__init__.py` contributes
only a *namespace portion*, which does not stop the path scan, and a regular package found later
on the path wins. The conditional hazard is real — adding `email/__init__.py` would make the repo
root's copy a regular package at `sys.path[0]` and shadow stdlib `email` repo-wide — but it is
already governed by a documented convention (`CLAUDE.md` §Python script conventions;
`docs/agent-creation-guide.md:307`), and a row asserting a defect that does not exist today would
be a false entry. Verified at agents `2868a3e`. The omission is a decision, not an oversight.

**Deliberately not seeded: `fetch_linode.py`'s round-before-multiply.** The `PriceTable` rounds its
unit rate at ingest (`:396`, `:402`) and multiplies at `:763`, which is the shape D4 rules on. It is
**already dispositioned** as `cloudcost/m6-github.md` D4's recorded counter-example, and a second
record of the same finding is the two-surfaces defect **BL-145** ruled on. The omission is a
decision, not an oversight.

`Source: R26, ruled by the arbiter 2026-08-13 at m6 t2b and recorded at
docs/milestones/hc-consolidation.md. Row created in the same commit, per R26's own stamp. The
ruling's ground is three code findings dropped across m6 t1 and t2 for want of a place to put
them; two of those are seeded above, and the third entry is a finding of t2b's own rather than a
recovered one — the dropped third is not reconstructed here, and this note says so instead of
letting the seed count imply it was.`

---

### BL-152 — the repo-root `pytest` invocation cannot collect (#TBD)
**Kind:** gate · **Census items:** n/a · **Contract:** `CLAUDE.md` (agents) §Definition of done — *every existing gate runs at ticket boundaries, even off-territory*
**Size:** S · **Priority:** medium — **CLOSED 2026-08-16**
**Section:** test apparatus (agents)

Filed 2026-08-13 at m6 t2b, **the day it was found**, by a ticket whose own done-check is the
repo-root whole-suite command. Off-territory: t2b touches neither module below.

**What is red.** `cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest -q` aborts during
collection:

```
ERROR boxy-pipeline/tests/test_pipeline.py               ModuleNotFoundError: No module named 'main'
ERROR provenance/mcp/corpus-search/tests/test_server.py  ModuleNotFoundError: No module named 'tests.test_server'
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
```

Collection is *interrupted*, so **no test runs at all** — the command is not "mostly green with
two errors", it is a command that executes nothing.

**Not introduced by t2b.** Reproduced with t2b's changes stashed, at agents `0303597`.

**Not broken product code.** Both modules import and their tests run when pytest is invoked
against their own scope. This is a rootdir / `sys.path` collection defect — the repo has no
`pytest.ini`, `setup.cfg` or `pyproject.toml`, so rootdir and `sys.path` are inferred per
invocation, and each use case's `conftest.py` inserts its own `scripts/` only.

**The two named modules are the visible edge of it, not the extent.** Scopes that collect
cleanly alone fail when *combined*, which means the defect is not "two broken files":

```
python3 -m pytest cloudcost/tests/ -q --collect-only    → 440 tests collected
python3 -m pytest tests/          -q --collect-only    → 136 tests collected
python3 -m pytest cloudcost/tests/ tests/ -q --collect-only
                                                        → 136 collected, 8 errors, Interrupted
```

So no single invocation covers even two scopes at once. Any fix must be verified by collecting
the whole tree, not by making the two named modules import.

**And collection is only the first obstacle.** With the two uncollectable modules `--ignore`d, the
tree run reaches `boxy-pipeline` and blocks inside a live subprocess —
`boxy-pipeline/scripts/plan_extractor.py` against two sample PDFs — still running at 8m42s with no
output, and killed rather than waited out. So even a collection fix would leave the root command
running live extraction work on every invocation. Whatever replaces it has to decide what the
whole-suite gate *excludes*, not only what it can import; the `@pytest.mark.integration`
convention already used elsewhere in the repo is the obvious lever and is not applied here.

**Why it matters more than it looks.** Ticket done-checks are written as *the whole suite, not
`<use_case>/tests/`* precisely when a change touches a root-level test — t2b's W3 is that case.
A done-check whose literal command collects nothing cannot distinguish a green repo from a broken
one, which is the **Silent-wrong-answer** class in the apparatus rather than the product. Sessions
have been running scoped invocations and reporting whole-suite-shaped numbers (m6 t1's *"386
passed"* is not reproducible from the root command), so the divergence has been invisible in both
directions.

**When it went red is unknown**, and nothing was watching in either direction — the same
invisibility the standing gate rule exists to prevent.

**Done when:** `python3 -m pytest -q` from the repo root collects every test module and its result
is a real pass/fail over the whole suite — or the root-level invocation is declared not to be the
gate, in one named document, with the gate that replaces it stated and the done-check wording in
`CLAUDE.md` corrected to match. **Not** when the two modules are individually skipped.

**Costs:** S. Likely one `pytest.ini`/`conftest.py` at the root fixing rootdir and `sys.path`;
the risk is that pinning rootdir changes how every use case's existing `conftest.py` resolves, so
it needs the whole suite run before and after rather than the two modules alone.

`Source: m6 t2b, 2026-08-13. Found by running the ticket's own stage-1 done-check command
verbatim, then reproduced with the ticket's changes stashed to establish it was inherited. Filed
rather than left in the packet, per the standing rule that prose in a packet or notes files
nothing.`

**Annotated 2026-08-16 (BL-152's own ticket): the gate exists and is green; the row is NOT
closed.** Established at agents `6ffcd76` / harness `d19f4b6`; record at
`docs/milestones/bl-152-implementation-notes.md`.

**The gate is now** `python3 -m pytest -q -m "not integration and not dormant"`, run from the
`aetheris-agents/` repo root, stated as that command — not as an outcome — in `CLAUDE.md`
§Definition of done, which also extends the standing gate enumeration to include it.
`1384 passed, 3 skipped, 320 deselected, 7 xfailed in 178.56s`, exit 0.

**Two exclusions, two markers, never merged, and the gate prints both counts** on its own summary
line: `deselected by reason: integration=112, dormant=208 (total 320)`. `integration` asserts
*test mechanics* — the test depends on state outside this repo's tracked tree. `dormant` asserts
*business state* — boxy-pipeline's work is paused pending its client, dated, with the condition
for return recorded in `pytest.ini` (*it runs again when boxy-pipeline work resumes*). Dormant
tests **still collect and still import**; 208 of them, deselected at run time and never at import,
because a use case whose tests stop collecting is the very rot this row exists to remove. Each set
has its own command, so an exclusion is a deferral rather than a deletion:
`python3 -m pytest -q -m "integration and not dormant"` and `python3 -m pytest -q -m dormant`.
Neither marker is in `addopts`. Dormancy was applied to the test apparatus and nothing else — no
sprint case, tools manifest, runbook or capability list was touched, and no boxy code, fixture or
output was moved.

**What fixed collection.** A root `pytest.ini` — pinning rootdir, and
`addopts = --import-mode=importlib` — plus one `sys.path.insert` in
`boxy-pipeline/tests/conftest.py` and the deletion of the empty `email/tests/__init__.py`. Not
`--ignore`, not `skip`, not `xfail`, and no product code. The row's *"two named modules are the
visible edge, not the extent"* is confirmed: three distinct module-name collisions under pytest's
default `prepend` import mode, only one of which either named module shows —
`tests/conftest.py` vs `cloudcost/tests/conftest.py` both claiming `conftest` (the row's 8
errors); `email/tests/` vs `provenance/mcp/corpus-search/tests/` both claiming the package
`tests`; and `boxy-pipeline/main.py` reachable only when the working directory *is*
`boxy-pipeline/`, because `python3 -m` puts the cwd on `sys.path` and nothing else did.

**The true whole-suite figure is 1714 collected, zero collection errors**, equal to the sum of all
twelve per-scope collections, and the gate accounts for every one of them (1384 + 3 + 7 + 320).
Only one scope's count moved — `boxy-pipeline/tests` 196+error → 208, the twelve tests in
`test_pipeline.py` that could not previously be imported from the root — so the *Costs*
paragraph's stated risk did not materialise. It reconciles with **no** figure previously recorded
here, and should not: every *"full suite"* number in the notes — m6 t1's **386 passed** included —
is printed beside `python3 -m pytest cloudcost/tests/`, a scope figure that was never a
root-command figure. That scope runs 464 passed today. Neither number is adjusted.

**Ten tests gained `@pytest.mark.integration`** — three in
`boxy-pipeline/tests/test_plan_extractor.py` reading gitignored client PDFs (four siblings with
the identical guard were already marked; these three were the inconsistency), seven in
`provenance/tests/` spawning `mix run --eval` in the sibling `../aetheris`. **None was red**:
the pre-marker tree run was 1545 passed / 0 failed and the post-marker run 1535, and 1545 − 1535
is exactly the ten. **Where this ticket exercised judgement the row did not settle**: the line
between those seven and the many tests that `subprocess.run` this repo's *own* tracked scripts is
drawn at *leaves this repository*, and is the packet's question for the arbiter.

**Reds found, reported, not fixed.**
`boxy-pipeline/tests/test_catalog_resolver_refactor.py::test_real_jsonl_resolve_matches_excel_result`
**FAILED** and is left red inside the dormant set — deselected for dormancy, never for failing. A
second failure in the same set is **unidentified**: the verbose run was cap-killed before reaching
it, and it is not named by inference. Separately, the ticket introduced and then removed a red of
its own: a root `conftest.py` shadowed the bare module name `conftest` that ten cloudcost lines
import at runtime, breaking two tests; the hooks moved to `tests/conftest.py`. That fragility
remains latent and is offered as a candidate row rather than fixed here.

**Every run that can reach live subprocess work ran under an explicit wall-clock cap, and a
cap-kill is recorded as a result.** `-m "integration and not dormant"` completes in 25.27s. The
dormant set is documented and **deliberately not run**: two capped runs made before the split were
killed at 52m21s (cap 2700s, 37/169) and 10m17s (cap 2400s, 21/57), the first stalled at
`test_plan_path_produces_same_output_as_drawings_path` — which spawns `plan_extractor.py` against
the two sample PDFs, exactly as the row describes. **The row's "blocks inside a live subprocess"
is confirmed, not refuted**; projected from the observed rate that set needs roughly four hours,
and it is now behind a marker nothing runs by default.

**Two of the row's other pointers were wrong at HEAD**, corrected in the notes rather than here:
the scope counts have moved (`cloudcost/tests/` 440 → 465, `tests/` 136 → 164, the 8-error
combination result exact); and *"their tests run when pytest is invoked against their own scope"*
is false for `boxy-pipeline/tests` from the repo root, which is the mechanism rather than a
detail.

**The harness needs no change; its HEAD is unchanged at `d19f4b6`.** `sprint.sh`'s
`python3 -m pytest ../aetheris-agents/api/{tenant,gateway}/tests/ -q` legs now find this
`pytest.ini` by upward search and are unaffected — 108 passed, 11 skipped, the same 119 collected
as before. Every scoped invocation in every runbook, README and milestone doc in both repos
collects identically before and after, verified scope by scope in both the root-relative and
cwd-relative forms, so none of them was edited.

`[CLOSED 2026-08-16 by the arbiter, on the BL-152 packet and its amendment —
agents 2868a3e and ace771c, both public. Closed on the row's FIRST branch: the
root invocation collects the whole tree and yields a real result. With one
qualification the row's own text demanded — the gate EXCLUDES tests, by two
separately named markers, each carrying its own command, with both counts printed
on every run that deselects anything. The row anticipated this in its "collection
is only the first obstacle" paragraph. The exclusion policy is part of what closed
it, not an escape from it.

WHAT THE CLOSURE CLAIMS. The root command collects every test module with zero
collection errors and its result is a real pass/fail over the set it runs.
CLAUDE.md names the COMMAND rather than an outcome, so that sentence stays true on
a day the suite is red. The per-scope census reconciles with the whole-tree total
in both root-relative and cwd-relative forms, so no scope silently lost tests to
the rootdir pin — which was this row's own stated Costs risk, and it did not
materialise.

WHAT IT DOES NOT CLAIM, recorded so no later reader mistakes a green gate for a
trustworthy suite. The gate deselects tests on marks that are registered but not
audited against the criterion the gate now uses (BL-158). The dormant set does not
terminate usefully, holds one named red left deliberately red, and holds at least
one further failure nobody has identified (BL-159). The bare name `conftest`
remains a trap held open by an absence that nothing checks (BL-157). The gate
reports truthfully about the population it runs; it certifies nothing about the
population it does not.

RULING 1 FIRED, IN A DIRECTION THE TICKET DID NOT PREDICT. The failures the fix
exposed were not in the gate's population but in the dormant one. The ticket also
introduced a red of its own — a root conftest.py breaking ten runtime
`from conftest import …` sites — and recorded it against itself after two runs had
reported a green gate that was not green. The positive control caught it. That is
the first occasion in this project on which a control paid for itself inside the
ticket that built it.

TWO OF THIS ROW'S OWN CLAIMS RESOLVED. "Both modules import and their tests run
when pytest is invoked against their own scope" was FALSE for boxy-pipeline, which
collects only with cwd set to its own directory. And m6 t1's "386 passed" was
never a root-command figure and was never presented as one — the mismatch was
between the number and the phrase "full suite" standing beside it, not between two
measurements. "When it went red is unknown" remains unknown, and is now moot.

THE ARBITER'S `integration` CRITERION WAS WRONG AS FIRST WRITTEN and was corrected
by the implementing session. Phrased as "would it pass in a fresh clone", it
exempted every test that guards itself with a skip — which was all ten it had just
been written to justify. The shipped criterion counts a silent skip. Recorded
because the defect was in the ruling, not in the work.]`

`[2026-08-16, appended after the closure. The earlier annotation in this row
stating that the row is NOT closed was TRUE WHEN WRITTEN — it recorded the
implementing session's correct refusal to close its own row — and is SUPERSEDED
by the closure above. It is left standing because dated annotations in this file
record what was believed at a date and are not rewritten. The row's status is the
`CLOSED` marker on its Size/Priority line.]`

---

### BL-153 — the cloudcost sprint's credential gate exits before the stale-artifact guard, so a credential-less leg leaves the previous run's artifacts in place (#TBD)
**Kind:** defect · **Census items:** n/a · **Contract:** `../aetheris/CLAUDE.md` **Silent-wrong-answer** — *stale/leftover artifacts from a prior run*; *bind an artifact to what produced it, never to its position in a listing*
**Size:** S · **Priority:** medium
**Section:** harness (`../aetheris/scripts/sprint.sh`) — **cross-repo**

Filed 2026-08-13 at m6 t2c, **the day it was found**, by a ticket whose deliverable is a
before/after comparison of rendered report artifacts. Off-territory: t2c touches no harness file.
**Sibling of BL-152** — both are verification mechanisms that can silently yield a wrong answer,
and this one produced false evidence inside the session that found it.

**The ordering.** The cloudcost case preflights the selected provider's credential at
`sprint.sh:2894–2931` and `exit 1`s when it is absent. The stale-artifact guard —
`find "$CLOUDCOST_OUT" -mindepth 1 -delete`, `sprint.sh:2934–2946` — runs **after** it, and is
therefore never reached on that path. The previous run's report and JSON survive, under the
right filenames, for the right period, with content that parses.

**The guard's own comment names the case it cannot cover.** At `sprint.sh:2937–2940`:

> a run whose orchestrator fails (expired credential, provider API down) greens on the
> *previous* run's report and orphan count: a check that passes identically whether or not the
> thing under test worked.

*Expired credential* is the first example it gives. An **absent** credential exits before the
guard, so the one failure mode the guard names first is the one the ordering excludes it from.

**Established at HEAD** (agents `0b32f36`, harness `d19f4b6`), by running it:

```
$ env -u CLOUDCOST_DO_TOKEN ./scripts/sprint.sh cloudcost
artifacts present before: 5 file(s)
sprint exit code: 1
artifacts present after:  5 file(s)
report md5 unchanged: YES - the previous run survives
guard ran? 0 (0 = it did not)
[FAIL]  CLOUDCOST_DO_TOKEN is not set — the digitalocean pipeline needs the read-only DO PAT
```

**What is and is not at risk, stated precisely rather than overclaimed.** The sprint **does exit
1**, so anything watching the exit code is safe, and no *sprint assertion* greens on the stale
files — the run stops before any of them. The exposure is to **whatever reads the output
directory afterwards**: a session, a reviewer, a packet, or a later tool inspecting artifacts to
establish what a run produced. By content alone the survivors are indistinguishable from a live
capture.

**It fires for any provider whose credential is unsourced** — the preflight `case` has the same
`fail`-then-`exit 1` shape for digitalocean, aws, linode and github, and the unknown-provider arm
too. It is not DO-specific.

**How it was caught, recorded because reading could not have caught it.** m6 t2c copied
`cloudcost/output/digitalocean/` as a "live before-state" for its done-check-4 pairing. It was
the previous run's output. What exposed it was checking the **exit code** and diffing against a
baseline preserved earlier in the session — not inspection of the artifacts, which parse, carry
the right period, and are internally consistent.

`[Annotated 2026-08-14 at m6 t3 — a SECOND MECHANISM reaching this row's symptom, recorded
here rather than as its own row because the symptom is the same one: sprint output that cannot
be trusted from its own content. **Inputs changing under a run, rather than a credential gate
skipping the guard.** m6 t2c's session discarded a sprint run because a template edit landed
while that run was still rendering. **The run exited 0**, and its output was indistinguishable
by content from the frozen-tree run that replaced it — so the exit-code check that catches the
credential-gate arm does not catch this one, and neither does anything in the artifacts. What
caught it was knowing an edit had happened. **The mitigation used was freezing the tree and
recording source mtimes before the run, which is a discipline rather than an enforced check** —
nothing in the sprint reads a source mtime or stamps the tree state a run was produced from.
Recorded so the arm-ordering decision below is taken knowing the row has two mechanisms and
not one; **it does not widen this row's scope and proposes no fix**, and the ruling the row
owes is still outstanding. Source: the m6 t2c session's own account, relayed in m6 t3's ticket
prompt. Not reconstructible from the tree — the discarded run left no artifact and the notes
file does not record it.]`

`[Annotated 2026-08-14 at m6 t4 — a THIRD MECHANISM, and the one that says what this row is
actually about. **A run killed from Rig's Cancel leaves its own partial prefix.**
`orchestrate_cancel` (`rig/src-tauri/src/commands/orchestrate.rs:149-159`) SIGKILLs the direct
child, so a pipeline killed between stages leaves whatever the completed stages wrote — a cost
snapshot and inventory with no orphan candidates and no report, or a report over a half-written
inventory — in the provider's output directory, where the next run's reader finds them.
**Weaker than the first two as a silent-wrong-answer**, and the packet that found it said so:
there is an observable cause, because a human pressed Cancel and knows they did. **Stronger as
evidence about the row's subject.** Three mechanisms now reach one symptom — a credential gate
skipping the guard, inputs changing under a run, and a run dying mid-flight — and they have no
fix in common. Reordering the sprint's arms addresses the first and neither of the others;
freezing the tree addresses the second and neither of the others. What all three would be caught
by is the thing none of them has: **a binding from an artifact to the run that produced it.** No
cloudcost artifact has ever carried one. Verified at agents `97c61a0` by grepping `run_id` across
every artifact on disk: zero hits in all three current `report_data_*.json` (aws and github
2026-08, linode 2026-07), zero in the per-provider `history/` snapshots, and zero in the oldest
surviving output — `cloudcost/output/do_costs_2026-07.json` and `do_inventory_2026-07.json`,
written 2026-07-29, so the gap is the whole life of the use case and not a recent regression.
A partial output directory is therefore indistinguishable from a complete one by content alone,
whichever way it got that way. That is
the argument, not the instance: this row's **Owes** already lists a provenance stamp as its third
shape and calls it *"the whole class rather than this arm"*, and the third mechanism is the case
that makes the other two shapes visibly insufficient rather than merely narrower. **It does not
widen this row's scope and proposes no fix**, and the ruling the row owes is still outstanding.
The cancel path's own defects — no process-group kill, no status transition — are **BL-154**, a
separate row because they are Rig-side and fire for any agent; this annotation is only about the
artifacts such a kill leaves behind. Verified at agents `97c61a0`.]`

**Owes:** a decision on arm ordering, which is a reviewer call rather than an obvious fix. At
least three shapes are defensible and they are not equivalent: clear the directory **before** the
credential preflight (a failed leg then leaves nothing, but a leg that fails for an unrelated
reason destroys the last good artifacts); keep the ordering and have the preflight's failure path
clear or stamp the directory (narrower, but duplicates the guard); or leave the ordering and make
the *staleness* visible instead — e.g. a provenance stamp written per run that a reader can check,
which addresses the whole class rather than this arm.
**Costs:** XS to reorder, S to stamp. **Do not take it as a reordering without ruling on the
destroy-the-last-good-artifact trade.**
**Collides with:** nothing in-repo. The clear is already scoped per provider (decision H), so any
fix stays within one provider's directory.

`[Ruled 2026-08-16 by the arbiter, on this row's Owes. THE ARM ORDERING IS NOT
CHANGED. Of the three shapes the row offers, the third is the fix; the first is
rejected; the second survives only in a form the third gives it.

NOT THE FIRST (clear before the preflight). It addresses one of this row's three
recorded mechanisms, and buys that with a destroy trade the row was right to
flag. The trade may be narrower than the row states — if the clear already
precedes the pipeline, every run that passes the preflight and dies later has
already destroyed the previous artifacts, which would confine the reorder's
marginal loss to preflight-stage failures. That is recorded here as an OPEN
QUESTION for the scoping ticket, not as a fact, and the ruling does not rest on
it in either direction: narrower is not zero.

NOT THE SECOND AS WRITTEN (the preflight's failure path clears or stamps). As a
duplicate clear it is what the row calls it — the same guard in two places, still
reaching one mechanism.

THE THIRD (bind an artifact to the run that produced it). It is the only shape all
three mechanisms reach, and it is what this row's own Contract line already names.
Reordering addresses the credential gate and neither of the others; freezing the
tree addresses inputs-changing-under-a-run and neither of the others; nothing
addresses a mid-flight kill except a directory that can state whether it is
complete.

WHAT THE RULING DOES NOT CLAIM. A provenance stamp does not by itself close the
credential-gate arm. On that path the survivors carry the PREVIOUS run's stamp,
which is internally coherent, so a reader with no independent handle on which run
they are asking about still cannot tell. Closing that arm needs the second shape
after all — but expressed in the stamp's vocabulary rather than as a second clear:
the preflight's failure path marks the directory as not-the-current-run instead of
deleting it. That is why the second shape is rejected in one form and retained in
the other.

TWO PROPERTIES THE IMPLEMENTATION OWES, both verification questions for the
scoping ticket rather than assertions here. The stamp must be written after every
artifact a run produces, so that an interrupted directory is UNSTAMPED rather than
stamped-and-partial. And the reader's rule must be that an unstamped or mismatched
directory is not a run, so that the ABSENCE of the stamp carries the meaning. A
stamp that can be written early, or that a reader is free to ignore, restores the
property it was added to remove.

WHERE THE STAMP LIVES IS NOT RULED, because it turns on facts nobody had read when
the ruling was made. If Rig's cancel path reaches cloudcost without going through
the harness sprint script, a stamp written by that script does not cover the
mechanism that made this row's subject visible. Scoping is blocked behind the
read-and-report filed as the ticket carrying this annotation; its findings belong
beside this ruling, not inside it.

Costs: the row's S stands for the stamp; the invalidation is additional and
unsized here. This is not licence to reorder.]`

`[Annotated 2026-08-16 at BL-153 s0 — the read-and-report the ruling above was blocked
behind. Its findings belong beside that ruling and are recorded here; the ruling block is
left exactly as written, being a record of what was believed at its date. Every line
below is verified at agents `900662f` / harness `d19f4b6` — the same harness commit this
row's own ordering was read at, unchanged since.

**R1 ANSWERED YES, and the ruling's OPEN QUESTION is closed.** The order is preflight
(`sprint.sh:2895-2932`) → guard (`sprint.sh:2944-2946`) → first writer
(`sprint.sh:3148-3151`, the orchestrator run), the guard roughly two hundred lines ahead
of anything that writes into `$CLOUDCOST_OUT`. Established by exhausting every mention of
that variable in the file: all of them after the guard are reads, and the four
`mix run --eval` checks between guard and run evaluate the agent file without running a
pipeline. So a run that passes the preflight and dies anywhere before the orchestrator has
**already destroyed the previous artifacts**, and the reorder's marginal loss is confined
to preflight-stage failures, exactly as the ruling conjectured. **This makes the reorder
cheaper than this row feared and does not revive it** — R2 is why: most of the mechanisms
never reach the sprint at all, so a cheaper sprint-side reorder still buys one of them.

**R2 ANSWERED NO, AND FOUND A FOURTH MECHANISM.** Rig does not reach cloudcost through
`sprint.sh`; the string appears nowhere in `rig/src` or `rig/src-tauri`. Two Rig paths
write into the provider directory and neither passes through the sprint. **The
Orchestrator**, whose child is what Cancel SIGKILLs: `mix run
$AETHERIS_AGENTS_PATH/agents/orchestrator.exs`, assembled at
`rig/src-tauri/src/commands/orchestrate.rs:45-50`, running an LLM planner whose agent
vocabulary is `docs/capability-matrix.md` — which lists cloudcost at `:198` — and which
loads the model's emitted path with no allowlist (`agents/orchestrator.exs:267-268, :287`)
and runs it **in-process**, inside the very child `orchestrate_cancel`
(`rig/src-tauri/src/commands/orchestrate.rs:149-159`) kills. **And the Tools panel**, which
this row did not previously know about: `python3 $AETHERIS_AGENTS_PATH/cloudcost/<file>
<args>`, assembled at `rig/src-tauri/src/commands/tools.rs:658-663`, running **one script**
rather than a pipeline, via `cmd.output()` at `:666`, never registered in the job map — so
it has **no cancel at all** and no pipeline ordering. A single stage run from that panel
writes into a directory whose other artifacts came from some other run entirely. That is a
fourth mechanism reaching this row's symptom, and unlike the third it needs no interruption
to produce a mixed directory.

**THE PLACEMENT QUESTION IS NOW RULED.** The ruling above left it open — *"WHERE THE STAMP
LIVES IS NOT RULED, because it turns on facts nobody had read"* — naming this read as what
it was waiting for. The read is done and the question is settled immediately below.

**R3 ANSWERED.** Completion is a single point in **execution order** on the default
configuration — STEP 4, `render_report.py` writing the HTML
(`cloudcost/scripts/render_report.py:378, :381`) — and **no point at all in the artifacts**:
nothing in the directory records that a STEP 4 was owed, so a directory missing the HTML is
indistinguishable from one whose pipeline never had that step. The last writer also **moves
with configuration** — with `--pdf` it is the PDF branch (`:261-285`), and STEP 2b's
`optimization_signals_*` file exists only under `CLOUDCOST_OPTIMIZATION`. And a complete run
writes **outside the guarded directory, at an earlier step**: `persist_history`
(`cloudcost/scripts/compose_report_data.py:974-991`) writes
`history/{provider}/{period}/` at STEP 3, a tree `sprint.sh:2944-2945`'s guard never clears
because the guard is scoped to `$CLOUDCOST_OUT`.

**R4 ANSWERED.** A per-run identifier exists upstream and reaches no script. The harness
carries `config.run_id` through every trajectory event
(`../aetheris/lib/aetheris/execution/loop.ex:183` and throughout) and it stops at the
exec-server boundary: the generic entry point passes an **empty env slice** —
`run_with_env(command, args, &[], working_dir, timeout_ms)`,
`../aetheris/native/aetheris_exec_server/src/runner.rs:46-48` — and the `run_command` tool
schema has **no env field** at all
(`../aetheris/lib/aetheris/execution/tool_schema/registry.ex:44-68` declares `command`,
`args`, `working_dir`, `timeout_ms`). Nor does it arrive by argv: the agent's arg arrays are
literal but for paths a previous step printed. Rig's own `job_id` is minted at
`rig/src-tauri/src/commands/orchestrate.rs:91-98`, **after** the child's environment is set
at `:56-65`, so it could not reach the child even in principle. The sprint reads the
harness's id at `sprint.sh:3401`, after the run has exited. This confirms the third
annotation's *zero artifacts carry a run_id* from the other end: nothing could have put one
there.

Record: `docs/milestones/bl-153-s0-implementation-notes.md`. Two of this row's own pointers
were imprecise and are corrected there rather than here.]`

`[Ruled 2026-08-16 by the arbiter, on the point the earlier ruling left open.
THE STAMP IS WRITTEN SCRIPT-SIDE, NOT BY THE SPRINT. R2 is the whole reason: two
Rig paths write into the provider directory without passing through the sprint at
all, so a sprint-written stamp is not merely absent on those paths — the previous
sprint run's stamp is still sitting there, internally coherent, and under this
ruling's own reader rule a Rig-written directory would read as a stale sprint
directory rather than as something to flag. A stamp that makes a new failure mode
indistinguishable from an old one is worse than no stamp.

THE IDENTIFIER IS MINTED BY THE PIPELINE, NOT INHERITED. R4 establishes that no
upstream identifier reaches a script, and that changing this means a harness
change at the exec-server boundary. A pipeline-minted id threaded stage to stage,
the way the period and the paths already are, needs no harness change. If a future
design does feed one through the sprint's environment instead, the sprint's
allow-list is default-deny and must name it, or the variable is stripped and the
stamp is silently absent — the exact shape the allow-list was built to make
impossible for credentials.

TWO PROPERTIES THIS RULING ADDS TO THE TWO ALREADY OWED. The stamp's coverage is
every artifact a run produces, INCLUDING the history tree written at an earlier
step into a directory the guard never clears — a stamp scoped to the guarded
directory alone would certify a subset while reading as certifying the run. And
the stamp needs a writer that runs LAST UNCONDITIONALLY; R3 establishes that no
current step is that, because the last writer moves with configuration. Whether
that writer is a new final step, the orchestrating agent, or something else is
NOT RULED.

WHAT IS STILL NOT RULED: the stamp's format, its file, and its reader. Those are
the scoping ticket's, and this row now has everything it was waiting for.]`

`Source: m6 t2c, 2026-08-13. Ordering read at harness d19f4b6; the reproduction above run at that
commit. Filed at the reviewer's direction rather than left as packet prose, per the standing rule
that a deferred finding gets a backlog row in the round it is deferred — and filed as its own row
rather than into BL-151, which is for defects that break nothing today.`

---

### BL-154 — Rig's Cancel kills the direct child only, and transitions nothing (#TBD)
**Kind:** defect · **Census items:** n/a · **Contract:** `../aetheris/CLAUDE.md` **Silent-wrong-answer** — *a mechanism that returns a well-formed value where a gap exists*
**Size:** M · **Priority:** medium
**Section:** aetheris-agents (`rig/`) — Rig-side, pre-cloudcost, fires for any agent

Filed 2026-08-14 at m6 t4, **the day it was found**, by a ticket that touches no Rig file.
Off-territory: m6 t4 edits three markdown files and one JSON overrides file, so nothing here is
attributable to the change under test. Found while establishing how the capability matrix reaches
Rig, not by looking for it.

**What the cancel path does.** `orchestrate_cancel`
(`rig/src-tauri/src/commands/orchestrate.rs:149-159`) takes the jobs lock, `remove`s the job from
state, and calls `job.child.lock().unwrap().kill()`. That is `std::process::Child::kill` — SIGKILL
to the **direct child only**. There is no process-group kill, no `SIGTERM` first, and **no write to
the protocol stream**: the agent is never told to stop, so it never emits
`orchestration_cancelled`, which is the message the UI's own state machine listens for
(`rig/src/hooks/useOrchestrator.ts:43-45`).

**Two independent frozen states. A fix for one does not fix the other, which is why both are
recorded here rather than one standing in for the pair.**

1. **The DB row.** The cancel path performs **no status transition at all**. It does not touch
   `runs.status`, and because the child is SIGKILLed it cannot run its own finalisation either, so
   any run the killed process had started stays `running`. This is not permanent — and the row
   says so rather than overstating it. `Aetheris.Sweep`
   (`../aetheris/lib/aetheris/sweep.ex`) cures orphaned `running` rows, and
   `config :aetheris, :sweep_on_start` is `true` (`../aetheris/config/config.exs:15`), so
   `Aetheris.Application` sweeps at every harness start
   (`../aetheris/lib/aetheris/application.ex:79-89`) and `mix aetheris sweep` runs it on demand.
   **The defect is what the cure then records.** With no terminal event in the trajectory the
   sweep takes the `orphaned` branch: it emits a `run_orphaned` event and sets `runs.status` to
   `failed`. So a run the operator deliberately cancelled is durably recorded as one that died
   unattended — the history cannot distinguish an intentional stop from a crash, and the
   distinction is not recoverable later because nothing wrote it down at the time. Until the next
   harness start the row also simply reads `running` for a process that is gone.

2. **The UI phase.** `cancel()` (`useOrchestrator.ts:107-110`) fires the invoke and then sets the
   phase to `cancelled` locally, on the assumption the kill succeeded — it does not await or check
   a result, and the invoke is `.catch(() => {})`, so a failed cancel is indistinguishable from a
   successful one. The polling effect early-returns on terminal phases
   (`useOrchestrator.ts:49-51`, `terminal = ['idle','done','cancelled','error']`), so the moment
   the phase flips no further `orchestrate_poll` runs. Every `stepStatuses` entry keeps whatever
   value it held, and the step that was executing renders its spinner **underneath the word
   "Cancelled."** (`OrchestratorView.tsx:379`, `:387`) — indefinitely, because nothing will ever
   update it. Fixing the DB half leaves this untouched; the view never reads `runs.status`.

**Not established, and named as such rather than assumed.** Whether OS descendants of the killed
child survive was **not** tested. The direct child is what `orchestrate_start` spawned; the
exec-server sandbox worker is a separate OS process reached over a Port, and a SIGKILLed BEAM
cannot run its normal port teardown, so an orphaned worker is *plausible* — but no run was killed
and no process table was inspected, so this row asserts only what was read from source. Anyone
disposing it should establish it before scoping a process-group fix around it.

**Done when:** cancelling a run from Rig leaves a record that says it was cancelled — a terminal
event and a `runs.status` distinguishable from both `running` and an unattended `failed` — and the
UI reflects the actual end state of the steps rather than freezing them; **or** it is ruled that
`failed`-by-sweep is the intended record for a cancel, in which case the sweep's own
`run_orphaned` framing is corrected to say so and the UI half is still owed. **Not** when only one
of the two frozen states is addressed.

**Costs:** M. The terminal write is small; deciding the status vocabulary is the real work, and it
is a harness question (`runs.status` and the trajectory's terminal event set are harness-owned)
reached through a Rig defect, so it is **cross-repo by consequence** even though the broken code
is Rig's. The UI half is S on its own.

**Collides with:** **BL-153**, whose third mechanism is the artifacts a killed run leaves behind —
annotated there, deliberately not folded in here, because that row is about artifact trust and
this one is about the cancel path itself.

`Source: m6 t4, 2026-08-14. Read at agents 97c61a0; every citation above is a line read, not a
shape inferred from a neighbour. Originally surfaced in the m6 t4 read-and-report packet as one
finding covering both frozen states; split into the two numbered items above because they have
disjoint fixes. The packet's "permanently" is corrected here against the sweep, which the packet
did not account for.`

---

### BL-155 — the capability matrix has three consumers, no gate, and is the one wiring place an LLM writes (#TBD)
**Kind:** defect · **Census items:** n/a · **Contract:** `../aetheris/CLAUDE.md` **Silent-wrong-answer** — *"An LLM computing a value inside a generated artifact nobody recounts"* (the D3 / BL-067 carrier)
**Size:** M · **Priority:** medium-high
**Section:** aetheris-agents (`docs/`, `scripts/`, `rig/`)

Filed 2026-08-14 at m6 t4, by the ticket that had to regenerate the matrix because provider four
was missing from it. **BL-090 is both the precedent and the recurrence** — it was
*"capability-matrix stale: cloudcost omits detect_optimization_signals"*, filed 2026-08-03 and
closed 2026-08-05 by regenerating, without adding the regen to `cloudcost/runbook.md` §Adding a
provider's wiring list. Provider four then landed 2026-08-13 and the document went stale in
exactly the same cell. m6 t4 added the regen to that list; **this row is the part a list entry
cannot fix.**

**Three consumers, one artefact.**

1. **Rig's Agents catalogue.** `rig/src/modules/registry.ts:11` labels the route "Agents";
   `rig/src/App.tsx:67-69` routes it to `CapabilityMatrixView`, which loads via
   `capability_matrix_load` (`rig/src-tauri/src/commands/capability_matrix.rs:29-42`) — a
   hand-rolled markdown table parser (`:44-125`) over `docs/capability-matrix.md`.
2. **Rig's launch prefill.** `CapabilityMatrixView.tsx:124` navigates to `/orchestrator` with
   `prefill: \`${agent.label}: \``, so column 2 of a markdown table becomes the opening text of an
   operator's request.
3. **The planner LLM's system prompt.** `agents/orchestrator.exs:17-18` reads the file with
   `File.read!` and `:34` interpolates it whole into the system prompt; `:54-55` then instructs
   the planner that agent paths *"must match exactly the file paths listed in the capability
   matrix"*. A script absent from the matrix is a script the planner cannot plan.

**No gate.** `grep -n "capability" scripts/drift_check.py` returns nothing at agents `97c61a0` —
none of checks 1–8 reads this file. Positive control for that negative: the same `grep -n` for
`manifest` over the same file returns its `project_knowledge` check, so the pattern and the path
are working and the zero is a real absence. There is no test either: `tests/test_assemble_matrix.py`
covers the **assembler**, which is deterministic and was made trustworthy by BL-067, and asserts
nothing about whether the sections it assembles describe the tree.

**And it is the only wiring place that is LLM-generated rather than hand-edited.** Every other
entry on the §Adding a provider list is a human editing a file. This one is nine
`agents/capability_matrix_*.exs` section agents writing `docs/.sections/*.md`, which are
gitignored scratch. That is not a stylistic difference — **the generator is not stable, and m6 t4
measured it.** Three regenerations of the cloudcost section over an unchanged tree produced three
different agent labels: `Cloudcost · {provider}` (committed, `4d98ec2`, m3 t3),
`Cloudcost Orchestrator` (run `cap-matrix-cloudcost-fEUkDw`), and
`Cloudcost · DigitalOcean, AWS, Linode, GitHub` (run `cap-matrix-cloudcost-vcUTlA`) — plus a full
rewording of all nine script purposes on each run. The first of those three is the one that
mattered: `{provider}` is not Elixir syntax, it is a section agent's paraphrase of
`cloudcost_orchestrator.exs:336`'s `"Cloudcost · #{provider_name}"`, and it was rendered raw in
consumer 1 and fed verbatim into consumers 2 and 3 for nine days. **So a regen is not only the
cure for staleness; it is itself an uncontrolled write to all three consumers.** m6 t4 pinned that
one cell through `docs/capability-matrix-overrides.json` (BL-068's mechanism, verified to survive
a regen by observation rather than by reading), which fixes the cell and not the class.

`docs/capability-matrix-runbook.md:79-80` **said** *"Two runs over unchanged sections produce
byte-identical output, so a matrix diff only ever shows a real change."* That was true of the
**assembler** and it was the sentence a reader would take as covering the ritual. It does not
cover the section step, and the measurements above are the counter-example.
`[Corrected 2026-08-14 at m6 t4's review, by a Touches widening the reviewer ruled: that sentence
is what a reader consults before deciding whether a matrix diff needs scrutiny, and a backlog row
does not reach someone who reads the guarantee and never the backlog. The file now states that the
assembler is deterministic over unchanged sections and the section step is not. **This row is
unaffected otherwise** — the false guarantee was corroboration, never the defect. The defect is
the instability itself, and it is still open.]`

**A drift check is the obvious candidate — this row does not design it, deliberately.** The
question is not only *whether* to check but *what is checkable*: file existence and row counts
are mechanical, prose purposes are not, and a check that only counts rows would have caught
BL-090 and this recurrence while never touching the `{provider}` cell. That trade is the row's to
decide, not this filing's.

**A stated unknown, recorded because it is this row's subject and nobody has looked.** m6 t4
regenerated **one** of nine sections, by ruling, for diff attributability. cloudcost's section was
stale for nine days with no gate; the other eight — payslip, drive, email, api/tenant,
api/gateway, provenance, docbuilder, eduloka — have the identical structural exposure and **have
not been checked against their source trees**. The whole-file assembly was verified byte-identical
to the committed matrix before the regen, which establishes that the on-disk sections match the
committed document; it establishes nothing about whether either matches the code. Eight sections
are therefore of unknown accuracy, and the last full regen was `4d98ec2`, 2026-08-05.

**Done when:** a stale or wrong capability matrix is caught by something other than a person
noticing — with the mechanism's own blind spots named, since a row-existence check and a
cell-content check are different instruments and the first does not imply the second; **or** it is
ruled that the matrix is not gate-worthy, with that ruling recorded and the three consumers
documented as reading an unchecked artefact. **Not** when the current staleness is merely
regenerated again — that is what BL-090 did.

**Costs:** S for an existence/count check in `scripts/drift_check.py` (the file walk already
exists for other checks). M–L for anything reaching cell content, and that is where the design
question is.

**Collides with:** the §Adding a provider wiring list (m6 t4 added the regen there, so the
procedural half is closed and this row is the mechanical half); **BL-068**, whose overrides file is
the only durable surface for a cell that must not be reworded, and which any content check must
read before flagging a cell.

`Source: m6 t4, 2026-08-14. Measured at agents 97c61a0. The three-way label divergence is this
ticket's own observation from two live regens plus the committed baseline, not a reconstruction —
the run ids are given so it is reproducible. BL-090's history read from
docs/backlog-2026-06.md:3742-3794. Filed rather than left in the packet, per the standing rule
that a deferred finding gets a backlog row in the round it is deferred.`

---

### BL-156 — the approval card's step text is written by the planner per run, and nothing checks it (#TBD)
**Kind:** defect · **Census items:** n/a · **Contract:** `../aetheris/CLAUDE.md` **Every claim has a truth-maker**
**Size:** M · **Priority:** medium
**Section:** aetheris-agents (`rig/`, `agents/orchestrator.exs`) — generic to every planner-launched agent

Filed 2026-08-14 at m6 t4. **Filed as its own row rather than appended to an existing one**, and
the ground is stated because the ticket left the choice open. No row owns approval-surface
*content*. **BL-094** owns the *door* — a direct, non-LLM launch path — and closing it removes the
plan card for the agents that move to that path while leaving this defect untouched for every
launch that still goes through the planner. **BL-085** owns credentials and per-launch provider
selection. **BL-151** is for defects that break nothing today, and this one can mislead an
operator into approving a run. So it belongs to none of them.

**What the surface is.** The plan card an operator reads before pressing Approve renders two
fields per step: `step.description` as the card's headline (`OrchestratorView.tsx:105`) and
`step.context` beneath it in italics (`:107-108`). Both are authored by the planner LLM, per run,
from the output contract at `agents/orchestrator.exs:44-47` — `description` is *"What this step
does"* and `context` is *"One sentence with specific runtime details — what data, which month,
where output goes"* (`:46`). The prompt asks the model to *"Use the request params and your
knowledge of the agent to be specific"* (`:57-58`).

**So the text an operator approves against exists in neither repo.** It is not in the agent file,
not in `tools.json`, not in the capability matrix, not in any template. It is generated fresh on
every run and never persisted anywhere a reviewer could inspect it. Grepping either repo for a
phrase an operator saw on the card finds nothing, because the phrase was authored at request time.

**No test covers it.** There is no assertion anywhere on plan-card content — not on the shape of
`description`/`context`, not on their agreement with the agent they describe, not on the agent
path in the same step being one the matrix lists. The only structural constraint is the JSON shape
`orchestrator.exs:212-220` decodes, which is satisfied by any two strings.

**And the observed instance was wrong in the way that matters.** The card asserted a **scope** the
cloudcost design forbids: `cloudcost/m6-github.md` decision H fixes **one provider per run** — the
provider is chosen at eval time and the run fetches, detects, composes and renders for that
provider alone, so two providers are two runs and two reports. The step text asserted otherwise.
Nothing downstream contradicted it: the run then did the correct, decision-H thing, and the
operator's basis for approving was a sentence about a different pipeline. That is the failure
shape — **the card is the only place a run is described in words before it is authorised, and it
is the one place with no truth-maker.**

**This is not a cloudcost defect.** cloudcost is where it was observed, because decision H is an
unusually crisp constraint to contradict. Any agent whose real behaviour is narrower than a
plausible-sounding description is exposed identically, and the more deterministic the pipeline the
more confidently the planner will describe it.

**Done when:** the text on the approval card is either derived from something checkable — the
agent's own manifest description, its matrix row, a per-agent template — or it is labelled on the
card as model-generated and unverified, so an operator knows what they are reading. **Not** when
the prompt is merely told to be more careful; a prompt instruction has no truth-maker either.

**Costs:** M. The cheap half is the label, which is XS and buys most of the safety. Deriving the
text from a checkable source is the real work and overlaps **BL-094** — a direct door would render
its own step text from the manifest and would want exactly this.

**Collides with:** **BL-094** (a direct door renders a different card, so sequencing matters and
neither should be designed without the other); **BL-085**, whose annotation records that the
planner has never been told any cloudcost key exists — the same planner, the same prompt, the
other end of the same gap.

`Source: m6 t4, 2026-08-14. Read at agents 97c61a0; OrchestratorView.tsx and orchestrator.exs
citations are lines read. The observed wrong-scope instance is reported from the m6 t4
read-and-report packet's account of a live Rig run — it is **not reconstructible from the tree**,
because plan-card text is not persisted, and that irreproducibility is itself the finding rather
than a weakness in it.`

**Appended 2026-08-14 at the m6 close — a second observed instance, on this row's first day, and
this one has a tree-checkable half.** *(Appended below the row's own `Source:` stamp, not between
it and the body it attributes.)* The operator's click-through discharging m6 t4's outstanding Rig
gate passed both its legs and, while passing, read an approval card claiming the run *"detects
orphans and optimization signals"* — on a **GitHub** run. The claim is wrong twice over, and the
second half was checked at HEAD rather than relayed:
`cloudcost/scripts/detect_optimization_signals.py:1-13` is scoped to *"AWS S3 / ECR / Secrets
Manager"*, so it cannot run on GitHub at all; and its own docstring records **decision G** — *"the
core pipeline never reads it"* — so **no provider's pipeline invokes it**, and the card would be
wrong on an AWS run too. The card names a capability the pipeline does not have, rather than one
it has for a different provider.

**Why this strengthens the row rather than merely repeating it.** The first instance was recorded
as not reconstructible from the tree, because plan-card text is not persisted — true of the card,
and the honest limit. This instance shows the *other* end is reconstructible: the claim's falsity
is a two-line read of a committed docstring. So a check does not need the card's history to exist.
It needs the card's claims to be derivable from something that does — which is what the Done-when
above already asks for.

`Source: the m6 close, 2026-08-14. Read at agents e0c1ee2. The card text is the operator's account
of a live Rig run and is not reconstructible from the tree, as above; the AWS scoping and the
decision-G exclusion are lines read in this session. Appended per the standing rule that a live
instance of an open row's class appends to that row rather than opening another.`

---

### BL-157 — the bare module name `conftest` is a standing trap, and it is held open by an absence (#TBD)
**Kind:** defect · **Census items:** n/a · **Contract:** `../aetheris/CLAUDE.md` **Silent-wrong-answer**; `CLAUDE.md` (agents) §Definition of done — *the Python whole-suite gate*
**Size:** S · **Priority:** medium
**Section:** test apparatus (agents)

Filed 2026-08-16 at BL-152's amendment, **the day it fired**. Established at agents `2868a3e`.

**What is there.** Ten lines across eight modules under `cloudcost/tests/` import the bare module
name `conftest` at runtime — `from conftest import FIXTURES, USE_CASE_ROOT, load_fixture` and
similar, two of them *inside test bodies* rather than at module level. These resolve through
`sys.path` when the line executes, not through pytest's collection machinery, which is why
**`--import-mode=importlib` does not cover them**: importlib mode changes how *pytest* names and
imports test and conftest modules, and has no bearing on an `import` statement written in test
code. The resolution works because `cloudcost/tests/conftest.py` inserts its own directory at
`sys.path[0]`.

**Why it is a trap rather than a wart.** It works today **only because no `conftest.py` exists at
the repository root**. pytest imports a rootdir `conftest.py` under the bare module name
`conftest`; the moment one exists, these ten lines can resolve to it instead. Nothing checks that
absence. It is not documented as load-bearing anywhere except in `pytest.ini`'s comment block,
added by the same ticket that discovered it, and a comment is not a check.

**It is not hypothetical: BL-152 violated it for two runs.** That ticket's first implementation put
the gate's deselection-reporting hooks in a new root `conftest.py`. The gate then reported a green
suite twice while two tests were failing, and the failure was invisible in any scoped run —
`cloudcost/tests` alone was 464 passed, and the two tests run alone passed. Only the whole-tree
run showed it:

```
E       ImportError: cannot import name 'CLOUDCOST_ACCESS_KEY' from 'conftest' (~/sandbox/elixirws/aetheris-agents/conftest.py)
cloudcost/tests/test_compose_report_data.py:888: ImportError
cloudcost/tests/test_detect_orphans.py:898: ImportError
```

BL-152 resolved it for itself by deleting the root `conftest.py` and moving the hooks into
`tests/conftest.py`. That removes the instance and leaves the trap.

**The reachability is ordinary, not exotic.** A root `conftest.py` is the first thing anyone
reaches for to add a repo-wide fixture, a session hook, a `pytest_addoption`, or reporting of the
kind BL-152 needed. The next person to want one will not know this costs two cloudcost tests, and
the symptom they will see is a green gate.

**Done when:** the absence is either enforced or removed as a dependency, and which of those is
**not decided here**. A test asserting no root `conftest.py` exists, a change to the ten call
sites so they do not import a bare top-level name, a package-qualified import, a fixture-based
replacement, and "document it and accept it" are all on the table; none is endorsed. What the row
requires is that the decision be made and recorded, not that any particular one be taken.

**Costs:** S to decide. The call-site change is mechanical but touches eight test modules; the
guard-test option is minutes. Whoever takes it should check whether use cases other than
`cloudcost` have the same pattern — **BL-152 established only that cloudcost does**, by a grep it
ran for its own purposes, and did not sweep for near-variants.

`Source: BL-152's amendment, 2026-08-16. The ImportError block above is transcribed from that
ticket's own failing run and is the row's evidence; the ten call sites were enumerated by
`grep -rn "^\s*\(from conftest import\|import conftest\)" --include=*.py .` at agents `2868a3e`.
Filed rather than left in the packet, per the standing rule that prose in a packet or notes files
nothing.`

---

### BL-158 — the pre-existing `integration` population has never been audited against the criterion the gate now uses (#TBD)
**Kind:** gate · **Census items:** n/a · **Contract:** `CLAUDE.md` (agents) §Definition of done — *the Python whole-suite gate*; Ruling 2 of BL-152's ticket text
**Size:** M · **Priority:** medium
**Section:** test apparatus (agents)

Filed 2026-08-16 at BL-152's amendment. Established at agents `2868a3e`.

**The consequence, stated plainly.** BL-152 made `@pytest.mark.integration` load-bearing: it is now
one of the two things that removes a test from the whole-suite gate. It also wrote down, for the
first time, what the marker asserts. **The marks it applied that criterion to are the ten it added
itself.** The other 159 predate the criterion by months and were applied under no stated rule at
all. So the repo now **excludes tests from its gate on the strength of marks that were never
checked against the reason the exclusion exists.**

**The figures, verified rather than estimated** (agents `2868a3e`):

| | count |
|---|---:|
| `@pytest.mark.integration` decorators in the tree | **169** |
| of those, added by BL-152 and checked against the criterion | 10 |
| of those, **pre-existing and unaudited** | **159** |
| integration-marked tests the gate deselects (`integration and not dormant`) | 112 |
| integration-marked tests the dormant set absorbs (boxy-pipeline) | 57 |

The 169 reconciles with collection exactly: `-m integration --collect-only` reports
`169/1714 tests collected`. A grep for the literal string returns 171; the two extra are prose
mentions inside module docstrings at `eduloka/tests/test_upsert.py:3` and
`tests/test_drift_check.py:5`, not decorators. **Of the 159 unaudited marks, 105 are deselected by
the gate today and 54 are inside the dormant set**, so the dormant half is not urgent and the
other half is what a gate currently skips on unexamined grounds.

**The cheap half is already done and came back clean.** BL-152's amendment added
`--strict-markers` to `pytest.ini`'s `addopts`. Whole-tree collection is clean under it —
`1714 tests collected`, exit 0 — so **every mark in the tree is registered**; there is no typo'd
or unknown marker anywhere. **That is a syntactic result and settles nothing here.** A mark can be
perfectly registered and still be on a test that would run fine in a fresh clone. The audit this
row names is semantic and no tool performs it.

**The criterion to audit against**, as `pytest.ini` now states it: *the test's outcome depends on
state that is not in this repository at the commit under test* — would it do its work and pass in
a fresh clone at this commit, offline, with no sibling repository present? Fail, error or **silent
skip** all mean yes. A subprocess against a tracked script in this repo does not, however many it
spawns.

**What is NOT known.** Whether any of the 159 fails the criterion; if so how many, and in which
direction. **Both directions are open** and the row does not assume the interesting one is
over-marking: a test that *should* carry the mark and does not is the worse defect, because it
puts out-of-repo dependence inside the gate, and BL-152 found exactly three of those in
`boxy-pipeline/tests/test_plan_extractor.py` — four siblings with an identical guard were marked
and three were not. A whole-repo sweep for that shape has not been run.

**Done when:** the 159 have been read against the criterion and the result recorded — each either
confirmed, or reported as not meeting it — and the reverse sweep for unmarked tests that should
carry it has been run once over the whole tree. **Not** when a tool passes; no tool decides this.
Per Ruling 1, a mark found to be wrong is **reported**, not silently corrected, and a red test
found by removing a mark stays red.

**Costs:** M. 159 marks across roughly two dozen files, each a short read. The reverse sweep is the
larger half and has no shortcut, though `pytest.skip(` and `shutil.which(` call sites are a
reasonable starting population — that is how BL-152 found its three.

`Source: BL-152's amendment, 2026-08-16, from that ticket's own §12 UNREAD — *"I did not audit the
159 pre-existing marks against the criterion now written in pytest.ini; I checked the other
direction"*. Figures re-verified here rather than carried from that packet. Filed rather than left
in the packet, per the standing rule that prose in a packet or notes files nothing.`

---

### BL-159 — what the dormant set owes when boxy-pipeline resumes (#TBD)
**Kind:** gate · **Census items:** n/a · **Contract:** `pytest.ini` — the `dormant` marker's stated condition for return; `CLAUDE.md` (agents) §Definition of done
**Size:** M · **Priority:** low until boxy-pipeline resumes, then blocking
**Section:** test apparatus (agents) — `boxy-pipeline/`

Filed 2026-08-16 at BL-152's amendment. Established at agents `2868a3e`.

**This row is the other half of a return condition.** `pytest.ini` says **how** to un-pause
boxy-pipeline — *delete the `pytestmark = pytest.mark.dormant` lines from
`boxy-pipeline/tests/test_*.py`; nothing else was changed for the pause*. It does not say what
un-pausing will find, and a condition for return that hides its own cost is one somebody will
satisfy by accident. This row is that cost. **The two must be read together**: the marker's
comment block in `pytest.ini` points at the mechanism, this row points at the consequence.

**208 tests are dormant**, all of `boxy-pipeline/tests/`, deselected from the gate since
2026-08-16 while still collecting and still importing. Restoring them puts all 208 back into
`python3 -m pytest -q -m "not integration and not dormant"`. Three things are known about what
that costs, and one important thing is not.

**1. It does not terminate usefully.** Two capped runs, both killed deliberately, neither
finishing:

| run | cap | outcome |
|---|---|---|
| `python3 -m pytest -q -m integration` (before the marker split; boxy is most of it) | 2700s | killed at **52m21s**, 37 of 169 results emitted |
| `python3 -m pytest -m integration boxy-pipeline -v` | 2400s | killed at **10m17s**, 21 of 57 results emitted |

Projected from the observed rate the boxy set needs **roughly four hours**. The projection is a
projection and is labelled as one. The first run stalled at
`boxy-pipeline/tests/test_pipeline.py::test_plan_path_produces_same_output_as_drawings_path`,
which `subprocess.run`s `boxy-pipeline/scripts/plan_extractor.py` against two sample PDFs — the
same shape BL-152's row described before any of this was fixed, so this is a **third independent
observation** of it, not a new symptom.

**2. At least one test is red, and was left red deliberately.**
`boxy-pipeline/tests/test_catalog_resolver_refactor.py::test_real_jsonl_resolve_matches_excel_result`
**FAILED**. Per Ruling 1 it was reported and not fixed, and it is **not** deselected for failing —
it is deselected because the use case is dormant, and it will be red again the moment the
`pytestmark` lines come out.

**3. At least one further failure exists and is NOT identified.** The merged run's progress stream
was `ssssssss................F....F......` — two failures. The verbose run that would have named
the second was cap-killed before reaching it. Its position is consistent with
`boxy-pipeline/tests/test_order_formatter.py`, and **that is an inference, deliberately not
recorded as a fact and deliberately not resolved**: naming it by counting dots is exactly the kind
of claim that later gets cited as established. Whoever resumes boxy-pipeline will find it by
running the set.

**And the whole set depends on data no clone carries.** `boxy-pipeline/data/samples/*.pdf` are
gitignored client files (`boxy-pipeline/.gitignore:2`, `data/*`); `git ls-files
boxy-pipeline/data/samples/` is empty. On a machine without them every sample-dependent test
skips, so **the four-hour figure and both failures are only reachable where the client data is
present.** A resumption on a fresh machine will look fast and green for the wrong reason.

**Done when:** boxy-pipeline's work resumes and, before the `pytestmark` lines are removed, the
set has been run to completion once under a cap large enough to finish, its true duration recorded,
every failure identified by name, and a decision taken on whether the set can be part of the gate
at that duration or needs splitting. If boxy-pipeline is retired rather than resumed, this row
closes on that instead — and the 208 tests' fate is stated in the same decision.

**Costs:** M, and mostly wall-clock rather than attention. Not payable until the use case is
active; attempting it before then spends four hours to learn about a paused pipeline.

`Source: BL-152, 2026-08-16, and its amendment. The two capped runs are that ticket's own,
recorded per the cap correction that a cap-kill is a complete result rather than a check still
owed. The named red and the unidentified second failure are transcribed from those runs. Filed
rather than left in the packet, per the standing rule that prose in a packet or notes files
nothing.`

---

### BL-160 — the U2 export gate has never returned information in either direction (#TBD)
**Kind:** gate · **Census items:** n/a · **Contract:** `cloudcost/docs/m6-t2-implementation-notes.md` §U2 — the scrub class, defined rather than enumerated; `CLAUDE.md` (agents) §Definition of done — the export mechanism
**Size:** M · **Priority:** medium
**Section:** process / project knowledge (`scripts/assemble_export_bundle.py`, `scripts/u2_patterns.txt`)

Filed 2026-08-16 at the export boundary's amendment pass. Established at agents `a2df7b5`.

**What is known, and it is the whole of the finding.** The U2 sweep is supposed to stand between
the export bundle and the project store. Until this row it could not, and the reason is not a bug
in the sweep — it is that **the sweep had no corpus from which its inputs could be derived**.

`assemble_export_bundle.py --needles FILE` takes a list of literal identifiers and greps the
bundle for them. It ships with none by design: a committed needle list is itself the
deanonymisation key the sweep exists to protect against. So the needles must be derived at run
time, and the only material on this machine to derive them from is
`cloudcost/output|history|data`. **That material cannot yield them.** Its 27 JSON files are
*normalized adapter output* — the two-schema contract's shape — whose key space is `amount`,
`type`, `invoice_uuid`, `date`, `description`, `resource_id`, `region`, `tags`, `service`,
`provider`, `name`, `account`, `created_at`, `last_activity_at`, and so on. **Not one** of the
class's named identity fields appears anywhere in them: no `login`, no `organization`, no
`organizationName`, no `repositoryName`, no `node_id`, no `avatar_url`, no `html_url`, no `email`.
The raw unscrubbed captures that §U2's own verification drew twenty-one identifiers from are not
in this repo and are not on this machine, and nothing in either repo says where they are or who
holds them.

**So a sweep derived from what is here cannot find the class it searches for, and its green is a
statement about the derivation rather than about the bundle.** Demonstrated at the boundary that
filed this row: needles restricted to the class as defined produced **one** needle over 27 files,
swept, and returned `[PASS] 1 needle(s), no hit`. That PASS is worth nothing. A wider net over the
same files produced 94 needles and three hits, all adjudicated **not in class** (R-F1 below) — so
that run was not the gate firing either. **The gate has never returned information in either
direction.**

**And this was true at every prior boundary, including the one that uploaded.** The mechanism
landed 2026-08-16; before it, the sweep was a step in
`prompts/bl-002-refresh-project-knowledge.md` performed by hand from the same absent corpus. No
boundary record claims a U2 sweep found anything, and none claims one was run against a corpus
that could have. **Nothing detected this, and nothing could have**: a sweep that cannot see the
class returns exactly what a clean bundle returns, which is the **Silent-wrong-answer** shape in
its purest form — *a check that cannot observe the failure it stands in for returns green for the
wrong reason* (`../aetheris/CLAUDE.md`). There was no positive control, because a positive control
needs a corpus too.

**The direction ruled, and what has already landed.** The arbiter ruled at this amendment that
**the sweep searches the class by pattern, not by value.** A needle list is a deanonymisation key
— which is why it cannot be committed, why the boundary's was shredded, and why the gate was
runnable only by someone holding captures nothing locates. **A pattern set is not disclosure**: it
commits, it runs anywhere, and it removes the raw-capture dependency entirely. **It lands in the
next commit of this same pass**, not in this one — `scripts/u2_patterns.txt`, read by the assembler
by default, one documented pattern per line naming the class member it covers, with `--needles`
surviving beside it as an additive value sweep for an operator who *does* hold captures. Stated as
forward here rather than asserted: at this row's commit the file does not exist yet.

**What is NOT known, and this row owns all three.**

1. **Whether pattern-sweeping is sufficient.** It is a different instrument, not a stronger one.
   It answers *does this bundle carry text shaped like the class* — never *does this bundle carry
   this account's identifiers*. Those questions have different answers and the second is the one
   §U2 asks.
2. **What it can miss, stated concretely rather than as a caveat.** The class's core members have
   **no lexical signature at all**: a login, a display name, an organisation name and a repository
   name are ordinary words, and a numeric user or organisation id is an ordinary number. A pattern
   set reaches them only *contextually* — adjacent to a key that names them, as in pasted JSON —
   so a leak in prose (*"the account belongs to …"*) is invisible to it and would have been visible
   to a value sweep with real needles. The under-reach enumeration is in this cycle's packet and in
   `scripts/u2_patterns.txt`'s header.
3. **Whether a raw-capture corpus should exist at all.** Keeping unscrubbed captures on disk so a
   value sweep can be derived from them creates the exposure the sweep exists to limit; not keeping
   them means the value sweep can never run again. This row does not choose. Note the choice is not
   free in either direction and that the status quo — no corpus, and a gate that reads as armed —
   is the one option that has been ruled out by this row's existence.

**Done when:** a decision is recorded on (3), and (1) and (2) are answered against whatever that
decision makes possible — either the pattern set is ruled sufficient with its under-reach accepted
in writing, or a corpus and its custody are defined and the value sweep is restored beside it.
Either branch must state what the gate then claims, in the narrow words rather than the broad ones:
a clean pattern sweep claims *no text matching these patterns*, never *no identifying content*.

**Costs:** M. The implementation half is done. What remains is a decision with a security shape
and no obviously right answer, which is why it is filed rather than settled here.

**Collides with:** **BL-143**, which asks who owns the export boundary and on what trigger. This row
is the same boundary's *other* unowned half — BL-143 asks whether the boundary runs, this asks
whether its one safety check means anything when it does. Neither answers the other and both should
be read by whoever takes either.

`Source: the export boundary of 2026-08-16 and its amendment pass. The 27-file key-space
enumeration, the one-needle result and the 94-needle result are that boundary's own, carried
verbatim from its packet §F2 rather than re-derived. The direction in the fourth paragraph is the
arbiter's ruling R-F2 at the amendment. Filed rather than left in the packet, per the standing rule
that prose in a packet or notes files nothing — the same rule BL-161 records being breached.`

---

### BL-161 — the export-mechanism round deferred a sprint arm and filed no row (#TBD)
**Kind:** process · **Census items:** n/a · **Contract:** `CLAUDE.md` (agents) §Learning — BL-007 — *a deferred finding gets a backlog row in the same round it's deferred*
**Size:** S · **Priority:** medium
**Section:** process / backlog discipline; the arm itself is harness (`../aetheris/scripts/sprint.sh`)

Filed 2026-08-16 at the export boundary's amendment pass. Established at agents `a2df7b5`.

**What happened.** The export-mechanism round (agents `5dae22b`, 2026-08-16) shipped
`scripts/repin_manifest.py` and `scripts/assemble_export_bundle.py` with tests and a runbook
pointer, and recorded in its notes that one companion could not land
(`docs/milestones/export-mechanism-implementation-notes.md`):

> **One companion is owed and cannot land here: a sprint case.** Both comparators have one
> (`sprint.sh` `capability_matrix` and `drift_check`, `aetheris/scripts/sprint.sh:1533` and
> `:1594`). `sprint.sh` lives in the harness, which this ticket's REPOS clause puts out of bounds,
> so the export mechanism ships with tests and no sprint arm. Reported rather than quietly
> dropped; it is a gap for whoever takes BL-143, not a defect this ticket may fix.

The reasoning is sound and the deferral is correct. **The record is not.** That round's commits
touched `CLAUDE.md` and never `docs/backlog-2026-06.md`, and **BL-143's row does not mention a
sprint arm** — so the sentence *"it is a gap for whoever takes BL-143"* addresses a reader who has
no way to receive it. Whoever takes BL-143 opens BL-143.

**The rule it breaches** is `CLAUDE.md` §Learning — BL-007: *a deferred finding gets a backlog row
in the same round it's deferred — prose in a packet or notes files nothing.* The same entry's
closing clause is why naming BL-143 was not enough: a finding recorded somewhere that does not
carry an executor *"has a record, not an executor"*.

**The breach was recoverable only by accident, and that is the part worth keeping.** The notes file
is committed and attributed, so the deferral survives in a readable form — that is the *only*
reason this row can be written at all. But nothing was going to read it. It surfaced because the
2026-08-16 export boundary's content sweep **wandered past its own scope**: that sweep was
chartered to find closures and rulings missing from tracked files, a sprint arm is neither, and it
was found by a session reading the round's notes for something else and noticing. A discipline that
depends on the next session being curious about a file it had no reason to open is not a discipline.

**Whose omission this is.** The arbiter's, stated so the record is not silently flattering: the
export-mechanism packet was approved and its §8 ruled against, without noticing that a deferred
companion had no row.

**What is actually owed, kept small.** A `sprint.sh` case exercising the two export scripts, beside
the `capability_matrix` and `drift_check` cases it would sit with. It is a harness write, so it
needs a cross-repo ticket; nothing about it is difficult, and it has been unowned since 2026-08-16.

**Done when:** either the sprint arm exists and is named in a boundary record, or a ruling is
recorded that the export mechanism's tests are sufficient and no sprint case is owed — with the
reason, in `CLAUDE.md` §Definition of done beside the mechanism's pointer, where a reader of that
pointer will meet it.

**Costs:** S. The arm is a few lines against two scripts that already exit non-zero on failure.

**Collides with:** **BL-143**, which the notes file named as the inheriting row and which does not
know it. Closing this row's first branch is naturally part of BL-143's work; closing its second
branch is not, and does not wait for it.

`[Annotated 2026-08-16 at BL-143's close. The **Collides with** above states, in passing, a shape
that is now filed as a finding in its own right: a document named BL-143 as the inheriting row and
BL-143 *"does not know it."* That is one of **BL-162**'s two instances — the other is the
check-1/check-3 contradiction, routed to the same row by two further documents and equally invisible
from it — and BL-162 owns the question of what a citing document owes its target. **This row is
unchanged by that filing:** the sprint arm is still owed here, both branches of its Done-when stand
as written, and BL-162 closes neither.]`

`Source: the export boundary of 2026-08-16, packet §F4, and the amendment pass that filed it. The
quoted paragraph is transcribed from `docs/milestones/export-mechanism-implementation-notes.md`
at agents `a2df7b5`. The attribution of the omission is the arbiter's own, given at the amendment.`

---

### BL-162 — an inbound pointer is not a scope change, and nothing tells the row (#TBD)
**Kind:** decision · **Census items:** n/a · **Contract:** n/a
**Size:** S to decide · **Priority:** medium
**Section:** process / backlog discipline (`docs/backlog-2026-06.md`, and any document that cites a
row)

Filed 2026-08-16 at BL-143's close, in the round that surfaced it. Established at agents `84c24c7`.
**This row poses the question; it does not settle it.**

**What is established.** BL-143's text asks **one** question — who owns the export-boundary refresh
and by what trigger — and the check-1/check-3 contradiction and the vocabulary gap appear nowhere in
it. Measured over the row's own range at `9741c4e`, the commit before the ruling landed:

```
$ git show 9741c4e:docs/backlog-2026-06.md | sed -n '8494,8555p' | grep -cEi "check 1|check 3|vocabulary|namespace"
0
$ git show 9741c4e:docs/backlog-2026-06.md | grep -cEi "check 1|check 3|vocabulary|namespace"
53
```

The whole-file count is the control: the regex finds those terms 53 times in the file and 0 times in
the row, so the zero is absence rather than a broken search. The questions were routed to BL-143 by
`docs/project-knowledge-manifest.md:721` — *"check 1 versus check 3 is BL-143's question"* — and by
`docs/milestones/export-mechanism-implementation-notes.md:8` — *"**BL-143** owns all of those"*.

**Two instances, both aimed at the same row.** The second is **BL-161**, which records that
`docs/milestones/export-mechanism-implementation-notes.md` named BL-143 as the inheriting row for a
deferred sprint arm — in BL-161's own words, a row *"which does not know it."* Both pointers were
**invisible from the row**: a reader of BL-143 at any commit before `84c24c7` would have found no
trace of either obligation in it.

**Why this is a system finding and not one row's bad luck.** The two halves of a citation are not
symmetric. **The citing document is satisfied the moment it names a row** — it has discharged its
own duty to say where the question goes, and it is correct and complete as written, so nothing about
it will ever prompt a second look. **The row acquires an obligation nobody wrote into it** — its
text, its Done-when and its status are untouched by the naming, so the obligation exists only in a
document the row does not reference and its next reader has no reason to open. Nothing in either
repo closes that gap and nothing reports it, and the idiom that produces it — a document deferring a
question to a row — is the standard one here.

**NOT KNOWN, and what this row owes.** Which remedy, of at least three that are not equivalent and
not merely different in cost: that a pointer **must amend its target** in the round it is written;
that an **unamended pointer is not load-bearing**, so a row is never bound by a document it does not
reference; or a **check**. This row picks none of them.

**The adjacency, noted and not decided — with a caveat about its pointer.** A **BL-ID resolution
check** would establish that a cited row *exists*, and **resolution is a weaker property than the
row knowing**: a check can plausibly establish the first and probably not the second, knowing being
a property of the target's own text rather than of the reference. That distinction is worth carrying
into whichever remedy is chosen and does not decide between them. **The pointer that came with it
does not resolve at HEAD.** It was given as drift-checker work queued for *m7 t1*, and no such queue
is locatable in either repo: `git grep -inE "m7[ -]t1" -- '*.md'` finds nothing in `aetheris-agents`
but docbuilder's closed m7-offer-letter t1 and this row's own prose, and nothing at all in
`aetheris` — the control being that `drift_check` appears in 9 harness `.md` files, so that search
is live — while `git grep -inE "BL-ID|BL id|resolution check"` returns nothing relevant in either
repo. Recorded as the arbiter's and unlocated, so the next session does not spend the search again
and so the adjacency is not mistaken for a repo fact.

`[De-numeralised 2026-08-17. The sentence above read *"returns four hits"*; run at `43e63e0` the
command returned one more than that, and the extra one was this row's own sentence, which contains
the string it counts. **A census recorded inside the document it censuses counts its own
sentences** — the harness rule *a count names the commit it was derived at, or a pointer replaces
it* (`../aetheris/CLAUDE.md` §Continuous learning) names exactly that as its worst case, and this
row was written the day after that rule was last reaffirmed. The figure was true when derived at
`84c24c7` and false from `d60c6df`, the commit that published it. Writing this note adds further
self-hits, which is the mechanism demonstrating itself rather than an oversight, and is why the
sentence above now names its population instead of sizing it. **Corrected by removing the number
rather than by writing a bigger one**, per `CLAUDE.md` §Learning — m6-cloudcost: a corrected figure
re-arms the same trap the next time anything in either repo mentions m7 t1. **The half worth
keeping:** the decay was caught in seconds because the command shipped beside the number —
`CLAUDE.md` §Learning — BL-152's second entry, *a count recorded in prose carries the command that
reproduces it*, paying for itself inside a day. **The row's substance is untouched:** no m7-t1 queue
is locatable in either repo, and nothing else in this row is edited.]`

**Done when:** one of the three remedies is chosen and written into a named document with its scope,
or the gap is accepted in writing with its reason — either way stating what a citing document owes
its target, and where a reader of a row learns what has been routed to it.

**Costs:** S to decide. Two of the three remedies are a paragraph in a standing document; the third
is a check and is larger, and the adjacency above is the reason not to assume a check reaches the
property that matters.

**Collides with:** **BL-161**, which is one of this row's two instances and cross-references it from
there. Neither closes the other: BL-161 owes a sprint arm, this row owes a rule about pointers, and
discharging either leaves the other exactly as it stands. Adjacent to **BL-150**, the standing home
for documentation-system findings — filed as its own row rather than appended there because it
carries an open decision between three candidate remedies, which is a unit of work rather than an
observation, and on the precedent of BL-160 and BL-161, both filed as rows on 2026-08-16.

`Source: the BL-143 close of 2026-08-16, packet §DC3 and §4. The grep and its control are that
packet's, re-run at `84c24c7` before this row was written. The two-instances framing and the
citing-document/row asymmetry are the arbiter's, given at that close. BL-161's wording is
transcribed from its **Collides with** at `84c24c7`.`

---

### BL-163 — `bl-002`'s post-upload checks state check 1 and check 3 without the namespace boundary (#TBD)
**Kind:** defect · **Census items:** n/a · **Contract:** `docs/backlog-2026-06.md` BL-143, the `[Ruled 2026-08-16 …]` annotation
**Size:** S · **Priority:** medium
**Section:** process / project knowledge (`prompts/bl-002-refresh-project-knowledge.md`)

Filed 2026-08-16 at BL-143's close, in the round that deferred it. Established at agents `84c24c7`.
**This row is the deferral's executor.**

**What is stale.** `prompts/bl-002-refresh-project-knowledge.md` §Post-upload verification (`:139`)
states the two checks in the form BL-143's ruling supersedes. Check 1 (`:150–152`): *"The store's
document set equals the manifest's export-name column exactly — set comparison in both directions,
not a count. A name in one and not the other is the finding."* Check 3 (`:156–162`) covers a
document predating the upload window and offers *"either it is a deliberate non-manifest document
(agent-written docs land under `claude/`), in which case the manifest should say such documents may
coexist and are out of scope, or the upload was incremental."* Neither is scoped to a namespace, so
check 1 reads a `claude/` document as a finding while check 3 reads it as out of scope — and check
3's escape clause is written as a *condition on the manifest* that was unmet when the text was
authored and is met now.

**What the rewrite must say**, carried here so it is not re-derived: **check 1 governs every store
path not under `claude/`**; **check 3 governs `claude/`**; and **neither treats the other's
population as a finding** — a `claude/`-namespaced document is out of the export set by construction,
neither a check-1 finding nor a check-3 exception. The reasoning is BL-143's and is not restated
here; the standing form is `CLAUDE.md` §Definition of done.

**NOT KNOWN, and this row's first step.** Whether anything else in that prompt assumes the unscoped
reading — the remove half of the procedure, the ordering of the three checks, or any prose
describing what the store contains. That sweep **was not run** at the close, and nothing here should
be read as a claim that the two checks are the only affected text. Running it is this row's first
step, before any edit.

**Why this is its own row and not a widening of BL-143's Done-when.** BL-143 asks one question —
ownership and trigger — and widening it to carry this rewrite would be **BL-162's defect committed
in the act of recording it**: an obligation attached to a row from outside, silently changing what
that row must satisfy. BL-143's Done-when can be discharged in full without this rewrite ever
happening, which is precisely why the deferral needed an executor rather than a mention.

**Why it was not done in the ruling's own commit**, in the ruling's own words: *"the ruling and the
procedure it governs are separate landings, and a procedure edited in the same commit as the ruling
that authorises it cannot be reviewed against it."*

**Done when:** §Post-upload verification states the namespace boundary for check 1 and check 3, and
the sweep above has been run with its result recorded — including the result that there is nothing
else, if that is what it finds.

**Costs:** S. The two checks are a paragraph each. The sweep is the unpriced half and is small.

**Collides with:** nothing. It does not reopen BL-143's ruling and does not touch that row's open
Done-when. **BL-161**'s second branch — whether the export mechanism owes a sprint case — concerns a
different file and does not wait on this.

`Source: the BL-143 close of 2026-08-16, packet §4, which established that the deferral recorded
inside BL-143 had a record and no executor. The deferred text is quoted from BL-143's `[Ruled
2026-08-16 …]` annotation at `84c24c7`. The prompt file was read at `84c24c7` to establish the
quotations above and was **not** edited, then or by this filing.`

---

### BL-164 — a test that hard-codes a value the code derives goes red when the derivation moves, not when the code breaks (#TBD)
**Kind:** defect (instance fixed) + decision (the class) · **Census items:** n/a · **Contract:** `CLAUDE.md` (agents) §Definition of done — *every existing gate runs at ticket boundaries*
**Size:** S to decide the class; the instance is already done · **Priority:** medium
**Section:** testing discipline (both repos' test suites)

Filed 2026-08-17, in the round that fixed the instance. The instance is closed; **the class is what
this row is for.**

**The instance, as found.** `tests/test_repin_manifest.py` built its fixture manifest with the date
column written as the literal `2026-08-16` (in `_manifest_text()`), over a fixture repo whose commits
were made at run time. `scripts/repin_manifest.py` derives that cell from the commit it resolves
(`git_commit_date`, BL-151's two-cells-one-reading change), so the two agreed for exactly one day.
At the first midnight the derivation returned `2026-08-17`, the fixture still said `2026-08-16`, and
the suite's two whole-file assertions —
`test_a_current_manifest_is_left_byte_identical` (idempotence) and
`test_only_the_commit_and_date_cells_change` (containment) — went red. **Nothing about the code had
changed.** Found at `43e63e0` by an off-territory gate run, one day after the tests landed.

**The two controls at discovery**, both in a throwaway detached worktree so no working copy was
touched: the same two tests fail at `d60c6df` with no local edits at all (so the red was not the
finding round's), and advancing the literal to that day's date turns all thirteen green (so the
mechanism is the date and nothing else).

**The two controls at the fix**, in the commit that files this row. **Load-bearing:** three
mutations on `scripts/repin_manifest.py`, each restored from a sha-verified working-copy backup —
reading the date off `HEAD` instead of off the resolved commit kills both repaired tests (and a
third), while dropping the date from the currency check or from the cell rewrite is caught by the two
date-specific tests instead. **Stable:** the repaired suite run under an injected future clock — a
`git` shim on `PATH` stamping 2031 wherever the caller left the date to the system, faithful because
the suite reaches the clock through git's commit stamping and through no other route — is green,
with the pre-fix suite under the same shim red as the positive control that the shim bites.

**And the finding that is worth more than the instance: a mutation test proves a test is
LOAD-BEARING; it says nothing about whether it is STABLE.** These two assertions were mutation-proved
when they landed, at the 2026-08-16 export boundary, and that is recorded in `CLAUDE.md` §Learning —
the 2026-08-16 export boundary. The mutation passing is what stopped anyone looking further: it
answers *does this test fail when the code is wrong?* and is silent on *does this test pass when the
code is right, tomorrow?* Two properties, one control, and the second was never run — by the arbiter
who issued the mutation requirement, on the round that wrote the tests. A suite can be fully
mutation-proved and still be a set of time bombs.

**Adjacency, stated and not collapsed.** `CLAUDE.md` §Python script conventions holds *bind to the
value a library resolved, never the one it advertises* — a rule about **product code** reading a
library's own resolved answer instead of re-deriving or re-typing it. This is the same family one
step over: a **test** stating a value the code under test derives, instead of reading what was
actually produced. They are not one rule and should not be merged — that one is about which of two
fields to read at a live call site, this one is about a fixture's expectation decaying against a
derivation — but the failure they share is a second surface holding a copy of something that has a
single authoritative source, and the repair in both cases is to read the source rather than restate
it.

**NOT KNOWN, and this row owns it: whether any other test in either repo hard-codes a value its code
derives.** That sweep **was not run** and nothing above should be read as if it were — no census, no
population, no count. The date shape is the obvious member (any test asserting a `YYYY-MM-DD` its
subject computes) but the class is wider: a commit hash, a version string, a resolved model id, a
generated filename, a row count. Running it is this row's first step, before any rule is written.

**Done when:** the class has a stated check — a rule in a standing document, a lint, or a sweep with
a recorded result — **or** is accepted in writing with its reason, and either way the sweep above has
been run and its result recorded, including the result that there is nothing else, if that is what it
finds.

**Costs:** S to decide. The sweep is the unpriced half; it is a substance search rather than a token
search, since a hard-coded derived value has no lexical signature (a date literal, a hash literal and
a count literal look like every other literal), which is the reason not to assume a lint reaches it.

**Collides with:** nothing open. It does not touch BL-151 (which established the derivation) or
BL-152 (which established the gate that found this). Adjacent to **BL-150**, the standing home for
documentation-system findings, but filed as its own row on the precedent of BL-160, BL-161, BL-162
and BL-163: it carries an open decision plus an unrun sweep, which is a unit of work rather than an
observation.

`Source: the handoff follow-up of 2026-08-17. The instance and both discovery controls are that
round's predecessor packet §3 F1 (the gate run at `43e63e0`); the fix and both fix-side controls are
this round's packet §1. The mutation-versus-stability finding is the arbiter's own, given at this
round's opening and recorded here in its words: *"A mutation test proves a test is LOAD-BEARING; it
says nothing about whether it is STABLE."*`

---
