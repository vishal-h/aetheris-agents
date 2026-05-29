"""
Tests for search_agent.exs — eval check only.

Live search queries against a real corpus are covered by m5-003 validate_search.
"""

import os
import subprocess
from pathlib import Path

import pytest

AGENT    = Path(__file__).parent.parent / "agents" / "search_agent.exs"
AETHERIS = Path(__file__).parent.parent.parent.parent / "aetheris"


def test_agent_evaluates_without_error(tmp_path):
    if not AETHERIS.exists():
        pytest.skip("aetheris repo not found")

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{AGENT}")'],
        cwd=str(AETHERIS),
        env={**os.environ,
             "PROVENANCE_DB_PATH": str(tmp_path / "corpus.duckdb"),
             "CORPUS_SEARCH_MCP_ENABLED": "true"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_agent_evaluates_without_mcp_enabled(tmp_path):
    """Agent must evaluate cleanly even when CORPUS_SEARCH_MCP_ENABLED is unset."""
    if not AETHERIS.exists():
        pytest.skip("aetheris repo not found")

    env = {**os.environ, "PROVENANCE_DB_PATH": str(tmp_path / "corpus.duckdb")}
    env.pop("CORPUS_SEARCH_MCP_ENABLED", None)

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{AGENT}")'],
        cwd=str(AETHERIS),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_agent_raises_without_db_path():
    """Agent must raise at eval time when PROVENANCE_DB_PATH is unset."""
    if not AETHERIS.exists():
        pytest.skip("aetheris repo not found")

    env = {k: v for k, v in os.environ.items() if k != "PROVENANCE_DB_PATH"}

    result = subprocess.run(
        ["mix", "run", "--eval", f'Code.eval_file("{AGENT}")'],
        cwd=str(AETHERIS),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
