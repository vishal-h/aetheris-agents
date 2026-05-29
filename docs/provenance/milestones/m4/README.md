# m4 — Zip Archaeology

**Goal:** Nothing important is buried in zip files.

The original corpus contains years of panic backups — zips of zips, partial
archives, indiscriminate compression applied at every level. This milestone
processes every zip file in the corpus, identifies what's inside, and surfaces
new-to-corpus documents into the classification and migration pipeline.

No source files are deleted. Original zips in `/archive/` are read-only.

---

## Issues

| # | Issue | Depends on | Description |
|---|-------|-----------|-------------|
| 001 | [extract_zip.py](m4-001-extract-zip.md) | — | Extract one zip to staging, detect encrypted, return manifest |
| 002 | [process_zip_finds.py](m4-002-process-zip-finds.md) | 001 | Hash extracted files, compare against corpus, update zip_inventory + zip_contents, register new finds in f2_file_index |
| 003 | [zip_archaeologist agent](m4-003-zip-archaeologist.md) | 001, 002 | Sub-agent that processes one zip end-to-end using both scripts |
| 004 | [zip orchestrator](m4-004-zip-orchestrator.md) | 003 | Orchestrator that spawns archaeologists, handles nested zips in passes, escalates encrypted zips |

**001 and 002** are independent and can run in parallel.
**003** depends on both. **004** depends on 003.

---

## Completion gate

- Human reviews new-to-corpus findings report — confirms nothing unexpected
- Encrypted zip list reviewed — passwords sourced from appropriate staff
- `zip_inventory` table shows `status = 'processed'` for all non-encrypted zips
- Re-running the orchestrator reports all zips already processed (idempotent)
- New-to-corpus files visible in `f2_file_index` and queued for classification

---

## Key design decisions

**Extract to permanent staging, not temp.** New-to-corpus files extracted from
zips need to persist long enough to be classified and migrated. They are stored
at `{STAGING_PATH}/new_finds/{sha256[:2]}/{sha256}/{filename}` — a
content-addressable layout that avoids filename collisions. `STAGING_PATH`
defaults to `priv/zip_staging/` relative to the Provenance root.

**New-to-corpus files flow through the existing pipeline.** After archaeology,
their staging paths are inserted into `f2_file_index`. The m2 classification
orchestrator picks them up on its next run. The m3 migration agent copies them
to `/clients/`. No new pipeline needed.

**Multi-pass for nested zips.** The orchestrator runs passes until no new
nested zips are discovered, up to `MAX_DEPTH` (default 4). Each pass spawns
archaeologists for the zips discovered in the previous pass.

**Encrypted zips escalate once, at the end.** Individual archaeologist agents
do not escalate per encrypted zip. They log `status = 'encrypted'` to
`zip_inventory` and continue. The orchestrator collects all encrypted zips after
each pass and presents them in a single escalation to the human.

**Temporary extraction cleaned up, new finds kept.** After `process_zip_finds.py`
runs, the raw extraction directory is deleted. Only the content-addressed
`new_finds/` entries survive. If a file was already in the corpus, its
extraction is discarded immediately.

---

## Reference

- DuckDB schema (zip_inventory, zip_contents): `docs/provenance/specs.md`
- Architecture: `docs/provenance/architecture.md`
- CLAUDE.md: `CLAUDE.md`
