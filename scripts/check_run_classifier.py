#!/usr/bin/env python3
"""Guard Rig's run-list classifier against the two ways it silently rots (BL-083).

Rig groups the run list by `classifyRun(label)` (rig/src/components/modules/harness/
RunList.tsx), matching lowercased `startsWith` against USE_CASE_PREFIXES. The input is
COALESCE(r.label, r.run_id) (rig/src-tauri/src/commands/harness.rs:161), so unlabelled
runs are classified by run_id.

Two failure directions, both of which have actually happened:

  DEAD ENTRY      a prefix that matches nothing. `api-tenant` / `api-gateway` sat in the
                  list matching zero labels because the api agents are labelled by agent
                  id (at1cmd / at1qry / cot1), not by directory name.

  UNCLASSIFIED    a declared agent label that no prefix matches, so its runs fall into
                  Unclassified. cloudcost and docbuilder did this for 69 runs.

The "real label" universe is declared agent labels UNION observed run labels. Declared
labels matter on their own: `Eduloka Orchestrator` is declared and has produced no run
yet, and a classifier that only knew about observed runs would call its prefix dead and
invite someone to delete it right before the first eduloka run lands.

Exit 0 when both checks pass, 1 otherwise. The DB is optional — without it the checks
still run against declared labels alone, and say so.
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNLIST = REPO / "rig/src/components/modules/harness/RunList.tsx"

GREEN, RED, YELLOW, CYAN, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[0m"


def parse_prefixes(source: str) -> list[tuple[list[str], str]]:
    """Pull USE_CASE_PREFIXES out of RunList.tsx.

    Parsed rather than duplicated so the guard cannot drift from the thing it guards —
    a hand-copied list would pass while the real classifier was broken.
    """
    block = re.search(
        r"const USE_CASE_PREFIXES[^=]*=\s*\[(.*?)\n\];", source, re.S
    )
    if not block:
        raise SystemExit(f"{RED}FAIL{RESET}: USE_CASE_PREFIXES not found in {RUNLIST}")

    entries: list[tuple[list[str], str]] = []
    for line in block.group(1).splitlines():
        if line.lstrip().startswith("//"):
            continue
        m = re.search(r"prefixes:\s*\[(.*?)\]\s*,\s*label:\s*'([^']+)'", line)
        if m:
            prefixes = re.findall(r"'([^']*)'", m.group(1))
            entries.append((prefixes, m.group(2)))
    if not entries:
        raise SystemExit(f"{RED}FAIL{RESET}: parsed zero entries from USE_CASE_PREFIXES")
    return entries


def classify(label: str, entries: list[tuple[list[str], str]]) -> str:
    """Mirror of classifyRun() in RunList.tsx."""
    lower = label.lower()
    for prefixes, group in entries:
        if any(lower.startswith(p) for p in prefixes):
            return group
    return "Unclassified"


# A RunConfig field: `label:` at the start of its line, value, trailing comma. Anchored
# deliberately — an unanchored `label:\s*"..."` also matches prose inside a system_prompt
# (the capability-matrix agents describe `- The label: "..." value`), which showed up as a
# declared label named "..." the first time this ran.
LABEL_FIELD = re.compile(r'^[ \t]*label:[ \t]*"([^"]+)"[ \t]*,', re.M)


def declared_labels() -> set[str]:
    """Every literal `label:` RunConfig field declared by an agent .exs."""
    found: set[str] = set()
    for exs in REPO.glob("**/agents/*.exs"):
        if "node_modules" in exs.parts:
            continue
        found.update(LABEL_FIELD.findall(exs.read_text(errors="replace")))
    return found


def observed_labels(db_path: str | None) -> set[str]:
    """Distinct COALESCE(label, run_id) actually in the store."""
    if not db_path or not Path(db_path).exists():
        return set()
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT DISTINCT COALESCE(label, run_id) FROM runs"
        ).fetchall()
    finally:
        con.close()
    return {r[0] for r in rows if r[0]}


def main() -> int:
    entries = parse_prefixes(RUNLIST.read_text())
    declared = declared_labels()
    db = os.environ.get("AETHERIS_DB_PATH")
    observed = observed_labels(db)

    # An interpolated label such as "Cloudcost · #{provider_name}" is stored with the
    # placeholder intact; expand it to something matchable so the guard tests the real
    # emitted shape rather than the source text.
    expanded = {re.sub(r"#\{[^}]+\}", "X", d) for d in declared}
    universe = expanded | observed

    print(f"{CYAN}Rig run-classifier guard — {len(entries)} groups{RESET}")
    print(
        f"  labels: {len(expanded)} declared in agent files, "
        f"{len(observed)} observed in store"
        + ("" if observed else f" {YELLOW}(AETHERIS_DB_PATH unset/missing){RESET}")
    )

    failures = 0

    # --- Check 1: no dead entries -------------------------------------------------
    for prefixes, group in entries:
        for p in prefixes:
            hits = [l for l in universe if l.lower().startswith(p)]
            if hits:
                print(f"{GREEN}[PASS]{RESET} prefix {p!r} → {group}: {len(hits)} label(s)")
            else:
                print(f"{RED}[FAIL]{RESET} prefix {p!r} → {group}: matches NO known label (dead entry)")
                failures += 1

    # --- Check 2: every declared agent label classifies ---------------------------
    stranded = sorted(l for l in expanded if classify(l, entries) == "Unclassified")
    if stranded:
        for l in stranded:
            print(f"{RED}[FAIL]{RESET} declared label {l!r} falls through to Unclassified")
        failures += len(stranded)
    else:
        print(f"{GREEN}[PASS]{RESET} all {len(expanded)} declared agent labels classify")

    # --- Informational: observed labels with no group -----------------------------
    if observed:
        loose = sorted(l for l in observed if classify(l, entries) == "Unclassified")
        print(
            f"{CYAN}[INFO]{RESET} {len(loose)} observed label(s) Unclassified "
            f"— expected for evals, smoke tests, forks and unlabelled runs"
        )

    print(f"\nSummary: {'FAIL' if failures else 'PASS'} ({failures} failure(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
