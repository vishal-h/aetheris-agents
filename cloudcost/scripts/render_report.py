#!/usr/bin/env python3
"""Render t3's report data into a self-contained local HTML report (m1, t4).

Reads one `report_data_{YYYY-MM}.json` — the merged payload `compose_report_data.py`
emits — and writes:

    {output_dir}/cloudcost_report_{YYYY-MM}.html

A single file with its CSS inlined: no stylesheet, font, script or image is fetched, so
the report opens from disk, survives being attached to a mail or copied to another
machine, and needs no system binary to produce. Local file only — this stage does not
mail, upload or deliver anything (m1 scope).

**Render-only. This module computes nothing.** Every figure in the report is read from the
payload: the grand total, the month-on-month delta and its percentage, the tag-coverage
ratio, the band cutoffs, each candidate's confidence and saving estimate, and every
subtotal. Nothing here re-totals, re-ranks or re-bands, and no figure absent from the
payload is invented. If the report seems to be missing a number, that is a t3 change, not a
template calculation (§t4 Contract refs). Two consequences worth stating, because they are
what "render-only" means in practice:

* It imports neither `detect_orphans` nor `compose_report_data` — there is no code path
  through which a stage's arithmetic could be re-run here. (Nor `_normalized`: its
  `money()` coerces an unusable value to `0.0`, which is right for arithmetic and wrong for
  a report, where an absent figure must read as absent — see `format_amount`.)
* It reads no clock. The report's "as of" line is `report_data.as_of`, the stamp t3 derived
  from its own inputs; `datetime.now`/`utcnow` appear nowhere in this module, and a test
  asserts that.

The transforms the template does apply are *formatting*, registered here as Jinja filters:
thousands separators and 2dp on an amount, an explicit sign on a change, and a payload
fraction (`tag_coverage.coverage = 0.1667`) shown as a percentage. They change how a number
reads, never which number it is — the render-only guard test mutates figures in the payload
and asserts the HTML follows.

Autoescaping is on. Resource names, tags, account identifiers and evidence strings come
from a provider's API; they are data, not markup.

Usage:
    python3 scripts/render_report.py output/report_data_2026-07.json
    python3 scripts/render_report.py report_data.json --output-dir /tmp/cc
    python3 scripts/render_report.py report_data.json --output /tmp/cc/report.html
    python3 scripts/render_report.py report_data.json --pdf     # optional, needs wkhtmltopdf
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import jinja2

# ------------------------------------------------------------------------- constants

#: The custom cloudcost layout. Anchored to the use-case root rather than the cwd, for the
#: same reason t3 anchors its history directory: the orchestrator may invoke this script
#: from anywhere, and the template is part of the use case, not of the working directory.
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
DEFAULT_TEMPLATE = TEMPLATE_DIR / "report.html.j2"

#: Top-level sections of the payload, with the empty value each degrades to. A section
#: missing from the payload costs the report that section and a rendering note — never a
#: traceback, and never a fabricated stand-in figure.
SECTIONS = (
    ("cost_summary", dict),
    ("mom_delta", dict),
    ("tag_coverage", dict),
    ("orphans", dict),
)

#: Optional PDF companion. Never on the primary path: the HTML is produced by Python and
#: Jinja2 alone, so a machine without this binary still gets the report.
PDF_BINARY = "wkhtmltopdf"


# ---------------------------------------------------------------- formatting filters


def format_amount(value) -> str:
    """A money-shaped figure: `1,234.56`. A non-numeric or absent figure renders as an
    em dash, never as `0.00` — a report that prints zero where it has nothing is the
    silent-wrong-answer shape, and this is the one place the distinction is cheap to keep.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return f"{value:,.2f}"


def format_signed_amount(value) -> str:
    """A change: `+1,234.56` / `-1,234.56`. The sign is the payload's own."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return f"{value:+,.2f}"


def format_ratio_pct(value) -> str:
    """A payload *fraction* (0.1667) shown as a percentage, with the fraction alongside so
    the printed figure and the payload figure are both visible: `16.67 % (0.1667)`."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return f"{value * 100:.2f} % ({value})"


def format_signed_pct(value) -> str:
    """A payload *percentage* (8.99) shown signed: `+8.99 %`. Not multiplied — t3 already
    expressed it in percent, and `None` means "no meaningful ratio" (a zero base), which
    renders as an em dash rather than as 0 %."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return f"{value:+.2f} %"


def format_nz(value, empty: str = "—") -> str:
    """`None` (or an absent key) as an em dash — or as `empty` where a dash would read as a
    figure, e.g. beside a currency code."""
    if value is None or isinstance(value, jinja2.Undefined):
        return empty
    return str(value)


FILTERS = {
    "amount": format_amount,
    "signed_amount": format_signed_amount,
    "ratio_pct": format_ratio_pct,
    "signed_pct": format_signed_pct,
    "nz": format_nz,
}


# --------------------------------------------------------------------------- context


def note_rows(entries, message_keys) -> list:
    """Restructure t3's `warnings[]`/`skipped[]` for display: the message on one side, the
    entry's remaining keys as detail chips on the other. Their shapes vary by origin (a
    provider warning, a scoped prior-period one, a file-level skip), so nothing is assumed
    beyond "a dict, possibly carrying one of these message keys" — and no key is dropped.
    """
    rows = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            rows.append({"message": str(entry), "details": []})
            continue
        message = next((str(entry[key]) for key in message_keys if entry.get(key)), None)
        details = [(key, value) for key, value in entry.items() if key not in message_keys]
        rows.append({"message": message or "(no message)", "details": details})
    return rows


def group_services(cost_summary: dict) -> list:
    """`cost_summary.by_service` grouped by provider, each group keeping the payload's own
    row order (t3 sorts by amount). Grouping moves rows; it does not touch a figure."""
    grouped: dict = {}
    for row in cost_summary.get("by_service") or []:
        if isinstance(row, dict):
            grouped.setdefault(row.get("provider"), []).append(row)
    return [{"provider": provider, "rows": rows} for provider, rows in grouped.items()]


def currencies_by_provider(cost_summary: dict) -> dict:
    """Each provider's currency code, read from `cost_summary.by_provider`. A lookup, so a
    per-provider figure elsewhere in the report (an untagged spender's estimate, a
    candidate's saving) can be labelled with that provider's own currency rather than with
    the report's — which is `null` by design when the providers disagree."""
    return {
        row.get("provider"): row.get("currency")
        for row in cost_summary.get("by_provider") or []
        if isinstance(row, dict)
    }


def build_context(data: dict, source_file: str) -> tuple:
    """The template context, plus the rendering notes gathered while building it.

    Absent or wrong-shaped sections degrade to empty containers and a note; every figure
    that *is* present is passed through untouched.
    """
    render_warnings: list = []
    context: dict = {
        "period": data.get("period"),
        "as_of": data.get("as_of"),
        "providers": data.get("providers") or [],
        "accounts": data.get("accounts") or [],
        "totals": data.get("totals") or {},
        "source_file": source_file,
    }

    for key, kind in SECTIONS:
        value = data.get(key)
        if not isinstance(value, kind):
            render_warnings.append(
                f"the report data has no usable '{key}' section, so that section of this "
                f"report is empty — the figures were not substituted or estimated"
            )
            value = kind()
        context[key] = value

    context["service_groups"] = group_services(context["cost_summary"])
    context["currency_of"] = currencies_by_provider(context["cost_summary"])
    context["data_warnings"] = note_rows(data.get("warnings"), ("warning",))
    context["data_skipped"] = note_rows(data.get("skipped"), ("reason",))
    context["render_warnings"] = render_warnings
    return context, render_warnings


# ---------------------------------------------------------------------------- render


def render_html(data: dict, template_path=DEFAULT_TEMPLATE, source_file: str = "") -> tuple:
    """Render `data` through the template. Returns `(html, render_warnings)`.

    Pure with respect to the payload: no clock, no network, no environment. The same
    report data and template always produce the same bytes.
    """
    template_path = Path(template_path)
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent)),
        autoescape=jinja2.select_autoescape(
            enabled_extensions=("html", "htm", "j2"), default_for_string=True
        ),
        undefined=jinja2.Undefined,
        trim_blocks=False,
        keep_trailing_newline=True,
    )
    environment.filters.update(FILTERS)
    template = environment.get_template(template_path.name)
    context, render_warnings = build_context(data, source_file)
    return template.render(**context), render_warnings


def write_pdf(html_path: Path) -> tuple:
    """Optional PDF companion beside the HTML. Returns `(path, note)`.

    The binary being absent is a note, not a failure — at the level that claim is made:
    the caller reports it on stdout and still exits 0, because the HTML has already been
    written and the primary path never depended on this.
    """
    binary = shutil.which(PDF_BINARY)
    if binary is None:
        return None, (
            f"--pdf was requested but {PDF_BINARY} is not installed; the HTML report was "
            f"written and no PDF was produced"
        )
    pdf_path = html_path.with_suffix(".pdf")
    result = subprocess.run(
        [binary, "--quiet", "--enable-local-file-access", str(html_path), str(pdf_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not pdf_path.exists():
        return None, (
            f"{PDF_BINARY} exited {result.returncode}; the HTML report was written and no "
            f"PDF was produced: {result.stderr.strip()[:200]}"
        )
    return pdf_path, None


# ------------------------------------------------------------------------------ main


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Render cloudcost report data into a self-contained local HTML report"
    )
    parser.add_argument("report_data", help="report_data_{YYYY-MM}.json from compose_report_data")
    parser.add_argument("--output-dir", default="output", help="default: output")
    parser.add_argument(
        "--output", default=None, help="explicit output path (overrides --output-dir)"
    )
    parser.add_argument(
        "--template", default=str(DEFAULT_TEMPLATE), help=f"default: {DEFAULT_TEMPLATE}"
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help=f"also write a PDF beside the HTML (needs {PDF_BINARY}; the HTML never does)",
    )
    return parser.parse_args(argv)


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    print(json.dumps({"status": "error", "error": message}, indent=2))
    return 1


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        data = json.loads(Path(args.report_data).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return fail(f"cannot read report data {args.report_data}: {exc}")
    if not isinstance(data, dict):
        return fail(f"report data {args.report_data} is not a JSON object")

    try:
        html, render_warnings = render_html(
            data, template_path=args.template, source_file=str(args.report_data)
        )
    except (jinja2.TemplateError, OSError) as exc:
        # Covers a missing or malformed template and an undefined-value access the section
        # guards did not catch. Degrade to the stage-CLI error envelope rather than letting
        # a traceback break the stdout contract the orchestrator reads.
        return fail(f"cannot render {args.template}: {type(exc).__name__}: {exc}")

    period = data.get("period") or "unknown"
    path = Path(args.output) if args.output else Path(args.output_dir) / f"cloudcost_report_{period}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(html, encoding="utf-8")
    tmp.replace(path)

    # The PDF is an optional companion, so its absence is a note on stdout and nothing more:
    # it must not flip the stage's status, because the HTML — the deliverable — was written
    # before this ran. It is kept out of `render_warnings` for that reason, and because that
    # list is rendered *into* the HTML, which by now exists on disk.
    pdf_path = pdf_note = None
    if args.pdf:
        pdf_path, pdf_note = write_pdf(path)

    orphans = data.get("orphans") if isinstance(data.get("orphans"), dict) else {}
    orphan_totals = orphans.get("totals") if isinstance(orphans.get("totals"), dict) else {}
    summary = {
        # `partial` reports *this stage's* problems only. The payload's own warnings and
        # skipped inputs are data — t3 already reported them, and they are rendered into
        # the report's Data notes rather than re-raised as a render failure.
        "status": "partial" if render_warnings else "ok",
        "period": data.get("period"),
        "as_of": data.get("as_of"),
        "file": str(path),
        "pdf": str(pdf_path) if pdf_path else None,
        "pdf_note": pdf_note,
        "bytes": len(html.encode("utf-8")),
        "template": str(args.template),
        "sections": [
            "header",
            "cost-summary",
            "month-on-month",
            "tag-coverage",
            "orphan-candidates",
            "data-notes",
        ],
        "counts": {
            "providers": len(data.get("providers") or []),
            "orphan_candidates": orphan_totals.get("candidates"),
            "data_warnings": len(data.get("warnings") or []),
            "data_skipped": len(data.get("skipped") or []),
        },
        "mom_status": (data.get("mom_delta") or {}).get("status"),
        "render_warnings": render_warnings,
    }
    print(json.dumps(summary, indent=2))
    return 1 if render_warnings else 0


if __name__ == "__main__":
    sys.exit(main())
