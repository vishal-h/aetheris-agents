# Implementation notes — m-docbuilder-m2a t5

Ticket: `compute_doc.py` pass-through of new template fields.

---

## What shipped

- `compute_doc.py`: the `compute_doc()` return dict now carries three more
  top-level keys, passed through from the template with defaults:
  - `"table_style": template.get("table_style", "Table Grid")`
  - `"data_col_start": template.get("data_col_start", 1)`
  - `"narrative": template.get("narrative")` (None when absent)
  Pure pass-through — no logic change.
- `doc-spec-schema.md`: §"Top-level object" documents the three new fields
  (type, default, which renderer consumes each) plus a note that they are
  always present so renderers can read them unconditionally.
- Tests: +2 (`test_passthrough_defaults_when_absent`,
  `test_passthrough_values_when_present`).
- Full suite: 145 passed (was 143).

---

## Effect — the template's values are now authoritative in the live pipeline

Before t5 the renderers already read these fields from the doc spec, but
`compute_doc.py` dropped them, so in the live pipeline they always fell back to
the renderer defaults (`generate_xlsx` data_col_start=1, `generate_docx`
table_style="Table Grid"). The earlier renderer tests exercised the non-default
paths by injecting the fields directly into a spec. With t5 the fields flow
through, so the template now controls them end-to-end:

- `generate_xlsx.py` ← `data_col_start`
- `generate_docx.py` ← `table_style`
- `generate_pdf.py` ← `narrative` (wired up in t7; ignored until then)

No renderer change was needed: each already reads its field(s) and the demo's
values match the prior defaults (`data_col_start: 1`, `table_style: "Table Grid"`),
so live-pipeline output is unchanged.

## Renderers tolerate the new top-level fields

The other renderers build their own output structure and ignore unknown
top-level keys. Confirmed by the full suite — notably `test_generate_json.py`
still asserts `"output_formats" not in data` (the json renderer strips top-level
metadata, so the new fields are likewise absent from its output).

---

## Forward notes

- **t7 (`generate_pdf.py` narrative mode):** `narrative` is now present in the demo
  doc spec (the demo declares it). Until t7, `generate_pdf.py` runs structured mode
  and ignores `narrative`; t7 makes it call `render_template.py` when `narrative` is
  present and `--template-dir` is supplied.
- **t8 (orchestrator):** the orchestrator does not need to pass `data_col_start` or
  `table_style` as flags — the renderers read them from the doc spec. It only needs
  to pass `--base-file` (xlsx/docx) and `--template-dir`/`--context` (pdf narrative).
- **t5 closes the pass-through list** (`table_style`, `data_col_start`, `narrative`)
  flagged in the t2/t3/t4 notes. No further pass-through fields outstanding for m2a.
