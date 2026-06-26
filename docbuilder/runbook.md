# Docbuilder Runbook

Operational guide for the docbuilder pipeline.

---

## Required env vars

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCBUILDER_TENANT` | Tenant name — selects the tenant subtree (`data/templates/{tenant}/` locally, or the Drive subtree) | `demo` |
| `DOCBUILDER_CONTEXT` | The single input blob — inline JSON of all run fields (see `docs/context-schema.md`). Required fields: `title`, `client_name`, `client_email`, `date`. Optional `doc_type` (selects Option A). | `{"title":"…","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}` |
| `ANTHROPIC_API_KEY` | Anthropic API key for the LLM | _(set in shell)_ |

> m2b note: `DOCBUILDER_DOC_TYPE` / `DOCBUILDER_VERSION` / `DOCBUILDER_DATA_PATH` (m1/m2a)
> are gone — the doc type/variant come from `DOCBUILDER_CONTEXT` + the catalogue (LLM
> selection), and data-source paths come from the template.

Optional — delivery (PHASE E/F skip when absent):

| Variable | Description |
|----------|-------------|
| `DRIVE_DOCBUILDER_ID` | `docbuilder` Shared Drive root id. Set → PHASE E uploads outputs to `{tenant}/output/`; unset → upload skipped. Also makes `list_templates`/`fetch_template` read from Drive. |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Service-account JSON path for Drive auth (falls back to `GOOGLE_SERVICE_ACCOUNT`). |
| `DOCBUILDER_REVIEW_EMAIL` | Internal review alias. Set → PHASE F emails it (with `SMTP_*`); unset → email skipped. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | SMTP creds for PHASE F (same as `email/scripts/email_send.py`). |
| `AETHERIS_MODEL` / `AETHERIS_PROVIDER` | Model/provider overrides (default `claude-haiku-4-5-20251001` / `anthropic`). |

### Pipeline phases (m2b)

The orchestrator resolves the template + delivery options at eval time and runs:

- **PHASE 0 — Template selection:** `list_templates.py --tenant {tenant}` → the LLM picks
  `{doc_type, variant}` from the catalogue + context → `fetch_template.py` downloads the
  bundle (Drive → local cache; no Drive → committed local nested bundle).
- **PHASE A — Fetch:** one `fetch_data.py --output` per `data_sources` entry. Paths are
  the template's, with the leading `docbuilder/` stripped (sandbox-relative). A declared
  source not read by any sheet is still fetched (e.g. the demo `summary`).
- **PHASE B — Compute:** `compute_doc.py {bundle}/…json {raw files} --output pipeline_spec.json`.
- **PHASE C — Render:** each `output_formats` entry; xlsx/docx get `--base-file` from the
  bundle, pdf gets `--template-dir {bundle}` + `--context` (narrative mode).
- **PHASE D — Rename:** `rename_output.py` → `{client_name_slug}_{doc_type}_{date}.{ext}`.
- **PHASE E — Upload** (only if `DRIVE_DOCBUILDER_ID` set): `upload_output.py` → `{tenant}/output/`.
- **PHASE F — Email** (only if `DOCBUILDER_REVIEW_EMAIL` set): `email_send_review.py` to the
  review alias with the Drive links.

In dev (no Drive/SMTP creds) PHASE E/F skip with a notice; the sprint verifies PHASE 0–D.

---

## Python dependencies

The renderer scripts need these third-party packages in the mise Python env:

```bash
python3 -m pip install openpyxl python-docx weasyprint markdown
```

- `openpyxl` — `generate_xlsx.py`
- `python-docx` — `generate_docx.py`
- `weasyprint` — `generate_pdf.py`
- `markdown` — `render_template.py` (narrative-mode PDF)

> A pinned `requirements.txt` is added at m2a t10. Until then, tests for a renderer
> whose dependency is missing **skip** (via `pytest.importorskip`) rather than fail —
> so a missing package is silent. Install the list above for a complete run.

---

## How to run

### Via sprint.sh (recommended)

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
./scripts/sprint.sh docbuilder
# add DRIVE_DOCBUILDER_ID / GOOGLE_SERVICE_ACCOUNT_FILE / DOCBUILDER_REVIEW_EMAIL / SMTP_*
# to also exercise PHASE E (upload) and PHASE F (email).
```

Other sprint cases:
- `./scripts/sprint.sh docbuilder_context` — m3 context builder → orchestrator chain
  ("same as last month").
- `./scripts/sprint.sh docbuilder_fresh` — m4 freeform fresh path: `context_builder.exs`
  extracts fields from a freeform `DOCBUILDER_REQUEST`, validates via `validate_fields.py`,
  and writes `confirmed_context.json`. Resets `run_log.json` to `[]` first (forces the fresh
  path); asserts the context is written + parseable and the run log is NOT appended
  (builder-only — PHASE D2 runs with the orchestrator). Full m4 detail: §"m4 — freeform NL
  field extraction" below.
- `./scripts/sprint.sh docbuilder_fresh_render` — m5 full fresh→render chain: builder-only
  `docbuilder_fresh` plus the orchestrator step. Chains `context_builder.exs` (fresh extract)
  → `docbuilder_orchestrator.exs` (reads `confirmed_context.json` via `DOCBUILDER_CONTEXT_FILE`,
  renders + PHASE D2). Resets `run_log.json` to `[]`; asserts every `renamed.json` output
  exists + non-empty, the rendered **PDF has no unresolved `{{placeholder}}` strings** (m5 t1
  `_sub_var` fix — degrades to `[INFO]` if `pdftotext` is absent), and the run log has exactly
  1 entry (PHASE D2 appended: 0 → 1).

### Direct run

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
mix aetheris run ../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs
```

### Syntax check (no LLM call)

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs")'
```

---

## Expected output

After a successful run, `docbuilder/output/` will contain:

```
output/template_cache_path.txt              # PHASE 0 — bundle path (fetch_template)
output/pipeline_raw_main.json               # PHASE A — raw fetch (one per source)
output/pipeline_raw_summary.json            # PHASE A — second source (demo)
output/pipeline_spec.json                   # PHASE B — computed doc spec
output/acme_corp_proposal_2026-06-20.xlsx   # PHASE C+D — branded, renamed (was proposal_v1.xlsx)
output/acme_corp_proposal_2026-06-20.docx   # PHASE C+D — branded, renamed
output/acme_corp_proposal_2026-06-20.pdf    # PHASE C+D — narrative, renamed
output/renamed.json                         # PHASE D — {original, renamed} pairs
output/uploaded.json                        # PHASE E — {filename, drive_file_id, drive_url} (only if Drive enabled)
```

The renamed filenames come from `DOCBUILDER_CONTEXT` (`{client_name_slug}_{doc_type}_{date}`).
The intermediate `proposal_v1.*` files are renamed away by PHASE D.

The formats generated depend on the `output_formats` array in the template. The
`demo/proposal_v1.json` template specifies `["xlsx", "docx", "pdf"]`. xlsx/docx open
their base files when present; pdf uses narrative mode when the template has a
`narrative` block and `--template-dir` is supplied.

---

## Template location convention

Templates live at:
```
data/templates/{DOCBUILDER_TENANT}/{DOCBUILDER_DOC_TYPE}_{DOCBUILDER_VERSION}.json
```

Example: `DOCBUILDER_TENANT=demo`, `DOCBUILDER_DOC_TYPE=proposal`, `DOCBUILDER_VERSION=v1`
→ `data/templates/demo/proposal_v1.json`

---

## Running tests

```bash
cd ~/sandbox/elixirws/aetheris-agents

# All docbuilder tests
python3 -m pytest docbuilder/tests/ -v

# Single script
python3 -m pytest docbuilder/tests/test_compute_doc.py -v
```

---

## m4 — freeform NL field extraction

The context builder's **fresh path** (no recurring "same as last month" match) turns a
freeform `DOCBUILDER_REQUEST` into a `confirmed_context.json`:

1. **Extract** — the LLM extracts a raw field map from the request (client, title, date,
   doc_type, invoice fields, and any `unit_price`/`line_item_qty`/`currency` stated) →
   `output/raw_extraction.json`.
2. **Validate** — `validate_fields.py --input output/raw_extraction.json --output
   output/validated_extraction.json` validates + normalises against the context schema
   (date → ISO 8601; `amount_due` validated-as-money but **kept as a display string**;
   `unit_price`/`line_item_qty` → numeric; `currency` → upper + checked against
   `{GBP,USD,EUR,AED,INR}`; required fields per `doc_type`). Exit 0 → normalised context;
   exit 1 → `{"missing":[...],"invalid":{...}}` payload (no partial context).
3. **Self-correct once** — on exit 1 the agent re-reads the original request for the named
   fields and re-validates ONCE. There is **no in-run human reply** (single-shot
   `mix aetheris run`, no `ask_human` tool — same model as the m3 confirmation gate).
4. **Gate or clarify** — exit 0 → write `output/confirmed_context.json`, emit the
   `PROPOSED DOCBUILDER_CONTEXT` block (the operator reviews before rendering). Still
   failing after the second pass → the agent emits one clarifying message naming the
   fields and STOPS without writing the context; the operator re-runs with the field
   included (the "reply" is a re-run).

### Sprint case

```bash
cd ~/sandbox/elixirws/aetheris
DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh
```

Runs only `context_builder.exs` with a freeform `DOCBUILDER_REQUEST`, resets
`data/run_log.json` to `[]` (forces the fresh path), and asserts `confirmed_context.json`
is written + parseable and the run log is NOT appended (builder-only — PHASE D2 appends
only when the orchestrator runs). The client-match assertion is client-agnostic (m5 t2): it
passes for any non-empty `client_name` (and reports the parsed client in the `[OK]` line), so
overriding `DOCBUILDER_REQUEST` for a different client works.

### Output files (m4)

- `output/raw_extraction.json` — the LLM's raw extracted field map (gitignored).
- `output/validated_extraction.json` — `validate_fields.py`'s normalised context (exit 0)
  or `{missing,invalid}` error payload (exit 1). Inspect this when the fresh path stops
  with a clarifying message.

### Failure mode — `validate_fields.py` exit 1

Read `output/validated_extraction.json`: `missing` lists absent required fields, `invalid`
maps a field to why it was rejected (bad date, unknown currency, non-monetary amount, bad
email). Supply the field in `DOCBUILDER_REQUEST` and re-run. The validator never fabricates
or defaults a value (e.g. a fresh invoice missing `invoice_number` is flagged, not invented).

---

## Common failure modes

### `DOCBUILDER_TENANT not set` (or similar) on eval

All four `DOCBUILDER_*` vars must be exported before running `mix aetheris run`
or `mix run --eval`. The orchestrator raises immediately if any are absent.

### Output files missing after run

Check `overlay_base_dir` — it must be `nil`. If output files appeared in a
per-run `upper/` directory under `priv/runs/`, `overlay_base_dir` was set
non-nil. The orchestrator explicitly sets `overlay_base_dir: nil`.

### `python3 python3 script.py` in run_command

The LLM duplicated the executable in both `command` and `args`. The system
prompt explicitly warns: "Do not pass 'python3' inside the args array." If
this happens, re-run — the system prompt guard should prevent it.

### Template not found (exit code 1 from compute_doc.py)

Verify the template path:
```bash
ls docbuilder/data/templates/demo/
```
Expected: `proposal_v1.json`. The path is constructed as
`data/templates/{TENANT}/{DOC_TYPE}_{VERSION}.json`.

### Env vars not inherited by workers

The exec server spawns workers at invocation time and they inherit the
environment at that moment. If you exported env vars after starting a
long-lived worker, kill stale workers and re-run:
```bash
pkill -f aetheris_worker
```

### Stale `output/pipeline_raw_*.json` or `output/pipeline_spec.json`

These intermediates are overwritten on each run (one `pipeline_raw_{key}.json`
per data source, plus `pipeline_spec.json`). If a partial run left stale
intermediates, delete them before re-running:
```bash
rm -f docbuilder/output/pipeline_raw_*.json docbuilder/output/pipeline_spec.json
```
