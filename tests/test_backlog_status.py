"""Tests for scripts/backlog_status.py — ds t0's `**Status:**` field and its check.

**No marker.** This does its work and passes in a fresh clone at this commit, offline,
with no sibling repository present and nothing installed beyond the declared
dependencies: it reads one tracked file and calls one tracked module. By `pytest.ini`'s
own criterion that is not `integration`, so it runs inside the whole-suite gate —
`python3 -m pytest -q -m "not integration and not dormant"` from the repo root — for
free, which is the whole reason ds t0's done-check is a test rather than a standalone
script (BL-150's `2026-08-17` off-territory-gate entry).

TWO KINDS OF TEST HERE, and they are kept apart on purpose:

  * **Over the real backlog** — the assertions that are the ticket's done-check. Every
    row id carries exactly one field, every value is in the vocabulary, and the census
    figure this module derives equals the CLI's. The census comparison is derived on
    BOTH sides and compared; **no figure in this file is a hardcoded literal**, which is
    BL-164's class exactly — a test that hard-codes a value the code derives goes red
    when the derivation moves, not when the code breaks. The backlog gains and loses
    rows continuously; a literal here would be wrong within the week.

  * **Over synthetic fixtures** — the parser unit tests, one per defeat. They are
    synthetic because each defeat needs a shape stated in three lines, and because a
    unit test pinned to a real row is a citation that decays (BL-151's unbounded-offset
    entry is about BL-001, whose line number has already moved once).

**The mutation test is in `test_check_fails_when_a_field_is_removed`** — owed by the
author of any check, per harness `CLAUDE.md` **Silent-wrong-answer**. It runs on a
FIXTURE, never on the real file: a mutation on a tracked file restored by anything other
than a working-copy backup is how the export boundary destroyed an uncommitted edit
(agents `CLAUDE.md` §Learning — the 2026-08-16 export boundary). Here there is nothing
to restore, because nothing real was touched.
"""

import subprocess
import sys
from pathlib import Path

import pytest

import backlog_status as bs

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Synthetic fixtures — one per defeat, each the smallest shape that shows it
# ---------------------------------------------------------------------------

# Defeat 1: a `### ` heading that is not a row heading, inside a row's body. A
# segmenter splitting on `^### ` truncates BL-900 and loses its field.
FIXTURE_INNER_HEADING = """\
### BL-900 — a row with a non-row heading in its body (#TBD)
**Status:** OPEN
**Size:** S · **Priority:** low

### Worked instance — BL-901, 2026-07-23

Body text that belongs to BL-900.

### BL-902 — the next real row (#TBD)
**Status:** DONE
**Size:** S · **Priority:** low
"""

# Defeat 2: one heading, three rows.
FIXTURE_MULTI_ID = """\
### BL-910 — first (#TBD)
**Status:** DONE
**Size:** S · **Priority:** low

### BL-911 — second (#TBD)
**Status:** DONE
**Size:** S · **Priority:** low

### BL-912 — third (#TBD)
**Status:** DONE
**Size:** S · **Priority:** low

### BL-910 + BL-911 + BL-912 — DONE 2026-07-25 (one reorder, three rows)

The closure section carries no field; the three title sections above do.
"""

# Defeat 3: the field is at offset 1, but a LEGACY status line sits far below it.
# A parser reading only the metadata prefix would miss the legacy line; one reading
# only line+1 could never assert `exactly one`.
FIXTURE_DEEP_LEGACY = """\
### BL-920 — a row whose legacy status is nineteen lines down (#TBD)
**Status:** DONE
**Size:** S · **Priority:** low

Prose.

Prose.

Prose.

**Status:** Done 2026-07-15 — the legacy line, kept by ADD-never-MOVE.
"""

# Defeat 4: a quoted disposition, in three of the forms the file actually uses.
FIXTURE_QUOTED = """\
### BL-930 — a row that quotes another row's disposition (#TBD)
**Status:** OPEN
**Size:** S · **Priority:** low

> **Status:** folded. Track the defect on **BL-075**.

**Status:** Done 2026-07-15 — a legacy line, not the canonical form.

The row it quotes said `**Status:** DONE` inline, which is not a whole line.
"""

# A second canonical field, at column 0, elsewhere in the body. The parser MUST NOT
# silently pick one — it must fail.
FIXTURE_TWO_FIELDS = """\
### BL-940 — a row carrying two canonical fields (#TBD)
**Status:** OPEN
**Size:** S · **Priority:** low

Someone quoted another row verbatim:

**Status:** DONE
"""

FIXTURE_BAD_VALUE = """\
### BL-950 — a row with a value outside the vocabulary (#TBD)
**Status:** CLOSED
**Size:** S · **Priority:** low
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "backlog.md"
    path.write_text(text)
    return path


# ---------------------------------------------------------------------------
# Parser unit tests — the four defeats
# ---------------------------------------------------------------------------


def test_defeat_1_segments_on_bl_headings_only(tmp_path):
    """`### Worked instance — …` is not a row heading and does not end BL-900."""
    path = _write(tmp_path, FIXTURE_INNER_HEADING)
    sections = bs.parse_sections(path.read_text())

    assert [s.ids for s in sections] == [("BL-900",), ("BL-902",)]
    # BL-900's section must still contain the inner heading and the body under it —
    # a `^### ` segmenter would have cut both away.
    assert "### Worked instance" in "\n".join(sections[0].lines)
    assert "Body text that belongs to BL-900." in "\n".join(sections[0].lines)

    rows = bs.resolve(sections)
    assert {r.row_id: r.value for r in rows} == {"BL-900": "OPEN", "BL-902": "DONE"}
    assert all(not r.problems for r in rows)


def test_defeat_1b_inner_heading_does_not_mint_a_row(tmp_path):
    """The fix for defeat 1 must not create defeat 2 at the wrong anchor.

    `### Worked instance — BL-901, …` names BL-901 in its TEXT. A cardinality rule
    applied at a `^### ` anchor would mint a spurious BL-901 section out of BL-900's
    body, which would then merge into any real BL-901.
    """
    path = _write(tmp_path, FIXTURE_INNER_HEADING)
    rows = bs.resolve(bs.parse_sections(path.read_text()))
    assert "BL-901" not in {r.row_id for r in rows}


def test_defeat_2_a_multi_id_heading_resolves_every_id(tmp_path):
    path = _write(tmp_path, FIXTURE_MULTI_ID)
    sections = bs.parse_sections(path.read_text())

    closure = sections[-1]
    assert closure.ids == ("BL-910", "BL-911", "BL-912")
    assert not closure.is_title

    rows = bs.resolve(sections)
    assert {r.row_id for r in rows} == {"BL-910", "BL-911", "BL-912"}
    # Each id owns two sections and still resolves to exactly one field.
    assert all(r.value == "DONE" and not r.problems for r in rows)


def test_defeat_3_scans_the_whole_section_not_a_prefix(tmp_path):
    """A legacy line far below the metadata block is inside the scanned span."""
    path = _write(tmp_path, FIXTURE_DEEP_LEGACY)
    section = bs.parse_sections(path.read_text())[0]

    assert section.lines.index("**Status:** DONE") == 1
    deep = [i for i, l in enumerate(section.lines) if l.startswith("**Status:** Done")]
    assert deep and deep[0] > 5, deep      # the legacy line is far below the prefix
    # …and it is NOT a canonical field, so the row still has exactly one.
    assert section.field_hits() == [(1, "DONE")]
    assert not bs.resolve([section])[0].problems


def test_defeat_4_a_quoted_disposition_is_not_the_row_s_status(tmp_path):
    path = _write(tmp_path, FIXTURE_QUOTED)
    rows = bs.resolve(bs.parse_sections(path.read_text()))

    assert len(rows) == 1
    assert rows[0].value == "OPEN"       # not DONE, not folded
    assert not rows[0].problems


def test_defeat_4b_a_second_canonical_field_fails_loudly(tmp_path):
    """Two candidates is a thing to look at, never a thing to silently pick between."""
    path = _write(tmp_path, FIXTURE_TWO_FIELDS)
    rows = bs.resolve(bs.parse_sections(path.read_text()))

    assert rows[0].value is None
    assert any("2 **Status:** fields" in p for p in rows[0].problems)
    assert bs.main(["--check", "--file", str(path)]) == 1


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


def test_an_unknown_value_is_an_error_never_a_silent_pass(tmp_path):
    """`CLOSED` merges into `DONE`; it is not itself a value."""
    path = _write(tmp_path, FIXTURE_BAD_VALUE)
    rows = bs.resolve(bs.parse_sections(path.read_text()))

    assert rows[0].value is None
    assert rows[0].problems == ("no **Status:** field",)
    assert bs.main(["--check", "--file", str(path)]) == 1


def test_done_is_the_only_terminal_value():
    """UNRULED is non-terminal by ratification: an open remainder must not archive."""
    assert bs.TERMINAL == ("DONE",)
    assert set(bs.VOCABULARY) == {"OPEN", "DONE", "UNRULED"}
    assert "UNRULED" not in bs.TERMINAL


# ---------------------------------------------------------------------------
# THE MUTATION TEST — owed by the author, run on a fixture and never on the real file
# ---------------------------------------------------------------------------


def test_check_fails_when_a_field_is_removed(tmp_path):
    """Break it, watch it fail, put it back, watch it pass — and verify the restore.

    Both halves are observations, not one action (harness `CLAUDE.md`, *the mutation
    test has two halves and the restore is the second one*). The restore is checked by
    the mutated string's absence, not assumed from a green run.
    """
    path = _write(tmp_path, FIXTURE_MULTI_ID)
    original = path.read_text()

    assert bs.main(["--check", "--file", str(path)]) == 0          # green before

    mutated = original.replace("### BL-911 — second (#TBD)\n**Status:** DONE\n",
                               "### BL-911 — second (#TBD)\n", 1)
    assert mutated != original                                      # the mutation landed
    path.write_text(mutated)

    rows = bs.resolve(bs.parse_sections(path.read_text()))
    by_id = {r.row_id: r for r in rows}
    assert by_id["BL-911"].problems == ("no **Status:** field",)
    assert bs.main(["--check", "--file", str(path)]) == 1           # RED under the mutation

    path.write_text(original)                                       # restore from the copy
    assert path.read_text() == original                             # the restore, verified
    assert bs.main(["--check", "--file", str(path)]) == 0           # green after


# ---------------------------------------------------------------------------
# The done-check, over the real backlog
# ---------------------------------------------------------------------------


def test_every_row_id_carries_exactly_one_field_in_the_vocabulary():
    rows = bs.load()
    bad = [(r.row_id, r.problems) for r in rows if r.problems]
    assert bad == [], bad
    assert all(r.value in bs.VOCABULARY for r in rows)


def test_the_backlog_passes_check():
    assert bs.main(["--check"]) == 0


def test_the_census_the_test_derives_equals_the_cli_s():
    """Both sides derived; neither is a literal (BL-164).

    The test's side comes from the module, the CLI's from a subprocess actually running
    it. A literal here would go red when the backlog grew, not when the code broke.
    """
    counts = bs.census(bs.load())
    result = subprocess.run(
        [sys.executable, "scripts/backlog_status.py", "--census"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr

    printed = {}
    for line in result.stdout.split("\n"):
        parts = line.split()
        if len(parts) == 2 and parts[0] in bs.VOCABULARY:
            printed[parts[0]] = int(parts[1])

    assert printed == counts
    assert f"THE OPEN SET IS {counts['OPEN']}." in result.stdout
    assert sum(counts.values()) == len(bs.load())


def test_the_census_names_the_command_that_reproduces_it():
    """§Learning — BL-152: a count in prose carries the command that reproduces it."""
    result = subprocess.run(
        [sys.executable, "scripts/backlog_status.py", "--census"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert "python3 scripts/backlog_status.py --census" in result.stdout


def test_the_closure_sections_carry_no_field():
    """One field per row id, on the title section only — else `exactly one` fails."""
    sections = bs.parse_sections(bs.BACKLOG_MD.read_text())
    closures = [s for s in sections if not s.is_title]
    assert closures, "positive control: the file has closure sections"
    assert all(s.field_hits() == [] for s in closures)


# ---------------------------------------------------------------------------
# PLACEMENT — the archive invariant
# ---------------------------------------------------------------------------
#
# Added after `5721718`, which marked BL-048 and BL-178 `DONE` and left both in the
# open file. Every gate passed: the vocabulary assertion reads the VALUE and was
# blind to the FILE, so the one rule t1b split the backlog on was the one rule
# nothing checked. Both directions are tested, because one direction is half a guard.


def _sec(row_id, value, path, *, title=True):
    """A minimal title (or closure) section, standing in one file."""
    suffix = " (#TBD)" if title else ""
    lines = (f"### {row_id} — synthetic{suffix}", f"**Status:** {value}", "")
    return bs.Section((row_id,), lines[0], 1, lines, path)


def test_a_terminal_row_in_the_open_file_fails():
    sec = _sec("BL-901", "DONE", bs.BACKLOG_MD)
    (row,) = bs.resolve([sec])
    assert row.value == "DONE"
    assert any("belongs in" in p for p in row.problems), row.problems


def test_a_non_terminal_row_in_the_archive_fails():
    sec = _sec("BL-902", "OPEN", bs.BACKLOG_ARCHIVE_MD)
    (row,) = bs.resolve([sec])
    assert row.value == "OPEN"
    assert any("only DONE archives" in p for p in row.problems), row.problems


def test_unruled_is_not_terminal_and_must_not_archive():
    """C4: UNRULED has an open remainder, so the archive is wrong for it."""
    assert bs.resolve([_sec("BL-903", "UNRULED", bs.BACKLOG_MD)])[0].problems == ()
    archived = bs.resolve([_sec("BL-904", "UNRULED", bs.BACKLOG_ARCHIVE_MD)])[0]
    assert any("only DONE archives" in p for p in archived.problems), archived.problems


def test_each_side_accepts_the_rows_that_belong_on_it():
    """The positive control: without it the two tests above pass on a check that
    flags everything."""
    assert bs.resolve([_sec("BL-905", "DONE", bs.BACKLOG_ARCHIVE_MD)])[0].problems == ()
    assert bs.resolve([_sec("BL-906", "OPEN", bs.BACKLOG_MD)])[0].problems == ()


def test_placement_is_inert_off_the_two_real_files(tmp_path):
    """A fixture is not part of the split and must not be judged against it —
    which is what keeps every `--file <fixture>` test above meaningful."""
    assert bs.resolve([_sec("BL-907", "DONE", None)])[0].problems == ()
    assert bs.resolve([_sec("BL-908", "DONE", tmp_path / "fixture.md")])[0].problems == ()


def test_the_real_backlog_honours_the_split():
    """The done-check, over both real files. Derived on both sides, no literals."""
    rows = bs.load()
    misplaced = [(r.row_id, r.problems) for r in rows
                 if any("archives" in p or "belongs in" in p for p in r.problems)]
    assert misplaced == [], misplaced

    # Positive control: both sides are non-empty, so the assertion above is not
    # passing over an empty set.
    by_file = {}
    for path in bs.BACKLOG_FILES:
        titles = [s for s in bs.parse_sections(path.read_text(), path) if s.is_title]
        by_file[path.name] = titles
        assert titles, f"positive control: {path.name} has title sections"
    archived = bs.resolve(
        [s for s in bs.parse_files(bs.BACKLOG_FILES)
         if s.path == bs.BACKLOG_ARCHIVE_MD]
    )
    assert archived and all(r.value in bs.TERMINAL for r in archived)
