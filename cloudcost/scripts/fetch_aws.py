#!/usr/bin/env python3
"""AWS read-only cost + inventory adapter (cloudcost m2, t1).

Fetches AWS cost (Cost Explorer, service granularity, every service on the bill) and a
full-region resource inventory (EC2 instances, EBS volumes, Elastic IPs, EBS snapshots,
load balancers, RDS instances and manual RDS snapshots) and emits the two normalized JSON
files defined in `cloudcost/milestone.md` §Normalized schemas:

    {output_dir}/aws_costs_{YYYY-MM}.json
    {output_dir}/aws_inventory_{YYYY-MM}.json

Read-only by construction: every call is a Describe/Get/List. This script never creates,
modifies or deletes an AWS resource.

Auth (D2 + m2 decision C). Credentials are read from CLOUDCOST_AWS_ACCESS_KEY_ID /
CLOUDCOST_AWS_SECRET_ACCESS_KEY (+ optional CLOUDCOST_AWS_SESSION_TOKEN /
CLOUDCOST_AWS_REGION) and passed to an explicitly-constructed boto3 Session. boto3's
default credential chain — AWS_ACCESS_KEY_ID/AWS_PROFILE, ~/.aws/credentials, instance
metadata — is never consulted, so the operator's personal AWS credential cannot shadow the
read-only one. Credentials are env-only: never an argument, never printed to stdout or
stderr, never written to an output file.

Usage:
    python3 scripts/fetch_aws.py [--output-dir output] [--period YYYY-MM]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import botocore.session
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from _normalized import (
    STATE_STOPPED,
    TYPE_COMPUTE_INSTANCE,
    TYPE_DATABASE,
    TYPE_DATABASE_SNAPSHOT,
    TYPE_LOAD_BALANCER,
    TYPE_SNAPSHOT,
    TYPE_STATIC_IP,
    TYPE_VOLUME,
)

#: The only environment variables this adapter will authenticate with.
ACCESS_KEY_ENV = "CLOUDCOST_AWS_ACCESS_KEY_ID"
SECRET_KEY_ENV = "CLOUDCOST_AWS_SECRET_ACCESS_KEY"
SESSION_TOKEN_ENV = "CLOUDCOST_AWS_SESSION_TOKEN"
REGION_ENV = "CLOUDCOST_AWS_REGION"
#: Documented override for the swept-region set (comma-separated). Decision D.
REGIONS_ENV = "CLOUDCOST_AWS_REGIONS"

#: Variables boto3's default credential chain reads. This adapter ignores them; their
#: presence is warned about, never their value. (~/.aws/credentials and IMDS are the other
#: two arms of the chain — neutralized by construction, see build_session.)
SHADOWING_ENV = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_PROFILE",
)

#: AWS bills USD (decision E).
CURRENCY = "USD"

#: Region used to bootstrap `ec2:DescribeRegions` when CLOUDCOST_AWS_REGION is unset.
DEFAULT_BOOTSTRAP_REGION = "us-east-1"

#: Cost Explorer is a global service with its endpoint in us-east-1. Pinned rather than
#: swept: a CE client built with the sweep region queries a different endpoint per region
#: and would multiply-count the bill.
CE_REGION = "us-east-1"

#: Error codes that mean "the credential is wrong", not "the call failed". Fatal, no retry.
AUTH_ERROR_CODES = frozenset(
    {
        "AuthFailure",
        "InvalidClientTokenId",
        "UnrecognizedClientException",
        "SignatureDoesNotMatch",
        "InvalidAccessKeyId",
        "MissingAuthenticationToken",
        "ExpiredToken",
        "ExpiredTokenException",
    }
)

#: Error codes that mean "this region/service is not enabled for the account". Not an auth
#: problem with the credential itself, and not a degradation worth reporting per-service.
#:
#: `UnauthorizedOperation` deliberately does NOT belong here. It is EC2's "you lack the IAM
#: permission for this action" — a real gap in the policy, not a disabled region. Reporting
#: it as a warning would let a missing `ec2:Describe*` produce an empty inventory on a green
#: run, with a reason that reads plausibly and is wrong. It falls through to `errors[]`,
#: which makes the run partial and non-zero. Same for `AccessDenied` (ELB/RDS's spelling).
REGION_DISABLED_CODES = frozenset({"OptInRequired"})


# ------------------------------------------------------------------ normalized vocabulary
#
# The canonical `type` / `state` values are imported from `_normalized.py`, which is their
# single home (m2 t2 a′). t1 declared them here, before the shared module was the agreed
# home; the relocation is byte-identical in what this adapter emits — every t1 fixture and
# test stays green, which is the check that it *was* a relocation and not a change.


# ---------------------------------------------------------------------------- list prices
#
# Monthly us-east-1 on-demand list prices used to derive `monthly_cost_estimate` from
# size/type (D4: resource-level dollars are *estimates*; actuals stay service-level on the
# cost side). The AWS Pricing API (`pricing:GetProducts`) is deliberately NOT used — it is
# not in the ratified read-only IAM policy (m2 §Prereqs 1) and adding it would widen the
# credential's surface.
#
# The block below is the LOAD-BEARING closed set: every orphan saving is derived from these
# rates, and each is a flat, well-known figure. Instance *compute* rates are best-effort and
# live in COMPUTE_MONTHLY further down — they feed running-instance display only, never an
# orphan saving, so the open-ended instance-type table cannot threaten the headline figure.
#
# BL-071 (resource-level cost + rate spot-check) checks these against a resource-granular
# bill; they are labelled here precisely so there is something to check.

EBS_GIB_MONTHLY = {
    "gp3": 0.08,
    "gp2": 0.10,
    "io1": 0.125,
    "io2": 0.125,
    "st1": 0.045,
    "sc1": 0.015,
    "standard": 0.05,
}
EBS_GIB_MONTHLY_DEFAULT = 0.10

#: EBS snapshots bill on stored (incremental) GiB; the volume size is the honest upper bound.
EBS_SNAPSHOT_GIB_MONTHLY = 0.05

#: AWS charges $0.005/hr for an Elastic IP that is not associated with a running instance.
ELASTIC_IP_UNASSOCIATED_MONTHLY = 3.65

#: Load balancer hourly base rate (capacity-unit charges are usage-driven and not estimated).
LOAD_BALANCER_MONTHLY = {
    "application": 16.43,  # $0.0225/hr
    "network": 16.43,  # $0.0225/hr
    "gateway": 9.13,  # $0.0125/hr
    "classic": 18.25,  # $0.025/hr
}
LOAD_BALANCER_MONTHLY_DEFAULT = 16.43

#: RDS storage, per allocated GiB-month.
RDS_STORAGE_GIB_MONTHLY = {
    "gp2": 0.115,
    "gp3": 0.115,
    "io1": 0.125,
    "io2": 0.125,
    "standard": 0.10,
    "magnetic": 0.10,
}
RDS_STORAGE_GIB_MONTHLY_DEFAULT = 0.115

#: RDS manual snapshots bill on stored GiB beyond the free allowance.
RDS_SNAPSHOT_GIB_MONTHLY = 0.095

# --------------------------------------------------------------------------------------
# Best-effort compute rates. NOT load-bearing: a stopped instance bills ~$0 compute (see
# `instance_compute_estimate`), so no orphan saving is ever derived from this table. An
# unknown instance type yields 0.0 plus a `warnings[]` entry naming the type — never an
# invented figure. Extend as the bill demands; an unknown type is a warning, not a defect.

COMPUTE_MONTHLY = {
    # EC2 (us-east-1, Linux on-demand, 730h)
    "t2.micro": 8.47,
    "t2.small": 16.94,
    "t2.medium": 33.87,
    "t3.micro": 7.59,
    "t3.small": 15.18,
    "t3.medium": 30.37,
    "t3.large": 60.74,
    "t3a.micro": 6.86,
    "t3a.small": 13.72,
    "t3a.medium": 27.45,
    "t4g.micro": 6.13,
    "t4g.small": 12.26,
    "t4g.medium": 24.53,
    "m5.large": 70.08,
    "m5.xlarge": 140.16,
    "m6i.large": 70.08,
    "m6g.large": 56.06,
    "c5.large": 62.05,
    "c6i.large": 62.05,
    "c6g.large": 49.64,
    "r5.large": 91.98,
    "r6i.large": 91.98,
    # RDS (us-east-1, single-AZ on-demand, 730h)
    "db.t3.micro": 11.68,
    "db.t3.small": 23.36,
    "db.t3.medium": 46.72,
    "db.t4g.micro": 10.51,
    "db.t4g.small": 21.02,
    "db.t4g.medium": 42.05,
    "db.m5.large": 124.83,
    "db.m6g.large": 111.69,
    "db.r5.large": 172.28,
}


# ------------------------------------------------------------------------------ exceptions


class AWSAuthError(RuntimeError):
    """Authentication/authorisation failure. Never carries a credential."""


class AWSAPIError(RuntimeError):
    """Non-auth API failure after retries are exhausted."""


# --------------------------------------------------------------------------------- clients


def load_credentials(env: dict | None = None) -> dict:
    """Read the read-only credential from CLOUDCOST_AWS_* and nowhere else."""
    env = os.environ if env is None else env
    access_key = (env.get(ACCESS_KEY_ENV) or "").strip()
    secret_key = (env.get(SECRET_KEY_ENV) or "").strip()
    missing = [
        name
        for name, value in ((ACCESS_KEY_ENV, access_key), (SECRET_KEY_ENV, secret_key))
        if not value
    ]
    if missing:
        raise AWSAuthError(
            f"{' and '.join(missing)} not set. cloudcost authenticates with "
            f"{ACCESS_KEY_ENV}/{SECRET_KEY_ENV} only and never falls back to boto3's "
            f"default credential chain ({' / '.join(SHADOWING_ENV)}, ~/.aws/credentials, "
            f"instance metadata) — export the read-only key before running."
        )
    return {
        "access_key_id": access_key,
        "secret_access_key": secret_key,
        "session_token": (env.get(SESSION_TOKEN_ENV) or "").strip() or None,
        "region": (env.get(REGION_ENV) or "").strip() or DEFAULT_BOOTSTRAP_REGION,
    }


def warn_shadowing_env(env: dict | None = None, stream=None) -> list:
    """Name (never print the value of) any default-chain credential that is being ignored."""
    env = os.environ if env is None else env
    # Resolved at call time, not import time, so redirected stderr is honoured.
    stream = sys.stderr if stream is None else stream
    present = [name for name in SHADOWING_ENV if (env.get(name) or "").strip()]
    for name in present:
        print(
            f"warning: {name} is set in this environment and is IGNORED; cloudcost "
            f"authenticates with {ACCESS_KEY_ENV}/{SECRET_KEY_ENV} only.",
            file=stream,
        )
    return present


class AWSClients:
    """Explicitly-credentialed boto3 client factory. The default chain is never consulted."""

    def __init__(
        self,
        credentials: dict,
        endpoint_url: str | None = None,
        timeout: int = 30,
        max_attempts: int = 4,
    ) -> None:
        # Held only to redact them out of error text; never logged, never returned.
        self._access_key = credentials["access_key_id"]
        self._secret_key = credentials["secret_access_key"]
        self._session_token = credentials.get("session_token")
        self.bootstrap_region = credentials.get("region") or DEFAULT_BOOTSTRAP_REGION
        self.endpoint_url = endpoint_url
        self.config = Config(
            connect_timeout=timeout,
            read_timeout=timeout,
            retries={"max_attempts": max(1, max_attempts), "mode": "standard"},
            user_agent_extra="aetheris-cloudcost/1.0 (read-only)",
        )
        self.session = self._build_session()
        self._cache: dict = {}

    def _build_session(self):
        """Explicit credentials only. boto3's default chain is never consulted.

        `session_vars` removes the profile from botocore's config resolution. Without it, a
        stray `AWS_PROFILE` naming a profile that does not exist raises `ProfileNotFound`
        from `get_scoped_config` *before* the explicit credentials are ever looked at — so
        the operator's environment could break a run that supplies perfectly good keys.
        Verified against boto3 1.43.14; see docs/m2-t1-implementation-notes.md.
        """
        botocore_session = botocore.session.Session(
            session_vars={"profile": (None, None, None, None)}
        )
        return boto3.session.Session(
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            aws_session_token=self._session_token,
            region_name=self.bootstrap_region,
            botocore_session=botocore_session,
        )

    def client(self, service: str, region: str | None = None):
        region = region or self.bootstrap_region
        key = (service, region)
        if key not in self._cache:
            self._cache[key] = self.session.client(
                service,
                region_name=region,
                endpoint_url=self.endpoint_url,
                config=self.config,
            )
        return self._cache[key]

    def redact(self, text: str) -> str:
        """Belt-and-braces: strip every credential value from text reaching an error path."""
        for secret in (self._access_key, self._secret_key, self._session_token):
            if secret:
                text = text.replace(secret, "***")
        return text

    def __repr__(self) -> str:  # pragma: no cover - defensive, keeps creds out of reprs
        return f"<AWSClients bootstrap_region={self.bootstrap_region!r}>"


def error_code(exc: ClientError) -> str:
    return (exc.response or {}).get("Error", {}).get("Code") or ""


def raise_for(clients: AWSClients, exc: Exception, what: str):
    """Translate a botocore exception into the adapter's own, credential-free, vocabulary."""
    if isinstance(exc, ClientError) and error_code(exc) in AUTH_ERROR_CODES:
        raise AWSAuthError(
            f"AWS rejected the {ACCESS_KEY_ENV} credential on {what}: "
            f"{clients.redact(error_code(exc))}"
        ) from None
    raise AWSAPIError(f"{what} failed: {clients.redact(str(exc))}") from None


#: `elb`/`elbv2` DescribeTags accept at most 20 identifiers per call.
TAG_BATCH = 20


def describe_tags(client, request_key: str, identifiers: list, response_key: str) -> dict:
    """{identifier -> normalized tag list} for load balancers, batched.

    Load balancer tags need a separate call — neither DescribeLoadBalancers returns them.
    Skipping it would be cheaper, but it would make every load balancer read as untagged,
    which is a wrong figure rather than a missing one: t3's tag-coverage percentage and its
    "top untagged spenders" table would both silently mis-count a tagged LB. One extra call
    per 20 load balancers is the honest price.
    """
    wanted = [str(i) for i in identifiers if i]
    out: dict = {}
    for start in range(0, len(wanted), TAG_BATCH):
        batch = wanted[start : start + TAG_BATCH]
        response = client.describe_tags(**{request_key: batch})
        for description in response.get("TagDescriptions") or []:
            key = description.get(response_key)
            if key:
                out[str(key)] = tags_of(description)
    return out


def paginate(client, operation: str, result_key: str, **kwargs):
    """Yield every item of `result_key`, following the operation's own paging token.

    Not every operation is pageable — `ec2:DescribeAddresses`, `ec2:DescribeRegions` and
    `ce:GetCostAndUsage` have no paginator (verified with `can_paginate`) — so this falls
    back to a single call rather than raising `OperationNotPageableError`.
    """
    if client.can_paginate(operation):
        for page in getattr(client, "get_paginator")(operation).paginate(**kwargs):
            yield from (page.get(result_key) or [])
    else:
        yield from (getattr(client, operation)(**kwargs).get(result_key) or [])


# ---------------------------------------------------------------------------------- helpers


def money(value) -> float:
    """Coerce an amount (CE returns strings) to a 2dp float; uncoercible is 0.0."""
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso(value) -> str | None:
    """Normalize a boto3 timestamp to the schema's `%Y-%m-%dT%H:%M:%SZ`.

    Parsed responses carry real `datetime` objects, which `json.dumps` cannot serialize —
    every `created_at` must pass through here or the emitted file cannot be written.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


def tags_of(raw: dict, key: str = "Tags") -> list:
    """AWS tags are [{Key,Value}]; the normalized schema is a flat `k=v` string list.

    RDS spells the field `TagList`; ELBv2 returns tags from a separate call the sweep does
    not make (read-only budget), so load balancers carry `[]`.
    """
    tags = raw.get(key)
    if not isinstance(tags, list):
        return []
    out = []
    for tag in tags:
        if not isinstance(tag, dict):
            continue
        name = tag.get("Key")
        if not name:
            continue
        value = tag.get("Value")
        out.append(f"{name}={value}" if value else str(name))
    return out


def name_from_tags(raw: dict, key: str = "Tags") -> str | None:
    tags = raw.get(key)
    if not isinstance(tags, list):
        return None
    for tag in tags:
        if isinstance(tag, dict) and tag.get("Key") == "Name":
            return tag.get("Value") or None
    return None


def month_bounds(period: str) -> tuple:
    """[start, end) for a YYYY-MM period, as the ISO dates Cost Explorer wants."""
    start = datetime.strptime(period, "%Y-%m").replace(tzinfo=timezone.utc)
    end = (start + timedelta(days=32)).replace(day=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def instance_compute_estimate(instance_type: str | None, stopped: bool, warnings: list) -> float:
    """Best-effort monthly compute list price.

    A *stopped* instance bills ~$0 compute — its storage bills on the volume rows, which the
    inventory carries separately. Emitting the running rate here would encode a provider cost
    model ("billed flat regardless of state") that is true for DO and false for AWS, and it
    would do so in a field shared machinery reads. The adapter owns its provider's cost
    model, so the honest figure is 0.0 (D5).

    An unrecognised instance type yields 0.0 and a named warning — never an invented figure.
    """
    if stopped:
        return 0.0
    if not instance_type:
        return 0.0
    rate = COMPUTE_MONTHLY.get(instance_type)
    if rate is None:
        note = (
            f"no list-price rate for instance type '{instance_type}'; "
            f"monthly_cost_estimate reported as 0.00 rather than invented"
        )
        if note not in warnings:
            warnings.append(note)
        return 0.0
    return round(rate, 2)


# ------------------------------------------------------------------------------ normalizers


def normalize_instance(raw: dict, region: str, warnings: list) -> dict:
    state = ((raw.get("State") or {}).get("Name") or "").lower()
    instance_type = raw.get("InstanceType")
    return {
        "resource_id": str(raw.get("InstanceId")),
        "type": TYPE_COMPUTE_INSTANCE,
        "name": name_from_tags(raw) or str(raw.get("InstanceId")),
        "region": region,
        "size": instance_type,
        # EC2's own vocabulary is already "stopped"; mapped through the constant so the
        # canonical value is stated once and a provider rename cannot drift silently.
        "state": STATE_STOPPED if state == "stopped" else state or None,
        "created_at": iso(raw.get("LaunchTime")),
        "last_activity_at": None,
        "attached_to": None,
        "monthly_cost_estimate": instance_compute_estimate(
            instance_type, state == "stopped", warnings
        ),
        "tags": tags_of(raw),
        "raw_ref": f"aws://ec2/{region}/{raw.get('InstanceId')}",
    }


def normalize_volume(raw: dict, region: str) -> dict:
    gib = raw.get("Size") or 0
    volume_type = raw.get("VolumeType") or "gp2"
    attachments = [a for a in (raw.get("Attachments") or []) if isinstance(a, dict)]
    attached_to = None
    for attachment in attachments:
        if attachment.get("InstanceId"):
            attached_to = str(attachment["InstanceId"])
            break
    rate = EBS_GIB_MONTHLY.get(volume_type, EBS_GIB_MONTHLY_DEFAULT)
    return {
        "resource_id": str(raw.get("VolumeId")),
        "type": TYPE_VOLUME,
        "name": name_from_tags(raw) or str(raw.get("VolumeId")),
        "region": region,
        "size": f"{gib}GiB",
        "state": raw.get("State"),
        "created_at": iso(raw.get("CreateTime")),
        "last_activity_at": None,
        "attached_to": attached_to,
        "monthly_cost_estimate": round(gib * rate, 2),
        "tags": tags_of(raw),
        "raw_ref": f"aws://ec2/{region}/{raw.get('VolumeId')}",
    }


def normalize_address(raw: dict, region: str) -> dict:
    """Elastic IP. `attached_to` is the association, which is the orphan signal.

    An EIP can be associated with an instance or with a network interface (an NLB, a NAT
    gateway); either association means it is in service. Only a fully unassociated address
    reads as an orphan — the direct analogue of DO's unassigned reserved IP.
    """
    attached_to = raw.get("InstanceId") or raw.get("NetworkInterfaceId") or None
    if attached_to is not None:
        attached_to = str(attached_to)
    resource_id = str(raw.get("AllocationId") or raw.get("PublicIp"))
    return {
        "resource_id": resource_id,
        "type": TYPE_STATIC_IP,
        "name": name_from_tags(raw) or raw.get("PublicIp"),
        "region": region,
        "size": None,
        "state": "associated" if attached_to else "unassociated",
        # EC2 exposes no allocation time for an address; the schema requires the field, so
        # it is null rather than fabricated. t2's static-IP rule has no age threshold.
        "created_at": None,
        "last_activity_at": None,
        "attached_to": attached_to,
        "monthly_cost_estimate": 0.0 if attached_to else ELASTIC_IP_UNASSOCIATED_MONTHLY,
        "tags": tags_of(raw),
        "raw_ref": f"aws://ec2/{region}/{resource_id}",
    }


def resolve_source(source, live: set, resolved: bool):
    """`attached_to` for a snapshot, given what the sweep could actually establish.

    A snapshot is *associated* with what it was taken from, so null here is not "unattached"
    — it is the positive claim *the source is gone*, which is the aged-orphan signal. AWS
    keeps `VolumeId`/`DBInstanceIdentifier` on a snapshot long after the source is deleted,
    so the field is cross-referenced against what this region's sweep actually found.

    That cross-reference is only meaningful if the sweep succeeded. When it did not — a
    partial run, a disabled region — `live` is empty or short, and cross-referencing would
    turn *every* snapshot in the region into "source is gone": a well-formed positive claim
    standing where the truth is simply unknown. So when the source sweep is unresolved the
    provider's own field is taken at face value, which under-claims (a genuinely orphaned
    snapshot reads as attached) rather than fabricating evidence a human would act on.
    Absent `source` is null either way — that is AWS recording no source, not a failed lookup.
    """
    if not source:
        return None
    if not resolved:
        return str(source)
    return str(source) if str(source) in live else None


def normalize_snapshot(raw: dict, region: str, live_volumes: set, resolved: bool = True) -> dict:
    """EBS snapshot. `attached_to` is the source volume, null when the source is gone."""
    gib = raw.get("VolumeSize") or 0
    attached_to = resolve_source(raw.get("VolumeId"), live_volumes, resolved)
    return {
        "resource_id": str(raw.get("SnapshotId")),
        "type": TYPE_SNAPSHOT,
        "name": name_from_tags(raw) or raw.get("Description") or str(raw.get("SnapshotId")),
        "region": region,
        "size": f"{gib}GiB",
        "state": (raw.get("State") or "").lower() or None,
        "created_at": iso(raw.get("StartTime")),
        "last_activity_at": None,
        "attached_to": attached_to,
        "monthly_cost_estimate": round(gib * EBS_SNAPSHOT_GIB_MONTHLY, 2),
        "tags": tags_of(raw),
        "raw_ref": f"aws://ec2/{region}/{raw.get('SnapshotId')}",
    }


def normalize_load_balancer_v2(raw: dict, region: str, targets: list, tags: list) -> dict:
    """ALB/NLB/GWLB. Zero registered targets across every target group is the idle signal."""
    arn = str(raw.get("LoadBalancerArn"))
    lb_type = (raw.get("Type") or "application").lower()
    attached_to = str(targets[0]) if targets else None
    return {
        "resource_id": arn,
        "type": TYPE_LOAD_BALANCER,
        "name": raw.get("LoadBalancerName"),
        "region": region,
        "size": lb_type,
        "state": ((raw.get("State") or {}).get("Code") or "").lower() or None,
        "created_at": iso(raw.get("CreatedTime")),
        "last_activity_at": None,
        "attached_to": attached_to,
        "monthly_cost_estimate": LOAD_BALANCER_MONTHLY.get(
            lb_type, LOAD_BALANCER_MONTHLY_DEFAULT
        ),
        "tags": tags,
        "raw_ref": f"aws://elasticloadbalancing/{region}/{raw.get('LoadBalancerName')}",
    }


def normalize_load_balancer_classic(raw: dict, region: str, tags: list) -> dict:
    """Classic ELB. Backends are registered instances, so an empty list is the idle signal."""
    instances = [
        str(i.get("InstanceId"))
        for i in (raw.get("Instances") or [])
        if isinstance(i, dict) and i.get("InstanceId")
    ]
    name = str(raw.get("LoadBalancerName"))
    return {
        "resource_id": name,
        "type": TYPE_LOAD_BALANCER,
        "name": name,
        "region": region,
        "size": "classic",
        # Classic ELB carries no lifecycle state field; the schema requires `state`, so it
        # is the constant that is true of every listed classic LB rather than a guess.
        "state": "active",
        "created_at": iso(raw.get("CreatedTime")),
        "last_activity_at": None,
        "attached_to": instances[0] if instances else None,
        "monthly_cost_estimate": LOAD_BALANCER_MONTHLY["classic"],
        "tags": tags,
        "raw_ref": f"aws://elasticloadbalancing/{region}/{name}",
    }


def normalize_db_instance(raw: dict, region: str, warnings: list) -> dict:
    """RDS instance. A stopped instance still pays for its allocated storage.

    `attached_to` is null when the instance is stopped-idle (the m2 field-mapping note): a
    stopped database serves nothing, which is the signal t2's stopped-with-storage rule keys
    on. A running instance is attached to itself — it is in service.
    """
    status = (raw.get("DBInstanceStatus") or "").lower()
    stopped = status == "stopped"
    identifier = str(raw.get("DBInstanceIdentifier"))
    gib = raw.get("AllocatedStorage") or 0
    storage_type = (raw.get("StorageType") or "gp2").lower()
    storage_rate = RDS_STORAGE_GIB_MONTHLY.get(storage_type, RDS_STORAGE_GIB_MONTHLY_DEFAULT)
    compute = instance_compute_estimate(raw.get("DBInstanceClass"), stopped, warnings)
    return {
        "resource_id": identifier,
        "type": TYPE_DATABASE,
        "name": identifier,
        "region": region,
        "size": raw.get("DBInstanceClass"),
        "state": STATE_STOPPED if stopped else status or None,
        "created_at": iso(raw.get("InstanceCreateTime")),
        "last_activity_at": None,
        "attached_to": None if stopped else identifier,
        "monthly_cost_estimate": round(compute + gib * storage_rate, 2),
        "tags": tags_of(raw, "TagList"),
        "raw_ref": f"aws://rds/{region}/{identifier}",
    }


def normalize_db_snapshot(
    raw: dict, region: str, live_databases: set, resolved: bool = True
) -> dict:
    """Manual RDS snapshot. `attached_to` is the source DB, null when the source is gone."""
    identifier = str(raw.get("DBSnapshotIdentifier"))
    attached_to = resolve_source(
        raw.get("DBInstanceIdentifier"), live_databases, resolved
    )
    gib = raw.get("AllocatedStorage") or 0
    return {
        "resource_id": identifier,
        "type": TYPE_DATABASE_SNAPSHOT,
        "name": identifier,
        "region": region,
        "size": f"{gib}GiB",
        "state": (raw.get("Status") or "").lower() or None,
        "created_at": iso(raw.get("SnapshotCreateTime")),
        "last_activity_at": None,
        "attached_to": attached_to,
        "monthly_cost_estimate": round(gib * RDS_SNAPSHOT_GIB_MONTHLY, 2),
        "tags": tags_of(raw, "TagList"),
        "raw_ref": f"aws://rds/{region}/{identifier}",
    }


def normalize_cost(
    groups: dict,
    account: str,
    period: str,
    balance_amount: float,
    swept_regions: list,
    ce_metadata: list,
) -> dict:
    """Build the frozen cost snapshot from Cost Explorer's SERVICE groups.

    D4/decision B: CE at `GroupBy=SERVICE` is exactly service granularity, so every line
    carries `resource_id: null` and `region`/`usage_qty`/`usage_unit: null`. Lines are sorted
    descending by amount, matching the DO adapter.
    """
    line_items = [
        {
            "service": service,
            "resource_id": None,
            "region": None,
            "amount": money(amount),
            "usage_qty": None,
            "usage_unit": None,
            "tags": [],
        }
        for service, amount in groups.items()
    ]
    line_items.sort(key=lambda item: (-item["amount"], item["service"]))
    total = round(sum(item["amount"] for item in line_items), 2)
    return {
        "provider": "aws",
        "account": account,
        "period": period,
        "currency": CURRENCY,
        "source_granularity": "service",
        "line_items": line_items,
        "totals": {"amount": total},
        "balance": {
            "month_to_date_balance": money(balance_amount),
            # AWS exposes no account-level balance through Cost Explorer; the schema
            # requires the field, so it is null rather than the month-to-date figure again.
            "account_balance": None,
            "month_to_date_usage": money(balance_amount),
            "generated_at": iso_now(),
        },
        "generated_at": iso_now(),
        "provider_extra": {
            # Opaque CE provenance. `swept_regions` lives here rather than on the inventory
            # envelope because that envelope is frozen at five keys and t2 (d) requires
            # compose/render to stay literally unchanged; surfacing the set in the rendered
            # report is forwarded to t3.
            "results_by_time": ce_metadata,
            "swept_regions": swept_regions,
        },
    }


# ------------------------------------------------------------------------------- fetchers


def fetch_account(clients: AWSClients) -> str:
    """Account id for the snapshot header.

    `sts:GetCallerIdentity` needs no IAM permission, so it works under the least-privilege
    policy. It degrades to "unknown" rather than failing the run: the account id is a header
    field, not a figure anything downstream computes with.
    """
    try:
        return str(clients.client("sts", CE_REGION).get_caller_identity().get("Account"))
    except ClientError as exc:
        if error_code(exc) in AUTH_ERROR_CODES:
            raise_for(clients, exc, "sts:GetCallerIdentity")
        return "unknown"
    except (BotoCoreError, OSError):
        return "unknown"


def enumerate_regions(clients: AWSClients, override: str | None = None) -> list:
    """The regions the sweep covers (decision D — full-region sweep).

    Opted-in regions only: `describe_regions()` without `AllRegions` returns exactly the
    regions the account can call, so a disabled region is never touched. `CLOUDCOST_AWS_REGIONS`
    is the documented override.
    """
    if override:
        regions = [r.strip() for r in override.split(",") if r.strip()]
        if regions:
            return sorted(set(regions))
    try:
        response = clients.client("ec2", clients.bootstrap_region).describe_regions()
    except ClientError as exc:
        raise_for(clients, exc, "ec2:DescribeRegions")
    except (BotoCoreError, OSError) as exc:
        raise_for(clients, exc, "ec2:DescribeRegions")
    names = [
        str(region.get("RegionName"))
        for region in (response.get("Regions") or [])
        if region.get("RegionName")
    ]
    if not names:
        raise AWSAPIError("ec2:DescribeRegions returned no regions")
    return sorted(set(names))


def fetch_costs(clients: AWSClients, account: str, period: str, swept_regions: list) -> dict:
    """Cost Explorer, MONTHLY, GroupBy SERVICE, unblended — every service on the bill."""
    start, end = month_bounds(period)
    client = clients.client("ce", CE_REGION)
    groups: dict = {}
    metadata: list = []
    token = None
    # CE has no paginator (verified: can_paginate("get_cost_and_usage") is False), so the
    # NextPageToken loop is hand-rolled.
    while True:
        kwargs = {
            "TimePeriod": {"Start": start, "End": end},
            "Granularity": "MONTHLY",
            "Metrics": ["UnblendedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": "SERVICE"}],
        }
        if token:
            kwargs["NextPageToken"] = token
        try:
            response = client.get_cost_and_usage(**kwargs)
        except ClientError as exc:
            raise_for(clients, exc, "ce:GetCostAndUsage")
        except (BotoCoreError, OSError) as exc:
            raise_for(clients, exc, "ce:GetCostAndUsage")
        for result in response.get("ResultsByTime") or []:
            entry = {
                "time_period": result.get("TimePeriod"),
                "estimated": result.get("Estimated"),
            }
            # CE repeats the same TimePeriod on every group-page, so a multi-page bill would
            # otherwise emit one identical metadata entry per page.
            if entry not in metadata:
                metadata.append(entry)
            for group in result.get("Groups") or []:
                keys = group.get("Keys") or []
                service = str(keys[0]) if keys else "Unknown"
                amount = ((group.get("Metrics") or {}).get("UnblendedCost") or {}).get("Amount")
                groups[service] = groups.get(service, 0.0) + float(amount or 0.0)
        token = response.get("NextPageToken")
        if not token:
            break

    # Two different zeros, and only one of them is suppressed.
    #
    #   * no `ResultsByTime` at all -> Cost Explorer has nothing for this period (a period
    #     outside the account's CE retention, or a malformed range). Raising means the cost
    #     file is not written, because a $0.00 snapshot would be read as a real zero bill.
    #
    #   * a `ResultsByTime` entry with no `Groups` -> CE *has* the period and reports no
    #     spend in it yet. This is what the first day of a month looks like, and it is also
    #     what a genuinely idle month looks like: the API does not distinguish "$0 so far"
    #     from "$0 total", so neither can this adapter. It sails through as a real $0.00
    #     snapshot, which is the honest reading of what CE said. The consequence — a report
    #     generated on the 1st has an empty cost section — is documented in the runbook and
    #     in docs/m2-t1-implementation-notes.md rather than guarded, because guarding it
    #     would mean inventing a distinction the data does not carry.
    if not metadata:
        raise AWSAPIError(f"no Cost Explorer data for period {period}")
    balance = sum(groups.values())
    return normalize_cost(groups, account, period, balance, swept_regions, metadata)


def fetch_region_inventory(clients: AWSClients, region: str) -> tuple:
    """Every inventory source in one region. A failing source degrades to an error entry."""
    resources: list = []
    errors: list = []
    warnings: list = []

    def guard(source: str, work) -> bool:
        """Run one source. Returns whether it completed — snapshot resolution depends on it."""
        try:
            work()
            return True
        except ClientError as exc:
            code = error_code(exc)
            if code in AUTH_ERROR_CODES:
                raise_for(clients, exc, f"{source} in {region}")
            if code in REGION_DISABLED_CODES:
                warnings.append(f"{source} in {region}: region not enabled ({code})")
                return False
            errors.append(
                {"source": source, "region": region, "error": clients.redact(str(exc))}
            )
            return False
        except (BotoCoreError, OSError) as exc:
            errors.append(
                {"source": source, "region": region, "error": clients.redact(str(exc))}
            )
            return False

    ec2 = clients.client("ec2", region)
    live_volumes: set = set()
    live_databases: set = set()
    #: Whether the sweep that seeds each snapshot cross-reference actually completed. Read by
    #: the snapshot closures below — assigned before they run, see the call order at the end.
    resolved = {"volumes": False, "databases": False}

    def instances():
        for reservation in paginate(ec2, "describe_instances", "Reservations"):
            for raw in reservation.get("Instances") or []:
                resources.append(normalize_instance(raw, region, warnings))

    def volumes():
        for raw in paginate(ec2, "describe_volumes", "Volumes"):
            live_volumes.add(str(raw.get("VolumeId")))
            resources.append(normalize_volume(raw, region))

    def addresses():
        for raw in paginate(ec2, "describe_addresses", "Addresses"):
            resources.append(normalize_address(raw, region))

    def snapshots():
        # owner=self: without it this returns every public snapshot on AWS.
        for raw in paginate(ec2, "describe_snapshots", "Snapshots", OwnerIds=["self"]):
            resources.append(
                normalize_snapshot(raw, region, live_volumes, resolved["volumes"])
            )

    def load_balancers_v2():
        elbv2 = clients.client("elbv2", region)
        balancers = list(paginate(elbv2, "describe_load_balancers", "LoadBalancers"))
        tags = describe_tags(
            elbv2, "ResourceArns", [b.get("LoadBalancerArn") for b in balancers], "ResourceArn"
        )
        for raw in balancers:
            arn = raw.get("LoadBalancerArn")
            targets = []
            for group in paginate(
                elbv2, "describe_target_groups", "TargetGroups", LoadBalancerArn=arn
            ):
                health = elbv2.describe_target_health(
                    TargetGroupArn=group.get("TargetGroupArn")
                )
                targets.extend(
                    (entry.get("Target") or {}).get("Id")
                    for entry in (health.get("TargetHealthDescriptions") or [])
                    if (entry.get("Target") or {}).get("Id")
                )
            resources.append(
                normalize_load_balancer_v2(raw, region, targets, tags.get(str(arn), []))
            )

    def load_balancers_classic():
        elb = clients.client("elb", region)
        balancers = list(
            paginate(elb, "describe_load_balancers", "LoadBalancerDescriptions")
        )
        tags = describe_tags(
            elb,
            "LoadBalancerNames",
            [b.get("LoadBalancerName") for b in balancers],
            "LoadBalancerName",
        )
        for raw in balancers:
            name = str(raw.get("LoadBalancerName"))
            resources.append(
                normalize_load_balancer_classic(raw, region, tags.get(name, []))
            )

    def databases():
        rds = clients.client("rds", region)
        for raw in paginate(rds, "describe_db_instances", "DBInstances"):
            live_databases.add(str(raw.get("DBInstanceIdentifier")))
            resources.append(normalize_db_instance(raw, region, warnings))

    def database_snapshots():
        rds = clients.client("rds", region)
        # manual only: automated snapshots are lifecycle-managed and are not orphans.
        for raw in paginate(
            rds, "describe_db_snapshots", "DBSnapshots", SnapshotType="manual"
        ):
            resources.append(
                normalize_db_snapshot(raw, region, live_databases, resolved["databases"])
            )

    # Ordered: volumes before snapshots and databases before their snapshots, so the source
    # cross-reference sets — and the flags saying whether they can be trusted — are populated
    # before the snapshot normalizers read them.
    resolved["volumes"] = guard("ec2:DescribeVolumes", volumes)
    guard("ec2:DescribeInstances", instances)
    guard("ec2:DescribeAddresses", addresses)
    guard("ec2:DescribeSnapshots", snapshots)
    guard("elbv2:DescribeLoadBalancers", load_balancers_v2)
    guard("elb:DescribeLoadBalancers", load_balancers_classic)
    resolved["databases"] = guard("rds:DescribeDBInstances", databases)
    guard("rds:DescribeDBSnapshots", database_snapshots)

    # Say so, rather than letting the under-claim pass silently: on a partial run the
    # snapshot section of this region is knowingly conservative.
    for kind, source in (("volumes", "EBS"), ("databases", "RDS")):
        if not resolved[kind]:
            warnings.append(
                f"{source} snapshot sources in {region} were not cross-referenced "
                f"(the {kind} sweep did not complete); their attached_to is the provider's "
                f"own field and does not assert that a source is gone"
            )
    return resources, errors, warnings


def fetch_inventory(clients: AWSClients, account: str, period: str, regions: list) -> tuple:
    resources: list = []
    errors: list = []
    warnings: list = []
    for region in regions:
        region_resources, region_errors, region_warnings = fetch_region_inventory(
            clients, region
        )
        resources.extend(region_resources)
        errors.extend(region_errors)
        # An unpriced instance type warns once, not once per region that runs one.
        warnings.extend(w for w in region_warnings if w not in warnings)
    inventory = {
        "provider": "aws",
        "account": account,
        "period": period,
        "resources": resources,
        "generated_at": iso_now(),
    }
    return inventory, errors, warnings


# ----------------------------------------------------------------------------------- main


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="AWS read-only cost/inventory adapter")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--period", default=None, help="YYYY-MM (default: current UTC month)")
    parser.add_argument(
        "--endpoint-url",
        default=None,
        help="override every AWS endpoint (offline tests point this at a local stub)",
    )
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-attempts", type=int, default=4)
    return parser.parse_args(argv)


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    print(json.dumps({"status": "error", "error": message}, indent=2))
    return 1


def main(argv=None) -> int:
    args = parse_args(argv)
    period = args.period or current_period()
    output_dir = Path(args.output_dir)
    errors: list = []
    warnings: list = []

    try:
        warn_shadowing_env()
        clients = AWSClients(
            credentials=load_credentials(),
            endpoint_url=args.endpoint_url,
            timeout=args.timeout,
            max_attempts=args.max_attempts,
        )
        account = fetch_account(clients)
        regions = enumerate_regions(clients, os.environ.get(REGIONS_ENV))
    except (AWSAuthError, AWSAPIError) as exc:
        return fail(str(exc))

    costs = None
    try:
        costs = fetch_costs(clients, account, period, regions)
    except AWSAuthError as exc:
        return fail(str(exc))
    except AWSAPIError as exc:
        errors.append({"source": "ce:GetCostAndUsage", "region": CE_REGION, "error": str(exc)})

    try:
        inventory, inventory_errors, inventory_warnings = fetch_inventory(
            clients, account, period, regions
        )
        errors.extend(inventory_errors)
        warnings.extend(inventory_warnings)
    except AWSAuthError as exc:
        return fail(str(exc))

    written = {}
    if costs is not None:
        written["costs"] = str(write_json(output_dir / f"aws_costs_{period}.json", costs))
    written["inventory"] = str(
        write_json(output_dir / f"aws_inventory_{period}.json", inventory)
    )

    summary = {
        "status": "ok" if not errors else "partial",
        "period": period,
        "files": written,
        # Stated so a capped or broken sweep is visible in the output rather than silent
        # (decision D, no-silent-caps). The set is redeemable against the wire: it is the
        # exact list the sweep iterated.
        "regions_swept": regions,
        "counts": {
            "line_items": len(costs["line_items"]) if costs else 0,
            "resources": len(inventory["resources"]),
            "regions": len(regions),
        },
        "totals": costs["totals"] if costs else None,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
