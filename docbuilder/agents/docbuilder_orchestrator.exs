agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

tenant    = System.get_env("DOCBUILDER_TENANT")    || raise "DOCBUILDER_TENANT not set"
doc_type  = System.get_env("DOCBUILDER_DOC_TYPE")  || raise "DOCBUILDER_DOC_TYPE not set"
version   = System.get_env("DOCBUILDER_VERSION")   || raise "DOCBUILDER_VERSION not set"
data_path = System.get_env("DOCBUILDER_DATA_PATH") || raise "DOCBUILDER_DATA_PATH not set"

# Optional scalar-variable context for narrative-mode PDF. Treat unset/empty as "{}"
# so we never pass an empty --context (render_template.py would fail json.loads("")).
context =
  case System.get_env("DOCBUILDER_CONTEXT") do
    nil -> "{}"
    "" -> "{}"
    v -> v
  end

template_rel = "data/templates/#{tenant}/#{doc_type}_#{version}.json"
template_dir = "data/templates/#{tenant}"
filename     = "#{doc_type}_#{version}"

# Resolve the template at eval time so the system prompt can list concrete steps
# (sources to fetch, formats to render, which renderers get base files / narrative).
# Scripts decide content; this only decides which commands to run.
template = agent_root |> Path.join(template_rel) |> File.read!() |> Jason.decode!()

data_sources   = template["data_sources"] || []
output_formats = template["output_formats"] || []
narrative?     = is_map(template["narrative"])

# Base-file presence (per format), checked once at eval time.
xlsx_base_rel = "#{template_dir}/#{doc_type}_#{version}.xlsx"
docx_base_rel = "#{template_dir}/#{doc_type}_#{version}.docx"
xlsx_base? = File.exists?(Path.join(agent_root, xlsx_base_rel))
docx_base? = File.exists?(Path.join(agent_root, docx_base_rel))

# Source paths in the template are relative to the aetheris-agents repo root
# (e.g. "docbuilder/data/...") but run_command runs from the docbuilder sandbox,
# so strip the leading "docbuilder/". The "main" source honours DOCBUILDER_DATA_PATH.
sources =
  Enum.map(data_sources, fn s ->
    key = s["key"]
    path =
      if key == "main" do
        data_path
      else
        String.replace_prefix(s["path"] || "", "docbuilder/", "")
      end

    %{key: key, path: path, raw_file: "output/pipeline_raw_#{key}.json"}
  end)

raw_files = Enum.map(sources, & &1.raw_file)

model    = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

# --- build concrete step text -------------------------------------------------

fetch_steps =
  sources
  |> Enum.with_index(1)
  |> Enum.map(fn {s, i} ->
    """
      A#{i}. Fetch source "#{s.key}":
            run_command  command: "python3"
                         args: ["scripts/fetch_data.py", "--key", "#{s.key}", "#{s.path}"]
            Then save it: write_file  path: "#{s.raw_file}"  content: <exact stdout from the fetch>
    """
  end)
  |> Enum.join("\n")

compute_args =
  ["scripts/compute_doc.py", template_rel] ++ raw_files

render_args = fn fmt ->
  extra =
    case fmt do
      "xlsx" -> if xlsx_base?, do: ["--base-file", xlsx_base_rel], else: []
      "docx" -> if docx_base?, do: ["--base-file", docx_base_rel], else: []
      "pdf"  -> if narrative?, do: ["--template-dir", template_dir], else: []
      _ -> []
    end

  ["scripts/generate_#{fmt}.py", "--input", "output/pipeline_spec.json"] ++
    extra ++ ["--output-dir", "output", "--filename", filename]
end

render_steps =
  output_formats
  |> Enum.with_index(1)
  |> Enum.map(fn {fmt, i} ->
    if fmt == "pdf" and narrative? do
      # Single clean args array with a "<CONTEXT>" placeholder element; the real
      # JSON is given below it so the LLM substitutes it verbatim (no escaping).
      display_args =
        ["scripts/generate_#{fmt}.py", "--input", "output/pipeline_spec.json",
         "--template-dir", template_dir, "--context", "<CONTEXT>",
         "--output-dir", "output", "--filename", filename]

      """
        C#{i}. Render #{fmt} (narrative mode):
              run_command  command: "python3"
                           args: #{inspect(display_args)}
              Replace the "<CONTEXT>" placeholder element with this EXACT JSON string,
              passed as a single arg verbatim (do not escape or reformat it):
                #{context}
      """
    else
      """
        C#{i}. Render #{fmt}:
              run_command  command: "python3"
                           args: #{inspect(render_args.(fmt))}
      """
    end
  end)
  |> Enum.join("\n")

system_prompt = """
You are the docbuilder orchestrator. Run the document-generation pipeline by
executing the exact commands listed below in order, then report the output files.

Configuration resolved at startup:
  Tenant:        #{tenant}
  Doc type:      #{doc_type}
  Version:       #{version}
  Template path: #{template_rel}
  Output prefix: #{filename}
  Data sources:  #{Enum.map_join(sources, ", ", & &1.key)}
  Output formats: #{Enum.join(output_formats, ", ")}

---

PHASE A — Fetch each data source and save its raw JSON.
#{fetch_steps}
  Fetch every source listed, even if you suspect a sheet does not read it — the
  set of sources is fixed; do not skip any.

PHASE B — Compute the doc spec from the template and ALL raw source files.
  B1. run_command  command: "python3"
                   args: #{inspect(compute_args)}
      Capture the full stdout (a JSON object — the doc spec).
  B2. Save it:  write_file  path: "output/pipeline_spec.json"  content: <exact stdout from B1>

PHASE C — Render each output format from the saved doc spec.
#{render_steps}
  Record the output path each renderer prints to stdout.

PHASE D — Report the list of output files generated.

---

Rules:
- All paths are relative to the sandbox root; overlay_base_dir is nil (files persist).
- Execute the commands exactly as written. Do not add, drop, or reorder arguments.
- If any script returns exit code 1, report its stderr and stop. Do not retry or
  investigate manually.
- Do not construct or modify JSON yourself. The scripts produce all data; write_file
  must save the exact stdout string captured from the preceding command.
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
  max_steps:        30,
  context_strategy: :full,
  tools:            ["run_command", "write_file"],
  system_prompt:    system_prompt,
  user_prompt:      "Run the document generation pipeline."
}
