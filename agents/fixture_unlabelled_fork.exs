# Fixture: unlabelled, stub-provider, single-tool-call agent.
#
# Purpose (greppable): produce a run that is BOTH unlabelled AND forkable, so
# BL-029's gate check 3 — "forking an unlabelled parent leaves the child
# unlabelled" — can actually be executed.
#
# Why a fixture and not a real run:
#   - UNLABELLED. No `label:` key, deliberately. `runs.label` stays NULL, so
#     Rig's `COALESCE(r.label, r.run_id)` falls back to the run_id. That is the
#     exact input condition for the fork guard in TrajectoryView.tsx
#     (`run.label === run.run_id` -> parentLabel undefined -> unlabelled child).
#     Adding a label here would silently defeat the only check this file exists
#     for.
#   - STUB PROVIDER. Real-provider fork continuations currently fail at the
#     first LLM call (BL-039: fork.ex:104 emits a "tool" role Anthropic
#     rejects, and the paired assistant tool_use turns are never reconstructed
#     — fork.ex:95-96 drops non-text responses). Stub forks are the only forks
#     that presently complete, so the gate check must run on one.
#   - ONE TOOL CALL. A fork needs a forkable step. The step must be a *tool*
#     step: a stub response of `type: :text` terminates the run immediately
#     (harness CLAUDE.md, "Use `type: :tool_call` for intermediate stub
#     responses"), so the queue is tool_call-then-text: the tool_call produces
#     step 0, the text ends the run cleanly at step 1.
#
# Lives in the top-level `agents/` directory (with `mock_orchestrator.exs` and the
# `capability_matrix_*` set) rather than a `<use-case>/agents/` one: it belongs to no
# single use case, and it is a test fixture, not production.
#
# Run:
#   cd ~/sandbox/elixirws/aetheris
#   mix aetheris run ../aetheris-agents/agents/fixture_unlabelled_fork.exs
#
# Then fork it from the Rig UI at step 0 and confirm the child's label is its
# own fork-id, NOT the parent's run_id.

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

%Aetheris.RunConfig{
  run_id: "fixture-unlabelled-fork-#{Aetheris.ID.generate()}",
  mode: :record,
  # Default per run_config.ex:153; stated explicitly because it is load-bearing,
  # not incidental. adapter_module_for("stub") -> LLMAdapter.Stub
  # (llm_adapter.ex:47).
  provider: "stub",
  model: "stub-model",
  # NO `label:` KEY — see header. This is the point of the fixture.
  sandbox_path: agent_root,
  overlay_base_dir: nil,
  max_steps: 4,
  context_strategy: :full,
  tools: ["run_command"],
  system_prompt: """
  You are a fixture agent. You exist to produce one forkable tool step.
  The stub adapter supplies your responses; this prompt is never sent to a
  real provider.
  """,
  user_prompt: "Emit one tool call, then finish.",
  # Queue shape matters: tool_call first (creates the forkable step), text
  # second (terminates). `echo` is allowlisted in the exec server
  # (native/aetheris_exec_server/src/runner.rs:20).
  stub_responses: [
    %{
      type: :tool_call,
      content: nil,
      tool_name: "run_command",
      tool_use_id: "toolu_fixture_01",
      tool_input: %{
        "command" => "echo",
        "args" => ["fixture-unlabelled-fork: forkable step"],
        "timeout_ms" => 10_000
      },
      latency_ms: 0,
      resolved_model: nil,
      system_fingerprint: nil
    },
    %{
      type: :text,
      content: "Fixture complete: one forkable tool step recorded.",
      tool_name: nil,
      tool_input: nil,
      latency_ms: 0,
      resolved_model: nil,
      system_fingerprint: nil
    }
  ]
}
