# Implementation notes — m-docbuilder-m2b t6

Ticket: `email_send_review.py` — review email to the internal alias (links-only).

---

## What shipped

- `scripts/email_send_review.py` (new): sends to `DOCBUILDER_REVIEW_EMAIL` with subject
  `[REVIEW] {client_name} {doc_type} — {date}` and a plain-text body naming the external
  `client_email` (for the reviewer to forward) + the Drive links. **Links-only — no
  attachments, no size check, no MIME binary encoding** (the files live in Drive; the
  reviewer opens the links). SMTP via env (`SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/
  `SMTP_PASSWORD`/optional `SMTP_FROM`), same pattern as `email/scripts/email_send.py`.
  Prints `{"status":"sent","recipient":...}`; exit 1 on missing config/fields or send error.
- `tests/test_email_send_review.py` (new): 7 unit (no SMTP) + 1 integration (skipped
  without `DOCBUILDER_REVIEW_EMAIL`/`SMTP_*`).
- Full suite: 202 passed, 3 skipped.

---

## Decisions

**Links-only (scope simplification, mid-ticket).** The ticket was simplified to drop
attachments entirely: no `--files` arg, no 10 MB threshold, no `MIMEApplication`/multipart.
The email is a single `MIMEText` plain-text part with the Drive links in the body. This is
simpler and correct for the review-and-forward flow — the deliverables are already in Drive
(uploaded by `upload_output.py`), so the reviewer clicks the `/view` links rather than
receiving (and re-forwarding) binary copies. The t6 milestone scope/prompt were updated to
match.

**Pure helpers factored for SMTP-free testing.** `build_subject`, `build_body`,
`build_message` are pure functions over context/links; `send_review` is the only network
part. The 7 unit tests cover subject (+ doc_type fallback), body (links + `(none)`), and
the message headers/plain-text type without SMTP — so the done-check `-m "not integration"`
has real coverage (same reasoning as t5). The real send is the `@pytest.mark.integration`
test, skipped without SMTP env.

**Validation order in `main()`: context fields → `DOCBUILDER_REVIEW_EMAIL` → SMTP config
→ send.** Missing context fields and a missing review alias exit 1 *before* any SMTP work,
so those failure paths are non-integration CLI tests (no creds).

**Email goes to the review alias, not the client.** Per the README design decision:
`To:` is `DOCBUILDER_REVIEW_EMAIL`; `client_email` appears only in the body so ops reviews
and forwards. Prevents accidental direct client delivery from an automated pipeline.

## Forward notes

- **t7 (orchestrator PHASE F):** `email_send_review.py --context '{...}' --drive-links
  <uploaded.json contents>` (no `--files` — already links-only in the t7 prompt). The
  `{filename, drive_url}` shape matches `upload_output.py`'s output.
- **t8:** add `email_send_review.py` to the capability matrix. No new `requirements.txt`
  dep — `smtplib`/`email` are stdlib.
