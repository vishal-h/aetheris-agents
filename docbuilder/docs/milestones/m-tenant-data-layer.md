# m-tenant-data-layer — Docbuilder: Tenant Data Layer

**Repo:** `aetheris-agents` · **Base commit:** `cacbff3` (post-m7 HEAD)
**Milestone path:** `docbuilder/docs/milestones/m-tenant-data-layer.md`
**Backlog ref:** `docs/backlog-docbuilder-data-layer.md` §BL-TDL-001

---

## Goal

Establish the tenant data layer as a first-class concept in the docbuilder
pipeline. Human-editable JSONL and CSV files at the tenant level become the
authoritative source for structured reference data (employee records, salary
structures). DuckDB views defined as committed `.sql` files provide the stable
query interface that `context_builder.exs` calls against. The LLM selects
which view to call from a `data_manifest.json` rather than constructing
queries itself.

Immediate payoff: the `docbuilder_offer_letter` sprint's direct-context
workaround (introduced in m7 t3 because the NL path cannot guarantee
display-string currency) is retired. The NL path becomes viable because the
view formats currency — not the operator.

---

## What is NOT in scope

- Drive agent sync (`sync_tenant_data.py` / Drive → local cache) — deferred
  to BL-TDL-005; local files only in this milestone (see D-Drive below)
- Parquet materialisation — deferred to BL-TDL-002; DuckDB reads CSV/JSONL
  natively and the view interface is identical
- Standalone `data_resolver.exs` agent — deferred to BL-TDL-003; extend
  `context_builder.exs` first
- Agent-managed writes — deferred to BL-TDL-004; read-only data layer in
  this milestone
- Client master data, rate cards, or any data file beyond `employees.jsonl`
  and `salary_structures.csv`
- Any change to `validate_fields.py`, the orchestrator, or any renderer
- Any change to the invoice or payslip pipelines

---

## Design decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **`tenants/{tenant_id}/data/`** as the canonical location | Tenant data is a platform-level concern shared across all agents, not a docbuilder artifact. `tenants/` is a new top-level directory in `aetheris-agents/` — this milestone introduces it. Not nested under `docbuilder/data/templates/`. |
| D2 | **DuckDB via Python package** (`import duckdb`), invoked with `run_command python3` | The exec-server allowlist permits `python3`; no explicit `duckdb` CLI entry found. Matches the existing `resolve_last_run.py` / `context_builder.exs` pattern exactly. |
| D3 | **Views as committed `.sql` files**, registered in `data_manifest.json` | Views are code — they encode business logic (e.g. currency formatting, field joins). The manifest is what the LLM reads; it never introspects the raw schema. |
| D4 | **Currency formatted in the SQL view** (`printf('₹%.2f', amount)` in DuckDB) | The CSV stores numeric `amount`; the view produces the display string. This is the fix for the m7 t3 direct-context workaround — the view is the single source of truth for display formatting, not the operator's free-text input. |
| D5 | **Local files only** — no Drive sync in this milestone | `fetch_data.py` has no Drive code; the Drive agent is a separate use case. Local JSONL/CSV are the source of truth for now; the Drive agent sync is a clean follow-on (BL-TDL-005) that plugs in without changing the query helper or views. |
| D6 | **`query_tenant_data.py`** as the shared query helper — a deterministic Python script, not an agent tool | Any agent invokes it via `run_command python3`. The interface is `query_tenant_data.py --tenant {id} --view {name} --params '{json}'`; it returns a JSON array of rows to stdout. When (B/C) deployment arrives, only this script changes — callers are untouched. |
| D7 | **Sensitive data gitignored; sample fixtures committed** | `tenants/bitloka/data/*.jsonl` and `tenants/bitloka/data/*.csv` are gitignored (real employee data). `tenants/bitloka/data/sample/` contains anonymised fixtures committed for sprint cases. A `.gitkeep` and runbook note document where real files come from. |
| D8 | **`context_builder.exs` extended** with a `query_tenant_data` step | The LLM reads `data_manifest.json`, selects the appropriate view, calls `run_command python3 scripts/query_tenant_data.py`, and uses the returned rows to build `confirmed_context`. Tool list unchanged: `["read_file", "write_file", "run_command"]`. |
| D-Drive | **Drive agent sync is the intended production path — deferred** | BL-TDL-005. The Drive agent fetches files into `tenants/{tenant_id}/data/`; the query helper and views are unchanged. The local cache is the abstraction boundary: callers never know whether files arrived via Drive agent, manual copy, or future sync. |
| D-B/C | **`query_tenant_data.py` is the (A)→(B/C) seam** | In deployment scenario (A) today: local path resolution. In (B/C) later: the script becomes an HTTP call to the tenant data service or an MCP server call. The interface (`--tenant`, `--view`, `--params` → JSON rows) is stable; the implementation is swappable. This is the architectural intent — it must not be treated as an implementation detail. |

---

## Repository structure (after this milestone)

```
aetheris-agents/
  tenants/                              ← NEW top-level directory
    bitloka/
      data/
        .gitignore                      ← ignores *.jsonl, *.csv (real data)
        sample/
          employees_sample.jsonl        ← anonymised, committed
          salary_structures_sample.csv  ← anonymised, committed
        views/
          employee_offer_context.sql    ← committed (code)
          employee_payslip_context.sql  ← committed (code, future use)
        data_manifest.json              ← committed (view registry)

  docbuilder/
    scripts/
      query_tenant_data.py              ← NEW shared query helper
    agents/
      context_builder.exs               ← MODIFIED (query_tenant_data step)
    data/
      sample/
        employees_sample.jsonl          ← symlink or copy from tenants/
    tests/
      test_query_tenant_data.py         ← NEW unit + integration tests
```

**Real data location (gitignored, operator-managed):**
```
tenants/bitloka/data/employees.jsonl
tenants/bitloka/data/salary_structures.csv
```

---

## Context fields resolved by the data layer

The `employee_offer_context` view returns all 18 `OFFER_LETTER_REQUIRED`
fields from `validate_fields.py` plus the optional bonus fields:

| Field | Source | View formatting |
|-------|--------|----------------|
| `candidate_name` | `employees.jsonl` | as-is |
| `candidate_email` | `employees.jsonl` | as-is |
| `candidate_phone` | `employees.jsonl` | as-is |
| `candidate_address` | `employees.jsonl` | as-is |
| `role` | `employees.jsonl` | as-is |
| `title` | `employees.jsonl` | as-is |
| `date` | caller-supplied param | ISO date |
| `annual_ctc` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `basic_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `hra_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `lta_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `wfh_allowance_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `flexi_pay_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `total_earnings_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `professional_tax_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `tds_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `total_deductions_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `net_take_home_monthly` | `salary_structures.csv` | `printf('₹%,.2f', amount)` |
| `internship_acknowledgement` | `employees.jsonl` (optional) | as-is or `""` |
| `business_performance_bonus_pct` | `employees.jsonl` (optional) | as-is or `""` |
| `business_performance_bonus_period` | `employees.jsonl` (optional) | as-is or `""` |
| `individual_performance_bonus_pct` | `employees.jsonl` (optional) | as-is or `""` |
| `individual_performance_bonus_period` | `employees.jsonl` (optional) | as-is or `""` |

`date` is the one field not in the data layer — it is supplied by the operator
in the NL request and extracted by `context_builder` as today.

---

## Ticket set

### t1 — `tenants/` directory + canonical data files + `.gitignore`

**Scope.** Introduce `tenants/` as a new top-level directory in
`aetheris-agents/`. Create the `tenants/bitloka/data/` structure: `.gitignore`
(ignoring real `*.jsonl` and `*.csv`), `sample/` with anonymised fixtures for
Ajay Rao (the sprint case employee), `views/` directory (empty — populated in
t2), and `data_manifest.json` (skeleton — populated in t2). No pipeline code
changes in this ticket.

The sample fixtures must cover all fields in the Context fields table above.
The sample `salary_structures_sample.csv` stores **numeric** `amount` values
— display formatting is the view's responsibility (D4), not the CSV's.

**Contract refs.**
- `CLAUDE.md` §Learning — m7-docbuilder (verified runtime shape before
  writing commands — applies equally to file schemas)
- `agent-creation-guide.md` §Repository structure (`.gitignore` rules)
- Design decisions D1, D4, D7 in this doc

**Touches.**
- `tenants/` (new top-level directory)
- `tenants/bitloka/data/.gitignore`
- `tenants/bitloka/data/sample/employees_sample.jsonl`
- `tenants/bitloka/data/sample/salary_structures_sample.csv`
- `tenants/bitloka/data/views/` (empty dir + `.gitkeep`)
- `tenants/bitloka/data/data_manifest.json` (skeleton with `views: []`)
- `docbuilder/runbook.md` — new §"Tenant data layer" (location, gitignore
  convention, how to add a real data file, the D-Drive deferred note)

**Do not generate.**
- Any `.sql` view files (t2)
- `query_tenant_data.py` (t2)
- Any change to `context_builder.exs` (t3)
- Any change to sprint cases (t4)

**Runbook update rule.** The §"Tenant data layer" section is part of this
ticket's Touches and done-check — an operator needs to know where real data
files go and that they are gitignored before they can use the data layer.

**Done-check.**
```bash
# From aetheris-agents/
# 1. Directory structure exists
python3 -c "
import pathlib, json
root = pathlib.Path('tenants/bitloka/data')
assert root.exists(), 'tenants/bitloka/data missing'
assert (root / '.gitignore').exists(), '.gitignore missing'
assert (root / 'sample/employees_sample.jsonl').exists(), 'employee sample missing'
assert (root / 'sample/salary_structures_sample.csv').exists(), 'salary sample missing'
assert (root / 'views').exists(), 'views dir missing'
assert (root / 'data_manifest.json').exists(), 'data_manifest.json missing'
print('PASS — directory structure present')
"

# 2. Sample data is valid (JSONL parseable, CSV has required columns)
python3 -c "
import json, csv, pathlib
root = pathlib.Path('tenants/bitloka/data/sample')
# employees: one record for Ajay Rao with all required fields
records = [json.loads(l) for l in (root / 'employees_sample.jsonl').read_text().splitlines() if l.strip()]
required = {'employee_id','candidate_name','candidate_email','candidate_phone',
            'candidate_address','role','title'}
for r in records:
    missing = required - r.keys()
    assert not missing, f'employee record missing fields: {missing}'
print(f'PASS — {len(records)} employee record(s), all required fields present')
# salary: numeric amount column, no display strings
rows = list(csv.DictReader((root / 'salary_structures_sample.csv').open()))
assert 'employee_id' in rows[0], 'salary CSV missing employee_id column'
assert 'component' in rows[0], 'salary CSV missing component column'
assert 'amount' in rows[0], 'salary CSV missing amount column'
for r in rows:
    float(r['amount'])  # must be numeric
print(f'PASS — {len(rows)} salary row(s), amount column is numeric')
"

# 3. .gitignore correctly excludes real data files.
# Use grep -F (fixed-string): a bare `grep '*.jsonl'` treats `*` as a regex quantifier and
# ERRORS under some engines (e.g. ugrep), where a leading `*` is an empty sub-expression.
grep -qF '*.jsonl' tenants/bitloka/data/.gitignore && \
grep -qF '*.csv'   tenants/bitloka/data/.gitignore && \
echo 'PASS — .gitignore excludes *.jsonl and *.csv' || \
echo 'FAIL — .gitignore missing entries'
# Authoritative check (behaviour, not file contents): real files ignored, sample/ tracked.
git check-ignore -q tenants/bitloka/data/employees.jsonl && \
! git check-ignore -q tenants/bitloka/data/sample/employees_sample.jsonl && \
echo 'PASS — git check-ignore: real ignored, sample tracked'

# 4. Runbook section exists
grep -q 'Tenant data layer' docbuilder/runbook.md && \
echo 'PASS — runbook §Tenant data layer present' || \
echo 'FAIL — runbook section missing'
```

**Claude-code prompt.**
> Read `CLAUDE.md` §Learning — m7-docbuilder and `agent-creation-guide.md`
> §Repository structure before starting.
>
> **Task:** introduce `tenants/` as a new top-level directory in
> `aetheris-agents/` and create the `tenants/bitloka/data/` structure per
> `docbuilder/docs/milestones/m-tenant-data-layer.md` §"Repository structure"
> and §t1 Touches.
>
> Key constraints:
> - D7: real `*.jsonl` and `*.csv` are gitignored; only `sample/` files are
>   committed. The `.gitignore` must cover both extensions.
> - D4: `salary_structures_sample.csv` stores **numeric** `amount` values —
>   no `₹` display strings in the CSV. Display formatting is the view's job.
> - Sample data covers Ajay Rao (employee_id: `EMP001`) with the salary
>   structure from the m7 sprint context (basic 37500, HRA 15000, LTA 3000,
>   WFH 2500, flexi pay 7800, total earnings 65800, PT 200, TDS 8300,
>   total deductions 8500, net take-home 67300, annual CTC 900000). Include
>   the optional bonus fields and internship_acknowledgement in the employee
>   record so the full conditional path is exercisable from the sample.
> - `data_manifest.json` skeleton: `{"tenant_id": "bitloka", "views": []}` —
>   views are populated in t2.
> - Add §"Tenant data layer" to `docbuilder/runbook.md` covering: canonical
>   location (`tenants/{tenant_id}/data/`), gitignore convention, how to add
>   a real data file, and the D-Drive deferred note (Drive agent sync is the
>   future production path; local files for now).
>
> Run the done-check (verbatim from §t1) and include its full output at the
> top of the review packet. Write implementation notes to
> `docbuilder/docs/milestones/m-tenant-data-layer-t1-implementation-notes.md`
> and commit.

---

### t2 — `query_tenant_data.py` + DuckDB views + `data_manifest.json`

**Scope.** Write `docbuilder/scripts/query_tenant_data.py` — the shared query
helper (D6). Write two `.sql` view files: `employee_offer_context.sql` and
`employee_payslip_context.sql`. Populate `data_manifest.json` with the view
registry. The script takes `--tenant`, `--view`, and `--params` (JSON string)
as CLI args and returns a JSON array of rows to stdout. Unit and integration
tests cover the query helper against the sample fixtures.

**Contract refs.**
- `agent-creation-guide.md` §"Scripts do; agents decide" (query helper is
  a deterministic script, not an agent)
- `agent-creation-guide.md` §"run_command has no stdin parameter" (script
  must accept `--params` FILE or inline JSON arg — not stdin)
- `CLAUDE.md` §Learning — m7-docbuilder (verify the runtime shape before
  writing the command — check DuckDB `printf` format string for `₹` output
  before writing the view)
- Design decisions D2, D3, D4, D6 in this doc

**Touches.**
- `docbuilder/scripts/query_tenant_data.py` (new)
- `tenants/bitloka/data/views/employee_offer_context.sql` (new)
- `tenants/bitloka/data/views/employee_payslip_context.sql` (new)
- `tenants/bitloka/data/data_manifest.json` (populate views array)
- `docbuilder/tests/test_query_tenant_data.py` (new)
- `docbuilder/runbook.md` — add one paragraph to §"Tenant data layer"
  documenting `query_tenant_data.py` CLI interface and the view manifest

**Do not generate.**
- Any change to `context_builder.exs` (t3)
- Any change to sprint cases (t4)
- Any additional view beyond the two specified

**Runbook update rule.** The `query_tenant_data.py` CLI interface and the
view manifest format are part of the §"Tenant data layer" runbook section —
an operator authoring a new view needs to know both.

**Done-check.**
```bash
# From aetheris-agents/
pip install duckdb --break-system-packages -q

# 1. Unit + integration tests
python3 -m pytest docbuilder/tests/test_query_tenant_data.py -v

# 2. Standalone query against sample data
python3 docbuilder/scripts/query_tenant_data.py \
  --tenant bitloka \
  --view employee_offer_context \
  --params '{"employee_id": "EMP001"}' \
  --data-root tenants

# 3. Verify display-string currency in output (D4)
python3 -c "
import subprocess, json
result = subprocess.run([
    'python3', 'docbuilder/scripts/query_tenant_data.py',
    '--tenant', 'bitloka',
    '--view', 'employee_offer_context',
    '--params', '{\"employee_id\": \"EMP001\"}',
    '--data-root', 'tenants'
], capture_output=True, text=True)
rows = json.loads(result.stdout)
assert len(rows) == 1, f'expected 1 row, got {len(rows)}'
row = rows[0]
# Currency fields must be display strings, not floats
assert row['basic_monthly'].startswith('₹'), \
    f'basic_monthly not a display string: {row[\"basic_monthly\"]}'
assert '37,500' in row['basic_monthly'], \
    f'basic_monthly value wrong: {row[\"basic_monthly\"]}'
assert row['net_take_home_monthly'].startswith('₹'), \
    f'net_take_home_monthly not a display string'
# All 18 OFFER_LETTER_REQUIRED fields present (minus date — caller-supplied)
required = {'candidate_name','candidate_email','candidate_phone',
    'candidate_address','role','title','annual_ctc','basic_monthly',
    'hra_monthly','lta_monthly','wfh_allowance_monthly','flexi_pay_monthly',
    'total_earnings_monthly','professional_tax_monthly','tds_monthly',
    'total_deductions_monthly','net_take_home_monthly','net_take_home_monthly'}
missing = required - row.keys()
assert not missing, f'missing fields: {missing}'
print('PASS — display-string currency correct, all required fields present')
print(json.dumps(row, indent=2, ensure_ascii=False))
"

# 4. Manifest is valid and references both views
python3 -c "
import json, pathlib
m = json.loads(pathlib.Path('tenants/bitloka/data/data_manifest.json').read_text())
view_names = [v['name'] for v in m['views']]
assert 'employee_offer_context' in view_names, 'employee_offer_context missing from manifest'
assert 'employee_payslip_context' in view_names, 'employee_payslip_context missing from manifest'
print(f'PASS — manifest has {len(view_names)} view(s): {view_names}')
"
```

**Claude-code prompt.**
> Read `agent-creation-guide.md` §"Scripts do; agents decide" and
> §"run_command has no stdin parameter" before writing any code.
> Read `CLAUDE.md` §Learning — m7-docbuilder.
>
> **Task:** write `docbuilder/scripts/query_tenant_data.py`, two DuckDB view
> files, and populate `data_manifest.json` per
> `docbuilder/docs/milestones/m-tenant-data-layer.md` §t2.
>
> **`query_tenant_data.py` interface:**
> ```
> python3 docbuilder/scripts/query_tenant_data.py \
>   --tenant {tenant_id} \
>   --view {view_name} \
>   --params '{json_string}' \
>   --data-root {path_to_tenants_dir}
> ```
> Returns a JSON array of row dicts to stdout. Exits non-zero with a clear
> error message to stderr on unknown view, missing params, or DuckDB error.
> Uses `import duckdb` (Python package, not CLI — D2).
>
> **View resolution:** the script reads `{data_root}/{tenant_id}/data/data_manifest.json`
> to find the `.sql` file for the requested view name, then executes it
> against the tenant's data files in `{data_root}/{tenant_id}/data/`.
> DuckDB reads the JSONL and CSV files directly — no Parquet step (D5
> deferred).
>
> **`employee_offer_context.sql`:** joins `employees` JSONL + `salary_structures`
> CSV on `employee_id`, filtered by `$employee_id` param. Returns all fields
> in the Context fields table in `m-tenant-data-layer.md`. Currency fields
> use `printf('₹%,.2f', CAST(amount AS DOUBLE))` — verify this produces
> `₹37,500.00` for `37500` before finalising (D4, CLAUDE.md learning).
>
> **`employee_payslip_context.sql`:** same sources, payslip projection
> (at minimum: `employee_id`, `candidate_name`, `role`, all monthly salary
> components with display-string currency). Exact field set is your
> implementation decision — document it in the implementation notes.
>
> **`data_manifest.json`:** populate the `views` array. Each entry:
> `{"name": "...", "description": "...", "sql_file": "views/....sql",
> "params": ["employee_id"], "returns": ["field1", "field2", ...]}`.
>
> **Tests** (`docbuilder/tests/test_query_tenant_data.py`):
> - Unit: unknown view name returns non-zero exit
> - Unit: missing required param returns non-zero exit
> - Integration (`@pytest.mark.integration`): `employee_offer_context` for
>   EMP001 returns 1 row with `basic_monthly == '₹37,500.00'`
> - Integration: all 17 substantive `OFFER_LETTER_REQUIRED` fields present
>   in the row (exclude `date` — caller-supplied)
>
> Run the done-check (verbatim from §t2) and include its full output at the
> top of the review packet. Write implementation notes to
> `docbuilder/docs/milestones/m-tenant-data-layer-t2-implementation-notes.md`
> and commit.

---

### t3 — `context_builder.exs` — tenant data query step

**Scope.** Extend `context_builder.exs` to query the tenant data layer when
the doc type is `offer_letter` (and, by the same mechanism, any doc type whose
schema has a corresponding view in the manifest). The LLM reads
`data_manifest.json`, selects the appropriate view, calls
`query_tenant_data.py` via `run_command`, and uses the returned rows to
populate the structured fields of `confirmed_context`. The `date` field
continues to be extracted from the NL request. The `title` field continues
to be supplied by the operator or defaulted. No change to `validate_fields.py`
or the orchestrator.

**Contract refs.**
- `agent-creation-guide.md` §"Be explicit about run_command format"
  (exact `command:` / `args:` format in the system prompt)
- `agent-creation-guide.md` §"Scripts do; agents decide"
- `CLAUDE.md` §Learning — m6-docbuilder (generic components stay generic;
  enrichment lives in the caller — the data query is caller-side enrichment)
- `CLAUDE.md` §Learning — m7-docbuilder (verify runtime shape before
  writing the command — confirm `query_tenant_data.py` arg convention
  matches what the system prompt instructs)
- Design decisions D6, D8 in this doc

**Touches.**
- `docbuilder/agents/context_builder.exs`
- `docbuilder/runbook.md` — update §"Tenant data layer" to note that
  `context_builder` reads the manifest and calls `query_tenant_data.py`
  when a matching view exists

**Do not generate.**
- Any change to `validate_fields.py`, `docbuilder_orchestrator.exs`, or
  any renderer script
- Any new view or data file (t2 is the data boundary)
- Any change to sprint cases (t4)

**Runbook update rule.** The runbook note is part of this ticket's Touches —
an operator debugging a context-builder run needs to know that a
`query_tenant_data.py` call may precede the field extraction step.

**Done-check.**
```bash
# From aetheris-agents/
# 1. context_builder.exs evaluates without error
cd ~/sandbox/elixirws/aetheris
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/context_builder.exs")' \
  2>/dev/null && echo 'PASS — context_builder.exs evaluates' || \
  echo 'FAIL — eval error'

# 2. Confirm data manifest is read and query_tenant_data is called
#    (grep the updated system prompt for the run_command instruction)
grep -c 'query_tenant_data' \
  ../aetheris-agents/docbuilder/agents/context_builder.exs
# Expected: ≥ 1

# 3. End-to-end context build via NL (no DOCBUILDER_CONTEXT inline JSON)
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Offer letter for Ajay Rao, date 1 July 2026" \
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/context_builder.exs")' \
  2>/dev/null

# Verify confirmed_context.json has display-string currency from the view
python3 -c "
import json, pathlib
ctx = json.loads(pathlib.Path(
    '../aetheris-agents/docbuilder/output/confirmed_context.json').read_text())
assert ctx.get('basic_monthly','').startswith('₹'), \
    f'basic_monthly not a display string: {ctx.get(\"basic_monthly\")}'
assert '37,500' in ctx.get('basic_monthly',''), \
    f'basic_monthly value wrong: {ctx.get(\"basic_monthly\")}'
assert ctx.get('candidate_name') == 'Ajay Rao', \
    f'candidate_name wrong: {ctx.get(\"candidate_name\")}'
print('PASS — confirmed_context has display-string currency from data layer')
print(f'  basic_monthly: {ctx[\"basic_monthly\"]}')
print(f'  net_take_home_monthly: {ctx[\"net_take_home_monthly\"]}')
"
```

**Claude-code prompt.**
> Read `agent-creation-guide.md` §"Be explicit about run_command format"
> and §"Scripts do; agents decide". Read `CLAUDE.md` §Learning — m6-docbuilder
> and §Learning — m7-docbuilder before editing.
>
> **Task:** extend `docbuilder/agents/context_builder.exs` so that when the
> doc type is `offer_letter` (or any doc type with a matching view in
> `data_manifest.json`), the LLM:
>
> 1. Calls `run_command` with:
>    ```
>    command: "python3"
>    args: ["docbuilder/scripts/query_tenant_data.py",
>           "--tenant", "{DOCBUILDER_TENANT}",
>           "--view", "employee_offer_context",
>           "--params", "{\"employee_id\": \"{extracted_id}\"}",
>           "--data-root", "tenants"]
>    ```
>    where `extracted_id` is resolved from the NL request (candidate name
>    lookup — the LLM reads the manifest to know which view to call and what
>    params are needed).
>
> 2. Uses the returned JSON rows to populate the structured fields of
>    `confirmed_context` (all salary components, employee contact fields).
>
> 3. Continues to extract `date` from the NL request as today.
>
> 4. Passes the populated context through `validate_fields.py` as before —
>    no change to the validation step.
>
> The system prompt must show the exact `run_command` format (per
> `agent-creation-guide.md`) — never a shell command string. Verify the
> `query_tenant_data.py` arg convention matches what you instruct before
> finalising the system prompt (CLAUDE.md m7 learning — check the actual
> CLI before writing the command).
>
> **Touches:** `context_builder.exs` only + the runbook one-liner.
> Do not touch `validate_fields.py`, the orchestrator, any renderer, or
> any sprint case.
>
> Run the done-check (verbatim from §t3) — the end-to-end context build
> (step 3) is the critical gate; include its full output. Write implementation
> notes to
> `docbuilder/docs/milestones/m-tenant-data-layer-t3-implementation-notes.md`
> and commit.

---

### t4 — Sprint case update + `docbuilder_offer_letter` NL path restoration

**Scope.** Update the `docbuilder_offer_letter` sprint case to use the live
NL path (DOCBUILDER_REQUEST → context_builder → data layer → orchestrator),
retiring the m7 t3 direct-context workaround. The sprint asserts that
`confirmed_context.json` has display-string currency sourced from the data
layer (not an inline JSON blob), and that both `.pdf` and `.docx` outputs
are produced. The direct-context blob (`DOCBUILDER_CONTEXT` inline JSON) is
removed from the sprint case. The existing assertions (zero `{{` in PDF,
candidate slug, `<table class="net">`, run log 0→1) are preserved.

**Contract refs.**
- `CLAUDE.md` §Learning — m6-docbuilder (end-to-end check beyond unit
  done-check)
- `CLAUDE.md` §Learning — m7-docbuilder (verify runtime shape before
  writing the sprint assertion)
- `docbuilder/runbook.md` §"Jinja2 templates (m6)" (offer-letter sprint
  conventions)
- Design decision D8 in this doc

**Touches.**
- `aetheris/scripts/sprint.sh` (`docbuilder_offer_letter` case block)
- `docbuilder/runbook.md` — update `docbuilder_offer_letter` entry to note
  the NL path is now live (direct-context workaround retired)

**Do not generate.**
- Any change to the template, bundle spec, or catalogue
- Any change to `context_builder.exs` (t3)
- Any other sprint case

**Runbook update rule.** The runbook `docbuilder_offer_letter` entry update
is part of this ticket's Touches — it documents the restoration of the NL
path and the retirement of the workaround introduced in m7 t3.

**Done-check.**
```bash
# From aetheris/ (harness repo)
cd ~/sandbox/elixirws/aetheris

# 1. Syntax check
bash -n scripts/sprint.sh && echo 'PASS — no syntax errors'

# 2. Confirm direct-context blob is gone from the offer_letter case
grep -c 'DOCBUILDER_CONTEXT=' scripts/sprint.sh
# Expected: 0 (or only in comments)

# 3. Live end-to-end NL run
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Offer letter for Ajay Rao dated 1 July 2026" \
./scripts/sprint.sh docbuilder_offer_letter

# 4. Verify confirmed_context currency is from data layer (not inline blob)
python3 -c "
import json, pathlib
ctx = json.loads(pathlib.Path(
    '../aetheris-agents/docbuilder/output/confirmed_context.json').read_text())
assert ctx.get('basic_monthly','').startswith('₹'), \
    'basic_monthly not a display string — data layer not used'
print(f'PASS — NL path live, display-string currency from data layer')
print(f'  basic_monthly: {ctx[\"basic_monthly\"]}')
"
```

**Claude-code prompt.**
> Read `CLAUDE.md` §Learning — m6-docbuilder and §Learning — m7-docbuilder.
> Read the current `docbuilder_offer_letter` case in `scripts/sprint.sh`
> before making any changes.
>
> **Task:** update the `docbuilder_offer_letter` sprint case to use the live
> NL path per `docbuilder/docs/milestones/m-tenant-data-layer.md` §t4.
>
> Specifically:
> 1. Replace the `DOCBUILDER_CONTEXT='...'` inline JSON blob with a
>    `DOCBUILDER_REQUEST` (NL string: "Offer letter for Ajay Rao dated
>    1 July 2026"). Remove `unset DOCBUILDER_CONTEXT_FILE` — the NL path
>    uses `DOCBUILDER_CONTEXT_FILE` (the `confirmed_context.json` written
>    by context_builder).
> 2. Add the context_builder step before the orchestrator step (the same
>    pattern as `docbuilder_context` sprint case).
> 3. Add an assertion that `confirmed_context.json` has `basic_monthly`
>    starting with `₹` — confirms the data layer is being used, not a
>    fallback inline blob.
> 4. Preserve all existing assertions: both `.pdf` and `.docx` in
>    `renamed.json`, zero `{{` in PDF, `₹` display string in PDF,
>    `<table class="net">` in rendered HTML, run log 0→1, candidate slug.
> 5. Update `docbuilder/runbook.md` `docbuilder_offer_letter` entry: note
>    that the NL path is now live and the direct-context workaround
>    (m7 t3) is retired.
>
> Verify the `DOCBUILDER_REQUEST` string is sufficient for the context
> builder to identify Ajay Rao in the data layer (the builder should
> resolve `candidate_name → employee_id → EMP001`). If the request needs
> to be more specific (e.g. include an explicit employee ID), adjust and
> note in the implementation notes.
>
> Run the done-check (verbatim from §t4) and include its full output.
> Write implementation notes to
> `docbuilder/docs/milestones/m-tenant-data-layer-t4-implementation-notes.md`
> and commit (aetheris repo for sprint.sh, aetheris-agents for runbook).

---

### t5 — Docs sync + milestone close

**Scope.** Close the milestone: drift check, review scan (t1–t4, all in
`docbuilder/docs/reviews/`), milestone summary, manifest advance for any
changed project-knowledge files, learning promotions if any finding recurs
on ≥2 tickets.

**Contract refs.**
- `milestone-methodology.md` §7 (milestone-end ritual)
- `docs/project-knowledge-manifest.md` (manifest format)
- `CLAUDE.md` §Learning format

**Touches.**
- `docbuilder/docs/milestones/m-tenant-data-layer.md` (milestone summary)
- `docs/project-knowledge-manifest.md` (hash updates for changed files)
- `CLAUDE.md` §Learning (new entry only if recurring findings)
- `docbuilder/docs/milestones/m-tenant-data-layer-t5-implementation-notes.md`

**Done-check.**
```bash
# From aetheris-agents/
python3 scripts/drift_check.py
# Expected: N PASS / 0 FAIL / 0 WARN (or 1 WARN if CLAUDE.md updated —
# clears after BL-002 re-upload)

grep -c '## Milestone summary' \
  docbuilder/docs/milestones/m-tenant-data-layer.md
# Expected: 1
```

**Claude-code prompt.**
> Read `milestone-methodology.md` §7 and `docs/project-knowledge-manifest.md`.
>
> **Task (milestone-end ritual):**
> 1. Run `python3 scripts/drift_check.py`. Report the result. Stop if FAIL.
> 2. Scan `docbuilder/docs/reviews/m-tenant-data-layer-t{1..4}-review.md`
>    for findings recurring on ≥2 tickets. Draft a `CLAUDE.md` learning entry
>    for each. If none recur, note "No recurring findings in m-tenant-data-layer".
> 3. Append `## Milestone summary` to
>    `docbuilder/docs/milestones/m-tenant-data-layer.md` (what shipped, what
>    was deferred with → backlog ref, surprises, open items for next milestone).
> 4. Update `docs/project-knowledge-manifest.md`: bump hash for any
>    manifest-tracked file changed in this milestone. Run
>    `git log -1 --format=%h -- <path>` per file. `tenants/` is not
>    manifest-tracked; check `CLAUDE.md` and `docbuilder/runbook.md`
>    (the latter is not tracked — confirm before updating).
>
> Run the done-check and include its full output. Write implementation notes
> to `docbuilder/docs/milestones/m-tenant-data-layer-t5-implementation-notes.md`
> and commit.

---

## Ticket order

t1 → t2 → t3 → t4 → t5.

t1 and t2 are independent of pipeline code and can be reviewed quickly.
t3 depends on t2 (needs `query_tenant_data.py` to exist for the eval check).
t4 depends on t3 (needs the data-layer context_builder path to be live).
t5 depends on all four review files.

---

## File locations

```
docbuilder/docs/milestones/m-tenant-data-layer.md              ← this doc
docbuilder/docs/milestones/m-tenant-data-layer-t{1-5}-implementation-notes.md
docbuilder/docs/reviews/m-tenant-data-layer-t{1-4}-review.md
```

---

## Open questions for claude-code (resolve in the relevant ticket)

| # | Question | Ticket | Notes |
|---|----------|--------|-------|
| Q1 | Does `duckdb` Python package need to be added to `requirements.txt`? | t2 | Verify `pip show duckdb` on the dev machine; if absent, add to `docbuilder/requirements.txt` |
| Q2 | Does `printf('₹%,.2f', ...)` in DuckDB produce `₹37,500.00` exactly? | t2 | Run standalone before finalising the view — CLAUDE.md m7 learning applies |
| Q3 | How does the context builder identify `employee_id` from a name in the NL request? | t3 | Options: (a) LLM queries a `employee_name_lookup` view first; (b) the NL request is expected to include the employee ID; (c) `query_tenant_data.py` supports a `candidate_name` param that the view resolves to `employee_id`. Decide in t3 and record in implementation notes. |
| Q4 | Does `DOCBUILDER_REQUEST = "Offer letter for Ajay Rao dated 1 July 2026"` give the context builder enough to resolve to EMP001? | t4 | May need a slightly richer request; adjust in t4 and note the minimum required NL form in the runbook. |

---

_Committed 2026-07-02 (Phase 1 → 2) at base `cacbff3`. Approved by operator ("commit the
milestone doc"). Open questions Q1–Q4 are deliberately deferred to their tickets (t2/t3/t4);
`Base commit: TBD` filled to the post-m7 HEAD._
