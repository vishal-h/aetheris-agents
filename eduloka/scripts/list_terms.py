"""list_terms.py — read data/terms.txt and return the term list as JSON.

Reads the configured terms file, strips blank lines and # comments, and prints:
  {"status": "ok", "terms": [...], "count": N}

File precedence: --terms-file flag > EDUX_TERMS_FILE env var > data/terms.txt.

Usage:
    python3 scripts/list_terms.py
    python3 scripts/list_terms.py --terms-file path/to/terms.txt
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_USE_CASE_ROOT = Path(__file__).parent.parent


def load_terms(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="list eduloka search terms")
    parser.add_argument("--terms-file", dest="terms_file",
                        help="path to terms file (overrides EDUX_TERMS_FILE)")
    args = parser.parse_args()

    path_str = (
        args.terms_file
        or os.environ.get("EDUX_TERMS_FILE")
        or str(_USE_CASE_ROOT / "data" / "terms.txt")
    )
    path = Path(path_str)

    if not path.exists():
        print(json.dumps({"status": "error", "error": f"terms file not found: {path}"}))
        sys.exit(1)

    terms = load_terms(path)
    print(json.dumps({"status": "ok", "terms": terms, "count": len(terms)}))


if __name__ == "__main__":
    main()
