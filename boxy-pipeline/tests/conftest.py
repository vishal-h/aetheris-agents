import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
# boxy-pipeline/main.py is imported by test_pipeline.py; the use-case root is only on
# sys.path when pytest is invoked from inside boxy-pipeline/, so put it there explicitly.
sys.path.insert(0, str(Path(__file__).parent.parent))

_SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: requires sample data files in data/samples/",
    )


def pytest_collection_modifyitems(config, items):
    samples_present = (
        (_SAMPLES_DIR / "Joey-_Kitchen_2D_Plans_V2.pdf").exists()
        and (_SAMPLES_DIR / "Joey-_Kitchen_Plan_V2.pdf").exists()
        and (_SAMPLES_DIR / "Updated_Boxy_MSRP_Sales_Order_Form.xlsx").exists()
        and (_SAMPLES_DIR / "SO86708_Aria_Joey.pdf").exists()
    )
    if samples_present:
        return
    skip = pytest.mark.skip(reason="sample files not present in data/samples/")
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _isolate_run_records(tmp_path_factory, monkeypatch):
    """Keep every test's run record out of the checked-out tree (ds t2).

    `run_record.use_case_root_for` anchors the record to the use case, not to the cwd or to
    a `--output-dir`, so without this a test driving a producer writes
    `<use_case>/data/run-records.json` in the working copy. That is gitignored, so it would
    never be caught by `git status` — a check blind to the thing it would need to see.
    """
    root = tmp_path_factory.mktemp("run-records")
    (root / "data").mkdir(exist_ok=True)
    monkeypatch.setenv("AETHERIS_RUN_RECORD_ROOT", str(root))
