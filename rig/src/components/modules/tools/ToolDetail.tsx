import { useState } from 'react';
import { AlertTriangle, Loader2, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTools } from '@/hooks/useTools';
import type { ManifestScript, HarnessTool } from '@/hooks/types';

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
      <pre className="text-xs bg-muted rounded p-3 overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto font-mono">
        {display}
      </pre>
    </div>
  );
}

function ScriptDetailPanel({
  tools,
  use_case,
  script,
}: {
  tools:    ReturnType<typeof useTools>;
  use_case: string;
  script:   ManifestScript;
}) {
  const { running, result, runError, runScript } = tools;
  const [argValues, setArgValues] = useState<Record<string, string>>(
    Object.fromEntries(script.args.map((a) => [a.name, a.default ?? '']))
  );
  const [rawArgs, setRawArgs] = useState('');

  return (
    <div className="flex flex-col gap-4">
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

      {!script.undeclared ? (
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
      ) : (
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
      )}

      <button
        onClick={() => navigator.clipboard.writeText(script.example)}
        className="text-left font-mono text-xs bg-muted rounded px-3 py-2
                   hover:bg-muted/80 w-full mb-3"
        title="Click to copy"
      >
        {script.example}
      </button>

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
    </div>
  );
}

function HarnessDetail({ tool }: { tool: HarnessTool }) {
  return (
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
  );
}

export function ToolDetail({ tools }: { tools: ReturnType<typeof useTools> }) {
  const { selected } = tools;

  if (!selected) {
    return (
      <div className="flex flex-col items-center justify-center h-full
                      text-muted-foreground gap-2">
        <Wrench className="h-8 w-8 opacity-30" />
        <p className="text-sm">Select a tool to inspect it</p>
      </div>
    );
  }

  if (selected.kind === 'script') {
    return (
      <ScriptDetailPanel
        key={`${selected.use_case}/${selected.script.name}`}
        tools={tools}
        use_case={selected.use_case}
        script={selected.script}
      />
    );
  }

  if (selected.kind === 'harness') {
    return <HarnessDetail tool={selected.tool} />;
  }

  return null;
}
