# Implementation notes — m-docbuilder-m2a t7

Ticket: `generate_pdf.py` narrative mode.

---

## What shipped

- `generate_pdf.py`: narrative mode. When the doc spec has a `narrative` block AND
  `--template-dir` is supplied, HTML is produced by `render_template.py` (Markdown +
  CSS) and passed to weasyprint. Otherwise structured mode (`_build_html`, m1
  behaviour, unchanged). `narrative` present but no `--template-dir` → stderr warning
  + structured fallback (no error).
- New CLI args: `--template-dir PATH`, `--context JSON` (default `"{}"`).
- `generate_pdf()` signature extended to `(doc_spec, output_path, template_dir=None,
  context=None)` — the existing 2-arg unit-test calls still work.
- Tests: +4 (structured no-warning, narrative-without-template-dir fallback,
  narrative direct, CLI narrative).
- Full suite: 160 passed (was 156).

---

## Decisions

**render_template.py invoked as a subprocess; doc spec via temp file + `--spec`.**
Per the milestone prompt (and the t6-review F4 clarification), `render_template.py`
takes `--spec PATH`/`--spec -`, not `--input`. `_narrative_html()` writes the doc spec
to a `tempfile.mkstemp(suffix=".json")` file, passes `--spec <temp>`, captures stdout,
and unlinks the temp file in a `finally`. This keeps the single-responsibility boundary
(no inlining of render_template logic) and matches the m1 write-to-temp orchestrator
pattern.

**render_template path resolved from `__file__`.** `_RENDER_TEMPLATE = Path(__file__).
parent / "render_template.py"` so the subprocess target is found regardless of the
caller's cwd. The subprocess otherwise inherits the parent cwd, so a relative
`--template-dir` (e.g. `data/templates/demo`) resolves against the run directory as the
CLI/orchestrator expects. The temp spec path is absolute.

**`--template`/`--css` resolved from the narrative block under `--template-dir`.**
`template_dir / narrative["template_file"]` and `… / narrative["css_file"]`. For the
demo that is `data/templates/demo/proposal_v1.md.template` and `proposal_v1.css`.

**Subprocess failure surfaces as exit 1.** If `render_template.py` returns non-zero,
`_narrative_html()` raises `RuntimeError(... stderr ...)`, caught by `main()` and
reported as a `{"status":"error"}` line with exit 1.

---

## Existing CLI tests now exercise the fallback path

The demo doc spec now carries `narrative` (t5 pass-through), so the pre-existing PDF CLI
tests (`test_cli_produces_file`, `test_cli_prints_output_path`, `test_cli_pdf_magic_bytes`)
— which call `generate_pdf.py` **without** `--template-dir` — now hit the
"narrative present, no template-dir → structured fallback + warning" path. They still
produce valid PDFs (returncode 0, `%PDF` magic bytes); the warning goes to stderr only and
none of them assert empty stderr, so all pass. This is the intended graceful-degradation
behaviour.

## Verified narrative path is genuinely engaged

The narrative HTML fed to weasyprint contains the template prose (`Terms & Conditions`,
`Net 30`), the substituted `client_name` (`Acme Corp`), and the rendered `<table>` — i.e.
it is the render_template output, not the structured `_build_html`. The narrative PDF is
~19K vs ~12K structured.

---

## Forward notes

- **t8 (orchestrator):** pass `--template-dir data/templates/{tenant}` and
  `--context "$DOCBUILDER_CONTEXT"` to `generate_pdf.py`. The renderer resolves the
  `.md.template`/`.css` filenames from the doc spec's `narrative` block, so the
  orchestrator only supplies the directory and the context JSON.
- **t10 (`_table_html.py`):** `_build_html` (structured) and
  `render_template._render_table` (narrative) still share table markup. The t10 shared
  helper (already in the t10 Touches) should dedupe both. No behaviour change intended.
