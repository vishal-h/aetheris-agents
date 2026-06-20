# Implementation notes — m-docbuilder-m2a t1

Ticket: template schema update + demo assets.

---

## What shipped

- `template-schema.md`: three new optional top-level fields (`table_style`,
  `data_col_start`, `narrative`) + a `Narrative` object section; full example
  updated.
- `proposal_v1.json`: added `table_style: "Table Grid"`, `data_col_start: 1`,
  `narrative` block; `output_formats` now `["xlsx", "docx", "pdf"]`.
- `proposal_v1.md.template`, `proposal_v1.css`: narrative-mode demo assets.
- `sample_data_summary.csv`: second data source (committed, not yet wired).
- `data/.gitignore`: whitelisted the three new committed files (+ the summary CSV).

---

## Decisions made

**`data_sources` left at one entry (deferred to t4).**
The original t1 prompt asked to bump `data_sources` to two entries. But the m1
multi-source guard in `compute_doc.py` (`len(data_sources) > 1 → raise`) is not
removed until t4, and t2/t3 done-checks run the full pipeline through
`compute_doc.py`. Adding the second source in t1 would have broken t2 and t3.
Per the milestone-doc update agreed before this ticket: the `summary` source is
wired into the template in t4, alongside the guard removal, so the schema change
and guard removal land together. `sample_data_summary.csv` is committed now
because t4 needs it; the template does not reference it yet. The t1 done-check
now asserts `len(data_sources) == 1`.

**`output_formats` extended to include `"docx"`.**
The milestone goal is branded output in xlsx, docx, and pdf; the t9 catalogue
declares all three; t8's sprint verifies all three. The template is the single
declaration of intent, and t1 owns the template, so `"docx"` was added here
rather than surfacing as a surprise at t8 (whose scope excludes template edits).
Safe for t2/t3/existing tests: renderers don't gate on `output_formats`, and
`compute_doc.py` doesn't pass the new fields through until t5.

**Table partials use exact sheet names, not the prompt's lowercase slugs.**
The prompt illustrated `{{>line_items}}` / `{{>summary}}`. t6's `render_template.py`
matches partials to sheets by `name` (case-insensitive). `line_items` would NOT
match the sheet named `Line Items` (space vs underscore). The committed
`proposal_v1.md.template` therefore uses `{{>Line Items}}` and `{{>Summary}}` so
the t6 done-check — which renders this exact template and asserts a `<table>` is
produced — stays green. The schema doc's Narrative section documents this rule.

**gitignore: summary CSV needed an explicit whitelist.**
The prompt only listed `!proposal_v1.md.template` and `!proposal_v1.css`. But
`data/.gitignore` ignores `*.csv` with only `sample_data.csv` whitelisted, so
`sample_data_summary.csv` would have been silently untracked. Added
`!sample_data_summary.csv`. Verified all three new committed files with
`git check-ignore`.

---

## Base file verification (t1 scope: "verify header_row: 3 alignment") — finding for t2

Inspected the committed placeholder base files:

**`proposal_v1.xlsx`**
- `Line Items`: row 1 = `[ LOGO ]` (A1) + `Company Name` (B1:E1 merged); rows 2–3 empty.
- `Summary`: empty.

**`proposal_v1.docx`**
- Body: title + "Prepared for…" subtitle paragraphs.
- Header: `[ LOGO ]\tCompany Name`. Footer: `Confidential | Page of`.
- No tables (t3 appends them).

**The alignment does not cleanly match `header_row: 3` today — t2 must resolve it.**
Two unreconciled facts:
1. The template's `Line Items` `merge_ranges` sits on **row 1**, which is exactly
   where the base file places the logo/company branding. `compute_doc.py` computes
   `header_row = max(merge_row) + 1 = 2`, so the structured renderer would write the
   proposal-title merge onto the logo row and the column header at row 2 — colliding
   with branding.
2. The t2 done-check comment expects the column header at **row 3** (it only
   `print`s the cell, so it will not fail, but the intent is row 3).

`header_row` is currently a **computed** value (from `merge_ranges`), not a stored
template field — even though README §"Row alignment convention" describes it as a
template field equal to the first empty row of the base file. Reconciling this is
base-file-support work and belongs in t2. Recommended options for t2:
- **Make `header_row` an explicit per-sheet template field** (README's stated model),
  set `Line Items` → `3`, and have `compute_doc.py` honour it when present (fall back
  to the computed value when absent). The base file would then own rows 1 (logo) and
  2 (a title/spacer), with column headers at row 3.
- **Or** have `generate_xlsx.py` skip/relocate `merge_ranges` that fall within
  base-file-owned rows (above `header_row`) so branding is never overwritten.

Either way, the placeholder base file likely needs a small tweak in t2 (e.g. a title
row 2) so the logo row and the proposal-title merge don't collide. Flagged here so
t2 starts from a known state rather than rediscovering it.

---

## Forward notes

- t2 (`generate_xlsx.py`): the `header_row` / merge-collision finding above is the
  primary input. `data_col_start` is `1` in the demo, so column-skip logic is
  exercised by tests but not by the demo template.
- t4: wire `summary` into `data_sources`; decide whether the `Summary` sheet
  consumes it (`source_key: "summary"`) or keeps deriving from `summary_rows`.
- t6/t7 (narrative): partials are `{{>Line Items}}` / `{{>Summary}}`; scalar vars are
  `{{title}}`, `{{client_name}}`, `{{date}}`. CSS uses weasyprint `@page` margin boxes
  for header (`[ LOGO ]` / `Company Name`) and footer (page counter).
