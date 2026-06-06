use serde::{Deserialize, Serialize};
use std::collections::HashSet;

// ── Manifest types (mirror tools.json schema) ─────────────────────────────────

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

// ── Harness tools (static list) ───────────────────────────────────────────────

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

// ── Inventory types ───────────────────────────────────────────────────────────

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
    pub mcp:       Vec<McpToolStub>,
}

// ── ScriptResult ──────────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct ScriptResult {
    pub stdout:    String,
    pub stderr:    String,
    pub exit_code: i32,
}

// ── Commands ──────────────────────────────────────────────────────────────────

#[tauri::command]
pub fn tools_list_inventory(
    state: tauri::State<'_, crate::ToolsState>,
) -> Result<ToolsInventory, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    let base = std::path::Path::new(agents_path);
    let mut use_cases: Vec<UseCaseGroup> = vec![];

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

        if use_case_name.starts_with('.') || use_case_name == "rig"
            || use_case_name == "docs" || use_case_name == "agents"
        {
            continue;
        }

        let manifest_path = dir.join("tools.json");
        let scripts_dir   = dir.join("scripts");

        let mut manifest: Option<ToolsManifest> = None;
        if manifest_path.exists() {
            if let Ok(raw) = std::fs::read_to_string(&manifest_path) {
                manifest = serde_json::from_str(&raw).ok();
            }
        }

        let declared_files: HashSet<String> = manifest
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

        if scripts_dir.exists() {
            if let Ok(dir_entries) = std::fs::read_dir(&scripts_dir) {
                let mut py_files: Vec<_> = dir_entries
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
        }

        if manifest_path.exists() || scripts_dir.exists() {
            use_cases.push(UseCaseGroup { use_case: use_case_name, description, scripts });
        }
    }

    Ok(ToolsInventory {
        use_cases,
        harness: harness_tools(),
        mcp:     vec![],
    })
}

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

#[tauri::command]
pub fn tools_run_script(
    state:    tauri::State<'_, crate::ToolsState>,
    use_case: String,
    file:     String,
    args:     Vec<String>,
) -> Result<ScriptResult, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    let use_case_dir  = std::path::Path::new(agents_path).join(&use_case);
    let script_path   = use_case_dir.join(&file);

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

#[tauri::command]
pub fn tools_list_mcp(
    _state: tauri::State<'_, crate::ToolsState>,
) -> Result<Vec<McpToolStub>, String> {
    Ok(vec![])
}
