# Review — m7 t1 — round 1

Reviewer: claude-ui
Subject: `offer_letter_v1.html.j2` HTML + inline-CSS template
(pre-t1 doc correction `db3a430`; t1 `b815d61`; round-1 fixes `<this commit>`)

> Path note: filed at `docbuilder/docs/reviews/` (round-2 F1 — consolidated to match m1–m6;
> repo-root `docs/reviews/` is for other use cases, e.g. eduloka/playground). The m7 milestone
> doc's File-locations + t4 review-scan were corrected to `docbuilder/docs/reviews/`.

---

## Findings

**1. [blocking] Net table renders 11pt normal, not 13pt bold (CSS cascade).** `table.comp
tbody td {font-size:11pt}` (specificity 0,1,3) out-specifies `table.net td {…13pt bold}`
(0,1,2), so WeasyPrint renders the Net row like a body row. Fix: raise specificity or make the
Net table standalone (no `comp`).

**2. [blocking] Bonus section conditionals not independent.** The outer
`{% if business_performance_bonus_pct %}` wrapped both the heading and the individual block, so
an individual-only bonus (business absent) rendered neither the heading nor the individual line.
Fix: `{% if business_… or individual_… %}` around the heading, then guard each paragraph.

**3. [non-blocking] Subject line not underlined.** Reference letter underlines "Re: Offer of
Employment". Add `text-decoration: underline` to `.subject`.

**4. [non-blocking] `candidate_phone` join.** `email | phone` leaves a trailing `email | ` if
phone is empty. Confirm whether `candidate_phone` is required (then guard is optional polish) or
optional (then mandatory). Guard with `{% if candidate_phone %}`.

**5. [question] `title` vs `candidate_name`.** Confirm the filename slug uses `candidate_name`
(not `title`); clarify the t1 note so t3's slug assertion targets the right slug.

## Cross-ticket notes

Pre-t1 doc correction correctly scoped; 17/17 field-coverage cross-check is a good done-check
addition — keep it in t3. F1 is the "unit check passes, artifact wrong" pattern from the m6
learning — fix before t3 runs rather than discover there.

---

## Resolution (round-1 fixes, all verified)

- **F1 — fixed by making the Net table standalone `class="net"`** (dropped `comp`), with its own
  border/padding/13pt-bold rules. `table.comp tbody td` no longer matches it, so there is no
  competing rule at all (stronger than just raising specificity). Verified: `<table class="net">`,
  no `class="comp net"`. Visual 13pt confirmed at t3's PDF render.
- **F2 — fixed.** `{% if business_… or individual_… %}` wraps the heading; each bonus paragraph
  guarded independently. Verified: individual-only → heading + individual (business absent);
  both absent → section suppressed.
- **F3 — fixed.** `.subject { text-decoration: underline; … }`.
- **F4 — `candidate_phone` IS required** (in `OFFER_LETTER_REQUIRED`), so always present; added
  the defensive `{% if candidate_phone %} | {{ … }}{% endif %}` guard anyway. Verified: absent
  phone → no trailing pipe.
- **F5 — confirmed + note corrected.** Filename slug = `candidate_name` (`rename_output.py`
  fallback); `compute_doc` takes the doc-spec title from the bundle spec (`template["title"]`),
  not context. `title` (context) is validated-but-not-rendered. t1 note updated; t3 slug
  assertion targets `ajay_rao_offer_letter_*`.

Re-ran the §t1 done-check + four edge cases (F1 standalone, F2a individual-only, F2b both-absent,
F4 absent-phone) → **ALL CHECKS PASS**.

## Disposition

**t1 clear to merge** after the round-1 fixes (both blocking findings resolved + the two polish
items + F5 clarified). Template code updated in `<this commit>`.

---

## Round 2

**F1 [blocking] — review-path convention.** Resolved by human decision: **consolidate under
`docbuilder/docs/reviews/`** (match m1–m6). Actioned: `git mv` of this file to
`docbuilder/docs/reviews/m7-offer-letter-t1-review.md`; the m7 milestone doc's File-locations
block + t4 review-scan path both corrected to `docbuilder/docs/reviews/`. Doc and file now agree
(methodology §1.1). Repo-root `docs/reviews/` is used by other use cases (eduloka, playground),
not docbuilder — so the Phase-1 `docs/reviews/` was the defect.

**F2 [non-blocking] — phone note.** t1 notes tightened: `candidate_phone` IS required;
`validate_fields` treats empty/whitespace as missing, so a valid context always has it. The
guard is defensive against an empty value reaching the template via a non-validated path, NOT
against absence in production.

**F3 [non-blocking] — title note.** t1 notes use the **validated-but-not-rendered** framing and
correctly record that `compute_doc`'s doc-spec title comes from the bundle spec
(`template["title"]`), not context — so context `title` is required-but-consumed-nowhere for the
offer letter.

**Cross-ticket (carried into t3 §scope):** keep the four t1 edge cases as committed sprint
assertions; assert the Net-table F1 fix structurally (rendered HTML has standalone
`<table class="net">`); pixel-13pt is a human visual check of the PDF.

**Disposition: t1 fully closed.** No template code change in round 2 (path/doc/notes only).
