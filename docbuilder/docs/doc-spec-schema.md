# docbuilder — Doc Spec Schema

The doc spec is the JSON contract between `compute_doc.py` and renderer scripts
(`generate_xlsx.py`, `generate_docx.py`, etc.). Renderers receive pre-computed values
and must not re-compute or re-derive anything.

---

## Top-level object

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Document title, passed through from the template. |
| `template_id` | string | Template identifier (`{tenant}/{doc_type}_v{N}`). |
| `output_formats` | array of string | Formats to render, passed through from the template. |
| `sheets` | array of [Sheet](#sheet) | Ordered list of sheets, in template order. |

---

## Sheet

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Sheet/tab name. |
| `header_row` | integer | 1-based row number where the column-header row is placed. Equal to `max(merge_range.row) + 1` when merge ranges exist, or `1` when there are none. |
| `columns` | array of [Column](#column) | Column metadata, left to right. Used by renderers for width and type-based number formatting. |
| `merge_ranges` | array of [MergeRange](#mergerange) | Merged header cells, passed through from the template unchanged. |
| `rows` | array of [Row](#row) | All content rows in display order. Does not include merge-range rows (those are in `merge_ranges`). |

---

## Column

Each entry in `Sheet.columns`. Renderer-only metadata — no row data here.
`bold` and `align` are intentionally absent: they are encoded per-cell in every `Row.cells` entry and are the sole source of truth for renderers.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Column header label. |
| `type` | string | `"string"`, `"number"`, or `"currency"`. Renderers apply `#,##0.00` format for `number`/`currency`. |
| `width` | number | Column width in character units (xlsx) / approximate em units (other formats). |

---

## MergeRange

Passed through unchanged from the template. Row and column indices are **1-based**.

| Field | Type | Description |
|-------|------|-------------|
| `row` | integer | Row number (1-based) of the merged cell. |
| `col_start` | integer | First column of the merge span (1-based, inclusive). |
| `col_end` | integer | Last column of the merge span (1-based, inclusive). |
| `value` | string | Text to display in the merged cell. |

---

## Row

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `"header"`, `"data"`, or `"aggregate"`. See below. |
| `cells` | array of [Cell](#cell) | One cell per column, in column order. |

### Row types

| Type | Source | Styling hint |
|------|--------|--------------|
| `"header"` | Column names from the template. One per sheet. | All cells bold. |
| `"data"` | Data rows from the source file (Pass 1) or summary rows (Pass 2). | Per-cell bold/align from template column definition. |
| `"aggregate"` | Computed aggregate rows (`aggregate_rows[]` in template). | All cells bold. Renderers add a thin top border. |

---

## Cell

| Field | Type | Description |
|-------|------|-------------|
| `value` | string \| number | Display value. Strings for data rows (passed through from CSV/JSON as-is). Numbers (int or float) for aggregate-computed values. |
| `bold` | boolean | Whether the cell is bold. |
| `align` | string | `"left"`, `"right"`, or `"center"`. |

---

## Complete example

Output of `compute_doc.py` for `demo/proposal_v1` with 2-row source data:

```json
{
  "title": "B2B Project Proposal",
  "template_id": "demo/proposal_v1",
  "output_formats": ["xlsx", "pdf"],
  "sheets": [
    {
      "name": "Line Items",
      "header_row": 2,
      "columns": [
        {"name": "Item Code",   "type": "string",   "width": 12},
        {"name": "Description", "type": "string",   "width": 35},
        {"name": "Quantity",    "type": "number",   "width": 10},
        {"name": "Unit Price",  "type": "currency", "width": 12},
        {"name": "Total",       "type": "currency", "width": 14}
      ],
      "merge_ranges": [
        {"row": 1, "col_start": 1, "col_end": 5,
         "value": "B2B Project Proposal — Line Items"}
      ],
      "rows": [
        {
          "type": "header",
          "cells": [
            {"value": "Item Code",   "bold": true,  "align": "left"},
            {"value": "Description", "bold": true,  "align": "left"},
            {"value": "Quantity",    "bold": true,  "align": "right"},
            {"value": "Unit Price",  "bold": true,  "align": "right"},
            {"value": "Total",       "bold": true,  "align": "right"}
          ]
        },
        {
          "type": "data",
          "cells": [
            {"value": "SRV-001",              "bold": false, "align": "left"},
            {"value": "Consulting services",  "bold": false, "align": "left"},
            {"value": "2",                    "bold": false, "align": "right"},
            {"value": "1500.00",              "bold": false, "align": "right"},
            {"value": "3000.00",              "bold": true,  "align": "right"}
          ]
        },
        {
          "type": "aggregate",
          "cells": [
            {"value": "",       "bold": true, "align": "left"},
            {"value": "TOTAL",  "bold": true, "align": "left"},
            {"value": 2,        "bold": true, "align": "right"},
            {"value": "",       "bold": true, "align": "right"},
            {"value": 3000,     "bold": true, "align": "right"}
          ]
        }
      ]
    },
    {
      "name": "Summary",
      "header_row": 2,
      "columns": [
        {"name": "Metric", "type": "string", "width": 22},
        {"name": "Value",  "type": "string", "width": 18}
      ],
      "merge_ranges": [
        {"row": 1, "col_start": 1, "col_end": 2, "value": "Proposal Summary"}
      ],
      "rows": [
        {
          "type": "header",
          "cells": [
            {"value": "Metric", "bold": true, "align": "left"},
            {"value": "Value",  "bold": true, "align": "right"}
          ]
        },
        {
          "type": "data",
          "cells": [
            {"value": "Total Line Items", "bold": true,  "align": "left"},
            {"value": 1,                  "bold": false, "align": "right"}
          ]
        },
        {
          "type": "data",
          "cells": [
            {"value": "Total Quantity",   "bold": true,  "align": "left"},
            {"value": 2,                  "bold": false, "align": "right"}
          ]
        },
        {
          "type": "data",
          "cells": [
            {"value": "Total Value (USD)", "bold": true,  "align": "left"},
            {"value": 3000,                "bold": false, "align": "right"}
          ]
        },
        {
          "type": "data",
          "cells": [
            {"value": "Notes",                                "bold": true,  "align": "left"},
            {"value": "Prices are valid for 30 days.",        "bold": false, "align": "right"}
          ]
        }
      ]
    }
  ]
}
```

---

## Renderer contract

- `columns[i]` corresponds to `rows[j].cells[i]` — column order is stable across all rows.
- `header_row` tells the renderer which physical row to write the header row to (after placing any `merge_ranges` rows first).
- `aggregate` rows are written after all `data` rows (position=bottom) or before them (position=top). The order in the `rows` array is the display order — renderers must not reorder.
- Summary sheet `data` rows (from `summary_rows`) are plain data rows. Renderers apply no special styling beyond the per-cell `bold` and `align` values.
