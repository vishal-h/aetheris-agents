# Review packet — BL-039: fork continuation against real providers (Design A)

Reviewer: claude-ui. Base: agents `81ef532` / harness `78df9f1`.
Implementation: harness `ebc3878` (docs-first §4), `e44d35c` (code+tests), `3f561d9` (notes);
agents `7d6013a` (mirrors), `0f48c09` (backlog: BL-039 done, BL-060 filed).

---

## 1. Done-check output

### 1a. Harness gate line

```
$ mix deps.get
Resolving Hex dependencies...
Resolution completed in 0.097s
Unchanged:
  bandit 1.11.1 VULNERABLE!
    EEF-CVE-2026-65623 (HIGH)
    aka: CVE-2026-65623, GHSA-vg8x-66vg-5pxh
    Quadratic CPU blow-up reassembling fragmented WebSocket messages in Bandit
    https://osv.dev/vulnerability/EEF-CVE-2026-65623
  bunt 1.0.0
  cc_precompiler 0.1.11
  credo 1.7.18
  crontab 1.2.0
  db_connection 2.10.1
  dialyxir 1.4.7
  elixir_make 0.9.0
  erlex 0.2.8
  exqlite 0.36.0
  file_system 1.1.1
  finch 0.23.0
  hpax 1.0.4
  jason 1.4.5
  mime 2.0.7
  mint 1.9.3
  nimble_options 1.1.1
  nimble_pool 1.1.0
  plug 1.20.3
  plug_crypto 2.1.1
  req 0.6.3
  telemetry 1.4.2
  thousand_island 1.4.3
  websock 0.5.3
Found packages with security advisories, see above for details
All dependencies are up to date

$ mix hex.audit
Advisories:
  bandit 1.11.1 - EEF-CVE-2026-65623 (HIGH)
    aka: CVE-2026-65623, GHSA-vg8x-66vg-5pxh
    Quadratic CPU blow-up reassembling fragmented WebSocket messages in Bandit
    https://osv.dev/vulnerability/EEF-CVE-2026-65623

Found packages with security advisories
exit=1
$ mix compile --warnings-as-errors
exit=0

$ mix format --check-formatted
exit=0

$ mix credo --strict
Please report incorrect results: https://github.com/rrrene/credo/issues

Analysis took 3.2 seconds (0.1s to load, 3.0s running 69 checks on 228 files)
2043 mods/funs, found no issues.

Use `mix credo explain` to explain issues, `mix credo --help` for options.

$ mix dialyzer
Total errors: 0, Skipped: 0, Unnecessary Skips: 0
done in 0m5.14s
done (passed successfully)
$ mix test
..............................................................
Finished in 90.1 seconds (3.5s async, 86.6s sync)
965 tests, 0 failures, 133 excluded
```

`mix hex.audit` is **expected-red, tracked as BL-060** (filed in this ticket, `0f48c09`):
`bandit 1.11.1` / `EEF-CVE-2026-65623`, published upstream under a lock nobody touched.
Named per the tracked-carry clause, not re-triaged, and not fixed here — out of BL-039's
scope. Every other gate is green.

### 1b. The three BL-039 done-check arms, plus the fork/CLI suites

```
$ mix test test/aetheris/execution/fork_test.exs test/aetheris/execution/canonical_message_test.exs \
      test/aetheris/cli/commands/fork_test.exs test/aetheris/cli/commands/run_helpers_test.exs \
      --include requires_real_provider --trace
Running ExUnit with seed: 364091, max_cases: 1
Excluding tags: [:requires_worker, :integration, :m10_fixture, :requires_internet]
Including tags: [:requires_real_provider]
Aetheris.Execution.CanonicalMessageTest [test/aetheris/execution/canonical_message_test.exs]
  * test tool_result_message/3 pairs a user turn to the tool_use id * test tool_result_message/3 pairs a user turn to the tool_use id (2.8ms) [L#54]
  * test assistant_tool_use_message/2 builds a single tool_use block on an assistant turn * test assistant_tool_use_message/2 builds a single tool_use block on an assistant turn (0.00ms) [L#6]
  * test assistant_tool_use_message/2 normalizes a nil tool_input to an empty object * test assistant_tool_use_message/2 normalizes a nil tool_input to an empty object (0.00ms) [L#20]
  * test assistant_tool_use_message/2 attaches a thought signature only when present * test assistant_tool_use_message/2 attaches a thought signature only when present (0.00ms) [L#33]
  * test tool_result_message/3 marks is_error only when true * test tool_result_message/3 marks is_error only when true (0.00ms) [L#67]
Aetheris.Execution.ForkTest [test/aetheris/execution/fork_test.exs]
  * test from_step/3 rebuilds a tool step into a paired tool_use / tool_result turn * test from_step/3 rebuilds a tool step into a paired tool_use / tool_result turn (7.0ms) [L#189]
  * test from_step/3 encodes a map-valued tool result as a JSON string * test from_step/3 encodes a map-valued tool result as a JSON string (0.6ms) [L#300]
  * test forked run trajectory meta includes fork_from and fork_step * test forked run trajectory meta includes fork_from and fork_step (59.0ms) [L#333]
  * test from_step/3 with valid step returns config with fork_context populated * test from_step/3 with valid step returns config with fork_context populated (4.1ms) [L#144]
  * test from_step/3 inherits meta seed unless overridden * test from_step/3 inherits meta seed unless overridden (1.5ms) [L#165]
  * test from_step/3 leaves seed nil when source meta has none * test from_step/3 leaves seed nil when source meta has none (1.2ms) [L#176]
  * test Anthropic accepts a reconstructed fork prefix with a synthesised tool_use id * test Anthropic accepts a reconstructed fork prefix with a synthesised tool_use id (1985.4ms) [L#500]
  * test from_step/3 with unknown run_id returns :not_found * test from_step/3 with unknown run_id returns :not_found (0.1ms) [L#329]
  * test from_step/3 with step beyond available step_complete returns :step_not_found * test from_step/3 with step beyond available step_complete returns :step_not_found (6.0ms) [L#322]
  * test from_step/3 carries is_error onto the tool_result block when recorded * test from_step/3 carries is_error onto the tool_result block when recorded (1.0ms) [L#225]
  * test a reconstructed fork context builds a wire-valid Anthropic request body * test a reconstructed fork context builds a wire-valid Anthropic request body (2.0ms) [L#451]
  * test from_step/3 normalizes a nil-valued tool result to the empty string * test from_step/3 normalizes a nil-valued tool result to the empty string (0.7ms) [L#278]
  * test from_step/3 rebuilds in-process ("result"-keyed) tool_result events * test from_step/3 rebuilds in-process ("result"-keyed) tool_result events (0.6ms) [L#257]
  * test from_step/3 omits is_error on a successful tool_result block * test from_step/3 omits is_error on a successful tool_result block (0.6ms) [L#244]
  * test a fork of a tool-call step continues past step 0 from a reconstructed context * test a fork of a tool-call step continues past step 0 from a reconstructed context (53.8ms) [L#377]
Aetheris.CLI.Commands.ForkTest [test/aetheris/cli/commands/fork_test.exs]
  * test fork with step routes through from_step, replaying context and carrying seed * test fork with step routes through from_step, replaying context and carrying seed (319.9ms) [L#23]
  * test fork without step returns expected error * test fork without step returns expected error (102.8ms) [L#43]
  * test a failed fork's error message carries the run's terminal reason * test a failed fork's error message carries the run's terminal reason (305.1ms) [L#53]
Aetheris.CLI.Commands.RunHelpersTest [test/aetheris/cli/commands/run_helpers_test.exs]
  * test terminal_error_reason returns nil for a run with no error event * test terminal_error_reason returns nil for a run with no error event (1.1ms) [L#61]
  * test lookup_run normalizes mcp_servers entries to atom-key maps * test lookup_run normalizes mcp_servers entries to atom-key maps (0.6ms) [L#17]
  * test await_run returns cancelled error and prints cancellation message * test await_run returns cancelled error and prints cancellation message (5.5ms) [L#32]
  * test terminal_error_reason returns the last recorded :error reason * test terminal_error_reason returns the last recorded :error reason (1.2ms) [L#47]
  * test terminal_error_reason returns nil when no event source is readable * test terminal_error_reason returns nil when no event source is readable (0.1ms) [L#69]
Finished in 3.0 seconds (0.2s async, 2.8s sync)
28 tests, 0 failures
```

### 1c. Mutation checks — each arm is load-bearing

```
### M1 — revert the assistant tool_use reconstruction (tool_call_messages/2 -> [])
  1) test from_step/3 rebuilds a tool step into a paired tool_use / tool_result turn (Aetheris.Execution.ForkTest)
     code:  assert config.fork_context == [
     left:  [
     right: [
  2) test a fork of a tool-call step continues past step 0 from a reconstructed context (Aetheris.Execution.ForkTest)
     code:  assert [
     left:  [
     right: [
  3) test a reconstructed fork context builds a wire-valid Anthropic request body (Aetheris.Execution.ForkTest)
     code:  assert length(blocks_of_type(messages, "tool_use")) == 1
     left:  0
     right: 1
15 tests, 3 failures, 1 excluded

### M2 — revert the tool_result turn to the pre-BL-039 role: "tool" message
  1) test Anthropic accepts a reconstructed fork prefix with a synthesised tool_use id (Aetheris.Execution.ForkTest)
     code:  assert {:ok, response} = Anthropic.call(nil, request)
     left:  {:ok, response}
     right: {:error,
             "HTTP 400: messages: Unexpected role \"tool\". Allowed roles are \"user\" or \"assistant\". For instructions on how to use tools, see https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview."}
15 tests, 1 failure, 14 excluded

### M3 — revert Part C (await_fork/1 -> RunHelpers.await_run/1)
  1) test a failed fork's error message carries the run's terminal reason (Aetheris.CLI.Commands.ForkTest)
     code:  assert message =~ "unknown provider: no-such-provider"
     left:  "run fork-042ba2f15f7948ed failed"
     right: "unknown provider: no-such-provider"
3 tests, 1 failure

### restored
working tree clean vs HEAD
```

**M2 is the one that matters.** With reconstruction reverted, the real-provider arm returns
`HTTP 400: messages: Unexpected role "tool". Allowed roles are "user" or "assistant".` —
byte-identical to the reason recorded in `priv/runs/fork-aa6a6a65804f6645/trajectory.json`.
The field failure is reproduced against the live API and closed by the same test, which also
proves the arm reaches the endpoint rather than a stub.

### 1d. Cross-repo done-check — `aetheris-agents/`

```
$ python3 scripts/drift_check.py --strict          # aetheris-agents/, post-commit
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
[WARN] project_knowledge: docs/rig/specs.md stale — manifest=c39bf7e current=c0977c2
[WARN] project_knowledge: docs/rig/architecture.md stale — manifest=d82cf7e current=c0977c2
[WARN] project_knowledge: docs/rig/runbook.md stale — manifest=d0690a6 current=7d6013a
[WARN] project_knowledge: docs/backlog-2026-06.md stale — manifest=6a8a32e current=0f48c09
[WARN] project_knowledge: docs/aetheris/runbook.md stale — manifest=915d582 current=ebc3878
[WARN] project_knowledge: docs/aetheris/determinism-contract.md stale — manifest=dd12dbb current=ebc3878
[PASS] command_fields: 10 documented §4 structs (54 fields) match commands/*.rs

Summary: 8 PASS  0 FAIL  6 WARN  7 INFO
exit=0

$ python3 -m pytest tests/test_drift_check.py -q
...................................................                      [100%]
51 passed in 0.45s

$ cd rig && bun run tsc -b && bun run lint && bun run build
tsc exit=0
$ eslint .
lint exit=0

✓ built in 600ms
```

Zero FAIL. The six WARNs are all `project_knowledge` manifest staleness — the named
`--strict` exemption, so `exit=0`. Four are staled by this ticket's own commits
(`rig/runbook.md` @ `7d6013a`, `backlog-2026-06.md` @ `0f48c09`, `aetheris/runbook.md` and
`determinism-contract.md` @ `ebc3878`); `rig/specs.md` and `rig/architecture.md` @ `c0977c2`
were already stale from BL-038 and predate this work. Named, not chased — the export
boundary is the enforcement point.

**Not run:** the agent sprint beyond its `drift_check` case (`./scripts/sprint.sh drift_check`
— PASS, output above is the same checker it invokes). The remaining cases drive real
use-case agents against paid providers and BL-039 touches no agent file, no script, and no
tool; the harness paths they would exercise are covered by `mix test` 965/0. Stated rather
than silently skipped.

---

## 2. Diff

### 2a. Harness — `ebc3878~1..HEAD`

```
 docs/aetheris/determinism-contract.md              |  53 ++-
 .../milestones/bl-039-implementation-notes.md      |  96 ++++++
 docs/aetheris/runbook.md                           |  28 +-
 lib/aetheris/cli/commands/fork.ex                  |  21 +-
 lib/aetheris/cli/commands/run_helpers.ex           |  33 ++
 lib/aetheris/execution/canonical_message.ex        |  83 +++++
 lib/aetheris/execution/fork.ex                     |  62 +++-
 lib/aetheris/execution/loop.ex                     |  44 +--
 test/aetheris/cli/commands/fork_test.exs           |  19 ++
 test/aetheris/cli/commands/run_helpers_test.exs    |  32 ++
 test/aetheris/execution/canonical_message_test.exs |  76 +++++
 test/aetheris/execution/fork_test.exs              | 366 +++++++++++++++++++--
 12 files changed, 813 insertions(+), 100 deletions(-)
```

```diff
diff --git a/docs/aetheris/determinism-contract.md b/docs/aetheris/determinism-contract.md
index bbedcf1..11df1cb 100644
--- a/docs/aetheris/determinism-contract.md
+++ b/docs/aetheris/determinism-contract.md
@@ -45,9 +45,12 @@ happen if the run were executed again.
 - **Transcript** — the ordered conversation messages reconstructable from recorded
   events. For fork, precisely: the initial user prompt (verbatim from
   `meta["user_prompt"]`), each `:llm_responded` event with `response_type == "text"`
-  as a verbatim assistant message, and each `:tool_result` event as a tool message
-  (`fork.ex:73-125`). **Assistant tool-call turns are not reconstructed** — see §4
-  known limitations.
+  as a verbatim assistant message, and each `:llm_responded` event with a tool-call
+  response type as an assistant turn carrying a `tool_use` content block, paired with
+  the same step's `:tool_result` event as a `user` turn carrying the matching
+  `tool_result` block. **Assistant tool-call turns are reconstructed** (BL-039) — see
+  §4 for the pairing rule and what the reconstructed prefix does and does not
+  preserve.
 - **Environment** — the per-run OverlayFS working directory, the wall clock, and
   the RNG seed. Distinct from the transcript; the contract treats them separately.
 
@@ -121,17 +124,39 @@ step with a recorded `:step_complete` event, matched **exactly**
 (CLI, Rig) MUST offer fork only on completed steps. The "at or before" docstrings
 (`fork.ex:15-18`, `aetheris.ex:64-69`) are defects corrected in t1.
 
-**Known limitation (documented, not guaranteed away):** non-text assistant turns
-(tool-call turns) are dropped in reconstruction (`fork.ex:88-111`). The prefix a
-forked run sees is therefore the *text-and-tool-results* transcript, not a
-byte-copy of the source context at step *N*. Changing this is future work and
-requires a doc edit here first.
-
-*Demonstrated consequence (2026-07-20): a fork continuation against the Anthropic
-provider fails at its first LLM call — the reconstructed tool-role message is
-rejected (HTTP 400), and relabeling alone cannot fix it because the paired assistant
-`tool_use` turns are not reconstructed. Stub-provider forks are unaffected.
-Tracked: BL-039 (`../aetheris-agents/docs/backlog-2026-06.md`).*
+**Fork reconstruction (BL-039).** A forked run's prefix is rebuilt from the source
+trajectory in the harness's canonical message form — the internal shape every
+provider's adapter already translates from, so the reconstructed prefix drives any
+provider, not only the one the source used. An assistant tool-call turn is
+reconstructed as a `tool_use` content block, paired with a `tool_result` block on the
+following `user` turn, exactly as the live execution loop builds them.
+
+The trajectory does not record the provider's original `tool_use` id, so
+reconstruction synthesises one per call and uses it for both halves of the pair. The
+id is opaque to the harness, which never validates it and requires only that the two
+halves of a pair agree; the harness already synthesises tool-call ids in production
+for providers that supply none, so the device is not new. Whether a given provider
+accepts a synthesised id in a replayed assistant turn is a claim about that provider's
+API, established by the real-provider arm of BL-039's done-check rather than by this
+clause.
+
+Each recorded tool result is paired with the tool call recorded at the same step. That
+pairing is **positional**, and it is sound only while a step carries at most one tool
+call. That is not a property of the provider APIs — Anthropic's permits parallel tool
+use and the harness does not disable it — but of the Anthropic adapter's response
+parse, which keeps the first `tool_use` block of a response and discards any others.
+Fork reconstruction therefore depends on adapter behaviour, and this sentence is the
+record of that dependency: if the adapter is changed to surface parallel tool calls,
+reconstruction's pairing must be changed with it. (Tracked separately as **BL-059** —
+the discard is a live defect in the record path, not a fork concern.)
+
+The reconstructed prefix is therefore not a byte-copy of the source context —
+synthesised ids, and assistant text emitted alongside a tool call is not recorded, so
+a reconstructed tool-call turn is tool_use-only — but it is the canonical shape the
+source ran on, and a fork continues against any provider whose adapter consumes that
+shape, including one different from the source's. Selecting a different provider is a
+capability of `Aetheris.fork_run/3`'s `overrides`; the CLI and Rig entry points pass a
+label only (BL-030).
 
 **Entry points (D2, ratified 2026-07-18):** `Aetheris.fork_run/3` and the CLI
 `aetheris fork <traj> --step N` MUST be behaviorally equivalent — both route
diff --git a/docs/aetheris/milestones/bl-039-implementation-notes.md b/docs/aetheris/milestones/bl-039-implementation-notes.md
new file mode 100644
index 0000000..1caedf0
--- /dev/null
+++ b/docs/aetheris/milestones/bl-039-implementation-notes.md
@@ -0,0 +1,96 @@
+# BL-039 — fork continuation against real providers (Design A)
+
+Harness `ebc3878` (docs-first §4) + `e44d35c` (implementation). Agents half:
+`7d6013a` (mirrors). Written against the ratified clause in
+`docs/reviews/bl-039-contract-draft.md` and the scout memo, which lives in
+`../aetheris-agents/docs/reviews/bl-039-fork-continuation-scout.md` (the ticket
+text places it in this repo; it is in the sibling).
+
+## Why the id is derived from the step, not generated
+
+The obvious device — mint a random id and thread it from the `:llm_responded`
+clause to the `:tool_result` clause — needs state between two clauses of a
+`flat_map`, which means restructuring `extract_context/3` into a step-aware
+fold. Deriving the id from the step instead (`"fork-toolu-#{step}"`) makes both
+halves agree *by construction*, keeps each clause independent, and has a
+property generation does not: two forks of the same run at the same step
+produce a byte-identical prefix, so `context_hash` is stable. §4 already says
+the id is opaque and only has to match within the pair, so nothing is lost.
+
+## The orphan case that cannot arise, and why there is no guard for it
+
+An assistant `tool_use` turn with no following `tool_result` would be rejected
+by the API, so it is worth stating why reconstruction cannot emit one. A fork
+point must have a `step_complete` (`find_step_complete_at/2`, exact match), and
+`step_complete` is appended only after `execute_response/4` returns `{:ok, …}`.
+Both tool outcomes reach that: success appends a `:tool_result`, and
+`record_tool_error/6` appends one with `"is_error" => true` and *also* returns
+`{:ok, …}`. The only tool path that returns `{:error, …}` is loop detection,
+which appends no `step_complete` and ends the run — so that step is always the
+last one, and can never sit *below* a valid fork step. Hence: within any
+context reconstruction can be asked to build, every tool-call turn has its
+result. A guard here would be unreachable code, and unreachable code cannot be
+mutation-checked, so it would be a claim rather than a check.
+
+Text turns are a related non-case: a `:text` response terminates the run
+(`handle_llm_response/4`'s `%{type: :text}` clause writes `run_complete`
+directly), so a text step never has a `step_complete` either. The text clause
+in `event_to_messages/1` is kept because it is correct and cheap, not because a
+well-formed trajectory exercises it below a fork point.
+
+## Two scout claims corrected at HEAD
+
+The scout's line-level facts were re-verified at `78df9f1` before the first
+edit. Two need recording, neither changing any conclusion:
+
+- **§4's "one constraint the design must respect"** attributes the key-dropping
+  to `Agent.Server.normalize_context_entry/1`, and quotes both clauses as
+  fetching `"content"`. At HEAD the atom-key clause fetches `:content`, and
+  more importantly that function is not on the wire path at all: it feeds
+  `Agent.Server`'s `context:` state field. The messages that reach the adapter
+  come from `Loop.run/5`, which takes `config.fork_context` **unnormalized**.
+  So the old message's `"tool_name"` sibling was passed through to
+  `build_request_body/2`, not dropped before it. The design instruction is
+  unaffected — everything belongs in `content` either way, and now does — but
+  the reason is "the canonical shape has no top-level siblings", not "the
+  normalizer would drop them".
+- The scout says the pre-BL-039 `role: "tool"` message "feeds none of the four
+  providers correctly". Confirmed, and worth keeping in view for BL-030: the
+  fix is what makes cross-provider forking real, not merely legal.
+
+## Arm 3 is the one that settles the contract
+
+§4 deliberately does not assert that Anthropic accepts a synthesised id in a
+*replayed* assistant turn — the live path had only ever sent Anthropic its own
+`toolu_…` ids back. Arm 3 was run manually against the real API: **PASS**. The
+mutation is the useful half: with reconstruction reverted, the same arm returns
+`HTTP 400: messages: Unexpected role "tool". Allowed roles are "user" or
+"assistant".` — byte-identical to the reason recorded in
+`priv/runs/fork-aa6a6a65804f6645/trajectory.json`. So the arm demonstrably
+reaches the endpoint, and the field failure is reproduced and then closed by the
+same test.
+
+It stays excluded by default (network, key, cost). Anyone re-running it needs
+`--include requires_real_provider`; it skips itself without `ANTHROPIC_API_KEY`,
+and it swaps `:req_options` because `config/test.exs` points them at a
+`Req.Test` stub plug — a done-check written against the assumed runtime shape
+fails here immediately, which is how that was found.
+
+## What the next fork ticket needs to know
+
+- **BL-059 disposition (a) breaks this file without touching it.** Positional
+  pairing is sound only while a step carries one tool call. The dependency is
+  named at `synthetic_tool_use_id/1` and in §4; BL-059's row carries the
+  reciprocal. If (a) lands, fork's done-check is part of that diff.
+- **BL-030 inherits a real capability now.** `fork_run/3`'s `overrides` can
+  select a different provider and the reconstructed prefix will drive it. The
+  CLI and Rig still pass a label only, so nothing operator-facing reaches it.
+- **A green stub fork still proves nothing on its own.** The empty-queue
+  behaviour is unchanged and deliberate; arm 1 gets past it only through
+  `overrides`, which no operator entry point can supply. Any future fork test
+  that asserts only `status == done` is a fifteenth vacuous green.
+- **Part C is scoped to the fork command.** `terminal_error_reason/1` is
+  general and `run`/`agent start` could adopt it, but they were not changed
+  here. It returns `nil` both when no `:error` was recorded and when no event
+  source is readable — the caller's fallback is the status message either way,
+  so the two are deliberately not distinguished.
diff --git a/docs/aetheris/runbook.md b/docs/aetheris/runbook.md
index d8df6ab..33710cf 100644
--- a/docs/aetheris/runbook.md
+++ b/docs/aetheris/runbook.md
@@ -476,21 +476,21 @@ mix aetheris replay priv/runs/<run_id>/trajectory.json
 
 ## Forking a run
 
-> **Known failure — real-provider fork continuations do not currently work (BL-039).**
-> A fork that continues against Anthropic fails at its **first LLM call** with
-> `HTTP 400: Unexpected role "tool"`: `Fork.event_to_messages/1` emits a `"tool"`-role
-> message (`lib/aetheris/execution/fork.ex:104`) that the API rejects. Relabeling it
-> alone is not sufficient — a `tool_result` must pair with a preceding assistant
-> `tool_use` block, and those are never reconstructed (non-text responses are dropped
-> at `fork.ex:95-96`; contract §4's known limitation). Tracked: BL-039 in
-> `../aetheris-agents/docs/backlog-2026-06.md`.
+> **Fork reconstruction rebuilds tool-call turns (BL-039, 2026-07-26).** A fork's
+> prefix carries assistant `tool_use` blocks paired with `user` `tool_result` blocks,
+> in the same canonical form the live loop builds — so a fork continuation is accepted
+> by a validating provider. Before BL-039 it emitted a `"tool"`-role message that
+> Anthropic rejected with `HTTP 400: Unexpected role "tool"` at the **first LLM call**;
+> that failure is fixed. See contract §4 for the pairing rule, the synthesised
+> `tool_use` id, and what the reconstructed prefix does *not* preserve.
 >
-> **Stub-provider forks reach `done`, but their continuation is empty.** `encode_config`
-> strips `stub_responses` (`lib/aetheris.ex:372`), so a stub fork starts with an empty
-> queue, gets `[stub exhausted]` on its first call, and terminates at step 0. So **no
-> fork on any provider has yet had a meaningful continuation** — real ones are rejected
-> at the first call, stub ones exhaust at it. The fourteen green `fork-*` rows from
-> 2026-07-19 are green for this reason, not because forking works.
+> **A stub-provider fork still starts with an empty response queue.** `stub_responses`
+> is not part of the trajectory meta and is not set by `Fork.assemble_config/5`, so it
+> falls to its `RunConfig` default of `[]`: a stub fork gets `[stub exhausted]` on its
+> first call and terminates at step 0 unless a queue is supplied through
+> `Fork.from_step/3`'s `overrides` (test-only — neither operator entry point can pass
+> one). A green stub fork is therefore still not evidence that forking works; the
+> fourteen green `fork-*` rows from 2026-07-19 are green for this reason.
 
 ```bash
 mix aetheris fork priv/runs/<run_id>/trajectory.json --step 3
diff --git a/lib/aetheris/cli/commands/fork.ex b/lib/aetheris/cli/commands/fork.ex
index 28e91c2..68454a8 100644
--- a/lib/aetheris/cli/commands/fork.ex
+++ b/lib/aetheris/cli/commands/fork.ex
@@ -34,7 +34,7 @@ defmodule Aetheris.CLI.Commands.Fork do
              :ok <- RunHelpers.ensure_started(),
              {:ok, _config} <- RunHelpers.lookup_run(run_id),
              {:ok, new_id} <- start_fork(run_id, step, opts) do
-          RunHelpers.await_run(new_id)
+          await_fork(new_id)
         end
 
       [] ->
@@ -42,6 +42,25 @@ defmodule Aetheris.CLI.Commands.Fork do
     end
   end
 
+  # `await_run/2` reports that the fork failed, not why — the cause is in the
+  # fork's own trajectory. Without this the operator sees only
+  # "run <id> failed", and (through Rig, which surfaces stderr verbatim) that
+  # line arrives behind the worker's sandbox preamble, so the message carries
+  # no diagnosis at all. BL-039 Part C.
+  @spec await_fork(String.t()) :: {:ok, map()} | {:error, String.t()}
+  defp await_fork(new_id) do
+    case RunHelpers.await_run(new_id) do
+      {:ok, result} ->
+        {:ok, result}
+
+      {:error, message} ->
+        case RunHelpers.terminal_error_reason(new_id) do
+          nil -> {:error, message}
+          reason -> {:error, "#{message}: #{reason}"}
+        end
+    end
+  end
+
   @spec start_fork(String.t(), non_neg_integer(), keyword()) ::
           {:ok, String.t()} | {:error, String.t()}
   defp start_fork(original_run_id, step, opts) do
diff --git a/lib/aetheris/cli/commands/run_helpers.ex b/lib/aetheris/cli/commands/run_helpers.ex
index 2a6cc49..bef6161 100644
--- a/lib/aetheris/cli/commands/run_helpers.ex
+++ b/lib/aetheris/cli/commands/run_helpers.ex
@@ -199,6 +199,39 @@ defmodule Aetheris.CLI.Commands.RunHelpers do
     latest_seq(new_events, last_seq)
   end
 
+  @doc """
+  Returns the `reason` recorded by a run's last `:error` event, or `nil`.
+
+  `await_run/2`'s failure branch reports a *status* — the cause is only in the
+  trajectory. Callers that want to name the cause in an operator-facing message
+  read it back with this (BL-039 Part C). Reads the live log when the run is
+  still registered, the trajectory file otherwise — the same source
+  `stream_new_events/2` uses.
+
+  Returns `nil` when the run recorded no `:error` event and when no event
+  source is readable, so a caller cannot tell "no error recorded" from "could
+  not read"; the caller's fallback is the status message either way.
+  """
+  @spec terminal_error_reason(String.t()) :: String.t() | nil
+  def terminal_error_reason(run_id) do
+    (live_events(run_id) || file_events(run_id))
+    |> Enum.filter(fn event -> event.type == :error end)
+    |> Enum.sort_by(fn event -> event.seq end)
+    |> List.last()
+    |> error_event_reason()
+  end
+
+  @spec error_event_reason(Event.t() | nil) :: String.t() | nil
+  defp error_event_reason(nil), do: nil
+
+  defp error_event_reason(event) do
+    case Map.get(event.payload, "reason") do
+      nil -> nil
+      reason when is_binary(reason) -> reason
+      other -> inspect(other)
+    end
+  end
+
   defp live_events(run_id) do
     case Registry.lookup(Aetheris.Registry, {:log, run_id}) do
       [{pid, _}] -> TrajectoryLog.all(pid)
diff --git a/lib/aetheris/execution/canonical_message.ex b/lib/aetheris/execution/canonical_message.ex
new file mode 100644
index 0000000..0fe5015
--- /dev/null
+++ b/lib/aetheris/execution/canonical_message.ex
@@ -0,0 +1,83 @@
+defmodule Aetheris.Execution.CanonicalMessage do
+  @moduledoc """
+  Builders for the harness's canonical conversation-message shape.
+
+  The canonical shape is Anthropic-shaped: an assistant tool call is a
+  `"tool_use"` content block on an `"assistant"` turn, and its result is a
+  `"tool_result"` content block on the following `"user"` turn, the two halves
+  paired by a shared `tool_use_id`. Every provider adapter either passes this
+  shape through (Anthropic) or translates out of it (`openrouter.ex`,
+  `gemini.ex`, `ollama.ex`).
+
+  Two paths build these messages and both call this module, so there is one
+  definition rather than two that can drift:
+
+  - `Aetheris.Execution.Loop` — the live loop, after dispatching a tool call.
+  - `Aetheris.Execution.Fork` — reconstruction of a forked run's prefix from
+    recorded trajectory events (determinism contract §4, BL-039).
+
+  `assistant_tool_use_message/2` deliberately takes a **response-shaped map**
+  rather than narrowed positional arguments. It reads
+  `:thought_signature_blob`, a key the live adapter response carries and the
+  recorded `llm_responded` payload does not; on the fork path `Map.get/2`
+  returns `nil` and the block is emitted unchanged. That degradation is what
+  lets one builder serve both callers with no guard and no branch.
+  """
+
+  @doc """
+  Builds the canonical assistant turn carrying a single `tool_use` block.
+
+  `response` is a map that must carry `:tool_name` and `:tool_input` (a `nil`
+  `tool_input` is normalised to `%{}`); an optional `:thought_signature_blob`
+  is attached to the block when present.
+
+  `tool_use_id` is opaque to the harness — it is never validated, and the only
+  requirement is that the paired `tool_result` block carries the same value.
+  """
+  @spec assistant_tool_use_message(map(), String.t() | nil) :: map()
+  def assistant_tool_use_message(response, tool_use_id) do
+    tool_use_block =
+      %{
+        "type" => "tool_use",
+        "id" => tool_use_id,
+        "name" => response.tool_name,
+        "input" => response.tool_input || %{}
+      }
+      |> maybe_put_thought_signature(Map.get(response, :thought_signature_blob))
+
+    %{"role" => "assistant", "content" => [tool_use_block]}
+  end
+
+  @doc """
+  Builds the canonical user turn carrying the `tool_result` block that pairs
+  with `tool_use_id`.
+
+  `is_error` adds the API's `"is_error"` marker; it is omitted when false so
+  the block is byte-identical to the pre-extraction success shape.
+  """
+  @spec tool_result_message(String.t() | nil, String.t(), boolean()) :: map()
+  def tool_result_message(tool_use_id, output, is_error \\ false) do
+    content_block = %{
+      "type" => "tool_result",
+      "tool_use_id" => tool_use_id,
+      "content" => output
+    }
+
+    content_block_with_error =
+      if is_error do
+        Map.put(content_block, "is_error", true)
+      else
+        content_block
+      end
+
+    %{
+      "role" => "user",
+      "content" => [
+        content_block_with_error
+      ]
+    }
+  end
+
+  defp maybe_put_thought_signature(block, nil), do: block
+  defp maybe_put_thought_signature(block, sig), do: Map.put(block, "thought_signature", sig)
+end
diff --git a/lib/aetheris/execution/fork.ex b/lib/aetheris/execution/fork.ex
index c8faa4f..8f731e8 100644
--- a/lib/aetheris/execution/fork.ex
+++ b/lib/aetheris/execution/fork.ex
@@ -5,8 +5,17 @@ defmodule Aetheris.Execution.Fork do
   The forked run starts with the conversation context replayed up to the
   fork point, then continues from there — no steps before the fork point
   are re-executed.
+
+  The replayed context is rebuilt in the harness's canonical message shape via
+  `Aetheris.Execution.CanonicalMessage`, the same builders the live execution
+  loop uses: an assistant tool-call turn becomes a `tool_use` content block and
+  its result a paired `tool_result` block on the following `user` turn. The
+  determinism contract §4 states what that prefix does and does not preserve —
+  notably that the provider's `tool_use` id is not recorded and is synthesised
+  here, and that pairing a result with the call at the same step is positional.
   """
 
+  alias Aetheris.Execution.CanonicalMessage
   alias Aetheris.{RunConfig, Trajectory.File}
 
   @doc """
@@ -66,10 +75,15 @@ defmodule Aetheris.Execution.Fork do
     Enum.find(events, fn e -> e.type == :step_complete and e.step == step end)
   end
 
-  # Builds a chronological list of conversation messages up to `step`.
-  # The initial user prompt (from meta) is prepended when present.
-  # Then, for each event at step <= fork_step, assistant text responses and
-  # tool results are appended in seq order.
+  # Builds a chronological list of conversation messages up to `step`, in the
+  # harness's canonical message shape — the same shape the live loop builds, so
+  # every provider adapter consumes it (contract §4).
+  #
+  # The initial user prompt (from meta) is prepended when present. Then, for
+  # each event at step <= fork_step in seq order: assistant text responses, and
+  # assistant tool-call turns each followed by their paired tool result. Events
+  # are already in seq order, so the `llm_responded` at step N precedes the
+  # `tool_result` at step N and the pair lands adjacent, as the API requires.
   defp extract_context(events, step, meta) do
     user_message =
       case Map.get(meta, "user_prompt", "") do
@@ -85,7 +99,7 @@ defmodule Aetheris.Execution.Fork do
     user_message ++ response_messages
   end
 
-  defp event_to_messages(%{type: :llm_responded, payload: payload}) do
+  defp event_to_messages(%{type: :llm_responded, payload: payload, step: step}) do
     case Map.get(payload, "response_type") do
       "text" ->
         case Map.get(payload, "raw_response") do
@@ -94,22 +108,52 @@ defmodule Aetheris.Execution.Fork do
         end
 
       _ ->
-        []
+        tool_call_messages(payload, step)
     end
   end
 
-  defp event_to_messages(%{type: :tool_result, payload: payload}) do
-    tool_name = Map.get(payload, "tool_name", "")
+  defp event_to_messages(%{type: :tool_result, payload: payload, step: step}) do
     # Worker/MCP dispatch writes the payload under "output" (loop.ex:537, :553,
     # :570); the in-process family and the tool-error path write "result"
     # (loop.ex:354 and :424-508). Read "output" first — it stays authoritative
     # when present, so a genuinely empty worker result is not overridden.
     output = normalize_content(Map.get(payload, "output") || Map.get(payload, "result"))
-    [%{"role" => "tool", "tool_name" => tool_name, "content" => output}]
+    is_error = Map.get(payload, "is_error") == true
+
+    [CanonicalMessage.tool_result_message(synthetic_tool_use_id(step), output, is_error)]
   end
 
   defp event_to_messages(_event), do: []
 
+  # An assistant tool-call turn is rebuilt as the canonical `tool_use` block
+  # (contract §4). The recorded payload carries `tool_name` and `tool_input`;
+  # it does not carry the provider's `tool_use` id, and the record path is not
+  # changed to add one — so the id is synthesised. A response type that is
+  # neither "text" nor a tool call has no `tool_name` and contributes nothing,
+  # as before.
+  defp tool_call_messages(payload, step) do
+    case Map.get(payload, "tool_name") do
+      nil ->
+        []
+
+      tool_name ->
+        response = %{tool_name: tool_name, tool_input: Map.get(payload, "tool_input")}
+        [CanonicalMessage.assistant_tool_use_message(response, synthetic_tool_use_id(step))]
+    end
+  end
+
+  # The id is opaque to the harness — the only requirement is that the two
+  # halves of a pair agree (contract §4). Deriving it from the step gives that
+  # by construction, with no state threaded between the two clauses, and keeps
+  # a reconstructed prefix deterministic across repeated forks of the same run.
+  #
+  # Pairing is positional: the `:tool_result` at step N pairs with the tool call
+  # recorded at step N. That is sound while a step carries at most one tool call
+  # — true today because the Anthropic adapter keeps the first `tool_use` block
+  # of a response and discards the rest (BL-059). §4 records the dependency;
+  # if BL-059 lands disposition (a), this pairing moves to N-to-N.
+  defp synthetic_tool_use_id(step), do: "fork-toolu-#{step}"
+
   # Transcript messages carry string content (contract §2). Absent-or-nil
   # normalizes to the empty default; a non-string result is JSON-encoded rather
   # than leaked into the transcript as a raw term — spawn_agent and
diff --git a/lib/aetheris/execution/loop.ex b/lib/aetheris/execution/loop.ex
index 037d188..a212887 100644
--- a/lib/aetheris/execution/loop.ex
+++ b/lib/aetheris/execution/loop.ex
@@ -26,6 +26,7 @@ defmodule Aetheris.Execution.Loop do
   alias Aetheris.AgentTree.Store, as: AgentTreeStore
 
   alias Aetheris.Execution.{
+    CanonicalMessage,
     ContextManager,
     LLMAdapter,
     LoopDetector,
@@ -1113,43 +1114,14 @@ defmodule Aetheris.Execution.Loop do
     Log.append(log_pid, event)
   end
 
-  defp assistant_tool_use_message(response, tool_use_id) do
-    tool_use_block =
-      %{
-        "type" => "tool_use",
-        "id" => tool_use_id,
-        "name" => response.tool_name,
-        "input" => response.tool_input || %{}
-      }
-      |> maybe_put_thought_signature(Map.get(response, :thought_signature_blob))
-
-    %{"role" => "assistant", "content" => [tool_use_block]}
-  end
-
-  defp maybe_put_thought_signature(block, nil), do: block
-  defp maybe_put_thought_signature(block, sig), do: Map.put(block, "thought_signature", sig)
-
-  defp tool_result_message(tool_use_id, output, is_error \\ false) do
-    content_block = %{
-      "type" => "tool_result",
-      "tool_use_id" => tool_use_id,
-      "content" => output
-    }
+  # The canonical (tool_use / tool_result) message pair is built in one place —
+  # `Aetheris.Execution.CanonicalMessage` — because `Execution.Fork` rebuilds the
+  # same shape from recorded events and the two must not drift (contract §4).
+  defp assistant_tool_use_message(response, tool_use_id),
+    do: CanonicalMessage.assistant_tool_use_message(response, tool_use_id)
 
-    content_block_with_error =
-      if is_error do
-        Map.put(content_block, "is_error", true)
-      else
-        content_block
-      end
-
-    %{
-      "role" => "user",
-      "content" => [
-        content_block_with_error
-      ]
-    }
-  end
+  defp tool_result_message(tool_use_id, output, is_error \\ false),
+    do: CanonicalMessage.tool_result_message(tool_use_id, output, is_error)
 
   defp hash_content(data),
     do: "sha256:" <> Base.encode16(:crypto.hash(:sha256, data), case: :lower)
diff --git a/test/aetheris/cli/commands/fork_test.exs b/test/aetheris/cli/commands/fork_test.exs
index 1665ecc..0c512bf 100644
--- a/test/aetheris/cli/commands/fork_test.exs
+++ b/test/aetheris/cli/commands/fork_test.exs
@@ -5,6 +5,7 @@ defmodule Aetheris.CLI.Commands.ForkTest do
 
   alias Aetheris.CLI.Commands.Fork
   alias Aetheris.RunConfig
+  alias Aetheris.Trajectory.File, as: TrajectoryFile
 
   setup do
     {:ok, _apps} = Application.ensure_all_started(:aetheris)
@@ -43,6 +44,24 @@ defmodule Aetheris.CLI.Commands.ForkTest do
     assert {:error, "fork requires --step N"} = Fork.run([path], [])
   end
 
+  # BL-039 Part C. Before this, a failed fork reported "run <id> failed" and
+  # nothing else — the cause lived only in the fork's trajectory, and through
+  # Rig (which surfaces stderr verbatim) that line arrived behind the worker's
+  # sandbox preamble, so the operator's message named no cause at all. The
+  # source's recorded provider is rewritten to one with no adapter, which fails
+  # the fork deterministically at its first call with a reason on the record.
+  test "a failed fork's error message carries the run's terminal reason",
+       %{run_id: source_run_id, trajectory_path: path} do
+    {:ok, trajectory} = TrajectoryFile.read(source_run_id)
+    meta = Map.put(trajectory.meta, "provider", "no-such-provider")
+    {:ok, _path} = TrajectoryFile.write(source_run_id, trajectory.events, meta)
+
+    assert {:error, message} = Fork.run([path, "--step", "0"], [])
+
+    assert message =~ "failed"
+    assert message =~ "unknown provider: no-such-provider"
+  end
+
   # Step 0 is a tool call (worker-free local echo dispatch) so it records a
   # :step_complete event — a real fork point (a terminal text step emits only
   # run_complete). Step 1 is the finishing text response.
diff --git a/test/aetheris/cli/commands/run_helpers_test.exs b/test/aetheris/cli/commands/run_helpers_test.exs
index a94307d..48a176b 100644
--- a/test/aetheris/cli/commands/run_helpers_test.exs
+++ b/test/aetheris/cli/commands/run_helpers_test.exs
@@ -6,6 +6,8 @@ defmodule Aetheris.CLI.Commands.RunHelpersTest do
   alias Aetheris.CLI.Commands.RunHelpers
   alias Aetheris.RunConfig
   alias Aetheris.Store
+  alias Aetheris.Trajectory.Event
+  alias Aetheris.Trajectory.File, as: TrajectoryFile
 
   setup do
     {:ok, _apps} = Application.ensure_all_started(:aetheris)
@@ -39,6 +41,36 @@ defmodule Aetheris.CLI.Commands.RunHelpersTest do
     assert output =~ "Run cancelled."
   end
 
+  # BL-039 Part C. `await_run/2` reports a status; the cause is only in the
+  # trajectory. The run is not registered here, so this exercises the
+  # trajectory-file source rather than the live log.
+  test "terminal_error_reason returns the last recorded :error reason" do
+    run_id = "run-helpers-error-#{System.unique_integer([:positive])}"
+
+    events = [
+      Event.new(run_id, 0, :llm_called, %{"model" => "stub-v1"}, 0),
+      Event.new(run_id, 0, :error, %{"reason" => "first failure"}, 1),
+      Event.new(run_id, 1, :error, %{"reason" => "unknown provider: nope"}, 2)
+    ]
+
+    {:ok, _path} = TrajectoryFile.write(run_id, events, %{"provider" => "nope"})
+
+    assert RunHelpers.terminal_error_reason(run_id) == "unknown provider: nope"
+  end
+
+  test "terminal_error_reason returns nil for a run with no error event" do
+    run_id = "run-helpers-noerror-#{System.unique_integer([:positive])}"
+    events = [Event.new(run_id, 0, :run_complete, %{"reason" => "agent_finished"}, 0)]
+    {:ok, _path} = TrajectoryFile.write(run_id, events, %{"provider" => "stub"})
+
+    assert RunHelpers.terminal_error_reason(run_id) == nil
+  end
+
+  test "terminal_error_reason returns nil when no event source is readable" do
+    assert RunHelpers.terminal_error_reason("run-helpers-missing-#{System.unique_integer()}") ==
+             nil
+  end
+
   defp build_config_json(run_id) do
     %RunConfig{
       run_id: run_id,
diff --git a/test/aetheris/execution/canonical_message_test.exs b/test/aetheris/execution/canonical_message_test.exs
new file mode 100644
index 0000000..87264e3
--- /dev/null
+++ b/test/aetheris/execution/canonical_message_test.exs
@@ -0,0 +1,76 @@
+defmodule Aetheris.Execution.CanonicalMessageTest do
+  use ExUnit.Case, async: true
+
+  alias Aetheris.Execution.CanonicalMessage
+
+  test "assistant_tool_use_message/2 builds a single tool_use block on an assistant turn" do
+    response = %{tool_name: "run_command", tool_input: %{"command" => "echo"}}
+
+    assert %{"role" => "assistant", "content" => [block]} =
+             CanonicalMessage.assistant_tool_use_message(response, "toolu_1")
+
+    assert block == %{
+             "type" => "tool_use",
+             "id" => "toolu_1",
+             "name" => "run_command",
+             "input" => %{"command" => "echo"}
+           }
+  end
+
+  test "assistant_tool_use_message/2 normalizes a nil tool_input to an empty object" do
+    response = %{tool_name: "run_command", tool_input: nil}
+
+    assert %{"content" => [block]} =
+             CanonicalMessage.assistant_tool_use_message(response, "toolu_1")
+
+    assert Map.fetch!(block, "input") == %{}
+  end
+
+  # The key is on the live adapter response and absent from the recorded
+  # `llm_responded` payload. That asymmetry is what lets one builder serve both
+  # the live loop and fork reconstruction with no guard: `Map.get/2` returns nil
+  # on the fork path and the block is emitted unchanged.
+  test "assistant_tool_use_message/2 attaches a thought signature only when present" do
+    with_sig = %{
+      tool_name: "run_command",
+      tool_input: %{},
+      thought_signature_blob: "sig-abc"
+    }
+
+    assert %{"content" => [block]} =
+             CanonicalMessage.assistant_tool_use_message(with_sig, "toolu_1")
+
+    assert Map.fetch!(block, "thought_signature") == "sig-abc"
+
+    assert %{"content" => [plain]} =
+             CanonicalMessage.assistant_tool_use_message(
+               %{tool_name: "run_command", tool_input: %{}},
+               "toolu_1"
+             )
+
+    refute Map.has_key?(plain, "thought_signature")
+  end
+
+  test "tool_result_message/3 pairs a user turn to the tool_use id" do
+    assert CanonicalMessage.tool_result_message("toolu_1", "output text") == %{
+             "role" => "user",
+             "content" => [
+               %{
+                 "type" => "tool_result",
+                 "tool_use_id" => "toolu_1",
+                 "content" => "output text"
+               }
+             ]
+           }
+  end
+
+  test "tool_result_message/3 marks is_error only when true" do
+    assert %{"content" => [errored]} =
+             CanonicalMessage.tool_result_message("toolu_1", "Error: :timeout", true)
+
+    assert Map.fetch!(errored, "is_error") == true
+
+    assert %{"content" => [ok]} = CanonicalMessage.tool_result_message("toolu_1", "fine", false)
+    refute Map.has_key?(ok, "is_error")
+  end
+end
diff --git a/test/aetheris/execution/fork_test.exs b/test/aetheris/execution/fork_test.exs
index 21b0536..b71c865 100644
--- a/test/aetheris/execution/fork_test.exs
+++ b/test/aetheris/execution/fork_test.exs
@@ -4,10 +4,30 @@ defmodule Aetheris.Execution.ForkTest do
   import Aetheris.Test.RunHelpers
 
   alias Aetheris.Execution.Fork
+  alias Aetheris.Execution.LLMAdapter.Anthropic
   alias Aetheris.Trajectory.{Event, File}
 
+  @anthropic_key_skip_reason if is_nil(System.get_env("ANTHROPIC_API_KEY")),
+                               do: "ANTHROPIC_API_KEY is required",
+                               else: nil
+
   defp unique_run_id, do: "test-fork-#{System.unique_integer([:positive])}"
 
+  # Reconstruction puts everything inside `content` (contract §4) — a list of
+  # blocks, which is what survives `Agent.Server.normalize_context_entry/1`.
+  defp content_blocks(message) do
+    case Map.get(message, "content") do
+      blocks when is_list(blocks) -> blocks
+      _other -> []
+    end
+  end
+
+  defp blocks_of_type(messages, type) do
+    messages
+    |> Enum.flat_map(&content_blocks/1)
+    |> Enum.filter(fn block -> Map.get(block, "type") == type end)
+  end
+
   # Writes a stub trajectory directly to disk with `steps` text steps.
   # Each step gets: prompt_built, llm_called, llm_responded (with raw_response),
   # optionally a tool_result (when `step == tool_result_step`), then
@@ -21,6 +41,37 @@ defmodule Aetheris.Execution.ForkTest do
   defp tool_result_value(:default, step), do: "tool output for step #{step}"
   defp tool_result_value(value, _step), do: value
 
+  # A tool step's recorded `llm_responded` is a `tool_call` carrying `tool_name`
+  # and `tool_input` with a **nil** `raw_response` — the shape `loop.ex` writes,
+  # verified verbatim against `priv/runs/payslip-orch-a7Vi3A/trajectory.json`
+  # step 0 (BL-039 scout §2). Before BL-039 this fixture wrote a `text` response
+  # on tool steps, which no real run produces.
+  defp llm_responded_payload(step, false = _tool_step?) do
+    %{
+      "response_type" => "text",
+      "raw_response" => "response for step #{step}",
+      "tool_name" => nil,
+      "tool_input" => nil,
+      "latency_ms" => 0
+    }
+  end
+
+  defp llm_responded_payload(step, true = _tool_step?) do
+    %{
+      "response_type" => "tool_call",
+      "raw_response" => nil,
+      "tool_name" => "run_command",
+      "tool_input" => %{"command" => "echo", "args" => ["step #{step}"]},
+      "latency_ms" => 0
+    }
+  end
+
+  defp tool_result_payload(key, value, false = _is_error?),
+    do: %{"tool_name" => "run_command", key => value}
+
+  defp tool_result_payload(key, value, true = _is_error?),
+    do: %{"tool_name" => "run_command", key => value, "is_error" => true}
+
   defp write_stub_trajectory(run_id, opts) do
     steps = Keyword.get(opts, :steps, 2)
     user_prompt = Keyword.get(opts, :user_prompt, "What is the answer?")
@@ -34,20 +85,18 @@ defmodule Aetheris.Execution.ForkTest do
     # The value under that key. In-process results are not always strings:
     # spawn_agent and wait_for_all record maps (loop.ex:435,450).
     tool_payload_value = Keyword.get(opts, :tool_payload_value, :default)
+    # Recorded by the tool-error path only (loop.ex record_tool_error/6).
+    tool_result_is_error = Keyword.get(opts, :tool_result_is_error, false)
+    tools = Keyword.get(opts, :tools, [])
+    provider = Keyword.get(opts, :provider, "stub")
+    model = Keyword.get(opts, :model, "stub-v1")
 
     step_specs =
       Enum.flat_map(0..(steps - 1), fn step ->
         head = [
           {step, :prompt_built, %{"context_hash" => "h#{step}", "message_count" => 1}},
           {step, :llm_called, %{"model" => "stub-v1"}},
-          {step, :llm_responded,
-           %{
-             "response_type" => "text",
-             "raw_response" => "response for step #{step}",
-             "tool_name" => nil,
-             "tool_input" => nil,
-             "latency_ms" => 0
-           }}
+          {step, :llm_responded, llm_responded_payload(step, step == tool_result_step)}
         ]
 
         maybe_tool =
@@ -55,7 +104,8 @@ defmodule Aetheris.Execution.ForkTest do
             value = tool_result_value(tool_payload_value, step)
 
             [
-              {step, :tool_result, %{"tool_name" => "run_command", tool_payload_key => value}}
+              {step, :tool_result,
+               tool_result_payload(tool_payload_key, value, tool_result_is_error)}
             ]
           else
             []
@@ -78,12 +128,12 @@ defmodule Aetheris.Execution.ForkTest do
     meta =
       %{
         "mode" => "record",
-        "provider" => "stub",
-        "model" => "stub-v1",
+        "provider" => provider,
+        "model" => model,
         "max_steps" => steps,
         "system_prompt" => system_prompt,
         "user_prompt" => user_prompt,
-        "tools" => []
+        "tools" => tools
       }
       |> then(fn m -> if seed, do: Map.put(m, "seed", seed), else: m end)
 
@@ -131,24 +181,76 @@ defmodule Aetheris.Execution.ForkTest do
     assert config.seed == nil
   end
 
-  test "from_step/3 rebuilds tool_result events into tool messages" do
+  # BL-039: a tool step rebuilds as the canonical pair — an assistant turn
+  # carrying a `tool_use` block, then a user turn carrying the matching
+  # `tool_result` block. Asserted whole, not by probe, because the two things
+  # that broke in the field are both structural: the `"tool"` role, and the
+  # top-level `tool_name` sibling that never reached the wire.
+  test "from_step/3 rebuilds a tool step into a paired tool_use / tool_result turn" do
     run_id = unique_run_id()
     :ok = write_stub_trajectory(run_id, steps: 1, user_prompt: "Hello", tool_result_step: 0)
 
     {:ok, config} = Fork.from_step(run_id, 0, %{})
 
-    # user + assistant(text) + tool, in seq order
     assert config.fork_context == [
              %{"role" => "user", "content" => "Hello"},
-             %{"role" => "assistant", "content" => "response for step 0"},
              %{
-               "role" => "tool",
-               "tool_name" => "run_command",
-               "content" => "tool output for step 0"
+               "role" => "assistant",
+               "content" => [
+                 %{
+                   "type" => "tool_use",
+                   "id" => "fork-toolu-0",
+                   "name" => "run_command",
+                   "input" => %{"command" => "echo", "args" => ["step 0"]}
+                 }
+               ]
+             },
+             %{
+               "role" => "user",
+               "content" => [
+                 %{
+                   "type" => "tool_result",
+                   "tool_use_id" => "fork-toolu-0",
+                   "content" => "tool output for step 0"
+                 }
+               ]
              }
            ]
   end
 
+  # The `is_error` marker is recorded only by the tool-error path
+  # (`record_tool_error/6`), so it is carried when present and omitted
+  # otherwise — an unconditional `"is_error" => false` would change every
+  # success block's bytes.
+  test "from_step/3 carries is_error onto the tool_result block when recorded" do
+    run_id = unique_run_id()
+
+    :ok =
+      write_stub_trajectory(run_id,
+        steps: 1,
+        tool_result_step: 0,
+        tool_payload_key: "result",
+        tool_payload_value: "Error: :timeout",
+        tool_result_is_error: true
+      )
+
+    {:ok, config} = Fork.from_step(run_id, 0, %{})
+    [block] = blocks_of_type(config.fork_context, "tool_result")
+
+    assert Map.fetch!(block, "is_error") == true
+    assert Map.fetch!(block, "content") == "Error: :timeout"
+  end
+
+  test "from_step/3 omits is_error on a successful tool_result block" do
+    run_id = unique_run_id()
+    :ok = write_stub_trajectory(run_id, steps: 1, tool_result_step: 0)
+
+    {:ok, config} = Fork.from_step(run_id, 0, %{})
+    [block] = blocks_of_type(config.fork_context, "tool_result")
+
+    refute Map.has_key?(block, "is_error")
+  end
+
   # BL-028: in-process tool writers emit the payload under "result", not
   # "output" (loop.ex:354,424-508). Reconstruction must carry that content
   # rather than silently defaulting to an empty string.
@@ -165,10 +267,10 @@ defmodule Aetheris.Execution.ForkTest do
 
     {:ok, config} = Fork.from_step(run_id, 0, %{})
 
-    tool_message = Enum.find(config.fork_context, &(&1["role"] == "tool"))
+    [block] = blocks_of_type(config.fork_context, "tool_result")
 
-    assert tool_message["content"] != ""
-    assert tool_message["content"] == "tool output for step 0"
+    assert Map.fetch!(block, "content") != ""
+    assert Map.fetch!(block, "content") == "tool output for step 0"
   end
 
   # BL-028 r2 F1: a present-but-nil "result" must normalize to the string
@@ -187,9 +289,9 @@ defmodule Aetheris.Execution.ForkTest do
 
     {:ok, config} = Fork.from_step(run_id, 0, %{})
 
-    tool_message = Enum.find(config.fork_context, &(&1["role"] == "tool"))
+    [block] = blocks_of_type(config.fork_context, "tool_result")
 
-    assert tool_message["content"] == ""
+    assert Map.fetch!(block, "content") == ""
   end
 
   # BL-028 r2 F1 (widened): spawn_agent and wait_for_all record maps under
@@ -209,12 +311,12 @@ defmodule Aetheris.Execution.ForkTest do
 
     {:ok, config} = Fork.from_step(run_id, 0, %{})
 
-    tool_message = Enum.find(config.fork_context, &(&1["role"] == "tool"))
+    [block] = blocks_of_type(config.fork_context, "tool_result")
 
-    assert is_binary(tool_message["content"])
+    assert is_binary(Map.fetch!(block, "content"))
 
     assert {:ok, %{"run_id" => "child-1", "status" => "started"}} =
-             Jason.decode(tool_message["content"])
+             Jason.decode(Map.fetch!(block, "content"))
   end
 
   test "from_step/3 with step beyond available step_complete returns :step_not_found" do
@@ -253,4 +355,216 @@ defmodule Aetheris.Execution.ForkTest do
     assert Map.get(trajectory.meta, "fork_from") == source_id
     assert Map.get(trajectory.meta, "fork_step") == 0
   end
+
+  # ---------------------------------------------------------------------------
+  # BL-039 done-check
+  # ---------------------------------------------------------------------------
+
+  # Arm 1 — a fork that actually continues. The fourteen green `fork-*` rows
+  # BL-039 documents were green because a stub fork starts with an empty queue
+  # (`stub_responses` is not in the trajectory meta and `assemble_config/5`
+  # never sets it), takes `[stub exhausted]` at step 0 and stops. Seeding the
+  # queue through `overrides` is the only way to get past that, and it is
+  # test-only by construction — the CLI's `fork_overrides/1` builds `%{label:}`
+  # and Rig invokes the CLI.
+  #
+  # **What makes this non-vacuous.** Continuation alone would be a fifteenth
+  # vacuous green: the stub adapter validates nothing, so a fork starting from
+  # the old `role: "tool"` transcript reaches step 1 just as happily. The
+  # `fork_context` assertion is what binds the test to the reconstruction —
+  # revert `tool_call_messages/2` and this test goes red on that assertion
+  # while the continuation assertions still pass.
+  test "a fork of a tool-call step continues past step 0 from a reconstructed context" do
+    source_id = unique_run_id()
+
+    :ok =
+      write_stub_trajectory(source_id,
+        steps: 1,
+        user_prompt: "Hello",
+        tool_result_step: 0,
+        tools: ["echo"]
+      )
+
+    {:ok, config} =
+      Fork.from_step(source_id, 0, %{
+        max_steps: 3,
+        stub_responses: [
+          %{
+            type: :tool_call,
+            content: nil,
+            tool_name: "echo",
+            tool_use_id: "toolu_fork_continuation_01",
+            tool_input: %{"payload" => %{"from" => "fork"}},
+            latency_ms: 0,
+            resolved_model: nil,
+            system_fingerprint: nil
+          },
+          %{
+            type: :text,
+            content: "fork finished",
+            tool_name: nil,
+            tool_input: nil,
+            latency_ms: 0,
+            resolved_model: nil,
+            system_fingerprint: nil
+          }
+        ]
+      })
+
+    # The reconstruction the fork starts from — the mutation-sensitive half.
+    assert [
+             %{"role" => "user", "content" => "Hello"},
+             %{"role" => "assistant", "content" => [tool_use_block]},
+             %{"role" => "user", "content" => [tool_result_block]}
+           ] = config.fork_context
+
+    assert Map.fetch!(tool_use_block, "type") == "tool_use"
+    assert Map.fetch!(tool_result_block, "type") == "tool_result"
+
+    assert Map.fetch!(tool_result_block, "tool_use_id") == Map.fetch!(tool_use_block, "id")
+
+    fork_id = config.run_id
+    {:ok, ^fork_id} = Aetheris.start_run(config)
+    assert_run_done(fork_id, timeout: 10_000, poll_interval: 50)
+
+    {:ok, trajectory} = File.read(fork_id)
+    events = trajectory.events
+
+    # Continued: step 0 completed and step 1 called the model again. Both are
+    # false for every fork recorded before this ticket.
+    assert Enum.any?(events, fn e -> e.type == :step_complete and e.step == 0 end)
+    assert Enum.any?(events, fn e -> e.type == :tool_result and e.step == 0 end)
+    assert Enum.any?(events, fn e -> e.type == :llm_responded and e.step == 1 end)
+
+    # ...and did not merely exhaust the queue at step 0.
+    refute Enum.any?(events, fn e ->
+             e.type == :llm_responded and
+               Map.get(e.payload, "raw_response") == "[stub exhausted]"
+           end)
+  end
+
+  # Arm 2 — the seam that failed in the field, with no network call.
+  # `build_request_body/2` passes `messages` through untouched, so this is the
+  # exact JSON a real-provider fork puts on the wire. There was no test
+  # anywhere driving a reconstructed transcript into an adapter's request
+  # builder; that gap is why a 100%-reproducible failure reached an operator.
+  test "a reconstructed fork context builds a wire-valid Anthropic request body" do
+    source_id = unique_run_id()
+
+    :ok =
+      write_stub_trajectory(source_id, steps: 2, user_prompt: "Hello", tool_result_step: 0)
+
+    {:ok, config} = Fork.from_step(source_id, 1, %{})
+
+    body =
+      Anthropic.build_request_body(
+        %{
+          model: config.model,
+          system_prompt: config.system_prompt,
+          messages: config.fork_context,
+          tool_schema: []
+        },
+        %{}
+      )
+
+    messages = Map.fetch!(body, "messages")
+
+    # The field rejection, expressed locally: `HTTP 400: Unexpected role "tool".
+    # Allowed roles are "user" or "assistant"`.
+    roles = Enum.map(messages, &Map.fetch!(&1, "role"))
+    assert Enum.all?(roles, fn role -> role in ["user", "assistant"] end)
+    refute "tool" in roles
+
+    # Not vacuous: there is a pair here to check.
+    assert length(blocks_of_type(messages, "tool_use")) == 1
+    assert length(blocks_of_type(messages, "tool_result")) == 1
+
+    assert_tool_results_paired(messages)
+
+    assert {:ok, _json} = Jason.encode(body)
+  end
+
+  # Arm 3 — the arm that retires §4's provider hedge. §4 scopes the
+  # synthesised-id claim to the harness and says explicitly that whether a given
+  # provider accepts a synthesised id in a *replayed* assistant turn is settled
+  # here, not by the clause. Excluded by default (network, API key, cost); run
+  # with `mix test --include requires_real_provider`.
+  #
+  # This calls the adapter directly rather than starting a fork run: the claim
+  # under test is the provider's acceptance of the reconstructed prefix, and the
+  # first LLM call is where every recorded real-provider fork died. No worker,
+  # no tool execution, one request.
+  @tag :requires_real_provider
+  @tag skip: @anthropic_key_skip_reason
+  @tag timeout: 120_000
+  test "Anthropic accepts a reconstructed fork prefix with a synthesised tool_use id" do
+    # `config/test.exs` points `:req_options` at a `Req.Test` stub plug; this arm
+    # is the one place that must reach the real endpoint.
+    original = Application.get_env(:aetheris, :req_options, [])
+    Application.put_env(:aetheris, :req_options, receive_timeout: 60_000)
+    on_exit(fn -> Application.put_env(:aetheris, :req_options, original) end)
+
+    source_id = unique_run_id()
+
+    :ok =
+      write_stub_trajectory(source_id,
+        steps: 1,
+        user_prompt: "Run the payslip script and tell me how many were generated.",
+        tool_result_step: 0,
+        provider: "anthropic",
+        model: "claude-haiku-4-5-20251001",
+        tools: ["run_command"]
+      )
+
+    {:ok, config} = Fork.from_step(source_id, 0, %{})
+
+    request = %{
+      model: config.model,
+      system_prompt: config.system_prompt,
+      messages: config.fork_context,
+      tool_schema: [
+        %{
+          "name" => "run_command",
+          "description" => "Run a shell command.",
+          "input_schema" => %{
+            "type" => "object",
+            "properties" => %{
+              "command" => %{"type" => "string"},
+              "args" => %{"type" => "array", "items" => %{"type" => "string"}}
+            },
+            "required" => ["command"]
+          }
+        }
+      ],
+      max_tokens: 64
+    }
+
+    assert {:ok, response} = Anthropic.call(nil, request)
+    assert Map.fetch!(response, :type) in [:text, :tool_call]
+    assert Map.fetch!(response, :resolved_model) =~ "claude"
+  end
+
+  # Contract §4's pairing invariant: a `tool_result` block sits on a `user` turn
+  # whose immediately preceding turn is an assistant turn carrying a `tool_use`
+  # block with the same id.
+  defp assert_tool_results_paired(messages) do
+    messages
+    |> Enum.with_index()
+    |> Enum.each(fn {message, index} ->
+      Enum.each(blocks_of_type([message], "tool_result"), fn block ->
+        assert Map.fetch!(message, "role") == "user"
+        assert index > 0
+
+        previous = Enum.at(messages, index - 1)
+        assert Map.fetch!(previous, "role") == "assistant"
+
+        ids =
+          [previous]
+          |> blocks_of_type("tool_use")
+          |> Enum.map(&Map.fetch!(&1, "id"))
+
+        assert Map.fetch!(block, "tool_use_id") in ids
+      end)
+    end)
+  end
 end
```

### 2b. Agents — `7d6013a~1..HEAD`

```
 agents/fixture_unlabelled_fork.exs | 13 +++---
 docs/backlog-2026-06.md            | 82 ++++++++++++++++++++++++++++++++++++++
 docs/rig/runbook.md                | 26 ++++++------
 3 files changed, 103 insertions(+), 18 deletions(-)
```

```diff
diff --git a/agents/fixture_unlabelled_fork.exs b/agents/fixture_unlabelled_fork.exs
index 4c5dc5b..0a609b7 100644
--- a/agents/fixture_unlabelled_fork.exs
+++ b/agents/fixture_unlabelled_fork.exs
@@ -11,11 +11,14 @@
 #     (`run.label === run.run_id` -> parentLabel undefined -> unlabelled child).
 #     Adding a label here would silently defeat the only check this file exists
 #     for.
-#   - STUB PROVIDER. Real-provider fork continuations currently fail at the
-#     first LLM call (BL-039: fork.ex:104 emits a "tool" role Anthropic
-#     rejects, and the paired assistant tool_use turns are never reconstructed
-#     — fork.ex:95-96 drops non-text responses). Stub forks are the only forks
-#     that presently complete, so the gate check must run on one.
+#   - STUB PROVIDER. The gate check is about labels, not about continuation, so
+#     it must not depend on a live provider or an API key. (Historically this
+#     line also said stub was the *only* provider whose forks complete —
+#     real-provider fork continuations failed at the first LLM call until
+#     BL-039 reconstructed the assistant tool_use turns. That is fixed; the
+#     stub choice here is now about hermeticity alone.) Note a stub fork's
+#     response queue is empty unless overrides supply one, so this fixture's
+#     fork terminates at step 0 — which is all check 3 needs.
 #   - ONE TOOL CALL. A fork needs a forkable step. The step must be a *tool*
 #     step: a stub response of `type: :text` terminates the run immediately
 #     (harness CLAUDE.md, "Use `type: :tool_call` for intermediate stub
diff --git a/docs/backlog-2026-06.md b/docs/backlog-2026-06.md
index 8402811..6a101c9 100644
--- a/docs/backlog-2026-06.md
+++ b/docs/backlog-2026-06.md
@@ -1806,6 +1806,80 @@ function is the scheduled-run template encoder). Conclusions unaffected.
 provider, or the contract states plainly that fork continuation is stub-only and the
 UI refuses real-provider forks rather than failing at the first call.
 
+**Status:** Done 2026-07-26 — harness `ebc3878` (docs-first §4 + §2 and runbook echo
+sweep), `e44d35c` (implementation), `3f561d9` (notes); agents `7d6013a` (rig runbook +
+fork fixture mirrors). Design A as ratified. A recorded tool step rebuilds as the
+canonical pair — an assistant `tool_use` block and a `user` `tool_result` block sharing
+a step-derived synthetic id — built through
+`Aetheris.Execution.CanonicalMessage`, extracted from `loop.ex` so the live loop and
+fork reconstruction have one definition. The record path is untouched: no `tool_use_id`
+is added to any event. Part C ships in the same change —
+`RunHelpers.terminal_error_reason/1` puts the fork's terminal `error` reason into the
+CLI message, which previously read only "run \<id\> failed". No provider/model fork
+overrides were built (BL-030).
+
+**Done-when is met, demonstrated not asserted.** The `:requires_real_provider` arm was
+run manually against Anthropic: **PASS**, and mutated back to the pre-fix shape the same
+arm returns `HTTP 400: messages: Unexpected role "tool"…` — byte-identical to the reason
+recorded in `fork-aa6a6a65804f6645`. That retires the hedge the §4 wording deliberately
+carried (`bl-039-contract-draft.md` obligation 2). All three done-check arms are
+mutation-checked; the stub-continuation arm asserts the reconstructed context as well as
+the continuation, because the stub validates nothing and continuation alone would be a
+fifteenth vacuous green. Notes:
+`../aetheris/docs/aetheris/milestones/bl-039-implementation-notes.md`.
+
+**Two corrections to the scout memo, recorded because they outlive this ticket.** The
+memo's §4 "one constraint the design must respect" attributes key-dropping to
+`Agent.Server.normalize_context_entry/1` and quotes both clauses fetching `"content"`;
+at HEAD the atom-key clause fetches `:content`, and the function is **not on the wire
+path** — it feeds `Agent.Server`'s `context:` state, while the adapter's messages come
+from `Loop.run/5`, which uses `config.fork_context` unnormalized. The design instruction
+(everything inside `content`) is unaffected; its stated reason was wrong. Also: the memo
+is at `docs/reviews/bl-039-fork-continuation-scout.md` in **this** repo, not
+`../aetheris/` as this row and the ticket text both say.
+
+**Spawned BL-060** (`mix hex.audit` red on an upstream `bandit` advisory), found by an
+off-territory gate run.
+
+---
+
+### BL-060 — `mix hex.audit` is red: bandit 1.11.1 carries EEF-CVE-2026-65623 (#TBD)
+**Size:** S · **Priority:** medium · **Section:** harness (`../aetheris/mix.exs`, `mix.lock`)
+
+Found 2026-07-26 by BL-039's ticket-boundary gate run — off-territory, exactly the way
+the gate rule intends. Filed the day it was found, not carried.
+
+```
+bandit 1.11.1 - EEF-CVE-2026-65623 (HIGH)
+  aka: CVE-2026-65623, GHSA-vg8x-66vg-5pxh
+  Quadratic CPU blow-up reassembling fragmented WebSocket messages in Bandit
+  https://osv.dev/vulnerability/EEF-CVE-2026-65623
+```
+
+**Upstream-triggered, not commit-triggered** — the advisory was published under a lock
+file nobody touched, which is the case `CLAUDE.md`'s `hex.audit` section names as the
+gate working rather than failing. BL-020 cleared all 15 advisories on 2026-07-17 with no
+residuals, so this is a fresh one, not a regression.
+
+`mix.exs` requires `{:bandit, "~> 1.0"}` and the lock pins **1.11.1**; hex advertises
+`Config: {:bandit, "~> 1.12"}` with 1.12.3 released 2026-07-25. So a patched line exists
+and the constraint already admits it — this looks like a lock bump plus a `mix.exs`
+floor, not a migration. **Confirm the advisory is actually fixed in the 1.12 line before
+bumping** (this row read the version list, not the changelog) and check the
+`thousand_island`/`websock`/`plug` co-resolution.
+
+Reachability is worth a sentence in the fix, not a reason to defer: bandit backs the
+playground API, which is **disabled by default** and started on demand
+(`api/server.ex`), and the WebSocket path is not something the harness exposes today.
+That bounds the exposure; it does not clear the advisory, and `hex.audit` has no
+suppression mechanism.
+
+Until it lands, the gate runs **expected-red, named with this row's ref** per the
+tracked-carry clause — named in packets, not re-triaged.
+
+**Done when:** `mix hex.audit` is clean, or the residual advisory has a recorded
+rationale here and the gate's expected-red state is stated with this ref.
+
 ---
 
 ### BL-059 — Parallel tool calls are silently discarded: the adapter keeps the first `tool_use` block (#TBD)
@@ -1891,6 +1965,14 @@ the dependency from the fork side; this line names it from the adapter side, so
 ticket can land its half and leave the other silently wrong. Fork's done-check must be
 re-run as part of (a), not deferred to whoever next opens `fork.ex`.
 
+**BL-039 has landed (2026-07-26), so the fork side is now concrete.** The pairing lives
+in `Fork.event_to_messages/1` and the id in `Fork.synthetic_tool_use_id/1`, which derives
+`"fork-toolu-#{step}"` — one id per *step*, which is precisely the assumption (a)
+removes. Both the function's comment and §4 point here. Under (a) the id must become one
+per *call*, and the `:tool_result` clause must consume N results rather than one; the
+canonical blocks themselves need no change, since `CanonicalMessage` already builds one
+block at a time and both turns take a list.
+
 ---
 
 ### BL-040 — Event-type list exists in three places; drift between them is silent (#TBD)
diff --git a/docs/rig/runbook.md b/docs/rig/runbook.md
index e119778..08d5bcc 100644
--- a/docs/rig/runbook.md
+++ b/docs/rig/runbook.md
@@ -118,20 +118,20 @@ a synthesized name, so a label in the list is always one an operator chose.
 
 ### Forking a run from a step
 
-> **Known failure — real-provider forks do not currently work (BL-039).** A fork whose
-> continuation runs against Anthropic fails at its **first LLM call** with
-> `HTTP 400: Unexpected role "tool"`. The reconstructed transcript carries a `"tool"`
-> role the API rejects, and relabeling alone would not fix it — the paired assistant
-> `tool_use` turns are never reconstructed. Tracked: BL-039 in
-> `docs/backlog-2026-06.md`. The button below is live and will happily start a fork
-> that then fails — the failure shows on the child run, not at the click.
+> **Real-provider forks reconstruct tool-call turns (BL-039, 2026-07-26).** The
+> reconstructed transcript carries assistant `tool_use` blocks paired with `user`
+> `tool_result` blocks, the shape a validating provider accepts. Before BL-039 it
+> carried a `"tool"` role and every fork continuation against Anthropic failed at its
+> **first LLM call** with `HTTP 400: Unexpected role "tool"`; that failure is fixed.
+> The determinism contract §4 states the pairing rule and its limits.
 >
-> **Stub-provider forks reach `done`, but their continuation is empty.** The fork
-> strips the response queue (`encode_config` drops `stub_responses`,
-> `../aetheris/lib/aetheris.ex:372`), so a stub fork gets `[stub exhausted]` on its
-> first call and terminates at step 0. So: **no fork on any provider has yet had a
-> meaningful continuation** — real ones are rejected at the first call, stub ones
-> exhaust at it. A green stub fork is not evidence that forking works.
+> **A stub-provider fork still starts with an empty response queue**, so it gets
+> `[stub exhausted]` on its first call and terminates at step 0. A green stub fork is
+> not evidence that forking works — only a continuation that runs past step 0 is.
+>
+> The button below starts a real run; if it fails, the failure shows on the child run,
+> not at the click. Since BL-039 the `Fork failed:` message carries the child run's
+> terminal error reason rather than only its run id.
 
 On the **Trajectory** tab, a completed step shows a **"Fork from here"** button. It
 starts a new run that replays the transcript up to that step and then continues live.
```

---

## 3. Implementation notes (committed, `3f561d9` — verbatim)

```markdown
# BL-039 — fork continuation against real providers (Design A)

Harness `ebc3878` (docs-first §4) + `e44d35c` (implementation). Agents half:
`7d6013a` (mirrors). Written against the ratified clause in
`docs/reviews/bl-039-contract-draft.md` and the scout memo, which lives in
`../aetheris-agents/docs/reviews/bl-039-fork-continuation-scout.md` (the ticket
text places it in this repo; it is in the sibling).

## Why the id is derived from the step, not generated

The obvious device — mint a random id and thread it from the `:llm_responded`
clause to the `:tool_result` clause — needs state between two clauses of a
`flat_map`, which means restructuring `extract_context/3` into a step-aware
fold. Deriving the id from the step instead (`"fork-toolu-#{step}"`) makes both
halves agree *by construction*, keeps each clause independent, and has a
property generation does not: two forks of the same run at the same step
produce a byte-identical prefix, so `context_hash` is stable. §4 already says
the id is opaque and only has to match within the pair, so nothing is lost.

## The orphan case that cannot arise, and why there is no guard for it

An assistant `tool_use` turn with no following `tool_result` would be rejected
by the API, so it is worth stating why reconstruction cannot emit one. A fork
point must have a `step_complete` (`find_step_complete_at/2`, exact match), and
`step_complete` is appended only after `execute_response/4` returns `{:ok, …}`.
Both tool outcomes reach that: success appends a `:tool_result`, and
`record_tool_error/6` appends one with `"is_error" => true` and *also* returns
`{:ok, …}`. The only tool path that returns `{:error, …}` is loop detection,
which appends no `step_complete` and ends the run — so that step is always the
last one, and can never sit *below* a valid fork step. Hence: within any
context reconstruction can be asked to build, every tool-call turn has its
result. A guard here would be unreachable code, and unreachable code cannot be
mutation-checked, so it would be a claim rather than a check.

Text turns are a related non-case: a `:text` response terminates the run
(`handle_llm_response/4`'s `%{type: :text}` clause writes `run_complete`
directly), so a text step never has a `step_complete` either. The text clause
in `event_to_messages/1` is kept because it is correct and cheap, not because a
well-formed trajectory exercises it below a fork point.

## Two scout claims corrected at HEAD

The scout's line-level facts were re-verified at `78df9f1` before the first
edit. Two need recording, neither changing any conclusion:

- **§4's "one constraint the design must respect"** attributes the key-dropping
  to `Agent.Server.normalize_context_entry/1`, and quotes both clauses as
  fetching `"content"`. At HEAD the atom-key clause fetches `:content`, and
  more importantly that function is not on the wire path at all: it feeds
  `Agent.Server`'s `context:` state field. The messages that reach the adapter
  come from `Loop.run/5`, which takes `config.fork_context` **unnormalized**.
  So the old message's `"tool_name"` sibling was passed through to
  `build_request_body/2`, not dropped before it. The design instruction is
  unaffected — everything belongs in `content` either way, and now does — but
  the reason is "the canonical shape has no top-level siblings", not "the
  normalizer would drop them".
- The scout says the pre-BL-039 `role: "tool"` message "feeds none of the four
  providers correctly". Confirmed, and worth keeping in view for BL-030: the
  fix is what makes cross-provider forking real, not merely legal.

## Arm 3 is the one that settles the contract

§4 deliberately does not assert that Anthropic accepts a synthesised id in a
*replayed* assistant turn — the live path had only ever sent Anthropic its own
`toolu_…` ids back. Arm 3 was run manually against the real API: **PASS**. The
mutation is the useful half: with reconstruction reverted, the same arm returns
`HTTP 400: messages: Unexpected role "tool". Allowed roles are "user" or
"assistant".` — byte-identical to the reason recorded in
`priv/runs/fork-aa6a6a65804f6645/trajectory.json`. So the arm demonstrably
reaches the endpoint, and the field failure is reproduced and then closed by the
same test.

It stays excluded by default (network, key, cost). Anyone re-running it needs
`--include requires_real_provider`; it skips itself without `ANTHROPIC_API_KEY`,
and it swaps `:req_options` because `config/test.exs` points them at a
`Req.Test` stub plug — a done-check written against the assumed runtime shape
fails here immediately, which is how that was found.

## What the next fork ticket needs to know

- **BL-059 disposition (a) breaks this file without touching it.** Positional
  pairing is sound only while a step carries one tool call. The dependency is
  named at `synthetic_tool_use_id/1` and in §4; BL-059's row carries the
  reciprocal. If (a) lands, fork's done-check is part of that diff.
- **BL-030 inherits a real capability now.** `fork_run/3`'s `overrides` can
  select a different provider and the reconstructed prefix will drive it. The
  CLI and Rig still pass a label only, so nothing operator-facing reaches it.
- **A green stub fork still proves nothing on its own.** The empty-queue
  behaviour is unchanged and deliberate; arm 1 gets past it only through
  `overrides`, which no operator entry point can supply. Any future fork test
  that asserts only `status == done` is a fifteenth vacuous green.
- **Part C is scoped to the fork command.** `terminal_error_reason/1` is
  general and `run`/`agent start` could adopt it, but they were not changed
  here. It returns `nil` both when no `:error` was recorded and when no event
  source is readable — the caller's fallback is the status message either way,
  so the two are deliberately not distinguished.
```

---

## 4. Touches deviations

Three, all named rather than absorbed:

1. **The scout memo is not where the ticket says it is.** The ticket and the BL-039 row both
   cite `../aetheris/docs/reviews/bl-039-fork-continuation-scout.md`; it is at
   `docs/reviews/bl-039-fork-continuation-scout.md` in **this** repo. Read there, re-verified
   at HEAD, and the row corrected in `0f48c09`.

2. **Files touched beyond the ticket's implied set.** `lib/aetheris/execution/canonical_message.ex`
   (new — the extraction the ticket mandates) and `lib/aetheris/cli/commands/run_helpers.ex`
   (Part C's reader; the ticket named only the CLI message). `run_helpers` gains a public
   `terminal_error_reason/1` and no behaviour change — `await_run/2` is untouched, so `run`
   and `agent start` are unaffected.

3. **BL-060 filed in `docs/backlog-2026-06.md`.** Not in BL-039's scope; filed because the
   gate rule requires a red gate to get a tracked ticket the day it is found, and
   `mix hex.audit` went red on an off-territory run.

## 5. One flagged observation

**A scout claim that is wrong in a way that outlives this ticket.** The memo's §4 "one
constraint the design must respect" says `Agent.Server.normalize_context_entry/1` drops every
non-`role`/`content` key, and that this "is already why `fork.ex:108`'s `tool_name` never
reaches the wire". At HEAD that function is not on the wire path at all — it feeds
`Agent.Server`'s `context:` state field (`server.ex:218`), while the messages the adapter
receives come from `Loop.run/5`, which uses `config.fork_context` **unnormalized**
(`loop.ex:70`). So the old message's `"tool_name"` sibling *was* serialised into
`build_request_body/2`'s body; it was ignored by Anthropic, not dropped by the harness. (The
memo also quotes both clauses fetching `"content"`; the atom-key clause fetches `:content`.)

The design instruction is unaffected — everything belongs inside `content`, and now is — but
the stated mechanism was load-bearing for a reader deciding whether top-level siblings are
safe. They are not automatically dropped. Recorded on the BL-039 row and in the notes so the
next reader of the memo gets the correction with it.
