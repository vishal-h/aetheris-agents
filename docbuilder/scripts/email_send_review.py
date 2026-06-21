"""Send a review email for a generated document set.

Sends to the internal review alias `DOCBUILDER_REVIEW_EMAIL` (NOT directly to the
client). The body names the external `client_email` so the ops reviewer can forward
after approval, and lists the Drive links to the uploaded files. Links-only — no
attachments (the files live in Drive; the reviewer opens the links).

SMTP via env (same as email/scripts/email_send.py): `SMTP_HOST`, `SMTP_PORT` (default
587), `SMTP_USER`, `SMTP_PASSWORD`, optional `SMTP_FROM`. Required context fields:
`client_name`, `client_email`, `date`. See docs/context-schema.md.

Prints {"status": "sent", "recipient": ...}. Exit 1 on missing config/fields or send error.
"""

import argparse
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText

REQUIRED_FIELDS = ("client_name", "client_email", "date")


def smtp_config():
    """SMTP settings from env. Exit 1 if a required var is missing."""
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    missing = [k for k, v in {"SMTP_HOST": host, "SMTP_USER": user,
                              "SMTP_PASSWORD": password}.items() if not v]
    if missing:
        print(json.dumps({"status": "error",
                          "error": f"SMTP env vars not set: {', '.join(missing)}"}),
              file=sys.stderr)
        sys.exit(1)
    return {
        "host": host,
        "port": os.getenv("SMTP_PORT", "587"),
        "username": user,
        "password": password,
        "from_address": os.getenv("SMTP_FROM") or user,
    }


def build_subject(context):
    doc_type = context.get("doc_type") or "document"
    return f"[REVIEW] {context['client_name']} {doc_type} — {context['date']}"


def build_body(context, drive_links):
    links = drive_links or []
    links_block = "\n".join(f"- {l['filename']}: {l['drive_url']}" for l in links) or "(none)"
    return (
        f"Please review the document(s) for {context['client_name']} and forward to "
        f"{context['client_email']} if approved.\n\nDrive links:\n{links_block}\n"
    )


def build_message(from_address, review_email, context, drive_links):
    """Build the plain-text review email (does not send)."""
    msg = MIMEText(build_body(context, drive_links), "plain")
    msg["From"] = from_address
    msg["To"] = review_email
    msg["Subject"] = build_subject(context)
    return msg


def send_review(context, drive_links):
    """Build and send the review email; return the recipient address."""
    review_email = os.getenv("DOCBUILDER_REVIEW_EMAIL")
    if not review_email:
        print(json.dumps({"status": "error",
                          "error": "DOCBUILDER_REVIEW_EMAIL not set"}), file=sys.stderr)
        sys.exit(1)
    config = smtp_config()
    msg = build_message(config["from_address"], review_email, context, drive_links)
    with smtplib.SMTP(config["host"], int(config["port"])) as smtp:
        smtp.starttls()
        smtp.login(config["username"], config["password"])
        smtp.sendmail(config["from_address"], review_email, msg.as_string())
    return review_email


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True, help="inline JSON of context fields")
    parser.add_argument("--drive-links", default="[]",
                        help="JSON array of {filename, drive_url}")
    args = parser.parse_args()

    try:
        context = json.loads(args.context)
        drive_links = json.loads(args.drive_links)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"invalid JSON: {e}"}), file=sys.stderr)
        sys.exit(1)

    missing = [f for f in REQUIRED_FIELDS if not context.get(f)]
    if missing:
        print(json.dumps({"status": "error",
                          "error": f"context missing required field(s): {', '.join(missing)}"}),
              file=sys.stderr)
        sys.exit(1)

    try:
        recipient = send_review(context, drive_links)
    except SystemExit:
        raise
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps({"status": "sent", "recipient": recipient}))


if __name__ == "__main__":
    main()
