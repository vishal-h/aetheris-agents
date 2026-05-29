# Provenance — Technical Specifications

## 1. DuckDB Schema

### Core tables

```sql
-- File index (populated by f2-scanner)
CREATE TABLE f2_file_index (
    path          TEXT PRIMARY KEY,
    size_bytes    BIGINT,
    modified_at   TIMESTAMP,
    mime_type     TEXT,
    sha256        TEXT,
    status        TEXT DEFAULT 'ok',  -- ok | duplicate | missing | encrypted
    last_scanned  TIMESTAMP
);

-- Scan run tracking
CREATE TABLE scan_runs (
    id              TEXT PRIMARY KEY,   -- UUID
    root_path       TEXT NOT NULL,
    started_at      TIMESTAMP NOT NULL,
    finished_at     TIMESTAMP,
    status          TEXT DEFAULT 'running', -- running | complete | failed
    files_scanned   BIGINT DEFAULT 0,
    files_new       BIGINT DEFAULT 0,
    files_updated   BIGINT DEFAULT 0,
    duplicates_found BIGINT DEFAULT 0,
    aetheris_run_id TEXT                -- trajectory reference
);

-- Classification results
CREATE TABLE classifications (
    id              TEXT PRIMARY KEY,   -- UUID
    path            TEXT NOT NULL REFERENCES f2_file_index(path),
    client          TEXT,
    financial_year  TEXT,               -- e.g. FY2024
    doc_type        TEXT,               -- tax | legal | accounts | correspondence | other
    confidence      REAL,               -- 0.0–1.0
    raw_excerpt     TEXT,               -- first N lines used for classification
    status          TEXT DEFAULT 'proposed', -- proposed | approved | rejected
    classified_at   TIMESTAMP NOT NULL,
    reviewed_at     TIMESTAMP,
    reviewed_by     TEXT,
    aetheris_run_id TEXT
);

-- Migration log
CREATE TABLE migrations (
    id              TEXT PRIMARY KEY,   -- UUID
    path            TEXT NOT NULL,      -- source path
    dest_path       TEXT NOT NULL,      -- target path on /clients/
    classification_id TEXT REFERENCES classifications(id),
    status          TEXT DEFAULT 'proposed', -- proposed | approved | migrated | failed
    proposed_at     TIMESTAMP NOT NULL,
    migrated_at     TIMESTAMP,
    error           TEXT,
    aetheris_run_id TEXT
);

-- Zip file inventory
CREATE TABLE zip_inventory (
    path            TEXT PRIMARY KEY,
    size_bytes      BIGINT,
    depth           INTEGER DEFAULT 0,  -- nesting depth from root zip
    parent_zip      TEXT,               -- path of containing zip, if nested
    extracted_to    TEXT,               -- staging path
    contents_count  INTEGER,
    new_to_corpus   INTEGER DEFAULT 0,  -- files not already in f2_file_index
    status          TEXT DEFAULT 'pending', -- pending | extracted | processed | encrypted | failed
    processed_at    TIMESTAMP,
    aetheris_run_id TEXT
);

-- Files found inside zips
CREATE TABLE zip_contents (
    id              TEXT PRIMARY KEY,
    zip_path        TEXT REFERENCES zip_inventory(path),
    internal_path   TEXT NOT NULL,      -- path inside the zip
    sha256          TEXT,
    size_bytes      BIGINT,
    corpus_match    TEXT,               -- path in f2_file_index if already known
    status          TEXT DEFAULT 'new'  -- new | known | migrated | discarded
);
```

### Views

```sql
-- Classified corpus ready for migration
CREATE VIEW client_corpus AS
SELECT
    c.client,
    c.financial_year,
    c.doc_type,
    c.confidence,
    f.path,
    f.size_bytes,
    f.mime_type,
    f.sha256,
    c.status AS classification_status
FROM classifications c
JOIN f2_file_index f ON c.path = f.path
WHERE f.status != 'missing'
ORDER BY c.client, c.financial_year, c.doc_type;

-- Duplicate groups
CREATE VIEW duplicate_groups AS
SELECT
    sha256,
    COUNT(*) AS copy_count,
    SUM(size_bytes) AS total_size,
    MIN(path) AS canonical_candidate,
    ARRAY_AGG(path) AS all_paths
FROM f2_file_index
WHERE sha256 IS NOT NULL AND status != 'missing'
GROUP BY sha256
HAVING COUNT(*) > 1;

-- Migration queue
-- Note: DuckDB 1.5.3 does not have basename(). Use
--   regexp_extract(path, '([^/]+)$', 1) for the filename component.
CREATE VIEW migration_queue AS
SELECT
    c.id AS classification_id,
    f.path AS source_path,
    '/clients/' || c.client || '/' || c.financial_year
        || '/' || c.doc_type || '/' || regexp_extract(f.path, '([^/]+)$', 1) AS proposed_dest,
    c.confidence
FROM classifications c
JOIN f2_file_index f ON c.path = f.path
LEFT JOIN migrations m ON m.classification_id = c.id
WHERE c.status = 'approved'
  AND m.id IS NULL
  AND f.status != 'missing';

-- Zip backlog
CREATE VIEW zip_backlog AS
SELECT path, size_bytes, depth, status
FROM zip_inventory
WHERE status IN ('pending', 'failed')
ORDER BY depth, size_bytes DESC;
```

---

## 2. File taxonomy

```
/clients/
  {client_id}/          ← normalised: lowercase, spaces → underscores
    FY{YYYY}/           ← e.g. FY2024 (April–March for AU/UK, Jan–Dec otherwise)
      tax/              ← tax returns, BAS, GST, income statements
      legal/            ← notices, contracts, court documents
      accounts/         ← balance sheets, P&L, trial balance, workpapers
      correspondence/   ← letters, emails (exported), memos
      other/            ← anything that doesn't fit the above
```

Document type classification rules are captured from the taxonomy session and
stored in `agents/provenance/taxonomy.md`. This file is the system prompt
source for the classification agent.

---

## 3. f2-scanner CLI

```
USAGE:
    f2-scanner scan [OPTIONS] --root <PATH> --db <PATH>
    f2-scanner resume --run-id <ID> --db <PATH>
    f2-scanner status --db <PATH>

OPTIONS:
    --root <PATH>         Root path to scan
    --db <PATH>           DuckDB file path
    --ignore <GLOB>       Additional ignore patterns (repeatable)
    --run-id <ID>         Scan run ID (generated if not provided)
    --throttle <PCT>      CPU throttle threshold (default: 50)
    --batch-size <N>      Progress update interval (default: 50)

EXIT CODES:
    0   Scan completed successfully
    1   Scan failed (see stderr)
    2   Scan interrupted (resumable with resume subcommand)
```

Progress is written to `scan_runs` table in DuckDB, not to stdout.
Structured JSON status line written to stdout on completion:

```json
{"run_id": "...", "status": "complete", "files_scanned": 142300,
 "duplicates_found": 89234, "duration_ms": 4823100}
```

---

## 4. Agent interfaces

### scan_orchestrator

```elixir
%Aetheris.RunConfig{
  tools:       ["run_command", "read_file"],
  mcp_servers: [],
  max_steps:   20,
  system_prompt: """
  You are a scan orchestrator for the Provenance document management system.
  Drive f2-scanner against the NAS archive, monitor completion, and
  produce a summary for human review.
  """
}
```

### classification_orb

One agent per client batch. Spawned by orchestrator after inventory approval.

```elixir
%Aetheris.RunConfig{
  tools:       ["run_command"],
  mcp_servers: [corpus_search_mcp, lattice_mcp],
  max_steps:   50,
  system_prompt: """
  Classify documents for assigned client batch.
  Use corpus-search MCP to retrieve documents, Matryoshka to read content.
  Write classifications to DuckDB via classify_documents.py script.
  """
}
```

### migration_agent

```elixir
%Aetheris.RunConfig{
  tools:       ["run_command", "read_file"],
  mcp_servers: [],
  max_steps:   30,
  system_prompt: """
  Execute approved migrations from f2_file_index to /clients/ structure.
  Use migration_queue view to get candidates.
  Escalate batches above 100 files for human confirmation before executing.
  Log every move to migrations table.
  """
}
```

### zip_archaeologist

```elixir
%Aetheris.RunConfig{
  tools:       ["run_command"],
  mcp_servers: [],
  max_steps:   40,
  system_prompt: """
  Process one zip file per run. Extract to staging, scan contents,
  compare against corpus. Classify new-to-corpus documents.
  Never exceed depth 4. Escalate encrypted zips immediately.
  Clean up staging on completion.
  """
}
```

---

## 5. Corpus search MCP tools

Self-developed stdio MCP. Lives at `mcp/stdio/src/corpus-search/`.

| Tool | Input | Output |
|------|-------|--------|
| `search_corpus` | `query, client?, fy?, doc_type?, limit?` | Ranked list of `{path, client, fy, doc_type, confidence}` |
| `list_clients` | *(none)* | All known clients from classifications table |
| `list_documents` | `client, fy?, doc_type?` | Documents matching filters |
| `get_document_meta` | `path` | Full classification record for a file |
| `find_duplicates` | `sha256` | All paths sharing this hash |

Backed by DuckDB queries. Read-only. Combines with Matryoshka for content access:
`search_corpus` returns handles → `lattice_load(path)` opens content.

---

## 6. Scripts

| Script | Purpose | Called by |
|--------|---------|-----------|
| `classify_documents.py` | Write classification batch to DuckDB | classification_orb |
| `approve_classifications.py` | Bulk approve/reject from a CSV | human operator |
| `execute_migration.py` | Move approved files, update migrations table | migration_agent |
| `extract_zip.py` | Extract zip to staging, return manifest | zip_archaeologist |
| `inventory_report.py` | Query DuckDB, produce Markdown report | scan_orchestrator |
| `taxonomy_session.py` | Structured interview → taxonomy.md | one-time human setup |

All scripts: `python3 scripts/{name}.py --db /data/corpus.duckdb [args]`
All scripts: exit 0 on success, exit 1 on error, structured JSON to stdout.
