# Implementation notes — m-docbuilder-m6 t4b (DOCX pipeline wiring)

Ticket: wire the offer letter end-to-end through the existing pipeline — five changes, all
deterministic except the orchestrator system prompt. Proven by a script-chain smoke (no live
LLM; that is t5).

---

## What shipped

### (a) `compute_doc.py` — zero-source
`source_paths` argparse `nargs="+"` → `nargs="*"` (+ help note). A bundle with
`data_sources: []` (offer letter) now calls `compute_doc(template, {})` → valid spec with
`sheets: []`; the t3 `has_jinja`/`narrative` passthroughs still hold. No body change needed
(the sheet loops simply don't iterate).

### (b) `rename_output.py` — candidate_name fallback
`rename_outputs` previously raised on missing `client_name` and slugged on it. Now:
```python
name = context.get("client_name") or context.get("candidate_name") or ""
if not name:
    raise ValueError("context has neither 'client_name' nor 'candidate_name'")
...
slug = slugify(name)
```
`client_name` still wins when both are present (invoices/proposals unchanged). Docstring updated.

### (c) `docbuilder_orchestrator.exs` — docx-jinja branch + slug fallback
Three edits (before → after):

1. **Eval-time flags** (after `narrative? = is_map(template["narrative"])`): added
   ```elixir
   has_jinja?       = template["has_jinja"] == true
   narrative_template = (template["narrative"] || %{})["template_file"]
   ```
   (previously: neither existed.)

2. **`client_slug`** (was):
   `client_slug = slugify.(context["client_name"] || "")`
   (now):
   `client_slug = slugify.(context["client_name"] || context["candidate_name"] || "")`
   — mirrors the rename_output.py fallback so the orchestrator's `renamed_files` (used for
   PHASE E) matches PHASE D's actual output.

3. **`render_steps` `cond`** — added a new clause **between** the `pdf and narrative?` clause
   and the catch-all `true ->` clause:
   ```elixir
   fmt == "docx" and narrative? and has_jinja? ->
     html_args = ["scripts/generate_html.py", "--template", "#{bundle_dir}/#{narrative_template}",
                  "--context", "<CONTEXT>", "--spec", "output/pipeline_spec.json",
                  "--output", "output/#{prefix}.html"]
     docx_args = ["scripts/generate_docx_from_html.py", "--input", "output/#{prefix}.html",
                  "--output", "output/#{prefix}.docx"]
     # emits two ordered run_command steps (C{i}a generate_html with <CONTEXT> replace,
     # C{i}b generate_docx_from_html)
   ```
   A docx bundle that is NOT narrative+has_jinja still hits the catch-all → `generate_docx.py`
   (unchanged). PHASE B (compute_doc) is kept — with (a) it handles the zero-source bundle and
   writes `pipeline_spec.json`, which `generate_html --spec` consumes (harmless; the offer
   letter template uses no `tables`).

### (d) `validate_fields.py` — `title` required for offer_letter (t4 F2 adjudication)
`OFFER_LETTER_REQUIRED` now starts with `"title"` (it is the `<h1>` in `offer_letter_v1.html.j2`
and is listed required in the milestone field list). +1 test (`offer_letter` missing title →
exit 1, `title` in `missing`).

### (e) `generate_pdf.py` — css_file guard: NOT needed (confirmed, no change)
`_narrative_html` branches `if doc_spec.get("has_jinja"): return _narrative_html_jinja(...)`
**before** the `css_path = Path(template_dir) / narrative["css_file"]` line, and
`_narrative_html_jinja` never reads `css_file`. So for the offer letter (`has_jinja: true`,
`css_file: null`) the null read is unreachable. It is also docx-only, so `generate_pdf` is not
invoked at all by the orchestrator. No guard added; `generate_pdf.py` untouched.

## Done-check

- Unit: `test_compute_doc.py` zero-source ×2; `test_rename_output.py` candidate ×3;
  `test_validate_fields.py` missing-title ×1 — all PASS.
- Full docbuilder suite: **370 passed, 3 skipped** (was 364/3 at t4 core — +6).
- **Script-chain smoke (no LLM)** — compute_doc (zero source) → generate_html →
  generate_docx_from_html → rename_output (candidate_name):
  ```
  1. compute_doc → output/pipeline_spec.json   (has_jinja: True)
  2. generate_html → output/offer_letter_test.html   ({{ leaks: 0)
  3. generate_docx_from_html → output/offer_letter_test.docx   (23145 bytes)
  4. rename_output → [{"original":"output/offer_letter_test.docx",
                       "renamed":"output/ajay_rao_offer_letter_2026-07-01.docx"}]
  5. output/ajay_rao_offer_letter_2026-07-01.docx  (23K)   script-chain smoke: PASS
  ```
- **Orchestrator eval** (offer-letter context, bitloka): exit 0; resolves
  `offer_letter / v1`, output `docx`; system prompt contains the `generate_html.py` AND
  `generate_docx_from_html.py` steps and does NOT contain `generate_docx.py` → the docx-jinja
  branch fires, the legacy path is bypassed. (Live LLM run is t5's `docbuilder_offer_letter`.)

## Notes / corrections

- **Done-check command correction:** the t4b ticket's smoke uses
  `compute_doc.py --template <bundle>` — but `compute_doc.py` takes the template as a
  **positional** arg (`compute_doc.py <template> [sources…]`; the orchestrator calls it
  positionally). Ran the positional form. The corrected command is recorded here; fold the fix
  into the t5/t6 docs pass if the ticket text is referenced again.
- (e) is a confirmation, not a change — `generate_pdf.py` is not in the final Touches.
