# Phase 4 — Tools Explorer

**Status: IMPLEMENTED** — MCP Try panel included (beyond original scope).

**Goal:** Browse every script, harness tool, and MCP tool available in the
Aetheris ecosystem. Inspect signatures. Run scripts with custom args directly
from Rig and see live output.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Manifest spec](p4-001-manifest-spec.md) | — | `tools.json` schema + write manifests for all existing use cases |
| 002 | [Rust backend](p4-002-rust-backend.md) | 001 | Inventory walker + script runner: 4 Tauri commands |
| 003 | [Tools UI](p4-003-tools-ui.md) | 002 | Two-panel view: tree + detail/run panel |
| 004 | [MCP discovery](p4-004-mcp-discovery.md) | 002 | HTTP + stdio MCP tool enumeration |
| 005 | [MCP Try panel](p4-005-mcp-try-panel.md) | 004 | JSON textarea + Run button + response output for MCP tools |
| 006 | [MCP stdio handshake](p4-006-mcp-stdio-handshake.md) | 005 | MCP initialize handshake + reader thread fix for stdio transport |

001 is pure JSON/docs — can be done immediately.
002 and 003 are the core delivery; 004 is additive and non-blocking.

---

## Completion gate

- Tools module appears in sidebar (Wrench icon, after Orchestrator)
- Left panel shows use cases grouped, harness tools section, MCP section
- Selecting a tool loads its detail in the right panel
- Scripts: arg form renders from manifest; Run executes with correct cwd/env
- Output streams live into the output area; exit code shown on finish
- Undeclared scripts (in `scripts/` but not in manifest) appear with a
  warning badge — nudge to write the manifest entry
- Harness tools: description + schema rendered, no Run button
- MCP tools: description + schema rendered (p4-004); no Run button in p4
- `bun run build` exits 0, zero TypeScript errors

---

## Key decisions

**Manifest-first, filesystem-fallback.** The inventory walker reads
`tools.json` from each use-case root first. Scripts present in `scripts/`
but absent from the manifest still appear — marked `undeclared: true` — so
nothing is invisible but the nudge to write the manifest is always there.

**`manifest_version`** at the file level (integer string `"1"`). Per-tool
versioning is not needed — arg schema changes are self-documenting. MCP
tools carry their own version from the server manifest.

**Full harness context for script execution.** `cwd` = use-case root,
env inherits from Rig's process (so `AETHERIS_DB_PATH`, `AETHERIS_AGENTS_PATH`
etc. are all available). Same model as `orchestrate_start` — spawn, stream
stdout, report exit code.

**No stdin for script runner.** Scripts in `scripts/` are one-shot: they
take args and produce output. If a script needs interactive input it's the
wrong tool — use the Orchestrator for that. The runner has no stdin pipe.

**MCP in p4-004, non-blocking.** The inventory data model has a slot for
MCP tools from the start, but discovery is implemented separately. The UI
renders MCP tools identically to harness tools if they're present.

**Harness tools are static.** They don't change between runs. They are
hardcoded in the backend (as a `Vec<HarnessTool>` returned by a helper)
and rendered read-only — no Run button.

See `p4-001-manifest-spec.md` for the full `tools.json` schema.

---

## Known issues

**MCP discovery blocks inventory load (p4-004).** `tools_list_inventory`
runs HTTP and stdio discovery synchronously. An unreachable server (e.g.
`google-drive` before OAuth is configured) will cause curl to hit its
5-second timeout before the inventory returns — the Tools tab appears
frozen for up to 5s per unreachable server on first load.

Quick fix when this becomes annoying: make MCP discovery lazy. Fetch
inventory without MCP first, then fire `tools_list_mcp` in a `useEffect`
after the main inventory resolves and merge the results in.

**`discover_stdio_tools` does not forward `env` from `mcp_servers.json`.**
Tokens (e.g. `GITHUB_TOKEN`) must be present in Rig's process environment
at launch — exported in the shell before `cargo tauri dev`. Follow-up:
read the `env` map in `discover_stdio_tools` and pass each entry via
`.env(key, value)` on the `Command`, so Rig can manage tokens entirely
through Settings without requiring a shell export.

---

## Directory

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```
