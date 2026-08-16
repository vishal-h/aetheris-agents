"""Shared reader for `docs/project-knowledge-manifest.md`'s export table.

Two CLIs consume it — `assemble_export_bundle.py` (source → export name) and
`repin_manifest.py` (commit column) — and they must agree on which lines are rows,
so the parser lives here rather than in either of them.

**The table is the sole authority for the source→export-name mapping**, and there is no
rule to fall back on. Some export names are editorial and no basename rule regenerates
them — `docs/rig/milestones/bl-007/README.md` exports as `rig--bl-007-milestone.md`, and
every one of the harness research briefs is renamed
(`docs/aetheris/research/jiyi-memory-service-2026-06.md` → `aetheris--jiyi-brief.md`).
Even the prefix is editorial: `docs/rig/specs.md` takes one and `docs/agent-creation-guide.md`
does not. So the mapping is data and stays data.

**Row shape is not negotiable**, because `drift_check.py`'s check 8 parses the same
table with a regex of its own (`scripts/drift_check.py:580-584`) that requires single
spaces around the pipes and backticks on the first two cells. `ROW_RE` below is that
regex widened to capture all five cells — anything check 8 parses, this parses.

**One deliberate divergence from check 8.** The self-referential row carries
`_(this export)_` in its commit column instead of a hash; check 8's regex does not match
it, by design, so the manifest cannot restale itself. This parser *does* return it, with
`commit=None`, because that row names a real file that belongs in the bundle — the
manifest is part of the export set. A parser that inherited check 8's skip would build a
bundle one document short and no assertion here would notice.
"""

import re
import subprocess
from pathlib import Path
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent
HARNESS_ROOT = REPO_ROOT.parent / "aetheris"
MANIFEST_MD = REPO_ROOT / "docs" / "project-knowledge-manifest.md"

REPO_DIRS = {
    "aetheris-agents": REPO_ROOT,
    "aetheris": HARNESS_ROOT,
}

# The literal the self-referential row carries in its commit column.
SELF_COMMIT = "_(this export)_"

HEADER = "| export name | repo path | repo | commit | last changed |"

# `| `name` | `repo/path` | repo | `abc1234` | YYYY-MM-DD |`, and the self row's
# unbackticked `_(this export)_` in the commit position.
ROW_RE = re.compile(
    r"^\| `([^`]+)` \| `([^`]+)` \| (\S+) \| (?:`([0-9a-f]{5,})`|"
    + re.escape(SELF_COMMIT)
    + r") \| (\S+) \|$"
)


class Row(NamedTuple):
    export_name: str
    repo_path: str
    repo: str
    commit: str | None  # None for the self-referential row
    last_changed: str
    line_no: int  # 1-based, for the rewriter and for error messages


class ManifestError(Exception):
    """The table could not be read as a table — never a silently short row list."""


def parse_rows(text: str) -> list[Row]:
    """Every data row of the one export table, in file order.

    Bounded to the table rather than swept over the whole file: the manifest's prose
    carries several other pipe tables — the per-boundary `row | repo | was | now`
    tables — and a sweep would have to rely on those happening not to match.
    """
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == HEADER)
    except StopIteration:
        raise ManifestError(f"export-table header not found: {HEADER!r}") from None

    if start + 1 >= len(lines) or not lines[start + 1].startswith("|-"):
        raise ManifestError("export-table header is not followed by a separator row")

    rows: list[Row] = []
    for offset, line in enumerate(lines[start + 2 :], start=start + 3):
        if not line.startswith("|"):
            break
        m = ROW_RE.match(line)
        if not m:
            raise ManifestError(f"line {offset}: unparseable export-table row: {line!r}")
        name, path, repo, commit, last_changed = m.groups()
        if repo not in REPO_DIRS:
            raise ManifestError(f"line {offset}: unknown repo {repo!r} for {path}")
        rows.append(Row(name, path, repo, commit, last_changed, offset))

    if not rows:
        raise ManifestError("zero data rows parsed from the export table")
    return rows


def read_rows(manifest: Path = MANIFEST_MD) -> list[Row]:
    return parse_rows(manifest.read_text(encoding="utf-8"))


def repo_dir(row: Row, repo_dirs: dict[str, Path] | None = None) -> Path:
    return (repo_dirs or REPO_DIRS)[row.repo]


def git_show(repo: Path, path: str, rev: str = "HEAD") -> bytes:
    """`git show <rev>:<path>` as bytes, from committed history and never the tree.

    Bytes rather than text: the bundle is a copy, so nothing here may re-encode or
    normalise line endings on the way through.
    """
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=repo,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise ManifestError(
            f"git show {rev}:{path} failed in {repo}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout


def git_last_commit(repo: Path, path: str) -> str | None:
    """`git log -1 --format=%h -- <path>`, the exact command check 8 compares against."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", path],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def git_commit_date(repo: Path, commit: str) -> str | None:
    """`git log -1 --format=%ad --date=short <commit>` — the date OF a resolved commit.

    Deliberately keyed on the commit rather than on the path. `git_last_commit` above
    runs the exact command check 8 compares against; this takes that command's own
    answer and asks when it landed, so the manifest's `commit` and `last changed` cells
    are two readings of one object and cannot drift apart. Keying this on the path
    instead would make them two independent derivations, which is the arrangement that
    let them disagree in the first place (BL-151, 2026-08-16).
    """
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=short", commit],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def git_head(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
