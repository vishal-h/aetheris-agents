import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("markdown")

from render_template import render_template

USE_CASE_ROOT = Path(__file__).parent.parent
DEMO = USE_CASE_ROOT / "data" / "templates" / "demo"
CSS = DEMO / "proposal_v1.css"


# --- fixtures ---

@pytest.fixture
def spec():
    return {
        "title": "B2B Project Proposal",
        "sheets": [
            {
                "name": "Line Items",
                "columns": [
                    {"name": "Item", "type": "string", "width": 12},
                    {"name": "Total", "type": "currency", "width": 12},
                ],
                "merge_ranges": [
                    {"row": 1, "col_start": 1, "col_end": 2, "value": "Line Items"}
                ],
                "rows": [
                    {"type": "header", "cells": [
                        {"value": "Item",  "bold": True, "align": "left"},
                        {"value": "Total", "bold": True, "align": "right"},
                    ]},
                    {"type": "data", "cells": [
                        {"value": "SRV-001", "bold": False, "align": "left"},
                        {"value": "3000.00", "bold": False, "align": "right"},
                    ]},
                    {"type": "aggregate", "cells": [
                        {"value": "TOTAL", "bold": True, "align": "left"},
                        {"value": 3000,    "bold": True, "align": "right"},
                    ]},
                ],
            },
        ],
    }


TEMPLATE = (
    "# {{title}}\n\n"
    "**Prepared for:** {{client_name}}\n\n"
    "## Line Items\n\n"
    "{{>Line Items}}\n"
)


# --- variable substitution ---

def test_variable_substituted(spec):
    out = render_template(TEMPLATE, {"title": "T", "client_name": "Acme Corp"}, spec, str(CSS))
    assert "Acme Corp" in out


def test_unknown_variable_left_as_is_with_warning(spec, capsys):
    out = render_template("Value: {{missing}}\n", {}, spec, str(CSS))
    assert "{{missing}}" in out
    assert "missing" in capsys.readouterr().err


# --- table partials ---

def test_table_partial_rendered(spec):
    out = render_template("{{>Line Items}}\n", {}, spec, str(CSS))
    assert "<table>" in out
    assert "SRV-001" in out
    assert "class='aggregate'" in out


def test_table_partial_case_insensitive(spec):
    # sheet name "Line Items" must match a lowercase partial token
    out = render_template("{{>line items}}\n", {}, spec, str(CSS))
    assert "<table>" in out
    assert "SRV-001" in out


def test_unknown_partial_empty_with_warning(spec, capsys):
    out = render_template("before {{>NoSuch}} after\n", {}, spec, str(CSS))
    assert "<table>" not in out
    assert "NoSuch" in capsys.readouterr().err


# --- HTML document structure ---

def test_css_link_in_head(spec):
    out = render_template(TEMPLATE, {"title": "T", "client_name": "C"}, spec, str(CSS))
    head = out.split("<body>")[0]
    assert "<link rel='stylesheet'" in head
    assert "proposal_v1.css" in head


def test_output_is_valid_html_document(spec):
    out = render_template(TEMPLATE, {"title": "T", "client_name": "C"}, spec, str(CSS))
    assert "<html>" in out
    assert "</html>" in out
    assert "<!DOCTYPE html>" in out


# --- markdown formatting ---

def test_markdown_heading(spec):
    out = render_template("# Hello\n", {}, spec, str(CSS))
    assert "<h1>Hello</h1>" in out


def test_markdown_bold(spec):
    out = render_template("**strong text**\n", {}, spec, str(CSS))
    assert "<strong>strong text</strong>" in out


# --- CLI ---

@pytest.mark.integration
def test_cli_missing_template_exits_1(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/render_template.py",
         "--template", "data/templates/demo/does_not_exist.md.template",
         "--css", "data/templates/demo/proposal_v1.css",
         "--context", "{}", "--spec", "-"],
        input="{}", capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert result.returncode == 1
    assert "error" in result.stderr


@pytest.mark.integration
def test_cli_full_pipeline(tmp_path):
    # Real pipeline doc spec (compute_doc now passes narrative through) → render.
    fetch = subprocess.run(
        [sys.executable, "scripts/fetch_data.py", "data/sample_data.csv"],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    compute = subprocess.run(
        [sys.executable, "scripts/compute_doc.py",
         "data/templates/demo/proposal_v1.json", "-"],
        input=fetch.stdout, capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(compute.stdout)

    render = subprocess.run(
        [sys.executable, "scripts/render_template.py",
         "--template", "data/templates/demo/proposal_v1.md.template",
         "--css", "data/templates/demo/proposal_v1.css",
         "--context", '{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}',
         "--spec", str(spec_path)],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT)
    )
    assert render.returncode == 0, render.stderr
    html = render.stdout
    assert "<html>" in html
    assert "Acme Corp" in html
    assert "<table>" in html       # {{>Line Items}} / {{>Summary}} rendered
    assert "proposal_v1.css" in html
