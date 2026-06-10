# Phase 7 — Agent Config Settings

**Status: IMPLEMENTED** — 5 commands delivered (spec said 3); includes
`agent_config_export` + `agent_config_import` beyond original scope.

**Goal:** Let users configure the env vars that Rig-launched agents need —
API keys, SMTP credentials, paths — through the settings panel. Values
persist across sessions and are automatically injected when the Orchestrator
spawns a child process.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Agent config settings](p7-001-agent-config.md) | — | tauri-plugin-store, AgentConfigState, settings panel Agent Config tab, env injection in orchestrate_start |

Single issue — all pieces are tightly coupled (store → state → commands →
UI → orchestrate injection).

---

## Completion gate

- Settings panel has two tabs: Watched Folders (unchanged) and Agent Config
- Agent Config tab shows ~10 known variables grouped by category
- Values persist across Rig restarts via tauri-plugin-store
- Credential fields (API keys, passwords) are masked by default with show/hide toggle
- Path and preference fields are plain text
- Each row has a clear button
- A banner notes that values are stored in plaintext on disk
- When the Orchestrator spawns a child process, all configured values are
  injected as env vars automatically
- Manually set env vars in the shell still take precedence (child process
  env var behaviour — explicit `.env()` calls on Command override inherited
  env only for that key; shell-set vars are inherited for unconfigured keys)
- `cargo build` exits 0, zero warnings
- `bun run build` exits 0, zero TypeScript errors

---

## Key decisions

**`tauri-plugin-store` not keychain.** Values are stored in a JSON file in
the app data directory — plaintext. The UI notes this. For a local dev tool
this is acceptable. OS keychain integration (`tauri-plugin-keychain`) is a
future upgrade.

**Known variable list is hardcoded in the frontend.** The UI shows a curated
list of known variables with labels and groupings. It is not a generic env
var editor. Unknown variables can't be added through the UI — they must be
set in the shell. This keeps the UI focused and avoids scope creep.

**Store values injected at spawn time.** `orchestrate_start` reads all
configured values from the store immediately before spawning the child
process. Shell env vars are inherited for any key not explicitly set via
`.env()`.

**Settings panel tab extension.** The existing settings route already has
a Watched Folders tab. The Agent Config tab is added as a second tab using
the same `MainArea` controlled-tab pattern established in p1.
