#!/usr/bin/env python3
"""
Re-pin the commit column of `docs/project-knowledge-manifest.md` (BL-002).

For each row of the export table, runs `git log -1 --format=%h -- <path>` in that row's
OWN repo — the same command `drift_check.py`'s check 8 compares the column against — and
rewrites the commit cell to what it returns.

**Nothing else in the manifest is touched.** Not its prose, not the deviation section,
and not the per-boundary sections: this script has no authority over the export narrative,
only over the fact each row states about git. The self-referential row keeps
`_(this export)_` — it is a placeholder rather than a commit by design, which is what keeps
the manifest from restaling itself.

**Two cells, one reading (BL-151, 2026-08-16).** `last changed` is re-derived here too, from
`git log -1 --format=%ad --date=short <commit>` on the commit this script just resolved —
not independently from the path. Until 2026-08-16 this script owned the commit cell and
disclaimed the date, `drift_check`'s check 8 read the commit cell and ignored the date, and
so the two could disagree with nothing in either repo able to say so. A row is now current
only when both cells are, and a date-only move is reported as one.

**The correctness property is idempotence**: run against a manifest already current, the
diff is empty. Anything else means the rewriter is moving something the derivation did
not ask it to.

The one thing this cannot tell you: check 8 and this script both establish that a pin is
*current*, never that the pinned content is *complete*. Read the pinned document against
what it should say — that is `CLAUDE.md` §Definition of done, not a step a script can do.

Usage:
  python3 scripts/repin_manifest.py [--manifest FILE] [--dry-run]

Exit codes:
  0 — manifest current, or rewritten (with --dry-run, no write either way)
  1 — the manifest could not be read, or a row's commit could not be derived
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from _manifest import (  # noqa: E402
    MANIFEST_MD,
    REPO_DIRS,
    SELF_COMMIT,
    ManifestError,
    git_commit_date,
    git_last_commit,
    read_rows,
)


def repin(
    manifest: Path = MANIFEST_MD,
    dry_run: bool = False,
    repo_dirs: dict[str, Path] | None = None,
) -> int:
    repo_dirs = repo_dirs or REPO_DIRS

    try:
        text = manifest.read_text(encoding="utf-8")
        rows = read_rows(manifest)
    except (ManifestError, OSError) as exc:
        print(f"[FAIL] manifest: {exc}", file=sys.stderr)
        return 1

    lines = text.splitlines(keepends=True)
    moved: list[tuple[str, str, str]] = []
    undeterminable: list[str] = []

    for row in rows:
        if row.commit is None:
            print(f"  {row.export_name:<40} {SELF_COMMIT} (self-referential row, left alone)")
            continue

        current = git_last_commit(repo_dirs[row.repo], row.repo_path)
        if current is None:
            print(
                f"[FAIL] {row.export_name}: git log returned nothing for "
                f"{row.repo}:{row.repo_path} — the path may not be committed",
                file=sys.stderr,
            )
            undeterminable.append(row.export_name)
            continue

        # The date is read from the commit just resolved, never independently from the
        # path — see `git_commit_date`. A row is current only when BOTH cells are.
        current_date = git_commit_date(repo_dirs[row.repo], current)
        if current_date is None:
            print(
                f"[FAIL] {row.export_name}: git log returned no date for commit "
                f"{current} in {row.repo} — refusing to rewrite the row",
                file=sys.stderr,
            )
            undeterminable.append(row.export_name)
            continue

        if current == row.commit and current_date == row.last_changed:
            print(f"  {row.export_name:<40} `{row.commit}` {row.last_changed} current")
            continue

        # Replace the commit and date cells together. Anchored on the row's own two
        # backticked neighbours so a hash that also appears in the path cannot be hit.
        old_cell = f"| `{row.commit}` | {row.last_changed} |"
        new_cell = f"| `{current}` | {current_date} |"
        line = lines[row.line_no - 1]
        if line.count(old_cell) != 1:
            print(
                f"[FAIL] {row.export_name}: line {row.line_no} does not carry its commit "
                f"cell exactly once — refusing to rewrite it",
                file=sys.stderr,
            )
            undeterminable.append(row.export_name)
            continue
        lines[row.line_no - 1] = line.replace(old_cell, new_cell)
        moved.append((row.export_name, row.commit, current))
        if current == row.commit:
            # Date-only move: the pin was current and the date was not. This is the
            # case nothing could report before BL-151's seed.
            print(
                f"  {row.export_name:<40} `{row.commit}` current, "
                f"date {row.last_changed} -> {current_date}"
            )
        else:
            print(
                f"  {row.export_name:<40} `{row.commit}` -> `{current}` "
                f"({row.last_changed} -> {current_date})"
            )

    if undeterminable:
        print(
            f"\nSummary: {len(undeterminable)} row(s) undeterminable — nothing written",
            file=sys.stderr,
        )
        return 1

    if not moved:
        print(f"\nSummary: {len(rows)} row(s), all current — manifest unchanged")
        return 0

    if dry_run:
        print(f"\nSummary: {len(moved)} row(s) would be re-pinned — --dry-run, nothing written")
        return 0

    manifest.write_text("".join(lines), encoding="utf-8")
    print(f"\nSummary: {len(moved)} row(s) re-pinned in {manifest}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_MD, help="manifest to re-pin")
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would move, write nothing"
    )
    args = parser.parse_args()

    return repin(args.manifest, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
