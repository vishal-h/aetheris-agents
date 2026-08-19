# ds t0 — the backlog gets a status field (implementation notes)

`2026-08-19, at agents 1deb832 → this commit / aetheris 8eb960d. Every path, line number, command
and figure below is measured at that pair unless it names another. THE HARNESS IS READ ONLY for
this ticket and its HEAD is unchanged at both ends. Absolute paths are normalised to ~ throughout.
Written for the next round in this arc — t1a and t1b — per harness CLAUDE.md, "an
implementation-notes file is read by the next round in its arc or by nobody".`

Milestone document: `docs/milestones/ds-milestone.md` §t0, which is the authority. Issue
`vishal-h/aetheris-agents#75`.

---

## Trial verdict A — was the Project consulted, and for what

**No. It was not consulted, for anything.**

Not once, at no point in either stage of this ticket. Every decision here came from the milestone
document, the two `CLAUDE.md` files, the backlog rows themselves, `hc-consolidation.md`'s R23/R26,
and the ticket prompt. Nothing was read out of the Project and no act was taken to keep it current.

Recorded as `no` rather than left out, and not remedied by a consultation staged for the record:
criterion 5's own ground is that a criterion whose evidence is nobody's recollection reports clean
in the one state it exists to catch, and consulting the Project for form's sake would make verdict
A unfalsifiable — which is the outcome the instrument exists to prevent. `no` is a stated and
expected value of this line.

---

## What landed

| artifact | change | note |
|---|---|---|
| `docs/milestones/ds-milestone.md` §t0 | section replaced as a unit | `**Issue.**` untouched; no other section touched |
| `docs/backlog-2026-06.md` | **270 insertions, 0 deletions** | the field on 165 rows, the retirement marker, three dated appends |
| `scripts/backlog_status.py` | new | parser + `--check` / `--census` |
| `tests/test_backlog_status.py` | new | 14 tests, no marker, inside the whole-suite gate |

**The field.** One line, `**Status:** <VALUE>`, at offset 1 from a row's **title** heading —
before `**Size:**`/`**Kind:**`, matching the file's existing spacing exactly. The 18 closure
sections get none, which is what keeps *exactly one per row id* true across the 20 ids those 18
sections name. Position uniformity was **checked before the migration was written**: all 165 title
sections have a metadata line immediately after the heading, no blanks, so S2b's STOP condition
never fired.

**Vocabulary.** `OPEN`, `DONE`, `UNRULED`. `DONE` is the only terminal value. `CLOSED` merges into
`DONE`; `folded` maps to `DONE`; absence means `OPEN`. **`UNRULED` is non-terminal** — a row with
an open remainder must not archive at t1b, which is the only reason the value exists rather than
being rounded to either neighbour. `OPEN` was adopted **with zero precedent in the file**: 0
heading-form `OPEN` and 0 `**Status:** Open`, against a positive control of 19 and 26 for the
`DONE`/`Done` variants of the same two patterns.

**ADD, never MOVE.** No legacy expression was removed, reworded or relocated — 0 deletions, which
is the invariant that makes the claim checkable rather than asserted.

---

## The assignment: totals matched, composition did not

**60 `DONE` / 2 `UNRULED` / 103 `OPEN`, over 165 rows — exactly the ratified prediction**, so the
ticket's STOP condition did not fire. The prediction's stated *basis* is wrong in a way that
changes no verdict and is recorded so t1b does not inherit it.

The prompt states 60 `DONE` as *"the 57 derivable, plus BL-027, BL-030, BL-135"*. The derivation
returns **61 row ids carrying a legacy expression**; two of those (BL-047, BL-048) are the ratified
`UNRULED`, leaving **59 derivable `DONE`**, and **BL-135 alone** needs an arbiter attribution:

- **BL-027 is derivable** — the on-the-Size-line form, `**Size:** S · **Priority:** medium —
  **DONE 2026-07-23 (folded into BL-025)**`, inside its own row.
- **BL-030 is derivable** — the body-`**Status:**`-line form, `**Status:** Done 2026-07-26.
  Harness: cli/commands/fork.ex emits the run id …`.
- **BL-135 is genuinely not derivable** — both its markers are **blockquoted**
  (`> **Status:** folded`, `> **[FOLDED into BL-075 …`), so every column-0 pattern correctly
  declines them. It is `DONE` by the ratified `folded` → `DONE` mapping.

59 + 1 = 60. The arbiter's ruling stands as ruled; only two of the three rows it names needed it.

---

## The parser, and the four defeats it is built around

`scripts/backlog_status.py`. Its module docstring is the executable statement of BL-151's new
constraint-set entry, and the two are meant to be read together.

1. **Anchor** — `HEADING_RE = ^### BL-\d+`, never `^### `. Two `### ` headings in the file are not
   row headings and sit inside BL-041's and BL-042's bodies; a `^### ` segmenter truncates both.
2. **Cardinality** — `ID_PREFIX_RE` reads the id list *before the em dash*, so
   `### BL-050 + BL-055 + BL-056 — DONE …` resolves three ids, and `resolve()` merges every section
   an id owns. **Anchoring at the prefix is also what stops the fix for defeat 1 becoming a new
   defeat**: `### Worked instance — BL-025, …` names an id in its *text*, and a cardinality rule at
   a `^### ` anchor would mint a spurious section out of BL-041's body that then merges into the
   real BL-025.
3. **Unbounded offset** — `Section.field_hits()` scans every line of the section, which is also what
   makes *exactly one* an assertion rather than a hope.
4. **Quoted disposition (BL-146)** — three structural defences: `fullmatch` on the whole line (so
   the 26 legacy `**Status:** Done 2026-07-15 — …` lines cannot match the canonical three-word
   form), column-0 anchoring (so BL-135's blockquoted line cannot match), and `--check` requiring
   offset 1, so a quotation elsewhere raises the count to two and **fails loudly**. Verified
   against BL-146's own two named traps — BL-137 and BL-014 both correctly absent from the derived
   set, positive control BL-001 and BL-132 both present.

**What it still cannot distinguish**, stated in the docstring rather than left to be found: a
genuine field from a verbatim column-0 quotation of another row's heading *and* field; a correct
value from a wrong one; and `### BL-` inside a fenced code block (0 today, positive control 100
fence markers). **The legacy census in `--census` inherits BL-146's hazard in full** and is
reported as occurrence counts, never as per-row claims.

---

## Deviations, stated

- **Parser and CLI in one module**, where the prompt asked for `_manifest.py`'s split.
  `_manifest.py` is split *because two CLIs consume it*; here there is one consumer pair, so the
  module follows `_manifest.py`'s **shape** — permitted form stated once in a docstring, a
  `NamedTuple`, named regex constants — rather than its file count. **A second consumer is the
  trigger to split.**
- **The migration generator is not committed.** It ran once, onto a copy; the prompt names two new
  files and `Do not generate` binds the rest. It is quoted whole in the review packet, which is
  where it is reproducible from.
- **One sentence was carried back into the replaced §t0 section** after the first cut dropped it —
  *"Rows whose status cannot be derived unambiguously are adjudicated by the arbiter, never
  guessed."* Still true, and lost by a replacement rather than by a decision. Caught by reading the
  deleted lines against the replacement, not by the diff.

---

## Uncertain, and what is owed

- **The in-file citation population is not derivable and the milestone section says so.** A bare
  `` `:NNN` `` anchor binds to whichever file was last named, and in this file that is usually not
  this file. 448 `:NNN`-shaped tokens; 169 bare backtick anchors; 154 on lines naming no other
  file, which is an **upper bound and a loose one** — a continuation's antecedent can be on a
  previous line. The external population *is* derivable: 31 tokens on 30 lines across 17 files.
  The prompt's figures (33/18/317) do not reproduce; it marked them for re-derivation.
- **This commit staled every absolute line-number citation into the backlog**, and t1b's relocation
  will stale the path-based ones. The cost is deliberately taken once. **Nothing is re-pinned by
  this ticket**, and the re-pinning belongs to whichever ticket moves the file.
- **BL-146 stays open.** The field is a structural answer to its question *for the new field only*;
  every derivation over the legacy expressions still inherits the hazard.
- **BL-145 stays open.** The marker at `## Suggested order` is a pointer, not the execution.
- **For t1b, filed on BL-151:** `sprint.sh`'s `expected_fail` / `known_red_healed` — the backlog's
  one programmatic parser — have **zero call sites** at harness `8eb960d` (positive control: `fail`
  94, `ok` 151, `info` 137). t1b must edit `sprint.sh` or break it, and it does so against a gate
  whose row-existence arm has never run.

---

## Anchors for the next round

- The field's definition and vocabulary: `docs/milestones/ds-milestone.md` §t0.
- The predicate t1b turns on: `backlog_status.TERMINAL`, and `bs.load()` for the per-row values.
- **The one line t1b changes when it relocates the file:** `backlog_status.BACKLOG_MD`.
- The four parser constraints as a filed set: BL-151's `2026-08-19` entry.
- What t0 did to BL-150's own census: BL-150's `2026-08-19` entry.
