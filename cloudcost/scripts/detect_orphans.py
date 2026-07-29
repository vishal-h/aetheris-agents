#!/usr/bin/env python3
"""Deterministic orphan detection over a normalized cloudcost inventory (m1, t2).

Reads a normalized resource inventory (`cloudcost/milestone.md` §Normalized schemas) and
applies the §t2 heuristic catalog, emitting orphan candidates with a confidence, the
`evidence[]` facts that fired, and a `monthly_saving_estimate`:

    {output_dir}/orphan_candidates_{YYYY-MM}.json

Provider-agnostic by construction. Every rule keys on normalized fields only — `state`,
`type`, `attached_to`, `created_at`, `last_activity_at`, `tags`, `name`,
`monthly_cost_estimate` — so a second provider needs a new adapter and nothing here. The
single exception is `STOPPED_STATES`, the one place a provider's own state vocabulary is
read; see its comment.

No LLM is involved anywhere in detection: rules, modifiers and thresholds are all
reviewable code (D3). There is no hardcoded "now" — the analysis is stamped with an
explicit reference date, so age rules are deterministic and testable.

Usage:
    python3 scripts/detect_orphans.py output/do_inventory_2026-07.json \\
        [--output-dir output] [--reference-date YYYY-MM-DD] [--snapshot-age-days 30]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from _normalized import day, iso, money, parse_timestamp, tag_coverage, tags_of, usable_resources

# --------------------------------------------------------------------------- thresholds

#: Base confidences for the §t2 rule catalog.
CONFIDENCE_UNATTACHED_VOLUME = 0.9
CONFIDENCE_UNASSOCIATED_RESERVED_IP = 0.95
CONFIDENCE_AGED_SNAPSHOT = 0.7
CONFIDENCE_IDLE_LOAD_BALANCER = 0.85
CONFIDENCE_STOPPED_DROPLET_WITH_STORAGE = 0.6

#: Age thresholds, in days. A rule fires on age *strictly greater* than its threshold.
UNATTACHED_VOLUME_MIN_AGE_DAYS = 14
STOPPED_DROPLET_MIN_AGE_DAYS = 30
DEFAULT_SNAPSHOT_AGE_DAYS = 30  # overridable: --snapshot-age-days N

#: Additive modifiers; the final confidence is clamped to [0.0, 1.0].
MODIFIER_RECENT_ACTIVITY = -0.2
MODIFIER_EPHEMERAL_NAME = 0.1

#: `last_activity_at` at most this many days before the reference date counts as recent.
#: A no-op for DigitalOcean, which exposes no such field (every resource emits null) —
#: that is the correct outcome, not a gap to paper over with `created_at`.
RECENT_ACTIVITY_WINDOW_DAYS = 14

#: §t2 Scope's literal pattern. Matched case-sensitively, as written.
EPHEMERAL_NAME_PATTERN = re.compile(r"^(tmp-|ci-|test-)")

#: A resource carrying this tag is dropped outright, before any scoring.
KEEP_TAG = "keep=true"

#: The account is "using tags" when coverage is strictly above this fraction. Above it, a
#: resource with no tags is a governance flag — reported, never queued (§t2).
TAGGED_ACCOUNT_COVERAGE_THRESHOLD = 0.5

#: The one place a provider's own state vocabulary is read. Normalize to a common state
#: enum in the adapter before the second provider lands (forward ticket).
STOPPED_STATES = {"off"}  # DO vocabulary


# ------------------------------------------------------------------------------ helpers
#
# `parse_timestamp`, `iso`, `day`, `money`, `tags_of`, `usable_resources` and
# `tag_coverage` are imported from `_normalized` — they are vocabulary of the normalized
# schema shared with t3's `compose_report_data.py`, not of this stage. In particular the
# coverage figure this module reports and the one the report renders are required to be
# the same number, so there is one definition of it.


def has_keep_tag(resource: dict) -> bool:
    return any(tag.strip().lower() == KEEP_TAG for tag in tags_of(resource))


class Context:
    """Everything a rule needs beyond the resource itself: the reference date, the tunable
    thresholds, and the intra-inventory join of volumes onto what they are attached to."""

    def __init__(self, reference_date: datetime, snapshot_age_days: int, resources: list):
        self.reference_date = reference_date
        self.snapshot_age_days = snapshot_age_days
        self.volumes_by_attachment: dict = {}
        for resource in resources:
            if resource.get("type") != "volume":
                continue
            attached_to = resource.get("attached_to")
            if isinstance(attached_to, str) and attached_to:
                self.volumes_by_attachment.setdefault(attached_to, []).append(resource)

    def age_days(self, timestamp_value):
        """Age of `timestamp_value` at the reference date, in days; None if unparseable."""
        moment = parse_timestamp(timestamp_value)
        if moment is None:
            return None
        return (self.reference_date - moment).total_seconds() / 86400.0

    def age_phrase(self, label: str, created_at, age: float, threshold=None) -> str:
        created = parse_timestamp(created_at)
        text = (
            f"{label} {int(age)}d "
            f"(created {day(created)}, ref {day(self.reference_date)})"
        )
        if threshold is not None:
            text += f"; threshold >{threshold}d"
        return text


def fired(rule: str, confidence: float, evidence: list) -> dict:
    return {"rule": rule, "base_confidence": confidence, "evidence": evidence}


# -------------------------------------------------------------------------------- rules
#
# Each rule takes (resource, ctx) and returns a `fired(...)` dict or None. Rules read the
# normalized schema only. In the m1 catalog the rules are type-disjoint, so at most one
# fires per resource; the engine is written to emit one candidate per firing regardless.


def rule_unattached_volume(resource: dict, ctx: Context):
    """Unattached volume older than 14 days — 0.9."""
    if resource.get("type") != "volume" or resource.get("attached_to") is not None:
        return None
    age = ctx.age_days(resource.get("created_at"))
    if age is None or age <= UNATTACHED_VOLUME_MIN_AGE_DAYS:
        return None
    return fired(
        "unattached_volume",
        CONFIDENCE_UNATTACHED_VOLUME,
        [
            "attached_to is null — the volume is not attached to any instance",
            ctx.age_phrase(
                "unattached for",
                resource.get("created_at"),
                age,
                UNATTACHED_VOLUME_MIN_AGE_DAYS,
            ),
        ],
    )


def rule_unassociated_reserved_ip(resource: dict, ctx: Context):
    """Reserved IP associated with nothing — 0.95. No age threshold: an unassociated
    reserved IP bills from the moment it is unassociated."""
    if resource.get("type") != "reserved_ip" or resource.get("attached_to") is not None:
        return None
    evidence = ["attached_to is null — the reserved IP is not associated with any instance"]
    age = ctx.age_days(resource.get("created_at"))
    if age is not None:
        evidence.append(
            ctx.age_phrase("reserved for", resource.get("created_at"), age)
            + "; this rule has no age threshold"
        )
    return fired("unassociated_reserved_ip", CONFIDENCE_UNASSOCIATED_RESERVED_IP, evidence)


def rule_aged_snapshot(resource: dict, ctx: Context):
    """Snapshot older than N days (N is a parameter, default 30) — 0.7."""
    if resource.get("type") != "snapshot":
        return None
    age = ctx.age_days(resource.get("created_at"))
    if age is None or age <= ctx.snapshot_age_days:
        return None
    evidence = [
        ctx.age_phrase(
            "snapshot age", resource.get("created_at"), age, ctx.snapshot_age_days
        )
    ]
    if resource.get("attached_to") is None:
        evidence.append(
            "attached_to is null — the source the snapshot was taken from is gone"
        )
    return fired("aged_snapshot", CONFIDENCE_AGED_SNAPSHOT, evidence)


def rule_idle_load_balancer(resource: dict, ctx: Context):
    """Load balancer with zero backends — 0.85.

    A tag-targeted load balancer carries `attached_to == "tag:<name>"` and is in service,
    so it never reaches this rule (milestone B2 / t1's normalizer). Known limitation, not
    built at m1: a backend *tag* matching zero live instances is idle too, but proving it
    needs an instance cross-reference the inventory alone does not support.
    """
    if resource.get("type") != "load_balancer" or resource.get("attached_to") is not None:
        return None
    return fired(
        "idle_load_balancer",
        CONFIDENCE_IDLE_LOAD_BALANCER,
        [
            "attached_to is null — no backend instances and no backend tag",
            "a tag-targeted load balancer would carry attached_to = 'tag:<name>' and is "
            "excluded from this rule",
        ],
    )


def rule_stopped_droplet_with_attached_storage(resource: dict, ctx: Context):
    """Stopped instance older than 30 days that still carries attached storage — 0.6.

    "Attached storage" is an intra-inventory join: at least one volume whose `attached_to`
    equals this resource's `resource_id`. The saving stays the instance's own estimate for
    m1 — the attached volumes are named in the evidence with their cost, but summing them
    into the saving is forwarded (a stopped instance's volumes may be intentionally kept).
    """
    if resource.get("type") != "droplet":
        return None
    if resource.get("state") not in STOPPED_STATES:
        return None
    age = ctx.age_days(resource.get("created_at"))
    if age is None or age <= STOPPED_DROPLET_MIN_AGE_DAYS:
        return None
    attached = ctx.volumes_by_attachment.get(resource.get("resource_id")) or []
    if not attached:
        return None

    evidence = [
        f"state is '{resource.get('state')}' — the instance is stopped",
        ctx.age_phrase(
            "stopped instance age",
            resource.get("created_at"),
            age,
            STOPPED_DROPLET_MIN_AGE_DAYS,
        ),
    ]
    for volume in sorted(attached, key=lambda v: str(v.get("resource_id"))):
        evidence.append(
            f"attached storage {volume.get('resource_id')} "
            f"({volume.get('name')}, {volume.get('size')}) — "
            f"${money(volume.get('monthly_cost_estimate')):.2f}/mo"
        )
    evidence.append(
        "saving estimate is the instance's own monthly_cost_estimate; attached storage "
        "is named but not summed (m1)"
    )
    return fired(
        "stopped_droplet_with_attached_storage",
        CONFIDENCE_STOPPED_DROPLET_WITH_STORAGE,
        evidence,
    )


#: Evaluated in order; each may contribute one candidate.
RULES = (
    rule_unattached_volume,
    rule_unassociated_reserved_ip,
    rule_aged_snapshot,
    rule_idle_load_balancer,
    rule_stopped_droplet_with_attached_storage,
)


# ---------------------------------------------------------------------------- modifiers


def modifier_recent_activity(resource: dict, ctx: Context):
    """Recent activity lowers confidence by 0.2.

    Keyed on `last_activity_at` and nothing else. DigitalOcean emits null for every
    resource type, so this is a deliberate no-op there — substituting `created_at` would
    invent a signal the schema does not carry.
    """
    age = ctx.age_days(resource.get("last_activity_at"))
    if age is None or age > RECENT_ACTIVITY_WINDOW_DAYS:
        return None
    seen = parse_timestamp(resource.get("last_activity_at"))
    return {
        "modifier": "recent_activity",
        "delta": MODIFIER_RECENT_ACTIVITY,
        "evidence": (
            f"last_activity_at {day(seen)} is {int(abs(age))}d from ref "
            f"{day(ctx.reference_date)}, inside the {RECENT_ACTIVITY_WINDOW_DAYS}d "
            f"window: {MODIFIER_RECENT_ACTIVITY:+.1f}"
        ),
    }


def modifier_ephemeral_name(resource: dict, ctx: Context):
    """An ephemeral naming convention raises confidence by 0.1."""
    name = resource.get("name")
    if not isinstance(name, str):
        return None
    match = EPHEMERAL_NAME_PATTERN.match(name)
    if not match:
        return None
    return {
        "modifier": "ephemeral_name",
        "delta": MODIFIER_EPHEMERAL_NAME,
        "evidence": (
            f"name '{name}' matches ephemeral pattern "
            f"{EPHEMERAL_NAME_PATTERN.pattern} ('{match.group(1)}'): "
            f"{MODIFIER_EPHEMERAL_NAME:+.1f}"
        ),
    }


MODIFIERS = (modifier_recent_activity, modifier_ephemeral_name)


def clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


# ------------------------------------------------------------------------------- engine


def identity(resource: dict) -> dict:
    """The human-facing identity carried onto a candidate so the report is reviewable
    without opening the provider console (the §Normalized schemas rationale for `name`)."""
    return {
        "resource_id": resource.get("resource_id"),
        "type": resource.get("type"),
        "name": resource.get("name"),
        "region": resource.get("region"),
        "raw_ref": resource.get("raw_ref"),
    }


def timestamp_warnings(resources: list) -> list:
    """Surface unparseable timestamps rather than letting them silently suppress a rule."""
    warnings = []
    for resource in resources:
        for field in ("created_at", "last_activity_at"):
            value = resource.get(field)
            if value is not None and parse_timestamp(value) is None:
                warnings.append(
                    {
                        "resource_id": resource.get("resource_id"),
                        "warning": f"unparseable {field}: {value!r} — age rules cannot "
                        f"evaluate this resource",
                    }
                )
    return warnings


def score(resource: dict, hit: dict, ctx: Context) -> dict:
    """Apply the modifiers to a fired rule and build the candidate record."""
    evidence = list(hit["evidence"])
    modifiers = []
    confidence = hit["base_confidence"]
    for apply_modifier in MODIFIERS:
        applied = apply_modifier(resource, ctx)
        if applied is None:
            continue
        confidence += applied["delta"]
        modifiers.append({"modifier": applied["modifier"], "delta": applied["delta"]})
        evidence.append(applied["evidence"])
    return {
        **identity(resource),
        "rule": hit["rule"],
        "base_confidence": hit["base_confidence"],
        "modifiers": modifiers,
        "confidence": clamp(confidence),
        "evidence": evidence,
        "monthly_saving_estimate": money(resource.get("monthly_cost_estimate")),
    }


def detect(
    inventory: dict,
    reference_date: datetime,
    snapshot_age_days: int = DEFAULT_SNAPSHOT_AGE_DAYS,
) -> dict:
    """Apply the rule catalog to a normalized inventory.

    Pure and deterministic: the same (inventory, reference_date, snapshot_age_days)
    always produces a byte-identical result. No wall clock is read.
    """
    resources, skipped = usable_resources(inventory)
    ctx = Context(reference_date, snapshot_age_days, resources)

    candidates, excluded = [], []
    for resource in resources:
        if has_keep_tag(resource):
            # Excluded outright, before scoring — never a candidate, whatever fired.
            excluded.append({**identity(resource), "reason": f"carries the '{KEEP_TAG}' tag"})
            continue
        for rule in RULES:
            hit = rule(resource, ctx)
            if hit is not None:
                candidates.append(score(resource, hit, ctx))

    candidates.sort(key=lambda c: (-c["confidence"], str(c["resource_id"])))

    coverage = tag_coverage(resources)
    account_uses_tags = coverage > TAGGED_ACCOUNT_COVERAGE_THRESHOLD
    untagged = []
    if account_uses_tags:
        for resource in sorted(resources, key=lambda r: str(r.get("resource_id"))):
            if tags_of(resource):
                continue
            untagged.append(
                {
                    **identity(resource),
                    "rule": "untagged_in_tagged_account",
                    "evidence": [
                        "tags is empty",
                        f"account tag coverage is {coverage:.0%} of "
                        f"{len(resources)} resources, above the "
                        f"{TAGGED_ACCOUNT_COVERAGE_THRESHOLD:.0%} threshold — the account "
                        f"is using tags",
                    ],
                    "monthly_cost_estimate": money(resource.get("monthly_cost_estimate")),
                }
            )

    return {
        "provider": inventory.get("provider"),
        "account": inventory.get("account"),
        "period": inventory.get("period"),
        "reference_date": iso(reference_date),
        "inventory_generated_at": inventory.get("generated_at"),
        "parameters": {
            "snapshot_age_days": snapshot_age_days,
            "unattached_volume_min_age_days": UNATTACHED_VOLUME_MIN_AGE_DAYS,
            "stopped_droplet_min_age_days": STOPPED_DROPLET_MIN_AGE_DAYS,
            "recent_activity_window_days": RECENT_ACTIVITY_WINDOW_DAYS,
            "tagged_account_coverage_threshold": TAGGED_ACCOUNT_COVERAGE_THRESHOLD,
        },
        "candidates": candidates,
        # Governance flags. Structurally not candidates: no `confidence`, no
        # `monthly_saving_estimate` — a reported-only rule can never be queued (§t2).
        "reported": {
            "untagged_in_tagged_account": {
                "account_uses_tags": account_uses_tags,
                "tag_coverage": coverage,
                "coverage_threshold": TAGGED_ACCOUNT_COVERAGE_THRESHOLD,
                "resources": untagged,
            }
        },
        "excluded": excluded,
        "warnings": timestamp_warnings(resources),
        "skipped": skipped,
        "totals": {
            "resources": len(resources),
            "candidates": len(candidates),
            "monthly_saving_estimate": round(
                sum(c["monthly_saving_estimate"] for c in candidates), 2
            ),
            "reported": len(untagged),
        },
    }


# --------------------------------------------------------------------------------- main


def resolve_reference_date(value, inventory: dict) -> datetime:
    """Explicit `--reference-date` wins; otherwise the inventory's own `generated_at`.

    Falling back to the fetch timestamp keeps a plain `detect_orphans.py inventory.json`
    reproducible — the same file always yields the same answer. The wall clock is only
    reached for an inventory that carries no usable `generated_at`.
    """
    if value:
        parsed = parse_timestamp(value)
        if parsed is None:
            raise ValueError(f"--reference-date is not an ISO-8601 date/timestamp: {value!r}")
        return parsed
    parsed = parse_timestamp(inventory.get("generated_at"))
    if parsed is not None:
        return parsed
    return datetime.now(timezone.utc)


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Deterministic orphan detection over a normalized cloudcost inventory"
    )
    parser.add_argument("inventory", help="normalized inventory JSON (from an adapter)")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument(
        "--reference-date",
        default=None,
        help="YYYY-MM-DD or ISO-8601 timestamp; age rules are evaluated against this "
        "(default: the inventory's generated_at)",
    )
    parser.add_argument(
        "--snapshot-age-days",
        type=int,
        default=DEFAULT_SNAPSHOT_AGE_DAYS,
        help=f"snapshot orphan threshold N in days (default: {DEFAULT_SNAPSHOT_AGE_DAYS})",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    try:
        inventory = json.loads(Path(args.inventory).read_text())
        if not isinstance(inventory, dict):
            raise ValueError("inventory root is not a JSON object")
        reference_date = resolve_reference_date(args.reference_date, inventory)
    except (OSError, ValueError) as exc:
        message = f"cannot read inventory {args.inventory}: {exc}"
        print(message, file=sys.stderr)
        print(json.dumps({"status": "error", "error": message}, indent=2))
        return 1

    result = detect(inventory, reference_date, snapshot_age_days=args.snapshot_age_days)
    period = result.get("period") or "unknown"
    path = write_json(Path(args.output_dir) / f"orphan_candidates_{period}.json", result)

    degraded = result["warnings"] or result["skipped"]
    summary = {
        "status": "partial" if degraded else "ok",
        "period": period,
        "reference_date": result["reference_date"],
        "file": str(path),
        "counts": {
            "resources": result["totals"]["resources"],
            "candidates": result["totals"]["candidates"],
            "reported": result["totals"]["reported"],
            "excluded": len(result["excluded"]),
            "skipped": len(result["skipped"]),
        },
        "totals": result["totals"],
        "warnings": result["warnings"],
        "skipped": result["skipped"],
    }
    print(json.dumps(summary, indent=2))
    return 1 if degraded else 0


if __name__ == "__main__":
    sys.exit(main())
