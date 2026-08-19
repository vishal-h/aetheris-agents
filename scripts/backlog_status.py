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
      (c) `### BL-` inside a fenced code block. Fences are not stripped. There are
          none today (checked at ds t0); if one lands it is segmented as a row.
    The LEGACY-form census in `--census` inherits BL-146's hazard in full and is
    reported as occurrence counts, never as per-row claims, for that reason.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent

# ONE constant for the file's location. t1b relocates it; this is the one-line change.
BACKLOG_MD = REPO_ROOT / "docs" / "backlog-2026-06.md"

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


class Section(NamedTuple):
    """One `### BL-` heading and every line under it, up to the next such heading."""

    ids: tuple[str, ...]
    heading: str
    start: int  # 1-based line number of the heading
    lines: tuple[str, ...]  # the heading line and its body, verbatim

    @property
    def is_title(self) -> bool:
        return bool(TITLE_SUFFIX_RE.search(self.heading))

    def field_hits(self) -> list[tuple[int, str]]:
        """Every canonical field line in the WHOLE section (defeat 3).

        Returns `(offset_from_heading, value)`. Offset 1 is the canonical position.
        """
        hits = []
        for offset, line in enumerate(self.lines):
            m = FIELD_RE.fullmatch(line)
            if m:
                hits.append((offset, m.group(1)))
        return hits


def parse_sections(text: str) -> list[Section]:
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if HEADING_RE.match(line)]
    out = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        heading = lines[i]
        m = ID_PREFIX_RE.match(heading)
        ids = tuple(ID_RE.findall(m.group(1))) if m else tuple(ID_RE.findall(heading[:40]))
        out.append(Section(ids, heading, i + 1, tuple(lines[i:end])))
    return out


class RowStatus(NamedTuple):
    row_id: str
    value: str | None
    problems: tuple[str, ...]


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
        for sec in by_id[row_id]:
            for offset, value in sec.field_hits():
                hits.append((sec, offset, value))
        problems = []
        if not hits:
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
        rows.append(RowStatus(row_id, value, tuple(problems)))
    return rows


def load(path: Path = BACKLOG_MD) -> list[RowStatus]:
    return resolve(parse_sections(path.read_text()))


def census(rows: list[RowStatus]) -> dict[str, int]:
    counts = {v: 0 for v in VOCABULARY}
    for row in rows:
        if row.value in counts:
            counts[row.value] += 1
    return counts


def _cmd_check(path: Path) -> int:
    sections = parse_sections(path.read_text())
    rows = resolve(sections)
    bad = [r for r in rows if r.problems]
    print(f"{path}: {len(sections)} sections, {len(rows)} row ids")
    for row in bad:
        for problem in row.problems:
            print(f"  FAIL  {row.row_id}: {problem}")
    if bad:
        print(f"FAIL: {len(bad)} of {len(rows)} row ids")
        return 1
    print(f"OK: all {len(rows)} row ids carry exactly one field, all in vocabulary")
    return 0


def _cmd_census(path: Path) -> int:
    text = path.read_text()
    sections = parse_sections(text)
    rows = resolve(sections)
    counts = census(rows)
    open_n = counts["OPEN"]
    terminal_n = sum(counts[v] for v in TERMINAL)

    print(f"rows        {len(rows)}")
    for value in VOCABULARY:
        print(f"{value:<12}{counts[value]}")
    print(f"terminal    {terminal_n}   ({', '.join(TERMINAL)})")
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
    ap.add_argument("--file", type=Path, default=BACKLOG_MD)
    args = ap.parse_args(argv)
    if args.check:
        return _cmd_check(args.file)
    return _cmd_census(args.file)


if __name__ == "__main__":
    sys.exit(main())
