#!/usr/bin/env python3
"""Stage-1 fetch CLI.

Fetches search results for a term and appends provider-native JSONL to
data/raw/{provider}.jsonl (or a partitioned path with --partition, t7).
JSON summary to stdout; errors to stderr; exit 0 / 1.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_base import SearchError, get_fetcher

_USE_CASE_ROOT = Path(__file__).parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch search results to JSONL.")
    parser.add_argument("--provider", default=None,
                        help="Provider name (default: $SEARCH_PROVIDER)")
    parser.add_argument("--term", required=True, help="Search term")
    parser.add_argument("--start", type=int, default=1, metavar="N",
                        help="Start offset, 1-indexed (default: 1)")
    parser.add_argument("--num", type=int, default=10, metavar="N",
                        help="Number of results (default: 10)")
    parser.add_argument("--country", default="IN", metavar="CC",
                        help="ISO country code (default: IN)")
    parser.add_argument("--output-dir", default=None, type=Path, metavar="DIR",
                        help="Output directory (default: data/raw/ under use-case root)")
    parser.add_argument("--partition", action="store_true",
                        help="Write to Hive-partitioned path provider=P/dt=YYYY-MM-DD/")
    args = parser.parse_args()

    provider = args.provider or os.environ.get("SEARCH_PROVIDER")
    if not provider:
        print(json.dumps({"ok": False, "error": "no provider — set --provider or SEARCH_PROVIDER"}))
        sys.exit(1)

    try:
        fetcher = get_fetcher(provider)
    except SearchError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)

    try:
        items = fetcher.fetch(args.term, start=args.start, num=args.num, country=args.country)
    except SearchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    base = args.output_dir or (_USE_CASE_ROOT / "data" / "raw")
    if args.partition:
        out_dir = base / f"provider={provider}" / f"dt={date.today().isoformat()}"
        filename = f"{args.term}.jsonl"
    else:
        out_dir = base
        filename = f"{provider}.jsonl"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    with open(out_path, "a") as f:
        for item in items:
            envelope = {
                "provider": provider,
                "term": args.term,
                "fetched_at": date.today().isoformat(),
                "raw": item,
            }
            f.write(json.dumps(envelope) + "\n")

    print(json.dumps({
        "ok": True,
        "provider": provider,
        "term": args.term,
        "count": len(items),
        "output": str(out_path),
    }))


if __name__ == "__main__":
    main()
