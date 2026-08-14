#!/usr/bin/env python3
"""Deterministic orphan detection over a normalized cloudcost inventory (m1, t2).

Reads a normalized resource inventory (`cloudcost/milestone.md` §Normalized schemas) and
applies the §t2 heuristic catalog, emitting orphan candidates with a confidence, the
`evidence[]` facts that fired, and a `monthly_saving_estimate`:

    {output_dir}/{provider}_orphan_candidates_{YYYY-MM}.json

Provider-agnostic by construction. Every rule keys on normalized fields only — `state`,
`type`, `attached_to`, `created_at`, `last_activity_at`, `tags`, `name`,
`monthly_cost_estimate` — and on the *canonical values* of `type` and `state`, which are
schema-level and imported from `_normalized.py`. A second provider needs a new adapter and
nothing here. (m1 read DO's own vocabulary in two places — `STOPPED_STATES={"off"}` and
rules keyed on `droplet`/`reserved_ip`. m2 t2 a/a′ closed both; BL-074 sweeps for the rest.)

No LLM is involved anywhere in detection: rules, modifiers and thresholds are all
reviewable code (D3). There is no hardcoded "now" — the analysis is stamped with an
explicit reference date, so age rules are deterministic and testable.

Usage:
    python3 scripts/detect_orphans.py output/do_inventory_2026-07.json \\
        [--output-dir output] [--reference-date YYYY-MM-DD] [--snapshot-age-days 30] \\
        [--seat-inactive-days 30]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from _normalized import (
    STATE_STOPPED,
    TYPE_COMPUTE_INSTANCE,
    TYPE_DATABASE,
    TYPE_DATABASE_SNAPSHOT,
    TYPE_LOAD_BALANCER,
    TYPE_SEAT,
    TYPE_SNAPSHOT,
    TYPE_STATIC_IP,
    TYPE_VOLUME,
    day,
    iso,
    money,
    parse_timestamp,
    provider_slug,
    tag_coverage,
    tags_of,
    usable_resources,
)

# --------------------------------------------------------------------------- thresholds

#: Base confidences for the §t2 rule catalog.
CONFIDENCE_UNATTACHED_VOLUME = 0.9
CONFIDENCE_UNASSOCIATED_STATIC_IP = 0.95
CONFIDENCE_AGED_SNAPSHOT = 0.7
CONFIDENCE_IDLE_LOAD_BALANCER = 0.85
CONFIDENCE_STOPPED_COMPUTE_WITH_STORAGE = 0.6
CONFIDENCE_STOPPED_DATABASE_WITH_STORAGE = 0.6
#: m6 t3. MEDIUM by *equality* with the band cutoff, which C8 records as deliberate
#: calibration rather than coincidence. Ground: like the aged snapshot — also 0.7 — elapsed
#: time is the whole signal and the thing may still be wanted; unlike an unattached volume
#: (0.9) the resource has a human owner who may come back to it.
CONFIDENCE_IDLE_SEAT = 0.7

#: Age thresholds, in days. A rule fires on age *strictly greater* than its threshold.
UNATTACHED_VOLUME_MIN_AGE_DAYS = 14
#: One threshold for stopped compute and stopped databases: they are the same heuristic
#: shape, and a per-type fork would be a provider assumption wearing a type's clothes.
STOPPED_COMPUTE_MIN_AGE_DAYS = 30
DEFAULT_SNAPSHOT_AGE_DAYS = 30  # overridable: --snapshot-age-days N
#: Idle-seat threshold (m6 t3). Overridable: --seat-inactive-days N.
#:
#: **Configurable rather than constant, deliberately.** C8 records the existing
#: override asymmetry as an accident of m1's wording with no rationale behind it; this
#: threshold has the reason that one never had. How long an assigned-but-unexercised
#: entitlement may sit before it counts as recoverable is an organisation's *policy*, not a
#: property of the resource — unlike the age at which a detached disk becomes waste.
#:
#: **Thirty, and both sources agree.** GitHub publishes 30 for exactly this decision: its
#: inactive-user guidance is written against "you haven't used your assigned license for
#: GitHub Copilot in 30 days", and its licence policy revokes a seat inactive for 30 days
#: plus a further 30. And 30 is already in this catalog's register — the shared
#: stopped-compute/stopped-database threshold and the snapshot default — so no new number
#: enters the model. Recorded with its ground because C8 names two thresholds whose
#: rationale is *unestablished*, and a third would be a pattern.
DEFAULT_SEAT_INACTIVE_DAYS = 30

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

#: Stopped compute, in the canonical state vocabulary — schema-level, not any provider's
#: spelling (m2 t2 a). Every adapter maps its own idiom onto it: DO's `off`, EC2's and RDS's
#: `stopped`. This constant was m1's named seam; it now reads a value the schema defines.
STOPPED_STATES = frozenset({STATE_STOPPED})

#: Both snapshot kinds are the *same* heuristic — age, plus a source that is gone — and
#: differ only in the canonical `type` the adapter emitted, which the candidate carries.
#: One rule covers both; a second rule would duplicate the aging and evidence logic for no
#: behavioural gain (m2 t2 c).
SNAPSHOT_TYPES = frozenset({TYPE_SNAPSHOT, TYPE_DATABASE_SNAPSHOT})


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

    def __init__(
        self,
        reference_date: datetime,
        snapshot_age_days: int,
        resources: list,
        seat_inactive_days: int = DEFAULT_SEAT_INACTIVE_DAYS,
    ):
        self.reference_date = reference_date
        self.snapshot_age_days = snapshot_age_days
        self.seat_inactive_days = seat_inactive_days
        self.volumes_by_attachment: dict = {}
        for resource in resources:
            if resource.get("type") != TYPE_VOLUME:
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

    def activity_phrase(self, label: str, timestamp_value, age: float, threshold) -> str:
        """`age_phrase`'s sibling for a rule anchored on activity rather than on creation.

        A separate method rather than a widened signature on `age_phrase`: that helper's
        sentence hard-codes the word *created*, it has five call sites, and every one of them
        is pinned by a mutation row. An idleness sentence is a different sentence, not a
        parameterisation of that one.
        """
        seen = parse_timestamp(timestamp_value)
        return (
            f"{label} {day(seen)} — idle {int(age)}d at ref {day(self.reference_date)}; "
            f"threshold >{threshold}d"
        )


def fired(rule: str, confidence: float, evidence: list, saving=None) -> dict:
    """A rule's hit. `saving` overrides the default `monthly_saving_estimate`, which is the
    resource's own `monthly_cost_estimate` — used by the one rule whose saving spans more
    than the resource itself (stopped compute plus its separately-inventoried storage)."""
    hit = {"rule": rule, "base_confidence": confidence, "evidence": evidence}
    if saving is not None:
        hit["saving"] = money(saving)
    return hit


# -------------------------------------------------------------------------------- rules
#
# Each rule takes (resource, ctx) and returns a `fired(...)` dict or None. Rules read the
# normalized schema only. In the m1 catalog the rules are type-disjoint, so at most one
# fires per resource; the engine is written to emit one candidate per firing regardless.


def rule_unattached_volume(resource: dict, ctx: Context):
    """Unattached volume older than 14 days — 0.9."""
    if resource.get("type") != TYPE_VOLUME or resource.get("attached_to") is not None:
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


def rule_unassociated_static_ip(resource: dict, ctx: Context):
    """Static IP associated with nothing — 0.95. No age threshold: an unassociated static
    IP bills from the moment it is unassociated (a DO reserved IP, an AWS Elastic IP)."""
    if resource.get("type") != TYPE_STATIC_IP or resource.get("attached_to") is not None:
        return None
    evidence = ["attached_to is null — the static IP is not associated with any instance"]
    age = ctx.age_days(resource.get("created_at"))
    if age is not None:
        evidence.append(
            ctx.age_phrase("reserved for", resource.get("created_at"), age)
            + "; this rule has no age threshold"
        )
    return fired("unassociated_static_ip", CONFIDENCE_UNASSOCIATED_STATIC_IP, evidence)


def rule_aged_snapshot(resource: dict, ctx: Context):
    """Snapshot older than N days (N is a parameter, default 30) — 0.7.

    Covers both canonical snapshot types (`snapshot`, `database_snapshot`): the heuristic is
    age plus a source that is gone, which is identical for an EBS snapshot and an RDS manual
    snapshot. The candidate carries the `type`, so the report still distinguishes them; the
    evidence sentences deliberately do not.
    """
    if resource.get("type") not in SNAPSHOT_TYPES:
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
    if resource.get("type") != TYPE_LOAD_BALANCER or resource.get("attached_to") is not None:
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


def rule_stopped_compute_with_attached_storage(resource: dict, ctx: Context):
    """Stopped instance older than 30 days that still carries attached storage — 0.6.

    "Attached storage" is an intra-inventory join: at least one volume whose `attached_to`
    equals this resource's `resource_id`. The saving is the instance's **own** estimate
    **plus** those volumes' — m1 named them in the evidence but did not sum them, which
    under-reported the saving (m2 t2 c closes that forward).

    Adding rather than replacing is what keeps the rule provider-agnostic: each adapter has
    already encoded its own cost model in `monthly_cost_estimate`, so the same sum is
    correct for a provider that bills a stopped instance (DO: own is the full droplet price)
    and one that does not (AWS: own is 0.0, and the EBS volume carries the whole charge).
    Only *separately inventoried* storage is summed here — storage a provider folds into the
    instance's own estimate is already counted once, in that estimate.
    """
    if resource.get("type") != TYPE_COMPUTE_INSTANCE:
        return None
    if resource.get("state") not in STOPPED_STATES:
        return None
    age = ctx.age_days(resource.get("created_at"))
    if age is None or age <= STOPPED_COMPUTE_MIN_AGE_DAYS:
        return None
    attached = ctx.volumes_by_attachment.get(resource.get("resource_id")) or []
    if not attached:
        return None

    own = money(resource.get("monthly_cost_estimate"))
    evidence = [
        f"state is '{resource.get('state')}' — the instance is stopped",
        ctx.age_phrase(
            "stopped instance age",
            resource.get("created_at"),
            age,
            STOPPED_COMPUTE_MIN_AGE_DAYS,
        ),
    ]
    storage_total = 0.0
    for volume in sorted(attached, key=lambda v: str(v.get("resource_id"))):
        cost = money(volume.get("monthly_cost_estimate"))
        storage_total += cost
        evidence.append(
            f"attached storage {volume.get('resource_id')} "
            f"({volume.get('name')}, {volume.get('size')}) — "
            f"${cost:.2f}/mo"
        )
    saving = round(own + storage_total, 2)
    evidence.append(
        f"saving estimate is the instance's own ${own:.2f}/mo plus its attached storage "
        f"${storage_total:.2f}/mo = ${saving:.2f}/mo"
    )
    return fired(
        "stopped_compute_with_attached_storage",
        CONFIDENCE_STOPPED_COMPUTE_WITH_STORAGE,
        evidence,
        saving=saving,
    )


def rule_stopped_database_with_storage(resource: dict, ctx: Context):
    """Stopped database older than 30 days still paying for its storage — 0.6.

    The same shape as the stopped-compute rule, for a resource whose storage the provider
    does not inventory separately: a stopped RDS instance bills no compute but keeps paying
    for its allocated storage, and that charge is already inside its own
    `monthly_cost_estimate`. So the signal that storage remains is simply a non-zero
    estimate on a stopped resource, and the saving is that estimate — summing an attached
    volume here would double-count storage the adapter has already priced in.

    `attached_to` is null for a stopped database (it serves nothing); a database still
    serving traffic is attached to itself and never reaches this rule.
    """
    if resource.get("type") != TYPE_DATABASE:
        return None
    if resource.get("state") not in STOPPED_STATES:
        return None
    if resource.get("attached_to") is not None:
        return None
    own = money(resource.get("monthly_cost_estimate"))
    if own <= 0:
        return None
    age = ctx.age_days(resource.get("created_at"))
    if age is None or age <= STOPPED_COMPUTE_MIN_AGE_DAYS:
        return None

    return fired(
        "stopped_database_with_storage",
        CONFIDENCE_STOPPED_DATABASE_WITH_STORAGE,
        [
            f"state is '{resource.get('state')}' — the database is stopped",
            "attached_to is null — the database is serving nothing",
            ctx.age_phrase(
                "stopped database age",
                resource.get("created_at"),
                age,
                STOPPED_COMPUTE_MIN_AGE_DAYS,
            ),
            f"monthly_cost_estimate is ${own:.2f}/mo while stopped — the allocated storage "
            f"still bills; it is priced into this estimate, so the saving is that estimate",
        ],
    )


def rule_idle_seat(resource: dict, ctx: Context):
    """Assigned seat unexercised for longer than N days (N is a parameter, default 30) — 0.7.

    **The first rule in the catalog keyed on an activity timestamp rather than on an age**, and
    the first whose notion of idleness is not C7's. C7 makes `attached_to is null` the universal
    idle signal, keyed by four rules, where idle means *attached to nothing*. A seat is never
    unattached — it is assigned to somebody, and the adapter says so — so that signal cannot
    reach this case at all. The waste here is an entitlement that **has** an owner and still
    produces nothing: assigned, billed, and unexercised. That distinction is what the
    consumption class needed a rule for.

    **A null `last_activity_at` is not an unknown here — it is the strongest form of the
    signal, and the rule anchors on `created_at` instead.** For a seat the field is null in
    exactly two situations: never exercised since it was assigned, or last exercised longer ago
    than the provider retains (GitHub nulls it past a rolling 90 days). Both mean *at least* as
    idle as any non-null value, so treating null as silence would hide the purest case of the
    waste this rule exists to find. GitHub's own published inactive-user workflow resolves it
    the same way, falling back to the assignment date. `created_at` is a sound anchor under
    both readings: a seat whose activity has aged out of retention was necessarily created
    before that.

    The fallback is keyed on the value being **absent**, never on its being unparseable — an
    unparseable timestamp leaves the rule silent, as it does every other rule, and is surfaced
    by `timestamp_warnings` rather than guessed around.
    """
    if resource.get("type") != TYPE_SEAT:
        return None

    last_activity = resource.get("last_activity_at")
    if last_activity is None:
        label, anchor = "no activity recorded since assignment", resource.get("created_at")
    else:
        label, anchor = "last activity", last_activity

    age = ctx.age_days(anchor)
    if age is None or age <= ctx.seat_inactive_days:
        return None

    evidence = [ctx.activity_phrase(label, anchor, age, ctx.seat_inactive_days)]
    if last_activity is None:
        evidence.append(
            "last_activity_at is null — for a seat that means never exercised since it was "
            "assigned, or exercised longer ago than the provider retains; both are at least "
            "this idle, so the age above is anchored on created_at"
        )
    if resource.get("attached_to") is not None:
        evidence.append(
            f"attached_to is {resource.get('attached_to')!r} — the seat is assigned, so it is "
            f"not idle in the unattached sense the other rules key on; it is an entitlement "
            f"nobody is exercising"
        )
    saving = money(resource.get("monthly_cost_estimate"))
    evidence.append(
        f"monthly_cost_estimate is ${saving:.2f}/mo and a seat bills for as long as it is "
        f"assigned regardless of use — so reclaiming it saves that whole figure"
    )
    return fired("idle_seat", CONFIDENCE_IDLE_SEAT, evidence)


#: Evaluated in order; each may contribute one candidate.
RULES = (
    rule_unattached_volume,
    rule_unassociated_static_ip,
    rule_aged_snapshot,
    rule_idle_load_balancer,
    rule_stopped_compute_with_attached_storage,
    rule_stopped_database_with_storage,
    rule_idle_seat,
)

#: The canonical `type` values some rule above keys on — the catalog's own account of what
#: it is able to evaluate, emitted on every artifact so a downstream stage never has to
#: infer it (m6 t2c).
#:
#: **This is NOT `CANONICAL_TYPES`, and the difference is the point.** `CANONICAL_TYPES` is
#: the schema's closed set: a `type` outside it is a contract violation. This is the rule
#: catalog's subset of it: a canonical type absent from here is **legitimate and permanent**
#: — it is counted in every total and evaluated by nothing, which is a stated boundary
#: rather than a fault. The two coincided until m6 t1 added a canonical type ahead of any
#: rule keying on it, and `compose_report_data` had been using membership of the first as a
#: proxy for the second; over the divergence it reported a completeness the catalog did not
#: have.
#:
#: Hand-maintained, and deliberately not derived: each rule's keying lives inside its body
#: as an early return, and introspecting that would couple this declaration to the rules'
#: internal shape. **A rule added without updating this set is not caught here** — the
#: composer's contradiction guard catches the other direction (a candidate whose type is
#: absent from this set), and the uncaught direction errs conservatively, understating
#: coverage rather than overstating it. Whoever adds the next rule updates this set.
#:
#: m6 t3 added `seat` with `rule_idle_seat`, which makes the two sets **equal again** — every
#: canonical type now has a rule keying on it. That is a fact about today's catalog and not a
#: property to rely on: the equality is not asserted anywhere, deliberately, because the next
#: canonical type introduced ahead of its rule reopens the divergence and must be allowed to.
RULE_KEYED_TYPES = frozenset(
    {
        TYPE_VOLUME,  # rule_unattached_volume
        TYPE_STATIC_IP,  # rule_unassociated_static_ip
        *SNAPSHOT_TYPES,  # rule_aged_snapshot — snapshot + database_snapshot
        TYPE_LOAD_BALANCER,  # rule_idle_load_balancer
        TYPE_COMPUTE_INSTANCE,  # rule_stopped_compute_with_attached_storage
        TYPE_DATABASE,  # rule_stopped_database_with_storage
        TYPE_SEAT,  # rule_idle_seat
    }
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
        # The resource's own estimate unless the rule computed a saving spanning more than
        # the resource itself (stopped compute + its separately-inventoried storage).
        "monthly_saving_estimate": (
            hit["saving"]
            if "saving" in hit
            else money(resource.get("monthly_cost_estimate"))
        ),
    }


def detect(
    inventory: dict,
    reference_date: datetime,
    snapshot_age_days: int = DEFAULT_SNAPSHOT_AGE_DAYS,
    seat_inactive_days: int = DEFAULT_SEAT_INACTIVE_DAYS,
) -> dict:
    """Apply the rule catalog to a normalized inventory.

    Pure and deterministic: the same (inventory, reference_date, snapshot_age_days,
    seat_inactive_days) always produces a byte-identical result. No wall clock is read.
    """
    resources, skipped = usable_resources(inventory)
    ctx = Context(
        reference_date, snapshot_age_days, resources, seat_inactive_days=seat_inactive_days
    )

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
        # What the catalog can evaluate, travelling with the run that used it (m6 t2c).
        # Top-level rather than inside `parameters`: a parameter is something a run can be
        # configured with, and this is derived from the catalog and is not settable.
        "rule_keyed_types": sorted(RULE_KEYED_TYPES),
        "parameters": {
            "snapshot_age_days": snapshot_age_days,
            "seat_inactive_days": seat_inactive_days,
            "unattached_volume_min_age_days": UNATTACHED_VOLUME_MIN_AGE_DAYS,
            "stopped_compute_min_age_days": STOPPED_COMPUTE_MIN_AGE_DAYS,
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
    parser.add_argument(
        "--seat-inactive-days",
        type=int,
        default=DEFAULT_SEAT_INACTIVE_DAYS,
        help=f"idle-seat threshold N in days (default: {DEFAULT_SEAT_INACTIVE_DAYS})",
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

    result = detect(
        inventory,
        reference_date,
        snapshot_age_days=args.snapshot_age_days,
        seat_inactive_days=args.seat_inactive_days,
    )
    period = result.get("period") or "unknown"
    # Provider-prefixed: each provider is its own solo run writing into the same output
    # directory (decision H), so an unprefixed name would have the second provider's
    # candidates overwrite the first's (m1 open item, closed at m2 t2 b).
    provider = provider_slug(result.get("provider"))
    path = write_json(
        Path(args.output_dir) / f"{provider}_orphan_candidates_{period}.json", result
    )

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
