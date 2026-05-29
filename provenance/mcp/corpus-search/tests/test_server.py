"""
Tests for corpus-search MCP server.

Unit tests call tool handlers directly with a real DuckDB connection.
Integration tests exercise the full JSON-RPC flow via subprocess.

Uses sample_corpus.duckdb fixture (classifications seeded per test).
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

# server.py is two levels up from this file
SERVER_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SERVER_DIR))
import server as srv

FIXTURE = Path(__file__).parents[3] / "tests" / "fixtures" / "sample_corpus.duckdb"
SERVER_PY = SERVER_DIR / "server.py"

# Paths present in the fixture's f2_file_index
_ACME_TAX    = "/data/archive/acme/FY2024/tax_return.pdf"
_ACME_LETTER = "/data/archive/acme/FY2024/letter_jan.docx"
_ACME_REPORT = "/data/archive/acme/FY2023/annual_report.pdf"
_GLOBEX_INV  = "/data/archive/globex/FY2024/invoice_001.pdf"
_INITECH_CON = "/data/archive/initech/FY2024/contract.pdf"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed(conn, path, client, fy, doc_type, confidence=0.90, raw_excerpt="", status="proposed"):
    conn.execute(
        """INSERT INTO classifications
           (id, path, client, financial_year, doc_type, confidence,
            raw_excerpt, status, classified_at)
           VALUES (gen_random_uuid()::TEXT, ?, ?, ?, ?, ?, ?, ?, now())
           ON CONFLICT (id) DO NOTHING""",
        [path, client, fy, doc_type, confidence, raw_excerpt, status],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    c = duckdb.connect(str(dest))
    # Seed classifications for all fixture paths used in tests
    _seed(c, _ACME_TAX,    "acme",    "FY2024", "tax",      0.92,
          "Tax return for ACME Corp fiscal year 2024 including GST schedule",
          "approved")
    _seed(c, _ACME_LETTER, "acme",    "FY2024", "legal",    0.85,
          "Legal correspondence from ACME Corp counsel January 2024")
    _seed(c, _ACME_REPORT, "acme",    "FY2023", "accounts", 0.80,
          "Annual report for ACME Corp 2023 balance sheet summary")
    _seed(c, _GLOBEX_INV,  "globex",  "FY2024", "accounts", 0.75,
          "Invoice 001 from Globex Corporation for consulting services")
    _seed(c, _INITECH_CON, "initech", "FY2024", "legal",    0.70,
          "Contract agreement Initech Inc service level 2024")
    yield c
    c.close()


@pytest.fixture
def db_path(tmp_path):
    dest = tmp_path / "corpus.duckdb"
    shutil.copy(FIXTURE, dest)
    c = duckdb.connect(str(dest))
    _seed(c, _ACME_TAX,    "acme",    "FY2024", "tax",      0.92,
          "Tax return for ACME Corp fiscal year 2024 including GST schedule",
          "approved")
    _seed(c, _GLOBEX_INV,  "globex",  "FY2024", "accounts", 0.75,
          "Invoice Globex")
    c.close()
    return dest


# ---------------------------------------------------------------------------
# search_corpus — unit tests
# ---------------------------------------------------------------------------

def test_search_corpus_keyword_matches_raw_excerpt(conn):
    results = srv.tool_search_corpus(conn, {"query": "GST"})
    assert any(r["path"] == _ACME_TAX for r in results)


def test_search_corpus_keyword_matches_client_name(conn):
    results = srv.tool_search_corpus(conn, {"query": "globex"})
    assert any(r["path"] == _GLOBEX_INV for r in results)


def test_search_corpus_keyword_no_match_returns_empty(conn):
    results = srv.tool_search_corpus(conn, {"query": "xyznonexistentterm987"})
    assert results == []


def test_search_corpus_client_filter(conn):
    results = srv.tool_search_corpus(conn, {"client": "acme"})
    paths = [r["path"] for r in results]
    assert all(r["client"] == "acme" for r in results)
    assert _ACME_TAX in paths
    assert _GLOBEX_INV not in paths


def test_search_corpus_fy_filter(conn):
    results = srv.tool_search_corpus(conn, {"fy": "FY2023"})
    assert all(r["fy"] == "FY2023" for r in results)
    assert any(r["path"] == _ACME_REPORT for r in results)


def test_search_corpus_doc_type_filter(conn):
    results = srv.tool_search_corpus(conn, {"doc_type": "legal"})
    assert all(r["doc_type"] == "legal" for r in results)
    assert len(results) == 2  # acme letter + initech contract


def test_search_corpus_limit(conn):
    results = srv.tool_search_corpus(conn, {"limit": 2})
    assert len(results) <= 2


def test_search_corpus_multi_token_and_logic(conn):
    # "ACME 2024" — both tokens must match; only FY2024 acme rows qualify
    results = srv.tool_search_corpus(conn, {"query": "ACME 2024"})
    assert all(r["client"] == "acme" for r in results)
    assert all(r["fy"] == "FY2024" for r in results)


def test_search_corpus_raw_excerpt_preview_truncated(conn):
    # Seed a row with a long raw_excerpt
    long_excerpt = "word " * 100
    _seed(conn, _ACME_LETTER, "acme", "FY2024", "legal", 0.80, long_excerpt)
    results = srv.tool_search_corpus(conn, {"client": "acme", "doc_type": "legal"})
    previews = [r["raw_excerpt_preview"] for r in results]
    assert all(len(p) <= 200 for p in previews)


# ---------------------------------------------------------------------------
# list_clients — unit tests
# ---------------------------------------------------------------------------

def test_list_clients_returns_all_clients(conn):
    results = srv.tool_list_clients(conn, {})
    client_names = [r["client"] for r in results]
    assert "acme" in client_names
    assert "globex" in client_names
    assert "initech" in client_names


def test_list_clients_ordered_alphabetically(conn):
    results = srv.tool_list_clients(conn, {})
    names = [r["client"] for r in results]
    assert names == sorted(names)


def test_list_clients_correct_file_count(conn):
    results = srv.tool_list_clients(conn, {})
    acme = next(r for r in results if r["client"] == "acme")
    assert acme["file_count"] == 3  # tax + letter + report


def test_list_clients_doc_types_present(conn):
    results = srv.tool_list_clients(conn, {})
    acme = next(r for r in results if r["client"] == "acme")
    assert set(acme["doc_types"]) == {"accounts", "legal", "tax"}


# ---------------------------------------------------------------------------
# list_documents — unit tests
# ---------------------------------------------------------------------------

def test_list_documents_for_client(conn):
    results = srv.tool_list_documents(conn, {"client": "acme"})
    assert len(results) == 3
    assert all(r["fy"] in ("FY2023", "FY2024") for r in results)


def test_list_documents_fy_filter(conn):
    results = srv.tool_list_documents(conn, {"client": "acme", "fy": "FY2024"})
    assert all(r["fy"] == "FY2024" for r in results)
    assert len(results) == 2  # tax + letter


def test_list_documents_doc_type_filter(conn):
    results = srv.tool_list_documents(conn, {"client": "acme", "doc_type": "tax"})
    assert len(results) == 1
    assert results[0]["path"] == _ACME_TAX


# ---------------------------------------------------------------------------
# get_document_meta — unit tests
# ---------------------------------------------------------------------------

def test_get_document_meta_known_path(conn):
    meta = srv.tool_get_document_meta(conn, {"path": _ACME_TAX})
    assert meta is not None
    assert meta["path"] == _ACME_TAX
    assert meta["client"] == "acme"
    assert meta["fy"] == "FY2024"
    assert meta["doc_type"] == "tax"
    assert meta["classification_status"] == meta["status"]
    assert "size_bytes" in meta
    assert "mime_type" in meta


def test_get_document_meta_unknown_path_returns_null(conn):
    meta = srv.tool_get_document_meta(conn, {"path": "/data/archive/does/not/exist.pdf"})
    assert meta is None


# ---------------------------------------------------------------------------
# find_duplicates — unit tests
# ---------------------------------------------------------------------------

def test_find_duplicates_known_hash(conn):
    # sha-a has 3 entries in the fixture (tax_return.pdf + 2 copies)
    results = srv.tool_find_duplicates(conn, {"sha256": "sha-a"})
    assert len(results) >= 2
    paths = [r["path"] for r in results]
    assert _ACME_TAX in paths


def test_find_duplicates_unknown_hash_returns_empty(conn):
    results = srv.tool_find_duplicates(conn, {"sha256": "no-such-hash-zzz"})
    assert results == []


# ---------------------------------------------------------------------------
# JSON-RPC protocol — integration tests (subprocess)
# ---------------------------------------------------------------------------

def _rpc(db_path, *messages):
    """Send JSON-RPC messages to the server via subprocess and return parsed responses."""
    stdin_data = "\n".join(json.dumps(m) for m in messages) + "\n"
    result = subprocess.run(
        [sys.executable, str(SERVER_PY)],
        input=stdin_data,
        capture_output=True,
        text=True,
        env={"CORPUS_DB_PATH": str(db_path), "PATH": "/usr/bin:/bin"},
        timeout=10,
    )
    lines = [l for l in result.stdout.splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


def test_jsonrpc_initialize(db_path):
    resps = _rpc(db_path, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert resps[0]["result"]["serverInfo"]["name"] == "corpus-search"
    assert "tools" in resps[0]["result"]["capabilities"]


def test_jsonrpc_tools_list(db_path):
    resps = _rpc(db_path,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )
    tool_names = {t["name"] for t in resps[1]["result"]["tools"]}
    assert tool_names == {"search_corpus", "list_clients", "list_documents",
                          "get_document_meta", "find_duplicates"}


def test_jsonrpc_tools_call_list_clients(db_path):
    resps = _rpc(db_path,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "list_clients", "arguments": {}}},
    )
    content = json.loads(resps[1]["result"]["content"][0]["text"])
    # db_path fixture seeded acme + globex only
    client_names = [r["client"] for r in content]
    assert "acme" in client_names


def test_jsonrpc_notification_produces_no_response(db_path):
    resps = _rpc(db_path,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},  # no id
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
    )
    # Only the tools/list response, not the notification
    assert len(resps) == 1
    assert resps[0]["id"] == 1


def test_jsonrpc_malformed_input_returns_error_no_crash(db_path):
    result = subprocess.run(
        [sys.executable, str(SERVER_PY)],
        input="not valid json\n",
        capture_output=True,
        text=True,
        env={"CORPUS_DB_PATH": str(db_path), "PATH": "/usr/bin:/bin"},
        timeout=10,
    )
    assert result.returncode == 0
    resp = json.loads(result.stdout.strip())
    assert "error" in resp


def test_jsonrpc_unknown_tool_returns_error(db_path):
    resps = _rpc(db_path,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "nonexistent_tool", "arguments": {}}},
    )
    assert "error" in resps[1]
    assert "nonexistent_tool" in resps[1]["error"]["message"]
