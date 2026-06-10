import sys
from unittest.mock import MagicMock, patch

import pytest

from email_download_template import download_template, find_template_file, main

MODULE = "email_download_template"

FILE_META = {"id": "template-file-id", "name": "payslip_email_template.html"}


def make_service(files=None):
    """Return a MagicMock Drive service whose files().list().execute() returns *files*."""
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": files if files is not None else []
    }
    return service


def fake_downloader(content=b"<html>template</html>"):
    """Return a side_effect for MediaIoBaseDownload that writes *content* into the buffer."""
    def _init(buf, request):
        mock_dl = MagicMock()
        buf.write(content)
        mock_dl.next_chunk.return_value = (MagicMock(), True)
        return mock_dl
    return _init


# ---------------------------------------------------------------------------
# find_template_file
# ---------------------------------------------------------------------------

def test_find_template_file_returns_metadata_when_found():
    service = make_service(files=[FILE_META])
    result = find_template_file(service, "folder-123")
    assert result == FILE_META


def test_find_template_file_returns_none_when_not_found():
    service = make_service(files=[])
    result = find_template_file(service, "folder-123")
    assert result is None


def test_find_template_file_query_includes_exact_filename():
    service = make_service()
    find_template_file(service, "folder-123")
    q = service.files.return_value.list.call_args.kwargs["q"]
    assert "payslip_email_template.html" in q


def test_find_template_file_passes_supports_all_drives():
    service = make_service()
    find_template_file(service, "folder-123")
    kwargs = service.files.return_value.list.call_args.kwargs
    assert kwargs.get("supportsAllDrives") is True
    assert kwargs.get("includeItemsFromAllDrives") is True


# ---------------------------------------------------------------------------
# download_template
# ---------------------------------------------------------------------------

def test_download_template_writes_correct_bytes(tmp_path):
    service = MagicMock()
    dest = tmp_path / "payslip_email_template.html"
    content = b"<html><body>Hello {{employee_name}}</body></html>"
    with patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader(content)):
        download_template(service, "file-id", str(dest))
    assert dest.read_bytes() == content


def test_download_template_calls_get_media_with_correct_file_id(tmp_path):
    service = MagicMock()
    dest = tmp_path / "payslip_email_template.html"
    with patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader()):
        download_template(service, "target-file-id", str(dest))
    service.files.return_value.get_media.assert_called_once_with(fileId="target-file-id")


def test_download_template_creates_parent_directories(tmp_path):
    service = MagicMock()
    dest = tmp_path / "deep" / "nested" / "payslip_email_template.html"
    with patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader()):
        download_template(service, "file-id", str(dest))
    assert dest.parent.exists()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_exits_1_when_templates_folder_id_not_set(monkeypatch):
    monkeypatch.delenv("DRIVE_TEMPLATES_FOLDER_ID", raising=False)
    monkeypatch.setattr(sys, "argv", ["email_download_template.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_with_stderr_when_template_not_found(monkeypatch, capsys):
    monkeypatch.setenv("DRIVE_TEMPLATES_FOLDER_ID", "templates-folder-id")
    monkeypatch.setattr(sys, "argv", ["email_download_template.py"])
    with patch(f"{MODULE}.build_service", return_value=MagicMock()), \
         patch(f"{MODULE}.find_template_file", return_value=None):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    assert capsys.readouterr().err != ""


def test_main_exits_0_on_success_and_prints_dest(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DRIVE_TEMPLATES_FOLDER_ID", "templates-folder-id")
    dest = str(tmp_path / "payslip_email_template.html")
    monkeypatch.setattr(sys, "argv", ["email_download_template.py", "--dest", dest])
    with patch(f"{MODULE}.build_service", return_value=MagicMock()), \
         patch(f"{MODULE}.find_template_file", return_value=FILE_META), \
         patch(f"{MODULE}.MediaIoBaseDownload", side_effect=fake_downloader()):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert dest in out


def test_template_file_not_found(monkeypatch, capsys):
    monkeypatch.setenv("DRIVE_TEMPLATES_FOLDER_ID", "templates-folder-id")
    monkeypatch.setattr(sys, "argv", ["email_download_template.py"])
    with patch(f"{MODULE}.build_service", return_value=MagicMock()), \
         patch(f"{MODULE}.find_template_file", return_value=None):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    assert "not found in templates folder" in capsys.readouterr().err


def test_payslip_month_not_required(monkeypatch, tmp_path):
    monkeypatch.setenv("DRIVE_TEMPLATES_FOLDER_ID", "templates-folder-id")
    monkeypatch.delenv("PAYSLIP_MONTH", raising=False)
    dest = str(tmp_path / "payslip_email_template.html")
    monkeypatch.setattr(sys, "argv", ["email_download_template.py", "--dest", dest])
    with patch(f"{MODULE}.build_service", return_value=MagicMock()), \
         patch(f"{MODULE}.find_template_file", return_value=FILE_META), \
         patch(f"{MODULE}.download_template"):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0
