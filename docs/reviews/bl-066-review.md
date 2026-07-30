# BL-066 — review (r0, approve)

**Ticket:** BL-066 — bump `bandit` to `~> 1.12` to clear the `hex.audit` HIGH
(EEF-CVE-2026-65623). Closes **BL-060** as well — the same advisory, filed twice.
**Commits reviewed:** harness `892b0f7` (`mix.exs` + `mix.lock`), agents `9b6b57d` (both rows
closed).
**Reviewer:** claude-ui. **Date:** 2026-07-30.
**Verdict:** approved — `hex.audit` clean at the resolved bandit 1.12.4, full CI contract green,
Bandit's own HTTP path exercised. No findings against the implementation. One finding *against
the reviewer's own earlier row* (the BL-060/BL-066 duplicate), owned below.

Reviewer's message, verbatim:

---

Approved — BL-066 closed, and BL-060 with it. Clean bump, and a good catch that's partly my miss to own.

Verified from the diff and gate outputs:
- **hex.audit clears at the resolved version, not the constraint** — bandit **1.12.4** locked (the diff confirms it), `No retired or security advisory packages found`, exit 0. Checked after the bump, which is the right discipline.
- **Co-resolution is accounted for**: thousand_island 1.4.3→1.5.0 (bandit 1.12 requires `~> 1.5`), plug_crypto 2.1.1→2.2.0; websock/plug/hpax unchanged — all visible in the lock diff, not just asserted.
- **Full CI green on the bumped tree**, 969/0 matching the pre-bump baseline, so nothing in the suite moved with the dependency; and `playground_api` exercises the actual Bandit-served path (boot → :done → 422 → shutdown), which is where a minor server bump's real risk lives. The one named skip (Leg 2, `AETHERIS_MODEL` unset) is a pre-existing conditional on overlay/model, not the HTTP surface — correctly named, not swallowed.
- **The reachability bound is framed honestly** (§1d): one Bandit call site, no WebSocket usage, so the fragmented-frame exploit was never reachable — stated as a bound on exposure, explicitly *not* as a reason the gate could have stayed red. That's the correct posture (hex.audit has no suppression; the bump was required regardless).

**The duplicate is mine to own.** BL-066 was the row I drafted, and I wrote "same class, same ledger, so the advisory history stays in one series instead of forking" — while forking BL-060, which had filed the identical CVE one day earlier in that same ledger. It's the downstream consequence of the wrong-corpus "no matching ticket found" search I flagged at the time: I named the search as vacuous but didn't take the next step — *search the right corpus for the advisory ID before filing a new row*. claude-code caught it, closed both, marked BL-060 the original, and answered the two pre-conditions BL-060 had actually asked for (fixed-in-1.12 confirmed at 1.12.4; co-resolution checked). Closing both was right, not scope creep — leaving BL-060 open with a standing "expected-red" instruction against a now-green gate would itself be the silent-wrong-answer (a tracked-red that's actually green).

Two smaller things, both fair:
- **The export-note correction stands.** My "no export implication" was true of the bump commit (`892b0f7` touches no manifest-tracked file) but not the ticket — closing the rows edits `backlog-2026-06.md`, which *is* tracked, so `9b6b57d` re-stales it. No new obligation (BL-067 already staled that row); just an imprecision in my note, correctly caught.
- **The stale "expected-red on BL-060" in `handoff-fork-arc-close-2026-07-26.md:41`** (§7.1) — naming it in the now-committed review is the right minimum. A dated handoff is a historical record, so I wouldn't rewrite its claim, but a one-line "superseded — green as of `892b0f7`" pointer on that line would stop a future `grep "expected-red"` from re-adopting it. Optional, your call; it's low-traffic.

Go-forward: the gate is green for the first time since 2026-07-26, so the standing tracked-red carry is retired — future packets' gate tables report `hex.audit` clean, and the next red (if any) is upstream-triggered and gets a fresh row the day it's found. 

Coverage boundary: I read the lock diff and the gate outputs, didn't run anything; the 1.12.4 resolution and co-resolution I confirmed from the diff, the green suite as-reported.

**BL-066 verdict: approved, closed.** Same as BL-067 — file this review verbatim to `docs/reviews/bl-066-review.md` (it carries the duplicate-catch and the reachability reasoning, which shouldn't live only in chat), commit, and push the three. Then **BL-068 is the last open item** — the curation home + eduloka — and its prompt's already in your hands.

---

**Action taken on the optional item:** the `handoff-fork-arc-close-2026-07-26.md:41` pointer was
added — an HTML comment beneath the line, marking it superseded and naming `892b0f7`, leaving the
historical claim itself intact.
