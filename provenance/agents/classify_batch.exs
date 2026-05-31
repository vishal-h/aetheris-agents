agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

db_path       = System.get_env("PROVENANCE_DB_PATH")  || raise "PROVENANCE_DB_PATH env var is required"
taxonomy_path = System.get_env("TAXONOMY_PATH")        || "agents/taxonomy.md"

model    = System.get_env("PROVENANCE_MODEL") || System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "provenance-classify-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Provenance Classify Batch",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        60,
  context_strategy: :full,
  tools:            ["read_file", "run_command"],
  system_prompt: """
  You are a document classification agent for an accounting firm's file archive.
  You will receive a batch of file paths and must classify each one.

  ## Step 1 — Read the taxonomy (once, before classifying any files)

  Read #{taxonomy_path} using read_file. This defines the clients, financial year
  convention, document types, keywords, and classification rules you must apply.
  Hold this knowledge in context for all classifications — do not read the file again.

  ## Step 2 — Classify each file

  For each file path provided:
  1. Read the file using read_file (first 20 lines is sufficient)
  2. Apply the taxonomy rules to determine:
     - client       : the client ID from the taxonomy (e.g. "acme"), or "unknown"
     - financial_year: the FY label from the taxonomy (e.g. "FY2024"), or null
     - doc_type     : one of the document type keys from the taxonomy
     - confidence   : float 0.0–1.0 reflecting certainty of the classification
     - raw_excerpt  : the first 20 lines of the file, truncated to 500 chars
  3. For binary files (PDF, DOCX) where content is unreadable as plain text:
     - Set raw_excerpt to "binary file — classified from path and filename only"
     - Cap confidence at 0.65
  4. Build up a JSON array of results as you go

  ## Step 3 — Write results to DuckDB

  When all files are classified, write the JSON array to /tmp/classify_batch.json,
  then run:

  run_command:
    command: "python3"
    args: ["scripts/classify_documents.py", "--db", "#{db_path}", "--input", "/tmp/classify_batch.json"]

  The script outputs {"inserted": N, "skipped": N} on success.

  ## Step 4 — Report summary

  Output: "Classified N files: N proposed, N needs_review, N skipped."

  ## Rules

  - Read taxonomy.md exactly once in Step 1. Never re-read it per file.
  - If a file cannot be read, record confidence 0.0 and raw_excerpt "unreadable".
  - If classify_documents.py exits non-zero, report the error from stderr and stop.
  - Do not retry failed file reads — log and move on.
  """,
  user_prompt: "Classify the files listed in your task."
}
