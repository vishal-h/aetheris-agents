# provenance/m1: Extract f2-scanner into standalone CLI binary

## Context

The file scanner currently lives inside a Tauri desktop application. It depends on
`AppHandle` and `Emitter` for progress reporting, which means it cannot be run
headlessly by Aetheris via `run_command`. Aetheris drives all agent work on the
server — the scanner must be callable as a standalone binary.

The Tauri app will continue to exist as a reporting dashboard, but it will read from
DuckDB rather than driving the scan itself.


>[!NOTE]
>Starting point: copied from `hai-rig/src-tauri/src/modules/f2/` and `hai-rig/src-tauri/src/db/`. 
>Refactor to remove Tauri dependencies rather than rewriting from scratch.

## What to build

Extract the core scanning logic from the Tauri app into a standalone Rust binary:
`aetheris-agents/provenance/scanner/` (separate Cargo project).

**Remove:**
- `tauri::AppHandle` parameter from `scan_directory`
- `app_handle.emit(...)` progress event calls
- All `tauri` dependencies from `Cargo.toml`

**Replace progress emission with DuckDB writes:**
- `scan_runs` table tracks scan progress (see specs.md schema)
- Every 50 files: update `scan_runs` row with current `files_scanned`, `duplicates_found`
- On completion: set `status = 'complete'`, `finished_at = now()`

**CLI interface:**
```
f2-scanner scan --root <PATH> --db <PATH> [--ignore <GLOB>]... [--run-id <ID>]
f2-scanner resume --run-id <ID> --db <PATH>
f2-scanner status --db <PATH>
```

On completion, write one JSON line to stdout:
```json
{"run_id": "...", "status": "complete", "files_scanned": N, "duplicates_found": N, "duration_ms": N}
```

Exit 0 on success, exit 1 on error (error message to stderr).

**Keep unchanged:**
- `compute_sha256` (streaming 64KB chunks)
- `process_file` (cache hit logic, upsert)
- `should_ignore` / `estimate_file_count`
- `mark_missing_files`
- `update_duplicate_statuses`
- `check_cpu_and_throttle`
- All DuckDB schema and upsert logic

## Acceptance criteria

- [ ] `cargo build --release` succeeds with no Tauri dependencies
- [ ] `f2-scanner scan --root . --db /tmp/test.duckdb` completes on a local directory
- [ ] `scan_runs` table populated with correct counts and timestamps on completion
- [ ] Progress updates written to `scan_runs` every 50 files
- [ ] JSON completion line written to stdout
- [ ] Exit code 0 on success, 1 on error
- [ ] `f2-scanner` binary added to exec server permitted commands list in `aetheris_exec_server`
- [ ] `Cargo.lock` committed

## Files to create/modify

- `aetheris-agents/provenance/scanner/Cargo.toml`
- `aetheris-agents/provenance/scanner/Cargo.lock`
- `aetheris-agents/provenance/scanner/src/main.rs`
- `aetheris-agents/provenance/scanner/src/scan.rs` (extracted from Tauri)
- `native/aetheris_exec_server/src/main.rs` (add f2-scanner to permitted commands)

## Notes

The `scan_runs` schema is in `docs/provenance/specs.md`. Create the table if it
does not exist on startup (`CREATE TABLE IF NOT EXISTS`).

Follow Rust conventions already established in `native/aetheris_worker/`.
No Rustler — this is a standalone binary, not a NIF.
