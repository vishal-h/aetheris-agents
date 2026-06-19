agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

tenant    = System.get_env("DOCBUILDER_TENANT")    || raise "DOCBUILDER_TENANT not set"
doc_type  = System.get_env("DOCBUILDER_DOC_TYPE")  || raise "DOCBUILDER_DOC_TYPE not set"
version   = System.get_env("DOCBUILDER_VERSION")   || raise "DOCBUILDER_VERSION not set"
data_path = System.get_env("DOCBUILDER_DATA_PATH") || raise "DOCBUILDER_DATA_PATH not set"

template_path = "data/templates/#{tenant}/#{doc_type}_#{version}.json"
filename      = "#{doc_type}_#{version}"

model    = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

system_prompt = """
You are the docbuilder orchestrator. Your job is to run the document-generation
pipeline and report the output files produced.

Configuration resolved at startup:
  Tenant:        #{tenant}
  Doc type:      #{doc_type}
  Version:       #{version}
  Data path:     #{data_path}
  Template path: #{template_path}
  Output filename prefix: #{filename}

---

Workflow — follow these steps in order:

1. Fetch data.
   Call run_command with:
     command: "python3"
     args: ["scripts/fetch_data.py", "--key", "main", "#{data_path}"]
   Capture the full stdout string. It is a JSON object.

2. Save the raw data to a temp file.
   Call write_file with:
     path: "output/pipeline_raw.json"
     content: <the exact stdout string from step 1>

3. Compute the doc spec.
   Call run_command with:
     command: "python3"
     args: ["scripts/compute_doc.py", "#{template_path}", "output/pipeline_raw.json"]
   Capture the full stdout string. It is a JSON object (the doc spec).

4. Save the doc spec to a temp file.
   Call write_file with:
     path: "output/pipeline_spec.json"
     content: <the exact stdout string from step 3>

5. Read output_formats from the doc spec JSON you captured in step 3.
   For each format in output_formats, call run_command with:
     command: "python3"
     args: ["scripts/generate_<format>.py", "--input", "output/pipeline_spec.json", "--output-dir", "output", "--filename", "#{filename}"]
   Replace <format> with the actual format string (e.g. xlsx, pdf, csv, json, xml, md).
   Record the output path printed by each renderer (its stdout).

6. Report the list of output files generated. If any step produced a non-zero
   exit code, report the stderr from that step and stop.

---

Rules:
- All paths are relative to the sandbox root.
- overlay_base_dir is nil — output files persist on disk.
- If any script returns exit code 1, report the stderr and stop. Do not retry
  or investigate manually.
- Do not construct or modify JSON yourself. The scripts produce all data.
- Do not pass "python3" inside the args array — it is already the command field.
"""

%Aetheris.RunConfig{
  run_id:           "docbuilder-orch-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Docbuilder Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        20,
  context_strategy: :full,
  tools:            ["run_command", "write_file"],
  system_prompt:    system_prompt,
  user_prompt:      "Run the document generation pipeline."
}
