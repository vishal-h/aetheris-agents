#!/usr/bin/env python3
"""Linode read-only cost + inventory adapter (cloudcost m3, t1).

Fetches Linode billing (account, period invoice, invoice items) and resource inventory
(volumes, NodeBalancers, images, and — conditionally — IP addresses) and emits the two
normalized JSON files defined in `cloudcost/milestone.md` §Normalized schemas:

    {output_dir}/linode_costs_{YYYY-MM}.json
    {output_dir}/linode_inventory_{YYYY-MM}.json

Read-only by construction: every call is a GET against a list/get endpoint. This script
never creates, modifies or deletes a Linode resource.

Auth (m1 D2, m3 §Prerequisites 1). The token is read from CLOUDCOST_LINODE_TOKEN and passed
to the HTTP client explicitly. LINODE_CLI_TOKEN / LINODE_TOKEN are never read: a stray write
token in the environment must not be able to shadow the intended read-only one. The token is
env-only — never an argument, never printed to stdout or stderr, never written to an output
file.

Two things distinguish this adapter's credential posture from its predecessors'.

  * The honest shadow list is *shorter*. `linode_api4` (the Python SDK) reads no environment
    variable at all — the token is a required positional constructor argument — so there is
    no default-pickup arm of the `doctl` / botocore kind. `LINODE_CLI_TOKEN` is the only
    variable any Linode tooling reads as a credential (linode-cli
    `linodecli/configuration/config.py:28`); `LINODE_TOKEN` is warned about on convention
    grounds alone, being a widespread spelling that no library honours.
  * There is a hazard class neither predecessor has: LINODE_CLI_API_HOST / _VERSION /
    _SCHEME redirect *where a credential is sent* rather than which credential is used. This
    adapter constructs its own base URL and warns if any of them is set.

Usage:
    python3 scripts/fetch_linode.py [--output-dir output] [--period YYYY-MM]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from _normalized import (
    STATE_STOPPED,
    TYPE_COMPUTE_INSTANCE,
    TYPE_LOAD_BALANCER,
    TYPE_SNAPSHOT,
    TYPE_STATIC_IP,
    TYPE_VOLUME,
    money,
)

DEFAULT_API_BASE = "https://api.linode.com/v4"

#: The only environment variable this adapter will authenticate with.
TOKEN_ENV = "CLOUDCOST_LINODE_TOKEN"

#: Credential variables Linode tooling reads by default. This adapter ignores them; their
#: presence is warned about, never their value. `LINODE_CLI_TOKEN` is read by linode-cli
#: (`linodecli/configuration/config.py:28`); `LINODE_TOKEN` is read by no library at all and
#: is warned about because it is the conventional spelling users export.
SHADOWING_ENV = ("LINODE_CLI_TOKEN", "LINODE_TOKEN")

#: Endpoint-shaping variables read by linode-cli (`linodecli/helpers.py:12-19`). They are a
#: different hazard from a shadowing credential: they redirect *where a credential is sent*.
#: This adapter never reads them as configuration — it warns and uses its own base URL.
ENDPOINT_REDIRECT_ENV = (
    "LINODE_CLI_API_HOST",
    "LINODE_CLI_API_VERSION",
    "LINODE_CLI_API_SCHEME",
)

#: Provenance for every adapter-asserted constant below (m3 §D-L2). The scout swept this
#: exact artifact twice — structurally over every `properties` object and textually over the
#: raw 7.9 MB file — and found no currency field anywhere, billing surface included; `US
#: Dollars` appears 100 times and only in `description` strings.
SPEC_VERSION = "4.215.0"
SPEC_ETAG = "290888161afda3d3566f755d664856fb937fbafbf817838587bb2be6e77ef6cd"

#: Linode bills in USD; the API carries no currency field (see SPEC_ETAG above). Asserted
#: with its basis, which is the third instance of a posture both predecessors already take
#: (`fetch_do.py:55-56`, `fetch_aws.py:70-71`), not a new concession.
CURRENCY = "USD"

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_PAGES = 100
#: `components.parameters.page-size`: default 100, minimum 25, maximum 500.
PAGE_SIZE = 500

#: The Linode instance status that means "the operator powered this off" — m3 §D-L4, the
#: milestone's sharpest seam, and settled by observation rather than by the spec.
#:
#: The `status` enum holds fourteen values and **two** terminal powered-off spellings,
#: `offline` and `stopped`. `stopped` collides literally with the canonical `STATE_STOPPED`
#: while the spec documents it as what *maintenance mode* produces, so a pass-through would
#: fire `rule_stopped_compute_with_attached_storage` for the maintenance case and never for
#: the ordinary powered-off one — a well-formed wrong answer with no error anywhere.
#:
#: EVIDENCE (recorded fixture `linode_instances.json`, live read 2026-08-05): the account
#: holds 11 instances; the one deliberately powered off — id 19294655, tagged `test server` —
#: reports `"status": "offline"`. No instance reports `stopped`. So `offline` is the customer
#: powered-off state and is the value mapped onto the canonical one. `stopped` and
#: `billing_suspension` pass through verbatim: both are terminal, but neither means "the
#: operator turned this off and forgot it".
POWERED_OFF_STATUS = "offline"

#: The synthetic cost line carrying `invoice.tax` (m3 §D-L1). Linode states subtotal, tax and
#: total as three separate fields with explicit before/after-tax descriptions, so the tax
#: figure is the provider's own — not a derived or apportioned number.
TAX_SERVICE = "Tax"

#: Resource classes deliberately not inventoried, each with the reason (m3 done-when 8:
#: an excluded class is recorded as an exclusion, never left as an absence — *absent is
#: unknown, not zero*). Emitted in the run summary.
EXCLUSIONS = (
    {
        "class": "managed_database",
        "endpoint": "/databases/instances",
        "reason": (
            "m3 §D-L7: no attachment field (rule_stopped_database_with_storage requires "
            "attached_to is None), no price object on /databases/types so "
            "monthly_cost_estimate > 0 can never be satisfied honestly, no tags field (which "
            "would drag tag_coverage down by a schema gap rather than by account practice), "
            "and the spec contradicts itself on whether databases:read_only exists at all"
        ),
    },
    {
        "class": "backup",
        "endpoint": "/linode/instances/{id}/backups",
        "reason": (
            "m3 §D-L11: an N+1 call gated on backups.enabled, carrying no tags and no region, "
            "whose rows exist only while the parent Linode does — so the aged-orphan semantics "
            "(a snapshot whose source is gone) is structurally unavailable"
        ),
    },
    {
        "class": "object_storage",
        "endpoint": "/object-storage/*",
        "reason": "m3 §NOT in scope — never scouted",
    },
    {
        "class": "lke",
        "endpoint": "/lke/*",
        "reason": "m3 §NOT in scope — never scouted",
    },
    {
        "class": "firewall",
        "endpoint": "/networking/firewalls*",
        "reason": "m3 §NOT in scope — never scouted",
    },
    {
        "class": "vpc",
        "endpoint": "/vpcs*",
        "reason": "m3 §NOT in scope — never scouted",
    },
)


class LinodeAuthError(RuntimeError):
    """Authentication/authorisation failure. Never carries the token."""


class LinodeAPIError(RuntimeError):
    """Non-auth API failure after retries are exhausted."""


# --------------------------------------------------------------------------- client


class LinodeClient:
    """Minimal read-only Linode APIv4 client: explicit auth, pagination, retry.

    Pagination is page-number with a total (`{data, page, pages, results}`,
    `components.schemas.pagination-envelope`), not DO's follow-the-URL scheme — so this
    client increments an integer and `fetch_do.py`'s `_same_origin` re-rooting guard has no
    analogue here and is deliberately not copied.
    """

    def __init__(
        self,
        token: str,
        api_base: str = DEFAULT_API_BASE,
        timeout: int = 30,
        max_retries: int = 4,
        retry_base_delay: float = 1.0,
    ) -> None:
        if not token:
            raise LinodeAuthError(f"{TOKEN_ENV} is empty")
        # Held only to redact it out of error text; never logged, never returned.
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.session = requests.Session()
        # Explicit credential. No default LINODE_CLI_TOKEN/LINODE_TOKEN pickup.
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
        return f"<LinodeClient api_base={self.api_base!r}>"

    def _retry_delay(self, attempt: int, response) -> float:
        if response is not None:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except ValueError:
                    pass
        return self.retry_base_delay * (2**attempt)

    def get(self, path: str, params: dict | None = None) -> dict:
        """GET a single Linode endpoint, with retry on 429/5xx and transport errors."""
        url = f"{self.api_base}{path}"
        attempt = 0
        while True:
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise LinodeAPIError(
                        f"GET {path} failed after {attempt + 1} attempts: "
                        f"{type(exc).__name__}"
                    ) from None
                time.sleep(self._retry_delay(attempt, None))
                attempt += 1
                continue

            if response.status_code in (401, 403):
                # The spec declares only `200` and `default` on every in-scope operation and
                # defers status codes to an external page (scout §B9a), so this is the
                # observed-behaviour arm, not a documented one. It is fatal either way: a
                # rejected credential must never read as an empty account.
                raise LinodeAuthError(
                    f"Linode rejected the credential (HTTP {response.status_code}) on "
                    f"GET {path}. Check that {TOKEN_ENV} holds a valid read-only PAT with "
                    f"the scope this endpoint needs."
                )
            if response.status_code in RETRY_STATUSES and attempt < self.max_retries:
                time.sleep(self._retry_delay(attempt, response))
                attempt += 1
                continue
            if not response.ok:
                body = self._redact(response.text)[:200]
                raise LinodeAPIError(f"GET {path} -> HTTP {response.status_code}: {body}")

            try:
                return response.json()
            except ValueError:
                raise LinodeAPIError(f"GET {path} -> non-JSON response body") from None

    def paginate(self, path: str, params: dict | None = None) -> list:
        """Collect every page of a list endpoint by incrementing `page` up to `pages`."""
        items: list = []
        page = 1
        for _ in range(MAX_PAGES):
            query = dict(params or {})
            query.update({"page": page, "page_size": PAGE_SIZE})
            body = self.get(path, params=query)
            items.extend(body.get("data") or [])
            pages = body.get("pages")
            if not isinstance(pages, int) or page >= pages:
                return items
            page += 1
        raise LinodeAPIError(f"pagination for {path} exceeded {MAX_PAGES} pages")


# ----------------------------------------------------------------------------- helpers
#
# `current_period`, `iso_now`, `write_json` and `warn_shadowing_env` are duplicated from
# the sibling adapters rather than imported: a CLI-to-CLI import is the anti-pattern named
# at `_normalized.py:35-37`, and these already exist twice on purpose (`fetch_do.py:213-240`,
# `fetch_aws.py:252-264`, `:399-404`). `money` is the exception — it is imported from
# `_normalized`, which is where the shared definition lives; the predecessors' private
# copies predate that module and disagree with each other (DO's raises, AWS's swallows).


def load_token(env: dict | None = None) -> str:
    """Read the read-only token from CLOUDCOST_LINODE_TOKEN and nowhere else."""
    env = os.environ if env is None else env
    token = (env.get(TOKEN_ENV) or "").strip()
    if not token:
        raise LinodeAuthError(
            f"{TOKEN_ENV} is not set. cloudcost authenticates with {TOKEN_ENV} only and "
            f"never falls back to {' / '.join(SHADOWING_ENV)} — export the read-only PAT "
            f"as {TOKEN_ENV} before running."
        )
    return token


def warn_shadowing_env(env: dict | None = None, stream=None) -> list:
    """Name (never print the value of) any stray Linode credential that is being ignored,
    and any endpoint-redirection variable that is set."""
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
    redirects = [name for name in ENDPOINT_REDIRECT_ENV if (env.get(name) or "").strip()]
    for name in redirects:
        print(
            f"warning: {name} is set in this environment and is IGNORED; it redirects "
            f"where a credential is sent, and cloudcost constructs its own Linode base URL.",
            file=stream,
        )
    return present + redirects


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tags_of(raw: dict) -> list:
    """Linode tags are a flat array of strings on every class that has them; classes that
    have none (IP addresses, backups, Managed Databases) carry no `tags` field at all."""
    tags = raw.get("tags")
    return [tag for tag in tags if isinstance(tag, str)] if isinstance(tags, list) else []


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
    return path


# ------------------------------------------------------------------------------ pricing


class Prices:
    """Live per-class monthly prices, read from the four `types` endpoints.

    Those endpoints declare `security: null` — they are unauthenticated, so the price sweep
    needs no scope and cannot be defeated by a narrow PAT. This is a genuine simplification
    over AWS, where `pricing:GetProducts` was excluded from the IAM policy and a
    hand-maintained table was written instead (`fetch_aws.py:114-128`): a Linode adapter reads
    the provider's own figures rather than transcribing a table that silently drifts.

    The spec's `monthly` values are `example` fields, not data, and the volume and
    NodeBalancer examples are the identical `0.1` — which is what a placeholder looks like.
    Nothing here is transcribed from the spec; every figure is a live read, and a class with
    no obtainable price yields no figure at all rather than a plausible neighbour.
    """

    def __init__(self) -> None:
        #: type id -> monthly, and (type id, region) -> monthly for region-specific prices.
        self.by_type: dict = {}
        self.by_type_region: dict = {}
        #: Where each figure came from, so a shipped estimate carries its basis.
        self.sources: dict = {}

    def load(self, client: LinodeClient, path: str, label: str, warnings: list) -> None:
        """Read one `types` endpoint. A failure warns and leaves the class unpriced — it
        never falls back to a figure from elsewhere."""
        try:
            rows = client.paginate(path)
        except (LinodeAPIError, requests.RequestException) as exc:
            warnings.append(
                f"{label}: price endpoint {path} unavailable ({type(exc).__name__}); "
                f"resources of this class are emitted with monthly_cost_estimate 0.0 and no "
                f"basis — the figure is unknown, not zero"
            )
            return
        for row in rows:
            type_id = row.get("id")
            if not type_id:
                continue
            monthly = (row.get("price") or {}).get("monthly")
            if monthly is not None:
                self.by_type[type_id] = money(monthly)
                self.sources[type_id] = f"{path} .price.monthly"
            for region_price in row.get("region_prices") or []:
                region = region_price.get("id")
                region_monthly = region_price.get("monthly")
                if region and region_monthly is not None:
                    self.by_type_region[(type_id, region)] = money(region_monthly)

    def monthly(self, type_id, region=None):
        """The monthly price for a type, region-specific where the provider states one.

        Returns None when no price was read — never a neighbouring region's rate. A rate
        borrowed from the next region is a fabrication wearing real provenance.
        """
        if type_id is None:
            return None
        if region is not None and (type_id, region) in self.by_type_region:
            return self.by_type_region[(type_id, region)]
        return self.by_type.get(type_id)

    def basis(self, type_id, region=None) -> str | None:
        if type_id is None:
            return None
        if region is not None and (type_id, region) in self.by_type_region:
            return f"{self.sources.get(type_id, 'types endpoint')} region_prices[{region}]"
        return self.sources.get(type_id)


# ------------------------------------------------------------------------ normalizers


#: A trailing `(12345)` on an invoice item label — the resource the line was for.
_LABEL_RESOURCE_SUFFIX = re.compile(r"\s*\(\d+\)\s*$")


def service_of(label) -> str:
    """The *service* an invoice item belongs to, from its human label.

    Linode labels its invoice items per resource — `"Linode 8GB - zz-ct-ravendb (19294655)"`,
    `"Storage Volume - pvc-0a8dce06b486430a (9022878) - 10 GiB"`,
    `"NodeBalancer - ccm-8cac00823f9b (1343674)"`. Grouping on the raw label would emit one
    `line_items[]` row per resource while every row carried `resource_id: null` — the shape of
    resource-level attribution without the attribution, which is worse than either honest
    alternative. So the service is the label's leading segment, and the resource-identifying
    remainder is **discarded**.

    Note what this deliberately does *not* do: it extracts no identifier. §D-L3 forbids
    parsing a resource id out of the label and using it as attribution, because an invoice
    item carries no machine-readable identifier at all (its ten properties are
    `{amount, from, label, quantity, region, tax, to, total, type, unit_price}`,
    `additionalProperties: false`). This function throws that text away and `resource_id`
    stays `None` unconditionally — the parse narrows the label towards the service, never
    towards the resource.
    """
    text = (label or "").strip()
    if not text:
        return "Unknown"
    # Only the first separator: `Storage Volume - <name> - 10 GiB` is one service, not three.
    head = text.split(" - ", 1)[0].strip()
    # `Outbound Data Processing Basic (1433944)` has no separator at all, so the trailing
    # resource id is stripped on its own — otherwise two lines of one service never group.
    return _LABEL_RESOURCE_SUFFIX.sub("", head).strip() or "Unknown"


def period_covered(items: list) -> dict:
    """The span the invoice's items actually bill, from their own `from`/`to` fields.

    Reported as observed, with `null` where no item states a bound — an absent range is
    unknown, never silently the invoice's own date.
    """
    starts = [item.get("from") for item in items if item.get("from")]
    ends = [item.get("to") for item in items if item.get("to")]
    return {"from": min(starts) if starts else None, "to": max(ends) if ends else None}


def normalize_cost(
    invoice: dict,
    items: list,
    account: str,
    period: str,
    balance: dict | None = None,
) -> dict:
    """Build the cost snapshot from an invoice's items, grouped to service granularity.

    m3 §D-L1 — `totals.amount` is `invoice.total`, which the spec describes as "the amount of
    the Invoice **after taxes**", and the tax is carried as its own `line_items[]` row taken
    from `invoice.tax`. That matches what AWS already ships (Cost Explorer returns `Tax` as
    one of its SERVICE groups, unfiltered) and makes the two providers' totals comparable.
    Σ`line_items[].amount` reconciles to `totals.amount`.

    m3 §D-L3 — an invoice item carries no machine-readable resource identifier: its complete
    property set is {amount, from, label, quantity, region, tax, to, total, type, unit_price},
    with `additionalProperties: false`. The only place a resource appears is inside the human
    `label` string, so the grouping key is that label and every line carries
    `resource_id: null`. Parsing an id out of the label would be fabricated attribution.

    m3 §D-L10 — `region` *is* populated here, from `invoice-item.region`. Nothing downstream
    reads it today, but §Normalized's rule is emit-with-a-real-value-or-null, never by
    omission, and Linode is the first provider that has the concept.
    """
    by_service: dict = {}
    for item in items:
        service = service_of(item.get("label"))
        entry = by_service.setdefault(service, {"amount": 0.0, "regions": set()})
        entry["amount"] += money(item.get("amount"))
        if item.get("region"):
            entry["regions"].add(item["region"])

    line_items = [
        {
            "service": service,
            "resource_id": None,
            # One region if every item under this service shares one; null if they differ or
            # none states one. The schema's rule is a real value or null, never a guess.
            "region": next(iter(entry["regions"])) if len(entry["regions"]) == 1 else None,
            "amount": money(entry["amount"]),
            "usage_qty": None,
            "usage_unit": None,
            "tags": [],
        }
        for service, entry in sorted(by_service.items(), key=lambda kv: -kv[1]["amount"])
    ]

    tax = money(invoice.get("tax"))
    if tax:
        line_items.append(
            {
                "service": TAX_SERVICE,
                "resource_id": None,
                "region": None,
                "amount": tax,
                "usage_qty": None,
                "usage_unit": None,
                "tags": [],
            }
        )

    return {
        "provider": "linode",
        "account": account,
        "period": period,
        "currency": CURRENCY,
        "source_granularity": "service",
        "line_items": line_items,
        "totals": {"amount": money(invoice.get("total"))},
        "balance": normalize_balance(balance),
        "generated_at": iso_now(),
        # Provider-specific payload. Everything above is the frozen cross-provider contract;
        # anything Linode-shaped that downstream scripts must not depend on generically lives
        # in here (§Normalized schemas).
        "provider_extra": {
            "invoice": {
                "invoice_id": invoice.get("id"),
                "label": invoice.get("label"),
                "date": invoice.get("date"),
                "billing_source": invoice.get("billing_source"),
                "subtotal": money(invoice.get("subtotal")),
                "tax": tax,
                "tax_summary": [
                    {"name": row.get("name"), "tax": money(row.get("tax"))}
                    for row in invoice.get("tax_summary") or []
                ],
                "total": money(invoice.get("total")),
                # The range the items actually cover, read off the items themselves. An
                # invoice issued in month M bills month M-1, so this is what stops `period`
                # being mistaken for the covered month (see `select_invoice`).
                "period_covered": period_covered(items),
            },
            "currency_basis": (
                f"adapter-asserted: Linode OpenAPI {SPEC_VERSION} (ETag {SPEC_ETAG}) declares "
                f"no currency field anywhere, billing surface included"
            ),
        },
    }


def normalize_balance(raw: dict | None) -> dict:
    """The account-level month-to-date position.

    `balance_uninvoiced` is the natural analogue of DO's `month_to_date_usage`, and the spec
    documents it as incomplete: "This is not your final invoice balance. Transfer charges are
    not included in the estimate." It is carried as the provider states it, not adjusted.

    Linode surfaces two figures where DO surfaces three, so `month_to_date_balance` and
    `month_to_date_usage` take the same value rather than a derived sum. That is the AWS
    precedent exactly (`fetch_aws.py:751-755` sets both from one figure and `account_balance`
    to None), not a new concession — and a synthesised third figure would be a number without
    a provider behind it.
    """
    raw = raw or {}
    return {
        "month_to_date_balance": money(raw.get("balance_uninvoiced")),
        "account_balance": money(raw.get("balance")),
        "month_to_date_usage": money(raw.get("balance_uninvoiced")),
        "generated_at": iso_now(),
    }


def normalize_instance(raw: dict, prices: Prices, warnings: list) -> dict:
    """A Linode instance is a `compute_instance` in the canonical vocabulary.

    **State (§D-L4).** `offline` — the observed customer powered-off value — maps onto the
    canonical `STATE_STOPPED`. Every other status passes through as the provider reports it,
    including `stopped` (maintenance mode) and `billing_suspension`: both are terminal, and
    neither is "the operator turned this off and forgot it". See `POWERED_OFF_STATUS` for the
    fixture that settled this.

    **Cost (§Seam 3).** Linode is DO-shaped, not AWS-shaped: it bills a service "even if it is
    powered off", so a stopped instance's own `monthly_cost_estimate` is non-zero and is *not*
    zeroed the way `fetch_aws.instance_compute_estimate` zeroes a stopped EC2 instance (D5).
    This is a live observation, not a reading of marketing copy: instance 19294655 reports
    `offline` and appears on invoice 32251471 at $48.00 for the covered month.
    `rule_stopped_compute_with_attached_storage` therefore sums a real own-cost plus attached
    volumes, and needs no change.

    `attached_to` is null: an instance is the attachment *target*, not the attached thing.
    """
    status = raw.get("status")
    type_id = raw.get("type")
    region = raw.get("region")
    rate = prices.monthly(type_id, region)
    if rate is None:
        note = (
            f"compute instance: no price read from /linode/types for type {type_id!r}; "
            f"monthly_cost_estimate is 0.0 and the figure is unknown, not zero"
        )
        if note not in warnings:
            warnings.append(note)
    return {
        "resource_id": str(raw.get("id")),
        "type": TYPE_COMPUTE_INSTANCE,
        "name": raw.get("label"),
        "region": region,
        "size": type_id,
        "state": STATE_STOPPED if status == POWERED_OFF_STATUS else status,
        "created_at": raw.get("created"),
        "last_activity_at": None,
        "attached_to": None,
        "monthly_cost_estimate": money(rate) if rate is not None else 0.0,
        "tags": tags_of(raw),
        "raw_ref": f"linode://linode/instances/{raw.get('id')}",
    }


def normalize_volume(raw: dict, prices: Prices, warnings: list) -> dict:
    """A Linode volume.

    Attachment is `linode_id` (nullable), exactly as DO derives it from `droplet_ids`. Note
    the axis mismatch the scout flagged: Linode's volume `status` is *lifecycle*
    (`creating`/`active`/`resizing`/`key_rotating`), not attachment — `active` means "online
    and ready for use" whether attached or not — so `status` is passed through as the state
    and is never read as an attachment signal.
    """
    linode_id = raw.get("linode_id")
    size_gb = raw.get("size") or 0
    # The basis is deliberately not carried on the resource: a `rate_basis` companion on the
    # inventory schema is a §Normalized change (§D-L5), and making one inside the milestone
    # whose purpose is proving §Normalized does not change would confound the proof. It is
    # recorded in the implementation notes and, when unknown, in `warnings[]`.
    monthly, _basis = volume_monthly(size_gb, raw.get("region"), prices, warnings)
    return {
        "resource_id": str(raw.get("id")),
        "type": TYPE_VOLUME,
        "name": raw.get("label"),
        "region": raw.get("region"),
        "size": f"{size_gb}GB",
        "state": raw.get("status"),
        "created_at": raw.get("created"),
        "last_activity_at": None,
        "attached_to": str(linode_id) if linode_id is not None else None,
        "monthly_cost_estimate": monthly,
        "tags": tags_of(raw),
        "raw_ref": f"linode://volumes/{raw.get('id')}",
    }


#: The volume `types` id. `/volumes/types` returns a single row whose `id` is `volume`.
#:
#: A collision worth naming: this literal is spelled exactly like the canonical `TYPE_VOLUME`
#: and means something entirely different — it is Linode's price-table key, sent on the wire,
#: while the canonical value is schema vocabulary imported from `_normalized`. They are equal
#: today by coincidence, and nothing keeps them equal: renaming the canonical type would
#: (correctly) leave this untouched. The adapter's vocabulary guard exempts exactly this one
#: assignment and fails on any other occurrence, so the coincidence cannot quietly spread.
VOLUME_TYPE_ID = "volume"

#: Whether `/volumes/types .price.monthly` is per-GB or per-volume is **not stated in the
#: schema** (scout U11), and the spec's example figure is identical to the NodeBalancer one —
#: which is what a placeholder looks like. Settled here from the account's own invoice, not
#: from the list price and not from the spec.
#:
#: EVIDENCE (live read 2026-08-05, invoice 32251471 covering 2026-07-01 -> 2026-08-01):
#: volume 9022878 is 10 GB in `ap-west`; its invoice line
#: `"Storage Volume - pvc-0a8dce06b486430a (9022878) - 10 GiB"` carries
#: `unit_price "0.0015"` and `amount 1.00`. The live `/volumes/types` row `id: "volume"`
#: carries `price.hourly 0.00015` and `price.monthly 0.1`. Both axes agree and both are
#: exact: 0.00015 x 10 GB == 0.0015 (the billed hourly unit price), and 0.1 x 10 GB == 1.00
#: (the billed monthly amount). Per-GB, confirmed twice over.
#:
#: If this were ever unset, a volume would be emitted with 0.0 plus a named warning rather
#: than a plausible per-GB multiply — `rule_unattached_volume` fires on attachment and age,
#: not on a non-zero estimate (`detect_orphans.py:165-181`), so an unknown basis would cost
#: the saving figure, never the rule.
VOLUME_PRICE_BASIS = "per_gb"
VOLUME_PRICE_BASIS_EVIDENCE = (
    "invoice 32251471 line for volume 9022878 (10 GiB): unit_price 0.0015 == "
    "/volumes/types hourly 0.00015 x 10 GB; amount 1.00 == monthly 0.1 x 10 GB"
)

#: A NodeBalancer object's `.type` is `common`/`premium`, but `/nodebalancers/types` keys its
#: rows `nodebalancer` / `nodebalancer-pr100` / `nodebalancer-40GB-pr100`. The object's value
#: is therefore NOT a key into the price table, and reading it as one yields None — which
#: would silently price every load balancer at 0.0.
#:
#: EVIDENCE for the one mapping this table states (live read 2026-08-05): NodeBalancer
#: 1343674 carries `"type": "common"`, and its invoice line
#: `"NodeBalancer - ccm-8cac00823f9b (1343674)"` carries `unit_price "0.015"` and
#: `amount 10.00` — exactly the `/nodebalancers/types` row `id: "nodebalancer"`
#: (`price.hourly 0.015`, `price.monthly 10.0`). So `common` bills at `nodebalancer`.
#:
#: `premium` is deliberately absent: this account holds no premium NodeBalancer, so there is
#: no evidence for which of the two `-pr100` rows it bills at, and guessing by name is exactly
#: the fabrication the milestone forbids. An unmapped type yields 0.0 plus a named warning.
NODEBALANCER_TYPE_PRICE_ID = {"common": "nodebalancer"}


def volume_monthly(size_gb, region, prices: Prices, warnings: list):
    """Monthly estimate for a volume, or 0.0 plus a named warning when the rate's unit is
    not established. Never an invented figure."""
    rate = prices.monthly(VOLUME_TYPE_ID, region)
    if rate is None:
        note = (
            "volume: no price read from /volumes/types; monthly_cost_estimate is 0.0 and the "
            "figure is unknown, not zero"
        )
        if note not in warnings:
            warnings.append(note)
        return 0.0, None
    if VOLUME_PRICE_BASIS == "per_gb":
        return money(rate * (size_gb or 0)), (
            f"{prices.basis(VOLUME_TYPE_ID, region)} x {size_gb}GB "
            f"({VOLUME_PRICE_BASIS_EVIDENCE})"
        )
    if VOLUME_PRICE_BASIS == "per_volume":
        return money(rate), f"{prices.basis(VOLUME_TYPE_ID, region)} ({VOLUME_PRICE_BASIS_EVIDENCE})"
    note = (
        "volume: /volumes/types states a monthly rate but not its unit (per-GB or "
        "per-volume — scout U11), so no estimate is derived; monthly_cost_estimate is 0.0 "
        "and the figure is unknown, not zero"
    )
    if note not in warnings:
        warnings.append(note)
    return 0.0, None


def normalize_nodebalancer(
    raw: dict, backends: int | None, prices: Prices, warnings: list
) -> dict:
    """A NodeBalancer is a `load_balancer` in the canonical vocabulary.

    Backends are **not on this object**: `nodes_status.{up,down}` lives on each config, so a
    NodeBalancer has zero backends iff Σ(up + down) == 0 across all its configs, including the
    degenerate case of zero configs. That is why this normalizer takes a backend count the
    caller computed from a second request per NodeBalancer.

    Linode has no tag-targeting concept — checked and absent, not unmentioned — so DO's
    `"tag:<name>"` attachment carve-out (`fetch_do.py:426-433`) has no analogue here and is
    deliberately not reproduced. `attached_to` is null exactly when there are no backends.

    A NodeBalancer whose backend count could not be read is **not** reported as unattached:
    `backends is None` means unknown, and an unknown must never render as the idle-LB signal.
    """
    type_id = raw.get("type") or "common"
    region = raw.get("region")
    # The object's `type` is not a key into the price table; see NODEBALANCER_TYPE_PRICE_ID.
    price_id = NODEBALANCER_TYPE_PRICE_ID.get(type_id)
    rate = prices.monthly(price_id, region) if price_id else None
    if rate is None:
        note = (
            f"nodebalancer: no price basis for type {type_id!r} — /nodebalancers/types keys "
            f"its rows differently and only {sorted(NODEBALANCER_TYPE_PRICE_ID)} is evidenced "
            f"by an invoice line; monthly_cost_estimate is 0.0 and the figure is unknown, "
            f"not zero"
        )
        if note not in warnings:
            warnings.append(note)
    return {
        "resource_id": str(raw.get("id")),
        "type": TYPE_LOAD_BALANCER,
        "name": raw.get("label"),
        "region": region,
        "size": type_id,
        # The NodeBalancer object carries no status field at all (scout §B4).
        "state": None,
        "created_at": raw.get("created"),
        "last_activity_at": None,
        "attached_to": None if backends == 0 else _backend_marker(raw, backends),
        "monthly_cost_estimate": money(rate) if rate is not None else 0.0,
        "tags": tags_of(raw),
        "raw_ref": f"linode://nodebalancers/{raw.get('id')}",
    }


def normalize_static_ip(raw: dict) -> dict:
    """A reserved Linode address is a `static_ip` in the canonical vocabulary.

    Only addresses carrying `reserved: true` reach this normalizer — see
    `is_reservable_address` for why, and for the spec-versus-live divergence behind it.
    """
    entity = raw.get("assigned_entity") or None
    attached_to = None
    if isinstance(entity, dict) and entity.get("id") is not None:
        attached_to = f"{entity.get('type') or 'entity'}:{entity['id']}"
    elif raw.get("linode_id") is not None:
        attached_to = str(raw["linode_id"])
    return {
        "resource_id": str(raw.get("address")),
        "type": TYPE_STATIC_IP,
        "name": raw.get("address"),
        "region": raw.get("region"),
        "size": None,
        "state": "assigned" if attached_to else "unassigned",
        # An IP object carries no allocation timestamp. Null here costs nothing:
        # `rule_unassociated_static_ip` has no age threshold (`detect_orphans.py:187-199`),
        # and it is already the AWS precedent (`fetch_aws.py:556-558`).
        "created_at": None,
        "last_activity_at": None,
        "attached_to": attached_to,
        # Linode publishes no pricing endpoint for addresses, so no rate can be read. The
        # caller adds the warning once per run rather than once per address.
        "monthly_cost_estimate": 0.0,
        "tags": tags_of(raw),
        "raw_ref": f"linode://networking/ips/{raw.get('address')}",
    }


def is_reservable_address(raw: dict) -> bool:
    """Whether an address has orphan semantics at all — m3 §D-L9, settled by live read.

    **The spec and the live API disagree, and the live API is what the adapter binds to.**
    OpenAPI 4.215.0 declares an IP object's complete field set as
    `{address, gateway, interface_id, linode_id, prefix, public, rdns, region, subnet_mask,
    type, vpc_nat_1_1}` — no `reserved` flag anywhere, which is why the scout concluded a
    reserved address might not be distinguishable from the free primary address every Linode
    has, and why §D-L9 pre-authorised recording the rule as not-reachable-on-Linode. The live
    response carries **three fields the spec does not declare**: `reserved`, `assigned_entity`
    and `tags`. So the distinction *is* expressible, and the rule is reachable after all.

    Two consequences, both load-bearing:

      * `reserved` is the discriminator. The spec's own request-body prose contrasts "a
        reserved or an automatically assigned IP", so the two-way distinction is the
        provider's, not this adapter's. Only reserved addresses are emitted: an
        automatically-assigned primary cannot be an orphan — it is inseparable from the
        instance that owns it — and emitting one would flag primaries, exactly the
        false-positive §D-L9 forbids.
      * `linode_id` alone is **not** an attachment signal. In the recorded read, two addresses
        carry `linode_id: null` while `assigned_entity` names the NodeBalancer each belongs
        to. Keying attachment on `linode_id` would have reported two in-service NodeBalancer
        addresses as unassociated — a well-formed wrong answer produced by reading the spec's
        field set as complete.

    This is the `CLAUDE.md` resolved-versus-advertised rule in a new carrier: a specification
    states what the API is *declared* to return, the wire states what it *does* return, and
    the two diverge exactly where the declaration is stale.
    """
    return raw.get("reserved") is True


def _backend_marker(raw: dict, backends: int | None) -> str:
    """What a NodeBalancer with backends (or with an unreadable backend count) is attached
    to. The rule keys on null/non-null, so any stable non-null marker is correct; this one
    states which case it is."""
    if backends is None:
        return f"unknown:configs-unreadable:{raw.get('id')}"
    return f"backends:{backends}"


def normalize_image(raw: dict, warnings: list) -> dict:
    """An Image is a `snapshot` in the canonical vocabulary.

    Two Linode-specific facts shape this normalizer, both recorded in m3 §D-L11:

      * An image records **no source** — there is no field naming the instance or disk it was
        taken from. So the aged-snapshot rule's second evidence signal (`attached_to is None`
        meaning the source is gone, `detect_orphans.py:220-223`) has no field to read, and
        `attached_to` is null on every image. The rule fires on age alone, which is its
        primary signal.
      * There is **no pricing endpoint for images** at all — not one that returns an empty
        price, one that does not exist. The estimate is therefore 0.0 with a named
        `warnings[]` entry (the `fetch_aws.py:474-482` precedent), never an invented figure.

    `regions` is plural — "details on the regions where this image is stored" — and there is
    no scalar region field. The normalized `region` takes the single region when the image is
    stored in exactly one, and null when it is stored in several: the schema's own answer is
    "many", and picking one of many would state as fact something the provider did not.
    """
    note = (
        "image: Linode publishes no pricing endpoint for images, so monthly_cost_estimate is "
        "0.0 — the saving is unknown, not zero"
    )
    if note not in warnings:
        warnings.append(note)
    regions = [
        row.get("region")
        for row in (raw.get("regions") or [])
        if isinstance(row, dict) and row.get("region")
    ]
    return {
        "resource_id": str(raw.get("id")),
        "type": TYPE_SNAPSHOT,
        "name": raw.get("label"),
        "region": regions[0] if len(regions) == 1 else None,
        "size": f"{raw.get('size')}MB" if raw.get("size") is not None else None,
        "state": raw.get("status"),
        "created_at": raw.get("created"),
        "last_activity_at": None,
        "attached_to": None,
        "monthly_cost_estimate": 0.0,
        "tags": tags_of(raw),
        "raw_ref": f"linode://images/{raw.get('id')}",
    }


# -------------------------------------------------------------------------- fetchers


def fetch_account(client: LinodeClient) -> tuple:
    """Account identity for the snapshot header, plus the balance object.

    Returns the raw account body too, so the caller can read `balance`/`balance_uninvoiced`
    without a second request.
    """
    body = client.get("/account") or {}
    account = body.get("euuid") or body.get("email") or "unknown"
    return account, body


def select_invoice(client: LinodeClient, period: str) -> dict:
    """Find the invoice **issued** in `period`.

    An invoice object carries a `date` and no period field of the DO kind, and the live read
    shows the two are a month apart: invoice 32251471 is dated `2026-08-01T04:36:37` and every
    one of its items runs `from 2026-07-01T04:00:00` `to 2026-08-01T03:59:59`. So the invoice
    issued in month M bills month M-1.

    Selection is by issue month, which is what makes `linode_costs_{current month}.json` exist
    on a run in an in-flight month: Linode publishes no live invoice preview (DO's
    `invoice_preview` has no analogue), so selecting by *covered* period would find nothing
    for the current month and every live run would degrade to partial. The covered range is
    not left implicit — `provider_extra.invoice.period_covered` carries the items' own
    `from`/`to`, so a reader can never mistake which month the figures are for.

    The divergence from DO — whose `period` is the covered period — is real and is recorded in
    the implementation notes as a cross-provider comparability item rather than silently
    picked; it shifts the label, not the month-over-month delta.
    """
    for invoice in client.paginate("/account/invoices"):
        date = invoice.get("date") or ""
        if isinstance(date, str) and date.startswith(period):
            return invoice
    raise LinodeAPIError(f"no Linode invoice issued in period {period}")


def fetch_costs(client: LinodeClient, account: str, period: str, account_body: dict) -> dict:
    invoice = select_invoice(client, period)
    items = client.paginate(f"/account/invoices/{invoice.get('id')}/items")
    return normalize_cost(invoice, items, account, period, balance=account_body)


def fetch_prices(client: LinodeClient, warnings: list) -> Prices:
    """Read live prices from the unauthenticated `types` endpoints.

    `security: null` on all of them, so this sweep needs no scope. Images are absent from
    this list because Linode publishes no image pricing endpoint — an absence recorded where
    the reader will look for it, rather than a silently missing entry.
    """
    prices = Prices()
    prices.load(client, "/linode/types", "compute instance", warnings)
    prices.load(client, "/volumes/types", "volume pricing", warnings)
    prices.load(client, "/nodebalancers/types", "nodebalancer", warnings)
    return prices


def fetch_nodebalancers(client: LinodeClient, prices: Prices, warnings: list) -> tuple:
    """NodeBalancers plus their configs — 1 + N requests.

    The per-config `.../nodes` endpoint is not needed: `nodes_status.{up,down}` on the config
    already carries the count.
    """
    resources: list = []
    errors: list = []
    for raw in client.paginate("/nodebalancers"):
        backends = None
        try:
            configs = client.paginate(f"/nodebalancers/{raw.get('id')}/configs")
            backends = 0
            for config in configs:
                status = config.get("nodes_status") or {}
                backends += (status.get("up") or 0) + (status.get("down") or 0)
        except (LinodeAPIError, requests.RequestException) as exc:
            # An unreadable config list leaves the backend count UNKNOWN. The normalizer
            # renders that distinctly from zero, so a failed read can never fire the idle
            # load-balancer rule.
            errors.append(
                {
                    "source": f"/nodebalancers/{raw.get('id')}/configs",
                    "error": str(exc),
                }
            )
        resources.append(normalize_nodebalancer(raw, backends, prices, warnings))
    return resources, errors


def fetch_inventory(
    client: LinodeClient, account: str, period: str, prices: Prices, warnings: list
) -> tuple:
    """Fetch every inventory class.

    m3 §D-L6 — a class never degrades silently to `[]`. A failing class becomes an `errors[]`
    entry *and* is named in `not_inventoried`, so a scope denial can never read as "the
    account owns none of these". The precedent is explicit and already adjudicated once:
    `fetch_aws.py:98-102` records why `UnauthorizedOperation` is deliberately not treated as a
    benign warning, because it would "produce an empty inventory on a green run, with a reason
    that reads plausibly and is wrong".
    """
    resources: list = []
    errors: list = []
    not_inventoried: list = []
    surveyed: dict = {}

    def guard(name: str, collect):
        try:
            resources.extend(collect())
        except LinodeAuthError:
            raise
        except (LinodeAPIError, requests.RequestException) as exc:
            errors.append({"source": name, "error": str(exc)})
            not_inventoried.append(
                {
                    "class": name,
                    "reason": "endpoint did not return 200; the class is UNKNOWN, not empty",
                }
            )

    guard(
        "/linode/instances",
        lambda: [
            normalize_instance(raw, prices, warnings)
            for raw in client.paginate("/linode/instances")
        ],
    )
    guard(
        "/volumes",
        lambda: [
            normalize_volume(raw, prices, warnings) for raw in client.paginate("/volumes")
        ],
    )

    def nodebalancers():
        rows, config_errors = fetch_nodebalancers(client, prices, warnings)
        errors.extend(config_errors)
        return rows

    guard("/nodebalancers", nodebalancers)
    guard(
        "/images",
        lambda: [
            normalize_image(raw, warnings)
            for raw in client.paginate("/images")
            # `is_public` marks distribution images that are not the account's own; billing
            # and orphan semantics apply only to images the account created.
            if not raw.get("is_public")
        ],
    )

    def static_ips():
        addresses = client.paginate("/networking/ips")
        reserved = [raw for raw in addresses if is_reservable_address(raw)]
        # The survey is why a zero here is readable. An empty `static_ip` class can mean the
        # account holds no reserved address (a fact) or that nothing was looked at (an
        # unknown), and the two are indistinguishable from the resource list alone — so the
        # counts that produced the zero are stated rather than left to be inferred.
        surveyed["networking_ips"] = {
            "addresses_read": len(addresses),
            "reserved": len(reserved),
            "emitted_as_static_ip": len(reserved),
            "note": (
                "only addresses with reserved=true carry orphan semantics; an "
                "automatically-assigned primary is inseparable from its instance and is "
                "never emitted (§D-L9)"
            ),
        }
        if reserved:
            note = (
                "static_ip: Linode publishes no pricing endpoint for addresses, so "
                "monthly_cost_estimate is 0.0 — the saving is unknown, not zero"
            )
            if note not in warnings:
                warnings.append(note)
        return [normalize_static_ip(raw) for raw in reserved]

    guard("/networking/ips", static_ips)

    inventory = {
        "provider": "linode",
        "account": account,
        "period": period,
        "resources": resources,
        "generated_at": iso_now(),
    }
    return inventory, errors, not_inventoried, surveyed


# ------------------------------------------------------------------------------- main


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Linode read-only cost/inventory adapter")
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
    warnings: list = []
    started = time.perf_counter()

    def fail(message: str) -> int:
        print(message, file=sys.stderr)
        print(json.dumps({"status": "error", "error": message}, indent=2))
        return 1

    try:
        warn_shadowing_env()
        client = LinodeClient(
            token=load_token(),
            api_base=args.api_base,
            timeout=args.timeout,
            max_retries=args.max_retries,
            retry_base_delay=args.retry_base_delay,
        )
        account, account_body = fetch_account(client)
    except (LinodeAuthError, LinodeAPIError) as exc:
        return fail(str(exc))

    prices = fetch_prices(client, warnings)

    costs = None
    try:
        costs = fetch_costs(client, account, period, account_body)
    except LinodeAuthError as exc:
        return fail(str(exc))
    except (LinodeAPIError, requests.RequestException) as exc:
        errors.append({"source": "billing", "error": str(exc)})

    try:
        inventory, inventory_errors, not_inventoried, surveyed = fetch_inventory(
            client, account, period, prices, warnings
        )
        errors.extend(inventory_errors)
    except LinodeAuthError as exc:
        return fail(str(exc))

    written = {}
    if costs is not None:
        written["costs"] = str(write_json(output_dir / f"linode_costs_{period}.json", costs))
    written["inventory"] = str(
        write_json(output_dir / f"linode_inventory_{period}.json", inventory)
    )

    summary = {
        "status": "ok" if not errors else "partial",
        "period": period,
        "files": written,
        "counts": {
            "line_items": len(costs["line_items"]) if costs else 0,
            "resources": len(inventory["resources"]),
        },
        "totals": costs["totals"] if costs else None,
        # BL-096 input: the adapter's own wall-clock, so the shared fetch-step timeout is
        # confirmed against a measurement rather than assumed (runbook.md:420-428).
        "duration_ms": int((time.perf_counter() - started) * 1000),
        # A class that could not be read is UNKNOWN, and renders differently from one that is
        # genuinely empty (§D-L6).
        "not_inventoried": not_inventoried,
        # ...and a class that WAS read and legitimately yielded nothing states the counts
        # behind that nothing, so an observed zero is distinguishable from an unexamined one.
        "surveyed": surveyed,
        # Classes deliberately not swept, each with its reason — an exclusion, never an
        # absence (done-when 8).
        "exclusions": [dict(row) for row in EXCLUSIONS],
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
