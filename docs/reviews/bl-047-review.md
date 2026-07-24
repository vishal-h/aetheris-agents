# BL-047 — review packet

**Ticket:** BL-047 — verify never re-executes the `git_*` family (exec-server routing gap +
taxonomy). Resolved as **served-not-verified** (Option 3, human-ratified 2026-07-24).
**Commits:** harness `f41eb12` (code+tests) + `68d2614` (implementation notes), on `main`,
**push held**. Agents-side commit follows.
**Base:** harness `a926631`, agents `e86a724` (+1 unpushed local: BL-051 count `4aefc3f`).
**Contract refs re-verified at `a926631`**, read from
`../aetheris/docs/aetheris/determinism-contract.md`. Project-knowledge export stale, not used.

**Process note:** the §5/§3 contract edits are **held for §8 ratification of the wording** —
only the Option-3 *classification* is ratified so far. The harness contract is unchanged at
`f41eb12` (still says "eleven", still lists the `git_*` `:error` residual). The five edits are
drafted verbatim before/after in `docs/reviews/bl-047-contract-draft.md`, reproduced in §5
below. They land in a separate commit this cycle once approved, per BL-049's discipline.

---

## 1. Done-check output

### 1a. Before-fix baseline — the spurious `:error` at `a926631`

A recorded `git_commit` step (shaped as a live run records an exec-server MCP tool), verified
against unmodified `lib/`:

```
=== BL-047 before-fix baseline (a926631) ===
verified: 0  served: 0  failed: 1
step status : :error
step error  : "unknown_tool:git_commit"
actual_output: nil
```

`git_commit` re-executed down the worker-native path (`Client.execute` → `main.rs dispatch/3`,
which knows only `read_file`/`list_dir`/`write_file`/`http_call`) → `unknown_tool:git_commit`.
Never a comparison; a per-step `:error`. This is what §5's residual-limitations bullet named.

### 1b. After-fix — served under both modes, no worker, non-vacuity

```
Running ExUnit with seed: 92119, max_cases: 1
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]


Aetheris.Execution.EffectClassTest [test/aetheris/execution/effect_class_test.exs]
  * test non_reproducible?/1 the git_* family is non-reproducible [L#62]
  * test non_reproducible?/1 the git_* family is non-reproducible (2.1ms) [L#62]
  * test non_reproducible?/1 an unknown tool is reproducible by default — non-reproducibility is an explicit opt-in [L#75]
  * test non_reproducible?/1 an unknown tool is reproducible by default — non-reproducibility is an explicit opt-in (0.00ms) [L#75]
  * test classify/2 the filesystem built-ins are contained [L#105]
  * test classify/2 the filesystem built-ins are contained (0.00ms) [L#105]
  * test completeness over the tool set every in-process tool module is classified [L#25]
  * test completeness over the tool set every in-process tool module is classified (13.1ms) [L#25]
  * test completeness over the tool set every git_* tool the registry exposes is served as non-reproducible [L#46]
  * test completeness over the tool set every git_* tool the registry exposes is served as non-reproducible (1.2ms) [L#46]
  * test classify/2 an unknown tool with no source is uncontained — the fail-safe default [L#90]
  * test classify/2 an unknown tool with no source is uncontained — the fail-safe default (0.00ms) [L#90]
  * test non_reproducible?/1 other contained tools are reproducible — this is not 'all contained' [L#68]
  * test non_reproducible?/1 other contained tools are reproducible — this is not 'all contained' (0.00ms) [L#68]
  * test from_tool_called/1 an exec-server payload resolves to the contained class [L#134]
  * test from_tool_called/1 an exec-server payload resolves to the contained class (0.00ms) [L#134]
  * test completeness over the tool set every registry tool name is classified [L#16]
  * test completeness over the tool set every registry tool name is classified (0.00ms) [L#16]
  * test classify/2 run_command stays contained despite being routed with source: :mcp [L#94]
  * test classify/2 run_command stays contained despite being routed with source: :mcp (0.00ms) [L#94]
  * test completeness over the tool set the classified domain contains no name that no longer exists [L#32]
  * test completeness over the tool set the classified domain contains no name that no longer exists (0.1ms) [L#32]
  * test from_tool_called/1 a payload with no source is a built-in call [L#145]
  * test from_tool_called/1 a payload with no source is a built-in call (0.00ms) [L#145]
  * test from_tool_called/1 reads the MCP source recorded on the event payload [L#123]
  * test from_tool_called/1 reads the MCP source recorded on the event payload (0.00ms) [L#123]
  * test classify/2 echo is pure [L#117]
  * test classify/2 echo is pure (0.00ms) [L#117]
  * test classify/2 in-process orb tools are uncontained — they run outside the worker sandbox [L#111]
  * test classify/2 in-process orb tools are uncontained — they run outside the worker sandbox (0.00ms) [L#111]
  * test classify/2 an unknown tool from an external MCP server is uncontained [L#85]
  * test classify/2 an unknown tool from an external MCP server is uncontained (0.00ms) [L#85]
  * test classify/2 http_call is uncontained — its purpose is network egress [L#81]
  * test classify/2 http_call is uncontained — its purpose is network egress (0.00ms) [L#81]

Aetheris.Execution.VerifyGitTest [test/aetheris/execution/verify_git_test.exs]
  * test under --allow-effects, git stays served while a co-recorded http_call re-executes [L#123][sandbox] entered user+mount namespaces (uid=1000, gid=1000); network namespace not requested


  * test under --allow-effects, git stays served while a co-recorded http_call re-executes (103.2ms) [L#123]
  * test a recorded git_status (read-only) is served the same way [L#74]
  * test a recorded git_status (read-only) is served the same way (0.4ms) [L#74]
  * test a git-only trajectory (mutating + read-only) starts no worker under either mode [L#100]
  * test a git-only trajectory (mutating + read-only) starts no worker under either mode (0.4ms) [L#100]
  * test a recorded git_commit (mutating) is served, not re-executed, under default verify [L#50]
  * test a recorded git_commit (mutating) is served, not re-executed, under default verify (0.2ms) [L#50]
  * test the git serve is unconditional — --allow-effects does not lift it [L#85]
  * test the git serve is unconditional — --allow-effects does not lift it (0.2ms) [L#85]

Finished in 0.2 seconds (0.1s async, 0.1s sync)
22 tests, 0 failures
```

- **served under default** (`git_commit` mutating, `git_status` read-only): status `:served`,
  recorded output surfaced, `verified`/`:output_mismatch` **not** asserted, no `actual_output`,
  no error, `network_isolated == nil` (no worker started).
- **served under `--allow-effects` too** — the property that separates Option 3 from
  `:uncontained`. Still `:served`, still no worker.
- **git-only trajectory (mutating + read-only) starts no worker under either mode** —
  `network_isolated == nil` asserted for both `allow_effects` values.
- **non-vacuity** (`@tag :requires_worker`): a trajectory with a `git_status` step **and** an
  `http_call` step, run with `--allow-effects` — `git_status` stays `:served` while `http_call`
  **re-executes** (`status != :served`) and opens a real connection to the counting listener
  (`connection_count` delta ≥ 1, `network_isolated == false`). Proves git is treated
  *differently* in the same run, not that nothing re-executes.

### 1c. Tripwire — registry-derived, mutation-checked green→red

The guard reads `Registry.names()` (a real source), so there is no literal to edit to silence
it (BL-049 F1 forward). Dropping `git_commit` from `@non_reproducible_tools` while it stays
`:contained`:

```
  1) test completeness over the tool set every git_* tool the registry exposes is served as non-reproducible (Aetheris.Execution.EffectClassTest)
     git tools that are :contained but not marked non-reproducible — verify would re-execute them to a spurious mismatch: ["git_commit"]. Add them to @non_reproducible_tools (via @git_tools) in EffectClass.
17 tests, 2 failures
```

The `EffectClass` completeness tests stay green under the mutation (git_commit still
`:contained`) — the guard fires on exactly the hole they cannot see. Restored: `17 tests, 0
failures`.

### 1d. Gates (harness `f41eb12`)

```
$ mix format --check-formatted
FORMAT OK

$ mix credo --strict
Analysis took 2.6 seconds (0.1s to load, 2.5s running 69 checks on 223 files)
2001 mods/funs, found no issues.

$ mix dialyzer
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done (passed successfully)

$ mix test
Finished in 88.5 seconds (2.6s async, 85.9s sync)
930 tests, 0 failures, 123 excluded

$ mix hex.audit
No retired or security advisory packages found
```

`mix test --include requires_worker` — **known-red, BL-048 + BL-050**, named not re-triaged:

```
930 tests, 15 failures, 65 excluded
```

Failing-set diff vs the clean tree at `9d994fd` is unchanged: the same 14 (**BL-048**) plus
`RunOverlayTest` (**BL-050**). No BL-047 regression — the git tests are all green in this set.

### 1e. `drift_check --strict`, post-commit

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
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=f0df85a current=21cd777
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=a935038 current=8021a59
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=9b2b102 current=a926631

Summary: 7 PASS  0 FAIL  3 WARN  7 INFO

exit=0

**0 FAIL.** The three WARNs are `project_knowledge` manifest staleness — the standing
exemption (exit 0). `determinism-contract.md current=a926631` is correct: the contract is
held at its pre-BL-047 state, untouched by `f41eb12`. The backlog `current=` names HEAD at
drift-run time and is one commit behind the commit that records this output, by construction.
```

---

## 2. What changed

```
 .../milestones/bl-047-implementation-notes.md      | 102 +++++++++
 lib/aetheris/execution/effect_class.ex             |  51 ++++-
 lib/aetheris/execution/verifier.ex                 |  24 ++-
 test/aetheris/execution/effect_class_test.exs      |  40 ++++
 test/aetheris/execution/verify_git_test.exs        | 231 +++++++++++++++++++++
 5 files changed, 439 insertions(+), 9 deletions(-)
```

**Two enumerations verified from source before editing:**

1. **The family is TEN, not eleven.** `main.rs` schemas, `loop.ex @exec_server_tools`, and
   `effect_class.ex @contained_tools` all carry ten `git_*` names (read-only: `git_status`,
   `git_diff`, `git_diff_staged`, `git_log`, `git_show`; mutating: `git_add`, `git_commit`,
   `git_checkout`, `git_cherry_pick`, `git_cherry_pick_control`). The landed §5 says "eleven"
   in two places, inherited from BL-042 — corrected in the held §5 edits, flagged not followed.
2. **No network egress in the family** — no `push`/`fetch`/`pull`/`clone`/`remote` in `main.rs`
   or `runner.rs`. Confirms the `:contained`-for-safety premise from source.

**The change.** `git_*` is `:contained` (safe) but not verify-reproducible (verify mounts no
overlay → recorded repo absent, `git_commit` SHA nondeterministic). So verify **serves** it,
never re-executes it. `EffectClass` gains `@git_tools` (single source of the ten, referenced by
both `@contained_tools` and the new `@non_reproducible_tools` — no drift, no fourth hand-copy)
and `non_reproducible?/1`. `Verifier.plan_step/2` checks `non_reproducible?` in its first `cond`
arm, **ahead of** the `:uncontained and not allow_effects` gate, so the git serve is
unconditional — the property distinguishing Option 3 from `:uncontained` (which `--allow-effects`
would lift). The `EffectClass` union, `@classes`, `known_tools/0`, the completeness test, and
`Verifier`'s `@exec_server_tools` (`[run_command]`) are all untouched — git is served, never
re-executed, so BL-049 F2's subset-containment concern does not touch it.

**Modeling (3a, confirmed from source).** `git_*` is already `:contained`, so Option 3 needs no
union change and no completeness-test change; a `non_reproducible?` predicate is the whole
Elixir-side addition. 3b (a `:nonreproducible` union value) would touch every exhaustive match
for one family with no observable gain — rejected.

---

## 3. §5/§3 edits — held for §8 (five, before/after in §5)

The design sketch named three ((a) residual bullet, (b) served-not-verified, (c?) §3). The
source read surfaced two more the same change forces, plus the `eleven`→`ten` correction:

- **Edit 1** — §5 "The three classes" `:contained` bullet + routing paragraph: `git_*` goes
  from "re-executed and compared" / "remain unrouted, report `:error`" to the re-executed-vs-
  served split; carries `eleven`→`ten` (×2).
- **Edit 2** — §5 "Reporting: served is not verified": the **two reasons** a step is served
  (unsafe `:uncontained`, lifted by `--allow-effects`; vs non-reproducible `git_*`, not lifted).
- **Edit 3** — §5 "The opt-in": `--allow-effects` does **not** lift the `git_*` serve.
- **Edit 4** — §5 residual-limitations `git_*` bullet → resolved.
- **Edit 5** — §3 verify row: reproducibility qualifier on "whose effect class permits it", the
  served set gains the `git_*` family, and the non-guarantee reframes to "served, not
  re-executed by design."

The omission of edits 1 and 5 from the sketch was claude-ui's; the source read caught them
(recorded in the draft's "why five, not three").

---

## 4. Full diff `a926631..HEAD`

### `lib/`

```diff
diff --git a/lib/aetheris/execution/effect_class.ex b/lib/aetheris/execution/effect_class.ex
index ce4d76d..5119726 100644
--- a/lib/aetheris/execution/effect_class.ex
+++ b/lib/aetheris/execution/effect_class.ex
@@ -54,14 +54,31 @@ defmodule Aetheris.Execution.EffectClass do
 
   @exec_server_id "aetheris_exec"
 
-  # Worker-dispatched, filesystem-confined by the verify sandbox.
-  @contained_tools ~w[
-    read_file list_dir write_file
-    run_command
+  # The `git_*` family, enumerated once. Referenced by `@contained_tools` (they are
+  # filesystem-confined like any exec-server tool) and by `@non_reproducible_tools` (verify
+  # reconstructs no repo, so re-executing them is meaningless — BL-047). Single-sourced so the
+  # two lists cannot drift and no hand-copied fourth enumeration exists beside this one,
+  # `loop.ex`'s `@exec_server_tools`, and `main.rs`.
+  @git_tools ~w[
     git_status git_diff git_add git_commit git_diff_staged git_log git_show
     git_checkout git_cherry_pick git_cherry_pick_control
   ]
 
+  # Worker-dispatched, filesystem-confined by the verify sandbox. `git_*` is contained for
+  # *safety* (local-only — the exec server exposes no push/fetch/pull/clone) even though it is
+  # not re-executed (see `@non_reproducible_tools`).
+  @contained_tools ~w[read_file list_dir write_file run_command] ++ @git_tools
+
+  # `:contained` tools whose output is not a function of `tool_input` alone but of run
+  # environment verify does not reconstruct (BL-047). Verify **serves** these rather than
+  # re-executing them, under *both* default and `--allow-effects`, because re-execution would
+  # only manufacture a spurious mismatch — verify mounts no overlay, so the recorded repo's
+  # working-tree and history are absent and `git_commit` would embed a nondeterministic SHA.
+  # This is the "is re-execution *meaningful*" axis, orthogonal to the "is it *safe*" axis the
+  # three classes encode. Kept separate from the class union deliberately: widening the union
+  # for one family would touch every exhaustive match on it for no observable gain.
+  @non_reproducible_tools @git_tools
+
   # In-process (BEAM-side) tools: never dispatched to the worker, therefore never
   # inside the sandbox. `spawn_agent` can start a run that makes live model calls.
   @in_process_uncontained_tools ~w[
@@ -121,6 +138,32 @@ defmodule Aetheris.Execution.EffectClass do
   @spec known_tools() :: [String.t()]
   def known_tools, do: Map.keys(@classes)
 
+  @doc """
+  Whether re-executing `tool_name` under verify is *meaningful* — i.e. whether its output is
+  reproducible from `tool_input` in the verify sandbox.
+
+  `false` for the `git_*` family: verify reconstructs no repo (no overlay), so re-executing a
+  `git_*` op reads an absent repo and `git_commit` embeds a nondeterministic SHA. Such tools
+  are served-not-verified regardless of `--allow-effects` (`Aetheris.Execution.Verifier`,
+  `docs/aetheris/determinism-contract.md` §5).
+
+  This is orthogonal to `classify/2`: `git_*` is `:contained` (safe to run) *and*
+  non-reproducible (pointless to run). A tool can be safe and meaningful (`run_command` on a
+  hermetic command), safe and non-meaningful (`git_*`), or unsafe (`:uncontained`).
+  """
+  @spec non_reproducible?(String.t()) :: boolean()
+  def non_reproducible?(tool_name) when is_binary(tool_name),
+    do: tool_name in @non_reproducible_tools
+
+  @doc """
+  Returns every tool name verify serves as non-reproducible.
+
+  The domain the BL-047 tripwire asserts against: every `git_*` tool the registry exposes must
+  appear here, or it would be `:contained` and silently re-executed to a spurious mismatch.
+  """
+  @spec non_reproducible_tools() :: [String.t()]
+  def non_reproducible_tools, do: @non_reproducible_tools
+
   @doc """
   Returns the `server_id` of the internal exec server.
 
diff --git a/lib/aetheris/execution/verifier.ex b/lib/aetheris/execution/verifier.ex
index ade24a5..c3099b2 100644
--- a/lib/aetheris/execution/verifier.ex
+++ b/lib/aetheris/execution/verifier.ex
@@ -107,13 +107,27 @@ defmodule Aetheris.Execution.Verifier do
     end
   end
 
+  # Two independent reasons to serve rather than re-execute (§5, "Reporting: served is not
+  # verified"), and they differ under `--allow-effects`:
+  #
+  #   * non-reproducible (`git_*`) — checked **first, ahead of the `--allow-effects` gate**, so
+  #     the serve is unconditional. Re-executing gains nothing (verify reconstructs no repo) and
+  #     the flag has no external `git_*` effect to re-issue, so `--allow-effects` does not lift
+  #     it (BL-047). Because these never re-execute, no `git_*` name is in `@exec_server_tools`.
+  #   * uncontained — the tool's effects escape the sandbox; served by default, and *lifted* by
+  #     `--allow-effects` when the operator opts into the real effects to get a verdict.
   defp plan_step({called_event, _result_event} = tool_step, allow_effects) do
-    class = EffectClass.from_tool_called(called_event.payload)
+    tool_name = Map.fetch!(called_event.payload, "tool_name")
 
-    if class == :uncontained and not allow_effects do
-      {:serve, tool_step}
-    else
-      {:execute, tool_step}
+    cond do
+      EffectClass.non_reproducible?(tool_name) ->
+        {:serve, tool_step}
+
+      EffectClass.from_tool_called(called_event.payload) == :uncontained and not allow_effects ->
+        {:serve, tool_step}
+
+      true ->
+        {:execute, tool_step}
     end
   end
```

### `test/`

```diff
diff --git a/test/aetheris/execution/effect_class_test.exs b/test/aetheris/execution/effect_class_test.exs
index 634acc2..ac36ab6 100644
--- a/test/aetheris/execution/effect_class_test.exs
+++ b/test/aetheris/execution/effect_class_test.exs
@@ -35,6 +35,46 @@ defmodule Aetheris.Execution.EffectClassTest do
 
       assert ghosts == [], "classified but absent from the harness: #{inspect(ghosts)}"
     end
+
+    # BL-047 tripwire. `git_*` is `:contained`, so the completeness tests above pass whether
+    # or not it is marked non-reproducible — a git tool left out of `@non_reproducible_tools`
+    # would be silently re-executed to a spurious `:output_mismatch`, the exact defect BL-047
+    # exists to prevent. This guard reads the **registry** (the real source of what git tools
+    # exist), not a hand-copied literal, so a `git_worktree` added tomorrow and forgotten here
+    # fails loudly rather than shipping mis-classified (the BL-049 F1 lesson: a guard that
+    # asserts against a copy of the answer guards nothing).
+    test "every git_* tool the registry exposes is served as non-reproducible" do
+      registry_git = Enum.filter(Registry.names(), &String.starts_with?(&1, "git_"))
+
+      # Non-vacuity: there really are git tools in the registry, or this proves nothing.
+      assert registry_git != []
+
+      unmarked = registry_git -- EffectClass.non_reproducible_tools()
+
+      assert unmarked == [],
+             "git tools that are :contained but not marked non-reproducible — verify would " <>
+               "re-execute them to a spurious mismatch: #{inspect(unmarked)}. " <>
+               "Add them to @non_reproducible_tools (via @git_tools) in EffectClass."
+    end
+  end
+
+  describe "non_reproducible?/1" do
+    test "the git_* family is non-reproducible" do
+      for name <- ~w[git_status git_diff git_add git_commit git_checkout git_cherry_pick] do
+        assert EffectClass.non_reproducible?(name), "#{name} should be non-reproducible"
+      end
+    end
+
+    test "other contained tools are reproducible — this is not 'all contained'" do
+      # run_command and the filesystem built-ins ARE re-executed; the property is git-specific.
+      for name <- ~w[run_command read_file list_dir write_file] do
+        refute EffectClass.non_reproducible?(name), "#{name} should be reproducible"
+      end
+    end
+
+    test "an unknown tool is reproducible by default — non-reproducibility is an explicit opt-in" do
+      refute EffectClass.non_reproducible?("a_tool_added_tomorrow")
+    end
   end
 
   describe "classify/2" do
diff --git a/test/aetheris/execution/verify_git_test.exs b/test/aetheris/execution/verify_git_test.exs
new file mode 100644
index 0000000..89b2322
--- /dev/null
+++ b/test/aetheris/execution/verify_git_test.exs
@@ -0,0 +1,231 @@
+defmodule Aetheris.Execution.VerifyGitTest do
+  @moduledoc """
+  BL-047: a recorded `git_*` step is served-not-verified under verify, under *both* default
+  and `--allow-effects`, and is never re-executed.
+
+  `git_*` is `:contained` (safe to run — local-only, no egress) but not verify-reproducible:
+  verify mounts no overlay, so the recorded repo's working-tree and history are absent, and a
+  re-executed `git_status`/`git_diff`/`git_commit` would read a repo that is not there (and
+  `git_commit` would embed a nondeterministic SHA). Re-executing would manufacture a spurious
+  `:output_mismatch`; verify serves the recorded output instead and makes no re-execution
+  claim.
+
+  Two properties distinguish this from `:uncontained` record-and-serve, and both are asserted:
+
+    * the serve is **unconditional** — `--allow-effects` does not lift it (there is no external
+      `git_*` effect to re-issue), whereas it *does* lift the `:uncontained` serve; and
+    * a git-only trajectory **starts no worker at all** — nothing is re-executed, so the
+      process whose job is to re-enter the world is never spawned.
+
+  The git-only arms need no worker and no netns, so they are ordinary async-safe tests. The
+  non-vacuity arm (git served *while* a co-recorded `http_call` re-executes under
+  `--allow-effects`) does drive the worker and carries `@tag :requires_worker`.
+  """
+  use ExUnit.Case, async: false
+
+  alias Aetheris.Execution.{Verifier, VerifyReport}
+  alias Aetheris.Trajectory.{Event, File}
+
+  @timestamp DateTime.from_naive!(~N[2026-07-24 00:00:00], "Etc/UTC")
+
+  # A representative mutating member and a representative read-only member — the family is
+  # uniform (none reproduce), so covering one of each guards against a read/mutate split
+  # sneaking back in.
+  @git_commit_output ~s({"exit_code":0,"output":"[main abc1234] recorded commit\\n 1 file changed"})
+  @git_status_output ~s({"exit_code":0,"output":" M lib/aetheris.ex\\n"})
+
+  setup do
+    run_id = "test-verify-git-#{System.unique_integer([:positive])}"
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
+  test "a recorded git_commit (mutating) is served, not re-executed, under default verify",
+       %{run_id: run_id, sandbox_path: sandbox_path} do
+    write_git_trajectory(run_id, sandbox_path, "git_commit", @git_commit_output)
+
+    assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)
+
+    assert report.served == 1
+    assert report.verified == 0
+    assert report.failed == 0
+
+    assert [step] = report.steps
+    assert Map.fetch!(step, :status) == :served
+    # The recorded output is surfaced — that is the value an operator wants to see.
+    assert Map.fetch!(step, :recorded_output) == @git_commit_output
+    # Nothing re-executed: no actual output, no fs_hash claim, no error.
+    assert Map.get(step, :actual_output) == nil
+    assert Map.get(step, :actual_fs_hash) == nil
+    assert Map.get(step, :error) == nil
+
+    # No worker was started — `network_isolated` is nil only when nothing re-executed
+    # (`build_report/3` default; `execute_planned_steps` would set it true/false).
+    assert report.network_isolated == nil
+  end
+
+  test "a recorded git_status (read-only) is served the same way",
+       %{run_id: run_id, sandbox_path: sandbox_path} do
+    write_git_trajectory(run_id, sandbox_path, "git_status", @git_status_output)
+
+    assert {:ok, %VerifyReport{} = report} = Verifier.verify(run_id, sandbox_path: sandbox_path)
+
+    assert report.served == 1
+    assert [%{status: :served, recorded_output: @git_status_output}] = report.steps
+    assert report.network_isolated == nil
+  end
+
+  test "the git serve is unconditional — --allow-effects does not lift it",
+       %{run_id: run_id, sandbox_path: sandbox_path} do
+    write_git_trajectory(run_id, sandbox_path, "git_commit", @git_commit_output)
+
+    # This is the property that separates BL-047 from classifying git_* as :uncontained:
+    # --allow-effects lifts the *unsafe* serve, never the *non-reproducible* one.
+    assert {:ok, %VerifyReport{} = report} =
+             Verifier.verify(run_id, sandbox_path: sandbox_path, allow_effects: true)
+
+    assert report.served == 1
+    assert [%{status: :served}] = report.steps
+    # Still no worker, even with effects allowed — there is nothing to re-execute.
+    assert report.network_isolated == nil
+  end
+
+  test "a git-only trajectory (mutating + read-only) starts no worker under either mode",
+       %{run_id: run_id, sandbox_path: sandbox_path} do
+    events =
+      git_events(run_id, "git_commit", @git_commit_output, 1) ++
+        git_events(run_id, "git_status", @git_status_output, 2)
+
+    assert {:ok, _} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+
+    for allow_effects <- [false, true] do
+      assert {:ok, %VerifyReport{} = report} =
+               Verifier.verify(run_id, sandbox_path: sandbox_path, allow_effects: allow_effects)
+
+      assert report.served == 2
+      assert report.verified == 0
+      assert report.failed == 0
+      assert Enum.all?(report.steps, &(Map.fetch!(&1, :status) == :served))
+      assert report.network_isolated == nil, "a git-only verify must start no worker"
+    end
+  end
+
+  # --- non-vacuity: git is served *while* a co-recorded uncontained step re-executes ---------
+
+  @tag :requires_worker
+  test "under --allow-effects, git stays served while a co-recorded http_call re-executes",
+       %{run_id: run_id, sandbox_path: sandbox_path} do
+    listener = start_counting_listener()
+    on_exit(fn -> stop_counting_listener(listener) end)
+
+    # One git step and one http_call step in the same trajectory.
+    events =
+      git_events(run_id, "git_status", @git_status_output, 1) ++
+        [
+          event(run_id, 2, 0, :tool_called, %{
+            "tool_name" => "http_call",
+            "tool_input" => %{"url" => "http://127.0.0.1:#{listener.port}/bl047", "method" => "GET"}
+          }),
+          event(run_id, 2, 1, :tool_result, %{
+            "tool_name" => "http_call",
+            "output" => ~s({"status":200,"body":"recorded"}),
+            "fs_hash" => nil
+          })
+        ]
+
+    assert {:ok, _} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+
+    Process.flag(:trap_exit, true)
+    baseline = connection_count(listener)
+
+    assert {:ok, %VerifyReport{} = report} =
+             Verifier.verify(run_id, sandbox_path: sandbox_path, allow_effects: true)
+
+    steps = Map.new(report.steps, fn s -> {Map.fetch!(s, :tool_name), s} end)
+    git_step = Map.fetch!(steps, "git_status")
+    http_step = Map.fetch!(steps, "http_call")
+
+    # The point of the test: the two tools are treated *differently* in the same run.
+    assert Map.fetch!(git_step, :status) == :served
+    assert Map.fetch!(http_step, :status) != :served
+
+    # And the http_call genuinely re-executed — a real connection reached the listener —
+    # so "git served" is not vacuously true of a run where nothing re-executed at all.
+    assert connection_count(listener) - baseline >= 1
+    assert report.network_isolated == false
+  end
+
+  # --- helpers ---------------------------------------------------------------
+
+  defp write_git_trajectory(run_id, sandbox_path, tool_name, output) do
+    events = git_events(run_id, tool_name, output, 1)
+    assert {:ok, _path} = File.write(run_id, events, %{"sandbox_path" => sandbox_path})
+  end
+
+  # Shaped as a live run records an exec-server tool: source/server_id on the call.
+  defp git_events(run_id, tool_name, output, step) do
+    [
+      event(run_id, step, 0, :tool_called, %{
+        "tool_name" => tool_name,
+        "tool_input" => %{},
+        "source" => "mcp",
+        "server_id" => "aetheris_exec"
+      }),
+      event(run_id, step, 1, :tool_result, %{
+        "tool_name" => tool_name,
+        "output" => output,
+        "fs_hash" => nil
+      })
+    ]
+  end
+
+  defp event(run_id, step, seq, type, payload) do
+    %Event{
+      id: "#{run_id}-#{step}-#{seq}",
+      run_id: run_id,
+      step: step,
+      type: type,
+      payload: payload,
+      timestamp: @timestamp,
+      seq: step * 10 + seq
+    }
+  end
+
+  defp start_counting_listener do
+    {:ok, listen_socket} =
+      :gen_tcp.listen(0, [:binary, packet: :raw, active: false, reuseaddr: true])
+
+    {:ok, port} = :inet.port(listen_socket)
+    {:ok, counter} = Agent.start(fn -> 0 end)
+    acceptor = spawn(fn -> accept_loop(listen_socket, counter) end)
+    %{port: port, counter: counter, listen_socket: listen_socket, acceptor: acceptor}
+  end
+
+  defp accept_loop(listen_socket, counter) do
+    case :gen_tcp.accept(listen_socket) do
+      {:ok, socket} ->
+        Agent.update(counter, &(&1 + 1))
+        :gen_tcp.send(socket, "HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nlive")
+        :gen_tcp.close(socket)
+        accept_loop(listen_socket, counter)
+
+      {:error, _reason} ->
+        :ok
+    end
+  end
+
+  defp connection_count(listener), do: Agent.get(Map.fetch!(listener, :counter), & &1)
+
+  defp stop_counting_listener(listener) do
+    :gen_tcp.close(Map.fetch!(listener, :listen_socket))
+    Process.exit(Map.fetch!(listener, :acceptor), :kill)
+    Agent.stop(Map.fetch!(listener, :counter))
+  end
+end
```

---

## 5. Contract draft, verbatim (§8 — for ratification)

The full contents of `docs/reviews/bl-047-contract-draft.md`:

---

# BL-047 — determinism contract §5/§3 edits (draft for human approval)

**Status:** DRAFT — awaiting human approval per §8.
**Gate:** §8 — a change that alters a guarantee lands only with a human-approved edit to this
doc in the same review cycle. BL-047 changes how verify treats a whole tool family
(`git_*` → served-not-verified), which is a §5/§3 semantics change.
**Drafted:** 2026-07-24 by claude-ui, against harness `a926631` + the ratified Option-3
classification. Verbatim "Before" blocks are from the live text at `a926631` (claude-code relay,
this cycle); the project-knowledge export is stale and was not used. `f41eb12` is the
implementation commit, filled when it lands.

## Edit set — why five, not three

The design sketch named (a) residual bullet, (b) served-not-verified, (c?) §3. The source read
surfaced two more that the same change forces, plus a factual correction that must ride along:

- **Edit 1 (new)** — §5 "The three classes" `:contained` bullet says `git_*` tools "are
  **re-executed and compared**," and its routing paragraph says they "remain unrouted … report
  `:error`." Both are exactly what BL-047 makes false; leaving them is the overstatement §5's own
  discipline forbids. This block also carries the **`eleven` → `ten`** correction (§5:186 and
  §5:196), inherited from BL-042's edit — it lands here because BL-047 rewrites both sentences
  anyway. Flagged, not silent.
- **Edit 5 adjacent-case** — §3's *Guarantees* cell says verify re-executes "every recorded tool
  call whose effect class permits it." After BL-047, `git_*` is `:contained` (effect class
  permits) but is **not** re-executed (non-reproducible gate). So that clause over-includes
  `git_*` and needs the reproducibility qualifier — one clause wider than the obvious serve-clause
  edit. Named per the Adjacent-case rule.

The omission of edits 1 and 5 from the sketch was claude-ui's; the source read is what caught
them. Recorded here rather than quietly widened.

---

## Edit 1 — §5 "The three classes", `:contained` bullet + routing paragraph (lines 184–198)

**Before** (verbatim):

> - **`:contained`** — contained against the exec allowlist and, under a default verify,
>   against the network itself. Members: `read_file`, `list_dir`, `write_file`,
>   `run_command`, and the eleven local `git_*` tools. These are **re-executed and compared** —
>   that is what verify is for — with one live gap named below.
>
>   **Routing gap (BL-047).** Re-execution reaches a tool only by the route that dispatches it.
>   `run_command` and the `git_*` tools are exec-server MCP tools in a live run (`loop.ex`
>   `@exec_server_tools`, `dispatch_mcp_tool/4`); the worker's own dispatch table
>   (`main.rs` `dispatch/3`) knows only `read_file`, `list_dir`, `write_file`, `http_call`.
>   `Verifier` sent every tool down the worker-native path, so the whole exec-server family
>   re-executed as `unknown_tool:<name>` — a per-step `:error`, never a comparison. BL-042
>   routes **`run_command`** correctly (`verifier.ex` `@exec_server_tools`, `reexecute/3`); the
>   eleven `git_*` tools remain unrouted and are tracked as **BL-047**, which decides whether
>   mutating git operations should re-execute under verify at all. Until it lands, a recorded
>   `git_*` step reports `:error`, not a verdict.

**After:**

> - **`:contained`** — contained against the exec allowlist and, under a default verify,
>   against the network itself. Members: `read_file`, `list_dir`, `write_file`, `run_command`,
>   and the ten local `git_*` tools. The filesystem tools and `run_command` are **re-executed
>   and compared** — that is what verify is for. The `git_*` family is `:contained` for
>   *safety* (local-only — no `push`/`fetch`/`pull`/`clone`/`remote`) but is **served, not
>   re-executed**, for the reason given below and detailed under "Reporting: served is not
>   verified".
>
>   **The exec-server route, and why `git_*` is served (BL-042, BL-047).** Re-execution reaches
>   a tool only by the route that dispatches it. `run_command` and the `git_*` tools are
>   exec-server MCP tools in a live run (`loop.ex` `@exec_server_tools`, `dispatch_mcp_tool/4`);
>   the worker's own dispatch table (`main.rs` `dispatch/3`) knows only `read_file`, `list_dir`,
>   `write_file`, `http_call`. Before either ticket, `Verifier` sent every tool down the
>   worker-native path, so the whole exec-server family re-executed as `unknown_tool:<name>` — a
>   per-step `:error`, never a comparison. **BL-042** routes `run_command` correctly
>   (`verifier.ex` `@exec_server_tools`, `reexecute/3`). **BL-047** decides the ten `git_*` tools
>   the other way: they are **not** re-executed, because they are not verify-reproducible —
>   verify reconstructs no repo working-tree or history (it mounts no overlay), so a re-executed
>   `git_*` op would read an absent repo and `git_commit` would embed a fresh, nondeterministic
>   SHA. A recorded `git_*` step is therefore served-not-verified (resolved at `f41eb12`),
>   and that serve is **not** lifted by `--allow-effects`.

*Note.* `eleven` → `ten` in both sentences (the family is ten: five read-only —
`git_status`, `git_diff`, `git_diff_staged`, `git_log`, `git_show`; five mutating — `git_add`,
`git_commit`, `git_checkout`, `git_cherry_pick`, `git_cherry_pick_control`). The
re-executed-vs-served split resolves the flat "these are re-executed and compared," which was
false for `git_*` once it is served.

---

## Edit 2 — §5 "Reporting: served is not verified" (lines 299–308): the second reason

**Before** (verbatim):

> ### Reporting: served is not verified
>
> A served step performs no re-execution, so nothing is compared: there is no output
> equality check and **no `fs_hash` claim**. A served step is reported with status
> `served (not re-executed)` and counted in a distinct `served` tally, never in `verified`
> (`verify_report.ex`, `verifier.ex`). A verify whose every effectful step was served
> therefore reports `Tools verified: 0  Served (not verified): N  Failed: 0` — it does not
> print a green count that overstates what was checked. This matters because a served step
> **cannot fail**: it echoes the record, so it would look identical if the underlying tool
> were entirely broken.

**After** (existing paragraph unchanged; one paragraph appended):

> ### Reporting: served is not verified
>
> A served step performs no re-execution, so nothing is compared: there is no output
> equality check and **no `fs_hash` claim**. A served step is reported with status
> `served (not re-executed)` and counted in a distinct `served` tally, never in `verified`
> (`verify_report.ex`, `verifier.ex`). A verify whose every effectful step was served
> therefore reports `Tools verified: 0  Served (not verified): N  Failed: 0` — it does not
> print a green count that overstates what was checked. This matters because a served step
> **cannot fail**: it echoes the record, so it would look identical if the underlying tool
> were entirely broken.
>
> **Two reasons a step is served, and they differ under `--allow-effects`.** A step is served
> either because re-executing it is *unsafe* — an `:uncontained` tool whose effects the sandbox
> cannot hold (network egress, external MCP, in-process orb tools; "The three classes") — or
> because re-executing it is *not meaningful* — a `:contained` tool whose output is
> environment-dependent while verify reconstructs no environment. The `git_*` family is the
> second kind: `:contained` for safety (local-only, no egress) but not verify-reproducible,
> because verify mounts no overlay, so the recorded run's repo working-tree and history are
> absent and a re-executed `git_*` op would read a repo that is not there (and `git_commit`
> would embed a fresh, nondeterministic SHA). The two reasons diverge on exactly one point: the
> unsafe-to-re-execute serve is **lifted by `--allow-effects`** — the operator opts into the real
> effects to obtain a verdict; the non-reproducible serve is **not** lifted — re-executing a
> `git_*` op still reconstructs no repo, so it would only manufacture a spurious mismatch, and
> `--allow-effects` has no external `git_*` effect to re-issue. `git_*` is therefore served under
> both default and `--allow-effects` verify.

---

## Edit 3 — §5 "The opt-in" (lines 310–327): `--allow-effects` does not lift the `git_*` serve

**Before** (verbatim, first paragraph only — the rest of the subsection is unchanged):

> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text.

**After:**

> `aetheris verify <trajectory> --allow-effects` restores re-execution of `:uncontained`
> tools. Default is off. The flag re-issues real network and MCP effects and says so in its
> help text. It does **not** restore re-execution of the non-reproducible `git_*` serve
> ("Reporting: served is not verified"): that serve is unconditional, because re-executing a
> `git_*` op reconstructs no repo and the flag has no external `git_*` effect to re-issue.
> `--allow-effects` lifts the *unsafe* serve, never the *non-reproducible* one.

---

## Edit 4 — §5 "Residual limitations", the `git_*` bullet (lines 345–347): → resolved

**Before** (verbatim):

> - **`git_*` tools are not re-executed at all** — the exec-server routing gap above; a
>   recorded `git_*` step reports `:error`. Tracked as **BL-047**, which also decides whether
>   they *should* be re-executed.

**After** (one-line resolved marker, matching the list's `Incidental egress … closed by` /
`run_command verdict … resolved at 13ff59c` convention):

> - **`git_*` tools are served, not re-executed** — resolved at `f41eb12` (BL-047):
>   `:contained` for safety but not verify-reproducible, so served-not-verified and not lifted by
>   `--allow-effects`. See "The three classes" and "Reporting: served is not verified" above.

---

## Edit 5 — §3 verify row (line 59): reproducibility qualifier + the served set + the non-guarantee

Three clauses in the one row. **Before** (verbatim, the changing clauses shown in context):

> *Guarantees cell:* Re-execution of every recorded tool call **whose effect class permits it**
> in a fresh sandboxed worker … ; serves the recorded result **for `:uncontained` tools** instead
> of re-executing them (§5), reporting those steps as **served, not verified**; emits a per-step
> report with verified/served/failed counts
>
> *Does NOT guarantee cell:* … ; **re-execution of the `git_*` family (§5, BL-047)** ; …

**After:**

> *Guarantees cell:* Re-execution of every recorded tool call **whose effect class permits it and
> whose output verify can reproduce** in a fresh sandboxed worker … ; serves the recorded result
> **for `:uncontained` tools, and for the `:contained` but non-reproducible `git_*` family,**
> instead of re-executing them (§5), reporting those steps as **served, not verified**; emits a
> per-step report with verified/served/failed counts
>
> *Does NOT guarantee cell:* … ; **re-execution of the `git_*` family — served, not re-executed
> by design (§5)** ; …

*(The BL-049 (c) qualifier already in this cell — "over the deterministic portion … excluded on
both sides (§5)" — and every other clause are unchanged.)*

---

## What this draft does **not** change

- §5's class *definitions* (`:pure` / `:contained` / `:uncontained`), the containment boundary,
  the fail-closed refusal, or "When containment cannot be established." `git_*` stays `:contained`
  — its safety label is correct; only its re-execution disposition changes.
- The `run_command` handling, the `http_call`/`:uncontained` handling, or BL-049's volatile strip.
- Verifier's `@exec_server_tools` (stays `~w[run_command]`) — `git_*` is served, never
  re-executed, so it is never added there and BL-049 F2's subset-containment concern does not
  touch it.

---

## Held

Contract edits land only on human ratification (§8), in the same cycle as the implementation.
Push held.

---

## 6. Held

**Push is held**, both repos. The §5/§3 edits are **not** in `f41eb12` — the harness contract
is unchanged. On ratification I apply the five edits and commit them referencing `f41eb12`, then
this cycle's work is complete.
