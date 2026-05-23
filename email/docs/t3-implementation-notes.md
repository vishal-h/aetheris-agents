# T3 Implementation Notes

## sandbox_path is two levels up

`email_orchestrator.exs` uses:

```elixir
Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))
```

One level up from `email/agents/` gives `email/`. Two levels up gives
`aetheris-agents/`. The system prompt args reference paths like
`email/scripts/email_download_template.py` and `email/scripts/email_send.py`,
which only resolve correctly when the CWD is the aetheris-agents root.
This is the same reasoning as `drive_orchestrator.exs`.

## overlay_base_dir: nil

Neither `email_download_template.py` nor `email_send.py` writes files that
need overlay isolation. The template download writes to `email/data/` and
must persist on disk. Email sending has no filesystem writes at all. There
is nothing to roll back, so overlay is unnecessary.

## smtp.cfg is a config file, not env vars

The SMTP app password is a 16-character string with spaces
(`xxxx xxxx xxxx xxxx`). A config file with a dedicated `[smtp]` section is
the natural format for SMTP credentials — `configparser` parses it cleanly
without shell quoting concerns. Env vars would require escaping the spaces
and are harder to audit.

## smtp.cfg.example is committed

The example documents the required keys and their semantics without exposing
real credentials. New operators can copy it and fill in values without
guessing field names or consulting the source. The distinction between
`username` and `from_address` is non-obvious enough that inline comments in
the example file are the right place to explain it.

## username vs from_address are separate fields

Gmail allows sending as an alias configured in "Send mail as" settings.
The account that authenticates (`username`) is the underlying Google account
that owns the app password. The address recipients see (`from_address`) is
the alias — e.g. `payroll@bitloka.com`. These are intentionally separate
fields: using the alias as `username` would cause authentication failure.

## Template is committed, not gitignored

`payslip_email_template.html` is not sensitive. The committed copy is the
working version used by `email_send.py`. Drive is the source of truth for
Finance-managed updates; `email_download_template.py` is a sync tool run
when Finance signals a change, not a required step on every monthly run.
Gitignoring the template would make the repo non-functional without a Drive
connection.

## uc-email V2 notes

- **Direct-to-employee sending**: current design sends to a single
  `to_address` (finance alias) for forwarding. V2 could send directly to
  `emp["email"]` with `to_address` from the employee record instead of config.
- **`--dry-run` flag**: `email_send.py` has no dry-run mode. A `--dry-run`
  flag that renders and logs without sending would make validation easier.
- **Per-employee error reporting**: failures are printed to stderr and
  counted, but the per-employee error message is not included in the final
  summary line. A `--report` flag or structured JSON output would improve
  auditability.
- **Attachment verification**: `find_pdf` returns the path if the file exists
  but does not validate it is a well-formed PDF. A header check (`%PDF`)
  would catch truncated files before attempting to send.
