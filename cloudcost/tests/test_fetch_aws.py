"""Offline tests for the AWS adapter (cloudcost m2, t1).

No credentials, no network: `AWSStub` serves the recorded fixtures over real HTTP and the
adapter reaches it through `--endpoint-url`. Because the requests are really signed, the
suite can assert on what the adapter actually *sent* — which access key, for which region —
rather than on its own test wiring. See `conftest.AWSStub` for why `botocore.stub.Stubber`
was not used.
"""

import datetime
import json
import os
import subprocess
import sys

import botocore.handlers
import botocore.parsers
import pytest

import aws_wire
import fetch_aws
from conftest import (
    ANY_REGION,
    AWS_INVENTORY_OPS,
    CLOUDCOST_ACCESS_KEY,
    CLOUDCOST_SECRET_KEY,
    CLOUDCOST_SESSION_TOKEN,
    FIXTURES,
    POISON_ACCESS_KEY,
    POISON_SECRET_KEY,
    REGION_A,
    REGION_B,
    REGION_C,
    USE_CASE_ROOT,
    load_fixture,
)

PERIOD = "2026-08"

#: The 12 first-class fields every inventory resource carries — the frozen contract.
FROZEN_RESOURCE_FIELDS = {
    "resource_id",
    "type",
    "name",
    "region",
    "size",
    "state",
    "created_at",
    "last_activity_at",
    "attached_to",
    "monthly_cost_estimate",
    "tags",
    "raw_ref",
}

#: The exact top-level key set of the cost snapshot. Asserted as equality, not containment,
#: so a stray addition fails the suite (the m1 t1 Deviation-3 precedent).
FROZEN_COST_KEYS = {
    "provider",
    "account",
    "period",
    "currency",
    "source_granularity",
    "line_items",
    "totals",
    "balance",
    "generated_at",
    "provider_extra",
}


@pytest.fixture
def cloudcost_creds(monkeypatch):
    monkeypatch.setenv("CLOUDCOST_AWS_ACCESS_KEY_ID", CLOUDCOST_ACCESS_KEY)
    monkeypatch.setenv("CLOUDCOST_AWS_SECRET_ACCESS_KEY", CLOUDCOST_SECRET_KEY)
    monkeypatch.setenv("CLOUDCOST_AWS_REGION", REGION_A)
    monkeypatch.delenv("CLOUDCOST_AWS_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDCOST_AWS_REGIONS", raising=False)
    for name in fetch_aws.SHADOWING_ENV:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def poisoned_default_chain(monkeypatch, tmp_path):
    """Poison every arm of boto3's default chain a hermetic test can reach.

    Env credentials, a shared-credentials file, and a profile name. IMDS is disabled rather
    than poisoned — there is no metadata service to answer here, and leaving it enabled would
    add a connection timeout to every test.
    """
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", POISON_ACCESS_KEY)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", POISON_SECRET_KEY)
    credentials = tmp_path / "poison-credentials"
    credentials.write_text(
        f"[default]\naws_access_key_id = {POISON_ACCESS_KEY}\n"
        f"aws_secret_access_key = {POISON_SECRET_KEY}\n"
    )
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(credentials))
    monkeypatch.setenv("AWS_PROFILE", "cloudcost-poison-profile-does-not-exist")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def run_main(stub, tmp_path, period=PERIOD, extra=None):
    argv = [
        "--output-dir",
        str(tmp_path),
        "--period",
        period,
        "--endpoint-url",
        stub.endpoint_url,
        "--max-attempts",
        "1",
    ]
    return fetch_aws.main(argv + (extra or []))


def emitted(tmp_path, kind, period=PERIOD):
    return json.loads((tmp_path / f"aws_{kind}_{period}.json").read_text())


def by_id(inventory):
    return {resource["resource_id"]: resource for resource in inventory["resources"]}


# =============================================================================== normalizers


def test_ec2_instance_normalizes_to_the_canonical_compute_type_and_state():
    raw = load_fixture("aws_ec2_instances_us_east_1_page2")["Reservations"][0]["Instances"][0]
    warnings = []
    resource = fetch_aws.normalize_instance(raw, REGION_A, warnings)

    assert set(resource) == FROZEN_RESOURCE_FIELDS
    assert resource["type"] == "compute_instance"
    assert resource["state"] == "stopped"
    assert resource["region"] == REGION_A
    assert resource["name"] == "old-worker"
    assert resource["created_at"] == "2025-06-20T11:40:00Z"
    assert resource["raw_ref"] == f"aws://ec2/{REGION_A}/i-0aaa3333"
    assert resource["last_activity_at"] is None


def test_a_stopped_instance_bills_no_compute():
    """The provider's cost model lives in the adapter, not in shared machinery.

    DO bills a droplet whether it is on or off; AWS does not bill a stopped instance's
    compute — only its storage, which the inventory carries on the volume rows. Emitting the
    running rate here would put a DO-shaped assumption into a field `detect_orphans.py`
    reads, which is the same class of leak as `STOPPED_STATES` and the `type` vocabulary.
    """
    warnings = []
    assert fetch_aws.instance_compute_estimate("t3.large", stopped=True, warnings=warnings) == 0.0
    assert fetch_aws.instance_compute_estimate("t3.large", stopped=False, warnings=warnings) > 0.0
    assert warnings == []


def test_an_unpriced_instance_type_reports_zero_and_names_itself():
    """Never an invented figure — 0.00 plus a warning that names the type."""
    warnings = []
    assert fetch_aws.instance_compute_estimate("m9.xlarge", False, warnings) == 0.0
    assert len(warnings) == 1
    assert "m9.xlarge" in warnings[0]
    # Warned once per type, not once per resource.
    fetch_aws.instance_compute_estimate("m9.xlarge", False, warnings)
    assert len(warnings) == 1


def test_volume_attachment_and_rate_by_volume_type():
    volumes = load_fixture("aws_ec2_volumes_us_east_1")["Volumes"]
    attached = fetch_aws.normalize_volume(volumes[0], REGION_A)
    unattached = fetch_aws.normalize_volume(volumes[1], REGION_A)

    assert set(attached) == FROZEN_RESOURCE_FIELDS
    assert attached["type"] == "volume"
    assert attached["attached_to"] == "i-0aaa1111"
    assert attached["size"] == "100GiB"
    assert attached["monthly_cost_estimate"] == 8.00  # 100 GiB gp3 @ 0.08
    # `attached_to is null` is the primary orphan signal; an empty Attachments list is it.
    assert unattached["attached_to"] is None
    assert unattached["monthly_cost_estimate"] == 5.00  # 50 GiB gp2 @ 0.10


def test_unassociated_elastic_ip_is_the_orphan_shape_and_bills():
    addresses = load_fixture("aws_ec2_addresses_us_east_1")["Addresses"]
    associated = fetch_aws.normalize_address(addresses[0], REGION_A)
    unassociated = fetch_aws.normalize_address(addresses[1], REGION_A)

    assert associated["type"] == "static_ip"
    assert associated["attached_to"] == "i-0aaa1111"
    assert associated["monthly_cost_estimate"] == 0.0
    assert unassociated["attached_to"] is None
    assert unassociated["state"] == "unassociated"
    assert unassociated["monthly_cost_estimate"] == fetch_aws.ELASTIC_IP_UNASSOCIATED_MONTHLY


def test_an_elastic_ip_on_a_network_interface_is_not_unassociated():
    """An EIP fronting an NLB or NAT gateway is in service; only a fully free one is waste."""
    raw = load_fixture("aws_ec2_addresses_eu_west_1")["Addresses"][0]
    resource = fetch_aws.normalize_address(raw, REGION_B)
    assert resource["attached_to"] == "eni-0bbb1111"
    assert resource["monthly_cost_estimate"] == 0.0


def test_snapshot_source_is_resolved_against_the_volumes_actually_found():
    """AWS keeps VolumeId on a snapshot after the volume is deleted.

    Trusting that field would make every snapshot look live and destroy the aged-orphan
    signal, so the source is cross-referenced against this region's volume sweep.
    """
    snapshots = load_fixture("aws_ec2_snapshots_us_east_1")["Snapshots"]
    live = {"vol-0aaa1111"}
    with_source = fetch_aws.normalize_snapshot(snapshots[0], REGION_A, live)
    orphaned = fetch_aws.normalize_snapshot(snapshots[1], REGION_A, live)

    assert with_source["type"] == "snapshot"
    assert with_source["attached_to"] == "vol-0aaa1111"
    assert orphaned["attached_to"] is None  # VolumeId is set, but the volume is gone
    assert orphaned["monthly_cost_estimate"] == 2.00  # 40 GiB @ 0.05


def test_load_balancers_from_two_different_apis_union_into_one_type():
    v2 = load_fixture("aws_elbv2_load_balancers_us_east_1")["LoadBalancers"]
    classic = load_fixture("aws_elb_load_balancers_us_east_1")["LoadBalancerDescriptions"][0]

    alb = fetch_aws.normalize_load_balancer_v2(v2[0], REGION_A, ["i-0aaa1111"], [])
    nlb = fetch_aws.normalize_load_balancer_v2(v2[1], REGION_A, [], [])
    clb = fetch_aws.normalize_load_balancer_classic(classic, REGION_A, [])

    assert {alb["type"], nlb["type"], clb["type"]} == {"load_balancer"}
    assert alb["attached_to"] == "i-0aaa1111"
    assert nlb["attached_to"] is None  # zero registered targets — the idle signal
    assert clb["attached_to"] is None  # empty Instances[] — the classic idle signal
    assert clb["size"] == "classic"
    assert set(clb) == FROZEN_RESOURCE_FIELDS


def test_rds_instance_lands_in_first_class_fields_with_canonical_state():
    page2 = load_fixture("aws_rds_instances_us_east_1_page2")["DBInstances"][0]
    running = load_fixture("aws_rds_instances_us_east_1_page1")["DBInstances"][0]
    warnings = []

    stopped = fetch_aws.normalize_db_instance(page2, REGION_A, warnings)
    live = fetch_aws.normalize_db_instance(running, REGION_A, warnings)

    assert set(stopped) == FROZEN_RESOURCE_FIELDS
    assert stopped["type"] == "database"
    assert stopped["state"] == "stopped"
    # Stopped-idle serves nothing, so attached_to is null — the signal t2's rule keys on.
    assert stopped["attached_to"] is None
    # Storage only: 200 GiB gp2 @ 0.115. No compute for a stopped database.
    assert stopped["monthly_cost_estimate"] == 23.00
    assert live["attached_to"] == "db-prod-1"
    assert live["monthly_cost_estimate"] == 34.86  # db.t3.small 23.36 + 100 GiB @ 0.115
    assert live["tags"] == ["env=prod"]


def test_load_balancer_tags_are_fetched_so_a_tagged_lb_is_not_reported_untagged(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """r0 F4. Neither DescribeLoadBalancers returns tags; without the extra call every load
    balancer reads as untagged, which makes t3's tag-coverage figure and its top-untagged
    table wrong rather than merely incomplete."""
    assert run_main(full_aws_stub, tmp_path) == 0
    resources = by_id(emitted(tmp_path, "inventory"))

    alb = next(r for r in resources.values() if r["name"] == "alb-prod-1")
    nlb = next(r for r in resources.values() if r["name"] == "nlb-idle-1")
    assert alb["tags"] == ["env=prod", "team=platform"]
    assert nlb["tags"] == []  # genuinely untagged, and still reported as such
    assert resources["clb-legacy-1"]["tags"] == ["env=legacy"]  # the other API's shape
    # Batched, not one call per load balancer.
    assert len(full_aws_stub.calls("elbv2:DescribeTags", REGION_A)) == 1


def test_tag_batching_respects_the_twenty_identifier_limit():
    """`elb`/`elbv2` DescribeTags reject more than 20 identifiers per call."""
    seen = []

    class FakeClient:
        def describe_tags(self, **kwargs):
            batch = kwargs["ResourceArns"]
            seen.append(len(batch))
            return {"TagDescriptions": [{"ResourceArn": a, "Tags": []} for a in batch]}

    out = fetch_aws.describe_tags(
        FakeClient(), "ResourceArns", [f"arn-{i}" for i in range(45)], "ResourceArn"
    )
    assert seen == [20, 20, 5]
    assert len(out) == 45
    # No identifiers, no call at all.
    seen.clear()
    assert fetch_aws.describe_tags(FakeClient(), "ResourceArns", [], "ResourceArn") == {}
    assert seen == []


def test_rds_snapshot_source_is_resolved_like_an_ebs_snapshot():
    snapshots = load_fixture("aws_rds_snapshots_us_east_1")["DBSnapshots"]
    live = {"db-prod-1"}
    kept = fetch_aws.normalize_db_snapshot(snapshots[0], REGION_A, live)
    orphaned = fetch_aws.normalize_db_snapshot(snapshots[1], REGION_A, live)

    assert kept["type"] == "database_snapshot"
    assert kept["attached_to"] == "db-prod-1"
    assert orphaned["attached_to"] is None
    assert orphaned["created_at"] == "2025-01-09T03:00:00Z"


def test_an_unresolved_source_sweep_does_not_claim_the_source_is_gone():
    """r0 F1. `attached_to: null` on a snapshot is a positive claim — *the source is gone*.

    The cross-reference that establishes it is only meaningful when the source sweep
    succeeded. If `DescribeVolumes` errored, `live_volumes` is empty or short, and
    cross-referencing would turn every snapshot in the region into "source is gone" —
    a well-formed positive claim standing where the truth is unknown.
    """
    snapshots = load_fixture("aws_ec2_snapshots_us_east_1")["Snapshots"]
    live = {"vol-0aaa1111"}

    # Resolved: the cross-reference means what it says.
    assert fetch_aws.normalize_snapshot(snapshots[0], REGION_A, live, True)["attached_to"] == (
        "vol-0aaa1111"
    )
    assert fetch_aws.normalize_snapshot(snapshots[1], REGION_A, live, True)["attached_to"] is None

    # Unresolved: the provider's own field is taken at face value. Under-claims (a genuinely
    # orphaned snapshot reads as attached) rather than fabricating evidence.
    assert fetch_aws.normalize_snapshot(snapshots[0], REGION_A, set(), False)["attached_to"] == (
        "vol-0aaa1111"
    )
    assert fetch_aws.normalize_snapshot(snapshots[1], REGION_A, set(), False)["attached_to"] == (
        "vol-deleted-9999"
    )

    # A snapshot AWS records no source for is null either way — that is not a failed lookup.
    assert fetch_aws.resolve_source(None, set(), False) is None
    assert fetch_aws.resolve_source(None, set(), True) is None


def test_a_failed_volume_sweep_leaves_snapshot_sources_unclaimed_and_says_so(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """r0 F1, end to end: the region's volume sweep fails, its snapshots must not read gone."""
    full_aws_stub.fail("ec2:DescribeVolumes", "InternalFailure", region=REGION_A)
    assert run_main(full_aws_stub, tmp_path) == 1
    summary = json.loads(capsys.readouterr().out)
    resources = by_id(emitted(tmp_path, "inventory"))

    # snap-0aaa2222's source really is gone, but this run cannot know that, so it must not
    # assert it. Before the fix both snapshots came out attached_to=null — "source gone".
    assert resources["snap-0aaa1111"]["attached_to"] == "vol-0aaa1111"
    assert resources["snap-0aaa2222"]["attached_to"] == "vol-deleted-9999"
    assert any("were not cross-referenced" in warning for warning in summary["warnings"])
    assert any(REGION_A in warning for warning in summary["warnings"])


def test_a_failed_database_sweep_leaves_rds_snapshot_sources_unclaimed(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """The same defect on the RDS side of the same mechanism."""
    full_aws_stub.fail("rds:DescribeDBInstances", "InternalFailure", region=REGION_A)
    assert run_main(full_aws_stub, tmp_path) == 1
    summary = json.loads(capsys.readouterr().out)
    resources = by_id(emitted(tmp_path, "inventory"))

    assert resources["snap-db-manual-1"]["attached_to"] == "db-prod-1"
    assert resources["snap-db-manual-orphan"]["attached_to"] == "db-deleted-9"
    assert any("RDS snapshot sources" in warning for warning in summary["warnings"])


def test_a_clean_sweep_raises_no_unresolved_warning(full_aws_stub, cloudcost_creds, tmp_path,
                                                    capsys):
    """The warning must be the exception, not background noise on every run."""
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)
    assert not any("were not cross-referenced" in warning for warning in summary["warnings"])


def test_aws_tags_flatten_to_the_normalized_string_list():
    raw = {"Tags": [{"Key": "env", "Value": "prod"}, {"Key": "keep", "Value": "true"},
                    {"Key": "Owner", "Value": ""}]}
    assert fetch_aws.tags_of(raw) == ["env=prod", "keep=true", "Owner"]
    # RDS spells the field TagList.
    assert fetch_aws.tags_of({"TagList": [{"Key": "a", "Value": "b"}]}, "TagList") == ["a=b"]
    assert fetch_aws.tags_of({}) == []


def test_boto3_datetimes_are_normalized_to_the_schema_format():
    """Parsed responses carry real datetimes, which json.dumps cannot serialize."""
    moment = datetime.datetime(2026, 3, 1, 4, 5, 6, tzinfo=datetime.timezone.utc)
    assert fetch_aws.iso(moment) == "2026-03-01T04:05:06Z"
    naive = datetime.datetime(2026, 3, 1, 4, 5, 6)
    assert fetch_aws.iso(naive) == "2026-03-01T04:05:06Z"
    assert fetch_aws.iso(None) is None


# ========================================================================= cost normalization


def test_cost_snapshot_top_level_shape_matches_the_frozen_contract(
    full_aws_stub, cloudcost_creds, tmp_path
):
    assert run_main(full_aws_stub, tmp_path) == 0
    costs = emitted(tmp_path, "costs")

    assert set(costs) == FROZEN_COST_KEYS
    assert costs["provider"] == "aws"
    assert costs["currency"] == "USD"
    assert costs["source_granularity"] == "service"
    assert costs["account"] == "111122223333"
    assert costs["period"] == PERIOD


def test_every_service_on_the_bill_becomes_a_service_level_line_item(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """Decision B: service granularity. Nothing is filtered — Tax and $0.00 services stay."""
    assert run_main(full_aws_stub, tmp_path) == 0
    costs = emitted(tmp_path, "costs")

    services = [item["service"] for item in costs["line_items"]]
    assert "Tax" in services
    assert "AWS Cost Explorer" in services  # the $0.00 service
    assert len(services) == 6
    # Sorted descending by amount, matching the DO adapter.
    assert services[0] == "Amazon Elastic Compute Cloud - Compute"
    assert costs["totals"]["amount"] == 201.74

    for item in costs["line_items"]:
        assert set(item) == {
            "service", "resource_id", "region", "amount", "usage_qty", "usage_unit", "tags",
        }
        # Service granularity means no resource attribution is ever fabricated (D4).
        assert item["resource_id"] is None
        assert item["region"] is None
        assert item["usage_qty"] is None
        assert item["usage_unit"] is None
        assert item["tags"] == []


def test_balance_carries_month_to_date_and_a_null_account_balance(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """AWS exposes no account-level balance; the field is null, not the MTD figure again."""
    assert run_main(full_aws_stub, tmp_path) == 0
    balance = emitted(tmp_path, "costs")["balance"]
    assert balance["month_to_date_balance"] == 201.74
    assert balance["month_to_date_usage"] == 201.74
    assert balance["account_balance"] is None


def test_cost_explorer_is_queried_monthly_grouped_by_service_from_us_east_1(
    full_aws_stub, cloudcost_creds, tmp_path
):
    assert run_main(full_aws_stub, tmp_path) == 0
    calls = full_aws_stub.calls("ce:GetCostAndUsage")
    assert len(calls) == 1
    # CE is a global service pinned to us-east-1. Built with the sweep region instead, it
    # would be queried once per region and the bill would be multiply counted.
    assert calls[0]["region"] == fetch_aws.CE_REGION
    params = calls[0]["params"]
    assert params["Granularity"] == "MONTHLY"
    assert params["Metrics"] == ["UnblendedCost"]
    assert params["GroupBy"] == [{"Type": "DIMENSION", "Key": "SERVICE"}]
    assert params["TimePeriod"] == {"Start": "2026-08-01", "End": "2026-09-01"}


def test_month_bounds_roll_over_the_year():
    assert fetch_aws.month_bounds("2026-08") == ("2026-08-01", "2026-09-01")
    assert fetch_aws.month_bounds("2026-12") == ("2026-12-01", "2027-01-01")


# ============================================================================== region sweep


def test_the_swept_region_set_is_derived_from_describe_regions(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)

    # The enumeration really happened — it is not a hardcoded list.
    assert full_aws_stub.calls("ec2:DescribeRegions")
    assert summary["regions_swept"] == [REGION_C, REGION_B, REGION_A]  # sorted
    assert summary["counts"]["regions"] == 3


def test_the_reported_region_set_is_redeemable_against_the_wire(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """No-silent-caps: the claim must be checkable against an observed fact, not itself.

    A sweep that reports three regions and visits one would pass a self-consistency check;
    it cannot pass this one, because the right-hand side is the set of regions the stub saw
    requests signed for.
    """
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)
    assert set(summary["regions_swept"]) == full_aws_stub.regions_seen("ec2:DescribeVolumes")


def test_inventory_is_the_union_across_regions(full_aws_stub, cloudcost_creds, tmp_path):
    """Resource ids are disjoint per region, so a one-region sweep is missing from the output.

    This is the half a request-log assertion cannot give: it fails on the emitted inventory.
    """
    assert run_main(full_aws_stub, tmp_path) == 0
    inventory = emitted(tmp_path, "inventory")
    resources = by_id(inventory)

    assert len(inventory["resources"]) == 21
    assert {resource["region"] for resource in inventory["resources"]} == {REGION_A, REGION_B}
    assert "i-0aaa1111" in resources and "i-0bbb1111" in resources  # both regions' EC2
    assert "db-prod-1" in resources and "db-eu-1" in resources  # both regions' RDS
    assert resources["i-0bbb1111"]["region"] == REGION_B


def test_an_empty_region_neither_breaks_the_sweep_nor_inflates_it(
    full_aws_stub, cloudcost_creds, tmp_path
):
    assert run_main(full_aws_stub, tmp_path) == 0
    inventory = emitted(tmp_path, "inventory")
    assert REGION_C not in {resource["region"] for resource in inventory["resources"]}
    # It was genuinely swept, not skipped.
    assert REGION_C in full_aws_stub.regions_seen("ec2:DescribeVolumes")


def test_regions_env_override_replaces_the_enumeration(
    full_aws_stub, cloudcost_creds, tmp_path, monkeypatch
):
    monkeypatch.setenv("CLOUDCOST_AWS_REGIONS", f"{REGION_B}, {REGION_B}")
    assert run_main(full_aws_stub, tmp_path) == 0
    inventory = emitted(tmp_path, "inventory")
    assert {resource["region"] for resource in inventory["resources"]} == {REGION_B}
    assert not full_aws_stub.calls("ec2:DescribeRegions")


def test_opted_in_regions_only_no_all_regions_flag(full_aws_stub, cloudcost_creds, tmp_path):
    """`describe_regions()` without AllRegions returns exactly the callable regions."""
    assert run_main(full_aws_stub, tmp_path) == 0
    params = full_aws_stub.calls("ec2:DescribeRegions")[0]["params"]
    assert "AllRegions" not in params


# ================================================================================ pagination


def test_ec2_pages_on_next_token(full_aws_stub, cloudcost_creds, tmp_path):
    assert run_main(full_aws_stub, tmp_path) == 0
    resources = by_id(emitted(tmp_path, "inventory"))
    assert "i-0aaa3333" in resources  # page 2 only
    calls = full_aws_stub.calls("ec2:DescribeInstances", REGION_A)
    assert len(calls) == 2
    assert calls[1]["params"]["NextToken"] == "us-east-1-instances-page-2"


def test_rds_pages_on_marker(full_aws_stub, cloudcost_creds, tmp_path):
    """A different paging idiom from EC2's, so it is covered independently."""
    assert run_main(full_aws_stub, tmp_path) == 0
    resources = by_id(emitted(tmp_path, "inventory"))
    assert "db-stopped-1" in resources  # page 2 only
    calls = full_aws_stub.calls("rds:DescribeDBInstances", REGION_A)
    assert len(calls) == 2
    assert calls[1]["params"]["Marker"] == "us-east-1-db-page-2"


def test_unpageable_operations_still_sweep(full_aws_stub, cloudcost_creds, tmp_path):
    """DescribeAddresses/DescribeRegions/GetCostAndUsage have no paginator (verified).

    A uniform `get_paginator(...)` sweep raises OperationNotPageableError on all three.
    """
    ec2 = fetch_aws.boto3.session.Session(
        aws_access_key_id="x", aws_secret_access_key="y", region_name=REGION_A
    ).client("ec2", endpoint_url=full_aws_stub.endpoint_url)
    assert ec2.can_paginate("describe_addresses") is False
    assert ec2.can_paginate("describe_regions") is False

    assert run_main(full_aws_stub, tmp_path) == 0
    assert "eipalloc-0aaa2222" in by_id(emitted(tmp_path, "inventory"))


# ============================================================================ request shapes


def test_snapshots_are_restricted_to_this_account(full_aws_stub, cloudcost_creds, tmp_path):
    """Without OwnerIds=['self'] this returns every public snapshot on AWS."""
    assert run_main(full_aws_stub, tmp_path) == 0
    params = full_aws_stub.calls("ec2:DescribeSnapshots", REGION_A)[0]["params"]
    assert params["Owner.1"] == "self"


def test_only_manual_rds_snapshots_are_swept(full_aws_stub, cloudcost_creds, tmp_path):
    """Automated snapshots are lifecycle-managed and are not orphans."""
    assert run_main(full_aws_stub, tmp_path) == 0
    params = full_aws_stub.calls("rds:DescribeDBSnapshots", REGION_A)[0]["params"]
    assert params["SnapshotType"] == "manual"


def test_every_call_is_a_read(full_aws_stub, cloudcost_creds, tmp_path):
    """Read-only by construction: no request may name a mutating action."""
    assert run_main(full_aws_stub, tmp_path) == 0
    for request in full_aws_stub.requests:
        assert request["action"].startswith(("Describe", "Get", "List")), request["action"]


# ======================================================================= default-chain guard


def test_adapter_authenticates_with_cloudcost_creds_not_the_poisoned_default_chain(
    full_aws_stub, cloudcost_creds, poisoned_default_chain, tmp_path
):
    """The milestone's poison guard (§t1), made real by the stub being the auth oracle.

    Every arm of boto3's default chain a hermetic test can reach is set to a decoy. If the
    adapter ever consulted the chain it would sign with `POISON_ACCESS_KEY`, the stub would
    answer 403 InvalidClientTokenId, and the run would fail. A green run therefore proves
    the fallback did not happen — which is only true because `AWSStub` rejects an unexpected
    key. Against a permissive stub this assertion would pass either way.
    """
    assert run_main(full_aws_stub, tmp_path) == 0

    assert full_aws_stub.access_keys_seen() == {CLOUDCOST_ACCESS_KEY}
    assert POISON_ACCESS_KEY not in json.dumps(full_aws_stub.requests)


def test_the_stub_really_rejects_a_foreign_key(full_aws_stub, cloudcost_creds, tmp_path):
    """The check on the check: prove the oracle has teeth before trusting the guard above."""
    full_aws_stub.expected_access_key = "AKIASOMETHINGELSE000"
    assert run_main(full_aws_stub, tmp_path) == 1


def test_a_stray_aws_profile_does_not_break_a_correctly_credentialed_run(
    full_aws_stub, cloudcost_creds, monkeypatch, tmp_path
):
    """boto3 resolves the profile before the explicit credentials.

    With `AWS_PROFILE` naming a profile that does not exist, a plain
    `boto3.session.Session(aws_access_key_id=..., ...)` raises ProfileNotFound from
    `get_scoped_config` — before it ever looks at the keys it was handed. The operator's
    workstation legitimately carries `AWS_PROFILE`, so without neutralizing it the adapter
    would fail on a perfectly good credential. Verified against boto3 1.43.14.
    """
    monkeypatch.setenv("AWS_PROFILE", "cloudcost-poison-profile-does-not-exist")
    assert run_main(full_aws_stub, tmp_path) == 0


def test_missing_cloudcost_credentials_raise_rather_than_falling_back(monkeypatch):
    monkeypatch.delenv("CLOUDCOST_AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("CLOUDCOST_AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", POISON_ACCESS_KEY)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", POISON_SECRET_KEY)

    with pytest.raises(fetch_aws.AWSAuthError) as excinfo:
        fetch_aws.load_credentials()
    message = str(excinfo.value)
    assert "CLOUDCOST_AWS_ACCESS_KEY_ID" in message
    assert POISON_ACCESS_KEY not in message


def test_shadowing_credentials_are_named_never_valued(monkeypatch, capsys):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", POISON_ACCESS_KEY)
    monkeypatch.setenv("AWS_PROFILE", "personal")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)

    present = fetch_aws.warn_shadowing_env()
    err = capsys.readouterr().err

    assert set(present) == {"AWS_ACCESS_KEY_ID", "AWS_PROFILE"}
    assert "AWS_ACCESS_KEY_ID" in err and "IGNORED" in err
    assert POISON_ACCESS_KEY not in err
    assert "personal" not in err


def test_the_session_token_is_used_when_supplied(full_aws_stub, cloudcost_creds, monkeypatch,
                                                 tmp_path):
    monkeypatch.setenv("CLOUDCOST_AWS_SESSION_TOKEN", CLOUDCOST_SESSION_TOKEN)
    assert run_main(full_aws_stub, tmp_path) == 0
    tokens = {
        request["headers"].get("X-Amz-Security-Token") for request in full_aws_stub.requests
    }
    assert tokens == {CLOUDCOST_SESSION_TOKEN}


# ================================================================================ leak guard


def test_auth_failure_does_not_leak_credentials_to_stdout_or_stderr(aws_stub, tmp_path):
    """A real 403 driven through the CLI as a subprocess — both streams captured."""
    aws_stub.expected_access_key = "AKIASOMETHINGELSE000"
    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLOUDCOST_AWS_ACCESS_KEY_ID": CLOUDCOST_ACCESS_KEY,
        "CLOUDCOST_AWS_SECRET_ACCESS_KEY": CLOUDCOST_SECRET_KEY,
        "CLOUDCOST_AWS_REGION": REGION_A,
        "AWS_EC2_METADATA_DISABLED": "true",
    }
    result = subprocess.run(
        [
            sys.executable,
            "scripts/fetch_aws.py",
            "--output-dir",
            str(tmp_path),
            "--period",
            PERIOD,
            "--endpoint-url",
            aws_stub.endpoint_url,
            "--max-attempts",
            "1",
        ],
        cwd=USE_CASE_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    for stream in (result.stdout, result.stderr):
        assert CLOUDCOST_ACCESS_KEY not in stream
        assert CLOUDCOST_SECRET_KEY not in stream
    # The variable's *name* must appear, so the operator knows what to fix.
    assert "CLOUDCOST_AWS_ACCESS_KEY_ID" in result.stderr


def test_emitted_files_never_contain_the_credentials(
    full_aws_stub, cloudcost_creds, monkeypatch, tmp_path
):
    monkeypatch.setenv("CLOUDCOST_AWS_SESSION_TOKEN", CLOUDCOST_SESSION_TOKEN)
    assert run_main(full_aws_stub, tmp_path) == 0
    for kind in ("costs", "inventory"):
        text = (tmp_path / f"aws_{kind}_{PERIOD}.json").read_text()
        assert CLOUDCOST_ACCESS_KEY not in text
        assert CLOUDCOST_SECRET_KEY not in text
        assert CLOUDCOST_SESSION_TOKEN not in text


def test_the_secret_key_never_reaches_the_wire(full_aws_stub, cloudcost_creds, tmp_path):
    """SigV4 transmits the key *id* in the credential scope and signs with the secret.

    The AWS-shaped counterpart of m1's bearer-token assertion: the id must be observable
    (that is what makes the poison guard checkable) and the secret must never be.
    """
    assert run_main(full_aws_stub, tmp_path) == 0
    wire = json.dumps(full_aws_stub.requests)
    assert CLOUDCOST_ACCESS_KEY in wire
    assert CLOUDCOST_SECRET_KEY not in wire


def test_the_client_repr_does_not_carry_credentials():
    clients = fetch_aws.AWSClients(
        {
            "access_key_id": CLOUDCOST_ACCESS_KEY,
            "secret_access_key": CLOUDCOST_SECRET_KEY,
            "session_token": None,
            "region": REGION_A,
        }
    )
    assert CLOUDCOST_ACCESS_KEY not in repr(clients)
    assert CLOUDCOST_SECRET_KEY not in repr(clients)
    assert clients.redact(f"boom {CLOUDCOST_SECRET_KEY} bang") == "boom *** bang"


# ============================================================================== degradation


def test_one_failing_source_degrades_to_partial_and_names_its_region(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    full_aws_stub.fail("rds:DescribeDBInstances", "InternalFailure", region=REGION_B)
    assert run_main(full_aws_stub, tmp_path) == 1
    summary = json.loads(capsys.readouterr().out)

    assert summary["status"] == "partial"
    assert len(summary["errors"]) == 1
    assert summary["errors"][0]["source"] == "rds:DescribeDBInstances"
    assert summary["errors"][0]["region"] == REGION_B
    # The rest of the sweep still landed.
    resources = by_id(emitted(tmp_path, "inventory"))
    assert "db-prod-1" in resources
    assert "db-eu-1" not in resources


def test_a_missing_cost_period_degrades_but_still_writes_the_inventory(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """A zero bill would read as a real $0.00 month, so no cost file is written at all."""
    full_aws_stub.route("ce:GetCostAndUsage", "aws_ce_cost_and_usage_empty")
    assert run_main(full_aws_stub, tmp_path) == 1
    summary = json.loads(capsys.readouterr().out)

    assert summary["status"] == "partial"
    assert "costs" not in summary["files"]
    assert summary["totals"] is None
    assert (tmp_path / f"aws_inventory_{PERIOD}.json").exists()
    assert not (tmp_path / f"aws_costs_{PERIOD}.json").exists()


def test_a_period_cost_explorer_reports_no_spend_in_yet_is_a_real_zero_bill(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """r0 F2. The two zeros are different shapes and only one of them is suppressed.

    `ResultsByTime: []`   -> CE has nothing for the period; the cost file is withheld,
                             because a $0.00 snapshot would be read as a real zero bill.
    `ResultsByTime: [{}]`  -> CE *has* the period and reports no spend in it. This is what
                             the first day of a month looks like, and it is also what a
                             genuinely idle month looks like; the API does not distinguish
                             them, so neither can this adapter. It sails through as a real
                             $0.00 snapshot.

    This is the shape that actually occurred on the live 2026-08 run, so it is the shape the
    suite has to pin — asserting the intended behaviour, not whichever empty CE happened to
    return.
    """
    full_aws_stub.route("ce:GetCostAndUsage", "aws_ce_cost_and_usage_zero_groups")
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["status"] == "ok"
    assert summary["counts"]["line_items"] == 0
    assert summary["totals"] == {"amount": 0.0}
    costs = emitted(tmp_path, "costs")  # written, deliberately
    assert costs["line_items"] == []
    assert costs["balance"]["month_to_date_balance"] == 0.0
    # The period CE reported on is still on the record, which is what distinguishes this
    # from the withheld case for anyone reading the snapshot afterwards.
    assert costs["provider_extra"]["results_by_time"][0]["time_period"]["Start"] == "2026-08-01"


def test_cost_explorer_page_metadata_is_deduplicated(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """r0 F3. CE repeats the same TimePeriod on every group-page."""
    full_aws_stub.sequence(
        "ce:GetCostAndUsage",
        ["aws_ce_cost_and_usage_page1", "aws_ce_cost_and_usage_page2"],
    )
    assert run_main(full_aws_stub, tmp_path) == 0
    costs = emitted(tmp_path, "costs")

    assert len(full_aws_stub.calls("ce:GetCostAndUsage")) == 2
    assert len(costs["provider_extra"]["results_by_time"]) == 1
    # Both pages' groups are still summed — dedup is metadata-only.
    services = {item["service"] for item in costs["line_items"]}
    assert "AWS Secrets Manager" in services  # page 2 only
    assert costs["totals"]["amount"] == 205.88  # 201.74 + 4.14


def test_an_auth_failure_is_fatal_and_writes_nothing(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    full_aws_stub.fail("ec2:DescribeRegions", "AuthFailure", status=403)
    assert run_main(full_aws_stub, tmp_path) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"
    assert not list(tmp_path.glob("*.json"))


def test_a_region_the_account_cannot_call_warns_rather_than_erroring(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """OptInRequired is a disabled region, not a broken credential and not a lost source."""
    full_aws_stub.fail("ec2:DescribeVolumes", "OptInRequired", status=403, region=REGION_C)
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "ok"
    assert any(REGION_C in warning for warning in summary["warnings"])


def test_a_missing_iam_permission_is_an_error_not_a_region_warning(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """`UnauthorizedOperation` is a policy gap, not a disabled region.

    Reporting it the way `OptInRequired` is reported would let a missing `ec2:Describe*`
    produce an empty inventory on a green run, under a reason that reads plausibly and is
    wrong — a well-formed answer where a gap exists.
    """
    full_aws_stub.fail(
        "ec2:DescribeVolumes", "UnauthorizedOperation", status=403, region=REGION_A
    )
    assert run_main(full_aws_stub, tmp_path) == 1
    summary = json.loads(capsys.readouterr().out)

    assert summary["status"] == "partial"
    assert summary["errors"][0]["source"] == "ec2:DescribeVolumes"
    assert not any("not enabled" in warning for warning in summary["warnings"])


def test_the_account_id_degrades_rather_than_failing_the_run(
    full_aws_stub, cloudcost_creds, tmp_path
):
    full_aws_stub.fail("sts:GetCallerIdentity", "InternalFailure")
    assert run_main(full_aws_stub, tmp_path) == 0
    assert emitted(tmp_path, "costs")["account"] == "unknown"


# ============================================================================ emitted shapes


def test_every_resource_carries_exactly_the_frozen_field_set(
    full_aws_stub, cloudcost_creds, tmp_path
):
    assert run_main(full_aws_stub, tmp_path) == 0
    inventory = emitted(tmp_path, "inventory")

    assert set(inventory) == {"provider", "account", "period", "resources", "generated_at"}
    assert inventory["provider"] == "aws"
    for resource in inventory["resources"]:
        assert set(resource) == FROZEN_RESOURCE_FIELDS
        assert isinstance(resource["resource_id"], str)
        assert isinstance(resource["monthly_cost_estimate"], float)
        assert isinstance(resource["tags"], list)
        assert resource["region"]  # a real value, never null, for every AWS resource
        assert resource["raw_ref"].startswith("aws://")
        # Populating last_activity_at would make t2's recency modifier live, and its window
        # has an unfixed one-sided bound (m1 open item). Left null at m2 (§t1).
        assert resource["last_activity_at"] is None


def test_the_type_vocabulary_is_canonical_not_provider_flavoured(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """`type` is schema-level, the same seam `state` occupies.

    `detect_orphans.py` keys its rules on these values, so a provider-flavoured one here
    (`droplet` for an EC2 instance) would put provider vocabulary inside shared machinery.
    `fetch_do.py` is renamed onto the same values at t2 (a').
    """
    assert run_main(full_aws_stub, tmp_path) == 0
    types = {resource["type"] for resource in emitted(tmp_path, "inventory")["resources"]}

    assert types == {
        "compute_instance",
        "volume",
        "static_ip",
        "snapshot",
        "load_balancer",
        "database",
        "database_snapshot",
    }
    assert "droplet" not in types
    assert "reserved_ip" not in types


def test_stopped_compute_uses_the_canonical_state(full_aws_stub, cloudcost_creds, tmp_path):
    """`detect_orphans.STOPPED_STATES` shrinks to `{"stopped"}` at t2 (a)."""
    assert run_main(full_aws_stub, tmp_path) == 0
    resources = by_id(emitted(tmp_path, "inventory"))
    assert resources["i-0aaa3333"]["state"] == "stopped"
    assert resources["db-stopped-1"]["state"] == "stopped"
    assert fetch_aws.STATE_STOPPED == "stopped"


def test_the_unpriced_instance_warning_reaches_the_stdout_summary(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)
    assert len(summary["warnings"]) == 1
    assert "m9.xlarge" in summary["warnings"][0]
    assert by_id(emitted(tmp_path, "inventory"))["i-0aaa2222"]["monthly_cost_estimate"] == 0.0


def test_the_swept_region_set_is_recorded_in_the_cost_snapshot(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """It lives under `provider_extra`, the block downstream must not key on generically.

    The frozen inventory envelope is five keys and t2 (d) holds compose/render unchanged, so
    this is the only contract-legal home for it. Surfacing it in the rendered report is a t3
    decision (see docs/m2-t1-implementation-notes.md).
    """
    assert run_main(full_aws_stub, tmp_path) == 0
    extra = emitted(tmp_path, "costs")["provider_extra"]
    assert extra["swept_regions"] == [REGION_C, REGION_B, REGION_A]
    assert extra["results_by_time"][0]["time_period"]["Start"] == "2026-08-01"


def test_the_stdout_summary_keeps_the_orchestrator_contract(
    full_aws_stub, cloudcost_creds, tmp_path, capsys
):
    """t3's orchestrator reads `files.costs` / `files.inventory` / `period` off this JSON."""
    assert run_main(full_aws_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["status"] == "ok"
    assert summary["period"] == PERIOD
    assert summary["files"]["costs"].endswith(f"aws_costs_{PERIOD}.json")
    assert summary["files"]["inventory"].endswith(f"aws_inventory_{PERIOD}.json")
    assert summary["counts"]["resources"] == 21
    assert summary["errors"] == []


# ========================================================================== encoder pinning


def test_every_fixture_round_trips_through_botocore():
    """The wire encoder is pinned by botocore's own parser, not by trust.

    Every AWS fixture is serialized by `aws_wire`, handed to the real botocore parser, and
    compared to the fixture it came from. If the encoder is wrong this is red before any
    adapter test is — so a green adapter test cannot be an artifact of a lenient encoder.
    """
    operations = {
        "aws_sts_caller_identity": ("sts", "GetCallerIdentity"),
        "aws_ec2_regions": ("ec2", "DescribeRegions"),
        "aws_ec2_regions_with_disabled": ("ec2", "DescribeRegions"),
        "aws_ec2_instances_us_east_1_page1": ("ec2", "DescribeInstances"),
        "aws_ec2_instances_us_east_1_page2": ("ec2", "DescribeInstances"),
        "aws_ec2_instances_eu_west_1": ("ec2", "DescribeInstances"),
        "aws_ec2_volumes_us_east_1": ("ec2", "DescribeVolumes"),
        "aws_ec2_volumes_eu_west_1": ("ec2", "DescribeVolumes"),
        "aws_ec2_addresses_us_east_1": ("ec2", "DescribeAddresses"),
        "aws_ec2_addresses_eu_west_1": ("ec2", "DescribeAddresses"),
        "aws_ec2_snapshots_us_east_1": ("ec2", "DescribeSnapshots"),
        "aws_elbv2_load_balancers_us_east_1": ("elbv2", "DescribeLoadBalancers"),
        "aws_elbv2_target_groups_alb": ("elbv2", "DescribeTargetGroups"),
        "aws_elbv2_target_groups_nlb": ("elbv2", "DescribeTargetGroups"),
        "aws_elbv2_target_health_alb": ("elbv2", "DescribeTargetHealth"),
        "aws_elbv2_target_health_empty": ("elbv2", "DescribeTargetHealth"),
        "aws_elbv2_tags_us_east_1": ("elbv2", "DescribeTags"),
        "aws_elb_load_balancers_us_east_1": ("elb", "DescribeLoadBalancers"),
        "aws_elb_tags_us_east_1": ("elb", "DescribeTags"),
        "aws_rds_instances_us_east_1_page1": ("rds", "DescribeDBInstances"),
        "aws_rds_instances_us_east_1_page2": ("rds", "DescribeDBInstances"),
        "aws_rds_instances_eu_west_1": ("rds", "DescribeDBInstances"),
        "aws_rds_snapshots_us_east_1": ("rds", "DescribeDBSnapshots"),
        "aws_ce_cost_and_usage": ("ce", "GetCostAndUsage"),
        "aws_ce_cost_and_usage_empty": ("ce", "GetCostAndUsage"),
        "aws_ce_cost_and_usage_zero_groups": ("ce", "GetCostAndUsage"),
        "aws_ce_cost_and_usage_page1": ("ce", "GetCostAndUsage"),
        "aws_ce_cost_and_usage_page2": ("ce", "GetCostAndUsage"),
        # t4's optimization spike. These carry the encoder into three shapes the core sweep
        # never exercised: rest-xml (s3), a second and third json target prefix (ecr,
        # secretsmanager), and the one service whose advertised protocol is not the protocol
        # botocore parses with (cloudwatch — see aws_wire._protocol).
        "aws_s3_list_buckets": ("s3", "ListBuckets"),
        "aws_s3_lifecycle_cc_assets": ("s3", "GetBucketLifecycleConfiguration"),
        "aws_s3_multipart_cc_logs": ("s3", "ListMultipartUploads"),
        "aws_s3_multipart_empty": ("s3", "ListMultipartUploads"),
        "aws_ecr_repositories": ("ecr", "DescribeRepositories"),
        "aws_ecr_images_cc_worker": ("ecr", "DescribeImages"),
        "aws_ecr_images_cc_api": ("ecr", "DescribeImages"),
        "aws_ecr_lifecycle_cc_api": ("ecr", "GetLifecyclePolicy"),
        "aws_secretsmanager_secrets": ("secretsmanager", "ListSecrets"),
        "aws_cloudwatch_metrics_cc_assets": ("cloudwatch", "GetMetricData"),
        "aws_cloudwatch_metrics_cc_logs": ("cloudwatch", "GetMetricData"),
        "aws_cloudwatch_metrics_cc_empty": ("cloudwatch", "GetMetricData"),
        "aws_cloudwatch_metrics_cc_unknown": ("cloudwatch", "GetMetricData"),
    }
    # GetBucketLocation is excluded here and pinned separately: botocore parses it with a
    # bespoke response handler rather than from the output shape, so the generic loop below
    # would assert against a parser that never runs in production.
    location_fixtures = ("aws_s3_location_us_east_1", "aws_s3_location_eu_west_1")
    # Nothing may be added to fixtures/ and quietly skipped by this check.
    on_disk = {path.stem for path in FIXTURES.glob("aws_*.json")}
    assert on_disk == set(operations) | set(location_fixtures)

    def normalize(value):
        if isinstance(value, dict):
            return {k: normalize(v) for k, v in value.items() if not k.startswith("_")}
        if isinstance(value, list):
            return [normalize(v) for v in value]
        if isinstance(value, datetime.datetime):
            return value.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return value

    for name, (service, action) in sorted(operations.items()):
        fixture = load_fixture(name)
        model = aws_wire.MODELS[service]
        body, _ = aws_wire.encode(service, action, fixture)
        parsed = botocore.parsers.create_parser(aws_wire._protocol(model)).parse(
            {"status_code": 200, "headers": {}, "body": body},
            model.operation_model(action).output_shape,
        )
        parsed.pop("ResponseMetadata", None)
        assert normalize(parsed) == normalize(fixture), name


class _RawResponse:
    """The two attributes `parse_get_bucket_location` touches: a non-None `raw`, and `content`.

    Deliberately not a real `AWSResponse` — that reads its body by streaming from `raw`, so
    constructing one around a bytestring means reimplementing a stream just to hand back the
    bytes we already hold.
    """

    def __init__(self, body: bytes) -> None:
        self.raw = object()
        self.content = body


def test_get_bucket_location_round_trips_through_botocores_own_handler():
    """The one hand-written encoder case, pinned by the code that actually consumes it.

    `s3:GetBucketLocation` is not parsed from its output shape: botocore ships
    `handlers.parse_get_bucket_location`, which re-reads the raw body and takes the ROOT
    element's text as the region. So the generic round-trip above would prove nothing about
    this operation — it would exercise a parser production never reaches. Driving the real
    handler is also what pins the us-east-1 convention: that bucket's constraint is the empty
    string on the wire, and the handler hands back None for it.
    """
    for name, expected in (
        ("aws_s3_location_us_east_1", None),
        ("aws_s3_location_eu_west_1", "eu-west-1"),
    ):
        body, _ = aws_wire.encode("s3", "GetBucketLocation", load_fixture(name))
        parsed = {}
        botocore.handlers.parse_get_bucket_location(parsed, _RawResponse(body))
        assert parsed["LocationConstraint"] == expected, name


def test_every_crafted_fixture_documents_what_it_proves():
    """The `_comment` convention from m1's crafted fixtures, kept for the AWS set."""
    for path in sorted(FIXTURES.glob("aws_*.json")):
        payload = json.loads(path.read_text())
        assert "_comment" in payload, path.name
        assert next(iter(payload)) == "_comment", path.name


def test_the_stub_covers_every_operation_the_sweep_makes(
    full_aws_stub, cloudcost_creds, tmp_path
):
    """An unrouted call is a 400, so a silent `[]` cannot be mistaken for an empty region."""
    assert run_main(full_aws_stub, tmp_path) == 0
    exercised = {
        f"{request['service']}:{request['action']}" for request in full_aws_stub.requests
    }
    assert set(AWS_INVENTORY_OPS) <= exercised
    assert ANY_REGION not in full_aws_stub.regions_seen()
