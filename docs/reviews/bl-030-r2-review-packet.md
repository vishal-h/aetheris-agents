# BL-030 r2 — source-seeded post-fork selection — review packet r0

**Rig-only.** `aetheris-agents` @ **c2af6cf**. Tree clean. Branch `main`.
Harness untouched (still `f79365a`).

Closes the r1 residual: the Events tab showed "Invalid Date" until the run was
re-selected. Prior packets: `docs/reviews/bl-030-review-packet.md` (r0),
`docs/reviews/bl-030-r1-review-packet.md` (r1).

**Fix direction taken: the source fix**, per the review — remove the synthesized
placeholder rather than teach each consumer to route around it.

---

## 1. Done-check

### 1a. The residual, located exactly

`rig/src/components/modules/harness/RunList.tsx:474` **before** this change,
verbatim:

```tsx
        <span className="text-muted-foreground">
          Started: {new Date(selectedRun.started_at).toLocaleString()}
        </span>
```

`selectedRun` is the summary `handleForked` synthesized, whose `started_at` was
`''`. `new Date('')` is an invalid Date and `toLocaleString()` on it returns the
literal string `"Invalid Date"`. It never went through `reconstructTrajectory`,
which is where r1 put the fix — so r1 could not reach it.

Two further fields on that same header were blank from the identical cause:
`selectedRun.label` (`''`, line 473) and `selectedRun.model` (`''`, line 491).
The reported symptom was one of three.

### 1b. The premise the fix rests on, verified

The review's mechanism requires that the `runs` row exist by the time `fork_run`
returns the id. It does, and the reason is structural rather than timing-based.

`Aetheris.start_run/1` (`../aetheris/lib/aetheris.ex:29-40`) calls
`Server.run(config.run_id)`. That is a **synchronous call**, not a cast —
`../aetheris/lib/aetheris/agent/server.ex:69-73`, verbatim:

```elixir
  def run(run_id) do
    case Registry.lookup(Aetheris.Registry, {:server, run_id}) do
      [{pid, _}] -> GenServer.call(pid, :run)
      [] -> {:error, :not_found}
    end
  end
```

and its `handle_call(:run, …)` upserts the row before it returns —
`server.ex:225-235`, verbatim:

```elixir
  def handle_call(:run, _from, %{status: :idle} = state) do
    config = state.config
    started_at = DateTime.to_iso8601(DateTime.utc_now())

    :ok =
      Store.upsert_run(config.run_id, %{
        status: "running",
        started_at: started_at,
        config_json: encode_config(config),
        label: config.label
      })
```

So the ordering is: row committed (with a **real** `started_at`) → `start_run`
returns → CLI emits the fork-start line → Rig parses the id. Awaiting one local
SQLite read in `handleForked` cannot race the insert. It also costs nothing
beside the seconds `fork_run` itself just spent on mix boot.

### 1c. Pure-logic verification and its mutation

Rig has no frontend test runner (`package.json`: no `test` script, no
vitest/jest). `runSummaryFromDetail` is pure, so it was executed under `bun`
against the row shape `harness_get_run` returns for a just-started fork:

```
PASS  started_at is the row value
PASS  Events header renders a real date, not "Invalid Date"
PASS  label is the row label (header stops rendering blank)
PASS  model parsed from config_json (header stops rendering blank)
PASS  provider parsed from config_json
PASS  status from the row drives polling
PASS  finished_at null passes through
PASS  cost is null, not 0
PASS  tokens are null, not 0
PASS  counts are 0 at fork-start
PASS  unlabelled fork: label === run_id, so parentLabel degrades to undefined
PASS  malformed config_json degrades, no throw
PASS  malformed config still keeps the row timestamp

ALL PASS
```

The second check is the reported symptom asserted **the way the consumer renders
it**, not a proxy for it.

**Mutation** — revert the mapper to the synthesized empty value
(`started_at: ''`):

```
FAIL  started_at is the row value  (got: "")
FAIL  Events header renders a real date, not "Invalid Date"  (got: "Invalid Date")
PASS  label is the row label (header stops rendering blank)
PASS  model parsed from config_json (header stops rendering blank)
PASS  provider parsed from config_json
PASS  status from the row drives polling
PASS  finished_at null passes through
PASS  cost is null, not 0
PASS  tokens are null, not 0
PASS  counts are 0 at fork-start
PASS  unlabelled fork: label === run_id, so parentLabel degrades to undefined
PASS  malformed config_json degrades, no throw
FAIL  malformed config still keeps the row timestamp  (got: "")

3 FAILED
```

It reproduces the reported symptom verbatim: `got: "Invalid Date"`.

**r1 regression check** — r1's `reconstructTrajectory` script re-run unchanged
against this commit:

```
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
```

11/11 still green: the r1 completion transition is not disturbed by replacing the
summary beneath it.

### 1d. Consumers of the selected run — enumerated, not assumed

A source fix is supposed to make this list need no per-item work. It is
enumerated anyway, because "the fix reaches them all" is precisely the claim r1
got wrong.

| consumer | field | before | after |
|---|---|---|---|
| `RunList:440` events polling | `status` | `'running'` (seed) | row status |
| `RunList:456` status badge | `status` | seed, else `isComplete` | row status, else `isComplete` |
| `RunList:473` header label | `label` | `''` — blank | row label |
| `RunList:481` header run_id | `label` vs `run_id` | always shown (`'' !== id`) | shown iff genuinely unlabelled |
| `RunList:491` header model | `model` | `''` — blank | from `config_json` |
| `RunList:494` header started | `started_at` | `''` → **"Invalid Date"** | row timestamp |
| `TrajectoryView:355` parentLabel | `label` | `''` → always `undefined` | real label inherited |

The last row **resolves a documented compromise** rather than merely fixing a
symptom. That guard's comment recorded that forking a fork before a Refresh
"drops a real label rather than passing it on", accepted because the placeholder
could not know the label. It can now, so a labelled fork hands its label to a
grandchild immediately; the comment is rewritten rather than left describing a
cost that no longer exists.

### 1e. Rig gate line — @ c2af6cf

```
--- bun run lint ---
$ eslint .
(eslint printed no findings = clean)

--- bunx tsc -b ---
(no output = clean)

--- bun run build ---
dist/assets/index-DL7BOxH0.css                           49.19 kB │ gzip:   9.09 kB
dist/assets/index-DEcJsb1f.js                           448.36 kB │ gzip: 124.65 kB

✓ built in 631ms

--- cargo test ---
running 22 tests
test result: ok. 21 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.43s
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Rust untouched; `cargo test` run anyway (off-territory gate rule). The one
`ignored` is pre-existing (`live_store_demo_01…`, requires `AETHERIS_DB_PATH`).

### 1f. `drift_check --strict` — post-commit, @ c2af6cf

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
strict-mode exemption; exit 0. No **new** staleness from this round: this commit
touches no manifest-tracked doc. The six are the same set carried since BL-030
r0, listed with origins in the r1 packet §1d.

### 1g. Manual GUI pass — **outstanding, and it is the gate**

Unchanged in kind. The r1 arms are confirmed working and are not re-litigated
here. **The r2 arm is new:**

- after a fork, on the **first** landing and with **no re-select**, the Events
  tab header shows a real `Started:` date (not "Invalid Date"), a real label, and
  a real model.

Nothing in §1 proves that — §1c covers only the pure mapper, and the wiring from
`handleForked` through `setSelectedRun` into the header is React, which this repo
cannot exercise without a runner.

---

## 2. Diff — `aetheris-agents` @ c2af6cf (notes file inlined in §3, not repeated here)

```diff
diff --git a/rig/src/components/modules/harness/RunList.tsx b/rig/src/components/modules/harness/RunList.tsx
index 6d2a744..214b83c 100644
--- a/rig/src/components/modules/harness/RunList.tsx
+++ b/rig/src/components/modules/harness/RunList.tsx
@@ -5,8 +5,10 @@ import { Tab } from '@/components/shell/TabBar';
 import { MainArea } from '@/components/shell/MainArea';
 import { Badge } from '@/components/ui/badge';
 import { Button } from '@/components/ui/button';
-import { RunSummary } from '@/hooks/types';
+import { invoke } from '@tauri-apps/api/core';
+import { RunDetail, RunSummary } from '@/hooks/types';
 import { useHarnessStatus, useRunList, useRunEvents } from '@/hooks';
+import { runSummaryFromDetail } from '@/lib/runSummary';
 import { NotConnected, LoadingShell } from './shared';
 import { TrajectoryView } from './TrajectoryView';
 
@@ -14,6 +16,24 @@ import { TrajectoryView } from './TrajectoryView';
 // Helpers
 // ============================================================================
 
+/**
+ * Render an ISO timestamp, or "—" when it is absent or unparseable (BL-030 r2).
+ *
+ * Not a substitute for the source fix — `handleForked` now seeds the selected run
+ * from the real `runs` row, so an empty `started_at` no longer arrives here on the
+ * normal path. This covers the one path that fix *introduces*: if
+ * `harness_get_run` fails, the fallback selection carries `started_at: ''`
+ * rather than an invented value, and `new Date('').toLocaleString()` would print
+ * "Invalid Date" — a broken-looking header where "—" is honest. Guarding the
+ * render, not teaching the header to fetch, keeps the data-source logic in one
+ * place.
+ */
+function formatTimestamp(iso: string): string {
+  if (!iso) return '—';
+  const ms = new Date(iso).getTime();
+  return Number.isNaN(ms) ? '—' : new Date(ms).toLocaleString();
+}
+
 function formatDuration(startedAt: string, finishedAt: string | null): string {
   if (!finishedAt) return '—';
   const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime();
@@ -471,7 +491,7 @@ function EventsContent({ selectedRun }: EventsContentProps) {
           {selectedRun.model.split('/').pop() ?? selectedRun.model}
         </span>
         <span className="text-muted-foreground">
-          Started: {new Date(selectedRun.started_at).toLocaleString()}
+          Started: {formatTimestamp(selectedRun.started_at)}
         </span>
         {isPolling && (
           <span className="flex items-center gap-1.5 text-xs text-green-600">
@@ -547,33 +567,57 @@ export function HarnessRoute() {
   }, []);
 
   // Surface a started fork (BL-007 t4, early-return since BL-030): jump to the child
-  // run's trajectory so its provenance banner is immediately visible. `fork_run` now
+  // run's trajectory so its provenance banner is immediately visible. `fork_run`
   // resolves as soon as the fork *starts*, so the child is still running when we land
-  // on it — `status: 'running'` is what turns TrajectoryView's event polling on, and
-  // the poll stops itself when `run_complete` reaches the stream. The trajectory file
-  // does not exist until the run finishes (it is written once, at completion), so
-  // TrajectoryView's file load fails and its events fallback reconstructs the view
-  // live; that fallback is the BL-005 path and needs no change here. The Runs-list
-  // row appears on the next manual Refresh.
-  const handleForked = useCallback((runId: string) => {
-    setSelectedRun({
-      run_id:         runId,
-      label:          '',
-      status:         'running',
-      provider:       '',
-      model:          '',
-      started_at:     '',
-      finished_at:    null,
-      step_count:     0,
-      event_count:    0,
-      last_event_at:  null,
-      total_cost_usd: null,
-      // Placeholder, like the rest of this literal — the real totals arrive with
-      // the row on the next manual Refresh. null (not 0) keeps the Cost cell and
-      // its token tooltip honest in the meantime.
-      total_input_tokens:  null,
-      total_output_tokens: null,
-    });
+  // on it — `status: 'running'` (from the row) is what turns TrajectoryView's event
+  // polling on, and the poll stops itself when `run_complete` reaches the stream. The
+  // trajectory file does not exist until the run finishes, so TrajectoryView's file
+  // load fails and its BL-005 events fallback reconstructs the view live, then swaps
+  // to the file in place when the run completes (r1). The Runs-list row appears on the
+  // next manual Refresh.
+  //
+  // **Seeded from the real row, not synthesized (r2).** This used to invent a summary
+  // with `started_at: ''`, `label: ''`, `model: ''`. Every consumer of the selected
+  // run inherited those blanks, and `new Date('')` renders "Invalid Date" — which r1
+  // fixed only for the consumers it enumerated (TrajectoryView, via
+  // reconstructTrajectory), leaving the Events tab header reading the placeholder
+  // directly. That is the Adjacent-case class: the fix's blast radius was one consumer
+  // wider than the view it was written against. Fixing the source removes the thing to
+  // enumerate.
+  //
+  // The row is guaranteed to exist by now: `Aetheris.start_run/1` calls `Server.run/1`,
+  // a synchronous `GenServer.call` (`server.ex:70-72`) whose `handle_call(:run, …)`
+  // upserts status / `started_at` / `config_json` / label before returning
+  // (`server.ex:229-235`), and the CLI's fork-start emit happens after that returns.
+  // So awaiting one local SQLite read here cannot race the insert — and it costs
+  // nothing next to the seconds `fork_run` itself just spent.
+  const handleForked = useCallback(async (runId: string) => {
+    try {
+      const detail = await invoke<RunDetail>('harness_get_run', { runId });
+      setSelectedRun(runSummaryFromDetail(detail));
+    } catch (e) {
+      // The fork itself succeeded — the id came off the CLI's stdout — so losing
+      // navigation would be a worse outcome than a sparse header. Select the run
+      // with what is certain (its id) and let the views fill themselves in: they
+      // read the row independently. `started_at: ''` is honest here rather than
+      // invented, and the header renders it as "—" (see EventsContent).
+      console.warn(`[HarnessRoute] harness_get_run failed for forked run ${runId}: ${String(e)}`);
+      setSelectedRun({
+        run_id:         runId,
+        label:          runId,
+        status:         'running',
+        provider:       '',
+        model:          '',
+        started_at:     '',
+        finished_at:    null,
+        step_count:     0,
+        event_count:    0,
+        last_event_at:  null,
+        total_cost_usd: null,
+        total_input_tokens:  null,
+        total_output_tokens: null,
+      });
+    }
     setActiveTab('trajectory');
   }, []);
 
diff --git a/rig/src/components/modules/harness/TrajectoryView.tsx b/rig/src/components/modules/harness/TrajectoryView.tsx
index 556a94c..1532e0f 100644
--- a/rig/src/components/modules/harness/TrajectoryView.tsx
+++ b/rig/src/components/modules/harness/TrajectoryView.tsx
@@ -340,18 +340,21 @@ export function TrajectoryView({ run, onForked }: Props) {
 
   // File loaded successfully — render it exactly as before.
   if (fileTrajectory) {
-    // A fork inherits its parent's label verbatim (BL-029 rider). Two ways `label`
-    // is not a real label, both of which must degrade to an unlabelled fork rather
-    // than to a synthesized one:
-    //   - server-side it is COALESCE(runs.label, run_id), so an unlabelled parent
-    //     yields the run_id — inheriting that writes a run_id into the child's label;
-    //   - the synthesized post-fork summary (RunList.tsx `handleForked`) carries
-    //     label: '', so forking a fork before a Refresh would inherit Some("").
-    // The second guard is not free: that child *does* carry the inherited label in
-    // the DB, so forking it before a Refresh drops a real label rather than passing
-    // it on. Chosen deliberately — the placeholder cannot tell us what the label is,
-    // and an unlabelled fork is legible where a wrong or empty one is not. A Refresh
-    // before the second fork gets the real row, and the label with it.
+    // A fork inherits its parent's label verbatim (BL-029 rider). `label` must
+    // degrade to an unlabelled fork when it is not a real label: server-side it is
+    // COALESCE(runs.label, run_id) (`harness.rs:300`), so an unlabelled parent
+    // yields its run_id, and inheriting that would write a run_id into the child's
+    // label.
+    //
+    // The empty-string arm of this guard used to carry a documented cost: the
+    // post-fork summary was *synthesized* with `label: ''` (RunList
+    // `handleForked`), so forking a fork before a Refresh dropped a real label
+    // rather than passing it on. Since r2 that summary is seeded from the real
+    // `runs` row, so a labelled fork now hands its label to a grandchild
+    // immediately — the compromise is gone, not merely tolerated. The `run.label &&`
+    // check is kept for the one path that can still produce a sparse selection
+    // (a failed `harness_get_run` in `handleForked`), where an unlabelled fork
+    // remains the legible outcome.
     const parentLabel =
       run && run.label && run.label !== run.run_id ? run.label : undefined;
     return <TrajectoryBody trajectory={fileTrajectory} banner={null} isPolling={false} showExport canFork parentLabel={parentLabel} onForked={onForked} />;
diff --git a/rig/src/lib/runSummary.ts b/rig/src/lib/runSummary.ts
new file mode 100644
index 0000000..95bde93
--- /dev/null
+++ b/rig/src/lib/runSummary.ts
@@ -0,0 +1,70 @@
+import type { RunDetail, RunSummary } from '@/hooks/types';
+
+/**
+ * Build a `RunSummary` from the real `runs` row (BL-030 r2).
+ *
+ * Exists to kill a synthesized placeholder at its source. After a fork, the run
+ * list had no row for the child yet, so `RunList.handleForked` invented a
+ * summary with `started_at: ''`, `label: ''`, `model: ''`. Every consumer of the
+ * selected run then inherited those blanks — `new Date('')` renders
+ * "Invalid Date" — and r1 fixed only the consumers it enumerated
+ * (`TrajectoryView` via `reconstructTrajectory`), leaving the Events tab header
+ * reading the placeholder directly. Fixing the source means there is nothing to
+ * enumerate: the invention is gone.
+ *
+ * The data was always available. `Aetheris.start_run/1` calls `Server.run/1`,
+ * which is a **synchronous** `GenServer.call` (`server.ex:70-72`) whose
+ * `handle_call(:run, …)` upserts the row — `status`, a real `started_at`,
+ * `config_json`, `label` — before returning (`server.ex:229-235`). The CLI's
+ * fork-start emit happens after that call returns, so by the time Rig has the
+ * forked id from stdout the row is already in SQLite. One `harness_get_run` and
+ * the placeholder is unnecessary.
+ *
+ * Fields with no live source are left honestly empty rather than zeroed with
+ * intent: counts are genuinely 0 at fork-start, and cost/token totals are
+ * `null` (not `0`) so the Cost cell and its tooltip render "—" instead of
+ * claiming $0.0000 — the same contract `handleForked`'s placeholder already
+ * observed and `types.ts` documents.
+ */
+export function runSummaryFromDetail(detail: RunDetail): RunSummary {
+  const config = parseConfig(detail.config);
+
+  return {
+    run_id:      detail.run_id,
+    // `harness_get_run` returns COALESCE(label, run_id) (harness.rs:300), so an
+    // unlabelled fork yields its run_id here. That is what the Events header
+    // wants: it prints the run_id separately only when it differs from the
+    // label, so the id shows exactly once either way.
+    label:       detail.label,
+    status:      detail.status,
+    provider:    stringField(config, 'provider'),
+    model:       stringField(config, 'model'),
+    started_at:  detail.started_at,
+    finished_at: detail.finished_at,
+    // True at fork-start, and superseded by the real row on the next Refresh.
+    step_count:  0,
+    event_count: 0,
+    last_event_at: null,
+    total_cost_usd: null,
+    total_input_tokens: null,
+    total_output_tokens: null,
+  };
+}
+
+function stringField(config: Record<string, unknown>, key: string): string {
+  const value = config[key];
+  return typeof value === 'string' ? value : '';
+}
+
+function parseConfig(configJson: string | null): Record<string, unknown> {
+  if (!configJson) return {};
+  try {
+    const parsed = JSON.parse(configJson) as unknown;
+    if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
+      return parsed as Record<string, unknown>;
+    }
+    return {};
+  } catch {
+    return {};
+  }
+}
diff --git a/rig/src/lib/runSummary.ts.notes.md b/rig/src/lib/runSummary.ts.notes.md
new file mode 100644
index 0000000..48cdce8
--- /dev/null
+++ b/rig/src/lib/runSummary.ts.notes.md
@@ -0,0 +1 @@
+placeholder
```

---

## 3. Committed implementation notes (verbatim)

### `docs/rig/milestones/bl-030-r2-source-seeded-selection-implementation-notes.md` @ c2af6cf

# BL-030 r2 — seed the post-fork selection from the real run row

Rig-only. Closes the r1 residual: the Events tab still showed "Invalid Date"
until the run was re-selected.

Follows `bl-030-r1-completion-transition-implementation-notes.md`.

---

## The residual, and why r1 missed it

r1 taught `TrajectoryView` / `reconstructTrajectory` to prefer the real `runs`
row over the synthesized summary's `started_at: ''`. The Events tab header does
not go through `reconstructTrajectory` at all — it reads the selected summary
directly:

```tsx
Started: {new Date(selectedRun.started_at).toLocaleString()}   // RunList.tsx:474 (pre-r2)
```

`new Date('')` is an invalid Date, so the header rendered the literal string
"Invalid Date". Two more fields on the same header were blank from the same
cause: `selectedRun.label` (`''`) and `selectedRun.model` (`''`).

This is the **Adjacent-case** class from the harness `CLAUDE.md`: r1's blast
radius was one consumer wider than the view it was written against, and r1's
per-consumer approach is what made it leaky — fixing consumers means every
consumer must be enumerated, and this one was not.

## The fix: remove the invention, don't chase its consumers

`RunList.handleForked` now fetches the real row and seeds the selection from it,
via a new pure mapper `lib/runSummary.ts` → `runSummaryFromDetail/1`. The
synthesized literal is gone from the normal path.

**The row is guaranteed to exist by then**, which is what makes this safe rather
than a race traded for a bug. `Aetheris.start_run/1` calls `Server.run/1`, a
**synchronous** `GenServer.call` (`../aetheris/lib/aetheris/agent/server.ex:70-72`),
whose `handle_call(:run, …)` upserts the row — `status`, a real `started_at`,
`config_json`, `label` — before returning (`server.ex:229-235`). The CLI's
fork-start emit happens *after* that call returns, so by the time Rig has parsed
the forked id off stdout the row is already committed. Awaiting one local SQLite
read in `handleForked` cannot race the insert, and costs nothing beside the
seconds `fork_run` just spent.

This was the r1 scout's finding taken one step further: that scout established
`config_json` + the `runs` row already carry everything the views need. r1 used
that to enrich one view. r2 uses it to delete the placeholder.

### Every consumer of the selected run, enumerated

The point of a source fix is that this list needs no per-item work — but it is
enumerated rather than assumed, since "the fix reaches them all" is exactly the
claim r1 got wrong:

| consumer | field | before | after |
|---|---|---|---|
| `RunList:440` events polling | `status` | `'running'` (seed) | row status |
| `RunList:456` status badge | `status` | seed, else `isComplete` | row status, else `isComplete` |
| `RunList:473` header label | `label` | `''` — blank | row label |
| `RunList:481` header run_id | `label` vs `run_id` | always shown (`'' !== id`) | shown iff genuinely unlabelled |
| `RunList:491` header model | `model` | `''` — blank | from `config_json` |
| `RunList:494` header started | `started_at` | `''` → **"Invalid Date"** | row timestamp |
| `TrajectoryView:355` parentLabel | `label` | `''` → always undefined | real label inherited |

The last row is an incidental **resolution of a documented compromise**, not just
a fix. That guard's comment recorded that forking a fork before a Refresh "drops
a real label rather than passing it on", accepted because the placeholder could
not know the label. With the row seeded, a labelled fork now hands its label to a
grandchild immediately. The comment is updated to say so rather than left
describing a cost that no longer exists.

## Failure path, and the one guard added beyond the ticket

If `harness_get_run` fails, the fork itself still succeeded — the id came off the
CLI's stdout — so losing navigation would be worse than a sparse header. The
fallback selects the run with what is certain (its id, as both `run_id` and
`label`) and leaves `started_at` empty rather than inventing one; the views read
the row independently and fill themselves in.

That fallback is a path *this change introduces*, and it is the only remaining
way an empty `started_at` reaches the Events header — so the header's render is
guarded: `formatTimestamp/1` returns `—` for an absent or unparseable timestamp.
This is deliberately **not** the localized fix the review argued against: it does
not teach the header to fetch the row, and it adds no second source of truth. It
makes a degraded render honest instead of broken. Named here so it can be
rejected on its own terms.

## Verification

Rig still has no frontend test runner, so the GUI pass remains the gate. What
could be verified without one:

`runSummaryFromDetail` is pure, so it was executed under `bun` against the row
shape `harness_get_run` returns for a just-started fork. 13 checks, all passing —
including the symptom asserted the way the consumer actually renders it:

```ts
check('Events header renders a real date, not "Invalid Date"',
  new Date(s.started_at).toLocaleString() !== 'Invalid Date', …);
```

Covered: row timestamp, label, provider/model parsed from `config_json`, status,
`finished_at` null passthrough, cost/tokens `null` (not `0`, so Cost renders "—"),
counts `0`, the unlabelled-fork `label === run_id` case the `parentLabel` guard
depends on, and malformed `config_json` degrading without throwing or losing the
timestamp.

**Mutation-checked:** reverting the mapper to `started_at: ''` reproduces the
reported symptom verbatim — `got: "Invalid Date"`.

r1's `reconstructTrajectory` script was re-run unchanged: 11/11 still green, so
the r1 fix is not regressed by the r2 change beneath it.

Both scripts are scratch, not committed; reproduced in the packet.

**Not verified without the GUI:** that the Events tab header shows the real date,
label and model on the first landing after a fork, with no re-select.

## Gates

`bun run lint` (clean) · `bunx tsc -b` (clean) · `bun run build` (clean) ·
`cargo test` (21 passed, 1 pre-existing ignored) — all green. Rust untouched.

---

## 4. Additions beyond the ticket

**One, named so it can be rejected on its own terms: `formatTimestamp/1` in the
Events header.**

The fix introduces a failure path — if `harness_get_run` throws, the fork itself
still succeeded (the id came off the CLI's stdout), so navigation is kept with a
sparse selection carrying the run id and an **empty** `started_at` rather than an
invented one. That is now the only remaining way an empty timestamp reaches the
header, and `new Date('').toLocaleString()` would print "Invalid Date" there —
the very string this round exists to remove.

So the render is guarded: absent or unparseable → `—`.

This is deliberately **not** the localized fix the review argued against. It does
not teach the header to fetch the row, and it introduces no second source of
truth; the data-source logic stays in `handleForked`/`runSummaryFromDetail`
alone. It makes a degraded render honest instead of broken, on a path this change
created. If the reviewer would rather the fallback not exist at all — i.e. a
failed `harness_get_run` should surface an error instead of navigating — that is
a coherent alternative and the guard goes with it.

**Touches:**

| file | why |
|---|---|
| `rig/src/lib/runSummary.ts` | **new** — pure `runSummaryFromDetail/1` |
| `rig/src/components/modules/harness/RunList.tsx` | `handleForked` seeds from the row; `formatTimestamp` guard |
| `rig/src/components/modules/harness/TrajectoryView.tsx` | `parentLabel` comment — its documented compromise is resolved, not merely tolerated |
| `rig/…/bl-030-r2-source-seeded-selection-implementation-notes.md` | notes |

No Rust, no harness, no `specs.md` (no command name, signature or struct
changed). `reconstructTrajectory.ts` is **not** touched — r1's preference logic
remains correct and still serves the non-fork reconstructed paths.

---

## 5. One flagged observation — the mount guard's window is no longer zero

`handleForked` is now `async`, and that slightly widens a window the BL-007 t4 r5
mount guard was written to close.

`TrajectoryBody.handleFork` checks `alive.current` immediately before calling
`onForked` (`TrajectoryView.tsx:424`), so that a fork resolving after the user
navigated away does not yank them to the child. Previously everything after that
check was synchronous — guard passed, state set, done. Now one `await
invoke('harness_get_run')` sits between the check and `setActiveTab`, so the
navigation lands a local SQLite read later than the guard observed.

**Not fixed, and the reasoning is why:** that await is a single read of a local
file, on the order of a millisecond, against a guard written for an operation
that originally took *minutes* (pre-BL-030) and now takes seconds. No user action
can intervene inside it. The alternatives are worse: navigating before the fetch
means `selectedRun` is null at the tab switch, and the Trajectory tab is
`disabled: !hasSelection`, so the user would land on a "Select a run" placeholder
and watch it repaint — reintroducing exactly the flash r1 worked to remove.

Named rather than absorbed because it is a real, if tiny, widening of an
intentionally-closed window, and the next person to add work to `handleForked`
should know the guard no longer covers everything downstream of it.

**Carried, not re-raised:** the r1 packet's flagged observation —
`../aetheris/lib/aetheris/agent/server.ex:680` discards the trajectory write's
return value, so a failed write still reports the run `done` — is unchanged and
still wants a harness backlog row. Not re-argued here.

---

## 6. The verification scripts (§1c), verbatim

Both are scratch, not committed — adding a test runner remains out of scope.
Place at `rig/verify_r2.ts` / `rig/verify_reconstruct.ts` and run with
`bun run <file>` from `rig/`. The r1 script is unchanged from the r1 packet §6
and is re-run here only as a regression check; it is not reproduced again.

### `verify_r2.ts`

```typescript
import { runSummaryFromDetail } from './src/lib/runSummary';

let fails = 0;
function check(name: string, cond: boolean, got?: unknown) {
  console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${cond ? '' : `  (got: ${JSON.stringify(got)})`}`);
  if (!cond) fails++;
}

// The row harness_get_run returns for a just-started fork: status running,
// finished_at null, config_json carrying provider/model/fork provenance.
const row = {
  run_id: 'fork-abc',
  label: 'retry with tighter prompt',
  status: 'running',
  config: JSON.stringify({
    provider: 'anthropic', model: 'anthropic/claude-x', mode: 'record',
    fork_from: 'run_parent', fork_step: 3,
  }),
  started_at: '2026-07-26T09:00:00.000000Z',
  finished_at: null,
};

const s = runSummaryFromDetail(row as never);

// The reported r1 residual, asserted as the consumer actually renders it
// (RunList EventsContent: `new Date(selectedRun.started_at).toLocaleString()`).
check('started_at is the row value', s.started_at === '2026-07-26T09:00:00.000000Z', s.started_at);
check('Events header renders a real date, not "Invalid Date"',
  new Date(s.started_at).toLocaleString() !== 'Invalid Date',
  new Date(s.started_at).toLocaleString());
check('label is the row label (header stops rendering blank)',
  s.label === 'retry with tighter prompt', s.label);
check('model parsed from config_json (header stops rendering blank)',
  s.model === 'anthropic/claude-x', s.model);
check('provider parsed from config_json', s.provider === 'anthropic', s.provider);
check('status from the row drives polling', s.status === 'running', s.status);
check('finished_at null passes through', s.finished_at === null, s.finished_at);

// Honest unknowns — null, not 0, so Cost renders "—" not "$0.0000".
check('cost is null, not 0', s.total_cost_usd === null, s.total_cost_usd);
check('tokens are null, not 0',
  s.total_input_tokens === null && s.total_output_tokens === null,
  [s.total_input_tokens, s.total_output_tokens]);
check('counts are 0 at fork-start', s.step_count === 0 && s.event_count === 0);

// An unlabelled fork: harness_get_run COALESCEs label to run_id. The
// parentLabel guard (TrajectoryView) must see label === run_id and degrade.
const unlabelled = runSummaryFromDetail({ ...row, label: 'fork-abc' } as never);
check('unlabelled fork: label === run_id, so parentLabel degrades to undefined',
  unlabelled.label === unlabelled.run_id);

// Malformed / absent config must not throw or invent.
const bad = runSummaryFromDetail({ ...row, config: '{not json' } as never);
check('malformed config_json degrades, no throw', bad.model === '' && bad.provider === '');
check('malformed config still keeps the row timestamp',
  bad.started_at === '2026-07-26T09:00:00.000000Z', bad.started_at);

console.log(fails === 0 ? '\nALL PASS' : `\n${fails} FAILED`);
process.exit(fails === 0 ? 0 : 1);
```
