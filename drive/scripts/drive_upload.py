#!/usr/bin/env python3
"""Upload per-employee payslip PDFs and CSVs from payslip/output/ to Google Drive."""
import argparse
import os
import sys
from datetime import datetime
from itertools import groupby
from pathlib import Path

# Ensure aetheris-agents/ is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from googleapiclient.http import MediaFileUpload

from drive.scripts.drive_download import build_service

UPLOAD_SCOPE = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"
MIME_TYPES = {".pdf": "application/pdf", ".csv": "text/csv"}


def collect_upload_files(source_dir, month):
    """Walk source_dir and return uploadable payslip files for *month*.

    For each direct subdirectory (employee), collects the files matching
    {month}-Payslip.pdf and {month}-Payslip.csv. Skips HTML files and any
    non-directory entries at the source root.

    *month* is an exact "YYYY-MM" string, not a pattern: payslip/output/ is a
    per-employee archive holding every month generated to date, so a glob with
    no month predicate uploads all of them into the requested month's folder.
    Matches the exact-month path construction in email/scripts/email_send.py.

    Returns a list of (employee_id, path) tuples sorted by
    (employee_id, path.name).
    """
    source = Path(source_dir)
    results = []
    for entry in source.iterdir():
        if not entry.is_dir():
            continue
        for pattern in (f"{month}-Payslip.pdf", f"{month}-Payslip.csv"):
            for path in entry.glob(pattern):
                results.append((entry.name, path))
    results.sort(key=lambda t: (t[0], t[1].name))
    return results


def find_or_create_folder(service, parent_id, name):
    """Return the Drive folder ID for *name* under *parent_id*, creating it if absent.

    Query scopes to the given parent and folder name. Returns the existing
    folder ID if found, otherwise creates the folder and returns the new ID.
    """
    query = (
        f"name = '{name}'"
        " and trashed = false"
        f" and mimeType = '{FOLDER_MIME}'"
        f" and '{parent_id}' in parents"
    )
    response = service.files().list(
        q=query, fields="files(id)", supportsAllDrives=True,
        includeItemsFromAllDrives=True, corpora="allDrives",
    ).execute()
    files = response.get("files", [])
    if files:
        return files[0]["id"]
    folder = (
        service.files()
        .create(
            body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]},
            fields="id",
            supportsAllDrives=True,
        )
        .execute()
    )
    return folder["id"]


def upload_file(service, folder_id, file_path):
    """Upload file_path into folder_id, updating in place if it already exists.

    Uses files.update when a file with the same name exists (no duplicate
    created), files.create otherwise. Returns the Drive file ID.
    """
    query = (
        f"name = '{file_path.name}'"
        " and trashed = false"
        f" and '{folder_id}' in parents"
    )
    response = service.files().list(
        q=query, fields="files(id)", supportsAllDrives=True,
        includeItemsFromAllDrives=True, corpora="allDrives",
    ).execute()
    existing = response.get("files", [])
    mime = MIME_TYPES.get(file_path.suffix, "application/octet-stream")
    media = MediaFileUpload(str(file_path), mimetype=mime)
    if existing:
        result = (
            service.files()
            .update(fileId=existing[0]["id"], media_body=media, fields="id",
                    supportsAllDrives=True)
            .execute()
        )
    else:
        result = (
            service.files()
            .create(
                body={"name": file_path.name, "parents": [folder_id]},
                media_body=media,
                fields="id",
                supportsAllDrives=True,
            )
            .execute()
        )
    return result["id"]


def main():
    """Walk payslip/output/, find or create per-employee Drive folders, and upload."""
    parser = argparse.ArgumentParser(
        description="Upload payslip PDFs and CSVs to Google Drive."
    )
    parser.add_argument(
        "--source",
        default="payslip/output/",
        help="Local source directory (default: payslip/output/)",
    )
    parser.add_argument(
        "--month",
        default=None,
        help="Payslip month to upload, YYYY-MM (default: PAYSLIP_MONTH env var)",
    )
    args = parser.parse_args()

    from drive.scripts.drive_utils import period_folder_name

    root_id = os.environ.get("DRIVE_ROOT_FOLDER_ID")
    if not root_id:
        print("DRIVE_ROOT_FOLDER_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    payslip_month = args.month
    if payslip_month is None:
        payslip_month = os.environ.get("PAYSLIP_MONTH")
    if not payslip_month:
        print("--month or PAYSLIP_MONTH env var is required.", file=sys.stderr)
        sys.exit(1)

    # The month is used as a glob pattern by collect_upload_files and as a Drive
    # folder name by period_folder_name, so an unvalidated value re-opens the very
    # defect this script was fixed for: '2026-*' would re-collect every month and
    # upload them into a folder literally named '2026-*'. Validated the way
    # email/scripts/email_send.py:220 does, but exiting 1 rather than raising.
    try:
        datetime.strptime(payslip_month, "%Y-%m")
    except ValueError:
        print(
            f"--month/PAYSLIP_MONTH must be YYYY-MM, got: {payslip_month!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    source = Path(args.source)
    if not source.exists():
        print(f"Source directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    files = collect_upload_files(source, payslip_month)
    if not files:
        print("No uploadable files found.", file=sys.stderr)
        sys.exit(1)

    service = build_service(scopes=UPLOAD_SCOPE)
    period = period_folder_name(payslip_month)
    folder_id = find_or_create_folder(service, root_id, period)

    uploaded = 0
    failed = []

    # collect_upload_files returns results sorted by (employee_id, path.name),
    # so groupby produces one contiguous group per employee.
    for employee_id, group in groupby(files, key=lambda t: t[0]):
        paths = [path for _, path in group]
        try:
            emp_folder_id = find_or_create_folder(service, folder_id, employee_id)
            for path in paths:
                upload_file(service, emp_folder_id, path)
                uploaded += 1
        except Exception as e:
            print(f"Failed {employee_id}: {e}", file=sys.stderr)
            failed.append(employee_id)

    print(f"{uploaded} uploaded, {len(failed)} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
