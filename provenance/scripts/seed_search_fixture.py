"""
Seed approved classifications into a corpus DuckDB for search validation.

Seeds the five known paths from sample_corpus.duckdb so that search_agent.exs
can find documents when run against that fixture.

Usage:
    python3 provenance/scripts/seed_search_fixture.py --db /path/to/corpus.duckdb
    python3 provenance/scripts/seed_search_fixture.py --db /path/to/corpus.duckdb --clear
"""

import argparse
import sys
import uuid

import duckdb

CLASSIFICATIONS = [
    {
        "path": "/data/archive/acme/FY2024/tax_return.pdf",
        "client": "acme",
        "financial_year": "FY2024",
        "doc_type": "tax",
        "confidence": 0.92,
        "raw_excerpt": "Tax return for ACME Corp fiscal year 2024 including GST schedule",
        "status": "approved",
    },
    {
        "path": "/data/archive/acme/FY2024/letter_jan.docx",
        "client": "acme",
        "financial_year": "FY2024",
        "doc_type": "legal",
        "confidence": 0.85,
        "raw_excerpt": "Legal correspondence from ACME Corp counsel January 2024",
        "status": "approved",
    },
    {
        "path": "/data/archive/acme/FY2023/annual_report.pdf",
        "client": "acme",
        "financial_year": "FY2023",
        "doc_type": "accounts",
        "confidence": 0.80,
        "raw_excerpt": "Annual report for ACME Corp 2023 balance sheet profit and loss summary",
        "status": "approved",
    },
    {
        "path": "/data/archive/globex/FY2024/invoice_001.pdf",
        "client": "globex",
        "financial_year": "FY2024",
        "doc_type": "accounts",
        "confidence": 0.75,
        "raw_excerpt": "Invoice 001 from Globex Corporation for consulting services rendered",
        "status": "approved",
    },
    {
        "path": "/data/archive/initech/FY2024/contract.pdf",
        "client": "initech",
        "financial_year": "FY2024",
        "doc_type": "legal",
        "confidence": 0.70,
        "raw_excerpt": "Contract agreement Initech Inc service level 2024 court notice clause",
        "status": "approved",
    },
]


def seed(conn: duckdb.DuckDBPyConnection, clear: bool = False) -> int:
    if clear:
        conn.execute("DELETE FROM classifications WHERE path IN (SELECT path FROM classifications)")
        print("Cleared existing classifications.", file=sys.stderr)

    inserted = 0
    for row in CLASSIFICATIONS:
        row_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO classifications
               (id, path, client, financial_year, doc_type, confidence,
                raw_excerpt, status, classified_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, now())
               ON CONFLICT DO NOTHING""",
            [
                row_id,
                row["path"],
                row["client"],
                row["financial_year"],
                row["doc_type"],
                row["confidence"],
                row["raw_excerpt"],
                row["status"],
            ],
        )
        inserted += conn.execute("SELECT changes()").fetchone()[0]

    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed search fixture classifications")
    parser.add_argument("--db", required=True, help="Path to DuckDB corpus file")
    parser.add_argument("--clear", action="store_true", help="Clear existing classifications first")
    args = parser.parse_args()

    conn = duckdb.connect(args.db, read_only=False)
    try:
        n = seed(conn, clear=args.clear)
        print(f"Seeded {n} classifications into {args.db}", file=sys.stderr)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
