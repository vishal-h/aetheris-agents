# Provenance — Architecture

## Overview

Provenance is built on the Aetheris agent harness. Agents drive all intelligent
work — scanning, classification, migration decisions, search. Scripts and tools
handle deterministic operations. DuckDB is the shared data layer between agents
and the reporting dashboard.

---

## Component map

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Server (VPN access)                           │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Aetheris                                  │    │
│  │                                                              │    │
│  │  Orchestrator agents                                         │    │
│  │    scan_orchestrator      ← drives f2-scanner               │    │
│  │    classification_orb     ← parallel classification         │    │
│  │    migration_agent        ← proposes + executes moves       │    │
│  │    zip_archaeologist      ← recursive zip extraction        │    │
│  │    search_agent           ← natural language → documents    │    │
│  │                                                              │    │
│  │  MCP servers                                                 │    │
│  │    corpus-search MCP      ← DuckDB + Matryoshka             │    │
│  │    Matryoshka (lattice)   ← token-efficient content access  │    │
│  └────────────────────────────┬─────────────────────────────┘    │
│                               │ run_command / MCP                  │
│  ┌────────────────────────────▼─────────────────────────────┐    │
│  │                  f2-scanner (CLI binary)                   │    │
│  │  Walk filesystem · SHA-256 hash · Upsert to DuckDB        │    │
│  │  Progress → scan_runs table (not Tauri events)            │    │
│  └────────────────────────────┬─────────────────────────────┘    │
│                               │                                    │
│  ┌────────────────────────────▼─────────────────────────────┐    │
│  │                    DuckDB (corpus.duckdb)                  │    │
│  │  f2_file_index · classifications · migrations             │    │
│  │  scan_runs · zip_inventory · zip_contents                 │    │
│  │  Views: client_corpus · duplicate_groups · migration_q    │    │
│  └────────────────────────────┬─────────────────────────────┘    │
│                               │ read (reporting only)              │
│  ┌────────────────────────────▼─────────────────────────────┐    │
│  │              Tauri Dashboard (auditor machines)            │    │
│  │  Corpus analytics · Migration status · Agent run history  │    │
│  │  Duplicate groups · Classification review                  │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ VPN / network mount
┌──────────────────────────────────▼──────────────────────────────────┐
│                            NAS                                        │
│                                                                       │
│  /archive/    ← original corpus (read-only after Phase 1)            │
│  /clients/    ← new structured store (write target from Phase 3)     │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Data flow by phase

### Phase 1 — Inventory

```
NAS /archive/
  → f2-scanner (run_command)
  → DuckDB f2_file_index
  → inventory_report_agent reads DuckDB
  → produces inventory_report.md
  → human reviews
```

### Phase 2 — Classification

```
DuckDB f2_file_index (unique files)
  → classification_orb (one agent per client batch)
    → corpus-search MCP → Matryoshka → read first N lines
    → LLM classifies: client, FY, doc_type, confidence
  → DuckDB classifications (status: proposed)
  → human approves/rejects via Tauri review view
  → status → approved
```

### Phase 3 — Migration

```
DuckDB classifications (approved)
  → migration_agent
    → proposes moves: source → /clients/{client}/{fy}/{doc_type}/
    → ask_human for batches above threshold
    → run_command: execute approved moves
  → DuckDB migrations (status: migrated)
  → NAS /clients/ populated
```

### Phase 4 — Zip archaeology

```
DuckDB f2_file_index (mime: application/zip, status: ok)
  → zip_archaeologist
    → extract to /staging/ (temp)
    → f2-scanner on staging
    → compare hashes against corpus
    → new_to_corpus → classification pipeline
    → already_known → discard
    → nested_zip → recurse (max depth 4)
    → encrypted → log + escalate
  → staging cleaned up
  → DuckDB zip_inventory updated
```

### Phase 5 — Search

```
Auditor query (natural language)
  → search_agent
    → corpus-search MCP: search_corpus(query, filters)
    → DuckDB full-text + metadata lookup
    → Matryoshka: read_document(handle) for top candidates
    → LLM synthesises answer with document references
  → response with file handles + summaries
```

---

## Deployment

| Component | Location | Access |
|-----------|----------|--------|
| Aetheris | Server | VPN |
| f2-scanner binary | Server | via Aetheris run_command |
| DuckDB file | Server | Local to Aetheris; read by Tauri via VPN |
| Matryoshka (lattice-mcp) | Server | stdio MCP subprocess |
| corpus-search MCP | Server | stdio MCP subprocess |
| Tauri dashboard | Auditor machines | Connects to DuckDB over VPN |
| NAS /archive/ | NAS | Read-only mount on server |
| NAS /clients/ | NAS | Read-write mount on server |

---

## Trust boundaries

| Component | Trust | Notes |
|-----------|-------|-------|
| Aetheris orchestrator | Trusted | Owns all decisions and audit log |
| f2-scanner | Semi-trusted | Sandboxed via Aetheris exec server |
| corpus-search MCP | Semi-trusted | Read-only DuckDB access |
| NAS /archive/ | Untrusted input | Read-only; no agent writes here |
| NAS /clients/ | Write target | Only migration_agent writes here, after approval |
| Tauri dashboard | Untrusted | Read-only DuckDB; no write path |

---

## Key design decisions

**DuckDB as the shared medium.** Agents write via scripts/run_command.
Tauri reads for reporting. No direct agent ↔ Tauri communication needed.

**NAS /archive/ is permanently read-only.** No agent ever modifies the original
corpus. This is enforced at the mount level, not just in code.

**Human approval gates between phases.** Nothing moves to the next phase without
explicit sign-off. The Aetheris `ask_human` escalation protocol handles this.

**Matryoshka for content access.** Raw file reads burn tokens at scale.
Matryoshka's handle-based model means agents read file stubs and drill into
content only when needed. Critical for a corpus of 100GB+.

**Trajectory as audit log.** Every agent decision — every classification, every
migration proposal, every escalation — is recorded in the Aetheris trajectory.
The auditors can audit the auditor.
