"""Offline tests for the GitHub adapter — no token, no network beyond a local stub."""

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import _normalized
import fetch_github
from conftest import (
    FIXTURES,
    GITHUB_EMPTY_PERIOD,
    GITHUB_ORG,
    GITHUB_PERIOD,
    USE_CASE_ROOT,
    load_fixture,
)

SCRIPT = USE_CASE_ROOT / "scripts" / "fetch_github.py"
PERIOD = GITHUB_PERIOD
ORG = GITHUB_ORG

# Distinctive so a leak is unambiguous in captured output.
READONLY_TOKEN = "cc-github-readonly-SENTINEL-3f9a1c7e"
DECOY_TOKEN = "gh-write-DECOY-9b2f4d81"
DECOY_TOKEN_2 = "gh-write-DECOY-alt-5e1c0a22"

#: The exact top-level key set of the cost snapshot. Asserted as equality, not containment, so
#: a stray addition fails the suite (the m1 t1 Deviation-3 precedent, which all three
#: predecessors carry).
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

#: The twelve first-class fields on every resource, and the five on the inventory envelope.
#: Both are asserted as equality for the same reason — and for a fourth adapter that reason is
#: sharper than it was for the third: `pending_cancellation_date` has nowhere in this shape to
#: go (see the t2 implementation notes), and an adapter that quietly grew a thirteenth key to
#: carry it would be declaring its own shape.
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
FROZEN_INVENTORY_KEYS = {"provider", "account", "period", "resources", "generated_at"}


def run_main(stub, tmp_path, period=PERIOD, extra=None):
    argv = [
        "--output-dir", str(tmp_path),
        "--period", period,
        "--org", ORG,
        "--api-base", stub.api_base,
        "--retry-base-delay", "0",
        "--max-retries", "0",
    ]
    return fetch_github.main(argv + (extra or []))


def emitted(tmp_path, kind, period=PERIOD):
    return json.loads((tmp_path / f"github_{kind}_{period}.json").read_text())


def summary_fixture():
    return load_fixture("github_billing_usage_summary")


def detail_fixture():
    return load_fixture("github_billing_usage_detail")


def seat_rows():
    return load_fixture("github_copilot_seats")["seats"]


def seat_sku_row():
    return next(
        row for row in summary_fixture()["usageItems"] if row["sku"] == fetch_github.SEAT_SKU
    )


# ------------------------------------------------------------------------------- vocabulary


def test_the_adapter_never_spells_a_canonical_value_locally():
    """Every canonical `type`/`state` value is imported from `_normalized`, never re-typed.

    LOAD-BEARING — do not weaken to a constants check. A local spelling would let the
    vocabulary drift on exactly the seam `_normalized` exists to remove, and this adapter is
    the first to emit `seat`, so it is the first place that drift could start.
    """
    # Comment lines are dropped first: the canonical words appear all through the adapter's
    # prose, where they are documentation rather than vocabulary.
    source = "\n".join(
        line for line in SCRIPT.read_text().splitlines() if not line.lstrip().startswith("#")
    )

    literals = set(re.findall(r'"([a-z_]+)"', source)) | set(re.findall(r"'([a-z_]+)'", source))
    canonical = set(_normalized.CANONICAL_TYPES) | {_normalized.STATE_STOPPED}
    assert not (literals & canonical), (
        f"canonical values spelled as literals in fetch_github.py: {sorted(literals & canonical)}"
    )
    assert "TYPE_SEAT" in source


def test_cloudcost_is_not_an_importable_stdlib_or_site_package(tmp_path):
    """Guards the `conftest.py`-not-`__init__.py` convention: run from a directory that is not
    the repo, `import fetch_github` must fail rather than resolve to something else."""
    result = subprocess.run(
        [sys.executable, "-c", "import fetch_github"],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError" in result.stderr


# ------------------------------------------------------------------------------ credentials


def test_load_token_reads_only_the_cloudcost_variable():
    env = {"CLOUDCOST_GITHUB_TOKEN": READONLY_TOKEN, "GITHUB_TOKEN": DECOY_TOKEN}
    assert fetch_github.load_token(env) == READONLY_TOKEN


def test_a_missing_token_raises_rather_than_falling_back_to_a_decoy():
    """Shadow guard, absence half. This is the first provider whose shadowed names are
    routinely PRESENT — `gh` reads GH_TOKEN then GITHUB_TOKEN — so the refusal is the arm that
    does the work, not the presence warning."""
    with pytest.raises(fetch_github.GitHubAuthError) as exc:
        fetch_github.load_token({"GH_TOKEN": DECOY_TOKEN, "GITHUB_TOKEN": DECOY_TOKEN_2})
    message = str(exc.value)
    assert "CLOUDCOST_GITHUB_TOKEN" in message
    # The error names the variables it refuses to read, and never their values.
    assert "GH_TOKEN" in message and "GITHUB_TOKEN" in message
    assert DECOY_TOKEN not in message and DECOY_TOKEN_2 not in message


def test_the_shadow_list_is_ghs_own_precedence_chain():
    """Membership is `gh help environment`'s list, not a guess. The two documented pairs plus
    the convention-only spelling, which is warned about on convention grounds alone — the same
    honesty clause `fetch_linode.py` records for `LINODE_TOKEN`."""
    assert fetch_github.SHADOWING_ENV == (
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "GH_ENTERPRISE_TOKEN",
        "GITHUB_ENTERPRISE_TOKEN",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
    )
    # GH_CONFIG_DIR redirects which STORED credential gh picks up, and this adapter reads no
    # credential store. Excluded deliberately; a padded list is what the convention warns off.
    assert "GH_CONFIG_DIR" not in fetch_github.SHADOWING_ENV
    assert "GH_CONFIG_DIR" not in fetch_github.ENDPOINT_REDIRECT_ENV


def test_the_adapter_authenticates_with_the_cloudcost_token_not_the_decoys(
    full_github_stub, tmp_path, monkeypatch
):
    """An observed wire fact, not test wiring: the stub records what was actually sent."""
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    monkeypatch.setenv("GH_TOKEN", DECOY_TOKEN)
    monkeypatch.setenv("GITHUB_TOKEN", DECOY_TOKEN_2)

    assert run_main(full_github_stub, tmp_path) == 0

    assert full_github_stub.requests, "the adapter made no requests"
    assert set(full_github_stub.auth_headers) == {f"Bearer {READONLY_TOKEN}"}
    recorded = json.dumps([r["headers"] for r in full_github_stub.requests])
    assert DECOY_TOKEN not in recorded
    assert DECOY_TOKEN_2 not in recorded


def test_warn_shadowing_env_names_the_variable_but_never_its_value(capsys):
    present = fetch_github.warn_shadowing_env(
        {"GH_TOKEN": DECOY_TOKEN, "GITHUB_PERSONAL_ACCESS_TOKEN": DECOY_TOKEN_2},
        stream=sys.stderr,
    )
    err = capsys.readouterr().err
    assert present == ["GH_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"]
    assert "GH_TOKEN" in err and "IGNORED" in err
    assert DECOY_TOKEN not in err and DECOY_TOKEN_2 not in err


def test_endpoint_redirection_variables_are_warned_about_and_never_read(capsys):
    """The second class: these redirect *where a credential is sent* rather than which
    credential is used. `GH_HOST` is gh's own; `GITHUB_API_URL` is read by @actions/github."""
    present = fetch_github.warn_shadowing_env(
        {"GH_HOST": "attacker.example", "GITHUB_API_URL": "https://attacker.example/api/v3"},
        stream=sys.stderr,
    )
    err = capsys.readouterr().err
    assert present == ["GH_HOST", "GITHUB_API_URL"]
    assert "redirects" in err
    # And the adapter's base URL is its own, unaffected by them.
    client = fetch_github.GitHubClient(READONLY_TOKEN)
    assert client.api_base == fetch_github.DEFAULT_API_BASE


@pytest.mark.parametrize("status", [401, 403])
def test_a_rejected_credential_is_fatal_not_an_empty_account(github_stub, tmp_path, status):
    """403 is GitHub's answer to a fine-grained token missing an organisation permission as
    well as to a revoked one. Both must stop the run: a scope gap that produced an empty
    inventory on a green run would read exactly like an organisation with no seats."""
    github_stub.route("/user/orgs", {"message": "Bad credentials"}, status=status)
    client = fetch_github.GitHubClient(
        READONLY_TOKEN, api_base=github_stub.api_base, max_retries=0
    )
    with pytest.raises(fetch_github.GitHubAuthError):
        client.get("/user/orgs")


def test_an_auth_failure_does_not_leak_the_token_to_stdout_or_stderr(
    github_stub, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    github_stub.route("/user/orgs", {"message": "Bad credentials"}, status=401)

    exit_code = fetch_github.main([
        "--output-dir", str(tmp_path), "--period", PERIOD,
        "--api-base", github_stub.api_base, "--retry-base-delay", "0", "--max-retries", "0",
    ])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert READONLY_TOKEN not in captured.out
    assert READONLY_TOKEN not in captured.err
    # It names the variable, not the value, so the operator knows what to fix.
    assert "CLOUDCOST_GITHUB_TOKEN" in captured.err


def test_an_error_body_echoing_the_token_is_redacted(github_stub):
    """Belt and braces: if a provider ever reflected the credential back in an error body, it
    must not reach an exception message."""
    github_stub.route("/user/orgs", {"message": f"bad {READONLY_TOKEN}"}, status=400)
    client = fetch_github.GitHubClient(
        READONLY_TOKEN, api_base=github_stub.api_base, max_retries=0
    )
    with pytest.raises(fetch_github.GitHubAPIError) as exc:
        client.get("/user/orgs")
    assert READONLY_TOKEN not in str(exc.value)
    assert "***" in str(exc.value)


def test_the_emitted_files_never_contain_the_token(full_github_stub, tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    assert run_main(full_github_stub, tmp_path) == 0
    for path in tmp_path.glob("*.json"):
        assert READONLY_TOKEN not in path.read_text()


def test_the_client_repr_carries_no_token():
    assert READONLY_TOKEN not in repr(fetch_github.GitHubClient(READONLY_TOKEN))


# ----------------------------------------------------------------------------------- period


def test_a_malformed_period_is_rejected_before_any_request_is_made(github_stub, tmp_path):
    """§W5a — the first adapter to validate deliberately. The predecessors' checks are
    incidental to a conversion that happens to raise; this one exists because GitHub's usage
    DETAIL endpoint answers `month=13` with HTTP 200 and January's rows."""
    for bad in ("2026-13", "2026-00", "2026-7", "202607", "2026-07-01"):
        with pytest.raises(fetch_github.GitHubAPIError) as exc:
            fetch_github.validate_period(bad)
        assert "YYYY-MM" in str(exc.value)
    assert fetch_github.validate_period(PERIOD) == PERIOD


def test_a_malformed_period_costs_no_request_at_all(github_stub, tmp_path, monkeypatch):
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    exit_code = run_main(github_stub, tmp_path, period="2026-13")
    assert exit_code == 1
    assert github_stub.requests == [], "a rejected period must not reach the network"


def test_a_mismatched_period_echo_is_rejected():
    """§W5b — the summary endpoint is the only one of the two that echoes what it served, and
    this is the assertion that echo exists for. The failure it prevents is the quiet kind: real
    figures under a month they are not about, erroring nowhere."""
    summary = copy.deepcopy(summary_fixture())
    summary["timePeriod"] = {"year": 2026, "month": 6}
    with pytest.raises(fetch_github.GitHubAPIError) as exc:
        fetch_github.assert_period_echo(summary, PERIOD)
    assert "different month" in str(exc.value)
    # Control: the recorded body, unmutated, passes.
    fetch_github.assert_period_echo(summary_fixture(), PERIOD)


def test_a_missing_period_echo_is_rejected():
    """An absent echo is not a pass. The detail endpoint carries no `timePeriod` at all, so
    silently accepting its absence would make this assertion a no-op against the very body it
    exists to distinguish the summary from."""
    summary = copy.deepcopy(summary_fixture())
    del summary["timePeriod"]
    with pytest.raises(fetch_github.GitHubAPIError) as exc:
        fetch_github.assert_period_echo(summary, PERIOD)
    assert "echoed no timePeriod" in str(exc.value)


def test_the_recorded_detail_body_carries_no_period_echo_to_assert_against():
    """The premise the two tests above rest on, checked rather than assumed."""
    assert "timePeriod" not in detail_fixture()
    assert detail_fixture()["usageItems"], "the detail fixture must not be empty"


def test_an_empty_month_does_not_produce_a_zero_cost_snapshot(github_stub, tmp_path, monkeypatch):
    """§W5c — a real month the organisation predates: HTTP 200, the period correctly echoed,
    and no usage rows. A $0.00 snapshot would be read as a real zero bill, so none is written —
    and the inventory still is, because seats were legitimately read."""
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    github_stub.route_fixtures({
        "/user/orgs": "github_user_orgs",
        f"/organizations/{ORG}/settings/billing/usage/summary":
            "github_billing_usage_summary_empty",
        f"/organizations/{ORG}/settings/billing/usage": "github_billing_usage_detail_empty",
        f"/orgs/{ORG}/copilot/billing/seats": "github_copilot_seats",
    })

    exit_code = run_main(github_stub, tmp_path, period=GITHUB_EMPTY_PERIOD)

    assert exit_code == 1
    assert not (tmp_path / f"github_costs_{GITHUB_EMPTY_PERIOD}.json").exists()
    inventory = emitted(tmp_path, "inventory", GITHUB_EMPTY_PERIOD)
    assert len(inventory["resources"]) == len(seat_rows())


# ------------------------------------------------------------------------------ cost snapshot


def test_the_cost_snapshot_is_the_frozen_shape():
    costs = fetch_github.normalize_cost(summary_fixture(), ORG, PERIOD)
    assert set(costs) == FROZEN_COST_KEYS
    assert costs["provider"] == "github"
    assert costs["account"] == ORG
    assert costs["period"] == PERIOD
    assert costs["source_granularity"] == "service"
    assert all(set(line) == {
        "service", "resource_id", "region", "amount", "usage_qty", "usage_unit", "tags"
    } for line in costs["line_items"])


def test_amount_and_usage_qty_are_both_net_never_amount_net_against_quantity_gross():
    """§W3b. A reader dividing `amount` by `usage_qty` must get an effective unit price. The
    detail endpoint's `quantity` sums to grossQuantity, so pairing a net amount with a gross
    quantity would give a number that looks like a rate and is not one."""
    summary = summary_fixture()
    costs = fetch_github.normalize_cost(summary, ORG, PERIOD)
    by_sku = {line["service"]: line for line in costs["line_items"]}

    for row in summary["usageItems"]:
        line = by_sku[row["sku"]]
        assert line["amount"] == _normalized.money(row["netAmount"])
        assert line["usage_qty"] == row["netQuantity"]
        assert line["usage_unit"] == row["unitType"]

    # The seat row is the one where gross and net actually differ enough to matter.
    seat = by_sku[fetch_github.SEAT_SKU]
    row = seat_sku_row()
    assert seat["usage_qty"] == row["netQuantity"] != row["grossQuantity"] or (
        row["netQuantity"] == row["grossQuantity"]
    )
    assert round(seat["amount"] / seat["usage_qty"], 2) == round(row["pricePerUnit"], 2)


def test_a_quantity_is_not_rounded_to_two_decimals_the_way_an_amount_is():
    """C4's two-decimal rule is about money. ai-units and gigabyte-hours have no minor unit,
    and rounding the quantity would destroy the divisor that makes the unit price recoverable
    — `copilot_ai_unit` bills 1953.080525 units, which is not 1953.08 of anything."""
    costs = fetch_github.normalize_cost(summary_fixture(), ORG, PERIOD)
    ai = next(line for line in costs["line_items"] if line["service"] == "copilot_ai_unit")
    assert ai["usage_qty"] == 1953.080525
    assert ai["amount"] == 19.53


def test_the_total_is_summed_at_full_precision_and_rounded_once():
    """m6 D3 — rounding follows aggregation, never precedes it.

    **The recorded month cannot show this on its own**, and that is worth stating rather than
    discovering twice: its five rows round to 134.0 under either order, so a version of this
    test asserting only against the fixture passed cleanly under the very mutation it names.
    That is the t1 notes' hazard in its general form — an assertion shipped having never been
    executed against a failing state — and it was caught here by running exactly that mutation.
    So the ORDER is pinned on a constructed set where the two answers differ, and the fixture
    stays beside it as the live-value check it actually is.
    """
    summary = summary_fixture()
    costs = fetch_github.normalize_cost(summary, ORG, PERIOD)
    exact = sum(float(row["netAmount"]) for row in summary["usageItems"])
    assert costs["totals"]["amount"] == _normalized.money(exact) == 134.0
    # And it still agrees with the rounded line items, which is the property a reader checks.
    assert round(sum(line["amount"] for line in costs["line_items"]), 2) == 134.0

    # Three rows of four tenths of a cent. Rounded first they are 0.00 each and total 0.00;
    # summed first they are 0.012 and total 0.01. Only one of those is the money owed.
    fractional = {
        "usageItems": [
            {"sku": f"sku-{index}", "netAmount": 0.004, "netQuantity": 1.0, "unitType": "u"}
            for index in range(3)
        ]
    }
    rounded_first = fetch_github.normalize_cost(fractional, ORG, PERIOD)
    assert rounded_first["totals"]["amount"] == 0.01
    assert sum(line["amount"] for line in rounded_first["line_items"]) == 0.0


def test_gross_discount_and_unit_price_live_under_provider_extra():
    """§W3b — they are provider payload, and downstream must not key on them generically."""
    costs = fetch_github.normalize_cost(summary_fixture(), ORG, PERIOD)
    for line in costs["line_items"]:
        assert "grossAmount" not in line and "pricePerUnit" not in line
    rows = costs["provider_extra"]["usage_items"]
    assert {row["sku"] for row in rows} == {
        row["sku"] for row in summary_fixture()["usageItems"]
    }
    assert all(
        {"grossQuantity", "discountQuantity", "grossAmount", "discountAmount", "pricePerUnit"}
        <= set(row)
        for row in rows
    )


def test_the_two_endpoints_spell_the_same_thing_differently_and_not_as_a_case_transform():
    """§W3b's note, asserted rather than only written down: a human comparing this report
    against the detail endpoint or the console sees different strings for the same product."""
    summary_skus = {row["sku"] for row in summary_fixture()["usageItems"]}
    detail_skus = {row["sku"] for row in detail_fixture()["usageItems"]}
    assert summary_skus.isdisjoint(detail_skus)
    # Not a case transform either — `copilot_ai_unit` is `Copilot AI Credits` there.
    assert {s.lower().replace("_", " ") for s in summary_skus} != {
        s.lower() for s in detail_skus
    }
    assert "copilot_for_business" in summary_skus
    assert "Copilot Business" in detail_skus


def test_the_balance_block_is_present_and_null_rather_than_restating_the_period_total():
    """GitHub exposes no balance surface. §Normalized requires the block, so it is emitted with
    nulls — and never with the period total under `month_to_date_usage`, which would be a
    well-formed wrong answer for every period but the current one."""
    costs = fetch_github.normalize_cost(summary_fixture(), ORG, PERIOD)
    balance = costs["balance"]
    assert set(balance) == {
        "month_to_date_balance", "account_balance", "month_to_date_usage", "generated_at"
    }
    assert balance["month_to_date_balance"] is None
    assert balance["account_balance"] is None
    assert balance["month_to_date_usage"] is None
    assert balance["generated_at"]


def test_currency_is_declared_with_a_recorded_basis_not_captured_from_the_response():
    """m6 D1. The declaration is an adapter constant; what makes it more than a bare assertion
    is the basis beside it, in the form `fetch_linode.py` established."""
    costs = fetch_github.normalize_cost(summary_fixture(), ORG, PERIOD)
    assert costs["currency"] == "USD"
    basis = costs["provider_extra"]["currency_basis"]
    assert basis.startswith("adapter-asserted: ")
    assert fetch_github.API_VERSION in basis
    # And the claim the basis makes is true of the recorded bodies, both of them.
    assert fetch_github.currency_field_names(summary_fixture()) == []
    assert fetch_github.currency_field_names(detail_fixture()) == []


def test_a_currency_field_appearing_in_the_response_is_warned_about_not_captured():
    """The invalidation for the basis above. A recorded finding about a live API is a claim
    with no expiry, and this is the expiry: finding a currency field does not change the
    emitted value (D1) — it means `currency_basis` now says something false."""
    assert fetch_github.currency_field_names(
        {"usageItems": [{"netAmount": 1.0, "currencyCode": "EUR"}]}
    ) == ["currencyCode"]
    assert fetch_github.currency_field_names({"a": [{"b": {"currency": "USD"}}]}) == ["currency"]
    # Control: a body with no such key finds nothing, so the finder is not matching everything.
    assert fetch_github.currency_field_names({"usageItems": [{"netAmount": 1.0}]}) == []


# -------------------------------------------------------------------------------- reconcile


def test_the_reconcile_gate_passes_on_the_recorded_pair():
    """m6 D7's premise, checked against the two recorded bodies rather than restated: 255
    detail rows summing to within float-summation noise of the summary's own total."""
    summary_total = sum(
        float(row["netAmount"]) for row in summary_fixture()["usageItems"]
    )
    result = fetch_github.reconcile_detail(detail_fixture(), summary_total, PERIOD)
    assert result["status"] == "reconciled"
    assert result["detail_items"] == 255
    assert abs(result["difference"]) < 1e-9
    assert result["tolerance"] == fetch_github.RECONCILE_TOLERANCE == 0.01


def test_the_reconcile_gate_FIRES_on_a_divergent_detail_body():
    """Not a scout-time finding but a per-run gate: two months agreeing does not guarantee the
    third, and a new SKU or a mid-month credit is exactly how the third would differ."""
    summary_total = sum(float(r["netAmount"]) for r in summary_fixture()["usageItems"])
    detail = copy.deepcopy(detail_fixture())
    detail["usageItems"][0]["netAmount"] = detail["usageItems"][0]["netAmount"] + 0.02

    with pytest.raises(fetch_github.GitHubAPIError) as exc:
        fetch_github.reconcile_detail(detail, summary_total, PERIOD)
    message = str(exc.value)
    assert "reconcile FAILED" in message and "no snapshot is written" in message


def test_a_divergence_inside_the_tolerance_does_not_fire():
    """The other side of the same control. C4's absolute one-hundredth is used rather than
    invented, so a half-cent difference is inside it and a two-cent one is not."""
    summary_total = sum(float(r["netAmount"]) for r in summary_fixture()["usageItems"])
    detail = copy.deepcopy(detail_fixture())
    detail["usageItems"][0]["netAmount"] = detail["usageItems"][0]["netAmount"] + 0.005
    assert fetch_github.reconcile_detail(detail, summary_total, PERIOD)["status"] == "reconciled"


def test_a_reconcile_failure_writes_no_cost_snapshot_and_still_writes_the_inventory(
    github_stub, tmp_path, monkeypatch
):
    """The gate at the seam it actually guards. Raising rather than warning is the one place
    this adapter departs from the existing reconcile arm: Linode's declared total stays
    authoritative whatever its line items do, where here the agreement between the two
    endpoints IS the ground on which D7 chose the summary endpoint."""
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    divergent = copy.deepcopy(detail_fixture())
    divergent["usageItems"][0]["netAmount"] = 999.0

    github_stub.route_fixtures({
        "/user/orgs": "github_user_orgs",
        f"/organizations/{ORG}/settings/billing/usage/summary": "github_billing_usage_summary",
        f"/orgs/{ORG}/copilot/billing/seats": "github_copilot_seats",
    })
    github_stub.route(f"/organizations/{ORG}/settings/billing/usage", divergent)

    exit_code = run_main(github_stub, tmp_path)

    assert exit_code == 1
    assert not (tmp_path / f"github_costs_{PERIOD}.json").exists()
    assert (tmp_path / f"github_inventory_{PERIOD}.json").exists()


def test_the_reconcile_result_is_recorded_on_the_artifact_not_only_in_the_run_log(
    full_github_stub, tmp_path, monkeypatch
):
    """A reader holding only the JSON can tell a reconciled figure from an unreconciled one."""
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    assert run_main(full_github_stub, tmp_path) == 0
    reconcile = emitted(tmp_path, "costs")["provider_extra"]["reconcile"]
    assert reconcile["status"] == "reconciled"
    assert reconcile["source"] == "billing usage detail endpoint"
    assert reconcile["detail_items"] == 255


# -------------------------------------------------------------------------------- inventory


def test_the_inventory_envelope_and_resource_shapes_are_frozen(
    full_github_stub, tmp_path, monkeypatch
):
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    assert run_main(full_github_stub, tmp_path) == 0
    inventory = emitted(tmp_path, "inventory")

    assert set(inventory) == FROZEN_INVENTORY_KEYS
    assert inventory["provider"] == "github"
    assert inventory["resources"]
    for resource in inventory["resources"]:
        assert set(resource) == FROZEN_RESOURCE_FIELDS
        assert resource["type"] == _normalized.TYPE_SEAT
        assert resource["type"] in _normalized.CANONICAL_TYPES


def test_a_seat_is_keyed_on_the_assignees_immutable_id_not_its_mutable_login():
    """A login is a display name its owner can change; the numeric id cannot. Keying on the
    login would make a renamed user look like one resource that vanished and a different one
    that appeared, in a report whose month-on-month section is built on that comparison."""
    raw = seat_rows()[0]
    seat = fetch_github.normalize_seat(raw, ORG, 19.0)
    assert seat["resource_id"] == str(raw["assignee"]["id"])
    assert seat["resource_id"] != raw["assignee"]["login"]
    assert seat["name"] == raw["assignee"]["login"]
    assert seat["raw_ref"] == (
        f"github://orgs/{ORG}/copilot/billing/seats/{raw['assignee']['id']}"
    )


def test_a_seat_without_any_assignee_identity_is_dropped_rather_than_given_a_made_up_key():
    """An inventory entry with no identity cannot be reported, joined or acted on. Dropping it
    is right here and would not be for a cost line, where the money is the point."""
    assert fetch_github.normalize_seat({"assignee": {}}, ORG, 19.0) is None
    assert fetch_github.normalize_seat({}, ORG, 19.0) is None
    # A seat with only a login is still emittable — the login is stable enough to key on when
    # it is all there is, and losing the row entirely would be the worse error.
    seat = fetch_github.normalize_seat({"assignee": {"login": "user-9"}}, ORG, 19.0)
    assert seat["resource_id"] == "user-9"


def test_every_seat_populates_last_activity_at():
    """The first non-null `last_activity_at` any adapter has emitted — the field has existed
    and been null on all seventeen normalizers across the three predecessors since m1. t3's
    rule is the first in the catalog to key on an activity timestamp, and this is what makes
    that possible."""
    seats = [fetch_github.normalize_seat(raw, ORG, 19.0) for raw in seat_rows()]
    assert seats and all(seat["last_activity_at"] for seat in seats)


def test_a_seat_state_is_null_because_github_has_no_such_field():
    """m6 t2 §S1, ruled. The seat object carries no lifecycle field at all, so the concept is
    absent and §Normalized's answer for an absent concept is a null value.

    LOAD-BEARING — do not "improve" this into a derived value. Deriving
    active/pending_cancellation from `pending_cancellation_date` would be this adapter minting
    a state vocabulary locally, which is seam #1 with `state` in `type`'s place; §Normalized
    enumerates a new state in the schema first, and m6 t1 declined to add a canonical seat one.
    """
    raw = seat_rows()[0]
    assert "state" not in raw and "status" not in raw
    assert fetch_github.normalize_seat(raw, ORG, 19.0)["state"] is None

    # And it stays null even for a seat GitHub HAS flagged, which is the case a derived value
    # would have been invented for.
    pending = copy.deepcopy(raw)
    pending["pending_cancellation_date"] = "2026-09-01"
    assert fetch_github.normalize_seat(pending, ORG, 19.0)["state"] is None


def test_attached_to_is_a_prefixed_marker_and_never_null():
    """C7 — null is the universal idle signal keyed by four rules, and a seat assigned to
    somebody is emphatically not idle. The prefix follows the grammar `fetch_do.py` (`tag:`)
    and `fetch_linode.py` (`<entity type>:`) already use, and it is what stops C7's
    `attached_to`-against-`resource_id` join matching a person to a resource that happens to
    share the number."""
    seats = [fetch_github.normalize_seat(raw, ORG, 19.0) for raw in seat_rows()]
    assert all(seat["attached_to"] for seat in seats)
    assert all(seat["attached_to"].startswith("user:") for seat in seats)
    resource_ids = {seat["resource_id"] for seat in seats}
    assert not resource_ids & {seat["attached_to"] for seat in seats}


def test_timestamps_are_normalized_to_utc_z_rather_than_passed_through_with_an_offset():
    """GitHub states seat timestamps at the account's own offset (`+05:30` on the recorded
    organisation) where §Normalized's example is `Z`. t3's rule compares `last_activity_at`
    against a reference date, so it is normalized at the adapter."""
    raw = seat_rows()[0]
    assert raw["created_at"].endswith("+05:30"), "the fixture must still carry the offset"
    seat = fetch_github.normalize_seat(raw, ORG, 19.0)
    assert seat["created_at"].endswith("Z")
    assert seat["last_activity_at"].endswith("Z")
    assert _normalized.parse_timestamp(seat["created_at"]) == _normalized.parse_timestamp(
        raw["created_at"]
    )
    assert fetch_github.iso_utc(None) is None
    assert fetch_github.iso_utc("not-a-timestamp") is None


def test_region_is_null_and_size_is_the_carry_only_plan_label():
    """C13 — `size` is a free-form human label and nothing may sort, compare, sum, branch or
    join on it. GitHub seats have no region concept at all."""
    seat = fetch_github.normalize_seat(seat_rows()[0], ORG, 19.0)
    assert seat["region"] is None
    assert seat["size"] == seat_rows()[0]["plan_type"] == "business"
    assert seat["tags"] == []


def test_organization_members_are_not_emitted_as_resources(
    full_github_stub, tmp_path, monkeypatch
):
    """m6 D6 bounds the consumption class to entities carrying all three of an activity signal,
    a derivable per-instance cost and a stable identifier. A member seat carries the third and
    neither of the first two, so it is an exclusion with a stated reason, not an absence."""
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    assert run_main(full_github_stub, tmp_path) == 0

    inventory = emitted(tmp_path, "inventory")
    assert len(inventory["resources"]) == len(seat_rows())
    assert not any("/members" in r["path"] for r in full_github_stub.requests)

    excluded = {row["class"] for row in fetch_github.EXCLUSIONS}
    assert "organization_member" in excluded
    assert {"actions_artifact", "actions_cache", "package"} <= excluded


# ------------------------------------------------------------------------- C14 — cost model


def test_a_seat_costs_what_the_organisations_own_bill_says_it_costs():
    """C14 — each adapter guarantees its own cost model and asserts it in its own tests.

    GitHub's model is neither DO's (billed flat whatever its state) nor AWS's (a stopped
    instance bills no compute): a seat is an entitlement, it bills for as long as it is
    assigned, and its price is not derived from a rate table at all. It is read off the
    organisation's own bill — the `copilot_for_business` row — and divided by the seats that
    row is charged for. The figure is checked here against that billed line, not a constant.

    The obligation C14 leaves standing is met trivially and it is worth saying why: *only
    separately-inventoried storage is summed*, and this adapter inventories no storage of any
    kind, so nothing it emits can be double-counted against a folded-in cost.
    """
    summary = summary_fixture()
    seats = seat_rows()
    row = seat_sku_row()

    unit = fetch_github.seat_monthly_cost(summary, len(seats), [])
    assert unit == 19.0
    # The derived per-seat figure, times the seats it was divided across, IS the billed line.
    assert round(unit * len(seats), 2) == _normalized.money(row["netAmount"]) == 114.0
    assert row["unitType"] == fetch_github.SEAT_UNIT

    # And it reaches the artifact, rather than only the helper.
    seat = fetch_github.normalize_seat(seats[0], ORG, unit)
    assert seat["monthly_cost_estimate"] == 19.0


def test_an_absent_seat_sku_is_zero_plus_a_named_warning_never_a_borrowed_rate():
    """Never an invented figure. The plan tier is `business`, whose list price is public — and
    reaching for it here would be exactly the fabrication the milestone forbids."""
    warnings = []
    assert fetch_github.seat_monthly_cost({"usageItems": []}, 6, warnings) == 0.0
    assert len(warnings) == 1
    assert fetch_github.SEAT_SKU in warnings[0] and "unknown, not zero" in warnings[0]

    # Warned once per cause, not once per resource.
    fetch_github.seat_monthly_cost({"usageItems": []}, 6, warnings)
    assert len(warnings) == 1

    # A zero seat count and a price-less row are the other two ways it can be unknown.
    assert fetch_github.seat_monthly_cost(summary_fixture(), 0, warnings) == 0.0
    priceless = {"usageItems": [{"sku": fetch_github.SEAT_SKU, "pricePerUnit": None}]}
    assert fetch_github.seat_monthly_cost(priceless, 6, warnings) == 0.0
    assert len(warnings) == 3


def test_a_billing_failure_leaves_seats_priced_zero_and_says_so_rather_than_guessing(
    github_stub, tmp_path, monkeypatch
):
    """The seat price comes from the bill, so a run that could not read the bill does not know
    it. Reporting the plan's list price here would be a figure with no provider behind it."""
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    github_stub.route_fixtures({
        "/user/orgs": "github_user_orgs",
        f"/orgs/{ORG}/copilot/billing/seats": "github_copilot_seats",
    })
    github_stub.route(
        f"/organizations/{ORG}/settings/billing/usage/summary", {"message": "boom"}, status=500
    )

    exit_code = run_main(github_stub, tmp_path)
    inventory = emitted(tmp_path, "inventory")

    assert exit_code == 1
    assert all(r["monthly_cost_estimate"] == 0.0 for r in inventory["resources"])


def test_the_seat_estimate_multiplies_before_it_rounds():
    """m6 D4, pinned with a rate whose two-decimal rounding is LOSSY, so the two orders give
    genuinely different answers. Asserting only against the live 19.0 rate would pass under
    either order and prove nothing — at a sub-cent unit price, rounding first does not lose
    precision, it zeroes the estimate.
    """
    rate = 0.00033602  # a real GitHub unit price: the actions_storage gigabyte-hour rate
    summary = {"usageItems": [
        {"sku": fetch_github.SEAT_SKU, "pricePerUnit": rate, "netQuantity": 300_000.0}
    ]}

    assert fetch_github.seat_monthly_cost(summary, 2, []) == 50.4  # money(rate * 150_000)
    # What rounding the unit rate first would have produced — the counter-example D4 records.
    assert _normalized.money(_normalized.money(rate) * 150_000) == 0.0


# -------------------------------------------------------------------------------- discovery


def test_the_organisation_comes_from_the_flag_then_the_env_var_then_a_single_membership(
    github_stub
):
    client = fetch_github.GitHubClient(
        READONLY_TOKEN, api_base=github_stub.api_base, max_retries=0
    )
    assert fetch_github.resolve_org(client, "explicit-org", {}) == "explicit-org"
    assert fetch_github.resolve_org(client, None, {"CLOUDCOST_GITHUB_ORG": "from-env"}) == (
        "from-env"
    )

    github_stub.route("/user/orgs", load_fixture("github_user_orgs"))
    assert fetch_github.resolve_org(client, None, {}) == ORG


def test_discovery_refuses_to_choose_when_the_answer_is_ambiguous_or_absent(github_stub):
    """Picking the first of several would silently bill the wrong organisation on an account
    whose owner holds two, and nothing downstream could tell."""
    client = fetch_github.GitHubClient(
        READONLY_TOKEN, api_base=github_stub.api_base, max_retries=0
    )

    github_stub.route("/user/orgs", [])
    with pytest.raises(fetch_github.GitHubAPIError) as exc:
        fetch_github.resolve_org(client, None, {})
    assert "no organisation" in str(exc.value)

    github_stub.route("/user/orgs", [{"login": "one"}, {"login": "two"}])
    with pytest.raises(fetch_github.GitHubAPIError) as exc:
        fetch_github.resolve_org(client, None, {})
    assert "2 organisations" in str(exc.value)


# --------------------------------------------------------------------------------- the seam


def test_a_full_sweep_writes_both_artifacts_and_reports_them(
    full_github_stub, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    assert run_main(full_github_stub, tmp_path) == 0
    summary = json.loads(capsys.readouterr().out)

    assert summary["status"] == "ok"
    assert summary["period"] == PERIOD
    assert summary["organization"] == ORG
    assert summary["counts"] == {"line_items": 5, "resources": len(seat_rows())}
    assert summary["totals"] == {"amount": 134.0}
    assert summary["surveyed"] == {"copilot_seat": len(seat_rows())}
    assert summary["errors"] == [] and summary["not_inventoried"] == []
    assert set(summary["files"]) == {"costs", "inventory"}


def test_the_normalized_inventory_is_readable_by_the_shared_rule_engine(
    full_github_stub, tmp_path, monkeypatch
):
    """The whole bet, asserted at the seam: `detect_orphans.py` consumes a consumption-class
    adapter's output with no GitHub knowledge and no change of its own. This is the first
    provider from outside the IaaS class to be put through it, so `skipped == 0` is a stronger
    result here than it was for provider three — a `seat` is a shape the rule engine has never
    seen, and t1's widening of the canonical set is what makes it legible rather than illegible.
    """
    monkeypatch.setenv("CLOUDCOST_GITHUB_TOKEN", READONLY_TOKEN)
    run_main(full_github_stub, tmp_path)

    result = subprocess.run(
        [sys.executable, str(USE_CASE_ROOT / "scripts" / "detect_orphans.py"),
         str(tmp_path / f"github_inventory_{PERIOD}.json"), "--output-dir", str(tmp_path)],
        capture_output=True, text=True, cwd=USE_CASE_ROOT,
    )
    assert result.returncode == 0, result.stderr
    counts = json.loads(result.stdout)["counts"]
    assert counts["skipped"] == 0
    # t3 is the ticket that gives seats a rule. Until it lands, a legible seat yields no
    # candidate, and that is the correct result rather than a gap.
    assert counts["candidates"] == 0


# ---------------------------------------------------------------------------------- fixtures


#: `/user/orgs` answers with a bare JSON array, and the stub replays a fixture verbatim as the
#: response body — so this one cannot carry a `_comment` first key without changing the shape
#: the adapter parses. Exempted by name rather than by weakening the test to containment.
LIST_BODIED_FIXTURES = {"github_user_orgs.json"}


def test_every_github_fixture_documents_what_it_proves():
    """A fixture whose purpose is not written down is one the next reader must reverse-engineer
    from the assertions that happen to use it."""
    seen = set()
    for path in sorted(FIXTURES.glob("github_*.json")):
        seen.add(path.name)
        if path.name in LIST_BODIED_FIXTURES:
            assert json.loads(path.read_text()), f"{path.name} is empty"
            continue
        payload = json.loads(path.read_text())
        assert "_comment" in payload, f"{path.name} carries no _comment"
        assert next(iter(payload)) == "_comment", f"{path.name}'s _comment is not first"
        assert "Recorded" in payload["_comment"], f"{path.name} does not say it was recorded"
    assert LIST_BODIED_FIXTURES <= seen, "the exemption names a fixture that does not exist"


def test_no_committed_fixture_carries_a_credential_or_a_real_identity():
    """The recorder's pseudonymisation is a guarantee only if something checks it.

    **Node ids are DECODED and then checked, and that is the point of this test rather than a
    detail of it.** A GitHub node id is base64 of `04:User<id>`, so a real numeric id hides
    inside a value a text scan reads as opaque. This bit twice while the adapter was written:
    first the recorder rewrote the type prefix instead of the id and left the real one standing
    while the plain-text sweep reported clean; then this test decoded the node id, appended the
    plaintext, and checked it for everything EXCEPT a number — so a planted real id passed. The
    check is now the internal-consistency one: a node id must decode to a string carrying its
    own object's `id`, and no other number but the `04:` type prefix.
    """
    import base64

    for path in sorted(FIXTURES.glob("github_*.json")):
        text = path.read_text()
        payload = json.loads(text)

        assert not re.search(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,})\b", text
        ), f"token-shaped string in {path.name}"
        assert "@" not in text.replace("cloudcost@example.invalid", ""), f"email in {path.name}"

        for encoded, identifier in _node_id_pairs(payload):
            if encoded == "NODE-ID-REDACTED":
                continue
            decoded = base64.b64decode(encoded).decode()
            assert str(identifier) in decoded, (
                f"node_id in {path.name} decodes to {decoded!r}, which does not carry its own "
                f"id {identifier} — a real id is hiding inside a value a text scan reads as "
                f"opaque"
            )
            # `<type digits>:<Type><id>` — `04:User…` for a person, `012:Organization…` for
            # an org. The leading prefix is GitHub's type tag and carries no identity, so it
            # is partitioned off rather than allow-listed by value.
            _, _, rest = decoded.partition(":")
            others = set(re.findall(r"\d+", rest)) - {str(identifier)}
            assert not others, (
                f"unexpected number {sorted(others)} inside a decoded node_id in {path.name}"
            )

        for identifier in _numeric_ids_in(payload):
            assert re.fullmatch(r"100000\d\d", str(identifier)), (
                f"unpseudonymised numeric id {identifier} in {path.name}"
            )

        for login in _logins_in(payload):
            assert re.fullmatch(r"user-\d+|example-org", login), (
                f"unpseudonymised login {login!r} in {path.name}"
            )
        for repo in _repos_in(payload):
            assert repo == "" or re.fullmatch(r"repo-\d+", repo), (
                f"unpseudonymised repository {repo!r} in {path.name}"
            )
        for org in _orgs_in(payload):
            assert org == "example-org", f"unpseudonymised organisation {org!r} in {path.name}"


def _collect(node, keys, out):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in keys and isinstance(value, str):
                out.append(value)
            _collect(value, keys, out)
    elif isinstance(node, list):
        for value in node:
            _collect(value, keys, out)
    return out


def _logins_in(payload):
    return _collect(payload, {"login"}, [])


def _repos_in(payload):
    return _collect(payload, {"repositoryName"}, [])


def _orgs_in(payload):
    return _collect(payload, {"organization", "organizationName"}, [])


def _node_id_pairs(node, out=None):
    """Every `(node_id, id)` pair, so a node id can be checked against its own object's id."""
    out = [] if out is None else out
    if isinstance(node, dict):
        if isinstance(node.get("node_id"), str) and "id" in node:
            out.append((node["node_id"], node["id"]))
        for value in node.values():
            _node_id_pairs(value, out)
    elif isinstance(node, list):
        for value in node:
            _node_id_pairs(value, out)
    return out


def _numeric_ids_in(node, out=None):
    """Every `id` sitting beside a `login` — i.e. every account identifier, user or org."""
    out = [] if out is None else out
    if isinstance(node, dict):
        if isinstance(node.get("id"), int) and isinstance(node.get("login"), str):
            out.append(node["id"])
        for value in node.values():
            _numeric_ids_in(value, out)
    elif isinstance(node, list):
        for value in node:
            _numeric_ids_in(value, out)
    return out


def test_the_scrub_check_actually_fails_on_an_unpseudonymised_identity():
    """The check on the check. A guard that cannot fail is not a guard, and this one is written
    over committed files that are all already clean — so its failing state is constructed here
    rather than assumed."""
    assert _logins_in({"assignee": {"login": "a-real-person"}}) == ["a-real-person"]
    assert not re.fullmatch(r"user-\d+|example-org", "a-real-person")
    assert re.fullmatch(r"user-\d+|example-org", "user-3")
    assert _repos_in({"usageItems": [{"repositoryName": "secret-repo"}]}) == ["secret-repo"]
    assert not re.fullmatch(r"repo-\d+", "secret-repo")

    # The base64 arm, which is the one that has actually failed twice. A node id carrying a
    # real id decodes to a string that does not contain its object's own (pseudonymised) id.
    import base64

    planted = base64.b64encode(b"04:User77777777").decode()
    assert "77777777" not in planted, "the point: the real id is invisible in the encoded form"
    pairs = _node_id_pairs({"assignee": {"node_id": planted, "id": 10000001, "login": "user-1"}})
    assert pairs == [(planted, 10000001)]
    assert str(10000001) not in base64.b64decode(pairs[0][0]).decode()
    assert _numeric_ids_in({"assignee": {"id": 77777777, "login": "user-1"}}) == [77777777]
    assert not re.fullmatch(r"100000\d\d", "77777777")
