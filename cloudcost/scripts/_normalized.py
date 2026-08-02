"""Shared vocabulary over the normalized cloudcost schemas (m1; canonical values at m2 t2).

The stages downstream of an adapter — `detect_orphans.py` (t2) and
`compose_report_data.py` (t3) — must agree on a handful of definitions that are part of
the *contract*, not of either stage: how a timestamp is parsed, what counts as a usable
resource entry, and what fraction of an inventory carries tags. t3's tag-coverage figure
is required to equal t2's, so that definition lives here once rather than being restated
in both CLIs (repo rule: factor cross-script plumbing into a shared `_helper.py` module
rather than duplicating it or cross-importing between CLIs).

The same argument, more strongly, holds for the canonical `type` / `state` *values* below:
they are the definition of the schema seam, so by construction they have exactly one home
— this module — which every adapter (`fetch_do.py`, `fetch_aws.py`) and the shared rule
engine imports from (m2 t2 a/a′).

Provider-agnostic by construction: every function here reads first-class fields of
`cloudcost/milestone.md` §Normalized schemas and nothing else — no provider vocabulary,
and nothing under the provider-specific payload block. (The name of that block is spelled
out nowhere in this module on purpose: t2's provider-agnostic guard greps for it.)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# --------------------------------------------------------------- canonical vocabulary
#
# The `type` and `state` values the normalized schema itself defines (m2 t2 a/a′). These
# are schema-level, not provider vocabulary: `detect_orphans.py` keys its rules on them, so
# a provider-flavoured value anywhere here would put provider vocabulary inside shared
# machinery — the seam m1 named as `STOPPED_STATES` and t1 found to be three (BL-074).
#
# This module is the single home, and every adapter imports from it: an adapter that
# declared its own would let the vocabulary drift on the exact seam t2 exists to remove,
# and an adapter importing from a *sibling adapter* is the cross-import anti-pattern.
# `cloudcost/milestone.md` §Normalized schemas enumerates the same set in prose.

TYPE_COMPUTE_INSTANCE = "compute_instance"  # EC2 instance / DO droplet
TYPE_VOLUME = "volume"  # EBS volume / DO volume
TYPE_STATIC_IP = "static_ip"  # Elastic IP / DO reserved IP
TYPE_SNAPSHOT = "snapshot"  # EBS snapshot / DO snapshot
TYPE_LOAD_BALANCER = "load_balancer"  # ELB/ALB/NLB / DO load balancer
TYPE_DATABASE = "database"  # RDS instance
TYPE_DATABASE_SNAPSHOT = "database_snapshot"  # RDS manual snapshot

#: The closed set every adapter emits from. A `type` outside it is a contract violation.
CANONICAL_TYPES = frozenset(
    {
        TYPE_COMPUTE_INSTANCE,
        TYPE_VOLUME,
        TYPE_STATIC_IP,
        TYPE_SNAPSHOT,
        TYPE_LOAD_BALANCER,
        TYPE_DATABASE,
        TYPE_DATABASE_SNAPSHOT,
    }
)

#: Canonical state for stopped compute — an EC2 instance, an RDS instance, a DO droplet.
#: `detect_orphans.STOPPED_STATES` is this value and nothing else.
STATE_STOPPED = "stopped"


def parse_timestamp(value):
    """Parse an ISO-8601 timestamp to an aware UTC datetime, or None if unparseable."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def day(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%d")


def money(value) -> float:
    """Coerce an amount to a 2dp float; anything uncoercible is 0.0, never an exception."""
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def provider_slug(value) -> str:
    """Filesystem-safe provider token for an output filename. Computed here, never by an
    LLM (repo rule).

    `compose_report_data.py` carries an identical private `slug()` for its history
    filenames. It is deliberately not converged onto this one: §t2 (d) freezes that file so
    the AWS run's "compose ran unchanged" result stays a clean negative proof. Converge the
    two when compose is next legitimately edited (BL-070).
    """
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return cleaned or "unknown"


def tags_of(resource: dict) -> list:
    tags = resource.get("tags")
    return [t for t in tags if isinstance(t, str)] if isinstance(tags, list) else []


def usable_resources(inventory: dict) -> tuple:
    """Split an inventory's resources into usable entries and skipped ones.

    A malformed entry is skipped and counted, never fatal — a stage degrades rather than
    breaking its stdout contract. The usable list is the denominator of `tag_coverage`,
    which is why this split is shared: t2 and t3 must report the same coverage figure.
    """
    usable, skipped = [], []
    for index, resource in enumerate(inventory.get("resources") or []):
        if not isinstance(resource, dict):
            skipped.append({"index": index, "reason": "resource entry is not an object"})
        elif not resource.get("resource_id"):
            skipped.append({"index": index, "reason": "resource entry has no resource_id"})
        elif not resource.get("type"):
            skipped.append({"index": index, "reason": "resource entry has no type"})
        else:
            usable.append(resource)
    return usable, skipped


def tag_coverage(resources: list) -> float:
    """Fraction of `resources` carrying at least one tag, to 4dp. Empty list -> 0.0."""
    if not resources:
        return 0.0
    tagged = sum(1 for resource in resources if tags_of(resource))
    return round(tagged / len(resources), 4)
