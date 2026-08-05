#!/usr/bin/env python3
"""Re-record the Linode fixtures from a live account. Operator-run, not collected by pytest.

The committed `linode_*.json` fixtures are raw APIv4 response envelopes — what the adapter's
client receives, page envelope included — scrubbed of account-identifying detail. This script
is how they are refreshed: it reuses the adapter's own client and token loader (so it
authenticates exactly the way the adapter does), calls each endpoint the sweep makes, scrubs,
and writes the files.

Run it under the D2 hermetic prefix, from the repo root:

    set -a; . ~/.secrets/linode-cloudcost.env; set +a
    env -u LINODE_CLI_TOKEN -u LINODE_TOKEN \\
        python3 cloudcost/tests/record_linode_fixtures.py --out /tmp/recorded

It writes to `--out` (default: a scratch dir), never over `tests/fixtures/` directly — a
recording is reviewed before it replaces a committed fixture.

**Scrubbing is code, not a manual pass.** Account identifiers, IP addresses, hostnames, `rdns`
and token-shaped strings are replaced by stable placeholders on the way out; a recording that
still carries a real identifier is a defect this script must catch, not the reviewer. The
placeholder mapping is first-seen-order and deterministic, so re-recording the same account
produces byte-identical fixtures except where the account itself changed. What is *not* stable
across runs, by construction: `created`/`updated`/`date` timestamps, `balance` and
`balance_uninvoiced`, and invoice item `quantity`/`amount` for the in-flight month. The
committed fixtures therefore pin a *settled* period, not the current one.

This file deliberately does **not** import from `record_aws_fixtures.py` — a CLI-to-CLI import
is the anti-pattern named at `_normalized.py:35-37`. The shape and posture are copied; the
scrub table, the endpoint list and the findings report are Linode's own.

It also prints a **findings report** to stdout: the evidence for the three questions t1 must
settle from live reads rather than from the spec —

  * §D-L4 / U1 — how many instances exist and the distinct `status` values across them. The
    enum holds two terminal powered-off spellings (`offline`, `stopped`) and `stopped`
    collides with the canonical value while denoting maintenance mode, so the mapping is
    decided by observation and never by spelling.
  * §D-L9 / U2 — whether an extra or unassigned address is distinguishable from the free
    primary address every Linode has.
  * U11 — whether `/volumes/types .price.monthly` is per-GB or per-volume, by comparing the
    live rate against the account's own invoice line for a volume of known size.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fetch_linode  # noqa: E402 - needs the sys.path line above

#: Every read the sweep makes, as (fixture stem, path). Per-parent endpoints
#: (`/nodebalancers/{id}/configs`) are expanded at run time from what the list returned.
ENDPOINTS = (
    ("linode_account", "/account"),
    ("linode_invoices", "/account/invoices"),
    ("linode_instances", "/linode/instances"),
    ("linode_volumes", "/volumes"),
    ("linode_ips", "/networking/ips"),
    ("linode_nodebalancers", "/nodebalancers"),
    ("linode_images", "/images"),
    ("linode_types_linode", "/linode/types"),
    ("linode_types_volumes", "/volumes/types"),
    ("linode_types_nodebalancers", "/nodebalancers/types"),
)

#: Keys whose entire value is account-identifying and is replaced wholesale.
SCRUB_KEYS = {
    "euuid": "aaaaaaaa-0000-1111-2222-333333333333",
    "email": "cloudcost@example.invalid",
    "first_name": "Cloudcost",
    "last_name": "Placeholder",
    "company": "Example Org",
    "address_1": "1 Example Street",
    "address_2": "",
    "city": "Exampleville",
    "state": "EX",
    "zip": "00000",
    "phone": "+10000000000",
    "tax_id": "",
    "rdns": "rdns-placeholder.invalid",
    "hostname": "hostname-placeholder.invalid",
    "instance_uri": "https://api.example.invalid/placeholder",
    "host_uuid": "host-uuid-placeholder",
}

#: A Linode PAT is 64 hex characters. Any string of that shape is replaced wherever it
#: appears, whatever key carries it — a credential must never survive into a fixture even if
#: the API starts returning one under a name this table does not know.
TOKEN_SHAPED = re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)

#: Both patterns deliberately over-match — a scrub must never let a real address through —
#: and every candidate they find is then *validated* by `ipaddress` before being replaced.
#: The validation is not a nicety: the bare regex matched the `04:20:01` inside an ISO
#: timestamp and rewrote `2026-08-01T04:20:01` to `2026-08-01T042001:db8::86`, corrupting
#: every `created`/`updated`/`date` field in the recording. Over-matching plus a real parser
#: is the combination that is both safe and correct; the regex alone is neither.
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6 = re.compile(r"\b(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?:/\d{1,3})?\b", re.IGNORECASE)


def _is_address(candidate: str, version: int) -> bool:
    """True iff `candidate` really is an IP address of the given version."""
    text = candidate.split("/", 1)[0]
    try:
        return ipaddress.ip_address(text).version == version
    except ValueError:
        return False


class Scrubber:
    """Stable, first-seen-order placeholder assignment.

    Addresses go to the documentation ranges reserved for exactly this purpose — TEST-NET-1
    (192.0.2.0/24, RFC 5737) and 2001:db8::/32 (RFC 3849) — so a fixture can never contain a
    routable address, and the scrub is verifiable by range rather than by eye.
    """

    def __init__(self) -> None:
        self._ipv4: dict = {}
        self._ipv6: dict = {}

    def ipv4(self, match) -> str:
        address = match.group(0)
        if not _is_address(address, 4):
            return address
        # Leave netmask-shaped and wildcard values alone: a subnet mask is not an identifier,
        # and rewriting it would corrupt the shape the adapter reads.
        if address.startswith("255.") or address == "0.0.0.0":
            return address
        if address not in self._ipv4:
            self._ipv4[address] = f"192.0.2.{len(self._ipv4) + 1}"
        return self._ipv4[address]

    def ipv6(self, match) -> str:
        address = match.group(0)
        if not _is_address(address, 6):
            return address
        if address not in self._ipv6:
            suffix = format(len(self._ipv6) + 1, "x")
            keep_prefix = "/" + address.split("/", 1)[1] if "/" in address else ""
            self._ipv6[address] = f"2001:db8::{suffix}{keep_prefix}"
        return self._ipv6[address]

    def text(self, value: str) -> str:
        value = TOKEN_SHAPED.sub("TOKEN-SHAPED-VALUE-REDACTED", value)
        value = IPV6.sub(self.ipv6, value)
        value = IPV4.sub(self.ipv4, value)
        return value

    def walk(self, node):
        if isinstance(node, dict):
            out = {}
            for key, value in node.items():
                if key in SCRUB_KEYS and not isinstance(value, (dict, list)):
                    out[key] = SCRUB_KEYS[key]
                elif key == "credit_card" and isinstance(value, dict):
                    out[key] = {"last_four": "0000", "expiry": "01/2030"}
                else:
                    out[key] = self.walk(value)
            return out
        if isinstance(node, list):
            return [self.walk(item) for item in node]
        if isinstance(node, str):
            return self.text(node)
        return node


def record_pages(client, path: str, scrubber: Scrubber) -> list:
    """Capture every page envelope of a list endpoint, scrubbed.

    The envelope is kept whole (`{data, page, pages, results}`) rather than flattened: the
    offline stub replays these pages verbatim, so pagination is exercised against the shape
    the provider actually returns.
    """
    pages = []
    page = 1
    while page <= fetch_linode.MAX_PAGES:
        body = client.get(
            path, params={"page": page, "page_size": fetch_linode.PAGE_SIZE}
        )
        pages.append(scrubber.walk(body))
        total = body.get("pages")
        if not isinstance(total, int) or page >= total:
            break
        page += 1
    return pages


def findings(recorded: dict) -> dict:
    """The evidence for the three questions t1 settles from live reads.

    Reported as data, not as a conclusion: this function states what was observed and never
    picks the state mapping. That choice belongs in the adapter, made by a human reading these
    numbers — the whole point of §D-L4 is that the two candidates are indistinguishable by
    inspection.
    """
    instances = [row for page in recorded.get("linode_instances", []) for row in page["data"]]
    ips = [row for page in recorded.get("linode_ips", []) for row in page["data"]]
    volumes = [row for page in recorded.get("linode_volumes", []) for row in page["data"]]
    volume_types = [
        row for page in recorded.get("linode_types_volumes", []) for row in page["data"]
    ]
    items = [row for page in recorded.get("linode_invoice_items", []) for row in page["data"]]

    statuses: dict = {}
    for row in instances:
        statuses[row.get("status")] = statuses.get(row.get("status"), 0) + 1

    return {
        "D-L4 (U1) — instance status": {
            "instance_count": len(instances),
            "status_counts": statuses,
            "powered_off_candidates_present": sorted(
                value for value in statuses if value in ("offline", "stopped")
            ),
            "note": (
                "The enum holds fourteen values and two terminal powered-off spellings. "
                "`stopped` collides literally with the canonical STATE_STOPPED while the spec "
                "documents it as what maintenance mode produces. If neither appears here, the "
                "mapping is NOT settled and must not be written."
            ),
        },
        "D-L9 (U2) — static IP reachability": {
            "address_count": len(ips),
            "fields_present": sorted({key for row in ips for key in row}),
            "unassigned_count": sum(1 for row in ips if row.get("linode_id") is None),
            "by_type": _count(ips, "type"),
            "public_true": sum(1 for row in ips if row.get("public") is True),
            "note": (
                "No response schema carries a `reserved` flag and an IP has no `created` "
                "timestamp. If every address here is attached to a Linode, an extra/reserved "
                "address is not distinguishable from the free primary one, and "
                "rule_unassociated_static_ip is recorded as not-reachable-on-Linode rather "
                "than approximated."
            ),
        },
        "U11 — volume price unit": {
            "volume_types": [
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "price": row.get("price"),
                    "region_prices_count": len(row.get("region_prices") or []),
                }
                for row in volume_types
            ],
            "volumes": [
                {"id": row.get("id"), "size_gb": row.get("size"), "region": row.get("region")}
                for row in volumes
            ],
            "invoice_items_mentioning_volume": [
                {
                    "label": row.get("label"),
                    "quantity": row.get("quantity"),
                    "unit_price": row.get("unit_price"),
                    "amount": row.get("amount"),
                    "region": row.get("region"),
                }
                for row in items
                if "volume" in (row.get("label") or "").lower()
            ],
            "note": (
                "Per-GB iff a known volume's invoice unit_price equals the live hourly rate "
                "times its size in GB. If the account has no volume line, the unit stays "
                "unsettled and a volume is emitted with 0.0 plus a named warning."
            ),
        },
    }


def _count(rows: list, key: str) -> dict:
    out: dict = {}
    for row in rows:
        out[row.get(key)] = out.get(row.get(key), 0) + 1
    return out


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Record Linode fixtures from a live account")
    parser.add_argument("--out", default="/tmp/recorded-linode")
    parser.add_argument("--api-base", default=fetch_linode.DEFAULT_API_BASE)
    parser.add_argument(
        "--period",
        default=None,
        help="YYYY-MM whose invoice items to record (default: the newest settled invoice)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scrubber = Scrubber()

    fetch_linode.warn_shadowing_env()
    client = fetch_linode.LinodeClient(token=fetch_linode.load_token(), api_base=args.api_base)

    recorded: dict = {}
    errors: list = []
    for stem, path in ENDPOINTS:
        try:
            recorded[stem] = record_pages(client, path, scrubber)
        except (fetch_linode.LinodeAuthError, fetch_linode.LinodeAPIError) as exc:
            errors.append({"source": path, "error": str(exc)})

    # Per-parent endpoints, expanded from what the list returned.
    for page in recorded.get("linode_nodebalancers", []):
        for row in page["data"]:
            stem = f"linode_nodebalancer_{row['id']}_configs"
            try:
                recorded[stem] = record_pages(
                    client, f"/nodebalancers/{row['id']}/configs", scrubber
                )
            except (fetch_linode.LinodeAuthError, fetch_linode.LinodeAPIError) as exc:
                errors.append({"source": stem, "error": str(exc)})

    # Invoice items for the chosen period's invoice.
    invoices = [row for page in recorded.get("linode_invoices", []) for row in page["data"]]
    chosen = None
    if args.period:
        chosen = next(
            (row for row in invoices if str(row.get("date", "")).startswith(args.period)), None
        )
    elif invoices:
        chosen = sorted(invoices, key=lambda row: row.get("date") or "")[-1]
    if chosen is not None:
        try:
            recorded["linode_invoice_items"] = record_pages(
                client, f"/account/invoices/{chosen['id']}/items", scrubber
            )
        except (fetch_linode.LinodeAuthError, fetch_linode.LinodeAPIError) as exc:
            errors.append({"source": "invoice items", "error": str(exc)})

    written = []
    for stem, pages in recorded.items():
        if len(pages) == 1:
            (out / f"{stem}.json").write_text(json.dumps(pages[0], indent=2) + "\n")
            written.append(f"{stem}.json")
        else:
            for index, page in enumerate(pages, start=1):
                name = f"{stem}_page{index}.json"
                (out / name).write_text(json.dumps(page, indent=2) + "\n")
                written.append(name)

    report = {
        "out": str(out),
        "written": sorted(written),
        "invoice_recorded": (
            {"id": chosen.get("id"), "date": chosen.get("date"), "label": chosen.get("label")}
            if chosen
            else None
        ),
        "findings": findings(recorded),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
