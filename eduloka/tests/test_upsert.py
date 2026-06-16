"""Stage-4 upsert tests.

DB tests are @pytest.mark.integration and auto-skip when EDUX_DATABASE_URL
is unset. The offline tests cover the row-projection logic and CLI error
paths without any DB connection.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from edux_record import EduxRecord
from upsert_institute import _row

USE_CASE_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Offline: row projection
# ---------------------------------------------------------------------------

def _rec(**kwargs):
    defaults = dict(link="https://iitm.ac.in", title="IIT Madras", snippet="Tech.",
                    image="https://iitm.ac.in/logo.png", search_term="edu.in", status=1,
                    metatags=[{"og:title": "IIT"}], enrichment={"domain": {"tld": "in", "_v": 1}})
    defaults.update(kwargs)
    return EduxRecord(**defaults)


def test_row_keys_match_gws_cse_columns():
    row = _row(_rec())
    assert set(row) == {"link", "title", "snippet", "image", "search_term", "status", "metatags", "enrichment"}


def test_row_metatags_is_json_string():
    row = _row(_rec())
    parsed = json.loads(row["metatags"])
    assert isinstance(parsed, list)


def test_row_enrichment_is_json_string():
    row = _row(_rec())
    parsed = json.loads(row["enrichment"])
    assert isinstance(parsed, dict)


def test_row_excludes_text():
    rec = _rec()
    rec.text = "full page body"
    row = _row(rec)
    assert "text" not in row


# ---------------------------------------------------------------------------
# Offline: CLI error paths (no DB needed)
# ---------------------------------------------------------------------------

def test_cli_missing_input_exits_1():
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "upsert_institute.py"),
         "--in", "/tmp/nonexistent_eduloka_gold.jsonl"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
        env={**os.environ, "EDUX_DATABASE_URL": "postgresql://unused"},
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"


def test_cli_missing_db_url_exits_1(tmp_path):
    in_file = tmp_path / "dummy.jsonl"
    in_file.write_text("")
    env = {k: v for k, v in os.environ.items() if k != "EDUX_DATABASE_URL"}
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "upsert_institute.py"),
         "--in", str(in_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
        env=env,
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "error"
    assert "EDUX_DATABASE_URL" in data["error"]


# ---------------------------------------------------------------------------
# Integration: real DB (auto-skip when EDUX_DATABASE_URL unset)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def db_url():
    url = os.environ.get("EDUX_DATABASE_URL")
    if not url:
        pytest.skip("EDUX_DATABASE_URL not set")
    return url


@pytest.mark.integration
def test_upsert_and_rerun_idempotent(db_url, tmp_path):
    import psycopg

    # One gold record.
    rec = EduxRecord(link="https://test-eduloka-upsert.example.com", title="Test Inst",
                     snippet="test", search_term="edu.in", status=1,
                     metatags=[], enrichment={})
    in_file = tmp_path / "gold.jsonl"
    in_file.write_text(json.dumps(rec.to_dict()) + "\n")

    for _ in range(2):  # run twice — second run must not error
        result = subprocess.run(
            [sys.executable, str(USE_CASE_ROOT / "scripts" / "upsert_institute.py"),
             "--in", str(in_file)],
            capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
            env={**os.environ, "EDUX_DATABASE_URL": db_url},
        )
        assert result.returncode == 0, result.stdout
        assert json.loads(result.stdout)["upserted"] == 1

    # Clean up test row.
    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM gws_cse WHERE link = %s",
                    ("https://test-eduloka-upsert.example.com",))
        conn.commit()


@pytest.mark.integration
def test_migration_is_idempotent(db_url):
    import psycopg

    sql = (USE_CASE_ROOT / "data" / "migrations" / "0001_add_enrichment_jsonb.sql").read_text()
    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
    # If IF NOT EXISTS works, no exception is raised on second apply.
