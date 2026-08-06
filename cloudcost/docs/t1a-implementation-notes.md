# t1a — implementation notes

**Ticket:** t1a v5 — correct the false causal claim in every standing carrier.
**Date:** 2026-08-06.
**Verified at:** `aetheris-agents@90c7c67`, `aetheris@aaf0f9a` — both clean, level with origin by
sha equality at the moment of acting. Every citation in this file and in the edits is pinned to
those two shas.
**Repos touched:** both. No code change in either; every edit is a `.md` file.

---

## 1. What was wrong

A causal claim — that merging stderr into stdout (`2>&1`) is what makes the sprint's `--json`
reads unparseable — is false.

**Established by demonstration, not inference:**

```
$ mix aetheris --json list --limit 1 2>/dev/null        # stdout only
07:51:25.434 [warning] [Aetheris.Application] failed to resume run bl031-paused-demo-2658: …
07:51:25.436 [info]    [Aetheris.Scheduler] started run run_5S_eBQ for schedule 'news-sprint-…'
07:51:25.460 [info]    [Aetheris.Application] orphan sweep: %{errors: 0, …}
{"entries":[{"id":"run_5S_eBQ","label":"","status":"running","type":"run","started_at":"…"}]}

$ mix aetheris --json list --limit 1 2>&1 >/dev/null    # stderr only
(nothing)
```

The harness's **Logger output shares stdout with the payload**. The merge is irrelevant.

**Two things this does NOT establish, held deliberately:**

- Whether `[sandbox]` lines go to stdout or stderr. **Not established** — the command above spawns
  no worker. No edit made in this ticket asserts anything about that routing in either direction.
- That stream splitting "could never have worked". It is not sufficient *now*; whether it sufficed
  in an earlier era depends on `[sandbox]` routing. Installing an unverifiable absolute in a
  correction whose purpose is removing one would be the error repeating a level up.

**The correction text, used verbatim at every site:**

> Stream splitting is **not sufficient**: it cannot restore parseability in any environment where
> the harness emits Logger output on stdout, which is every capture in this repo from 2026-07
> onward. Whether it sufficed earlier depends on `[sandbox]` routing, which is unestablished.

## 2. The sharper finding the census exposed

**The reads are non-deterministic, not uniformly broken.** Identical expressions succeed or fail
by environment:

| Capture set | `jq` parses? |
|---|---|
| `../aetheris/sprint/20260521_075730/news/day{1,3}.json` + schedule_trigger | 4 of 4 **succeed** |
| `../aetheris/sprint/*/payslip/run.json` | 0 of 8 |
| `../aetheris/sprint/*/cloudcost/run.json` | 0 of 10 |

Same helper (`run_agent`), same `> file 2>&1` redirect.

**Corrected after round-1 review, finding 2 — the mechanism was over-claimed.** An earlier draft of
this section, and of the `claude-notes.md` replacement, said the contaminating Logger lines "are
emitted only when there is state to report". That is true of one line and false of the other:

- **Resume-failure lines** (`[Aetheris.Application] failed to resume run …`) *are* store-state
  dependent. The clean 2026-05-21 07:57 capture was written **after** that code existed
  (`../aetheris/lib/aetheris/application.ex`, 2026-05-20) and carries none — so for this line,
  presence tracks store state, not code age.
- **The orphan-sweep line is NOT state-conditional.** It logs with every counter at zero —
  `orphan sweep: %{errors: 0, running_before: 0, orphaned: 0, reconciled: 0, skipped_live: 0,
  skipped_paused: 0, skipped_recent: 0}` — and is gated on `config :aetheris, :sweep_on_start`
  (`../aetheris/config/config.exs`), not on there being anything to sweep. It also **did not exist
  until 2026-07-15** (`0188a90`, BL-003), so its absence from the May captures is a version
  boundary, not an environment one.
- **`[sandbox]` lines** head the May payslip captures ahead of any Logger line, and their stream
  routing is **not established**.

So the *variation* (4/4, 0/8, 0/10) is evidenced; a single mechanism covering all of it is not.
Attributing a given file's failure to one cause without checking which lines it carries is the
error this ticket exists to retire, and it had reproduced inside the correction itself.

This is why the fix makes the reads **deterministic** rather than "makes every read work" — some
already work, which is the defect.

## 3. The census — method, terms, and every hit

**Method (ratified in v4 after four rounds of a token-keyed search missing sites):** search the
claim's *substance*, not a token. A census keyed on `2>&1` finds `2>&1`, not the class.

**Search terms used.** Ratified minimum: `no-json`, `unparseable`, `mixed output`, `log noise`,
`boot output`, `log line prefix`, `orb_id=n/a`, `Run ID: n/a`, `sandbox`, `2>&1`, `stderr`.
Extensions the results suggested: `mixes stderr`, `stderr (sandbox`, `sandbox stderr`,
`Sandbox log lines`, `boot warnings`, `log noise before`, `stdout.*stderr`, `stderr.*stdout`.

**Scope.** Both repos, `find . -name "*.md*"` — the `*.md*` glob deliberately catches irregular
extensions, which is the only reason `handoff-m09-m10.md.md` (double extension) enters the census.
`.git/`, `deps/`, `_build/` excluded.

**Classification criterion.** **Standing** — states current behaviour or its cause as a fact a
reader would act on. **Historical** — a dated record of what was believed then; correcting it would
falsify the record, so it is left intact.

**Convergence.** The census was derived three times at these shas with the term set above and
returned an identical set each time. No novel standing site appeared, so the ticket's
undecidable-default clause was not exercised.

**Why an earlier round's hit list differs — corrected at round 3, and the first explanation was
wrong.** A v4-era record lists `cloudcost/docs/m3-t3-implementation-notes.md` at `:160`, `:199`,
`:235`; the classification census lists `:159` and `:167`. Round 2 explained this as "different
term sets, both correct". **That explanation cannot be true as stated** — `2>&1` is in the
ratified minimum quoted above, and a superset cannot return fewer hits than one of its own terms.
The reviewer was right to reject it.

**The actual reconciliation: the documented term set is not the executed one.** The census ran in
two passes, and only the second is what the classification rests on:

- **Pass 1 — the ratified minimum**, exactly as quoted above. It returned ~31 KB of hits,
  overwhelmingly unrelated uses of `stdout`/`stderr` (script conventions, tool-result payload
  shapes, unparseable *dates*).
- **Pass 2 — a tightened claim-bearing filter**, which is what produced the classification:
  `no-json|orb_id=n/a|Run ID: n/a|log line prefix|log noise before|mixes stderr|stderr \(sandbox|`
  `sandbox stderr|Sandbox log lines|boot output|boot warnings`. It **excludes** `2>&1`,
  `unparseable` and `mixed output`.

So `:160/:199/:235` match `2>&1`, a term pass 2 does not use; `:159/:167` match `no-json`, which
both use. **The `:160`→`:159` "shift" is not a shift** — they are different lines matched by
different patterns, adjacent in the same paragraph.

**Did tightening lose a site?** Checked rather than assumed: of every document matched by pass 1
but not pass 2 across both repos, exactly one is claim-shaped —
`cloudcost/docs/m3-linode-scout.md`, which this census already records as **out of scope** (it
quotes the command line and asserts no cause). No standing site was lost.

**The defect this exposes is in the method record, not the census.** §3 documented the ratified
minimum as though it were what ran. The method is a deliverable; a deliverable that misdescribes
what executed is the same class this ticket exists to close. Both passes are now recorded.

### Standing — corrected (7 sites, 6 documents)

| Site | Class | Treatment |
|---|---|---|
| agents `docs/backlog-2026-06.md` — BL-100 body | open row | corrected in place; heading, Size (XS → S–M), cause, scope, fix and Done-when all revised, with each change marked `[corrected 2026-08-06]` and the superseded text kept beneath |
| agents `cloudcost/m3-milestone.md`:599-601 | closed record | dated superseded note; two defects named — the cause, and "Display only", false at the chaos gate |
| harness `docs/aetheris/claude-notes.md` — §"Claude Code — sprint output parsing" **and** the second passage below it | live guidance | corrected in place, **document-scoped**; grep filters replaced with a tested backward scan |
| harness `docs/aetheris/runbook-m10b.md`:93-99 §Inspecting results | closed record | dated note |
| harness `docs/aetheris/runbook-m10b.md`:229-236 troubleshooting entry | closed record | dated note |
| harness `docs/aetheris/milestones/handoff-m10b-m11.md`:116 | closed record | dated note, **conclusion only** |
| harness `docs/aetheris/milestones/milestone-reference.md`:116 | undecidable → default | dated note (see §5) |

**Tie-breaker applied to `runbook-m10b.md`:** a current equivalent exists —
`../aetheris/docs/aetheris/runbook.md`, which is manifest-tracked and **clean of the claim**
(verified) — so the milestone-named runbook is a closed record and takes notes rather than an
in-place rewrite. Establishing this, rather than inferring from the filename, moved two sites from
one treatment to the other.

**Document-scoping caught a site a section-scope would have missed:** `claude-notes.md`'s second
passage sits *outside* the §"Claude Code — sprint output parsing" section, after its closing code
fence. Editing the named section alone would have left it standing.

### Standing — deferred to the fix ticket, not omitted (2)

`docbuilder/milestone.md`:88 and `docbuilder/docs/m1-milestone.md`:680 carry byte-identical text
calling the behaviour cosmetic noise and holding an open TODO to trace its cause. Two reasons for
deferral, both ratified: the characterisation is false for the class (one affected site is a gate),
and the TODO is discharged by the *fix*, not by this ticket — writing "discharged" here would land
a claim in the same commit as the thing that would make it true. Note these two do **not** carry
the `2>&1` claim; an earlier draft asserted they did, and following it would have written a false
correction into a ticket about a false claim.

### Historical — left intact (13)

agents: `docs/reviews/m1-cloudcost-t5-review.md`:63 ·
`docs/reviews/m3-cloudcost-t3-review.md`:20,:28 · `docs/handoffs/handoff-m3-close-2026-08-05.md`:56 ·
`docbuilder/docs/milestones/m-docbuilder-m1-t7-implementation-notes.md`:67 ·
`docbuilder/docs/reviews/m-docbuilder-m1-t7-review.md`:35 · `…m1-t8-review.md`:32 ·
`…m5-t2-review.md`:37 · `cloudcost/docs/m3-t3-implementation-notes.md`:159,:167 ·
`cloudcost/docs/m2-t3-implementation-notes.md`:44,:67

harness: `docs/reviews/bl-048-fs-hash-diagnosis.md`:213 (different subject)

Worth noting: `m-docbuilder-m1-t7-implementation-notes.md`:67 carries the *correct* diagnosis
(*"log noise before the JSON line"*), written 2026-06 and never acted on.

### Out of scope — recorded, not treated (2)

- `../aetheris/docs/aetheris/milestones/handoff-m09-m10.md.md`:145 — attributes the `n/a` step
  count to `step_count` being absent from the `--json` payload. A **different** diagnosis, and
  historical by the criterion. It may itself be wrong: `extract_step_count`
  (`../aetheris/scripts/sprint.sh:79-81`) already reads from `mix aetheris inspect`, and its
  failure appears to trace to the fragile `.run_id` read above it. **Not established** — not
  chased. Left to the fix ticket.
- `../aetheris/docs/aetheris/runbook-m09-sandbox.md`:400 — `# Run with stderr visible to see
  sandbox log lines`. A comment about making sandbox logs visible during a smoke run; asserts
  nothing about parseability.

### G3 — no standing carrier is a contract document

Checked explicitly rather than assumed; all clean of the claim:
`../aetheris/docs/aetheris/runbook.md` (the live, manifest-tracked runbook) ·
`../aetheris/CLAUDE.md` · `CLAUDE.md` (agents) ·
`../aetheris/docs/methodology/milestone-methodology.md` ·
`../aetheris/docs/aetheris/architecture.md` · `docs/rig/specs.md` · `docs/agent-creation-guide.md`.

Had the live runbook carried it, the ticket would have stopped: it is both a standing carrier and
an exported project-knowledge document, and correcting normative text is a different act with
different review.

## 4. The replacement guidance, and why it is what it is

`claude-notes.md` now prescribes a **backward scan for the last line that parses as a JSON
object**, replacing `grep -v '^\[sandbox\]' | grep -v '^\d\d:\d\d'`.

Reasons, in order of weight:

1. It holds regardless of `[sandbox]` routing — the thing we could not establish.
2. It holds regardless of store state — the thing that makes the reads non-deterministic.
3. It holds whether noise lands **before or after** the payload. Both occur.
4. It fails loudly when there is no payload, rather than printing a fabricated status.

**`tail -1` is not sufficient**, and this is evidenced rather than argued: three captured files
carry worker output *after* the payload —
`../aetheris/sprint/2026052{1_202137,2_090058,2_095912}/payslip/run.json`, each ending in five
`aetheris_worker fatal: Broken pipe (os error 32)` lines below the JSON.

**The command was run before it was documented**, against all four shapes present in `sprint/`:

| Capture | Shape | Result |
|---|---|---|
| `20260805_134754/cloudcost/run.json` | Logger noise before payload | payload returned |
| `20260522_090058/payslip/run.json` | worker output **after** payload | payload returned |
| `20260521_075730/news/day1.json` | clean, single line, no noise | payload returned |
| `20260521_191506/payslip/run.json` | **no payload at all** | `no JSON payload found …`, exit 1 |

The fourth row is the mutation posture: the guidance was watched failing in the state it guards
against, not only passing.

## 5. The `milestone-reference.md` ruling

Two files carry the name. Liveness was undecidable after the rule and its tie-breaker, so the
ticket's ratified **non-destructive default** applied: take the note.

- `../aetheris/docs/aetheris/milestone-reference.md` — 12 lines, **clean of the claim**, and the
  target of every cross-reference in the repo (`claude-notes.md`, and the "Add to
  `docs/aetheris/milestone-reference.md`" instructions in `m11-eval-framework.md`,
  `m12-hierarchical-delegation.md` ×2, `m13-persistent-agents.md`, `ollama-xml-milestone.md`,
  `handoff-m12-m13.md`, `remove-nif.md`). **Not touched**, per the ticket.
- `../aetheris/docs/aetheris/milestones/milestone-reference.md` — the substantive index, carries
  the claim, **annotated**.

Canonical-by-reference-graph and canonical-by-content are different files, and the record cannot
order them: both were last touched 2026-05-27 and neither covers past m13. The asymmetry decided
it — a note on a live document still delivers the correction; an in-place rewrite of what turns out
to be a record falsifies it irreversibly. The duplication itself is filed as **BL-109**; resolving
it is not this ticket's scope.

## 6. Rows filed

| Row | Subject |
|---|---|
| **BL-105** | the `--json` payload shares stdout with Logger output; consequence is non-determinism; Rig parses this output |
| **BL-106** | `--json` emits no JSON document on a non-success run; sibling of BL-105; the consumer compensates by parsing prose |
| **BL-107** | the chaos-case gate has never evaluated its subject; both claims qualified; the gate rule's tracked ticket |
| **BL-108** | the eduloka sink gate — same shape, different root cause; evidence indicates it passes; one env-var check remains |
| **BL-109** | two `milestone-reference.md` files, canonical by different measures |

BL-100 was **not** closed — the fix has not landed.

## 7. Scope confirmation (not a deviation)

*Reframed after round-1 review, finding 4.* This section previously called the BL-100 handling a
deviation. It is not. The ratified treatment table read `agents docs/backlog-2026-06.md BL-100
body — corrected in place (open row)`, and the Touches entry instructed correcting the causal
claim, rescoping the subject and updating the Size field. Correcting the candidate-fixes
paragraph, the Done-when and the signal-recovery justification is **inside** that instruction, not
outside it.

What was done: because BL-100 is an open row — text someone will act on — leaving those paragraphs
unqualified would have left the dead stream-splitting branch reading as live guidance. Each is
marked `[corrected 2026-08-06]`, with the superseded wording kept beneath under *"Original …,
superseded, kept as the record"*. **No deviation from the ticket was taken.**

## 7b. Carries into t1b and into the promotion set (round-1 review, findings 6 and 7)

Recorded here rather than filed as rows, per the reviewer's disposition — each has exactly two
named consumers, and prose in a packet files nothing.

**1. Assert-versus-retract classification (finding 6).** This ticket's own superseded notes quote
the claim they retract, so the ratified substance-search now returns roughly a dozen hits across
the six edited documents that are **corrections, not carriers**. The method as ratified classifies
by term match alone and would mis-flag every one. Carries to:
- **t1b's census method** — as an explicit assert-versus-retract step before classification.
- **The promotion candidate** *"search the claim's substance, not a token"* — so the rule ships
  with its own hazard attached rather than acquiring it later.

**2. The multiple-payload question (finding 7).** The backward scan takes the *last* line that
parses as a JSON object. If a file carried more than one, "the last" may be the wrong one. Across
the 50 `run.json` captures in `../aetheris/sprint/`, **zero** carry more than one parsing JSON
object — so the case has never been observed here, and nothing in the CLI's contract excludes it.
The guidance in `claude-notes.md` is now qualified accordingly. Carries to:
- **t1b**, which ports this scan from documentation into a `sprint.sh` assertion. There, being
  wrong is a false pass rather than a misleading read, so the question is owed an answer before
  the mechanism lands — either a contract statement that at most one payload is emitted, or a
  scan that detects and reports multiplicity instead of silently taking the last.

**3. Cwd-independent commands (round-2 finding N1).** Three times in this ticket a bare `cd` in a
compound command persisted into a later stage and pointed a check at the wrong repo: the v5 G4
attribution check (caught, self-evidently wrong), the review packet's §2b diff (not caught — it
became a blocking review finding), and the round-1 commit itself (failed loudly, nothing
miscommitted). A cwd defect that redirects a grep is indistinguishable from a clean negative
result — Silent-wrong-answer applied to the verification apparatus. Carries to **t1b's method**:
every repo-scoped command in a gate or census uses `git -C` or an absolute path, and the report
says which. All G0–G5 checks were re-run under that rule at the round-2 disposition; no ruling
moved (see the packet's N1 section).

## 8. Not established

Carried forward rather than resolved or papered over:

- `[sandbox]` line routing — the available test command spawns no worker.
- Which document first carried the claim. Three harness documents acquired it on 2026-05-18 and
  same-day ordering is not recoverable from the record. **No origin claim appears in any edit.**
- Whether `handoff-m09-m10.md.md`:145's step-count diagnosis is correct.
- Whether the chaos gate has ever run in a clean-store environment — no chaos output has ever been
  captured, so "it has always warned" is inference, and every edit says so.
- Whether `EDUX_DATABASE_URL` is set in the sprint's ambient environment (decides BL-108).
- Which `milestone-reference.md` survives (BL-109).
- Whether a `--json` invocation can ever emit **more than one** parsing JSON object on one stream.
  Zero of 50 captures do; the contract does not exclude it. Blocks nothing here, blocks t1b's
  assertion (§7b).
- Whether `[sandbox]` lines are what break the May-era payslip captures specifically. Those files
  carry both `[sandbox]` and Logger lines, with `[sandbox]` first, so the Logger finding explains
  the 2026-07+ failures but is not established as the cause of the May ones.

## 9. Process note (round-1 review, finding 5)

An earlier draft of this file and of the review packet reported that writing the packet after the
commits violated "the loop's own rule that the packet precedes the commit". **No such rule
exists** — methodology §5 defines the packet as diff + implementation notes + done-check output,
and a diff cannot precede the commit that produces it. The gate is the **push**, which was held
throughout and is still held. What actually happened: commits made locally, packet assembled from
`git show`, nothing pushed. Recorded because an invented rule in a durable document is the same
defect class this ticket exists to close, and this one was self-inflicted.
