# Agent Config — Architecture Reference

Use this document to orient a new conversation about adding,
changing, or querying agent configuration in Rig.

---

## How agent config is stored

Values are stored in a plain JSON file in the Tauri app data directory:

```
~/.local/share/dev.rig.app/agent-config.json   # Linux
~/Library/Application Support/dev.rig.app/agent-config.json  # macOS
```

Format — a flat JSON object, string keys and string values:

```json
{
  "ANTHROPIC_API_KEY": "sk-ant-...",
  "SMTP_HOST": "smtp.gmail.com",
  "SMTP_PORT": "587",
  "SMTP_USER": "sender@example.com",
  "SMTP_PASSWORD": "...",
  "SMTP_FROM": "payroll@example.com",
  "SMTP_TO": "payroll@example.com",
  "GOOGLE_SERVICE_ACCOUNT": "/path/to/service-account.json",
  "DRIVE_ROOT_FOLDER_ID": "1-6r5e5KrR38ghk6uCTD09Dw4-U_L94Fs",
  "PROVENANCE_NAS_PATH": "/mnt/nas/archive",
  "AETHERIS_MODEL": "claude-haiku-4-5-20251001",
  "AETHERIS_PROVIDER": "anthropic"
}
```

**No encryption.** Values are plaintext. The UI shows a warning.
Do not store production credentials on shared machines.

---

## How the harness picks it up

When the Orchestrator spawns a child process (`mix run agents/orchestrator.exs`),
`orchestrate_start` in `rig/src-tauri/src/commands/orchestrate.rs` reads
all values from `AgentConfigState` and injects each as an env var:

```rust
let agent_config = config_state.cache.lock().unwrap().clone();
let mut cmd = std::process::Command::new("mix");
cmd.args(["run", &script_path])
    .env("ORCHESTRATOR_REQUEST", &request)
    .current_dir(aetheris_dir);

for (key, value) in &agent_config {
    cmd.env(key, value);
}
```

Sub-agents read them via `System.get_env/1` (Elixir) or `os.environ.get`
(Python) as normal environment variables. The harness itself does not
read `agent-config.json` — only Rig does.

**Key point:** agent config values are injected at spawn time into the
orchestrator process. The orchestrator then injects them into sub-agents
via `System.put_env` before calling `RunHelpers.load_agent_file`.

---

## Rust backend

### State struct (`lib.rs`)

```rust
pub struct AgentConfigState {
    pub store_path: std::path::PathBuf,  // path to agent-config.json
    pub cache:      Mutex<HashMap<String, String>>,  // in-memory cache
}
```

The cache is loaded from disk at startup. Every write persists
to disk immediately via the `persist` helper.

### Commands (`commands/agent_config.rs`)

| Command | Args | Returns | Description |
|---------|------|---------|-------------|
| `agent_config_get_all` | — | `HashMap<String, String>` | All stored values |
| `agent_config_set` | `key, value` | `()` | Set one value, persist |
| `agent_config_delete` | `key` | `()` | Remove one value, persist |
| `agent_config_export` | — | `String` | Pretty-printed JSON of all 12 known keys |
| `agent_config_import` | `values` | `usize` | Merge a map, persist, return count |

---

## Frontend

### Hook (`src/hooks/useAgentConfig.ts`)

```typescript
const { values, loading, error, set, remove, reload,
        exportConfig, importConfig } = useAgentConfig();
```

- `values` — `Record<string, string>` of currently stored values
- `set(key, value)` — calls `agent_config_set`, updates local state
- `remove(key)` — calls `agent_config_delete`, updates local state
- `exportConfig()` — builds JSON from all known defs + stored values,
  returns as string (frontend-only, no Tauri call)
- `importConfig(json)` — calls `agent_config_import`, refreshes state

### Known variable definitions (`src/components/modules/settings/agentConfigDefs.ts`)

Each entry in `AGENT_CONFIG_DEFS` defines one row in the UI:

```typescript
interface AgentConfigEntry {
  key:          string;    // env var name, e.g. "SMTP_HOST"
  label:        string;    // display label, e.g. "Host"
  group:        string;    // section header, e.g. "SMTP"
  masked:       boolean;   // true = password field with show/hide
  placeholder?: string;    // hint shown when not set
  linkPrefix?:  string;    // if set, shows external link icon
  value?:       string;    // present when set
}
```

Current groups and keys:

| Group | Keys |
|-------|------|
| Harness | `AETHERIS_MODEL`, `AETHERIS_PROVIDER` |
| Anthropic | `ANTHROPIC_API_KEY` |
| SMTP | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TO` |
| Google Drive | `GOOGLE_SERVICE_ACCOUNT`, `DRIVE_ROOT_FOLDER_ID` |
| Provenance | `PROVENANCE_NAS_PATH` |

### Settings UI (`src/components/modules/settings/`)

```
SettingsRoute.tsx          ← two-tab MainArea: Watched Folders + Agent Config
AgentConfigTab.tsx         ← renders groups of ConfigRow components
agentConfigDefs.ts         ← AGENT_CONFIG_DEFS array (the known variables)
```

`SettingsRoute` is rendered at `/settings` in `App.tsx`.

---

## Adding a new config key

**1. Add to `agentConfigDefs.ts`:**

```typescript
{ key: 'GITHUB_TOKEN', label: 'GitHub token', group: 'GitHub',
  masked: true, placeholder: 'ghp_...' },
```

That's it for the UI — the row appears automatically in the correct group.
If the group name is new, it becomes a new section header.

**2. If the agent needs it:**

The value is injected as `GITHUB_TOKEN` env var when the orchestrator
spawns. Python scripts read it via `os.environ.get("GITHUB_TOKEN")`,
Elixir scripts via `System.get_env("GITHUB_TOKEN")`. No other changes.

**3. If you want it shown in the Orchestrator plan view:**

Add to `STEP_CONFIG_HINTS` in `OrchestratorView.tsx`:

```typescript
'agents/my_agent.exs': ['GITHUB_TOKEN'],
```

The value appears alongside the step during plan_ready and executing.
Masked keys (like tokens) are shown as-is — add masking logic if needed.

---

## Export / Import

The Export button downloads all 12 known keys as `agent-config.json`.
Unset keys use their placeholder as a hint value. Keys are sorted
alphabetically. The file is human-editable — fill in real values and
Import to apply.

Import merges silently — existing keys not in the file are unchanged.
A "N values imported." confirmation appears for 3 seconds.

---

## Backlog: migrate to data.db

Currently `localStorage` is used for orchestrator request history.
Agent config uses its own JSON file. The long-term plan:

- Agent config → `data.db` table (`agent_config` key/value)
- Orchestrator history → `data.db` table (`orchestrator_history`)
- New Tauri commands: `history_add`, `history_list`
- `useRequestHistory` swaps `localStorage` for `invoke` calls —
  hook interface stays identical, `OrchestratorView` unchanged

`data.db` is already initialised by Rig at startup:
`~/.local/share/dev.rig.app/data.db`
