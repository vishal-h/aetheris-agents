# Review — m-docbuilder-m2b t5 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design"; aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/drive-structure.md; drive/scripts/drive_upload.py (reference pattern)

---

## Packet assessment

Ticket ID + scope: ✅ provided
Done-check output: ✅ opens packet — 4/4 unit tests (-m "not integration"), 195/195 + 2 skipped full suite (both Drive integration tests correctly skipped without creds)
Diff: ✅ included (4 files, 271 insertions, 0 deletions — pure addition)
Implementation notes: ✅ committed — update-in-place decision, mocked testing approach, "done-check has real tests" rationale, forward notes

---

## Findings (all non-blocking)

1. `find_or_create_folder` doesn't enforce RW scope itself — caller responsibility;
   `upload_outputs` correctly passes `RW_SCOPE`. Consistent with the `_drive.py` design
   (caller picks the scope). ✅

2. `upload_file` is read-then-write (find_child → update/create), not atomic. Race only
   matters for concurrent same-filename uploads — unreachable for a single-tenant,
   single-run pipeline. Worth noting for m3 if concurrent runs are introduced.

3. The mocked `test_upload_outputs_mocked` verifies the full folder chain
   (ROOT → tenant → output) and that uploads target the output folder — complete
   navigation verification. ✅

4. `drive_url` returns a `/view` link — correct for the email review-and-forward pattern
   (the ops team opens it to review before forwarding). A future need for `/edit`/export
   links would add an optional `mode`. No action for m2b.

---

## Cross-ticket notes

- **`_drive.py` write surface confirmed:** `find_or_create_folder` + `upload_file` +
  `drive_url` added to the shared helper (not inline), per the t2 review F-note. The
  helper now covers read + write + navigate for t2/t5/t7.
- **t6:** the `{filename, drive_url}` list from `uploaded.json` is the input to
  `email_send_review.py --drive-links`; the `/view` URL is what belongs in the email body.
- **t7 PHASE E confirmed:** `upload_output.py --tenant {tenant} --files {renamed} --output
  output/uploaded.json` (scratch-0 pattern).
- **t8:** `_drive.py` + `upload_output.py` need capability-matrix entries;
  `google-api-python-client` → `requirements.txt`. (Already recorded in the t8 ticket.)

---

**Outcome: zero blocking findings. t5 clear to merge. t6 clear to start.**
All four findings are confirmations — no action required.
