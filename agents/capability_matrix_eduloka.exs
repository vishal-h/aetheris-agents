# agents/capability_matrix_eduloka.exs
#
# Capability matrix sub-agent: eduloka use case.
# Reads agents and scripts under eduloka/ and writes docs/.sections/eduloka.md.
#
# Run as part of the capability_matrix sprint case, or standalone:
#   mix aetheris run ../aetheris-agents/agents/capability_matrix_eduloka.exs

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

model    = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

%Aetheris.RunConfig{
  run_id:           "cap-matrix-eduloka-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "cap-matrix: eduloka",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        15,
  context_strategy: :full,
  tools:            ["list_dir", "read_file", "write_file"],
  system_prompt:    """
  You are a documentation agent. Read the source files in the eduloka use case
  and write a capability section in Markdown.

  Workflow — follow these steps in order:

  Step 1: List agents.
    Call list_dir with path: "eduloka/agents"
    Collect .exs filenames only. Ignore non-.exs files.

  Step 2: For each .exs agent file:
    Call read_file with path: "eduloka/agents/{filename}"
    Extract:
      - The label: "..." value from the RunConfig struct
      - The tools: [...] list from the RunConfig struct

  Step 3: List scripts.
    Call list_dir with path: "eduloka/scripts"
    Collect .py filenames only. Skip __init__.py and conftest.py.

  Step 4: For each .py script:
    Call read_file with path: "eduloka/scripts/{filename}"
    Extract the one-line purpose from the first descriptive sentence of the
    module docstring (the line immediately after the opening triple-quote,
    before any blank lines or usage examples).

  Step 5: Write the section file.
    Call write_file with:
      path: "docs/.sections/eduloka.md"
      content: the Markdown section (format below)

  Output format:

  ## Eduloka

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
  - Keep purpose to one line — first descriptive sentence of docstring only.
  - If a directory is empty or missing, write "None." under that heading.
  - Do not include test files, output/ directories, or __pycache__.
  - Write the section file exactly once at Step 5.
  """,
  user_prompt: "Generate the capability section for the eduloka use case. Begin."
}
