#!/usr/bin/env python3
"""Extract SalesOrder from a Boxy Sales Order PDF (pdfplumber).

Usage:
    python3 scripts/so_extractor.py --so <pdf> --project <name> --output-dir <dir>

Writes {output_dir}/{project}/sales_order.json.
Prints a one-line summary to stdout.  Errors to stderr.
"""

import argparse
import datetime
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
from schema import SalesOrder, SOHeader, SOLineItem

# ── Column x-boundaries (points) calibrated from SO86708_Aria_Joey.pdf ────────
# Derived from header word x0 positions:
#   Quantity=48.1  Item=100.8  Special=340.8  Rate=472.8  Amount=538.8
_QTY_X_MAX  =  90.0   # qty column upper bound
_SPECIAL_X  = 340.0   # Special Request column start
_RATE_X     = 460.0   # Rate column start (rate values may land left of header)
_AMOUNT_X   = 530.0   # Amount column start

_MONEY_RE = re.compile(r'\$([\d,]+\.\d{2})')
_DATE_RE  = re.compile(r'(\d{1,2})/(\d{1,2})/(\d{4})')
_FEE_RE   = re.compile(
    r'^(Assembly Fee|Modify-[SL]|Delivery fee|Installation fee.*)',
    re.IGNORECASE,
)


# ── Low-level helpers ──────────────────────────────────────────────────────────

def _parse_money(s: str) -> float:
    return float(re.sub(r'[$,]', '', s))


def _to_iso_date(s: str) -> str:
    m = _DATE_RE.search(s)
    if not m:
        return s
    return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"


def _group_rows(words: list[dict], tol: float = 4.0) -> list[list[dict]]:
    """Group word dicts into lines by approximate top (y) coordinate."""
    if not words:
        return []
    srt = sorted(words, key=lambda w: (round(w['top'] / tol) * tol, w['x0']))
    rows: list[list[dict]] = [[srt[0]]]
    cur_top = srt[0]['top']
    for w in srt[1:]:
        if abs(w['top'] - cur_top) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
            cur_top = w['top']
    return rows


def _split_cols(row: list[dict]) -> dict[str, str]:
    """Assign each word to a table column by x-coordinate."""
    qty, item, special, rate, amount = [], [], [], [], []
    for w in sorted(row, key=lambda x: x['x0']):
        x, t = w['x0'], w['text']
        if   x < _QTY_X_MAX: qty.append(t)
        elif x < _SPECIAL_X: item.append(t)
        elif x < _RATE_X:    special.append(t)
        elif x < _AMOUNT_X:  rate.append(t)
        else:                 amount.append(t)
    return {k: ' '.join(v) for k, v in
            zip(('qty', 'item', 'special', 'rate', 'amount'),
                (qty, item, special, rate, amount))}


def _extract_sku(item_t: str) -> str:
    """Return the SKU from item-column text.

    Products: first hyphenated/digit token.  Fees: full text (they have spaces
    but no leading digit or hyphen in their first word).
    """
    if not item_t:
        return ''
    first = item_t.split()[0]
    if '-' not in first and not first[0].isdigit():
        return item_t   # multi-word fee name
    return first


def _finalise(p: dict) -> SOLineItem:
    sku = p['sku']
    return SOLineItem(
        line=p['line'],
        sku=sku,
        description=' '.join(p['desc']).strip(),
        qty=p['qty'],
        unit_price=p['unit_price'],
        amount=p['amount'],
        special_request=' '.join(p['special']).strip() or None,
        is_fee=bool(_FEE_RE.match(sku)),
        is_accessory=sku.startswith('Accs-'),
    )


# ── Line-item extractor ────────────────────────────────────────────────────────

def _parse_line_items(pages: list) -> list[SOLineItem]:
    """Extract SOLineItem records from the table on pages 1-3.

    Rate values in this PDF are right-aligned and may render to the left of the
    Rate column header, landing inside the Special Request column range.  When
    the spec cell ends with a $NNN.NN token that is absent from the rate cell,
    that token is the unit price.
    """
    pending: dict | None = None
    items: list[SOLineItem] = []
    done = False
    line_num = 0

    for page in pages:
        if done:
            break
        in_table = False   # reset per page (each page has a repeating header)

        for row in _group_rows(page.extract_words()):
            c = _split_cols(row)
            qty_t    = c['qty'].strip()
            item_t   = c['item'].strip()
            spec_t   = c['special'].strip()
            rate_t   = c['rate'].strip()
            amount_t = c['amount'].strip()

            # Detect table header row
            if 'Quantity' in qty_t and 'Item' in item_t:
                in_table = True
                continue

            # Detect end of table
            if in_table and 'Subtotal' in spec_t:
                done = True
                break

            if not in_table:
                continue

            is_primary = bool(re.match(r'^\d+$', qty_t)) and '$' in amount_t

            if is_primary:
                if pending:
                    items.append(_finalise(pending))
                line_num += 1
                sku = _extract_sku(item_t)

                # Extract unit price: last $NNN.NN in spec (right-aligned overspill)
                # or from the explicit rate cell when spec has none.
                spec_monies = _MONEY_RE.findall(spec_t)
                if spec_monies:
                    unit_price  = _parse_money(spec_monies[-1])
                    special_start = _MONEY_RE.sub('', spec_t).strip().rstrip(',').strip()
                elif rate_t.startswith('$'):
                    unit_price  = _parse_money(rate_t)
                    special_start = spec_t
                else:
                    unit_price  = 0.0
                    special_start = spec_t

                pending = {
                    'line': line_num,
                    'sku': sku,
                    'desc': [],
                    'qty': int(qty_t),
                    'unit_price': unit_price,
                    'amount': _parse_money(amount_t),
                    'special': [special_start] if special_start else [],
                }
            else:
                if pending is None:
                    continue
                if item_t:
                    pending['desc'].append(item_t)
                if spec_t:
                    pending['special'].append(spec_t)

    if pending:
        items.append(_finalise(pending))

    return items


# ── Header and totals ──────────────────────────────────────────────────────────

def _parse_header(page) -> SOHeader:
    text = page.extract_text() or ''

    m = re.search(r'#(SO\d+)', text)
    order_number = m.group(1) if m else ''

    dates = _DATE_RE.findall(text)
    order_date = (f"{dates[0][2]}-{int(dates[0][0]):02d}-{int(dates[0][1]):02d}"
                  if dates else '')

    m = re.search(r'Estimate #(EST\d+)', text)
    estimate_number = m.group(1) if m else None

    # Company name repeats in all three address columns
    m = re.search(r'Bill To Ship To Customer\n(.+)', text)
    customer_name = ''
    if m:
        words = m.group(1).split()
        n = max(1, len(words) // 3)
        customer_name = ' '.join(words[:n])

    # Payment Term data line: "COD  PO#  AccountMgr...  ShipDate"
    m = re.search(r'Payment Term.*\n(.+)', text)
    payment_term = po_number = account_manager = ship_date = None
    if m:
        tokens = m.group(1).strip().split()
        if tokens:
            payment_term = tokens[0]
        if len(tokens) > 1:
            po_number = tokens[1]
        if len(tokens) > 2:
            remaining = list(tokens[2:])
            if remaining and _DATE_RE.match(remaining[-1]):
                ship_date = _to_iso_date(remaining.pop())
            account_manager = ' '.join(remaining) or None

    return SOHeader(
        order_number=order_number,
        order_date=order_date,
        customer=customer_name,
        bill_to=customer_name,
        ship_to=customer_name,
        estimate_number=estimate_number,
        payment_term=payment_term,
        po_number=po_number,
        account_manager=account_manager,
        ship_date=ship_date,
        memo=None,
    )


def _parse_totals(page3) -> tuple[float, float, float]:
    text = page3.extract_text() or ''
    m = re.search(r'Subtotal\s+\$([\d,]+\.\d{2})', text)
    subtotal = _parse_money(m.group(1)) if m else 0.0
    m = re.search(r'Tax Total[^$]*\$([\d,]+\.\d{2})', text)
    tax_total = _parse_money(m.group(1)) if m else 0.0
    # findall returns [tax_total_amount, final_total_amount]; take last
    matches = re.findall(r'\bTotal\b\s+\$([\d,]+\.\d{2})', text)
    total = _parse_money(matches[-1]) if matches else subtotal
    return subtotal, tax_total, total


# ── Public entry point ─────────────────────────────────────────────────────────

def extract_so(so_path: Path) -> SalesOrder:
    """Extract and return a SalesOrder from a Boxy SO PDF."""
    with pdfplumber.open(so_path) as pdf:
        header     = _parse_header(pdf.pages[0])
        line_items = _parse_line_items(pdf.pages[:3])
        subtotal, tax_total, total = _parse_totals(pdf.pages[2])

    return SalesOrder(
        header=header,
        line_items=line_items,
        subtotal=subtotal,
        tax_total=tax_total,
        total=total,
        source_file=so_path.name,
        extracted_at=datetime.datetime.now().isoformat(timespec='seconds'),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract Boxy SO PDF to sales_order.json."
    )
    parser.add_argument('--so',         required=True, type=Path,   metavar='PDF')
    parser.add_argument('--project',    required=True,              metavar='NAME')
    parser.add_argument('--output-dir', default='data/projects',
                        type=Path, metavar='DIR')
    args = parser.parse_args()

    if not args.so.exists():
        print(f"Error: SO file not found: {args.so}", file=sys.stderr)
        sys.exit(1)

    try:
        so = extract_so(args.so)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    out_dir = args.output_dir / args.project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'sales_order.json'
    with open(out_path, 'w') as f:
        json.dump(asdict(so), f, indent=2)

    print(
        f"SO {so.header.order_number} — {len(so.line_items)} items — "
        f"${so.total:,.2f} — {out_path}"
    )


if __name__ == '__main__':
    main()
