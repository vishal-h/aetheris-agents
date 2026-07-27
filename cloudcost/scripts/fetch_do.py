#!/usr/bin/env python3
"""DigitalOcean read-only cost + inventory adapter (cloudcost m1, t1).

Fetches DO billing (balance, current-period invoice, billing history) and resource
inventory (droplets, volumes, reserved IPs, snapshots, load balancers) and emits the two
normalized JSON files defined in `cloudcost/milestone.md` §Normalized schemas:

    {output_dir}/do_costs_{YYYY-MM}.json
    {output_dir}/do_inventory_{YYYY-MM}.json

Read-only by construction: every call is a GET against a list/get endpoint. This script
never creates, modifies or deletes a DO resource.

Auth (D2 + §Prerequisites 1). The token is read from CLOUDCOST_DO_TOKEN and passed to the
HTTP client explicitly. DO_TOKEN / DIGITALOCEAN_ACCESS_TOKEN are never read: a stray write
token in the environment must not be able to shadow the intended read-only one. The token
is env-only — never an argument, never printed to stdout or stderr, never written to an
output file.

Usage:
    python3 scripts/fetch_do.py [--output-dir output] [--period YYYY-MM]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests

DEFAULT_API_BASE = "https://api.digitalocean.com/v2"

#: The only environment variable this adapter will authenticate with.
TOKEN_ENV = "CLOUDCOST_DO_TOKEN"

#: Variables that DO tooling (doctl, and any code using a default-pickup client) reads by
#: default. This adapter ignores them; their presence is warned about, never their value.
SHADOWING_ENV = ("DO_TOKEN", "DIGITALOCEAN_ACCESS_TOKEN")

#: DO bills in USD; the billing API carries no currency field.
CURRENCY = "USD"

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_PAGES = 100
PER_PAGE = 200

# Monthly list-price rates used to derive `monthly_cost_estimate` from size/type (D4:
# resource-level dollars are *estimates*; actuals stay service-level on the cost side).
# Droplets are exempt — the API returns their real `size.price_monthly`.
VOLUME_GIB_MONTHLY = 0.10  # confirmed against a real invoice line: 1 GiB volume, 624h, $0.09
SNAPSHOT_GIB_MONTHLY = 0.06
RESERVED_IP_UNASSIGNED_MONTHLY = 4.38  # $0.006/hr; assigned reserved IPs are free
LOAD_BALANCER_NODE_MONTHLY = {"lb-small": 12.00, "lb-medium": 24.00, "lb-large": 48.00}


class DOAuthError(RuntimeError):
    """Authentication/authorisation failure. Never carries the token."""


class DOAPIError(RuntimeError):
    """Non-auth API failure after retries are exhausted."""


# --------------------------------------------------------------------------- client


class DOClient:
    """Minimal read-only DO REST client: explicit auth, pagination, retry, rate limits."""

    def __init__(
        self,
        token: str,
        api_base: str = DEFAULT_API_BASE,
        timeout: int = 30,
        max_retries: int = 4,
        retry_base_delay: float = 1.0,
    ) -> None:
        if not token:
            raise DOAuthError(f"{TOKEN_ENV} is empty")
        # Held only to redact it out of error text; never logged, never returned.
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.session = requests.Session()
        # Explicit credential. No default DO_TOKEN/DIGITALOCEAN_ACCESS_TOKEN pickup.
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "aetheris-cloudcost/1.0 (read-only)",
            }
        )

    def _redact(self, text: str) -> str:
        """Belt-and-braces: strip the token from any text that may reach an error path."""
        return text.replace(self._token, "***") if self._token else text

    def __repr__(self) -> str:  # pragma: no cover - defensive, keeps token out of reprs
        return f"<DOClient api_base={self.api_base!r}>"

    def _retry_delay(self, attempt: int, response: requests.Response | None) -> float:
        if response is not None:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except ValueError:
                    pass
            reset = response.headers.get("ratelimit-reset")
            if reset:
                try:
                    return max(0.0, min(float(reset) - time.time(), 60.0))
                except ValueError:
                    pass
        return self.retry_base_delay * (2**attempt)

    def _same_origin(self, url: str) -> str:
        """Re-root an absolute DO pagination link onto the configured api_base origin.

        DO returns fully-qualified `links.pages.next` URLs. Keeping the path but forcing
        our own scheme/host means pagination can never be walked off to another host, and
        lets the offline test suite replay recorded pages against a local stub.
        """
        base = urlsplit(self.api_base)
        nxt = urlsplit(url)
        return urlunsplit((base.scheme, base.netloc, nxt.path, nxt.query, ""))

    def get(self, path: str, params: dict | None = None) -> dict:
        """GET a single DO endpoint, with retry on 429/5xx and transport errors."""
        url = path if path.startswith("http") else f"{self.api_base}{path}"
        attempt = 0
        while True:
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise DOAPIError(
                        f"GET {path} failed after {attempt + 1} attempts: "
                        f"{type(exc).__name__}"
                    ) from None
                time.sleep(self._retry_delay(attempt, None))
                attempt += 1
                continue

            if response.status_code in (401, 403):
                raise DOAuthError(
                    f"DigitalOcean rejected the credential (HTTP {response.status_code}) "
                    f"on GET {path}. Check that {TOKEN_ENV} holds a valid read-only PAT."
                )
            if response.status_code in RETRY_STATUSES and attempt < self.max_retries:
                time.sleep(self._retry_delay(attempt, response))
                attempt += 1
                continue
            if not response.ok:
                body = self._redact(response.text)[:200]
                raise DOAPIError(f"GET {path} -> HTTP {response.status_code}: {body}")

            try:
                return response.json()
            except ValueError:
                raise DOAPIError(f"GET {path} -> non-JSON response body") from None

    def paginate(self, path: str, key: str, params: dict | None = None) -> list:
        """Collect every page of a list endpoint by following `links.pages.next`."""
        params = dict(params or {})
        params.setdefault("per_page", PER_PAGE)
        items: list = []
        url = path
        for _ in range(MAX_PAGES):
            body = self.get(url, params=params)
            items.extend(body.get(key) or [])
            nxt = ((body.get("links") or {}).get("pages") or {}).get("next")
            if not nxt:
                return items
            url = self._same_origin(nxt)
            params = None  # the next link already carries page/per_page
        raise DOAPIError(f"pagination for {path} exceeded {MAX_PAGES} pages")


# ----------------------------------------------------------------------------- helpers


def load_token(env: dict | None = None) -> str:
    """Read the read-only token from CLOUDCOST_DO_TOKEN and nowhere else."""
    env = os.environ if env is None else env
    token = (env.get(TOKEN_ENV) or "").strip()
    if not token:
        raise DOAuthError(
            f"{TOKEN_ENV} is not set. cloudcost authenticates with {TOKEN_ENV} only and "
            f"never falls back to {' / '.join(SHADOWING_ENV)} — export the read-only PAT "
            f"as {TOKEN_ENV} before running."
        )
    return token


def warn_shadowing_env(env: dict | None = None, stream=None) -> list:
    """Name (never print the value of) any stray DO token that is being ignored."""
    env = os.environ if env is None else env
    # Resolved at call time, not import time, so redirected stderr is honoured.
    stream = sys.stderr if stream is None else stream
    present = [name for name in SHADOWING_ENV if (env.get(name) or "").strip()]
    for name in present:
        print(
            f"warning: {name} is set in this environment and is IGNORED; cloudcost "
            f"authenticates with {TOKEN_ENV} only.",
            file=stream,
        )
    return present


def money(value) -> float:
    """DO returns amounts as strings; normalise to a 2dp float."""
    if value is None or value == "":
        return 0.0
    return round(float(value), 2)


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tags_of(raw: dict) -> list:
    """DO is inconsistent: droplets/volumes use `tags`, load balancers use `tag`."""
    tags = raw.get("tags")
    if isinstance(tags, list):
        return tags
    single = raw.get("tag")
    return [single] if single else []


# ------------------------------------------------------------------------ normalizers


def normalize_cost(summary: dict, invoice: dict, account: str, period: str) -> dict:
    """Build the cost snapshot from an invoice summary's service-level product charges.

    D4: DO bills at service granularity, so every line carries `resource_id: null` and
    `region`/`usage_qty`/`usage_unit` stay null — the adapter never fabricates
    resource-level cost attribution DO's API does not give.
    """
    charges = (summary.get("product_charges") or {}).get("items") or []
    by_service: dict = {}
    for item in charges:
        service = item.get("name") or "Unknown"
        by_service.setdefault(service, 0.0)
        by_service[service] += money(item.get("amount"))

    line_items = [
        {
            "service": service,
            "resource_id": None,
            "region": None,
            "amount": round(amount, 2),
            "usage_qty": None,
            "usage_unit": None,
            "tags": [],
        }
        for service, amount in sorted(by_service.items(), key=lambda kv: -kv[1])
    ]

    return {
        "provider": "digitalocean",
        "account": account,
        "period": period,
        "currency": CURRENCY,
        "source_granularity": "service",
        "line_items": line_items,
        "totals": {"amount": money(summary.get("amount"))},
        # Additive beyond the schema example — see docs/t1-implementation-notes.md.
        "invoice": {
            "invoice_uuid": invoice.get("invoice_uuid"),
            "invoice_id": invoice.get("invoice_id"),
            "status": invoice.get("status", "preview"),
        },
        "generated_at": iso_now(),
    }


def normalize_droplet(raw: dict) -> dict:
    size = raw.get("size") or {}
    return {
        "resource_id": str(raw.get("id")),
        "type": "droplet",
        "name": raw.get("name"),
        "region": (raw.get("region") or {}).get("slug"),
        "size": raw.get("size_slug"),
        "state": raw.get("status"),
        "created_at": raw.get("created_at"),
        "last_activity_at": None,
        "attached_to": None,
        "monthly_cost_estimate": money(size.get("price_monthly")),
        "tags": tags_of(raw),
        "raw_ref": f"do://droplets/{raw.get('id')}",
    }


def normalize_volume(raw: dict) -> dict:
    droplet_ids = raw.get("droplet_ids") or []
    gib = raw.get("size_gigabytes") or 0
    return {
        "resource_id": str(raw.get("id")),
        "type": "volume",
        "name": raw.get("name"),
        "region": (raw.get("region") or {}).get("slug"),
        "size": f"{gib}GiB",
        # The volumes endpoint carries no status field; attachment is the only state DO
        # exposes, so it is derived rather than read.
        "state": "attached" if droplet_ids else "available",
        "created_at": raw.get("created_at"),
        "last_activity_at": None,
        "attached_to": str(droplet_ids[0]) if droplet_ids else None,
        "monthly_cost_estimate": round(gib * VOLUME_GIB_MONTHLY, 2),
        "tags": tags_of(raw),
        "raw_ref": f"do://volumes/{raw.get('id')}",
    }


def normalize_reserved_ip(raw: dict) -> dict:
    droplet = raw.get("droplet") or None
    attached_to = str(droplet.get("id")) if isinstance(droplet, dict) else None
    return {
        "resource_id": str(raw.get("ip")),
        "type": "reserved_ip",
        "name": raw.get("ip"),
        "region": (raw.get("region") or {}).get("slug"),
        "size": None,
        "state": "assigned" if attached_to else "unassigned",
        "created_at": raw.get("created_at"),
        "last_activity_at": None,
        "attached_to": attached_to,
        # DO charges for a reserved IP only while it is NOT assigned.
        "monthly_cost_estimate": 0.0 if attached_to else RESERVED_IP_UNASSIGNED_MONTHLY,
        "tags": tags_of(raw),
        "raw_ref": f"do://reserved_ips/{raw.get('ip')}",
    }


def normalize_snapshot(raw: dict) -> dict:
    gib = raw.get("size_gigabytes") or 0
    source = raw.get("resource_id")
    regions = raw.get("regions") or []
    return {
        "resource_id": str(raw.get("id")),
        "type": "snapshot",
        "name": raw.get("name"),
        "region": regions[0] if regions else None,
        "size": f"{gib}GiB",
        "state": "available",
        "created_at": raw.get("created_at"),
        "last_activity_at": None,
        # A snapshot is "associated" with the resource it was taken from; a snapshot whose
        # source is gone is the aged-orphan signal t2 keys on.
        "attached_to": str(source) if source else None,
        "monthly_cost_estimate": round(gib * SNAPSHOT_GIB_MONTHLY, 2),
        "tags": tags_of(raw),
        "raw_ref": f"do://snapshots/{raw.get('id')}",
    }


def normalize_load_balancer(raw: dict) -> dict:
    droplet_ids = raw.get("droplet_ids") or []
    size_slug = raw.get("size") or "lb-small"
    nodes = raw.get("size_unit") or 1
    rate = LOAD_BALANCER_NODE_MONTHLY.get(size_slug, LOAD_BALANCER_NODE_MONTHLY["lb-small"])
    return {
        "resource_id": str(raw.get("id")),
        "type": "load_balancer",
        "name": raw.get("name"),
        "region": (raw.get("region") or {}).get("slug"),
        "size": size_slug,
        "state": raw.get("status"),
        "created_at": raw.get("created_at"),
        "last_activity_at": None,
        "attached_to": str(droplet_ids[0]) if droplet_ids else None,
        "monthly_cost_estimate": round(nodes * rate, 2),
        "tags": tags_of(raw),
        "raw_ref": f"do://load_balancers/{raw.get('id')}",
    }


#: endpoint path -> (response key, normalizer)
INVENTORY_SOURCES = (
    ("/droplets", "droplets", normalize_droplet),
    ("/volumes", "volumes", normalize_volume),
    ("/reserved_ips", "reserved_ips", normalize_reserved_ip),
    ("/snapshots", "snapshots", normalize_snapshot),
    ("/load_balancers", "load_balancers", normalize_load_balancer),
)


# -------------------------------------------------------------------------- fetchers


def fetch_account(client: DOClient) -> str:
    """Account identifier for the snapshot header. The uuid, not the email."""
    return ((client.get("/account") or {}).get("account") or {}).get("uuid") or "unknown"


def select_invoice(client: DOClient, period: str) -> dict:
    """Find the invoice for `period` — the live preview for the current month, else a
    settled invoice from the list."""
    body = client.get("/customers/my/invoices", params={"per_page": PER_PAGE})
    preview = body.get("invoice_preview") or {}
    if preview.get("invoice_period") == period:
        return {**preview, "status": "preview"}
    for invoice in body.get("invoices") or []:
        if invoice.get("invoice_period") == period:
            return invoice
    raise DOAPIError(f"no DigitalOcean invoice found for period {period}")


def fetch_costs(client: DOClient, account: str, period: str) -> dict:
    invoice = select_invoice(client, period)
    uuid = invoice.get("invoice_uuid")
    summary = client.get(f"/customers/my/invoices/{uuid}/summary")
    snapshot = normalize_cost(summary, invoice, account, period)

    balance = client.get("/customers/my/balance") or {}
    snapshot["balance"] = {
        "month_to_date_balance": money(balance.get("month_to_date_balance")),
        "account_balance": money(balance.get("account_balance")),
        "month_to_date_usage": money(balance.get("month_to_date_usage")),
        "generated_at": balance.get("generated_at"),
    }

    history = client.paginate("/customers/my/billing_history", "billing_history")
    snapshot["billing_history"] = [
        {
            "date": entry.get("date"),
            "type": entry.get("type"),
            "description": entry.get("description"),
            "amount": money(entry.get("amount")),
            "invoice_uuid": entry.get("invoice_uuid"),
        }
        for entry in history
    ]
    return snapshot


def fetch_inventory(client: DOClient, account: str, period: str) -> tuple:
    """Fetch every inventory source. A failing source degrades to an error entry rather
    than aborting the sweep."""
    resources: list = []
    errors: list = []
    for path, key, normalize in INVENTORY_SOURCES:
        try:
            for raw in client.paginate(path, key):
                resources.append(normalize(raw))
        except DOAuthError:
            raise
        except (DOAPIError, requests.RequestException) as exc:
            errors.append({"source": path, "error": str(exc)})
    inventory = {
        "provider": "digitalocean",
        "account": account,
        "period": period,
        "resources": resources,
        "generated_at": iso_now(),
    }
    return inventory, errors


# ------------------------------------------------------------------------------- main


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="DigitalOcean read-only cost/inventory adapter")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--period", default=None, help="YYYY-MM (default: current UTC month)")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--retry-base-delay", type=float, default=1.0)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    period = args.period or current_period()
    output_dir = Path(args.output_dir)
    errors: list = []

    try:
        warn_shadowing_env()
        client = DOClient(
            token=load_token(),
            api_base=args.api_base,
            timeout=args.timeout,
            max_retries=args.max_retries,
            retry_base_delay=args.retry_base_delay,
        )
        account = fetch_account(client)
    except DOAuthError as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1
    except DOAPIError as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    costs = None
    try:
        costs = fetch_costs(client, account, period)
    except DOAuthError as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1
    except (DOAPIError, requests.RequestException) as exc:
        errors.append({"source": "billing", "error": str(exc)})

    try:
        inventory, inventory_errors = fetch_inventory(client, account, period)
        errors.extend(inventory_errors)
    except DOAuthError as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    written = {}
    if costs is not None:
        written["costs"] = str(write_json(output_dir / f"do_costs_{period}.json", costs))
    written["inventory"] = str(write_json(output_dir / f"do_inventory_{period}.json", inventory))

    summary = {
        "status": "ok" if not errors else "partial",
        "period": period,
        "files": written,
        "counts": {
            "line_items": len(costs["line_items"]) if costs else 0,
            "resources": len(inventory["resources"]),
        },
        "totals": costs["totals"] if costs else None,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
