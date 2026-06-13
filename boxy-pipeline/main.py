#!/usr/bin/env python3
"""Boxy kitchen pipeline CLI.

Wires plan_extractor → catalog_resolver → PipelineResult aggregation →
order_formatter into a single command.
"""
import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from catalog_resolver import parse_finish, resolve as resolve_catalog
from order_formatter import write_order_form
from plan_extractor import extract_pdfs
from schema import PipelineResult, ResolvedItem


def _aggregate(
    resolved: list[ResolvedItem],
    project_name: str,
    catalog_file: str,
) -> PipelineResult:
    unresolved_codes = sorted({
        r.component.code
        for r in resolved
        if r.match_confidence == "unresolved"
    })
    subtotal = sum(r.line_total for r in resolved)
    source_drawings = sorted({r.component.drawing for r in resolved})
    return PipelineResult(
        project_name=project_name,
        resolved=resolved,
        unresolved_codes=unresolved_codes,
        subtotal=subtotal,
        source_drawings=source_drawings,
        catalog_file=catalog_file,
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )


def run_pipeline(
    drawings: list[Path],
    catalog: Path,
    template: Path,
    project: str,
    upper_finish: tuple[str, str, str],
    lower_finish: tuple[str, str, str],
    output_dir: Path,
    dry_run: bool = False,
) -> PipelineResult:
    components = extract_pdfs(drawings)
    resolved = resolve_catalog(components, catalog, upper_finish, lower_finish)
    pipeline_result = _aggregate(resolved, project, str(catalog))

    if dry_run:
        print(json.dumps(asdict(pipeline_result), indent=2))
        return pipeline_result

    resolved_dicts = [asdict(r) for r in pipeline_result.resolved]
    out_path = write_order_form(resolved_dicts, template, project, output_dir)

    catalog_matched = sum(1 for r in resolved if r.match_confidence != "unresolved")
    print(f"Project:    {project}")
    print(f"Drawings:   {len(drawings)} file(s)")
    print(f"Items:      {len(resolved)} total, {catalog_matched} resolved, "
          f"{len(pipeline_result.unresolved_codes)} unresolved codes")
    print(f"Subtotal:   ${pipeline_result.subtotal:,.2f}")
    print(f"Output:     {out_path}")

    return pipeline_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Boxy kitchen pipeline.")
    parser.add_argument("--drawings", required=True, nargs="+", type=Path, metavar="PDF")
    parser.add_argument("--catalog", required=True, type=Path, metavar="XLSX")
    parser.add_argument("--template", required=True, type=Path, metavar="XLSX")
    parser.add_argument("--project", required=True, metavar="NAME")
    parser.add_argument("--upper-finish", required=True, metavar="CODE:NAME:SERIES")
    parser.add_argument("--lower-finish", required=True, metavar="CODE:NAME:SERIES")
    parser.add_argument("--output-dir", default=Path("output"), type=Path, metavar="DIR")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print PipelineResult JSON; do not write xlsx")
    args = parser.parse_args()

    for p in args.drawings:
        if not p.exists():
            print(f"Error: drawing not found: {p}", file=sys.stderr)
            sys.exit(1)
    for label, p in (("catalog", args.catalog), ("template", args.template)):
        if not p.exists():
            print(f"Error: {label} not found: {p}", file=sys.stderr)
            sys.exit(1)

    upper_finish = parse_finish(args.upper_finish)
    lower_finish = parse_finish(args.lower_finish)

    try:
        run_pipeline(
            drawings=args.drawings,
            catalog=args.catalog,
            template=args.template,
            project=args.project,
            upper_finish=upper_finish,
            lower_finish=lower_finish,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
