# provenance/m2: Review tooling

## Context

After classification runs, a human operator reviews proposed classifications
before any files are moved. This milestone provides two scripts:
1. Export proposed classifications to a CSV for review
2. Import the reviewed CSV back to DuckDB, recording approvals and rejections

The review workflow is intentionally offline — export to CSV, review in Excel
or any spreadsheet tool, import the decisions back. No web UI required.

## What to build

### `scripts/export_for_review.py`

Exports classifications for human review.

**CLI:**
```
python3 scripts/export_for_review.py \
  --db /data/corpus.duckdb \
  --out output/review_{timestamp}.csv \
  [--status proposed,needs_review] \
  [--client acme] \
  [--limit 500]
```

**Output columns:**
```
path, client, financial_year, doc_type, confidence, status,
raw_excerpt (truncated to 200 chars), classified_at,
reviewer_action (blank — filled by human), reviewer_notes (blank)
```

**Behaviour:**
- Default: exports `proposed` + `needs_review` classifications
- `--status` filters by one or more statuses (comma-separated)
- `--client` filters to one client
- `--limit` caps export size (default: no limit)
- Prints output path to stdout
- Exits 0 on success

**Summary printed to stdout after the path:**
```
{"output": "output/review_20260115_091230.csv", "exported": 1247, "needs_review": 89}
```

### `scripts/approve_classifications.py`

Imports the reviewed CSV and updates the `classifications` table.

**CLI:**
```
python3 scripts/approve_classifications.py \
  --db /data/corpus.duckdb \
  --input output/review_20260115_091230.csv \
  [--reviewer "Jane Smith"] \
  [--dry-run]
```

**Expected CSV columns:** same as export, with `reviewer_action` filled in:
- `approve` — set `status = 'approved'`, record `reviewed_by` and `reviewed_at`
- `reject` — set `status = 'rejected'`, record `reviewed_by` and `reviewed_at`
- blank / anything else — leave unchanged (skip)

**`--dry-run`:** prints what would change without writing to DB.

**Output JSON to stdout:**
```json
{"approved": 1158, "rejected": 89, "skipped": 0, "errors": 0}
```

**Validation:**
- Reject rows where `reviewer_action` is not blank, `approve`, or `reject`
- Warn (not error) if a path in the CSV is not found in `classifications`
- Exits 0 even if some rows are skipped; exits 1 only on DB or parse errors

## Acceptance criteria

**export_for_review.py:**
- [ ] Exports correct columns to CSV
- [ ] `--status`, `--client`, `--limit` filters work
- [ ] Summary JSON printed to stdout after output path
- [ ] Exits 0 on success
- [ ] `pytest tests/test_review_tooling.py::test_export_*` passes

**approve_classifications.py:**
- [ ] `approve` rows update `status`, `reviewed_by`, `reviewed_at`
- [ ] `reject` rows update `status`, `reviewed_by`, `reviewed_at`
- [ ] Blank `reviewer_action` rows are skipped
- [ ] `--dry-run` prints changes without writing
- [ ] Output JSON counts are correct
- [ ] Idempotent — re-importing the same CSV is a no-op
- [ ] `pytest tests/test_review_tooling.py::test_approve_*` passes

**Workflow test:**
- [ ] Export → edit CSV (approve some, reject some, leave some blank) →
  import → verify DB state matches CSV decisions

## Files to create

- `provenance/scripts/export_for_review.py`
- `provenance/scripts/approve_classifications.py`
- `provenance/tests/test_review_tooling.py`

## Notes

**Reviewer identity.** `--reviewer` defaults to `$USER` env var if not provided.
This is informal — it's for the audit log, not access control.

**Large corpora.** For corpora with >10K classifications, the default export
with no `--limit` produces a large CSV. Recommend exporting by client:
```bash
for client in acme globex initech; do
  python3 scripts/export_for_review.py --db corpus.duckdb --client $client \
    --out output/review_${client}.csv
done
```
Document this pattern in `runbook.md`.

**`needs_review` first.** The export should order rows by `confidence ASC`
so low-confidence results appear at the top of the spreadsheet where reviewers
are most likely to catch problems.

**Rejection handling.** Rejected classifications are not deleted — they remain
in the `classifications` table with `status = 'rejected'`. This preserves the
audit trail. The orchestrator's unclassified file query excludes rejected paths,
so rejected files will be re-classified if the orchestrator is re-run (with an
updated taxonomy, for example).

Add `export_for_review.py` and `approve_classifications.py` usage to
`docs/provenance/runbook.md` under a new "Classification review" section.
