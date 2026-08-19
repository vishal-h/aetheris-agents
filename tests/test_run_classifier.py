"""Standing guard for Rig's TWO run classifiers (BL-083, widened at ds t1a).

Wraps `scripts/check_run_classifier.py` so its rot directions fail a normal
`python3 -m pytest tests/` rather than waiting for someone to notice a use case sitting
in Unclassified. Same posture as BL-084's manifest suite.

**Two surfaces, not one.** `RunList.tsx` groups the run list and `usage.rs` aggregates the
usage view; both carry a hand-written `USE_CASE_PREFIXES` with the same lowercased
prefix-match semantics, and they must agree. BL-083 fixed the first and left the second, so
ten of thirty-one declared agent labels classified in one view and fell to "Unclassified" in
the other. The guard now parses both and compares them; the tests below cover the comparison
and run the per-surface checks against each.

Hermetic: the checker degrades to declared agent labels when AETHERIS_DB_PATH is unset,
and every prefix is required to match a declared label, so these pass with no store.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "scripts" / "check_run_classifier.py"
RUNLIST = REPO / "rig/src/components/modules/harness/RunList.tsx"
USAGE_RS = REPO / "rig/src-tauri/src/commands/usage.rs"

sys.path.insert(0, str(REPO / "scripts"))


def _surfaces():
    """(name, entries) for both constants, parsed from the real files."""
    import check_run_classifier as c

    return [
        ("RunList.tsx", c.parse_prefixes(RUNLIST.read_text())),
        ("usage.rs", c.parse_rust_prefixes(USAGE_RS.read_text())),
    ]


def run_checker(env=None):
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=REPO, capture_output=True, text=True, env=env,
    )


def test_classifier_guard_passes():
    """No dead prefixes, and every declared agent label classifies."""
    result = run_checker()
    assert result.returncode == 0, (
        f"run-classifier guard failed:\n{result.stdout}\n{result.stderr}"
    )


def test_the_two_constants_agree():
    """The check ds t1a exists for: usage.rs and RunList.tsx declare the same prefixes.

    Compared as prefix -> group mappings, so the TS constant's grouped shape and the Rust
    constant's flat pairs are comparable without either being privileged.
    """
    import check_run_classifier as c

    (name_a, a), (name_b, b) = _surfaces()
    map_a, map_b = c.as_mapping(a), c.as_mapping(b)
    assert map_a == map_b, (
        f"{name_a} and {name_b} disagree.\n"
        f"  in {name_a} only: {{k: v for k, v in map_a.items() if k not in map_b}}\n"
        f"  in {name_b} only: {{k: v for k, v in map_b.items() if k not in map_a}}\n"
        f"  regrouped: "
        f"{{k: (map_a[k], map_b[k]) for k in map_a.keys() & map_b.keys() if map_a[k] != map_b[k]}}"
    )


@pytest.mark.parametrize("surface", ["RunList.tsx", "usage.rs"])
def test_every_declared_label_classifies(surface):
    """Direct assertion, so a failure names the label rather than only the exit code."""
    import re

    import check_run_classifier as c

    entries = dict(_surfaces())[surface]
    declared = {re.sub(r"#\{[^}]+\}", "X", d) for d in c.declared_labels()}
    assert declared, "no agent labels found — the scan is broken, not the classifier"

    stranded = sorted(l for l in declared if c.classify(l, entries) == "Unclassified")
    assert not stranded, (
        f"{surface}: declared labels falling through to Unclassified: {stranded}"
    )


@pytest.mark.parametrize("surface", ["RunList.tsx", "usage.rs"])
def test_no_dead_prefixes_against_declared_labels(surface):
    """Every prefix must match at least one declared label (the BL-083 defect)."""
    import re

    import check_run_classifier as c

    entries = dict(_surfaces())[surface]
    declared = {re.sub(r"#\{[^}]+\}", "X", d) for d in c.declared_labels()}

    dead = [
        p for prefixes, _ in entries for p in prefixes
        if not any(l.lower().startswith(p) for l in declared)
    ]
    assert not dead, f"{surface}: prefixes matching no declared label: {dead}"


def test_one_entry_per_group_label():
    """groupRuns() pushes one group per entry — duplicate labels render duplicate headings."""
    import check_run_classifier as c

    entries = c.parse_prefixes(RUNLIST.read_text())
    labels = [group for _, group in entries]
    dupes = {l for l in labels if labels.count(l) > 1}
    assert not dupes, f"group label(s) declared by more than one entry: {sorted(dupes)}"


@pytest.mark.parametrize(
    "label,expected",
    [
        ("Cloudcost · AWS", "Cloudcost"),
        ("Cloudcost · DigitalOcean", "Cloudcost"),
        ("Cloudcost Orchestrator", "Cloudcost"),
        ("Docbuilder Context Builder", "Docbuilder"),
        ("Docbuilder Context Orchestrator", "Docbuilder"),
        ("at1qry — TAP Tenant Collector", "API / Tenant"),
        ("cot1_stub — TAP Gateway Stub", "API / Gateway"),
        ("Capability Matrix -- Provenance", "Capability Matrix"),
        ("cap-matrix: cloudcost", "Capability Matrix"),
        ("Eduloka Orchestrator", "Eduloka"),
        ("Smoke test", "Unclassified"),
    ],
)
def test_known_labels_map_to_expected_group(label, expected):
    """Real labels observed in the store, including the provider-suffixed cloudcost ones.

    Run against BOTH surfaces: these are the labels a user sees grouped in the run list and
    aggregated in the usage view, and the whole point of ds t1a's widening is that the two
    answers must be the same one.

    `cap-matrix: cloudcost` is the ordering guard: it must group as Capability Matrix,
    not Cloudcost, and would silently regress if anyone switched startsWith to includes.
    """
    import check_run_classifier as c

    for name, entries in _surfaces():
        assert c.classify(label, entries) == expected, name


# --------------------------------------------------------------------------- #
# Mutation tests — synthetic sources, never a tracked file                     #
# --------------------------------------------------------------------------- #

_TSX = """const USE_CASE_PREFIXES: Array<{ prefixes: string[]; label: string }> = [
  { prefixes: ['alpha'],          label: 'Alpha' },
  { prefixes: ['b1', 'b2'],       label: 'Beta' },
];
"""

_RS = """const USE_CASE_PREFIXES: &[(&str, &str)] = &[
    ("alpha", "Alpha"),
    ("b1",    "Beta"),
    ("b2",    "Beta"),
];
"""


def test_mutation_positive_control_both_parsers_agree():
    """The control every mutation below is read against."""
    import check_run_classifier as c

    a = c.as_mapping(c.parse_prefixes(_TSX))
    b = c.as_mapping(c.parse_rust_prefixes(_RS))
    assert a == b == {"alpha": "Alpha", "b1": "Beta", "b2": "Beta"}


def test_mutation_rust_parser_ignores_comment_lines():
    """A commented-out pair must not be read as a live entry."""
    import check_run_classifier as c

    mutated = _RS.replace('    ("b2",    "Beta"),', '    // ("b2",    "Beta"),')
    assert "b2" not in c.as_mapping(c.parse_rust_prefixes(mutated))


def test_mutation_a_prefix_dropped_from_one_side_is_visible():
    """BL-083's exact shape: one copy is fixed and the other is not."""
    import check_run_classifier as c

    mutated = _RS.replace('    ("b2",    "Beta"),\n', "")
    a = c.as_mapping(c.parse_prefixes(_TSX))
    b = c.as_mapping(c.parse_rust_prefixes(mutated))
    assert a != b
    assert {k: v for k, v in a.items() if k not in b} == {"b2": "Beta"}


def test_mutation_a_dead_prefix_left_on_one_side_is_visible():
    """The other half of BL-083: a stale prefix survives in one constant."""
    import check_run_classifier as c

    mutated = _RS.replace('];', '    ("api-tenant", "API / Tenant"),\n];')
    a = c.as_mapping(c.parse_prefixes(_TSX))
    b = c.as_mapping(c.parse_rust_prefixes(mutated))
    assert a != b
    assert {k: v for k, v in b.items() if k not in a} == {"api-tenant": "API / Tenant"}


def test_mutation_same_prefix_regrouped_is_visible():
    """Neither side is missing a prefix; they disagree about which group it is in."""
    import check_run_classifier as c

    mutated = _RS.replace('("b2",    "Beta")', '("b2",    "Gamma")')
    a = c.as_mapping(c.parse_prefixes(_TSX))
    b = c.as_mapping(c.parse_rust_prefixes(mutated))
    assert a != b
    assert a.keys() == b.keys(), "the divergence must not be a missing key"
    assert [k for k in a if a[k] != b[k]] == ["b2"]


def test_mutation_rust_parser_fails_loudly_on_a_missing_constant():
    import check_run_classifier as c

    with pytest.raises(SystemExit, match="USE_CASE_PREFIXES not found"):
        c.parse_rust_prefixes("fn main() {}\n")


def test_mutation_rust_parser_fails_loudly_on_an_empty_constant():
    import check_run_classifier as c

    with pytest.raises(SystemExit, match="parsed zero entries"):
        c.parse_rust_prefixes("const USE_CASE_PREFIXES: &[(&str, &str)] = &[\n];\n")
