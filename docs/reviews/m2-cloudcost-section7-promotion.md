# m2-cloudcost — §7 promotion packet (claude-ui, 2026-08-03)

Landed as a review-file artifact **before** any promotion commit, per the BL-007 learning:
promotion wording travels as a file, not as chat — that relay gap bit the P3–P6 handoff twice in
one milestone.

Ground rule from the packet: each item is a **scoped add**, applied against the target doc and
diffed. Where a learning already exists the item is a refinement clause, not a duplicate, and the
diff shows which. Items are marked NEW / REFINEMENT.

**Ratification: COMPLETE, 2026-08-03. All seven ratified and landed.**

| # | Home as landed | Commit |
|---|---|---|
| P1 | `aetheris-agents/CLAUDE.md` — Python script conventions, beside "verify a foreign table's live DDL" (same don't-trust-the-inferred-shape genre) | agents |
| P2 | `aetheris/CLAUDE.md` — **Silent-wrong-answer**, as its quietest carrier | `710ecd2` |
| P3 | `triad-loop.md` Phase 2 — already landed, verified at HEAD, no action | `7328755` |
| P4 | `aetheris/CLAUDE.md` — appended to **Adjacent-case** | `710ecd2` |
| P5 | `aetheris/CLAUDE.md` — appended to **Cited-means-read** | `710ecd2` |
| P6 | `aetheris-agents/CLAUDE.md` — appended to the gate/tracked-carry rule | agents |
| P7 | `aetheris/CLAUDE.md` — new sibling bullet after Silent-wrong-answer | `710ecd2` |

**Homing rule applied: a learning is homed by its FAMILY, not by the milestone that surfaced
it.** The packet homed the discipline items in `aetheris-agents` because that is where m2
happened; P4/P5 exposed that as a guess, since both are refinements to parents living in the
harness repo. Three homes therefore diverge from the packet, each verified by grep rather than
assumed:

- **P2** — packet said "sibling of no-silent-caps". `no-silent-caps` is **not a learning** in
  either `CLAUDE.md`; it is a cloudcost decision-D phrase. The real family is
  **Silent-wrong-answer**, which P2's own closing sentence names ("absent→zero is the
  silent-wrong-answer's quietest form"). Homed by mechanism, not by the name in the sketch.
- **P6** — packet said "likely the same harness home". It is not: the gate rule carrying the
  tracked-carry clause lives in `aetheris-agents/CLAUDE.md`; `aetheris/CLAUDE.md` only
  *references* that clause from its `hex.audit` section. P6 stayed in agents, beside its parent.
- **P7** — packet said "beside no-fabrication / D4". No learning of that name exists, and D4 is
  a cloudcost *milestone decision* in a third document. Landed as a new sibling bullet in the
  harness learnings section, adjacent to the class it sharpens, pointing at both.

**One correction inside P5's own text.** The packet's incident line cites
`detect_orphans.py:250`. That is precisely the inherited-never-opened miss the clause is *about*
— the rule it describes lives at `:243`. Writing "do not repeat a number you did not open" while
repeating that number would be self-refuting, so the landed source ref reads
`detect_orphans.py:243 (the :250→:243 inherited-citation miss)`. `:243` was verified by opening
the file (`rule_stopped_compute_with_attached_storage`), not inherited from this packet.

---

**P1 — Resolved-value over advertised-value.** NEW → `aetheris-agents/CLAUDE.md` learnings.
*Incident:* the AWS stub encoded from `ServiceModel.protocol` (what a service *advertises*). CloudWatch advertises `smithy-rpc-v2-cbor` but botocore *resolves* to `json`; encoding to the advertised value drove the cbor parser over a json body → MemoryError. Nine of ten services agreed, so it hid until the tenth.
*Text to add:* "When a library exposes both what a thing advertises and what it resolved to — protocol, API version, endpoint, region — bind to the resolved value (`resolved_protocol`, not `protocol`). A value the tool computes will diverge from the 'preferred' field or a hand-typed table, and the divergence hides until the one case where they differ. Read what the tool resolved; never re-derive it."

**P2 — Absent is unknown, not zero.** NEW → `aetheris-agents/CLAUDE.md` (sibling of no-silent-caps).
*Incident:* CloudWatch returns a result object for every query whether or not the metric has data, so "no datapoints" and "zero objects" arrive in the same shape — reading absent as 0 raises a false empty-bucket signal on a brand-new bucket. Same shape three ways: unparseable push-date → undated not recent; denied API → unknown not nothing-found.
*Text to add:* "An absent reading is UNKNOWN, never a zero/default that reads like an observation — and the two usually arrive in the same shape. Assert a fact (empty, recent, clean) only from a value actually observed. Give the three cases distinct homes in the output — a value, an unknown (warning), a refusal (denied) — so 'not checked' renders differently from 'nothing found'. Absent→zero is the silent-wrong-answer's quietest form."

**P3 — Section-scoped edits from the no-repo party.** ALREADY DRAFTED → `triad-loop.md` Phase 2.
*Incident:* the mirror round-trip that lost fixes twice (phantom corrections, then three reverted).
*Status:* text handed over two turns ago. Ratify = confirm it landed; no new text here.

**P4 — Adjacent-case: "the one X" is an observation, not a census.** REFINEMENT → the existing Adjacent-case learning.
*Incident:* m1 called `STOPPED_STATES` "the one seam"; t1 found three. The claim came from noticing one, not enumerating the class (BL-074).
*Clause to append:* "Tell: any doc or comment that says 'the one X' / 'the only place that…' is almost always an observation of one, not an enumeration. Treat it as unproven — enumerate the class before fixing the first instance, and correct the 'the one' text when you find it was N."

**P5 — Cited-means-read: an inherited citation is still uncited.** REFINEMENT → the existing Cited-means-read learning.
*Incident:* `detect_orphans.py:250` was carried from t1 notes into a review, a rev-5 draft, and survived two review rounds; the real line was `:243`. Inherited, never opened.
*Clause to append:* "A line/commit/section reference you inherited from prior notes and never opened yourself is not a citation — it is a rumor with a number. Open it before you repeat it; 'it came from the earlier packet' is not having read it."

**P6 — Tracked-carry + the coupling constraint.** REFINEMENT (carry) + NEW (coupling) → `aetheris-agents/CLAUDE.md`.
*Incident:* BL-069's ≥1-orphan assertion left red and named with its ref on every leg, never quietly relaxed. BL-077 surfaced the coupling: flipping the sprint's `fail` to set an exit status would turn *every* tracked known-red blocking at once, so the enforcement and an `expected_fail()` declaration must land together, and neither ships while any tripwire is armed.
*Text to add:* "A known-red gate with a filed ticket is named with its ref in the packet and left red — never silently relaxed, re-pointed, or downgraded to a warning (a quiet downgrade is how a real regression later goes unnoticed). Before making a soft failure hard, enumerate what else that gate holds: if flipping it blocks every tracked known-red at once, the enforcement and the exempt/expected-fail declaration are one landing, not two — the hardening cannot ship while any carried red is armed."

**P7 — A figure carries its basis or it does not exist.** NEW → `aetheris-agents/CLAUDE.md` (sharpens D4/no-fabrication).
*Incident:* t4's `monthly_cost_estimate` and `rate_basis` are emitted together-or-not-at-all; a figure without `{rate, unit, source, as_of}` is unrepresentable by construction, and any dimension without a constant omits-and-warns rather than borrowing a neighbour's rate.
*Text to add:* "A computed figure ships with its provenance (rate/source/as-of, or the derivation) or it does not ship — a number without a checkable basis is indistinguishable from a fabricated one. Make presence-together structural (the value and its basis are one object), and for any input dimension you have no basis for, omit and say so — never substitute a plausible neighbour."

---

**Placement note (claude-ui).** P2, P4, P5, P6, P7 are repo-agnostic review discipline. Homed in
`aetheris-agents/CLAUDE.md` because that is where this milestone's learnings sit; if cross-repo
learnings are kept in a shared spot, hoist them there rather than duplicating into
`aetheris/CLAUDE.md` — the home is the arbiter's call, the text is the same either way.
