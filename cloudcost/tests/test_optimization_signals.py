"""Offline tests for the optimization-signals spike (cloudcost m2, t4).

No credentials, no network. `AWSStub` serves the recorded fixtures over real HTTP and the
detector reaches it through `--endpoint-url`, so the requests are really signed and the suite
can assert on what was actually sent — including that the spike, like the core adapter, never
falls back to boto3's default credential chain.

Ages are measured against an explicit `--reference-date` throughout. A suite that let them
run off the wall clock would start failing on a date nobody chose.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

import detect_optimization_signals as detector
import fetch_aws
from conftest import (
    CLOUDCOST_ACCESS_KEY,
    CLOUDCOST_SECRET_KEY,
    POISON_ACCESS_KEY,
    POISON_SECRET_KEY,
    REGION_A,
    REGION_B,
    USE_CASE_ROOT,
    load_fixture,
)

PERIOD = "2026-08"

#: Every age in the fixtures is stated relative to this instant, not to today.
REFERENCE = "2026-08-02T00:00:00Z"

SCRIPT = USE_CASE_ROOT / "scripts" / "detect_optimization_signals.py"


@pytest.fixture
def cloudcost_creds(monkeypatch):
    monkeypatch.setenv("CLOUDCOST_AWS_ACCESS_KEY_ID", CLOUDCOST_ACCESS_KEY)
    monkeypatch.setenv("CLOUDCOST_AWS_SECRET_ACCESS_KEY", CLOUDCOST_SECRET_KEY)
    monkeypatch.setenv("CLOUDCOST_AWS_REGION", REGION_A)
    monkeypatch.setenv("CLOUDCOST_AWS_REGIONS", f"{REGION_A},{REGION_B}")
    monkeypatch.delenv("CLOUDCOST_AWS_SESSION_TOKEN", raising=False)
    for name in fetch_aws.SHADOWING_ENV:
        monkeypatch.delenv(name, raising=False)


def run_main(stub, tmp_path, extra=None):
    argv = [
        "--output-dir",
        str(tmp_path),
        "--period",
        PERIOD,
        "--reference-date",
        REFERENCE,
        "--endpoint-url",
        stub.endpoint_url,
        "--max-attempts",
        "1",
    ]
    return detector.main(argv + (extra or []))


def emitted(tmp_path, period=PERIOD):
    return json.loads((tmp_path / f"optimization_signals_aws_{period}.json").read_text())


def signals_of(payload, name):
    return [entry for entry in payload["signals"] if entry["signal"] == name]


def only(payload, name):
    found = signals_of(payload, name)
    assert len(found) == 1, f"expected exactly one {name}, got {len(found)}"
    return found[0]


# ============================================================================ the sweep


def test_the_sweep_writes_the_signals_file_and_prints_its_path(
    optimization_stub, cloudcost_creds, tmp_path, capsys
):
    assert run_main(optimization_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["file"].endswith(f"optimization_signals_aws_{PERIOD}.json")
    assert summary["period"] == PERIOD
    # `enumerate_regions` sorts, so the swept set is alphabetical rather than env order.
    assert summary["regions_swept"] == sorted([REGION_A, REGION_B])
    assert (tmp_path / f"optimization_signals_aws_{PERIOD}.json").exists()


def test_the_envelope_carries_the_documented_fields(
    optimization_stub, cloudcost_creds, tmp_path
):
    """The §t4 envelope, as amended: signals[] plus the honesty half."""
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)

    assert set(payload) == {
        "provider",
        "account",
        "period",
        "generated_at",
        "reference_date",
        "regions_swept",
        "parameters",
        "signals",
        "denied",
        "warnings",
        "totals",
    }
    assert payload["provider"] == "aws"
    assert payload["period"] == PERIOD
    assert payload["reference_date"] == "2026-08-02T00:00:00Z"
    assert payload["parameters"] == {
        "old_image_days": 90,
        "secret_unused_days": 90,
        "s3_size_lookback_days": 3,
    }


def test_every_signal_carries_the_t4_element_shape(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    for entry in emitted(tmp_path)["signals"]:
        assert set(entry) <= {
            "service",
            "resource_id",
            "region",
            "signal",
            "evidence",
            "monthly_cost_estimate",
            "rate_basis",
            "note",
        }
        assert {"service", "resource_id", "region", "signal", "evidence", "note"} <= set(
            entry
        )
        assert entry["signal"] in detector.SIGNALS
        assert entry["evidence"] and all(isinstance(line, str) for line in entry["evidence"])
        assert entry["note"]


def test_the_totals_are_counted_not_asserted(optimization_stub, cloudcost_creds, tmp_path):
    """`totals` is what the report renders, so it is recomputed here from `signals[]`."""
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)

    assert payload["totals"]["signals"] == len(payload["signals"])
    counted = {name: 0 for name in detector.SIGNALS}
    for entry in payload["signals"]:
        counted[entry["signal"]] += 1
    assert payload["totals"]["by_signal"] == counted


def test_no_signal_is_confidence_scored_like_an_orphan_candidate(
    optimization_stub, cloudcost_creds, tmp_path
):
    """Decision G: these are not orphan candidates wearing a different hat.

    §t4 forbids confidence scores dressed up as orphan candidates, so the orphan file's
    scoring vocabulary must appear nowhere in this payload.
    """
    payload = emitted(tmp_path) if run_main(optimization_stub, tmp_path) == 0 else None
    text = json.dumps(payload)
    for forbidden in ("confidence", "base_confidence", "modifiers", "monthly_saving_estimate"):
        assert forbidden not in text


# ============================================================================ S3 signals


def test_a_bucket_without_a_lifecycle_policy_is_flagged_and_one_with_it_is_not(
    optimization_stub, cloudcost_creds, tmp_path
):
    """The error IS the signal: cc-assets answers with rules, the others with 404s."""
    assert run_main(optimization_stub, tmp_path) == 0
    flagged = {
        entry["resource_id"]
        for entry in signals_of(emitted(tmp_path), detector.SIGNAL_S3_NO_LIFECYCLE)
    }
    assert flagged == {"cc-logs", "cc-empty"}


def test_each_bucket_is_measured_in_its_own_region(
    optimization_stub, cloudcost_creds, tmp_path
):
    """cc-logs lives in REGION_B, and its CloudWatch read has to go there.

    A detector that queried one fixed region would find no datapoints for it and silently
    lose both its size and the Glacier warning — which is exactly the failure this asserts
    against, since the stub answers per region.
    """
    assert run_main(optimization_stub, tmp_path) == 0
    regions = {
        entry["resource_id"]: entry["region"]
        for entry in emitted(tmp_path)["signals"]
        if entry["service"] == "s3"
    }
    assert regions["cc-logs"] == REGION_B
    assert regions["cc-empty"] == REGION_A

    metric_regions = {
        request["region"] for request in optimization_stub.calls("cloudwatch:GetMetricData")
    }
    assert metric_regions == {REGION_A, REGION_B}


def test_incomplete_multipart_uploads_are_reported_with_the_oldest_named(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    entry = only(emitted(tmp_path), detector.SIGNAL_S3_INCOMPLETE_MULTIPART)

    assert entry["resource_id"] == "cc-logs"
    assert "2 incomplete multipart upload(s)" in entry["evidence"][0]
    assert "2025-02-14T03:22:11Z" in entry["evidence"][1]
    assert "archive/2025-02-bundle.tar.gz" in entry["evidence"][1]
    # Part sizes need s3:ListParts, which is not granted — so there is no figure to give.
    assert "monthly_cost_estimate" not in entry


def test_a_bucket_with_no_incomplete_uploads_raises_no_multipart_signal(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    flagged = {
        entry["resource_id"]
        for entry in signals_of(emitted(tmp_path), detector.SIGNAL_S3_INCOMPLETE_MULTIPART)
    }
    assert "cc-assets" not in flagged and "cc-empty" not in flagged


def test_an_observed_zero_object_count_is_the_empty_bucket_signal(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    entry = only(emitted(tmp_path), detector.SIGNAL_S3_EMPTY_BUCKET)

    assert entry["resource_id"] == "cc-empty"
    assert "NumberOfObjects reports 0" in entry["evidence"][0]


def test_the_size_question_is_answered_by_the_metric_never_by_listing_objects(
    optimization_stub, cloudcost_creds, tmp_path
):
    """§t4 forbids listing every object where a CloudWatch metric answers size.

    The stub records every request it receives, so this reads the wire rather than the source:
    no `ListObjects` of any generation was ever issued.
    """
    assert run_main(optimization_stub, tmp_path) == 0
    actions = {request["action"] for request in optimization_stub.requests}
    assert not {"ListObjects", "ListObjectsV2", "ListObjectVersions"} & actions
    assert "GetMetricData" in actions


def test_every_call_the_spike_makes_is_a_read(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    for request in optimization_stub.requests:
        action = request["action"] or ""
        assert action.startswith(("List", "Describe", "Get")), action


# ================================================================== dollars and their basis


def test_no_figure_ever_appears_without_its_rate_basis(
    optimization_stub, cloudcost_creds, tmp_path
):
    """The load-bearing pricing invariant, asserted in both directions.

    A `monthly_cost_estimate` without a `rate_basis` IS the fabricated figure §t4 forbids, so
    presence must imply a complete basis; and the sweep must actually produce some figures,
    or this passes vacuously against a payload that priced nothing.
    """
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)

    priced = 0
    for entry in payload["signals"]:
        if "monthly_cost_estimate" in entry:
            priced += 1
            basis = entry["rate_basis"]
            assert set(basis) == {"rate", "unit", "source", "as_of"}
            assert isinstance(basis["rate"], (int, float)) and basis["rate"] > 0
            assert basis["as_of"] and basis["source"]
            assert "list price" in basis["source"].lower()
        else:
            assert "rate_basis" not in entry
    assert priced >= 2, "no figure was produced, so the invariant proved nothing"


def test_the_standard_bytes_are_rated_and_the_glacier_bytes_are_not(
    optimization_stub, cloudcost_creds, tmp_path
):
    """cc-logs holds 100 GB Standard and 50 GB Glacier.

    Rating the total would overstate by more than 2x, so the figure covers the Standard half
    only and the excluded class is named in a warning rather than dropped.
    """
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)
    entry = next(
        e
        for e in signals_of(payload, detector.SIGNAL_S3_NO_LIFECYCLE)
        if e["resource_id"] == "cc-logs"
    )

    assert entry["monthly_cost_estimate"] == pytest.approx(100.0 * 0.023, rel=1e-6)
    assert any("GlacierStorage" in line for line in entry["evidence"])
    assert any(
        "GlacierStorage" in warning and "cc-logs" in warning
        for warning in payload["warnings"]
    ), payload["warnings"]


def test_a_region_with_no_published_rate_omits_the_figure_and_says_so():
    """The other no-silent-caps dimension, unit-tested because no fixture region lacks a rate.

    A fallback to another region's rate is the failure being excluded here — the figure has
    to be absent, and the region has to be named.
    """
    warnings = []
    found = detector.s3_bucket_signals(
        "cc-elsewhere",
        "ap-southeast-4",
        has_lifecycle=False,
        uploads=[],
        metrics={detector.size_query_id("StandardStorage"): 50 * detector.BYTES_PER_GB},
        reference=detector.resolve_reference_date(REFERENCE),
        warnings=warnings,
    )
    entry = next(e for e in found if e["signal"] == detector.SIGNAL_S3_NO_LIFECYCLE)

    assert "monthly_cost_estimate" not in entry
    assert "rate_basis" not in entry
    assert any("ap-southeast-4" in warning for warning in warnings), warnings

    # The failable half: the same bucket in a region that IS in the table gets a figure.
    priced = detector.s3_bucket_signals(
        "cc-elsewhere",
        "us-east-1",
        has_lifecycle=False,
        uploads=[],
        metrics={detector.size_query_id("StandardStorage"): 50 * detector.BYTES_PER_GB},
        reference=detector.resolve_reference_date(REFERENCE),
        warnings=[],
    )
    assert "monthly_cost_estimate" in priced[0]


def test_every_rate_constant_carries_an_as_of():
    """A rate without a date is a rate nobody can check."""
    assert detector.S3_RATE_AS_OF and detector.SECRET_RATE_AS_OF
    assert detector.S3_STANDARD_USD_PER_GB_MONTH
    assert all(rate > 0 for rate in detector.S3_STANDARD_USD_PER_GB_MONTH.values())


def test_ecr_signals_carry_no_dollar_figure(optimization_stub, cloudcost_creds, tmp_path):
    """§t4 sanctions two cases. ECR storage is not one of them, so it stays unpriced."""
    assert run_main(optimization_stub, tmp_path) == 0
    ecr = [entry for entry in emitted(tmp_path)["signals"] if entry["service"] == "ecr"]
    assert ecr
    assert all("monthly_cost_estimate" not in entry for entry in ecr)


# ================================================================== the unknown/zero divide


def test_an_absent_metric_is_unknown_and_never_read_as_an_empty_bucket():
    """The mutation control for the empty-bucket rule.

    `aws_cloudwatch_metrics_cc_unknown` publishes not one datapoint — what a brand-new bucket
    looks like. A detector that read "no datapoints" as zero would raise a false
    `s3_empty_bucket` here, so this fails loudly against that implementation rather than
    merely describing the intent.
    """
    metrics = detector.read_bucket_metrics(
        load_fixture("aws_cloudwatch_metrics_cc_unknown")["MetricDataResults"]
    )
    assert metrics == {}, "a dataless result must not survive as a value"

    warnings = []
    found = detector.s3_bucket_signals(
        "cc-unknown",
        "us-east-1",
        has_lifecycle=True,
        uploads=[],
        metrics=metrics,
        reference=detector.resolve_reference_date(REFERENCE),
        warnings=warnings,
    )
    assert not [e for e in found if e["signal"] == detector.SIGNAL_S3_EMPTY_BUCKET]
    assert any("unknown" in warning for warning in warnings), warnings

    # The failable half: an OBSERVED zero does raise it.
    observed = detector.read_bucket_metrics(
        load_fixture("aws_cloudwatch_metrics_cc_empty")["MetricDataResults"]
    )
    raised = detector.s3_bucket_signals(
        "cc-empty",
        "us-east-1",
        has_lifecycle=True,
        uploads=[],
        metrics=observed,
        reference=detector.resolve_reference_date(REFERENCE),
        warnings=[],
    )
    assert [e for e in raised if e["signal"] == detector.SIGNAL_S3_EMPTY_BUCKET]


# ============================================================================ ECR signals


def test_a_repository_without_a_lifecycle_policy_is_flagged_and_one_with_it_is_not(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    entry = only(emitted(tmp_path), detector.SIGNAL_ECR_NO_LIFECYCLE)
    assert entry["resource_id"] == "cc-worker"
    assert entry["region"] == REGION_A


def test_untagged_and_aged_images_are_counted_from_the_image_list(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    entry = only(emitted(tmp_path), detector.SIGNAL_ECR_UNTAGGED_IMAGES)

    assert entry["resource_id"] == "cc-worker"
    # Three of cc-worker's five images carry no imageTags key at all; the other two are
    # tagged, so this is a count of untagged images and not just a count of images.
    assert "3 untagged image(s)" in entry["evidence"][0]
    assert any("older than 90 days" in line for line in entry["evidence"])


def test_an_image_with_an_unreadable_push_date_is_undated_not_young():
    """`(age or 0) >= threshold` would file an unparseable timestamp under "recent".

    That is the same defect as reading an absent CloudWatch datapoint as zero: it shrinks the
    finding silently. The image must be excluded from the aged count AND warned about, and
    the failable half below shows the same image dated does count.
    """
    reference = detector.resolve_reference_date(REFERENCE)
    broken = {"imageDigest": "sha256:dead", "imagePushedAt": "not-a-date", "imageTags": ["x"]}

    warnings = []
    found = detector.ecr_repository_signals(
        {"repositoryName": "cc-broken"},
        REGION_A,
        has_lifecycle=True,
        images=[broken],
        reference=reference,
        old_days=90,
        warnings=warnings,
    )
    assert found == []
    assert any("unreadable imagePushedAt" in warning for warning in warnings), warnings

    dated = dict(broken, imagePushedAt="2020-01-01T00:00:00Z")
    warnings = []
    found = detector.ecr_repository_signals(
        {"repositoryName": "cc-broken"},
        REGION_A,
        has_lifecycle=True,
        images=[dated],
        reference=reference,
        old_days=90,
        warnings=warnings,
    )
    assert [e for e in found if e["signal"] == detector.SIGNAL_ECR_UNTAGGED_IMAGES]
    assert warnings == []


def test_a_repository_of_tagged_recent_images_raises_nothing(
    optimization_stub, cloudcost_creds, tmp_path
):
    """cc-api is the negative control: a policy, and every image tagged and recent."""
    assert run_main(optimization_stub, tmp_path) == 0
    flagged = {
        entry["resource_id"]
        for entry in emitted(tmp_path)["signals"]
        if entry["service"] == "ecr"
    }
    assert flagged == {"cc-worker"}


# ======================================================================== Secrets signals


def test_a_stale_and_a_never_read_secret_are_both_unused_and_a_fresh_one_is_not(
    optimization_stub, cloudcost_creds, tmp_path
):
    assert run_main(optimization_stub, tmp_path) == 0
    found = {
        entry["resource_id"]: entry
        for entry in signals_of(emitted(tmp_path), detector.SIGNAL_SECRET_UNUSED)
    }

    assert set(found) == {"cc/legacy/api-key", "cc/never-used"}
    assert "last accessed 2025-03-14" in found["cc/legacy/api-key"]["evidence"][0]
    assert "never read" in found["cc/never-used"]["evidence"][0]
    assert found["cc/never-used"]["monthly_cost_estimate"] == 0.40


def test_the_secret_charge_reads_last_accessed_off_the_listing_never_describe_secret(
    optimization_stub, cloudcost_creds, tmp_path
):
    """DescribeSecret is neither granted nor needed — asserted against the wire."""
    assert run_main(optimization_stub, tmp_path) == 0
    actions = {request["action"] for request in optimization_stub.requests}
    assert "ListSecrets" in actions
    assert "DescribeSecret" not in actions


# ======================================================== degradation: denied vs warnings


def test_a_denied_api_costs_its_signal_class_and_nothing_else(
    optimization_stub, cloudcost_creds, tmp_path, capsys
):
    """The spike's IAM actions are optional, so a refusal degrades rather than failing.

    The run still exits 0 and still writes its file — but the refused family is recorded as
    UNKNOWN in `denied[]`, never as an absence of findings.
    """
    optimization_stub.fail(
        "secretsmanager:ListSecrets", "AccessDeniedException", status=400, region=REGION_A
    )
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)

    assert signals_of(payload, detector.SIGNAL_SECRET_UNUSED) == []
    assert {entry["call"] for entry in payload["denied"]} == {"secretsmanager:ListSecrets"}
    assert payload["denied"][0]["code"] == "AccessDeniedException"
    # The other lanes are untouched by one service's refusal.
    assert signals_of(payload, detector.SIGNAL_S3_NO_LIFECYCLE)
    assert json.loads(capsys.readouterr().out)["status"] == "partial"


def test_a_denied_family_is_never_written_into_signals_as_a_fake_entry(
    optimization_stub, cloudcost_creds, tmp_path
):
    optimization_stub.fail(
        "ecr:DescribeRepositories", "AccessDeniedException", status=400, region=REGION_A
    )
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)

    assert [entry for entry in payload["signals"] if entry["service"] == "ecr"] == []
    assert payload["denied"]
    assert all(entry["signal"] in detector.SIGNALS for entry in payload["signals"])


def test_an_entirely_denied_spike_is_still_a_pass(
    optimization_stub, cloudcost_creds, tmp_path
):
    """A thin or empty result is a PASS labeled exploratory, never a failure (§t4)."""
    for key, region in (
        ("s3:ListBuckets", REGION_A),
        ("ecr:DescribeRepositories", REGION_A),
        ("secretsmanager:ListSecrets", REGION_A),
        ("ecr:DescribeRepositories", REGION_B),
        ("secretsmanager:ListSecrets", REGION_B),
    ):
        optimization_stub.fail(key, "AccessDeniedException", status=400, region=region)

    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)
    assert payload["signals"] == []
    assert payload["totals"]["signals"] == 0
    assert len(payload["denied"]) >= 3


def test_a_disabled_region_warns_rather_than_being_recorded_as_refused(
    optimization_stub, cloudcost_creds, tmp_path
):
    """OptInRequired is not the policy refusing — it is the region being off."""
    optimization_stub.fail(
        "ecr:DescribeRepositories", "OptInRequired", status=403, region=REGION_B
    )
    assert run_main(optimization_stub, tmp_path) == 0
    payload = emitted(tmp_path)

    assert payload["denied"] == []
    assert any("OptInRequired" in warning for warning in payload["warnings"])


def test_an_auth_failure_is_fatal_and_writes_nothing(
    optimization_stub, cloudcost_creds, tmp_path, capsys
):
    """A rejected credential is misconfiguration, not a thin result — the one exit-1 path."""
    optimization_stub.fail(
        "s3:ListBuckets", "InvalidClientTokenId", status=403, region=REGION_A
    )
    assert run_main(optimization_stub, tmp_path) == 1
    assert not list(tmp_path.glob("optimization_signals_*.json"))
    assert json.loads(capsys.readouterr().out)["status"] == "error"


# ============================================================== credentials (decision C/D2)


def test_the_spike_authenticates_with_cloudcost_creds_not_the_poisoned_default_chain(
    optimization_stub, cloudcost_creds, poisoned_default_chain, tmp_path
):
    """The D2 guard, extended to the spike.

    The stub returns a real 403 to any key it does not know, so a run that HAD fallen back to
    the poisoned default chain fails outright rather than passing quietly — which is what
    makes the assertion on `access_keys_seen()` mean something.
    """
    assert run_main(optimization_stub, tmp_path) == 0
    assert optimization_stub.access_keys_seen() == {CLOUDCOST_ACCESS_KEY}
    assert POISON_ACCESS_KEY not in optimization_stub.access_keys_seen()


def test_missing_cloudcost_credentials_raise_rather_than_falling_back(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.delenv("CLOUDCOST_AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("CLOUDCOST_AWS_SECRET_ACCESS_KEY", raising=False)
    assert detector.main(["--output-dir", str(tmp_path), "--period", PERIOD]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"


def test_no_credential_reaches_stdout_stderr_or_the_emitted_file(
    optimization_stub, cloudcost_creds, tmp_path, capsys
):
    assert run_main(optimization_stub, tmp_path) == 0
    captured = capsys.readouterr()
    emitted_text = (tmp_path / f"optimization_signals_aws_{PERIOD}.json").read_text()

    for secret in (CLOUDCOST_SECRET_KEY, POISON_SECRET_KEY):
        assert secret not in captured.out
        assert secret not in captured.err
        assert secret not in emitted_text
    assert CLOUDCOST_ACCESS_KEY not in emitted_text


# ============================================================================== the CLI


def cli(args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=USE_CASE_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_the_cli_writes_a_schema_shaped_file_to_an_arbitrary_output_dir(
    optimization_stub, tmp_path, monkeypatch
):
    """The §t4 done-check, run as the operator runs it: a real subprocess, real argv."""
    import os

    env = dict(os.environ)
    env.update(
        {
            "CLOUDCOST_AWS_ACCESS_KEY_ID": CLOUDCOST_ACCESS_KEY,
            "CLOUDCOST_AWS_SECRET_ACCESS_KEY": CLOUDCOST_SECRET_KEY,
            "CLOUDCOST_AWS_REGION": REGION_A,
            "CLOUDCOST_AWS_REGIONS": f"{REGION_A},{REGION_B}",
        }
    )
    for name in fetch_aws.SHADOWING_ENV:
        env.pop(name, None)

    result = cli(
        [
            "--output-dir",
            str(tmp_path),
            "--period",
            PERIOD,
            "--reference-date",
            REFERENCE,
            "--endpoint-url",
            optimization_stub.endpoint_url,
            "--max-attempts",
            "1",
        ],
        env=env,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["file"].endswith(f"optimization_signals_aws_{PERIOD}.json")

    payload = emitted(tmp_path)
    assert payload["signals"]
    assert CLOUDCOST_SECRET_KEY not in result.stdout + result.stderr


def test_the_detector_never_touches_the_orphan_lane(
    optimization_stub, cloudcost_creds, tmp_path
):
    """Decision G, asserted structurally: two lanes that do not import each other.

    Checked against a positive control first, so the guard cannot be one that only ever
    passes.
    """
    import re

    source = SCRIPT.read_text(encoding="utf-8")

    def imports(text, name):
        return re.search(rf"^\s*(import {name}\b|from {name} import)", text, re.M) is not None

    assert imports("import detect_orphans\n", "detect_orphans")
    assert imports(source, "fetch_aws")

    for module in ("detect_orphans", "compose_report_data", "render_report"):
        assert not imports(source, module), f"the spike imports {module}"

    # And it writes only its own file — nothing lands in the core pipeline's names.
    assert run_main(optimization_stub, tmp_path) == 0
    written = {path.name for path in tmp_path.glob("*.json")}
    assert written == {f"optimization_signals_aws_{PERIOD}.json"}
