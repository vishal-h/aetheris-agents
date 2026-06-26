# Review — m-docbuilder-m6 t4 (core) — round 1

Reviewer: claude-ui
Subject: offer_letter bundle + validate_fields, core (commit `c931465`)

---

## Findings

1. [non-blocking] `offer_letter_v1.json` has `"css_file": null`. The legacy
   `_narrative_html` path in `generate_pdf.py` reads `narrative["css_file"]` to
   resolve the CSS path. If the orchestrator ever calls the PDF render path for an
   offer_letter bundle (before m7 adds PDF support), it will attempt
   `Path(template_dir) / None` and raise `TypeError`. This is not a t4 issue — the
   offer_letter is docx-only and the PDF path will not be reached via the
   orchestrator prompt (t4b wires this correctly). Noting for t4b: confirm the
   orchestrator's render branch for `has_jinja` + `output_formats: ["docx"]` does not
   accidentally call `generate_pdf.py`. If needed, add a guard in `_narrative_html`:
   `if doc_spec.get("css_file") is None: skip CSS resolution`. Carry to t4b review.

2. [non-blocking] The `_offer_letter()` test fixture sets `"title": "Offer Letter —
   Ajay Rao"` but `title` is not in `OFFER_LETTER_REQUIRED`. The valid test passes
   because `title` is present in the fixture, not because it is required. This is
   intentional — `title` is in `BASE_REQUIRED` but offer_letter uses the complete
   `OFFER_LETTER_REQUIRED` list which omits it. If `title` should be required for
   offer letters, add it to `OFFER_LETTER_REQUIRED`. If not (the letter heading comes
   from `candidate_name` + `role`), this is correct as-is. No action required —
   noting for the record; confirm intent in t4b or t5 implementation notes.

## Cross-ticket notes

- F1 (css_file null) is a t4b watch item — confirm the DOCX render branch does not
  accidentally fall through to the PDF path.
- The `test_offer_letter_does_not_require_client_fields` regression guard is exactly
  right — this is the most important test in the offer_letter set and explicitly
  protects the `OFFER_LETTER_REQUIRED`-replaces-`BASE_REQUIRED` design decision.
- t4b prompt should include: (a) `compute_doc.py` zero-source fix, (b)
  `rename_output.py` `candidate_name` fallback, (c) orchestrator DOCX-jinja branch.
  All three should have tests. The orchestrator prompt change is highest-risk — worth
  an end-to-end script-chain smoke (not a live LLM run) in t4b's done-check.

Clean. 29 tests pass, 364/3 suite, smoke confirms zero `{{` leaks, conditional sections
verified both absent and present.

---

## Disposition

**t4 core clear to merge as-is** (code unchanged from `c931465`). Both findings non-blocking;
both routed to t4b:

- **F2 adjudicated: `title` IS required for offer_letter.** The milestone §"Offer letter field
  list" lists `title` as the first required field, and `offer_letter_v1.html.j2` renders it as
  the `<h1>`. `OFFER_LETTER_REQUIRED` omitting it is a real gap (the valid test passes only
  because the fixture includes `title`). Per the reviewer's "confirm in t4b" suggestion and to
  keep t4 merged as-is, the fix — add `"title"` to `OFFER_LETTER_REQUIRED` + a missing-title
  test — is **folded into t4b**.
- **F1: `css_file: null` PDF-path guard** — t4b must confirm the docx-jinja render branch never
  reaches `generate_pdf._narrative_html` for the offer_letter (it shouldn't, output_formats is
  docx-only); add the `css_file is None` guard only if a path can reach it.

Both are recorded in the t4b scope below (carried into the milestone doc when t4b is drafted).
