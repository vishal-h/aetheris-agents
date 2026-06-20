# Implementation notes — m-docbuilder-m2a t10

Ticket: docs sync + capability matrix + milestone close (with three carried cleanups).

---

## What shipped

- **Capability matrix regenerated** — `docs/.sections/docbuilder.md` + `docs/capability-matrix.md`
  (docbuilder now 1 agent / 12 scripts; total 24 agents / 50 scripts).
- **`requirements.txt`** (new) — pinned renderer deps (`openpyxl==3.1.5`,
  `python-docx==1.2.0`, `weasyprint==69.0`, `markdown==3.10.2`).
- **`scripts/_table_html.py`** (new) — shared `esc()` + `render_table()`; `generate_pdf.py`
  and `render_template.py` now import it (table markup deduped).
- **`compute_doc.py --output FILE`** — writes the doc spec to the file, prints only the
  path (stdout default preserved). Orchestrator uses it (drops the spec `write_file`).
- **`docbuilder_orchestrator.exs`** — PHASE B computes straight to
  `output/pipeline_spec.json` via `--output`; no large-blob `write_file`.
- **Docs:** README m2a → *done*; `rig/runbook.md` m2a additions (`DOCBUILDER_CONTEXT`,
  multi-source, base files, narrative PDF, updated expected output); `runbook.md`
  stale-intermediates reference updated to `pipeline_raw_*.json`; CLAUDE.md m2a learning
  section; milestone summary.
- Full suite: 168 passed.

---

## Decisions / notes

**Capability matrix generator `max_steps` bumped 15 → 30.** The first regen run produced a
stale 9-script section: with the script count grown to 12, Step 4 (read each script)
exceeded `max_steps: 15` (≈16 tool calls), and the agent wrote a partial/stale list.
Bumped `capability_matrix_docbuilder.exs` to `max_steps: 30`; the re-run correctly listed
all 12 scripts (incl. `render_template.py`, `list_templates.py`, `_table_html.py`).
Regenerated via the two real agents (`capability_matrix_docbuilder.exs` then
`capability_matrix_assemble.exs`) — only docbuilder changed, so the full 8-agent
`sprint.sh capability_matrix` was unnecessary. (The milestone done-check references a
non-existent monolithic `agents/capability_matrix.exs`; the actual mechanism is
per-use-case sub-agents + assemble, as established at m1 t8.)

**`_table_html.py` import works run-as-script and under pytest.** Run as
`python3 scripts/generate_pdf.py`, `scripts/` is `sys.path[0]`, so `from _table_html import …`
resolves; under pytest, `conftest.py` inserts `scripts/`. Pure stdlib (`html`), so it adds
no dependency and keeps `render_template.py` weasyprint-free. `_build_html` now = shared
`render_table` + a per-sheet `<h2>` heading; the HTML unit tests pass unchanged (identical
markup).

**`compute_doc.py --output` is backward-compatible.** Absent → stdout (all existing tests
and the renderer pipelines that pipe `compute_doc | generate_*` keep working). The
orchestrator opts in. Re-ran the sprint (run `docbuilder-orch-8x3XkQ`): the simplified
PHASE B produced `proposal_v1.{xlsx,docx,pdf}` correctly via the `--output` spec file.

**Orchestrator scratch reduced 8 → 1, not 0.** t8 left 8 `/tmp` scratch scripts; this run
left 1 (`capture_output.py`, removed). The residual ran `compute_doc.py` **bare** (no
`--output`) to capture/print the spec — i.e. the agent ran compute a second time purely to
*inspect* the output, despite the "do not investigate manually" rule. It is not a
functional failure: the `--output` spec file and all three branded outputs were produced
correctly. The `--output` flag fixed the large-blob `write_file` round-trip (the t8 root
cause); the remaining behaviour is over-eager inspection. **m2b follow-up:** strengthen the
orchestrator rule ("the `--output` file is the spec; do not re-run compute to view it")
and/or give `fetch_data.py` an `--output FILE` flag too so PHASE A drops its `write_file`
as well — then re-verify. Left as-is here (commit = the verified run); not re-hardened
post-verification.

**CLAUDE.md promotions (≥2-ticket recurrences):** large-stdout `write_file` → `--output FILE`
(t6/t7, t8/t9/t10); two-step optional-field rollout (t2, t3, t5); base-file asset gap
(t1–t3); verify a carried finding is actually open before re-flagging (t5, t7).

---

## Milestone close

m2a is complete (t1–t10). The milestone summary (what shipped / deferred / surprises /
open items for m2b) is at the bottom of `m2a-milestone.md`. Deferred to m2b: LLM template
selection, Drive registry + delivery; to m3: NL requests + conversational editing.
