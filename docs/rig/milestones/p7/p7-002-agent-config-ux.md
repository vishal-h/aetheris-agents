# rig/p7-002: Agent config — placeholders + export/import

## Context

The Agent Config tab shows "Not set" for every unset field with no indication
of what format or value is expected. This issue adds placeholder text to each
field and export/import buttons to the tab header for easier credential
management.

All work is in `aetheris-agents/rig/`. No new Tauri commands needed for
placeholders. Export/import use two new commands.

---

## What to build

### 1. Add `placeholder` to `agentConfigDefs.ts`

Extend the def type and add placeholder text for every entry:

```typescript
export const AGENT_CONFIG_DEFS: Omit<AgentConfigEntry, 'value'>[] = [
  // Harness
  { key: 'AETHERIS_MODEL',      label: 'Default model',     group: 'Harness',
    masked: false, placeholder: 'claude-haiku-4-5-20251001' },
  { key: 'AETHERIS_PROVIDER',   label: 'Default provider',  group: 'Harness',
    masked: false, placeholder: 'anthropic' },

  // Anthropic
  { key: 'ANTHROPIC_API_KEY',   label: 'API key',           group: 'Anthropic',
    masked: true,  placeholder: 'sk-ant-...' },

  // SMTP
  { key: 'SMTP_HOST',           label: 'Host',              group: 'SMTP',
    masked: false, placeholder: 'smtp.gmail.com' },
  { key: 'SMTP_PORT',           label: 'Port',              group: 'SMTP',
    masked: false, placeholder: '587' },
  { key: 'SMTP_USER',           label: 'Username',          group: 'SMTP',
    masked: false, placeholder: 'sender@example.com' },
  { key: 'SMTP_PASSWORD',       label: 'Password',          group: 'SMTP',
    masked: true,  placeholder: 'app password (not your login password)' },
  { key: 'SMTP_FROM',           label: 'From address',      group: 'SMTP',
    masked: false, placeholder: 'payroll@example.com' },
  { key: 'SMTP_TO',             label: 'To address',        group: 'SMTP',
    masked: false, placeholder: 'payroll@example.com' },

  // Google Drive
  { key: 'GOOGLE_CREDENTIALS',  label: 'Credentials JSON',  group: 'Google Drive',
    masked: true,  placeholder: '{"type":"service_account",...}' },

  // Provenance
  { key: 'PROVENANCE_NAS_PATH', label: 'NAS archive path',  group: 'Provenance',
    masked: false, placeholder: '/mnt/nas/archive' },
];
```

Update `AgentConfigEntry` in `types.ts`:
```typescript
export interface AgentConfigEntry {
  key:          string;
  label:        string;
  group:        string;
  masked:       boolean;
  placeholder?: string;
  value?:       string;
}
```

In `ConfigRow`, pass `placeholder` through `ConfigRowProps` → `ConfigGroup` → `ConfigRow`
and use it in the input:
```tsx
placeholder={isSet ? '••••••••' : (placeholder ?? 'Not set')}
```

---

### 2. Export / Import commands

Add to `src-tauri/src/commands/agent_config.rs`:

```rust
#[tauri::command]
pub fn agent_config_export(
    state: State<'_, AgentConfigState>,
) -> Result<String, String> {
    let cache = state.cache.lock().unwrap();
    serde_json::to_string_pretty(&*cache)
        .map_err(|e| format!("serialise failed: {}", e))
}

#[tauri::command]
pub fn agent_config_import(
    state:  State<'_, AgentConfigState>,
    values: std::collections::HashMap<String, String>,
) -> Result<usize, String> {
    let count = values.len();
    {
        let mut cache = state.cache.lock().unwrap();
        for (k, v) in values {
            cache.insert(k, v);
        }
    }
    persist(&state)?;
    Ok(count)
}
```

Register in `lib.rs`:
```rust
commands::agent_config::agent_config_export,
commands::agent_config::agent_config_import,
```

---

### 3. Export / Import in `useAgentConfig.ts`

```typescript
const exportConfig = useCallback(async (): Promise<string> => {
  return invoke<string>('agent_config_export');
}, []);

const importConfig = useCallback(async (json: string): Promise<number> => {
  const parsed = JSON.parse(json) as Record<string, string>;
  const count = await invoke<number>('agent_config_import', { values: parsed });
  const updated = await invoke<Record<string, string>>('agent_config_get_all');
  setValues(updated);
  return count;
}, []);
```

---

### 4. Export / Import UI in `AgentConfigTab.tsx`

Export handler — browser download via temporary anchor:
```typescript
async function handleExport() {
  const json = await exportConfig();
  const blob = new Blob([json], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'agent-config.json';
  a.click();
  URL.revokeObjectURL(url);
}
```

Import handler — hidden file input:
```typescript
async function handleImport() {
  const input    = document.createElement('input');
  input.type     = 'file';
  input.accept   = '.json,application/json';
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;
    const text = await file.text();
    try {
      const count = await importConfig(text);
      setImportMessage(`${count} value${count !== 1 ? 's' : ''} imported.`);
      setTimeout(() => setImportMessage(null), 3000);
    } catch (e) {
      setImportMessage(`Import failed: ${String(e)}`);
    }
  };
  input.click();
}
```

---

## Acceptance criteria

- [ ] Every field shows a meaningful placeholder when not set
- [ ] `AgentConfigEntry` has optional `placeholder` field
- [ ] `agentConfigDefs.ts` has placeholder for all 11 entries
- [ ] `ConfigRow` uses placeholder from def, falls back to 'Not set'
- [ ] Export button downloads `agent-config.json` with current values
- [ ] Import button opens file picker, accepts JSON, overwrites silently
- [ ] "N values imported." confirmation shown for 3s after import
- [ ] Import parse error shown inline (not a crash)
- [ ] `agent_config_export` returns pretty-printed JSON string
- [ ] `agent_config_import` merges values, persists, returns count
- [ ] Both commands registered in `generate_handler![]`
- [ ] No TypeScript `any`
- [ ] `cargo build` exits 0, zero warnings
- [ ] `bun run build` exits 0, zero TypeScript errors

---

## Notes

**Import overwrites silently.** Count returned is total keys in imported file.

**Export uses browser download.** The `<a download>` trick works in Tauri's WebView.

**Import uses a hidden file input.** `document.createElement('input')` + `.click()`.

**`importConfig` refreshes state after import** via `agent_config_get_all`.

**3s import message timeout.** No need to track timeout ID for this use case.
