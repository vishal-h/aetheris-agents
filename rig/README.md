# Rig

A personal desktop productivity host. One app, multiple tools. Built with Tauri, React, and DuckDB.

---

## What It Is

Rig is a cross-platform desktop application designed as a personal tool belt — a single binary that houses multiple unrelated utilities, each isolated but sharing a common shell.

It is not a SaaS product. There is no server, no account, no telemetry. Everything runs locally. Your data lives in a DuckDB file on your machine.

---

## Current Modules

| Module | Status | Description |
|---|---|---|
| Portfolio | 🚧 In progress | Stock portfolio tracking, transaction log, performance analytics |

---

## Design Philosophy

- **Offline-first** — works fully without internet. Network calls are on-demand and user-initiated
- **Local data** — all data stored in a local DuckDB file you own and can back up
- **No telemetry** — no analytics, no update checks, no background network activity
- **Modular** — each tool is isolated. Adding a new module does not affect existing ones
- **Single binary** — one file to download and run, per OS

---

## Tech Stack

| Layer | Technology |
|---|---|
| App framework | [Tauri v2](https://tauri.app) |
| Frontend | React 18 + TypeScript |
| Styling | Tailwind CSS + [shadcn/ui](https://ui.shadcn.com) |
| Storage | [DuckDB](https://duckdb.org) |
| Backend | Rust (via Tauri) |
| Build tool | Vite + Bun |

---

## Project Structure

```
rig/
├── src/                        # React frontend
│   ├── components/
│   │   ├── shell/              # TopBar, Sidebar, MainArea, RightPanel
│   │   └── modules/
│   │       └── portfolio/      # Holdings, Transactions, Performance, Watchlist
│   ├── context/                # App-wide React context (active module, settings)
│   ├── hooks/                  # Custom hooks wrapping Tauri invoke() calls
│   ├── modules/
│   │   └── registry.ts         # Module registration for the frontend
│   ├── App.tsx
│   └── main.tsx
│
├── src-tauri/                  # Rust backend
│   ├── src/
│   │   ├── main.rs             # Tauri app entry point + command registration
│   │   ├── commands/           # Tauri command handlers (frontend-callable functions)
│   │   │   └── portfolio.rs
│   │   ├── db/                 # DuckDB connection, migrations
│   │   │   ├── mod.rs
│   │   │   └── migrations/
│   │   ├── http/               # reqwest HTTP client wrappers
│   │   └── modules/
│   │       └── portfolio/      # Portfolio business logic
│   └── Cargo.toml
│
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── ARCHITECTURE.md
├── SPECS.md
└── RUNBOOK.md
```

---

## Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Tech stack decisions, system design, data layer, module system |
| [SPECS.md](./SPECS.md) | Feature specifications for the app shell and each module |
| [RUNBOOK.md](./RUNBOOK.md) | Step-by-step setup, development, and build instructions |

---

## Status

Early development. Not ready for use.

Platform target: Linux first, then macOS and Windows.

---

## Data Location

```
Linux:   ~/.local/share/rig/data.db
macOS:   ~/Library/Application Support/rig/data.db
Windows: C:\Users\<user>\AppData\Roaming\rig\data.db
```

You can back up your data by copying this file. You can restore it by replacing the file before launching the app.

---

## Development

See [RUNBOOK.md](./RUNBOOK.md) for full setup instructions.

Quick start (assumes prerequisites are installed):

```bash
git clone <repo>
cd rig
bun install
cargo tauri dev
```

---

## License

Personal use. Not licensed for redistribution.