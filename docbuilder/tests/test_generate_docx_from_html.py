"""Tests for generate_docx_from_html.py (m6 t2) — the Pandoc HTML→DOCX wrapper.

Two layers:
- Pure-unit error paths (pandoc missing → FileNotFoundError; pandoc non-zero →
  RuntimeError) via monkeypatch — no pandoc needed.
- Real conversion + CLI, marked `integration` and skipped when pandoc is absent.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from generate_docx_from_html import html_to_docx

USE_CASE_ROOT = Path(__file__).parent.parent
SCRIPT = USE_CASE_ROOT / "scripts" / "generate_docx_from_html.py"
PANDOC = shutil.which("pandoc") is not None
needs_pandoc = pytest.mark.skipif(not PANDOC, reason="pandoc not installed")


# --- pure-unit error paths (no pandoc required) ---

def test_pandoc_missing_raises_filenotfound(tmp_path, monkeypatch):
    monkeypatch.setattr("generate_docx_from_html.shutil.which", lambda _: None)
    with pytest.raises(FileNotFoundError):
        html_to_docx(tmp_path / "in.html", tmp_path / "out.docx")


def test_pandoc_nonzero_raises_runtimeerror(tmp_path, monkeypatch):
    monkeypatch.setattr("generate_docx_from_html.shutil.which", lambda _: "/usr/bin/pandoc")

    class _FakeResult:
        returncode = 1
        stderr = "boom: bad input"

    monkeypatch.setattr(
        "generate_docx_from_html.subprocess.run", lambda *a, **k: _FakeResult()
    )
    with pytest.raises(RuntimeError) as exc:
        html_to_docx(tmp_path / "in.html", tmp_path / "out.docx")
    assert "boom: bad input" in str(exc.value)


# --- real conversion + CLI (require pandoc) ---

@needs_pandoc
@pytest.mark.integration
def test_html_to_docx_produces_nonempty_file(tmp_path):
    html = tmp_path / "in.html"
    html.write_text("<h1>Test</h1><p>Hello World</p>", encoding="utf-8")
    out = tmp_path / "out.docx"
    html_to_docx(html, out)               # default Bitloka reference doc
    assert out.exists() and out.stat().st_size > 0


@needs_pandoc
@pytest.mark.integration
def test_explicit_reference_doc(tmp_path):
    ref = USE_CASE_ROOT / "data" / "templates" / "bitloka" / "reference.docx"
    assert ref.exists(), "committed reference.docx should exist"
    html = tmp_path / "in.html"
    html.write_text("<h1>Title</h1><p>Body</p>", encoding="utf-8")
    out = tmp_path / "out.docx"
    html_to_docx(html, out, reference_doc=str(ref))
    assert out.stat().st_size > 0


@needs_pandoc
@pytest.mark.integration
def test_cli_output_created(tmp_path):
    html = tmp_path / "in.html"
    html.write_text("<p>CLI</p>", encoding="utf-8")
    out = tmp_path / "out.docx"
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(html), "--output", str(out)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert r.returncode == 0, r.stderr
    assert out.exists() and out.stat().st_size > 0
    assert r.stdout.strip() == str(out)          # prints the output path


@needs_pandoc
@pytest.mark.integration
def test_cli_bad_input_exit1(tmp_path):
    out = tmp_path / "out.docx"
    r = subprocess.run(
        [sys.executable, str(SCRIPT),
         "--input", str(tmp_path / "nope.html"), "--output", str(out)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT),
    )
    assert r.returncode == 1
    assert "error" in r.stderr
