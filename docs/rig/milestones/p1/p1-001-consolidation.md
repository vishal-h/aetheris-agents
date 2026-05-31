# rig/p1: Repo consolidation

## Context

Rig is the Tauri desktop app that was previously a standalone repo (`hai-rig`).
It moves to `aetheris-agents/rig/` so the UI and the agents that it monitors
live in the same repo.

This is the foundation issue — all subsequent p1 work happens in the new location.

## What to do

**Claude Code should run in `aetheris-agents/` for this issue.**

### Step 1 — Copy hai-rig contents

```bash
# From aetheris-agents/ root:
cp -r ../hai-rig/. rig/
```

Copy everything from `hai-rig/` into a new `rig/` directory at the
`aetheris-agents/` root. Include all files: `src/`, `src-tauri/`,
`CLAUDE.md`, `package.json`, `index.html`, etc.

### Step 2 — Update CLAUDE.md

The `rig/CLAUDE.md` needs these updates:

**Add at the top, after the title:**

```
## Location

This app lives at `aetheris-agents/rig/`. The aetheris harness repo is
at `../aetheris/` (sibling directory). Claude Code must run from
`aetheris-agents/rig/` for all Rig work.
```

**Add a new section — Harness DB:**

```
## Harness DB (aetheris.db)

Rig reads the harness SQLite database at `AETHERIS_DB_PATH` for run
inspection features. Uses `rusqlite` with `bundled` feature.

Connection opened read-only at startup in `HarnessState`:

  pub struct HarnessState {
      pub conn: Option<Arc<Mutex<rusqlite::Connection>>>,
      pub path: Option<String>,
  }

If `AETHERIS_DB_PATH` is absent, `conn` is None and all harness commands
return Err("harness not connected").

**Never write to aetheris.db.** Open with SQLITE_OPEN_READ_ONLY always.

SQLite timestamp columns are TEXT in ISO 8601 format — no casting needed
(unlike DuckDB's TIMESTAMP type).
```

**Add `rusqlite` to the DuckDB gotchas section header:**

Rename "DuckDB gotchas" to "Database gotchas" and note that SQLite and
DuckDB have different type systems — do not mix up casting rules between them.

### Step 3 — Add rusqlite to Cargo.toml

In `rig/src-tauri/Cargo.toml`, add:

```toml
rusqlite = { version = "0.31", features = ["bundled"] }
```

### Step 4 — Confirm it builds

```bash
cd rig
cargo build 2>&1 | tail -20
```

Fix any compilation errors from the new dependency. The app does not need
to start — just compile cleanly.

### Step 5 — Update .gitignore if needed

Ensure `rig/src-tauri/target/` is gitignored. Check `aetheris-agents/.gitignore`:

```
rig/src-tauri/target/
rig/node_modules/
```

Add if not present.

## Acceptance criteria

- [ ] `rig/` directory exists in `aetheris-agents/` with all Tauri app files
- [ ] `rig/CLAUDE.md` updated with location note and HarnessDB section
- [ ] `rusqlite` added to `rig/src-tauri/Cargo.toml` with `bundled` feature
- [ ] `cargo build` from `rig/src-tauri/` exits 0
- [ ] `.gitignore` covers `rig/src-tauri/target/` and `rig/node_modules/`
- [ ] No changes to `aetheris/` repo required

## Notes

**Do not run `cargo tauri dev` yet** — the full app requires environment
variables and a running Aetheris DB that may not be available in the
build environment. `cargo build` is sufficient for this issue.

**`hai-rig` stays intact.** Do not delete or modify the original `hai-rig`
repo. The copy in `aetheris-agents/rig/` is the new home; `hai-rig` is
retired but kept for reference until p1 is fully validated.

**`rusqlite` bundled feature** compiles SQLite from source — no system
SQLite required. This ensures the binary works on any target platform.
Build time increases by ~30 seconds on first compile.
