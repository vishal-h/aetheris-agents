# eduloka/agents/eduloka_orchestrator.exs
#
# Orchestrates the full eduloka discovery pipeline over data/terms.txt:
#   list_terms → [per term: fetch → map → enrich → sink]
#
# Runtime env vars:
#   SEARCH_PROVIDER    provider for fetch.py (default: cse)
#   EDUX_SINK          direct (Postgres upsert) or export (JSONL handoff); default: export
#   EDUX_DATABASE_URL  required when EDUX_SINK=direct; must be set before eval
#   EDUX_TERMS_FILE    override path to terms file (default: data/terms.txt)
#
# Run:
#   mix aetheris run ../aetheris-agents/eduloka/agents/eduloka_orchestrator.exs

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

provider  = System.get_env("SEARCH_PROVIDER")   || "cse"
edux_sink = System.get_env("EDUX_SINK")          || "export"

# Fail fast: direct sink requires a DB URL — no silent fallback to export.
if edux_sink == "direct" && is_nil(System.get_env("EDUX_DATABASE_URL")) do
  raise "EDUX_SINK=direct requires EDUX_DATABASE_URL to be set. " <>
        "Set the env var or use EDUX_SINK=export for the file-handoff sink."
end

sink_script =
  case edux_sink do
    "direct" -> "upsert_institute.py"
    "export" -> "export_institute.py"
    other    -> raise "EDUX_SINK must be 'direct' or 'export', got: #{other}"
  end

model         = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
provider_name = System.get_env("AETHERIS_PROVIDER") || "anthropic"

system_prompt = """
You are the eduloka discovery orchestrator. Drive the institute-data pipeline
over the configured term list. Follow the workflow exactly.

Workflow — follow these steps in order:

Step 1 — Load terms.
  Call run_command with:
    command: "python3"
    args: ["scripts/list_terms.py"]
  Parse the JSON output. Extract:
    - "terms"  — original terms (used for API queries)
    - "slugs"  — filesystem-safe versions (used for all paths)
  Both lists are the same length; terms[i] and slugs[i] are a pair.
  If status is "error" or count is 0, report the error and stop.

Step 2 — Spawn one sub-agent per term.
  For each pair (T=terms[i], S=slugs[i]), call spawn_agent with:
    tools: ["run_command"]
    max_steps: 20
    task_prompt: (use the template below — replace <TERM> with T and <SLUG> with S)

  Sub-agent task prompt template:
  ===
  You are an eduloka pipeline worker. Process ONE search term to completion.

  Term (for API):  <TERM>
  Slug (for paths): <SLUG>
  Provider: #{provider}
  Sink:     #{edux_sink} (script: scripts/#{sink_script})

  Execute each step in order. Report any error immediately and stop.

  Step A — Fetch raw results:
    Call run_command with:
      command: "python3"
      args: ["scripts/fetch.py", "--provider", "#{provider}", "--term", "<TERM>",
             "--output-dir", "data/raw/<SLUG>"]
    On success the raw file is: data/raw/<SLUG>/#{provider}.jsonl
    If status is "error", report the error and stop.

  Step B — Map to edux format:
    Call run_command with:
      command: "python3"
      args: ["scripts/map.py",
             "--in",  "data/raw/<SLUG>/#{provider}.jsonl",
             "--out", "data/edux/<SLUG>.jsonl"]
    If status is "error" or "partial", report and stop.

  Step C — Enrich:
    Call run_command with:
      command: "python3"
      args: ["scripts/enrich.py",
             "--in",  "data/edux/<SLUG>.jsonl",
             "--out", "data/gold/<SLUG>.jsonl"]
    If status is "error" or "partial", report and stop.

  Step D — Sink:
    Call run_command with:
      command: "python3"
      args: ["scripts/#{sink_script}",
             "--in", "data/gold/<SLUG>.jsonl"]
    Report the full output (status, count, out path).

  After completing all four steps, report:
    "term: <TERM> (slug: <SLUG>) — done. Sink status: <status from Step D>."
  ===

Step 3 — Wait for all sub-agents.
  Collect all run_ids returned by the spawn_agent calls.
  Call wait_for_all with:
    run_ids: [the collected run_ids]
    timeout_ms: 600000

Step 4 — Report results.
  Report: total terms processed, how many sub-agents completed successfully,
  and the names of any failed terms.

Rules:
- Use the exact run_command format (command: and args: as separate fields).
  Never put "python3" inside args — command: "python3", args: ["scripts/..."].
- All paths use the slug, not the raw term.
- All paths are relative to the sandbox root.
- overlay_base_dir is nil; output files must persist on disk.
- If wait_for_all reports failures, report which terms failed and stop.
  Do not investigate, explore files, or retry manually.
"""

# max_steps: list_terms(1) + spawn N(N) + wait_for_all(1) + report(1) + buffer(3).
# Set to 50 to handle up to ~44 terms without hitting the ceiling.
%Aetheris.RunConfig{
  run_id:            "eduloka-orch-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          provider_name,
  model:             model,
  label:             "Eduloka Orchestrator",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         50,
  max_spawn_depth:   2,
  context_strategy:  :full,
  tools:             ["run_command", "spawn_agent", "wait_for_all"],
  system_prompt:     system_prompt,
  user_prompt:       "Run the eduloka discovery pipeline. Begin."
}
