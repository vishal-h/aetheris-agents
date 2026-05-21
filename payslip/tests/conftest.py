import shutil
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: marks tests requiring wkhtmltopdf and gs to be installed"
    )


def pytest_collection_modifyitems(config, items):
    if shutil.which("wkhtmltopdf") is None or shutil.which("gs") is None:
        skip = pytest.mark.skip(reason="wkhtmltopdf not installed")
        for item in items:
            if item.get_closest_marker("integration"):
                item.add_marker(skip)
