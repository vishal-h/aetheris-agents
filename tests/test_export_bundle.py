"""Tests for scripts/assemble_export_bundle.py (BL-002's assembler).

The bundle is the artifact that leaves the machine, so every property asserted here is
one whose failure is invisible in the bundle itself: a document read from the working
tree instead of committed history looks exactly like one read correctly; two exports
merged into one directory look exactly like one export; an unswept bundle looks exactly
like a swept one.

**Hermetic, against throwaway git repos.** The assembler's whole job is to read
`git show HEAD:<path>` in the *owning* repo, so a test that runs against this repo would
be asserting the answer it wants to derive. Each test builds its own two-repo fixture,
commits content, and then **dirties the working tree** — the mutation that would make a
`Path.read_text()` implementation pass is present in every fixture by construction.

The live-repo reproduction (this bundle against the preserved one from the 2026-08-14
boundary) is the ticket's done-check and is reported in the packet; the one integration
test below is its durable residue.
"""

import subprocess
import sys
from pathlib import Path

import pytest

import assemble_export_bundle
from _manifest import HEADER, SELF_COMMIT, ManifestError

REPO_ROOT = Path(__file__).resolve().parent.parent
HARNESS_ROOT = REPO_ROOT.parent / "aetheris"


# --------------------------------------------------------------------------- #
# Fixture repos                                                                #
# --------------------------------------------------------------------------- #
# Deliberately duplicated in test_repin_manifest.py rather than shared through
# conftest.py: the two suites want different fixtures, and the repo has no root
# pytest configuration to make a shared helper importable from both (BL-152).


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


def _manifest_text(rows: list[tuple[str, str, str, str]]) -> str:
    """`rows` = (export name, repo path, repo, commit-cell-or-None)."""
    lines = [
        "# fixture manifest",
        "",
        HEADER,
        "|-------------|-----------|------|--------|--------------|",
    ]
    for name, path, repo, commit in rows:
        cell = SELF_COMMIT if commit is None else f"`{commit}`"
        lines.append(f"| `{name}` | `{path}` | {repo} | {cell} | 2026-08-16 |")
    lines += ["", "Some prose after the table.", ""]
    return "\n".join(lines)


@pytest.fixture
def bundle_world(tmp_path):
    """Two repos, a manifest, and a dirtied working tree in both.

    Returns (manifest_path, repo_dirs, committed) where `committed` maps export name
    to the bytes the bundle must carry.
    """
    agents = _init_repo(tmp_path / "agents")
    harness = _init_repo(tmp_path / "harness")

    committed = {
        "agents--CLAUDE.md": "agents claude, committed\n",
        "renamed-brief.md": "a brief whose export name no path rule regenerates\n",
        "harness--runbook.md": "harness runbook, committed\n",
    }
    _commit(agents, "CLAUDE.md", committed["agents--CLAUDE.md"])
    _commit(agents, "docs/research/long-original-name-2026-06.md", committed["renamed-brief.md"])
    _commit(harness, "docs/runbook.md", committed["harness--runbook.md"])

    manifest_rel = "docs/project-knowledge-manifest.md"
    manifest_body = _manifest_text(
        [
            ("agents--CLAUDE.md", "CLAUDE.md", "aetheris-agents", "0000000"),
            (
                "renamed-brief.md",
                "docs/research/long-original-name-2026-06.md",
                "aetheris-agents",
                "0000000",
            ),
            ("harness--runbook.md", "docs/runbook.md", "aetheris", "0000000"),
            ("project-knowledge-manifest.md", manifest_rel, "aetheris-agents", None),
        ]
    )
    _commit(agents, manifest_rel, manifest_body)
    committed["project-knowledge-manifest.md"] = manifest_body

    # The mutation that a working-tree implementation would pass under, planted in
    # every fixture: HEAD and the tree disagree on every exported document. The
    # manifest itself is left clean — it is read as *data* from the path given, and
    # its own dirty case has a test of its own below.
    for repo, rel in (
        (agents, "CLAUDE.md"),
        (agents, "docs/research/long-original-name-2026-06.md"),
        (harness, "docs/runbook.md"),
    ):
        (repo / rel).write_text("WORKING TREE — must not reach the bundle\n", encoding="utf-8")

    repo_dirs = {"aetheris-agents": agents, "aetheris": harness}
    return agents / manifest_rel, repo_dirs, {k: v.encode() for k, v in committed.items()}


def _assemble(world, dest, **kwargs):
    manifest, repo_dirs, _ = world
    return assemble_export_bundle.assemble(dest, manifest, repo_dirs=repo_dirs, **kwargs)


def _bundle_docs(dest: Path) -> dict[str, bytes]:
    return {
        p.name: p.read_bytes()
        for p in dest.iterdir()
        if p.name != assemble_export_bundle.MARKER_NAME
    }


# --------------------------------------------------------------------------- #
# The export set                                                               #
# --------------------------------------------------------------------------- #


def test_bundle_carries_every_manifest_row_including_the_self_referential_one(
    bundle_world, tmp_path
):
    """The manifest is itself an exported document, and its row carries no hash.

    `drift_check`'s check 8 skips that row by design; an assembler that inherited the
    skip would build a bundle one document short and nothing would say so.
    """
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest) == 0
    assert sorted(_bundle_docs(dest)) == [
        "agents--CLAUDE.md",
        "harness--runbook.md",
        "project-knowledge-manifest.md",
        "renamed-brief.md",
    ]


def test_content_comes_from_committed_history_not_the_working_tree(bundle_world, tmp_path):
    """Every fixture file is dirty; the bundle must carry the committed bytes."""
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest) == 0
    _, _, committed = bundle_world
    for name, expected in committed.items():
        assert (dest / name).read_bytes() == expected


def test_export_names_come_from_the_manifest_not_from_the_path(bundle_world, tmp_path):
    """The mapping is data: this row's basename regenerates nothing like its name."""
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest) == 0
    assert (dest / "renamed-brief.md").exists()
    assert not (dest / "long-original-name-2026-06.md").exists()


def test_an_uncommitted_manifest_edit_bundles_the_committed_copy_and_says_so(
    bundle_world, tmp_path, capsys
):
    """The manifest drives assembly from disk and is bundled from HEAD — both, and they
    can disagree.

    This is not hypothetical: the 2026-08-14 boundary shipped exactly this state and
    recorded it (`docs/project-knowledge-manifest.md`, "the bundle's copy of it was the
    pre-update one, which is what byte-identical-to-HEAD meant at assembly time"). The
    behaviour is right — a bundle carries committed documents — but silence about it
    would let an operator believe the store received the edit they just made.
    """
    manifest, _, committed = bundle_world
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "\nAn uncommitted paragraph.\n", encoding="utf-8"
    )
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest) == 0
    assert (dest / "project-knowledge-manifest.md").read_bytes() == committed[
        "project-knowledge-manifest.md"
    ]
    # Not the bare word: `tmp_path` is named after this test, and the run prints the
    # destination path — so `"uncommitted" in out` passes with the warning deleted.
    assert "has uncommitted edits" in capsys.readouterr().out


def test_a_duplicate_export_name_is_refused_before_anything_is_written(tmp_path):
    """Two rows claiming one name would silently drop a document from the store."""
    agents = _init_repo(tmp_path / "agents")
    _commit(agents, "a.md", "a\n")
    _commit(agents, "b.md", "b\n")
    manifest = tmp_path / "manifest.md"
    manifest.write_text(
        _manifest_text(
            [
                ("same.md", "a.md", "aetheris-agents", "0000000"),
                ("same.md", "b.md", "aetheris-agents", "0000000"),
            ]
        ),
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    assert (
        assemble_export_bundle.assemble(dest, manifest, repo_dirs={"aetheris-agents": agents}) == 1
    )
    assert not dest.exists()


def test_a_source_missing_from_history_writes_no_partial_bundle(tmp_path):
    """A half-written directory looks like a bundle and is not one."""
    agents = _init_repo(tmp_path / "agents")
    _commit(agents, "a.md", "a\n")
    manifest = tmp_path / "manifest.md"
    manifest.write_text(
        _manifest_text(
            [
                ("a.md", "a.md", "aetheris-agents", "0000000"),
                ("gone.md", "never-committed.md", "aetheris-agents", "0000000"),
            ]
        ),
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    assert (
        assemble_export_bundle.assemble(dest, manifest, repo_dirs={"aetheris-agents": agents}) == 1
    )
    assert not dest.exists()


# --------------------------------------------------------------------------- #
# W1a — the destination                                                        #
# --------------------------------------------------------------------------- #


def test_a_non_empty_destination_is_refused_and_left_untouched(bundle_world, tmp_path):
    """The 2026-08-14 hazard: a previous boundary's bundle sitting at the target."""
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "agents--CLAUDE.md").write_text("PREVIOUS EXPORT\n", encoding="utf-8")

    assert _assemble(bundle_world, dest) == 1
    assert sorted(p.name for p in dest.iterdir()) == ["agents--CLAUDE.md"]
    assert (dest / "agents--CLAUDE.md").read_text(encoding="utf-8") == "PREVIOUS EXPORT\n"


def test_replace_moves_the_previous_bundle_aside_and_deletes_nothing(bundle_world, tmp_path):
    """The prior bundle is the only evidence of what was last uploaded."""
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "agents--CLAUDE.md").write_text("PREVIOUS EXPORT\n", encoding="utf-8")

    assert _assemble(bundle_world, dest, replace=True) == 0
    aside = dest.with_name("out.superseded.1")
    assert aside.is_dir()
    assert (aside / "agents--CLAUDE.md").read_text(encoding="utf-8") == "PREVIOUS EXPORT\n"
    assert (dest / "agents--CLAUDE.md").read_bytes() == bundle_world[2]["agents--CLAUDE.md"]


def test_a_second_replace_does_not_overwrite_the_first_aside(bundle_world, tmp_path):
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "agents--CLAUDE.md").write_text("EXPORT ONE\n", encoding="utf-8")
    assert _assemble(bundle_world, dest, replace=True) == 0
    assert _assemble(bundle_world, dest, replace=True) == 0

    assert (dest.with_name("out.superseded.1") / "agents--CLAUDE.md").read_text(
        encoding="utf-8"
    ) == "EXPORT ONE\n"
    assert (dest.with_name("out.superseded.2")).is_dir()


def test_an_empty_existing_destination_is_accepted(bundle_world, tmp_path):
    """Refusal keys on content, not on existence — mkdir'ing a target is not an error."""
    dest = tmp_path / "out"
    dest.mkdir()
    assert _assemble(bundle_world, dest) == 0


# --------------------------------------------------------------------------- #
# W1b — the U2 sweep                                                           #
# --------------------------------------------------------------------------- #


def test_an_unswept_bundle_says_so_in_the_bundle(bundle_world, tmp_path):
    """Terminal output scrolls away; the directory is what the operator uploads.

    Unswept now means both sweeps off — the pattern set is the default, so reaching this
    state takes `--no-patterns` and no needles.
    """
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest, patterns_file=None) == 0
    marker = dest / assemble_export_bundle.MARKER_NAME
    assert marker.exists()
    assert "NOT cleared for upload" in marker.read_text(encoding="utf-8")


def test_a_clean_sweep_writes_no_marker(bundle_world, tmp_path):
    needles = tmp_path / "needles.txt"
    needles.write_text("some-real-login\n# a comment\n\n", encoding="utf-8")
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest, needles_file=needles) == 0
    assert not (dest / assemble_export_bundle.MARKER_NAME).exists()


# --------------------------------------------------------------------------- #
# The pattern sweep (BL-160)                                                   #
# --------------------------------------------------------------------------- #


def test_the_pattern_sweep_runs_by_default_and_needs_no_corpus(bundle_world, tmp_path):
    """The whole point of R-F2: a bare run sweeps, with no operator-supplied anything.

    Before this, a bare run wrote the unswept marker, because the only sweep available
    needed a needle corpus nothing in the repo locates.
    """
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest) == 0
    assert not (dest / assemble_export_bundle.MARKER_NAME).exists()


def test_a_planted_in_class_string_fails_the_run_then_passes_when_removed(
    bundle_world, tmp_path
):
    """The positive control, as a test rather than as a one-off.

    A pattern set that has never fired is a pattern set nobody has tested. The planted
    string is synthetic — a login key/value pair of the shape a pasted API response has,
    with a value that is not anybody's login.
    """
    manifest, repo_dirs, _ = bundle_world
    planted = '{"login": "not-a-real-login-planted-by-a-test"}'
    target = repo_dirs["aetheris-agents"] / "CLAUDE.md"

    target.write_text(f"agents claude, committed\n{planted}\n", encoding="utf-8")
    _git(repo_dirs["aetheris-agents"], "add", "CLAUDE.md")
    _git(repo_dirs["aetheris-agents"], "commit", "-q", "-m", "plant")

    red = tmp_path / "red"
    assert _assemble(bundle_world, red) == 1, "the pattern set did not fire on a planted hit"
    assert (red / assemble_export_bundle.MARKER_NAME).exists()
    assert "FOUND 1 hit" in (red / assemble_export_bundle.MARKER_NAME).read_text(
        encoding="utf-8"
    )

    target.write_text("agents claude, committed\n", encoding="utf-8")
    _git(repo_dirs["aetheris-agents"], "add", "CLAUDE.md")
    _git(repo_dirs["aetheris-agents"], "commit", "-q", "-m", "unplant")

    green = tmp_path / "green"
    assert _assemble(bundle_world, green) == 0, "the restore did not restore"
    assert not (green / assemble_export_bundle.MARKER_NAME).exists()


def test_a_pattern_hit_is_redacted_unless_asked_for(bundle_world, tmp_path, capsys):
    """A packet quoting the sweep must not republish what the sweep exists to catch."""
    manifest, repo_dirs, _ = bundle_world
    secret = "planted-value-nobody-should-see"
    target = repo_dirs["aetheris-agents"] / "CLAUDE.md"
    target.write_text(f'{{"login": "{secret}"}}\n', encoding="utf-8")
    _git(repo_dirs["aetheris-agents"], "add", "CLAUDE.md")
    _git(repo_dirs["aetheris-agents"], "commit", "-q", "-m", "plant")

    assert _assemble(bundle_world, tmp_path / "redacted") == 1
    assert secret not in capsys.readouterr().err

    assert _assemble(bundle_world, tmp_path / "shown", show_matches=True) == 1
    assert secret in capsys.readouterr().err


def test_every_committed_pattern_compiles_and_carries_a_label():
    """The shipped set is the thing under test, not a fixture standing in for it."""
    patterns = assemble_export_bundle.load_patterns(assemble_export_bundle.DEFAULT_PATTERNS)
    assert len(patterns) >= 10
    for label, rx in patterns:
        assert label and not label.startswith("#"), label
        assert rx.pattern


def test_a_malformed_pattern_line_is_a_failure_not_a_skip(tmp_path):
    """A pattern set that silently drops a line is a gate that silently narrows."""
    bad = tmp_path / "patterns.txt"
    bad.write_text("label :: [unclosed\n", encoding="utf-8")
    with pytest.raises(ManifestError):
        assemble_export_bundle.load_patterns(bad)

    no_sep = tmp_path / "nosep.txt"
    no_sep.write_text("just a line with no separator\n", encoding="utf-8")
    with pytest.raises(ManifestError):
        assemble_export_bundle.load_patterns(no_sep)


def test_reserved_documentation_domains_are_excluded_and_only_those():
    """RFC 2606 / RFC 6761 addresses are the standard's designated non-addresses.

    The exclusion is scoped to exactly the reserved list, so the discriminating cases are
    the ones that must STILL match: a reserved name used as a subdomain of a real domain,
    and a name that merely resembles one. A wildcard would pass the first half of this
    test and fail the second.
    """
    email = dict(
        (label, rx)
        for label, rx in assemble_export_bundle.load_patterns(
            assemble_export_bundle.DEFAULT_PATTERNS
        )
    )["email address"]

    for excluded in (
        "ops@acme.example",              # RFC 2606 .example TLD — the live 2026-08-16 hit
        "billing@northwind.example",     # RFC 2606 .example TLD — the live 2026-08-16 hit
        "someone@example.com",
        "a@sub.example.org",
        "x@thing.invalid",
        "x@thing.test",
        "x@foo.localhost",
    ):
        assert not email.search(excluded), f"{excluded} should be excluded"

    for still_matches in (
        "real.person@bitloka.com",
        "ops@test.company.com",          # 'test' as a SUBDOMAIN is not reserved
        "ops@examples.com",              # 'examples' is not 'example'
        "ops@example.company.com",       # 'example' as a subdomain of a real domain
    ):
        assert email.search(still_matches), f"{still_matches} should still match"


def test_an_empty_pattern_file_is_refused_rather_than_read_as_a_clean_sweep(tmp_path):
    """Same vacuity the empty-needles test guards, one instrument over."""
    empty = tmp_path / "patterns.txt"
    empty.write_text("# only a comment\n", encoding="utf-8")
    with pytest.raises(ManifestError):
        assemble_export_bundle.load_patterns(empty)


def test_a_needle_in_the_bundle_fails_the_run_and_marks_it(bundle_world, tmp_path):
    needles = tmp_path / "needles.txt"
    needles.write_text("COMMITTED\n", encoding="utf-8")  # matches 'committed' case-insensitively
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest, needles_file=needles) == 1
    assert (dest / assemble_export_bundle.MARKER_NAME).exists()


def test_an_empty_needles_file_is_refused_rather_than_read_as_a_clean_sweep(
    bundle_world, tmp_path
):
    """A sweep over zero needles passes trivially and would clear the marker."""
    needles = tmp_path / "needles.txt"
    needles.write_text("# nothing but a comment\n", encoding="utf-8")
    dest = tmp_path / "out"
    assert _assemble(bundle_world, dest, needles_file=needles) == 1
    assert not dest.exists()


# --------------------------------------------------------------------------- #
# Determinism                                                                  #
# --------------------------------------------------------------------------- #


def test_two_runs_into_two_directories_are_byte_identical(bundle_world, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    assert _assemble(bundle_world, a) == 0
    assert _assemble(bundle_world, b) == 0
    assert {p.name: p.read_bytes() for p in a.iterdir()} == {
        p.name: p.read_bytes() for p in b.iterdir()
    }


# --------------------------------------------------------------------------- #
# The live repos                                                               #
# --------------------------------------------------------------------------- #


@pytest.mark.integration
@pytest.mark.skipif(not HARNESS_ROOT.exists(), reason="sibling harness checkout absent")
def test_the_live_bundle_reproduces_every_manifest_row_at_head(tmp_path):
    """The done-check's durable residue: 25 rows in, 25 documents out, all at HEAD.

    Compared against the preserved 2026-08-14 bundle in the packet; here against
    `git show HEAD:` because a /tmp artifact cannot be a committed test's fixture.

    **Swept off deliberately, and this is not the sweep being tuned.** This test's claim
    is composition — every manifest row in, one document out, bytes from HEAD — and the
    sweep's verdict is a different claim about the same directory. As of 2026-08-16 the
    live sweep is NOT clean (three RFC-2606 documentation addresses in `rig--runbook.md`,
    reported unadjudicated in that boundary's packet), so leaving the default on would
    make this test red for a reason it does not assert. The sweep's live verdict belongs
    to the boundary run and to whoever rules on those hits, not here.
    """
    from _manifest import REPO_DIRS, git_show, read_rows

    dest = tmp_path / "live"
    assert assemble_export_bundle.assemble(dest, patterns_file=None) == 0

    rows = read_rows()
    assert sorted(_bundle_docs(dest)) == sorted(r.export_name for r in rows)
    for row in rows:
        assert (dest / row.export_name).read_bytes() == git_show(
            REPO_DIRS[row.repo], row.repo_path
        ), f"{row.export_name} is not what HEAD holds"
