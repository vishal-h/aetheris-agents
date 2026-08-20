import shutil
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests requiring wkhtmltopdf and gs to be installed"
    )


def pytest_collection_modifyitems(config, items):
    if shutil.which("wkhtmltopdf") is None:
        skip = pytest.mark.skip(reason="wkhtmltopdf not installed")
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
