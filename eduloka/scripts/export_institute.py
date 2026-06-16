"""Stage-4b CLI: export edux/gold JSONL as gws_cse-shaped JSONL for ct-edux ingest.

Reads each line as an EduxRecord, projects via to_gws_cse(), and writes the
result as JSONL to data/export/{stem}.jsonl. No DB access — output files are
consumed by ct-edux via its GwsCseApi.upsert/1 (companion workstream).

The exported row shape mirrors the direct-upsert column set exactly; both
sinks share the same to_gws_cse() projection so ct-edux sees consistent data
regardless of which sink the orchestrator chose.

Sink selection is explicit: the orchestrator (t6) reads EDUX_SINK=direct|export
and invokes either upsert_institute.py or this script. No silent fallback.

Usage:
    python3 scripts/export_institute.py --in data/gold/exa.jsonl
    python3 scripts/export_institute.py --in data/gold/exa.jsonl --out /tmp/export.jsonl

stdout: {"status": "ok"|"partial"|"error", "exported": N, "skipped": M, "out": path}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_USE_CASE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from edux_record import EduxRecord  # noqa: E402


def _run(in_path: Path, out_path: Path) -> dict:
    lines = [ln for ln in in_path.read_text().splitlines() if ln.strip()]
    exported, skipped, errors = 0, 0, []

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for line in lines:
            try:
                rec = EduxRecord(**json.loads(line))
                fh.write(json.dumps(rec.to_gws_cse()) + "\n")
                exported += 1
            except Exception as exc:  # noqa: BLE001
                skipped += 1
                errors.append(str(exc))

    return {"exported": exported, "skipped": skipped, "errors": errors, "out": str(out_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="export edux/gold JSONL as gws_cse-shaped JSONL")
    parser.add_argument("--in", dest="in_path", required=True, help="input edux/gold JSONL")
    parser.add_argument("--out", dest="out_path", help="output path (default: data/export/{stem}.jsonl)")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        print(json.dumps({"status": "error", "error": f"input not found: {in_path}"}))
        sys.exit(1)

    out_path = (
        Path(args.out_path)
        if args.out_path
        else _USE_CASE_ROOT / "data" / "export" / f"{in_path.stem}.jsonl"
    )

    try:
        result = _run(in_path, out_path)
        status = "partial" if result["skipped"] else "ok"
        print(json.dumps({"status": status, **result}))
        if result["skipped"]:
            sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
