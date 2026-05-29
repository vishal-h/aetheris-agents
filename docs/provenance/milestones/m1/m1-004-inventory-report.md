# provenance/m1: Inventory report

## Context

After the scan completes, stakeholders need a clear, human-readable report
before any classification or migration work begins. This is the gate between
Phase 1 and Phase 2 — the report must be reviewed and approved before proceeding.

## What to build

`scripts/inventory_report.py` — queries DuckDB and produces a Markdown report.

**Report sections:**

### Summary
- Total files scanned
- Unique files (by SHA-256)
- Duplicate files (count and wasted space)
- Total storage size / unique content size
- Scan duration and timestamp

### By file type
Table: MIME type | file count | total size | % of corpus

### Estimated FY distribution
Table: Year (from modified_at) | file count | size
Note: this is an estimate from filesystem dates, not document content.

### Duplicate groups (top 20 by wasted space)
Table: SHA-256 (truncated) | copy count | size each | total wasted | sample paths

### Zip files
- Total zip files found
- Estimated total contents (based on zip metadata if available)
- Largest zips (top 10)

### What's next
Boilerplate section explaining Phase 2 classification and the review process.

**CLI:**
```
python3 scripts/inventory_report.py --db /data/corpus.duckdb --out /data/reports/inventory_{timestamp}.md
```

Prints report path to stdout on completion.

## Acceptance criteria

- [ ] Script runs against a populated DuckDB and produces a valid Markdown file
- [ ] All sections present and populated with real data
- [ ] Duplicate groups section shows correct wasted space calculation
- [ ] Report is readable by a non-technical stakeholder
- [ ] `pytest tests/test_inventory_report.py` passes against a fixture DuckDB
- [ ] Output path includes timestamp (no overwrite risk)

## Files to create

- `aetheris-agents/provenance/scripts/inventory_report.py`
- `aetheris-agents/provenance/tests/test_inventory_report.py`
- `aetheris-agents/provenance/tests/fixtures/sample_corpus.duckdb` (small fixture DB)

## Notes

The report is the first thing the auditing firm will see. It must be clear and
professional. Use human-readable sizes (GB, MB — not raw bytes). Use plain
Markdown tables with no embedded code or technical jargon.

The "Estimated FY distribution" section should note clearly that dates are from
filesystem metadata, not document content — actual FY breakdown comes in Phase 2.

The fixture DuckDB should have enough data to exercise all report sections:
at least 3 MIME types, 5+ duplicate groups, 2+ zip files.
