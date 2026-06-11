#!/usr/bin/env python3
"""
Deterministic doc-drift checker for Rig documentation.

Checks that docs/rig/specs.md, docs/rig/runbook.md, and related docs
stay in sync with Rust/TypeScript/Elixir source code.

Exit codes:
  0 — no FAIL findings
  1 — one or more FAIL findings

Checks:
  event_types      — event.ex @type vs specs.md §6
  tauri_commands   — lib.rs generate_handler! vs .rs files vs specs.md §4
  db_schema        — store.ex CREATE TABLE vs specs.md §2
  env_vars         — Rust env::var() calls vs specs.md §1 and runbook.md
  routes           — registry.ts paths vs App.tsx Route paths
  payload_fields   — live DB payload sampling vs specs.md §6 (skipped if DB absent)
  milestone_status — docs/rig/milestones/*/README.md has Status: line
"""

import argparse
import os
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Repo layout                                                                  #
# --------------------------------------------------------------------------- #

SCRIPT_DIR    = Path(__file__).parent.resolve()
REPO_ROOT     = SCRIPT_DIR.parent
HARNESS_ROOT  = REPO_ROOT.parent / "aetheris"
RIG_ROOT      = REPO_ROOT / "rig"

SPECS_MD      = REPO_ROOT / "docs" / "rig" / "specs.md"
RUNBOOK_MD    = REPO_ROOT / "docs" / "rig" / "runbook.md"
EVENT_EX      = HARNESS_ROOT / "lib" / "aetheris" / "trajectory" / "event.ex"
STORE_EX      = HARNESS_ROOT / "lib" / "aetheris" / "store.ex"
LIB_RS        = RIG_ROOT / "src-tauri" / "src" / "lib.rs"
COMMANDS_DIR  = RIG_ROOT / "src-tauri" / "src" / "commands"
RIG_SRC_TAURI = RIG_ROOT / "src-tauri" / "src"
REGISTRY_TS   = RIG_ROOT / "src" / "modules" / "registry.ts"
APP_TSX       = RIG_ROOT / "src" / "App.tsx"
MILESTONES_DIR = REPO_ROOT / "docs" / "rig" / "milestones"

# --------------------------------------------------------------------------- #
# Findings                                                                     #
# --------------------------------------------------------------------------- #

FINDINGS: list[tuple[str, str, str]] = []
_strict = False

_COLORS = {
    "FAIL": "\033[31m",
    "WARN": "\033[33m",
    "INFO": "\033[36m",
    "PASS": "\033[32m",
}
_RESET = "\033[0m"


def record(level: str, check: str, message: str) -> None:
    if level == "WARN" and _strict:
        level = "FAIL"
    FINDINGS.append((level, check, message))
    color = _COLORS.get(level, "")
    print(f"{color}[{level}]{_RESET} {check}: {message}")


def _fail(check, msg): record("FAIL", check, msg)
def _warn(check, msg): record("WARN", check, msg)
def _info(check, msg): record("INFO", check, msg)
def _ok(check, msg):   record("PASS", check, msg)


def _require_file(path: Path, check: str) -> str | None:
    if not path.exists():
        _fail(check, f"file not found: {path}")
        return None
    return path.read_text(encoding="utf-8")


def _require_section(text: str, pattern: str, check: str, anchor: str) -> re.Match | None:
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        _fail(check, f"anchor not found: {anchor!r}")
        return None
    return m

# --------------------------------------------------------------------------- #
# Check 1: event_types                                                         #
# --------------------------------------------------------------------------- #

def _parse_event_types_from_event_ex(text: str, check: str) -> set[str] | None:
    m = _require_section(
        text,
        r"@type event_type ::\s*(.*?)(?=\n\s*@|\Z)",
        check,
        "@type event_type ::",
    )
    if not m:
        return None
    types = re.findall(r":(\w+)", m.group(1))
    if not types:
        _fail(check, "zero event types parsed from @type event_type block")
        return None
    return set(types)


def _parse_event_types_from_specs(text: str, check: str) -> set[str] | None:
    m = _require_section(
        text,
        r"## 6\. Event Type Reference(.*?)(?=\n## |\Z)",
        check,
        "## 6. Event Type Reference",
    )
    if not m:
        return None
    # First column of each pipe-table row is the event type
    types = re.findall(r"^\| `(\w+)` \|", m.group(1), re.MULTILINE)
    if not types:
        _fail(check, "zero event types parsed from specs.md §6 table")
        return None
    return set(types)


def check_event_types() -> None:
    check = "event_types"
    src = _require_file(EVENT_EX, check)
    specs = _require_file(SPECS_MD, check)
    if src is None or specs is None:
        return

    code_types = _parse_event_types_from_event_ex(src, check)
    doc_types  = _parse_event_types_from_specs(specs, check)
    if code_types is None or doc_types is None:
        return

    for t in sorted(code_types - doc_types):
        _fail(check, f"{t!r} in event.ex but missing from specs.md §6")
    for t in sorted(doc_types - code_types):
        _fail(check, f"{t!r} in specs.md §6 but not in event.ex (ghost)")

    if not any(l == "FAIL" and c == check for l, c, _ in FINDINGS):
        _ok(check, f"{len(code_types)} event types match between event.ex and specs.md §6")

# --------------------------------------------------------------------------- #
# Check 2: tauri_commands                                                      #
# --------------------------------------------------------------------------- #

def _parse_commands_from_lib_rs(text: str, check: str) -> set[str] | None:
    m = _require_section(
        text,
        r"generate_handler!\[(.*?)\]",
        check,
        "generate_handler![...]",
    )
    if not m:
        return None
    # Qualified paths: commands::module::fn_name
    names = set(re.findall(r"commands::\w+::(\w+)", m.group(1)))
    if not names:
        _fail(check, "zero commands parsed from generate_handler! block")
        return None
    return names


def _parse_commands_from_command_files(commands_dir: Path) -> set[str]:
    result: set[str] = set()
    for rs_file in sorted(commands_dir.glob("*.rs")):
        text = rs_file.read_text(encoding="utf-8")
        for m in re.finditer(
            r"#\[tauri::command\]\s*\n\s*pub(?:\s+async)?\s+fn\s+(\w+)",
            text,
        ):
            result.add(m.group(1))
    return result


def _parse_commands_from_specs(text: str, check: str) -> set[str] | None:
    m = _require_section(
        text,
        r"## 4\. Tauri Command Shapes(.*?)(?=\n## |\Z)",
        check,
        "## 4. Tauri Command Shapes",
    )
    if not m:
        return None
    section = m.group(1)
    names: set[str] = set()
    # Bold-backtick blocks: **`command_name`**
    names.update(re.findall(r"\*\*`(\w+)`\*\*", section))
    # Table first column: | `command_name` |
    names.update(re.findall(r"^\| `(\w+)` \|", section, re.MULTILINE))
    # Keep only snake_case names (command names always have underscores)
    names = {n for n in names if "_" in n}
    if not names:
        _fail(check, "zero commands parsed from specs.md §4")
        return None
    return names


def check_tauri_commands() -> None:
    check = "tauri_commands"
    lib_text = _require_file(LIB_RS, check)
    specs_text = _require_file(SPECS_MD, check)
    if lib_text is None or specs_text is None:
        return

    lib_cmds  = _parse_commands_from_lib_rs(lib_text, check)
    file_cmds = _parse_commands_from_command_files(COMMANDS_DIR)
    doc_cmds  = _parse_commands_from_specs(specs_text, check)
    if lib_cmds is None or doc_cmds is None:
        return

    for n in sorted(file_cmds - lib_cmds):
        _warn(check, f"{n!r} has #[tauri::command] but is not in generate_handler!")
    for n in sorted(lib_cmds - doc_cmds):
        _warn(check, f"{n!r} is registered but not documented in specs.md §4")
    for n in sorted(doc_cmds - lib_cmds):
        _fail(check, f"{n!r} documented in specs.md §4 but not in generate_handler! (ghost)")

    if not any(l == "FAIL" and c == check for l, c, _ in FINDINGS):
        _ok(check, f"{len(lib_cmds)} commands checked: lib.rs / .rs files / specs.md §4")

# --------------------------------------------------------------------------- #
# Check 3: db_schema                                                           #
# --------------------------------------------------------------------------- #

def _extract_table_body(text: str, open_paren_pos: int) -> str:
    """Return the text between the opening '(' and its matching closing ')'.

    Uses paren-depth tracking so nested parens (REFERENCES, UNIQUE) don't
    truncate the body prematurely.
    """
    depth = 1
    i = open_paren_pos
    while i < len(text) and depth > 0:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    return text[open_paren_pos : i - 1]


def _extract_tables_from_sql(text: str) -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\(", text):
        name = m.group(1)
        body = _extract_table_body(text, m.end())
        cols = set(re.findall(r"^\s+([a-z_][a-z0-9_]*)\s+\S", body, re.MULTILINE))
        tables[name] = cols
    return tables


def _parse_tables_from_store_ex(text: str, check: str) -> dict[str, set[str]] | None:
    tables = _extract_tables_from_sql(text)
    if not tables:
        _fail(check, "zero CREATE TABLE blocks parsed from store.ex")
        return None
    for m in re.finditer(r"ALTER TABLE (\w+) ADD COLUMN (\w+)", text):
        t, col = m.group(1), m.group(2)
        if t in tables:
            tables[t].add(col)
    return tables


def _parse_tables_from_specs(text: str, check: str) -> dict[str, set[str]] | None:
    m = _require_section(
        text,
        r"## 2\. Harness DB Schema(.*?)(?=\n## |\Z)",
        check,
        "## 2. Harness DB Schema",
    )
    if not m:
        return None
    tables = _extract_tables_from_sql(m.group(1))
    if not tables:
        _fail(check, "zero CREATE TABLE blocks parsed from specs.md §2")
        return None
    return tables


def check_db_schema() -> None:
    check = "db_schema"
    store_text = _require_file(STORE_EX, check)
    specs_text = _require_file(SPECS_MD, check)
    if store_text is None or specs_text is None:
        return

    code_tables = _parse_tables_from_store_ex(store_text, check)
    doc_tables  = _parse_tables_from_specs(specs_text, check)
    if code_tables is None or doc_tables is None:
        return

    for table_name, doc_cols in doc_tables.items():
        if table_name not in code_tables:
            _fail(check, f"table {table_name!r} in specs.md §2 but not in store.ex")
            continue
        code_cols = code_tables[table_name]
        for col in sorted(doc_cols - code_cols):
            _fail(check, f"{table_name}.{col} in specs.md §2 but not in store.ex")
        for col in sorted(code_cols - doc_cols):
            _info(check, f"{table_name}.{col} in store.ex but not in specs.md §2")

    if not any(l == "FAIL" and c == check for l, c, _ in FINDINGS):
        _ok(check, f"{len(doc_tables)} documented tables match store.ex schema")

# --------------------------------------------------------------------------- #
# Check 4: env_vars                                                            #
# --------------------------------------------------------------------------- #

def _parse_env_vars_from_rust_text(text: str) -> set[str]:
    # SCREAMING_SNAKE_CASE with at least one underscore (project config vars)
    return set(re.findall(r'env::var\("([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)"\)', text))


def _parse_env_vars_from_rust(src_dir: Path, check: str) -> set[str]:
    result: set[str] = set()
    for rs_file in src_dir.rglob("*.rs"):
        result.update(_parse_env_vars_from_rust_text(rs_file.read_text(encoding="utf-8")))
    return result


def _parse_env_vars_from_doc(text: str, section_pattern: str, check: str, anchor: str) -> set[str] | None:
    m = _require_section(text, section_pattern, check, anchor)
    if not m:
        return None
    rows = re.findall(r"^\| `([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)` \|", m.group(0), re.MULTILINE)
    if not rows:
        _fail(check, f"zero env vars parsed from {anchor!r}")
        return None
    return set(rows)


def check_env_vars() -> None:
    check = "env_vars"
    specs_text   = _require_file(SPECS_MD, check)
    runbook_text = _require_file(RUNBOOK_MD, check)
    if specs_text is None or runbook_text is None:
        return

    code_vars    = _parse_env_vars_from_rust(RIG_SRC_TAURI, check)
    specs_vars   = _parse_env_vars_from_doc(
        specs_text,
        r"## 1\. Environment Variables(.*?)(?=\n## |\Z)",
        check,
        "## 1. Environment Variables",
    )
    runbook_vars = _parse_env_vars_from_doc(
        runbook_text,
        r"## Environment variables(.*?)(?=\n## |\Z)",
        check,
        "## Environment variables",
    )
    if specs_vars is None or runbook_vars is None:
        return

    for v in sorted(code_vars - specs_vars):
        _warn(check, f"{v!r} read by Rig Rust but not listed in specs.md §1")
    for v in sorted(specs_vars - runbook_vars):
        _warn(check, f"{v!r} in specs.md §1 but absent from runbook.md env table")
    # vars in specs but not in code — some are agent-side (INFO, not WARN)
    for v in sorted(specs_vars - code_vars):
        _info(check, f"{v!r} in specs.md §1 but not read via env::var() in Rig (may be agent-side)")

    if not any(l in ("FAIL", "WARN") and c == check for l, c, _ in FINDINGS):
        _ok(check, f"env vars consistent: {len(specs_vars)} in specs, {len(code_vars)} read in Rust")

# --------------------------------------------------------------------------- #
# Check 5: routes                                                              #
# --------------------------------------------------------------------------- #

# Routes present in App.tsx that are not required in registry.ts
_ROUTE_EXCEPTIONS = {"/", "/settings"}


def _parse_routes_from_registry(text: str, check: str) -> set[str] | None:
    paths = re.findall(r"path:\s*'([^']+)'", text)
    if not paths:
        _fail(check, "zero paths parsed from registry.ts")
        return None
    return set(paths)


def _parse_routes_from_app_tsx(text: str, check: str) -> set[str] | None:
    paths = re.findall(r'path="([^"]+)"', text)
    if not paths:
        _fail(check, "zero paths parsed from App.tsx")
        return None
    return set(paths) - _ROUTE_EXCEPTIONS


def check_routes() -> None:
    check = "routes"
    reg_text = _require_file(REGISTRY_TS, check)
    app_text = _require_file(APP_TSX, check)
    if reg_text is None or app_text is None:
        return

    registry_paths = _parse_routes_from_registry(reg_text, check)
    app_paths      = _parse_routes_from_app_tsx(app_text, check)
    if registry_paths is None or app_paths is None:
        return

    for p in sorted(registry_paths - app_paths):
        _fail(check, f"{p!r} in registry.ts but no matching Route in App.tsx")
    for p in sorted(app_paths - registry_paths):
        _warn(check, f"{p!r} in App.tsx but no matching entry in registry.ts")

    if not any(l == "FAIL" and c == check for l, c, _ in FINDINGS):
        _ok(check, f"{len(registry_paths)} registry paths all have matching App.tsx routes")

# --------------------------------------------------------------------------- #
# Check 6: payload_fields                                                      #
# --------------------------------------------------------------------------- #

def _parse_payload_fields_from_specs(text: str, check: str) -> dict[str, list[str]] | None:
    m = _require_section(
        text,
        r"## 6\. Event Type Reference(.*?)(?=\n## |\Z)",
        check,
        "## 6. Event Type Reference",
    )
    if not m:
        return None

    result: dict[str, list[str]] = {}
    for row in re.finditer(r"^\| `(\w+)` \| (.*?) \|$", m.group(1), re.MULTILINE):
        event_type  = row.group(1)
        fields_cell = row.group(2)
        # Strip enum values listed after " — " (e.g. `reason` — `done` | `failed`)
        fields_part = fields_cell.split(" — ")[0]
        fields = re.findall(r"`(\w+)`", fields_part)
        if fields:
            result[event_type] = fields

    if not result:
        _fail(check, "zero payload field rows parsed from specs.md §6 table")
        return None
    return result


def check_payload_fields() -> None:
    check = "payload_fields"

    db_path_str = os.environ.get("AETHERIS_DB_PATH")
    if not db_path_str:
        _warn(check, "AETHERIS_DB_PATH not set — skipping live payload sampling")
        return

    db_path = Path(db_path_str).expanduser()
    if not db_path.exists():
        _warn(check, f"AETHERIS_DB_PATH={db_path} not found — skipping")
        return

    specs_text = _require_file(SPECS_MD, check)
    if specs_text is None:
        return

    doc_fields = _parse_payload_fields_from_specs(specs_text, check)
    if doc_fields is None:
        return

    try:
        import sqlite3
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
    except Exception as e:
        _warn(check, f"could not open {db_path}: {e}")
        return

    try:
        for event_type, field_names in doc_fields.items():
            count = conn.execute(
                "SELECT COUNT(*) FROM events WHERE type = ?", (event_type,)
            ).fetchone()[0]
            if count == 0:
                _info(check, f"no {event_type!r} events in DB — cannot verify payload fields")
                continue

            # Use json_each to get all distinct payload keys across every event
            seen_keys: set[str] = {
                row[0]
                for row in conn.execute(
                    "SELECT DISTINCT je.key"
                    " FROM events e, json_each(e.payload_json) je"
                    " WHERE e.type = ?",
                    (event_type,),
                ).fetchall()
            }

            for field in field_names:
                if field not in seen_keys:
                    _fail(check, f"{event_type}.{field} in specs.md §6 but not seen in DB")
            for key in sorted(seen_keys - set(field_names)):
                _info(check, f"{event_type}.{key} in DB events but not listed in specs.md §6")
    finally:
        conn.close()

    if not any(l == "FAIL" and c == check for l, c, _ in FINDINGS):
        _ok(check, "sampled DB payload fields consistent with specs.md §6")

# --------------------------------------------------------------------------- #
# Check 7: milestone_status                                                    #
# --------------------------------------------------------------------------- #

def check_milestone_status() -> None:
    check = "milestone_status"

    if not MILESTONES_DIR.exists():
        _warn(check, f"milestones directory not found: {MILESTONES_DIR}")
        return

    milestone_dirs = sorted(d for d in MILESTONES_DIR.iterdir() if d.is_dir())
    if not milestone_dirs:
        _warn(check, "no milestone subdirectories found")
        return

    missing: list[str] = []
    for d in milestone_dirs:
        readme = d / "README.md"
        if not readme.exists():
            _warn(check, f"{d.name}/README.md not found")
            missing.append(d.name)
        elif "Status:" not in readme.read_text(encoding="utf-8"):
            _warn(check, f"{d.name}/README.md has no 'Status:' line")
            missing.append(d.name)

    if not missing:
        _ok(check, f"{len(milestone_dirs)} milestone READMEs all have Status: lines")

# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

CHECKS = [
    check_event_types,
    check_tauri_commands,
    check_db_schema,
    check_env_vars,
    check_routes,
    check_payload_fields,
    check_milestone_status,
]

_CHECK_NAMES = {fn.__name__.replace("check_", ""): fn for fn in CHECKS}


def main() -> int:
    global _strict

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="promote WARN to FAIL")
    parser.add_argument(
        "--check",
        action="append",
        metavar="NAME",
        choices=list(_CHECK_NAMES),
        help="run only this check (repeat for multiple)",
    )
    args = parser.parse_args()
    _strict = args.strict

    selected = [_CHECK_NAMES[n] for n in args.check] if args.check else CHECKS

    print(f"Rig doc-drift checker — {len(selected)} check(s)\n")
    for fn in selected:
        fn()

    fails  = sum(1 for l, _, _ in FINDINGS if l == "FAIL")
    warns  = sum(1 for l, _, _ in FINDINGS if l == "WARN")
    passes = sum(1 for l, _, _ in FINDINGS if l == "PASS")
    infos  = sum(1 for l, _, _ in FINDINGS if l == "INFO")

    print(f"\nSummary: {passes} PASS  {fails} FAIL  {warns} WARN  {infos} INFO")
    return 1 if fails > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
