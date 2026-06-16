import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requiring external resources (DB, API)"
    )
