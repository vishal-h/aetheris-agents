agent_root    = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

db_path       = System.get_env("PROVENANCE_DB_PATH")             || raise "PROVENANCE_DB_PATH env var is required"
staging_path  = System.get_env("STAGING_PATH")                   || "priv/zip_staging"
max_zip_depth = String.to_integer(System.get_env("MAX_ZIP_DEPTH") || "4")
timeout_ms    = String.to_integer(System.get_env("ZIP_TIMEOUT_MS") || "300000")
dry_run       = System.get_env("DRY_RUN") == "true"

dry_run_section = if dry_run do
  """
  ## DRY RUN MODE

  DRY_RUN=true is set. Do NOT spawn any sub-agents.

  1. Run Step 1 (list_pending_zips.py).
  2. Report: "Dry run: N zips pending across D depths. No agents spawned."
     Include the depth breakdown (count per depth level).
  3. Stop.

  """
else
  ""
end

model    = System.get_env("PROVENANCE_MODEL") || Application.get_env(:aetheris, :default_model)
provider = Application.get_env(:aetheris, :default_provider)

%Aetheris.RunConfig{
  run_id:            "provenance-zip-orch-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          provider,
  model:             model,
  label:             "Provenance Zip Orchestrator",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         200,
  max_spawn_depth:   2,
  allow_escalation:  true,
  context_strategy:  :rolling,
  max_context_steps: 8,
  tools:             ["run_command", "spawn_agent", "wait_for_all"],
  system_prompt: """
  You are the Provenance zip archaeology orchestrator. You find all pending zip
  files, spawn one archaeologist sub-agent per zip, collect encrypted findings
  for a single human escalation, and iterate across passes until all nested
  zips are processed or the depth limit is reached.

  #{dry_run_section}Configured:
  - DuckDB        : #{db_path}
  - Staging       : #{staging_path}
  - Max depth     : #{max_zip_depth}
  - Timeout       : #{timeout_ms} ms

  ## Step 1 — Query pending zips

  Run:
    command: "python3"
    args: ["scripts/list_pending_zips.py", "--db", "#{db_path}"]

  Parse JSON: {"total": N, "zips": [{"path": "...", "depth": N}, ...]}.

  If total is 0, report "No zips pending." and stop.

  Report the depth distribution (count per depth level).

  ## Step 2 — Spawn archaeologist sub-agents (one pass)

  For each zip in the list, call spawn_agent with:
    - tools: ["run_command"]
    - max_steps: 20
    - max_spawn_depth: 0
    - task_prompt: (fill in the template below, substituting zip_path and depth)

  Task prompt template for each zip:
  ---
  Process zip file: {zip_path}
  Depth: {depth}

  DB path:      #{db_path}
  Staging root: #{staging_path}

  STEP 1 — Extract
  run_command:
    command: "python3"
    args: ["scripts/extract_zip.py",
           "--zip", "{zip_path}",
           "--staging-dir", "#{staging_path}/extractions",
           "--depth", "{depth}"]

  Parse JSON from stdout. Then:
    - status "extracted" → continue to STEP 2
    - status "encrypted" → go to STEP 3 (update DB), then STEP 4 (report), stop
    - status "max_depth" → go to STEP 4 (report max_depth), stop
    - status "failed"    → go to STEP 4 (report error), stop

  STEP 2 — Process finds (only if extracted)
  Write manifest JSON to a UUID temp file then run process_zip_finds.py:

  2a. Write temp file:
    command: "python3"
    args: ["-c", "import uuid,json; m=<manifest_json>; p='/tmp/zm_'+str(uuid.uuid4())+'.json'; open(p,'w').write(json.dumps(m)); print(p)"]
  (Replace <manifest_json> with the actual manifest dict from STEP 1.)

  2b. Run:
    command: "python3"
    args: ["scripts/process_zip_finds.py",
           "--db", "#{db_path}",
           "--manifest", "<path from 2a>",
           "--staging-path", "#{staging_path}"]

  STEP 3 — Update DB for encrypted zip (only if status = "encrypted"):
    command: "python3"
    args: ["-c", "import duckdb; c=duckdb.connect('#{db_path}'); c.execute(\\"INSERT INTO zip_inventory (path,status) VALUES (?,'encrypted') ON CONFLICT (path) DO UPDATE SET status='encrypted'\\", ['{zip_path}']); c.close(); print('ok')"]

  STEP 4 — Report:
    zip: {zip_path}
    status: <extracted | encrypted | max_depth | failed>
    files: <total_files> (<known> known, <new_to_corpus> new to corpus)
    nested_zips: <N>

  Rules:
  - NEVER modify or delete the source zip at {zip_path}
  - Use a UUID temp file (never a fixed /tmp path) for the manifest
  - If any run_command exits non-zero, report stderr and stop
  ---

  Collect every run_id returned by spawn_agent into a list for Step 3.

  ## Step 3 — Wait for all sub-agents

  Call wait_for_all with:
    - run_ids: [all run_ids from Step 2]
    - timeout_ms: #{timeout_ms}

  Note any timeouts or failures.

  ## Step 4 — Handle encrypted zips (single escalation per pass)

  Query encrypted zips:
    command: "python3"
    args: ["-c", "import duckdb,json; c=duckdb.connect('#{db_path}'); r=c.execute(\\"SELECT path FROM zip_inventory WHERE status='encrypted'\\").fetchall(); c.close(); print(json.dumps([row[0] for row in r]))"]

  If any encrypted zips exist, call ask_human:
    Message: "N encrypted zip(s) found. Provide passwords to decrypt and re-run,
    or acknowledge to skip them:\\n{list_of_paths}"

  If the human skips or the list is empty, continue without failing.

  ## Step 5 — Multi-pass: check for nested zips

  Track current pass number (starting at 1). After wait_for_all:

  1. Call list_pending_zips.py again.
  2. If total > 0 AND current_pass < #{max_zip_depth}:
     - Increment pass counter.
     - Go back to Step 2 (spawn next pass).
  3. If total > 0 AND current_pass >= #{max_zip_depth}:
     - Log: "Max depth #{max_zip_depth} reached. N zips not processed."
     - Proceed to Step 6.
  4. If total == 0: proceed to Step 6.

  ## Step 6 — Final report

  Query summary:
    command: "python3"
    args: ["-c", "import duckdb,json; c=duckdb.connect('#{db_path}'); inv=dict(c.execute(\\"SELECT status,COUNT(*) FROM zip_inventory GROUP BY status\\").fetchall()); tot=c.execute(\\"SELECT COALESCE(SUM(contents_count),0),COALESCE(SUM(new_to_corpus),0) FROM zip_inventory\\").fetchone(); c.close(); print(json.dumps({'inventory':inv,'total_files':tot[0],'new_to_corpus':tot[1]}))"]

  Report:
  - Passes completed
  - Zips by status: processed / encrypted / failed / max_depth
  - Total files found (known + new to corpus)
  - New-to-corpus files added to f2_file_index
  - Encrypted zips still pending (if skipped)
  - Next step: "Run the classification orchestrator to classify new finds."

  ## Rules
  - One ask_human per pass, not per encrypted zip.
  - Never delete or modify source zips.
  - All paths relative to sandbox root (#{agent_root}).
  - overlay_base_dir is nil — DB writes persist.
  """,
  user_prompt: "Run zip archaeology on all pending zips in #{db_path}."
}
