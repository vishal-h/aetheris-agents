# Rig — Runbook

## Platform

Ubuntu 22.04 LTS (upgraded from 20.04). These steps are specific to Ubuntu/Debian. The app itself is cross-platform but this runbook covers the development machine setup only.

---

## Part 1 — System Prerequisites

### Step 1 — System packages

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  build-essential \
  curl \
  wget \
  git \
  pkg-config \
  libssl-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  libwebkit2gtk-4.1-dev \
  libjavascriptcoregtk-4.1-dev \
  libsoup-3.0-dev
```

> **Note:** `libwebkit2gtk-4.1-dev` requires Ubuntu 22.04 or later. It is not available on Ubuntu 20.04. If you are on 20.04, upgrade first.

---

### Step 2 — Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
rustc --version   # should print rustc 1.x.x
```

---

### Step 3 — Node.js (via nvm)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
node --version   # should print v22.x.x
```

---

### Step 4 — Bun

```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
bun --version
```

---

### Step 5 — Tauri CLI

```bash
cargo install tauri-cli --version "^2"
cargo tauri --version   # should print tauri-cli x.x.x
```

> This step takes 3–5 minutes. It looks stuck — it isn't.

---

## Part 2 — Project Setup

### Step 6 — Clone the repo

```bash
git clone https://github.com/swiftekin/hai-rig.git
cd hai-rig
```

---

### Step 7 — Install frontend dependencies

```bash
bun install
```

---

### Step 8 — First build (slow — DuckDB compiles from source)

```bash
cd src-tauri
cargo build -j2
```

> **This takes 15–25 minutes on first run.** The `-j2` flag limits parallel jobs to 2 to avoid freezing the machine. DuckDB's `features = ["bundled"]` compiles the entire DuckDB C++ codebase from source. This only happens once — subsequent builds are fast (under 1 minute).
>
> If the machine freezes anyway, use **Alt+PrtScr+R-E-I-S-U-B** (hold Alt+PrtScr, press each letter with a pause between) for a safe reboot. Then retry with `-j1`.

```bash
cd ..
```

---

### Step 9 — First run

```bash
cargo tauri dev
```

The first run compiles the Rust backend and starts the Vite dev server. Expect 30–60 seconds. A window should open showing the Rig shell with the F2 module in the sidebar.

Subsequent runs are fast — frontend HMR is instant, Rust only recompiles changed files.

---

## Part 3 — Data

### Step 10 — Database location

The DuckDB file is created automatically on first run at:

```
Linux:   ~/.local/share/dev.rig.app/data.db    (dev mode)
         ~/.local/share/rig/data.db             (production build)
```

No manual setup required. Migrations run automatically on startup.

---

### Step 11 — Resetting the database

If you need to reset all data (e.g. after a migration change):

```bash
rm ~/.local/share/dev.rig.app/data.db
```

Then restart the app. Migrations will re-run from scratch.

---

### Step 12 — Adding a watched folder

1. Open Rig
2. Click the **Settings** gear icon in the top right
3. Under **Watched Folders**, type a folder path (e.g. `/home/you/documents`)
4. Click **Add**
5. Navigate to **F2 → Operations**
6. Click the **Sync** (↻) button in the top bar
7. Watch the terminal for scan progress logs
8. The **Index** tab will populate when the scan completes

---

## Part 3b — Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PROVENANCE_DB_PATH` | For Provenance module | Absolute path to the Aetheris corpus DuckDB file |
| `AETHERIS_DB_PATH` | For Harness module | Absolute path to `aetheris.db` (SQLite) — used for run inspection. Also used to derive `aetheris_dir` for the Orchestrator |
| `AETHERIS_AGENTS_PATH` | For Orchestrator module | Absolute path to the `aetheris-agents/` root directory |

Example for local dev:

```bash
export AETHERIS_DB_PATH=$(realpath ~/sandbox/elixirws/aetheris/priv/aetheris.db)
export AETHERIS_AGENTS_PATH=$(realpath ~/sandbox/elixirws/aetheris-agents)
export PROVENANCE_DB_PATH=$(realpath ~/sandbox/provenance-test/corpus.duckdb)
cargo tauri dev
```

> **Important:** Use `$(realpath ~/…)` or an absolute path — never a bare `~`. The `~`
> shorthand is expanded by the shell only when it appears as a standalone token. When
> assigned to an env var (`export FOO=~/bar`), the shell passes the literal string
> `~/bar` to the Rust process, which has no knowledge of `~`. Rust's `std::env::var`
> returns the literal value, so `rusqlite` tries to open a file literally named `~`
> and silently falls back to the app's local data DB. Use `$HOME/…` or `$(realpath …)`.

`aetheris_dir` (the working directory for the Mix orchestrator process) is derived automatically from `AETHERIS_DB_PATH`: parent of `priv/` → the aetheris repo root.

---

## Part 3c — Harness Module

The Harness module connects to `aetheris.db` and surfaces agent run history.
It requires `AETHERIS_DB_PATH` to be set (see Part 3b). It has four sidebar sections:

### Runs (`/harness`)

Displays runs grouped by use case. Groups are derived from run label prefixes:

| Group | Prefix |
|-------|--------|
| Payslip | `payslip` |
| Drive | `drive` |
| Email | `email` |
| API / Tenant | `api-tenant` |
| API / Gateway | `api-gateway` |
| Provenance | `provenance` |
| Capability Matrix | `cap-matrix` |
| Unclassified | *(no match)* |

Each group is collapsible and shows 10 runs by default with a **Show N more…** toggle.
The status filter (All / Running / Done / Failed / Paused) is applied before grouping —
empty groups disappear entirely.

Clicking a run selects it and switches to the **Events** tab. The **Trajectory** tab
is also enabled for the selected run. The Trajectory tab meta panel shows LLM calls,
input tokens, output tokens, and cost for instrumented runs. Runs before 2026-06-01
show `—` for token/cost fields.

### Diff (`/diff`)

Side-by-side comparison of two runs. Select Run A and Run B from the dropdowns,
click **Compare**. Differing metadata rows and step tool paths are highlighted.
The metadata table includes Input tokens, Output tokens, and Total cost rows;
these are highlighted when the values differ between Run A and Run B.

### Agents (`/capability-matrix`)

Browsable catalogue parsed from `docs/capability-matrix.md` in the agents repo.
Requires `AETHERIS_AGENTS_PATH` to be set. Organised by use case:

- **Agents** — filename, display label, tool badges. Click **Run** to navigate to
  the Orchestrator with `{agent label}: ` pre-filled in the request textarea.
- **Scripts** — readonly reference: filename and one-line purpose. No launch button.
  Scripts are called by agents, not run directly.

### Usage (`/usage`)

Aggregate token and cost statistics across all instrumented runs (runs after
the 2026-06-01 harness token/cost instrumentation). Requires `AETHERIS_DB_PATH`.

**Four summary cards:** Total spend, Total runs, Total tokens, Avg cost/run.

**By model table:** model (font-mono), runs, input tokens, output tokens, total
cost, avg cost per run — sorted by total cost descending.

**By use case table:** use case, runs, total cost — aggregated using the same
prefix logic as the run list (Payslip, Drive, Email, API / Tenant, API / Gateway,
Provenance, Capability Matrix, Unclassified).

A **Refresh** button reloads stats on demand. A pre-instrumentation note
appears when some runs predate the token/cost change. An empty state is shown
when no instrumented runs exist yet.

---

## Part 4 — Development Notes

### Hot reload

- **Frontend changes** (`.tsx`, `.ts`, `.css`): instant via Vite HMR — no restart needed
- **Rust changes** (`.rs`): Tauri detects the change and recompiles automatically — takes 5–30 seconds depending on what changed

### Checking logs

Rust logs appear in the terminal where `cargo tauri dev` is running. Log levels:
- `[INFO]` — normal operation
- `[WARN]` — non-fatal issues (e.g. file permission errors during scan, skipped and continued)
- `[ERROR]` — failures worth investigating

### Common issues

**`libwebkit2gtk-4.1-dev` not found**
You are on Ubuntu 20.04. Upgrade to 22.04.

**App window doesn't open / blank window**
Check the terminal for Rust panics. Most common cause: database migration failure. Reset the DB file (Step 11) and retry.

**Scan completes with 0 files**
The watched folder path doesn't exist or has no readable files. Check the `[WARN]` lines in the terminal for the specific error.

**`cargo build` freezes the machine**
Use `-j2` or `-j1` to limit parallelism. The DuckDB bundled compile is very CPU/memory intensive.

**Agents section shows error**
`AETHERIS_AGENTS_PATH` is not set, or `docs/capability-matrix.md` is missing from the agents root.
Fix: set `AETHERIS_AGENTS_PATH` to the absolute path of the `aetheris-agents/` directory, then
confirm the file exists at `$AETHERIS_AGENTS_PATH/docs/capability-matrix.md`.

**Usage shows $0.00 / no data**
All runs predate the token/cost instrumentation (landed 2026-06-01). Earlier runs have
`NULL` for `cost_usd`, `input_tokens`, and `output_tokens` in their `llm_responded` events
and are excluded from all aggregates.
Fix: run any agent against a real Anthropic model, then click **Refresh** in the Usage view.

**`@tauri-apps/api` import errors in Vite**
Run `bun install` — the package may not be installed yet.

---

## Part 5 — Production Build

```bash
cargo tauri build
```

Output in `src-tauri/target/release/bundle/`:
- `appimage/rig_x.x.x_amd64.AppImage`
- `deb/rig_x.x.x_amd64.deb`

The AppImage is self-contained — no installation required, just `chmod +x` and run.
