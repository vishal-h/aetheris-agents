import pytest
from drive.scripts.drive_utils import period_folder_name


def test_may_2026():
    assert period_folder_name("2026-05") == "2026-05"


def test_april_2026():
    assert period_folder_name("2026-04") == "2026-04"


def test_january():
    assert period_folder_name("2026-01") == "2026-01"


def test_december():
    assert period_folder_name("2025-12") == "2025-12"
