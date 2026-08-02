"""Offline tests for the orphan heuristics — pure, deterministic, no network, no LLM.

Every rule is asserted twice: once on a fixture that fires it, and once on the near-miss
fixture that must leave it silent. A rule that cannot fail to fire tests nothing.
"""

import ast
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

import detect_orphans
from conftest import FIXTURES, USE_CASE_ROOT, load_fixture

SCRIPT = USE_CASE_ROOT / "scripts" / "detect_orphans.py"
#: The normalized-schema helpers this module imports (extracted at t3, shared with it).
SHARED = USE_CASE_ROOT / "scripts" / "_normalized.py"

#: Every crafted fixture is written against this reference date.
REF = detect_orphans.parse_timestamp("2026-07-27T00:00:00Z")


def run(fixture, ref=REF, snapshot_age_days=30):
    return detect_orphans.detect(
        load_fixture(fixture), ref, snapshot_age_days=snapshot_age_days
    )


def by_id(result):
    return {c["resource_id"]: c for c in result["candidates"]}


def rules_fired(result):
    return {c["resource_id"]: c["rule"] for c in result["candidates"]}


def reported_ids(result):
    section = result["reported"]["untagged_in_tagged_account"]
    return [r["resource_id"] for r in section["resources"]]


def code_string_literals(path: Path) -> set:
    """Every string literal in a module's *code*, docstrings excluded.

    The provider-vocabulary guards below assert on what the engine can key on, which is the
    literals in its code — never its prose. A comment that records what m1 used to do here
    is documentation; the same word in a set literal is the seam coming back.
    """
    tree = ast.parse(path.read_text())
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", None) or []
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstrings.add(id(body[0].value))
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    }


# ------------------------------------------------------------- rule: unattached volume


def test_unattached_volume_fires_past_the_age_threshold():
    candidate = by_id(run("inventory_rules_positive"))["vol-orphan-1"]
    assert candidate["rule"] == "unattached_volume"
    assert candidate["confidence"] == 0.9
    assert candidate["monthly_saving_estimate"] == 10.0


def test_unattached_volume_is_silent_when_attached_young_or_exactly_at_the_threshold():
    fired = rules_fired(run("inventory_rules_negative"))
    # attached at all; unattached but 7d old; unattached for exactly 14d (rule is >14d)
    assert "vol-attached-1" not in fired
    assert "vol-young-orphan-1" not in fired
    assert "vol-orphan-exactly-14d-1" not in fired


# ------------------------------------------------------------ rule: unassociated static IP


def test_unassociated_static_ip_fires_regardless_of_age():
    candidate = by_id(run("inventory_rules_positive"))["203.0.113.10"]
    assert candidate["rule"] == "unassociated_static_ip"
    assert candidate["confidence"] == 0.95
    assert candidate["monthly_saving_estimate"] == 4.38
    # 7 days old and still a candidate — this rule carries no age threshold.
    assert any("no age threshold" in fact for fact in candidate["evidence"])


def test_assigned_reserved_ip_is_silent():
    assert "203.0.113.20" not in rules_fired(run("inventory_rules_negative"))


# ------------------------------------------------------------------- rule: aged snapshot


def test_aged_snapshot_fires_past_the_threshold():
    candidate = by_id(run("inventory_rules_positive"))["snap-aged-1"]
    assert candidate["rule"] == "aged_snapshot"
    assert candidate["confidence"] == 0.7
    assert candidate["monthly_saving_estimate"] == 1.2


def test_recent_snapshot_is_silent():
    assert "snap-recent-1" not in rules_fired(run("inventory_rules_negative"))


def test_snapshot_age_threshold_is_a_parameter():
    # snap-aged-1 is 148d old at REF.
    assert "snap-aged-1" in rules_fired(run("inventory_rules_positive", snapshot_age_days=30))
    assert "snap-aged-1" in rules_fired(run("inventory_rules_positive", snapshot_age_days=147))
    assert "snap-aged-1" not in rules_fired(
        run("inventory_rules_positive", snapshot_age_days=148)
    )
    assert "snap-aged-1" not in rules_fired(
        run("inventory_rules_positive", snapshot_age_days=200)
    )
    # And a 3d-old snapshot becomes a candidate once N drops below its age.
    assert "snap-recent-1" in rules_fired(
        run("inventory_rules_negative", snapshot_age_days=1)
    )


def test_default_snapshot_age_threshold_is_thirty_days():
    assert detect_orphans.DEFAULT_SNAPSHOT_AGE_DAYS == 30
    signature = detect_orphans.parse_args(["inventory.json"])
    assert signature.snapshot_age_days == 30


# ------------------------------------------------------------- rule: idle load balancer


def test_idle_load_balancer_fires_with_zero_backends():
    candidate = by_id(run("inventory_rules_positive"))["lb-idle-1"]
    assert candidate["rule"] == "idle_load_balancer"
    assert candidate["confidence"] == 0.85
    assert candidate["monthly_saving_estimate"] == 12.0


def test_tag_targeted_load_balancer_is_not_idle():
    """B2: a tag-targeted LB carries `attached_to == 'tag:<name>'` and has backends."""
    result = run("inventory_rules_negative")
    lb = next(r for r in load_fixture("inventory_rules_negative")["resources"]
              if r["resource_id"] == "lb-tagged-1")
    assert lb["attached_to"] == "tag:web"
    assert "lb-tagged-1" not in rules_fired(result)


def test_droplet_targeted_load_balancer_is_silent():
    assert "lb-attached-1" not in rules_fired(run("inventory_rules_negative"))


# ------------------------------------------- rule: stopped compute with attached storage


def test_stopped_compute_with_attached_storage_fires():
    candidate = by_id(run("inventory_rules_positive"))["drop-stopped-1"]
    assert candidate["rule"] == "stopped_compute_with_attached_storage"
    assert candidate["confidence"] == 0.6


def test_stopped_compute_saving_is_the_instance_estimate_plus_its_attached_storage():
    """m2 t2 c: m1 named the attached storage but did not sum it — an under-report. The
    saving *adds* attached storage to the instance's own estimate; it never replaces it,
    because a provider that bills a stopped instance (DO) and one that does not (AWS) are
    both correct only if the own term survives."""
    candidate = by_id(run("inventory_rules_positive"))["drop-stopped-1"]
    # DO droplet's own estimate 24.00 (billed on-or-off) + its attached volume 5.00.
    assert candidate["monthly_saving_estimate"] == 29.0
    assert (
        "saving estimate is the instance's own $24.00/mo plus its attached storage "
        "$5.00/mo = $29.00/mo" in candidate["evidence"]
    )


def test_stopped_compute_evidence_names_the_state_the_age_and_the_attached_volume():
    evidence = by_id(run("inventory_rules_positive"))["drop-stopped-1"]["evidence"]
    assert "state is 'stopped' — the instance is stopped" in evidence
    assert (
        "stopped instance age 193d (created 2026-01-15, ref 2026-07-27); threshold >30d"
        in evidence
    )
    assert "attached storage vol-on-stopped-1 (old-worker-data, 50GiB) — $5.00/mo" in evidence


def test_stopped_compute_is_silent_without_storage_when_young_or_when_running():
    fired = rules_fired(run("inventory_rules_negative"))
    assert "drop-off-young-1" not in fired  # stopped + storage, but only 5d old
    assert "drop-off-nostorage-1" not in fired  # stopped + old, but no attached volume
    assert "drop-active-1" not in fired  # old + storage, but running


# ---------------------------------------------- rule: stopped database with its storage


def test_stopped_database_with_storage_fires_and_the_saving_is_its_own_estimate():
    """The storage of a database is not separately inventoried — the adapter prices it into
    the instance's own estimate — so the saving is that estimate and nothing is summed onto
    it. Summing an attached volume here would double-count (m2 t2 c)."""
    candidate = by_id(run("inventory_rds_positive"))["db-stopped-1"]
    assert candidate["rule"] == "stopped_database_with_storage"
    assert candidate["confidence"] == 0.6
    assert candidate["monthly_saving_estimate"] == 23.0
    assert "state is 'stopped' — the database is stopped" in candidate["evidence"]
    assert "attached_to is null — the database is serving nothing" in candidate["evidence"]
    assert any("still bills" in fact for fact in candidate["evidence"])


def test_stopped_database_is_silent_when_running_young_or_paying_nothing():
    fired = rules_fired(run("inventory_rds_negative"))
    assert "db-running-1" not in fired  # stopped-state absent: it is serving
    assert "db-stopped-young-1" not in fired  # stopped + storage, but 5d old
    assert "db-stopped-nostorage-1" not in fired  # stopped + old, but $0 — nothing to save


def test_the_state_vocabulary_is_schema_level_not_any_providers_spelling():
    """m2 t2 a: the constant m1 called "the one seam" now reads a value the schema defines.
    DO's `off` is mapped in its adapter; nothing here knows the word."""
    assert detect_orphans.STOPPED_STATES == {"stopped"}
    assert detect_orphans.STOPPED_STATES == {detect_orphans.STATE_STOPPED}

    # No provider's own state spelling appears in the shared machinery's *code*. Read from
    # the AST rather than the raw text so the prose may still say what m1 did here — a
    # comment recording the history is not a value the engine can key on.
    literals = code_string_literals(SCRIPT) | code_string_literals(SHARED)
    assert "off" not in literals

    # And `state` is read only inside the two rules that need it.
    rule_sources = inspect.getsource(
        detect_orphans.rule_stopped_compute_with_attached_storage
    ) + inspect.getsource(detect_orphans.rule_stopped_database_with_storage)
    state_reads = [
        line
        for line in SCRIPT.read_text().splitlines()
        if 'get("state")' in line or "get('state')" in line
    ]
    assert len(state_reads) == 4  # two guards, two evidence lines that quote the state
    assert all(line in rule_sources for line in state_reads)
    assert 'resource.get("state") not in STOPPED_STATES' in rule_sources


# ------------------------------------------ the aged-snapshot rule covers both snapshot types


def test_one_aged_snapshot_rule_covers_both_canonical_snapshot_types():
    """m2 t2 c: an RDS manual snapshot and an EBS snapshot are the same heuristic — age
    plus a source that is gone — so one rule covers both, keyed on the canonical `type`
    set. The candidate's own `type` is what distinguishes them downstream."""
    candidates = by_id(run("inventory_rds_positive"))

    database_snapshot = candidates["snap-db-manual-orphan"]
    ebs_snapshot = candidates["snap-ebs-aged-1"]
    assert database_snapshot["rule"] == ebs_snapshot["rule"] == "aged_snapshot"
    assert database_snapshot["confidence"] == ebs_snapshot["confidence"] == 0.7
    assert database_snapshot["type"] == "database_snapshot"
    assert ebs_snapshot["type"] == "snapshot"
    assert database_snapshot["monthly_saving_estimate"] == 4.75

    # Same evidence sentences for both — the rule does not branch on the type.
    assert (
        "snapshot age 563d (created 2025-01-09, ref 2026-07-27); threshold >30d"
        in database_snapshot["evidence"]
    )
    assert (
        "attached_to is null — the source the snapshot was taken from is gone"
        in database_snapshot["evidence"]
    )
    assert (
        "attached_to is null — the source the snapshot was taken from is gone"
        in ebs_snapshot["evidence"]
    )


def test_the_aged_rule_shares_one_threshold_across_both_snapshot_types():
    """One `--snapshot-age-days` governs both; the threshold is never forked per type."""
    assert detect_orphans.SNAPSHOT_TYPES == {"snapshot", "database_snapshot"}
    fired = rules_fired(run("inventory_rds_positive", snapshot_age_days=600))
    assert "snap-db-manual-orphan" not in fired  # 563d old — under the raised threshold
    assert "snap-ebs-aged-1" not in fired  # 148d old — likewise
    # ...and both come back when the shared threshold drops below their ages.
    assert {"snap-db-manual-orphan", "snap-ebs-aged-1"} <= set(
        rules_fired(run("inventory_rds_positive", snapshot_age_days=100))
    )
    assert "snap-db-manual-recent" not in rules_fired(run("inventory_rds_negative"))


# -------------------------------------------------------------- the negative fixture as a whole


def test_the_near_miss_fixture_produces_no_candidates_at_all():
    result = run("inventory_rules_negative")
    assert result["candidates"] == []
    assert result["totals"]["monthly_saving_estimate"] == 0.0


def test_the_rds_near_miss_fixture_produces_no_candidates_at_all():
    result = run("inventory_rds_negative")
    assert result["candidates"] == []
    assert result["totals"]["monthly_saving_estimate"] == 0.0


def test_every_rule_in_the_catalog_fires_on_the_positive_fixture():
    result = run("inventory_rules_positive")
    assert set(c["rule"] for c in result["candidates"]) == {
        "unattached_volume",
        "unassociated_static_ip",
        "aged_snapshot",
        "idle_load_balancer",
        "stopped_compute_with_attached_storage",
    }
    # Six rules in the catalog, five fired: this DO-shaped fixture carries no database.
    # The sixth fires on the RDS fixture — together the two cover the whole catalog.
    assert len(result["candidates"]) == 5
    assert len(detect_orphans.RULES) == 6
    rds = set(c["rule"] for c in run("inventory_rds_positive")["candidates"])
    assert rds == {"stopped_database_with_storage", "aged_snapshot"}
    assert set(c["rule"] for c in result["candidates"]) | rds == {
        rule.__name__.removeprefix("rule_") for rule in detect_orphans.RULES
    }
    # 4.38 + 10.00 + 12.00 + 1.20 + (24.00 own + 5.00 attached) = 56.58
    assert result["totals"]["monthly_saving_estimate"] == 56.58


def test_candidates_are_ordered_by_descending_confidence():
    result = run("inventory_rules_positive")
    assert [c["resource_id"] for c in result["candidates"]] == [
        "203.0.113.10",
        "vol-orphan-1",
        "lb-idle-1",
        "snap-aged-1",
        "drop-stopped-1",
    ]


# ------------------------------------------------------------------------- modifier: keep


def test_keep_true_tag_excludes_the_resource_outright():
    result = run("inventory_modifiers")
    # vol-keep-1 is an unattached volume 207d old — it would otherwise be a 0.9 candidate.
    assert "vol-keep-1" not in by_id(result)
    excluded = {e["resource_id"]: e for e in result["excluded"]}
    assert excluded["vol-keep-1"]["reason"] == "carries the 'keep=true' tag"


def test_a_resource_without_the_keep_tag_is_not_excluded():
    result = run("inventory_modifiers")
    assert [e["resource_id"] for e in result["excluded"]] == ["vol-keep-1"]
    assert by_id(result)["vol-plain-1"]["confidence"] == 0.9


# -------------------------------------------------------------- modifier: recent activity


def test_recent_activity_modifier_is_a_no_op_when_last_activity_at_is_null():
    """Decision A: DO emits null for every resource, so the modifier is inert there — and
    must not silently substitute `created_at`, which is 207d old on this fixture."""
    candidate = by_id(run("inventory_modifiers"))["vol-do-null-activity-1"]
    assert candidate["modifiers"] == []
    assert candidate["confidence"] == candidate["base_confidence"] == 0.9


def test_recent_activity_modifier_fires_when_last_activity_at_is_set():
    candidate = by_id(run("inventory_modifiers"))["vol-recent-activity-1"]
    assert candidate["modifiers"] == [{"modifier": "recent_activity", "delta": -0.2}]
    assert candidate["confidence"] == 0.7
    assert (
        "last_activity_at 2026-07-25 is 2d from ref 2026-07-27, inside the 14d window: -0.2"
        in candidate["evidence"]
    )


def test_last_activity_at_outside_the_window_does_not_fire_the_modifier():
    candidate = by_id(run("inventory_modifiers"))["vol-stale-activity-1"]
    assert candidate["modifiers"] == []
    assert candidate["confidence"] == 0.9


# -------------------------------------------------------------- modifier: ephemeral name


@pytest.mark.parametrize(
    "resource_id,prefix", [("vol-tmp-1", "tmp-"), ("vol-test-1", "test-")]
)
def test_ephemeral_name_modifier_adds_confidence(resource_id, prefix):
    candidate = by_id(run("inventory_modifiers"))[resource_id]
    assert candidate["modifiers"] == [{"modifier": "ephemeral_name", "delta": 0.1}]
    assert candidate["confidence"] == 1.0
    assert any(f"'{prefix}'" in fact for fact in candidate["evidence"])


def test_a_non_ephemeral_name_gets_no_modifier():
    candidate = by_id(run("inventory_modifiers"))["vol-plain-1"]
    assert candidate["name"] == "detached-data-vol"
    assert candidate["modifiers"] == []


def test_both_modifiers_apply_additively():
    candidate = by_id(run("inventory_modifiers"))["vol-ci-recent-1"]
    assert [m["modifier"] for m in candidate["modifiers"]] == [
        "recent_activity",
        "ephemeral_name",
    ]
    assert candidate["base_confidence"] == 0.9
    assert candidate["confidence"] == 0.8  # 0.9 - 0.2 + 0.1


def test_confidence_is_clamped_to_the_unit_interval():
    candidate = by_id(run("inventory_modifiers"))["203.0.113.30"]
    raw = candidate["base_confidence"] + sum(m["delta"] for m in candidate["modifiers"])
    assert round(raw, 2) == 1.05  # 0.95 + 0.10
    assert candidate["confidence"] == 1.0
    assert detect_orphans.clamp(1.7) == 1.0
    assert detect_orphans.clamp(-0.3) == 0.0


# ----------------------------------------------------- reported-only: untagged resources


def test_untagged_resource_in_a_tagged_account_is_reported_not_queued():
    result = run("inventory_tagged_account")
    section = result["reported"]["untagged_in_tagged_account"]
    assert section["account_uses_tags"] is True
    assert section["tag_coverage"] == pytest.approx(5 / 7, abs=1e-4)
    assert reported_ids(result) == ["drop-legacy-1", "vol-untagged-orphan-1"]
    # drop-legacy-1 fires no rule at all: it is a governance flag and nothing else.
    assert "drop-legacy-1" not in by_id(result)


def test_a_reported_resource_may_still_be_a_candidate_by_a_different_rule():
    result = run("inventory_tagged_account")
    candidate = by_id(result)["vol-untagged-orphan-1"]
    # It is queued because it is an unattached volume — never because it is untagged.
    assert candidate["rule"] == "unattached_volume"
    assert "untagged_in_tagged_account" not in rules_fired(result).values()


def test_reported_entries_carry_no_confidence_and_no_saving_estimate():
    """Structural: a reported-only rule cannot be mistaken for an actionable candidate."""
    section = run("inventory_tagged_account")["reported"]["untagged_in_tagged_account"]
    for entry in section["resources"]:
        assert "confidence" not in entry
        assert "monthly_saving_estimate" not in entry
        assert entry["rule"] == "untagged_in_tagged_account"
        assert "monthly_cost_estimate" in entry


def test_untagged_reported_evidence_names_the_coverage_and_threshold():
    section = run("inventory_tagged_account")["reported"]["untagged_in_tagged_account"]
    evidence = section["resources"][0]["evidence"]
    assert "tags is empty" in evidence
    assert (
        "account tag coverage is 71% of 7 resources, above the 50% threshold — "
        "the account is using tags" in evidence
    )


def test_an_account_below_the_coverage_threshold_reports_nothing():
    result = run("inventory_untagged_account")
    section = result["reported"]["untagged_in_tagged_account"]
    assert section["account_uses_tags"] is False
    assert section["tag_coverage"] == 0.25
    assert section["resources"] == []
    # ...while the rule catalog still does its job on the same inventory.
    assert rules_fired(result) == {"vol-orphan-2": "unattached_volume"}


# ------------------------------------------------------------- reference-date determinism


def test_age_rules_are_evaluated_against_the_reference_date_not_the_wall_clock():
    early = detect_orphans.parse_timestamp("2026-05-10T00:00:00Z")
    fired = rules_fired(run("inventory_rules_positive", ref=early))
    # vol-orphan-1 is 9d old on 2026-05-10 and 87d old on 2026-07-27.
    assert "vol-orphan-1" not in fired
    assert "vol-orphan-1" in rules_fired(run("inventory_rules_positive"))


def test_the_payload_carries_no_wall_clock_field():
    result = run("inventory_rules_positive")
    assert "generated_at" not in result
    assert result["reference_date"] == "2026-07-27T00:00:00Z"
    assert result["inventory_generated_at"] == "2026-07-27T00:00:00Z"


def test_the_same_inputs_produce_a_byte_identical_payload():
    first = json.dumps(run("inventory_rules_positive"), indent=2, sort_keys=True)
    second = json.dumps(run("inventory_rules_positive"), indent=2, sort_keys=True)
    assert first == second


def test_the_reference_date_defaults_to_the_inventory_generated_at():
    inventory = load_fixture("inventory_rules_positive")
    resolved = detect_orphans.resolve_reference_date(None, inventory)
    assert detect_orphans.iso(resolved) == "2026-07-27T00:00:00Z"


def test_an_explicit_reference_date_overrides_the_inventory_timestamp():
    inventory = load_fixture("inventory_rules_positive")
    resolved = detect_orphans.resolve_reference_date("2026-05-10", inventory)
    assert detect_orphans.iso(resolved) == "2026-05-10T00:00:00Z"


def test_an_unparseable_reference_date_is_rejected():
    with pytest.raises(ValueError):
        detect_orphans.resolve_reference_date("last tuesday", {})


# ------------------------------------------------------------------------------ evidence


def test_evidence_quotes_the_facts_that_fired_with_dates_and_thresholds():
    evidence = by_id(run("inventory_rules_positive"))["vol-orphan-1"]["evidence"]
    assert evidence == [
        "attached_to is null — the volume is not attached to any instance",
        "unattached for 87d (created 2026-05-01, ref 2026-07-27); threshold >14d",
    ]


def test_snapshot_evidence_reports_the_age_and_the_missing_source():
    evidence = by_id(run("inventory_rules_positive"))["snap-aged-1"]["evidence"]
    assert "snapshot age 148d (created 2026-03-01, ref 2026-07-27); threshold >30d" in evidence
    assert (
        "attached_to is null — the source the snapshot was taken from is gone" in evidence
    )


def test_candidates_carry_the_identity_fields_the_report_renders():
    candidate = by_id(run("inventory_rules_positive"))["vol-orphan-1"]
    assert candidate["name"] == "detached-data-vol"
    assert candidate["region"] == "blr1"
    assert candidate["raw_ref"] == "do://volumes/vol-orphan-1"
    assert candidate["type"] == "volume"


# ----------------------------------------------------------------------------- degrading


def test_malformed_entries_are_skipped_and_warned_about_never_fatal():
    result = run("inventory_malformed")
    assert [s["index"] for s in result["skipped"]] == [0, 1, 2, 3]
    assert result["warnings"] == [
        {
            "resource_id": "vol-bad-date-1",
            "warning": "unparseable created_at: 'yesterday' — age rules cannot evaluate "
            "this resource",
        }
    ]
    # The unparseable date suppresses its own resource, not the sweep.
    assert rules_fired(result) == {"vol-ok-orphan-1": "unattached_volume"}


def test_an_empty_inventory_is_not_an_error():
    result = detect_orphans.detect({"resources": []}, REF)
    assert result["candidates"] == []
    assert result["reported"]["untagged_in_tagged_account"]["account_uses_tags"] is False
    assert result["totals"] == {
        "resources": 0,
        "candidates": 0,
        "monthly_saving_estimate": 0.0,
        "reported": 0,
    }


# ----------------------------------------------------------------------------------- CLI


def cli(args, tmp_path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=USE_CASE_ROOT,
        capture_output=True,
        text=True,
    )


def test_cli_writes_the_candidates_file_and_prints_a_summary(tmp_path):
    result = cli(
        [
            str(FIXTURES / "inventory_rules_positive.json"),
            "--output-dir",
            str(tmp_path),
            "--reference-date",
            "2026-07-27",
        ],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["counts"] == {
        "resources": 6,
        "candidates": 5,
        "reported": 0,
        "excluded": 0,
        "skipped": 0,
    }

    written = Path(summary["file"])
    # m2 t2 b: provider-prefixed, so a second provider's run into the same output
    # directory cannot overwrite the first's candidates.
    assert written == tmp_path / "digitalocean_orphan_candidates_2026-07.json"
    payload = json.loads(written.read_text())
    assert payload == run("inventory_rules_positive")


def test_cli_defaults_the_reference_date_to_the_inventory_timestamp(tmp_path):
    result = cli(
        [str(FIXTURES / "inventory_rules_positive.json"), "--output-dir", str(tmp_path)],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["reference_date"] == "2026-07-27T00:00:00Z"


def test_cli_reports_a_partial_status_on_a_degraded_inventory(tmp_path):
    result = cli(
        [str(FIXTURES / "inventory_malformed.json"), "--output-dir", str(tmp_path)],
        tmp_path,
    )
    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["status"] == "partial"
    assert summary["counts"]["skipped"] == 4
    assert len(summary["warnings"]) == 1
    # Degraded, not aborted: the file it could produce is still written.
    assert (tmp_path / "digitalocean_orphan_candidates_2026-07.json").exists()


def test_cli_snapshot_age_flag_changes_the_verdict(tmp_path):
    args = [str(FIXTURES / "inventory_rules_positive.json"), "--output-dir", str(tmp_path)]
    assert cli(args + ["--snapshot-age-days", "200"], tmp_path).returncode == 0
    payload = json.loads(
        (tmp_path / "digitalocean_orphan_candidates_2026-07.json").read_text()
    )
    assert "snap-aged-1" not in [c["resource_id"] for c in payload["candidates"]]
    assert payload["parameters"]["snapshot_age_days"] == 200


def test_cli_missing_inventory_exits_with_an_error_envelope(tmp_path):
    result = cli([str(tmp_path / "nope.json"), "--output-dir", str(tmp_path)], tmp_path)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"
    assert "cannot read inventory" in result.stderr


def test_cli_rejects_an_unparseable_reference_date(tmp_path):
    result = cli(
        [
            str(FIXTURES / "inventory_rules_positive.json"),
            "--output-dir",
            str(tmp_path),
            "--reference-date",
            "last tuesday",
        ],
        tmp_path,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"


# -------------------------------------------------------- cross-stage: t1 adapter → t2
#
# The unit tests above run on crafted inventories. This one runs the real t1 adapter
# against the recorded DO fixtures and feeds *its* emitted file to the t2 CLI, so a
# rename or shape drift across the stage seam fails here rather than in the live pipeline.


def test_the_adapter_output_feeds_detection_without_translation(
    full_stub, tmp_path, monkeypatch
):
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

    inventory_file = tmp_path / "do_inventory_2026-07.json"
    assert inventory_file.exists()

    result = cli(
        [str(inventory_file), "--output-dir", str(tmp_path), "--reference-date", "2026-07-27"],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(
        (tmp_path / "digitalocean_orphan_candidates_2026-07.json").read_text()
    )
    fired = {c["resource_id"]: c["rule"] for c in payload["candidates"]}

    assert fired == {
        "vol-orphan-1": "unattached_volume",
        "203.0.113.11": "unassociated_static_ip",
        "snap-0001": "aged_snapshot",
        "snap-0002": "aged_snapshot",
        "lb-orphan-1": "idle_load_balancer",
    }
    # The tag-targeted LB survives the seam: t1 emits `tag:web`, t2 does not call it idle.
    assert "lb-tagged-1" not in fired
    assert payload["provider"] == "digitalocean"
    assert payload["skipped"] == [] and payload["warnings"] == []


def test_the_aws_adapter_output_feeds_detection_without_translation(
    full_aws_stub, tmp_path, monkeypatch
):
    """The m2 seam, end to end: t1's AWS adapter → t2's rules, no translation between them.

    This is the test the whole ticket exists for. Before t2, every rule keyed on DO's
    vocabulary, so this same run produced *zero* candidates from an inventory full of them
    — a green pipeline reporting nothing. Now the AWS-shaped orphans fire on the identical
    catalog the DO run uses, with no provider knowledge anywhere in it.
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

    inventory_file = tmp_path / "aws_inventory_2026-07.json"
    assert inventory_file.exists()

    result = cli(
        [str(inventory_file), "--output-dir", str(tmp_path), "--reference-date", "2026-07-27"],
        tmp_path,
    )
    assert result.returncode == 0, result.stderr

    # (b) the provider prefix, on the provider that motivated it.
    payload = json.loads((tmp_path / "aws_orphan_candidates_2026-07.json").read_text())
    assert payload["provider"] == "aws"
    fired = {c["resource_id"]: c["rule"] for c in payload["candidates"]}
    candidates = {c["resource_id"]: c for c in payload["candidates"]}

    # Stopped EC2 + its EBS volume; stopped RDS; the aged manual RDS snapshot whose source
    # DB is gone; the unassociated Elastic IP (the done-when shape on the live account).
    assert fired["i-0aaa3333"] == "stopped_compute_with_attached_storage"
    assert fired["db-stopped-1"] == "stopped_database_with_storage"
    assert fired["snap-db-manual-orphan"] == "aged_snapshot"
    assert any(rule == "unassociated_static_ip" for rule in fired.values())

    # The saving is provider-correct without the rule knowing the provider: AWS bills no
    # compute on a stopped instance (own 0.00), so the whole saving is the attached EBS.
    stopped_ec2 = candidates["i-0aaa3333"]
    assert stopped_ec2["monthly_saving_estimate"] == 16.0
    assert (
        "saving estimate is the instance's own $0.00/mo plus its attached storage "
        "$16.00/mo = $16.00/mo" in stopped_ec2["evidence"]
    )
    # RDS storage is priced into the instance's own estimate — counted once, not summed.
    assert candidates["db-stopped-1"]["monthly_saving_estimate"] == 23.0

    assert payload["skipped"] == [] and payload["warnings"] == []


# --------------------------------------------------------------- provider-agnostic shape


def test_the_rules_never_read_a_provider_specific_field():
    """Every field the catalog keys on is a first-class normalized-schema field.

    Reads `_normalized.py` alongside the rule module: the shared helpers moved there at t3
    and the guard follows the code it watches, so the refactor cannot shrink its reach.
    """
    source = SCRIPT.read_text() + SHARED.read_text()
    normalized_fields = {
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
        # inventory envelope
        "provider",
        "account",
        "period",
        "generated_at",
        "resources",
    }
    read_fields = set(
        line.split('resource.get("')[1].split('"')[0]
        for line in source.splitlines()
        if 'resource.get("' in line
    )
    assert read_fields <= normalized_fields, read_fields - normalized_fields
    assert "provider_extra" not in source


def test_the_rules_key_only_on_canonical_type_values():
    """m2 t2 a′: `type` values are schema-level too. m1 keyed two rules on DO's own
    `droplet`/`reserved_ip` — the second seam — so the guard now watches the values, not
    just the field names."""
    import _normalized

    literals = code_string_literals(SCRIPT) | code_string_literals(SHARED)
    assert "droplet" not in literals
    assert "reserved_ip" not in literals

    # Every canonical type is defined once, in the shared module, and imported here.
    assert _normalized.CANONICAL_TYPES == {
        "compute_instance",
        "volume",
        "static_ip",
        "snapshot",
        "load_balancer",
        "database",
        "database_snapshot",
    }
    for name in ("TYPE_COMPUTE_INSTANCE", "TYPE_STATIC_IP", "TYPE_DATABASE"):
        assert getattr(detect_orphans, name) is getattr(_normalized, name)
    assert detect_orphans.SNAPSHOT_TYPES <= _normalized.CANONICAL_TYPES


def test_compose_and_render_key_on_no_type_value():
    """§t2 (d), as an assertion rather than a claim: the downstream stages read the `type`
    field but must never special-case one of its *values* — that would be a third leak of
    provider-shaped knowledge into shared machinery, and its own finding."""
    downstream = {
        "compose_report_data.py": USE_CASE_ROOT / "scripts" / "compose_report_data.py",
        "render_report.py": USE_CASE_ROOT / "scripts" / "render_report.py",
    }
    import _normalized

    for name, path in downstream.items():
        literals = code_string_literals(path)
        leaked = literals & (_normalized.CANONICAL_TYPES | {"droplet", "reserved_ip"})
        assert leaked == set(), f"{name} keys on type value(s): {leaked}"

    template = (USE_CASE_ROOT / "templates" / "report.html.j2").read_text()
    for value in _normalized.CANONICAL_TYPES | {"droplet", "reserved_ip"}:
        assert f"'{value}'" not in template and f'"{value}"' not in template


def test_detection_runs_on_a_non_do_inventory_unchanged():
    """The same catalog on a differently-provided inventory: no adapter knowledge needed."""
    inventory = {
        "provider": "someothercloud",
        "account": "acct-1",
        "period": "2026-07",
        "resources": [
            {
                "resource_id": "disk-1",
                "type": "volume",
                "name": "tmp-orphan-disk",
                "region": "eu-1",
                "size": "40GiB",
                "state": "available",
                "created_at": "2026-01-01T00:00:00Z",
                "last_activity_at": None,
                "attached_to": None,
                "monthly_cost_estimate": 4.0,
                "tags": [],
                "raw_ref": "soc://disks/disk-1",
            }
        ],
        "generated_at": "2026-07-27T00:00:00Z",
    }
    result = detect_orphans.detect(inventory, REF)
    assert result["provider"] == "someothercloud"
    assert result["candidates"][0]["rule"] == "unattached_volume"
    assert result["candidates"][0]["confidence"] == 1.0  # 0.9 + ephemeral 0.1
