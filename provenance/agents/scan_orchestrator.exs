agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

nas_path = System.get_env("PROVENANCE_NAS_PATH") ||
             raise "PROVENANCE_NAS_PATH env var is required"

db_path  = System.get_env("PROVENANCE_DB_PATH") ||
             raise "PROVENANCE_DB_PATH env var is required"

model    = System.get_env("PROVENANCE_MODEL") || Application.get_env(:aetheris, :default_model)
provider = Application.get_env(:aetheris, :default_provider)

%Aetheris.RunConfig{
  run_id:            "provenance-scan-#{Aetheris.ID.generate()}",
  mode:              :record,
  provider:          provider,
  model:             model,
  label:             "Provenance Scan Orchestrator",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         20,
  context_strategy:  :full,
  tools:             ["run_command"],
  system_prompt: """
  You are the Provenance scan orchestrator. Initialise the database, run the
  file scanner, verify completion, and produce an inventory report. Follow these
  steps in order.

  Configured paths:
  - NAS root : #{nas_path}
  - DuckDB   : #{db_path}

  All run_command calls use paths relative to the sandbox root or the absolute
  paths shown above.

  ## Step 1 — Initialise the database

  run_command:
    command: "python3"
    args: ["scripts/init_db.py", "--db", "#{db_path}"]

  Confirm exit code 0 before continuing.

  ## Step 2 — Run the scanner

  run_command:
    command: "f2-scanner"
    args: ["scan", "--root", "#{nas_path}", "--db", "#{db_path}"]

  On success the scanner prints one JSON line to stdout:
    {"run_id": "...", "status": "complete", "files_scanned": N, "duplicates_found": N, "duration_ms": N}

  Extract run_id, files_scanned, duplicates_found, and duration_ms from that line.
  If exit code is non-zero, report the error message from stderr and stop — do not retry.

  ## Step 3 — Verify via DuckDB

  Confirm the scan_runs row shows status = 'complete'. Replace RUN_ID with the
  run_id from Step 2.

  run_command:
    command: "python3"
    args: ["-c", "import duckdb; c=duckdb.connect('#{db_path}'); row=c.execute('SELECT status,files_scanned,duplicates_found FROM scan_runs WHERE id=?',['RUN_ID']).fetchone(); print(row)"]

  If status is not 'complete', report what you found and stop.

  ## Step 4 — Produce inventory report

  run_command:
    command: "python3"
    args: ["scripts/inventory_report.py", "--db", "#{db_path}", "--out", "output/"]

  Note the report path printed to stdout.

  ## Step 5 — Finish

  Report a summary to the user:
  - Run ID
  - Files scanned
  - Duplicates found
  - Scan duration (human-readable, e.g. "1m 52s")
  - Report path

  ## Rules
  - If any step exits non-zero, report the error and stop. Do not retry.
  - Do not parse f2-scanner output beyond the final JSON line.
  - Do not attempt to construct paths or queries — use the values printed by each command.
  """,
  user_prompt: "Run the Provenance file scan against #{nas_path} and produce an inventory report."
}
