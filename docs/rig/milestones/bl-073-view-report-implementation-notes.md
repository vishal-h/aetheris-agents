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
| D | Open external | never `innerHTML` — the HTML embeds provider data even though `render_report` escapes it. **Superseded at r2:** the open moved from the frontend shell plugin to a Rust command; see the reopen section. |

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

**Owed: the open itself.** ~~`open()` from the Tauri shell plugin cannot be exercised headless.~~
**Superseded at r2** — and this is where the residual turned out to be hiding a defect rather than
merely an unverified step: the frontend `open` could not have worked at all. See the reopen section.

---

## Scope

Explicitly not built, per the row's scope guard: inline HTML render, section navigation,
orphan/optimization panels, live refresh. `stageLabel.ts` (BL-086) sits beside this rather than
being reused — it answers "which stage is this step", this answers "which results carry a document
path", and the walks differ. They read the same events and should stay consistent.

The deferred alternative — a run that *formally records* its artifact path — remains the cleaner
long-run answer and is untouched here; it would need a harness change and probably an event-union
change. Worth settling before provider three if recording is wanted over scraping.

---

## Reopen — the open failed; server-side open (BL-073 r2)

**The bug.** Clicking "View report" threw a Tauri shell-scope error:

```
Scoped command argument at position 0 ... failed regex validation
^((mailto:\w+)|(tel:\w+)|(https?://\w+)).+
```

`tauri-plugin-shell`'s frontend `open` is **URL-scoped**. It accepts `mailto:`, `tel:` and
`http(s)://` and rejects everything else — so a local filesystem path, which is the only kind of
path this feature produces, could never work. The first implementation handed `artifact.path`
straight to it.

This is a case where the derivation being proven made the surface look safer than it was: the
resolver was tested end-to-end against real files, and every one of those tests passed while the
button could not open anything. The offline proof covered "is the path right", never "can this
primitive take a path at all".

**Not fixed by widening the scope.** Adding a file-path pattern to `shell:allow-open` would let the
frontend open *any* local file, which discards the whole point of the existence-gated resolver —
the invariant that only vetted artifacts are openable. The allowlist would become the weakest link
in a feature whose entire design is about not offering paths that shouldn't be opened.

**Fixed by moving the open into Rust.** New `harness_open_artifact(run_id, path)`:

1. Re-runs `run_artifacts_with` for that run — the same scrape, the same existence check.
2. Refuses unless `path` is in that freshly computed set. This covers both "never an artifact of
   this run" and "was one, but is gone now".
3. Opens with `open::that_detached`.

So the command **cannot open an arbitrary file even when asked to**, and there is no frontend
primitive taking a raw filesystem path at all. The shell plugin's scope is untouched.

`open` 5.3.5 was already vendored transitively via `tauri-plugin-shell`; declaring it directly adds
no download (`cargo build --offline` succeeds).

The frontend's `openArtifact` now calls the command and surfaces failures inline rather than
swallowing them — a control that silently does nothing is worse than one that says why.

**Acceptance.** The exact server-side path the button calls, run against real artifacts including
the real `open::that_detached`:

```
opening /home/it/…/cloudcost/output/aws/cloudcost_report_2026-08.html
opening /home/it/…/docbuilder/output/xyz_inc_invoice_30-Jun-2026.pdf
guard ok: arbitrary path not in allowed set
test result: ok. 3 passed
```

Both launched in the OS handler — the operation that previously threw. The guard arm asserts an
arbitrary local path (`/etc/hostname`) never appears in the allowed set.

**Still owed: the in-app button click.** The test exercises the command's code path, not the React
`invoke`. What that leaves unverified is only the wiring — command name and argument casing
(`{ runId, path }`, camelCase per the Tauri convention, confirmed by inspection). Rig needs a
rebuild before eyeballing; Tauri does not hot-reload the Rust side.

Doc-sync: `specs.md` §4 carries `harness_open_artifact` in the same commit; `drift_check` counts
49 → 50 commands.
