"""Tests for scripts/repin_manifest.py (BL-002's pin updater).

The pinned commit column is what `drift_check`'s check 8 reads, so a rewriter that
touches one character too many corrupts the record the check is measured against — and
a manifest is 500 lines of prose around 25 rows, most of it *about* commits.

Two properties carry this suite:

  * **Idempotence.** Run against a current manifest, the diff is empty. Anything else
    means the rewriter is moving something the derivation did not ask it to.
  * **Containment.** The prose, the per-boundary `row | repo | was | now` tables (which
    are full of backticked hashes), the `last changed` column and the self-referential
    row are all left byte-identical. Asserted against the whole file, not the row.

Hermetic against throwaway git repos, for the reason test_export_bundle.py states.

**The fixture's commits are dated explicitly, and every date cell is read back out of
git (2026-08-17).** Until then this module wrote the literal `2026-08-16` into the date
column of a manifest whose commits were made at run time, so `repin_manifest.py` — which
derives the date from the commit it resolves — disagreed with the fixture from the first
midnight onward, and the two whole-file assertions went red on a clock tick rather than on
a defect. The dates are also **distinct per commit**, which is load-bearing rather than
tidy: when every commit in the fixture shares one date, a rewriter reading the date off
`HEAD`, or off the wrong repo, writes the right answer by coincidence and no assertion
here can see it. See `docs/backlog-2026-06.md` BL-164 for the class.
"""

import os
import subprocess
from pathlib import Path
from typing import NamedTuple

import pytest

import repin_manifest
from _manifest import HEADER, SELF_COMMIT

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_ROOT = REPO_ROOT.parent / "aetheris"

# A per-boundary table of the kind the real manifest carries: five cells, backticked
# hashes in the middle two, and NOT part of the export set. The rewriter must not see it.
PROSE_TABLE = """\
**Export boundary — 2026-08-16.** Two rows advanced:

| row | repo | was | now | last changed |
|---|---|---|---|---|
| `agents--CLAUDE.md` | aetheris-agents | `aaaaaaa` | `bbbbbbb` | 2026-08-14 |

Prose that mentions `0000000` and a path `CLAUDE.md` in the same breath.
"""


class Commit(NamedTuple):
    """What the fixture made, as git recorded it — never as the fixture assumed it."""

    hash: str
    date: str  # `--date=short`, read back from the commit rather than restated


def _git(repo: Path, *args: str, date: str | None = None) -> str:
    """`date`, when given, is stamped on the commit instead of the system clock."""
    env = None
    if date is not None:
        env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True, env=env
    )
    return result.stdout.strip()


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "fixture@example.invalid")
    _git(path, "config", "user.name", "fixture")
    return path


def _commit(repo: Path, rel: str, content: str, date: str) -> Commit:
    """Commit `rel` at an explicit `date`, and return the hash AND date git stored.

    The date is an input the fixture controls, not an expectation the fixture states:
    the cell written into the manifest below is read back out of the commit, so the
    fixture and `repin_manifest.py` are reading one object rather than agreeing about
    one. `--date=short` is git's own rendering, which is what the script writes too.
    """
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", f"add {rel}", date=date)
    stored = _git(repo, "log", "-1", "--format=%h %ad", "--date=short", "--", rel)
    commit_hash, commit_date = stored.split()
    return Commit(commit_hash, commit_date)


# The self-referential row's date cell is inert: the rewriter reaches `continue` on
# `_(this export)_` before it reads a date, so this literal is an input nothing derives.
SELF_ROW_DATE = "2020-03-04"


def _manifest_text(rows) -> str:
    lines = [
        "# fixture manifest",
        "",
        "Header prose that names `deadbee` for no reason.",
        "",
        HEADER,
        "|-------------|-----------|------|--------|--------------|",
    ]
    for name, path, repo, commit in rows:
        cell = SELF_COMMIT if commit is None else f"`{commit.hash}`"
        date = SELF_ROW_DATE if commit is None else commit.date
        lines.append(f"| `{name}` | `{path}` | {repo} | {cell} | {date} |")
    lines += ["", PROSE_TABLE]
    return "\n".join(lines)


MANIFEST_REL = "docs/project-knowledge-manifest.md"


@pytest.fixture
def repin_world(tmp_path):
    """Two repos and a manifest whose rows are all current.

    Two things the fixture does on purpose, because without them a whole class of
    mutation is invisible:

      * **The manifest is committed, in the agents repo**, as the real one is. Its own
        row is then a live path rather than a dangling one, so a rewriter that stopped
        honouring `_(this export)_` would produce a hash rather than an error.
      * **Each repo takes a later, unrelated commit.** Without it `HEAD` and the pinned
        path's last commit are the same hash, and a rewriter reading repo HEAD instead
        of `git log -1 -- <path>` passes every assertion here. The later commits are
        also dated later, for the same reason one cell up: same-day commits let a
        rewriter read the wrong object and still write the right date.

    Every commit is dated explicitly and distinctly, so this fixture is the same fixture
    on every day it runs.

    Returns (manifest_path, repo_dirs, commits-by-export-name).
    """
    agents = _init_repo(tmp_path / "agents")
    harness = _init_repo(tmp_path / "harness")

    commits = {
        "agents--CLAUDE.md": _commit(
            agents, "CLAUDE.md", "agents claude\n", "2020-01-02T10:00:00+00:00"
        ),
        "harness--runbook.md": _commit(
            harness, "docs/runbook.md", "harness runbook\n", "2020-02-03T10:00:00+00:00"
        ),
    }
    manifest_body = _manifest_text(
        [
            ("agents--CLAUDE.md", "CLAUDE.md", "aetheris-agents", commits["agents--CLAUDE.md"]),
            (
                "harness--runbook.md",
                "docs/runbook.md",
                "aetheris",
                commits["harness--runbook.md"],
            ),
            ("project-knowledge-manifest.md", MANIFEST_REL, "aetheris-agents", None),
        ]
    )
    _commit(agents, MANIFEST_REL, manifest_body, "2020-03-04T10:00:00+00:00")

    _commit(
        agents, "unrelated.md", "moves agents HEAD past CLAUDE.md\n", "2020-04-05T10:00:00+00:00"
    )
    _commit(
        harness,
        "unrelated.md",
        "moves harness HEAD past docs/runbook.md\n",
        "2020-05-06T10:00:00+00:00",
    )

    return (
        agents / MANIFEST_REL,
        {"aetheris-agents": agents, "aetheris": harness},
        commits,
    )


def _repin(world, **kwargs):
    manifest, repo_dirs, _ = world
    return repin_manifest.repin(manifest, repo_dirs=repo_dirs, **kwargs)


# --------------------------------------------------------------------------- #
# The correctness property                                                     #
# --------------------------------------------------------------------------- #


def test_a_current_manifest_is_left_byte_identical(repin_world):
    """Idempotence, stated as the file rather than as the rows."""
    manifest, _, _ = repin_world
    before = manifest.read_bytes()
    assert _repin(repin_world) == 0
    assert manifest.read_bytes() == before


def test_running_twice_changes_nothing_the_second_time(repin_world):
    manifest, repo_dirs, _ = repin_world
    _commit(
        repo_dirs["aetheris-agents"],
        "CLAUDE.md",
        "agents claude, moved\n",
        "2021-01-02T10:00:00+00:00",
    )

    assert _repin(repin_world) == 0
    after_first = manifest.read_bytes()
    assert _repin(repin_world) == 0
    assert manifest.read_bytes() == after_first


# --------------------------------------------------------------------------- #
# Rewriting                                                                    #
# --------------------------------------------------------------------------- #


def test_a_stale_row_is_repinned_to_what_git_log_returns(repin_world):
    manifest, repo_dirs, _ = repin_world
    moved = _commit(
        repo_dirs["aetheris-agents"],
        "CLAUDE.md",
        "agents claude, moved\n",
        "2021-02-03T10:00:00+00:00",
    )

    assert _repin(repin_world) == 0
    text = manifest.read_text(encoding="utf-8")
    assert f"| `agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `{moved.hash}` |" in text


def test_a_row_pins_its_own_paths_history_not_the_repos_head(repin_world):
    """`git log -1 -- <path>`, and the `-- <path>` is the whole of it.

    Both fixture repos have moved past the pinned files, so a rewriter that read HEAD
    would write a hash that exists, parses, and is wrong — which is the shape check 8
    cannot distinguish from a correct one. The same holds of the date cell, and only
    because the fixture's commits are dated distinctly: a same-day fixture lets a
    rewriter read HEAD's date and still write the pinned commit's.
    """
    manifest, repo_dirs, commits = repin_world
    assert _repin(repin_world) == 0

    text = manifest.read_text(encoding="utf-8")
    assert f"`{commits['agents--CLAUDE.md'].hash}`" in text
    assert f"`{commits['harness--runbook.md'].hash}`" in text
    for repo in repo_dirs.values():
        assert f"`{_git(repo, 'log', '-1', '--format=%h')}`" not in text
        head_date = _git(repo, "log", "-1", "--format=%ad", "--date=short")
        assert f"| {head_date} |" not in text


def test_a_harness_row_is_read_in_the_harness_repo(repin_world):
    """The row's own repo, never this one — a hash from the wrong history parses fine."""
    manifest, repo_dirs, _ = repin_world
    moved = _commit(
        repo_dirs["aetheris"],
        "docs/runbook.md",
        "harness runbook, moved\n",
        "2021-03-04T10:00:00+00:00",
    )

    assert _repin(repin_world) == 0
    assert f"`{moved.hash}`" in manifest.read_text(encoding="utf-8")


def test_only_the_commit_and_date_cells_change(repin_world):
    """Whole-file containment: one line differs, and only in the two cells this owns.

    Cells 4 and 5 are `commit` and `last changed`. Before 2026-08-16 this asserted `[4]`
    alone, which was true of the code and was the defect — the date cell was owned by
    nobody and drifted (BL-151).
    """
    manifest, repo_dirs, _ = repin_world
    before = manifest.read_text(encoding="utf-8").splitlines()
    _commit(
        repo_dirs["aetheris-agents"],
        "CLAUDE.md",
        "agents claude, moved\n",
        "2021-04-05T10:00:00+00:00",
    )

    assert _repin(repin_world) == 0
    after = manifest.read_text(encoding="utf-8").splitlines()

    assert len(before) == len(after)
    changed = [i for i, (b, a) in enumerate(zip(before, after)) if b != a]
    assert len(changed) == 1
    b_cells = before[changed[0]].split("|")
    a_cells = after[changed[0]].split("|")
    assert set(i for i, (b, a) in enumerate(zip(b_cells, a_cells)) if b != a) <= {4, 5}


def test_a_stale_date_beside_a_current_commit_is_repinned(repin_world):
    """The case nothing could report before 2026-08-16: the pin is right, the date is not.

    A row whose commit cell is current and whose date cell is wrong passed every check
    the repo had — this script skipped it as `current`, and check 8 never reads the date.
    """
    manifest, _, commits = repin_world
    text = manifest.read_text(encoding="utf-8")
    staled = text.replace(f"| {commits['agents--CLAUDE.md'].date} |", "| 2014-01-01 |", 1)
    assert staled != text
    manifest.write_text(staled, encoding="utf-8")

    assert _repin(repin_world) == 0
    assert "2014-01-01" not in manifest.read_text(encoding="utf-8")


def test_the_date_is_derived_from_the_resolved_commit_not_from_the_path(repin_world):
    """Two cells, one reading — so they cannot disagree.

    The commit is dated well in the past; the row must take THAT date, which is only
    obtainable from the commit the script already resolved.
    """
    manifest, repo_dirs, _ = repin_world
    _git(
        repo_dirs["aetheris-agents"],
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "unrelated",
    )
    target = repo_dirs["aetheris-agents"] / "CLAUDE.md"
    target.write_text("agents claude, moved with an old date\n", encoding="utf-8")
    _git(repo_dirs["aetheris-agents"], "add", "CLAUDE.md")
    _git(
        repo_dirs["aetheris-agents"],
        "commit",
        "-q",
        "--date=2015-03-04T12:00:00",
        "-m",
        "moved, dated 2015",
    )

    assert _repin(repin_world) == 0
    row = [
        line
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if line.startswith("| `agents--CLAUDE.md`")
    ][0]
    assert row.endswith("| 2015-03-04 |"), row


def test_the_self_referential_row_keeps_its_placeholder(repin_world):
    """`_(this export)_` is what stops the manifest restaling itself."""
    manifest, repo_dirs, _ = repin_world
    _commit(
        repo_dirs["aetheris-agents"],
        "CLAUDE.md",
        "agents claude, moved\n",
        "2021-05-06T10:00:00+00:00",
    )

    assert _repin(repin_world) == 0
    text = manifest.read_text(encoding="utf-8")
    assert (
        f"| `project-knowledge-manifest.md` | `{MANIFEST_REL}` | aetheris-agents | {SELF_COMMIT} |"
        in text
    )


def test_a_per_boundary_prose_table_is_not_rewritten(repin_world):
    """The manifest's own narrative is full of backticked hashes in five-cell rows."""
    manifest, repo_dirs, _ = repin_world
    _commit(
        repo_dirs["aetheris-agents"],
        "CLAUDE.md",
        "agents claude, moved\n",
        "2021-06-07T10:00:00+00:00",
    )

    assert _repin(repin_world) == 0
    assert PROSE_TABLE in manifest.read_text(encoding="utf-8")


def test_dry_run_reports_the_move_and_writes_nothing(repin_world):
    manifest, repo_dirs, _ = repin_world
    before = manifest.read_bytes()
    _commit(
        repo_dirs["aetheris-agents"],
        "CLAUDE.md",
        "agents claude, moved\n",
        "2021-07-08T10:00:00+00:00",
    )

    assert _repin(repin_world, dry_run=True) == 0
    assert manifest.read_bytes() == before


# --------------------------------------------------------------------------- #
# Refusals                                                                     #
# --------------------------------------------------------------------------- #


def test_an_underivable_row_writes_nothing_at_all(repin_world):
    """One bad row does not get a partially re-pinned manifest committed on top of it."""
    manifest, repo_dirs, _ = repin_world
    text = manifest.read_text(encoding="utf-8").replace(
        "| `CLAUDE.md` |", "| `never-committed.md` |"
    )
    manifest.write_text(text, encoding="utf-8")
    _commit(
        repo_dirs["aetheris"],
        "docs/runbook.md",
        "harness runbook, moved\n",
        "2021-08-09T10:00:00+00:00",
    )
    before = manifest.read_bytes()

    assert _repin(repin_world) == 1
    assert manifest.read_bytes() == before


def test_a_malformed_row_is_a_failure_not_a_skip(repin_world):
    """A row the parser cannot read must not silently drop out of the export set."""
    manifest, _, _ = repin_world
    text = manifest.read_text(encoding="utf-8").replace(
        "| `harness--runbook.md` |", "| harness--runbook.md |"
    )
    manifest.write_text(text, encoding="utf-8")
    before = manifest.read_bytes()

    assert _repin(repin_world) == 1
    assert manifest.read_bytes() == before


# --------------------------------------------------------------------------- #
# The live manifest                                                            #
# --------------------------------------------------------------------------- #


@pytest.mark.integration
@pytest.mark.skipif(not HARNESS_ROOT.exists(), reason="sibling harness checkout absent")
def test_the_live_manifest_converges_in_one_pass(tmp_path):
    """Idempotence over the real rows in the two real repos — on a copy, with a
    planted staleness so the write path is actually exercised.

    It asserts convergence, **not** currency. The live manifest is *expected* to go
    stale between export boundaries — that is the strict-exempt WARN class — so a test
    asserting the pins are current would go red on the next `CLAUDE.md` edit and train
    exactly the alarm fatigue BL-009 exists to prevent. What must hold at every point in
    the cycle is that one pass settles and the next moves nothing.

    The plant is what keeps it from passing vacuously: over a manifest that happens to
    be current, `repin` writes nothing at all and every defect in the rewriter is
    invisible to a convergence assertion.
    """
    from _manifest import MANIFEST_MD, read_rows

    copy = tmp_path / "manifest.md"
    copy.write_bytes(MANIFEST_MD.read_bytes())

    # Settle first, so the comparison below is against what this HEAD implies rather
    # than against whatever the last export boundary pinned.
    assert repin_manifest.repin(copy) == 0
    settled = copy.read_text(encoding="utf-8")

    row = next(r for r in read_rows(copy) if r.commit)
    lines = settled.splitlines(keepends=True)
    lines[row.line_no - 1] = lines[row.line_no - 1].replace(f"`{row.commit}`", "`0000000`")
    assert "".join(lines) != settled, "the plant did not land — no row was staled"
    copy.write_text("".join(lines), encoding="utf-8")

    # Pass 1 restores exactly what was planted over, and nothing else.
    assert repin_manifest.repin(copy) == 0
    assert copy.read_text(encoding="utf-8") == settled
    assert repin_manifest.repin(copy) == 0
    assert copy.read_text(encoding="utf-8") == settled
