# m1-cloudcost §t4 — review (r0, approve)

**Ticket:** m1-cloudcost §t4 — custom cloudcost report template + render (local file).
**Commit reviewed:** `e1c26d5`. **Reviewer:** claude-ui. **Date:** 2026-07-29.
**Verdict:** approved, push. No blocking finding; three non-blocking (one a code fix folded
before push, two forwarded), plus a gate-table omission.

Reviewer's message, verbatim:

---

Reviewed the whole packet — read `render_report.py`, the full template, and all 30 tests, and swept by invariant. The render-only discipline is genuinely enforced, and the visual-review diligence (rendering to PDF and reading it, which is how the flex-`gap` header defect surfaced) is the right call for a human-facing deliverable. Approving, with findings — the notable one is an **incomplete sweep in claude-code's own finding #1.**

Independently confirmed:
- **Render-only holds.** The mutation test sets six figures to values their own components contradict (`grand_total`, coverage, a band subtotal, a candidate saving, the delta) and all six reach the HTML — a renderer that recomputed anything would print the consistent value. The import guard is positive-controlled (it verifies its own detector fires on a real importing sibling first), so it can't pass by matching nothing. No clock imported.
- **F2 (new-provider caveat) is adjacent, structurally.** The test asserts `figure_index < caveat_index < first_table_index`, not mere presence. Verified in the template — the caveat sits inside the headline block.
- **Autoescape, determinism, section-degrade, multi-currency withholding** all check out; the `<script>` payload escapes 5×, none raw.

Findings:

**1 — claude-code's finding #1 is real but under-scoped: the cross-currency sum is in four places, it named one.** `month_on_month.current_total`/`delta_amount` summing across currencies with `currency: null` is correct — but the *same* unhandled cross-currency sum also lives in `orphans.by_band[].monthly_saving_estimate` + `orphans.totals.monthly_saving_estimate`, and in `tag_coverage.untagged_monthly_cost_estimate`. Only `cost_summary.grand_total` actually withholds. So the class is one-handled / three-unhandled, not one/one. The template mitigates by rendering the aggregates unit-less (`nz("")`), which is the honest render-only response — but the fix belongs in t3, and it must cover all three or it repeats the "named 3 spots when there were 6" failure. All latent while m1 is DO-only single-currency; it becomes live at fan-out. File the whole set in one executor-visible place (milestone §Open items / a backlog row), the way the recency bound was filed — not only in t4's notes.

**2 — `--pdf` with an absent binary exits 1 / `partial`, which contradicts the notes' "a note, not a failure" — and the test that carries that name doesn't check it.** `write_pdf`'s warning lands in `render_warnings`, which flips `status` to `partial` and returns 1, even though the HTML (the deliverable) was written. `test_a_missing_pdf_binary_is_a_note_not_a_failure` calls `write_pdf` in isolation and asserts the tuple — it never runs the CLI or checks the exit code, so the "not a failure" claim is unverified at the level it's made, and the actual run-level behavior is the opposite. The orchestrator never uses `--pdf`, so it's non-blocking — but since t4 is held, fold the one-liner: don't let a missing *optional* companion flip the stage's status (exit 0 + the visible note), and add a CLI-level test that asserts exit 0. Otherwise correct the prose.

**3 — refine claude-code's finding #2.** The `excluded` (`keep=true`) block being invisible is *correct* — those are resources the user said to keep, so suppressing them from the report is intended, not a gap. Only the `reported` half (untagged-in-tagged-account governance flags, with their own evidence) is a genuine forward: decide whether the report should carry t2's reported-only list, or whether "tag coverage + top untagged spenders" (which t3/t4 do render) is the intended governance surface. The milestone's stated report sections don't include a governance-flags section, so this isn't a done-when gap — a scope question for t3-fast-follow / P2.

**Minor:** `mix dialyzer` is absent from the §1f gate table — t4 is Python-only so it's unaffected, but name it (run green, or stand it on t3's result), don't leave it silently missing. The count is clean this round (156 = 25+54+47+30, t1 correctly 25).

What I did **not** do: run the 156-suite or the mutations, and I can't open the HTML myself — I read the template source and the tests, and take the page-by-page visual review as reported. Since this HTML is the milestone's human-reviewable deliverable, you may want to open both files (`cloudcost_report_2026-07.html` and the first-run one) yourself before t5 — a report's layout correctness rests on eyes, not assertions, and the flex-`gap` catch shows that matters here.

**t4 verdict: approved, push** — optionally folding finding #2's one-liner first since it's held. t5 is the last ticket: orchestrator `.exs` + sprint case + the real-bill end-to-end (and the ≥1-orphan done-when, which still needs Prerequisite 2 — an orphan planted on the live account). Two things gate t5's live half that aren't code: **the token** (`CLOUDCOST_DO_TOKEN` in a fresh login shell) and **a genuine orphan on the account**. Confirm both before the end-to-end, or t5 builds green offline but can't close its done-when. Say the word and I'll hand you the t5 prompt.

---

## Disposition

| Item | Where it landed |
|---|---|
| **F1** — cross-currency sweep under-scoped | Re-verified against source before filing rather than taken on the reviewer's word (`compose_report_data.py:220` handled; `:333–342`, `:419`, `:487`, `:500` not). The reviewer's count is right; stated here as **one handled / four unhandled** because `mom_delta` carries three figures from one sum and is a fourth site beside the three named. Filed in full at `cloudcost/milestone.md` **§Open items carried forward** — the executor-visible place, as asked, with the line cites, the "must cover all four" instruction, and the note that t4's mitigation is render-side only. Also recorded in t4's notes as the *sweep* lesson rather than the defect. |
| **F2** — `--pdf` exits 1 where the prose says it does not | **Fixed in code, since t4 is held.** The PDF note moved out of `render_warnings` into its own `pdf_note` summary field; the stage stays `ok` / exit 0. New CLI-level test `test_a_missing_pdf_binary_does_not_fail_the_run` runs `--pdf` with an empty `PATH` and asserts the exit code — the level the claim is made at. Mutation-checked: folding the note back into `render_warnings` reddens exactly that test and nothing else. The unit test that mis-carried the name is now `test_write_pdf_returns_a_note_when_the_binary_is_absent`, which is what it actually asserts. |
| **F3** — `excluded` is intended, only `reported` is a forward | Accepted; the reviewer is right and t4's original forward was wrong about the second half. `cloudcost/milestone.md` §Open items now files the `reported` half as a **scope question** (governance-flags section vs. the tag-coverage surface already rendered), states it is not a done-when gap, and states that `excluded` staying invisible is correct. t4's notes carry the same correction. |
| **Minor** — `mix dialyzer` missing from the gate table | Run and reported, not stood on t3's result. |
| Reviewer's request to open both HTML files before t5 | **Discharged by the human, 2026-07-29 — passed.** Neither claude-code nor claude-ui could do it: the files live in the build workspace and the reviewer sees only relayed packets. The human confirmed the figures trace back through the pipeline (172.21 reconciles against 168.50 + 3.71 + 0.00; MoM +14.21 / +8.99 % off June's 158.00; the untagged subtotal 32.58 correctly excludes the one tagged resource; band subtotals 14.38 / 13.20 / 24.00 = 51.58 match t2), that provider strings are escaped rather than injected, that all six sections are present and ordered, and that the flex-`gap` fix held. **Boundary recorded, not glossed:** the look covered the N=1 DO report — the only path m1 ships. The new-provider caveat and the multi-currency rendering have been rendered and tested but never browser-viewed; filed at `cloudcost/milestone.md` §Open items for the fan-out ticket. |

**No change to the template or to any figure the report renders.** F2 is the only code change
(`scripts/render_report.py`, the PDF-note routing, plus its test); F1 and F3 are forwards.
