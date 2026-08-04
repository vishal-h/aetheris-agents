# BL-073 — "View report": discover and open a run's artifacts (implementation notes)

Discover + open, nothing more. One new Tauri command (`harness_run_artifacts`), one hook, one
control. No harness change, no new event type, no cloudcost strings in Rig.

These notes carry the shape findings that changed the design, the one the ticket did not
anticipate, and what is proven versus owed.

---

## The resolver

`harness.rs` → `run_artifacts_with(conn, run_id, exists)` behind
`harness_run_artifacts(run_id) -> Vec<RunArtifact>`.

1. `runs.config_json` → `sandbox_path`. Absent → empty answer, not an error.
2. `SELECT payload_json FROM events WHERE run_id = ? AND type = 'tool_result' ORDER BY seq`.
3. Per payload, four fallible hops: `output` (string, MCP/exec key) → `JSON.parse` →
   `.stdout` (string) → `JSON.parse` → any JSON value. Any failure yields no artifact.
4. **Recursively** scan that value's *string values* for document extensions.
5. Resolve relative paths against `sandbox_path`; dedup; **verify existence**; return what survives.

`exists` is injected so the gate is testable without writing files; production passes
`Path::exists`.

### Why value-scanning, not key-matching

cloudcost puts its report under `file`; docbuilder puts its under `renamed` inside a **list** of
`{original, renamed}` objects. Keying on `file` is cloudcost-specific and finds nothing in
docbuilder — precisely the failure the row warned would leave the control permanently absent on the
case that proves it generic.

Extensions: `.html .htm .pdf .docx .xlsx .pptx .csv .md .xml`, derived from what the generators
actually emit (cloudcost `.html`; docbuilder `.xlsx`/`.docx`/`.pdf`) plus margin. `.json` is
deliberately excluded — every pipeline's intermediates are `.json`, which is exactly what must not
be offered as "the report".

A useful accident of extension matching: cloudcost's render result carries
`template: /…/cloudcost/templates/report.html.j2` beside the artifact. It ends `.j2`, so it is
excluded without needing a template-specific rule.

---

## The finding the ticket did not anticipate

Docbuilder's `rename_output` stdout is a **JSON list** of `{original, renamed}` pairs — both fields
are document paths, so value-scanning yields **six** candidates for a three-document run. The
`original` files no longer exist: they were renamed away by the step that reported them.

Verified on disk for `docbuilder-orch-wFwf_g`:

```
absent  output/invoice_v1.xlsx                    ← `original`
EXISTS  output/xyz_inc_invoice_30-Jun-2026.xlsx   ← `renamed`
absent  output/invoice_v1.pdf
EXISTS  output/xyz_inc_invoice_30-Jun-2026.pdf
```

**The existence gate resolves this for free.** It was specified (Decision C) to make the overlay
case fall out without special-casing; it also drops stale intermediate names without the resolver
knowing what `original` and `renamed` mean. Had the gate been client-side or absent, "offer the
set" would have shown six entries, three of them dead links — the exact outcome the row forbids.

That is the argument for keeping existence server-side rather than treating it as a UI nicety:
the same mechanism covers overlays, renamed-away intermediates, deleted output directories, and
anything else that makes a recorded path stale, none of which the resolver has to enumerate.

---

## Decisions

| # | Decision | Note |
|---|---|---|
| A | Offer the set, never silently pick one | 1 artifact → plain "View report"; >1 → "View reports (N)" with a filename list, each opening externally |
| B | Guard every hop | four shapes; `result`-carrying native tools are skipped rather than parsed — they produce no documents |
| C | Resolve + existence-gate server-side | subsumes the overlay guard; no `overlay_base_dir` branch exists in the code |
| D | Open external via Tauri shell | never `innerHTML` — the HTML embeds provider data even though `render_report` escapes it |

The frontend receives only existing artifacts, so an empty list means "render nothing". The hook
degrades errors to empty for the same reason: a failed lookup must hide the control, not offer one
that cannot open.

---

## Verification

**Unit — 8 cargo tests, in-memory DB, injected `exists`:**

| test | proves |
|---|---|
| `cloudcost_shape_yields_only_the_report` | `.json` intermediate excluded; `template` (`.html.j2`) not matched |
| `docbuilder_list_shape_is_found_by_recursion` | list-shaped stdout found; 4 candidates before the gate |
| `existence_gate_drops_the_renamed_away_originals` | 4 → 2, keeping only `renamed` |
| `overlay_run_yields_nothing_via_the_existence_gate` | overlay resolves to empty, no overlay branch |
| `every_malformed_hop_degrades` | `result`-not-`output`, null output, non-JSON output, non-JSON stdout, unparseable payload, NULL payload, `.json`-only — all empty, none error |
| `the_degrade_test_is_not_vacuous` | the **anti-vacuity arm**: the same harness *does* find an artifact in a well-formed payload |
| `duplicates_collapse` | first-seen dedup |
| `missing_config_yields_empty` | no config → empty, not an error |

The anti-vacuity test is the load-bearing one. `every_malformed_hop_degrades` asserts an empty
result, and would pass identically against a resolver that never finds anything at all — so the
next test feeds the same store a good payload and requires exactly one artifact.

**Live — real store, real filesystem** (`cargo test -- --ignored`, needs `AETHERIS_DB_PATH`):

```
live cloudcost   → ["cloudcost_report_2026-08.html"]
live docbuilder  → ["xyz_inc_invoice_30-Jun-2026.xlsx",
                    "xyz_inc_invoice_30-Jun-2026.docx",
                    "xyz_inc_invoice_30-Jun-2026.pdf"]
live no-artifact → 0 artifact(s)
```

It asserts no returned filename contains `_v1.`, so the existence gate dropping the originals is
checked rather than assumed.

**Gates:** `cargo test --lib` 29 passed · `bun run lint` clean · `bun run build` clean ·
`drift_check --strict` 8 PASS / 0 FAIL — commands 48 → 49 and §4 structs 10 → 11 (56 fields), both
validated against `specs.md`, which carries the `harness_run_artifacts` entry in this commit.

**Owed: the open itself.** `open()` from the Tauri shell plugin cannot be exercised headless. That
the correct absolute path is produced and verified to exist is proven; that the OS opens it is a
click-through owed to the operator. Same split as BL-086's derivation-vs-badge.

---

## Scope

Explicitly not built, per the row's scope guard: inline HTML render, section navigation,
orphan/optimization panels, live refresh. `stageLabel.ts` (BL-086) sits beside this rather than
being reused — it answers "which stage is this step", this answers "which results carry a document
path", and the walks differ. They read the same events and should stay consistent.

The deferred alternative — a run that *formally records* its artifact path — remains the cleaner
long-run answer and is untouched here; it would need a harness change and probably an event-union
change. Worth settling before provider three if recording is wanted over scraping.
