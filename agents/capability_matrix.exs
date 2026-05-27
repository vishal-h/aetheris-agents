# agents/capability_matrix.exs
#
# Dog-fooding agent: reads the aetheris-agents repo and generates a capability
# matrix documenting all use cases, agents, tools, and scripts.
#
# Two-step process:
#
#   Step 1 — run the sub-agents orb (all use cases in parallel):
#     mix aetheris run ../aetheris-agents/agents/capability_matrix.exs
#
#   Step 2 — run the orchestrator after all sub-agents complete:
#     mix aetheris run ../aetheris-agents/agents/capability_matrix_assemble.exs
#
# Output: docs/capability-matrix.md
# Intermediate: docs/.sections/{use_case}.md (one per sub-agent)
#
# Re-run both steps whenever a new use case, agent, or script is added.

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

sub_agent_prompt = fn use_case, side ->
  {agents_dir, scripts_dir, section_title, note} =
    case {use_case, side} do
      {"api", "tenant"} ->
        {"api/tenant/agents", "api/tenant/scripts",
         "api/ — TAP Protocol — Tenant side",
         "Tenant-side agents: at1cmd (dispatcher), at1qry (collector)."}

      {"api", "gateway"} ->
        {"api/gateway/agents", "api/gateway/scripts",
         "api/ — TAP Protocol — Gateway side",
         "Gateway-side agents: cot1 (TAP gateway). Connects to ct.stu API."}

      {uc, _} ->
        {"#{uc}/agents", "#{uc}/scripts",
         String.capitalize(uc),
         ""}
    end

  section_file =
    case side do
      "" -> "docs/.sections/#{use_case}.md"
      s  -> "docs/.sections/#{use_case}_#{s}.md"
    end

  """
  You are a documentation agent. Read the source files in this use case and
  write a capability section in Markdown. #{note}

  Workflow — follow these steps in order:

  Step 1: List agents.
    Call list_dir with path: "#{agents_dir}"
    Collect .exs filenames only. Ignore non-.exs files.

  Step 2: For each .exs agent file:
    Call read_file with path: "#{agents_dir}/{filename}"
    Extract:
      - The label: "..." value (agent's human name)
      - The tools: [...] list
      - If OrbConfig: extract tools from each agent_config entry separately,
        labelling each by its label field.

  Step 3: List scripts.
    Call list_dir with path: "#{scripts_dir}"
    Collect .py filenames only. Skip __init__.py and conftest.py.

  Step 4: For each .py script:
    Call read_file with path: "#{scripts_dir}/{filename}"
    Read the file and extract the one-line purpose from the opening docstring
    (the line immediately after the opening triple-quote, before any blank
    lines or argument descriptions). Example:
      \"\"\"parse_csv.py <csv_path>\\n\\nReads payroll CSV...\"\"\"
      → purpose is "Reads payroll CSV..."
      (skip the usage line, use the first descriptive sentence)

  Step 5: Write the section file.
    Call write_file with:
      path: "#{section_file}"
      content: the Markdown section (format below)

  Output format:

  ## #{section_title}

  ### Agents

  | Agent file | Label | Tools |
  |------------|-------|-------|
  | {file}.exs | {label} | `{tool1}`, `{tool2}` |

  ### Scripts

  | Script | Purpose |
  |--------|---------|
  | {script}.py | {one-line purpose} |

  Rules:
  - One row per agent file. For OrbConfig, expand to one row per agent_config.
  - Keep purpose to one line — first descriptive sentence of docstring only.
  - If a directory is empty or missing, write "None." under that heading.
  - Do not include test files, output/ directories, or __pycache__.
  - Write the section file once at Step 5.
  """
end

%Aetheris.OrbConfig{
  orb_id: "cap-matrix-#{Aetheris.ID.generate()}",
  agent_configs: [
    %Aetheris.RunConfig{
      run_id:           "cap-matrix-#{Aetheris.ID.generate()}-payslip",
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "cap-matrix: payslip",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        15,
      context_strategy: :full,
      tools:            ["list_dir", "read_file", "write_file"],
      system_prompt:    sub_agent_prompt.("payslip", ""),
      user_prompt:      "Generate the capability section for the payslip use case. Begin."
    },
    %Aetheris.RunConfig{
      run_id:           "cap-matrix-#{Aetheris.ID.generate()}-drive",
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "cap-matrix: drive",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        15,
      context_strategy: :full,
      tools:            ["list_dir", "read_file", "write_file"],
      system_prompt:    sub_agent_prompt.("drive", ""),
      user_prompt:      "Generate the capability section for the drive use case. Begin."
    },
    %Aetheris.RunConfig{
      run_id:           "cap-matrix-#{Aetheris.ID.generate()}-email",
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "cap-matrix: email",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        15,
      context_strategy: :full,
      tools:            ["list_dir", "read_file", "write_file"],
      system_prompt:    sub_agent_prompt.("email", ""),
      user_prompt:      "Generate the capability section for the email use case. Begin."
    },
    %Aetheris.RunConfig{
      run_id:           "cap-matrix-#{Aetheris.ID.generate()}-api-tenant",
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "cap-matrix: api/tenant",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        15,
      context_strategy: :full,
      tools:            ["list_dir", "read_file", "write_file"],
      system_prompt:    sub_agent_prompt.("api", "tenant"),
      user_prompt:      "Generate the capability section for the api/tenant side. Begin."
    },
    %Aetheris.RunConfig{
      run_id:           "cap-matrix-#{Aetheris.ID.generate()}-api-gateway",
      mode:             :record,
      provider:         "anthropic",
      model:            "claude-haiku-4-5-20251001",
      label:            "cap-matrix: api/gateway",
      sandbox_path:     agent_root,
      overlay_base_dir: nil,
      max_steps:        15,
      context_strategy: :full,
      tools:            ["list_dir", "read_file", "write_file"],
      system_prompt:    sub_agent_prompt.("api", "gateway"),
      user_prompt:      "Generate the capability section for the api/gateway side. Begin."
    }
  ]
}
