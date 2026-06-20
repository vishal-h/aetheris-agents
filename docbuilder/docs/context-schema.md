# docbuilder — `DOCBUILDER_CONTEXT` schema

`DOCBUILDER_CONTEXT` is a single JSON object carrying the run's scalar variables.
It is the one input blob that drives three things:

1. **Narrative PDF** — scalar `{{variable}}` substitution in the `.md.template`
   (via `render_template.py`).
2. **LLM template selection** (m2b) — the context is shown to the LLM alongside the
   catalogue so it can pick the right `{doc_type, variant}`.
3. **Delivery** — output file naming (`rename_output.py`) and the review email
   (`email_send_review.py`).

This document is the **source of truth** for the context fields. It is designed so a
later milestone can generate an input form (e.g. a Tauri form) directly from this
schema.

---

## How it is passed

The orchestrator reads `DOCBUILDER_CONTEXT` from the environment at eval time. Unset
or empty resolves to `"{}"` — it is never passed as an empty string to a script (an
empty `--context` would fail `json.loads`). Scripts receive it inline via a `--context
'<json>'` argument.

```bash
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"20 Jun 2026"}'
```

---

## Fields

| Field | Type | Required | Description | Example | Consumed by |
|-------|------|----------|-------------|---------|-------------|
| `title` | string | **yes** | Document title; the `{{title}}` narrative variable and the document heading. | `"B2B Project Proposal"` | render_template (narrative PDF) |
| `client_name` | string | **yes** | Customer name; the `{{client_name}}` narrative variable. Also used in the output filename (slugified: lowercased, spaces → underscores). | `"Acme Corp"` | render_template, rename_output, email_send_review |
| `client_email` | string | **yes** | The external recipient. Placed in the **review email body** so the ops reviewer can forward — it is *not* a direct send target (see the review-alias design decision in README). | `"ops@acme.example"` | email_send_review |
| `date` | string | **yes** | Proposal/issue date, ISO (`2026-06-20`) or display (`20 Jun 2026`) format. The `{{date}}` narrative variable; also used in the output filename. | `"20 Jun 2026"` | render_template, rename_output, email_send_review |
| `doc_type` | string | optional | The doc type to render. **Option A** (LLM picks variant only) when present; **Option B** (LLM derives doc_type + variant) when absent. Also used in the output filename. | `"proposal"` | LLM selection, rename_output, email_send_review |
| `deal_type` | string | optional | Free-text deal classification; context hint for LLM variant selection. | `"fixed-scope delivery"` | LLM selection |
| `tone` | string | optional | One of `"formal"` / `"standard"` / `"informal"`; context hint for LLM variant selection. | `"formal"` | LLM selection |
| `amount` | string \| number | optional | Headline deal amount; context hint for LLM selection / narrative prose. | `21090` or `"21,090 USD"` | LLM selection, render_template |

> **Unknown fields are silently ignored.** Scripts read only the fields they need
> (`dict.get`); extra keys do not error. This keeps the context forward-compatible —
> a Tauri form can add fields before any script consumes them.

> **Narrative variables vs context fields.** The `.md.template` may reference
> `{{variable}}` placeholders. Those names must match context keys to be substituted;
> an unmatched `{{variable}}` is left as-is with a stderr warning (see
> `render_template.py` / doc-spec-schema §"Renderer contract").

---

## Complete example

```json
{
  "title": "B2B Project Proposal",
  "client_name": "Acme Corp",
  "client_email": "ops@acme.example",
  "date": "20 Jun 2026",
  "doc_type": "proposal",
  "deal_type": "fixed-scope delivery",
  "tone": "formal",
  "amount": "21,090 USD"
}
```

Minimal (required fields only; Option B — LLM derives the doc type):

```json
{
  "title": "B2B Project Proposal",
  "client_name": "Acme Corp",
  "client_email": "ops@acme.example",
  "date": "20 Jun 2026"
}
```

---

## Validation

There is no central validator script. Each consuming script validates the fields it
requires and exits 1 with a JSON error on stderr if one is missing.

> This table reflects m2b scope. **Scripts are the authoritative source** — consult a
> script's `main()` argparse/validation block if in doubt.

| Script | Requires |
|--------|----------|
| `rename_output.py` | `client_name`, `date` (`doc_type` falls back to the filename prefix) |
| `email_send_review.py` | `client_name`, `client_email`, `date` |
| LLM selection (orchestrator) | `doc_type` only for Option A; none for Option B |
| `render_template.py` | none hard-required — unmatched `{{variables}}` warn, not fail |
