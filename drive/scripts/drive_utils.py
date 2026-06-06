#!/usr/bin/env python3
"""Shared utilities for Drive folder navigation."""
from datetime import datetime


def period_folder_name(payslip_month: str) -> str:
    """Convert PAYSLIP_MONTH to a period folder name.

    Examples:
        "2026-05" → "202605-may"
        "2026-04" → "202604-april"

    Raises ValueError if payslip_month is not in YYYY-MM format.
    """
    dt = datetime.strptime(payslip_month, "%Y-%m")
    return dt.strftime("%Y%m-") + dt.strftime("%B").lower()


def find_folder(service, parent_id: str, name: str) -> str | None:
    """Return the Drive folder ID for *name* under *parent_id*, or None if absent.

    Does NOT create the folder. Use this for read paths where the folder
    must already exist.

    Passes supportsAllDrives and includeItemsFromAllDrives for Shared Drive
    compatibility.
    """
    query = (
        f"name = '{name}'"
        " and trashed = false"
        " and mimeType = 'application/vnd.google-apps.folder'"
        f" and '{parent_id}' in parents"
    )
    response = service.files().list(
        q=query,
        fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()
    files = response.get("files", [])
    return files[0]["id"] if files else None


def resolve_period_folder(service, root_id: str, payslip_month: str) -> str:
    """Navigate root → payslips → {period} and return the period folder ID.

    Fails with a clear error message and sys.exit(1) if any folder in the
    path does not exist. The period folder must be created manually (or by
    the upload script) before download scripts can use it.
    """
    import sys

    period = period_folder_name(payslip_month)

    payslips_id = find_folder(service, root_id, "payslips")
    if not payslips_id:
        print(
            f"Folder 'payslips' not found under root folder {root_id}.",
            file=sys.stderr,
        )
        sys.exit(1)

    period_id = find_folder(service, payslips_id, period)
    if not period_id:
        print(
            f"Period folder '{period}' not found under payslips/. "
            f"Create the folder in Drive before running this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    return period_id
