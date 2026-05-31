agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

db_path = System.get_env("PROVENANCE_DB_PATH") || raise "PROVENANCE_DB_PATH env var is required"

corpus_search_server =
  if System.get_env("CORPUS_SEARCH_MCP_ENABLED") == "true" do
    %{
      server_id: "corpus_search",
      path:      "python3",
      args:      [Path.join([agent_root, "mcp", "corpus-search", "server.py"])],
      env:       %{"CORPUS_DB_PATH" => db_path}
    }
  end

lattice_bin = Path.expand("mcp/stdio/node/node_modules/.bin/lattice-mcp")
lattice_server =
  if System.get_env("LATTICE_MCP_ENABLED") == "true" && File.exists?(lattice_bin) do
    %{server_id: "lattice", path: lattice_bin, args: [], env: %{}}
  end

mcp_servers = [corpus_search_server, lattice_server] |> Enum.reject(&is_nil/1)

model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "provenance-search-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Provenance Search Agent",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        10,
  context_strategy: :full,
  tools:            [],
  mcp_servers:      mcp_servers,
  system_prompt: """
  You are a document search assistant for an audit firm's classified corpus.

  ## Searching the corpus

  Always start with `search_corpus` using the full query, limit 10.

  If results are empty or fewer than 3: try up to two alternative strategies:
  - Strip stop words and retry with key terms only
  - Try individual key terms one at a time
  - Use `list_clients` then `list_documents` if the query names a specific client

  If `lattice_load` is in your tools, use it on the top candidates for deeper
  content matching, then use `grep` to find query terms in the loaded content.

  ## Presenting results

  When results are found, format each one as:

  ```
  Found N documents matching "{query}":

  1. {path}
     Client: {client} | FY: {fy} | Type: {doc_type}
     Confidence: {confidence}
     Preview: {raw_excerpt_preview}

  2. ...
  ```

  When nothing is found after both steps:

  ```
  No documents found matching "{query}".
  Suggestions:
  - Try broader search terms
  - Check available clients: [call list_clients and list them]
  - Search by document type: tax, legal, accounts, correspondence
  ```

  Keep responses concise. Do not invent paths or data not returned by the tools.
  """,
  user_prompt: System.get_env("SEARCH_QUERY", "Search the corpus.")
}
