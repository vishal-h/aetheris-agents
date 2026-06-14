#!/usr/bin/env python3
"""Extract all CatalogEntry records from the Boxy MSRP Excel.

One-shot script — run manually when the Boxy catalog is updated.
Reads all Price List sheets and writes one CatalogEntry JSON per line to
the output JSONL file.
"""
import argparse
import datetime
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from schema import CatalogEntry

_COLOR_HEADER_RE = re.compile(r"^\*{0,2}(\d{4})$")


def _extract_cabinet_type(description: str) -> str:
    return description.split(",", 1)[0].strip()


def _parse_dimensions(description: str) -> tuple[float | None, float | None, float | None]:
    dim_re = re.compile(r'([\d]+(?:-\d+/\d+)?)"([WHD])')
    parts: dict[str, float] = {}
    for m in dim_re.finditer(description):
        raw, axis = m.group(1), m.group(2)
        try:
            if "-" in raw:
                whole, frac = raw.split("-", 1)
                num, denom = frac.split("/")
                val = float(whole) + float(num) / float(denom)
            else:
                val = float(raw)
            parts[axis] = val
        except ValueError:
            pass
    return parts.get("W"), parts.get("H"), parts.get("D")


def _parse_color_columns(header_row: "pd.Series") -> dict[str, int]:
    color_cols: dict[str, int] = {}
    for col_idx, val in enumerate(header_row):
        if not pd.notna(val):
            continue
        first_line = str(val).split("\n")[0]
        m = _COLOR_HEADER_RE.fullmatch(first_line)
        if m:
            color_cols[m.group(1)] = col_idx
    return color_cols


def _color_name_from_header(header: str, fallback: str) -> str:
    lines = re.sub(r"^\*+", "", str(header)).split("\n")
    return lines[1].strip() if len(lines) > 1 else fallback


def extract_catalog(catalog_path: Path) -> list[CatalogEntry]:
    """Read all Price List sheets and return a list of CatalogEntry records."""
    xl = pd.ExcelFile(catalog_path)
    catalog_version = datetime.date.today().isoformat()
    source_file = catalog_path.name
    entries: list[CatalogEntry] = []

    for sheet in xl.sheet_names:
        if "Price List" not in sheet:
            continue
        m = re.match(r"(\d+)000 Price List", sheet)
        if not m:
            continue
        series = f"{m.group(1)}000"
        df = pd.read_excel(xl, sheet_name=sheet, header=None)
        color_cols = _parse_color_columns(df.iloc[1])

        for _, row in df.iterrows():
            raw_code = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
            if not raw_code or raw_code in ("nan", "Item", "NO.") or "\n" in raw_code:
                continue
            description = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""
            if not description or description == "nan":
                continue

            cabinet_type = _extract_cabinet_type(description)
            width_in, height_in, depth_in = _parse_dimensions(description)
            base_code = re.sub(r"^[1-9]", "", raw_code)

            for color_code, col_idx in color_cols.items():
                if col_idx >= len(row):
                    continue
                val = row.iloc[col_idx]
                if not pd.notna(val):
                    continue
                try:
                    msrp = float(val)
                except (TypeError, ValueError):
                    continue

                color_name = _color_name_from_header(df.iloc[1, col_idx], color_code)
                entries.append(CatalogEntry(
                    sku=f"{raw_code}-{color_code}",
                    base_code=base_code,
                    raw_code=raw_code,
                    series=series,
                    color_code=color_code,
                    color_name=color_name,
                    description=description,
                    cabinet_type=cabinet_type,
                    width_in=width_in,
                    height_in=height_in,
                    depth_in=depth_in,
                    msrp=msrp,
                    mapped_20_20_codes=[],
                    notes=None,
                    catalog_version=catalog_version,
                    source_file=source_file,
                ))

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Boxy MSRP catalog to JSONL. Run once per catalog update."
    )
    parser.add_argument("--catalog", required=True, type=Path, metavar="XLSX")
    parser.add_argument("--output", required=True, type=Path, metavar="JSONL")
    args = parser.parse_args()

    if not args.catalog.exists():
        print(f"Error: catalog not found: {args.catalog}", file=sys.stderr)
        sys.exit(1)

    try:
        entries = extract_catalog(args.catalog)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        for entry in entries:
            f.write(json.dumps(asdict(entry)) + "\n")

    series_counts: dict[str, int] = {}
    for e in entries:
        series_counts[e.series] = series_counts.get(e.series, 0) + 1

    print(f"Total entries: {len(entries)}")
    for s, n in sorted(series_counts.items()):
        print(f"  Series {s}: {n} entries")
    print(f"Written to: {args.output}")


if __name__ == "__main__":
    main()
