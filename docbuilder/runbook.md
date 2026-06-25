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
