# Implementation notes — m-docbuilder-m2b t4

Ticket: `rename_output.py` — rename run outputs to the deliverable convention.

---

## What shipped

- `scripts/rename_output.py` (new): `--output-dir`, `--filename-prefix`, `--context`
  (inline JSON), `--output FILE`. Finds `{prefix}.{ext}` for the known render exts
  (xlsx, docx, pdf, csv, json, xml, md), renames each to
  `{client_name_slug}_{doc_type}_{date}.{ext}`, prints a JSON array of
  `{original, renamed}` path pairs. Exit 1 if `client_name` or `date` is missing.
- `tests/test_rename_output.py` (new): 15 tests.
- Full suite: 191 passed, 1 skipped.

---

## Decisions

**Return path strings, not bare basenames.** Each pair is
`{"original": "output/proposal_v1.xlsx", "renamed": "output/acme_corp_proposal_2026-06-20.xlsx"}`
— full (output-dir-joined) paths so the t7 orchestrator can pass `renamed` straight to
`upload_output.py --files` without re-joining.

**`doc_type` fallback strips the `_v{N}` version.** When context omits `doc_type`,
`doc_type_base(filename_prefix)` removes a trailing `_v\d+` (`proposal_v1` → `proposal`),
matching the prompt's "(e.g. `proposal`)". A prefix without a version is used unchanged.

**Date is filename-sanitised (`safe_segment`), a small deviation from literal `{date}`.**
The context schema allows a display date like `"20 Jun 2026"`, which would otherwise put
spaces in the filename. `safe_segment` collapses whitespace to `_` and strips anything but
`[A-Za-z0-9_.-]`, so `"20 Jun 2026"` → `20_Jun_2026` and ISO `"2026-06-20"` is unchanged.
`client_name` uses the stricter `slugify` (lowercase + `[a-z0-9_-]`) per the schema.

**Intermediates are never matched.** The match is exactly `{prefix}.{ext}`, so
`pipeline_raw_*.json` / `pipeline_spec.json` (which don't start with the doc prefix) are
untouched — covered by `test_non_matching_files_untouched`.

**No-match is not an error.** If nothing matches the prefix, returns `[]` and exits 0
(rename's job is to rename what's there; an empty run is an upstream concern).

## Forward notes

- **t5 (`upload_output.py`):** consumes the `renamed` paths from this script's JSON.
- **t7 (orchestrator PHASE D):** `rename_output.py --output-dir output --filename-prefix
  {doc_type}_{variant} --context '{...}' --output output/renamed.json`; then PHASE E reads
  `renamed.json` for the files to upload. (`--output` is here for that, consistent with the
  m2b scratch-0 pattern.)
