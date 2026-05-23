#!/usr/bin/env python3
"""Upload per-employee payslip PDFs and CSVs from payslip/output/ to Google Drive."""
import argparse
import os
import sys
from itertools import groupby
from pathlib import Path

# Ensure aetheris-agents/ is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from googleapiclient.http import MediaFileUpload

from drive.scripts.drive_download import build_service

UPLOAD_SCOPE = ["https://www.googleapis.com/auth/drive.file"]
FOLDER_MIME = "application/vnd.google-apps.folder"
MIME_TYPES = {".pdf": "application/pdf", ".csv": "text/csv"}


def collect_upload_files(source_dir):
    """Walk source_dir and return uploadable payslip files.

    For each direct subdirectory (employee), collects all files matching
    *-Payslip.pdf and *-Payslip.csv. Skips HTML files and any non-directory
    entries at the source root.

    Returns a list of (employee_id, path) tuples sorted by
    (employee_id, path.name).
    """
    source = Path(source_dir)
    results = []
    for entry in source.iterdir():
        if not entry.is_dir():
            continue
        for pattern in ("*-Payslip.pdf", "*-Payslip.csv"):
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
        includeItemsFromAllDrives=True,
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
        includeItemsFromAllDrives=True,
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
    args = parser.parse_args()

    folder_id = os.environ.get("DRIVE_OUTPUT_FOLDER_ID")
    if not folder_id:
        print("DRIVE_OUTPUT_FOLDER_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    source = Path(args.source)
    if not source.exists():
        print(f"Source directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    files = collect_upload_files(source)
    if not files:
        print("No uploadable files found.", file=sys.stderr)
        sys.exit(1)

    service = build_service(scopes=UPLOAD_SCOPE)

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
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
