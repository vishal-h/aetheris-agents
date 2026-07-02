# Implementation notes — m-tenant-data-layer t1 (`tenants/` dir + data files + .gitignore)

Ticket: introduce the top-level `tenants/` directory and the `tenants/bitloka/data/` structure
(sample fixtures, `.gitignore`, empty `views/`, manifest skeleton) + a runbook §"Tenant data
layer". No pipeline code (t2+).

---

## What shipped

- **`tenants/`** — new top-level directory in `aetheris-agents/` (D1).
- **`tenants/bitloka/data/.gitignore`** — `/*.jsonl` + `/*.csv`, **anchored with a leading `/`**
  so it ignores the real files at the `data/` root (`employees.jsonl`, `salary_structures.csv`)
  but NOT the deeper `sample/` copies (D7). Verified functionally (see done-check).
- **`sample/employees_sample.jsonl`** — one record, `EMP001` / Ajay Rao, with all 7 required
  identity fields (`employee_id`, `candidate_name`, `candidate_email`, `candidate_phone`,
  `candidate_address`, `role`, `title`) + the optional fields (`internship_acknowledgement`,
  `business_/individual_performance_bonus_pct`/`_period`) so the full conditional path is
  exercisable from the sample.
- **`sample/salary_structures_sample.csv`** — long format `employee_id,component,amount`, 11 rows
  for EMP001 (`annual_ctc` 900000, `basic_monthly` 37500 … `net_take_home_monthly` 67300).
  **Amounts are numeric** — no `₹` display strings (D4; formatting is the t2 view's job).
  Component names are the field-base names, so the t2 view can pivot component→field directly.
- **`views/.gitkeep`** — empty dir marker (views land in t2).
- **`data_manifest.json`** — skeleton `{"tenant_id": "bitloka", "views": []}` (populated in t2).
- **`docbuilder/runbook.md`** — new §"Tenant data layer": canonical location, the anchored
  gitignore convention, how to add a real data file, and the D-Drive deferred note.

## Done-check

1. Directory structure — **PASS**.
2. Sample data valid — **PASS** (1 employee record, all required fields; 11 salary rows, `amount`
   numeric).
3. `.gitignore` excludes real data — **PASS (functionally verified)**. See the command-shape note
   below: the doc's `grep -q '*.jsonl'` errors under this box's grep, so I verified the *behaviour*
   instead with `git check-ignore`:
   - `tenants/bitloka/data/employees.jsonl` → **IGNORED**
   - `tenants/bitloka/data/salary_structures.csv` → **IGNORED**
   - `tenants/bitloka/data/sample/employees_sample.jsonl` → **TRACKED**
   - `tenants/bitloka/data/sample/salary_structures_sample.csv` → **TRACKED**
   - `git add -n tenants/` lists only the 5 intended files (gitignore, manifest, 2 samples,
     `.gitkeep`) — no real data files.
4. Runbook §"Tenant data layer" present — **PASS**.

## Done-check command correction (command-shape class — CLAUDE.md m7 learning)

The §t1 done-check step 3 uses `grep -q '*.jsonl' …`. On this machine `grep` is **ugrep**, which
parses `*.jsonl` as a **regex** — a leading `*` is "empty (sub)expression" → the command *errors*
(neither matches nor cleanly fails). It assumes GNU grep, where a leading `*` is a literal. This
is precisely the recurring "command written against an assumed runtime shape, not a verified one"
pattern (`## Learning — m7-docbuilder`). **Corrected form:** `grep -qF '*.jsonl'` (`-F` =
fixed-string, engine-independent) — passes. But the *authoritative* check for a `.gitignore` is
`git check-ignore` (behaviour, not file contents), which I used above. Recorded for t5's docs pass
if the §t1 block is referenced again; it's another instance for the command-shape learning.

## Scope held

Only the `tenants/bitloka/data/` assets + the runbook section. No `.sql` views, no
`query_tenant_data.py`, no `context_builder.exs`/sprint changes (t2+).
