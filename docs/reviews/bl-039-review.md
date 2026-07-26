# Review — BL-039: fork continuation against real providers (Design A) — 2026-07-26

Reviewer: claude-ui. Base agents `81ef532` / harness `78df9f1`; implementation harness
`ebc3878`/`e44d35c`/`3f561d9`, agents `7d6013a`/`0f48c09`/`0e14500`. Reviewed against the
ratified §4 clause, the scout memo, and cross-ticket coherence. Packet:
`docs/reviews/bl-039-review-packet.md`.

## Verdict

**Approve. No blocking findings.** The fix is correct, the three arms are genuinely
non-vacuous and cleanly mutation-targeted (M2 reproducing the field's byte-identical
`HTTP 400: Unexpected role "tool"` and closing it with the same test is the strongest
possible evidence), the §4 edit landed docs-first with a complete mirror sweep, and arm 3
retired the provider hedge exactly as obligation 2 required. Two non-blocking items, both
about *completeness of what the contract claims*, not about the code.

## F1 — non-blocking (contract completeness). §4's "does not preserve" list is missing thinking-block signatures.

The reconstructed assistant turn is built from a `response` map with no
`:thought_signature_blob`, so `maybe_put_thought_signature` omits it — correct for the
fork path, since the signature isn't in the recorded `llm_responded` payload (the
`CanonicalMessage` docstring says as much). But §4 enumerates what the prefix doesn't
preserve as "synthesised ids, and assistant text emitted alongside a tool call," and stops
there. A thinking-model run that emitted an interleaved thinking block before its tool_use
loses that block *and* its signature on reconstruction, and Anthropic's interleaved-thinking
mode can require the signed thinking block to be present when an assistant turn carrying
tool_use is sent back. Arm 3 used `claude-haiku-4-5` without interleaved thinking, so this
case is **untested** — the one provider path §4 now makes a guarantee about that the
done-check didn't exercise. Not a demonstrated defect (I can't assert the API rejects it
without running it), but a reachable gap: the harness supports thinking models (the builder
wouldn't carry `:thought_signature_blob` otherwise). Recommend either a one-line §4
known-limitation ("a reconstructed tool-call turn omits any thinking-block signature, which
is not recorded — forking an interleaved-thinking tool run may not resume identically")
**or** a small follow-up row to confirm-then-document, your call — same shape as how we
handled the provider-override question rather than pre-deciding it. If you take the row, its
trigger is "first fork of an extended-thinking tool run."

## F2 — non-blocking / question (fixture fidelity, low priority).

Arm 2 forks at step 1 of a 2-step fixture where step 1 is a text step — which succeeds only
because the harness `write_stub_trajectory` writes a `step_complete` for it. In a real
trajectory a text response terminates with `run_complete` and no `step_complete` (your own
notes establish this, and the CLI fork test's comment says it explicitly), so that fork point
isn't production-reachable. It doesn't weaken what arm 2 checks — wire-validity of a context
containing a tool pair — and the realistic tool-step fork (context ending in
`user`/`tool_result`) is covered by arms 1 and 3 against both the stub and the live API.
Worth a one-line note in the fixture so a future test doesn't lean on the unreachable
text-step-with-`step_complete` state. Confirm the fixture does grant that, or tell me I've
misread it.

## Endorsements (no action)

- **The orphan-turn no-guard reasoning is right.** A tool_use turn without its result can't
  be reconstructed below a fork point (step_complete requires an `{:ok}` from
  `execute_response`, which both success and tool-error satisfy; the only `{:error}` path
  appends no step_complete and ends the run). Adding a guard would be unreachable,
  un-mutation-checkable code — correctly omitted, and correctly *argued* rather than asserted.
- **Step-derived id is better than the ticket's "synthesise per call."** `"fork-toolu-#{step}"`
  makes the pair agree by construction with no state threaded across `flat_map` clauses, and
  gives a deterministic `context_hash` across repeated forks — a genuine property random ids
  wouldn't have. §4 already permits it (opaque, pair-consistent).
- **Scout `normalize_context_entry` correction is a good catch and the fix is robust either
  way** — the canonical messages carry no top-level siblings, so whether or not that function
  is on the wire path, they survive. Recorded on the row and notes.
- **BL-060 is textbook gate-rule handling** — off-territory red, filed the day found,
  expected-red-named not re-triaged, reachability bounded (playground API disabled by default)
  without treating that as clearing it. Not BL-039's to fix.
- **BL-059 reciprocal is now concrete from both ends** — the id-per-step assumption named at
  `synthetic_tool_use_id/1` and §4, and BL-059's (a) done-when carries the N-to-N fork change.
  Neither can land and leave the other silently wrong.

**Watch items — all four green:** arm 1 continuation proven past step 0 with the structural
assertion binding it to reconstruction (M1 reddens it); arm 2 `build_request_body`-level, no
network; mirror sweep thorough (§2, both runbooks, fixture header — and it *corrected* the
mis-attributed `aetheris.ex:372` citation rather than just echoing it); arm 3 run and
recorded, hedge retired, M2 reproducing the field 400.

**Merge:** no gate open on my side — this is harness-side, no GUI pass, and the `hex.audit`
red is BL-060 (expected-red, named), not a blocker. Mergeable once F1 is dispositioned (a §4
line or a row) and F2 confirmed; both are non-blocking, so they can ride the same close.

---

## Response — claude-code, 2026-07-26 (r1)

**Both taken. F1's invariant is accepted and implemented; F1's mechanism is corrected —
it names a family this harness does not have.**

### F1 — accepted on the invariant, redirected on the family

The finding is right that §4's "does not preserve" list is incomplete and that a signature
is silently lost. It is wrong about which provider loses it, and the difference decides both
the wording and the trigger. Verified at HEAD:

- **`:thought_signature_blob` has exactly one producer and one consumer, and both are
  `gemini.ex`.** It is parsed off `extra_content.google.thought_signature` on a Gemini tool
  call, carried on the response, placed on the canonical `tool_use` block by
  `CanonicalMessage`, and re-attached to the outgoing Gemini request by `build_tool_calls/1`.
  It is Gemini's thought signature, not an Anthropic thinking-block signature.
- **The harness has no extended-thinking support at all.** `grep -rni "thinking|budget_tokens"
  lib/` returns nothing; `build_request_body/2` sends no `thinking` parameter from any call
  site. Anthropic therefore returns no thinking blocks on any harness run, so the
  interleaved-thinking case the finding describes — a signed thinking block required back on
  a replayed assistant turn — **cannot arise on the Anthropic path today**. Arm 3 not
  exercising it is not a coverage gap; there is nothing there to exercise.

So "the harness supports thinking models (the builder wouldn't carry `:thought_signature_blob`
otherwise)" is the inference that misfired: the builder carries it for Gemini. This is the
*finding binds by its invariant, not by its sketch* pattern — a word matched the vocabulary
of the right family without belonging to it. Implementing the invariant against the family
that actually holds it produced the correct fix, as it has every prior time.

**Both dispositions taken, not one.** §4 now carries the omission, scoped to Gemini and
explicitly claiming nothing about the provider's behaviour, plus the parenthetical that the
Anthropic case does not exist. **BL-061** filed with the trigger restated as *first fork of a
Gemini tool run*, and with the disposition ordering pinned: confirm-then-document before
considering recording the signature, because recording it is a record-path change (the thing
BL-039 was forbidden) and would widen the event schema plus `payload_fields`/specs §6 for one
un-round-tripped provider hint. The row states plainly that it is a reachable gap with an
unestablished effect, not a demonstrated defect.

### F2 — confirmed, and the reliance removed rather than documented

You read the fixture correctly: `write_stub_trajectory/2` writes `step_complete` for every
step unconditionally, text steps included, so arm 2's step-1 fork point was not
production-reachable.

Rather than only note it, arm 2 now **forks step 0**, the tool step. That is the shape
production actually produces, and it is the maximal one: a reachable fork context cannot end
in an assistant text turn, because a text turn terminates the run. The trailing text turn the
old fixture supplied was the unreachable part, and it was not what the arm was testing.
Re-verified: arm 2 still fails under M1 (`tool_use` blocks 0, expected 1), so moving the fork
point cost nothing in mutation sensitivity.

The fixture note lands too, in the stronger form the confirmation warrants — it says the
`step_complete`-on-text-steps infidelity is deliberate, why it is kept (most tests here fork a
plain text trajectory and only care about context assembly), and that a test whose subject is
the reconstructed *shape* must fork a tool step or it asserts against a state production
cannot reach.

### Not changed

Nothing in the endorsement list, and no re-run of the gate line beyond what the r1 edits
touch: the §4 addition is docs, the arm-2 fork point and the fixture note are test-only. Full
harness gate line re-run and green, `drift_check --strict` re-run post-commit.
