"""BL-193: the Rig orchestrator's step-card error.

The orchestrator issues no outer timeout of its own, so a stalled step reaches the card
as `await_run`'s diagnosis. Prose errors reach the card unquoted.

The static tests read `agents/orchestrator.exs`. The behavioural test evaluates the
file's `step_error_text` block with `elixir`, so it is `integration`: it needs a tool
this repo does not carry.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent / "agents" / "orchestrator.exs"


def _source():
    return ORCHESTRATOR.read_text()


def test_orchestrator_has_no_outer_step_cap():
    text = _source()
    assert "Task.yield" not in text
    assert "step timed out after" not in text


def test_orchestrator_awaits_the_step_run_directly():
    assert "{:ok, outcome} <- RunHelpers.await_run(run_id, verbose: false) do" in _source()


def test_orchestrator_does_not_inspect_the_step_error():
    text = _source()
    assert "{:error, inspect(reason)}" not in text
    assert "{:error, reason} -> {:error, step_error_text.(reason)}" in text


def _step_error_text_block():
    match = re.search(r"# step_error_text:begin\n(.*?)# step_error_text:end", _source(), re.S)
    assert match, "step_error_text block markers not found in agents/orchestrator.exs"
    return match.group(1)


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("elixir") is None, reason="elixir not on PATH")
def test_step_error_text_passes_prose_through_unquoted():
    stalled = (
        "run drive-upload-x stalled: no status or event activity for 300000ms "
        "(last status: running, last event seq: 3)"
    )
    script = _step_error_text_block() + "\n".join([
        f'IO.puts(step_error_text.("{stalled}"))',
        'IO.puts(step_error_text.(%{run_id: "r", status: :failed, error: "run r failed"}))',
        "IO.puts(step_error_text.(:enoent))",
        "IO.puts(step_error_text.({:shutdown, 1}))",
    ])
    out = subprocess.run(
        ["elixir", "-e", script], capture_output=True, text=True, timeout=120, check=True
    ).stdout.splitlines()
    assert out == [stalled, "run r failed", ":enoent", "{:shutdown, 1}"]
