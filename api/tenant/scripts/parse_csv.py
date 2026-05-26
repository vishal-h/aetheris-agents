#!/usr/bin/env python3
"""parse_csv.py <csv_path>

Reads a student enrollment CSV and outputs a JSON array of normalised row dicts.
Dates normalised to ISO8601 (YYYY-MM-DD). Empty strings become null.
Exit 0 on success, exit 1 on error.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


DATE_INPUT_FORMATS = ["%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]


def parse_date(value: str) -> str | None:
    if not value:
        return None
    for fmt in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value.strip() or None


def normalise(value: str) -> str | None:
    stripped = value.strip() if value else ""
    return stripped if stripped else None


def parse_csv(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "name": normalise(row.get("name", "")),
                "date_of_birth": parse_date(row.get("date_of_birth", "")),
                "gender": normalise(row.get("gender", "")),
                "email": normalise(row.get("email", "")),
                "mobile": normalise(row.get("mobile", "")),
                "course": normalise(row.get("course", "")),
                "section": normalise(row.get("section", "")),
                "roll_no": normalise(row.get("roll_no", "")),
                "father_name": normalise(row.get("father_name", "")),
                "father_email": normalise(row.get("father_email", "")),
                "father_mobile": normalise(row.get("father_mobile", "")),
                "mother_name": normalise(row.get("mother_name", "")),
                "mother_email": normalise(row.get("mother_email", "")),
                "mother_mobile": normalise(row.get("mother_mobile", "")),
                "guardian_name": normalise(row.get("guardian_name", "")),
                "guardian_gender": normalise(row.get("guardian_gender", "")),
                "guardian_email": normalise(row.get("guardian_email", "")),
                "guardian_mobile": normalise(row.get("guardian_mobile", "")),
            })
    return rows


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: parse_csv.py <csv_path>", file=sys.stderr)
        sys.exit(1)

    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        rows = parse_csv(csv_path)
        print(json.dumps(rows, ensure_ascii=False))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
