# Review — BL-042: Capability-shaped containment for the verify worker (`CLONE_NEWNET`)

**What this file is.** By convention `docs/reviews/bl-0XX-review.md` holds the packet and,
once review happens, the rounds and dispositions. No review rounds yet — §A below is the
packet as submitted.

---

## §A. Packet

Generated artifact — gate output, diffs and evidence captured from the tools, not retyped.

---

## BL-042 — Capability-shaped containment for the verify worker (`CLONE_NEWNET`)

**Review packet** · cross-repo (harness `../aetheris/` + `aetheris-agents/`) · 2026-07-23
**Branch:** `main` (both repos) · **committed locally, pushes held**
**Commits:** harness `72a7f5e`, agents `0d5676a` · **basis:** harness `8021a59`, agents `6ec3304`
**Contract §5:** drafted, **NOT landed** — awaiting §8 approval (§7 below, verbatim)

**Scope changed in-cycle, with approval.** The row's red-first arm could not be written as
specified: `run_command` was never re-executed under verify at all, so its "0 connections"
was already true before any namespace existed. Routing `run_command` (and only
`run_command`) was approved to make the arm real; the `git_*` family is filed as BL-047 with
the taxonomy question it carries. §5 adjudicates this and every other deviation.

---

### 1. Done-check output

#### 1a. Harness gates (from `../aetheris/`)

```
$ mix deps.get
All dependencies are up to date

$ mix hex.audit
No retired or security advisory packages found

$ mix compile --warnings-as-errors
(no output — clean)

$ mix format --check-formatted
(no output — clean)

$ mix credo --strict
Checking 219 source files (this might take a while) ...
Analysis took 2.8 seconds (0.1s to load, 2.6s running 69 checks on 219 files)
1972 mods/funs, found no issues.

$ mix dialyzer
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done in 0m4.67s
done (passed successfully)

$ mix test
Finished in 88.3 seconds (2.4s async, 85.8s sync)
907 tests, 0 failures, 120 excluded
```

`cargo build` (worker) — clean, no warnings:

```
$ cargo build
   Compiling aetheris_worker v0.1.0 (/home/it/sandbox/elixirws/aetheris/native/aetheris_worker)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.46s
```

#### 1b. Known-red gate, named not re-triaged — `mix test --include requires_worker`

```
$ mix test --include requires_worker
Finished in 90.3 seconds (2.4s async, 87.8s sync)
907 tests, 15 failures, 65 excluded
```

**Pre-existing, not a BL-042 regression.** Verified by stashing every BL-042 change and
re-running on the clean tree — the failing set is identical, test for test:

```
$ git stash push -m "bl-042-wip" && mix compile && mix test --include requires_worker
900 tests, 15 failures, 65 excluded

  1) test HTTP MCP transport connects, lists tools, and calls echo (Aetheris.Integration.McpHttpTest)
  2) test write_file with overlay_base_dir set lands in upper/, not sandbox_path (Aetheris.Integration.OverlayAutonomousTest)
  3) test agent lists open issues via GitHub MCP server (Aetheris.Integration.McpGithubTest)
  4) test Worker.Client spawn_mcp_server/2 sends mcp_spawn command and returns :ok (Aetheris.Worker.ClientTest)
  5) test Worker.Client list_mcp_tools/2 decodes JSON output into tool definition maps (Aetheris.Worker.ClientTest)
  6) test Worker.Client execute/2 http_call to unreachable host returns tool error payload (Aetheris.Worker.ClientTest)
  7) test Worker.Client execute/2 reads a file from the sandbox (Aetheris.Worker.ClientTest)
  8) test Worker.Client call_mcp_tool/4 returns output string from mcp_call command (Aetheris.Worker.ClientTest)
  9) test Worker.Client execute/2 http_call successful GET returns status and body (Aetheris.Worker.ClientTest)
 10) test read_file returns identical fs_hash for two consecutive calls in the same run (Aetheris.Worker.FsHashStabilityTest)
 11) test read_file returns identical fs_hash across two separate runs with identical file content (Aetheris.Worker.FsHashStabilityTest)
 12) test run_command with unknown command returns non-zero exit_code (Aetheris.Execution.Tool.RunCommandTest)
 13) test run_command with working_dir executes in the specified directory (Aetheris.Execution.Tool.RunCommandTest)
 14) test run_command with timeout_ms returns exit_code -1 and stderr contains timed out (Aetheris.Execution.Tool.RunCommandTest)
 15) test overlay dirs are created and upper is empty after a read-only worker session (Aetheris.CLI.Commands.RunOverlayTest)
```

(900 vs 907 = this ticket's 7 new tests. Same 15 failures either side.)

Three distinct causes, sampled verbatim:

```
 13) test run_command with working_dir executes in the specified directory
     right: {:error, "{\"duration_ms\":0,\"exit_code\":-1,
             \"stderr\":\"command not permitted: pwd\",\"stdout\":\"\"}"}
              ^ test written against an allowlist that never contained `pwd`

  7) test Worker.Client execute/2 reads a file from the sandbox
     ** (FunctionClauseError) no function clause matching in String.starts_with?/2
         # 1
         nil
         # 2
         "sha256:"
              ^ fs_hash is nil where sha256: is expected — may be a live defect, not a stale test
```

plus network/credential-dependent integration tests (`httpbin.org`, GitHub MCP, HTTP MCP)
pulled in because `--include` overrides the `:integration` exclusion for dual-tagged tests.

**Filed as BL-048** the day it was found, per the gate rule. Invisible to CI
(`ci.yml:64` excludes the tag) and to every default `mix test` (`test_helper.exs:4` excludes
it too) — found only because this ticket ran the gate off-territory.

#### 1c. Cross-repo gate (from `aetheris-agents/`), POST-commit

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
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=f0df85a current=0d5676a
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=a935038 current=8021a59
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=9b2b102 current=8021a59

Summary: 7 PASS  0 FAIL  3 WARN  7 INFO
EXIT=0
```

**0 FAIL. The 3 WARNs are the documented `project_knowledge` manifest-staleness exemption**
— named, not chased: one per tracked doc in the export set, expected mid-cycle, cleared at
the export boundary. Run **post-commit** per BL-041: `current=0d5676a` is this cycle's agents
commit, so check 8 read committed history rather than passing vacuously.

#### 1d. Full test-name output — the two files this ticket touches

```
$ mix test test/aetheris/execution/verify_effects_test.exs test/aetheris/worker/client_test.exs \
    --include requires_worker --trace --seed 0

Aetheris.Worker.ClientSandboxPathTest [test/aetheris/worker/client_test.exs]
  * test port_options/1 includes {:cd, File.cwd!/0} when sandbox_path is nil (1.5ms) [L#258]
  * test port_options/1 includes {:cd, sandbox_path} when sandbox_path is explicit (0.00ms) [L#262]
  * test port_options/1 includes :binary (0.01ms) [L#266]
  * test port_options/1 includes {:packet, 4} (0.02ms) [L#270]
  * test worker init payload defaults nil sandbox_path to File.cwd!/0 (0.07ms) [L#274]
  * test worker init payload preserves explicit sandbox_path (0.00ms) [L#279]
  * test worker init payload includes overlay key when overlay is provided (0.00ms) [L#284]
  * test worker init payload omits overlay key when overlay is nil (0.00ms) [L#290]
  * test worker init payload includes memory_limit_bytes (0.00ms) [L#295]
  * test worker init payload includes cpu_quota_percent (0.00ms) [L#300]
  * test worker init payload does not request a network namespace by default (0.00ms) [L#307]
  * test worker init payload requests a network namespace when asked (0.00ms) [L#312]
  * test containment_verdict/2 refuses when a required network namespace was not established (0.00ms) [L#320]
  * test containment_verdict/2 accepts when a required network namespace was established (0.00ms) [L#324]
  * test containment_verdict/2 accepts when no network namespace was required (0.00ms) [L#328]

Aetheris.Execution.VerifyEffectsTest [test/aetheris/execution/verify_effects_test.exs]
  * test default verify serves the recorded http_call and opens no connection (9.3ms) [L#40]
  * test a recorded http_call failure is served verbatim, not improved on (0.6ms) [L#66]
  * test --allow-effects re-executes the http_call and the connection returns (90.6ms) [L#92]
  * test default verify does not re-open a recorded run_command's connection (46.3ms) [L#122]
  * test --allow-effects re-executes the recorded run_command and the connection returns (45.9ms) [L#157]

Aetheris.Worker.ClientTest [test/aetheris/worker/client_test.exs]
  ... 6 pre-existing failures, listed in §1b (BL-048); unchanged by this ticket
```

The five `VerifyEffectsTest` tests and all fifteen `ClientSandboxPathTest` tests pass. Truncation
stated: the `ClientTest` block is elided here because it is reproduced in full in §1b.

```
$ mix test test/aetheris/execution/verify_effects_test.exs --include requires_worker --seed 0
Running ExUnit with seed: 0, max_cases: 16
Excluding tags: [:integration, :m10_fixture]
Including tags: [:requires_worker]
Finished in 0.3 seconds (0.00s async, 0.3s sync)
5 tests, 0 failures
```

Namespace establishment across that run, counted from the worker's own log lines:

```
$ ... | grep -o "network namespace [a-z ]*" | sort | uniq -c
      1 network namespace established      <- the default-verify arm
      4 network namespace not requested    <- 2 recordings + 2 --allow-effects verifies
```

---

### 2. Red-first evidence

**The tag matters.** Both arms are `@tag :requires_worker`, excluded by `test_helper.exs:4`
and `ci.yml:64`. A green default `mix test` exercises neither. Every run below used
`--include requires_worker`.

**The arms measure a delta.** The recorded step is produced by a real worker, which egresses
by construction, so each arm asserts the change against that baseline and asserts
`baseline >= 1` first. An absolute count would have been satisfied by a step that never ran.

#### 2a. Red-zero — the specified red arm was already "green", for the wrong reason

Against unmodified `8021a59`, before any change:

```
BL-042 PRE-FIX default-verify step: %{
  error: "unknown_tool:run_command",
  status: :error,
  step: 1,
  recorded_output: "{\"duration_ms\":20,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"connected\\n\"}",
  actual_output: nil,
  actual_fs_hash: nil,
  recorded_fs_hash: nil,
  tool_input: %{
    "args" => ["-c",
     "import socket; s = socket.create_connection((\"127.0.0.1\", 35569), 2); s.close(); print(\"connected\")"],
    "command" => "python3"
  },
  tool_name: "run_command"
}
```

and the `--allow-effects` arm, which should have egressed, did not:

```
  1) test --allow-effects re-executes the recorded run_command and the connection returns
     Assertion with >= failed
     code:  assert connection_count(listener) - baseline >= 1
     left:  0
     right: 1
```

`Verifier.verify_step/2` re-executed every tool through `Client.execute` → the worker's own
dispatch table (`main.rs` `dispatch/3`: `read_file`, `list_dir`, `write_file`, `http_call`),
but `run_command` and the eleven `git_*` tools are exec-server MCP tools in a live run
(`loop.ex` `@exec_server_tools`, `dispatch_mcp_tool/4`). **The row's done-when — "hermetic
listener: 0 hits" — was already satisfied at HEAD by a tool that never ran.**

#### 2b. Red — routing lands, the egress is real

With `run_command` routed and **no namespace yet**:

```
  1) test default verify does not re-open a recorded run_command's connection
     Assertion with == failed
     code:  assert connection_count(listener) - baseline == 0
     left:  1
     right: 0
```

One inbound connection at the listener, from a `run_command` re-executed under verify. This
is the finding BL-042 was written against, demonstrated rather than cited.

#### 2c. Green — the namespace closes it, and the `--allow-effects` arm survives

```
$ mix test test/aetheris/execution/verify_effects_test.exs --include requires_worker
5 tests, 0 failures
```

| arm | connections (delta) | step status | `network_isolated` |
|---|---|---|---|
| pre-fix, unrouted | 0 | `:error` — `unknown_tool:run_command` | n/a |
| pre-netns, routed | **1** | re-executed, egressed | n/a |
| default verify | **0** | `:output_mismatch` + isolation note | `true` |
| `--allow-effects` | **≥1** | `:verified` | `false` |

The last row is BL-025's opt-in guard (H4): an unconditional namespace would have silently
inverted it into asserting the opposite of what it was written for.

#### 2d. The green arm cannot pass vacuously

A step that failed to run would also open no connection, so the default arm asserts the
divergence as well as the silence:

```elixir
assert connection_count(listener) - baseline == 0
assert report.network_isolated == true
assert Map.fetch!(step_result, :status) == :output_mismatch
assert Map.fetch!(step_result, :actual_output) != nil
refute Map.fetch!(step_result, :actual_output) =~ "connected"
rendered = Verifier.to_report(report)
assert rendered =~ "Re-execution ran under a network namespace"
assert rendered =~ "re-executed under network isolation"
```

`actual_output != nil` is what distinguishes "re-executed and diverged" from "never ran".

#### 2e. The fail-closed gate is exercised where it can fail

The refusal path cannot be reached on a host whose kernel grants `unshare` (this one does:
`unshare --user --net --mount true` succeeds, `max_user_namespaces=62595`,
`apparmor_restrict_unprivileged_userns=0`). The decision is therefore extracted and tested
directly over all four combinations — three of which must be `:ok`, because those are what
keep record mode and `--allow-effects` on the existing fail-open:

```
  * test containment_verdict/2 refuses when a required network namespace was not established
  * test containment_verdict/2 accepts when a required network namespace was established
  * test containment_verdict/2 accepts when no network namespace was required
```

Stated limitation: a live kernel-refusal end-to-end is not exercised, because forcing one
requires either root (sysctl) or a container this repo does not run in. The gate's *decision*
is tested exhaustively; its *trigger* is not.

---

### 3. Operator surface — before / after

Default verify of a trajectory containing a networked `run_command`:

```
BEFORE (8021a59)
step 1  run_command  {"command":"python3","args":["-c","...create_connection..."]}  error
  error: unknown_tool:run_command
  recorded output: {"duration_ms":20,"exit_code":0,"stderr":"","stdout":"connected\n"}
  actual output: nil
       ^ the step never ran, and the report does not say so

AFTER (72a7f5e)
Verify: <run_id>
Tools verified: 0  Served (not verified): 0  Failed: 1
Re-execution ran under a network namespace: no re-executed tool could egress.

step 1  run_command  {"command":"python3","args":["-c","...create_connection..."]}  output_mismatch
  recorded output: {"duration_ms":20,"exit_code":0,"stderr":"","stdout":"connected\n"}
  actual output: {"duration_ms":..,"exit_code":1,"stderr":"...Network is unreachable...","stdout":""}
  note: re-executed under network isolation — a step that reached the network when
        recorded cannot reproduce here
```

Where the kernel refuses `unshare`:

```
$ aetheris verify <trajectory>
cannot establish network containment for verify; re-run with --allow-effects to proceed
uncontained, or run where unshare is permitted
```

Record runs are byte-identical to before: they never request the namespace, so their
`unshare` flags are unchanged and their fail-open is untouched.

---

### 4. Adjacent cases enumerated

- **Record mode** — passes `network_namespace: false` (the default), so flags are exactly
  `CLONE_NEWUSER | CLONE_NEWNS` as before and `containment_verdict(false, _)` is always
  `:ok`. Restricted-container record runs still degrade rather than fail.
- **`--allow-effects`** — no namespace, so the opt-in still egresses (§2c, arm 4).
- **`:uncontained` tools under a default verify** — served, never executed, so the namespace
  cannot break them. `http_call`/MCP remain served (BL-025), asserted by the two untagged
  tests in the same file that continue to pass.
- **Verifies where every step is served** — no worker is started at all, so
  `network_isolated` is `nil` rather than a misleading `false`, and `render_containment/1`
  prints nothing.
- **`Port.close` on refusal** — `init/1` closes the port before `{:stop, …}` so a refused
  worker is not orphaned.
- **`%VerifyReport{}` literals** — `network_isolated` is added as a **non-enforced** field
  with a default, because `verifier_test.exs:53` constructs the struct literally and
  `@enforce_keys` would have broken it.
- **Non-Linux** — the `cfg(not(target_os = "linux"))` stub reports `net: false`, so a default
  verify there refuses. Named in §5 and the notes rather than left to be discovered.
- **BL-043's SIGSYS** — unchanged. `--allow-effects` on an `http_call` trajectory still
  crashes; the `{:worker_crashed, 159}` lines in §1d are that, pre-existing and expected.

---

### 5. Deviations from the ticket — each adjudicated

1. **`run_command` routing added to scope.** The ticket said "Do not touch" only the seccomp
   filter and the exec-server asymmetry; routing was not contemplated because the row assumed
   re-execution reached `run_command`. It did not (§2a). Raised with the human before
   implementing; scoped to `run_command` alone and approved. `git_*` untouched → **BL-047**.
2. **Third §5 statement.** The row scoped two (upgrade + condition). Implementation showed
   §5's `:contained` claim is false at HEAD for the whole exec-server family, and §8 forbids
   leaving a known-false guarantee standing, so the draft carries a correction as well.
3. **`/proc`-write failure surfacing.** The reorder was expected to turn a hard
   `/proc/self/*` write failure into no-`ready`. It does not: `main.rs` keeps
   log-and-continue and reports `network_namespace: false`. Record's fail-open then survives
   that path too, while verify still refuses. Deliberate, and stated in the notes.
4. **Report field named `network_isolated`, tri-state.** The row asked for the divergence to
   be interpretable; `nil` (no worker started) is distinguished from `false` (worker ran
   uncontained) so the report never implies a containment decision that was never made.

Not deviations, restated for the record: `lo` left down (H2); netns gated on
`not allow_effects` (H4); record fail-open untouched; BL-043 not fixed.

---

### 6. What this ticket does NOT claim

- **Not** that `git_*` tools verify. They still return `unknown_tool:<name>` — BL-047.
- **Not** that a kernel refusal was exercised end-to-end (§2e).
- **Not** that `http_call` works under `--allow-effects` — BL-043 is untouched, and the
  worker still dies of SIGSYS on that path.
- **Not** that the `requires_worker` set is green — it is red with 15 pre-existing failures,
  BL-048.
- **Not** that §5 is updated. The draft is in §7 and lands only on approval.

---

### 7. Contract §5 — DRAFT for §8 approval (verbatim, not landed)

Reproduced in full below from `docs/reviews/bl-042-contract-draft.md` (committed at
`0d5676a`). Three statements, one approval, as BL-025 did with §3+§5.

<!-- begin verbatim: docs/reviews/bl-042-contract-draft.md @ 0d5676a -->

# BL-042 — determinism contract §5 edit (draft for human approval)

**Status:** DRAFT — awaiting human approval per contract §8.
**Gate:** §8 — "Any code change that would alter a guarantee here lands only with a
human-approved edit to this doc in the same review cycle." BL-042 alters §5's containment
guarantee, so the edit is drafted here first and lands only once approved.
**Drafted:** 2026-07-23, against harness `8021a59` + the BL-042 working tree.
**Verification basis:** every citation below was read at the post-change tree in this cycle.
The third statement is a *correction* of text BL-025 landed one cycle ago — see "Why three
statements".

---

## Why three statements

The row scoped two (upgrade + condition). Implementation surfaced a third, and it is not
optional: §5's existing `:contained` claim is **false at HEAD**, and §8 forbids leaving a
false guarantee standing once it is known.

- **(a) Upgrade** — the egress-safety statement goes from *partial* to *capability-complete*.
- **(b) Condition** — that guarantee holds only where the namespace is establishable, and the
  fail-closed refusal is contract-visible behaviour. Drafting (a) without (b) would restate
  the exact unconditional overclaim BL-025's §5 rewrite existed to remove.
- **(c) Correction** — §5 says `:contained` tools are "re-executed and compared". They were
  not: `run_command` and all eleven `git_*` tools are dispatched to the exec server over MCP
  in a live run but were sent down the worker-native path by `Verifier`, so they returned
  `unknown_tool:<name>` and never ran. Only the worker-native filesystem built-ins were ever
  actually re-executed.

(c) is a Cited-means-read instance one level up: BL-025's claim was true of `read_file`, from
which the family's behaviour was inferred rather than exercised. Demonstrated this cycle
before the fix, against the unmodified tree:

```
BL-042 PRE-FIX default-verify step: %{
  error: "unknown_tool:run_command",
  status: :error,
  recorded_output: "{\"duration_ms\":20,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"connected\\n\"}",
  actual_output: nil,
  tool_name: "run_command"
}
```

BL-042 fixes the routing for **`run_command` only** — the tool its own proof requires, whose
re-execution BL-025 already ratified as `:contained`, and whose sole new hazard is the egress
this row contains. The `git_*` family is left exactly as it is (`unknown_tool` today, already
broken, not regressed) and filed as **BL-047**, because whether mutating git operations should
re-execute under verify at all, be served, or be declared unsupported is a taxonomy decision of
the same weight as BL-025's three classes — it should be decided, not inherited from a routing
accident.

---

## Replacement for the `:contained` bullet (§5 "The three classes")

> - **`:contained`** — contained **against the exec allowlist and, under a default verify,
>   against the network itself**. Members: `read_file`, `list_dir`, `write_file`,
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

## Replacement for the `run_command` limitation paragraph (§5, after the three classes)

Replaces the paragraph beginning "**`:contained` does not mean "incapable of egress."**" whose
last sentence currently reads *"Until BL-042 lands, verify's egress-safety is partial: closed
for the purpose-network tools, open for incidental egress through an allowed interpreter."*

> **The exec allowlist does not constrain capability; the sandbox does.** The allowlist
> (`native/aetheris_exec_server/src/runner.rs:7-24`) names no networking command — `curl` and
> `wget` are blocked and tested — but permits `python3`, `python`, `node`, `npm`, `mix`,
> `cargo` and `git`, every one socket-capable, and `npm install` / `mix deps.get` /
> `cargo build` egress by design. A recorded `run_command` that performed network I/O would
> therefore have done so again under verify. This is *incidental* egress: a property of
> particular invocations rather than of the tool, which is why record-and-serve is the wrong
> instrument for it (it would serve every computation verify exists to re-check).
>
> **The instrument is capability-shaped containment at the sandbox layer, and it is now in
> place (BL-042).** A default verify re-executes inside a **network namespace**: the worker
> `unshare`s `CLONE_NEWNET` alongside the user and mount namespaces
> (`native/aetheris_worker/src/sandbox.rs:161-224`), and the exec server is spawned *after*
> that call (`main.rs:59` → `:100`), so it inherits the namespace and `run_command` inherits it
> in turn. The namespace has only a loopback interface and it is left **down**: nothing in the
> worker needs it, since the worker↔BEAM channel and MCP stdio are pipes. No re-executed tool
> can egress, whatever the allowlist permits and whatever the recorded command chose to do.
>
> **Verify's egress-safety is therefore capability-complete for re-execution, conditional on
> the namespace being establishable** — see "When containment cannot be established" below.
> Record-and-serve (BL-025) remains in force for the `:uncontained` class and is now
> defence-in-depth rather than the sole defence.

## Replacement for "Containment boundary (from source)"

The existing subsection states the opposite of what is now true and must be replaced, not
amended.

> ### Containment boundary (from source)
>
> The re-execution worker runs under a user + mount namespace with sandbox-root path
> confinement (`sandbox.rs`, `Sandbox::resolve/resolve_new`; verify passes no overlay, so
> OverlayFS is not mounted on this path — `verifier.ex`, `main.rs`). Under a **default**
> verify it additionally runs under a **network namespace** (`CLONE_NEWUSER | CLONE_NEWNS |
> CLONE_NEWNET`, `sandbox.rs:169-172`), which is what closes incidental egress.
>
> The namespace is requested per verify, not globally: `Verifier` passes
> `network_namespace: not allow_effects` when it starts the worker (`verifier.ex:89-96`). This
> gating is a requirement rather than a preference — `--allow-effects` exists to re-issue real
> network effects, and a worker inside a fresh network namespace cannot. **Record runs are
> unaffected**: they never request the namespace, so their flags and their fail-open behaviour
> in restricted containers are unchanged.
>
> The seccomp filter still allows the socket family (`sandbox.rs`, "Network (`http_call` +
> MCP stdio)"), and is deliberately not the mechanism here: the exec server is a *separate
> process*, spawned before the filter is applied (`main.rs:100` vs `:112`), so it never runs
> under the filter at all. The namespace is inherited by that process; the filter would not
> have been.

## New subsection — "When containment cannot be established"

Insert immediately after "Containment boundary (from source)".

> ### When containment cannot be established
>
> A kernel may refuse `unshare` — restricted containers do, and no namespaces exist on
> non-Linux hosts at all. The worker reports what it actually established rather than only
> logging it: namespaces are entered **before** the `ready` handshake is written, and `ready`
> carries `network_namespace: true|false` (`main.rs:56-74`).
>
> **A default verify fails closed.** Requesting the namespace is requiring it: a worker that
> could not establish one never finishes starting (`client.ex`, `containment_verdict/2`), and
> `aetheris verify` reports
>
> ```
> cannot establish network containment for verify; re-run with --allow-effects to proceed
> uncontained, or run where unshare is permitted
> ```
>
> rather than a verdict. This is contract-visible behaviour, not an internal detail: an
> operator whose kernel denies `unshare` gets an error instead of a report, and on a non-Linux
> host every default verify refuses. The reasoning is that verify's entire value *is* the
> guarantee, so a verify that cannot guarantee has nothing to report — and `--allow-effects`
> already names the deliberate uncontained path, so a *silently* uncontained default has no
> constituency.
>
> **Record mode keeps its fail-open** and is untouched: a normal run in a restricted container
> continues without isolation, exactly as before.
>
> The report says which way it ran. A verify that re-executed under isolation prints
> `Re-execution ran under a network namespace: no re-executed tool could egress.`; under
> `--allow-effects` it prints the corresponding warning; and a diverging step under isolation
> carries a note that a step which reached the network when recorded cannot reproduce there
> (`verifier.ex`, `render_containment/1`, `render_isolation_note/2`). A networked divergence is
> a true report about a non-reproducible step, and it must read as one rather than as a
> mystery mismatch.

## Update to "Residual limitations"

Replace the first bullet; leave the rest as they are.

> - **Incidental egress via `run_command`** — closed by the network namespace (above), for
>   re-execution under a default verify. `--allow-effects` re-opens it by design.
> - **`git_*` tools are not re-executed at all** — the exec-server routing gap above; a
>   recorded `git_*` step reports `:error`. Tracked as **BL-047**, which also decides whether
>   they *should* be re-executed.

## Update to the §3 `verify` row

One clause only, in the "does not guarantee" column. The row currently ends:

> … **capability-level egress safety** — see §5's `run_command` limitation

Replace with:

> … re-execution of the `git_*` family (§5, BL-047); capability-level egress safety **where
> the kernel refuses to create a network namespace** — verify declines rather than
> guaranteeing (§5)

---

## Demonstration (both arms, hermetic)

`test/aetheris/execution/verify_effects_test.exs`, run with `--include requires_worker`
(the tag is excluded by default in `test_helper.exs`, so a plain `mix test` does not
exercise either arm). The listener counts inbound connections; the recorded step is produced
by a real worker, so both arms measure a **delta** against that recording.

| arm | connections | step status |
|---|---|---|
| pre-fix, routing unrouted | 0 | `:error` — `unknown_tool:run_command` (never ran) |
| pre-netns, routing fixed | **1** | re-executed and egressed — the red arm |
| default verify (netns) | **0** | `:output_mismatch`, with the isolation note |
| `--allow-effects` (no netns) | **≥1** | `:verified` — the opt-in still egresses |

The middle row is why the routing fix rides this ticket: without it the "0 connections" of a
default verify is true before the namespace exists, and proves nothing.

---

## Not in this edit

- **BL-043** (`setsockopt` missing from the seccomp allowlist → `http_call` SIGSYS) is
  unchanged, and §5's existing paragraph on it stands as written. `--allow-effects` on an
  `http_call` trajectory still crashes the CLI. BL-042 lands first by design: repairing
  `setsockopt` before this namespace existed would have widened the egress window.
- The `echo` residual limitation is unchanged — same routing mechanism, different family
  (in-process, not exec-server).

<!-- end verbatim -->

---

### 8. Implementation notes (verbatim)

From \`../aetheris/docs/aetheris/milestones/bl-042-implementation-notes.md\`, committed at `72a7f5e`.

<!-- begin verbatim: bl-042-implementation-notes.md @ 72a7f5e -->

# BL-042 — implementation notes

Capability-shaped containment for the verify worker (`CLONE_NEWNET`). Cross-repo:
harness code + `../aetheris-agents/docs/backlog-2026-06.md` and the §5 contract draft.

---

## The scope change, and why it was not optional

The row's red-first arm (H6) was specified as: point BL-025's hermetic listener at a
`run_command` that shells out to `python3` and opens a socket; expect ≥1 connection under
verify today, 0 once the namespace lands.

The first half of that is false. Run against unmodified `8021a59`:

```
%{error: "unknown_tool:run_command", status: :error, actual_output: nil, tool_name: "run_command"}
```

0 connections, with and without `--allow-effects`. `Verifier.verify_step/2` re-executed
every tool through `Client.execute` → the worker's own dispatch table (`main.rs` `dispatch/3`:
`read_file`, `list_dir`, `write_file`, `http_call`), but `run_command` and the eleven `git_*`
tools are dispatched to the **exec server over MCP** in a live run (`loop.ex`
`@exec_server_tools`, `dispatch_mcp_tool/4`). The whole family therefore never re-executed at
all.

So the row's done-when — "a `run_command` recorded doing network egress cannot egress during
verify (hermetic listener: 0 hits)" — was **already satisfied at HEAD**, by a mechanism that
has nothing to do with containment. Shipping the namespace against that check would have been
a check that cannot fail to pass, over a guarantee never exercised.

Human decision, 2026-07-23: route **`run_command` only** in this cycle. It is the tool the
proof requires, BL-025 already ratified its re-execution as `:contained`, and its only new
hazard is the egress this row exists to contain. The `git_*` family stays unrouted and becomes
**BL-047** — because whether `git_commit`/`git_checkout`/`git_cherry_pick` should re-execute
under verify *at all* is a taxonomy decision of BL-025's weight, and inheriting it from a
three-line routing fix would be deciding it by accident. §5 gains a named gap rather than a
silent one.

## Decisions

**H2 — `lo` is left down.** A fresh network namespace has only a loopback interface and it
starts down. Nothing brings it up, and no code refers to it. The worker↔BEAM channel is a
`Port` over stdin/stdout pipes and MCP stdio is likewise pipes, so nothing in the worker needs
loopback; raising it would re-admit localhost egress that verify has no use for. Recorded as a
decision, not left as an unexamined default.

**Rust reports, the BEAM decides.** `enter_namespaces/1` returns a `NamespaceStatus` and keeps
its fail-open: an `unshare` *refusal* returns `Ok(status all-false)`, never `Err`. Collapsing
refusal into `Err` would have taken record mode's fail-open with it — a normal run in a
restricted container must still work. The policy half (refuse to start when containment was
required and not established) lives in `Worker.Client.init/1`.

**Fail-closed is enforced in `Client.init`, not checked by `Verifier`.** `network_namespace:
true` *means* required: the worker that could not establish one never finishes starting, and
`start_link/1` returns `{:error, :containment_unavailable}`. A `Verifier`-side check would work
today and silently not work the first time a second caller forgets it. `containment_verdict/2`
is public so all four request/report combinations are unit-tested without a worker — three of
which must be `:ok`, since those are what keep record runs and `--allow-effects` on the
existing fail-open.

**`ready` moved after `enter_namespaces`.** The handshake now carries what was actually
established (`{"status":"ready","network_namespace":bool}`). This is better ordering on its own
terms — a worker announcing readiness before its isolation exists was always slightly wrong —
and the existing `%{"status" => "ready"}` pattern still matches, so nothing else changed.
Verified before relying on it: the worker channel is `Port.open({:spawn_executable, …},
{:packet, 4})`, i.e. pipes, so putting `CLONE_NEWNET` ahead of the handshake cannot break it.

**Divergence from the anticipated `/proc`-failure surfacing.** A hard `/proc/self/{setgroups,
uid_map,gid_map}` write failure still returns `Err`, but `main.rs` keeps the existing
log-and-continue and sends `ready` with `network_namespace: false` rather than exiting before
`ready`. Record's fail-open then survives that path too, and verify still refuses because the
reported status is `false`. Claiming containment we cannot attest to is the overclaim this
reporting exists to remove; refusing to *start* would have tightened record mode, which H3
forbids.

**Non-Linux hosts refuse.** The `#[cfg(not(target_os = "linux"))]` stub reports `net: false`,
so a default verify on macOS errors rather than running uncontained. That is fail-closed
working as ratified rather than a new decision, but it is operator-visible, so §5 names it
instead of leaving it to be discovered.

## Things the next ticket should know

- **The proof is tag-gated.** Both arms are `@tag :requires_worker`, which `test_helper.exs:4`
  and `ci.yml:64` exclude. A green `mix test` says nothing about them; run
  `mix test test/aetheris/execution/verify_effects_test.exs --include requires_worker`.
- **The arms measure a delta, not an absolute.** The recorded step is produced by a real worker
  (which egresses), so the baseline is non-zero by construction and each arm asserts the change
  against it. The `baseline >= 1` assertion is what keeps the delta meaningful.
- **`mix test --include requires_worker` is red — 15 failures, identical on a clean tree**
  (stale `pwd` in `run_command_test`, a nil `fs_hash` that may be a live defect, and
  network/credential-dependent integration tests dragged in because an include overrides the
  `:integration` exclusion). Filed as **BL-048**. It is a known-red gate with a ticket ref, not
  a BL-042 regression.
- **BL-043 is now unblocked.** Adding `setsockopt` to the seccomp allowlist restores full
  `http_call` egress; with the namespace in place that no longer widens an open window. The
  ordering constraint the row carried is discharged.
- **`echo` is unchanged** — same routing shape, different family (in-process, not exec-server).
  Still a §5 residual limitation.

<!-- end verbatim -->

---

### 9. Diff — harness (`../aetheris/` @ `72a7f5e`)

```
72a7f5e BL-042: capability-shaped containment for the verify worker (CLONE_NEWNET)
 .../milestones/bl-042-implementation-notes.md      |  99 ++++++++++++++++++
 lib/aetheris/cli/commands/verify.ex                |  29 +++++-
 lib/aetheris/execution/verifier.ex                 |  89 ++++++++++++++--
 lib/aetheris/execution/verify_report.ex            |  13 ++-
 lib/aetheris/worker/client.ex                      |  68 +++++++++++--
 native/aetheris_worker/src/main.rs                 |  28 +++++-
 native/aetheris_worker/src/sandbox.rs              |  92 ++++++++++++++---
 test/aetheris/execution/verify_effects_test.exs    | 112 +++++++++++++++++++++
 test/aetheris/worker/client_test.exs               |  28 ++++++
 9 files changed, 516 insertions(+), 42 deletions(-)
```

```diff
commit 72a7f5e95d10a866e3b3b179f4aa172a8fd5dab6
Author: Vishal Honnatti <vishal@bitloka.com>
Date:   Thu Jul 23 13:46:53 2026 +0530

    BL-042: capability-shaped containment for the verify worker (CLONE_NEWNET)
    
    Default verify now re-executes inside a network namespace, so no re-executed
    tool can egress regardless of what the exec allowlist permits. Record-and-serve
    (BL-025) becomes defence-in-depth rather than the sole, partial defence.
    
    - sandbox.rs: enter_namespaces/1 takes the request and returns NamespaceStatus.
      CLONE_NEWNET rides the existing unshare (CLONE_NEWUSER grants the capability).
      Fail-open is kept in Rust: an unshare refusal returns Ok(all-false), never Err,
      or record mode loses its fail-open. `lo` is left down (H2) — nothing needs it,
      the worker channel and MCP stdio are pipes.
    - main.rs: namespaces are entered BEFORE the ready handshake, which now carries
      network_namespace. A worker announcing ready before its isolation existed left
      the BEAM no way to tell containment from its absence.
    - client.ex: network_namespace: true means *required*. containment_verdict/2
      refuses to finish starting a worker that could not establish one, so no caller
      can hold an uncontained-but-usable worker by forgetting to check (H3).
    - verifier.ex: requests the namespace as `not allow_effects` (H4 — an
      unconditional netns would invert BL-025's opt-in guard).
    - verify.ex: the refusal is legible, naming --allow-effects as the way forward.
    - verify_report.ex: network_isolated, so a networked divergence is interpretable
      rather than a mystery mismatch.
    
    Grew in-cycle by one tool, and the growth was load-bearing: run_command was
    never re-executed under verify at all. Verifier sent every tool to the worker's
    own dispatch table, but run_command is an exec-server MCP tool, so it returned
    unknown_tool:run_command and opened 0 connections *before* the namespace
    existed — the row's "0 hits" done-when was already true for a reason unrelated
    to containment. Routing run_command (scoped decision, human) made the red arm
    real: 1 connection pre-netns, 0 after, >=1 under --allow-effects. The git_*
    family is deliberately left unrouted and filed as BL-047 with the taxonomy
    question it deserves.
    
    Gates: format, credo --strict, dialyzer, compile --warnings-as-errors, mix test
    (907/0). `mix test --include requires_worker` is red with 15 failures, identical
    on a clean tree — pre-existing, filed as BL-048.
    
    Backlog rows, the §5 contract draft and the closing evidence are in the sibling
    repo (aetheris-agents), per the cross-repo split. The §5 edit itself is NOT in
    this commit: it lands only on human approval, per contract §8.
    
    Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

diff --git a/lib/aetheris/cli/commands/verify.ex b/lib/aetheris/cli/commands/verify.ex
index 06f0fce..801174f 100644
--- a/lib/aetheris/cli/commands/verify.ex
+++ b/lib/aetheris/cli/commands/verify.ex
@@ -8,6 +8,11 @@ defmodule Aetheris.CLI.Commands.Verify do
   verify sandbox does not contain are served from the record rather than
   re-executed; `--allow-effects` opts back in to re-executing them, which
   re-issues real network and MCP effects.
+
+  The default re-execution worker runs inside a network namespace, so no
+  re-executed tool can egress (§5). Where the kernel refuses to create one,
+  verify **declines** rather than running uncontained: the command errors with
+  a message naming `--allow-effects` as the deliberate uncontained path.
   """
 
   alias Aetheris.CLI.Commands.RunHelpers
@@ -43,10 +48,25 @@ defmodule Aetheris.CLI.Commands.Verify do
     allow_effects = Keyword.get(opts, :allow_effects, false)
 
     case Aetheris.verify_run(run_id, allow_effects: allow_effects) do
-      {:ok, %VerifyReport{} = report} -> report_result(report)
-      {:error, :not_found} -> {:error, "no trajectory found for run #{run_id}"}
-      {:error, :sandbox_required} -> {:error, "no sandbox_path recorded for run #{run_id}"}
-      {:error, reason} -> {:error, "verification failed: #{inspect(reason)}"}
+      {:ok, %VerifyReport{} = report} ->
+        report_result(report)
+
+      {:error, :not_found} ->
+        {:error, "no trajectory found for run #{run_id}"}
+
+      {:error, :sandbox_required} ->
+        {:error, "no sandbox_path recorded for run #{run_id}"}
+
+      # Fail-closed (BL-042 H3): verify declines rather than re-executing without the
+      # containment it claims. The message names both ways forward, because an
+      # unexplained refusal is what pushes an operator back to an uncontained run.
+      {:error, :containment_unavailable} ->
+        {:error,
+         "cannot establish network containment for verify; re-run with --allow-effects " <>
+           "to proceed uncontained, or run where unshare is permitted"}
+
+      {:error, reason} ->
+        {:error, "verification failed: #{inspect(reason)}"}
     end
   end
 
@@ -65,6 +85,7 @@ defmodule Aetheris.CLI.Commands.Verify do
        verified: report.verified,
        served: report.served,
        failed: report.failed,
+       network_isolated: report.network_isolated,
        report: Verifier.to_report(report)
      }}
   end
diff --git a/lib/aetheris/execution/verifier.ex b/lib/aetheris/execution/verifier.ex
index 5840aa3..4c264fb 100644
--- a/lib/aetheris/execution/verifier.ex
+++ b/lib/aetheris/execution/verifier.ex
@@ -50,18 +50,29 @@ defmodule Aetheris.Execution.Verifier do
       Integer.to_string(report.served),
       "  Failed: ",
       Integer.to_string(report.failed),
-      "\n\n",
-      Enum.map(report.steps, &render_step/1)
+      "\n",
+      render_containment(report.network_isolated),
+      "\n",
+      Enum.map(report.steps, &render_step(&1, report.network_isolated))
     ]
     |> IO.iodata_to_binary()
   end
 
+  defp render_containment(true),
+    do: "Re-execution ran under a network namespace: no re-executed tool could egress.\n"
+
+  defp render_containment(false),
+    do:
+      "Re-execution ran WITHOUT network isolation (--allow-effects): real effects were re-issued.\n"
+
+  defp render_containment(nil), do: []
+
   defp verify_tool_steps(run_id, sandbox_path, tool_steps, opts) do
     allow_effects = Keyword.get(opts, :allow_effects, false)
     planned = Enum.map(tool_steps, &plan_step(&1, allow_effects))
 
     if Enum.any?(planned, fn {action, _step} -> action == :execute end) do
-      execute_planned_steps(run_id, sandbox_path, planned)
+      execute_planned_steps(run_id, sandbox_path, planned, allow_effects)
     else
       # Nothing to re-execute: do not start a worker at all. Serving every step
       # must not spawn the process whose job is to re-enter the world.
@@ -69,12 +80,24 @@ defmodule Aetheris.Execution.Verifier do
     end
   end
 
-  defp execute_planned_steps(run_id, sandbox_path, planned) do
-    case Client.start_link(run_id: "verify-#{run_id}", sandbox_path: sandbox_path) do
+  # The re-execution worker runs under a network namespace unless the caller opted
+  # into effects (BL-042). Gating on `allow_effects` is a requirement, not a
+  # preference: `--allow-effects` exists to re-issue real network effects, and a
+  # worker inside a fresh netns cannot. Requesting it is also *requiring* it —
+  # `Client.start_link` refuses to start a worker that could not establish one, so
+  # verify errors rather than reporting a clean verdict over containment it never had.
+  defp execute_planned_steps(run_id, sandbox_path, planned, allow_effects) do
+    network_isolated = not allow_effects
+
+    case Client.start_link(
+           run_id: "verify-#{run_id}",
+           sandbox_path: sandbox_path,
+           network_namespace: network_isolated
+         ) do
       {:ok, worker_pid} ->
         try do
           step_results = Enum.map(planned, &run_planned_step(worker_pid, &1))
-          {:ok, build_report(run_id, step_results)}
+          {:ok, build_report(run_id, step_results, network_isolated)}
         after
           stop_worker(worker_pid)
         end
@@ -207,7 +230,7 @@ defmodule Aetheris.Execution.Verifier do
     recorded_output = recorded_result(result_event.payload)
     recorded_fs_hash = Map.get(result_event.payload, "fs_hash")
 
-    case Client.execute(worker_pid, %{name: tool_name, input: tool_input}) do
+    case reexecute(worker_pid, tool_name, tool_input) do
       {:ok, tool_result} ->
         actual_output = Map.fetch!(tool_result, :output)
         actual_fs_hash = Map.get(tool_result, :fs_hash)
@@ -239,6 +262,33 @@ defmodule Aetheris.Execution.Verifier do
     end
   end
 
+  # `run_command` is dispatched to the exec server over MCP in a live run
+  # (`loop.ex` — `@exec_server_tools`, `dispatch_mcp_tool/4`), not to the worker's
+  # own tool table (`main.rs` `dispatch/3`: `read_file`, `list_dir`, `write_file`,
+  # `http_call`). Verify sent every tool down the worker-native path, so a recorded
+  # `run_command` step re-executed as `unknown_tool:run_command` — it never ran, and
+  # §5's claim that `:contained` tools are "re-executed and compared" was false for
+  # it. Demonstrated at BL-042 before this line existed.
+  #
+  # Deliberately `run_command` only. The eleven `git_*` tools share the defect and
+  # are left as they are: whether mutating git operations should be re-executed
+  # under verify at all, served, or declared unsupported is a taxonomy decision,
+  # tracked as BL-047 rather than settled by an accident of routing.
+  @exec_server_tools ~w[run_command]
+
+  defp reexecute(worker_pid, tool_name, tool_input) when tool_name in @exec_server_tools do
+    case Client.call_mcp_tool(worker_pid, "aetheris_exec", tool_name, tool_input) do
+      # The exec server makes no filesystem-hash claim, matching how a live run
+      # records these steps (`dispatch_mcp_tool/4` writes `"fs_hash" => nil`).
+      {:ok, output} -> {:ok, %{output: output, fs_hash: nil}}
+      {:error, reason} -> {:error, reason}
+    end
+  end
+
+  defp reexecute(worker_pid, tool_name, tool_input) do
+    Client.execute(worker_pid, %{name: tool_name, input: tool_input})
+  end
+
   defp compare_status(recorded_output, actual_output, recorded_fs_hash, actual_fs_hash) do
     cond do
       recorded_output != actual_output -> :output_mismatch
@@ -247,7 +297,9 @@ defmodule Aetheris.Execution.Verifier do
     end
   end
 
-  defp build_report(run_id, step_results) do
+  # `network_isolated` is nil when no worker was started at all (every step served):
+  # neither isolated nor uncontained, because nothing was re-executed.
+  defp build_report(run_id, step_results, network_isolated \\ nil) do
     verified = count_status(step_results, :verified)
     served = count_status(step_results, :served)
 
@@ -258,7 +310,8 @@ defmodule Aetheris.Execution.Verifier do
       # Served steps are neither verified nor failed — a served step cannot fail,
       # which is exactly why it must not be counted as a pass either.
       failed: Enum.count(step_results) - verified - served,
-      steps: step_results
+      steps: step_results,
+      network_isolated: network_isolated
     }
   end
 
@@ -266,7 +319,7 @@ defmodule Aetheris.Execution.Verifier do
     Enum.count(step_results, fn step_result -> Map.fetch!(step_result, :status) == status end)
   end
 
-  defp render_step(step_result) do
+  defp render_step(step_result, network_isolated) do
     input_json = Jason.encode!(Map.fetch!(step_result, :tool_input))
     status = Map.fetch!(step_result, :status)
 
@@ -280,10 +333,24 @@ defmodule Aetheris.Execution.Verifier do
       "  ",
       render_status(status),
       "\n",
-      render_failure_details(step_result, status)
+      render_failure_details(step_result, status),
+      render_isolation_note(status, network_isolated)
     ]
   end
 
+  # A diverging step under network isolation is the expected shape for a recorded
+  # step that performed network I/O: it cannot reproduce, and saying so is the
+  # difference between an honest report and a mystery mismatch.
+  defp render_isolation_note(:verified, _network_isolated), do: []
+  defp render_isolation_note(:served, _network_isolated), do: []
+
+  defp render_isolation_note(_status, true) do
+    "  note: re-executed under network isolation — a step that reached the network when " <>
+      "recorded cannot reproduce here\n"
+  end
+
+  defp render_isolation_note(_status, _network_isolated), do: []
+
   defp render_status(:verified), do: "\u2713 verified"
   defp render_status(:served), do: "served (not re-executed)"
   defp render_status(status), do: Atom.to_string(status)
diff --git a/lib/aetheris/execution/verify_report.ex b/lib/aetheris/execution/verify_report.ex
index fee662a..186689a 100644
--- a/lib/aetheris/execution/verify_report.ex
+++ b/lib/aetheris/execution/verify_report.ex
@@ -4,7 +4,7 @@ defmodule Aetheris.Execution.VerifyReport do
   """
 
   @enforce_keys [:run_id, :verified, :served, :failed, :steps]
-  defstruct [:run_id, :verified, :served, :failed, :steps]
+  defstruct [:run_id, :verified, :served, :failed, :steps, network_isolated: nil]
 
   @typedoc """
   Outcome of a single recorded tool step.
@@ -26,11 +26,20 @@ defmodule Aetheris.Execution.VerifyReport do
           error: String.t() | nil
         }
 
+  @typedoc """
+  `network_isolated` records whether the re-execution worker ran inside a network
+  namespace: `true` for a default verify, `false` when `allow_effects: true` waived
+  it, and `nil` when no worker was started because every step was served. It is
+  reported because a step that performed network I/O when recorded cannot reproduce
+  under isolation, and that divergence is only interpretable if the isolation is
+  visible (BL-042).
+  """
   @type t :: %__MODULE__{
           run_id: String.t(),
           verified: non_neg_integer(),
           served: non_neg_integer(),
           failed: non_neg_integer(),
-          steps: [step_result()]
+          steps: [step_result()],
+          network_isolated: boolean() | nil
         }
 end
diff --git a/lib/aetheris/worker/client.ex b/lib/aetheris/worker/client.ex
index 080be17..5c69088 100644
--- a/lib/aetheris/worker/client.ex
+++ b/lib/aetheris/worker/client.ex
@@ -8,7 +8,17 @@ defmodule Aetheris.Worker.Client do
 
   The init handshake is performed synchronously inside `init/1`: the worker
   must respond with `{"status": "ready"}` within 5 seconds or the process
-  fails to start with `{:stop, :worker_init_timeout}`.
+  fails to start with `{:stop, :worker_init_timeout}`. The worker enters its
+  namespaces *before* replying, so the ready message also reports whether a
+  network namespace was established (`"network_namespace"`).
+
+  Passing `network_namespace: true` makes that containment **required**: a
+  worker that could not establish it never finishes starting, and `start_link/1`
+  returns `{:error, :containment_unavailable}`. The requirement is enforced here
+  rather than left to each caller so that no code path can hold a worker that
+  silently lacks the isolation it asked for (BL-042 H3). The default is `false`,
+  which preserves the worker's fail-open behaviour for normal runs in restricted
+  container environments.
   """
 
   use GenServer
@@ -53,14 +63,23 @@ defmodule Aetheris.Worker.Client do
           String.t() | nil,
           map() | nil,
           non_neg_integer(),
-          non_neg_integer()
+          non_neg_integer(),
+          boolean()
         ) :: map()
-  def worker_init_payload(run_id, sandbox_path, overlay, memory_limit_bytes, cpu_quota_percent) do
+  def worker_init_payload(
+        run_id,
+        sandbox_path,
+        overlay,
+        memory_limit_bytes,
+        cpu_quota_percent,
+        network_namespace \\ false
+      ) do
     base = %{
       run_id: run_id,
       sandbox_path: resolve_sandbox_path(sandbox_path),
       memory_limit_bytes: memory_limit_bytes,
-      cpu_quota_percent: cpu_quota_percent
+      cpu_quota_percent: cpu_quota_percent,
+      network_namespace: network_namespace
     }
 
     case overlay do
@@ -160,6 +179,7 @@ defmodule Aetheris.Worker.Client do
     overlay = Keyword.get(opts, :overlay)
     memory_limit_bytes = Keyword.get(opts, :memory_limit_bytes, 536_870_912)
     cpu_quota_percent = Keyword.get(opts, :cpu_quota_percent, 50)
+    network_namespace = Keyword.get(opts, :network_namespace, false)
 
     worker_path = Application.app_dir(:aetheris, "priv/worker/aetheris_worker")
 
@@ -168,15 +188,37 @@ defmodule Aetheris.Worker.Client do
     Port.command(
       port,
       Jason.encode!(
-        worker_init_payload(run_id, sandbox_path, overlay, memory_limit_bytes, cpu_quota_percent)
+        worker_init_payload(
+          run_id,
+          sandbox_path,
+          overlay,
+          memory_limit_bytes,
+          cpu_quota_percent,
+          network_namespace
+        )
       )
     )
 
     receive do
       {^port, {:data, data}} ->
         case Jason.decode!(data) do
-          %{"status" => "ready"} ->
-            {:ok, %{port: port, run_id: run_id, pending: %{}}}
+          %{"status" => "ready"} = ready ->
+            established = Map.get(ready, "network_namespace", false)
+
+            case containment_verdict(network_namespace, established) do
+              :ok ->
+                {:ok,
+                 %{
+                   port: port,
+                   run_id: run_id,
+                   pending: %{},
+                   network_namespace: established
+                 }}
+
+              {:stop, reason} ->
+                Port.close(port)
+                {:stop, reason}
+            end
 
           other ->
             {:stop, {:init_failed, other}}
@@ -187,6 +229,18 @@ defmodule Aetheris.Worker.Client do
     end
   end
 
+  @doc """
+  Decides whether a worker that reported `established` satisfies a `required`
+  network-namespace request.
+
+  Only a *required* namespace that was not established refuses; a worker that was
+  not asked for one is unaffected however it reports, which is what keeps record
+  runs and `verify --allow-effects` on the worker's existing fail-open.
+  """
+  @spec containment_verdict(boolean(), boolean()) :: :ok | {:stop, :containment_unavailable}
+  def containment_verdict(true, false), do: {:stop, :containment_unavailable}
+  def containment_verdict(_required, _established), do: :ok
+
   @impl true
   def handle_call({:execute, tool_call}, from, state) do
     request = %{
diff --git a/native/aetheris_worker/src/main.rs b/native/aetheris_worker/src/main.rs
index ddf6033..028adcb 100644
--- a/native/aetheris_worker/src/main.rs
+++ b/native/aetheris_worker/src/main.rs
@@ -46,13 +46,33 @@ fn run() -> Result<(), Box<dyn std::error::Error>> {
         .and_then(|v| v.as_u64())
         .and_then(|v| u8::try_from(v).ok())
         .unwrap_or(50);
+    let network_namespace = init
+        .get("network_namespace")
+        .and_then(|v| v.as_bool())
+        .unwrap_or(false);
     let mut sandbox = Sandbox::new(sandbox_path);
     let mut mcp_clients: HashMap<String, mcp::McpClientKind> = HashMap::new();
-    protocol::write_message(&mut writer, &serde_json::json!({"status": "ready"}))?;
 
-    if let Err(e) = sandbox::enter_namespaces() {
-        eprintln!("[sandbox] namespace entry failed: {e}");
-    }
+    // Namespaces are entered BEFORE "ready" is written (BL-042) so the handshake can
+    // carry what was actually established. A worker that announced itself ready before
+    // its isolation existed left the BEAM no way to tell containment from its absence.
+    let ns_status = match sandbox::enter_namespaces(network_namespace) {
+        Ok(status) => status,
+        Err(e) => {
+            // A /proc mapping write failed. Keep the fail-open (record mode must still
+            // run in restricted environments) but report no containment: claiming a
+            // namespace we cannot attest to is the overclaim this reporting exists to
+            // remove. The BEAM decides what to do about it.
+            eprintln!("[sandbox] namespace entry failed: {e}");
+            sandbox::NamespaceStatus::default()
+        }
+    };
+
+    protocol::write_message(
+        &mut writer,
+        &serde_json::json!({"status": "ready", "network_namespace": ns_status.net}),
+    )?;
+
     if let Err(e) = sandbox::enter_cgroup(run_id, memory_limit_bytes, cpu_quota_pct) {
         eprintln!("[sandbox] cgroup setup failed: {e}");
     }
diff --git a/native/aetheris_worker/src/sandbox.rs b/native/aetheris_worker/src/sandbox.rs
index 470aa96..111f108 100644
--- a/native/aetheris_worker/src/sandbox.rs
+++ b/native/aetheris_worker/src/sandbox.rs
@@ -126,43 +126,107 @@ fn normalize_lexically(path: &Path) -> PathBuf {
     components.iter().collect()
 }
 
-/// Enters a new user namespace and mount namespace via `unshare(2)`, then maps the real
-/// UID/GID to 0 inside the new user namespace.
+/// Which namespaces `enter_namespaces` actually established.
+///
+/// Reported rather than merely logged (BL-042): the caller cannot tell a successful
+/// `unshare` from a refused one otherwise, because both leave the process running.
+/// `net` is what the BEAM's fail-closed gate for verify is decided on.
+#[derive(Debug, Clone, Copy, Default)]
+pub struct NamespaceStatus {
+    pub user: bool,
+    pub mount: bool,
+    pub net: bool,
+}
+
+/// Enters a new user namespace and mount namespace via `unshare(2)` — and, when
+/// `network_namespace` is requested, a new network namespace as well — then maps the
+/// real UID/GID to 0 inside the new user namespace.
+///
+/// `CLONE_NEWUSER` is created in the same `unshare` call and grants the capability for
+/// the others, so the network namespace rides the existing call rather than needing a
+/// second one.
+///
+/// The new network namespace has only a loopback interface and it starts **down**.
+/// Nothing brings it up (BL-042 H2): the worker↔BEAM channel and MCP stdio are pipes,
+/// so no loopback is needed, and raising `lo` would re-admit localhost egress that
+/// verify has no use for.
 ///
 /// Must be called BEFORE `apply_seccomp_filter` so that the `unshare` syscall is still
-/// permitted. Fails open: if `unshare` is rejected by the kernel (e.g. in restricted
-/// container environments), the error is logged and the worker continues without isolation.
+/// permitted. **Fails open**: if `unshare` is rejected by the kernel (e.g. in restricted
+/// container environments), the error is logged and the worker continues without
+/// isolation — the returned status reports what was established, and the policy decision
+/// of whether to proceed belongs to the caller. Collapsing a refusal into `Err` here
+/// would take record mode's fail-open with it.
 #[cfg(target_os = "linux")]
-pub fn enter_namespaces() -> anyhow::Result<()> {
-    use libc::{CLONE_NEWNS, CLONE_NEWUSER};
+pub fn enter_namespaces(network_namespace: bool) -> anyhow::Result<NamespaceStatus> {
+    use libc::{CLONE_NEWNET, CLONE_NEWNS, CLONE_NEWUSER};
 
     // Capture real host UID/GID BEFORE unshare — after entering the user namespace
     // getuid()/getgid() return the overflow UID (65534) until a mapping is written.
     let uid = unsafe { libc::getuid() };
     let gid = unsafe { libc::getgid() };
 
-    let flags = CLONE_NEWUSER | CLONE_NEWNS;
+    let mut flags = CLONE_NEWUSER | CLONE_NEWNS;
+    if network_namespace {
+        flags |= CLONE_NEWNET;
+    }
+
     let rc = unsafe { libc::unshare(flags) };
     if rc != 0 {
         eprintln!(
-            "[sandbox] unshare failed: {}",
-            std::io::Error::last_os_error()
+            "[sandbox] unshare failed: {} (network namespace {})",
+            std::io::Error::last_os_error(),
+            if network_namespace {
+                "REQUESTED but NOT established"
+            } else {
+                "not requested"
+            }
         );
-        return Ok(());
+        return Ok(NamespaceStatus::default());
     }
 
+    let status = NamespaceStatus {
+        user: true,
+        mount: true,
+        net: network_namespace,
+    };
+
     // "deny" must be written before gid_map when inside a user namespace
     std::fs::write("/proc/self/setgroups", "deny")?;
     std::fs::write("/proc/self/uid_map", format!("0 {uid} 1\n"))?;
     std::fs::write("/proc/self/gid_map", format!("0 {gid} 1\n"))?;
 
-    eprintln!("[sandbox] entered user+mount namespaces (uid={uid}, gid={gid})");
-    Ok(())
+    // Name the network namespace explicitly either way: this log is the operator's
+    // only signal, and "entered namespaces" that silently omitted the one that
+    // matters is what BL-042 had to reconstruct from source.
+    let mut entered: Vec<&str> = Vec::new();
+    if status.user {
+        entered.push("user");
+    }
+    if status.mount {
+        entered.push("mount");
+    }
+    if status.net {
+        entered.push("net");
+    }
+
+    eprintln!(
+        "[sandbox] entered {} namespaces (uid={uid}, gid={gid}); network namespace {}",
+        entered.join("+"),
+        if status.net {
+            "established"
+        } else {
+            "not requested"
+        }
+    );
+    Ok(status)
 }
 
 #[cfg(not(target_os = "linux"))]
-pub fn enter_namespaces() -> anyhow::Result<()> {
-    Ok(())
+pub fn enter_namespaces(_network_namespace: bool) -> anyhow::Result<NamespaceStatus> {
+    // No namespaces anywhere but Linux, so `net: false` is the honest report. A caller
+    // that requires network containment gets a refusal rather than a silent pass.
+    Ok(NamespaceStatus::default())
 }
 
 /// Mounts an OverlayFS at `merged`, presenting `lower` as read-only and directing all writes
```

### 10. Diff — agents (`aetheris-agents/` @ `0d5676a`), backlog only

The contract draft added by the same commit is reproduced in full in §7; only the backlog
diff is repeated here, to avoid duplicating it.

```diff
commit 0d5676a3b5b9b0f3031eced7cfbbef0e4e273c57
Author: Vishal Honnatti <vishal@bitloka.com>
Date:   Thu Jul 23 13:47:07 2026 +0530

    BL-042 done + follow-ups (BL-047, BL-048); §5 contract draft (3 statements)
    
    Harness side landed in ../aetheris @ 72a7f5e (conditional CLONE_NEWNET,
    establishment status through a reordered handshake, fail-closed enforcement in
    Worker.Client.init, run_command routing).
    
    - BL-042 row closed with the four-arm evidence table and the decisions that do
      not survive in the code: `lo` left down; a /proc mapping-write failure keeps
      log-and-continue and reports network_namespace: false, so record's fail-open
      survives that path while verify still refuses; non-Linux hosts refuse.
    - BL-047 filed — the git_* half of the routing gap. Not a three-line fix
      deferred out of laziness: whether mutating git ops (commit/checkout/
      cherry_pick) should re-execute under verify at all is a taxonomy decision of
      BL-025's weight, and inheriting it from a routing accident is how it would
      otherwise get decided.
    - BL-048 filed — `mix test --include requires_worker` is red with 15 failures,
      identical on a clean tree, invisible to CI (ci.yml excludes the tag) and to
      every default mix test (test_helper excludes it too). Found off-territory by
      this ticket's own done-check; three distinct causes, one of which (nil
      fs_hash) may be a live defect rather than a stale test.
    - docs/reviews/bl-042-contract-draft.md — the §5 edit for §8 approval, as three
      statements rather than the two the row scoped: (a) partial ->
      capability-complete, (b) conditional on establishability with the fail-closed
      refusal named as contract-visible behaviour, and (c) a correction of BL-025's
      "`:contained` ... re-executed and compared", which was false for the whole
      exec-server family. (c) is not optional: §8 forbids leaving a known-false
      guarantee standing.
    
    Priority table: BL-042 marked done, BL-043 noted as now-unblocked (the netns
    landed, so restoring setsockopt egress no longer widens an open window).
    
    Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>

diff --git a/docs/backlog-2026-06.md b/docs/backlog-2026-06.md
index 7b8b41e..b5f3fc8 100644
--- a/docs/backlog-2026-06.md
+++ b/docs/backlog-2026-06.md
@@ -1957,6 +1957,49 @@ Pre-implementation handoff verified at 8021a59, 2026-07-23.`
 
 ---
 
+### BL-042 — DONE 2026-07-23
+
+**Landed:** conditional `CLONE_NEWNET` (`sandbox.rs:161-224`, gated on the init payload's
+`network_namespace`), establishment status reported through a reordered handshake (namespaces
+entered *before* `ready`, which now carries `network_namespace` — `main.rs:56-74`),
+fail-closed enforcement in `Worker.Client.init/1` via `containment_verdict/2`, the netns
+requested as `not allow_effects` by `Verifier` (`verifier.ex:89-96`), a legible CLI refusal,
+and `network_isolated` on `VerifyReport` so a networked divergence is interpretable.
+
+**Grew in-cycle by one tool, and the growth was load-bearing.** H6's red-first arm could not
+be written as specified: `Verifier` sent every tool to the worker's own dispatch table, but
+`run_command` is an exec-server MCP tool, so it re-executed as `unknown_tool:run_command` and
+opened **0 connections before the netns existed**. The row's "0 hits" done-when was already
+true, for a reason that had nothing to do with containment — a check that could not fail.
+Routing `run_command` (scoped decision, human, 2026-07-23) made the red arm real; the
+`git_*` family was left alone and filed as **BL-047** with the taxonomy question it deserves.
+
+**Evidence** (`test/aetheris/execution/verify_effects_test.exs`, `--include requires_worker`;
+the tag is excluded by default, so a plain `mix test` exercises neither arm):
+
+| arm | connections | step status |
+|---|---|---|
+| pre-fix, unrouted | 0 | `:error` — `unknown_tool:run_command`, never ran |
+| pre-netns, routed | **1** | re-executed and egressed — the red arm |
+| default verify (netns) | **0** | `:output_mismatch` + isolation note |
+| `--allow-effects` | **≥1** | `:verified` — opt-in preserved (H4) |
+
+**Decisions recorded** (implementation notes: `../aetheris/docs/aetheris/milestones/bl-042-implementation-notes.md`):
+H2 `lo` left down — no code brings it up. On a `/proc` mapping-write failure the worker keeps
+its log-and-continue and reports `network_namespace: false`, so record's fail-open survives
+that path too while verify still refuses. Non-Linux hosts report `net: false`, so a default
+verify there refuses — fail-closed working as ratified, named in §5 rather than discovered.
+
+**Off-territory gate finding:** `mix test --include requires_worker` is red with 15 failures,
+identical on a clean tree — filed as **BL-048**, not carried silently.
+
+**§5 contract edit:** drafted in `docs/reviews/bl-042-contract-draft.md` as three statements
+— (a) partial → capability-complete, (b) conditional on establishability with the fail-closed
+refusal named as contract-visible, and (c) the correction of BL-025's false "`:contained` …
+re-executed and compared" claim. Lands only on human approval per §8.
+
+---
+
 ### BL-043 — `http_call` is killed by seccomp (SIGSYS) in every mode: `setsockopt` missing from the allowlist (#TBD)
 **Size:** S · **Priority:** medium · **Section:** Harness (aetheris/)
 
@@ -2043,6 +2086,93 @@ change rather than as a side effect.
 
 ---
 
+### BL-047 — Verify never re-executes the `git_*` family: exec-server routing gap + a taxonomy decision (#TBD)
+**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)
+
+`Verifier` re-executes a recorded tool by sending it to the worker's own dispatch table
+(`Client.execute` → `main.rs` `dispatch/3`), which knows only `read_file`, `list_dir`,
+`write_file`, `http_call`. But `run_command` and the eleven `git_*` tools are **exec-server
+MCP tools** in a live run (`loop.ex` `@exec_server_tools`, `dispatch_mcp_tool/4`). So every
+member of that family re-executed as `unknown_tool:<name>` — a per-step `:error`, never a
+comparison — while determinism-contract §5 claimed `:contained` tools are "re-executed and
+compared".
+
+Demonstrated at BL-042 against unmodified `8021a59`, before any fix:
+
+```
+%{error: "unknown_tool:run_command", status: :error, actual_output: nil,
+  recorded_output: "{\"duration_ms\":20,\"exit_code\":0,\"stderr\":\"\",\"stdout\":\"connected\\n\"}"}
+```
+
+**BL-042 routed `run_command` only** — the tool its own containment proof requires, whose
+re-execution BL-025 already ratified, and whose new hazard (egress) is exactly what BL-042's
+network namespace contains. The `git_*` family was deliberately left unrouted rather than
+fixed by the same three lines, because routing it is not merely a bug fix:
+
+**The real question is whether mutating git operations should re-execute under verify at
+all.** `git_add`, `git_commit`, `git_checkout`, `git_cherry_pick` and
+`git_cherry_pick_control` mutate a repository. Re-executing `git_commit` against a sandbox
+whose HEAD has moved does not reproduce a recorded step, it writes a new one; `git_checkout`
+can destroy working-tree state that the recorded run did not have. The read-only members
+(`git_status`, `git_diff`, `git_diff_staged`, `git_log`, `git_show`) are a different case
+entirely. This is a taxonomy decision of the same weight as BL-025's three classes and it
+should be **decided**, not inherited from an accident of routing — which is the whole reason
+BL-042 did not quietly extend its own fix over the family.
+
+**Options to adjudicate (not a menu to pick from silently):** route them all as `:contained`;
+split the family, re-executing the read-only members and reclassifying the mutating ones as
+`:uncontained` (record-and-served); or declare the family unsupported under verify with an
+explicit status distinct from `:error`.
+
+**Done when:** the classification of each `git_*` tool is decided and recorded in §5 with a
+human-approved edit (§8), the implementation matches the decision, and a recorded `git_*`
+trajectory verifies to whatever verdict that decision implies — never to
+`unknown_tool:<name>`. §5's routing-gap paragraph and §3's verify row (both landed by BL-042)
+are updated to remove the named gap.
+
+`Source: BL-042 execution, demonstrated 2026-07-23 at 8021a59. §5 correction landed with
+BL-042's contract edit; this row closes the gap that correction names.`
+
+---
+
+### BL-048 — The `requires_worker` test set is red: 15 failures, invisible to CI and to every default `mix test` (#TBD)
+**Size:** M · **Priority:** medium · **Section:** Harness (aetheris/)
+
+`mix test --include requires_worker` reports **15 failures** on `main` at `8021a59`, with no
+BL-042 changes applied (verified by stashing them and re-running: the failing set is
+byte-identical, 900 tests / 15 failures). CI never sees them — `ci.yml:64` runs
+`--exclude requires_worker --exclude integration` — and neither does a local `mix test`,
+because `test_helper.exs:4` excludes the same tags by default. Found off-territory by
+BL-042's own done-check, which is the only reason it is on the record at all.
+
+Three distinct causes, not one:
+
+- **Test written against a stale allowlist** — `run_command_test.exs` uses `pwd`, which is not
+  in `PERMITTED_COMMANDS` (`aetheris_exec_server/src/runner.rs:7-24`); the exec server
+  correctly answers `command not permitted: pwd`. 3 failures.
+- **`fs_hash` is nil where the test expects `sha256:…`** — `client_test.exs:53`,
+  `fs_hash_stability_test.exs` (×2). This one is **not** obviously a stale test and may be a
+  live defect in worker fs-hashing; it needs diagnosis, not a test edit.
+- **Network/credential-dependent integration tests pulled in by the include** — `httpbin.org`,
+  the GitHub MCP server, the HTTP MCP transport. `--include requires_worker` overrides the
+  `:integration` exclusion for tests carrying both tags, so these run whether or not the
+  environment can support them. 6+ failures.
+
+**This is the gate-rot pattern the CLAUDE.md gate rule exists to catch**, running in the
+direction that is hardest to see: a set that no gate executes cannot go red visibly, so it
+went red silently and stayed. When it broke is unknown, because nothing was watching.
+
+**Done when:** each failure is triaged to stale-test / live-defect / environment-dependent;
+stale tests are corrected, live defects get their own rows, environment-dependent tests are
+tagged so an include cannot drag them into a run that cannot satisfy them; and the set is
+wired into something that runs it — a sprint case or a CI job with the worker available —
+so it cannot rot invisibly again. Until then it is a **known-red gate named with this ticket
+ref** in packets, not re-triaged each time.
+
+`Source: BL-042 done-check, off-territory, 2026-07-23. Baseline captured on a clean tree.`
+
+---
+
 ### BL-045 — `RunConfig mode: :verify` is a misnomer: no verification semantics (#TBD)
 **Size:** S · **Priority:** low · **Section:** Harness (aetheris/)
 
@@ -2308,8 +2438,10 @@ multi-line street/city/state/zip.
 | 13 | BL-028 | Silent-empty is the worst failure shape: a fork proceeds from a wrong context with no signal |
 | 14 | BL-031 | Small resilience fix; converts a class of hangs into a legible error. Cheaper before BL-030 changes the fork call shape |
 | ✔ | BL-025 | **Done 2026-07-23.** Grew in-cycle to include the CLI rewire (it never reached `Verifier`). Spawned BL-042/043/044/045 |
-| 15 | BL-042 | Inherits BL-025's slot: closes the *incidental* egress BL-025 named but could not fix. Must follow BL-025 (landed), and should precede BL-043 — repairing `setsockopt` before the netns exists widens the window |
-| 15a | BL-043 | `http_call` is dead in every mode, so nothing regresses by waiting; but it is the reason BL-042's exposure looks smaller than it is. Confirm the tool has no live users before choosing repair-vs-retire |
+| ✔ | BL-042 | **Done 2026-07-23.** Grew in-cycle by one tool: `run_command` was never re-executed under verify at all (`unknown_tool`), so the netns had nothing to contain until the routing was fixed. Spawned BL-047 (the `git_*` half of that gap, plus its taxonomy question) and BL-048 (the red `requires_worker` set found off-territory) |
+| 15 | BL-043 | `http_call` is dead in every mode, so nothing regresses by waiting; but it is the reason BL-042's exposure looks smaller than it is. Confirm the tool has no live users before choosing repair-vs-retire. **Now unblocked**: BL-042's netns has landed, so restoring egress no longer widens an open window |
+| 15a | BL-047 | The `git_*` half of the routing gap BL-042's §5 correction names. Decide the mutating-vs-read-only classification *first*; the routing is three lines once the taxonomy is settled |
+| 15a2 | BL-048 | Known-red gate, tracked not carried. Triage before anything cites "the worker tests pass" |
 | 15b | BL-038 | Medium, operator-facing, and it carries the shared find-run-by-id piece so BL-024 (19b) inherits it rather than the reverse — deciding which lands first rather than leaving "whichever" open |
 | 15c | BL-039 | Ahead of BL-030 — an early-return fork UX matters little while real-provider forks fail at the first LLM call. Builds atop BL-028's landed state (same clause, `fork.ex:101-105`); must not race it |
 | 16 | BL-030 | Unblocks a non-blocking fork UX; do after BL-031 so the wait path is already bounded |
```

---

### 11. Backlog rows filed this round

- **BL-047** — Verify never re-executes the `git_*` family: the exec-server routing gap
  plus the taxonomy question (should mutating git ops re-execute under verify at all?).
  Filed as a row in the same round it was deferred, not left as prose.
- **BL-048** — `mix test --include requires_worker` red with 15 failures, invisible to
  CI and to every default `mix test`. Off-territory gate finding; tracked, not carried.
- **BL-042** — row closed with the four-arm evidence table and the decisions that do not
  survive in the code. **BL-043** noted as now-unblocked in the priority table.

### 12. Done-when

| clause | status |
|---|---|
| verify worker runs under `CLONE_NEWNET` when re-executing without `--allow-effects` | done — `sandbox.rs:169-172`, requested at `verifier.ex:89-96`; worker log shows `network namespace established` on exactly the default-verify arm (§1d) |
| a recorded networked `run_command` cannot egress during verify (0 hits) | done — §2c, delta 0, against a red arm that showed 1 (§2b) |
| its divergence is reported legibly | done — `:output_mismatch` plus the isolation note and header line (§3) |
| `--allow-effects` still egresses; BL-025 opt-in arm still asserts ≥1 | done — §2c arm 4 |
| netns establishment reported by the worker and acted on by verify, never silently assumed | done — status rides `ready` (`main.rs:56-74`), enforced in `Client.init/1` via `containment_verdict/2` (§2e) |
| `record` mode fail-open untouched | done — §4; record passes `network_namespace: false`, flags identical to before |
| `http_call`/MCP remain served, do not fail under the netns | done — the two untagged BL-025 tests still pass (§1d) |
| §5 edit as two statements, human-approved in-cycle | **drafted, three statements, awaiting approval** (§7). Not landed. |
| complete output or stated truncation in every section | done — one truncation stated, §1d |
| push held | held — both repos committed locally, nothing pushed |

**Outstanding:** §5 approval. Everything else is complete.
