#!/usr/bin/env python3
"""Merge N providers' cost + inventory + orphan bundles into one report-data file (m1, t3).

Consumes the normalized artifacts of the stages before it — an adapter's cost snapshot and
resource inventory (t1) and the orphan candidates detected from that inventory (t2) — and
emits the single structure the t4 report renders:

    {output_dir}/report_data_{YYYY-MM}.json

Sections: totals by service, the month-on-month delta against the prior calendar month's
persisted snapshot, tag coverage with the top untagged spenders, and the orphan candidates
grouped into confidence bands with their evidence carried through intact.

Pure and deterministic. `compose()` reads no clock, no environment and no filesystem: the
report is stamped "as of" the newest `generated_at` among its own inputs, so the same
inputs always produce a byte-identical payload. No LLM is involved in the merge or the
delta — every figure here is arithmetic over the stages' own output (D3).

**D4 — granularity is honest.** Cost totals are built from the cost snapshot's
service-level `line_items[].amount` only. A resource-level `monthly_cost_estimate` is an
estimate derived from size/type; it is used to rank untagged spenders and to carry an
orphan's saving, and is never summed into a cost total.

Written to merge N providers; N=1 is the DO-only m1 case. Each provider contributes one
bundle (cost + inventory + orphans), given either as a repeatable triple or discovered
from a directory.

Usage:
    python3 scripts/compose_report_data.py \\
        --cost output/do_costs_2026-07.json \\
        --inventory output/do_inventory_2026-07.json \\
        --orphans output/orphan_candidates_2026-07.json \\
        [--cost ... --inventory ... --orphans ...]   # repeat per provider \\
        [--output-dir output] [--history-dir cloudcost/history] \\
        [--period YYYY-MM] [--top-untagged 10]

    python3 scripts/compose_report_data.py --input-dir output [--period YYYY-MM]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from _normalized import (
    iso,
    money,
    parse_timestamp,
    provider_slug,
    tag_coverage,
    tags_of,
    usable_resources,
)

# ------------------------------------------------------------------------- constants

#: Confidence bands for the orphan section. Emitted into the payload alongside the grouped
#: candidates so the report shows the cutoffs it grouped by, rather than asking the reader
#: to trust three labels.
BAND_HIGH_MIN = 0.9
BAND_MEDIUM_MIN = 0.7

BANDS = (
    {
        "band": "HIGH",
        "min_confidence": BAND_HIGH_MIN,
        "max_confidence": None,
        "rule": f"confidence >= {BAND_HIGH_MIN}",
    },
    {
        "band": "MEDIUM",
        "min_confidence": BAND_MEDIUM_MIN,
        "max_confidence": BAND_HIGH_MIN,
        "rule": f"{BAND_MEDIUM_MIN} <= confidence < {BAND_HIGH_MIN}",
    },
    {
        "band": "LOW",
        "min_confidence": None,
        "max_confidence": BAND_MEDIUM_MIN,
        "rule": f"confidence < {BAND_MEDIUM_MIN}",
    },
)

#: How many untagged resources the report ranks. Overridable: --top-untagged N.
DEFAULT_TOP_UNTAGGED = 10

#: Persisted monthly cost snapshots. Anchored to the use-case root rather than the cwd:
#: history accumulates across runs and must land in the same place whichever directory the
#: orchestrator invoked the script from. Overridable: --history-dir (tests point it at a
#: tmp_path; the t5 sprint seeds a known prior month there).
DEFAULT_HISTORY_DIR = Path(__file__).resolve().parent.parent / "history"

#: A provider's declared period total and the sum of its line items may differ by at most
#: this much before the mismatch is reported as a warning.
RECONCILE_TOLERANCE = 0.01


# --------------------------------------------------------------------------- helpers


def prior_period(period: str):
    """The prior *calendar* month of `period`, derived from the period itself and never
    from the wall clock — re-composing an old period must look at that period's own
    predecessor. Returns None if `period` is not YYYY-MM."""
    if not isinstance(period, str) or not re.fullmatch(r"\d{4}-\d{2}", period):
        return None
    year, month = int(period[:4]), int(period[5:])
    if not 1 <= month <= 12:
        return None
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


def pct_change(current: float, prior: float):
    """Percent change, or None when the prior figure is zero (no meaningful ratio)."""
    if not prior:
        return None
    return round((current - prior) / prior * 100.0, 2)


def newest_timestamp(values) -> str | None:
    """The latest parseable timestamp in `values`, ISO-8601 Z. None if there is none."""
    moments = [m for m in (parse_timestamp(v) for v in values) if m is not None]
    return iso(max(moments)) if moments else None


def provider_of(bundle: dict) -> str:
    """A bundle's provider, read from whichever of its documents arrived."""
    for key in ("cost", "inventory", "orphans"):
        document = bundle.get(key)
        if isinstance(document, dict) and document.get("provider"):
            return str(document["provider"])
    return str(bundle.get("provider") or "unknown")


def period_of(bundles: list):
    """The period the bundles agree on, or None."""
    for bundle in bundles:
        for key in ("cost", "inventory", "orphans"):
            document = bundle.get(key)
            if isinstance(document, dict) and document.get("period"):
                return str(document["period"])
    return None


# ---------------------------------------------------------------------- cost totals


def service_totals(bundles: list, warnings: list) -> dict:
    """Totals by (provider, service), and the grand total.

    D4: the only figures read here are the cost snapshot's service-level
    `line_items[].amount` and its declared `totals.amount`. This function must never
    touch a resource's `monthly_cost_estimate` — that is an estimate, not billed cost.
    """
    by_service, by_provider = [], []

    for bundle in bundles:
        cost = bundle.get("cost")
        provider = bundle["provider"]
        if not isinstance(cost, dict):
            continue

        currency = cost.get("currency")
        grouped: dict = {}
        for index, item in enumerate(cost.get("line_items") or []):
            if not isinstance(item, dict):
                warnings.append(
                    {
                        "provider": provider,
                        "warning": f"cost line item {index} is not an object — ignored",
                    }
                )
                continue
            service = item.get("service") or "Unknown"
            grouped[service] = grouped.get(service, 0.0) + money(item.get("amount"))

        rows = [
            {
                "provider": provider,
                "service": service,
                "amount": round(amount, 2),
                "currency": currency,
            }
            for service, amount in grouped.items()
        ]
        by_service.extend(rows)

        # Summed from the rounded rows the report renders, so the column adds up on paper.
        line_items_sum = round(sum(row["amount"] for row in rows), 2)
        declared = cost.get("totals") or {}
        amount = money(declared.get("amount")) if "amount" in declared else line_items_sum
        reconciled = abs(amount - line_items_sum) <= RECONCILE_TOLERANCE
        if not reconciled:
            warnings.append(
                {
                    "provider": provider,
                    "warning": f"declared period total {amount:.2f} does not match the sum "
                    f"of its service line items {line_items_sum:.2f}",
                }
            )
        by_provider.append(
            {
                "provider": provider,
                "currency": currency,
                "amount": amount,
                "line_items_sum": line_items_sum,
                "reconciled": reconciled,
                "source_granularity": cost.get("source_granularity"),
            }
        )

    by_service.sort(key=lambda row: (-row["amount"], row["provider"], row["service"]))
    by_provider.sort(key=lambda row: row["provider"])

    totals_by_currency: dict = {}
    for row in by_provider:
        key = row["currency"] or "UNKNOWN"
        totals_by_currency[key] = round(totals_by_currency.get(key, 0.0) + row["amount"], 2)

    # No currency conversion at m1 (original currency only), so a grand total across two
    # currencies would be a number with no meaning. Report per-currency and withhold the
    # scalar rather than emitting a well-formed wrong answer.
    if len(totals_by_currency) == 1:
        currency, grand_total = next(iter(totals_by_currency.items()))
    else:
        currency, grand_total = None, None
        if totals_by_currency:
            warnings.append(
                {
                    "warning": "bundles report more than one currency "
                    f"({', '.join(sorted(totals_by_currency))}); no conversion is done at "
                    "m1, so grand_total is null and totals_by_currency carries the figures",
                }
            )

    return {
        "currency": currency,
        "grand_total": grand_total,
        "totals_by_currency": dict(sorted(totals_by_currency.items())),
        "by_provider": by_provider,
        "by_service": by_service,
        "granularity_note": "cost is service-level; per-resource dollars elsewhere in this "
        "report are estimates and are never summed into these totals (D4)",
    }


# ------------------------------------------------------------------------ MoM delta


def month_on_month(current: dict, prior_snapshots: list, period, warnings: list) -> dict:
    """This period's service totals against the prior calendar month's persisted snapshot.

    First run — no prior snapshot on disk — is the normal path, not an error: the section
    reports `no_prior_month` and the run stays clean.
    """
    previous = prior_period(period) if period else None
    usable = [snapshot for snapshot in (prior_snapshots or []) if isinstance(snapshot, dict)]
    if not usable:
        return {
            "status": "no_prior_month",
            "prior_period": previous,
            "reason": "no persisted cost snapshot found for the prior calendar month",
        }

    prior_bundles = [
        {"provider": str(snapshot.get("provider") or "unknown"), "cost": snapshot}
        for snapshot in usable
    ]
    # Composed through the same function as the current period, so both sides of the delta
    # are grouped and reconciled by identical rules. Its warnings are carried, scoped to
    # the prior period rather than swallowed — a prior snapshot that does not reconcile is
    # exactly as worth knowing about as a current one that does not.
    prior_warnings: list = []
    prior = service_totals(prior_bundles, prior_warnings)
    warnings.extend({**entry, "scope": f"prior period {previous}"} for entry in prior_warnings)

    current_services = {(r["provider"], r["service"]): r["amount"] for r in current["by_service"]}
    prior_services = {(r["provider"], r["service"]): r["amount"] for r in prior["by_service"]}

    rows = []
    for key in sorted(set(current_services) | set(prior_services)):
        provider, service = key
        current_amount = current_services.get(key)
        prior_amount = prior_services.get(key)
        change = (
            "new" if prior_amount is None else "removed" if current_amount is None else "changed"
        )
        current_amount = current_amount or 0.0
        prior_amount = prior_amount or 0.0
        delta_amount = round(current_amount - prior_amount, 2)
        if change == "changed" and delta_amount == 0.0:
            change = "unchanged"
        rows.append(
            {
                "provider": provider,
                "service": service,
                "prior_amount": prior_amount,
                "current_amount": current_amount,
                "delta_amount": delta_amount,
                "delta_pct": pct_change(current_amount, prior_amount),
                "change": change,
            }
        )
    rows.sort(key=lambda row: (-abs(row["delta_amount"]), row["provider"], row["service"]))

    current_providers = {row["provider"]: row["amount"] for row in current["by_provider"]}
    prior_providers = {row["provider"]: row["amount"] for row in prior["by_provider"]}
    provider_rows = []
    for provider in sorted(set(current_providers) | set(prior_providers)):
        current_amount = current_providers.get(provider, 0.0)
        prior_amount = prior_providers.get(provider, 0.0)
        provider_rows.append(
            {
                "provider": provider,
                "prior_amount": prior_amount,
                "current_amount": current_amount,
                "delta_amount": round(current_amount - prior_amount, 2),
                "delta_pct": pct_change(current_amount, prior_amount),
            }
        )

    missing = sorted(set(current_providers) - set(prior_providers))
    if missing:
        warnings.append(
            {
                "warning": f"no prior-month snapshot for provider(s) {', '.join(missing)}; "
                "their services are reported as new"
            }
        )

    current_total = round(sum(current_providers.values()), 2)
    prior_total = round(sum(prior_providers.values()), 2)
    return {
        "status": "ok",
        "prior_period": previous,
        "current_period": period,
        "currency": current["currency"],
        "prior_total": prior_total,
        "current_total": current_total,
        "delta_amount": round(current_total - prior_total, 2),
        "delta_pct": pct_change(current_total, prior_total),
        "by_provider": provider_rows,
        "by_service": rows,
        "providers_without_prior_snapshot": missing,
        "providers_only_in_prior": sorted(set(prior_providers) - set(current_providers)),
    }


# ------------------------------------------------- tag coverage + untagged spenders


def coverage_section(bundles: list, top_untagged: int, skipped: list) -> dict:
    """Tag coverage over the union of the inventories, and the costliest untagged resources.

    Coverage is computed once, here, from the inventories themselves — never re-read from
    an orphan file — using the same usable-resource split and the same ratio t2 applies,
    so at N=1 this figure is t2's `tag_coverage` by construction rather than by luck.

    The ranking is the one place a resource-level `monthly_cost_estimate` is read on the
    cost side of the report: it ranks spenders, and never contributes to a cost total (D4).
    """
    everything, untagged, per_provider = [], [], []

    for bundle in bundles:
        inventory = bundle.get("inventory")
        provider = bundle["provider"]
        if not isinstance(inventory, dict):
            continue
        resources, unusable = usable_resources(inventory)
        for entry in unusable:
            skipped.append({"provider": provider, "source": "inventory", **entry})
        everything.extend(resources)
        # BL-127 / C6: a non-`str` tag element is a counted skip, not a silent drop. The
        # sink is this stage's own `skipped`, never `detect_orphans`' — see `tags_of`.
        for resource in resources:
            tag_skips: list = []
            tags_of(resource, tag_skips)
            for entry in tag_skips:
                skipped.append({"provider": provider, "source": "tags", **entry})
        provider_untagged = [r for r in resources if not tags_of(r)]
        untagged.extend((provider, resource) for resource in provider_untagged)
        per_provider.append(
            {
                "provider": provider,
                "resources": len(resources),
                "tagged": len(resources) - len(provider_untagged),
                "untagged": len(provider_untagged),
                "coverage": tag_coverage(resources),
            }
        )

    per_provider.sort(key=lambda row: row["provider"])
    untagged.sort(
        key=lambda pair: (
            -money(pair[1].get("monthly_cost_estimate")),
            pair[0],
            str(pair[1].get("resource_id")),
        )
    )

    top = [
        {
            "provider": provider,
            "resource_id": resource.get("resource_id"),
            "type": resource.get("type"),
            "name": resource.get("name"),
            "region": resource.get("region"),
            "size": resource.get("size"),
            "monthly_cost_estimate": money(resource.get("monthly_cost_estimate")),
            "raw_ref": resource.get("raw_ref"),
            # BL-101: the rows the report already renders now show their tags.
            "tags": tags_of(resource),
        }
        for provider, resource in untagged[:top_untagged]
    ]

    # BL-101: every distinct tag in use, what carries it, and what that costs. Ranked by
    # cost like the spenders table, and capped by the same `top_k` — a long tail of
    # one-off tags is the expected shape.
    by_tag: dict = {}
    for resource in everything:
        for tag in tags_of(resource):
            row = by_tag.setdefault(tag, {"tag": tag, "resources": 0, "monthly_cost_estimate": 0.0})
            row["resources"] += 1
            row["monthly_cost_estimate"] += money(resource.get("monthly_cost_estimate"))
    tags_in_use = sorted(
        ({**row, "monthly_cost_estimate": round(row["monthly_cost_estimate"], 2)}
         for row in by_tag.values()),
        key=lambda row: (-row["monthly_cost_estimate"], row["tag"]),
    )

    tagged = len(everything) - len(untagged)
    return {
        "coverage": tag_coverage(everything),
        "resources": len(everything),
        "tagged": tagged,
        "untagged": len(untagged),
        "by_provider": per_provider,
        "top_untagged_spenders": top,
        "top_k": top_untagged,
        # BL-121 / C11: caps report their truncation. `top_k` alone says what was asked
        # for, never what was withheld — and a table that silently ends reads as the whole
        # set. Zero is emitted explicitly rather than omitted, so "nothing was dropped" and
        # "nobody counted" are different renderings (absent-is-unknown).
        "untagged_not_shown": max(0, len(untagged) - len(top)),
        "tags_in_use": tags_in_use[:top_untagged],
        "tags_in_use_total": len(tags_in_use),
        "tags_not_shown": max(0, len(tags_in_use) - len(tags_in_use[:top_untagged])),
        "untagged_monthly_cost_estimate": round(
            sum(money(resource.get("monthly_cost_estimate")) for _, resource in untagged), 2
        ),
        "estimate_note": "monthly_cost_estimate is a per-resource estimate used for ranking "
        "only; it is not billed cost and is not part of any cost total (D4)",
    }


# --------------------------------------------------------------------- orphan section


def band_of(confidence: float) -> str:
    if confidence >= BAND_HIGH_MIN:
        return "HIGH"
    if confidence >= BAND_MEDIUM_MIN:
        return "MEDIUM"
    return "LOW"


def orphan_section(bundles: list, warnings: list, skipped: list) -> dict:
    """t2's candidates, grouped into confidence bands and otherwise untouched.

    Each candidate is carried through exactly as t2 emitted it — `evidence[]`,
    `base_confidence`, `modifiers[]` and `monthly_saving_estimate` intact — with one key
    added, `provider`, because at N>1 the candidate itself carries no provenance and the
    band it lands in is shared across providers.
    """
    grouped: dict = {band["band"]: [] for band in BANDS}
    evaluated: list = []
    reported: list = []
    total = 0

    for bundle in bundles:
        orphans = bundle.get("orphans")
        provider = bundle["provider"]
        if not isinstance(orphans, dict):
            continue
        # `reported` is a dict keyed by RULE NAME, and this consumer handles exactly one:
        # `untagged_in_tagged_account`, the only reported-only rule the catalog has today.
        # **One rule today is an observation, not a census** (BL-074's own lesson). A second
        # reported-only rule would be emitted by `detect_orphans`, ignored here, and absent
        # from the report — silently, which is precisely the defect BL-101 exists to fix,
        # reproduced one rule along. Recorded rather than filed: by m4 t4c's membership rule
        # a defect latent on a hypothetical and exhibited by nothing gets a note, not a row
        # (the same test that excluded D15, D17 and P4). Iterating the block generically is a
        # design change; if a second reported-only rule is ever added, it belongs with it.
        block = orphans.get("reported")
        governance = block.get("untagged_in_tagged_account") if isinstance(block, dict) else None
        if isinstance(governance, dict):
            reported.append(
                {
                    "provider": provider,
                    "rule": "untagged_in_tagged_account",
                    "account_uses_tags": governance.get("account_uses_tags"),
                    "tag_coverage": governance.get("tag_coverage"),
                    "coverage_threshold": governance.get("coverage_threshold"),
                    "resources": [
                        r for r in (governance.get("resources") or []) if isinstance(r, dict)
                    ],
                }
            )
        evaluated.append(
            {
                "provider": provider,
                "reference_date": orphans.get("reference_date"),
                "inventory_generated_at": orphans.get("inventory_generated_at"),
            }
        )
        for index, candidate in enumerate(orphans.get("candidates") or []):
            if not isinstance(candidate, dict) or not isinstance(
                candidate.get("confidence"), (int, float)
            ):
                skipped.append(
                    {
                        "provider": provider,
                        "source": "orphans",
                        "index": index,
                        "reason": "orphan candidate has no numeric confidence — it cannot "
                        "be banded",
                    }
                )
                continue
            total += 1
            grouped[band_of(candidate["confidence"])].append({"provider": provider, **candidate})

    by_band = []
    for band in BANDS:
        entries = grouped[band["band"]]
        entries.sort(key=lambda c: (-c["confidence"], c["provider"], str(c.get("resource_id"))))
        by_band.append(
            {
                **band,
                "count": len(entries),
                "monthly_saving_estimate": round(
                    sum(money(c.get("monthly_saving_estimate")) for c in entries), 2
                ),
                "candidates": entries,
            }
        )

    return {
        "bands": list(BANDS),
        "by_band": by_band,
        "evaluated_as_of": sorted(evaluated, key=lambda row: row["provider"]),
        # BL-101: t2's governance rule fires in the pipeline and has been invisible in the
        # report since m1 — `orphan_section` carried `candidates` only, so `report_data`
        # had no key for it and the template could not render it. Carried through intact,
        # evidence included, and kept OUT of `by_band`: a reported-only entry has no
        # confidence and no saving estimate, and must never be bandable (§t2).
        "reported": reported,
        "totals": {
            "candidates": total,
            "monthly_saving_estimate": round(
                sum(band["monthly_saving_estimate"] for band in by_band), 2
            ),
        },
    }


# ------------------------------------------------------------------- region coverage

#: The single provider-payload key this stage reads (m2 A4, adjudicated at t3).
#:
#: That payload block is opaque by contract — compose must never iterate it, copy it
#: through, or key on it generically — so the lift is written as one *named* constant and
#: every other key in the block stays invisible to the report. The distinction is the whole
#: point of A4: a generic pass-through would put provider-shaped data into shared machinery,
#: which is the leak this milestone exists to prove does not happen.
SWEPT_REGIONS_KEY = "swept_regions"


def region_coverage_section(bundles: list) -> list:
    """Per-provider swept-region coverage, lifted from each cost snapshot's one named key.

    Decision D's no-silent-caps clause: a provider that enumerates the regions it swept says
    so in the report, so a sweep narrowed by an override or by a failed region enumeration is
    visible rather than quietly shrinking the inventory behind an unchanged-looking report.

    Nothing is derived. The list is the adapter's own, in the adapter's own order — it
    already sorts and dedupes, and re-sorting here would be this stage inventing a figure.
    `count` is taken once so the template does not have to compute it (t4 render contract:
    the template computes nothing).

    A provider whose snapshot carries no swept set contributes no entry, which is what keeps
    a single-region provider's report identical to the one it produced before this field
    existed. A provider that swept *nothing* contributes an entry saying zero — the honest
    report of a broken sweep, and not the same thing as not sweeping.
    """
    entries = []
    for bundle in bundles:
        cost = bundle.get("cost")
        extra = cost.get("provider_extra") if isinstance(cost, dict) else None
        regions = extra.get(SWEPT_REGIONS_KEY) if isinstance(extra, dict) else None
        if not isinstance(regions, list):
            continue
        entries.append(
            {
                "provider": bundle["provider"],
                # str() rather than a type filter: a malformed element is *shown*, never
                # dropped. A silently shorter region list is exactly the silent cap
                # decision D forbids.
                "swept": [str(region) for region in regions],
                "count": len(regions),
            }
        )
    return entries


# --------------------------------------------------------------------------- compose


def compose(
    bundles: list,
    prior_snapshots: list | None = None,
    period: str | None = None,
    top_untagged: int = DEFAULT_TOP_UNTAGGED,
    skipped: list | None = None,
) -> dict:
    """Merge N provider bundles into the report-data payload.

    `bundles` is a list of `{"cost": …, "inventory": …, "orphans": …}` dicts — each value a
    parsed document or None. `prior_snapshots` is the prior calendar month's persisted cost
    snapshots (empty or None on a first run). `skipped` carries the reader's own file-level
    failures so they land in the payload beside the ones found here.

    Pure: no clock, no filesystem, no environment. Same inputs, byte-identical payload.
    """
    warnings: list = []
    skipped = list(skipped or [])

    bundles = [{**bundle, "provider": provider_of(bundle)} for bundle in bundles]
    bundles.sort(key=lambda bundle: bundle["provider"])
    period = period or period_of(bundles)

    for bundle in bundles:
        for key, label in (("cost", "cost snapshot"), ("inventory", "inventory"), ("orphans", "orphan candidates")):
            if not isinstance(bundle.get(key), dict):
                warnings.append(
                    {
                        "provider": bundle["provider"],
                        "warning": f"no usable {label} for this provider — the sections it "
                        f"feeds are composed without it",
                    }
                )
        for key in ("cost", "inventory", "orphans"):
            document = bundle.get(key)
            if isinstance(document, dict) and document.get("period") not in (None, period):
                warnings.append(
                    {
                        "provider": bundle["provider"],
                        "warning": f"{key} document is for period {document['period']}, not "
                        f"{period}",
                    }
                )

    costs = service_totals(bundles, warnings)
    delta = month_on_month(costs, prior_snapshots, period, warnings)
    coverage = coverage_section(bundles, top_untagged, skipped)
    orphans = orphan_section(bundles, warnings, skipped)
    regions = region_coverage_section(bundles)

    stamps = []
    for bundle in bundles:
        for key in ("cost", "inventory"):
            document = bundle.get(key)
            if isinstance(document, dict):
                stamps.append(document.get("generated_at"))

    return {
        "period": period,
        # Stamped from the inputs, not from a clock: the report is as fresh as the newest
        # fetch it was built from, and re-composing the same files never moves it.
        "as_of": newest_timestamp(stamps),
        "providers": [bundle["provider"] for bundle in bundles],
        "accounts": [
            {
                "provider": bundle["provider"],
                "account": next(
                    (
                        document.get("account")
                        for document in (bundle.get("cost"), bundle.get("inventory"))
                        if isinstance(document, dict) and document.get("account")
                    ),
                    None,
                ),
            }
            for bundle in bundles
        ],
        "cost_summary": costs,
        "mom_delta": delta,
        "tag_coverage": coverage,
        "orphans": orphans,
        # m2 A4 (t3): a *named* first-class field, never a generic copy of the provider
        # payload block. Empty for every provider that does not sweep regions, which is what
        # keeps the DigitalOcean report byte-identical to the one this milestone started
        # from — the field is additive, not a new required section.
        "region_coverage": regions,
        "totals": {
            "providers": len(bundles),
            "services": len(costs["by_service"]),
            "cost_grand_total": costs["grand_total"],
            "currency": costs["currency"],
            "resources": coverage["resources"],
            "tag_coverage": coverage["coverage"],
            "untagged_resources": coverage["untagged"],
            "orphan_candidates": orphans["totals"]["candidates"],
            "orphan_monthly_saving_estimate": orphans["totals"]["monthly_saving_estimate"],
        },
        "warnings": warnings,
        "skipped": skipped,
    }


# ------------------------------------------------------------------------------- I/O


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
    return path


def read_document(path, kind: str, skipped: list):
    """Read one input file. An unreadable or malformed file degrades to a skipped entry —
    the stage composes what it has rather than breaking its stdout contract."""
    if path is None:
        return None
    try:
        document = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        skipped.append({"source": kind, "path": str(path), "reason": str(exc)})
        return None
    if not isinstance(document, dict):
        skipped.append(
            {"source": kind, "path": str(path), "reason": "document root is not a JSON object"}
        )
        return None
    return document


def classify(document: dict):
    """Which normalized artifact a parsed document is, by shape rather than by filename —
    so a directory holding several providers' files groups correctly whatever they are
    called."""
    if isinstance(document.get("line_items"), list):
        return "cost"
    if isinstance(document.get("candidates"), list):
        return "orphans"
    if isinstance(document.get("resources"), list):
        return "inventory"
    return None


def discover_bundles(input_dir: Path, period, skipped: list, warnings: list) -> tuple:
    """Group every normalized artifact in `input_dir` into per-provider bundles."""
    grouped: dict = {}
    for path in sorted(input_dir.glob("*.json")):
        try:
            document = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            skipped.append({"source": "input-dir", "path": str(path), "reason": str(exc)})
            continue
        if not isinstance(document, dict):
            continue
        kind = classify(document)
        if kind is None:
            continue
        if period is not None and document.get("period") not in (None, period):
            continue
        provider = str(document.get("provider") or "unknown")
        bundle = grouped.setdefault(provider, {"cost": None, "inventory": None, "orphans": None})
        if bundle[kind] is not None:
            warnings.append(
                {
                    "provider": provider,
                    "warning": f"more than one {kind} document for this provider in "
                    f"{input_dir}; {path.name} ignored",
                }
            )
            continue
        bundle[kind] = document
    return [grouped[provider] for provider in sorted(grouped)]


def persist_history(bundles: list, history_dir: Path, period: str) -> list:
    """Persist each provider's cost snapshot into `history/{period}/` for next month.

    Idempotent by (provider, period): the filename is derived from both, so re-running a
    period overwrites its snapshot and never appends a second one.
    """
    written = []
    if prior_period(period) is None:
        # Not a calendar period: there is no month for next month's delta to look up, so
        # writing a `history/unknown/` tree would only leave a snapshot nothing can read.
        return written
    for bundle in bundles:
        cost = bundle.get("cost")
        if not isinstance(cost, dict):
            continue
        path = history_dir / period / f"{provider_slug(bundle['provider'])}_costs_{period}.json"
        written.append(str(write_json(path, cost)))
    return sorted(written)


def load_prior_snapshots(history_dir: Path, period, skipped: list) -> tuple:
    """Read the prior calendar month's persisted cost snapshots.

    An absent directory is the first-run path and is silent — not a warning, not an error.
    """
    previous = prior_period(period) if period else None
    if previous is None:
        return [], None
    directory = history_dir / previous
    if not directory.is_dir():
        return [], previous
    snapshots = []
    for path in sorted(directory.glob("*.json")):
        document = read_document(path, "history", skipped)
        if isinstance(document, dict) and classify(document) == "cost":
            snapshots.append(document)
    return snapshots, previous


# ------------------------------------------------------------------------------ main


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Merge N providers' cost + inventory + orphan bundles into report data"
    )
    parser.add_argument(
        "--cost", action="append", default=[], help="normalized cost snapshot (repeatable)"
    )
    parser.add_argument(
        "--inventory", action="append", default=[], help="normalized inventory (repeatable)"
    )
    parser.add_argument(
        "--orphans", action="append", default=[], help="orphan candidates (repeatable)"
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="group every normalized artifact in this directory into per-provider bundles",
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument(
        "--history-dir",
        default=str(DEFAULT_HISTORY_DIR),
        help=f"persisted monthly cost snapshots (default: {DEFAULT_HISTORY_DIR})",
    )
    parser.add_argument("--period", default=None, help="YYYY-MM (default: from the inputs)")
    parser.add_argument("--top-untagged", type=int, default=DEFAULT_TOP_UNTAGGED)
    return parser.parse_args(argv)


def bundles_from_args(args, skipped: list, warnings: list):
    """Build the bundle list from either the repeatable triples or --input-dir."""
    if args.input_dir:
        if args.cost or args.inventory or args.orphans:
            raise ValueError("--input-dir cannot be combined with --cost/--inventory/--orphans")
        directory = Path(args.input_dir)
        if not directory.is_dir():
            raise ValueError(f"--input-dir {args.input_dir} is not a directory")
        return discover_bundles(directory, args.period, skipped, warnings)

    lengths = {
        "--cost": len(args.cost),
        "--inventory": len(args.inventory),
        "--orphans": len(args.orphans),
    }
    given = {flag: count for flag, count in lengths.items() if count}
    if not given:
        raise ValueError("pass --input-dir, or at least one --cost/--inventory/--orphans triple")
    if len(set(given.values())) > 1:
        # Bundles are paired by position, so mismatched counts would silently misattribute
        # one provider's inventory to another's costs. An absent file is expressed by
        # passing its path anyway (it degrades to a skipped entry).
        raise ValueError(
            "--cost/--inventory/--orphans must be repeated the same number of times "
            f"(got {given}); pass the path of a missing file anyway rather than omitting one"
        )

    size = max(given.values())
    return [
        {
            "cost": read_document(args.cost[i] if i < len(args.cost) else None, "cost", skipped),
            "inventory": read_document(
                args.inventory[i] if i < len(args.inventory) else None, "inventory", skipped
            ),
            "orphans": read_document(
                args.orphans[i] if i < len(args.orphans) else None, "orphans", skipped
            ),
        }
        for i in range(size)
    ]


def main(argv=None) -> int:
    args = parse_args(argv)
    skipped: list = []
    warnings: list = []

    try:
        bundles = bundles_from_args(args, skipped, warnings)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    period = args.period or period_of(
        [{**bundle, "provider": provider_of(bundle)} for bundle in bundles]
    )
    history_dir = Path(args.history_dir)
    prior_snapshots, previous = load_prior_snapshots(history_dir, period, skipped)

    report = compose(
        bundles,
        prior_snapshots=prior_snapshots,
        period=period,
        top_untagged=args.top_untagged,
        skipped=skipped,
    )
    report["warnings"].extend(warnings)

    period = report["period"] or "unknown"
    path = write_json(Path(args.output_dir) / f"report_data_{period}.json", report)
    history = persist_history(
        [{**bundle, "provider": provider_of(bundle)} for bundle in bundles], history_dir, period
    )

    degraded = bool(report["warnings"] or report["skipped"])
    summary = {
        "status": "partial" if degraded else "ok",
        "period": period,
        "as_of": report["as_of"],
        "file": str(path),
        "history": {"dir": str(history_dir), "prior_period": previous, "written": history},
        "counts": {
            "providers": report["totals"]["providers"],
            "services": report["totals"]["services"],
            "resources": report["totals"]["resources"],
            "untagged_resources": report["totals"]["untagged_resources"],
            "orphan_candidates": report["totals"]["orphan_candidates"],
            "prior_snapshots": len(prior_snapshots),
            "skipped": len(report["skipped"]),
        },
        "totals": report["totals"],
        "mom_delta": {
            "status": report["mom_delta"]["status"],
            "prior_period": report["mom_delta"].get("prior_period"),
            "delta_amount": report["mom_delta"].get("delta_amount"),
            "delta_pct": report["mom_delta"].get("delta_pct"),
        },
        "warnings": report["warnings"],
        "skipped": report["skipped"],
    }
    print(json.dumps(summary, indent=2))
    return 1 if degraded else 0


if __name__ == "__main__":
    sys.exit(main())
