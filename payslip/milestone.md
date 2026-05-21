# Milestone: uc-payslip — Payslip Generation

## Why

Bitloka Solutions Private Limited generates monthly payslips for employees with diverse salary structures (regular, stipend, consultant). Today the process is manual: HR enters data into spreadsheets, calculates salary breakdowns, copies values into an HTML template, and exports to PDF. This is error-prone and slow, especially with edge cases like bonuses, arrears, and consultant TDS (section 94J vs standard TDS).

## What this enables

- One-command payslip generation for all employees from a CSV input
- AI-orchestrated sub-agent per employee: computes, renders per-month HTML, merges to PDF
- Correct handling of all salary types: regular 5-component breakdown, stipend single-line, consultant fee
- Bonus and arrears as separate earnings lines — never folded into the base salary
- Merged PDF per employee with newest month first
- Full audit trail via Aetheris trajectory and agent tree

## Exit criterion

- `mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs` completes without error for the sample payroll
- Each employee in `data/payroll.csv` has `output/{employee_id_safe}/merged.pdf`
- `python3 -m pytest payslip/tests/ -v` — all 17 tests pass

## Delivery sequence

| # | Ticket | Repo | What |
|---|--------|------|------|
| 0 | T0 | aetheris | Propagate `sandbox_path` to sub-agents in `spawn_agent.ex` |
| 1 | T1 | aetheris-agents | `payslip_compute.py`: CSV → JSON salary computation (11 tests) |
| 2 | T2-Part-B | aetheris-agents | `merge_payslips.py`: HTML → PDF merge via wkhtmltopdf + gs (6 tests) |
| 3 | T3 | both | Orchestrator, docs, sprint case, eval test |

## Repos

| Repo | Role |
|------|------|
| `aetheris` | Agent harness (Elixir + Rust); hosts sprint case and eval test |
| `aetheris-agents` | Agent scripts and use-case assets; hosts orchestrator and Python tools |

## Tickets

### T0 — sandbox_path propagation (aetheris)

**File:** `lib/aetheris/execution/tool/spawn_agent.ex`

Copy `sandbox_path` from the parent `RunConfig` to the child `RunConfig` inside `build_child_config/4`. Without this fix, sub-agents spawned by the orchestrator fall back to a default temp path and cannot read the payslip data directory or write to the shared `output/` tree.

---

### T1 — payslip_compute.py (aetheris-agents)

**File:** `payslip/scripts/payslip_compute.py`

Stdlib-only Python 3 script. Reads a payroll CSV and emits per-employee, per-month salary JSON to stdout. Supports `--employee-id` filter; exits non-zero with an error message if the employee is not found. Month entries are sorted newest-first.

Business rules:
- **Regular** (sal > ₹25,000, not Consultant): Basic = 50% sal, HRA = 50% Basic, LTA = ₹3,000, WFH Allowance = ₹3,000, Flexi Pay = remainder
- **Stipend** (sal ≤ ₹25,000): single "Stipend" line, TDS from `tds` column
- **Consultant** (employee_type == "Consultant", case-insensitive): single "Consultant Fee" line, TDS from `tds_94j` column
- **Bonus**: separate earnings entry if `bonus` column is non-zero
- **Arrears**: any column with name prefix `arrears` (case-insensitive) is auto-detected; non-zero value produces a separate "Arrears" earnings entry

**Tests:** `payslip/tests/test_payslip_compute.py` — 11 pytest cases

---

### T2-Part-B — merge_payslips.py (aetheris-agents)

**File:** `payslip/scripts/merge_payslips.py`

Stdlib-only Python 3 script. Globs `*.html` files in an employee output directory, sorts them descending by filename (newest month first), converts each to a temp PDF via `wkhtmltopdf`, then merges all temp PDFs into `merged.pdf` via Ghostscript (`gs`). Uses `tempfile.TemporaryDirectory` for intermediate files. Exits non-zero on any subprocess failure; exits 0 with a message if no HTML files are found.

**Tests:** `payslip/tests/test_merge_payslips.py` — 6 pytest cases (subprocess mocked)

---

### T3 — Orchestrator, docs, sprint (both repos)

**aetheris-agents:**
- `payslip/agents/payslip_orchestrator.exs` — Aetheris RunConfig; uses `__ENV__.file` to set `sandbox_path` to the `payslip/` directory so all tool paths resolve correctly regardless of where `mix aetheris run` is invoked from
- `payslip/README.md` — usage, business rules, CSV column reference
- `payslip/runbook.md` — operational procedures
- `payslip/milestone.md` — this document
- `payslip/docs/t3-implementation-notes.md`

**aetheris:**
- `scripts/sprint.sh` — added `payslip` target: checks prerequisites, copies sample CSV if `payroll.csv` absent, runs orchestrator, verifies output
- `test/aetheris/agents_test.exs` — orchestrator eval test: asserts `RunConfig` shape, `sandbox_path`, `overlay_base_dir`, tools, `max_spawn_depth`, `context_strategy`

## Repository structure

```
aetheris-agents/
└── payslip/
    ├── agents/
    │   └── payslip_orchestrator.exs   # T3
    ├── data/
    │   ├── payroll.csv                # production input (not committed)
    │   ├── payslip_template.html      # HTML template for sub-agents
    │   └── sample_payroll.csv         # reference (3 employees: regular×2mo, stipend, consultant)
    ├── docs/
    │   └── t3-implementation-notes.md
    ├── output/                        # generated (not committed)
    │   └── {employee_id_safe}/
    │       ├── {YYYY-MM}.html
    │       └── merged.pdf
    ├── scripts/
    │   ├── merge_payslips.py          # T2-Part-B
    │   └── payslip_compute.py         # T1
    ├── tests/
    │   ├── test_merge_payslips.py
    │   └── test_payslip_compute.py
    ├── milestone.md
    ├── README.md
    └── runbook.md

aetheris/
├── scripts/sprint.sh                  # T3: payslip target added
└── test/aetheris/agents_test.exs      # T3: orchestrator eval test added
```

## Milestone reference

| Milestone | Tickets | Status |
|-----------|---------|--------|
| uc-payslip | T0, T1, T2-Part-B, T3 | complete |
