"""Offline tests for the Linode adapter — no token, no network beyond a local stub."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import _normalized
import fetch_linode
from conftest import FIXTURES, LINODE_PERIOD, USE_CASE_ROOT, load_fixture

SCRIPT = USE_CASE_ROOT / "scripts" / "fetch_linode.py"
PERIOD = LINODE_PERIOD

# Distinctive so a leak is unambiguous in captured output.
READONLY_TOKEN = "cc-linode-readonly-SENTINEL-3f9a1c7e"
DECOY_TOKEN = "linode-cli-DECOY-9b2f4d81"
DECOY_TOKEN_2 = "linode-write-DECOY-alt-5e1c0a22"


def run_main(stub, tmp_path, period=PERIOD, extra=None):
    argv = [
        "--output-dir", str(tmp_path),
        "--period", period,
        "--api-base", stub.api_base,
        "--retry-base-delay", "0",
        "--max-retries", "0",
    ]
    return fetch_linode.main(argv + (extra or []))


def rows(fixture):
    return load_fixture(fixture)["data"]


def prices_from_fixtures():
    """A `Prices` loaded straight from the recorded price tables, without a client."""
    prices = fetch_linode.Prices()
    for fixture, path in (
        ("linode_types_linode", "/linode/types"),
        ("linode_types_volumes", "/volumes/types"),
        ("linode_types_nodebalancers", "/nodebalancers/types"),
    ):
        for row in rows(fixture):
            monthly = (row.get("price") or {}).get("monthly")
            if monthly is not None:
                prices.by_type[row["id"]] = monthly
                prices.sources[row["id"]] = f"{path} .price.monthly"
            for region_price in row.get("region_prices") or []:
                prices.by_type_region[(row["id"], region_price["id"])] = region_price["monthly"]
    return prices


# ------------------------------------------------------------------ canonical vocabulary


def test_the_adapter_emits_the_canonical_type_vocabulary_not_linodes_own(
    full_linode_stub, tmp_path, monkeypatch
):
    """m2 t2 a′: `type` is schema-level, and every adapter emits from the closed set.

    LOAD-BEARING — do not weaken. This test and its `state` sibling below are the only ones
    binding a canonical *string value* to the schema. Everywhere else the adapter and the rule
    engine import the same constant, so a rename moves both sides together and every test
    stays green. What catches a vocabulary rename is Linode's own raw API value — `offline`,
    a NodeBalancer, an Image — no longer mapping onto the renamed constant. Assert the
    literals, not the constants, or the drift goes silent.
    """
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    inventory = json.loads((tmp_path / f"linode_inventory_{PERIOD}.json").read_text())

    types = {r["type"] for r in inventory["resources"]}
    assert types == {"compute_instance", "volume", "load_balancer"}
    assert types <= _normalized.CANONICAL_TYPES
    # Linode's own spellings are gone from the emitted contract; they survive only in
    # raw_ref, which is provenance — a pointer back to the Linode object, not vocabulary.
    assert not types & {"linode", "nodebalancer", "image"}
    assert all(r["raw_ref"].startswith("linode://") for r in inventory["resources"])


def test_the_adapter_never_spells_a_canonical_value_locally():
    """Every canonical `type`/`state` value is imported from `_normalized`, never re-typed.

    The `test_detect_orphans.py:793` provider-agnostic-guard precedent, pointed the other way:
    there it proves the rules read no provider field; here it proves the adapter declares no
    schema value. A local spelling would let the vocabulary drift on exactly the seam
    `_normalized` exists to remove.
    """
    # Comment lines are dropped first: the canonical words appear all through the adapter's
    # prose, where they are documentation rather than vocabulary — including in the evidence
    # citation that quotes the provider's own `id: "volume"` price row.
    source = "\n".join(
        line for line in SCRIPT.read_text().splitlines() if not line.lstrip().startswith("#")
    )

    # ONE exemption, and it is a genuine collision rather than a weakening: Linode's
    # /volumes/types row is keyed `id: "volume"`, which is the provider's own wire value and
    # happens to be spelled exactly like the canonical type. It must stay a literal — it is
    # what the price lookup sends — so the guard exempts the single assignment that carries
    # it and still fails on any other occurrence, including a second one on that same line.
    assert 'VOLUME_TYPE_ID = "volume"' in source
    assert source.count('"volume"') == 1, (
        "the price-table id is the only place `volume` may appear as a literal; a second "
        "occurrence is either a canonical value spelled locally or an unlabelled duplicate"
    )
    source = source.replace('VOLUME_TYPE_ID = "volume"', "VOLUME_TYPE_ID = <exempt>")

    # Strings only — the canonical words appear throughout the prose, where they are
    # documentation rather than vocabulary.
    literals = set(re.findall(r'"([a-z_]+)"', source)) | set(re.findall(r"'([a-z_]+)'", source))
    canonical = set(_normalized.CANONICAL_TYPES) | {_normalized.STATE_STOPPED}
    assert not (literals & canonical), (
        f"canonical values spelled as literals in fetch_linode.py: {sorted(literals & canonical)}"
    )
    for name in ("TYPE_COMPUTE_INSTANCE", "TYPE_VOLUME", "TYPE_LOAD_BALANCER",
                 "TYPE_SNAPSHOT", "TYPE_STATIC_IP", "STATE_STOPPED"):
        assert name in source


# ------------------------------------------------------------------------------- §D-L4


def test_offline_is_the_canonical_stopped_state_and_stopped_itself_is_not():
    """m3 §D-L4, settled from the recorded fixture and not from the spelling.

    LOAD-BEARING — see the canonical-type test above. The first assertion is against the
    literal `"stopped"` on purpose; the second, against `STATE_STOPPED`, would pass under any
    rename on its own.

    The trap this guards: Linode's enum contains BOTH `offline` and `stopped`, and `stopped`
    collides literally with the canonical value while the spec documents it as what
    *maintenance mode* produces. Mapping by spelling would fire the stopped-compute rule for
    maintenance and never for the ordinary powered-off case.
    """
    raw = next(r for r in rows("linode_instances_page1") if r["status"] == "offline")
    assert raw["id"] == 19294655, "the recorded §D-L4 evidence row"

    out = fetch_linode.normalize_instance(raw, prices_from_fixtures(), [])
    assert out["state"] == "stopped"
    assert out["state"] == _normalized.STATE_STOPPED

    # `stopped` (maintenance) and `billing_suspension` are terminal but are NOT "the operator
    # turned this off and forgot it" — they pass through as the provider reports them.
    for passthrough in ("stopped", "billing_suspension", "running", "provisioning"):
        out = fetch_linode.normalize_instance(
            {**raw, "status": passthrough}, prices_from_fixtures(), []
        )
        assert out["state"] == passthrough


def test_a_powered_off_instance_still_carries_its_full_monthly_cost():
    """§Seam 3 — Linode is DO-shaped, not AWS-shaped: it bills a powered-off instance, so the
    stopped-compute rule's own-cost term is non-zero and must not be zeroed the way
    `fetch_aws.instance_compute_estimate` zeroes a stopped EC2 instance.

    The figure is checked against the account's own invoice line, not against a table.
    """
    raw = next(r for r in rows("linode_instances_page1") if r["status"] == "offline")
    out = fetch_linode.normalize_instance(raw, prices_from_fixtures(), [])
    assert out["state"] == _normalized.STATE_STOPPED
    assert out["monthly_cost_estimate"] == 48.0

    billed = next(
        item for item in rows("linode_invoice_items") if f"({raw['id']})" in item["label"]
    )
    assert billed["amount"] == out["monthly_cost_estimate"]


# ------------------------------------------------------------- §D-L1 / §D-L3 / §D-L10


def test_cost_lines_are_service_granular_never_resource_attributed():
    """§D-L3 — an invoice item carries no machine-readable identifier, so every line is
    service-granular with `resource_id: null`, and the label's resource identity is discarded
    rather than parsed into attribution."""
    invoice = rows("linode_invoices")[-1]
    out = fetch_linode.normalize_cost(invoice, rows("linode_invoice_items"), "acct", PERIOD)

    assert out["source_granularity"] == "service"
    assert all(line["resource_id"] is None for line in out["line_items"])
    # 19 per-resource invoice rows collapse to their services.
    assert len(rows("linode_invoice_items")) == 19
    assert {line["service"] for line in out["line_items"]} == {
        "Linode 8GB", "Linode 16GB", "Linode 4GB", "Linode 2GB", "Nanode 1GB",
        "NodeBalancer", "Storage Volume", "LKE Standard Availability",
        "Inbound Data Processing Basic", "Outbound Data Processing Basic",
    }
    # No resource identity survives into the service name.
    assert not any(re.search(r"\(\d+\)", line["service"]) for line in out["line_items"])


def test_service_of_discards_resource_identity_without_extracting_it():
    assert fetch_linode.service_of("Linode 8GB - zz-ct-ravendb (19294655)") == "Linode 8GB"
    assert (
        fetch_linode.service_of("Storage Volume - pvc-0a8dce06b486430a (9022878) - 10 GiB")
        == "Storage Volume"
    )
    # No separator at all: the trailing resource id still has to go, or two lines of one
    # service never group.
    assert (
        fetch_linode.service_of("Outbound Data Processing Basic (1433944)")
        == "Outbound Data Processing Basic"
    )
    assert fetch_linode.service_of(None) == "Unknown"
    assert fetch_linode.service_of("   ") == "Unknown"


def test_line_items_reconcile_to_the_invoice_total():
    invoice = rows("linode_invoices")[-1]
    out = fetch_linode.normalize_cost(invoice, rows("linode_invoice_items"), "acct", PERIOD)
    assert round(sum(line["amount"] for line in out["line_items"]), 2) == 422.0
    assert out["totals"]["amount"] == invoice["total"] == 422.0


def test_tax_is_its_own_line_and_the_total_stays_post_tax():
    """§D-L1 — `totals.amount` is `invoice.total`, described by the spec as the amount **after
    taxes**, and the tax is carried as its own line so Σ lines still reconciles. This matches
    what AWS already ships, where Cost Explorer returns `Tax` as one of its SERVICE groups.

    The live account is zero-rated, so this is the one place the suite must use a synthetic
    invoice — the recording cannot exercise it.
    """
    invoice = rows("linode_invoice_taxed")[0]
    out = fetch_linode.normalize_cost(
        invoice, rows("linode_invoice_items_taxed"), "acct", PERIOD
    )

    tax_lines = [line for line in out["line_items"] if line["service"] == "Tax"]
    assert len(tax_lines) == 1
    assert tax_lines[0]["amount"] == 18.0
    assert tax_lines[0]["resource_id"] is None
    assert out["totals"]["amount"] == 118.0
    assert round(sum(line["amount"] for line in out["line_items"]), 2) == 118.0
    # The provider's own figures survive verbatim for audit.
    assert out["provider_extra"]["invoice"]["subtotal"] == 100.0
    assert out["provider_extra"]["invoice"]["tax_summary"] == [{"name": "IN GST", "tax": 18.0}]


def test_a_zero_rated_invoice_gets_no_tax_line():
    """The recorded invoice's tax is 0.00, and a $0.00 `Tax` row would be a line item for
    something that was never charged."""
    invoice = rows("linode_invoices")[-1]
    out = fetch_linode.normalize_cost(invoice, rows("linode_invoice_items"), "acct", PERIOD)
    assert invoice["tax"] == 0.0
    assert not [line for line in out["line_items"] if line["service"] == "Tax"]


def test_region_is_kept_for_a_single_region_service_and_null_when_it_spans_regions():
    """§D-L10 — `region` is populated because Linode is the first provider that has the
    concept on a cost line. A service billed in two regions has no single region, and the
    schema's rule is a real value or null, never a guess."""
    out = fetch_linode.normalize_cost(
        rows("linode_invoice_taxed")[0], rows("linode_invoice_items_taxed"), "acct", PERIOD
    )
    by_service = {line["service"]: line for line in out["line_items"]}
    assert by_service["Storage Volume"]["region"] == "ap-west"
    # Two `Linode 4GB` rows, ap-west and in-maa.
    assert by_service["Linode 4GB"]["region"] is None
    assert by_service["Linode 4GB"]["amount"] == 85.0


def test_the_covered_period_is_recorded_because_it_is_not_the_period_field():
    """An invoice issued in month M bills month M-1, so the covered range is stated rather
    than left to be inferred from `period`."""
    out = fetch_linode.normalize_cost(
        rows("linode_invoices")[-1], rows("linode_invoice_items"), "acct", PERIOD
    )
    assert out["period"] == "2026-08"
    assert out["provider_extra"]["invoice"]["period_covered"] == {
        "from": "2026-07-01T04:00:00",
        "to": "2026-08-01T03:59:59",
    }


def test_period_covered_is_null_when_no_item_states_a_bound():
    assert fetch_linode.period_covered([{"label": "x"}]) == {"from": None, "to": None}


def test_currency_is_asserted_with_its_basis():
    """§D-L2 — no currency field exists anywhere in the spec, so USD is adapter-asserted and
    ships with the spec version and ETag that justify it."""
    out = fetch_linode.normalize_cost(
        rows("linode_invoices")[-1], rows("linode_invoice_items"), "acct", PERIOD
    )
    assert out["currency"] == "USD"
    basis = out["provider_extra"]["currency_basis"]
    assert fetch_linode.SPEC_VERSION in basis and fetch_linode.SPEC_ETAG in basis


def test_balance_carries_the_uninvoiced_estimate():
    out = fetch_linode.normalize_cost(
        rows("linode_invoices")[-1], rows("linode_invoice_items"), "acct", PERIOD,
        balance=load_fixture("linode_account"),
    )
    account = load_fixture("linode_account")
    assert out["balance"]["month_to_date_usage"] == account["balance_uninvoiced"]
    assert out["balance"]["account_balance"] == account["balance"]


# ------------------------------------------------------------------------------ pricing


def test_volume_estimate_is_per_gb_at_the_live_rate():
    """U11, settled from the account's own invoice: 0.1/GB/month. The synthetic orphan volume
    is 20 GB, so it must price at 2.00 — a per-*volume* reading would give 0.10."""
    assert fetch_linode.VOLUME_PRICE_BASIS == "per_gb"
    out = fetch_linode.normalize_volume(
        rows("linode_volumes_orphan")[0], prices_from_fixtures(), []
    )
    assert out["monthly_cost_estimate"] == 2.0


def test_the_recorded_volume_estimate_matches_its_own_invoice_line():
    """The per-GB basis is not asserted against a constant but against the provider's bill:
    the 10 GB volume is billed 1.00, and the adapter derives 1.00 independently."""
    raw = rows("linode_volumes")[0]
    out = fetch_linode.normalize_volume(raw, prices_from_fixtures(), [])
    billed = next(
        item for item in rows("linode_invoice_items") if f"({raw['id']})" in item["label"]
    )
    assert out["monthly_cost_estimate"] == billed["amount"] == 1.0


def test_an_unpriced_volume_is_zero_plus_a_named_warning_never_a_borrowed_rate():
    warnings = []
    out = fetch_linode.normalize_volume(
        rows("linode_volumes_orphan")[0], fetch_linode.Prices(), warnings
    )
    assert out["monthly_cost_estimate"] == 0.0
    assert len(warnings) == 1 and "unknown, not zero" in warnings[0]


def test_nodebalancer_common_prices_through_the_types_id_not_its_own_type_value():
    """The object says `type: "common"`; the price table keys its rows `nodebalancer`. Reading
    the object's value as a price key yields None and would silently price every load balancer
    at 0.00."""
    raw = rows("linode_nodebalancers")[0]
    assert raw["type"] == "common"
    warnings = []
    out = fetch_linode.normalize_nodebalancer(raw, 2, prices_from_fixtures(), warnings)
    assert out["monthly_cost_estimate"] == 10.0
    assert warnings == []
    # And that figure is the one the account is actually billed.
    billed = next(
        item for item in rows("linode_invoice_items") if f"({raw['id']})" in item["label"]
    )
    assert billed["amount"] == 10.0


def test_an_unmapped_nodebalancer_type_is_zero_plus_a_named_warning():
    """`premium` has no evidenced price row, and guessing by name is the fabrication the
    milestone forbids."""
    raw = dict(rows("linode_nodebalancers")[0], type="premium")
    warnings = []
    out = fetch_linode.normalize_nodebalancer(raw, 2, prices_from_fixtures(), warnings)
    assert out["monthly_cost_estimate"] == 0.0
    assert len(warnings) == 1 and "premium" in warnings[0]


def test_prices_never_borrow_a_neighbouring_regions_rate():
    prices = prices_from_fixtures()
    # The volume table states region prices for id-cgk and br-gru only.
    assert prices.monthly("volume", "id-cgk") == 0.12
    assert prices.monthly("volume", "br-gru") == 0.14
    # ap-west has no region price, so the base rate applies — not one of the two above.
    assert prices.monthly("volume", "ap-west") == 0.1
    assert prices.monthly("no-such-type", "ap-west") is None


def test_a_missing_price_endpoint_warns_and_leaves_the_class_unpriced(linode_stub):
    """A failed price read must not fall back to a figure from anywhere else."""
    client = fetch_linode.LinodeClient(
        READONLY_TOKEN, api_base=linode_stub.api_base, max_retries=0, retry_base_delay=0
    )
    warnings = []
    prices = fetch_linode.Prices()
    prices.load(client, "/volumes/types", "volume", warnings)
    assert prices.by_type == {}
    assert len(warnings) == 1 and "unknown, not zero" in warnings[0]


# ---------------------------------------------------------------------------- inventory


def test_normalize_volume_attached_and_unattached():
    prices = prices_from_fixtures()
    attached = fetch_linode.normalize_volume(rows("linode_volumes")[0], prices, [])
    orphan = fetch_linode.normalize_volume(rows("linode_volumes_orphan")[0], prices, [])

    assert attached["attached_to"] == "99356691"
    # attached_to is null for an unattached resource — the primary orphan signal.
    assert orphan["attached_to"] is None
    # Linode's volume `status` is lifecycle, not attachment: both are `active`, so reading
    # the status as an attachment signal would call the orphan attached.
    assert attached["state"] == orphan["state"] == "active"
    assert orphan["raw_ref"] == "linode://volumes/9100001"


def test_nodebalancer_is_idle_with_zero_backends_across_configs_and_with_no_configs():
    prices = prices_from_fixtures()
    idle, config_less = rows("linode_nodebalancers_idle")

    assert fetch_linode.normalize_nodebalancer(idle, 0, prices, [])["attached_to"] is None
    # Zero configs is the degenerate case and must read the same way.
    assert (
        fetch_linode.normalize_nodebalancer(config_less, 0, prices, [])["attached_to"] is None
    )
    # A NodeBalancer serving backends is not idle.
    assert (
        fetch_linode.normalize_nodebalancer(rows("linode_nodebalancers")[0], 2, prices, [])[
            "attached_to"
        ]
        is not None
    )


def test_a_nodebalancer_whose_configs_could_not_be_read_is_not_reported_idle():
    """An unknown backend count is not zero. Rendering it as `attached_to: null` would fire
    the idle-load-balancer rule off a failed request."""
    out = fetch_linode.normalize_nodebalancer(
        rows("linode_nodebalancers")[0], None, prices_from_fixtures(), []
    )
    assert out["attached_to"] is not None
    assert "unknown" in out["attached_to"]


def test_backends_are_counted_up_plus_down_across_every_config(full_linode_stub):
    """`nodes_status.down` counts too: a backend that is registered but unhealthy is still a
    backend, so a load balancer with only down backends is misconfigured, not idle."""
    client = fetch_linode.LinodeClient(
        READONLY_TOKEN, api_base=full_linode_stub.api_base, max_retries=0, retry_base_delay=0
    )
    resources, errors = fetch_linode.fetch_nodebalancers(client, prices_from_fixtures(), [])
    assert errors == []
    # The recorded config fixture has two configs, each up=1 down=0.
    assert all(r["attached_to"] == "backends:2" for r in resources)


def test_image_has_no_source_and_no_price_so_it_ages_alone_at_zero():
    warnings = []
    single, multi = rows("linode_images_private")
    out = fetch_linode.normalize_image(single, warnings)

    assert out["type"] == "snapshot"
    # An image records no source, so the aged-snapshot rule's second signal has no field to
    # read and the rule fires on age alone.
    assert out["attached_to"] is None
    assert out["monthly_cost_estimate"] == 0.0
    assert len(warnings) == 1 and "unknown, not zero" in warnings[0]
    # `regions` is plural: one region resolves, several resolve to null.
    assert out["region"] == "ap-west"
    assert fetch_linode.normalize_image(multi, warnings)["region"] is None


def test_public_distribution_images_are_not_inventoried(
    full_linode_stub, tmp_path, monkeypatch
):
    """All 39 images on the account are Linode distribution images; they are not the
    account's property and cannot be its orphans."""
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    inventory = json.loads((tmp_path / f"linode_inventory_{PERIOD}.json").read_text())
    assert all(r["is_public"] for r in rows("linode_images"))
    assert not [r for r in inventory["resources"] if r["type"] == "snapshot"]


# --------------------------------------------------------------------------------- §D-L9


def test_only_reserved_addresses_are_emitted_as_static_ips():
    """§D-L9 — an automatically-assigned primary address is inseparable from its instance and
    can never be an orphan; emitting one would flag primaries, the exact false positive the
    design decision forbids."""
    assert all(not fetch_linode.is_reservable_address(r) for r in rows("linode_ips"))
    assert all(fetch_linode.is_reservable_address(r) for r in rows("linode_ips_reserved"))


def test_a_nodebalancer_address_is_not_read_as_unattached():
    """The load-bearing correction the live read forced: two recorded addresses carry
    `linode_id: null` while `assigned_entity` names the NodeBalancer each belongs to. Keying
    attachment on `linode_id` alone would report two in-service addresses as orphans."""
    nb_addresses = [r for r in rows("linode_ips") if r["linode_id"] is None]
    assert len(nb_addresses) == 2
    for raw in nb_addresses:
        assert raw["assigned_entity"]["type"] == "nodebalancer"
        out = fetch_linode.normalize_static_ip(raw)
        assert out["attached_to"] is not None
        assert out["state"] == "assigned"


def test_a_reserved_unassigned_address_is_the_orphan_shape_and_an_assigned_one_is_not():
    unassigned, assigned = rows("linode_ips_reserved")
    assert fetch_linode.normalize_static_ip(unassigned)["attached_to"] is None
    assert fetch_linode.normalize_static_ip(unassigned)["state"] == "unassigned"
    assert fetch_linode.normalize_static_ip(assigned)["attached_to"] == "linode:19294655"
    # An IP object carries no allocation timestamp, and the rule has no age threshold.
    assert fetch_linode.normalize_static_ip(unassigned)["created_at"] is None


def test_an_empty_static_ip_class_states_the_counts_behind_the_zero(
    full_linode_stub, tmp_path, monkeypatch, capsys
):
    """*Absent is unknown, not zero.* The account holds no reserved address, so the class is
    legitimately empty — and the survey is what makes that readable as an observation rather
    than as a class nobody looked at."""
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    summary = json.loads(capsys.readouterr().out)

    survey = summary["surveyed"]["networking_ips"]
    assert survey["addresses_read"] == len(rows("linode_ips"))
    assert survey["reserved"] == 0
    assert survey["emitted_as_static_ip"] == 0
    assert summary["not_inventoried"] == []


# ---------------------------------------------------------------------- §D-L6 degradation


def test_a_failing_class_is_an_error_plus_not_inventoried_never_an_empty_list(
    full_linode_stub, tmp_path, monkeypatch, capsys
):
    """§D-L6 — the hazard `fetch_aws.py:98-102` already adjudicated once: a denied class must
    never produce an empty inventory on a green run, "with a reason that reads plausibly and
    is wrong"."""
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    full_linode_stub.route("/v4/volumes", {"errors": [{"reason": "Unauthorized"}]}, status=400)

    exit_code = run_main(full_linode_stub, tmp_path)
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert summary["status"] == "partial"
    assert [e["source"] for e in summary["errors"]] == ["/volumes"]
    assert [n["class"] for n in summary["not_inventoried"]] == ["/volumes"]
    # The class is absent from the inventory, and the summary says why — it does not read as
    # "the account owns no volumes".
    inventory = json.loads((tmp_path / f"linode_inventory_{PERIOD}.json").read_text())
    assert not [r for r in inventory["resources"] if r["type"] == "volume"]


def test_excluded_classes_are_recorded_with_reasons_never_left_as_absences(
    full_linode_stub, tmp_path, monkeypatch, capsys
):
    """Milestone done-when 8. A class nobody swept is a decision, and a decision with no
    record is indistinguishable from an oversight."""
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    summary = json.loads(capsys.readouterr().out)

    classes = {row["class"] for row in summary["exclusions"]}
    assert {"managed_database", "backup", "object_storage", "lke", "firewall", "vpc"} <= classes
    assert all(row["reason"] for row in summary["exclusions"])


def test_a_missing_invoice_is_reported_not_invented(
    full_linode_stub, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    exit_code = run_main(full_linode_stub, tmp_path, period="2019-01")
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert summary["status"] == "partial"
    assert "no Linode invoice issued in period 2019-01" in summary["errors"][0]["error"]
    # The inventory still lands: one failing source does not abort the sweep.
    assert (tmp_path / "linode_inventory_2019-01.json").exists()


# ------------------------------------------------------------------- transport / paging


def test_paginate_walks_page_numbers_across_pages(linode_stub):
    """Linode pages by incrementing an integer against a stated total, not by following a
    `next` URL — so DO's re-rooting guard has no analogue and none is copied."""
    linode_stub.sequence(
        "/v4/things",
        [
            (200, {"data": [{"id": 1}], "page": 1, "pages": 2, "results": 2}),
            (200, {"data": [{"id": 2}], "page": 2, "pages": 2, "results": 2}),
        ],
    )
    client = fetch_linode.LinodeClient(READONLY_TOKEN, api_base=linode_stub.api_base)
    assert [row["id"] for row in client.paginate("/things")] == [1, 2]
    assert [r["query"]["page"] for r in linode_stub.requests] == [["1"], ["2"]]


def test_pagination_stops_at_the_stated_total_rather_than_looping(linode_stub):
    linode_stub.route("/v4/things", {"data": [{"id": 1}], "page": 1, "pages": 1, "results": 1})
    client = fetch_linode.LinodeClient(READONLY_TOKEN, api_base=linode_stub.api_base)
    assert len(client.paginate("/things")) == 1
    assert len(linode_stub.requests) == 1


def test_retries_on_429_then_succeeds(linode_stub):
    linode_stub.sequence(
        "/v4/account",
        [(429, {"errors": []}, {"retry-after": "0"}), (200, {"euuid": "ok"})],
    )
    client = fetch_linode.LinodeClient(
        READONLY_TOKEN, api_base=linode_stub.api_base, retry_base_delay=0
    )
    assert client.get("/account")["euuid"] == "ok"
    assert len(linode_stub.requests) == 2


def test_retries_on_500_then_gives_up_with_an_api_error(linode_stub):
    linode_stub.route("/v4/account", {"errors": []}, status=500)
    client = fetch_linode.LinodeClient(
        READONLY_TOKEN, api_base=linode_stub.api_base, max_retries=1, retry_base_delay=0
    )
    with pytest.raises(fetch_linode.LinodeAPIError):
        client.get("/account")


@pytest.mark.parametrize("status", [401, 403])
def test_a_rejected_credential_is_fatal_not_an_empty_account(linode_stub, status):
    linode_stub.route("/v4/account", {"errors": [{"reason": "Invalid Token"}]}, status=status)
    client = fetch_linode.LinodeClient(READONLY_TOKEN, api_base=linode_stub.api_base)
    with pytest.raises(fetch_linode.LinodeAuthError):
        client.get("/account")


# --------------------------------------------------------------------------- credentials


def test_load_token_reads_only_the_cloudcost_variable():
    assert fetch_linode.load_token({"CLOUDCOST_LINODE_TOKEN": READONLY_TOKEN}) == READONLY_TOKEN


def test_a_missing_token_raises_rather_than_falling_back_to_a_decoy():
    with pytest.raises(fetch_linode.LinodeAuthError) as exc:
        fetch_linode.load_token({"LINODE_CLI_TOKEN": DECOY_TOKEN, "LINODE_TOKEN": DECOY_TOKEN_2})
    message = str(exc.value)
    assert "CLOUDCOST_LINODE_TOKEN" in message
    # The error names the variables it refuses to read, and never their values.
    assert "LINODE_CLI_TOKEN" in message
    assert DECOY_TOKEN not in message and DECOY_TOKEN_2 not in message


def test_the_adapter_authenticates_with_the_cloudcost_token_not_the_decoys(
    full_linode_stub, tmp_path, monkeypatch
):
    """An observed wire fact, not test wiring: the stub records what was actually sent."""
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    monkeypatch.setenv("LINODE_CLI_TOKEN", DECOY_TOKEN)
    monkeypatch.setenv("LINODE_TOKEN", DECOY_TOKEN_2)

    run_main(full_linode_stub, tmp_path)

    sent = set(full_linode_stub.auth_headers)
    assert sent == {f"Bearer {READONLY_TOKEN}"}
    assert f"Bearer {DECOY_TOKEN}" not in sent
    assert f"Bearer {DECOY_TOKEN_2}" not in sent


def test_warn_shadowing_env_names_the_variable_but_never_its_value(capsys):
    present = fetch_linode.warn_shadowing_env(
        {"LINODE_CLI_TOKEN": DECOY_TOKEN, "LINODE_TOKEN": DECOY_TOKEN_2}, stream=sys.stderr
    )
    err = capsys.readouterr().err
    assert present == ["LINODE_CLI_TOKEN", "LINODE_TOKEN"]
    assert "LINODE_CLI_TOKEN" in err and "IGNORED" in err
    assert DECOY_TOKEN not in err and DECOY_TOKEN_2 not in err


def test_endpoint_redirection_variables_are_warned_about_and_never_read(capsys):
    """A hazard class neither predecessor has: these redirect *where a credential is sent*
    rather than which credential is used."""
    present = fetch_linode.warn_shadowing_env(
        {"LINODE_CLI_API_HOST": "attacker.example", "LINODE_CLI_API_SCHEME": "http"},
        stream=sys.stderr,
    )
    err = capsys.readouterr().err
    assert present == ["LINODE_CLI_API_HOST", "LINODE_CLI_API_SCHEME"]
    assert "redirects" in err
    # And the adapter's base URL is its own, unaffected by them.
    client = fetch_linode.LinodeClient(READONLY_TOKEN)
    assert client.api_base == fetch_linode.DEFAULT_API_BASE


def test_an_auth_failure_does_not_leak_the_token_to_stdout_or_stderr(
    linode_stub, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    linode_stub.route("/v4/account", {"errors": [{"reason": "Invalid Token"}]}, status=401)

    exit_code = run_main(linode_stub, tmp_path)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert READONLY_TOKEN not in captured.out
    assert READONLY_TOKEN not in captured.err


def test_an_error_body_echoing_the_token_is_redacted(linode_stub):
    """Belt and braces: if a provider ever reflected the credential back in an error body, it
    must not reach an exception message."""
    linode_stub.route("/v4/account", {"errors": [{"reason": f"bad {READONLY_TOKEN}"}]}, status=400)
    client = fetch_linode.LinodeClient(
        READONLY_TOKEN, api_base=linode_stub.api_base, max_retries=0
    )
    with pytest.raises(fetch_linode.LinodeAPIError) as exc:
        client.get("/account")
    assert READONLY_TOKEN not in str(exc.value)
    assert "***" in str(exc.value)


def test_the_emitted_files_never_contain_the_token(full_linode_stub, tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    for path in tmp_path.glob("*.json"):
        assert READONLY_TOKEN not in path.read_text()


def test_the_client_repr_carries_no_token():
    assert READONLY_TOKEN not in repr(fetch_linode.LinodeClient(READONLY_TOKEN))


# --------------------------------------------------------------------------------- main


def test_main_writes_both_normalized_files(full_linode_stub, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    exit_code = run_main(full_linode_stub, tmp_path)
    summary = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert summary["status"] == "ok"
    assert (tmp_path / f"linode_costs_{PERIOD}.json").exists()
    assert (tmp_path / f"linode_inventory_{PERIOD}.json").exists()
    assert summary["counts"]["resources"] == len(
        json.loads((tmp_path / f"linode_inventory_{PERIOD}.json").read_text())["resources"]
    )
    # BL-096 input: the adapter reports its own wall-clock.
    assert isinstance(summary["duration_ms"], int) and summary["duration_ms"] >= 0


def test_the_cost_snapshot_top_level_shape_matches_the_frozen_contract(
    full_linode_stub, tmp_path, monkeypatch
):
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    costs = json.loads((tmp_path / f"linode_costs_{PERIOD}.json").read_text())

    assert set(costs) == {
        "provider", "account", "period", "currency", "source_granularity", "line_items",
        "totals", "balance", "generated_at", "provider_extra",
    }
    assert costs["provider"] == "linode"
    assert set(costs["line_items"][0]) == {
        "service", "resource_id", "region", "amount", "usage_qty", "usage_unit", "tags",
    }


def test_the_inventory_shape_matches_the_frozen_contract(
    full_linode_stub, tmp_path, monkeypatch
):
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)
    inventory = json.loads((tmp_path / f"linode_inventory_{PERIOD}.json").read_text())

    assert set(inventory) == {"provider", "account", "period", "resources", "generated_at"}
    for resource in inventory["resources"]:
        assert set(resource) == {
            "resource_id", "type", "name", "region", "size", "state", "created_at",
            "last_activity_at", "attached_to", "monthly_cost_estimate", "tags", "raw_ref",
        }
    # §D-L5: no rate_basis companion on the frozen inventory resource.
    assert "rate_basis" not in json.dumps(inventory)


def test_the_normalized_inventory_is_readable_by_the_shared_rule_engine(
    full_linode_stub, tmp_path, monkeypatch
):
    """The whole bet, asserted at the seam: `detect_orphans.py` consumes this adapter's output
    with no Linode knowledge and no change of its own."""
    monkeypatch.setenv("CLOUDCOST_LINODE_TOKEN", READONLY_TOKEN)
    run_main(full_linode_stub, tmp_path)

    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "detect_orphans.py"),
         str(tmp_path / f"linode_inventory_{PERIOD}.json"), "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=USE_CASE_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["counts"]["skipped"] == 0


# --------------------------------------------------------------------- fixture hygiene


def test_no_committed_fixture_carries_a_credential_or_a_routable_address():
    """The recorder's scrub is a guarantee only if something checks it. Account identity,
    token-shaped strings and real addresses must not survive into the repo."""
    import ipaddress

    for path in sorted(FIXTURES.glob("linode_*.json")):
        text = path.read_text()
        assert not re.search(r"\b[0-9a-f]{64}\b", text, re.I), f"token-shaped string in {path.name}"
        assert "@" not in text.replace("cloudcost@example.invalid", ""), f"email in {path.name}"

        for candidate in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text):
            try:
                address = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            assert not address.is_global, f"routable IPv4 {candidate} in {path.name}"
        for candidate in re.findall(r"\b(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}\b", text, re.I):
            try:
                address = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            assert not address.is_global, f"routable IPv6 {candidate} in {path.name}"


def test_every_synthetic_fixture_says_so():
    """A synthetic fixture read as a recording is evidence that was never observed."""
    for name in ("linode_invoice_taxed", "linode_volumes_orphan", "linode_ips_reserved",
                 "linode_images_private", "linode_nodebalancers_idle"):
        assert "SYNTHETIC" in load_fixture(name)["_comment"]
    for name in ("linode_instances_page1", "linode_ips", "linode_invoice_items"):
        comment = load_fixture(name).get("_comment", "")
        assert "Recorded" in comment and "SYNTHETIC" not in comment


def test_cloudcost_is_not_an_importable_stdlib_or_site_package(tmp_path):
    """Guards the `conftest.py`-not-`__init__.py` convention: run from a directory that is not
    the repo, `import fetch_linode` must fail rather than resolve to something else."""
    result = subprocess.run(
        [sys.executable, "-c", "import fetch_linode"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError" in result.stderr
