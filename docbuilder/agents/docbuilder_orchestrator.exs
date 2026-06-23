agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

tenant = System.get_env("DOCBUILDER_TENANT") || raise "DOCBUILDER_TENANT not set"

# Context source (m3 t4). Precedence:
#   1. DOCBUILDER_CONTEXT env var (non-empty) — explicit/legacy runs always win, so a
#      stale output/confirmed_context.json can never hijack a direct env-var run.
#   2. output/confirmed_context.json — written by the context builder (context_builder.exs);
#      this is the "same as last month" → render handoff when no env var is set.
#   3. "{}" — never pass an empty --context to a script (json.loads("") would fail).
confirmed_path = Path.join(agent_root, "output/confirmed_context.json")

{raw_context_json, context_source} =
  case System.get_env("DOCBUILDER_CONTEXT") do
    v when is_binary(v) and v != "" -> {v, "env:DOCBUILDER_CONTEXT"}
    _ ->
      if File.exists?(confirmed_path) do
        {File.read!(confirmed_path), "file:output/confirmed_context.json"}
      else
        {"{}", "default:{}"}
      end
  end

context = Jason.decode!(raw_context_json)
# Normalise to compact single-line JSON for verbatim prompt interpolation (the file
# source is pretty-printed; the "one arg, verbatim" steps need a single line).
context_json = Jason.encode!(context)

# Delivery creds — when absent, the matching delivery PHASE is skipped (the pipeline
# degrades gracefully in dev; runs fully in production).
env_or_nil = fn name ->
  case System.get_env(name) do
    nil -> nil
    "" -> nil
    v -> v
  end
end

drive_id      = env_or_nil.("DRIVE_DOCBUILDER_ID")
review_email  = env_or_nil.("DOCBUILDER_REVIEW_EMAIL")
deliver_upload? = drive_id != nil
deliver_email?  = review_email != nil

# --- resolve doc_type / variant at eval time (from the catalogue + context) -----
# The LLM selection in PHASE 0 is genuine but confirmatory: for a single-variant
# catalogue (the demo) it resolves to the one entry; the orchestrator pre-bakes the
# downstream commands against this resolution. Multi-variant runtime selection is a
# future concern (see docs/m2b-milestone.md).
catalogue =
  agent_root |> Path.join("data/templates/#{tenant}/catalogue.json")
  |> File.read!() |> Jason.decode!()

doc_types = catalogue["doc_types"] || []
resolved_doc_type = context["doc_type"] || (List.first(doc_types) || %{})["doc_type"]
dt_entry = Enum.find(doc_types, fn d -> d["doc_type"] == resolved_doc_type end) || %{}
resolved_version = ((List.first(dt_entry["variants"] || []) || %{})["version"])

prefix = "#{resolved_doc_type}_#{resolved_version}"

# Bundle dir = where fetch_template puts the template bundle. Drive → local cache;
# no Drive → the committed local nested bundle. The renderers point --base-file /
# --template-dir here.
bundle_dir =
  if drive_id,
    do: "output/template_cache/#{tenant}/#{resolved_doc_type}/#{resolved_version}",
    else: "data/templates/#{tenant}/#{resolved_doc_type}/#{resolved_version}"

bundle_template_rel = "#{bundle_dir}/#{prefix}.json"

# Resolve data_sources / output_formats / narrative from the committed template at
# eval time (always present, even in Drive mode where the bundle isn't fetched yet).
# It mirrors the bundle template that compute_doc reads at runtime. Prefer the
# canonical NESTED bundle layout (data/templates/{tenant}/{doc_type}/{version}/);
# fall back to the FLAT layout (the demo keeps both). A nested-only tenant (e.g.
# bitloka) resolves here without a flat duplicate.
nested_dir_rel    = "data/templates/#{tenant}/#{resolved_doc_type}/#{resolved_version}"
nested_exists?    = File.exists?(Path.join(agent_root, "#{nested_dir_rel}/#{prefix}.json"))
eval_template_dir = if nested_exists?, do: nested_dir_rel, else: "data/templates/#{tenant}"

template =
  agent_root |> Path.join("#{eval_template_dir}/#{prefix}.json")
  |> File.read!() |> Jason.decode!()

data_sources   = template["data_sources"] || []
output_formats = template["output_formats"] || []
narrative?     = is_map(template["narrative"])

# Base-file presence: proxy via the committed base files alongside the eval template.
xlsx_base? = File.exists?(Path.join(agent_root, "#{eval_template_dir}/#{prefix}.xlsx"))
docx_base? = File.exists?(Path.join(agent_root, "#{eval_template_dir}/#{prefix}.docx"))

# Source paths in the template are repo-root-relative ("docbuilder/data/...") but
# run_command runs from the docbuilder sandbox — strip the leading "docbuilder/"
# at eval time (t2 review F3, Option a; same strip the m2a orchestrator did).
sources =
  Enum.map(data_sources, fn s ->
    key = s["key"]
    %{
      key: key,
      path: String.replace_prefix(s["path"] || "", "docbuilder/", ""),
      raw_file: "output/pipeline_raw_#{key}.json"
    }
  end)

raw_files = Enum.map(sources, & &1.raw_file)

# --- renamed output paths (deterministic from context) for PHASE E ---------------
slugify = fn name ->
  s = name |> to_string() |> String.trim() |> String.downcase() |> String.replace(" ", "_")
  Regex.replace(~r/[^a-z0-9_-]/, s, "")
end

safe_seg = fn v ->
  s = Regex.replace(~r/\s+/, v |> to_string() |> String.trim(), "_")
  Regex.replace(~r/[^A-Za-z0-9_.-]/, s, "")
end

rename_doc_type = context["doc_type"] || Regex.replace(~r/_v\d+$/, prefix, "")
client_slug = slugify.(context["client_name"] || "")
safe_date = safe_seg.(context["date"] || "")
renamed_files =
  Enum.map(output_formats, fn ext ->
    "output/#{client_slug}_#{rename_doc_type}_#{safe_date}.#{ext}"
  end)

model    = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

# Pre-establish the run_id so it can be referenced both in the RunConfig and in
# the PHASE D2 run-log step (m3: the context builder reads run_log by run_id).
run_id = "docbuilder-orch-#{Aetheris.ID.generate()}"

# --- build concrete step text -------------------------------------------------

fetch_steps =
  sources
  |> Enum.with_index(1)
  |> Enum.map(fn {s, i} ->
    """
      A#{i}. Fetch source "#{s.key}":
            run_command  command: "python3"
                         args: ["scripts/fetch_data.py", "--key", "#{s.key}", "#{s.path}", "--output", "#{s.raw_file}"]
            Writes #{s.raw_file} and prints only that path.
    """
  end)
  |> Enum.join("\n")

compute_args =
  ["scripts/compute_doc.py", bundle_template_rel] ++
    raw_files ++ ["--output", "output/pipeline_spec.json"]

render_steps =
  output_formats
  |> Enum.with_index(1)
  |> Enum.map(fn {fmt, i} ->
    cond do
      fmt == "pdf" and narrative? ->
        display_args =
          ["scripts/generate_pdf.py", "--input", "output/pipeline_spec.json",
           "--template-dir", bundle_dir, "--context", "<CONTEXT>",
           "--output-dir", "output", "--filename", prefix]

        """
          C#{i}. Render pdf (narrative mode):
                run_command  command: "python3"  args: #{inspect(display_args)}
                Replace the "<CONTEXT>" element with this EXACT JSON, one arg, verbatim:
                  #{context_json}
        """

      true ->
        extra =
          case fmt do
            "xlsx" -> if xlsx_base?, do: ["--base-file", "#{bundle_dir}/#{prefix}.xlsx"], else: []
            "docx" -> if docx_base?, do: ["--base-file", "#{bundle_dir}/#{prefix}.docx"], else: []
            _ -> []
          end

        args =
          ["scripts/generate_#{fmt}.py", "--input", "output/pipeline_spec.json"] ++
            extra ++ ["--output-dir", "output", "--filename", prefix]

        """
          C#{i}. Render #{fmt}:
                run_command  command: "python3"  args: #{inspect(args)}
        """
    end
  end)
  |> Enum.join("\n")

rename_args =
  ["scripts/rename_output.py", "--output-dir", "output", "--filename-prefix", prefix,
   "--context", "<CONTEXT>", "--output", "output/renamed.json"]

run_log_args =
  ["scripts/run_log_writer.py", "--tenant", tenant, "--doc-type", resolved_doc_type,
   "--variant", to_string(resolved_version), "--run-id", run_id,
   "--renamed", "output/renamed.json", "--context", "<CONTEXT>",
   "--log-file", "data/run_log.json"]

upload_phase =
  if deliver_upload? do
    upload_args =
      ["scripts/upload_output.py", "--tenant", tenant, "--files"] ++
        renamed_files ++ ["--output", "output/uploaded.json"]

    """
    PHASE E — Upload the renamed outputs to Drive.
      E1. run_command  command: "python3"  args: #{inspect(upload_args)}
          Writes output/uploaded.json (array of {filename, drive_file_id, drive_url}).
    """
  else
    """
    PHASE E — (skipped: DRIVE_DOCBUILDER_ID not set, so there is no upload target).
    """
  end

email_phase =
  cond do
    deliver_email? and deliver_upload? ->
      """
      PHASE F — Send the review email.
        F1. Read output/uploaded.json (the array PHASE E wrote) and pass its exact
            contents as the --drive-links value:
              run_command  command: "python3"
                           args: ["scripts/email_send_review.py", "--context", "<CONTEXT>", "--drive-links", "<UPLOADED_JSON>"]
            Replace "<CONTEXT>" with the EXACT context JSON below, and "<UPLOADED_JSON>"
            with the exact stdout/array contents of output/uploaded.json:
              #{context_json}
      """

    deliver_email? ->
      """
      PHASE F — Send the review email (no Drive links — upload was skipped).
        F1. run_command  command: "python3"
                         args: ["scripts/email_send_review.py", "--context", "<CONTEXT>"]
            Replace "<CONTEXT>" with the EXACT context JSON below, one arg, verbatim:
              #{context_json}
      """

    true ->
      """
      PHASE F — (skipped: DOCBUILDER_REVIEW_EMAIL not set).
      """
  end

system_prompt = """
You are the docbuilder orchestrator. Run the document-generation + delivery pipeline by
executing the steps below in order, then report the output files and any Drive links.

Configuration resolved at startup:
  Tenant:          #{tenant}
  Context source:  #{context_source}
  Resolved target: #{resolved_doc_type} / #{resolved_version}  (output prefix #{prefix})
  Template bundle: #{bundle_dir}
  Data sources:    #{Enum.map_join(sources, ", ", & &1.key)}
  Output formats:  #{Enum.join(output_formats, ", ")}
  Delivery:        upload=#{deliver_upload?}  email=#{deliver_email?}

---

PHASE 0 — Select the template, then fetch its bundle.
  0.1 List the tenant's catalogue:
        run_command  command: "python3"  args: ["scripts/list_templates.py", "--tenant", "#{tenant}"]
  0.2 From that catalogue and the context, choose the best doc_type and variant.
      State your choice as JSON (this is your selection of record):
        {"doc_type": "...", "variant": "...", "rationale": "..."}
  0.3 Fetch the chosen template bundle (resolved target #{resolved_doc_type}/#{resolved_version}):
        run_command  command: "python3"
                     args: ["scripts/fetch_template.py", "--tenant", "#{tenant}", "--doc-type", "#{resolved_doc_type}", "--version", "#{resolved_version}", "--output", "output/template_cache_path.txt"]
        Writes the bundle path to that file (#{bundle_dir}).

PHASE A — Fetch each data source and save its raw JSON.
#{fetch_steps}
  Fetch every source listed; do not skip any.

PHASE B — Compute the doc spec from the bundle template and ALL raw source files.
  B1. run_command  command: "python3"  args: #{inspect(compute_args)}
      Writes output/pipeline_spec.json and prints only that path.

PHASE C — Render each output format from the saved doc spec.
#{render_steps}

PHASE D — Rename the rendered outputs to the deliverable convention, then log the run.
  D1. run_command  command: "python3"  args: #{inspect(rename_args)}
      Replace the "<CONTEXT>" element with this EXACT JSON, one arg, verbatim:
        #{context_json}
      Writes output/renamed.json (array of {original, renamed}).
  D2. Append this run to the run log (m3 "same as last month" context builder):
        run_command  command: "python3"  args: #{inspect(run_log_args)}
        Replace the "<CONTEXT>" element with this EXACT JSON, one arg, verbatim:
          #{context_json}
        Writes data/run_log.json and prints only that path.

#{upload_phase}
#{email_phase}
PHASE G — Report: the renamed output files, and (if uploaded) the Drive links.

---

Rules:
- All paths are relative to the sandbox root; overlay_base_dir is nil (files persist).
- Execute the commands exactly as written. Do not add, drop, or reorder arguments.
- If any script returns exit code 1, report its stderr and stop. Do not retry or
  investigate manually.
- Each `--output FILE` call writes its result directly to that file and prints ONLY the
  path. Do NOT re-run a script without `--output` to view its content, and do NOT write
  any helper/scratch script — use the file the script already wrote and proceed.
- Template selection (0.2): parse/produce the JSON exactly; do not add fields. If you
  cannot select, report why and stop.
- Do not construct or modify JSON yourself beyond the selection in 0.2. The scripts
  produce all data.
- Do not pass "python3" inside the args array — it is already the command field.
"""

%Aetheris.RunConfig{
  run_id:           run_id,
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Docbuilder Orchestrator",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        40,
  context_strategy: :full,
  tools:            ["run_command"],
  system_prompt:    system_prompt,
  user_prompt:      "Run the document generation and delivery pipeline."
}
