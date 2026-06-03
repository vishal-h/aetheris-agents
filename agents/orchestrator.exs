# orchestrator.exs
# Real LLM-driven orchestrator for the Rig p3 pipeline.
# Protocol: newline-delimited JSON on stdout / stdin.
# See docs/rig/milestones/p3/protocol.md

alias Aetheris.CLI.Commands.RunHelpers

# ── Configuration ─────────────────────────────────────────────────────────────

request     = System.get_env("ORCHESTRATOR_REQUEST") || "default request"
agents_path = System.get_env("AETHERIS_AGENTS_PATH")  ||
                raise "AETHERIS_AGENTS_PATH not set"

model    = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
_provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

matrix_path = Path.join(agents_path, "docs/capability-matrix.md")
matrix      = File.read!(matrix_path)

# ── Ensure harness supervision tree is running ────────────────────────────────

:ok = RunHelpers.ensure_started()

# ── System prompt ─────────────────────────────────────────────────────────────

system_prompt = """
You are an orchestration planner for the Aetheris agent harness.

Given a user request and the capability matrix below, produce a JSON execution
plan — a sequence of agent files to run in order.

## Capability Matrix

#{matrix}

## Output format

Respond with a JSON object ONLY — no preamble, no explanation, no markdown.

{
  "steps": [
    { "id": "step-1", "agent": "relative/path/to/agent.exs", "description": "What this step does" },
    { "id": "step-2", "agent": "relative/path/to/agent.exs", "description": "What this step does" }
  ],
  "params": {
    "PAYSLIP_MONTH": "2026-04"
  }
}

Agent paths must be relative to the aetheris-agents/ root and must match
exactly the file paths listed in the capability matrix.

params is a flat map of env var names to values extracted from the request.
Include only params that are directly relevant to the steps.
If no params are needed, return "params": {}.

Known params:
- PAYSLIP_MONTH: month in YYYY-MM format, extracted from the request
  (e.g. "april 2026" → "2026-04", "may 2026" → "2026-05")

## Rules

- Only include agents that are directly relevant to the request
- Order steps logically — dependencies before dependents
- Use at most 5 steps
- If the request cannot be fulfilled by any available agent, return { "steps": [], "params": {} }

## Examples

Request: "email payslips to all employees for May 2026"
{
  "steps": [
    { "id": "step-1", "agent": "drive/agents/drive_orchestrator.exs",    "description": "Download payroll CSV from Google Drive" },
    { "id": "step-2", "agent": "payslip/agents/payslip_orchestrator.exs", "description": "Compute and generate payslips for May 2026" },
    { "id": "step-3", "agent": "email/agents/email_orchestrator.exs",    "description": "Email payslips to all employees" }
  ],
  "params": { "PAYSLIP_MONTH": "2026-05" }
}

Request: "scan the corpus for new files"
{
  "steps": [
    { "id": "step-1", "agent": "provenance/agents/scan_orchestrator.exs", "description": "Scan NAS archive and update corpus inventory" }
  ],
  "params": {}
}

Request: "classify unclassified documents"
{
  "steps": [
    { "id": "step-1", "agent": "provenance/agents/classification_orchestrator.exs", "description": "Classify unclassified corpus documents" }
  ],
  "params": {}
}

Request: "enroll students from CSV"
{
  "steps": [
    { "id": "step-1", "agent": "api/tenant/agents/at1cmd.exs", "description": "Submit student enrollment intent via TAP protocol" }
  ],
  "params": {}
}
"""

# ── LLM call — planning ───────────────────────────────────────────────────────

{:ok, _} = Application.ensure_all_started(:req)

headers = [
  {"x-api-key",         System.get_env("ANTHROPIC_API_KEY") || raise("ANTHROPIC_API_KEY not set")},
  {"anthropic-version", "2023-06-01"},
  {"content-type",      "application/json"}
]

body = Jason.encode!(%{
  model:      model,
  max_tokens: 1024,
  system:     system_prompt,
  messages:   [%{role: "user", content: request}]
})

response = Req.post!("https://api.anthropic.com/v1/messages",
  headers: headers,
  body:    body
)

raw_text =
  response.body
  |> Map.get("content", [])
  |> Enum.find(%{}, fn b -> Map.get(b, "type") == "text" end)
  |> Map.get("text", "{\"steps\":[]}")

plan_data =
  raw_text
  |> String.trim()
  |> String.replace(~r/^```(?:json)?\n?/, "")
  |> String.replace(~r/\n?```$/, "")
  |> Jason.decode!()

steps  = Map.get(plan_data, "steps",  [])
params = Map.get(plan_data, "params", %{})

# ── Emit plan → wait for approval ────────────────────────────────────────────

IO.puts(Jason.encode!(%{type: "plan", request: request, steps: steps, params: params}))

approval = IO.gets("") |> String.trim() |> Jason.decode!()

unless approval["approved"] do
  IO.puts(Jason.encode!(%{type: "orchestration_cancelled"}))
  System.halt(0)
end

# ── Execute steps ─────────────────────────────────────────────────────────────

Enum.each(steps, fn step ->
  step_id    = step["id"]
  agent_file = step["agent"]
  agent_path = Path.join(agents_path, agent_file)

  IO.puts(Jason.encode!(%{type: "step_started", step_id: step_id}))

  original = Enum.map(params, fn {k, _} -> {k, System.get_env(k)} end)
  Enum.each(params, fn {k, v} -> System.put_env(k, v) end)

  result =
    with {:ok, config}  <- RunHelpers.load_agent_file(agent_path),
         {:ok, run_id}  <- Aetheris.start_run(config),
         {:ok, _result} <- RunHelpers.await_run(run_id, verbose: false) do
      :ok
    else
      {:error, reason} -> {:error, reason}
    end

  Enum.each(original, fn
    {k, nil} -> System.delete_env(k)
    {k, v}   -> System.put_env(k, v)
  end)

  status = if result == :ok, do: "done", else: "failed"
  IO.puts(Jason.encode!(%{type: "step_complete", step_id: step_id, status: status}))
end)

IO.puts(Jason.encode!(%{type: "orchestration_complete", status: "done"}))
