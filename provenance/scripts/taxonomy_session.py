#!/usr/bin/env python3
"""
Taxonomy session — interactive CLI that interviews a senior auditor and writes
agents/taxonomy.md. Run with --non-interactive for CI / template generation.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# ~8 000 chars ≈ 2 000 tokens; warn if exceeded
TOKEN_WARN_CHARS = 8_000

DEFAULT_DOC_TYPES = ["tax", "legal", "accounts", "correspondence", "other"]

DOC_TYPE_DEFAULTS = {
    "tax": {
        "keywords": "BAS, GST, tax return, income statement, PAYG, franking credits",
        "filename_signals": "tax, bas, gst, return",
        "content_signals": '"Australian Taxation Office", "taxable income", "ATO"',
    },
    "legal": {
        "keywords": "notice, deed, contract, agreement, court, ASIC, litigation",
        "filename_signals": "legal, notice, deed, contract, agreement",
        "content_signals": '"Australian Securities and Investments Commission", "pursuant to"',
    },
    "accounts": {
        "keywords": "balance sheet, profit and loss, trial balance, workpapers, journal",
        "filename_signals": "accounts, balance, pl, tb, workpaper",
        "content_signals": '"Total assets", "Net profit", "equity"',
    },
    "correspondence": {
        "keywords": "letter, email, memo, correspondence",
        "filename_signals": "letter, email, memo, corr",
        "content_signals": '"Dear", "Regards", "Subject:"',
    },
    "other": {
        "keywords": "miscellaneous",
        "filename_signals": "",
        "content_signals": "",
    },
}

CLASSIFICATION_RULES = """\
## Classification rules (for the agent)

When classifying a document:
1. Check the file path for client ID or known alias
2. Check the first 20 lines for client name, FY indicators, and document keywords
3. If confident (>0.85): assign client, FY, doc_type directly
4. If uncertain (0.50–0.85): assign best guess, set confidence accordingly
5. If client unidentifiable (<0.50): set client = "unknown", doc_type as best effort

For binary files (PDF, DOCX) where content is not readable as text:
- Classify from path and filename only
- Cap confidence at 0.65 for path-only classifications
- Set raw_excerpt to "binary file — classified from path and filename only"
"""


# ---------------------------------------------------------------------------
# Interactive session
# ---------------------------------------------------------------------------

def _ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        return default
    return answer if answer else default


def _ask_list(prompt: str, default: str = "") -> list[str]:
    raw = _ask(prompt, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def run_interactive(auditor: str) -> str:
    print("\n=== Provenance Taxonomy Session ===")
    print("Answer each question. Press Enter to accept the default.\n")

    # --- Section 1: Clients ---
    print("─── 1. Clients ───────────────────────────────────")
    client_ids = _ask_list(
        "Client IDs used in filenames/folders (comma-separated, e.g. ACME, globex)"
    )
    if not client_ids:
        client_ids = ["[CLIENT_ID]"]

    clients = []
    for cid in client_ids:
        full_name = _ask(f"  Full name for '{cid}'", cid)
        aliases = _ask(f"  Aliases for '{cid}' (comma-separated, or Enter to skip)")
        notes = _ask(f"  Notes for '{cid}' (or Enter to skip)")
        clients.append((cid, full_name, aliases, notes))

    isolated = _ask(
        "Clients whose files are never mixed with others (comma-separated, or Enter)",
        ""
    )

    # --- Section 2: Financial year ---
    print("\n─── 2. Financial year convention ─────────────────")
    fy_type = _ask("Calendar year (Jan–Dec) or Australian/UK FY (Apr–Mar)? [cal/fy]", "fy")
    fy_label = _ask("FY label format in filenames (e.g. FY2024, 2023-24, FY24)", "FY{YYYY}")
    fy_boundary = _ask("Month that starts the financial year (e.g. April, January)", "April")

    # --- Section 3: Document types ---
    print("\n─── 3. Document types ────────────────────────────")
    type_input = _ask(
        "Document categories (comma-separated)",
        ",".join(DEFAULT_DOC_TYPES)
    )
    doc_types_list = [t.strip() for t in type_input.split(",") if t.strip()]

    doc_types = {}
    for dt in doc_types_list:
        print(f"\n  → '{dt}'")
        defaults = DOC_TYPE_DEFAULTS.get(dt, {"keywords": "", "filename_signals": "", "content_signals": ""})
        kw = _ask(f"    Keywords", defaults["keywords"])
        fn = _ask(f"    Filename signals", defaults["filename_signals"])
        cs = _ask(f"    Content signals", defaults["content_signals"])
        doc_types[dt] = {"keywords": kw, "filename_signals": fn, "content_signals": cs}

    # --- Section 4: Naming patterns ---
    print("\n─── 4. Naming patterns ───────────────────────────")
    includes_client = _ask("Filenames typically include client name? [y/n]", "y")
    includes_year = _ask("Filenames typically include the year? [y/n]", "y")
    affixes = _ask("Common prefixes/suffixes (e.g. DRAFT, FINAL, v2 — or Enter to skip)", "DRAFT, FINAL, v2, _signed")
    language = _ask("Language of most document headers", "English")

    # --- Section 5: Special cases ---
    print("\n─── 5. Special cases ─────────────────────────────")
    multi_client = _ask("Documents spanning multiple clients? How to handle? (or Enter to skip)")
    confidential = _ask("Confidential markers to watch for? (or Enter to skip)")
    path_rules = _ask("Path patterns always mapping to a specific client? (or Enter to skip)")

    return _render(
        auditor=auditor,
        clients=clients,
        isolated=isolated,
        fy_type=fy_type,
        fy_label=fy_label,
        fy_boundary=fy_boundary,
        doc_types=doc_types,
        includes_client=includes_client,
        includes_year=includes_year,
        affixes=affixes,
        language=language,
        multi_client=multi_client,
        confidential=confidential,
        path_rules=path_rules,
    )


# ---------------------------------------------------------------------------
# Non-interactive template
# ---------------------------------------------------------------------------

def run_non_interactive() -> str:
    clients = [
        ("acme",    "Acme Pty Ltd",    "ACME, acme_pty", "Primary client"),
        ("globex",  "Globex Corp",     "GLOBEX",          ""),
        ("initech", "Initech Ltd",     "",                ""),
    ]
    doc_types = {dt: DOC_TYPE_DEFAULTS.get(dt, {}) for dt in DEFAULT_DOC_TYPES}

    return _render(
        auditor="[AUDITOR NAME]",
        clients=clients,
        isolated="",
        fy_type="fy",
        fy_label="FY{YYYY}",
        fy_boundary="April",
        doc_types=doc_types,
        includes_client="y",
        includes_year="y",
        affixes="DRAFT, FINAL, v2, _signed",
        language="English",
        multi_client="Assign to the client whose name appears first in the file path.",
        confidential="CONFIDENTIAL, PRIVILEGED",
        path_rules="Paths containing /personal/ are always client = 'unknown'.",
    )


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def _render(
    auditor, clients, isolated, fy_type, fy_label, fy_boundary,
    doc_types, includes_client, includes_year, affixes, language,
    multi_client, confidential, path_rules,
) -> str:
    lines = [
        "# Provenance Document Taxonomy",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Auditor: {auditor}",
        "",
        "## Clients",
        "",
        "| Client ID | Full name | Aliases | Notes |",
        "|-----------|-----------|---------|-------|",
    ]
    for cid, full, aliases, notes in clients:
        lines.append(f"| {cid} | {full} | {aliases or '—'} | {notes or '—'} |")

    if isolated:
        lines += ["", f"**Isolated clients** (files never mixed): {isolated}"]

    # FY
    if fy_type.lower() == "fy":
        fy_desc = f"Format: {fy_label} (April–March)"
        fy_example = "FY2024 = April 2023 – March 2024"
    else:
        fy_desc = f"Format: {fy_label} (January–December)"
        fy_example = "2024 = January 2024 – December 2024"

    lines += [
        "",
        "## Financial year convention",
        "",
        f"- {fy_desc}",
        f"- Example: {fy_example}",
        f"- Boundary month: {fy_boundary}",
    ]

    # Doc types
    lines += ["", "## Document types", ""]
    for dt, info in doc_types.items():
        lines.append(f"### {dt}")
        if info.get("keywords"):
            lines.append(f"Keywords: {info['keywords']}")
        if info.get("filename_signals"):
            lines.append(f"Filename signals: {info['filename_signals']}")
        if info.get("content_signals"):
            lines.append(f"Content signals: {info['content_signals']}")
        lines.append("")

    # Classification rules (static)
    lines += ["", CLASSIFICATION_RULES.strip(), ""]

    # Naming patterns
    lines += [
        "",
        "## Naming patterns",
        "",
        f"- Filenames include client name: {'yes' if includes_client.lower().startswith('y') else 'no'}",
        f"- Filenames include year: {'yes' if includes_year.lower().startswith('y') else 'no'}",
    ]
    if affixes:
        lines.append(f"- Common affixes: {affixes}")
    lines.append(f"- Document language: {language}")

    # Edge cases
    lines += ["", "## Edge cases", ""]
    edge_items = [
        ("Multi-client documents", multi_client),
        ("Confidential markers", confidential),
        ("Path-to-client rules", path_rules),
    ]
    for label, value in edge_items:
        if value:
            lines.append(f"**{label}:** {value}")
        else:
            lines.append(f"**{label}:** _(none specified)_")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Provenance taxonomy session")
    parser.add_argument("--output", default="agents/taxonomy.md", help="Output path")
    parser.add_argument("--auditor", default="", help="Auditor name")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Write a placeholder template without prompting",
    )
    args = parser.parse_args()

    if args.non_interactive:
        content = run_non_interactive()
    else:
        auditor = args.auditor or _ask("Auditor name")
        content = run_interactive(auditor)

    if len(content) > TOKEN_WARN_CHARS:
        print(
            f"Warning: taxonomy is {len(content)} chars (~{len(content)//4} tokens). "
            f"Consider consolidating to stay under ~2 000 tokens.",
            file=sys.stderr,
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content)
    print(str(out))


if __name__ == "__main__":
    main()
