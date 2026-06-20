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

    for row in sheet["rows"]:
        cls = " class='aggregate'" if row["type"] == "aggregate" else ""
        parts.append(f"<tr{cls}>")
        for cell in row["cells"]:
            fw = "bold" if cell["bold"] else "normal"
            parts.append(
                f"<td style='text-align:{cell['align']};font-weight:{fw};'>"
                f"{esc(cell['value'])}</td>"
            )
        parts.append("</tr>")

    parts.append("</table>")
    return "".join(parts)
