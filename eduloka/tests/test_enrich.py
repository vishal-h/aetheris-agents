"""Stage-3 enrich tests: pure enrichers + CLI, no network."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from edux_record import EduxRecord
from enrichers import ENRICHER_VERSIONS, ENRICHERS, enrich_domain, enrich_keywords

USE_CASE_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


def _record(link="https://www.iitm.ac.in", title="IIT Madras", snippet="Tech university in Chennai."):
    return EduxRecord(link=link, title=title, snippet=snippet, source_provider="exa",
                      fetched_at="2026-06-14T09:00:00+00:00")


# ---------------------------------------------------------------------------
# enrich_domain
# ---------------------------------------------------------------------------

def test_domain_extracts_host_and_tld():
    r = enrich_domain(_record())
    assert r["domain"] == "iitm.ac.in"
    assert r["tld"] == "in"


def test_domain_strips_www():
    r = enrich_domain(_record(link="https://www.annauniv.edu"))
    assert r["domain"] == "annauniv.edu"
    assert r["tld"] == "edu"


def test_domain_none_link():
    r = enrich_domain(EduxRecord())
    assert r["domain"] is None and r["tld"] is None


# ---------------------------------------------------------------------------
# enrich_keywords
# ---------------------------------------------------------------------------

def test_keywords_returns_terms_list():
    r = enrich_keywords(_record())
    assert isinstance(r["terms"], list)
    assert len(r["terms"]) > 0


def test_keywords_filters_stopwords_and_short():
    r = enrich_keywords(_record(title="A is the IIT", snippet="in an of"))
    assert "a" not in r["terms"]
    assert "is" not in r["terms"]
    assert "in" not in r["terms"]


def test_keywords_deduplicates():
    r = enrich_keywords(_record(title="madras madras madras", snippet="madras"))
    assert r["terms"].count("madras") == 1


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def test_all_enrichers_have_versions():
    assert set(ENRICHERS) == set(ENRICHER_VERSIONS)
    assert all(isinstance(v, int) for v in ENRICHER_VERSIONS.values())


# ---------------------------------------------------------------------------
# enrich.py: stamp + idempotency
# ---------------------------------------------------------------------------

def _enriched(tmp_path, fixture="exa.edux.jsonl", enrichers="domain,keywords"):
    out = tmp_path / "gold.jsonl"
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "enrich.py"),
         "--in", str(FIXTURES / fixture),
         "--out", str(out),
         "--enrichers", enrichers],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    return result, out


def test_enrich_cli_stamps_by_at_v(tmp_path):
    result, out = _enriched(tmp_path)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "ok"
    rec = json.loads(out.read_text().splitlines()[0])
    for name in ("domain", "keywords"):
        e = rec["enrichment"][name]
        assert e["_by"] == name
        assert "_at" in e
        assert e["_v"] == ENRICHER_VERSIONS[name]


def test_enrich_cli_idempotent(tmp_path):
    _, out = _enriched(tmp_path)
    first = json.loads(out.read_text().splitlines()[0])
    first_at = first["enrichment"]["keywords"]["_at"]

    # Run again over the gold output — should not overwrite existing enrichment.
    out2 = tmp_path / "gold2.jsonl"
    subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "enrich.py"),
         "--in", str(out), "--out", str(out2), "--enrichers", "keywords"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    second = json.loads(out2.read_text().splitlines()[0])
    assert second["enrichment"]["keywords"]["_at"] == first_at  # not re-stamped


def test_enrich_cli_domain_payload(tmp_path):
    _, out = _enriched(tmp_path, enrichers="domain")
    rec = json.loads(out.read_text().splitlines()[0])
    assert rec["enrichment"]["domain"]["tld"] == "in"
    assert "keywords" not in rec["enrichment"]


def test_enrich_cli_unknown_enricher_exits_1(tmp_path):
    out = tmp_path / "gold.jsonl"
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "enrich.py"),
         "--in", str(FIXTURES / "exa.edux.jsonl"),
         "--out", str(out), "--enrichers", "bogus"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"


def test_enrich_cli_missing_input_exits_1(tmp_path):
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "enrich.py"),
         "--in", "/tmp/nonexistent_eduloka_edux.jsonl"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"


def test_enrich_cli_partial_on_bad_line(tmp_path):
    good = json.dumps({"link": "https://iitm.ac.in", "title": "IIT", "snippet": "s",
                        "enrichment": {}, "status": 1})
    in_file = tmp_path / "mixed.jsonl"
    out_file = tmp_path / "gold.jsonl"
    in_file.write_text(good + "\n{bad json\n")
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "enrich.py"),
         "--in", str(in_file), "--out", str(out_file)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "partial"
    assert data["enriched"] == 1 and data["skipped"] == 1
