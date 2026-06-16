"""Stage-2 map tests: pure transforms, no network and no mocking needed."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from edux_record import EduxRecord
from mappers import display_snippet, map_envelope

USE_CASE_ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"

GWS_CSE_COLUMNS = {"link", "title", "snippet", "image", "search_term", "metatags", "status", "enrichment"}


def _env(provider, raw):
    return {"provider": provider, "term": "edu.in", "fetched_at": "2026-06-14T09:00:00+00:00", "raw": raw}


# ---------------------------------------------------------------------------
# All-provider shape tests
# ---------------------------------------------------------------------------

def test_all_providers_map_to_same_edux_shape():
    cases = [
        _env("cse", {"title": "IIT", "link": "https://iitm.ac.in",
                     "pagemap": {"cse_image": [{"src": "https://iitm.ac.in/l.png"}],
                                 "metatags": [{"og:title": "IIT"}]}}),
        _env("serper", {"title": "IIT", "link": "https://iitm.ac.in", "snippet": "tech", "position": 1}),
        _env("dataforseo", {"title": "IIT", "url": "https://iitm.ac.in", "description": "tech", "rank_absolute": 1}),
        _env("exa", {"title": "IIT", "url": "https://iitm.ac.in", "text": "tech ...", "score": 0.9}),
    ]
    for env in cases:
        rec = map_envelope(env)
        assert rec.link == "https://iitm.ac.in"
        assert rec.search_term == "edu.in"
        assert rec.source_provider == env["provider"]
        assert rec.enrichment == {}


# ---------------------------------------------------------------------------
# Exa: full text + snippet derivation
# ---------------------------------------------------------------------------

def test_exa_keeps_full_text_and_derives_snippet():
    rec = map_envelope(_env("exa", {"url": "https://x.edu", "text": "y " * 400}))
    assert rec.text == "y " * 400
    assert rec.snippet.endswith("…")
    assert len(rec.snippet) <= 301


def test_serp_providers_have_no_full_text():
    rec = map_envelope(_env("serper", {"link": "https://x.edu", "snippet": "s"}))
    assert rec.text is None and rec.snippet == "s"


# ---------------------------------------------------------------------------
# to_gws_cse: columns, _edux provenance, no text
# ---------------------------------------------------------------------------

def test_to_gws_cse_columns_and_excludes_full_text():
    rec = map_envelope(_env("exa", {"url": "https://x.edu", "text": "full body text"}))
    row = rec.to_gws_cse()
    assert set(row) == GWS_CSE_COLUMNS
    assert "text" not in row
    assert row["metatags"][-1]["_edux"]["source_provider"] == "exa"
    assert row["enrichment"] == {}


def test_to_gws_cse_does_not_mutate_original_metatags():
    rec = map_envelope(_env("cse", {"link": "https://x.edu",
                                    "pagemap": {"metatags": [{"og:title": "X"}]}}))
    original_len = len(rec.metatags)
    rec.to_gws_cse()
    assert len(rec.metatags) == original_len  # to_gws_cse() must not mutate the record


# ---------------------------------------------------------------------------
# to_dict roundtrip
# ---------------------------------------------------------------------------

def test_roundtrip_dict_reconstructs_record():
    rec = map_envelope(_env("exa", {"url": "https://x.edu", "text": "hello", "score": 0.5}))
    assert EduxRecord(**rec.to_dict()) == rec


# ---------------------------------------------------------------------------
# display_snippet
# ---------------------------------------------------------------------------

def test_display_snippet_passthrough_short():
    assert display_snippet("short") == "short"
    assert display_snippet(None) is None


# ---------------------------------------------------------------------------
# CSE pagemap
# ---------------------------------------------------------------------------

def test_cse_populates_image_and_metatags_from_pagemap():
    rec = map_envelope(_env("cse", {
        "title": "IIT", "link": "https://iitm.ac.in",
        "pagemap": {"cse_image": [{"src": "https://iitm.ac.in/l.png"}],
                    "metatags": [{"og:title": "IIT", "og:type": "website"}]},
    }))
    assert rec.image == "https://iitm.ac.in/l.png"
    assert rec.metatags == [{"og:title": "IIT", "og:type": "website"}]


def test_cse_no_pagemap_returns_none_image_empty_metatags():
    rec = map_envelope(_env("cse", {"title": "IIT", "link": "https://iitm.ac.in"}))
    assert rec.image is None
    assert rec.metatags == []


# ---------------------------------------------------------------------------
# Unknown provider
# ---------------------------------------------------------------------------

def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="no mapper"):
        map_envelope({"provider": "bing", "raw": {}})


# ---------------------------------------------------------------------------
# Fixture-based tests (committed fixtures)
# ---------------------------------------------------------------------------

def test_cse_fixture_maps_image_and_metatags():
    lines = FIXTURES.joinpath("cse.raw.jsonl").read_text().splitlines()
    rec = map_envelope(json.loads(lines[0]))
    assert rec.image is not None
    assert rec.metatags  # real pagemap metatags present


def test_exa_fixture_maps_full_text():
    lines = FIXTURES.joinpath("exa.raw.jsonl").read_text().splitlines()
    rec = map_envelope(json.loads(lines[0]))
    assert rec.text is not None
    assert rec.source_provider == "exa"


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------

def test_map_cli_cse_fixture(tmp_path):
    out = tmp_path / "cse.jsonl"
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "map.py"),
         "--in", str(FIXTURES / "cse.raw.jsonl"),
         "--out", str(out)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "ok"
    assert data["mapped"] == 2
    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert records[0]["image"] is not None
    assert records[0]["metatags"]


def test_map_cli_missing_input_exits_1():
    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "map.py"),
         "--in", "/tmp/nonexistent_eduloka.jsonl"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "error"
