# m-docbuilder-m4 — Freeform NL Field Extraction

> **Path:** `docbuilder/docs/milestones/m-docbuilder-m4.md`
> **Canonical repo:** aetheris-agents
> **Base commit:** `c14a0e4` (m3 + rig-p9 clean, 8 PASS / 0 FAIL / 0 WARN)

---

## Goal

Extend `context_builder.exs` so a freeform open-ended request like:

> "a formal quote for Acme Corp, 40 days of consulting at £1,200/day, standard payment terms"

produces a valid `confirmed_context.json` — without requiring a prior run in the
log. The recurring / "same as last month" path (m3) is unchanged. m4 adds the
complementary freeform extraction path.

---

## What is NOT in scope

- Conversational template editing (patch schema + JSONL edit log) — deferred
- Multi-tenant support beyond the existing tenant layout
- New document types or template variants
- Changes to the Rig Docbuilder panel (rig-p9 is closed and wired)
- Interactive confirm/amend loop (requires a conversational harness)
- More than one clarifying-question round before fallback
- Any change to the orchestrator, PHASE D2, or `run_log_writer.py`

---

## Design decisions

These were resolved in the planning session before this doc was drafted.

**D1 — LLM/script boundary.** Field extraction from NL is LLM work; there is no
deterministic rule for parsing "40 days at £1,200/day" into
`{line_item_qty: 40, unit_price: 1200, currency: "GBP"}`. The boundary is:
LLM extracts a raw field map (inside the existing `context_builder.exs` system
prompt), then a new `validate_fields.py` script validates and normalises that
raw JSON against the context schema — required fields present, date parseable,
amounts well-formed, currency codes valid. The script exits non-zero with a
structured JSON error payload if anything is missing or malformed. The agent
reads the error and formulates the clarifying question; it never re-derives
the validated values itself.

> **Amount normalisation (t1 review, accepted divergence).** `amount_due` is a context
> schema string substituted **verbatim** into the rendered document (`{{amount_due}}` →
> "$1,000.00"), so it is **validated as a monetary value but kept as its display string** —
> NOT coerced to a bare float (which would regress the invoice render to "1000.0"). Only
> the LLM-extracted numeric *intermediates* `unit_price` / `line_item_qty` (not in the final
> context schema) are coerced to numbers.

**D2 — Ambiguity loop depth (single-shot self-correction; t2 review).**
`context_builder.exs` runs single-shot via `mix aetheris run` — there is no in-run
human-reply channel, and `ask_human` is intentionally NOT in its tools (identical
constraint to the m3 confirmation gate). So the "one round" is a **self-correction
re-pass**: on a validation failure the agent re-reads the *original* request for fields
the first extraction missed and re-validates ONCE. If a required field is genuinely absent
from the request, the agent emits **one** clarifying message naming the missing/invalid
fields and stops without writing `confirmed_context.json` — the operator's "reply" is a
**re-run with the field included** (out-of-run). An interactive in-run wait/loop requires
a conversational harness and is deferred. (The agent prompt's step-iv parenthetical —
"this run cannot pause for a human reply; the second pass is your own re-read" — encodes
this.)

**D3 — Agent extension vs sub-agent.** Extend `context_builder.exs` (Option A).
The extraction logic is a section replacement in the existing step-3b decision
branch, not a new agent. The `context_builder` already owns the inputs
(catalogue, run log) and the output (`confirmed_context.json`); a sub-agent
adds plumbing without payoff at this scope.

**D4 — `validate_fields.py`.** Yes — a separate validation/normalisation script
is required. Validation is deterministic: given a raw extracted JSON it either
produces a clean normalised JSON (`--output FILE`) or exits 1 with a structured
`{"missing": [...], "invalid": {...}}` payload the agent can read. This gives
a machine-checkable done-condition for t1 and upholds the m3 learning: scripts
do, agents decide.

---

## Ticket set

| # | Title | Artifact boundary | Depends on |
|---|-------|------------------|------------|
| t1 | `validate_fields.py` — schema validation + normalisation script | new script | — |
| t2 | `context_builder.exs` — freeform extraction + one-round clarification | system prompt edit | t1 |
| t3 | Tests + sprint case for the freeform path | test file + sprint case | t1, t2 |
| t4 | Runbook + docs update | docs only | t1–t3 |

---

### t1 — `validate_fields.py`

**Scope.** A new Python script `docbuilder/scripts/validate_fields.py` accepts
a raw extracted-field JSON (via `--input FILE`) and the context schema rules,
and either writes a normalised context JSON to `--output FILE` (exit 0) or
writes a structured error JSON to `--output FILE` and exits 1. No LLM call;
no network. The normalisation rules are: ISO 8601 date coercion for `date` and
`order_effective_date`; `amount_due` validated as a monetary value but kept as its
display string (verbatim render substitution — t1 review); numeric coercion for the
extraction intermediates `unit_price`, `line_item_qty`; `currency` uppercased and
validated against a fixed set
(`GBP`, `USD`, `EUR`, `AED`, `INR`); required-field presence checked against
the doc_type (all: `title`, `client_name`, `client_email`, `date`; invoice
additionally: `invoice_number`, `client_address`, `amount_due`). Fields not in
the schema are passed through unchanged. The script does not read the tenant
catalogue or run log — it only validates what it is given.

**Contract refs.**
- `aetheris-agents/CLAUDE.md` — "Scripts do; agents decide"; `--input FILE` /
  `--output FILE` pattern; stage-CLI degrade rule; conftest.py pattern
- `aetheris-agents/CLAUDE.md` Learning — m3 derived-values rule (byte-identical
  assertion)
- `docbuilder/docs/context-schema.md` — required fields, field types (normative;
  do not restate in the prompt)

**Touches.**
- `docbuilder/scripts/validate_fields.py` (new)
- `docbuilder/tests/test_validate_fields.py` (new)

**Do not generate.**
- Do not modify `context_builder.exs`, `resolve_last_run.py`, or any other
  existing script.
- Do not add the sprint case (t3).
- Do not read or modify `data/run_log.json` or the tenant catalogue.

**Runbook update rule.** This ticket introduces no new env vars, startup steps,
or operational procedures. No runbook change required in t1.

**Done-check.**
```bash
# From aetheris-agents/ root
python3 -m pytest docbuilder/tests/test_validate_fields.py -v

# Spot-check exit codes manually:
# Valid input → exit 0, output is parseable JSON with required fields present
# Missing required field → exit 1, output contains {"missing": ["client_email"]}
# Malformed date → exit 1, output contains {"invalid": {"date": "..."}}
```

**Claude-code prompt.**

> Read `aetheris-agents/CLAUDE.md` (all learning sections) and
> `docbuilder/docs/context-schema.md` before writing any code.
>
> **Scope:** create `docbuilder/scripts/validate_fields.py` and
> `docbuilder/tests/test_validate_fields.py`.
>
> The script accepts `--input FILE` (raw extracted-field JSON) and
> `--output FILE`. On success it writes a normalised context JSON to the output
> file and exits 0. On failure it writes
> `{"missing": ["field", ...], "invalid": {"field": "reason", ...}}` to the
> output file and exits 1. Partial failure (some fields valid, some not) exits 1
> — the full normalised-as-far-as-possible JSON is NOT written on exit 1; only
> the error payload.
>
> Normalisation rules (from `context-schema.md` — read it, do not restate):
> date fields → ISO 8601; `amount_due` → validated as money, kept as display string
> (verbatim render substitution); `unit_price`/`line_item_qty` → numeric (extraction
> intermediates); `currency` → upper + validate
> against the fixed set; required fields checked per doc_type (read from input
> as `doc_type`, default `invoice` if absent).
>
> Tests must cover: all-valid invoice input (exit 0, byte-compare key fields);
> missing required field (exit 1, `missing` array); invalid date format (exit 1,
> `invalid` dict); unknown currency (exit 1); non-invoice doc_type skips
> invoice-only required fields; extra/unknown fields pass through in exit-0
> output unchanged.
>
> **Touches:** `docbuilder/scripts/validate_fields.py`,
> `docbuilder/tests/test_validate_fields.py`. Anything outside this list must
> be noted in your implementation notes.
>
> **Do not generate:** do not modify any existing file. Do not add the sprint
> case (t3 does that).
>
> Run the done-check and include its full output at the top of your review
> packet, before the diff. Implementation notes are a required deliverable —
> commit them to `docbuilder/docs/milestones/m-docbuilder-m4-t1-implementation-notes.md`
> before sending the packet.

---

### t2 — `context_builder.exs` freeform extraction + one-round clarification

**Scope.** The existing step-3b "FRESH request" section of `context_builder.exs`
currently instructs the agent to list missing fields and stop. This ticket
replaces that behaviour with: (1) extract a raw field map from the freeform
request text; (2) call `validate_fields.py --input <extracted> --output
<validated>`; (3a) if exit 0, proceed to the existing confirmation gate
(write `confirmed_context.json`, emit the `PROPOSED DOCBUILDER_CONTEXT` block);
(3b) if exit 1, read the error payload and **self-correct once** — re-read the
*original* request for the named fields (no in-run human reply; see D2), re-extract only
what the request actually contains, and re-run `validate_fields.py`; (3c) if
still exit 1 after that second pass, emit one clarifying message ("I need the following
to proceed: <list>. Please re-run with these included.") and stop
without writing the context file. The recurring path (step 3a, "same as last
month") and the confirmation gate are unchanged.

**Contract refs.**
- `aetheris-agents/CLAUDE.md` — "Scripts do; agents decide"; `--output FILE`
  rule; m3 learning: LLM reads the file back, passes it downstream verbatim
- `aetheris-agents/CLAUDE.md` Learning — m3 doc-divergence rule (if
  implementation diverges from this spec, adjudicate + update the doc)
- `agent-creation-guide.md` — `run_command` format (`command:` / `args:`);
  Common failure modes (`python3 python3` guard)
- `docbuilder/docs/context-schema.md` — field names referenced by the new
  prompt section (do not restate the schema; point at the file)

**Touches.**
- `docbuilder/agents/context_builder.exs` (system prompt edit, step 3b only)

**Do not generate.**
- Do not modify `validate_fields.py` (t1 owns it).
- Do not modify `resolve_last_run.py`, the orchestrator, or any other file.
- Do not add new tools to the agent's `tools:` list — `run_command`,
  `read_file`, `write_file` are already present from m3; `validate_fields.py`
  is called via `run_command`.
- Do not add the sprint case (t3).

**Runbook update rule.** No new env vars introduced. No runbook change in t2.
The new step-3b behaviour is prose-documented in the milestone summary (t4).

**Done-check.**
```bash
# From aetheris/ — uses the existing docbuilder_context sprint case.
# First: clear the run log so the fresh path is exercised (not the recurring path).
# The sprint case must be adapted or a direct run used; see note below.

# Direct run — freeform request with all required fields present (expect exit 0,
# confirmed_context.json written, PROPOSED block in trajectory):
cd ~/sandbox/elixirws/aetheris
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="A formal quote for Acme Corp, 40 days of consulting at £1,200/day, standard payment terms, ops@acme.example" \
mix aetheris run ../aetheris-agents/docbuilder/agents/context_builder.exs

# Verify:
cat ../aetheris-agents/docbuilder/output/confirmed_context.json | python3 -m json.tool
# Must contain client_name, client_email, date, title; must be parseable JSON.

# Direct run — freeform request with missing client_email (expect one clarifying
# question in the trajectory, not a STOP; second pass should produce confirmed_context.json
# if a mock reply supplies the email — or trajectory shows fallback if no reply):
# (This is a manual trajectory inspection; the sprint case in t3 automates it.)
```

> **Note on the sprint case:** the existing `docbuilder_context` sprint case exercises
> the recurring path. t2's done-check uses direct `mix aetheris run` calls to verify
> the fresh path. t3 will wire the automated freeform sprint case.

**Claude-code prompt.**

> Read `aetheris-agents/CLAUDE.md` (all learning sections),
> `agent-creation-guide.md` §"run_command format" and §"Common failure modes",
> and `docbuilder/docs/context-schema.md` before editing any file.
>
> **Scope:** edit the system prompt of `docbuilder/agents/context_builder.exs`,
> step-3b section only.
>
> Replace the current "LIST what is missing and STOP" instruction with the
> three-branch logic:
>
> 1. Extract a raw field map from the freeform request. Write it to
>    `output/raw_extraction.json` using `write_file`.
> 2. Call `validate_fields.py` via `run_command`:
>    `command: "python3", args: ["scripts/validate_fields.py", "--input",
>    "output/raw_extraction.json", "--output", "output/validated_extraction.json"]`.
> 3a. Exit 0 → read `output/validated_extraction.json` via `read_file`. Proceed
>    to the existing confirmation gate: write `output/confirmed_context.json`,
>    emit the `PROPOSED DOCBUILDER_CONTEXT` block. (Confirmation gate logic is
>    unchanged — do not touch it.)
> 3b. Exit 1 → read `output/validated_extraction.json` (the error payload) via
>    `read_file`. Self-correct ONCE: re-read the ORIGINAL request for the named
>    missing/invalid fields and re-extract only what it actually contains (this run
>    cannot pause for a human reply — the second pass is your own re-read, not an operator
>    answer). Repeat from step 1 (one time only).
> 3c. If validation still fails after the second pass → emit one clarifying message:
>    "I need the following to proceed: <list from error payload>. Please re-run with
>    these included." Do NOT write `confirmed_context.json`. Stop.
>
> The step-3a recurring path ("same as last month" → `resolve_last_run.py`) is
> unchanged. Do not touch it.
>
> Constraints from contract:
> - The LLM must not recompute, infer, or fabricate values that `validate_fields.py`
>   rejected. The second-pass extraction must incorporate the operator's literal
>   reply, not the LLM's guess at what the reply implies.
> - `python3 python3 script.py` is a known failure mode — guard: `command: "python3"`,
>   `args: ["scripts/validate_fields.py", ...]`. Never put `python3` in both fields.
>
> **Touches:** `docbuilder/agents/context_builder.exs` only.
>
> **Do not generate:** any other file. If the done-check reveals a gap in
> `validate_fields.py`, note it in implementation notes and raise it as a
> finding — do not patch the script in this session.
>
> Run the done-check (both direct-run cases) and include the full output at the
> top of your review packet. Implementation notes are required — commit to
> `docbuilder/docs/milestones/m-docbuilder-m4-t2-implementation-notes.md`.

---

### t3 — Tests and sprint case for the freeform path

**Scope.** Two additions: (1) a pytest integration test
`docbuilder/tests/test_context_builder_fresh.py` that exercises the freeform
path end-to-end using a mock LLM stub or fixture (no live API call required —
use a pre-recorded trajectory fixture if the harness supports it, or test
`validate_fields.py` in isolation for the deterministic portion); (2) a new
sprint case `docbuilder_fresh` in `aetheris/scripts/sprint.sh` that runs
`context_builder.exs` with a freeform request containing all required fields,
verifies `confirmed_context.json` is written and parseable, and verifies that
the run log is NOT written (PHASE D2 runs only after the orchestrator, not
after the context builder alone).

**Contract refs.**
- `aetheris-agents/CLAUDE.md` — conftest.py pattern; integration test
  `tmp_path` pattern; sprint script pattern (`../aetheris-agents/...` paths)
- `aetheris-agents/CLAUDE.md` Learning — m3 learning: sprint must reset
  accumulating fixtures (run log) for deterministic runs
- `agent-creation-guide.md` §"Sprint case" and §"Testing strategy"

**Touches.**
- `docbuilder/tests/test_context_builder_fresh.py` (new)
- `aetheris/scripts/sprint.sh` (new case `docbuilder_fresh`)

**Do not generate.**
- Do not modify `context_builder.exs` (t2 owns it).
- Do not modify `validate_fields.py` or `test_validate_fields.py` (t1 owns them).
- Do not modify the existing `docbuilder_context` sprint case.

**Runbook update rule.** The new sprint case is operational knowledge —
the runbook section for the context builder (m3 entry in `docbuilder/runbook.md`
and `docs/rig/runbook.md`) must be updated in t3 to document
`docbuilder_fresh` alongside `docbuilder_context`. t4 syncs higher-level docs;
the sprint-case entry is t3's responsibility.

**Done-check.**
```bash
# From aetheris-agents/ root
python3 -m pytest docbuilder/tests/test_context_builder_fresh.py -v

# From aetheris/
DOCBUILDER_TENANT=bitloka ./scripts/sprint.sh docbuilder_fresh
# Expected: confirmed_context.json written; parseable; run log unchanged.
```

**Claude-code prompt.**

> Read `aetheris-agents/CLAUDE.md` (all learning sections) and
> `agent-creation-guide.md` §"Testing strategy" and §"Sprint case" before
> writing any code.
>
> **Scope:** create `docbuilder/tests/test_context_builder_fresh.py` and add
> the `docbuilder_fresh` case to `aetheris/scripts/sprint.sh`.
>
> **Test file:** test `validate_fields.py` as the deterministic core of the
> freeform path (no live LLM needed). Cover at minimum: a complete freeform
> invoice input produces a valid normalised JSON (all required invoice fields
> present after normalisation); a request missing `client_email` produces an
> exit-1 error payload with `client_email` in the `missing` array. Use
> `tmp_path` for I/O. Import `validate_fields` via `sys.path.insert` +
> `subprocess.run` (script invocation pattern, not direct import of internals).
>
> **Sprint case `docbuilder_fresh`:** runs `context_builder.exs` with
> `DOCBUILDER_REQUEST` set to a freeform all-fields-present invoice request
> for a client name that does NOT appear in the run log (so the fresh path
> is exercised, not the recurring path). Before the run, truncate or reset
> `data/run_log.json` to `[]` (or copy a known-good seed that excludes the
> test client). After the run: assert `output/confirmed_context.json` exists
> and is valid JSON; assert `client_name` in the output matches the request;
> assert the run log was NOT appended (PHASE D2 runs only when the
> orchestrator runs). Emit `ok` / `fail` per the sprint.sh convention.
>
> Both the runbook entries for `docbuilder_fresh` (in
> `docbuilder/runbook.md` and the m3 section of `docs/rig/runbook.md`) must
> be added in this ticket.
>
> **Touches:** `docbuilder/tests/test_context_builder_fresh.py`,
> `aetheris/scripts/sprint.sh`, `docbuilder/runbook.md`,
> `docs/rig/runbook.md` (m3 section only — add `docbuilder_fresh` row).
>
> **Do not generate:** any other file. Do not touch `context_builder.exs`
> or `validate_fields.py`.
>
> Run the done-check and include its full output at the top of the review
> packet. Implementation notes required — commit to
> `docbuilder/docs/milestones/m-docbuilder-m4-t3-implementation-notes.md`.

---

### t4 — Runbook and docs update

**Scope.** Sync all milestone-level docs to reflect the completed m4 work:
`docbuilder/docs/milestones/m-docbuilder-m4.md` milestone summary section
(what shipped, what was deferred, open items); the m4 section in
`docbuilder/runbook.md`; the m4 entry in `docs/rig/runbook.md` (docbuilder
module section); and the capability matrix `docs/capability-matrix.md`
(new script row for `validate_fields.py`). No code changes. Write the
milestone summary based on implementation notes from t1–t3, not from
the diffs. Run the drift checker to confirm zero FAIL.

**Contract refs.**
- `milestone-methodology.md` §7 (milestone-end ritual) and §8 (sync rules)
- `aetheris-agents/CLAUDE.md` — definition of done / doc-sync; drift checker
  invocation
- `milestone-methodology.md` §9 anti-pattern: "Recovery sessions are where
  doc-first discipline slips" — re-verify canonical-doc sync explicitly

**Touches.**
- `docbuilder/docs/milestones/m-docbuilder-m4.md` (milestone summary section,
  appended)
- `docbuilder/runbook.md` (new m4 section)
- `docs/rig/runbook.md` (docbuilder module section — m4 entry)
- `docs/capability-matrix.md` (new row: `validate_fields.py`)

**Do not generate.**
- Do not modify any `.exs` agent file or `.py` script.
- Do not modify `CLAUDE.md` learning sections (learning promotion is a
  separate human-approved step per methodology §7; it is not part of t4).
- Do not modify the sprint.sh case (t3 owns it).

**Runbook update rule.** This ticket is the runbook ticket. All runbook
sections must be complete before t4 is marked done.

**Done-check.**
```bash
# From aetheris-agents/ root
python3 scripts/drift_check.py
# Expected: 0 FAIL, 0 WARN. (The capability matrix check should now include
# validate_fields.py — confirm it appears in the PASS output.)

# Verify the milestone summary section exists in the doc:
grep -c "## Milestone summary" docbuilder/docs/milestones/m-docbuilder-m4.md
# Expected: 1
```

**Claude-code prompt.**

> Read `aetheris-agents/CLAUDE.md` §"Definition of done — doc sync" and
> `milestone-methodology.md` §7 and §8 before making any changes.
>
> **Scope:** doc-only updates for m-docbuilder-m4. No code.
>
> 1. Read implementation notes from
>    `docbuilder/docs/milestones/m-docbuilder-m4-t{1,2,3}-implementation-notes.md`.
>    Append a `## Milestone summary` section to
>    `docbuilder/docs/milestones/m-docbuilder-m4.md` covering: what shipped
>    (validate_fields.py, context_builder.exs step-3b, tests + sprint case),
>    what was deferred (interactive confirm/amend, multi-round clarification),
>    surprises from implementation notes, open items for m5.
>
> 2. Add an `### m4 — freeform NL field extraction` section to
>    `docbuilder/runbook.md`. Document: what the freeform path does (extract →
>    validate → one-round clarification → confirmation gate); the
>    `docbuilder_fresh` sprint case; the output files added
>    (`raw_extraction.json`, `validated_extraction.json`); common failure modes
>    (validate_fields.py exit 1 — check error payload at
>    `output/validated_extraction.json`).
>
> 3. Add the m4 entry to the docbuilder module section of `docs/rig/runbook.md`
>    (one paragraph, mirrors the m3 entry style).
>
> 4. Add `validate_fields.py` to the Docbuilder scripts table in
>    `docs/capability-matrix.md` with purpose:
>    "Validate and normalise a raw extracted-field JSON against the context
>    schema; exits 1 with a structured error payload if required fields are
>    missing or values are malformed (m4)."
>
> **Touches:** the four files listed above only.
>
> **Do not generate:** any `.exs` or `.py` file. Do not edit CLAUDE.md
> (learning promotion is separate).
>
> Run the done-check and include its full output at the top of the review
> packet. Implementation notes required — commit to
> `docbuilder/docs/milestones/m-docbuilder-m4-t4-implementation-notes.md`.

---

## Milestone summary (close — t4, 2026-06-25)

**m4 is done (t1–t4).** The context builder's fresh path now turns a freeform request
("a formal quote for Acme Corp, 40 days at £1,200/day, …") into a valid
`confirmed_context.json` without a prior run — complementing the m3 "same as last month"
path.

**Shipped:**
- t1 — `validate_fields.py`: deterministic validate + normalise of a raw extracted-field
  map; exit 0 → normalised context, exit 1 → `{missing,invalid}` payload (no partial).
  20 tests.
- t2 — `context_builder.exs` step-3b: extract → `validate_fields.py` → write
  `confirmed_context.json` (exit 0) / self-correct once → clarify-and-stop (exit 1).
  Recurring path + confirmation gate unchanged.
- t3 — `test_context_builder_fresh.py` (3) + `docbuilder_fresh` sprint case (builder-only;
  resets run_log to `[]`; asserts context written + run log not appended) + runbook entries.
- t4 — docs sync: milestone summary, full m4 runbook sections (`docbuilder/runbook.md` +
  `docs/rig/runbook.md`), capability matrix (`validate_fields.py` → docbuilder 2 agents /
  22 scripts; repo total 25 / 60).

**Two accepted divergences (recorded in the doc, per the m3 doc-divergence learning):**
- **`amount_due` kept as a display string** (validated as money, not coerced to float) —
  it is substituted verbatim into the rendered invoice; coercing would regress
  "$1,000.00" → "1000.0". Only `unit_price`/`line_item_qty` (extraction intermediates) →
  numeric. (D1 / t1 review.)
- **Single-shot self-correction**, not an in-run interactive wait — `mix aetheris run` has
  no human-reply channel and `ask_human` is intentionally excluded (identical to the m3
  confirmation gate). The "one round" is a re-read of the request; a still-absent field →
  one clarifying message + stop; the operator re-runs with the field. (D2 / t2 review.)

**Deferred:** interactive confirm/amend loop and multi-round clarification (need a
conversational harness); conversational template editing; new doc types/variants.

**Open items for m5:**
- A full *render-with-intermediates* end-to-end check (the `docbuilder_fresh` sprint is
  builder-only by design; the orchestrator ignoring unknown fields is the schema contract).
- `validate_fields.py` `CURRENCIES` allowlist is hardcoded (`{GBP,USD,EUR,AED,INR}`) —
  extend when multi-currency support broadens (t1 review F2).
- `test_context_builder_fresh.py` module docstring says "Integration tests" — a cosmetic
  tidy (they are non-integration script-CLI tests; t3 review F3).
- The `docbuilder_fresh` client-match assertion uses the default request's client name
  (t3 review F1).

**Single-shot pattern — promotion candidate.** The single-shot harness constraint has now
resolved an interactive-loop design question identically in m3 (confirmation gate) and m4
(clarification round). If it recurs, promote to CLAUDE.md as a standing instruction.

**Project-knowledge refresh (BL-002, human-owned):** `docs/capability-matrix.md` and
`docs/rig/runbook.md` changed — re-upload to the Claude.ai project and advance
`docs/project-knowledge-manifest.md` to clear the drift WARNs.

---

## Open questions carried from planning

1. **`invoice_number` for fresh invoice runs.** `resolve_last_run.py` generates
   the invoice number for recurring runs (`{FY}/{client_code}/{seq+1}`). For a
   fresh run, `validate_fields.py` must accept `invoice_number` as either
   present-in-request or missing. If missing from the request, the validator
   should include it in the `missing` array so the clarifying question prompts
   the operator — not silently default or fabricate it. This is the correct
   behaviour under D1 (no invention); confirm it is tested in t1.

2. **`client_code` derivation.** `client_code` is optional in the schema but
   drives the invoice sequence in recurring runs. For a fresh run the operator
   may not know it; the fresh path should accept absence and pass through
   whatever the operator supplies. Confirm `validate_fields.py` does not
   require it. If it does require it, that is a blocking t1 finding.

3. **`raw_extraction.json` in `.gitignore`.** `output/` is already gitignored.
   Confirm with `docbuilder/.gitignore` — no action needed if already covered.
