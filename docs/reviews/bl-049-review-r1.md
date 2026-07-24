# BL-049 — review packet, round 1

**Ticket:** BL-049 — a `run_command` step can essentially never verify: `duration_ms` is
inside the compared payload.
**Commits:** harness `13ff59c` (r0) + `c80a8e4` (r1 fixes), on `main`, **push held**.
**Base:** harness `9d994fd`, agents `4af336e`.
**Round 0 packet:** `docs/reviews/bl-049-review.md`. **Review:** r1, claude-ui, 2026-07-24.
Diffs below are cumulative `9d994fd..HEAD`, regenerated — not patched onto r0.

**Disposition: F1 fixed (blocking). F2, F3, F4, F5 answered — F3 conceded and turned into a
third contract edit. F6 relayed.** One correction to my own r1 claim, in §1.

---

## 1. F1 [blocking] — the worker-native tripwire asserted a copy. Fixed.

Accepted in full. The r0 guard checked field names against a hand-copied literal
(`[:output, :fs_hash, :duration_ms]`) and never called `parse_execute_response/1`.

**Correction to my own account of it.** My r1 commit message and notes first said the r0 guard
*passed* the mutation. That was wrong. Reconstructed verbatim and run against
`@volatile_fields ~w[duration_ms started_at]` with `parse_execute_response/1` unchanged:

```
OldTripwireTest [reconstructed r0 guard]
  * test GROUND TRUTH — parse_execute_response/1 really does not lift started_at (4.7ms)
  * test ARM B — r0 guard after adding the atom to the literal, function still wrong (0.00ms)
  * test ARM A — r0 guard, literal untouched (3.5ms)

  1) test ARM A — r0 guard, literal untouched (OldTripwireTest)
     started_at is declared volatile but parse_execute_response/1 does not lift it
     code: for field <- VolatileMetadata.fields() do

3 tests, 1 failure
```

Arm A **fails**; arm B — the same guard after the single edit its own message invites —
**passes** while the function is still wrong. So the defect is that the guard is *silenceable
by the edit it asks for*, not that it was inert. The review's wording carried that proviso
("Yes — *provided* the new atom is in the literal"); my paraphrase dropped it. The finding
stands exactly as written; my restatement of it was the imprecise part.

**The fix.** `parse_execute_response/1` is now a `@doc false` seam (alongside
`worker_init_payload/6`, `port_options/1`, `containment_verdict/2` in the same module). The
guard drives a response through it and reads what the function produced — each volatile field
must be an envelope key and absent from `:output`. The response is built *from* `fields/0`, so
input and expectation grow together and arm B has no analogue: there is nothing left to edit
but the function.

Mutation-checked green→red on the same mutation:

```
  1) test fields/0 — the single definition the worker-native envelope lifts every volatile field out of its output (Aetheris.Execution.VolatileMetadataTest)
     test/aetheris/execution/volatile_metadata_test.exs:109
     started_at is declared volatile in VolatileMetadata.fields/0, but Worker.Client.parse_execute_response/1 did not lift it into the step envelope — it produced keys ["output", "fs_hash", "duration_ms"]. Lift it there, in the function; editing this test is not the fix.
     code: for field <- VolatileMetadata.fields() do
     stacktrace:
       test/aetheris/execution/volatile_metadata_test.exs:119: anonymous fn/3 in ...
       test/aetheris/execution/volatile_metadata_test.exs:118: (test)

12 tests, 1 failure
```

Restored: `12 tests, 0 failures`.

## 2. F2 [needs-source] — two attributes, deliberately different scopes, not a copy

Answered from source. They are **separate attributes answering different questions**, and the
invariant between them is containment rather than equality:

- `loop.ex:1014` — `@exec_server_tools`, **twelve** names. Decides which tools are *routed* to
  the exec server (`build_exec_server_index/1`, `loop.ex:1043-1044`).
- `verifier.ex:280` — `@exec_server_tools`, **one** name, `run_command`. Decides which tools
  verify *re-executes*. Scoped to one deliberately by BL-042; `git_*` is BL-047's taxonomy call.

The record-side strip does not use either list — it keys off the **server id** at dispatch
(`loop.ex:538`, `dispatch_mcp_tool(worker_pid, @exec_server_id = server_id, …)`), so it covers
all twelve.

**No live inconsistency today.** `git_*` records stripped and is never compared: verify returns
`unknown_tool` for that family, so it reports `:error` rather than reaching `compare_status/4`.
The drift you describe would need a name in `Verifier`'s list that `Loop` does not route —
recorded unstripped, normalized on read — which is BL-049's failure mode for that one tool.
That invariant (verify's list ⊆ loop's) is now stated at the attribute, with BL-047 named as
the ticket that extends both together. Not single-sourced, because merging them would silently
widen what verify re-executes — which is precisely BL-047's decision to make, not this
ticket's.

## 3. F3 [needs-source] — conceded. §3 does need the qualifier.

You were right and my r0 §4 claim was too strong. The live row at `9d994fd`
(`determinism-contract.md:59`) reads:

> compares recorded vs. re-executed tool **output by value equality** and recorded vs. actual
> filesystem **`fs_hash`**

After BL-049 the equality is preceded by a normalization on *both* sides
(`normalize_recorded/2` on the recorded side, `VolatileMetadata.strip/1` on the re-executed
one), so what is compared is the deterministic portion, not the tool output. "Output by value
equality" now reads as whole-output equality — the claim BL-049 makes false. A guarantee table
row that overstates what was checked is what §5's own residual-limitations discipline exists to
prevent.

The contract draft is now **three** edits, with (c) added and a "Why three, not two" section
recording that the omission was mine and the correction yours. (c) changes only the emphasised
clause of the `verify` row's *Guarantees* cell.

## 4. F4 [non-blocking] — measured: no reordering

The premise does not hold. Against the exact bytes from the baseline recording:

```
server   : {"duration_ms":10,"exit_code":0,"stderr":"","stdout":"bl049\n"}
stripped : {"exit_code":0,"stderr":"","stdout":"bl049\n"}
volatile : %{"duration_ms" => 10}
server keys   : ["duration_ms", "exit_code", "stderr", "stdout"]
stripped keys : ["exit_code", "stderr", "stdout"]
sorted?       : true
order kept?   : true
```

Decode → drop → encode round-trips insertion order for maps under 32 keys (Elixir's flatmap
representation); every exec-server payload has three or four. So the model-visible change
really is only the removal, and no eval golden or agent behaviour can be keying on an order
that did not change. Two boundaries recorded in the notes rather than left implicit: above 32
keys the order becomes the hashmap's iteration order rather than the server's, and a blob with
no volatile field is returned as the original bytes without a round-trip at all
(`split_decoded/2`), so it cannot be reshaped. Neither affects the compare, which re-encodes
equal maps on both sides.

## 5. F5 [non-blocking] — flagged for BL-047

Recorded in the implementation notes under its own heading, and in the BL-047 backlog row: the
strip is already in place for `git_*` on the record side (server-id keyed), unit-covered for
the `git_*` response shape, and unreached under verify. When BL-047 routes the family it adds
those names to `Verifier`'s `@exec_server_tools`, which wires `reexecute/3` and
`normalize_recorded/2` together in one edit — and must confirm the subset containment in §2.

## 6. F6 [blocks §8] — contract draft relayed

`docs/reviews/bl-049-contract-draft.md` is reproduced verbatim in §9 below, and is also on the
clipboard. It is **not** in any commit's contract file — `determinism-contract.md` is untouched
at `9d994fd` content.

---

## 7. Done-check, re-run after F1

```
Running ExUnit with seed: 862613, max_cases: 1
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]


Aetheris.Execution.VolatileMetadataTest [test/aetheris/execution/volatile_metadata_test.exs]
  * test split/1 a git_* response shape splits the same way [L#43]
  * test split/1 a git_* response shape splits the same way (10.8ms) [L#43]
  * test Loop.exec_server_payload/2 records the deterministic output and puts the duration in the envelope [L#134]
  * test Loop.exec_server_payload/2 records the deterministic output and puts the duration in the envelope (2.3ms) [L#134]
  * test strip/1 — the read-side normalizer passes through a blob that carries no volatile field, byte for byte [L#69]
  * test strip/1 — the read-side normalizer passes through a blob that carries no volatile field, byte for byte (0.00ms) [L#69]
  * test strip/1 — the read-side normalizer a pre-fix recording normalizes byte-identically to a post-fix recording [L#52]
  * test strip/1 — the read-side normalizer a pre-fix recording normalizes byte-identically to a post-fix recording (0.02ms) [L#52]
  * test strip/1 — the read-side normalizer passes through truncated, non-JSON and nil output without raising [L#76]
  * test strip/1 — the read-side normalizer passes through truncated, non-JSON and nil output without raising (0.01ms) [L#76]
  * test fields/0 — the single definition duration_ms is volatile [L#89]
  * test fields/0 — the single definition duration_ms is volatile (0.00ms) [L#89]
  * test Loop.exec_server_payload/2 the transcript message is the recorded output, so a fork cannot diverge [L#145]
  * test Loop.exec_server_payload/2 the transcript message is the recorded output, so a fork cannot diverge (0.01ms) [L#145]
  * test split/1 two responses differing only in duration_ms compare byte-identical [L#24]
  * test split/1 two responses differing only in duration_ms compare byte-identical (0.01ms) [L#24]
  * test Loop.exec_server_payload/2 output the exec server did not shape passes through unchanged [L#154]
  * test Loop.exec_server_payload/2 output the exec server did not shape passes through unchanged (0.00ms) [L#154]
  * test fields/0 — the single definition the worker-native envelope lifts every volatile field out of its output [L#109]
  * test fields/0 — the single definition the worker-native envelope lifts every volatile field out of its output (2.1ms) [L#109]
  * test split/1 the deterministic portion is the output blob without the volatile fields [L#39]
  * test split/1 the deterministic portion is the output blob without the volatile fields (0.02ms) [L#39]
  * test strip/1 — the read-side normalizer is idempotent [L#62]
  * test strip/1 — the read-side normalizer is idempotent (0.00ms) [L#62]

Aetheris.Execution.VerifyVerdictTest [test/aetheris/execution/verify_verdict_test.exs]
  * test a pre-fix recording of a reproducing run_command verifies on every run [L#49][sandbox] entered user+mount namespaces (uid=1000, gid=1000); network namespace not requested
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established

  * test a pre-fix recording of a reproducing run_command verifies on every run (110.9ms) [L#49]
  * test a post-fix recording of a reproducing run_command verifies on every run [L#65][sandbox] entered user+mount namespaces (uid=1000, gid=1000); network namespace not requested
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established
[sandbox] entered user+mount+net namespaces (uid=1000, gid=1000); network namespace established

  * test a post-fix recording of a reproducing run_command verifies on every run (95.3ms) [L#65]

Finished in 0.2 seconds (0.07s async, 0.2s sync)
14 tests, 0 failures
```

Gates, re-run at `c80a8e4`:

```
$ mix format --check-formatted
FORMAT OK

$ mix compile --warnings-as-errors
(no output — nothing to recompile)

$ mix credo --strict
Analysis took 2.7 seconds (0.1s to load, 2.5s running 69 checks on 222 files)
1991 mods/funs, found no issues.

$ mix dialyzer
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done in 0m4.63s
done (passed successfully)

$ mix test   (see note below — one unreproduced failure was observed once)
Finished in 89.4 seconds (2.9s async, 86.4s sync)
921 tests, 0 failures, 122 excluded

$ mix hex.audit
No retired or security advisory packages found
```

**One unreproduced `mix test` failure, reported rather than dropped — filed as BL-051.** The
first gate run at `c80a8e4` printed `921 tests, 1 failure, 122 excluded`. Nine consecutive
runs since have been `0 failures`. **The failing test's name was not captured**: my gate
command piped through `tail -2`, which kept the summary line and discarded the failure block —
a Complete-output slip on my part, and the reason there is no name to give you here. The
default suite has never been red on this branch before or since, and none of the r1 changes
touch runtime behaviour (the diff is a test, a `@doc false` seam, and comments). I am not
claiming it was pre-existing, because I cannot show that; I am claiming only what was
observed. BL-051 carries the observation plus the capture-discipline fix so the next
occurrence is identifiable.

`mix test --include requires_worker` — **known-red, BL-048**, named not re-triaged:

```
$ mix test --include requires_worker
Finished in 91.0 seconds (2.8s async, 88.2s sync)
921 tests, 15 failures, 65 excluded
```

Failing-set diff against the clean tree at `9d994fd` — unchanged from r0: the same 14, plus
`RunOverlayTest` (**BL-050**, demonstrated in r0 §3 not to be BL-049's):

```
$ diff <(clean-tree failing set) <(BL-049 r1 failing set)
2a3
> test overlay dirs are created and upper is empty after a read-only worker session (Aetheris.CLI.Commands.RunOverlayTest)
```

`drift_check --strict`, post-commit:

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

## 8. Cumulative diff `9d994fd..HEAD`

```
 .../milestones/bl-049-implementation-notes.md      | 210 +++++++++++++++++++++
 lib/aetheris/execution/loop.ex                     |  48 ++++-
 lib/aetheris/execution/tool_schema/registry.ex     |   4 +-
 lib/aetheris/execution/verifier.ex                 |  42 ++++-
 lib/aetheris/execution/volatile_metadata.ex        |  93 +++++++++
 lib/aetheris/worker/client.ex                      |  16 +-
 test/aetheris/execution/verify_effects_test.exs    |  30 ++-
 test/aetheris/execution/verify_verdict_test.exs    | 160 ++++++++++++++++
 test/aetheris/execution/volatile_metadata_test.exs | 161 ++++++++++++++++
 9 files changed, 745 insertions(+), 19 deletions(-)
```

### `lib/`

```diff
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
index 4c264fb..ade24a5 100644
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
@@ -274,13 +277,27 @@ defmodule Aetheris.Execution.Verifier do
   # are left as they are: whether mutating git operations should be re-executed
   # under verify at all, served, or declared unsupported is a taxonomy decision,
   # tracked as BL-047 rather than settled by an accident of routing.
+  #
+  # This is **not** a copy of `Loop`'s `@exec_server_tools` — the two answer different
+  # questions and are deliberately different sizes. `Loop`'s twelve names decide which tools
+  # are *routed* to the exec server, and the record-side volatile strip keys off the
+  # server-id at dispatch, so it covers all twelve. This list decides which tools verify
+  # *re-executes*, which is one. The invariant between them is containment, not equality:
+  # this list must stay a subset of `Loop`'s. A name here that `Loop` does not route would
+  # be normalized on read but never recorded stripped — the BL-049 failure mode for that one
+  # tool. BL-047 extends both together when it routes the `git_*` family (BL-049 r1 F2).
   @exec_server_tools ~w[run_command]
 
   defp reexecute(worker_pid, tool_name, tool_input) when tool_name in @exec_server_tools do
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
@@ -289,6 +306,25 @@ defmodule Aetheris.Execution.Verifier do
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
index 5c69088..da4850a 100644
--- a/lib/aetheris/worker/client.ex
+++ b/lib/aetheris/worker/client.ex
@@ -373,7 +373,21 @@ defmodule Aetheris.Worker.Client do
     end
   end
 
-  defp parse_execute_response(response) do
+  @doc false
+  # The worker-native realization of the volatile-metadata invariant: `duration_ms` is a
+  # sibling of `output`, never inside it, so it never reaches verify's compare
+  # (`Aetheris.Execution.VolatileMetadata`, `docs/aetheris/determinism-contract.md` §5).
+  # The exec-server path reaches the same shape by splitting the field back out of the
+  # blob (`Loop.exec_server_payload/2`); the fields treated as volatile are defined once,
+  # in `VolatileMetadata`.
+  #
+  # Public as a test seam, deliberately. `VolatileMetadataTest`'s tripwire drives a real
+  # response through *this function* and reads what it produced. An earlier version of that
+  # test compared field names against a hand-copied literal of the envelope shape, which
+  # could be satisfied by editing the copy rather than this function — a guard that would
+  # have passed while the path it guards was wrong (BL-049 r1 F1).
+  @spec parse_execute_response(map()) :: tool_result()
+  def parse_execute_response(response) do
     %{
       output: Map.fetch!(response, "output"),
       fs_hash: Map.get(response, "fs_hash"),
```

### `test/`

```diff
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
index 0000000..576ec80
--- /dev/null
+++ b/test/aetheris/execution/volatile_metadata_test.exs
@@ -0,0 +1,161 @@
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
+  alias Aetheris.Worker.Client
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
+    #
+    # This drives a response through `parse_execute_response/1` and reads what the function
+    # produced. The first version compared field names against a hand-copied literal of the
+    # envelope shape (`[:output, :fs_hash, :duration_ms]`) and never called the function at
+    # all — so a volatile field added to `fields/0` but not lifted by the parse would pass
+    # as soon as someone added the atom to the literal, which is what its own failure
+    # message invited. A guard that can be satisfied by editing its own copy of the answer
+    # is not a guard (BL-049 r1 F1).
+    #
+    # The response is built *from* `fields/0`, so adding a field extends the input and the
+    # expectation together; nothing here needs editing when the definition grows.
+    test "the worker-native envelope lifts every volatile field out of its output" do
+      response =
+        VolatileMetadata.fields()
+        |> Map.new(fn field -> {field, 7} end)
+        |> Map.merge(%{"output" => @deterministic, "fs_hash" => "abc123"})
+
+      envelope = Client.parse_execute_response(response)
+      envelope_keys = envelope |> Map.keys() |> Enum.map(&Atom.to_string/1)
+
+      for field <- VolatileMetadata.fields() do
+        assert field in envelope_keys,
+               """
+               #{field} is declared volatile in VolatileMetadata.fields/0, but \
+               Worker.Client.parse_execute_response/1 did not lift it into the step \
+               envelope — it produced keys #{inspect(envelope_keys)}. Lift it there, in \
+               the function; editing this test is not the fix.\
+               """
+
+        refute Map.fetch!(envelope, :output) =~ field,
+               "#{field} reached the compared \"output\" on the worker-native path"
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

## 9. Contract draft, verbatim (F6)

The full contents of `docs/reviews/bl-049-contract-draft.md`:

---

# BL-049 — determinism contract §5 edits (draft for human approval)

**Status:** DRAFT — awaiting human approval per contract §8.
**Gate:** §8 — "Any code change that would alter a guarantee here lands only with a
human-approved edit to this doc in the same review cycle." BL-049 changes what verify's
comparison ranges over, which is a §5 semantics change, so the edits are drafted here and
land only once approved.
**Drafted:** 2026-07-24, against harness `9d994fd` + the BL-049 working tree.
**Verification basis:** §5 was re-read from
`../aetheris/docs/aetheris/determinism-contract.md` at `9d994fd` this cycle. The
project-knowledge export is stale (pre-BL-025/042) and was not used. Line numbers below are
at `9d994fd`.

Three edits. (a) is the one BL-049 earns; (b) is a completeness gap noticed at BL-042 and
folded here rather than spending a standalone §8 cycle; **(c) was added at review r1 (F3)** —
an earlier version of this draft claimed §3 needed no change, and that claim was wrong. See
"Why three, not two" below.

## Why three, not two

The first draft asserted that §3's verify row stayed "exactly true, since BL-049 changes what
the recorded output *is*, not how it is compared." Read against the live row at `9d994fd`,
that does not hold. The row says the mode "compares recorded vs. re-executed tool **output by
value equality**". After BL-049 the equality is preceded by a normalization on *both* sides
(`Verifier.normalize_recorded/2` on the recorded side, `VolatileMetadata.strip/1` on the
re-executed one) — so what is compared is no longer the tool output but its deterministic
portion. "Output by value equality" now reads as whole-output equality, which is the claim
BL-049 makes false. §3 is a guarantee table; a row that overstates what was checked is
exactly what §5's own residual-limitations discipline exists to prevent.

Recorded here rather than quietly fixed: the omission was mine, and the correction is the
reviewer's (r1 F3).

The implementation commit referenced below is `13ff59c` (harness).

---

## (a) Residual limitations — the `run_command` verdict bullet

**Before** (§5 "Residual limitations", lines 313-321, verbatim):

> - **A `run_command` step can essentially never report `:verified`.** Comparison is value
>   equality over the tool's whole output payload, and the exec server's payload carries
>   `duration_ms` — a wall-clock measurement that differs between the recording and the
>   re-execution. A perfectly reproducible command therefore reports `:output_mismatch` on
>   timing alone (measured: five of six runs; the sixth coincided). Verify tells the truth
>   about the bytes it compared, but "the outputs differ" is not the claim an operator reads
>   it as. Tracked as **BL-049**, which decides whether the comparison should exclude volatile
>   fields, compare structurally, or the tool should stop returning timing in the compared
>   payload — a §5 semantics decision, not a patch.

**After** (replaces that bullet; the surrounding bullets are unchanged):

> - **What the comparison ranges over: the deterministic portion of the output.** Volatile
>   execution metadata — `duration_ms`, and any wall-clock or timing field — is **not part of
>   the compared value**. It is recorded in the step envelope alongside the output, never
>   inside it, so a difference in how long a tool took is not reported as a difference in what
>   it did. Worker-native tools always satisfied this at the parse layer
>   (`worker/client.ex`, `parse_execute_response/1`); exec-server tools did not, which is why
>   a perfectly reproducible `run_command` reported `:output_mismatch` on timing alone
>   (measured: five of six runs, the sixth coinciding). Closed by **BL-049** at `13ff59c`.
>   The fields treated as volatile are defined once, in
>   `Aetheris.Execution.VolatileMetadata`; both the exec-server response parse
>   (`Loop.exec_server_payload/2`) and the verifier call that definition, so there is no
>   second list to drift. The resolution covers **both record eras**: trajectory events are
>   immutable, so a trajectory recorded before `13ff59c` still carries `duration_ms` inside
>   its recorded blob, and the verifier normalizes the recorded side through the same strip
>   before comparing. A `:verified` `run_command` step therefore now asserts something an
>   honest command can satisfy.

**Note on the dependency, for the approver.** Without the read-side normalization this edit
would have to hedge to *"resolved for records at or after `13ff59c`"* — the pre-fix corpus
would otherwise have gone from a 1-in-6 flap to a deterministic `:output_mismatch`, which is
a confident wrong verdict rather than a flaky one. Normalizing both sides is what earns the
unqualified "resolved", and it is why the verifier changed at all.

---

## (b) "The opt-in" — `--allow-effects` also waives the network namespace

**Before** (§5 "The opt-in", lines 288-292, verbatim):

> ### The opt-in
>
> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.

**After:**

> ### The opt-in
>
> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.
>
> It also **waives the network namespace**. The re-execution worker is started with
> `network_namespace: not allow_effects` (`verifier.ex`), so the flag removes *both* guards
> at once: record-and-serve for `:uncontained` tools, and the containment boundary described
> above for everything else. This is a requirement rather than an oversight — `--allow-effects`
> exists to re-issue real network effects, and a worker inside a fresh network namespace
> cannot. The consequence is that under `--allow-effects` a `:contained` tool's incidental
> egress is live again, and the report says so
> (`Re-execution ran WITHOUT network isolation (--allow-effects): real effects were re-issued.`).
>
> Requesting effects is therefore requiring the uncontained path. The converse also holds and
> is stated under "When containment cannot be established": a default verify that cannot
> establish the namespace **refuses** rather than falling back to running without one.

**Why this belongs in §5 rather than being left implicit.** The netns gating is already
documented under "Containment boundary (from source)", which is where a reader looking for
*how containment works* will find it. "The opt-in" is where a reader looking for *what the
flag does* will look, and it named only the record-and-serve half. An operator reading only
this subsection would reasonably conclude `--allow-effects` re-executes uncontained tools
while leaving the namespace in place — the one reading it cannot have.

---

## (c) §3 verify row — what the equality ranges over

**Before** (§3 mode-guarantees table, the `verify` row's *Guarantees* cell, line 59,
verbatim — the *Does NOT guarantee* cell is unchanged and is elided here):

> | `verify` | Re-execution of every recorded tool call **whose effect class permits it** in a
> fresh sandboxed worker (`verifier.ex`, `effect_class.ex`); compares recorded vs.
> re-executed tool **output by value equality** and recorded vs. actual filesystem
> **`fs_hash`**; serves the recorded result for `:uncontained` tools instead of re-executing
> them (§5), reporting those steps as **served, not verified**; emits a per-step report with
> verified/served/failed counts | … |

**After** (only the emphasised clause changes; everything else in the cell stands):

> … compares recorded vs. re-executed tool output by value equality **over the deterministic
> portion of that output — volatile execution metadata is excluded from the comparison on
> both sides (§5)** — and recorded vs. actual filesystem **`fs_hash`**; …

**Scope note for the approver.** This is a precision fix to a row that became imprecise, not
a new guarantee: the comparison is still value equality, and nothing about which tools are
re-executed or served changes. The alternative — leaving the row as-is — asserts whole-output
equality, which BL-049 deliberately no longer performs.

---

## What this draft does **not** change

- §5's three classes, the containment boundary, the fail-closed refusal, served-not-verified,
  or the tripwire. BL-049 is verdict-correctness only and touches no containment guarantee.
- The `git_*` residual-limitation bullet (BL-047) and the `echo` bullet — both still open,
  both unchanged.

---

## 10. Held

**Push is held**, both repos. Contract edits (a)/(b)/(c) are drafted only; landing them is
the §8 approval step.
