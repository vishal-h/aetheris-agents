#!/usr/bin/env python3
"""Resolve PlanComponent codes against the Boxy MSRP Excel catalog.

Reads a JSON array of PlanComponent dicts from stdin.
Writes a JSON array of ResolvedItem dicts to stdout.
"""
import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from schema import CatalogItem, PlanComponent, ResolvedItem

# Color columns are identified by a 4-digit code in the header first line.
# Leading '*' characters mark "coming soon" columns (kept for parsing, skipped on NaN MSRP).
_COLOR_HEADER_RE = re.compile(r"^\*{0,2}(\d{4})$")


def parse_finish(spec: str) -> tuple[str, str, str]:
    """Parse "2001:Ivory White:2000" → (color_code, color_name, series)."""
    parts = spec.split(":", 2)
    if len(parts) != 3:
        raise ValueError(f"finish spec must be code:name:series, got {spec!r}")
    return parts[0], parts[1], parts[2]


def _extract_cabinet_type(description: str) -> str:
    return description.split(",", 1)[0].strip()


def _parse_dimensions(description: str) -> tuple[float | None, float | None, float | None]:
    """Return (width_in, height_in, depth_in) parsed from a description string."""
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


def _is_upper(cabinet_type: str) -> bool:
    return "Wall" in cabinet_type


def _parse_color_columns(header_row: "pd.Series") -> dict[str, int]:
    """Return {color_code: col_idx} from the header row of a Price List sheet."""
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


def load_catalog(path: Path) -> dict[str, list[CatalogItem]]:
    """Load all Price List sheets; return code → [CatalogItem] index.

    Both raw catalog codes and leading-digit-stripped codes are indexed so that
    plan code "DB30" (which doesn't exist verbatim in the catalog) resolves via
    the normalized form of catalog entry "3DB30".
    """
    xl = pd.ExcelFile(path)
    index: dict[str, list[CatalogItem]] = {}

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
                item = CatalogItem(
                    sku=f"{raw_code}-{color_code}",
                    series=series,
                    color_code=color_code,
                    color_name=color_name,
                    description=description,
                    cabinet_type=cabinet_type,
                    width_in=width_in,
                    height_in=height_in,
                    depth_in=depth_in,
                    msrp=msrp,
                )

                index.setdefault(raw_code, []).append(item)
                normalized = re.sub(r"^[1-9]", "", raw_code)
                if normalized != raw_code:
                    index.setdefault(normalized, []).append(item)

    return index


def _resolve_component(
    component: PlanComponent,
    index: dict[str, list[CatalogItem]],
    upper_finish: tuple[str, str, str],
    lower_finish: tuple[str, str, str],
) -> ResolvedItem:
    code = component.code
    matched_code: str | None = None
    catalog_items: list[CatalogItem] | None = None
    match_confidence = "unresolved"
    match_notes: str | None = None

    # 1. Direct lookup — covers both exact catalog codes and normalized forms
    if code in index:
        matched_code = code
        catalog_items = index[code]
        match_confidence = "exact"
    else:
        # 2. Plan code itself has a leading digit — strip it and retry
        norm_plan = re.sub(r"^[1-9]", "", code)
        if norm_plan != code and norm_plan in index:
            matched_code = norm_plan
            catalog_items = index[norm_plan]
            match_confidence = "exact"
        else:
            # 3. Dash-suffix codes like W2439-24 → strip → W2439
            stripped = re.sub(r"-\d{2}[A-Z0-9]*$", "", code)
            if stripped != code:
                if stripped in index:
                    matched_code = stripped
                    catalog_items = index[stripped]
                    match_confidence = "fuzzy"
                    match_notes = f"matched as {stripped} after suffix strip"
                else:
                    norm_stripped = re.sub(r"^[1-9]", "", stripped)
                    if norm_stripped != stripped and norm_stripped in index:
                        matched_code = norm_stripped
                        catalog_items = index[norm_stripped]
                        match_confidence = "fuzzy"
                        match_notes = f"matched as {norm_stripped} after suffix and prefix strip"

    if catalog_items is None or matched_code is None:
        return ResolvedItem(
            component=component,
            catalog_item=None,
            qty=component.qty,
            unit_price=0.0,
            line_total=0.0,
            match_confidence="unresolved",
            match_notes=None,
        )

    # Pick finish based on cabinet type
    first = catalog_items[0]
    chosen_finish = upper_finish if _is_upper(first.cabinet_type) else lower_finish
    color_code, _color_name, preferred_series = chosen_finish

    # Prefer matching series + color, fall back to just color, then first available
    candidates = [ci for ci in catalog_items if ci.series == preferred_series and ci.color_code == color_code]
    if not candidates:
        candidates = [ci for ci in catalog_items if ci.color_code == color_code]
    if not candidates:
        candidates = catalog_items[:1]

    chosen = candidates[0]
    catalog_item = CatalogItem(
        sku=f"{matched_code}-{color_code}",
        series=chosen.series,
        color_code=chosen.color_code,
        color_name=chosen.color_name,
        description=chosen.description,
        cabinet_type=chosen.cabinet_type,
        width_in=chosen.width_in,
        height_in=chosen.height_in,
        depth_in=chosen.depth_in,
        msrp=chosen.msrp,
    )

    return ResolvedItem(
        component=component,
        catalog_item=catalog_item,
        qty=component.qty,
        unit_price=chosen.msrp,
        line_total=chosen.msrp * component.qty,
        match_confidence=match_confidence,
        match_notes=match_notes,
    )


def resolve(
    components: list[PlanComponent],
    catalog_path: Path,
    upper_finish: tuple[str, str, str],
    lower_finish: tuple[str, str, str],
) -> list[ResolvedItem]:
    index = load_catalog(catalog_path)
    return [_resolve_component(c, index, upper_finish, lower_finish) for c in components]


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve plan codes against Boxy catalog.")
    parser.add_argument("--catalog", required=True, type=Path, metavar="XLSX")
    parser.add_argument("--upper-finish", required=True, metavar="CODE:NAME:SERIES")
    parser.add_argument("--lower-finish", required=True, metavar="CODE:NAME:SERIES")
    args = parser.parse_args()

    upper_finish = parse_finish(args.upper_finish)
    lower_finish = parse_finish(args.lower_finish)

    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON on stdin: {exc}", file=sys.stderr)
        sys.exit(1)

    components = [PlanComponent(**d) for d in data]

    try:
        results = resolve(components, args.catalog, upper_finish, lower_finish)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps([asdict(r) for r in results], indent=2))


if __name__ == "__main__":
    main()
