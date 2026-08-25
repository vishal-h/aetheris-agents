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

# Defeat 5: a row that preserves its own pre-implementation ticket under a
# `<summary>`. BOTH attributions are exercised at once — the inner `### BL-` must
# not mint a section, and the inner `**Status:**` must not be read as the row's
# live value — because in the real shape they arrive together and a fixture that
# separated them would not be the shape.
#
# BL-960 is the whole shape: a live depth-0 field ABOVE the block, an archived one
# INSIDE it, and they disagree. If depth is ignored the row has two fields and
# `--check` fails; if depth is tracked it has exactly one and the value is DONE —
# the live one, never the archived one. The disagreement is deliberate: with both
# set to the same value, a parser reading the wrong line would still print the
# right answer and the test would pass on a broken parser.
FIXTURE_DETAILS = """\
### BL-960 — a row preserving its pre-implementation ticket (#TBD)
**Status:** DONE
**Size:** S · **Priority:** low

Body of the live row.

<details><summary>Original ticket (pre-implementation)</summary>

### BL-960 — the original title, preserved verbatim (#TBD)
**Status:** UNRULED
**Size:** S · **Priority:** low

Body of the archived ticket.

</details>

### BL-961 — the next real row (#TBD)
**Status:** OPEN
**Size:** S · **Priority:** low
"""

# The same shape with the live field REMOVED — BL-047's actual state between C1
# and C2. The row's only `**Status:**` is archived, so it has no live declaration.
FIXTURE_ARCHIVED_ONLY = """\
### BL-970 — DONE (impl) 2026-07-24 · a disposition heading, no live field
Body of the live row.

<details><summary>Original ticket (pre-implementation)</summary>

### BL-970 — the original title, preserved verbatim (#TBD)
**Status:** UNRULED

</details>
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
# Defeat 5 — `<details>` depth. TEST 1 of the C1 pair.
# ---------------------------------------------------------------------------


def test_defeat_5_a_depth_1_status_is_not_counted_and_a_depth_0_one_is(tmp_path):
    """The whole of defeat 5 in one shape, both halves asserted separately.

    The two halves fail differently and a single assertion could not tell them
    apart: forgetting the HEADING half mints a second BL-960 section, forgetting
    the FIELD half gives the row two fields. Both are checked, and the resolved
    value is checked against the disagreeing pair so that reading the wrong line
    cannot produce the right answer.
    """
    path = _write(tmp_path, FIXTURE_DETAILS)
    sections = bs.parse_sections(path.read_text())

    # HALF 1 — the inner `### BL-960` is not a row heading. Two sections, not three.
    assert [s.ids for s in sections] == [("BL-960",), ("BL-961",)]
    # …and the preserved heading is still INSIDE BL-960's span, not dropped.
    assert "### BL-960 — the original title" in "\n".join(sections[0].lines)

    # HALF 2 — the depth-0 field is the value; the depth-1 one is not a field.
    assert sections[0].field_hits() == [(1, "DONE")]
    assert [v for _, v in sections[0].field_hits(deep=True)] == ["UNRULED"]

    rows = bs.resolve(sections)
    assert {r.row_id: r.value for r in rows} == {"BL-960": "DONE", "BL-961": "OPEN"}
    # DONE, not UNRULED: the archived line disagrees, so this distinguishes a
    # parser that reads the live line from one that reads the last line it saw.
    assert all(not r.problems for r in rows)
    assert bs.main(["--check", "--file", str(path)]) == 0


def test_depth_is_measured_at_line_start(tmp_path):
    """`<details><summary>…</summary>` is itself outer; `</details>` is itself inner.

    This is the ordering the two attributions rest on, and getting it wrong by one
    line moves the block's own delimiters into the wrong row.
    """
    lines = ["a", "<details><summary>s</summary>", "b", "</details>", "c"]
    assert bs.details_depths(lines) == [0, 0, 1, 1, 0]


def test_an_unbalanced_close_clamps_rather_than_going_negative(tmp_path):
    """Malformed markup must not silently PROMOTE archived text to a field.

    Without the clamp a stray `</details>` drives depth to -1, and every later
    `**Status:**` inside a real block then reads as depth 0 — a well-formed wrong
    answer, which is the class this parser exists to remove.
    """
    lines = ["</details>", "<details>", "x", "</details>", "y"]
    assert bs.details_depths(lines) == [0, 0, 1, 1, 0]
    assert min(bs.details_depths(lines)) >= 0


# --- defeat 5's own defeat: this file is full of prose ABOUT its markup ---------
#
# Found the day depth tracking landed. A row filed to record the design choice
# wrote `<details>` inside a code span, in a sentence explaining depth tracking;
# the scanner read it as a tag, opened a depth that never closed, and 64 row
# headings after that line stopped existing. `--check` said 45 sections where
# there were 109, and exited 0.

FIXTURE_PROSE_ABOUT_MARKUP = """\
### BL-990 — a row whose PROSE names the tag (#TBD)
**Status:** OPEN

A `<details>` block is archived text. Nothing here opens one, and a naked
</details> in prose must not close one either.

```
<details><summary>an EXAMPLE, inside a fence</summary>
### BL-991 — an example heading, not a row
**Status:** DONE
</details>
```

### BL-992 — the row after all that (#TBD)
**Status:** OPEN
"""


def test_markup_named_in_prose_or_quoted_in_a_fence_is_not_markup(tmp_path):
    """The regression that amended C1, asserted at every surface it broke."""
    path = _write(tmp_path, FIXTURE_PROSE_ABOUT_MARKUP)
    lines = path.read_text().split("\n")
    depths, in_fence = bs.scan_markup(lines)

    # 1. Depth never rises: no line in this fixture is a real tag.
    assert max(depths) == 0, [(i + 1, lines[i]) for i, d in enumerate(depths) if d]
    # 2. The fence is recognised, so the assertion above is not passing because the
    #    scanner has simply stopped seeing anything.
    assert any(in_fence), "positive control: the fixture's fence is detected"

    sections = bs.parse_sections(path.read_text())
    # 3. The fenced `### BL-991` is an example, not a row.
    assert [s.ids for s in sections] == [("BL-990",), ("BL-992",)]
    # 4. The fenced `**Status:** DONE` is an example, not a field — BL-990 would
    #    otherwise carry two and fail.
    rows = bs.resolve(sections)
    assert {r.row_id: r.value for r in rows} == {"BL-990": "OPEN", "BL-992": "OPEN"}
    assert all(not r.problems and not r.notes for r in rows)
    assert bs.main(["--check", "--file", str(path)]) == 0


def test_a_fence_closes_only_on_its_own_character():
    """CommonMark's rule, and the one that keeps a shell block quoting `~~~` safe."""
    _, in_fence = bs.scan_markup(["a", "```", "~~~", "x", "```", "b"])
    assert in_fence == [False, True, True, True, True, False]


def test_the_live_corpus_details_depth_is_balanced():
    """THE ASSERTION THAT WOULD HAVE CAUGHT IT, over the real files.

    An unclosed `<details>` swallows every row heading after it, and the symptom is
    a section count that is quietly too low — indistinguishable from a correct one
    by reading the exit code. Balance is the property that fails loudly instead.
    """
    for path in bs.BACKLOG_FILES:
        lines = path.read_text().split("\n")
        depths = bs.details_depths(lines)
        assert depths[-1] == 0, (path.name, "unclosed <details>", depths[-1])
        assert min(depths) >= 0, (path.name, "clamp breached")

    # Positive control: the corpus really does contain a `<details>` block, so the
    # balance assertion is standing over something rather than over a file with no
    # tags at all.
    #
    # It does NOT also assert that the corpus contains a PROSE mention of the tag.
    # That was written here first and was wrong: it is a claim about what the
    # backlog happens to say this week, not about the parser, and it went red the
    # moment it was checked against a tree that did not yet carry the row whose
    # prose it was describing. The prose-vs-markup property is a SHAPE, and it is
    # asserted where shapes belong — on a fixture, in
    # `test_markup_named_in_prose_or_quoted_in_a_fence_is_not_markup`, which holds
    # whatever the corpus says.
    text = "\n".join(p.read_text() for p in bs.BACKLOG_FILES)
    assert bs.DETAILS_OPEN_RE.search(text), "positive control: a real block exists"


def test_archived_only_is_a_note_and_never_a_failure(tmp_path):
    """The C1 design choice, asserted rather than described.

    A row whose only field is archived has NO live declaration. `--check` says so,
    loudly and by name, and exits 0 — and the row is NOT given the archived value.
    """
    path = _write(tmp_path, FIXTURE_ARCHIVED_ONLY)
    (row,) = bs.resolve(bs.parse_sections(path.read_text()))

    assert row.value is None                       # NOT "UNRULED"
    assert row.problems == ()                      # not a failure…
    assert row.archived_only                       # …but flagged
    assert any(n.startswith("ARCHIVED-ONLY") for n in row.notes), row.notes
    assert bs.main(["--check", "--file", str(path)]) == 0


def test_no_field_at_any_depth_is_still_a_hard_failure(tmp_path):
    """The boundary of the choice above: ARCHIVED-ONLY is softened, absence is not.

    Without this, `test_archived_only_is_a_note_and_never_a_failure` would pass
    just as well on a parser that had stopped failing on anything at all.
    """
    path = _write(tmp_path, "### BL-980 — a row with no status line at all (#TBD)\nBody.\n")
    (row,) = bs.resolve(bs.parse_sections(path.read_text()))

    assert row.problems == ("no **Status:** field",)
    assert row.notes == ()
    assert not row.archived_only
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
    """Widened at C1, not weakened: the partition is asserted to be EXHAUSTIVE.

    Before defeat 5 every row had a value, so `all(value in VOCABULARY)` was the
    whole statement. Defeat 5 adds one lawful way to have none — ARCHIVED-ONLY —
    and the assertion becomes *every row is in exactly one of the two states*,
    which is strictly more than the old form said. A row that fell out of both
    (value `None`, no note) would now fail here and could not have failed before.
    """
    rows = bs.load()
    bad = [(r.row_id, r.problems) for r in rows if r.problems]
    assert bad == [], bad

    valued = [r for r in rows if r.value is not None]
    noted = bs.archived_only(rows)
    assert all(r.value in bs.VOCABULARY for r in valued)
    assert len(valued) + len(noted) == len(rows), [
        r.row_id for r in rows if r.value is None and not r.archived_only
    ]


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

    # The exhaustiveness identity, in its C1 form. It previously read
    # `sum(counts.values()) == len(load())`, which asserted that every row has a
    # value; defeat 5 makes that false by design for an ARCHIVED-ONLY row. The
    # replacement asserts the same thing the old one did — that the census
    # partitions the row set with nothing falling through — over the partition
    # that now exists. Both sides stay derived; neither is a literal (BL-164).
    rows = bs.load()
    archived_n = len(bs.archived_only(rows))
    assert sum(counts.values()) + archived_n == len(rows)
    assert f"= {len(rows)}" in result.stdout and "(OK)" in result.stdout


def test_the_census_names_the_command_that_reproduces_it():
    """§Learning — BL-152: a count in prose carries the command that reproduces it."""
    result = subprocess.run(
        [sys.executable, "scripts/backlog_status.py", "--census"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
    )
    assert "python3 scripts/backlog_status.py --census" in result.stdout


def test_the_closure_sections_carry_no_field():
    """One field per row id, on the title section only — else `exactly one` fails.

    Scoped to the UNION, not to the open file. The invariant was always about both
    — `resolve` merges every section an id owns across both files — and pinning the
    positive control to one side made it hostage to which side happened to hold a
    closure section that week. It stopped holding the week the open file's last one
    moved to the archive, and the test then failed on its own control while the
    invariant it asserts was untouched.
    """
    sections = bs.parse_files(bs.BACKLOG_FILES)
    closures = [s for s in sections if not s.is_title]
    assert closures, "positive control: the union has closure sections"
    assert all(s.field_hits() == [] for s in closures)


# ---------------------------------------------------------------------------
# THE NO-CHANGE TEST — defeat 5 over the LIVE corpus. TEST 2 of the C1 pair,
# and the one that proves the fix has EXACTLY ONE SUBJECT.
# ---------------------------------------------------------------------------
#
# A unit test shows the new reading is right on a shape built to show it. It says
# nothing about the 183 rows nobody built, and a depth fix is exactly the kind of
# change that can quietly re-segment a file. So the two readings are run over the
# real corpus and DIFFED, and the diff is asserted to be the ARCHIVED-ONLY set —
# derived on both sides, never enumerated here.


def _depth_blind_reading(paths):
    """The PRE-C1 algorithm, reconstructed: every `### BL-` is a heading and every
    `**Status:**` is a field, whatever depth it sits at.

    This is a deliberate SECOND derivation over the same file, which the module
    docstring warns against — and the warning does not reach it, because its whole
    purpose is to be the OTHER derivation. It is never trusted: it exists only to
    be compared against the module, and if the two ever agree everywhere the test
    fails on its own positive control below.

    Built from the module's own regexes so that a later change to `HEADING_RE` or
    `FIELD_RE` moves both readings together and this test keeps measuring depth
    rather than drifting into a regex test.
    """
    rows = {}
    for path in paths:
        lines = path.read_text().split("\n")
        starts = [i for i, l in enumerate(lines) if bs.HEADING_RE.match(l)]
        for n, i in enumerate(starts):
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            m = bs.ID_PREFIX_RE.match(lines[i])
            ids = (tuple(bs.ID_RE.findall(m.group(1))) if m
                   else tuple(bs.ID_RE.findall(lines[i][:40])))
            hits = [bs.FIELD_RE.fullmatch(l).group(1)
                    for l in lines[i:end] if bs.FIELD_RE.fullmatch(l)]
            for row_id in ids:
                rows.setdefault(row_id, []).extend(hits)
    return rows


def test_defeat_5_changes_exactly_one_row_over_the_live_corpus():
    """Same row ids, same field count, same value — for every row but the noted ones."""
    old = _depth_blind_reading(bs.BACKLOG_FILES)
    new = {r.row_id: r for r in bs.load()}

    # POSITIVE CONTROL, first: both readings are over a real, non-trivial corpus.
    # Without it every assertion below passes vacuously on two empty dicts.
    assert len(new) > 100, len(new)
    assert len(old) > 100, len(old)

    # 1. THE ROW-ID COUNT IS UNCHANGED. Re-segmenting is the failure mode a depth
    #    change most easily causes, and it shows up here before anything else.
    assert set(old) == set(new)
    assert len(old) == len(new)

    # 2. THE PER-ROW FIELD-COUNT SET. Not a summary string: the count for every id
    #    under both readings, compared id by id.
    old_counts = {k: len(v) for k, v in old.items()}
    new_counts = {k: r.n_fields for k, r in new.items()}
    differing = {k for k in old_counts if old_counts[k] != new_counts[k]}

    # 3. THE DIFF IS THE SET OF ROWS CARRYING A FIELD INSIDE `<details>` — derived
    #    from the module, never enumerated here. This is the stable statement of
    #    what defeat 5 changed. It is NOT "the ARCHIVED-ONLY set": those coincide
    #    only while such a row has no live field, and the first row to gain one
    #    (BL-047, at its close) separated them. ARCHIVED-ONLY is a strict SUBSET,
    #    asserted as such below, and can legitimately be empty.
    deep = {row_id
            for sec in bs.parse_files(bs.BACKLOG_FILES)
            if sec.field_hits(deep=True)
            for row_id in sec.ids}
    assert differing == deep, (sorted(differing), sorted(deep))

    # 4. …and it is NOT empty. If it were, this test would be asserting that the
    #    C1 change did nothing at all, and would pass on a reverted parser.
    assert deep, "positive control: defeat 5 has at least one subject in the corpus"
    assert {r.row_id for r in bs.archived_only(bs.load())} <= deep

    # 5. Every row OUTSIDE the diff resolves to the same value it did before.
    for row_id, r in new.items():
        if row_id in deep:
            continue
        assert old[row_id] == ([r.value] if r.value else []), (row_id, old[row_id])


def test_the_deep_field_rows_are_exactly_what_a_raw_depth_scan_finds():
    """A third, independent reading — a raw depth scan over the files — agrees.

    Steps 3 and 4 above compare the module against a reconstruction of its own
    prior self, which shares its assumptions. This shares none of them: it counts
    `<details>` and `**Status:**` directly and asks which rows have the second
    only inside the first.
    """
    deep = {row_id
            for sec in bs.parse_files(bs.BACKLOG_FILES)
            if sec.field_hits(deep=True)
            for row_id in sec.ids}

    scanned = set()
    for path in bs.BACKLOG_FILES:
        lines = path.read_text().split("\n")
        depths = bs.details_depths(lines)
        cur, seen_deep = None, {}
        for i, line in enumerate(lines):
            if bs.HEADING_RE.match(line) and depths[i] == 0:
                m = bs.ID_PREFIX_RE.match(line)
                cur = (tuple(bs.ID_RE.findall(m.group(1))) if m
                       else tuple(bs.ID_RE.findall(line[:40])))
            if cur and depths[i] > 0 and bs.FIELD_RE.fullmatch(line):
                for row_id in cur:
                    seen_deep[row_id] = seen_deep.get(row_id, 0) + 1
        scanned |= set(seen_deep)

    assert scanned == deep, (sorted(scanned), sorted(deep))
    # Positive control: the corpus contains `<details>` at all, so a scan that
    # found nothing would be caught rather than read as agreement.
    blocks = sum(len(bs.DETAILS_OPEN_RE.findall(p.read_text()))
                 for p in bs.BACKLOG_FILES)
    assert blocks > 0, "positive control: the corpus contains <details> blocks"


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
