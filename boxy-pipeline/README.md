# boxy-pipeline

Extract cabinet component codes from 20-20 kitchen design PDFs, cross-reference
them against the Boxy MSRP catalog (Excel), and produce a populated Boxy Sales
Order Form (Excel) ready for review and submission.

## Install

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt
```

Requires Python 3.12 (mise-managed). The PDFs have embedded text — no OCR needed.

## Data files

Sample input files are **not committed** (`data/` is gitignored). Place them at
`data/samples/` before running:

- `Joey-_Kitchen_Plan_V2.pdf`
- `Joey-_Kitchen_2D_Plans_V2.pdf`
- `Updated_Boxy_MSRP_Sales_Order_Form.xlsx`

## Run the pipeline

```bash
python3 main.py \
  --drawings data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
             data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --catalog  data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
  --project  Joey_Kitchen_V2 \
  --upper-finish "2001:Ivory White:2000" \
  --lower-finish "2004:Mingo Oak:2000"
```

Output: `output/Joey_Kitchen_V2_order_form.xlsx`

Add `--dry-run` to print the `PipelineResult` JSON to stdout without writing a file.

## Run tests

```bash
python3 -m pytest tests/ -v
```

Integration tests (`@pytest.mark.integration`) require the sample files in
`data/samples/` and are auto-skipped when absent.

## Scripts

| Script | Role |
|--------|------|
| `scripts/plan_extractor.py` | t1 — extract codes from 20-20 PDFs → `PlanComponent` JSON |
| `scripts/catalog_resolver.py` | t2 — resolve codes against Boxy MSRP catalog → `ResolvedItem` JSON |
| `scripts/order_formatter.py` | t3 — write populated Boxy Order Form xlsx |
| `scripts/schema.py` | canonical dataclasses; no logic |
| `scripts/catalog_extractor.py` | data layer — extract all SKU × color entries from Excel → `data/catalog.jsonl` |
| `scripts/so_extractor.py` | data layer — parse Boxy sales order PDF → `data/projects/{name}/sales_order.json` |
| `main.py` | t4 — CLI wiring all three together |

Each script can also be run standalone and piped:

```bash
python3 scripts/plan_extractor.py data/samples/*.pdf \
  | python3 scripts/catalog_resolver.py \
      --catalog data/catalog.jsonl \  # or .xlsx — auto-detected by extension
      --upper-finish "2001:Ivory White:2000" \
      --lower-finish "2004:Mingo Oak:2000" \
  | python3 scripts/order_formatter.py \
      --template data/samples/Updated_Boxy_MSRP_Sales_Order_Form.xlsx \
      --project  Joey_Kitchen_V2 \
      --output-dir output/
```
