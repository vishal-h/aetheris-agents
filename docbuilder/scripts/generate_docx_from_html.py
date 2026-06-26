"""Convert an HTML file to DOCX via Pandoc, using a Bitloka reference doc for styling.

Deterministic, no LLM. The DOCX half of the m6 Jinja2 path: `generate_html.py` renders a
`.html.j2` template to HTML, then this script shells out to Pandoc to produce a branded
`.docx`. Pandoc reads the named styles (Normal, Heading 1/2, table style) from
`--reference-doc` and ignores that file's body content, so the reference doc carries
branding only.

  --input         HTML file to convert
  --output        DOCX file to write
  --reference-doc DOCX whose styles brand the output
                  (default: data/templates/bitloka/reference.docx)

Errors (pandoc missing, pandoc non-zero, bad paths) print
`{"status":"error","error":"..."}` to stderr and exit 1 (stage-CLI pattern).
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

# Resolved relative to the script so it is cwd-independent (run_command runs from the
# docbuilder sandbox; tests run with cwd=USE_CASE_ROOT — both resolve here).
DEFAULT_REFERENCE_DOC = (
    Path(__file__).parent.parent / "data" / "templates" / "bitloka" / "reference.docx"
)


def html_to_docx(html_path, output_path, reference_doc=None):
    """Convert `html_path` → `output_path` (DOCX) via Pandoc.

    `reference_doc` brands the output (default: the committed Bitloka reference doc).
    Raises FileNotFoundError if pandoc is not on PATH; RuntimeError (carrying pandoc's
    stderr) if pandoc exits non-zero.
    """
    if shutil.which("pandoc") is None:
        raise FileNotFoundError("pandoc not found on PATH")

    ref = Path(reference_doc) if reference_doc else DEFAULT_REFERENCE_DOC
    cmd = [
        "pandoc",
        "--from", "html",
        "--to", "docx",
        "--reference-doc", str(ref),
        "-o", str(output_path),
        str(html_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed (exit {result.returncode}): {result.stderr.strip()}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="HTML file to convert")
    parser.add_argument("--output", required=True, help="DOCX file to write")
    parser.add_argument(
        "--reference-doc",
        default=None,
        help="DOCX whose styles brand the output (default: bitloka/reference.docx)",
    )
    args = parser.parse_args()

    try:
        html_to_docx(args.input, args.output, args.reference_doc)
    except (FileNotFoundError, RuntimeError, OSError) as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(args.output)


if __name__ == "__main__":
    main()
