"""Stage-1 fetch tests (t1: cse + exa; t2 adds serper + dataforseo).

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
import fetch_exa

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _creds(monkeypatch):
    for k in ("GWS_CSE_API_KEY", "GWS_CSE_ENGINE_ID", "EXA_API_KEY"):
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
    assert data["ok"] is False
    assert "provider" in data["error"]
