# Implementation notes — m7 t1 (`offer_letter_v1.html.j2` — HTML + inline CSS)

Ticket: replace the bare `offer_letter_v1.html.j2` with a complete HTML + inline CSS template
matching the Bitloka FTE offer letter (A4, logo, Calibri, three comp tables, conditionals,
boilerplate, footer). Template only — no pipeline/spec/sprint changes.

---

## Pre-t1 doc correction (committed `db3a430`)

Before writing the template I reconciled a **field-name contradiction** in the milestone doc:
its Context-fields table (inferred from the reference DOCX by claude-ui without repo state)
used names that don't exist in the pipeline (`candidate_title`, `basic_salary`, split address,
`start_date`, `has_performance_bonus`). **The code is the source of truth (methodology §1.1).**
I corrected the doc's field table + the t1 done-check context dict to the actual
`OFFER_LETTER_REQUIRED` (18 fields) + the m6 `OPTIONAL_FIELDS` names, dropped `start_date`, and
fixed 19→18. `validate_fields.py` is unchanged (frozen, per scope). A template built against the
old names would have rendered `""` silently (the m6 t5 `jinja2.Undefined` bug class).

## What shipped

- **`offer_letter_v1.html.j2`** (replaced) — complete HTML + **inline CSS** (D1):
  - `@page { size: A4; margin: 1.3cm; }`, body `Calibri, 'Gill Sans', sans-serif` 10pt,
    text `#1A1A2E` (D5/page).
  - Header: `<img src="btl_logo-withtext.png">` (resolves at render time via WeasyPrint
    `base_url` = bundle dir, D3) + "Bitloka Solutions Private Limited" bold 12pt, orange
    bottom rule.
  - To block (`candidate_name`, flat `candidate_address`, `candidate_email | candidate_phone`),
    "Re: Offer of Employment" subject, offer paragraph (`role`).
  - **Conditionals:** `{% if internship_acknowledgement %}` paragraph;
    `{% if business_performance_bonus_pct %}` bonus section with a nested
    `{% if individual_performance_bonus_pct %}`, periods via `default('March/April')` /
    `default('September/October')`.
  - CTC line (`annual_ctc`); three tables — **Earnings** (basic/hra/lta/wfh/flexi +
    bold Total Earnings), **Deductions** (PT/TDS + bold Total Deductions), **Net** (single
    13pt bold row). Table header rows `background:#F5A623; color:#fff` (D4); body cells
    `1px solid #ccc` (D4).
  - Hardcoded boilerplate: notice period ("eight (8) weeks"), T&C, Documents Required list,
    NDA, signatory ("Vishal Honnatti / Director"), footer address.

## Decisions / notes

- **`title` is NOT rendered in the letter body** (corrected per t1 review F5). `title` is a
  required `OFFER_LETTER_REQUIRED` context field, but it does **not** drive the filename and is
  not letter content: `rename_output.py` slugs the **`candidate_name`** fallback for the output
  filename (`{candidate_name_slug}_{doc_type}_{date}.ext`), and `compute_doc` takes the doc-spec
  title from the **bundle spec** (`template["title"]`), not from context. So `title` is
  validated-but-not-rendered here; the body opens with the letterhead + date + To block per the
  reference. Cross-check confirmed the other 17 required fields all render.
- **Amount column header is "Amount", not "Amount (₹)".** Per D5 the currency values are
  display strings that already carry `₹` (e.g. `₹37,500.00`); a "(₹)" header would double the
  symbol. The symbol lives in the value.
- **All required fields use `{{ field | default('') }}`** — defensive (they're required, but
  this keeps the template robust and matches the m6 invoice convention).
- **Logo dependency:** the `<img>` references `btl_logo-withtext.png`, which **t2 copies** into
  the bundle. t1's standalone done-check renders HTML (no asset resolution), so it passes
  without the file; the actual PDF/DOCX render (t3) needs t2's logo in place.

## Done-check

`python3 -c "<§t1 done-check>"` → **PASS — template renders cleanly, tables present,
conditionals toggle.** No `{{ }}` leaks; Earnings/Deductions/Net tables present; internship +
bonus sections render when their triggers are set and are suppressed when empty.

Field-coverage cross-check (sentinel value per `OFFER_LETTER_REQUIRED` field): **17/17**
substantive fields referenced in the template (`title` excluded — doc metadata, not body).

## Round-1 review fixes (claude-ui)

- **F1 [blocking] — Net row rendered 11pt normal, not 13pt bold (CSS cascade).** `table.comp
  tbody td {font-size:11pt}` (0,1,3) out-specified `table.net td {…13pt bold}` (0,1,2). Fixed
  by making the Net table **standalone** `class="net"` (dropped `comp`) with its own
  border/padding/13pt-bold rules — `table.comp tbody td` no longer matches it at all, so there
  is no competing rule (not just a higher-specificity one). Verified: HTML has `<table class="net">`,
  no `class="comp net"`.
- **F2 [blocking] — bonus heading/independent conditionals.** Restructured to
  `{% if business_… or individual_… %}` wrapping the heading, then each bonus paragraph guarded
  independently. Verified: individual-only bonus → heading + individual line render (business
  absent); both absent → section fully suppressed.
- **F3 [non-blocking] — subject underline.** Added `text-decoration: underline` to `.subject`.
- **F4 [non-blocking] — phone guard.** `candidate_phone` IS required (in `OFFER_LETTER_REQUIRED`),
  so it's always present; added a defensive `{% if candidate_phone %} | {{ … }}{% endif %}` so
  an empty value can't leave a trailing `email | `. Verified: absent phone → no trailing pipe.
- **F5 [question] — title vs candidate_name.** Resolved + the title note above corrected: the
  filename slug uses `candidate_name`; `title` is validated-but-not-rendered. t3's sprint slug
  assertion should target the `candidate_name` slug (`ajay_rao_offer_letter_*`).

Re-ran the done-check plus all four edge cases above → **ALL CHECKS PASS**.

## Scope held

Only `offer_letter_v1.html.j2` changed (+ the pre-t1 doc correction). No `offer_letter_v1.json`,
`catalogue.json`, pipeline script, `validate_fields.py`, or sprint/test file touched. No
separate `.css` file (inline per D1).
