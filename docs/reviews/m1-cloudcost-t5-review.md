# m1-cloudcost §t5 — review (r0, approve)

**Ticket:** m1-cloudcost §t5 — orchestrator `.exs` + sprint case + end-to-end.
**Commits reviewed:** agents `6abc3e8`, harness `ba49d06` (cross-repo pair).
**Reviewer:** claude-ui. **Date:** 2026-07-29.
**Verdict:** approved — milestone done-when met. Two non-blocking findings, both folded before
push (one sprint-case fix, one backlog widening).

Reviewer's message, verbatim:

---

Two findings:

1 — should-fix before push: the sprint case isn't hermetic, so the two silent-green traps it documents will recur. Deviation #4 cleared them by hand for this run (moved stale output/ and fixture history/ aside), but the committed sprint case (lines 1139-1197) does neither. Both its checks read gitignored files a prior run leaves behind: [[ -f "$CLOUDCOST_REPORT" ]] and the orphan count from report_data_2026-07.json. On any re-run where the orchestrator fails — expired token, API down — the sprint greens on the previous run's report and count. That's the exact trap the packet identified, fixed as an instance but not as a mechanism. Fix is two lines: clear cloudcost/output/ (keep .gitkeep) at the top of the case before run_agent, per the m3 "reset accumulating fixtures for deterministic sprints" rule. (History contamination was workspace-local and gitignored — clean on a fresh clone — so the output-clear is the essential piece; a scratch --history-dir is optional polish.)

2 — minor, extends BL-067: the assembler's "Unique tools" line is LLM-generated and unverified too. §3/BL-067 named the counts; the same assembler computes the unique-tools line, which changed this regen (it now includes write_file, correcting a pre-existing omission — proof it's non-deterministic, not authoritative). Scope BL-067's deterministic-generation fix to cover the whole assembler-computed block, not just the Summary counts, or the sweep is one line short of complete.

Neither blocks the milestone — this run's evidence stands on its own. Fold finding 1 into the sprint case before you push (it's held), widen BL-067's wording for finding 2.

Coverage boundary: I read the code and the guard outputs; I didn't run anything or open trajectory.json myself, so the latency/token-grep figures are as-reported (though I checked the command sequence, the counts, and the timestamp reconciliation by hand).

t5 verdict: approved — milestone done-when met. Once finding 1 is folded and you push the cross-repo pair, two things close it out: delete the reserved IP (its job is done — it's billing ~$4.38/mo unassigned), and the milestone-close ritual — a §7 pass over m1's recurring findings for anything that should be promoted to the learning log. The dominant thread this milestone was silent-wrong-answer in a dozen costumes (vacuous import check, fixture-vs-live, stub fallback, the typo'd token check, LLM arithmetic, non-hermetic sprint); most are already in the log, but it's worth a deliberate look before you call m1 closed. Say the word and I'll draft that promotion pass.

---

## Disposition

### F1 — sprint case not hermetic (should-fix) — FOLDED

Correct, and the sharper framing is the reason it matters: t5 fixed the *instance* (moved the
stale artifacts aside by hand for one run) while committing the *mechanism* unchanged. The
packet named the trap and then shipped it.

Fixed in the case, before `run_agent`:

```bash
find "${CLOUDCOST_DIR}/output" -mindepth 1 ! -name '.gitkeep' -delete 2>/dev/null || true
ok "cleared ${CLOUDCOST_DIR}/output (stale-artifact guard)"
```

Verified as a mechanism, both halves — that it engages, and that it prevents what it exists to
prevent:

```
=== mechanism test: does the clear engage AND prevent the green? ===
before: cloudcost_report_2026-07.html do_costs_2026-07.json do_inventory_2026-07.json
        .gitkeep orphan_candidates_2026-07.json report_data_2026-07.json
        STALE_sentinel.html STALE_subdir
after : .gitkeep

=== the negative half: with output cleared, do both checks FAIL? ===
  report check: FAIL (correct — nothing to pass on)
  orphan check: FAIL with N='err' (correct)
```

Then the happy path re-run live to confirm the clear does not break it —
`cloudcost-orch-mhmohw`, a second independent live run:

```
[OK]    cleared ../aetheris-agents/cloudcost/output (stale-artifact guard)
[OK]    cloudcost_orchestrator.exs evaluates
[OK]    uc-cloudcost orchestrator → no-json (691 bytes)
[OK]    report: cloudcost_report_2026-07.html (14K)
[OK]    orphan candidates: 1 (≥1 — milestone done-when)
-rw-rw-r-- 1 it it  14K Jul 29 18:54 cloudcost_report_2026-07.html
-rw-rw-r-- 1 it it  22K Jul 29 18:54 do_costs_2026-07.json
-rw-rw-r-- 1 it it 9.5K Jul 29 18:54 do_inventory_2026-07.json
-rw-rw-r-- 1 it it 2.8K Jul 29 18:54 orphan_candidates_2026-07.json
-rw-rw-r-- 1 it it 5.2K Jul 29 18:54 report_data_2026-07.json
```

All five artifacts stamped 18:54 — none survived the clear, so each is this run's.

The reviewer's scoping of the history half is accepted: `cloudcost/history/` is gitignored and
therefore empty on a fresh clone, so it cannot green a CI run; the contamination was
workspace-local. Not fixed, not silently dropped — the packet's caveat stands and a scratch
`--history-dir` remains optional polish.

### F2 — unique-tools line unverified (minor) — BL-067 WIDENED

Confirmed against source before adopting. `write_file` is genuinely used by
`context_builder.exs` (`docs/capability-matrix.md:164`, carried since m3) and was **absent**
from `eeb37a1`'s unique-tools line:

```
eeb37a1 : … spawn_agent, wait_for_all, read_file,             MCP servers (corpus_search, lattice)
6abc3e8 : … spawn_agent, wait_for_all, write_blackboard, …, write_file, MCP servers (…)
```

So the line was wrong before and is right now by luck. BL-067 rewritten to cover the whole
assembler-derived block — Summary counts, unique-tools line, **and** the Overlap Report, which
is derived by the same means (Step 2) and has never been checked at all. Done-when now requires
a test per derived value, not just the totals.

### Carried to milestone close

- **Delete the reserved IP** `168.144.13.150` — a write op on the DO account, outside this
  session's read-only credential (D2). Human-owned.
- **§7 promotion pass** over m1's recurring findings before m1 is called closed.
