import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from email_send_review import build_body, build_message, build_subject

USE_CASE_ROOT = Path(__file__).parent.parent

CTX = {
    "client_name": "Acme Corp",
    "client_email": "ops@acme.example",
    "date": "2026-06-20",
    "doc_type": "proposal",
}
LINKS = [
    {"filename": "acme_corp_proposal_2026-06-20.pdf",
     "drive_url": "https://drive.google.com/file/d/ID1/view"},
    {"filename": "acme_corp_proposal_2026-06-20.xlsx",
     "drive_url": "https://drive.google.com/file/d/ID2/view"},
]


def _env_minus(*keys):
    env = dict(os.environ)
    for k in keys:
        env.pop(k, None)
    return env


# --- unit: subject ---

def test_build_subject():
    assert build_subject(CTX) == "[REVIEW] Acme Corp proposal — 2026-06-20"


def test_build_subject_doc_type_fallback():
    ctx = {k: v for k, v in CTX.items() if k != "doc_type"}
    assert build_subject(ctx) == "[REVIEW] Acme Corp document — 2026-06-20"


# --- unit: body ---

def test_build_body_has_client_email_and_links():
    body = build_body(CTX, LINKS)
    assert "ops@acme.example" in body
    assert "forward to" in body
    assert "ID1/view" in body
    assert "ID2/view" in body


def test_build_body_no_links():
    assert "(none)" in build_body(CTX, [])


# --- unit: message build (no send) ---

def test_build_message_headers_and_plain_text():
    msg = build_message("from@x", "review@x", CTX, LINKS)
    assert msg["To"] == "review@x"
    assert msg["From"] == "from@x"
    assert msg["Subject"] == "[REVIEW] Acme Corp proposal — 2026-06-20"
    assert msg.get_content_type() == "text/plain"
    assert "ops@acme.example" in msg.get_payload()


# --- CLI validation (no SMTP needed) ---

def test_cli_missing_context_field_exits_1():
    result = subprocess.run(
        [sys.executable, "scripts/email_send_review.py",
         "--context", '{"client_name":"Acme","date":"2026-06-20"}'],  # no client_email
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 1
    assert "client_email" in result.stderr


def test_cli_missing_review_email_exits_1():
    result = subprocess.run(
        [sys.executable, "scripts/email_send_review.py", "--context", json.dumps(CTX)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
        env=_env_minus("DOCBUILDER_REVIEW_EMAIL")
    )
    assert result.returncode == 1
    assert "DOCBUILDER_REVIEW_EMAIL" in result.stderr


# --- integration (real SMTP; skipped without env) ---

@pytest.mark.integration
def test_send_review_smtp():
    if not (os.environ.get("DOCBUILDER_REVIEW_EMAIL") and os.environ.get("SMTP_HOST")):
        pytest.skip("DOCBUILDER_REVIEW_EMAIL / SMTP_* not set")
    result = subprocess.run(
        [sys.executable, "scripts/email_send_review.py",
         "--context", json.dumps(CTX), "--drive-links", json.dumps(LINKS)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "sent"
