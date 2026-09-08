"""
Tests for scripts/gen_index.py and scripts/_frontmatter.py.

Every fixture tree is SYNTHETIC and written to tmp_path: the refusal cases are constructed
here and watched fail here, never by editing a tracked file (harness `CLAUDE.md`
**Silent-wrong-answer** — "construct the broken state and watch the check fail in it, as
part of writing the check"). The one test that reads the sibling research tree is marked
`integration` on the standing criterion: it would silently skip in a fresh clone with no
sibling checkout and no PyYAML.
"""

import subprocess
import sys
from pathlib import Path

import pytest

import gen_index
from _frontmatter import FrontmatterError, first_heading, read_document

REPO_ROOT = Path(__file__).resolve().parent.parent
GEN = REPO_ROOT / "scripts" / "gen_index.py"


def _doc(title, description="One line about it.", type_="brief", extra=""):
    return (
        "---\n"
        f"type: {type_}\n"
        f'title: "{title}"\n'
        f"description: {description}\n"
        f"{extra}"
        "---\n"
        f"# {title}\n\nBody.\n"
    )


def _good_tree(tmp_path):
    tree = tmp_path / "research"
    tree.mkdir(parents=True)
    (tree / "b-second.md").write_text(_doc("Second brief", "About the second."), encoding="utf-8")
    (tree / "a-first.md").write_text(_doc("First brief", "About the first."), encoding="utf-8")
    (tree / "README.md").write_text(_doc("Research", "The charter.", type_="readme"), encoding="utf-8")
    return tree


def _run(*args):
    return subprocess.run(
        [sys.executable, str(GEN), *args], capture_output=True, text=True, cwd=REPO_ROOT
    )


# --------------------------------------------------------------------------- #
# _frontmatter                                                                 #
# --------------------------------------------------------------------------- #

def test_read_document_no_fence_is_none_not_error():
    doc = read_document("# Title\n\nbody\n")
    assert doc.frontmatter is None
    assert doc.body.startswith("# Title")


def test_read_document_parses_scalars_nested_map_and_list():
    text = (
        '---\ntype: brief\ntitle: "Quoted: \\"q\\" — dash"\n'
        "generated:\n  by: research-session\n  at: 2026-06-24\n"
        "sources:\n  - one\n  - two\n---\n# Quoted\n"
    )
    doc = read_document(text)
    assert doc.frontmatter == {
        "type": "brief",
        "title": 'Quoted: "q" — dash',
        "generated": {"by": "research-session", "at": "2026-06-24"},
        "sources": ["one", "two"],
    }
    assert first_heading(doc.body) == "Quoted"


@pytest.mark.parametrize(
    "block",
    [
        "type: brief\ntitle: unterminated \"quote\n",   # not actually unterminated — plain w/ quote inside
    ],
)
def test_plain_scalar_may_contain_a_quote_mid_string(block):
    fm = read_document(f"---\n{block}---\n").frontmatter
    assert fm["title"] == 'unterminated "quote'


@pytest.mark.parametrize(
    "block, why",
    [
        ("type: brief\n  orphan: x\n", "indented line with no parent"),
        ("type: brief\ntype: again\n", "duplicate key"),
        ("generated:\n", "container with no entries"),
        ("title: [flow, list]\n", "unsupported flow form"),
        ("title: 'unterminated\n", "unterminated single quote"),
        ("just prose\n", "line that is not key: value"),
    ],
)
def test_frontmatter_errors_are_raised_not_guessed(block, why):
    with pytest.raises(FrontmatterError):
        read_document(f"---\n{block}---\n")


def test_open_fence_without_close_is_error():
    with pytest.raises(FrontmatterError):
        read_document("---\ntype: brief\n# no closing fence\n")


# --------------------------------------------------------------------------- #
# generation                                                                   #
# --------------------------------------------------------------------------- #

def test_generate_orders_by_path_and_lifts_title_and_description(tmp_path):
    tree = _good_tree(tmp_path)
    text = gen_index.generate(tree)
    entries = [l for l in text.splitlines() if l.startswith("- [")]
    assert entries == [
        "- [Research](README.md) - The charter.",
        "- [First brief](a-first.md) - About the first.",
        "- [Second brief](b-second.md) - About the second.",
    ]
    assert text.startswith("---\ntype: index\nokf_version: \"0.2\"\n")
    assert "generated — do not hand-edit" in text
    assert "index.md" not in "".join(entries), "the index must not index itself"


def test_generate_is_deterministic_and_independent_of_creation_order(tmp_path):
    tree_a = _good_tree(tmp_path / "x")
    # Same documents, created in the opposite order, different mtimes.
    tree_b = (tmp_path / "y" / "research")
    tree_b.mkdir(parents=True)
    for name in ("README.md", "a-first.md", "b-second.md"):
        tree_b.joinpath(name).write_text((tree_a / name).read_text(encoding="utf-8"), encoding="utf-8")
    assert gen_index.generate(tree_a) == gen_index.generate(tree_b)
    assert gen_index.generate(tree_a) == gen_index.generate(tree_a)


def test_generate_skips_the_output_file_even_when_it_already_exists(tmp_path):
    tree = _good_tree(tmp_path)
    first = gen_index.generate(tree)
    (tree / "index.md").write_text(first, encoding="utf-8")
    assert gen_index.generate(tree) == first


def test_link_text_escapes_square_brackets(tmp_path):
    tree = tmp_path / "t"
    tree.mkdir()
    (tree / "a.md").write_text(_doc("Title [with] brackets"), encoding="utf-8")
    text = gen_index.generate(tree)
    assert "- [Title \\[with\\] brackets](a.md) - One line about it." in text


# --------------------------------------------------------------------------- #
# the header's fetch instruction (2026-09-08) — present, repo derived per tree, #
# deterministic                                                                #
# --------------------------------------------------------------------------- #

FETCH_SENTENCE = (
    "Documents listed here are on-demand. When their content is needed, FETCH them via the "
    "github-mcp connector — repository {repo} (this tree), branch main, path as written — and "
    "cite the served commit SHA. Do not answer from kernel summaries when the source is one "
    "fetch away. If a fetch fails, say so and answer from the kernel with the gap named."
)


def _git_tree(root, remote_url):
    """A good tree inside its own git checkout whose `origin` is `remote_url`."""
    tree = _good_tree(root)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "remote", "add", "origin", remote_url], check=True)
    return tree


def _fetch_lines(text):
    return [l for l in text.splitlines() if l.startswith("Documents listed here are on-demand.")]


def test_header_carries_the_fetch_instruction_verbatim_above_the_entries(tmp_path):
    tree = _git_tree(tmp_path, "git@github.com:vishal-h/aetheris-agents.git")
    text = gen_index.generate(tree)
    lines = text.splitlines()
    fetch = _fetch_lines(text)
    assert fetch == [FETCH_SENTENCE.format(repo="vishal-h/aetheris-agents")]
    assert lines.index(fetch[0]) < min(i for i, l in enumerate(lines) if l.startswith("- ["))
    assert lines.index(fetch[0]) > lines.index("# Index: research")


@pytest.mark.parametrize(
    "remote, slug",
    [
        ("git@github.com:vishal-h/aetheris.git", "vishal-h/aetheris"),
        ("git@github.com:vishal-h/aetheris-agents.git", "vishal-h/aetheris-agents"),
        ("https://github.com/vishal-h/aetheris.git", "vishal-h/aetheris"),
        ("https://github.com/vishal-h/aetheris-agents", "vishal-h/aetheris-agents"),
    ],
)
def test_repository_line_is_derived_from_the_tree_not_hardcoded(tmp_path, remote, slug):
    tree = _git_tree(tmp_path, remote)
    assert gen_index._repo_slug(tree) == slug
    assert _fetch_lines(gen_index.generate(tree)) == [FETCH_SENTENCE.format(repo=slug)]


def test_two_trees_with_identical_documents_differ_only_in_the_repository_line(tmp_path):
    harness = _git_tree(tmp_path / "h", "git@github.com:vishal-h/aetheris.git")
    agents = _git_tree(tmp_path / "a", "git@github.com:vishal-h/aetheris-agents.git")
    diff = [
        (x, y) for x, y in zip(gen_index.generate(harness).splitlines(),
                               gen_index.generate(agents).splitlines()) if x != y
    ]
    assert diff == [(FETCH_SENTENCE.format(repo="vishal-h/aetheris"),
                     FETCH_SENTENCE.format(repo="vishal-h/aetheris-agents"))]


def test_repository_line_falls_back_to_an_explicit_placeholder_outside_a_checkout(tmp_path):
    tree = _good_tree(tmp_path)          # no git init: nothing to derive from
    assert gen_index._repo_slug(tree) is None
    assert _fetch_lines(gen_index.generate(tree)) == [
        FETCH_SENTENCE.format(repo=gen_index.REPO_UNRESOLVED)
    ]
    result = _run(str(tree))
    assert result.returncode == 0
    assert "repository not derivable" in result.stderr
    assert gen_index.REPO_UNRESOLVED in (tree / "index.md").read_text(encoding="utf-8")


def test_cli_repo_override_names_the_given_repository(tmp_path):
    tree = _git_tree(tmp_path, "git@github.com:vishal-h/aetheris.git")
    assert _run(str(tree), "--repo", "someone/elsewhere").returncode == 0
    text = (tree / "index.md").read_text(encoding="utf-8")
    assert _fetch_lines(text) == [FETCH_SENTENCE.format(repo="someone/elsewhere")]
    assert "vishal-h/aetheris" not in text


def test_regenerated_index_with_fetch_header_is_byte_identical_across_runs(tmp_path):
    tree = _git_tree(tmp_path, "git@github.com:vishal-h/aetheris.git")
    assert _run(str(tree)).returncode == 0
    first = (tree / "index.md").read_bytes()
    assert _run(str(tree)).returncode == 0
    assert (tree / "index.md").read_bytes() == first
    assert _run(str(tree), "--check").returncode == 0
    assert b"vishal-h/aetheris (this tree)" in first


# --------------------------------------------------------------------------- #
# refusal (§1.2) — every case lists the document and writes nothing            #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "content, fragment",
    [
        ("# No frontmatter at all\n\nbody\n", "no frontmatter"),
        ("---\ntype: brief\ntitle: \"T\"\n---\n# T\n", "description"),
        ("---\ntype: brief\ndescription: d\n---\n# T\n", "title"),
        ("---\ntype: \"\"\ntitle: \"T\"\ndescription: d\n---\n# T\n", "type"),
        ("---\ntype: brief\ntitle: \"T\"\ndescription: d\n---\n# Different heading\n", "H1 differs"),
        ("---\ntype: brief\ntitle: \"T\"\ndescription: d\nbroken line\n---\n# T\n", "unreadable"),
        ("---\ntype: brief\ntitle: \"T\"\ndescription: d\n# never closed\n", "unreadable"),
    ],
)
def test_refuses_on_each_missing_frontmatter_shape(tmp_path, content, fragment):
    tree = _good_tree(tmp_path)
    (tree / "z-bad.md").write_text(content, encoding="utf-8")
    with pytest.raises(gen_index.Refusal) as exc:
        gen_index.generate(tree)
    problems = dict(exc.value.problems)
    assert list(problems) == ["z-bad.md"]
    assert fragment in problems["z-bad.md"]


def test_refusal_lists_every_offender_not_just_the_first(tmp_path):
    tree = _good_tree(tmp_path)
    (tree / "y-bad.md").write_text("# no frontmatter\n", encoding="utf-8")
    (tree / "z-bad.md").write_text("---\ntype: brief\ntitle: \"T\"\n---\n# T\n", encoding="utf-8")
    with pytest.raises(gen_index.Refusal) as exc:
        gen_index.generate(tree)
    assert [rel for rel, _ in exc.value.problems] == ["y-bad.md", "z-bad.md"]


def test_cli_refusal_exits_1_writes_nothing_and_names_the_file(tmp_path):
    tree = _good_tree(tmp_path)
    (tree / "z-bad.md").write_text("# no frontmatter\n", encoding="utf-8")
    result = _run(str(tree))
    assert result.returncode == 1, result.stderr
    assert "[REFUSED]" in result.stderr
    assert "z-bad.md: no frontmatter" in result.stderr
    assert not (tree / "index.md").exists(), "a refused run must write nothing"


def test_cli_refusal_does_not_overwrite_an_existing_index(tmp_path):
    tree = _good_tree(tmp_path)
    assert _run(str(tree)).returncode == 0
    before = (tree / "index.md").read_bytes()
    (tree / "z-bad.md").write_text("# no frontmatter\n", encoding="utf-8")
    assert _run(str(tree)).returncode == 1
    assert (tree / "index.md").read_bytes() == before


# --------------------------------------------------------------------------- #
# CLI: write, --check, usage                                                   #
# --------------------------------------------------------------------------- #

def test_cli_writes_index_and_reports_entry_count(tmp_path):
    tree = _good_tree(tmp_path)
    result = _run(str(tree))
    assert result.returncode == 0, result.stderr
    assert "3 entries" in result.stdout
    assert (tree / "index.md").read_text(encoding="utf-8") == gen_index.generate(tree)


def test_cli_check_passes_when_current_and_fails_when_stale_or_absent(tmp_path):
    tree = _good_tree(tmp_path)
    assert _run(str(tree), "--check").returncode == 1        # absent
    assert _run(str(tree)).returncode == 0
    assert _run(str(tree), "--check").returncode == 0        # current
    (tree / "c-third.md").write_text(_doc("Third"), encoding="utf-8")
    result = _run(str(tree), "--check")
    assert result.returncode == 1                             # stale
    assert "regenerate" in result.stderr
    assert "Third" not in (tree / "index.md").read_text(encoding="utf-8"), "--check must not write"


def test_cli_label_names_the_tree_in_the_heading(tmp_path):
    tree = _good_tree(tmp_path)
    assert _run(str(tree), "--label", "docs/aetheris/research").returncode == 0
    text = (tree / "index.md").read_text(encoding="utf-8")
    assert "# Index: docs/aetheris/research" in text


def test_cli_missing_tree_is_usage_exit_2(tmp_path):
    assert _run(str(tmp_path / "absent")).returncode == 2


# --------------------------------------------------------------------------- #
# The reader agrees with a real YAML parser on the committed research tree     #
# --------------------------------------------------------------------------- #

@pytest.mark.integration
def test_frontmatter_reader_matches_pyyaml_on_the_research_tree():
    """Needs the sibling harness checkout AND PyYAML: `integration` on both counts."""
    yaml = pytest.importorskip("yaml")
    tree = REPO_ROOT.parent / "aetheris" / "docs" / "aetheris" / "research"
    if not tree.is_dir():
        pytest.skip("sibling harness checkout not present")
    compared = 0
    for path in sorted(tree.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        doc = read_document(text)
        assert doc.frontmatter is not None, f"{path.name} has no frontmatter"
        block = text.split("---\n", 2)[1]
        # BaseLoader keeps every scalar a string, which is this reader's contract;
        # safe_load would resolve `2026-06-24` to a date and compare the wrong thing.
        assert doc.frontmatter == yaml.load(block, Loader=yaml.BaseLoader), path.name
        compared += 1
    assert compared > 0
