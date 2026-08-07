"""Offline tests for the report renderer — no network, no LLM, no clock.

Every payload rendered here is produced by the **real t3 merge** over the t1/t2 fixtures the
earlier stages are tested against, rather than by a hand-written report-data stand-in: a
crafted payload would prove only that the template reads what this file's author wrote, and
the shape the renderer has to survive is the one `compose_report_data.py` actually emits.

The load-bearing test in the file is `test_a_mutated_figure_reaches_the_html` and its
siblings: they change a figure in the payload and assert the HTML follows, which is what
"render-only" means operationally — a renderer that recomputed anything would print the
recomputed value and fail.
"""

import json
import re
import shutil
import subprocess
import sys
from html import unescape
from pathlib import Path

import compose_report_data
import detect_orphans
import pytest
import render_report
from conftest import FIXTURES, USE_CASE_ROOT, load_fixture

SCRIPT = USE_CASE_ROOT / "scripts" / "render_report.py"
TEMPLATE = USE_CASE_ROOT / "templates" / "report.html.j2"

#: The reference date every crafted fixture is written against (t2's convention).
REF = detect_orphans.parse_timestamp("2026-07-27T00:00:00Z")

#: Section anchors the report is contracted to carry. The renderer names these in its own
#: stdout summary, so a section silently disappearing fails here and there.
SECTION_IDS = (
    "report-header",
    "cost-summary",
    "month-on-month",
    "tag-coverage",
    "orphan-candidates",
    "data-notes",
)


# ---------------------------------------------------------------------------- payloads


def do_bundle():
    return {
        "cost": load_fixture("cost_do_2026-07"),
        "inventory": load_fixture("inventory_rules_positive"),
        "orphans": detect_orphans.detect(load_fixture("inventory_rules_positive"), REF),
    }


def soc_bundle(currency=None):
    cost = load_fixture("cost_soc_2026-07")
    if currency is not None:
        cost["currency"] = currency
    return {
        "cost": cost,
        "inventory": load_fixture("inventory_soc_2026-07"),
        "orphans": load_fixture("orphans_soc_2026-07"),
    }


def compose(bundles, prior=None):
    return compose_report_data.compose(bundles, prior_snapshots=prior, period="2026-07")


@pytest.fixture(scope="module")
def report():
    """N=1, with a prior month on disk — the ordinary monthly report."""
    return compose([do_bundle()], prior=[load_fixture("cost_do_2026-06")])


@pytest.fixture(scope="module")
def first_run_report():
    """N=1, nothing persisted yet — the §t4 done-check payload."""
    return compose([do_bundle()])


@pytest.fixture(scope="module")
def two_provider_report():
    """N=2 where only DO has a prior month: the +74.21 / +46.97 % the t3 review carried,
    of which DO's real growth is +14.21 and someothercloud's first appearance is $60."""
    return compose([do_bundle(), soc_bundle()], prior=[load_fixture("cost_do_2026-06")])


@pytest.fixture(scope="module")
def multi_currency_report():
    return compose([do_bundle(), soc_bundle(currency="EUR")], prior=[load_fixture("cost_do_2026-06")])


# ----------------------------------------------------------------------------- helpers


def render(data):
    html, render_warnings = render_report.render_html(data, source_file="report_data.json")
    assert render_warnings == [], f"unexpected rendering notes: {render_warnings}"
    return html


def section(page, section_id):
    """The markup of one top-level block. They are siblings, never nested."""
    match = re.search(
        rf'<(section|header) id="{section_id}">(.*?)</\1>', page, re.S
    )
    assert match, f"section {section_id} is missing from the report"
    return match.group(2)


def text_of(page):
    """The rendered *text*: tags stripped and entities resolved — so an assertion reads
    what a person reads, and an evidence line carrying `>` or `<` is compared against the
    string t2 emitted rather than against its escaped form."""
    stripped = re.sub(r"<style.*?</style>", " ", page, flags=re.S)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    return re.sub(r"\s+", " ", unescape(stripped))


def candidates(data):
    return [c for band in data["orphans"]["by_band"] for c in band["candidates"]]


def cli(args, cwd=USE_CASE_ROOT, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True, env=env
    )


def write_payload(tmp_path, data, name="report_data_2026-07.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ------------------------------------------------------------------- sections present


def test_every_section_is_present(report):
    html = render(report)
    for section_id in SECTION_IDS:
        assert f'<section id="{section_id}">' in html or f'<header id="{section_id}">' in html

    body = text_of(html)
    for heading in (
        "Cost summary",
        "Month on month",
        "Tag coverage",
        "Orphan candidates",
        "Data notes",
    ):
        assert heading in body


def test_the_header_reads_its_stamps_from_the_payload(report):
    html = render(report)
    header = text_of(section(html, "report-header"))
    assert report["period"] in header
    # The "as of" line is t3's derived stamp, not a clock reading.
    assert report["as_of"] in header
    for provider in report["providers"]:
        assert provider in header
    for entry in report["accounts"]:
        assert entry["account"] in header


def test_cost_summary_renders_the_grand_total_and_every_service_line(report):
    body = text_of(section(render(report), "cost-summary"))
    assert "172.21" in body
    assert report["cost_summary"]["currency"] in body
    for row in report["cost_summary"]["by_service"]:
        assert row["service"] in body
        assert f"{row['amount']:,.2f}" in body
    # The reconciliation flag and the D4 note are payload content, carried verbatim.
    assert report["cost_summary"]["granularity_note"] in body


def test_tag_coverage_renders_the_ratio_the_spenders_and_the_estimate_note(report):
    coverage = report["tag_coverage"]
    body = text_of(section(render(report), "tag-coverage"))
    assert "16.67 %" in body and str(coverage["coverage"]) in body
    assert f"top {coverage['top_k']}" in body
    for row in coverage["top_untagged_spenders"]:
        assert row["name"] in body
        assert row["raw_ref"] in body
        assert f"{row['monthly_cost_estimate']:,.2f}" in body
    # Verbatim — "estimate, not billed cost" has to survive into the report.
    assert coverage["estimate_note"] in body


# --------------------------------------------------------------------- orphan section


def test_the_orphan_section_shows_every_candidate_with_its_evidence_and_saving(report):
    body = text_of(section(render(report), "orphan-candidates"))
    payload_candidates = candidates(report)
    assert len(payload_candidates) == 5

    for candidate in payload_candidates:
        assert candidate["name"] in body
        assert candidate["resource_id"] in body
        assert candidate["raw_ref"] in body
        assert candidate["rule"] in body
        assert f"{candidate['monthly_saving_estimate']:,.2f}" in body
        assert candidate["evidence"], "a candidate reached the report with no evidence"
        for line in candidate["evidence"]:
            assert line in body, f"evidence line missing from the report: {line}"


def test_the_orphan_section_prints_the_band_cutoffs_and_subtotals(report):
    body = text_of(section(render(report), "orphan-candidates"))
    for band in report["orphans"]["bands"]:
        assert band["rule"] in body, f"band cutoff not printed: {band['rule']}"
    for band in report["orphans"]["by_band"]:
        assert band["band"] in body
        assert f"{band['monthly_saving_estimate']:,.2f}" in body
    assert f"{report['orphans']['totals']['monthly_saving_estimate']:,.2f}" in body


def test_the_orphan_section_shows_what_date_the_age_rules_ran_against(report):
    body = text_of(section(render(report), "orphan-candidates"))
    for row in report["orphans"]["evaluated_as_of"]:
        assert row["reference_date"] in body
        assert row["inventory_generated_at"] in body


# ---------------------------------------------------------------- month-on-month paths


def test_first_run_renders_no_prior_month_cleanly(first_run_report):
    """The §t4 done-check: the no-MoM payload renders as a sentence, not as a blank, a
    zero, an em dash or an error."""
    assert first_run_report["mom_delta"]["status"] == "no_prior_month"
    body = text_of(section(render(first_run_report), "month-on-month"))

    assert "No prior month (first run)" in body
    assert first_run_report["mom_delta"]["prior_period"] in body
    assert first_run_report["mom_delta"]["reason"] in body
    # No delta was computed, so none is shown — and nothing leaks a Python repr.
    assert "None" not in body and "Undefined" not in body
    assert "%" not in body
    # The rest of the report is unaffected by the absent section.
    full = render(first_run_report)
    assert "172.21" in text_of(section(full, "cost-summary"))
    assert candidates(first_run_report)[0]["name"] in text_of(section(full, "orphan-candidates"))


def test_two_providers_render_with_the_new_provider_caveat_adjacent_to_the_delta(
    two_provider_report,
):
    delta = two_provider_report["mom_delta"]
    assert delta["providers_without_prior_snapshot"] == ["someothercloud"]
    assert (delta["delta_amount"], delta["delta_pct"]) == (74.21, 46.97)

    html = render(two_provider_report)
    mom = section(html, "month-on-month")
    body = text_of(mom)

    # Both providers are in the report, and both sides of the headline are present.
    assert "digitalocean" in body and "someothercloud" in body
    assert "+74.21" in body and "+46.97 %" in body

    # Adjacent, not merely present: the caveat sits between the headline figure and the
    # first table of the section — i.e. inside the headline block, beside the number a
    # reader would otherwise take for organic growth.
    figure_at = mom.index("+74.21")
    caveat_at = mom.index("Not all of this change is organic growth")
    first_table_at = mom.index("<table")
    assert figure_at < caveat_at < first_table_at
    assert "someothercloud" in body[body.index("Not all of this change") :][:400]

    # And the per-provider rows separate real growth from a first appearance.
    assert "+14.21" in body and "+60.00" in body
    assert "no prior snapshot" in body


def test_a_provider_that_vanished_is_called_out_too(report):
    """The mirror case — present last month, absent this month — is payload data as well
    (`providers_only_in_prior`), and gets the same treatment."""
    data = compose([do_bundle()], prior=[load_fixture("cost_do_2026-06"), load_fixture("cost_soc_2026-07")])
    assert data["mom_delta"]["providers_only_in_prior"] == ["someothercloud"]
    body = text_of(section(render(data), "month-on-month"))
    assert "A provider present last month is absent this month" in body
    assert "someothercloud" in body


# ------------------------------------------------------------------- multi-currency


def test_multi_currency_renders_per_currency_and_fabricates_no_grand_total(
    multi_currency_report,
):
    summary = multi_currency_report["cost_summary"]
    assert summary["grand_total"] is None and summary["currency"] is None
    assert summary["totals_by_currency"] == {"EUR": 60.0, "USD": 172.21}

    body = text_of(section(render(multi_currency_report), "cost-summary"))
    assert "No combined total" in body
    for code, total in summary["totals_by_currency"].items():
        assert code in body and f"{total:,.2f}" in body
    # The cross-currency sum the payload refuses to make is nowhere in the cost summary.
    assert "232.21" not in body


def test_a_cross_currency_month_on_month_figure_carries_its_own_caveat(multi_currency_report):
    """`month_on_month` sums across providers whatever their currency, so `current_total`
    is a cross-currency scalar (232.21 = 172.21 USD + 60.00 EUR) even in the report whose
    `grand_total` was withheld for exactly that reason — and `mom_delta.currency` is null,
    so the headline would otherwise print a bare number with no unit. That is a t3 gap
    (forwarded in the notes); until it closes, the template does what it does for the
    new-provider case: prints the caveat beside the figure rather than letting an honest
    payload read as a misleading report."""
    assert multi_currency_report["mom_delta"]["currency"] is None
    assert multi_currency_report["mom_delta"]["current_total"] == 232.21

    mom = section(render(multi_currency_report), "month-on-month")
    body = text_of(mom)
    assert "This change spans more than one currency" in body
    assert "EUR" in body and "USD" in body
    assert mom.index("232.21") < mom.index("This change spans more than one currency")
    assert mom.index("This change spans more than one currency") < mom.index("<table")


def test_multi_currency_labels_each_providers_figures_with_its_own_currency(
    multi_currency_report,
):
    orphans = text_of(section(render(multi_currency_report), "orphan-candidates"))
    assert "40.00 EUR / month" in orphans  # someothercloud's candidate
    assert "10.00 USD / month" in orphans  # DO's
    # A band subtotal spans providers, so it carries no currency code rather than a wrong one.
    assert "54.38 / month estimated" in orphans


# --------------------------------------------------------------- data-quality notes


def test_warnings_and_skipped_entries_are_rendered(two_provider_report):
    assert two_provider_report["warnings"], "fixture no longer carries a warning to render"
    body = text_of(section(render(two_provider_report), "data-notes"))
    for entry in two_provider_report["warnings"]:
        assert entry["warning"] in body


def test_a_skipped_input_is_visible_rather_than_hidden(report):
    data = json.loads(json.dumps(report))
    data["skipped"] = [
        {"source": "orphans", "path": "output/orphan_candidates_2026-07.json", "reason": "no such file"}
    ]
    body = text_of(section(render(data), "data-notes"))
    assert "no such file" in body
    assert "output/orphan_candidates_2026-07.json" in body
    assert "Skipped inputs (1)" in body


# ------------------------------------------------------- region coverage (m2 t3, A4)
#
# The field is *additive*: it renders when a provider swept regions and is invisible
# otherwise. The two invariants that matter are that it reaches the page when present, and
# that it costs a payload without it exactly nothing — the second is what keeps every m1
# DigitalOcean report byte-for-byte what it was.


@pytest.fixture(scope="module")
def swept_report():
    """A payload carrying A4's field, composed by the real merge like every other here."""
    bundle = soc_bundle()
    bundle["cost"] = {
        **bundle["cost"],
        "provider_extra": {"swept_regions": ["ap-south-1", "eu-west-1", "us-east-1"]},
    }
    return compose([bundle])


def test_the_swept_region_set_is_stated_in_the_report(swept_report):
    header = text_of(section(render(swept_report), "report-header"))
    entry = swept_report["region_coverage"][0]
    assert f"{entry['provider']} regions swept ({entry['count']})" in header
    for region in entry["swept"]:
        assert region in header


def test_a_mutated_region_figure_reaches_the_html(swept_report):
    """The render-only guard for the new field. A template computing the count with
    `| length` would print 3 here and fail — the payload's figure is the one on the page."""
    mutated = json.loads(json.dumps(swept_report))
    mutated["region_coverage"][0]["count"] = 999
    mutated["region_coverage"][0]["swept"][0] = "xx-mutant-1"
    header = text_of(section(render(mutated), "report-header"))
    assert "regions swept (999)" in header
    assert "xx-mutant-1" in header


def test_a_provider_that_swept_nothing_renders_as_nothing_not_as_absent(swept_report):
    mutated = json.loads(json.dumps(swept_report))
    mutated["region_coverage"][0] = {"provider": "someothercloud", "swept": [], "count": 0}
    header = text_of(section(render(mutated), "report-header"))
    assert "regions swept (0)" in header and "the sweep enumerated no region" in header


def test_a_payload_without_region_coverage_is_not_a_degraded_render(tmp_path, report):
    """The load-bearing one: adding `region_coverage` to SECTIONS instead of OPTIONAL_FIELDS
    turns this red. A missing *section* costs a rendering note and a `partial` exit — and
    DigitalOcean, which has no regions to sweep, would then fail every run it ever makes."""
    data = json.loads(json.dumps(report))
    del data["region_coverage"]
    result = cli([str(write_payload(tmp_path, data)), "--output-dir", str(tmp_path)])
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["render_warnings"] == []
    # The stdout list is unchanged: A4 added a field inside the header, not a new section.
    assert summary["sections"] == [
        "header",
        "cost-summary",
        "month-on-month",
        "tag-coverage",
        "orphan-candidates",
        "data-notes",
    ]


def test_the_report_is_byte_identical_whether_the_field_is_empty_or_absent(report):
    """A non-sweeping provider's report must not move by one byte. `report` is a DO payload,
    so compose already gives it `region_coverage: []`; deleting the key must render the same
    page — the state every m1 report_data on disk is in."""
    absent = json.loads(json.dumps(report))
    del absent["region_coverage"]
    assert report["region_coverage"] == []
    assert render(report) == render(absent)
    assert "regions swept" not in render(report)


def test_the_region_block_names_no_provider_and_no_provider_payload_key():
    """Rendered *generically*: the renderer and the template know a named report_data field,
    not AWS, not the provider-payload block, not the key inside it that compose lifted.

    Scoped to the whole of both files rather than to the region block, so it also holds the
    t4 optimization section to the same rule — that section exists for one provider today,
    which is exactly the condition under which a provider name tends to get hardcoded.
    """
    for source in (SCRIPT.read_text(), TEMPLATE.read_text()):
        assert "provider_extra" not in source
        assert "swept_regions" not in source
        assert not re.search(r"\baws\b", source, re.I)
        assert not re.search(r"\bdigitalocean\b", source, re.I)


def test_two_providers_each_state_their_own_sweep():
    one = soc_bundle()
    one["cost"] = {**one["cost"], "provider_extra": {"swept_regions": ["us-east-1"]}}
    html = render(compose([do_bundle(), one]))
    header = text_of(section(html, "report-header"))
    assert "someothercloud regions swept (1)" in header
    assert "digitalocean regions swept" not in header


# ------------------------------------------------------- render-only guard (failable)


def test_a_mutated_figure_reaches_the_html(report):
    """The renderer reads the payload rather than recomputing it.

    Each mutation below is arithmetically impossible — the grand total no longer matches
    its own service lines, the coverage ratio no longer matches its counts, the band
    subtotal no longer matches its candidates. A renderer that re-totalled, re-derived or
    re-banded anything would print the consistent value and fail here.
    """
    data = json.loads(json.dumps(report))
    data["cost_summary"]["grand_total"] = 999999.99
    data["tag_coverage"]["coverage"] = 0.4242
    data["orphans"]["by_band"][0]["monthly_saving_estimate"] = 777.77
    data["orphans"]["by_band"][0]["candidates"][0]["monthly_saving_estimate"] = 123.45
    data["mom_delta"]["delta_amount"] = -12345.67
    data["mom_delta"]["delta_pct"] = -99.99

    body = text_of(render(data))
    assert "999,999.99" in body
    assert "42.42 %" in body
    assert "777.77" in body
    assert "123.45" in body
    assert "-12,345.67" in body
    assert "-99.99 %" in body


def test_an_absent_figure_renders_as_absent_not_as_zero(report):
    """A null figure must not become 0.00 — a report that prints a zero where it has
    nothing is asserting rather than reporting."""
    data = json.loads(json.dumps(report))
    data["orphans"]["by_band"][0]["candidates"][0]["monthly_saving_estimate"] = None
    data["tag_coverage"]["coverage"] = None
    page = render(data)
    assert "— USD / month" in text_of(page)
    # The headline coverage figure reads as absent; the per-provider row that still has a
    # figure still shows it — a null is not contagious.
    coverage = section(page, "tag-coverage")
    assert re.search(r'<div class="figure">\s*—', coverage)
    assert "16.67 % (0.1667)" in text_of(coverage)
    assert render_report.format_amount(None) == "—"
    assert render_report.format_amount(0) == "0.00"
    assert render_report.format_signed_pct(None) == "—"


def imports_module(source: str, name: str) -> bool:
    """Whether `source` imports `name` — used as an absence guard below, so it is checked
    against a positive control first: a guard that can only ever pass proves nothing."""
    return re.search(rf"^\s*(import {name}\b|from {name} import)", source, re.M) is not None


def test_the_renderer_imports_no_stage_script_and_reads_no_clock():
    source = SCRIPT.read_text(encoding="utf-8")

    # Positive controls — synthetic, and a real sibling that genuinely does both.
    assert imports_module("import detect_orphans\n", "detect_orphans")
    assert imports_module("from _normalized import money\n", "_normalized")
    sibling = (USE_CASE_ROOT / "scripts" / "detect_orphans.py").read_text(encoding="utf-8")
    assert imports_module(sibling, "_normalized")
    assert imports_module(sibling, "datetime") and "datetime.now(" in sibling

    # The guard itself.
    for module in ("detect_orphans", "compose_report_data", "_normalized"):
        assert not imports_module(source, module), (
            f"render_report imports {module}: there is now a code path through which a "
            f"stage's arithmetic could be re-run inside the renderer"
        )
    for module in ("datetime", "time"):
        assert not imports_module(source, module), f"render_report imports {module}"
    assert "datetime.now(" not in source and "utcnow(" not in source


def test_the_report_is_byte_identical_across_renders(report):
    assert render(report) == render(report)


# ------------------------------------------------------------------------ autoescape


def test_provider_supplied_strings_are_escaped_not_injected(report):
    """Resource names, tags and evidence come from a provider's API. They are data."""
    payload = '<script>alert("xss")</script>'
    data = json.loads(json.dumps(report))
    data["orphans"]["by_band"][0]["candidates"][0]["name"] = f"vol-{payload}"
    data["orphans"]["by_band"][0]["candidates"][0]["evidence"][0] = f"evidence {payload}"
    data["tag_coverage"]["top_untagged_spenders"][0]["name"] = f"lb-{payload}"
    data["accounts"][0]["account"] = f"acct-{payload}"
    data["warnings"] = [{"warning": f"warning {payload}"}]

    html = render(data)
    assert "<script>" not in html
    assert html.count("&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;") == 5


def test_the_report_is_self_contained(report):
    """No stylesheet, script, font or image is fetched: the file opens from disk anywhere."""
    html = render(report)
    assert "<style>" in html
    assert not re.search(r'(src|href)\s*=\s*"(https?:)?//', html)
    assert "<link" not in html and "<img" not in html
    assert not re.search(r"<script[\s>]", html)


# ------------------------------------------------------------------------------- CLI


def test_the_cli_writes_the_report_and_prints_its_path(tmp_path, report):
    payload = write_payload(tmp_path, report)
    result = cli([str(payload), "--output-dir", str(tmp_path / "out")])
    assert result.returncode == 0, result.stderr

    summary = json.loads(result.stdout)
    written = Path(summary["file"])
    assert written == tmp_path / "out" / "cloudcost_report_2026-07.html"
    assert written.is_file()
    assert summary["status"] == "ok"
    assert summary["render_warnings"] == []
    assert summary["mom_status"] == "ok"
    assert summary["counts"]["orphan_candidates"] == 5
    assert summary["pdf"] is None
    assert "Orphan candidates" in text_of(written.read_text(encoding="utf-8"))


def test_the_cli_honours_an_explicit_output_path(tmp_path, first_run_report):
    payload = write_payload(tmp_path, first_run_report)
    target = tmp_path / "nested" / "custom.html"
    result = cli([str(payload), "--output", str(target)])
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["file"] == str(target)
    assert "No prior month (first run)" in text_of(target.read_text(encoding="utf-8"))


def test_an_unreadable_or_malformed_payload_is_an_error_envelope(tmp_path):
    missing = cli([str(tmp_path / "nope.json"), "--output-dir", str(tmp_path)])
    assert missing.returncode == 1
    assert json.loads(missing.stdout)["status"] == "error"

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    result = cli([str(broken), "--output-dir", str(tmp_path)])
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "error"
    assert not list(tmp_path.glob("cloudcost_report_*.html"))

    not_an_object = tmp_path / "list.json"
    not_an_object.write_text("[]", encoding="utf-8")
    assert cli([str(not_an_object), "--output-dir", str(tmp_path)]).returncode == 1


def test_a_payload_missing_a_section_degrades_to_a_partial_run(tmp_path, report):
    """Degrade, don't crash (repo rule): the report is still written, the gap is named in
    it, and the stage reports `partial`/exit 1 rather than a well-formed silent one."""
    data = json.loads(json.dumps(report))
    del data["orphans"]
    payload = write_payload(tmp_path, data)

    result = cli([str(payload), "--output-dir", str(tmp_path / "out")])
    assert result.returncode == 1
    summary = json.loads(result.stdout)
    assert summary["status"] == "partial"
    assert any("orphans" in note for note in summary["render_warnings"])

    body = text_of(Path(summary["file"]).read_text(encoding="utf-8"))
    assert "Rendering notes (1)" in body
    assert "no usable 'orphans' section" in body
    # The sections that *do* have data are unaffected.
    assert "172.21" in body


def test_the_cli_is_deterministic(tmp_path, report):
    payload = write_payload(tmp_path, report)
    first = tmp_path / "a.html"
    second = tmp_path / "b.html"
    assert cli([str(payload), "--output", str(first)]).returncode == 0
    assert cli([str(payload), "--output", str(second)]).returncode == 0
    assert first.read_bytes() == second.read_bytes()


def test_the_template_resolves_from_any_working_directory(tmp_path, report):
    """The template is anchored to the use-case root, not the cwd — the orchestrator
    invokes this script from wherever the harness put it."""
    payload = write_payload(tmp_path, report)
    result = cli([str(payload), "--output-dir", str(tmp_path / "out")], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["template"] == str(TEMPLATE)


# --------------------------------------------------------- optional PDF companion


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("wkhtmltopdf") is None, reason="wkhtmltopdf not installed")
def test_the_optional_pdf_companion_is_written(tmp_path, report):
    payload = write_payload(tmp_path, report)
    result = cli([str(payload), "--output-dir", str(tmp_path / "out"), "--pdf"])
    assert result.returncode == 0, result.stderr

    summary = json.loads(result.stdout)
    pdf = Path(summary["pdf"])
    assert pdf.is_file() and pdf.stat().st_size > 1000
    assert pdf.read_bytes().startswith(b"%PDF")
    # The HTML — the deliverable — is written either way.
    assert Path(summary["file"]).is_file()


def test_write_pdf_returns_a_note_when_the_binary_is_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(render_report.shutil, "which", lambda _: None)
    html_path = tmp_path / "report.html"
    html_path.write_text("<html></html>", encoding="utf-8")

    path, note = render_report.write_pdf(html_path)
    assert path is None
    assert "wkhtmltopdf" in note and "the HTML report was written" in note


def test_a_missing_pdf_binary_does_not_fail_the_run(tmp_path, report):
    """The claim is about the *run*, so it is asserted at the run level — the unit test
    above checks the return tuple and could not have caught the stage exiting 1 with it.

    `--pdf` is asked for and the binary is unreachable (an empty PATH, which is what
    `shutil.which` consults). The HTML is the deliverable and it was written before the PDF
    step ran, so the stage stays `ok` / exit 0 and says on stdout what it did not produce.
    """
    payload = write_payload(tmp_path, report)
    env = {"PATH": "", "HOME": str(tmp_path)}
    result = cli(
        [str(payload), "--output-dir", str(tmp_path / "out"), "--pdf"], env=env
    )
    assert result.returncode == 0, result.stderr

    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["pdf"] is None
    assert "wkhtmltopdf" in summary["pdf_note"]
    assert summary["render_warnings"] == []
    assert Path(summary["file"]).is_file()


def test_the_fixture_payloads_are_what_t3_actually_emits(report, first_run_report):
    """Guard on the premise of every test above: these payloads came out of the real merge,
    so a t3 shape change lands here rather than in the live pipeline."""
    assert set(report) >= {"period", "as_of", "providers", "cost_summary", "mom_delta",
                           "tag_coverage", "orphans", "warnings", "skipped"}
    assert report["as_of"] == load_fixture("cost_do_2026-07")["generated_at"]
    assert first_run_report["mom_delta"]["status"] == "no_prior_month"
    assert (FIXTURES / "cost_do_2026-06.json").is_file()


# ==================== optimization signals — the isolation invariant (m2 t4)
#
# §t4's ONE hard gate. The exploratory section is a second, separately sanctioned additive
# change to shared render machinery (A4 was the first), and the whole basis for sanctioning it
# is that a report without the optimization file cannot tell the difference. So the absent case
# is asserted at the byte level, not by inspection, and the mutation that would break it — a
# section rendered unconditionally — is what these tests exist to catch.


def optimization_payload():
    """The shape `detect_optimization_signals.py` emits, with both halves of the caveat."""
    return {
        "provider": "someothercloud",
        "account": "000000000000",
        "period": "2026-07",
        "signals": [
            {
                "service": "objectstore",
                "resource_id": "cc-logs",
                "region": "somewhere-1",
                "signal": "s3_no_lifecycle_policy",
                "evidence": [
                    "no lifecycle configuration (NoSuchLifecycleConfiguration)",
                    "StandardStorage 100.0 GB (CloudWatch BucketSizeBytes)",
                ],
                "monthly_cost_estimate": 2.3,
                "rate_basis": {
                    "rate": 0.023,
                    "unit": "USD/GB-month",
                    "source": "list price, Standard storage, pre-discount",
                    "as_of": "2026-08-02",
                },
                "note": "No lifecycle policy, so nothing expires on a schedule.",
            },
            {
                "service": "registry",
                "resource_id": "cc-worker",
                "region": "somewhere-1",
                "signal": "ecr_untagged_image_accumulation",
                "evidence": ["3 untagged image(s), 1.122 GB total"],
                "note": "Untagged does not mean unreferenced.",
            },
        ],
        "denied": [
            {"call": "secretsmanager:ListSecrets", "region": "somewhere-1", "code": "AccessDenied"}
        ],
        "warnings": ["cc-other: no NumberOfObjects datapoint published, so emptiness is unknown"],
        "totals": {"signals": 2, "by_signal": {"s3_no_lifecycle_policy": 1}},
    }


def test_the_report_is_byte_identical_when_the_optimization_file_is_absent(report):
    """The invariant itself, at the byte level.

    `source_file` is held constant across the three renders — it is part of the render
    context, and a measurement that let it vary would report a spurious difference (the trap
    that caught t3's first attempt at exactly this measurement).
    """
    core = render_report.render_html(report, source_file="report_data.json")[0]
    none_passed = render_report.render_html(
        report, source_file="report_data.json", optimization=None
    )[0]
    empty_passed = render_report.render_html(
        report, source_file="report_data.json", optimization={}
    )[0]

    assert core == none_passed
    assert core == empty_passed
    assert "Optimization signals" not in core
    assert 'id="optimization-signals"' not in core

    # Failable: the same payload WITH the file renders a different page. Without this the
    # three-way equality above would hold just as well for a section that never renders.
    with_signals = render_report.render_html(
        report, source_file="report_data.json", optimization=optimization_payload()
    )[0]
    assert with_signals != core


def test_an_absent_optimization_file_is_not_a_degraded_render(tmp_path, report):
    """The CLI half, mirroring A4's load-bearing absent-case test.

    Putting the section in SECTIONS instead of keeping it out of both tuples turns this red:
    a missing SECTIONS member costs a rendering note and a `partial` exit, which would make
    every run that has no optimization file — every DigitalOcean run, forever — exit 1.
    """
    result = cli([str(write_payload(tmp_path, report)), "--output-dir", str(tmp_path)])

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["render_warnings"] == []
    # Unchanged, and the state key is absent entirely: a core run's envelope is what it was.
    assert summary["sections"] == [
        "header",
        "cost-summary",
        "month-on-month",
        "tag-coverage",
        "orphan-candidates",
        "data-notes",
    ]
    assert "optimization" not in summary


def test_a_named_optimization_file_that_cannot_be_read_still_renders_the_core_report(
    tmp_path, report
):
    """Isolation holds unconditionally — but the failure is reported, not swallowed.

    A file the operator explicitly named and that did not load must not leave the run looking
    like one that was never asked for; otherwise "the section is missing" is indistinguishable
    from "there was nothing to show".
    """
    payload_path = write_payload(tmp_path, report)
    broken = tmp_path / "not-json.json"
    broken.write_text("{ this is not json", encoding="utf-8")

    plain = cli([str(payload_path), "--output", str(tmp_path / "plain.html")])
    named = cli(
        [
            str(payload_path),
            "--output", str(tmp_path / "named.html"),
            "--optimization-file", str(broken),
        ]
    )

    assert plain.returncode == 0 and named.returncode == 0, named.stderr
    assert (tmp_path / "plain.html").read_text() == (tmp_path / "named.html").read_text()

    summary = json.loads(named.stdout)
    assert summary["status"] == "ok"
    assert summary["render_warnings"] == []
    assert summary["optimization"]["state"].startswith("unreadable")
    assert "optimization-signals" not in summary["sections"]

    # A path that does not exist at all takes the same route.
    missing = cli(
        [
            str(payload_path),
            "--output", str(tmp_path / "missing.html"),
            "--optimization-file", str(tmp_path / "nope.json"),
        ]
    )
    assert missing.returncode == 0
    assert (tmp_path / "missing.html").read_text() == (tmp_path / "plain.html").read_text()


def test_the_exploratory_section_renders_its_evidence_when_the_file_is_present(report):
    html = render_report.render_html(
        report, source_file="report_data.json", optimization=optimization_payload()
    )[0]
    block = section(html, "optimization-signals")
    body = text_of(block)

    assert "Optimization signals (exploratory)" in text_of(html)
    # Every signal's evidence and note reach the page.
    assert "no lifecycle configuration (NoSuchLifecycleConfiguration)" in body
    assert "StandardStorage 100.0 GB (CloudWatch BucketSizeBytes)" in body
    assert "3 untagged image(s), 1.122 GB total" in body
    assert "Untagged does not mean unreferenced." in body
    assert "s3_no_lifecycle_policy" in body and "ecr_untagged_image_accumulation" in body


def test_a_figure_is_shown_only_where_the_signal_carried_one_and_never_without_its_basis(
    report
):
    """Both directions. The unpriced signal must not acquire a figure from anywhere."""
    html = render_report.render_html(
        report, source_file="report_data.json", optimization=optimization_payload()
    )[0]
    articles = re.findall(r'<article class="candidate">(.*?)</article>',
                          section(html, "optimization-signals"), re.S)
    assert len(articles) == 2

    priced, unpriced = text_of(articles[0]), text_of(articles[1])
    assert "2.30 USD / month" in priced
    assert "0.023 USD/GB-month" in priced
    assert "as of 2026-08-02" in priced
    assert "USD / month" not in unpriced


def test_a_refused_call_reads_as_not_checked_rather_than_as_nothing_found(report):
    """No-silent-caps, reaching the page.

    A denied family and an empty result look identical to a reader unless the report says so,
    and the difference between "unknown" and "zero" is the whole reason the envelope carries
    `denied[]` separately from `signals[]`.
    """
    payload = optimization_payload()
    body = text_of(
        section(
            render_report.render_html(
                report, source_file="report_data.json", optimization=payload
            )[0],
            "optimization-signals",
        )
    )

    assert "Not checked (1)" in body
    assert "unknown, not zero" in body
    assert "secretsmanager:ListSecrets" in body
    assert "AccessDenied" in body
    assert "no NumberOfObjects datapoint published" in body

    # And with nothing found AND something refused, the page still says so rather than
    # implying a clean bill.
    payload["signals"] = []
    payload["totals"] = {"signals": 0, "by_signal": {}}
    empty_body = text_of(
        section(
            render_report.render_html(
                report, source_file="report_data.json", optimization=payload
            )[0],
            "optimization-signals",
        )
    )
    assert "Not checked (1)" in empty_body
    assert "No signals were raised by the calls that ran" in empty_body


def test_the_cli_threads_the_optimization_file_into_the_section(tmp_path, report):
    """End to end through argv, as the orchestrator calls it."""
    signals_path = tmp_path / "optimization_signals_aws_2026-07.json"
    signals_path.write_text(json.dumps(optimization_payload()), encoding="utf-8")

    result = cli(
        [
            str(write_payload(tmp_path, report)),
            "--output-dir", str(tmp_path),
            "--optimization-file", str(signals_path),
        ]
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["status"] == "ok"
    assert summary["optimization"] == {
        "state": "rendered",
        "file": str(signals_path),
        "signals": 2,
        "denied": 1,
    }
    assert summary["sections"] == [
        "header",
        "cost-summary",
        "month-on-month",
        "tag-coverage",
        "orphan-candidates",
        "optimization-signals",
        "data-notes",
    ]
    assert 'id="optimization-signals"' in Path(summary["file"]).read_text(encoding="utf-8")


def test_the_exploratory_section_is_not_confidence_scored_like_the_orphan_section(report):
    """Decision G at the page level: two lanes that must not read as one.

    The orphan section prints a rule and a confidence for every candidate. This one must not,
    or a reader would take an exploratory observation for a scored abandonment verdict.
    """
    block = section(
        render_report.render_html(
            report, source_file="report_data.json", optimization=optimization_payload()
        )[0],
        "optimization-signals",
    )

    # No FINDING carries a score. Scoped to the articles rather than to the whole section,
    # because the section's own caveat says "not confidence-scored" — and that disclaimer is
    # asserted separately below, so a section that dropped it would not pass here by accident.
    for article in re.findall(r'<article class="candidate">(.*?)</article>', block, re.S):
        assert "confidence" not in text_of(article).lower()
    assert "not confidence-scored" in text_of(block)

    # The positive control: the orphan section next door does score every candidate, so the
    # absence above is a property of this section and not of the way it is being read.
    orphan_articles = re.findall(
        r'<article class="candidate">(.*?)</article>',
        section(render(report), "orphan-candidates"),
        re.S,
    )
    assert orphan_articles
    assert any("confidence" in text_of(article).lower() for article in orphan_articles)


# ------------------------------------------------------- m4 t5b — the report value pass
#
# Every new distinction is asserted in BOTH states. A rendering seen in one state only has
# not been shown to distinguish anything — which is the whole subject of this ticket.


def test_the_tags_in_use_table_renders_with_its_tags(report):
    body = text_of(section(render(report), "tag-coverage"))
    assert "Tags in use" in body
    for row in report["tag_coverage"]["tags_in_use"]:
        assert row["tag"] in body


def test_an_inventory_with_no_tags_says_so_rather_than_rendering_an_empty_table(report):
    data = json.loads(json.dumps(report))
    data["tag_coverage"]["tags_in_use"] = []
    data["tag_coverage"]["tags_in_use_total"] = 0
    data["tag_coverage"]["tags_not_shown"] = 0
    body = text_of(section(render(data), "tag-coverage"))
    assert "No tags are in use on any resource in this inventory." in body


def test_the_spenders_cap_states_what_it_dropped_in_both_states(report):
    data = json.loads(json.dumps(report))

    data["tag_coverage"]["untagged_not_shown"] = 0
    kept = text_of(section(render(data), "tag-coverage"))
    assert "dropped none" in kept

    data["tag_coverage"]["untagged_not_shown"] = 5
    dropped = text_of(section(render(data), "tag-coverage"))
    assert "5 further untagged" in dropped
    assert "not shown" in dropped
    # The two states render differently — the point of the row.
    assert kept != dropped


def test_the_tag_table_cap_states_what_it_dropped_in_both_states(report):
    data = json.loads(json.dumps(report))

    data["tag_coverage"]["tags_not_shown"] = 0
    kept = text_of(section(render(data), "tag-coverage"))
    assert "the cap dropped none" in kept

    data["tag_coverage"]["tags_not_shown"] = 3
    data["tag_coverage"]["tags_in_use_total"] = 9
    dropped = text_of(section(render(data), "tag-coverage"))
    assert "3 further tag(s) of" in dropped
    assert kept != dropped


def test_untagged_spender_rows_render_their_tags_or_an_explicit_dash(report):
    data = json.loads(json.dumps(report))
    rows = data["tag_coverage"]["top_untagged_spenders"]
    assert rows, "fixture no longer produces untagged spenders"

    plain = section(render(data), "tag-coverage")
    assert "<th>Tags</th>" in plain

    rows[0]["tags"] = ["env=prod", "owner=team-a"]
    tagged = text_of(section(render(data), "tag-coverage"))
    assert "env=prod" in tagged and "owner=team-a" in tagged


def test_the_governance_block_distinguishes_not_evaluated_from_nothing_found(report):
    """The rider's shape, on the one section where this ticket already had to face it.

    Below the coverage threshold the rule does not run, and the report must not render
    that as "no untagged resources" — it must say the rule did not evaluate.
    """
    data = json.loads(json.dumps(report))

    data["orphans"]["reported"] = [
        {
            "provider": "digitalocean",
            "rule": "untagged_in_tagged_account",
            "account_uses_tags": False,
            "tag_coverage": 0.1667,
            "coverage_threshold": 0.5,
            "resources": [],
        }
    ]
    not_evaluated = text_of(section(render(data), "tag-coverage"))
    assert "Not evaluated" in not_evaluated
    assert 'This is not a finding of "no untagged resources".' in not_evaluated

    data["orphans"]["reported"][0]["account_uses_tags"] = True
    data["orphans"]["reported"][0]["tag_coverage"] = 0.8
    data["orphans"]["reported"][0]["resources"] = [
        {
            "resource_id": "vol-1",
            "type": "volume",
            "name": "untagged-vol",
            "region": "blr1",
            "raw_ref": "do://volumes/vol-1",
            "monthly_cost_estimate": 10.0,
            "evidence": ["tags is empty", "account tag coverage is 80% of 5 resources"],
        }
    ]
    fired = text_of(section(render(data), "tag-coverage"))
    assert "untagged-vol" in fired
    assert "tags is empty" in fired          # the evidence renders, per BL-101
    assert "Not evaluated" not in fired
    assert fired != not_evaluated


def test_a_reported_resource_never_appears_in_the_orphan_section(report):
    """BL-101's Done-when: the m1 ruling on `keep=true` is preserved, not reversed."""
    data = json.loads(json.dumps(report))
    data["orphans"]["reported"] = [
        {
            "provider": "digitalocean",
            "rule": "untagged_in_tagged_account",
            "account_uses_tags": True,
            "tag_coverage": 0.8,
            "coverage_threshold": 0.5,
            "resources": [
                {
                    "resource_id": "kept-1",
                    "type": "volume",
                    "name": "kept-resource",
                    "region": "blr1",
                    "raw_ref": "do://volumes/kept-1",
                    "monthly_cost_estimate": 9.0,
                    "evidence": ["tags is empty"],
                }
            ],
        }
    ]
    page = render(data)
    assert "kept-resource" in text_of(section(page, "tag-coverage"))
    assert "kept-resource" not in text_of(section(page, "orphan-candidates"))
