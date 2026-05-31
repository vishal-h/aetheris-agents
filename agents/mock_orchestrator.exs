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
