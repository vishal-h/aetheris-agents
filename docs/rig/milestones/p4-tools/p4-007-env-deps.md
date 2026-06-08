# rig/p4-tools: Dynamic env deps from manifests

## Context

`agentConfigDefs.ts` is a static declaration file — the Settings UI only
shows keys explicitly listed there. As new scripts and MCP tools are added,
their env var dependencies must be manually added to `agentConfigDefs.ts`.

This issue makes env deps declarative: scripts declare what env vars they
need in `tools.json`, the inventory walker collects them, and the Settings
UI merges them with the static definitions automatically. No code change
needed when adding a new script with new credentials.

All work is in `aetheris-agents/rig/` plus the `tools.json` manifests.

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

---

## Schema addition — `env` field per script in `tools.json`

Add an optional `env` array to each script entry. Each element declares
one env var the script depends on:

```json
{
  "name": "ping_ct",
  "file": "gateway/scripts/ping_ct.py",
  "description": "Check connectivity to the ct-api",
  "args": [],
  "env": [
    {
      "key":         "CT_API_BASE_URL",
      "label":       "API base URL",
      "group":       "ct",
      "masked":      false,
      "placeholder": "https://api.ct.example.com"
    },
    {
      "key":         "CT_JWT_TOKEN",
      "label":       "JWT token",
      "group":       "ct",
      "masked":      true,
      "placeholder": "eyJ..."
    },
    {
      "key":         "CT_ACCESS_CODE",
      "label":       "Access code",
      "group":       "ct",
      "masked":      true,
      "placeholder": ""
    }
  ],
  "output": "json",
  "example": "python3 gateway/scripts/ping_ct.py"
}
```

**`env` field reference:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `key` | string | Yes | Env var name — e.g. `CT_API_BASE_URL` |
| `label` | string | Yes | Display label in Settings UI |
| `group` | string | Yes | Section header in Settings UI — e.g. `"ct"` |
| `masked` | boolean | Yes | `true` = password field with show/hide toggle |
| `placeholder` | string | Yes | Hint shown when not set. `""` = no hint |

**Deduplication rule:** if the same `key` appears in multiple scripts
(e.g. `CT_API_BASE_URL` in both `ping_ct` and `validate_intent`), only
one entry appears in Settings. First declaration wins for `label`,
`group`, `masked`, `placeholder`. Subsequent declarations with the same
`key` are silently skipped.

**`env` is optional.** Scripts with no env deps omit the field entirely.
The manifest remains backward-compatible — existing `tools.json` files
without `env` fields parse correctly.

---

## Manifests to update

Update `api/tools.json` — add `env` arrays to scripts that need `ct`
credentials. All gateway scripts that call the ct-api share the same
set. Tenant scripts that don't make API calls need no `env` field.

Scripts that need ct env deps:
- `ping_ct` — `CT_API_BASE_URL`
- `validate_intent` — `CT_API_BASE_URL`
- `resolve_context` — `CT_API_BASE_URL`
- `direct_call` — `CT_API_BASE_URL`, `CT_JWT_TOKEN`, `CT_ACCESS_CODE`
- `lookup_existing` — `CT_API_BASE_URL`, `CT_JWT_TOKEN`
- `build_etl_job` — `CT_API_BASE_URL`
- `upload_etl_to_s3` — `CT_S3_BUCKET`, `CT_AWS_ACCESS_KEY_ID`, `CT_AWS_SECRET_ACCESS_KEY`
- `submit_to_rmq` — `CT_RMQ_HOST`, `CT_RMQ_USER`, `CT_RMQ_PASSWORD`, `CT_RMQ_VHOST`
- `notify_at1qry` — `CT_AETHERIS_RESUME_URL` (or similar — read the script to confirm)

> **Instruction to Claude Code:** read each gateway script before writing
> its `env` array. Use the exact env var names from `os.environ.get()`
> or `os.getenv()` calls in the script. Do not guess or invent names.

Scripts that do NOT need `env` (no ct-api calls):
- `parse_csv` — pure data transformation
- `package_intent` — pure data transformation
- `extract_skill_hints` — reads a local file
- `gap_analysis` — pure data analysis
- `stub_cot1` — generates mock data locally

---

## Rust — `src-tauri/src/commands/tools.rs`

### New type

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnvDep {
    pub key:         String,
    pub label:       String,
    pub group:       String,
    pub masked:      bool,
    pub placeholder: String,
}
```

### Add to `ManifestScript`

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestScript {
    pub name:        String,
    pub file:        String,
    pub description: String,
    pub args:        Vec<ManifestArg>,
    pub output:      String,
    pub example:     String,
    #[serde(default)]
    pub undeclared:  bool,
    #[serde(default)]
    pub env:         Vec<EnvDep>,   // ← add this
}
```

### Add to `ToolsInventory`

```rust
#[derive(Debug, Serialize)]
pub struct ToolsInventory {
    pub use_cases: Vec<UseCaseGroup>,
    pub harness:   Vec<HarnessTool>,
    pub mcp:       Vec<McpTool>,
    pub env_deps:  Vec<EnvDep>,     // ← add this — deduplicated across all scripts
}
```

### Collect env deps in `tools_list_inventory`

After building `use_cases`, collect and deduplicate env deps:

```rust
let mut env_deps: Vec<EnvDep> = vec![];
let mut seen_keys: std::collections::HashSet<String> = std::collections::HashSet::new();

for group in &use_cases {
    for script in &group.scripts {
        for dep in &script.env {
            if seen_keys.insert(dep.key.clone()) {
                env_deps.push(dep.clone());
            }
        }
    }
}

Ok(ToolsInventory { use_cases, harness: harness_tools(), mcp, env_deps })
```

---

## TypeScript — `src/hooks/types.ts`

```typescript
export interface EnvDep {
  key:         string;
  label:       string;
  group:       string;
  masked:      boolean;
  placeholder: string;
}
```

Add `env_deps` to `ToolsInventory`:

```typescript
export interface ToolsInventory {
  use_cases: UseCaseGroup[];
  harness:   HarnessTool[];
  mcp:       McpTool[];
  env_deps:  EnvDep[];
}
```

Add `env` to `ManifestScript`:

```typescript
export interface ManifestScript {
  name:        string;
  file:        string;
  description: string;
  args:        ManifestArg[];
  output:      'json' | 'text' | 'files';
  example:     string;
  undeclared?: boolean;
  env?:        EnvDep[];
}
```

Export `EnvDep` from `src/hooks/index.ts`.

---

## Frontend — Settings tab

The Settings tab currently renders only `AGENT_CONFIG_DEFS` (static).
Extend it to also render env deps collected from the inventory.

### `useAgentConfig.ts` — no changes needed

The hook already exposes `values` (all stored config), `set`, and
`remove`. Env deps from the inventory are just additional keys to
render — the storage and persistence layer is identical.

### `AgentConfigTab.tsx` — merge static + dynamic

```typescript
// Fetch inventory to get env_deps
const { inventory } = useTools();

// Merge: static defs first, then dynamic deps not already in static list
const staticKeys = new Set(AGENT_CONFIG_DEFS.map((d) => d.key));
const dynamicDefs = (inventory?.env_deps ?? []).filter(
  (d) => !staticKeys.has(d.key)
);
const allDefs = [...AGENT_CONFIG_DEFS, ...dynamicDefs];
```

Then render `allDefs` instead of `AGENT_CONFIG_DEFS`. Existing groups
(Harness, Anthropic, SMTP, Google Drive, Provenance, GitHub) are
unaffected — they come from the static list. New groups (e.g. `ct`)
appear automatically when scripts declare them.

**`useTools` is already available** — `AgentConfigTab` can import
`useTools` directly. No prop drilling needed.

**Loading state:** if `inventory` is still null (loading), render only
the static defs. Dynamic deps appear once the inventory loads — no
skeleton needed, the static rows are already visible.

---

## Script detail panel — env dep hints

When a script is selected and it has an `env` array, show a small
hint section above the arg form listing which env vars it needs and
whether they are currently set:

```tsx
{script.env && script.env.length > 0 && (
  <div className="flex flex-col gap-1 mb-4">
    <h3 className="text-sm font-medium">Required config</h3>
    {script.env.map((dep) => {
      const isSet = Boolean(values[dep.key]);
      return (
        <div key={dep.key}
             className="flex items-center gap-2 text-xs">
          <span className={`h-1.5 w-1.5 rounded-full shrink-0
            ${isSet ? 'bg-green-500' : 'bg-amber-400'}`}
          />
          <code className="font-mono">{dep.key}</code>
          <span className="text-muted-foreground">
            {isSet ? 'set' : 'not set — add in Settings'}
          </span>
        </div>
      );
    })}
  </div>
)}
```

This requires `values` from `useAgentConfig` in `ScriptDetailPanel`.
Import `useAgentConfig` directly in `ToolDetail.tsx`.

---

## Acceptance criteria

- [ ] `env` field added to `ManifestScript` in `tools.rs` and `types.ts`
      with `#[serde(default)]` / optional so existing manifests parse
- [ ] `EnvDep` type in `tools.rs` and `types.ts`, exported from `index.ts`
- [ ] `ToolsInventory.env_deps` populated and deduplicated by key
- [ ] `api/tools.json` gateway scripts updated with correct `env` arrays
      (exact var names read from scripts — not guessed)
- [ ] Settings tab renders dynamic groups from `env_deps` alongside
      static `AGENT_CONFIG_DEFS`
- [ ] `ct` group appears in Settings automatically with all ct vars
- [ ] Script detail panel shows "Required config" section with
      green/amber indicators for each declared env dep
- [ ] No TypeScript `any`
- [ ] No `<form>` tags
- [ ] `cargo build` exits 0 zero warnings
- [ ] `bun run build` exits 0 zero TypeScript errors

## Files to create/modify

- `aetheris-agents/api/tools.json` — add `env` arrays to gateway scripts
- `src-tauri/src/commands/tools.rs` — add `EnvDep`, update
  `ManifestScript`, update `ToolsInventory`, collect in
  `tools_list_inventory`
- `src/hooks/types.ts` — add `EnvDep`, update `ManifestScript` and
  `ToolsInventory`
- `src/hooks/index.ts` — export `EnvDep`
- `src/components/modules/settings/AgentConfigTab.tsx` — merge static
  + dynamic defs
- `src/components/modules/tools/ToolDetail.tsx` — add env dep hints
  to `ScriptDetailPanel`

## Notes

**Static defs take precedence over dynamic.** If `CT_API_BASE_URL` is
later added to `AGENT_CONFIG_DEFS` (e.g. to change its group or label),
the static entry wins and the dynamic one is filtered out. This prevents
duplicates and lets static declarations override manifest declarations.

**`useTools` in `AgentConfigTab` — no circular dependency.** `useTools`
calls `tools_list_inventory`; `AgentConfigTab` uses `useAgentConfig` for
values and `useTools` for the dep list. No circular hook calls.

**Env dep hints are informational only.** The Run button is not disabled
when deps are unset — the script may still work (e.g. if the var is set
in the shell environment). The amber indicator is a nudge, not a block.

**`inventory` may be null on first render.** `dynamicDefs` falls back to
`[]` when `inventory` is null — `allDefs` is just the static list until
the inventory loads. No flash, no skeleton needed.
