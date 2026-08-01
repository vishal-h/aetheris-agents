#!/usr/bin/env python3
"""Re-record the AWS fixtures from a live account. Operator-run, not collected by pytest.

The committed `aws_*.json` fixtures are parsed API responses — what boto3 hands the adapter —
scrubbed of account-identifying detail. This script is how they are refreshed: it reuses the
adapter's own session factory (so it authenticates exactly the way the adapter does), calls
each operation the sweep makes, scrubs, and writes the files.

Run it under the D2 hermetic prefix, from `cloudcost/`:

    set -a; . ~/.secrets/aws-cloudcost.env; set +a
    env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_PROFILE \\
        AWS_SHARED_CREDENTIALS_FILE=/dev/null \\
        python3 tests/record_aws_fixtures.py --region us-east-1 --out /tmp/recorded

It writes to `--out` (default: a scratch dir), never over `tests/fixtures/` directly — a
recording is reviewed and scrubbed before it replaces a committed fixture. Two things the
reviewer must check before promoting a recording, both learned at m1 t1:

  * The live account may carry none of the shapes the rules key on (no unattached volume, no
    unassociated Elastic IP). Those entries stay synthetic and clearly marked in `_comment`;
    a pure recording would leave the orphan normalizers untested.
  * Scrubbing is allow-list-ish but not exhaustive by construction. Read the diff.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fetch_aws  # noqa: E402

#: Every read the sweep makes, as (fixture stem suffix, service, method, kwargs).
OPERATIONS = (
    ("sts_caller_identity", "sts", "get_caller_identity", {}),
    ("ec2_regions", "ec2", "describe_regions", {}),
    ("ec2_instances", "ec2", "describe_instances", {}),
    ("ec2_volumes", "ec2", "describe_volumes", {}),
    ("ec2_addresses", "ec2", "describe_addresses", {}),
    ("ec2_snapshots", "ec2", "describe_snapshots", {"OwnerIds": ["self"]}),
    ("elbv2_load_balancers", "elbv2", "describe_load_balancers", {}),
    ("elbv2_target_groups", "elbv2", "describe_target_groups", {}),
    ("elb_load_balancers", "elb", "describe_load_balancers", {}),
    ("rds_instances", "rds", "describe_db_instances", {}),
    ("rds_snapshots", "rds", "describe_db_snapshots", {"SnapshotType": "manual"}),
)

#: Patterns replaced wherever they appear in a recorded value. Identity, network and key
#: material only — resource ids and sizes are the point of the recording and are kept.
SCRUB = (
    (re.compile(r"\b\d{12}\b"), "111122223333"),  # account id, incl. inside ARNs
    (re.compile(r"\bAIDA[A-Z0-9]{8,}"), "AIDAEXAMPLEREADONLY01"),  # IAM unique id
    # Defence in depth. A key id should never appear in a Describe response; if one ever
    # did, a recording is the last place it should come to rest.
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{12,}"), "AKIAEXAMPLEKEYID0000"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "203.0.113.1"),  # public IPv4
    (re.compile(r"[\w.-]+\.(?:elb|rds|compute)\.amazonaws\.com"), "host.example.invalid"),
    (re.compile(r"\bvpc-[0-9a-f]+"), "vpc-0000000000000000"),
    (re.compile(r"\bsubnet-[0-9a-f]+"), "subnet-0000000000000000"),
    (re.compile(r"\bsg-[0-9a-f]+"), "sg-0000000000000000"),
    (re.compile(r"\beni-[0-9a-f]+"), "eni-0000000000000000"),
    (re.compile(r"\bkey-[0-9a-f]+"), "key-0000000000000000"),
    (re.compile(r"arn:aws:kms:[^\"\s]+"), "arn:aws:kms:us-east-1:111122223333:key/scrubbed"),
)


def scrub(value):
    if isinstance(value, dict):
        return {key: scrub(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, datetime):
        # The schema's format, and what the fixtures store: botocore parses it back to a
        # datetime, so the round-trip check compares like with like.
        return fetch_aws.iso(value)
    if isinstance(value, str):
        for pattern, replacement in SCRUB:
            value = pattern.sub(replacement, value)
    return value


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Re-record AWS fixtures from a live account")
    parser.add_argument("--region", default=None, help="default: CLOUDCOST_AWS_REGION")
    parser.add_argument("--out", default="recorded")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    fetch_aws.warn_shadowing_env()
    credentials = fetch_aws.load_credentials()
    region = args.region or credentials["region"]
    clients = fetch_aws.AWSClients(credentials)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for suffix, service, method, kwargs in OPERATIONS:
        client = clients.client(service, region)
        try:
            response = getattr(client, method)(**kwargs)
        except Exception as exc:  # noqa: BLE001 - a recording tool reports and continues
            print(f"skip {service}:{method} — {clients.redact(str(exc))}", file=sys.stderr)
            continue
        response.pop("ResponseMetadata", None)
        payload = {
            "_comment": (
                f"RECORDED from {service}:{method} in {region} and scrubbed "
                f"(account id, public IPs, DNS names, VPC/subnet/SG/ENI/KMS ids). "
                f"Replace this line with what the fixture proves before committing."
            ),
            **scrub(response),
        }
        path = out / f"aws_{suffix}_{region.replace('-', '_')}.json"
        path.write_text(json.dumps(payload, indent=2) + "\n")
        print(path)

    # Cost Explorer is global and hand-paged; recorded separately so the period is explicit.
    print(
        "note: aws_ce_cost_and_usage is recorded by running fetch_aws.py itself and lifting "
        "provider_extra.results_by_time — the CE call is paged in the adapter, not here.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
