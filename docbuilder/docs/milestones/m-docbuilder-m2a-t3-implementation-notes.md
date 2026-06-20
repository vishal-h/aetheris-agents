# Implementation notes — m-docbuilder-m2a t3

Ticket: `generate_docx.py` base-file support + `table_style`.

---

## What shipped

- `generate_docx.py`: `--base-file PATH` opens an existing document and appends
  content (sheet headings + tables) after the existing body; the base file's
  header, footer, cover page, and styles are preserved. Absent → fresh
  `Document()` (m1 behaviour, unchanged).
- `table_style` read from the doc spec (top-level, default `"Table Grid"`) and
  applied per table.
- Both heading and table-style application are **defensive** — a minimal base
  file that lacks the named style degrades gracefully instead of crashing.
- Tests: +9 (table_style default/explicit/unknown, base-file header preserved,
  tables appended, title-not-duplicated, missing-styles-degrade, CLI flag).
- Full suite: 141 passed (was 132; +9). All 17 prior docx tests still pass.

---

## Decisions

**Top-level title heading is skipped in base-file mode.**
The base docx already carries the cover/title ("B2B Project Proposal" + a
"Prepared for…" subtitle). Calling `doc.add_heading(title, level=0)` would add a
second title after the existing cover. So in base-file mode the document title
heading is skipped (the base file owns the cover); sheet headings ("Line Items",
"Summary") are still added to label each table. In fresh mode the title heading is
added as before — `test_document_title_present` still passes. This mirrors t2's
"base file owns the branding region" rule (xlsx merge-skip).

**Defensive style application ("degrade, don't crash").**
The committed demo base docx was built from a minimal template and does **not**
define the `Heading 1` or `Table Grid` styles — `doc.add_heading(name, level=1)`
and `table.style = "Table Grid"` both raise `KeyError` on it. Per CLAUDE.md
("stage CLIs degrade, they don't crash"):
- `_add_section_heading()` tries `add_heading(level=1)`; on `KeyError` it falls
  back to a bold paragraph.
- `_apply_table_style()` tries `table.style = name`; on `KeyError` it emits a
  `{"status": "warning", ...}` line to stderr and leaves the table with default
  (unstyled) formatting.
In fresh mode both styles exist, so behaviour is identical to m1 and the explicit
`table_style` test (`Light List Accent 1`) applies cleanly.

**`table_style` read at top level.** `doc_spec.get("table_style", "Table Grid")`,
consistent with the schema (top-level field). `compute_doc.py` does not pass it
through yet — that is t5 (same pattern as `data_col_start` in t2). The renderer's
default covers the live pipeline until then; no renderer change needed when t5 lands.

---

## F4 from the t2 review — `header_row` is xlsx-specific (confirmed)

The t2 review (F4) asked t3 to state this explicitly: **the docx renderer does not
use `header_row` for positioning.** It builds each table from the logical `rows`
array in order (header → data → aggregate), so the demo's `header_row: 3` is
irrelevant to docx output. This is not a missed requirement — `header_row` governs
physical cell placement, which only applies to xlsx. The docx (and csv/json/xml/md,
and pdf via `_build_html()`) renderers are row-array driven. No change needed here.

---

## Carried asset items (base files need a regeneration pass before t8)

Two placeholder-base-file deficiencies now block *visual* quality (not the
pipeline — both degrade gracefully). Recommend a single asset commit to regenerate
both demo base files before the t8 sprint:

1. **docx base file lacks named styles** (`Heading 1`, `Table Grid`). Tables in the
   branded docx currently render without grid borders, and sheet headings fall back
   to bold paragraphs. Regenerate `proposal_v1.docx` from a template that includes
   the standard styles (or inject them) so `table_style: "Table Grid"` applies.
2. **xlsx Summary base sheet is under-built** (flagged at t1, t1-addendum, t2). Its
   `Summary` sheet has only a single styled row — no logo/navy branding rows like
   `Line Items`. Add branding rows 1–2 to match.

Neither is fixed here (t3 is script + tests + notes; base files are binary assets).
The defensive fallbacks mean the pipeline produces valid output regardless.

## Forward notes

- **t5 pass-through list:** `table_style`, `data_col_start`, `narrative` all need to
  flow `compute_doc.py` → doc spec. xlsx and docx renderers already read them with
  defaults; t5 makes the defaults unnecessary for the live pipeline.
- **t8 orchestrator:** pass `--base-file …/{doc_type}_{version}.docx` to the docx
  renderer (and `.xlsx` to xlsx). Expect the table-style warning on stderr until the
  docx base file is regenerated (asset item 1).
