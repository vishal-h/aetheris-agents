"""Fetch a template bundle (the whole {doc_type}/{version}/ subfolder) for a tenant.

Wide fetch: one call downloads every asset in the version folder
(JSON config + optional base files + narrative template/CSS) to a local cache
dir, and prints the cache dir path to stdout.

- When a Drive id is available (`--drive-id` or `DRIVE_DOCBUILDER_ID`), the bundle
  is downloaded from the `docbuilder` Shared Drive:
  `{tenant}/templates/{doc_type}/{version}/` → `{cache_dir}/{tenant}/{doc_type}/{version}/`.
- When no Drive id is set, falls back to the local committed bundle at
  `data/templates/{tenant}/{doc_type}/{version}/` (m2a behaviour for local dev/tests).

Exit 1 if neither source resolves. See docs/drive-structure.md.
"""

import argparse
import json
import sys
from pathlib import Path

import _drive

KNOWN_EXTS = ("json", "docx", "xlsx", "md.template", "css")


def local_bundle_path(templates_dir, tenant, doc_type, version):
    """Return the nested local bundle Path: {templates_dir}/{tenant}/{doc_type}/{version}/."""
    return Path(templates_dir) / tenant / doc_type / version


def fetch_from_drive(drive_id, tenant, doc_type, version, cache_dir):
    """Download the version subfolder from Drive into the cache; return the cache path."""
    service = _drive.build_service()
    folder_id = _drive.resolve_folder(
        service, drive_id, tenant, "templates", doc_type, version
    )
    if not folder_id:
        raise FileNotFoundError(
            f"Drive bundle not found: {tenant}/templates/{doc_type}/{version}"
        )
    dest = Path(cache_dir) / tenant / doc_type / version
    dest.mkdir(parents=True, exist_ok=True)
    files = [f for f in _drive.list_children(service, folder_id)
             if f["mimeType"] != "application/vnd.google-apps.folder"]
    if not files:
        raise FileNotFoundError(
            f"Drive bundle is empty: {tenant}/templates/{doc_type}/{version}"
        )
    for f in files:
        _drive.download_file(service, f["id"], dest / f["name"])
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--doc-type", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--cache-dir", default="output/template_cache")
    parser.add_argument("--templates-dir", default="data/templates",
                        help="local fallback templates root (default: data/templates)")
    parser.add_argument("--drive-id", default=None,
                        help="Drive Shared Drive root id (falls back to DRIVE_DOCBUILDER_ID)")
    parser.add_argument("--output", default=None,
                        help="write the resolved cache/bundle path to FILE instead of stdout")
    args = parser.parse_args()

    import os
    drive_id = args.drive_id or os.environ.get("DRIVE_DOCBUILDER_ID")

    try:
        if drive_id:
            path = fetch_from_drive(
                drive_id, args.tenant, args.doc_type, args.version, args.cache_dir
            )
        else:
            path = local_bundle_path(
                args.templates_dir, args.tenant, args.doc_type, args.version
            )
            if not path.is_dir():
                raise FileNotFoundError(
                    f"no Drive id (DRIVE_DOCBUILDER_ID) and local bundle missing: {path}"
                )
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    out = str(path)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(args.output)
    else:
        print(out)


if __name__ == "__main__":
    main()
