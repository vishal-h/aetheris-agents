# aetheris-agents: Real Orchestrator Agent

**File:** `agents/orchestrator.exs`
**Replaces:** `agents/mock_orchestrator.exs` (keep mock; change script path in Rig to switch)

---

## Context

The mock orchestrator always emits the same two placeholder steps regardless
of the request. This ticket replaces it with a real LLM-driven orchestrator
that:

1. Reads the capability matrix to understand available agents
2. Uses few-shot structured generation to plan a sequence of real agents
3. Emits the plan and waits for Rig approval via stdin
4. Executes each agent programmatically using the harness internal API
5. Streams step events back to Rig via stdout throughout

The protocol (newline-delimited JSON over stdin/stdout) is unchanged —
`docs/rig/milestones/p3/protocol.md` remains authoritative.

---

## Internal API

The orchestrator uses the harness CLI helpers directly — no shell execution,
no new VM per sub-agent:

```elixir
alias Aetheris.CLI.Commands.RunHelpers

# Load a .exs agent file → %RunConfig{} or %OrbConfig{}
{:ok, config} = RunHelpers.load_agent_file(agent_path)

# Start the run → run_id
{:ok, run_id} = Aetheris.start_run(config)

# Block until terminal status
{:ok, result} = RunHelpers.await_run(run_id, verbose: false)
```

`RunHelpers.ensure_started()` must be called once before any `start_run`
call — it ensures the harness supervision tree is running. Call it once at
the top of the script.

---

## Agent file

### `agents/orchestrator.exs`

```elixir
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
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

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
  ]
}

Agent paths must be relative to the aetheris-agents/ root and must match
exactly the file paths listed in the capability matrix.

## Rules

- Only include agents that are directly relevant to the request
- Order steps logically — dependencies before dependents
- Use at most 5 steps
- If the request cannot be fulfilled by any available agent, return { "steps": [] }

## Examples

Request: "email payslips to all employees for May 2026"
{
  "steps": [
    { "id": "step-1", "agent": "drive/agents/drive_orchestrator.exs",   "description": "Download payroll CSV from Google Drive" },
    { "id": "step-2", "agent": "payslip/agents/payslip_orchestrator.exs", "description": "Compute and generate payslips for May 2026" },
    { "id": "step-3", "agent": "email/agents/email_orchestrator.exs",   "description": "Email payslips to all employees" }
  ]
}

Request: "scan the corpus for new files"
{
  "steps": [
    { "id": "step-1", "agent": "provenance/agents/scan_orchestrator.exs", "description": "Scan NAS archive and update corpus inventory" }
  ]
}

Request: "classify unclassified documents"
{
  "steps": [
    { "id": "step-1", "agent": "provenance/agents/classification_orchestrator.exs", "description": "Classify unclassified corpus documents" }
  ]
}

Request: "enroll students from CSV"
{
  "steps": [
    { "id": "step-1", "agent": "api/tenant/agents/at1cmd.exs", "description": "Submit student enrollment intent via TAP protocol" }
  ]
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
  |> Jason.decode!()

steps = Map.get(plan_data, "steps", [])

# ── Emit plan → wait for approval ────────────────────────────────────────────

IO.puts(Jason.encode!(%{type: "plan", request: request, steps: steps}))

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

  result =
    with {:ok, config}  <- RunHelpers.load_agent_file(agent_path),
         {:ok, run_id}  <- Aetheris.start_run(config),
         {:ok, _result} <- RunHelpers.await_run(run_id, verbose: false) do
      :ok
    else
      {:error, reason} -> {:error, reason}
    end

  status = if result == :ok, do: "done", else: "failed"
  IO.puts(Jason.encode!(%{type: "step_complete", step_id: step_id, status: status}))
end)

IO.puts(Jason.encode!(%{type: "orchestration_complete", status: "done"}))
```

---

## Switching Rig from mock to real

In `rig/src-tauri/src/commands/orchestrate.rs`, `orchestrate_start` builds
the script path:

```rust
// Currently (mock):
let script_path = format!("{}/agents/mock_orchestrator.exs", agents_path);

// Change to (real):
let script_path = format!("{}/agents/orchestrator.exs", agents_path);
```

Keep `mock_orchestrator.exs` — revert this line to switch back for testing.

---

## Few-shot examples rationale

The four examples in the system prompt cover the primary use cases and anchor
the LLM to valid agent paths:

| Request pattern | Agents involved |
|----------------|-----------------|
| Email payslips | drive → payslip → email (full pipeline) |
| Scan corpus | provenance/scan only |
| Classify documents | provenance/classification only |
| Enroll students | api/tenant (TAP protocol) |

These examples teach the model the path convention (`use-case/agents/file.exs`)
and the dependency ordering (drive before payslip before email).

---

## Context passing to sub-agents

Sub-agents are launched via `RunHelpers.load_agent_file` + `Aetheris.start_run`.
Their `system_prompt` and `user_prompt` are defined inside their `.exs` files
— the orchestrator does not modify them.

For the first version, sub-agents run with their default prompts. Context
passing (e.g. telling payslip_orchestrator which month to process) is deferred
— the user's request is visible in Rig and the sub-agent's own prompt handles
it. A future version can write context to the blackboard before spawning.

---

## Error handling

- LLM returns empty steps (`{ "steps": [] }`) → plan emitted with empty steps,
  user sees an empty plan in Rig, can cancel
- Agent file not found → `load_agent_file` returns `{:error, reason}` →
  step marked `failed`, orchestration continues to next step
- Sub-agent run fails → `await_run` returns `{:error, reason}` →
  step marked `failed`, orchestration continues
- `ANTHROPIC_API_KEY` not set → `raise` at startup → Rig shows error state

---

## Manual test

From `aetheris/`:

```bash
# Approve path
(sleep 10; echo '{"type":"approval","approved":true}') \
  | ORCHESTRATOR_REQUEST="scan the corpus for new files" \
    AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents \
    mix run ../aetheris-agents/agents/orchestrator.exs
```

Expected stdout:
```
{"type":"plan","request":"scan the corpus for new files","steps":[{"id":"step-1","agent":"provenance/agents/scan_orchestrator.exs","description":"..."}]}
{"type":"step_started","step_id":"step-1"}
{"type":"step_complete","step_id":"step-1","status":"done"}
{"type":"orchestration_complete","status":"done"}
```

The planning LLM call takes a few seconds — the `sleep 10` gives it time
before sending approval.

---

## Acceptance criteria

- [ ] `agents/orchestrator.exs` created
- [ ] LLM planning call produces valid JSON with real agent paths from the matrix
- [ ] Plan emitted to stdout, script blocks on stdin approval
- [ ] Approved: steps execute via `load_agent_file` + `start_run` + `await_run`
- [ ] Cancelled: `orchestration_cancelled` emitted, script exits
- [ ] Each step emits `step_started` then `step_complete` (done or failed)
- [ ] `orchestration_complete` emitted after all steps
- [ ] Manual test (scan corpus path) produces correct JSON sequence
- [ ] `orchestrate.rs` script path updated to `orchestrator.exs`
- [ ] Mock kept at `mock_orchestrator.exs` for regression testing

---

## Notes

**`RunHelpers.ensure_started/0`** must be called before any `start_run` call.
It ensures the harness supervision tree (Store, AgentSupervisor, etc.) is
running. Without it, `start_run` will fail with a supervision tree error.

**`Application.ensure_all_started(:req)`** — the HTTP client needs to be
started before the planning LLM call. Already done in other agents; include
it here.

**`System.halt(0)` vs normal exit** — after emitting `orchestration_cancelled`,
call `System.halt(0)` rather than relying on the script falling off the end.
The harness may hold open file handles that prevent a clean exit otherwise.

**Path relativity** — agent paths in the plan are relative to
`AETHERIS_AGENTS_PATH`. `Path.join(agents_path, agent_file)` resolves them
correctly. The matrix lists paths like `payslip/agents/payslip_orchestrator.exs`
— these join cleanly.

**LLM JSON reliability** — the system prompt instructs the model to return
JSON only. `Jason.decode!` will raise if the model adds preamble. For
robustness, wrap in a `try/rescue` and emit `{ "steps": [] }` on parse
failure. Add this in a follow-up if the plain version proves unreliable.
