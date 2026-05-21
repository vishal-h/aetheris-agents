# uc-payslip — Payslip Generation

**Status:** Complete (T0, T1, T2, T3)
**Repos:** `aetheris` (T0, T2-Part-A, T3 sprint) + `aetheris-agents` (T1, T2-Part-B, T3 agent)
**Goal:** Generate monthly payslips from CSV data, producing per-employee
HTML archives and merged PDFs, orchestrated by an Aetheris agent hierarchy.

---

## Why uc-payslip

This is the first production use-case milestone — using Aetheris to do real
business work rather than extend the harness. It validates the full agent
authoring pattern against a concrete business requirement and establishes
conventions for the `aetheris-agents` repo.

The existing workflow is manual: a finance person uploads a CSV to a chat
session, instructs an LLM step by step, downloads generated HTML, runs a
shell script to convert to PDF, then uploads to Drive and emails employees.
The process repeats monthly, is error-prone for arithmetic, and leaves no
audit trail.

Aetheris replaces the manual orchestration with a reproducible, auditable
agent run. The trajectory captures every tool call, every file written, and
every computation. A failed run is resumable from the last checkpoint. The
same agent file runs every month against a new CSV.

Three things needed to be in place before the first run:

**Arithmetic accuracy.** LLMs make arithmetic errors on payslip calculations.
A Python script handles all computation — the LLM only does HTML templating
with pre-computed values.

**PDF generation from within Aetheris.** `wkhtmltopdf` and `gs` were not in
the exec server allowlist. Both needed to be added before the agent could
invoke the PDF merger.

**`spawn_agent` sandbox inheritance.** Agent files set `sandbox_path` using
`__ENV__.file` so all tool calls resolve relative to the use-case root.
Sub-agents must inherit this path or their `read_file` and `write_file`
calls fail.

---

## What this enables

```bash
# From the aetheris repo
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
```

The orchestrator spawns one sub-agent per employee in parallel. Each
sub-agent generates HTML payslips for all months, then merges them into a
single PDF. A failed employee run can be re-run independently. The full
tree is inspectable via `mix aetheris tree show`.

---

## Exit criterion

| Criterion | Status |
|-----------|--------|
| `spawn_agent` propagates `sandbox_path`, `overlay_base_dir`, `context_strategy`, `max_context_steps` | ✅ ad3675f |
| `wkhtmltopdf` and `gs` callable via `run_command` | ✅ b5f329b |
| `payslip_compute.py` produces correct JSON for all earnings types | ✅ 2e8b0e1 |
| `merge_payslips.py` converts and merges HTML to PDF | ✅ f7f31a3 |
| Running the orchestrator against `sample_payroll.csv` produces `output/BTL_999/*.html` | ✅ b37dc72 |
| `output/BTL_999/merged.pdf` generated | ✅ b37dc72 |
| `mix aetheris tree show <run_id>` shows orchestrator + sub-agent tree | ✅ b37dc72 |
| `./scripts/sprint.sh payslip` passes | ✅ 7cb26d8 |
| All aetheris CI checks pass | ✅ 7cb26d8 |
| `README.md` and `runbook.md` complete | ✅ b37dc72 |

---

## Delivery sequence

```
T0 (aetheris) — spawn_agent sandbox inheritance          ✅ ad3675f
  └─ T1 (aetheris-agents) — payslip_compute.py          ✅ 2e8b0e1
     T2-Part-A (aetheris) — exec server allowlist        ✅ b5f329b
     T2-Part-B (aetheris-agents) — merge_payslips.py    ✅ f7f31a3
       └─ T3 (aetheris-agents + aetheris) — agent + docs + sprint  ✅ b37dc72 / 7cb26d8
```

T1 and T2-Part-B were implemented together in branch `t1-t2b-payslip-scripts`
in the aetheris-agents repo. T2-Part-A was a separate branch `t2a-exec-allowlist`
in the aetheris repo.

---

## Repos

| Ticket | Repo | Branch | Commit |
|--------|------|--------|--------|
| T0 | `aetheris` | `t0-spawn-agent-sandbox` | ad3675f |
| T1 | `aetheris-agents` | `t1-t2b-payslip-scripts` | 2e8b0e1 |
| T2-Part-A | `aetheris` | `t2a-exec-allowlist` | b5f329b |
| T2-Part-B | `aetheris-agents` | `t1-t2b-payslip-scripts` | f7f31a3 |
| T3 | `aetheris-agents` + `aetheris` | `t3-payslip-agent` | b37dc72 / 7cb26d8 |

---

## Tickets

---

### T0 — spawn_agent sandbox_path inheritance ✅

**Repo:** aetheris
**Commit:** ad3675f

**Problem:**

`spawn_agent` constructed sub-agent `RunConfig` with `sandbox_path: nil`.
Orchestrator agent files set `sandbox_path` to the use-case root via
`__ENV__.file`. Sub-agents with `nil` resolved file paths against the aetheris
repo CWD and failed.

**What was built:**

Three lines added to `build_child_config/4` in `spawn_agent.ex`:

```elixir
sandbox_path:      parent_config.sandbox_path,
context_strategy:  parent_config.context_strategy,
max_context_steps: parent_config.max_context_steps,
```

`overlay_base_dir` was already propagated from m12. `context_strategy` and
`max_context_steps` were added in m13 after `spawn_agent` was written and had
never been wired through.

Fields deliberately not propagated: `spawn_depth` (incremented by harness),
`run_id` (generated fresh), `label`, `coordinator_pid`, `orb_id`,
`blackboard_pid`, `stub_responses`.

**Tests:** 3 new unit tests using `Registry.lookup` + `:sys.get_state` to
inspect the child config directly after spawn.

---

### T1 — payslip_compute.py ✅

**Repo:** aetheris-agents
**Commit:** 2e8b0e1

**What was built:**

`payslip/scripts/payslip_compute.py` — reads a payroll CSV, applies business
rules, outputs JSON to stdout. No dependencies beyond Python 3 stdlib.

```bash
python3 payslip/scripts/payslip_compute.py data/payroll.csv
python3 payslip/scripts/payslip_compute.py data/payroll.csv --employee-id BTL_999
```

Business rules implemented:

- **Employee ID:** `/` → `_` in `employee_id_safe`; original preserved in
  `employee_id_raw`
- **Stipend:** `sal <= 25000` → single "Stipend" earnings entry; TDS from
  `tds` column
- **Consultant:** `employee_type == "Consultant"` (case-insensitive) → single
  "Consultant Fee" entry; TDS from `tds_94j` column
- **Regular:** Basic=50% sal, HRA=50% Basic, LTA=₹3000, WFH=₹3000,
  FlexiPay=remainder
- **Bonus/Arrears:** separate earnings entries if non-zero; never folded into sal
- **Arrears column detection:** case-insensitive prefix match on `"arrears"` —
  column name includes date range and varies per CSV export
- **Deductions:** PT, TDS (per type above), Loan Recovery; only included if
  non-zero
- **Month ordering:** newest first; `month_file` field: "Apr 2026" → "2026-04"

**Tests:** 11 pytest tests in `payslip/tests/test_payslip_compute.py` covering
all earnings types, bonus, arrears detection, month sorting, employee ID
filter, not-found exit.

---

### T2 — Exec server allowlist + merge_payslips.py ✅

**T2-Part-A repo:** aetheris — commit b5f329b
**T2-Part-B repo:** aetheris-agents — commit f7f31a3

**Problem:**

`wkhtmltopdf` and `gs` were not in the exec server `PERMITTED_COMMANDS`.
The existing `merge_html_to_pdf.sh` required `bash` which is explicitly
blocked.

**What was built:**

**T2-Part-A:** Two entries appended to `PERMITTED_COMMANDS` in
`native/aetheris_exec_server/src/runner.rs`:

```rust
"echo", "wkhtmltopdf", "gs",
```

Compiled binary at `priv/exec_server/aetheris_exec_server` updated and
committed.

**T2-Part-B:** `payslip/scripts/merge_payslips.py` — Python replacement for
`merge_html_to_pdf.sh`. Calls `wkhtmltopdf` and `gs` directly via
`subprocess.run` without requiring bash.

```bash
python3 payslip/scripts/merge_payslips.py output/BTL_999/
```

Sorts HTML files descending by filename (newest month first in merged PDF),
converts each to a temp PDF, merges with gs, writes `merged.pdf` to the
employee directory. Uses `tempfile.TemporaryDirectory()` for cleanup.

**Tests:** 6 pytest tests in `payslip/tests/test_merge_payslips.py` with
mocked subprocess calls covering sort order, per-file conversion, gs argument
order, failure propagation, empty directory, output path.

---

### T3 — Orchestrator agent + sprint + docs ✅

**Repo:** aetheris-agents + aetheris
**Commits:** b37dc72 (aetheris-agents) / 7cb26d8 (aetheris)

**What was built:**

**`payslip/agents/payslip_orchestrator.exs`**

Uses `__ENV__.file` to set `sandbox_path` to the payslip use-case root,
making the agent file portable regardless of invocation directory:

```elixir
agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

%Aetheris.RunConfig{
  run_id:            "payslip-orch-#{Aetheris.ID.generate()}",
  provider:          "anthropic",
  model:             "claude-haiku-4-5-20251001",
  label:             "Payslip Orchestrator",
  sandbox_path:      agent_root,
  overlay_base_dir:  nil,
  max_steps:         20,
  max_spawn_depth:   2,
  context_strategy:  :rolling,
  max_context_steps: 6,
  tools:             ["run_command", "spawn_agent", "wait_for_all"],
  system_prompt:     "...",
  user_prompt:       "Generate payslips for all employees in data/payroll.csv."
}
```

The orchestrator:
1. Runs `payslip_compute.py` to get all employees as JSON
2. Spawns one sub-agent per employee via `spawn_agent`
3. Each sub-agent runs compute for its employee, reads the template, writes
   one HTML per month, then runs `merge_payslips.py`
4. Collects all run_ids and calls `wait_for_all`
5. Reports summary

**`payslip/README.md`:** use case description, business rules, prerequisites,
folder structure, end-to-end run instructions, CSV column reference.

**`payslip/runbook.md`:** re-run one employee, handle bad CSV, resume failed
run, install wkhtmltopdf/gs, inspect trajectory.

**`scripts/sprint.sh payslip` (aetheris repo):** prerequisite checks
(python3, wkhtmltopdf, gs), runs orchestrator, verifies HTML and PDF output.

**`test/aetheris/agents_test.exs` addition (aetheris repo):** evaluates
`payslip_orchestrator.exs` and asserts `sandbox_path != nil`,
`overlay_base_dir == nil`, correct tools, `max_spawn_depth == 2`.

**`payslip/docs/t3-implementation-notes.md`**

---

## Repository structure

### aetheris repo additions

```
native/
  aetheris_exec_server/
    src/
      runner.rs              ← wkhtmltopdf + gs in PERMITTED_COMMANDS (T2-Part-A)
    priv/
      exec_server/
        aetheris_exec_server ← rebuilt binary (T2-Part-A)
lib/aetheris/execution/tool/
  spawn_agent.ex             ← sandbox_path inheritance (T0)
test/aetheris/
  agents_test.exs            ← payslip_orchestrator eval test (T3)
scripts/
  sprint.sh                  ← payslip case (T3)
docs/aetheris/milestones/
  uc-payslip-t0-implementation-notes.md
  uc-payslip-t2a-implementation-notes.md
```

### aetheris-agents repo

```
aetheris-agents/
  README.md
  .gitignore
  payslip/
    __init__.py
    README.md                       ← T3
    runbook.md                      ← T3
    milestone.md                    ← this document
    .gitignore
    data/
      sample_payroll.csv            ← committed (anonymised, covers all test cases)
      payslip_template.html         ← committed
    output/
      .gitkeep
    agents/
      payslip_orchestrator.exs      ← T3
    scripts/
      __init__.py
      payslip_compute.py            ← T1
      merge_payslips.py             ← T2-Part-B
    tests/
      __init__.py
      test_payslip_compute.py       ← T1 (11 tests)
      test_merge_payslips.py        ← T2-Part-B (6 tests)
    docs/
      t3-implementation-notes.md    ← T3
```

---

## Milestone reference row

```
| uc-payslip | payslip-generation | ✅ | Python + Elixir | Use Case |
spawn_agent sandbox inheritance, payslip_compute.py, merge_payslips.py,
payslip orchestrator | Monthly payslips from CSV; per-employee PDFs;
full audit trail |
```
