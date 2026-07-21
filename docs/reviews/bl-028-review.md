# Review — b2: BL-028 — round 1

Packet integrity: conforms, and sets the batch's high-water mark — red-first evidence against the unpatched file is Demonstration-not-citation done properly (the failing assertion *is* the backlog row's symptom, `left: ""`, silent not crashing), and re-running gates fresh rather than reconstructing output is Packet-integrity done properly. The writer-family table (worker/MCP → `"output"` at `loop.ex:537,553,570`; in-process + error path → `"result"`) is a better map of the root cause than the backlog row carries, and the `record_tool_error/6` observation — **every recorded tool error is `"result"`-keyed regardless of tool** — materially raises BL-027's stakes: verify doesn't just crash on orb trajectories, it crashes on any trajectory containing a recorded tool error. That's for BL-027's trigger-day reader; see finding 2.

## Findings

1. **[blocking — one-line fix]** The fix's fallback silently degrades on recorded tool errors, and the `||` idiom is why. `record_tool_error/6` writes `"result" => error_result` (`loop.ex:354`) — per your own table, part of the `"result"` family. If that error result is ever `nil` (or for any in-process writer whose `"result"` value is `nil`), `Map.get(payload, "output")` → `nil`, `|| Map.get(payload, "result", "")` → reads `"result"`, gets `nil`, returns `nil` — and the reconstructed message carries `"content" => nil` where every other path guarantees a string. Downstream, a nil content in a transcript message is exactly the malformed-shape class BL-039 just demonstrated providers reject. The truthiness trick that correctly protects empty-string `"output"` is the same trick that leaks `nil` through `"result"`. Fix: `output = Map.get(payload, "output") || Map.get(payload, "result") || ""` — one more `||` arm normalizes nil-from-either-key to the string default while preserving all three stated properties. Contract: §2's transcript definition (messages are strings); the fix's own property list ("neither key present keeps the `""` default" — a present-but-nil key currently evades it). Add a third fixture arm to the test (`tool_payload_key: "result"` with a `nil` value, assert `content == ""`) so the normalization is pinned, not incidental.

2. **[non-blocking]** The impl notes' BL-027 analysis — the writer-family table, the tool-error universality, the shared-helper-vs-writer-convergence fork with its contract implication — is precisely what BL-027's trigger-day session needs, and it currently lives only in notes that BL-027's reader has no pointer to. The parked row must not be reopened, but *annotating a parked row's evidence base is not reopening it*: one sentence appended to BL-027's row — "Root-cause map and fix-space analysis in BL-028's implementation notes (<final path>, 2026-07-21); note `record_tool_error/6` means every recorded tool error is `"result"`-keyed, so the crash is reachable on any trajectory with a tool error, not only orb trajectories" — with the trigger, ratification, and parking untouched. That's N+1-carry applied to a trigger-parked row: the prompt path for BL-027's future session is its row, and analysis that doesn't reach the row doesn't travel. Same commit can absorb the row's missing `:450` citation you recorded — both are backlog edits, agents repo, one touch.

3. **[non-blocking]** Impl-notes home: `docs/reviews/bl-028-review.md` is this findings file's name by convention (`bl-0XX-review.md` = claude-ui's findings, saved by the human — the ownership table is explicit). Move the notes to the harness milestones dir beside BL-003's precedent (`../aetheris/docs/aetheris/milestones/bl-028-implementation-notes.md`) or名 them `bl-028-implementation-notes.md` in the agents docs tree. Naming collision between the two triad artifacts is exactly the confusion the who-writes-what table exists to prevent.

4. **[non-blocking — ratification, granted]** The §6 citation repair outside the §2/§4 Touches scope is **approved as flagged**. Same symbols, same decay, same round — correction-chasing's plain instruction; the narrower Touches reading would have manufactured two knowingly-wrong lines. The flag-then-proceed transport was correct. For the record: the nine-line citation-repair table, verified line-by-line at `d831220` including confirming `fork.ex:6-7` still exact, is the correction-chasing rule executed at full fidelity — the promoted rule earning its keep on the contract's own citations.

5. **[question]** The comment in `fork.ex` cites `loop.ex:354,424-508` as the `"result"` range — a range that spans the worker-dispatch lines too if read carelessly (537/553/570 are outside it, so it's technically clean, but `424-508` includes non-writer lines). Cosmetic: consider the enumerated list form the test comment uses, or "loop.ex:354 and :424-508 (in-process family)". Take it or leave it in round 2; noting only because this exact comment is what BL-039's implementer reads first.

## Cross-ticket notes

- Finding 1's mechanism — a guard correct for the case it was written against, leaking on the adjacent case sharing its syntax — is kin to b1's F9 (correct fix, coincidence-removal side effect). Not the silent-wrong-answer class; more "the fix's blast radius is one case wider than its test." Two instances this batch; watching, not drafting.
- The red-first pattern (1a) should be the batch norm going forward: b3's done-check can state it — the timeout test run against unbounded `await_run` should hang-or-fail before the fix, demonstrably.
- BL-027's stakes-raise (finding 2) does **not** un-park it — the trigger stands as ratified. But trigger-day just got more likely to arrive via "first trajectory with a tool error under verify" than via orbs; the row annotation should let the trigger's wording stand while noting the reachability widened.

---

Round 2: finding 1's fix + test arm, findings 2–3's relocations/annotations, 5 optional. Then commit (still held), and b3 fires on a fresh session — its prompt gains one line from this review: red-first evidence requested in the done-check. Disposition table with the round-2 packet, per form.

---

# Review — b2: BL-028 — round 2

Packet integrity: conforms. Round 2 is the review loop working at its best in both directions — F1's mechanism confirmed by live reproduction of the predicted leak (`left: nil`), then *widened* by reading the writers rather than patching the named case: the map shape (`spawn_agent`/`wait_for_all`, both in the ticket's own citation list) would have sailed through my proposed third `||` arm, and the finding's stated invariant ("every other path guarantees a string") is what got implemented rather than my suggested implementation of it. That's the correct relationship between a finding and a fix — the contract binds, the sketch doesn't. The credo mid-round red, reported rather than silently repaired, is exactly the right transport for a gate that goes red and green inside one round.

## Dispositions on round 2

- **F1 — closed, widened form accepted.** `normalize_content/1` satisfies the invariant across all three shapes; the `inspect/1` fallback is right (lossy but string-typed — the invariant at stake is type, not fidelity, and fidelity for those tools is unreachable anyway per the live-vs-recorded note). Both new arms verified red against the round-1 expression — the widening is demonstrated, not asserted. The map-arm test's `Jason.decode` round-trip assertion pins the encoding, not just the type. No residue.
- **F2 — closed.** BL-027 annotation as specified: evidence pointer, reachability widened, trigger/ratification/parked untouched. The distinction held cleanly — annotating evidence is not scheduling work.
- **F3 — closed.** Notes relocated beside BL-003's precedent; the findings-file name is now unambiguous.
- **F4 — nothing owed**, correctly.
- **F5 — closed**, split-range form taken.
- **Second citation re-verification** — accepted, including the judgment call inside it: widening §2/§4.1 to `:73-125` (the normalizer is now part of how a `:tool_result` becomes a message, so the citation must cover it for §2 to mean what it says) while deliberately *not* widening the §4 known-limitation citation (it points at where tool-call turns are dropped; normalization is not part of that claim). That's citation semantics done right — the range follows the claim, not the diff.
- **Live-vs-recorded gap** — correctly recorded-not-acted-on, and correctly homed: it's in the impl notes BL-039's row already points readers toward via the same-clause note. It also sharpens BL-039's fix space in a way worth one clause when that ticket is scoped: the "fold results into user-role text" option cannot be byte-faithful for `spawn_agent`/`wait_for_all` because the live string was never recorded — a constraint on the design choice, discovered here.

## Findings (round 2)

16. **[non-blocking — one line, with the commit]** `mix.exs` line count aside: `normalize_content/1` introduces `fork.ex`'s dependency on `Jason` — almost certainly already a top-level dep (the Event struct derives `Jason.Encoder`), but "almost certainly" is the inference class this batch keeps convicting. Confirm `{:jason, ...}` is a direct dependency in `mix.exs` (not transitive), state it in one line in the round-close note or commit message. If it's somehow transitive-only, promoting it to direct is the fix and is in-scope. Thirty seconds; closes the last undemonstrated claim in the round.
17. **[non-blocking — record, no action]** The packet's §5c diff block for the agents-repo backlog change is **empty** — the BL-027 annotation and `:450` addition are described in prose and dispositioned "done" but the diff section contains only an empty fence. Given this batch's F13/F14 history (claims about N artifacts, evidence for N−1), the round-close needs either the actual backlog diff pasted or the committed sha named once it exists. I don't doubt the edit was made; the record shouldn't have to take my confidence as evidence.

## Verdict

**Zero blocking findings.** F16/F17 close with the commit itself — neither needs another review round. Proceed: commit (both repos' pieces, harness code+contract+notes and the agents backlog touch), report the shas with the F16 confirmation and F17's diff-or-sha, and hold pushes per discipline. My recommendation once reported: push b2 immediately rather than stacking it under b3 — b2 touches `fork.ex`, BL-039's row says must-not-race, and a pushed b2 makes the sequencing fact a property of origin rather than of a local stack.

## Cross-ticket notes

- **F1's arc is the promotion-relevant part**: reviewer names a mechanism and sketches a fix; implementer verifies the mechanism against source and finds the sketch under-covers; the *invariant* from the finding, not the sketch, drives the implementation. Pair this with round 1's F1 (`--name`), where the reviewer's sketch was wrong the same way for the same reason — inference from named cases instead of reading the family. Two instances, both directions of the loop. Candidate wording for the batch boundary: *"A finding binds by its invariant, not its sketch — implementer verifies the mechanism against the full writer/consumer family before adopting the reviewer's proposed fix."* Goes in the draft file, not promoted here.
- The red-first pattern held for all three arms including reproducing the *round-1* expression's failure — b3's prompt gets the red-first line as planned.
- b2 will land at a harness HEAD past `d831220`; b3's prompt citations (`run_helpers.ex:30`, `fork.ex:37`, etc.) are in files b2 doesn't touch except `fork.ex:37` — which is caller territory b2 also didn't touch. b3 fires as drafted, with its own re-verify instruction covering the delta as usual.

---

Commit, report shas + F16/F17 closure, push on your word — then b3 to a fresh session and the batch enters its last leg.
