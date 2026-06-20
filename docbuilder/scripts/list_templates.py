"""List the template catalogue for a tenant.

Reads the tenant's `catalogue.json` — listing doc types and per-variant metadata
(versions, output formats, base-file/narrative availability) — and prints it to stdout.
Foundation for LLM template selection in m2b.

Source resolution:
- When `DRIVE_DOCBUILDER_ID` (or `--drive-id`) is set, reads
  `{tenant}/templates/catalogue.json` from the `docbuilder` Shared Drive.
- Otherwise reads the flat local file `{templates_dir}/{tenant}/catalogue.json`
  (m2a behaviour; what the unit/CLI tests exercise).

Exit 1 if the catalogue is missing. See docs/drive-structure.md.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import _drive


def load_catalogue(templates_dir, tenant_id):
    """Return the parsed catalogue dict from the flat local file.

    Raises FileNotFoundError if the catalogue does not exist.
    """
    path = Path(templates_dir) / tenant_id / "catalogue.json"
    if not path.exists():
        raise FileNotFoundError(
            f"catalogue not found for tenant '{tenant_id}': {path}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalogue_drive(tenant_id, drive_id):
    """Download and parse `{tenant}/templates/catalogue.json` from Drive."""
    service = _drive.build_service()
    templates_folder = _drive.resolve_folder(service, drive_id, tenant_id, "templates")
    if not templates_folder:
        raise FileNotFoundError(
            f"templates folder not found for tenant '{tenant_id}' in Drive {drive_id}"
        )
    meta = _drive.find_child(service, templates_folder, "catalogue.json")
    if not meta:
        raise FileNotFoundError(
            f"catalogue.json not found for tenant '{tenant_id}' in Drive"
        )
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "catalogue.json"
        _drive.download_file(service, meta["id"], dest)
        return json.loads(dest.read_text(encoding="utf-8"))


def resolve_catalogue(tenant_id, templates_dir, drive_id):
    """Drive-backed when a drive_id is present, else the flat local file."""
    if drive_id:
        return load_catalogue_drive(tenant_id, drive_id)
    return load_catalogue(templates_dir, tenant_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True, help="tenant id")
    parser.add_argument("--templates-dir", default="data/templates",
                        help="local templates root for the flat-file path (default: data/templates)")
    parser.add_argument("--drive-id", default=None,
                        help="Drive Shared Drive root id (falls back to DRIVE_DOCBUILDER_ID)")
    args = parser.parse_args()

    drive_id = args.drive_id or os.environ.get("DRIVE_DOCBUILDER_ID")

    try:
        catalogue = resolve_catalogue(args.tenant, args.templates_dir, drive_id)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(catalogue, indent=2))


if __name__ == "__main__":
    main()
