# provenance/m4: process_zip_finds.py

## Context

After extraction, we need to know what the zip actually contained relative to
the existing corpus: which files are already known (duplicates of something in
`f2_file_index`) and which are genuinely new. New finds are preserved in a
content-addressed staging layout and registered in `f2_file_index` so the
existing classification and migration pipeline can pick them up.

## What to build

`scripts/process_zip_finds.py`

### Input

Takes the manifest JSON from `extract_zip.py` via `--manifest` or stdin, plus
`--db` and `--staging-path`.

```
python3 scripts/process_zip_finds.py \
  --db /data/corpus.duckdb \
  --manifest /tmp/extract_manifest.json \
  --staging-path priv/zip_staging
```

### Behaviour per extracted file

1. Compute SHA-256 of the extracted file
2. Check `f2_file_index` for that hash
3. **Known (hash in corpus):** insert `zip_contents` row with
   `corpus_match = matching_path`, `status = 'known'`. Delete the extracted file.
4. **New to corpus:** copy to permanent staging at
   `{staging_path}/new_finds/{sha256[:2]}/{sha256}/{original_filename}`.
   Insert into `f2_file_index` with the permanent staging path.
   Insert `zip_contents` row with `corpus_match = null`, `status = 'new'`.
5. Update `zip_inventory` row for this zip: set `contents_count`, `new_to_corpus`
   count, `status = 'processed'`, `processed_at = now()`.
6. Delete the raw extraction directory (`staging_dir` from manifest) after
   all files are processed.

### Output JSON to stdout

```json
{
  "zip_path":       "/data/archive/acme/archive_2022.zip",
  "total_files":    47,
  "known":          43,
  "new_to_corpus":  4,
  "nested_zips":    1,
  "new_finds": [
    {
      "staging_path":   "priv/zip_staging/new_finds/ab/abcd1234.../letter.docx",
      "internal_path":  "acme/FY2022/letter.docx",
      "sha256":         "abcd1234..."
    }
  ]
}
```

### DuckDB writes

**`zip_inventory`** — upsert on `path`:
```sql
INSERT INTO zip_inventory (path, size_bytes, depth, status, contents_count,
                           new_to_corpus, processed_at)
VALUES (...)
ON CONFLICT (path) DO UPDATE SET
    status = 'processed', contents_count = ..., new_to_corpus = ..., processed_at = now()
```

**`zip_contents`** — one row per extracted file:
```sql
INSERT INTO zip_contents (id, zip_path, internal_path, sha256, size_bytes,
                          corpus_match, status)
VALUES (...)
```

**`f2_file_index`** — one row per new-to-corpus file:
```sql
INSERT INTO f2_file_index (path, size_bytes, sha256, mime_type, status, last_scanned)
VALUES (staging_path, ...)
ON CONFLICT (path) DO NOTHING
```

`mime_type` for new finds: use `mime_guess` on the filename (same as the scanner).

### Idempotent behaviour

If a `zip_contents` row already exists for `(zip_path, internal_path)`, skip
that file. If `zip_inventory` already shows `status = 'processed'` for this
zip, skip the whole zip and return counts from existing DB rows.

## Acceptance criteria

- [ ] Correctly identifies known vs new-to-corpus files by SHA-256
- [ ] Known files: `zip_contents` row with `corpus_match`, extracted file deleted
- [ ] New files: copied to `new_finds/` layout, added to `f2_file_index`, `zip_contents` row
- [ ] `zip_inventory` updated with correct counts and `status = 'processed'`
- [ ] Raw extraction directory deleted after processing
- [ ] Idempotent — second run on same zip is a no-op
- [ ] Output JSON correct in all cases
- [ ] `pytest tests/test_process_zip_finds.py` — 10+ tests pass
- [ ] Tests use `sample_corpus.duckdb` fixture + real zip files created with `zipfile`

## Files to create

- `provenance/scripts/process_zip_finds.py`
- `provenance/tests/test_process_zip_finds.py`

## Notes

**Content-addressed layout.** `new_finds/{sha256[:2]}/{sha256}/{filename}` is the
same scheme used by git object storage. The two-character prefix avoids
filesystem directory size limits on large corpora. The sha256 subdirectory
ensures collision-free storage even if two zips contain files with the same name.

**Filename for new finds.** Use the `internal_path` basename from the zip.
If two files in the same zip have the same basename but different hashes,
the second gets `{basename}_{sha256[:8]}.{ext}`.

**`f2_file_index` path for new finds is the staging path.** When these files
go through classification and migration, the migration agent copies from the
staging path to `/clients/`. After migration, `status` in `f2_file_index` is
updated to `ok` (the staging path entry remains — it's the source of truth
until the file is in `/clients/`).

**Nested zips in the manifest** are reported in the output JSON but not
processed here — that's the orchestrator's responsibility (recursive pass).
They should be added to `zip_inventory` with `status = 'pending'` so the
orchestrator can find them.
