# docbuilder — Milestone Summary

---

## m1 — Core doc builder

_Written at milestone end (t8)._

---

### What shipped

| Ticket | Artifact | Notes |
|--------|----------|-------|
| t1 | Template schema, `demo/proposal_v1.json`, `sample_data.csv` | Two-sheet B2B proposal fixture with merge ranges, aggregate rows, multi-format output |
| t2 | `fetch_data.py`, `compute_doc.py` | Two-pass engine (data-bearing sheets → summary sheets); doc spec JSON contract |
| t3 | `generate_xlsx.py` | openpyxl; merged cells, column widths, numeric formatting, aggregate border |
| t4 | `generate_docx.py` | python-docx; tables, alignment, bold; merge_ranges represented as sheet headings |
| t5 | `generate_pdf.py` | weasyprint; HTML intermediate; `_build_html()` pure function; merge_ranges as `<th colspan>` |
| t6 | `generate_csv.py`, `generate_json.py`, `generate_xml.py`, `generate_md.py` | stdlib only; 44 tests |
| t7 | `docbuilder_orchestrator.exs`, `runbook.md`, sprint case | Linear pipeline; `--input FILE` added to all renderers |
| t8 | Capability matrix, docs sync, learning promotions | This file |

**Test count at milestone close:** 123 tests, all passing.

**Output formats proven end-to-end:** xlsx, pdf (via `output_formats` in demo template). csv, json, xml, md available and unit-tested.

---

### What was deferred

| Item | Target |
|------|--------|
| Template registry (fetch_template.py, tenant onboarding) | → m2 |
| Drive upload / email delivery integration | → m2 |
| Multi-source data fetch and join (template `data_sources` length > 1) | → m2 |
| Derived/formula columns in templates | → m2+ |
| Conversational template editing (patch schema, JSONL edit log) | → m3 |
| Real tenant data (sample data only in m1) | operational constraint, not deferred |
| reportlab PDF renderer | → backlog (single-script swap when needed) |

The template schema is forward-compatible with multi-source (`data_sources` is an array from day one); m1 validates that the array has exactly one entry.

---

### Surprises and recurring findings

#### 1. `run_command` has no stdin parameter — renderers need `--input FILE`

Discovered at t7 when the orchestrator tried to pipe the doc spec to `generate_xlsx.py` via stdin. `run_command` schema has no `stdin` parameter. The first attempt used `sh -c "cat spec.json | python3 scripts/generate_xlsx.py ..."` — the LLM did not follow this reliably and the script timed out.

**Fix:** added `--input FILE` (optional, falls back to stdin) to all 7 generate scripts. This is now a standing pattern.

**Learning promoted:** see `agent-creation-guide.md` §"Common failure modes" and `CLAUDE.md` §"Learning — m1-docbuilder".

#### 2. merge_ranges diverge significantly across renderers

| Renderer | merge_ranges handling |
|----------|-----------------------|
| xlsx | Merged cells via `worksheet.merge_cells` — value preserved |
| pdf | `<th colspan="N">` — value preserved |
| docx | Silently substituted with sheet name heading — value **lost** |
| csv, json, xml, md | Silently dropped — value **lost** |

Template authors who rely on merge_range values appearing faithfully in docx output will be surprised. Documented in t4 and t6 implementation notes. Added to `doc-spec-schema.md` §"Format characteristics".

#### 3. `_build_html()` pure function pattern worth propagating

Separating the HTML builder from the `weasyprint` call (t5) gave 8 fast unit tests with zero PDF rendering overhead. The integration tests (5 tests) cover weasyprint specifically. Useful wherever a renderer has a testable intermediate representation.

#### 4. max_steps sizing for a linear pipeline

The docbuilder pipeline consumes approximately: 4 setup tool calls (fetch, write_raw, compute, write_spec) + 1 LLM parse step + N render calls + 1 LLM per step = ~12 steps minimum for 2 formats. Set `max_steps: 20` with 8 steps of headroom. The first run hit the initial 15-step limit before completing.

#### 5. Review packet done-check completeness (raised t4 → t6)

The pipeline file listing (`ls -lh output/proposal.{fmt}`) was missing from packets at t5 and t6. The t4 packet was returned unreviewed. Resolution: milestone doc was updated to require "Review packet must open with the full done-check output block." This applies to all future use-case tickets.

---

### Open items for m2

- `fetch_template.py` — resolves template from registry by `(tenant, doc_type, version)`
- Multi-source joins in `compute_doc.py` (schema already supports it; m1 rejects arrays > 1)
- Non-convertible numeric string cells in xlsx renderer should emit a stderr warning instead of silently rendering as text
- `generate_json.py` drops row `type` field — m2 consumers may want `header`/`data`/`aggregate` metadata
- `--input` file handles should use `with` block (F1 from t7 review) — harmless for m1 short-lived scripts, revisit if scripts become longer-lived
- Sprint case `run_id` extraction now fixed but the underlying `no-json` label in sprint output is cosmetic noise — trace to the log line prefix in run.json format
