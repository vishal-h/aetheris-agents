# provenance/m5: corpus-search MCP server

## Context

The corpus-search MCP is the metadata search layer over the Provenance corpus.
It exposes DuckDB-backed tools to Aetheris agents via the standard stdio
JSON-RPC 2.0 protocol. No external MCP framework — plain Python over stdio.

This is the first self-developed MCP server in this project. It lives at
`mcp/stdio/src/corpus-search/` following the conventions in `mcp/CLAUDE.md`.

## What to build

### `mcp/stdio/src/corpus-search/server.py`

A Python stdio MCP server implementing the JSON-RPC 2.0 protocol.

**Protocol requirements:**
- Read newline-delimited JSON from stdin, write responses to stdout
- Handle `initialize` handshake (return server info + capabilities)
- Handle `tools/list` (return tool definitions)
- Handle `tools/call` (dispatch to tool handlers)
- Ignore notifications (messages without `"id"`)
- Never crash — catch all exceptions and return JSON-RPC error responses

**Environment variables:**
- `CORPUS_DB_PATH` — required; path to DuckDB corpus file
- `CORPUS_SEARCH_READ_ONLY` — default `true`; open DuckDB read-only

### Tools

**`search_corpus`**

Search the corpus by keyword and/or metadata filters.

Input schema:
```json
{
  "query":    {"type": "string", "description": "Search terms"},
  "client":   {"type": "string", "description": "Filter by client ID"},
  "fy":       {"type": "string", "description": "Filter by financial year (e.g. FY2024)"},
  "doc_type": {"type": "string", "description": "Filter by document type"},
  "limit":    {"type": "integer", "default": 20}
}
```

Search logic:
1. If `query` provided: tokenise on whitespace; each token must match at least
   one of: `path ILIKE`, `client ILIKE`, or `raw_excerpt ILIKE`
2. Apply `client`, `fy`, `doc_type` filters where provided
3. Join `classifications` with `f2_file_index`
4. Return up to `limit` results ordered by `confidence DESC, path ASC`

Output: JSON array of `{path, client, fy, doc_type, confidence, raw_excerpt_preview, status, size_bytes}`

`raw_excerpt_preview`: first 200 chars of `raw_excerpt`.

**`list_clients`**

List all known clients with file counts.

Input: `{}` (no parameters)

Output: `[{client, file_count, doc_types}]` ordered by `client ASC`

```sql
SELECT client, COUNT(*) AS file_count,
       ARRAY_AGG(DISTINCT doc_type ORDER BY doc_type) AS doc_types
FROM classifications
WHERE status IN ('proposed', 'approved')
GROUP BY client
ORDER BY client
```

**`list_documents`**

List documents for a specific client, optionally filtered.

Input schema:
```json
{
  "client":   {"type": "string", "required": true},
  "fy":       {"type": "string"},
  "doc_type": {"type": "string"},
  "limit":    {"type": "integer", "default": 50}
}
```

Output: `[{path, fy, doc_type, confidence, status, size_bytes, mime_type}]`

**`get_document_meta`**

Full metadata for a specific file path.

Input: `{"path": {"type": "string", "required": true}}`

Output:
```json
{
  "path": "...",
  "client": "...", "fy": "...", "doc_type": "...",
  "confidence": 0.92,
  "raw_excerpt": "...",
  "status": "approved",
  "size_bytes": 120000,
  "mime_type": "application/pdf",
  "sha256": "...",
  "classification_status": "approved"
}
```

Returns `null` if path not found.

**`find_duplicates`**

Find all corpus entries with the same SHA-256 hash.

Input: `{"sha256": {"type": "string", "required": true}}`

Output: `[{path, size_bytes, status, last_scanned}]`

### Supporting files

`mcp/stdio/src/corpus-search/requirements.txt`:
```
duckdb==1.5.3
```

`mcp/stdio/src/corpus-search/README.md`:
Brief description, env vars, tool list, how to test standalone.

### Registration

Per `mcp/CLAUDE.md`:
1. Add row to `mcp/stdio/README.md` server table
2. Add row to `mcp/README.md` stdio MCPs table
3. Add row to `mcp/stdio/node/package.json` — N/A (Python, not npm)

### Availability pattern in agent files

```elixir
db_path = System.get_env("PROVENANCE_DB_PATH", "")

corpus_search_server =
  if System.get_env("CORPUS_SEARCH_MCP_ENABLED") == "true" && db_path != "" do
    %{
      server_id: "corpus_search",
      path:      "python3",
      args:      [Path.expand("mcp/stdio/src/corpus-search/server.py")],
      env:       %{"CORPUS_DB_PATH" => db_path}
    }
  end
```

## Acceptance criteria

- [ ] Server handles `initialize` → `tools/list` → `tools/call` sequence without error
- [ ] All 5 tools return correct results against `sample_corpus.duckdb` fixture
- [ ] `search_corpus` with keyword finds files whose `raw_excerpt` contains that word
- [ ] `search_corpus` with `client` filter returns only that client's files
- [ ] `list_clients` returns all clients with correct counts
- [ ] `get_document_meta` returns `null` for unknown paths (no crash)
- [ ] Server never crashes on malformed input — returns JSON-RPC error response
- [ ] `pytest mcp/stdio/src/corpus-search/tests/test_server.py` — 12+ tests pass
- [ ] Registered in `mcp/stdio/README.md` and `mcp/README.md`
- [ ] `mcp/stdio/src/corpus-search/README.md` written

## Files to create

- `mcp/stdio/src/corpus-search/server.py`
- `mcp/stdio/src/corpus-search/requirements.txt`
- `mcp/stdio/src/corpus-search/README.md`
- `mcp/stdio/src/corpus-search/tests/__init__.py`
- `mcp/stdio/src/corpus-search/tests/test_server.py`
- `mcp/stdio/README.md` (update)
- `mcp/README.md` (update)

## Notes

**Testing the server directly.** The test suite should exercise the tool
handlers directly (calling the Python functions, not going through the JSON-RPC
layer) for unit tests. A small integration test can exercise the full
JSON-RPC flow using `subprocess` + stdin/stdout.

**`raw_excerpt` ILIKE search.** Tokenise the query on whitespace:
```python
tokens = query.split()
conditions = " AND ".join(
    f"(path ILIKE ? OR client ILIKE ? OR raw_excerpt ILIKE ?)"
    for _ in tokens
)
params = [f"%{t}%" for t in tokens for _ in range(3)]
```

**Read-only DuckDB.** Open with `read_only=True` by default. The corpus
is written by Aetheris agents; the search server never writes.

**Server stdin/stdout isolation.** Any `print()` debug output from DuckDB
or Python internals will corrupt the JSON-RPC stream. Use `sys.stderr` for
all logging. Wrap the entire read loop in a try/except that writes JSON-RPC
error responses on stdout.
