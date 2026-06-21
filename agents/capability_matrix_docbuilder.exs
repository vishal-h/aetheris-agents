# agents/capability_matrix_docbuilder.exs
#
# Capability matrix sub-agent: docbuilder use case.
# Reads agents and scripts under docbuilder/ and writes docs/.sections/docbuilder.md.
#
# Run as part of the capability_matrix sprint case, or standalone:
#   mix aetheris run ../aetheris-agents/agents/capability_matrix_docbuilder.exs

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

model    = System.get_env("AETHERIS_MODEL") || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "cap-matrix-docbuilder-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "cap-matrix: docbuilder",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        50,
  context_strategy: :full,
  tools:            ["list_dir", "read_file", "write_file"],
  system_prompt:    """
  You are a documentation agent. Read the source files in this use case and
  write a capability section in Markdown.

  Workflow — follow these steps in order:

  Step 1: List agents.
    Call list_dir with path: "docbuilder/agents"
    Collect .exs filenames only. Ignore non-.exs files.

  Step 2: For each .exs agent file:
    Call read_file with path: "docbuilder/agents/{filename}"
    Extract:
      - The label: "..." value (agent's human name)
      - The tools: [...] list

  Step 3: List scripts.
    Call list_dir with path: "docbuilder/scripts"
    Collect .py filenames. Skip __init__.py and conftest.py.

  Step 4: For each .py script:
    Call read_file with path: "docbuilder/scripts/{filename}"
    Read the file and infer the one-line purpose from the function names and
    docstring if present, or from the opening imports and main() logic if not.
    Summarise in one sentence what the script does.

  Step 5: Write the section file.
    Call write_file with:
      path: "docs/.sections/docbuilder.md"
      content: the Markdown section (format below)

  Output format:

  ## Docbuilder

  ### Agents

  | Agent file | Label | Tools |
  |------------|-------|-------|
  | {file}.exs | {label} | `{tool1}`, `{tool2}` |

  ### Scripts

  | Script | Purpose |
  |--------|---------|
  | {script}.py | {one-line purpose} |

  Rules:
  - One row per agent file.
  - Keep purpose to one line — first descriptive sentence only.
  - If a directory is empty or missing, write "None." under that heading.
  - Do not include test files, output/ directories, or __pycache__.
  - Write the section file once at Step 5.
  """,
  user_prompt: "Generate the capability section for the docbuilder use case. Begin."
}
