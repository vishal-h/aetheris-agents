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

- **`title` is NOT rendered in the letter body.** It is the document-title field (e.g. "Offer
  Letter — Ajay Rao") used for the output filename / metadata, not letter content. The body
  opens with the letterhead + date + To block per the reference. Cross-check confirmed the
  other 17 required fields all render.
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

## Scope held

Only `offer_letter_v1.html.j2` changed (+ the pre-t1 doc correction). No `offer_letter_v1.json`,
`catalogue.json`, pipeline script, `validate_fields.py`, or sprint/test file touched. No
separate `.css` file (inline per D1).
