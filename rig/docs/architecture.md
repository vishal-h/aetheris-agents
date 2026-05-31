# Rig — Architecture

## Overview

Rig is a cross-platform desktop application built with Tauri v2. It is designed as a personal productivity host — a single binary that houses multiple unrelated tools (modules), each with its own data, UI, and logic, unified under a shared app shell.

The guiding principles are:

- **Offline-first** — the app runs fully without a network. Network calls are on-demand, user-initiated, and scoped to individual modules
- **No telemetry** — the binary never calls home. No analytics, no silent update checks
- **Single binary distribution** — one build artifact per OS, no installers required (AppImage on Linux)
- **Module isolation** — adding or removing a module does not affect others
- **Local data ownership** — all data lives in a local DuckDB file the user controls

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| App framework | Tauri v2 | Small binary, Rust backend, WebView frontend, cross-platform |
| Frontend language | TypeScript | Type safety, good tooling |
| Frontend framework | React 18 | Component model fits the module/host architecture |
| Styling | Tailwind CSS + shadcn/ui | Utility-first styling; shadcn provides sidebar, tabs, dialogs out of the box |
| Frontend build | Vite + Bun | Fast dev server, fast installs |
| Backend language | Rust | Required by Tauri; handles DB, HTTP, file I/O |
| Storage | DuckDB (via duckdb-rs) | Columnar storage; excellent for time-series and analytical queries (portfolio returns, price history, aggregations) |
| HTTP client | reqwest (async) | Standard Rust async HTTP; used for on-demand API calls |
| Serialization | serde + serde_json | Standard Rust JSON layer; bridges Rust ↔ TypeScript via Tauri commands |
| Icons | lucide-react | Consistent icon set |
| Routing | react-router-dom | Client-side navigation between modules and sub-views |

---

## Application Layers

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│   App Shell (TopBar, Sidebar, MainArea)              │
│   Module UIs  (Portfolio, ...)                       │
│   shadcn/ui components + Tailwind                    │
├──────────────────────────┬──────────────────────────┤
│     Tauri Bridge         │                          │
│  invoke() commands       │   Tauri Events           │
│  (request → response)    │   (backend → frontend)   │
├──────────────────────────┴──────────────────────────┤
│                   Rust Backend                       │
│   Command handlers  (src-tauri/src/commands/)        │
│   DuckDB layer      (src-tauri/src/db/)              │
│   HTTP client       (src-tauri/src/http/)            │
│   Module logic      (src-tauri/src/modules/)         │
└─────────────────────────────────────────────────────┘
         │                          │
    DuckDB file               External APIs
    (~/.rig/data.db)     (on-demand only)
```

### Frontend → Backend Communication

The React frontend never accesses the filesystem, database, or network directly. All such operations go through **Tauri commands**:

```typescript
// Frontend calls a named Rust function
const holdings = await invoke<Holding[]>('get_holdings', { portfolioId: 1 });
```

```rust
// Rust exposes it as a command
#[tauri::command]
async fn get_holdings(portfolio_id: i64, db: State<'_, DbPool>) -> Result<Vec<Holding>, String> {
    db.query_holdings(portfolio_id).await.map_err(|e| e.to_string())
}
```

This boundary is strict. The frontend is purely a view layer. Business logic, data access, and external calls all live in Rust.

---

## Module System

A module is a self-contained feature area. Each module owns:

- A **sidebar entry** (label, icon, optional nested children)
- One or more **main area views** (rendered in tabs or as a single view)
- An optional **right panel** view (contextual detail)
- Its own **DuckDB schema** (tables namespaced by module)
- Its own **Rust command handlers** (namespaced by module name)

### Module Registration

Modules are registered statically in two places:

**Frontend** — `src/modules/registry.ts`
```typescript
export const modules: Module[] = [
  portfolioModule,
  // add future modules here
];
```

**Backend** — `src-tauri/src/main.rs`
```rust
tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![
        portfolio::get_holdings,
        portfolio::add_transaction,
        // add future module commands here
    ])
```

There is no dynamic plugin loading. Modules are compiled in. Adding a module means adding code and registering it in these two places.

---

## Data Layer

### Database File Location

```
Linux:   ~/.local/share/rig/data.db
macOS:   ~/Library/Application Support/rig/data.db
Windows: C:\Users\<user>\AppData\Roaming\rig\data.db
```

Tauri provides `app_data_dir()` to resolve this path at runtime regardless of OS.

### Schema Strategy

Each module owns its tables, prefixed by module name:

```sql
-- Portfolio module tables
portfolio_holdings
portfolio_transactions
portfolio_price_history
portfolio_watchlists

-- Future module tables would follow the same convention
-- <module>_<table>
```

DuckDB is initialized on app start. Migrations are applied in order using a simple versioned migration table:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    version   INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT now()
);
```

### Why DuckDB Over SQLite

For portfolio data specifically:

- Price history is a time series — DuckDB's columnar storage handles range scans and aggregations significantly faster
- Common queries (rolling returns, portfolio value over time, gain/loss by sector) are analytical, not transactional
- DuckDB supports window functions, `ASOF` joins (for aligning prices to dates), and date arithmetic natively
- For simple CRUD (future modules that are just structured data), DuckDB handles that fine too — no need for a second database

---

## Network Layer

Network access is **module-scoped and on-demand only**.

- The app shell makes zero network calls
- Each module declares what API it needs
- Calls are triggered by explicit user actions (refresh button, opening a view that needs live data)
- API keys are stored in the local DuckDB settings table, never in code or environment files

### Portfolio — Finnhub API

The Portfolio module uses the [Finnhub API](https://finnhub.io) for:

- Current stock quotes (`/quote`)
- Historical OHLCV prices (`/stock/candle`)
- Company profile (`/stock/profile2`)
- Symbol search (`/search`)

Free tier: 60 requests/minute. Sufficient for personal use.

---

## App Shell Layout

```
┌─────────────────────────────────────────────────────────┐
│  [◉ Rig]        [Global Search]      [↻]  [⚙]     │  TopBar
├───────────────┬─────────────────────────────────────────┤
│               │  [Tab 1]  [Tab 2]  [Tab 3]              │
│  ▼ Portfolio  ├─────────────────────────────────────────┤
│    ├ Holdings │                              │           │
│    ├ Txns     │     Main Content Area        │  Right    │
│    └ Perf     │                              │  Panel    │
│               │                              │ (optional)│
│  ▼ Watchlist  │                              │           │
│               │                              │           │
│  ＋ Module    │                              │           │
└───────────────┴──────────────────────────────┴───────────┘
```

### TopBar responsibilities
- App identity (name/logo)
- Global search (deferred — post-MVP)
- Manual sync/refresh trigger
- Settings entry point

### Sidebar responsibilities
- Module navigation
- Nested sub-section navigation within a module
- Active state tracking
- Collapsible sections

### Main Area responsibilities
- Tabbed content per module/section
- Tab state is per-sidebar-selection (each sidebar item remembers its open tabs)

### Right Panel
- Optional, toggled per module
- Used for contextual detail (e.g., clicking a stock shows details without leaving the main view)
- Hidden when not applicable

---

## State Management

No external state library (no Redux). React's built-in tools are sufficient:

- `useState` / `useReducer` for local component state
- `useContext` for app-wide state: active module, sidebar selection, right panel visibility, settings
- Custom hooks wrap all `invoke()` calls (e.g., `useHoldings()`, `useQuote(symbol)`)

Data fetched from the backend is not cached in the frontend beyond the component lifecycle. DuckDB is the source of truth.

---

## Build and Distribution

### Development
```bash
cargo tauri dev   # Starts Vite dev server + Rust backend with hot reload
```

### Production Build
```bash
cargo tauri build
# Output: src-tauri/target/release/bundle/
#   linux:   appimage/rig_x.x.x_amd64.AppImage
#             deb/rig_x.x.x_amd64.deb
#   macos:   macos/Rig.app  +  dmg/
#   windows: msi/  +  nsis/
```

### Cross-platform Builds
Local builds only target the host OS. To produce all three binaries, use a CI matrix (GitHub Actions with ubuntu, macos, windows runners). Not needed during local development.

---

## Security Considerations

- Tauri's [Content Security Policy](https://tauri.app/security/csp/) is enabled — the WebView cannot make arbitrary network requests
- All network calls go through Rust command handlers, not the frontend
- No `eval()`, no arbitrary script execution
- API keys stored in local DuckDB, not in env files or frontend code
- `tauri.conf.json` explicitly allowlists which Tauri APIs the frontend can use

---

## Future Considerations

- **Backup/Restore** — export the DuckDB file, import it on another machine
- **Multiple portfolios** — schema supports it from day one via `portfolio_id`
- **Additional modules** — the module registry pattern keeps this additive and non-breaking
- **Global search** — deferred; would query across module-owned tables via a shared search interface