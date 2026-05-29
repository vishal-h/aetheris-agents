# Provenance — Roadmap

## Milestone summary

| # | Milestone | Theme | Deliverable | Gate |
|---|-----------|-------|-------------|------|
| m1 | Inventory | Foundation | Complete file index + inventory report | Human reviews report |
| m2 | Classification | Intelligence | Every unique file classified by client/FY/type | Human approves classifications |
| m3 | Migration | Structure | Clean corpus on new NAS structure | Human approves migration batch |
| m4 | Zip archaeology | Completeness | All zip contents inventoried and classified | Human reviews new-to-corpus finds |
| m5 | Corpus MCP + Search | Discovery | Natural language search over full corpus | Auditors validate search quality |
| m6 | Tauri dashboard | Visibility | Analytics and review UI for all stakeholders | Stakeholder sign-off |

---

## m1 — Inventory

**Goal:** Know exactly what exists before touching anything.

**Delivered:**
- `f2-scanner` extracted from Tauri context — standalone CLI binary
- DuckDB schema v1 (f2_file_index, scan_runs, zip_inventory)
- `scan_orchestrator` agent — triggers scanner, monitors completion
- `inventory_report.py` — queries DuckDB, produces human-readable Markdown report
- Report covers: total files, unique files, duplicate groups, size distribution,
  MIME type breakdown, estimated FY distribution, zip file count

**Gate:** Senior auditor reviews inventory report and confirms it accurately
reflects the known state of the storage before Phase 2 begins.

**Not in scope:** Classification, migration, zip extraction, any file modifications.

---

## m2 — Classification

**Goal:** Every unique document assigned to client, FY, and document type.

**Delivered:**
- `taxonomy_session.py` — structured interview script to capture classification rules
- `taxonomy.md` — output of the session; system prompt source for classification agents
- `classification_orb` — parallel agents, one per client batch
- `classify_documents.py` — writes classification results to DuckDB
- Tauri classification review view (basic) — approve/reject proposed classifications
- `approve_classifications.py` — bulk review tool for human operator
- Confidence scoring — classifications below threshold flagged for mandatory review

**Gate:** Human operator reviews proposed classifications (sample + low-confidence).
Approval recorded in DuckDB before migration begins.

**Not in scope:** Moving any files.

---

## m3 — Migration

**Goal:** Approved documents in the correct location on the new NAS structure.

**Delivered:**
- `/clients/` folder structure created on NAS
- `migration_agent` — reads migration_queue view, executes approved moves
- `execute_migration.py` — atomic move with DuckDB logging
- Escalation for batches > 100 files (ask_human before execution)
- `migrations` table fully populated with source, dest, status, timestamp
- NAS `/archive/` mount switched to read-only

**Gate:** Human reviews migration summary. Spot-check sample of moved files in
new location before original paths are considered superseded.

**Not in scope:** Zip extraction, dedup deletion, anything on /archive/.

---

## m4 — Zip archaeology

**Goal:** Nothing important hidden in zip files.

**Delivered:**
- `zip_archaeologist` agent — one per zip, spawned in parallel
- `extract_zip.py` — extracts to staging, returns manifest
- Recursive zip handling (max depth 4)
- Encrypted zip detection + escalation
- New-to-corpus documents fed into classification pipeline (m2 agents)
- `zip_inventory` and `zip_contents` tables populated
- Staging cleanup on completion

**Gate:** Human reviews new-to-corpus findings from zips before they are
classified and migrated. Encrypted zip list reviewed — passwords sourced
from appropriate staff.

**Not in scope:** Deleting original zips (deferred indefinitely).

---

## m5 — Corpus MCP + Natural language search

**Goal:** Ask a question, get the relevant documents.

**Delivered:**
- `corpus-search` MCP server (`mcp/stdio/src/corpus-search/`)
- Tools: `search_corpus`, `list_clients`, `list_documents`, `get_document_meta`, `find_duplicates`
- Matryoshka integration for content-level search
- `search_agent` — natural language query → document results with summaries
- Full-text indexing on DuckDB (FTS extension)
- Search covers both `/clients/` (migrated) and `/archive/` (original)

**Gate:** Auditors run 20 representative queries against the search agent.
Pass rate ≥ 85% (relevant results returned) before sign-off.

---

## m6 — Tauri dashboard

**Goal:** All stakeholders can see the state of the corpus without touching a terminal.

**Delivered:**
- Corpus overview: total files, unique, duplicates, size by client/FY
- Migration status: what's been moved, what's pending, what failed
- Classification review: approve/reject proposed classifications from the UI
- Zip inventory: status of all zip processing
- Agent run history: what ran, when, outcomes (reads Aetheris trajectory index)
- Search interface: natural language query via search_agent

**Gate:** Stakeholder walkthrough. All views working. Sign-off from firm contact.

---

## Capability arc

```
m1   Know what exists
m2   Know what it is
m3   Put it where it belongs
m4   Leave nothing behind
m5   Find anything
m6   See everything
```

---

## Dependencies and sequencing

```
m1 ──→ m2 ──→ m3
              ↑
m1 ──→ m4 ───┘   (zip finds feed classification pipeline)

m3 + m4 ──→ m5   (search needs complete classified corpus)
m5      ──→ m6   (dashboard search tab needs search agent)
```

m1 and m4 can partially overlap — zip scanning can begin while flat file
classification is running, as long as zip extraction targets staging rather
than the corpus directly.
