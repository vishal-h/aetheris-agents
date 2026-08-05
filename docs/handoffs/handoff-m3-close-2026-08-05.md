# Handoff — m3-cloudcost close → next cycle — 2026-08-05

> Not exported to project knowledge — handoffs never carry a manifest row. Commit to
> `docs/handoffs/` and attach it to the next claude-ui session.

## Status

**m3-cloudcost is CLOSED** — Linode landed as provider three, report-only, read-only. Three
tickets, eight review rounds, the click-through gate passed on both surfaces, the export
boundary closed with the store verified from the project-knowledge side.

Repo state **verified at commit time and corrected where it moved**: aetheris-agents
`main@348bb93` — `f29cd35` at close; the two commits since are unexported backlog briefs
(`a915f96` uc-inbox, `348bb93` payslip-view-report), neither touching cloudcost or the manifest.
aetheris `main@aaf0f9a` — unchanged since close. Both level with origin.
`drift_check --strict` re-run at `348bb93`: 8 PASS / 0 FAIL / 3 WARN — unchanged from close,
every WARN the strict-exempt `project_knowledge` staleness class from post-boundary commits
(`backlog-2026-06.md`, `CLAUDE.md`, `milestone-methodology.md`), all clearing at the next export.

## Triad rules (unchanged)

claude-ui = design + review, never touches the repos; claude-code implements, fresh session per
ticket; the human relays packets verbatim and arbitrates. Pushes held for review.
Offline-pytest-against-fixtures is the test spine. claude-ui's doc edits are section-scoped,
applied against HEAD and diffed.

## The bet, after three instances

A new provider = a new adapter + its fixtures + its own run. At m3's close the four shared
scripts — `detect_orphans.py`, `compose_report_data.py`, `render_report.py`, `_normalized.py` —
were **byte-identical to `dc8c077`**, mutation-checked, and the shared engine produced a real
candidate from Linode-shaped input on the live run. No §Normalized extension was needed: every
in-scope class mapped onto an existing canonical type. §D-C's pre-authorised extension went
unused, which is itself the result.

## Review-discipline learnings — in `CLAUDE.md`, deliberately not restated here

The previous handoff carried a section headed *"Review-discipline learnings promoted"* whose
four rules were **absent from both `CLAUDE.md` files**. They held for three m3 tickets only
because each kickoff restated them by hand. That is now fixed — the four are promoted, along
with five m3 learnings and a credential-provenance rule — and `milestone-methodology.md` §7
gained a verification step so a promotion is not complete until the entry can be read out of the
file.

So this handoff carries **no learnings section by design**. They are in
`aetheris/CLAUDE.md` §Continuous learning → Workflow patterns and `aetheris-agents/CLAUDE.md`
§Definition of done — doc sync. Read them there. A handoff that restates a rule is how the rule
stops being read where it lives.

## Queued work, in the order it should happen

1. **BL-069 — a durable ≥1-orphan fixture.** Do this first. The assertion is now red on **all
   three legs**: DO's planted reserved IP was deleted 2026-07-30, AWS's Elastic IP is
   `m2-milestone.md` §Prereqs 3 and still pending, and m3's Linode NodeBalancer plant was
   deleted after the run. A tripwire that fails on every run trains everyone to skip the line —
   the same "signal trained into noise" argument BL-100 makes about `no-json`. m3 proved the
   assertion *can* go green for the right reason with a real dollar figure; what it lacks is a
   fixture that does not evaporate. The row's own fix is re-pointing it at a recorded fixture.

2. **BL-099 + BL-100 + BL-104 — one pass over the cloudcost sprint case, not three.** They edit
   the same block and two of them interact: BL-104 inverts `CC_HERMETIC` from a denylist to an
   allowlist, which changes what reaches the child at all, so BL-099's per-provider credential
   grep must still see that provider's credential; BL-100's stream-splitting option changes what
   that grep searches. The interaction is only visible reading them together. This is also the
   file that produced three Linode-shaped defects found by tickets that could not fix them — and
   it is the file every new provider touches.

3. **BL-074 — the seam sweep. This is the gate on provider four, not a nice-to-have.** Every
   close since m1 has said "before provider four, read BL-074." It enumerates whether the
   remaining values a provider could legitimately differ on — the rule-catalog age thresholds,
   `KEEP_TAG`'s spelling, `EPHEMERAL_NAME_PATTERN`, `TAGGED_ACCOUNT_COVERAGE_THRESHOLD` — are
   schema-level or adapter-owned. m3 confirmed the `KEEP_TAG` finding on Linode (flat string
   tags, so `k=v` is an adapter convention wearing a shared constant's clothes). Running it tells
   you whether the next provider is mechanical before you commit to one.

**Independent of all three, and the only queued item a person sees: BL-101 with BL-070.** One
pass over `compose_report_data.py` — surface the tags themselves rather than a coverage
percentage, and retire the now-unreachable cross-provider merge code. `compose` has been
byte-unchanged since m1 and its stillness was the negative proof for two milestones, so opening
it once beats twice. Start here if visible value beats infrastructure.

## Open design item — GitHub as provider four is not provider-shaped

Raised at close, undecided, and larger than the provider count suggests. **GitHub would be the
first non-IaaS provider.** The canonical type set — `compute_instance`, `volume`, `static_ip`,
`snapshot`, `load_balancer`, `database` — maps to essentially nothing GitHub bills for: seats,
Actions minutes, packages, LFS storage, Copilot. The orphan analogue is an unused seat or a
self-hosted runner nobody schedules to, and none of it carries an attachment relation, which is
the primary signal every current rule keys on.

So GitHub tests whether the frozen contract generalises **past IaaS at all**, which is a
different question from the one m2 and m3 answered, and it very likely needs the §Normalized
extension §D-C pre-authorised and m3 never used. Decide that deliberately in an issue-doc, not
at t1. GCP is the other candidate and is a design milestone too — its billing arrives through a
BigQuery export path m1 deferred by name.

## Live tripwires (carried)

- **BL-069** — armed and red on all three legs; see queued item 1.
- **BL-077** — sprint `fail` prints and returns, setting no exit status. Read the `[OK]`/`[FAIL]`
  lines, never `$?`.
- **Artifact periods are not the wall clock.** A Linode run reads the newest *settled* invoice,
  so its artifacts are named for the month they COVER — a run on 2026-08-05 writes
  `cloudcost_report_2026-07.html` (m3 §Seam 7). Never construct one of these filenames from
  `date -u +%Y-%m`; the sprint used to and it was right for two providers and wrong for the third.

## Cold set (parked, trigger-fired)

BL-071, BL-078, BL-087, BL-088, BL-089, BL-091, BL-093, BL-095, BL-098, BL-102, BL-103. Each
fires on its trigger or when someone is already in the file. BL-098 is the one to know about
before touching the inventory schema: adding an extras key obliges all three adapters to emit it.

## How this cycle ran — proposed at close, not yet ratified

The three tickets took 3 + 2 + 2 review rounds, which is normal and produced the real catches.
The long tail was not ticket work: six revisions to the milestone doc, four of them correcting
figures claude-ui asserted from a scout or a packet rather than from HEAD — "three manifests"
(six), "seven scripts" (eight), `:2394` (`:2393`), `:2371-2373` (`:2383-2386`), "two ordinal
citations" (thirteen). claude-ui has no repo access by design, so every checkable specific it
authors is inferred, which is structurally guaranteed to drift.

Four changes proposed, **none ratified — the next cycle's human decides**:

1. claude-ui asserts no checkable specifics in specs it authors; anchors only, and where a
   number is needed the ticket says *verify and record* rather than stating a value.
2. **A verification pass before ratification, not after** — one claude-code session checks every
   checkable claim in a drafted doc against HEAD before it is committed. This caught two errors
   in the promotion set for the cost of a paragraph; the milestone doc never got it and paid in
   four revisions.
3. Corrections batch to ticket boundaries rather than issuing one per discovery.
4. A close has an explicit stop line; anything found after it goes to a list for the next
   milestone rather than being worked immediately. Everything after t3 merged — BL-101 through
   BL-104, the BL-002 post-upload step, the §7 amendment, the ordinal clause — was work generated
   at the close, each defensible alone and cumulatively drift.

## First move

Not a milestone doc. The next cycle opens with a decision the human owns: **the consolidation
sequence above (1 → 2 → 3), or the BL-101/BL-070 value pass, or a provider-four issue-doc.**
If provider four, BL-074's sweep runs first and its result decides whether the next milestone is
mechanical or a design one.

`Source: m3-cloudcost close, 2026-08-05.`
