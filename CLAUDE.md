# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repo is

A collection of use-case agent implementations built on top of the **Aetheris** harness (sibling repo at `../aetheris`). Each use case is a self-contained directory with Python scripts, Elixir agent files, tests, and docs. No Elixir source lives here — only `.exs` agent scripts that the harness evaluates.

The two repos work together:
- `aetheris/` — the harness (`mix aetheris run`, `mix aetheris inspect`, etc.)
- `aetheris-agents/` — this repo; use-case scripts and agent files

All sprint and agent commands are run from `~/sandbox/elixirws/aetheris/`, not from this repo.

**Repos rule (claude-code sessions).** Sessions run with this repo
(`aetheris-agents/`) as the working directory; the harness is the sibling
`../aetheris/`. Paths in tickets and docs are relative to `aetheris-agents/`
unless prefixed with `../aetheris/`. Edits default to this repo; touching the
harness is explicit and called out in the ticket's `Touches` list.
**Cross-repo milestone sessions read *both* repos' CLAUDE.md learning sections at
session start** — promoted rules live in one repo only and are not otherwise
reachable from the other.

---

## Commands

**Run tests for a use case:**
```bash
# From the aetheris-agents/ root
python3 -m pytest payslip/tests/ -v
python3 -m pytest api/tenant/tests/ api/gateway/tests/ -v

# Single test file
python3 -m pytest payslip/tests/test_payslip_compute.py -v

# Single test
python3 -m pytest payslip/tests/test_payslip_compute.py::test_net_salary -v
```

> `python3` here is the mise-managed Python 3.12 (`mise.toml`). If `python3 -m pytest` reports "No module named pytest", install with `python3 -m pip install pytest`. The system `pip3` (Python 3.10) writes to a different site-packages.

**Run a script standalone:**
```bash
cd ~/sandbox/elixirws/aetheris-agents/payslip
python3 scripts/payslip_compute.py data/sample_payroll.csv | python3 -m json.tool
python3 scripts/generate_employee_payslips.py BTL_999
```

**Run an agent:**
```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/payslip/agents/payslip_orchestrator.exs
```

**Evaluate an agent file (syntax/struct check, no LLM call):**
```bash
cd ~/sandbox/elixirws/aetheris
mix run --eval 'Code.eval_file("../aetheris-agents/api/tenant/agents/at1cmd.exs")'
```

**Run a sprint case:**
```bash
cd ~/sandbox/elixirws/aetheris
./scripts/sprint.sh payslip
./scripts/sprint.sh uc_api_agent_t1
```

**Inspect a run:**
```bash
mix aetheris inspect <run_id>
mix aetheris tree show <run_id>
mix aetheris list --limit 20
```

**Aetheris checks (run from `aetheris/` repo, not here):**
```bash
cd ~/sandbox/elixirws/aetheris
mix format --check-formatted
mix credo --strict
mix dialyzer
mix test
```

---

## Architecture

### Core principle

**Scripts do; agents decide.** Python scripts contain all deterministic logic (CSV parsing, computation, file generation, API calls). Elixir agent files contain only the `RunConfig` or `OrbConfig` struct — the LLM reads context, calls scripts via `run_command`, and orchestrates results. Never ask the LLM to construct file content or compute values programmatically.

### Use-case layout

Each use case follows:
```
{use_case}/
  agents/           # .exs files — RunConfig or OrbConfig structs
  scripts/          # Python — deterministic logic, one responsibility per file
  tests/            # pytest — unit + integration; conftest.py per directory
  data/             # input files; .gitignore excludes real data
  docs/             # t*-implementation-notes.md written after each ticket
  output/           # gitignored; .gitkeep committed
```

Current use cases: `payslip`, `drive`, `email`, `api` (uc-api-agent / TAP protocol), `boxy-pipeline` (pure Python; no Aetheris agent — includes data layer scripts for catalog and sales order extraction).

### Agent files

Agent `.exs` files evaluate to either a `%Aetheris.RunConfig{}` (solo agent) or a `%Aetheris.OrbConfig{}` (multi-agent). The harness's `mix aetheris run` loads the first positional file — extra file paths passed to `run_orb` in sprint.sh are ignored by the CLI.

**Critical conventions:**

```elixir
# Always use __ENV__.file — never File.cwd!()
agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))
# For agents two levels deep (e.g. api/tenant/agents/):
agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), "../.."))

# Always nil when output must persist
overlay_base_dir: nil,

# context_strategy for orb agents
context_strategy: :full,   # short-lived pipeline agents (<~10 steps)
context_strategy: :rolling, max_context_steps: 6,  # long-running orchestrators only
```

> `:rolling` with a small `max_context_steps` truncates old messages and can leave orphaned `tool_use_id` references, causing HTTP 400. Use `:full` for any agent that runs fewer than ~10 steps.

### Multi-agent orbs (OrbConfig)

Agents communicate via blackboard and `send_message`. The pattern:

1. **Sender** writes to blackboard: `write_blackboard key: "tap:intent:{id}", value: json`
2. **Sender** signals receiver: `send_message to: "{run_id}", message: "...intent_id: {id}"`
3. **Receiver** waits: `wait_for_event condition: "message_received", timeout_ms: 120000`
4. **Receiver** extracts the key from the message body, reads from blackboard

Run IDs must be pre-established in the OrbConfig so send_message targets are known at prompt-write time:
```elixir
orb_id    = "uc-api-t1-#{Aetheris.ID.generate()}"
at1cmd_id = "#{orb_id}-at1cmd"
cot1_id   = "#{orb_id}-cot1"
```

### Python script conventions

- **One responsibility per script.** Compute scripts → JSON. Generation scripts → files. No mixing.
- **stdout is the contract.** Scripts print JSON to stdout; agents parse it. Errors go to stderr.
- **Exit codes:** 0 on success, 1 on recoverable error. Always 0 for analysis/reporting scripts.
- **`--output-dir` flag** on generation scripts (default `"output"`); lets tests write to `tmp_path`.
- **`cwd=USE_CASE_ROOT`** in subprocess calls from tests so `data/` and `scripts/` resolve correctly.
- **No `__init__.py`** in use-case directories whose name collides with stdlib packages. Use `conftest.py` to insert `scripts/` into `sys.path` instead.
- **Done-check thresholds:** set numeric thresholds (e.g. "≥N resolved items") only after running the pipeline against actual sample data. Estimating before examining output consistently produces wrong numbers and requires a correction commit.
- **Slugification belongs in Python, not the LLM.** When file paths depend on user-supplied strings (search terms, names), implement a `slug_term()` function in a script that returns a filesystem-safe slug. The orchestrator calls the script once, receives pre-computed slugs alongside the original values, and passes both to sub-agents — the LLM does string substitution only, never derives slugs itself.
- **Explicit sink selection with fail-fast.** When a pipeline supports multiple operational sinks (e.g., DB upsert vs. file export), select via an env var resolved at agent eval time. A required-but-absent credential must `raise` immediately — never silently fall back to a different sink. Regression-guard the raise in sprint with a hermetic env check: `env -u MISSING_VAR SINK=mode mix run --eval ...`.
- **Parallel sub-agent file isolation.** When an orchestrator spawns parallel sub-agents that each write files for the same logical output, give each sub-agent a per-term directory (e.g., `data/raw/{slug}/`) rather than a shared flat directory. Without isolation, parallel agents silently overwrite each other's output.
- **Stage CLIs degrade, they don't crash.** A pipeline script hitting empty, null, or malformed input (a provider returning `null`, one bad JSONL line) emits a partial result with a `{"status": "partial"}` envelope and `exit 1` — never an uncaught exception that breaks the stdout contract. Guard per-line/per-item (skip + count `skipped`/`errors`), and treat an API's explicit `null` the same as absent (`x or []`, not `dict.get(k, default)`).
- **Verify a foreign table's live DDL before writing raw SQL to it.** When a script writes to a table owned by another system (e.g. an Ecto/ActiveRecord schema), confirm the real column types and write semantics (`\d table`) before trusting an inferred schema — raw SQL breaks on array types (`jsonb[]` vs `jsonb`), `NOT NULL` timestamps with no DB default, and update-field semantics (don't clobber columns the owner manages, e.g. soft-delete `status`). Test against a faithful schema clone, not a hand-rolled table.

### conftest.py pattern

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

def pytest_configure(config):
    config.addinivalue_line("markers", "integration: ...")
```

Integration tests that require external tools (wkhtmltopdf, etc.) get `@pytest.mark.integration` and are auto-skipped if the tool is absent.

When multiple integration tests share an expensive setup (e.g. running the full pipeline once), extract it into a `@pytest.fixture(scope="module")` rather than repeating the subprocess chain in each test body.

### Domain documents (api/ use case)

The `api/domain/` directory holds two JSONL files read by the gateway agent:
- `ct.stu.vocabulary.jsonl` — tenant-visible; intent definitions, field rules, enum lookups
- `ct.stu.behaviour.jsonl` — gateway-internal; execution modes, on_duplicate, outcomes

Each line is a self-contained JSON record. `record_type` is the discriminator. Blank lines are separators, not errors.

### Sprint script

`aetheris/scripts/sprint.sh` is the integration test harness. Add new cases before the `# Summary` section. All paths from sprint.sh to this repo must use `../aetheris-agents/...` (sprint runs from `aetheris/`). The `run_orb` helper passes its args to `mix aetheris run`; only the first file path is loaded.

---

## Definition of done — doc sync

`docs/rig/specs.md`, `docs/rig/runbook.md`, and `docs/rig/architecture.md` must
stay in sync with the Rig source code. Use the drift checker to verify:

```bash
# From aetheris-agents/ root
python3 scripts/drift_check.py

# Or via sprint.sh (from aetheris/)
./scripts/sprint.sh drift_check
```

**Checks run:** event types (event.ex ↔ specs.md §6), Tauri commands (lib.rs ↔ specs.md §4),
DB schema (store.ex ↔ specs.md §2), env vars (Rust code ↔ specs.md §1 ↔ runbook.md),
routes (registry.ts ↔ App.tsx), payload field sampling (live DB ↔ specs.md §6),
milestone README Status: lines.

**When to run:** after any Rig milestone, after adding commands, event types, env vars,
routes, or DB tables. Zero FAIL findings and zero WARN findings required before committing.

**Strict mode (`--strict`, BL-009).** The sprint runs `drift_check.py --strict`: any
WARN fails the sprint, so drift cannot accumulate into the next alarm-fatigue cycle.
**One exemption** — `project_knowledge` manifest-*staleness* WARNs stay WARN and do not
fail. Rationale: every doc commit re-stales the manifest until the next export, so
mid-cycle staleness is expected truth, not regression; the export boundary is the
enforcement point (that is where the manifest is regenerated and staleness must clear).
So the strict invariant is **"zero *unexplained* WARNs"**, not "zero WARNs" — a standing
manifest-staleness WARN in day-to-day output is the signal we chose to keep, not a
regression to chase. Structural manifest problems (missing manifest, unknown repo, git
failure) are **not** exempt and still fail under `--strict`.

**Ticket text that quotes repo state** (counts, paths, expected outputs) cites the commit
it was verified against; claude-code treats divergence between ticket text and repo reality
as a deviation to note, never to silently follow. Source: BL-001, BL-015, BL-002.

**Every existing gate runs at ticket boundaries, even off-territory** (`mix test`,
`tsc -b`/`bun run build`, `bun run lint`, sprint, `drift_check --strict`). A red gate gets a
tracked ticket the day it's found — never carried silently. Gates that only run when a ticket
happens to touch their territory rot invisibly, and each rot normalizes the next: `mix test`
was red before BL-003, `tsc -b`/`bun run build` red for three weeks (p9-t4), `bun run lint` red
since an undated `eslint-plugin-react-hooks` bump — all three surfaced only because a later
ticket ran the gate off-territory. A known-red gate that already has a tracked ticket is
**named in the packet with its ticket ref, not re-triaged** — the rule prevents silent carry,
not tracked carry. Source: BL-016, BL-005 (×2).

**Optional payload fields:** suffix with `?` in the §6 table cell (e.g. `` `stop_reason?` ``) to allow the field to be absent from current DB events without triggering a FAIL. The drift check emits INFO instead. Add the `?` suffix when the field is valid but not yet emitted by the harness version in use; the INFO firing is the trigger to drop the `?` and promote the field to required.

**Tests:** `python3 -m pytest tests/test_drift_check.py -v`

---

## Key docs to read for each use case

| Use case | Read first |
|----------|-----------|
| payslip | `payslip/docs/t3c-implementation-notes.md` |
| drive | `drive/docs/t3-implementation-notes.md` |
| email | `email/docs/t3-implementation-notes.md` |
| api (TAP) | `docs/uc-api-agent-design.md`, `api/docs/t1-implementation-notes.md` |
| boxy-pipeline | `boxy-pipeline/docs/m-boxy-pipeline.md`, `boxy-pipeline/docs/m-boxy-pipeline-1a.md`, `boxy-pipeline/docs/runbook.md` |
| eduloka | `eduloka/runbook.md`, `docs/milestones/m-eduloka-discovery-summary.md` |
| docbuilder | `docbuilder/runbook.md`, `docbuilder/milestone.md` |

The `docs/agent-creation-guide.md` is the authoritative reference for building new agents.

---

## Learning — m1-docbuilder

Findings that recurred across ≥2 tickets in the docbuilder m1 milestone, promoted per methodology §7.

**`run_command` has no stdin parameter — generation scripts must also accept `--input FILE`.**
The orchestrator cannot pipe a JSON payload to a script's stdin via `run_command`. Any script that reads JSON from stdin must also accept `--input FILE` before it can be called from a `run_command` orchestrator. The first attempt using `sh -c "cat file | python3 script.py"` was unreliable — the LLM timed out on the pipe. See `agent-creation-guide.md` §"Common failure modes".
`Source: m-docbuilder-m1 t7`

**Review packets must include the full done-check output block, opened first.**
A packet without done-check output (test names + PASSED/FAILED + elapsed time + pipeline file listing) is returned unreviewed. The done-check output goes at the top of the packet — not after the diff. This was raised at t4 (blocking) and recurred at t5 and t6 (pipeline file listing absent). The milestone doc prompts for packets now include an explicit "Review packet must open with the full done-check output block" instruction.
`Source: m-docbuilder-m1 t4, t5, t6`

**Implementation notes are a required deliverable, not optional — commit before submitting the review packet.**
A packet missing an implementation notes file is returned unreviewed. The notes file must be committed (not just written) before the packet is sent. For docs-only tickets (no scripts, no agents) a brief notes file is still required: capture decisions made, open items forwarded, and anything that does not survive in the code itself.
`Source: m-docbuilder-m1 t1 (F1 blocking), t8 (F1 — accepted without it for docs ticket)`

---

## Learning — m2a-docbuilder

Findings that recurred across ≥2 tickets in the docbuilder m2a milestone, promoted per methodology §7.

**LLM orchestrators can't reliably round-trip large stdout through `write_file` — give scripts an `--output FILE` (or `--spec FILE`) flag so they write directly.** This is the write-side complement to the m1 `--input FILE` rule. When the orchestrator must capture a script's large stdout (e.g. an ~8K doc-spec JSON) and re-emit it verbatim as a `write_file` `content:` field, the LLM improvises (it wrote `/tmp` scratch scripts instead). Add an `--output FILE` flag: the script writes its payload to the file and prints only the path; the orchestrator passes the path downstream and never handles the blob. Reserve `write_file` for small content the LLM can reproduce exactly.
`Source: m-docbuilder-m2a t6/t7 (render_template `--spec FILE`), t8/t9/t10 (compute_doc `--output FILE`)`

**A new optional doc-spec/template field lands in two steps: the renderer reads it with a fallback default first, `compute_doc` passes it through later.** Add the field to the consuming renderer with `doc_spec.get("field", default)` so it is testable and backward-compatible immediately (tests inject the field directly); wire the `compute_doc` pass-through in a later ticket. When the pass-through lands, the renderer needs no change and live output is unchanged because the demo's values match the prior defaults.
`Source: m-docbuilder-m2a t2 (data_col_start), t3 (table_style), t5 (pass-through)`

**Committed demo/tenant base files must carry the standard named styles and consistent branding across all sheets before the sprint runs.** A placeholder base file built from a minimal template lacks styles like `Heading 1`/`Table Grid`, so renderers fall back (warnings, gridless tables) and branding is asymmetric across sheets. Renderers should degrade rather than crash, but the asset must be regenerated with the needed styles + per-sheet branding before the milestone sprint — otherwise the gap is re-flagged every ticket.
`Source: m-docbuilder-m2a t1, t2, t3 (base-file gap flagged across four tickets)`

**Before re-flagging a carried review finding as "still open", verify it is actually unresolved.** A finding resolved in an earlier commit was re-flagged as open in two later reviews; each time the correction (already fixed in `<commit>`) had to be recorded. Check the current source/commit history for the fix before carrying a finding forward.
`Source: m-docbuilder-m2a t5, t7 (t4 F1 re-flagged after resolution in 6d1d382)`

---

## Learning — m2b-docbuilder

Findings that recurred across ≥2 tickets in the docbuilder m2b milestone, promoted per methodology §7.

**Remove `write_file` from an orchestrator's tools once every phase uses `--output FILE`.** When the last `write_file` user is converted to `--output`, the tool becomes dead capability — drop it from the agent's `tools:` list. Fewer available tools is a smaller surface for the LLM to improvise scratch files. This was the closing piece of the orchestrator scratch-artifact arc (8 → 1 → 0): `--output` on the scripts removed the large-blob round-trip, the explicit "don't investigate" rule removed the re-run-to-inspect habit, and dropping `write_file` removed the capability entirely.
`Source: m-docbuilder-m2b t3 (raised), t7 (confirmed: scratch 0 with tools: ["run_command"])`

**For a JSON env-var default in a shell script, use an `if [ -z ]` guard + single-quoted literal, not `${VAR:-{...}}`.** Bash's `${VAR:-WORD}` mis-parses nested `{...}` in the default WORD: when the var is *already set* to a value ending in `}`, it appends a stray `}`, producing invalid JSON downstream (a `Jason.DecodeError` at the trailing brace). Guard instead: `if [[ -z "${VAR:-}" ]]; then VAR='{"k":"v"}'; fi`. (And keep nounset-safe `${VAR:-}` in any `set -u` script.)
`Source: m-docbuilder-m2b t7 (sprint.sh DOCBUILDER_CONTEXT default; latent since m2a)`

**Factor cross-script plumbing into a shared `_helper.py` module with lazy heavy imports.** When several scripts in a use case share non-trivial plumbing (HTML table markup, Drive auth/navigation/upload), put it in one `scripts/_name.py` rather than duplicating or cross-importing between CLIs. Keep heavy third-party imports *inside the functions* (not at module top) so unit tests can import the helper — and the scripts that use it — without the dependency installed; only the code path that actually calls out needs it.
`Source: m-docbuilder-m2a t10 (_table_html.py), m2b t2/t5 (_drive.py: build_service/find_or_create_folder/upload_file with lazy googleapiclient imports)`

---

## Learning — m3-docbuilder

Findings that recurred across ≥2 tickets in the docbuilder m3 milestone (the context
builder), promoted per methodology §7.

**Derived values are computed by a deterministic script and written to a file; the LLM only orchestrates and never recomputes them — assert this with a byte-identical / end-to-end check.** When an agent must produce values that have real rules (a financial-year invoice sequence, a month-end date), put the rule in a Python script that writes the result to a `--output` file; the agent calls the script, reads the file back, and passes it downstream verbatim. Prove the LLM added nothing by diffing the agent-produced artifact against the script run directly (must be byte-identical), or by an end-to-end render whose output could only come from the script's values. This is the concrete, testable form of "scripts do, agents decide" — when it holds, the agent prompt can shrink to "detect intent → call script → present", which is far more reliable than asking the LLM to do the math.
`Source: m-docbuilder-m3 t3 (resolve_last_run.py; byte-identical confirmed_context.json), t4 (end-to-end render from the script-produced context)`

**When the implementation diverges from the milestone doc, adjudicate the intent, then update the doc — the milestone doc is the single source of truth, so a divergence is closed by changing code *or* the doc, never left as a silent mismatch.** Repeatedly the right call was to keep the (better) implementation and bring the doc to it: single-shot confirmation gate vs an interactive loop; absent-run-log → exit 0 (degrade) vs exit 1; a configurable `DOCBUILDER_CONTEXT_FILE` env var; `DOCBUILDER_AUTOCONFIRM` recorded as not-implemented. Each was adjudicated and the design-decisions table / done-check note updated in the same commit, so the next ticket (and the t5 runbook) is written against the truth rather than a stale spec.
`Source: m-docbuilder-m3 t2 (single-shot gate), t3 (missing-log degrade), t4 (DOCBUILDER_CONTEXT_FILE, DOCBUILDER_AUTOCONFIRM)`

**Pre-list a tool an agent will need next milestone-step, and verify stateful pipelines against their own output record (not a hardcoded value); reset accumulating fixtures for deterministic sprints.** Adding `run_command` to the context builder's `tools:` in t2 — before it was used — made the t3 wiring a prompt-only edit. For the t4 sprint, verifying rendered files against the orchestrator's `renamed.json` (its authoritative PHASE-D record) rather than a hardcoded `…30-Jun-2026…` made the check date-independent; and because `run_log.json` accumulates, the sprint must reset it to a known seed so "same as last month" resolves deterministically (production accumulates; the test seeds).
`Source: m-docbuilder-m3 t2 (run_command pre-listed), t4 (renamed.json verification + run_log seed reset)`

---

## Learning — rig-p9

Findings that recurred across ≥2 tickets in the rig-p9 milestone (Rig per-run env vars +
Docbuilder integration), promoted per methodology §7.

**`run_command` cannot set per-invocation env, and `sh`/`bash` are blocked — per-step env / shell sequencing must live in a `python3` script.** The `run_command` tool schema has no `env` field (`command`/`args`/`working_dir`/`timeout_ms` only), and the exec-server allowlist (`aetheris/native/aetheris_exec_server/src/runner.rs`, `PERMITTED_COMMANDS`) rejects `sh`/`bash` by basename. So an agent cannot do `sh -c "VAR=… cmd"` to set env, nor pass env through the tool. When a step needs per-invocation env (or any shell logic), put it in a Python script (`python3` is allowlisted) that uses `subprocess.run(env=…, cwd=…)`. Verify the allowlist, not just the tool schema, before assuming a command is runnable.
`Source: rig-p9 t3 (sh blocked + no env field → chain_docbuilder.py), t4 (.py heuristic in orchestrate_start)`

**`mix aetheris run` cannot be nested — a chained run must be top-level or sequential, never one agent run inside another.** A nested `mix aetheris run` (inside a running agent's `run_command`) fails: the inner run's `compile.aetheris_worker` does an unconditional `File.copy!` of the worker binary the outer run holds open → `ETXTBSY` ("text file busy"); there is no `--no-compile`/skip escape. To chain Aetheris runs, run the chain **top-level** (e.g. Rig spawns a Python script that runs the sub-agents sequentially) — each sub-run's worker exits and frees the binary before the next, exactly like a shell sprint. This is why the Rig Docbuilder chain is a top-level script, not a wrapping `.exs` agent.
`Source: rig-p9 t3 (nested mix aetheris run → ETXTBSY; verified runs docbuilder-ctx-orch-WRNyiQ/lsjxug), t4 (top-level .py via orchestrate_start)`

---

## Learning — m4-docbuilder

**`mix aetheris run` is single-shot — any design that requires an in-run human reply must be re-modelled as a stop-and-re-run pattern.** The harness has no human-reply channel and `ask_human` is intentionally excluded from the tool set. Interactive-loop designs (confirmation gates, clarification rounds, approval flows) resolve the same way every time: the agent performs its best single-pass (extraction, proposal, self-correction), then stops if human input is required; the operator's "reply" is a re-run with the additional information.
`Source: m-docbuilder-m3 t2 (confirmation gate), m-docbuilder-m4 t2 (clarification round)`

---

## Learning — m5-docbuilder

No recurring findings in this milestone (polish & fresh→render chain). Each t1–t3 review
carried at most one finding, none recurring across ≥2 tickets: t1 (the done-check smoke
command used wrong asset filenames + a `/dev/null` spec that fails JSON-parse → carried to
t4 as a docs fix), t2 (missing live-sprint evidence → re-ran, PASS), t3 (informational
`variant` optional-absent note). The single-shot standing instruction was promoted in the
m5 pre-milestone commit under `## Learning — m4-docbuilder` above.

---

## Learning — m6-docbuilder

Findings that recurred across ≥2 tickets in the m6 milestone (Jinja2 renderer + offer letter),
promoted per methodology §7.

**For a pipeline-integration ticket, run an end-to-end (or agent-eval) check beyond the ticket's stated unit done-check — cross-stage wiring defects pass the unit check and only surface when the real pipeline runs.** Twice the per-ticket done-check went green while the integration was silently broken, caught only by running the full chain: t3 — `compute_doc.py` rebuilt a fresh output dict and dropped `has_jinja`, so the invoice fell back to the Markdown renderer on the `.html.j2` and leaked `{{ }}` (the unit tests + the standalone `generate_html` smoke all passed; the `fetch_data→compute_doc→generate_pdf` end-to-end exposed it). t5 — the docx-jinja render branch over-matched the invoice's docx (`fmt==docx and narrative? and has_jinja?`), and standalone `generate_html.py` does not inject sheet `tables` (only `generate_pdf._narrative_html_jinja` does), so the invoice docx silently lost its Line Items table (the sprint's own assertions passed; opening the rendered `.docx` exposed it). Lesson: when a change touches a multi-stage pipeline (compute → render → rename, or a renderer shared by PDF and DOCX paths), add an end-to-end smoke or an agent-eval that inspects the *final artifact*, not just the stage you changed — and prefer narrowing a generic branch (`…and no_sheets?`) over assuming it only matches the intended bundle.
`Source: m-docbuilder-m6 t3 (compute_doc has_jinja passthrough), t5 (docx-jinja over-match → no_sheets? narrowing)`

**A generic renderer stays generic; pipeline-specific enrichment (sheet tables) lives in the caller, so every code path that renders must perform that enrichment — or be excluded.** `generate_html.py` is a pure Jinja2 renderer (template + context → HTML); the sheet-table injection (`context["tables"] = render_table(...)`) lives in `generate_pdf._narrative_html_jinja`, the PDF caller. The DOCX path that called `generate_html.py` directly therefore had no tables. The fix kept the renderer generic and routed table-bearing docs away from the table-less path, rather than duplicating injection logic into `generate_html.py`. When two output paths share a generic renderer, either both callers enrich identically or the path that can't enrich is restricted to inputs that don't need it.
`Source: m-docbuilder-m6 t3 (tables injected in generate_pdf, not generate_html), t5 (docx path lacked injection → no_sheets? guard)`

---

## Learning — m7-docbuilder

**Write a done-check / sprint command against the *verified* runtime shape, never an assumed one — check the actual data structure, export status, and arg convention before writing the command.** This failure recurred four times across two milestones as different surface manifestations of one root cause: a command was written against what the author *assumed* the shape was, and it broke (or, worse, passed trivially) because the real shape differed. (1) m5 t1 — the §t1 smoke used wrong asset filenames + `--spec /dev/null` (a path arg fed a non-existent/invalid spec), so `grep -c '{{'` returned 0 *trivially* (the renderer never ran). (2) m6 t4b — `compute_doc.py --template X` assumed a flag, but the template is a *positional* arg. (3) m7 t2 — the catalogue done-check did `for e in cat`, but `catalogue.json` is `{"tenant_id":…, "doc_types":[…]}` (a dict); it must iterate `cat["doc_types"]`. (4) m7 t3 — a sprint line read `os.environ['DOCBUILDER_CONTEXT']`, but the value was a shell var (not exported), so under `set -euo pipefail` the `KeyError` killed the run before the agent step; fix was to pass it via argv. **Before writing the command: inspect the file/JSON (`\d`, `head`, a one-line `json.load(...).keys()`), the CLI signature (`--help` / argparse), and whether a var is exported — then write the command to match. A done-check that can pass without exercising the thing it checks is worse than no check.**
`Source: m-docbuilder-m5 t1, m-docbuilder-m6 t4b, m-docbuilder-m7 t2, t3`

---

## Learning — BL-007 (fork: Rig UX + provenance/determinism contract)

Promoted per methodology §7 after the BL-007 milestone-end ritual. Adjudicated
2026-07-20; wording authored by claude-ui, committed by claude-code.

**A packet section referenced is a packet section absent — inline every required section verbatim; existence-in-repo does not satisfy the packet.** This class was already promoted twice from m1 ("review packets must include the full done-check output block"; "implementation notes are a required deliverable") and still arrived as a *blocking* finding, because both earlier rules read as "the section must exist and be committed" — which a packet that *cites* a committed file technically satisfies. It does not: the reviewer reads the packet, not the repo. By §7's own test, a class recurring as blocking means the promoted rule was too vague, so this is a rewrite of the m1 pair, not a third rule beside them.
`Source: m-docbuilder-m1 t4, t8; BL-007 t3`

**No action past a gate until that gate has run and its result is on the record** — covering doc-order gates, test gates, and publish/merge gates alike. Three instances in one milestone, same muscle, different artifact: a doc edited ahead of the gate that should have preceded it; a rider acted on before the milestone doc carried it; and both branches pushed on a "push both branches" instruction before the acceptance e2e was reported green, inverting the agreed reorder → gates → e2e → commit → push order. All three were recoverable only because the held-push discipline caught them — the rule is what makes the discipline unnecessary rather than load-bearing.
`Source: BL-007 t2, t4 (×2)`

**A deferred finding gets a backlog row in the same round it's deferred — prose in a packet or notes files nothing.** Three times this milestone a deferred item survived only because a later reviewer re-noticed it; prose has no executor.
`Source: BL-007 t1, t2, t3`

**Decisions that constrain ticket N+1 land in N+1's README section before its session starts — implementation notes don't travel forward on the prompt path.** The next session reads its ticket text and contract refs, not the previous ticket's notes; three consecutive tickets proved the carry works when done and bites when skipped.
`Source: BL-007 t2, t3, t4`

**A correction chases the corrected claim into every doc that adopted it, in the same round — and a verified citation decays the moment the file moves; re-verify at HEAD before reuse.** A verification pass's own output goes stale when a later pass corrects it (three instances), and two t5 instances show the decay form: a mirror citation and a line number that was right when read. This is the residual of the "cited-means-read" class, which covers claims *never* verified; this one covers claims verified once and reused after they rotted.
`Source: BL-007 t2, t4, t5`

**One symptom can have several mechanisms: verify a fix against the real counterpart in the operator's environment, not a simulation — and a fix proven for one face doesn't close the symptom until the observed face is captured directly.** Six review rounds at BL-007 t4: a real fix for one face (the store `:busy` crash under a per-statement lock race) was mistaken for closure of a symptom actually caused by another (the StrictMode-dead mount guard), and every simulated adversary passed where the field failed — the simulation verified the simulation. Promoted below §7's ≥2-ticket threshold by explicit human ratification, 2026-07-20 — six rounds of cost within one ticket judged sufficient evidence, exception recorded here so the override is auditable.
`Source: BL-007 t4 r3–r6`

**Promotion wording travels as a review-file artifact, not chat: claude-ui's §7 promotion draft lands in `docs/reviews/` before the promotion commit is cut.** Class E's mechanism hit this milestone's own promotion pipeline twice — the P3–P6 relay gap, then P6 again across the session restart — because the authored wording existed only in conversation.
`Source: BL-007 t5 (§7 ritual, ×2)`
