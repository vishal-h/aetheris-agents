"""Shared HTML table markup for the PDF-side renderers.

Single source of truth for the per-sheet table markup used by:
  - generate_pdf.py  (structured mode, `_build_html`)
  - render_template.py  (narrative-mode `{{>Sheet}}` partials)

Markup conventions: merge_ranges become `<th colspan>` rows above the data rows,
aggregate rows get `class='aggregate'`, and each cell carries inline
`text-align`/`font-weight`. `render_table` returns only the `<table>…</table>`
(no heading) so callers add their own heading where appropriate.
"""

import html as _html

from _format import format_cell


def esc(value):
    return _html.escape(str(value) if value is not None else "")


def render_table(sheet):
    """Return the `<table>…</table>` HTML for one doc-spec sheet (no heading)."""
    n_cols = len(sheet["columns"])
    parts = ["<table>"]

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
            f"{esc(mr['value'])}</th>"
        )
        if post:
            row += f"<td colspan='{post}'></td>"
        row += "</tr>"
        parts.append(row)

    columns = sheet["columns"]
    for row in sheet["rows"]:
        cls = " class='aggregate'" if row["type"] == "aggregate" else ""
        is_header = row["type"] == "header"
        parts.append(f"<tr{cls}>")
        for col_idx, cell in enumerate(row["cells"]):
            fw = "bold" if cell["bold"] else "normal"
            # Header cells hold the column name; never type-format them. Data and
            # aggregate cells are formatted by their column's type (currency/number).
            col_type = columns[col_idx]["type"] if col_idx < len(columns) else None
            value = cell["value"] if is_header else format_cell(cell["value"], col_type)
            parts.append(
                f"<td style='text-align:{cell['align']};font-weight:{fw};'>"
                f"{esc(value)}</td>"
            )
        parts.append("</tr>")

    parts.append("</table>")
    return "".join(parts)
