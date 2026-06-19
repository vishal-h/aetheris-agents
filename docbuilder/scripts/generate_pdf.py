import argparse
import html as _html
import json
import sys
from pathlib import Path

import weasyprint


def _esc(value):
    return _html.escape(str(value) if value is not None else "")


def _build_html(doc_spec):
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>",
        "body{font-family:sans-serif;font-size:10pt;margin:20mm}",
        "h1{font-size:16pt;margin-bottom:6pt}",
        "h2{font-size:12pt;margin-top:14pt;margin-bottom:4pt}",
        "table{border-collapse:collapse;width:100%;margin-bottom:14pt}",
        "th,td{border:1px solid #bbb;padding:3pt 5pt}",
        "tr.aggregate td{border-top:2px solid #444}",
        "</style></head><body>",
    ]

    title = doc_spec.get("title")
    if title:
        parts.append(f"<h1>{_esc(title)}</h1>")

    for sheet in doc_spec["sheets"]:
        n_cols = len(sheet["columns"])
        parts.append(f"<h2>{_esc(sheet['name'])}</h2><table>")

        # merge_ranges: rendered as <th colspan="N"> rows above the data rows
        for mr in sheet.get("merge_ranges", []):
            colspan = mr["col_end"] - mr["col_start"] + 1
            pre = mr["col_start"] - 1
            post = n_cols - mr["col_end"]
            row = "<tr>"
            if pre:
                row += f"<td colspan='{pre}'></td>"
            row += (
                f"<th colspan='{colspan}' "
                f"style='text-align:center;font-weight:bold;'>"
                f"{_esc(mr['value'])}</th>"
            )
            if post:
                row += f"<td colspan='{post}'></td>"
            row += "</tr>"
            parts.append(row)

        for row in sheet["rows"]:
            cls = " class='aggregate'" if row["type"] == "aggregate" else ""
            parts.append(f"<tr{cls}>")
            for cell in row["cells"]:
                fw = "bold" if cell["bold"] else "normal"
                parts.append(
                    f"<td style='text-align:{cell['align']};font-weight:{fw};'>"
                    f"{_esc(cell['value'])}</td>"
                )
            parts.append("</tr>")

        parts.append("</table>")

    parts.append("</body></html>")
    return "".join(parts)


def generate_pdf(doc_spec, output_path):
    html = _build_html(doc_spec)
    weasyprint.HTML(string=html).write_pdf(str(output_path))


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
        output_path = output_dir / f"{args.filename}.pdf"
        generate_pdf(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
