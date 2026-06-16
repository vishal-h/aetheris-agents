"""Stage-3 CLI: enrich edux JSONL (silver) to gold JSONL.

Usage:
    python3 scripts/enrich.py --in data/edux/exa.jsonl [--out data/gold/exa.jsonl]
                               [--enrichers domain,keywords]

Each named enricher writes its payload under enrichment[name], stamped with
_by/_at/_v. Idempotent: if enrichment[name] is already set, the record is
skipped for that enricher (allows composing workers without stepping on each
other).

stdout: {"status": "ok"|"partial", "enriched": N, "skipped": M, ...}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_USE_CASE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from edux_record import EduxRecord  # noqa: E402
from enrichers import ENRICHER_VERSIONS, ENRICHERS  # noqa: E402


def _stamp(payload: dict, name: str) -> dict:
    payload["_by"] = name
    payload["_at"] = datetime.now(timezone.utc).isoformat()
    payload["_v"] = ENRICHER_VERSIONS[name]
    return payload


def _enrich_record(record: EduxRecord, enricher_names: list[str]) -> None:
    for name in enricher_names:
        if name in record.enrichment:
            continue  # idempotent: already enriched by this worker
        fn = ENRICHERS[name]
        payload = fn(record)
        record.enrichment[name] = _stamp(payload, name)


def _run(in_path: Path, out_path: Path, enricher_names: list[str]) -> dict:
    lines = [l for l in in_path.read_text().splitlines() if l.strip()]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records, skipped, errors = [], 0, []
    for line in lines:
        try:
            data = json.loads(line)
            rec = EduxRecord(**data)
            _enrich_record(rec, enricher_names)
            records.append(rec.to_dict())
        except Exception as exc:  # noqa: BLE001
            skipped += 1
            errors.append(str(exc))
    out_path.write_text("\n".join(json.dumps(r) for r in records) + ("\n" if records else ""))
    return {"enriched": len(records), "skipped": skipped, "errors": errors, "out": str(out_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="enrich edux JSONL to gold JSONL")
    parser.add_argument("--in", dest="in_path", required=True, help="input edux JSONL")
    parser.add_argument("--out", dest="out_path", help="output gold JSONL (default: data/gold/<stem>.jsonl)")
    parser.add_argument("--enrichers", default=",".join(ENRICHERS),
                        help=f"comma-separated enrichers (default: all — {','.join(ENRICHERS)})")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        print(json.dumps({"status": "error", "error": f"input not found: {in_path}"}))
        sys.exit(1)

    enricher_names = [n.strip() for n in args.enrichers.split(",") if n.strip()]
    unknown = [n for n in enricher_names if n not in ENRICHERS]
    if unknown:
        print(json.dumps({"status": "error", "error": f"unknown enrichers: {unknown}"}))
        sys.exit(1)

    stem = in_path.stem
    out_path = Path(args.out_path) if args.out_path else _USE_CASE_ROOT / "data" / "gold" / f"{stem}.jsonl"

    try:
        result = _run(in_path, out_path, enricher_names)
        status = "partial" if result["skipped"] else "ok"
        print(json.dumps({"status": status, **result}))
        if result["skipped"]:
            sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
