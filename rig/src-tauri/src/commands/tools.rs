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

// ── MCP types ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct McpServerConfig {
    pub id:        String,
    pub label:     String,
    pub transport: String,
    pub url:       Option<String>,
    pub command:   Option<String>,
    pub args:      Option<Vec<String>>,
    pub cwd:       Option<String>,
    pub auth:      String,
    pub notes:     Option<String>,
    pub env:       Option<std::collections::HashMap<String, String>>,
}

#[derive(Debug, Deserialize)]
struct McpServersFile {
    #[allow(dead_code)]
    config_version: String,
    servers:        Vec<McpServerConfig>,
}

#[derive(Debug, Clone, Serialize)]
pub struct McpTool {
    pub server_id:    String,
    pub server_label: String,
    pub name:         String,
    pub description:  String,
    pub input_schema: Option<serde_json::Value>,
    pub auth:         String,
    pub notes:        Option<String>,
}

#[derive(Debug, Serialize)]
pub struct McpServerGroup {
    pub server_id:    String,
    pub server_label: String,
    pub auth:         String,
    pub notes:        Option<String>,
    pub tools:        Vec<McpTool>,
    pub reachable:    bool,
}

// ── MCP helper functions ──────────────────────────────────────────────────────

fn load_mcp_servers(agents_path: &str) -> Vec<McpServerConfig> {
    let path = std::path::Path::new(agents_path)
        .join("mcp")
        .join("mcp_servers.json");
    if !path.exists() { return vec![]; }
    let raw = std::fs::read_to_string(&path).unwrap_or_default();
    serde_json::from_str::<McpServersFile>(&raw)
        .map(|f| f.servers)
        .unwrap_or_default()
}

fn parse_tools_list_response(bytes: &[u8], server: &McpServerConfig) -> Vec<McpTool> {
    let text = String::from_utf8_lossy(bytes);
    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() { continue; }
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(trimmed) {
            if let Some(tools) = val.pointer("/result/tools").and_then(|v| v.as_array()) {
                return tools.iter().filter_map(|t| {
                    let name = t.get("name")?.as_str()?.to_string();
                    let description = t.get("description")
                        .and_then(|d| d.as_str())
                        .unwrap_or("(no description)")
                        .to_string();
                    Some(McpTool {
                        server_id:    server.id.clone(),
                        server_label: server.label.clone(),
                        name,
                        description,
                        input_schema: t.get("inputSchema").cloned(),
                        auth:         server.auth.clone(),
                        notes:        server.notes.clone(),
                    })
                }).collect();
            }
        }
    }
    vec![]
}

const MCP_INITIALIZE: &str = r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rig","version":"0.1.0"}}}"#;
const MCP_INITIALIZED: &str = r#"{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}"#;

fn resolve_env_template(template: &str, config: &std::collections::HashMap<String, String>) -> String {
    let mut out = template.to_string();
    loop {
        let start = match out.find("${") { Some(i) => i, None => break };
        let end   = match out[start..].find('}') { Some(i) => start + i, None => break };
        let var   = out[start + 2..end].to_string();
        let val   = config.get(&var)
            .cloned()
            .or_else(|| std::env::var(&var).ok())
            .unwrap_or_default();
        out = format!("{}{}{}", &out[..start], val, &out[end + 1..]);
    }
    out
}

// Fixed id for the actual request within a session; avoids collision with
// the initialize response (id=1) when the caller also uses id=1.
const MCP_SESSION_REQUEST_ID: u64 = 99;

fn run_stdio_session(
    server:      &McpServerConfig,
    agents_path: &str,
    request:     &serde_json::Value,
    config:      &std::collections::HashMap<String, String>,
) -> Result<Vec<u8>, String> {
    use std::io::{BufRead, BufReader, Write};
    use std::sync::mpsc;

    let command = server.command.as_ref()
        .ok_or("stdio server has no command")?;

    let cwd = server.cwd.as_deref()
        .map(|c| c.replace("${AETHERIS_AGENTS_PATH}", agents_path))
        .unwrap_or_else(|| agents_path.to_string());

    let mut cmd = std::process::Command::new(command);
    cmd.args(server.args.as_deref().unwrap_or(&[]))
        .current_dir(&cwd)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null());

    if let Some(env_map) = &server.env {
        for (k, v) in env_map {
            cmd.env(k, resolve_env_template(v, config));
        }
    }

    let mut child = cmd.spawn()
        .map_err(|e| format!("spawn failed: {}", e))?;

    let stdout = child.stdout.take()
        .ok_or("no stdout")?;

    // Reader thread sends lines to main thread via channel
    let (tx, rx) = mpsc::channel::<String>();
    let reader = std::thread::spawn(move || {
        for line in BufReader::new(stdout).lines() {
            if let Ok(l) = line {
                let trimmed = l.trim().to_string();
                if !trimmed.is_empty() {
                    if tx.send(trimmed).is_err() { break; }
                }
            }
        }
    });

    // Rewrite the request id so it never collides with the initialize response (id=1)
    let mut actual_request = request.clone();
    actual_request["id"] = serde_json::json!(MCP_SESSION_REQUEST_ID);

    let output = {
        let mut stdin = child.stdin.take().ok_or("no stdin")?;
        writeln!(stdin, "{}", MCP_INITIALIZE)
            .map_err(|e| format!("stdin write failed: {}", e))?;
        writeln!(stdin, "{}", MCP_INITIALIZED)
            .map_err(|e| format!("stdin write failed: {}", e))?;
        writeln!(stdin, "{}", actual_request)
            .map_err(|e| format!("stdin write failed: {}", e))?;

        // Collect lines until we see the response to our request, then let
        // stdin drop (closing EOF). This avoids a fixed sleep and handles
        // servers (like github-mcp-server) that make network calls before
        // responding (token scope fetch, tool enumeration, etc.).
        let deadline = std::time::Instant::now()
            + std::time::Duration::from_secs(15);
        let mut lines: Vec<String> = Vec::new();

        loop {
            let remaining = deadline.saturating_duration_since(std::time::Instant::now());
            if remaining.is_zero() { break; }
            match rx.recv_timeout(remaining) {
                Ok(line) => {
                    let is_response = serde_json::from_str::<serde_json::Value>(&line)
                        .ok()
                        .and_then(|v| v.get("id").and_then(|i| i.as_u64()))
                        .map(|id| id == MCP_SESSION_REQUEST_ID)
                        .unwrap_or(false);
                    lines.push(line);
                    if is_response { break; }
                }
                Err(_) => break,
            }
        }

        lines.join("\n").into_bytes()
        // stdin drops here → EOF to server
    };

    reader.join().ok();
    let _ = child.wait();
    Ok(output)
}

fn discover_http_tools(server: &McpServerConfig) -> Vec<McpTool> {
    let url = match &server.url {
        Some(u) => format!("{}/mcp", u.trim_end_matches('/')),
        None    => return vec![],
    };
    let body = serde_json::json!({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/list", "params": {}
    });
    let output = std::process::Command::new("curl")
        .args([
            "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", &body.to_string(),
            "--max-time", "5",
            &url,
        ])
        .output();
    match output {
        Ok(o) if o.status.success() => parse_tools_list_response(&o.stdout, server),
        _ => vec![],
    }
}

fn discover_stdio_tools(
    server:      &McpServerConfig,
    agents_path: &str,
    config:      &std::collections::HashMap<String, String>,
) -> Vec<McpTool> {
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id":      2,
        "method":  "tools/list",
        "params":  {}
    });

    match run_stdio_session(server, agents_path, &request, config) {
        Ok(bytes) => parse_tools_list_response(&bytes, server),
        Err(_)    => vec![],
    }
}

// ── MCP tool call helpers ─────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct McpCallResult {
    pub content:  serde_json::Value,
    pub is_error: bool,
}

fn call_http_tool(
    server:  &McpServerConfig,
    request: &serde_json::Value,
) -> Result<Vec<u8>, String> {
    let url = server.url.as_ref()
        .map(|u| format!("{}/mcp", u.trim_end_matches('/')))
        .ok_or("HTTP server has no url")?;

    let output = std::process::Command::new("curl")
        .args([
            "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", &request.to_string(),
            "--max-time", "30",
            &url,
        ])
        .output()
        .map_err(|e| format!("curl failed: {}", e))?;

    if !output.status.success() {
        return Err(format!("curl exited {}", output.status));
    }
    Ok(output.stdout)
}

fn call_stdio_tool(
    server:      &McpServerConfig,
    agents_path: &str,
    request:     &serde_json::Value,
    config:      &std::collections::HashMap<String, String>,
) -> Result<Vec<u8>, String> {
    run_stdio_session(server, agents_path, request, config)
}

fn parse_tool_call_response(bytes: &[u8]) -> Result<McpCallResult, String> {
    let text = String::from_utf8_lossy(bytes);

    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() { continue; }
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(trimmed) {
            if val.get("error").is_some() {
                let msg = val.pointer("/error/message")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown error");
                return Err(format!("MCP error: {}", msg));
            }
            if let Some(result) = val.get("result") {
                let is_error = result.get("isError")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                let content = result.get("content")
                    .cloned()
                    .unwrap_or_else(|| result.clone());
                return Ok(McpCallResult { content, is_error });
            }
        }
    }

    Err("no valid JSON-RPC response found".into())
}

// ── Inventory types ───────────────────────────────────────────────────────────

#[derive(Debug, Serialize)]
pub struct UseCaseGroup {
    pub use_case:    String,
    pub description: String,
    pub scripts:     Vec<ManifestScript>,
}

#[derive(Debug, Serialize)]
pub struct ToolsInventory {
    pub use_cases: Vec<UseCaseGroup>,
    pub harness:   Vec<HarnessTool>,
    pub mcp:       Vec<McpTool>,
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
    state:        tauri::State<'_, crate::ToolsState>,
    config_state: tauri::State<'_, crate::AgentConfigState>,
) -> Result<ToolsInventory, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;
    let config = config_state.cache.lock().unwrap().clone();

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

    let mcp_servers = load_mcp_servers(agents_path);
    let mcp: Vec<McpTool> = mcp_servers.iter()
        .flat_map(|s| match s.transport.as_str() {
            "http"  => discover_http_tools(s),
            "stdio" => discover_stdio_tools(s, agents_path, &config),
            _       => vec![],
        })
        .collect();

    Ok(ToolsInventory { use_cases, harness: harness_tools(), mcp })
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
pub fn tools_call_mcp(
    state:        tauri::State<'_, crate::ToolsState>,
    config_state: tauri::State<'_, crate::AgentConfigState>,
    server_id:    String,
    tool_name:    String,
    arguments:    serde_json::Value,
) -> Result<McpCallResult, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;
    let config = config_state.cache.lock().unwrap().clone();

    let servers = load_mcp_servers(agents_path);
    let server  = servers.iter()
        .find(|s| s.id == server_id)
        .ok_or_else(|| format!("server '{}' not found in mcp_servers.json", server_id))?;

    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id":      1,
        "method":  "tools/call",
        "params":  {
            "name":      tool_name,
            "arguments": arguments,
        }
    });

    let response_bytes = match server.transport.as_str() {
        "http"  => call_http_tool(server, &request)?,
        "stdio" => call_stdio_tool(server, agents_path, &request, &config)?,
        other   => return Err(format!("unsupported transport: {}", other)),
    };

    parse_tool_call_response(&response_bytes)
}

#[tauri::command]
pub fn tools_list_mcp(
    state:        tauri::State<'_, crate::ToolsState>,
    config_state: tauri::State<'_, crate::AgentConfigState>,
) -> Result<Vec<McpServerGroup>, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;
    let config = config_state.cache.lock().unwrap().clone();

    let servers = load_mcp_servers(agents_path);

    Ok(servers.iter().map(|s| {
        let tools = match s.transport.as_str() {
            "http"  => discover_http_tools(s),
            "stdio" => discover_stdio_tools(s, agents_path, &config),
            _       => vec![],
        };
        let reachable = !tools.is_empty();
        McpServerGroup {
            server_id:    s.id.clone(),
            server_label: s.label.clone(),
            auth:         s.auth.clone(),
            notes:        s.notes.clone(),
            tools,
            reachable,
        }
    }).collect())
}
