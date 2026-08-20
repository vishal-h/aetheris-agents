"""boxy-pipeline's adoption of the per-step run record (ds t2).

**This file is deselected from the whole-suite gate, and what that does and does not mean
is stated rather than left to be inferred.** boxy-pipeline is the registry's one `dormant`
row (`docs/use-cases.md`, status set 2026-08-16, "Paused pending the client"), so like
every other test in this directory it carries `pytestmark = pytest.mark.dormant`. The
marker is not optional: `tests/test_use_case_registry.py`'s marker-equals-registry arm
asserts that the marked set equals the `dormant` rows, so landing this file unmarked would
turn that arm red.

**It was run at ds t2, targeted, and passed** — `python3 -m pytest
boxy-pipeline/tests/test_run_record_adoption.py -q -m dormant` → 3 passed. So the claim
"written and never executed" would be false, and is not made. What it is NOT evidence for
is the boxy *pipeline*: no order form was produced through `write_order_form`, which needs
openpyxl and a template, and the full `-m dormant` set has never finished under either of
the two caps recorded against it (see `pytest.ini`'s condition for return, and BL-159 for
what un-pausing costs). These assertions exercise the record seam and the module constant;
they do not exercise boxy.

`run_id` is `None` throughout, and that is the point rather than an omission: boxy-pipeline
has no agent file, no sprint leg and no `tools.json`, so no harness run id reaches any of
its scripts by any route. `null` is a real value here.
"""

import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.dormant

USE_CASE_ROOT = Path(__file__).parent.parent
RECORD_RELPATH = Path("data") / "run-records.json"


@pytest.fixture
def record_root(tmp_path, monkeypatch):
    root = tmp_path / "record-root"
    (root / "data").mkdir(parents=True)
    monkeypatch.setenv("AETHERIS_RUN_RECORD_ROOT", str(root))
    return root


def _records(record_root):
    return json.loads((record_root / RECORD_RELPATH).read_text())


def test_order_formatter_declares_its_step():
    """The step name is a module constant, so the record does not depend on argv."""
    sys.path.insert(0, str(USE_CASE_ROOT / "scripts"))
    import order_formatter

    assert order_formatter.STEP == "order_formatter"


def test_the_run_id_flag_exists_and_defaults_to_none():
    """The seam is in place for the day boxy acquires an agent; nothing passes it today."""
    sys.path.insert(0, str(USE_CASE_ROOT / "scripts"))
    import argparse
    import order_formatter

    parser = argparse.ArgumentParser()
    # Mirrors the flag as declared in order_formatter.main().
    parser.add_argument("--run-id", default=None)
    assert parser.parse_args([]).run_id is None
    assert parser.parse_args(["--run-id", "x"]).run_id == "x"


def test_a_written_order_form_is_attested_with_a_null_run_id(record_root, tmp_path):
    """The shape boxy's record takes. Specification: this does not run while dormant."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from run_record import run_record

    artifact = record_root / "output" / "SO86708_order_form.xlsx"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"xlsx-bytes")

    with run_record(record_root, None, "order_formatter") as rec:
        rec.add(artifact)

    entry, = _records(record_root)
    assert entry["run_id"] is None
    assert entry["step"] == "order_formatter"
    assert "attested_at" in entry
    assert entry["artifacts"][0]["path"] == "output/SO86708_order_form.xlsx"
    assert entry["artifacts"][0]["bytes"] == 10
