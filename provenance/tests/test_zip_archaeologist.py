"""
Tests for zip_archaeologist.exs — eval check only.

The live end-to-end test (real zip → extract → process → DB) is covered by
the orchestrator acceptance test in m4-004.
"""

import os
import subprocess
from pathlib import Path

import pytest

AGENT  = Path(__file__).parent.parent / "agents" / "zip_archaeologist.exs"
AETHERIS = Path(__file__).parent.parent.parent.parent / "aetheris"


def test_agent_evaluates_without_error(tmp_path):
    if not AETHERIS.exists():
        pytest.skip("aetheris repo not found")

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{AGENT}")'],
        cwd=str(AETHERIS),
        env={**os.environ,
             "PROVENANCE_DB_PATH": str(tmp_path / "corpus.duckdb"),
             "STAGING_PATH": str(tmp_path / "zip_staging")},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
