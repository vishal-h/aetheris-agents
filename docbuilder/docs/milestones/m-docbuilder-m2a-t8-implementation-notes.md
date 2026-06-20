# Implementation notes — m-docbuilder-m2a t8

Ticket: orchestrator + sprint case update (m2a features end-to-end).

---

## What shipped

- `docbuilder_orchestrator.exs`: rebuilt to drive the m2a pipeline — multi-source
  fetch, base-file rendering (xlsx/docx), and narrative-mode PDF — by resolving the
  template at eval time and emitting a concrete, enumerated set of commands.
- `../aetheris/scripts/sprint.sh`: docbuilder case now passes `DOCBUILDER_CONTEXT`
  (with a demo default) and verifies all three branded outputs (xlsx, docx, pdf).
- `runbook.md`: `DOCBUILDER_CONTEXT`, multi-source, base-file/narrative sections;
  updated expected-output listing.

**Verified:** manual command-plan end-to-end produces all three branded outputs;
the LLM sprint (run `docbuilder-orch-3qwZ9g`, status `done`) fetched both sources,
computed, and rendered `proposal_v1.{xlsx,docx,pdf}` (6.3K / 38K / 18K).

---

## Decisions

**Template resolved at eval time; LLM does pure orchestration.**
The `.exs` reads the template JSON (`Jason.decode!`) and checks base-file existence
(`File.exists?`) at eval time, then builds a fully concrete, enumerated system prompt
(which sources to fetch, which formats to render, which renderers get `--base-file` /
`--template-dir`). This is the "pre-establish at prompt-write time" pattern (same spirit
as orb run IDs): the LLM never parses JSON or derives paths — it executes the listed
`run_command`/`write_file` calls and reports. Keeps "scripts do, agents decide" intact.

**Multi-source fetch.** One `fetch_data.py --key {key} {path}` per `data_sources`
entry → `output/pipeline_raw_{key}.json`; then a single `compute_doc.py {template}
raw_main raw_summary …`. The intermediate filename changed from `pipeline_raw.json`
to per-source `pipeline_raw_{key}.json` (runbook updated).

**Source path resolution.** Template `data_sources[].path` is repo-root-relative
(`docbuilder/data/…`, per template-schema.md), but `run_command` runs from the
docbuilder sandbox, so the orchestrator strips a leading `docbuilder/` to make it
sandbox-relative. The `main` source uses `DOCBUILDER_DATA_PATH` (preserves the env
contract / lets the caller repoint the primary data). *Limitation:* a source outside
`docbuilder/` wouldn't resolve via this strip — acceptable for m2a (all demo data is
under `docbuilder/data/`); m2b's Drive fetch handles remote sources differently.

**Declared-but-unconsumed source fetched anyway.** Per the t4 decision, the demo's
`summary` source is fetched and passed to `compute_doc.py` even though the Summary
sheet derives from `summary_rows`. The orchestrator prompt explicitly says "fetch every
source listed … do not skip any" so the LLM doesn't optimise it away.

**`DOCBUILDER_CONTEXT` default.** Resolved to `"{}"` when unset/empty
(`System.get_env(...) || "{}"`, `"" -> "{}"`), so `generate_pdf.py`/`render_template.py`
never receive an empty `--context` (which would fail `json.loads("")`). The sprint case
applies the same default with a demo context. In the prompt, the context value is shown
as a `"<CONTEXT>"` placeholder element in the args array with the literal JSON given
below it, so the LLM substitutes it verbatim without escaping confusion.

**`max_steps` 20 → 30.** Two sources + three formats ≈ 9 tool calls (2 fetch + 2 write
+ 1 compute + 1 write + 3 render) plus reasoning steps; 30 gives headroom.

---

## Forward notes

- **t9 (catalogue / `list_templates.py`):** independent of the orchestrator; not wired
  into it in m2a (m2b uses it for LLM selection).
- **t10 (docs sync):** capability matrix regenerate (new scripts `render_template.py`,
  `list_templates.py`); `requirements.txt` (pinned) and `_table_html.py` shared helper
  are already in the t10 Touches; `rig--runbook.md` m2a additions
  (`DOCBUILDER_CONTEXT`, multi-source, narrative PDF).
