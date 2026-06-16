"""Tests for list_terms.py."""

import json
import os
import subprocess
import sys
from pathlib import Path

from list_terms import load_terms, slug_term

USE_CASE_ROOT = Path(__file__).parent.parent
SCRIPT = USE_CASE_ROOT / "scripts" / "list_terms.py"


# ---------------------------------------------------------------------------
# slug_term
# ---------------------------------------------------------------------------

def test_slug_domain_unchanged():
    assert slug_term("iit.ac.in") == "iit.ac.in"

def test_slug_spaces_become_dashes():
    assert slug_term("engineering college Karnataka") == "engineering-college-karnataka"

def test_slug_slash_replaced():
    assert slug_term("nit/raipur.ac.in") == "nit-raipur.ac.in"

def test_slug_colon_replaced():
    assert slug_term("term:value") == "term-value"

def test_slug_multiple_spaces_collapsed():
    assert slug_term("a  b") == "a-b"

def test_slug_strips_leading_trailing():
    assert slug_term("  iit.ac.in  ") == "iit.ac.in"

def test_slug_empty_returns_term():
    assert slug_term("") == "term"
    assert slug_term("---") == "term"

def test_slug_no_slash_in_result():
    slug = slug_term("any/slash:colon term")
    assert "/" not in slug
    assert "\\" not in slug


# ---------------------------------------------------------------------------
# load_terms
# ---------------------------------------------------------------------------

def test_load_filters_blank_lines(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text("iit.ac.in\n\nnit.ac.in\n")
    assert load_terms(f) == ["iit.ac.in", "nit.ac.in"]


def test_load_filters_comments(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text("# header comment\niit.ac.in\n# inline\n")
    assert load_terms(f) == ["iit.ac.in"]


def test_load_empty_file(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text("")
    assert load_terms(f) == []


def test_load_strips_whitespace(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text("  iit.ac.in  \n  nit.ac.in\n")
    assert load_terms(f) == ["iit.ac.in", "nit.ac.in"]


def test_cli_default_terms_file():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "ok"
    assert data["count"] >= 1
    assert isinstance(data["terms"], list)
    assert isinstance(data["slugs"], list)
    assert len(data["slugs"]) == len(data["terms"])


def test_cli_custom_terms_file(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text("iit.ac.in\nnit.ac.in\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--terms-file", str(f)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["terms"] == ["iit.ac.in", "nit.ac.in"]
    assert data["count"] == 2


def test_cli_env_var_override(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text("iisc.ac.in\n")
    env = {**os.environ, "EDUX_TERMS_FILE": str(f)}
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), env=env,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["terms"] == ["iisc.ac.in"]


def test_cli_missing_file_exits_1():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--terms-file", "/tmp/nonexistent_terms_eduloka.txt"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "error"
    assert "not found" in data["error"]
