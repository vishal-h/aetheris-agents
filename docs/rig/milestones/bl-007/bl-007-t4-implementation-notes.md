# BL-007 t4 — implementation notes

**Ticket:** BL-007 t4 — TrajectoryView "Fork from here" + provenance banner (agents repo only).
**Watermark:** agents `e652408` (pre-t4 HEAD), harness `eef174f` (reference-only, not touched).
Anything cited beyond that watermark was fresh-read this session.
**Contract refs used:** t3 `fork_run` command contract (specs.md §4 lines 238–258; t3 impl
notes lines 9, 11, 19–23, 58, 62–63); determinism contract §4 "fork guarantee" (`../aetheris/
docs/aetheris/determinism-contract.md:61-101`) for banner copy bounds; frames-vs-forks rule
(`../aetheris/docs/aetheris/research/activegraph-log-is-agent-2026-07.md:133-137`) for UX copy
basis; `rig/CLAUDE.md` UI conventions (camelCase invoke, nested-clickable stopPropagation,
null-not-zero, no-polling, doc-sync).

## Scope delivered

A per-step "Fork from here" affordance in `TrajectoryView.tsx` (offered only on steps with a
`:step_complete` event), a provenance banner on forked runs read from `meta.fork_from`, the
`useFork` action hook wrapping the t3 `fork_run` command, auto-navigation to the child run on
resolve, and the §t5 row (f) whole-interface `TrajectoryMeta` sweep. No Rust touched.

## Files changed

| File | Change |
|---|---|
| `rig/src/hooks/types.ts` | (f) sweep — `seed` retyped, `fork_from?`/`fork_step?` added |
| `rig/src/lib/reconstructTrajectory.ts` | `seedField()` → `number \| null` (forced by the sweep) |
| `rig/src/hooks/useFork.ts` (new) | imperative fork hook, mirrors `usePlaygroundSubmit` |
| `rig/src/hooks/index.ts` | export `useFork` |
| `rig/src/components/modules/harness/TrajectoryView.tsx` | affordance + provenance banner + error strip |
| `rig/src/components/modules/harness/RunList.tsx` | `handleForked` surfacing (HarnessRoute) |
| `docs/rig/specs.md` | `TrajectoryMeta` doc-sync |
| `docs/rig/milestones/bl-007/README.md` | §t4 Touches amendment (doc-first) naming the harness store fix + why (r3 F7) |
| `../aetheris/lib/aetheris/store.ex` (harness) | r3 F7 fix — WAL + `busy_timeout` in `init/1`, `:busy` handled in `run_stmt/3` (cross-repo, human-approved) |

## The (f) sweep — `TrajectoryMeta` vs harness meta writer

Swept the whole interface against the harness meta writer at `eef174f`
(`../aetheris/lib/aetheris/agent/server.ex`), value types confirmed against the `RunConfig`
typespec (`../aetheris/lib/aetheris/run_config.ex`).

| Field | Harness writer (file:line) | Value type (source) | Was | Correction |
|---|---|---|---|---|
| `seed` | server.ex:668 (execute_run) & :939 (resume) | `integer() \| nil` (run_config.ex:194) | `string \| null` | → `number \| null` |
| `fork_from` | server.ex:720 `maybe_add_fork_meta` | `String.t() \| nil` (run_config.ex:196) | *absent* | add `fork_from?: string` |
| `fork_step` | server.ex:720 `maybe_add_fork_meta` | `non_neg_integer() \| nil` (run_config.ex:197) | *absent* | add `fork_step?: number \| null` |
| `sandbox_path` | server.ex:663 (`config.sandbox_path`) | `Map.get(map,"sandbox_path")` no default, config default `nil` (run_config.ex:171,88) | `string` | → `string \| null` |

`resumed?` already correctly optional (only the resume path at server.ex:941 writes it, always
`true`). `fork_from`/`fork_step` are optional and co-present **as keys** — `maybe_add_fork_meta`
(server.ex:717–721) does a single `Map.merge` of both, or omits both when `config.fork_from` is
nil. **Key co-presence is a verified runtime invariant, not an assumption:** of the 1,201
`fork_from`-bearing metas in the dev store, **0** have the `fork_step` key absent. What varies is
the **value**: `fork_from` is guarded non-nil (the `%{fork_from: nil}` clause), so present ⟹
string; `fork_step` carries `config.fork_step` (`non_neg_integer() | nil`), so its value may be
null — 540 of the 1,201 have `fork_step: null` and 661 have an integer. The null-valued 540 are
**all** `replay-source-*` (270) / `verify-*` (270) runs — a pre-BL-007 replay/verify fork
producer (D4-lineage territory), distinct from BL-007's `Fork.from_step`, which writes the
integer step. So two fork-provenance shapes coexist in the store; `fork_step?: number | null` and
the banner's `@ step` guard tolerate both. (This refines review r1 F4 / r2 F5: the 540 do **not**
falsify key co-presence — they falsify value-non-nullness only.)

**Re-verified against real artifacts (review r1 F4).** The initial "all other fields match" claim
was checked against the writer *code* only; a full field-by-field scan of the writer's *output*
(23,729 dev-store trajectory metas) corrected it:
- **`sandbox_path`** — null in **22,726 / 23,729** artifacts (every fresh-overlay fork). The
  writer confirms it: `Map.get(map, "sandbox_path")` has no default and the config default is
  `nil`. Retyped `string | null`. Not rendered in the meta panel, so no render change needed.
- **`fork_step`** — 540 fork artifacts carry `fork_from` (string) with `fork_step: null`. Retyped
  `number | null`; the banner now guards the null case.
- **`model` / `provider`** — observed null in 1,353 artifacts, but **only in hand-authored test
  fixtures** with all-null meta (e.g. `verbose-run-complete-34692`: model/provider/mode/sandbox_path/seed
  all null — clearly a minimal render fixture, not a harness run). The real writer defaults them
  (`provider: Map.get(map,"provider","stub")`, `model: Map.get(map,"model","")` — run_config.ex:153-154),
  so a genuine run never emits null. Per the §t5(f) charter ("sweep against the **meta writer**")
  these stay `string`; widening to `string | null` for fixture-only nulls would misrepresent the
  writer contract. Recorded here rather than silently widened.
- All remaining fields (`mode`, `step_count`, `max_steps`, `started_at`, `finished_at`, `tools`,
  `system_prompt`, `user_prompt`, `overlay_changes`) confirmed matching against both writer and
  artifacts.

**Companion edit (forced by the sweep):** `reconstructTrajectory.ts:78` `seedField()` returned
`string | null` via `String(value)` and is assigned to `meta.seed` at `:132`; retyping `seed`
to `number | null` forced `seedField` to return `number | null` (`Number(value)`, `NaN` → null).
`reconstructTrajectory.ts` is not in the §t4 Touches list but the change is a mechanical
consequence of the type correction, not new behaviour.

**specs.md sync:** brought the §-Trajectory `TrajectoryMeta` block (specs.md:429) into exact
match with the corrected interface — fixed `seed` and `sandbox_path`, added
`fork_from?`/`fork_step?`, and also added the pre-existing-missing `resumed?` (a standing doc gap
surfaced while sweeping). The sample meta at specs.md:115 keeps `"seed": null` and
`"sandbox_path": "…"` (both valid; the demo run is a non-fork ollama run, so `fork_from` is
correctly absent).

**Passthrough verified — no Rust needed.** `commands/trajectory.rs:20,88` types `meta` as
`serde_json::Value` and `.clone()`s it through, so `fork_from`/`fork_step`/integer `seed` reach
the frontend untouched. `trajectory.rs` stays out of Touches. (The diff-view meta enumeration
in `useRunDiff.ts` / `MetaDiffRow` was noted as a possible downstream consumer but is out of
t4 scope — it iterates whatever meta keys are present and is unaffected by the two new optional
fields.)

## Three-state affordance (user-approved this session)

- **(a) forkable step** — group contains `:step_complete` → active "Fork from here" button
  (`GitBranch` icon, `Button` variant `outline` size `xs`). Gate:
  `events.some(e => e.event_type === 'step_complete')` (TrajectoryView.tsx StepGroup) — the
  same idiom already used for `run_complete` in `useHarness.ts:87` / `RunList.tsx`. The `step`
  value is exactly `fork_run`'s `--step N`.
- **(b) non-forkable step** — no `:step_complete` → **no affordance** (chosen over
  disabled-with-why). Justification: matches the determinism contract's mandate that consumers
  "MUST offer fork only on completed steps" (`determinism-contract.md:93`) and the "don't
  over-build" guidance; the terminal text step (which emits `run_complete`, not
  `step_complete`, per t2) is the common non-forkable case and a disabled control on every such
  step is clutter. The education lives in the active button's `title` tooltip.
- **(c) run with zero forkable steps** — no fork buttons anywhere, and no fork banner unless the
  run is itself a fork (`meta.fork_from` present). No special empty state — nothing to build.
- **File-backed path only (review r1 F3).** The affordance is offered only on the file-backed
  view (`canFork` prop: true on the file branch, false on the reconstructed/live branch). A
  running or orphan-swept run has no `trajectory.json` (written atomically at run end), so the
  fork CLI's source-trajectory load would always fail — offering a button there is the
  disabled-button problem in worse clothing (offered-but-always-fails). This is decision (b)'s
  "absence over dead controls" principle applied to a path the decision round didn't enumerate;
  the fix inherits its rationale. Fork points only exist on completed, file-backed runs.

## Fork invocation, in-flight state, error surfacing

- `useFork()` (new hook) mirrors `usePlaygroundSubmit` (`usePlayground.ts:112-139`): imperative
  `fork(runId, step, label?)` → `invoke<string>('fork_run', { runId, step, label })`, sets
  `forking`, on reject sets `error = String(e)` and rethrows. Invoke keys: `runId` (camelCase →
  Rust `run_id`), `step`/`label` single-word safe; omitting `label` → Rust `Option::None`.
- **State lives in `TrajectoryBody`** (not `StepGroup`) so every fork button disables while one
  is in flight: `forking` (any in-flight) disables all; `forkingStep === step` shows the
  `<Loader2 animate-spin/> Forking…` label on the pressed button only. `handleFork(step)` sets
  `forkingStep`, awaits, calls `onForked?.(childId)` on success, clears in `finally` — both the
  navigate and the state writes gated on the mount guard below.
- **Mount guard on resolve (review r1 F1).** A fork blocks for minutes; if the user selects
  another run or leaves the Trajectory tab meanwhile, `TrajectoryBody` unmounts (run change → the
  `fileLoading` branch swaps in `CentredMessage`; tab switch → Radix `TabsContent` unmounts
  inactive content — verified `MainArea.tsx:40-48` has no `forceMount`). The pending promise still
  resolves, but `onForked` lives on the still-mounted `HarnessRoute`, so an unguarded resolve
  would yank the user to the child from wherever they navigated. An `alive` ref
  (`useRef(true)` + `useEffect(() => () => { alive.current = false }, [])`) gates both
  `onForked?.(childId)` and `setForkingStep(null)`. **Designed navigate-away behavior:** the fork
  completes silently in the background and the child appears in Runs on the next refresh (same
  surfacing as the synthesized-summary deviation below); only a user still on the source view is
  auto-navigated. Because `TrajectoryBody` remounts on run change, the guard covers both the
  switched-run and left-tab cases with one ref.
- **Pending UX / quit-during-fork** — honest in-flight labeling only (user-approved). The
  pressed button reads "Forking…" and stays disabled for the full (minutes-long) block; the
  `title` tooltip explains the fork replays the prefix then continues live. **No
  `onCloseRequested` quit guard** — decided against, cost recorded: it would need the leaf fork
  state lifted to window scope (a shared store or app-level state) plus a confirm dialog, a
  cross-cutting change for a leaf feature; the harness orphan sweep already recovers the DB row
  of a fork killed mid-flight. No detach built (out of scope per §t4).
- **Error** surfaced from the rejected promise as a dismissible destructive strip at the top of
  `TrajectoryBody` (`border-destructive/40 bg-destructive/5 text-destructive`, the `ViolationList`
  convention), carrying the CLI stderr the t3 command returns on a non-`done` fork. A failed
  fork is never shown as a silent new run.

## Provenance banner

- Rendered when `meta.fork_from != null` (null-not-zero — only when the field is present), as a
  sibling to the existing reconstructed-source banner slot in `TrajectoryBody`, so it shows on
  **both** the file-backed and reconstructed render paths (the banner is a provenance display,
  independent of the fork *affordance* which is file-backed-only). Copy:
  `Forked from <fork_from>[ @ step <fork_step>]` — the `@ step N` clause is guarded on
  `meta.fork_step != null` (review r1 F4: `fork_step`'s value may be null), so a null-step fork
  renders "Forked from X" with no dangling "@ step". Distinct indigo styling + `GitBranch` icon
  to read as "branch" (the amber banner is reserved for the reconstructed-source signal).
- **Identified by `meta.fork_from`, never `meta.mode`** — CLI forks run in `:record` mode
  (determinism contract §4 / specs.md §4), so a mode badge would read "record", not "fork".
- **Copy is bounded by the determinism contract §4.** The `title` tooltip claims only what the
  contract licenses: "Transcript prefix and seed carried; environment (filesystem, clock) is
  fresh. Post-fork execution is live." — no post-fork-reproducibility claim, per the D1
  non-guarantees (`determinism-contract.md:79-88`). UX framing ("a fork replays the transcript
  then continues live") follows the frames-vs-forks decision rule.

## Surfacing the fork (auto-navigate)

`TrajectoryView` gained an optional `onForked?: (runId: string) => void` prop; on resolve
`handleFork` calls it with the child id. `HarnessRoute` (`RunList.tsx`) passes `handleForked`,
which selects the child and switches to the Trajectory tab so the provenance banner is
immediately visible.

**Deviation — synthesized summary vs honest refetch.** `HarnessRoute` selection is local
component state, not routed, and `useRunList().refetch` is `() => void` (returns nothing).
`handleForked` therefore **synthesizes a minimal `RunSummary`** (`{ run_id: childId, status:
'done', … }`, other fields empty/null/0) and selects it, rather than refetching the list and
finding the real row. This is honest: `fork_run` resolves only on a `done` fork (so
`status: 'done'` is true), and `TrajectoryView` reads all display data from the trajectory
**file's** `meta` — never from the summary — so the synthesized summary's empty fields are
never rendered; its `status: 'done'` only gates the live-poll fallback off. Consequence: the
new run's **row** does not appear in the Runs list until the next manual Refresh (the list is
owned by `RunsContent`'s internal `useRunList`, and lifting it into `HarnessRoute` to
auto-insert the row was judged beyond "no RunList changes beyond surfacing"). The banner-bearing
trajectory — the acceptance signal — is shown automatically. Alternative recorded for a future
ticket: lift `useRunList` to `HarnessRoute`, refetch on fork, select the real summary once it
lands.

## Done-check results

- `cd rig/src-tauri && cargo build` → **exit 0**. No Rust source changed (`git diff --name-only`
  shows 0 `.rs`); the observed recompile of the `app` crate was fingerprint invalidation from
  the branch checkout touching mtimes, not a source change.
- `bun run build` (`tsc -b && vite build`) → **clean** (1909 modules; the `seed` retype leaves
  no `string`-assumption — `reconstructTrajectory` compiles).
- `bun run lint` (`eslint .`) → **clean**.
- camelCase invoke sweep (`rig/CLAUDE.md` grep) → **two benign baseline hits only**:
  `useClassifications.ts:56` (false-positive: the command name `provenance_set_classification_status`
  contains `_status`; args are single-word `{ path, status, reviewer }`) and
  `TrajectoryView.tsx:357` (false-positive: `{ runId: trajectory.run_id }` matches on the
  `run_id` **value**; the key is the correct camelCase `runId`). The new `fork_run` invoke
  (`{ runId, step, label }`) adds no real hit.
- `python3 scripts/drift_check.py` → **0 FAIL**; `--strict` exit 0. The one WARN is the
  exempted `project_knowledge` manifest-staleness WARN (per CLAUDE.md the export boundary is the
  enforcement point; it does not fail `--strict`).

## E2e (human-verified exception — procedure)

Not run by claude-code (needs the Rig UI + dev store). Procedure for the packet:

1. `cargo tauri dev` with `AETHERIS_DB_PATH` pointing at the dev store containing
   `t3-fork-src-452` (known-forkable per t3). **Verify in `cargo tauri dev` specifically —
   dev is the operator's environment and React StrictMode is active there, double-firing
   effects; a production-only smoke masks the StrictMode-class defect that r5 found (a
   cleanup-only mount-guard latched dead on remount).**
2. Harness → Runs → select `t3-fork-src-452` → Trajectory tab.
3. A completed step (has `:step_complete`) shows "Fork from here"; a non-forkable step (e.g. the
   terminal text step) shows **no** button (state b).
4. Click "Fork from here" on step 0 → expect the button to switch to "Forking…" and stay
   disabled (in-flight); all other fork buttons disabled.
5. On resolve → Rig auto-navigates to the child run's Trajectory; the indigo banner reads
   **"Forked from t3-fork-src-452 @ step 0"** from `meta.fork_from`/`meta.fork_step`; the
   transcript prefix (events up to step 0) matches the source.
6. Bad-step / `:step_not_found` path is **not UI-reachable** — the affordance is gated to
   completed steps, so the only way to hit it is a direct backend call; no UI verification
   needed. (A forced failure would surface the CLI stderr in the dismissible error strip.)

## Review round 1 — dispositions

- **F1 [blocking] — mount guard on auto-navigate.** Accepted. Added the `alive` ref + unmount
  effect in `TrajectoryBody`, gating `onForked` and `setForkingStep` (see "Mount guard on
  resolve" above). Verified the unmount actually fires on both triggers: run change
  (`fileLoading`→`CentredMessage`) and tab switch (Radix `TabsContent`, no `forceMount`,
  `MainArea.tsx:40-48`). Navigate-away behavior now recorded as designed.
- **F2 [question] — is the fork-gate field name correct at runtime?** Verified, no change. The
  gate `e.event_type === 'step_complete'` reads the right field on **both** paths:
  (a) file-backed — `trajectory_load` maps the file's `e["type"]` into the struct field
  `event_type` (`trajectory.rs:99`), and the `#[derive(Serialize)]` struct emits JSON key
  `event_type`; (b) reconstructed — `parseEventRow` emits `event_type: row.event_type` from the
  SQLite `EventRow` (`reconstructTrajectory.ts:40`). The pre-existing color map reads the same
  `event.event_type` (`TrajectoryView.tsx:22,90`) and works today — that is the ground truth for
  the field name. So the `"type"` key the reviewer saw is the *file's on-disk* key; Rust renames
  it to `event_type` before it reaches JS. Gate is live, not dead.
- **F3 [non-blocking] — affordance offered on a path where it can't succeed.** Accepted. Added
  `canFork` (false on the reconstructed branch); fork buttons render only on the file-backed
  view. Recorded in the three-state rationale above.
- **F4 [non-blocking] — sweep "all match" falsified by an artifact.** Accepted and extended.
  Retyped `sandbox_path: string | null` (writer-justified: no default, 22,726/23,729 nulls) and
  `fork_step?: number | null` (540 artifacts null; banner guarded). Re-ran the field-by-field
  assertion against 23,729 real metas, not writer-code alone — that also surfaced `model`/`provider`
  nulls, which I traced to test-fixture metas only (the writer defaults them) and deliberately
  **kept** as `string` per the "sweep against the writer" charter, recorded rather than silently
  widened. Details in the sweep section above.

**§7 cross-ticket candidate (if the class recurs, per the reviewer's cross-ticket note).**
*Writer-code reads verify what code intends; an artifact verifies what it does. When real
artifacts exist (this milestone's e2e outputs sit in the dev store), sweep/verification claims
should be checked against them — the artifact is free evidence.* This extends the "Cited-means-read"
discipline from "read the line" to "read the output." F2 (field is `type` on disk but `event_type`
after the Rust rename) and F4 (`sandbox_path`/`fork_step` null in output though the writer's
happy-path types read non-null) are the same lesson from opposite directions — code-intent and
artifact-output disagreeing, with the artifact being authoritative for a **consumer** like Rig.

*Sharpened by r3/r4 into a second, adjacent §7 candidate — **a simulated adversary verifies the
simulation; only the real counterpart verifies the fix.*** The F7 fork-hang fix was called
"verified" in r3 against a simulation that did not reproduce the field failure (wrong connection
mode, already-converted db, a lock that wasn't actually held); r4 showed the true mechanism is a
per-**statement** timing race that no held-connection simulation can deterministically hit. The
worked example: r3 passed on a simulation and was wrong to claim closure; r4 exercised the real
field cell (real Rig) and reframed the mechanism. Rule: when the failure is a race or is
environment-coupled, a passing simulation is evidence about the simulation — reproduce against the
real counterpart, or record the claim as *observed-not-reproduced* with the mechanism named, never
as "verified." Pairs with the artifact lesson: both say *the real thing is the authority.*

*Third §7 candidate — **acting ahead of an unexecuted gate under momentum.*** Two instances this
ticket, same muscle, different artifact: (1) the pre-t4 "rider slip" — editing a doc ahead of the
gate that should precede it; (2) post-r4 — pushing both `bl-007-t4` branches on a "push both
branches" instruction before the full GUI e2e (the acceptance gate) was reported green, inverting
the agreed reorder → gates → e2e → commit → push sequence. Both were recoverable because the
held-push / held-merge discipline caught them (nothing reached `main`; closure is the ff-merge,
which stayed held). Rule, if a third instance appears at t5, promoting as one line: *no action
past a gate until that gate has run and its result is on the record* — covering doc-order gates,
test gates, and publish/merge gates alike. (Ownership recorded as-is in the review file r4.)

*Fourth §7 candidate (sharpest, now a complete worked example) — **one symptom, three faces:
separate symptom from mechanism by direct capture in the operator's own environment.*** The
"fork hangs" symptom (rounds 3–5) had three mechanisms — a harness `:busy` crash, an `await_run`
poll-forever, and a StrictMode-dead mount-guard. Each round's capture executed the *previous*
theory and moved on; a **real** fix shipped for face 1 and was mistaken for the fix of the
observed symptom, which was actually face 3 — a bug my own face-1-adjacent fix (F1) introduced.
What finally separated them was capturing in the operator's real environment (`cargo tauri dev`,
StrictMode on) rather than a simulation or a production smoke. Rule: when one symptom admits
multiple plausible mechanisms, do not treat the first real defect you fix as closure — reproduce
the *symptom* in the operator's environment and confirm the fix kills *that*, because a correct
fix for a real defect can still be the wrong fix for the symptom. Subsumes the
simulation-verifies-simulation candidate as its most complete instance.

## Review round 2 — dispositions

- **F5 [non-blocking] — chase the "co-presence" claim into every doc that adopted it.** Done, and
  the artifact sharpened the claim rather than merely deleting it. Checked all three carriers —
  t4 notes (f)-sweep paragraph, `types.ts:218-219` comment, `specs.md:445` — plus a repo-wide
  `grep` for `co-present|together|omits both` (no other doc adopted it). All three already
  distinguished **key** co-presence from **value** nullability post-r1, so none asserted the
  falsified form. Went further and *verified* key co-presence against the store: **0 of 1,201**
  `fork_from`-bearing metas have the `fork_step` key absent — so key co-presence is a genuine
  runtime invariant; only value-non-nullness was false. Updated the sweep paragraph to state the
  0/1,201 result explicitly so no future reader reads the 540 null-**values** as key-absence.
- **F6 [question] — which producer wrote the 540 `fork_from`-with-null-`fork_step` metas?**
  Answered cheaply and confirmed. The 540 are exactly `replay-source-*` (270) + `verify-*` (270)
  — a pre-BL-007 replay/verify fork producer (D4-lineage territory, plausibly `Eval.AB`), distinct
  from BL-007's `Fork.from_step` (the 661 integer-`fork_step` metas). Recorded in the sweep
  paragraph and carried to open items for t5's backlog as "two fork-provenance shapes coexist in
  the store."

## Review round 3 — Finding 7 (fork hang) + Finding 8 (gate)

**F7 [blocking] — fork children complete `done` but the invoke never resolves.** Root-caused
to a **latent harness defect**, surfaced (not caused) by t4 being the first feature to run
`mix aetheris fork` while Rig holds a concurrent read handle on the same SQLite file.

*Reproduction (evidence).* Rig-closed, the exact `fork.rs` argv against `t3-fork-src-452`
(stub provider, step 0) ran clean ×3 (EXIT 0, ~1.23s each, no orphan residue) — reproducing t3's
success, so nothing in the fork path regressed. Simulating Rig's read handle (a held SHARED read
lock) made the fork **crash** in ~3s: `** (WithClauseError) no with clause matching: :busy` at
`store.ex:1727` (`run_stmt/3`), on the fork's first write (`upsert_run status:"running"`).

*Mechanism (named).* `Aetheris.Store` is a singleton GenServer with one connection opened with
**no `journal_mode=WAL` and no `busy_timeout`** (`store.ex:564-576`) → SQLite defaults
`journal_mode=delete` (verified) + `busy_timeout=0`. In rollback-journal mode any concurrent
reader blocks a writer's exclusive lock; with `busy_timeout=0`, `Exqlite.Sqlite3.step/2` returns
the bare atom `:busy` immediately; `run_stmt/3` matched only `:done | {:error, _}`, so `:busy`
fell through to a `WithClauseError` and crashed the singleton `Store`.

*Two faces, one cause.* I reproduced the **crash** face (contention on a start-path write → CLI
exits 1 → invoke rejects). The human saw the **hang** face: `await_run` (`run_helpers.ex`) is a
poll-forever loop (`Process.sleep(200)` + `Store.get_run`, no timeout/cap); when contention kills
the child's terminal `status:"done"` write, `get_run` returns `"running"` forever → the CLI never
prints → invoke never settles. Boot-time DDL/sweep writes can also block before any log ("printed
nothing"). *State variable (why t3 passed, now hangs):* BL-003's boot orphan sweep (`0188a90`)
added conditional startup **writes**; combined with the always-present WAL/busy_timeout gap, the
hang appears only when a concurrent reader (Rig open) or a cure-able `running` row is present
during a write — neither held at t3's e2e.

*Fix (harness, human-approved cross-repo amendment — §t4 Touches amended doc-first).* Three
changes in `../aetheris/lib/aetheris/store.ex`, branch `bl-007-t4` off `eef174f`:
1. `init/1` — `PRAGMA journal_mode=WAL` (readers never block writers; Rig is a reader).
2. `init/1` — `PRAGMA busy_timeout=5000` (residual contention waits, not immediate `:busy`).
3. `run_stmt/3` — handle `:busy → {:error, :busy}` so a residual busy degrades gracefully
   instead of crashing the singleton `Store` (and every run sharing it).

*Verification.*
- **Before/after, apples-to-apples** (same held SHARED read lock): before = EXIT 1 / `WithClauseError`
  crash; after = **EXIT 0 in ~1.04s, clean run_id, 0 `WithClauseError`**, no orphan residue.
- **WAL took**: `PRAGMA journal_mode` = `wal` (persistent), fork still EXIT 0.
- **Harness gate set green**: `mix format --check-formatted` exit 0; `mix credo --strict` no issues;
  `mix test` **868 tests, 0 failures**; integration fork path (`--include integration
  --include requires_worker`) **7 tests, 0 failures**; `mix dialyzer` **0 errors**.
- **Agents gates unchanged**: drift `0 FAIL` / `--strict` exit 0; the README §t4 amendment is the
  only agents-repo change this round.

*Condition dispositions (the five attached to the approval).*
1. **Local disk** — confirmed: `priv/` is `/dev/nvme0n1p2`, **ext4** (`df -T`/`findmnt`). WAL valid.
   (The DuckDB-over-VPN corpus is a different DB, irrelevant here.)
2. **Read-side WAL vs Rig's `SQLITE_OPEN_READ_ONLY`** — verified empirically at the SQLite layer
   (the semantics Rig's rusqlite read-only connection depends on): a read-only connection
   (`mode=ro`) reads the WAL db (a) with **no writer and no `-shm`/`-wal` sidecars** present
   (849 runs read — the Rig-idle case), and (b) **held open + continuously reading while a fork
   writes concurrently** — the fork completed EXIT 0 and the reader survived. So WAL holds; the
   fallback (busy_timeout + `:busy`-handling alone, no journal-mode change) was **not** needed. The
   final Rig-GUI read-side check (Runs list / trajectory load with the CLI writing concurrently)
   is part of the human e2e, condition-2's empirical launch. Known WAL property, documented not
   fixed: a read-only connection cannot *recover* a dirty `-wal` left by a harness crash with no
   live writer — resolved on the next harness write (which recovers it); realistic Rig usage
   (TEST A/B) is unaffected and the pre-fix behavior in that window was strictly worse (crash).
3. **Doc-first** — the §t4 Touches amendment (`../aetheris/lib/aetheris/store.ex`, one line + why)
   landed in the README before the harness edit; both commits held for the human.
4. **Scope = exactly three changes** — harness diff is `store.ex` only, +13 lines. `await_run`'s
   missing timeout was **not** touched (see backlog row (i)).
5. **Observed-combination reconciliation (done rows visible while the spinner spun).** Rig and the
   fork CLI hold **separate** SQLite connections in **separate OS processes**. Within one CLI
   process a committed `"done"` is always seen by that process's own `await_run` on the next poll
   — so a spinner that never resolves means *this* fork's `"done"` never committed (its child
   crashed on the contended write), and its row is stuck `"running"`. The `"done"` rows Rig
   displayed are almost certainly **earlier successful presses** (or the source), read fresh by
   Rig's independent connection — not the hung fork's. This reconciles the observation without a
   third face. **Residual uncertainty acknowledged**: I cannot prove which press produced which
   row from here; the post-fix full e2e is the adjudicator — if the combination recurs after the
   fix (which removes the crash so `"done"` lands and the loop terminates), a third face exists.

**F8 [question] — did the `isForking` gate hold across four presses?** Yes. `forking` disables all
fork buttons within a `TrajectoryBody` mount and resets only on promise-settle, remount, or app
restart. Relayed answer (confirmed with the human): the four presses were the **hang** face —
stuck "Forking…" spinner, **no** red error strips (so no rejection/crash surfaced to Rig), and the
repeat presses came via **navigating to the Runs tab and back**, which remounts `TrajectoryBody`
and resets the mount-local `forking` — **no app restarts**. So the gate held as designed; the
mount-local reset (intended, per the quit-during-fork decision) explains the repeats. Note this is
consistent with F1's mount-local model and is not a defect — a cross-mount in-flight guard was
explicitly out of scope (would need lifted/window-scope state).

## Review round 4 — the race model + honesty correction

**F9/F10 [blocking/non-blocking] — r3's "verified" was over-claimed; the field hang
reproduced post-fix in a bare shell with Rig open.** Owned. r3's contention "proof" rested
on a flawed simulation: a **read/write** Python connection (not Rig's `SQLITE_OPEN_READ_ONLY`),
run against a db my own first post-fix fork had **already converted to WAL** (so it tested
steady-state WAL, never the delete→WAL moment), and Python releases the SHARED lock when a
`SELECT` finishes stepping (so the "held" lock wasn't held). A simulation that passes where the
field fails verifies the simulation, not the fix.

**The real mechanism — a per-statement timing race (not a held-connection block).** SQLite
locks are per-**statement**, not per-connection: Rig's read-only handle holds a SHARED lock only
while a read is *in flight*. So contention between a harness write and Rig is a **timing race** —
the fork's `EXCLUSIVE` commit crashes/stalls only if it lands in the window of an in-flight Rig
read. This reframes everything: it explains the **intermittency** (t3 passed, t4 sometimes hangs),
why **held-connection sims can't reproduce it** (the lock releases between statements), and the
field observation that Rig **denied a journal-mode conversion at one instant** (`database is
locked`) yet **permitted a fork 5 min later** on the same connection — per-statement, not
per-connection.

**Verification status — honest.** The full field cell (**delete-mode + Rig open + current
tree**) was exercised: press 1 = the human's real-Rig fork (clean, EXIT 0); presses 2–3 = an
adversarial reconstruction here — delete-mode scratch with three processes firing **continuous**
in-flight reads while the fork ran — both **EXIT 0** (~1.5s, slightly slowed as `busy_timeout`
absorbs collisions), mode stayed `delete`, no wedge, capture armed (no `erl_crash.dump`). The
idle real store converted to `wal` (completion 1). **The field hang is recorded
observed-not-reproduced**: I could not reproduce it under simulation (held *or* hammering), which
is consistent with — not contradicted by — the race model (my sims can't deterministically hit
the sub-second collision window). The definitive adjudicator is the human's final GUI e2e; if a
wedge recurs, the capture procedure (SIGUSR1 → `erl_crash.dump` "Current call", `lslocks`,
`PRAGMA journal_mode` at hang time) names the blocking call at file:line.

**Disposition applied (round 4).**
- **`busy_timeout` reordered FIRST**, then `journal_mode=WAL` — so `busy_timeout` also bounds the
  WAL-conversion attempt (removing the `busy_timeout=0` window r3 introduced), and `:busy`
  handling in `run_stmt/3` remains the **load-bearing** crash/hang preventer.
- **WAL kept, opportunistic (with comment).** Justified under the race model: WAL converts at an
  idle instant (proven — the real store went `wal`) and can't while reads are in flight (stays
  `delete`), so "opportunistic" is coherent — it removes contention entirely whenever the store
  is idle at init, while the fix does **not** depend on WAL taking. Still exactly three functional
  changes (busy_timeout, journal_mode=WAL, `:busy` handling), reordered — scope held (condition 4).
- **Gates re-run green** post-reorder: `mix format` 0 · `credo --strict` no issues · `mix test`
  **868/0** · store+fork+integration **23/0** · `dialyzer` **0**; agents drift `0 FAIL`/strict 0.

## Review round 5 — the actual bug (StrictMode-dead mount-guard)

**F9 [blocking — resolved] — the GUI "spinner-forever / no-navigate" symptom was my own F1
mount-guard, not the harness.** Root cause, verified first-hand: `<StrictMode>` wraps the app
(`main.tsx:9`); the F1 guard was written **cleanup-only** —
`useEffect(() => () => { alive.current = false; }, [])` (`TrajectoryView.tsx:336`) — so the effect
**body never re-armed** `alive.current = true`. React StrictMode double-invokes effects in dev
(mount → cleanup → remount), latching `alive.current` to `false` from the first render. Both
`onForked` (navigate, :349) and `setForkingStep(null)` (spinner-clear, :353) were gated on the
dead ref → **no navigate, spinner forever, every press, in dev, always** — the exact observed
symptom, zero residue. Nine missing characters in an effect body.

Fix (3 lines): StrictMode-safe effect — set `alive.current = true` in the **body**, cleanup sets
false — and **narrow the guard to `onForked` only**: the spinner-clear now always runs (a state
set on an unmounted component is a React 18/19 no-op), so it can never strand again; only the
navigate stays mount-guarded (F1's real intent — don't yank a navigated-away user).

**Three faces, one symptom (§7 worked example).** The "fork hangs" symptom had three distinct
mechanisms across five rounds: (1) the harness `Store` `:busy` crash under a per-statement lock
race — a real latent defect, really fixed (WAL / busy_timeout / `:busy`, harness `059c92e`);
(2) `await_run`'s poll-forever loop — the amplifier, backlog (i); (3) **this** StrictMode dead
mount-guard — the actual cause of the GUI symptom. Each round's capture evidence executed the
prior theory; the face-1 fix was real but was *verified against the wrong face* until the live
GUI capture (the StrictMode grep) separated symptom from mechanism. The face-1 and face-3 fixes
both ship — they fix different real things — but only face 3 explains the operator's observation.

**F10 answer (mtime, not guess).** `fork-ceb84dfea946c04f` mtime `18:36:53`; newest child
`fork-bbef9485ebbdc55f` `18:54:41` — both real completed forks from different GUI presses. Every
press *did* land a child (the harness fork works); the dead ref merely suppressed navigation.
"Stale from an earlier press" was directionally right (ceb84df is from an earlier press) but
undersells it — it is a genuine completed fork, confirming the fork mechanism and isolating the
bug to the UI navigate/spinner.

Gates: frontend `bun run build` + `bun run lint` + camelCase sweep (2 benign) green. No Rust, no
harness this round (agents-repo frontend only).

## Review round 6 — acceptance close

Full GUI e2e passed against the shipped tree (agents `4641527`; harness `059c92e`): press 1
(banner + navigate + prefix through step 0), presses 2–3 adversarial (full cycle each, one child
per press — the button re-enabling on return confirmed the StrictMode-safe `alive` reset in the
field), error path via real-run forks (rejection → red strip, no silent run; the failures were the
live runtime answering truthfully, per the determinism contract), Bonus 2 (reconstructed view, no
fork buttons). Bonus 1 recorded **not-reachable-with-trigger** — the 544 `fork_step:null` forks are
trajectory-file-only (pre-BL-007 replay/verify, D4-era), not in the runs table, so unselectable;
the guard is code + type verified. Finding 10 closed empirically (mtimes + one-child-per-press).

**Cosmetic fold applied:** the "Fork failed: fork failed:" double prefix — `useFork` now strips
the redundant leading `fork failed:` from `fork_run`'s message (`fork.rs:68`), leaving the strip's
"Fork failed:" label as the single frame (frontend-only; build+lint+sweep green).

**t4 closed** on the ff-merge to main (both repos). Two real defects fixed on their own merits
(store `:busy` crash — harness `059c92e`; StrictMode alive-latch — agents `4641527`); one face
recorded observed-not-reproduced; F3 error contract exercised in the field; four §7 candidates
banked.

## Open items / carries

- Fork **label** not surfaced by Rig (`harness_list_runs`/`harness_get_run` read label from
  `config_json`, which `encode_config` strips) — pre-existing Rig defect flagged at t3, not a
  t4 concern; the fork invoke omits `label` for now. Carry to t5 / standalone Rig ticket.
- Runs-list row for a fork appears only on manual Refresh (see surfacing deviation above) —
  candidate for the honest-refetch follow-up.
- `reconstructTrajectory` does not populate `fork_from`/`fork_step` from `config_json`; a fork
  viewed via the reconstruct path (file missing) would not show the banner. Acceptable — a
  just-completed fork always has a trajectory file. Noted for completeness.
- **Two fork-provenance shapes coexist in the dev store (t5 backlog / D4-lineage carry).**
  BL-007's `Fork.from_step` writes an integer `fork_step` (661 metas); a pre-BL-007 replay/verify
  producer (`replay-source-*`, `verify-*` — 540 metas) writes `fork_from` with `fork_step: null`.
  Rig tolerates both (type + banner guard), but any lineage/fork-list view (D4, deferred) should
  carry this as a fact — the store is not single-shaped. Surfaced by r2 F6.
- **(t5 backlog row (i)) `await_run` has no timeout/cap — a never-landing terminal status spins
  the CLI forever** (`../aetheris/lib/aetheris/cli/commands/run_helpers.ex`, `Process.sleep(200)` +
  `Store.get_run`, no bound). This was the *amplifier* of F7's hang face — with F7's `:busy` crash
  fixed and contention removed, statuses land and the loop terminates, so it is not part of the
  emergency fix (scope stayed at the three store changes, condition 4). But it remains a latent
  resilience defect: any future cause of a stuck non-terminal status hangs the CLI (and any Rig
  invoke wrapping it) with no timeout. Resilience work for t5, not this ticket. Surfaced by r3 F7.
- **(t5 backlog row (j)) WAL / connection-lifecycle, since WAL is kept opportunistic.** Follow-ups
  for a t5 look: (a) WAL auto-checkpointing / `-wal` growth when Rig holds a long read snapshot;
  (b) a read-only connection cannot *recover* a dirty `-wal` left by a harness crash with no live
  writer (resolved on the next harness write, but Rig reads may fail in that window); (c) whether
  to make WAL's success/failure observable (log the post-pragma `journal_mode`) rather than silent.
  None block t4; the load-bearing fix (`busy_timeout` + `:busy` handling) is independent of WAL.
  Surfaced by r4.
