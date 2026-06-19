import argparse
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

ALIGN_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
}


def _write_cell(doc_cell, cell_spec):
    para = doc_cell.paragraphs[0]
    run = para.add_run(str(cell_spec["value"]) if cell_spec["value"] is not None else "")
    run.bold = cell_spec["bold"]
    para.alignment = ALIGN_MAP.get(cell_spec["align"], WD_ALIGN_PARAGRAPH.LEFT)


def generate_docx(doc_spec, output_path):
    doc = Document()

    title = doc_spec.get("title")
    if title:
        doc.add_heading(title, level=0)

    for sheet in doc_spec["sheets"]:
        rows = sheet["rows"]
        columns = sheet["columns"]

        if not rows:
            continue

        doc.add_heading(sheet["name"], level=1)

        table = doc.add_table(rows=len(rows), cols=len(columns))
        table.style = "Table Grid"

        for row_idx, row_spec in enumerate(rows):
            tr = table.rows[row_idx]
            for col_idx, cell_spec in enumerate(row_spec["cells"]):
                _write_cell(tr.cells[col_idx], cell_spec)

    doc.save(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--filename", default="document")
    parser.add_argument("--input", default=None, help="doc spec JSON file path (default: stdin)")
    args = parser.parse_args()

    try:
        src = open(args.input, encoding="utf-8") if args.input else sys.stdin
        doc_spec = json.load(src)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.filename}.docx"
        generate_docx(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
