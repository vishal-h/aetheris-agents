# boxy-pipeline runbook

Operational guide for the boxy-pipeline use case. For design background, see
`docs/m-boxy-pipeline.md`.

---

## Prerequisites

- Python 3.12 (mise-managed — check `mise.toml` at repo root)
- Sample files at `boxy-pipeline/data/samples/` (gitignored — never commit)

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt
```

---

## Running the full pipeline

```bash
cd aetheris-agents/boxy-pipeline

python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2 \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"
```

Expected output:

```
Project:    Joey_Kitchen_V2
Drawings:   2 file(s)
Items:      27 total, 7 resolved, 14 unresolved codes
Subtotal:   $5,346.45
Output:     output/Joey_Kitchen_V2_order_form.xlsx
```

---

## CLI reference

| Flag | Required | Description |
|------|----------|-------------|
| `--drawings <pdf> [<pdf> ...]` | yes | One or more 20-20 PDF drawings |
| `--catalog <xlsx_or_jsonl>` | yes | Boxy MSRP Excel file (Price List sheets) **or** pre-extracted `data/catalog.jsonl`; auto-detected by `.jsonl` extension |
| `--template <xlsx>` | yes | Boxy Order Form template (may be same file as catalog) |
| `--project <name>` | yes | Project name; used as output filename stem |
| `--upper-finish <code:name:series>` | yes | Finish spec for wall cabinets, e.g. `"2001:Ivory White:2000"` |
| `--lower-finish <code:name:series>` | yes | Finish spec for base/tall cabinets, e.g. `"2004:Mingo Oak:2000"` |
| `--output-dir <dir>` | no | Output directory (default: `output/`) |
| `--dry-run` | no | Print `PipelineResult` JSON to stdout; do not write xlsx |

---

## Running individual scripts

Each script is independently runnable and pipe-composable.

**t1 — plan_extractor**

```bash
python3 scripts/plan_extractor.py <pdf> [<pdf> ...] | python3 -m json.tool | head -60
```

Outputs a JSON array of `PlanComponent` dicts.

**t2 — catalog_resolver**

```bash
python3 scripts/catalog_resolver.py \
  --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000" \
  < <(python3 scripts/plan_extractor.py data/samples/*.pdf)
```

Reads `PlanComponent` JSON from stdin; outputs `ResolvedItem` JSON.

**t3 — order_formatter**

```bash
python3 scripts/order_formatter.py \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2 \
  --output-dir output/ \
  < resolved_items.json
```

Reads `ResolvedItem` JSON from stdin; writes `output/{project}_order_form.xlsx`.

---

## Data layer

Scripts that build or read the persistent data files (stored under `data/`,
gitignored — never commit).

**catalog_extractor — build catalog.jsonl**

```bash
cd aetheris-agents/boxy-pipeline
python3 scripts/catalog_extractor.py \
  --catalog data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --output  data/catalog.jsonl
```

Reads all Price List sheets from the Excel template; writes one JSON record per
SKU × color combination to `data/catalog.jsonl` (4,594 entries for the Joey
project catalog). Run once per catalog version. Subsequent pipeline runs can pass
`data/catalog.jsonl` to `--catalog` instead of the Excel file — same results,
faster startup.

**so_extractor — parse a sales order PDF**

```bash
python3 scripts/so_extractor.py \
  --so         data/samples/SO86708_Aria_Joey.pdf \
  --project    joey \
  --output-dir data/projects/
```

Extracts line items, header, and totals from a Boxy PDF sales order; writes
`data/projects/{project}/sales_order.json`.

**main.py — full pipeline using JSONL catalog**

```bash
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/catalog.jsonl \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2 \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"
```

Passing `data/catalog.jsonl` instead of the Excel file skips pandas/openpyxl
overhead on each run. The `--template` flag still requires the Excel file — it
is used only by `order_formatter.py` for the output sheet structure, not for
catalog lookup.

**Enrichment note**: `catalog.jsonl` includes `mapped_20_20_codes` and `notes`
fields for future manual enrichment. Re-running `catalog_extractor.py` regenerates
the file from Excel and overwrites any hand-edits — merge before re-extracting if
enrichment data needs to be preserved.

---

## Running tests

```bash
cd aetheris-agents/boxy-pipeline

# All tests
python3 -m pytest tests/ -v

# Single ticket
python3 -m pytest tests/test_plan_extractor.py -v
python3 -m pytest tests/test_catalog_resolver.py -v
python3 -m pytest tests/test_order_formatter.py -v
python3 -m pytest tests/test_pipeline.py -v

# Skip integration (no sample files needed)
python3 -m pytest tests/ -v -m "not integration"
```

Integration tests are auto-skipped when `data/samples/` files are absent.

---

## Finish spec format

`--upper-finish` and `--lower-finish` each take a colon-separated string:

```
<color_code>:<color_name>:<series>
```

Example: `"2001:Ivory White:2000"` — color code 2001 (Ivory White), series 2000
(Frameless Regular Shaker).

The Joey kitchen project uses:
- Uppers: `"2001:Ivory White:2000"`
- Lowers & Talls: `"2004:Mingo Oak:2000"`

---

## Understanding the output

The output Excel file opens directly in the Boxy Sales Order Form format:
- Rows 12–38: line items (cabinet codes, color, qty, unit price, amount formula)
- Rows 39–41: fee placeholder rows (Assembly Fee, Modification Fee, Delivery Fee)
  — fill in manually before submission
- Rows 42–67: blank — formatter clears all cells in this range; no VLOOKUP formulas
- Row 68: subtotal (`=SUM($F12:$F67)`)

The output file contains only the `2000 Order Form` sheet; all Price List and other
Order Form sheets from the template are stripped before saving.

Items with `match_confidence: "unresolved"` appear in the form with a blank Color
and Unit Price, and `"UNRESOLVED - manual review required"` in the Special Request
column. These require manual lookup and entry before submission.

---

## Troubleshooting

**`No module named pdfplumber`** — run `pip install -r requirements.txt` from the
`boxy-pipeline/` directory (not system pip).

**`Error: drawing not found: ...`** — sample PDFs are gitignored. Copy them to
`data/samples/` from the project source.

**Integration tests skipped** — expected when `data/samples/` files are absent.
Place the files and re-run.

**`KeyError` in catalog_resolver** — the Excel catalog format may have changed.
Check that the Price List sheet names match `{N}000 Price List` and that row 1
(0-indexed) is the header row with color codes.

**Appliance codes unresolved** — expected. Codes like `KFNF 9959 iDE`, `G 7186 SCVi`,
`DA 6698 W` are manufacturer-specific and have no Boxy catalog equivalent. Enter
them manually in the order form.
