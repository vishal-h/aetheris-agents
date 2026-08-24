# uc-almanac — Obligation Calendar & Status Ledger (design brief)

**Status:** parked — design largely closed, scope decision recorded (§3). Not scheduled.
**Type:** design brief. §12 lists what remains open.
**Date:** 2026-08-13
**Depends on:** uc-inbox (Telegram adapter) · E-cluster E2/E3/E6 (deployment directory)

---

## 1. Name

**`almanac`** — a book of recurring dates and obligations. Matches the register of
`provenance` and `eduloka`, spans compliance *and* payments *and* payroll without
privileging one, and does not overpromise automation.

Considered: `docket` (drier, precise — a list of matters with dates), `panchang` (more
distinctive; literally "the calendar that tells you what to do when"). **Rejected:
`tally`** — it means accounting software to every Indian finance person who reads it.

Run `python3 -c "import almanac"` before committing to the directory name
(`agent-creation-guide.md` → Python package naming).

---

## 2. Framing — the first system-of-record use case

Recurring org-level obligations — TDS by the 7th, PT and GST by the 20th, quarterly
filings, advance tax, company accounts, salary disbursement, and cloud provider payments
that cannot be automated because RBI does not permit recurring card mandates in India.

**What makes this different from every prior use case:** payslip, docbuilder, and
cloudcost *produce artifacts*. If one is wrong you regenerate it. Almanac *holds state
you rely on*. If it is wrong you miss a statutory deadline and pay interest and penalty.

That is a step change in what Aetheris is, and almanac is the test of whether the
one-surface thesis survives contact with something consequential.

### Two systems, not one

Conflating these is the usual failure — put both in one spreadsheet and they drift on
the first manual edit.

| | Nature |
|---|---|
| **Schedule** | A pure function: `(catalogue, profile, date range) → occurrences`. Deterministic, regenerable, zero LLM. |
| **Ledger** | Mutable state: which occurrence is settled, when, with what evidence. Append-only. |

The schedule is **derived** on every run. The status is **recorded**, never derived.

---

## 3. Settled parameters

| Question | Answer | Consequence |
|---|---|---|
| Multi-entity? | **Yes, from day one** | Forces the catalogue/profile split (§4). |
| Seed rules exist today? | **No** — different people handle different obligations; consolidation *is* the value | Bootstrap is an interview, not an import (§9). |
| Commercial destination | Managed services or build-operate-transfer; customer-facing LiveView planned if viable | The editorial burden is the product, not overhead (§11). |
| Surfaces | Rig = operator console (unpolished, yours). LiveView = client surface, later. | No client-facing polish debt in Rig. |
| v1 scope | **Bitloka as entity zero**, structured so multi-entity needs no refactor | Dogfooding is the pilot, not a de-risking step. |
| Applicability | **Explicit per entity in v1**, not derived from turnover/thresholds | An inference engine that silently changes a filing calendar is not what you want first. Record entity facts alongside so derivation can come later as a *proposal*. |

---

## 4. Architecture — catalogue and profile

The single most important structural decision, and it only becomes visible once
multi-entity is committed.

**Obligation catalogue** — shared statutory truth, authored once. *"TDS: monthly, due
7th of the following month, shift policy X."* Not specific to any company.

**Entity profile** — what is true of *this* entity: state of PT registration, GST
monthly vs QRMP, entity type, registration identifiers, channel binding, which
catalogue obligations apply.

Model rules per-entity instead and statutory knowledge is duplicated N times and drifts
on the first rate change. Onboarding entity #12 must be *filling a profile*, not
authoring rules.

### Distribution — catalogue as a pinned pack

The profile lives in the client's **deployment directory** (QM Pattern 1 / E6). The
catalogue does **not** — it is not client-specific material.

- Catalogue is a **versioned pack**, authored once, distributed by reference.
- The deployment directory **pins** it: `catalogue: 2026.08, hash: …`, lockfile-style.
- Updating a client is: bump the pin → revalidate → redeploy. Central authorship,
  client-controlled cadence, and the pin is auditable evidence of which version produced
  which advice.
- Shipping the catalogue inside the release binary is the tempting alternative and is
  **wrong** — statutory changes must not wait on a core release cycle.

This is QM Pattern 4's "skill packs from git repositories" applied to domain data, so it
reuses a decision already taken rather than inventing a mechanism.

### Rules are data, not model knowledge

The largest hazard in the whole idea. Statutory due dates are jurisdiction-specific,
move with budgets and notifications, and are exactly the class of fact a model states
confidently and wrongly.

The catalogue is a hand-authored committed file, reviewed by a named CA, carrying
`last_reviewed_by` and `last_reviewed_on` per version. **No agent populates it from model
knowledge, and neither should any brief — including this one.**

---

## 5. Data model

**Occurrences** carry `source`: `rule` | `email` | `manual`. Provider payment-failure
emails create obligations no rule predicted — event-driven, not calendar-derived. One
field now; expensive to retrofit.

**Occurrences stamp `catalogue_version`.** When a date turns out wrong you must be able
to answer who received it.

**`effective_from` on catalogue rules; `tracking_from` on entity-obligations.** You
*will* discover a missing obligation in month seven. Adding it must not retroactively
generate six months of false "overdue" occurrences.

**Ledger is append-only** — JSONL or SQLite, shaped like docbuilder's
`run_log_writer.py` (append entry, idempotent by key). Never mutate a status; append a
correction. For statutory compliance the audit trail is worth more than the convenience.

### Storage inversion

Google Sheets is the wrong system of record and the right presentation layer. No
transactions, no constraints, and "update status" degenerates into cell-coordinate
arithmetic.

**Ledger is the record; the Sheet is a rendered view pushed to Drive** via the existing
`_drive.py`. This preserves the goal — the operator never touches Drive — and gains the
audit trail.

---

## 6. The hard part is date arithmetic

Not the LLM. Financial year is Apr–Mar. Advance tax is four instalments at rising
cumulative percentages. GST dates vary by return type and turnover band. Due dates
landing on a Sunday or a regional holiday shift by rules that differ per authority.

Requires a **committed holiday calendar as data** plus a **per-rule shift policy**. This
is where the bugs will live, and it is entirely deterministic.

**Done-check:** generate a past financial year's full calendar for a known entity and
assert against a hand-verified list. Strong, cheap, and reusable every time the
catalogue changes.

---

## 7. Almanac has no UI of its own — it speaks through uc-inbox

A calendar you have to remember to look at is a calendar you forget. The value is
T-3 / T-1 / overdue alerts and a periodic digest arriving on Telegram, with status
updates returning on the same channel.

This is the first proof that use cases **compose** rather than duplicate — which is what
makes "many features on one surface" viable at all. It is also a real argument for
building uc-inbox first.

### Entity scoping comes from the channel, not the message text

"TDS paid on 6th Sep" is ambiguous across twelve entities, and making the LLM resolve it
puts the risk in the wrong place. **One Telegram group or topic per entity** — the entity
is implied by *where the message arrived*, exactly as uc-inbox routes on `Delivered-To`
rather than parsing the body. Access control comes free: whoever is in the group can
update that entity.

### The natural-language update

Smaller than it looks, more consequential than it looks.

- **Small:** "TDS paid on 6th Sep" is entity resolution against the *open* occurrence
  list — a closed set of perhaps twenty candidates, not open-ended parsing.
- **Consequential:** it writes to a record about statutory money. A false "paid" costs
  interest and penalty.

Therefore: **echo and confirm before commit** (uc-inbox §7); never resolve to a
non-open occurrence; on ambiguity ask rather than guess.

---

## 8. QM pattern adoption

| Pattern | Application here |
|---|---|
| **P1 — deployment-directory contract** | The entity profile *is* deployment-directory material. Almanac is a **consumer** of the E6 skeleton, not an author of its own. Directory hash answers "which config produced this calendar." |
| **P2 — private clone, never fork** | Profiles contain GSTINs, PANs, portal credentials. Plain-clone private repos only. These identifiers are strict regex-detectable formats, so `validate` and the E5 pre-push sweep can **hard-fail on a PAN or GSTIN outside a deployment directory** — a cheap check the general case does not get. |
| **P3 — tighten-only lattice** | Adapted: a profile legitimately says "PT does not apply — not registered in a PT state." So not literal tighten-only. The rule: **suppressing a catalogue obligation requires a recorded reason and reviewer, and surfaces in `validate` output.** Same spirit — a narrower scope cannot silently widen risk. |
| **P5 — provenance-labelled screening** | Applies when provider failure emails begin driving ledger writes via uc-inbox. External documents mutating a compliance record is precisely the case. Same hardening note uc-inbox already defers. |

---

## 9. Bootstrap — the interview is the first deliverable

No seed rules exist. The precedent is already in the repo: **`taxonomy_session.py`**, the
interactive CLI that interviews a senior auditor and writes `taxonomy.md`. Same shape —
interview the people who each hold a piece, emit catalogue and profile as committed
artifacts.

Two things to get right:

- **React to a checklist; do not free-recall.** People reliably forget obligations when
  asked "what do we owe?" and reliably catch them when shown a list and asked "which of
  these apply?" Sourcing that checklist is a CA task — same stale-knowledge hazard as §4.
- **Expect omissions in year one.** The `tracking_from` field (§5) is what keeps a
  late-discovered obligation from flooding the ledger with false overdue items.

---

## 10. Difficulty

Lowest of the current candidate set. No new infrastructure; mostly deterministic
scripts; one small bounded LLM job.

| Component | Difficulty |
|---|---|
| Rule engine + date arithmetic | Moderate — the real engineering, fully testable |
| Ledger append + correction | Trivial |
| Sheet render + Drive push | Low — plumbing exists (`_drive.py`) |
| NL status resolution | Low — closed-set entity resolution |
| Telegram digest + alerts | Inherited from uc-inbox |
| **Catalogue authorship and upkeep** | **Not an engineering task** — see §11 |

**This is barely an agent**, and that is fine. One orchestrator, mostly `run_command`,
with the LLM earning its keep in exactly one place (§7). Do not over-agent it.

---

## 11. Commercial shape

**The editorial burden inverts.** Self-serve SaaS must make catalogue maintenance
invisible and free, which is why compliance products die on it. A **managed service
bills for exactly that**. Anyone can write a date engine in a weekend; nobody else wants
to own the statutory catalogue across entities and keep it current. That is the moat.

**BOT implication worth pricing now.** At transfer the client takes the deployment
directory, but the catalogue pack is **separable**. They either keep subscribing to
catalogue updates — a clean annuity, best outcome for both sides — or they fork it and it
rots within two budget cycles. Design the pin and distribution so a *transferred*
instance can keep pulling updates without you operating anything.

**Instrument from entity one.** Managed services scales with people, not code. Every
entity adds recurring human operation: reviewing profiles, confirming applicability
changes, chasing status updates that never arrived. **Log operator interventions as
recorded events** — the event log exists, so "a human had to touch this" costs nothing to
capture. If human-minutes-per-entity-per-month does not fall as entities accumulate, the
model does not scale, and you want that at entity three, not entity thirty. It is also
the number that prices the service.

**Trajectories become client-facing evidence.** In a compliance service, disputes are
about who knew what when. Run records answer natively — "here is the run that sent the
T-3 reminder on the 3rd." Determinism was built for replay; here it doubles as
evidentiary record, which internal use would never have surfaced.

**Non-authority framing is load-bearing.** This is a tracker, not tax advice. Every
rendered calendar carries an "as of" and the catalogue version's named reviewer. That is
what makes it sellable *to* a CA firm rather than a liability *for* one.

---

## 12. Open questions

1. **Who authors catalogue v1, and at what review cadence?** The single dependency the
   engineering cannot absorb.
2. **Does v1 need a Rig panel**, or are Telegram alerts plus the rendered Sheet
   sufficient? Answering this also picks the ledger store — JSONL is simplest and enough
   for render-and-notify; SQLite if Rig needs to query.
3. **What evidence does a settled occurrence capture?** A payment reference / UTR /
   challan number materially raises evidentiary value and changes the ledger schema.
   Decide before the first write, not after.
4. **Scheduling** — the daily tick is cron-shaped and should fit harness
   `scheduled_runs` cleanly (unlike uc-inbox's long-poll loop). Confirm when E-cluster
   lands.
5. **Kill criterion.** If almanac goes unused for two months, is it deleted? Cheap to
   agree now, hard to agree later, and it is what keeps the one-surface promise credible.

---

## 13. Suggested first milestone shape (not tickets)

1. Interview session → catalogue v1 + Bitloka profile, both committed artifacts.
2. Date engine + holiday calendar; done-check = regenerate a past FY against a
   hand-verified list.
3. Ledger (append-only) + occurrence generation with `catalogue_version`,
   `effective_from`, `tracking_from`, `source`.
4. Sheet render + Drive push.
5. Telegram digest and T-3 / T-1 / overdue alerts via uc-inbox.
6. NL status update with echo-and-confirm.
7. Entity two — the test of the catalogue/profile split. If adding it touches the
   catalogue, the seam was drawn in the wrong place.

Step 1 gates everything. Steps 2–4 are independent of uc-inbox and can proceed before it
lands.

---

## Appendix — feature-selection test (generalises beyond almanac)

Surfaced while assessing whether almanac was worth building; applies to every "should
this live in Aetheris" question. **Promotion candidate for methodology or `CLAUDE.md`.**

1. **Does the state live in the harness, or does it need a system of record elsewhere?**
   Elsewhere means you are building an integration — the expensive kind.
2. **Is the ongoing cost engineering or editorial?** The harness makes execution cheap.
   It does not make domain-data maintenance, integration surface, or UI cheap.
3. **Does it need more UI than a list and a detail pane?**
4. **What is the kill criterion?**

Almanac passes 1, 3, and 4 cleanly and fails 2 — which is exactly why the commercial
model (§11) is the decision that matters, since it is what converts that failure into
the product.
