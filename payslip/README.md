# uc-payslip — Payslip Generation

Generates monthly HTML payslips and merged PDFs for all employees in a
payroll CSV. An Aetheris orchestrator spawns one sub-agent per employee;
each sub-agent runs a single Python script that handles computation,
template filling, and PDF merging end-to-end.

---

## Design principle

Scripts do, agents decide.

- **Python scripts** handle all data transformation, arithmetic, file I/O,
  and HTML generation — everything deterministic and testable in isolation.
- **Agents** handle orchestration: read the employee list, spawn sub-agents
  in parallel, wait for results, report.
- The LLM is never asked to generate file content programmatically or perform
  arithmetic.

This keeps prompts simple, business logic testable without Aetheris, and
prevents the LLM from reaching for inline scripting patterns.

---

## Business rules

| Condition | Earnings type | Salary breakdown |
|-----------|---------------|-----------------|
| `sal ≤ ₹25,000` | Stipend | Single **Stipend** line; no component breakdown |
| `employee_type = Consultant` | Consultant | Single **Consultant Fee** line; TDS from `tds_94j` column |
| All others | Regular | Basic = 50% sal · HRA = 50% Basic · LTA = ₹3,000 · WFH Allowance = ₹3,000 · Flexi Pay = remainder |

**Bonus** — if `bonus` column is non-zero: separate earnings line, never
folded into salary.

**Arrears** — any column whose name starts with `arrears` (case-insensitive,
e.g. `arrears - Jan-Feb 2025`) is auto-detected. Non-zero value adds a
separate Arrears earnings line.

**Deductions** — PT, TDS, and Loan Recovery are included only when non-zero.

---

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| `python3` | Computation and HTML generation | stdlib only — no pip install needed |
| `wkhtmltopdf` | HTML → PDF conversion | `sudo apt-get install wkhtmltopdf` |
| Aetheris | Agent harness | See `../aetheris` |
| `ANTHROPIC_API_KEY` | LLM orchestration | Set in environment |

Verify:
```bash
mix aetheris doctor          # from aetheris repo
python3 -m pytest payslip/tests/ -v
```

---

## Folder structure

```
payslip/
├── agents/
│   └── payslip_orchestrator.exs     # Aetheris orchestrator — entry point
├── data/
│   ├── payroll.csv                  # Your payroll data (gitignored)
│   ├── payslip_template.html        # HTML template
│   └── sample_payroll.csv           # Reference: 3 employees covering all types
├── docs/
│   └── t*-implementation-notes.md   # Per-ticket implementation notes
├── output/                          # Generated (gitignored)
│   └── {employee_id_safe}/
│       ├── {YYYY-MM}-Payslip.html   # Source template (kept as build artefact)
│       ├── {YYYY-MM}-Payslip.pdf    # One PDF per month
│       └── {YYYY-MM}-Payslip.csv   # Source data for that month
├── scripts/
│   ├── payslip_compute.py           # CSV → per-employee JSON with salary breakdown
│   └── generate_employee_payslips.py # JSON + template → per-month HTML, PDF, CSV
├── tests/
│   ├── conftest.py                  # Integration marker; skips if wkhtmltopdf absent
│   ├── test_payslip_compute.py      # 11 unit tests
│   └── test_generate_employee_payslips.py  # 7 integration tests
├── milestone.md
├── README.md
└── runbook.md
```

---

## How to run

1. Place your payroll CSV at `payslip/data/payroll.csv`.
   See `sample_payroll.csv` for the required column format.

2. From the aetheris repo:
   ```bash
   cd ~/sandbox/elixirws/aetheris
   mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
   ```

3. Inspect the agent tree:
   ```bash
   mix aetheris tree show <run_id>
   ```

4. Output per employee:
   ```bash
   ls ../aetheris-agents/payslip/output/BTL_999/
   # 2026-04-Payslip.html  2026-04-Payslip.pdf  2026-04-Payslip.csv
   # 2026-03-Payslip.html  2026-03-Payslip.pdf  2026-03-Payslip.csv
   ```

---

## Scripts

Each script can be run standalone from the `payslip/` directory:

```bash
cd ~/sandbox/elixirws/aetheris-agents/payslip

# Compute salary breakdown for all employees
python3 scripts/payslip_compute.py data/payroll.csv

# Compute for one employee
python3 scripts/payslip_compute.py data/payroll.csv --employee-id BTL_999

# Generate HTML payslips, per-month PDFs, and CSVs for one employee
python3 scripts/generate_employee_payslips.py BTL_999
```

---

## CSV column reference

| Column | Description |
|--------|-------------|
| `employee_id` | Identifier (e.g. `BTL/999`); `/` → `_` in output paths |
| `employee_type` | `Regular` or `Consultant` |
| `designation` | Job title |
| `name` | Full name |
| `email` | Work email |
| `pan` | PAN card number |
| `doj` | Date of joining (`DD-Mon-YYYY`) |
| `month` | Payslip month (e.g. `Apr 2026`) |
| `paid_in` | Month salary was paid (e.g. `May 2026`) |
| `sal` | Gross salary |
| `bonus` | One-time bonus; `0` if none |
| `arrears - …` | Any column starting with `arrears`; auto-detected |
| `loan_recovery` | Loan deduction; blank or `0` if none |
| `pt` | Professional Tax |
| `tds_94j` | TDS section 94J — Consultants only |
| `tds` | Income tax TDS — Regular and Stipend employees |
| `work_mode` | `Hybrid`, `WFH`, or `Remote` |
| `account_number` | Bank account printed on payslip |
