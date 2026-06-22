"""Shared display formatting for cell values, keyed off the doc-spec column type.

Used by the text-based renderers (`generate_docx`, and `_table_html` →
`generate_pdf` / `render_template`) so a `currency` column shows `$1,000.00` and a
plain `number` column shows `1` (not `1.00`). The xlsx renderer formats natively
via Excel number formats and does not use this module.

The cell value reaching a renderer may be a number (the sum aggregate yields an
int/float) or a numeric string (a CSV data cell). A value that cannot be parsed as
a number passes through unchanged (e.g. a header label or a non-numeric column).
"""


def _as_number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _passthrough(value):
    return "" if value is None else str(value)


def format_currency(value):
    """Format a numeric (or numeric-string) value as ``$1,234.56``.

    Returns the value's string form unchanged if it is not numeric."""
    num = _as_number(value)
    if num is None:
        return _passthrough(value)
    return f"${num:,.2f}"


def format_number(value):
    """Format a number with thousands separators and no trailing zeros:
    ``1`` → ``1``, ``1000`` → ``1,000``, ``1234.5`` → ``1,234.5``.

    Returns the value's string form unchanged if it is not numeric."""
    num = _as_number(value)
    if num is None:
        return _passthrough(value)
    if num == int(num):
        return f"{int(num):,}"
    return f"{num:,.2f}".rstrip("0").rstrip(".")


def format_cell(value, col_type):
    """Return the display string for a cell value given its column ``type``.

    Unknown / string / None column types fall through to ``str(value)`` so the
    text renderers behave exactly as before for non-numeric columns."""
    if col_type == "currency":
        return format_currency(value)
    if col_type == "number":
        return format_number(value)
    return _passthrough(value)
