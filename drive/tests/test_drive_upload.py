import sys
from unittest.mock import MagicMock, patch

import pytest

from drive.scripts.drive_upload import (
    collect_upload_files,
    find_or_create_folder,
    main,
    upload_file,
)

MODULE = "drive.scripts.drive_upload"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_service(list_files=None, create_id="created-id"):
    """Return a MagicMock Drive service with configurable list/create responses."""
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": list_files if list_files is not None else []
    }
    service.files.return_value.create.return_value.execute.return_value = {"id": create_id}
    service.files.return_value.update.return_value.execute.return_value = {"id": "updated-id"}
    return service


# ---------------------------------------------------------------------------
# collect_upload_files
# ---------------------------------------------------------------------------

def test_collect_finds_pdf_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.pdf").touch()
    result = collect_upload_files(tmp_path)
    assert len(result) == 1
    assert result[0][0] == "BTL_999"
    assert result[0][1].suffix == ".pdf"


def test_collect_finds_csv_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.csv").touch()
    result = collect_upload_files(tmp_path)
    assert len(result) == 1
    assert result[0][1].suffix == ".csv"


def test_collect_skips_html_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.html").touch()
    assert collect_upload_files(tmp_path) == []


def test_collect_skips_dirs_with_no_matching_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "notes.txt").touch()
    assert collect_upload_files(tmp_path) == []


def test_collect_skips_non_directory_entries_at_source_root(tmp_path):
    (tmp_path / "stray.pdf").touch()
    assert collect_upload_files(tmp_path) == []


def test_collect_returns_sorted_by_employee_and_filename(tmp_path):
    for emp_name in ["BTL_999", "BTL_001"]:
        d = tmp_path / emp_name
        d.mkdir()
        (d / "2026-04-Payslip.pdf").touch()
        (d / "2026-03-Payslip.csv").touch()
    result = collect_upload_files(tmp_path)
    keys = [(emp, p.name) for emp, p in result]
    assert keys == sorted(keys)


def test_collect_returns_empty_list_for_empty_source_dir(tmp_path):
    assert collect_upload_files(tmp_path) == []


# ---------------------------------------------------------------------------
# find_or_create_folder
# ---------------------------------------------------------------------------

def test_find_or_create_folder_returns_existing_id():
    service = make_service(list_files=[{"id": "existing-folder-id"}])
    result = find_or_create_folder(service, "parent-id", "BTL_999")
    assert result == "existing-folder-id"
    service.files.return_value.create.assert_not_called()


def test_find_or_create_folder_creates_when_not_found():
    service = make_service(list_files=[], create_id="new-folder-id")
    result = find_or_create_folder(service, "parent-id", "BTL_999")
    assert result == "new-folder-id"
    service.files.return_value.create.assert_called_once()


def test_find_or_create_folder_query_includes_parent_id_and_name():
    service = make_service(list_files=[], create_id="x")
    find_or_create_folder(service, "parent-abc", "BTL_999")
    q = service.files.return_value.list.call_args.kwargs["q"]
    assert "parent-abc" in q
    assert "BTL_999" in q


# ---------------------------------------------------------------------------
# upload_file
# ---------------------------------------------------------------------------

def test_upload_file_creates_when_not_exists(tmp_path):
    service = make_service(list_files=[], create_id="new-file-id")
    path = tmp_path / "2026-04-Payslip.pdf"
    path.write_bytes(b"%PDF")
    with patch(f"{MODULE}.MediaFileUpload"):
        result = upload_file(service, "folder-id", path)
    assert result == "new-file-id"
    service.files.return_value.create.assert_called_once()
    service.files.return_value.update.assert_not_called()


def test_upload_file_updates_when_file_already_exists(tmp_path):
    service = make_service(list_files=[{"id": "existing-file-id"}])
    path = tmp_path / "2026-04-Payslip.pdf"
    path.write_bytes(b"%PDF")
    with patch(f"{MODULE}.MediaFileUpload"):
        result = upload_file(service, "folder-id", path)
    assert result == "updated-id"
    service.files.return_value.update.assert_called_once()
    service.files.return_value.create.assert_not_called()


def test_upload_file_uses_pdf_mime_type(tmp_path):
    service = make_service(list_files=[])
    path = tmp_path / "2026-04-Payslip.pdf"
    path.write_bytes(b"%PDF")
    with patch(f"{MODULE}.MediaFileUpload") as mock_mfu:
        upload_file(service, "folder-id", path)
    mock_mfu.assert_called_once_with(str(path), mimetype="application/pdf")


def test_upload_file_uses_csv_mime_type(tmp_path):
    service = make_service(list_files=[])
    path = tmp_path / "2026-04-Payslip.csv"
    path.write_text("id,name\n")
    with patch(f"{MODULE}.MediaFileUpload") as mock_mfu:
        upload_file(service, "folder-id", path)
    mock_mfu.assert_called_once_with(str(path), mimetype="text/csv")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def test_main_exits_1_when_output_folder_id_not_set(monkeypatch):
    monkeypatch.delenv("DRIVE_OUTPUT_FOLDER_ID", raising=False)
    monkeypatch.setattr(sys, "argv", ["drive_upload.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_when_source_dir_not_found(monkeypatch, tmp_path):
    monkeypatch.setenv("DRIVE_OUTPUT_FOLDER_ID", "folder123")
    monkeypatch.setattr(sys, "argv",
                        ["drive_upload.py", "--source", str(tmp_path / "no_such_dir")])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_when_no_uploadable_files(monkeypatch, tmp_path):
    monkeypatch.setenv("DRIVE_OUTPUT_FOLDER_ID", "folder123")
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_0_on_success_and_prints_summary(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DRIVE_OUTPUT_FOLDER_ID", "folder123")
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.pdf").write_bytes(b"%PDF")
    (emp / "2026-04-Payslip.csv").write_text("id,name\n")
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])
    with patch(f"{MODULE}.build_service"), \
         patch(f"{MODULE}.find_or_create_folder", return_value="emp-folder-id"), \
         patch(f"{MODULE}.upload_file", return_value="file-id"):
        main()
    out = capsys.readouterr().out
    assert "2 uploaded" in out
    assert "0 failed" in out


def test_main_exits_1_on_partial_failure_and_reports_employee(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DRIVE_OUTPUT_FOLDER_ID", "folder123")
    for emp_name in ["BTL_998", "BTL_999"]:
        d = tmp_path / emp_name
        d.mkdir()
        (d / "2026-04-Payslip.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])

    def failing_find_or_create(service, parent_id, name):
        if name == "BTL_999":
            raise Exception("API error")
        return "ok-folder-id"

    with patch(f"{MODULE}.build_service"), \
         patch(f"{MODULE}.find_or_create_folder", side_effect=failing_find_or_create), \
         patch(f"{MODULE}.upload_file", return_value="file-id"):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 1
    assert "BTL_999" in capsys.readouterr().err
