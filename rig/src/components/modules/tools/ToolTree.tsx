import { useState } from 'react';
import { ChevronDown, ChevronRight, RefreshCw, AlertTriangle } from 'lucide-react';
import { useTools } from '@/hooks/useTools';
import type { McpTool } from '@/hooks/types';

export function ToolTree({ tools }: { tools: ReturnType<typeof useTools> }) {
  const { inventory, loading, error, selected,
          selectScript, selectHarness, selectMcp, refresh } = tools;
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
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Tools
        </span>
        <button onClick={refresh} className="text-muted-foreground hover:text-foreground">
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

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
                  <span className="text-xs text-muted-foreground italic">no scripts</span>
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

      <div className="mt-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground block mb-1">
          Harness
        </span>
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

      {inventory.mcp.length > 0 && (
        <div className="mt-3">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground block mb-1">
            MCP
          </span>
          {Object.entries(
            inventory.mcp.reduce<Record<string, McpTool[]>>((acc, t) => {
              (acc[t.server_id] ??= []).push(t);
              return acc;
            }, {})
          ).map(([serverId, serverTools]) => (
            <div key={serverId} className="mb-1">
              <span className="text-xs text-muted-foreground/60 px-2 block">
                {serverTools[0].server_label}
              </span>
              {serverTools.map((tool) => (
                <button
                  key={tool.name}
                  onClick={() => selectMcp(tool)}
                  className={`text-left px-2 py-1 rounded text-sm w-full
                    ${selected?.kind === 'mcp' && selected.tool.name === tool.name
                      && selected.tool.server_id === tool.server_id
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                    }`}
                >
                  {tool.name}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
