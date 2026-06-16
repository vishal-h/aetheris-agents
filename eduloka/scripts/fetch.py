#!/usr/bin/env python3
"""Stage-1 fetch CLI.

Fetches search results for a term and appends provider-native JSONL to
data/raw/{provider}.jsonl (or a Hive-partitioned path with --partition).
JSON summary to stdout; errors to stderr; exit 0 / 1.

Envelope shape: {"status": "ok"|"error", "out": <path>, ...} — matches
the map/enrich CLIs so the t6 orchestrator has one stdout parser.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch_base import PROVIDERS, SearchError, get_fetcher
from list_terms import slug_term  # noqa: E402

_USE_CASE_ROOT = Path(__file__).parent.parent


def _make_output_path(base: Path, provider: str, term: str, dt: str, *, partition: bool) -> Path:
    """Return the output file path for a fetch run."""
    if partition:
        return base / f"provider={provider}" / f"dt={dt}" / f"{slug_term(term)}.jsonl"
    return base / f"{provider}.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch search results to JSONL.")
    parser.add_argument("--provider", default=None, choices=list(PROVIDERS),
                        metavar="PROVIDER",
                        help=f"Provider ({', '.join(PROVIDERS)}; default: $SEARCH_PROVIDER)")
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
        print(json.dumps({"status": "error", "error": "no provider — set --provider or SEARCH_PROVIDER"}))
        sys.exit(1)

    try:
        fetcher = get_fetcher(provider)
    except SearchError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)

    try:
        items = fetcher.fetch(args.term, start=args.start, num=args.num, country=args.country)
    except SearchError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    fetched_at = datetime.now(timezone.utc).isoformat()
    dt_partition = fetched_at[:10]  # YYYY-MM-DD from UTC timestamp

    base = args.output_dir or (_USE_CASE_ROOT / "data" / "raw")
    out_path = _make_output_path(base, provider, args.term, dt_partition, partition=args.partition)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "a") as f:
        for item in items:
            envelope = {
                "provider": provider,
                "term": args.term,
                "fetched_at": fetched_at,
                "raw": item,
            }
            f.write(json.dumps(envelope) + "\n")

    print(json.dumps({
        "status": "ok",
        "provider": provider,
        "term": args.term,
        "count": len(items),
        "out": str(out_path),
    }))


if __name__ == "__main__":
    main()
