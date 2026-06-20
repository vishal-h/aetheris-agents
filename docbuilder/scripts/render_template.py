"""Render a Markdown narrative template + doc spec + CSS into a complete HTML
document (narrative-mode PDF input for generate_pdf.py).

Deterministic, no LLM. Reads:
  --template  a .md.template file with {{variable}} and {{>Sheet Name}} placeholders
  --css       a .css file (linked into the HTML <head> by absolute URI)
  --context   inline JSON of scalar variables for {{variable}} substitution
  --spec      doc spec JSON path (or '-' for stdin), source of {{>Sheet}} tables

Pipeline: substitute scalar {{variable}} placeholders, replace {{>Sheet}}
partials with HTML tables rendered from the doc spec (same markup/CSS classes
as generate_pdf.py's _build_html), run the result through python-markdown
(tables extension), wrap in a full HTML document, print to stdout.
"""

import argparse
import html as _html
import json
import re
import sys
from pathlib import Path

import markdown

# {{variable}} — scalar substitution. \w+ deliberately excludes {{>...}} partials
# (the '>' and spaces in a sheet name never match \w+), so the two are disjoint.
VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
# {{>Sheet Name}} — table partial. Sheet names may contain spaces.
PARTIAL_RE = re.compile(r"\{\{>\s*([^}]+?)\s*\}\}")


def _esc(value):
    return _html.escape(str(value) if value is not None else "")


def _render_table(sheet):
    """Render one doc-spec sheet as an HTML <table>. Mirrors the per-sheet table
    markup of generate_pdf.py's _build_html: merge_ranges as <th colspan> rows,
    aggregate rows get class='aggregate', cells carry inline text-align/font-weight."""
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
    return "".join(parts)


def _warn(message):
    print(json.dumps({"status": "warning", "warning": message}), file=sys.stderr)


def render_template(template_text, context, doc_spec, css_path):
    """Pure function: return a complete HTML document string."""
    sheets_by_name = {s["name"].lower(): s for s in doc_spec.get("sheets", [])}

    def _sub_var(m):
        key = m.group(1)
        if key in context:
            return str(context[key])
        _warn(f"unknown variable '{key}' left unsubstituted")
        return m.group(0)

    def _sub_partial(m):
        name = m.group(1).strip()
        sheet = sheets_by_name.get(name.lower())
        if sheet is None:
            _warn(f"unknown sheet partial '{name}' replaced with empty string")
            return ""
        return _render_table(sheet)

    text = VAR_RE.sub(_sub_var, template_text)
    text = PARTIAL_RE.sub(_sub_partial, text)

    html_body = markdown.markdown(text, extensions=["tables"])

    # Absolute file:// URI so weasyprint can resolve the stylesheet regardless of cwd.
    css_href = Path(css_path).resolve().as_uri()

    return (
        "<!DOCTYPE html>\n"
        "<html>\n<head>\n<meta charset='utf-8'>\n"
        f"<link rel='stylesheet' href='{css_href}'>\n"
        "</head>\n<body>\n"
        f"{html_body}\n"
        "</body>\n</html>\n"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, help="path to .md.template file")
    parser.add_argument("--css", required=True, help="path to .css file")
    parser.add_argument("--context", default="{}", help="inline JSON of scalar variables")
    parser.add_argument("--spec", default="-", help="doc spec JSON path, or '-' for stdin")
    args = parser.parse_args()

    try:
        template_text = Path(args.template).read_text(encoding="utf-8")
        context = json.loads(args.context)
        if args.spec == "-":
            doc_spec = json.load(sys.stdin)
        else:
            doc_spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        html_doc = render_template(template_text, context, doc_spec, args.css)
        sys.stdout.write(html_doc)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
