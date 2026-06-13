# Rig — Runbook

---

## Environment variables

| Variable | Required | Description |
|----------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | Absolute path to `aetheris/priv/aetheris.db` |
| `AETHERIS_AGENTS_PATH` | Yes (tools features) | Absolute path to `aetheris-agents/` root |
| `AETHERIS_PROVIDER` | No | Default LLM provider for agents (`anthropic`); not read by Rig itself |
| `AETHERIS_API_URL` | Yes (playground features) | Base URL of the running aetheris harness API (e.g. `http://localhost:4001`) |
| `AETHERIS_API_TOKEN` | Yes (playground features) | Bearer token — must match one entry in `AETHERIS_PLAYGROUND_TOKENS` on the harness side |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | Absolute path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | Set `true` to enable corpus-search MCP |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No (GitHub MCP) | PAT for GitHub MCP server — or set in Rig Settings |

---

## Development

```bash
cd aetheris-agents/rig

# Set env vars
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb      # optional
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...                             # optional, or set in Settings

# Start dev server
cargo tauri dev
```

All env vars except `AETHERIS_DB_PATH` are optional at startup —
Rig renders "not connected" placeholders for features that require them.

---

## Building

```bash
cd aetheris-agents/rig
cargo tauri build
```

Output binary: `src-tauri/target/release/bundle/`

---

## Running against the test sandbox

```bash
# Create/reset the test sandbox
python3 provenance/scripts/create_test_sandbox.py --overwrite

# Run the scan orchestrator to populate aetheris.db and corpus.duckdb
export PROVENANCE_NAS_PATH=~/sandbox/provenance-test/archive
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs

# Open Rig
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
cargo tauri dev
```

---

## Harness module — Run inspection

The Harness module shows all agent runs recorded in `aetheris.db`.

### What you see

**Run list tab:**
- Label, status badge, model, started at, duration, steps
- Click any row to open the event log for that run
- Refresh button — no auto-refresh

**Event log tab:**
- All events for the selected run, ordered by seq
- Step number, event type, timestamp, payload preview
- Colour coding by event type

### Status badges

| Status | Colour | Notes |
|--------|--------|-------|
| `done` | Green | |
| `running` | Amber | pulsing "Live" indicator while events are streaming |
| `running` + "stalled?" | Amber + amber text | no events for >5 min; process may have died |
| `failed` | Red | |
| `paused` | Blue | |
| `idle` | Grey | |

### Not connected

If `AETHERIS_DB_PATH` is not set or the file doesn't exist, the Harness
tab shows a "Not connected" placeholder with the path to set.

---

## Tools module — Script and MCP browser

The Tools module browses scripts, harness tools, and MCP tools.
Requires `AETHERIS_AGENTS_PATH` to be set.

### What you see

**Left panel — tree:**
- Use-case groups (collapsible) — scripts from `tools.json` manifests
- Undeclared scripts (amber `!`) — `.py` files not in `tools.json`
- Harness section — 8 built-in tools, read-only
- MCP section — per server, collapsible, only shown when servers respond

**Right panel — detail:**
- Scripts: description, arg form, example command (click to copy), Run button
- Harness tools: description + args, read-only
- MCP tools: description, collapsible input schema, Try panel

### Try panel (MCP tools)

- JSON textarea pre-populated with required fields skeleton
- Run invokes the tool via stdio/HTTP and shows the response
- `ok` / `error` badge + pretty-printed JSON response

### MCP section not appearing

The MCP section is hidden when all servers return empty tool lists.
Common causes:
1. `GITHUB_PERSONAL_ACCESS_TOKEN` not set — set in Rig Settings or export before launch
2. `github-mcp-server` not on PATH — install: `go install github.com/github/github-mcp-server@latest`
3. Token expired or insufficient scopes — needs `repo` scope

Test the binary directly:
```bash
(
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rig","version":"0.1.0"}}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  sleep 2
) | GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
    github-mcp-server stdio 2>/dev/null
```

Should return a JSON line with 43 tools.

### Adding a new MCP server

1. Add entry to `aetheris-agents/mcp/mcp_servers.json`
2. If auth needed, add key to `agentConfigDefs.ts` (Settings → new group)
3. Restart Rig — server appears in Tools panel automatically

### Adding a tools.json manifest

Place at `{use_case}/tools.json` in `aetheris-agents/`. See
`docs/rig/milestones/p4-tools/p4-001-manifest-spec.md` for full schema.
Minimum viable entry:

```json
{
  "manifest_version": "1",
  "use_case": "my_use_case",
  "description": "What this use case does",
  "scripts": []
}
```

Undeclared scripts (`.py` files without a manifest entry) appear with
an amber warning badge. Add them to `tools.json` to get structured
arg forms and output formatting.

---

## Agent config — Settings

Agent config is stored at:
```
~/.local/share/dev.rig.app/agent-config.json   # Linux
~/Library/Application Support/dev.rig.app/agent-config.json  # macOS
```

Values are injected as env vars when the Orchestrator spawns agents.
To add a new config key: add one line to `agentConfigDefs.ts` — the
row appears automatically in Settings. See `agent-config-reference.md`
for full documentation.

Current groups: Harness, Anthropic, SMTP, Google Drive, Payslip, GitHub.

---

## Provenance module

See `docs/provenance/runbook.md` for full Provenance documentation.

Quick reference:
- Corpus overview: `PROVENANCE_DB_PATH` must be set
- Classification review: approve/reject proposed classifications
- Migration status: progress by client
- Zip inventory: processed/encrypted/pending counts

---

## Playground module — Run Composer

The Playground module lets Rig users submit agent runs to a running aetheris
harness API without needing repo access or a local Elixir environment.

### Enabling the harness API

Set in aetheris `config/runtime.exs`:

```elixir
config :aetheris, api_enabled: true
config :aetheris, api_port: 4001
config :aetheris, api_bind: {127, 0, 0, 1}   # default: localhost only
```

`api_bind` defaults to localhost. Binding all interfaces (`{0, 0, 0, 0}`) is an
explicit opt-in; see Trust model section below.

### Generating a token

Add to aetheris config:

```elixir
config :aetheris, :playground_tokens, ["your-token-here"]
```

Or via env: `AETHERIS_PLAYGROUND_TOKENS=your-token-here` (comma-separated for
multiple). Set `AETHERIS_API_TOKEN` in Rig's env to the same value.

### Matching env var example

```bash
# Harness side
AETHERIS_PLAYGROUND_TOKENS=tok-abc ./scripts/run_server.sh

# Rig side
AETHERIS_API_URL=http://localhost:4001
AETHERIS_API_TOKEN=tok-abc
cargo tauri dev
```

### Exposing beyond localhost (reverse proxy)

Change `api_bind: {0, 0, 0, 0}` or a specific IP for VPN/private interface.
Note: once `api_bind` is opened, `GET /api/runs/*` endpoints leak run labels and
timing — operators on shared networks may wish to front them with proxy auth.

### Trust model — `run_command` and secrets

- `run_command` is not in the default playground allowlist. Enabling it grants
  shell-equivalent access to all bearer token holders — they can execute arbitrary
  commands with the harness process's UID.
- If `run_command` is enabled, or if `openrouter` is in the provider allowlist, the
  harness startup environment must not contain `ANTHROPIC_API_KEY`,
  `OPENROUTER_API_KEY`, or other secrets accessible to playground token holders.
  Use a dedicated harness process with a scoped environment.
- Playground tokens that enable `run_command` are equivalent to SSH keys — issue
  only to fully-trusted team members and rotate on personnel changes.

### Reverse proxy note

Behind a reverse proxy, `conn.remote_ip` in auth-rejection logs is the proxy's
address, not the client's. `X-Forwarded-For` must not be naively trusted without
explicit trusted-proxy configuration (deferred to p3).

### Overlay retention

Per-run overlay upper directories are not automatically cleaned up (tracked: issue
#84). Retention and cleanup tooling is planned for p3.

### Overlay isolation is Linux-only

The overlay mechanism uses `libc::mount` + user namespaces. On non-Linux hosts the
worker fails open and writes reach the real sandbox path. Production deployments
should run on Linux.

---

## Common issues

### Harness tab shows "Not connected"

**Fix:** Set `AETHERIS_DB_PATH` to the absolute path of `aetheris.db` and
restart:
```bash
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
```

### Run list is empty

`aetheris.db` exists but has no runs — no agents have been run yet.
Run any agent via `mix aetheris run` and refresh.

### Events table shows no events for a run

The run was recorded but the harness may have crashed before persisting
events. Check `mix aetheris inspect <run_id>` for details.

### Tools panel shows no use cases

`AETHERIS_AGENTS_PATH` is not set. Set it and restart:
```bash
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
```

### Run list shows "stalled?" next to a running badge

A run is flagged "stalled?" when `status = 'running'` in the DB but no events
have arrived for more than 5 minutes. This means the `mix` process likely died
mid-run and the harness did not get a chance to update the status.

**Verify:** `mix aetheris inspect <run_id>` — if the last event is old and no
new events arrive, the process is dead.

**The harness does not automatically mark these runs as failed.** Rig detects
the condition display-only; no DB write occurs. The status in `aetheris.db`
remains `running` permanently unless the harness is restarted and a cleanup
sweep runs (no such sweep currently exists in the harness).

**Distinguish from paused runs:** a run in `wait_for_event` state is paused
legitimately — it will also show no new events, but `mix aetheris inspect`
will show a `agent_waiting` event as the latest. Treat these differently.

### Trajectory tab shows "read failed" or blank for a completed run

The trajectory file is written atomically at run completion. If the run
finished too recently (< 1s) or the harness crashed mid-write, the file
may be absent or truncated.

**Check:** `ls -la ~/sandbox/elixirws/aetheris/priv/runs/<run_id>/` — the
file should be `trajectory.json`, not `trajectory.json.tmp`.

**If `.tmp` exists**, the write was interrupted. The `.tmp` file is partial
and cannot be recovered — the run data is still in `aetheris.db` (Events tab).

**If the file exists** but Rig reports a read error, check
`AETHERIS_DB_PATH` — `trajectory.rs` derives the run directory from it;
a wrong path will produce a misleading error.

### MCP Try panel returns initialize response instead of tool result

This was a bug fixed in p4-006. If seen again, check that
`parse_tool_call_response` filters by `id == MCP_SESSION_REQUEST_ID` (99).

### cargo tauri dev fails to compile

Ensure Rust toolchain is up to date:
```bash
rustup update
```

Check that `rusqlite` feature flags in `Cargo.toml` include `bundled`:
```toml
rusqlite = { version = "...", features = ["bundled"] }
```

---

## Adding a new module

1. Create `src/components/modules/{name}/` with component files
2. Add hook to `src/hooks/use{Name}.ts`
3. Add Tauri commands to `src-tauri/src/commands/{name}.rs`
4. Register commands in `src-tauri/src/lib.rs`
5. Add route to `src/App.tsx`
6. Add module entry to `src/modules/registry.ts`
7. Add TypeScript interfaces to `src/hooks/types.ts`
8. Export from `src/hooks/index.ts`

Follow the pattern established in `commands/tools.rs` and
`components/modules/tools/`.
