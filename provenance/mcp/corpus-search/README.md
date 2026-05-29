# corpus-search MCP server

Provenance-specific stdio MCP server. Exposes DuckDB-backed metadata search
over the classified corpus to Aetheris agents. No external MCP framework —
plain Python JSON-RPC 2.0 over stdin/stdout.

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORPUS_DB_PATH` | Yes | — | Path to DuckDB corpus file |
| `CORPUS_SEARCH_READ_ONLY` | No | `true` | Set `false` to open read-write |
| `CORPUS_SEARCH_MCP_ENABLED` | Yes (agent) | — | Must be `true` to wire into agent |

## Tools

| Tool | Description |
|------|-------------|
| `search_corpus` | Keyword + metadata filter search (ILIKE over path/client/raw\_excerpt) |
| `list_clients` | All clients with file counts and doc\_type lists |
| `list_documents` | Documents for a client, optionally filtered by FY and doc\_type |
| `get_document_meta` | Full metadata for a single path; returns `null` if not found |
| `find_duplicates` | All corpus entries sharing a SHA-256 hash |

## Installation

No install step — the server is a single Python file. Requires `duckdb==1.5.3`:

```bash
pip install -r provenance/mcp/corpus-search/requirements.txt
```

## Test standalone

```bash
export CORPUS_DB_PATH=/data/corpus.duckdb
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  | python3 provenance/mcp/corpus-search/server.py
```

## Wiring into an agent

```elixir
db_path = System.get_env("PROVENANCE_DB_PATH") || raise "PROVENANCE_DB_PATH required"

corpus_search_server =
  if System.get_env("CORPUS_SEARCH_MCP_ENABLED") == "true" do
    %{
      server_id: "corpus_search",
      path:      "python3",
      args:      [Path.expand("mcp/corpus-search/server.py")],
      env:       %{"CORPUS_DB_PATH" => db_path}
    }
  end

mcp_servers = [corpus_search_server] |> Enum.reject(&is_nil/1)
```

`Path.expand("mcp/corpus-search/server.py")` resolves relative to the process
working directory (`aetheris/`), so the agent file's `sandbox_path` points to
`provenance/` while the MCP path expands from `aetheris/`.

## Run tests

```bash
python3 -m pytest provenance/mcp/corpus-search/tests/ -v
```
