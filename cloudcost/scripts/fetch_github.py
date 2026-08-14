#!/usr/bin/env python3
"""GitHub read-only cost + inventory adapter (cloudcost m6, t2).

Fetches GitHub billing (the organisation's monthly usage summary, reconciled on every run
against the per-day usage detail) and resource inventory (Copilot seats) and emits the two
normalized JSON files defined in `cloudcost/milestone.md` §Normalized schemas:

    {output_dir}/github_costs_{YYYY-MM}.json
    {output_dir}/github_inventory_{YYYY-MM}.json

Read-only by construction: every call is a GET against a list/get endpoint. This script
never creates, modifies or deletes a GitHub resource.

Auth (m1 D2, m6 t2 §W2). The token is read from CLOUDCOST_GITHUB_TOKEN and passed to the HTTP
client explicitly. GH_TOKEN / GITHUB_TOKEN / GH_ENTERPRISE_TOKEN / GITHUB_ENTERPRISE_TOKEN /
GITHUB_PERSONAL_ACCESS_TOKEN are never read: a stray write token in the environment must not
be able to shadow the intended read-only one. The token is env-only — never an argument,
never printed to stdout or stderr, never written to an output file.

Three things distinguish this adapter from its three predecessors.

  * It is the first whose shadowed names are routinely PRESENT rather than hypothetical.
    `gh` is installed on developer workstations and CI runners alike and reads
    `GH_TOKEN`/`GITHUB_TOKEN` in that precedence order (`gh help environment`); on the
    machine this adapter was written both `GITHUB_TOKEN` and `GITHUB_PERSONAL_ACCESS_TOKEN`
    were set, to a broader-scoped write credential than the read-only one used here. The
    refusal half of the convention is load-bearing rather than precautionary.
  * The cost figure is built from ONE endpoint and checked against ANOTHER on every run
    (m6 D7). The summary endpoint is the source; the detail endpoint is an independent
    reconcile arm. They are two aggregations of the same underlying spend, so they agree to
    within float-summation noise — and a run where they do not has lost the basis on which
    the summary endpoint was chosen, which is why divergence withholds the snapshot rather
    than annotating it.
  * Only the summary endpoint echoes the period it served. The detail endpoint answers HTTP
    200 to `month=13` with the *January* rows and HTTP 200 with an empty array for a month
    predating the data, so an out-of-range month is indistinguishable from an empty one
    there by status code alone. The period is therefore validated before the call and the
    summary's echo asserted after it, and the reconcile arm inherits that verified period
    rather than asserting one of its own.

Usage:
    python3 scripts/fetch_github.py [--output-dir output] [--period YYYY-MM] [--org NAME]
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

from _normalized import TYPE_SEAT, iso, money, parse_timestamp

DEFAULT_API_BASE = "https://api.github.com"

#: The only environment variable this adapter will authenticate with.
TOKEN_ENV = "CLOUDCOST_GITHUB_TOKEN"

#: The organisation to bill, when it is not passed as `--org` and not discoverable.
ORG_ENV = "CLOUDCOST_GITHUB_ORG"

#: Credential variables GitHub tooling reads by default. This adapter ignores them; their
#: presence is warned about, never their value. Membership is `gh help environment`'s own
#: list, in the precedence order it states, not a guess: `GH_TOKEN` then `GITHUB_TOKEN` for
#: github.com and `*.ghe.com`, `GH_ENTERPRISE_TOKEN` then `GITHUB_ENTERPRISE_TOKEN` for a
#: GitHub Enterprise Server host. `GITHUB_PERSONAL_ACCESS_TOKEN` is read by nothing on that
#: list and is warned about because it is a conventional spelling users export — the same
#: honesty clause `fetch_linode.py:64-68` records for `LINODE_TOKEN`, and it is set on this
#: workstation, so the convention is a live one rather than a supposed one.
SHADOWING_ENV = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
)

#: Endpoint-shaping variables. A different hazard from a shadowing credential: they redirect
#: *where a credential is sent* rather than which credential is used (the class
#: `fetch_linode.py:70-77` established). `GH_HOST` is gh's own — "specify the GitHub hostname
#: ... If this host was previously authenticated with, the stored credentials will be used".
#: `GITHUB_API_URL` is not gh's; it is read by `@actions/github`, and is named here with that
#: provenance rather than folded in as though gh honoured it.
#:
#: `GH_CONFIG_DIR` is deliberately EXCLUDED. It redirects which *stored* credential gh picks
#: up, which is a hazard only for a caller that uses gh's credential store; this adapter uses
#: none. A padded list is the thing `fetch_linode.py`'s comment argues against, so the
#: exclusion is recorded rather than left as a silent absence.
ENDPOINT_REDIRECT_ENV = ("GH_HOST", "GITHUB_API_URL")

#: Provenance for the currency constant below (m6 D1). Both billing endpoints were swept in
#: full over a settled month — structurally over every object at every depth, and textually
#: over the raw body — and neither declares a currency field. The complete key set across the
#: two is {date, discountAmount, discountQuantity, grossAmount, grossQuantity, month,
#: netAmount, netQuantity, organization, organizationName, pricePerUnit, product, quantity,
#: repositoryName, sku, timePeriod, unitType, usageItems, year}, and the substrings `currenc`
#: and `usd` appear in neither body. `currency_field_names` re-runs the structural half of
#: that sweep on every fetch, so the basis cannot go stale silently.
API_VERSION = "2022-11-28"
CURRENCY_BASIS_PERIOD = "2026-07"

#: GitHub bills in USD; neither billing endpoint carries a currency field (see above).
#: Asserted with its basis, which is the posture all three predecessors take and the one
#: `fetch_linode.py:583-586` states as provenance rather than leaving bare (m6 D1).
CURRENCY = "USD"

#: C4's stated figure — "The reconcile tolerance ... is an absolute one-hundredth today" —
#: used rather than invented, and applied to the FULL-PRECISION sums rather than to their
#: rounded forms (m6 D3: rounding follows aggregation).
#:
#: The one existing reconcile arm (`fetch_linode.normalize_cost`) instead tests exact equality
#: after `money()`, an implicit half-cent. That is right for what it checks — one payload's own
#: parts against its own declared total, where any difference at all means an amount failed to
#: parse. This arm compares two INDEPENDENT aggregations, one of them over hundreds of float
#: terms, so the residual is summation noise rather than evidence and an explicit epsilon is
#: the honest form. Measured headroom on a settled month: 2.8e-14 against 1e-2.
RECONCILE_TOLERANCE = 0.01

#: The summary SKU that prices a Copilot seat, and the unit it is stated in. The per-seat
#: estimate is derived from this row and from nothing else; an absent row yields 0.00 plus a
#: named warning, never a figure borrowed from the plan tier or from a neighbouring SKU.
SEAT_SKU = "copilot_for_business"
SEAT_UNIT = "user-months"

#: `YYYY-MM`, months 01-12. Validated BEFORE the call, deliberately — see the module
#: docstring. None of the three predecessors validates on purpose: `fetch_do.select_invoice`
#: matches the string literally against `invoice_period`, `fetch_aws.month_bounds` raises out
#: of an incidental `strptime`, and `fetch_linode.month_of` slices. This adapter is the first,
#: because it is the first whose provider answers an invalid period with HTTP 200.
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_PAGES = 100
#: The REST API's documented maximum page size.
PAGE_SIZE = 100

#: Resource classes deliberately not inventoried, each with the reason. An excluded class is
#: recorded as an exclusion, never left as an absence — absent is unknown, not zero. Emitted
#: in the run summary.
EXCLUSIONS = (
    {
        "class": "organization_member",
        "endpoint": "/orgs/{org}/members",
        "reason": (
            "m6 D6: a member seat carries a stable identifier but no activity signal and no "
            "per-instance cost, failing two of the three legs the consumption class is "
            "bounded by. The org's plan reports purchased-versus-filled seat counts, but that "
            "is a class-level figure and synthesising resources from it would invent entities "
            "the provider does not enumerate"
        ),
    },
    {
        "class": "actions_artifact",
        "endpoint": "/repos/{owner}/{repo}/actions/artifacts",
        "reason": (
            "m6 §Ticket set: enumerable per repository rather than per organisation, lifetime "
            "governed by a retention policy rather than by neglect, and no per-instance cost"
        ),
    },
    {
        "class": "actions_cache",
        "endpoint": "/repos/{owner}/{repo}/actions/caches",
        "reason": "m6 §Ticket set: same as actions_artifact — per-repo, retention-governed",
    },
    {
        "class": "package",
        "endpoint": "/orgs/{org}/packages",
        "reason": (
            "m6 §Ticket set: accumulation is real (org-level and persists until deleted), but "
            "the credential form reaching it is not the one this adapter uses and no packages "
            "product appears on this organisation's bill — so its cost is unestablished "
            "rather than known to be zero"
        ),
    },
)


class GitHubAuthError(RuntimeError):
    """Authentication/authorisation failure. Never carries the token."""


class GitHubAPIError(RuntimeError):
    """Non-auth API failure after retries are exhausted."""


# --------------------------------------------------------------------------- client


class GitHubClient:
    """Minimal read-only GitHub REST client: explicit auth, pagination, retry.

    Pagination is page-number against a documented maximum page size, like Linode's, rather
    than DO's follow-the-`next`-URL scheme — so `fetch_do.py`'s `_same_origin` re-rooting
    guard has no analogue here and is deliberately not copied.
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
            raise GitHubAuthError(f"{TOKEN_ENV} is empty")
        # Held only to redact it out of error text; never logged, never returned.
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.session = requests.Session()
        # Explicit credential. gh's GH_TOKEN/GITHUB_TOKEN precedence chain is never consulted,
        # and there is no default-pickup arm to disable — the header is built here or nowhere.
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "aetheris-cloudcost/1.0 (read-only)",
            }
        )

    def _redact(self, text: str) -> str:
        """Belt-and-braces: strip the token from any text that may reach an error path."""
        return text.replace(self._token, "***") if self._token else text

    def __repr__(self) -> str:  # pragma: no cover - defensive, keeps token out of reprs
        return f"<GitHubClient api_base={self.api_base!r}>"

    def _retry_delay(self, attempt: int, response) -> float:
        if response is not None:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    return min(float(retry_after), 60.0)
                except ValueError:
                    pass
        return self.retry_base_delay * (2**attempt)

    def get(self, path: str, params: dict | None = None):
        """GET a single GitHub endpoint, with retry on 429/5xx and transport errors."""
        url = f"{self.api_base}{path}"
        attempt = 0
        while True:
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt >= self.max_retries:
                    raise GitHubAPIError(
                        f"GET {path} failed after {attempt + 1} attempts: "
                        f"{type(exc).__name__}"
                    ) from None
                time.sleep(self._retry_delay(attempt, None))
                attempt += 1
                continue

            if response.status_code in (401, 403):
                # Fatal, not degrading: a rejected credential must never read as an empty
                # account. 403 is GitHub's answer to a fine-grained PAT missing a permission
                # as well as to a revoked one, and both are the operator's to fix.
                raise GitHubAuthError(
                    f"GitHub rejected the credential (HTTP {response.status_code}) on "
                    f"GET {path}. Check that {TOKEN_ENV} holds a valid read-only token with "
                    f"the organisation permission this endpoint needs."
                )
            if response.status_code in RETRY_STATUSES and attempt < self.max_retries:
                time.sleep(self._retry_delay(attempt, response))
                attempt += 1
                continue
            if not response.ok:
                body = self._redact(response.text)[:200]
                raise GitHubAPIError(f"GET {path} -> HTTP {response.status_code}: {body}")

            try:
                return response.json()
            except ValueError:
                raise GitHubAPIError(f"GET {path} -> non-JSON response body") from None

    def paginate(self, path: str, key: str | None = None, params: dict | None = None) -> list:
        """Collect every page of a list endpoint.

        GitHub returns two shapes and both are in use here: a bare JSON array (`/user/orgs`)
        and an object wrapping its rows under a key (`/orgs/{org}/copilot/billing/seats` under
        `seats`). `key=None` selects the first. A short page ends the walk, which is the
        page-number idiom without needing the `Link` header parsed.
        """
        items: list = []
        page = 1
        for _ in range(MAX_PAGES):
            query = dict(params or {})
            query.update({"page": page, "per_page": PAGE_SIZE})
            body = self.get(path, params=query)
            if key is None:
                rows = body if isinstance(body, list) else []
            else:
                rows = (body or {}).get(key) or []
            items.extend(rows)
            if len(rows) < PAGE_SIZE:
                return items
            page += 1
        raise GitHubAPIError(f"pagination for {path} exceeded {MAX_PAGES} pages")


# ----------------------------------------------------------------------------- helpers
#
# `current_period`, `iso_now`, `write_json` and `warn_shadowing_env` are duplicated from the
# sibling adapters rather than imported: a CLI-to-CLI import is the anti-pattern named at
# `_normalized.py:35-37`, and these already exist three times on purpose. `money`, `iso` and
# `parse_timestamp` are the exceptions — they are imported from `_normalized`, which is where
# the shared definitions live, following `fetch_linode.py:284-291` rather than the two
# predecessors' private `money` copies, which disagree with each other.


def load_token(env: dict | None = None) -> str:
    """Read the read-only token from CLOUDCOST_GITHUB_TOKEN and nowhere else."""
    env = os.environ if env is None else env
    token = (env.get(TOKEN_ENV) or "").strip()
    if not token:
        raise GitHubAuthError(
            f"{TOKEN_ENV} is not set. cloudcost authenticates with {TOKEN_ENV} only and "
            f"never falls back to {' / '.join(SHADOWING_ENV)} — export the read-only token "
            f"as {TOKEN_ENV} before running."
        )
    return token


def warn_shadowing_env(env: dict | None = None, stream=None) -> list:
    """Name (never print the value of) any stray GitHub credential that is being ignored,
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
            f"where a credential is sent, and cloudcost constructs its own GitHub base URL.",
            file=stream,
        )
    return present + redirects


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_utc(value):
    """Normalize a provider timestamp to the schema's `%Y-%m-%dT%H:%M:%SZ`, or None.

    GitHub states seat timestamps at the account's own UTC offset (`+05:30` on the recorded
    organisation) where §Normalized's example is `Z`. `last_activity_at` is the first non-null
    instance of that field any adapter has emitted, and t3's rule will compare it against a
    reference date — so it is normalized at the adapter rather than left for the rule to
    parse, which is the reasoning `fetch_aws.iso` already records for boto3's datetimes.
    """
    moment = parse_timestamp(value)
    return iso(moment) if moment is not None else None


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
    return path


def validate_period(period: str) -> str:
    """Reject a malformed period before any call is made — see `PERIOD_RE`."""
    if not isinstance(period, str) or not PERIOD_RE.match(period):
        raise GitHubAPIError(
            f"--period must be YYYY-MM with a month in 01-12; got {period!r}. GitHub's usage "
            f"detail endpoint answers an out-of-range month with HTTP 200 and another month's "
            f"rows, so an unvalidated period would be reconciled against the wrong data."
        )
    return period


def period_parts(period: str) -> tuple:
    """`(year, month)` as ints, for the query and for the echo assertion."""
    return int(period[:4]), int(period[5:7])


def currency_field_names(payload) -> list:
    """Every key anywhere in `payload` whose name suggests a currency field.

    The structural half of the D1 sweep, re-run on every fetch. The constant below is asserted
    against a recorded finding, and a recorded finding about a live API is a claim with no
    invalidation — this is the invalidation. Finding one does not change the emitted value
    (D1: adapter-declared, never captured); it means the declaration's stated basis is now
    false and the operator is told so.
    """
    found: set = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if "currenc" in str(key).lower():
                    found.add(str(key))
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(payload)
    return sorted(found)


# --------------------------------------------------------------------------- normalizers


def normalize_balance() -> dict:
    """The account-level month-to-date position, which GitHub does not have.

    Neither billing endpoint carries an account balance, an amount due, or a credit position,
    and the read-only credential this adapter uses reaches no endpoint that does. §Normalized
    requires the block, so it is emitted with nulls rather than omitted, and rather than
    restating the period total under a name that would then claim to be something it is not:
    a settled month's total is a final figure, and calling it `month_to_date_usage` would be
    a well-formed wrong answer for every period but the current one.
    """
    return {
        "month_to_date_balance": None,
        "account_balance": None,
        "month_to_date_usage": None,
        "generated_at": iso_now(),
    }


def normalize_cost(
    summary: dict,
    org: str,
    period: str,
    reconcile: dict | None = None,
) -> dict:
    """Build the cost snapshot from the billing usage SUMMARY endpoint (m6 D7).

    **Net to net (§W3b).** `amount` is `netAmount` and `usage_qty` is `netQuantity` — the two
    halves of one row, after discount. The detail endpoint's `quantity` sums to
    `grossQuantity`, not to net, so pairing a net amount with a gross quantity would make
    `amount / usage_qty` something other than an effective unit price. Verified on a settled
    month: `actions_linux` detail quantity 806.0 = summary grossQuantity 806.0, and its
    netQuantity is 0.0.

    **Service identity is the summary's own SKU spelling.** `source_granularity` is `service`,
    and the SKU is what the summary endpoint calls a billable thing. The two endpoints spell
    every product, SKU and unit differently and NOT as a case transform of one another —
    `copilot_for_business`/`user-months` there is `Copilot Business`/`UserMonths` here, and
    `copilot_ai_unit` is `Copilot AI Credits` — so a human comparing this report against the
    detail endpoint or the console will see different strings for the same thing.

    **`amount` is rounded and `usage_qty` is not.** C4's two-decimal rule is about money;
    ai-units and gigabyte-hours have no minor unit, and rounding a quantity to 2dp would
    destroy the divisor that makes the unit price recoverable.
    """
    items = summary.get("usageItems") or []

    line_items = [
        {
            "service": item.get("sku"),
            "resource_id": None,
            # GitHub's summary endpoint states no region for any product, and the detail
            # endpoint states none either. A real value or null, never a guess.
            "region": None,
            "amount": money(item.get("netAmount")),
            "usage_qty": item.get("netQuantity"),
            "usage_unit": item.get("unitType"),
            "tags": [],
        }
        for item in items
    ]
    # Descending by amount with the service as tie-break: several SKUs legitimately net to
    # 0.00 in a fully-discounted month, so amount alone is not a total order.
    line_items.sort(key=lambda item: (-item["amount"], item["service"] or ""))

    # Aggregate at full precision, round once (m6 D3/D4). Summing the already-rounded
    # `line_items[].amount` would accumulate up to half a cent per row.
    total = money(sum(float(item.get("netAmount") or 0.0) for item in items))

    return {
        "provider": "github",
        "account": org,
        "period": period,
        "currency": CURRENCY,
        "source_granularity": "service",
        "line_items": line_items,
        "totals": {"amount": total},
        "balance": normalize_balance(),
        "generated_at": iso_now(),
        # Provider-specific payload. Everything above is the frozen cross-provider contract;
        # anything GitHub-shaped that downstream scripts must not depend on generically lives
        # in here (§Normalized schemas).
        "provider_extra": {
            "organization": summary.get("organization") or org,
            # The endpoint's own echo of the period it served, kept as evidence for the
            # assertion `assert_period_echo` makes against it.
            "time_period": summary.get("timePeriod"),
            # The gross/discount/unit-price half of every row, which the first-class fields
            # deliberately do not carry (§W3b). Kept verbatim as the provider stated it.
            "usage_items": [
                {
                    "product": item.get("product"),
                    "sku": item.get("sku"),
                    "unitType": item.get("unitType"),
                    "grossQuantity": item.get("grossQuantity"),
                    "discountQuantity": item.get("discountQuantity"),
                    "netQuantity": item.get("netQuantity"),
                    "grossAmount": item.get("grossAmount"),
                    "discountAmount": item.get("discountAmount"),
                    "netAmount": item.get("netAmount"),
                    "pricePerUnit": item.get("pricePerUnit"),
                }
                for item in items
            ],
            # D7's independent arm, recorded on the artifact rather than only in the run log:
            # a reader holding this file can tell a reconciled figure from an unreconciled one.
            "reconcile": reconcile,
            "currency_basis": (
                f"adapter-asserted: the GitHub billing usage summary and detail endpoints "
                f"(X-GitHub-Api-Version {API_VERSION}) declare no currency field — both swept "
                f"in full over {CURRENCY_BASIS_PERIOD}, structurally at every depth and "
                f"textually over the raw body"
            ),
        },
    }


def seat_monthly_cost(summary: dict, warnings: list) -> float:
    """The per-seat monthly estimate: the SKU's own **rate**, `pricePerUnit`.

    **m6 t3 — corrected from month-to-date spend to the monthly rate, by ruling.** This
    returned `pricePerUnit × (netQuantity / seat_count)` until t3. `netQuantity` is
    user-months *consumed so far*, so that product was the rate scaled by a ratio reaching
    ~1.0 only on a settled month in which every seat was held throughout: the same six seats
    estimated at 7.97 for the in-flight `2026-08` against 19.00 for the settled `2026-07`.

    Two things make the rate the right figure and the correction a correction rather than a
    redefinition. **A saving is forward-looking** — this field feeds an orphan's
    `monthly_saving_estimate`, and a saving is what stops being paid next month, not what has
    already been spent this one; a seat reclaimed on the 14th saves the full monthly rate from
    then on. And §Normalized already says what the field is: *"the per-resource dollar figure —
    the provider's own price where given"*. GitHub gives one, in this very row, and
    DigitalOcean takes `price_monthly` for exactly this reason. The month-to-date product was a
    departure from that contract, not a permitted reading of it.

    **Nothing is lost.** The consumed user-months the old figure encoded are still carried, in
    the cost line item's `usage_qty` and in `provider_extra.usage_items` — where quantities
    belong. This function reports a price.

    **m6 D4 no longer binds here, and that is worth stating rather than leaving as an
    absence.** D4 governs an adapter that *multiplies a unit price by a quantity*; this one no
    longer multiplies, and `seat_monthly_cost` was its only such site in this adapter. What
    replaces D4's lossy-rate pin is a pin of the opposite property — that the estimate does not
    move with `netQuantity` — asserted in `test_fetch_github.py` across a settled month and an
    in-flight one.

    An absent SKU and an absent price each yield 0.00 plus one named warning, never a figure
    borrowed from the plan tier or from a neighbouring SKU.
    """
    items = (summary or {}).get("usageItems") or []
    row = next((item for item in items if item.get("sku") == SEAT_SKU), None)

    def unknown(reason: str) -> float:
        note = (
            f"copilot seats: {reason}, so the per-seat monthly_cost_estimate is reported as "
            f"0.00 rather than invented — the figure is unknown, not zero"
        )
        if note not in warnings:
            warnings.append(note)
        return 0.0

    if row is None:
        return unknown(f"the billing summary carries no `{SEAT_SKU}` row")

    price = row.get("pricePerUnit")
    if price is None:
        return unknown(f"the `{SEAT_SKU}` row states no pricePerUnit")

    return money(float(price))


def normalize_seat(raw: dict, org: str, unit_cost: float) -> dict | None:
    """A Copilot seat is a `seat` in the canonical vocabulary — the first consumption-class
    resource the pipeline emits, and the first resource of any provider to carry an activity
    timestamp.

    **`resource_id` is the assignee's numeric id, not the login.** A seat object carries no id
    of its own, so its stable key is the assignee's; and of the assignee's two identifiers only
    the numeric one is immutable. A user who renames would otherwise appear as a resource that
    vanished and a different one that appeared, in a report whose month-on-month section is
    built on exactly that comparison. The login survives as `name`, where it is the
    human-facing identity field the schema asks for.

    **`state` is null.** The seat object carries no lifecycle field: its complete property set
    is {created_at, assignee, pending_cancellation_date, plan_type, last_authenticated_at,
    updated_at, last_activity_at, last_activity_editor}. §Normalized's rule for a concept the
    provider lacks is a null value, never omission — and deriving `active` /
    `pending_cancellation` from `pending_cancellation_date` would be this adapter minting a
    state vocabulary locally, which is seam #1 with `state` in `type`'s place. §Normalized says
    other states are enumerated in the schema the moment a rule needs one; m6 t1 declined to
    add a canonical seat state, and this ticket is not the place to reverse that on the way
    past. `pending_cancellation_date` is therefore carried nowhere — see the t2 notes.

    **`attached_to` is a prefixed marker, and is never null.** C7's null is the universal idle
    signal, and a seat that is assigned to somebody is emphatically not idle — an unexercised
    one is t3's business, keyed on `last_activity_at`. The prefix follows the grammar
    `fetch_do.py:431` (`tag:`) and `fetch_linode.py:835` (`<entity type>:`) already use, and it
    is what stops C7's `attached_to`-against-`resource_id` join from matching a person to a
    resource that happens to share the number.
    """
    assignee = raw.get("assignee") or {}
    identifier = assignee.get("id")
    login = assignee.get("login")
    if identifier is None and not login:
        # Nothing stable to key on. Dropping the row is correct here and would not be for a
        # cost line: an inventory entry with no identity cannot be reported, joined or acted
        # on, and the caller warns so the short count is never silent.
        return None

    resource_id = str(identifier) if identifier is not None else str(login)
    return {
        "resource_id": resource_id,
        "type": TYPE_SEAT,
        "name": login,
        # GitHub seats have no region concept.
        "region": None,
        # C13 carry-only human label: the plan tier this seat is billed under. Nothing sorts,
        # compares, sums, branches or joins on it.
        "size": raw.get("plan_type"),
        "state": None,
        "created_at": iso_utc(raw.get("created_at")),
        "last_activity_at": iso_utc(raw.get("last_activity_at")),
        "attached_to": f"user:{login}" if login else f"user:{resource_id}",
        "monthly_cost_estimate": unit_cost,
        # GitHub exposes no tags for seats. The empty form the schema requires, not omission.
        "tags": [],
        "raw_ref": f"github://orgs/{org}/copilot/billing/seats/{resource_id}",
    }


# ----------------------------------------------------------------------------- fetchers


def resolve_org(client: GitHubClient, requested: str | None, env: dict | None = None) -> str:
    """The organisation to bill: the flag, else the env var, else the token's sole membership.

    Discovery is a real read, not an inference, and it refuses to choose: a token with no
    organisation membership and a token with several both raise, naming the flag. Picking the
    first of several would silently bill the wrong organisation on an account where the
    operator holds two, and nothing downstream could tell.
    """
    env = os.environ if env is None else env
    if requested:
        return requested
    configured = (env.get(ORG_ENV) or "").strip()
    if configured:
        return configured

    orgs = [row.get("login") for row in client.paginate("/user/orgs") or []]
    orgs = [login for login in orgs if login]
    if len(orgs) == 1:
        return orgs[0]
    if not orgs:
        raise GitHubAPIError(
            f"the credential's user belongs to no organisation, so there is nothing to bill "
            f"— pass --org or set {ORG_ENV}."
        )
    raise GitHubAPIError(
        f"the credential's user belongs to {len(orgs)} organisations, so the one to bill is "
        f"ambiguous — pass --org or set {ORG_ENV}."
    )


def assert_period_echo(summary: dict, period: str) -> None:
    """Reject a summary whose `timePeriod` is not the period that was asked for.

    Only this endpoint of the two echoes what it served (m6 D7), and this is the assertion
    that echo exists for. The failure it prevents is the quiet kind: a report whose figures
    are real and whose stated month is not the one they cover reads correctly, errors nowhere,
    and stays internally consistent under a constant offset — the shape
    `fetch_linode.resolve_billing` records for the same class of mistake.
    """
    echoed = summary.get("timePeriod")
    year, month = period_parts(period)
    if not isinstance(echoed, dict):
        raise GitHubAPIError(
            f"the billing usage summary for {period} echoed no timePeriod, so the month it "
            f"served cannot be confirmed and the figures are not attributable to a period."
        )
    if (echoed.get("year"), echoed.get("month")) != (year, month):
        raise GitHubAPIError(
            f"the billing usage summary was asked for {period} and served "
            f"{echoed.get('year')}-{echoed.get('month')} — the figures are for a different "
            f"month than the one requested and are not written."
        )


def reconcile_detail(detail: dict, summary_total: float, period: str) -> dict:
    """D7's per-run gate: the detail endpoint summed against the summary's own total.

    A finding at scout time is not a guarantee at run time — a new SKU, a mid-month credit or
    a plan change could break agreement in a month neither of the two that were checked. So
    the two are summed and compared on every fetch, at full precision, against C4's tolerance.

    Divergence RAISES rather than warning, and the difference from the one existing reconcile
    arm is deliberate. `fetch_linode.normalize_cost` warns because its declared total stays
    authoritative whatever its line items do. Here the agreement between the two endpoints is
    the entire ground on which D7 chose the summary endpoint as the source; if they disagree,
    that ground is gone and the figure has no basis. The precedent is `fetch_aws.py:859-874` —
    a zero written anyway "would be read as a real zero bill" — and the posture is the same:
    withhold the snapshot, keep the inventory, exit non-zero.
    """
    items = detail.get("usageItems") or []
    detail_total = sum(float(item.get("netAmount") or 0.0) for item in items)
    difference = detail_total - summary_total
    if abs(difference) > RECONCILE_TOLERANCE:
        raise GitHubAPIError(
            f"billing reconcile FAILED for {period}: the usage detail endpoint sums to "
            f"{detail_total!r} over {len(items)} items but the usage summary total is "
            f"{summary_total!r} — a difference of {difference!r} against a tolerance of "
            f"{RECONCILE_TOLERANCE}. m6 D7 builds the cost snapshot from the summary endpoint "
            f"ON THE GROUND that the two agree, so no snapshot is written."
        )
    return {
        "status": "reconciled",
        "source": "billing usage detail endpoint",
        "detail_items": len(items),
        "detail_total": detail_total,
        "summary_total": summary_total,
        "difference": difference,
        "tolerance": RECONCILE_TOLERANCE,
    }


def fetch_costs(client: GitHubClient, org: str, period: str, warnings: list) -> tuple:
    """Returns `(summary, cost_snapshot)` — built from the summary endpoint, gated on the
    detail endpoint.

    The raw summary is returned beside the snapshot rather than re-read off it: the inventory
    prices a seat from the `copilot_for_business` row's `pricePerUnit`/`netQuantity` pair, and
    those live under `provider_extra` on the artifact, which is exactly the block §Normalized
    forbids downstream from keying on generically. Handing the payload over directly keeps the
    adapter from taking a dependency on its own provider-specific block.
    """
    year, month = period_parts(period)
    query = {"year": year, "month": month}
    summary = client.get(
        f"/organizations/{org}/settings/billing/usage/summary", params=query
    )
    assert_period_echo(summary, period)

    items = summary.get("usageItems") or []
    if not items:
        # Two different zeros, and only one of them can be written.
        #
        #   * an echoed period with no usage rows -> GitHub has the month and reports no spend
        #     in it. That is what a month predating the organisation's data looks like, and it
        #     is also what a genuinely free month would look like. A $0.00 snapshot would be
        #     read as a real zero bill by everything downstream, and by a human, so the file is
        #     not written and the run says why.
        #
        #   * a period the endpoint rejects outright -> a 400 from the client, which never
        #     reaches here. That distinction is the summary endpoint's gift; the detail
        #     endpoint answers both with HTTP 200 (see the module docstring).
        raise GitHubAPIError(
            f"the billing usage summary for {period} carries no usage items. The period was "
            f"echoed back, so the month is real and reports no spend — which is not the same "
            f"claim as a bill of 0.00, and no cost snapshot is written for it."
        )

    stale = currency_field_names(summary)
    if stale:
        warnings.append(
            f"billing: the usage summary now carries {', '.join(stale)} — {CURRENCY} is still "
            f"emitted (D1: adapter-declared, never captured), but `currency_basis` says this "
            f"endpoint declares no currency field, and that statement is now false"
        )

    summary_total = sum(float(item.get("netAmount") or 0.0) for item in items)
    # The reconcile arm inherits the period the summary echoed rather than asserting its own:
    # the detail endpoint carries no timePeriod to assert against.
    detail = client.get(f"/organizations/{org}/settings/billing/usage", params=query)
    reconcile = reconcile_detail(detail, summary_total, period)

    return summary, normalize_cost(summary, org, period, reconcile=reconcile)


def fetch_inventory(
    client: GitHubClient, org: str, period: str, summary: dict | None, warnings: list
) -> tuple:
    """Copilot seats, and nothing else. See `EXCLUSIONS` for what is deliberately not swept."""
    errors: list = []
    resources: list = []
    surveyed: dict = {}

    try:
        seats = client.paginate(f"/orgs/{org}/copilot/billing/seats", "seats")
    except GitHubAPIError as exc:
        errors.append({"source": "copilot_seats", "error": str(exc)})
        return (
            {
                "provider": "github",
                "account": org,
                "period": period,
                "resources": resources,
                "generated_at": iso_now(),
            },
            errors,
            ["copilot_seat"],
            surveyed,
        )

    unit_cost = seat_monthly_cost(summary or {}, warnings)
    for raw in seats:
        seat = normalize_seat(raw, org, unit_cost)
        if seat is None:
            warnings.append(
                "copilot seats: a seat carries no assignee id and no login, so it has no "
                "stable identifier and is not emitted — the count is short by one and this "
                "line is why"
            )
            continue
        resources.append(seat)

    # A class that WAS read and legitimately yielded nothing states the count behind that
    # nothing, so an observed zero is distinguishable from an unexamined one.
    surveyed["copilot_seat"] = len(seats)

    inventory = {
        "provider": "github",
        "account": org,
        "period": period,
        "resources": resources,
        "generated_at": iso_now(),
    }
    return inventory, errors, [], surveyed


# -------------------------------------------------------------------------------- main


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="GitHub read-only cost/inventory adapter")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--period", default=None, help="YYYY-MM (default: current UTC month)")
    parser.add_argument(
        "--org",
        default=None,
        help=f"organisation login (default: {ORG_ENV}, else the token's sole membership)",
    )
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--retry-base-delay", type=float, default=1.0)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
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
        # Validated before the client is built, so a malformed period costs no request at all.
        period = validate_period(args.period or current_period())
        client = GitHubClient(
            token=load_token(),
            api_base=args.api_base,
            timeout=args.timeout,
            max_retries=args.max_retries,
            retry_base_delay=args.retry_base_delay,
        )
        org = resolve_org(client, args.org)
    except (GitHubAuthError, GitHubAPIError) as exc:
        return fail(str(exc))

    costs = None
    billing_summary = None
    try:
        billing_summary, costs = fetch_costs(client, org, period, warnings)
    except GitHubAuthError as exc:
        return fail(str(exc))
    except (GitHubAPIError, requests.RequestException) as exc:
        errors.append({"source": "billing", "error": str(exc)})

    try:
        inventory, inventory_errors, not_inventoried, surveyed = fetch_inventory(
            client, org, period, billing_summary, warnings
        )
        errors.extend(inventory_errors)
    except GitHubAuthError as exc:
        return fail(str(exc))

    written = {}
    if costs is not None:
        written["costs"] = str(write_json(output_dir / f"github_costs_{period}.json", costs))
    written["inventory"] = str(
        write_json(output_dir / f"github_inventory_{period}.json", inventory)
    )

    complete = not errors and not not_inventoried

    summary = {
        "status": "ok" if complete else "partial",
        "period": period,
        "organization": org,
        "files": written,
        "counts": {
            "line_items": len(costs["line_items"]) if costs else 0,
            "resources": len(inventory["resources"]),
        },
        "totals": costs["totals"] if costs else None,
        # D7's gate, surfaced where an operator reads it rather than only on the artifact.
        "reconcile": (costs or {}).get("provider_extra", {}).get("reconcile"),
        # BL-096 input: the adapter's own wall-clock, so the shared fetch-step timeout is
        # confirmed against a measurement rather than assumed.
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "not_inventoried": not_inventoried,
        "surveyed": surveyed,
        "exclusions": [dict(row) for row in EXCLUSIONS],
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
