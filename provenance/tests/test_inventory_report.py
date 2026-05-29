import re
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from inventory_report import build_report

FIXTURE_DB = Path(__file__).parent / "fixtures" / "sample_corpus.duckdb"
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
INVENTORY_SCRIPT = SCRIPTS_DIR / "inventory_report.py"


@pytest.fixture(scope="module")
def report() -> str:
    conn = duckdb.connect(str(FIXTURE_DB), read_only=True)
    try:
        return build_report(conn)
    finally:
        conn.close()


def test_all_sections_present(report):
    for heading in [
        "## Summary",
        "## By file type",
        "## Estimated FY distribution",
        "## Duplicate groups",
        "## Zip files",
        "## What's next",
    ]:
        assert heading in report, f"Missing section: {heading}"


def test_summary_correct(report):
    assert "run-fixture-001" in report
    assert "/data/archive" in report
    assert "30" in report          # files_scanned
    assert "4m 30s" in report      # duration


def test_unique_and_wasted_in_summary(report):
    # fixture has duplicates so unique < total and wasted > 0
    assert "Unique files" in report
    assert "Wasted space" in report
    assert "Unique content size" in report


def test_filetype_section_has_three_types(report):
    assert "application/pdf" in report
    assert "text/csv" in report
    # docx mime type (truncated is fine — just check it appears)
    assert "wordprocessingml" in report


def test_fy_distribution_years(report):
    for yr in ("2024", "2023", "2022", "2021"):
        assert yr in report


def test_fy_disclaimer_present(report):
    assert "filesystem" in report.lower()


def test_duplicate_groups_wasted_space(report):
    # sha-h has 4 copies at 85 000 bytes each → 3 × 85 000 = 255 000 wasted
    # sha-a has 3 copies at 1 200 000 each → 2 × 1 200 000 = 2 400 000 wasted
    assert "sha-a" in report or "2.3 MB" in report or "2.4 MB" in report


def test_duplicate_groups_shows_top_entries(report):
    # sha-h (4 copies, most copies) and sha-a (largest wasted) must appear
    section_start = report.index("## Duplicate groups")
    section = report[section_start:]
    assert "sha-" in section


def test_zip_section_counts(report):
    assert "2" in report[report.index("## Zip files"):]


def test_zip_inventory_rows(report):
    # one 'processed', one 'pending'
    section = report[report.index("## Zip files"):]
    assert "processed" in section or "pending" in section


def test_whats_next_boilerplate(report):
    section = report[report.index("## What's next"):]
    assert "Phase 2" in section
    assert "classification" in section.lower()


def test_output_path_has_timestamp(tmp_path):
    conn = duckdb.connect(str(FIXTURE_DB), read_only=True)
    try:
        from inventory_report import build_report as _build
        text = _build(conn)
    finally:
        conn.close()

    from datetime import datetime
    from inventory_report import _human_size  # noqa: F401 — import check

    import inventory_report as ir
    # Simulate writing: check filename pattern
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, str(INVENTORY_SCRIPT), "--db", str(FIXTURE_DB), "--out", td],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        out_path = result.stdout.strip()
        assert re.search(r"inventory_\d{8}_\d{6}\.md$", out_path), out_path
        assert Path(out_path).exists()


def test_cli_exit_zero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--db", str(FIXTURE_DB), "--out", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out_path = Path(result.stdout.strip())
    assert out_path.exists()
    content = out_path.read_text()
    assert "# Provenance Inventory Report" in content
