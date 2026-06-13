import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
    )
    if samples_present:
        return
    skip = pytest.mark.skip(reason="sample files not present in data/samples/")
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip)
