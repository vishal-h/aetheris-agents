# Phase 5 — Run Grouping + Capability Matrix

**Goal:** Make the run list navigable at scale, and surface the agent/script
inventory as a launchable catalogue.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [Run list grouping](p5-001-run-list-grouping.md) | — | Parse run labels → collapsible use-case groups → show more per group |
| 002 | [Capability matrix view](p5-002-capability-matrix.md) | 001 (shares registry/route patterns) | New Harness section: agents by use case, readonly scripts, launch via Orchestrator |

001 and 002 are independent — they can be implemented in parallel. 001 is
pure frontend; 002 needs one new Tauri command.

---

## Completion gate

- Run list groups runs by use case (payslip, drive, email, api/tenant,
  api/gateway, provenance, unclassified)
- Each group is collapsible; shows 10 runs by default with a "Show all" toggle
- Status filter applies within groups
- Capability Matrix section appears in the Harness sidebar
- Agents are listed by use case with their tool badges
- Scripts are listed as readonly reference (name + purpose)
- Clicking Run on an agent navigates to `/orchestrator` with the textarea
  pre-filled as `{agent_label}: `
- All existing modules unaffected
- `bun run build` exits 0, zero TypeScript errors
- `cargo build` exits 0, zero warnings

---

## Key decisions

**Label parsing for grouping (p5-001).** Run labels follow the convention
`{use-case-slug}-{AgentLabel}-{RunId}`. The use case is extracted by matching
the label prefix against a known set of slugs. Runs that don't match are
grouped under "Unclassified". The capability matrix file is not read for
grouping — that's deferred to a future issue (C on the backlog).

**Capability matrix parsed in Rust (p5-002).** `capability_matrix_load` reads
`docs/capability-matrix.md` from `AETHERIS_AGENTS_PATH` and parses the
Markdown into structured data. Parsing is line-by-line: section headers
identify use cases, table rows identify agents and scripts.

**Option A launch flow (p5-002).** Clicking Run on an agent navigates to
`/orchestrator` and pre-fills the request textarea with `{agent_label}: `.
The Orchestrator view owns all execution state — no duplication. The cursor
lands after the colon so the user types their intent naturally.

**Scripts are readonly (p5-002).** Scripts are reference material only —
name and one-line purpose. No launch button. This matches their role in the
architecture: scripts are called by agents, not run directly by users.

**Backlog: matrix-as-grouping-source.** Replace label-prefix parsing with
capability-matrix-derived prefixes. Requires `capability_matrix_load` (built
in p5-002) to be called from `useHarness`. Tracked but not specced.
