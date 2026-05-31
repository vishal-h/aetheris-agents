# Rig — Aetheris Dashboard

Rig is the desktop UI for the Aetheris agent harness. It provides a unified
interface for inspecting agent runs, reviewing classified documents, and
orchestrating multi-step workflows through natural language.

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
| p4 | Trajectory explorer — full event detail, diff, export | ✅ |
| —  | Provenance corpus dashboard | ✅ (ported from hai-rig) |

---

## Three data sources

```
aetheris.db                SQLite — harness state: runs, events, orbs, skills
priv/runs/*/trajectory.json  JSON — immutable per-run snapshot: events + meta
corpus.duckdb              DuckDB — Provenance corpus: files, classifications, migrations
```

`aetheris.db` and the trajectory files are read-only in Rig. `corpus.duckdb`
has one write path: `set_classification_status` (approve/reject) opens a
short-lived write connection.

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
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb  # optional
cargo tauri dev
```

---

## Documentation

- `docs/rig/specs.md` — data model, Tauri command shapes, TypeScript types
- `docs/rig/architecture.md` — component map and data flow
- `docs/rig/runbook.md` — dev setup, env vars, common issues
- `docs/rig/milestones/` — phase READMEs and issue files
