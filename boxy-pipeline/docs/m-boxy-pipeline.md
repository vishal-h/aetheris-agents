# Milestone: boxy-pipeline

**Goal.** Given a set of 20-20 kitchen design drawings (PDF), extract all
cabinet component codes, cross-reference them against the Boxy MSRP catalog
(Excel), and produce a populated Boxy Sales Order Form (Excel) ready for
review and submission.

**What exists before this milestone.** Nothing. Greenfield Python package.

**What exists after.** A standalone Python package `boxy_pipeline/` with:
- three scripts (extractor, catalog resolver, order formatter)
- a canonical JSON schema (`schema.py`)
- pytest unit + integration coverage
- a `main.py` CLI that runs the full pipeline end-to-end

**Out of scope.**
- Aetheris agents or orchestration of any kind
- Cabinet Vision integration
- Any web UI or API
- Handling manufacturer catalogs other than Boxy MSRP Excel
- Multi-series mixing per project (series 2000 used throughout; parameterisable in a future ticket)
- Fee row computation (Assembly, Delivery, Modification — placeholder rows only)

**Sample files (committed to `data/samples/`, anonymised).**
- `Joey-_Kitchen_Plan_V2.pdf` — 20-20 floor plan (1 page)
- `Joey-_Kitchen_2D_Plans_V2.pdf` — 20-20 elevation drawings (4 pages: El1–El4)
- `Updated_Boxy_MSRP_Sales_Order_Form.xlsx` — Boxy catalog + order form template
- `SO86708_Aria_Joey.pdf` — reference output (completed sales order); used
  as ground truth for formatter validation only

---

## Repository layout

Follows the `aetheris-agents/` use-case convention. Lives at
`aetheris-agents/boxy-pipeline/`.

```
aetheris-agents/
  boxy-pipeline/
    scripts/
      plan_extractor.py     ← t1: extract codes from 20-20 PDFs
      catalog_resolver.py   ← t2: cross-reference codes → CatalogItems
      order_formatter.py    ← t3: write populated Boxy Order Form xlsx
      schema.py             ← canonical dataclasses; no logic
    main.py                 ← t4: CLI wiring all three together
    data/
      samples/              ← committed (anonymised) sample inputs
      .gitignore            ← excludes real client data
    output/
      .gitkeep              ← gitignored; local only
    tests/
      conftest.py
      test_plan_extractor.py   ← t1
      test_catalog_resolver.py ← t2
      test_order_formatter.py  ← t3
      test_pipeline.py         ← t4 end-to-end
    docs/
      m-boxy-pipeline.md    ← this file
      t*-implementation-notes.md  ← written by claude-code after each ticket
    README.md
```

`.gitignore` for the use case:
```
# Client data — never commit
data/*
!data/.gitkeep

# Generated output — local only
output/*
!output/.gitkeep
```

**No `agents/` directory.** This milestone is pure Python scripts; there is
no Aetheris agent. A future milestone may add an orchestrator agent on top.

---

## Dependencies

Pinned in `requirements.txt`. Install once before running any script or test:

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt
```

| Library | Version | Role |
|---|---|---|
| `pdfplumber` | ≥0.11.9 | Extracts embedded text from 20-20 PDFs |
| `pandas` | ≥3.0.2 | Reads Boxy MSRP Excel catalog |
| `openpyxl` | ≥3.1.5 | pandas xlsx engine; also used directly to write Order Form formulas |
| `pytest` | ≥8.0.0 | Test runner |

**Do not substitute `pytesseract`, `pdf2image`, or any OCR library.**
The 20-20 PDFs have embedded text — OCR is unnecessary and will produce
worse results. `pdfplumber` is the correct tool for this input type.

**Data files are not committed.** `data/` is fully gitignored. Place the
sample files at `data/samples/` on disk before running done-checks.
If the files are missing, report and stop — do not attempt to recreate them.

---

## Canonical schema (`schema.py`)

The schema is the contract between all three scripts. It is defined once here
and referenced by ticket prompts; it must not be restated or paraphrased in
ticket prompts.

```python
@dataclass
class PlanComponent:
    code: str           # raw code from drawing, e.g. "DB30", "BLB42FHL", "W2739"
    drawing: str        # source drawing label, e.g. "floor_plan", "El1", "El2"
    qty: int            # default 1; incremented when same code appears multiple times
    notes: Optional[str]  # any annotation text captured near the component

@dataclass
class CatalogItem:
    sku: str              # full SKU incl. color code, e.g. "3DB30-2004"
    series: str           # "2000", "3000", etc.
    color_code: str       # "2001", "2004", etc.
    color_name: str       # "Ivory White", "Mingo Oak"
    description: str      # full description from catalog
    cabinet_type: str     # "Base Cabinet", "Wall Cabinet", "Accessory", etc.
    width_in: Optional[float]
    height_in: Optional[float]
    depth_in: Optional[float]
    msrp: float

@dataclass
class ResolvedItem:
    component: PlanComponent
    catalog_item: Optional[CatalogItem]   # None = unresolved
    qty: int
    unit_price: float
    line_total: float
    match_confidence: str   # "exact", "fuzzy", "unresolved"
    match_notes: Optional[str]

@dataclass
class PipelineResult:
    project_name: str
    resolved: list[ResolvedItem]
    unresolved_codes: list[str]   # codes that had no catalog match
    subtotal: float
    source_drawings: list[str]
    catalog_file: str
    extracted_at: str   # ISO datetime
```

---

## Tickets

---

### t1 — Plan extractor

**Scope.** `extractors/plan_extractor.py` reads one or more 20-20 design PDF
files and returns a JSON array of `PlanComponent` dicts to stdout. It handles
both floor plan and elevation drawing layouts. No catalog lookup; no pricing.

**Contract refs.**
- `schema.py` — `PlanComponent` is the output type; reference the file,
  do not restate the fields.
- `docs/m-boxy-pipeline.md §Repository layout` — file locations.

**Approach.**
The 20-20 PDFs contain embedded text (they are not scanned images). Cabinet
codes appear as short uppercase alphanumeric strings (e.g. `DB30`, `BLB42FHL`,
`W2739`, `DCW2439R`, `USF330`, `FSEP2493`). The extractor uses `pdfplumber`
to extract text per page, then applies a regex to identify component codes.

Known code patterns from the sample drawings:
- Base cabinets: `[0-9]?[A-Z]{1,3}[0-9]{2,4}[A-Z]*` (e.g. `DB30`, `3DB21`,
  `SB42`, `BBC42`, `BSR09`, `OVB36`, `BPBC12`, `BPBC9`)
- Wall cabinets: `W[0-9]{4}`, `DCW[0-9]{4}[LR]?`, `WDC[0-9]{4}[LR]?`
- Tall/specialty: `USF[0-9]{3}`, `SUW[0-9]{4}-[0-9]{2}`, `WP[0-9]{4}-[0-9]{2}[A-Z]*`
- Appliance/filler codes from non-Boxy sources (e.g. `KFNF 9959 iDE`,
  `G 7186 SCVi`, `DA 6698 W`) — capture these too; they will be flagged
  as unresolved by the resolver.

Drawing label detection: each PDF page has a footer identifying the drawing
(`All`, `El 1`, `El 2`, `El 3`, `El 4`). Extract this and set `drawing` field.

Deduplication: if the same code appears multiple times on the same drawing,
increment `qty` rather than emit duplicate records. Across drawings, emit
separate records (same code may appear in multiple elevations for context).

**Touches.**
- `scripts/plan_extractor.py` (new)
- `scripts/schema.py` (new — shared canonical types, written once in t1)
- `requirements.txt` (new — per `docs/m-boxy-pipeline.md §Dependencies`)
- `tests/test_plan_extractor.py` (new)
- `tests/conftest.py` (new)

**Do not generate.**
- Catalog lookup or pricing logic
- OCR (the PDFs have embedded text; no image processing needed)
- `main.py` or any other file outside Touches

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v
# Also verify standalone execution:
python3 scripts/plan_extractor.py data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf | python3 -m json.tool | head -60
```

Expected: JSON array with ≥15 distinct component codes extracted, each with
`code`, `drawing`, `qty`, `notes` fields. `DB30`, `BLB42FHL`, `W2739`,
`SB42`, `USF330` must be present.

**Claude-code prompt.**
> Implement `scripts/plan_extractor.py` per `docs/m-boxy-pipeline.md §t1`.
> The canonical output type is `PlanComponent` in `scripts/schema.py` — create
> that file first with the full schema from `docs/m-boxy-pipeline.md §Canonical schema`;
> do not restate the fields in this prompt.
> Also create `requirements.txt` per `docs/m-boxy-pipeline.md §Dependencies`.
>
> Sample files are at `data/samples/` on disk but not committed. If they
> are missing, stop and report — do not attempt to recreate them.
>
> The 20-20 PDFs have embedded text (not scanned). Use `pdfplumber` to extract
> text per page. Apply regex matching per the code patterns in §t1. Detect
> the drawing label from the page footer. Deduplicate per-drawing by
> incrementing `qty`. Emit JSON array to stdout; errors to stderr; exit 0
> on success, 1 on failure.
>
> Write `tests/test_plan_extractor.py` with unit tests covering: code
> detection regex, drawing label detection, deduplication logic, and at least
> one integration test against the real sample PDFs in `data/samples/`.
> Write `tests/conftest.py` with the standard skip-marker pattern from
> `aetheris-agents/CLAUDE.md`.
>
> Run the done-check from §t1 and include the actual output in your review
> packet.

---

### t2 — Catalog resolver

**Scope.** `utils/catalog_resolver.py` loads the Boxy MSRP Excel catalog
and, given a list of `PlanComponent` dicts (from t1 stdout), resolves each
to a `ResolvedItem`. Outputs a JSON array of `ResolvedItem` dicts to stdout.

**Contract refs.**
- `schema.py` — `PlanComponent`, `CatalogItem`, `ResolvedItem` are the types.
- `docs/m-boxy-pipeline.md §t2 — Catalog resolver` (this section).

**Catalog structure (do not restate in ticket prompt; reference this section).**

The Excel file has sheets named `{N}000 Price List` (N = 1–5) and
`{N}000 Order Form`. Only the Price List sheets are needed for resolution.

Each Price List sheet has:
- Row 1 (0-indexed): header row. Columns: `NO.`, `Image`, `Item`,
  `Description`, and one column per color (e.g. `2001\nIvory White\nMSRP`,
  `2004\nMingo Oak\nMSRP`).
- Category separator rows: col 4 contains strings like
  `WALL CABINET\n39" Height` — these are section labels, not items.
- Item rows: col 2 = item code (e.g. `W0939`), col 3 = description,
  col 4+ = MSRP per color.

Series mapping: sheet `1000 Price List` → series `"1000"` (Framed Regular
Shaker). Sheet `2000 Price List` → series `"2000"` (Frameless Regular
Shaker). The sales order for the Joey kitchen uses series 2000/3000 (the
SO86708 sample shows `-2004` and `-2001` suffixes on SKUs).

**Resolution logic.**

A 20-20 code like `DB30` maps to a Boxy base code. The resolver must:

1. Normalise the plan code: strip leading digit (e.g. `3DB21` → `DB21`
   may indicate qty 3 or a variant; keep raw code and try both).
2. Look up the base code in the catalog (exact match on the `Item` column).
3. If multiple series match, prefer the series indicated by the finish
   assignment in the drawing notes (Lowers = 2004 Mingo Oak / series 2000
   or 3000; Uppers = 2001 Ivory White / series 2000 or 3000).
4. Build the full SKU: `{item_code}-{color_code}` (e.g. `DB30-2004`).
5. Set `match_confidence`:
   - `"exact"` — direct item code match found in catalog
   - `"fuzzy"` — matched after normalisation or partial strip
   - `"unresolved"` — no catalog match (appliance codes, non-Boxy items)

Finish rules from the sample drawings:
- `Finish 1 Uppers: Ivory White` → color code `2001`, series 2000
- `Finish 2 Lowers & Talls: Mingo Oak` → color code `2004`, series 2000

These finish rules should be configurable (passed as a resolver argument),
not hardcoded, since they vary per project.

**Touches.**
- `scripts/catalog_resolver.py` (new)
- `tests/test_catalog_resolver.py` (new)

**Do not generate.**
- Order form writing logic
- `main.py`
- Any modification to `scripts/schema.py`

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_catalog_resolver.py -v
# Pipe t1 output into t2:
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 scripts/catalog_resolver.py \
    --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --upper-finish "2001:Ivory White:2000" \
    --lower-finish "2004:Mingo Oak:2000" \
  | python3 -m json.tool | head -80
```

Expected: JSON array of `ResolvedItem` dicts. `DB30` resolves to
`DB30-2004` with `match_confidence: "exact"`. Appliance codes
(`KFNF 9959 iDE`, `G 7186 SCVi`) appear as `unresolved`. At least 10
`exact` matches present.

**Claude-code prompt.**
> Implement `scripts/catalog_resolver.py` per `docs/m-boxy-pipeline.md §t2`.
> The canonical types are in `scripts/schema.py` — read that file.
> The catalog structure is described in §t2 of the milestone doc — read
> that section; do not restate the column layout here.
>
> The resolver reads `PlanComponent` JSON from stdin and writes
> `ResolvedItem` JSON to stdout. Accept CLI flags:
> `--catalog <path>`, `--upper-finish <code:name:series>`,
> `--lower-finish <code:name:series>`.
>
> Load the catalog once at startup using pandas. For each component, apply
> the resolution logic in §t2. Emit JSON array to stdout; errors to stderr.
>
> Write `tests/test_catalog_resolver.py` covering: catalog loading,
> exact match, fuzzy match after code normalisation, unresolved code
> handling, and finish rule application. Use `cwd=USE_CASE_ROOT` in
> subprocess calls per `aetheris-agents/CLAUDE.md`.
>
> Run the done-check from §t2 and include the actual output in your review
> packet.

---

### t3 — Order formatter

**Scope.** `scripts/order_formatter.py` takes a `PipelineResult` JSON
(from t2 aggregation) and writes a populated Boxy Order Form Excel file to
the output directory. The output matches the structure of the
`{N}000 Order Form` sheets in the catalog Excel — specifically the 2000
series sheet, since the Joey kitchen uses Frameless Regular Shaker.

**Contract refs.**
- `scripts/schema.py` — `PipelineResult`, `ResolvedItem` are the input types.
- `docs/m-boxy-pipeline.md §t3 — Order formatter` (this section).

**Order Form sheet structure (do not restate in ticket prompt).**

The `2000 Order Form` sheet has:
- Rows 0–9: header metadata (dealer, PO#, need date, shipping, assembly,
  address, contact — all empty cells to be filled)
- Row 10: column headers — `Line`, `*ITEM`, `*Color`, `*QTY`,
  `Unit Price`, `Amount`, `*Hinge`, `Add on 1`, `Add on 2`,
  `Modification 1`, `Modification or Special Request Details`
- Rows 11+: one line per item (up to ~60 lines in the template)

The formatter fills:
- `*ITEM` — base item code (e.g. `DB30`)
- `*Color` — color code (e.g. `2004`)
- `*QTY` — quantity
- `Unit Price` — MSRP from `ResolvedItem.unit_price`
- `Amount` — formula `=E{row}*D{row}` (not hardcoded)
- `Modification or Special Request Details` — `ResolvedItem.match_notes`
  if present, plus `"UNRESOLVED - manual review required"` for unresolved
  items

Unresolved items: still included, with ITEM = raw plan code, Color and
Unit Price left blank, and a note in the Special Request column.

Fee placeholder rows: after all cabinet line items, append three blank
placeholder rows with ITEM set to `Assembly Fee`, `Modification Fee`, and
`Delivery Fee` respectively, all other columns empty. These are not
derivable from drawings; they exist so the reviewer can fill them in.

The formatter opens the template Excel, writes into the correct sheet,
saves to `output/{project_name}_order_form.xlsx`. It does NOT modify the
price list sheets.

**Touches.**
- `scripts/order_formatter.py` (new)
- `tests/test_order_formatter.py` (new)

**Do not generate.**
- `main.py`
- Any modification to `scripts/schema.py` or other scripts

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_order_formatter.py -v
# Full pipeline smoke test (t1 → t2 → aggregate → t3):
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  | python3 scripts/catalog_resolver.py \
    --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --upper-finish "2001:Ivory White:2000" \
    --lower-finish "2004:Mingo Oak:2000" \
  | python3 scripts/order_formatter.py \
    --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
    --project "Joey_Kitchen_V2" \
    --output-dir output/
ls -lh output/
```

Expected: `output/Joey_Kitchen_V2_order_form.xlsx` created. Open and
verify: ≥10 line items populated, Amount column contains formulas not
hardcoded values, at least one unresolved item flagged.

**Claude-code prompt.**
> Implement `scripts/order_formatter.py` per
> `docs/m-boxy-pipeline.md §t3`.
> The input type is `PipelineResult` from `scripts/schema.py` — read that file.
> The Order Form sheet structure is described in §t3 — read that section.
>
> The formatter reads `PipelineResult` JSON from stdin. It opens the
> template Excel using openpyxl, writes line items into the `2000 Order
> Form` sheet starting at row 11, uses Excel formulas for the Amount
> column (not Python-calculated values), saves to
> `{output_dir}/{project_name}_order_form.xlsx`.
>
> Accept CLI flags: `--template <path>`, `--project <name>`,
> `--output-dir <dir>` (default `"output"`).
>
> Write `tests/test_order_formatter.py` covering: line item writing,
> formula presence in Amount cells, unresolved item flagging, output
> file creation.
>
> Run the done-check from §t3 and include the actual output in your
> review packet.

---

### t4 — Pipeline CLI (`main.py`)

**Scope.** `main.py` wires the three scripts into a single CLI command.
It also adds a `PipelineResult` aggregation step between t2 and t3
(grouping `ResolvedItem` list + metadata into a `PipelineResult`).

**Contract refs.**
- `scripts/schema.py` — `PipelineResult` is the aggregation output type.
- `docs/m-boxy-pipeline.md §t4 — Pipeline CLI` (this section).

**CLI interface.**

```
python3 main.py \
  --drawings <pdf> [<pdf> ...] \
  --catalog <xlsx> \
  --template <xlsx>           # may be same file as catalog \
  --project <name> \
  --upper-finish <code:name:series> \
  --lower-finish <code:name:series> \
  [--output-dir <dir>]        # default: output/ \
  [--dry-run]                 # print PipelineResult JSON, do not write xlsx
```

The pipeline:
1. Call `plan_extractor` → list of `PlanComponent`
2. Call `catalog_resolver` → list of `ResolvedItem`
3. Aggregate into `PipelineResult` (sum subtotal, collect unresolved codes,
   set metadata)
4. Call `order_formatter` → write xlsx
5. Print a summary to stdout: total items, resolved count, unresolved
   codes, output file path

**Touches.**
- `main.py` (new)
- `tests/test_pipeline.py` (new — end-to-end integration test)

**Do not generate.**
- Any modification to t1/t2/t3 scripts unless a genuine bug is found
  (note any such fix in implementation notes)

**Done-check.**
```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_pipeline.py -v
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project Joey_Kitchen_V2 \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"
```

Expected: summary printed to stdout, `output/Joey_Kitchen_V2_order_form.xlsx`
created, exit code 0. Summary must show ≥10 resolved items.

**Claude-code prompt.**
> Implement `main.py` per `docs/m-boxy-pipeline.md §t4`.
> The aggregation type is `PipelineResult` from `scripts/schema.py` — read that
> file.
>
> Import and call the three scripts as Python modules (not via subprocess).
> Add the `PipelineResult` aggregation step between resolver and formatter.
> Implement the `--dry-run` flag.
>
> Write `tests/test_pipeline.py` with one end-to-end integration test
> against the sample files in `data/samples/`. Mark it
> `@pytest.mark.integration`. Use `cwd=USE_CASE_ROOT` per
> `aetheris-agents/CLAUDE.md`. It should assert: exit code 0, output file
> created, at least 10 resolved items.
>
> Run the done-check from §t4 and include actual output in your review
> packet.
