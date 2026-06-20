# Implementation notes — m-docbuilder-m2a t9

Ticket: template catalogue + `list_templates.py`.

---

## What shipped

- `data/templates/demo/catalogue.json` (new): the demo tenant's catalogue — one
  doc type (`proposal`) with one variant (`v1`) declaring `output_formats`,
  `has_base_files`, and `has_narrative`. Matches the structure in the t9 prompt and
  README §"Template model".
- `scripts/list_templates.py` (new): `--tenant TENANT_ID` + optional
  `--templates-dir PATH` (default `data/templates`). Reads
  `{templates_dir}/{tenant_id}/catalogue.json`, prints it (indent=2) to stdout.
  Exit 1 (JSON error on stderr, matching `fetch_data.py`) if the catalogue is missing.
- `tests/test_list_templates.py` (new): 7 tests.
- `data/.gitignore`: `!templates/demo/catalogue.json` whitelist line.
- Full suite: 167 passed (was 160; +7).

---

## Decisions

**Standalone in m2a — not wired into the orchestrator.** Per the ticket scope,
`list_templates.py` is implemented and tested but not called by
`docbuilder_orchestrator.exs`. It is the foundation for LLM template selection in
m2b (the orchestrator will call it, pass the catalogue + context to the LLM, and the
LLM picks `{doc_type, variant}`).

**`load_catalogue()` factored for direct testing.** The path resolution + read is a
module-level function so unit tests import it (`from list_templates import
load_catalogue`) and assert on the dict directly, while CLI tests exercise the
argparse/exit-code path via subprocess. Same split as the other renderer tests.

**Missing catalogue → `FileNotFoundError` → exit 1.** Both "tenant directory absent"
and "directory present but no catalogue.json" surface as `FileNotFoundError` (the
`path.exists()` check), reported as `{"status":"error",...}` on stderr with exit 1 —
consistent with `fetch_data.py`'s error convention.

**gitignore whitelist.** `catalogue.json` was already un-ignored by the existing
`!templates/demo/` rule (verified with `git check-ignore`), but the explicit
`!templates/demo/catalogue.json` line is added for intent/consistency with the other
committed demo files (base files, md.template, css).

---

## Forward notes

- **m2b:** the orchestrator calls `list_templates.py --tenant {tenant}` to get the
  catalogue, then the LLM selects `{doc_type, variant, rationale}` from it (Options A/B).
  When the registry moves to Drive (m2b), `list_templates.py` reads from Drive rather
  than the flat `catalogue.json` (its `--templates-dir`/loader is the seam for that).
- **t10:** `list_templates.py` is a new script → include it in the capability-matrix
  regeneration (alongside `render_template.py`). No catalogue/scripts changes expected
  at t10 beyond the docs sync + the already-listed `requirements.txt` / `_table_html.py`.
