# m6 t4 — implementation notes

**The provider-set enumerations m6 is short, and the wiring list that did not name them.**

Measured at agents `97c61a0`, harness `d19f4b6`, both clean and level with origin at the start of
the session. Harness untouched by this ticket.

---

## 1. What this ticket was

m6's close criterion requires that *"the runbook's provider list and wiring section include
GitHub"* (`cloudcost/m6-github.md:379-385`). It did not. Provider four shipped at t2b (`bcb63e6`)
and three places that enumerate the provider set were never updated. One of them is functional
rather than documentary: `docs/capability-matrix.md` is read with `File.read!`
(`agents/orchestrator.exs:17-18`) and interpolated whole into the planner LLM's system prompt
(`:34`), which then tells the planner its agent paths *"must match exactly the file paths listed
in the capability matrix"* (`:54-55`). A script absent from it is a script the planner cannot plan.

This ticket regenerates the matrix, repairs the §Rig enumerations, extends the wiring list, and
files six backlog items. It fixes no code and designs no drift check.

---

## 2. Gate

**(i)** Both repos clean, level with origin.

**(ii)** The m6 t4 read-and-report packet was read as the brief. Every load-bearing claim was
verified at HEAD rather than re-derived. **One disagreement**, recorded in §7a and carried into
BL-154's text: the packet's *"runs.status stuck at 'running' permanently"* is too strong, and its
description of the sweep as something *"the normal completion path performs"* is wrong.

**(iii) Companion artifacts and companion practices.** Established per *kind of change*, not per
file class:

| kind of change | companion the repo's practice attaches |
|---|---|
| generated doc | the regen ritual, never a hand edit |
| a cell that must survive a regen | an entry in `docs/capability-matrix-overrides.json` (BL-068) |
| runbook prose enumeration | §Adding a provider's wiring-list clause |
| a count in prose about a growing set | de-numeralise (m6 t1's rule) |
| backlog row | `### BL-NNN ` heading — `sprint.sh:104-126` greps it anchored; a dangling ref fails the sprint |
| any manifest-tracked edit | the pin re-stales; check 8 is **post-commit only** |

No omission from the ticket's implied Touches was found.

**(iv) Regen ritual — cost.** Full form is `./scripts/sprint.sh capability_matrix`: **nine LLM
sub-agents** (`../aetheris/scripts/sprint.sh:1533-1570`), one per use case, each rewriting its own
`docs/.sections/{uc}.md` (gitignored scratch), then the **deterministic, no-LLM**
`scripts/assemble_matrix.py`. Regeneration is per-section (LLM); assembly is whole-file
(deterministic). A single-section re-run is explicitly sanctioned at
`docs/capability-matrix-runbook.md:131-148`. The ritual was runnable in this session — no stop.

**A gate step done out of order, recorded rather than smoothed.** This repo's CLAUDE.md requires
every session to read *both* repos' learning sections before its first edit. `../aetheris/CLAUDE.md`
was read **after** W1–W3 had landed, when a contract citation was needed for the W4 rows — not
before the first edit. Nothing in it contradicted work already done (it in fact supplied the exact
carriers the rows now cite), so no rework followed, but the rule was not followed and the reason it
exists is that this is not knowable in advance.

---

## 3. AO2 — the premise, verified before being relied on

The scope ruling rested on the claim that the on-disk sections were in sync with the committed
matrix. That was checked, read-only, before anything was written. Assembling from the on-disk
sections plus the committed overrides reproduced the committed matrix **byte-identically**:

```
assembled == committed : True
assembled md5 e0cc0643bd4d58a9144c01abe4a871d3
committed md5 e0cc0643bd4d58a9144c01abe4a871d3
```

Per section — raw section text against the committed matrix, and post-override-merge text against
it:

| section | raw ⊂ matrix | merged ⊂ matrix | overrides |
|---|---|---|---|
| payslip, drive, email, api_tenant, api_gateway, cloudcost, eduloka | True | True | 0 |
| provenance | False | True | 1 |
| docbuilder | False | True | 11 |

**No section had drifted.** provenance and docbuilder differ from their raw files only because
their 12 curated overrides merge in — the mechanism working, not drift. So neither failure AO2
named had occurred: nobody had regenerated without committing, and nobody had hand-edited the
generated file.

---

## 4. W1 — the regen

**Scope: cloudcost section only** (ruling AO1), via

```bash
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/agents/capability_matrix_cloudcost.exs
python3 ../aetheris-agents/scripts/assemble_matrix.py
```

**The full form exists and was deliberately not used.** Ground: attributability. A diff every line
of which traces to this ticket is reviewable; one carrying eight LLM rewordings of unrelated use
cases is not, and an unrelated rewording arrives with no way to tell a correction from a
regression. The next provider faces the same question and should not re-derive it. **The
assembler still rewrites the whole file**, so the whole-file diff was still produced and read —
the choice narrows what the LLM touches, not what is inspected.

### 4a. The diff, in three blocks (AO3, AO4)

**Block 1 — the cloudcost section.** Not one row was left alone. All eight pre-existing script
rows were reworded, the table was reordered from source order to alphabetical, `fetch_github.py`
was added, and the agent label changed. This is reported in full because the section agent is not
deterministic and a reworded row that was previously fine is still a change this ticket is
accountable for.

**Block 2 — the deterministic derived block.** `| cloudcost | 1 | 8 |` → `| cloudcost | 1 | 9 |`
and `| **Total** | **27** | **84** |` → `**85**`. The two overlap tables and the unique-tools line
did not move.

**Block 3 — anything outside cloudcost.** **Empty.** Confirmed structurally: the four diff hunks
are at `:198`, `:204-212`, `:273`, `:275` — the cloudcost tables and the summary rows, nothing
else. This is what §3's byte-identity predicted and it held.

**No AO4 stop condition.** No cell is worse than the committed one beyond the two known defects.
Two are materially *better* and were checked rather than assumed: run 2's `render_report.py`
purpose claims an *"optional PDF companion"*, which is real (`render_report.py:43`, `:86`,
`:261-276` — `--pdf` via `wkhtmltopdf`), and its `fetch_linode.py` purpose says *"static IPs"*
where the committed text said *"reserved IPs"* — `static_ip` is the **canonical vocabulary** term
(`fetch_linode.py:827-852`, `TYPE_STATIC_IP`), so the regen is more precise than the text it
replaced. `detect_orphans.py` also gained *"idle seats"*, which is m6 t3's rule.

### 4b. The `{provider}` placeholder — and what the regen actually showed

**The regen did not reproduce it.** It produced something different, twice. Three regenerations of
the same section over an unchanged tree gave three different agent labels:

| source | label |
|---|---|
| committed (`4d98ec2`, m3 t3) | `Cloudcost · {provider}` |
| run `cap-matrix-cloudcost-fEUkDw` | `Cloudcost Orchestrator` |
| run `cap-matrix-cloudcost-vcUTlA` | `Cloudcost · DigitalOcean, AWS, Linode, GitHub` |

That is a stronger result than the ticket anticipated and it is the substance of BL-155: the cell
is not stale, it is **unstable**, and all three values reach three consumers unchecked. Every
script purpose was likewise reworded on both runs.

`docs/capability-matrix-runbook.md:79-80` said *"Two runs over unchanged sections produce
byte-identical output, so a matrix diff only ever shows a real change."* True of the **assembler**;
it does not cover the section step, and the table above is the counter-example. Recorded in BL-155
and — at the review of `fcde58c`, on a Touches widening the reviewer ruled — **corrected in that
file as well**. See §11.

**Mechanism and text.** The override mechanism is the intended one and no stop was needed: `label`
is an explicitly overridable agent field (`docs/capability-matrix-runbook.md:106-110`,
`scripts/assemble_matrix.py:269-272`), the file is committed, and the merge happens *before*
anything is counted so the emitted table and the derived block cannot disagree. The **text** was
ruled by the reviewer: **`Cloudcost`**. A bare file key is correct — `cloudcost_orchestrator.exs`
contributes exactly one row (runbook `:111-115`).

**Survival verified by observation, not by reading (AP5).** The override was added, then the
section agent was run **again** — producing the third, different raw label above — and the
assembled matrix still read `Cloudcost`. The assembler reported `13 curated override(s) applied`,
up from 12. So the claim is that an override survived an actual regeneration that changed the cell
underneath it, which is a different and stronger claim than that it ought to.

**Why not a label naming the knob (AP6).** The tempting option was `Cloudcost — one provider per
run (CLOUDCOST_PROVIDER)`, and it is the one to avoid. That string would place the literal
`CLOUDCOST_PROVIDER` into the planner's system prompt as decoration; the planner emits a params
map, and `agents/orchestrator.exs:272-273` `System.put_env`s every param before
`load_agent_file`, so a planner that picked the key out of a label **would actually work**. That
is an accidental mechanism — load-bearing, undocumented, and broken by the first person to shorten
a label. If the planner should know that key it is a deliberate edit to the Known params block,
which BL-085's annotation now owns. `Cloudcost Orchestrator` was also rejected: column 1 of the
same row is already `cloudcost_orchestrator.exs`.

### 4c. `compose_report_data.py`'s row — answered, not fixed

The row still reads *"Merge N providers'…"* against decision H's *"still runs per provider"*.
**Its source is the docstring, not the section agent.** `compose_report_data.py:2` opens *"Merge N
providers' cost + inventory + orphan bundles into one report-data file (m1, t3)."*, and the
section agent is instructed to take the purpose from the docstring, *"first descriptive sentence
only"* (`agents/capability_matrix_cloudcost.exs:49-50`, `:76`). So the cell will keep saying this
for as long as the docstring does, and no amount of regenerating changes it. Not fixed — the
ticket excludes the docstring.

---

## 5. W2 — `cloudcost/runbook.md` §Rig

Four units, each quoted at HEAD before replacement. The **width rule fired on both** units the
ticket named, and found two more of the same class beside them.

| unit | defect | repair |
|---|---|---|
| `:521` + table `:525-533` | credential table omits both GitHub rows; prose says *"seven"* | two rows added; **de-numeralised** to "The rows below" |
| `:615` (was `:608`) | *"The **six** `CLOUDCOST_*` keys"* — same defect, same section, nine keys today | de-numeralised |
| `:543` + `:547` | `# or: digitalocean, linode`; and *"Selecting `aws` or `linode`"* | `github` added to both |
| `:505-507` | run-id and label enumerations list three providers | fourth added |
| `:500` (§Offline tests) | *"recorded DO + AWS + Linode fixtures"* | `+ GitHub` added |

Credential-row wording is taken from the canonical source rather than invented —
`cloudcost/tools.json:286-300`, the `env` rows Rig actually renders from.

**Two things done inside these units that the ticket did not ask for, both stated:**

- **A stale citation corrected.** `:547` cited the provider `case` at
  `cloudcost_orchestrator.exs:53-62`; it is at `:60-69` at HEAD (the Linode and GitHub arms shifted
  it). Corrected because the sentence was being rewritten anyway and a citation that was right when
  written decays silently.
- **`:500` is outside §Rig**, one line above the section boundary, and W2 is scoped to §Rig. Fixed
  rather than left, because it is a prose enumeration of the provider set and the wiring-list clause
  covers it — so leaving it would have meant filing a known instance of a clause this same ticket
  was repairing. Reported under W3c as an instance, not under W2.

**A BL-151 pointer was added under the credential table**, noting that Rig renders every row —
including the two marked optional — under a heading reading *"Required config"*. That is a caption
over the defect so an operator has somewhere correct to read; it is not a fix, and the row says so.

---

## 6. W3 — the wiring list

The clause *"every prose enumeration of the provider set"* was right; its enumeration of four
instances was incomplete. Repaired as an incomplete enumeration, not as a missing clause.

- **W3a** — added §Rig's credential table and §Rig's `CLOUDCOST_PROVIDER` literal list.
- **W3b** — added **a regeneration of `docs/capability-matrix.md`** as a wiring place *in its own
  right*, with the ground in one clause: a generated artefact with three consumers, which BL-090
  closed for provider three without adding the regen to the list, and which was therefore stale
  again at provider four.
- **W3c** — two further **instances** of the existing clause, reported separately from the two
  repairs: §Rig's run-id and label enumeration (`:505-507`) and §Offline tests' fixture comment
  (`:500`). The clause now enumerates eight instances where it enumerated four.

A dated change-note blockquote follows the list, in the established convention (`:711-721`,
`:723-730`).

**Is the list now complete against what this ticket had to touch?** Yes, with one item deliberately
excluded. This ticket touched `docs/capability-matrix.md` (now a place),
`cloudcost/runbook.md` §Rig ×4 (now instances), `docs/backlog-2026-06.md` (not a wiring place), and
`docs/capability-matrix-overrides.json` — which is **not** added, because it was needed to repair a
*pre-existing* defect in a generated cell, not because a provider was added. Provider five will
need no override entry. Adding it would have made the list assert a step that is not owed.

---

## 7. W4 — the rows

Numbers verified free at HEAD: BL-153 was the highest real row. `BL-999` appears in prose only and
is a deliberate dangling-reference decoy — not taken and not usable. New rows appended flat at EOF
in numeric order; `## Suggested order` is retired (BL-145) and was not touched. Every heading was
checked against `sprint.sh:110`'s anchored `^### BL-NNN ` grep, and every `BL-` reference
introduced into `cloudcost/runbook.md` was checked to resolve to a real row.

| item | disposition |
|---|---|
| **BL-154** | NEW — Rig's Cancel kills the direct child only, and transitions nothing |
| **BL-155** | NEW — the capability matrix has three consumers, no gate, and is the one wiring place an LLM writes |
| **BL-156** | NEW — the approval card's step text is written by the planner per run, and nothing checks it |
| **BL-153** | ANNOTATED — a third mechanism |
| **BL-085** | ANNOTATED — the launch door |
| **BL-151** | APPENDED — `EnvDep` has no optionality axis |

### 7a. The W4a disagreement

The brief said `runs.status` is *"stuck at 'running' permanently"* and that the cancel path skips
*"the 'running' → 'failed' sweep the normal completion path performs"*. Both halves are off, and
BL-154 is written to the corrected shape:

- `Aetheris.Sweep` (`../aetheris/lib/aetheris/sweep.ex`) is a **startup and on-demand cure**, not
  part of the completion path. `config :aetheris, :sweep_on_start` is `true`
  (`../aetheris/config/config.exs:15`) and `Aetheris.Application` runs it at every harness start
  (`application.ex:79-89`); `mix aetheris sweep` runs it on demand. This was observed live during
  this ticket's own regen runs, which print `orphan sweep: %{…}` at startup.
- So the row is not stuck permanently. **The defect is what the cure then records**: with no
  terminal event the sweep takes the `orphaned` branch, emits `run_orphaned` and sets `failed` — so
  a deliberately cancelled run is durably recorded as one that died unattended, and the
  distinction is unrecoverable because nothing wrote it down at the time.

The two frozen states are recorded separately, since a fix for one does not fix the other: the DB
row is never transitioned by the cancel path, and the UI freezes independently because `cancel()`
sets a terminal phase locally (`useOrchestrator.ts:107-110`) and the poll effect early-returns on
terminal phases (`:49-51`), leaving a spinner under "Cancelled." indefinitely.

**One thing deliberately left unestablished and labelled as such in the row:** whether OS
descendants survive the SIGKILL. `kill()` targets the direct child and no process group is used —
that was read. Whether the exec-server sandbox worker outlives it was **not** tested, and the row
says so rather than asserting a plausible inference.

### 7b. W4d — which row owns the launch door

**BL-085**, verified by reading both rows at HEAD. BL-094 is *"A direct, non-LLM launch door"* —
peeled off BL-085 on the direct-door half — and its subject is the path that **bypasses** the
planner; closing it would leave the defect intact for every launch still going through the planner.
BL-085 owns *"per-launch provider selection"* and its Open questions 1 and 2 are exactly this. The
annotation records that `agents/orchestrator.exs`'s **Known params** block (`:65-70`) lists
`PAYSLIP_MONTH` and `PAYSLIP_EMPLOYEE_ID` and has never mentioned any cloudcost key, so provider
selection depends entirely on an operator having read the runbook before each launch — with
`cloudcost_orchestrator.exs:58` defaulting to `digitalocean` when the key is absent.

Noted in passing, not edited: BL-085's own Done-when says *"the operator can pick aws vs do per
launch"* — itself a two-provider enumeration written before providers three and four. Rewriting a
Done-when is a disposition and this ticket files rather than disposes.

### 7c. W4e — new row, and the ground for it

Filed as **BL-156** rather than as an annotation. No row owns approval-surface *content*: BL-094
owns the door, BL-085 owns credentials and provider selection, and BL-151 is for defects that break
nothing today — this one can mislead an operator into approving a run. The defect is generic to
every planner-launched agent; cloudcost is the observation site because decision H is an unusually
crisp constraint to contradict.

### 7d. W4f — an ambiguity reported rather than guessed

The ticket asked for *"the same shape as the kind-axis entry already there"*. **No entry in BL-151
— nor anywhere in `docs/backlog-2026-06.md` — uses the word "axis"** (checked). The nearest match
in shape is the third appended entry: the `tools.json` `env` row versus `sprint.sh`'s
`KNOB_CONSTANTS`, two surfaces with nothing checking that they agree. The new entry follows that
one's shape and says so in its own text. If a different entry was meant, this is the thing to
correct.

The finding itself: `EnvDep` (`rig/src-tauri/src/commands/tools.rs:6-13`) carries
`key`/`label`/`group`/`masked`/`placeholder` and no optionality field, while its sibling
`ManifestArg` (`:15-24`) *does* carry `required: bool` — the axis exists on the args half of the
same manifest and not on the env half. `ToolDetail.tsx:85` prints *"Required config"* over
`script.env` unconditionally, so `CLOUDCOST_GITHUB_ORG` renders as required under a label
(`cloudcost/tools.json:295`) that says it is optional.

---

## 8. Done-checks

Both pytest scopes, because BL-152 means neither covers the other.

```
$ cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest cloudcost/tests/ -q
465 passed in 152.72s (0:02:32)

$ cd ~/sandbox/elixirws/aetheris-agents && python3 -m pytest tests/ -q
129 passed, 7 xfailed in 1.41s

$ cd ~/sandbox/elixirws/aetheris && set -a && . ~/.secrets/do-cloudcost.env && set +a && ./scripts/sprint.sh cloudcost
→ exit 0; blocking failures 0; arms tracked KNOWN_RED 0; reds NOT YET DECLARED 0
```

`tests/` is the scope that matters for the regen — `test_assemble_matrix.py` and
`test_tools_manifests.py` both live there, and `test_tools_manifests.py:153`'s
`assert len(_flat_cli_scripts("cloudcost")) == 8` is unaffected because it counts runnable CLIs on
disk, not matrix rows.

**The rule-legibility arm, quoted against t3's.** That arm is non-blocking by construction
(`sprint.sh:3327-3331` — its failure path increments a counter and does not halt), so a green
summary is not sufficient evidence and the line itself is quoted:

```
[OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance,
        load_balancer, volume] all drawn from the canonical set
```

t3 recorded *"18 resources evaluated"* (`cloudcost/docs/m6-t3-implementation-notes.md:418`).
**Unchanged — same count, same verdict.**

**On completeness of the sprint capture.** The run's own console capture is
`aetheris/sprint/20260814_130922/console.log`, **62 lines**. The live terminal view was taken with
`tail -60`, so 2 content lines and a blank were initially outside it; both were then read from the
saved capture (the provenance-stamp and console-capture INFO lines, plus the retention sweep
line). Nothing is elided from the packet. The run's provenance stamp records
`agents_commit: 97c61a0`, `agents_dirty: yes` — expected, the working tree carries this ticket.

**Manifest staleness — named, not chased.** Two edited files are manifest-tracked:
`docs/capability-matrix.md` (pinned `4d98ec2`) and `docs/backlog-2026-06.md` (pinned `124707f`).
Both re-stale on commit; those `project_knowledge` WARNs are the declared strict-mode exemption and
clear at the export boundary. `cloudcost/runbook.md` is explicitly **out** of the manifest
(`docs/project-knowledge-manifest.md:147-149`), as is
`docs/capability-matrix-overrides.json` (`:164`). Check 8 reads committed history, so a
`drift_check --strict` run *before* this commit would be vacuous on exactly the staleness the
commit introduces; it belongs after.

---

## 9. The fourth gate is the operator's — outstanding, not done

**Three green mechanical checks are not evidence that this ticket worked.** What the ticket is
*for* is a click-through nobody in this session can perform:

1. Rig's **Agents** view must list `fetch_github.py` under Cloudcost.
2. A run launched from Rig with `CLOUDCOST_PROVIDER=github` in **Additional env vars** must plan
   and execute a GitHub run.

Neither is covered by anything that ran. The matrix is parsed by Rust
(`rig/src-tauri/src/commands/capability_matrix.rs:44-125`) that **no test in this repo exercises**,
and the second leg involves a live model whose behaviour no assertion here constrains. A green
board says the document now contains the right rows; it says nothing about whether Rig renders them
or the planner acts on them. **State this as an outstanding gate.**

---

## 10. Open items forwarded

- **BL-155** carries the stated unknown this ticket's scope choice created: eight of nine matrix
  sections were not regenerated and have **not** been checked against their source trees. The
  byte-identity in §3 establishes that the on-disk sections match the committed document; it
  establishes nothing about whether either matches the code. Last full regen: `4d98ec2`,
  2026-08-05.
- **`docs/capability-matrix-runbook.md:79-80`** overstated stability. **Closed at review by an
  amendment to this commit — see §11.**
- **`compose_report_data.py`'s docstring** still says *"Merge N providers'"*. Excluded by this
  ticket; it is the source of the matrix cell, so the cell cannot be fixed without it.
- **BL-085's Done-when** carries a stale two-provider enumeration, noted in its annotation and left
  for whoever disposes the row.

---

## 11. Amendment at review — AQ1, and a Touches widening

**The widening is a reviewer decision, not this session's.** The ticket's Touches did not include
`docs/capability-matrix-runbook.md`, and §4c originally recorded the defect and left the file
alone on that ground. The reviewer widened Touches at the review of `fcde58c` and gave the
reason: that sentence is the one a reader consults **before** deciding whether a matrix diff needs
scrutiny, and it told them it did not. A backlog row does not reach someone who reads the
guarantee first and the backlog never — so the correction has to live where the false claim lives.

**The unit at HEAD** (`docs/capability-matrix-runbook.md:79-80`, quoted before replacement):

> Two runs over unchanged sections produce byte-identical output, so a matrix diff
> only ever shows a real change.

**Replaced with:**

> Two runs of the **assembler** over unchanged sections produce byte-identical output. The
> section step above it does not share that property — it is an LLM, and regenerating a section
> rewords cells whose source has not changed — so a matrix diff carries rewordings as well as
> real changes, and needs reading rather than skimming.

The claim was true of the assembler and false of the ritual it appeared to describe. This ticket
is what disproved it: three regenerations of the cloudcost section over an unchanged tree
produced three different agent labels and reworded every script purpose on each run (§4c). Nothing
else in that file was touched, no fix is proposed, and BL-155 is not restated here — the row
carries the instability; this sentence carries only what the ritual does and does not guarantee.

**Re-run scope for the amendment.** One markdown file changes and no executable is touched, so
both sprint legs and `drift_check.py` are exempt on t2's ground — stated rather than assumed, with
`git diff --stat` as the truth-maker (§12). Both pytest scopes still run, since BL-152 means
neither covers the other.

---

## 12. AQ2 — re-run scope, with its truth-maker

**The exemption is stated, not assumed.** `git diff --stat` against `fcde58c`:

```
 cloudcost/docs/m6-t4-implementation-notes.md | 43 +++++++++++++++++++++++++---
 docs/backlog-2026-06.md                      | 14 ++++++---
 docs/capability-matrix-runbook.md            |  6 ++--
 3 files changed, 53 insertions(+), 10 deletions(-)
```

Every changed path is `.md` — confirmed by filtering the name list for
`\.(py|exs|ex|rs|ts|tsx|sh|json)$`, which returns nothing. **No executable, no agent file, no
manifest, no sprint script.** So both sprint legs and `drift_check.py` are exempt on t2's
ground: neither can observe a change to prose in these three files. (`drift_check` reads Rust,
Elixir, TS and the manifest table; none of the three files is a manifest-tracked *source* it
compares against, and the two manifest-tracked files among them re-stale identically to the
pre-amendment commit — the WARN set is unchanged.)

Both pytest scopes ran, since BL-152 means neither covers the other:

```
$ python3 -m pytest cloudcost/tests/ -q
465 passed in 153.96s (0:02:33)

$ python3 -m pytest tests/ -q
129 passed, 7 xfailed in 1.30s
```

**One correction chased beyond AQ1's file, reported rather than folded in silently.** AQ1 said
not to restate BL-155 in the runbook and not to touch anything else *in that file*. It did not
reach BL-155's own text, which **quoted the false guarantee as still standing** — leaving it
would have made the row cite a sentence that no longer says what the row says it says. Per the
standing rule that a correction chases the corrected claim into every doc that adopted it in the
same round, BL-155's paragraph carries a dated `[Corrected …]` note recording the widening, and
states explicitly that **the row is unaffected otherwise**: the guarantee was corroboration, the
instability is the defect, and it is still open. No other part of the row changed.
