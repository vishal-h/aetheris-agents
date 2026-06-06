#!/usr/bin/env python3
"""Download the payroll CSV from a Google Drive folder to a local path."""
import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

# Ensure aetheris-agents/ is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def build_service(scopes=None):
    """Build and return an authenticated Drive v3 service.

    Reads the service account key path from GOOGLE_SERVICE_ACCOUNT.
    Exits 1 with a clear message if the variable is not set.
    Defaults to drive.readonly scope; pass *scopes* to override.
    """
    if scopes is None:
        scopes = SCOPES
    key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT")
    if not key_path:
        print("GOOGLE_SERVICE_ACCOUNT environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_payroll_file(service, folder_id):
    """Query the Drive folder for the most recently modified file whose name contains 'payroll'.

    Query includes: name contains 'payroll', trashed = false,
    mimeType != 'application/vnd.google-apps.folder'.
    Orders by modifiedTime desc.

    Returns the first result's metadata dict, or None if no match.
    """
    query = (
        f"'{folder_id}' in parents"
        " and name contains 'payroll'"
        " and trashed = false"
        " and mimeType != 'application/vnd.google-apps.folder'"
    )
    response = (
        service.files()
        .list(
            q=query,
            orderBy="modifiedTime desc",
            fields="files(id, name, modifiedTime)",
            pageSize=10,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = response.get("files", [])
    return files[0] if files else None


def download_file(service, file_id, dest_path):
    """Download a Drive file by ID to dest_path.

    Downloads into a BytesIO buffer via MediaIoBaseDownload, then writes
    atomically to dest_path. Creates parent directories as needed.
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(buf.getvalue())


def main():
    """Parse arguments, find the payroll file in Drive, and download it."""
    parser = argparse.ArgumentParser(
        description="Download payroll CSV from Google Drive."
    )
    parser.add_argument(
        "--dest",
        default="payslip/data/payroll.csv",
        help="Local destination path (default: payslip/data/payroll.csv)",
    )
    args = parser.parse_args()

    from drive.scripts.drive_utils import resolve_period_folder

    root_id = os.environ.get("DRIVE_ROOT_FOLDER_ID")
    if not root_id:
        print("DRIVE_ROOT_FOLDER_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    payslip_month = os.environ.get("PAYSLIP_MONTH")
    if not payslip_month:
        print("PAYSLIP_MONTH environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    service = build_service()
    folder_id = resolve_period_folder(service, root_id, payslip_month)

    file_meta = find_payroll_file(service, folder_id)
    if file_meta is None:
        print("No payroll file found in Drive folder.", file=sys.stderr)
        sys.exit(1)

    download_file(service, file_meta["id"], args.dest)
    print(f"Downloaded: {file_meta['name']} (modified {file_meta['modifiedTime']})")
    print(f"Saved to: {args.dest}")


if __name__ == "__main__":
    main()
