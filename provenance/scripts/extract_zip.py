#!/usr/bin/env python3
"""
Extract a zip file to a staging directory and return a manifest JSON.

Exits 0 always — encrypted, failed, and max_depth outcomes are reported
in the manifest, not as process errors.

Usage:
  python3 scripts/extract_zip.py \
    --zip /data/archive/acme/archive_2022.zip \
    --staging-dir /tmp/provenance_staging/extractions \
    [--depth 0]
"""

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

MAX_DEPTH = 4
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB


def extract_zip(zip_path: str, staging_dir: str, depth: int = 0) -> dict:
    zp = Path(zip_path)
    base = {
        "zip_path": zip_path,
        "status": None,
        "staging_dir": None,
        "file_count": 0,
        "files": [],
        "nested_zips": [],
        "error": None,
    }

    if depth >= MAX_DEPTH:
        return {**base, "status": "max_depth",
                "error": f"depth {depth} >= max depth {MAX_DEPTH}"}

    if not zp.exists():
        return {**base, "status": "failed", "error": f"file not found: {zip_path}"}

    try:
        zf = zipfile.ZipFile(zp, "r")
    except zipfile.BadZipFile as e:
        return {**base, "status": "failed", "error": f"BadZipFile: {e}"}
    except Exception as e:
        return {**base, "status": "failed", "error": str(e)}

    with zf:
        # Detect encryption by checking flag_bits before attempting extraction
        for info in zf.infolist():
            if info.flag_bits & 0x1:
                return {**base, "status": "encrypted",
                        "error": "zip is password-protected"}

        # Destination for this zip's contents
        dest = Path(staging_dir) / zp.stem
        dest.mkdir(parents=True, exist_ok=True)

        files = []
        nested_zips = []

        try:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                # Path traversal safety — resolve and verify within dest
                member_path = (dest / info.filename).resolve()
                try:
                    member_path.relative_to(dest.resolve())
                except ValueError:
                    print(
                        f"warning: skipping path traversal attempt: {info.filename!r}",
                        file=sys.stderr,
                    )
                    continue

                member_path.parent.mkdir(parents=True, exist_ok=True)

                # Stream large members; copy small ones directly
                if info.file_size >= LARGE_FILE_THRESHOLD:
                    with zf.open(info) as src, member_path.open("wb") as dst:
                        shutil.copyfileobj(src, dst, length=1024 * 1024)
                else:
                    with zf.open(info) as src, member_path.open("wb") as dst:
                        dst.write(src.read())

                entry = {
                    "internal_path": info.filename,
                    "staging_path": str(member_path),
                    "size_bytes": info.file_size,
                }
                files.append(entry)

                if info.filename.lower().endswith(".zip"):
                    nested_zips.append({
                        "internal_path": info.filename,
                        "staging_path": str(member_path),
                    })

        except Exception as e:
            # Clean up partial extraction
            shutil.rmtree(dest, ignore_errors=True)
            return {**base, "status": "failed", "error": str(e)}

    return {
        "zip_path": zip_path,
        "status": "extracted",
        "staging_dir": str(dest),
        "file_count": len(files),
        "files": files,
        "nested_zips": nested_zips,
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a zip to staging")
    parser.add_argument("--zip", required=True, help="Path to zip file")
    parser.add_argument("--staging-dir", required=True, help="Staging root directory")
    parser.add_argument("--depth", type=int, default=0,
                        help="Current nesting depth (default 0)")
    args = parser.parse_args()

    result = extract_zip(args.zip, args.staging_dir, depth=args.depth)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
