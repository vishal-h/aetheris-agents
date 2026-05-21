# T3 Implementation Notes — Payslip Orchestrator

## The `__ENV__.file` pattern for sandbox_path

```elixir
agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))
```

`__ENV__.file` is set by the Elixir runtime to the absolute path of the file being evaluated — including when the file is loaded via `Code.eval_file/1`. `Path.dirname` gives the `payslip/agents/` directory; the `".."` join walks up to `payslip/`. `Path.expand` resolves any `..` segments to a clean absolute path.

This is the correct approach because:

1. **Invocation-independent.** `File.cwd!()` returns the directory where `mix aetheris run` was invoked, which can be anywhere (`~/aetheris`, `~/aetheris-agents`, `~`, etc.). The orchestrator must always find its data at `payslip/data/` regardless of the caller's working directory. `__ENV__.file` is always the script's own location.

2. **Test-safe.** `Code.eval_file` preserves `__ENV__.file`, so the eval test in `agents_test.exs` correctly verifies that `sandbox_path` differs from the test's `File.cwd!()` (the aetheris repo root).

3. **No environment variable dependency.** The path is computed from the file itself at evaluation time — no `AETHERIS_AGENTS_DIR` export required.

## Why overlay_base_dir is nil

`overlay_base_dir` enables OverlayFS isolation: writes go to a per-run `upper/` layer and are discarded (or archived) after the run. The payslip use case is the opposite — **the output IS the persistent result**. The PDF and HTML files in `payslip/output/{employee_id}/` are the deliverables; they must survive the run and be accessible to the user after `mix aetheris run` exits. Setting `overlay_base_dir: nil` means all `write_file` calls go directly to the real filesystem under `sandbox_path`. This is intentional and is documented in the system prompt's Rules section.

## Task prompt design for sub-agents

The orchestrator spawns sub-agents via `spawn_agent`. The `spawn_agent` tool maps `task_prompt` to the child's `system_prompt` — there is no separate `system_prompt` parameter in the `spawn_agent` call. This means **all context, instructions, and constraints must be embedded in `task_prompt`**.

Consequences for the prompt design:
- The task prompt includes both the high-level goal ("Generate payslips for employee {id}") and every step in order (run compute, read template, write HTML per month, merge PDF, report).
- Earnings type rules are spelled out inline so the sub-agent never needs to guess: "regular" → 5-component breakdown, "stipend" → single Stipend line, "consultant" → single Consultant Fee line.
- The explicit rule "All salary values are pre-computed. Do not recalculate anything." prevents the sub-agent from re-deriving Basic/HRA/LTA/etc. from the raw salary, which would risk rounding divergence.
- Output path patterns (`output/{id}/{month_file}.html`, `output/{id}/`) are given as literals so the sub-agent writes files in the expected locations for `merge_payslips.py`.

## Deviations from milestone spec

None. The implementation matches the T3 spec exactly:
- `sandbox_path` via `__ENV__.file` ✓
- `overlay_base_dir: nil` ✓
- `context_strategy: :rolling`, `max_context_steps: 6` ✓
- `max_spawn_depth: 2` ✓
- `tools: ["run_command", "spawn_agent", "wait_for_all"]` ✓
- Sub-agent tools: `["run_command", "read_file", "write_file"]` ✓
- `wait_for_all` with `timeout_ms: 300000` ✓
- `model: "claude-haiku-4-5-20251001"` ✓
