#!/usr/bin/env python3
"""Generate tests/fixtures/sample_corpus.duckdb for inventory_report tests."""

import sys
from pathlib import Path

import duckdb

OUT = Path(__file__).parent / "sample_corpus.duckdb"
OUT.unlink(missing_ok=True)

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from init_db import init_schema

conn = duckdb.connect(str(OUT))
init_schema(conn)

# One completed scan run
conn.execute("""
    INSERT INTO scan_runs
        (id, root_path, started_at, finished_at, status,
         files_scanned, files_new, files_updated, duplicates_found)
    VALUES
        ('run-fixture-001', '/data/archive',
         TIMESTAMPTZ '2026-01-15 09:00:00',
         TIMESTAMPTZ '2026-01-15 09:04:30',
         'complete', 30, 24, 6, 8)
""")

# 30 files across 3 MIME types with varied dates and 5+ duplicate groups
files = [
    # PDF files — 10 files, sha-a has 3 copies, sha-b has 2 copies
    ("/data/archive/acme/FY2024/tax_return.pdf",        1_200_000, "2024-03-10", "application/pdf",  "sha-a"),
    ("/data/archive/acme/backup/tax_return_v2.pdf",     1_200_000, "2024-03-15", "application/pdf",  "sha-a"),
    ("/data/archive/shared/tax_return_copy.pdf",        1_200_000, "2024-04-01", "application/pdf",  "sha-a"),
    ("/data/archive/acme/FY2023/annual_report.pdf",     3_500_000, "2023-06-30", "application/pdf",  "sha-b"),
    ("/data/archive/acme/old/annual_report.pdf",        3_500_000, "2023-06-30", "application/pdf",  "sha-b"),
    ("/data/archive/acme/FY2022/balance_sheet.pdf",     2_100_000, "2022-09-20", "application/pdf",  "sha-c"),
    ("/data/archive/globex/FY2024/invoice_001.pdf",       450_000, "2024-02-14", "application/pdf",  "sha-d"),
    ("/data/archive/globex/FY2024/invoice_002.pdf",       460_000, "2024-02-28", "application/pdf",  "sha-e"),
    ("/data/archive/globex/FY2023/invoice_101.pdf",       430_000, "2023-03-01", "application/pdf",  "sha-f"),
    ("/data/archive/initech/FY2024/contract.pdf",         900_000, "2024-07-01", "application/pdf",  "sha-g"),

    # DOCX files — 12 files, sha-h has 4 copies, sha-i has 2 copies
    ("/data/archive/acme/FY2024/letter_jan.docx",        85_000, "2024-01-10", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-h"),
    ("/data/archive/acme/FY2024/letter_jan_v2.docx",     85_000, "2024-01-12", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-h"),
    ("/data/archive/acme/old/letter_jan.docx",            85_000, "2024-01-10", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-h"),
    ("/data/archive/shared/letter_jan_final.docx",        85_000, "2024-01-15", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-h"),
    ("/data/archive/globex/FY2024/memo_q1.docx",          42_000, "2024-04-05", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-i"),
    ("/data/archive/globex/backup/memo_q1.docx",          42_000, "2024-04-05", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-i"),
    ("/data/archive/initech/FY2023/agreement.docx",      130_000, "2023-11-20", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-j"),
    ("/data/archive/initech/FY2022/agreement_old.docx",  125_000, "2022-11-20", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-k"),
    ("/data/archive/acme/FY2021/notice.docx",             60_000, "2021-08-01", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-l"),
    ("/data/archive/globex/FY2022/proposal.docx",        200_000, "2022-03-15", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-m"),
    ("/data/archive/initech/FY2024/scope.docx",           95_000, "2024-09-01", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-n"),
    ("/data/archive/acme/FY2024/addendum.docx",           55_000, "2024-10-15", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "sha-o"),

    # Plain text / CSV — 6 files, sha-p has 2 copies
    ("/data/archive/acme/FY2024/data_export.csv",        320_000, "2024-06-30", "text/csv",   "sha-p"),
    ("/data/archive/acme/backup/data_export.csv",        320_000, "2024-06-30", "text/csv",   "sha-p"),
    ("/data/archive/globex/FY2023/transactions.csv",     510_000, "2023-12-31", "text/csv",   "sha-q"),
    ("/data/archive/initech/FY2022/ledger.csv",          140_000, "2022-12-31", "text/csv",   "sha-r"),
    ("/data/archive/acme/FY2021/notes.txt",               12_000, "2021-03-10", "text/plain", "sha-s"),
    ("/data/archive/shared/readme.txt",                    1_500, "2023-01-01", "text/plain", "sha-t"),

    # Zip files — 2
    ("/data/archive/acme/archive_2022.zip",           15_000_000, "2022-12-31", "application/zip", "sha-u"),
    ("/data/archive/globex/old_docs.zip",              8_500_000, "2021-06-30", "application/zip", "sha-v"),
]

for path, size, date, mime, sha in files:
    conn.execute(
        """
        INSERT INTO f2_file_index (path, size_bytes, modified_at, mime_type, sha256, status, last_scanned)
        VALUES (?, ?, CAST(? AS TIMESTAMP), ?, ?, 'ok', now())
        """,
        [path, size, date, mime, sha],
    )

# Mark duplicates
conn.execute("""
    UPDATE f2_file_index
    SET status = 'duplicate'
    WHERE sha256 IN (
        SELECT sha256 FROM f2_file_index
        WHERE sha256 IS NOT NULL
        GROUP BY sha256 HAVING COUNT(*) > 1
    )
    AND path NOT IN (
        SELECT MIN(path) FROM f2_file_index
        WHERE sha256 IS NOT NULL
        GROUP BY sha256
    )
""")

# 2 zip inventory entries
conn.execute("""
    INSERT INTO zip_inventory (path, size_bytes, depth, status, contents_count, processed_at)
    VALUES
        ('/data/archive/acme/archive_2022.zip',  15000000, 0, 'processed', 47, now()),
        ('/data/archive/globex/old_docs.zip',     8500000, 0, 'pending',   NULL, NULL)
""")

conn.close()
print(f"Generated {OUT}")
