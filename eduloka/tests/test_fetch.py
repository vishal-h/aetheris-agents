"""Stage-1 fetch tests (t1: cse + exa; t2: serper + dataforseo).

The single http_get_json / http_post_json choke points are monkeypatched so
tests run offline with no credentials or network.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import fetch_base
import fetch_cse
import fetch_dataforseo
import fetch_exa
import fetch_serper

USE_CASE_ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Fixture bodies (provider-native shapes)
# ---------------------------------------------------------------------------

CSE_BODY = {
    "items": [
        {
            "title": "IIT Madras",
            "link": "https://iitm.ac.in",
            "snippet": "tech",
            "pagemap": {
                "cse_image": [{"src": "https://iitm.ac.in/logo.png"}],
                "metatags": [{"og:title": "IIT Madras", "og:type": "website"}],
            },
        },
        {
            "title": "Anna University",
            "link": "https://annauniv.edu",
            "snippet": "uni",
            "pagemap": {"metatags": [{"og:title": "Anna University"}]},
        },
    ]
}

EXA_BODY = {
    "results": [
        {"title": "IIT Madras", "url": "https://iitm.ac.in", "text": "tech ...", "score": 0.9},
        {"title": "Anna University", "url": "https://annauniv.edu", "text": "uni ...", "score": 0.8},
    ]
}

SERPER_BODY = {
    "organic": [
        {"title": "IIT Madras", "link": "https://iitm.ac.in", "snippet": "tech", "position": 1},
        {"title": "Anna University", "link": "https://annauniv.edu", "snippet": "uni", "position": 2},
    ]
}

DATAFORSEO_BODY = {
    "tasks": [{"result": [{"items": [
        {"type": "organic", "title": "IIT Madras", "url": "https://iitm.ac.in",
         "description": "tech", "rank_absolute": 1},
        {"type": "people_also_ask", "title": "ignored"},
        {"type": "organic", "title": "Anna University", "url": "https://annauniv.edu",
         "description": "uni", "rank_absolute": 2},
    ]}]}]
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    for k in ("GWS_CSE_API_KEY", "GWS_CSE_ENGINE_ID", "EXA_API_KEY",
              "SERPER_API_KEY", "DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"):
        monkeypatch.setenv(k, "test-key")


# ---------------------------------------------------------------------------
# CSE tests
# ---------------------------------------------------------------------------

def test_cse_returns_raw_items_with_pagemap(monkeypatch):
    monkeypatch.setattr(fetch_cse, "http_get_json", lambda *a, **k: CSE_BODY)
    items = fetch_cse.CseFetcher().fetch("iit")
    assert [i["link"] for i in items] == ["https://iitm.ac.in", "https://annauniv.edu"]
    assert "pagemap" in items[0]  # raw, unmapped — pagemap preserved for the mapper


def test_cse_num_capped_at_10(monkeypatch):
    captured = {}

    def fake_get(url, headers, params, **k):
        captured["num"] = params["num"]
        return CSE_BODY

    monkeypatch.setattr(fetch_cse, "http_get_json", fake_get)
    fetch_cse.CseFetcher().fetch("iit", num=99)
    assert captured["num"] == 10


def test_cse_country_cr_param(monkeypatch):
    captured = {}

    def fake_get(url, headers, params, **k):
        captured["cr"] = params["cr"]
        return CSE_BODY

    monkeypatch.setattr(fetch_cse, "http_get_json", fake_get)
    fetch_cse.CseFetcher().fetch("iit", country="US")
    assert captured["cr"] == "countryUS"


# ---------------------------------------------------------------------------
# Exa tests
# ---------------------------------------------------------------------------

def test_exa_returns_raw_results(monkeypatch):
    monkeypatch.setattr(fetch_exa, "http_post_json", lambda *a, **k: EXA_BODY)
    items = fetch_exa.ExaFetcher().fetch("iit")
    assert [i["url"] for i in items] == ["https://iitm.ac.in", "https://annauniv.edu"]


def test_exa_start_offset_slices_raw(monkeypatch):
    monkeypatch.setattr(fetch_exa, "http_post_json", lambda *a, **k: EXA_BODY)
    items = fetch_exa.ExaFetcher().fetch("iit", start=2, num=10)
    assert [i["url"] for i in items] == ["https://annauniv.edu"]


def test_exa_overfetch_num(monkeypatch):
    captured = {}

    def fake_post(url, headers, payload, **k):
        captured["numResults"] = payload["numResults"]
        return EXA_BODY

    monkeypatch.setattr(fetch_exa, "http_post_json", fake_post)
    fetch_exa.ExaFetcher().fetch("iit", start=3, num=5)
    assert captured["numResults"] == 7  # (3-1) + 5


# ---------------------------------------------------------------------------
# Credentials / unknown provider
# ---------------------------------------------------------------------------

def test_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    with pytest.raises(fetch_base.SearchError):
        fetch_exa.ExaFetcher()


def test_missing_cse_credentials_raise(monkeypatch):
    monkeypatch.delenv("GWS_CSE_API_KEY", raising=False)
    with pytest.raises(fetch_base.SearchError):
        fetch_cse.CseFetcher()


def test_unknown_provider_raises():
    with pytest.raises(fetch_base.SearchError):
        fetch_base.get_fetcher("bing")


# ---------------------------------------------------------------------------
# Serper tests
# ---------------------------------------------------------------------------

def test_serper_returns_raw_organic(monkeypatch):
    monkeypatch.setattr(fetch_serper, "http_post_json", lambda *a, **k: SERPER_BODY)
    items = fetch_serper.SerperFetcher().fetch("iit")
    assert [i["link"] for i in items] == ["https://iitm.ac.in", "https://annauniv.edu"]
    assert "position" in items[0]  # raw, unmapped


def test_serper_page_param(monkeypatch):
    captured = {}

    def fake_post(url, headers, payload, **k):
        captured["page"] = payload["page"]
        return SERPER_BODY

    monkeypatch.setattr(fetch_serper, "http_post_json", fake_post)
    fetch_serper.SerperFetcher().fetch("iit", start=11, num=10)
    assert captured["page"] == 2  # (11-1)//10 + 1


def test_serper_country_gl_param(monkeypatch):
    captured = {}

    def fake_post(url, headers, payload, **k):
        captured["gl"] = payload["gl"]
        return SERPER_BODY

    monkeypatch.setattr(fetch_serper, "http_post_json", fake_post)
    fetch_serper.SerperFetcher().fetch("iit", country="US")
    assert captured["gl"] == "us"


def test_serper_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    with pytest.raises(fetch_base.SearchError):
        fetch_serper.SerperFetcher()


# ---------------------------------------------------------------------------
# DataForSEO tests
# ---------------------------------------------------------------------------

def test_dataforseo_filters_non_organic_raw(monkeypatch):
    monkeypatch.setattr(fetch_dataforseo, "http_post_json", lambda *a, **k: DATAFORSEO_BODY)
    items = fetch_dataforseo.DataForSeoFetcher().fetch("iit")
    assert [i["url"] for i in items] == ["https://iitm.ac.in", "https://annauniv.edu"]
    assert all(i["type"] == "organic" for i in items)


def test_dataforseo_overfetch_depth(monkeypatch):
    captured = {}

    def fake_post(url, headers, payload, **k):
        captured["depth"] = payload[0]["depth"]
        return DATAFORSEO_BODY

    monkeypatch.setattr(fetch_dataforseo, "http_post_json", fake_post)
    fetch_dataforseo.DataForSeoFetcher().fetch("iit", start=3, num=5)
    assert captured["depth"] == 7  # (3-1) + 5


def test_dataforseo_start_slice(monkeypatch):
    monkeypatch.setattr(fetch_dataforseo, "http_post_json", lambda *a, **k: DATAFORSEO_BODY)
    items = fetch_dataforseo.DataForSeoFetcher().fetch("iit", start=2, num=10)
    assert [i["url"] for i in items] == ["https://annauniv.edu"]


def test_dataforseo_null_result_returns_empty(monkeypatch):
    # DataForSEO returns "result": null on task-level errors (auth, quota, bad params).
    # Must return [] rather than raising TypeError (which would break the stdout contract).
    monkeypatch.setattr(fetch_dataforseo, "http_post_json",
                        lambda *a, **k: {"tasks": [{"result": None}]})
    items = fetch_dataforseo.DataForSeoFetcher().fetch("iit")
    assert items == []


def test_dataforseo_null_items_returns_empty(monkeypatch):
    monkeypatch.setattr(fetch_dataforseo, "http_post_json",
                        lambda *a, **k: {"tasks": [{"result": [{"items": None}]}]})
    items = fetch_dataforseo.DataForSeoFetcher().fetch("iit")
    assert items == []


def test_dataforseo_missing_credentials_raise(monkeypatch):
    monkeypatch.delenv("DATAFORSEO_LOGIN", raising=False)
    with pytest.raises(fetch_base.SearchError):
        fetch_dataforseo.DataForSeoFetcher()


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Partition path construction (t7)
# ---------------------------------------------------------------------------

def test_partition_path_uses_slug():
    from fetch import _make_output_path
    path = _make_output_path(Path("/base"), "exa",
                             "engineering college Karnataka", "2026-06-16",
                             partition=True)
    assert path == Path("/base/provider=exa/dt=2026-06-16/engineering-college-karnataka.jsonl")


def test_partition_path_no_slash_in_filename():
    from fetch import _make_output_path
    path = _make_output_path(Path("/base"), "cse", "nit/raipur.ac.in", "2026-06-16",
                             partition=True)
    assert "/" not in path.name


def test_partition_path_domain_term_unchanged():
    from fetch import _make_output_path
    path = _make_output_path(Path("/base"), "exa", "iit.ac.in", "2026-06-16",
                             partition=True)
    assert path.name == "iit.ac.in.jsonl"


def test_flat_path_uses_provider():
    from fetch import _make_output_path
    path = _make_output_path(Path("/base"), "exa", "any term", "2026-06-16",
                             partition=False)
    assert path == Path("/base/exa.jsonl")


# ---------------------------------------------------------------------------
# DuckDB integration (skip if duckdb absent)
# ---------------------------------------------------------------------------

@pytest.fixture
def duckdb_cmd():
    import shutil
    if shutil.which("duckdb") is None:
        pytest.skip("duckdb not found")
    return "duckdb"


@pytest.mark.integration
def test_duckdb_reads_partitioned_jsonl(tmp_path, duckdb_cmd):
    partition_dir = tmp_path / "provider=exa" / "dt=2026-06-16"
    partition_dir.mkdir(parents=True)
    record = {"provider": "exa", "term": "iit.ac.in",
              "fetched_at": "2026-06-16T00:00:00+00:00", "raw": {}}
    (partition_dir / "iit.ac.in.jsonl").write_text(json.dumps(record) + "\n")

    query = f"select count(*) as n from read_json_auto('{tmp_path}/provider=*/dt=*/*.jsonl')"
    result = subprocess.run([duckdb_cmd, "-c", query], capture_output=True, text=True)
    assert result.returncode == 0
    assert "1" in result.stdout


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def test_cli_no_provider_exits_1_with_json_envelope():
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "fetch.py"), "--term", "edu.in"],
        capture_output=True,
        text=True,
        cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "error"
    assert "provider" in data["error"]
