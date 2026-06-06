import sys
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from drive.scripts.drive_download import download_file, find_payroll_file, main

MODULE = "drive.scripts.drive_download"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FILE_A = {"id": "id-apr", "name": "payroll-Apr-2026.csv", "modifiedTime": "2026-04-01T00:00:00Z"}
FILE_B = {"id": "id-mar", "name": "payroll-Mar-2026.csv", "modifiedTime": "2026-03-01T00:00:00Z"}


def make_service(files=None):
    """Return a MagicMock Drive service whose files().list().execute() returns *files*."""
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": files if files is not None else []
    }
    return service


def fake_downloader(content=b"col1,col2\nval1,val2\n"):
    """Return a side_effect for MediaIoBaseDownload that writes *content* into the buffer."""
    def _init(buf, request):
        mock_dl = MagicMock()
        buf.write(content)
        mock_dl.next_chunk.return_value = (MagicMock(), True)
        return mock_dl
    return _init


# ---------------------------------------------------------------------------
# find_payroll_file
# ---------------------------------------------------------------------------

def test_find_payroll_file_returns_most_recent_when_multiple_match():
    service = make_service(files=[FILE_A, FILE_B])
    result = find_payroll_file(service, "folder123")
    assert result["id"] == "id-apr"


def test_find_payroll_file_returns_none_when_folder_empty():
    service = make_service(files=[])
    result = find_payroll_file(service, "folder123")
    assert result is None


def test_find_payroll_file_query_includes_folder_id():
    service = make_service()
    find_payroll_file(service, "my-folder-id")
    q = service.files.return_value.list.call_args.kwargs["q"]
    assert "my-folder-id" in q


def test_find_payroll_file_query_includes_payroll_name_filter():
    service = make_service()
    find_payroll_file(service, "folder123")
    q = service.files.return_value.list.call_args.kwargs["q"]
    assert "payroll" in q


def test_find_payroll_file_query_orders_by_modified_time_desc():
    service = make_service()
    find_payroll_file(service, "folder123")
    order_by = service.files.return_value.list.call_args.kwargs["orderBy"]
    assert order_by == "modifiedTime desc"


# ---------------------------------------------------------------------------
# download_file
# ---------------------------------------------------------------------------

def test_download_file_writes_correct_bytes(tmp_path):
    service = MagicMock()
    dest = tmp_path / "payroll.csv"
    content = b"id,name\n1,Alice\n"
    with patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader(content)):
        download_file(service, "file123", str(dest))
    assert dest.read_bytes() == content


def test_download_file_creates_parent_directories(tmp_path):
    service = MagicMock()
    dest = tmp_path / "deep" / "nested" / "payroll.csv"
    with patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader()):
        download_file(service, "file123", str(dest))
    assert dest.parent.exists()


def test_download_file_calls_get_media_with_correct_file_id(tmp_path):
    service = MagicMock()
    dest = tmp_path / "payroll.csv"
    with patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader()):
        download_file(service, "target-file-id", str(dest))
    service.files.return_value.get_media.assert_called_once_with(fileId="target-file-id")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_exits_1_when_drive_folder_id_not_set(monkeypatch):
    monkeypatch.delenv("DRIVE_ROOT_FOLDER_ID", raising=False)
    monkeypatch.setattr(sys, "argv", ["drive_download.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_and_prints_stderr_when_no_file_found(monkeypatch, capsys):
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
    monkeypatch.setattr(sys, "argv", ["drive_download.py"])
    with patch(f"{MODULE}.build_service", return_value=make_service(files=[])), \
         patch("drive.scripts.drive_utils.resolve_period_folder", return_value="period-folder-id"):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    assert capsys.readouterr().err != ""


def test_main_exits_0_on_success_and_prints_dest(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
    dest = str(tmp_path / "payroll.csv")
    monkeypatch.setattr(sys, "argv", ["drive_download.py", "--dest", dest])
    with patch(f"{MODULE}.build_service", return_value=make_service(files=[FILE_A])), \
         patch("drive.scripts.drive_utils.resolve_period_folder", return_value="period-folder-id"), \
         patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader()):
        main()
    assert dest in capsys.readouterr().out
