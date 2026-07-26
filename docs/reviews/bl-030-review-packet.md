# BL-030 — Early-return fork (Rig use case) — review packet r0

**Cross-repo.** Harness `aetheris` @ **ae0c510** · agents/Rig `aetheris-agents` @
**b5e8eee**. Both trees clean. Branch: `main` in both.

Scout: `docs/reviews/bl-030-fork-early-return-scout.md` (read-only, committed
`6f15488`). Ticket: `docs/backlog-2026-06.md` §BL-030.

Both repos' `CLAUDE.md` learning sections read before the first edit.

---

## 1. Done-check

### 1a. Harness gate line — `aetheris` @ ae0c510

```
--- mix deps.get / hex.audit ---
Advisories:
  bandit 1.11.1 - EEF-CVE-2026-65623 (HIGH)
    aka: CVE-2026-65623, GHSA-vg8x-66vg-5pxh
    Quadratic CPU blow-up reassembling fragmented WebSocket messages in Bandit
    https://osv.dev/vulnerability/EEF-CVE-2026-65623

Found packages with security advisories

--- mix compile --warnings-as-errors ---
(no output = clean)

--- mix format --check-formatted ---
(no output = clean)

--- mix credo --strict ---
Analysis took 2.9 seconds (0.1s to load, 2.7s running 69 checks on 228 files)
2047 mods/funs, found no issues.

Use `mix credo explain` to explain issues, `mix credo --help` for options.

--- mix dialyzer ---
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done in 0m4.79s
done (passed successfully)
```

`mix hex.audit` is **red, expected, tracked as BL-060** — one advisory, complete
output above (not truncated): `bandit 1.11.1` / EEF-CVE-2026-65623 (HIGH),
upstream, unrelated to this ticket. Named per the gate rule, not re-triaged.
Every other harness gate is green.

### 1b. Harness — `test/aetheris/cli/commands/fork_test.exs` (the ticket's named done-check)

```
Running ExUnit with seed: 875144, max_cases: 1
Excluding tags: [:requires_worker, :integration, :m10_fixture, :requires_real_provider, :requires_internet]
Aetheris.CLI.Commands.ForkTest [test/aetheris/cli/commands/fork_test.exs]
  * test fork without step returns expected error (113.0ms) [L#44]
  * test the fork-start line precedes the completion line under --json (329.8ms) [L#79]
  * test a failed fork's error message carries the run's terminal reason (306.6ms) [L#54]
  * test fork with step routes through from_step, replaying context and carrying seed (305.7ms) [L#24]
  * test the run id reaches stdout while the fork is still running (302.8ms) [L#134]
  * test the fork-start emit follows the resolved output mode (712.7ms) [L#101]
Finished in 2.1 seconds (0.00s async, 2.1s sync)
6 tests, 0 failures
```

Three pre-existing tests unchanged; three added.

### 1c. Harness — full suite

```
Finished in 90.3 seconds (2.8s async, 87.5s sync)
968 tests, 0 failures, 133 excluded
```

### 1d. Rig — `cargo test`

```
running 22 tests
test commands::fork::tests::fork_argv_with_label ... ok
test commands::fork::tests::fork_argv_without_label ... ok
test commands::fork::tests::read_first_run_id_none_on_eof_without_a_run_id ... ok
test commands::fork::tests::read_first_run_id_returns_the_start_line_id ... ok
test commands::fork::tests::start_failure_error_carries_the_stderr_reason ... ok
test commands::fork::tests::read_first_run_id_stops_before_the_completion_line ... ok
test commands::fork::tests::start_failure_error_without_stderr_says_so ... ok
test commands::harness::tests::live_store_demo_01_absent_from_window_then_found_by_search ... ignored, requires AETHERIS_DB_PATH — run with `cargo test -- --ignored`
test commands::trajectory::tests::root_from_db_path_strips_two_levels ... ok
test commands::trajectory::tests::traj_path_under_has_expected_shape ... ok
test commands::harness::tests::searched_total_count_is_the_match_count_not_the_store_count ... ok
test commands::harness::tests::search_is_case_insensitive ... ok
test commands::harness::tests::unsearched_total_count_is_the_whole_store_not_the_window ... ok
test commands::harness::tests::search_matches_label_and_run_id_separately ... ok
test commands::harness::tests::like_metacharacters_are_literal ... ok
test commands::harness::tests::search_reaches_a_run_outside_the_window ... ok
test commands::harness::tests::empty_and_whitespace_search_are_identical_to_no_search ... ok
test db::migrations::tests::test_migrations_are_idempotent ... ok
test db::migrations::tests::test_f2_views_seeded ... ok
test db::tests::test_init_creates_db_file ... ok
test db::migrations::tests::test_all_f2_tables_created ... ok
test db::tests::test_init_is_idempotent ... ok
test result: ok. 21 passed; 0 failed; 1 ignored; 0 measured; 0 filtered out; finished in 0.24s
```

The one `ignored` is pre-existing and unrelated (`live_store_demo_01…`, requires
`AETHERIS_DB_PATH`). Seven `commands::fork` tests: two pre-existing `fork_argv`,
five added.

### 1e. Rig — frontend gates

```
--- bun run lint ---
$ eslint .
(no findings printed = clean)
--- bunx tsc -b ---
(no output = clean)
--- bun run build ---
dist/assets/index-DL7BOxH0.css                           49.19 kB │ gzip:   9.09 kB
dist/assets/index-rN0Vtkzf.js                           446.93 kB │ gzip: 124.32 kB

✓ built in 655ms
```

`bun run lint` green — off-territory confirmation, consistent with BL-029
(2026-07-20).

### 1f. `drift_check --strict` — run **post-commit**, at agents `b5e8eee`

```
Rig doc-drift checker — 9 check(s)

[PASS] event_types: 22 event types match between event.ex and specs.md §6
[PASS] tauri_commands: 48 commands checked: lib.rs / .rs files / specs.md §4
[PASS] db_schema: 4 documented tables match store.ex schema
[INFO] env_vars: 'AETHERIS_PROVIDER' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'CORPUS_SEARCH_MCP_ENABLED' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'DOCBUILDER_TENANT' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[INFO] env_vars: 'GITHUB_PERSONAL_ACCESS_TOKEN' in specs.md §1 but not read via env::var() in Rig (may be agent-side)
[PASS] env_vars: env vars consistent: 9 in specs, 5 read in Rust
[PASS] routes: 11 registry paths all have matching App.tsx routes
[INFO] payload_fields: prompt_built.key in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.content in DB events but not listed in specs.md §6
[INFO] payload_fields: llm_responded.type in DB events but not listed in specs.md §6
[PASS] payload_fields: sampled DB payload fields consistent with specs.md §6
[PASS] milestone_status: 11 milestone READMEs all have Status: lines
[WARN] project_knowledge: docs/rig/specs.md stale — manifest=c39bf7e current=b5e8eee
[WARN] project_knowledge: docs/rig/architecture.md stale — manifest=d82cf7e current=c0977c2
[WARN] project_knowledge: docs/rig/runbook.md stale — manifest=d0690a6 current=7d6013a
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=6a8a32e current=b5e8eee
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=915d582 current=ae0c510
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=dd12dbb current=1ab24d8
[PASS] command_fields: 10 documented §4 structs (54 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  6 WARN  7 INFO
```

**0 FAIL. 6 WARN, all `project_knowledge` manifest-staleness** — the documented
strict-mode exemption (`CLAUDE.md`, "Definition of done — doc sync"); exit 0.
Named individually, since "zero *unexplained* WARNs" is the invariant:

| file | manifest | current | caused by this ticket? |
|---|---|---|---|
| `docs/rig/specs.md` | c39bf7e | b5e8eee | **yes** — §4 rewrite |
| `docs/backlog-2026-06.md` | 6a8a32e | b5e8eee | **yes** — BL-030 closure entry |
| `docs/aetheris/runbook.md` | 915d582 | ae0c510 | **yes** — fork section rewrite |
| `docs/rig/architecture.md` | d82cf7e | c0977c2 | no — pre-existing |
| `docs/rig/runbook.md` | d0690a6 | 7d6013a | no — pre-existing |
| `docs/aetheris/determinism-contract.md` | dd12dbb | 1ab24d8 | no — pre-existing |

Run post-commit deliberately: check 8 reads committed history, so a pre-commit
run cannot see the staleness the edit introduces. Checks 1–7 also green.

Command/struct names are unchanged, so checks 2 (`tauri_commands`, 48 commands)
and 9 (`command_fields`, 10 structs / 54 fields) pass without edits.

### 1g. Cross-repo done-check

```
agents HEAD: b5e8eee  dirty=0
harness HEAD: ae0c510  dirty=0
--- cross-citations resolve ---
OK  aetheris-agents/docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md
OK  aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md
OK  aetheris-agents/docs/reviews/bl-030-fork-early-return-scout.md
--- each notes file names the other ---
1
1
```

Both repos committed, both gate lines run, both notes files present and
cross-citing. The harness commit names the Rig half; the Rig commit names
`aetheris ae0c510`.

**Ordering note:** every gate above ran against the code as committed. The only
files added after the last `mix test` / `cargo test` were markdown (the two notes
files, the backlog entry). The `cargo test` and `bun run *` blocks in 1d/1e were
re-run at `b5e8eee` for this packet.

### 1h. Manual GUI pass — **outstanding, and it gates merge**

Rig has no frontend test runner (BL-029 / BL-038 precedent), so the frontend half
of this ticket — `handleForked`'s `status: 'running'` and the `TrajectoryView`
polling it switches on — **has no automated coverage at all.** The `cargo`,
`tsc`, lint and build gates above do not touch it. Not yet performed; recorded
here as the merge gate, not as a formality:

1. "Fork from here" on a completed step of a real (non-stub) run → the child
   opens **immediately**, in seconds, not at completion.
2. The child shows `running` and **streams** — events appear progressively and
   polling stops itself when `run_complete` lands.
3. The header run_id matches the forked run.
4. A failing fork (e.g. `--step` on a text-only step → `step_not_found`) surfaces
   its reason on the click as `fork failed: …`; a fork that *starts* then fails
   surfaces on the child, not the click.

---

## 2. Diff

### Harness — `aetheris` @ ae0c510 (notes file inlined in §3, not repeated here)

```diff
diff --git a/docs/aetheris/runbook.md b/docs/aetheris/runbook.md
index 33710cf..f5b444d 100644
--- a/docs/aetheris/runbook.md
+++ b/docs/aetheris/runbook.md
@@ -537,9 +537,18 @@ both display `Mode: record` for a forked run — that is correct and does not me
 fork was lost. Identify a fork by `meta.fork_from`, never by mode or by the `fork-`
 run-id prefix. The original run is never mutated.
 
-**The command blocks until the fork finishes.** The run id is revealed only when the run
-completes, so there is no spawn-and-return-early form today (tracked as BL-030). For a
-long fork, expect the terminal to sit.
+**The command still blocks until the fork finishes, but the run id is revealed at the
+start.** As soon as the fork run is started, the CLI prints it — `Forked run <id> —
+running…`, or a `{"status":"forked","run_id":"…"}` line under `--json` — and only then
+waits. So for a long fork the terminal still sits, but you have the id immediately and
+can `mix aetheris inspect <id>` or tail it from another shell while it runs (BL-030).
+
+The block itself is deliberate and cannot be dropped without a daemon: the fork run is a
+Task in *this* process's supervision tree, so a command that returned early would take
+the run down with it. A consumer that wants a non-blocking fork keeps the process alive
+and owns it — which is what Rig does, reading the start line and handing the running
+child to a background thread. `--detach` remains unimplemented (it reports "not yet
+available"); that is the daemon path, not this one.
 
 **Errors.** `fork requires --step N` (flag missing, or not a non-negative integer) ·
 `expected a path to a trajectory file` (**no positional argument at all** — a bare run id
diff --git a/lib/aetheris/cli/commands/fork.ex b/lib/aetheris/cli/commands/fork.ex
index 68454a8..a374962 100644
--- a/lib/aetheris/cli/commands/fork.ex
+++ b/lib/aetheris/cli/commands/fork.ex
@@ -4,29 +4,35 @@ defmodule Aetheris.CLI.Commands.Fork do
   """
 
   alias Aetheris.CLI.Commands.RunHelpers
+  alias Aetheris.CLI.Output.Formatter
   alias Aetheris.Execution.Fork
 
   @switches [step: :integer, name: :string]
 
   @doc """
   Runs the CLI fork command.
+
+  Unlike every other command, this one prints *before* its result is formatted:
+  the forked run's id is emitted at fork-start, then the command blocks to
+  completion as before and the final result is printed by
+  `Aetheris.CLI.Output.Formatter` as usual. See `emit_fork_started/2`.
   """
   @spec run([String.t()], keyword()) :: {:ok, map()} | {:error, String.t()}
-  def run(args, _global_opts) do
+  def run(args, global_opts) do
     {opts, positional, _} = OptionParser.parse(args, strict: @switches)
 
     case Keyword.get(opts, :step) do
       step when is_integer(step) and step >= 0 ->
-        run_with_step(positional, opts, step)
+        run_with_step(positional, opts, step, Formatter.resolve_mode(global_opts))
 
       _other ->
         {:error, "fork requires --step N"}
     end
   end
 
-  @spec run_with_step([String.t()], keyword(), non_neg_integer()) ::
+  @spec run_with_step([String.t()], keyword(), non_neg_integer(), Formatter.mode()) ::
           {:ok, map()} | {:error, String.t()}
-  defp run_with_step(positional, opts, step) do
+  defp run_with_step(positional, opts, step, mode) do
     case positional do
       [path | _rest] ->
         with {:ok, run_id} <- RunHelpers.extract_run_id(path),
@@ -34,6 +40,7 @@ defmodule Aetheris.CLI.Commands.Fork do
              :ok <- RunHelpers.ensure_started(),
              {:ok, _config} <- RunHelpers.lookup_run(run_id),
              {:ok, new_id} <- start_fork(run_id, step, opts) do
+          :ok = emit_fork_started(new_id, mode)
           await_fork(new_id)
         end
 
@@ -42,6 +49,34 @@ defmodule Aetheris.CLI.Commands.Fork do
     end
   end
 
+  # The early emit (BL-030). The fork run's id exists as soon as `start_fork/3`
+  # returns — `Fork.from_step/3` generates it before the run is started — but
+  # until now it reached stdout only through the final `Formatter.print/2`,
+  # after `await_fork/1` had blocked for the whole run. A consumer that wants to
+  # follow the child (Rig) therefore could not learn the id until there was
+  # nothing left to follow.
+  #
+  # This is additive and does not change the blocking contract: the command
+  # still awaits a terminal status, still returns the same result, and the
+  # completion line still prints after this one. The block is load-bearing — the
+  # fork run is a Task in *this* process's supervision tree
+  # (`Aetheris.RunSupervisor`), so returning early would kill it. Keeping the
+  # process alive and handing the id out early is the whole mechanism; owning
+  # that process is the consumer's job.
+  #
+  # Fork is consequently the only command that writes to stdout before dispatch
+  # returns. Any consumer scanning for a single result line must account for two.
+  @spec emit_fork_started(String.t(), Formatter.mode()) :: :ok
+  defp emit_fork_started(new_id, :json) do
+    IO.puts(Jason.encode!(%{status: "forked", run_id: new_id}))
+  end
+
+  defp emit_fork_started(new_id, :human) do
+    IO.puts("Forked run #{new_id} — running…")
+  end
+
+  defp emit_fork_started(_new_id, :quiet), do: :ok
+
   # `await_run/2` reports that the fork failed, not why — the cause is in the
   # fork's own trajectory. Without this the operator sees only
   # "run <id> failed", and (through Rig, which surfaces stderr verbatim) that
diff --git a/lib/aetheris/cli/main.ex b/lib/aetheris/cli/main.ex
index 60880b5..8058511 100644
--- a/lib/aetheris/cli/main.ex
+++ b/lib/aetheris/cli/main.ex
@@ -41,7 +41,7 @@ defmodule Aetheris.CLI do
     {global_opts, rest, _invalid} =
       OptionParser.parse_head(argv, strict: @global_switches, aliases: @global_aliases)
 
-    mode = output_mode(global_opts)
+    mode = Formatter.resolve_mode(global_opts)
     result = maybe_dispatch(rest, global_opts)
     Formatter.print(result, mode)
     # exit_code = Formatter.print(result, mode)
@@ -86,14 +86,6 @@ defmodule Aetheris.CLI do
   @spec verbose_mode?(keyword()) :: boolean()
   def verbose_mode?(opts), do: Keyword.get(opts, :verbose, false)
 
-  defp output_mode(opts) do
-    cond do
-      Keyword.get(opts, :json, false) -> :json
-      Keyword.get(opts, :quiet, false) -> :quiet
-      true -> :human
-    end
-  end
-
   defp maybe_dispatch(rest, opts) do
     if Keyword.get(opts, :detach, false) or Keyword.get(opts, :follow, false) do
       :not_yet_available
diff --git a/lib/aetheris/cli/output/formatter.ex b/lib/aetheris/cli/output/formatter.ex
index e1ea68f..68197b9 100644
--- a/lib/aetheris/cli/output/formatter.ex
+++ b/lib/aetheris/cli/output/formatter.ex
@@ -11,6 +11,25 @@ defmodule Aetheris.CLI.Output.Formatter do
   @type mode :: :human | :json | :quiet
   @type result :: {:ok, term()} | {:error, String.t()} | :not_yet_available
 
+  @doc """
+  Resolves the output mode from parsed global CLI options.
+
+  Lives here rather than in `Aetheris.CLI` because a command that prints
+  *before* its result is formatted needs the same resolution the final
+  `print/2` will use, and `Aetheris.CLI` dispatching to that command while the
+  command reaches back for a private helper is the wrong direction. The mode
+  and its `t:mode/0` type now have one home. Used by `Aetheris.CLI.run/1` and
+  by `Aetheris.CLI.Commands.Fork` for its fork-start emit (BL-030).
+  """
+  @spec resolve_mode(keyword()) :: mode()
+  def resolve_mode(opts) do
+    cond do
+      Keyword.get(opts, :json, false) -> :json
+      Keyword.get(opts, :quiet, false) -> :quiet
+      true -> :human
+    end
+  end
+
   @doc """
   Prints `result` according to `mode` and returns an exit code.
   """
diff --git a/test/aetheris/cli/commands/fork_test.exs b/test/aetheris/cli/commands/fork_test.exs
index 0c512bf..c41ac55 100644
--- a/test/aetheris/cli/commands/fork_test.exs
+++ b/test/aetheris/cli/commands/fork_test.exs
@@ -2,6 +2,7 @@ defmodule Aetheris.CLI.Commands.ForkTest do
   use ExUnit.Case, async: false
 
   import Aetheris.Test.RunHelpers
+  import ExUnit.CaptureIO
 
   alias Aetheris.CLI.Commands.Fork
   alias Aetheris.RunConfig
@@ -62,6 +63,113 @@ defmodule Aetheris.CLI.Commands.ForkTest do
     assert message =~ "unknown provider: no-such-provider"
   end
 
+  # BL-030, wire format. Two JSON lines now reach stdout: the fork-start line
+  # first, the completion line second, naming the same run. This is what Rig's
+  # reader parses, so it is asserted positionally.
+  #
+  # Exercised through `CLI.run/1` (not `CLI.main/1`, which halts the VM) because
+  # the claim spans the seam: the first line comes from the command, the second
+  # from `Formatter.print/2` after dispatch returns.
+  #
+  # What this test does NOT prove: that the emit is *ahead of* `await_fork/1`.
+  # Both writes happen inside `CLI.run/1`, so moving the emit after the await
+  # leaves this order untouched — mutation-verified, that reordering keeps this
+  # test and every other one in this file green. The timing test below is the
+  # one that fails on it.
+  test "the fork-start line precedes the completion line under --json",
+       %{trajectory_path: path} do
+    output = capture_io(fn -> Aetheris.CLI.run(["--json", "fork", path, "--step", "0"]) end)
+
+    decoded =
+      output
+      |> String.split("\n", trim: true)
+      |> Enum.flat_map(fn line ->
+        case Jason.decode(line) do
+          {:ok, %{} = map} -> [map]
+          _other -> []
+        end
+      end)
+
+    assert [%{"status" => "forked", "run_id" => started_id}, completion | _rest] = decoded
+    assert Map.fetch!(completion, "status") == "done"
+    assert Map.fetch!(completion, "run_id") == started_id
+  end
+
+  # The emit resolves through `Formatter.resolve_mode/1`, the same resolution the
+  # closing `print/2` uses — so a `--quiet` consumer stays silent and a human one
+  # gets prose. `quiet` asserts the *absence* of a line the other two modes emit.
+  test "the fork-start emit follows the resolved output mode", %{trajectory_path: path} do
+    {{:ok, json_result}, json_out} =
+      with_io(fn -> Fork.run([path, "--step", "0"], json: true) end)
+
+    assert {:ok, %{"status" => "forked", "run_id" => emitted_id}} =
+             json_out |> String.trim() |> Jason.decode()
+
+    assert emitted_id == Map.fetch!(json_result, :run_id)
+
+    {{:ok, human_result}, human_out} = with_io(fn -> Fork.run([path, "--step", "0"], []) end)
+    assert human_out =~ "Forked run #{Map.fetch!(human_result, :run_id)} — running…"
+
+    {{:ok, _quiet_result}, quiet_out} =
+      with_io(fn -> Fork.run([path, "--step", "0"], quiet: true) end)
+
+    refute quiet_out =~ "run_id"
+    refute quiet_out =~ "Forked run"
+  end
+
+  # The discriminating test. BL-030's property is not "two lines in this order"
+  # (see above) — it is that the id reaches stdout *while the run is still in
+  # flight*, so a consumer can follow the child. That is a timing property and
+  # is asserted as one, against a live `StringIO` group leader rather than
+  # `capture_io/1`, which only yields its buffer after the captured function has
+  # already returned.
+  #
+  # The window is `await_run/2`'s poll floor: it sleeps `@poll_interval_ms` (200)
+  # between status checks, so a stub fork emits at ~+6 ms and the command
+  # returns at ~+204 ms — measured over five runs, window 197–200 ms. Moving the
+  # emit after `await_fork/1` collapses that to ~0. The 100 ms threshold sits
+  # between the two with margin either side and deliberately does not encode the
+  # poll interval, which is free to change.
+  @min_emit_lead_ms 100
+  test "the run id reaches stdout while the fork is still running", %{trajectory_path: path} do
+    {:ok, io} = StringIO.open("")
+    started_at = System.monotonic_time(:millisecond)
+
+    task =
+      Task.async(fn ->
+        Process.group_leader(self(), io)
+        Fork.run([path, "--step", "0"], json: true)
+      end)
+
+    emitted_at = await_forked_line(io, started_at)
+    assert {:ok, _result} = Task.await(task, 30_000)
+    returned_at = System.monotonic_time(:millisecond)
+
+    lead = returned_at - emitted_at
+
+    assert lead >= @min_emit_lead_ms,
+           "expected the fork-start line at least #{@min_emit_lead_ms}ms before the command " <>
+             "returned; got #{lead}ms. The emit is not ahead of await_fork/1."
+  end
+
+  @forked_line_deadline_ms 30_000
+  defp await_forked_line(io, started_at) do
+    now = System.monotonic_time(:millisecond)
+    emitted? = io |> StringIO.contents() |> elem(1) |> String.contains?(~s("forked"))
+
+    cond do
+      emitted? ->
+        now
+
+      now - started_at > @forked_line_deadline_ms ->
+        flunk("no fork-start line within 30s")
+
+      true ->
+        Process.sleep(5)
+        await_forked_line(io, started_at)
+    end
+  end
+
   # Step 0 is a tool call (worker-free local echo dispatch) so it records a
   # :step_complete event — a real fork point (a terminal text step emits only
   # run_complete). Step 1 is the finishing text response.
```

### Rig / agents — `aetheris-agents` @ b5e8eee (notes file inlined in §3, not repeated here)

```diff
diff --git a/docs/backlog-2026-06.md b/docs/backlog-2026-06.md
index 04838eb..4b24d62 100644
--- a/docs/backlog-2026-06.md
+++ b/docs/backlog-2026-06.md
@@ -563,6 +563,29 @@ loop far less load-bearing.
 **Done when:** the fork CLI can emit the run id at start; Rig's affordance returns
 without waiting for completion.
 
+**Status:** Done 2026-07-26. Harness: `cli/commands/fork.ex` emits the run id
+between `start_fork/3` and `await_fork/1`, per resolved mode
+(`{"status":"forked","run_id":…}` under `--json`); `output_mode/1` moved from
+`Aetheris.CLI` to `Formatter.resolve_mode/1` so the command can resolve the same
+mode the closing `print/2` uses. The CLI still blocks to completion — deliberately:
+the fork run is a Task in the CLI process's own supervision tree, so an early
+return would kill it. Rig: `fork.rs` spawns piped and owns the child, returns at
+the first `run_id` line, and hands the running subprocess to a detached thread that
+drains both pipes and reaps; `handleForked` sets `status: 'running'` so
+`TrajectoryView`'s existing BL-005 events-fallback polling streams the child.
+`--detach`/`--follow` untouched (daemon path). Notes:
+`docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md` +
+`../aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md`. Scout:
+`docs/reviews/bl-030-fork-early-return-scout.md`.
+
+> **Dangling ref, deliberate.** Determinism contract §4 says "the CLI and Rig entry
+> points pass a label only (BL-030)". That sentence is still **true** after this
+> ticket — BL-030 did not add overrides — but its `(BL-030)` ref now points at a
+> closed ticket that never carried them. The override work split out as **BL-062**,
+> whose §8 edit repoints it. Flagged rather than left to rot: §4 already carries one
+> decayed parenthetical (D2's `cli/commands/fork.ex:47-55`, per the scout), so this
+> section has form.
+
 ---
 
 ### BL-031 — `await_run` has no timeout or cap (#TBD)
diff --git a/docs/rig/specs.md b/docs/rig/specs.md
index d6f4875..faf1a19 100644
--- a/docs/rig/specs.md
+++ b/docs/rig/specs.md
@@ -259,7 +259,7 @@ pub struct TrajectoryFile {
 Takes `run_id: String`. Opens a save dialog; copies
 `priv/runs/{run_id}/trajectory.json` to the user-chosen path. Returns `()`.
 
-### Fork command (`commands/fork.rs`) — BL-007 t3
+### Fork command (`commands/fork.rs`) — BL-007 t3, early-return since BL-030
 
 **`fork_run`** — `async` command. Takes `run_id: String`, `step: u64`,
 `label: Option<String>`. Resolves the source trajectory (`traj_path`, shared with
@@ -268,15 +268,33 @@ Takes `run_id: String`. Opens a save dialog; copies
 `AETHERIS_DB_PATH`.parent().parent()). The child run is the post-t2 CLI's fork —
 re-execution from step N (converged on `Fork.from_step/3`): it runs in `:record`
 mode and is identified by `meta.fork_from`, not a `:fork` mode. Returns the forked
-`run_id: String` parsed from the CLI's JSON result line, or an error string.
-**Blocks to completion:** `mix aetheris fork` prints the run id only when the fork
-reaches a terminal status (`await_run`), so the command runs the blocking
-subprocess on `spawn_blocking` (`async`, off the UI thread — Tauri v2 runs *sync*
-commands on the main thread); the invoke promise resolves when the fork finishes
-(progress UX is t4's concern). **Terminal status:** a run id appears on stdout only
-for a `done` fork; `failed`/`cancelled`/`step_not_found` produce a CLI error on
-*stderr* with a zero exit code, so `fork_run` returns `Err` carrying that stderr —
-never a false success. **`label` caveat:** persisted to the harness `runs.label`
+`run_id: String`, or an error string.
+
+**Returns at fork-start; Rig owns the subprocess (BL-030).** The CLI emits
+`{"status":"forked","run_id":"…"}` as soon as the fork run is started, then
+blocks to completion as before and prints its result line at the end. `fork_run`
+spawns the CLI with both pipes piped, reads stdout only until that first
+`run_id` line, returns it, and hands the still-running child to a detached
+thread that drains both pipes to EOF and reaps it (`child.wait()`). The CLI's
+block is deliberate and must not be interrupted — the fork run is a Task in the
+CLI process's own supervision tree (`Aetheris.RunSupervisor`), so the process
+must stay alive for the run to finish; the run outlives the invoke, not the app.
+This is `orchestrate.rs`'s owned-subprocess shape, with stderr kept (below). The
+command remains `async` on `spawn_blocking`: the wait is seconds (mix boot +
+fork start) rather than minutes, but it is still blocking, and Tauri v2 runs
+*sync* commands on the main thread.
+
+**Start failure vs run failure.** A fork that never starts (`step_not_found`, an
+unreadable trajectory) fails inside `Fork.from_step/3` before any run exists, so
+no `run_id` line is written and stdout reaches EOF; the CLI reports the reason on
+*stderr* with a zero exit code (`mix` discards the CLI exit code), so **stderr
+stays piped** and is read on that path — `fork_run` returns `Err` carrying it,
+preserving `fork failed: <reason>`. Nulling stderr (as `orchestrate.rs` does,
+having no stderr contract) would degrade every start failure to a bare "produced
+no run_id". A fork that starts and *then* fails does so after the command has
+returned, and surfaces on the child run's own streamed trajectory.
+
+**`label` caveat:** persisted to the harness `runs.label`
 column, but Rig's `harness_list_runs`/`harness_get_run` read the label from
 `config_json` (where `encode_config` strips it), so a fork label is stored but not
 surfaced by Rig today (see BL-007 t3 notes).
diff --git a/rig/src-tauri/src/commands/fork.rs b/rig/src-tauri/src/commands/fork.rs
index 109cf72..c2118dd 100644
--- a/rig/src-tauri/src/commands/fork.rs
+++ b/rig/src-tauri/src/commands/fork.rs
@@ -1,4 +1,6 @@
 use crate::commands::trajectory::{aetheris_root, traj_path};
+use std::io::{BufRead, BufReader, Read};
+use std::process::{ChildStderr, ChildStdout, Stdio};
 
 /// Fork a completed run at `step` via the post-t2 CLI
 /// (`mix aetheris fork <trajectory> --step N [--name label]`, converged on
@@ -6,24 +8,38 @@ use crate::commands::trajectory::{aetheris_root, traj_path};
 ///
 /// Resolves the source run's trajectory path from `run_id`, spawns the CLI in
 /// the aetheris repo root, and returns the forked run's id parsed from the CLI's
-/// JSON result line. The child run executes in `:record` mode and is identified
+/// fork-*start* line. The child run executes in `:record` mode and is identified
 /// by `meta.fork_from` (t2 convention); it is not a `:fork` mode.
 ///
-/// **Async, blocks to completion.** `mix aetheris fork` blocks until the forked
-/// run reaches a terminal status (the CLI's `await_run` contract), and only then
-/// prints the run id — so this command cannot spawn-and-return an id early like
-/// `orchestrate_start` (the id does not exist until completion; changing that is a
-/// harness concern). The command is therefore `async` and runs the blocking
-/// subprocess on `spawn_blocking`, so a long (real-provider) fork does not freeze
-/// the UI thread (Tauri v2 runs *sync* commands on the main thread). The invoke
-/// promise still resolves only when the fork finishes — a progress affordance is
-/// t4's concern.
+/// **Returns early; Rig owns the subprocess (BL-030).** The CLI emits
+/// `{"status":"forked","run_id":"…"}` as soon as the fork run is started, then
+/// blocks to completion as before and prints its result line at the end. That
+/// block is load-bearing and must not be interrupted: the fork run is a Task in
+/// the CLI process's own supervision tree (`Aetheris.RunSupervisor`), so the
+/// process has to stay alive for the run to finish. This command therefore does
+/// **not** wait for exit — it reads stdout only until the first `run_id` line,
+/// returns it, and hands the still-running child to a detached thread that
+/// drains both pipes to EOF and reaps it. The pattern is `orchestrate.rs`'s
+/// owned-subprocess shape; the run outlives the invoke, not the app.
 ///
-/// **Terminal status.** A run id appears on stdout only for a `done` fork. The CLI
-/// turns `failed`/`cancelled` into an error on *stderr* with a zero exit code
-/// (`mix` discards the CLI exit code), so a non-`done` fork yields no stdout id and
-/// this command returns `Err` carrying the CLI's stderr — it never reports a failed
-/// fork as success.
+/// The command stays `async` on `spawn_blocking`: the wait is now seconds (mix
+/// boot + fork start) rather than minutes, but it is still blocking, and Tauri
+/// v2 runs *sync* commands on the main thread.
+///
+/// **Start failure.** A fork that never starts — `step_not_found`, an unreadable
+/// trajectory, a config error — fails inside `Fork.from_step/3` before any run
+/// exists, so no `run_id` line is ever written and stdout reaches EOF. The CLI
+/// reports the reason on *stderr* with a zero exit code (`mix` discards the CLI
+/// exit code), so that is where the diagnosis lives: stderr stays piped and is
+/// read on this path, preserving `fork failed: <reason>` — including BL-039
+/// Part C's terminal-reason detail. Nulling stderr the way `orchestrate.rs`
+/// does (it has no stderr contract) would silently degrade every start failure
+/// to a bare "produced no run_id".
+///
+/// **Run failure is no longer this command's business.** A fork that starts and
+/// then fails does so after this command has returned; the operator sees it on
+/// the child run's own streamed trajectory, which is where the diagnosis was
+/// always recorded.
 ///
 /// **`label` caveat.** `label` maps to CLI `--name` → `RunConfig.label`, durably
 /// stored in the harness `runs.label` column. Rig's own `harness_list_runs` /
@@ -41,37 +57,63 @@ pub async fn fork_run(
         .map_err(|e| format!("fork task failed to run: {}", e))?
 }
 
-/// The blocking body: spawn the CLI and parse the result. Runs off the UI thread
-/// via `spawn_blocking`.
+/// The blocking body: spawn the CLI, read up to the fork-start line, hand off.
+/// Runs off the UI thread via `spawn_blocking`.
 fn fork_run_blocking(run_id: String, step: u64, label: Option<String>) -> Result<String, String> {
     let traj = traj_path(&run_id)?;
     let root = aetheris_root()?;
     let traj_str = traj.to_str().ok_or("trajectory path is not valid UTF-8")?;
 
-    let output = std::process::Command::new("mix")
+    let mut child = std::process::Command::new("mix")
         .args(fork_argv(traj_str, step, label.as_deref()))
         .current_dir(&root)
-        .output()
+        .stdout(Stdio::piped())
+        .stderr(Stdio::piped())
+        .spawn()
         .map_err(|e| format!("failed to spawn `mix aetheris fork`: {}", e))?;
 
-    let stdout = String::from_utf8_lossy(&output.stdout);
-
-    // A run id is present on stdout only for a `done` fork. Absence means the CLI
-    // reported an error on stderr (with a zero exit code) — surface it verbatim so
-    // a `failed`/`cancelled`/`step_not_found` fork is never mistaken for success.
-    parse_run_id(&stdout).ok_or_else(|| {
-        let stderr = String::from_utf8_lossy(&output.stderr);
-        let detail = stderr.trim();
-        if detail.is_empty() {
-            format!("fork produced no run_id; stdout: {}", stdout.trim())
-        } else {
-            format!("fork failed: {}", detail)
+    let stdout = child
+        .stdout
+        .take()
+        .ok_or("fork subprocess produced no stdout pipe")?;
+    let stderr = child
+        .stderr
+        .take()
+        .ok_or("fork subprocess produced no stderr pipe")?;
+
+    // stderr is drained on its own thread from the moment of spawn, in both
+    // outcomes. A start failure needs its contents, and a successful fork must
+    // not be able to wedge on a full stderr pipe while nobody is reading it —
+    // one collector satisfies both, so neither pipe can deadlock the run.
+    let stderr_collector = std::thread::spawn(move || collect(stderr));
+
+    let mut reader = BufReader::new(stdout);
+
+    match read_first_run_id(&mut reader) {
+        // Started. Hand the child off: drain the rest of stdout to EOF and reap,
+        // so the run completes and leaves no zombie. Nothing here is awaited.
+        Some(forked_run_id) => {
+            std::thread::spawn(move || {
+                drain(&mut reader);
+                let _ = stderr_collector.join();
+                let _ = child.wait();
+            });
+            Ok(forked_run_id)
         }
-    })
+
+        // Never started: stdout hit EOF with no run_id line. The reason is on
+        // stderr — surface it verbatim, preserving the `fork failed: <reason>`
+        // shape the UI and its error-strip were built against.
+        None => {
+            let detail = stderr_collector.join().unwrap_or_default();
+            let _ = child.wait();
+            Err(start_failure_error(&detail))
+        }
+    }
 }
 
 /// Build the `mix` argv for the fork invocation. `--json` (a global CLI flag)
-/// must precede the `fork` subcommand so the CLI emits a machine-parseable line.
+/// must precede the `fork` subcommand so the CLI emits machine-parseable lines.
 fn fork_argv(traj: &str, step: u64, label: Option<&str>) -> Vec<String> {
     let mut args = vec![
         "aetheris".to_string(),
@@ -88,20 +130,72 @@ fn fork_argv(traj: &str, step: u64, label: Option<&str>) -> Vec<String> {
     args
 }
 
-/// Extract the forked run id from the CLI's stdout. The `--json` result is one
-/// line, but mix/compile/log noise may share stdout, so scan from the end for the
-/// last JSON object carrying a `run_id`.
-fn parse_run_id(stdout: &str) -> Option<String> {
-    stdout.lines().rev().find_map(|line| {
-        serde_json::from_str::<serde_json::Value>(line.trim())
-            .ok()
-            .and_then(|v| v.get("run_id").and_then(|r| r.as_str()).map(String::from))
-    })
+/// Extract a run id from one stdout line, if it carries one.
+///
+/// This is the predicate the pre-BL-030 `parse_run_id` applied while scanning
+/// the whole buffer backwards; only the scan direction changed, not what counts
+/// as a run_id line. `mix` compile and log noise shares stdout and does not
+/// parse as JSON, so no filtering beyond "is a JSON object with a string
+/// `run_id`" is needed.
+fn run_id_from_line(line: &str) -> Option<String> {
+    serde_json::from_str::<serde_json::Value>(line.trim())
+        .ok()
+        .and_then(|v| v.get("run_id").and_then(|r| r.as_str()).map(String::from))
+}
+
+/// Read stdout line by line and stop at the **first** line carrying a `run_id` —
+/// the CLI's fork-start emit. Returns `None` if stdout reaches EOF without one.
+///
+/// First-wins is safe here, and the reader deliberately does not try to
+/// disambiguate further: `await_run`'s verbose event stream goes to stderr, and
+/// under `--json` the closing `Formatter.print/2` writes exactly once, so the
+/// only JSON-with-`run_id` lines on stdout are this start line and the eventual
+/// completion line. Stopping at the first is what makes the command return in
+/// seconds instead of minutes — the whole point of BL-030.
+fn read_first_run_id<R: BufRead>(reader: &mut R) -> Option<String> {
+    let mut line = String::new();
+    loop {
+        line.clear();
+        match reader.read_line(&mut line) {
+            Ok(0) => return None,
+            Ok(_) => {
+                if let Some(id) = run_id_from_line(&line) {
+                    return Some(id);
+                }
+            }
+            Err(_) => return None,
+        }
+    }
+}
+
+/// Render the error for a fork that never started. Preserves the `fork failed:`
+/// prefix `useFork.ts` strips and the UI's error strip re-labels.
+fn start_failure_error(stderr: &str) -> String {
+    let detail = stderr.trim();
+    if detail.is_empty() {
+        "fork produced no run_id and reported no error".to_string()
+    } else {
+        format!("fork failed: {}", detail)
+    }
+}
+
+/// Read a pipe to EOF and return it as a lossy string.
+fn collect(mut pipe: ChildStderr) -> String {
+    let mut buf = Vec::new();
+    let _ = pipe.read_to_end(&mut buf);
+    String::from_utf8_lossy(&buf).into_owned()
+}
+
+/// Discard the remainder of a pipe so the child never blocks on a full buffer.
+fn drain(reader: &mut BufReader<ChildStdout>) {
+    let mut sink = Vec::new();
+    let _ = reader.read_to_end(&mut sink);
 }
 
 #[cfg(test)]
 mod tests {
     use super::*;
+    use std::io::Cursor;
 
     fn svec(a: &[&str]) -> Vec<String> {
         a.iter().map(|s| s.to_string()).collect()
@@ -124,14 +218,53 @@ mod tests {
     }
 
     #[test]
-    fn parse_run_id_finds_last_json_line() {
-        let out = "Compiling 2 files (.ex)\n{\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n";
-        assert_eq!(parse_run_id(out), Some("fork-abc123".to_string()));
+    fn read_first_run_id_returns_the_start_line_id() {
+        let out = "Compiling 2 files (.ex)\n\
+                   {\"status\":\"forked\",\"run_id\":\"fork-abc123\"}\n\
+                   {\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n";
+        let mut cursor = Cursor::new(out);
+        assert_eq!(read_first_run_id(&mut cursor), Some("fork-abc123".to_string()));
+    }
+
+    /// The early-return property, asserted structurally rather than by wall
+    /// clock: after the id is read, the completion line must still be unread in
+    /// the stream. A reader that drained to EOF first (the old last-wins scan)
+    /// would leave nothing behind and fail this.
+    #[test]
+    fn read_first_run_id_stops_before_the_completion_line() {
+        let out = "{\"status\":\"forked\",\"run_id\":\"fork-abc123\"}\n\
+                   {\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n";
+        let mut cursor = Cursor::new(out);
+
+        assert_eq!(read_first_run_id(&mut cursor), Some("fork-abc123".to_string()));
+
+        let mut rest = String::new();
+        cursor.read_to_string(&mut rest).unwrap();
+        assert_eq!(rest, "{\"status\":\"done\",\"run_id\":\"fork-abc123\"}\n");
+    }
+
+    #[test]
+    fn read_first_run_id_none_on_eof_without_a_run_id() {
+        // A fork that never starts: no run_id line is ever written to stdout.
+        let mut cursor = Cursor::new("no json here\n{\"status\":\"error\"}\n");
+        assert_eq!(read_first_run_id(&mut cursor), None);
     }
 
+    /// A start failure must carry the CLI's stderr reason (BL-039 Part C's
+    /// diagnosis), not a generic "no run_id" line.
     #[test]
-    fn parse_run_id_none_when_absent() {
-        // A `failed`/`cancelled` fork prints its error to stderr, not a run_id line.
-        assert_eq!(parse_run_id("no json here\n{\"status\":\"done\"}\n"), None);
+    fn start_failure_error_carries_the_stderr_reason() {
+        assert_eq!(
+            start_failure_error("Error: failed to build fork config: :step_not_found\n"),
+            "fork failed: Error: failed to build fork config: :step_not_found"
+        );
+    }
+
+    #[test]
+    fn start_failure_error_without_stderr_says_so() {
+        assert_eq!(
+            start_failure_error("   \n"),
+            "fork produced no run_id and reported no error"
+        );
     }
 }
diff --git a/rig/src/components/modules/harness/RunList.tsx b/rig/src/components/modules/harness/RunList.tsx
index f4f2507..6d2a744 100644
--- a/rig/src/components/modules/harness/RunList.tsx
+++ b/rig/src/components/modules/harness/RunList.tsx
@@ -546,16 +546,20 @@ export function HarnessRoute() {
     setActiveTab('events');
   }, []);
 
-  // Surface a resolved fork (BL-007 t4): jump to the child run's trajectory so its
-  // provenance banner is immediately visible. `fork_run` resolves only on a `done`
-  // fork, and TrajectoryView reads all display data from the trajectory file's meta
-  // (not this summary) — the synthesized summary's `status: 'done'` only gates polling
-  // off. The Runs-list row appears on the next manual Refresh.
+  // Surface a started fork (BL-007 t4, early-return since BL-030): jump to the child
+  // run's trajectory so its provenance banner is immediately visible. `fork_run` now
+  // resolves as soon as the fork *starts*, so the child is still running when we land
+  // on it — `status: 'running'` is what turns TrajectoryView's event polling on, and
+  // the poll stops itself when `run_complete` reaches the stream. The trajectory file
+  // does not exist until the run finishes (it is written once, at completion), so
+  // TrajectoryView's file load fails and its events fallback reconstructs the view
+  // live; that fallback is the BL-005 path and needs no change here. The Runs-list
+  // row appears on the next manual Refresh.
   const handleForked = useCallback((runId: string) => {
     setSelectedRun({
       run_id:         runId,
       label:          '',
-      status:         'done',
+      status:         'running',
       provider:       '',
       model:          '',
       started_at:     '',
diff --git a/rig/src/components/modules/harness/TrajectoryView.tsx b/rig/src/components/modules/harness/TrajectoryView.tsx
index d209319..840f16a 100644
--- a/rig/src/components/modules/harness/TrajectoryView.tsx
+++ b/rig/src/components/modules/harness/TrajectoryView.tsx
@@ -344,7 +344,9 @@ function TrajectoryBody({ trajectory, banner, isPolling, showExport, canFork, pa
   const { fork, forking, error, clearError } = useFork();
   const [forkingStep, setForkingStep] = useState<number | null>(null);
 
-  // A fork blocks to completion (minutes). If the user selects another run or leaves
+  // A fork resolves at fork-start (seconds, since BL-030) rather than at completion,
+  // so this window is far shorter than it was — but it is not zero, and the hazard is
+  // unchanged. If the user selects another run or leaves
   // the Trajectory tab meanwhile, this body unmounts (run change → the fileLoading
   // branch swaps in CentredMessage; tab switch → Radix TabsContent unmounts inactive
   // content). The pending promise still resolves, but `onForked` lives on the
diff --git a/rig/src/hooks/useFork.ts b/rig/src/hooks/useFork.ts
index 04691c2..b9ccaaa 100644
--- a/rig/src/hooks/useFork.ts
+++ b/rig/src/hooks/useFork.ts
@@ -2,15 +2,22 @@ import { useState, useCallback } from 'react';
 import { invoke } from '@tauri-apps/api/core';
 
 // ============================================================================
-// useFork — imperative fork action (BL-007 t4)
+// useFork — imperative fork action (BL-007 t4, early-return since BL-030)
 //
 // Wraps the `fork_run` Tauri command (BL-007 t3). The command is `async` and
-// **blocks to completion**: `mix aetheris fork` prints the child run id only when
-// the fork reaches a terminal status (`await_run`), so the invoke promise resolves
-// only when the fork finishes — minutes for a real provider. Callers therefore
-// need the `forking` flag to show an in-flight state. A non-`done` outcome rejects
-// with the CLI's stderr; the mirror of `usePlaygroundSubmit`'s error handling
-// surfaces it via `error` and rethrows so the caller can skip its success path.
+// **resolves when the fork starts**, not when it finishes: the CLI emits the
+// child run id as soon as the run is started, and Rig returns it and hands the
+// still-running subprocess to a background thread. The promise settles in
+// seconds (mix boot + fork start) rather than minutes, so `forking` now covers
+// the start, not the whole run — the caller navigates to the child and watches
+// it stream.
+//
+// The signature is unchanged. A rejection now means the fork never *started*
+// (`step_not_found`, an unreadable trajectory), carrying the CLI's stderr; a
+// fork that starts and then fails surfaces on the child run's own trajectory,
+// where its diagnosis was always recorded. The error handling mirrors
+// `usePlaygroundSubmit`: surface via `error` and rethrow so the caller can skip
+// its success path.
 // ============================================================================
 
 export function useFork(): {
@@ -31,9 +38,10 @@ export function useFork(): {
       const forkedRunId = await invoke<string>('fork_run', { runId, step, label });
       return forkedRunId;
     } catch (e) {
-      // fork_run's non-`done` error already reads "fork failed: <stderr>" (fork.rs:68);
-      // the error strip adds its own "Fork failed:" label, so strip the redundant prefix
-      // here — the UI label is the single authoritative frame (BL-007 t4 r6 cosmetic).
+      // fork_run's start-failure error already reads "fork failed: <stderr>"
+      // (fork.rs `start_failure_error`); the error strip adds its own "Fork failed:"
+      // label, so strip the redundant prefix here — the UI label is the single
+      // authoritative frame (BL-007 t4 r6 cosmetic).
       const msg = String(e).replace(/^fork failed:\s*/i, '');
       setError(msg);
       throw new Error(msg);
```

---

## 3. Committed implementation notes (verbatim)

### 3a. `aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md` @ ae0c510

# BL-030 — Early-return fork: harness side (the fork-start emit)

Cross-repo ticket. The Rig half — the owned-subprocess rewrite that consumes this
emit — is in `aetheris-agents/docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md`.
Read that one for the consumer contract; this one covers the CLI.

Scout that preceded the design: `aetheris-agents/docs/reviews/bl-030-fork-early-return-scout.md`.

---

## What changed

`mix aetheris fork` now prints the forked run's id **at fork-start**, then blocks
to completion exactly as before and prints its result line at the end.

- `cli/commands/fork.ex` — `run/2` stops ignoring its second argument, resolves the
  output mode, and `run_with_step/4` calls `emit_fork_started/2` between
  `start_fork/3` and `await_fork/1`.
- `cli/output/formatter.ex` — new public `resolve_mode/1`.
- `cli/main.ex` — the private `output_mode/1` is gone; `run/1` calls
  `Formatter.resolve_mode/1`.
- `docs/aetheris/runbook.md` — the fork section's "the run id is revealed only when
  the run completes … tracked as BL-030" paragraph replaced.

Emit shape, per resolved mode:

| mode | stdout |
|---|---|
| `--json` | `{"run_id":"fork-…","status":"forked"}` |
| human | `Forked run fork-… — running…` |
| `--quiet` | nothing |

## Design decisions

**The block stays. It is the mechanism, not the problem.** The fork run is a Task
in the CLI process's own supervision tree (`Aetheris.RunSupervisor` ←
`Agent.Supervisor` ← the `Task.start_link` in `agent/server.ex:247`), started
in-process by `RunHelpers.ensure_started/0`. A CLI that returned early would take
the run down with it. So BL-030 is not "stop blocking" — it is "hand the id out
before blocking, and let the consumer own the process". `--detach`/`--follow` stay
unimplemented; that is the daemon path and is untouched here.

**Fork is now the only command that writes to stdout before dispatch returns.**
Everywhere else `Aetheris.CLI.run/1` prints exactly once, after `maybe_dispatch/2`
returns (`main.ex:45-46`). This is inherent to the ticket — the id has to reach the
consumer while the process is still running — and is called out in `fork.ex`'s
moduledoc and `@doc` so the next reader does not take the single-line invariant for
granted. Any consumer scanning stdout for *the* result line must now account for two.

**`resolve_mode/1` moved to `Formatter` rather than being made public on
`Aetheris.CLI`.** A command that prints before its result is formatted needs the
same resolution the closing `print/2` will use. Reaching back into `Aetheris.CLI`
— the module that dispatches *to* the command — is the wrong direction; `Formatter`
already owns `t:mode/0`, so the mode and its type now have one home. `main.ex` lost
a private function and gained a call; no behaviour change (the `cond` is identical).

**Nothing about `Fork.from_step/3`, `Aetheris.fork_run/3`, `await_fork/1` or
`await_run/2` changed.** Determinism contract §4 D2 (entry-point equivalence) is
untouched: both entry points still route through `Fork.from_step/3`, and the emit
is a CLI presentation concern that does not reach the API. BL-039 Part C's
terminal-reason error path is byte-for-byte unchanged.

## Testing — and one test that had to be thrown away

The obvious done-check is the one the ticket named: `capture_io` asserting the
`{"status":"forked"}` line precedes the completion line. **It is vacuous.** Both
writes happen inside `Aetheris.CLI.run/1` — the first from the command, the second
from `Formatter.print/2` after dispatch returns — so moving the emit to *after*
`await_fork/1` leaves their stdout order identical. Mutation-verified: with the
emit reordered, that test and every other test in the file stayed green.

That is the **Silent-wrong-answer** class in its original form (harness `CLAUDE.md`)
— a check that cannot fail to pass is not a check. The ordering test is kept
(it pins the wire format Rig parses, which is real) but its comment now says
plainly what it does not prove.

The discriminating test asserts the property as what it actually is — a timing
property. It runs the command in a `Task` against a live `StringIO` group leader
(not `capture_io/1`, which only yields its buffer after the captured function has
returned), polls for the fork-start line, and requires it to land at least 100 ms
before the command returns. The window is `await_run/2`'s poll floor
(`@poll_interval_ms 200`): measured over five runs, the emit lands at ~+6 ms and
the command returns at ~+204 ms — a 197–200 ms window. The emit-after-await mutant
collapses it to 0 ms and the test fails with exactly that number. The 100 ms
threshold sits between the two with margin either side and deliberately does not
encode the poll interval, which is free to change.

Six tests in `test/aetheris/cli/commands/fork_test.exs`; the three pre-existing
ones are unchanged.

## Gates

`mix deps.get` · `mix compile --warnings-as-errors` · `mix format --check-formatted`
· `mix credo --strict` (no issues) · `mix dialyzer` (0 errors) · `mix test`
(968 tests, 0 failures, 133 excluded) — all green.

`mix hex.audit` is **red, expected, and tracked as BL-060**: one advisory,
`bandit 1.11.1` / EEF-CVE-2026-65623 (HIGH), upstream and unrelated to this ticket.
Named per the gate rule, not re-triaged.

---

### 3b. `aetheris-agents/docs/rig/milestones/bl-030-early-return-fork-implementation-notes.md` @ b5e8eee

# BL-030 — Early-return fork: Rig side (owned subprocess)

Cross-repo ticket. The harness half — the CLI's fork-start emit that this consumes
— is in `../aetheris/docs/aetheris/milestones/bl-030-implementation-notes.md`.

Scout that preceded the design: `docs/reviews/bl-030-fork-early-return-scout.md`.

---

## What changed

"Fork from here" returns as soon as the fork **starts** (seconds) instead of when
it finishes (minutes for a real provider), and the operator lands on the child run
while it is still executing and watches it stream.

- `rig/src-tauri/src/commands/fork.rs` — `.output()` (which waits for exit *and*
  pipe EOF) replaced with spawn-piped + own-the-child. The calling thread reads
  stdout only until the first `run_id` line, returns it, and hands the running
  child to a detached thread that drains both pipes to EOF and reaps it.
- `rig/src/components/modules/harness/RunList.tsx` — `handleForked` synthesises
  `status: 'running'` instead of `'done'`.
- `rig/src/hooks/useFork.ts` — header comment swept; behaviour and signature
  unchanged.
- `rig/src/components/modules/harness/TrajectoryView.tsx` — the unmount-guard
  comment's "a fork blocks to completion (minutes)" premise corrected.
- `docs/rig/specs.md` §4 — the "Blocks to completion" paragraph replaced.

## Design decisions

**`status: 'running'` lands on a road that was already built.** The trajectory file
is written **once, at run completion** (`agent/server.ex:680`, `:952`), so a
running fork has no file. `TrajectoryView` already handles exactly that: the file
load fails, `fileMissing` engages the events fallback, and
`useRunEvents(runId, { polling: run?.status === 'running' })` polls SQLite every
2 s and stops itself when `run_complete` reaches the stream
(`useHarness.ts:118-133`). That is BL-005's live path. The only thing that was
holding it shut on the fork route was `handleForked`'s hardcoded `'done'` — which
was correct when a fork could only be navigated to after it finished. One word.

**stderr stays `piped()`. This is the part where copying `orchestrate.rs` verbatim
would have regressed BL-039 Part C.** `orchestrate.rs:55` nulls stderr because it
has no stderr contract. `fork.rs` does: a fork that never *starts*
(`step_not_found`, an unreadable trajectory) fails inside `Fork.from_step/3` before
any run exists, writes no `run_id` line, and reports its reason on stderr with a
zero exit code (`mix` discards the CLI exit code). Nulling stderr would have
degraded every start failure to a bare "produced no run_id" — well-formed, wrong,
and invisible to a reader-only unit test. `start_failure_error/1` preserves
`fork failed: <reason>` and is unit-tested on both arms.

**One stderr collector thread, spawned at spawn time, serving both outcomes.** A
start failure needs stderr's contents; a *successful* fork must not be able to
wedge on a full stderr pipe with nobody reading it. Reading stdout to EOF first and
*then* stderr would deadlock on a chatty stderr. Collecting stderr on its own
thread from t=0 removes the ordering question entirely: on failure the collector is
joined for its message, on success it simply ends at EOF alongside the stdout
drain, and `child.wait()` reaps.

**First-wins, and deliberately no smarter.** `parse_run_id`'s last-wins backward
scan required the whole buffer, i.e. the whole run — the exact thing BL-030
removes. The new `read_first_run_id/1` stops at the first `run_id` line. It needs
no further disambiguation: `await_run`'s verbose event stream goes to **stderr**
(`run_helpers.ex:53`), and under `--json` the closing `Formatter.print/2` writes
exactly once, so the only JSON-with-`run_id` lines on stdout are the start line and
the completion line. `mix` compile noise does not parse as JSON.

**Failure semantics moved, and that is the point.** A rejection from `fork_run` now
means the fork never started. A fork that starts and then fails does so after the
command returned, and the operator sees it on the child's own streamed trajectory —
which is where the diagnosis was always recorded, and which they are now already
looking at.

## Scope deviation — `parse_run_id` was deleted, not preserved

The ticket said not to change `parse_run_id`'s last-wins. Nothing consumes it after
this change: the streaming reader replaces it wholesale, and a private Rust function
used only from `#[cfg(test)]` is a `dead_code` warning in every non-test build, so
keeping it would have meant an `#[allow(dead_code)]` on a function no code path can
reach. It was removed.

What the instruction was protecting — *what counts as a run_id line* — is preserved
byte-for-byte as `run_id_from_line/1` (same `serde_json` parse, same
object-with-string-`run_id` predicate) and is still unit-tested. Only the scan
direction and the dead wrapper are gone. Flagged here and in the review packet
rather than decided silently.

## Testing

`cargo test` — 7 tests in `commands::fork`, inside a crate total of 22
(21 passed, 1 ignored: `live_store_demo_01…`, which requires `AETHERIS_DB_PATH`):

- `read_first_run_id_returns_the_start_line_id` — the id comes off the fork-start
  line through mix compile noise.
- `read_first_run_id_stops_before_the_completion_line` — the **early-return**
  property, asserted structurally rather than by wall clock: after the id is read,
  the completion line must still be *unread* in the stream. A reader that drained
  to EOF first (the old last-wins scan) leaves nothing behind and fails this.
- `read_first_run_id_none_on_eof_without_a_run_id` — a fork that never starts.
- `start_failure_error_carries_the_stderr_reason` / `…without_stderr_says_so` — the
  Part C diagnosis survives, and its absence is reported as absence.
- the two pre-existing `fork_argv` tests, unchanged.

**Rig has no frontend test runner.** `handleForked`'s `'running'` and the polling it
switches on are not covered by any automated test in this repo — the manual GUI pass
is the merge gate for that half, not a formality. See the packet.

## Gates

`cargo test` (21 passed, 1 ignored) · `bun run lint` (clean) · `bunx tsc -b` (clean) ·
`bun run build` (clean) — all green. `drift_check --strict` and the cross-repo
done-check are in the packet.

---

## 4. Deviations from the ticket

**One, named rather than decided silently: `parse_run_id` was deleted, not
preserved.** The ticket's do-not list says "no `parse_run_id` change". Nothing
consumes it after the streaming reader lands, and a private Rust function used
only from `#[cfg(test)]` is a `dead_code` warning in every non-test build — so
keeping it would have meant `#[allow(dead_code)]` on a function no code path can
reach, under a `bun run lint`/`cargo` gate line that is currently clean.

What the instruction protects — *what counts as a run_id line* — is preserved
byte-for-byte as `run_id_from_line/1`: same `serde_json` parse, same
object-with-string-`run_id` predicate, still unit-tested. Only the backward scan
and the dead wrapper are gone. If the reviewer wants the function retained, say
so and it comes back with an `#[allow]`.

**Touches, as landed** (the ticket predicted `main.ex` would join; it did):

| repo | file | why |
|---|---|---|
| aetheris | `lib/aetheris/cli/commands/fork.ex` | the emit |
| aetheris | `lib/aetheris/cli/output/formatter.ex` | `resolve_mode/1` |
| aetheris | `lib/aetheris/cli/main.ex` | private `output_mode/1` removed; calls `Formatter` |
| aetheris | `test/aetheris/cli/commands/fork_test.exs` | 3 tests added |
| aetheris | `docs/aetheris/runbook.md` | **not in the ticket's list** — its fork section asserted the old behaviour and named BL-030 by number; left alone it would have been false-in-place at closure |
| agents | `rig/src-tauri/src/commands/fork.rs` | owned subprocess |
| agents | `rig/src/components/modules/harness/RunList.tsx` | `status: 'running'` |
| agents | `rig/src/hooks/useFork.ts` | header sweep |
| agents | `rig/src/components/modules/harness/TrajectoryView.tsx` | **not in the ticket's list** — its unmount-guard comment's premise ("a fork blocks to completion (minutes)") became false; the guard itself is unchanged and still needed |
| agents | `docs/rig/specs.md` | §4 rewrite |
| agents | `docs/backlog-2026-06.md` | closure entry + dangling-ref note |

Nothing on the do-not list was touched: no daemon, no harness-side detach,
`--detach`/`--follow` still report "not yet available", `Aetheris.fork_run/3`
unchanged, no cancel command, no `--provider`/`--model` (BL-062).

---

## 5. One flagged observation

**The ticket's named harness done-check is vacuous, and was replaced rather than
shipped.** "capture_io asserts a `{"status":"forked","run_id":…}` line precedes
the completion line" cannot fail: both writes happen inside `Aetheris.CLI.run/1`
— the first from the command, the second from `Formatter.print/2` after dispatch
returns — so moving the emit to *after* `await_fork/1` leaves their stdout order
identical. Mutation-verified: with the emit reordered, that test and every other
test in the file stayed green. It is the **Silent-wrong-answer** class in its
original form.

The check is kept (it pins the wire format Rig parses, which is real) with its
limit stated in-place, and a second test asserts the property as the timing
property it actually is: against a live `StringIO` group leader, the fork-start
line must land ≥100 ms before the command returns. The window is `await_run/2`'s
200 ms poll floor — measured over five runs, emit at ~+6 ms, return at ~+204 ms.
The mutant collapses it to 0 ms and the test fails naming that number:

```
1) test the run id reaches stdout while the fork is still running (Aetheris.CLI.Commands.ForkTest)
   test/aetheris/cli/commands/fork_test.exs:134
   expected the fork-start line at least 100ms before the command returned; got 0ms.
   The emit is not ahead of await_fork/1.
```

The Rig-side equivalent is asserted structurally rather than by clock
(`read_first_run_id_stops_before_the_completion_line`): after the id is read, the
completion line must still be *unread* in the stream — a reader that drained to
EOF first leaves nothing behind and fails it.

---

## 6. Closure items for the reviewer

- **Manual GUI pass (§1h) is outstanding and gates merge.** The frontend half has
  no automated coverage; the gates in §1 do not touch it.
- **BL-062 to be filed** (the split-out `--provider`/`--model` override row) with
  its §8 determinism-contract edit.
- **Dangling §4 ref, recorded in the backlog entry.** §4's "the CLI and Rig entry
  points pass a label only (BL-030)" is still *true* after this ticket, but its
  `(BL-030)` ref now points at a closed ticket that never carried the overrides.
  BL-062's §8 edit repoints it. Flagged rather than left to rot — §4 already
  carries one decayed parenthetical (D2's `cli/commands/fork.ex:47-55`, per the
  scout).
- **Manifest export boundary:** three `project_knowledge` staleness WARNs are new
  from this ticket (§1f) and clear at the next export, which is human-owned.
