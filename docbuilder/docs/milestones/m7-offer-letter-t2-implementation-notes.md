# Implementation notes — m7 t2 (bundle spec + logo)

Ticket: add `"pdf"` to the offer-letter `output_formats` (PDF primary, DOCX secondary), copy
`btl_logo-withtext.png` into the offer-letter bundle, and update the catalogue. No pipeline
script changes.

---

## What shipped

- **`offer_letter_v1.json`** — `output_formats` `["docx"]` → `["pdf", "docx"]` (PDF first =
  primary, D6). All other fields unchanged (`has_jinja: true`, `css_file: null`, `sheets: []`).
- **`offer_letter_v1.png`** … actually `btl_logo-withtext.png` (new) — **copied byte-identical**
  from the invoice bundle (`data/templates/bitloka/invoice/v1/btl_logo-withtext.png`, 68509 B).
  **No placeholder needed** — the real asset is committed in the invoice bundle. (Note: the file
  is JPEG content with a `.png` name — the existing bundle convention; WeasyPrint sniffs content,
  and the template references `btl_logo-withtext.png`, so it resolves correctly.)
- **`catalogue.json`** — offer_letter v1 variant `output_formats` → `["pdf", "docx"]`;
  description → "branded PDF (primary) … DOCX secondary draft". Invoice entry untouched.

## Done-check

Ran the §t2 verification (with one correction — see below): **PASS** — spec `output_formats`
`["pdf","docx"]` (pdf first), logo present in bundle, catalogue v1 in sync `["pdf","docx"]`.
Invoice catalogue entry unchanged (`["xlsx","docx","pdf"]`).

**End-to-end PDF render (m6 "check the artifact" lesson — de-risks t3):** `compute_doc`
(zero-source) → `generate_pdf` (has_jinja → `generate_html` → WeasyPrint) with the t1 sample
context → **84K PDF, `%PDF`, zero `{{`, logo embedded** (1 `/Image` XObject); content verified
(candidate, role, Net Monthly Take Home, Business Performance Bonus with `default('March/April')`,
signatory). The logo resolves via `base_url` = bundle dir (D3) — confirmed working now that the
asset is in the bundle.

## Done-check command correction (carry to t4)

The §t2 done-check's catalogue check iterates `for e in cat` — but `catalogue.json` is
`{"tenant_id": ..., "doc_types": [...]}` (a dict), so it must iterate **`cat["doc_types"]`**
(`e['doc_type']` on the dict's string keys would raise). Ran the corrected form. Same class as
the t4b `compute_doc --template` positional fix — recorded here; fold the corrected command into
the milestone doc at t4 if the §t2 block is referenced again.

## Scope held

Only `offer_letter_v1.json`, the new `btl_logo-withtext.png`, and the `catalogue.json`
offer_letter entry changed. No pipeline script (`generate_pdf.py`/`generate_html.py`/
`generate_docx_from_html.py`/`compute_doc.py`/orchestrator), no `css_file` handling (stays null,
D7), no v2 bundle.
