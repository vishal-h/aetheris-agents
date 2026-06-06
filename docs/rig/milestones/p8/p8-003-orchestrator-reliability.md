# rig/p8-003: Orchestrator reliability fixes

## Context

Three bugs found during end-to-end testing:

1. **False `done` status** — sub-agent runs that fail internally (tool
   exit_code != 0) are marked `done` because `await_run` returns
   `{:ok, ...}` whenever the run reaches `run_complete`. The orchestrator
   cannot distinguish between "finished successfully" and "finished after
   reporting an error".

2. **Step list disappears on Done/Cancelled** — the `done` and `cancelled`
   UI states replace the step list with a minimal message, losing the
   final step statuses.

3. **Fail-forward despite failures** — when a step fails (e.g. drive
   download folder missing), subsequent steps still execute. A failed
   drive step should stop the payslip and email steps from running since
   they depend on the downloaded CSV.

---

## Fix 1 — True failure detection in `agents/orchestrator.exs`

After `await_run` completes, read the sub-agent's trajectory file and
check for any `tool_result` event with a non-zero `exit_code`. If found,
treat the step as failed.

Define as a named anonymous function (`.exs` scripts don't support `defp`):

```elixir
has_tool_failure = fn run_id ->
  db_path   = System.get_env("AETHERIS_DB_PATH") || raise "AETHERIS_DB_PATH not set"
  traj_path = Path.join([
    db_path |> Path.dirname() |> Path.dirname(),
    "priv", "runs", run_id, "trajectory.json"
  ])
  case File.read(traj_path) do
    {:ok, raw} ->
      raw
      |> Jason.decode!()
      |> Map.get("events", [])
      |> Enum.any?(fn e ->
           e["type"] == "tool_result" &&
           is_integer(e["payload"]["exit_code"]) &&
           e["payload"]["exit_code"] != 0
         end)
    _ ->
      false
  end
end
```

Update the execution loop to use `Enum.reduce_while` and stop on failure:

```elixir
Enum.reduce_while(steps, :ok, fn step, _acc ->
  step_id    = step["id"]
  agent_file = step["agent"]
  agent_path = Path.join(agents_path, agent_file)

  IO.puts(Jason.encode!(%{type: "step_started", step_id: step_id}))

  original = Enum.map(params, fn {k, _} -> {k, System.get_env(k)} end)
  Enum.each(params, fn {k, v} -> System.put_env(k, v) end)

  result =
    with {:ok, config}  <- RunHelpers.load_agent_file(agent_path),
         {:ok, run_id}  <- Aetheris.start_run(config),
         {:ok, outcome} <- RunHelpers.await_run(run_id, verbose: false) do
      if has_tool_failure.(outcome.run_id) do
        {:error, :tool_failure}
      else
        :ok
      end
    else
      {:error, reason} -> {:error, reason}
    end

  Enum.each(original, fn
    {k, nil} -> System.delete_env(k)
    {k, v}   -> System.put_env(k, v)
  end)

  status = if result == :ok, do: "done", else: "failed"
  IO.puts(Jason.encode!(%{type: "step_complete", step_id: step_id, status: status}))

  case result do
    :ok         -> {:cont, :ok}
    {:error, _} -> {:halt, :failed}
  end
end)
```

`await_run` returns `{:ok, %{run_id: run_id, status: :done}}` — extract
`run_id` via pattern match on `outcome.run_id`.

---

## Fix 2 — Step list preserved in Done/Cancelled states

### `src/components/modules/orchestrator/OrchestratorView.tsx`

**`done` state:**

```tsx
{phase === 'done' && plan && (
  <div className="flex flex-col gap-4">
    <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
    <ParamsStrip params={params} />
    <div className="flex flex-col gap-2">
      {plan.steps.map((step, i) => (
        <StepCard
          key={step.id}
          step={step}
          index={i}
          configValues={configValues}
          status={stepStatuses[step.id] ?? 'done'}
        />
      ))}
    </div>
    <div className="flex flex-col items-center gap-3 pt-2">
      <CheckCircle2 className="h-8 w-8 text-green-600" />
      <p className="font-medium">Done</p>
      <Button variant="outline" onClick={reset}>Run another</Button>
    </div>
  </div>
)}
```

**`cancelled` state — with plan:**

```tsx
{phase === 'cancelled' && plan && (
  <div className="flex flex-col gap-4">
    <p className="text-sm text-muted-foreground">Request: {plan.request}</p>
    <ParamsStrip params={params} />
    <div className="flex flex-col gap-2">
      {plan.steps.map((step, i) => (
        <StepCard
          key={step.id}
          step={step}
          index={i}
          configValues={configValues}
          status={stepStatuses[step.id] ?? 'pending'}
        />
      ))}
    </div>
    <div className="flex flex-col items-center gap-3 pt-2">
      <p className="text-muted-foreground">Cancelled.</p>
      <Button variant="outline" onClick={reset}>Run another</Button>
    </div>
  </div>
)}
```

**`cancelled` state — no plan (cancelled before plan arrived):**

```tsx
{phase === 'cancelled' && !plan && (
  <div className="flex flex-col items-center gap-4">
    <p className="text-muted-foreground">Cancelled.</p>
    <Button variant="outline" onClick={reset}>Run another</Button>
  </div>
)}
```

---

## Acceptance criteria

- [ ] `orchestrator.exs` uses `Enum.reduce_while` — stops on first failed step
- [ ] `has_tool_failure` reads trajectory JSON, checks `tool_result` exit codes
- [ ] Failed step emits `step_complete` with `status: "failed"`
- [ ] Steps after a failed step are not executed
- [ ] `orchestration_complete` still emitted after the loop (even if some
      steps failed — the orchestration itself completed)
- [ ] `done` state shows frozen step list above the Done indicator
- [ ] `cancelled` state shows frozen step list when plan exists
- [ ] `cancelled` state shows minimal view when plan is null
- [ ] No TypeScript `any`
- [ ] `bun run build` exits 0

---

## Files to modify

- `agents/orchestrator.exs` — `has_tool_failure` fn, `Enum.reduce_while`,
  trajectory check after `await_run`
- `rig/src/components/modules/orchestrator/OrchestratorView.tsx` — `done`
  and `cancelled` states show step list

---

## Notes

**`await_run` returns `outcome.run_id`.** The spec for `await_run` is
`{:ok, %{run_id: String.t(), status: :done}}`. Pattern match the result
as `{:ok, outcome}` then use `outcome.run_id` to locate the trajectory.

**Trajectory path derivation.** Same pattern as `trajectory.rs`:
`AETHERIS_DB_PATH` → `Path.dirname` (priv/) → `Path.dirname` (aetheris/)
→ join `priv/runs/{run_id}/trajectory.json`.

**`Enum.reduce_while` accumulator.** The accumulator is `:ok` initially.
`{:cont, :ok}` continues; `{:halt, :failed}` stops. The return value of
`reduce_while` is unused — the side effects (IO.puts) are what matter.

**`orchestration_complete` always emitted.** Even when steps fail and the
loop halts early, emit `orchestration_complete` so Rig transitions to
`done` and the user sees the final state. The step statuses (some `failed`)
tell the story.

**StepCard default status in `done` state.** Use `stepStatuses[step.id] ?? 'done'`
as the fallback — steps that completed show their real status; steps that
never ran (halted loop) default to `done` rather than `pending`.

**Steps after a halted step.** When `reduce_while` halts after step 1,
steps 2 and 3 never emit `step_started` or `step_complete`. Their status
in `stepStatuses` remains `pending` — which is correct, they never ran.
