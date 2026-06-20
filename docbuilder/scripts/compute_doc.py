import argparse
import json
import sys
from pathlib import Path

VALID_FORMATS = {"xlsx", "docx", "pdf", "csv", "json", "xml", "md"}
VALID_FUNCTIONS = {"sum", "count", "avg"}


def _run_aggregate(values, function):
    if function == "count":
        return sum(1 for v in values if v is not None and str(v).strip() != "")
    nums = []
    for v in values:
        try:
            nums.append(float(v))
        except (ValueError, TypeError):
            pass
    if function == "sum":
        return sum(nums)
    if function == "avg":
        return (sum(nums) / len(nums)) if nums else 0
    raise ValueError(f"unknown aggregate function '{function}'")


def _fmt(val):
    if isinstance(val, float) and val == int(val):
        return int(val)
    return val


def _cell(value, bold, align):
    return {"value": value, "bold": bold, "align": align}


def compute_doc(template, sources):
    """
    template: parsed template dict
    sources:  dict of key -> list of row dicts
    returns:  doc spec dict
    """
    if len(template["data_sources"]) > 1:
        raise ValueError("m1 supports exactly one data_source")

    for fmt in template.get("output_formats", []):
        if fmt not in VALID_FORMATS:
            raise ValueError(f"unknown output_format '{fmt}'")

    sheet_raw_rows = {}   # sheet_name -> raw rows (populated in Pass 1)
    output_map = {}       # sheet_name -> built sheet spec

    # Pass 1 — data-bearing sheets (source_key non-null)
    for sheet in template["sheets"]:
        if sheet["source_key"] is None:
            continue

        if sheet.get("summary_rows"):
            raise ValueError(
                f"sheet '{sheet['name']}' has both source_key and summary_rows — invalid"
            )

        source_key = sheet["source_key"]
        if source_key not in sources:
            raise ValueError(f"source key '{source_key}' not found in provided sources")

        raw_rows = sources[source_key]
        sheet_raw_rows[sheet["name"]] = raw_rows
        columns = sheet["columns"]

        if raw_rows:
            available = set(raw_rows[0].keys())
            for col in columns:
                sf = col["source_field"]
                if sf is not None and sf not in available:
                    raise ValueError(
                        f"source_field '{sf}' not found in source '{source_key}'"
                    )

        header_cells = [_cell(col["name"], True, col["align"]) for col in columns]

        data_rows = []
        for raw_row in raw_rows:
            cells = [
                _cell(raw_row.get(col["source_field"], "") if col["source_field"] else "",
                      col["bold"], col["align"])
                for col in columns
            ]
            data_rows.append({"type": "data", "cells": cells})

        agg_top = []
        agg_bottom = []
        for agg_def in sheet.get("aggregate_rows", []):
            for agg in agg_def["aggregates"]:
                if agg["function"] not in VALID_FUNCTIONS:
                    raise ValueError(f"unknown aggregate function '{agg['function']}'")

            agg_values = {
                agg["column"]: _fmt(_run_aggregate(
                    [row.get(agg["column"], "") for row in raw_rows],
                    agg["function"]
                ))
                for agg in agg_def["aggregates"]
            }

            cells = []
            for col in columns:
                sf = col["source_field"]
                if sf == agg_def["label_column"]:
                    cells.append(_cell(agg_def["label"], True, col["align"]))
                elif sf in agg_values:
                    cells.append(_cell(agg_values[sf], True, col["align"]))
                else:
                    cells.append(_cell("", True, col["align"]))

            agg_row = {"type": "aggregate", "cells": cells}
            (agg_top if agg_def["position"] == "top" else agg_bottom).append(agg_row)

        merge_rows = [mr["row"] for mr in sheet.get("merge_ranges", [])]
        computed_header_row = max(merge_rows) + 1 if merge_rows else 1
        header_row = sheet.get("header_row", computed_header_row)

        all_rows = (
            [{"type": "header", "cells": header_cells}]
            + agg_top
            + data_rows
            + agg_bottom
        )

        output_map[sheet["name"]] = {
            "name": sheet["name"],
            "header_row": header_row,
            "columns": [{"name": c["name"], "type": c["type"], "width": c["width"]} for c in columns],
            "merge_ranges": sheet.get("merge_ranges", []),
            "rows": all_rows,
        }

    # Pass 2 — summary sheets (source_key null)
    for sheet in template["sheets"]:
        if sheet["source_key"] is not None:
            continue

        columns = sheet["columns"]
        header_cells = [_cell(col["name"], True, col["align"]) for col in columns]

        data_rows = []
        for sr in sheet.get("summary_rows", []):
            if sr["type"] == "aggregate_ref":
                agg = sr["aggregate"]
                src_name = agg["source_sheet"]

                if src_name not in sheet_raw_rows:
                    raise ValueError(f"source_sheet '{src_name}' not found")

                fn = agg["function"]
                if fn not in VALID_FUNCTIONS:
                    raise ValueError(f"unknown aggregate function '{fn}'")

                col_vals = [row.get(agg["column"], "") for row in sheet_raw_rows[src_name]]
                val = _fmt(_run_aggregate(col_vals, fn))

                cells = [_cell(sr["label"], columns[0]["bold"], columns[0]["align"])]
                if len(columns) > 1:
                    cells.append(_cell(val, columns[1]["bold"], columns[1]["align"]))
                for col in columns[2:]:
                    cells.append(_cell("", col["bold"], col["align"]))

            elif sr["type"] == "static":
                cells = [_cell(sr["label"], columns[0]["bold"], columns[0]["align"])]
                if len(columns) > 1:
                    cells.append(_cell(sr["value"], columns[1]["bold"], columns[1]["align"]))
                for col in columns[2:]:
                    cells.append(_cell("", col["bold"], col["align"]))

            else:
                continue

            data_rows.append({"type": "data", "cells": cells})

        merge_rows = [mr["row"] for mr in sheet.get("merge_ranges", [])]
        computed_header_row = max(merge_rows) + 1 if merge_rows else 1
        header_row = sheet.get("header_row", computed_header_row)

        output_map[sheet["name"]] = {
            "name": sheet["name"],
            "header_row": header_row,
            "columns": [{"name": c["name"], "type": c["type"], "width": c["width"]} for c in columns],
            "merge_ranges": sheet.get("merge_ranges", []),
            "rows": [{"type": "header", "cells": header_cells}] + data_rows,
        }

    # Preserve template sheet order
    output_sheets = [output_map[s["name"]] for s in template["sheets"]]

    return {
        "title": template["title"],
        "template_id": template["template_id"],
        "output_formats": template["output_formats"],
        "sheets": output_sheets,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("template_path")
    parser.add_argument("source_paths", nargs="+",
                        help="raw source JSON paths, or '-' for stdin")
    args = parser.parse_args()

    try:
        template = json.loads(Path(args.template_path).read_text())
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        source_dicts = []
        for p in args.source_paths:
            if p == "-":
                source_dicts.append(json.load(sys.stdin))
            else:
                source_dicts.append(json.loads(Path(p).read_text()))

        sources = {s["key"]: s["rows"] for s in source_dicts}
        doc_spec = compute_doc(template, sources)
        print(json.dumps(doc_spec, indent=2))
    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
