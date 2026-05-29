"""
Tests for list_migration_queue.py and migration_agent.exs eval check.

Uses sample_corpus.duckdb fixture. Classifications are seeded via
write_classifications() then marked approved, matching production flow.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import classify_documents as cd
import list_migration_queue as lmq

FIXTURE = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"
SCRIPT  = Path(__file__).parent.parent / "scripts" / "list_migration_queue.py"

ACME_PATH   = "/data/archive/acme/FY2024/tax_return.pdf"
GLOBEX_PATH = "/data/archive/globex/FY2024/invoice_001.pdf"
INITECH_PATH = "/data/archive/initech/FY2024/contract.pdf"


def _seed_approved(conn, path, client="acme", doc_type="tax", confidence=0.90):
    """Insert a classification and immediately mark it approved."""
    cd.write_classifications(conn, [{
        "path": path, "client": client, "financial_year": "FY2024",
        "doc_type": doc_type, "confidence": confidence,
    }])
    conn.execute(
        "UPDATE classifications SET status = 'approved' WHERE path = ?", [path]
    )


@pytest.fixture
def db(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    conn = duckdb.connect(str(dest))
    yield conn
    conn.close()


@pytest.fixture
def db_path(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    return dest


# ---------------------------------------------------------------------------
# list_migration_queue — query logic
# ---------------------------------------------------------------------------

def test_empty_queue_when_no_approved_classifications(db):
    result = lmq.list_migration_queue(db)
    assert result == {"total": 0, "records": []}


def test_approved_classification_appears_in_queue(db):
    _seed_approved(db, ACME_PATH)
    result = lmq.list_migration_queue(db)
    assert result["total"] == 1
    rec = result["records"][0]
    assert rec["source_path"] == ACME_PATH
    assert rec["classification_id"] is not None


def test_proposed_classification_not_in_queue(db):
    """Only approved (not proposed/needs_review) classifications appear."""
    cd.write_classifications(db, [{
        "path": ACME_PATH, "client": "acme", "financial_year": "FY2024",
        "doc_type": "tax", "confidence": 0.90,
    }])
    result = lmq.list_migration_queue(db)
    assert result["total"] == 0


def test_dest_path_follows_taxonomy_structure(db):
    """proposed_dest = /clients/{client}/{fy}/{doc_type}/{filename}"""
    _seed_approved(db, ACME_PATH, client="acme", doc_type="tax")
    result = lmq.list_migration_queue(db)
    rec = result["records"][0]
    assert rec["dest_path"].startswith("/clients/acme/FY2024/tax/")
    assert rec["dest_path"].endswith("tax_return.pdf")


def test_classification_id_is_real_uuid(db):
    """classification_id must be the UUID from classifications, not null."""
    _seed_approved(db, ACME_PATH)
    result = lmq.list_migration_queue(db)
    cls_id = result["records"][0]["classification_id"]
    # Verify it matches the actual classification row
    db_id = db.execute(
        "SELECT id FROM classifications WHERE path = ?", [ACME_PATH]
    ).fetchone()[0]
    assert cls_id == db_id


def test_multiple_clients_in_queue(db):
    _seed_approved(db, ACME_PATH,    client="acme",    doc_type="tax")
    _seed_approved(db, GLOBEX_PATH,  client="globex",  doc_type="accounts")
    _seed_approved(db, INITECH_PATH, client="initech", doc_type="legal")
    result = lmq.list_migration_queue(db)
    assert result["total"] == 3
    clients = {r["source_path"].split("/")[3] for r in result["records"]}
    assert clients == {"acme", "globex", "initech"}


def test_already_migrated_excluded_from_queue(db, tmp_path):
    """Files already in migrations table with status='migrated' not in queue."""
    import uuid
    from datetime import datetime, timezone

    _seed_approved(db, ACME_PATH)

    # Insert a migration record for it
    now = datetime.now(timezone.utc)
    cls_id = db.execute(
        "SELECT id FROM classifications WHERE path = ?", [ACME_PATH]
    ).fetchone()[0]
    db.execute(
        """INSERT INTO migrations (id, path, dest_path, classification_id, status, proposed_at, migrated_at)
           VALUES (?, ?, ?, ?, 'migrated', ?, ?)""",
        [str(uuid.uuid4()), ACME_PATH, "/clients/acme/FY2024/tax/tax_return.pdf",
         cls_id, now, now],
    )

    result = lmq.list_migration_queue(db)
    assert result["total"] == 0


def test_limit_caps_results(db):
    _seed_approved(db, ACME_PATH,    client="acme",   doc_type="tax")
    _seed_approved(db, GLOBEX_PATH,  client="globex", doc_type="accounts")
    _seed_approved(db, INITECH_PATH, client="initech",doc_type="legal")
    result = lmq.list_migration_queue(db, limit=2)
    assert result["total"] == 2


def test_results_ordered_by_source_path(db):
    _seed_approved(db, INITECH_PATH, client="initech", doc_type="legal")
    _seed_approved(db, ACME_PATH,    client="acme",    doc_type="tax")
    _seed_approved(db, GLOBEX_PATH,  client="globex",  doc_type="accounts")
    result = lmq.list_migration_queue(db)
    paths = [r["source_path"] for r in result["records"]]
    assert paths == sorted(paths)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_empty_queue_outputs_json(db_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout.strip())
    assert out == {"total": 0, "records": []}


def test_cli_reports_count_to_stderr(db_path):
    conn = duckdb.connect(str(db_path))
    _seed_approved(conn, ACME_PATH)
    conn.close()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", str(db_path)],
        capture_output=True, text=True,
    )
    assert "1 files pending migration" in result.stderr


def test_cli_bad_db_exits_1():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--db", "/nonexistent/path.duckdb"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Agent eval check
# ---------------------------------------------------------------------------

def test_agent_evaluates_without_error(tmp_path):
    agent = Path(__file__).parent.parent / "agents" / "migration_agent.exs"
    aetheris = Path(__file__).parent.parent.parent.parent / "aetheris"
    if not aetheris.exists():
        pytest.skip("aetheris repo not found")

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{agent}")'],
        cwd=str(aetheris),
        env={**__import__("os").environ,
             "PROVENANCE_DB_PATH": str(tmp_path / "corpus.duckdb"),
             "CLIENTS_ROOT": str(tmp_path / "clients")},
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
