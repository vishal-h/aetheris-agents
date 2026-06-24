# Implementation notes — rig-p9 t2

Ticket: Docbuilder stored config entry + `STEP_CONFIG_HINTS`.

---

## What shipped

- **`src/components/modules/settings/agentConfigDefs.ts`** — new "Docbuilder" group with
  one entry:
  `{ key: 'DOCBUILDER_TENANT', label: 'Tenant', group: 'Docbuilder', masked: false, placeholder: 'bitloka' }`.
  Placed after the Payslip group, before Provenance. (Export is `AGENT_CONFIG_DEFS`,
  typed `Omit<AgentConfigEntry, 'value'>[]` — the entry matches the existing shape.)
  Adding the key here is sufficient for the Settings UI and for automatic env-var
  injection at spawn time (the `agent_config` cache → `orchestrate_start`'s first loop).
- **`src/components/modules/orchestrator/OrchestratorView.tsx`** — three
  `STEP_CONFIG_HINTS` entries so the plan view surfaces the vars the operator should
  verify before approving:
  - `docbuilder/agents/context_builder.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']`
  - `docbuilder/agents/docbuilder_orchestrator.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_CONTEXT_FILE']`
  - `docbuilder/agents/docbuilder_context_orchestrator.exs` → `['DOCBUILDER_TENANT', 'DOCBUILDER_REQUEST']`

---

## Scope adherence

- Only `DOCBUILDER_TENANT` added to stored config — `DOCBUILDER_REQUEST` and
  `DOCBUILDER_CONTEXT_FILE` are per-run vars (t1 `extra_env` / set by the chained
  orchestrator) and intentionally **not** in `agentConfigDefs.ts`.
- No new module/route/sidebar entry (that is t4); no Rust changes.

---

## Done-check

- `bun run tsc --noEmit` → **no errors**.
- `grep DOCBUILDER_TENANT|Docbuilder agentConfigDefs.ts` → entry with group "Docbuilder".
- `grep` the three agent paths in `STEP_CONFIG_HINTS` → all present.
- **`cargo tauri dev` smoke — NOT run** (interactive GUI; no display). Manual pass needed:
  Settings → a "Docbuilder" section with a `Tenant` field (placeholder `bitloka`).

---

## Notes

- `docbuilder_context_orchestrator.exs` is referenced in `STEP_CONFIG_HINTS` but does not
  exist until t3. A hint for a not-yet-existing agent is harmless — `STEP_CONFIG_HINTS` is
  a lookup keyed by agent path; an entry with no matching plan step is simply never read.
