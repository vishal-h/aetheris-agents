# Claude Code prompt — P7

## p7-001 (run from aetheris-agents/rig/)

```
Read docs/rig/milestones/p7/p7-001-agent-config.md and implement agent
config settings.

Files to create:
- src-tauri/src/commands/agent_config.rs — 3 commands + persist helper
- src/hooks/useAgentConfig.ts
- src/components/modules/settings/agentConfigDefs.ts — 9 known variables
- src/components/modules/settings/AgentConfigTab.tsx
- src/components/modules/settings/SettingsRoute.tsx

Files to modify:
- src-tauri/Cargo.toml — see note below about tauri-plugin-store
- src-tauri/src/lib.rs — AgentConfigState, cache load on startup,
  register 3 commands
- src-tauri/src/commands/mod.rs — pub mod agent_config;
- src-tauri/src/commands/orchestrate.rs — add AgentConfigState param,
  inject env vars before spawn
- src/hooks/types.ts — add AgentConfigEntry
- src/hooks/index.ts — export useAgentConfig and AgentConfigEntry
- src/App.tsx — replace WatchedFoldersSettings in settings route with
  SettingsRoute

Constraints:
- Read the note in the spec about tauri-plugin-store: the manual JSON
  file approach (AgentConfigState with HashMap cache + serde_json) is
  preferred over the plugin. Only add tauri-plugin-store to Cargo.toml
  if there is a compelling reason — the manual approach has no new
  dependency.
- AgentConfigState cache is loaded from disk on startup if the file
  exists; empty HashMap if not
- orchestrate_start: add config_state: State<'_, AgentConfigState> as
  second parameter; inject all cache values as .env(key, value) calls
  before .spawn()
- ConfigRow manages its own draft state — saving one row does not
  affect others
- Save button only visible when draft is dirty AND non-empty
- Clear button only visible when a value is currently set
- Masked fields: type="password" by default, toggle to type="text"
  with Eye/EyeOff icons
- Check App.tsx for the current settings route — it may render
  WatchedFoldersSettings directly or via an existing wrapper; replace
  with SettingsRoute
- No TypeScript any
- When done: cargo build exits 0 zero warnings, bun run build exits 0
  zero TypeScript errors. Paste the diff.
```
