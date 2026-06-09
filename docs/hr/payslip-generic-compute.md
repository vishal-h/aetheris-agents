# payslip: Generic payroll CSV + config-driven compute

## Context

`payslip_compute.py` currently hard-codes column names (`sal`, `bonus`,
`pt`, `tds` etc.) and salary breakdown percentages (`basic = sal * 0.50`,
`lta = 3000` etc.). Adding a new allowance or changing a percentage
requires a code change.

This ticket makes the script generic:
- CSV columns declare their role via `e_` (earnings) / `d_` (deductions)
  prefix convention
- Breakdown rules (percentages, fixed amounts, thresholds) move to a
  `payroll_config.json` file
- The script becomes reusable for any company's payroll structure

---

## Part 1 — CSV column convention

### New header format

```
employee_id, employee_type, designation, name, email, pan, doj,
month, paid_in,
e_sal, e_bonus, e_arrears_jan_feb_2025,
d_loan_recovery, d_pt, d_tds_94j, d_tds,
work_mode, account_number
```

### Rules

- Columns prefixed `e_` are earnings. Label = strip prefix, replace
  underscores with spaces, title-case. Override via label map in config.
- Columns prefixed `d_` are deductions. Same label derivation.
- `e_sal` is the reserved base salary column — drives earnings_type
  detection and breakdown computation.
- `e_arrears*` columns (any `e_` column whose name contains "arrears")
  are grouped as arrears earnings — same behaviour as today.
- All other fixed columns (`employee_id`, `name`, `email` etc.) are
  identity/metadata — unchanged.
- Old column names (`sal`, `bonus`, `pt`, `tds` etc.) are no longer
  supported. Migration: rename in the CSV header.

### Migration for existing `data/sample_payroll.csv`

Rename columns:
```
sal              → e_sal
bonus            → e_bonus
arrears - Jan-Feb 2025 → e_arrears_jan_feb_2025
loan_recovery    → d_loan_recovery
pt               → d_pt
tds_94j          → d_tds_94j
tds              → d_tds
```

---

## Part 2 — `payroll_config.json`

Place at `payslip/data/payroll_config.json`. Script reads it at startup
via `--config` flag (default: `data/payroll_config.json`).

```json
{
  "config_version": "1",
  "stipend_threshold": 25000,
  "consultant_type_value": "consultant",
  "regular_breakdown": {
    "basic_pct":      0.50,
    "hra_pct":        0.50,
    "lta_fixed":      3000.00,
    "wfh_fixed":      3000.00,
    "flexi_residual": true
  },
  "labels": {
    "e_sal":           "Base Salary",
    "e_bonus":         "Performance Bonus",
    "d_pt":            "Professional Tax",
    "d_tds":           "TDS",
    "d_tds_94j":       "TDS (94J)",
    "d_loan_recovery": "Loan Recovery"
  }
}
```

### Field reference

| Field | Type | Description |
|-------|------|-------------|
| `config_version` | `"1"` | For future schema evolution |
| `stipend_threshold` | number | `e_sal` ≤ this → `earnings_type = "stipend"` |
| `consultant_type_value` | string | `employee_type` value that triggers consultant branch |
| `regular_breakdown.basic_pct` | float | Basic = `e_sal * basic_pct` |
| `regular_breakdown.hra_pct` | float | HRA = `basic * hra_pct` |
| `regular_breakdown.lta_fixed` | float | LTA fixed amount |
| `regular_breakdown.wfh_fixed` | float | WFH allowance fixed amount |
| `regular_breakdown.flexi_residual` | bool | Flexi Pay = `e_sal - basic - hra - lta - wfh` |
| `labels` | object | Column key → display label. Fallback: strip `e_`/`d_`, replace `_` with space, title-case |

---

## Part 3 — Updated `payslip_compute.py`

### Key changes

**Column scanning** replaces hard-coded names:

```python
def get_earnings_cols(fieldnames):
    return [f for f in fieldnames if f.startswith('e_') and f != 'e_sal']

def get_deductions_cols(fieldnames):
    return [f for f in fieldnames if f.startswith('d_')]

def get_arrears_cols(fieldnames):
    return [f for f in fieldnames
            if f.startswith('e_') and 'arrears' in f.lower()]
```

**Label resolution:**

```python
def col_label(col, label_map):
    if col in label_map:
        return label_map[col]
    name = col[2:] if col.startswith(('e_', 'd_')) else col
    return name.replace('_', ' ').title()
```

**Config-driven breakdown** (regular earnings type):

```python
bd = config['regular_breakdown']
basic     = round(sal * bd['basic_pct'], 2)
hra       = round(basic * bd['hra_pct'], 2)
lta       = bd['lta_fixed']
wfh       = bd['wfh_fixed']
flexi_pay = round(sal - basic - hra - lta - wfh, 2) if bd['flexi_residual'] else 0.0
```

**Dynamic deductions** (replaces hard-coded `pt`, `tds`, `loan_recovery`):

```python
deductions = []
for col in deductions_cols:
    val = _float(row.get(col, ''))
    if val:
        deductions.append({'label': col_label(col, label_map), 'amount': val})
```

**TDS selection for consultant** — `tds_94j` was the consultant TDS
column. With the prefix scheme the script no longer special-cases it:
all `d_*` columns are included if non-zero. For consultant rows where
both `d_tds` and `d_tds_94j` may be present, both appear as separate
deduction line items. This is more transparent than the current
hard-coded selection.

### CLI interface (unchanged)

```
python3 scripts/payslip_compute.py <csv_path> [--employee-id ID] [--config PATH]
```

`--config` defaults to `data/payroll_config.json` relative to cwd.

---

## Part 4 — Update `payslip/tools.json`

Add `--config` arg to `payslip_compute` entry:

```json
{
  "name": "config",
  "flag": "--config",
  "type": "file",
  "required": false,
  "default": "data/payroll_config.json",
  "description": "Path to payroll config JSON"
}
```

Also add `--employee-id` arg (currently missing from the manifest):

```json
{
  "name": "employee_id",
  "flag": "--employee-id",
  "type": "string",
  "required": false,
  "default": null,
  "description": "Filter output to a single employee ID"
}
```

---

## Acceptance criteria

- [ ] `payslip/data/payroll_config.json` created with the schema above
- [ ] `payslip/data/sample_payroll.csv` headers renamed to `e_`/`d_` convention
- [ ] `payslip_compute.py` reads `e_`/`d_` columns dynamically — no
      hard-coded column names except `e_sal` as the base salary key
- [ ] `payslip_compute.py` reads breakdown rules from config — no
      hard-coded percentages or fixed amounts
- [ ] Label fallback works: `e_flexi_pay` → `Flexi Pay`,
      `d_loan_recovery` → `Loan Recovery`
- [ ] Label override works: `d_tds` → `TDS` (from config labels map)
- [ ] Output JSON structure unchanged — same keys, same nesting
- [ ] `python3 -m pytest payslip/tests/ -v` exits 0
- [ ] Existing tests updated to use new column names if they reference
      CSV headers directly

## Files to create/modify

- `payslip/data/payroll_config.json` (new)
- `payslip/data/sample_payroll.csv` (rename columns)
- `payslip/scripts/payslip_compute.py` (rewrite compute logic)
- `payslip/tools.json` (add --config and --employee-id args)
- `payslip/tests/` (update any tests that use old column names)

## Notes

**`e_sal` is reserved.** It is the only column with special treatment
— drives `earnings_type` detection and the regular breakdown. All other
`e_*` columns are treated uniformly as additional earnings line items.

**Consultant TDS change.** Previously `tds_94j` was selected instead of
`tds` for consultant rows. With the generic approach, all `d_*` columns
are included if non-zero. If a payroll has both `d_tds` and `d_tds_94j`,
both appear. Payroll operators should zero out the inapplicable column.

**Backward compatibility.** Old CSVs with un-prefixed column names will
silently produce empty earnings/deductions (no `e_`/`d_` columns found).
The script should detect this and exit with a clear error:
`"No e_/d_ columns found. Did you rename the CSV headers?"`

**Tests.** If `conftest.py` or test fixtures embed CSV content with old
column names, update them. Do not add new test files — update existing
ones.
