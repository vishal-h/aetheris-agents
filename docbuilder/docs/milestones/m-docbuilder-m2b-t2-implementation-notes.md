# Implementation notes — m-docbuilder-m2b t2

Ticket: `fetch_template.py` (new) + `list_templates.py` Drive fallback.

---

## What shipped

- `scripts/fetch_template.py` (new): `--tenant`/`--doc-type`/`--version`,
  `--cache-dir` (default `output/template_cache`), `--templates-dir`, `--drive-id`
  (falls back to `DRIVE_DOCBUILDER_ID`), `--output FILE`. Drive id present → wide-fetch
  the `{tenant}/templates/{doc_type}/{version}/` subfolder into the cache; absent →
  local nested bundle `data/templates/{tenant}/{doc_type}/{version}/`. Prints the
  resolved path (or writes it to `--output`). Exit 1 if neither resolves.
- `scripts/list_templates.py` (update): `resolve_catalogue()` — Drive-backed when
  `DRIVE_DOCBUILDER_ID`/`--drive-id` is set, flat local file otherwise. `load_catalogue`
  (flat) unchanged so existing tests pass.
- `scripts/_drive.py` (new helper — see decision below): auth + folder navigation +
  download.
- `data/templates/demo/proposal/v1/` (new nested demo bundle — Option A): copies of the
  flat `proposal_v1.*` files for the local-fallback path.
- Tests: +2 list_templates (Drive routing), +5 fetch_template (1 integration, skipped).
- Full suite: 175 passed, 1 skipped (was 168).

---

## Decisions

**`scripts/_drive.py` shared helper (addition beyond the listed Touches).** Both
`fetch_template.py` and the updated `list_templates.py` need the same Drive plumbing
(service-account auth, Shared-Drive-flagged folder navigation, file download), and
`upload_output.py` (t5) will too. Rather than duplicate it or import across scripts, I
added `_drive.py` — the same precedent as `_table_html.py` (m2a t10). Pattern replicated
from `drive/scripts/drive_download.py` (not imported, per the contract ref). The google
imports are lazy (inside functions), so importing `_drive`/`fetch_template`/`list_templates`
for unit tests does **not** require `googleapiclient` — only actual Drive calls do.

**Service-account env var: `GOOGLE_SERVICE_ACCOUNT_FILE` with `GOOGLE_SERVICE_ACCOUNT`
fallback.** The m2b docs (drive-structure.md, README) name it `GOOGLE_SERVICE_ACCOUNT_FILE`;
the existing `drive/` scripts use `GOOGLE_SERVICE_ACCOUNT`. `_drive.service_account_key_path()`
reads the m2b name first, falls back to the legacy name. **t8 should pick one canonical
name** and align the docs/scripts (flagged).

**Local fallback = nested bundle (Option A, from t1 review).** `fetch_template.py`'s
local fallback resolves `data/templates/{tenant}/{doc_type}/{version}/`. The committed
nested demo bundle (`data/templates/demo/proposal/v1/`) is copies of the flat files; the
flat files remain untouched (the m2a orchestrator still uses them directly via
`template_rel`). Clean separation: flat = m2a direct path, nested = m2b fetch_template
local fallback. The nested bundle's `proposal_v1.json` is a verbatim copy — its
`data_sources` paths are still repo-root-relative (a t7 concern when the orchestrator
consumes the cache dir).

**`--output FILE` on fetch_template too.** Consistent with the m2a `--output` pattern so
the t7 orchestrator can capture the cache-dir path without round-tripping it through
`write_file`.

## Testing without Drive creds

- fetch_template: local-fallback path fully tested via subprocess with
  `DRIVE_DOCBUILDER_ID` removed from the env (so a set shell var can't divert the test);
  the Drive path is `@pytest.mark.integration` and skips without `DRIVE_DOCBUILDER_ID`.
- list_templates: the Drive branch is unit-tested by monkeypatching
  `load_catalogue_drive` (asserts routing + args) — no creds/network.

## Forward notes

- **t5 (`upload_output.py`):** reuse `_drive.build_service` (RW scope) +
  `find_child`/`resolve_folder`; it creates `{tenant}/output/` if absent (add a
  `find_or_create_folder` to `_drive.py` then).
- **t7 (orchestrator):** PHASE 0 calls `list_templates.py` then `fetch_template.py
  --output ...`; subsequent phases point `--base-file`/`--template-dir` at the returned
  cache/bundle dir.
- **t8:** add `google-api-python-client` to `requirements.txt`; reconcile the
  `GOOGLE_SERVICE_ACCOUNT_FILE` vs `GOOGLE_SERVICE_ACCOUNT` env-var name.
