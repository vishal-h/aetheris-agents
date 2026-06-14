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
from schema import PipelineResult, PlanComponent, ResolvedItem

_CONFIDENCE_RANK = {"exact": 0, "fuzzy": 1, "unresolved": 2}


def _consolidate(resolved: list[ResolvedItem]) -> list[ResolvedItem]:
    """Consolidate ResolvedItems by code across drawings.

    Groups items by component.code. For each group, sums qty, picks the
    best catalog_item and match_confidence, merges match_notes, and sets
    component.drawing to "multiple" when the code appeared on >1 drawing.
    """
    from collections import defaultdict
    groups: dict[str, list[ResolvedItem]] = defaultdict(list)
    for item in resolved:
        groups[item.component.code].append(item)

    consolidated = []
    for code, items in groups.items():
        total_qty = sum(i.qty for i in items)
        drawings = {i.component.drawing for i in items}

        best_item = next(
            (i for i in items if i.catalog_item is not None), items[0]
        )
        unit_price = best_item.unit_price

        best_confidence = min(
            items, key=lambda i: _CONFIDENCE_RANK.get(i.match_confidence, 99)
        ).match_confidence

        notes = list(dict.fromkeys(
            n for i in items if i.match_notes
            for n in [i.match_notes]
        ))
        merged_notes = "; ".join(notes) if notes else None

        consolidated_component = PlanComponent(
            code=code,
            drawing="multiple" if len(drawings) > 1 else next(iter(drawings)),
            qty=total_qty,
            notes=None,
        )

        consolidated.append(ResolvedItem(
            component=consolidated_component,
            catalog_item=best_item.catalog_item,
            qty=total_qty,
            unit_price=unit_price,
            line_total=unit_price * total_qty,
            match_confidence=best_confidence,
            match_notes=merged_notes,
        ))

    return consolidated


def _aggregate(
    resolved: list[ResolvedItem],
    project_name: str,
    catalog_file: str,
) -> PipelineResult:
    consolidated = _consolidate(resolved)
    unresolved_codes = sorted({
        r.component.code
        for r in consolidated
        if r.match_confidence == "unresolved"
    })
    subtotal = sum(r.line_total for r in consolidated)
    source_drawings = sorted({
        d
        for r in resolved
        for d in [r.component.drawing]
    })
    return PipelineResult(
        project_name=project_name,
        resolved=consolidated,
        unresolved_codes=unresolved_codes,
        subtotal=subtotal,
        source_drawings=source_drawings,
        catalog_file=catalog_file,
        extracted_at=datetime.now(timezone.utc).isoformat(),
    )


def _load_plan_jsonl(path: Path) -> tuple[list[PlanComponent], list[str]]:
    """Load PlanComponents from a plan.jsonl file.

    Returns (components, source_drawings).
    Skips the metadata header line (_meta: true).
    """
    components = []
    source_drawings: list[str] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get("_meta"):
                source_drawings = obj.get("source_drawings", [])
                continue
            components.append(PlanComponent(**obj))
    return components, source_drawings


def run_pipeline(
    drawings: list[Path] | None,
    catalog: Path,
    template: Path,
    project: str,
    upper_finish: tuple[str, str, str],
    lower_finish: tuple[str, str, str],
    output_dir: Path,
    plan_jsonl: Path | None = None,
    dry_run: bool = False,
) -> PipelineResult:
    if plan_jsonl:
        components, _ = _load_plan_jsonl(plan_jsonl)
        print(f"Loaded {len(components)} components from {plan_jsonl}", file=sys.stderr)
    else:
        components = extract_pdfs(drawings)

    resolved = resolve_catalog(components, catalog, upper_finish, lower_finish)
    pipeline_result = _aggregate(resolved, project, str(catalog))

    if dry_run:
        print(json.dumps(asdict(pipeline_result), indent=2))
        return pipeline_result

    resolved_dicts = [asdict(r) for r in pipeline_result.resolved]
    out_path = write_order_form(resolved_dicts, template, project, output_dir)

    catalog_matched = sum(
        1 for r in pipeline_result.resolved if r.match_confidence != "unresolved"
    )
    print(f"Project:    {project}")
    if plan_jsonl:
        print(f"Plan:       {plan_jsonl}")
    else:
        print(f"Drawings:   {len(drawings)} file(s)")
    print(f"Items:      {len(pipeline_result.resolved)} total, {catalog_matched} resolved, "
          f"{len(pipeline_result.unresolved_codes)} unresolved codes")
    print(f"Subtotal:   ${pipeline_result.subtotal:,.2f}")
    print(f"Output:     {out_path}")

    return pipeline_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Boxy kitchen pipeline.")
    parser.add_argument("--drawings", nargs="+", type=Path, metavar="PDF", default=None)
    parser.add_argument("--plan", type=Path, default=None, metavar="JSONL",
                        help=(
                            "Path to a pre-extracted plan.jsonl "
                            "(from plan_extractor.py --output). "
                            "Skips PDF extraction. Mutually exclusive with --drawings."
                        ))
    parser.add_argument("--catalog", required=True, type=Path, metavar="XLSX")
    parser.add_argument("--template", required=True, type=Path, metavar="XLSX")
    parser.add_argument("--project", required=True, metavar="NAME")
    parser.add_argument("--upper-finish", required=True, metavar="CODE:NAME:SERIES")
    parser.add_argument("--lower-finish", required=True, metavar="CODE:NAME:SERIES")
    parser.add_argument("--output-dir", default=Path("output"), type=Path, metavar="DIR")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print PipelineResult JSON; do not write xlsx")
    args = parser.parse_args()

    if args.plan and args.drawings:
        print("Error: --plan and --drawings are mutually exclusive", file=sys.stderr)
        sys.exit(1)
    if not args.plan and not args.drawings:
        print("Error: one of --plan or --drawings is required", file=sys.stderr)
        sys.exit(1)

    if args.drawings:
        for p in args.drawings:
            if not p.exists():
                print(f"Error: drawing not found: {p}", file=sys.stderr)
                sys.exit(1)
    if args.plan and not args.plan.exists():
        print(f"Error: plan not found: {args.plan}", file=sys.stderr)
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
            plan_jsonl=args.plan,
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
