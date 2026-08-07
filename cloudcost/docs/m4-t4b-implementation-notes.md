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

### G4 — BL-074 is open; its Done-when verbatim

```
$ sed -n '/^### BL-074/,/^### BL-075/p' docs/backlog-2026-06.md | grep -cE "^\*\*DONE|^#### DONE|^\*\*Closed"
0
```

**PASS — no DONE section; the row is open.** Its Done-when, verbatim:

> **Done when:** every provider-differing value in shared machinery is enumerated with a
> schema-level-or-adapter-owned ruling; the ones ruled schema-level are in §Normalized schemas;
> m1's "one seam" text is corrected; the sweep's *method* (how completeness was established) is
> recorded, so this is an enumeration and not another observation.

Four clauses. t4a discharged the first and the fourth; t4b discharges the second and the third.
**The row is still not closed by this ticket** — no DONE section is written here, per the ticket's
scope and because t4c's rows are the code consequences the second clause creates.

> One deviation of wording, declared: the Done-when says the schema-level rulings go *"in
> §Normalized schemas"*. They are in **§Contracts**, a new sibling section in the same file,
> immediately after §Normalized schemas. §Normalized schemas states the *shapes* and is a frozen
> m1 artifact that two later milestones cite as frozen (`m2-milestone.md:361` calls it *"the frozen
> §Normalized schemas"*); appending 48 value-contracts into it would have rewritten a document
> other documents rely on being stable. A sibling section satisfies the clause's intent — the
> rulings are stated, in the schemas document, where a reader of §Normalized schemas finds them —
> without falsifying the frozen-ness other files assert. Flagged rather than taken silently.

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

Per the ticket's ruling that §Open items is live operational guidance. **After**, verbatim:

> ```
> - **`STOPPED_STATES` normalisation — ~~the one seam~~ ~~*one of three seams*~~ *one of 54 censused
>   values* where a provider's own vocabulary or cost model reaches shared machinery.
>   RESOLVED at m2 t2 a.**
> ```

and the correction paragraph:

> ```
>   *Correction (m2 t1/t2, BL-074): "the one seam" was observation, not enumeration — the
>   **Adjacent-case** rule's failure mode. Three were known by m2: (1) this one; (2) the
>   `type` vocabulary, un-enumerated by m1 so DO's `droplet`/`reserved_ip` sat inside the rules
>   (resolved at t2 a′ — see §Normalized schemas); (3) the assumption that a provider bills a
>   resource regardless of state, which made the stopped-with-storage saving under-report
>   (resolved at t2 c).*
>   *Corrected again (m4 t4a/t4b, BL-074, 2026-08-07) — and "at least three" was itself an
>   observation, for the same reason "the one seam" was: nobody had enumerated. **The census found
>   54**, of which the four candidates BL-074 named and the three later observations account for
>   only **8**. The adjudication ruled **48 schema-level, 4 adapter-owned, 2 neither**; all 54 are
>   now stated as contracts in **§Contracts (C1–C15)**, each cited there by census item id. The
>   substantive finding is that this was never a handful of seams to close but a large, mostly
>   undocumented contract — so the deliverable was a contract section, not a migration. The census's
>   method, and the argument for why it is an enumeration rather than a fourth observation, is
>   `cloudcost/docs/m4-t4a-implementation-notes.md` §2.* Raised in
> ```

Two editorial choices, both declared. The m2 strikethrough is **kept and extended** rather than
replaced — `~~the one seam~~ ~~*one of three seams*~~ *one of 54 censused values*` — so the passage
carries its own correction history on its face; that history is the point of the entry. And the m2
correction paragraph's *"There were at least three"* became *"Three were known by m2"*: the same
fact, restated so it reads as a statement about m2's knowledge rather than about the world, which
is what made it wrong.

**Every number in the new text was re-derived** — 54 at G1, and 48/4/2 in §3 below. None was
carried from the ticket.

---

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

## 5. Gaps named rather than filled

Where the record does not establish what a contract would have to say, the contract says so. Three:

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

Three further items are **recorded, not filed**, because no current provider exhibits them —
D15's many-to-many under-report, D17's wall-clock fallback, P4's silent triple-failure. t4c's
membership rule excludes exactly these three, and its Done-when requires the exclusions be recorded
with their reasons.

---

## 6. What t4b did not do

- **No code.** No file under `cloudcost/scripts/` was touched; the eight blob hashes are unchanged.
- **No backlog row.** BL-074 gets no DONE section here. The eleven defect rows and the three
  recorded exclusions are t4c's, and **t4c is held until this ticket closes and is pushed.**
- **No ruling changed.** Every ruling implemented is the ticket's; where I disagreed with the
  ticket's text (§3) I reported rather than adjusted.
