# Implementation notes — m-docbuilder-m2b t1

Ticket: `DOCBUILDER_CONTEXT` schema doc + Drive folder structure doc (docs only).

---

## What shipped

- `docs/context-schema.md` — the `DOCBUILDER_CONTEXT` schema (source of truth):
  purpose, how it's passed (env → `--context` inline JSON; unset/empty → `{}`),
  a field table (required: `title`, `client_name`, `client_email`, `date`;
  optional: `doc_type`, `deal_type`, `tone`, `amount`) with a "consumed by"
  column, complete + minimal example JSON, the unknown-fields-ignored note, and
  a per-script validation table.
- `docs/drive-structure.md` — the `docbuilder` Shared Drive layout: tenant-first
  folder tree, `DRIVE_DOCBUILDER_ID` / `GOOGLE_SERVICE_ACCOUNT_FILE` env vars,
  output filename convention, step-by-step tenant onboarding, and a local-vs-Drive
  layout mapping.

---

## Decisions

**Added a "consumed by" column to the context field table.** The prompt asked for
field/type/required/description/example. I added which script(s) read each field,
because the context fans out to four consumers (render_template, LLM selection,
rename_output, email_send_review) and the mapping is the non-obvious part — it tells
the t2–t7 implementers exactly which fields each script must read/validate.

**`doc_type` documented as the Option A/B switch.** Listed optional, with the note
that its presence selects Option A (LLM picks variant only) vs Option B (LLM derives
doc_type + variant). This is the orchestrator behaviour t7 implements; documenting it
here keeps the context schema the single source of truth for it.

**Per-script validation table instead of a central validator.** There is no context
validator script (and the milestone doesn't call for one). Each consuming script
validates the fields it needs and exits 1 — so the schema doc records *which script
requires what* rather than implying a single gate.

---

## Finding for t2 — local vs Drive layout mismatch (flagged in drive-structure.md)

The m2b Drive bundle is **nested**: `{tenant}/templates/{doc_type}/{version}/{doc_type}_{version}.json`.
The committed m2a demo is **flat**: `data/templates/demo/proposal_v1.json`.

The t2 prompt says `fetch_template.py`'s local fallback should match
`data/templates/{tenant}/{doc_type}/{version}/` — i.e. the **nested** shape, which the
committed demo does not have. So t2 must either:
- (a) add a nested demo bundle under `data/templates/demo/proposal/v1/` for the
  local-fallback tests, or
- (b) have the fallback map the existing flat layout onto the bundle shape.

`drive-structure.md` §"Local vs Drive layout" documents the canonical (nested) Drive
layout and flags this explicitly so t2 starts from a known state. Not resolved here
(t1 is docs only; no scripts/assets).

## Forward notes

- **t2:** `fetch_template.py` (wide fetch) + `list_templates.py` Drive fallback; resolve
  the local-fallback layout question above.
- **t4 / t6:** `rename_output.py` validates `client_name` + `date`; `email_send_review.py`
  validates `client_name` + `client_email` + `date` — both per the validation table here.
- **t8:** README m2b → done; this doc pair is the contract those scripts were written against.
