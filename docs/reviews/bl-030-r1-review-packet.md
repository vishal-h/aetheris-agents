# BL-030 r1 — completion transition (folds BL-063) — review packet r0

**Rig-only.** `aetheris-agents` @ **4bf0fd6**. Tree clean. Branch `main`.
Harness untouched this round (still `f79365a`).

Follows the BL-030 early-return fork (packet `docs/reviews/bl-030-review-packet.md`,
review `docs/reviews/bl-030-review.md`).

**Invariant under test:** a fork's real metadata — id, provenance banner,
`started_at`, duration — must appear without a manual re-mount once the run
completes in place.

---

## 1. Done-check

### 1a. Scout — the data-availability seam (the ticket's precondition)

Both questions were answered from source and confirmed against live data
**before** a mechanism was chosen. This section is the evidence, not a summary.

**(a) Does `runs.config_json` carry `fork_from`/`fork_step`? — Yes.**

`encode_config`, `../aetheris/lib/aetheris/agent/server.ex:759-768`, verbatim:

```elixir
  defp encode_config(config) do
    config
    |> Map.from_struct()
    |> Map.delete(:stub_responses)
    |> Map.delete(:coordinator_pid)
    |> Map.delete(:blackboard_pid)
    |> Map.delete(:label)
    |> Map.delete(:max_duration)
    |> Jason.encode!()
  end
```

Five fields stripped; `fork_from`/`fork_step` are `RunConfig` fields and are not
among them. Confirmed against a live row rather than inferred:

```
$ sqlite3 priv/aetheris.db "select config_json from runs where run_id='fork-d0b6042bcb44c369';"
has fork_from: True => fixture-unlabelled-fork-CbZX6w
has fork_step: True => 0
has fork_context: True (len 3)
all keys: ['allow_escalation', 'context_strategy', 'cpu_quota_percent', 'env',
'fork_context', 'fork_from', 'fork_step', 'max_context_steps',
'max_identical_tool_calls', 'max_spawn_depth', 'max_steps', 'max_tokens',
'max_wait_ms', 'mcp_servers', 'memory_limit_mb', 'mode', 'model', 'orb_id',
'overlay_base_dir', 'pre_tools', 'provider', 'run_id', 'sandbox_path',
'schedule', 'seed', 'spawn_depth', 'stop_sequences', 'store_prompts',
'system_prompt', 'temperature', 'tool_choice', 'tools', 'top_p', 'user_prompt']
```

`RunDetail.config` is already the raw `config_json` string
(`rig/src-tauri/src/commands/harness.rs:280-287`), so provenance **and** the real
`started_at` were reachable during streaming all along — nothing consumed them.

**(b) Is the trajectory file written before or after the `run_complete` event? —
The event precedes it; the status follows it.**

| # | what | where |
|---|---|---|
| 1 | `run_complete` **event** appended to SQLite | `loop.ex:267` |
| 2 | loop returns | |
| 3 | `trajectory.json` written — tmp, then **atomic rename** | `server.ex:680` → `file.ex:37-38` |
| 4 | `runs.status` set terminal | `server.ex:456-465` |

`server.ex:680-684`, verbatim:

```elixir
    Aetheris.Trajectory.File.write(config.run_id, events, meta)

    case result do
      :ok -> GenServer.cast(server_pid, {:run_complete, :done})
      {:error, reason} -> GenServer.cast(server_pid, {:run_failed, reason})
    end
```

`file.ex:37-38`, verbatim:

```elixir
    with :ok <- File.write(tmp_path, Jason.encode!(payload)),
         :ok <- File.rename(tmp_path, file_path) do
```

**Decision this forces:** a reload fired on the `run_complete` **event** races the
file write — the event is durable in SQLite before `File.rename/2` is called, so
the hazard the ticket suspected is real, not theoretical. A reload gated on the
run row's **terminal status** cannot race, because the status flip strictly
follows the completed rename. The mechanism is status-gated and **no retry is
used** (see §4).

### 1b. Pure-logic verification, and its mutation check

Rig has no frontend test runner — `package.json` has no `test` script and no
vitest/jest dependency, verified. `reconstructTrajectory` is a pure function with
type-only imports, so it was executed directly under `bun` against **the exact
summary `RunList.handleForked` synthesizes** (`started_at: ''`, `status:
'running'`, `label: ''`):

```
$ bun run verify_reconstruct.ts   # against HEAD (4bf0fd6)
PASS  started_at comes from the run row, not the synthesized empty string
PASS  started_at parses to a valid Date (no "Invalid Date")
PASS  finished_at comes from the run row
PASS  duration computes (TrajectoryBody formula) = 12s
PASS  fork_from present while running (banner renders pre-file)
PASS  fork_step present while running
PASS  isFork gate (meta.fork_from != null) is true
PASS  finished_at empty while running
PASS  non-fork has no fork_from (banner stays hidden)
PASS  null detail degrades to empty started_at, no throw
PASS  null detail has no fork_from

ALL PASS

$ # mutation: revert the operand order to the pre-fix form
$ #   started_at: run?.started_at ?? detail?.started_at ?? ''
FAIL  started_at comes from the run row, not the synthesized empty string  (got: "")
FAIL  started_at parses to a valid Date (no "Invalid Date")  (got: "")
PASS  finished_at comes from the run row
FAIL  duration computes (TrajectoryBody formula) = 12s  (got: undefined)
PASS  fork_from present while running (banner renders pre-file)
PASS  fork_step present while running
PASS  isFork gate (meta.fork_from != null) is true
PASS  finished_at empty while running
PASS  non-fork has no fork_from (banner stays hidden)
PASS  null detail degrades to empty started_at, no throw
PASS  null detail has no fork_from

3 FAILED
```

The mutation restores the pre-fix operand order and reproduces the reported
defect exactly: `started_at: ""` → invalid `Date` → duration `undefined` (the
duration row is gated on `meta.started_at && meta.finished_at`). Three checks
flip; the fork-provenance and degradation checks are correctly unaffected, since
they are a different fix.

The script is **scratch, not committed** — adding a test runner is outside this
ticket. It is reproduced verbatim in §5 so the reviewer can re-run it.

### 1c. Rig gate line — @ 4bf0fd6

```
--- bun run lint ---
$ eslint .
(eslint printed no findings = clean)

--- bunx tsc -b ---
(no output = clean)

--- bun run build ---
dist/assets/geist-latin-ext-wght-normal-DMtmJ5ZE.woff2   15.30 kB
dist/assets/geist-latin-wght-normal-Dm3htQBi.woff2       28.40 kB
dist/assets/index-DL7BOxH0.css                           49.19 kB │ gzip:   9.09 kB
dist/assets/index-DWg-Px2M.js                           447.63 kB │ gzip: 124.49 kB

✓ built in 703ms

--- cargo test ---
running 22 tests
test result: ok. 21 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.21s
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Rust untouched this round; `cargo test` run anyway (off-territory gate rule). The
one `ignored` is pre-existing (`live_store_demo_01…`, requires `AETHERIS_DB_PATH`).

### 1d. `drift_check --strict` — post-commit, @ 4bf0fd6

```
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 48 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[WARN] project_knowledge: docs/rig/specs.md stale — manifest=c39bf7e current=b5e8eee
[WARN] project_knowledge: docs/rig/architecture.md stale — manifest=d82cf7e current=c0977c2
[WARN] project_knowledge: docs/rig/runbook.md stale — manifest=d0690a6 current=7d6013a
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=6a8a32e current=a29d5a4
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=915d582 current=ae0c510
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=dd12dbb current=1ab24d8
[PASS] command_fields: 10 documented §4 structs (54 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  6 WARN  7 INFO
```

**0 FAIL. 6 WARN, all `project_knowledge` manifest-staleness** — the documented
strict-mode exemption; exit 0. Named individually:

| file | manifest | current | from this round? |
|---|---|---|---|
| `docs/rig/specs.md` | c39bf7e | 4bf0fd6 | no — BL-030 r0 (§4 rewrite), re-stamped by this commit |
| `docs/backlog-2026-06.md` | 6a8a32e | a29d5a4 | no — BL-030 r0 closure entry |
| `docs/aetheris/runbook.md` | 915d582 | ae0c510 | no — BL-030 r0 |
| `docs/rig/architecture.md` | d82cf7e | c0977c2 | no — pre-existing |
| `docs/rig/runbook.md` | d0690a6 | 7d6013a | no — pre-existing |
| `docs/aetheris/determinism-contract.md` | dd12dbb | 1ab24d8 | no — pre-existing |

No **new** staleness from this round: this commit touches no manifest-tracked doc
except by re-stamping `specs.md`'s current hash, which was already stale.
`specs.md` §4 needed no edit — the command's name, signature and struct are
unchanged, which is why checks 2 (`tauri_commands`) and 9 (`command_fields`) pass
untouched. The behavioural prose it carries describes `fork_run`, which this round
does not alter.

### 1e. Manual GUI pass — **outstanding, and it is the gate**

Unchanged in kind from r0 and *more* load-bearing here: this round is entirely
frontend, and §1b covers only the pure reconstruction function. **Nothing in §1
proves the reload fires in a browser.** Specifically unverified without the GUI:

- that `useRunDetail`'s poll observes the status transition and stops;
- that `reload()` fires and the view flips from reconstructed to file-backed
  **in place**, without a `Loading…` flash;
- that the amber "live — reconstructed from events" banner disappears.

**Re-run arm 2 of the BL-030 GUI pass**, extended per this ticket's done-check:
after a fork completes with **no tab-out/in** — the provenance banner renders,
`started_at` shows a real date (no "Invalid Date"), Duration renders, and the
status reads `done`. Arms 1, 3 and 4 from the r0 packet are unaffected by this
change but come along for free in the same session.

---

## 2. Diff — `aetheris-agents` @ 4bf0fd6 (notes file inlined in §3, not repeated here)

```diff
diff --git a/rig/src/components/modules/harness/TrajectoryView.tsx b/rig/src/components/modules/harness/TrajectoryView.tsx
index 840f16a..556a94c 100644
--- a/rig/src/components/modules/harness/TrajectoryView.tsx
+++ b/rig/src/components/modules/harness/TrajectoryView.tsx
@@ -229,7 +229,7 @@ interface Props {
  */
 export function TrajectoryView({ run, onForked }: Props) {
   const runId = run?.run_id ?? null;
-  const { trajectory: fileTrajectory, loading: fileLoading, error: fileError } =
+  const { trajectory: fileTrajectory, loading: fileLoading, error: fileError, reload } =
     useTrajectory(runId);
 
   // Only reach for the event stream once the file load has failed. Gating the
@@ -237,8 +237,23 @@ export function TrajectoryView({ run, onForked }: Props) {
   // the extra queries. Poll while the run is live so the view appends events.
   const fileMissing = fileError !== null;
   const fallbackRunId = fileMissing ? runId : null;
-  const events = useRunEvents(fallbackRunId, { polling: run?.status === 'running' });
-  const detail = useRunDetail(fallbackRunId);
+
+  // Poll the run row whenever the fallback is engaged. Not gated on a status of
+  // our own: `useRunDetail` stops itself the moment the row reads terminal, and
+  // gating it on the status it is the source of would be circular. The cost when
+  // the fallback engages for an already-terminal run (a BL-003-swept orphan) is
+  // one extra fetch before it stops. A completed run with a file never gets here
+  // at all — `fallbackRunId` stays null — so BL-005's "completed runs unaffected"
+  // gating is intact.
+  const detail = useRunDetail(fallbackRunId, { polling: fallbackRunId !== null });
+
+  // The *real* run row is the authority on status, not the summary we were
+  // handed. A run navigated to straight from a fork carries a synthesized
+  // summary (RunList `handleForked`) whose `status` is a seed that never
+  // changes; reading the row is what lets a run finishing in place be noticed.
+  // Falls back to the prop until the first row arrives.
+  const liveStatus = detail.data?.status ?? run?.status;
+  const events = useRunEvents(fallbackRunId, { polling: liveStatus === 'running' });
 
   // Preserve the interrupted-write / corrupt-file signal the runbook documents:
   // the banner reports the file as "unavailable" generically, so log the actual
@@ -249,6 +264,29 @@ export function TrajectoryView({ run, onForked }: Props) {
     }
   }, [fileError, runId]);
 
+  // Completion transition (BL-030 r1). A run being watched writes its
+  // `trajectory.json` only at the end, so the view is in reconstructed mode by
+  // the time the file appears and would otherwise never read it — the run's real
+  // provenance, started_at and duration stayed hidden until a manual tab-out/in.
+  //
+  // The trigger is the run row reaching a **terminal status**, not the
+  // `run_complete` event, and that choice is the whole race story. The harness
+  // appends `run_complete` to SQLite inside the loop (`loop.ex:267`), *then*
+  // writes the file (`server.ex:680`, tmp + atomic rename), *then* sets the
+  // status (`server.ex:456`). Reloading on the event would race the write and
+  // land back on `fileMissing`; reloading on the status cannot, because the
+  // status flip strictly follows the completed rename. No retry is needed, and
+  // none is used — if the load still fails at terminal status the file genuinely
+  // is not there (a failed write, a swept orphan) and staying reconstructed with
+  // the terminal banner is the correct final state, which `reload` preserves.
+  //
+  // Generalizes beyond forks: any run watched live through its own completion
+  // gets the same in-place transition.
+  const isTerminal = liveStatus !== undefined && liveStatus !== 'running';
+  useEffect(() => {
+    if (fileMissing && isTerminal) reload();
+  }, [fileMissing, isTerminal, reload]);
+
   if (!runId) {
     return <CentredMessage>Select a run to view its trajectory.</CentredMessage>;
   }
@@ -281,14 +319,17 @@ export function TrajectoryView({ run, onForked }: Props) {
     const reconstructed = reconstructTrajectory(
       runId,
       run,
-      detail.data?.config ?? null,
+      detail.data,
       events.data ?? [],
     );
 
     return (
       <TrajectoryBody
         trajectory={reconstructed}
-        banner={reconstructedBanner(run?.status)}
+        // The row's status, not the (possibly synthesized) summary's — so a run
+        // that finishes while watched and whose file is genuinely absent stops
+        // claiming to be "live".
+        banner={reconstructedBanner(liveStatus)}
         isPolling={events.isPolling}
         showExport={false}
         canFork={false}
diff --git a/rig/src/hooks/useHarness.ts b/rig/src/hooks/useHarness.ts
index d12e4b2..455f04e 100644
--- a/rig/src/hooks/useHarness.ts
+++ b/rig/src/hooks/useHarness.ts
@@ -134,7 +134,35 @@ export function useRunEvents(
   return { data, loading, error, refetch: fetch, isPolling: activelyPolling };
 }
 
-export function useRunDetail(runId: string | null): AsyncState<RunDetail> {
+/**
+ * Run statuses at which the harness has finished writing everything it will
+ * write for a run. Mirrors `Aetheris.Store` (`done` / `failed` / `cancelled`).
+ */
+const TERMINAL_STATUSES = ['done', 'failed', 'cancelled'];
+
+/**
+ * The run row, optionally polled while the run is live (BL-030 r1).
+ *
+ * Polling this rather than only the event stream is what makes the completion
+ * transition race-free. The harness's ordering at run end is:
+ *
+ *   1. the `run_complete` **event** is appended to SQLite  (`loop.ex:267`)
+ *   2. the loop returns
+ *   3. `trajectory.json` is written — tmp file, then atomic rename
+ *      (`server.ex:680` → `file.ex:37-38`)
+ *   4. `runs.status` is set to a terminal value       (`server.ex:456-465`)
+ *
+ * So the `run_complete` event arrives *before* the file exists — a reload fired
+ * on seeing it in the event stream races the write — whereas the status flip
+ * strictly follows the completed rename. Waiting for a terminal **status** is
+ * therefore correct by construction and needs no retry.
+ *
+ * Self-terminating: polling stops as soon as a terminal status is observed.
+ */
+export function useRunDetail(
+  runId: string | null,
+  options?: { polling?: boolean },
+): AsyncState<RunDetail> & { isPolling: boolean } {
   const [data, setData] = useState<RunDetail | null>(null);
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState<string | null>(null);
@@ -153,6 +181,8 @@ export function useRunDetail(runId: string | null): AsyncState<RunDetail> {
     }
   }, [runId]);
 
+  const [activelyPolling, setActivelyPolling] = useState(false);
+
   useEffect(() => {
     if (!runId) {
       setData(null);
@@ -162,5 +192,25 @@ export function useRunDetail(runId: string | null): AsyncState<RunDetail> {
     fetch();
   }, [fetch, runId]);
 
-  return { data, loading, error, refetch: fetch };
+  // Sync activelyPolling with caller's intent
+  useEffect(() => {
+    setActivelyPolling(options?.polling ?? false);
+  }, [options?.polling]);
+
+  // Stop polling once the run row reaches a terminal status — by then the
+  // harness has written everything, including the trajectory file.
+  useEffect(() => {
+    if (!data || !activelyPolling) return;
+    if (TERMINAL_STATUSES.includes(data.status)) setActivelyPolling(false);
+  }, [data, activelyPolling]);
+
+  // Interval-based polling. Same 2s cadence as useRunEvents, against the same
+  // local SQLite file.
+  useEffect(() => {
+    if (!activelyPolling || !runId) return;
+    const id = setInterval(fetch, 2000);
+    return () => clearInterval(id);
+  }, [activelyPolling, runId, fetch]);
+
+  return { data, loading, error, refetch: fetch, isPolling: activelyPolling };
 }
diff --git a/rig/src/hooks/useTrajectory.ts b/rig/src/hooks/useTrajectory.ts
index 7f8a112..fd71894 100644
--- a/rig/src/hooks/useTrajectory.ts
+++ b/rig/src/hooks/useTrajectory.ts
@@ -1,4 +1,4 @@
-import { useState, useEffect } from 'react';
+import { useState, useEffect, useCallback } from 'react';
 import { invoke } from '@tauri-apps/api/core';
 import { TrajectoryFile } from './types';
 
@@ -19,5 +19,29 @@ export function useTrajectory(runId: string | null) {
       .catch((e) => { setError(String(e)); setLoading(false); });
   }, [runId]);
 
-  return { trajectory, loading, error };
+  /**
+   * Re-attempt the file load without disturbing what is on screen (BL-030 r1).
+   *
+   * A run that completes while being watched writes its `trajectory.json` only
+   * at the end, so by then the view is in BL-005 reconstructed mode and the
+   * now-existing file would never be read. This lets the caller pick it up.
+   *
+   * **Silent by design:** `loading` is deliberately not set. `TrajectoryView`
+   * renders `Loading…` whenever `loading` is true, so a reload that touched it
+   * would blank the streamed view mid-watch and flash it back — the transition
+   * has to be seamless or it is no better than the tab-out this exists to
+   * remove. On success `error` is cleared, and that is what flips the view from
+   * reconstructed to file-backed. On failure the previous error is kept, so a
+   * run whose file genuinely never appeared (a failed write — `server.ex:680`
+   * discards the write result — or a BL-003-swept orphan) stays reconstructed
+   * with its terminal banner instead of losing the view it had.
+   */
+  const reload = useCallback(() => {
+    if (!runId) return;
+    invoke<TrajectoryFile>('trajectory_load', { runId })
+      .then((t) => { setTrajectory(t); setError(null); })
+      .catch(() => { /* keep the reconstructed view and its existing error */ });
+  }, [runId]);
+
+  return { trajectory, loading, error, reload };
 }
diff --git a/rig/src/lib/reconstructTrajectory.ts b/rig/src/lib/reconstructTrajectory.ts
index 3e0f03c..26e7d5f 100644
--- a/rig/src/lib/reconstructTrajectory.ts
+++ b/rig/src/lib/reconstructTrajectory.ts
@@ -1,5 +1,6 @@
 import type {
   EventRow,
+  RunDetail,
   RunSummary,
   TrajectoryEvent,
   TrajectoryFile,
@@ -82,6 +83,34 @@ function seedField(config: Record<string, unknown>): number | null {
   return Number.isNaN(n) ? null : n;
 }
 
+/**
+ * Fork provenance for the reconstructed meta (BL-030 r1).
+ *
+ * The file path gets `fork_from`/`fork_step` from `meta` (`maybe_add_fork_meta`,
+ * `server.ex:720`), which only exists once the run has finished. They are also
+ * `RunConfig` fields, and `encode_config` (`server.ex:759-768`) strips only
+ * `stub_responses` / `coordinator_pid` / `blackboard_pid` / `label` /
+ * `max_duration` — so `runs.config_json` carries them from the moment the run is
+ * started. Verified against a live row: `fork_from` and `fork_step` both present.
+ * That is why the provenance banner can render while the fork is still running
+ * and does not have to wait for the file.
+ *
+ * Emitted only when present, because `TrajectoryBody` gates the banner on
+ * `meta.fork_from != null`. `fork_step` may legitimately be null
+ * (`run_config.ex:197`), and the banner already guards for that, so it is passed
+ * through as-is rather than being dropped or defaulted.
+ */
+function forkMeta(config: Record<string, unknown>): Partial<TrajectoryMeta> {
+  const forkFrom = config['fork_from' as keyof typeof config];
+  if (typeof forkFrom !== 'string' || forkFrom === '') return {};
+
+  const forkStep = config['fork_step' as keyof typeof config];
+  return {
+    fork_from: forkFrom,
+    fork_step: typeof forkStep === 'number' ? forkStep : null,
+  };
+}
+
 function parseConfig(configJson: string | null): Record<string, unknown> {
   if (!configJson) return {};
   try {
@@ -96,20 +125,21 @@ function parseConfig(configJson: string | null): Record<string, unknown> {
 }
 
 /**
- * Build a `TrajectoryFile` from live events + the run's `config_json`.
+ * Build a `TrajectoryFile` from live events + the run row.
  *
- * @param runId      the run being viewed
- * @param run        the run summary (status / provider / model / timestamps), or null
- * @param configJson `runs.config_json` (from `harness_get_run`), or null
- * @param rows       events from `harness_get_events`
+ * @param runId  the run being viewed
+ * @param run    the run summary the list handed over (may be synthesized), or null
+ * @param detail the real `runs` row from `harness_get_run` — `config_json`,
+ *               `started_at`, `finished_at` — or null if it has not arrived
+ * @param rows   events from `harness_get_events`
  */
 export function reconstructTrajectory(
   runId: string,
   run: RunSummary | null,
-  configJson: string | null,
+  detail: RunDetail | null,
   rows: EventRow[],
 ): TrajectoryFile {
-  const config = parseConfig(configJson);
+  const config = parseConfig(detail?.config ?? null);
   const events = rows.map(parseEventRow);
 
   // step_count: number of distinct step indices observed so far. Live runs
@@ -122,16 +152,24 @@ export function reconstructTrajectory(
     mode:            stringField(config, 'mode'),
     step_count:      stepCount,
     max_steps:       maxStepsField(config),
-    started_at:      run?.started_at ?? stringField(config, 'started_at'),
+    // The real `runs` row wins over the summary, and `||` (not `??`) is
+    // load-bearing: a run navigated to straight from a fork carries a
+    // *synthesized* summary whose `started_at` is `''` (RunList `handleForked`),
+    // and `''` is neither null nor undefined, so `??` kept it and the view
+    // rendered "Invalid Date". `||` falls through the empty string to the row's
+    // real timestamp. `config_json` has no timestamps — they are run-row
+    // columns — so there is no third source to consult (BL-030 r1).
+    started_at:      detail?.started_at || run?.started_at || '',
     // TrajectoryMeta.finished_at is '' when the run has not finished — mirrors
     // the Rust unwrap_or default on the file path (see types.ts).
-    finished_at:     run?.finished_at ?? '',
+    finished_at:     detail?.finished_at || run?.finished_at || '',
     tools:           toolsField(config),
     system_prompt:   stringField(config, 'system_prompt'),
     user_prompt:     stringField(config, 'user_prompt'),
     sandbox_path:    stringField(config, 'sandbox_path'),
     seed:            seedField(config),
     overlay_changes: [],
+    ...forkMeta(config),
   };
 
   return {
```

---

## 3. Committed implementation notes (verbatim)

### `docs/rig/milestones/bl-030-r1-completion-transition-implementation-notes.md` @ 4bf0fd6

# BL-030 r1 — completion transition (folded BL-063)

Rig-only. Follows the BL-030 early-return fork
(`docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md`).

**Invariant:** a fork's real metadata — id, provenance banner, `started_at`,
duration — must appear without a manual re-mount once the run completes in place.

---

## Scout: the data-availability seam

Both questions the ticket posed were answered from source and confirmed against
live data before a mechanism was chosen.

### (a) Does `runs.config_json` carry `fork_from` / `fork_step`? — **Yes.**

`encode_config` (`../aetheris/lib/aetheris/agent/server.ex:759-768`) strips
exactly five fields:

```elixir
    |> Map.delete(:stub_responses)
    |> Map.delete(:coordinator_pid)
    |> Map.delete(:blackboard_pid)
    |> Map.delete(:label)
    |> Map.delete(:max_duration)
```

`fork_from` and `fork_step` are `RunConfig` fields and are not among them.
Confirmed against a real row (`fork-d0b6042bcb44c369`): `fork_from =
fixture-unlabelled-fork-CbZX6w`, `fork_step = 0`, both present from the moment
the run is inserted.

So provenance **and** the real `started_at` are available from `harness_get_run`
during streaming, with no wait for the file. `RunDetail.config` is already the
raw `config_json` string (`harness.rs:280-287`) — the data was on the wire the
whole time; nothing consumed it.

### (b) Is the trajectory file written before or after `run_complete`? — **The event precedes it; the status follows it.**

The ordering at run end, read end-to-end:

| # | what | where |
|---|---|---|
| 1 | `run_complete` **event** appended to SQLite | `loop.ex:267` |
| 2 | loop returns | |
| 3 | `trajectory.json` written — tmp file, then **atomic rename** | `server.ex:680` → `file.ex:37-38` |
| 4 | `runs.status` set to a terminal value | `server.ex:456-465` |

This is the decisive finding. **A reload fired on the `run_complete` event races
the file write** — exactly the hazard the ticket suspected, and it is real, not
theoretical: the event is durable in SQLite before `File.rename/2` has been
called. **A reload gated on the run row's terminal status cannot race**, because
the status flip strictly follows the completed atomic rename.

So the mechanism is status-gated, and **no retry is needed or used**. The ticket
offered "a short retry if it's written just after the event" as a fallback; the
ordering makes it unnecessary, and a retry would have been an untestable code
path papering over a trigger chosen one step too early.

One asymmetry worth recording: `server.ex:680` **discards** the write's return
value (`result` in the following `case` is the *loop's* result, not the write's),
so a failed file write still flips the status to `done`. Terminal status
therefore means "the harness is finished writing", not "the file exists" — which
is why the reload is best-effort and failure keeps the reconstructed view.

## What changed

- `hooks/useTrajectory.ts` — new `reload()`, deliberately **silent** (does not
  touch `loading`, since `TrajectoryView` renders `Loading…` off it and a reload
  that blanked the streamed view would be no better than the tab-out this
  removes). Clears `error` on success — that is what flips the view to
  file-backed; keeps the prior error on failure.
- `hooks/useHarness.ts` — `useRunDetail` takes `{ polling }` and self-terminates
  on a terminal status, mirroring `useRunEvents`. The ordering rationale lives in
  its doc comment so the next reader does not "simplify" the trigger back to the
  event.
- `lib/reconstructTrajectory.ts` — takes the `RunDetail` row instead of a bare
  config string; prefers the row's `started_at`/`finished_at`; emits
  `fork_from`/`fork_step` into meta when the config carries them.
- `components/modules/harness/TrajectoryView.tsx` — polls the row while the
  fallback is engaged, derives `liveStatus` from the row, and reloads the file
  once the status is terminal. The reconstructed banner now reads the row's
  status too.

### The `??` → `||` fix is the whole "Invalid Date" symptom

```ts
- started_at: run?.started_at ?? stringField(config, 'started_at'),
+ started_at: detail?.started_at || run?.started_at || '',
```

A run navigated to straight from a fork carries a *synthesized* summary whose
`started_at` is `''` (`RunList.handleForked`). `''` is neither `null` nor
`undefined`, so `??` kept it and the view rendered "Invalid Date" — and the
duration row vanished, since `TrajectoryBody` gates it on
`meta.started_at && meta.finished_at`. `||` falls through the empty string to
the row's real timestamp. `config_json` has no timestamps (they are run-row
columns), so the old second operand could never have supplied one either.

## Scope held

BL-005's "completed runs unaffected" gating is intact: the fallback queries stay
behind `fallbackRunId`, which is null whenever the file loaded, so a completed
run opened directly still issues **zero** extra queries and takes the unchanged
file-backed path. The row poll is gated on the same value.

The fix is deliberately **not** fork-specific — it triggers on any run watched
through its own completion, which is what the ticket asked for. The synthesized
summary's `status` is left as the `'running'` seed rather than being mutated on
completion: the real row supersedes it as soon as it arrives, which covers every
run rather than only the one path that synthesizes a summary.

## Verification

Rig has no frontend test runner (`package.json` has no test script and no
vitest/jest dependency), so **the GUI pass is the gate**. What could be verified
without one was:

`reconstructTrajectory` is a pure function with type-only imports, so it was
executed directly under `bun` against the exact summary `handleForked`
synthesizes. 11 checks, all passing: the row's `started_at` wins over the
synthesized `''`; it parses to a valid `Date`; `finished_at` likewise; the
duration formula yields 12s; `fork_from`/`fork_step` are present *while running*
so the banner renders pre-file; the `isFork` gate is true; a non-fork grows no
`fork_from`; and a null detail row degrades without throwing.

Mutation-checked: reverting the operand order to `run?.started_at ?? …`
reproduces the original defect exactly — `started_at: ""`, invalid `Date`,
duration `undefined`.

The script is scratch, not committed — adding a test runner is outside this
ticket. It is reproduced in the packet so the reviewer can re-run it.

**Not verified without the GUI:** that the reload actually fires in the browser
on the status transition, that the banner disappears in place, and that the
polling stops. Those are the GUI pass, arm 2.

## Gates

`bun run lint` (clean) · `bunx tsc -b` (clean) · `bun run build` (clean) ·
`cargo test` (21 passed, 1 pre-existing ignored) — all green. Rust untouched this
round.

---

## 4. Divergences from the ticket

Both are deliberate, and both follow from §1a rather than from preference.

**1. No retry on the file reload.** The ticket allowed "on `run_complete`
re-attempt the file load (with a short retry if it's written just after the
event)". The scout showed the file *is* written just after the event — so the
retry would have been load-bearing had the trigger stayed on the event. Gating on
terminal status instead removes the race at its source, and the retry with it. A
retry kept anyway would be an untestable code path compensating for a trigger
chosen one step too early, and on the one occasion the file genuinely never
appears (below) it would delay the correct fallback rather than fix anything.

**2. The synthesized summary's `status` is not flipped.** The ticket said "flip
the synthesized status to `done` when the terminal event lands". Instead
`TrajectoryView` derives `liveStatus` from the **real run row**, falling back to
the prop only until the first row arrives. Reason: flipping the synthesized value
fixes the one path that synthesizes a summary (post-fork navigation), whereas
reading the row fixes every run watched through its own completion — which is the
generalization the same ticket asks for two paragraphs later. The synthesized
`status: 'running'` remains correct as a *seed*; nothing depends on it once the
row lands. (The Events tab already derives its own completion independently —
`RunList.tsx:436`, `isComplete ? 'done' : …` — and is unaffected either way.)

**Touches:**

| file | why |
|---|---|
| `rig/src/hooks/useTrajectory.ts` | silent `reload()` |
| `rig/src/hooks/useHarness.ts` | `useRunDetail` polling, self-terminating on terminal status |
| `rig/src/lib/reconstructTrajectory.ts` | takes the run row; real timestamps; fork provenance |
| `rig/src/components/modules/harness/TrajectoryView.tsx` | row-derived `liveStatus`; status-gated reload |
| `rig/…/bl-030-r1-completion-transition-implementation-notes.md` | notes |

`RunList.tsx` is **not** touched — see divergence 2. No Rust, no harness, no
`specs.md` (the `fork_run` command's name, signature and struct are unchanged;
checks 2 and 9 pass untouched).

---

## 5. One flagged observation — a latent harness defect this work surfaced

**`server.ex:680` discards the trajectory write's return value, so a failed write
still reports the run as `done`.**

```elixir
    Aetheris.Trajectory.File.write(config.run_id, events, meta)

    case result do
      :ok -> GenServer.cast(server_pid, {:run_complete, :done})
```

`result` is the **loop's** result. `File.write/3`'s `{:ok, path} | {:error, …}` is
never examined, so a disk-full, permission or rename failure produces a run whose
status reads `done` with no trajectory file and no error anywhere. It is the
Silent-wrong-answer shape: the failure renders as a normal completion.

Not introduced here and not fixed here — out of scope for a Rig-only ticket — but
it is why this round's reload is **best-effort**: terminal status means "the
harness has finished writing", not "the file exists". On that path the reload
fails, the prior error is kept, and the view stays reconstructed with its terminal
banner, which is the correct degradation. Worth a backlog row against the harness;
raising it here rather than only in a comment so it has an executor.

Same round, same rule as the r0 dangling-§4 note: a deferred finding gets a row,
not prose.

---

## 6. The verification script (§1b), verbatim

Scratch — not committed. Place at `rig/verify_reconstruct.ts` and
`bun run verify_reconstruct.ts` from `rig/`.

```typescript
import { reconstructTrajectory } from './src/lib/reconstructTrajectory';

let fails = 0;
function check(name: string, cond: boolean, got?: unknown) {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${cond ? '' : `  (got: ${JSON.stringify(got)})`}`);
  if (!cond) fails++;
}

// The exact summary RunList.handleForked synthesizes after a fork.
const synthesized = {
  run_id: 'fork-abc', label: '', status: 'running', provider: '', model: '',
  started_at: '', finished_at: null, step_count: 0, event_count: 0,
  last_event_at: null, total_cost_usd: null,
  total_input_tokens: null, total_output_tokens: null,
} as never;

const forkConfig = JSON.stringify({
  model: 'claude-x', provider: 'anthropic', mode: 'record', max_steps: 10,
  tools: ['echo'], system_prompt: 's', user_prompt: '', seed: 42,
  fork_from: 'run_parent', fork_step: 3,
});

const detail = {
  run_id: 'fork-abc', label: 'fork-abc', status: 'done', config: forkConfig,
  started_at: '2026-07-26T09:00:00.000000Z', finished_at: '2026-07-26T09:00:12.000000Z',
};

// 1. The Invalid Date bug: synthesized '' must not win over the real row.
const t1 = reconstructTrajectory('fork-abc', synthesized, detail as never, []);
check('started_at comes from the run row, not the synthesized empty string',
  t1.meta.started_at === '2026-07-26T09:00:00.000000Z', t1.meta.started_at);
check('started_at parses to a valid Date (no "Invalid Date")',
  !Number.isNaN(new Date(t1.meta.started_at).getTime()), t1.meta.started_at);
check('finished_at comes from the run row',
  t1.meta.finished_at === '2026-07-26T09:00:12.000000Z', t1.meta.finished_at);
const durationOk = Math.round(
  (new Date(t1.meta.finished_at).getTime() - new Date(t1.meta.started_at).getTime()) / 1000) === 12;
check('duration computes (TrajectoryBody formula) = 12s', durationOk);

// 2. Provenance from config_json, available while still streaming (no file).
const streaming = { ...detail, status: 'running', finished_at: null };
const t2 = reconstructTrajectory('fork-abc', synthesized, streaming as never, []);
check('fork_from present while running (banner renders pre-file)',
  t2.meta.fork_from === 'run_parent', t2.meta.fork_from);
check('fork_step present while running', t2.meta.fork_step === 3, t2.meta.fork_step);
check('isFork gate (meta.fork_from != null) is true', t2.meta.fork_from != null);
check('finished_at empty while running', t2.meta.finished_at === '', t2.meta.finished_at);

// 3. Non-fork must not grow a banner.
const plain = { ...detail, config: JSON.stringify({ model: 'm', provider: 'p' }) };
const t3 = reconstructTrajectory('run_x', synthesized, plain as never, []);
check('non-fork has no fork_from (banner stays hidden)',
  t3.meta.fork_from === undefined, t3.meta.fork_from);

// 4. No detail row yet: must not crash, must not invent timestamps.
const t4 = reconstructTrajectory('fork-abc', synthesized, null, []);
check('null detail degrades to empty started_at, no throw', t4.meta.started_at === '', t4.meta.started_at);
check('null detail has no fork_from', t4.meta.fork_from === undefined, t4.meta.fork_from);

console.log(fails === 0 ? '\nALL PASS' : `\n${fails} FAILED`);
process.exit(fails === 0 ? 0 : 1);
```
