#!/usr/bin/env python3
"""
Create a test sandbox for local end-to-end testing of Provenance.

Generates a realistic corpus with:
  - Three clients (acme, globex, initech) across multiple financial years
  - All four document types per taxonomy (tax, legal, accounts, correspondence)
  - Exact duplicates at multiple levels (same content, different paths)
  - Dup of a dup (A copied to B and C)
  - Same filename, different content (must NOT be deduped)
  - Zip containing known files (corpus match) + new files
  - Zip containing another zip (backup of backup, depth 2)
  - Nested zips three levels deep (depth limit test)
  - An encrypted zip (escalation test)

Usage:
    python3 provenance/scripts/create_test_sandbox.py [--root ~/sandbox/provenance-test] [--overwrite]

Then run:
    export PROVENANCE_NAS_PATH=~/sandbox/provenance-test/archive
    export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb
    mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs
"""

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Document content templates — realistic enough for classification
# ---------------------------------------------------------------------------

def tax_doc(client: str, fy: str, variant: str = "") -> bytes:
    return f"""TAX RETURN -{f' ({variant})' if variant else ''}
Australian Taxation Office
Taxable income: $450,000
PAYG withholding: $135,000
GST collected: $45,000
BAS lodgement: quarterly
Franking credits: $28,500
Prepared by: {client} Accounts Team
""".encode()


def legal_doc(client: str, fy: str) -> bytes:
    return f"""LEGAL NOTICE -
Australian Securities and Investments Commission
Notice pursuant to section 601BC of the Corporations Act 2001
Matter: Annual compliance review
Client: {client.upper()}
Reference: ASIC-{fy}-{client[:3].upper()}-001
This notice requires a response within 28 days.
Prepared by: Legal Department
""".encode()


def accounts_doc(client: str, fy: str) -> bytes:
    return f"""BALANCE SHEET -
Total assets:       $2,450,000
Total liabilities:    $890,000
Net assets:         $1,560,000
Net profit:           $320,000
Equity:             $1,560,000
Trial balance: reconciled
Workpapers: attached
Prepared by: {client} Accounting
""".encode()


def correspondence_doc(client: str, fy: str) -> bytes:
    return f"""CORRESPONDENCE -
Dear {client.upper()} Accounts Team,
Subject: Annual review for {fy}
Please find attached the documents requested for the {fy} audit.
Regards,
Senior Audit Manager
""".encode()


# ---------------------------------------------------------------------------
# Encrypted zip helper (patches central directory flag_bits)
# ---------------------------------------------------------------------------

def make_encrypted_zip(path: Path, members: dict) -> None:
    """
    Create a zip that appears encrypted.

    Python's zipfile cannot write real encrypted zips. We create a normal zip
    then patch the encryption flag (bit 0) in both the local file header (LFH,
    flag at +6) and the central directory header (CDH, flag at +8).

    zipfile.ZipInfo.flag_bits reads from the CDH — patching only the LFH is
    not sufficient for detection via infolist().
    """
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)

    data = bytearray(path.read_bytes())

    for sig, offset in [(b"PK\x03\x04", 6), (b"PK\x01\x02", 8)]:
        pos = 0
        while True:
            idx = data.find(sig, pos)
            if idx == -1:
                break
            data[idx + offset] = data[idx + offset] | 0x01
            pos = idx + 4

    path.write_bytes(bytes(data))


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def create_sandbox(root: Path, overwrite: bool = False) -> None:
    archive = root / "archive"

    if archive.exists():
        if overwrite:
            shutil.rmtree(archive)
        else:
            print(f"Archive already exists at {archive}")
            print("Use --overwrite to recreate.")
            return

    flat_files: list[Path] = []
    dup_groups: list[tuple] = []
    zip_notes: list[tuple] = []

    def write(path: Path, content: bytes) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        flat_files.append(path)
        return path

    # -------------------------------------------------------------------------
    # ACME — FY2022, FY2023, FY2024
    # -------------------------------------------------------------------------

    acme_tax_24  = write(archive / "acme/FY2024/tax_return_FY2024.txt",      tax_doc("acme", "FY2024"))
    acme_lgl_24  = write(archive / "acme/FY2024/legal_notice_FY2024.txt",    legal_doc("acme", "FY2024"))
    acme_acc_24  = write(archive / "acme/FY2024/balance_sheet_FY2024.txt",   accounts_doc("acme", "FY2024"))
    acme_cor_24  = write(archive / "acme/FY2024/correspondence_FY2024.txt",  correspondence_doc("acme", "FY2024"))

    acme_tax_23  = write(archive / "acme/FY2023/tax_return_FY2023.txt",      tax_doc("acme", "FY2023"))
    acme_acc_23  = write(archive / "acme/FY2023/balance_sheet_FY2023.txt",   accounts_doc("acme", "FY2023"))
    acme_cor_23  = write(archive / "acme/FY2023/correspondence_FY2023.txt",  correspondence_doc("acme", "FY2023"))

    acme_tax_22  = write(archive / "acme/FY2022/tax_return_FY2022.txt",      tax_doc("acme", "FY2022"))
    acme_acc_22  = write(archive / "acme/FY2022/balance_sheet_FY2022.txt",   accounts_doc("acme", "FY2022"))

    # Duplicate group A: tax_return_FY2024 copied to two locations (dup of dup)
    dup_a1 = write(archive / "acme/FY2024/backup/tax_return_FY2024.txt",     acme_tax_24.read_bytes())
    dup_a2 = write(archive / "acme/old/copy_of_tax_return_2024.txt",         acme_tax_24.read_bytes())
    dup_groups.append((acme_tax_24, [dup_a1, dup_a2], "acme tax FY2024 — 3 copies"))

    # Duplicate group B: balance sheet copied once
    dup_b1 = write(archive / "acme/shared/balance_sheet_copy.txt",           acme_acc_24.read_bytes())
    dup_groups.append((acme_acc_24, [dup_b1], "acme accounts FY2024 — 2 copies"))

    # Same filename as a duplicate, but DIFFERENT content — must NOT dedup
    write(archive / "acme/old/tax_return_FY2024_revised.txt",                tax_doc("acme", "FY2024", variant="revised"))

    # -------------------------------------------------------------------------
    # GLOBEX - FY2023, FY2024
    # -------------------------------------------------------------------------

    globex_tax_24 = write(archive / "globex/FY2024/tax_return_FY2024.txt",   tax_doc("globex", "FY2024"))
    globex_lgl_24 = write(archive / "globex/FY2024/legal_notice_FY2024.txt", legal_doc("globex", "FY2024"))
    globex_lgl_23 = write(archive / "globex/FY2023/legal_notice_FY2023.txt", legal_doc("globex", "FY2023"))
    globex_acc_23 = write(archive / "globex/FY2023/accounts_FY2023.txt",     accounts_doc("globex", "FY2023"))

    # Duplicate group C
    dup_c1 = write(archive / "globex/backup/tax_return_FY2024.txt",          globex_tax_24.read_bytes())
    dup_groups.append((globex_tax_24, [dup_c1], "globex tax FY2024 — 2 copies"))

    # -------------------------------------------------------------------------
    # INITECH — FY2022
    # -------------------------------------------------------------------------

    initech_lgl_22 = write(archive / "initech/FY2022/contract_FY2022.txt",       legal_doc("initech", "FY2022"))
    initech_acc_22 = write(archive / "initech/FY2022/balance_sheet_FY2022.txt",  accounts_doc("initech", "FY2022"))
    initech_tax_22 = write(archive / "initech/FY2022/tax_return_FY2022.txt",     tax_doc("initech", "FY2022"))

    # -------------------------------------------------------------------------
    # ZIP FILES
    # -------------------------------------------------------------------------

    zips = archive / "zips"
    zips.mkdir(parents=True, exist_ok=True)

    # Zip 1: 2 known files + 1 new file (the new one was never in flat corpus)
    new_memo = b"""INTERNAL MEMO - ACME - FY2023
Date: 2023-06-15
Subject: FY2023 filing deadline reminder
Action required: submit workpapers by 30 June.
This document existed only in the zip archive.
"""
    with zipfile.ZipFile(zips / "acme_archive_FY2023.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("acme/FY2023/tax_return_FY2023.txt",    acme_tax_23.read_bytes())  # known
        zf.writestr("acme/FY2023/balance_sheet_FY2023.txt", acme_acc_23.read_bytes())  # known
        zf.writestr("acme/FY2023/internal_memo_jun2023.txt", new_memo)                 # NEW
    zip_notes.append(("acme_archive_FY2023.zip", "2 known + 1 new (internal_memo_jun2023.txt)"))

    # Zip 2: 1 known + 1 new
    new_addendum = b"""GLOBEX CONTRACT ADDENDUM - FY2023
Date: 2023-09-01
Pursuant to the master services agreement dated 2023-01-01,
the following addendum applies to the FY2023 engagement.
This document was archived in a zip and not in the flat corpus.
"""
    with zipfile.ZipFile(zips / "globex_backup_FY2023.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("globex/FY2023/legal_notice_FY2023.txt", globex_lgl_23.read_bytes())  # known
        zf.writestr("globex/FY2023/contract_addendum.txt",   new_addendum)                # NEW
    zip_notes.append(("globex_backup_FY2023.zip", "1 known + 1 new (contract_addendum.txt)"))

    # Zip 3: backup of a backup (zip-within-zip, depth 2)
    with zipfile.ZipFile(zips / "backup_of_backup.zip", "w") as zf:
        zf.write(zips / "acme_archive_FY2023.zip", "acme_archive_FY2023.zip")
        zf.writestr("manifest.txt", b"Backup created 2024-01-01\nContains: acme_archive_FY2023.zip\n")
    zip_notes.append(("backup_of_backup.zip", "depth 2 — contains acme_archive_FY2023.zip"))

    # Zip 4: three levels of nesting — deep_document.txt only reachable at depth 3
    deep_doc = b"""DEEP NESTED DOCUMENT
This document is nested three zip levels deep.
It tests the MAX_DEPTH=4 limit in the zip archaeologist.
If you are reading this, the depth limit was not exceeded.
"""
    _inner  = zips / "_tmp_inner.zip"
    _middle = zips / "_tmp_middle.zip"
    with zipfile.ZipFile(_inner, "w") as zf:
        zf.writestr("deep_document.txt", deep_doc)
        zf.writestr("also_deep.txt", b"Another document at depth 3.\n")
    with zipfile.ZipFile(_middle, "w") as zf:
        zf.write(_inner, "level2/inner_archive.zip")
        zf.writestr("level2/readme.txt", b"Level 2 of nested zip.\n")
    with zipfile.ZipFile(zips / "nested_depth3_outer.zip", "w") as zf:
        zf.write(_middle, "level1/middle_archive.zip")
        zf.writestr("level1/readme.txt", b"Level 1 of nested zip.\n")
    _inner.unlink()
    _middle.unlink()
    zip_notes.append(("nested_depth3_outer.zip", "depth 3 — deep_document.txt only reachable at level 3"))

    # Zip 5: encrypted — will trigger escalation in zip_archaeologist
    make_encrypted_zip(
        zips / "confidential_board_minutes.zip",
        {"board/minutes_FY2024.txt": b"Board minutes FY2024 - CONFIDENTIAL\nPassword hint: audit2024\n"}
    )
    zip_notes.append(("confidential_board_minutes.zip", "ENCRYPTED — triggers escalation"))

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------

    zip_files  = list(zips.glob("*.zip"))
    total_size = sum(f.stat().st_size for f in flat_files) + sum(z.stat().st_size for z in zip_files)
    unique_hashes = len(set(hashlib.sha256(f.read_bytes()).hexdigest() for f in flat_files))
    dup_file_count = len(flat_files) - unique_hashes

    print(f"\n✅  Provenance test sandbox created at {root}")
    print(f"\n    Archive: {archive}")
    print(f"\n{'─'*64}")
    print(f"  Flat files:          {len(flat_files):>4}")
    print(f"  Unique files (SHA):  {unique_hashes:>4}  (scanner will find {dup_file_count} duplicates)")
    print(f"  Zip files:           {len(zip_files):>4}")
    print(f"  Total size:          {total_size / 1024:>6.1f} KB")
    print(f"\n  Duplicate groups:")
    for original, dups, note in dup_groups:
        print(f"    {note}")
        print(f"      original: {original.relative_to(archive)}")
        for d in dups:
            print(f"      copy:     {d.relative_to(archive)}")
    print(f"\n  Zip files:")
    for name, notes in zip_notes:
        print(f"    {name}")
        print(f"      → {notes}")
    print(f"\n{'─'*64}")
    print(f"  Expected scan results:")
    print(f"    files_scanned:     {len(flat_files)}")
    print(f"    unique_files:      {unique_hashes}")
    print(f"    duplicate_files:   {dup_file_count}")
    print(f"    zip_files:         {len(zip_files)}")
    print(f"\n  Expected zip archaeology:")
    print(f"    new-to-corpus:     2  (internal_memo_jun2023.txt, contract_addendum.txt)")
    print(f"    known files:       3  (files already in flat corpus)")
    print(f"    encrypted:         1  (confidential_board_minutes.zip → escalation)")
    print(f"    max nesting depth: 3  (nested_depth3_outer.zip)")
    print(f"\n{'─'*64}")
    print(f"  To run:")
    print(f"\n    export PROVENANCE_NAS_PATH={archive}")
    print(f"    export PROVENANCE_DB_PATH={root}/corpus.duckdb")
    print(f"    mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs")
    print()


import hashlib  # noqa: E402 (used in create_sandbox above, imported here for clarity)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a local test sandbox for Provenance end-to-end testing"
    )
    parser.add_argument(
        "--root",
        default=str(Path.home() / "sandbox/provenance-test"),
        help="Root directory (default: ~/sandbox/provenance-test)"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete and recreate the archive if it already exists"
    )
    args = parser.parse_args()
    create_sandbox(Path(args.root).expanduser(), overwrite=args.overwrite)


if __name__ == "__main__":
    main()
