# rig/p4: Trajectory viewer

## Context

P1 gave the Harness module two tabs: Runs and Events. Events shows a compact
log of event rows for a selected run. The trajectory viewer is a third tab
that reads from `priv/runs/{run_id}/trajectory.json` — the harness's
canonical immutable snapshot — and presents the full event stream with
complete payload detail, step grouping, and JSON export.

All work is in `aetheris-agents/rig/`.

---

## What to build

### New Tauri command: `trajectory_load`

Add `src-tauri/src/commands/trajectory.rs`. No new state struct — derives
the runs directory from `AETHERIS_DB_PATH` at call time.

```rust
use std::path::Path;
use tauri::State;
use crate::HarnessState;

#[derive(serde::Serialize)]
pub struct TrajectoryEvent {
    pub id:         String,
    pub run_id:     String,
    pub seq:        i64,
    pub step:       i64,
    pub event_type: String,
    pub payload:    serde_json::Value,   // parsed object, not a raw string
    pub timestamp:  String,
}

#[derive(serde::Serialize)]
pub struct TrajectoryFile {
    pub run_id:         String,
    pub schema_version: String,
    pub meta:           serde_json::Value,   // full meta block, typed on the frontend
    pub events:         Vec<TrajectoryEvent>,
}

#[tauri::command]
pub fn trajectory_load(
    state:  State<'_, HarnessState>,
    run_id: String,
) -> Result<TrajectoryFile, String> {
    // Derive runs directory from AETHERIS_DB_PATH:
    //   ~/…/aetheris/priv/aetheris.db → priv/ → aetheris/ → priv/runs/
    let db_path = std::env::var("AETHERIS_DB_PATH")
        .map_err(|_| "AETHERIS_DB_PATH not set".to_string())?;

    let traj_path = Path::new(&db_path)
        .parent()                              // priv/
        .and_then(|p| p.parent())             // aetheris/
        .map(|p| p.join("priv").join("runs").join(&run_id).join("trajectory.json"))
        .ok_or_else(|| "could not derive trajectory path from AETHERIS_DB_PATH".to_string())?;

    let raw = std::fs::read_to_string(&traj_path)
        .map_err(|e| format!("read failed: {}", e))?;

    let v: serde_json::Value = serde_json::from_str(&raw)
        .map_err(|e| format!("parse failed: {}", e))?;

    let run_id_out = v["run_id"].as_str().unwrap_or("").to_string();
    let schema_version = v["schema_version"].as_str().unwrap_or("1").to_string();
    let meta = v["meta"].clone();

    let events = v["events"]
        .as_array()
        .ok_or("events not an array")?
        .iter()
        .map(|e| TrajectoryEvent {
            id:         e["id"].as_str().unwrap_or("").to_string(),
            run_id:     e["run_id"].as_str().unwrap_or("").to_string(),
            seq:        e["seq"].as_i64().unwrap_or(0),
            step:       e["step"].as_i64().unwrap_or(0),
            event_type: e["type"].as_str().unwrap_or("").to_string(),
            payload:    e["payload"].clone(),
            timestamp:  e["timestamp"].as_str().unwrap_or("").to_string(),
        })
        .collect();

    Ok(TrajectoryFile { run_id: run_id_out, schema_version, meta, events })
}
```

### New Tauri command: `trajectory_export`

In the same file. Opens a save dialog and copies the trajectory file.

```rust
use tauri_plugin_dialog::DialogExt;

#[tauri::command]
pub async fn trajectory_export(
    app:    tauri::AppHandle,
    run_id: String,
) -> Result<(), String> {
    let db_path = std::env::var("AETHERIS_DB_PATH")
        .map_err(|_| "AETHERIS_DB_PATH not set".to_string())?;

    let src = std::path::Path::new(&db_path)
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.join("priv").join("runs").join(&run_id).join("trajectory.json"))
        .ok_or_else(|| "could not derive trajectory path".to_string())?;

    let dest = app
        .dialog()
        .file()
        .set_file_name(format!("trajectory-{}.json", run_id))
        .blocking_save_file();

    if let Some(path) = dest {
        std::fs::copy(&src, path.as_path().unwrap())
            .map_err(|e| format!("copy failed: {}", e))?;
    }

    Ok(())
}
```

### Registration

In `commands/mod.rs`:
```rust
pub mod trajectory;
```

In `lib.rs` `generate_handler![]`:
```rust
commands::trajectory::trajectory_load,
commands::trajectory::trajectory_export,
```

`trajectory_load` takes `State<'_, HarnessState>` (to follow the existing
helper pattern) but does not use the DB connection — it only needs the
env var. If `HarnessState` is not needed, remove the state parameter and
derive the path from env directly. Either compiles; prefer the simpler form.

---

### TypeScript types (add to `src/hooks/types.ts`)

```typescript
export interface TrajectoryMeta {
  model:           string;
  provider:        string;
  mode:            string;
  step_count:      number;
  max_steps:       number;
  started_at:      string;
  finished_at:     string;
  tools:           string[];
  system_prompt:   string;
  user_prompt:     string;
  sandbox_path:    string;
  seed:            string | null;
  overlay_changes: unknown[];
}

export interface TrajectoryEvent {
  id:          string;
  run_id:      string;
  seq:         number;
  step:        number;
  event_type:  string;
  payload:     Record<string, unknown>;   // parsed object — NOT a raw string
  timestamp:   string;
}

export interface TrajectoryFile {
  run_id:         string;
  schema_version: string;
  meta:           TrajectoryMeta;
  events:         TrajectoryEvent[];
}
```

Export all three from `src/hooks/index.ts`.

**Important:** `TrajectoryEvent.payload` is `Record<string, unknown>`, not
`string`. This is intentional and differs from the existing `EventRow.payload`
(raw JSON string). Do not conflate the two types.

---

### `src/hooks/useTrajectory.ts`

```typescript
import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { TrajectoryFile } from './types';

export function useTrajectory(runId: string | null) {
  const [trajectory, setTrajectory] = useState<TrajectoryFile | null>(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setTrajectory(null);
      return;
    }
    setLoading(true);
    setError(null);
    invoke<TrajectoryFile>('trajectory_load', { run_id: runId })
      .then((t) => { setTrajectory(t); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, [runId]);

  return { trajectory, loading, error };
}
```

Export from `src/hooks/index.ts`.

---

### `src/components/modules/harness/TrajectoryView.tsx`

Tab content component. Receives `runId: string | null` and `onExport` from
`HarnessRoute`. Renders three sections.

```tsx
import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { ChevronDown, ChevronRight, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTrajectory } from '@/hooks/useTrajectory';
import type { TrajectoryEvent } from '@/hooks/types';

// ── Event type colour map ────────────────────────────────────────────────────
const EVENT_COLOURS: Record<string, string> = {
  prompt_built:            'bg-blue-100 text-blue-800',
  llm_called:              'bg-purple-100 text-purple-800',
  llm_responded:           'bg-violet-100 text-violet-800',
  tool_called:             'bg-amber-100 text-amber-800',
  tool_result:             'bg-orange-100 text-orange-800',
  step_complete:           'bg-green-100 text-green-800',
  run_complete:            'bg-green-200 text-green-900',
  error:                   'bg-red-100 text-red-800',
  agent_message_sent:      'bg-sky-100 text-sky-800',
  agent_message_received:  'bg-sky-100 text-sky-800',
};

function eventColour(type: string): string {
  return EVENT_COLOURS[type] ?? 'bg-muted text-muted-foreground';
}

// ── Single expandable event row ──────────────────────────────────────────────
function EventRow({ event }: { event: TrajectoryEvent }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b last:border-b-0">
      <button
        className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted/50
                   transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <span className="text-xs font-mono text-muted-foreground w-8 shrink-0">
          {event.seq}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0
                          ${eventColour(event.event_type)}`}>
          {event.event_type}
        </span>
        <span className="text-xs text-muted-foreground ml-auto shrink-0">
          {new Date(event.timestamp).toISOString().replace('T', ' ').slice(0, 23)}
        </span>
        {open
          ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
          : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />}
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs font-mono bg-muted/30 overflow-x-auto
                        whitespace-pre-wrap break-all">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      )}
    </div>
  );
}

// ── Step group ───────────────────────────────────────────────────────────────
function StepGroup({ step, events }: { step: number; events: TrajectoryEvent[] }) {
  const [open, setOpen] = useState(true);

  return (
    <div className="border rounded-md mb-2">
      <button
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted/50
                   transition-colors font-medium text-sm"
        onClick={() => setOpen((o) => !o)}
      >
        {open
          ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
          : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        Step {step}
        <span className="ml-2 text-xs text-muted-foreground font-normal">
          {events.length} event{events.length !== 1 ? 's' : ''}
        </span>
      </button>
      {open && (
        <div className="border-t">
          {events.map((e) => <EventRow key={e.id} event={e} />)}
        </div>
      )}
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
interface Props {
  runId: string | null;
}

export function TrajectoryView({ runId }: Props) {
  const { trajectory, loading, error } = useTrajectory(runId);
  const [metaOpen, setMetaOpen] = useState(true);

  if (!runId) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Select a run to view its trajectory.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        Loading…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-red-600">{error}</div>
    );
  }

  if (!trajectory) return null;

  const { meta, events } = trajectory;

  // Group events by step
  const steps = events.reduce<Map<number, TrajectoryEvent[]>>((acc, e) => {
    const group = acc.get(e.step) ?? [];
    group.push(e);
    acc.set(e.step, group);
    return acc;
  }, new Map());

  const duration = meta.started_at && meta.finished_at
    ? Math.round(
        (new Date(meta.finished_at).getTime() - new Date(meta.started_at).getTime()) / 1000
      )
    : null;

  async function handleExport() {
    try {
      await invoke('trajectory_export', { run_id: trajectory!.run_id });
    } catch (e) {
      console.error('export failed', e);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">

      {/* ── Meta panel ─────────────────────────────────────────────────── */}
      <div className="border-b shrink-0">
        <div className="flex items-center justify-between px-4 py-2">
          <button
            className="flex items-center gap-2 text-sm font-medium hover:text-foreground
                       text-muted-foreground transition-colors"
            onClick={() => setMetaOpen((o) => !o)}
          >
            {metaOpen
              ? <ChevronDown className="h-4 w-4" />
              : <ChevronRight className="h-4 w-4" />}
            Run metadata
          </button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-3.5 w-3.5 mr-1.5" />
            Export JSON
          </Button>
        </div>

        {metaOpen && (
          <div className="px-4 pb-3 grid grid-cols-2 gap-x-8 gap-y-1 text-xs">
            <MetaRow label="Model"    value={meta.model} />
            <MetaRow label="Provider" value={meta.provider} />
            <MetaRow label="Mode"     value={meta.mode} />
            <MetaRow label="Steps"    value={`${meta.step_count} / ${meta.max_steps}`} />
            {duration !== null &&
              <MetaRow label="Duration" value={`${duration}s`} />}
            <MetaRow label="Tools"    value={meta.tools.join(', ') || '—'} />
            <div className="col-span-2 mt-1">
              <ExpandableText label="System prompt" text={meta.system_prompt} />
            </div>
            <div className="col-span-2">
              <ExpandableText label="User prompt" text={meta.user_prompt} />
            </div>
          </div>
        )}
      </div>

      {/* ── Event stream ───────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-4">
        {Array.from(steps.entries())
          .sort(([a], [b]) => a - b)
          .map(([step, evts]) => (
            <StepGroup key={step} step={step} events={evts} />
          ))}
      </div>
    </div>
  );
}

// ── Small helpers ────────────────────────────────────────────────────────────
function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-muted-foreground shrink-0 w-24">{label}</span>
      <span className="font-mono truncate">{value}</span>
    </div>
  );
}

function ExpandableText({ label, text }: { label: string; text: string }) {
  const [open, setOpen] = useState(false);
  const preview = text?.slice(0, 120);

  return (
    <div className="mb-1">
      <button
        className="text-muted-foreground hover:text-foreground transition-colors flex
                   items-center gap-1"
        onClick={() => setOpen((o) => !o)}
      >
        {open
          ? <ChevronDown className="h-3 w-3" />
          : <ChevronRight className="h-3 w-3" />}
        {label}
      </button>
      {open
        ? <pre className="mt-1 text-xs font-mono bg-muted/30 rounded p-2
                          whitespace-pre-wrap break-all">{text}</pre>
        : <p className="mt-0.5 text-xs text-muted-foreground truncate">{preview}
            {text?.length > 120 ? '…' : ''}</p>
      }
    </div>
  );
}
```

---

### Modifications to `HarnessRoute` in `RunList.tsx`

Add Trajectory as a third tab. The existing component owns `selectedRunId`
and `activeTab` — extend both.

```tsx
// Add to tab config (alongside existing 'runs' and 'events'):
{ id: 'trajectory', label: 'Trajectory', disabled: !selectedRunId }

// Add tab content:
{activeTab === 'trajectory' && (
  <TrajectoryView runId={selectedRunId} />
)}
```

Events and Trajectory tabs should both be disabled (visually muted, not
clickable) when no run is selected. Check how the existing Events tab handles
this — match the same pattern. If `MainArea` does not yet support a
`disabled` prop on tab config entries, add it: render the tab label in
`text-muted-foreground` and skip the `onClick` handler.

---

### Additions to `registry.ts`

No changes — Trajectory is a tab within the Harness module, not a new
sidebar section. The Harness sidebar entry already covers it.

---

### Additions to `App.tsx`

No new routes — Trajectory renders inside the existing `/harness` route via
`HarnessRoute`.

---

## Acceptance criteria

- [ ] `trajectory_load` command compiles, reads correct file path, returns
      `TrajectoryFile` with parsed payload objects
- [ ] `trajectory_export` opens a save dialog and copies the file
- [ ] Both commands registered in `generate_handler![]`
- [ ] `TrajectoryMeta`, `TrajectoryEvent`, `TrajectoryFile` in `types.ts`,
      exported from `index.ts`
- [ ] `useTrajectory` hook: fetches on `runId` change, clears on null
- [ ] Trajectory tab appears in Harness module, disabled when no run selected
- [ ] Meta panel shows model, provider, mode, steps, duration, tools,
      system_prompt, user_prompt — all expandable/collapsible
- [ ] Events grouped by step; each step group is collapsible (open by default)
- [ ] Each event row shows seq, type badge (colour-coded), timestamp
- [ ] Clicking an event row expands the full pretty-printed JSON payload
- [ ] Export button triggers `trajectory_export` invoke
- [ ] No TypeScript `any`
- [ ] `cargo build` exits 0, zero warnings
- [ ] `bun run build` exits 0, zero TypeScript errors

---

## Files to create/modify

**Create:**
- `src-tauri/src/commands/trajectory.rs`
- `src/hooks/useTrajectory.ts`
- `src/components/modules/harness/TrajectoryView.tsx`

**Modify:**
- `src-tauri/src/commands/mod.rs` — add `pub mod trajectory;`
- `src-tauri/src/lib.rs` — register both commands in `generate_handler![]`
- `src/hooks/types.ts` — add `TrajectoryMeta`, `TrajectoryEvent`, `TrajectoryFile`
- `src/hooks/index.ts` — export `useTrajectory` and new types
- `src/components/modules/harness/RunList.tsx` — add Trajectory tab +
  `TrajectoryView` content

---

## Notes

**`payload` type difference.** `EventRow.payload` (harness.rs) is a raw JSON
string. `TrajectoryEvent.payload` (trajectory.rs) is a parsed
`serde_json::Value`. Do not mix them. The trajectory viewer always has
structured payloads; no `JSON.parse()` needed on the frontend.

**Path derivation.** `AETHERIS_DB_PATH` → parent (`priv/`) → parent
(`aetheris/`) → join `priv/runs/{run_id}/trajectory.json`. This is the same
derivation used for `aetheris_dir` in `orchestrate.rs`. The path goes back
into `priv/` from the aetheris root — this is correct; the harness writes
trajectory files under its own `priv/runs/`.

**`tauri-plugin-dialog`.** Check `Cargo.toml` — if the dialog plugin is
already present (it may be from existing provenance features), import it as
shown. If not, add `tauri-plugin-dialog = "2"` to dependencies and register
it in `lib.rs` with `.plugin(tauri_plugin_dialog::init())`.

**Step grouping.** Events are ordered by `seq` ascending in the JSON file.
Group by the `step` field. Steps are rendered in ascending step order.
Within a step, events render in seq order (already sorted in the file).

**No polling.** Trajectory files are immutable — written once at run
completion. `useTrajectory` fetches once and never polls.
