#!/usr/bin/env python3
"""
Deterministic assembler for the Claude.ai project-knowledge export bundle (BL-002).

Reads `docs/project-knowledge-manifest.md` as the sole authority for which documents are
exported and under what name, reads each one's content from `git show HEAD:<path>` in the
owning repo, and writes the flat bundle into the directory given as an argument.

Deterministic given the two repos' HEADs: no timestamps, no working-tree reads, no
directory ordering — same HEADs and same manifest, byte-identical bundle.

Two things this script will not do silently:

  * **Write into a directory that already has content.** The 2026-08-14 export found a
    complete bundle from the previous boundary sitting at the target. Writing into it
    would have produced correctly-named, parseable files from two exports with nothing
    distinguishing them. So a non-empty destination is refused; `--replace` moves the
    existing directory aside to `<dest>.superseded.<n>` and says where it went. Nothing
    here deletes: the previous bundle is the only evidence of what was last uploaded.

  * **Emit a bundle that presents as ready to upload.** The bundle leaves the machine,
    and the U2 scrub sweep is what stands between it and a project. The sweep runs BY
    DEFAULT, against the committed pattern set in `scripts/u2_patterns.txt`, which also
    carries the class's authoritative statement. Only a clean sweep leaves no marker.

    Patterns rather than values, ruled 2026-08-16 (BL-160). A needle list is a
    deanonymisation key, so it cannot be committed, so it had to be derived at run time
    from raw captures — and no such corpus exists in this repo or is located by it. The
    value sweep was therefore unrunnable in practice and its green said nothing. A
    pattern set is not disclosure: it commits, it runs anywhere, it needs no corpus.
    `--needles FILE` survives beside it as an additive value sweep for an operator who
    does hold captures; `--no-patterns` disables the default set, and then a run with no
    needles is unswept and says so.

    What a clean sweep claims is NARROW: no text in the bundle matches these patterns.
    Not "no identifying content" — `u2_patterns.txt` enumerates the under-reach.

Usage:
  python3 scripts/assemble_export_bundle.py DEST [--manifest FILE] [--replace]
                                                 [--patterns FILE | --no-patterns]
                                                 [--needles FILE] [--show-matches]

Exit codes:
  0 — bundle written from every manifest row, sweep clean (or not run)
  1 — destination refused, a source could not be read, or the U2 sweep hit
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from _manifest import (  # noqa: E402
    MANIFEST_MD,
    REPO_DIRS,
    SCRIPT_DIR,
    ManifestError,
    git_head,
    git_show,
    read_rows,
)

DEFAULT_PATTERNS = SCRIPT_DIR / "u2_patterns.txt"
PATTERN_SEP = " :: "

MARKER_NAME = "_UNSWEPT-DO-NOT-UPLOAD.txt"

MARKER_BODY = """\
This bundle is NOT cleared for upload. Do not upload it.

U2 — the export scrub class — covers anything identifying an account, the people in
it, or its internal structure: organisation and repository names, logins, display
names, numeric user and organisation ids, node ids, profile and avatar URLs, every
one of the fifteen *_url fields, email addresses, and any token-shaped string.

The authoritative statement of the class, its pattern set, and the enumeration of
what the patterns do NOT reach is scripts/u2_patterns.txt. (The class was first
written at cloudcost/docs/m6-t2-implementation-notes.md §U2, which is a milestone
working artifact and travels nowhere; that file is now the historical record of how
the class was reached, not its home.)

This file is here for one of two reasons, and the last line says which:

  * the sweep RAN and HIT — a human adjudicates the hits; do not re-run with the
    matching pattern removed, because a pattern dropped for firing is a gate
    quietly narrowed; or
  * the sweep was NOT RUN, because --no-patterns was passed with no --needles.

A clean sweep writes no marker at all. If you are holding raw captures, --needles
<untracked-file> sweeps literal identifiers in ADDITION to the patterns — and delete
that file afterwards: it is a deanonymisation key, and leaving it beside the thing it
deanonymises is the mistake m6 t3 recorded making.

Assembled from:
"""


def _refuse_or_clear(dest: Path, replace: bool) -> tuple[Path | None, str | None]:
    """Resolve the destination. Returns (moved_to, error)."""
    if not dest.exists():
        return None, None
    if not dest.is_dir():
        return None, f"destination exists and is not a directory: {dest}"

    entries = sorted(p.name for p in dest.iterdir())
    if not entries:
        return None, None

    if not replace:
        shown = ", ".join(entries[:5]) + (f", … (+{len(entries) - 5})" if len(entries) > 5 else "")
        return None, (
            f"destination is not empty ({len(entries)} entries: {shown}) — refusing to "
            f"merge two exports into one directory. Re-run with --replace to move it "
            f"aside, or name an empty directory."
        )

    n = 1
    while (aside := dest.with_name(f"{dest.name}.superseded.{n}")).exists():
        n += 1
    dest.rename(aside)
    return aside, None


def _sweep(files: dict[str, bytes], needles: list[str]) -> list[tuple[str, str]]:
    """Every (export name, needle) pair where the needle appears in the bundle."""
    hits = []
    for name in sorted(files):
        text = files[name].decode("utf-8", "replace")
        lowered = text.lower()
        for needle in needles:
            if needle.lower() in lowered:
                hits.append((name, needle))
    return hits


def load_patterns(path: Path) -> list[tuple[str, "re.Pattern[str]"]]:
    """`<label> :: <regex>` lines from the committed pattern set.

    The label names the class member the pattern covers and is what a hit reports, so a
    reviewer checks coverage against the class rather than against the author's intent.
    A malformed line raises rather than being skipped: a pattern set that silently drops
    a line is a gate that silently narrows.
    """
    patterns: list[tuple[str, re.Pattern[str]]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if PATTERN_SEP not in line:
            raise ManifestError(f"{path}:{lineno}: no {PATTERN_SEP!r} separator: {line!r}")
        label, _, expr = line.partition(PATTERN_SEP)
        try:
            patterns.append((label.strip(), re.compile(expr.strip(), re.IGNORECASE)))
        except re.error as exc:
            raise ManifestError(f"{path}:{lineno}: bad regex for {label.strip()!r}: {exc}") from None
    if not patterns:
        raise ManifestError(f"{path} holds no patterns")
    return patterns


def _redact(match: str) -> str:
    """Enough of a match to find it, not enough to be the disclosure.

    A pattern hit may be a real identifier, so the default report must not carry it —
    a packet quoting the sweep would then republish what the sweep exists to catch.
    `--show-matches` prints them in full for local adjudication.
    """
    flat = " ".join(match.split())
    if len(flat) <= 6:
        return f"{flat[:1]}…{flat[-1:]} (len {len(flat)})"
    return f"{flat[:3]}…{flat[-2:]} (len {len(flat)})"


def _sweep_patterns(
    files: dict[str, bytes],
    patterns: list[tuple[str, "re.Pattern[str]"]],
    show_matches: bool = False,
) -> list[tuple[str, str, int, str]]:
    """Every (export name, label, line number, rendered match) the pattern set hits."""
    hits = []
    for name in sorted(files):
        text = files[name].decode("utf-8", "replace")
        for label, rx in patterns:
            for m in rx.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                got = m.group(0)
                hits.append((name, label, line_no, got if show_matches else _redact(got)))
    return hits


def assemble(
    dest: Path,
    manifest: Path = MANIFEST_MD,
    replace: bool = False,
    needles_file: Path | None = None,
    repo_dirs: dict[str, Path] | None = None,
    patterns_file: Path | None = DEFAULT_PATTERNS,
    show_matches: bool = False,
) -> int:
    repo_dirs = repo_dirs or REPO_DIRS

    try:
        rows = read_rows(manifest)
    except (ManifestError, OSError) as exc:
        print(f"[FAIL] manifest: {exc}", file=sys.stderr)
        return 1

    seen: dict[str, str] = {}
    for row in rows:
        if row.export_name in seen:
            print(
                f"[FAIL] manifest: export name {row.export_name!r} claimed by both "
                f"{seen[row.export_name]} and {row.repo_path} — a bundle cannot carry both",
                file=sys.stderr,
            )
            return 1
        seen[row.export_name] = row.repo_path

    # Read every source before touching the destination: a run that fails half way
    # through leaves a directory that looks like a bundle and is not one.
    files: dict[str, bytes] = {}
    for row in rows:
        try:
            files[row.export_name] = git_show(repo_dirs[row.repo], row.repo_path)
        except ManifestError as exc:
            print(f"[FAIL] {row.export_name}: {exc}", file=sys.stderr)
            return 1

    # The manifest drives assembly from the path given (working tree) and is itself
    # bundled from HEAD, so the two can disagree. Right behaviour — a bundle carries
    # committed documents — but the 2026-08-14 boundary shipped this state and had to
    # explain it afterwards, so say it at assembly time instead.
    for row in rows:
        if (repo_dirs[row.repo] / row.repo_path).resolve() == manifest.resolve():
            if files[row.export_name] != manifest.read_bytes():
                print(
                    f"[WARN] {manifest} has uncommitted edits — the bundle carries the "
                    f"committed copy, not the one that drove this run"
                )

    needles: list[str] = []
    if needles_file is not None:
        try:
            needles = [
                line.strip()
                for line in needles_file.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            ]
        except OSError as exc:
            print(f"[FAIL] needles: {exc}", file=sys.stderr)
            return 1
        if not needles:
            print(f"[FAIL] needles: {needles_file} holds no needles", file=sys.stderr)
            return 1

    patterns: list[tuple[str, re.Pattern[str]]] = []
    if patterns_file is not None:
        try:
            patterns = load_patterns(patterns_file)
        except (ManifestError, OSError) as exc:
            print(f"[FAIL] patterns: {exc}", file=sys.stderr)
            return 1

    moved_to, error = _refuse_or_clear(dest, replace)
    if error:
        print(f"[FAIL] destination: {error}", file=sys.stderr)
        return 1
    if moved_to:
        print(f"[INFO] destination: previous bundle moved aside to {moved_to} (not deleted)")

    dest.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (dest / name).write_bytes(content)

    heads = {repo: git_head(repo_dirs[repo]) or "?" for repo in sorted({r.repo for r in rows})}
    head_line = ", ".join(f"{repo} {head}" for repo, head in heads.items())

    print(f"Wrote {dest} — {len(files)} document(s) at {head_line}")
    for row in rows:
        digest = hashlib.sha256(files[row.export_name]).hexdigest()[:12]
        print(
            f"  {row.export_name:<40} {len(files[row.export_name]):>7}  {digest}  "
            f"{row.repo}:{row.repo_path}"
        )

    needle_hits = _sweep(files, needles) if needles else []
    pattern_hits = _sweep_patterns(files, patterns, show_matches) if patterns else []

    if needle_hits or pattern_hits:
        total = len(needle_hits) + len(pattern_hits)
        print(
            f"\n[FAIL] U2 sweep: {total} hit(s) — the bundle carries content matching "
            f"the scrub class and must not be uploaded:",
            file=sys.stderr,
        )
        for name, needle in needle_hits:
            # The needle is the operator's own; echoing which document carries it is
            # the finding, and the file it came from is already on their disk.
            print(f"  [needle]  {name}: {needle!r}", file=sys.stderr)
        for name, label, line_no, shown in pattern_hits:
            # Redacted unless --show-matches: a pattern hit may be a real identifier,
            # and a packet quoting the sweep would republish what the sweep is for.
            print(f"  [pattern] {name}:{line_no}: {label} — {shown}", file=sys.stderr)
        (dest / MARKER_NAME).write_text(
            MARKER_BODY + f"  {head_line}\n\nThe sweep RAN and FOUND {total} hit(s).\n",
            encoding="utf-8",
        )
        return 1

    if patterns or needles:
        ran = []
        if patterns:
            ran.append(f"{len(patterns)} pattern(s) from {patterns_file}")
        if needles:
            ran.append(f"{len(needles)} needle(s)")
        print(f"\n[PASS] U2 sweep: {' + '.join(ran)}, no hit — no marker written.")
        print(
            "       This claims only that NO TEXT IN THE BUNDLE MATCHES THESE PATTERNS.\n"
            "       It does not claim the bundle carries no identifying content; the\n"
            "       class members no pattern reaches are enumerated under UNDER-REACH in\n"
            f"       {patterns_file}."
            if patterns
            else "       This claims only that none of the supplied needles appears in the bundle."
        )
    else:
        (dest / MARKER_NAME).write_text(
            MARKER_BODY + f"  {head_line}\n", encoding="utf-8"
        )
        print(
            f"\n[WARN] U2 sweep NOT RUN — this bundle is unswept and must not be "
            f"uploaded as it stands.\n"
            f"       {dest / MARKER_NAME} says so in the bundle, where the terminal "
            f"output cannot scroll away.\n"
            f"       The pattern sweep is on by default; it was disabled for this run."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("dest", type=Path, help="directory to write the bundle into")
    parser.add_argument(
        "--manifest", type=Path, default=MANIFEST_MD, help="manifest to read the export set from"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="move a non-empty destination aside to <dest>.superseded.<n> and proceed",
    )
    parser.add_argument(
        "--needles",
        type=Path,
        default=None,
        help="untracked file of literal U2 needles, one per line; swept in ADDITION to "
        "the committed pattern set",
    )
    parser.add_argument(
        "--patterns",
        type=Path,
        default=DEFAULT_PATTERNS,
        help=f"committed U2 pattern set, '<label> :: <regex>' per line (default {DEFAULT_PATTERNS})",
    )
    parser.add_argument(
        "--no-patterns",
        action="store_true",
        help="disable the default pattern sweep; with no --needles the bundle is unswept",
    )
    parser.add_argument(
        "--show-matches",
        action="store_true",
        help="print pattern matches in full instead of redacted — local adjudication "
        "only, never paste the output into a packet",
    )
    args = parser.parse_args()

    return assemble(
        args.dest,
        args.manifest,
        args.replace,
        args.needles,
        patterns_file=None if args.no_patterns else args.patterns,
        show_matches=args.show_matches,
    )


if __name__ == "__main__":
    sys.exit(main())
