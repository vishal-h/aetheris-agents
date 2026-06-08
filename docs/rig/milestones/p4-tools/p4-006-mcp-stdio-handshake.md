# rig/p4-tools: MCP stdio handshake fix

## Context

The GitHub MCP server (and likely all compliant MCP servers) requires a
handshake before accepting any method calls. The current `discover_stdio_tools`
and `call_stdio_tool` send the request immediately, causing the server to
reject it with `method invalid during initialization` and exit.

Additionally, `wait_with_output` closes stdin before reading stdout, so
the server receives EOF before it can write its response.

This issue fixes both problems for all stdio MCP servers.

All work is in `aetheris-agents/rig/src-tauri/src/commands/tools.rs`.

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

---

## Root cause

### Problem 1 — Missing handshake

MCP protocol requires this sequence before any method call:

```
client → initialize request
server ← initialize response
client → notifications/initialized (no response expected)
client → actual request (tools/list, tools/call etc.)
server ← actual response
```

Current code sends only the actual request. Server rejects it.

### Problem 2 — stdin closes before response is read

`wait_with_output()` internally drops stdin (sending EOF) and then
waits for the process to exit before returning stdout. The server
interprets EOF as session end and exits before writing the response.

The fix: take stdout into a reader thread *before* closing stdin.
Write all messages to stdin, then drop stdin explicitly to signal
session end, then join the reader thread to get the response.

---

## What to build

### Shared handshake helper

Extract a single `run_stdio_session` function used by both
`discover_stdio_tools` and `call_stdio_tool`. It handles:
1. Spawn the process
2. Forward env vars
3. Send initialize + initialized + actual request
4. Read response lines in a reader thread
5. Drop stdin to signal EOF
6. Join reader thread
7. Return collected stdout bytes

```rust
use std::io::{BufRead, Write};
use std::sync::{Arc, Mutex};

const MCP_INITIALIZE: &str = r#"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rig","version":"0.1.0"}}}"#;
const MCP_INITIALIZED: &str = r#"{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}"#;

/// Runs a full MCP stdio session: handshake + one request.
/// Returns all stdout lines collected before EOF.
fn run_stdio_session(
    server:      &McpServerConfig,
    agents_path: &str,
    request:     &serde_json::Value,
) -> Result<Vec<u8>, String> {
    let command = server.command.as_ref()
        .ok_or("stdio server has no command")?;

    let cwd = server.cwd.as_deref()
        .map(|c| c.replace("${AETHERIS_AGENTS_PATH}", agents_path))
        .unwrap_or_else(|| agents_path.to_string());

    // Build command
    let mut cmd = std::process::Command::new(command);
    cmd.args(server.args.as_deref().unwrap_or(&[]))
        .current_dir(&cwd)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null());

    // Forward declared env vars
    if let Some(env_map) = &server.env {
        for (k, v) in env_map {
            let resolved = v.replace(
                &format!("${{{}}}", k),
                &std::env::var(k).unwrap_or_default(),
            );
            cmd.env(k, resolved);
        }
    }

    let mut child = cmd.spawn()
        .map_err(|e| format!("spawn failed: {}", e))?;

    // Take stdout before anything else — reader thread needs it
    let stdout = child.stdout.take()
        .ok_or("no stdout")?;

    // Spawn reader thread — collects all lines into a buffer
    let buffer: Arc<Mutex<Vec<String>>> = Arc::new(Mutex::new(vec![]));
    let buf_clone = buffer.clone();
    let reader = std::thread::spawn(move || {
        for line in std::io::BufReader::new(stdout).lines() {
            if let Ok(l) = line {
                let trimmed = l.trim().to_string();
                if !trimmed.is_empty() {
                    buf_clone.lock().unwrap().push(trimmed);
                }
            }
        }
    });

    // Write handshake + request to stdin
    if let Some(mut stdin) = child.stdin.take() {
        writeln!(stdin, "{}", MCP_INITIALIZE)
            .map_err(|e| format!("stdin write failed: {}", e))?;
        writeln!(stdin, "{}", MCP_INITIALIZED)
            .map_err(|e| format!("stdin write failed: {}", e))?;
        writeln!(stdin, "{}", request)
            .map_err(|e| format!("stdin write failed: {}", e))?;
        // stdin drops here — signals EOF to server
    }

    // Join reader thread (waits for server to finish writing + exit)
    reader.join().ok();

    // Also wait for process to exit cleanly
    let _ = child.wait();

    // Collect buffered lines as bytes
    let lines = buffer.lock().unwrap();
    let output = lines.join("\n").into_bytes();
    Ok(output)
}
```

### Updated `discover_stdio_tools`

Replace the current implementation body with a call to
`run_stdio_session`:

```rust
fn discover_stdio_tools(server: &McpServerConfig, agents_path: &str) -> Vec<McpTool> {
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id":      2,
        "method":  "tools/list",
        "params":  {}
    });

    match run_stdio_session(server, agents_path, &request) {
        Ok(bytes) => parse_tools_list_response(&bytes, server),
        Err(_)    => vec![],
    }
}
```

### Updated `call_stdio_tool`

Replace the current implementation body with a call to
`run_stdio_session`:

```rust
fn call_stdio_tool(
    server:      &McpServerConfig,
    agents_path: &str,
    request:     &serde_json::Value,
) -> Result<Vec<u8>, String> {
    run_stdio_session(server, agents_path, request)
}
```

Note: `call_stdio_tool` uses id `1` in its request (already set by
`tools_call_mcp`). `run_stdio_session` uses id `1` for `initialize`.
This means both use id `1` — acceptable since they are different
sessions and ids only need to be unique within a session. No change
needed.

### `parse_tools_list_response` — id filter

The response buffer will now contain multiple JSON lines including the
`initialize` response. Update `parse_tools_list_response` to skip lines
that don't match `tools/list` result shape — i.e. only process lines
where `/result/tools` exists:

```rust
fn parse_tools_list_response(bytes: &[u8], server: &McpServerConfig) -> Vec<McpTool> {
    let text = String::from_utf8_lossy(bytes);
    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() { continue; }
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(trimmed) {
            // Only process lines that have result.tools array
            if let Some(tools) = val.pointer("/result/tools")
                .and_then(|v| v.as_array())
            {
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
```

This is the same logic as before — `val.pointer("/result/tools")` only
matches the `tools/list` response, not the `initialize` response which
has `result.capabilities`. No extra filtering needed.

### `parse_tool_call_response` — unchanged

The existing implementation already skips lines without `/result` or
`/error`, so the `initialize` response line is ignored automatically.
No change needed.

---

## Acceptance criteria

- [ ] `run_stdio_session` sends initialize → initialized → request
      in that order, all to the same stdin
- [ ] Reader thread started before stdin is written to — no race
- [ ] stdin dropped after all writes (explicit EOF signal)
- [ ] `discover_stdio_tools` uses `run_stdio_session` — old
      implementation removed
- [ ] `call_stdio_tool` uses `run_stdio_session` — old
      implementation removed
- [ ] `parse_tools_list_response` unchanged in behaviour —
      still skips non-tools/list lines correctly
- [ ] Manual test passes:
      GitHub MCP section appears in Tools panel with 12 tools
- [ ] `cargo build` exits 0 zero warnings

## Files to modify

- `src-tauri/src/commands/tools.rs` only — no frontend changes,
  no lib.rs changes, no TypeScript changes

## Notes

**Reader thread before stdin write — order matters.** The reader thread
must be spawned before writing to stdin. If the server writes a large
initialize response before we start reading, it could block on a full
pipe buffer. Spawning the reader first prevents this.

**No sleep needed.** The `sleep` in the manual test was keeping stdin
open, not pacing messages. With the reader thread approach, stdin stays
open until explicitly dropped — no sleeps required.

**id collision between initialize and actual request.** `run_stdio_session`
uses id `1` for `initialize`. `tools_call_mcp` also uses id `1` for its
request. This is fine — JSON-RPC ids are session-scoped, and each
`run_stdio_session` call is a fresh session. Discovery uses id `2` for
`tools/list` to avoid any ambiguity within a single session.

**`call_stdio_tool` becomes a thin wrapper.** Its only job is to call
`run_stdio_session` and propagate the error. The session logic is not
duplicated.

**stderr suppressed.** The server writes log lines to stderr (the
`time=... level=INFO` lines seen in manual testing). These don't affect
stdout parsing. Keep `Stdio::null()` for stderr.

**HTTP transport unchanged.** `call_http_tool` and `discover_http_tools`
are not affected — no handshake required for HTTP MCP.
