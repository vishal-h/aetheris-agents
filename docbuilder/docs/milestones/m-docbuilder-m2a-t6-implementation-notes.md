# Implementation notes — m-docbuilder-m2a t6

Ticket: `render_template.py` — Markdown + CSS → HTML (narrative-mode PDF input).

---

## What shipped

- `scripts/render_template.py` (new): `--template`, `--css`, `--context` (inline
  JSON), `--spec` (path or `-`). Substitutes `{{variable}}` scalars, replaces
  `{{>Sheet Name}}` partials with HTML tables from the doc spec, runs the result
  through python-markdown (`tables` ext), wraps in a full HTML document linking the
  CSS, prints to stdout. Exit 1 on error; warnings (unknown var / unknown partial)
  go to stderr as `{"status":"warning",...}` and do not fail.
- `tests/test_render_template.py` (new): 11 tests.
- Full suite: 156 passed (was 145; +11).

---

## New dependency: `markdown` (third-party, not stdlib)

The prompt described `markdown` as a "stdlib library" — it is not; it's the
third-party `Markdown` PyPI package. It was not installed in the mise env, so I
installed it (`python3 -m pip install markdown` → 3.10.2), matching how docbuilder's
other renderer deps (openpyxl, python-docx, weasyprint) are simply present in the env
rather than declared in a requirements file.

- Tests `pytest.importorskip("markdown")` at module top, consistent with the
  openpyxl/python-docx skip pattern, so the suite degrades gracefully where it's absent.
- **t10 docs-sync candidate:** docbuilder has no `requirements.txt` (unlike
  boxy-pipeline/eduloka/drive/provenance). Worth adding one at t10 listing
  `openpyxl`, `python-docx`, `weasyprint`, `markdown` so the env is reproducible.

---

## Decisions

**Table logic replicated, not imported.** `_render_table()` mirrors the per-sheet
markup of `generate_pdf.py`'s `_build_html()` (merge_ranges as `<th colspan>`,
`class='aggregate'`, inline `text-align`/`font-weight`). I deliberately did **not**
import `generate_pdf` — it imports `weasyprint` at module load, and the prompt
requires the t6 tests to run without weasyprint. The small duplication keeps
`render_template.py` weasyprint-free and independently testable. (t7/t10 could later
factor the shared table markup into a helper module both import, if desired.)

**Markdown raw-HTML passthrough.** Partials are replaced with `<table>…</table>`
blocks *before* the markdown conversion. python-markdown preserves block-level raw
HTML (a block starting with `<table>`, surrounded by blank lines in the template),
so the table passes through verbatim while the surrounding prose is converted
(`#` → `<h1>`, `**` → `<strong>`). Verified end-to-end.

**Disjoint placeholder regexes.** `{{variable}}` uses `\w+`, which never matches
`{{>Sheet Name}}` (the `>` and spaces aren't `\w`), so scalar substitution and
partial replacement are independent and order doesn't matter. Partial matching is
case-insensitive (`sheets_by_name` keyed on `name.lower()`), so `{{>line items}}`
resolves the "Line Items" sheet — this answers the t2-review F-note that t6 must
handle sheet names with spaces under the case-insensitive rule.

**CSS href = absolute `file://` URI.** `Path(css).resolve().as_uri()` yields an
absolute `file:///…/proposal_v1.css` link so weasyprint (t7) resolves the stylesheet
regardless of the working directory, rather than relying on a relative path + base_url.

---

## Forward notes

- **t7 (`generate_pdf.py` narrative mode):** call `render_template.py` as a subprocess
  (per the milestone prompt) when the doc spec has `narrative` and `--template-dir` is
  supplied; pass its stdout HTML to `weasyprint.HTML(string=…).write_pdf()`. `narrative`
  already flows through the doc spec (t5), and the demo template declares it, so t7's
  done-check can use the real pipeline doc spec.
- **t8 (orchestrator):** passes `--template-dir` (locating `.md.template` + `.css`) and
  `--context` to `generate_pdf.py`; `generate_pdf.py` resolves the two filenames from
  the `narrative` block and invokes `render_template.py`.
