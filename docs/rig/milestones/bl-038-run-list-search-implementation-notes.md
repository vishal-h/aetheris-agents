# BL-038 — Run list: server-side search + honest window disclosure — implementation notes

Single-repo (`aetheris-agents/`). Rig reads the harness DB; no `../aetheris/` source change.

Applied at agents HEAD `d6baeba`, harness `da25e01` (both trees clean at start).

## What landed

**Backend — `rig/src-tauri/src/commands/harness.rs`.** `harness_list_runs` takes a new
`search: Option<String>` and returns `RunListResult { runs: Vec<RunSummary>, total_count: i64 }`.
`RunSummary`'s fields are untouched. The query core moved into `pub(crate) fn list_runs(conn,
limit, search)` so it is reachable from `cargo test` — a `#[tauri::command]` taking `State` is
not — and the command is now a two-line wrapper.

**Frontend.** `useRunList({ limit?, search? })` returns `RunListResult` and keys its effect on
both arguments. `RunList.tsx` gains a 250 ms-debounced search input and a "Showing N of M runs"
disclosure. `DiffView.tsx` reads `.runs` off the new shape (its picker keeps the same windowed
list). No client-side filtering layer.

**Docs.** specs §4 gains the `RunListResult` block plus the search/escaping semantics on the
command; specs §5 gains the TS `RunListResult`; architecture.md's run-inspection data-flow block
described the old command shape and now describes this one.

## Decisions

**One `WHERE`, shared by both queries, with `NULL` as "no search".** The filter is a single
`const RUNS_WHERE` reading `WHERE (?1 IS NULL OR r.label LIKE ?1 ESCAPE '\' OR r.run_id LIKE ?1
ESCAPE '\')`, interpolated into both the row query and `SELECT COUNT(*)`. The searched and
unsearched paths are therefore the *same* SQL with the same binding rather than two clauses
that can drift apart, and "empty search ≡ no search" holds by construction rather than by two
code paths agreeing. `search_pattern` normalises absent / `""` / whitespace-only to `None`.

**Raw `r.label` / `r.run_id`, not the `COALESCE(...) AS label` alias.** An unlabelled run has
`label IS NULL`, and `LIKE` never matches NULL — the `r.run_id` arm is the only thing that finds
it. `demo-01` (NULL label, 879th of 896 by `started_at DESC`) is the recorded instance and is
the live test's subject.

**Both reads inside one deferred read transaction.** The ticket's stated invariant is that the
count cannot disagree with the rows; one *command* does not deliver that on its own, because two
statements on one connection can still straddle a harness `INSERT`. `conn.unchecked_transaction()`
pins one snapshot for both. The connection is opened `SQLITE_OPEN_READ_ONLY`, so this takes a read
snapshot only and the implicit rollback on drop is a no-op — verified against the real store
(`priv/aetheris.db`, 896 runs) by the live test arm, not just in-memory.

**LIKE metacharacters are escaped** (`%`, `_`, `\` → `ESCAPE '\'`). This is an addition to the
ticket's sketch, made because the invariant it serves is the ticket's own: `run_zS6XSQ` is a real
run_id, and unescaped its `_` matches any character, while a lone `_` or `%` matches the whole
store. A silently *wider* result set is indistinguishable from a correct one, which is the class
BL-038 exists to remove — not to relocate into the search box. Case-insensitivity is SQLite's
default ASCII `LIKE` behaviour and is left alone, as specified.

**The loading gate no longer unmounts the pane on refetch.** `if (runList.loading)` became
`if (runList.loading && !runList.data)`. The old form was harmless when the list fetched once;
with search it would tear down the toolbar — and the focused search box with it — on every
debounce tick. Only the first load shows the skeleton.

**The badge has two forms, because the status filter is client-side.** `statusFilter` narrows the
loaded rows in the browser, so quoting only the server's numbers while the table shows fewer rows
would be its own confidently-wrong line. Unfiltered: `Showing {loaded} of {total} runs`. Filtered:
`Showing {filtered} of {loaded} loaded · {total} runs in store`. While searching, "runs" becomes
"match"/"matches". The empty state likewise distinguishes *no match in the whole store* from *no
runs at all* from *status filter hid the matches*.

**Nothing pulled in from adjacent rows.** No pagination UI, no client-side filter, no
`RunSummary` field change, no label real-vs-fallback work (BL-037), no `formatCost`/`formatTokens`
extraction — `RunList.tsx` is touched but adds no fourth formatter site, so BL-035 does not fire.

## Tests

Seven unit tests in `commands/harness.rs` over an in-memory SQLite store (12 recent labelled runs
+ one old unlabelled `demo-01`), plus one `#[ignore]`d live arm against `AETHERIS_DB_PATH`.

The load-bearing test is `search_reaches_a_run_outside_the_window`: it asserts `demo-01` is
**absent** from the unsearched list at the test limit *before* asserting the search returns it. A
search test against a run already inside the window passes identically whether or not the search
term is used at all. Both arms were mutation-checked (see the review packet): with `search_pattern`
stubbed to `None`, five tests fail including this one; with the window widened to cover the store,
the precondition assertion fires with the run ids it saw.

The live arm panics rather than skips when `AETHERIS_DB_PATH` is unset — a check that quietly
passes when it did not run is worse than no check. It is `#[ignore]`d so a machine without the
harness store still gets a green `cargo test`.

## Open / forwarded

**specs §5 (TypeScript Interfaces) is unchecked and its `RunSummary` is stale** — it lacks
`last_event_at`, `total_cost_usd`, `total_input_tokens`, `total_output_tokens`, all of which
`src/hooks/types.ts` has carried since BL-004. check 9 (`command_fields`) parses §4 only, so the
TS half of the same contract drifts silently. Out of BL-038's scope; the new `RunListResult` was
added to §5 so this ticket adds no drift of its own. Filed as **BL-058** rather than left as prose.

**Manual GUI pass gates merge** (BL-029 precedent — Rig has no frontend test runner, BL-017).
Two arms: type a run_id fragment for an out-of-window run and confirm it appears; clear the box
and confirm the "N of M" badge shows the truncation.
