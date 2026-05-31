# Register the provenance_search eval task in the Aetheris eval store.
#
# Run once from the aetheris/ directory:
#   mix run ../aetheris-agents/provenance/scripts/register_eval_task.exs
#
# The task smoke-tests the corpus-search MCP server by having the agent send an
# initialize request and verify the server responds with its tool list.
# This confirms the server starts correctly and is importable at eval time.

{:ok, _} = Application.ensure_all_started(:aetheris)

provenance_root =
  Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

# model/provider are baked into the template at registration time — if you change
# PROVENANCE_MODEL or AETHERIS_MODEL later, re-run this script to update the task.
model    = System.get_env("PROVENANCE_MODEL") || Application.get_env(:aetheris, :default_model)
provider = Application.get_env(:aetheris, :default_provider)

task = %Aetheris.Eval.Task{
  id:          "task_#{Aetheris.ID.generate()}",
  name:        "provenance_search",
  description: "corpus-search MCP server responds correctly to an initialize request",
  run_config_template: %{
    "provider"      => provider,
    "model"         => model,
    "label"         => "Provenance Search — MCP smoke test (eval)",
    "max_steps"     => 3,
    "tools"         => ["run_command"],
    "sandbox_path"  => provenance_root,
    "system_prompt" => """
    Test the corpus-search MCP server by sending it a JSON-RPC initialize request.

    Run this command:
      printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\\n' | CORPUS_DB_PATH=/tmp/eval_smoke.duckdb python3 mcp/corpus-search/server.py

    Report whether the server responded with the server name "corpus-search" and
    a tools list containing search_corpus, list_clients, list_documents,
    get_document_meta, and find_duplicates.
    """,
    "user_prompt"   => "Run the MCP server smoke test and confirm it responds correctly."
  },
  outcome_spec: %{
    type:    :regex,
    pattern: "(?i)(corpus-search|search_corpus|list_clients)"
  },
  created_at: DateTime.utc_now(),
  tags:        ["provenance", "mcp", "search"]
}

case Aetheris.Eval.Store.get_task_by_name(task.name) do
  {:ok, existing} ->
    IO.puts("Task \"#{task.name}\" already registered (id: #{existing.id}). No change.")

  {:error, :not_found} ->
    case Aetheris.Eval.Store.insert_task(task) do
      {:ok, inserted} ->
        IO.puts("Registered eval task \"#{inserted.name}\" (id: #{inserted.id})")

      {:error, reason} ->
        IO.puts(:stderr, "Failed to register task: #{inspect(reason)}")
        System.halt(1)
    end

  {:error, reason} ->
    IO.puts(:stderr, "Store error: #{inspect(reason)}")
    System.halt(1)
end
