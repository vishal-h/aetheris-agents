# rig/p4-tools: Rust backend

## Context

With manifests in place, this issue implements the Tauri backend for the
Tools module: walking the agents path to build an inventory, and running
scripts with full harness context.

All work is in `aetheris-agents/rig/`.

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

---

## What to build

### State struct (add to `src-tauri/src/lib.rs`)

```rust
pub struct ToolsState {
    pub agents_path: Option<String>,
}
```

Setup in `lib.rs` inside `.setup(|app| { ... })` — `agents_path` is
already read for `OrchestratorState`; reuse the same value:

```rust
app.manage(ToolsState {
    agents_path: std::env::var("AETHERIS_AGENTS_PATH").ok(),
});
```

No separate job map needed — script runs are synchronous (see
`tools_run_script` below).

---

### Data types (add to `src-tauri/src/commands/tools.rs`)

Mirror the `tools.json` schema exactly.

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestArg {
    pub name:        String,
    pub flag:        Option<String>,
    #[serde(rename = "type")]
    pub arg_type:    String,
    pub required:    bool,
    pub default:     Option<String>,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ManifestScript {
    pub name:        String,
    pub file:        String,
    pub description: String,
    pub args:        Vec<ManifestArg>,
    pub output:      String,   // "json" | "text" | "files"
    pub example:     String,
    #[serde(default)]
    pub undeclared:  bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolsManifest {
    pub manifest_version: String,
    pub use_case:         String,
    pub description:      String,
    pub scripts:          Vec<ManifestScript>,
}
```

These are also the shapes returned to the frontend — Tauri serialises
them directly.

---

### Harness tools (static list, hardcoded)

```rust
#[derive(Debug, Clone, Serialize)]
pub struct HarnessToolArg {
    pub name:        String,
    pub arg_type:    String,
    pub required:    bool,
    pub description: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct HarnessTool {
    pub name:        String,
    pub description: String,
    pub args:        Vec<HarnessToolArg>,
    pub notes:       Option<String>,
}

fn harness_tools() -> Vec<HarnessTool> {
    vec![
        HarnessTool {
            name: "run_command".into(),
            description: "Run a shell command. stdout is captured and returned as the tool result.".into(),
            args: vec![
                HarnessToolArg { name: "command".into(), arg_type: "string".into(),  required: true,  description: "Shell command to execute".into() },
                HarnessToolArg { name: "cwd".into(),     arg_type: "string".into(),  required: false, description: "Working directory (default: agent sandbox_path)".into() },
            ],
            notes: Some("stdout is the contract. Errors go to stderr. Exit code 0 = success, 1 = recoverable error.".into()),
        },
        HarnessTool {
            name: "read_file".into(),
            description: "Read a file and return its contents as a string.".into(),
            args: vec![
                HarnessToolArg { name: "path".into(), arg_type: "string".into(), required: true, description: "Absolute or sandbox-relative path".into() },
            ],
            notes: None,
        },
        HarnessTool {
            name: "write_file".into(),
            description: "Write a string to a file, creating directories as needed.".into(),
            args: vec![
                HarnessToolArg { name: "path".into(),    arg_type: "string".into(), required: true, description: "Absolute or sandbox-relative path".into() },
                HarnessToolArg { name: "content".into(), arg_type: "string".into(), required: true, description: "Content to write".into() },
            ],
            notes: None,
        },
        HarnessTool {
            name: "ask_human".into(),
            description: "Pause the run and surface a question to the operator. Blocks until answered.".into(),
            args: vec![
                HarnessToolArg { name: "question".into(), arg_type: "string".into(), required: true, description: "The question to ask".into() },
            ],
            notes: Some("Used for confirmation gates. The Orchestrator UI surfaces these via the approval flow.".into()),
        },
        HarnessTool {
            name: "write_blackboard".into(),
            description: "Write a value to the shared orb blackboard.".into(),
            args: vec![
                HarnessToolArg { name: "key".into(),   arg_type: "string".into(), required: true, description: "Blackboard key".into() },
                HarnessToolArg { name: "value".into(), arg_type: "string".into(), required: true, description: "Value to write (typically JSON string)".into() },
            ],
            notes: Some("Orb agents only. Keys are scoped to the orb.".into()),
        },
        HarnessTool {
            name: "read_blackboard".into(),
            description: "Read a value from the shared orb blackboard.".into(),
            args: vec![
                HarnessToolArg { name: "key".into(), arg_type: "string".into(), required: true, description: "Blackboard key to read".into() },
            ],
            notes: Some("Orb agents only.".into()),
        },
        HarnessTool {
            name: "send_message".into(),
            description: "Send a message to another agent in the same orb.".into(),
            args: vec![
                HarnessToolArg { name: "to".into(),      arg_type: "string".into(), required: true, description: "Target run_id".into() },
                HarnessToolArg { name: "message".into(), arg_type: "string".into(), required: true, description: "Message content".into() },
            ],
            notes: Some("Orb agents only. Receiver uses wait_for_event to consume.".into()),
        },
        HarnessTool {
            name: "wait_for_event".into(),
            description: "Block until a specific event condition is met.".into(),
            args: vec![
                HarnessToolArg { name: "condition".into(),  arg_type: "string".into(),  required: true,  description: "Event condition atom (e.g. message_received)".into() },
                HarnessToolArg { name: "timeout_ms".into(), arg_type: "integer".into(), required: false, description: "Timeout in milliseconds (default: 60000)".into() },
            ],
            notes: Some("Use timeout_ms: 120000 for cross-agent waits.".into()),
        },
    ]
}
```

---

### `src-tauri/src/commands/tools.rs` — four commands

---

**`tools_list_inventory`**

Walks `AETHERIS_AGENTS_PATH`, reads every `tools.json`, synthesises
entries for undeclared scripts, appends harness tools.

```rust
#[derive(Debug, Serialize)]
pub struct UseCaseGroup {
    pub use_case:    String,
    pub description: String,
    pub scripts:     Vec<ManifestScript>,
}

#[derive(Debug, Serialize)]
pub struct McpToolStub {
    pub server:      String,
    pub name:        String,
    pub description: String,
}

#[derive(Debug, Serialize)]
pub struct ToolsInventory {
    pub use_cases: Vec<UseCaseGroup>,
    pub harness:   Vec<HarnessTool>,
    pub mcp:       Vec<McpToolStub>,   // empty until p4-004
}

#[tauri::command]
pub fn tools_list_inventory(
    state: tauri::State<'_, crate::ToolsState>,
) -> Result<ToolsInventory, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    let base = std::path::Path::new(agents_path);
    let mut use_cases: Vec<UseCaseGroup> = vec![];

    // Walk top-level directories in agents_path
    let mut entries: Vec<_> = std::fs::read_dir(base)
        .map_err(|e| format!("read_dir failed: {}", e))?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_dir())
        .collect();
    entries.sort_by_key(|e| e.file_name());

    for entry in entries {
        let dir = entry.path();
        let use_case_name = dir.file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .to_string();

        // Skip hidden dirs, rig/ itself, docs/, agents/ top-level
        if use_case_name.starts_with('.') || use_case_name == "rig"
            || use_case_name == "docs" || use_case_name == "agents" {
            continue;
        }

        let manifest_path = dir.join("tools.json");
        let scripts_dir   = dir.join("scripts");

        // Load manifest if present
        let mut manifest: Option<ToolsManifest> = None;
        if manifest_path.exists() {
            let raw = std::fs::read_to_string(&manifest_path)
                .map_err(|e| format!("read {} failed: {}", manifest_path.display(), e))?;
            manifest = serde_json::from_str(&raw).ok();
        }

        // Collect declared script filenames
        let declared_files: std::collections::HashSet<String> = manifest
            .as_ref()
            .map(|m| m.scripts.iter().map(|s| s.file.clone()).collect())
            .unwrap_or_default();

        let mut scripts: Vec<ManifestScript> = manifest
            .as_ref()
            .map(|m| m.scripts.clone())
            .unwrap_or_default();

        let description = manifest
            .as_ref()
            .map(|m| m.description.clone())
            .unwrap_or_else(|| format!("{} (no manifest)", use_case_name));

        // Synthesise entries for undeclared scripts
        if scripts_dir.exists() {
            let mut py_files: Vec<_> = std::fs::read_dir(&scripts_dir)
                .unwrap_or_else(|_| std::fs::read_dir(".").unwrap())
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path().extension()
                        .map(|x| x == "py")
                        .unwrap_or(false)
                })
                .collect();
            py_files.sort_by_key(|e| e.file_name());

            for f in py_files {
                let rel = format!("scripts/{}", f.file_name().to_string_lossy());
                if !declared_files.contains(&rel) {
                    let stem = f.path()
                        .file_stem()
                        .unwrap_or_default()
                        .to_string_lossy()
                        .to_string();
                    scripts.push(ManifestScript {
                        name:        stem.clone(),
                        file:        rel.clone(),
                        description: "(not declared in tools.json)".into(),
                        args:        vec![],
                        output:      "text".into(),
                        example:     format!("python3 {}", rel),
                        undeclared:  true,
                    });
                }
            }
        }

        // Only include use case if it has a scripts dir or a manifest
        if manifest_path.exists() || scripts_dir.exists() {
            use_cases.push(UseCaseGroup { use_case: use_case_name, description, scripts });
        }
    }

    Ok(ToolsInventory {
        use_cases,
        harness: harness_tools(),
        mcp:     vec![],   // p4-004
    })
}
```

---

**`tools_read_script`**

Returns the raw source of a script file. Path traversal guard included.

```rust
#[tauri::command]
pub fn tools_read_script(
    state:    tauri::State<'_, crate::ToolsState>,
    use_case: String,
    file:     String,
) -> Result<String, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    let path = std::path::Path::new(agents_path)
        .join(&use_case)
        .join(&file);

    let canonical = path.canonicalize()
        .map_err(|e| format!("path error: {}", e))?;
    let base = std::path::Path::new(agents_path)
        .canonicalize()
        .map_err(|e| format!("base path error: {}", e))?;
    if !canonical.starts_with(&base) {
        return Err("path traversal rejected".into());
    }

    std::fs::read_to_string(&canonical)
        .map_err(|e| format!("read failed: {}", e))
}
```

---

**`tools_run_script`**

Runs a script with `cwd` = use-case root, inheriting Rig's env. Waits
for completion and returns stdout, stderr, and exit code.

```rust
#[derive(Debug, Serialize)]
pub struct ScriptResult {
    pub stdout:    String,
    pub stderr:    String,
    pub exit_code: i32,
}

#[tauri::command]
pub fn tools_run_script(
    state:    tauri::State<'_, crate::ToolsState>,
    use_case: String,
    file:     String,
    args:     Vec<String>,   // fully-assembled CLI args from the frontend
) -> Result<ScriptResult, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    let use_case_dir = std::path::Path::new(agents_path).join(&use_case);
    let script_path  = use_case_dir.join(&file);

    // Path traversal guard
    let canonical_script = script_path.canonicalize()
        .map_err(|e| format!("script path error: {}", e))?;
    let canonical_base = use_case_dir.canonicalize()
        .map_err(|e| format!("base path error: {}", e))?;
    if !canonical_script.starts_with(&canonical_base) {
        return Err("path traversal rejected".into());
    }

    let output = std::process::Command::new("python3")
        .arg(&canonical_script)
        .args(&args)
        .current_dir(&use_case_dir)
        .output()
        .map_err(|e| format!("spawn failed: {}", e))?;

    Ok(ScriptResult {
        stdout:    String::from_utf8_lossy(&output.stdout).to_string(),
        stderr:    String::from_utf8_lossy(&output.stderr).to_string(),
        exit_code: output.status.code().unwrap_or(-1),
    })
}
```

> **Note:** `tools_run_script` is synchronous — it blocks the Tauri
> command thread until the script exits. Fine for sub-10s scripts. If a
> script is long-running, move to the async streaming pattern from
> `orchestrate_start` in a follow-up.

---

**`tools_list_mcp`**

Stub for p4-004. Returns empty vec now.

```rust
#[tauri::command]
pub fn tools_list_mcp(
    _state: tauri::State<'_, crate::ToolsState>,
) -> Result<Vec<McpToolStub>, String> {
    Ok(vec![])
}
```

---

### Registration

In `commands/mod.rs`:
```rust
pub mod tools;
```

In `lib.rs` `generate_handler![]`:
```rust
commands::tools::tools_list_inventory,
commands::tools::tools_read_script,
commands::tools::tools_run_script,
commands::tools::tools_list_mcp,
```

---

### TypeScript additions (`src/hooks/types.ts`)

```typescript
// Tools inventory
export interface ManifestArg {
  name:        string;
  flag?:       string;
  arg_type:    string;
  required:    boolean;
  default:     string | null;
  description: string;
}

export interface ManifestScript {
  name:        string;
  file:        string;
  description: string;
  args:        ManifestArg[];
  output:      'json' | 'text' | 'files';
  example:     string;
  undeclared?: boolean;
}

export interface UseCaseGroup {
  use_case:    string;
  description: string;
  scripts:     ManifestScript[];
}

export interface HarnessToolArg {
  name:        string;
  arg_type:    string;
  required:    boolean;
  description: string;
}

export interface HarnessTool {
  name:        string;
  description: string;
  args:        HarnessToolArg[];
  notes:       string | null;
}

export interface McpToolStub {
  server:      string;
  name:        string;
  description: string;
}

export interface ToolsInventory {
  use_cases: UseCaseGroup[];
  harness:   HarnessTool[];
  mcp:       McpToolStub[];
}

export interface ScriptResult {
  stdout:    string;
  stderr:    string;
  exit_code: number;
}

export type SelectedTool =
  | { kind: 'script';  use_case: string; script: ManifestScript }
  | { kind: 'harness'; tool: HarnessTool }
  | { kind: 'mcp';     tool: McpToolStub };
```

Export all new types from `src/hooks/index.ts`.

---

## Acceptance criteria

- [ ] `ToolsState` in `lib.rs`, managed in setup
- [ ] `tools_list_inventory` walks `AETHERIS_AGENTS_PATH`, merges
      manifest + filesystem, returns grouped inventory
- [ ] Undeclared scripts synthesised with `undeclared: true`
- [ ] Harness tools static list returned verbatim
- [ ] `tools_read_script` returns script source; rejects path traversal
- [ ] `tools_run_script` runs with correct `cwd` and inherited env;
      returns stdout, stderr, exit_code
- [ ] `tools_list_mcp` returns `[]` (stub)
- [ ] TypeScript types in `types.ts`, exported from `index.ts`
- [ ] `cargo build` clean, zero warnings

## Files to create/modify

- `src-tauri/src/commands/tools.rs` (new)
- `src-tauri/src/commands/mod.rs` (add `pub mod tools`)
- `src-tauri/src/lib.rs` (add `ToolsState`, manage in setup, register commands)
- `src/hooks/types.ts` (add types)
- `src/hooks/index.ts` (export new types)
