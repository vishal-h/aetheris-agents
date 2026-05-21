# uc-payslip — Payslip Generation

This use case generates monthly payslips for all employees in a payroll CSV. An Aetheris orchestrator runs `payslip_compute.py` to produce structured salary JSON, then spawns one sub-agent per employee. Each sub-agent renders per-month HTML payslips from the JSON and the HTML template, then merges them into a single PDF via `wkhtmltopdf` and Ghostscript. All output survives the run because `overlay_base_dir` is nil — files are written directly to `payslip/output/`.

---

## Business rules

| Condition | Earnings type | Breakdown |
|-----------|---------------|-----------|
| `sal ≤ ₹25,000` | `stipend` | Single **Stipend** line; TDS from `tds` column |
| `employee_type == "Consultant"` (case-insensitive) | `consultant` | Single **Consultant Fee** line; TDS from `tds_94j` column |
| All others | `regular` | Basic = 50% sal · HRA = 50% Basic · LTA = ₹3,000 · WFH Allowance = ₹3,000 · Flexi Pay = remainder |

**Bonus** — if the `bonus` column is non-zero, a separate **Bonus** earnings line is appended after the salary components. Never folded into sal.

**Arrears** — any CSV column whose name starts with `arrears` (case-insensitive, e.g. `arrears - Jan-Feb 2025`) is detected automatically. If non-zero, a separate **Arrears** earnings line is appended.

**Deductions** — PT, TDS, and Loan Recovery are included only when non-zero.

---

## Prerequisites

| Tool | Notes |
|------|-------|
| `python3` | stdlib only — no pip install needed |
| `wkhtmltopdf` | HTML → PDF conversion |
| `gs` (Ghostscript) | PDF merge |
| Aetheris | Running at `../aetheris`; `ANTHROPIC_API_KEY` must be set |

---

## Folder structure

```
payslip/
├── agents/
│   └── payslip_orchestrator.exs   # Aetheris RunConfig — top-level orchestrator
├── data/
│   ├── payroll.csv                # Your payroll data (not committed)
│   ├── payslip_template.html      # HTML template used by sub-agents
│   └── sample_payroll.csv         # Reference example (3 employees)
├── docs/
│   └── t3-implementation-notes.md
├── output/                        # Generated — not committed
│   └── {employee_id_safe}/
│       ├── {YYYY-MM}.html         # One file per payslip month
│       └── merged.pdf             # All months merged, newest first
├── scripts/
│   ├── merge_payslips.py          # HTML → PDF merge (wkhtmltopdf + gs)
│   └── payslip_compute.py         # CSV → JSON salary computation
├── tests/
│   ├── test_merge_payslips.py
│   └── test_payslip_compute.py
├── milestone.md
├── README.md
└── runbook.md
```

---

## How to run end-to-end

1. Place your payroll CSV at `payslip/data/payroll.csv` (see `sample_payroll.csv` for the column format).

2. Change to the Aetheris repo:
   ```bash
   cd ~/sandbox/elixirws/aetheris
   ```

3. Run the orchestrator:
   ```bash
   mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
   ```

4. Inspect the agent tree:
   ```bash
   mix aetheris tree show <run_id>
   ```

5. Output is in `payslip/output/{employee_id_safe}/`:
   - `{YYYY-MM}.html` — per-month payslip
   - `merged.pdf` — all months merged, newest first

---

## CSV column reference

| Column | Description |
|--------|-------------|
| `employee_id` | Employee identifier (e.g. `BTL/999`); `/` is sanitised to `_` in filenames and the `--employee-id` flag |
| `employee_type` | `Regular` or `Consultant` |
| `designation` | Job title |
| `name` | Full name |
| `email` | Work email |
| `pan` | PAN card number |
| `doj` | Date of joining (`DD-Mon-YYYY`) |
| `month` | Payslip month (e.g. `Apr 2026`) |
| `paid_in` | Month salary was paid (e.g. `May 2026`) |
| `sal` | Gross salary / CTC component |
| `bonus` | One-time bonus; `0` if none |
| `arrears - …` | Arrears column(s); any column whose name starts with `arrears` is auto-detected |
| `loan_recovery` | Loan recovery deduction; blank or `0` if none |
| `pt` | Professional Tax |
| `tds_94j` | TDS under section 94J (Consultants only) |
| `tds` | Income tax TDS (Regular and Stipend employees) |
| `work_mode` | `Hybrid`, `WFH`, or `Remote` |
| `account_number` | Bank account reference printed on the payslip |
