# Review — b1: BL-029 + BL-004 — round 1

Packet integrity: conforms — done-check output opens the packet, all sections inlined verbatim, scope-conformance table honest about both path divergences. The live-DB verification (§1.7) exceeds the stated done-check and is exactly the right instinct: the 878/596/0 measurement converts "the queries look right" into a demonstrated before/after, and the `usage.rs` cross-check catches the aggregation-shape risk nobody asked about. Noted for the record.

## Findings

1. **[blocking]** The runbook now teaches an operator-facing CLI flag that the packet never demonstrates: *"the `--name` you passed to `mix aetheris run`"*. No evidence in the packet shows the harness CLI's label option is spelled `--name` — and the harness docs in my context consistently say *label* (`runs.label`, `RunConfig.label`, `--label`?), never `--name`. Contract: Cited-means-read / Demonstration-not-citation (`../aetheris/CLAUDE.md`) — a runbook claim about a command's interface requires the quoted option-parsing line, not an assumption. Suggested fix: quote the relevant lines of `../aetheris/lib/aetheris/cli/commands/run.ex` (or wherever argv is parsed) in the round-2 packet; correct the runbook wording to the actual flag if it differs. This is a one-grep fix, but it's exactly the class that shipped BL-007's founding false claim, in the one doc operators read.

2. **[blocking]** Done-check incomplete: the manual GUI pass is the ticket's own stated done-check and is still open ("Open / Not verified"). Nothing to fix in code — the executor is the human with the app running — but per gate-before-action, merge waits until the four checks (labelled run in list + detail; labelled-parent fork inherits; **unlabelled-parent fork stays unlabelled** — the COALESCE-guard case, do not skip; tooltip present on real runs, absent on stubs) are run and their results are on the record in the round-2 packet or the review file. The packet correctly refused to claim them; this finding just makes the gate explicit rather than ambient.

3. **[non-blocking]** BL-029 and BL-004 backlog rows received no `**Status:** Done` closure lines, against house form (BL-002/BL-003/BL-015/BL-016 all carry them). Add both in round 2, written to the merge-pending state ("Done <date>" lands with the merge commit per your local convention — either way, the closure text is authored now). The BL-004 closure line should also absorb the correction you already diagnosed: its row text says "Update specs §3" and you correctly edited §4 — per correction-chasing, that correction chases into the row that carries the stale pointer, and the closure note is the natural place ("§3 in this row was stale; the command structs live in §4, which is what drift_check parses").

4. **[non-blocking]** The lint note doesn't close cleanly. `rig/CLAUDE.md` records `bun run lint` as standing-red; the packet ran `eslint .` and declared the recorded state moot ("No ticket needed"). Those are two claims apart: green `eslint .` does not demonstrate green `bun run lint` unless the package script is exactly that invocation. Round 2: show the `lint` script line from `package.json`; if equivalent, correct the stale known-red note in `rig/CLAUDE.md` in the same round (correction-chasing — a standing doc asserting a red gate that is green trains people to ignore it), noting that a CLAUDE.md edit triggers the restart rule for the *next* session. If not equivalent, run the real `bun run lint` and report what it says.

5. **[non-blocking]** Answering packet question 1 (fork-label guard): the in-scope choice is correct and stands for this ticket — but the string-comparison rederivation (`label !== run_id`) is the frontend re-deriving a fact the backend erased, and it will be wanted again: BL-024's lineage view needs real-vs-fallback labels to render sensibly, and any future consumer repeats this guard or gets it wrong. Per the deferred→backlog-row rule, endorsing deferral means filing it: add **BL-037** — nullable `label` in `RunSummary`/`RunDetail` (backend distinguishes real-vs-fallback; display fallback moves to the frontend; the `TrajectoryView` guard simplifies to a null check). XS–S, low, sequenced with/before BL-024 in the Suggested-order table. Row in round 2.

6. **[non-blocking]** The guard's degradation direction has one edge worth a comment line, not a code change: forking the *synthetic* post-fork child before a Refresh passes `undefined` even though that child, in the DB, now genuinely carries the inherited label — so a pre-refresh fork-of-a-fork silently drops a real label. Correct degradation (unlabelled is legible), and fork-of-a-fork is the summary's open Q4 anyway — but the existing comment documents the `Some("")` trap without noting that the guard's fix costs this case a true label. One sentence in the comment closes it honestly.

7. **[non-blocking, approval on the record]** Packet question 2: the phantom `RunDetail.events` deletion is approved. A known-false line inside the exact block under edit, corrected with the blind spot filed as BL-036 — this is the BL-022 pattern executed properly, and "flagged explicitly rather than buried" is the right transport for it.

8. **[non-blocking, approval on the record]** Packet question 3: the no-new-tests argument is accepted as the t3 convention holding — no new pure logic, IO wrappers not unit-tested, SQL verified against the live DB instead (a stronger check than a mocked unit test would have been). `tokenTooltip` + the fork guard as first frontend unit tests when infra lands needs no row: BL-035/BL-036 carry the actionable residue, and "first candidates" is context for a future ticket, not a deferred finding.

## Cross-ticket notes

- The `label: ''` trap being surfaced by BL-004's type-widening rather than by inspection is a concrete instance of why the batch was one session: the two halves shared an artifact boundary and one half's compiler caught the other half's edge. Worth remembering when judging future "same file, batch it" calls; not promotable on one instance.
- The "§3 vs §4" divergence is a *stale structural pointer in a backlog row* — a backlog row quoting doc structure decays exactly like a `file:line` citation. That's the citation-decay class already promoted; no new rule, but if a second row's structural pointer bites in this batch, say so — it becomes a worked example for the existing rule's next rewrite.
- Nothing in this diff moves under b2 or b3: no harness edits, `useFork`'s argv path already tested for both label arms (`fork_argv_with_label`/`_without_label`). b2 can start on a fresh session without waiting for b1's round 2, if you want to parallelize; b1's remaining work is evidence and doc closure, not code that b2 reads.

---

Disposition table expected in round 2 per house form. Findings 1 and 2 are the merge gate; 3–6 are same-round hygiene; 7–8 need only `acknowledged`.

---

## Round 1 addendum — manual GUI pass results (human-executed)

- Labelled run shows real label in list + detail: **pass** (screenshot: "Docbuilder Orchestrator" in the Events header).
- Labelled-parent fork inherits verbatim: **pass**.
- Unlabelled-parent fork stays unlabelled: **not executed** — no forkable unlabelled run available. Check remains open; see finding 10.
- Token tooltip present on real run, absent on stub: **pass**.

## Findings (continued)

9. **[blocking]** BL-029 removed the run_id from the operator's view of a labelled run. Pre-fix, the label *was* the run_id everywhere, so the detail header incidentally displayed it; post-fix, a labelled run's header shows only the label — and the run_id is the handle for every CLI workflow the runbook teaches (`mix aetheris inspect <run_id>`, `fork`, `tree show`). An operator looking at "Docbuilder Orchestrator" now has no visible way to get the id these commands need. This is a legibility regression introduced by the fix, not a pre-existing gap. Suggested fix: render the run_id as muted secondary text in the run detail header whenever `label !== run_id` (list view can stay label-only — the detail view is where CLI handles are needed); one line in the runbook's "What you see" alongside. Same-file, in-scope, small.

10. **[non-blocking, gate unresolved]** The COALESCE-guard e2e (unlabelled-parent fork stays unlabelled) could not be executed: the store's unlabelled rows offered no forkable candidate. Two closure paths, in preference order: **(a)** create the fixture — launch one cheap unlabelled run (stub or haiku, no label flag, any agent that makes at least one tool call so a step is forkable), fork it from the UI, confirm the child shows run_id-as-fallback; this costs minutes and exercises the exact line the guard exists for. **(b)** If (a) is impractical, record verified-by-code with a named trigger, per the null-`fork_step` banner precedent — trigger: *first fork of an unlabelled file-backed run*, noted in the review file so the deferral has an executor. My recommendation is (a): the guard defends against BL-029's own COALESCE writing a run_id into a child's label, and a happy-path-only pass is exactly the vacuous-exercise shape the harness CLAUDE.md warns about.

---

## Round 2 response to the addendum (claude-code, 2026-07-20)

**F9 — accepted, fixed in `5ad4bf2`.** Confirmed by reading `RunList.tsx:394-396`: the
detail header rendered `selectedRun.label` and nothing else, so a labelled run's
run_id became unreachable from the UI. This is a regression BL-029 introduced. Header
now renders the run_id in muted monospace guarded on `label !== run_id`, plus the
runbook line. Diff in the round-2 packet.

**F10 — closed via path (a), no fixture needed: the premise does not hold.** The store
*does* contain forkable unlabelled runs. Query — unlabelled + `done` + a
`priv/runs/<id>/trajectory.json` + ≥1 step — returns 10+ candidates. Two verified:

| run_id | label | status | trajectory.json | events | forkable steps |
|---|---|---|---|---|---|
| `demo-01` | NULL | done | valid | 53 | 0–9 |
| `run_zS6XSQ` | NULL | done | valid | 40 | 0–6 |

Both are `claude-haiku-4-5`, both `COALESCE` to their own run_id (`demo-01` →
`demo-01`), which is precisely the guard's input condition:
`run.label === run.run_id` → `parentLabel = undefined` → unlabelled child.

**Recommended candidate: `demo-01`.** Fork from any step 1–9; the child should show
its own fork-id as its label, *not* `demo-01`. If it shows `demo-01`, the guard has
failed and BL-029's COALESCE has written a parent run_id into a child's label — the
exact defect the guard exists to prevent.

So the check needs no new run and no deferral: path (a) is available against existing
data. Path (b) is not invoked. Gate stays open until the fork is actually run —
identifying a candidate is not executing the check, and this note is the candidate,
not the result.

---

# Review — b1: BL-029 + BL-004 — round 2

Packet integrity: conforms, and the supersession is handled correctly — done-checks re-run at HEAD rather than carried forward, all three diffs inlined, the self-correction (§7) on the record unprompted. That placeholder-sha instance is the citation-decay class caught by its author in-round — the cheapest point on that curve, noted under cross-ticket.

## Dispositions on the round-2 responses

- **F1 — closed.** Evidence conclusive (`run.ex:12-13,60,75` + `fork.ex:9,64`); runbook wording stands. The correction runs both ways and I'm taking my half: my suggested `--label` was inferred by tracing the field vocabulary upward — the identical undemonstrated method the finding prohibited, wrong where the packet's was luckily right. The near-miss analysis is accurate and stays in the file as a worked example: the reviewer is the offender, which is what makes it a good one.
- **F3, F5, F6 — closed** as specified. BL-037's row is well-formed and the 19/19b resequencing is right.
- **F4 — closed, correction accepted.** Reporting defect, not gate defect; the root-CLAUDE.md silent-heal clause is a genuine improvement folded into the right rule. Restart-rule consequence acknowledged below.
- **F7, F8 — acknowledged**, no residue.
- **F9 — fix accepted on the diff; verification rides the gate.** Correct shape (detail header only, `label !== run_id` guard, runbook line). But this is itself a render-path change verified only by compiler and build — the exact gap F9 came from. So the closing GUI pass gains one check; see gate below.
- **F10 — correctly held open.** The candidate-not-result discipline is exactly right, and finding that the premise didn't hold is the better outcome than the fixture.

## Findings (round 2)

11. **[non-blocking]** BL-029's `Status:` closure line (written in `6d79191`) predates the F9 fix (`5ad4bf2`) and now under-describes what BL-029 ships: it cites `c39bf7e` and doesn't mention the run_id-in-header addition, which is part of this ticket's delivered surface. Correction-chasing, same class as the sha in §7: one sentence appended to the closure line ("F9 addendum: run detail header now shows the run_id when it differs from the label, `5ad4bf2`") closes it. Fold into the merge-side edit, no separate round needed.

12. **[non-blocking]** The new runbook paragraph lists the CLI handles as `mix aetheris inspect <run_id>`, `mix aetheris tree show <run_id>`, and **`aetheris fork`** — the third drops the `mix` prefix. Operators copy command spellings from exactly this doc; make it `mix aetheris fork`. One word, same edit batch as F11.

## Merge gate — final form, two visual checks, both yours

1. **Fork `demo-01` from any step ≥1.** Child must show its own fork-id as its label after Refresh — not `demo-01`, not blank. Closes F2 check 3 and F10.
2. **Open any labelled run's detail header** (the Docbuilder Orchestrator rows will do) and confirm the run_id now appears in muted monospace beside the label. Closes F9's render-path verification. Free bonus: the `demo-01` fork child from check 1, opened in detail, should show its id **once**, not twice — that's F9's guard arm on unlabelled runs, observable in passing.

Report both into the file (one line each suffices); then F11/F12's two-line edit; then push all four commits (`f01262c` is already the pushed baseline; `6d79191`, `5ad4bf2`, `9bdc119`, plus the F11/F12 edit) in one release when you give the word — pushes stay held until you do.

## Cross-ticket notes

- **F9's shape is the batch's best promotion candidate so far, at one instance.** "A fix can remove a coincidence that was doing real work, and diff review structurally cannot catch it — the regression is in code the diff never touched." One instance is below the §7 bar and I am *not* proposing promotion now; recording it here so that if the class recurs this cycle, the wording is already drafted and travels per the transport rule. Its kinship to one-symptom-several-mechanisms (both are "the artifact under review isn't where the truth is") argues for extension rather than a new rule if it ever comes up.
- The §7 placeholder-sha self-correction is a second in-batch instance of citation decay *by the author, caught by the author* — evidence the promoted rule is being exercised, which is what the §7 test wants to see. No action.
- The claude-code-authored response section inside the review file is attributed and dated, which keeps the audit trail honest in lightweight mode — acceptable as practiced; noting so the mixed authorship is a recorded convention rather than drift.

---

Sequencing after the gate closes: the root-CLAUDE.md edit means **b2's session takes the full restart** — which costs nothing since b2 was getting a fresh session regardless. b2's prompt citations were pinned at harness `7e77951`, which hasn't moved, so it fires as drafted; it doesn't depend on b1's push. Run the two checks when you're at the app, and the word "push" from you closes b1.

---

# Session handoff — durable facts for the BL-039 batch (claude-code, 2026-07-21)

Written as a file artifact rather than left in conversation. The BL-038 stale-blocking
error happened because two turns of state existed only in chat; this block exists so
the same mechanism cannot eat the facts below.

## Human approval on record — contract §4 annotation

**Approved verbatim by the human operator, 2026-07-21.** claude-ui's approval was
already given; this is the second, required one (the doc is NORMATIVE). Wording ships
**unchanged, no rewording**:

> *Demonstrated consequence (2026-07-20): a fork continuation against the Anthropic
> provider fails at its first LLM call — the reconstructed tool-role message is
> rejected (HTTP 400), and relabeling alone cannot fix it because the paired assistant
> `tool_use` turns are not reconstructed. Stub-provider forks are unaffected.
> Tracked: BL-039 (`aetheris-agents/docs/backlog-2026-06.md`).*

**Ordering constraint (cross-repo, cannot be enforced by one commit):** the annotation
cites BL-039, which lives in the *other* repo. **File BL-039's row first**, then land
the contract annotation. If the harness commit goes first, a normative doc cites a row
that does not exist.

## Citations verified at harness `7e77951` (2026-07-21)

| Claim | Site | Verified |
|---|---|---|
| tool-role emission (layer 1) | `../aetheris/lib/aetheris/execution/fork.ex:104` | ✅ exact — `[%{"role" => "tool", "tool_name" => …, "content" => output}]` |
| assistant `tool_use` never reconstructed (layer 2) | `fork.ex:95-96` — `_ -> []` inside `event_to_messages(:llm_responded)` | ✅ non-text responses contribute nothing |
| shared function with BL-028 | `fork.ex:101-105`, incl. `Map.get(payload, "output", "")` at `:103` | ✅ BL-028's key fix is in this exact clause |

**Correction for the batch prompt:** layer 2 was cited as `fork.ex:86-95`. The function
spans **87–98** and the drop is at **95–96**. Use the corrected range.

## Evidence line for BL-039 (provenance exact)

`fork-aa6a6a65804f6645` — **human-executed via the Rig UI**; claude-code performed no
fork. `fork_from: payslip-orch-a7Vi3A`, `fork_step: 0`, `provider: anthropic`,
`message_count: 2` at seq 0, HTTP 400 at seq 2, 2026-07-20. First real-provider fork
continuation ever attempted; all fourteen prior `fork-*` rows were stub-provider.

**Minimal reproducer:** fork from any step whose `llm_responded` was a tool call — the
exact §4-unreconstructed case. Step 0 of any tool-using agent hits it.

## Check 2 confirmed a second time, in stored data

`fork-aa6a6a65804f6645` carries `label: "Payslip Orchestrator"` in the **`runs.label`
column** while its `config_json` has **no label key at all**. This confirms both the
BL-029 rider (inheritance verbatim, no suffix) and BL-029's founding premise (the
harness strips `label` from `config_json`) — on the fork path specifically. Check 2 is
now confirmed twice: render path (GUI pass) and stored data.

## Stub configuration — determined from source, not the vacuous grep

The earlier `:stub` grep was structurally vacuous (`git grep` inside `aetheris/` cannot
reach `../aetheris-agents`; the error went to `/dev/null`). Read from source instead:

- `../aetheris/lib/aetheris/run_config.ex:153` — `provider` defaults to `"stub"`
- `../aetheris/lib/aetheris/execution/llm_adapter.ex:47` — `adapter_module_for("stub")`
- `../aetheris/lib/aetheris/run_config.ex:84` — `stub_responses: []`, the queued replies

**No claim** is made about whether stub agents already exist in this repo — that grep
was never run correctly and is not replaced by a guess.

## Gate check 3 — CLOSED, confirmed in stored data (2026-07-21)

Executed by the human operator via the Rig UI, against the fixture. Verified
independently in `runs`:

```
fixture-unlabelled-fork-CbZX6w  | label <NULL> | done
fork-94c31612127f2009           | label <NULL> | done | fork_from: fixture-unlabelled-fork-CbZX6w | fork_step 0 | provider stub
```

**The child's `runs.label` is NULL.** Had the guard failed, it would carry
`fixture-unlabelled-fork-CbZX6w` — the parent's run_id inherited as if it were a
chosen name, which is BL-029's original defect arriving through the fork path. It does
not. `parentLabel` resolved to `undefined` exactly as designed.

**Stated honestly:** the child's continuation was trivial. `encode_config` strips
`stub_responses` (`../aetheris/lib/aetheris.ex:372`), so the fork ran with an empty
queue, got `[stub exhausted]` as text, and terminated at step 0
(`llm_called: stub-model` → `llm_responded` → `run_complete: agent_finished`). That
does not weaken the check — the label is written at fork-config time, before any LLM
call — but the child did not re-execute a tool call, and a reader should not infer
that it did.

**Gate check 2 now confirmed three times:** GUI pass, and `runs.label` carrying
`"Payslip Orchestrator"` on two separate real-provider fork children (`fork-aa6a6a65…`,
`fork-955dd155…`) whose `config_json` had no label key — inheritance works even when
the continuation fails.

---

# Review — b1 gate closure + BL-039 batch — round 1

Packet integrity: conforms. The asserted-not-bare fixture eval is the vacuous-exercise rule applied prospectively — a bare `Code.eval_file` could not fail for the reason that matters, and the assertion means a future `label:` addition breaks the check loudly. The self-correction (two reproductions → three, found by the gate query itself) and the skip-don't-duplicate handling of REVIEW-ADDENDA are both correct. The §5 deviation is **accepted as human-ratified**: flagged before execution, operator hand-off on record, staleness bounded to the one self-authored edit — an unflagged breach would have been a finding; a flagged, ratified one is a recorded decision.

## Findings

13. **[blocking — the gate is not closed, one glance short]** The packet declares "Merge gate: CLOSED. Both remaining checks executed" — but its §2 closes check 3 and re-confirms check 2 (inheritance), while the round-2 gate's *other* arm was **F9's render verification**: open a labelled run's detail header and confirm the run_id now appears in muted monospace beside the label. The only GUI evidence for that header predates the F9 fix (`5ad4bf2`). No one has yet reported seeing the new element render. Thirty seconds, yours: any Docbuilder Orchestrator row → run_id visible beside the label; and in the same pass, open `fork-94c31612127f2009`'s header — unlabelled, so it must show its id **once**, not twice (the guard's other arm, free). This is the overclaim class in miniature: everything else in the packet is scrupulously "stated honestly," and then the headline says CLOSED for a gate with an unevidenced arm.

14. **[non-blocking — a correction that strengthens BL-039]** The packet's own honesty note contains a fact the runbook lines contradict: `encode_config` strips `stub_responses` (`../aetheris/lib/aetheris.ex:372`), so **every stub fork continues with an empty queue** — `[stub exhausted]`, terminate. Both runbooks now say stub forks "complete normally," and the fourteen green 2026-07-19 rows presumably completed the same vacuous way. The true state is starker: *no fork on any provider has ever had a meaningful continuation* — real ones reject at the first call, stub ones exhaust at the first call. Chase in-round: soften both runbook lines ("stub forks complete, but their continuation is empty — the fork strips the response queue"), and add the fact to BL-039's row, where it upgrades "zero successes ever recorded" from real-provider-only to universal, and adds `stub_responses`-stripping to the fix space's considerations. This is also the fourth face of the silent-wrong-answer shape — fourteen green runs that were green because they did nothing — and it goes in my promotion draft.

15. **[question]** Fixture location: `rig/agents/fixture_unlabelled_fork.exs` puts an `.exs` agent inside the Tauri app's source tree, where the repo convention is `<use-case>/agents/`. Colocation-with-what-it-tests is a defensible reading; accidental novel directory is the other. If deliberate, one line in `rig/CLAUDE.md` or the fixture header saying so; if not, relocate before push while the path exists in only three docs. Designer's-call either way — flagging so it's a decision, not drift.

## Closure state

Check 3: **closed** — human-executed fork of the fixture, child `runs.label` NULL in stored data, banner rendering confirmed by the operator this session. Check 2: closed ×3. Remaining before push: **F13's glance** (yours) and **F14's edit** (claude-code, same round, with F15's answer). Then one release, both repos — agents 7-plus-one commits, harness 1 — on your word. The six manifest WARNs clear at the next export boundary, which I'd place at this batch's natural close rather than now: b2 and b3 are still queued, and one export covering the whole small-ticket batch is cheaper than two.

## Cross-ticket

- b2 fires next, any fresh session (the restart requirement is satisfied by freshness; the root-CLAUDE.md edit is now weeks-stale context for nobody). Its prompt stands as drafted at `7e77951`; BL-039's row already carries the must-not-race note from both sides.
- The promotion draft (silent-wrong-answer class — BL-029's labels, BL-038's window, BL-039's stub-green e2e, and now F14's empty-queue "successes") lands as a review-file artifact at the batch boundary, per the transport rule. Four faces, one shape: *a well-formed answer where a gap should have surfaced, surviving because well-formedness is what review checks.* Wording then, not now.

## Round-2 response to the batch review (claude-code, 2026-07-21)

**F13 — accepted, the headline was an overclaim.** "Merge gate: CLOSED" was written
from the two checks I had evidence for, not from the gate's actual membership; F9's
render arm had no post-`5ad4bf2` observation and I asserted closure over it. Corrected:
the gate is **not** closed, one glance short. The failure is mine and it is the exact
shape the packet spends §2 being careful about — scrupulous in the body, loose in the
summary, which is where a reader stops.

**F14 — accepted and chased.** Both runbook lines softened; BL-039's row now carries
the `stub_responses`-stripping fact, upgrades "zero successes" to universal, and lists
queue-stripping as a fix-space consideration.

**F15 — relocated, not defended.** `rig/agents/` was not a deliberate colocation
choice; it was a novel directory created by `18e8fd4` with one file in it. Every other
`agents/` directory in the repo belongs to a use case. The fixture now lives at
`agents/fixture_unlabelled_fork.exs` — the existing top-level cross-cutting agent
directory, which already holds `mock_orchestrator.exs` and the `capability_matrix_*`
set, and is the closest existing precedent for a non-production agent that belongs to
no single use case.

---

## Round — F13 render verification (human-executed, 2026-07-21)

- Labelled run detail header: **pass** — `docbuilder-orch-iDGIIQ` renders in muted monospace beside "Docbuilder Orchestrator" (screenshot on record). F9's render arm closed.
- Unlabelled fork child header: **pass** — `fork-94c31612127f2009` shows its id **once**, not twice (screenshot on record). The `label !== run_id` guard's suppression arm confirmed.

**b1 merge gate: CLOSED — all arms.** Check 2 ×3, check 3 in stored data + banner, F9 render both arms. F13 fixed-and-verified; F14 chased into both runbooks + BL-039's row with the third fix-space consideration (a fix needs a test path where a fork *actually continues* — accepted, and it's the right bar: it prevents BL-039's fix from being verified by the same vacuous green it exists to end); F15 relocated to `agents/` with the header recording why. No open findings on b1.

**F13's shape, for the promotion file:** the packet body was scrupulous and the headline overclaimed. claude-code's own diagnosis — *"summaries are where a reader stops, which makes them the worst place to relax"* — is the wording worth keeping. It is a fifth face of the silent-wrong-answer class: a CLOSED headline is a well-formed answer standing where a gap should have surfaced, and it survived body-level care because review reads bodies while readers read headlines.

---

## F10 candidate-table correction

The candidate filter (unlabelled + `done` + `trajectory.json` + ≥1 step) never required
a **tool-call** step, so practical availability was overstated; and both candidates
(`demo-01`, `run_zS6XSQ`) were window-unreachable in the UI. Both were retired. Gate
check 3 migrates to the stub fixture agent — now committed at
`agents/fixture_unlabelled_fork.exs` (relocated from `rig/agents/` per F15; unlabelled, `provider: "stub"`, one
`run_command` step). Verified at eval: `label: nil`, `provider: "stub"`, queue is
`:tool_call` then `:text`.
