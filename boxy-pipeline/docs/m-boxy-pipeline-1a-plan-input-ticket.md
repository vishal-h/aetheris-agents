# Ticket: main.py — accept pre-extracted plan.jsonl via --plan flag

**Depends on:**
- Consolidation patch (`m-boxy-pipeline-1a-consolidation-patch.md`) merged
- plan.jsonl output ticket (`m-boxy-pipeline-1a-plan-jsonl-ticket.md`) merged

**Context.** Once `plan_extractor.py` writes `plan.jsonl`, the pipeline
should be able to skip re-extraction and read from it directly. This:
- Speeds up repeated runs (no PDF parsing, no vision API calls)
- Enables re-running resolution with a different catalog or finish rules
  without touching the drawings
- Makes extraction and resolution independently auditable steps

**The fix:** add `--plan` flag to `main.py`. When given, skip
`extract_pdfs()` and load `PlanComponent` list from the `plan.jsonl` file.
The rest of the pipeline (resolve → consolidate → format) is unchanged.

---

## Change

**File:** `main.py`

Add `--plan` CLI flag:

```python
parser.add_argument(
    "--plan", type=Path, default=None, metavar="JSONL",
    help=(
        "Path to a pre-extracted plan.jsonl (from plan_extractor.py --output). "
        "If given, skips PDF extraction. Mutually exclusive with --drawings."
    ),
)
```

Mutual exclusivity validation:

```python
if args.plan and args.drawings:
    print("Error: --plan and --drawings are mutually exclusive", file=sys.stderr)
    sys.exit(1)
if not args.plan and not args.drawings:
    print("Error: one of --plan or --drawings is required", file=sys.stderr)
    sys.exit(1)
```

Loading function:

```python
def _load_plan_jsonl(path: Path) -> tuple[list[PlanComponent], list[str]]:
    """Load PlanComponents from a plan.jsonl file.

    Returns (components, source_drawings).
    Skips the metadata header line (_meta: true).
    """
    components = []
    source_drawings = []
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
```

Update `run_pipeline()` to accept either source:

```python
def run_pipeline(
    drawings: list[Path] | None,
    plan_jsonl: Path | None,
    catalog: Path,
    template: Path,
    project: str,
    upper_finish: tuple[str, str, str],
    lower_finish: tuple[str, str, str],
    output_dir: Path,
    dry_run: bool = False,
) -> PipelineResult:
    if plan_jsonl:
        components, _ = _load_plan_jsonl(plan_jsonl)
        print(f"Loaded {len(components)} components from {plan_jsonl}")
    else:
        components = extract_pdfs(drawings)

    resolved = resolve_catalog(components, catalog, upper_finish, lower_finish)
    pipeline_result = _aggregate(resolved, project, str(catalog))
    ...
```

Update `main()` to pass the new arguments to `run_pipeline()`.

---

## Touches

- `main.py` — add `--plan` flag, `_load_plan_jsonl`, update `run_pipeline`
  and `main`
- `tests/test_pipeline.py` — add integration test for `--plan` path

**Do not generate.**
- Changes to `plan_extractor.py`, `catalog_resolver.py`, `schema.py`,
  `order_formatter.py`, or any other file
- Any change to existing tests

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_pipeline.py -v

# First: extract to plan.jsonl (requires plan_extractor --output ticket)
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --project joey \
  --output  data/projects/

# Then: run pipeline from plan.jsonl (skips extraction)
python3 main.py \
  --plan     data/projects/joey/plan.jsonl \
  --catalog  data/catalog.jsonl \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2_from_plan \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"

# Compare output to drawings-based run (must be identical)
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/catalog.jsonl \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2_from_drawings \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"

# Verify outputs are equivalent
python3 -c "
import openpyxl

def get_items(path):
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    items = {}
    for row in ws.iter_rows(min_row=12, max_row=50, values_only=True):
        item, color, qty, price = row[1], row[2], row[3], row[4]
        if item and item not in ('Assembly Fee','Modification Fee','Delivery Fee'):
            items[item] = {'color': color, 'qty': qty, 'price': price}
    return items

plan_items = get_items('output/Joey_Kitchen_V2_from_plan_order_form.xlsx')
draw_items = get_items('output/Joey_Kitchen_V2_from_drawings_order_form.xlsx')

if plan_items == draw_items:
    print(f'✓ Both paths produce identical output ({len(plan_items)} items)')
else:
    only_plan = set(plan_items) - set(draw_items)
    only_draw = set(draw_items) - set(plan_items)
    if only_plan: print(f'Only in plan path: {only_plan}')
    if only_draw: print(f'Only in drawings path: {only_draw}')
    print('✗ Outputs differ')
"

# Verify mutual exclusivity validation
python3 main.py --plan data/projects/joey/plan.jsonl \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  --catalog data/catalog.jsonl --template data/catalog.jsonl \
  --project test --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000" 2>&1 | grep "mutually exclusive"
```

Expected: `--plan` path produces identical output to `--drawings` path,
mutual exclusivity error message shown, all tests pass.

---

## Claude-code prompt

> Implement the `--plan` flag in `main.py` per
> `docs/m-boxy-pipeline-1a-plan-input-ticket.md`.
>
> Read `main.py` in full before making any changes — you are extending
> it, not replacing it.
>
> Add `--plan` flag, `_load_plan_jsonl()`, and mutual exclusivity
> validation per §Change. Update `run_pipeline()` and `main()` to
> accept either source. The rest of the pipeline (resolve → consolidate
> → format) is unchanged.
>
> Add one `@pytest.mark.integration` test to `tests/test_pipeline.py`
> that runs the full pipeline via `--plan` and asserts the output is
> identical to the `--drawings` path.
>
> Do not modify any other file. Do not modify existing tests.
>
> Run the done-check from §Done-check — include both pipeline summary
> outputs and the equivalence check result in your review packet.
