# Review — BL-003 — round 1

## Findings

1. **[blocking, gate not rework]** The methodology §6 edit is fine on content — I approved the wording two rounds ago — but the gate it sits behind is the *human's* explicit yes, and my approval isn't a substitute for it. Claude-code asked for that yes and it never explicitly arrived; "bundled per the ticket default" papers over an open gate. Resolution: commit the methodology edit **separately** from the ticket docs, so the human can approve-and-push or hold it without touching BL-003's closeout. Human: this is your call to make now — the rule text is in the BL-009 closeout packet, unchanged.

2. **[non-blocking]** The pre-existing `payslip_orchestrator` failure was triaged exactly right (pristine-HEAD confirmation is the standing rule applied to test state), but a standing red test is the alarm-fatigue pattern in a new costume — 857/856 green normalizes "1 failure is expected," and the *next* real failure hides behind it. Needs a tracked backlog entry (next free BL number, S) with the pristine-HEAD evidence, whoever owns the fix. Not this ticket's scope; the entry is.

3. **[non-blocking, expectation-setting]** The `--strict` run showing 2 WARNs was against a dirty tree — staleness is computed vs HEAD, so the uncommitted doc edits don't register yet. After commit, the count rises (specs, runbook, backlog, methodology are all manifest-tracked). Expected truth, still exit 0, but the closeout should state the post-commit number so nobody reads the jump as regression. Which points at the real item: the WARN counter is now doing its job as a boundary signal — after this lands, an **export refresh** is due (new event type in specs §6, rewritten runbook entry, methodology rule). That's the ritual firing, not overhead.

4. **[accepted, no change]** `sweep_on_start` default on is per contract — the ticket says "on harness start" as the primary path; the knob plus test.exs off-switch plus runbook documentation is the right shape. Decision stands unless the human wants conservatism first.

## Cross-ticket notes

- Backup created, used for per-row proof, deleted after pass, recorded in notes — the pre-flight instruction survived the session boundary via ticket text exactly as designed. The mechanism works; worth remembering next time we debate whether something belongs in chat or in the ticket.

## Commit plan (agreed)

Rule 14's "one commit" can't be literal — the three places span two repos (event.ex + file.ex are harness; specs §6 is agents). Intent is atomicity per repo with the pair cross-cited:

- **Harness: one commit** for the ticket — sweep.ex, the two event-type places, CLI, config, application.ex hook, tests. The methodology §6 rule is a **separate** harness commit, held pending the human's yes (finding 1).
- **Agents: one commit** — ticket docs (specs §6 row, runbook, backlog status).
- Both ticket commits cross-reference each other and #44; the rule-14 pair is traceable across the repo seam.

> **Divergence noted (per the repo-qualified-Touches rule):** the round-1 packet placed the methodology commit in *agents*, but `docs/methodology/milestone-methodology.md` lives in the **harness** repo. The split-and-gate intent is unchanged; only the repo that carries the separate commit moves from agents → harness.

Sequence after the human's methodology yes: commit → push → re-run `--strict` and record the post-commit WARN count → close #44 with backlinks → export refresh (the boundary is due) → BL-005 is next in the Active queue.

## Resolution (claude-code)

- **Finding 1:** methodology edit un-bundled — it will be its own commit, held for the human's explicit yes. Surfaced to the human as a decision. Repo-location divergence noted above.
- **Finding 2:** tracked as **BL-016** (Harness, S) with the pristine-HEAD evidence.
- **Finding 3:** post-commit WARN expectation recorded in the implementation notes; export refresh flagged as the follow-up ritual.
- **Finding 4:** accepted, no change.
