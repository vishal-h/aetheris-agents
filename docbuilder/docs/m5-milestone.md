# Milestone — m5-docbuilder — Polish & fresh→render chain

**Repo:** aetheris-agents
**Branch:** m5-docbuilder
**Depends on:** aetheris-agents `78c7448` (m4 closed, drift clean 8 PASS / 0 FAIL / 0 WARN)

> **Doc path:** `docbuilder/docs/m5-milestone.md` (aligned to the m1–m3/m4 convention —
> all milestone scope docs live at `docbuilder/docs/m{N}-milestone.md`; `milestones/` holds
> per-ticket implementation notes, `reviews/` holds reviews).

---

## Goal

Close the m4 open items and complete the fresh path end-to-end: a freeform NL request
for a new client should produce a correctly rendered invoice with no `{{placeholder}}`
artifacts in the output. The milestone also promotes the single-shot standing instruction
to `CLAUDE.md` and adds the `docbuilder_fresh_render` sprint case to verify the full
fresh→render chain.

---

## What is NOT in scope

- Changes to `context_builder.exs`, `resolve_last_run.py`, `run_log_writer.py`, or
  any orchestrator pipeline beyond `render_template.py`
- New document types or template variants
- Tenant-configurable `CURRENCIES` allowlist (extend the hardcoded list if needed, but
  do not make it tenant-configurable in this milestone)
- Multi-round clarification or interactive confirm/amend loop
- Changes to the Rig Docbuilder panel

---

## Pre-milestone commit (before ticket work starts)

Promote the single-shot standing instruction to `CLAUDE.md`. This was recorded in the
m4 milestone summary as a promotion candidate sourced to m3 t2 and m4 t2. Commit it
as a standalone doc-only change before t1 begins.

**Content to add** under `## Learning — m4-docbuilder` in `CLAUDE.md`:

> **`mix aetheris run` is single-shot — any design that requires an in-run human reply
> must be re-modelled as a stop-and-re-run pattern.** The harness has no human-reply
> channel and `ask_human` is intentionally excluded from the tool set. Interactive-loop
> designs (confirmation gates, clarification rounds, approval flows) resolve the same
> way every time: the agent performs its best single-pass (extraction, proposal,
> self-correction), then stops if human input is required; the operator's "reply" is a
> re-run with the additional information.
> `Source: m-docbuilder-m3 t2 (confirmation gate), m-docbuilder-m4 t2 (clarification round)`

---

## Design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Optional field rendering | `render_template.py` `_sub_var` returns `""` for absent optional fields instead of raw `{{placeholder}}` | Unresolved Handlebars placeholders in a client-facing PDF are a rendering defect; absent optional fields should render as empty, not as template syntax |
| Known vs unknown variable distinction | Distinguish schema-known optional fields (return `""`, no warning) from truly unknown variables (return `""` with warning) | Allows operators to detect template mismatches while keeping optional fields clean |
| Optional fields list | `order_ref`, `order_effective_date`, `terms`, `client_code`, `currency`, `unit_price`, `line_item_qty` — fields in the context schema that are not in `BASE_REQUIRED` or `INVOICE_REQUIRED` | Matches `validate_fields.py`'s schema; keeps the two scripts in sync |
| `docbuilder_fresh_render` sprint | Chains `context_builder.exs` (fresh) → `docbuilder_orchestrator.exs`; resets run log to `[]`; verifies rendered files exist and contain no `{{` strings | Full fresh→render verification; complementary to `docbuilder_fresh` (builder-only) |
| `CURRENCIES` allowlist | Extend with `SGD`, `CAD`, `AUD` (common for the tenant's client base); add a comment noting it is hardcoded and must be extended manually | Simple extension, no architecture change; carries the t1 F2 note forward |
| Test docstring tidy | Fix `test_context_builder_fresh.py` module docstring from "Integration tests" to "Script CLI tests" | Cosmetic; avoids confusion with the `integration` pytest marker |

---

## Ticket structure

| Ticket | Title | Key artifacts |
|---|---|---|
| t1 | `render_template.py` optional field fix | `scripts/render_template.py`, tests |
| t2 | `validate_fields.py` + test housekeeping | `scripts/validate_fields.py`, `tests/test_context_builder_fresh.py` |
| t3 | `docbuilder_fresh_render` sprint case | `aetheris/scripts/sprint.sh` |
| t4 | Docs sync + milestone close | `docs/capability-matrix.md`, `docbuilder/runbook.md`, `CLAUDE.md` |

---

## Tickets

### t1 — `render_template.py` optional field fix

**Scope.** `render_template.py`'s `_sub_var` currently returns `m.group(0)` (the raw
`{{placeholder}}` string) when a variable is absent from the context. This causes
unresolved `{{order_ref}}`, `{{order_effective_date}}`, `{{terms}}` etc. to appear in
rendered PDFs for fresh-path invoices that don't supply these optional fields. Fix:
return `""` for absent fields, distinguishing schema-known optional fields (silent) from
genuinely unknown variables (warn).

**Contract refs.**
- `agent-creation-guide.md` §"Scripts do, agents decide" — the fix is in the script,
  not the agent
- `docbuilder/docs/context-schema.md` — the optional fields list

**Touches.**
- `docbuilder/scripts/render_template.py` — update `_sub_var` to return `""` for absent
  fields; add `OPTIONAL_FIELDS` set; distinguish known-optional (silent) from unknown (warn)
- `docbuilder/tests/test_render_template.py` — add tests for: absent optional field →
  `""` substituted (no placeholder in output); absent required field → warning emitted;
  unknown variable → warning emitted; known optional absent → no warning

**Do not generate.**
- Do not modify `generate_pdf.py`, `_table_html.py`, `context_builder.exs`, or any
  other script outside Touches
- Do not modify the Handlebars templates in `data/templates/` — the fix is in the
  renderer, not the templates

**Runbook update rule.** No new env vars or operational procedures. No runbook update
required.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

# Unit tests (new + existing)
python3 -m pytest tests/test_render_template.py -v

# Full docbuilder suite
python3 -m pytest tests/ -q

# Smoke: render a context with missing optional fields — no {{placeholders}} in output
python3 scripts/render_template.py \
  --template data/templates/bitloka/invoice/v1/invoice.md.template \
  --css data/templates/bitloka/invoice/v1/invoice.css \
  --context '{"title":"Test","client_name":"Acme"}' \
  --spec /dev/null 2>/dev/null | grep -c '{{'
# Expected: 0
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing any code. Then implement t1
> of `docbuilder/docs/m5-milestone.md`.
>
> **Scope:** fix `render_template.py`'s `_sub_var` so absent variables render as `""`
> rather than the raw `{{placeholder}}` string.
>
> **Change to `_sub_var` in `render_template.py`:**
> - Add an `OPTIONAL_FIELDS` set at module level containing all context-schema fields
>   that are not in `BASE_REQUIRED` or `INVOICE_REQUIRED` from `validate_fields.py`:
>   `{"order_ref", "order_effective_date", "terms", "client_code", "currency",
>   "unit_price", "line_item_qty", "variant"}`.
> - In `_sub_var`: if `key in context`, return `str(context[key])` (unchanged).
>   If `key not in context` AND `key in OPTIONAL_FIELDS`, return `""` silently.
>   If `key not in context` AND `key not in OPTIONAL_FIELDS`, call `_warn(...)` and
>   return `""` (was: return `m.group(0)`). This collapses both missing cases to `""`
>   while preserving the warning for genuinely unknown variables.
>
> **Tests to add in `test_render_template.py`** (or create the file if absent):
> - Absent optional field → renders as `""`, no `{{` in output, no warning emitted
> - Absent non-optional (unknown) variable → renders as `""`, warning emitted
> - Present field → renders its value (existing behaviour, confirm not broken)
>
> Use `render_template(template_text, context, doc_spec, css_path)` directly for unit
> tests (not the CLI subprocess) where possible.
>
> **Touches:** `docbuilder/scripts/render_template.py`,
> `docbuilder/tests/test_render_template.py`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m5-milestone.md §t1` and include its full output at the
> top of the review packet, before the diff.

---

### t2 — `validate_fields.py` + test housekeeping

**Scope.** Three small carried items from the m4 open list: extend the `CURRENCIES`
allowlist in `validate_fields.py` and add a comment noting it is hardcoded; fix the
misleading module docstring in `test_context_builder_fresh.py`; harden the
`docbuilder_fresh` sprint's client-match assertion to work with any `DOCBUILDER_REQUEST`.

**Contract refs.**
- m4 milestone summary §"Open items for m5" — the three items
- `agent-creation-guide.md` §"Scripts do, agents decide" — `validate_fields.py` is a
  deterministic script; no LLM logic

**Touches.**
- `docbuilder/scripts/validate_fields.py` — extend `CURRENCIES` with `{"SGD", "CAD",
  "AUD"}`; add a comment: `# Hardcoded; extend manually when currency support broadens`
- `docbuilder/tests/test_validate_fields.py` — add tests for the three new currencies
- `docbuilder/tests/test_context_builder_fresh.py` — fix module docstring from
  "Integration tests" to "Script CLI tests for the freeform fresh path (m4 t3)"
- `aetheris/scripts/sprint.sh` — harden the `docbuilder_fresh` client-match assertion:
  parse `client_name` from `confirmed_context.json` and assert it is non-empty, rather
  than checking for the hardcoded "Northwind" substring

**Do not generate.**
- Do not modify `context_builder.exs`, `run_log_writer.py`, or any agent file
- Do not change the `CURRENCIES` validation logic — only extend the set and add the comment
- Do not add new sprint cases — that is t3

**Runbook update rule.** No new env vars or procedures. The `CURRENCIES` extension is
a code change only; no runbook update required.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents/docbuilder

# validate_fields.py new currency tests
python3 -m pytest tests/test_validate_fields.py -v

# Full docbuilder suite
python3 -m pytest tests/ -q

# Verify docstring fix
head -5 tests/test_context_builder_fresh.py

# Verify CURRENCIES comment
grep -n "Hardcoded" scripts/validate_fields.py

# Sprint case: client-match no longer hardcodes "Northwind"
cd ~/sandbox/elixirws/aetheris
DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh
# Expected: [OK] confirmed_context.json written + parseable
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing any code. Then implement t2
> of `docbuilder/docs/m5-milestone.md`.
>
> **Three changes, all small:**
>
> 1. `validate_fields.py` — extend `CURRENCIES` from `{"GBP","USD","EUR","AED","INR"}`
>    to also include `{"SGD","CAD","AUD"}`. Add a comment on the line:
>    `# Hardcoded; extend manually when currency support broadens (m4 t1 F2).`
>    Add tests in `test_validate_fields.py` for: `"sgd"` → normalised to `"SGD"` (exit 0);
>    `"cad"` → `"CAD"` (exit 0); `"aud"` → `"AUD"` (exit 0).
>
> 2. `test_context_builder_fresh.py` — fix the module docstring (first line after the
>    opening `"""`): change `"Integration tests for the freeform "fresh" path (m4 t3)."`
>    to `"Script CLI tests for the freeform fresh path — exercises validate_fields.py
>    via CLI subprocess (no live LLM). m4 t3."`. Do not change any test logic.
>
> 3. `aetheris/scripts/sprint.sh` `docbuilder_fresh` case — replace the hardcoded
>    `'Northwind' in c.get('client_name','')` substring check with:
>    ```bash
>    python3 -c "import json,sys; c=json.load(open('$CTX')); \
>      sys.exit(0 if c.get('client_name','').strip() else 1)" 2>/dev/null
>    ```
>    and update the `ok` message to `"confirmed_context.json written + parseable
>    (client: $(python3 -c "import json; \
>    print(json.load(open('$CTX')).get('client_name','?'))" 2>/dev/null))"`.
>    This makes the assertion client-agnostic: any non-empty `client_name` passes.
>
> **Touches:** `docbuilder/scripts/validate_fields.py`,
> `docbuilder/tests/test_validate_fields.py`,
> `docbuilder/tests/test_context_builder_fresh.py`,
> `aetheris/scripts/sprint.sh`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m5-milestone.md §t2` and include its full output at the
> top of the review packet, before the diff.

---

### t3 — `docbuilder_fresh_render` sprint case

**Scope.** A new sprint case that chains the fresh path end-to-end: resets `run_log.json`
to `[]`, runs `context_builder.exs` (fresh extraction), then runs `docbuilder_orchestrator.exs`
consuming `confirmed_context.json`, and verifies: (a) rendered files are present via
`renamed.json`, (b) none of the rendered PDFs contain unresolved `{{` placeholder strings.

The check (b) is the key assertion that t1's fix holds end-to-end — a fresh-path invoice
must have zero `{{` artifacts in the PDF output.

**Contract refs.**
- m3-milestone §Design decisions — `DOCBUILDER_CONTEXT_FILE` + orchestrator context
  source precedence
- m4-milestone §"docbuilder_fresh sprint" — the builder-only pattern to extend

**Touches.**
- `aetheris/scripts/sprint.sh` — new `docbuilder_fresh_render` case (also under `all`);
  usage line updated
- `docbuilder/runbook.md` — add `docbuilder_fresh_render` sprint-case entry
- `docbuilder/docs/milestones/m-docbuilder-m5-t3-implementation-notes.md` — new

**Do not generate.**
- Do not modify `context_builder.exs`, `docbuilder_orchestrator.exs`, or any Python script
- Do not update `docs/rig/runbook.md` — that is t4

**Runbook update rule.** Add the new sprint case entry to `docbuilder/runbook.md` in
this ticket (not deferred to t4) — the sprint-case entry is operational documentation
that belongs with the ticket that introduces the case.

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris

# Full fresh→render chain
DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh_render
# Expected:
#   context_builder.exs evaluates [OK]
#   confirmed_context.json written (client: Northwind Traders) [OK]
#   rendered: northwind_traders_invoice_2026-06-30.{xlsx,docx,pdf} [OK]  (via renamed.json)
#   no {{placeholders}} in PDF [OK]
#   run log appended (PHASE D2 fired) [OK]
```

**Claude-code prompt.**
> Read `CLAUDE.md` (aetheris-agents root) before writing any code. Then implement t3
> of `docbuilder/docs/m5-milestone.md`.
>
> **Scope:** add `docbuilder_fresh_render` sprint case to `sprint.sh`.
>
> **Case behaviour:**
> - Reset `data/run_log.json` to `[]` and clear `confirmed_context.json`,
>   `raw_extraction.json`, `validated_extraction.json`, `renamed.json`.
> - Set the default `DOCBUILDER_REQUEST` to the Northwind Traders full-field request
>   (same as `docbuilder_fresh`).
> - Unset `DOCBUILDER_CONTEXT`.
>
> Step 1 — context builder (fresh):
> - Eval check, then `run_agent` for `context_builder.exs`.
> - Assert `confirmed_context.json` written + parseable + `client_name` non-empty
>   (use the client-agnostic check from t2, not a hardcoded substring).
>
> Step 2 — orchestrator (reads `confirmed_context.json` via `DOCBUILDER_CONTEXT_FILE`):
> - Set `DOCBUILDER_CONTEXT_FILE` to the absolute path of `confirmed_context.json`.
> - `run_agent` for `docbuilder_orchestrator.exs` with `DOCBUILDER_CONTEXT` unset.
> - Unset `DOCBUILDER_CONTEXT_FILE` after the run.
>
> Step 3 — verify rendered output:
> - Read `renamed.json` and assert each listed file exists and is non-empty
>   (reuse the `renamed.json` loop from `docbuilder_context`).
> - For the PDF output (the file ending in `.pdf`), assert it contains no `{{`
>   strings: `pdftotext <file> - 2>/dev/null | grep -c '{{'` → expected 0. If
>   `pdftotext` is unavailable, skip this check with an `[INFO]` message (do not fail).
>
> Step 4 — verify PHASE D2:
> - Assert `run_log.json` has exactly 1 entry (was `[]` before, orchestrator appended).
>
> Also under `all`. Update the usage line.
>
> Add a `docbuilder_fresh_render` sprint-case entry to `docbuilder/runbook.md` (the
> same section as `docbuilder_fresh`).
>
> **Touches:** `aetheris/scripts/sprint.sh`, `docbuilder/runbook.md`,
> `docbuilder/docs/milestones/m-docbuilder-m5-t3-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m5-milestone.md §t3` and include its full output at the
> top of the review packet, before the diff.

---

### t4 — Docs sync + milestone close

**Scope.** Bring all reference docs in sync with t1–t3. Update the capability matrix
(`render_template.py` description updated; no new scripts). Run drift check. Write the
milestone summary. CLAUDE.md scan for recurring findings.

**Contract refs.**
- `milestone-methodology.md` §7 — milestone-end ritual
- `milestone-methodology.md` §8 — sync rules

**Touches.**
- `docs/capability-matrix.md` — update `render_template.py` description to note the
  optional-field fix (m5); counts unchanged (no new scripts/agents)
- `docs/rig/runbook.md` — add `docbuilder_fresh_render` sprint-case mention in the m4
  section (mirrors the docbuilder/runbook.md entry from t3)
- `docbuilder/docs/m5-milestone.md` — milestone summary appended
- `aetheris-agents/CLAUDE.md` — `## Learning — m5-docbuilder` (recurring findings scan;
  "No recurring findings" if none)
- `docbuilder/docs/milestones/m-docbuilder-m5-t4-implementation-notes.md` — new

**Do not generate.**
- Do not modify any script, agent, or test file
- Do not add new env vars

**Done-check.**
```bash
cd ~/sandbox/elixirws/aetheris-agents

python3 scripts/drift_check.py
# Expected: 0 FAIL (project_knowledge WARNs = BL-002, human-owned)

grep -n "render_template" docs/capability-matrix.md
grep -n "docbuilder_fresh_render" docs/rig/runbook.md
grep -c "^## Milestone summary" docbuilder/docs/m5-milestone.md
```

**Claude-code prompt.**
> Read `CLAUDE.md` and `milestone-methodology.md` §7 before writing. Then implement t4
> of `docbuilder/docs/m5-milestone.md`. Docs-only — no scripts, agents,
> or tests.
>
> 1. `docs/capability-matrix.md` — update the `render_template.py` row description to
>    append: `Optional fields render as empty string when absent (m5).` Counts unchanged.
>
> 2. `docs/rig/runbook.md` — in the m4 section, add a sentence after the
>    `docbuilder_fresh` paragraph: `For the full fresh→render chain (context builder +
>    orchestrator), use \`./scripts/sprint.sh docbuilder_fresh_render\` (m5).`
>
> 3. Scan `docbuilder/docs/reviews/m-docbuilder-m5-t{1,2,3}-review.md` for findings
>    recurring on ≥2 tickets. Write `## Learning — m5-docbuilder` in `CLAUDE.md` per
>    methodology §7. If no findings recurred, write the header with "No recurring
>    findings in this milestone."
>
> 4. Append milestone summary to `docbuilder/docs/m5-milestone.md`:
>    what shipped (t1–t3), deferred, surprises, open items for m6.
>
> 5. Run `drift_check.py` and include the full output in the review packet.
>
> **Touches:** `docs/capability-matrix.md`, `docs/rig/runbook.md`,
> `docbuilder/docs/m5-milestone.md`,
> `aetheris-agents/CLAUDE.md`,
> `docbuilder/docs/milestones/m-docbuilder-m5-t4-implementation-notes.md`.
>
> **Do not generate** anything outside Touches.
>
> Run the done-check from `m5-milestone.md §t4` and include its full output at the
> top of the review packet, before the diff.

---

## Open questions for m6

- The rendered invoice line-item table (Rate / # Resources / # Months / Amount) is
  hardcoded in the template. A future milestone could make this data-driven from the
  context (e.g. `line_items: [{description, rate, qty, months, amount}]`) and drive
  it through `compute_doc.py`.
- The `CURRENCIES` allowlist in `validate_fields.py` is still hardcoded after m5.
  If the tenant adds new currencies frequently, make it tenant-configurable via the
  catalogue.
- The `docbuilder_fresh_render` PDF placeholder check uses `pdftotext` (degrades
  gracefully if absent). Consider adding `pdftotext` to the prerequisites check in
  `sprint.sh` for environments where it is expected to be available.

---

## Milestone summary

_To be written by claude-code at t4, from the implementation notes._
