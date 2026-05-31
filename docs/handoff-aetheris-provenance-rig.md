# Handoff — Aetheris + Provenance + Rig

**Session date:** 2026-05-31
**Prepared for:** next Claude session

---

## Repo locations

| Repo | Path | Purpose |
|------|------|---------|
| `aetheris` | `~/sandbox/elixirws/aetheris/` | Harness (Elixir + Rust) |
| `aetheris-agents` | `~/sandbox/elixirws/aetheris-agents/` | Agents, scripts, Rig UI, docs |
| `hai-rig` | `~/workspaces/hai/hai-rig/` | Old standalone Tauri repo (being retired) |
| test sandbox | `~/sandbox/provenance-test/` | Local corpus for pipeline validation |

---

## What is complete

### Provenance — all 6 milestones done

| Milestone | What it does |
|-----------|-------------|
| m1 | Inventory — scan NAS, populate f2_file_index, generate report |
| m2 | Classification — taxonomy session, classify batches, review cycle |
| m3 | Migration — copy approved files to /clients/, SHA-256 verify, rollback |
| m4 | Zip archaeology — extract zips, find new-to-corpus, handle encrypted |
| m5 | Corpus MCP + search — corpus-search MCP server, search_agent, validation |
| m6 | Tauri dashboard — corpus overview, classification review, migration + zip status |

### Rig — Phase 1 in progress

Rig is the new name for the Tauri desktop app, now living in
`aetheris-agents/rig/` (moved from `hai-rig`).

| Issue | Status |
|-------|--------|
| p1-001 Consolidation | 🔄 Build compiling (first Rust build, slow — wait for it) |
| p1-002 Harness DB commands | ⬜ Ready to start after p1-001 |
| p1-003 Run list UI | ⬜ Ready to start after p1-002 |

### Infrastructure — done

- Model parameterisation: all agent files use `PROVENANCE_MODEL` →
  `AETHERIS_MODEL` → hardcoded fallback. Configured via `aetheris-agents/.env`
- Capability matrix: generated and committed at `docs/capability-matrix.md`
- Runbook: `docs/provenance/runbook.md` — complete including "Before going live"
  checklist and model configuration section
- Test sandbox: `provenance/scripts/create_test_sandbox.py` — creates 26 files,
  5 zips, 4 duplicate groups, 1 encrypted zip, depth-3 nesting

---

## What is in progress

### p1-001 build

Claude Code is compiling `aetheris-agents/rig/` with `rusqlite` (bundled feature).
First build takes 5–8 minutes. When it finishes:

1. Confirm `cargo build` exits 0
2. Check `.gitignore` covers `rig/src-tauri/target/` and `rig/node_modules/`
3. Commit and move to p1-002

### Pending: uc-provenance-validation

Full pipeline validation against the test sandbox. In `ROADMAP.md` under
Planned. Steps in order:

1. Taxonomy session (`taxonomy_session.py` interactively)
2. Classification orchestrator against sandbox
3. Export → review → import cycle
4. Migration agent against sandbox
5. Zip archaeology against sandbox
6. Search validation (`validate_search.py`, pass rate ≥ 85%)
7. Eval sprint (`./scripts/sprint.sh eval`)

Blocked on: `ANTHROPIC_API_KEY` available in shell.

---

## What comes next (Rig roadmap)

| Phase | Goal |
|-------|------|
| p1 | ✅ Consolidation + run list UI (in progress) |
| p2 | Live monitoring — watch active runs update in real time |
| p3 | Orchestrator — NL request → plan → confirm → execute agents |
| p4 | Trajectory explorer — full event detail, search, export |

Phase docs live at `aetheris-agents/docs/rig/milestones/`.

---

## Key files to know

```
aetheris-agents/
  .env                              ← model defaults (AETHERIS_MODEL etc.)
  docs/
    capability-matrix.md            ← auto-generated, all agents + scripts
    capability-matrix-runbook.md    ← how to regenerate
    rig/
      README.md                     ← Rig project overview
      specs.md                      ← data model, command shapes, TS types
      architecture.md               ← component map, data flow
      runbook.md                    ← dev setup, env vars, common issues
      milestones/p1/                ← p1-001, p1-002, p1-003 issues
    provenance/
      runbook.md                    ← full Provenance operator guide
      milestones/                   ← m1–m6 issue files
  rig/                              ← Tauri app (new location)
  provenance/
    agents/                         ← all 7 Provenance agents
    scripts/                        ← all 16 Provenance scripts
    mcp/corpus-search/server.py     ← corpus-search MCP server

aetheris/
  config/runtime.exs               ← no model config (removed — agents read env directly)
  scripts/sprint.sh                 ← sources aetheris-agents/.env at start
  priv/aetheris.db                  ← harness SQLite (runs, events, orbs, skills)
  priv/runs/                        ← trajectory JSON files per run
```

---

## Patterns established

**Agent model config (two-level fallback):**
```elixir
model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"
```

**Rolling context causes 429 at step N:** switch to `context_strategy: :full`
for agents running ≤20 steps.

**Aetheris scan worked:** `mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs`
against the test sandbox produced correct results (26 files, 22 unique, 4 duplicates).

**`Application.ensure_all_started/1` returns `{:ok, []}` not `:ok`.**
Match as `{:ok, _} = Application.ensure_all_started(:aetheris)` in `.exs` scripts.

**Tauri Rust SQLite pattern (new in p1):**
- Use `rusqlite` with `bundled` feature
- Open read-only: `OpenFlags::SQLITE_OPEN_READ_ONLY | SQLITE_OPEN_NO_MUTEX`
- `HarnessState { conn: Option<Arc<Mutex<Connection>>> }` — same shape as `CorpusState`
- `json_extract(config_json, '$.label')` — SQLite built-in JSON, no casting needed

---

## Quick commands

```bash
# Run any Provenance agent
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs

# Check a run
mix aetheris inspect <run_id>
mix aetheris list --limit 5

# Regenerate capability matrix
./scripts/sprint.sh capability_matrix

# Reset test sandbox
python3 provenance/scripts/create_test_sandbox.py --overwrite

# Open Rig (after p1 complete)
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb
cargo tauri dev
```
