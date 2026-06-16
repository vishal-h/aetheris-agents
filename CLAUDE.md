# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repo is

A collection of use-case agent implementations built on top of the **Aetheris** harness (sibling repo at `../aetheris`). Each use case is a self-contained directory with Python scripts, Elixir agent files, tests, and docs. No Elixir source lives here — only `.exs` agent scripts that the harness evaluates.

The two repos work together:
- `aetheris/` — the harness (`mix aetheris run`, `mix aetheris inspect`, etc.)
- `aetheris-agents/` — this repo; use-case scripts and agent files

All sprint and agent commands are run from `~/sandbox/elixirws/aetheris/`, not from this repo.

---

## Commands

**Run tests for a use case:**
```bash
# From the aetheris-agents/ root
python3 -m pytest payslip/tests/ -v
python3 -m pytest api/tenant/tests/ api/gateway/tests/ -v

# Single test file
python3 -m pytest payslip/tests/test_payslip_compute.py -v

# Single test
python3 -m pytest payslip/tests/test_payslip_compute.py::test_net_salary -v
```

> `python3` here is the mise-managed Python 3.12 (`mise.toml`). If `python3 -m pytest` reports "No module named pytest", install with `python3 -m pip install pytest`. The system `pip3` (Python 3.10) writes to a different site-packages.

**Run a script standalone:**
```bash
cd ~/sandbox/elixirws/aetheris-agents/payslip
python3 scripts/payslip_compute.py data/sample_payroll.csv | python3 -m json.tool
python3 scripts/generate_employee_payslips.py BTL_999
```

**Run an agent:**
```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
```

**Evaluate an agent file (syntax/struct check, no LLM call):**
```bash
cd ~/sandbox/elixirws/aetheris
mix run --eval 'Code.eval_file("../aetheris-agents/api/tenant/agents/at1cmd.exs")'
```

**Run a sprint case:**
```bash
cd ~/sandbox/elixirws/aetheris
./scripts/sprint.sh payslip
./scripts/sprint.sh uc_api_agent_t1
```

**Inspect a run:**
```bash
mix aetheris inspect <run_id>
mix aetheris tree show <run_id>
mix aetheris list --limit 20
```

**Aetheris checks (run from `aetheris/` repo, not here):**
```bash
cd ~/sandbox/elixirws/aetheris
mix format --check-formatted
mix credo --strict
mix dialyzer
mix test
```

---

## Architecture

### Core principle

**Scripts do; agents decide.** Python scripts contain all deterministic logic (CSV parsing, computation, file generation, API calls). Elixir agent files contain only the `RunConfig` or `OrbConfig` struct — the LLM reads context, calls scripts via `run_command`, and orchestrates results. Never ask the LLM to construct file content or compute values programmatically.

### Use-case layout

Each use case follows:
```
{use_case}/
  agents/           # .exs files — RunConfig or OrbConfig structs
  scripts/          # Python — deterministic logic, one responsibility per file
  tests/            # pytest — unit + integration; conftest.py per directory
  data/             # input files; .gitignore excludes real data
  docs/             # t*-implementation-notes.md written after each ticket
  output/           # gitignored; .gitkeep committed
```

Current use cases: `payslip`, `drive`, `email`, `api` (uc-api-agent / TAP protocol), `boxy-pipeline` (pure Python; no Aetheris agent — includes data layer scripts for catalog and sales order extraction).

### Agent files

Agent `.exs` files evaluate to either a `%Aetheris.RunConfig{}` (solo agent) or a `%Aetheris.OrbConfig{}` (multi-agent). The harness's `mix aetheris run` loads the first positional file — extra file paths passed to `run_orb` in sprint.sh are ignored by the CLI.

**Critical conventions:**

```elixir
# Always use __ENV__.file — never File.cwd!()
agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))
# For agents two levels deep (e.g. api/tenant/agents/):
agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))

# Always nil when output must persist
overlay_base_dir: nil,

# context_strategy for orb agents
context_strategy: :full,   # short-lived pipeline agents (<~10 steps)
context_strategy: :rolling, max_context_steps: 6,  # long-running orchestrators only
```

> `:rolling` with a small `max_context_steps` truncates old messages and can leave orphaned `tool_use_id` references, causing HTTP 400. Use `:full` for any agent that runs fewer than ~10 steps.

### Multi-agent orbs (OrbConfig)

Agents communicate via blackboard and `send_message`. The pattern:

1. **Sender** writes to blackboard: `write_blackboard key: "tap:intent:{id}", value: json`
2. **Sender** signals receiver: `send_message to: "{run_id}", message: "...intent_id: {id}"`
3. **Receiver** waits: `wait_for_event condition: "message_received", timeout_ms: 120000`
4. **Receiver** extracts the key from the message body, reads from blackboard

Run IDs must be pre-established in the OrbConfig so send_message targets are known at prompt-write time:
```elixir
orb_id    = "uc-api-t1-#{Aetheris.ID.generate()}"
at1cmd_id = "#{orb_id}-at1cmd"
cot1_id   = "#{orb_id}-cot1"
```

### Python script conventions

- **One responsibility per script.** Compute scripts → JSON. Generation scripts → files. No mixing.
- **stdout is the contract.** Scripts print JSON to stdout; agents parse it. Errors go to stderr.
- **Exit codes:** 0 on success, 1 on recoverable error. Always 0 for analysis/reporting scripts.
- **`--output-dir` flag** on generation scripts (default `"output"`); lets tests write to `tmp_path`.
- **`cwd=USE_CASE_ROOT`** in subprocess calls from tests so `data/` and `scripts/` resolve correctly.
- **No `__init__.py`** in use-case directories whose name collides with stdlib packages. Use `conftest.py` to insert `scripts/` into `sys.path` instead.
- **Done-check thresholds:** set numeric thresholds (e.g. "≥N resolved items") only after running the pipeline against actual sample data. Estimating before examining output consistently produces wrong numbers and requires a correction commit.
- **Slugification belongs in Python, not the LLM.** When file paths depend on user-supplied strings (search terms, names), implement a `slug_term()` function in a script that returns a filesystem-safe slug. The orchestrator calls the script once, receives pre-computed slugs alongside the original values, and passes both to sub-agents — the LLM does string substitution only, never derives slugs itself.
- **Explicit sink selection with fail-fast.** When a pipeline supports multiple operational sinks (e.g., DB upsert vs. file export), select via an env var resolved at agent eval time. A required-but-absent credential must `raise` immediately — never silently fall back to a different sink. Regression-guard the raise in sprint with a hermetic env check: `env -u MISSING_VAR SINK=mode mix run --eval ...`.
- **Parallel sub-agent file isolation.** When an orchestrator spawns parallel sub-agents that each write files for the same logical output, give each sub-agent a per-term directory (e.g., `data/raw/{slug}/`) rather than a shared flat directory. Without isolation, parallel agents silently overwrite each other's output.
- **Stage CLIs degrade, they don't crash.** A pipeline script hitting empty, null, or malformed input (a provider returning `null`, one bad JSONL line) emits a partial result with a `{"status": "partial"}` envelope and `exit 1` — never an uncaught exception that breaks the stdout contract. Guard per-line/per-item (skip + count `skipped`/`errors`), and treat an API's explicit `null` the same as absent (`x or []`, not `dict.get(k, default)`).
- **Verify a foreign table's live DDL before writing raw SQL to it.** When a script writes to a table owned by another system (e.g. an Ecto/ActiveRecord schema), confirm the real column types and write semantics (`\d table`) before trusting an inferred schema — raw SQL breaks on array types (`jsonb[]` vs `jsonb`), `NOT NULL` timestamps with no DB default, and update-field semantics (don't clobber columns the owner manages, e.g. soft-delete `status`). Test against a faithful schema clone, not a hand-rolled table.

### conftest.py pattern

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: ...")
```

Integration tests that require external tools (wkhtmltopdf, etc.) get `@pytest.mark.integration` and are auto-skipped if the tool is absent.

When multiple integration tests share an expensive setup (e.g. running the full pipeline once), extract it into a `@pytest.fixture(scope="module")` rather than repeating the subprocess chain in each test body.

### Domain documents (api/ use case)

The `api/domain/` directory holds two JSONL files read by the gateway agent:
- `ct.stu.vocabulary.jsonl` — tenant-visible; intent definitions, field rules, enum lookups
- `ct.stu.behaviour.jsonl` — gateway-internal; execution modes, on_duplicate, outcomes

Each line is a self-contained JSON record. `record_type` is the discriminator. Blank lines are separators, not errors.

### Sprint script

`aetheris/scripts/sprint.sh` is the integration test harness. Add new cases before the `# Summary` section. All paths from sprint.sh to this repo must use `../aetheris-agents/...` (sprint runs from `aetheris/`). The `run_orb` helper passes its args to `mix aetheris run`; only the first file path is loaded.

---

## Definition of done — doc sync

`docs/rig/specs.md`, `docs/rig/runbook.md`, and `docs/rig/architecture.md` must
stay in sync with the Rig source code. Use the drift checker to verify:

```bash
# From aetheris-agents/ root
python3 scripts/drift_check.py

# Or via sprint.sh (from aetheris/)
./scripts/sprint.sh drift_check
```

**Checks run:** event types (event.ex ↔ specs.md §6), Tauri commands (lib.rs ↔ specs.md §4),
DB schema (store.ex ↔ specs.md §2), env vars (Rust code ↔ specs.md §1 ↔ runbook.md),
routes (registry.ts ↔ App.tsx), payload field sampling (live DB ↔ specs.md §6),
milestone README Status: lines.

**When to run:** after any Rig milestone, after adding commands, event types, env vars,
routes, or DB tables. Zero FAIL findings and zero WARN findings required before committing.

**Optional payload fields:** suffix with `?` in the §6 table cell (e.g. `` `stop_reason?` ``) to allow the field to be absent from current DB events without triggering a FAIL. The drift check emits INFO instead. Add the `?` suffix when the field is valid but not yet emitted by the harness version in use; the INFO firing is the trigger to drop the `?` and promote the field to required.

**Tests:** `python3 -m pytest tests/test_drift_check.py -v`

---

## Key docs to read for each use case

| Use case | Read first |
|----------|-----------|
| payslip | `payslip/docs/t3c-implementation-notes.md` |
| drive | `drive/docs/t3-implementation-notes.md` |
| email | `email/docs/t3-implementation-notes.md` |
| api (TAP) | `docs/uc-api-agent-design.md`, `api/docs/t1-implementation-notes.md` |
| boxy-pipeline | `boxy-pipeline/docs/m-boxy-pipeline.md`, `boxy-pipeline/docs/m-boxy-pipeline-1a.md`, `boxy-pipeline/docs/runbook.md` |
| eduloka | `eduloka/runbook.md`, `docs/milestones/m-eduloka-discovery-summary.md` |

The `docs/agent-creation-guide.md` is the authoritative reference for building new agents.
