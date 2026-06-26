# Implementation notes — m-docbuilder-m6 t2 (`generate_docx_from_html.py` — Pandoc wrapper)

Ticket: an HTML→DOCX converter shelling out to Pandoc, branded by a styles-only Bitloka
`reference.docx`. The DOCX half of the m6 Jinja2 path (`generate_html.py` → HTML →
this → branded `.docx`).

---

## What shipped

- **`scripts/generate_docx_from_html.py`**
  - `html_to_docx(html_path, output_path, reference_doc=None) -> None` — importable.
    Guards `shutil.which("pandoc") is None` → `FileNotFoundError`. Runs
    `pandoc --from html --to docx --reference-doc REF -o OUT IN`; non-zero exit →
    `RuntimeError` carrying pandoc's stderr. Default reference doc resolved relative to the
    script (`Path(__file__).parent.parent/…/bitloka/reference.docx`) so it is cwd-independent.
  - CLI: `--input`, `--output` (both required), `--reference-doc` (optional). Stage-CLI
    errors (`FileNotFoundError`/`RuntimeError`/`OSError`) → `{"status":"error",...}` on
    stderr, exit 1; on success prints the output path.

- **`data/templates/bitloka/reference.docx`** — styles-only reference doc, generated with
  `python-docx` (one-off; the generator is not a committed artifact, only the binary is):
  Normal = Calibri 11pt; Heading 1 = bold 16pt dark grey `#333333`; Heading 2 = bold 13pt
  Bitloka orange `#F5A623` (theme accent); `Table Grid` materialised via a placeholder 1×1
  table. **Pandoc reads only the styles from the reference doc and ignores its body**, so the
  placeholder table is never copied into output — the doc carries branding only.

- **`tests/test_generate_docx_from_html.py`** — 6 tests:
  - Pure-unit (no pandoc): pandoc-missing → `FileNotFoundError` (monkeypatch
    `shutil.which` → None); pandoc non-zero → `RuntimeError` with stderr (monkeypatch
    `subprocess.run` → fake `returncode=1`).
  - Real conversion + CLI, marked `@pytest.mark.integration` + `skipif(not pandoc)`:
    `html_to_docx` produces a non-empty `.docx`; explicit `--reference-doc`; CLI creates the
    output + prints its path; bad `--input` → exit 1.

## Done-check

- `tests/test_generate_docx_from_html.py`: **6 passed** (pandoc 2.9.2.1 present → integration
  tests ran, not skipped).
- Full docbuilder suite: **353 passed, 3 skipped** (was 347/3 at t1 — +6; the 3 skips are the
  pre-existing wkhtmltopdf integration tests, unrelated).
- Smoke (verbatim from §t2): `--input /tmp/test.html --output /tmp/test.docx` → printed the
  output path; `/tmp/test.docx` exists at 22K.

## Notes / decisions

- **Reference doc body is intentionally non-empty (a 1×1 Table Grid table).** Pandoc ignores
  the reference doc's body content (uses styles only), so this is harmless and is the simplest
  way to materialise the `Table Grid` style into `styles.xml`. The "no content pages" intent
  is honoured in effect — nothing from the reference body reaches the output.
- **Error-path tests use monkeypatch, not a real broken pandoc**, so they are deterministic
  and pandoc-independent (they run even where pandoc is absent). Only the real-conversion
  tests are gated on pandoc.
- Scope held: no bundle asset or catalogue changed (t3/t4 wire this into the pipeline).
  `reference.docx` is a committed binary.

## Reproducing `reference.docx` (t2 review F2)

The reference doc is a committed binary; this is the python-docx recipe used to generate it,
so it is reproducible from the repo without the original throwaway script. Run from
`docbuilder/`:

```python
from docx import Document
from docx.shared import Pt, RGBColor

BITLOKA_ORANGE = RGBColor(0xF5, 0xA6, 0x23)
DARK_GREY = RGBColor(0x33, 0x33, 0x33)

doc = Document()
n = doc.styles["Normal"];   n.font.name = "Calibri"; n.font.size = Pt(11)
h1 = doc.styles["Heading 1"]; h1.font.name = "Calibri"; h1.font.bold = True
h1.font.size = Pt(16); h1.font.color.rgb = DARK_GREY
h2 = doc.styles["Heading 2"]; h2.font.name = "Calibri"; h2.font.bold = True
h2.font.size = Pt(13); h2.font.color.rgb = BITLOKA_ORANGE   # accent on H2 (not H1)
doc.add_table(rows=1, cols=1).style = "Table Grid"          # materialise Table Grid
doc.save("data/templates/bitloka/reference.docx")
```

Pandoc reads only these styles and ignores the body, so the placeholder table never appears
in output. Regenerate when branding/styles change; the `docbuilder_invoice_jinja` and
`docbuilder_offer_letter` sprints (t5) are the regression guard for the rendered result.
