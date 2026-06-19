# docbuilder — Template Schema

Reference for `docbuilder/data/templates/{tenant}/{doc_type}_v{N}.json`.
Every field is documented below with type, required/optional, and an example value.

---

## Top-level object

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `template_id` | string | yes | Unique slug: `{tenant}/{doc_type}_v{N}` | `"demo/proposal_v1"` |
| `title` | string | yes | Human-readable document title; used as the document heading | `"B2B Project Proposal"` |
| `data_sources` | array of [DataSource](#datasource) | yes | Ordered list of data sources. **m1: exactly one entry required.** | see below |
| `output_formats` | array of string | yes | Formats to render in sequence. Valid values: `"xlsx"`, `"docx"`, `"pdf"`, `"csv"`, `"json"`, `"xml"`, `"md"` | `["xlsx", "pdf"]` |
| `sheets` | array of [Sheet](#sheet) | yes | Ordered list of sheets/sections. Each sheet becomes one tab in xlsx, one table in docx, etc. | see below |

> **m1 constraint:** `compute_doc.py` rejects templates where `data_sources` has more than one entry
> (exits 1 with `{"status": "error", "error": "m1 supports exactly one data_source"}`).
> Multi-source support lands in m2 — the schema is forward-compatible.

---

## DataSource

Each entry in `data_sources`.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `key` | string | yes | Identifier used by `Sheet.source_key` to reference this source. Must be unique within the template. | `"main"` |
| `type` | string | yes | Source type. m1 values: `"csv"`, `"json"`. | `"csv"` |
| `path` | string | yes | Path to the data file, relative to the aetheris-agents sandbox root. | `"docbuilder/data/sample_data.csv"` |

---

## Sheet

Each entry in `sheets`.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `name` | string | yes | Sheet/section name. Becomes the worksheet tab name in xlsx. | `"Line Items"` |
| `source_key` | string or null | yes | Key of the `DataSource` this sheet reads from. `null` for summary sheets that derive all values from `summary_rows`. | `"main"` |
| `columns` | array of [Column](#column) | yes | Column definitions, left to right. | see below |
| `merge_ranges` | array of [MergeRange](#mergerange) | no | Merged header cells. Typically row 1. | see below |
| `aggregate_rows` | array of [AggregateRow](#aggregaterow) | no | Computed rows appended above or below data rows. Used when `source_key` is non-null. | see below |
| `summary_rows` | array of [SummaryRow](#summaryrow) | no | Rows for sheets where `source_key` is null. Each row references an aggregate from another sheet or is a static label/value pair. | see below |

---

## Column

Each entry in `Sheet.columns`.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `name` | string | yes | Column header label (displayed in row 2 when a merge_range occupies row 1). | `"Unit Price"` |
| `source_field` | string or null | yes | Field name in the raw data rows. `null` for summary-sheet columns that have no direct data mapping. | `"unit_price"` |
| `type` | string | yes | Data type hint used by renderers for formatting. Values: `"string"`, `"number"`, `"currency"`. | `"currency"` |
| `bold` | boolean | yes | Whether data cells in this column are bold. Header cells are always bold. | `true` |
| `align` | string | yes | Horizontal alignment for data cells. Values: `"left"`, `"right"`, `"center"`. | `"right"` |
| `width` | number | yes | Column width in character units (xlsx) / approximate em units (other formats). | `14` |

---

## MergeRange

Each entry in `Sheet.merge_ranges`.

Row and column indices are **1-based** throughout (matching xlsx cell notation).

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `row` | integer | yes | Row number (1-based) of the merged cell. | `1` |
| `col_start` | integer | yes | First column of the merge span (1-based, inclusive). | `1` |
| `col_end` | integer | yes | Last column of the merge span (1-based, inclusive). | `5` |
| `value` | string | yes | Text to display in the merged cell. | `"B2B Project Proposal — Line Items"` |

---

## AggregateRow

Each entry in `Sheet.aggregate_rows`. Applies only to sheets with `source_key` non-null.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `position` | string | yes | Where to place the row relative to data rows. Values: `"top"`, `"bottom"`. | `"bottom"` |
| `label` | string | yes | Text placed in the `label_column` cell of the aggregate row. | `"TOTAL"` |
| `label_column` | string | yes | `source_field` value of the column that receives the label text. | `"description"` |
| `aggregates` | array of [Aggregate](#aggregate) | yes | Per-column aggregation specs. Columns not listed here are left blank in the aggregate row. | see below |

### Aggregate

Each entry in `AggregateRow.aggregates`.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `column` | string | yes | `source_field` value of the column to aggregate. | `"total"` |
| `function` | string | yes | Aggregation function. Values: `"sum"`, `"count"`, `"avg"`. | `"sum"` |

---

## SummaryRow

Each entry in `Sheet.summary_rows`. Applies only to sheets with `source_key: null`.
Two row types are supported: `"aggregate_ref"` and `"static"`.

### type: `"aggregate_ref"`

References an aggregated value computed from a data-bearing sheet.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `type` | string | yes | Must be `"aggregate_ref"`. | `"aggregate_ref"` |
| `label` | string | yes | Label text (placed in the first column). | `"Total Value (USD)"` |
| `aggregate` | [SummaryAggregate](#summaryaggregate) | yes | Pointer to the source sheet and column to aggregate. | see below |

#### SummaryAggregate

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `source_sheet` | string | yes | `name` of the sheet whose data to aggregate. | `"Line Items"` |
| `column` | string | yes | `source_field` of the column to aggregate (must exist on the referenced sheet). | `"total"` |
| `function` | string | yes | Aggregation function. Values: `"sum"`, `"count"`, `"avg"`. | `"sum"` |

### type: `"static"`

A fixed label/value pair — not derived from data.

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `type` | string | yes | Must be `"static"`. | `"static"` |
| `label` | string | yes | Label text (placed in the first column). | `"Notes"` |
| `value` | string | yes | Value text (placed in the second column). | `"Prices are valid for 30 days."` |

---

## Full example

```json
{
  "template_id": "demo/proposal_v1",
  "title": "B2B Project Proposal",
  "data_sources": [
    {
      "key": "main",
      "type": "csv",
      "path": "docbuilder/data/sample_data.csv"
    }
  ],
  "output_formats": ["xlsx", "pdf"],
  "sheets": [
    {
      "name": "Line Items",
      "source_key": "main",
      "merge_ranges": [
        {"row": 1, "col_start": 1, "col_end": 5, "value": "B2B Project Proposal — Line Items"}
      ],
      "columns": [
        {"name": "Item Code",   "source_field": "item_code",   "type": "string",   "bold": false, "align": "left",  "width": 12},
        {"name": "Description", "source_field": "description", "type": "string",   "bold": false, "align": "left",  "width": 35},
        {"name": "Quantity",    "source_field": "quantity",    "type": "number",   "bold": false, "align": "right", "width": 10},
        {"name": "Unit Price",  "source_field": "unit_price",  "type": "currency", "bold": false, "align": "right", "width": 12},
        {"name": "Total",       "source_field": "total",       "type": "currency", "bold": true,  "align": "right", "width": 14}
      ],
      "aggregate_rows": [
        {
          "position": "bottom",
          "label": "TOTAL",
          "label_column": "description",
          "aggregates": [
            {"column": "quantity", "function": "sum"},
            {"column": "total",    "function": "sum"}
          ]
        }
      ]
    },
    {
      "name": "Summary",
      "source_key": null,
      "merge_ranges": [
        {"row": 1, "col_start": 1, "col_end": 2, "value": "Proposal Summary"}
      ],
      "columns": [
        {"name": "Metric", "source_field": null, "type": "string", "bold": true,  "align": "left",  "width": 22},
        {"name": "Value",  "source_field": null, "type": "string", "bold": false, "align": "right", "width": 18}
      ],
      "summary_rows": [
        {
          "type": "aggregate_ref",
          "label": "Total Line Items",
          "aggregate": {"source_sheet": "Line Items", "column": "item_code", "function": "count"}
        },
        {
          "type": "aggregate_ref",
          "label": "Total Value (USD)",
          "aggregate": {"source_sheet": "Line Items", "column": "total", "function": "sum"}
        },
        {
          "type": "static",
          "label": "Notes",
          "value": "Thank you for your business. Prices are valid for 30 days."
        }
      ]
    }
  ]
}
```

---

## Validation rules enforced by `compute_doc.py`

| Rule | Error |
|------|-------|
| `data_sources` has more than one entry | `"m1 supports exactly one data_source"` (exit 1) |
| A `source_field` referenced by a column is absent from the raw data rows | `"source_field '{field}' not found in source '{key}'"` (exit 1) |
| A `summary_row.aggregate.source_sheet` name does not match any sheet `name` | `"source_sheet '{name}' not found"` (exit 1) |
| `output_formats` contains an unrecognised format string | `"unknown output_format '{fmt}'"` (exit 1) |
| `aggregate_rows[].aggregates[].function` is not `sum`, `count`, or `avg` | `"unknown aggregate function '{fn}'"` (exit 1) |
