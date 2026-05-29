"""
Tests for validate_search.py and search_queries.json fixture.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import validate_search as vs

QUERIES_FILE = Path(__file__).parent / "fixtures" / "search_queries.json"


# ---------------------------------------------------------------------------
# search_queries.json fixture tests
# ---------------------------------------------------------------------------

def test_queries_file_has_20_entries():
    with open(QUERIES_FILE) as f:
        queries = json.load(f)
    assert len(queries) == 20


def test_queries_have_required_fields():
    with open(QUERIES_FILE) as f:
        queries = json.load(f)
    for q in queries:
        assert "query" in q, f"Missing 'query' in: {q}"
        assert "expected_paths" in q, f"Missing 'expected_paths' in: {q}"
        assert "notes" in q, f"Missing 'notes' in: {q}"


def test_queries_expected_paths_types():
    with open(QUERIES_FILE) as f:
        queries = json.load(f)
    for q in queries:
        ep = q["expected_paths"]
        assert ep is None or isinstance(ep, list), (
            f"expected_paths must be null or list, got {type(ep)} in: {q['query']}"
        )


def test_queries_have_two_no_results():
    with open(QUERIES_FILE) as f:
        queries = json.load(f)
    null_count = sum(1 for q in queries if q["expected_paths"] is None)
    assert null_count == 2, f"Expected exactly 2 no-results queries, got {null_count}"


def test_queries_all_have_non_empty_query():
    with open(QUERIES_FILE) as f:
        queries = json.load(f)
    for q in queries:
        assert q["query"].strip(), f"Empty query string in: {q}"


# ---------------------------------------------------------------------------
# score_query unit tests
# ---------------------------------------------------------------------------

def _make_result(output: str, exit_code: int = 0, error: str | None = None) -> dict:
    return {"output": output, "run_id": "test-run-1", "exit_code": exit_code, "error": error}


def test_score_empty_expected_paths_pass_when_path_found():
    case = {"query": "acme tax", "expected_paths": [], "notes": ""}
    run_result = _make_result("Found 1 document: /data/archive/acme/tax.pdf")
    result = vs.score_query(case, run_result)
    assert result["passed"] is True
    assert result["result_count"] >= 1


def test_score_empty_expected_paths_fail_when_no_results():
    case = {"query": "acme tax", "expected_paths": [], "notes": ""}
    run_result = _make_result("No documents found matching \"acme tax\".")
    result = vs.score_query(case, run_result)
    assert result["passed"] is False


def test_score_null_expected_paths_pass_when_not_found_message():
    case = {"query": "nonexistent", "expected_paths": None, "notes": ""}
    run_result = _make_result("No documents found matching \"nonexistent\".\nSuggestions:")
    result = vs.score_query(case, run_result)
    assert result["passed"] is True


def test_score_null_expected_paths_fail_when_no_not_found_message():
    case = {"query": "nonexistent", "expected_paths": None, "notes": ""}
    run_result = _make_result("/data/archive/acme/tax.pdf")
    result = vs.score_query(case, run_result)
    assert result["passed"] is False


def test_score_specific_paths_pass_when_expected_path_present():
    case = {"query": "acme tax", "expected_paths": ["/data/archive/acme/tax.pdf"], "notes": ""}
    run_result = _make_result("1. /data/archive/acme/tax.pdf\n   Client: acme")
    result = vs.score_query(case, run_result)
    assert result["passed"] is True


def test_score_specific_paths_fail_when_expected_path_absent():
    case = {"query": "acme tax", "expected_paths": ["/data/archive/acme/tax.pdf"], "notes": ""}
    run_result = _make_result("Found: /data/archive/other/file.pdf")
    result = vs.score_query(case, run_result)
    assert result["passed"] is False


def test_score_error_always_fails():
    case = {"query": "acme", "expected_paths": [], "notes": ""}
    run_result = _make_result("", exit_code=-1, error="timeout")
    result = vs.score_query(case, run_result)
    assert result["passed"] is False
    assert result["reason"] == "timeout"


def test_score_no_results_pattern_case_insensitive():
    case = {"query": "nonexistent", "expected_paths": None, "notes": ""}
    run_result = _make_result("No Results Found matching your query.")
    result = vs.score_query(case, run_result)
    assert result["passed"] is True


# ---------------------------------------------------------------------------
# _extract_run_id
# ---------------------------------------------------------------------------

def test_extract_run_id_from_stdout():
    stdout = "Run ID:   provenance-search-abc123\nLabel:    Provenance Search\n"
    assert vs._extract_run_id(stdout) == "provenance-search-abc123"


def test_extract_run_id_returns_none_when_absent():
    assert vs._extract_run_id("no run id here") is None
