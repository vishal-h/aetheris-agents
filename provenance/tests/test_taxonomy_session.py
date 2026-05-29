"""Tests for taxonomy_session.py — non-interactive mode and output structure."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import taxonomy_session as ts

SCRIPT = Path(__file__).parent.parent / "scripts" / "taxonomy_session.py"


# ---------------------------------------------------------------------------
# _render output structure
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rendered() -> str:
    return ts.run_non_interactive()


def test_rendered_has_clients_table(rendered):
    assert "| acme |" in rendered
    assert "| globex |" in rendered
    assert "| initech |" in rendered


def test_rendered_has_fy_convention(rendered):
    assert "## Financial year convention" in rendered
    assert "FY{YYYY}" in rendered
    assert "April–March" in rendered


def test_rendered_has_all_doc_types(rendered):
    for dt in ["tax", "legal", "accounts", "correspondence", "other"]:
        assert f"### {dt}" in rendered


def test_rendered_has_classification_rules(rendered):
    assert "## Classification rules (for the agent)" in rendered
    assert "confident (>0.85)" in rendered
    assert "Cap confidence at 0.65" in rendered


def test_rendered_has_naming_patterns(rendered):
    assert "## Naming patterns" in rendered
    assert "Filenames include client name: yes" in rendered
    assert "DRAFT" in rendered


def test_rendered_has_edge_cases(rendered):
    assert "## Edge cases" in rendered
    assert "CONFIDENTIAL" in rendered
    assert "/personal/" in rendered


def test_rendered_has_generated_header(rendered):
    assert "# Provenance Document Taxonomy" in rendered
    assert "Generated:" in rendered
    assert "Auditor:" in rendered


def test_rendered_within_token_budget(rendered):
    assert len(rendered) < ts.TOKEN_WARN_CHARS, (
        f"Non-interactive template is {len(rendered)} chars — exceeds 8 000 char budget"
    )


# ---------------------------------------------------------------------------
# CLI — --non-interactive writes a file
# ---------------------------------------------------------------------------

def test_cli_non_interactive_writes_file(tmp_path):
    out = tmp_path / "taxonomy.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--non-interactive", "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out.exists()
    content = out.read_text()
    assert "# Provenance Document Taxonomy" in content


def test_cli_non_interactive_prints_output_path(tmp_path):
    out = tmp_path / "taxonomy.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--non-interactive", "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(out) in result.stdout.strip()


def test_cli_non_interactive_creates_parent_dirs(tmp_path):
    out = tmp_path / "agents" / "taxonomy.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--non-interactive", "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert out.exists()


# ---------------------------------------------------------------------------
# _render edge cases
# ---------------------------------------------------------------------------

def test_render_isolated_clients_included():
    output = ts._render(
        auditor="Test",
        clients=[("X", "X Corp", "", "")],
        isolated="X",
        fy_type="fy",
        fy_label="FY{YYYY}",
        fy_boundary="April",
        doc_types={"tax": ts.DOC_TYPE_DEFAULTS["tax"]},
        includes_client="y",
        includes_year="y",
        affixes="",
        language="English",
        multi_client="",
        confidential="",
        path_rules="",
    )
    assert "**Isolated clients**" in output
    assert "X" in output


def test_render_calendar_year():
    output = ts._render(
        auditor="Test",
        clients=[],
        isolated="",
        fy_type="cal",
        fy_label="YYYY",
        fy_boundary="January",
        doc_types={},
        includes_client="n",
        includes_year="n",
        affixes="",
        language="English",
        multi_client="",
        confidential="",
        path_rules="",
    )
    assert "January–December" in output
    assert "Filenames include client name: no" in output


def test_render_no_edge_case_values_shows_placeholder():
    output = ts._render(
        auditor="Test",
        clients=[],
        isolated="",
        fy_type="fy",
        fy_label="FY{YYYY}",
        fy_boundary="April",
        doc_types={},
        includes_client="y",
        includes_year="y",
        affixes="",
        language="English",
        multi_client="",
        confidential="",
        path_rules="",
    )
    assert "_(none specified)_" in output
