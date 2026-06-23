"""Resolve "same as last month" from the run log (m3 t3).

Finds the most recent run-log entry matching {tenant, doc_type, client_name}, copies
its context, and produces the NEXT period's context deterministically:
  - `date`            → month-end of the target month (default: current month).
  - `invoice_number`  → `{FY}/{client_code}/{seq+1}` with the financial year rolling on
                        April 1 (month >= 4 → FY of {year}-{year+1}; else {year-1}-{year}).
                        FY code = last two digits of each year, e.g. 2026-27 → "2627"
                        (matches the committed Bitloka invoice format).
  - `title`           → the old invoice number substring is replaced with the new one.
  - all other fields  → carried forward verbatim (client_*, order_ref, terms, amount_due…).

This replaces the provisional LLM math in context_builder (t2): the agent calls this
script and writes its output as confirmed_context.json. Graceful when there is no prior
run (prints `{"status": "no_prior_run"}`, exit 0 — the caller falls back to the request).

Exit codes: 0 on success or no-prior-run; 1 if the run log is unreadable, --target-month
is malformed, or no matching client/doc_type entry's invoice number can be parsed (the
date bump still applies; a warning is emitted to stderr but the run does not fail).
"""

import argparse
import calendar
import json
import sys
from datetime import datetime
from pathlib import Path

from run_log_writer import _load_log  # reuse: missing/empty → []; malformed → raises


def fy_code(year, month):
    """Financial-year code, last two digits of each year. FY rolls on April 1:
    month >= 4 → {year}-{year+1}; else {year-1}-{year}. e.g. (2026, 6) → "2627"."""
    start = year if month >= 4 else year - 1
    end = start + 1
    return f"{start % 100:02d}{end % 100:02d}"


def month_end(year, month):
    """Last calendar day of the month as 'DD-Mon-YYYY' (e.g. (2026, 6) → '30-Jun-2026')."""
    last = calendar.monthrange(year, month)[1]
    return f"{last:02d}-{calendar.month_abbr[month]}-{year}"


def bump_invoice_number(invoice_number, target_year, target_month):
    """`{FY}/{client_code}/{seq}` → `{new_FY}/{client_code}/{seq+1}`, preserving the
    sequence's zero-pad width. Returns None if the value isn't in the expected 3-part
    `FY/code/seq` shape with a numeric sequence."""
    parts = invoice_number.split("/")
    if len(parts) != 3:
        return None
    _fy, client_code, seq_str = parts
    try:
        seq = int(seq_str)
    except ValueError:
        return None
    width = len(seq_str)
    return f"{fy_code(target_year, target_month)}/{client_code}/{seq + 1:0{width}d}"


def _client_match(query, entry_client):
    q = (query or "").lower().strip()
    c = (entry_client or "").lower().strip()
    if not q or not c:
        return False
    return q == c or q in c or c in q


def find_last_match(log, tenant, doc_type, client_name):
    """Most recent entry matching {tenant, doc_type, client_name}. 'Most recent' = max
    timestamp, tie-broken by array order (append/replace semantics put the latest write
    last). client_name matches case-insensitively, allowing substring either direction
    (so "XYZ" matches "XYZ Inc")."""
    matches = [
        (i, e) for i, e in enumerate(log)
        if e.get("tenant") == tenant
        and e.get("doc_type") == doc_type
        and _client_match(client_name, (e.get("context") or {}).get("client_name", ""))
    ]
    if not matches:
        return None
    return max(matches, key=lambda ie: ((ie[1].get("timestamp") or ""), ie[0]))[1]


def resolve(log, tenant, doc_type, client_name, target_year, target_month):
    """Return (new_context, matched_entry, warnings) or (None, None, []) if no match."""
    match = find_last_match(log, tenant, doc_type, client_name)
    if match is None:
        return None, None, []

    ctx = dict(match.get("context") or {})
    warnings = []

    ctx["date"] = month_end(target_year, target_month)

    old_inv = ctx.get("invoice_number")
    if old_inv:
        new_inv = bump_invoice_number(old_inv, target_year, target_month)
        if new_inv:
            if ctx.get("title") and old_inv in ctx["title"]:
                ctx["title"] = ctx["title"].replace(old_inv, new_inv)
            ctx["invoice_number"] = new_inv
        else:
            warnings.append(
                f"invoice_number '{old_inv}' not in FY/code/seq form; left unchanged"
            )

    return ctx, match, warnings


def _parse_target_month(s):
    """'YYYY-MM' → (year, month). Default (None) → current calendar month."""
    if not s:
        now = datetime.now()
        return now.year, now.month
    # maxsplit=1 so a 3-part value like "2026-06-01" yields ("2026", "06-01") and
    # int("06-01") raises a clean ValueError (caught by main) rather than an unhandled
    # "too many values to unpack".
    year_s, month_s = s.split("-", 1)
    year, month = int(year_s), int(month_s)
    if not 1 <= month <= 12:
        raise ValueError(f"month out of range in --target-month '{s}'")
    return year, month


def main():
    parser = argparse.ArgumentParser(
        description='Resolve "same as last month" from the run log.')
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--doc-type", required=True)
    parser.add_argument("--client-name", required=True)
    parser.add_argument("--target-month", default=None,
                        help="YYYY-MM of the new document; default = current month")
    parser.add_argument("--run-log", default="data/run_log.json")
    parser.add_argument("--output", default=None,
                        help="write the resolved context JSON to FILE and print only the "
                             "path (default: print the context to stdout)")
    args = parser.parse_args()

    try:
        target_year, target_month = _parse_target_month(args.target_month)
    except ValueError as e:
        print(json.dumps({"status": "error", "error": f"bad --target-month: {e}"}),
              file=sys.stderr)
        sys.exit(1)

    try:
        log = _load_log(args.run_log)
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"run log unreadable: {e}"}),
              file=sys.stderr)
        sys.exit(1)

    ctx, match, warnings = resolve(
        log, args.tenant, args.doc_type, args.client_name, target_year, target_month)

    if ctx is None:
        print(json.dumps({
            "status": "no_prior_run",
            "tenant": args.tenant, "doc_type": args.doc_type,
            "client_name": args.client_name,
        }))
        sys.exit(0)

    for w in warnings:
        print(json.dumps({"status": "warning", "warning": w}), file=sys.stderr)
    # Resolution summary to stderr (does not pollute the stdout/file contract).
    print(json.dumps({
        "status": "resolved",
        "matched_run_id": match.get("run_id"),
        "new_invoice_number": ctx.get("invoice_number"),
        "new_date": ctx.get("date"),
    }), file=sys.stderr)

    out = json.dumps(ctx, indent=2, ensure_ascii=False)
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(out + "\n", encoding="utf-8")
        print(str(p))
    else:
        print(out)


if __name__ == "__main__":
    main()
