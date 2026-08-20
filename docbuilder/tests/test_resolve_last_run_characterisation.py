"""Characterisation of `resolve_last_run.py`'s contract, pinned before ds t2 changes it.

`resolve_last_run.py` is the **live consumer** of the docbuilder run log, and ds t2
generalises the log's writer onto a shared module. This file pins the consumer's observed
behaviour *before* that change so the change can be shown not to move it. It is written
against behaviour, not against implementation: nothing here imports a private helper or
asserts a call sequence, so it stays valid across the generalisation.

The contract it pins, each clause read out of the source at `f9328aa`:

  * `tenant` and `doc_type` match by exact `==` (`:77-78`);
  * `context.client_name` matches case-insensitively as a substring in **either**
    direction (`:79`, `_client_match` `:62-67`);
  * "most recent" is the **lexicographic max of the `timestamp` string**, tie-broken by
    array order (`:83`);
  * the whole `context` dict is carried forward, not a selected subset (`:92`);
  * `run_id` is read for a stderr summary line only (`:171`) and never selects.

The lexicographic clause is pinned **as a defect**, deliberately. It is BL-151's first
filing from this ticket: over the local-offset stamps `run_log_writer.build_entry` writes
(`:80`), a string sort orders by printed digits rather than by instant. Pinning it keeps
this ticket honest — t2 must not quietly change the consumer's selection while claiming
only to have moved the writer. `test_lexicographic_sort_is_the_pinned_defect` states the
inversion in the terms a fix would have to change.
"""

import json

import pytest

from resolve_last_run import find_last_match, resolve


def _entry(*, tenant="bitloka", doc_type="invoice", client="Northwind Traders",
           timestamp="2026-05-31T12:00:00+05:30", run_id="r1", **ctx):
    """One run-log entry in the shape `run_log_writer.build_entry` produces."""
    context = {"client_name": client}
    context.update(ctx)
    return {
        "tenant": tenant,
        "doc_type": doc_type,
        "variant": "1",
        "run_id": run_id,
        "timestamp": timestamp,
        "context": context,
        "outputs": [],
    }


# --------------------------------------------------------------------------- matching


def test_tenant_and_doc_type_match_exactly():
    """Both are `==`, so a near-miss on either selects nothing."""
    log = [_entry()]
    assert find_last_match(log, "bitloka", "invoice", "Northwind") is not None
    # The state in which the check fails: a tenant differing only in case.
    assert find_last_match(log, "Bitloka", "invoice", "Northwind") is None
    assert find_last_match(log, "bitloka", "invoices", "Northwind") is None


@pytest.mark.parametrize("query", ["Northwind Traders", "northwind traders",
                                   "NORTHWIND", "  northwind  "])
def test_client_name_matches_case_insensitively_and_either_direction(query):
    """Query inside entry, entry inside query, and exact — all match; case is folded."""
    log = [_entry(client="Northwind Traders")]
    assert find_last_match(log, "bitloka", "invoice", query) is not None


def test_client_name_matches_when_the_entry_is_the_substring():
    """The *other* direction: the stored name is contained in the query."""
    log = [_entry(client="Northwind")]
    assert find_last_match(log, "bitloka", "invoice", "Northwind Traders Ltd") is not None


def test_empty_client_name_never_matches():
    """An empty query or an empty stored name is a non-match, not a wildcard."""
    assert find_last_match([_entry(client="")], "bitloka", "invoice", "Northwind") is None
    assert find_last_match([_entry()], "bitloka", "invoice", "") is None


# --------------------------------------------------------------------------- selection


def test_most_recent_is_the_max_timestamp_not_the_last_element():
    """Selection is by timestamp, so array order does not decide it on its own."""
    log = [
        _entry(run_id="older", timestamp="2026-05-31T12:00:00+05:30"),
        _entry(run_id="newer", timestamp="2026-06-30T12:00:00+05:30"),
        _entry(run_id="middle", timestamp="2026-06-15T12:00:00+05:30"),
    ]
    assert find_last_match(log, "bitloka", "invoice", "Northwind")["run_id"] == "newer"


def test_equal_timestamps_are_tie_broken_by_array_order():
    """Same stamp → the later element wins (append/replace puts the latest write last)."""
    ts = "2026-06-30T12:00:00+05:30"
    log = [_entry(run_id="first", timestamp=ts), _entry(run_id="second", timestamp=ts)]
    assert find_last_match(log, "bitloka", "invoice", "Northwind")["run_id"] == "second"


def test_lexicographic_sort_is_the_pinned_defect():
    """Selection sorts the timestamp STRING, so offsets invert it. Pinned as a defect.

    `later_instant` is 2026-06-30T09:00:00Z; `earlier_instant` is 2026-06-30T12:00:00Z —
    three hours EARLIER in real time, and lexicographically greater because "14" > "12".
    A correct chronological selection returns `later_instant`. This asserts what the code
    does today, which is the opposite; it is BL-151's first filing from ds t2.
    """
    log = [
        _entry(run_id="later_instant", timestamp="2026-06-30T12:00:00+00:00"),
        _entry(run_id="earlier_instant", timestamp="2026-06-30T14:30:00+05:30"),
    ]
    selected = find_last_match(log, "bitloka", "invoice", "Northwind")["run_id"]
    assert selected == "earlier_instant", (
        "the lexicographic sort no longer inverts across offsets — if this is a "
        "deliberate fix, retire this characterisation and close BL-151's entry"
    )


def test_run_id_does_not_participate_in_selection():
    """A run_id that sorts high does not win; the timestamp decides."""
    log = [
        _entry(run_id="zzzz", timestamp="2026-05-31T12:00:00+05:30"),
        _entry(run_id="aaaa", timestamp="2026-06-30T12:00:00+05:30"),
    ]
    assert find_last_match(log, "bitloka", "invoice", "Northwind")["run_id"] == "aaaa"


# --------------------------------------------------------------------------- carry-forward


def test_whole_context_dict_is_carried_forward():
    """Every key survives; only `date`, `invoice_number` and `title` are rewritten."""
    log = [_entry(
        timestamp="2026-05-31T12:00:00+05:30",
        invoice_number="2627/NWT/01",
        title="Invoice 2627/NWT/01",
        client_code="NWT",
        order_ref="PO-4471",
        terms="Net 30",
        amount_due="125000.00",
    )]
    ctx, match, warnings = resolve(log, "bitloka", "invoice", "Northwind", 2026, 6)

    assert warnings == []
    assert ctx["date"] == "30-Jun-2026"
    assert ctx["invoice_number"] == "2627/NWT/02"
    assert ctx["title"] == "Invoice 2627/NWT/02"
    # Untouched keys, carried verbatim.
    assert ctx["client_code"] == "NWT"
    assert ctx["order_ref"] == "PO-4471"
    assert ctx["terms"] == "Net 30"
    assert ctx["amount_due"] == "125000.00"
    assert ctx["client_name"] == "Northwind Traders"
    # The source entry is not mutated.
    assert match["context"]["invoice_number"] == "2627/NWT/01"


def test_no_match_returns_the_no_prior_run_shape():
    """No match → `(None, None, [])`, which the CLI renders as `no_prior_run`, exit 0."""
    assert resolve([], "bitloka", "invoice", "Northwind", 2026, 6) == (None, None, [])


def test_unparseable_invoice_number_warns_and_leaves_it_unchanged():
    """The date bump still applies; the invoice number is left alone with a warning."""
    log = [_entry(invoice_number="not-an-invoice", title="Draft")]
    ctx, _match, warnings = resolve(log, "bitloka", "invoice", "Northwind", 2026, 6)

    assert ctx["invoice_number"] == "not-an-invoice"
    assert ctx["date"] == "30-Jun-2026"
    assert len(warnings) == 1 and "not in FY/code/seq form" in warnings[0]


def test_the_log_shape_this_pins_is_the_one_the_writer_emits():
    """Guard against the fixture drifting from `run_log_writer.build_entry`'s shape."""
    from run_log_writer import build_entry

    produced = build_entry("bitloka", "invoice", "1", "r1", {"client_name": "N"}, [])
    assert set(produced) == set(_entry())
    # The writer's own stamp is what the lexicographic selection sorts.
    assert json.dumps(produced)  # serialisable, as the log file requires
