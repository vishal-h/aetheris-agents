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
"""

import subprocess
from pathlib import Path

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


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "fixture@example.invalid")
    _git(path, "config", "user.name", "fixture")
    return path


def _commit(repo: Path, rel: str, content: str) -> str:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", f"add {rel}")
    return _git(repo, "log", "-1", "--format=%h", "--", rel)


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
        cell = SELF_COMMIT if commit is None else f"`{commit}`"
        lines.append(f"| `{name}` | `{path}` | {repo} | {cell} | 2026-08-16 |")
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
        of `git log -1 -- <path>` passes every assertion here.

    Returns (manifest_path, repo_dirs, hashes-by-export-name).
    """
    agents = _init_repo(tmp_path / "agents")
    harness = _init_repo(tmp_path / "harness")

    hashes = {
        "agents--CLAUDE.md": _commit(agents, "CLAUDE.md", "agents claude\n"),
        "harness--runbook.md": _commit(harness, "docs/runbook.md", "harness runbook\n"),
    }
    manifest_body = _manifest_text(
        [
            ("agents--CLAUDE.md", "CLAUDE.md", "aetheris-agents", hashes["agents--CLAUDE.md"]),
            ("harness--runbook.md", "docs/runbook.md", "aetheris", hashes["harness--runbook.md"]),
            ("project-knowledge-manifest.md", MANIFEST_REL, "aetheris-agents", None),
        ]
    )
    _commit(agents, MANIFEST_REL, manifest_body)

    _commit(agents, "unrelated.md", "moves agents HEAD past CLAUDE.md\n")
    _commit(harness, "unrelated.md", "moves harness HEAD past docs/runbook.md\n")

    return (
        agents / MANIFEST_REL,
        {"aetheris-agents": agents, "aetheris": harness},
        hashes,
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
    _commit(repo_dirs["aetheris-agents"], "CLAUDE.md", "agents claude, moved\n")

    assert _repin(repin_world) == 0
    after_first = manifest.read_bytes()
    assert _repin(repin_world) == 0
    assert manifest.read_bytes() == after_first


# --------------------------------------------------------------------------- #
# Rewriting                                                                    #
# --------------------------------------------------------------------------- #


def test_a_stale_row_is_repinned_to_what_git_log_returns(repin_world):
    manifest, repo_dirs, _ = repin_world
    new_hash = _commit(repo_dirs["aetheris-agents"], "CLAUDE.md", "agents claude, moved\n")

    assert _repin(repin_world) == 0
    text = manifest.read_text(encoding="utf-8")
    assert f"| `agents--CLAUDE.md` | `CLAUDE.md` | aetheris-agents | `{new_hash}` |" in text


def test_a_row_pins_its_own_paths_history_not_the_repos_head(repin_world):
    """`git log -1 -- <path>`, and the `-- <path>` is the whole of it.

    Both fixture repos have moved past the pinned files, so a rewriter that read HEAD
    would write a hash that exists, parses, and is wrong — which is the shape check 8
    cannot distinguish from a correct one.
    """
    manifest, repo_dirs, hashes = repin_world
    assert _repin(repin_world) == 0

    text = manifest.read_text(encoding="utf-8")
    assert f"`{hashes['agents--CLAUDE.md']}`" in text
    assert f"`{hashes['harness--runbook.md']}`" in text
    for repo in repo_dirs.values():
        assert f"`{_git(repo, 'log', '-1', '--format=%h')}`" not in text


def test_a_harness_row_is_read_in_the_harness_repo(repin_world):
    """The row's own repo, never this one — a hash from the wrong history parses fine."""
    manifest, repo_dirs, _ = repin_world
    new_hash = _commit(repo_dirs["aetheris"], "docs/runbook.md", "harness runbook, moved\n")

    assert _repin(repin_world) == 0
    assert f"`{new_hash}`" in manifest.read_text(encoding="utf-8")


def test_only_the_commit_cell_changes(repin_world):
    """Whole-file containment: exactly one line differs, and only in its fourth cell."""
    manifest, repo_dirs, _ = repin_world
    before = manifest.read_text(encoding="utf-8").splitlines()
    _commit(repo_dirs["aetheris-agents"], "CLAUDE.md", "agents claude, moved\n")

    assert _repin(repin_world) == 0
    after = manifest.read_text(encoding="utf-8").splitlines()

    assert len(before) == len(after)
    changed = [i for i, (b, a) in enumerate(zip(before, after)) if b != a]
    assert len(changed) == 1
    b_cells = before[changed[0]].split("|")
    a_cells = after[changed[0]].split("|")
    assert [i for i, (b, a) in enumerate(zip(b_cells, a_cells)) if b != a] == [4]


def test_the_self_referential_row_keeps_its_placeholder(repin_world):
    """`_(this export)_` is what stops the manifest restaling itself."""
    manifest, repo_dirs, _ = repin_world
    _commit(repo_dirs["aetheris-agents"], "CLAUDE.md", "agents claude, moved\n")

    assert _repin(repin_world) == 0
    text = manifest.read_text(encoding="utf-8")
    assert (
        f"| `project-knowledge-manifest.md` | `{MANIFEST_REL}` | aetheris-agents | {SELF_COMMIT} |"
        in text
    )


def test_a_per_boundary_prose_table_is_not_rewritten(repin_world):
    """The manifest's own narrative is full of backticked hashes in five-cell rows."""
    manifest, repo_dirs, _ = repin_world
    _commit(repo_dirs["aetheris-agents"], "CLAUDE.md", "agents claude, moved\n")

    assert _repin(repin_world) == 0
    assert PROSE_TABLE in manifest.read_text(encoding="utf-8")


def test_dry_run_reports_the_move_and_writes_nothing(repin_world):
    manifest, repo_dirs, _ = repin_world
    before = manifest.read_bytes()
    _commit(repo_dirs["aetheris-agents"], "CLAUDE.md", "agents claude, moved\n")

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
    _commit(repo_dirs["aetheris"], "docs/runbook.md", "harness runbook, moved\n")
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
