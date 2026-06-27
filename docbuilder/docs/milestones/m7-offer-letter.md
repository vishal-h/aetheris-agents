# m7 — Offer Letter Refinements

**Repo:** `aetheris-agents` · **Base commit:** `eeb37a1`
**Milestone path:** `docbuilder/docs/milestones/m7-offer-letter.md`

---

## Goal

Replace the bare `offer_letter_v1.html.j2` (no CSS, no logo, Pandoc heading-style
problem) with a proper HTML + inline CSS template that faithfully reproduces the
Bitloka FTE offer letter. WeasyPrint PDF becomes the primary output; Pandoc DOCX
is secondary (a draft the recipient edits in Word before sending).

The m6 pipeline wiring is correct and must not be changed. m7 is template +
bundle-spec only, plus a sprint-case update to assert PDF + DOCX outputs.

---

## What is NOT in scope

- Any change to pipeline scripts: `generate_html.py`, `generate_pdf.py`,
  `generate_docx_from_html.py`, `compute_doc.py`, orchestrator `.exs` files
- New doc types or new template variants
- Shared tenant asset directory (logo lives in the bundle for now — shared dir
  is a future consideration)
- `compute_offer.py` salary computation
- `is_intern` boolean field (conditional rendering stays Jinja `{% if %}` on
  the existing string field `internship_acknowledgement`)
- Context builder optional-field-name awareness (BL / m6-t5 F2 — bonus field
  names off-schema)
- Removing `render_template.py` / `.md.template` (deferred from m6)
- Any change to `validate_fields.py` `OFFER_LETTER_REQUIRED` (18 fields, stable)

---

## Design decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Inline CSS** in the `.html.j2` (no separate `.css` file) | Self-contained; no `base_url` path resolution needed for styles. Matches the StringTemplate pattern Bitloka already uses. A shared CSS base for future doc types can be extracted later. |
| D2 | **Logo** copied to `data/templates/bitloka/offer_letter/v1/btl_logo-withtext.png` | Confirmed in m6 closing discussion. `<img src="btl_logo-withtext.png">` resolves via `base_url` = bundle dir (same path WeasyPrint already uses for the invoice). |
| D3 | **`base_url` for WeasyPrint** is already set to the bundle dir in `generate_pdf._narrative_html_jinja` | The invoice uses the same path; no change to `generate_pdf.py` needed. The offer-letter logo resolves identically. |
| D4 | **Table borders: `1px solid #ccc`** (light grey) for body cells; header row uses Bitloka orange `#F5A623` background with white text | WeasyPrint renders `border: 1px solid #ccc` cleanly on A4. Orange header matches the invoice's branding accent. ⚠️ **Human confirm required** — if you prefer all-grey headers (no orange), say so before approving this doc. Default is orange-header / grey-body as stated. |
| D5 | **Currency values are display strings in the sprint context** — e.g. `"₹37,500.00"` not `37500` | Validated-as-money → kept as display string (same design as `amount_due` for invoices). The sprint case must supply them pre-formatted. `validate_fields.py` keeps them as-is. |
| D6 | **Output format change**: `offer_letter_v1.json` changes from `output_formats: ["docx"]` to `output_formats: ["pdf", "docx"]` | PDF (WeasyPrint) is primary. DOCX (Pandoc) is secondary. No pipeline change required — the orchestrator already has both branches wired from m6. |
| D7 | **`css_file: null`** in `offer_letter_v1.json` stays null | The `_narrative_html_jinja` path does not read `css_file`. Inline CSS makes this permanently correct — no change needed. |

---

## Reference letter structure (authoritative)

Source: `BTL-Offer_Letter-_Template_-_FTE_-_Ajay_Rao.docx` (inspected in m6 closing discussion)

**Page:** A4 (8.27" × 11.69"), 1.3cm margins all round → CSS: `@page { size: A4; margin: 1.3cm; }`

**Fonts:** Calibri 10pt throughout. WeasyPrint uses system fonts; fall back to
`font-family: Calibri, 'Gill Sans', sans-serif`.

**Document sections (in order):**

1. **Header** — logo left + "Bitloka Solutions Private Limited" bold 12pt right (or
   below logo). Date line below header, `space_after: 12pt`.
2. **To block** — candidate name, address lines. `space_after: 2pt` per line.
3. **Subject line** — "Re: Offer of Employment" (bold inline).
4. **Offer paragraph** — body text 10pt.
5. **[CONDITIONAL] Internship acknowledgement** — paragraph only if
   `internship_acknowledgement` is non-empty (`{% if internship_acknowledgement %}`).
6. **CTC line** — "Your annual CTC is ₹X,XX,XXX.00."
7. **Monthly earnings table** (Table 1):
   - Header row: bold 12pt, orange background (#F5A623), white text
   - Body rows: 11pt
   - Columns: Earnings | Amount (₹)
   - Rows: Basic Salary | HRA | LTA | WFH Allowance | Flexi Pay | **Total Earnings** (bold 12pt)
8. **Monthly deductions table** (Table 2):
   - Same sizing as Table 1
   - Columns: Deductions | Amount (₹)
   - Rows: Professional Tax | TDS @ 10% | **Total Deductions** (bold 12pt)
9. **Net take-home table** (Table 3):
   - Single row, bold 13pt
   - Net Monthly Take Home | ₹XX,XXX.00
10. **[CONDITIONAL] Performance bonuses section** — only if `business_performance_bonus_pct`
    is non-empty (`{% if business_performance_bonus_pct %}`; no `has_performance_bonus` flag):
    - Business Performance Bonus: `business_performance_bonus_pct`% of CTC, provisioned in
      `business_performance_bonus_period` (`default('March/April')`)
    - Individual Performance Bonus: `individual_performance_bonus_pct`% of CTC, provisioned in
      `individual_performance_bonus_period` (`default('September/October')`)
11. **Notice period paragraph** — hardcoded "eight (8) weeks"
12. **Terms and Conditions** — boilerplate paragraph
13. **Documents Required** — boilerplate list
14. **NDA paragraph** — boilerplate
15. **Signature block** — hardcoded "Vishal Honnatti / Director"
16. **Footer** — `#311/1, Zikhin Bhavan, 26th X, BSK II Stage, Bangalore - 560070 | www.bitloka.com | contact@bitloka.com`

---

## Context fields

> **Authoritative source = `validate_fields.py` `OFFER_LETTER_REQUIRED`, read from the repo
> (not the reference DOCX).** The Phase-1 draft of this table inferred field names from the
> DOCX structure and was wrong (`candidate_title`, `basic_salary`, split address, `start_date`,
> `has_performance_bonus` etc. do not exist). Corrected below to the actual pipeline schema —
> the template MUST use these exact names, or `jinja2.Undefined` silently renders `""`
> (the m6 t5 class of bug). `validate_fields.py` is unchanged (frozen, per §"NOT in scope").

**Required — the 18 `OFFER_LETTER_REQUIRED` fields (all display strings):**

| Field | Notes |
|-------|-------|
| `title` | Document title (e.g. `Offer Letter — Ajay Rao`) |
| `candidate_name` | To block + `rename_output.py` candidate-name fallback |
| `candidate_email` | To block |
| `candidate_phone` | To block |
| `candidate_address` | **Flat** single string (may contain commas / city / pincode) — NOT split |
| `role` | Position offered (the doc's old `candidate_title`) |
| `date` | Letter date (ISO or display) |
| `annual_ctc` | e.g. `₹9,00,000.00` |
| `basic_monthly` | e.g. `₹37,500.00` |
| `hra_monthly` | |
| `lta_monthly` | |
| `wfh_allowance_monthly` | |
| `flexi_pay_monthly` | |
| `total_earnings_monthly` | |
| `professional_tax_monthly` | |
| `tds_monthly` | |
| `total_deductions_monthly` | |
| `net_take_home_monthly` | |

**Optional (m6 `OPTIONAL_FIELDS` names) — conditional `{% if %}` sections:**

| Field | Notes |
|-------|-------|
| `internship_acknowledgement` | Non-empty → internship paragraph renders |
| `business_performance_bonus_pct` | Non-empty → business-bonus line (the conditional trigger; there is NO `has_performance_bonus` flag) |
| `business_performance_bonus_period` | e.g. `March/April` (Jinja `default('March/April')`) |
| `individual_performance_bonus_pct` | Non-empty → individual-bonus line |
| `individual_performance_bonus_period` | e.g. `September/October` (Jinja `default('September/October')`) |

**Dropped from the Phase-1 draft (no backing field):** `start_date`, `candidate_title`
(→ `role`), `candidate_address_1/_2/_city` (→ flat `candidate_address`), `has_performance_bonus`
(→ trigger on `business_performance_bonus_pct`).

---

## Ticket set

### t1 — `offer_letter_v1.html.j2` — proper HTML + inline CSS template

**Scope.** Replace the current bare-HTML `offer_letter_v1.html.j2` with a complete
HTML + inline CSS template matching the Bitloka FTE offer letter: A4 layout,
Calibri font stack, logo header, proper paragraph spacing, three compensation
tables with orange header rows, both conditional sections (internship
acknowledgement, performance bonuses), all hardcoded boilerplate (notice period,
T&C, documents required, NDA, signatory), and footer. The existing file is
overwritten; no other files change in this ticket.

**Contract refs.**
- `CLAUDE.md` § Learning — m6-docbuilder (generic renderer stays generic; inline CSS rationale)
- `docbuilder/runbook.md` §"Jinja2 templates (m6)" (template authoring rules)
- Design decisions D1–D5, D7 in this doc

**Touches.**
- `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.html.j2` (replace)

**Do not generate.**
- Do not touch `offer_letter_v1.json`, `catalogue.json`, any pipeline script,
  `validate_fields.py`, or any sprint/test file.
- Do not create a separate `.css` file — CSS is inline in the template per D1.
- Do not add any new context fields beyond those listed in the Context fields table
  above. The 18 required fields in `validate_fields.py` are frozen.

**Runbook update rule.** No new env vars, startup steps, or operational procedures.
No runbook change required.

**Done-check.**
```bash
# From aetheris-agents/
# Render the template standalone with a representative context dict and
# verify: (a) no {{ }} leaks in the HTML, (b) the three table sections
# are present, (c) the conditional sections toggle correctly.
python3 -c "
import jinja2, json, pathlib
bundle = pathlib.Path('docbuilder/data/templates/bitloka/offer_letter/v1')
env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(bundle)),
    autoescape=True, undefined=jinja2.Undefined)
ctx = {
    'title': 'Offer Letter — Ajay Rao',
    'candidate_name': 'Ajay Rao',
    'candidate_email': 'ajay.rao@example.com',
    'candidate_phone': '980 000 1234',
    'candidate_address': '12 MG Road, Indiranagar, Bangalore 560038',
    'role': 'Software Engineer',
    'date': '2026-06-30',
    'annual_ctc': '₹9,00,000.00',
    'basic_monthly': '₹37,500.00',
    'hra_monthly': '₹15,000.00',
    'lta_monthly': '₹3,000.00',
    'wfh_allowance_monthly': '₹2,500.00',
    'flexi_pay_monthly': '₹7,800.00',
    'total_earnings_monthly': '₹65,800.00',
    'professional_tax_monthly': '₹200.00',
    'tds_monthly': '₹8,300.00',
    'total_deductions_monthly': '₹8,500.00',
    'net_take_home_monthly': '₹67,300.00',
    'internship_acknowledgement': 'We acknowledge your internship from Jan–Mar 2026.',
    'business_performance_bonus_pct': '10',
    'business_performance_bonus_period': 'March/April',
    'individual_performance_bonus_pct': '5',
    'individual_performance_bonus_period': 'September/October',
}
html = env.get_template('offer_letter_v1.html.j2').render(**ctx)
assert '{{' not in html and '}}' not in html, 'Jinja leaks found'
assert 'Total Earnings' in html, 'earnings table missing'
assert 'Total Deductions' in html, 'deductions table missing'
assert 'Net Monthly Take Home' in html, 'net take-home table missing'
assert 'internship' in html.lower(), 'conditional internship section missing'
assert 'Business Performance Bonus' in html, 'conditional bonus section missing'
# Now test conditional suppression (drop the optional triggers)
ctx2 = dict(ctx, internship_acknowledgement='', business_performance_bonus_pct='')
html2 = env.get_template('offer_letter_v1.html.j2').render(**ctx2)
assert 'acknowledge' not in html2.lower(), 'internship section should be suppressed when empty'
assert 'Business Performance Bonus' not in html2, 'bonus section should be suppressed'
print('PASS — template renders cleanly, tables present, conditionals toggle')
"
```

**Claude-code prompt.**

> Read `CLAUDE.md` §Learning — m6-docbuilder and `docbuilder/runbook.md`
> §"Jinja2 templates (m6)" before writing any code.
>
> **Task:** replace `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.html.j2`
> with a complete HTML + inline CSS template that faithfully reproduces the Bitloka
> FTE offer letter. Reference structure is in `docbuilder/docs/milestones/m7-offer-letter.md`
> §"Reference letter structure".
>
> Design constraints (from §"Design decisions"):
> - D1: CSS is **inline** in the template — no separate `.css` file
> - D4: Table header rows use `background-color: #F5A623; color: #fff;`; body cell
>   borders `1px solid #ccc`
> - D5: All currency fields are Jinja variables (`{{ basic_monthly }}` etc.) already
>   pre-formatted as display strings — do not add formatting filters
> - D7: `css_file` is null; `base_url` is set by `generate_pdf.py` — no path handling
>   needed in the template
>
> Page CSS: `@page { size: A4; margin: 1.3cm; }`, `body { font-family: Calibri,
> 'Gill Sans', sans-serif; font-size: 10pt; }`. Logo: `<img src="btl_logo-withtext.png">`
> (resolves via `base_url` at render time).
>
> Three tables (earnings 7 rows, deductions 4 rows, net take-home 1 row). Both
> conditional sections via `{% if %}`. All hardcoded boilerplate as specified in the
> milestone doc. `rename_output.py` uses `candidate_name` from context — ensure that
> variable is in the template (it is, in the To block).
>
> **Touches:** only `offer_letter_v1.html.j2`. Do not touch any pipeline script,
> `offer_letter_v1.json`, `catalogue.json`, `validate_fields.py`, or sprint files.
>
> Run the done-check (verbatim command from §t1 Done-check) and include its full
> output in the review packet. Review packet must open with the done-check output.
> Write implementation notes to `docbuilder/docs/milestones/m7-offer-letter-t1-implementation-notes.md`
> and commit before submitting.

---

### t2 — Bundle spec + logo: add PDF to `output_formats`, copy logo

**Scope.** Two changes to the offer-letter bundle: (1) update `offer_letter_v1.json`
to add `"pdf"` as the first entry in `output_formats` (PDF primary, DOCX secondary);
(2) copy `btl_logo-withtext.png` from wherever it currently lives (invoice bundle or
a shared assets dir) into `data/templates/bitloka/offer_letter/v1/`. No pipeline
script changes. `catalogue.json` description updated to reflect PDF primary.

**Contract refs.**
- `docbuilder/runbook.md` §"Adding a new doc type" (bundle spec fields)
- `docbuilder/data/templates/bitloka/catalogue.json` (offer_letter entry)
- Design decisions D2, D6 in this doc

**Touches.**
- `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.json`
- `docbuilder/data/templates/bitloka/offer_letter/v1/btl_logo-withtext.png` (new — copy)
- `docbuilder/data/templates/bitloka/catalogue.json` (description update only)

**Do not generate.**
- Do not modify any pipeline script (`generate_pdf.py`, `generate_html.py`,
  `generate_docx_from_html.py`, `compute_doc.py`, orchestrator `.exs`).
- Do not add `css_file` handling — it stays null (D7).
- Do not create a new version of the offer-letter bundle (v2).

**Runbook update rule.** No new env vars or operational steps. No runbook change.

**Done-check.**
```bash
# From aetheris-agents/
python3 -c "
import json, pathlib
bundle = pathlib.Path('docbuilder/data/templates/bitloka/offer_letter/v1')
spec = json.loads((bundle / 'offer_letter_v1.json').read_text())
assert spec['output_formats'][0] == 'pdf', 'pdf must be first output_format'
assert 'docx' in spec['output_formats'], 'docx must still be present'
assert (bundle / 'btl_logo-withtext.png').exists(), 'logo not found in bundle'
cat = json.loads(pathlib.Path('docbuilder/data/templates/bitloka/catalogue.json').read_text())
ol = next(e for e in cat if e['doc_type'] == 'offer_letter')
v1 = next(v for v in ol['variants'] if v['version'] == 'v1')
assert 'pdf' in v1['output_formats'], 'catalogue variant must reflect pdf'
print('PASS — output_formats correct, logo present, catalogue in sync')
"
```

**Claude-code prompt.**

> Read `docbuilder/runbook.md` §"Adding a new doc type" for bundle spec field
> conventions.
>
> **Task (two parts):**
>
> 1. Edit `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.json`:
>    change `output_formats` from `["docx"]` to `["pdf", "docx"]` (PDF first = primary).
>    Leave all other fields unchanged (`has_jinja: true`, `css_file: null`, etc.).
>
> 2. Copy `btl_logo-withtext.png` into
>    `docbuilder/data/templates/bitloka/offer_letter/v1/btl_logo-withtext.png`.
>    Source: locate it in the invoice bundle
>    (`docbuilder/data/templates/bitloka/invoice/v1/`) or wherever it currently lives.
>    If it is absent from the repo entirely, record that in the implementation notes
>    and create a 1×1 transparent PNG placeholder so the done-check passes — the
>    real asset will be dropped in by hand.
>
> 3. Update `docbuilder/data/templates/bitloka/catalogue.json`: update the offer_letter
>    v1 variant's `output_formats` to `["pdf", "docx"]` and update the description to
>    note "PDF primary, DOCX secondary draft".
>
> **Touches:** `offer_letter_v1.json`, `btl_logo-withtext.png` (new), `catalogue.json`.
> Do not touch any pipeline script.
>
> Run the done-check and include its full output at the top of the review packet.
> Write implementation notes to
> `docbuilder/docs/milestones/m7-offer-letter-t2-implementation-notes.md` and commit.

---

### t3 — Sprint case update: assert `.pdf` + `.docx` outputs; zero `{{` in PDF

**Scope.** Update the `docbuilder_offer_letter` sprint case (in `scripts/sprint.sh` and
its companion assertion script) to: (a) assert both a `.pdf` and a `.docx` output are
present in `renamed.json`; (b) assert the PDF has zero unresolved `{{ }}` strings
(same `pdftotext` check as `docbuilder_fresh_render`); (c) update the sprint context
blob to supply all currency fields as display strings (e.g. `"₹37,500.00"` not
`37500`). Also add a one-line entry to `docbuilder/runbook.md` §"Jinja2 templates (m6)"
noting that the offer-letter sprint now exercises both outputs.

**Contract refs.**
- `CLAUDE.md` §Learning — m6-docbuilder (end-to-end check beyond unit done-check)
- `docbuilder/runbook.md` §"Jinja2 templates (m6)"
- Design decision D5 in this doc (currency as display strings)

**Touches.**
- `aetheris/scripts/sprint.sh` (the `docbuilder_offer_letter` case block)
- `aetheris/scripts/sprint_docbuilder_offer_letter.sh` (or inline assertions —
  whichever pattern the existing case uses; check before editing)
- `docbuilder/runbook.md` (one-line addition only)

**Do not generate.**
- Do not change any other sprint case.
- Do not change the sprint case name (`docbuilder_offer_letter`).
- Do not add a new sprint case — update the existing one.

**Runbook update rule.** Runbook addition is part of this ticket's Touches and
done-check (assert the runbook section mentions "pdf" after the edit).

**Done-check.**
```bash
# From aetheris/ (the harness repo)
cd ~/sandbox/elixirws/aetheris

# 1. Run the offer-letter sprint case
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Offer letter for Ajay Rao, Software Engineer, address 12 MG Road Indiranagar Bangalore 560038, start date 15 July 2026, annual CTC ₹9,00,000.00, basic salary ₹37,500.00, HRA ₹15,000.00, LTA ₹3,000.00, WFH allowance ₹2,500.00, flexi pay ₹7,800.00, total earnings ₹65,800.00, professional tax ₹200.00, TDS ₹8,300.00, total deductions ₹8,500.00, net take home ₹67,300.00" \
./scripts/sprint.sh docbuilder_offer_letter

# 2. Verify the sprint case itself asserts pdf + docx (grep the case block)
grep -A 30 'docbuilder_offer_letter' scripts/sprint.sh | grep -E '\.pdf|\.docx|pdftotext'
```

**Claude-code prompt.**

> Read `CLAUDE.md` §Learning — m6-docbuilder before editing.
>
> **Task:** update the `docbuilder_offer_letter` sprint case so it:
>
> 1. Passes a `DOCBUILDER_REQUEST` (or `DOCBUILDER_CONTEXT` inline JSON) that
>    supplies all currency fields as **display strings** (e.g. `"₹37,500.00"`, not
>    `37500`). Include the conditional fields for a run that exercises
>    `internship_acknowledgement` (non-empty) and `business_performance_bonus_pct` set.
>    Use the sample values from §t1 Done-check.
>
> 2. Asserts **both** `ajay_rao_offer_letter_*.pdf` and `ajay_rao_offer_letter_*.docx`
>    (or equivalent candidate-name slug) appear in `renamed.json`.
>
> 3. Asserts zero `{{` in the PDF using `pdftotext` (degrade to `[INFO]` if
>    `pdftotext` absent — same pattern as `docbuilder_fresh_render`).
>
> 4. Add one sentence to `docbuilder/runbook.md` §"Jinja2 templates (m6)" noting
>    the `docbuilder_offer_letter` sprint now asserts both `.pdf` and `.docx`.
>
> **Touches:** `aetheris/scripts/sprint.sh` (offer_letter case block),
> any companion assertion script if one exists, `docbuilder/runbook.md`.
>
> Check the existing sprint.sh file before writing to confirm the exact pattern
> (inline assertions vs helper script). Do not change other sprint cases.
>
> Run the done-check and include its **full output** (sprint run + grep) at the
> top of the review packet. Write implementation notes to
> `docbuilder/docs/milestones/m7-offer-letter-t3-implementation-notes.md` and commit.

---

### t4 — Docs sync + milestone close

**Scope.** Close the m7 milestone: (1) verify drift check is 8 PASS / 0 FAIL / 0 WARN;
(2) write the m7 milestone summary at the bottom of this document; (3) update
`docs/project-knowledge-manifest.md` with any changed files that are in project
knowledge (the manifest tracks commit hashes — update any row whose file changed
in m7); (4) scan all three review files (m7-t1, m7-t2, m7-t3) for findings
recurring on ≥2 tickets and propose any `CLAUDE.md` learning promotions to the
human. If no findings recur, record "No recurring findings" per the m5 pattern.

**Contract refs.**
- `milestone-methodology.md` §7 (milestone-end ritual)
- `docs/project-knowledge-manifest.md` (manifest format)
- `CLAUDE.md` §Learning — m6-docbuilder (format for new learning entries)

**Touches.**
- `docbuilder/docs/milestones/m7-offer-letter.md` (milestone summary appended)
- `docs/project-knowledge-manifest.md` (commit hash updates if any project-knowledge
  files changed — check `offer_letter_v1.html.j2` is not in the manifest; check if
  `runbook.md` row needs a hash bump)
- `CLAUDE.md` §Learning (new entry only if recurring findings; format per §7)
- `docbuilder/docs/milestones/m7-offer-letter-t4-implementation-notes.md` (new)

**Do not generate.**
- Do not update GitHub issues (that's the human's task post-merge).
- Do not change any template, pipeline script, or sprint case.

**Runbook update rule.** No new env vars or operational steps. Runbook edit in t3
is already landed; t4 does not re-touch it.

**Done-check.**
```bash
# From aetheris-agents/
python3 scripts/drift_check.py
# Expected: 8 PASS / 0 FAIL / 0 WARN

# Confirm milestone summary exists in the doc
grep -c '## Milestone summary' docbuilder/docs/milestones/m7-offer-letter.md
# Expected: 1

# Confirm manifest was updated (no stale hashes for changed files)
python3 -c "
import pathlib, subprocess, re
manifest = pathlib.Path('docs/project-knowledge-manifest.md').read_text()
# Basic parse: check the runbook row's commit hash matches HEAD for that file
result = subprocess.run(
    ['git', 'log', '-1', '--format=%h', '--', 'docbuilder/docs/runbook.md'],
    capture_output=True, text=True)
head_hash = result.stdout.strip()
if head_hash and head_hash in manifest:
    print(f'PASS — runbook manifest hash {head_hash} matches HEAD')
elif not head_hash:
    print('INFO — runbook not in git (local only); skip manifest check')
else:
    print(f'WARN — runbook manifest may be stale (HEAD={head_hash}); verify manually')
"
```

**Claude-code prompt.**

> Read `milestone-methodology.md` §7 and `docs/project-knowledge-manifest.md` before
> starting.
>
> **Task (milestone-end ritual):**
>
> 1. Run `python3 scripts/drift_check.py`. Report the result. If it is not
>    8 PASS / 0 FAIL / 0 WARN, stop and report what failed — do not proceed.
>
> 2. Read all three review files for m7 (`docs/reviews/m7-offer-letter-t1-review.md`,
>    `-t2-review.md`, `-t3-review.md`). List every finding that appears on ≥2 tickets.
>    For each recurring finding, draft a `CLAUDE.md` learning entry in the §7 format.
>    If none recur, note "No recurring findings in m7".
>
> 3. Append a `## Milestone summary` section to
>    `docbuilder/docs/milestones/m7-offer-letter.md`. Follow the format from prior
>    milestone summaries (what shipped, what was deferred with → ref, surprises,
>    open items for m8). Source is the three implementation notes files, not the diffs.
>
> 4. Update `docs/project-knowledge-manifest.md`: for every file in the manifest
>    whose content changed in m7, update the commit hash to HEAD. Run
>    `git log -1 --format=%h -- <path>` to get the hash. The offer-letter template
>    is NOT in the manifest (it is not a project-knowledge export file). Check
>    `docbuilder/docs/runbook.md` — if t3 touched it, bump its row.
>
> Run the done-check and include its full output at the top of the review packet.
> Write implementation notes to
> `docbuilder/docs/milestones/m7-offer-letter-t4-implementation-notes.md` and commit.

---

## Open questions at doc approval

| # | Question | Default if not resolved before t1 |
|---|----------|-----------------------------------|
| Q1 | **Table header colour** — orange (`#F5A623`) or grey? | Orange per D4. Change D4 before approving if grey preferred. |
| Q2 | Does `btl_logo-withtext.png` exist in the invoice bundle or another committed path? | t2 will locate it; if absent, creates a placeholder and notes it. |

---

## Ticket order

t1 → t2 → t3 → t4. All four are independent of pipeline changes; t1 and t2 can
run in parallel sessions if desired (they touch disjoint files). t3 depends on t1
and t2 (needs the rendered output to exist). t4 depends on all three review files.

---

## File locations

```
docbuilder/docs/milestones/m7-offer-letter.md          ← this doc
docbuilder/docs/milestones/m7-offer-letter-t1-implementation-notes.md
docbuilder/docs/milestones/m7-offer-letter-t2-implementation-notes.md
docbuilder/docs/milestones/m7-offer-letter-t3-implementation-notes.md
docbuilder/docs/milestones/m7-offer-letter-t4-implementation-notes.md
docs/reviews/m7-offer-letter-t1-review.md
docs/reviews/m7-offer-letter-t2-review.md
docs/reviews/m7-offer-letter-t3-review.md
```

---

_Approved & committed (2026-06-27). Q1 resolved to the **orange header / grey body**
default (D4) — operator approved the doc without overriding; flag at t1 if grey is
preferred instead. Q2 resolved at t2 (locate the logo; placeholder + note if absent)._
