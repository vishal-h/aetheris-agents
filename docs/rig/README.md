# Rig — Aetheris Dashboard

Rig is the desktop UI for the Aetheris agent harness. It provides a unified
interface for inspecting agent runs, reviewing classified documents,
orchestrating multi-step workflows through natural language, and browsing
and running the tools available to agents.

Rig lives in `aetheris-agents/rig/` — it is an artifact of the agents repo,
not the harness. The harness (`aetheris/`) is generic infrastructure; Rig
is use-case aware.

---

## What it does

| Phase | Capability | Status |
|-------|-----------|--------|
| p1 | Run inspection — browse past agent runs and their event trajectories | ✅ |
| p2 | Live monitoring — watch an active run's events in real time | ✅ |
| p3 | Orchestrator — natural language → plan → confirm → execute | ✅ |
| p4 | Trajectory viewer + run diff — compare tool paths across runs | ✅ |
| p4-tools | Tools explorer — browse, inspect, and run scripts + MCP tools | ✅ |
| p5 | Run grouping + capability matrix — use-case overview + Run shortcuts | ✅ |
| p6 | Token/cost surface — per-run and aggregate cost/token stats | ✅ |
| p7 | Agent config + settings — env var config store with import/export | ✅ |
| p8 | Orchestrator reliability — step errors, Drive split, cancel, config hints | ✅ |
| orchestrator | Real orchestrator agent — LLM-driven plan generation | ✅ |
| — | Provenance corpus dashboard | ✅ (ported from hai-rig) |

See `docs/rig/current-state-2026-06.md` for a code-verified reality check
of all milestones and known doc drift.

---

## Two data sources

```
aetheris.db       SQLite — harness state: runs, events, orbs, skills
corpus.duckdb     DuckDB — Provenance corpus: files, classifications, migrations
```

Both are read-only in Rig except the single write path:
`set_classification_status` (approve/reject) opens a short-lived write
connection to `corpus.duckdb`.

---

## Repos

| Repo | Role |
|------|------|
| `aetheris/` | Harness — runs agents, writes aetheris.db and trajectory files |
| `aetheris-agents/` | Agents, scripts, and this Rig UI |
| (hai-rig was the old standalone Tauri repo — contents moved here) |

---

## Quick start

```bash
cd aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb        # optional
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...                               # optional
cargo tauri dev
```

---

## Documentation

- `docs/rig/specs.md` — data model, Tauri command shapes, TypeScript types
- `docs/rig/architecture.md` — component map and data flow
- `docs/rig/runbook.md` — dev setup, env vars, common issues
- `docs/rig/current-state-2026-06.md` — code-verified snapshot (authoritative)
- `docs/rig/milestones/` — phase READMEs and issue files
- `agent-config-reference.md` — agent config architecture, adding new keys
