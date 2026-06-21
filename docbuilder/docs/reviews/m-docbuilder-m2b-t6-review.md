# Review — m-docbuilder-m2b t6 — round 1

Reviewer: claude-ui
Contract refs: milestone-methodology.md §5, §6; agent-creation-guide.md §"Script design" (Python package naming — email/ stdlib collision warning); aetheris-agents--CLAUDE.md §"Implementation notes"; docbuilder/docs/context-schema.md (required fields: client_name, client_email, date); email/scripts/email_send.py (SMTP pattern reference)

---

## Packet assessment

Ticket ID + scope: ✅ provided — mid-ticket simplification (links-only) flagged upfront and applied across code, tests, milestone prompt, and notes
Done-check output: ✅ opens packet — 7/7 unit tests (-m "not integration"), 202/202 + 3 skipped full suite (all three integration tests skipped without creds)
Diff: ✅ included (4 files, 285 insertions, 10 deletions)
Implementation notes: ✅ committed — links-only rationale, pure-helpers testing, validation order, review-alias design, forward notes

---

## Findings (all non-blocking)

1. `from email.mime.text import MIMEText` is in `docbuilder/scripts/`, not `email/scripts/`;
   the docbuilder conftest inserts `docbuilder/scripts/` into `sys.path`, so this resolves
   to the stdlib `email` package — no collision (the `agent-creation-guide.md` email/
   collision warning applies to the `email/` use-case dir, not here). ✅

2. `smtp_config()` calls `sys.exit(1)` directly (not unit-testable without a subprocess);
   the `test_cli_missing_review_email_exits_1` path uses subprocess. `send_review()` has
   `except SystemExit: raise` so `smtp_config()`'s exit propagates cleanly through `main()`.
   Correct pattern; subprocess coverage adequate.

3. `--drive-links` defaults to `"[]"` → a `(none)` links block if upload was skipped.
   Graceful degradation; covered by `test_build_body_no_links`. ✅

4. The scope simplification (attachments → links-only) is reflected consistently in the
   milestone doc update within this same commit; t7 PHASE F was already links-only. The
   in-commit milestone update is the right pattern for a mid-ticket scope change. ✅

---

## Cross-ticket notes

- **t7 (the big one):** wires all scripts into the full orchestrator with LLM selection in
  PHASE 0. **Read before t7:** the t2-review F3 note (now in the t7 prompt) — strip the
  leading `docbuilder/` from the bundle JSON's `data_sources[].path` at eval time (Option
  (a), same as the m2a source-path strip). That is the one non-obvious PHASE A detail.
- **t7 PHASE F confirmed:** `email_send_review.py --context '{...}' --drive-links
  <uploaded.json>` — no `--files`; the `{filename, drive_url}` shape matches
  `upload_output.py`'s output, which is what `build_body` consumes.
- **t8:** `email_send_review.py` → capability matrix. No new `requirements.txt` dep
  (`smtplib`/`email.mime.text` are stdlib).

---

**Outcome: zero blocking findings. t6 clear to merge. t7 clear to start.**
All four findings are confirmations — no action required.
