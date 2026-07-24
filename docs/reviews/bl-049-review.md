# BL-049 — review packet

**Ticket:** BL-049 — a `run_command` step can essentially never verify: `duration_ms` is
inside the compared payload.
**Commit:** harness `13ff59c` (on `main`, **push held**). Agents-side commit follows.
**Base:** harness `9d994fd`, agents `4af336e` — the ticket's watermark, both clean at start.
**Contract refs re-verified at HEAD `9d994fd`**, read from
`../aetheris/docs/aetheris/determinism-contract.md`. The project-knowledge export is stale
(pre-BL-025/042) and was not used.

---

## 1. Done-check output

### 1a. Before-fix baseline — the defect, measured

Six verifies of one recorded hermetic `python3 -c 'print("bl049")'` trajectory, against
unmodified `lib/` at `9d994fd`:

```
recorded: {"duration_ms":10,"exit_code":0,"stderr":"","stdout":"bl049\n"}

run 1  status: :output_mismatch  actual: {"duration_ms":13,"exit_code":0,"stderr":"","stdout":"bl049\n"}
run 2  status: :output_mismatch  actual: {"duration_ms":12,"exit_code":0,"stderr":"","stdout":"bl049\n"}
run 3  status: :output_mismatch  actual: {"duration_ms":9,"exit_code":0,"stderr":"","stdout":"bl049\n"}
run 4  status: :output_mismatch  actual: {"duration_ms":11,"exit_code":0,"stderr":"","stdout":"bl049\n"}
run 5  status: :verified         actual: {"duration_ms":10,"exit_code":0,"stderr":"","stdout":"bl049\n"}
run 6  status: :output_mismatch  actual: {"duration_ms":11,"exit_code":0,"stderr":"","stdout":"bl049\n"}
```

Five of six, the sixth coinciding — the ticket's measurement reproduced exactly.
`stdout`, `stderr` and `exit_code` are byte-identical in all six rows; only `duration_ms`
moves.

Same trajectory shape driven through the committed test, still against unmodified `lib/`:

```
  1) test a pre-fix recording of a reproducing run_command verifies on every run (Aetheris.Execution.VerifyVerdictTest)
     test/aetheris/execution/verify_verdict_test.exs:49
     verdict is not deterministic across 6 runs: [:output_mismatch, :output_mismatch,
     :output_mismatch, :output_mismatch, :output_mismatch, :output_mismatch]
     code: assert statuses == List.duplicate(:verified, @runs),
     stacktrace:
       test/aetheris/execution/verify_verdict_test.exs:60: (test)

Finished in 0.1 seconds (0.00s async, 0.1s sync)
1 test, 1 failure
```

### 1b. After-fix — both record eras, six runs each

```
$ mix test test/aetheris/execution/verify_verdict_test.exs \
           test/aetheris/execution/volatile_metadata_test.exs \
           --include requires_worker --trace

Running ExUnit with seed: 306216, max_cases: 1
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]

Aetheris.Execution.VolatileMetadataTest [test/aetheris/execution/volatile_metadata_test.exs]
  * test fields/0 — the single definition the worker-native envelope lifts every volatile field out of its output (4.6ms) [L#95]
  * test split/1 a git_* response shape splits the same way (5.7ms) [L#42]
  * test Loop.exec_server_payload/2 the transcript message is the recorded output, so a fork cannot diverge (3.8ms) [L#121]
  * test strip/1 — the read-side normalizer is idempotent (0.01ms) [L#61]
  * test fields/0 — the single definition duration_ms is volatile (0.00ms) [L#86]
  * test split/1 the deterministic portion is the output blob without the volatile fields (0.02ms) [L#38]
  * test Loop.exec_server_payload/2 records the deterministic output and puts the duration in the envelope (0.01ms) [L#110]
  * test Loop.exec_server_payload/2 output the exec server did not shape passes through unchanged (0.00ms) [L#130]
  * test strip/1 — the read-side normalizer passes through a blob that carries no volatile field, byte for byte (0.01ms) [L#68]
  * test strip/1 — the read-side normalizer passes through truncated, non-JSON and nil output without raising (0.01ms) [L#73]
  * test strip/1 — the read-side normalizer a pre-fix recording normalizes byte-identically to a post-fix recording (0.02ms) [L#51]
  * test split/1 two responses differing only in duration_ms compare byte-identical (0.01ms) [L#23]

Aetheris.Execution.VerifyVerdictTest [test/aetheris/execution/verify_verdict_test.exs]
  * test a post-fix recording of a reproducing run_command verifies on every run [L#65]
[sandbox] entered user+mount namespaces (uid=1000, gid=1000); network namespace not requested
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
  * test a post-fix recording of a reproducing run_command verifies on every run (121.3ms) [L#65]
  * test a pre-fix recording of a reproducing run_command verifies on every run [L#49]
[sandbox] entered user+mount namespaces (uid=1000, gid=1000); network namespace not requested
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
  * test a pre-fix recording of a reproducing run_command verifies on every run (99.3ms) [L#49]

Finished in 0.2 seconds (0.06s async, 0.2s sync)
14 tests, 0 failures
```

Six contained (netns) re-executions per arm, twelve in total, all `:verified`. Each run also
asserts `verified: 1`, `served: 0`, a non-empty actual output containing
`"stdout":"bl049\n"`, and `actual_output == recorded_output` — a served step cannot fail, so
it must not be allowed to pass as a fix.

### 1c. BL-042's `--allow-effects` arm, tightened `!= :served` → `== :verified`

```
$ for i in 1 2 3 4 5 6; do mix test test/aetheris/execution/verify_effects_test.exs \
                                    --include requires_worker --seed $i; done
seed 1: 5 tests, 0 failures
seed 2: 5 tests, 0 failures
seed 3: 5 tests, 0 failures
seed 4: 5 tests, 0 failures
seed 5: 5 tests, 0 failures
seed 6: 5 tests, 0 failures
```

### 1d. Gates

```
$ mix format --check-formatted
FORMAT OK

$ mix compile --warnings-as-errors
Compiling 6 files (.ex)
Generated aetheris app

$ mix credo --strict
Analysis took 2.6 seconds (0.1s to load, 2.5s running 69 checks on 222 files)
1991 mods/funs, found no issues.

$ mix dialyzer
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done in 0m4.61s
done (passed successfully)

$ mix test
Finished in 88.5 seconds (2.7s async, 85.7s sync)
921 tests, 0 failures, 122 excluded

$ mix hex.audit
No retired or security advisory packages found
```

`mix test --include requires_worker` — **known-red, tracked as BL-048**, named rather than
re-triaged:

```
Finished in 93.3 seconds (3.9s async, 89.3s sync)
921 tests, 15 failures, 65 excluded
```

Fourteen of those fifteen are the clean-tree set at this base, unchanged. Note the count
differs from BL-048's row, which recorded **15 on a clean tree at `8021a59`**: at `9d994fd`
a clean tree gives **14**. The set moved between those commits; that drift is BL-048's to
triage, not re-triaged here. The fifteenth failure in the BL-049 run is new and is **not
BL-049's** — see §3.

### 1e. `drift_check --strict`, post-commit

**0 FAIL.** The three WARNs are all `project_knowledge` manifest staleness — the standing
exemption in CLAUDE.md, which is why `--strict` still exits 0. They are named, not chased.
The `current=` hash in the backlog WARN names HEAD at run time; the commit that records
this output is necessarily its successor, so that field is always one commit behind by
construction.

```
$ python3 scripts/drift_check.py --strict
Rig doc-drift checker — 8 check(s)

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
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=f0df85a current=bf7b9b0
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=a935038 current=8021a59
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=9b2b102 current=9d994fd

Summary: 7 PASS  0 FAIL  3 WARN  7 INFO

exit=0
```

---

## 2. What changed

```
 .../milestones/bl-049-implementation-notes.md      | 147 +++++++++++++++++++
 lib/aetheris/execution/loop.ex                     |  48 ++++++-
 lib/aetheris/execution/tool_schema/registry.ex     |   4 +-
 lib/aetheris/execution/verifier.ex                 |  33 ++++-
 lib/aetheris/execution/volatile_metadata.ex        |  93 ++++++++++++
 lib/aetheris/worker/client.ex                      |   6 +
 test/aetheris/execution/verify_effects_test.exs    |  30 ++--
 test/aetheris/execution/verify_verdict_test.exs    | 160 +++++++++++++++++++++
 test/aetheris/execution/volatile_metadata_test.exs | 139 ++++++++++++++++++
 9 files changed, 642 insertions(+), 18 deletions(-)
```

`Aetheris.Execution.VolatileMetadata` owns `@volatile_fields`. `Loop.exec_server_payload/2`
splits them into the step envelope when recording any `aetheris_exec`-routed tool.
`Verifier` calls the same strip on the re-executed output *and*, via `normalize_recorded/2`,
on the recorded one before comparing. The verifier holds no field list of its own — that is
what separates this from the rejected "exclude volatile fields in the compare".

**Why the read side is in scope at all.** Trajectory events are immutable (critical rule #1),
so every trajectory recorded before `13ff59c` carries `duration_ms` inside the recorded blob
permanently. A parse-layer-only fix would have satisfied the invariant for new records while
turning the old corpus's 1-in-6 flap into a deterministic `:output_mismatch` — a confident
wrong verdict, which is worse than a flaky one.

**Consequence, stated rather than buried:** the agent no longer sees `duration_ms` in an
exec-server tool result. `payload["output"]` *is* the transcript content (`fork.ex:107`
rebuilds a fork's transcript from it), so the recorded and model-visible values cannot
diverge without breaking fork replay. `registry.ex:47,138` advertised the field to the model
and are corrected. This is exactly the worker-native behaviour, where `duration_ms` has
always been envelope-only.

### The two enumerations the ticket required before editing

**(i) Volatile field set = `{duration_ms}` exactly.** `handle_run_command`
(`main.rs:477-482`, and the not-permitted branch `:442-447`) → `{stdout, stderr, exit_code,
duration_ms}`; `format_git_result` (`main.rs:947-951`, all eleven `git_*`) → `{output,
exit_code, duration_ms}`; `missing_arg_error_msg` (`main.rs:685-694`) → `{error}`, nothing
volatile. `runner::RunResult` (`runner.rs:38-43`) has four fields and no other timing, pid,
or host measurement. The JSON-RPC envelope's `id` never crosses into Elixir — the worker
returns only the collected text content (`mcp.rs:97,111`). `mcp_http_list_tools` /
`mcp_http_call` are exec-server tools but are not in `Loop`'s `@exec_server_tools` and are
reached under an external `server_id`, so the new clause does not match them.

**(ii) No consumer parses `duration_ms` out of the blob** — in either repo. What the
enumeration did turn up: `fork.ex:101-108` (load-bearing, above); `run_helpers.ex:257`, which
read the envelope key with a `0` default and was therefore rendering `ok (0ms)` for every
exec-server step and now renders the real duration; `registry.ex:47,138` (corrected);
`docs/rig/specs.md:550`, which already declares `duration_ms` on `tool_result`, so no drift
either way; and no reader at all in `rig/src` or `rig/src-tauri/src`.

### Deviation from the ticket's sketch

The ticket said to extract the strip *out of* `parse_execute_response/1`. Nothing there is
extractable: that function splits **sibling keys of an already-decoded map**, while the
exec-server case removes keys from a **JSON object embedded in the `output` string**.
Different shapes, different operations — a function serving both would be a coincidence of
naming, not of behaviour.

The invariant binds, not the sketch. `VolatileMetadata.fields/0` is the single definition,
and the worker-native path is bound to it by a **tripwire test** rather than by shared code:
`VolatileMetadataTest` asserts every field in `fields/0` is lifted into the worker-native
envelope, so adding a second volatile field without lifting it there fails loudly instead of
silently re-admitting it to the compared blob through the other path.

---

## 3. Off-territory gate finding — filed as BL-050, not fixed here

`mix test --include requires_worker` gains one entry beyond BL-048's set:
`RunOverlayTest`, "overlay dirs are created and upper is empty after a read-only worker
session".

**Mechanism, read from source.** `run_overlay_test.exs:38` asserts `File.dir?(upper)`
immediately after `Client.start_link` returns. `start_link` returns as soon as the `ready`
handshake arrives (`client.ex`, `init/1`), but the worker writes `ready` at `main.rs:71-74`
and only *then* runs `sandbox::mount_overlay` (`main.rs:79-94`), which is what creates
`upper`/`work`/`merged` (`sandbox.rs:242-244`). The test synchronises on a handshake that
does not cover the side effect it asserts. Latent since BL-042 moved namespace entry — and
with it the `ready` write — ahead of the rest of init.

**Not BL-049's, demonstrated rather than asserted.** Three-way run:

| tree | result | failing set vs clean |
|---|---|---|
| clean `9d994fd` | 907 tests, 14 failures | — |
| BL-049 `lib/` changes, new test files removed | 907 tests, 14 failures | **byte-identical** |
| BL-049 full | 921 tests, 15 failures | +`RunOverlayTest` only |

The `lib/` changes alone reproduce the clean tree exactly. The new tests add worker churn
ahead of it and it loses the race more often — 5 of 8 seeds when paired directly, 0 of 3 in
isolation, 0 under `--trace` (`max_cases: 1`). Filed as **BL-050** with the mechanism and a
recommended fix (report overlay establishment in the handshake, as BL-042 did for
`network_namespace`; a deadline-poll is the acceptable alternative; not `Process.sleep`).

---

## 4. §5 contract edits — drafted, not landed

Both edits are in `docs/reviews/bl-049-contract-draft.md`, verbatim before/after, awaiting
ratification per §8. They are **not** in `13ff59c`; the contract file is untouched.

- **(a)** replaces the `run_command` residual-limitation bullet with a statement of what the
  comparison ranges over, resolved unqualified across both record eras. The draft carries the
  dependency note: without the read-side normalization this would have to hedge to "resolved
  for records at or after `13ff59c`".
- **(b)** "The opt-in" — `--allow-effects` also waives the netns. Completeness gap noticed at
  BL-042, folded here rather than spending a standalone §8 cycle.

The draft also records what it deliberately does **not** change, including §3's verify row:
"output by value equality" remains exactly true, since BL-049 changes what the recorded
output *is*, not how it is compared.

---

## 5. Full diff — `lib/`

```diff
commit 13ff59cbdf7682b70dde46bb670944be7d9c3f2e
Author: Vishal Honnatti <vishal@bitloka.com>
Date:   Fri Jul 24 07:38:08 2026 +0530

    BL-049: volatile execution metadata is not part of the verify compare
    
    The exec server embeds `duration_ms` inside the tool-output blob, and verify
    compares that blob by value equality — so a perfectly reproducible
    `run_command` reported `:output_mismatch` on timing alone (measured: five of
    six runs; the sixth coincided). Worker-native tools never had this: their
    `duration_ms` is a sibling of `output`, lifted at the parse layer.
    
    `Aetheris.Execution.VolatileMetadata` is now the single definition of which
    fields are volatile. `Loop.exec_server_payload/2` splits them into the step
    envelope when recording, and `Verifier` strips them from the re-executed
    output *and* from the recorded one before comparing.
    
    The read side is not optional. Trajectory events are immutable, so every
    trajectory recorded before this commit carries `duration_ms` in the recorded
    blob permanently; normalizing only the re-executed side would have traded a
    nondeterministic verdict for a deterministically wrong one on that corpus.
    It is reuse rather than a compare-side policy: the verifier holds no field
    list of its own.
    
    `registry.ex` no longer advertises `duration_ms` to the model, which is now
    true — `payload["output"]` is the transcript content (`fork.ex`), so the
    recorded and model-visible values cannot diverge without breaking fork replay.
    
    Verdict stability is asserted six times per arm, over both record eras, with
    `verified: 1`/`served: 0` guards so a served step cannot pass as a fix. The
    BL-042 `--allow-effects` arm is tightened from `!= :served` to `== :verified`.
    
    Refs: determinism-contract §5 (edits drafted for §8 approval), BL-042, BL-048.
    
    Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

diff --git a/lib/aetheris/execution/loop.ex b/lib/aetheris/execution/loop.ex
index 77e68e6..ca88765 100644
--- a/lib/aetheris/execution/loop.ex
+++ b/lib/aetheris/execution/loop.ex
@@ -31,13 +31,19 @@ defmodule Aetheris.Execution.Loop do
     LoopDetector,
     Pricing,
     ToolSchema.AnthropicTranslator,
-    ToolSchema.Registry
+    ToolSchema.Registry,
+    VolatileMetadata
   }
 
   alias Aetheris.{RunConfig, Store, Trajectory.Event, Trajectory.Log, WaitRegistry}
   alias Aetheris.Worker.Client, as: WorkerClient
   require Logger
 
+  # The internal exec server, spawned at worker startup before seccomp. Its tools are
+  # routed as MCP calls but are ours, so their response shape is known — which is what
+  # lets `exec_server_payload/2` split volatile metadata out of the recorded output.
+  @exec_server_id "aetheris_exec"
+
   @doc """
   Runs the execution loop for the given `config`.
 
@@ -529,6 +535,13 @@ defmodule Aetheris.Execution.Loop do
   defp dispatch_mcp_tool(nil, _server_id, _tool_name, _tool_input),
     do: {:error, "Worker client not available for MCP tool call"}
 
+  defp dispatch_mcp_tool(worker_pid, @exec_server_id = server_id, tool_name, tool_input) do
+    case WorkerClient.call_mcp_tool(worker_pid, server_id, tool_name, tool_input) do
+      {:ok, output} -> exec_server_payload(tool_name, output)
+      {:error, reason} -> {:error, reason}
+    end
+  end
+
   defp dispatch_mcp_tool(worker_pid, server_id, tool_name, tool_input) do
     case WorkerClient.call_mcp_tool(worker_pid, server_id, tool_name, tool_input) do
       {:ok, output} ->
@@ -545,6 +558,35 @@ defmodule Aetheris.Execution.Loop do
     end
   end
 
+  @doc """
+  Builds the recorded payload and the transcript message for an exec-server tool result.
+
+  The exec server embeds `duration_ms` in its output blob; this lifts it into the step
+  envelope so the recorded `"output"` is the deterministic portion only — the same shape
+  `Worker.Client.parse_execute_response/1` produces for worker-native tools, and the shape
+  `Aetheris.Execution.Verifier` compares (`docs/aetheris/determinism-contract.md` §5,
+  BL-049).
+
+  The payload's `"output"` and the returned message are the *same value*, deliberately:
+  `Aetheris.Execution.Fork` rebuilds a fork's transcript from the recorded `"output"`, so
+  a message that differed from what was recorded would make a fork diverge from the run it
+  forked. The agent therefore no longer sees `duration_ms` in an exec-server tool result —
+  exactly as it never saw it for a worker-native one.
+  """
+  @spec exec_server_payload(String.t(), String.t()) :: {:ok, map(), String.t()}
+  def exec_server_payload(tool_name, output) do
+    {deterministic, volatile} = VolatileMetadata.split(output)
+
+    payload = %{
+      "tool_name" => tool_name,
+      "output" => deterministic,
+      "fs_hash" => nil,
+      "duration_ms" => Map.get(volatile, "duration_ms")
+    }
+
+    {:ok, payload, deterministic}
+  end
+
   defp dispatch_tool(nil, tool_name, tool_input) do
     case Echo.execute(%{tool_name: tool_name, tool_input: tool_input}) do
       {:ok, result} ->
@@ -968,7 +1010,7 @@ defmodule Aetheris.Execution.Loop do
     end
   end
 
-  # Tools routed through the internal exec server (spawned at worker startup before seccomp).
+  # Tools routed through the internal exec server (@exec_server_id).
   @exec_server_tools ~w[
     run_command git_status git_diff git_add git_commit
     git_diff_staged git_log git_show git_checkout git_cherry_pick git_cherry_pick_control
@@ -999,7 +1041,7 @@ defmodule Aetheris.Execution.Loop do
   defp build_exec_server_index(tools) do
     tools
     |> Enum.filter(&(&1 in @exec_server_tools))
-    |> Map.new(fn tool -> {tool, %{source: :mcp, server_id: "aetheris_exec"}} end)
+    |> Map.new(fn tool -> {tool, %{source: :mcp, server_id: @exec_server_id}} end)
   end
 
   defp merge_mcp_server_tools(server_config, worker_client_pid, schemas_acc, index_acc) do
diff --git a/lib/aetheris/execution/tool_schema/registry.ex b/lib/aetheris/execution/tool_schema/registry.ex
index e4369a2..2a33087 100644
--- a/lib/aetheris/execution/tool_schema/registry.ex
+++ b/lib/aetheris/execution/tool_schema/registry.ex
@@ -44,7 +44,7 @@ defmodule Aetheris.Execution.ToolSchema.Registry do
     "run_command" => %{
       "name" => "run_command",
       "description" =>
-        "Execute a shell command in the sandboxed workspace. Returns stdout, stderr, exit_code, and duration_ms.",
+        "Execute a shell command in the sandboxed workspace. Returns stdout, stderr, and exit_code.",
       "input_schema" => %{
         "type" => "object",
         "properties" => %{
@@ -135,7 +135,7 @@ defmodule Aetheris.Execution.ToolSchema.Registry do
     "git_diff_staged" => %{
       "name" => "git_diff_staged",
       "description" =>
-        "Show staged changes (what will be committed). Returns output, exit_code, and duration_ms.",
+        "Show staged changes (what will be committed). Returns output and exit_code.",
       "input_schema" => %{
         "type" => "object",
         "properties" => %{
diff --git a/lib/aetheris/execution/verifier.ex b/lib/aetheris/execution/verifier.ex
index 4c264fb..2daea9c 100644
--- a/lib/aetheris/execution/verifier.ex
+++ b/lib/aetheris/execution/verifier.ex
@@ -10,7 +10,7 @@ defmodule Aetheris.Execution.Verifier do
   restore re-execution of everything; that re-issues real network and MCP effects.
   """
 
-  alias Aetheris.Execution.{EffectClass, VerifyReport}
+  alias Aetheris.Execution.{EffectClass, VerifyReport, VolatileMetadata}
   alias Aetheris.Trajectory.{Event, File}
   alias Aetheris.Worker.Client
 
@@ -227,7 +227,10 @@ defmodule Aetheris.Execution.Verifier do
   defp verify_step(worker_pid, {called_event, result_event}) do
     tool_name = called_event.payload |> Map.fetch!("tool_name")
     tool_input = called_event.payload |> Map.fetch!("tool_input")
-    recorded_output = recorded_result(result_event.payload)
+
+    recorded_output =
+      result_event.payload |> recorded_result() |> then(&normalize_recorded(tool_name, &1))
+
     recorded_fs_hash = Map.get(result_event.payload, "fs_hash")
 
     case reexecute(worker_pid, tool_name, tool_input) do
@@ -280,7 +283,12 @@ defmodule Aetheris.Execution.Verifier do
     case Client.call_mcp_tool(worker_pid, "aetheris_exec", tool_name, tool_input) do
       # The exec server makes no filesystem-hash claim, matching how a live run
       # records these steps (`dispatch_mcp_tool/4` writes `"fs_hash" => nil`).
-      {:ok, output} -> {:ok, %{output: output, fs_hash: nil}}
+      #
+      # The output is stripped of volatile execution metadata for the same reason a live
+      # run's is: the compare ranges over the deterministic portion only. A live run does
+      # this in `Loop.exec_server_payload/2`; verify cannot reuse it because it calls the
+      # exec server directly, so both call the one shared definition instead.
+      {:ok, output} -> {:ok, %{output: VolatileMetadata.strip(output), fs_hash: nil}}
       {:error, reason} -> {:error, reason}
     end
   end
@@ -289,6 +297,25 @@ defmodule Aetheris.Execution.Verifier do
     Client.execute(worker_pid, %{name: tool_name, input: tool_input})
   end
 
+  # Volatile execution metadata is not part of the compared value
+  # (`Aetheris.Execution.VolatileMetadata`, §5, BL-049). The re-executed side is stripped
+  # above; the recorded side is stripped here, because trajectory events are immutable and
+  # every trajectory recorded before BL-049 carries `duration_ms` inside the recorded blob.
+  # Normalizing only one side would trade a nondeterministic verdict for a deterministically
+  # wrong one on that corpus.
+  #
+  # Deliberately restricted to the exec-server family rather than applied to every recorded
+  # output. Worker-native results never embed volatile metadata — `parse_execute_response/1`
+  # lifts it out at the parse layer — and a `read_file` result that merely *happens* to be a
+  # JSON object carrying a `duration_ms` key is file content, not execution metadata.
+  #
+  # This is not a compare-side field policy: the definition of "volatile" lives in one
+  # place and both sides call it.
+  defp normalize_recorded(tool_name, output) when tool_name in @exec_server_tools,
+    do: VolatileMetadata.strip(output)
+
+  defp normalize_recorded(_tool_name, output), do: output
+
   defp compare_status(recorded_output, actual_output, recorded_fs_hash, actual_fs_hash) do
     cond do
       recorded_output != actual_output -> :output_mismatch
diff --git a/lib/aetheris/execution/volatile_metadata.ex b/lib/aetheris/execution/volatile_metadata.ex
new file mode 100644
index 0000000..227a425
--- /dev/null
+++ b/lib/aetheris/execution/volatile_metadata.ex
@@ -0,0 +1,93 @@
+defmodule Aetheris.Execution.VolatileMetadata do
+  @moduledoc """
+  The single source of truth for which tool-result fields are **volatile execution
+  metadata** — measurements of the execution rather than of what the tool did.
+
+  `docs/aetheris/determinism-contract.md` §5 compares a recorded tool output against a
+  re-executed one by value equality. That compare ranges over the *deterministic portion*
+  of the output: a wall-clock duration says nothing about whether the tool reproduced, so
+  a difference in it must not read as a divergence.
+
+  Worker-native tools already satisfy this at the parse layer — `Worker.Client`'s
+  `parse_execute_response/1` lifts `duration_ms` out of the worker's response into the
+  step envelope, alongside `output` rather than inside it. Exec-server tools did not: the
+  server embeds `duration_ms` *inside* the output blob
+  (`native/aetheris_exec_server/src/main.rs`, `handle_run_command` and
+  `format_git_result`), so it reached the compare and a perfectly reproducible command
+  reported `:output_mismatch` on timing alone (BL-049).
+
+  This module holds the one definition of "volatile" and both sides call it:
+
+    * `Aetheris.Execution.Loop` splits it out when recording an exec-server result, so the
+      volatile value lands in the step envelope and the compared payload is deterministic.
+    * `Aetheris.Execution.Verifier` strips it from the re-executed output *and* from the
+      recorded output before comparing. The read side is not optional: trajectory events
+      are immutable, so every trajectory recorded before BL-049 carries `duration_ms`
+      inside the recorded blob forever. Without normalizing that side too, the fix would
+      merely trade a nondeterministic verdict for a deterministically wrong one.
+
+  This is deliberately *not* a compare-side field policy. The verifier holds no list of
+  its own; it calls `strip/1` here. One definition, two call sites.
+
+  ## Adding a volatile field
+
+  Add it to `@volatile_fields`. The worker-native envelope must lift the same field —
+  `Aetheris.Execution.VolatileMetadataTest` asserts that correspondence, so a field added
+  here without the matching worker-native lift fails loudly rather than silently
+  re-entering the compare through the other path.
+  """
+
+  @volatile_fields ~w[duration_ms]
+
+  @doc """
+  The field names treated as volatile execution metadata.
+  """
+  @spec fields() :: [String.t()]
+  def fields, do: @volatile_fields
+
+  @doc """
+  Splits an exec-server output blob into its deterministic portion and its volatile fields.
+
+  Returns `{deterministic_json, volatile_map}`. The deterministic portion is the same JSON
+  object with `fields/0` removed; the volatile map holds those fields and their values.
+
+  Anything that is not a JSON object passes through unchanged with an empty volatile map,
+  and never raises. That case is reached in practice: the worker truncates MCP tool output
+  at 8192 characters (`native/aetheris_worker/src/mcp.rs`, `truncate_text`), which
+  produces a string that is no longer parseable JSON. A truncated blob has already lost
+  its trailing fields, so there is nothing to split and passing it through is correct.
+  """
+  @spec split(term()) :: {term(), map()}
+  def split(output) when is_binary(output) do
+    case Jason.decode(output) do
+      {:ok, decoded} when is_map(decoded) -> split_decoded(output, decoded)
+      _other -> {output, %{}}
+    end
+  end
+
+  def split(output), do: {output, %{}}
+
+  @doc """
+  Returns only the deterministic portion of an exec-server output blob.
+
+  This is the read-side normalizer: idempotent, so applying it to a post-BL-049 recording
+  (already stripped) is a no-op, while a pre-BL-049 recording normalizes to the same shape.
+  """
+  @spec strip(term()) :: term()
+  def strip(output) do
+    {deterministic, _volatile} = split(output)
+    deterministic
+  end
+
+  defp split_decoded(output, decoded) do
+    {volatile, deterministic} = Map.split(decoded, @volatile_fields)
+
+    if map_size(volatile) == 0 do
+      # Nothing volatile present: return the original bytes rather than a re-encoding,
+      # so a blob that never carried these fields is not reshaped by passing through here.
+      {output, volatile}
+    else
+      {Jason.encode!(deterministic), volatile}
+    end
+  end
+end
diff --git a/lib/aetheris/worker/client.ex b/lib/aetheris/worker/client.ex
index 5c69088..7f942bd 100644
--- a/lib/aetheris/worker/client.ex
+++ b/lib/aetheris/worker/client.ex
@@ -373,6 +373,12 @@ defmodule Aetheris.Worker.Client do
     end
   end
 
+  # The worker-native realization of the volatile-metadata invariant: `duration_ms` is a
+  # sibling of `output`, never inside it, so it never reaches verify's compare
+  # (`Aetheris.Execution.VolatileMetadata`, `docs/aetheris/determinism-contract.md` §5).
+  # The exec-server path reaches the same shape by splitting the field back out of the
+  # blob (`Loop.exec_server_payload/2`); the fields treated as volatile are defined once,
+  # in `VolatileMetadata`, and `VolatileMetadataTest` asserts this envelope lifts them all.
   defp parse_execute_response(response) do
     %{
       output: Map.fetch!(response, "output"),
```

## 6. Full diff — `test/`

```diff
commit 13ff59cbdf7682b70dde46bb670944be7d9c3f2e
Author: Vishal Honnatti <vishal@bitloka.com>
Date:   Fri Jul 24 07:38:08 2026 +0530

    BL-049: volatile execution metadata is not part of the verify compare
    
    The exec server embeds `duration_ms` inside the tool-output blob, and verify
    compares that blob by value equality — so a perfectly reproducible
    `run_command` reported `:output_mismatch` on timing alone (measured: five of
    six runs; the sixth coincided). Worker-native tools never had this: their
    `duration_ms` is a sibling of `output`, lifted at the parse layer.
    
    `Aetheris.Execution.VolatileMetadata` is now the single definition of which
    fields are volatile. `Loop.exec_server_payload/2` splits them into the step
    envelope when recording, and `Verifier` strips them from the re-executed
    output *and* from the recorded one before comparing.
    
    The read side is not optional. Trajectory events are immutable, so every
    trajectory recorded before this commit carries `duration_ms` in the recorded
    blob permanently; normalizing only the re-executed side would have traded a
    nondeterministic verdict for a deterministically wrong one on that corpus.
    It is reuse rather than a compare-side policy: the verifier holds no field
    list of its own.
    
    `registry.ex` no longer advertises `duration_ms` to the model, which is now
    true — `payload["output"]` is the transcript content (`fork.ex`), so the
    recorded and model-visible values cannot diverge without breaking fork replay.
    
    Verdict stability is asserted six times per arm, over both record eras, with
    `verified: 1`/`served: 0` guards so a served step cannot pass as a fix. The
    BL-042 `--allow-effects` arm is tightened from `!= :served` to `== :verified`.
    
    Refs: determinism-contract §5 (edits drafted for §8 approval), BL-042, BL-048.
    
    Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

diff --git a/test/aetheris/execution/verify_effects_test.exs b/test/aetheris/execution/verify_effects_test.exs
index fe73051..f4c3334 100644
--- a/test/aetheris/execution/verify_effects_test.exs
+++ b/test/aetheris/execution/verify_effects_test.exs
@@ -21,6 +21,12 @@ defmodule Aetheris.Execution.VerifyEffectsTest do
   @timestamp DateTime.from_naive!(~N[2026-07-23 00:00:00], "Etc/UTC")
   @recorded_output ~s({"status":200,"body":"recorded-not-live"})
 
+  # What verify compares for the recorded `run_command` step, and therefore what it
+  # reports as `recorded_output`: the deterministic portion of the exec server's blob.
+  # The trajectory on disk still holds the full blob including `duration_ms` — events are
+  # immutable — but that field is not part of the compared value (BL-049).
+  @compared_run_command_output ~s({"exit_code":0,"stderr":"","stdout":"connected\\n"})
+
   setup do
     run_id = "test-verify-effects-#{System.unique_integer([:positive])}"
     sandbox_path = Path.join("/tmp", run_id)
@@ -137,7 +143,10 @@ defmodule Aetheris.Execution.VerifyEffectsTest do
     assert report.network_isolated == true
 
     assert [step_result] = report.steps
-    assert Map.fetch!(step_result, :recorded_output) == recorded_output
+
+    # The recording kept `duration_ms` (immutable event), and the compare did not see it.
+    assert recorded_output =~ ~s("duration_ms")
+    assert Map.fetch!(step_result, :recorded_output) == @compared_run_command_output
 
     # run_command is :contained, so it must not be served — it is re-executed and
     # diverges, because the network is unreachable under the namespace. Asserting
@@ -176,19 +185,20 @@ defmodule Aetheris.Execution.VerifyEffectsTest do
 
     assert [step_result] = report.steps
 
-    # The status is deliberately NOT asserted, and must not be: the exec server's
-    # run_command payload carries `duration_ms`, and comparison is value equality
-    # over the whole blob, so an identical command lands on :verified or
-    # :output_mismatch depending on whether the millisecond timing coincides
-    # (measured: 1 of 6 runs verified). Asserting either value would make this a
-    # flaky test; asserting `!= :served` is the claim that actually holds and is
-    # the one this arm exists to make. Tracked as BL-049.
-    assert Map.fetch!(step_result, :status) != :served
+    # This arm asserted only `!= :served` until BL-049: the exec server's run_command
+    # payload carried `duration_ms` inside the compared blob, so an identical command
+    # landed on :verified or :output_mismatch depending on whether the millisecond timing
+    # coincided (measured: 1 of 6 runs verified), and asserting either value would have
+    # made this test flaky. Volatile execution metadata is now outside the compared value
+    # (`Aetheris.Execution.VolatileMetadata`), so the verdict a reproducing command
+    # deserves is the verdict it gets, and this arm can make the stronger claim.
+    assert Map.fetch!(step_result, :status) == :verified
 
     # What does reproduce is the observable behaviour: same command, network
     # reachable, same stdout.
     assert Map.fetch!(step_result, :actual_output) =~ "connected"
-    assert Map.fetch!(step_result, :recorded_output) == recorded_output
+    assert recorded_output =~ ~s("duration_ms")
+    assert Map.fetch!(step_result, :recorded_output) == @compared_run_command_output
 
     rendered = Verifier.to_report(report)
     assert rendered =~ "WITHOUT network isolation"
diff --git a/test/aetheris/execution/verify_verdict_test.exs b/test/aetheris/execution/verify_verdict_test.exs
new file mode 100644
index 0000000..e297461
--- /dev/null
+++ b/test/aetheris/execution/verify_verdict_test.exs
@@ -0,0 +1,160 @@
+defmodule Aetheris.Execution.VerifyVerdictTest do
+  @moduledoc """
+  BL-049: the verify verdict for a reproducing `run_command` must be deterministic.
+
+  The exec server embeds `duration_ms` in the tool-output blob. Comparison is value
+  equality over that blob, so before BL-049 a perfectly reproducible command reported
+  `:output_mismatch` whenever the re-execution's wall clock differed — measured at five
+  of six runs, with the sixth "verifying" by coincidence.
+
+  A single green `verify` is therefore not evidence of anything here: it is the ~1/6
+  coincidence. Every assertion below runs the verdict `@runs` times and requires *all*
+  of them, and each arm asserts a real per-step compare engaged (`verified: 1`,
+  `served: 0`) so a step that quietly stopped being re-executed cannot pass as a fix.
+
+  Both record eras are covered, and they fail for different reasons if the fix is
+  incomplete:
+
+    * **pre-fix era** — the recorded blob still carries `duration_ms` (trajectory events
+      are immutable, critical rule #1, so this corpus exists forever). Only the
+      read-side normalization makes it verify.
+    * **post-fix era** — the recorded payload is built by the production constructor
+      `Loop.exec_server_payload/2`, so the recorded side is already stripped.
+  """
+  use ExUnit.Case, async: false
+
+  alias Aetheris.Execution.{Loop, Verifier, VerifyReport}
+  alias Aetheris.Trajectory.{Event, File}
+  alias Aetheris.Worker.Client
+
+  @timestamp DateTime.from_naive!(~N[2026-07-24 00:00:00], "Etc/UTC")
+
+  # Six is the ticket's measured sample: five mismatches, one coincidental pass.
+  @runs 6
+
+  setup do
+    run_id = "test-verify-verdict-#{System.unique_integer([:positive])}"
+    sandbox_path = Path.join("/tmp", run_id)
+    Elixir.File.mkdir_p!(sandbox_path)
+
+    on_exit(fn ->
+      Elixir.File.rm_rf!(Path.join(["priv", "runs", run_id]))
+      Elixir.File.rm_rf!(sandbox_path)
+    end)
+
+    %{run_id: run_id, sandbox_path: sandbox_path}
+  end
+
+  @tag :requires_worker
+  test "a pre-fix recording of a reproducing run_command verifies on every run", context do
+    %{run_id: run_id, sandbox_path: sandbox_path} = context
+
+    recorded_output = record_pre_fix_trajectory(run_id, sandbox_path)
+
+    # Non-vacuity: the fixture really is the pre-fix shape. If this stops holding,
+    # the arm below would pass without exercising the read-side normalization at all.
+    assert recorded_output =~ ~s("duration_ms")
+
+    statuses = verdicts(run_id, sandbox_path)
+
+    assert statuses == List.duplicate(:verified, @runs),
+           "verdict is not deterministic across #{@runs} runs: #{inspect(statuses)}"
+  end
+
+  @tag :requires_worker
+  test "a post-fix recording of a reproducing run_command verifies on every run", context do
+    %{run_id: run_id, sandbox_path: sandbox_path} = context
+
+    recorded_output = record_post_fix_trajectory(run_id, sandbox_path)
+
+    # Non-vacuity, the other way round: the recorded blob is genuinely the stripped shape,
+    # so this arm exercises the parse-layer fix rather than the read-side normalization.
+    refute recorded_output =~ ~s("duration_ms")
+
+    statuses = verdicts(run_id, sandbox_path)
+
+    assert statuses == List.duplicate(:verified, @runs),
+           "verdict is not deterministic across #{@runs} runs: #{inspect(statuses)}"
+  end
+
+  defp verdicts(run_id, sandbox_path) do
+    Enum.map(1..@runs, fn _run ->
+      assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)
+
+      # A served step cannot fail, so it must not be allowed to masquerade as a pass:
+      # run_command is :contained and has to be genuinely re-executed and compared.
+      assert report.served == 0
+      assert report.verified == 1
+      assert [step_result] = report.steps
+
+      # The command really ran in the verify worker — not a nil-vs-nil or empty-vs-empty
+      # equality, which would report `:verified` while proving nothing.
+      assert Map.fetch!(step_result, :actual_output) =~ ~s("stdout":"bl049\\n")
+      assert Map.fetch!(step_result, :actual_output) == Map.fetch!(step_result, :recorded_output)
+
+      Map.fetch!(step_result, :status)
+    end)
+  end
+
+  # The pre-BL-049 recording shape: the exec server's blob verbatim, `duration_ms`
+  # included. Produced by a real exec-server call rather than a hand-written string,
+  # so the fixture cannot drift from the shape the server actually emits.
+  defp record_pre_fix_trajectory(run_id, sandbox_path) do
+    output = call_run_command(run_id, sandbox_path)
+    write_trajectory(run_id, sandbox_path, %{"output" => output, "fs_hash" => nil})
+    output
+  end
+
+  # The current recording shape, built by the production constructor rather than by the
+  # test restating it — a test that hand-rolled the stripped payload would keep passing if
+  # `Loop` stopped producing it.
+  defp record_post_fix_trajectory(run_id, sandbox_path) do
+    raw = call_run_command(run_id, sandbox_path)
+    {:ok, payload, _message} = Loop.exec_server_payload("run_command", raw)
+
+    write_trajectory(run_id, sandbox_path, Map.delete(payload, "tool_name"))
+
+    Map.fetch!(payload, "output")
+  end
+
+  defp call_run_command(run_id, sandbox_path) do
+    {:ok, worker_pid} = Client.start_link(run_id: "record-#{run_id}", sandbox_path: sandbox_path)
+
+    {:ok, output} =
+      Client.call_mcp_tool(worker_pid, "aetheris_exec", "run_command", run_command_input())
+
+    Client.stop(worker_pid)
+
+    output
+  end
+
+  defp write_trajectory(run_id, sandbox_path, result_payload) do
+    events = [
+      event(run_id, 0, :tool_called, %{
+        "tool_name" => "run_command",
+        "tool_input" => run_command_input()
+      }),
+      event(run_id, 1, :tool_result, Map.put(result_payload, "tool_name", "run_command"))
+    ]
+
+    assert {:ok, _path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+  end
+
+  # Hermetic and reproducible: no network, no clock, no filesystem. Any divergence
+  # this command reports is a defect in the compare, not in the command.
+  defp run_command_input do
+    %{"command" => "python3", "args" => ["-c", ~s[print("bl049")]]}
+  end
+
+  defp event(run_id, seq, type, payload) do
+    %Event{
+      id: "#{run_id}-#{seq}",
+      run_id: run_id,
+      step: 1,
+      type: type,
+      payload: payload,
+      timestamp: @timestamp,
+      seq: seq
+    }
+  end
+end
diff --git a/test/aetheris/execution/volatile_metadata_test.exs b/test/aetheris/execution/volatile_metadata_test.exs
new file mode 100644
index 0000000..dd354ca
--- /dev/null
+++ b/test/aetheris/execution/volatile_metadata_test.exs
@@ -0,0 +1,139 @@
+defmodule Aetheris.Execution.VolatileMetadataTest do
+  @moduledoc """
+  BL-049 done-check 1: the deterministic proof that volatile execution metadata cannot
+  reach verify's compare.
+
+  This is the half of the evidence that does not depend on live timing. The integration
+  arm (`Aetheris.Execution.VerifyVerdictTest`) runs a real `verify` six times; a single
+  green run there proves nothing, because before the fix one run in six passed by
+  coincidence. Here the coincidence is impossible: the two inputs differ only in
+  `duration_ms`, and the compared portions are asserted byte-identical.
+  """
+  use ExUnit.Case, async: true
+
+  alias Aetheris.Execution.{Loop, VolatileMetadata}
+
+  # The exec server emits sorted keys (serde_json's map is a BTreeMap), which is why these
+  # fixtures are written in that order rather than in the order the fields are documented.
+  @fast ~s({"duration_ms":9,"exit_code":0,"stderr":"","stdout":"bl049\\n"})
+  @slow ~s({"duration_ms":231,"exit_code":0,"stderr":"","stdout":"bl049\\n"})
+  @deterministic ~s({"exit_code":0,"stderr":"","stdout":"bl049\\n"})
+
+  describe "split/1" do
+    test "two responses differing only in duration_ms compare byte-identical" do
+      {fast_output, fast_volatile} = VolatileMetadata.split(@fast)
+      {slow_output, slow_volatile} = VolatileMetadata.split(@slow)
+
+      # The compared portion — this is the whole point of the ticket.
+      assert fast_output == slow_output
+
+      # ...and non-vacuously so: the inputs really did differ, and the difference is
+      # preserved in the envelope rather than discarded. A `split/1` that returned a
+      # constant would satisfy the assertion above and nothing else.
+      refute @fast == @slow
+      assert Map.fetch!(fast_volatile, "duration_ms") == 9
+      assert Map.fetch!(slow_volatile, "duration_ms") == 231
+    end
+
+    test "the deterministic portion is the output blob without the volatile fields" do
+      assert {@deterministic, %{"duration_ms" => 9}} = VolatileMetadata.split(@fast)
+    end
+
+    test "a git_* response shape splits the same way" do
+      blob = ~s({"duration_ms":4,"exit_code":0,"output":"M lib/aetheris.ex\\n"})
+
+      assert {~s({"exit_code":0,"output":"M lib/aetheris.ex\\n"}), %{"duration_ms" => 4}} =
+               VolatileMetadata.split(blob)
+    end
+  end
+
+  describe "strip/1 — the read-side normalizer" do
+    test "a pre-fix recording normalizes byte-identically to a post-fix recording" do
+      # The compatibility guarantee in one assertion. The left side is what a trajectory
+      # recorded before BL-049 holds (immutable, critical rule #1); the right side is what
+      # `Loop.exec_server_payload/2` records now. They must compare equal, or every
+      # pre-fix trajectory reports a divergence on a command that reproduced exactly.
+      {:ok, payload, _message} = Loop.exec_server_payload("run_command", @fast)
+
+      assert VolatileMetadata.strip(@fast) == Map.fetch!(payload, "output")
+    end
+
+    test "is idempotent" do
+      once = VolatileMetadata.strip(@fast)
+
+      assert VolatileMetadata.strip(once) == once
+      assert once == @deterministic
+    end
+
+    test "passes through a blob that carries no volatile field, byte for byte" do
+      assert VolatileMetadata.strip(@deterministic) == @deterministic
+
+      assert VolatileMetadata.strip(~s({"error":"missing command"})) ==
+               ~s({"error":"missing command"})
+    end
+
+    test "passes through truncated, non-JSON and nil output without raising" do
+      # The worker truncates MCP output at 8192 chars (`mcp.rs`, `truncate_text`), which
+      # leaves invalid JSON. Verify must still produce a verdict rather than crash.
+      truncated = ~s({"duration_ms":9,"exit_code":0,"stdout":"aaaa[truncated])
+
+      assert VolatileMetadata.strip(truncated) == truncated
+      assert VolatileMetadata.strip("plain text output") == "plain text output"
+      assert VolatileMetadata.strip("[1,2,3]") == "[1,2,3]"
+      assert VolatileMetadata.strip(nil) == nil
+    end
+  end
+
+  describe "fields/0 — the single definition" do
+    test "duration_ms is volatile" do
+      assert "duration_ms" in VolatileMetadata.fields()
+    end
+
+    # Tripwire. The invariant is "no volatile field reaches the compare", and it has two
+    # realizations: this module (exec-server tools) and `parse_execute_response/1`
+    # (worker-native tools). Adding a field here without lifting it there would leave the
+    # worker-native path silently re-admitting it to the compared blob — the exact
+    # asymmetry BL-049 existed to close, running the other way.
+    test "the worker-native envelope lifts every volatile field out of its output" do
+      worker_envelope_keys = [:output, :fs_hash, :duration_ms]
+
+      for field <- VolatileMetadata.fields() do
+        assert String.to_existing_atom(field) in worker_envelope_keys,
+               """
+               #{field} is declared volatile but Worker.Client.parse_execute_response/1 \
+               does not lift it into the step envelope, so it would stay inside the \
+               compared "output" for every worker-native tool. Add it there too.\
+               """
+      end
+    end
+  end
+
+  describe "Loop.exec_server_payload/2" do
+    test "records the deterministic output and puts the duration in the envelope" do
+      assert {:ok, payload, _message} = Loop.exec_server_payload("run_command", @fast)
+
+      assert Map.fetch!(payload, "output") == @deterministic
+      assert Map.fetch!(payload, "duration_ms") == 9
+      assert Map.fetch!(payload, "tool_name") == "run_command"
+      assert Map.fetch!(payload, "fs_hash") == nil
+
+      refute Map.fetch!(payload, "output") =~ "duration_ms"
+    end
+
+    test "the transcript message is the recorded output, so a fork cannot diverge" do
+      # `Aetheris.Execution.Fork` rebuilds a fork's transcript from the recorded
+      # `"output"`. If the message the model saw differed from what was recorded, the fork
+      # would replay a transcript the original run never had.
+      {:ok, payload, message} = Loop.exec_server_payload("run_command", @fast)
+
+      assert message == Map.fetch!(payload, "output")
+    end
+
+    test "output the exec server did not shape passes through unchanged" do
+      assert {:ok, payload, _message} = Loop.exec_server_payload("run_command", "not json")
+
+      assert Map.fetch!(payload, "output") == "not json"
+      assert Map.fetch!(payload, "duration_ms") == nil
+    end
+  end
+end
```

---

## 7. Held

**Push is held**, both repos. `13ff59c` is local on `main`.
