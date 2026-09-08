#!/usr/bin/env python3
"""
Generate `index.md` for an indexed tree from each document's frontmatter.

    python3 scripts/gen_index.py TREE [--output FILE] [--check]

The hybrid-context design (harness `docs/aetheris/research/hybrid-context-design-2026-08.md`
§1, §1.2) makes a generated, OKF-conformant `index.md` the retrieval map of every tree that
lives on the `on-demand` surface: one entry per document, `[title](path) - description`,
title and description lifted from the document's own frontmatter. This script is that
generator. It is deterministic — the same tree at the same content produces the same bytes,
in an ordering that depends on nothing but the documents' relative paths — so a committed
index that no longer matches the tree is *drift*, and `drift_check.py`'s `index_integrity`
arm (§1.1) is what detects it between runs.

**Refusal is the contract (§1.2).** A document in the tree that lacks the frontmatter the
index needs is not skipped, not logged, and not indexed with a placeholder: the run REFUSES,
names every offending document and what it lacks, writes nothing, and exits 1. A brief
without a `description` is invisible to retrieval, and the reader of a miss caused that way
gets a confident answer assembled from whatever did index, experiences no miss, and never
learns the right brief existed — so invisibility is a build failure here, at generation time,
rather than a consequence discovered later. Required per document: parseable frontmatter,
non-empty `type` (the OKF conformance bar), `title`, `description`. When the body carries an
H1, it must equal `title` — the frontmatter title is a second surface stating what the
heading determines, and this is the check that keeps the two from drifting silently.

**The header carries a fetch instruction (2026-09-08).** An index that only *lists* on-demand
documents was measured to produce zero connector fetches in ten probes — the store said
on-demand without saying fetch. So every generated index states, above its entries, that the
documents are fetched via the github-mcp connector, names the repository, and says what to do
on a miss. The repository is DERIVED from the tree being indexed — the `origin` remote of the
checkout containing it — never hardcoded, so an agents-repo tree names `vishal-h/aetheris-agents`
and a harness tree `vishal-h/aetheris`. `--repo OWNER/NAME` overrides the derivation; when
neither is available the line carries an explicit placeholder and the CLI warns on stderr.

Exit codes:
  0 — index written (or, with --check, the committed index already equals the generated one)
  1 — refusal (frontmatter missing/unreadable/incomplete, or H1 ≠ title), or --check mismatch
  2 — usage: TREE is not a directory
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from _frontmatter import FrontmatterError, first_heading, read_document  # noqa: E402

REQUIRED_FIELDS = ("type", "title", "description")
GENERATOR = "scripts/gen_index.py"
OKF_VERSION = "0.2"

# The fetch instruction every generated index carries above its entries. `{repo}` is the
# owner/name of the checkout containing the indexed tree (see `_repo_slug`).
FETCH_INSTRUCTION = (
    "Documents listed here are on-demand. When their content is needed, FETCH them via the "
    "github-mcp connector — repository {repo} (this tree), branch main, path as written — and "
    "cite the served commit SHA. Do not answer from kernel summaries when the source is one "
    "fetch away. If a fetch fails, say so and answer from the kernel with the gap named."
)
REPO_UNRESOLVED = "<unresolved: not inside a git checkout with a GitHub origin remote; pass --repo OWNER/NAME>"
_GITHUB_REMOTE_RE = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


class Refusal(Exception):
    """One or more documents cannot be indexed; `.problems` lists every one."""

    def __init__(self, problems: list[tuple[str, str]]):
        super().__init__(f"{len(problems)} document(s) refused")
        self.problems = problems


def _escape_link_text(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")


def _yaml_quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def collect_entries(tree: Path, output: Path) -> list[tuple[str, str, str]]:
    """(relative path, title, description) for every markdown document under `tree`.

    Sorted by relative path — the only ordering that depends on nothing but the tree.
    Raises Refusal listing every document that cannot be indexed, never just the first.
    """
    problems: list[tuple[str, str]] = []
    entries: list[tuple[str, str, str]] = []
    output_resolved = output.resolve()
    for path in sorted(tree.rglob("*.md"), key=lambda p: p.relative_to(tree).as_posix()):
        if path.resolve() == output_resolved:
            continue
        rel = path.relative_to(tree).as_posix()
        try:
            doc = read_document(path.read_text(encoding="utf-8"))
        except FrontmatterError as exc:
            problems.append((rel, f"frontmatter unreadable: {exc}"))
            continue
        if doc.frontmatter is None:
            problems.append((rel, "no frontmatter (file does not open with a `---` fence)"))
            continue
        fm = doc.frontmatter
        missing = [
            f for f in REQUIRED_FIELDS
            if not isinstance(fm.get(f), str) or not fm.get(f, "").strip()
        ]
        if missing:
            problems.append((rel, "missing or empty required field(s): " + ", ".join(missing)))
            continue
        h1 = first_heading(doc.body)
        if h1 is not None and h1 != fm["title"]:
            problems.append((rel, f"H1 differs from frontmatter title: {h1!r} vs {fm['title']!r}"))
            continue
        entries.append((rel, fm["title"], fm["description"]))
    if problems:
        raise Refusal(problems)
    return entries


def render_index(
    tree_label: str, regen_command: str, entries: list[tuple[str, str, str]], repo: str | None = None
) -> str:
    lines = [
        "---",
        "type: index",
        f"okf_version: {_yaml_quote(OKF_VERSION)}",
        f"title: {_yaml_quote('Index: ' + tree_label)}",
        "description: "
        + _yaml_quote(
            f"Generated retrieval map of {tree_label}: one entry per document, "
            f"title and description lifted from each document's frontmatter."
        ),
        "generated:",
        f"  by: {GENERATOR}",
        "---",
        f"# Index: {tree_label}",
        "",
        "<!-- generated — do not hand-edit. This file is produced by "
        f"`{GENERATOR}` from each document's frontmatter; edit the document, then regenerate: "
        f"`{regen_command}`. It carries no timestamp because the same tree must produce the "
        "same bytes. Entry format: [title](path) - description. -->",
        "",
        FETCH_INSTRUCTION.format(repo=repo or REPO_UNRESOLVED),
        "",
    ]
    for rel, title, description in entries:
        lines.append(f"- [{_escape_link_text(title)}]({rel}) - {description}")
    lines.append("")
    return "\n".join(lines)


def generate(
    tree: Path, output: Path | None = None, tree_label: str | None = None, repo: str | None = None
) -> str:
    output = output or (tree / "index.md")
    label = tree_label or tree.name
    entries = collect_entries(tree, output)
    regen = f"python3 {GENERATOR} <path-to>/{label}"
    return render_index(label, regen, entries, repo or _repo_slug(tree))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tree", help="directory to index")
    parser.add_argument("--output", help="where to write (default: TREE/index.md)")
    parser.add_argument(
        "--label",
        help="tree label used in the heading (default: the tree's repo-relative path when "
             "TREE is inside a git checkout, else its directory name)",
    )
    parser.add_argument(
        "--repo",
        help="owner/name named in the header's fetch instruction (default: derived from the "
             "`origin` remote of the git checkout containing TREE)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 unless the existing index equals what would be generated",
    )
    args = parser.parse_args(argv)

    tree = Path(args.tree)
    if not tree.is_dir():
        print(f"[FAIL] {tree} is not a directory", file=sys.stderr)
        return 2
    output = Path(args.output) if args.output else tree / "index.md"
    label = args.label or _repo_relative_label(tree)
    repo = args.repo or _repo_slug(tree)
    if repo is None:
        print(f"[WARN] {tree}: repository not derivable from an origin remote — the fetch "
              f"instruction will name {REPO_UNRESOLVED}; pass --repo OWNER/NAME", file=sys.stderr)

    try:
        text = generate(tree, output, label, repo)
    except Refusal as exc:
        print(f"[REFUSED] {len(exc.problems)} document(s) in {tree} cannot be indexed; "
              f"nothing written:", file=sys.stderr)
        for rel, why in exc.problems:
            print(f"  {rel}: {why}", file=sys.stderr)
        return 1

    if args.check:
        existing = output.read_text(encoding="utf-8") if output.exists() else None
        if existing == text:
            print(f"[OK] {output} is current ({len(text.splitlines())} lines)")
            return 0
        state = "absent" if existing is None else "differs from the generated index"
        print(f"[FAIL] {output} {state} — regenerate it", file=sys.stderr)
        return 1

    output.write_text(text, encoding="utf-8")
    n = sum(1 for line in text.splitlines() if line.startswith("- ["))
    print(f"[OK] wrote {output}: {n} entr{'y' if n == 1 else 'ies'}")
    return 0


def _repo_slug(tree: Path) -> str | None:
    """`owner/name` from the `origin` remote of the checkout containing `tree`, else None.

    Derived, never hardcoded: an agents-repo tree names vishal-h/aetheris-agents and a harness
    tree vishal-h/aetheris because that is what each checkout's remote says. ssh and https
    forms both parse; a trailing `.git` is dropped.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(tree), "remote", "get-url", "origin"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    m = _GITHUB_REMOTE_RE.search(result.stdout.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _repo_relative_label(tree: Path) -> str:
    """`docs/aetheris/research` rather than `research` when a git root is above the tree."""
    resolved = tree.resolve()
    for parent in [resolved, *resolved.parents]:
        if (parent / ".git").exists():
            return resolved.relative_to(parent).as_posix() if parent != resolved else resolved.name
    return resolved.name


if __name__ == "__main__":
    sys.exit(main())
