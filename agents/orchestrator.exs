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
    {
      "id": "step-1",
      "agent": "relative/path/to/agent.exs",
      "description": "What this step does",
      "context": "One sentence with specific runtime details — what data, which month, where output goes"
    }
  ],
  "params": {
    "PAYSLIP_MONTH": "2026-04"
  }
}

Agent paths must be relative to the aetheris-agents/ root and must match
exactly the file paths listed in the capability matrix.

context is a single sentence that makes the step concrete for the user to
verify. Use the request params and your knowledge of the agent to be specific.
If there is nothing specific to add, omit the field or use an empty string.

params is a flat map of env var names to values extracted from the request.
Include only params that are directly relevant to the steps.
If no params are needed, return "params": {}.

Known params:
- PAYSLIP_MONTH: month in YYYY-MM format, extracted from the request
  (e.g. "april 2026" → "2026-04", "may 2026" → "2026-05")
- PAYSLIP_EMPLOYEE_ID: employee ID when the request targets a single employee
  (e.g. "for BTL_01" → "BTL_01", "employee BTL_999" → "BTL_999")
  Omit this param when the request is for all employees.

## Rules

- Only include agents that are directly relevant to the request
- Order steps logically — dependencies before dependents
- Use at most 5 steps
- If the request cannot be fulfilled by any available agent, return { "steps": [], "params": {} }
- REQUIRED: whenever email/agents/email_orchestrator.exs is in the plan, you MUST include drive/agents/drive_upload_orchestrator.exs as the immediately preceding step — payslips must be archived in Drive before distribution

## Examples

Request: "email payslips to all employees for May 2026"
{
  "steps": [
    {
      "id": "step-1",
      "agent": "drive/agents/drive_download_orchestrator.exs",
      "description": "Download payroll CSV from Google Drive",
      "context": "Downloads payroll.csv from the configured Google Drive folder to payslip/data/"
    },
    {
      "id": "step-2",
      "agent": "payslip/agents/payslip_orchestrator.exs",
      "description": "Compute and generate payslips for May 2026",
      "context": "Reads payslip/data/payroll.csv, generates PDFs to payslip/output/{employee_id}/2026-05-Payslip.pdf"
    },
    {
      "id": "step-3",
      "agent": "drive/agents/drive_upload_orchestrator.exs",
      "description": "Upload payslip PDFs to Google Drive",
      "context": "Uploads payslip/output/ PDFs to the May 2026 period folder in Drive"
    },
    {
      "id": "step-4",
      "agent": "email/agents/email_orchestrator.exs",
      "description": "Email payslips to all employees",
      "context": "Sends May 2026 payslip PDFs to the configured delivery address"
    }
  ],
  "params": { "PAYSLIP_MONTH": "2026-05" }
}

Request: "email may 2026 payslip for BTL_01"
{
  "steps": [
    {
      "id": "step-1",
      "agent": "drive/agents/drive_download_orchestrator.exs",
      "description": "Download payroll CSV from Google Drive",
      "context": "Downloads payroll.csv from the configured Google Drive folder to payslip/data/"
    },
    {
      "id": "step-2",
      "agent": "payslip/agents/payslip_orchestrator.exs",
      "description": "Compute and generate payslip for BTL_01 for May 2026",
      "context": "Reads payslip/data/payroll.csv, generates PDF to payslip/output/BTL_01/2026-05-Payslip.pdf"
    },
    {
      "id": "step-3",
      "agent": "drive/agents/drive_upload_orchestrator.exs",
      "description": "Upload payslip PDF to Google Drive",
      "context": "Uploads payslip/output/BTL_01/ PDF to the May 2026 period folder in Drive"
    },
    {
      "id": "step-4",
      "agent": "email/agents/email_orchestrator.exs",
      "description": "Email payslip to BTL_01",
      "context": "Sends May 2026 payslip PDF for BTL_01 to the configured delivery address"
    }
  ],
  "params": { "PAYSLIP_MONTH": "2026-05", "PAYSLIP_EMPLOYEE_ID": "BTL_01" }
}

Request: "scan the corpus for new files"
{
  "steps": [
    {
      "id": "step-1",
      "agent": "provenance/agents/scan_orchestrator.exs",
      "description": "Scan NAS archive and update corpus inventory",
      "context": "Walks the NAS archive path, hashes new files, and updates the corpus DuckDB inventory"
    }
  ],
  "params": {}
}

Request: "classify unclassified documents"
{
  "steps": [
    {
      "id": "step-1",
      "agent": "provenance/agents/classification_orchestrator.exs",
      "description": "Classify unclassified corpus documents",
      "context": "Runs LLM classification on files with status = unclassified and writes proposed labels"
    }
  ],
  "params": {}
}

Request: "enroll students from CSV"
{
  "steps": [
    {
      "id": "step-1",
      "agent": "api/tenant/agents/at1cmd.exs",
      "description": "Submit student enrollment intent via TAP protocol",
      "context": "Reads the CSV, submits each row as a TAP enrollment intent to the gateway"
    }
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

get_step_result = fn run_id ->
  db_path   = System.get_env("AETHERIS_DB_PATH") || raise "AETHERIS_DB_PATH not set"
  traj_path = Path.join([
    db_path |> Path.dirname() |> Path.dirname(),
    "priv", "runs", run_id, "trajectory.json"
  ])
  case File.read(traj_path) do
    {:ok, raw} ->
      events = raw |> Jason.decode!() |> Map.get("events", [])
      failed = Enum.find(events, fn e ->
        e["type"] == "tool_result" &&
        case Jason.decode(e["payload"]["output"] || "") do
          {:ok, output} -> is_integer(output["exit_code"]) && output["exit_code"] != 0
          _             -> false
        end
      end)
      case failed do
        nil -> :ok
        e ->
          stderr = case Jason.decode(e["payload"]["output"] || "") do
            {:ok, output} -> output["stderr"] || "Step failed"
            _             -> "Step failed"
          end
          {:error, String.trim(stderr)}
      end
    _ ->
      :ok
  end
end

Enum.reduce_while(steps, :ok, fn step, _acc ->
  step_id    = step["id"]
  agent_file = step["agent"]
  agent_path = Path.join(agents_path, agent_file)

  IO.puts(Jason.encode!(%{type: "step_started", step_id: step_id}))

  original = Enum.map(params, fn {k, _} -> {k, System.get_env(k)} end)
  Enum.each(params, fn {k, v} -> System.put_env(k, v) end)

  await_with_timeout = fn run_id ->
    task = Task.async(fn -> RunHelpers.await_run(run_id, verbose: false) end)
    case Task.yield(task, 300_000) do
      {:ok, {:ok, outcome}}   -> {:ok, outcome}
      {:ok, {:error, reason}} -> {:error, reason}
      nil ->
        Task.shutdown(task, :brutal_kill)
        {:error, "step timed out after 5 minutes"}
    end
  end

  result =
    with {:ok, config}  <- RunHelpers.load_agent_file(agent_path),
         {:ok, run_id}  <- Aetheris.start_run(config),
         {:ok, outcome} <- await_with_timeout.(run_id) do
      get_step_result.(outcome.run_id)
    else
      {:error, reason} -> {:error, inspect(reason)}
    end

  Enum.each(original, fn
    {k, nil} -> System.delete_env(k)
    {k, v}   -> System.put_env(k, v)
  end)

  case result do
    :ok ->
      IO.puts(Jason.encode!(%{type: "step_complete", step_id: step_id, status: "done"}))
      {:cont, :ok}
    {:error, reason} ->
      IO.puts(Jason.encode!(%{type: "step_complete", step_id: step_id,
                               status: "failed", error: reason}))
      {:halt, :failed}
  end
end)

IO.puts(Jason.encode!(%{type: "orchestration_complete", status: "done"}))
