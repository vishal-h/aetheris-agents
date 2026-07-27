"""Offline tests for the DO adapter — no token, no network beyond a local stub."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import fetch_do
from conftest import USE_CASE_ROOT, load_fixture

SCRIPT = USE_CASE_ROOT / "scripts" / "fetch_do.py"
PERIOD = "2026-07"

# Distinctive so a leak is unambiguous in captured output.
READONLY_TOKEN = "cc-readonly-SENTINEL-3f9a1c7e"
DECOY_TOKEN = "do-write-DECOY-9b2f4d81"
DECOY_TOKEN_2 = "do-write-DECOY-alt-5e1c0a22"


def run_main(stub, tmp_path, period=PERIOD, extra=None):
    argv = [
        "--output-dir", str(tmp_path),
        "--period", period,
        "--api-base", stub.api_base,
        "--retry-base-delay", "0",
        "--max-retries", "0",
    ]
    return fetch_do.main(argv + (extra or []))


# --------------------------------------------------------------------- normalizers


def test_normalize_droplet_uses_the_api_price_not_an_estimate():
    raw = load_fixture("do_droplets_page1")["droplets"][0]
    out = fetch_do.normalize_droplet(raw)
    assert out["type"] == "droplet"
    assert out["monthly_cost_estimate"] == float(raw["size"]["price_monthly"])
    assert out["raw_ref"] == f"do://droplets/{raw['id']}"
    assert out["attached_to"] is None


def test_normalize_volume_attached_and_unattached():
    volumes = load_fixture("do_volumes")["volumes"]
    attached = fetch_do.normalize_volume(volumes[0])
    orphan = fetch_do.normalize_volume(volumes[-1])

    assert attached["attached_to"] == str(volumes[0]["droplet_ids"][0])
    assert attached["state"] == "attached"
    # attached_to is null for an unattached resource — the primary orphan signal.
    assert orphan["attached_to"] is None
    assert orphan["state"] == "available"
    assert orphan["monthly_cost_estimate"] == 10.0  # 100 GiB * $0.10
    assert orphan["raw_ref"] == "do://volumes/vol-orphan-1"


def test_normalize_reserved_ip_costs_only_while_unassigned():
    ips = load_fixture("do_reserved_ips")["reserved_ips"]
    assigned = fetch_do.normalize_reserved_ip(ips[0])
    unassigned = fetch_do.normalize_reserved_ip(ips[1])

    assert assigned["attached_to"] == "100000001"
    assert assigned["state"] == "assigned"
    assert assigned["monthly_cost_estimate"] == 0.0
    assert unassigned["attached_to"] is None
    assert unassigned["state"] == "unassigned"
    assert unassigned["monthly_cost_estimate"] == fetch_do.RESERVED_IP_UNASSIGNED_MONTHLY


def test_normalize_snapshot_keeps_source_association():
    snaps = load_fixture("do_snapshots")["snapshots"]
    with_source = fetch_do.normalize_snapshot(snaps[0])
    without_source = fetch_do.normalize_snapshot(snaps[1])

    assert with_source["attached_to"] == "100000001"
    assert with_source["monthly_cost_estimate"] == round(12.5 * 0.06, 2)
    assert without_source["attached_to"] is None
    assert without_source["created_at"] == "2024-12-15T02:00:00Z"


def test_normalize_load_balancer_without_backends():
    lbs = load_fixture("do_load_balancers")["load_balancers"]
    orphan = fetch_do.normalize_load_balancer(
        next(lb for lb in lbs if lb["id"] == "lb-orphan-1")
    )
    assert orphan["attached_to"] is None
    assert orphan["monthly_cost_estimate"] == 12.0
    assert orphan["tags"] == []  # load balancers carry `tag`, not `tags`


def test_tag_targeted_load_balancer_is_not_reported_unattached():
    """A tag-targeted LB has no droplet_ids but is emphatically not idle. Emitting
    attached_to: null here would false-positive t2's idle-LB rule, and the normalizer is
    frozen after m1 — so the tag has to survive normalization."""
    lbs = load_fixture("do_load_balancers")["load_balancers"]
    tagged = fetch_do.normalize_load_balancer(
        next(lb for lb in lbs if lb["id"] == "lb-tagged-1")
    )
    assert tagged["attached_to"] is not None
    assert tagged["attached_to"] == "tag:web"
    assert tagged["tags"] == ["web"]


def test_tags_of_handles_both_do_spellings():
    assert fetch_do.tags_of({"tags": ["a", "b"]}) == ["a", "b"]
    assert fetch_do.tags_of({"tag": "solo"}) == ["solo"]
    assert fetch_do.tags_of({"tag": None}) == []
    assert fetch_do.tags_of({}) == []


# ---------------------------------------------------------------- cost normalization


def test_cost_lines_are_service_granular_never_resource_attributed():
    summary = load_fixture("do_invoice_summary")
    invoice = load_fixture("do_invoices")["invoice_preview"]
    snapshot = fetch_do.normalize_cost(summary, invoice, "acct-1", PERIOD)

    assert snapshot["source_granularity"] == "service"
    assert snapshot["provider"] == "digitalocean"
    assert snapshot["currency"] == "USD"
    for line in snapshot["line_items"]:
        assert line["resource_id"] is None
        assert line["region"] is None
        assert line["usage_qty"] is None
        assert line["usage_unit"] is None
        assert set(line) == {
            "service", "resource_id", "region", "amount", "usage_qty", "usage_unit", "tags"
        }


def test_cost_snapshot_aggregates_repeated_services_and_preserves_the_total():
    summary = load_fixture("do_invoice_summary")
    invoice = load_fixture("do_invoices")["invoice_preview"]
    snapshot = fetch_do.normalize_cost(summary, invoice, "acct-1", PERIOD)

    services = [line["service"] for line in snapshot["line_items"]]
    assert len(services) == len(set(services)), "each service appears once"
    # DO returns three separate 'Kubernetes Clusters' rows; they aggregate to one line.
    k8s = next(line for line in snapshot["line_items"] if line["service"] == "Kubernetes Clusters")
    assert k8s["amount"] == round(141.14 + 25.07 + 2.29, 2)
    assert round(sum(line["amount"] for line in snapshot["line_items"]), 2) == \
        snapshot["totals"]["amount"]


# ----------------------------------------------------------------------- http client


def test_paginate_follows_the_next_link_across_pages(do_stub):
    do_stub.sequence(
        "/v2/droplets",
        [(200, load_fixture("do_droplets_page1")), (200, load_fixture("do_droplets_page2"))],
    )
    client = fetch_do.DOClient(READONLY_TOKEN, api_base=do_stub.api_base, retry_base_delay=0)
    droplets = client.paginate("/droplets", "droplets")

    assert len(droplets) == 3
    # Two requests, and the second was re-rooted onto the stub — not api.digitalocean.com.
    assert do_stub.paths() == ["/v2/droplets", "/v2/droplets"]
    assert do_stub.requests[1]["query"]["page"] == ["2"]


def test_retries_on_429_then_succeeds(do_stub):
    do_stub.sequence(
        "/v2/droplets",
        [
            (429, {"id": "too_many_requests"}, {"retry-after": "0"}),
            (200, load_fixture("do_droplets_page2")),
        ],
    )
    client = fetch_do.DOClient(
        READONLY_TOKEN, api_base=do_stub.api_base, retry_base_delay=0, max_retries=3
    )
    assert len(client.paginate("/droplets", "droplets")) == 1
    assert len(do_stub.requests) == 2


def test_retries_on_500_then_gives_up_with_api_error(do_stub):
    do_stub.route("/v2/droplets", {"id": "server_error"}, status=500)
    client = fetch_do.DOClient(
        READONLY_TOKEN, api_base=do_stub.api_base, retry_base_delay=0, max_retries=2
    )
    with pytest.raises(fetch_do.DOAPIError):
        client.get("/droplets")
    assert len(do_stub.requests) == 3  # initial + 2 retries


def test_401_raises_auth_error(do_stub):
    do_stub.route("/v2/account", {"id": "unauthorized"}, status=401)
    client = fetch_do.DOClient(READONLY_TOKEN, api_base=do_stub.api_base, retry_base_delay=0)
    with pytest.raises(fetch_do.DOAuthError):
        client.get("/account")


# ------------------------------------------------------------ shadow guard (D2 / §P1)


def test_load_token_reads_only_the_cloudcost_variable():
    env = {"CLOUDCOST_DO_TOKEN": READONLY_TOKEN, "DO_TOKEN": DECOY_TOKEN}
    assert fetch_do.load_token(env) == READONLY_TOKEN


def test_missing_cloudcost_token_raises_rather_than_falling_back_to_a_decoy():
    """Shadow guard, absence half: with only the default-pickup variables set, the
    adapter must refuse — never silently authenticate with the stray token."""
    env = {"DO_TOKEN": DECOY_TOKEN, "DIGITALOCEAN_ACCESS_TOKEN": DECOY_TOKEN_2}
    with pytest.raises(fetch_do.DOAuthError) as excinfo:
        fetch_do.load_token(env)
    assert "CLOUDCOST_DO_TOKEN" in str(excinfo.value)
    assert DECOY_TOKEN not in str(excinfo.value)


def test_adapter_authenticates_with_cloudcost_token_not_the_decoys(
    full_stub, tmp_path, monkeypatch
):
    """Shadow guard, presence half: with decoy DO_TOKEN/DIGITALOCEAN_ACCESS_TOKEN set to
    different values, every outgoing request must carry the CLOUDCOST_DO_TOKEN bearer."""
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    monkeypatch.setenv("DO_TOKEN", DECOY_TOKEN)
    monkeypatch.setenv("DIGITALOCEAN_ACCESS_TOKEN", DECOY_TOKEN_2)

    assert run_main(full_stub, tmp_path) == 0

    assert full_stub.requests, "the adapter made no requests"
    assert set(full_stub.auth_headers) == {f"Bearer {READONLY_TOKEN}"}
    recorded = json.dumps([r["headers"] for r in full_stub.requests])
    assert DECOY_TOKEN not in recorded
    assert DECOY_TOKEN_2 not in recorded


def test_warn_shadowing_env_names_the_variable_but_never_its_value(capsys):
    fetch_do.warn_shadowing_env({"DO_TOKEN": DECOY_TOKEN})
    captured = capsys.readouterr()
    assert "DO_TOKEN" in captured.err
    assert "IGNORED" in captured.err
    assert DECOY_TOKEN not in captured.err


# --------------------------------------------------------------------- leak guard


def test_auth_failure_does_not_leak_the_token_to_stdout_or_stderr(do_stub, tmp_path):
    """Leak guard: drive a real 401 through the CLI and prove the token appears in
    neither stream (D2 — the trajectory captures both)."""
    do_stub.route("/v2/account", {"id": "unauthorized", "message": "Unable to authenticate"},
                  status=401)
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--output-dir", str(tmp_path),
            "--period", PERIOD,
            "--api-base", do_stub.api_base,
            "--retry-base-delay", "0",
        ],
        cwd=USE_CASE_ROOT,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin", "CLOUDCOST_DO_TOKEN": READONLY_TOKEN},
    )

    assert result.returncode == 1
    assert READONLY_TOKEN not in result.stdout
    assert READONLY_TOKEN not in result.stderr
    assert "CLOUDCOST_DO_TOKEN" in result.stderr  # it names the variable, not the value


def test_emitted_files_never_contain_the_token(full_stub, tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    assert run_main(full_stub, tmp_path) == 0
    for path in tmp_path.glob("*.json"):
        assert READONLY_TOKEN not in path.read_text()


# ------------------------------------------------------------------------ end to end


def test_main_writes_both_normalized_files(full_stub, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    assert run_main(full_stub, tmp_path) == 0

    costs = json.loads((tmp_path / f"do_costs_{PERIOD}.json").read_text())
    inventory = json.loads((tmp_path / f"do_inventory_{PERIOD}.json").read_text())

    assert costs["period"] == PERIOD
    assert costs["account"] == "11111111-2222-3333-4444-555555555555"
    assert costs["totals"]["amount"] == 172.21
    assert costs["balance"]["month_to_date_usage"] == 173.65
    assert costs["provider_extra"]["billing_history"], "billing history is fetched"
    assert costs["provider_extra"]["invoice"]["status"] == "preview"

    assert inventory["provider"] == "digitalocean"
    # 3 droplets (paginated) + 4 volumes + 2 reserved IPs + 2 snapshots + 4 LBs
    assert len(inventory["resources"]) == 15
    for resource in inventory["resources"]:
        assert resource["raw_ref"].startswith("do://")
        assert set(resource) == {
            "resource_id", "type", "name", "region", "size", "state", "created_at",
            "last_activity_at", "attached_to", "monthly_cost_estimate", "tags", "raw_ref",
        }
        assert isinstance(resource["monthly_cost_estimate"], float)
        assert isinstance(resource["tags"], list)

    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "ok"
    assert summary["counts"]["resources"] == 15


def test_cost_snapshot_top_level_shape_matches_the_frozen_contract(
    full_stub, tmp_path, monkeypatch
):
    """Everything DO-shaped lives under provider_extra; the rest is the cross-provider
    contract downstream scripts may depend on."""
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    run_main(full_stub, tmp_path)
    costs = json.loads((tmp_path / f"do_costs_{PERIOD}.json").read_text())

    assert set(costs) == {
        "provider", "account", "period", "currency", "source_granularity",
        "line_items", "totals", "balance", "generated_at", "provider_extra",
    }
    assert set(costs["balance"]) == {
        "month_to_date_balance", "account_balance", "month_to_date_usage", "generated_at"
    }
    assert set(costs["provider_extra"]) == {"invoice", "billing_history"}


def test_inventory_surfaces_the_unattached_resources(full_stub, tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    run_main(full_stub, tmp_path)
    inventory = json.loads((tmp_path / f"do_inventory_{PERIOD}.json").read_text())

    orphans = [r for r in inventory["resources"] if r["attached_to"] is None]
    types = {r["type"] for r in orphans}
    assert {"volume", "reserved_ip", "load_balancer"} <= types


def test_a_failing_source_degrades_to_partial_rather_than_crashing(
    full_stub, tmp_path, monkeypatch, capsys
):
    """Stage CLIs degrade: one bad endpoint yields a partial envelope and exit 1, with the
    other resources still emitted."""
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    full_stub.route("/v2/snapshots", {"id": "server_error"}, status=500)

    assert run_main(full_stub, tmp_path) == 1

    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "partial"
    assert summary["errors"][0]["source"] == "/snapshots"

    inventory = json.loads((tmp_path / f"do_inventory_{PERIOD}.json").read_text())
    assert {r["type"] for r in inventory["resources"]} == {
        "droplet", "volume", "reserved_ip", "load_balancer"
    }


def test_missing_invoice_for_period_is_reported_not_invented(full_stub, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CLOUDCOST_DO_TOKEN", READONLY_TOKEN)
    assert run_main(full_stub, tmp_path, period="1999-01") == 1
    summary = json.loads(capsys.readouterr().out)
    assert summary["status"] == "partial"
    assert "no DigitalOcean invoice found" in summary["errors"][0]["error"]
    # Inventory still lands; only the cost half is missing.
    assert (tmp_path / "do_inventory_1999-01.json").exists()
    assert not (tmp_path / "do_costs_1999-01.json").exists()


# -------------------------------------------------------------- dir-name collision


def test_cloudcost_is_not_an_importable_stdlib_or_site_package(tmp_path):
    """The use-case dir name must not shadow (or be shadowed by) an installed module.

    Run from a cwd that does not contain `cloudcost/` — from the repo root Python's
    implicit-namespace-package rule makes the bare directory importable, which proves
    nothing about the name being safe.
    """
    result = subprocess.run(
        [sys.executable, "-c", "import cloudcost"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "No module named 'cloudcost'" in result.stderr
