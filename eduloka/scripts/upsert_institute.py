"""Stage-4 CLI: upsert edux/gold JSONL into Postgres gws_cse.

Reads each line as an EduxRecord, projects via to_gws_cse(), and upserts
into gws_cse keyed on link (ON CONFLICT DO UPDATE). Mirrors the insert-or-
update semantics of ct-edux lib/gws/cse.ex.

Schema notes (from ct-edux Ecto DDL):
  - metatags is jsonb[] (Ecto {:array, :map}); each element is a Jsonb value.
  - inserted_at/updated_at are NOT NULL with no DB default; set via now().
  - status is NOT updated on conflict — existing rows keep their status
    (preserves manual status=0 soft-deletes; B3 fix).

Requires:
  - EDUX_DATABASE_URL env var (psycopg connection string)
  - Migration 0001_add_enrichment_jsonb.sql applied first

Usage:
    python3 scripts/upsert_institute.py --in data/gold/exa.jsonl

stdout: {"status": "ok"|"partial"|"error", "upserted": N, "skipped": M, ...}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_USE_CASE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from edux_record import EduxRecord  # noqa: E402

# B1: metatags is jsonb[]; use ARRAY[...] construction with per-element ::jsonb.
# B2: inserted_at/updated_at are NOT NULL with no DB default — set now() on insert;
#     bump updated_at = now() on conflict.
# B3: status excluded from DO UPDATE SET — preserves existing status (e.g. status=0
#     soft-deletes) across re-discoveries.
_UPSERT_SQL = """
INSERT INTO gws_cse (link, title, snippet, image, search_term, status, metatags, enrichment,
                     inserted_at, updated_at)
VALUES (%(link)s, %(title)s, %(snippet)s, %(image)s, %(search_term)s,
        %(status)s, %(metatags)s, %(enrichment)s,
        now(), now())
ON CONFLICT (link) DO UPDATE SET
    title       = EXCLUDED.title,
    snippet     = EXCLUDED.snippet,
    image       = EXCLUDED.image,
    search_term = EXCLUDED.search_term,
    metatags    = EXCLUDED.metatags,
    enrichment  = EXCLUDED.enrichment,
    updated_at  = now()
"""


def _row(rec: EduxRecord) -> dict:
    """Pure projection — Python-native types, no psycopg-specific wrappers."""
    return rec.to_gws_cse()


def _adapt(row: dict) -> dict:
    """Convert Python types to psycopg-compatible values for DB insertion.

    Deferred import keeps psycopg optional for offline tests.
    """
    from psycopg.types.json import Jsonb  # noqa: PLC0415

    return {
        **row,
        "metatags": [Jsonb(m) for m in row["metatags"]],
        "enrichment": Jsonb(row["enrichment"]),
    }


def _run(in_path: Path, db_url: str) -> dict:
    import psycopg  # noqa: PLC0415 — import deferred; psycopg is optional (t5)

    lines = [l for l in in_path.read_text().splitlines() if l.strip()]
    upserted, skipped, errors = 0, 0, []

    with psycopg.connect(db_url) as conn, conn.cursor() as cur:
        for line in lines:
            try:
                data = json.loads(line)
                rec = EduxRecord(**data)
                cur.execute(_UPSERT_SQL, _adapt(_row(rec)))
                upserted += 1
            except Exception as exc:  # noqa: BLE001
                skipped += 1
                errors.append(str(exc))
        conn.commit()

    return {"upserted": upserted, "skipped": skipped, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description="upsert edux/gold JSONL into gws_cse")
    parser.add_argument("--in", dest="in_path", required=True, help="input edux/gold JSONL")
    parser.add_argument("--db", dest="db_url", help="PostgreSQL connection string (overrides EDUX_DATABASE_URL)")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    if not in_path.exists():
        print(json.dumps({"status": "error", "error": f"input not found: {in_path}"}))
        sys.exit(1)

    db_url = args.db_url or os.environ.get("EDUX_DATABASE_URL")
    if not db_url:
        print(json.dumps({"status": "error", "error": "EDUX_DATABASE_URL not set"}))
        sys.exit(1)

    try:
        result = _run(in_path, db_url)
        status = "partial" if result["skipped"] else "ok"
        print(json.dumps({"status": status, **result}))
        if result["skipped"]:
            sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
