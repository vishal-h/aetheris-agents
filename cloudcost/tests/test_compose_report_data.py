"""Offline tests for the report-data merge — pure, deterministic, no network, no LLM.

The DO side is composed from the t1/t2 fixtures the earlier stages are tested against, and
the second provider is a genuinely foreign bundle (`*_soc_*`) whose orphan file was produced
by running the real t2 CLI over its inventory. Every figure asserted here is either derived
from the fixtures in the test or is a constant the milestone names.
"""

import inspect
import json

import pytest
import subprocess
import sys
from pathlib import Path

import compose_report_data
import detect_orphans
from conftest import FIXTURES, USE_CASE_ROOT, load_fixture

SCRIPT = USE_CASE_ROOT / "scripts" / "compose_report_data.py"
DETECT = USE_CASE_ROOT / "scripts" / "detect_orphans.py"

#: The reference date every crafted fixture is written against (t2's convention).
REF = detect_orphans.parse_timestamp("2026-07-27T00:00:00Z")


# ---------------------------------------------------------------------------- helpers


def do_orphans():
    """The real t2 payload for the DO inventory fixture — not a hand-copied stand-in."""
    return detect_orphans.detect(load_fixture("inventory_rules_positive"), REF)


def do_bundle():
    return {
        "cost": load_fixture("cost_do_2026-07"),
        "inventory": load_fixture("inventory_rules_positive"),
        "orphans": do_orphans(),
    }


def soc_bundle():
    return {
        "cost": load_fixture("cost_soc_2026-07"),
        "inventory": load_fixture("inventory_soc_2026-07"),
        "orphans": load_fixture("orphans_soc_2026-07"),
    }


def compose(bundles=None, prior=None, **kwargs):
    return compose_report_data.compose(
        bundles if bundles is not None else [do_bundle()], prior_snapshots=prior, **kwargs
    )


def services(report):
    return {(r["provider"], r["service"]): r["amount"] for r in report["cost_summary"]["by_service"]}


def bands(report):
    return {b["band"]: b for b in report["orphans"]["by_band"]}


def banded_ids(report):
    return {band: [c["resource_id"] for c in b["candidates"]] for band, b in bands(report).items()}


def cli(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=USE_CASE_ROOT, capture_output=True, text=True
    )


def full_bundle_args(tmp_path, orphans_path):
    return [
        "--cost", str(FIXTURES / "cost_do_2026-07.json"),
        "--inventory", str(FIXTURES / "inventory_rules_positive.json"),
        "--orphans", str(orphans_path),
        "--output-dir", str(tmp_path / "out"),
        "--history-dir", str(tmp_path / "history"),
    ]


def write_orphans(tmp_path, name="orphan_candidates_2026-07.json", payload=None):
    path = tmp_path / name
    path.write_text(json.dumps(payload if payload is not None else do_orphans(), indent=2))
    return path


# ----------------------------------------------------------------- totals by service


def test_totals_are_grouped_by_provider_and_service_with_a_grand_total():
    report = compose()
    assert services(report) == {
        ("digitalocean", "Kubernetes Clusters"): 168.5,
        ("digitalocean", "Droplets"): 3.71,
        ("digitalocean", "Container Registry Subscription"): 0.0,
    }
    assert report["cost_summary"]["grand_total"] == 172.21
    assert report["cost_summary"]["totals_by_currency"] == {"USD": 172.21}
    assert report["cost_summary"]["by_provider"] == [
        {
            "provider": "digitalocean",
            "currency": "USD",
            "amount": 172.21,
            "line_items_sum": 172.21,
            "reconciled": True,
            "source_granularity": "service",
        }
    ]


def test_services_are_ordered_by_descending_amount():
    report = compose()
    assert [r["service"] for r in report["cost_summary"]["by_service"]] == [
        "Kubernetes Clusters",
        "Droplets",
        "Container Registry Subscription",
    ]


def test_the_cost_total_is_the_billed_service_figure_not_the_sum_of_resource_estimates():
    """D4, behaviourally: the two numbers are far apart on this fixture, and the report
    must carry the billed one."""
    inventory = load_fixture("inventory_rules_positive")
    resource_estimates = round(
        sum(r["monthly_cost_estimate"] for r in inventory["resources"]), 2
    )
    report = compose()
    assert resource_estimates == 56.58  # what a resource-level sum would have produced
    assert report["cost_summary"]["grand_total"] == 172.21
    assert report["totals"]["cost_grand_total"] != resource_estimates
    assert report["cost_summary"]["by_provider"][0]["source_granularity"] == "service"


def test_the_cost_functions_never_read_a_resource_level_estimate():
    """D4, structurally: neither cost figure has a resource estimate in scope.

    Matches the two forms a field is actually read by, not the bare name — prose mentions
    it. The same patterns are asserted *present* in the sections that legitimately rank and
    total estimates, so the absence above is a real absence rather than a pattern that
    never matches anything.
    """
    reads = ('get("monthly_cost_estimate")', 'get("monthly_saving_estimate")')
    cost_side = inspect.getsource(compose_report_data.service_totals) + inspect.getsource(
        compose_report_data.month_on_month
    )
    estimate_side = inspect.getsource(compose_report_data.coverage_section) + inspect.getsource(
        compose_report_data.orphan_section
    )
    for read in reads:
        assert read not in cost_side
        assert '["monthly_cost_estimate"]' not in cost_side
        assert '["monthly_saving_estimate"]' not in cost_side
        assert read in estimate_side


def test_a_declared_total_that_does_not_match_its_line_items_is_warned_about():
    cost = {
        "provider": "digitalocean",
        "period": "2026-07",
        "currency": "USD",
        "line_items": [{"service": "Droplets", "amount": 10.0}],
        "totals": {"amount": 99.0},
    }
    report = compose([{"cost": cost, "inventory": None, "orphans": None}])
    provider_row = report["cost_summary"]["by_provider"][0]
    assert provider_row["amount"] == 99.0 and provider_row["line_items_sum"] == 10.0
    assert provider_row["reconciled"] is False
    assert any("does not match the sum" in w["warning"] for w in report["warnings"])


def test_two_currencies_withhold_the_grand_total_rather_than_summing_them():
    """No conversion at m1, so a cross-currency scalar would be a well-formed wrong answer."""
    other = soc_bundle()
    other["cost"] = {**other["cost"], "currency": "EUR"}
    report = compose([do_bundle(), other])
    assert report["cost_summary"]["grand_total"] is None
    assert report["cost_summary"]["currency"] is None
    assert report["cost_summary"]["totals_by_currency"] == {"EUR": 60.0, "USD": 172.21}
    assert any("more than one currency" in w["warning"] for w in report["warnings"])


# -------------------------------------------------------------------------- MoM delta


def test_the_first_run_reports_no_prior_month_and_is_not_an_error():
    report = compose(prior=[])
    assert report["mom_delta"]["status"] == "no_prior_month"
    assert report["mom_delta"]["prior_period"] == "2026-06"
    assert report["warnings"] == [] and report["skipped"] == []


def test_the_prior_month_is_derived_from_the_period_not_the_wall_clock():
    assert compose_report_data.prior_period("2026-07") == "2026-06"
    assert compose_report_data.prior_period("2026-01") == "2025-12"
    assert compose_report_data.prior_period("2026-13") is None
    assert compose_report_data.prior_period("last month") is None
    assert compose_report_data.prior_period(None) is None


def test_the_delta_is_computed_against_the_seeded_snapshots_own_numbers():
    """Expectations are derived from the seeded prior snapshot here in the test — a
    hardcoded delta would still pass if the prior month were never read."""
    prior = load_fixture("cost_do_2026-06")
    prior_by_service = {item["service"]: item["amount"] for item in prior["line_items"]}
    prior_total = prior["totals"]["amount"]

    report = compose(prior=[prior])
    delta = report["mom_delta"]
    assert delta["status"] == "ok"
    assert delta["prior_period"] == "2026-06" and delta["current_period"] == "2026-07"
    assert delta["prior_total"] == prior_total
    assert delta["current_total"] == report["cost_summary"]["grand_total"]
    assert delta["delta_amount"] == round(delta["current_total"] - prior_total, 2)
    assert delta["delta_pct"] == round(delta["delta_amount"] / prior_total * 100, 2)

    rows = {row["service"]: row for row in delta["by_service"]}
    current = services(report)
    for service, row in rows.items():
        assert row["prior_amount"] == prior_by_service.get(service, 0.0)
        assert row["current_amount"] == current.get(("digitalocean", service), 0.0)
        assert row["delta_amount"] == round(row["current_amount"] - row["prior_amount"], 2)


def test_services_that_appeared_or_disappeared_are_labelled_not_silently_zeroed():
    report = compose(prior=[load_fixture("cost_do_2026-06")])
    rows = {row["service"]: row for row in report["mom_delta"]["by_service"]}
    assert rows["Spaces"]["change"] == "removed"
    assert rows["Spaces"]["current_amount"] == 0.0 and rows["Spaces"]["delta_pct"] == -100.0
    assert rows["Container Registry Subscription"]["change"] == "new"
    # New off a zero base has no meaningful ratio; null, not a fabricated percentage.
    assert rows["Container Registry Subscription"]["delta_pct"] is None
    assert rows["Kubernetes Clusters"]["change"] == "changed"


def test_a_provider_with_no_prior_snapshot_is_flagged_rather_than_read_as_growth():
    report = compose([do_bundle(), soc_bundle()], prior=[load_fixture("cost_do_2026-06")])
    delta = report["mom_delta"]
    assert delta["providers_without_prior_snapshot"] == ["someothercloud"]
    assert any("no prior-month snapshot for provider(s)" in w["warning"] for w in report["warnings"])
    soc = next(row for row in delta["by_provider"] if row["provider"] == "someothercloud")
    assert soc["prior_amount"] == 0.0 and soc["current_amount"] == 60.0


def test_a_prior_snapshot_that_does_not_reconcile_is_warned_about_and_scoped():
    prior = load_fixture("cost_do_2026-06")
    prior["totals"] = {"amount": 999.0}
    report = compose(prior=[prior])
    warning = next(w for w in report["warnings"] if "does not match the sum" in w["warning"])
    assert warning["scope"] == "prior period 2026-06"


# ---------------------------------------------------- tag coverage + top untagged


def test_coverage_is_the_same_figure_t2_reports_for_the_same_inventory():
    """The ticket requires these to be equal; they share one definition, and this is the
    assertion that keeps them equal if either side is ever edited."""
    t2 = do_orphans()["reported"]["untagged_in_tagged_account"]["tag_coverage"]
    assert compose()["tag_coverage"]["coverage"] == t2 == 0.1667


def test_coverage_is_computed_from_the_inventories_not_read_from_the_orphan_file():
    """A lie planted in the orphan file's coverage field must not reach the report."""
    bundle = do_bundle()
    bundle["orphans"]["reported"]["untagged_in_tagged_account"]["tag_coverage"] = 0.99
    report = compose([bundle])
    assert report["tag_coverage"]["coverage"] == 0.1667


def test_coverage_is_computed_over_the_union_of_the_inventories():
    report = compose([do_bundle(), soc_bundle()])
    coverage = report["tag_coverage"]
    assert coverage["resources"] == 10 and coverage["tagged"] == 2 and coverage["untagged"] == 8
    assert coverage["coverage"] == 0.2
    assert coverage["by_provider"] == [
        {
            "provider": "digitalocean",
            "resources": 6,
            "tagged": 1,
            "untagged": 5,
            "coverage": 0.1667,
        },
        {
            "provider": "someothercloud",
            "resources": 4,
            "tagged": 1,
            "untagged": 3,
            "coverage": 0.25,
        },
    ]


def test_top_untagged_spenders_are_ranked_across_providers_by_resource_estimate():
    report = compose([do_bundle(), soc_bundle()])
    top = report["tag_coverage"]["top_untagged_spenders"]
    assert [(t["provider"], t["resource_id"], t["monthly_cost_estimate"]) for t in top] == [
        ("someothercloud", "vm-2", 80.0),
        ("someothercloud", "disk-1", 40.0),
        ("digitalocean", "lb-idle-1", 12.0),
        ("digitalocean", "vol-orphan-1", 10.0),
        ("digitalocean", "vol-on-stopped-1", 5.0),
        ("digitalocean", "203.0.113.10", 4.38),
        ("someothercloud", "bucket-1", 3.0),
        ("digitalocean", "snap-aged-1", 1.2),
    ]
    # No tagged resource is ever in the list, however expensive (soc's vm-1 is $120/mo).
    assert "vm-1" not in [t["resource_id"] for t in top]


def test_each_untagged_spender_carries_the_identity_fields_the_report_renders():
    top = compose()["tag_coverage"]["top_untagged_spenders"][0]
    assert top == {
        "provider": "digitalocean",
        "resource_id": "lb-idle-1",
        "type": "load_balancer",
        "name": "orphaned-lb",
        "region": "blr1",
        "size": "lb-small",
        "monthly_cost_estimate": 12.0,
        "raw_ref": "do://load_balancers/lb-idle-1",
        # BL-101: the rows the report already renders now carry their tags. This row is an
        # untagged spender, so the list is empty — and empty is the point: the key is
        # always present, so "no tags" and "tags not carried" are different shapes.
        "tags": [],
    }


def test_the_top_k_is_a_parameter_and_is_reported_with_the_list():
    report = compose([do_bundle(), soc_bundle()], top_untagged=3)
    assert report["tag_coverage"]["top_k"] == 3
    assert len(report["tag_coverage"]["top_untagged_spenders"]) == 3
    # Truncating the list does not truncate the count or the estimate behind it.
    assert report["tag_coverage"]["untagged"] == 8
    assert report["tag_coverage"]["untagged_monthly_cost_estimate"] == 155.58


# --------------------------------------------------------------------- orphan section


def test_candidates_are_grouped_into_the_documented_confidence_bands():
    assert banded_ids(compose()) == {
        "HIGH": ["203.0.113.10", "vol-orphan-1"],
        "MEDIUM": ["lb-idle-1", "snap-aged-1"],
        "LOW": ["drop-stopped-1"],
    }


def test_the_band_cutoffs_are_printed_in_the_payload():
    report = compose()
    assert report["orphans"]["bands"] == [
        {
            "band": "HIGH",
            "min_confidence": 0.9,
            "max_confidence": None,
            "rule": "confidence >= 0.9",
        },
        {
            "band": "MEDIUM",
            "min_confidence": 0.7,
            "max_confidence": 0.9,
            "rule": "0.7 <= confidence < 0.9",
        },
        {
            "band": "LOW",
            "min_confidence": None,
            "max_confidence": 0.7,
            "rule": "confidence < 0.7",
        },
    ]
    for band in report["orphans"]["by_band"]:
        printed = next(b for b in report["orphans"]["bands"] if b["band"] == band["band"])
        assert {key: band[key] for key in printed} == printed


def test_the_band_boundaries_are_inclusive_at_the_bottom_of_each_band():
    candidates = [
        {"resource_id": "at-high", "confidence": 0.9, "monthly_saving_estimate": 1.0},
        {"resource_id": "below-high", "confidence": 0.89, "monthly_saving_estimate": 1.0},
        {"resource_id": "at-medium", "confidence": 0.7, "monthly_saving_estimate": 1.0},
        {"resource_id": "below-medium", "confidence": 0.69, "monthly_saving_estimate": 1.0},
    ]
    report = compose(
        [{"cost": None, "inventory": None, "orphans": {"provider": "p", "candidates": candidates}}]
    )
    assert banded_ids(report) == {
        "HIGH": ["at-high"],
        "MEDIUM": ["below-high", "at-medium"],
        "LOW": ["below-medium"],
    }


def test_each_candidate_is_carried_through_verbatim_with_only_a_provider_key_added():
    original = {c["resource_id"]: c for c in do_orphans()["candidates"]}
    for band in compose()["orphans"]["by_band"]:
        for entry in band["candidates"]:
            assert entry["provider"] == "digitalocean"
            assert {k: v for k, v in entry.items() if k != "provider"} == original[
                entry["resource_id"]
            ]
    # And the evidence trail is intact, not summarised.
    high = bands(compose())["HIGH"]["candidates"][0]
    assert high["evidence"] == original[high["resource_id"]]["evidence"]
    assert high["base_confidence"] == 0.95 and high["modifiers"] == []


def test_each_band_carries_its_own_saving_subtotal_and_the_section_carries_the_overall():
    report = compose()
    subtotals = {band: b["monthly_saving_estimate"] for band, b in bands(report).items()}
    # LOW is the stopped-compute candidate: 24.00 own + 5.00 attached storage (m2 t2 c —
    # compose is unchanged; the figure moved because the stage above it stopped
    # under-reporting).
    assert subtotals == {"HIGH": 14.38, "MEDIUM": 13.2, "LOW": 29.0}
    assert report["orphans"]["totals"] == {
        "candidates": 5,
        "monthly_saving_estimate": round(sum(subtotals.values()), 2),
    }
    # Which is t2's own total for the same inventory, carried through undisturbed.
    assert report["orphans"]["totals"]["monthly_saving_estimate"] == do_orphans()["totals"][
        "monthly_saving_estimate"
    ]


def test_the_orphan_section_records_what_the_age_rules_were_evaluated_against():
    assert compose()["orphans"]["evaluated_as_of"] == [
        {
            "provider": "digitalocean",
            "reference_date": "2026-07-27T00:00:00Z",
            "inventory_generated_at": "2026-07-27T00:00:00Z",
        }
    ]


def test_a_candidate_without_a_numeric_confidence_is_skipped_not_banded():
    orphans = {"provider": "p", "candidates": [{"resource_id": "mystery", "evidence": []}]}
    report = compose([{"cost": None, "inventory": None, "orphans": orphans}])
    assert report["orphans"]["totals"]["candidates"] == 0
    assert report["skipped"][0]["reason"].startswith("orphan candidate has no numeric confidence")


# ------------------------------------------------------- region coverage (m2 t3, A4)


def swept_bundle(regions, extra=None):
    """A foreign bundle whose cost snapshot carries the one payload key A4 lifts.

    Built on `soc_bundle()` so everything around the key is a real normalized document —
    a hand-written stand-in would prove only that the lift reads what this file's author
    wrote. `extra` seeds decoy keys alongside it.
    """
    bundle = soc_bundle()
    bundle["cost"] = {
        **bundle["cost"],
        "provider_extra": {**(extra or {}), "swept_regions": regions},
    }
    return bundle


def test_the_swept_region_set_is_lifted_into_a_named_report_field():
    report = compose([swept_bundle(["eu-west-1", "us-east-1"])])
    assert report["region_coverage"] == [
        {"provider": "someothercloud", "swept": ["eu-west-1", "us-east-1"], "count": 2}
    ]


def test_a_provider_that_sweeps_no_regions_contributes_no_entry():
    """The failable pair for the test above, and the invariant the DO report rests on: a
    provider with no swept set leaves the field empty rather than inventing coverage."""
    assert compose([do_bundle()])["region_coverage"] == []


def test_the_lift_copies_one_named_key_and_nothing_else_out_of_the_provider_payload():
    """The "never key on the provider payload block generically" clause, as an assertion.

    An implementation that copied the block through — or iterated it — would carry these
    decoys into the report and fail here. Only the one named key may cross.
    """
    decoys = {"results_by_time": [{"time_period": {"Start": "2026-07-01"}}], "raw_arn": "arn:aws:ec2:x"}
    report = compose([swept_bundle(["us-east-1"], extra=decoys)])
    payload = json.dumps(report)
    assert "results_by_time" not in payload
    assert "raw_arn" not in payload and "arn:aws:" not in payload
    assert report["region_coverage"][0]["swept"] == ["us-east-1"]


def test_the_region_list_is_the_adapters_own_order_and_is_never_re_sorted():
    """compose derives nothing here. The adapter already sorts and dedupes; re-doing it in
    shared machinery would be this stage inventing a figure, and would hide an adapter whose
    sweep had started returning duplicates."""
    report = compose([swept_bundle(["us-west-2", "ap-south-1", "us-west-2"])])
    assert report["region_coverage"][0]["swept"] == ["us-west-2", "ap-south-1", "us-west-2"]
    assert report["region_coverage"][0]["count"] == 3


def test_a_malformed_swept_set_degrades_and_a_malformed_element_is_shown_not_dropped():
    assert compose([swept_bundle("us-east-1")])["region_coverage"] == []
    entry = compose([swept_bundle(["us-east-1", 42])])["region_coverage"][0]
    assert entry["swept"] == ["us-east-1", "42"] and entry["count"] == 2


def test_a_provider_that_swept_nothing_says_so_rather_than_going_silent():
    """Zero regions and no sweep are different facts: the first is a broken sweep worth
    seeing (decision D, no-silent-caps), the second is a provider with no such concept."""
    assert compose([swept_bundle([])])["region_coverage"] == [
        {"provider": "someothercloud", "swept": [], "count": 0}
    ]


def test_each_provider_states_its_own_sweep():
    report = compose([do_bundle(), swept_bundle(["us-east-1"])])
    assert [entry["provider"] for entry in report["region_coverage"]] == ["someothercloud"]


# --------------------------------------------------------------------- N providers


def test_a_two_provider_bundle_composes_with_no_code_change():
    report = compose([do_bundle(), soc_bundle()])
    assert report["providers"] == ["digitalocean", "someothercloud"]
    assert report["accounts"] == [
        {"provider": "digitalocean", "account": "aaaaaaaa-1111-2222-3333-444444444444"},
        {"provider": "someothercloud", "account": "acct-77281"},
    ]
    assert report["cost_summary"]["grand_total"] == round(172.21 + 60.0, 2)
    assert services(report)[("someothercloud", "Compute")] == 50.0
    # The foreign candidate outranks every DO one and leads the HIGH band.
    assert banded_ids(report)["HIGH"] == ["disk-1", "203.0.113.10", "vol-orphan-1"]
    assert report["totals"]["orphan_candidates"] == 6
    assert report["totals"]["orphan_monthly_saving_estimate"] == 96.58


def test_bundles_are_ordered_by_provider_whatever_order_they_arrive_in():
    assert compose([soc_bundle(), do_bundle()]) == compose([do_bundle(), soc_bundle()])


def test_input_dir_groups_files_into_per_provider_bundles_by_shape_not_by_filename(tmp_path):
    source = tmp_path / "in"
    source.mkdir()
    for name, fixture in (
        ("a.json", "cost_do_2026-07"),
        ("b.json", "inventory_rules_positive"),
        ("d.json", "cost_soc_2026-07"),
        ("e.json", "inventory_soc_2026-07"),
        ("f.json", "orphans_soc_2026-07"),
    ):
        (source / name).write_text(json.dumps(load_fixture(fixture)))
    (source / "c.json").write_text(json.dumps(do_orphans()))

    result = cli(
        [
            "--input-dir", str(source),
            "--output-dir", str(tmp_path / "out"),
            "--history-dir", str(tmp_path / "history"),
        ]
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["counts"]["providers"] == 2
    report = json.loads(Path(summary["file"]).read_text())
    assert report["providers"] == ["digitalocean", "someothercloud"]
    assert report["totals"]["orphan_candidates"] == 6


def test_input_dir_ignores_a_previously_written_report_data_file(tmp_path):
    """The pipeline's own output lands in the same directory; re-running must not read it
    back in as an input."""
    source = tmp_path / "in"
    source.mkdir()
    (source / "cost.json").write_text(json.dumps(load_fixture("cost_do_2026-07")))
    (source / "inv.json").write_text(json.dumps(load_fixture("inventory_rules_positive")))
    (source / "orph.json").write_text(json.dumps(do_orphans()))
    first = cli(
        ["--input-dir", str(source), "--output-dir", str(source),
         "--history-dir", str(tmp_path / "history")]
    )
    assert first.returncode == 0, first.stderr
    second = cli(
        ["--input-dir", str(source), "--output-dir", str(source),
         "--history-dir", str(tmp_path / "history")]
    )
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["counts"]["providers"] == 1


# ------------------------------------------------------------------------ determinism


def test_the_same_inputs_produce_a_byte_identical_payload():
    first = json.dumps(compose([do_bundle(), soc_bundle()]), indent=2, sort_keys=True)
    second = json.dumps(compose([do_bundle(), soc_bundle()]), indent=2, sort_keys=True)
    assert first == second


def test_the_report_is_stamped_from_its_inputs_and_reads_no_clock():
    report = compose([do_bundle(), soc_bundle()])
    # The newest fetch timestamp among the inputs: DO's cost snapshot.
    assert report["as_of"] == "2026-07-27T04:41:53Z"
    source = SCRIPT.read_text()
    assert "datetime.now" not in source and "utcnow" not in source


# -------------------------------------------------------------------------- degrading


def test_a_bundle_missing_a_document_still_composes_the_sections_it_can():
    report = compose([{"cost": load_fixture("cost_do_2026-07"), "inventory": None, "orphans": None}])
    assert report["cost_summary"]["grand_total"] == 172.21
    assert report["tag_coverage"]["resources"] == 0
    assert report["orphans"]["totals"]["candidates"] == 0
    assert [w["warning"].split(" for this")[0] for w in report["warnings"]] == [
        "no usable inventory",
        "no usable orphan candidates",
    ]


def test_a_malformed_inventory_entry_is_skipped_not_fatal():
    report = compose([{"cost": None, "inventory": load_fixture("inventory_malformed"), "orphans": None}])
    assert [entry["index"] for entry in report["skipped"]] == [0, 1, 2, 3]
    assert all(entry["source"] == "inventory" for entry in report["skipped"])
    assert report["tag_coverage"]["resources"] == 2


def test_a_document_for_the_wrong_period_is_composed_but_flagged():
    bundle = do_bundle()
    bundle["cost"] = {**bundle["cost"], "period": "2026-05"}
    report = compose([bundle], period="2026-07")
    assert any("is for period 2026-05" in w["warning"] for w in report["warnings"])
    assert report["cost_summary"]["grand_total"] == 172.21


def test_an_empty_bundle_list_is_not_an_error():
    report = compose([])
    assert report["totals"]["providers"] == 0
    assert report["cost_summary"]["grand_total"] is None
    assert report["mom_delta"]["status"] == "no_prior_month"


# --------------------------------------------------------------------------- history


def test_the_runs_cost_snapshot_is_written_into_the_history_dir(tmp_path):
    result = cli(full_bundle_args(tmp_path, write_orphans(tmp_path)))
    assert result.returncode == 0, result.stderr
    written = tmp_path / "history" / "2026-07" / "digitalocean_costs_2026-07.json"
    assert written.exists()
    assert json.loads(written.read_text()) == load_fixture("cost_do_2026-07")
    assert json.loads(result.stdout)["history"]["written"] == [str(written)]


def test_re_running_a_period_overwrites_its_snapshot_and_never_appends(tmp_path):
    args = full_bundle_args(tmp_path, write_orphans(tmp_path))
    assert cli(args).returncode == 0
    period_dir = tmp_path / "history" / "2026-07"
    (period_dir / "digitalocean_costs_2026-07.json").write_text('{"provider": "stale"}')
    assert cli(args).returncode == 0
    assert [p.name for p in sorted(period_dir.iterdir())] == ["digitalocean_costs_2026-07.json"]
    assert json.loads(
        (period_dir / "digitalocean_costs_2026-07.json").read_text()
    ) == load_fixture("cost_do_2026-07")


def test_each_provider_gets_its_own_history_file(tmp_path):
    result = cli(
        [
            "--cost", str(FIXTURES / "cost_do_2026-07.json"),
            "--inventory", str(FIXTURES / "inventory_rules_positive.json"),
            "--orphans", str(write_orphans(tmp_path)),
            "--cost", str(FIXTURES / "cost_soc_2026-07.json"),
            "--inventory", str(FIXTURES / "inventory_soc_2026-07.json"),
            "--orphans", str(FIXTURES / "orphans_soc_2026-07.json"),
            "--output-dir", str(tmp_path / "out"),
            "--history-dir", str(tmp_path / "history"),
        ]
    )
    assert result.returncode == 0, result.stderr
    assert [p.name for p in sorted((tmp_path / "history" / "2026-07").iterdir())] == [
        "digitalocean_costs_2026-07.json",
        "someothercloud_costs_2026-07.json",
    ]


def test_the_history_default_is_the_use_case_root_not_the_current_directory():
    assert compose_report_data.DEFAULT_HISTORY_DIR == USE_CASE_ROOT / "history"
    assert compose_report_data.parse_args(["--input-dir", "x"]).history_dir == str(
        USE_CASE_ROOT / "history"
    )


# --------------------------------------------------------------------------------- CLI


def test_the_cli_writes_the_report_data_file_and_prints_the_summary_envelope(tmp_path):
    result = cli(full_bundle_args(tmp_path, write_orphans(tmp_path)))
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["period"] == "2026-07"
    assert summary["counts"] == {
        "providers": 1,
        "services": 3,
        "resources": 6,
        "untagged_resources": 5,
        "orphan_candidates": 5,
        "prior_snapshots": 0,
        "skipped": 0,
    }
    assert summary["mom_delta"]["status"] == "no_prior_month"
    assert summary["warnings"] == [] and summary["skipped"] == []

    written = Path(summary["file"])
    assert written == tmp_path / "out" / "report_data_2026-07.json"
    assert json.loads(written.read_text())["totals"] == summary["totals"]


def test_the_cli_first_run_exits_zero_with_no_prior_month(tmp_path):
    result = cli(full_bundle_args(tmp_path, write_orphans(tmp_path)))
    assert result.returncode == 0
    report = json.loads((tmp_path / "out" / "report_data_2026-07.json").read_text())
    assert report["mom_delta"] == {
        "status": "no_prior_month",
        "prior_period": "2026-06",
        "reason": "no persisted cost snapshot found for the prior calendar month",
    }


def test_the_cli_second_month_reads_the_seeded_prior_snapshot(tmp_path):
    """Seeded, not accumulated: production accumulates history, the test seeds it."""
    prior_dir = tmp_path / "history" / "2026-06"
    prior_dir.mkdir(parents=True)
    prior = load_fixture("cost_do_2026-06")
    (prior_dir / "digitalocean_costs_2026-06.json").write_text(json.dumps(prior))

    result = cli(full_bundle_args(tmp_path, write_orphans(tmp_path)))
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["counts"]["prior_snapshots"] == 1
    report = json.loads((tmp_path / "out" / "report_data_2026-07.json").read_text())
    delta = report["mom_delta"]
    assert delta["status"] == "ok"
    assert delta["prior_total"] == prior["totals"]["amount"]
    assert delta["delta_amount"] == round(
        report["cost_summary"]["grand_total"] - prior["totals"]["amount"], 2
    )
    assert summary["mom_delta"]["delta_amount"] == delta["delta_amount"]


def test_the_cli_degrades_on_a_missing_input_file(tmp_path):
    args = full_bundle_args(tmp_path, tmp_path / "nope.json")
    result = cli(args)
    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["status"] == "partial"
    assert summary["skipped"][0]["source"] == "orphans"
    # Degraded, not aborted: everything that did not depend on the missing file is there.
    assert (tmp_path / "out" / "report_data_2026-07.json").exists()
    assert summary["totals"]["cost_grand_total"] == 172.21
    assert summary["counts"]["orphan_candidates"] == 0


def test_the_cli_degrades_on_malformed_json(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    result = cli(full_bundle_args(tmp_path, broken))
    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["status"] == "partial"
    assert summary["skipped"][0]["path"] == str(broken)
    assert (tmp_path / "out" / "report_data_2026-07.json").exists()


def test_the_cli_rejects_mismatched_triple_counts_rather_than_mispairing_them(tmp_path):
    result = cli(
        [
            "--cost", str(FIXTURES / "cost_do_2026-07.json"),
            "--cost", str(FIXTURES / "cost_soc_2026-07.json"),
            "--inventory", str(FIXTURES / "inventory_rules_positive.json"),
            "--output-dir", str(tmp_path),
            "--history-dir", str(tmp_path / "history"),
        ]
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"
    assert "same number of times" in result.stderr


def test_the_cli_rejects_no_inputs_at_all(tmp_path):
    result = cli(["--output-dir", str(tmp_path), "--history-dir", str(tmp_path / "history")])
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"


# ------------------------------------------------- cross-stage: t1 → t2 → t3 (m6 rule)
#
# The tests above run on fixtures written by the same hand as the consumer. This one runs
# the real adapter against the recorded DO responses, feeds its files to the real t2 CLI,
# and feeds *those* to the t3 CLI — so a rename or a shape drift anywhere along the two
# stage seams fails here rather than in the live pipeline.


def test_the_whole_pipeline_composes_end_to_end(full_stub, tmp_path, monkeypatch):
    import fetch_do

    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", "cc-readonly-SENTINEL-3f9a1c7e")
    assert (
        fetch_do.main(
            [
                "--output-dir", str(tmp_path),
                "--period", "2026-07",
                "--api-base", full_stub.api_base,
                "--retry-base-delay", "0",
                "--max-retries", "0",
            ]
        )
        == 0
    )
    costs_file = tmp_path / "do_costs_2026-07.json"
    inventory_file = tmp_path / "do_inventory_2026-07.json"

    detect = subprocess.run(
        [
            sys.executable, str(DETECT), str(inventory_file),
            "--output-dir", str(tmp_path), "--reference-date", "2026-07-27",
        ],
        cwd=USE_CASE_ROOT, capture_output=True, text=True,
    )
    assert detect.returncode == 0, detect.stderr
    orphans_file = tmp_path / "digitalocean_orphan_candidates_2026-07.json"

    result = cli(
        [
            "--cost", str(costs_file),
            "--inventory", str(inventory_file),
            "--orphans", str(orphans_file),
            "--output-dir", str(tmp_path / "out"),
            "--history-dir", str(tmp_path / "history"),
        ]
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "out" / "report_data_2026-07.json").read_text())

    costs = json.loads(costs_file.read_text())
    orphans = json.loads(orphans_file.read_text())

    # Cost: the adapter's own service lines and declared total, reconciled.
    assert report["cost_summary"]["grand_total"] == costs["totals"]["amount"]
    assert services(report) == {
        ("digitalocean", item["service"]): item["amount"] for item in costs["line_items"]
    }
    assert report["cost_summary"]["by_provider"][0]["reconciled"] is True

    # Coverage: computed from the adapter's inventory, equal to what t2 reported on it.
    assert (
        report["tag_coverage"]["coverage"]
        == orphans["reported"]["untagged_in_tagged_account"]["tag_coverage"]
    )
    assert report["tag_coverage"]["top_untagged_spenders"]

    # Orphans: every t2 candidate lands in a band, none lost, evidence intact.
    banded = {c["resource_id"]: c for band in report["orphans"]["by_band"] for c in band["candidates"]}
    assert set(banded) == {c["resource_id"] for c in orphans["candidates"]}
    assert report["orphans"]["totals"]["monthly_saving_estimate"] == orphans["totals"][
        "monthly_saving_estimate"
    ]
    assert banded["vol-orphan-1"]["evidence"] == next(
        c["evidence"] for c in orphans["candidates"] if c["resource_id"] == "vol-orphan-1"
    )
    assert report["skipped"] == [] and report["warnings"] == []

    # And the run's snapshot is on disk for next month's delta.
    assert (tmp_path / "history" / "2026-07" / "digitalocean_costs_2026-07.json").exists()

    # DigitalOcean sweeps no regions, so the A4 field stays empty on this pipeline.
    assert report["region_coverage"] == []


def test_the_aws_adapters_swept_set_reaches_report_data(full_aws_stub, tmp_path, monkeypatch):
    """A4 across the same two seams, on the provider that motivated it.

    The swept set is asserted equal to the *adapter's own* emitted value read back off disk,
    not to a list written here: a hardcoded expectation would still pass if compose lifted
    the wrong key, or lifted nothing and the constant happened to match.
    """
    import fetch_aws
    from conftest import CLOUDCOST_ACCESS_KEY, CLOUDCOST_SECRET_KEY

    monkeypatch.setenv("CLOUDCOST_AWS_ACCESS_KEY_ID", CLOUDCOST_ACCESS_KEY)
    monkeypatch.setenv("CLOUDCOST_AWS_SECRET_ACCESS_KEY", CLOUDCOST_SECRET_KEY)
    assert (
        fetch_aws.main(
            [
                "--output-dir", str(tmp_path),
                "--period", "2026-07",
                "--endpoint-url", full_aws_stub.endpoint_url,
            ]
        )
        == 0
    )
    costs_file = tmp_path / "aws_costs_2026-07.json"
    inventory_file = tmp_path / "aws_inventory_2026-07.json"

    detect = subprocess.run(
        [
            sys.executable, str(DETECT), str(inventory_file),
            "--output-dir", str(tmp_path), "--reference-date", "2026-07-27",
        ],
        cwd=USE_CASE_ROOT, capture_output=True, text=True,
    )
    assert detect.returncode == 0, detect.stderr

    result = cli(
        [
            "--cost", str(costs_file),
            "--inventory", str(inventory_file),
            "--orphans", str(tmp_path / "aws_orphan_candidates_2026-07.json"),
            "--output-dir", str(tmp_path / "out"),
            "--history-dir", str(tmp_path / "history"),
        ]
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "out" / "report_data_2026-07.json").read_text())

    emitted = json.loads(costs_file.read_text())["provider_extra"]["swept_regions"]
    assert emitted, "the adapter emitted no swept set — this test would assert nothing"
    assert report["region_coverage"] == [
        {"provider": "aws", "swept": emitted, "count": len(emitted)}
    ]


# ------------------------------------------------------- m4 t5b — the report value pass
#
# BL-101 (tags surfaced), BL-121 (the cap reports its truncation), BL-127 (a non-`str` tag
# element is a counted skip), BL-070 (slug convergence). Each new *distinction* is asserted
# in both of its states, per the mutation posture: a rendering that has only ever been seen
# in one state has not been shown to distinguish anything.


def _tags_of_all(inventory_list):
    """Every distinct tag across the inventories, recomputed from the inputs."""
    return {
        tag
        for inv in inventory_list
        for r in compose_report_data.usable_resources(inv)[0]
        for tag in compose_report_data.tags_of(r)
    }


def _carriers(inventory_list):
    """Every resource carrying at least one tag, recomputed from the inputs."""
    return {
        str(r.get("resource_id"))
        for inv in inventory_list
        for r in compose_report_data.usable_resources(inv)[0]
        if compose_report_data.tags_of(r)
    }


def _multi_tag_bundle():
    """A DO bundle whose tag set is large enough for a cap to bite, with a known overlap.

    Mutates `inventory["resources"]` **directly**. `usable_resources` happens to return
    references into that list, but a test that depends on it would silently stop measuring
    anything if it ever copied — the same failure class as an assertion that cannot fail.
    """
    inventory = load_fixture("inventory_rules_positive")
    inventory["resources"][0]["tags"] = ["env=prod", "team=core"]
    inventory["resources"][1]["tags"] = ["env=prod"]
    inventory["resources"][2]["tags"] = ["terraform"]
    inventory["resources"][3]["tags"] = ["env=staging"]
    # Established, not assumed: the mutation is visible on the object compose will read.
    assert compose_report_data.usable_resources(inventory)[0][0]["tags"] == ["env=prod", "team=core"]
    return {
        "cost": load_fixture("cost_do_2026-07"),
        "inventory": inventory,
        "orphans": detect_orphans.detect(inventory, REF),
    }


def _assert_aggregation_reconciles(coverage, inventories):
    """BL-101's Done-when, as the aggregation invariant alone.

    **Computed from the FULL tag set, never from `tags_in_use`** — that payload key is the
    capped prefix, so reading the invariant off it would assert something the design does
    not have and would go red on correct behaviour the moment a cap bit.
    """
    resources = [r for inv in inventories for r in compose_report_data.usable_resources(inv)[0]]
    carriers = _carriers(inventories)

    # (1) the coverage figures are the ratio's own computation, not a second one
    assert coverage["resources"] == len(resources)
    assert coverage["tagged"] == len(carriers)
    assert coverage["untagged"] == len(resources) - len(carriers)
    assert coverage["coverage"] == compose_report_data.tag_coverage(resources)

    # (2) THE reconciliation: the full tag set's carriers are exactly `tagged`
    assert coverage["tags_in_use_total"] == len(_tags_of_all(inventories))
    assert len(carriers) == coverage["tagged"]

    # (3) every row the payload does carry is exact against the inputs
    for row in coverage["tags_in_use"]:
        carrying = [r for r in resources if row["tag"] in compose_report_data.tags_of(r)]
        assert row["resources"] == len(carrying)
        assert row["monthly_cost_estimate"] == round(
            sum(compose_report_data.money(r.get("monthly_cost_estimate")) for r in carrying), 2
        )

    # (4) the sums are asserted NOT to reconcile, so nobody later "fixes" them into a total
    assert sum(row["resources"] for row in coverage["tags_in_use"]) >= len(coverage["tags_in_use"])


def test_tags_in_use_reconciles_with_the_coverage_ratio():
    """BL-101's Done-when clause, uncapped."""
    bundles = [do_bundle(), soc_bundle()]
    _assert_aggregation_reconciles(
        compose(bundles)["tag_coverage"], [b["inventory"] for b in bundles]
    )


def test_the_aggregation_still_reconciles_when_the_cap_bites():
    """The same invariant with `top_untagged` below the tag count.

    r1's version read the carrier set off `tags_in_use` — the *capped* list — so a resource
    whose only tag fell below the cap dropped out of the derived set while staying a carrier,
    and the assertion would have gone red on correct behaviour. It passed only because the
    fixture had fewer tags than `top_k`. This is the case that would have caught it.
    """
    bundle = _multi_tag_bundle()
    coverage = compose([bundle], top_untagged=2)["tag_coverage"]
    assert coverage["tags_in_use_total"] == 4
    assert len(coverage["tags_in_use"]) == 2
    assert coverage["tags_not_shown"] == 2, "the cap must actually bite for this test to mean anything"
    _assert_aggregation_reconciles(coverage, [bundle["inventory"]])


def test_tags_in_use_is_a_cost_ordered_prefix_of_the_full_set():
    """The payload-view invariant, kept separate from the aggregation one."""
    bundle = _multi_tag_bundle()
    full = compose([bundle], top_untagged=99)["tag_coverage"]
    capped = compose([bundle], top_untagged=2)["tag_coverage"]

    assert [r["tag"] for r in capped["tags_in_use"]] == [r["tag"] for r in full["tags_in_use"]][:2]
    assert capped["tags_in_use_total"] == full["tags_in_use_total"]
    assert capped["tags_not_shown"] == capped["tags_in_use_total"] - len(capped["tags_in_use"])
    assert full["tags_not_shown"] == 0
    # Cost-ordered, descending.
    costs = [r["monthly_cost_estimate"] for r in full["tags_in_use"]]
    assert costs == sorted(costs, reverse=True)


def test_the_tag_columns_overlap_and_the_report_says_so():
    """B2: the cost column is real money that does not sum to a total, rendered beside money
    that does. The numbers are right for what they measure; the note says what they measure."""
    bundle = _multi_tag_bundle()
    inventory = bundle["inventory"]
    coverage = compose([bundle], top_untagged=99)["tag_coverage"]
    rows = {row["tag"]: row for row in coverage["tags_in_use"]}

    assert rows["env=prod"]["resources"] == 2
    assert rows["team=core"]["resources"] == 1
    # The columns overlap by construction: resources[0] carries two tags, so the row-slots
    # exceed the carriers. Derived from the data rather than hardcoded — the fixture also
    # carries a pre-existing tag, and a hardcoded total would have been wrong about it.
    slots = sum(r["resources"] for r in rows.values())
    carriers = len(_carriers([inventory]))
    assert coverage["tagged"] == carriers
    assert slots == carriers + 1, f"expected exactly one doubly-tagged resource; slots={slots} carriers={carriers}"
    assert slots > coverage["tagged"]

    # The doubly-tagged resource's estimate is counted under BOTH of its tags.
    own = compose_report_data.money(inventory["resources"][0].get("monthly_cost_estimate"))
    assert rows["team=core"]["monthly_cost_estimate"] == own
    assert rows["env=prod"]["monthly_cost_estimate"] >= own


def test_the_reconciliation_check_fails_against_a_deliberately_broken_fixture():
    """The anti-vacuity control, rewritten at r2 — **and it is run, not described.**

    r1's control was inherited from r0, where it guarded an assertion since called nearly
    vacuous; a control written against a vacuous assertion is not evidence about the ones
    that replaced it. Each break below is executed and the assertion it falsifies is named.

    The breaks are **asymmetric on purpose**: they corrupt what `compose` produced while
    the expectation side is recomputed from the true inputs. A symmetric break — stripping
    every tag from the inventory — makes both sides empty and every assertion passes on
    `{} == {}`, which is why it is not used as the control.
    """
    bundles = [do_bundle(), soc_bundle()]
    inventories = [b["inventory"] for b in bundles]
    good = compose(bundles)["tag_coverage"]
    _assert_aggregation_reconciles(good, inventories)  # green before any break

    def broken(**overrides):
        payload = json.loads(json.dumps(good))
        payload.update(overrides)
        return payload

    # Break 1 -> falsifies assertion (1): the coverage figures are no longer the ratio's own.
    with pytest.raises(AssertionError):
        _assert_aggregation_reconciles(broken(tagged=good["tagged"] + 1), inventories)
    with pytest.raises(AssertionError):
        _assert_aggregation_reconciles(broken(coverage=0.9999), inventories)

    # Break 2 -> falsifies assertion (2): the full-set count no longer matches the inputs.
    with pytest.raises(AssertionError):
        _assert_aggregation_reconciles(
            broken(tags_in_use_total=good["tags_in_use_total"] + 1), inventories
        )

    # Break 3 -> falsifies assertion (3): a row's own count/cost no longer matches its carriers.
    bad_rows = json.loads(json.dumps(good["tags_in_use"]))
    assert bad_rows, "fixture no longer produces tag rows"
    bad_rows[0]["resources"] += 1
    with pytest.raises(AssertionError):
        _assert_aggregation_reconciles(broken(tags_in_use=bad_rows), inventories)

    bad_cost = json.loads(json.dumps(good["tags_in_use"]))
    bad_cost[0]["monthly_cost_estimate"] += 1.0
    with pytest.raises(AssertionError):
        _assert_aggregation_reconciles(broken(tags_in_use=bad_cost), inventories)

    # Assertion (4) is deliberately NOT controlled by a break, and that is stated rather
    # than papered over: it pins a NON-invariant (the sums do not reconcile), so there is
    # no "correct" value for a break to depart from. It exists to stop a later reader
    # turning the cost column into a total, and a test that fails when someone does that
    # would have to know what they intended.


def _tagged_account_inventory():
    """An inventory over the coverage threshold, so the governance rule actually fires.

    **No committed fixture does this.** Both `inventory_rules_positive` (16.67 %) and
    `inventory_soc_2026-07` (25 %) sit below the 50 % threshold, so on every fixture in the
    repo `account_uses_tags` is False and the rule reports nothing. Constructing the firing
    case is the only way to assert the state the report renders when it does fire.
    """
    inventory = load_fixture("inventory_rules_positive")
    resources = inventory["resources"]
    for resource in resources[: (len(resources) * 2) // 3]:
        resource["tags"] = ["env=prod"]
    for resource in resources[(len(resources) * 2) // 3 :]:
        resource["tags"] = []
    return inventory


def test_the_governance_rule_does_not_fire_below_the_threshold_and_says_so():
    """The state every committed fixture actually produces — and it is *not evaluated*,
    not *nothing found*. C6 records the distortion; this pins the payload that carries it."""
    block = compose()["orphans"]["reported"][0]
    assert block["account_uses_tags"] is False
    assert block["resources"] == []
    assert block["tag_coverage"] == 0.1667
    assert block["coverage_threshold"] == 0.5


def test_the_governance_reported_block_reaches_report_data_with_its_evidence():
    """BL-101: t2's rule fired in the pipeline and had no key in report_data since m1."""
    inventory = _tagged_account_inventory()
    orphans = detect_orphans.detect(inventory, REF)
    assert orphans["reported"]["untagged_in_tagged_account"]["resources"], (
        "constructed fixture no longer exercises the governance rule"
    )
    bundle = {"cost": load_fixture("cost_do_2026-07"), "inventory": inventory, "orphans": orphans}
    reported = compose([bundle])["orphans"]["reported"]
    assert len(reported) == 1
    block = reported[0]
    assert block["provider"] == "digitalocean"
    assert block["rule"] == "untagged_in_tagged_account"
    assert block["account_uses_tags"] is True
    assert block["tag_coverage"] == orphans["reported"]["untagged_in_tagged_account"]["tag_coverage"]
    assert [r["resource_id"] for r in block["resources"]] == [
        r["resource_id"] for r in orphans["reported"]["untagged_in_tagged_account"]["resources"]
    ]
    # Carried intact — the evidence is the point, and it is what the report renders.
    assert all(r["evidence"] for r in block["resources"])


def test_a_reported_entry_is_never_banded_as_a_candidate():
    """§t2's structural rule survives the passthrough: reported-only is not queueable."""
    report = compose()
    banded = {c["resource_id"] for band in report["orphans"]["by_band"] for c in band["candidates"]}
    for block in report["orphans"]["reported"]:
        for row in block["resources"]:
            assert "confidence" not in row
            assert "monthly_saving_estimate" not in row
    # And the totals count candidates only.
    assert report["orphans"]["totals"]["candidates"] == len(banded)


def test_untagged_spender_rows_carry_their_tags_and_the_key_is_always_present():
    """BL-101: absent-is-unknown applied to a list — `[]` and 'no key' are different."""
    top = compose([do_bundle(), soc_bundle()])["tag_coverage"]["top_untagged_spenders"]
    assert top, "fixture no longer produces untagged spenders"
    for row in top:
        assert "tags" in row
        assert row["tags"] == []  # by construction: these are the untagged


def test_the_cap_reports_what_it_dropped_in_both_states():
    """BL-121, mutation posture: the distinction is asserted in both directions."""
    full = compose([do_bundle(), soc_bundle()])
    assert full["tag_coverage"]["untagged_not_shown"] == 0  # 8 untagged, default cap 10

    capped = compose([do_bundle(), soc_bundle()], top_untagged=3)
    assert len(capped["tag_coverage"]["top_untagged_spenders"]) == 3
    assert capped["tag_coverage"]["untagged"] == 8
    assert capped["tag_coverage"]["untagged_not_shown"] == 5
    # The dropped count is emitted as 0 rather than omitted, so "nothing dropped" and
    # "nobody counted" are distinguishable in the payload.
    assert "untagged_not_shown" in full["tag_coverage"]


def test_the_tag_table_reports_its_own_cap_in_both_states():
    """BL-121's sibling on the tag table, which BL-101's own text requires."""
    full = compose([do_bundle(), soc_bundle()])["tag_coverage"]
    assert full["tags_not_shown"] == 0
    assert len(full["tags_in_use"]) == full["tags_in_use_total"]

    capped = compose([do_bundle(), soc_bundle()], top_untagged=1)["tag_coverage"]
    assert len(capped["tags_in_use"]) == 1
    assert capped["tags_not_shown"] == capped["tags_in_use_total"] - 1
    assert capped["tags_not_shown"] > 0, "fixture no longer has enough distinct tags to cap"


def test_a_non_string_tag_element_is_counted_not_silently_dropped():
    """BL-127 / C6. Both states asserted: a clean inventory records no tag skip."""
    clean = compose([do_bundle()])
    assert not [s for s in clean["skipped"] if s.get("source") == "tags"]

    bundle = do_bundle()
    bundle["inventory"]["resources"][0]["tags"] = ["keep=true", 42, {"k": "v"}]
    broken = compose([bundle])
    tag_skips = [s for s in broken["skipped"] if s.get("source") == "tags"]
    assert len(tag_skips) == 2
    assert {s["reason"] for s in tag_skips} == {
        "tag element is int, not a string",
        "tag element is dict, not a string",
    }
    # The string tag survives; only the malformed elements are skipped.
    assert tag_skips[0]["resource_id"] == bundle["inventory"]["resources"][0]["resource_id"]


def test_the_tag_skip_sink_never_reaches_the_orphan_artifacts_skipped_list():
    """The cross-repo constraint, asserted here so it cannot regress silently.

    `../aetheris/scripts/sprint.sh`'s rule-legibility arm reads `orphans["skipped"]` and
    fires `illegible` on ANY entry, and separately asserts
    `evaluated + len(skipped) == len(resources)`. A tag-element skip is neither a whole
    resource nor unreadable, so routing one there would fail the sprint from another repo.
    """
    inventory = load_fixture("inventory_rules_positive")
    inventory["resources"][0]["tags"] = ["keep=true", 42]
    result = detect_orphans.detect(inventory, REF)
    assert result["skipped"] == []
    assert result["totals"]["resources"] + len(result["skipped"]) == len(inventory["resources"])


def test_compose_uses_the_shared_slug_and_carries_no_private_one():
    """BL-070's slug convergence — the only BL-070 target in m4 t5b's scope."""
    assert not hasattr(compose_report_data, "slug")
    assert compose_report_data.provider_slug is detect_orphans.provider_slug
    source = inspect.getsource(compose_report_data.persist_history)
    assert "provider_slug(bundle" in source
    # Not `"slug(bundle" not in source` — that substring is inside `provider_slug(bundle`,
    # which would make the assertion unfalsifiable. Match the whole call instead.
    assert "{slug(bundle" not in source
