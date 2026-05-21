# Payslip Runbook

Operational procedures for the uc-payslip use case.
All commands assume `~/sandbox/elixirws/` as the working root.

---

## Run the full sprint

```bash
cd ~/sandbox/elixirws/aetheris
./scripts/sprint.sh payslip
```

Requires: `ANTHROPIC_API_KEY`, `python3`, `wkhtmltopdf`, `gs`.
Uses `sample_payroll.csv` if `payroll.csv` is absent.

---

## Generate payslips for a new month

1. Replace `payslip/data/payroll.csv` with the new month's CSV.
2. Run the orchestrator:
   ```bash
   cd ~/sandbox/elixirws/aetheris
   mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
   ```
3. Output lands in `payslip/output/{employee_id_safe}/`.

---

## Re-run one employee

Run the generation script directly — no agent needed:

```bash
cd ~/sandbox/elixirws/aetheris-agents/payslip
python3 scripts/generate_employee_payslips.py BTL_999
```

To write to a different directory:
```bash
python3 scripts/generate_employee_payslips.py BTL_999 --output-dir /tmp/test_out
```

---

## Handle a bad CSV row

1. Fix the row in `payslip/data/payroll.csv`.
2. Delete partial output for that employee if any:
   ```bash
   rm -rf payslip/output/BTL_999/
   ```
3. Re-run the single-employee script or the full orchestrator.

---

## Resume a failed orchestrator run

Failed runs checkpoint automatically. When the Aetheris application next
starts (any `mix aetheris` command), interrupted runs resume from their
last checkpoint. You do not need to re-run the agent file.

Check status:
```bash
mix aetheris agent status <run_id>
mix aetheris inspect <run_id>
```

Inspect which sub-agents completed:
```bash
mix aetheris tree show <run_id>
```

---

## Inspect a run

```bash
# Full agent tree — orchestrator + per-employee sub-agents
mix aetheris tree show <run_id>

# Orchestrator trajectory
mix aetheris trajectory <run_id>

# Sub-agent trajectory
mix aetheris trajectory <child_run_id>

# Recent runs
mix aetheris list --limit 10
```

---

## Verify output

```bash
ls -la payslip/output/BTL_999/
# Expect: 2026-04.html  2026-03.html  merged.pdf

xdg-open payslip/output/BTL_999/merged.pdf   # Linux
open payslip/output/BTL_999/merged.pdf        # macOS
```

---

## Run the test suite

```bash
cd ~/sandbox/elixirws/aetheris-agents
python3 -m pytest payslip/tests/ -v
```

Unit tests (no external tools needed): always run.
Integration tests: skipped automatically if `wkhtmltopdf` or `gs` absent.

---

## Install prerequisites

**wkhtmltopdf:**
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# macOS
brew install wkhtmltopdf

wkhtmltopdf --version
```

**Ghostscript:**
```bash
# Ubuntu/Debian
sudo apt-get install ghostscript

# macOS
brew install ghostscript

gs --version
```

---

## Validate the computation script standalone

```bash
cd ~/sandbox/elixirws/aetheris-agents/payslip

# All employees
python3 scripts/payslip_compute.py data/sample_payroll.csv | python3 -m json.tool

# One employee
python3 scripts/payslip_compute.py data/sample_payroll.csv --employee-id BTL_999

# Unknown employee — should exit non-zero
python3 scripts/payslip_compute.py data/sample_payroll.csv --employee-id BTL_000
echo "Exit code: $?"
```
