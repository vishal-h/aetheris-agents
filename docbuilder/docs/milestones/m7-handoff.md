# Docbuilder m7 — Handoff & Conversation Starter

## State at session close (2026-06-27)

**Repos:** aetheris-agents @ `eeb37a1` · aetheris @ `78fe332`
**Drift:** 8 PASS / 0 FAIL / 0 WARN (15 project_knowledge entries match HEAD)
**m6:** FULLY CLOSED — manifest advanced, BL-002 done

---

## What closed this session (m6 summary)

**m6 — Jinja2 renderer + offer letter (t1–t6 + t4b, all merged):**
- `generate_html.py` — Jinja2 `.html.j2` renderer (t1)
- `generate_docx_from_html.py` — Pandoc HTML→DOCX wrapper + `reference.docx` (t2)
- Invoice migrated to `invoice_v1.html.j2` (`has_jinja: true`); `generate_pdf.py` Jinja branch (t3)
- Offer letter bundle: `offer_letter_v1.html.j2` (minimal, no CSS) + `offer_letter_v1.json` + catalogue entry; `OFFER_LETTER_REQUIRED` in `validate_fields.py` (t4 core)
- DOCX pipeline wiring: `compute_doc` zero-source, `rename_output` `candidate_name` fallback, orchestrator `docx + narrative? + has_jinja? + no_sheets?` branch (t4b)
- Sprint cases `docbuilder_invoice_jinja` + `docbuilder_offer_letter`; runbook §"Jinja2 templates (m6)" (t5)
- Docs sync; `## Learning — m6-docbuilder` (two promotions); capability matrix 2/24, 25/62 (t6)

**Two m6 CLAUDE.md learnings (already in standing instructions):**
1. For pipeline-integration tickets, run an end-to-end check beyond the unit done-check — cross-stage wiring defects pass the unit check and only surface at the final artifact.
2. A generic renderer stays generic; pipeline-specific enrichment lives in the caller. Route table-bearing docs away from the table-less path rather than duplicating injection logic.

---

## Why m7 — the offer letter output is wrong

The current `offer_letter_v1.html.j2` has no CSS and no logo. The generated DOCX (via Pandoc) is far from the reference Bitloka FTE offer letter. Two root problems:

1. **No CSS** — the template is bare HTML; Pandoc maps `<h1>`/`<h2>` to Word heading styles that don't match the reference (which uses all-normal style with inline bold). Layout, fonts, and spacing are off.
2. **Currency values stripped** — the context builder extracted `₹37,500.00` as the integer `37500` because the sprint request used bare numbers. Display strings must be supplied as strings in the context (same design decision as `amount_due` for invoices — validated as money, kept as display string).

**Decision made in the closing discussion:**
- Use **HTML + inline CSS** (same model as the StringTemplate templates already in use at Bitloka — familiar pattern, full layout control)
- **WeasyPrint PDF as primary output** (`@page { size: A4; margin: 1.3cm; }` gives precise layout)
- **Pandoc DOCX as secondary** (acceptable fidelity for "draft to edit in Word before sending")
- **Logo**: copy `btl_logo-withtext.png` into the offer letter bundle dir (`data/templates/bitloka/offer_letter/v1/`) for now — shared tenant assets dir is a future consideration
- **`generate_offer_letter.py`** (python-docx direct, built during the closing discussion) — discard; the HTML+CSS path is the right foundation for future complex doc types

---

## Reference letter structure (from inspecting the actual DOCX)

Source: `BTL-Offer_Letter-_Template_-_FTE_-_Ajay_Rao.docx`

**Page setup:** A4 (8.27" × 11.69"), 1.3cm margins all round

**Body text:** Calibri 10pt, `normal` style throughout — section headings are bold inline runs, NOT heading styles

**Paragraph spacing:**
- Date: space_after=12pt
- To block: space_after=2pt per line
- Body paragraphs: space_after=12pt
- Section headings (bold inline): space_after=4pt

**Tables (3 total):**
- Table 1 — Monthly earnings: header row bold 12pt, body rows 11pt, Total Earnings row bold 12pt
  - Columns: Earnings | Amount (₹)
  - Rows: Basic Salary, House Rent Allowance (HRA), Leave Travel Allowance (LTA), Work From Home Allowance, Flexi Pay, **Total Earnings**
- Table 2 — Monthly deductions: same sizing pattern
  - Columns: Deductions | Amount (₹)
  - Rows: Professional Tax, TDS @ 10%, **Total Deductions**
- Table 3 — Net take-home: single row, bold 13pt
  - Net Monthly Take Home | ₹67,300.00

**Conditional sections:**
- Internship acknowledgement paragraph (between offer paragraph and CTC line)
- Performance bonuses section (after net take-home table): Business Performance Bonus + Individual Performance Bonus, each with pct + period

**Fixed/hardcoded content:**
- Notice period: "eight (8) weeks" — not a field
- Terms and Conditions paragraph — boilerplate
- Documents Required list — boilerplate
- NDA paragraph — boilerplate
- Signatory: "Vishal Honnatti / Director" — hardcoded
- Footer: "#311/1, Zikhin Bhavan, 26th X, BSK II Stage, Bangalore - 560070 | www.bitloka.com | contact@bitloka.com"

---

## Current bundle state

```
data/templates/bitloka/offer_letter/v1/
  offer_letter_v1.html.j2   ← EXISTS but has no CSS, no logo, bare HTML
  offer_letter_v1.json      ← output_formats: ["docx"], has_jinja: true, css_file: null
```

**`catalogue.json`** — offer_letter entry present:
```json
{
  "doc_type": "offer_letter",
  "description": "Employment offer letter for new hires — Word document with compensation structure",
  "variants": [{ "version": "v1", "label": "Standard FTE", "output_formats": ["docx"], ... }]
}
```

**Pipeline wiring already in place (from m6):**
- Orchestrator `docx + narrative? + has_jinja? + no_sheets?` branch → `generate_html.py` → `generate_docx_from_html.py`
- `generate_pdf.py` `has_jinja` branch → `generate_html.py` → WeasyPrint
- `validate_fields.py` `OFFER_LETTER_REQUIRED` (19 fields including `title`)
- `rename_output.py` `candidate_name` fallback

---

## m7 Scope

**Goal:** replace the bare `offer_letter_v1.html.j2` with a proper HTML+CSS template that matches the Bitloka FTE offer letter, with WeasyPrint PDF as primary output.

**What is NOT in scope:**
- Changes to any pipeline script (`generate_html.py`, `generate_pdf.py`, `generate_docx_from_html.py`) — the m6 wiring is correct
- New doc types
- Shared tenant asset directory (logo stays in the bundle for now)
- `compute_offer.py` salary computation
- `is_intern` boolean field
- Context builder optional-field-name awareness (m6 t5 F2 — bonus fields named off-schema)
- Removing `render_template.py` / `.md.template` (deferred from m6)

**Output format change:** `offer_letter_v1.json` changes from `output_formats: ["docx"]` to `output_formats: ["pdf", "docx"]` — PDF becomes primary, DOCX is secondary.

**Ticket structure:**

| Ticket | Scope |
|---|---|
| t1 | `offer_letter_v1.html.j2` — proper HTML+inline CSS template (A4, logo, tables, conditionals, Calibri) |
| t2 | `offer_letter_v1.json` — add `"pdf"` to `output_formats`; copy `btl_logo-withtext.png` to offer_letter bundle dir; fix `css_file` handling for inline-CSS templates |
| t3 | `docbuilder_offer_letter` sprint update — assert `.pdf` + `.docx` outputs; zero `{{` in PDF; runbook update |
| t4 | Docs sync + milestone close |

**Key design decision — inline CSS vs separate `.css` file:**
The current invoice uses a separate `invoice_v1.css` file (referenced via `<link>`; WeasyPrint resolves it against `base_url`). For the offer letter, the CSS can be inline in the template (simpler, self-contained, no `base_url` resolution needed for styles) OR in a separate file. The StringTemplate examples Bitloka already uses have inline CSS. Recommend inline for m7; a shared CSS base for future doc types can be extracted later.

**`css_file: null` in `offer_letter_v1.json`:** the `_narrative_html_jinja` path in `generate_pdf.py` doesn't read `css_file` — confirmed safe in m6 t4b (e). No change needed to `generate_pdf.py` for inline CSS; `base_url` must still be set to the bundle directory for the logo `<img src="btl_logo-withtext.png">` to resolve.

---

## Conversation starter for the m7 session

Paste this at the start of the new session:

---

We're starting m7 of the docbuilder pipeline. Read `CLAUDE.md` and the project knowledge before we begin.

**State:** aetheris-agents @ `eeb37a1`, drift clean (8 PASS / 0 FAIL / 0 WARN). m1–m6 + rig-p9 are all closed.

**m7 goal:** replace the bare `offer_letter_v1.html.j2` (no CSS, no logo) with a proper HTML+inline CSS template that matches the Bitloka FTE offer letter. WeasyPrint PDF becomes the primary output; Pandoc DOCX is secondary (draft to edit).

**What already exists and must NOT be changed:**
- Pipeline wiring: `generate_html.py`, `generate_pdf.py` `has_jinja` branch, orchestrator `docx + narrative? + has_jinja? + no_sheets?` branch, `generate_docx_from_html.py` — all correct from m6
- `validate_fields.py` `OFFER_LETTER_REQUIRED` (19 fields including `title`)
- `rename_output.py` `candidate_name` fallback
- `offer_letter_v1.json` bundle spec (will gain `"pdf"` in `output_formats` in t2)

**The problem with the current output:**
1. No CSS — bare HTML, Pandoc maps `<h1>` to Word heading styles that don't match the reference
2. No logo
3. Currency values were extracted as integers (`37500`) not display strings (`37,500.00`) — the sprint request needs to supply them as formatted strings; `validate_fields.py` keeps them as display strings (same as `amount_due`)

**Reference letter structure** (from the actual `BTL-Offer_Letter-_Template_-_FTE_-_Ajay_Rao.docx`):
- A4, 1.3cm margins, Calibri 10pt throughout
- Logo top-left + "Bitloka Solutions Private Limited" bold 12pt header
- Section headings = bold inline runs (NOT heading styles) at 10pt
- 3 compensation tables: earnings (7 rows), deductions (4 rows), net take-home (1 row, 13pt bold)
- Conditional: internship acknowledgement paragraph, performance bonus section
- Hardcoded: notice period, T&C, documents required, NDA, signatory (Vishal Honnatti/Director), footer address

**Four design questions to resolve before drafting the milestone doc:**
1. **Inline CSS vs separate `.css` file** — the current invoice uses a linked `.css` file; recommend inline for the offer letter (self-contained, no path resolution needed for styles). Agree?
2. **Logo path** — copy `btl_logo-withtext.png` into `data/templates/bitloka/offer_letter/v1/`. Confirmed in the closing discussion. Just confirming before drafting.
3. **`base_url` for WeasyPrint** — the `generate_pdf._narrative_html_jinja` already sets `base_url` to the bundle dir for the invoice. Confirm this works the same way for the offer letter so `<img src="btl_logo-withtext.png">` resolves.
4. **Table borders** — the reference tables have thin borders. WeasyPrint renders `border: 1px solid #ccc` cleanly on A4. Any preference on border colour (match the invoice grey, or Bitloka orange `#F5A623` for headers)?

The handoff doc with full context is at `docbuilder/docs/milestones/m7-handoff.md`. Ready to draft the m7 milestone doc once the four design questions are resolved.
