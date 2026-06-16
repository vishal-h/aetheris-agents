"""Stage-2 CLI: map raw JSONL (bronze) to edux JSONL (silver).

Usage:
    python3 scripts/map.py --in data/raw/cse.jsonl [--out data/edux/cse.jsonl]

stdout: {"status": "ok"|"error", "out": ..., ...}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mappers import map_envelope  # noqa: E402


def _run(in_path: Path, out_path: Path) -> dict:
    lines = [l for l in in_path.read_text().splitlines() if l.strip()]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for line in lines:
        env = json.loads(line)
        rec = map_envelope(env)
        records.append(rec.to_dict())
    out_path.write_text("\n".join(json.dumps(r) for r in records) + ("\n" if records else ""))
    return {"mapped": len(records), "out": str(out_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="map raw JSONL to edux JSONL")
    parser.add_argument("--in", dest="in_path", required=True, help="input raw JSONL")
    parser.add_argument("--out", dest="out_path", help="output edux JSONL (default: data/edux/<stem>.jsonl)")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        print(json.dumps({"status": "error", "error": f"input not found: {in_path}"}))
        sys.exit(1)

    stem = in_path.stem
    out_path = Path(args.out_path) if args.out_path else Path("data/edux") / f"{stem}.jsonl"

    try:
        result = _run(in_path, out_path)
        print(json.dumps({"status": "ok", **result}))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
