# Rig — Runbook

---

## Environment variables

| Variable | Required | Description |
|----------|---------|-------------|
| `AETHERIS_DB_PATH` | Yes (harness features) | Absolute path to `aetheris/priv/aetheris.db` |
| `AETHERIS_AGENTS_PATH` | Yes (tools features) | Absolute path to `aetheris-agents/` root |
| `AETHERIS_PROVIDER` | No | Default LLM provider for agents (`anthropic`); not read by Rig itself |
| `AETHERIS_API_URL` | Yes (playground features) | Base URL of the running aetheris harness API (e.g. `http://localhost:4001`) |
| `AETHERIS_API_TOKEN` | Yes (playground features) | Bearer token — must match one entry in `AETHERIS_PLAYGROUND_TOKENS` on the harness side |
| `PROVENANCE_DB_PATH` | Yes (Provenance features) | Absolute path to corpus DuckDB |
| `CORPUS_SEARCH_MCP_ENABLED` | No | Set `true` to enable corpus-search MCP |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | No (GitHub MCP) | PAT for GitHub MCP server — or set in Rig Settings |
| `DOCBUILDER_TENANT` | No (Docbuilder) | p9 — docbuilder tenant (e.g. `bitloka`); set in Rig Settings → "Docbuilder", injected when spawning agents and passed to the chain script. Not read by Rig itself |

---

## Development

```bash
cd aetheris-agents/rig

# Set env vars
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb      # optional
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...                             # optional, or set in Settings
export AETHERIS_API_URL=http://localhost:4001  # optional: enables Playground module
export AETHERIS_API_TOKEN=tok-abc              # optional: see Playground module section

# Start dev server
cargo tauri dev
```

All env vars except `AETHERIS_DB_PATH` are optional at startup —
Rig renders "not connected" placeholders for features that require them.

---

## Building

```bash
cd aetheris-agents/rig
cargo tauri build
```

Output binary: `src-tauri/target/release/bundle/`

---

## Running against the test sandbox

```bash
# Create/reset the test sandbox
python3 provenance/scripts/create_test_sandbox.py --overwrite

# Run the scan orchestrator to populate aetheris.db and corpus.duckdb
export PROVENANCE_NAS_PATH=~/sandbox/provenance-test/archive
export PROVENANCE_DB_PATH=~/sandbox/provenance-test/corpus.duckdb
cd ~/sandbox/elixirws/aetheris
mix aetheris run ../aetheris-agents/provenance/agents/scan_orchestrator.exs

# Open Rig
cd ~/sandbox/elixirws/aetheris-agents/rig
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
cargo tauri dev
```

---

## Harness module — Run inspection

The Harness module shows all agent runs recorded in `aetheris.db`.

### What you see

**Run list tab:**
- Label, status badge, model, started at, duration, steps
- Click any row to open the event log for that run
- Refresh button — no auto-refresh

**Event log tab:**
- All events for the selected run, ordered by seq
- Step number, event type, timestamp, payload preview
- Colour coding by event type

### Status badges

| Status | Colour | Notes |
|--------|--------|-------|
| `done` | Green | |
| `running` | Amber | pulsing "Live" indicator while events are streaming |
| `running` + "stalled?" | Amber + amber text | no events for >5 min; process may have died |
| `failed` | Red | |
| `paused` | Blue | |
| `idle` | Grey | |

### Not connected

If `AETHERIS_DB_PATH` is not set or the file doesn't exist, the Harness
tab shows a "Not connected" placeholder with the path to set.

---

## Tools module — Script and MCP browser

The Tools module browses scripts, harness tools, and MCP tools.
Requires `AETHERIS_AGENTS_PATH` to be set.

### What you see

**Left panel — tree:**
- Use-case groups (collapsible) — scripts from `tools.json` manifests
- Undeclared scripts (amber `!`) — `.py` files not in `tools.json`
- Harness section — 8 built-in tools, read-only
- MCP section — per server, collapsible, only shown when servers respond

**Right panel — detail:**
- Scripts: description, arg form, example command (click to copy), Run button
- Harness tools: description + args, read-only
- MCP tools: description, collapsible input schema, Try panel

### Try panel (MCP tools)

- JSON textarea pre-populated with required fields skeleton
- Run invokes the tool via stdio/HTTP and shows the response
- `ok` / `error` badge + pretty-printed JSON response

### MCP section not appearing

The MCP section is hidden when all servers return empty tool lists.
Common causes:
1. `GITHUB_PERSONAL_ACCESS_TOKEN` not set — set in Rig Settings or export before launch
2. `github-mcp-server` not on PATH — install: `go install github.com/github/github-mcp-server@latest`
3. Token expired or insufficient scopes — needs `repo` scope

Test the binary directly:
```bash
(
  echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"rig","version":"0.1.0"}}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
  sleep 0.5
  echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
  sleep 2
) | GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN \
    github-mcp-server stdio 2>/dev/null
```

Should return a JSON line with 43 tools.

### Adding a new MCP server

1. Add entry to `aetheris-agents/mcp/mcp_servers.json`
2. If auth needed, add key to `agentConfigDefs.ts` (Settings → new group)
3. Restart Rig — server appears in Tools panel automatically

### Adding a tools.json manifest

Place at `{use_case}/tools.json` in `aetheris-agents/`. See
`docs/rig/milestones/p4-tools/p4-001-manifest-spec.md` for full schema.
Minimum viable entry:

```json
{
  "manifest_version": "1",
  "use_case": "my_use_case",
  "description": "What this use case does",
  "scripts": []
}
```

Undeclared scripts (`.py` files without a manifest entry) appear with
an amber warning badge. Add them to `tools.json` to get structured
arg forms and output formatting.

---

## Agent config — Settings

Agent config is stored at:
```
~/.local/share/dev.rig.app/agent-config.json   # Linux
~/Library/Application Support/dev.rig.app/agent-config.json  # macOS
```

Values are injected as env vars when the Orchestrator spawns agents.
To add a new config key: add one line to `agentConfigDefs.ts` — the
row appears automatically in Settings. See `agent-config-reference.md`
for full documentation.

Current groups: Harness, Anthropic, SMTP, Google Drive, Payslip, GitHub.

---

## Provenance module

See `docs/provenance/runbook.md` for full Provenance documentation.

Quick reference:
- Corpus overview: `PROVENANCE_DB_PATH` must be set
- Classification review: approve/reject proposed classifications
- Migration status: progress by client
- Zip inventory: processed/encrypted/pending counts

---

## Playground module — Run Composer

The Playground module lets Rig users submit agent runs to a running aetheris
harness API without needing repo access or a local Elixir environment.

### Enabling the harness API

Set in aetheris `config/runtime.exs`:

```elixir
config :aetheris, api_enabled: true
config :aetheris, api_port: 4001
config :aetheris, api_bind: {127, 0, 0, 1}   # default: localhost only
```

`api_bind` defaults to localhost. Binding all interfaces (`{0, 0, 0, 0}`) is an
explicit opt-in; see Trust model section below.

### Generating a token

Add to aetheris config:

```elixir
config :aetheris, :playground_tokens, ["your-token-here"]
```

Or via env: `AETHERIS_PLAYGROUND_TOKENS=your-token-here` (comma-separated for
multiple). Set `AETHERIS_API_TOKEN` in Rig's env to the same value.

### Matching env var example

```bash
# Harness side
AETHERIS_PLAYGROUND_TOKENS=tok-abc ./scripts/run_server.sh

# Rig side
AETHERIS_API_URL=http://localhost:4001
AETHERIS_API_TOKEN=tok-abc
cargo tauri dev
```

### Starting Rig against the playground API

With the harness API running, start Rig with the two additional env vars:

```bash
cd ~/sandbox/elixirws/aetheris-agents/rig

export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
export AETHERIS_API_URL=http://localhost:4001
export AETHERIS_API_TOKEN=tok-abc   # must match AETHERIS_PLAYGROUND_TOKENS

cargo tauri dev
```

The Playground sidebar entry (FlaskConical icon) appears once Rig starts.
The Composer form is shown only when the connection gate passes — if it shows
"not connected", check that both `AETHERIS_API_URL` and `AETHERIS_API_TOKEN`
are set and that the harness is listening (`curl -s http://localhost:4001/api/playground/policy -H "Authorization: Bearer tok-abc"`).

**Full e2e flow:**
1. Fill in provider, model, sandbox, system prompt in the Composer form.
2. Submit — the returned `run_id` appears with a "Check status" button.
3. Click "Check status" to poll on demand (no background polling).
4. Switch to **Harness → Runs** to see the run in RunList and open its trajectory.

**Violation testing:** Submit with `max_steps` above the policy cap — the
Composer renders each violation's field and message as a structured list, not
a raw error string.

**MRU:** Recent submissions persist in localStorage across restarts. The list
appears below the form after the first submission.

### Exposing beyond localhost (reverse proxy)

Change `api_bind: {0, 0, 0, 0}` or a specific IP for VPN/private interface.
Note: once `api_bind` is opened, `GET /api/runs/*` endpoints leak run labels and
timing — operators on shared networks may wish to front them with proxy auth.

### Trust model — `run_command` and secrets

- `run_command` is not in the default playground allowlist. Enabling it grants
  shell-equivalent access to all bearer token holders — they can execute arbitrary
  commands with the harness process's UID.
- If `run_command` is enabled, or if `openrouter` is in the provider allowlist, the
  harness startup environment must not contain `ANTHROPIC_API_KEY`,
  `OPENROUTER_API_KEY`, or other secrets accessible to playground token holders.
  Use a dedicated harness process with a scoped environment.
- Playground tokens that enable `run_command` are equivalent to SSH keys — issue
  only to fully-trusted team members and rotate on personnel changes.

### Reverse proxy note

Behind a reverse proxy, `conn.remote_ip` in auth-rejection logs is the proxy's
address, not the client's. `X-Forwarded-For` must not be naively trusted without
explicit trusted-proxy configuration (deferred to p3).

### Overlay retention

Per-run overlay upper directories are not automatically cleaned up (tracked: issue
#84). Retention and cleanup tooling is planned for p3.

### Overlay isolation is Linux-only

The overlay mechanism uses `libc::mount` + user namespaces. On non-Linux hosts the
worker fails open and writes reach the real sandbox path. Production deployments
should run on Linux.

---

## Docbuilder module — natural-language document build (p9)

Sidebar entry **Docbuilder** (FileText icon, route `/docbuilder`). Turns a
natural-language request into a rendered, branded document via the chained docbuilder
flow, without the terminal.

### Setup

Set **`DOCBUILDER_TENANT`** in Settings → "Docbuilder" group (e.g. `bitloka`). The panel
shows the configured tenant and disables Run with a Settings link if it is unset.

### What you do

1. Type a request — e.g. `Invoice for XYZ for June 2026, same as last month`.
2. Run. The panel runs `docbuilder/scripts/chain_docbuilder.py` **top-level** (via the
   `.py` heuristic in `orchestrate_start`) with `--tenant`/`--request` and `--protocol`.
   This is one-click — there is no plan-approval gate.
3. The phase lifecycle renders from the script's emitted protocol: planning → a two-step
   plan (context builder, then orchestrator) → steps update live → done.
4. On completion, the rendered file list is read from `docbuilder/output/renamed.json`
   (via `tools_read_script`). A failed step shows "Completed with errors".

### Why a script, not an agent

The chain can't be a wrapping Aetheris agent: a nested `mix aetheris run` fails (the inner
run re-copies the worker binary the outer run holds open → "text file busy"), and
`run_command` can't set per-step env (no `env` field; `sh`/`bash` are blocked by the
exec-server allowlist). Run top-level, `chain_docbuilder.py` runs the two `mix aetheris run`
sub-agents **sequentially** — each frees the worker binary before the next.

### Inspecting the sub-runs

The chain produces **two** Aetheris runs (context builder, orchestrator), each with its own
`run_id` and trajectory — inspect them separately in the Harness module (or
`mix aetheris inspect <run_id>`). PHASE D2 of the orchestrator appends the run to
`data/run_log.json`, which feeds the next "same as last month".

---

## Common issues

### Harness tab shows "Not connected"

**Fix:** Set `AETHERIS_DB_PATH` to the absolute path of `aetheris.db` and
restart:
```bash
export AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db
```

### Run list is empty

`aetheris.db` exists but has no runs — no agents have been run yet.
Run any agent via `mix aetheris run` and refresh.

### Events table shows no events for a run

The run was recorded but the harness may have crashed before persisting
events. Check `mix aetheris inspect <run_id>` for details.

### Tools panel shows no use cases

`AETHERIS_AGENTS_PATH` is not set. Set it and restart:
```bash
export AETHERIS_AGENTS_PATH=~/sandbox/elixirws/aetheris-agents
```

### Run list shows "stalled?" next to a running badge

A run is flagged "stalled?" when `status = 'running'` in the DB but no events
have arrived for more than 5 minutes. This means the `mix` process likely died
mid-run and the harness did not get a chance to update the status.

**Verify:** `mix aetheris inspect <run_id>` — if the last event is old and no
new events arrive, the process is dead.

**Rig's badge is display-only** — it never writes to the DB. The **cure** lives
in the harness: the orphan sweep (`Aetheris.Sweep`). It runs automatically on
harness start (after checkpoint resume) and on demand via `mix aetheris sweep`.
For each `running` row whose owning process is gone and whose last event is older
than the liveness threshold, it:

- **orphaned** (no terminal event) → marks the run `failed` and appends a
  `run_orphaned` event; `finished_at` is stamped from the run's last-event
  timestamp (or `started_at` if it has no events), never the sweep time;
- **reconcilable** (trajectory already ends in `run_complete`/`error`) → adopts
  that recorded outcome (`done`/`failed`) and stamps `finished_at` from the
  terminal event; it appends **no** new event.

To cure a stalled run now: `mix aetheris sweep` (prints a summary of the actions
taken). See specs.md §6 for the `run_orphaned` event and its status mapping.

**Distinguish from paused runs:** a run in `wait_for_event` state is paused
legitimately — it will also show no new events, but `mix aetheris inspect`
will show a `agent_waiting` event as the latest. The sweep leaves these alone:
a run whose latest event is `agent_waiting` and whose `run_checkpoints` row is
`waiting` with an unexpired wait is skipped, not swept.

**Sweep configuration (harness `config :aetheris`):**

```elixir
# How old a running row's last event must be before it is considered dead.
# 5 min mirrors the "stalled?" display threshold above, so the cure fires
# exactly when the badge warns. Lower it (e.g. in a done-check) to sweep a
# just-killed run without waiting.
config :aetheris, :sweep_liveness_threshold_ms, 300_000

# Whether the sweep runs automatically on harness start (after checkpoint
# resume). Set false to cure only on demand via `mix aetheris sweep`.
config :aetheris, :sweep_on_start, true
```

### Trajectory tab shows a "reconstructed from events" banner

`trajectory.json` is written atomically only at clean run end, so it does
not exist while a run is live, and never exists for runs swept from orphaned
state (see "stalled?" above — the sweep marks them `failed` without writing a
file). Rather than erroring, the Trajectory tab **falls back to the live event
stream** (`harness_get_events` + `runs.config_json`) and renders the same
step-grouped view with a banner naming the source (BL-005):

- **`live — reconstructed from events`** — a `running` run. The view polls and
  appends new events until `run_complete` arrives (the same p2 polling used by
  the Events tab). It does **not** auto-switch to the file when the run
  finishes; reopen the run (or reselect it) to load the file-backed view.
- **`trajectory file unavailable — reconstructed from events`** — a terminal run
  whose file could not be read: either **absent** (typically a swept orphan) or
  **unreadable** (a corrupt file, or a truncated `.tmp` from an interrupted
  write — see below). Either way the DB events are complete. The wording is
  deliberately generic; the actual `trajectory_load` error is logged to the
  browser console (`[TrajectoryView] trajectory_load failed …`) so the
  interrupted-write signal is not lost behind the banner.

Fidelity is identical to the file: both stores hold complete, untruncated
payloads. The only meta fields unavailable pre-completion are those with no
live source (e.g. `overlay_changes`); everything else is derived from
`config_json` and the run row. The **Export JSON** button is hidden in
reconstructed mode (there is no readable file to copy).

### Trajectory tab shows "read failed" or blank

Reached only when **both** the trajectory file and the DB event stream are
unavailable — otherwise the fallback above renders instead.

The trajectory file is written atomically at run completion. If the run
finished too recently (< 1s) or the harness crashed mid-write, the file
may be absent or truncated.

**Check:** `ls -la ~/sandbox/elixirws/aetheris/priv/runs/<run_id>/` — the
file should be `trajectory.json`, not `trajectory.json.tmp`.

**If `.tmp` exists**, the write was interrupted. The `.tmp` file is partial
and cannot be recovered — the run data is still in `aetheris.db` (Events tab,
or the reconstructed Trajectory view once events exist).

**If the file exists** but Rig reports a read error, check
`AETHERIS_DB_PATH` — `trajectory.rs` derives the run directory from it;
a wrong path will produce a misleading error.

### MCP Try panel returns initialize response instead of tool result

This was a bug fixed in p4-006. If seen again, check that
`parse_tool_call_response` filters by `id == MCP_SESSION_REQUEST_ID` (99).

### cargo tauri dev fails to compile

Ensure Rust toolchain is up to date:
```bash
rustup update
```

Check that `rusqlite` feature flags in `Cargo.toml` include `bundled`:
```toml
rusqlite = { version = "...", features = ["bundled"] }
```

---

## Docbuilder use case

Run the docbuilder pipeline (data → formatted document) via sprint or direct.

### Required env vars (m2b)

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCBUILDER_TENANT` | Tenant subtree (`data/templates/{tenant}/` locally, or the Drive subtree) | `demo` |
| `DOCBUILDER_CONTEXT` | The single input blob — inline JSON of all run fields (see `docbuilder/docs/context-schema.md`). Required: `title`, `client_name`, `client_email`, `date`; optional `doc_type` (Option A) | `{"title":"…","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}` |

> **Retired in m2b:** `DOCBUILDER_DOC_TYPE`, `DOCBUILDER_VERSION`, `DOCBUILDER_DATA_PATH`
> (m1/m2a). The doc type/variant now come from `DOCBUILDER_CONTEXT` + the catalogue (LLM
> selection); data-source paths come from the template.

Optional — delivery (each PHASE skips when its var is absent):

| Variable | Description |
|----------|-------------|
| `DRIVE_DOCBUILDER_ID` | `docbuilder` Shared Drive root id → PHASE E uploads to `{tenant}/output/` and `list_templates`/`fetch_template` read from Drive |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Service-account JSON for Drive auth (falls back to legacy `GOOGLE_SERVICE_ACCOUNT`) |
| `DOCBUILDER_REVIEW_EMAIL` + `SMTP_*` | Review alias + SMTP creds → PHASE F emails the review |

### Sprint invocation

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_CONTEXT='{"title":"B2B Proposal","client_name":"Acme Corp","client_email":"ops@acme.example","date":"2026-06-20"}' \
./scripts/sprint.sh docbuilder
# add DRIVE_DOCBUILDER_ID / GOOGLE_SERVICE_ACCOUNT_FILE / DOCBUILDER_REVIEW_EMAIL / SMTP_*
# to exercise PHASE E (upload) and PHASE F (email).
```

### m2b pipeline behaviour

- **PHASE 0 — selection:** `list_templates.py` → LLM picks `{doc_type, variant}` → `fetch_template.py` downloads the bundle (Drive cache, or committed local nested bundle in dev).
- **PHASE A–C:** multi-source fetch (one raw JSON per source; template paths with the leading `docbuilder/` stripped), compute, render (xlsx/docx base files + narrative PDF), against the fetched bundle.
- **PHASE D — rename:** outputs → `{client_name_slug}_{doc_type}_{date}.{ext}`.
- **PHASE E/F (conditional):** upload to Drive / email the review alias — skipped with a notice when their creds are absent (dev verifies PHASE 0–D).
- **PHASE D2 (m3):** after rename, `run_log_writer.py` appends the run to `data/run_log.json` (gitignored) — the history the context builder reads for "same as last month".

### m3 — context builder ("same as last month")

A conversational agent (`context_builder.exs`) turns a natural-language request into a
`DOCBUILDER_CONTEXT` and hands off to the orchestrator. Single-shot gate: it always
writes the context file and emits a "PROPOSED DOCBUILDER_CONTEXT" block; the operator
reviews the trajectory before the orchestrator renders.

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCBUILDER_REQUEST` | The natural-language request for `context_builder.exs` | `Invoice for XYZ for June 2026, same as last month` |
| `DOCBUILDER_CONTEXT_FILE` | Orchestrator: path to the confirmed-context file to read when `DOCBUILDER_CONTEXT` is unset. Default `output/confirmed_context.json` | `/abs/path/output/confirmed_context.json` |

- **Context source precedence (orchestrator):** `DOCBUILDER_CONTEXT` env var (non-empty)
  > `DOCBUILDER_CONTEXT_FILE` (or the default `output/confirmed_context.json`) > `{}`.
  Env-var-wins protects legacy/direct runs from a stale file; the NL flow leaves the env
  var unset and uses the file.
- **`DOCBUILDER_AUTOCONFIRM`: not implemented** — the builder always writes the context
  file; the gate is the operator reviewing the trajectory (no auto-confirm flag).
- **Recurring resolution:** for "same as last month", `context_builder` calls
  `resolve_last_run.py`, which reads `data/run_log.json`, finds the latest matching
  `{tenant, doc_type, client_name}`, bumps the date to month-end and increments the
  invoice number (`{FY}/{client_code}/{seq+1}`, FY rolling April 1). An absent run log →
  `no_prior_run` (the builder falls back to the request).

```bash
cd ~/sandbox/elixirws/aetheris
# Chains context_builder.exs → docbuilder_orchestrator.exs (reads confirmed_context.json).
# The case resets data/run_log.json to the May seed for a deterministic June invoice.
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Invoice for XYZ for June 2026, same as last month" \
./scripts/sprint.sh docbuilder_context
```

### m4 — freeform NL field extraction (fresh path)

The complementary path to "same as last month": a freeform `DOCBUILDER_REQUEST` for a
client with no prior run. `context_builder.exs` extracts a raw field map →
`validate_fields.py` validates + normalises it against the context schema (date → ISO;
`amount_due` validated-as-money, kept as a display string; `currency` upper+checked;
required fields per doc_type) → on success writes `confirmed_context.json`; on a validation
failure the agent self-corrects ONCE (re-reads the request) and, if a field is still
genuinely absent, emits one clarifying message and stops without writing the context —
**single-shot self-correction**, no in-run human reply (same model as the m3 gate; the
operator's "reply" is a re-run with the field).

```bash
cd ~/sandbox/elixirws/aetheris
# Runs only context_builder.exs; resets run_log.json to [] to force the fresh path.
DOCBUILDER_TENANT=bitloka \
DOCBUILDER_REQUEST="Invoice for Northwind Traders at billing@northwind.example, address 12 Harbour Rd, invoice number 2627/NWT/01, amount due \$3,400.00, dated 30 June 2026, titled Invoice 2627/NWT/01" \
./scripts/sprint.sh docbuilder_fresh
```

Asserts `confirmed_context.json` is written + parseable and the run log is NOT appended
(builder-only — PHASE D2 appends only with the orchestrator). The fresh extraction artifacts
are `output/raw_extraction.json` + `output/validated_extraction.json` (inspect the latter on
a clarifying stop). The client-match assertion is client-agnostic (m5 t2): it passes for any
non-empty `client_name`, so overriding `DOCBUILDER_REQUEST` for a different client works.

For the full fresh→render chain (context builder + orchestrator), use
`./scripts/sprint.sh docbuilder_fresh_render` (m5). It chains `context_builder.exs` (fresh
extract) → `docbuilder_orchestrator.exs` (reads `confirmed_context.json` via
`DOCBUILDER_CONTEXT_FILE`, renders + PHASE D2), and additionally asserts every `renamed.json`
output exists, the rendered **PDF has no unresolved `{{placeholder}}` strings** (the m5 t1
`_sub_var` fix — degrades to `[INFO]` if `pdftotext` is absent), and the run log goes 0 → 1.

m6 added a Jinja2 (`.html.j2`) renderer and an offer-letter doc type (DOCX via Pandoc). For
template/doc-type authoring — editing a template, adding a new doc type, and the Jinja2 path
(`generate_html.py`, `generate_docx_from_html.py`, `has_jinja`) — see `docbuilder/runbook.md`
§"Editing an existing template", §"Adding a new doc type", and §"Jinja2 templates (m6)". The
m6 sprint gates are `./scripts/sprint.sh docbuilder_invoice_jinja` (invoice via Jinja, zero
`{{` in the PDF) and `./scripts/sprint.sh docbuilder_offer_letter` (fresh → DOCX).

### Expected output files

After a successful run, `aetheris-agents/docbuilder/output/` contains:

```
template_cache_path.txt              # PHASE 0 — bundle path
pipeline_raw_main.json               # PHASE A — one per data source
pipeline_raw_summary.json            # PHASE A — second demo source
pipeline_spec.json                   # PHASE B — computed doc spec
acme_corp_proposal_2026-06-20.{xlsx,docx,pdf}  # PHASE C+D — branded, renamed
renamed.json                         # PHASE D — {original, renamed} pairs
uploaded.json                        # PHASE E — {filename, drive_file_id, drive_url} (Drive only)
```

### Common failure modes

**`DOCBUILDER_TENANT not set` on eval** — `DOCBUILDER_TENANT` and `DOCBUILDER_CONTEXT` must be set before `mix aetheris run` / `mix run --eval`. The orchestrator raises if `DOCBUILDER_TENANT` is absent.

**Output files missing after run** — check that `overlay_base_dir: nil` is set in the orchestrator. If output appeared under `priv/runs/*/upper/`, overlay was enabled and files were discarded.

**`python3 python3 script.py` in run log** — LLM duplicated the executable in both `command:` and `args:`. Re-run; the system prompt guard should prevent recurrence. See `docbuilder/runbook.md` §"Common failure modes" for the full list.

---

## Adding a new module

1. Create `src/components/modules/{name}/` with component files
2. Add hook to `src/hooks/use{Name}.ts`
3. Add Tauri commands to `src-tauri/src/commands/{name}.rs`
4. Register commands in `src-tauri/src/lib.rs`
5. Add route to `src/App.tsx`
6. Add module entry to `src/modules/registry.ts`
7. Add TypeScript interfaces to `src/hooks/types.ts`
8. Export from `src/hooks/index.ts`

Follow the pattern established in `commands/tools.rs` and
`components/modules/tools/`.
