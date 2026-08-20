"""Rename generated output files to the deliverable convention.

Finds the run's generated files in the output dir (those matching
`{filename_prefix}.{ext}` for the known render extensions) and renames each to
`{client_name_slug}_{doc_type}_{date}.{ext}`, with fields taken from a context
JSON. Deterministic — no LLM. Prints a JSON array of `{original, renamed}` path
pairs (so the orchestrator can hand the renamed paths to upload_output.py).

Required context fields: `client_name` (or `candidate_name` for offer letters), and
`date`. `doc_type` is optional and falls back to the `--filename-prefix` base (its
`_v{N}` version suffix stripped).

See docs/context-schema.md and docs/drive-structure.md §"Output filename convention".
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from run_record import run_record, use_case_root_for  # noqa: E402

KNOWN_EXTS = ("xlsx", "docx", "pdf", "csv", "json", "xml", "md")

#: This script writes the run's deliverable files, so it is the step that attests them.
#: The record is written HERE rather than by a later orchestrator prompt step: a writer an
#: LLM is free to skip is the same defect as a reader free to ignore the stamp, one step
#: earlier (BL-153 ruling 1, and ds t2 §A2).
STEP = "rename_output"


def slugify(name):
    """Lowercase, spaces → underscores, strip anything but [a-z0-9_-]."""
    s = str(name).strip().lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_-]", "", s)


def safe_segment(value):
    """Filename-safe form of a free-text segment (e.g. the date): collapse
    whitespace to underscores, strip anything but [A-Za-z0-9_.-]. ISO dates pass
    through unchanged; a display date like '20 Jun 2026' → '20_Jun_2026'."""
    s = re.sub(r"\s+", "_", str(value).strip())
    return re.sub(r"[^A-Za-z0-9_.-]", "", s)


def doc_type_base(filename_prefix):
    """Derive a doc_type from the filename prefix when context omits it:
    strip a trailing `_v{N}` version segment. `proposal_v1` → `proposal`."""
    return re.sub(r"_v\d+$", "", filename_prefix)


def rename_outputs(output_dir, filename_prefix, context):
    """Rename matching files; return a list of {original, renamed} path-pair dicts.

    Raises KeyError-equivalent ValueError if a required context field is missing.
    """
    # client_name for invoices/proposals; candidate_name for offer letters (m6 t4b).
    name = context.get("client_name") or context.get("candidate_name") or ""
    if not name:
        raise ValueError("context has neither 'client_name' nor 'candidate_name'")
    if not context.get("date"):
        raise ValueError("context missing required field 'date'")

    slug = slugify(name)
    doc_type = context.get("doc_type") or doc_type_base(filename_prefix)
    date = safe_segment(context["date"])

    out = Path(output_dir)
    pairs = []
    for ext in KNOWN_EXTS:
        src = out / f"{filename_prefix}.{ext}"
        if not src.exists():
            continue
        dest = out / f"{slug}_{doc_type}_{date}.{ext}"
        src.rename(dest)
        pairs.append({"original": str(src), "renamed": str(dest)})
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--filename-prefix", required=True,
                        help="generated filename prefix, e.g. proposal_v1")
    parser.add_argument("--context", required=True, help="inline JSON of context fields")
    parser.add_argument("--output", default=None,
                        help="write the JSON result to FILE and print only the path")
    parser.add_argument("--run-id", default=None,
                        help="harness run id; omitted when no run reaches this script, in "
                             "which case the record carries run_id null")
    args = parser.parse_args()

    try:
        with run_record(use_case_root_for(__file__), args.run_id, STEP) as rec:
            context = json.loads(args.context)
            pairs = rename_outputs(args.output_dir, args.filename_prefix, context)
            rec.add(*(pair["renamed"] for pair in pairs))

            result = json.dumps(pairs)
            if args.output:
                Path(args.output).write_text(result, encoding="utf-8")
                rec.add(args.output)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(args.output if args.output else result)


if __name__ == "__main__":
    main()
