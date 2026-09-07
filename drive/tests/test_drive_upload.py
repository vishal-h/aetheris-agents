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
    result = collect_upload_files(tmp_path, "2026-04")
    assert len(result) == 1
    assert result[0][0] == "BTL_999"
    assert result[0][1].suffix == ".pdf"


def test_collect_finds_csv_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.csv").touch()
    result = collect_upload_files(tmp_path, "2026-04")
    assert len(result) == 1
    assert result[0][1].suffix == ".csv"


def test_collect_skips_html_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.html").touch()
    assert collect_upload_files(tmp_path, "2026-04") == []


def test_collect_skips_dirs_with_no_matching_files(tmp_path):
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "notes.txt").touch()
    assert collect_upload_files(tmp_path, "2026-04") == []


def test_collect_skips_non_directory_entries_at_source_root(tmp_path):
    (tmp_path / "stray.pdf").touch()
    assert collect_upload_files(tmp_path, "2026-04") == []


def test_collect_returns_sorted_by_employee_and_filename(tmp_path):
    # Corrected for bug-001: the fixture used to span months (2026-04 pdf +
    # 2026-03 csv) and assert both were returned, which encoded the defect —
    # collect_upload_files uploaded every archived month into the requested
    # month's folder. Both files are now in the requested month, so the test
    # still exercises two files per employee and asserts sort order only.
    for emp_name in ["BTL_999", "BTL_001"]:
        d = tmp_path / emp_name
        d.mkdir()
        (d / "2026-04-Payslip.pdf").touch()
        (d / "2026-04-Payslip.csv").touch()
    result = collect_upload_files(tmp_path, "2026-04")
    keys = [(emp, p.name) for emp, p in result]
    assert keys == [
        ("BTL_001", "2026-04-Payslip.csv"),
        ("BTL_001", "2026-04-Payslip.pdf"),
        ("BTL_999", "2026-04-Payslip.csv"),
        ("BTL_999", "2026-04-Payslip.pdf"),
    ]


def test_collect_returns_empty_list_for_empty_source_dir(tmp_path):
    assert collect_upload_files(tmp_path, "2026-04") == []


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
    monkeypatch.delenv("DRIVE_ROOT_FOLDER_ID", raising=False)
    monkeypatch.setattr(sys, "argv", ["drive_upload.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_when_source_dir_not_found(monkeypatch, tmp_path):
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
    monkeypatch.setattr(sys, "argv",
                        ["drive_upload.py", "--source", str(tmp_path / "no_such_dir")])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_when_no_uploadable_files(monkeypatch, tmp_path):
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_0_on_success_and_prints_summary(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.pdf").write_bytes(b"%PDF")
    (emp / "2026-04-Payslip.csv").write_text("id,name\n")
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])
    with patch(f"{MODULE}.build_service"), \
         patch(f"{MODULE}.find_or_create_folder", return_value="folder-id"), \
         patch(f"{MODULE}.upload_file", return_value="file-id"):
        with pytest.raises(SystemExit) as exc:
            main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "2 uploaded" in out
    assert "0 failed" in out


def test_main_exits_1_on_partial_failure_and_reports_employee(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
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


def test_main_uploads_only_the_requested_month(monkeypatch, tmp_path):
    """bug-001 regression: only PAYSLIP_MONTH's files reach Drive.

    Drives the ENTRYPOINT, not collect_upload_files directly — a test calling
    collect_upload_files(dir, month) cannot run against pre-fix code, so it
    could not show the defect. PAYSLIP_MONTH is the vehicle because pre-fix
    main() already reads it (argparse would exit 2 on an unknown --month).

    Asserts the exact set of uploaded filenames, not the printed count: a count
    assertion passes for the wrong reason as soon as the fixture changes.
    """
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-04")
    for emp_name in ["BTL_001", "BTL_999"]:
        d = tmp_path / emp_name
        d.mkdir()
        for month in ["2026-03", "2026-04"]:
            (d / f"{month}-Payslip.pdf").write_bytes(b"%PDF")
            (d / f"{month}-Payslip.csv").write_text("id,name\n")
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])

    with patch(f"{MODULE}.build_service"), \
         patch(f"{MODULE}.find_or_create_folder", return_value="folder-id"), \
         patch(f"{MODULE}.upload_file", return_value="file-id") as mock_upload:
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0
    uploaded = sorted(call.args[2].name for call in mock_upload.call_args_list)
    assert uploaded == [
        "2026-04-Payslip.csv",
        "2026-04-Payslip.csv",
        "2026-04-Payslip.pdf",
        "2026-04-Payslip.pdf",
    ]


def test_main_month_flag_wins_over_payslip_month_env(monkeypatch, tmp_path):
    """--month takes precedence over PAYSLIP_MONTH (review finding 2).

    Copy of test_main_uploads_only_the_requested_month with the argv line
    changed: the env var names March, the flag names April, and April is what
    reaches Drive. Pins the flag's plumbing and its precedence together — the
    behaviour an operator relies on when overriding a Rig-injected value.
    """
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.setenv("PAYSLIP_MONTH", "2026-03")
    for emp_name in ["BTL_001", "BTL_999"]:
        d = tmp_path / emp_name
        d.mkdir()
        for month in ["2026-03", "2026-04"]:
            (d / f"{month}-Payslip.pdf").write_bytes(b"%PDF")
            (d / f"{month}-Payslip.csv").write_text("id,name\n")
    monkeypatch.setattr(
        sys, "argv",
        ["drive_upload.py", "--source", str(tmp_path), "--month", "2026-04"],
    )

    with patch(f"{MODULE}.build_service"), \
         patch(f"{MODULE}.find_or_create_folder", return_value="folder-id"), \
         patch(f"{MODULE}.upload_file", return_value="file-id") as mock_upload:
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 0
    uploaded = sorted(call.args[2].name for call in mock_upload.call_args_list)
    assert uploaded == [
        "2026-04-Payslip.csv",
        "2026-04-Payslip.csv",
        "2026-04-Payslip.pdf",
        "2026-04-Payslip.pdf",
    ]


def test_main_exits_1_when_neither_month_flag_nor_env_is_set(monkeypatch, tmp_path):
    """The 'neither set' branch and its message (review finding 2, optional half)."""
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    monkeypatch.delenv("PAYSLIP_MONTH", raising=False)
    monkeypatch.setattr(sys, "argv", ["drive_upload.py", "--source", str(tmp_path)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_1_on_a_month_that_is_not_yyyy_mm(monkeypatch, tmp_path, capsys):
    """A glob in --month is rejected before it can re-open the defect (finding 3).

    entry.glob() treats the month as a pattern, so '2026-*' would re-collect every
    month and upload it into a Drive folder literally named '2026-*'. The exit must
    happen before build_service, and build_service is left unpatched so that the
    test is only green when it does.

    What reaching build_service actually costs was established by mutation, not
    assumed: with the validation disabled this test fails with an HttpError 404
    from a live request to www.googleapis.com carrying q=name = '2026-*'. It does
    NOT fail on absent credentials — a machine running this suite generally has
    GOOGLE_SERVICE_ACCOUNT set, so build_service succeeds. A live outbound request
    for a folder named '2026-*' is precisely the reach the validation prevents,
    and the green path never gets there.
    """
    monkeypatch.setenv("DRIVE_ROOT_FOLDER_ID", "root123")
    emp = tmp_path / "BTL_999"
    emp.mkdir()
    (emp / "2026-04-Payslip.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr(
        sys, "argv",
        ["drive_upload.py", "--source", str(tmp_path), "--month", "2026-*"],
    )
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "YYYY-MM" in capsys.readouterr().err
