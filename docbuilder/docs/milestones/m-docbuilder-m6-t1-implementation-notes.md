# Implementation notes — m-docbuilder-m6 t1 (`generate_html.py` — Jinja2 renderer)

Ticket: a new Jinja2 `.html.j2` renderer (`render_html` + CLI) that supersedes
`render_template.py` (Markdown+regex) for new doc types. Absent variables render as the
empty string natively — no `OPTIONAL_FIELDS` workaround.

---

## Dependency (Pre-flight blocker resolved)

Per the milestone §"Pre-flight verification", **jinja2 was not installed** and not in
`docbuilder/requirements.txt`. Resolved as the first step:
- Added `jinja2==3.1.6  # generate_html.py (Jinja2 narrative renderer, m6)` to
  `docbuilder/requirements.txt` (and annotated the `markdown` line as deprecated m6).
- Installed: `python3 -m pip install jinja2==3.1.6` → `jinja2-3.1.6` (+ `MarkupSafe-3.0.3`).
- Confirmed importable: `python3 -c "import jinja2; print(jinja2.__version__)"` → `3.1.6`.

## What shipped

- **`scripts/generate_html.py`**
  - `render_html(template_path, context, spec=None) -> str` — importable pure function.
    `jinja2.Environment(loader=FileSystemLoader(template_dir), undefined=jinja2.Undefined,
    autoescape=select_autoescape([...]))`. Renders `template.render(**context, spec=spec)`.
    With the default `Undefined`, an absent `{{ var }}` renders as `""` and `{% if var %}`
    is falsy — so a template never leaks a literal `{{ placeholder }}`.
  - **Autoescaping is ON** for html/htm/j2 — this is a deliberate upgrade over
    `render_template.py` (the design table cites "proper escaping" as a Jinja2 benefit);
    values containing markup are escaped, not injected.
  - `spec` (parsed `--spec` JSON, or `None`) is exposed to the template as the `spec`
    variable for `{% for s in spec.sheets %}`-style access.
  - CLI: `--template` (required), `--context` (inline JSON, default `{}`), `--spec`
    (optional JSON file path), `--output` (optional; default stdout — when given, writes the
    file and prints the path). Stage-CLI errors: `jinja2.TemplateNotFound` /
    `TemplateSyntaxError` and `json.JSONDecodeError` / `OSError` → `{"status":"error",
    "error":"..."}` on stderr, exit 1.

- **`tests/test_generate_html.py`** — 15 tests: `render_html` (present var; absent → `""`;
  `default()` filter; `{% if %}` present/absent; `{% for %}`; `spec` exposed; autoescape;
  `TemplateNotFound`; `TemplateSyntaxError`) + CLI (stdout; absent→empty; `--output` writes
  file + prints path; `--spec`; missing template → exit 1; bad context JSON → exit 1).
  `pytest.importorskip("jinja2")` guards collection.

## Done-check

- `tests/test_generate_html.py`: **15 passed**.
- Full docbuilder suite: **347 passed, 3 skipped** (was 332/3 at m5 close — +15 new).
- Smoke (verbatim from §t1): `--context '{"name":"World"}'` → `<p>Hello World</p>`;
  `--context '{}'` → `<p>Hello </p>` (absent var → empty, exit 0, no error). Both match
  the expected output exactly.

## Notes

- Scope held: `render_template.py`, `generate_pdf.py`, and all bundle assets untouched (t3
  wires the `has_jinja` branch into `generate_pdf.py`).
- `requirements.txt` is the only non-listed Touches item beyond the script/tests/notes — it
  was pre-authorised in the t1 Touches (the Pre-flight blocker).
