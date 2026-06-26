# Milestone — m6-docbuilder — Offer Letter bundle

**Repo:** aetheris-agents
**Branch:** m6-docbuilder
**Depends on:** aetheris-agents `6dce721` (m5 closed, drift clean 8 PASS / 0 FAIL / 0 WARN)

> **Doc path:** `docbuilder/docs/m6-milestone.md` (aligned to the m1–m5 convention — all
> milestone scope docs live at `docbuilder/docs/m{N}-milestone.md`; `milestones/` holds
> per-ticket implementation notes, `reviews/` holds reviews).

---

## Goal

Add an `offer_letter/v1` bundle for the Bitloka tenant so the docbuilder pipeline
can produce a branded Word document offer letter from a natural-language request.
The output is a `.docx` file ready to upload to Drive and tweak before sending.
This is also the first end-to-end proof that the runbook's "Adding a new doc type"
guide (`docbuilder/runbook.md`) is correct.

---

## What is NOT in scope

- PDF output (docx only — Drive + manual edit handles distribution)
- XLSX output
- Salary arithmetic / `compute_doc.py` extension (operator provides all amounts)
- Multi-variant support (v1 only)
- Changes to the orchestrator, context builder, or any existing script beyond
  `validate_fields.py` and `OPTIONAL_FIELDS` in `render_template.py`
- Drive upload wiring (PHASE E) — the runbook covers this; not a new milestone item

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Output format | `docx` only | Offer letter is reviewed/signed in Word; Drive handles distribution |
| Compensation table | Individual `{{field}}` placeholders in the base `.docx`, not a sheet partial | Simpler; "good enough + Drive tweak" model; no `compute_doc.py` change needed |
| Internship acknowledgement | Optional field `{{internship_acknowledgement}}` — full paragraph text when applicable, empty string for direct hires | Avoids needing conditional template logic; absent → renders as empty (m5 `OPTIONAL_FIELDS` mechanism) |
| Performance bonuses | Optional fields `{{business_performance_bonus_pct}}` and `{{individual_performance_bonus_pct}}` | Vary per hire; absent → renders as empty |
| Notice period | Hardcoded in the base `.docx` template ("eight (8) weeks") | Fixed for all hires |
| Field naming | Offer-letter-specific aliases (`candidate_name`, `candidate_email`, etc.) rather than reusing `client_name` | Clearer semantics; option (b) from the pre-milestone discussion |
| `validate_fields.py` | Add `OFFER_LETTER_REQUIRED` branch | Same pattern as `INVOICE_REQUIRED`; keeps validation doc-type-aware |
| `render_template.py` | Add offer-letter optional fields to `OPTIONAL_FIELDS` | Ensures absent optional fields render as empty, not `{{placeholders}}` |

---

## Field list

### Required for `offer_letter`

| Field | Description | Example |
|---|---|---|
| `title` | Document title | `"Offer Letter — Ajay Rao"` |
| `candidate_name` | Full name | `"Ajay Rao"` |
| `candidate_email` | Email address | `"ajay.rao@example.com"` |
| `candidate_phone` | Phone number | `"980 000 1234"` |
| `candidate_address` | Full postal address | `"123, Main Street, Bengaluru, Karnataka - 560012"` |
| `role` | Position offered | `"Software Engineer"` |
| `date` | Letter date (ISO or DD-Mon-YYYY) | `"01-Jul-2026"` |
| `annual_ctc` | Annual Cost to Company | `"₹9,00,000"` |
| `basic_monthly` | Basic salary per month | `"37,500.00"` |
| `hra_monthly` | HRA per month | `"18,750.00"` |
| `lta_monthly` | LTA per month | `"3,000.00"` |
| `wfh_allowance_monthly` | WFH allowance per month | `"3,000.00"` |
| `flexi_pay_monthly` | Flexi pay per month | `"12,750.00"` |
| `total_earnings_monthly` | Sum of earnings | `"75,000.00"` |
| `professional_tax_monthly` | PT deduction | `"200.00"` |
| `tds_monthly` | TDS deduction | `"7,500.00"` |
| `total_deductions_monthly` | Sum of deductions | `"7,700.00"` |
| `net_take_home_monthly` | Net take-home | `"₹67,300.00"` |

### Optional for `offer_letter`

| Field | Description |
|---|---|
| `internship_acknowledgement` | Full paragraph text acknowledging prior internship; empty for direct hires |
| `business_performance_bonus_pct` | e.g. `"12.5%"` |
| `individual_performance_bonus_pct` | e.g. `"12.5%"` |
| `business_performance_bonus_period` | e.g. `"March/April"` |
| `individual_performance_bonus_period` | e.g. `"September/October"` |

---

## Bundle structure

```
data/templates/bitloka/offer_letter/v1/
  offer_letter_v1.docx        ← base file with {{placeholders}} and table structure
  offer_letter_v1.json        ← bundle spec (required by orchestrator at eval time)
```

No `.md.template`, no `.css`, no data source — docx only, context-driven.

### `offer_letter_v1.json` (bundle spec)

```json
{
  "title": "{{title}}",
  "sheets": [],
  "narrative": null,
  "sources": [],
  "output_formats": ["docx"],
  "base_file": {
    "docx": "offer_letter_v1.docx"
  }
}
```

> **t1 verification note (raised at scope time):** confirm the exact spec key names against
> the live invoice bundle `invoice_v1.json` and the orchestrator before writing. Known
> discrepancies to resolve at t1: the invoice spec uses `data_sources` (not `sources`); the
> orchestrator detects the DOCX base by **file existence** (`File.exists?(prefix.docx)`), so
> a `base_file` key may be ignored; `narrative: null` is intentional (non-map → structured /
> base-file docx path, not the `render_template.py` narrative path). Adjust the spec to match
> reality at t1 rather than trusting this illustrative shape verbatim.

### `catalogue.json` addition

```json
{
  "doc_type": "offer_letter",
  "description": "Employment offer letter for new hires — branded Word document with compensation structure",
  "variants": [
    {
      "version": "v1",
      "label": "Standard FTE",
      "output_formats": ["docx"],
      "has_base_files": {
        "xlsx": false,
        "docx": true
      },
      "has_narrative": false
    }
  ]
}
```

---

## Ticket structure

| Ticket | Title | Key artifacts |
|---|---|---|
| t1 | Bundle assets — `offer_letter_v1.docx` + `offer_letter_v1.json` + catalogue entry | `data/templates/bitloka/offer_letter/v1/` |
| t2 | `validate_fields.py` — `OFFER_LETTER_REQUIRED` branch + `render_template.py` `OPTIONAL_FIELDS` | `scripts/validate_fields.py`, `scripts/render_template.py` |
| t3 | `context-schema.md` + end-to-end sprint (`docbuilder_offer_letter`) + runbook | `docbuilder/docs/context-schema.md`, `aetheris/scripts/sprint.sh`, `docbuilder/runbook.md` |
| t4 | Docs sync + milestone close | `docs/capability-matrix.md`, `CLAUDE.md`, milestone summary |

---

## Tickets

### t1 — Bundle assets

**Scope.** Create the offer letter bundle: the `.docx` base file with `{{placeholder}}`
fields and table structure matching the Bitloka FTE offer letter template, the
`offer_letter_v1.json` bundle spec, and the catalogue entry. No Python script changes
in this ticket.

**The `.docx` base file** must contain:
- Bitloka letterhead (copy style from the actual template)
- All `{{placeholder}}` fields in the narrative (candidate details, role, date, CTC,
  `{{internship_acknowledgement}}`, notice period hardcoded)
- Compensation table with `{{basic_monthly}}`, `{{hra_monthly}}`, `{{lta_monthly}}`,
  `{{wfh_allowance_monthly}}`, `{{flexi_pay_monthly}}`, `{{total_earnings_monthly}}`
- Deductions table with `{{professional_tax_monthly}}`, `{{tds_monthly}}`,
  `{{total_deductions_monthly}}`
- Net take-home row: `{{net_take_home_monthly}}`
- Performance bonus section with `{{business_performance_bonus_pct}}`,
  `{{business_performance_bonus_period}}`, `{{individual_performance_bonus_pct}}`,
  `{{individual_performance_bonus_period}}`
- Signature block (hardcoded: Vishal Honnatti, Director)
- Footer (hardcoded: address, www.bitloka.com, contact@bitloka.com)

**Contract refs.**
- `docbuilder/runbook.md` §"Adding a new doc type" — the two-layer structure
  (catalogue = selection metadata; bundle spec = operative config)
- `generate_docx.py` — does find-and-replace of `{{field}}` → value throughout the
  document; the base file must use exactly the `{{field}}` syntax

**Touches.**
- `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.docx` — new
- `docbuilder/data/templates/bitloka/offer_letter/v1/offer_letter_v1.json` — new
- `docbuilder/data/templates/bitloka/catalogue.json` — add `offer_letter` entry
- `docbuilder/docs/milestones/m-docbuilder-m6-t1-implementation-notes.md` — new

**Do not generate.**
- Do not modify any `.py` or `.exs` file
- Do not add a sprint case — that is t3

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

# Verify bundle files exist
ls data/templates/bitloka/offer_letter/v1/

# Verify catalogue entry
python3 -c "
import json
cat = json.load(open('data/templates/bitloka/catalogue.json'))
types = [d['doc_type'] for d in cat['doc_types']]
print('doc_types:', types)
assert 'offer_letter' in types, 'offer_letter missing from catalogue'
print('OK')
"

# Verify bundle spec is valid JSON
python3 -c "import json; json.load(open('data/templates/bitloka/offer_letter/v1/offer_letter_v1.json')); print('bundle spec: valid JSON')"

# Smoke: run generate_docx.py against the base file with a minimal context
python3 scripts/generate_docx.py \
  --output-dir output \
  --filename test_offer_letter \
  --base-file data/templates/bitloka/offer_letter/v1/offer_letter_v1.docx \
  --context '{"candidate_name":"Test Candidate","role":"Engineer","date":"2026-07-01","annual_ctc":"₹9,00,000","basic_monthly":"37,500.00","hra_monthly":"18,750.00","lta_monthly":"3,000.00","wfh_allowance_monthly":"3,000.00","flexi_pay_monthly":"12,750.00","total_earnings_monthly":"75,000.00","professional_tax_monthly":"200.00","tds_monthly":"7,500.00","total_deductions_monthly":"7,700.00","net_take_home_monthly":"₹67,300.00"}'
ls -lh output/test_offer_letter.docx
# Expected: file exists, non-zero size
```

> **t1 verification note:** the smoke command's `generate_docx.py` flags above
> (`--output-dir` / `--filename` / `--base-file` / `--context`) are illustrative — confirm
> the script's real CLI signature before relying on them, and adjust the done-check to match.

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) and `docbuilder/runbook.md` §"Adding a new
> doc type" before writing any files. Then implement t1 of
> `docbuilder/docs/m6-milestone.md`.
>
> **Scope:** create the offer_letter/v1 bundle assets.
>
> **`offer_letter_v1.docx`:** Build a Word document that faithfully reproduces the
> Bitloka FTE offer letter structure (see the field list in the milestone doc).
> Use `{{placeholder}}` syntax throughout — `generate_docx.py` does a find-and-replace
> of `{{field}}` → value. The document must contain:
> - Bitloka Solutions Private Limited header
> - Date: `{{date}}`
> - Candidate address block: `{{candidate_name}}`, `{{candidate_address}}`,
>   `{{candidate_email}}` | `{{candidate_phone}}`
> - Salutation: `Dear Mr./Ms. {{candidate_name}},`
> - Offer paragraph mentioning `{{role}}`
> - `{{internship_acknowledgement}}` paragraph (leave as a placeholder — empty for
>   direct hires, full paragraph text for interns)
> - CTC line: `{{annual_ctc}}`
> - Notice period: hardcoded "eight (8) weeks"
> - Terms, documents-required, and NDA paragraphs: hardcoded boilerplate
> - Acceptance paragraph: hardcoded
> - Signature block: hardcoded (Vishal Honnatti, Director)
> - Compensation section heading
> - Monthly salary breakup table with all `{{earnings_field}}` placeholders
> - Monthly deductions table with all `{{deductions_field}}` placeholders
> - Net take-home row: `{{net_take_home_monthly}}`
> - Performance bonus section with all `{{bonus_field}}` placeholders
> - Footer: hardcoded (address, www.bitloka.com, contact@bitloka.com)
>
> Use `python-docx` to construct the document programmatically. Match the Bitloka
> invoice style (professional, clean). Commit the generated `.docx` file as a binary.
>
> **`offer_letter_v1.json`:** Use the bundle spec from the milestone doc §"Bundle
> structure". Confirm the exact fields the orchestrator expects by checking
> `fetch_template.py` AND the live `invoice_v1.json` before writing — resolve the
> known discrepancies flagged in the §"Bundle structure" verification note
> (`data_sources` vs `sources`; `base_file` likely ignored; `narrative: null` intended).
>
> **`catalogue.json`:** Append the `offer_letter` entry from the milestone doc
> §"Design decisions" to the `doc_types` array. Do not modify the existing `invoice`
> entry.
>
> **Touches:** `data/templates/bitloka/offer_letter/v1/offer_letter_v1.docx`,
> `data/templates/bitloka/offer_letter/v1/offer_letter_v1.json`,
> `data/templates/bitloka/catalogue.json`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t1-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t1` and include its full output at the
> top of the review packet, before the diff.

---

### t2 — `validate_fields.py` + `render_template.py` updates

**Scope.** Add `OFFER_LETTER_REQUIRED` to `validate_fields.py` so the fresh extraction
path enforces the correct required fields for offer letters. Add offer-letter optional
fields to `OPTIONAL_FIELDS` in `render_template.py` (though `render_template.py` is not
used for docx, this keeps the two constants in sync for future PDF support).

**Contract refs.**
- `validate_fields.py` — existing `INVOICE_REQUIRED` pattern; same approach
- `render_template.py` — existing `OPTIONAL_FIELDS` set; add new optional fields

**Touches.**
- `docbuilder/scripts/validate_fields.py` — add `OFFER_LETTER_REQUIRED`, extend
  required-fields branch
- `docbuilder/scripts/render_template.py` — add offer-letter optional fields to
  `OPTIONAL_FIELDS`
- `docbuilder/tests/test_validate_fields.py` — add tests for offer_letter doc_type
- `docbuilder/docs/milestones/m-docbuilder-m6-t2-implementation-notes.md` — new

**Do not generate.**
- Do not modify any bundle asset, catalogue, or agent file
- Do not add a sprint case — that is t3

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

python3 -m pytest tests/test_validate_fields.py -v
# Expected: all existing tests pass + new offer_letter tests pass

python3 -m pytest tests/ -q
# Expected: full suite passes
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing any code. Then implement t2
> of `docbuilder/docs/m6-milestone.md`.
>
> **`validate_fields.py`:**
> Add at module level:
> ```python
> OFFER_LETTER_REQUIRED = [
>     "candidate_name", "candidate_email", "candidate_phone", "candidate_address",
>     "role", "date", "annual_ctc",
>     "basic_monthly", "hra_monthly", "lta_monthly", "wfh_allowance_monthly",
>     "flexi_pay_monthly", "total_earnings_monthly",
>     "professional_tax_monthly", "tds_monthly", "total_deductions_monthly",
>     "net_take_home_monthly",
> ]
> ```
> Update the required-fields selection in `validate()`:
> ```python
> required = BASE_REQUIRED + (
>     INVOICE_REQUIRED if doc_type == "invoice" else
>     OFFER_LETTER_REQUIRED if doc_type == "offer_letter" else
>     []
> )
> ```
> Note: `BASE_REQUIRED` (`title`, `client_name`, `client_email`, `date`) is
> NOT used for offer_letter — `OFFER_LETTER_REQUIRED` is the complete list
> (it has its own name/email/date fields with offer-letter semantics). The
> `BASE_REQUIRED` check only applies when `doc_type` is neither `invoice` nor
> `offer_letter`. (i.e. the `required = BASE_REQUIRED + (...)` shape must NOT
> add `BASE_REQUIRED` for offer_letter — make `required` be exactly
> `OFFER_LETTER_REQUIRED` for that branch; restructure the expression if needed
> so `client_name`/`client_email` are never required for an offer letter.)
>
> Also add `candidate_email` to the email format check (currently only
> `client_email` is checked) — check whichever of `client_email` /
> `candidate_email` is present.
>
> **`render_template.py`:** Add to `OPTIONAL_FIELDS`:
> ```python
> "internship_acknowledgement",
> "business_performance_bonus_pct",
> "business_performance_bonus_period",
> "individual_performance_bonus_pct",
> "individual_performance_bonus_period",
> "candidate_name", "candidate_email", "candidate_phone", "candidate_address",
> "role", "annual_ctc",
> "basic_monthly", "hra_monthly", "lta_monthly", "wfh_allowance_monthly",
> "flexi_pay_monthly", "total_earnings_monthly",
> "professional_tax_monthly", "tds_monthly", "total_deductions_monthly",
> "net_take_home_monthly",
> ```
> These are offer-letter fields; marking them optional in `render_template.py`
> keeps the two scripts in sync for future PDF support.
>
> **Tests:** add to `test_validate_fields.py`:
> - Valid offer_letter with all required fields → exit 0
> - offer_letter missing `candidate_name` → exit 1, in `missing`
> - offer_letter missing `net_take_home_monthly` → exit 1, in `missing`
> - offer_letter with invalid `candidate_email` → exit 1, in `invalid`
> - offer_letter with optional `internship_acknowledgement` absent → exit 0
>   (optional field, must not be required)
> - offer_letter does NOT require `client_name` / `client_email` (regression guard
>   for the BASE_REQUIRED exclusion)
>
> **Touches:** `docbuilder/scripts/validate_fields.py`,
> `docbuilder/scripts/render_template.py`,
> `docbuilder/tests/test_validate_fields.py`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t2-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t2` and include its full output at the
> top of the review packet, before the diff.

---

### t3 — `context-schema.md` + `docbuilder_offer_letter` sprint + runbook

**Scope.** Document the offer-letter fields in `context-schema.md`. Add a
`docbuilder_offer_letter` sprint case that runs the full fresh path end-to-end for an
offer letter: freeform NL request → extraction → validation → confirmed_context.json →
orchestrator renders → `ajay_rao_offer_letter_{date}.docx`. Add the sprint-case entry
to `docbuilder/runbook.md`. This is the end-to-end proof that the runbook's "Adding a
new doc type" guide works correctly.

**Contract refs.**
- `docbuilder/runbook.md` §"Adding a new doc type" — the guide this ticket proves
- m4/m5 sprint case patterns (`docbuilder_fresh_render`) — same structure

**Touches.**
- `docbuilder/docs/context-schema.md` — add offer-letter fields (required + optional)
- `aetheris/scripts/sprint.sh` — new `docbuilder_offer_letter` case (also under `all`)
- `docbuilder/runbook.md` — sprint-case entry
- `docbuilder/docs/milestones/m-docbuilder-m6-t3-implementation-notes.md` — new

**Do not generate.**
- Do not modify any `.py` or `.exs` file
- Do not update `docs/rig/runbook.md` — that is t4

**Runbook update rule.** Add the sprint-case entry to `docbuilder/runbook.md` in
this ticket (not deferred to t4) — same rule as m5 t3.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=bitloka \
./scripts/sprint.sh docbuilder_offer_letter
# Expected:
#   context_builder.exs evaluates [OK]
#   confirmed_context.json written (candidate: Ajay Rao) [OK]
#   rendered: ajay_rao_offer_letter_{date}.docx [OK]  (via renamed.json)
#   run log appended (PHASE D2 fired: 0 → 1 entry) [OK]
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing. Then implement t3 of
> `docbuilder/docs/m6-milestone.md`.
>
> **`context-schema.md`:** add the offer-letter required and optional fields from
> the milestone doc §"Field list". Mark them as offer_letter-specific.
>
> **`sprint.sh` — `docbuilder_offer_letter` case:**
> Follow the `docbuilder_fresh_render` pattern (m5 t3). Key differences:
> - Default `DOCBUILDER_REQUEST`:
>   `"Offer letter for Ajay Rao at ajay.rao@example.com, phone 980 000 1234,
>   address 123 Main Street Bengaluru Karnataka 560012, role Software Engineer,
>   date 1 Jul 2026, annual CTC ₹9,00,000, basic monthly 37500, HRA 18750,
>   LTA 3000, WFH allowance 3000, flexi pay 12750, total earnings 75000,
>   professional tax 200, TDS 7500, total deductions 7700, net take-home
>   ₹67300, business performance bonus 12.5% in March/April, individual
>   performance bonus 12.5% in September/October"`
> - Verify `confirmed_context.json` written + parseable + `candidate_name`
>   non-empty (not `client_name` — offer letters use `candidate_name`)
> - Verify `renamed.json` output file exists (docx only)
> - Verify run log goes 0 → 1 (PHASE D2)
> - No PDF placeholder check (docx output, not PDF)
> - Under `all` + usage line updated
>
> Add sprint-case entry to `docbuilder/runbook.md` (same section as
> `docbuilder_fresh_render`).
>
> **Touches:** `docbuilder/docs/context-schema.md`, `aetheris/scripts/sprint.sh`,
> `docbuilder/runbook.md`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t3-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t3` and include its full output at
> the top of the review packet, before the diff.

---

### t4 — Docs sync + milestone close

**Scope.** Bring all reference docs in sync with t1–t3. Update the capability matrix
(no new scripts/agents — counts unchanged, but `validate_fields.py` description updated).
Run drift check. Write the milestone summary and CLAUDE.md learning scan.

**Touches.**
- `docs/capability-matrix.md` — update `validate_fields.py` description: append
  `offer_letter doc_type branch added (m6).`
- `docs/rig/runbook.md` — add one-line pointer to `docbuilder/runbook.md`
  §"Adding a new doc type" (the deferred BL-002 item from the pre-m6 runbook work)
- `docbuilder/docs/m6-milestone.md` — milestone summary appended
- `aetheris-agents/CLAUDE.md` — `## Learning — m6-docbuilder` (recurring findings
  scan; "No recurring findings" if none)
- `docbuilder/docs/milestones/m-docbuilder-m6-t4-implementation-notes.md` — new

**Do not generate.**
- Do not modify any script, agent, or test file

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents

python3 scripts/drift_check.py
# Expected: 0 FAIL (project_knowledge WARNs = BL-002, human-owned)

grep -n "offer_letter" docs/capability-matrix.md
grep -n "Adding a new doc type" docs/rig/runbook.md
grep -c "^## Milestone summary" docbuilder/docs/m6-milestone.md
```

**Claude-code prompt.**
> Read `CLAUDE.md` and `milestone-methodology.md` §7 before writing. Then implement
> t4 of `docbuilder/docs/m6-milestone.md`. Docs-only.
>
> 1. `docs/capability-matrix.md` — update `validate_fields.py` description row:
>    append `offer_letter doc_type branch added (m6).` Counts unchanged.
>
> 2. `docs/rig/runbook.md` — in the Docbuilder section (after the m4 fresh path
>    entry), add: `For template and doc-type authoring (including adding new doc
>    types like offer_letter), see \`docbuilder/runbook.md\` §"Adding a new doc type".`
>    (This clears the deferred pre-m6 BL-002 pointer item — fold the re-upload in
>    with the t4 close.)
>
> 3. Scan `docbuilder/docs/reviews/m-docbuilder-m6-t{1,2,3}-review.md` for
>    findings recurring on ≥2 tickets. Write `## Learning — m6-docbuilder` in
>    `aetheris-agents/CLAUDE.md` per methodology §7. If none recurred, write the
>    header with "No recurring findings in this milestone."
>
> 4. Append milestone summary to `docbuilder/docs/m6-milestone.md`.
>
> 5. Run `drift_check.py` and include the full output in the review packet.
>
> **Touches:** `docs/capability-matrix.md`, `docs/rig/runbook.md`,
> `docbuilder/docs/m6-milestone.md`, `aetheris-agents/CLAUDE.md`,
> `docbuilder/docs/milestones/m-docbuilder-m6-t4-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m6-milestone.md §t4` and include its full output at
> the top of the review packet, before the diff.

---

## Open questions for m7

- The offer letter is currently context-only (no data source). If salary computation
  is needed (derive breakdown from a single `annual_ctc` input), a `compute_offer.py`
  script following the `compute_doc.py` pattern would handle it.
- The `internship_acknowledgement` field is a full paragraph of text supplied by the
  operator. A future improvement: a boolean `is_intern` field that triggers the standard
  Bitloka internship paragraph automatically (stored in the template or as a constant).
- Drive upload (PHASE E) is already wired in the orchestrator — it just needs
  `DRIVE_DOCBUILDER_ID` set. No milestone work needed; document the env var in the
  runbook if not already there.

---

## Milestone summary

_To be written by claude-code at t4, from the implementation notes._
