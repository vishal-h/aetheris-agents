# rig/p7-003: Agent config export improvements

## Context

Three small improvements to the Agent Config export:
1. Export all known keys (not just set ones), with placeholder as hint value for unset keys
2. Keys sorted alphabetically
3. Export button debounced for 2s to prevent rapid re-clicks

All changes are in the frontend only — no Rust changes needed.

---

## Changes

### `src/hooks/useAgentConfig.ts`

Replace `exportConfig` with a frontend-driven version:

```typescript
import { AGENT_CONFIG_DEFS } from '@/components/modules/settings/agentConfigDefs';

const exportConfig = useCallback(async (): Promise<string> => {
  const allKeys: Record<string, string> = {};
  for (const def of AGENT_CONFIG_DEFS) {
    allKeys[def.key] = values[def.key] ?? def.placeholder ?? '';
  }
  const sorted = Object.fromEntries(
    Object.entries(allKeys).sort(([a], [b]) => a.localeCompare(b))
  );
  return JSON.stringify(sorted, null, 2);
}, [values]);
```

No longer calls `invoke('agent_config_export')`. Rust command stays registered.

---

### `src/components/modules/settings/AgentConfigTab.tsx`

Add `exporting` state. Disable Export button while true; show "Exported" label.
Reset after 2s.

---

## Acceptance criteria

- [ ] Export includes all 11 known keys, not just set ones
- [ ] Unset keys use placeholder as hint value
- [ ] Keys sorted alphabetically in exported JSON
- [ ] GOOGLE_CREDENTIALS (JSON string value) exports as escaped string
- [ ] Export button disabled for 2s after click, label changes to "Exported"
- [ ] No TypeScript any
- [ ] bun run build exits 0, zero TypeScript errors
