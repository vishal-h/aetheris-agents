# rig/p3: Mock script

## Context

The real orchestrator agent does not exist yet. This issue creates a
deterministic mock script that implements the full p3 protocol so the
Rig UI can be built and tested end-to-end.

## What to build

### `aetheris-agents/agents/mock_orchestrator.exs`

```elixir
# mock_orchestrator.exs
# Deterministic mock for the p3 Rig orchestrator pipeline.
# Protocol: newline-delimited JSON on stdout / stdin.
# See docs/rig/milestones/p3/protocol.md

request = System.get_env("ORCHESTRATOR_REQUEST") || "default request"

# Simulate planning delay
Process.sleep(2000)

steps = [
  %{id: "step-1", agent: "scan_agent.exs",  description: "Scan corpus for relevant files"},
  %{id: "step-2", agent: "report_agent.exs", description: "Generate summary report"},
]

IO.puts(Jason.encode!(%{type: "plan", request: request, steps: steps}))

# Wait for approval
approval = IO.gets("") |> String.trim() |> Jason.decode!()

if approval["approved"] do
  Enum.each(steps, fn step ->
    Process.sleep(500)
    IO.puts(Jason.encode!(%{type: "step_started",  step_id: step.id}))
    Process.sleep(1500)
    IO.puts(Jason.encode!(%{type: "step_complete", step_id: step.id, status: "done"}))
  end)
  IO.puts(Jason.encode!(%{type: "orchestration_complete", status: "done"}))
else
  IO.puts(Jason.encode!(%{type: "orchestration_cancelled"}))
end
```

### Manual test

From the `aetheris/` directory:

```bash
# Approve path
(sleep 3; echo '{"type":"approval","approved":true}') \
  | ORCHESTRATOR_REQUEST="email payslips" \
    mix run ../aetheris-agents/agents/mock_orchestrator.exs
```

```bash
# Reject path
(sleep 3; echo '{"type":"approval","approved":false}') \
  | ORCHESTRATOR_REQUEST="test" \
    mix run ../aetheris-agents/agents/mock_orchestrator.exs
```

Expected stdout (approve path):
```
{"type":"plan","request":"email payslips","steps":[...]}
{"type":"step_started","step_id":"step-1"}
{"type":"step_complete","step_id":"step-1","status":"done"}
{"type":"step_started","step_id":"step-2"}
{"type":"step_complete","step_id":"step-2","status":"done"}
{"type":"orchestration_complete","status":"done"}
```

Expected stdout (reject path):
```
{"type":"plan","request":"test","steps":[...]}
{"type":"orchestration_cancelled"}
```

## Acceptance criteria

- [ ] Script at `aetheris-agents/agents/mock_orchestrator.exs`
- [ ] Manual test (approve path) produces the correct JSON sequence
- [ ] Manual test (reject path) produces `orchestration_cancelled` then exits
- [ ] `ORCHESTRATOR_REQUEST` env var sets the `request` field in the plan
- [ ] `mix test` in `aetheris/` continues to pass (script has no test side-effects)
- [ ] Follows `protocol.md` exactly — no extra fields, no deviation

## Notes

**Why `ORCHESTRATOR_REQUEST` env var and not a CLI arg?** `mix run` treats
arguments after the filename as Mix options, not script arguments.
`System.argv()` is unreliable in this context. An env var is unambiguous.

**Why `IO.gets("")`?** In Elixir, `IO.gets/1` reads one line from stdin
including the newline. `String.trim/1` removes it before JSON decoding.
The argument is the prompt string (empty here — we don't want a prompt
printed to stdout).
