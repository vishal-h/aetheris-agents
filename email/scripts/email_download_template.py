#!/usr/bin/env python3
"""Download payslip_email_template.html from the Shared Drive output folder."""
import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

# Ensure aetheris-agents/ is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from googleapiclient.http import MediaIoBaseDownload

from drive.scripts.drive_download import build_service

TEMPLATE_NAME = "payslip_email_template.html"
READONLY_SCOPE = ["https://www.googleapis.com/auth/drive.readonly"]


def find_template_file(service, folder_id):
    """Search for payslip_email_template.html in the given Shared Drive folder.

    Query matches an exact filename, excludes trashed items, excludes folders,
    and scopes to the given parent. Passes supportsAllDrives and
    includeItemsFromAllDrives so the query works on Shared Drives.

    Returns the first result's metadata dict, or None if not found.
    """
    query = (
        f"name = '{TEMPLATE_NAME}'"
        " and trashed = false"
        " and mimeType != 'application/vnd.google-apps.folder'"
        f" and '{folder_id}' in parents"
    )
    response = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    files = response.get("files", [])
    return files[0] if files else None


def download_template(service, file_id, dest_path):
    """Download the template file by ID and write it to dest_path.

    Downloads into a BytesIO buffer via MediaIoBaseDownload, then writes
    atomically to dest_path. Creates parent directories as needed.
    Passes supportsAllDrives=True to files().get_media().
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(buf.getvalue())


def main():
    """Parse arguments, locate the template in Drive, and download it."""
    parser = argparse.ArgumentParser(
        description="Download payslip email template from Google Drive."
    )
    parser.add_argument(
        "--dest",
        default="email/data/payslip_email_template.html",
        help="Local destination path (default: email/data/payslip_email_template.html)",
    )
    args = parser.parse_args()

    folder_id = os.environ.get("DRIVE_OUTPUT_FOLDER_ID")
    if not folder_id:
        print("DRIVE_OUTPUT_FOLDER_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    service = build_service(scopes=READONLY_SCOPE)

    file_meta = find_template_file(service, folder_id)
    if file_meta is None:
        print(f"{TEMPLATE_NAME} not found in Drive folder.", file=sys.stderr)
        sys.exit(1)

    download_template(service, file_meta["id"], args.dest)
    print(f"Downloaded: {file_meta['name']}")
    print(f"Saved to: {args.dest}")


if __name__ == "__main__":
    main()
