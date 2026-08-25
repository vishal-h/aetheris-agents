"""Parser and CLI for the `**Status:**` field in `docs/backlog-2026-06.md`.

Landed at ds t0. The field is one line, at a fixed position — immediately after a
row's title heading — carrying one of three values: `OPEN`, `DONE`, `UNRULED`.
`DONE` is the only terminal value. The field is a **declaration**; the row body
keeps the **record**, and no legacy status expression was removed to make room
for it (ds t0's ADD-never-MOVE rule).

Structured after `scripts/_manifest.py`: the shape the file is allowed to have is
stated here, in one place, because a second derivation over the same file is how
the two status surfaces this ticket exists to collapse came about. Parser and CLI
live in one module because there is exactly one consumer pair — this file's own
`main()` and `tests/test_backlog_status.py` — and `_manifest.py`'s split exists
only because *two* CLIs consume it.

FOUR DEFEATS THIS PARSER HONOURS, each a recorded way a derivation over this file
has already gone wrong:

1.  **Segment on `^### BL-`, never on `^### `.** Two `### ` headings in this file
    are not row headings — a *Worked instance* heading inside BL-041's body and a
    *Pre-implementation handoff* heading inside BL-042's. A segmenter splitting on
    `^### ` truncates both those rows. (BL-151, filed by ds t0.)

2.  **Ids come from the heading's anchored id-list prefix**, so a multi-id heading
    resolves *every* id it names: `### BL-050 + BL-055 + BL-056 — DONE 2026-07-25`
    is one heading and three rows. Anchoring at the prefix is also what keeps
    defeat 1's fix from creating a new defeat — `### Worked instance — BL-025, …`
    names BL-025 in its *text*, and a cardinality rule applied at the wrong anchor
    would mint a spurious BL-025 section out of BL-041's body, which would then
    merge into the real BL-025. Fix and anchor are one thing, not two.
    (BL-150 and `hc-consolidation.md` record the cardinality fact; BL-151 records
    the constraint on parsers, which is what this is.)

3.  **Scan the whole section, never a prefix.** The row format admits a legacy
    `**Status:**` line at an unbounded offset — BL-001's sits nineteen lines below
    its heading, and two derivations reading the `**Size:** · **Priority:**` block
    as "the metadata" concluded the row had none. Scanning the whole section is
    also what makes `exactly one` an assertion rather than a hope: a check that
    only read line+1 could never see a second field. (BL-151, `2026-08-17`.)

4.  **Proof against a quoted disposition.** A row may quote another row's
    disposition in the same bold-marker form a row uses for its own status; that
    is routine and useful, and it once made a status extraction classify the open
    BL-137 as closed (BL-146). Three things defeat it here, and they are
    structural rather than heuristic:
      - `FIELD_RE` is `fullmatch` on the WHOLE line, so `**Status:** DONE` matches
        and `**Status:** Done 2026-07-15 — baseline in …` (the 26 legacy lines)
        does not. The canonical form is a closed three-word line.
      - The pattern is anchored at column 0, so a blockquoted `> **Status:** …`
        (BL-135 carries one) cannot match.
      - `--check` requires the field at OFFSET 1 of the section. A quotation
        elsewhere in a body raises the count to two and the check FAILS LOUDLY,
        which is the correct outcome: a second candidate is a thing to look at,
        never a thing to silently pick between.

    WHAT IT STILL CANNOT DISTINGUISH, stated rather than left to be discovered:
      (a) a genuine field from a verbatim quotation of some other row's heading
          AND canonical field as a two-line block at column 0 — that quotation
          would be segmented as a real row section. Nothing in the file's syntax
          separates the two; only fencing or blockquoting the quotation does, and
          both of those already defeat it.
      (b) a correct value from a wrong one. `DONE` on an open row parses clean.
          The field records what a session declared, and no parser adjudicates it.
      (c) `### BL-` inside a fenced code block. **CLOSED by defeat 5's masking**,
          which strips fences and inline code spans before any structural decision
          (`scan_markup`). Still none in the corpus (re-checked 2026-08-25, both
          files, zero), so the guard is for tomorrow's file rather than today's.
    The LEGACY-form census in `--census` inherits BL-146's hazard in full and is
    reported as occurrence counts, never as per-row claims, for that reason.

5.  **A `**Status:**` line inside a `<details>` block is ARCHIVED TEXT, not a
    field.** A row may preserve its own pre-implementation ticket under a
    `<summary>`; that block's `**Status:**` records what the row declared BEFORE
    the work, and reading it as the row's live status makes an archived block
    speak for the present. Depth is tracked across the parse and BOTH attributions
    are made at DEPTH 0 only:
      - a `### BL-` heading at depth > 0 is **not a row heading**. It belongs to
        the enclosing depth-0 row, exactly as defeat 1's `### Worked instance`
        does. So a preserved ticket does not mint a second section for its id.
      - a `**Status:**` line at depth > 0 is **not a field**. It is reported by
        `field_hits(deep=True)` and never by `field_hits()`.
    Depth is measured AT LINE START — the opens and closes on a line are applied
    after that line is classified — so `<details><summary>…</summary>` opens for
    the lines that follow it and `</details>` is itself read at the inner depth.

    THE STATE THIS CREATES, and it is a real one rather than a corner: a row whose
    ONLY `**Status:**` lines are archived has **no live declaration at all**. That
    is `ARCHIVED-ONLY`, reported by `--check` as a loud NOTE and NOT as a failure —
    see `_cmd_check` for the ruling and its cost. A row with no `**Status:**` line
    at any depth is unchanged: still a hard FAIL.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent

# The row set is the UNION of these two files. t1b split the backlog: terminal rows
# (`**Status:** DONE`) moved to the archive and everything else stayed. **The id is
# the address and the path is never load-bearing**, so every consumer resolves against
# the union and no caller needs to know which side a row is on. Reading only the open
# file would report a real row as absent — a well-formed answer to the wrong question.
BACKLOG_MD = REPO_ROOT / "docs" / "backlog-2026-06.md"
BACKLOG_ARCHIVE_MD = REPO_ROOT / "docs" / "backlog-2026-06-closed.md"
BACKLOG_FILES = (BACKLOG_MD, BACKLOG_ARCHIVE_MD)

# The closed vocabulary. DONE is the only terminal value; UNRULED is deliberately
# NOT terminal — a row the arbiter has not settled has an open remainder and must
# not archive at t1b.
VOCABULARY = ("OPEN", "DONE", "UNRULED")
TERMINAL = ("DONE",)

# Defeat 1: the row-heading anchor. `^### BL-` and nothing wider.
HEADING_RE = re.compile(r"^### BL-\d+")

# Defeat 2: the id-list prefix. Ids are read from the heading text BEFORE the em
# dash, so `### BL-050 + BL-055 + BL-056 — DONE …` yields three and
# `### Worked instance — BL-025, …` yields none (it is not a heading at all, per
# HEADING_RE, and this is the second line of defence if that ever changes).
ID_PREFIX_RE = re.compile(r"^### ((?:BL-\d+)(?:\s*\+\s*BL-\d+)*)\s*—")
ID_RE = re.compile(r"BL-\d+")

# Defeat 4: fullmatch, column-anchored, closed value set.
FIELD_RE = re.compile(r"\*\*Status:\*\* (%s)" % "|".join(VOCABULARY))

# Defeat 5: `<details>` depth. Counted per OCCURRENCE, not per line, because
# `<details><summary>…</summary>` is one line carrying one open, and a line may in
# principle carry a matched pair. `<details` unanchored matches the attribute form
# `<details open>` as well as the bare tag.
DETAILS_OPEN_RE = re.compile(r"<details\b")
DETAILS_CLOSE_RE = re.compile(r"</details\s*>")

# …and defeat 5's own defeat, found the day it landed. THIS FILE IS FULL OF PROSE
# ABOUT ITS OWN MARKUP. The first row filed after depth tracking landed wrote the
# word `<details>` inside a code span, in a sentence explaining depth tracking; the
# scanner read it as a real tag, opened a depth that never closed, and SIXTY-FOUR
# row headings after that line stopped existing. `--check` reported 45 sections
# where there were 109 and exited 0 — a silent wrong answer produced by the fix for
# a silent wrong answer, in the commit that introduced it.
#
# So markup is read only where markup can occur: fenced blocks and inline code
# spans are MASKED before any structural decision. A document that discusses a tag
# must be able to name it. This also closes, for `<details>`, the hole the defeat-4
# note records as (c) — and closes it for `### BL-` and for the field line too, at
# no cost: the corpus contains ZERO of either inside a fence, measured at the
# commit that added this, so the widening is a no-op on today's file and a guard
# for tomorrow's.
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
CODE_SPAN_RE = re.compile(r"(?P<t>`+)(?:(?!(?P=t)).)*?(?P=t)")

# A row's TITLE section carries the issue-ref suffix `(#42)` / `(#TBD)`; a CLOSURE
# section appended to an already-filed row does not. The field goes on the title
# section only, so that `exactly one per id` holds across the 18 closure sections
# (which between them name 20 ids).
TITLE_SUFFIX_RE = re.compile(r"\(#[^)]*\)$")

# Legacy expressions, for --census only. Occurrence counts, never per-row claims.
LEGACY_FORMS = {
    "heading word": re.compile(
        r"^### BL-[^—]*— *(DONE|CLOSED|SUPERSEDED|WONTFIX|OPEN)"
    ),
    "body **Status:** line": re.compile(r"^\*\*Status:\*\*"),
    "bold **DONE …** paragraph": re.compile(r"^\*\*(DONE|CLOSED) "),
    "on the Size/Kind line": re.compile(
        r"^\*\*(Size|Kind):\*\*.*\*\*(DONE|CLOSED|OPEN)"
    ),
}


def scan_markup(lines) -> tuple[list[int], list[bool]]:
    """`(details_depth_at_line_start, is_inside_a_fenced_block)` per line.

    One pass, because the two facts are read from the same state and a second
    traversal is a second derivation that would drift from this one.

    A fence line is itself marked in-fence, so the delimiter can never be mistaken
    for content. A fence closes only on its OWN character (``` does not close ~~~),
    which is the CommonMark rule and the one that keeps a shell block quoting a
    tilde from silently ending the block.
    """
    depths, in_fence = [], []
    depth, fence_char = 0, None
    for line in lines:
        m = FENCE_RE.match(line)
        if m:
            char = m.group(1)[0]
            if fence_char is None:
                fence_char = char
            elif char == fence_char:
                fence_char = None
            depths.append(depth)
            in_fence.append(True)
            continue
        depths.append(depth)
        in_fence.append(fence_char is not None)
        if fence_char is not None:
            continue                      # markup inside a fence is text, not markup
        masked = CODE_SPAN_RE.sub("", line)
        depth += len(DETAILS_OPEN_RE.findall(masked))
        depth -= len(DETAILS_CLOSE_RE.findall(masked))
        if depth < 0:
            depth = 0
    return depths, in_fence


def details_depths(lines) -> list[int]:
    """Depth AT LINE START for each line — the reading both attributions use.

    A line's own opens and closes are applied *after* it is classified, so
    `<details><summary>…</summary>` is itself at the outer depth and opens for what
    follows, while `</details>` is read at the inner depth and closes after. This is
    the one ordering that makes a preserved ticket's heading and field both inner
    while the block's own delimiters stay attributable to the row that wrote them.

    Depth is clamped at 0: an unbalanced `</details>` degrades to "still at the
    top level" rather than driving the count negative and turning every later line
    into a phantom field. Malformed markup must not silently promote archived text.
    """
    return scan_markup(lines)[0]


class Section(NamedTuple):
    """One `### BL-` heading and every line under it, up to the next such heading."""

    ids: tuple[str, ...]
    heading: str
    start: int  # 1-based line number of the heading
    lines: tuple[str, ...]  # the heading line and its body, verbatim
    # Which file the section was read from, for the PLACEMENT assertion below.
    # `None` when the caller parsed a bare string (every fixture test does), and
    # the placement check is inert for those — it is an invariant about the two
    # real backlog files, not a property of arbitrary text.
    path: Path | None = None

    @property
    def is_title(self) -> bool:
        return bool(TITLE_SUFFIX_RE.search(self.heading))

    def field_hits(self, deep: bool = False) -> list[tuple[int, str]]:
        """Canonical field lines in the WHOLE section (defeat 3), at ONE depth.

        Returns `(offset_from_heading, value)`. Offset 1 is the canonical position.

        `deep=False` (the default, and what every caller that resolves a row uses)
        returns the DEPTH-0 fields — the row's live declaration. `deep=True`
        returns the fields inside `<details>` — archived text, reported so that a
        row with no live field can be described rather than merely failed
        (defeat 5). The two sets are disjoint by construction; no caller merges
        them, and nothing in this module treats a deep hit as a value.

        A section always begins at depth 0 — `parse_sections` recognises headings
        nowhere else — so depth over `self.lines` is measured from 0 with no state
        carried in from the file.
        """
        depths, in_fence = scan_markup(self.lines)
        hits = []
        for offset, line in enumerate(self.lines):
            if in_fence[offset]:
                continue            # a field line quoted in a code block is an example
            inside = depths[offset] > 0
            if inside != deep:
                continue
            m = FIELD_RE.fullmatch(line)
            if m:
                hits.append((offset, m.group(1)))
        return hits


def parse_sections(text: str, path: Path | None = None) -> list[Section]:
    lines = text.split("\n")
    depths, in_fence = scan_markup(lines)
    # Defeat 5: a `### BL-` heading inside `<details>` is a preserved ticket's
    # heading, not a row heading. It stays inside the enclosing depth-0 section.
    # A heading inside a FENCE is not a heading at all — it is an example of one.
    # HEADING_RE is matched against the ORIGINAL line, never the masked one: the
    # mask exists to decide *whether* a line is markup, and mangling a heading's
    # own text to answer that would corrupt the ids and title suffix read from it.
    starts = [
        i for i, line in enumerate(lines)
        if HEADING_RE.match(line) and depths[i] == 0 and not in_fence[i]
    ]
    out = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        heading = lines[i]
        m = ID_PREFIX_RE.match(heading)
        ids = tuple(ID_RE.findall(m.group(1))) if m else tuple(ID_RE.findall(heading[:40]))
        out.append(Section(ids, heading, i + 1, tuple(lines[i:end]), path))
    return out


class RowStatus(NamedTuple):
    row_id: str
    value: str | None
    problems: tuple[str, ...]
    # Defeat 5. A NOTE is something a reader must be told and a gate must not block
    # on; a PROBLEM fails `--check`. The two are separate fields rather than one
    # list with a severity prefix, so no caller can accidentally count a note as a
    # failure by reading the wrong attribute.
    notes: tuple[str, ...] = ()
    # How many DEPTH-0 fields the row actually carries. Recorded rather than
    # inferred from `value`, because `value` is `None` for both "two fields" and
    # "no live field" and a consumer comparing readings must be able to tell them
    # apart. `_depth_blind_reading` in the tests compares against exactly this.
    n_fields: int = 0

    @property
    def archived_only(self) -> bool:
        """No live field, but at least one preserved inside `<details>`."""
        return self.value is None and any(
            n.startswith("ARCHIVED-ONLY") for n in self.notes
        )


def resolve(sections: list[Section]) -> list[RowStatus]:
    """Merge every section a row id owns and resolve that id's single field.

    Merging is the point: an id's field may live on any section it owns, and the
    `exactly one` assertion is over the MERGED set, not per section.
    """
    by_id: dict[str, list[Section]] = {}
    for sec in sections:
        for row_id in sec.ids:
            by_id.setdefault(row_id, []).append(sec)

    rows = []
    for row_id in sorted(by_id, key=lambda s: int(s.split("-")[1])):
        hits = []
        deep_hits = []
        for sec in by_id[row_id]:
            for offset, value in sec.field_hits():
                hits.append((sec, offset, value))
            for offset, value in sec.field_hits(deep=True):
                deep_hits.append((sec, offset, value))
        problems = []
        notes = []
        if not hits and deep_hits:
            # Defeat 5's new state. NOT a failure — see `_cmd_check`.
            where = ", ".join(f"{s.start + o}" for s, o, _ in deep_hits)
            values = "/".join(v for _, _, v in deep_hits)
            notes.append(
                f"ARCHIVED-ONLY: no depth-0 **Status:** field; "
                f"{len(deep_hits)} inside <details> (line {where}, `{values}`) — "
                f"archived text, which is not a live declaration"
            )
        elif not hits:
            problems.append("no **Status:** field")
        elif len(hits) > 1:
            where = ", ".join(f"{s.start + o}" for s, o, _ in hits)
            problems.append(f"{len(hits)} **Status:** fields (lines {where})")
        for sec, offset, _ in hits:
            if offset != 1:
                problems.append(
                    f"field at line {sec.start + offset} is offset {offset} "
                    f"from its heading, not 1"
                )
            if not sec.is_title:
                problems.append(
                    f"field on a closure section (`{sec.heading[:48]}…`), "
                    f"not the row's title section"
                )
        value = hits[0][2] if len(hits) == 1 else None
        problems.extend(_placement_problems(row_id, value, hits))
        rows.append(
            RowStatus(row_id, value, tuple(problems), tuple(notes), len(hits))
        )
    return rows


# The ARCHIVE INVARIANT, added after `5721718` broke it: a row is in the closed
# file **iff** its title section carries a terminal value. t1b split the backlog on
# exactly this rule and nothing asserted it afterwards, so two rows were marked DONE
# and left in the open file, and every gate passed — the vocabulary check reads the
# VALUE and was blind to the FILE.
#
# THIS DOES NOT MAKE THE PATH LOAD-BEARING. The module docstring's rule — *the id is
# the address and the path is never load-bearing* — governs how a CONSUMER resolves a
# row, and it is unchanged: every consumer still reads the union and no caller asks
# which side a row is on. This is a hygiene invariant about the two files, checked
# here because this module is the only thing that already parses both.
#
# UNRULED IS NOT TERMINAL and belongs in the open file. `TERMINAL` is the authority,
# not a second list — a row the arbiter has not settled has an open remainder.
def _placement_problems(row_id, value, hits) -> list[str]:
    """Empty unless a row's title section sits on the wrong side of the split."""
    title = next((sec for sec, _, _ in hits if sec.is_title), None)
    # Inert for a bare string, and for any file that is not one of the two real
    # backlog files — `--file <fixture>` must not be judged against a split it is
    # not part of.
    if title is None or title.path is None:
        return []
    try:
        where = title.path.resolve()
    except OSError:                                       # pragma: no cover
        return []
    if where not in (BACKLOG_MD.resolve(), BACKLOG_ARCHIVE_MD.resolve()):
        return []
    in_archive = where == BACKLOG_ARCHIVE_MD.resolve()
    should_be_archived = value in TERMINAL
    if should_be_archived and not in_archive:
        return [
            f"`**Status:** {value}` is terminal, but the row is in "
            f"{BACKLOG_MD.name} — a terminal row belongs in {BACKLOG_ARCHIVE_MD.name}"
        ]
    if in_archive and not should_be_archived:
        return [
            f"`**Status:** {value}` is not terminal, but the row is in "
            f"{BACKLOG_ARCHIVE_MD.name} — only {', '.join(TERMINAL)} archives"
        ]
    return []


def parse_files(paths) -> list[Section]:
    """Sections from every file in the union, concatenated in the given order."""
    out = []
    for path in paths:
        out.extend(parse_sections(path.read_text(), path))
    return out


def load(paths=BACKLOG_FILES) -> list[RowStatus]:
    if isinstance(paths, Path):
        paths = (paths,)
    return resolve(parse_files(paths))


def census(rows: list[RowStatus]) -> dict[str, int]:
    counts = {v: 0 for v in VOCABULARY}
    for row in rows:
        if row.value in counts:
            counts[row.value] += 1
    return counts


def archived_only(rows: list[RowStatus]) -> list[RowStatus]:
    """Defeat 5's state. Its size is what makes the census partition exhaustive."""
    return [r for r in rows if r.archived_only]


def _cmd_check(paths) -> int:
    sections = parse_files(paths)
    rows = resolve(sections)
    bad = [r for r in rows if r.problems]
    noted = [r for r in rows if r.notes]
    for path in paths:
        n = len(parse_sections(path.read_text()))
        print(f"{path}: {n} sections")
    print(f"union: {len(sections)} sections, {len(rows)} row ids")
    # NOTES FIRST, and unconditionally — including on a failing run, where a note
    # is often the thing that explains the failure. A note printed only on the
    # green path is a note nobody reads on the day it matters.
    for row in noted:
        for note in row.notes:
            print(f"  NOTE  {row.row_id}: {note}")
    for row in bad:
        for problem in row.problems:
            print(f"  FAIL  {row.row_id}: {problem}")
    if bad:
        print(f"FAIL: {len(bad)} of {len(rows)} row ids")
        return 1
    if noted:
        # THE RULING, stated where it takes effect. ARCHIVED-ONLY is reported and
        # does NOT fail, and the reason is that this check's own fix created the
        # state: before defeat 5 the parser read a preserved ticket's `**Status:**`
        # as the row's live value, so such a row reported a well-formed WRONG
        # answer and passed. Turning the corrected reading straight into a FAIL
        # would make the parser fix and a live-corpus repair one landing, which is
        # the coupling agents `CLAUDE.md` §Definition of done forbids — *before
        # making a soft failure hard, enumerate what else that gate holds*. Here
        # the enumeration is exact and cheap: the census over the corpus finds ONE
        # row in this state.
        #
        # THE COST, named rather than left implicit: while this is a NOTE, a row
        # can lose its live declaration and `--check` still exits 0. That is a
        # real hole and it is meant to be temporary — promotion to FAIL is a
        # tracked row, to be taken once the corpus population is zero.
        print(
            f"NOTE: {len(noted)} of {len(rows)} row ids carry an advisory above. "
            f"Advisories are reported, never blocking; see `_cmd_check`."
        )
    # The count is `len(rows) - len(noted)`, never `len(rows)`: an ARCHIVED-ONLY row
    # does NOT carry a field, and a summary line that says it does is the exact
    # Silent-wrong-answer this check exists to remove — well-formed, reassuring,
    # and false about the one row anybody is reading the line to learn about.
    carried = len(rows) - len(noted)
    print(
        f"OK: {carried} of {len(rows)} row ids carry exactly one field, all in "
        f"vocabulary, and each is on the correct side of the split "
        f"({'/'.join(TERMINAL)} archives, everything else stays open)"
        + (f"; the remaining {len(noted)} are ARCHIVED-ONLY, noted above and not "
           f"blocking" if noted else "")
    )
    return 0


def _cmd_census(paths) -> int:
    text = "\n".join(p.read_text() for p in paths)
    sections = parse_files(paths)
    rows = resolve(sections)
    counts = census(rows)
    open_n = counts["OPEN"]
    terminal_n = sum(counts[v] for v in TERMINAL)
    archived_n = len(archived_only(rows))

    w = 14  # widest label is `ARCHIVED-ONLY` (13) + 1
    print(f"{'rows':<{w}}{len(rows)}")
    for value in VOCABULARY:
        print(f"{value:<{w}}{counts[value]}")
    # Printed always, including as 0. A line that appears only when non-zero is a
    # line whose absence a reader cannot distinguish from the state not existing,
    # and 0 here is the assertion that every row has a live declaration.
    print(f"{'ARCHIVED-ONLY':<{w}}{archived_n}   (no depth-0 field; only <details> text)")
    print(f"{'terminal':<{w}}{terminal_n}   ({', '.join(TERMINAL)})")
    print(f"{'partition':<{w}}{sum(counts.values())} + {archived_n} = {len(rows)}"
          f"   ({'OK' if sum(counts.values()) + archived_n == len(rows) else 'BROKEN'})")
    print()
    print(f"THE OPEN SET IS {open_n}.")
    print("  python3 scripts/backlog_status.py --census")
    print()
    print("legacy expressions, OCCURRENCES not rows (BL-146: a body may quote another")
    print("row's disposition, and no pattern over this file can tell the two apart):")
    for name, pattern in LEGACY_FORMS.items():
        n = sum(1 for line in text.split("\n") if pattern.match(line))
        print(f"  {n:>4}  {name}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="exactly-one-field assertion")
    mode.add_argument("--census", action="store_true", help="the open set, as a number")
    # Repeatable, and defaulting to the UNION. A single `--file` still works for
    # testing one side in isolation; the default is never one side.
    ap.add_argument("--file", type=Path, action="append", dest="files")
    args = ap.parse_args(argv)
    paths = tuple(args.files) if args.files else BACKLOG_FILES
    if args.check:
        return _cmd_check(paths)
    return _cmd_census(paths)


if __name__ == "__main__":
    sys.exit(main())
