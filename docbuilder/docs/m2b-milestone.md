# m-docbuilder-m2b — LLM selection + Drive registry + delivery

> Milestone doc for `aetheris-agents/docbuilder/` — m2b.
> Canonical. Do not edit scope in issue comments — edit here first.

---

## Goal

Templates and base files fetched from Drive at runtime. LLM picks the right
doc type and variant from the catalogue. Output renamed, uploaded to Drive,
and emailed to an internal review alias. Orchestrator hardened to zero scratch
artifacts.

After this milestone: a sprint run fetches the template bundle from Drive,
uses the LLM to select the variant, generates branded xlsx/docx/pdf, renames
the outputs, uploads to Drive, and sends a review email — all from a single
`DOCBUILDER_CONTEXT` JSON blob.

---

## What is NOT in m2b

- Natural language requests (Option C) — → m3
- Conversational template editing — → m3
- Tauri form for `DOCBUILDER_CONTEXT` input — → future
- Multi-user collaboration or approval workflows — → future

---

## Contract refs (read before any ticket)

- `docs/agent-creation-guide.md` — all agent/script conventions (authoritative)
- `docs/milestone-methodology.md` — ticket loop, review format, sizing rule
- `CLAUDE.md` (aetheris-agents root) — standing conventions; read at session start
- `../aetheris/CLAUDE.md` — harness-side conventions
- `docbuilder/README.md` — design decisions, Drive structure, context schema
- `docbuilder/docs/doc-spec-schema.md` — doc spec contract (authoritative for renderers)
- `docbuilder/docs/template-schema.md` — template JSON schema
- `drive/scripts/drive_utils.py` — existing Drive auth/navigation utilities (reference)
- `email/scripts/email_send.py` — existing email send script (reference)

---

## Design decisions (resolved before tickets start)

| Decision | Rationale |
|---|---|
| Drive Shared Drive name: `docbuilder` | Single shared drive, one root `DRIVE_DOCBUILDER_ID`. Tenant subtrees shareable independently. |
| Tenant-first folder structure | `{tenant_id}/templates/` and `{tenant_id}/output/` — access control and onboarding are per-tenant, not per-function. |
| Template bundle: wide fetch | `fetch_template.py` downloads entire `{doc_type}/{version}/` subfolder to local cache. One call, all assets. |
| `list_templates.py` falls back to flat file | When `DRIVE_DOCBUILDER_ID` is absent, reads flat `catalogue.json` (m2a behaviour). Drive-backed in production. |
| Output renamed before upload | `rename_output.py` renames to `{client_name}_{doc_type}_{date}.{ext}`. Deterministic script, not LLM work. |
| Email to internal review alias | `DOCBUILDER_REVIEW_EMAIL` receives with `client_email` in body. Ops reviews and forwards. No accidental direct client delivery. |
| `DOCBUILDER_CONTEXT` schema is standalone doc | `docs/context-schema.md` — source of truth for context fields, designed for eventual Tauri form. |
| LLM selection output is small structured JSON | `{doc_type, variant, rationale}` — the LLM decides; scripts do everything after. Eval-time resolution pattern from m2a preserved. |
| `fetch_data.py --output FILE` | Eliminates remaining PHASE A `write_file` calls. Same pattern as `compute_doc.py --output FILE`. |

---

## Tickets

---

### t1 — `DOCBUILDER_CONTEXT` schema doc + Drive folder structure doc

**Scope.** Two documentation artifacts before any code is written. First:
`docs/context-schema.md` — the standalone schema for `DOCBUILDER_CONTEXT`
JSON, documenting every field (required/optional, type, description, example).
Required m2b fields: `title`, `client_name`, `client_email`, `date`.
Optional: `deal_type`, `tone`, `amount`. Second: `docs/drive-structure.md` —
the canonical Drive folder layout for the `docbuilder` Shared Drive, the
`DRIVE_DOCBUILDER_ID` env var, and the tenant onboarding procedure (how to
create a tenant subtree, upload a template bundle, and verify with
`list_templates.py`).

**Contract refs.** `docbuilder/README.md` §"Design decisions" (`DOCBUILDER_CONTEXT`
schema, Drive structure, tenant-first layout); `docs/agent-creation-guide.md`
§"Script design".

**Touches.**
- `docbuilder/docs/context-schema.md` (new)
- `docbuilder/docs/drive-structure.md` (new)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t1-implementation-notes.md` (new)

**Do not generate.** No Python scripts, no agent files, no test files in
this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Both docs exist and are non-empty
wc -l docs/context-schema.md docs/drive-structure.md

# context-schema.md documents all required fields
grep -c "client_name\|client_email\|title\|date" docs/context-schema.md

# drive-structure.md contains the folder tree
grep -c "DRIVE_DOCBUILDER_ID\|tenant_id\|templates\|output" docs/drive-structure.md
```

**claude-code-prompt.**
> Read `docs/agent-creation-guide.md` §"Script design", `CLAUDE.md`,
> `docbuilder/README.md` §"Design decisions" and §"m2b scope" before writing.
>
> **`docs/context-schema.md`:** Document the `DOCBUILDER_CONTEXT` JSON schema.
> Must cover: purpose (scalar variable context for narrative PDF + LLM selection
> + delivery); all fields in a table (field name, type, required/optional,
> description, example value); a complete example JSON object; a note that this
> doc is the source of truth for any Tauri form generation in a later milestone.
> Required fields: `title` (string), `client_name` (string, used in output
> filename — will be slugified), `client_email` (string, recipient for review
> email body), `date` (string, ISO or display format). Optional: `deal_type`
> (string), `tone` (string: `"formal"` / `"standard"` / `"informal"`),
> `amount` (string or number). Include a note that unknown fields are silently
> ignored by scripts.
>
> **`docs/drive-structure.md`:** Document the `docbuilder` Shared Drive layout.
> Must cover: the full annotated folder tree (tenant-first: `{tenant_id}/
> templates/{doc_type}/{version}/` and `{tenant_id}/output/`); the
> `DRIVE_DOCBUILDER_ID` env var (the Shared Drive root folder ID); the
> tenant onboarding procedure step-by-step (create subfolder, upload
> `catalogue.json`, create doc-type/version subfolders, upload template bundle
> files, verify with `list_templates.py --tenant {id}`); and the output
> filename convention (`{client_name}_{doc_type}_{date}.{ext}`).
>
> **Review packet must open with the full done-check output block.**

---

### t2 — `fetch_template.py` + `list_templates.py` Drive update

**Scope.** Two script changes. First: new `fetch_template.py` — given a
tenant, doc type, and version, downloads the entire version subfolder from
Drive to a local cache dir and returns the cache dir path. Second:
`list_templates.py` updated to read `catalogue.json` from Drive when
`DRIVE_DOCBUILDER_ID` is set, falling back to the flat file when it is not.
The m2a flat-file behaviour and all existing tests must be preserved.

**Contract refs.** `docbuilder/docs/drive-structure.md` (Drive layout);
`docbuilder/docs/context-schema.md`; `agent-creation-guide.md` §"Script
design"; `drive/scripts/drive_utils.py` (Drive auth pattern — reference,
do not import directly).

**Touches.**
- `docbuilder/scripts/fetch_template.py` (new)
- `docbuilder/scripts/_drive.py` (new — shared Drive auth/navigation/download helper;
  also used by `list_templates.py` here and `upload_output.py` in t5)
- `docbuilder/scripts/list_templates.py` (update — Drive fallback)
- `docbuilder/data/templates/demo/proposal/v1/proposal_v1.*` (new — nested demo
  bundle for the local fallback; see Option A below)
- `docbuilder/tests/test_fetch_template.py` (new)
- `docbuilder/tests/test_list_templates.py` (update — Drive path tests)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t2-implementation-notes.md` (new)

**Pre-flight (from t1 review).**
- Install `google-api-python-client` in the mise env before implementing
  (`python3 -m pip install google-api-python-client`); add it to
  `requirements.txt` at t8. `fetch_template.py` and `upload_output.py` need it.
- **Nested vs flat layout — Option A (resolved at t1 review):** the Drive bundle is
  nested (`{tenant}/templates/{doc_type}/{version}/`) but the committed m2a demo is
  flat (`data/templates/demo/proposal_v1.json`). Add a **nested demo bundle** at
  `data/templates/demo/proposal/v1/proposal_v1.{json,docx,xlsx,md.template,css}`
  (copies of the flat files) for `fetch_template.py`'s local-fallback tests. Leave the
  flat files untouched — the m2a orchestrator still uses them directly via its
  eval-time `template_rel` path. Clean separation: flat = m2a direct path, nested =
  m2b fetch_template local fallback. (See `docs/drive-structure.md` §"Local vs Drive
  layout".)

**Do not generate.** Do not modify any renderer scripts or the orchestrator
in this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Existing list_templates tests still pass (flat-file path)
python3 -m pytest tests/test_list_templates.py -v

# New fetch_template tests pass
python3 -m pytest tests/test_fetch_template.py -v

# Full regression
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -5
```

**claude-code-prompt.**
> Read `docs/agent-creation-guide.md` §"Script design", `CLAUDE.md`,
> `docbuilder/docs/drive-structure.md`, `docbuilder/docs/context-schema.md`,
> `drive/scripts/drive_utils.py` (for Drive API auth pattern), and
> `docbuilder/scripts/list_templates.py` before writing any code.
>
> **`fetch_template.py`:** accepts `--tenant`, `--doc-type`, `--version`,
> `--cache-dir` (default `output/template_cache`), and optional
> `--drive-id` (falls back to `DRIVE_DOCBUILDER_ID` env var).
> Downloads the entire `{tenant}/templates/{doc_type}/{version}/` subfolder
> from the Drive Shared Drive to `{cache_dir}/{tenant}/{doc_type}/{version}/`.
> Returns the local cache dir path to stdout. Exit 1 if Drive ID absent or
> download fails. Use `googleapiclient` (same auth as `drive_utils.py`).
> When `DRIVE_DOCBUILDER_ID` is absent and a local fallback path matches
> `data/templates/{tenant}/{doc_type}/{version}/`, use it (allows tests to
> run without Drive credentials by pointing at the demo flat files).
>
> **`list_templates.py` update:** if `DRIVE_DOCBUILDER_ID` is set, download
> `{tenant}/templates/catalogue.json` from Drive to a temp file and read it;
> if not set, read the flat `data/templates/{tenant}/catalogue.json` as before.
> All existing unit and CLI tests must continue to pass (they don't set the
> env var, so they exercise the flat-file path).
>
> Tests for `fetch_template.py`: local fallback path (no Drive creds needed
> for CI); Drive path mocked or skipped with `pytest.mark.integration`.
> Tests for `list_templates.py` update: add a test that confirms Drive path
> is taken when env var is set (mock the Drive download).
>
> **Review packet must open with the full done-check output block.**

---

### t3 — `fetch_data.py --output FILE` + orchestrator PHASE A hardening

**Scope.** Add `--output FILE` to `fetch_data.py` (same pattern as
`compute_doc.py --output FILE` from m2a t10): when provided, write the raw
JSON to the file and print only the path. Update the orchestrator PHASE A
to use `--output` for each source fetch, eliminating the `write_file` calls
for raw source files. Strengthen the orchestrator "don't investigate" rule.
Sprint re-run to confirm scratch artifacts → 0.

**Contract refs.** `agent-creation-guide.md` §"Script design" (`--output FILE`
pattern from CLAUDE.md m2a learning); `docbuilder/docs/milestones/
m-docbuilder-m2a-t10-implementation-notes.md` (context on m2a scratch).

**Touches.**
- `docbuilder/scripts/fetch_data.py` (update — add `--output FILE`)
- `docbuilder/agents/docbuilder_orchestrator.exs` (update — PHASE A uses
  `--output`, drop `write_file` for raw sources; strengthen "don't investigate")
- `docbuilder/tests/test_fetch_data.py` (add `--output FILE` test)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t3-implementation-notes.md` (new)

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# fetch_data --output FILE writes file, prints path
python3 scripts/fetch_data.py data/sample_data.csv --output /tmp/raw_test.json
cat /tmp/raw_test.json | python3 -m json.tool | head -5

# Tests pass
python3 -m pytest tests/test_fetch_data.py -v

# Sprint re-run (LLM) — verify scratch artifacts → 0
# Count files created during the run that are not in output/ or known paths
DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","date":"20 Jun 2026"}' \
./scripts/sprint.sh docbuilder

# After sprint: confirm no scratch files in docbuilder/ (exhaustive, location-based —
# more reliable than a -newer timestamp heuristic: list any .py outside known dirs)
find ../aetheris-agents/docbuilder -name "*.py" \
  ! -path "*/output/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/tests/*" \
  ! -path "*/scripts/*" \
  ! -path "*/agents/*" \
  ! -path "*/docs/*"
# Expected: empty — any output here is a scratch file the orchestrator created
```

**claude-code-prompt.**
> Read `CLAUDE.md` §"Learning — m2a-docbuilder" (the `--output FILE` pattern),
> `docbuilder/scripts/fetch_data.py`, `docbuilder/scripts/compute_doc.py`
> (the m2a `--output` implementation as the reference pattern), and
> `docbuilder/docs/milestones/m-docbuilder-m2a-t10-implementation-notes.md`
> §"Orchestrator scratch reduced 8→1" before writing any code.
>
> **`fetch_data.py --output FILE`:** add `--output` optional arg (default None).
> When provided: write the raw JSON to the file, print only the file path to
> stdout. When absent: print JSON to stdout as before. Backward-compatible.
>
> **Orchestrator PHASE A:** update each fetch step to use
> `--output output/pipeline_raw_{key}.json` and remove the `write_file` step
> that follows it. The PHASE A step count drops from 2N (N fetch + N write)
> to N (N fetch with `--output`).
>
> **Strengthen "don't investigate" rule:** add to the orchestrator Rules section:
> "Each `--output FILE` call writes its result directly to the file and prints
> only the path. Do NOT re-run the script without `--output` to inspect the
> content. Proceed to the next step using the file path printed."
>
> Add one test: `--output FILE` writes the file, stdout is the path, file
> contains valid JSON.
>
> Run the sprint and include the scratch-file check in the done-check output.
>
> **Review packet must open with the full done-check output block.**

---

### t4 — `rename_output.py`

**Scope.** New script `rename_output.py` — reads the output dir, finds the
generated files matching the current run's filename prefix, and renames them
to `{client_name_slug}_{doc_type}_{date}.{ext}` using fields from a context
JSON argument. Returns a JSON array of `{original, renamed}` pairs to stdout.
`client_name` is slugified (lowercase, spaces → underscores, non-alphanumeric
stripped). Exit 1 if required context fields are missing.

**Contract refs.** `docbuilder/docs/context-schema.md` (required fields:
`client_name`, `date`; `doc_type` from env or context); `agent-creation-guide.md`
§"Script design".

**Touches.**
- `docbuilder/scripts/rename_output.py` (new)
- `docbuilder/tests/test_rename_output.py` (new)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t4-implementation-notes.md` (new)

**Do not generate.** No Drive or email scripts in this ticket.

**Done-check.**
```bash
cd aetheris-agents/docbuilder

python3 -m pytest tests/test_rename_output.py -v

# Standalone: rename the current output files
python3 scripts/rename_output.py \
  --output-dir output \
  --filename-prefix proposal_v1 \
  --context '{"client_name":"Acme Corp","date":"2026-06-20","doc_type":"proposal"}' \
  | python3 -m json.tool

ls -lh output/acme_corp_*
```

**claude-code-prompt.**
> Read `docs/agent-creation-guide.md` §"Script design", `CLAUDE.md`,
> `docbuilder/docs/context-schema.md` before writing any code.
>
> Implement `rename_output.py`:
> - Args: `--output-dir` (default `output`), `--filename-prefix` (the current
>   generated filename prefix, e.g. `proposal_v1`), `--context` (inline JSON
>   of context fields).
> - Finds all files in `--output-dir` matching `{filename_prefix}.{ext}` for
>   known extensions (xlsx, docx, pdf, csv, json, xml, md).
> - Slugifies `client_name`: lowercase, spaces → underscores, strip non-
>   alphanumeric except underscores and hyphens.
> - Renames to `{slug}_{doc_type}_{date}.{ext}`. If `doc_type` absent from
>   context, use the `--filename-prefix` base (e.g. `proposal`).
> - Prints a JSON array of `[{"original": "...", "renamed": "..."}]` to stdout.
> - Exit 1 if `client_name` or `date` missing from context.
>
> Tests: correct slugification, rename produces expected filename, missing
> required field exits 1, files not matching prefix are untouched.
>
> **Review packet must open with the full done-check output block.**

---

### t5 — `upload_output.py`

**Scope.** New script `upload_output.py` — uploads a list of local files to
the `{tenant}/output/` subfolder of the `docbuilder` Shared Drive. Returns
a JSON array of `{filename, drive_file_id, drive_url}` objects. Uses the same
service account auth as `drive/scripts/drive_upload.py`.

**Contract refs.** `docbuilder/docs/drive-structure.md`; `agent-creation-guide.md`
§"Script design"; `drive/scripts/drive_upload.py` (auth pattern reference).

**Touches.**
- `docbuilder/scripts/upload_output.py` (new)
- `docbuilder/scripts/_drive.py` (update — add `find_or_create_folder` for the
  `{tenant}/output/` target; reuse `build_service` with the RW scope. From t2 review:
  add Drive plumbing here, not inline in `upload_output.py`.)
- `docbuilder/tests/test_upload_output.py` (new — integration tests only,
  marked `@pytest.mark.integration`, skipped when `DRIVE_DOCBUILDER_ID` absent)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t5-implementation-notes.md` (new)

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Unit tests (no Drive creds needed)
python3 -m pytest tests/test_upload_output.py -v -m "not integration"

# Full suite regression
python3 -m pytest tests/ --tb=short 2>&1 | tail -5
```

**claude-code-prompt.**
> Read `docs/agent-creation-guide.md` §"Script design", `CLAUDE.md`,
> `docbuilder/docs/drive-structure.md`, and
> `drive/scripts/drive_upload.py` (for the Drive API auth + upload pattern)
> before writing any code.
>
> Implement `upload_output.py`:
> - Args: `--tenant` (required), `--files` (one or more local file paths),
>   `--drive-id` (falls back to `DRIVE_DOCBUILDER_ID` env var).
> - Resolves the target Drive folder: `{tenant}/output/` under the Shared
>   Drive root. Creates it if it does not exist.
> - Uploads each file; returns JSON array of
>   `{"filename": ..., "drive_file_id": ..., "drive_url": ...}` to stdout.
> - Exit 1 if Drive ID absent or any upload fails.
> - Mark integration tests with `@pytest.mark.integration`; skip if
>   `DRIVE_DOCBUILDER_ID` not set.
>
> **Review packet must open with the full done-check output block.**

---

### t6 — `email_send_review.py`

**Scope.** New script `email_send_review.py` — sends a review email to
`DOCBUILDER_REVIEW_EMAIL` with subject `[REVIEW] {client_name} {doc_type} — {date}`,
body including the external `client_email` recipient and Drive links to the
uploaded files, and the output files as attachments (if under 10MB total;
otherwise Drive links only). Uses SMTP pattern from `email/scripts/email_send.py`.

**Contract refs.** `docbuilder/docs/context-schema.md` (required fields:
`client_name`, `client_email`, `date`); `agent-creation-guide.md` §"Script design";
`email/scripts/email_send.py` (SMTP pattern reference).

**Touches.**
- `docbuilder/scripts/email_send_review.py` (new)
- `docbuilder/tests/test_email_send_review.py` (new — integration tests marked,
  skipped without SMTP env vars)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t6-implementation-notes.md` (new)

**Done-check.**
```bash
cd aetheris-agents/docbuilder

# Unit tests (no SMTP needed)
python3 -m pytest tests/test_email_send_review.py -v -m "not integration"

# Full suite regression
python3 -m pytest tests/ --tb=short 2>&1 | tail -5
```

**claude-code-prompt.**
> Read `docs/agent-creation-guide.md` §"Script design", `CLAUDE.md`,
> `docbuilder/docs/context-schema.md`, and
> `email/scripts/email_send.py` (for the SMTP auth + send pattern)
> before writing any code.
>
> Implement `email_send_review.py`:
> - Args: `--context` (inline JSON), `--files` (local file paths, optional),
>   `--drive-links` (JSON array of `{filename, drive_url}`, optional).
> - Required context fields: `client_name`, `client_email`, `date`.
> - Reads `DOCBUILDER_REVIEW_EMAIL` (required), `SMTP_HOST`, `SMTP_PORT`,
>   `SMTP_USER`, `SMTP_PASSWORD` (same as `email_send.py`).
> - Subject: `[REVIEW] {client_name} {doc_type} — {date}`
>   (`doc_type` from context or `"document"` if absent).
> - Body: "Please review the attached document(s) for {client_name} and
>   forward to {client_email} if approved.\n\nDrive links:\n{links}"
> - Attaches files if provided and total size < 10MB; otherwise body
>   contains Drive links only.
> - Prints `{"status": "sent", "recipient": REVIEW_EMAIL}` to stdout.
>   Exit 1 on failure.
> - Mark integration tests; skip without SMTP env vars.
>
> **Review packet must open with the full done-check output block.**

---

### t7 — LLM selection agent + orchestrator full update

**Scope.** Wire everything together. The orchestrator gains a PHASE 0
(template selection) before the existing fetch/compute/render/deliver
phases. PHASE 0: call `list_templates.py` (Drive-backed), pass the
catalogue + `DOCBUILDER_CONTEXT` to the LLM, receive `{doc_type, variant,
rationale}`, call `fetch_template.py` to download the template bundle to
cache. Subsequent phases use the cache dir for `--base-file` and
`--template-dir`. After rendering: PHASE D (rename), PHASE E (upload),
PHASE F (email). `DOCBUILDER_DOC_TYPE` is now optional — if set, Option A
(LLM picks variant only); if absent, Option B (LLM picks doc_type +
variant). Update sprint case: verify rename + Drive upload + email.
Update runbook.

**Contract refs.** `agent-creation-guide.md` §"Agent file conventions",
§"Orchestrator patterns", §"Pre-flight checklist"; `CLAUDE.md`
(eval-time template resolution pattern from m2a learning; `--output FILE`
pattern); `docbuilder/docs/context-schema.md`;
`docbuilder/docs/drive-structure.md`.

**Touches.**
- `docbuilder/agents/docbuilder_orchestrator.exs` (full update)
- `docbuilder/runbook.md` (new env vars: `DRIVE_DOCBUILDER_ID`,
  `DOCBUILDER_REVIEW_EMAIL`, `GOOGLE_SERVICE_ACCOUNT_FILE`; new phases)
- `../aetheris/scripts/sprint.sh` (update docbuilder case — verify renamed
  outputs + Drive upload + email)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t7-implementation-notes.md` (new)

**Runbook update rule.** New env vars and operational phases in this ticket —
`runbook.md` update is part of this ticket's Touches, not deferred to t8.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

# Syntax check
DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"test@example.com","date":"20 Jun 2026"}' \
DRIVE_DOCBUILDER_ID=placeholder \
DOCBUILDER_REVIEW_EMAIL=review@internal.example.com \
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs")'

# Full sprint (LLM)
DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"test@example.com","date":"20 Jun 2026"}' \
DRIVE_DOCBUILDER_ID=${DRIVE_DOCBUILDER_ID} \
DOCBUILDER_REVIEW_EMAIL=${DOCBUILDER_REVIEW_EMAIL} \
GOOGLE_SERVICE_ACCOUNT_FILE=${GOOGLE_SERVICE_ACCOUNT_FILE} \
./scripts/sprint.sh docbuilder

# Verify renamed outputs
ls -lh ../aetheris-agents/docbuilder/output/acme_corp_*

# Verify no scratch files
find ../aetheris-agents/docbuilder -name "*.py" \
  ! -path "*/output/*" ! -path "*/__pycache__/*" \
  ! -path "*/tests/*" ! -path "*/scripts/*" \
  -newer ../aetheris-agents/docbuilder/scripts/fetch_data.py
# Expected: empty
```

**claude-code-prompt.**
> Read `docs/agent-creation-guide.md` (full), `CLAUDE.md` (all learning
> sections — especially eval-time resolution and `--output FILE`),
> `docbuilder/docs/context-schema.md`, `docbuilder/docs/drive-structure.md`,
> `docbuilder/docs/milestones/m-docbuilder-m2a-t8-implementation-notes.md`
> (eval-time pattern), and `docbuilder/runbook.md` before writing any code.
>
> Update `docbuilder_orchestrator.exs` for the full m2b pipeline:
>
> **Eval-time resolution (same pattern as m2a):** read `DOCBUILDER_CONTEXT`,
> `DRIVE_DOCBUILDER_ID`, `DOCBUILDER_REVIEW_EMAIL` at eval time. Determine
> Option A (doc_type in context) or Option B (no doc_type) and embed the
> concrete step list in the system prompt.
>
> **PHASE 0 — Template selection:**
> - Call `list_templates.py --tenant {tenant}` → catalogue JSON
> - Pass catalogue + context to LLM: "Given this context and catalogue,
>   select the best `{doc_type, variant}`. Return ONLY JSON:
>   `{\"doc_type\": \"...\", \"variant\": \"...\", \"rationale\": \"...\"}`"
> - Parse LLM response; call `fetch_template.py --tenant {tenant}
>   --doc-type {doc_type} --version {variant} --output
>   output/template_cache_path.txt` → get cache dir path
>
> **PHASE A–C** (fetch data, compute, render): same as m2a but use cache
> dir for `--base-file` and `--template-dir`. File prefix = `{doc_type}_{variant}`.
> The bundle's `{doc_type}_{version}.json` carries repo-root-relative
> `data_sources[].path` values (`docbuilder/data/...`). Per the t2 review, resolve
> them **Option (a):** strip the leading `docbuilder/` at eval time (the same
> source-path strip the m2a orchestrator already does) before issuing the fetch
> commands — do not rewrite the bundle JSON on disk.
>
> **PHASE D — Rename:**
> - Call `rename_output.py --output-dir output --filename-prefix {prefix}
>   --context '{context_json}' --output output/renamed.json`
>
> **PHASE E — Upload:**
> - Call `upload_output.py --tenant {tenant} --files {renamed files}
>   --output output/uploaded.json`
>
> **PHASE F — Email:**
> - Call `email_send_review.py --context '{context_json}'
>   --drive-links {uploaded.json contents}`
>
> **Rules additions:**
> - "Each `--output FILE` call writes directly to the file. Do not re-run
>   without `--output` to inspect. Use the file path and proceed."
> - "Template selection: parse the LLM JSON response exactly. Do not add
>   fields or reformat. If the response is not valid JSON, report the raw
>   response and stop."
>
> Update `runbook.md` with: `DRIVE_DOCBUILDER_ID`, `DOCBUILDER_REVIEW_EMAIL`,
> `GOOGLE_SERVICE_ACCOUNT_FILE` env vars; new PHASE 0 description; updated
> expected output (renamed files + Drive IDs in output/).
>
> `max_steps: 40` (PHASE 0 adds ~6 steps: list, LLM select, fetch template,
> plus existing 12 minimum from m2a).
>
> **Review packet must open with the full done-check output block.**
> Include: syntax check, sprint run output with all phases confirmed,
> `ls -lh output/acme_corp_*`, scratch-file check (empty).

---

### t8 — Docs sync + capability matrix update

**Scope.** Sync all docs to match what shipped in m2b. Regenerate capability
matrix (new scripts: `fetch_template.py`, `rename_output.py`, `upload_output.py`,
`email_send_review.py`). Update `docbuilder/README.md` m2b → done. Update
`rig/runbook.md` with m2b additions. Promote CLAUDE.md learning candidates
from t1–t7 reviews. Write milestone summary.

**Contract refs.** `milestone-methodology.md` §7; `aetheris-agents/CLAUDE.md`
§"Doc-sync DoD".

**Touches.**
- `docs/capability-matrix.md` (regenerate)
- `docbuilder/README.md` (m2b → done)
- `docbuilder/docs/m2b-milestone.md` (milestone summary at bottom)
- `docs/rig/runbook.md` (m2b additions: new env vars, Drive structure, LLM
  selection, delivery)
- `CLAUDE.md` (learning promotions from ≥2-ticket findings)
- `docbuilder/requirements.txt` (add `google-api-python-client`)
- `docbuilder/scripts/_drive.py` + `drive/scripts/*` (from t2 review F2: settle the
  canonical service-account env var on `GOOGLE_SERVICE_ACCOUNT_FILE` — the explicit m2b
  name — and align the legacy `drive/` scripts to it, not the other direction)
- `docbuilder/docs/milestones/m-docbuilder-m2b-t8-implementation-notes.md` (new)

> Capability matrix note: the regen must include the new m2b scripts
> (`fetch_template.py`, `rename_output.py`, `upload_output.py`, `email_send_review.py`)
> and list `_drive.py` as a shared helper (same row style as `_table_html.py`). The
> `capability_matrix_docbuilder.exs` `max_steps` may need another bump as the script
> count grows (it was raised to 30 at m2a t10).

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

mix aetheris run ../aetheris-agents/agents/capability_matrix.exs

grep -A 3 "fetch_template\|rename_output\|upload_output\|email_send_review" \
  ../aetheris-agents/docs/capability-matrix.md

cd ../aetheris-agents
python3 -m pytest docbuilder/tests/ --tb=short 2>&1 | tail -5
```

**claude-code-prompt.**
> Read `CLAUDE.md`, `docs/milestone-methodology.md` §7, and all m2b
> implementation notes (`m-docbuilder-m2b-t1-implementation-notes.md`
> through `m-docbuilder-m2b-t7-implementation-notes.md`) and review files
> before starting.
>
> Regenerate capability matrix, update README, write milestone summary,
> promote CLAUDE.md learning candidates (≥2-ticket recurrences).
>
> **Review packet must open with the full done-check output block.**

---

## Milestone summary

_(written by claude-code at milestone end, after t8)_
