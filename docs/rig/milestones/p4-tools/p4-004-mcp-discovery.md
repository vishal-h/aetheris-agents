# rig/p4-tools: MCP discovery

## Context

With the Tools UI in place, this issue fills in the MCP section: querying
connected MCP servers for their tool manifests and surfacing them in the
inventory alongside scripts and harness tools.

All work is in `aetheris-agents/rig/`.

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

This issue is non-blocking — the MCP section renders as empty until this
is merged. Implement after p4-003 is stable.

---

## Current MCP landscape

```
aetheris/mcp/
  http/
    google-drive/          — HTTP MCP server (OAuth 2.0)
  stdio/
    node/                  — stdio MCP server (Node.js stub)
```

Two transport types. Discovery strategy differs per type.

---

## MCP server config

MCP servers are not auto-discovered from the filesystem — they must be
declared so Rig knows transport type, URL/command, and auth requirements.

Add `aetheris-agents/mcp/mcp_servers.json`:

```json
{
  "config_version": "1",
  "servers": [
    {
      "id": "google-drive",
      "label": "Google Drive",
      "transport": "http",
      "url": "http://localhost:3000",
      "auth": "oauth2",
      "notes": "Requires OAuth token. Run mcp/http/google-drive/get_token.py first."
    },
    {
      "id": "node-stdio",
      "label": "Node stdio stub",
      "transport": "stdio",
      "command": "node",
      "args": ["mcp/stdio/node/index.js"],
      "cwd": "${AETHERIS_AGENTS_PATH}",
      "auth": "none",
      "notes": "Stub server for development."
    }
  ]
}
```

**Field reference:**

| Field | Type | Notes |
|-------|------|-------|
| `config_version` | `"1"` | Integer string. Same versioning convention as `manifest_version`. |
| `id` | string | Snake_case unique identifier. |
| `label` | string | Display name in the MCP section header. |
| `transport` | `"http"` \| `"stdio"` | Determines discovery strategy. |
| `url` | string | HTTP only — base URL of the MCP server. |
| `command` | string | stdio only — executable to spawn. |
| `args` | string[] | stdio only — args to the command. |
| `cwd` | string | stdio only — working dir; `${AETHERIS_AGENTS_PATH}` is interpolated. |
| `auth` | `"none"` \| `"oauth2"` \| `"api_key"` | For display/warning only in p4. No auth flows implemented. |
| `notes` | string | Shown in the MCP tool detail panel. |

---

## MCP protocol — tools/list

Both transports use the same MCP JSON-RPC request:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {} }
```

Response shape:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "tool_name",
        "description": "What this tool does",
        "inputSchema": {
          "type": "object",
          "properties": {
            "param1": { "type": "string", "description": "..." }
          },
          "required": ["param1"]
        }
      }
    ]
  }
}
```

---

## What to build

### Extend types in `src-tauri/src/commands/tools.rs`

Replace `McpToolStub` with full types:

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
}

#[derive(Debug, Deserialize)]
struct McpServersFile {
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
```

Update `ToolsInventory` — replace `Vec<McpToolStub>` with `Vec<McpTool>`.

### Helper functions

```rust
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

fn discover_stdio_tools(server: &McpServerConfig, agents_path: &str) -> Vec<McpTool> {
    let command = match &server.command {
        Some(c) => c,
        None    => return vec![],
    };
    let cwd = server.cwd.as_deref()
        .map(|c| c.replace("${AETHERIS_AGENTS_PATH}", agents_path))
        .unwrap_or_else(|| agents_path.to_string());

    let body = {
        let mut s = serde_json::json!({
            "jsonrpc": "2.0", "id": 1,
            "method": "tools/list", "params": {}
        }).to_string();
        s.push('\n');
        s
    };

    let mut child = match std::process::Command::new(command)
        .args(server.args.as_deref().unwrap_or(&[]))
        .current_dir(&cwd)
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null())
        .spawn()
    {
        Ok(c)  => c,
        Err(_) => return vec![],
    };

    if let Some(mut stdin) = child.stdin.take() {
        use std::io::Write;
        let _ = stdin.write_all(body.as_bytes());
    }

    match child.wait_with_output() {
        Ok(o)  => parse_tools_list_response(&o.stdout, server),
        Err(_) => vec![],
    }
}
```

> **Why curl for HTTP?** Adding `reqwest` or `ureq` for a single
> one-time inventory call adds significant compile weight. `curl` is
> available on all target platforms (macOS, Linux) and sufficient here.
> Revisit if auth flows or polling require more.

### Updated `tools_list_inventory`

Replace `mcp: vec![]` with:

```rust
let mcp_servers = load_mcp_servers(agents_path);
let mcp: Vec<McpTool> = mcp_servers.iter()
    .flat_map(|s| match s.transport.as_str() {
        "http"  => discover_http_tools(s),
        "stdio" => discover_stdio_tools(s, agents_path),
        _       => vec![],
    })
    .collect();

Ok(ToolsInventory { use_cases, harness: harness_tools(), mcp })
```

### Updated `tools_list_mcp`

Returns per-server groups with a `reachable` flag:

```rust
#[tauri::command]
pub fn tools_list_mcp(
    state: tauri::State<'_, crate::ToolsState>,
) -> Result<Vec<McpServerGroup>, String> {
    let agents_path = state.agents_path.as_ref()
        .ok_or("AETHERIS_AGENTS_PATH not set")?;

    let servers = load_mcp_servers(agents_path);

    Ok(servers.iter().map(|s| {
        let tools = match s.transport.as_str() {
            "http"  => discover_http_tools(s),
            "stdio" => discover_stdio_tools(s, agents_path),
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
```

### TypeScript updates (`src/hooks/types.ts`)

Replace `McpToolStub` with:

```typescript
export interface McpTool {
  server_id:    string;
  server_label: string;
  name:         string;
  description:  string;
  input_schema: Record<string, unknown> | null;
  auth:         string;
  notes:        string | null;
}

export interface McpServerGroup {
  server_id:    string;
  server_label: string;
  auth:         string;
  notes:        string | null;
  tools:        McpTool[];
  reachable:    boolean;
}
```

Update `ToolsInventory.mcp` type from `McpToolStub[]` to `McpTool[]`.

Update `SelectedTool`:
```typescript
export type SelectedTool =
  | { kind: 'script';  use_case: string; script: ManifestScript }
  | { kind: 'harness'; tool: HarnessTool }
  | { kind: 'mcp';     tool: McpTool };
```

### UI updates

**`ToolTree.tsx`** — group MCP tools by server:

```tsx
{inventory.mcp.length > 0 && (
  <div className="mt-3">
    <span className="text-xs font-semibold uppercase tracking-wide
                     text-muted-foreground block mb-1">MCP</span>
    {Object.entries(
      inventory.mcp.reduce<Record<string, McpTool[]>>((acc, t) => {
        (acc[t.server_id] ??= []).push(t);
        return acc;
      }, {})
    ).map(([serverId, tools]) => (
      <div key={serverId} className="mb-1">
        <span className="text-xs text-muted-foreground/60 px-2 block">
          {tools[0].server_label}
        </span>
        {tools.map((tool) => (
          <button
            key={tool.name}
            onClick={() => selectMcp(tool)}
            className={`text-left px-2 py-1 rounded text-sm w-full
              ${selected?.kind === 'mcp' && selected.tool.name === tool.name
                && selected.tool.server_id === tool.server_id
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
              }`}
          >
            {tool.name}
          </button>
        ))}
      </div>
    ))}
  </div>
)}
```

Add `selectMcp` to `useTools`:
```typescript
const selectMcp = useCallback((tool: McpTool) => {
  setSelected({ kind: 'mcp', tool });
  setResult(null);
  setRunError(null);
}, []);
```

**`ToolDetail.tsx`** — MCP tool detail (read-only, no Run button):

```tsx
// selected.kind === 'mcp'
<div className="flex flex-col gap-4">
  <div>
    <div className="flex items-center gap-2 mb-1">
      <h2 className="text-lg font-semibold">{tool.name}</h2>
      <span className="text-xs text-muted-foreground/60">
        {tool.server_label}
      </span>
    </div>
    <p className="text-sm text-muted-foreground">{tool.description}</p>
  </div>

  {tool.auth !== 'none' && (
    <div className="flex items-center gap-2 rounded-md border border-amber-200
                    bg-amber-50 dark:bg-amber-950/20 px-3 py-2 text-sm
                    text-amber-800 dark:text-amber-300">
      <AlertTriangle className="h-4 w-4 shrink-0" />
      Requires {tool.auth} authentication.
      {tool.notes && ` ${tool.notes}`}
    </div>
  )}

  {tool.input_schema && (
    <div className="flex flex-col gap-1">
      <h3 className="text-sm font-medium">Input schema</h3>
      <pre className="text-xs bg-muted rounded p-3 overflow-x-auto font-mono">
        {JSON.stringify(tool.input_schema, null, 2)}
      </pre>
    </div>
  )}

  {tool.notes && tool.auth === 'none' && (
    <p className="text-xs text-muted-foreground border-l-2 pl-3 italic">
      {tool.notes}
    </p>
  )}
</div>
```

---

## Acceptance criteria

- [ ] `aetheris-agents/mcp/mcp_servers.json` written with google-drive
      and node-stdio entries
- [ ] `tools_list_inventory` populates `mcp` field from live server queries
- [ ] Unreachable servers produce empty tool list, no crash
- [ ] `tools_list_mcp` returns per-server groups with `reachable` flag
- [ ] MCP tools visible in left-panel tree, grouped by server
- [ ] Selecting an MCP tool shows read-only detail with input schema
- [ ] Auth warning shown when `auth !== 'none'`
- [ ] `cargo build` clean, zero warnings
- [ ] `bun run build` exits 0

## Files to create/modify

- `aetheris-agents/mcp/mcp_servers.json` (new)
- `src-tauri/src/commands/tools.rs` (extend: MCP types + discovery)
- `src/hooks/types.ts` (replace McpToolStub, add McpServerGroup)
- `src/hooks/useTools.ts` (add selectMcp)
- `src/components/modules/tools/ToolTree.tsx` (MCP grouping by server)
- `src/components/modules/tools/ToolDetail.tsx` (MCP detail panel)

## Notes

**Discovery runs at inventory fetch time** — both HTTP and stdio
discovery happen synchronously inside `tools_list_inventory`. A slow or
unreachable server delays the whole inventory call by up to the curl
5s timeout. If this is noticeable, move MCP discovery to a lazy separate
call that the UI triggers after the main inventory loads.

**No auth flow in p4.** OAuth2 servers (google-drive) will return 401
unless the user has already run `get_token.py`. The `reachable: false`
path handles this — the server appears in the tree with a "not reachable"
indicator. Auth flows are out of scope for p4.

**stdio server EOF behaviour.** The discovery spawns the process, sends
one request, and closes stdin. Servers that exit on EOF work correctly.
Servers that stay alive after EOF will cause `wait_with_output` to hang —
if this happens with the node stub, add a read timeout via a thread.
