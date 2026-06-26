import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import weasyprint

from _table_html import esc, render_table

_RENDER_TEMPLATE = Path(__file__).parent / "render_template.py"


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
        parts.append(f"<h1>{esc(title)}</h1>")

    for sheet in doc_spec["sheets"]:
        # structured mode prepends a sheet heading; the table markup itself is shared.
        parts.append(f"<h2>{esc(sheet['name'])}</h2>")
        parts.append(render_table(sheet))

    parts.append("</body></html>")
    return "".join(parts)


def _narrative_html_jinja(doc_spec, template_dir, context_json):
    """Produce narrative HTML via the Jinja2 path (m6, `has_jinja: true`).

    Calls `generate_html.render_html` in-process (no subprocess). Sheet tables are
    pre-rendered with the shared `render_table` (so all table formatting stays in
    Python, not the template) and injected as `tables[{sheet name}]`; the `.html.j2`
    emits them with `{{ tables['Name'] | safe }}` (trusted, pre-rendered markup —
    autoescaping is on). The template links its CSS relatively; WeasyPrint resolves it
    against `base_url` (set by `generate_pdf`). `spec` (the full doc spec) is also
    exposed to the template."""
    from generate_html import render_html

    narrative = doc_spec["narrative"]
    template_path = Path(template_dir) / narrative["template_file"]
    context = json.loads(context_json) if context_json else {}
    context["tables"] = {s["name"]: render_table(s) for s in doc_spec.get("sheets", [])}
    return render_html(template_path, context, spec=doc_spec)


def _narrative_html(doc_spec, template_dir, context_json):
    """Produce HTML for narrative mode.

    `has_jinja: true` → the Jinja2 path (`_narrative_html_jinja`). Otherwise the legacy
    Markdown path: shell out to render_template.py (the doc spec is written to a temp file
    and passed via `--spec`; `--template`/`--css` are resolved from the `narrative` block's
    filenames under `template_dir`)."""
    if doc_spec.get("has_jinja"):
        return _narrative_html_jinja(doc_spec, template_dir, context_json)

    narrative = doc_spec["narrative"]
    template_path = Path(template_dir) / narrative["template_file"]
    css_path = Path(template_dir) / narrative["css_file"]

    fd, spec_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc_spec, f)
        result = subprocess.run(
            [
                sys.executable, str(_RENDER_TEMPLATE),
                "--template", str(template_path),
                "--css", str(css_path),
                "--context", context_json,
                "--spec", spec_path,
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"render_template.py failed: {result.stderr.strip()}")
        return result.stdout
    finally:
        os.unlink(spec_path)


def generate_pdf(doc_spec, output_path, template_dir=None, context=None):
    """Render the doc spec to PDF.

    Narrative mode (doc spec has a `narrative` block AND `template_dir` is given):
    HTML is produced by render_template.py (Markdown + CSS). Otherwise structured
    mode: `_build_html(doc_spec)` (m1 behaviour). If `narrative` is present but no
    `template_dir` is supplied, warn on stderr and fall back to structured mode."""
    base_url = None
    if doc_spec.get("narrative") and template_dir:
        html = _narrative_html(doc_spec, template_dir, context or "{}")
        # Resolve relative asset URLs (e.g. <img src="logo.png">) against the
        # template bundle dir where the committed assets live — not the CWD.
        # Trailing os.sep so urljoin keeps the final path segment (without it,
        # urljoin treats the dir name as a file and drops it).
        base_url = str(Path(template_dir).resolve()) + os.sep
    else:
        if doc_spec.get("narrative") and not template_dir:
            print(
                json.dumps({
                    "status": "warning",
                    "warning": "narrative present but --template-dir not provided; "
                               "falling back to structured mode",
                }),
                file=sys.stderr,
            )
        html = _build_html(doc_spec)
    weasyprint.HTML(string=html, base_url=base_url).write_pdf(str(output_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--filename", default="document")
    parser.add_argument("--input", default=None, help="doc spec JSON file path (default: stdin)")
    parser.add_argument("--template-dir", default=None,
                        help="directory holding the narrative .md.template and .css "
                             "(enables narrative mode when the doc spec has a narrative block)")
    parser.add_argument("--context", default="{}",
                        help="inline JSON of scalar variables for narrative-mode substitution")
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
        generate_pdf(doc_spec, output_path,
                     template_dir=args.template_dir, context=args.context)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
