import argparse
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter


def _thin_top():
    return Border(top=Side(style="thin"))


def _write_cell(ws_cell, cell_spec, col_type=None):
    value = cell_spec["value"]
    if col_type in ("currency", "number") and isinstance(value, str):
        try:
            value = float(value)
        except (ValueError, TypeError):
            pass
    ws_cell.value = value
    ws_cell.font = Font(bold=cell_spec["bold"])
    ws_cell.alignment = Alignment(horizontal=cell_spec["align"])
    if col_type in ("currency", "number"):
        ws_cell.number_format = "#,##0.00"


def generate_xlsx(doc_spec, output_path):
    wb = Workbook()
    wb.remove(wb.active)

    for sheet in doc_spec["sheets"]:
        ws = wb.create_sheet(title=sheet["name"])
        columns = sheet["columns"]

        for i, col in enumerate(columns, start=1):
            ws.column_dimensions[get_column_letter(i)].width = col["width"]

        for mr in sheet.get("merge_ranges", []):
            ws.merge_cells(
                start_row=mr["row"], start_column=mr["col_start"],
                end_row=mr["row"], end_column=mr["col_end"],
            )
            top_left = ws.cell(row=mr["row"], column=mr["col_start"])
            top_left.value = mr["value"]
            top_left.font = Font(bold=True)
            top_left.alignment = Alignment(horizontal="center")

        header_row = sheet["header_row"]
        for row_offset, row in enumerate(sheet["rows"]):
            physical_row = header_row + row_offset
            is_aggregate = row["type"] == "aggregate"

            for col_offset, cell_spec in enumerate(row["cells"]):
                col_idx = col_offset + 1
                col_type = columns[col_offset]["type"] if col_offset < len(columns) else None
                ws_cell = ws.cell(row=physical_row, column=col_idx)
                _write_cell(ws_cell, cell_spec, col_type)
                if is_aggregate:
                    ws_cell.border = _thin_top()

    wb.save(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--filename", default="document")
    args = parser.parse_args()

    try:
        doc_spec = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.filename}.xlsx"
        generate_xlsx(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
