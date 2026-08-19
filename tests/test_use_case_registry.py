"""The use-case registry's two tracked-content checks (ds t1a).

`docs/use-cases.md` declares one row per use case: status, the date it was set, the reason as
business state, and the condition for return. Two properties of it are decidable by reading
files in this repository alone, so they ride the whole-suite gate rather than the doc-sync gate:

  MEMBERSHIP   every directory meeting the registry's own criterion has a row, and every row a
               directory. Breaks the moment someone adds a use case, and that person should
               learn it from the gate they already run.

  DORMANCY     the set of use cases whose tests carry `pytest.mark.dormant` is exactly the set
               of rows declaring status `dormant`. This is ds t1a constraint 3's discharge:
               dormancy and test-mechanics exclusions do not share a mechanism, and the two
               sides here are BOTH machine-derived — the registry table and the markers as
               applied — so neither is a sentence anyone has to read at run time. `pytest.ini`'s
               dormancy prose is deliberately not a party to this check.

By `pytest.ini`'s own criterion neither is `integration`: both do their work and pass in a fresh
clone at this commit, offline, with no sibling repository present. Same ground as ds t0's
`tests/test_backlog_status.py`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_MD = REPO_ROOT / "docs" / "use-cases.md"

VALID_STATUSES = {"active", "dormant"}

# A registry row: | `id` | status | YYYY-MM-DD | reason | condition |
# Anchored on the backticked identifier in cell 1, so the header row, the separator row and
# any other pipe table in the file cannot be mistaken for data.
_ROW_RE = re.compile(
    r"^\|\s*`([a-z0-9/_-]+)`\s*\|\s*(\w+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|([^|]*)\|(.*)\|\s*$",
    re.MULTILINE,
)

_SECTION_RE = re.compile(r"^## The registry\s*$(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


def parse_registry(text: str) -> list[dict]:
    """Rows of `## The registry`'s table, in file order.

    Parsed rather than duplicated: a hand-copied expectation would pass while the registry was
    wrong, which is the failure this check exists to remove.
    """
    section = _SECTION_RE.search(text)
    if not section:
        raise AssertionError(
            f"anchor not found: '## The registry' in {REGISTRY_MD.relative_to(REPO_ROOT)}"
        )
    rows = [
        {
            "id": m.group(1),
            "status": m.group(2),
            "status_set": m.group(3),
            "reason": m.group(4).strip(),
            "condition": m.group(5).strip(),
        }
        for m in _ROW_RE.finditer(section.group(1))
    ]
    if not rows:
        raise AssertionError("parsed zero rows from '## The registry'")
    return rows


def discover_use_cases() -> set[str]:
    """Directories meeting the registry's membership criterion, from git's index.

    `git ls-files` rather than a filesystem walk: an untracked directory is not a use case, and
    the criterion is about committed content.
    """
    out = subprocess.run(
        ["git", "ls-files", "*/tests/conftest.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    found = set()
    for path in out:
        d = path[: -len("/tests/conftest.py")]
        if d == "tests":          # the repo root's own tests/ — not a use case
            continue
        if (REPO_ROOT / d / "scripts").is_dir():
            found.add(d)
    return found


def dormant_marked_use_cases() -> set[str]:
    """Use cases with at least one test file carrying `pytest.mark.dormant`."""
    out = subprocess.run(
        ["git", "grep", "-l", "pytest.mark.dormant", "--", "*/tests/*.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    ).stdout.split()
    return {p.split("/tests/")[0] for p in out if "/tests/" in p}


# --------------------------------------------------------------------------- #
# The assertions, as pure functions of their inputs                            #
# --------------------------------------------------------------------------- #
# Split from the pytest wrappers below so each can be mutation-tested on a synthetic
# fixture rather than on a tracked file. Per `../aetheris/CLAUDE.md` **Silent-wrong-answer**,
# ***"construct the broken state and watch the check fail in it, as part of writing the
# check"*** — and the broken state is built here, never by editing docs/use-cases.md.


def check_wellformed(rows: list[dict]) -> None:
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"duplicate registry ids: {ids}"
    bad = [(r["id"], r["status"]) for r in rows if r["status"] not in VALID_STATUSES]
    assert not bad, f"unknown status(es) {bad}; valid: {sorted(VALID_STATUSES)}"
    empty = [r["id"] for r in rows if not r["reason"] or not r["condition"]]
    assert not empty, (
        f"rows with an empty reason or condition-for-return cell: {empty}. "
        "Both fields are required payload — a row that states neither declares nothing."
    )


def check_membership(rows: list[dict], on_disk: set[str]) -> None:
    declared = {r["id"] for r in rows}
    missing_rows = sorted(on_disk - declared)
    orphan_rows = sorted(declared - on_disk)
    assert not missing_rows and not orphan_rows, (
        f"docs/use-cases.md disagrees with the tree.\n"
        f"  directories with no row: {missing_rows}\n"
        f"  rows with no directory:  {orphan_rows}\n"
        "Membership criterion: a directory D != the repo root with both D/tests/conftest.py "
        "and D/scripts/. Reproduce with: "
        "git ls-files '*/tests/conftest.py' | sed 's|/tests/conftest.py||' | grep -v '^tests$'"
    )


def check_dormancy(rows: list[dict], marked: set[str]) -> None:
    declared_dormant = {r["id"] for r in rows if r["status"] == "dormant"}
    assert declared_dormant == marked, (
        f"registry dormancy disagrees with pytest.mark.dormant.\n"
        f"  declared dormant in docs/use-cases.md: {sorted(declared_dormant)}\n"
        f"  carrying pytest.mark.dormant:          {sorted(marked)}\n"
        "These are the same claim in two places and must agree. The registry is the "
        "declaration; the marker is its effect on test selection."
    )


def check_dormant_conditions(rows: list[dict]) -> None:
    for row in (r for r in rows if r["status"] == "dormant"):
        assert len(row["condition"]) >= 40, (
            f"row {row['id']!r} is dormant but its condition-for-return cell is "
            f"{len(row['condition'])} chars: {row['condition']!r}. "
            "It must be something a future reader can evaluate."
        )


# --------------------------------------------------------------------------- #
# Live: the real registry against the real tree                                #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def registry() -> list[dict]:
    assert REGISTRY_MD.exists(), f"registry not found: {REGISTRY_MD}"
    return parse_registry(REGISTRY_MD.read_text(encoding="utf-8"))


def test_registry_rows_are_wellformed(registry):
    """Every row carries a known status, a distinct identifier and both payload fields."""
    check_wellformed(registry)


def test_registry_matches_use_case_directories(registry):
    """MEMBERSHIP — every use-case directory has a row and every row a directory."""
    check_membership(registry, discover_use_cases())


def test_registry_dormancy_matches_markers(registry):
    """DORMANCY — constraint 3. Both sides machine-derived; neither is prose."""
    check_dormancy(registry, dormant_marked_use_cases())


def test_dormant_rows_state_a_condition_for_return(registry):
    """A dormant row whose condition nobody can evaluate is a disabled directory with a date."""
    check_dormant_conditions(registry)


# --------------------------------------------------------------------------- #
# Mutation tests — the broken state, constructed                               #
# --------------------------------------------------------------------------- #

_SYNTHETIC = """# Synthetic registry

## Membership — what is a row

Prose the parser must not read as data, with a table of its own:

| check | home |
|---|---|
| registry <-> directories | tests/ |

## The registry

| Use case | Status | Status set | Reason (business state) | Condition for return |
|---|---|---|---|---|
| `alpha` | active | 2026-01-01 | Work is not paused. | Nothing pending, and this cell is long enough to be evaluated. |
| `beta/one` | dormant | 2026-01-02 | Paused pending a thing. | It runs again when the thing resumes; delete the markers to restore it. |

## After

| not | a row |
|---|---|
"""


def _rows():
    return parse_registry(_SYNTHETIC)


def test_parser_reads_only_the_registry_section():
    """Positive control for the mutation tests below: the parser sees 2 rows, not 4."""
    rows = _rows()
    assert [r["id"] for r in rows] == ["alpha", "beta/one"]
    assert rows[1]["status"] == "dormant"
    assert rows[1]["status_set"] == "2026-01-02"


def test_parser_fails_loudly_when_the_anchor_is_gone():
    with pytest.raises(AssertionError, match="anchor not found"):
        parse_registry(_SYNTHETIC.replace("## The registry", "## The rows"))


def test_parser_fails_loudly_when_the_table_is_empty():
    gutted = _SYNTHETIC.replace("| `alpha`", "| alpha").replace("| `beta/one`", "| beta/one")
    with pytest.raises(AssertionError, match="parsed zero rows"):
        parse_registry(gutted)


def test_mutation_membership_directory_with_no_row():
    """A use case is added and nobody declares it."""
    with pytest.raises(AssertionError, match=r"directories with no row: \['gamma'\]"):
        check_membership(_rows(), {"alpha", "beta/one", "gamma"})


def test_mutation_membership_row_with_no_directory():
    """A row survives the directory it named."""
    with pytest.raises(AssertionError, match=r"rows with no directory:\s+\['beta/one'\]"):
        check_membership(_rows(), {"alpha"})


def test_mutation_membership_passes_when_they_agree():
    """The restore. A check only ever seen fail is as untrustworthy as one only seen pass."""
    check_membership(_rows(), {"alpha", "beta/one"})


def test_mutation_dormancy_marker_without_a_declaration():
    """Someone marks tests dormant and does not touch the registry."""
    with pytest.raises(AssertionError, match="registry dormancy disagrees"):
        check_dormancy(_rows(), {"alpha", "beta/one"})


def test_mutation_dormancy_declaration_without_a_marker():
    """Someone flips a row to dormant and the tests keep gating."""
    with pytest.raises(AssertionError, match="registry dormancy disagrees"):
        check_dormancy(_rows(), set())


def test_mutation_dormancy_passes_when_they_agree():
    check_dormancy(_rows(), {"beta/one"})


def test_mutation_wellformed_unknown_status():
    rows = _rows()
    rows[0]["status"] = "paused"
    with pytest.raises(AssertionError, match="unknown status"):
        check_wellformed(rows)


def test_mutation_wellformed_duplicate_id():
    rows = _rows()
    rows[1]["id"] = "alpha"
    with pytest.raises(AssertionError, match="duplicate registry ids"):
        check_wellformed(rows)


def test_mutation_wellformed_empty_payload_cell():
    rows = _rows()
    rows[0]["condition"] = ""
    with pytest.raises(AssertionError, match="empty reason or condition-for-return"):
        check_wellformed(rows)


def test_mutation_dormant_condition_too_thin_to_evaluate():
    rows = _rows()
    rows[1]["condition"] = "disabled"
    with pytest.raises(AssertionError, match="condition-for-return cell is 8 chars"):
        check_dormant_conditions(rows)
