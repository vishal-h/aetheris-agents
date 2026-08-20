import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


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
