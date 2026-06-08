# rig/p4-tools: MCP Try panel

## Context

MCP tools in the Tools panel are currently read-only — description and
input schema only, no way to invoke them. This issue adds a Try section
to the MCP detail panel: a JSON textarea pre-populated from the tool's
input schema, a Run button, and a response output block.

All work is in `aetheris-agents/rig/`.

This issue lives in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

---

## What to build

### Rust — `tools_call_mcp` command

New command in `src-tauri/src/commands/tools.rs`.

Spawns the MCP server process, sends a `tools/call` JSON-RPC request,
reads the response, and returns the result. Synchronous — same pattern
as `tools_run_script`.

```rust
#[derive(Debug, Serialize)]
pub struct McpCallResult {
    pub content:  serde_json::Value,   // raw result from MCP response
    pub is_error: bool,                // true if MCP returned isError: true
}

#[tauri::command]
pub fn tools_call_mcp(
    state:       tauri::State<'_, crate::ToolsState>,
    server_id:   String,
    tool_name:   String,
    arguments:   serde_json::Value,    // parsed JSON from the textarea
) -> Result<McpCallResult, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    // Find the server config
    let servers = load_mcp_servers(agents_path);
    let server  = servers.iter()
        .find(|s| s.id == server_id)
        .ok_or_else(|| format!("server '{}' not found in mcp_servers.json", server_id))?;

    // Build the tools/call request
    let request = serde_json::json!({
        "jsonrpc": "2.0",
        "id":      1,
        "method":  "tools/call",
        "params":  {
            "name":      tool_name,
            "arguments": arguments,
        }
    });

    // Dispatch by transport
    let response_bytes = match server.transport.as_str() {
        "http"  => call_http_tool(server, &request)?,
        "stdio" => call_stdio_tool(server, agents_path, &request)?,
        other   => return Err(format!("unsupported transport: {}", other)),
    };

    // Parse response
    parse_tool_call_response(&response_bytes)
}
```

**`call_http_tool`** — same curl pattern as `discover_http_tools`:

```rust
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
            "--max-time", "30",   // tool calls may be slower than discovery
            &url,
        ])
        .output()
        .map_err(|e| format!("curl failed: {}", e))?;

    if !output.status.success() {
        return Err(format!("curl exited {}", output.status));
    }
    Ok(output.stdout)
}
```

**`call_stdio_tool`** — spawn, write request, read one response line:

```rust
fn call_stdio_tool(
    server:      &McpServerConfig,
    agents_path: &str,
    request:     &serde_json::Value,
) -> Result<Vec<u8>, String> {
    let command = server.command.as_ref()
        .ok_or("stdio server has no command")?;

    let cwd = server.cwd.as_deref()
        .map(|c| c.replace("${AETHERIS_AGENTS_PATH}", agents_path))
        .unwrap_or_else(|| agents_path.to_string());

    let mut msg = request.to_string();
    msg.push('\n');

    // Forward declared env vars (e.g. GITHUB_TOKEN)
    let mut cmd = std::process::Command::new(command);
    cmd.args(server.args.as_deref().unwrap_or(&[]))
        .current_dir(&cwd)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null());

    // Forward env map from server config if present
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

    if let Some(mut stdin) = child.stdin.take() {
        use std::io::Write;
        stdin.write_all(msg.as_bytes())
            .map_err(|e| format!("stdin write failed: {}", e))?;
    }

    let output = child.wait_with_output()
        .map_err(|e| format!("wait failed: {}", e))?;

    Ok(output.stdout)
}
```

**`parse_tool_call_response`**:

```rust
fn parse_tool_call_response(bytes: &[u8]) -> Result<McpCallResult, String> {
    let text = String::from_utf8_lossy(bytes);

    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.is_empty() { continue; }
        if let Ok(val) = serde_json::from_str::<serde_json::Value>(trimmed) {
            // Check for JSON-RPC error
            if val.get("error").is_some() {
                let msg = val.pointer("/error/message")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown error");
                return Err(format!("MCP error: {}", msg));
            }
            // Extract result
            if let Some(result) = val.get("result") {
                let is_error = result.get("isError")
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
                let content = result.get("content")
                    .cloned()
                    .unwrap_or(result.clone());
                return Ok(McpCallResult { content, is_error });
            }
        }
    }

    Err("no valid JSON-RPC response found".into())
}
```

**Note on `env` field in `McpServerConfig`:** Add `env` to the struct
and deserialise it. This also fixes the `discover_stdio_tools` gap
noted in p4-004:

```rust
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
    pub env:       Option<std::collections::HashMap<String, String>>,  // ← add this
}
```

Also apply the same env-forwarding logic to `discover_stdio_tools` so
tool discovery and tool calls are consistent.

**Registration** in `lib.rs` `generate_handler![]`:
```rust
commands::tools::tools_call_mcp,
```

---

### TypeScript — `src/hooks/types.ts`

```typescript
export interface McpCallResult {
  content:  unknown;   // raw MCP result content — JSON.stringify for display
  is_error: boolean;
}
```

Export from `src/hooks/index.ts`.

---

### Frontend — `McpDetail` in `ToolDetail.tsx`

Replace the current read-only `McpDetail` with one that includes a
Try section below the schema.

**Local state:**

```typescript
const [argsJson,    setArgsJson]    = useState<string>('');
const [calling,     setCalling]     = useState(false);
const [callResult,  setCallResult]  = useState<McpCallResult | null>(null);
const [callError,   setCallError]   = useState<string | null>(null);
```

**Pre-populate `argsJson` from `input_schema`** when the component
mounts (key the component on `tool.server_id + tool.name` to reset
on selection change):

```typescript
function buildArgsSkeleton(schema: Record<string, unknown> | null): string {
  if (!schema) return '{}';
  const props = (schema as { properties?: Record<string, unknown>;
                              required?:   string[] }).properties ?? {};
  const required = (schema as { required?: string[] }).required ?? [];
  const skeleton: Record<string, string> = {};
  for (const key of required) {
    if (key in props) skeleton[key] = '';
  }
  return JSON.stringify(skeleton, null, 2);
}

// In component body:
const [argsJson, setArgsJson] = useState(() => buildArgsSkeleton(tool.input_schema));
```

**Run handler:**

```typescript
async function handleRun() {
  setCalling(true);
  setCallResult(null);
  setCallError(null);
  try {
    const parsed = JSON.parse(argsJson);
    const res = await invoke<McpCallResult>('tools_call_mcp', {
      serverId:  tool.server_id,
      toolName:  tool.name,
      arguments: parsed,
    });
    setCallResult(res);
  } catch (e) {
    setCallError(String(e));
  } finally {
    setCalling(false);
  }
}
```

**Full `McpDetail` layout:**

```tsx
function McpDetail({ tool }: { tool: McpTool }) {
  const [schemaOpen,  setSchemaOpen]  = useState(false);
  const [argsJson,    setArgsJson]    = useState(() => buildArgsSkeleton(tool.input_schema));
  const [calling,     setCalling]     = useState(false);
  const [callResult,  setCallResult]  = useState<McpCallResult | null>(null);
  const [callError,   setCallError]   = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-4">

      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-lg font-semibold">{tool.name}</h2>
          <span className="text-xs text-muted-foreground/60">{tool.server_label}</span>
        </div>
        <p className="text-sm text-muted-foreground">{tool.description}</p>
      </div>

      {/* Auth warning */}
      {tool.auth !== 'none' && tool.auth !== 'env_token' && (
        <div className="flex items-center gap-2 rounded-md border border-amber-200
                        bg-amber-50 dark:bg-amber-950/20 px-3 py-2 text-sm
                        text-amber-800 dark:text-amber-300">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          Requires {tool.auth} authentication.
          {tool.notes && ` ${tool.notes}`}
        </div>
      )}

      {/* Input schema — collapsible */}
      {tool.input_schema && (
        <div className="flex flex-col gap-1">
          <button
            onClick={() => setSchemaOpen((o) => !o)}
            className="flex items-center gap-1 text-sm font-medium
                       text-muted-foreground hover:text-foreground"
          >
            {schemaOpen
              ? <ChevronDown  className="h-3.5 w-3.5" />
              : <ChevronRight className="h-3.5 w-3.5" />}
            Input schema
          </button>
          {schemaOpen && (
            <pre className="text-xs bg-muted rounded p-3 overflow-x-auto font-mono">
              {JSON.stringify(tool.input_schema, null, 2)}
            </pre>
          )}
        </div>
      )}

      {/* Divider */}
      <div className="border-t" />

      {/* Try section */}
      <div className="flex flex-col gap-3">
        <h3 className="text-sm font-medium">Try</h3>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">Arguments (JSON)</label>
          <textarea
            className="w-full rounded-md border border-input bg-background
                       px-3 py-2 text-sm font-mono placeholder:text-muted-foreground
                       focus-visible:outline-none focus-visible:ring-2
                       focus-visible:ring-ring resize-y min-h-[100px]"
            value={argsJson}
            onChange={(e) => setArgsJson(e.target.value)}
            spellCheck={false}
          />
        </div>

        <Button
          onClick={handleRun}
          disabled={calling}
        >
          {calling ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
          {calling ? 'Running…' : 'Run'}
        </Button>

        {callError && (
          <p className="text-sm text-red-600">{callError}</p>
        )}

        {callResult && (
          <div className="flex flex-col gap-2">
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full w-fit
              ${callResult.is_error
                ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
              }`}>
              {callResult.is_error ? 'error' : 'ok'}
            </span>
            <pre className="text-xs bg-muted rounded p-3 overflow-x-auto
                            whitespace-pre-wrap max-h-96 overflow-y-auto font-mono">
              {JSON.stringify(callResult.content, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Notes (non-auth) */}
      {tool.notes && (tool.auth === 'none' || tool.auth === 'env_token') && (
        <p className="text-xs text-muted-foreground border-l-2 pl-3 italic">
          {tool.notes}
        </p>
      )}
    </div>
  );
}
```

**Key the component** on `tool.server_id + tool.name` in `ToolDetail`:

```tsx
if (selected.kind === 'mcp') {
  return (
    <McpDetail
      key={`${selected.tool.server_id}/${selected.tool.name}`}
      tool={selected.tool}
    />
  );
}
```

---

## Auth warning change

The current warning triggers on `auth !== 'none'` which incorrectly
fires for `env_token` (token managed via Rig Settings — no user action
needed). Updated condition: only warn for `oauth2` and `api_key`:

```typescript
tool.auth !== 'none' && tool.auth !== 'env_token'
```

---

## Acceptance criteria

- [ ] `tools_call_mcp` command compiles, registered in `generate_handler![]`
- [ ] `env` field added to `McpServerConfig`, forwarded in both
      `call_stdio_tool` and `discover_stdio_tools`
- [ ] `McpCallResult` in `types.ts`, exported from `index.ts`
- [ ] `McpDetail` shows collapsible input schema (collapsed by default)
- [ ] Textarea pre-populated with required-fields skeleton on mount
- [ ] Textarea resets when a different tool is selected (key prop)
- [ ] Run button calls `tools_call_mcp` with camelCase invoke keys
      (`serverId`, `toolName`, `arguments`)
- [ ] Response shown as pretty-printed JSON with ok/error badge
- [ ] Auth warning suppressed for `env_token`
- [ ] `env_token` tools show notes in italic at the bottom
- [ ] No `<form>` tags, no TypeScript `any`
- [ ] `cargo build` exits 0 zero warnings
- [ ] `bun run build` exits 0 zero TypeScript errors

## Files to modify

- `src-tauri/src/commands/tools.rs` — add `env` to `McpServerConfig`;
  add `call_http_tool`, `call_stdio_tool`, `parse_tool_call_response`,
  `tools_call_mcp`; apply env forwarding to `discover_stdio_tools`
- `src-tauri/src/lib.rs` — register `tools_call_mcp`
- `src/hooks/types.ts` — add `McpCallResult`
- `src/hooks/index.ts` — export `McpCallResult`
- `src/components/modules/tools/ToolDetail.tsx` — replace `McpDetail`
  with Try-enabled version; add `buildArgsSkeleton`; key on
  `server_id/name`

## Notes

**`tools_call_mcp` is synchronous.** Tool calls may be slower than
discovery — 30s curl timeout for HTTP. For stdio, `wait_with_output`
has no timeout. If a tool hangs (e.g. waiting for auth), the UI will
be unresponsive. Acceptable for sanity testing; move to async if
it becomes a problem in practice.

**`arguments` is `serde_json::Value` on the Rust side.** Tauri
deserialises the frontend's parsed JSON object directly — no
double-serialisation needed. The frontend must `JSON.parse` the
textarea string before passing to invoke, and handle parse errors
(show as `callError`).

**`buildArgsSkeleton` only includes required fields.** Optional fields
are omitted to keep the skeleton minimal. Users can add them manually
if needed.

**Schema collapsed by default.** The pre-populated skeleton makes the
schema less critical to have open. Power users can expand it.

**`discover_stdio_tools` env fix is bundled here.** It was noted as
a known gap in p4-004. Fixing it in the same PR as `call_stdio_tool`
keeps the env-forwarding logic consistent and avoids a separate small
PR.
