"""The harness sprint's KNOWN_RED resolver, pinned from this repo's side (BL-252).

`../aetheris/scripts/sprint.sh`'s `expected_fail` resolves a ref with
`grep -qE "^### ${ref} "` over the open and closed backlog files, and reads nothing else
of the row. BL-252 changed the open file's row shape without touching the harness, so the
dependency is pinned here.

The first test is hermetic. The second sources the real function from the sibling repo
and is `integration` by `pytest.ini`'s criterion: without `../aetheris` it cannot run.
"""

import re
import subprocess
from pathlib import Path

import pytest

import backlog_status as bs

REPO_ROOT = Path(__file__).resolve().parent.parent
SPRINT_SH = REPO_ROOT.parent / "aetheris" / "scripts" / "sprint.sh"


def _heading_matches(row_id):
    pattern = re.compile(rf"^### {re.escape(row_id)} ", re.M)
    return any(pattern.search(p.read_text()) for p in bs.BACKLOG_FILES)


def test_every_row_id_is_reachable_by_the_resolver_s_heading_pattern():
    rows = bs.load()
    assert rows, "positive control: the union parses"
    missing = [r.row_id for r in rows if not _heading_matches(r.row_id)]
    assert missing == [], missing
    assert not _heading_matches("BL-998"), "negative control: a nonexistent id does not match"


def _title_ids(path):
    return [i for s in bs.parse_sections(path.read_text(), path) if s.is_title
            for i in s.ids if re.fullmatch(r"BL-\d{3}", i)]


@pytest.mark.integration
def test_the_sibling_resolver_accepts_a_row_from_each_file_and_refuses_a_dangling_one():
    if not SPRINT_SH.exists():
        pytest.skip(f"sibling harness not present at {SPRINT_SH}")
    script = (
        'FAILURES=0; KNOWN_RED_ARMS=0; SPRINT_BACKLOG=("$1" "$2"); '
        'eval "$(sed -n \'/^expected_fail() {/,/^}/p\' "$3")"; '
        'expected_fail "$4" probe >/dev/null; echo "$FAILURES $KNOWN_RED_ARMS"'
    )

    def run(ref):
        out = subprocess.run(
            ["bash", "-c", script, "_", str(bs.BACKLOG_MD), str(bs.BACKLOG_ARCHIVE_MD),
             str(SPRINT_SH), ref],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout.split()
        return tuple(int(n) for n in out)

    open_ids, closed_ids = _title_ids(bs.BACKLOG_MD), _title_ids(bs.BACKLOG_ARCHIVE_MD)
    assert open_ids and closed_ids, "positive control: both files hold title rows"
    assert run(open_ids[0]) == (0, 1), open_ids[0]
    assert run(closed_ids[0]) == (0, 1), closed_ids[0]
    assert run("BL-998") == (1, 0)
