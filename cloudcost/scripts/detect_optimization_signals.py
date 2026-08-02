#!/usr/bin/env python3
"""Exploratory optimization signals for AWS S3 / ECR / Secrets Manager (cloudcost m2, t4).

**A second lane, not an extension of the first.** `detect_orphans.py` answers "is this
resource abandoned?" over the frozen inventory, and every answer it gives is
confidence-scored. Nothing here is. S3 lifecycle gaps, incomplete multipart uploads, ECR
image accumulation and unread secrets are not orphan-shaped: they are configuration and
housekeeping observations about resources that are, in every case, still in use. Forcing
them through the orphan schema would mean inventing a confidence for a question that has no
abandoned/not-abandoned axis. So this script is separate, its file is separate, its report
section is separate and labelled exploratory, and — decision G — **the core pipeline never
reads it**. `compose_report_data.py` is not touched, which is what keeps t2/t3's "shared
machinery did not change for AWS" negative proof intact.

**Read-only, and narrowly so.** Every call is a `List*`/`Describe*`/`Get*`. The t4 spike IAM
policy grants specific actions rather than families, and this script is written against that
exact list — using a near-neighbour would produce an AccessDenied that reads like a real gap:

  * Bucket size AND emptiness come from `cloudwatch:GetMetricData` over `BucketSizeBytes` and
    `NumberOfObjects`, queried in each bucket's own region. There is no `s3:ListBucket` grant
    and listing objects to derive either is forbidden outright (§t4 Do-not-generate) — the
    metric answers the question.
  * `GetMetricData`, never `get_metric_statistics`: the latter maps to a different IAM action
    (`cloudwatch:GetMetricStatistics`) which is not granted.
  * Secret staleness reads `LastAccessedDate` off `secretsmanager:ListSecrets` itself.
    `DescribeSecret` is neither granted nor needed.
  * `s3:GetLifecycleConfiguration` authorizes `get_bucket_lifecycle_configuration` — S3 drops
    the "Bucket" from the IAM action name.

**Degrade, don't crash — and never silently.** A denied API, an absent service or an empty
account costs the signal class and nothing else; the file is still written and the exit is
still 0 (the repo rule for analysis/reporting scripts). This deliberately differs from
`fetch_aws.py`, where AccessDenied is an `errors[]` entry and a non-zero exit: there a denial
is a real gap in a gating adapter, here the spike actions are explicitly optional and the
orchestrator step is non-gating. The distinction that keeps that honest is `denied[]` versus
`warnings[]` versus `signals[]`. A refused API means that family is **UNKNOWN, not zero**, and
it is recorded as such; a soft degradation that leaves a fact unknown is a warning. Neither is
ever written into `signals[]` as a fake entry, and the report renders both as visible caveats
so a family that was never checked can never read as a family with nothing to report.

**Dollar figures carry their basis or they do not exist.** `monthly_cost_estimate` appears
only where §t4 sanctions it — a bucket's Standard bytes at a published rate, and the flat
per-secret charge — and never without a `rate_basis` naming the rate, unit, source and
`as_of`. A figure without its basis IS the fabricated figure the ticket forbids. Every
dimension the rate table does not cover (an unlisted region; bytes in a storage class held at
no constant) omits the figure and warns naming the dimension, rather than falling back to a
default rate. These are AWS *list* prices, pre-discount, so the figure is a prioritization
signal and not this account's bill — account-specific accuracy (discounts, savings plans,
real per-class rates) is BL-072's scope, not t4's.

Usage:
    python3 scripts/detect_optimization_signals.py --output-dir output/aws --period 2026-08
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from botocore.exceptions import BotoCoreError, ClientError

# The AWS plumbing — explicit-session construction, the `AWS_PROFILE` neutralization, region
# enumeration, credential loading and redaction — already exists in `fetch_aws.py` and is
# imported rather than reimplemented. The repo prefers a shared `_helper.py` to a CLI-to-CLI
# import, but lifting these into `scripts/_aws.py` would mean editing `fetch_aws.py`, which
# t4 forbids. Filed to converge when that file is next legitimately edited (the BL-070
# precedent, where compose's duplicated `slug()` was left alone for the same reason).
from fetch_aws import (  # noqa: E402 - conftest/orchestrator put scripts/ on the path
    AUTH_ERROR_CODES,
    REGION_DISABLED_CODES,
    REGIONS_ENV,
    AWSAuthError,
    AWSClients,
    current_period,
    enumerate_regions,
    error_code,
    fetch_account,
    iso,
    iso_now,
    load_credentials,
    paginate,
    warn_shadowing_env,
    write_json,
)

#: This script is the AWS spike. The provider is a constant, not a conditional — there is no
#: `provider == …` branch anywhere in the path (the t3 rule), and the orchestrator hands it
#: `output/{provider}/` exactly as it does every other stage.
PROVIDER = "aws"

#: The six signal names, frozen by the milestone. Anything not in here is not a signal.
SIGNAL_S3_NO_LIFECYCLE = "s3_no_lifecycle_policy"
SIGNAL_S3_INCOMPLETE_MULTIPART = "s3_incomplete_multipart"
SIGNAL_S3_EMPTY_BUCKET = "s3_empty_bucket"
SIGNAL_ECR_NO_LIFECYCLE = "ecr_no_lifecycle_policy"
SIGNAL_ECR_UNTAGGED_IMAGES = "ecr_untagged_image_accumulation"
SIGNAL_SECRET_UNUSED = "secret_unused"

SIGNALS = (
    SIGNAL_S3_NO_LIFECYCLE,
    SIGNAL_S3_INCOMPLETE_MULTIPART,
    SIGNAL_S3_EMPTY_BUCKET,
    SIGNAL_ECR_NO_LIFECYCLE,
    SIGNAL_ECR_UNTAGGED_IMAGES,
    SIGNAL_SECRET_UNUSED,
)

DEFAULT_OLD_IMAGE_DAYS = 90
DEFAULT_SECRET_UNUSED_DAYS = 90
DEFAULT_SIZE_LOOKBACK_DAYS = 3

#: `NoSuchLifecycleConfiguration` is not a failure — it IS the no-lifecycle-policy signal.
#: Same for ECR's spelling. Treating either as an error would turn the finding into a warning
#: and lose it.
NO_LIFECYCLE_CODES = frozenset(
    {"NoSuchLifecycleConfiguration", "LifecyclePolicyNotFoundException"}
)

#: The IAM policy refused the call. The signal family is UNKNOWN, not zero, so this is a
#: `denied[]` entry rather than a warning — a distinction the report surfaces.
DENIED_CODES = frozenset(
    {
        "AccessDenied",
        "AccessDeniedException",
        "UnauthorizedOperation",
        "NotAuthorized",
        "AuthorizationError",
    }
)

# ------------------------------------------------------------------------------ list prices
#
# Static AWS **list** prices, pre-discount. `pricing:GetProducts` is deliberately not used —
# it is not in the ratified read-only policy and adding it would widen the credential's
# surface (the same call t1 made for its own rate table).
#
# The region table is deliberately PARTIAL. An unlisted region omits the figure and warns
# naming the region; it never falls back to another region's rate. That is not a gap to be
# filled in by guessing — a wrong rate silently applied is worse than no rate honestly
# withheld, and the omit path is exercised, not decorative.

S3_STANDARD_USD_PER_GB_MONTH = {
    "us-east-1": 0.023,
    "us-east-2": 0.023,
    "us-west-2": 0.023,
    "us-west-1": 0.026,
    "eu-west-1": 0.023,
    "eu-central-1": 0.0245,
    "sa-east-1": 0.0405,
}

S3_RATE_AS_OF = "2026-08-02"
S3_RATE_SOURCE = (
    "AWS S3 list price, Standard storage, first 50 TB/month tier, pre-discount "
    "(static table in detect_optimization_signals.py; not fetched from pricing:GetProducts, "
    "which the read-only policy does not grant)"
)

#: The flat published per-secret charge. Unlike storage this does not vary by region across
#: the standard partition, so it is one constant rather than a table.
SECRET_USD_PER_MONTH = 0.40
SECRET_RATE_AS_OF = "2026-08-02"
SECRET_RATE_SOURCE = (
    "AWS Secrets Manager list price, per secret per month, pre-discount "
    "(static constant in detect_optimization_signals.py)"
)

#: AWS bills S3 storage per GB where a GB is 2**30 bytes.
BYTES_PER_GB = 1024**3

#: The storage classes `BucketSizeBytes` is published under. CloudWatch has no "all classes"
#: dimension for SIZE (only for object count), and `cloudwatch:ListMetrics` is not granted, so
#: the classes present cannot be discovered — each is queried explicitly instead and the ones
#: the bucket does not use simply come back with no datapoints. Only `StandardStorage` is
#: rateable here; the rest are reported and excluded from the figure.
S3_STORAGE_TYPES = (
    "StandardStorage",
    "IntelligentTieringFAStorage",
    "IntelligentTieringIAStorage",
    "StandardIAStorage",
    "OneZoneIAStorage",
    "ReducedRedundancyStorage",
    "GlacierInstantRetrievalStorage",
    "GlacierStorage",
    "DeepArchiveStorage",
)

RATEABLE_STORAGE_TYPE = "StandardStorage"

#: CloudWatch metric-query ids must match ^[a-z][a-zA-Z0-9_]*$.
OBJECTS_QUERY_ID = "objects"


def size_query_id(storage_type: str) -> str:
    return f"size_{storage_type.lower()}"


# ---------------------------------------------------------------------------------- helpers


def parse_timestamp(value):
    """A boto3 timestamp (or an ISO string) as an aware UTC datetime, or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def resolve_reference_date(value: str | None) -> datetime:
    """The instant ages are measured against.

    Defaults to now, but is a parameter so the offline suite is not wall-clock dependent and
    so the emitted file records what its own age rules were evaluated against — the same
    posture as `detect_orphans.resolve_reference_date`.
    """
    if not value:
        return datetime.now(timezone.utc)
    moment = parse_timestamp(value)
    if moment is None:
        raise ValueError(f"cannot parse --reference-date {value!r}")
    return moment


def age_days(moment, reference: datetime):
    """Whole days between `moment` and `reference`, or None if the timestamp is unusable."""
    parsed = parse_timestamp(moment)
    if parsed is None:
        return None
    return (reference - parsed).days


def gb(size_bytes: float) -> float:
    return round(size_bytes / BYTES_PER_GB, 3)


def signal(service, resource_id, region, name, evidence, note, estimate=None, basis=None):
    """One signal, in the §t4 element shape.

    `monthly_cost_estimate` and `rate_basis` are present together or not at all: the key is
    omitted rather than set to null, and a figure without its basis is unrepresentable here
    by construction rather than by convention.
    """
    entry = {
        "service": service,
        "resource_id": resource_id,
        "region": region,
        "signal": name,
        "evidence": list(evidence),
    }
    if estimate is not None and basis is not None:
        entry["monthly_cost_estimate"] = round(float(estimate), 2)
        entry["rate_basis"] = dict(basis)
    entry["note"] = note
    return entry


def s3_standard_rate(region: str):
    return S3_STANDARD_USD_PER_GB_MONTH.get(region)


def s3_rate_basis(rate: float) -> dict:
    return {
        "rate": rate,
        "unit": "USD/GB-month",
        "source": S3_RATE_SOURCE,
        "as_of": S3_RATE_AS_OF,
    }


LIST_PRICE_NOTE = (
    "List-price estimate for prioritization, not this account's bill — discounts, savings "
    "plans and real per-class rates are out of scope for this exploratory spike."
)


# ------------------------------------------------------------------------------ S3 signals


def read_bucket_metrics(results: list) -> dict:
    """Parsed `GetMetricData` results -> {query id: latest value}, absent when dataless.

    A query with no datapoints is DROPPED rather than defaulted to 0.0, and that is the whole
    point: CloudWatch returns a result object for every query id whether or not the metric has
    data, so "no datapoints" and "zero" are the same shape and different facts. A brand-new
    bucket and an empty bucket are indistinguishable if the absent case is read as zero.
    """
    values = {}
    for result in results or []:
        points = result.get("Values") or []
        if not points:
            continue
        stamps = result.get("Timestamps") or []
        if stamps and len(stamps) == len(points):
            latest = max(zip(stamps, points), key=lambda pair: parse_timestamp(pair[0]))
            values[result.get("Id")] = float(latest[1])
        else:
            values[result.get("Id")] = float(points[0])
    return values


def bucket_size_evidence(metrics: dict) -> tuple:
    """(evidence lines, rateable bytes, unrateable {class: bytes}) for one bucket."""
    lines = []
    rateable = None
    unrateable = {}
    for storage_type in S3_STORAGE_TYPES:
        size = metrics.get(size_query_id(storage_type))
        if size is None or size <= 0:
            continue
        lines.append(f"{storage_type} {gb(size)} GB (CloudWatch BucketSizeBytes)")
        if storage_type == RATEABLE_STORAGE_TYPE:
            rateable = size
        else:
            unrateable[storage_type] = size
    if not lines:
        lines.append("no BucketSizeBytes datapoint published — size unknown")
    return lines, rateable, unrateable


def s3_bucket_signals(bucket, region, has_lifecycle, uploads, metrics, reference, warnings):
    """Every S3 signal for one bucket. Pure: no network, no clock."""
    found = []
    size_lines, rateable, unrateable = bucket_size_evidence(metrics)
    objects = metrics.get(OBJECTS_QUERY_ID)

    for storage_type, size in sorted(unrateable.items()):
        warnings.append(
            f"s3 {bucket}: {gb(size)} GB in {storage_type} is excluded from the cost "
            f"estimate — no published rate is held for that storage class"
        )

    if not has_lifecycle:
        estimate = basis = None
        rate = s3_standard_rate(region)
        if rateable is not None and rate is not None:
            estimate, basis = gb(rateable) * rate, s3_rate_basis(rate)
        elif rateable is not None and rate is None:
            warnings.append(
                f"s3 {bucket}: no published Standard rate is held for {region}, so its "
                f"cost estimate is omitted rather than taken from another region"
            )
        note = (
            "No lifecycle policy, so nothing expires or transitions on a schedule. The "
            "figure is what the Standard bytes cost today, not a saving — what a policy "
            "would save depends on the object age profile, which this spike does not read. "
            + LIST_PRICE_NOTE
        )
        found.append(
            signal(
                "s3",
                bucket,
                region,
                SIGNAL_S3_NO_LIFECYCLE,
                ["no lifecycle configuration (NoSuchLifecycleConfiguration)"] + size_lines,
                note,
                estimate,
                basis,
            )
        )

    if uploads:
        ages = [
            (age_days(upload.get("Initiated"), reference), upload) for upload in uploads
        ]
        oldest = max(
            (pair for pair in ages if pair[0] is not None), key=lambda p: p[0], default=None
        )
        evidence = [f"{len(uploads)} incomplete multipart upload(s)"]
        if oldest is not None:
            evidence.append(
                f"oldest initiated {iso(oldest[1].get('Initiated'))} "
                f"({oldest[0]} days before the reference date), key "
                f"{oldest[1].get('Key')!r}"
            )
        found.append(
            signal(
                "s3",
                bucket,
                region,
                SIGNAL_S3_INCOMPLETE_MULTIPART,
                evidence,
                "Parts of an abandoned upload are billed as storage but are invisible to "
                "object listings. No figure: part sizes need s3:ListParts, which the spike "
                "policy does not grant, so the byte count is genuinely unknown here.",
            )
        )

    if objects is not None and objects == 0:
        found.append(
            signal(
                "s3",
                bucket,
                region,
                SIGNAL_S3_EMPTY_BUCKET,
                ["CloudWatch NumberOfObjects reports 0 objects"] + size_lines,
                "Empty bucket. Storage cost is already nil — the value is tidiness and one "
                "less name to reason about, not a saving.",
            )
        )
    elif objects is None:
        warnings.append(
            f"s3 {bucket}: no NumberOfObjects datapoint published, so whether it is empty "
            f"is unknown — no empty-bucket signal is raised on an absent metric"
        )

    return found


# ----------------------------------------------------------------------------- ECR signals


def ecr_repository_signals(
    repository, region, has_lifecycle, images, reference, old_days, warnings
):
    """Every ECR signal for one repository. Pure.

    No `monthly_cost_estimate` on either: §t4 sanctions a figure for the secret charge and for
    CloudWatch-derived S3 size only. ECR storage has a published rate too, but rating it here
    would be extending the sanctioned set on this script's own authority, so the byte counts
    go in the evidence and the dollars stay out.
    """
    found = []
    name = repository.get("repositoryName")

    if not has_lifecycle:
        found.append(
            signal(
                "ecr",
                name,
                region,
                SIGNAL_ECR_NO_LIFECYCLE,
                [
                    "no lifecycle policy (LifecyclePolicyNotFoundException)",
                    f"{len(images)} image(s) currently stored",
                ],
                "Nothing prunes this repository, so image count grows without bound. "
                "No figure: ECR storage is not one of the two cases §t4 sanctions a dollar "
                "estimate for.",
            )
        )

    untagged = [image for image in images if not image.get("imageTags")]

    # An image whose push timestamp will not parse is counted as UNDATED, never as young.
    # `(age or 0) >= threshold` would silently file it under "recent" and quietly shrink the
    # finding — the same shape as reading an absent CloudWatch datapoint as zero.
    dated, undated = [], []
    for image in images:
        age = age_days(image.get("imagePushedAt"), reference)
        (dated if age is not None else undated).append((age, image))
    aged = [(age, image) for age, image in dated if age >= old_days]
    if undated:
        warnings.append(
            f"ecr {name}: {len(undated)} image(s) have an unreadable imagePushedAt, so "
            f"their age is unknown and they are excluded from the aged count"
        )

    if untagged or aged:
        untagged_bytes = sum(int(image.get("imageSizeInBytes") or 0) for image in untagged)
        evidence = []
        if untagged:
            evidence.append(
                f"{len(untagged)} untagged image(s), {gb(untagged_bytes)} GB total"
            )
        if aged:
            ages = [age for age, _ in aged]
            evidence.append(
                f"{len(aged)} image(s) older than {old_days} days "
                f"(oldest {max(ages)} days, most recent of those {min(ages)} days)"
            )
        found.append(
            signal(
                "ecr",
                name,
                region,
                SIGNAL_ECR_UNTAGGED_IMAGES,
                evidence,
                "Untagged and aged images are the accumulation a lifecycle policy exists to "
                "clear. Untagged does not mean unreferenced — a digest-pinned deployment "
                "still resolves — so this is a prompt to look, not a delete list.",
            )
        )
    return found


# ------------------------------------------------------------------------- Secrets signals


def secret_signal(secret, region, reference, unused_days):
    """The `secret_unused` signal for one secret, or None. Pure."""
    name = secret.get("Name")
    last_accessed = secret.get("LastAccessedDate")
    age = age_days(last_accessed, reference)

    if last_accessed is None:
        evidence = ["no LastAccessedDate — never read since it was created"]
        created = iso(secret.get("CreatedDate"))
        if created:
            evidence.append(f"created {created}")
    elif age is not None and age >= unused_days:
        evidence = [
            f"last accessed {iso(last_accessed)} ({age} days before the reference date, "
            f"threshold {unused_days})"
        ]
    else:
        return None

    return signal(
        "secretsmanager",
        name,
        region,
        SIGNAL_SECRET_UNUSED,
        evidence,
        "A secret bills whether or not anything reads it. AWS reports LastAccessedDate at "
        "day granularity and only for retrievals, so a recently-rotated but never-read "
        "secret still looks unused — confirm before deleting. " + LIST_PRICE_NOTE,
        SECRET_USD_PER_MONTH,
        {
            "rate": SECRET_USD_PER_MONTH,
            "unit": "USD/secret-month",
            "source": SECRET_RATE_SOURCE,
            "as_of": SECRET_RATE_AS_OF,
        },
    )


# ------------------------------------------------------------------------------- collection


class Collector:
    """Runs the reads and records what could not be run.

    `guard` is the single degradation point: an auth failure is fatal (a bad credential is
    misconfiguration, not a thin result), a refusal is a `denied[]` entry, and everything else
    is a warning. In every non-fatal case the caller gets `None` and drops that signal class.
    """

    def __init__(self, clients: AWSClients) -> None:
        self.clients = clients
        self.denied = []
        self.warnings = []

    def guard(self, call: str, region: str, work, absent_codes=frozenset()):
        """(ok, value). `absent_codes` are answers, not failures — see NO_LIFECYCLE_CODES."""
        try:
            return True, work()
        except ClientError as exc:
            code = error_code(exc)
            if code in AUTH_ERROR_CODES:
                raise AWSAuthError(
                    f"AWS rejected the credential on {call}: "
                    f"{self.clients.redact(code)}"
                ) from None
            if code in absent_codes:
                return True, None
            if code in DENIED_CODES:
                self.denied.append({"call": call, "region": region, "code": code})
                return False, None
            if code in REGION_DISABLED_CODES:
                self.warnings.append(f"{call} in {region}: region not enabled ({code})")
                return False, None
            self.warnings.append(
                f"{call} in {region}: {self.clients.redact(str(exc))}"
            )
            return False, None
        except (BotoCoreError, OSError) as exc:
            self.warnings.append(f"{call} in {region}: {self.clients.redact(str(exc))}")
            return False, None


def bucket_metric_queries(bucket: str) -> list:
    """One query per storage class plus the object count — a single GetMetricData call."""
    queries = [
        {
            "Id": size_query_id(storage_type),
            "Label": storage_type,
            "MetricStat": {
                "Metric": {
                    "Namespace": "AWS/S3",
                    "MetricName": "BucketSizeBytes",
                    "Dimensions": [
                        {"Name": "BucketName", "Value": bucket},
                        {"Name": "StorageType", "Value": storage_type},
                    ],
                },
                "Period": 86400,
                "Stat": "Average",
            },
            "ReturnData": True,
        }
        for storage_type in S3_STORAGE_TYPES
    ]
    queries.append(
        {
            "Id": OBJECTS_QUERY_ID,
            "Label": "AllStorageTypes",
            "MetricStat": {
                "Metric": {
                    "Namespace": "AWS/S3",
                    "MetricName": "NumberOfObjects",
                    "Dimensions": [
                        {"Name": "BucketName", "Value": bucket},
                        {"Name": "StorageType", "Value": "AllStorageTypes"},
                    ],
                },
                "Period": 86400,
                "Stat": "Average",
            },
            "ReturnData": True,
        }
    )
    return queries


def collect_s3(collector: Collector, reference, lookback_days: int) -> list:
    """S3 signals across every bucket, each queried in its own region."""
    clients = collector.clients
    ok, response = collector.guard(
        "s3:ListBuckets",
        "global",
        lambda: clients.client("s3", clients.bootstrap_region).list_buckets(),
    )
    if not ok or response is None:
        return []

    start = datetime.now(timezone.utc) if reference is None else reference
    window_start = start.timestamp() - lookback_days * 86400

    found = []
    for entry in response.get("Buckets") or []:
        bucket = entry.get("Name")
        if not bucket:
            continue

        ok, location = collector.guard(
            "s3:GetBucketLocation",
            "global",
            lambda b=bucket: clients.client(
                "s3", clients.bootstrap_region
            ).get_bucket_location(Bucket=b),
        )
        if not ok:
            continue
        # An empty/absent LocationConstraint IS us-east-1 — that bucket's constraint is the
        # empty string on the wire, which botocore's handler reports as None.
        region = (location or {}).get("LocationConstraint") or "us-east-1"

        ok, lifecycle = collector.guard(
            "s3:GetLifecycleConfiguration",
            region,
            lambda b=bucket, r=region: clients.client(
                "s3", r
            ).get_bucket_lifecycle_configuration(Bucket=b),
            absent_codes=NO_LIFECYCLE_CODES,
        )
        if not ok:
            continue
        has_lifecycle = bool((lifecycle or {}).get("Rules"))

        ok, multipart = collector.guard(
            "s3:ListBucketMultipartUploads",
            region,
            lambda b=bucket, r=region: clients.client("s3", r).list_multipart_uploads(
                Bucket=b
            ),
        )
        uploads = (multipart or {}).get("Uploads") or [] if ok else []

        ok, metric_response = collector.guard(
            "cloudwatch:GetMetricData",
            region,
            lambda b=bucket, r=region: clients.client("cloudwatch", r).get_metric_data(
                MetricDataQueries=bucket_metric_queries(b),
                StartTime=datetime.fromtimestamp(window_start, tz=timezone.utc),
                EndTime=start,
            ),
        )
        metrics = (
            read_bucket_metrics((metric_response or {}).get("MetricDataResults"))
            if ok
            else {}
        )
        if not ok:
            collector.warnings.append(
                f"s3 {bucket}: size and object count are unknown, so no empty-bucket "
                f"verdict and no cost estimate are given for it"
            )

        found.extend(
            s3_bucket_signals(
                bucket,
                region,
                has_lifecycle,
                uploads,
                metrics,
                reference,
                collector.warnings,
            )
        )
    return found


def collect_ecr(collector: Collector, region: str, reference, old_days: int) -> list:
    clients = collector.clients
    ok, repositories = collector.guard(
        "ecr:DescribeRepositories",
        region,
        lambda: list(
            paginate(clients.client("ecr", region), "describe_repositories", "repositories")
        ),
    )
    if not ok or not repositories:
        return []

    found = []
    for repository in repositories:
        name = repository.get("repositoryName")
        if not name:
            continue
        ok, policy = collector.guard(
            "ecr:GetLifecyclePolicy",
            region,
            lambda n=name: clients.client("ecr", region).get_lifecycle_policy(
                repositoryName=n
            ),
            absent_codes=NO_LIFECYCLE_CODES,
        )
        if not ok:
            continue
        has_lifecycle = bool((policy or {}).get("lifecyclePolicyText"))

        ok, images = collector.guard(
            "ecr:DescribeImages",
            region,
            lambda n=name: list(
                paginate(
                    clients.client("ecr", region),
                    "describe_images",
                    "imageDetails",
                    repositoryName=n,
                )
            ),
        )
        if not ok:
            continue
        found.extend(
            ecr_repository_signals(
                repository,
                region,
                has_lifecycle,
                images or [],
                reference,
                old_days,
                collector.warnings,
            )
        )
    return found


def collect_secrets(collector: Collector, region: str, reference, unused_days: int) -> list:
    clients = collector.clients
    ok, secrets = collector.guard(
        "secretsmanager:ListSecrets",
        region,
        lambda: list(
            paginate(
                clients.client("secretsmanager", region), "list_secrets", "SecretList"
            )
        ),
    )
    if not ok or not secrets:
        return []
    found = []
    for secret in secrets:
        entry = secret_signal(secret, region, reference, unused_days)
        if entry is not None:
            found.append(entry)
    return found


def detect(clients: AWSClients, account: str, period: str, regions: list, reference, params):
    """The whole spike: S3 globally, ECR and Secrets Manager per region."""
    collector = Collector(clients)
    signals = list(
        collect_s3(collector, reference, params["s3_size_lookback_days"])
    )
    for region in regions:
        signals.extend(
            collect_ecr(collector, region, reference, params["old_image_days"])
        )
        signals.extend(
            collect_secrets(collector, region, reference, params["secret_unused_days"])
        )

    by_signal = {name: 0 for name in SIGNALS}
    for entry in signals:
        by_signal[entry["signal"]] = by_signal.get(entry["signal"], 0) + 1

    return {
        "provider": PROVIDER,
        "account": account,
        "period": period,
        "generated_at": iso_now(),
        "reference_date": reference.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "regions_swept": list(regions),
        "parameters": dict(params),
        "signals": signals,
        "denied": collector.denied,
        "warnings": collector.warnings,
        "totals": {"signals": len(signals), "by_signal": by_signal},
    }


# --------------------------------------------------------------------------------------- CLI


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Exploratory AWS optimization signals (S3 / ECR / Secrets Manager)"
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--period", default=None, help="YYYY-MM (default: current UTC month)")
    parser.add_argument(
        "--reference-date",
        default=None,
        help="YYYY-MM-DD or ISO-8601; age rules run against this (default: now)",
    )
    parser.add_argument(
        "--endpoint-url",
        default=None,
        help="override every AWS endpoint (offline tests point this at a local stub)",
    )
    parser.add_argument("--old-image-days", type=int, default=DEFAULT_OLD_IMAGE_DAYS)
    parser.add_argument("--secret-unused-days", type=int, default=DEFAULT_SECRET_UNUSED_DAYS)
    parser.add_argument(
        "--s3-size-lookback-days", type=int, default=DEFAULT_SIZE_LOOKBACK_DAYS
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
    warn_shadowing_env()

    try:
        credentials = load_credentials()
        reference = resolve_reference_date(args.reference_date)
    except (AWSAuthError, ValueError) as exc:
        return fail(str(exc))

    clients = AWSClients(
        credentials,
        endpoint_url=args.endpoint_url,
        timeout=args.timeout,
        max_attempts=args.max_attempts,
    )
    period = args.period or current_period()
    params = {
        "old_image_days": args.old_image_days,
        "secret_unused_days": args.secret_unused_days,
        "s3_size_lookback_days": args.s3_size_lookback_days,
    }

    try:
        account = fetch_account(clients)
        regions = enumerate_regions(clients, os.environ.get(REGIONS_ENV))
        result = detect(clients, account, period, regions, reference, params)
    except AWSAuthError as exc:
        return fail(str(exc))
    except (ClientError, BotoCoreError, OSError) as exc:
        # Region enumeration is the only read outside `Collector.guard`; losing it means
        # there is no sweep to degrade, so it is reported rather than silently emptied.
        return fail(f"cannot enumerate regions: {clients.redact(str(exc))}")

    path = write_json(
        Path(args.output_dir) / f"optimization_signals_{PROVIDER}_{period}.json", result
    )

    print(
        json.dumps(
            {
                # `partial` records that something could not be read. It is NOT a failure and
                # the exit stays 0: this is an exploratory, non-gating spike whose IAM actions
                # are optional, and the repo rule is that analysis scripts always exit 0.
                "status": "partial" if (result["denied"] or result["warnings"]) else "ok",
                "period": period,
                "file": str(path),
                "regions_swept": result["regions_swept"],
                "totals": result["totals"],
                "denied": result["denied"],
                "warnings": result["warnings"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
