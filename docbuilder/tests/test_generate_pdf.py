import os
import subprocess
import sys
from pathlib import Path

import pytest

weasyprint = pytest.importorskip("weasyprint")

from generate_pdf import _build_html, generate_pdf

USE_CASE_ROOT = Path(__file__).parent.parent


# --- fixture ---

@pytest.fixture
def simple_spec():
    return {
        "title": "Test Proposal",
        "template_id": "test/v1",
        "output_formats": ["pdf"],
        "sheets": [
            {
                "name": "Line Items",
                "header_row": 2,
                "columns": [
                    {"name": "Code",  "type": "string",   "width": 12},
                    {"name": "Total", "type": "currency", "width": 10},
                ],
                "merge_ranges": [
                    {"row": 1, "col_start": 1, "col_end": 2,
                     "value": "Test Proposal — Line Items"}
                ],
                "rows": [
                    {
                        "type": "header",
                        "cells": [
                            {"value": "Code",  "bold": True,  "align": "left"},
                            {"value": "Total", "bold": True,  "align": "right"},
                        ],
                    },
                    {
                        "type": "data",
                        "cells": [
                            {"value": "A-01",   "bold": False, "align": "left"},
                            {"value": "250.00", "bold": False, "align": "right"},
                        ],
                    },
                    {
                        "type": "aggregate",
                        "cells": [
                            {"value": "TOTAL", "bold": True, "align": "left"},
                            {"value": 250,     "bold": True, "align": "right"},
                        ],
                    },
                ],
            },
            {
                "name": "Summary",
                "header_row": 1,
                "columns": [
                    {"name": "Metric", "type": "string", "width": 18},
                    {"name": "Value",  "type": "string", "width": 12},
                ],
                "merge_ranges": [],
                "rows": [
                    {
                        "type": "header",
                        "cells": [
                            {"value": "Metric", "bold": True,  "align": "left"},
                            {"value": "Value",  "bold": True,  "align": "right"},
                        ],
                    },
                    {
                        "type": "data",
                        "cells": [
                            {"value": "Total Items", "bold": True,  "align": "left"},
                            {"value": 1,             "bold": False, "align": "right"},
                        ],
                    },
                ],
            },
        ],
    }


# --- HTML builder unit tests (fast, no PDF rendering) ---

def test_html_contains_title(simple_spec):
    html = _build_html(simple_spec)
    assert "<h1>Test Proposal</h1>" in html


def test_html_contains_sheet_headings(simple_spec):
    html = _build_html(simple_spec)
    assert "<h2>Line Items</h2>" in html
    assert "<h2>Summary</h2>" in html


def test_html_merge_range_as_colspan(simple_spec):
    html = _build_html(simple_spec)
    assert "colspan='2'" in html
    assert "Test Proposal &#x2014; Line Items" in html or \
           "Test Proposal — Line Items" in html


def test_html_bold_cell(simple_spec):
    html = _build_html(simple_spec)
    assert "font-weight:bold" in html


def test_html_normal_weight_cell(simple_spec):
    html = _build_html(simple_spec)
    assert "font-weight:normal" in html


def test_html_aggregate_row_class(simple_spec):
    html = _build_html(simple_spec)
    assert "class='aggregate'" in html


def test_html_right_align(simple_spec):
    html = _build_html(simple_spec)
    assert "text-align:right" in html


def test_html_escapes_special_chars():
    spec = {
        "title": "<script>alert('xss')</script>",
        "sheets": [{
            "name": "S",
            "header_row": 1,
            "columns": [{"name": "C", "type": "string", "width": 10}],
            "merge_ranges": [],
            "rows": [{
                "type": "data",
                "cells": [{"value": "<b>bold</b>", "bold": False, "align": "left"}],
            }],
        }],
    }
    html = _build_html(spec)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;" in html


# --- base_url regression tests (fast: weasyprint.HTML stubbed, no rendering) ---

class _FakeHTML:
    """Captures the kwargs generate_pdf passes to weasyprint.HTML."""
    captured = {}

    def __init__(self, string=None, base_url=None):
        _FakeHTML.captured = {"string": string, "base_url": base_url}

    def write_pdf(self, path):
        Path(path).write_bytes(b"%PDF-stub")


def test_narrative_mode_passes_base_url(tmp_path, simple_spec, monkeypatch):
    # Regression: a relative <img src="logo.png"> in the narrative template must
    # resolve against the bundle dir, so base_url is the resolved dir + os.sep
    # (trailing sep so urljoin keeps the final segment).
    import generate_pdf as gp
    simple_spec["narrative"] = {"template_file": "x.md.template", "css_file": "x.css"}
    monkeypatch.setattr(gp, "_narrative_html", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(gp.weasyprint, "HTML", _FakeHTML)

    gp.generate_pdf(simple_spec, tmp_path / "n.pdf",
                    template_dir="/some/bundle/dir", context="{}")
    base_url = _FakeHTML.captured["base_url"]
    assert base_url == str(Path("/some/bundle/dir").resolve()) + os.sep
    assert base_url.endswith(os.sep)


def test_structured_mode_base_url_none(tmp_path, simple_spec, monkeypatch):
    # No narrative → structured mode → no base_url (nothing to resolve against).
    import generate_pdf as gp
    monkeypatch.setattr(gp.weasyprint, "HTML", _FakeHTML)
    gp.generate_pdf(simple_spec, tmp_path / "s.pdf")
    assert _FakeHTML.captured["base_url"] is None


# --- PDF rendering integration tests ---

@pytest.mark.integration
def test_pdf_file_created(tmp_path, simple_spec):
    out = tmp_path / "out.pdf"
    generate_pdf(simple_spec, out)
    assert out.exists()
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_pdf_magic_bytes(tmp_path, simple_spec):
    out = tmp_path / "out.pdf"
    generate_pdf(simple_spec, out)
    assert out.read_bytes()[:4] == b"%PDF"


# --- CLI integration ---

@pytest.mark.integration
def test_cli_produces_file(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert fetch.returncode == 0
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert compute.returncode == 0
    render = subprocess.run(
        [sys.executable, "scripts/generate_pdf.py",
         "--output-dir", str(tmp_path), "--filename", "proposal"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0
    out = tmp_path / "proposal.pdf"
    assert out.exists()
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_cli_prints_output_path(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_pdf.py",
         "--output-dir", str(tmp_path), "--filename", "out"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0
    assert render.stdout.strip().endswith("out.pdf")


@pytest.mark.integration
def test_cli_pdf_magic_bytes(tmp_path):
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_pdf.py",
         "--output-dir", str(tmp_path), "--filename", "prop"],
        input=compute.stdout, capture_output=True, text=True,
        cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0
    assert (tmp_path / "prop.pdf").read_bytes()[:4] == b"%PDF"


# --- narrative mode (m2a t7) ---

DEMO = USE_CASE_ROOT / "data" / "templates" / "demo"


@pytest.mark.integration
def test_structured_mode_no_warning(tmp_path, simple_spec, capsys):
    # No narrative block → structured mode, no warning.
    out = tmp_path / "out.pdf"
    generate_pdf(simple_spec, out)
    assert out.read_bytes()[:4] == b"%PDF"
    assert capsys.readouterr().err == ""


@pytest.mark.integration
def test_narrative_present_without_template_dir_falls_back(tmp_path, simple_spec, capsys):
    # narrative present but no template_dir → structured fallback + stderr warning.
    simple_spec["narrative"] = {
        "template_file": "proposal_v1.md.template", "css_file": "proposal_v1.css"}
    out = tmp_path / "out.pdf"
    generate_pdf(simple_spec, out, template_dir=None)
    assert out.read_bytes()[:4] == b"%PDF"
    assert "template-dir" in capsys.readouterr().err


@pytest.mark.integration
def test_narrative_mode_direct(tmp_path, simple_spec):
    # narrative block + template_dir → HTML via render_template.py → PDF.
    # simple_spec has "Line Items" and "Summary" sheets, matching the demo
    # md.template's {{>Line Items}} / {{>Summary}} partials.
    simple_spec["narrative"] = {
        "template_file": "proposal_v1.md.template", "css_file": "proposal_v1.css"}
    out = tmp_path / "narr.pdf"
    generate_pdf(simple_spec, out, template_dir=str(DEMO),
                 context='{"title":"T","client_name":"Acme Corp","date":"20 Jun 2026"}')
    assert out.read_bytes()[:4] == b"%PDF"
    assert out.stat().st_size > 0


@pytest.mark.integration
def test_cli_narrative_mode(tmp_path):
    # Full pipeline: the demo doc spec carries `narrative` (t5 pass-through);
    # passing --template-dir triggers narrative rendering.
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    render = subprocess.run(
        [sys.executable, "scripts/generate_pdf.py",
         "--template-dir", "data/templates/demo",
         "--context", '{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}',
         "--output-dir", str(tmp_path), "--filename", "narr"],
        input=compute.stdout, capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0, render.stderr
    assert (tmp_path / "narr.pdf").read_bytes()[:4] == b"%PDF"
