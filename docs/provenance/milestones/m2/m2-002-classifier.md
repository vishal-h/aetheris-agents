# provenance/m2: Classifier script and agent

## Context

With `taxonomy.md` in place, we need two things that work together:
1. A script that writes classification results to DuckDB
2. An Aetheris sub-agent that reads a batch of files and classifies each one

The sub-agent is spawned by the orchestrator (m2-003). It receives a batch of
file paths, reads each file's content, applies the taxonomy rules, and calls
the script to write results.

## What to build

### `scripts/classify_documents.py`

Receives a JSON array of classification results on stdin and writes them to the
`classifications` table. One record per file.

**Input (stdin):**
```json
[
  {
    "path": "/data/archive/acme/FY2024/tax_return.pdf",
    "client": "acme",
    "financial_year": "FY2024",
    "doc_type": "tax",
    "confidence": 0.92,
    "raw_excerpt": "first 20 lines of the file..."
  },
  ...
]
```

**CLI:**
```
echo '[...]' | python3 scripts/classify_documents.py --db /data/corpus.duckdb
python3 scripts/classify_documents.py --db /data/corpus.duckdb --input classifications.json
```

**Behaviour:**
- Inserts each record into `classifications` with a generated UUID
- `status` is set to `'proposed'` if `confidence >= THRESHOLD`, else `'needs_review'`
- `THRESHOLD` defaults to 0.70; overridden by `CLASSIFICATION_THRESHOLD` env var
- `classified_at` is set to `now()`
- Skip files that already have a `proposed` or `approved` classification
  (idempotent — safe to re-run on the same batch)
- Exits 0 on success; writes count of inserted records to stdout as JSON:
  `{"inserted": N, "skipped": N}`

### `agents/classify_batch.exs`

Sub-agent that classifies a batch of files. Spawned by the orchestrator.

**Reads from env:**
- `PROVENANCE_DB_PATH`
- `TAXONOMY_PATH` — path to `agents/taxonomy.md` (default: `agents/taxonomy.md`)
- `CLASSIFICATION_THRESHOLD` (optional, default 0.70)

**`task_prompt` structure** (passed by orchestrator via `spawn_agent`):
```
Classify the following files using the taxonomy rules in agents/taxonomy.md.

Files to classify:
- /data/archive/acme/FY2024/tax_return.pdf
- /data/archive/acme/FY2024/letter_jan.docx
...

For each file:
1. Read the first 20 lines using read_file
2. Classify: client, financial_year, doc_type, confidence (0.0–1.0), raw_excerpt
3. Collect all results into a JSON array

When all files are classified, write results:
  run_command:
    command: "python3"
    args: ["scripts/classify_documents.py", "--db", "{db_path}"]
  Pass the JSON array via --input or stdin.

Output a summary: N classified, N needs_review.
```

**Tools:** `["read_file", "run_command"]`

If Matryoshka is available (`LATTICE_MCP_ENABLED=true`), the agent uses
`lattice_load` + `grep` instead of `read_file`. The task_prompt does not
change — the agent selects the best available tool.

## Acceptance criteria

**classify_documents.py:**
- [ ] Writes all fields correctly to `classifications` table
- [ ] Sets `status = 'needs_review'` when `confidence < THRESHOLD`
- [ ] Idempotent — second run on same paths is a no-op, no duplicates
- [ ] Outputs `{"inserted": N, "skipped": N}` JSON to stdout
- [ ] Exits 0 on success, 1 on error
- [ ] `pytest tests/test_classify_documents.py` — 6+ tests pass

**classify_batch.exs:**
- [ ] Agent file evaluates without error
- [ ] `mix run --eval 'Code.eval_file(...)'` passes with env vars set
- [ ] Test run against 3 files from `tests/fixtures/` completes in ≤ 5 steps
- [ ] Results appear in `classifications` table after run

## Files to create

- `provenance/scripts/classify_documents.py`
- `provenance/agents/classify_batch.exs`
- `provenance/tests/test_classify_documents.py`

## Notes

The classifier agent reads `taxonomy.md` content via `read_file` at the start
of its run and includes it in its reasoning. It does not have the taxonomy baked
into its system prompt — the taxonomy is runtime data, not prompt data. This
allows taxonomy changes without modifying agent files.

`raw_excerpt` should be the first 20 lines of the file, truncated to 500 chars.
It is stored for audit purposes — reviewers can see what content the agent used
to make its classification decision.

For binary files (PDFs, DOCX): `read_file` returns the raw bytes as a string.
The agent should note "binary file — classified from path and filename only" in
`raw_excerpt` and lower confidence accordingly (max 0.65 for path-only
classifications).

The `classifications` table uses `path` as a foreign key to `f2_file_index`.
The script must verify the path exists in `f2_file_index` before inserting.
Unknown paths are skipped with a warning, not an error.
