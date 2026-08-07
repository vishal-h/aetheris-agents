# m4 t4c — file the rows the rulings created, and close BL-074

**Ticket:** t4c, the filing half of the t4 split. **Row:** BL-074 — **closed here.**
**Date:** 2026-08-07. **Predecessors:** m4 t4a (the 54-item census), m4 t4b (§Contracts C1–C15,
agents `611feba`, pushed).

Documentation only. **17 rows filed, none implemented.** Which rows get taken and when is a
milestone-close decision; each row carries enough for that decision without re-deriving it.

---

## 1. The scope discrepancy, resolved before anything was filed

Two committed statements described t4c's scope and did not describe the same set:

- **§Contracts' preamble**: *"Where a code change genuinely follows, it is marked
  `[code consequence]` and is owed a backlog row by m4 t4c."* — a blanket commitment.
- **`cloudcost/m4-consolidation.md` §Ticket set**: *"11 rows filed, 3 exclusions recorded."*

**A specification gap in the t4b ticket, authored by the reviewer and named as theirs.** The
derivation (G2) settles the shape: **11 `[code consequence]` markers**, of which **3** are already
on the defect list (N8, P8, P11) and **1** is an exclusion (D17, marked *"recorded here, not
filed. [code consequence] **when taken**"* — a conditional marker), leaving **7** the defect list
does not reach.

**Ruled: file both sets, one file, one format, a `Kind` field.**

| Kind | States |
|---|---|
| **defect** | what is broken or missing **today**, established from the record |
| **contract consequence** | what §Contracts now **requires** that the code does not yet do |

The distinction is load-bearing for triage: a contract-consequence row that reads as a defect gets
triaged as one, and nothing in that set is broken today.

---

## 2. Step-1 gate

### G1 — both repos level with origin

```
$ git -C .../aetheris-agents status -sb  →  ## main...origin/main   (611feba)
$ git -C .../aetheris          status -sb  →  ## main...origin/main   (e75f838, unchanged)
```
**PASS.**

### G2 — every `[code consequence]` marker, derived

Parsed from §Contracts by walking each contract block and matching paragraphs containing the
marker, attributing each to the census id named in that paragraph.

**11 markers: N8 (C1), N3 (C3), D17 (C3, conditional), D20 (C3), N5 (C4), N7 (C6), D6 (C6),
P6 (C10), P8 (C10), P11 (C10), P7 (C11).**

Two needed resolving by reading rather than by pattern:

- **C4's marker names no id in its own paragraph.** The paragraph is the minor-unit exponent, which
  is **N5**'s schema-level arm (C4 covers N5, P3, P5, R2). Attributed to N5.
- **C3's D17 marker is conditional** — *"the defect is **recorded here, not filed**.
  `[code consequence]` **when taken**."* D17 is one of the three exclusions, so it takes no row;
  the marker is the hedge, not a commitment.

**Partition:** on the defect list → N8, P8, P11 (3). Exclusion → D17 (1). **Remainder → N3, D20,
N5, N7, D6, P6, P7 (7).**

### G3 — duplicate check across all 120 open rows

**No duplicates. Every item needs a new row.** Five rows were candidates and each was read:

| Row | Relation | Ruling |
|---|---|---|
| **BL-112** | X5 | **Two rows** — see below |
| **BL-098** | P7 | **Adjacent, not duplicate** — BL-098 is the *inventory* envelope's missing extras key; P7 is the *cost* envelope's `provider_extra` promotion. BL-098's own text draws the line: *"The **cost** schema sanctions `provider_extra`, but the m1 **inventory** schema has no extras key at all."* Two halves of one §Normalized decision; both rows now cite the other and ask to be sequenced |
| **BL-070** | P6, P8, P2, P11 | Not a duplicate — it retires dormant merge code and converges the slug functions. **Collides on the file**: BL-070 asks to be a dedicated cleanup, and four new rows edit the same module. Named in each |
| **BL-076** | P6 | Not a duplicate — `load_prior_snapshots` globbing vs service-name keying. Same MoM path; adjacency named |
| **BL-101** | P2, D6 | Not a duplicate — it redesigns the tag section. Same section and file; adjacency named in both |

A residual grep over twelve mechanism names (`last_activity_at`, `aged_snapshot`,
`usable_resources`, `source_granularity`, `age_phrase`, `KEEP_TAG`, `timestamp_warnings`,
`minor-unit`, `ephemeral`, `top_untagged`, `classify(`, `tag:`) returned hits only in BL-071
(a *finer* granularity, adjacency named in BL-122), BL-101, and **BL-074's own text** — the row
being closed, which is self-reference and not a duplicate.

#### BL-112 vs X5 — ruled two rows

They share a root cause and nothing else.

| | BL-112 | BL-118 (X5) |
|---|---|---|
| Repo | harness | aetheris-agents |
| Language | Elixir / BEAM | Python |
| Mechanism | `:file.native_name_encoding() == :latin1` | `locale.getpreferredencoding()` |
| Artifact | the `--json` payload's run label | cloudcost JSON read/written on disk |
| Symptom | a bare high byte where UTF-8 was expected | raise, or silent mis-decode into report text |

**Neither fix addresses the other's failure.** A single environment change — exporting `LANG` —
would mask both without repairing either, which is the argument *for* two rows rather than against:
one row would invite exactly that fix and leave both defects live. §Contracts C12 already states
*neither guards the other*; each row now cites the other as sibling.

### G4 — BL-074's Done-when, all five clauses

> **Done when:** every provider-differing value in shared machinery is enumerated with a
> schema-level-or-adapter-owned ruling; the ones ruled schema-level are in
> `[amended 2026-08-07]` **§Contracts** ~~§Normalized schemas~~;
> m1's "one seam" text is corrected; the sweep's *method* (how completeness was established) is
> recorded, so this is an enumeration and not another observation;
> `[added 2026-08-07]` **and the rows the rulings created are filed** — see the second amendment
> note below.

### G5 — the t4c row before this ticket

> `| **t4c** | File the defect rows the rulings created | BL-074 **closes here**; 11 rows filed, 3
> exclusions recorded | not started — **held until t4b is closed and pushed** |`

Reconciled against G2 in §6.

---

## 3. Part 1 — the three exclusions, confirmed not authored

All three are present in §Contracts with their reasons, each marked *recorded, not filed*.
**Confirmed by reading, not rewritten, and no exclusion row was filed.**

| Item | Contract | Reason, as §Contracts states it |
|---|---|---|
| **D15** | C7 | many-to-many attachment cannot be expressed and the join would under-report attached storage, silently lowering the stopped-compute saving — *"No current provider exhibits it"* |
| **D17** | C3 | the wall-clock fallback in `resolve_reference_date` — *"unreachable on all three current adapters"* |
| **P4** | C10 | a non-calendar period yields no MoM section, no history, forever, with nothing reported — *"No current provider exhibits it"* |

---

## 4. Row 11's precondition — run, and it failed

### Check 1 — does the case policy bite? **No.**

The sharp form: does any recorded resource name match the ephemeral pattern **case-insensitively
but not case-sensitively**? That is the only way the case-sensitivity can cost a firing.

```
distinct resource-name strings across all fixtures/data/output: 118
capitalised names: 11  ['Bangalore 1', 'Container Registry Subscription',
  'Credits & adjustments', 'Droplets', 'Example Team', 'IN GST',
  'Kubernetes Clusters', 'Overages', 'Product usage charges', 'Taxes', 'Zero Rate']
match case-INsensitively but NOT case-sensitively (the bite): 0  []
match as written (modifier fires): 5  ['ci-runner-cache', 'test-fixture-vol',
  'tmp-egress-ip', 'tmp-orphan-disk', 'tmp-scratch-vol']
```

**Zero bite.** The eleven capitalised strings are **all cost line-item service labels**, not
resource names, and none begins with an ephemeral prefix in any casing. The AWS `Name`-tag path
that motivated the concern (`fetch_aws.py:442`) yields eight recorded values, **all lowercase**.

### Check 2 — does it cross a band? **Yes, exactly.**

Verified from the constants, not reasoned:

```
CONFIDENCE_STOPPED_COMPUTE_WITH_STORAGE  = 0.6
CONFIDENCE_STOPPED_DATABASE_WITH_STORAGE = 0.6
MODIFIER_EPHEMERAL_NAME                  = 0.1
BAND_MEDIUM_MIN                          = 0.7
compute   without=0.6 -> LOW  | with=0.7 -> MEDIUM
database  without=0.6 -> LOW  | with=0.7 -> MEDIUM
boundary hit exactly? True
```

### The branch taken — and a conflict in the ticket, reported

The ticket gives two branch rules that **conflict for this outcome**: *"If check 1 comes back
negative, **file no row**"* and *"If **either** comes back positive, file the row."* Check 1 is
negative and check 2 is positive.

**Ruled on trigger versus severity.** Check 1 is the trigger; check 2 is the severity. **A row needs
a trigger**, and the trigger is unobserved across every provider in the record — which is exactly the
shape of the three items this cycle excluded (*latent on a hypothetical provider, exhibited by none
of the three*). Filing it would put an unreproducible row beside ten reproducible ones.

**No row filed. The residual is a note under C15**, carrying both results, and carrying what a later
reader needs: reconcile **toward case-folding** if ever reconciled — it can only move candidates
**up** a band, never down — and re-run check 1 before trusting the first report from any provider
whose names arrive capitalised.

---

## 5. Parts 2 and 3 — the filed set, derived

```
G2 markers                     : 11  [N8, N3, D17, D20, N5, N7, D6, P6, P8, P11, P7]
Part 2 (11 minus dropped D5)   : 10  [X4, F2, F3, N8, X5, P8, D16, P2, P11, D12]
G2 remainder (not defect/excl) :  7  [N3, D20, N5, N7, D6, P6, P7]
G3 duplicates to subtract      :  0
EXPECTED filed                 : 17
ACTUALLY filed                 : 17
match: True
```

**BL-114–BL-130.** Ten defect, seven contract consequence. Every row carries its Kind, census item,
contract, what is broken or required, whether it is *observed on a current provider* or *established
from the code*, what it owes, what it costs, and what it collides with.

**Three rows carry a cost statement that is the row's real content**, taken from §Contracts where it
already said so: BL-118's non-ASCII fixture (*"the fixture is the row's real cost"*), BL-126's
signature change across 14 call sites, BL-129's history tree already on disk carrying the old
service names.

**One row owes a check rather than a fix** — BL-120 (D16). The idle-load-balancer rule's correctness
rests on a `tag:` convention no adapter but one emits and no test asserts. The question *"can a load
balancer in active use present with no attachment on the other two adapters?"* is prior to any fix,
and the fix differs completely between the two answers. Proposing one now would be the guess the row
exists to prevent.

**One row cannot be taken alone** — BL-117 (N8). Adding the canonicality validation makes the
sprint's `illegible` arm unreachable, because that arm exists *precisely because the validation is
absent*. That is the chaos-gate shape (BL-107) arriving by another route, and the row says the change
must land with a sprint change in one commit.

---

## 6. Part 4 — BL-074 closed

All five clauses assessed per clause in the row's DONE section, each naming its artifact. One
qualification is stated rather than glossed: **clause 1 offers two arms and two items fit neither**
(D5, operator configuration; R4, an environment dependency), so *"all 54 received one of the two
rulings"* would be false.

The DONE section also records what the row established beyond its own fix — that the §7 promotion
candidate it carried (*a uniqueness claim produced by observation*) is now evidenced **three times
in one lineage**: *"the one seam"* → *"at least three"* → t4b r0's seam predicate over all 54, which
the census denies. Each was a count replaced without re-checking the claim it hung on. Carried to
the m4 close.

---

## 7. Part 5 — the cycle document: five falsifications, not two

Checked rather than assumed, on t4b r1's precedent.

1. **The t4c row's subject** — *"File the defect rows"*; it filed two kinds.
2. **The t4c row's counts** — *"11 rows filed, 3 exclusions recorded"*; it is 17 filed, 3 confirmed,
   1 dropped.
3. **The t4c row's state** — `not started`.
4. **The split rationale's count**, one section down, which also said eleven. Corrected in place with
   the derivation and the reason the two statements diverged.
5. **§Rows filed this cycle** — its table ends at BL-113. A second block was added for t4c's
   seventeen, with its own commit reference; the original table's *"read at agents `009f666`"* header
   was left alone, being true when written.

The t4c row reads `Closed` under the ticket's pre-authorisation, cited in the §Sequence note beside
t4b's — the regress is unchanged, only the ticket differs.

---

## 8. What t4c did not do

- **No implementation.** Every row is filed, none taken. Eight `cloudcost/scripts/` blob hashes
  unchanged.
- **No exclusion authored.** The three were confirmed present, not rewritten.
- **No census, ruling, mapping or contract substance re-opened.**
- **The comment-as-truth-maker question stays carried** to the m4 close, not swept here.
