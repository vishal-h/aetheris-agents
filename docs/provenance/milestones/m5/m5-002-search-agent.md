# provenance/m5: search_agent.exs

## Context

The search agent is the human-facing interface to the corpus. It takes a
natural language query, translates it into corpus-search MCP calls, optionally
deepens the search with Matryoshka, and returns a formatted response with
relevant document paths and summaries.

## What to build

`agents/search_agent.exs`

### Behaviour

The agent receives a query via `SEARCH_QUERY` env var (or `user_prompt`).

**Step 1 — Metadata search**

Use the `search_corpus` MCP tool:
```
search_corpus(query="{user's query}", limit=10)
```

If results are found: present them with paths, client, FY, doc_type, and the
raw_excerpt preview. Go to Step 3.

If results are empty or insufficient (<3 results): proceed to Step 2.

**Step 2 — Broaden search (if Step 1 insufficient)**

Try one or two alternative search strategies:
- Strip stop words from the query and retry
- Try individual key terms from the query
- Use `list_clients` + `list_documents` to navigate by client if the query
  mentions a client name

If Matryoshka is available (`lattice_load` in the tool schema):
- Load the top candidate files with `lattice_load`
- Use `grep` to search for the query terms in the content
- Return files with matching content

**Step 3 — Format response**

Present results as a structured list:

```
Found N documents matching "{query}":

1. {path}
   Client: {client} | FY: {fy} | Type: {doc_type}
   Confidence: {confidence}
   Preview: {raw_excerpt_preview}

2. ...
```

If no results after both steps:
```
No documents found matching "{query}".
Suggestions:
- Try broader search terms
- Check available clients: [call list_clients]
- Search by document type: tax, legal, accounts, correspondence
```

### Env vars

| Variable | Required | Description |
|----------|---------|-------------|
| `PROVENANCE_DB_PATH` | Yes | DuckDB corpus path (passed to corpus-search MCP) |
| `SEARCH_QUERY` | No | Pre-set query (otherwise agent uses user_prompt) |
| `CORPUS_SEARCH_MCP_ENABLED` | Yes | Must be `true` |
| `LATTICE_MCP_ENABLED` | No | Enable Matryoshka content search |

### RunConfig

```elixir
db_path = System.get_env("PROVENANCE_DB_PATH") || raise "PROVENANCE_DB_PATH required"

corpus_search_server =
  if System.get_env("CORPUS_SEARCH_MCP_ENABLED") == "true" do
    %{
      server_id: "corpus_search",
      path:      "python3",
      args:      [Path.expand("mcp/stdio/src/corpus-search/server.py")],
      env:       %{"CORPUS_DB_PATH" => db_path}
    }
  end

lattice_bin = Path.expand("mcp/stdio/node/node_modules/.bin/lattice-mcp")
lattice_server =
  if System.get_env("LATTICE_MCP_ENABLED") == "true" && File.exists?(lattice_bin) do
    %{server_id: "lattice", path: lattice_bin, args: [], env: %{}}
  end

mcp_servers = [corpus_search_server, lattice_server] |> Enum.reject(&is_nil/1)

%Aetheris.RunConfig{
  ...
  tools:       [],
  mcp_servers: mcp_servers,
  max_steps:   10,
  system_prompt: """
  You are a document search assistant for an audit firm's corpus.

  Search the corpus using the tools available to you.
  Always start with search_corpus for the full query.
  If results are sparse, try narrower terms or navigate by client.
  If lattice_load is available, use it for deeper content search on top candidates.

  Present results clearly: path, client, FY, type, and a brief preview.
  If nothing is found, suggest alternatives.
  """,
  user_prompt: System.get_env("SEARCH_QUERY", "Search the corpus.")
}
```

### Invocation

```bash
export PROVENANCE_DB_PATH=/data/corpus.duckdb
export CORPUS_SEARCH_MCP_ENABLED=true
SEARCH_QUERY="tax returns for acme FY2024" \
  mix aetheris run ../aetheris-agents/provenance/agents/search_agent.exs
```

## Acceptance criteria

- [ ] Agent evaluates without error
- [ ] `corpus_search` tool appears in trajectory when CORPUS_SEARCH_MCP_ENABLED=true
- [ ] Agent returns formatted results for a query that matches `sample_corpus.duckdb`
- [ ] Agent returns helpful "not found" message for a query with no matches
- [ ] Matryoshka tools used when LATTICE_MCP_ENABLED=true and binary exists
- [ ] `pytest tests/test_search_agent.py` — eval check + smoke test pass
- [ ] Runbook updated with search section

## Files to create/modify

- `provenance/agents/search_agent.exs`
- `provenance/tests/test_search_agent.py`
- `docs/provenance/runbook.md`

## Notes

**`tools: []` with only MCP servers.** Since the worker-start fix (Aetheris
`Agent.Supervisor` patch in m2), an agent with `tools: []` and non-empty
`mcp_servers` correctly starts the worker. No `http_call` workaround needed.

**Step 2 is optional.** If the corpus-search MCP returns good results on the
first call, the agent should not waste steps on broadening. The system prompt
should make this clear: Step 2 only when Step 1 returns <3 results.

**Search covers the full corpus.** The `search_corpus` tool queries both
classified and unclassified files. The agent does not need to know whether
files are in `/clients/` or `/archive/` — the MCP handles that.
