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
    and the U2 scrub sweep is what stands between it and a project. This script cannot
    run that sweep on its own: U2's needles are real identities (logins, account and user
    ids, the organisation), derived at runtime from untracked live captures — a committed
    script carrying them would itself be the disclosure it exists to prevent. So the
    default is an explicit unswept notice, on stdout and as a marker file dropped in the
    bundle, naming what must run first. `--needles FILE` (an untracked file, one needle
    per line) runs the sweep here instead; only a clean sweep leaves no marker.

Usage:
  python3 scripts/assemble_export_bundle.py DEST [--manifest FILE] [--replace]
                                                 [--needles FILE]

Exit codes:
  0 — bundle written from every manifest row
  1 — destination refused, a source could not be read, or the U2 sweep found a needle
"""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from _manifest import (  # noqa: E402
    MANIFEST_MD,
    REPO_DIRS,
    ManifestError,
    git_head,
    git_show,
    read_rows,
)

MARKER_NAME = "_UNSWEPT-DO-NOT-UPLOAD.txt"

MARKER_BODY = """\
This bundle has NOT been swept for the U2 scrub class. Do not upload it.

U2 (cloudcost/docs/m6-t2-implementation-notes.md, "the scrub class, defined rather
than enumerated") covers anything identifying an account, the people in it, or its
internal structure: organisation and repository names, logins, display names, numeric
user and organisation ids, node ids, profile and avatar URLs, email addresses, and any
token-shaped string.

assemble_export_bundle.py cannot run that sweep unaided. Its needles are the real
identifiers themselves, derived from untracked live captures; a committed script
carrying them would be the disclosure the sweep exists to prevent.

To clear this marker, re-run with the needles:

    python3 scripts/assemble_export_bundle.py <dest> --replace --needles <untracked-file>

one needle per line. A clean sweep writes no marker. Delete the needle file afterwards —
it is a deanonymisation key, and leaving it beside the thing it deanonymises is the
mistake m6 t3 recorded making.

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


def assemble(
    dest: Path,
    manifest: Path = MANIFEST_MD,
    replace: bool = False,
    needles_file: Path | None = None,
    repo_dirs: dict[str, Path] | None = None,
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

    hits = _sweep(files, needles) if needles else []
    if hits:
        print(
            f"\n[FAIL] U2 sweep: {len(hits)} hit(s) — the bundle carries identifying "
            f"content and must not be uploaded:",
            file=sys.stderr,
        )
        for name, needle in hits:
            # The needle is the operator's own; echoing which document carries it is
            # the finding, and the file it came from is already on their disk.
            print(f"  {name}: {needle!r}", file=sys.stderr)
        (dest / MARKER_NAME).write_text(
            MARKER_BODY + f"  {head_line}\n\nThe sweep RAN and FOUND {len(hits)} hit(s).\n",
            encoding="utf-8",
        )
        return 1

    if needles:
        print(f"\n[PASS] U2 sweep: {len(needles)} needle(s), no hit — no marker written.")
    else:
        (dest / MARKER_NAME).write_text(
            MARKER_BODY + f"  {head_line}\n", encoding="utf-8"
        )
        print(
            f"\n[WARN] U2 sweep NOT RUN — this bundle is unswept and must not be "
            f"uploaded as it stands.\n"
            f"       {dest / MARKER_NAME} says so in the bundle, where the terminal "
            f"output cannot scroll away.\n"
            f"       Re-run with --replace --needles FILE to sweep; a clean sweep "
            f"writes no marker."
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
        help="untracked file of U2 needles, one per line; runs the sweep over the bundle",
    )
    args = parser.parse_args()

    return assemble(args.dest, args.manifest, args.replace, args.needles)


if __name__ == "__main__":
    sys.exit(main())
