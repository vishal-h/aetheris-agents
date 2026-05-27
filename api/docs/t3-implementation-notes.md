## T3 Implementation Notes — Skill Extraction and Structured Clarification

### What was built

T3 adds two capabilities on top of the T2 steady-state baseline:

1. **Skill extraction**: `extract_skill_hints.py` reads a cot1 trajectory export and produces a JSON summary of the tool sequence, scripts called, flags raised, and record count. `at1cmd.exs` reads `tenant/data/skill_hint.json` at eval time and appends it to the system prompt if present.

2. **Structured clarification**: `cot1` can now ask `at1qry` to clarify a missing `termName` when the vocabulary has no `current: true` term. `at1qry` handles two message types: `"TAP result ready"` (existing flow) and `"TAP clarification needed"` (new clarification path).

---

### Skill injection — eval-time vs LLM-call-time

The skill hint is injected at eval time via Elixir string interpolation (`#{skill_context}`), not at LLM call time. This means:

- The skill context is baked into the system_prompt when `Code.eval_file/1` runs.
- The file read happens once per orb, not per tool call.
- If `tenant/data/skill_hint.json` does not exist, `skill_context` is `""` and the prompt is unchanged.

This is different from `Aetheris.Skill.Injector.inject/2`, which wraps the prompt at runtime. The simpler `File.exists?` / `File.read!` pattern is used here because at1cmd reads a single JSON file rather than a named skill from the store.

---

### Trajectory export format

`mix aetheris trajectory <run_id> --export path.json` writes only the **events array** (not the full trajectory struct). `extract_skill_hints.py` handles both:

- Plain events array: `[{...}, {...}]`
- Full trajectory dict: `{"schema_version": "1", "run_id": "...", "meta": {}, "events": [...]}`

The relevant events for extraction are `tool_called` events. `run_command` events carry the script path in `args[0]` and may carry intent JSON in subsequent args. Intent type, flags, and record count are parsed from intent JSON strings found in those args.

---

### Clarification trigger condition

Clarification fires ONLY when:
1. `validate_intent.py` flags `termName` as unresolved
2. The vocabulary (`domain/ct.stu.vocabulary.jsonl`) has no term with `"current": true`

The Annual term has `"current": true`, so the clarification path does **not** fire in any T3 sprint run. The `cot1` prompt explicitly states: "In normal runs (Annual has 'current': true), skip this step."

This ensures the T3 sprint is deterministic without mocking or modifying the vocabulary.

---

### at1qry tools expanded

at1qry gained `write_blackboard` and `send_message` tools in T3. These are required for the clarification path: at1qry writes the failed result to the blackboard and sends response messages back to cot1. The max_steps ceiling was raised from 15 to 20 to accommodate the extra exchanges.

---

### Clarification round tracking

The round limit (2) applies to ALL exchanges, including invalid responses. The round counter tracks how many validation attempts have been consumed. If the operator provides an invalid response, that round is consumed before re-requesting. If the limit is reached, `tap:result:{intent_id}` is written with `intent_lifecycle.status: "failed"` and `reason: "clarification_unresolved"`.

---

### Sprint case: two runs with step comparison

The `uc_api_agent_t3` sprint case:

1. Clears `skill_hint.json` before run 1 (cold start)
2. Runs the full T3 orb (at1cmd_sprint → cot1 → at1qry)
3. Exports cot1's trajectory, extracts skill hint, writes `tenant/data/skill_hint.json`
4. Runs the full orb again (run 2, with hint)
5. Reports at1cmd step counts for both runs

The step counts for at1cmd are identical (5 steps) because the workflow is fully prescribed. The skill hint helps the LLM reason more directly about intent classification on run 2, but at1cmd's 5 discrete steps (parse CSV → package intent → write blackboard → send message → report) remain mandatory regardless. The hint's value compounds over iterations: `cot1` receives a hint on run 2 that confirms the expected script sequence, reducing exploration.

---

### T4 handoff

T4 adds at1qry persistence via m13 webhooks. Key things T4 must know:

- The clarification path in at1qry currently uses `read_blackboard` for the operator response (assumes pre-written). T4 should wire this to an actual webhook/API for real operator interaction.
- `context_strategy: :full` is mandatory on ALL orb agents. Do not introduce `:rolling` without verifying orphaned `tool_use_id` behaviour.
- `at1qry.exs` standalone file is the eval-check target. The OrbConfig inline version inside `at1cmd.exs` is what actually runs in the orb.
