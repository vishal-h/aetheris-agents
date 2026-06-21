"""Shared Google Drive helpers for docbuilder (m2b).

Auth + folder navigation + download, factored so `fetch_template.py` and
`list_templates.py` (and m2b's `upload_output.py`) share one implementation
rather than duplicating the Drive plumbing. Pattern mirrors
`drive/scripts/drive_download.py` (service-account auth, Shared-Drive flags);
it is *replicated* here, not imported, to keep docbuilder self-contained.

Service-account key path is read from `GOOGLE_SERVICE_ACCOUNT_FILE` (the m2b
docs name), falling back to `GOOGLE_SERVICE_ACCOUNT` (the name the existing
`drive/` scripts use). See drive-structure.md.
"""

import mimetypes
import os
import sys
from io import BytesIO
from pathlib import Path

READONLY_SCOPE = ["https://www.googleapis.com/auth/drive.readonly"]
RW_SCOPE = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"


def service_account_key_path():
    """Return the service-account JSON path, or None if neither env var is set."""
    return os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE") or os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT"
    )


def build_service(scopes=None):
    """Build an authenticated Drive v3 service. Exits 1 if no key path is set."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    if scopes is None:
        scopes = READONLY_SCOPE
    key_path = service_account_key_path()
    if not key_path:
        print(
            "GOOGLE_SERVICE_ACCOUNT_FILE (or GOOGLE_SERVICE_ACCOUNT) is not set.",
            file=sys.stderr,
        )
        sys.exit(1)
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_child(service, parent_id, name, folder_only=False):
    """Return the metadata dict {id, name, mimeType} of the child named *name*
    under *parent_id*, or None. Shared-Drive compatible."""
    q = f"name = '{name}' and trashed = false and '{parent_id}' in parents"
    if folder_only:
        q += " and mimeType = 'application/vnd.google-apps.folder'"
    resp = service.files().list(
        q=q,
        fields="files(id, name, mimeType)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    files = resp.get("files", [])
    return files[0] if files else None


def resolve_folder(service, root_id, *names):
    """Navigate root_id → names[0] → names[1] … (all folders); return the final
    folder id, or None if any segment is missing."""
    current = root_id
    for name in names:
        child = find_child(service, current, name, folder_only=True)
        if not child:
            return None
        current = child["id"]
    return current


def list_children(service, parent_id):
    """List immediate children (files + folders) of *parent_id*."""
    resp = service.files().list(
        q=f"'{parent_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=200,
    ).execute()
    return resp.get("files", [])


def download_file(service, file_id, dest_path):
    """Download a Drive file by id to dest_path (creates parent dirs)."""
    from googleapiclient.http import MediaIoBaseDownload

    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    dest.write_bytes(buf.getvalue())


def find_or_create_folder(service, parent_id, name):
    """Return the folder id for *name* under *parent_id*, creating it if absent.
    Requires the RW scope (`build_service(RW_SCOPE)`) to create."""
    existing = find_child(service, parent_id, name, folder_only=True)
    if existing:
        return existing["id"]
    folder = service.files().create(
        body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]},
        fields="id",
        supportsAllDrives=True,
    ).execute()
    return folder["id"]


def upload_file(service, folder_id, file_path):
    """Upload *file_path* into *folder_id*, updating in place if a file of the same
    name already exists (no duplicate). Returns the Drive file id."""
    from googleapiclient.http import MediaFileUpload

    path = Path(file_path)
    existing = find_child(service, folder_id, path.name)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    media = MediaFileUpload(str(path), mimetype=mime)
    if existing:
        result = service.files().update(
            fileId=existing["id"], media_body=media, fields="id",
            supportsAllDrives=True,
        ).execute()
    else:
        result = service.files().create(
            body={"name": path.name, "parents": [folder_id]},
            media_body=media, fields="id", supportsAllDrives=True,
        ).execute()
    return result["id"]


def drive_url(file_id):
    """A shareable view URL for a Drive file id."""
    return f"https://drive.google.com/file/d/{file_id}/view"
