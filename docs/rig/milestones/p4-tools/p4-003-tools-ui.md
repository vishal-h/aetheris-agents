# rig/p4-tools: Tools UI

## Context

With the inventory backend in place, this issue builds the Tools module:
a two-panel view for browsing, inspecting, and running tools.

All work is in `aetheris-agents/rig/`.

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

---

## What to build

### `src/hooks/useTools.ts`

Owns inventory fetch, selection state, and script execution.

```typescript
import { useState, useEffect, useCallback } from 'react';
import { invoke } from '@tauri-apps/api/core';
import {
  ToolsInventory, SelectedTool, ManifestScript, ScriptResult,
} from './types';

export function useTools() {
  const [inventory,  setInventory]  = useState<ToolsInventory | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [selected,   setSelected]   = useState<SelectedTool | null>(null);
  const [running,    setRunning]    = useState(false);
  const [result,     setResult]     = useState<ScriptResult | null>(null);
  const [runError,   setRunError]   = useState<string | null>(null);

  useEffect(() => {
    invoke<ToolsInventory>('tools_list_inventory')
      .then(setInventory)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const selectScript = useCallback((use_case: string, script: ManifestScript) => {
    setSelected({ kind: 'script', use_case, script });
    setResult(null);
    setRunError(null);
  }, []);

  const selectHarness = useCallback((name: string) => {
    const tool = inventory?.harness.find((t) => t.name === name);
    if (tool) {
      setSelected({ kind: 'harness', tool });
      setResult(null);
      setRunError(null);
    }
  }, [inventory]);

  const runScript = useCallback(async (
    use_case: string,
    file:     string,
    args:     string[],
  ) => {
    setRunning(true);
    setResult(null);
    setRunError(null);
    try {
      const res = await invoke<ScriptResult>('tools_run_script', {
        use_case, file, args,
      });
      setResult(res);
    } catch (e) {
      setRunError(String(e));
    } finally {
      setRunning(false);
    }
  }, []);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    invoke<ToolsInventory>('tools_list_inventory')
      .then(setInventory)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return {
    inventory, loading, error,
    selected, selectScript, selectHarness,
    running, result, runError, runScript,
    refresh,
  };
}
```

---

### `src/components/modules/tools/ToolsView.tsx`

Top-level component. Two-panel layout. No outer padding — left panel
must flush against the border.

```tsx
import { useTools } from '@/hooks/useTools';
import { ToolTree }   from './ToolTree';
import { ToolDetail } from './ToolDetail';

export function ToolsView() {
  const tools = useTools();

  return (
    <div className="flex flex-1 h-full overflow-hidden">
      {/* Left panel — tree */}
      <div className="w-64 shrink-0 border-r overflow-y-auto p-3">
        <ToolTree tools={tools} />
      </div>
      {/* Right panel — detail + run */}
      <div className="flex-1 overflow-y-auto p-6">
        <ToolDetail tools={tools} />
      </div>
    </div>
  );
}
```

---

### `src/components/modules/tools/ToolTree.tsx`

Left panel. Three sections: use cases (grouped + collapsible), Harness,
MCP (hidden when empty).

```tsx
import { useState } from 'react';
import { ChevronDown, ChevronRight, RefreshCw, AlertTriangle } from 'lucide-react';
import { useTools } from '@/hooks/useTools';

export function ToolTree({ tools }: { tools: ReturnType<typeof useTools> }) {
  const { inventory, loading, error, selected,
          selectScript, selectHarness, refresh } = tools;
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});

  if (loading && !inventory) {
    return <div className="text-sm text-muted-foreground p-2">Loading…</div>;
  }
  if (error) {
    return <div className="text-sm text-red-600 p-2">{error}</div>;
  }
  if (!inventory) return null;

  const toggle = (key: string) =>
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="flex flex-col gap-1 text-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wide
                         text-muted-foreground">Tools</span>
        <button onClick={refresh}
                className="text-muted-foreground hover:text-foreground">
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Use-case groups */}
      {inventory.use_cases.map((group) => {
        const isOpen = !collapsed[group.use_case];
        const isActive = (name: string) =>
          selected?.kind === 'script' &&
          selected.use_case === group.use_case &&
          selected.script.name === name;

        return (
          <div key={group.use_case}>
            <button
              onClick={() => toggle(group.use_case)}
              className="flex items-center gap-1 w-full text-left font-medium
                         text-foreground hover:text-foreground/80 py-0.5"
            >
              {isOpen
                ? <ChevronDown  className="h-3.5 w-3.5 shrink-0" />
                : <ChevronRight className="h-3.5 w-3.5 shrink-0" />}
              {group.use_case}
            </button>
            {isOpen && (
              <div className="ml-4 flex flex-col gap-0.5 mt-0.5">
                {group.scripts.length === 0 && (
                  <span className="text-xs text-muted-foreground italic">
                    no scripts
                  </span>
                )}
                {group.scripts.map((script) => (
                  <button
                    key={script.name}
                    onClick={() => selectScript(group.use_case, script)}
                    className={`flex items-center gap-1.5 text-left px-2 py-1 rounded
                      ${isActive(script.name)
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                      }`}
                  >
                    {script.undeclared && (
                      <AlertTriangle className="h-3 w-3 text-amber-500 shrink-0" />
                    )}
                    {script.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      })}

      {/* Harness section */}
      <div className="mt-3">
        <span className="text-xs font-semibold uppercase tracking-wide
                         text-muted-foreground block mb-1">Harness</span>
        <div className="flex flex-col gap-0.5">
          {inventory.harness.map((tool) => (
            <button
              key={tool.name}
              onClick={() => selectHarness(tool.name)}
              className={`text-left px-2 py-1 rounded text-sm
                ${selected?.kind === 'harness' && selected.tool.name === tool.name
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                }`}
            >
              {tool.name}
            </button>
          ))}
        </div>
      </div>

      {/* MCP section — only rendered when populated (p4-004) */}
      {inventory.mcp.length > 0 && (
        <div className="mt-3">
          <span className="text-xs font-semibold uppercase tracking-wide
                           text-muted-foreground block mb-1">MCP</span>
          <div className="flex flex-col gap-0.5">
            {inventory.mcp.map((tool) => (
              <button
                key={`${tool.server}/${tool.name}`}
                className="text-left px-2 py-1 rounded text-sm
                           text-muted-foreground hover:text-foreground hover:bg-accent/50"
              >
                <span className="text-xs text-muted-foreground/60">
                  {tool.server}/
                </span>
                {tool.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### `src/components/modules/tools/ToolDetail.tsx`

Right panel. Three rendering modes keyed on `selected.kind`.

**Empty state:**
```tsx
import { Wrench } from 'lucide-react';

// selected === null
<div className="flex flex-col items-center justify-center h-full
                text-muted-foreground gap-2">
  <Wrench className="h-8 w-8 opacity-30" />
  <p className="text-sm">Select a tool to inspect it</p>
</div>
```

**Script detail** (`selected.kind === 'script'`):

Use a `key` prop on the outer div keyed to `${use_case}/${script.name}`
to force React to remount and reset local state on every selection change.

Local state:
```typescript
const [argValues, setArgValues] = useState<Record<string, string>>(
  Object.fromEntries(
    script.args.map((a) => [a.name, a.default ?? ''])
  )
);
const [rawArgs, setRawArgs] = useState('');
```

Layout — three stacked sections:

**1. Header**
```tsx
<div className="flex flex-col gap-1 mb-4">
  <h2 className="text-lg font-semibold">{script.name}</h2>
  <p className="text-sm text-muted-foreground">{script.description}</p>
</div>

{script.undeclared && (
  <div className="flex items-center gap-2 rounded-md border border-amber-200
                  bg-amber-50 dark:bg-amber-950/20 px-3 py-2 text-sm
                  text-amber-800 dark:text-amber-300 mb-4">
    <AlertTriangle className="h-4 w-4 shrink-0" />
    This script is not declared in tools.json. Add an entry to enable
    structured arg forms and output formatting.
  </div>
)}
```

**2. Arg form** (declared scripts only — structured fields):
```tsx
<div className="flex flex-col gap-3 mb-4">
  <h3 className="text-sm font-medium">Arguments</h3>
  {script.args.map((arg) => (
    <div key={arg.name} className="flex flex-col gap-1">
      <label className="text-xs font-medium">
        {arg.name}
        {arg.required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {arg.arg_type === 'boolean' ? (
        <input
          type="checkbox"
          checked={argValues[arg.name] === 'true'}
          onChange={(e) =>
            setArgValues((prev) => ({
              ...prev,
              [arg.name]: e.target.checked ? 'true' : 'false',
            }))
          }
        />
      ) : (
        <input
          type="text"
          className="rounded-md border border-input bg-background px-3 py-1.5
                     text-sm font-mono placeholder:text-muted-foreground
                     focus-visible:outline-none focus-visible:ring-2
                     focus-visible:ring-ring"
          placeholder={arg.default ?? ''}
          value={argValues[arg.name]}
          onChange={(e) =>
            setArgValues((prev) => ({ ...prev, [arg.name]: e.target.value }))
          }
        />
      )}
      <p className="text-xs text-muted-foreground">{arg.description}</p>
    </div>
  ))}
</div>
```

Undeclared scripts: single raw args input instead:
```tsx
<div className="flex flex-col gap-1 mb-4">
  <label className="text-xs font-medium">Args</label>
  <input
    type="text"
    className="w-full rounded-md border border-input bg-background px-3 py-1.5
               text-sm font-mono placeholder:text-muted-foreground
               focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    placeholder="e.g. data/sample.csv --limit 10"
    value={rawArgs}
    onChange={(e) => setRawArgs(e.target.value)}
  />
</div>
```

**3. Run section**

Example command (click to copy):
```tsx
<button
  onClick={() => navigator.clipboard.writeText(script.example)}
  className="text-left font-mono text-xs bg-muted rounded px-3 py-2
             hover:bg-muted/80 w-full mb-3"
  title="Click to copy"
>
  {script.example}
</button>
```

Run button + output:
```tsx
<Button
  onClick={() => {
    const builtArgs = script.undeclared
      ? rawArgs.trim().split(/\s+/).filter(Boolean)
      : buildArgs(script, argValues);
    runScript(use_case, script.file, builtArgs);
  }}
  disabled={running || (!script.undeclared && hasEmptyRequired(script, argValues))}
>
  {running ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
  {running ? 'Running…' : 'Run'}
</Button>

{runError && (
  <p className="text-sm text-red-600 mt-3">{runError}</p>
)}

{result && (
  <div className="flex flex-col gap-2 mt-4">
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full w-fit
      ${result.exit_code === 0
        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
      }`}>
      exit {result.exit_code}
    </span>
    {result.stdout && (
      <OutputBlock label="stdout" content={result.stdout} format={script.output} />
    )}
    {result.stderr && (
      <OutputBlock label="stderr" content={result.stderr} format="text" />
    )}
  </div>
)}
```

**Helper functions (local to `ToolDetail.tsx`):**

```typescript
function buildArgs(script: ManifestScript, values: Record<string, string>): string[] {
  const positional: string[] = [];
  const flagged:    string[] = [];
  for (const arg of script.args) {
    const val = values[arg.name];
    if (!val && !arg.required) continue;
    if (arg.arg_type === 'boolean') {
      if (val === 'true' && arg.flag) flagged.push(arg.flag);
    } else if (arg.flag) {
      flagged.push(arg.flag, val);
    } else {
      positional.push(val);
    }
  }
  return [...positional, ...flagged];
}

function hasEmptyRequired(
  script: ManifestScript,
  values: Record<string, string>,
): boolean {
  return script.args
    .filter((a) => a.required)
    .some((a) => !values[a.name]?.trim());
}
```

**`OutputBlock` sub-component (local to `ToolDetail.tsx`):**

```tsx
function OutputBlock({
  label, content, format,
}: {
  label:   string;
  content: string;
  format:  'json' | 'text' | 'files';
}) {
  const display = (() => {
    if (format === 'json') {
      try { return JSON.stringify(JSON.parse(content), null, 2); }
      catch { return content; }
    }
    return content;
  })();

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground font-medium">{label}</span>
      <pre className="text-xs bg-muted rounded p-3 overflow-x-auto
                      whitespace-pre-wrap max-h-96 overflow-y-auto font-mono">
        {display}
      </pre>
    </div>
  );
}
```

**Harness tool detail** (`selected.kind === 'harness'`):

Read-only — no Run button.

```tsx
<div className="flex flex-col gap-4">
  <div>
    <h2 className="text-lg font-semibold">{tool.name}</h2>
    <p className="text-sm text-muted-foreground mt-1">{tool.description}</p>
  </div>

  {tool.args.length > 0 && (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">Arguments</h3>
      {tool.args.map((arg) => (
        <div key={arg.name} className="flex flex-col gap-0.5 rounded-md border p-3">
          <div className="flex items-center gap-2">
            <code className="text-sm font-mono">{arg.name}</code>
            <span className="text-xs text-muted-foreground">{arg.arg_type}</span>
            {arg.required && (
              <span className="text-xs text-red-500">required</span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">{arg.description}</p>
        </div>
      ))}
    </div>
  )}

  {tool.notes && (
    <p className="text-xs text-muted-foreground border-l-2 pl-3 italic">
      {tool.notes}
    </p>
  )}
</div>
```

---

### Route + registry

In `src/App.tsx`:
```tsx
import { ToolsView } from '@/components/modules/tools/ToolsView';

<Route path="/tools" element={
  <div className="flex flex-1 h-full overflow-hidden bg-background">
    <ToolsView />
  </div>
} />
```

No `p-8` wrapper — `ToolsView` manages its own internal padding.

In `src/modules/registry.ts` (add after orchestratorModule):
```typescript
const toolsModule: Module = {
  id: 'tools',
  label: 'Tools',
  icon: 'Wrench',
  sections: [
    { id: 'tools', label: 'Tools', icon: 'Wrench', path: '/tools' },
  ],
};

export const modules: Module[] = [
  harnessModule,
  orchestratorModule,
  toolsModule,
  f2Module,
  provenanceModule,
];
```

Add `Wrench` to `iconMap` in `Sidebar.tsx`.

Export `useTools` from `src/hooks/index.ts`.

---

## Acceptance criteria

- [ ] Tools module in sidebar (Wrench icon, third entry)
- [ ] Left panel renders use-case groups (collapsible), Harness section,
      MCP section (hidden when empty)
- [ ] Undeclared scripts show amber warning icon in tree
- [ ] Selecting a script loads detail + arg form in right panel
- [ ] Undeclared scripts get raw args text input instead of structured form
- [ ] Required arg validation: Run button disabled until all required
      fields have values
- [ ] Clicking example command copies it to clipboard
- [ ] Run executes script with correct `use_case` + `file` + assembled args
- [ ] Output area shows stdout (pretty-printed if `output: "json"`),
      stderr (if non-empty), exit code badge
- [ ] Selecting a harness tool shows read-only detail, no Run button
- [ ] Refresh button re-fetches inventory
- [ ] No TypeScript `any`
- [ ] No `<form>` tags
- [ ] `bun run build` exits 0

## Files to create/modify

- `src/hooks/useTools.ts` (new)
- `src/components/modules/tools/ToolsView.tsx` (new)
- `src/components/modules/tools/ToolTree.tsx` (new)
- `src/components/modules/tools/ToolDetail.tsx` (new)
- `src/hooks/index.ts` (export useTools)
- `src/modules/registry.ts` (add toolsModule)
- `src/App.tsx` (add /tools route)
- `src/components/shell/Sidebar.tsx` (add Wrench to iconMap)

## Notes

**Arg form state resets on selection change.** Use a `key` prop on the
outermost div in the script detail section, keyed to
`${use_case}/${script.name}`. This forces React to remount the component
and reinitialise `argValues` from the new script's defaults cleanly.

**`tools_run_script` is synchronous.** The invoke call blocks until the
script exits. For scripts that take more than a few seconds, the UI will
appear frozen — the `running` state and spinner communicate that something
is happening. If this becomes a problem in practice, a follow-up can
switch to the async streaming pattern from `orchestrate_start`.

**`OutputBlock` is local to `ToolDetail.tsx`.** Not worth extracting
until there is a second consumer.
