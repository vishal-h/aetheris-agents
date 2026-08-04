"""Standing guard for Rig's run-list classifier (BL-083).

Wraps `scripts/check_run_classifier.py` so the two rot directions it checks — a prefix
matching nothing, and a declared agent label matching no prefix — fail a normal
`python3 -m pytest tests/` rather than waiting for someone to notice a use case sitting
in Unclassified. Same posture as BL-084's manifest suite.

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

sys.path.insert(0, str(REPO / "scripts"))


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


def test_every_declared_label_classifies():
    """Direct assertion, so a failure names the label rather than only the exit code."""
    import check_run_classifier as c

    entries = c.parse_prefixes(RUNLIST.read_text())
    import re

    declared = {re.sub(r"#\{[^}]+\}", "X", d) for d in c.declared_labels()}
    assert declared, "no agent labels found — the scan is broken, not the classifier"

    stranded = sorted(l for l in declared if c.classify(l, entries) == "Unclassified")
    assert not stranded, f"declared labels falling through to Unclassified: {stranded}"


def test_no_dead_prefixes_against_declared_labels():
    """Every prefix must match at least one declared label (the BL-083 defect)."""
    import check_run_classifier as c
    import re

    entries = c.parse_prefixes(RUNLIST.read_text())
    declared = {re.sub(r"#\{[^}]+\}", "X", d) for d in c.declared_labels()}

    dead = [
        p for prefixes, _ in entries for p in prefixes
        if not any(l.lower().startswith(p) for l in declared)
    ]
    assert not dead, f"prefixes matching no declared label: {dead}"


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

    `cap-matrix: cloudcost` is the ordering guard: it must group as Capability Matrix,
    not Cloudcost, and would silently regress if anyone switched startsWith to includes.
    """
    import check_run_classifier as c

    entries = c.parse_prefixes(RUNLIST.read_text())
    assert c.classify(label, entries) == expected
