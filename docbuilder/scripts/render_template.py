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
import json
import re
import sys
from pathlib import Path

import markdown

from _table_html import render_table

# {{variable}} — scalar substitution. \w+ deliberately excludes {{>...}} partials
# (the '>' and spaces in a sheet name never match \w+), so the two are disjoint.
VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
# {{>Sheet Name}} — table partial. Sheet names may contain spaces.
PARTIAL_RE = re.compile(r"\{\{>\s*([^}]+?)\s*\}\}")

# Context-schema fields that are not in validate_fields.py's BASE_REQUIRED or
# INVOICE_REQUIRED — when absent from the context they render as "" silently
# (an absent optional field is expected, not a defect). Kept in sync with the
# optional fields documented in docs/context-schema.md / validate_fields.py.
# A variable absent from the context AND absent from this set is treated as an
# unknown variable: it still renders as "" (never a raw {{placeholder}} in a
# client-facing PDF) but emits a warning so template/context mismatches surface.
OPTIONAL_FIELDS = {
    "order_ref",
    "order_effective_date",
    "terms",
    "client_code",
    "currency",
    "unit_price",
    "line_item_qty",
    "variant",
}


def _warn(message):
    print(json.dumps({"status": "warning", "warning": message}), file=sys.stderr)


def render_template(template_text, context, doc_spec, css_path):
    """Pure function: return a complete HTML document string."""
    sheets_by_name = {s["name"].lower(): s for s in doc_spec.get("sheets", [])}

    def _sub_var(m):
        key = m.group(1)
        if key in context:
            return str(context[key])
        # Absent: render as empty string (never leave a raw {{placeholder}} in a
        # client-facing PDF). Known-optional fields are silent; anything else
        # warns so template/context mismatches are still visible.
        if key not in OPTIONAL_FIELDS:
            _warn(f"unknown variable '{key}' rendered as empty string")
        return ""

    def _sub_partial(m):
        name = m.group(1).strip()
        sheet = sheets_by_name.get(name.lower())
        if sheet is None:
            _warn(f"unknown sheet partial '{name}' replaced with empty string")
            return ""
        return render_table(sheet)

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
