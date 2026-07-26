# BL-030 scout — early-return fork: where it blocks, and what "return early" would have to reuse

**Read-only.** No source, test, or contract change. This memo is input to a design
decision; it proposes nothing and chooses nothing.

**Cited at HEAD:** harness `../aetheris/` = `1ab24d8` (clean) · agents/Rig
`aetheris-agents/` = `186cb2a` (clean). Every line number below was read at those
commits.

Harness `CLAUDE.md` learning section read before the first read (Continuous learning,
`../aetheris/CLAUDE.md:485-582`), per the cross-repo first-action rule.

---

## 1. The CLI fork block point

`../aetheris/lib/aetheris/cli/commands/fork.ex:29-43` — verbatim:

```elixir
  @spec run_with_step([String.t()], keyword(), non_neg_integer()) ::
          {:ok, map()} | {:error, String.t()}
  defp run_with_step(positional, opts, step) do
    case positional do
      [path | _rest] ->
        with {:ok, run_id} <- RunHelpers.extract_run_id(path),
             {:ok, _trajectory} <- RunHelpers.load_trajectory(run_id),
             :ok <- RunHelpers.ensure_started(),
             {:ok, _config} <- RunHelpers.lookup_run(run_id),
             {:ok, new_id} <- start_fork(run_id, step, opts) do
          await_fork(new_id)
        end

      [] ->
        {:error, "expected a path to a trajectory file"}
    end
  end
```

`start_fork/3`, `fork.ex:64-77` — verbatim:

```elixir
  @spec start_fork(String.t(), non_neg_integer(), keyword()) ::
          {:ok, String.t()} | {:error, String.t()}
  defp start_fork(original_run_id, step, opts) do
    case Fork.from_step(original_run_id, step, fork_overrides(opts)) do
      {:ok, config} ->
        case Aetheris.start_run(config) do
          {:ok, run_id} -> {:ok, run_id}
          {:error, reason} -> {:error, "failed to start fork run: #{inspect(reason)}"}
        end

      {:error, reason} ->
        {:error, "failed to build fork config: #{inspect(reason)}"}
    end
  end
```

`await_fork/1`, `fork.ex:50-62` — verbatim:

```elixir
  @spec await_fork(String.t()) :: {:ok, map()} | {:error, String.t()}
  defp await_fork(new_id) do
    case RunHelpers.await_run(new_id) do
      {:ok, result} ->
        {:ok, result}

      {:error, message} ->
        case RunHelpers.terminal_error_reason(new_id) do
          nil -> {:error, message}
          reason -> {:error, "#{message}: #{reason}"}
        end
    end
  end
```

**Confirmed: the new run id exists before the await blocks.** `start_fork/3` binds
`{:ok, new_id}` at `fork.ex:36` and `await_fork(new_id)` is the *next* line, `:37`.
The id is not derived from the await's result — `await_run/2`'s success value is
`%{run_id: run_id, status: :done}` built from the id it was *given*
(`run_helpers.ex:112-116`). So the BL-039 Part C diff's reading is correct: at
`fork.ex:36` the id is in hand and nothing has been printed yet.

Where the id is generated: `Fork.assemble_config/5` calls `generate_run_id/0`,
`../aetheris/lib/aetheris/execution/fork.ex:192-194` —
`"fork-" <> Base.encode16(:crypto.strong_rand_bytes(8), case: :lower)`. It is set
before `Aetheris.start_run/1` is called, i.e. before the run exists at all.

**Nothing reaches stdout before the await.** The CLI has exactly one print site:
`Aetheris.CLI.run/1` calls `Formatter.print(result, mode)` at `main.ex:46`, *after*
`maybe_dispatch/2` (`main.ex:45`) has returned. Under `--json` that is a single
`IO.puts(Jason.encode!(data))` (`output/formatter.ex:26-29`). There is no
incremental/streaming stdout channel on this path.

---

## 2. The feasibility gate — what `orchestrate_start` actually does

The BL-030 backlog entry (`docs/backlog-2026-06.md:546-566`) states the want as
"a spawn-and-return-early shape like `orchestrate_start`, which needs the **harness
CLI to emit the run id at fork-start**".

**`orchestrate_start` does not emit a run id at start. It never emits a run id at
all.** Full mechanism, `rig/src-tauri/src/commands/orchestrate.rs:8-108`, verbatim
in the parts that matter:

Spawn — the child is a *piped* subprocess, not `.output()`:

```rust
    cmd.stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::null());
...
    let mut child = cmd.spawn()
        .map_err(|e| format!("spawn failed: {}", e))?;

    let stdin  = Arc::new(Mutex::new(child.stdin.take().unwrap()));
    let stdout = child.stdout.take().unwrap();
```

A detached reader thread drains stdout into a buffer and flips a `done` flag at EOF:

```rust
    std::thread::spawn(move || {
        for line in std::io::BufReader::new(stdout).lines() {
            if let Ok(l) = line {
                let trimmed = l.trim().to_string();
                if !trimmed.is_empty() {
                    if let Ok(v) = serde_json::from_str::<serde_json::Value>(&trimmed) {
                        buf_clone.lock().unwrap().push(v);
                    }
                }
            }
        }
        done_clone.store(true, Ordering::Relaxed);
    });
```

The returned identifier is a **Rig-synthesised job handle**, wall-clock derived —
not a harness run id:

```rust
    let job_id = format!(
        "orch-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis()
    );

    state.jobs.lock().unwrap().insert(
        job_id.clone(),
        crate::OrchestratorJob { child: Arc::new(Mutex::new(child)), stdin, buffer, done },
    );

    Ok(job_id)
```

The job record is held in Rig's own app state (`rig/src-tauri/src/lib.rs:21-37`):

```rust
pub struct OrchestratorJob {
    pub child:  Arc<Mutex<std::process::Child>>,
    pub stdin:  Arc<Mutex<std::process::ChildStdin>>,
    pub buffer: Arc<Mutex<Vec<serde_json::Value>>>,
    pub done:   Arc<AtomicBool>,
}
...
pub struct OrchestratorState {
    pub jobs:         Mutex<HashMap<String, OrchestratorJob>>,
    pub agents_path:  Option<String>,
    pub aetheris_dir: Option<String>,
}
```

Progress and completion come from `orchestrate_poll` draining that buffer
(`orchestrate.rs:116-128`), driven from the frontend by `jobId`, never a run id —
`rig/src/hooks/useOrchestrator.ts:55` `invoke<PollResult>('orchestrate_poll', { jobId })`,
`:88` `const id = await invoke<string>('orchestrate_start', { request, extraEnv, scriptPath })`.
A grep for `run_id`/`runId` in `useOrchestrator.ts` returns nothing.

**So the "keep it alive after the command returns" question does not arise for
`orchestrate_start`, because nothing there returns while the run is in flight in the
sense BL-030 means.** The *Tauri command* returns immediately; the **spawned OS
process keeps running as a child of Rig**, with its `Child` handle, stdin and reader
thread owned by `OrchestratorState.jobs` for the life of the job. The BEAM never
exits early — the whole `mix run` lives, in the background, under Rig's ownership,
until it finishes on its own or `orchestrate_cancel` kills it
(`orchestrate.rs:149-159`).

There is no detached/supervised harness-side process, no daemon, and no
process-outlives-the-CLI mechanism anywhere in this path. What exists to reuse is a
**Rig-side subprocess-ownership + stdout-polling pattern**, not a harness-side
early-return one.

---

## 3. BEAM lifecycle of `mix aetheris fork`

The invocation is `mix`, not the escript: `rig/src-tauri/src/commands/fork.rs:51-55`
runs `std::process::Command::new("mix")` with argv built by `fork_argv`
(`fork.rs:75-89`): `aetheris --json fork <traj> --step N [--name label]`.

The mix task, `../aetheris/lib/mix/tasks/aetheris.ex` — verbatim, whole file body:

```elixir
defmodule Mix.Tasks.Aetheris do
  @moduledoc "CLI entry point. Usage: mix aetheris <command> [options]"
  use Mix.Task

  # @impl true
  # def run(argv), do: Aetheris.CLI.main(argv)

  @impl true
  def run(argv) do
    _ = Aetheris.CLI.run(argv)
    :ok
  end
end
```

Note the commented-out escript path: `Aetheris.CLI.main/1` (`main.ex:33-35`) is
`argv |> run() |> System.halt()`. Under `mix`, `main/1` is not used and nothing calls
`System.halt` on the success path — the task simply returns `:ok`.

The fork run lives **in that same BEAM node**, under the CLI's own application tree:

- `Aetheris.start_run/1`, `../aetheris/lib/aetheris.ex:29-40`:
  `DynamicSupervisor.start_child(Aetheris.RunSupervisor, {Supervisor, config})` then
  `Server.run(config.run_id)`.
- `Aetheris.RunSupervisor` is a child of the application supervisor —
  `../aetheris/lib/aetheris/application.ex:43`:
  `{DynamicSupervisor, name: Aetheris.RunSupervisor, strategy: :one_for_one}`.
- `Agent.Server` executes the loop in a **linked Task inside that tree** —
  `../aetheris/lib/aetheris/agent/server.ex:246-255`, `{:ok, _task} = Task.start_link(fn -> execute_run(...) end)`;
  moduledoc, `server.ex:10`: "On `:run`, spawns a linked `Task` that calls
  `Execution.Loop.run/4`".
- The application is started by the CLI itself, in-process:
  `RunHelpers.ensure_started/0` = `Application.ensure_all_started(:aetheris)`
  (`run_helpers.ex:344-350`), reached at `fork.ex:34`.

So the run's supervision tree is the CLI process's own tree. When
`Mix.Tasks.Aetheris.run/1` returns, mix's task run completes and the OS process
exits; the application stops and every child of `Aetheris.RunSupervisor` terminates
with it. There is no node, port, or OS process that the run could survive into.

**In-repo evidence that this is the mechanism, not an inference from mix defaults:**
the one command that must outlive its own logical completion keeps the VM up by
explicitly refusing to return — `Commands.Server`,
`../aetheris/lib/aetheris/cli/commands/server.ex:31-34`:

```elixir
      {:ok, _pid} ->
        IO.puts("Aetheris API server listening on port #{port}")
        Process.sleep(:infinity)
        {:ok, "server stopped"}
```

Its moduledoc says the same, `server.ex:7-8`: "Starts `Aetheris.API.Server` on the
specified port … and **blocks until the process is interrupted**." No other CLI
command has such a hold, and `fork.ex` has none.

*Labelled precisely:* what is demonstrated from source is (a) the run is a Task in
the CLI's own supervision tree, (b) the mix task returns `:ok` with no hold, and (c)
the only command needing the VM to persist installs an explicit infinite block. That
mix then halts the VM on task return is standard `mix`/`elixir` behaviour and was
**not** separately demonstrated by an experiment in this scout.

**One consequence worth recording, because it is a read and not a proposal:** Rig's
fork call uses `.output()` (`fork.rs:51-55`), which waits for process exit *and* for
stdout/stderr EOF. A CLI that printed a run id early but held the VM open would not
unblock `.output()` — the two ends of this path are coupled, and both are in scope
for any change here.

**Daemon status.** An HTTP API server exists (`mix aetheris server`,
`lib/aetheris/api/server.ex`, routes in `lib/aetheris/api/router.ex`), and it does
expose run creation — `post "/api/runs"` (`router.ex:96`), plus
`get "/api/runs/:run_id"` (`:38`), `get "/api/runs/:run_id/trajectory"` (`:57`),
`post "/api/runs/:run_id/resume"` (`:79`), and a forwarded
`/api/playground` (`:121`). **There is no fork route.** The only `fork` token in
`lib/aetheris/api/` is `run_policy.ex:62`, where `fork_from fork_step fork_context`
appear in a field list. Rig does not use the API server for forking — it shells out
to `mix`.

---

## 4. §4 D2 equivalence clause — verbatim at HEAD

`../aetheris/docs/aetheris/determinism-contract.md:172-175`, verbatim and complete:

```
**Entry points (D2, ratified 2026-07-18):** `Aetheris.fork_run/3` and the CLI
`aetheris fork <traj> --step N` MUST be behaviorally equivalent — both route
through `Fork.from_step/3`. (Today the CLI does not, `cli/commands/fork.ex:47-55`
— a defect against this contract, resolved by t2.)
```

It sits under `## 4. The fork guarantee (D1, ratified 2026-07-18)`
(`determinism-contract.md:91`), immediately before `## 5.` (`:177`).

For reading the clause at HEAD: the parenthetical is a historical note whose
citation has decayed. `cli/commands/fork.ex:47-55` at `1ab24d8` is the `await_fork/1`
comment block and head, not a divergent fork-construction path; the CLI *does* route
through `Fork.from_step/3` today (`fork.ex:67`), which is what "resolved by t2"
records. The normative sentence — the MUST — is unqualified and current.

What the clause does and does not bind is a reading question for the decision, not
settled here: it names `Fork.from_step/3` routing as the shared mechanism, and the
adjacent §4 text distinguishes the two entry points on capability elsewhere —
`determinism-contract.md:157-159`, verbatim: "Selecting a different provider is a
capability of `Aetheris.fork_run/3`'s `overrides`; the CLI and Rig entry points pass
a label only (BL-030)." So §4 already carries at least one recorded asymmetry between
`fork_run/3` and the CLI, attributed to BL-030.

---

## 5. Rig consumption — what "emit at start" would have to put on stdout

`parse_run_id`, `rig/src-tauri/src/commands/fork.rs:91-100` — verbatim:

```rust
/// Extract the forked run id from the CLI's stdout. The `--json` result is one
/// line, but mix/compile/log noise may share stdout, so scan from the end for the
/// last JSON object carrying a `run_id`.
fn parse_run_id(stdout: &str) -> Option<String> {
    stdout.lines().rev().find_map(|line| {
        serde_json::from_str::<serde_json::Value>(line.trim())
            .ok()
            .and_then(|v| v.get("run_id").and_then(|r| r.as_str()).map(String::from))
    })
}
```

Its call site, `fork_run_blocking`, `fork.rs:57-71` — verbatim:

```rust
    let stdout = String::from_utf8_lossy(&output.stdout);

    // A run id is present on stdout only for a `done` fork. Absence means the CLI
    // reported an error on stderr (with a zero exit code) — surface it verbatim so
    // a `failed`/`cancelled`/`step_not_found` fork is never mistaken for success.
    parse_run_id(&stdout).ok_or_else(|| {
        let stderr = String::from_utf8_lossy(&output.stderr);
        let detail = stderr.trim();
        if detail.is_empty() {
            format!("fork produced no run_id; stdout: {}", stdout.trim())
        } else {
            format!("fork failed: {}", detail)
        }
    })
```

The contract the parser encodes: **any line on stdout that JSON-parses to an object
with a string `run_id` counts, and the *last* such line wins.** Its own unit tests
assert exactly that shape — `fork.rs:126-136`:
`"Compiling 2 files (.ex)\n{\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n"` →
`Some("fork-abc123")`; and `parse_run_id("no json here\n{\"status\":\"done\"}\n")` →
`None`. Note the "last such line wins" rule is what an early-emit plus a later
completion line would interact with.

Absence of a `run_id` line is currently overloaded as the *failure* signal
(`fork.rs:59-61` comment, and the `Err` branch above).

What Rig does after parsing — `useFork`, `rig/src/hooks/useFork.ts:25-43`, the invoke
and error handling:

```typescript
      const forkedRunId = await invoke<string>('fork_run', { runId, step, label });
      return forkedRunId;
    } catch (e) {
      const msg = String(e).replace(/^fork failed:\s*/i, '');
      setError(msg);
      throw new Error(msg);
```

and `handleForked`, `rig/src/components/modules/harness/RunList.tsx:550-572` —
verbatim, including its comment:

```typescript
  // Surface a resolved fork (BL-007 t4): jump to the child run's trajectory so its
  // provenance banner is immediately visible. `fork_run` resolves only on a `done`
  // fork, and TrajectoryView reads all display data from the trajectory file's meta
  // (not this summary) — the synthesized summary's `status: 'done'` only gates polling
  // off. The Runs-list row appears on the next manual Refresh.
  const handleForked = useCallback((runId: string) => {
    setSelectedRun({
      run_id:         runId,
      label:          '',
      status:         'done',
      ...
    });
    setActiveTab('trajectory');
  }, []);
```

So: **navigate, do not stream.** The synthesised summary hardcodes `status: 'done'`,
and that value is load-bearing for the one polling gate on this screen —
`rig/src/components/modules/harness/TrajectoryView.tsx:240`:
`const events = useRunEvents(fallbackRunId, { polling: run?.status === 'running' });`
Polling is off for a fork-navigated run today by construction, because the fork is
finished by the time navigation happens.

The documented contract for the command lives at `docs/rig/specs.md:262-281`
("Fork command (`commands/fork.rs`) — BL-007 t3"), including the sentence
"**Blocks to completion:** `mix aetheris fork` prints the run id only when the fork
reaches a terminal status (`await_run`)". §4 of `specs.md` is a drift-checked surface
(`scripts/drift_check.py`, `tauri_commands` check, `lib.rs` ↔ `.rs` files ↔ specs §4),
so any change to this command's registration is gated; the prose above is the part
that would go stale silently. The blocking behaviour is also asserted in prose in
three more places read at HEAD: `fork.rs:12-20` (doc comment), `useFork.ts:6-14`
(header comment), and `RunList.tsx:550-553` (the comment above).

---

## 6. Existing convention — is there a `--detach` to mirror?

**Yes, `--detach` already exists — as a declared, globally-intercepted, unimplemented
flag. It would not be the first; it would be a completion of an existing stub.**

Global switch, `../aetheris/lib/aetheris/cli/main.ex:18-25` — verbatim:

```elixir
  @global_switches [
    json: :boolean,
    quiet: :boolean,
    verbose: :boolean,
    detach: :boolean,
    follow: :boolean
  ]
```

Global interception, `main.ex:97-103` — verbatim. This runs **before dispatch**, so
it applies to *every* subcommand including `fork`:

```elixir
  defp maybe_dispatch(rest, opts) do
    if Keyword.get(opts, :detach, false) or Keyword.get(opts, :follow, false) do
      :not_yet_available
    else
      dispatch(rest, opts)
    end
  end
```

Command-level duplicate on `run`, `../aetheris/lib/aetheris/cli/commands/run.ex:12-35`
— verbatim:

```elixir
  @switches [
    name: :string,
    model: :string,
    max_steps: :integer,
    max_duration: :string,
    detach: :boolean
  ]
...
  def run(args, global_opts) do
    {opts, positional, _} = OptionParser.parse(args, strict: @switches)

    case Keyword.get(opts, :detach, false) do
      true ->
        :not_yet_available

      false ->
        run_attached(positional, opts, global_opts)
    end
  end
```

The `:not_yet_available` value is a first-class CLI result type
(`main.ex:56`, `run.ex:24`) and renders as, `output/formatter.ex:41-46` — verbatim:

```elixir
  def print(:not_yet_available, mode) when mode != :quiet do
    IO.puts("Not yet available (requires daemon — see roadmap)")
    0
  end

  def print(:not_yet_available, :quiet), do: 0
```

Note the exit code is **0**, and the message goes to **stdout**, not stderr.

The existing intent is recorded as daemon-dependent —
`../aetheris/lib/aetheris/cli/commands/agent/start.ex:5-6`, verbatim:

```
  Alias for `aetheris run`. Starts an agent in the foreground.
  Use `--detach` for background execution (not yet available — requires daemon).
```

`--follow` is declared in the same global list and intercepted by the same branch,
with no implementation anywhere: grep for `follow` across `lib/aetheris/cli/` returns
only `main.ex:23` and `main.ex:98`.

There is no `--no-wait`, `--async`, or `--background` flag anywhere in
`lib/aetheris/cli/`.

**Interaction worth recording:** because `maybe_dispatch/2` intercepts globally at
`main.ex:98`, `mix aetheris --detach fork …` at HEAD prints
`Not yet available (requires daemon — see roadmap)` on stdout with exit 0 — which
`parse_run_id` reads as "no `run_id` line" and `fork_run_blocking` converts to
`Err("fork produced no run_id; stdout: Not yet available …")`, since stderr is empty
(`fork.rs:62-70`). The flag is reachable from Rig's argv builder position today
(global flags precede the subcommand, `fork_argv`, `fork.rs:75-89`) and fails in that
specific, legible way.

---

## What this memo does not settle

- Whether D2 permits a CLI-only flag or requires a matching `fork_run/3` change — §4
  is quoted above; the reading is the decision's.
- Whether the run id should ride the existing single `--json` result line, a second
  line, or a different channel — recorded above is only what `parse_run_id` accepts
  today and that the last matching line wins.
- Whether "keep the run alive" is a harness problem at all, given §2: Rig's existing
  early-return pattern keeps the *CLI process* alive under Rig's ownership rather
  than detaching anything harness-side.
- Any experiment. Nothing was run; every claim above is a source read at
  `1ab24d8` / `186cb2a`, with the one standard-`mix`-behaviour step labelled as such
  in §3.
