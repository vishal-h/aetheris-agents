import pytest
from drive.scripts.drive_utils import period_folder_name


def test_may_2026():
    assert period_folder_name("2026-05") == "202605-may"


def test_april_2026():
    assert period_folder_name("2026-04") == "202604-april"


def test_january():
    assert period_folder_name("2026-01") == "202601-january"


def test_december():
    assert period_folder_name("2025-12") == "202512-december"


def test_invalid_format():
    with pytest.raises(ValueError):
        period_folder_name("05-2026")
