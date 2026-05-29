# provenance/m4: extract_zip.py

## Context

The first step of zip archaeology is pure extraction: open a zip file, detect
if it's encrypted, extract its contents to a staging directory, and return a
manifest describing what was found. No DuckDB interaction, no hashing — this
script does one thing and is independently testable.

## What to build

`scripts/extract_zip.py`

### Behaviour

1. Open the zip file at `--zip`
2. If encrypted: do not extract, return manifest with `status = 'encrypted'`
3. Extract all contents to `--staging-dir/{zip_basename}/`
4. For each extracted entry, note whether it is itself a zip (nested)
5. Return manifest JSON to stdout
6. Delete the staging directory on failure (clean up partial extractions)

### Output manifest

```json
{
  "zip_path":      "/data/archive/acme/archive_2022.zip",
  "status":        "extracted",
  "staging_dir":   "/path/to/staging/archive_2022/",
  "file_count":    47,
  "files": [
    {
      "internal_path": "acme/FY2024/tax_return.pdf",
      "staging_path":  "/path/to/staging/archive_2022/acme/FY2024/tax_return.pdf",
      "size_bytes":    1200000
    },
    ...
  ],
  "nested_zips": [
    {
      "internal_path": "old_archive/backup_2021.zip",
      "staging_path":  "/path/to/staging/archive_2022/old_archive/backup_2021.zip"
    }
  ],
  "error": null
}
```

For encrypted zips:
```json
{
  "zip_path": "/data/archive/acme/confidential.zip",
  "status":   "encrypted",
  "staging_dir": null,
  "file_count": 0,
  "files": [],
  "nested_zips": [],
  "error": "zip is password-protected"
}
```

For failed extractions (corrupt zip, permission error, etc.):
```json
{
  "zip_path": "...",
  "status":   "failed",
  "error":    "BadZipFile: File is not a zip file"
}
```

### CLI

```
python3 scripts/extract_zip.py \
  --zip /data/archive/acme/archive_2022.zip \
  --staging-dir /tmp/provenance_staging/extractions
```

Exits 0 always — encrypted and failed zips are reported in the manifest, not
as process errors. The caller decides how to handle each status.

### Depth guard

Accept a `--depth N` argument (default 0, max 4). If `--depth` equals or
exceeds the maximum, return `status = 'max_depth'` without extracting.
The orchestrator passes the current depth when calling this script.

### Large zip handling

Extraction uses Python's `zipfile` module with streaming (`ZipFile.open` +
`shutil.copyfileobj`) for files above 100MB. Do not load entire members into
memory.

## Acceptance criteria

- [ ] Extracts all files from a real zip to the staging directory
- [ ] Returns correct manifest with all fields
- [ ] Detects encrypted zip — returns `status = 'encrypted'`, no files extracted
- [ ] Detects nested zips — listed in `nested_zips`
- [ ] Returns `status = 'max_depth'` when depth limit exceeded
- [ ] Cleans up partial extraction on failure
- [ ] Exits 0 in all cases (error reported in manifest JSON, not exit code)
- [ ] `pytest tests/test_extract_zip.py` — 8+ tests pass, all using real zip files

## Files to create

- `provenance/scripts/extract_zip.py`
- `provenance/tests/test_extract_zip.py`

## Notes

**Test fixtures.** Tests must create real zip files using Python's `zipfile`
module rather than committing binary `.zip` fixtures. This keeps the repo clean
and makes test data self-documenting. Use `tmp_path` for all zip creation and
extraction.

**Encrypted zip detection.** Python's `zipfile` module does not natively
distinguish encrypted zips before extraction — it raises `RuntimeError:
'File ... is encrypted, password required for extraction'` on the first
member extraction attempt. Catch this and return `status = 'encrypted'`.
Alternatively, check the member's `flag_bits` for bit 0 (encryption flag)
without extracting.

**Internal path safety.** Zip files can contain members with path traversal
components (`../../etc/passwd`). Extract using `ZipFile.extractall()` with a
`members` filter, or manually construct each destination path and verify it is
within the staging directory before writing.
