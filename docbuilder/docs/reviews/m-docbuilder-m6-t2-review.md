# Review — m-docbuilder-m6 t2 — round 1

Reviewer: claude-ui
Subject: `generate_docx_from_html.py` + `reference.docx` (commit `877d521`)

---

## Findings

1. [non-blocking] The reference.docx has Bitloka orange (`#F5A623`) on Heading 2,
   not Heading 1. The milestone doc specifies "Heading 1: bold 16pt dark grey
   `#333333`" — the done-check output confirms Heading 2 colour is `F5A623`, which
   matches the implementation notes ("Heading 2 bold 13pt Bitloka orange"). This is
   internally consistent and acceptable — Pandoc uses these styles in the output DOCX,
   so Heading 1 will be dark grey and Heading 2 will be orange. Noting for the record;
   no action required.

2. [non-blocking] The reference.docx generator script is not committed — only the
   binary is. The implementation notes acknowledge this: "the generator is not a
   committed artifact, only the binary is." If the reference doc ever needs to be
   regenerated (new branding, additional styles), the generator is not recoverable
   from the repo. Consider adding a brief `data/templates/bitloka/README.md` or an
   inline comment in the implementation notes with the key python-docx calls used to
   produce `reference.docx` so it can be reproduced. Low priority — carry to t6 docs
   sync if desired.

3. [non-blocking] The integration tests are correctly gated on pandoc availability
   (`@needs_pandoc` + `@pytest.mark.integration`). The error-path tests use
   monkeypatch and run without pandoc. This is the correct pattern — consistent with
   the wkhtmltopdf integration test convention in the docbuilder suite. No action
   required.

## Cross-ticket notes

- t3 (invoice Jinja2 migration) wires `generate_html.py` into `generate_pdf.py` for
  the PDF path. t4 (offer letter) wires both `generate_html.py` and
  `generate_docx_from_html.py` for the DOCX path. Both depend on the `DEFAULT_REFERENCE_DOC`
  path resolution being cwd-independent — confirmed correct (resolved relative to
  `__file__`).
- F2 (generator script) is a t6 docs item if desired — low priority.

Clean. 6 tests pass, 353/3 suite, smoke confirms a 22K DOCX, reference.docx styles verified
with Bitloka orange on Heading 2.

---

## Disposition

**t2 clear to merge as-is.** All three findings non-blocking; no code change to the script.
**F2 addressed now** (not deferred): the python-docx generator recipe for `reference.docx` is
appended to the t2 implementation notes, so the binary is reproducible from the repo. F1
(orange on Heading 2) and F3 (integration gating) are informational. Code unchanged from
`877d521`.
