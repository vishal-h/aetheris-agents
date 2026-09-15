#!/usr/bin/env python3
"""Quarantine payslip objects misplaced in one Drive period folder (BL-194).

An object is misplaced iff its filename's month prefix differs from the name of the
period folder that contains it. Two invocations, never one:

  drive_quarantine.py --period YYYY-MM --report FILE     # dry run: lists, tests, writes FILE
  drive_quarantine.py --execute --report FILE            # moves exactly FILE's pairs

The dry run holds a read-only Drive scope and calls nothing that writes, so it cannot
move anything. `--execute` re-checks each reported object before moving it, moves it
into `payslip-quarantine/<period>/<employee>/` beside the payslips root (outside the
tree being cleaned), re-runs the test over the period folder, and writes
`FILE.executed.json`. Nothing is deleted. An object with no month prefix (payroll.csv)
is unclassifiable: reported, never moved.

stdout is a one-line JSON summary; errors go to stderr. Exit 0 on success, 1 on any
error, any skipped pair, or a period folder still failing the test after execution.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure aetheris-agents/ is on the path when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

READONLY_SCOPE = ["https://www.googleapis.com/auth/drive.readonly"]
WRITE_SCOPE = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"
QUARANTINE_FOLDER = "payslip-quarantine"
PERIOD_RE = re.compile(r"\d{4}-(0[1-9]|1[0-2])")
MONTH_PREFIX_RE = re.compile(r"^(\d{4}-\d{2})-")


def classify(name, period):
    """Return 'clean', 'misplaced', or 'unclassifiable' for an object in *period*'s folder."""
    match = MONTH_PREFIX_RE.match(name)
    if match is None:
        return "unclassifiable"
    return "clean" if match.group(1) == period else "misplaced"


def list_children(service, parent_id):
    """Every non-trashed child of *parent_id*, across all result pages."""
    items, token = [], None
    while True:
        response = service.files().list(
            q=f"'{parent_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=1000,
            pageToken=token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives",
        ).execute()
        items.extend(response.get("files") or [])
        token = response.get("nextPageToken")
        if not token:
            return items


def root_parent(service, root_id):
    """The payslips root's own parent, where the quarantine is placed; None if it has none."""
    meta = service.files().get(fileId=root_id, fields="parents", supportsAllDrives=True).execute()
    parents = meta.get("parents") or []
    return parents[0] if parents else None


def scan(service, root_id, period):
    """Apply the identity test to every object under *period*'s folder; return the report body."""
    from drive.scripts.drive_utils import find_folder

    period_id = find_folder(service, root_id, period)
    if period_id is None:
        raise LookupError(f"Period folder '{period}' not found under the payslips root.")
    quarantine_parent_id = root_parent(service, root_id)
    if quarantine_parent_id is None:
        raise LookupError("The payslips root has no parent folder, so no quarantine can sit outside it.")

    objects = []  # (object, source parent id, employee or None)
    for entry in list_children(service, period_id):
        if entry.get("mimeType") != FOLDER_MIME:
            objects.append((entry, period_id, None))
            continue
        for child in list_children(service, entry["id"]):
            objects.append((child, entry["id"], entry["name"]))

    counts = {"objects": 0, "clean": 0, "misplaced": 0, "unclassifiable": 0}
    pairs, unclassifiable = [], []
    for obj, source_parent_id, employee in sorted(objects, key=lambda o: (o[2] or "", o[0]["name"])):
        counts["objects"] += 1
        source = "/".join(p for p in (period, employee, obj["name"]) if p)
        verdict = "unclassifiable" if obj.get("mimeType") == FOLDER_MIME else classify(obj["name"], period)
        counts[verdict] += 1
        if verdict == "misplaced":
            pairs.append({
                "file_id": obj["id"],
                "name": obj["name"],
                "employee": employee,
                "source_parent_id": source_parent_id,
                "source": source,
                "quarantine": "/".join(p for p in (QUARANTINE_FOLDER, period, employee, obj["name"]) if p),
            })
        elif verdict == "unclassifiable":
            unclassifiable.append({"source": source, "mimeType": obj.get("mimeType")})

    return {
        "period": period,
        "root_folder_id": root_id,
        "period_folder_id": period_id,
        "quarantine_parent_id": quarantine_parent_id,
        "counts": counts,
        "pairs": pairs,
        "unclassifiable": unclassifiable,
    }


def execute(service, report):
    """Move the report's pairs into quarantine; return (moved, skipped)."""
    from drive.scripts.drive_upload import find_or_create_folder

    period = report["period"]
    quarantine_root = find_or_create_folder(service, report["quarantine_parent_id"], QUARANTINE_FOLDER)
    quarantine_period = find_or_create_folder(service, quarantine_root, period)
    employee_folders = {}
    moved, skipped = [], []

    for pair in report["pairs"]:
        meta = service.files().get(
            fileId=pair["file_id"], fields="id, name, parents, trashed", supportsAllDrives=True
        ).execute()
        still_matches = (
            not meta.get("trashed")
            and pair["source_parent_id"] in (meta.get("parents") or [])
            and meta.get("name") == pair["name"]
            and classify(meta["name"], period) == "misplaced"
        )
        if not still_matches:
            skipped.append({"source": pair["source"], "reason": "object no longer matches the dry-run report"})
            continue

        destination = quarantine_period
        if pair["employee"]:
            if pair["employee"] not in employee_folders:
                employee_folders[pair["employee"]] = find_or_create_folder(
                    service, quarantine_period, pair["employee"]
                )
            destination = employee_folders[pair["employee"]]

        service.files().update(
            fileId=pair["file_id"],
            addParents=destination,
            removeParents=pair["source_parent_id"],
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()
        moved.append({"source": pair["source"], "quarantine": pair["quarantine"]})

    return moved, skipped


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Quarantine payslip objects misplaced in a Drive period folder.")
    parser.add_argument("--period", help="Period folder to test, YYYY-MM (dry run only)")
    parser.add_argument("--report", required=True, help="Dry-run report path (written by the dry run, read by --execute)")
    parser.add_argument("--execute", action="store_true", help="Move the pairs the report names")
    args = parser.parse_args(argv)

    from drive.scripts.drive_download import build_service

    report_path = Path(args.report)

    if args.execute:
        if args.period:
            print("--period is read from the report under --execute; do not pass it.", file=sys.stderr)
            return 1
        executed_path = Path(f"{args.report}.executed.json")
        if executed_path.exists():
            print(f"Report already executed: {executed_path} exists.", file=sys.stderr)
            return 1
        try:
            report = json.loads(report_path.read_text())
        except (OSError, ValueError) as exc:
            print(f"Cannot read dry-run report {report_path}: {exc}", file=sys.stderr)
            return 1
        if report.get("mode") != "dry-run":
            print(f"{report_path} is not a dry-run report.", file=sys.stderr)
            return 1

        service = build_service(scopes=WRITE_SCOPE)
        moved, skipped = execute(service, report)
        after = scan(service, report["root_folder_id"], report["period"])
        record = {
            "mode": "executed",
            "executed_at": _now(),
            "report": str(report_path),
            "period": report["period"],
            "moved": moved,
            "skipped": skipped,
            "counts_after": after["counts"],
        }
        executed_path.write_text(json.dumps(record, indent=2) + "\n")
        ok = not skipped and after["counts"]["misplaced"] == 0
        print(json.dumps({
            "status": "ok" if ok else "partial",
            "mode": "executed",
            "period": report["period"],
            "moved": len(moved),
            "skipped": len(skipped),
            "misplaced_after": after["counts"]["misplaced"],
            "record": str(executed_path),
        }))
        return 0 if ok else 1

    if not args.period or not PERIOD_RE.fullmatch(args.period):
        print(f"--period must be YYYY-MM, got: {args.period!r}", file=sys.stderr)
        return 1
    root_id = os.environ.get("DRIVE_ROOT_FOLDER_ID")
    if not root_id:
        print("DRIVE_ROOT_FOLDER_ID environment variable is not set.", file=sys.stderr)
        return 1
    if report_path.exists():
        print(f"Report {report_path} already exists; a reviewed report is never overwritten.", file=sys.stderr)
        return 1

    service = build_service(scopes=READONLY_SCOPE)
    try:
        body = scan(service, root_id, args.period)
    except LookupError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    report = {"mode": "dry-run", "generated_at": _now(), **body}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "ok", "mode": "dry-run", "period": args.period,
                      "report": str(report_path), **body["counts"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
