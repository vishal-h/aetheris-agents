# Handoff — Aetheris + Provenance + Rig

**Session date:** 2026-06-06
**Prepared for:** next Claude session

---

## Repo locations

| Repo | Path | Purpose |
|------|------|---------|
| `aetheris` | `~/sandbox/elixirws/aetheris/` | Harness (Elixir + Rust) |
| `aetheris-agents` | `~/sandbox/elixirws/aetheris-agents/` | Agents, scripts, Rig UI, docs |
| `hai-rig` | `~/workspaces/hai/hai-rig/` | Old standalone Tauri repo (retired — do not touch) |
| test sandbox | `~/sandbox/provenance-test/` | Local corpus for pipeline validation |

---

## What is complete

### Provenance — all 6 milestones done

| Milestone | What it does |
|-----------|-------------|
| m1 | Inventory — scan NAS, populate f2_file_index, generate report |
| m2 | Classification — taxonomy session, classify batches, review cycle |
| m3 | Migration — copy approved files to /clients/, SHA-256 verify, rollback |
| m4 | Zip archaeology — extract zips, find new-to-corpus, handle encrypted |
| m5 | Corpus MCP + search — corpus-search MCP server, search_agent, validation |
| m6 | Tauri dashboard — corpus overview, classification review, migration + zip status |

### Rig — Phases 1–7 all complete ✅

| Phase | Goal | Status |
|-------|------|--------|
| p1 | Consolidation + run list UI | ✅ Complete |
| p2 | Live monitoring | ✅ Complete |
| p3 | Orchestrator — NL → plan → confirm → execute | ✅ Complete |
| p4 | Trajectory explorer — full event detail, diff, export | ✅ Complete |
| p5 | Run grouping + Capability matrix | ✅ Complete |
| p6 | Token & cost surface | ✅ Complete |
| p7 | Agent config settings | ✅ Complete |
| p8 | Orchestrator UX + reliability | 🔄 In progress |

**What p1 delivered:**
- `aetheris-agents/rig/` — full Tauri app (moved from hai-rig)
- `HarnessState` + 4 read-only SQLite commands for `aetheris.db`
- Harness module in sidebar: Runs tab (table + status filter) and Events tab
- Controlled/uncontrolled `MainArea` — supports cross-tab shared state

**What p2 delivered:**
- `useRunEvents` polls every 2s when `{ polling: true }` — stops on `run_complete`
- Smart auto-scroll (respects user scroll position, 50px threshold)
- Pulsing "Live" indicator while polling
- Local status badge update on `run_complete` — no extra network call

**What p3 delivered:**
- `agents/mock_orchestrator.exs` — deterministic Elixir script; stdin/stdout newline-delimited JSON; kept for regression testing
- `commands/orchestrate.rs` — 4 commands: start, poll, approve, cancel; reader thread + job map
- `useOrchestrator` hook — full phase state machine; poll effect self-terminates on terminal phase
- `OrchestratorView` — single-view workflow (idle → planning → plan_ready → executing → done/cancelled/error)
- `agents/orchestrator.exs` — real LLM-driven orchestrator: few-shot planning against capability matrix, params extraction (PAYSLIP_MONTH → YYYY-MM), sub-agent execution via RunHelpers internal API, System.put_env/restore for context injection

**What p4 delivered:**
- `trajectory_load` + `trajectory_export` Tauri commands
- `TrajectoryView` — meta panel (model/provider/tools/token costs), step-grouped events, expandable payload
- `DiffView` — run selection dropdowns, metadata + step-path comparison, amber highlight on differing rows
- Token/cost rows in diff metadata table

**What p5 delivered:**
- Run list grouped by use case (label prefix parsing, 7 groups)
- `useSessionRecord` — collapsed-by-default, persists via `sessionStorage`
- Collapse all / Expand all buttons on run list and capability matrix
- `CapabilityMatrixView` — agents listed with pre-fill link to Orchestrator; scripts readonly
- `capability_matrix_load` parses `docs/capability-matrix.md` in Rust

**What p6 delivered:**
- Harness: `input_tokens`, `output_tokens`, `cost_usd` in `llm_responded` events
- `pricing.ex` — per-model pricing table, `compute_cost/3` returns nil for unknown/uninstrumented runs
- `TokenSummaryRows` in Trajectory tab meta panel (LLM calls / Input / Output / Cost)
- `UsageView` — 4 stat cards, by-model table, by-use-case table; `usage_stats_load` command
- Diff metadata table: input tokens, output tokens, total cost rows

**What p7 delivered:**
- `AgentConfigState` — HashMap cache loaded from JSON file on startup; `persist()` writes on every change; no plugin needed
- `agent_config_get_all` / `agent_config_set` / `agent_config_delete` Tauri commands
- `AgentConfigTab` in Settings panel (second tab alongside Watched Folders); credential fields masked with show/hide toggle; save/clear per-row; amber plaintext-storage notice
- `orchestrate_start` injects all stored values as `.env()` calls before child process spawn
- `email_send.py`: env var fallback when `smtp.cfg` absent (SMTP_HOST/USER/PASSWORD/FROM/TO)
- `SMTP_FROM`, `SMTP_TO` added to `agentConfigDefs.ts`

**What p8 delivered (partial — 2026-06-06):**

**p8-001 — Plan view enrichment:**
- `context` field added to each step in orchestrator LLM output format and all 4 few-shot examples
- `ParamsStrip` component renders extracted params (e.g. `PAYSLIP_MONTH = 2026-05`) above the step list
- `STEP_CONFIG_HINTS` map in `OrchestratorView` shows relevant env var values per step
- `useAgentConfig().values` called in `OrchestratorView` to supply config values to `StepCard`
- `OrchestratorPlan.params` and `PlanStep.context` added to TypeScript types

**p8-002 — Drive folder convention refactor:**
- `DRIVE_ROOT_FOLDER_ID` replaces `DRIVE_PAYROLL_FOLDER_ID` + `DRIVE_OUTPUT_FOLDER_ID` (two vars → one)
- `drive/scripts/drive_utils.py`: `period_folder_name()` + `find_folder()` + `resolve_period_folder()`
- `DRIVE_ROOT_FOLDER_ID` points directly to the payslips folder; scripts navigate one level below to the period folder (`{YYYYMM-monthname}/`, e.g. `202605-may`)
- `drive_download.py` and `drive_upload.py` both navigate this tree; `resolve_period_folder` exits 1 if folder absent
- `drive/tests/test_drive_utils.py`: 5 unit tests for `period_folder_name`
- `agentConfigDefs.ts`: `GOOGLE_CREDENTIALS` removed; `GOOGLE_SERVICE_ACCOUNT` + `DRIVE_ROOT_FOLDER_ID` added (12 vars total, 5 groups)
- `DRIVE_ROOT_FOLDER_ID` has `linkPrefix` → external link icon in Agent Config UI (uses `tauri-plugin-shell` `open()`)

**p8-003 — Orchestrator reliability:**
- `get_step_result` function reads trajectory JSON post-run to detect true failures (see Elixir patterns below)
- `Enum.each` replaced with `Enum.reduce_while` — stops on first failed step, preventing dependent steps from running
- `step_complete` protocol extended with optional `error` field (stderr string from failed tool_result)
- `done`/`cancelled` states in `OrchestratorView` now show frozen step list above the final message
- `stepErrors: Record<string, string>` state in `useOrchestrator`; errors shown inline in `StepCard`
- `AlertCircle` (amber) shown on done + any failures; `CheckCircle2` (green) on clean completion
- `linkifyDriveIds` in `OrchestratorView`: regex `/([A-Za-z0-9_-]{15,})/` renders matching tokens as clickable buttons opening Drive URLs in system browser

**Agent config UX (p8):**
- External link icon in `ConfigRow` when `linkPrefix` is set and value is non-empty — uses `open()` not anchor
- `tauri-plugin-shell` added to Cargo.toml, registered in `lib.rs`, and declared in `capabilities/default.json`

**p8-004 — Drive agent split:**
- `drive_orchestrator.exs` split into two single-purpose agents: `drive_download_orchestrator.exs` + `drive_upload_orchestrator.exs`
- `drive_orchestrator.exs` kept for standalone download + upload workflow (no payslip generation step)
- `agents/orchestrator.exs` few-shot example for "email payslips" updated to 4-step pipeline:
  1. `drive/agents/drive_download_orchestrator.exs` — downloads payroll CSV + email template
  2. `payslip/agents/payslip_orchestrator.exs` — generates PDF payslips
  3. `drive/agents/drive_upload_orchestrator.exs` — uploads PDFs to Shared Drive
  4. `email/agents/email_orchestrator.exs` — sends payslip emails
- `STEP_CONFIG_HINTS` in `OrchestratorView.tsx` updated for all three drive agents
- All agent system_prompts rewritten: "run exactly once, do not verify or retry" — prevents LLM issuing a second run_command for verification
- Explicit `sys.exit(0/1)` added to all agent-facing Python scripts (`drive_download.py`, `drive_upload.py`, `email_send.py`, `email_download_template.py`) — forces process termination; without this, unclosed HTTP connections keep the agent spinner running indefinitely

**Drive API fixes (p8):**
- `find_or_create_folder` in `drive_upload.py`: added `corpora="allDrives"` to `list()` and `supportsAllDrives=True` to `create()` — without `corpora`, Drive API uses `corpora='user'` by default and cannot see existing Shared Drive folders, silently creating duplicate period folders
- `find_payroll_file` in `drive_download.py`: added `supportsAllDrives=True` + `includeItemsFromAllDrives=True` — same fix, same root cause
- Upload OAuth scope changed from `drive.file` → `drive` — `drive.file` only sees files the application itself created; it cannot list or find pre-existing folders in a Shared Drive
- All three required flags for Shared Drive `list()` calls: `corpora="allDrives"`, `supportsAllDrives=True`, `includeItemsFromAllDrives=True`

**Exec server (p8):**
- `fs_hash` removed from `PERMITTED_COMMANDS` in `aetheris/native/aetheris_exec_server/src/runner.rs` — scanning is now owned by `f2-scanner`
- `priv/exec_server/aetheris_exec_server` is gitignored; must be rebuilt locally after any `runner.rs` change:
  ```bash
  cd ~/sandbox/elixirws/aetheris/native/aetheris_exec_server
  cargo build --release
  cp target/release/aetheris_exec_server ../../priv/exec_server/
  ```

**p8-005 — Orchestrator request history:**
- `useRequestHistory` hook — localStorage under `rig:orchestrator:history`, max 20 entries, deduplicates (same request moves to top)
- Typeahead dropdown: shown below textarea when input is non-empty and history entries match (case-insensitive substring); max 5 suggestions; clicking populates textarea
- Recent list: shown below Run button when textarea is empty and history non-empty; max 5 entries; clicking populates textarea
- `history.add(request)` called in Run button's `onClick` before `start(request)`

**P8 pending (not yet implemented):**
- Timestamped output folders — deprioritised; run log added to `generate_employee_payslips.py` instead
- Keyboard shortcut verification (Ctrl+Z, Escape in all inputs — fix committed but not end-to-end tested)

### Infrastructure — done

- Model parameterisation: `PROVENANCE_MODEL` → `AETHERIS_MODEL` → hardcoded fallback
- Capability matrix: committed at `docs/capability-matrix.md`
- Test sandbox: `provenance/scripts/create_test_sandbox.py` resets between runs

---

## What comes next

P8 is in progress. Remaining P8 item:
- Keyboard shortcut end-to-end verification

After P8, candidate priorities:
1. **Migrate orchestrator history to `data.db`** — localStorage is ephemeral (cleared on reinstall); move to SQLite for durability and analytics:
   - Table: `orchestrator_history (id INTEGER PK, request TEXT NOT NULL, created_at TIMESTAMP)`
   - New Tauri commands: `history_add(request: String) → usize`, `history_list(limit: usize) → Vec<HistoryEntry>`
   - `useRequestHistory` swaps `localStorage` for `invoke` calls — hook interface stays identical, `OrchestratorView` unchanged
   - `data.db` is already initialised at startup (`~/.local/share/dev.rig.app/data.db`); add a migration
   - Survives app reinstalls; queryable for usage analytics
2. **`eval_runs` surface in Rig** — pass rates, token efficiency by model, using existing `eval_runs` + `eval_baselines` tables in `aetheris.db`
3. **LiteLLM migration** (see `docs/aetheris/backlog/litellm-migration.md`)

---

## Key files

```
aetheris-agents/
  agents/
    orchestrator.exs              ← real LLM orchestrator (params extraction, env injection)
    mock_orchestrator.exs         ← kept for regression testing
  email/scripts/email_send.py     ← env var fallback for smtp.cfg (p7)
  aetheris/lib/aetheris/execution/
    pricing.ex                    ← model pricing table, compute_cost/3 (p6)
  rig/
    CLAUDE.md                     ← authoritative context for Claude Code (read first)
    src-tauri/src/
      lib.rs                      ← HarnessState + CorpusState + OrchestratorState + AgentConfigState
      commands/
        harness.rs                ← 4 read-only SQLite commands; get_harness_conn is pub(crate)
        orchestrate.rs            ← 4 process management commands; injects AgentConfigState env vars
        trajectory.rs             ← trajectory_load + trajectory_export (p4)
        capability_matrix.rs      ← capability_matrix_load parses docs/capability-matrix.md (p5)
        usage.rs                  ← usage_stats_load — 3 aggregate queries, per-run avg in Rust (p6)
        agent_config.rs           ← agent_config_get_all/set/delete + persist helper (p7)
    src/
      App.tsx                     ← routes: /harness, /orchestrator, /f2/*, /provenance, /settings
      components/
        shell/MainArea.tsx        ← controlled/uncontrolled tabs
        modules/
          harness/
            RunList.tsx           ← grouped by use case; useSessionRecord for collapse state (p5)
            TrajectoryView.tsx    ← meta panel with TokenSummaryRows (p4, p6)
            DiffView.tsx          ← two-run comparison with token/cost rows (p4, p6)
            CapabilityMatrixView.tsx  ← agent catalogue + Orchestrator pre-fill (p5)
            UsageView.tsx         ← aggregate token + cost stats (p6)
          orchestrator/OrchestratorView.tsx  ← p3: single-view workflow, no MainArea wrapper
          settings/
            AgentConfigTab.tsx    ← config UI, masked fields, per-row save/clear, external link icon (p7, p8)
            agentConfigDefs.ts    ← 12 known vars in 5 groups; linkPrefix on DRIVE_ROOT_FOLDER_ID (p8)
            SettingsRoute.tsx     ← two-tab settings wrapper (p7)
      hooks/
        useHarness.ts             ← polling useRunEvents + 3 other hooks
        useOrchestrator.ts        ← p3: full phase state machine
        useTrajectory.ts          ← trajectory load hook (p4)
        useRunDiff.ts             ← two-run diff hook with token/cost rows (p4, p6)
        useCapabilityMatrix.ts    ← capability matrix hook (p5)
        useSessionRecord.ts       ← sessionStorage-backed collapse state (p5)
        useUsageStats.ts          ← usage stats hook (p6)
        useAgentConfig.ts         ← agent config load/set/delete hook (p7)
        types.ts                  ← all TypeScript interfaces; PlanStep.context, OrchestratorPlan.params (p8)
  drive/
    agents/
      drive_download_orchestrator.exs  ← p8-004: download payroll CSV + email template only
      drive_upload_orchestrator.exs    ← p8-004: upload payslip PDFs only
      drive_orchestrator.exs           ← kept for standalone download+upload workflow
    scripts/
      drive_utils.py              ← period_folder_name, find_folder, resolve_period_folder (p8-002)
      drive_download.py           ← uses DRIVE_ROOT_FOLDER_ID + PAYSLIP_MONTH; sys.exit(0) (p8-002, p8)
      drive_upload.py             ← navigates root→period, corpora=allDrives, drive scope; sys.exit(0) (p8-002, p8)
    tests/
      test_drive_utils.py         ← 5 unit tests for period_folder_name (p8-002)
  docs/rig/milestones/
    p1/ p2/ p3/ p4/ p5/ p6/ p7/ p8/  ← p1-p7 done; p8 in progress
```

---

---

## Patterns established

### Elixir

**Agent model config (two-level fallback):**
```elixir
model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"
```

**`Application.ensure_all_started/1` returns `{:ok, []}` not `:ok`.**

**Sub-agent invocation via internal API (no shell spawning):**
```elixir
alias Aetheris.CLI.Commands.RunHelpers
:ok = RunHelpers.ensure_started()   # call once at top of script

{:ok, config} = RunHelpers.load_agent_file(agent_path)
{:ok, run_id} = Aetheris.start_run(config)
{:ok, _}      = RunHelpers.await_run(run_id, verbose: false)
```
`ensure_started()` must be called before any `start_run` call — it starts the supervision tree.
Runs in the same VM — sub-runs appear in `aetheris.db` and Rig trajectory normally.

**System.put_env/restore for per-step context injection:**
```elixir
# Snapshot originals, inject, run, restore
original = Enum.map(params, fn {k, _} -> {k, System.get_env(k)} end)
Enum.each(params, fn {k, v} -> System.put_env(k, v) end)

# ... load_agent_file → start_run → await_run ...

Enum.each(original, fn
  {k, nil} -> System.delete_env(k)
  {k, v}   -> System.put_env(k, v)
end)
```
Safe because orchestrator steps are sequential (not concurrent). Restore before `step_complete` IO.puts so env is clean for the next step. Sub-agents read env vars via `System.get_env` at `Code.eval_file` time — before the harness loop runs — so this is the only way to pass per-run params.

**`get_step_result` — true failure detection via trajectory (p8-003):**
`await_run` returns `{:ok, ...}` even when an agent's internal tool calls fail.
To detect real failures, read the trajectory JSON after the run and find the first
`tool_result` event with a non-zero `exit_code`:
```elixir
get_step_result = fn run_id ->
  db_path   = System.get_env("AETHERIS_DB_PATH") || raise "AETHERIS_DB_PATH not set"
  traj_path = Path.join([
    db_path |> Path.dirname() |> Path.dirname(),
    "priv", "runs", run_id, "trajectory.json"
  ])
  case File.read(traj_path) do
    {:ok, raw} ->
      events = raw |> Jason.decode!() |> Map.get("events", [])
      failed = Enum.find(events, fn e ->
        e["type"] == "tool_result" &&
        case Jason.decode(e["payload"]["output"] || "") do
          {:ok, output} -> is_integer(output["exit_code"]) && output["exit_code"] != 0
          _             -> false
        end
      end)
      case failed do
        nil -> :ok
        e ->
          stderr = case Jason.decode(e["payload"]["output"] || "") do
            {:ok, output} -> output["stderr"] || "Step failed"
            _             -> "Step failed"
          end
          {:error, String.trim(stderr)}
      end
    _ -> :ok
  end
end
```
Critical: `e["payload"]["output"]` is a **JSON-encoded string** `{"exit_code":N,"stderr":"...","stdout":""}`.
It must be decoded with `Jason.decode/1` — do NOT access `e["payload"]["exit_code"]` directly (that key does not exist).
Trajectory path derivation: `AETHERIS_DB_PATH → Path.dirname → Path.dirname → priv/runs/{run_id}/trajectory.json`

Use `Enum.reduce_while` to stop on first failure:
```elixir
result = Enum.reduce_while(plan["steps"], :ok, fn step, _acc ->
  # ... load and run sub-agent ...
  case get_step_result.(run_id) do
    :ok           -> {:cont, :ok}
    {:error, msg} ->
      IO.puts(Jason.encode!(%{type: "step_complete", step_id: step["id"], status: "failed", error: msg}))
      {:halt, :failed}
  end
end)
```

**Markdown fence stripping on LLM JSON responses:**
```elixir
raw_text
|> String.trim()
|> String.replace(~r/^```(?:json)?\n?/, "")
|> String.replace(~r/\n?```$/, "")
|> Jason.decode!()
```
Models often wrap JSON in code fences despite "JSON only" instructions. Always strip before decode.

**`System.halt(0)` on early exit in .exs scripts.**
Use `System.halt(0)` rather than letting the script fall off the end when exiting early (e.g. orchestration_cancelled). The harness may hold open file handles.

### Python / Google Drive API

**Google Drive scope — use `drive` for Shared Drive automation:**
```python
# Download scripts — read-only is sufficient
READONLY_SCOPE = ["https://www.googleapis.com/auth/drive.readonly"]

# Upload script — must list + create folders + upload files
UPLOAD_SCOPE = ["https://www.googleapis.com/auth/drive"]
```
`drive.file` only sees files the application itself created — it cannot list or find
pre-existing folders in a Shared Drive. Never use `drive.file` for server-side automation.

**All three flags required on every `files().list()` against a Shared Drive:**
```python
service.files().list(
    q=query,
    corpora="allDrives",            # ← essential; default 'user' cannot see Shared Drives
    supportsAllDrives=True,
    includeItemsFromAllDrives=True,
    fields="files(id, name)",
).execute()
```
`corpora="allDrives"` is the critical missing piece — `supportsAllDrives` + `includeItemsFromAllDrives`
alone are not sufficient. Omitting `corpora` causes the lookup to return empty, leading to duplicate
folder creation.

**`sys.exit(0/1)` at the end of every agent-facing script's `main()`:**
Without an explicit exit, Python keeps HTTP connections open. The Aetheris agent holds its
`run_command` call open waiting for EOF, causing the Rig spinner to spin indefinitely.
Always end `main()` with `sys.exit(0)` on success, `sys.exit(1)` on failure.

### Rust / Tauri

**Tauri plugin permissions must be declared in `capabilities/default.json`.**
Adding a plugin to `Cargo.toml` and registering it in `lib.rs` is not sufficient.
The capabilities file also needs explicit permission entries or the plugin's APIs silently fail:
```json
{
  "permissions": [
    "core:default",
    "shell:default",
    "shell:allow-open"
  ]
}
```
File: `src-tauri/capabilities/default.json`. Each plugin has its own permission identifiers.
For `tauri-plugin-shell`: `"shell:default"` enables the plugin; `"shell:allow-open"` allows `open()`.

**Tauri v2 `invoke()` keys must be camelCase.**
Tauri v2 deserializes arguments by converting JS camelCase keys → Rust snake_case.
Always use camelCase keys in `invoke()`:
```typescript
invoke('trajectory_load', { runId })          // ✓ runId → run_id
invoke('trajectory_load', { run_id: runId })  // ✗ fails — "missing required key runId"
```
Error form: `invalid args runId for command X: missing required key runId`

After wiring any new command, run this sweep before testing:
```bash
grep -rn "invoke(" src/hooks/ src/components/ --include="*.ts" --include="*.tsx" \
  | grep "_id\|_path\|_dir\|_type\|_name\|_count\|_status"
```
Any hit with a snake_case key in the args object is a bug.

**`harness_connection_status` returns `Ok`, not `Err`.**
Returns `Ok(HarnessStatus { connected: false, error: Some(...) })` when not
connected. All other harness commands return `Err("harness not connected")`.
Check `data.connected`, not the Result.

**`pub(crate)` on shared helpers between command modules.**
```rust
// harness.rs
pub(crate) fn get_harness_conn<'a>(...) -> ... { ... }
// usage.rs
use crate::commands::harness::get_harness_conn;
```

**`json_extract IS NOT NULL` filter for optional payload fields.**
```sql
WHERE json_extract(payload_json, '$.cost_usd') IS NOT NULL
```
Never use `COALESCE` alone — it masks missing data as zero.

**Compute per-run averages in Rust, not SQL `AVG()`.**
`SQL AVG()` averages per-event cost, not per-run cost:
```rust
let avg_cost_usd = if run_count > 0 { total_cost_usd / run_count as f64 } else { 0.0 };
```

**`AgentConfigState` pattern — no plugin needed.**
HashMap cache loaded from JSON file on startup; written on every change via `persist()` helper.
`serde_json` is already a dep — no `tauri-plugin-store` required:
```rust
pub struct AgentConfigState {
    pub store_path: std::path::PathBuf,
    pub cache:      Mutex<HashMap<String, String>>,
}
```
File lives at `app_data_dir/agent-config.json`. Read plain text at startup; write on every set/delete.

**`OrchestratorState` pattern.**
Long-running child processes stored as `Arc<Mutex<Child>>` in a job map.
Reader thread pushes parsed `serde_json::Value` to `Arc<Mutex<Vec>>` buffer.
Frontend drains buffer via `orchestrate_poll`. `AtomicBool` signals EOF.

**`orchestrate_approve` clones the stdin Arc before releasing the jobs lock.**
```rust
let stdin = {
    let jobs = state.jobs.lock().unwrap();
    let job  = jobs.get(&job_id).ok_or("job not found")?;
    job.stdin.clone()  // Arc clone — cheap; jobs lock released here
};
let mut guard = stdin.lock().unwrap();
let result = writeln!(guard, "{}", msg).map_err(|e| format!(...));
result  // bind to variable — forces guard to drop before function exits
```

**Env var delivery for Mix scripts.**
Pass request data via environment variable (`ORCHESTRATOR_REQUEST`), not CLI args.
`mix run script.exs arg` passes args to Mix, not to the script.

### React / Frontend

**Controlled/uncontrolled `MainArea`.**
Optional `activeTab`/`onTabChange` props. Without: internal state. With: parent owns tab.

**`HarnessRoute` pattern.**
When a route needs shared state across tabs, create a `*Route` component that owns state and wraps `MainArea` with `activeTab`/`onTabChange`.

**`hasData` check before aggregating optional payload fields.**
Return `null` (not `0`) for pre-instrumentation runs — so `formatCost`/`formatTokens` render `—`:
```typescript
const hasData = llmEvents.some((e) => e.payload['cost_usd'] != null);
if (!hasData) return null;
```

**`formatCost` / `formatTokens` duplication.**
Currently in `TrajectoryView.tsx`, `UsageView.tsx`, `useRunDiff.ts`. Extract to `src/lib/format.ts` if they spread to a fourth location.

**`useSessionRecord(storageKey, defaultValue)` for collapse state persistence.**
```typescript
const record = useSessionRecord('run-list-groups', false); // false = collapsed by default
record.get(label)            // boolean
record.set(label, value)     // persist one
record.setAll(labels, value) // collapse/expand all
```
Backed by `sessionStorage` — survives page refresh within a session, cleared on tab close.

**`useState(prefill)` seeding from `useLocation().state`.**
Derive prefill before `useState`, pass as initial value. Do NOT use `useEffect` — causes flash.

**Poll effect deps `[jobId, phase, processMessage]` (`useOrchestrator`).**
`phase` must be in deps so polling stops when a terminal state is set.

**`OrchestratorView` is not a tabs component.**
Single-view workflow — renders directly into the route's padded div, no `MainArea` wrapper.

**`loading && !data` for polling-safe skeletons.**
Shows skeleton on initial load only. Prevents flash on every poll refetch.

**Filter before group.**
Always apply filters to the flat list before `groupRuns()`. Never filter after grouping.

**localStorage MRU list pattern (`useRequestHistory`).**
Initialise state lazily from localStorage in the `useState` initialiser (not `useEffect`) to avoid a blank→populated flash. Deduplicate with `filter` before prepending. Cap with `slice`. Write back on every add. Key: `rig:orchestrator:history`.
```typescript
const [history, setHistory] = useState<string[]>(() => {
  try {
    const raw = localStorage.getItem('rig:orchestrator:history');
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
});

const add = useCallback((request: string) => {
  setHistory((prev) => {
    const deduped = [request, ...prev.filter((r) => r !== request)].slice(0, 20);
    localStorage.setItem('rig:orchestrator:history', JSON.stringify(deduped));
    return deduped;
  });
}, []);
```
Same pattern works for any MRU list. When durability across reinstalls matters, migrate to `data.db` (see backlog).

---

## Database gotchas

SQLite and DuckDB have different type systems — do not mix up casting rules.

**SQLite (aetheris.db):** timestamps are TEXT in ISO 8601 format — no casting needed.

**DuckDB (corpus):**
- `TIMESTAMP` columns must be `CAST(col AS VARCHAR)` when reading as Rust `String`
- Unix epoch seconds need `to_timestamp()` on INSERT
- `INSERT OR REPLACE` fails with multiple unique constraints — use `ON CONFLICT (col) DO UPDATE SET`
- No auto-increment without `SEQUENCE` — define `seq_<table>` and `DEFAULT nextval()`
- Use `now()` not `CURRENT_TIMESTAMP` in `DO UPDATE SET` clauses

---

## Quick commands

```bash
# Open Rig (dev mode)
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=$(realpath ~/sandbox/elixirws/aetheris/priv/aetheris.db)
export AETHERIS_AGENTS_PATH=$(realpath ~/sandbox/elixirws/aetheris-agents)
export PROVENANCE_DB_PATH=$(realpath ~/sandbox/provenance-test/corpus.duckdb)  # optional
cargo tauri dev
# NOTE: never use bare ~ in env vars — Rust receives the literal "~/…" unexpanded.
# Use $(realpath …) or $HOME/…

# Test real orchestrator manually (from aetheris/)
cd ~/sandbox/elixirws/aetheris
(sleep 12; echo '{"approved":true}') \
  | ORCHESTRATOR_REQUEST="generate payslips for apr 2026" \
    AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents \
    mix run ../aetheris-agents/agents/orchestrator.exs

# Test mock orchestrator manually (from aetheris/)
(sleep 3; echo '{"approved":true}') \
  | ORCHESTRATOR_REQUEST="email payslips" \
    mix run ../aetheris-agents/agents/mock_orchestrator.exs

# TypeScript build check (from rig/)
cd ~/sandbox/elixirws/aetheris-agents/rig && bun run build

# Rust build check (from rig/)
cd ~/sandbox/elixirws/aetheris-agents/rig/src-tauri && cargo build

# Check agent config store (not sqlite — values in JSON file)
cat ~/.local/share/dev.rig.app/agent-config.json

# Run full payslip pipeline via Rig Orchestrator (4-step)
# Prerequisites — Settings → Agent Config:
#   GOOGLE_SERVICE_ACCOUNT  absolute path to service account JSON key file
#   DRIVE_ROOT_FOLDER_ID    folder ID of the payslips folder in Shared Drive
#   SMTP_HOST / SMTP_USER / SMTP_PASSWORD / SMTP_FROM / SMTP_TO
# 1. Orchestrator → type: "generate and email payslips for april 2026" (or any month)
# 2. Review 4-step plan (PAYSLIP_MONTH extracted automatically), approve
#    Step 1: drive_download_orchestrator  — downloads payroll.csv + email template
#    Step 2: payslip_orchestrator         — generates PDF payslips
#    Step 3: drive_upload_orchestrator    — uploads PDFs to Shared Drive
#    Step 4: email_orchestrator           — sends payslip emails to finance inbox

# Check a harness run
cd ~/sandbox/elixirws/aetheris
mix aetheris inspect <run_id>
mix aetheris list --limit 5

# camelCase sweep — run before testing any new Tauri command
grep -rn "invoke(" src/hooks/ src/components/ --include="*.ts" --include="*.tsx" \
  | grep "_id\|_path\|_dir\|_type\|_name\|_count\|_status"
```

---

## Next session starter

```
Read docs/handoff-aetheris-provenance-rig.md.

Continuing Rig development. P8 is partially complete:
- Done: plan enrichment, drive folder convention, orchestrator
  reliability, drive agent split, request history
- Pending: timestamped output folders (deprioritised in favour of
  run log), keyboard shortcuts verification

Suggested next priorities:
1. Migrate orchestrator history from localStorage to data.db
   (spec in handoff backlog section)
2. eval_runs surface in Rig — pass rates, token efficiency by model,
   using existing eval_runs + eval_baselines tables in aetheris.db
3. LiteLLM migration (see docs/aetheris/backlog/litellm-migration.md)

What would you like to work on?
```
