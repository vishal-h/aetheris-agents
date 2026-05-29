#!/usr/bin/env python3
"""
Process extracted zip finds against the corpus.

Reads the manifest from extract_zip.py, computes SHA-256 for each extracted
file, classifies it as known (duplicate in f2_file_index) or new-to-corpus,
persists results to DuckDB, and returns a summary JSON.

Nested zips are processed like regular files (SHA-256 computed, moved to
new_finds if new) and registered in zip_inventory with status='pending' at
their permanent path so the orchestrator can extract them recursively.

Usage:
  python3 scripts/process_zip_finds.py \
    --db /data/corpus.duckdb \
    --manifest /tmp/extract_manifest.json \
    --staging-path priv/zip_staging

  # Or pipe from extract_zip.py:
  python3 scripts/extract_zip.py --zip ... | \
    python3 scripts/process_zip_finds.py --db ... --staging-path ...
"""

import argparse
import hashlib
import json
import mimetypes
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import duckdb


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _mime(filename: str) -> str | None:
    t, _ = mimetypes.guess_type(filename)
    return t


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_find_dest(staging_root: Path, sha256: str, filename: str) -> Path:
    """Content-addressed destination: new_finds/{sha256[:2]}/{sha256}/{filename}."""
    return staging_root / "new_finds" / sha256[:2] / sha256 / filename


def process_zip_finds(
    conn: duckdb.DuckDBPyConnection,
    manifest: dict,
    staging_path: str,
) -> dict:
    """Process a zip extraction manifest.  Returns summary dict."""
    zip_path = manifest["zip_path"]
    staging_root = Path(staging_path)

    # Idempotent: zip already fully processed — return counts from DB
    processed = conn.execute(
        "SELECT contents_count, new_to_corpus FROM zip_inventory "
        "WHERE path = ? AND status = 'processed'",
        [zip_path],
    ).fetchone()
    if processed:
        total = processed[0] or 0
        new_count = processed[1] or 0
        known_count = total - new_count
        new_find_rows = conn.execute(
            "SELECT sha256, internal_path FROM zip_contents "
            "WHERE zip_path = ? AND status = 'new'",
            [zip_path],
        ).fetchall()
        new_finds = [
            {
                "staging_path": str(_new_find_dest(
                    staging_root, r[0], Path(r[1]).name
                )),
                "internal_path": r[1],
                "sha256": r[0],
            }
            for r in new_find_rows
        ]
        return {
            "zip_path": zip_path,
            "total_files": total,
            "known": known_count,
            "new_to_corpus": new_count,
            "nested_zips": len(manifest.get("nested_zips", [])),
            "new_finds": new_finds,
        }

    # Ensure zip_inventory row exists before any zip_contents inserts (FK constraint)
    conn.execute(
        """INSERT INTO zip_inventory (path, status)
           VALUES (?, 'pending')
           ON CONFLICT (path) DO NOTHING""",
        [zip_path],
    )

    # Per-file idempotent: load already-processed internal paths
    already_done = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT internal_path, status FROM zip_contents WHERE zip_path = ?",
            [zip_path],
        ).fetchall()
    }

    known = 0
    new_to_corpus = 0
    new_finds = []
    # Maps original staging_path → permanent path (for nested zip registration)
    permanent_paths: dict[str, str] = {}

    for entry in manifest.get("files", []):
        internal_path = entry["internal_path"]
        size_bytes = entry.get("size_bytes", 0)
        staging_file = Path(entry["staging_path"])

        # Already recorded from a prior partial run
        if internal_path in already_done:
            if already_done[internal_path] == "known":
                known += 1
                # Corpus match is the permanent path for known files
                corpus_match = conn.execute(
                    "SELECT corpus_match FROM zip_contents "
                    "WHERE zip_path = ? AND internal_path = ?",
                    [zip_path, internal_path],
                ).fetchone()[0]
                permanent_paths[entry["staging_path"]] = corpus_match or ""
            else:
                new_to_corpus += 1
                sha256 = conn.execute(
                    "SELECT sha256 FROM zip_contents "
                    "WHERE zip_path = ? AND internal_path = ?",
                    [zip_path, internal_path],
                ).fetchone()[0]
                filename = Path(internal_path).name
                dest = _new_find_dest(staging_root, sha256, filename)
                permanent_paths[entry["staging_path"]] = str(dest)
                new_finds.append({
                    "staging_path": str(dest),
                    "internal_path": internal_path,
                    "sha256": sha256,
                })
            continue

        if not staging_file.exists():
            continue

        digest = _sha256(staging_file)

        # Check corpus for known duplicate
        match = conn.execute(
            "SELECT MIN(path) FROM f2_file_index WHERE sha256 = ?",
            [digest],
        ).fetchone()[0]

        if match:
            conn.execute(
                """INSERT INTO zip_contents
                   (id, zip_path, internal_path, sha256, size_bytes, corpus_match, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'known')""",
                [str(uuid.uuid4()), zip_path, internal_path, digest, size_bytes, match],
            )
            staging_file.unlink(missing_ok=True)
            permanent_paths[entry["staging_path"]] = match
            known += 1
        else:
            filename = Path(internal_path).name
            dest = _new_find_dest(staging_root, digest, filename)

            # Defensive collision guard: same dir, same filename but different
            # content (shouldn't occur in a content-addressed layout)
            if dest.exists() and _sha256(dest) != digest:
                stem = Path(filename).stem
                ext = Path(filename).suffix
                dest = dest.parent / f"{stem}_{digest[:8]}{ext}"

            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.copy2(staging_file, dest)

            conn.execute(
                """INSERT INTO f2_file_index
                   (path, size_bytes, sha256, mime_type, status, last_scanned)
                   VALUES (?, ?, ?, ?, 'ok', ?)
                   ON CONFLICT (path) DO NOTHING""",
                [str(dest), size_bytes, digest, _mime(filename), _now()],
            )
            conn.execute(
                """INSERT INTO zip_contents
                   (id, zip_path, internal_path, sha256, size_bytes, corpus_match, status)
                   VALUES (?, ?, ?, ?, ?, null, 'new')""",
                [str(uuid.uuid4()), zip_path, internal_path, digest, size_bytes],
            )
            staging_file.unlink(missing_ok=True)
            permanent_paths[entry["staging_path"]] = str(dest)
            new_to_corpus += 1
            new_finds.append({
                "staging_path": str(dest),
                "internal_path": internal_path,
                "sha256": digest,
            })

    # Register nested zips in zip_inventory as 'pending' using their permanent
    # paths so the orchestrator can call extract_zip on them recursively.
    nested_zips = manifest.get("nested_zips", [])
    parent_row = conn.execute(
        "SELECT depth FROM zip_inventory WHERE path = ?", [zip_path]
    ).fetchone()
    parent_depth = parent_row[0] if parent_row else 0

    for nested in nested_zips:
        orig_staging = nested["staging_path"]
        permanent = permanent_paths.get(orig_staging, orig_staging)
        conn.execute(
            """INSERT INTO zip_inventory (path, depth, parent_zip, status)
               VALUES (?, ?, ?, 'pending')
               ON CONFLICT (path) DO NOTHING""",
            [permanent, parent_depth + 1, zip_path],
        )

    total_files = known + new_to_corpus

    # Upsert zip_inventory for the outer zip
    conn.execute(
        """INSERT INTO zip_inventory
           (path, contents_count, new_to_corpus, status, processed_at)
           VALUES (?, ?, ?, 'processed', ?)
           ON CONFLICT (path) DO UPDATE SET
               status         = 'processed',
               contents_count = excluded.contents_count,
               new_to_corpus  = excluded.new_to_corpus,
               processed_at   = excluded.processed_at""",
        [zip_path, total_files, new_to_corpus, _now()],
    )

    # Delete the raw extraction staging directory
    staging_dir = manifest.get("staging_dir")
    if staging_dir and Path(staging_dir).exists():
        shutil.rmtree(staging_dir, ignore_errors=True)

    return {
        "zip_path": zip_path,
        "total_files": total_files,
        "known": known,
        "new_to_corpus": new_to_corpus,
        "nested_zips": len(nested_zips),
        "new_finds": new_finds,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process zip extraction manifest against corpus"
    )
    parser.add_argument("--db", required=True, help="Path to DuckDB file")
    parser.add_argument("--manifest", help="Path to manifest JSON (default: stdin)")
    parser.add_argument(
        "--staging-path", required=True,
        help="Root path for new_finds permanent staging",
    )
    args = parser.parse_args()

    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text())
    else:
        manifest = json.loads(sys.stdin.read())

    try:
        conn = duckdb.connect(args.db)
    except Exception as e:
        print(json.dumps({"error": str(e), "status": "failed"}))
        sys.exit(1)

    try:
        result = process_zip_finds(conn, manifest, args.staging_path)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e), "status": "failed"}))
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
