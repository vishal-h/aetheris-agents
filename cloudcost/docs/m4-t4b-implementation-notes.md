# m4 t4b — the BL-074 rulings, written as contracts

**Ticket:** t4b, the ruling half of the t4 split. **Row:** BL-074. **Date:** 2026-08-07.
**Predecessor:** m4 t4a, the seam census (`cloudcost/docs/m4-t4a-implementation-notes.md`).
**Successor:** m4 t4c, **held** — no backlog row is filed by this ticket.

Documentation only. No code change is in scope; every code consequence named in §Contracts is
marked **[code consequence]** and is owed a row by t4c.

---

## 1. Step-1 gate — all five checked before any edit

### G1 — the census exists with exactly 54 items, six fields each

Re-derived from the file, not taken from the notes or the ticket.

```
$ cd /home/it/sandbox/elixirws/aetheris-agents
$ F=cloudcost/docs/m4-t4a-implementation-notes.md
$ grep -cE "^#### (X|N|D|F|P|R)[0-9]+" "$F"
54
$ for g in X N D F P R; do printf "  %s = %s\n" "$g" "$(grep -cE "^#### $g[0-9]+ " "$F")"; done
  X = 5
  N = 9
  D = 21
  F = 4
  P = 11
  R = 4
$ for f in "Meets" "Diverges today" "Could diverge" \
           "If ruled schema-level" "If ruled adapter-owned" "Consumers"; do
      printf "  %-24s %s\n" "$f" "$(grep -cE "^- \*\*$f\*\*" "$F")"; done
  Meets                    54
  Diverges today           54
  Could diverge            54
  If ruled schema-level    54
  If ruled adapter-owned   54
  Consumers                54
$ git ls-files --error-unmatch "$F" && git log --oneline -1 -- "$F"
cloudcost/docs/m4-t4a-implementation-notes.md
904a568 docs(m4 t4a r2): r0 held 53 not 54; §Sequence updated on the reviewer's ruling
```

**PASS.** 54 items; X×5, N×9, D×21, F×4, P×11, R×4; all six fields at 54. Committed at `904a568`.

### G2 — locate §Normalized schemas; ambiguity is the failure

```
$ cd /home/it/sandbox/elixirws
$ grep -rniE "^#+.*normalized schema" --include="*.md" aetheris-agents/ aetheris/
aetheris-agents/cloudcost/milestone.md:169:## Normalized schemas (the adapter contract — this is what m1 proves)
aetheris-agents/cloudcost/m2-milestone.md:361:### AWS field-mapping notes (how AWS populates the frozen §Normalized schemas — not a re-spec)
```

**PASS — exactly one section, no ambiguity.**

| | |
|---|---|
| **Repo** | `aetheris-agents` (this repo — **not** the harness) |
| **File path** | `cloudcost/milestone.md` |
| **Exact heading text** | `## Normalized schemas (the adapter contract — this is what m1 proves)` (`:169`) |

The second hit is **not** a section by that name: it is a `###` sub-heading in a *different*
milestone document that *cites* §Normalized schemas and explicitly says it is *"not a re-spec"*.
Checked and excluded rather than counted, because a citation and a definition look alike to a
heading grep — the substring-versus-field distinction, applied to the gate that exists to catch it.

**Consequence worth stating**, because it collapses two Done-when clauses into one: **§Normalized
schemas and §Open items are sections of the same file.** So Done-when 5's *"the schemas document
and `cloudcost/milestone.md`"* names **one** file, not two, and both §1 and §2 of this ticket land
in it.

### G3 — the "one seam" text in §Open items

`## Open items carried forward (not this milestone)` is at `cloudcost/milestone.md:569` (pre-edit
numbering). The passage, **quoted verbatim before editing**:

> ```
> - **`STOPPED_STATES` normalisation — ~~the one seam~~ *one of three seams* where a provider's
>   own vocabulary or cost model reaches shared machinery. RESOLVED at m2 t2 a.**
>   `detect_orphans.py:71` was `STOPPED_STATES = {"off"}  # DO vocabulary`, read by
>   `rule_stopped_droplet_with_attached_storage` and pinned by three tests precisely so a
>   second provider could not widen it silently. m2 t2 shrank it to the schema-level
>   `{STATE_STOPPED}` and moved the mapping into each adapter.
>   *Correction (m2 t1/t2, BL-074): "the one seam" was observation, not enumeration — the
>   **Adjacent-case** rule's failure mode. There were at least three: (1) this one; (2) the
>   `type` vocabulary, un-enumerated by m1 so DO's `droplet`/`reserved_ip` sat inside the rules
>   (resolved at t2 a′ — see §Normalized schemas); (3) the assumption that a provider bills a
>   resource regardless of state, which made the stopped-with-storage saving under-report
>   (resolved at t2 c). BL-074 sweeps for the rest; the rule-catalog age thresholds and the
>   `keep=true` tag spelling are the named next candidates.* Raised in
>   `docs/t2-implementation-notes.md:170`; promoted here at m1 close because it gates the
>   fan-out and an implementation-notes file does not travel to the next ticket's session.
> ```

**PASS.** The text exists and already carries one correction, from m2. **That is the finding worth
carrying forward**: m2 corrected *"the one seam"* to *"at least three"* — and *"at least three"*
was itself an observation, produced the same way, by the same failure mode the sentence is
describing. The passage had corrected its count without correcting its method. §2 below corrects
both.

### G4 — BL-074 is open; its Done-when **in full**

```
$ sed -n '/^### BL-074/,/^### BL-075/p' docs/backlog-2026-06.md \
    | grep -cE "^\*\*DONE|^#### DONE|^\*\*Closed"
0
```

**PASS — no DONE section; the row is open.** Its Done-when, **quoted in full** (r0 quoted it
through three of its four clauses and stopped mid-sentence at *"the sweep's method (how
completeness was established) is"* — the cited-means-read failure at the point it costs most,
because the unread clause is the one t4a exists to satisfy):

> **Done when:** every provider-differing value in shared machinery is enumerated with a
> schema-level-or-adapter-owned ruling; the ones ruled schema-level are in §Normalized schemas;
> m1's "one seam" text is corrected; the sweep's *method* (how completeness was established) is
> recorded, so this is an enumeration and not another observation.

#### Per-clause assessment

| # | Clause | Satisfied? | By what |
|---|---|---|---|
| 1 | *every provider-differing value in shared machinery is enumerated with a schema-level-or-adapter-owned ruling* | **Yes** | Enumeration: t4a's census, 54 items from a structural extraction over 518 AST nodes, with a recorded completeness argument. Ruling: t4b's adjudication, 48 schema-level / 4 adapter-owned / 2 neither. **One qualification, stated not glossed**: two items (D5, R4) received **neither** ruling, D5 because the value is operator configuration and R4 because it is an environment dependency. The clause offers two arms; the honest report is that two items fit neither and are recorded with their reason rather than forced. |
| 2 | *the ones ruled schema-level are in §Normalized schemas* | **Yes, against the amended clause** | §Contracts (C1–C15) in `cloudcost/milestone.md`, all 48 stated. **As originally written this clause was unsatisfiable** under the accepted deviation, so it was amended in `docs/backlog-2026-06.md` to name §Contracts — **before** the row was assessed against it, per the reviewer's ruling and on t2/BL-069's precedent. Before and after are quoted in the packet. |
| 3 | *m1's "one seam" text is corrected* | **Yes** | `cloudcost/milestone.md` §Open items, corrected in place. r1 corrected the correction: the r0 text attached a seam predicate to all 54 (false — four meet nothing adapter-supplied) and asserted an unshown total; both are fixed below. |
| 4 | *the sweep's method (how completeness was established) is recorded, so this is an enumeration and not another observation* | **Yes** | `cloudcost/docs/m4-t4a-implementation-notes.md` §2 — the extraction source inlined verbatim and re-runnable, per-class node counts a reader can diff, the classification criterion, the exclusion record with reasons, the completeness argument, and **§2.7 "what would not have counted"**, which names *"I searched for the known candidates and found them"* as the failure mode. §2.6 also bounds the claim: an AST-class census is complete *relative to its class list*, and the method cannot answer from inside itself whether a further population remains. |

**All four clauses satisfied — and BL-074 is still not closed here.** No DONE section is written by
t4b. The row's rulings created eleven defect rows and three recorded exclusions; those are t4c's,
and a Done-when satisfied by documents whose consequences have nowhere to live is the
complete-but-unmarked shape BL-102 exists for. **BL-074 closes at t4c.**

### G5 — repo of each censused script, and the command form used

```
$ for f in _normalized.py detect_orphans.py compose_report_data.py render_report.py; do
      git -C aetheris-agents ls-files --error-unmatch "cloudcost/scripts/$f"; done
cloudcost/scripts/_normalized.py
cloudcost/scripts/detect_orphans.py
cloudcost/scripts/compose_report_data.py
cloudcost/scripts/render_report.py
$ git -C aetheris ls-files --error-unmatch scripts/sprint.sh
scripts/sprint.sh
```

**PASS.** All four censused scripts are in **`aetheris-agents`**. The cross-repo consumer named by
N1 — `scripts/sprint.sh`, which imports `CANONICAL_TYPES` by name — is in **`aetheris`**, and C1
says so, because a change to C1 is therefore a cross-repo change.

**Command form used in this ticket: `git -C <repo>` and absolute paths throughout**, with the one
exception of `cd`-into-repo blocks whose `cd` is inside the quoted command itself. No command
depends on an inherited working directory.

---

## 2. What was written

### 2a. §Contracts — `cloudcost/milestone.md:293`

C1–C15, inserted immediately after §Normalized schemas and before §Contract refs. Each contract
states, in prose: what shared machinery guarantees; what an adapter must guarantee for that to
hold; the census items it covers, **cited by item id**; and, where the census recorded an arm as
closed, that the arm is closed **and why**.

Line numbers are deliberately absent as identifiers — item ids are the stable reference, and a
census whose own findings included *a verified citation decays the moment the file moves* should
not key its contract section on line numbers.

### 2b. The m1 correction — corrected **in place**, no superseded note

Per the ticket's ruling that §Open items is live operational guidance. **Rewritten at r1** — the r0
text failed twice, and both failures are recorded here as they happened, because a correction
section that hides its own corrections is the defect it is about.

**r0 attached a false predicate to the 54.** It read *"one of 54 censused values **where a
provider's own vocabulary or cost model reaches shared machinery**"* — which asserts all 54 are
seams. The census denies it: four items' **Meets** field states they meet nothing adapter-supplied
(D8, D21, F1, R4), and R4 is censused and reported explicitly as **not a seam**. That is the
passage's own failure recurring inside the correction — a count replaced without re-checking the
predicate it hangs on. `the one seam` → `three seams` → `54 censused values`, and only the first
two were seams by that sentence's own definition.

**r0 asserted an unshown total.** It said m2's *"four candidates … and three later observations
account for only 8"* — four plus three is seven, and nothing showed where the eighth came from or
which ids were in either group. **Branch (b) was taken: the clause is dropped.** Branch (a) fails
its own test — mapping m2's ordinary-language phrase *"the rule-catalog age thresholds"* onto a
definite number of census ids is inference, not reading, and this cycle has dropped that class
twice already. The correction's point stands without any arithmetic about what m2 had accounted
for, and is the stronger sentence for it.

**r0 rewrote an m2-datelined paragraph.** `There were at least three` had been silently replaced
with `Three were known by m2` *inside* m2's own dateline — making an m2 correction say something m2
did not write, and removing from view the exact phrase the new correction criticises. **The original
paragraph is now restored verbatim and untouched**, including its closing sentence about the named
next candidates, which r0 had also dropped. The file's house style has a strikethrough form for the
*bullet* but none for a paragraph, so per the reviewer's instruction the original stands unmarked
and the dated correction does the work beneath it.

**AFTER**, verbatim:

> ```
> - **`STOPPED_STATES` normalisation — a place where a provider's own vocabulary reached shared
>   machinery, and ~~the one seam~~ ~~*one of three seams*~~ *one of 54 values censused for provider
>   divergence at m4 t4a*. RESOLVED at m2 t2 a.**
> ```

The predicate now attaches to `STOPPED_STATES` itself — *a place where a provider's own vocabulary
reached shared machinery* — and the strikethrough chain describes only its membership in a censused
set. Nothing is claimed about the other 53. The chain is kept, per instruction.

> ```
>   *Correction (m2 t1/t2, BL-074): "the one seam" was observation, not enumeration — the
>   **Adjacent-case** rule's failure mode. There were at least three: (1) this one; (2) the
>   `type` vocabulary, un-enumerated by m1 so DO's `droplet`/`reserved_ip` sat inside the rules
>   (resolved at t2 a′ — see §Normalized schemas); (3) the assumption that a provider bills a
>   resource regardless of state, which made the stopped-with-storage saving under-report
>   (resolved at t2 c). BL-074 sweeps for the rest; the rule-catalog age thresholds and the
>   `keep=true` tag spelling are the named next candidates.*
>   *Corrected again (m4 t4a/t4b, BL-074, 2026-08-07). **"At least three" was itself an observation**,
>   for the same reason "the one seam" was: nobody had enumerated. The m2 correction fixed the count
>   and left the method — which is why it needed correcting a second time. m4 t4a swept the four
>   scripts structurally and **censused 54 values**; the adjudication ruled **48 schema-level, 4
>   adapter-owned, 2 neither**, and all 54 are now stated as contracts in **§Contracts (C1–C15)**,
>   each cited there by census item id.*
>   *Two things this correction does **not** claim. It does not say all 54 are seams: the census
>   swept for provider divergence and censused some values it then reported as **not** seams — four
>   meet nothing adapter-supplied at all (D8, D21, F1, R4), and R4 is recorded explicitly as
>   unrulable by this row's own schema-level-or-adapter-owned dichotomy. **A seam count, as distinct
>   from a censused count, is not established by t4a and is not asserted here.** Nor does it restate
>   what m2's candidates would have amounted to in census terms; mapping that prose onto a definite
>   number of census ids is inference, not reading. The substantive finding is that this was never a
>   handful of seams to close but a large, mostly undocumented contract — so the deliverable was a
>   contract section, not a migration. The census's method, and the argument for why it is an
>   enumeration rather than a fourth observation, is
>   `cloudcost/docs/m4-t4a-implementation-notes.md` §2.* Raised in
> ```

**The seam count is a gap, named under §5** — t4a establishes a censused count, not a seam count,
and none is manufactured to fill the sentence.

#### The derivation behind "four meet nothing adapter-supplied"

The pass parses each census item's **Meets** field and matches the census's own phrasings for
meeting nothing adapter-supplied:

```
$ python3 -c '
import re; from pathlib import Path
blocks = re.split(r"^#### ", Path("cloudcost/docs/m4-t4a-implementation-notes.md").read_text(), flags=re.M)[1:]
pat = re.compile(r"nothing adapter-supplied|the absence is the item|nothing;|nothing\.", re.I)
for b in blocks:
    m = re.match(r"([XNDFPR]\d+)\b", b)
    mm = re.search(r"^- \*\*Meets\*\* — (.+?)(?=\n- \*\*)", b, re.S|re.M)
    if m and mm and pat.search(" ".join(mm.group(1).split())):
        print(m.group(1), "—", " ".join(mm.group(1).split())[:105])'

D8 — nothing adapter-supplied directly; each is the prior probability that a rule's firing means th
D21 — nothing adapter-supplied; it is the self-description of the run.
F1 — nothing; the absence is the item. The rule fires on `type == load_balancer` and `attached_to i
R4 — nothing adapter-supplied.
```

**Four items: D8, D21, F1, R4.** Reported by id with the command, per instruction; no total was
taken from the ticket. A separate pass for items reported explicitly as non-seams returns **R4**
(*"Censused and reported as not a seam"*; *"cannot be ruled by BL-074's dichotomy"*).

### 2c. BL-074's Done-when clause 2, amended before assessment  *(Edit 5)*

**BEFORE**, verbatim:

> ```
> **Done when:** every provider-differing value in shared machinery is enumerated with a
> schema-level-or-adapter-owned ruling; the ones ruled schema-level are in §Normalized schemas;
> m1's "one seam" text is corrected; the sweep's *method* (how completeness was established) is
> recorded, so this is an enumeration and not another observation.
> ```

**AFTER**, verbatim:

> ```
> **Done when:** every provider-differing value in shared machinery is enumerated with a
> schema-level-or-adapter-owned ruling; the ones ruled schema-level are in
> `[amended 2026-08-07]` **§Contracts** ~~§Normalized schemas~~;
> m1's "one seam" text is corrected; the sweep's *method* (how completeness was established) is
> recorded, so this is an enumeration and not another observation.
> ```

followed in the row by a dated amendment note giving the reason.

**The correction to my own r0 reasoning**, per the ruling. The load-bearing argument is **not** the
freeze: §Normalized schemas states **shapes**; §Contracts states **value semantics and adapter
obligations**. Interleaving 48 of the second into the first makes the shapes harder to read for
every future reader, and that argument holds whether or not anything ever called the section frozen.

The freeze is secondary — and it is now **derived rather than asserted**. r0 said *"later milestones
cite as frozen"*, a plural claim resting on the one citation I had actually read. Swept:

```
$ grep -rniE "frozen.{0,40}normalized schema|normalized schema.{0,40}frozen" \
    --include="*.md" . /home/it/sandbox/elixirws/aetheris --exclude-dir=priv | wc -l
12
```

**12 citations across 9 files** (excluding this ticket's own notes): `cloudcost/m2-milestone.md` ×3,
`cloudcost/m3-milestone.md`, `cloudcost/runbook.md`, `cloudcost/docs/t1-implementation-notes.md` ×2,
`cloudcost/docs/t3-implementation-notes.md`, `cloudcost/docs/m3-linode-scout.md`,
`docs/reviews/m2-cloudcost-closeout.md`, and two handoffs. **The plural claim holds — but it held by
luck**, since I had checked one and written "milestones". `cloudcost/runbook.md` is live operational
guidance and is the citation that would have cost most.

**No row is filed.** This is the only backlog-file edit in scope; t4c owns the rows.

### 2d. The cycle document  *(Edit 6, authorised)*

Four things this landing falsifies, not one — checked rather than assumed:

1. **§Ticket set, the t4b row** — read `not started — blocked on the rulings`, and claimed
   *"BL-074 closes here"*. Both false: t4b is closed, and BL-074 closes at **t4c**.
2. **§Ticket set had no t4c row at all.** Added, marked held.
3. **§Sequence** — read `t4a → t4b`; now `t4a → t4b → t4c`, with a note that t4c is gated on t4b
   being closed **and pushed**.
4. **§Why t4 became t4a and t4b** — described a two-way split that is now three-way. A dated
   sub-note records the second split and its reason: the census's output separated into values whose
   ruling is a sentence about which side of the seam they live on, and values that **stay broken
   whichever arm they land in**, and ruling the second kind does not fix it.

## 3. The tally, re-derived

The ticket's counts are its author's and were to be re-derived rather than copied. Derived from the
ruling table by reading off the ruling column:

| | Items | Count |
|---|---|---|
| **A** — adapter-owned | X2, D13, D14, D19 | **4** |
| **N** — neither arm | D5, R4 | **2** |
| **S** — schema-level | the remaining 54 − 6 | **48** |
| **†** — defect-flagged (t4c) | X4, X5, N8, D5, D12, D16, F2, F3, P2, P8, P11 | **11** |

**48 / 4 / 2, and 11 defect-flagged. No disagreement with the ticket.**

The contract assignments were derived twice and cross-checked: once by reading the per-item
`Contract` column of the ruling table, once by reading the `Covers` column of the C1–C15 table.
**The two agree on all 54**, which is the check worth having — the two columns are independent
statements of the same mapping, so agreement is evidence and disagreement would have been a real
finding.

### Two discrepancies in the ticket text, reported rather than reconciled

1. **Done-when clause 2 says "The three arms recorded as closed" and then lists nine items** —
   N4, N9, D12, D20, P2, P9, R2, R3, X5. The list of nine is correct and matches the census's own
   §6 (*"Nine items have one genuinely closed arm"*); **"three" is a wording slip**. I implemented
   the list, not the number: all nine say closed-and-why. Reported because the ticket asked for
   disagreement rather than silent reconciliation, and because a count-versus-list mismatch is
   precisely the class this ticket's predecessor spent three rounds on.
2. **Done-when clause 5 names "the schemas document and `cloudcost/milestone.md`" as though they
   were two files.** They are one (G2). Satisfied trivially, but stated so the clause is not read
   as permitting a second file.

---

## 4. Done-when, clause by clause

### 1. §Contracts exists with C1–C15; every census item cited by id in exactly one contract

Derivation — parses the cited ids out of the contract headings and compares against the census's
own item headings:

```
$ python3 - <<'PY'
import re
from pathlib import Path
ms = Path("cloudcost/milestone.md").read_text()
sec = ms[ms.index("## Contracts (C1–C15"):ms.index("## Contract refs (read, do not restate)")]
cites = {m.group(1): [x.strip() for x in m.group(2).split(",")]
         for m in re.finditer(r"^### (C\d+) — .*?\*\((.+?)\)\*", sec, re.M)}
census = re.findall(r"^#### ([XNDFPR]\d+) ",
                    Path("cloudcost/docs/m4-t4a-implementation-notes.md").read_text(), re.M)
allc = [i for v in cites.values() for i in v]
...
PY
contracts found      : 15  (C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15)
census items         : 54
ids cited (total)    : 54
ids cited (distinct) : 54
cited more than once : none
in census, not cited : none
cited, not in census : none
```

**An exact bijection.** 54 cited, 54 distinct, nothing double-cited, nothing missed, nothing
invented. Per-contract distribution:

```
  C1   ( 3) N1 N8 D11          C9   ( 3) N6 D18 P10
  C2   ( 3) X1 N2 D10          C10  ( 4) P4 P6 P8 P11
  C3   ( 5) N3 N4 D12 D17 D20  C11  ( 3) R1 P2 P7
  C4   ( 4) N5 P3 P5 R2        C12  ( 1) X5
  C5   ( 3) N9 P9 R3           C13  ( 2) X2 D19
  C6   ( 4) X3 N7 D6 D7        C14  ( 2) D13 D14
  C7   ( 2) D15 D16            C15  ( 2) D5 R4
  C8   (13) D1 D2 D3 D4 D8 D9 D21 F1 F2 F3 F4 P1 X4
```

### 2. The nine closed arms each say closed **and why**

```
  N4   closed-arm stated with reason      P2   closed-arm stated with reason
  N9   closed-arm stated with reason      P9   closed-arm stated with reason
  D12  closed-arm stated with reason      R2   closed-arm stated with reason
  D20  closed-arm stated with reason      R3   closed-arm stated with reason
  X5   closed-arm stated with reason
```

The check requires the item id and the phrase *closed arm* in the **same paragraph**, so an arm
closed somewhere else in the contract does not pass it. X5 initially failed for that reason — the
arm was closed in C12 but the id appeared only in the heading — and C12 was rewritten to name X5 in
the closing sentence itself. **The check was not loosened to match the document; the document was
changed to satisfy the check.**

### 3. §Open items corrected, before and after quoted verbatim

§1 G3 (before) and §2b (after). Corrected in place, no dated superseded note, per the ticket's
ruling that the section is live operational guidance.

### 4. The tally re-derived; disagreements reported

§3. **48 / 4 / 2 / 11 — agreed.** Two discrepancies in the ticket's own text reported there rather
than reconciled.

### 5. No file outside the schemas document and `cloudcost/milestone.md` modified

```
$ git -C /home/it/sandbox/elixirws/aetheris-agents status --short
 M cloudcost/milestone.md
?? cloudcost/docs/m4-t4b-implementation-notes.md
$ git -C /home/it/sandbox/elixirws/aetheris status --short
(empty)
```

**One file modified**, and it is the one file the clause names (G2: the schemas document *is*
`cloudcost/milestone.md`). The harness repo is untouched.

The untracked file is **this document**. It is *created*, not *modified*, and it is required both
by the repo rule that implementation notes are a deliverable and by this ticket's own instructions
to *"record in the notes"* at G2 and G4. Declared rather than assumed to be permitted.

**`cloudcost/m4-consolidation.md` was NOT edited**, and the omission is deliberate. Its §Ticket set
row for t4b will read `not started` after this lands, which is false in its own commit — the exact
condition its §What t3, t4 and t5 inherit item 2 calls a `Touches` omission by design. t4a hit this
and held to the literal scope; the reviewer subsequently ruled the sibling case (§Sequence) owed and
authorised it. **Flagged for the same ruling rather than taken unilaterally.**

---

## 4b. r2 — the counts, the negatives, and the truth-maker sweep

Seven edits (A–G). No ruling, no census item and no C1–C15 mapping changed.

**The finding r2 names**: three committed numbers were produced by matching a phrase and written as
definite counts, in a commit whose subject is a passage that acquired numbers nobody derived.
**None of the three arguments needed a count — each needed a floor.**

| | Was | Is | Method now named? |
|---|---|---|---|
| **A** | *"four meet nothing adapter-supplied at all"* | *"at least four"*, with **N4** cited as a known case the method misses | yes — a match on the census's **Meets** field, stated as a lower bound |
| **B** | *"12 citations across 9 files"* | *"at least 12 across 9 files"* | yes — a search for the literal word `frozen` near the section name |
| **C** | *"six age and confidence thresholds"* | no count — *"age thresholds, confidence priors, two additive modifiers, a clamp, and three confidence bands"* | n/a — the count is gone |

**Edit A is the reviewer's specification gap before it is mine**, and they said so: the r1 ticket
keyed the derivation on the **Meets** field, which is what produced a phrasing match. What is mine
is that **the packet hedged and the file did not** — the packet said *"at least these four"* and the
committed sentence said *"four … at all"*. The hedge was load-bearing and it was lost in transit.
**N4** is the counterexample it was protecting: by substance it meets nothing adapter-supplied
(*"Output-side only; no adapter reads them"*), but its Meets field names a value, so the match
cannot see it. The committed text now cites N4 by name.

**Edit B's thirteenth hit is the claim itself.** The r1 command returns **13**; the enumeration
named 12. The thirteenth is `docs/backlog-2026-06.md:2549` — **the sentence asserting the count**,
which the search matches because it contains the phrase. Counting an assertion as evidence for
itself. It is **not** the harness hit the review guessed: every genuine citation is agents-side, so
the qualifier *"in this repo"* was doing no work and has been dropped. Reconciled explicitly in the
row rather than silently excluded.

**Edit C removed the count** rather than reconciling three figures. C8's opening said six, C8's body
enumerates three distinct age-threshold values across four rules and treats the confidences and the
activity window as separate populations, and the census's D21 states five thresholds exist as
constants. No derivation existed for any of them. The reviewer's suggested wording is adopted
verbatim because it is sufficient and cannot be wrong.

**Edit D scoped two unbounded negatives to their searches.** Both are in C8, both were absolute
negatives over a corpus asserted from a search that was not named:

- *"The rationale for 14-versus-7-or-30 is **not recorded anywhere**"* → **not established**, with
  the search stated: `cloudcost/` and `docs/` for `14 ?d(ays)?|fourteen`, **27 hits**, every one
  restating or using the value and none giving a reason.
- *"**The rationale is unrecorded.** No document says why m1 wrote `N` there."* → **not
  established**, with the search stated.

The gap is real either way; the claim is now the size of the evidence. Noted against myself: the
correct form was applied one paragraph earlier, separating the CLI asymmetry's established *origin*
from its unrecorded *reason*, and then not applied to the sentence beside it.

### Edit E — the truth-maker sweep, and its result

**Scope**: all 15 contracts, read for sentences asserting a property of **current code** that is not
traceable to a census item's fields. Sentences stating what a contract *requires* are out of scope.

**Result: one untraceable sentence found. It is C4's, the one the review named.** Everything else
that asserts a code property carries a census id whose fields establish it — C1's individual
`TYPE_*` imports and the unenforced canonicality (N1, N8), C2's source-text test (D10), C6's `k=v`
construction (X3), C7's unenforced `tag:` convention (D16), C8's write-only parameter block (D21),
C9's slug behaviour (N6), C11's comment-only guard (P7), C12's five unspecified I/O sites (X5),
C13's three `size` spellings (X2), C14's three-adapter satisfaction (D13). **Reported as a result:
the sweep changed one contract and confirmed fourteen.**

**C4's sentence was kept, not removed**, because it verified. Truth-maker added to the contract:

> read of `compose_report_data.py` at agents `a25f72f`. `service_totals` is the only function
> building a cost total (`:150`) and reads exactly `line_items`, `amount` and `totals` — never
> `monthly_cost_estimate`. The three reads of `monthly_cost_estimate` in that module are all in
> `coverage_section` (`:390`, `:404`, `:419`), the untagged-spender ranking.

**And the check found a precision the sentence needed**: `:419` **does** sum `monthly_cost_estimate`,
into `untagged_monthly_cost_estimate`. So *"never summed"* would be false and *"never summed **into
a cost total**"* is what holds. The existing wording was already the correct one — but it was
correct without anyone having checked, which is the condition the rule exists to end.

**One sentence was upgraded although it was traceable.** *"A test asserts the renderer stays
ignorant"* appears in C4's closed arm and in C11. It is traceable — R1's census entry carries it —
but the census took it from a **code comment beside `OPTIONAL_FIELDS`** that claims a test exists.
A comment asserting its own test coverage is not a truth-maker. Verified: the test is
`tests/test_render_report.py::test_the_region_block_names_no_provider_and_no_provider_payload_key`
(`:436`). Both contracts now cite the test, and C11 says explicitly that it is cited *rather than
taken from the comment beside `OPTIONAL_FIELDS` that claims it*.

### Edit F — branch (a): a fifth Done-when clause

Taken, as the review leaned. The assessment was **already applying a fifth clause** and it was
simply unwritten; an unwritten clause cannot be reviewed and cannot be checked at the close. The row
now reads *"and the rows the rulings created are filed"*, with a dated note explaining that this
makes the row **honestly unmet** rather than mysteriously open. The alternative — (b), a hold note —
would have left the Done-when recording what BL-074 asked for while the assessment silently applied
something else.

### Edit G — the t4b row's state

The row read `Closed` in a commit that was itself under review, so it was false from the moment r1
landed until r2 passes — the same class as the observation this ticket raised at r0, applied to the
row this ticket wrote.

**The file has no mid-review state form**: §Ticket set uses `Closed`, `not started`, and t1a-c's
`you are reading it`. Rather than invent a review-state vocabulary, the row is **written truthfully
for the commit it lands in** — `In review (r2)`. t1a-c is the precedent: a state that is true when
read, not a state predicted to become true. It becomes `Closed` in the commit that closes it.

---

## 5. Gaps named rather than filled

Where the record does not establish what a contract would have to say, the contract says so. Four:

1. **C8 — the rationale for the 14-day unattached-volume threshold is unrecorded.** The value is in
   m1's §t2 Scope, but no document says why 14 rather than 7 or 30. Named as a gap; the next
   provider that wants to argue against it has nothing to argue with.
2. **C8 — the CLI-override asymmetry has an established origin but no recorded rationale.** m1's
   §t2 Scope specifies the catalog as *"unattached volume >14d … snapshot older than **N days** …
   stopped droplet with attached storage >30d"* — the snapshot rule alone written with a symbolic
   threshold, the other two with literals, and the implementation rendered that faithfully as one
   flag and two constants. **Where it came from is a fact; why is a gap.** Recorded as unexplained
   rather than filled by inference, per the ticket's explicit instruction.
3. **C6 — the tag-coverage denominator question is stated and left open.** Restricting it to
   taggable resources would move `tag_coverage`, which C5 records as contractually shared between
   two stages, so it is not a local edit and is not decided here.
4. **§Open items — the seam count is not established** *(added r1)*. t4a censused 54 values swept
   for provider divergence; it did **not** establish how many are seams, and four of the 54 meet
   nothing adapter-supplied at all. So the corrected bullet states the **censused** count and what
   was censused, and asserts no seam count. **A number was not manufactured to fill the sentence**
   — which is the whole failure that bullet is a record of, and doing it would have been the third
   time.

Three further items are **recorded, not filed**, because no current provider exhibits them —
D15's many-to-many under-report, D17's wall-clock fallback, P4's silent triple-failure. t4c's
membership rule excludes exactly these three, and its Done-when requires the exclusions be recorded
with their reasons.

---

## 6. What t4b did not do

- **No code.** No file under `cloudcost/scripts/` was touched; the eight blob hashes are unchanged.
- **No backlog row filed.** BL-074 gets no DONE section here, and no row is created. The one
  backlog-file edit made is the **amendment of BL-074's own Done-when clause 2** (§2c), authorised
  by the reviewer and landed *before* the row was assessed against it, on t2/BL-069's precedent.
  The eleven defect rows and the three
  recorded exclusions are t4c's, and **t4c is held until this ticket closes and is pushed.**
- **No ruling changed.** Every ruling implemented is the ticket's; where I disagreed with the
  ticket's text (§3) I reported rather than adjusted. r1 changed no ruling either — the 54 items,
  the 48/4/2 tally and the C1–C15 mapping are untouched, as instructed.
- **The cycle document *was* edited at r1** (§2d), on the reviewer's authorisation. r0 held to the
  literal `Touches` and flagged; the ruling is that a cycle document false in its own commit is a
  `Touches` omission by design, and the fix is owed rather than optional.
