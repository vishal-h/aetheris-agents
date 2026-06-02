# rig/p7: Agent config settings

## Context

Rig-launched agents fail silently when env vars like `ANTHROPIC_API_KEY`,
`SMTP_PASSWORD`, or `PAYSLIP_MONTH` are not set. This issue adds an Agent
Config tab to the settings panel where users can configure these values
persistently. Values are stored via `tauri-plugin-store` and automatically
injected when `orchestrate_start` spawns the child process.

All work is in `aetheris-agents/rig/`.

---

## What to build

### 1. Add `tauri-plugin-store`

In `src-tauri/Cargo.toml` — add to `[dependencies]`:
```toml
tauri-plugin-store = "2"
```

Register in `lib.rs` inside `.setup()`:
```rust
.plugin(tauri_plugin_store::Builder::default().build())
```

The store file path: `app_data_dir/agent-config.json`. Derive with:
```rust
let store_path = app.path().app_data_dir()
    .expect("app data dir")
    .join("agent-config.json");
```

---

### 2. `AgentConfigState` (add to `src-tauri/src/lib.rs`)

```rust
use std::sync::Mutex;
use std::collections::HashMap;

pub struct AgentConfigState {
    pub store_path: std::path::PathBuf,
    pub cache:      Mutex<HashMap<String, String>>,
}
```

Initialise in `.setup()`:

```rust
let store_path = app.path().app_data_dir()
    .expect("app data dir")
    .join("agent-config.json");

// Load existing values into cache
let cache = if store_path.exists() {
    let raw = std::fs::read_to_string(&store_path).unwrap_or_default();
    serde_json::from_str::<HashMap<String, String>>(&raw).unwrap_or_default()
} else {
    HashMap::new()
};

app.manage(AgentConfigState {
    store_path,
    cache: Mutex::new(cache),
});
```

Register in `generate_handler![]`:
```rust
commands::agent_config::agent_config_get_all,
commands::agent_config::agent_config_set,
commands::agent_config::agent_config_delete,
```

---

### 3. `src-tauri/src/commands/agent_config.rs`

Three commands. Reads/writes a plain JSON file — no encryption.

```rust
use crate::AgentConfigState;
use std::collections::HashMap;
use tauri::State;

fn persist(state: &AgentConfigState) -> Result<(), String> {
    let cache = state.cache.lock().unwrap();
    let json = serde_json::to_string_pretty(&*cache)
        .map_err(|e| format!("serialise failed: {}", e))?;
    std::fs::write(&state.store_path, json)
        .map_err(|e| format!("write failed: {}", e))
}

#[tauri::command]
pub fn agent_config_get_all(
    state: State<'_, AgentConfigState>,
) -> Result<HashMap<String, String>, String> {
    Ok(state.cache.lock().unwrap().clone())
}

#[tauri::command]
pub fn agent_config_set(
    state: State<'_, AgentConfigState>,
    key:   String,
    value: String,
) -> Result<(), String> {
    state.cache.lock().unwrap().insert(key, value);
    persist(&state)
}

#[tauri::command]
pub fn agent_config_delete(
    state: State<'_, AgentConfigState>,
    key:   String,
) -> Result<(), String> {
    state.cache.lock().unwrap().remove(&key);
    persist(&state)
}
```

Register in `commands/mod.rs`:
```rust
pub mod agent_config;
```

---

### 4. Inject config into `orchestrate_start`

In `src-tauri/src/commands/orchestrate.rs`:

```rust
use crate::AgentConfigState;

#[tauri::command]
pub fn orchestrate_start(
    state:        State<'_, OrchestratorState>,
    config_state: State<'_, AgentConfigState>,   // ← add
    request:      String,
) -> Result<String, String> {
    // ... existing path derivation ...

    // Read agent config values
    let agent_config = config_state.cache.lock().unwrap().clone();

    let mut cmd = std::process::Command::new("mix");
    cmd.args(["run", &script_path])
        .env("ORCHESTRATOR_REQUEST", &request)
        .current_dir(aetheris_dir)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null());

    // Inject all configured values
    for (key, value) in &agent_config {
        cmd.env(key, value);
    }

    let mut child = cmd.spawn()
        .map_err(|e| format!("spawn failed: {}", e))?;

    // ... rest unchanged ...
}
```

---

### 5. TypeScript types (add to `src/hooks/types.ts`)

```typescript
export interface AgentConfigEntry {
  key:       string;
  label:     string;
  group:     string;
  masked:    boolean;   // true for credentials — show/hide toggle
  value?:    string;    // present when set
}
```

Export from `src/hooks/index.ts`.

---

### 6. Known variable definitions

Define in `src/components/modules/settings/agentConfigDefs.ts`:

```typescript
import type { AgentConfigEntry } from '@/hooks/types';

export const AGENT_CONFIG_DEFS: Omit<AgentConfigEntry, 'value'>[] = [
  // Harness
  { key: 'AETHERIS_MODEL',    label: 'Default model',    group: 'Harness',    masked: false },
  { key: 'AETHERIS_PROVIDER', label: 'Default provider', group: 'Harness',    masked: false },

  // Anthropic
  { key: 'ANTHROPIC_API_KEY', label: 'API key',          group: 'Anthropic',  masked: true  },

  // SMTP
  { key: 'SMTP_HOST',         label: 'Host',             group: 'SMTP',       masked: false },
  { key: 'SMTP_PORT',         label: 'Port',             group: 'SMTP',       masked: false },
  { key: 'SMTP_USER',         label: 'Username',         group: 'SMTP',       masked: false },
  { key: 'SMTP_PASSWORD',     label: 'Password',         group: 'SMTP',       masked: true  },

  // Google Drive
  { key: 'GOOGLE_CREDENTIALS',label: 'Credentials JSON', group: 'Google Drive', masked: true },

  // Provenance
  { key: 'PROVENANCE_NAS_PATH', label: 'NAS archive path', group: 'Provenance', masked: false },
];
```

---

### 7. `src/hooks/useAgentConfig.ts`

```typescript
import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';

export function useAgentConfig() {
  const [values,  setValues]  = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    invoke<Record<string, string>>('agent_config_get_all')
      .then((v) => { setValues(v);  setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, []);

  useEffect(() => { load(); }, [load]);

  const set = useCallback(async (key: string, value: string) => {
    await invoke('agent_config_set', { key, value });
    setValues((prev) => ({ ...prev, [key]: value }));
  }, []);

  const remove = useCallback(async (key: string) => {
    await invoke('agent_config_delete', { key });
    setValues((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  return { values, loading, error, set, remove, reload: load };
}
```

Export from `src/hooks/index.ts`.

---

### 8. `src/components/modules/settings/AgentConfigTab.tsx`

```tsx
import { useState } from 'react';
import { Eye, EyeOff, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAgentConfig } from '@/hooks/useAgentConfig';
import { AGENT_CONFIG_DEFS } from './agentConfigDefs';

// ── Single config row ─────────────────────────────────────────────────────────

interface ConfigRowProps {
  label:   string;
  envKey:  string;
  masked:  boolean;
  value:   string | undefined;
  onSave:  (key: string, value: string) => void;
  onClear: (key: string) => void;
}

function ConfigRow({ label, envKey, masked, value, onSave, onClear }: ConfigRowProps) {
  const [draft,   setDraft]   = useState(value ?? '');
  const [visible, setVisible] = useState(false);
  const isSet = value !== undefined && value !== '';
  const isDirty = draft !== (value ?? '');

  return (
    <div className="flex items-center gap-3 py-2.5 border-b last:border-b-0">
      <div className="w-40 shrink-0">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground font-mono">{envKey}</p>
      </div>

      <div className="flex-1 relative">
        <input
          type={masked && !visible ? 'password' : 'text'}
          className="w-full rounded-md border border-input bg-background px-3 py-1.5
                     text-sm font-mono focus-visible:outline-none
                     focus-visible:ring-2 focus-visible:ring-ring"
          placeholder={isSet ? '••••••••' : 'Not set'}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
        />
        {masked && (
          <button
            className="absolute right-2 top-1/2 -translate-y-1/2
                       text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => setVisible((v) => !v)}
          >
            {visible
              ? <EyeOff className="h-3.5 w-3.5" />
              : <Eye    className="h-3.5 w-3.5" />}
          </button>
        )}
      </div>

      <div className="flex gap-1 shrink-0">
        {isDirty && draft !== '' && (
          <Button
            size="sm"
            onClick={() => { onSave(envKey, draft); }}
          >
            Save
          </Button>
        )}
        {isSet && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { onClear(envKey); setDraft(''); }}
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}

// ── Group section ─────────────────────────────────────────────────────────────

function ConfigGroup({
  group,
  defs,
  values,
  onSave,
  onClear,
}: {
  group:   string;
  defs:    typeof AGENT_CONFIG_DEFS;
  values:  Record<string, string>;
  onSave:  (key: string, value: string) => void;
  onClear: (key: string) => void;
}) {
  return (
    <section className="mb-6">
      <h3 className="text-xs font-semibold uppercase tracking-wide
                     text-muted-foreground mb-2">{group}</h3>
      <div className="rounded-md border">
        {defs.map((def) => (
          <ConfigRow
            key={def.key}
            label={def.label}
            envKey={def.key}
            masked={def.masked}
            value={values[def.key]}
            onSave={onSave}
            onClear={onClear}
          />
        ))}
      </div>
    </section>
  );
}

// ── Main tab ──────────────────────────────────────────────────────────────────

export function AgentConfigTab() {
  const { values, loading, error, set, remove } = useAgentConfig();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32
                      text-muted-foreground text-sm">
        Loading…
      </div>
    );
  }

  if (error) {
    return <div className="p-4 text-sm text-red-600">{error}</div>;
  }

  // Group defs by group name
  const groups = Array.from(
    new Set(AGENT_CONFIG_DEFS.map((d) => d.group))
  );

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">

        {/* Storage notice */}
        <div className="rounded-md border border-amber-200 bg-amber-50
                        px-4 py-3 text-xs text-amber-800 mb-6">
          Values are stored in plaintext on disk in the app data directory.
          Do not store production credentials on shared machines.
        </div>

        {groups.map((group) => (
          <ConfigGroup
            key={group}
            group={group}
            defs={AGENT_CONFIG_DEFS.filter((d) => d.group === group)}
            values={values}
            onSave={set}
            onClear={remove}
          />
        ))}

      </div>
    </div>
  );
}
```

---

### 9. Wire into the settings route

The existing settings route renders `WatchedFoldersSettings`. Extend it to
use `MainArea` with two tabs.

In `App.tsx` (or wherever the settings route is defined):

```tsx
import { AgentConfigTab } from '@/components/modules/settings/AgentConfigTab';

// Wrap existing WatchedFoldersSettings in a tabbed layout:
<Route path="/settings" element={
  <SettingsRoute />
} />
```

Create `src/components/modules/settings/SettingsRoute.tsx`:

```tsx
import { useState } from 'react';
import { MainArea } from '@/components/shell/MainArea';
import { WatchedFoldersSettings } from '@/components/modules/f2';
import { AgentConfigTab } from './AgentConfigTab';

export function SettingsRoute() {
  const [activeTab, setActiveTab] = useState('watched-folders');

  const tabs = [
    {
      id:      'watched-folders',
      label:   'Watched Folders',
      content: <WatchedFoldersSettings />,
    },
    {
      id:      'agent-config',
      label:   'Agent Config',
      content: <AgentConfigTab />,
    },
  ];

  return (
    <MainArea
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
    />
  );
}
```

Check `App.tsx` for how the settings route is currently rendered — if it
renders `WatchedFoldersSettings` directly, replace with `<SettingsRoute />`.

---

## Acceptance criteria

- [ ] `tauri-plugin-store = "2"` in `Cargo.toml`, registered in `lib.rs`
- [ ] `AgentConfigState` with `store_path` and `cache` in `lib.rs`
- [ ] Cache loaded from disk on startup if file exists
- [ ] `agent_config_get_all`, `agent_config_set`, `agent_config_delete`
      commands — all persist to disk
- [ ] `orchestrate_start` injects all cache values as env vars before spawn
- [ ] Settings panel has two tabs: Watched Folders + Agent Config
- [ ] Agent Config tab shows all 9 known variables grouped by category
- [ ] Credential fields masked by default with show/hide toggle
- [ ] Save button appears only when field is dirty and non-empty
- [ ] Clear button appears only when a value is set
- [ ] Amber storage notice displayed at top of tab
- [ ] Values persist across Rig restarts
- [ ] `cargo build` exits 0, zero warnings
- [ ] `bun run build` exits 0, zero TypeScript errors
- [ ] No TypeScript `any`

---

## Files to create/modify

**Create:**
- `src-tauri/src/commands/agent_config.rs`
- `src/hooks/useAgentConfig.ts`
- `src/components/modules/settings/agentConfigDefs.ts`
- `src/components/modules/settings/AgentConfigTab.tsx`
- `src/components/modules/settings/SettingsRoute.tsx`

**Modify:**
- `src-tauri/Cargo.toml` — add `tauri-plugin-store = "2"`
- `src-tauri/src/lib.rs` — add `AgentConfigState`, register plugin and
  3 new commands
- `src-tauri/src/commands/mod.rs` — `pub mod agent_config;`
- `src-tauri/src/commands/orchestrate.rs` — add `AgentConfigState` param,
  inject env vars before spawn
- `src/hooks/types.ts` — add `AgentConfigEntry`
- `src/hooks/index.ts` — export `useAgentConfig` and `AgentConfigEntry`
- `src/App.tsx` — replace `WatchedFoldersSettings` in settings route with
  `<SettingsRoute />`

---

## Notes

**`tauri-plugin-store` vs manual JSON file.** The spec uses a manual
`HashMap` cache + JSON file rather than the plugin's store API, because the
plugin's async API adds complexity for what is essentially a simple read-at-
startup / write-on-change pattern. If the plugin is already pulled in as a
dependency for another reason, use its API instead. If adding it only for
this feature, the manual approach in `agent_config.rs` is simpler and has
no external dependency — just `serde_json` which is already present.

**Reconsider the plugin dependency.** Given the above, you may not need
`tauri-plugin-store` at all. The `AgentConfigState` with a JSON file path
and in-memory cache is self-contained. Remove `tauri-plugin-store` from
`Cargo.toml` if you go with the manual approach — it avoids an unnecessary
dependency.

**`orchestrate_start` signature change.** Adding `config_state:
State<'_, AgentConfigState>` as a second parameter changes the command
signature. Tauri discovers parameters by name, so adding a new state
parameter is safe — the frontend call `invoke('orchestrate_start', {
request })` is unchanged.

**`ConfigRow` local draft state.** Each row manages its own draft
independently. Saving one row does not affect others. The `isDirty` check
prevents spurious save calls when the user clicks into a field without
changing it.

**Show/hide toggle for masked fields.** The toggle switches between
`type="password"` and `type="text"`. The button is positioned absolutely
inside the input container — ensure the input has enough right padding
(`pr-8`) so text doesn't overlap the button.

**`GOOGLE_CREDENTIALS` as a JSON blob.** This value may be a multi-line
JSON string. The input renders it as a single-line field — the full value
is stored correctly even if it appears truncated. A future improvement could
use a textarea for this specific key.
