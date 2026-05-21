# Payslip Runbook

Operational procedures for the uc-payslip use case.

---

## Re-run one employee

**Option A — filter at the orchestrator level:**
Edit `user_prompt` in `payslip_orchestrator.exs` to name the specific employee, then re-run:
```bash
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
```

**Option B — run the compute script and spawn a manual sub-agent:**
```bash
cd ~/sandbox/elixirws/aetheris
python3 ../aetheris-agents/payslip/scripts/payslip_compute.py \
  ../aetheris-agents/payslip/data/payroll.csv \
  --employee-id BTL_999 | python3 -m json.tool
```
Then construct and run a one-off sub-agent config pointing at that employee's data.

---

## Handle a bad CSV row

1. Fix the row in `payslip/data/payroll.csv`.
2. Delete any partial output for that employee:
   ```bash
   rm -rf payslip/output/BTL_999/
   ```
3. Re-run the orchestrator (or use the single-employee path above).

---

## Resume a failed orchestrator run

Check run status:
```bash
mix aetheris agent status <run_id>
```

If checkpointed, the interrupted run resumes automatically the next time
the Aetheris application starts — for example, when you run any
`mix aetheris` command. You do not need to re-run the orchestrator agent file.

Inspect which sub-agents completed and which failed:
```bash
mix aetheris inspect <run_id>
```

---

## Inspect the agent tree

```bash
# Show the full orchestrator + sub-agent tree
mix aetheris tree show <run_id>

# Inspect a specific sub-agent's trajectory
mix aetheris trajectory <child_run_id>
```

---

## wkhtmltopdf not installed

**Ubuntu / Debian:**
```bash
sudo apt-get install wkhtmltopdf
```

**macOS:**
```bash
brew install wkhtmltopdf
```

**Verify:**
```bash
wkhtmltopdf --version
```

---

## Ghostscript not installed

**Ubuntu / Debian:**
```bash
sudo apt-get install ghostscript
```

**macOS:**
```bash
brew install ghostscript
```

**Verify:**
```bash
gs --version
```

---

## Check output for an employee

```bash
ls -la payslip/output/BTL_999/
# Should show: 2026-04.html  2026-03.html  merged.pdf  (etc.)

open payslip/output/BTL_999/merged.pdf
# macOS — use xdg-open on Linux
```

---

## Run the test suite

```bash
cd ~/sandbox/elixirws/aetheris-agents
python3 -m pytest payslip/tests/ -v
```

All 17 tests (11 compute + 6 merge) should pass with no external dependencies.
