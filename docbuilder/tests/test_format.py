"""Unit tests for the shared cell-display formatter (scripts/_format.py).

Pure stdlib — no external deps, so these run in the standard
`-m "not integration"` done-check.
"""

import pytest

from _format import format_cell, format_currency, format_number


# --- currency ---

@pytest.mark.parametrize("value,expected", [
    (1000, "$1,000.00"),
    (1000.0, "$1,000.00"),
    ("1000.00", "$1,000.00"),
    (1234.5, "$1,234.50"),
    (1234.567, "$1,234.57"),     # rounds to 2 dp
    (0, "$0.00"),
    (-50, "$-50.00"),
])
def test_format_currency_numeric(value, expected):
    assert format_currency(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("Amount", "Amount"),        # header label — not numeric, passes through
    ("", ""),
    (None, ""),
])
def test_format_currency_non_numeric_passthrough(value, expected):
    assert format_currency(value) == expected


# --- number (thousands separators, no trailing zeros) ---

@pytest.mark.parametrize("value,expected", [
    (1, "1"),
    ("1", "1"),
    (1000, "1,000"),
    (1000.0, "1,000"),
    (1234.5, "1,234.5"),
    (1234.50, "1,234.5"),
    (1234.567, "1,234.57"),
])
def test_format_number_numeric(value, expected):
    assert format_number(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("# Resource(s)", "# Resource(s)"),  # header label passes through
    (None, ""),
])
def test_format_number_non_numeric_passthrough(value, expected):
    assert format_number(value) == expected


# --- format_cell dispatch ---

def test_format_cell_currency():
    assert format_cell(1000, "currency") == "$1,000.00"


def test_format_cell_number():
    assert format_cell(1, "number") == "1"


@pytest.mark.parametrize("col_type", ["string", None, "unknown"])
def test_format_cell_other_types_passthrough(col_type):
    assert format_cell("May", col_type) == "May"
    assert format_cell(5, col_type) == "5"


def test_format_cell_none_value():
    assert format_cell(None, "string") == ""
    assert format_cell(None, "currency") == ""
