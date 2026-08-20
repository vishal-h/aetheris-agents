"""Upload generated output files to a tenant's Drive output folder.

Uploads each local file to `{tenant}/output/` under the `docbuilder` Shared Drive
(creating the tenant + output folders if absent), and prints a JSON array of
`{filename, drive_file_id, drive_url}`.

Drive id from `--drive-id` or `DRIVE_DOCBUILDER_ID`; service-account auth via
`GOOGLE_SERVICE_ACCOUNT_FILE` / `GOOGLE_SERVICE_ACCOUNT` (see `_drive.py`).
Exit 1 if the Drive id is absent or any upload fails. See docs/drive-structure.md.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import _drive
from run_record import run_record, use_case_root_for  # noqa: E402

#: The upload is its own step with its own entry, rather than being folded into the render
#: step's. Until ds t2 the docbuilder run log was written at PHASE D2 and PHASE E wrote
#: `output/uploaded.json` afterwards, so the record predated an artifact it implied
#: (BL-151, filed by ds t2). One entry per step is what makes that expressible.
STEP = "upload_output"


def upload_outputs(tenant, files, drive_id):
    """Upload *files* to `{tenant}/output/`; return a list of
    {filename, drive_file_id, drive_url} dicts. Requires RW scope."""
    service = _drive.build_service(_drive.RW_SCOPE)
    tenant_folder = _drive.find_or_create_folder(service, drive_id, tenant)
    output_folder = _drive.find_or_create_folder(service, tenant_folder, "output")

    results = []
    for f in files:
        path = Path(f)
        if not path.exists():
            raise FileNotFoundError(f"file not found: {f}")
        file_id = _drive.upload_file(service, output_folder, path)
        results.append({
            "filename": path.name,
            "drive_file_id": file_id,
            "drive_url": _drive.drive_url(file_id),
        })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--files", nargs="+", required=True,
                        help="local file paths to upload")
    parser.add_argument("--drive-id", default=None,
                        help="Drive Shared Drive root id (falls back to DRIVE_DOCBUILDER_ID)")
    parser.add_argument("--output", default=None,
                        help="write the JSON result to FILE and print only the path")
    parser.add_argument("--run-id", default=None,
                        help="harness run id; omitted when no run reaches this script, in "
                             "which case the record carries run_id null")
    args = parser.parse_args()

    drive_id = args.drive_id or os.environ.get("DRIVE_DOCBUILDER_ID")
    if not drive_id:
        print(json.dumps({"status": "error",
                          "error": "no Drive id (--drive-id or DRIVE_DOCBUILDER_ID)"}),
              file=sys.stderr)
        sys.exit(1)

    try:
        with run_record(use_case_root_for(__file__), args.run_id, STEP) as rec:
            results = upload_outputs(args.tenant, args.files, drive_id)

            out = json.dumps(results)
            if args.output:
                Path(args.output).write_text(out, encoding="utf-8")
                rec.add(args.output)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(args.output if args.output else out)


if __name__ == "__main__":
    main()
