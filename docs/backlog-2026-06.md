# Backlog — 2026-06

Distilled from the reality-check / drift-apparatus work of 2026-06-11.
All file references verified against code as of `docs/rig/current-state-2026-06.md`
(plus subsequent commits: stale-run/cost `88705f1`/`0eddf20`, drift checker
`66566b6` + `bd2c3d8` and follow-ups).

Sizes: **S** < half a day · **M** a day or two · **L** milestone-sized (gets its
own `docs/rig/milestones/` directory and issue docs before implementation).

GitHub issues: #42–#55 on vishal-h/aetheris-agents.

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

**Done when:** a fork of a tool-using run continues successfully against a real
provider, or the contract states plainly that fork continuation is stub-only and the
UI refuses real-provider forks rather than failing at the first call.

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

`Source: BL-025 execution, 2026-07-23.`

---

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
  `fs_hash_stability_test.exs` (×2). This one is **not** obviously a stale test and may be a
  live defect in worker fs-hashing; it needs diagnosis, not a test edit.
- **Network/credential-dependent integration tests pulled in by the include** — `httpbin.org`,
  the GitHub MCP server, the HTTP MCP transport. `--include requires_worker` overrides the
  `:integration` exclusion for tests carrying both tags, so these run whether or not the
  environment can support them. 6+ failures.

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
| 1 | BL-001, BL-015, BL-002 | Minutes each; locks in everything just built. BL-015 before BL-002 so one export catches the §6 promotions |
| 2 | BL-010 | First real run revealed output defects; fix before next client demo |
| 3 | BL-003 | Done. 76 orphaned `running` rows (66 orphaned / 10 reconcilable) cured; pairs with the shipped stalled? marker |
| 4 | BL-005 | Small, immediate daily-use value |
| 5 | BL-009 | One-line change once baseline holds |
| 6 | BL-011 | Refactor before more scripts share the helpers |
| 7 | BL-004 | Trivial, batch with any harness.rs touch |
| 8 | BL-012 | Design decision first; implement after 1a t3 merges |
| 9 | BL-013 | Needed before testing a second SO template |
| 10 | BL-014 | Low-effort address fix; do with BL-013 pass |
| 11 | BL-007 → BL-008 | Milestone-sized; docs-first per repo convention |
| 12 | BL-029 | Every run shows the wrong label today; one line per site. Batch with BL-004 — same file (`harness.rs`) |
| 13 | BL-028 | Silent-empty is the worst failure shape: a fork proceeds from a wrong context with no signal |
| 14 | BL-031 | Small resilience fix; converts a class of hangs into a legible error. Cheaper before BL-030 changes the fork call shape |
| ✔ | BL-025 | **Done 2026-07-23.** Grew in-cycle to include the CLI rewire (it never reached `Verifier`). Spawned BL-042/043/044/045 |
| ✔ | BL-042 | **Done 2026-07-23.** Grew in-cycle by one tool: `run_command` was never re-executed under verify at all (`unknown_tool`), so the netns had nothing to contain until the routing was fixed. Spawned BL-047 (the `git_*` half of that gap, plus its taxonomy question) and BL-048 (the red `requires_worker` set found off-territory) |
| 15 | BL-043 | `http_call` is dead in every mode, so nothing regresses by waiting; but it is the reason BL-042's exposure looks smaller than it is. Confirm the tool has no live users before choosing repair-vs-retire. **Now unblocked**: BL-042's netns has landed, so restoring egress no longer widens an open window |
| 15a | BL-047 | The `git_*` half of the routing gap BL-042's §5 correction names. Decide the mutating-vs-read-only classification *first*; the routing is three lines once the taxonomy is settled |
| 15a2 | BL-048 | Known-red gate, tracked not carried. Triage before anything cites "the worker tests pass" |
| 15a3 | BL-049 | Operator-facing *today*: BL-042 made `run_command` reach the comparison, and the comparison is wrong for it. Ahead of BL-047 — routing more exec-server tools into a comparison that mis-reports would multiply the defect |
| 15b | BL-038 | Medium, operator-facing, and it carries the shared find-run-by-id piece so BL-024 (19b) inherits it rather than the reverse — deciding which lands first rather than leaving "whichever" open |
| 15c | BL-039 | Ahead of BL-030 — an early-return fork UX matters little while real-provider forks fail at the first LLM call. Builds atop BL-028's landed state (same clause, `fork.ex:101-105`); must not race it |
| 16 | BL-030 | Unblocks a non-blocking fork UX; do after BL-031 so the wait path is already bounded |
| 17 | BL-032 | Decide WAL-or-not once the fork call pattern (BL-030) settles, since that changes the contention profile |
| 18 | BL-033 | Trivial deletion, but do it after BL-024 confirms no lineage work wants the union member |
| 19 | BL-037 | Before BL-024 — the lineage view needs real-vs-fallback labels; building it first bakes in the string-comparison guard |
| 19b | BL-024 | Design-led; compose with `caused_by` rather than a fork-only index. Handle both provenance shapes |
| 20 | BL-034 | Do before the next export, not during one — the prompt's own ordering bug is easiest to fix when no export is in flight |
| 21 | BL-035 | Do with the next frontend ticket that touches a fourth formatter site — the trigger, not the calendar |
| 22 | BL-036 | Closes the blind spot that hid the phantom `RunDetail.events` field. After BL-035; both are cleanup on the same surface |
| 23 | BL-041 | Disposition (a) is a doc-only rule worth landing before the next export, since that export's own done-check is the case it governs. Disposition (b) batches with BL-036 — both are drift_check blind spots |
| 23b | BL-044, BL-045 | Small harness cleanups from BL-025; neither blocks anything. BL-045 is a naming decision, not a deletion — do not batch it with BL-033 |
| 23c | BL-046 | The payload-key convention, after three read-side fixes. Low priority but rising: each new reader has cost a bug. Do with the next `:tool_result` reader, not on a calendar |
| — | BL-026 | Fires on its trigger: first `verify` run against a multi-agent/orb trajectory (ratified 2026-07-19) |
| ✔ | BL-027 | **Done 2026-07-23, folded into BL-025.** Its trigger was too narrow — any failed contained tool call reached the crash — and BL-025 made `aetheris verify` real, which would have shipped it. Convention residue → BL-046 |
| — | BL-006 | Fires on its own trigger |
