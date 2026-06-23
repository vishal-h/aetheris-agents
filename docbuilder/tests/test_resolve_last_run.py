"""Unit + CLI tests for resolve_last_run.py (m3 t3).

Pure stdlib — runs in the standard `-m "not integration"` done-check.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from resolve_last_run import (
    _parse_target_month,
    bump_invoice_number,
    find_last_match,
    fy_code,
    month_end,
    resolve,
)

USE_CASE_ROOT = Path(__file__).parent.parent


def _entry(run_id, client_name, invoice_number, date, ts, doc_type="invoice",
           tenant="bitloka", title=None):
    return {
        "tenant": tenant, "doc_type": doc_type, "variant": "v1",
        "run_id": run_id, "timestamp": ts,
        "context": {
            "title": title or f"Invoice {invoice_number}",
            "client_name": client_name, "client_email": "a@b.c", "date": date,
            "doc_type": doc_type, "invoice_number": invoice_number,
            "client_address": "1234 Stevens Creek Blvd", "amount_due": "$1,000.00",
            "terms": "Discounted rates",
        },
        "outputs": [],
    }


@pytest.fixture
def seed_log():
    return [_entry("run-1", "XYZ Inc", "2627/XYZ/02", "31-May-2026",
                   "2026-06-21T07:27:00+05:30")]


# --- fy_code (April-1 rollover) ---

@pytest.mark.parametrize("year,month,expected", [
    (2026, 5, "2627"),   # May  → FY 2026-27
    (2026, 4, "2627"),   # Apr  → boundary, new FY
    (2026, 6, "2627"),   # Jun
    (2026, 12, "2627"),  # Dec  → still 2026-27
    (2026, 3, "2526"),   # Mar  → FY 2025-26
    (2026, 1, "2526"),   # Jan
    (2027, 4, "2728"),   # next FY
])
def test_fy_code(year, month, expected):
    assert fy_code(year, month) == expected


# --- month_end ---

@pytest.mark.parametrize("year,month,expected", [
    (2026, 6, "30-Jun-2026"),
    (2026, 2, "28-Feb-2026"),
    (2024, 2, "29-Feb-2024"),   # leap year
    (2026, 12, "31-Dec-2026"),
    (2026, 1, "31-Jan-2026"),
])
def test_month_end(year, month, expected):
    assert month_end(year, month) == expected


# --- _parse_target_month ---

def test_parse_target_month_basic():
    assert _parse_target_month("2026-06") == (2026, 6)


def test_parse_target_month_default_is_current(monkeypatch):
    import resolve_last_run as r
    class _Now:
        @staticmethod
        def now():
            import datetime as _dt
            return _dt.datetime(2026, 6, 23)
    monkeypatch.setattr(r, "datetime", _Now)
    assert _parse_target_month(None) == (2026, 6)


def test_parse_target_month_extra_parts_raises():
    # "2026-06-01" → ("2026", "06-01") → int("06-01") raises (F2 hardening).
    with pytest.raises(ValueError):
        _parse_target_month("2026-06-01")


def test_parse_target_month_out_of_range_raises():
    with pytest.raises(ValueError):
        _parse_target_month("2026-13")


# --- bump_invoice_number ---

def test_bump_basic():
    # June 2026 invoice off May 2026's 2627/XYZ/02 → seq+1, same FY.
    assert bump_invoice_number("2627/XYZ/02", 2026, 6) == "2627/XYZ/03"


def test_bump_fy_rollover_march_to_april():
    # Last invoice was March 2026 (FY 2025-26); new one is April 2026 (FY 2026-27).
    # FY part changes 2526→2627, sequence still increments (no reset per spec).
    assert bump_invoice_number("2526/XYZ/05", 2026, 4) == "2627/XYZ/06"


def test_bump_preserves_pad_width():
    assert bump_invoice_number("2627/XYZ/09", 2026, 6) == "2627/XYZ/10"
    assert bump_invoice_number("2627/XYZ/099", 2026, 6) == "2627/XYZ/100"


def test_bump_unparseable_returns_none():
    assert bump_invoice_number("ABC123", 2026, 6) is None
    assert bump_invoice_number("2627/XYZ/0A", 2026, 6) is None
    assert bump_invoice_number("2627/XYZ", 2026, 6) is None


# --- find_last_match ---

def test_find_match_exact(seed_log):
    m = find_last_match(seed_log, "bitloka", "invoice", "XYZ Inc")
    assert m["run_id"] == "run-1"


def test_find_match_client_substring(seed_log):
    # "XYZ" should match "XYZ Inc".
    assert find_last_match(seed_log, "bitloka", "invoice", "XYZ")["run_id"] == "run-1"


def test_find_match_none_wrong_client(seed_log):
    assert find_last_match(seed_log, "bitloka", "invoice", "Acme") is None


def test_find_match_none_wrong_doc_type(seed_log):
    assert find_last_match(seed_log, "bitloka", "proposal", "XYZ Inc") is None


def test_find_match_latest_by_timestamp():
    log = [
        _entry("old", "XYZ Inc", "2627/XYZ/02", "31-May-2026", "2026-05-31T10:00:00+05:30"),
        _entry("new", "XYZ Inc", "2627/XYZ/03", "30-Jun-2026", "2026-06-30T10:00:00+05:30"),
    ]
    assert find_last_match(log, "bitloka", "invoice", "XYZ Inc")["run_id"] == "new"


# --- resolve ---

def test_resolve_bumps_date_and_invoice(seed_log):
    ctx, match, warnings = resolve(seed_log, "bitloka", "invoice", "XYZ Inc", 2026, 6)
    assert ctx["date"] == "30-Jun-2026"
    assert ctx["invoice_number"] == "2627/XYZ/03"
    assert ctx["title"] == "Invoice 2627/XYZ/03"        # title substring updated
    assert ctx["client_name"] == "XYZ Inc"               # carried verbatim
    assert ctx["client_address"] == "1234 Stevens Creek Blvd"
    assert ctx["terms"] == "Discounted rates"
    assert match["run_id"] == "run-1"
    assert warnings == []


def test_resolve_no_match_returns_none(seed_log):
    ctx, match, warnings = resolve(seed_log, "bitloka", "invoice", "Nobody", 2026, 6)
    assert ctx is None and match is None


def test_resolve_unparseable_invoice_warns_but_bumps_date():
    log = [_entry("r", "XYZ Inc", "WEIRD-NUMBER", "31-May-2026",
                  "2026-05-31T10:00:00+05:30")]
    ctx, _m, warnings = resolve(log, "bitloka", "invoice", "XYZ Inc", 2026, 6)
    assert ctx["date"] == "30-Jun-2026"
    assert ctx["invoice_number"] == "WEIRD-NUMBER"       # left unchanged
    assert warnings and "left unchanged" in warnings[0]


def test_resolve_does_not_mutate_source(seed_log):
    resolve(seed_log, "bitloka", "invoice", "XYZ Inc", 2026, 6)
    assert seed_log[0]["context"]["invoice_number"] == "2627/XYZ/02"
    assert seed_log[0]["context"]["date"] == "31-May-2026"


# --- CLI ---

def _run(args, **kw):
    return subprocess.run(
        [sys.executable, "scripts/resolve_last_run.py", *args],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), **kw)


def test_cli_resolves_to_output_file(tmp_path):
    log = tmp_path / "run_log.json"
    log.write_text(json.dumps([_entry(
        "run-1", "XYZ Inc", "2627/XYZ/02", "31-May-2026", "2026-06-21T07:27:00+05:30")]))
    out = tmp_path / "confirmed_context.json"
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "XYZ Inc",
              "--target-month", "2026-06", "--run-log", str(log), "--output", str(out)])
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == str(out)
    ctx = json.loads(out.read_text())
    assert ctx["date"] == "30-Jun-2026"
    assert ctx["invoice_number"] == "2627/XYZ/03"
    # resolution summary goes to stderr, not stdout
    assert "matched_run_id" in r.stderr


def test_cli_stdout_when_no_output(tmp_path):
    log = tmp_path / "run_log.json"
    log.write_text(json.dumps([_entry(
        "run-1", "XYZ Inc", "2627/XYZ/02", "31-May-2026", "2026-06-21T07:27:00+05:30")]))
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "XYZ",
              "--target-month", "2026-07", "--run-log", str(log)])
    assert r.returncode == 0, r.stderr
    ctx = json.loads(r.stdout)
    assert ctx["date"] == "31-Jul-2026"
    assert ctx["invoice_number"] == "2627/XYZ/03"


def test_cli_no_prior_run_graceful(tmp_path):
    log = tmp_path / "run_log.json"
    log.write_text("[]")
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "XYZ Inc",
              "--target-month", "2026-06", "--run-log", str(log)])
    assert r.returncode == 0
    assert json.loads(r.stdout)["status"] == "no_prior_run"


def test_cli_missing_log_is_no_prior_run(tmp_path):
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "XYZ Inc",
              "--run-log", str(tmp_path / "nope.json")])
    assert r.returncode == 0
    assert json.loads(r.stdout)["status"] == "no_prior_run"


def test_cli_bad_target_month_exits_1(tmp_path):
    log = tmp_path / "run_log.json"
    log.write_text("[]")
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "X",
              "--target-month", "2026-13", "--run-log", str(log)])
    assert r.returncode == 1
    assert "error" in r.stderr


def test_cli_target_month_extra_parts_exits_1(tmp_path):
    # F2: a 3-part --target-month must exit 1 cleanly, not raise an unhandled error.
    log = tmp_path / "run_log.json"
    log.write_text("[]")
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "X",
              "--target-month", "2026-06-01", "--run-log", str(log)])
    assert r.returncode == 1
    assert "error" in r.stderr
    assert "Traceback" not in r.stderr  # clean error path, not an unhandled exception


def test_cli_corrupt_log_exits_1(tmp_path):
    log = tmp_path / "run_log.json"
    log.write_text('{"not": "array"}')
    r = _run(["--tenant", "bitloka", "--doc-type", "invoice", "--client-name", "X",
              "--run-log", str(log)])
    assert r.returncode == 1
    assert "error" in r.stderr
