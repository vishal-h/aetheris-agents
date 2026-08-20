# Backlog — 2026-06

Distilled from the reality-check / drift-apparatus work of 2026-06-11.
All file references verified against code as of `docs/rig/current-state-2026-06.md`
(plus subsequent commits: stale-run/cost `88705f1`/`0eddf20`, drift checker
`66566b6` + `bd2c3d8` and follow-ups).

Sizes: **S** < half a day · **M** a day or two · **L** milestone-sized (gets its
own `docs/rig/milestones/` directory and issue docs before implementation).

GitHub issues: #42–#55 on vishal-h/aetheris-agents.

---

> **This file holds the OPEN rows.** Terminal rows — `**Status:** DONE` — live in
> [`backlog-2026-06-closed.md`](backlog-2026-06-closed.md). The **id is the address**;
> the path is never load-bearing, so a `BL-nnn` that returns nothing here is in the
> archive, not gone. `scripts/backlog_status.py` and `drift_check.py`'s
> `backlog_resolution` check both read the **union**, and so does the harness sprint's
> KNOWN_RED resolver.
>
> **The export set carries this file only.** `docs/project-knowledge-manifest.md` has a
> row for `backlog-2026-06.md` and **deliberately none for the archive**: a row would buy
> an export obligation and a third standing staleness WARN over history that does not
> change. The consequence is stated rather than left silent — an uploaded backlog
> describes the open set and not the closed one.


---

## Harness (aetheris/)

### BL-024 — Fork lineage queries (`fork_event_id` / "list forks of run X") (#TBD)
**Status:** OPEN
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

### BL-026 — Verify: divergence report names no first diverging event (#TBD)
**Status:** OPEN
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

### BL-032 — WAL connection-lifecycle follow-ups (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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


---

## Rig (aetheris-agents/rig/)

### BL-006 — Document `stop_reason` when first observed (#47)
**Status:** OPEN
**Size:** S · **Priority:** tracked (event-triggered, not scheduled)

Confirmed absent from all current DB events (count = 0). The trigger is
mechanical: when drift_check emits
`INFO payload_fields: llm_responded.stop_reason in DB events but not
listed in specs.md §6`, add `stop_reason` to the §6 `llm_responded` row —
no `?` suffix needed, since by then it is observed. The `?` convention
exists for the general case; this ticket just records the trigger.

**Done when:** the INFO fires once and the field is promoted.

---

### BL-023 — Retry parity for hosted-provider adapters: 429 handling (#74)
**Status:** OPEN
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

### BL-035 — Extract `formatCost` / `formatTokens` to `src/lib/format.ts` (#TBD)
**Status:** OPEN
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

### BL-054 — The twelfth `requires_worker` failure is a load-sensitive flake with no stable identity (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-058 — specs §5 (TypeScript Interfaces) is unchecked, and already stale (#TBD)
**Status:** OPEN
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

### BL-062 — Fork provider/model overrides (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-071 — Resource-level AWS cost + the resource-rate spot-check (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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

### BL-075 — `mix test` flakes on a fixed 300 ms inactivity window in `RunHelpersTimeoutTest` (#TBD)
**Status:** OPEN
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

**Annotated 2026-08-19 (ds cycle, stage B) — a fourth observation, and it is the first pair that
pins the flake to an *unchanged tree in both directions*.** Three runs come from the ds cycle's
stage A of 2026-08-18 and the fourth is this session's own boundary gate:

```
2026-08-18, ds stage A    harness 9ba6c8c    green
2026-08-18, ds stage A    harness 8eb960d    green
2026-08-18, ds stage A    harness 8eb960d    RED
2026-08-19, ds stage B    harness 8eb960d    972 tests, 0 failures, 133 excluded (90.8 s)
```

**What is new is the second and third rows: the same tree, opposite outcomes.** Every earlier
observation on this row compared runs across *different* trees — m2 t2, m4 close-b, hc-d r3 — and
had to argue from the diff that the tree was irrelevant; hc-c's annotation says so in as many
words, *"that is reasoning from the diff, not a measurement."* This is the measurement. At
`8eb960d`, clean and unchanged, `mix test` has now returned both red and green, and this session's
fourth run is a third pass over that same tree. The failure is **intermittent at a fixed tree and
not deterministic in the tree**, which removes the last reading under which it could have been a
tree-dependent failure rather than a flake.

**One of the three stage-A data points is not in either repository and is the reviewer's account.**
The red was reported, not captured here: no output of it exists in this repo, in the harness, or in
any committed artifact, and this session did not observe it. It is carried on attribution, and it
is **not** evidence about the failing test's identity — nothing establishes that it hit
`…run_helpers_timeout_test.exs:84` rather than something else, which is the same gap the
2026-08-02 run left and for the same reason. The two stage-A greens are that session's account on
the same terms. The fourth run is this session's own with its full output retained — in a session
scratchpad, which is **BL-133** arriving on this row for the fourth time.

**Neither Done-when arm moves, and neither is amended.** Arm 1 wants the flake reproduced *with its
name captured*; the red above has no name. Arm 2 wants three further full-output runs come back
clean **retained somewhere durable**; this session's green is retained nowhere durable, so E4's
finding stands exactly as written — the place exists, the routing does not.

**The row's heading was corrected in the same commit, and it is a label rather than a record.** It
read *"`mix test` failed once then passed three times, identity uncaptured"* — a heading its own
body has falsified since 2026-08-08, when the m4 close-b annotation captured the identity. The
filing narrative it described is intact in the body and is not edited. One transcription of the old
heading survives at `cloudcost/docs/m5-scoping-landing-notes.md:272`; that is a milestone working
artifact and a point-in-time record, and it is deliberately left.

`Source: m2-cloudcost t2 done-check, 2026-08-02 (aetheris-agents 7a7b7ec; aetheris fd9ac48,
untouched). Annotated at m4-cloudcost close-b, 2026-08-08 — close-a Part 5 for the retention
finding; the reproduction and the failing test's identity are this close's own four runs, at agents
2806305 / aetheris 288c8ef, neither of which touches harness code. Annotated again 2026-08-09 at
hc-e's opening edit (E3 fold, E4 blocker status), at agents f8ed90f / aetheris 48f59e7.
Annotated again 2026-08-19 at the ds cycle's stage B, at agents `9b9b274` / aetheris `8eb960d`,
the harness untouched by that commit; three of the four runs recorded there are the ds cycle's own
account and one is this session's, as the annotation distinguishes.`

---

### BL-076 — `compose_report_data` sums *every* provider's prior snapshot into one `prior_total` (#TBD)
**Status:** OPEN
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

### BL-061 — Gemini thought signatures are not recorded, so a forked Gemini run loses them (#TBD)
**Status:** OPEN
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

### BL-059 — Parallel tool calls are silently discarded: the adapter keeps the first `tool_use` block (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-084 — Tools manifests for the four use cases that have none (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-091 — exportConfig() drops every manifest-derived env key (#TBD)
**Status:** OPEN
**Size:** S · **Priority:** low-medium · **Section:** aetheris-agents (`rig/`)

Filed 2026-08-03 by BL-084. `exportConfig()` (`rig/src/hooks/useAgentConfig.ts:33-41`) iterates
`AGENT_CONFIG_DEFS` only, so every dynamic env_deps key — api's 16, cloudcost's 6 — is editable and
persisted in agent-config but silently omitted from Export. Pre-existing (api already affected);
BL-084 surfaced it. Decide the masked-key policy deliberately when fixing: omitting secret keys from
export may be intended hygiene, but omitting the non-masked keys (region, access-key-id) is silent
data loss on config transfer.

`Source: BL-084, 2026-08-03.`

### BL-093 — runbook drift: PAYSLIP_MONTH described as non-persistent (#TBD)
**Status:** OPEN
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

### BL-097 — Orchestrator: selecting a Recent prompt covers Run and the env disclosure (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-046 — Tool-result payload key is a convention, not a contract: `"output"` vs `"result"` (#TBD)
**Status:** OPEN
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

### BL-044 — `mix aetheris` discards every command's exit code (#TBD)
**Status:** OPEN
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
**Status:** UNRULED
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
**Status:** OPEN
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
**Status:** UNRULED
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

### BL-051 — One unidentified `mix test` failure, and the capture discipline that lost its name (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

> **RETIRED 2026-08-12 by the arbiter's ruling on BL-145, and left in place rather than
> removed.** The row bodies are authoritative; each row's `**Status:**` field, added at ds
> t0, is where the question *is this row terminal?* is answered. This table has not been
> maintained since 2026-07-26 and its ✔ marks are a second surface that disagrees with the
> bodies in both directions. **Do not add a ✔ here and do not read one as current.**
> Executing the retirement — deleting the table, and deciding what becomes of the
> *sequencing opinion* it carries and the bodies do not — is **BL-145**'s and stays BL-145's.

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
**Status:** OPEN
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

### BL-102 — The complete-but-unmarked sweep runs at milestone closes only, so batch closes leave rows silently open (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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

### BL-108 — the eduloka sink gate parses a merged stream: same shape, different root cause (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-122 — `source_granularity` is carried into the report and validated nowhere (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-128 — C6: the keep marker becomes a first-class field, not a tag spelling (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-133 — the loop's evidence is not retained, so no past run's greenness is checkable after the fact (#TBD)
**Status:** OPEN
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

**C7, 2026-08-19 — the gate ran clean, outside any session, and this row is the only place it is
recorded.** `c7180a8` (agents) fixed `rig/src-tauri/src/usage.rs` and its message states, verbatim,
that the change is compiler-unverified: *"Not verified by the compiler in this session:
`cargo check --offline` was killed at its 570s cap twice, still building dependencies
(tauri-runtime-wry, then libduckdb-sys). Recorded as a capped result rather than retried at a longer
cap."* **The non-verification is therefore already in the permanent record** — commit messages are
committed — and it is not what was missing. What was missing is the **clearing**: the operator ran
the same `cargo check` to completion on **2026-08-19** and it was clean, in a terminal neither
repository records. Verified unrecorded at agents `b98be4d`: `git grep -niI 'cargo check' --
'docs/'` → **0** in agents; the three harness hits are `m10b-autonomous-agent-hardening.md`
done-when lines, unrelated.

**This is a worked instance of this row's own subject, which is why it lands here rather than as a
note elsewhere.** Face 1 says a green result whose evidence does not outlive the session it ran in
is not checkable afterwards. The clean run is exactly that: no later reader can establish that
`c7180a8` compiles, because the only artifact is a line in a terminal that is gone. The result is
recorded here **as the operator's report, with its holder named** — it is not repo state, and this
append does not make it so. Its mechanism, as one of three distinct ways an off-territory gate goes
unreachable, is filed on **BL-150**'s `2026-08-19` off-territory append.

**And the same ticket's own gate run then measured the mechanism, which is worth more
than the report it corroborates.** At the ds t1b boundary, `cargo check --offline
--all-targets` was run in this repository against the warm `target/` the operator's run
had left behind, and finished **clean in 17.59s, exit 0**. So the gate that was
cap-killed twice at 570s from cold clears in **under twenty seconds** warm: the binding
constraint was never the gate's own cost but the cap against cold build state, and that
is now a measurement rather than an inference. **What this does NOT establish:** that
`c7180a8` compiles. The run was at ds t1b's HEAD, not at that commit, and a gate covers
the tree it ran against — which is this row's face-1 subject restated, not an exception
to it. The evidence for this run outlives the session only because the ds t1b review
packet carries it; nothing in the repository does, which is the gap the row holds.

`Recorded 2026-08-09 by hc-e's §Close criteria clause 1 sweep, which found the discharge claimed
in docs/milestones/hc-consolidation.md §Ticket set and recorded on no row here. The work is hc-d's;
only the record was missing.`

---

### BL-134 — verify the seven comment-anchored census claims, and hand-classify the eight the sweep could not reach (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

- `2026-08-17` — **`CLAUDE.md` instructs the creation of the file `pytest.ini` exists to keep
  absent.** §Definition of done states that the root `conftest.py` attributes every deselected test
  to exactly one reason. There is no root `conftest.py`; the hook is in `tests/conftest.py`, and the
  root file's absence is deliberate and load-bearing — a `conftest.py` at the rootdir is imported
  under the bare module name `conftest` and shadows the runtime `from conftest import …` lines in
  `cloudcost/tests/`. `pytest.ini` says so and names **BL-157** as the row holding the trap open.
  The two documents contradict each other and the exported one is the wrong one, so a session
  following `CLAUDE.md` creates the file the ini exists to prevent. This is a live instruction to
  break a gate, which is why it is recorded first. **A documentation-system finding and not a code
  one** because the code is correct and only the sentence about it is wrong. Verified at agents
  `df2600f`: `ls conftest.py` → No such file; the hook at `tests/conftest.py:51-55`; the rationale
  and the BL-157 pointer at `pytest.ini:38-41`. No fix is proposed here.

- `2026-08-17` — **The backlog has no uniform status field, and the open set can only be
  bracketed.** Status is expressed four ways, and most rows express it not at all: as a word in the
  `###` heading — 19 rows, from
  `grep -cE '^### BL-[^—]*— *(DONE|CLOSED|SUPERSEDED|WONTFIX|OPEN)' docs/backlog-2026-06.md`; as a
  standalone `**Status:**` line in the body — 26, from
  `grep -cE '^\*\*Status:\*\*' docs/backlog-2026-06.md`; as a bold `**DONE …**` body paragraph —
  11, from `grep -cE '^\*\*(DONE|CLOSED) ' docs/backlog-2026-06.md`; and bolded onto the
  `**Size:** · **Priority:**` metadata line — 3, from
  `grep -cE '^\*\*(Size|Kind):\*\*.*\*\*(DONE|CLOSED|OPEN)' docs/backlog-2026-06.md`. **122 of 181
  rows carry none of the four**, by a per-row derivation over all four patterns. BL-024 (`:393`) is
  the plain case: its whole metadata block is `**Size:** M · **Priority:** low`. Two derivations
  over the same file therefore return a bracket rather than a number — a strict pass misses
  closures recorded only in body prose, a loose pass over-counts rows whose body merely discusses
  one. The consequence is scope rather than hygiene and it is already owned — the ds cycle's t0
  exists to give every row the field — so what is recorded here is the class: a record whose status
  is expressed four ways cannot be queried, and nothing in the file's own structure makes that
  visible to a reader adding the next row. Figures derived at agents `df2600f`, each with the
  command that reproduces it, per `CLAUDE.md` §Learning — BL-152.
  `[Corrected at stage 2 of the ds open, before landing. As drafted this entry named three forms
  and offered **BL-001** as a row carrying none. BL-001 carries one — `**Status:** Done 2026-07-15`
  at `:120`, inside its own row (`:101`–`:124`) — and the enumeration omitted the two most common
  forms after "nowhere". The clause was right and its enumeration short, which `CLAUDE.md`
  §Learning — m6-cloudcost rules is repaired by extending the enumeration rather than by adding a
  clause. Landing it as drafted would have committed a false claim about the backlog into the
  backlog.]`
  `[Corrected by append 2026-08-18, not by rewrite — the entry above stands as landed at
  `6bb81ef` and is the record of what was claimed. **"122 of 181" counted `### BL-` HEADING
  OCCURRENCES, not distinct rows, and overstates the no-status population at both ends of the
  ratio.** Eighteen ids carry a second heading, each an appended `— DONE <date>` closure section
  on an already-counted row, so a row with no status in its original heading and a closure
  section below is counted once in the numerator and twice in the denominator. Carry the
  commands rather than the pair, this being an entry about counts: headings from
  `grep -c '^### BL-' docs/backlog-2026-06.md`; distinct rows from
  `grep -oE '^### BL-[0-9]+' docs/backlog-2026-06.md | sort -u | wc -l`; and the no-status
  population only from a derivation that merges every section a row id owns and asks whether
  ANY carries a status by any of the four forms — a per-heading pass cannot answer it. At agents
  `6bb81ef` those return 181, 163, and **103 of 163**. The numerator falls by 19 rather than 18
  because `### BL-050 + BL-055 + BL-056 — DONE 2026-07-25` is one heading resolving three rows.
  The four per-form figures above are counts of occurrences of a form, never per-row claims, and
  are unaffected.]`

- `2026-08-17` — **The packet-written-as-the-ticket-runs rule presumes a session that commits, and
  has now been missed twice by sessions that do not.** Both the 2026-08-17 scout pass and the ds
  stage-1 session disclosed non-compliance unprompted, with the same reason: instructed to commit
  nothing and issue no packet, there was no packet file to open at the start and append to at each
  boundary, so the prose was assembled at the end from evidence files that were written
  incrementally. Both mitigated the same way, by regenerating rather than reconstructing. The
  disclosure is the rule working; the wording is the finding. Either the rule names the artifact
  that must be incremental — the evidence, not the prose — or a read-only pass is exempted
  explicitly. Two instances, disclosed by the sessions themselves, neither a defect in the work.
  Recorded so it is findable; not triaged here.

- `2026-08-17` — **The off-territory gate rule names a gate it cannot reach.** *Every existing gate
  runs at ticket boundaries, even off-territory* (`CLAUDE.md` §Definition of done) lists the sprint
  among the gates it binds, and its ground is that a gate running only on its own territory rots
  invisibly — three gates were found red exactly that way. But a bare `./scripts/sprint.sh`
  resolves to `TARGET="${1:-all}"` (`../aetheris/scripts/sprint.sh:22`) and dispatches most of its
  arms through live model calls with outward writes to Drive, email and GitHub, so no session can
  run it routinely and none has. The rule therefore binds hardest on the one gate it is
  structurally unable to reach, and that gate will rot in the way the rule exists to prevent, with
  the rule's own text reading as though it were covered. Surfaced when a docs-only boundary was
  instructed to run the full set and the instruction turned out to be unexecutable rather than
  merely expensive. **What is NOT claimed:** that any arm is currently red, or that a cheap
  hermetic subset does not exist — neither was established. **No fix proposed**; whether the remedy
  is a hermetic sprint subset, a stated exemption with its own cadence, or re-keying the rule on
  cost rather than territory is this row's to hold rather than answer. Verified at harness
  `9ba6c8c`: `all` dispatches **18** arms, from
  `grep -oE '"\$TARGET" == "[a-z0-9_]+" \|\| "\$TARGET" == "all"' scripts/sprint.sh | grep -oE '"[a-z0-9_]+"' | tr -d '"' | grep -v '^all$' | sort -u`;
  the script guards **29** cases in total, from
  `grep -oE '"\$TARGET" == "[a-z0-9_]+"' scripts/sprint.sh | grep -oE '"[a-z0-9_]+"' | tr -d '"' | grep -v '^all$' | sort -u`.
  The two sets are not the same: **11** cases are guarded and outside `all` — `payslip`, `eduloka`,
  `eval`, `m12`, `news`, and the six `uc_api_agent_t*` arms — so even a full `all` run is not a
  full sweep. Re-derive both at HEAD rather than carrying these figures.

- `2026-08-17` — **The export boundary ships one half of a byte-identical pair, and the asymmetry
  is invisible to every instrument.** `docs/methodology/triad-loop.md` in the harness carries a
  project-knowledge manifest row; the agents copy `docs/triad-loop.md` does not, though the two
  are byte-identical and are maintained as a pair. Check 8 therefore reports staleness for one and
  is silent about the other, so a divergence landing only in the agents copy raises no WARN
  anywhere. Nothing syncs the pair and `drift_check` has no byte-identity check between mirrors: a
  hand-run `diff -q` is the only instrument covering the class, so the covering instrument is one
  a session must remember to run. Observed at the ds open, where both files were edited together
  and the post-commit `--strict` raised a WARN for the harness path only. **What the boundary does
  carry, stated so this entry is not read as stronger than it is:** the manifest's own note beside
  that row (`docs/project-knowledge-manifest.md:53-55`) names the mirror, declares the harness
  copy canonical, and says to edit that one; and a mirror-pair `diff -q` is recorded as having
  been run at past export boundaries. So the gap is not that the pair is undocumented — it is that
  the documented instrument is an **operator convention rather than a check**, and it lives beside
  a manifest row the agents copy does not have, so the reader most likely to diverge the pair is
  the one least likely to be reading the manifest. **Not the same as** the manifest's coverage
  question generally: this is one document existing twice with one row, not a document missing a
  row. **No fix proposed.** Verify the manifest rows, the note, and the pair's hashes at HEAD.

- `2026-08-17` — **`sprint.sh all` is not all, and nothing says so.** The script guards on 29 case
  names; `all` dispatches 18. Eleven guarded arms — `payslip` among them — are unreachable through
  the aggregate mode and can only be run by name. A reader who runs `./scripts/sprint.sh`
  reasonably believes they have run the suite, and the run reports no shortfall: the BL-077 exit
  contract tallies the arms that ran, not the arms that exist, so a complete-looking green covers
  a set the operator did not choose and cannot see. This is the **Silent-wrong-answer** shape
  applied to coverage rather than to a value. **Distinct from the off-territory-gate entry** above:
  that one is a gate too expensive to run, this one is a gate whose own definition of "everything"
  is short. **No fix proposed**, and specifically it was NOT established whether any of the eleven
  is excluded deliberately. Verify both arm sets at HEAD; do not carry the figures from this text.

- `2026-08-17` — **The scrub class does not reach a session transcript, which is the second channel
  it has missed.** A session instructed to report a variable's assignment site without its value
  printed four unrelated credentials from neighbouring lines of the same file, one of them live and
  uncommented. The redaction it built matched variable NAMES against a sensitive-word list — an
  allowlist, where the constraint required deny-by-default — so the one whose name carried no such
  word passed through. Nothing reached a committed file, a scratchpad file or a packet; each was
  verified with a positive control, and the exposure is confined to the session transcript. **The
  redactor is not the finding.** The U2 class binds the fixtures, the tests, the packet and the
  prose describing them; a session transcript is none of those, and it is a channel that leaves the
  machine. That is the same gap as the `2026-08-14` entry above, where the check was repo-scoped
  and the packet was the unwatched channel — **second instance, different channel, and the
  recurrence is the point.** A second observation, recorded because it generalises: an instruction
  that forbids emitting a class of content without supplying the mechanism leaves the executor to
  invent one, and an invented filter defaults to an allowlist. The deny-by-default form here was a
  read that structurally cannot capture a value. **No fix proposed.** **This entry names no
  variable, no file under any secrets directory, and no value; do not add one.**

  `[Corrected by append 2026-08-18, not by rewrite — the entry above stands as landed and is the
  record of what could be established at the time. **The credential characterised as live was a
  DUMMY**, used for random testing; established by the arbiter on 2026-08-18 and derivable from
  nothing on the machine. (Landed 2026-08-19.) **The finding is unchanged**, because it is about the
  channel and the redactor's shape rather than about the value: the scrub class still does not reach
  a session transcript, and a name-matching filter still defaults to an allowlist. What is corrected
  is the **severity**, which was overstated. **And the reason it was overstated is itself part of
  the class.** No instrument present could distinguish a dummy from a live credential — the redactor
  would have leaked either identically, and a deny-by-default read would have withheld either
  identically. Severity in this class is therefore not machine-derivable, so a session that hits a
  value **reports** it and does not triage it, and a report calling a value live is stating what it
  could not have checked. This clause names no variable, no secrets path and no value either.]`

- `2026-08-19` — **ds t0 changed this list's own subject: the no-status population is now
  zero by construction, and the four form-counts return different figures from the same
  commands.** Recorded as a dated append rather than as an edit, because the
  `2026-08-17` entry above is stamped and carries the command for every figure it
  states — it is **refreshable, not wrong**, and rewriting it would destroy the record
  of what the file looked like before the field existed. What changed: every one of the
  165 row ids now carries a `**Status:**` field at a fixed position, one line below its
  title heading, so *"most rows express it not at all"* is false at HEAD and the bracket
  the entry describes has collapsed to a number — `python3 scripts/backlog_status.py
  --census`, which prints the open set and the command that reproduces it. The four
  legacy forms were **not** removed (ds t0's ADD-never-MOVE rule), so three of the four
  commands return what they returned; the second does not, because the new field shares
  its `**Status:**` prefix — `grep -cE '^\*\*Status:\*\*' docs/backlog-2026-06.md`
  counted 26 at `df2600f` and counts 191 at this commit, of which 165 are the new field
  and 26 are the legacy lines it did not touch. **A reader running that command for the
  legacy population now gets a wrong answer, and the entry above cannot warn them**;
  the form-aware derivation is `scripts/backlog_status.py --census`, whose legacy block
  matches the legacy shape rather than the prefix. **This is the worked instance of a
  census recorded inside the file it censuses** (harness `CLAUDE.md`, *a census recorded
  inside the document it censuses is the worst case, because the sentences describing
  the count are themselves counted*) — the entry did not go stale because time passed,
  it went stale because a later commit to this same file changed what its commands
  measure, and no instrument connects the two.

- `2026-08-19` — **The project-knowledge manifest's own growth compounds on every boundary,
  because the manifest is a row in its own table.**
  `docs/project-knowledge-manifest.md:51` carries `| \`project-knowledge-manifest.md\` |
  \`docs/project-knowledge-manifest.md\` | aetheris-agents | _(this export)_ |`, so each export
  ships a document whose narrative describes the previous exports, and the next boundary's
  narrative is appended to it. Growth derived from the file's own history, not asserted:
  **30 lines at its first commit (`a5a0e12`, 2026-06-11) to 939 at `61b02e1` (2026-08-19)**,
  with boundary-to-boundary jumps around 100 in the 2026-08-16 run alone (537 → 639 → 739 →
  740 → 808 → 817). The table itself is roughly 50 of those lines; the rest is boundary
  narrative. Reproducing command, from the agents repo root:
  `git log --reverse --format='%h %ad' --date=short -- docs/project-knowledge-manifest.md | while
  read h d; do echo "$d $h $(git show $h:docs/project-knowledge-manifest.md | wc -l)"; done`
  **One correction to the wording this was carried in as:** the growth is **near-monotonic, not
  monotonic** — there is exactly **one decrease in the whole history**, 119 → 110 on 2026-07-25
  (`7fa5c16` → `f72f096`). Stated because "monotonic" is falsifiable by one row and the claim
  does not need it. **No fix proposed**; what is claimed is that the artefact's size is a
  function of how many boundaries have run, and that nothing bounds it.

- `2026-08-19` — **The store's manifest can never contain the boundary that produced it, and
  this is structural rather than an oversight.** `scripts/assemble_export_bundle.py:5-9` reads
  each document's content from `git show HEAD:<path>` — *"no timestamps, no working-tree reads"*
  — so the manifest that ships in bundle *N* is HEAD's copy, written **before** the upload it
  would have to describe. It is not fixable by re-uploading one file after the fact: the
  narrative of boundary *N* can only exist at a commit after *N*'s upload, which is by
  construction after *N*'s bundle was assembled. So the store always describes *N-1*. **No fix
  proposed** — recorded because the document most likely to be read as the export's own record
  is the one document that cannot carry it.

- `2026-08-19` — **"the hits that exist are prose and operator instructions" is narrower than
  the census supports, and there is a third kind nobody named.** The operative half **holds**:
  no executable in either repo invokes `gh` — 0 hits for invocation shapes across
  `.py .sh .exs .ex .rs .ts .tsx .yml .yaml`, read against a positive control of 8 subprocess
  invocations of `python3`/`sys.executable` found by the same shape. What the characterisation
  misses is that non-prose `gh`-shaped text does exist, in three kinds and not two:
  **decoy token constants** (`cloudcost/tests/test_fetch_github.py:29-30`,
  `DECOY_TOKEN = "gh-write-DECOY-9b2f4d81"` and `DECOY_TOKEN_2`); **token-shaped regexes**
  (`cloudcost/tests/record_github_fixtures.py:69`, and the same constant name over a different
  pattern at `cloudcost/tests/record_linode_fixtures.py:96`); and **a UI placeholder string** —
  `rig/src/components/modules/settings/agentConfigDefs.ts:59`, `placeholder: 'ghp_...'` — which
  is neither prose nor an operator instruction nor a test constant, and which the two-kind
  characterisation has no slot for. **No fix proposed.** It matters because a sweep written
  against "prose and operator instructions" will not look in a React config file.

- `2026-08-19` — **A whole-file read/write round-trip normalises line endings, and the diff it
  produces cannot be reviewed.** The §Use cases edit at agents `9cf3689` went through a Python
  `read_text` / `write_text` round-trip. `README.md` is the one CRLF file among the ten that ticket
  touched, so the round-trip read CRLF, wrote LF, and rendered a six-row table change as
  **89 insertions(+), 78 deletions(-)** — `git show --stat 9cf3689 -- README.md` — with *"twelve
  real lines of table hidden inside a whole-file rewrite"* (`b98be4d`'s own message). It cost a
  follow-up commit, `b98be4d`, whose only content is restoring the line endings. The class is
  wider than CRLF: **any whole-file round-trip re-encodes everything it did not mean to change**,
  and the damage is invisible in the tool's output and visible only in the diff's shape. Verified
  unfiled at agents `b98be4d`: `git grep -niI -e CRLF -e 'line ending' -e 'line-ending' --
  'docs/' 'CLAUDE.md'` → **0** in agents; the single harness hit
  (`docs/aetheris/runbook-m10-autonomous-agent-tooling.md:178`) is about git stderr being
  discarded on success and is unrelated. Positive control on the same corpus and flags:
  `off-territory` → **24** lines in `docs/backlog-2026-06.md`. **No fix proposed** — whether the
  remedy is an edit discipline, a `.gitattributes`, or a pre-commit shape check is this row's to
  hold rather than answer. ds t1b applied the discipline rather than the rule: its split is
  generated at the **byte** level, splitting on `b"\n"`, so no encoding decision is available to
  be taken wrongly.

- `2026-08-19` — **Two further instances of the off-territory-gate entry above, and their
  mechanisms are NOT the same.** That entry's instance is `./scripts/sprint.sh`, unreachable
  because a bare invocation dispatches live model calls with outward writes — unreachable **by
  cost**. Two more gates are unreachable for two other reasons, and collapsing them would hide
  that the remedy differs per mechanism.
  **(i) Unreachable from cold under a session cap.** `cargo check --offline` over the Rig tree was
  killed at its 570s cap **twice** while still building dependencies (`tauri-runtime-wry`, then
  `libduckdb-sys`) — recorded verbatim in `c7180a8`'s message and not retried at a longer cap, per
  §Definition of done. The gate is not expensive in itself; it is expensive **against cold build
  state**, and the same gate clears in minutes once `target/` is warm. So the binding constraint
  is the cap versus the build cache, not the gate — and a remedy keyed on cost (a cheaper subset)
  would not touch it, while one keyed on warming state would.
  **(ii) Reachable only outside the session.** The operator ran that same `cargo check` to
  completion on 2026-08-19 and it was clean. No session can reach that result: it happened in a
  terminal neither repo records, so the gate is *runnable* but its outcome is *unrecordable* from
  where the rule binds. That is a different failure from (i) — the gate ran and passed, and the
  rule still cannot be satisfied. The result itself is filed on **BL-133**, whose subject it is.
  Verified unfiled at agents `b98be4d`: `git grep -niI 'cargo check' -- 'docs/'` → **0** in agents;
  the three harness hits are `m10b-autonomous-agent-hardening.md` done-when lines, unrelated.
  **No fix proposed.** Note that the entry above closes with *"Re-derive both at HEAD rather than
  carrying these figures"*; this append restates none of its arm counts, so none were re-derived.

- `2026-08-19` — **A document whose subject is stale claims carries eleven stale citations, and
  one insert made all eleven at once.** `docs/milestones/gc-stale-claims.md` cites
  `hc-consolidation.md` nineteen times by bare line number. **Eight resolve; eleven do not** — every
  one of the eleven pointing into the `§Decisions` table, which has moved down by a uniform **+121**
  lines: decision 6 cited `:583` is at `:704` (`gc-stale-claims.md:153`, `:433`); decision 7 cited
  `:584` is at `:705` (`:154`, `:551`); decision 8 cited `:585` is at `:706` (`:155`, `:512`,
  `:550`); decision 10 cited `:587` is at `:708` (`:156`, `:266`, `:552`); decision 11 cited `:588`
  is at `:709` (`:157`). At HEAD, `:583`–`:588` land in an unrelated passage about R22–R24
  numbering and *"hc stays closed"*. **What is NOT claimed, because the tempting version is false:**
  the eight survivors are not cited in a better form — they are bare line numbers too, and they
  survive only because they sit **above** the insertion point. The discriminating fact is position,
  not citation style. What the instance does show is `CLAUDE.md`'s *cite-by-anchor* rule at full
  size — the failure is not one decayed pointer but a whole table's worth going at once, silently,
  each still resolving to *a* line. Derived at agents `b98be4d` by resolving all nineteen citations
  against the target at HEAD. **No fix proposed**; whether the remedy is re-pinning, re-citing by
  anchor, or a check is this row's to hold rather than answer.

- `2026-08-19` — **RESOLVED for ds t1b, and recorded because the ticket routed the question here:
  no backlog issue reference needs repo-qualifying, and the reason is that the backlog names
  issues almost nowhere.** `docs/milestones/ds-milestone.md`'s t1b section routed *"whether backlog
  issue references need repo-qualifying — the file spans both repos and its existing references
  are unqualified, so whether any already points across is unverified"* to this row. Resolved at
  agents `b98be4d`. The backlog's `(#nnn)` heading suffixes are issue refs in **`vishal-h/aetheris-agents`**
  only, and `(#TBD)` is by far the commonest value; the file carries no `owner/repo#n` form and no
  bare `#n` naming a harness issue. So there is nothing today that resolves to the wrong object.
  **What this does not settle:** the qualification rule itself. A bare `#77` written in a *harness*
  artifact resolves to `vishal-h/aetheris#77`, a different object — which is why ds t1b's harness
  commit `a6464f4` spells `vishal-h/aetheris-agents#77` in full. The backlog is an agents-repo file,
  so bare refs are correct **in it** and would not be correct if quoted out of it. Kept as an
  observation about the system rather than closed as a task.

`Source: R23, ruled by the arbiter 2026-08-12 at the gc t3 review and recorded at
docs/milestones/hc-consolidation.md. Row created in the same commit, per R23's own stamp. The five
findings that prompted it are BL-145–BL-149, which stand as separately filed.`

---

### BL-151 — standing: code findings, append-only (#TBD)
**Status:** OPEN
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

- `2026-08-17` — **Two Rig surfaces enumerate use cases and disagree, and nothing checks either.**
  `rig/src-tauri/src/commands/usage.rs`'s `USE_CASE_PREFIXES` carries seven entries and
  `rig/src/components/modules/harness/RunList.tsx`'s carries eleven, so runs for the use cases
  present in one and absent from the other group correctly in the run list and fall to
  `"Unclassified"` in the usage view. Both are hand-written, neither is generated, and no test
  compares them. Two surfaces that must agree with nothing checking that they do — the same shape
  as the `KNOB_CONSTANTS` entry above, except both surfaces are Rig's own and the disagreement is
  visible on screen. **It may be absorbed by the ds cycle's t1a**, whose doc-enumeration check has
  an open slot for which enumerating surfaces are in scope; filed here because that slot is unruled
  and an unowned finding is not left to a decision that may not reach it. Verified at agents
  `df2600f`: `usage.rs:146-154`, seven entries; `RunList.tsx:126-141`, eleven. No fix is proposed
  here.

- `2026-08-17` — **A row's status can sit nineteen lines below its heading, and two derivations
  written against the metadata block missed it.** BL-001 carries a `**Status:**` line inside its
  own row, well past the `**Size:** · **Priority:**` block that both a scout pass and a review
  prompt read as the row's whole metadata. Both concluded the row carried no status; both were
  wrong, and the second nearly committed the claim into this file. The finding is not the wrong
  conclusion — it is that **the row format admits the field at an unbounded offset**, so any
  derivation over this file must scan the whole row, and no derivation reading a fixed prefix can
  be trusted. This is the mechanical half of the no-uniform-status-field entry on BL-150; it is
  filed here because what it constrains is any program that parses this file, and the ds cycle's
  **t0** is the first such program. **No fix proposed** beyond the constraint on derivations.
  Verify BL-001's row bounds and its status line at HEAD.

- `2026-08-18` — **THREE of the four, not two: the `2026-08-16` entry above understates its own
  recurrence.** That entry's *"Two of the four were written the same day they went false, at this
  boundary's own later passes"* is the one clause of it that does not survive measurement. All
  **three** of the 2026-08-16 passes were written and went false on 2026-08-16, and they went false
  in a **single push**. Derived, not eyeballed — the paragraph-authoring commit by
  `git log -S` over the manifest, and the first push containing it by walking this clone's
  `origin/main` reflog oldest-first for the earliest entry that contains the commit:

  | paragraph | written by | committed | first push containing it |
  |---|---|---|---|
  | `:632–637` | `a2df7b5` | 2026-08-16 17:14:36 +0530 | `9741c4e` @ 2026-08-16 18:31:59 +0530 |
  | `:732–737` | `f32516b` | 2026-08-16 17:39:14 +0530 | `9741c4e` @ 2026-08-16 18:31:59 +0530 |
  | `:802–806` | `9741c4e` | 2026-08-16 18:11:12 +0530 | `9741c4e` @ 2026-08-16 18:31:59 +0530 |

  The fourth, `:347–352`, is **UNKNOWN and not excluded**: it was written 2026-08-05 and this
  clone's `origin/main` reflog does not reach back that far — its oldest entry is
  `97c61a0 @ 2026-08-14 10:11:16`, so every pre-`2026-08-14` commit reads as "first push
  2026-08-14" and that reading is an artefact of the reflog's depth, not a fact about the push. So
  the true figure is *three, and possibly four*, and it is **not** the two the entry records.

  **What this changes and what it does not.** The entry's finding is *strengthened*, not
  weakened — the decay is faster and more uniform than recorded, and all three claims died to one
  push nobody had reason to relate to the file. What it corrects is a **count**, and the count is
  the entry's evidence of how the mechanism behaves. Recorded as a correction here rather than by
  editing the `2026-08-16` entry, because that entry is a dated point-in-time record with a
  `Verified at agents 9741c4e` stamp, and the two do different work.

  **A second thing, and it is about the instrument.** The `2026-08-16` entry proposes leaving push
  state to `git branch -r --contains <hash>`, and the manifest's `2026-08-18` note repeats it. That
  command answers *is it public now* and cannot answer *when did it become public*, which is the
  question the "same day" clause is about. The only local evidence for timing is the `origin/main`
  reflog, which is **machine-local, depth-limited and not part of either repository** — so a timing
  claim of this kind is not reproducible from a fresh clone at any commit. Anyone re-deriving the
  figure above will need this clone, or a different instrument. **Not decided here.** Verified at
  agents `e1c7386`; the manifest paragraphs are quoted at their line numbers as of that commit.

- `2026-08-20` — **`resolve_last_run.py` selects "most recent" by a LEXICOGRAPHIC sort over
  local-offset timestamps, so it can return the earlier instant.** `find_last_match`
  (`docbuilder/scripts/resolve_last_run.py:83`) takes `max(matches, key=lambda ie:
  ((ie[1].get("timestamp") or ""), ie[0]))` — a **string** comparison — over the stamps
  `run_log_writer.build_entry` writes at `:80`,
  `datetime.now().astimezone().isoformat(timespec="seconds")`, which carry a **local UTC
  offset**. Two entries written under different offsets therefore sort by printed digits
  rather than by instant. Worked instance: `2026-06-30T14:30:00+05:30` (09:00Z) sorts
  ABOVE `2026-06-30T12:00:00+00:00` (12:00Z), so "same as last month" copies forward the
  context of the run that happened three hours *earlier*. It breaks nothing today because
  every entry in the one surviving log was written in one zone — which is exactly the
  condition that makes it invisible. **Deliberately NOT fixed at ds t2**, whose subject was
  the writer: fixing the reader would have changed the live consumer's selection under
  cover of a refactor. It is pinned as a defect instead, by
  `docbuilder/tests/test_resolve_last_run_characterisation.py::test_lexicographic_sort_is_the_pinned_defect`,
  whose failure message says to retire it and close this entry when the fix lands. The new
  `data/run-records.json` does not reproduce it: `run_record.utc_now` emits UTC with a `Z`
  suffix, under which a lexicographic sort **is** chronological. **A sibling site, filed not
  fixed for the same scope reason:** `provenance/scripts/inventory_report.py:49` names its
  report `inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md` — local time with no
  offset marker at all, so two reports from different zones cannot be ordered from their
  names. Verified at agents `0e5e0d2`.

- `2026-08-20` — **`cloudcost/history/` carries two incompatible layouts for the same
  provider and period, and `load_prior_snapshots` can never read one of them.** The cause is
  ONE code layout under TWO roots, not two code paths. `persist_history`
  (`cloudcost/scripts/compose_report_data.py:989`) always writes
  `{history_dir}/{period}/{provider}_costs_{period}.json`; what differs is `history_dir`.
  The orchestrator passes `--history-dir history/#{provider_slug}`
  (`cloudcost/agents/cloudcost_orchestrator.exs:141`, used at `:277` and `:282`) → a
  **provider-first** tree. The flag is **optional** and defaults to `DEFAULT_HISTORY_DIR`,
  the shared `<use-case root>/history` (`:111`), so any invoker omitting it writes a
  **period-first** tree — and `cloudcost/tools.json:509-514` exposes it as an optional Tools
  panel field whose own help text says *"left blank the script falls back to the shared
  cloudcost/history"*. Both are on disk now, for github/2026-08, six hours apart and
  differing in content:

  | path | md5 | bytes | mtime (UTC) |
  |---|---|---|---|
  | `cloudcost/history/2026-08/github_costs_2026-08.json` | `15167b93df3415a685a6f86c12677cda` | 3788 | `2026-08-14T02:48:27Z` |
  | `cloudcost/history/github/2026-08/github_costs_2026-08.json` | `3361b436a87e6b732cec0727db89595d` | 3790 | `2026-08-14T08:59:55Z` |

  `load_prior_snapshots` reads `history_dir / previous` (`:1002`), so under the
  orchestrator's root the period-first file is **unreachable by every orchestrator-driven
  run** — a month-on-month delta silently computed against the wrong snapshot, or against
  none. Not fixed at ds t2, which recorded the history writes rather than relocating them;
  the record now names the history files as `compose_report_data`'s artifacts, so a reader
  can at least tell which tree a given run wrote. **The shape is why ds t2's own test seam is
  an env var and not a flag** (`run_record.RUN_RECORD_ROOT_ENV`): an optional flag whose
  default differs from what the orchestrator passes is what produced this. Verified at agents
  `0e5e0d2`.

- `2026-08-20` — **docbuilder's PHASE D2 writes the run log before PHASE E writes
  `output/uploaded.json`, so the record predates an artifact of the run it describes.** D2
  invokes `run_log_writer.py` at PHASE D (`docbuilder/agents/docbuilder_orchestrator.exs`
  §PHASE D, step D2); PHASE E then runs `upload_output.py --output output/uploaded.json`
  whenever `DRIVE_DOCBUILDER_ID` is set. That violates BL-153 ruling 1's first owed
  property — *the stamp must be written after every artifact a run produces* — and it is
  the **writer** side of the same defect the ruling names on the reader side: a writer free
  to skip the stamp is a reader free to ignore it, one step earlier, and D2 is a prompt line
  an LLM may skip.
  **The sweep asked for, and its result.** Across all **31** `docbuilder-orch-*` directories
  under `../aetheris/priv/runs/` (`ls -d priv/runs/docbuilder-orch-* | wc -l` → 31; the
  earlier figure of fifteen is wrong), each trajectory parsed and its `run_command` calls
  counted by `args[0]`: `rename_output.py` fired in **25**, `run_log_writer.py` in **20**,
  and `upload_output.py` in **0**. Cross-tabulating prompt-mention against tool-fired gives
  `no/no: 11` and `yes/yes: 20` with nothing off-diagonal — a clean temporal split, the 11
  runs of 2026-06-19..22 predating D2 and all 20 of 2026-06-23..27 firing it. So **D2 fired
  in 20 of 20 runs that instructed it**, and PHASE E has never run at all, meaning the
  ordering defect has never been *exercised*. That changes nothing: a prompt-invoked writer
  is the forbidden shape whether or not it happens to fire. (`docbuilder/data/run_log.json`
  holds one entry, but it is gitignored and three sprint legs truncate it to `[]`
  — `../aetheris/scripts/sprint.sh:2235`, `:2317`, `:2553` — so the file is not evidence of
  the ratio; the sweep is.)
  **Partly addressed at ds t2, and only partly.** The new per-step record is written by
  `rename_output.py` and `upload_output.py` themselves, each attesting its own step, so the
  upload no longer sits outside the thing that describes it. D2 itself is **left where it
  is**: `run_log.json` feeds `resolve_last_run.py`'s "same as last month" and moving it to a
  later prompt phase would relocate the defect rather than remove it. Verified at agents
  `0e5e0d2`.

- `2026-08-20` — **the sprint's `email` and `drive` legs read `payslip/output/` across a
  use-case boundary, and under `all` the payslip leg cannot have run.** The email leg's
  precondition is `find "../aetheris-agents/payslip/output" -name "*-Payslip.pdf" -quit`,
  failing with *"No Payslip PDFs found in payslip/output/ — run the payslip orchestrator
  first"* and otherwise `ok "Payslip PDFs found in payslip/output/"`
  (`../aetheris/scripts/sprint.sh:1129-1133`). The drive leg reports another use case's
  leftovers as its own summary: `PAYSLIP_OUTPUT="../aetheris-agents/payslip/output"`, then
  `TOTAL_EMP` and `TOTAL_PDF` counted from it and printed as `Employees processed` and
  `PDFs generated` (`:1085-1092`).
  **The target guards make it structural rather than merely possible.** `payslip` is
  `if [[ "$TARGET" == "payslip" ]]` (`:973`) — **not in `all`** — while drive (`:1049`) and
  email (`:1104`) both are. So `./scripts/sprint.sh all` never runs the payslip leg, and the
  email precondition is **guaranteed** to be greening on PDFs from some earlier invocation,
  of any age, with no guard and no staleness check. The payslip leg's own
  `rm -rf "${PAYSLIP_DIR}/output"` (`:1006`) is unreachable on that path. This is
  **Silent-wrong-answer**'s *stale/leftover artifacts from a prior run* carrier, crossing a
  use-case boundary. **Neighbour, not a duplicate:** BL-110 is also about
  `payslip/output/`, but its subject is an assertion about `BTL_999` inside the payslip leg;
  this is the cross-boundary read by two other legs. Not fixed here — ds t2 changed no
  harness file. Verified at harness `a6464f4`.

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

- `2026-08-19` — **Four constraints on any program that derives over
  `docs/backlog-2026-06.md`, filed as one entry because they are one subject.** R23
  rules against a row per facet and the same ground applies within a row: these four
  are not four findings, they are the shape of one file stated four ways, and a
  derivation that honours three of them is still wrong. Two are new here; two already
  sit on this row and on BL-146 and are cross-referenced rather than restated, so the
  set can be read in one place. Written at ds t0, which is the first program to derive
  over this file, and each constraint is one its parser implements —
  `scripts/backlog_status.py`, whose module docstring is the executable statement of
  this entry.

  - **Cardinality — a heading may name more than one row, so key on every `BL-\d+`.**
    `### BL-050 + BL-055 + BL-056 — DONE 2026-07-25 (one reorder, three rows)` is one
    heading and three rows, and a parser keyed on the first id credits BL-050 with a
    closure BL-055 and BL-056 also own. **The FACT is recorded twice already** — on
    BL-150's `2026-08-18` correction, which needed it to explain why a numerator fell
    by nineteen rather than eighteen, and in `docs/milestones/hc-consolidation.md`.
    **What is unfiled is the CONSTRAINT ON PARSERS**, and that distinction is this
    entry: both prior records use the fact to *correct a count they had already got
    wrong*, neither states it as a rule binding the next derivation, and a fact
    recorded only inside a correction is reachable only by someone reading that
    correction. Verify the heading and the id counts at HEAD.

  - **The anchor — segment on `^### BL-`, never on `^### `.** Two `### ` headings in
    this file are not row headings, and both sit **inside a row's body**: a
    *Worked instance* heading in BL-041's, and a *Pre-implementation handoff* heading
    in BL-042's. A segmenter splitting on `^### ` truncates both rows at those lines
    and loses everything under them. **And the fix for one defeat creates another when
    applied at the wrong anchor** — that is the point of filing this beside the
    cardinality constraint rather than separately. The *Worked instance* heading names
    a row id in its **text**; a cardinality rule applied at a `^### ` anchor therefore
    mints a spurious section for that id out of BL-041's body, which then **merges into
    the real row of that id** and hands it a status derived from a different row's
    worked example. Correct cardinality plus wrong anchor is worse than neither: it
    produces a well-formed wrong answer on a row that reads clean. Verify both headings'
    positions and their containing rows at HEAD.

  - **The unbounded offset** — already on this row, `2026-08-17`: the row format admits
    a status expression at any distance from the heading, so a derivation must scan the
    whole section and no fixed-prefix read can be trusted.

  - **The quoted disposition** — **BL-146**: a row's body may quote another row's
    disposition in the same form a row uses for its own status, and no pattern over this
    file separates the two. ds t0's field is one structural answer to BL-146's open
    question — a canonical whole-line form at a fixed offset, so a quotation elsewhere
    raises the count to two and fails loudly instead of being silently chosen between —
    but it answers it **for the new field only**. Every derivation over the LEGACY
    expressions still inherits the hazard in full, and BL-146 stays open.

  **No fix proposed beyond the constraint set.** What is claimed is that these four
  bind together; what is not claimed is that they are exhaustive.

- `2026-08-19` — **The backlog's one programmatic parser has never fired in anger, so
  t1b's cross-repo claim rests on a gate with no live arms.** Harness `scripts/sprint.sh`
  defines `expected_fail` and `known_red_healed` — the KNOWN_RED pairing that reads a
  `BL-` reference and checks the row exists in this file (`SPRINT_BACKLOG`) — and
  **both have zero call sites.** So the only executable in either repo that parses
  `docs/backlog-2026-06.md` has never run against it outside its own definition, and its
  behaviour under the row shapes above is unobserved rather than known-good. That matters
  to **t1b and not to t0**: t1b must edit `sprint.sh` or break it, and it is the ticket
  whose cross-repo arm the ds trial exists to exercise (ds-milestone §Close criteria,
  criterion 8). Re-verified at harness `8eb960d`, with a positive control because a zero
  is a claim about a command: non-comment, non-definition mentions of either helper —
  `grep -nE '^[^#]*\b(expected_fail|known_red_healed)\b' scripts/sprint.sh | grep -vE
  '(expected_fail|known_red_healed)\(\) *\{'` → **0**; the same shape over helpers that
  do have call sites — `grep -cE '^[[:space:]]*fail '` → **94**, `ok` → **151**, `info`
  → **137**. The script says so of itself at `scripts/sprint.sh:161` (*"There are zero
  KNOWN_RED arms today (both helpers have zero call sites)"*), which is agreement and
  not the evidence — a document quoting repo state is a snapshot with no invalidation,
  so the count above is the derivation and the comment is the corroboration.
  **No fix proposed**, and specifically it is NOT claimed that either helper is wrong or
  that the row-existence check would fail; only that nothing has ever run it.

- `2026-08-19` — **Correction to the `2026-08-17` Rig entry above: `RunList.tsx` carries TEN
  entries, not eleven. The finding it states is unaffected; the mechanism of the miscount is
  worth more than the digit.** The entry records *"seven entries and … eleven"*, verified at
  `df2600f`. `git diff df2600f..HEAD -- rig/src/components/modules/harness/RunList.tsx` is
  **empty**, so this is a miscount rather than drift. The eleventh occurrence is the
  **TypeScript type annotation on the declaration line** — `RunList.tsx:126`,
  `const USE_CASE_PREFIXES: Array<{ prefixes: string[]; label: string }> = [` — which contains
  the token `prefixes:` and is not an entry. `grep -c "prefixes:"` returns **11**;
  `grep -n "prefixes:"` shows line 126 is the declaration. **The repo's own instrument
  disagreed with the append and nobody read it**: `python3 scripts/check_run_classifier.py`
  prints `Rig run-classifier guard — 10 groups`, and has done so since BL-083 built it. The
  `seven` is correct. Recorded as a dated append rather than an edit, because the entry above
  is stamped at the commit it was verified at and is the record of what was believed then.
  *(This is the class the harness rule* **a count is a claim about a population — name the
  population and show the enumeration** *exists for: the population here is "entries", the
  enumeration was a token grep, and the two differ by exactly the declaration line.)*
  **Fixed under ds t1a**, which is the ticket the entry above nominated: `usage.rs` is
  repointed and `check_run_classifier.py` now parses **both** constants and compares them.

`Source: R26, ruled by the arbiter 2026-08-13 at m6 t2b and recorded at
docs/milestones/hc-consolidation.md. Row created in the same commit, per R26's own stamp. The
ruling's ground is three code findings dropped across m6 t1 and t2 for want of a place to put
them; two of those are seeded above, and the third entry is a finding of t2b's own rather than a
recovered one — the dropped third is not reconstructed here, and this note says so instead of
letting the seed count imply it was.`

---

### BL-153 — the cloudcost sprint's credential gate exits before the stale-artifact guard, so a credential-less leg leaves the previous run's artifacts in place (#TBD)
**Status:** OPEN
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

`[Amended 2026-08-20 at ds t2, the scoping ticket. THE ATTESTABLE UNIT IS THE STEP,
NOT THE DIRECTORY. The two rulings above are inconsistent and this settles it in the
direction the second already points. Ruling 1 owes that "the reader's rule must be that
an unstamped or mismatched DIRECTORY is not a run"; ruling 2 owes that "the stamp's
coverage is every artifact a run produces, INCLUDING the history tree written at an
earlier step into a directory the guard never clears". A directory-level stamp cannot
express the second — cloudcost's `history/` is a *different* directory from the guarded
one, and one run writes into both — so a stamp that certified a directory would certify a
subset while reading as certifying the run, which is the failure ruling 2 names in terms.

The record therefore ENUMERATES ARTIFACTS and attests the STEP that wrote them. Restated
as the reader's rule, replacing ruling 1's directory form: **an artifact not named in an
attested step record is not that step's output.** Ruling 1's substance is preserved
whole — absence still carries the meaning, and an interrupted step is UNSTAMPED rather
than stamped-and-partial — because `attested_at` is written only after every artifact
write for that step has returned. What changes is only the unit the rule quantifies over.

Landed at `scripts/run_record.py`, adopted by all six producers. Format, file and reader
are now ruled and this row's outstanding question is answered: `<use_case>/data/run-records.json`,
a JSON array, one entry per step, `{run_id, step, started_at, attested_at?, artifacts[]}`
with each artifact `{path, sha256, bytes}`. NOT under `output/`: payslip's `output/runs.log`
sits inside the tree `../aetheris/scripts/sprint.sh:1006` `rm -rf`s, so it dies with the
artifacts it attests.]`

`[Amended 2026-08-20 at ds t2. R3'S CONCLUSION HOLDS; ITS STATED REASON DOES NOT. R3
records that the last writer "moves with configuration — with `--pdf` it is the PDF branch".
**The orchestrator never passes `--pdf`.** The flag occurs in `cloudcost/tools.json:582`
and in `cloudcost/scripts/render_report.py` (3 occurrences, which is this search's positive
control) and in **no** cloudcost `.exs` file and **not** in `../aetheris/scripts/sprint.sh`.
So on every orchestrator-driven and every sprint-driven run the last writer is fixed, and
what actually moves it is **which invoker ran** — the orchestrator, or Rig's Tools panel
where an operator may tick the flag. That is the same fourth mechanism R2 found, reaching
R3: the panel is not merely an alternative caller, it is the only route by which the
configuration R3 describes can vary. The conclusion R3 was cited for — that no current step
is a last-writer position — is unaffected and remains true for a stronger reason: it is not
that the position moves with a flag, it is that the position is a property of the invoker,
which no script can observe. Verified at agents `0e5e0d2`.]`

`[Amended 2026-08-20 at ds t2. R4'S GENERALISATION IS FALSE, AND RULING 2 STANDS ON A
BETTER PREMISE THAN ITS OWN CITATION. R4 states that "a per-run identifier exists upstream
and reaches no script", and the second ruling rests its identifier decision on it: *"R4
establishes that no upstream identifier reaches a script, and that changing this means a
harness change at the exec-server boundary."* **docbuilder is a standing counter-example
and predates both rulings.** `docbuilder/agents/docbuilder_orchestrator.exs` mints
`run_id = "docbuilder-orch-#{Aetheris.ID.generate()}"` at `:146`, threads that binding into
argv as `--run-id` at `:231`, and uses the SAME binding as the harness `run_id:` at `:351` —
so the id a script receives resolves under `../aetheris/priv/runs/`, and no harness change
was needed for any of it. R4's reading is correct about every route it examined (the
exec-server env slice, the `run_command` schema, Rig's `job_id`) and wrong in its
quantifier: it concluded from "no route CARRIES one" that none ARRIVES, when the agent file
can simply write one into the argv it was already constructing.

**This makes ruling 2 cheaper, not wrong.** "THE IDENTIFIER IS MINTED BY THE PIPELINE, NOT
INHERITED" is the right call and its real ground is better than the one cited: an id minted
at agent-eval time and threaded into argv needs no harness change AND is the same string as
the harness run id, so it is simultaneously pipeline-minted and resolvable — which the
ruling treated as alternatives. ds t2 applied the docbuilder pattern to `payslip` and
`cloudcost`, each of which minted inline in the struct field and needed only a hoisted
binding plus two argv elements, and to `eduloka`, whose three sub-agent stages now carry the
orchestrating run's id. `boxy-pipeline` keeps `run_id: null` because it has no agent file,
no sprint leg and no `tools.json` — no route at all, which is R4's claim holding for the one
producer it is true of. Verified at agents `0e5e0d2`.]`

`Source: m6 t2c, 2026-08-13. Ordering read at harness d19f4b6; the reproduction above run at that
commit. Filed at the reviewer's direction rather than left as packet prose, per the standing rule
that a deferred finding gets a backlog row in the round it is deferred — and filed as its own row
rather than into BL-151, which is for defects that break nothing today.`

---

### BL-154 — Rig's Cancel kills the direct child only, and transitions nothing (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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

**Appended 2026-08-19 at ds t1a — the matrix serves two consumers with different needs, and a
use case with runnable scripts and no agent is invisible to one and correctly absent from the
other.** *(Appended below the row's own `Source:` stamp, not between it and the body it
attributes.)* This row enumerates three consumers of one artefact; t1a's registry work found
that **two of them do not want the same set**, which bears on any gate this row eventually
proposes.

- **The planner's system prompt** reads `docs/capability-matrix.md` whole. Its unit is an
  **agent**: a section exists because `agents/capability_matrix_<key>.exs` produced it, and a
  section for a use case with no agent would advertise a capability the planner cannot dispatch
  to. For this consumer, `boxy-pipeline`'s absence is **correct**.
- **Rig's Agents catalogue view** shows a human what this repo can do. For this consumer,
  `boxy-pipeline` — six runnable CLIs under `boxy-pipeline/scripts/`, no `agents/` directory at
  all — is a real capability that the view does not show, and its absence reads as "this use
  case does not exist" rather than "this use case has no agent".

So the artefact's scope is unambiguous only once you say **whose** question it answers, and the
two answers differ by exactly the non-agent-bearing use cases. ds t1a **declared** the planner's
reading — `assemble_matrix.SECTIONS` is checked against `docs/use-cases.md` filtered to
agent-bearing use cases, and the predicate is named in the check's failure message — which turns
`boxy-pipeline`'s omission from accidental into declared. **That closes nothing here.** It makes
the omission legible; it does not give the second consumer what it lacks, and it does not answer
this row's question of whether the matrix is gate-worthy.

**No fix proposed.** Specifically it is NOT claimed that the matrix should gain a
`boxy-pipeline` section, nor that Rig's view should read a different artefact. What is claimed is
that a gate designed for one consumer's set will be wrong for the other's, and that the design
question this row holds open now has a second axis.

`Source: ds t1a, 2026-08-19. The three-consumer enumeration is this row's own, above, and is not
re-derived here. What is new is read at agents 7841060: `assemble_matrix.SECTIONS` (9 keys) and
`agents/capability_matrix_*.exs` (9 files) against the ten-row registry; `boxy-pipeline` has no
`agents/` directory (`git ls-files 'boxy-pipeline/agents/*.exs'` -> 0) and six scripts under
`boxy-pipeline/scripts/`. Filed as an append rather than a new row because it sharpens this
row's open question rather than stating a separate one.`

---

### BL-156 — the approval card's step text is written by the planner per run, and nothing checks it (#TBD)
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

`[Answered 2026-08-20 at ds t2. THE INFERENCE WAS CORRECT AND IS NOW A FACT — the second
failure is `boxy-pipeline/tests/test_order_formatter.py::test_no_stale_formulas_beyond_used_rows`.
Found off-territory: ds t2 instruments `boxy-pipeline/scripts/order_formatter.py` for the run
record and ran that file to establish whether its own change had broken anything. Reproducing
command, cap and result:

```
$ timeout 580 python3 -m pytest boxy-pipeline/tests/test_order_formatter.py -q -m dormant
FAILED boxy-pipeline/tests/test_order_formatter.py::test_no_stale_formulas_beyond_used_rows
1 failed, 23 passed in 474.34s (0:07:54)          # AssertionError at :494
```

**Not caused by ds t2, established by control rather than argued.** Re-run with that file's
pre-t2 content restored from a working-copy backup (sha `c1947c0d…`, `grep -c run_record` → 0),
the same single test fails identically in 96s; the working copy was then restored to the t2
version (sha `70d6c645…`, `grep -c run_record` → 2) and `git status --porcelain boxy-pipeline/`
is empty. So the failure predates the instrumentation and is independent of it.

**Item 3's caution was right and is left standing** — the position-counting inference is still
not how this was settled; it was settled by running the file. **This narrows the row and does
not close it**: both failures are now named, the four-hour figure and the
`data/samples/*.pdf` dependency are untouched, and neither failure is diagnosed or fixed.
Established at agents `c73b649`, on a machine that has the client data.]`

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
**Status:** OPEN
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
**Status:** OPEN
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
**Status:** OPEN
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

### BL-164 — a test that hard-codes a value the code derives goes red when the derivation moves, not when the code breaks (#TBD)
**Status:** OPEN
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

**And the conclusion the instance forces, which is stronger than that: the two properties are not
independent — stability gates what the mutation control can see.** An unstable fixture does not only
go red on its own schedule. While it is still green it can make a real defect invisible to the
mutation run against it, because the same coincidence that dates the fixture also supplies the wrong
answer. Here that is measured rather than argued: against the pre-fix fixture, every commit stamped
the same day, a rewriter reading the date off `HEAD` instead of off the resolved commit wrote the
right date by coincidence and **passed all thirteen tests on the day they were green**; against the
repaired fixture the identical mutation kills three. So a mutation run over an unstable fixture can
return a clean *load-bearing* verdict about tests that could not have seen the defect it was probing
for — the instability is not a second problem standing beside the mutation result, it is the thing
that determined it. The order the two controls are owed in follows: establish the fixture is stable,
then read the mutation as evidence about the tests rather than about the day it ran. This is the
follow-up packet's §8, promoted into the row because it is the row's conclusion rather than one of
its measurements.

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
says nothing about whether it is STABLE."* The stability-gates-the-mutation paragraph is that
packet's §8, added to this row on 2026-08-17 at the arbiter's direction — as first filed, the row
held the two properties apart and never said that one gates the other, and the measurement behind
that claim appeared in the packet alone.`

---

### BL-165 — `bl-002` Step 5 states the remove half as a hand enumeration of document kinds, not as the manifest set (#TBD)
**Status:** OPEN
**Kind:** defect · **Census items:** n/a · **Contract:** `CLAUDE.md` (agents) §Definition of done — *the manifest set is the scope of remove-all, and `claude/` is outside it*
**Size:** S · **Priority:** medium
**Section:** process / project knowledge (`prompts/bl-002-refresh-project-knowledge.md`)

Filed 2026-08-18 at the ds cycle's export boundary, stage A, by BL-163's required sweep — which
found it and could not close it, the two being different classes in different units of the file.
Established at agents `7e8602d`, the commit that closed BL-163 and did not touch this text.

**What is wrong.** Step 5 (`:102–113`) prints the operator's instructions, and its remove half reads:
*"upload instructions: in the Claude.ai project, REMOVE the old knowledge files (stale handoff, old
specs/architecture/runbook/protocol/README, old CLAUDE.md), then upload everything in
/tmp/claude-project-export/"*. The standing rule is that the remove is **all of the manifest set** —
`CLAUDE.md` §Definition of done, *"The manifest set is the scope of *remove-all*, and `claude/` is
outside it"*, and the export rule above it, *"Export is remove-all-upload-all against the full
manifest set, never a hash-driven diff"*. Step 5 states neither. It names a parenthetical list of
document kinds — six of them, against a 25-row table — and an operator who follows it literally
removes those and leaves the rest, which is a partial remove: precisely the state post-upload check
3 exists to detect, produced by the procedure's own instruction.

**Why it is not BL-163's defect.** BL-163's two checks were **unscoped** — they said *the store* and
meant one namespace or the other. This says **too little**: it names no namespace, and it
under-reaches rather than over-reaches, so the scoping ruling does not repair it. It is the
enumeration class instead — `CLAUDE.md` §Learning — m6-cloudcost, *"A wiring list's clause can be
right while its enumeration is short — repair it as an incomplete enumeration, not as a missing
clause"* — with the twist that here there is **no clause at all**, only the enumeration, so the
repair is to state the rule and let the export-name column be the list.

**NOT KNOWN, and this row's first step.** Whether the enumeration was ever complete, and against
which boundary. The six kinds named look like a 2026-06-era export set rather than the current 25
rows, but nothing in the file dates them, and the sweep that found this did not chase the history.
Establish that before rewriting, so the fix records what it is replacing.

**Also open, and the reason this is S and not XS.** Whether Step 5 should state the remove as a rule
(*"remove every document whose name appears in the manifest's export-name column, and nothing
else"*) or point at `CLAUDE.md` §Definition of done and carry no restatement. The repo's standing
preference is the pointer — two surfaces disagree at the next amendment — but Step 5 is read by a
human performing an irreversible deletion in a UI, which is the one audience an indirection costs
something. Decide it, do not default it.

**Done when:** Step 5's remove half states the manifest set as its scope, by rule or by pointer with
the choice recorded; the `claude/` namespace's exclusion from *remove-all* is legible to the
operator at the point of the deletion; and the history question above is answered or recorded as
unanswerable.

**Costs:** S. One paragraph, plus the small history check.

**Collides with:** nothing. BL-163 is CLOSED and this does not reopen it. It does not touch BL-143's
open Done-when (ownership and trigger), and it does not touch BL-161.

`[Appended 2026-08-19 at the ds boundary's stage B — **the remove half is not performable by the
tool it now has an actor for.** A second defect in the same Step 5, and it was found by *performing*
the step rather than by reading it. Step 5 states the remove-all-upload-all as an instruction to an
actor with UI-equivalent capabilities; claude-ui's Projects tool **cannot execute it in that
order.** Deleting a top-level document destroys the only handle that permits writing to its path: a
new bare filename is forced into the `claude/` namespace, `./name` normalises to the same, and
`/name` creates a distinct path rather than the original. So remove-then-upload leaves the store
unrecoverable **by that actor** — and upload-over-existing-then-prune, the only order that works,
cannot create a document the store does not already have. Measured 2026-08-18, when the order was
followed literally: all twenty-five documents were removed and none could be written back, and the
human restored them by hand. The boundary record is
`docs/project-knowledge-manifest.md`, §Export boundary — 2026-08-18. **No fix proposed.** Whether
Step 5 gains an actor-conditional procedure, or the upload half is declared the human's, belongs to
**BL-143** and to this row's own open question above, and is not decided here. Note that this
interacts with that question rather than with the enumeration defect this row was filed for: the
enumeration under-reaches, and this says the instruction is unexecutable in its stated order — they
are repaired in the same paragraph and are not the same defect.]`

`Source: BL-163's Done-when sweep, run 2026-08-18 at the ds export boundary stage A over the whole
of `prompts/bl-002-refresh-project-knowledge.md`; the sweep's population, its five examined sites and
its four clears are recorded in BL-163's `[CLOSED 2026-08-18 …]` annotation. Filed as its own row
rather than inside that annotation because a finding recorded inside a row the same commit closes has
a record and no executor — `CLAUDE.md` §Learning — BL-007, the deferred-finding rule's closing
clause.`

---

### BL-166 — `drift_check --strict` is green because of an untracked personal profile export (#TBD)
**Status:** OPEN
**Kind:** defect · **Census items:** n/a · **Contract:** `CLAUDE.md` (agents) §Definition of done — the `drift_check` done-check and its `--strict` invariant
**Size:** S _(proposed)_ · **Priority:** medium _(proposed)_
**Section:** process / gates (`scripts/drift_check.py`, the `payload_fields` check)

Filed 2026-08-19 at the ds cycle's stage B. **Its own row rather than an append to BL-151**, which
is for code findings with no natural home and no discharge condition: this has both. It closes when
the gate resolves the path itself or the repo declares it, and closing it makes the gate
reproducible in a fresh clone and in CI.

**What is wrong.** The `payload_fields` check reads the live harness SQLite database at
`os.environ.get("AETHERIS_DB_PATH")` (`scripts/drift_check.py:492`). On this machine that variable
is exported from `~/.profile:156` — a personal shell profile tracked in neither repository. The
gate is green because of untracked machine state, and **every `drift_check --strict` green
published in this cycle's packets was produced under it.**

**Measured, four arms, all at agents `9b9b274` / harness `8eb960d`:**

| invocation | environment | result | exit |
|---|---|---|---|
| `python3 scripts/drift_check.py --strict` | as inherited | `9 PASS  0 FAIL  0 WARN  7 INFO` | 0 |
| `env -u AETHERIS_DB_PATH python3 scripts/drift_check.py --strict` | variable absent | `8 PASS  1 FAIL  0 WARN  4 INFO` | 1 |
| `AETHERIS_DB_PATH=/nonexistent/aetheris.db python3 scripts/drift_check.py --strict` | set, file absent | `8 PASS  1 FAIL  0 WARN  4 INFO` | 1 |
| `env -u AETHERIS_DB_PATH python3 scripts/drift_check.py` | variable absent, no `--strict` | `8 PASS  0 FAIL  1 WARN  4 INFO` | **0** |

The line is `payload_fields: AETHERIS_DB_PATH not set — skipping live payload sampling`, emitted by
`_warn` (`:494`; `:499` for the set-but-missing form) and promoted to FAIL by `--strict`.

**The Silent-wrong-answer shape, stated as measured rather than as commissioned.** This row was
asked for on the claim that *a bare published green cannot be told apart from one produced without
the variable.* **That is false of `--strict`** — without the variable `--strict` is red, so no
`--strict` green can have been produced without it. It is **true of the bare, non-strict
invocation**, arm 4: with the variable absent it exits **0**, and a done-check publishing only an
exit code cannot tell that from a real pass. The defect that does hold for `--strict` sits one step
over. The green asserts `payload_fields` was validated, and what it was validated against is a
database **outside both repositories** that nothing else can see; two machines running the identical
published command can legitimately disagree, and the summary line names neither the database nor
the fact that one was read. The only signal in the output is the INFO count — **7 against 4** —
which is a figure no reader has a baseline for. So the published green is not a wrong answer; it is
an answer about a different subject than a reader will take it for, and nothing in it says so.

**And the gate is not reproducible where it matters.** Put through the `integration` marker's own
question (`CLAUDE.md` §Definition of done): in a fresh clone at this commit, offline, with no
sibling repository present, `drift_check --strict` **fails**. The `drift_check` sprint case runs
`--strict`, so this reaches CI the first time anything runs it there.

**Two candidate directions, and this row chooses neither.** *(i) The check resolves the path
itself* — derive it from the sibling harness checkout the way the rest of this repo locates
`../aetheris`, so the gate depends on repo layout rather than on environment. *(ii) The repo
declares it where a fresh clone can read it* — `mise.toml`, a tracked env file, or the sprint case
— so the dependency is visible and settable rather than inherited. They differ in what should
happen when the harness DB is genuinely absent, and that is the question that decides between them.

**Done when:** `drift_check --strict` is green in a fresh clone at HEAD with no untracked
environment, **or** the dependency is declared in a tracked file the gate reads and a run without it
is a stated, legible skip rather than a machine-dependent pass — and, either way, a published
`drift_check` done-check says what `payload_fields` sampled.

**Costs:** S. One resolution site plus a test for the absent case.

**Size and priority are proposed, not ruled.** Medium over low on the ground that the row is not
about a wrong answer today but about whether a published green means something a reader can
reproduce, which is the property the whole done-check discipline rests on. Low is defensible if the
gate is held to be operator-local by design; that reading is not taken here.

**Collides with:** nothing. It is not **BL-133** — that row is about where a run's output goes, this
is about whether the run's greenness depends on the machine.

`Source: measured at the ds cycle's stage B, 2026-08-19, at agents `9b9b274` / harness `8eb960d`;
the four arms are this session's own runs. The profile export is cited by path and line only — the
row names no value and needs none, the dependency being the finding.`

---

### BL-167 — run-level completion needs a harness post-run hook; it is not satisfiable agents-side (#TBD)
**Status:** OPEN
**Kind:** gap · **Census items:** n/a · **Contract:** `../aetheris/CLAUDE.md` **Silent-wrong-answer** — *stale/leftover artifacts from a prior run*
**Size:** M _(proposed)_ · **Priority:** medium _(proposed)_
**Section:** harness (`../aetheris/`) — **cross-repo**, with an agents-side consumer

Filed 2026-08-20 at ds t2, **the day it was established**, by the ticket that implemented
BL-153's stamp and found the run-level half of it unbuildable where it stood. **A new row
rather than an append to BL-153**, which is now discharged of everything it was waiting for:
its format, file and reader are ruled and landed. This is the one property those rulings
name that ds t2 did **not** build, did not stub, and does not pretend to.

**What is owed and what exists.** BL-153's second ruling requires *"a writer that runs LAST
UNCONDITIONALLY"*, so that a directory can state whether a **run** — not merely a step — is
complete. ds t2 delivers per-step attestation: every producing step writes
`<use_case>/data/run-records.json` with an `attested_at` set only after that step's writes
have returned, so an interrupted step is legible. What no reader can yet ask is *"did this
run finish?"*, because nothing knows the set of steps a run intended.

**Why it cannot be done agents-side, which is the whole content of this row.** Under an LLM
orchestrator **every step is prompt-invoked**, so a "final step" is a line the model may
skip, reorder, or never reach — and a writer free to skip the stamp is the same defect as a
reader free to ignore it, one step earlier. That alone disqualifies the prompt route. Two of
the six producers have no last-writer position at all, by construction rather than by
oversight:

* **`eduloka`** — its writers are N concurrent sub-agents, one per search term, joined only
  at `wait_for_all` (`eduloka/agents/eduloka_orchestrator.exs:53`, `:105-106`, `:137`). No
  sub-agent is last, and the join is itself a prompt step in the parent.
* **`boxy-pipeline`** — has no agent file, no sprint leg and no `tools.json`. **No program
  knows a run occurred**, so there is nothing that could hold a post-run position. Its
  records carry `run_id: null` for the same reason.

A third consideration rules out the remaining candidate: a writer placed in the *sprint*
does not cover the two Rig paths that reach a use case without passing through it — BL-153's
own R2 established that `sprint.sh` appears nowhere in `rig/src` or `rig/src-tauri`, and
that the Orchestrator and the Tools panel both write into a provider directory directly.

**So the position has to be held by something that observes the run rather than participates
in it** — a harness post-run hook, which would know the run id, the fact that the run ended,
and how it ended, none of which any script in this repo can observe. That is a harness
change and is why this row is filed cross-repo.

**Not established, and named as such.** No design is proposed here. Whether such a hook
should write a run-level record, seal the per-step records, or merely emit an event for a
reader to join against is **not ruled** — nor is what it should do for a run that is
cancelled (see **BL-154**) as against one that fails. Anyone scoping it should also decide
whether the hook fires for sub-agent runs, since eduloka's N sub-agents each have their own
harness run id.

**Done when:** a reader can distinguish a complete run from an interrupted one **for all six
producers**, by a mechanism no prompt line can skip — or it is ruled that per-step
attestation is sufficient and the run-level property is retired, in which case BL-153's
"writer that runs LAST UNCONDITIONALLY" clause is corrected to say so rather than left
standing unmet. **Not** when only the producers that happen to have an agent are covered.

**Costs:** M. The hook is small; deciding its semantics against the cancel path and against
sub-agent runs is the work.

**Collides with:** **BL-153**, which owes the property and is otherwise discharged —
annotated there. **BL-154**, whose cancel path is one of the run endings such a hook would
have to classify, and which is where the status vocabulary question already sits.

`Source: ds t2, 2026-08-20. Established at agents `0e5e0d2` / harness `a6464f4`; the two
producers with no last-writer position were read, not inferred from a neighbour.`

---

### BL-168 — `aetheris_run_id` is declared in five DDL sites across two languages, written by nothing and read by nothing (#TBD)
**Status:** OPEN
**Kind:** defect · **Census items:** 5 code sites + 4 doc lines · **Contract:** `../aetheris/CLAUDE.md` **Silent-wrong-answer** — a column that reads as a provenance link and is always null
**Size:** S _(proposed)_ · **Priority:** low _(proposed)_
**Section:** aetheris-agents (`provenance/`)

Filed 2026-08-20 at ds t2, off-territory: t2 instruments `provenance/scripts/inventory_report.py`
and touches neither the schema nor the scanner. Found while establishing how a run id reaches a
provenance script — the answer being that a column exists for exactly that and nothing fills it.

**The five sites, enumerated rather than counted** (`grep -rn 'aetheris_run_id'` across both
repos, excluding `__pycache__`, `target/`, `node_modules` and `.git`):

| # | site | table |
|---|---|---|
| 1 | `provenance/scripts/init_db.py:31` | `f2_file_index` |
| 2 | `provenance/scripts/init_db.py:47` | `classifications` |
| 3 | `provenance/scripts/init_db.py:60` | `zip_inventory` |
| 4 | `provenance/scripts/init_db.py:74` | `scan_runs` |
| 5 | `provenance/scanner/src/migrations.rs:39` | the scanner's own DDL |

All five are `TEXT` column declarations. **Non-DDL references: zero** — no `INSERT` names it,
no `UPDATE` sets it, no `SELECT` reads it. The positive control for that zero, run with the
same flags over the same tree: `status`, a column that *is* written, returns 11 `INSERT`/
`UPDATE`/`SET`/`VALUES` hits. So the zero is a fact about the column rather than about the
search.

**Four further sites are documentation, and are listed because a fix that touches only code
leaves the docs describing a column that no longer exists**: `docs/provenance/specs.md:30`,
`:46`, `:59`, `:73` mirror the four `init_db.py` declarations, `:30` annotating it
`-- trajectory reference`. (`docs/reviews/provenance-scout-2026-08-03.md` also discusses it
in eight places; that is a dated review record and is **not** to be edited.)

**Already known, and that is part of the finding.** The provenance scout of 2026-08-03
recorded it — *"`aetheris_run_id` written by nothing (Q6). Four tables, zero writes, no
error"* (`:557`), with `SELECT count(aetheris_run_id)` → **0 in all 8** across both DBs
(`:673`), and warned *"Either wire `aetheris_run_id` or soften the claim first"* (`:631`).
It has been unfiled and unfixed since, which is the deferred-finding-with-no-executor shape:
prose in a review record has no owner.

**Why it is worth a row now.** ds t2 gives it a use it did not have. Five tables carry a
column whose name promises a link to a harness trajectory; `provenance/scripts/inventory_report.py`
now takes `--run-id` and stamps it into `provenance/data/run-records.json`, so the identifier
this column was declared for is finally available at the point provenance writes. Either the
column gets wired to it or it should go — what it must not stay is a schema field that reads,
to anyone inspecting the DB, as a provenance link that is simply always null.

**Note the scanner's ids are NOT this.** `scan_runs.id` is the scanner's own run id, written
at `provenance/scanner/src/scan.rs:457` and completed at `:502`; it works and is not in
question. `aetheris_run_id` is a separate column intended for the *harness* run, and it is
the empty one.

**Done when:** either the five sites are written and something reads them, **or** all five
are dropped and `docs/provenance/specs.md`'s four lines go with them. **Not** when only the
code half is done.

**Costs:** S either way. Dropping is XS plus a migration question for existing DBs; wiring is
S and needs the run id threaded to `init_db.py`'s and the scanner's write paths, which is the
same seam `--run-id` opened for the report step.

**Collides with:** nothing. It is independent of **BL-167**, which is about run *completion*;
this is about a run *identifier* that already has a declared home.

`Source: ds t2, 2026-08-20. Enumerated at agents `0e5e0d2`; every line above was opened. The
count of five is this ticket's own derivation and is not carried from the prompt that
requested it, which named the same five.`
