# Implementation notes — m7 t3 (`docbuilder_offer_letter` sprint update)

Ticket: update the `docbuilder_offer_letter` sprint case to assert both `.pdf` and `.docx`
outputs, zero `{{` in the PDF, currency as display strings (D5), + a runbook line. The live
end-to-end is the m7 rendering gate.

---

## What shipped

- **`aetheris/scripts/sprint.sh`** — `docbuilder_offer_letter` case reworked
  **fresh-path → direct-context** (see decision below). It now: sets `DOCBUILDER_CONTEXT`
  inline JSON (all 18 required fields as **display strings**, e.g. `"₹37,500.00"`, + the
  internship + both bonus optionals), unsets `DOCBUILDER_CONTEXT_FILE`, seeds `run_log.json` to
  `[]`, clears stale render artifacts, evals + runs the **orchestrator** directly (no
  context_builder), then asserts:
  - every `renamed.json` output exists + non-empty;
  - `renamed.json` contains **BOTH a `.pdf` and a `.docx`** (D6);
  - the slug uses `candidate_name` (`ajay_rao_offer_letter_*`, not `title` — t1 F5);
  - the PDF has **zero `{{`** AND a **`₹` display string** (`37,500.00`) — D5;
  - the rendered `output/offer_letter_v1.html` uses the standalone `<table class="net">`
    (t1 F1 structural check; pixel-13pt is a human visual check);
  - run log `0 → 1` (PHASE D2).
- **`docbuilder/runbook.md`** — updated the `docbuilder_offer_letter` sprint-case entry
  (→ PDF + DOCX, direct display-string context) + a one-line m7 note in §"Jinja2 templates (m6)".

## Decision — fresh-path → direct-context (adjudicated; flag for review)

The m6 case was fresh-path (NL `DOCBUILDER_REQUEST` → `context_builder` → `confirmed_context`).
m7 D5 requires **display-string currency**, which the fresh/NL path **cannot guarantee** — the
LLM strips `₹37,500.00` to the int `37500` and renames optional fields off-schema (the m6 t5 F2
finding, explicitly out of m7 scope). To test m7's actual deliverable — the template's
rendering fidelity with correct inputs — the case now supplies context **directly** via
`DOCBUILDER_CONTEXT` and runs the orchestrator alone. The t3 prompt explicitly allowed
"`DOCBUILDER_CONTEXT` inline JSON", so this is the faithful reading.

**Trade-off:** this case no longer exercises `context_builder` for `offer_letter`. That path was
proven live at m6 t5 (`docbuilder-orch-MXl0Ew`), and `OFFER_LETTER_REQUIRED` validation is unit-
tested (`test_validate_fields.py`), so the loss is the *live fresh extraction for offer_letter*
specifically — acceptable for an m7 rendering-focused gate. If ongoing fresh-extraction coverage
for offer_letter is wanted, a separate fresh case can be added later. **Flagged for review.**

## Bug found + fixed during implementation (sprint wiring, not template/bundle)

The first run died right after `docbuilder_orchestrator.exs evaluates`, before `run_agent`. Cause:
`CAND=$(python3 -c "… os.environ['DOCBUILDER_CONTEXT'] …")` read the var from the **environment**,
but `DOCBUILDER_CONTEXT='…'` is a shell var (not exported) → `KeyError` → under `set -euo pipefail`
the failed command substitution **killed the script**. Fixed by passing the JSON via **argv**
(`… sys.argv[1] …` + `|| echo "?"`), no env dependency. This is exactly the predicted failure
surface: t2's end-to-end PDF render had already de-risked the template/bundle, so the only thing
left to break was the sprint wiring / context blob — and it was.

## Done-check (live)

`DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_offer_letter` → **all PASS**, run
`docbuilder-orch-iDGIIQ`:
```
[OK] docbuilder_orchestrator.exs evaluates
[INFO] Candidate: Ajay Rao  (direct DOCBUILDER_CONTEXT, display-string currency)
[OK] rendered: ajay_rao_offer_letter_2026-07-01.docx (24K)
[OK] rendered: ajay_rao_offer_letter_2026-07-01.pdf (84K)
[OK] renamed.json contains BOTH a .pdf and a .docx output
[OK] renamed slug uses candidate_name (ajay_rao_offer_letter_*)
[OK] no {{placeholders}} in ajay_rao_offer_letter_2026-07-01.pdf
[OK] display-string currency rendered in PDF (37,500.00 — D5)
[OK] rendered HTML uses standalone <table class="net"> (t1 F1)
[OK] run log appended (PHASE D2 fired: 0 → 1 entry)
```
`bash -n scripts/sprint.sh`: clean.

## Round-1 review fixes (claude-ui)

- **F1 [non-blocking] — stale runbook ref.** `docbuilder/runbook.md` §"Jinja2 templates"
  deprecation note said "removal is m7"; `render_template.py` removal was descoped from m7.
  Updated to "**removal deferred (post-m7)** — descoped from m7, tracked as an m8 open item".
- **F2 [question] — does `offer_letter_v1.html` persist? + is the `[INFO]` fallback a silent
  pass?** Confirmed it persists: the docx-jinja step (`generate_html.py --output`) writes it,
  `generate_pdf` renders **in-process** (`render_html`, no `.html` file I/O), and
  `rename_output.py` only renames `KNOWN_EXTS` (`.html` not among them) — so nothing
  consumes-and-deletes it. **Hardened** the check anyway: a missing intermediate is now a
  `fail` (not `[INFO]`-skip), since for a pdf+docx `has_jinja` bundle the file MUST exist — the
  `[INFO]` branch would have been a silent pass on a regression. Re-ran: still PASS (file present,
  standalone `<table class="net">`).

## Notes

- `sprint.sh` is committed in the sibling `aetheris` repo (separate from this repo's commit).
- The done-check command-shape lesson recurs (CAND env-var; t2 `cat["doc_types"]`; m6 t4b
  positional; m5 t1 smoke) — a CLAUDE.md learning-promotion candidate for t4.
