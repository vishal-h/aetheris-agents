# Implementation notes — m-docbuilder-m2b t5

Ticket: `upload_output.py` — upload run outputs to the tenant's Drive output folder.

---

## What shipped

- `scripts/upload_output.py` (new): `--tenant`, `--files` (one+), `--drive-id`
  (falls back to `DRIVE_DOCBUILDER_ID`), `--output FILE`. Resolves `{tenant}/output/`
  under the Shared Drive root (creating both folders if absent), uploads each file,
  prints a JSON array of `{filename, drive_file_id, drive_url}`. Exit 1 if no Drive id
  or any upload fails.
- `scripts/_drive.py` (update): added `find_or_create_folder`, `upload_file`
  (update-in-place), and `drive_url` — the Drive plumbing lives in the shared helper
  (per the t2 review), not inline in `upload_output.py`.
- `tests/test_upload_output.py` (new): 4 unit (mocked, no creds) + 1 integration (skipped
  without `DRIVE_DOCBUILDER_ID`).
- Full suite: 195 passed, 2 skipped.

---

## Decisions

**Drive plumbing added to `_drive.py`, not inline (t2 review F-note).** `find_or_create_folder`
+ `upload_file` + `drive_url` join the shared helper alongside the t2 read helpers.
`upload_file` uses **update-in-place** (files.update when a same-named file exists,
files.create otherwise) so re-running a sprint doesn't create Drive duplicates — same
behaviour as `drive/scripts/drive_upload.py`. MIME type via `mimetypes.guess_type`
(covers xlsx/docx/pdf; octet-stream fallback), broader than drive_upload's pdf/csv map.

**`upload_outputs()` factored for mocked unit testing.** The orchestration (resolve
`{tenant}/output/`, upload each, build the JSON) is a pure function over the `_drive`
helpers, so the unit tests monkeypatch `_drive.build_service`/`find_or_create_folder`/
`upload_file` and assert the navigation order (ROOT → tenant → output) and JSON shape
without any creds or network. The real round-trip is the `@pytest.mark.integration` test,
skipped when `DRIVE_DOCBUILDER_ID` is absent.

**Done-check `-m "not integration"` has real tests to run.** Because all-integration
would make `-m "not integration"` collect nothing (pytest exit 5), I included
non-integration unit tests (URL helper, mocked upload, missing-file, no-drive-id CLI) —
4 run under the done-check filter; the 1 integration test is deselected.

**`--output FILE`** for the t7 orchestrator (write `uploaded.json`, print only the path) —
consistent with the m2b scratch-0 pattern.

## Forward notes

- **t6 (`email_send_review.py`):** consumes the `{filename, drive_url}` list (its
  `--drive-links` arg).
- **t7 (orchestrator):** PHASE E `upload_output.py --tenant {tenant} --files {renamed}
  --output output/uploaded.json`; PHASE F `email_send_review.py --drive-links <uploaded.json>`.
- **t8:** `_drive.py` (shared helper) + `upload_output.py` in the capability matrix;
  `google-api-python-client` to `requirements.txt`.
