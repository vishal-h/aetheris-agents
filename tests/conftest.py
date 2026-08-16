import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires live repo files and optionally AETHERIS_DB_PATH")


# ---------------------------------------------------------------------------
# Gate exclusion reporting (BL-152)
# ---------------------------------------------------------------------------
# pytest prints one merged `N deselected`. The whole-suite gate excludes tests for
# two unrelated reasons — `integration` (test mechanics: the test leaves this repo's
# tracked tree) and `dormant` (business state: the use case's work is paused) — and a
# single figure hides the distinction, which is how an exclusion set becomes permanent
# and unexaminable. So each deselected item is attributed to exactly one reason and
# both counts are printed.
#
# Attribution is disjoint and the two counts plus `other` always sum to pytest's own
# total; `dormant` wins when an item carries both, because a dormant use case's tests
# are not gating regardless of their mechanics.
#
# WHY THIS LIVES HERE AND NOT IN A ROOT conftest.py: a conftest.py at the repo root is
# imported by pytest under the bare module name `conftest`, which shadows it for any
# test doing a runtime `from conftest import ...`. Eight cloudcost test modules do
# exactly that, and a root conftest.py broke two of them with
# `ImportError: cannot import name 'CLOUDCOST_ACCESS_KEY' from 'conftest'`. tests/ is
# collected by every whole-tree invocation, so the hooks below are registered for the
# gate; a directory-scoped run will not print the line, which is the accepted cost.

_deselected = []


def pytest_deselected(items):
    _deselected.extend(items)


def pytest_terminal_summary(terminalreporter):
    if not _deselected:
        return
    dormant = integration = other = 0
    for item in _deselected:
        if item.get_closest_marker("dormant"):
            dormant += 1
        elif item.get_closest_marker("integration"):
            integration += 1
        else:
            other += 1
    parts = [f"integration={integration}", f"dormant={dormant}"]
    if other:
        parts.append(f"other={other}")
    terminalreporter.write_line(
        f"deselected by reason: {', '.join(parts)} (total {len(_deselected)})"
    )
