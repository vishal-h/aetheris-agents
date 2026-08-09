# m5 — scoping landing record

Records the landing of `cloudcost/m5-n1-compose.md` and its two backlog annotations across
two rounds: **r0** at agents `eebd47c` (the round document, 300 lines, plus the BL-131 and
BL-132 annotations in `docs/backlog-2026-06.md`) and **r1** at **this commit** (the amendment
round — §6 heading nesting, the two section names, and this file).

`Authored 2026-08-09 at r1, on the reviewer's six findings. Every figure below was derived in
this session at r1's tree; none is transcribed from r0's packet.`

> **`[Filename divergence, raised rather than glossed.]`** `ls cloudcost/docs/` returns 24
> files at r0's tree; 23 match `*-implementation-notes.md` and one — `m3-linode-scout.md` —
> does not. This file takes neither shape exactly. It is **not** a ticket's implementation
> notes: no ticket ran, and the `*-implementation-notes.md` suffix would describe it wrongly.
> The name was specified by the reviewer at r1 F4 and is landed as specified; the divergence
> from the dominant pattern is recorded here rather than resolved, and `m3-linode-scout.md` is
> the standing precedent that a non-notes name is available in this directory.

---

## Why this file exists

R20 makes an edit's implementation-notes file its committed record. **R20 does not reach this
document** — see §F3 below — so the landing had no committed artifact at all: the round
document's deviation blockquote was authored *before* the session it describes, and r0's six
verifications existed only in a packet, which is committed in neither repo. That is §Not
established item 2's own shape one level up: a derivation whose only record is a channel that
does not travel. This file is that record.

---

## §Verifications

Six verifications, r0's set. Three are superseded by r1 re-runs; r0's results are retained and
marked, not deleted.

### 1. §6 field names — **r0 result superseded 2026-08-09 (r1 F2e)**

> **r0, 2026-08-09 — PASS, and the PASS was partial.** r0 checked that both tickets carry §6's
> seven field *names* in §6's order. They did, and they still do. What r0 did not check was the
> ticket **heading's level**, so a divergence from §6's template passed as PASS. That is r1 F2:
> the defect was in the authored document, not in the landing, and the check that should have
> caught it was scoped to names only.

r1 command, run after the F2 demotion (the `awk` ranges retargeted from `^## t` to `^### t`):

```bash
echo "### §6 canonical list (harness) ###"; grep -nE '^\*\*(Scope|Contract refs|Touches|Do not generate|Runbook update rule|Done-check|Claude-code prompt)\.\*\*' ../aetheris/docs/methodology/milestone-methodology.md | sed -n '1,20p'
echo "### t1 fields (landed file) ###"; awk '/^### t1 —/,/^### t2 —/' cloudcost/m5-n1-compose.md | grep -nE '^\*\*[A-Z][^*]*\.\*\*|^\*\*Step-1 gate\*\*'
echo "### t2 fields (landed file) ###"; awk '/^### t2 —/,/^## Ratified decisions/' cloudcost/m5-n1-compose.md | grep -nE '^\*\*[A-Z][^*]*\.\*\*|^\*\*Step-1 gate\*\*'
```

Output, verbatim:

```
### §6 canonical list (harness) ###
166:**Scope.** <2–4 sentences. What exists after this ticket that didn't before.>
168:**Contract refs.** <doc §refs that are normative for this ticket — the prompt
171:**Touches.** <files/dirs expected to change. Anything outside this list needs
177:**Do not generate.** <ticket-specific exclusions, on top of the repo-level
180:**Runbook update rule.** If a ticket introduces a new environment variable,
196:**Done-check.**
202:**Claude-code prompt.**
### t1 fields (landed file) ###
3:**Step-1 gate** *(m4 decision 3, carried by R8 — run before any other work in
19:**Scope.** After this ticket, the evidence the BL-131 ruling needs exists as a
25:**Contract refs.**
33:**Touches.**
41:**Do not generate.** No change to any file under `cloudcost/scripts/`,
48:**Runbook update rule.** t1 introduces no environment variable, no startup step,
55:**Done-check.**
74:**Claude-code prompt.**
### t2 fields (landed file) ###
3:**Step-1 gate** *(m4 decision 3, carried by R8).* **R13-marked.** The gate's
8:**Scope.** After this ticket, the BL-131 ruling is implemented in
14:**Contract refs.** t1's implementation notes · this document's §Ratified
19:**Touches.** **R13-marked.** The path set is one of two disjoint sets and the
26:**Do not generate.** Authorable now, and complete as written: no reachability
31:**Runbook update rule.** **Partly R13-marked, and a runbook change is in scope
37:**Done-check.** **R13-marked, deliberately.** Anchor: the offline pytest spine
45:**Claude-code prompt.** **R13-marked.** `Resolver: authored by the reviewer after
```

**PASS.** All seven §6 fields present on both tickets, in §6's order, plus the step-1 gate,
which the document itself declares is not a §6 field. **No field text moved at r1** — the
`awk` ranges are the only thing that changed, and they changed because the headings did.

The heading-level check r0 omitted, added at r1:

```bash
grep -n '^#\{2,3\} ' cloudcost/m5-n1-compose.md
```

```
6:## Why this exists
13:## Scope
27:## Sequence
41:## Ticket set
57:### t1 — establish the N>1 compose surface (read-only)
191:### t2 — apply the ruling
240:## Ratified decisions
248:## Not established
284:## Carried in
```

**PASS.** Both tickets now nest one level under `## Ticket set`, matching §6's template at
`../aetheris/docs/methodology/milestone-methodology.md:164` — `### t<N> — <title>`.

### 2. Path resolution — **r0 result superseded 2026-08-09 (r1 F5)**

> **r0, 2026-08-09 — PASS over a population r0 did not demonstrate.** r0 checked 21 paths and
> called them *"every path named in the landed document"*. The list was hand-assembled. A count
> over an undemonstrated population is the carrier this round exists to close, so r1 re-derived
> the population mechanically. r0's 21 were all real and all correctly resolved; what was
> missing was the derivation, not the arithmetic.

r1 derivation (F5a) — every backticked token in the round document, filtered to path-shaped:

```bash
grep -o '`[^`]*`' cloudcost/m5-n1-compose.md | tr -d '`' \
  | grep -E '(/|\.md$|\.py$|\.exs$|\.json$|\.sh$)' | sort -u
```

**23 tokens**, verbatim:

```
../aetheris/
../aetheris/docs/methodology/milestone-methodology.md
cloudcost/
cloudcost/agents/
cloudcost/agents/cloudcost_orchestrator.exs
cloudcost/docs/m5-t1-implementation-notes.md
cloudcost/m2-milestone.md
cloudcost/m4-consolidation.md
cloudcost/m5-n1-compose.md
cloudcost/milestone.md
cloudcost/runbook.md
cloudcost/scripts/
cloudcost/scripts/compose_report_data.py
cloudcost/templates/
cloudcost/tests/
cloudcost/tools.json
compose_report_data.py
docs/backlog-2026-06.md
docs/milestones/hc-consolidation.md
docs/reviews/hc-b-review.md
eduloka/
rig/
tools.json
```

r1 existence check (F5b) — bare = agents, `../aetheris/…` = harness:

```bash
while read -r p; do if [ -e "$p" ]; then printf 'RESOLVES  %s\n' "$p"; else printf 'ABSENT    %s\n' "$p"; fi; done < derived.txt
```

```
RESOLVES  ../aetheris/
RESOLVES  ../aetheris/docs/methodology/milestone-methodology.md
RESOLVES  cloudcost/
RESOLVES  cloudcost/agents/
RESOLVES  cloudcost/agents/cloudcost_orchestrator.exs
ABSENT    cloudcost/docs/m5-t1-implementation-notes.md
RESOLVES  cloudcost/m2-milestone.md
RESOLVES  cloudcost/m4-consolidation.md
RESOLVES  cloudcost/m5-n1-compose.md
RESOLVES  cloudcost/milestone.md
RESOLVES  cloudcost/runbook.md
RESOLVES  cloudcost/scripts/
RESOLVES  cloudcost/scripts/compose_report_data.py
RESOLVES  cloudcost/templates/
RESOLVES  cloudcost/tests/
RESOLVES  cloudcost/tools.json
ABSENT    compose_report_data.py
RESOLVES  docs/backlog-2026-06.md
RESOLVES  docs/milestones/hc-consolidation.md
RESOLVES  docs/reviews/hc-b-review.md
RESOLVES  eduloka/
RESOLVES  rig/
ABSENT    tools.json
```

**20 RESOLVES, 3 ABSENT.** Each absence accounted for (F5d):

| token | reading |
|---|---|
| `cloudcost/docs/m5-t1-implementation-notes.md` | **Absent by design.** Declared `*(new)*` by t1's **Touches** field at `cloudcost/m5-n1-compose.md:91` — the line reads ``- `cloudcost/docs/m5-t1-implementation-notes.md` *(new)*``. t1 has not opened, so the file cannot exist. |
| `compose_report_data.py` | **Extraction artifact, not a path claim.** A bare basename in E2's prose (*"Every in-repo invocation of `compose_report_data.py`"*). Resolves as `cloudcost/scripts/compose_report_data.py`, which RESOLVES above. |
| `tools.json` | **Extraction artifact, not a path claim.** A bare basename in E2's enumeration of invocation sites. Resolves as `cloudcost/tools.json`, which RESOLVES above. |

Reconciliation against r0's 21 (F5c), produced by `comm -3` over the two sorted lists rather
than by hand — first as written, then with trailing slashes normalised away:

```
=== comm -3 (left = derivation-only | right = hand-list-only), slashes AS WRITTEN ===
	../aetheris
../aetheris/
cloudcost/
	cloudcost/agents
cloudcost/agents/
	cloudcost/docs
	cloudcost/scripts
cloudcost/scripts/
	cloudcost/templates
cloudcost/templates/
	cloudcost/tests
cloudcost/tests/
compose_report_data.py
	eduloka
eduloka/
	rig
rig/
tools.json
=== same, with trailing slashes normalised away ===
cloudcost
	cloudcost/docs
compose_report_data.py
tools.json
```

**Three the derivation found and the hand list missed**, and why each:

- **`cloudcost/`** — the document writes it as a bare directory in t1's **Do not generate**
  field; r0's hand list carried the four subdirectories but not the parent.
- **`compose_report_data.py`** and **`tools.json`** — bare basenames in E2's prose. r0
  normalised both to their qualified forms while assembling, which is the right *reading* but
  removes them from the population before it is counted. Both are ABSENT at repo root, and
  that is the correct answer for a token the document never qualifies.

**One the hand list had and the derivation did not produce:**

- **`cloudcost/docs`** — the round document never writes this standalone, only as a prefix of
  `cloudcost/docs/m5-t1-implementation-notes.md`. r0 added it from knowledge of the tree, not
  from the document. It is a real directory; it is not a member of the document's population.

All remaining differences are trailing-slash normalisation on **seven** directory entries
(`../aetheris`, `cloudcost/agents`, `cloudcost/scripts`, `cloudcost/templates`,
`cloudcost/tests`, `eduloka`, `rig`) — the document writes them with a trailing slash, r0's
list without.

### 3. Cross-document anchors — re-run at r1, unchanged

```bash
echo "--- hc-consolidation R-anchors ---"; grep -nE '^### R(8|12|13|19|20|21) —' docs/milestones/hc-consolidation.md
echo "--- milestone.md Contracts / C4 / C11 ---"; grep -nE '^## Contracts|^### C4 —|^### C11 —' cloudcost/milestone.md
echo "--- m2-milestone decision H ---"; grep -nE '^### H —' cloudcost/m2-milestone.md
echo "--- hc-b-review Round 0 ---"; grep -nE '^## Round 0' docs/reviews/hc-b-review.md; grep -n 'manufactured a' docs/reviews/hc-b-review.md
echo "--- backlog rows ---"; grep -nE '^### BL-(070|074|075|119|121|131|132) —' docs/backlog-2026-06.md
```

```
--- hc-consolidation R-anchors ---
271:### R8 — decision 3 (the step-1 gate) carries, and carrying it forecloses nothing.
335:### R12 — a ticket's §6 anatomy is written into this document **before that ticket opens**.
349:### R13 — a slot that cannot be authored yet is marked with its resolver: never blank, never guessed.
468:### R19 — a session that changes a ticket's state updates that ticket's row in the same commit.
528:### R20 — a reviewer-authored section-scoped edit is not a ticket round and gets no review file.
546:### R21 — §Not established holds three kinds of entry, and only one of them owes a resolver.
--- milestone.md Contracts / C4 / C11 ---
293:## Contracts (C1–C15 — what shared machinery guarantees, and what an adapter must guarantee)
402:### C4 — Money and currency  *(N5, P3, P5, R2)*
652:### C11 — Optionality and presentation  *(R1, P2, P7)*
--- m2-milestone decision H ---
305:### H — Per-provider reporting; no cross-provider roll-up (ratified 2026-07-30, rev 3)
--- hc-b-review Round 0 ---
18:## Round 0 — packet submitted
54:   R8 carries it on. Listing it as a methodology obligation would have manufactured an
--- backlog rows ---
2414:### BL-070 — Retire the dormant cross-provider merge code in `compose_report_data.py` (#TBD)
2629:### BL-074 — Seam sweep: enumerate every provider-vocabulary / provider-assumption seam in shared machinery (#TBD)
2777:### BL-075 — `mix test` failed once then passed three times, identity uncaptured (#TBD)
7064:### BL-119 — a cost snapshot with a declared total and no line items is silently dropped from discovery (#TBD)
7138:### BL-121 — the untagged-spenders cap truncates across all providers and reports nothing (#TBD)
7484:### BL-131 — decide whether the N>1 compose path is a supported surface (#TBD)
7547:### BL-132 — establish, per contract, whether the behaviour it states is reachable from the live pipeline (#TBD)
```

**PASS.** Every anchor the round document cites resolves. `docs/reviews/hc-b-review.md:54`
carries the *manufactured authority* finding the document's §Ticket set preamble cites.

### 4. Section-name convention vs `m4-consolidation.md` — **r0 result superseded 2026-08-09 (r1 F7d)**

> **r0, 2026-08-09 — reported, not changed.** r0 correctly identified that `## Why this exists`
> and `## Scope` were present as content but absent as headings. r1 F7 heads them.

r1 re-run:

```bash
comm -3 <(grep -o '^## .*' cloudcost/m5-n1-compose.md | sort -u) \
        <(grep -o '^## .*' cloudcost/m4-consolidation.md | sort -u)
```

```
## Carried in
	## Close criteria
	## Open for the close
	## Promotion candidates
	## The close
	## What this cycle established
```

**PASS.** Left column (m5-only) is `## Carried in` alone; the two ticket headings have left it,
demoted by F2. Right column (m4-only) is five sections, **all close-side** — a document opened
before its first ticket cannot carry any of them. `## Scope` and `## Why this exists` have left
the divergence set entirely. The residue is the correct residue for a round document at open.

### 5. §Not established entry kinds — re-run at r1, unchanged

```bash
awk '/^## Not established/,/^## Carried in/' cloudcost/m5-n1-compose.md | grep -nE '^\s*[0-9]\. \*\*`\[OPEN\]|No owner|\*\*Resolver:\*\*|\*\*Settled by:\*\*'
```

```
10:1. **`[OPEN]` (b)** **Provider four carries two non-identical gate statements at
15:   **Settled by:** a ruling that reconciles them, authored wherever provider four
16:   is scoped. **No owner** — provider four is not open, and this round declined
19:2. **`[OPEN]` (b)** **BL-131's `Source:` line cites gate items that exist as no
23:   **Settled by:** nothing in-repo — the derivation is re-run at HEAD instead,
25:   cite those gate items as though they were a document. **No owner.**
27:3. **`[OPEN]` (a)** **Whether decision H's re-derivability clause is satisfied
33:   **Resolver:** t1's **E7**, in this document.
```

**PASS, both arms.** The two `(b)` items carry `**Settled by:**` and state `**No owner**`,
inventing none — R21(b)'s requirement. The one `(a)` item's `**Resolver:** t1's **E7**`
resolves to a heading that exists at `cloudcost/m5-n1-compose.md:176` (see verification 6).

### 6. The eight E-items — re-run at r1

The check r0's done-check item 3 specifies — `grep -c '^### E[1-8] '` over
`cloudcost/docs/m5-t1-implementation-notes.md` — **remains not applicable**, and the reason is
the same at r1 as at r0:

```bash
ls -l cloudcost/docs/m5-t1-implementation-notes.md
```

```
ls: cannot access 'cloudcost/docs/m5-t1-implementation-notes.md': No such file or directory
```

t1 has not opened, so that grep would report a number about an absent file rather than a
check. What **is** checkable now is that the round document's own t1 prompt declares all eight:

```bash
grep -c '^> \*\*E[1-8] —' cloudcost/m5-n1-compose.md
grep -n  '^> \*\*E[1-8] —' cloudcost/m5-n1-compose.md
```

```
8
144:> **E1 — Route census.** Every code path by which `compose_report_data.py` can
148:> **E2 — Invocation census.** Every in-repo invocation of
153:> **E3 — Test coverage.** Which tests, if any, exercise more than one bundle.
158:> **E4 — Blast radius of REMOVE.** Everything that deletes if the multi-bundle
164:> **E5 — Blast radius of SUPPORT.** Everything that must be *added* for the
170:> **E6 — The three-state contradiction.** BL-131 tabulates three assertions
176:> **E7 — Decision H's re-derivability clause.** Quote decision H's own sentence
182:> **E8 — Reachability of C4's and C11's stated behaviour.** For each of the two
```

**PASS, with its substitution stated.** Eight declared, E1–E8 contiguous, no gaps and no
duplicates. This substitutes for the done-check's own grep and does not stand in for it: when
t1 runs, the done-check's grep over the notes file is the check that must return 8.

---

## §Divergences from the sibling cycle documents

r0's four classes, carried verbatim, with class 2 updated for r1 F7 and class 4 for r1 F2.

**1. Shared names, identical spelling** (4): `Sequence`, `Ticket set`, `Ratified decisions`,
`Not established`.

**2. Names m4 carries that this document omits** (7): `Why this exists`, `Scope`,
`What this cycle established`, `Open for the close`, `Promotion candidates`,
`Close criteria`, `The close`. Five of the seven are close-side sections that a document
opened before its first ticket could not yet carry. The two that are *not* close-side —
**`Why this exists` and `Scope`** — are the substantive omission: their content is present
in the landed document as the unheaded opening paragraphs (*"What this round decides"*,
*"Shape: two tickets with a gate stop between them"*) rather than under m4's names.

> **`[Updated at r1 (F7), 2026-08-09.]`** Closed. `## Why this exists` is inserted at
> `cloudcost/m5-n1-compose.md:6`, above the paragraph beginning *"**What this round decides.**"*;
> `## Scope` at `:13`, above the paragraph beginning *"**Shape: two tickets with a gate stop
> between them.**"* No text moved and no sentence was rewritten — the two insertions are
> headings only, and the deviation blockquote stays where it was, after the §Scope paragraph
> (now `:19–23`). **The class is now five, not seven, and all five are close-side.**

**3. Names new to this document** (1): **`Carried in`**. m4-consolidation carries no section of
that name; the nearest equivalent is hc-consolidation's `§Milestone summary → §Open for the
next cycle`, which is where the landed section says its content came from.

**4. A structural divergence the name-set comparison does not show, and the order.**
m4-consolidation nests its tickets as `###` under `## Ticket set` (`:133`, with `### What t1b
inherits` etc. beneath it); hc-consolidation does the same (`## Ticket set :664`, `### hc-a
:689`). This document promotes **`## t1 —`** and **`## t2 —`** to top-level, leaving
`## Ticket set` as a two-row state table. Order also differs: m4 runs
`Ratified decisions → Ticket set → Sequence`; this document runs
`Sequence → Ticket set → t1 → t2 → Ratified decisions`.

> **`[Updated at r1 (F2), 2026-08-09.]`** The heading half is closed; the order half stands and
> is not a defect. `t1` and `t2` are demoted to `###` and the two `---` separators between
> §Ticket set and t1, and between t1 and t2, are removed, so both tickets are inside
> §Ticket set. The `---` after t2 is kept.
>
> **r0's evidence for this class understated it, and the correction runs toward the finding.**
> §6 specifies the level directly — `### t<N> — <title>` at
> `../aetheris/docs/methodology/milestone-methodology.md:164` — so the sibling documents were
> never the authority; the template is. And the sibling evidence is stronger than r0 stated:
> **three** cloudcost cycle documents nest actual ticket sections one level under
> `## Ticket set` — `cloudcost/milestone.md:844`/`:846`, `cloudcost/m2-milestone.md:453`/`:460`,
> `cloudcost/m3-milestone.md:347`/`:349`. `m4-consolidation.md:133` is **not** among them: it
> carries a two-column state table, and the three `###` headings between it and `## Sequence`
> (`:247`) — `### What t1b inherits` (`:188`), `### What t2 inherits` (`:216`), `### What t3, t4
> and t5 inherit` (`:230`) — carry none of §6's seven field markers.
>
> **`[Derived at r2 (G2), 2026-08-09 — this replaces a reading with a test.]`** The claim that
> those headings are inheritance notes rather than ticket sections was stated at r1 as an
> interpretation. It is decidable mechanically: a ticket section carries §6's fields, an
> inheritance note does not. The seven markers return **zero hits over the whole file**, not
> merely zero inside §Ticket set:
>
> ```bash
> for f in cloudcost/milestone.md cloudcost/m3-milestone.md cloudcost/m2-milestone.md \
>          cloudcost/m5-n1-compose.md cloudcost/m4-consolidation.md; do
>   printf '%s:%s\n' "$f" "$(command grep -c \
>     -e '\*\*Scope\.\*\*' -e '\*\*Contract refs\.\*\*' -e '\*\*Touches\.\*\*' \
>     -e '\*\*Do not generate\.\*\*' -e '\*\*Runbook update rule\.\*\*' \
>     -e '\*\*Done-check\.\*\*' -e '\*\*Claude-code prompt\.\*\*' "$f")"
> done
> ```
>
> One file per call, and `command grep` rather than the bare name: a multi-file `grep -c` in this
> session returns its lines in a **non-deterministic order** — the shell's `grep` is a wrapper
> function delegating to `ugrep`, which searches the arguments in parallel. The counts were
> identical under both, but a quoted output block whose row order the command does not reproduce
> is a block that cannot be re-derived. The loop fixes the order in the argument list.
>
> ```
> cloudcost/milestone.md:25
> cloudcost/m3-milestone.md:18
> cloudcost/m2-milestone.md:15
> cloudcost/m5-n1-compose.md:14
> cloudcost/m4-consolidation.md:0
> ```
>
> The four non-zero counts are the positive control: the patterns match where ticket sections
> exist, so `m4-consolidation.md`'s zero is a fact about that file and not about the grep. A
> heading with none of §6's fields beneath it is not a ticket section, so m4 does not
> demonstrate the nesting convention in either direction — and r0's correction stands on a
> derivation rather than on a reading. r0 cited the one sibling that does not demonstrate the
> convention and omitted the three that do.

---

## §F1 — the anchor discrepancy and its resolution

Two sessions at the same agents HEAD reported what each took to be the provider-four seam-sweep
gate statement in `cloudcost/m4-consolidation.md` at two different line numbers — `:52` and
`:362`. A line number
cannot move at a fixed HEAD.

**(a) The file is unchanged across both readings.**

```bash
git log -1 --format='%H %ad %s' -- cloudcost/m4-consolidation.md
```

```
8490362691aef3f4017e84afcff918917ed6df75 Sat Aug 8 10:12:58 2026 +0530 fix(m4 close-d r1): head-1's count was right about a different population
```

Last touched 2026-08-08, before either reading. Both sessions read identical content.

**(b) Enumeration.**

```bash
git grep -n -e 'seam sweep' -e 'Provider four' -e 'provider four' -- cloudcost/m4-consolidation.md
```

```
cloudcost/m4-consolidation.md:52:- **Provider four.** Gated on this cycle's seam sweep and on the harness round.
cloudcost/m4-consolidation.md:250:**BL-131** → **provider four**.
cloudcost/m4-consolidation.md:286:> m4; **BL-131** decides it after the harness round, before provider four, where it bites.
cloudcost/m4-consolidation.md:362:**The harness round runs before provider four**, and for the same reason the seam sweep does. BL-074
cloudcost/m4-consolidation.md:373:touches no code. What the harness round buys is that *implementing* provider four lands on
cloudcost/m4-consolidation.md:1060:**Three things made provider four harder, not easier, and this is not smoothed:**
cloudcost/m4-consolidation.md:1078:| **BL-131** | the N>1 compose surface — **gates provider four**, decided after the harness round |
cloudcost/m4-consolidation.md:1229:BL-077 once the chaos gate's real state is known) → **BL-131** → **provider four**.
cloudcost/m4-consolidation.md:1232:*implementing* provider four lands on apparatus that works.
```

**(c) Context, verbatim.**

`sed -n '48,56p' cloudcost/m4-consolidation.md`:

```
**Not in scope, and deliberately so.**

- **The harness `--json` contract** — BL-105 and BL-106. Found during this cycle and the most
  consequential thing in it, filed rather than pulled in. Scheduled as its own round; see §Sequence.
- **Provider four.** Gated on this cycle's seam sweep and on the harness round.
- **Any §Normalized extension.** BL-098 remains filed; extending the contract belongs with the
  provider that needs it, not before.

---
```

`sed -n '358,366p' cloudcost/m4-consolidation.md`:

```
> now reads `Closed` with its commit range, and the column is back to the three durable forms plus
> two retired interim ones. Neither `Live` nor `In review (r2)` should be read as vocabulary
> available to a future cycle without the same declaration.

**The harness round runs before provider four**, and for the same reason the seam sweep does. BL-074
tells you whether the next adapter is mechanical on the agents side; BL-105 and BL-106 tell you
whether the apparatus a new provider lands on works. Every new provider adds a leg to the sprint
case, and a leg added to non-deterministic reads inherits the flakiness — m3 already paid that cost
three times.
```

**(d) Resolution: the two reports named passages of different kinds, and `:362` is a third
kind.** Neither report was wrong; both were partial. The two **non-identical statements**
§Not established item 1 names are `:52` on the gate side and the sequence lines `:249–250` /
`:1228–1229` on the other. `:362` is neither — a sequencing rationale that cites the seam sweep
by analogy — and it is what made a partial reading of either side look complete. Enumerated by
kind:

| `path:line` | kind | statement | section it sits in |
|---|---|---|---|
| `cloudcost/m4-consolidation.md:52` | **gate** — gates provider four on the seam sweep *and* the harness round | `- **Provider four.** Gated on this cycle's seam sweep and on the harness round.` | §Scope → *"Not in scope, and deliberately so."* — a scope exclusion |
| `cloudcost/m4-consolidation.md:249–250`, `cloudcost/m4-consolidation.md:1228–1229` | **sequence** — `… → BL-131 → provider four`, seam sweep unnamed | enumerated verbatim in (e) below | §Sequence; §The close → *7. The sequence from here, unchanged* |
| `cloudcost/m4-consolidation.md:362` | **sequencing rationale — not a gate** | `**The harness round runs before provider four**, and for the same reason the seam sweep does. BL-074` | §Sequence |

`:52` and `:362` both name the seam sweep, which is why one could be read for the other; only
`:52` gates on it. `:362` argues *why* the harness round precedes provider four and cites the
seam sweep by analogy rather than as a second gate — so it belongs in neither of the two sides
the discrepancy is between.

> **`[Corrected in place at r2 (G3), 2026-08-09 — not a dated supersession block, because the
> file has never been pushed and no reader ever saw the earlier text.]`** This table previously
> read *"BOTH carry a gate statement, and they are TWO distinct statements"* and listed `:52`
> and `:362` as its two rows, while the prose beneath said `:362` cites the seam sweep *"by
> analogy rather than as a second gate"*. A passage tabled as a gate and described as not-a-gate
> leaves the section with no readable finding. The table now sorts by kind and `:362` sits in
> its own row as the third kind.

Three further statements name provider four **without** the seam sweep, and are therefore not
candidates for either report: `:286` (BL-131 decides the N>1 question *"before provider four,
where it bites"*), `:1078` (the hand-forward table row: BL-131 *"**gates provider four**,
decided after the harness round"*), and `:1232`.

**(e) Sequence lines reading `… → BL-131 → provider four`** — every one, enumerated. Both are
two-line wraps, cited at the line the arrow chain terminates:

| `path:line` | text |
|---|---|
| `cloudcost/m4-consolidation.md:249–250` | `t1b → t2 → t3 → **t4a → t4b → t4c** → **t5a → t5b → t5c** → **harness consolidation round** →` / `**BL-131** → **provider four**.` — §Sequence |
| `cloudcost/m4-consolidation.md:1228–1229` | `**harness consolidation round** (BL-105 + BL-106 as one contract with two mechanisms, folding` / `BL-077 once the chaos gate's real state is known) → **BL-131** → **provider four**.` — §The close → *7. The sequence from here, unchanged* |

Neither sequence line names the seam sweep.

**Carried into the round document: §Not established item 1 is correct as landed and needs no
edit.** It says m4 *"states in one place that provider four is gated on the cycle's seam sweep
and the harness round, and sequences it in another as following BL-131 with no seam sweep
named."* At HEAD the first is `:52` and the second is `:249–250`. The item claims two
non-identical statements and two is what the enumeration finds. What the enumeration adds is
that the *sequence* side has a second member at `:1228–1229`, and that a third passage of a
third kind sits beside both — `:362`, a sequencing rationale — which adds a member to neither
side. Four passages in all, and the item's characterisation of the disagreement survives every
one of them.

---

## §F3 — R20 as it reads

**(a) R20 in full, `docs/milestones/hc-consolidation.md:528–544`**, heading through the line
before R21's heading:

```
### R20 — a reviewer-authored section-scoped edit is not a ticket round and gets no review file.

Its implementation-notes file is its committed record, and the reviewer's findings on it land
there, appended as a dated `## Review` section with the findings verbatim and the dispositions
beneath — the same shape **R2** requires of a review file, in the artifact the edit already has.
R2 is unchanged for `hc-*` ticket rounds.

The reason is that R2's purpose is a committed trail for every session that changes the repo, not
a particular filename. Inventing a review file for a session with no rounds would make the file's
own `## Round N` structure a fiction; putting the findings in the notes keeps the trail and keeps
the structure honest.

`Recorded 2026-08-09, closing hc-d anatomy r1.4 Finding 2, which had been stood in for at that
edit's r1.5 and again at hc-e's anatomy edit §5. Authored by the reviewer at hc-e's anatomy edit
r1, F3.`

---
```

**(b) Does R20's body mention an implementation-notes file? Yes — in its first body line.**
*"Its implementation-notes file is its committed record."*

**(c) Restated — and the finding's premise inverts.** F3 anticipated that R20 says nothing
about implementation notes and that r0's closing observation had therefore characterised the
rule from a reading rather than from its text. The opposite is the case, and the correction
runs against the finding: **r0's observation was faithful to R20's body.** R20 does make an
implementation-notes file the committed record for a reviewer-authored section-scoped edit,
in as many words.

What was partial was the **anchor table's quotation**, which reproduced R20's *heading* only —
*"a reviewer-authored section-scoped edit is not a ticket round and gets no review file"* — and
so carried the no-review-file half without the where-the-record-goes half. Heading and body are
both R20 and they do not contradict each other; each states one half of a two-part rule, and a
reader given either alone would form a different account of what R20 requires.

**This is the (i)–(viii) carrier one level up, and it appeared twice in one round.** F1 is the
same shape over a document — two sessions each reading one of two passages and each reporting
as though it were the only one. F3 is that shape over a *rule*, with the two partial readings
landing in a single packet: the observation quoted the body, the anchor table quoted the
heading, and nothing in the packet reconciled them. A rule characterised from any reading short
of its full text is a rule that can be cited against itself.

**R20 nonetheless does not reach this document, and that is why this file exists.** The round
document's own deviation blockquote records it at `cloudcost/m5-n1-compose.md:19–23`:

```
> `[Deviation, recorded rather than glossed. R20 covers a reviewer-authored
> **section-scoped** edit; this document's creation is not one, because there was
> no document to scope into. Recorded here as a divergence-with-record, on the
> same footing as m4-5's clause-4 entries: the authoring is the reviewer's per
> R12 and decision 11, and only the edit's shape differs.]`
```

R20 attaches the committed record to an artifact a section-scoped edit *already has*. Creating a
document is not a section-scoped edit and has no such artifact, so R20 supplies none — which
left the landing with no committed record at all until this file. The substance of r0's
observation (F4) never needed R20 as authority and does not rest on it.

---

## §The attribution rule, first application

**`[first application, recorded 2026-08-09 (r1, F6).]`**

**What the rule asked.** §Carried in's first rule, inherited from
`docs/milestones/hc-consolidation.md` §Open for the next cycle and in force for this round:
*"An entry's attribution is structural. An insertion between a claim and its `Source:`
re-attributes both. An edit that inserts into a structured document states where the insertion
point falls relative to the surrounding unit's boundaries, and a verification that quotes
context asserts what the context is."*

**What was done.** r0 landed two annotations, each inside a backlog row and each above that
row's `Source:` line — the exact position the rule names:

| annotation | `path:line` | row it sits in |
|---|---|---|
| `**Scoped 2026-08-09 into `cloudcost/m5-n1-compose.md`**` | `docs/backlog-2026-06.md:7535` | BL-131, opening `:7484` |
| `**Annotated 2026-08-09.**` | `docs/backlog-2026-06.md:7586` | BL-132, opening `:7547` |

**Where each insertion point falls, with the surrounding context asserted rather than quoted
(F6d), at r1's tree.**

At `:7535`, the **preceding** unit is BL-131's closing sequencing paragraph — it opens
`**It blocks nothing in m4 and it blocks provider four.**` and ends by placing the row *"after
the harness consolidation round, before provider four"*. That is **argument about the row's
timing**, the last substantive claim the row makes. The **following** unit at `:7542` is the
row's provenance line, `` `Source: m4 t5b G2 gate-stop and G7, 2026-08-07. …` ``, which attests
where the row's *content* was derived. The annotation therefore sits between a claim and the
attestation of that claim's origin.

At `:7586`, the **preceding** unit is BL-132's field block — three bolded fields, `**Owes:**`,
`**Costs:**`, `**Collides with:**`, the last of which ends `**Take BL-131 first**`. That is the
row's **structured field set**, not prose. The **following** unit at `:7591` is again that row's
`Source:` provenance line, dated 2026-08-07. Same position, different preceding unit type.

Both insertions fall **inside a row** and **before its provenance line**. Neither falls at a row
boundary.

**What actually bounds the re-attribution.** Each annotation **opens with its own date** —
`**Scoped 2026-08-09 into …**` and `**Annotated 2026-08-09.**` — and each row's `Source:` line
carries a **different, earlier date, 2026-08-07**, in both rows. Two dates three days apart
cannot be read as one authored unit: a reader reaching the `Source:` line has already passed a
dated block that the `Source:` predates, so the provenance cannot be attached to it without the
dates contradicting. **The dates are the bound, and they are the whole of it.**

**What was rejected as a justification.** r0 applied the rule and then cleared itself, citing
*"the file's established convention"* — BL-070's dated `**Done-when amended 2026-08-07…**` block
sitting above its own `Source:` line in the same file. That is **precedent for the defect, not a
defence of it.** The rule was carried out of the previous cycle precisely because that placement
re-attributes both paragraphs; pointing at an earlier instance of the placement shows the
practice is established, not that it is sound. **Convention is not the reason and is not recorded
as one here.**

The second half is procedural and independent of whether r0's conclusion was right: **an
implementer does not clear a carried rule on the reviewer's behalf.** A rule carried into a round
is in force for that round until the reviewer discharges it. r0 reached the correct outcome —
the placement does stand — by a route that was not r0's to take.

**Disposition, on the reviewer's ruling at r1 F6: the placement stands and both annotations stay
where they are.** `docs/backlog-2026-06.md` is not touched by r1. What changed is the recorded
justification, and only that.

---

## Closing note

**This file is the committed record of the m5 scoping landing; the r0 and r1 packets are not.**
Neither packet is committed in either repo, and content that lives only in a packet does not
travel — which is the same failure §Not established item 2 records about BL-131's own `Source:`
line, one level up. Where this file and a packet disagree, this file is the artifact.

Every figure, line number, count and quotation above was **derived in this session at r1's tree**
by the command printed beside it, and each command was transcribed after it exited. Nothing was
re-run to illustrate a result obtained another way, and nothing was carried from r0's packet
except the four divergence classes and the six verification subjects, both marked as such where
they appear. Line numbers cited into `cloudcost/m5-n1-compose.md` are **r1** line numbers: F7
inserted four lines above `:13` and F2 removed four, so the file is 300 lines at both commits
while anchors between `:6` and `:57` differ from r0's.

`Landed at r1. Commits: r0 = eebd47c7acafbc6b9eb93682b3f3a6aaa8689802; r1 = this commit.`

---

## Review

`[Authored by the reviewer, 2026-08-09, at r2. R20's shape: findings verbatim,
dispositions beneath. Covers r0 and r1 of the m5 scoping landing. This edit is
not a ticket round and gets no review file.]`

**F1 — anchor discrepancy.** Two sessions at the same agents HEAD gave two
different line numbers for the same claim about `cloudcost/m4-consolidation.md`:
`:52` in the scoping read, `:362` in r0's packet. A line number cannot move at a
fixed HEAD, so at most one is right — or there are two such statements and both
reports were partial.

> **Disposition: resolved at r1, and the finding's own framing was wrong.**
> Neither report was wrong and neither was complete. `:52` is a scope exclusion
> gating provider four on the seam sweep and the harness round; `:362` is a
> sequencing rationale citing the seam sweep by analogy; the sequence lines at
> `:249–250` and `:1228–1229` name no seam sweep. §Not established item 1 in the
> round document is correct as landed and was not edited. §F1's own table
> conflated `:362` with `:52` and was corrected in place at r2 (G3).

**F2 — §6 heading level.** The landed document promoted `## t1 —` and `## t2 —`
to top level. §6's template specifies `### t<N> — <title>`. r0's verification 1
checked field NAMES and not the heading that carries them, so a divergence passed
as PASS. A defect in the authored document, not in the landing.

> **Disposition: applied at r1, and the finding's supporting claim was corrected
> by the implementer.** The finding cited "both sibling cycle documents" as
> nesting tickets under §Ticket set. Three cloudcost cycle documents do —
> `cloudcost/milestone.md`, `m2-milestone.md`, `m3-milestone.md` — and
> `m4-consolidation.md`, the one the finding leaned on, does not: it carries a
> state table and no ticket *sections* — its three `###` headings under
> §Ticket set carry none of §6's seven fields (derived at r2, G2). The
> correction is accepted; §6's template is the authority regardless of what the
> siblings do.

**F3 — R20 restatement.** r0's closing observation characterised R20 as making an
implementation-notes file the committed record for a reviewer-authored
section-scoped edit, while the same packet's anchor table quoted R20 as *"is not a
ticket round and gets no review file."* Those are not the same claim and the
second is a quotation. Resolve R20's body and restate.

> **Disposition: resolved at r1, and the finding's premise inverted.** R20's first
> body line reads *"Its implementation-notes file is its committed record."* r0's
> observation was faithful to the body; the anchor table's quotation was
> heading-only and carried one half of a two-part rule. The reviewer wrote the
> finding expecting the opposite and was wrong about which half was partial.
> **Standing consequence, recorded because it binds work that has not run yet:**
> every future reviewer-authored section-scoped edit in this round — pinning t1's
> done-check invocation, completing t2's R13-marked slots, authoring the ruling
> into §Ratified decisions — owes its own implementation-notes file as its
> committed record, with the reviewer's findings appended there as a dated
> `## Review` section. Not a packet. Not this file.

**F4 — landing record.** No in-repo artifact recorded that the landing session
ran: the round document's deviation note was authored before the session it
describes, and r0's six verifications existed only in a packet. §Not established
item 2's own shape one level up.

> **Disposition: accepted and created at r1** as this file. Its filename diverges
> from the directory's dominant `*-implementation-notes.md` pattern; the
> divergence is raised in the file's own opening blockquote and stands — no ticket
> ran, so the notes suffix would describe it wrongly.

**F5 — population derivation.** r0's verification 2 called a 21-path list "every
path named in the landed document" and checked it, but the list was
hand-assembled rather than derived from the file. A count over an undemonstrated
population is carrier 1.

> **Disposition: applied at r1.** The mechanical derivation returned 23 tokens:
> three the hand list missed (`cloudcost/`, and the bare basenames
> `compose_report_data.py` and `tools.json`, both normalised to qualified forms
> before the count) and one the hand list supplied from knowledge of the tree
> rather than from the document (`cloudcost/docs`). Every one of r0's 21 was real
> and correctly resolved. What was missing was the derivation, not the arithmetic
> — which is the carrier exactly.

**F6 — the attribution rule, self-clearance reversed.** §Carried in's first rule
is in force for this round. r0 applied it and then cleared it as *"the file's
established convention"*, citing BL-070's dated block sitting above its own
`Source:`. That is precedent for the defect, not a defence of it.

> **Disposition: placement stands, justification replaced, application recorded
> at r1.** What bounds the re-attribution is the date pair — each annotation opens
> 2026-08-09, each row's `Source:` carries 2026-08-07 — and that is the whole of
> it. Convention is not the reason and is not recorded as one. The procedural half
> stands independently of r0 having reached the right outcome: an implementer does
> not clear a carried rule on the reviewer's behalf.

**F7 — two section names.** `## Why this exists` and `## Scope` existed as
unheaded opening paragraphs, leaving the round document ungreppable by the section
names its siblings use.

> **Disposition: applied at r1.** Headings inserted, no text moved. The residual
> divergence against `m4-consolidation.md` is five close-side sections, which a
> document opened before its first ticket cannot carry.

**F8 — this section's own absence.** `m5-scoping-landing-notes.md` was created at
r1 as R20's committed record and carried no `## Review` section, so the reviewer's
findings on the edit remained in packets alone — the gap the file exists to close,
one level up. Found only because F3 forced R20's body to be read in full rather
than cited from its heading.

> **Disposition: closed by this section, at r2.**

`Source: m5 scoping landing, r0 (agents eebd47c) and r1 (agents a039a0d),
2026-08-09. Findings authored by the reviewer; dispositions record what the
implementing sessions established, including where they corrected the finding.`
